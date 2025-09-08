import os, time, subprocess, json, select, traceback, sys, uuid, io, contextlib


class PersistentDockerBot:
    """
    Environment knobs:
      CTPC_READY_TIMEOUT_SEC    -> max seconds to wait for the bot to print READY (default 5.0)
      CTPC_BOT_IO_TIMEOUT_SEC   -> host-side per-move wall-clock timeout (default 1.5)
      MOVE_BUDGET_SEC           -> in-container wall-clock for namespace.move() (default 1.45)
    """

    def __init__(self, bot_code, container_name_prefix):
        # Unique name per instance
        self.container_name = f"{container_name_prefix}-{uuid.uuid4().hex[:8]}"
        self.bot_code = bot_code

        subprocess.run(["docker", "rm", "-f", self.container_name],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Program executed within docker container
        docker_program_code = "\n".join([
            "import sys, json, types, traceback, io, contextlib, os, signal, time",
            "namespace = types.SimpleNamespace()",
            "code = []",
            "while True:",
            "    line = sys.stdin.readline()",
            "    if not line: break",
            "    if line.strip() == '__END__': break",
            "    code.append(line)",
            "exec(compile(''.join(code), '<stdin>', 'exec'), namespace.__dict__)",
            "print('READY', flush=True)",
            "",
            "def _timeout_handler(signum, frame):",
            "    raise TimeoutError('move timed out')",
            "try:",
            "    move_budget = float(os.getenv('MOVE_BUDGET_SEC', '1.45'))",
            "except Exception:",
            "    move_budget = 1.45",
            "",
            "while True:",
            "    line = sys.stdin.readline()",
            "    if not line: break",
            "    try:",
            "        raw = json.loads(line)",
            "        state, player = raw",
            "        try:",
            "            buf = io.StringIO()",
            "            with contextlib.redirect_stdout(buf):",
            "                signal.signal(signal.SIGALRM, _timeout_handler)",
            "                signal.setitimer(signal.ITIMER_REAL, move_budget)",
            "                try:",
            "                    result = namespace.move(state, player)",
            "                finally:",
            "                    signal.setitimer(signal.ITIMER_REAL, 0.0)",
            "            log = buf.getvalue()",
            "            if log:",
            "                print(log, file=sys.stderr, flush=True)",
            "            print(json.dumps({'ok': result}), flush=True)",
            "        except TimeoutError:",
            "            print(json.dumps({'error': 'MoveTimeout'}), flush=True)",
            "        except Exception as e:",
            "            error_msg = f\"{type(e).__name__}: {str(e)}\"",
            "            tb = traceback.format_exc()",
            "            print(json.dumps({'error': error_msg, 'traceback': tb}), flush=True)",
            "    except Exception as e:",
            "        print(json.dumps({'error': 'BadInput', 'traceback': str(e)}), flush=True)",
        ])

        self.proc = subprocess.Popen(
            [
                "docker", "run", "-i", "--rm",
                "--name", self.container_name,
                "--label", "ctpc=bot",
                "--network", "none",
                "--memory", "128m", "--memory-swap", "128m",
                "--oom-kill-disable=false",
                "--cpus", "0.5",
                "--pids-limit", "64",
                "--read-only",
                "--security-opt", "no-new-privileges",
                "--cap-drop=ALL",
                "--tmpfs", "/tmp:exec,nosuid,nodev,size=64m",
                "--ulimit", "nofile=64:64",
                "--ulimit", "nproc=32:32",
                "--device-read-bps", "/dev/null:1mb",
                "--device-read-iops", "/dev/null:10",
                "bot-runner",
                "env", "PYTHONPATH=/app",
                "python3", "-u", "-c", docker_program_code
            ],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        # Send bot code then signal end
        self.proc.stdin.write(self.bot_code + "\n__END__\n")
        self.proc.stdin.flush()

        try:
            ready_timeout = float(os.getenv("CTPC_READY_TIMEOUT_SEC", "5.0"))
        except ValueError:
            ready_timeout = 5.0

        deadline = time.time() + ready_timeout
        self._ready = False
        while time.time() < deadline:
            if self.proc.poll() is not None:
                # Process exited; stop waiting
                break
            if select.select([self.proc.stdout], [], [], 0.05)[0]:
                line = self.proc.stdout.readline().strip()
                if line == "READY":
                    self._ready = True
                    break
                self._debug_log(f"[boot-stdout:{self.container_name}] {line}")
            else:
                time.sleep(0.01)

        if not self._ready:
            self._debug_log(f"[warn] {self.container_name} did not signal READY in {ready_timeout}s")

    def send_state(self, state, player):
        try:
            if self.proc.poll() is not None:
                self._debug_log(f"[dead] {self.container_name} exited before send_state")
                self._drain_stderr_nonblocking()
                return None

            # Send (state, player)
            msg = json.dumps([state, player]) + "\n"
            try:
                self.proc.stdin.write(msg)
                self.proc.stdin.flush()
            except Exception as e:
                self._debug_log(f"[stdin-error] {self.container_name}: {e}")
                self._drain_stderr_nonblocking()
                return None

            # Strict per-move timeout (default 1.5s, allowed slight leeway)
            try:
                timeout = float(os.getenv("CTPC_BOT_IO_TIMEOUT_SEC", "1.5"))
            except ValueError:
                timeout = 1.5

            start = time.perf_counter()
            deadline = start + timeout
            while True:
                remaining = deadline - time.perf_counter()
                if remaining <= 0:
                    break
                if select.select([self.proc.stdout], [], [], remaining)[0]:
                    output = self.proc.stdout.readline().strip()
                    if not output:
                        continue
                    try:
                        response = json.loads(output)
                    except json.JSONDecodeError:
                        # Unexpected stdout (shouldn't happen due to redirect) — log and keep waiting
                        self._debug_log(f"[non-json:{self.container_name}] {output!r}")
                        self._drain_stderr_nonblocking()
                        continue

                    if "error" in response and "ok" not in response:
                        self._debug_log(f"[bot-error:{self.container_name}] {response['error']}")
                        tb = response.get('traceback', '')
                        if tb:
                            self._debug_log(tb)
                        self._drain_stderr_nonblocking()
                        return None

                    self._drain_stderr_nonblocking()
                    return response.get("ok", None)

            elapsed = time.perf_counter() - start
            self._debug_log(f"[timeout] {self.container_name} exceeded {timeout:.3f}s (actual {elapsed:.3f}s)")
            self._drain_stderr_nonblocking()
            return None

        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            self._debug_log(f"[exception:{self.container_name}] {type(e).__name__}: {e}")
            return None

    def _drain_stderr_nonblocking(self):
        # Drain any available stderr without blocking
        try:
            while select.select([self.proc.stderr], [], [], 0)[0]:
                err_line = self.proc.stderr.readline()
                if err_line:
                    self._debug_log(f"[stderr:{self.container_name}] {err_line.rstrip()}")
        except Exception:
            pass

    def _debug_log(self, msg):
        print(msg)

    def shutdown(self):
        # Try graceful shutdown before trying to forcefully kill
        try:
            if self.proc.stdin and not self.proc.stdin.closed:
                try:
                    self.proc.stdin.close()
                except Exception:
                    pass
        except Exception:
            pass

        try:
            self.proc.terminate()
        except Exception:
            pass

        try:
            self.proc.wait(timeout=3)
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass
            try:
                self.proc.wait(timeout=2)
            except Exception:
                pass

        try:
            subprocess.run(["docker", "rm", "-f", self.container_name],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

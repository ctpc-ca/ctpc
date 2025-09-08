import subprocess, json, select, traceback, sys, uuid

class PersistentDockerBot:
    def __init__(self, bot_code, container_name_prefix):
        # Unique name per instance
        self.container_name = f"{container_name_prefix}-{uuid.uuid4().hex[:8]}"
        self.bot_code = bot_code

        # Clean up old leftovers with same name
        subprocess.run(["docker","rm","-f", self.container_name],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        docker_program_code = "\n".join([
            "import sys, json, types, traceback",
            "namespace = types.SimpleNamespace()",
            "code = []",
            "while True:",
            "    line = sys.stdin.readline()",
            "    if line.strip() == '__END__': break",
            "    code.append(line)",
            "exec(compile(''.join(code), '<stdin>', 'exec'), namespace.__dict__)",
            "while True:",
            "    line = sys.stdin.readline()",
            "    if not line: break",
            "    try:",
            "        raw = json.loads(line)",
            "        state, player = raw",
            "        result = namespace.move(state, player)",
            "        print(json.dumps({ 'ok': result }), flush=True)",
            "    except Exception as e:",
            "        error_msg = f\"{type(e).__name__}: {str(e)}\"",
            "        tb = traceback.format_exc()",
            "        print(json.dumps({ 'error': error_msg, 'traceback': tb }), flush=True)"
        ])

        self.proc = subprocess.Popen(
            [
                "docker","run","-i","--rm",
                "--name", self.container_name,
                "--label","ctpc=bot",
                "--network","none",
                "--memory","128m","--memory-swap","128m",
                "--oom-kill-disable=false",
                "--cpus","0.5",
                "--pids-limit","64",
                "--read-only",
                "--security-opt","no-new-privileges",
                "--cap-drop=ALL",
                "--tmpfs","/tmp:exec,nosuid,nodev,size=64m",
                "--ulimit","nofile=64:64",
                "--ulimit","nproc=32:32",
                "--device-read-bps","/dev/null:1mb",
                "--device-read-iops","/dev/null:10",
                "bot-runner",
                "env","PYTHONPATH=/app",
                "python3","-u","-c", docker_program_code
            ],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        self.proc.stdin.write(self.bot_code + "\n__END__\n")
        self.proc.stdin.flush()

    def send_state(self, state, player):
        try:
            msg = json.dumps([state, player]) + "\n"
            self.proc.stdin.write(msg)
            self.proc.stdin.flush()

            if select.select([self.proc.stdout], [], [], 1.25)[0]:
                output = self.proc.stdout.readline().strip()

                if not output:
                    print("[!] Empty output from bot.")
                    self._print_stderr_lines()
                    return None

                try:
                    response = json.loads(output)
                except json.JSONDecodeError as e:
                    print(f"[!] JSON decode error: {e}")
                    print(f"[!] Bot stdout: {repr(output)}")
                    self._print_stderr_lines()
                    return None

                if "error" in response:
                    print(f"[!] Bot error: {response['error']}")
                    print(f"[!] Traceback: {response.get('traceback', '')}")
                    self._print_stderr_lines()
                    return None

                self._print_stderr_lines()
                return response["ok"]

            else:
                print(f"[!] Bot {self.container_name} timed out.")
                self._print_stderr_lines()
                return None

        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            print(json.dumps({'error': f"{type(e).__name__}: {str(e)}"}), flush=True)

    def _print_stderr_lines(self):
        while select.select([self.proc.stderr], [], [], 0)[0]:
            err_line = self.proc.stderr.readline()
            if err_line:
                print(f"[stderr] {err_line.strip()}")

    def shutdown(self):
        try:
            if self.proc.stdin and not self.proc.stdin.closed:
                self.proc.stdin.close()
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


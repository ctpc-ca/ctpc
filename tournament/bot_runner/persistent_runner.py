import subprocess
import json
import select

class PersistentDockerBot:
    def __init__(self, bot_code, container_name):
        self.container_name = container_name
        self.bot_code = bot_code

        subprocess.run([
            "docker", "rm", "-f", self.container_name
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        docker_program_code = "\n".join([
            "import sys, json, types",
            "namespace = types.SimpleNamespace()",
            "code = []",
            "while True:",
            "    line = sys.stdin.readline()",
            "    if line.strip() == '__END__': break",
            "    code.append(line)",
            "exec(compile(''.join(code), '<stdin>', 'exec'), namespace.__dict__)",
            "while True:",
            "    try:",
            "        raw = json.loads(sys.stdin.readline())",
            "        state, player = raw",
            "        result = namespace.move(state, player)",
            "        print(json.dumps({ 'ok': result }), flush=True)",
            "    except Exception as e:",
            "        print(json.dumps({ 'error': str(e) }), flush=True)"
        ])

        self.proc = subprocess.Popen(
            [
                "docker", "run", "-i", "--rm",
                "--name", self.container_name,
                "--network", "none",
                "--memory", "128m",
                "--memory-swap", "128m",
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
                "bot-runner", "python3", "-u", "-c", docker_program_code
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        self.proc.stdin.write(self.bot_code + "\n__END__\n")
        self.proc.stdin.flush()

    def send_state(self, state, player):
        try:
            msg = json.dumps([state, player]) + "\n"
            self.proc.stdin.write(msg)
            self.proc.stdin.flush()

            if select.select([self.proc.stdout], [], [], 1)[0]:
                output = self.proc.stdout.readline()
                response = json.loads(output.strip())
                if "error" in response:
                    print(f"[!] Bot error: {response['error']}")
                    return None
                return response["ok"]
            else:
                print(f"[!] Bot {self.container_name} timed out.")
                return None

        except Exception as e:
            print(f"[!] Exception in send_state: {e}")
            return None

    def shutdown(self):
        self.proc.kill()

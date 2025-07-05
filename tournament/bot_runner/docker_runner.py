import subprocess
import json
from typing import Optional

def run_bot_in_docker(bot_code: str, game_state: dict) -> Optional[dict]:
    try:
        # Prepare JSON input combining code + game state
        docker_input = json.dumps({
            "bot_code": bot_code,
            "game_state": game_state
        }).encode()

        result = subprocess.run(
            [
                "docker", "run", "--rm", "-i",
                "--network", "none",
                "--memory", "128m",
                "--memory-swap", "128m",
                "--oom-kill-disable=false",
                "--cpus", "0.5",
                "--pids-limit", "64",
                "--read-only",
                "--security-opt", "no-new-privileges",
                "--cap-drop=ALL",
                "--tmpfs", "/bot:exec,nosuid,nodev,size=64m",
                "--ulimit", "nofile=64:64",
                "--ulimit", "nproc=32:32",
                "--device-read-bps", "/dev/null:1mb",
                "--device-read-iops", "/dev/null:10",
                "bot-runner"
            ],
            input=docker_input,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=1
        )

        if result.returncode != 0:
            print("Bot stderr:", result.stderr.decode())
            return None

        output = json.loads(result.stdout.decode())
        return output.get("result")

    except subprocess.TimeoutExpired:
        print("[!] Bot timed out")
        return None

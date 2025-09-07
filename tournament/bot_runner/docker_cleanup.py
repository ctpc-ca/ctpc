import subprocess

def clean_previous_bot_containers(force=False):
    cmd = 'docker ps -aq --filter label=ctpc=bot --filter status=exited | xargs -r docker rm'
    if force:
        cmd = 'docker ps -aq --filter label=ctpc=bot | xargs -r docker rm -f'
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

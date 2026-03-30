import os
import subprocess


def run_backup(user_path: str) -> None:
    os.system("tar -czf backup.tgz " + user_path)


def preview_file(filename: str) -> None:
    subprocess.run(f"type {filename}", shell=True)

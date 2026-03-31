from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

from shared.runtime_settings import load_config, save_config


DEFAULT_CONTAINER = "vsh-sonarqube"
DEFAULT_IMAGE = "sonarqube:community"
DEFAULT_URL = "http://127.0.0.1:9000"
DEFAULT_PROJECT_KEY = "vsh-local"
DEFAULT_TOKEN_NAME = "vsh-local-token"


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def ensure_container_running(container_name: str, image: str) -> None:
    run(["docker", "pull", image])

    existing = run(["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"], check=False)
    names = {line.strip() for line in existing.stdout.splitlines() if line.strip()}
    if container_name in names:
        run(["docker", "start", container_name], check=False)
        return

    run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            container_name,
            "-p",
            "9000:9000",
            "-v",
            "vsh_sonarqube_data:/opt/sonarqube/data",
            "-v",
            "vsh_sonarqube_logs:/opt/sonarqube/logs",
            "-v",
            "vsh_sonarqube_extensions:/opt/sonarqube/extensions",
            image,
        ]
    )


def wait_until_ready(base_url: str, timeout_sec: int = 600) -> None:
    deadline = time.time() + timeout_sec
    last_text = ""
    while time.time() < deadline:
        try:
            res = requests.get(f"{base_url}/api/system/status", timeout=10)
            if res.ok:
                payload = res.json()
                status = payload.get("status")
                if status == "UP":
                    return
                last_text = json.dumps(payload, ensure_ascii=False)
        except Exception as exc:
            last_text = str(exc)
        time.sleep(5)
    raise RuntimeError(f"SonarQube did not become ready in time. Last response: {last_text}")


def generate_user_token(base_url: str, token_name: str) -> str:
    auth = HTTPBasicAuth("admin", "admin")
    res = requests.post(
        f"{base_url}/api/user_tokens/generate",
        data={"name": token_name},
        auth=auth,
        timeout=20,
    )
    if not res.ok:
        raise RuntimeError(f"Token generation failed: {res.status_code} {res.text}")
    payload = res.json()
    token = payload.get("token")
    if not token:
        raise RuntimeError(f"Token response did not include a token: {payload}")
    return token


def ensure_project(base_url: str, token: str, project_key: str) -> None:
    auth = HTTPBasicAuth(token, "")
    search = requests.get(
        f"{base_url}/api/projects/search",
        params={"projects": project_key},
        auth=auth,
        timeout=20,
    )
    if search.ok and search.json().get("paging", {}).get("total", 0) > 0:
        return

    create = requests.post(
        f"{base_url}/api/projects/create",
        data={"name": project_key, "project": project_key},
        auth=auth,
        timeout=20,
    )
    if not create.ok:
        raise RuntimeError(f"Project creation failed: {create.status_code} {create.text}")


def update_vsh_config(base_url: str, token: str, project_key: str) -> Path:
    cfg = load_config()
    cfg.setdefault("llm", {})["enable_l3"] = True
    cfg.setdefault("l3", {})["sonar_url"] = base_url
    cfg["l3"]["sonar_token"] = token
    cfg["l3"]["sonar_org"] = ""
    cfg["l3"]["sonar_project_key"] = project_key
    saved = save_config(cfg)
    from shared.runtime_settings import CONFIG_PATH

    return CONFIG_PATH


def main() -> int:
    parser = argparse.ArgumentParser(description="Start a local SonarQube Docker container and wire VSH to it.")
    parser.add_argument("--container-name", default=DEFAULT_CONTAINER)
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--project-key", default=DEFAULT_PROJECT_KEY)
    parser.add_argument("--token-name", default=DEFAULT_TOKEN_NAME)
    args = parser.parse_args()

    ensure_container_running(args.container_name, args.image)
    wait_until_ready(args.url)
    token = generate_user_token(args.url, args.token_name)
    ensure_project(args.url, token, args.project_key)
    config_path = update_vsh_config(args.url, token, args.project_key)

    print(json.dumps(
        {
            "status": "ok",
            "sonar_url": args.url,
            "project_key": args.project_key,
            "token_name": args.token_name,
            "config_path": str(config_path),
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())

from __future__ import annotations

import base64
import json
import os
import requests

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
REPO = "lucianawork3-png/task-kanban"
FILE_PATH = "tasks.json"
API_BASE = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"

def _headers():
    return {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

def load_tasks() -> list[dict]:
    r = requests.get(API_BASE, headers=_headers())
    if r.status_code == 404:
        return [], None
    r.raise_for_status()
    data = r.json()
    content = base64.b64decode(data["content"]).decode()
    return json.loads(content).get("tasks", []), data["sha"]

def save_tasks(tasks: list[dict], sha: str | None):
    content = base64.b64encode(json.dumps({"tasks": tasks}, indent=2).encode()).decode()
    body = {"message": "update tasks", "content": content}
    if sha:
        body["sha"] = sha
    requests.put(API_BASE, headers=_headers(), json=body).raise_for_status()

def upload_attachment(task_id: str, filename: str, data: bytes) -> dict:
    path = f"attachments/{task_id}/{filename}"
    api_url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    content = base64.b64encode(data).decode()
    r = requests.put(api_url, headers=_headers(), json={
        "message": f"attach {filename} to task {task_id}",
        "content": content,
    })
    r.raise_for_status()
    return {
        "name": filename,
        "path": path,
        "url": f"https://raw.githubusercontent.com/{REPO}/main/{path}",
    }

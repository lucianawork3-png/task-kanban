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
    r.raise_for_status()
    data = r.json()
    content = base64.b64decode(data["content"]).decode()
    return json.loads(content).get("tasks", []), data["sha"]

def save_tasks(tasks: list[dict], sha: str):
    content = base64.b64encode(json.dumps({"tasks": tasks}, indent=2).encode()).decode()
    requests.put(API_BASE, headers=_headers(), json={
        "message": "update tasks",
        "content": content,
        "sha": sha,
    }).raise_for_status()

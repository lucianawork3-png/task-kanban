import json
import os
from datetime import date
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

COLUMNS = ["Backlog", "This Week", "In Progress", "Done"]

SYSTEM_PROMPT = f"""You are a task management assistant controlling a Kanban board with columns: {", ".join(COLUMNS)}.

Parse the user's message and return ONLY a valid JSON object with:
- action: one of "add", "move", "delete", "edit", "none"
- task_title: the task title (for add/move/delete/edit — use the user's words exactly)
- column: target column name (for add: default "Backlog"; for move: the destination column)
- notes: optional extra notes for the task (or null)
- reply: a short friendly confirmation message to show the user

For "move" and "delete", match the task by title (fuzzy is fine).
For "none", just return a helpful reply with no board changes.
Return raw JSON only, no markdown fences."""


def parse_command(user_message: str, tasks: list[dict]) -> dict:
    task_list = "\n".join(
        f"- [{t['column']}] {t['title']}" for t in tasks
    ) or "(no tasks yet)"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Today: {date.today().isoformat()}\n\nCurrent tasks:\n{task_list}\n\nMessage: {user_message}"
        }],
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)

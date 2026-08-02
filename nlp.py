import json
import os
from datetime import date
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

COLUMNS = ["Backlog", "This Week", "In Progress", "Done"]

WEEK_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

ROUTINE = """Weekday routine, Monday-Thursday: wake 07:10, morning ritual, walk the dog, personal time,
get ready 09:45, leave for work 10:45. Two work blocks: 11:00-13:30 and 14:30-17:30 (lunch 13:30-14:30).
Finish work 17:30, evening routine, bed 22:00.
Friday: lighter day — only the morning work block (~11:00-13:30) is realistically available; treat it as
low-capacity, good for wrap-up/admin/quick items rather than deep work.
Saturday and Sunday: no work time at all — never schedule tasks on these days."""

PLAN_SYSTEM_PROMPT = f"""You are a time-management expert building Leticia's plan for the coming week.

Her routine:
{ROUTINE}

Available work windows for scheduling:
- Monday-Thursday: 11:00-13:30 and 14:30-17:30
- Friday: 11:00-13:30 only
- Saturday/Sunday: none

You'll be given her current active tasks (id, title, tag/project, column, deadline, notes).
For each task, decide:
- day: one of {", ".join(WEEK_DAYS)}, or null if it doesn't fit this week
- start_time: "HH:MM" (24h) falling inside that day's available window(s) above, or null if day is null
- duration_min: a reasonable estimate for the task — one of 30, 45, 60, or 90
- reason: a short one-sentence rationale

Rules:
- Tasks with a deadline this week, or already overdue, are scheduled earliest and get priority for a slot.
- Never give two tasks on the same day overlapping start_time/duration_min — pack them back-to-back
  within the available windows instead.
- Don't overload a day: Monday-Thursday can reasonably hold a handful of focused tasks across the two
  work blocks (roughly 3-4 total). Friday is lighter — roughly 1-2 quick/admin tasks only.
- Group tasks that share a tag/project on the same day where reasonable, to reduce context-switching.
- If there isn't enough weekly capacity for everything, leave the lowest-priority tasks unassigned
  (day, start_time: null) rather than overloading any single day.

Return ONLY a valid JSON object:
{{"plan": [{{"id": "<task id>", "day": "Monday"|"Tuesday"|"Wednesday"|"Thursday"|"Friday"|null, "start_time": "HH:MM"|null, "duration_min": 30|45|60|90, "reason": "<short reason, one sentence>"}}, ...]}}
One entry per task given, in the same order. Return raw JSON only, no markdown fences."""


def plan_week(tasks: list[dict]) -> dict:
    task_list = "\n".join(
        f"- id={t['id']} | {t['title']} | tag: {t.get('project', 'General')} | column: {t['column']} | "
        f"deadline: {t.get('deadline') or 'none'} | notes: {t.get('notes') or 'none'}"
        for t in tasks
    ) or "(no active tasks)"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=PLAN_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"Today: {date.today().isoformat()} ({date.today().strftime('%A')})\n\n"
                f"Active tasks:\n{task_list}"
            ),
        }],
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)

SYSTEM_PROMPT = f"""You are a task management assistant controlling a Kanban board with columns: {", ".join(COLUMNS)}.

Parse the user's message and return ONLY a valid JSON object with:
- action: one of "add", "move", "delete", "edit", "none"
- task_title: the task title (for add/move/delete/edit — use the user's words exactly)
- column: target column name (for add: default "Backlog"; for move: the destination column)
- notes: optional extra notes for the task (or null) — only for "edit" (e.g. "add a note to X saying ...")
- project: a short project/theme name (e.g. "PA", "Riel Collective") — only for "edit", when the user
  explicitly asks to retag an existing task (e.g. "tag X as PA"). Never set this for "add" — tagging for
  new tasks is handled separately after this response, so leave it null when action is "add".
  If reusing an existing project for an edit, match one from "Existing projects" below exactly.
- reply: a short friendly confirmation message to show the user

For "move" and "delete", match the task by title (fuzzy is fine).
For "none", just return a helpful reply with no board changes.
Return raw JSON only, no markdown fences."""


def parse_command(user_message: str, tasks: list[dict]) -> dict:
    task_list = "\n".join(
        f"- [{t['column']}] {t['title']} (project: {t.get('project', 'General')})" for t in tasks
    ) or "(no tasks yet)"

    existing_projects = sorted({t.get("project", "General") for t in tasks}) or ["General"]

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"Today: {date.today().isoformat()}\n\n"
                f"Existing projects: {', '.join(existing_projects)}\n\n"
                f"Current tasks:\n{task_list}\n\nMessage: {user_message}"
            )
        }],
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)

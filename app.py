import uuid
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

import nlp
import storage

st.set_page_config(page_title="Task Board", page_icon="✅", layout="wide")

COLUMNS = ["Backlog", "This Week", "In Progress", "Done"]
COL_COLORS = {
    "Backlog": "#e8e8e8",
    "This Week": "#fff3cd",
    "In Progress": "#cce5ff",
    "Done": "#d4edda",
}

# ── Load tasks ────────────────────────────────────────────────────────────────

def refresh_tasks():
    tasks, sha = storage.load_tasks()
    st.session_state.tasks = tasks
    st.session_state.sha = sha

if "tasks" not in st.session_state:
    refresh_tasks()

if "messages" not in st.session_state:
    st.session_state.messages = []


def save(tasks):
    storage.save_tasks(tasks, st.session_state.sha)
    refresh_tasks()


# ── Board ─────────────────────────────────────────────────────────────────────

st.title("✅ Task Board")

cols = st.columns(4)
for col_ui, col_name in zip(cols, COLUMNS):
    col_tasks = [t for t in st.session_state.tasks if t["column"] == col_name]
    with col_ui:
        st.markdown(f"### {col_name}")
        st.caption(f"{len(col_tasks)} task{'s' if len(col_tasks) != 1 else ''}")
        for task in col_tasks:
            with st.container(border=True):
                st.markdown(f"**{task['title']}**")
                if task.get("notes"):
                    st.caption(task["notes"])
                move_cols = [c for c in COLUMNS if c != col_name]
                btn_cols = st.columns(len(move_cols) + 1)
                for i, dest in enumerate(move_cols):
                    if btn_cols[i].button(f"→ {dest}", key=f"mv_{task['id']}_{dest}"):
                        for t in st.session_state.tasks:
                            if t["id"] == task["id"]:
                                t["column"] = dest
                        save(st.session_state.tasks)
                        st.rerun()
                if btn_cols[-1].button("✕", key=f"del_{task['id']}"):
                    st.session_state.tasks = [t for t in st.session_state.tasks if t["id"] != task["id"]]
                    save(st.session_state.tasks)
                    st.rerun()

# ── Chat ──────────────────────────────────────────────────────────────────────

st.divider()
st.subheader("Chat")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("e.g. 'add task: review proposals' or 'move review to in progress'")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.spinner("Thinking..."):
        try:
            cmd = nlp.parse_command(user_input, st.session_state.tasks)
        except Exception as e:
            cmd = {"action": "none", "reply": f"Error: {e}"}

    action = cmd.get("action", "none")
    tasks = list(st.session_state.tasks)

    if action == "add":
        tasks.append({
            "id": str(uuid.uuid4())[:8],
            "title": cmd.get("task_title", user_input),
            "column": cmd.get("column", "Backlog"),
            "notes": cmd.get("notes"),
        })
        save(tasks)

    elif action == "move":
        target = cmd.get("task_title", "").lower()
        for t in tasks:
            if target in t["title"].lower():
                t["column"] = cmd.get("column", t["column"])
                break
        save(tasks)

    elif action == "delete":
        target = cmd.get("task_title", "").lower()
        tasks = [t for t in tasks if target not in t["title"].lower()]
        save(tasks)

    elif action == "edit":
        target = cmd.get("task_title", "").lower()
        for t in tasks:
            if target in t["title"].lower():
                if cmd.get("notes"):
                    t["notes"] = cmd["notes"]
                break
        save(tasks)

    reply = cmd.get("reply", "Done!")
    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)

    st.rerun()

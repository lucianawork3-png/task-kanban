import math
import uuid
from datetime import date, datetime, timedelta
from xml.sax.saxutils import escape as xml_escape
from zoneinfo import ZoneInfo

import streamlit as st
import streamlit.components.v1 as components
from streamlit_sortables import sort_items
from dotenv import load_dotenv

load_dotenv()

import holidays as holidays_lib

import nlp
import storage
from nlp import WEEK_DAYS

LISBON = ZoneInfo("Europe/Lisbon")


def today_lisbon():
    return datetime.now(LISBON).date()


GRID_DAYS = WEEK_DAYS + ["Saturday", "Sunday"]
PT_HOLIDAYS = holidays_lib.Portugal(years=range(today_lisbon().year, today_lisbon().year + 2))

try:
    import calendar_google
    HAS_CALENDAR = True
except ImportError:
    HAS_CALENDAR = False

st.set_page_config(page_title="Task Board", page_icon="✅", layout="wide")

if "light_mode" not in st.session_state:
    st.session_state.light_mode = False
LIGHT = st.session_state.light_mode

ACCENT = "#D4A037"
ACCENT_GRADIENT = "linear-gradient(135deg, #D4A037, #E06B8A, #A78BFA)"

THEME = {
    "app_bg": "#F7F5F0" if LIGHT else "#0D0B10",
    "panel_bg": "#FFFEFB" if LIGHT else "#17151B",
    "panel_bg_hover": "#FAF8F3" if LIGHT else "#1D1A21",
    "border": "#E9E5DB" if LIGHT else "rgba(255,255,255,0.09)",
    "text": "#2A2724" if LIGHT else "#F1EEE8",
    "muted": "#8A8578" if LIGHT else "#9B96A3",
    "card_bg": "#FFFEFB" if LIGHT else "rgba(255,255,255,0.035)",
    "card_border": "#EDE9DF" if LIGHT else "rgba(255,255,255,0.08)",
    "grid_line": "#EFEBE2" if LIGHT else "rgba(255,255,255,0.06)",
    "col_border": "#E9E5DB" if LIGHT else "rgba(255,255,255,0.09)",
    "axis_text": "#A39D8E" if LIGHT else "#8A8594",
    "shadow": "0 2px 10px rgba(0,0,0,0.04)" if LIGHT else "0 8px 24px rgba(0,0,0,0.32)",
    "accent": ACCENT,
}

CSS_TEMPLATE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Fraunces:opsz,wght@9..144,500;9..144,600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif !important; }
    div[data-testid="stButton"] button, div[data-testid="stFormSubmitButton"] button {
        border-radius: 999px !important;
        padding: 0.5rem 1.3rem !important;
        font-weight: 600 !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
    }
    div[data-testid="stButton"] button:hover, div[data-testid="stFormSubmitButton"] button:hover {
        transform: translateY(-1px);
        box-shadow: __SHADOW__;
    }
    [data-testid="stAppViewContainer"], .stApp {
        background: __APP_BG__ !important;
        __GLOW__
    }
    [data-testid="stHeader"] { background: transparent !important; }
    [data-testid="stMarkdownContainer"] p, [data-testid="stCaptionContainer"], label,
    [data-testid="stWidgetLabel"] p { color: __TEXT__ !important; }
    .stTextInput input, .stTextArea textarea, .stDateInput input,
    div[data-baseweb="select"] > div, div[data-baseweb="input"] {
        background: __PANEL_BG__ !important; color: __TEXT__ !important;
        border-color: __BORDER__ !important;
    }
    [data-testid="stExpander"] {
        background: __PANEL_BG__ !important; border: 1px solid __BORDER__ !important;
        border-radius: 12px !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        border-radius: 12px !important;
        border: 1px solid __BORDER__ !important;
        background: __PANEL_BG__ !important;
        box-shadow: __SHADOW__;
        transition: background 0.15s ease, border-color 0.15s ease;
    }
    [data-testid="stVerticalBlockBorderWrapper"] > div:hover {
        background: __PANEL_BG_HOVER__ !important;
        border-color: __ACCENT__66 !important;
    }
    h1, h2, h3 {
        font-family: 'Fraunces', 'Inter', serif !important;
        font-weight: 600 !important; color: __TEXT__; letter-spacing: -0.01em;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] p {
        color: __ACCENT__ !important;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        border-bottom-color: __ACCENT__ !important;
    }
    .lvr-banner {
        margin-bottom: 14px;
    }
    .lvr-banner .crumb {
        color: __MUTED__; font-size: 0.75rem; margin-bottom: 6px;
        text-transform: uppercase; letter-spacing: 0.14em; font-weight: 600;
    }
    .lvr-banner .crumb::before {
        content: "●"; color: __ACCENT__; font-size: 0.55rem;
        margin-right: 7px; vertical-align: middle;
    }
    .lvr-banner h1 {
        font-family: 'Fraunces', 'Inter', serif !important;
        margin: 0 0 18px 0; font-size: 2.15rem; font-weight: 600 !important;
        color: __TEXT__; letter-spacing: -0.01em;
        border-bottom: 1px solid transparent;
        border-image: linear-gradient(90deg, __ACCENT__, transparent) 1;
        padding-bottom: 18px;
    }
    .tag-pill {
        display: inline-block; padding: 2px 9px; border-radius: 999px;
        font-size: 0.75rem; font-weight: 600;
    }
</style>
"""
st.markdown(
    CSS_TEMPLATE
    .replace("__APP_BG__", THEME["app_bg"])
    .replace("__GLOW__", "" if LIGHT else
             "background-image: radial-gradient(ellipse 900px 500px at 15% -5%, rgba(212,160,55,0.10), transparent 60%), "
             "radial-gradient(ellipse 700px 500px at 100% 10%, rgba(167,139,250,0.08), transparent 60%);")
    .replace("__PANEL_BG_HOVER__", THEME["panel_bg_hover"])
    .replace("__PANEL_BG__", THEME["panel_bg"])
    .replace("__BORDER__", THEME["border"])
    .replace("__TEXT__", THEME["text"])
    .replace("__MUTED__", THEME["muted"])
    .replace("__SHADOW__", THEME["shadow"])
    .replace("__ACCENT__", THEME["accent"]),
    unsafe_allow_html=True,
)

KANBAN_STYLE_TEMPLATE = """
.sortable-component { background: transparent; }
.sortable-container {
    background: __PANEL_BG__ !important; border: 1px solid __BORDER__; border-radius: 14px;
    padding: 14px; min-height: 160px;
}
.sortable-container-header {
    background: __PANEL_BG__ !important;
    font-weight: 700; color: __TEXT__ !important; font-size: 0.85rem;
    padding-bottom: 10px; margin-bottom: 10px; border-bottom: 1px solid __BORDER__;
}
.sortable-container-body {
    background: __PANEL_BG__ !important;
}
.sortable-item {
    background: __CARD_BG__ !important; border: 1px solid __CARD_BORDER__; border-radius: 10px;
    padding: 11px 13px; margin-bottom: 9px; color: __TEXT__ !important; font-size: 0.82rem;
    line-height: 1.55; white-space: pre-line; cursor: grab; box-shadow: __SHADOW__;
}
.sortable-item:hover { border-color: __ACCENT__99; }
"""
KANBAN_STYLE = (
    KANBAN_STYLE_TEMPLATE
    .replace("__PANEL_BG__", THEME["panel_bg"])
    .replace("__BORDER__", THEME["border"])
    .replace("__TEXT__", THEME["text"])
    .replace("__CARD_BG__", THEME["card_bg"])
    .replace("__CARD_BORDER__", THEME["card_border"])
    .replace("__SHADOW__", THEME["shadow"])
    .replace("__ACCENT__", THEME["accent"])
)


def darken(hex_color: str, amount: float = 0.45) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    r, g, b = int(r * (1 - amount)), int(g * (1 - amount)), int(b * (1 - amount))
    return f"#{r:02x}{g:02x}{b:02x}"


def tag_pill(name: str) -> str:
    color = project_color(name)
    text_color = darken(color) if LIGHT else color
    bg_alpha = "20" if LIGHT else "26"
    return (
        f'<span class="tag-pill" style="background:{color}{bg_alpha};color:{text_color};">'
        f'{xml_escape(name)}</span>'
    )

COLUMNS = ["Backlog", "This Week", "In Progress", "Done"]
COLUMN_EMOJI = {"Backlog": "📥", "This Week": "🗓️", "In Progress": "🔨", "Done": "✅"}
DAY_SHORT = {"Monday": "Mon", "Tuesday": "Tue", "Wednesday": "Wed", "Thursday": "Thu", "Friday": "Fri"}

PROJECT_PALETTE = [
    "#D4A037",  # gold
    "#E06B8A",  # pink
    "#00BCD4",  # cyan
    "#7FB88F",  # sage green
    "#E0954B",  # muted orange
    "#A78BFA",  # purple
    "#4FB8AE",  # teal
    "#B0A99C",  # warm gray
]


DOT_EMOJI = ["🟡", "🔴", "🔵", "🟢", "🟠", "🟣", "🟤", "⚪"]


def project_color(name: str) -> str:
    return PROJECT_PALETTE[hash(name) % len(PROJECT_PALETTE)]


def project_dot(name: str) -> str:
    return DOT_EMOJI[hash(name) % len(DOT_EMOJI)]


def deadline_badge(deadline):
    if not deadline:
        return None
    try:
        d = date.fromisoformat(deadline)
    except ValueError:
        return None
    days = (d - today_lisbon()).days
    label = d.strftime("%d %b")
    if days < 0:
        return f"⚠️ Overdue ({label})"
    if days <= 3:
        return f"⏳ Due {label}"
    return f"📅 {label}"


# ── Load tasks ────────────────────────────────────────────────────────────────

def refresh_tasks():
    tasks, sha = storage.load_tasks()
    st.session_state.tasks = tasks
    st.session_state.sha = sha

if "tasks" not in st.session_state:
    refresh_tasks()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "new_task_flow" not in st.session_state:
    st.session_state.new_task_flow = None

if "proposed_week_plan" not in st.session_state:
    st.session_state.proposed_week_plan = None


def save(tasks):
    storage.save_tasks(tasks, st.session_state.sha)
    refresh_tasks()


def push_assistant(text: str):
    st.session_state.messages.append({"role": "assistant", "content": text})


def existing_tags():
    return sorted({t.get("project", "General") for t in st.session_state.tasks if t.get("project")})


def render_mind_map(tasks, theme):
    projects = {}
    for t in tasks:
        projects.setdefault(t.get("project", "General"), []).append(t)
    project_names = sorted(projects.keys())

    width, height = 980, 720
    cx, cy = width / 2, height / 2
    hub_r, tag_r, leaf_r = 44, 190, 130
    text_color = theme["text"]
    muted_color = theme["muted"]

    svg = [
        f'<svg width="100%" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg" style="background:{theme["app_bg"]};border-radius:16px;">',
        '<defs>'
        '<filter id="glow" x="-60%" y="-60%" width="220%" height="220%">'
        '<feGaussianBlur stdDeviation="5" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>'
        '</filter>'
        '<linearGradient id="hubGrad" x1="0%" y1="0%" x2="100%" y2="100%">'
        '<stop offset="0%" stop-color="#D4A037"/>'
        '<stop offset="55%" stop-color="#E06B8A"/>'
        '<stop offset="100%" stop-color="#A78BFA"/>'
        '</linearGradient>'
        '</defs>',
    ]

    if not project_names:
        svg.append(
            f'<text x="{cx}" y="{cy}" fill="{muted_color}" font-size="18" text-anchor="middle">'
            '✨ Nothing going on yet — add a task to see it here.</text>'
        )
        svg.append("</svg>")
        return "".join(svg)

    n = len(project_names)
    angle_step = 2 * math.pi / n
    for i, project in enumerate(project_names):
        angle = -math.pi / 2 + i * angle_step
        tx, ty = cx + tag_r * math.cos(angle), cy + tag_r * math.sin(angle)
        color = project_color(project)

        svg.append(
            f'<line x1="{cx}" y1="{cy}" x2="{tx:.1f}" y2="{ty:.1f}" '
            f'stroke="{color}" stroke-width="2" opacity="0.5"/>'
        )

        items = projects[project]
        k = len(items)
        spread = math.radians(min(60, 14 * k))
        for j, task in enumerate(items):
            leaf_angle = angle if k == 1 else angle - spread / 2 + spread * j / (k - 1)
            lx, ly = tx + leaf_r * math.cos(leaf_angle), ty + leaf_r * math.sin(leaf_angle)
            is_done = task["column"] == "Done"
            badge = deadline_badge(task.get("deadline")) or ""
            dot = "🔴" if badge.startswith("⚠️") and not is_done else ("🟠" if badge.startswith("⏳") and not is_done else "")
            title_raw = task["title"]
            title_disp = xml_escape(title_raw if len(title_raw) <= 26 else title_raw[:24] + "…")
            opacity = "0.45" if is_done else "0.95"
            dash = 'stroke-dasharray="3 3"' if is_done else ""

            svg.append(
                f'<line x1="{tx:.1f}" y1="{ty:.1f}" x2="{lx:.1f}" y2="{ly:.1f}" '
                f'stroke="{color}" stroke-width="1.3" opacity="0.35" {dash}/>'
            )
            svg.append(
                f'<g><title>{xml_escape(title_raw)}</title>'
                f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="6" fill="{color}" opacity="{opacity}"/>'
                f'<text x="{lx:.1f}" y="{ly - 11:.1f}" fill="{text_color}" font-size="11" '
                f'text-anchor="middle" opacity="{opacity}">{dot} {title_disp}</text></g>'
            )

        svg.append(
            f'<g filter="url(#glow)"><circle cx="{tx:.1f}" cy="{ty:.1f}" r="30" fill="{color}"/></g>'
            f'<text x="{tx:.1f}" y="{ty + 4:.1f}" fill="#0B0B0C" font-size="12" font-weight="700" '
            f'text-anchor="middle">{xml_escape(project)}</text>'
            f'<text x="{tx:.1f}" y="{ty + 44:.1f}" fill="{text_color}" font-size="10" opacity="0.6" '
            f'text-anchor="middle">{k} task{"s" if k != 1 else ""}</text>'
        )

    svg.append(
        f'<g filter="url(#glow)"><circle cx="{cx}" cy="{cy}" r="{hub_r}" fill="url(#hubGrad)"/></g>'
        f'<text x="{cx}" y="{cy + 5}" fill="#0B0B0C" font-size="15" font-weight="800" '
        f'text-anchor="middle">LMM</text>'
    )
    svg.append("</svg>")
    return "".join(svg)


def current_week_dates(offset=0):
    today = today_lisbon()
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=offset)
    return {GRID_DAYS[i]: monday + timedelta(days=i) for i in range(len(GRID_DAYS))}


@st.cache_data(ttl=300)
def load_calendar_events(monday_iso, sunday_iso):
    return calendar_google.list_events_between(date.fromisoformat(monday_iso), date.fromisoformat(sunday_iso))


def render_week_grid(tasks, plan_preview, week_dates, theme, calendar_events=None):
    grid_start_hour, grid_end_hour = 5, 23
    row_px = 56
    body_height = (grid_end_hour - grid_start_hour) * row_px
    text_color, muted_color = theme["text"], theme["axis_text"]
    CAL_COLOR = "#7B8794"
    HOLIDAY_COLOR = "#C0392B"

    def effective(task):
        if plan_preview and task["id"] in plan_preview:
            p = plan_preview[task["id"]]
            return p.get("day"), p.get("start_time"), p.get("duration_min") or 45
        return task.get("day"), task.get("start_time"), task.get("duration_min") or 45

    by_day_timed = {d: [] for d in GRID_DAYS}
    by_day_allday = {d: [] for d in GRID_DAYS}
    for t in tasks:
        day, start_time, dur = effective(t)
        if day not in WEEK_DAYS:
            continue
        if start_time:
            by_day_timed[day].append((t, start_time, dur))
        else:
            by_day_allday[day].append(t)

    date_to_day = {v: k for k, v in week_dates.items()}
    cal_allday = {d: [] for d in GRID_DAYS}
    cal_timed = {d: [] for d in GRID_DAYS}
    for ev in (calendar_events or []):
        try:
            if ev["all_day"]:
                ev_date = date.fromisoformat(ev["start"][:10])
                day_name = date_to_day.get(ev_date)
                if day_name:
                    cal_allday[day_name].append(ev)
            else:
                start_dt = datetime.fromisoformat(ev["start"])
                day_name = date_to_day.get(start_dt.date())
                if day_name:
                    end_dt = datetime.fromisoformat(ev["end"])
                    dur = max(15, int((end_dt - start_dt).total_seconds() / 60))
                    cal_timed[day_name].append((ev, start_dt.strftime("%H:%M"), dur))
        except (ValueError, KeyError):
            continue

    html = [f'<div style="font-family:\'Inter\',-apple-system,sans-serif;color:{text_color};background:{theme["app_bg"]};">']

    html.append(
        f'<div style="display:flex;border-bottom:2px solid {theme["accent"]};padding-bottom:6px;margin-bottom:2px;">'
        '<div style="width:52px;flex-shrink:0;"></div>'
    )
    for d in GRID_DAYS:
        dt = week_dates[d]
        is_today = dt == today_lisbon()
        num_color = theme["accent"] if is_today else text_color
        holiday_name = PT_HOLIDAYS.get(dt)
        html.append(
            f'<div style="flex:1;padding-left:6px;">'
            f'<div style="font-size:11px;color:{muted_color};text-transform:uppercase;letter-spacing:0.05em;">{d[:3]}</div>'
            f'<div style="font-size:19px;font-weight:700;color:{num_color};">{dt.day}</div>'
            + (f'<div title="{xml_escape(holiday_name)}" style="font-size:10px;color:{HOLIDAY_COLOR};'
               f'font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'
               f'🇵🇹 {xml_escape(holiday_name[:16])}</div>' if holiday_name else '')
            + '</div>'
        )
    html.append('</div>')

    if any(by_day_allday.values()) or any(cal_allday.values()):
        html.append(
            f'<div style="display:flex;border-bottom:1px solid {theme["col_border"]};padding:4px 0;margin-bottom:2px;">'
            f'<div style="width:52px;flex-shrink:0;font-size:10px;color:{muted_color};">📌 All day</div>'
        )
        for d in GRID_DAYS:
            html.append('<div style="flex:1;padding:2px 4px;display:flex;flex-direction:column;gap:3px;">')
            for ev in cal_allday[d]:
                html.append(
                    f'<div title="{xml_escape(ev["title"])}" style="border-left:4px solid {CAL_COLOR};'
                    f'background:{CAL_COLOR}1A;border-radius:4px;padding:2px 6px;font-size:11px;'
                    f'font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'
                    f'📅 {xml_escape(ev["title"][:20])}</div>'
                )
            for t in by_day_allday[d]:
                color = project_color(t.get("project", "General"))
                html.append(
                    f'<div title="{xml_escape(t["title"])}" style="border-left:4px solid {color};'
                    f'background:{color}22;border-radius:4px;padding:2px 6px;font-size:11px;'
                    f'font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'
                    f'{xml_escape(t["title"][:22])}</div>'
                )
            html.append('</div>')
        html.append('</div>')

    html.append(f'<div id="hourgrid" style="display:flex;position:relative;height:{body_height}px;">')
    html.append('<div style="width:52px;flex-shrink:0;position:relative;">')
    for h in range(grid_start_hour, grid_end_hour + 1):
        top = (h - grid_start_hour) * row_px
        html.append(f'<div style="position:absolute;top:{top - 7}px;font-size:11px;color:{muted_color};">{h:02d}:00</div>')
    html.append('</div>')

    for d in GRID_DAYS:
        is_weekend = d in ("Saturday", "Sunday")
        col_bg = "rgba(123,135,148,0.05)" if is_weekend else "transparent"
        html.append(
            f'<div style="flex:1;position:relative;border-left:1px solid {theme["col_border"]};'
            f'height:{body_height}px;background:{col_bg};">'
        )
        for h in range(grid_start_hour, grid_end_hour + 1):
            top = (h - grid_start_hour) * row_px
            html.append(f'<div style="position:absolute;top:{top}px;left:0;right:0;border-top:1px solid {theme["grid_line"]};"></div>')
        for t, start_time, dur in by_day_timed[d]:
            try:
                hh, mm = map(int, start_time.split(":"))
            except (ValueError, AttributeError):
                continue
            start_min = hh * 60 + mm - grid_start_hour * 60
            top_px = start_min / 60 * row_px
            height_px = max(26, dur / 60 * row_px)
            color = project_color(t.get("project", "General"))
            is_done = t["column"] == "Done"
            html.append(
                f'<div title="{xml_escape(t["title"])}" style="position:absolute;top:{top_px:.0f}px;'
                f'height:{height_px:.0f}px;left:4px;right:4px;background:{color}33;'
                f'border-left:4px solid {color};border-radius:6px;padding:4px 6px;overflow:hidden;'
                f'font-size:12px;font-weight:600;opacity:{"0.5" if is_done else "1"};color:{text_color};">'
                f'{xml_escape(t["title"][:34])}</div>'
            )
        for ev, start_time, dur in cal_timed[d]:
            hh, mm = map(int, start_time.split(":"))
            start_min = hh * 60 + mm - grid_start_hour * 60
            top_px = start_min / 60 * row_px
            height_px = max(22, dur / 60 * row_px)
            html.append(
                f'<div title="{xml_escape(ev["title"])}" style="position:absolute;top:{top_px:.0f}px;'
                f'height:{height_px:.0f}px;left:4px;right:4px;background:{CAL_COLOR}22;'
                f'border-left:4px dashed {CAL_COLOR};border-radius:6px;padding:4px 6px;overflow:hidden;'
                f'font-size:12px;font-style:italic;color:{text_color};">'
                f'📅 {xml_escape(ev["title"][:30])}</div>'
            )
        html.append('</div>')
    html.append('</div></div>')
    html.append(
        '<script>'
        '(function(){'
        'var g = document.getElementById("hourgrid");'
        'if (g) { window.scrollTo(0, g.offsetTop + ' + str(max(0, 9 - grid_start_hour) * row_px) + ' - 40); }'
        '})();'
        '</script>'
    )
    return "".join(html)


def finalize_new_task(uploaded_file=None):
    flow = st.session_state.new_task_flow
    attachments = list(flow["attachments"])
    if uploaded_file is not None:
        att = storage.upload_attachment(flow["id"], uploaded_file.name, uploaded_file.getvalue())
        attachments.append(att)

    tasks = list(st.session_state.tasks)
    tasks.append({
        "id": flow["id"],
        "title": flow["title"],
        "column": flow["column"],
        "project": flow["tag"] or "General",
        "deadline": flow["deadline"],
        "notes": flow["notes"],
        "attachments": attachments,
        "day": None,
        "start_time": None,
        "duration_min": None,
    })
    save(tasks)
    st.session_state.new_task_flow = None
    push_assistant(f"Added **{flow['title']}** to {flow['column']} (tag: {flow['tag'] or 'General'}).")


# ── Board ─────────────────────────────────────────────────────────────────────

banner_col, toggle_col = st.columns([6, 1])
with banner_col:
    st.markdown(
        '<div class="lvr-banner"><div class="crumb">LMM</div><h1>✅ Task Board</h1></div>',
        unsafe_allow_html=True,
    )
with toggle_col:
    if st.button("☀️ Light" if not LIGHT else "🌙 Dark", key="theme_toggle"):
        st.session_state.light_mode = not LIGHT
        st.rerun()

tab_board, tab_big_picture, tab_week = st.tabs(["📋 Board", "🧠 Big Picture", "🗓️ Week Plan"])

with tab_board:
    with st.expander("➕ Add a card manually"):
        title = st.text_input("Title", key="manual_title")
        col1, col2 = st.columns(2)
        column = col1.selectbox("Column", COLUMNS, key="manual_column")
        tags = existing_tags()
        tag_options = tags + ["+ New tag"]
        tag_choice = col2.selectbox("Tag", tag_options, key="manual_tag_choice")
        new_tag = st.text_input("New tag name", key="manual_new_tag") if tag_choice == "+ New tag" else None
        has_deadline = st.checkbox("Set a deadline", key="manual_has_deadline")
        deadline_val = st.date_input("Deadline", value=today_lisbon(), key="manual_deadline") if has_deadline else None
        notes = st.text_area("Notes (optional)", key="manual_notes")
        uploaded = st.file_uploader("Attach a file (optional)", key="manual_uploader")
        if st.button("Add card", key="manual_add_btn", type="primary"):
            if title.strip():
                tag = (new_tag or "").strip() if tag_choice == "+ New tag" else tag_choice
                task_id = str(uuid.uuid4())[:8]
                attachments = []
                if uploaded is not None:
                    attachments.append(storage.upload_attachment(task_id, uploaded.name, uploaded.getvalue()))
                tasks = list(st.session_state.tasks)
                tasks.append({
                    "id": task_id,
                    "title": title.strip(),
                    "column": column,
                    "project": tag or "General",
                    "deadline": deadline_val.isoformat() if has_deadline and deadline_val else None,
                    "notes": notes.strip() or None,
                    "attachments": attachments,
                    "day": None,
                    "start_time": None,
                    "duration_min": None,
                })
                save(tasks)
                st.rerun()
            else:
                st.warning("Give the card a title first.")

    def kanban_card_label(task):
        prefix = ""
        badge = deadline_badge(task.get("deadline"))
        if badge and badge.startswith("⚠️"):
            prefix = "⚠️ "
        elif badge and badge.startswith("⏳"):
            prefix = "⏳ "
        clip = "📎 " if task.get("attachments") else ""
        tag = task.get("project", "General")
        return f"{prefix}{clip}{task['title']}\n{project_dot(tag)} {tag}  #{task['id'][-4:]}"

    board_by_col = {c: [t for t in st.session_state.tasks if t["column"] == c] for c in COLUMNS}
    label_of = {t["id"]: kanban_card_label(t) for t in st.session_state.tasks}
    before = [
        {"header": f"{COLUMN_EMOJI[c]} {c}  ·  {len(board_by_col[c])}", "items": [label_of[t["id"]] for t in board_by_col[c]]}
        for c in COLUMNS
    ]

    board_ids_sig = ",".join(sorted(t["id"] for t in st.session_state.tasks))
    after = sort_items(
        before, multi_containers=True, direction="vertical",
        custom_style=KANBAN_STYLE, key=f"board_sort_{hash(board_ids_sig)}",
    )

    if after != before:
        label_to_id = {v: k for k, v in label_of.items()}
        new_tasks = []
        for group in after:
            col_name = next(c for c in COLUMNS if c in group["header"])
            for label in group["items"]:
                tid = label_to_id.get(label)
                if tid is None:
                    continue
                t = dict(next(x for x in st.session_state.tasks if x["id"] == tid))
                t["column"] = col_name
                new_tasks.append(t)
        save(new_tasks)
        st.rerun()

    with st.expander("🗂️ Manage tasks (details, attachments, delete)"):
        for c in COLUMNS:
            if not board_by_col[c]:
                continue
            st.markdown(f"{COLUMN_EMOJI[c]} **{c}**")
            for task in board_by_col[c]:
                with st.container(border=True):
                    st.markdown(f"**{task['title']}**")
                    st.markdown(tag_pill(task.get("project", "General")), unsafe_allow_html=True)
                    badge = deadline_badge(task.get("deadline"))
                    if badge:
                        st.caption(badge)
                    if task.get("notes"):
                        st.caption(task["notes"])
                    for att in task.get("attachments", []):
                        st.markdown(f"📎 [{att['name']}]({att['url']})")
                    if st.button("✕ Delete", key=f"del_{task['id']}"):
                        st.session_state.tasks = [t for t in st.session_state.tasks if t["id"] != task["id"]]
                        save(st.session_state.tasks)
                        st.rerun()

with tab_big_picture:
    st.caption("Everything going on, radiating out by tag. Hover a node for the full title.")
    components.html(render_mind_map(st.session_state.tasks, THEME), height=740, scrolling=False)
    st.caption("🔴 overdue · 🟠 due soon · dashed line = done")

with tab_week:
    st.caption(
        "Your week, based on your routine (Mon-Thu two work blocks, lighter Friday, weekend off)."
    )

    if "week_offset" not in st.session_state:
        st.session_state.week_offset = 0

    nav_prev, nav_label, nav_next, nav_today = st.columns([1, 4, 1, 1])
    if nav_prev.button("◀", key="week_prev"):
        st.session_state.week_offset -= 1
        st.rerun()
    is_this_week = st.session_state.week_offset == 0
    week_dates = current_week_dates(st.session_state.week_offset)
    nav_label.markdown(
        f"**{'This week' if is_this_week else week_dates['Monday'].strftime('%d %b') + ' – ' + week_dates['Sunday'].strftime('%d %b')}**"
    )
    if nav_next.button("▶", key="week_next"):
        st.session_state.week_offset += 1
        st.rerun()
    if not is_this_week and nav_today.button("Today", key="week_today"):
        st.session_state.week_offset = 0
        st.rerun()

    active_tasks = [t for t in st.session_state.tasks if t["column"] != "Done"] if is_this_week else []

    if not is_this_week:
        st.caption("Viewing another week — showing your Google Calendar only. Task scheduling always applies to this week.")

    btn_plan, btn_discard = st.columns([1, 1])
    if is_this_week and btn_plan.button("🧠 Plan my week", key="plan_week_btn", type="primary"):
        with st.spinner("Thinking like a time-management expert..."):
            try:
                result = nlp.plan_week(active_tasks)
                normalized = {}
                for p in result.get("plan", []):
                    day = p.get("day")
                    if isinstance(day, str):
                        day = day.strip().title()
                        if day not in WEEK_DAYS:
                            day = None
                    start_time = p.get("start_time") if day else None
                    normalized[p["id"]] = {
                        "day": day,
                        "start_time": start_time,
                        "duration_min": p.get("duration_min") or 45,
                        "reason": p.get("reason"),
                    }
                st.session_state.proposed_week_plan = normalized
            except Exception as e:
                st.error(f"Couldn't generate a plan: {e}")

    plan_preview = st.session_state.proposed_week_plan if is_this_week else None

    if plan_preview:
        if btn_discard.button("✕ Discard proposal", key="discard_week_plan"):
            st.session_state.proposed_week_plan = None
            st.rerun()
        st.info("Proposed plan below — approve to apply it, or discard and place tasks yourself.")
        if st.button("✅ Approve plan", key="approve_week_plan", type="primary"):
            tasks = list(st.session_state.tasks)
            for t in tasks:
                if t["id"] in plan_preview:
                    entry = plan_preview[t["id"]]
                    t["day"] = entry["day"]
                    t["start_time"] = entry.get("start_time")
                    t["duration_min"] = entry.get("duration_min")
                    if t["day"] and t["column"] == "Backlog":
                        t["column"] = "This Week"
            save(tasks)
            st.session_state.proposed_week_plan = None
            st.rerun()

    calendar_events = []
    if HAS_CALENDAR:
        try:
            calendar_events = load_calendar_events(week_dates["Monday"].isoformat(), week_dates["Sunday"].isoformat())
        except Exception as e:
            st.caption(f"⚠️ Couldn't load your calendar: {e}")
    else:
        st.caption("Google Calendar packages not installed — showing tasks only.")

    components.html(
        render_week_grid(active_tasks, plan_preview, week_dates, THEME, calendar_events),
        height=620, scrolling=True,
    )
    st.caption(
        "Shaded blocks are timed by the AI plan · dashed blocks (📅) are from your Google Calendar · "
        "chips in \"All day\" are manually-assigned, no set time · 🇵🇹 marks Portuguese public holidays. "
        "Scroll the grid to see the full day (00:00–23:00)."
    )

    if plan_preview:
        with st.expander("💭 Why these slots"):
            for task in active_tasks:
                entry = plan_preview.get(task["id"])
                if entry and entry.get("reason"):
                    st.caption(f"**{task['title']}** — {entry['reason']}")
    elif is_this_week:
        st.caption("Drag a task onto a day to schedule it (no exact time — shows in \"All day\").")

        def week_card_label(task):
            prefix = ""
            badge = deadline_badge(task.get("deadline"))
            if badge and badge.startswith("⚠️"):
                prefix = "⚠️ "
            elif badge and badge.startswith("⏳"):
                prefix = "⏳ "
            tag = task.get("project", "General")
            return f"{prefix}{task['title']}\n{project_dot(tag)} {tag}  #{task['id'][-4:]}"

        week_groups = WEEK_DAYS + [None]
        week_group_names = WEEK_DAYS + ["Unscheduled"]
        week_by_group = {g: [t for t in active_tasks if t.get("day") == g] for g in week_groups}
        week_label_of = {t["id"]: week_card_label(t) for t in active_tasks}
        week_before = [
            {"header": name, "items": [week_label_of[t["id"]] for t in week_by_group[g]]}
            for g, name in zip(week_groups, week_group_names)
        ]

        week_ids_sig = ",".join(sorted(t["id"] for t in active_tasks))
        week_after = sort_items(
            week_before, multi_containers=True, direction="vertical",
            custom_style=KANBAN_STYLE, key=f"week_sort_{hash(week_ids_sig)}",
        )

        if week_after != week_before:
            week_label_to_id = {v: k for k, v in week_label_of.items()}
            name_to_day = dict(zip(week_group_names, week_groups))
            updated = {}
            for group in week_after:
                day_value = name_to_day.get(group["header"])
                for label in group["items"]:
                    tid = week_label_to_id.get(label)
                    if tid is not None:
                        updated[tid] = day_value
            tasks = list(st.session_state.tasks)
            for t in tasks:
                if t["id"] in updated:
                    t["day"] = updated[t["id"]]
                    t["start_time"] = None
                    t["duration_min"] = None
            save(tasks)
            st.rerun()

# ── Chat ──────────────────────────────────────────────────────────────────────

st.divider()
st.subheader("💬 Chat")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

flow = st.session_state.new_task_flow

# ── New-task wizard: tag → deadline → notes/files ─────────────────────────────

if flow and flow["stage"] == "tag":
    with st.chat_message("assistant"):
        tags = existing_tags()
        if tags:
            st.caption("Pick a tag, or type a new one in the chat box below (e.g. PA).")
            btn_cols = st.columns(min(len(tags), 6))
            for i, tag in enumerate(tags):
                if btn_cols[i % len(btn_cols)].button(tag, key=f"tagbtn_{flow['id']}_{tag}"):
                    flow["tag"] = tag
                    flow["stage"] = "deadline"
                    push_assistant(f"Tagged **{flow['title']}** as {tag}. Pick a deadline below, or say \"no deadline\".")
                    st.rerun()
        else:
            st.caption("Type a tag below (e.g. PA, or a project name).")

elif flow and flow["stage"] == "deadline":
    with st.chat_message("assistant"):
        picked = st.date_input("Deadline", value=today_lisbon(), key=f"deadline_picker_{flow['id']}")
        c1, c2 = st.columns(2)
        if c1.button("Set deadline", key=f"set_deadline_{flow['id']}"):
            flow["deadline"] = picked.isoformat()
            flow["stage"] = "notes_files"
            push_assistant(
                f"Deadline set to {picked.strftime('%d %b')}. Want to add notes or attach a file? "
                "Type notes below and/or upload a file, then hit Done — or just hit Done to skip."
            )
            st.rerun()
        if c2.button("No deadline", key=f"no_deadline_{flow['id']}"):
            flow["deadline"] = None
            flow["stage"] = "notes_files"
            push_assistant(
                "No deadline. Want to add notes or attach a file? "
                "Type notes below and/or upload a file, then hit Done — or just hit Done to skip."
            )
            st.rerun()

elif flow and flow["stage"] == "notes_files":
    with st.chat_message("assistant"):
        if flow.get("notes"):
            st.caption(f"Notes so far: {flow['notes']}")
        uploaded = st.file_uploader("Attach a file (optional)", key=f"uploader_{flow['id']}")
        if st.button("✅ Done — add card", key=f"finish_card_{flow['id']}", type="primary"):
            finalize_new_task(uploaded_file=uploaded)
            st.rerun()

if flow and flow["stage"] == "tag":
    placeholder = "Type a tag (e.g. PA)"
elif flow and flow["stage"] == "deadline":
    placeholder = "Say 'no deadline' to skip, or use the date picker above"
elif flow and flow["stage"] == "notes_files":
    placeholder = "Type notes (optional), or just hit Done above"
else:
    placeholder = "e.g. 'add task: review proposals' or 'move review to in progress'"

user_input = st.chat_input(placeholder)

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    flow = st.session_state.new_task_flow

    if flow and flow["stage"] == "tag":
        flow["tag"] = user_input.strip()
        flow["stage"] = "deadline"
        push_assistant(f"Tagged **{flow['title']}** as {flow['tag']}. Pick a deadline below, or say \"no deadline\".")
        st.rerun()

    elif flow and flow["stage"] == "deadline":
        if user_input.strip().lower() in ("no", "none", "skip", "no deadline"):
            flow["deadline"] = None
            flow["stage"] = "notes_files"
            push_assistant(
                "No deadline. Want to add notes or attach a file? "
                "Type notes below and/or upload a file, then hit Done — or just hit Done to skip."
            )
        else:
            push_assistant("Use the date picker above to set a deadline, or say \"no deadline\" to skip.")
        st.rerun()

    elif flow and flow["stage"] == "notes_files":
        if user_input.strip().lower() not in ("no", "none", "skip"):
            flow["notes"] = user_input.strip()
            push_assistant("Got it — notes saved. Attach a file above if you want, then hit Done.")
        else:
            flow["notes"] = None
            push_assistant("No notes. Attach a file above if you want, then hit Done.")
        st.rerun()

    else:
        with st.spinner("Thinking..."):
            try:
                cmd = nlp.parse_command(user_input, st.session_state.tasks)
            except Exception as e:
                cmd = {"action": "none", "reply": f"Error: {e}"}

        action = cmd.get("action", "none")
        tasks = list(st.session_state.tasks)

        if action == "add":
            new_title = cmd.get("task_title", user_input)
            st.session_state.new_task_flow = {
                "id": str(uuid.uuid4())[:8],
                "title": new_title,
                "column": cmd.get("column", "Backlog"),
                "stage": "tag",
                "tag": None,
                "deadline": None,
                "notes": None,
                "attachments": [],
            }
            push_assistant(f"Got it — **{new_title}**. What tag should this go under? (e.g. PA, or a project name)")

        elif action == "move":
            target = cmd.get("task_title", "").lower()
            for t in tasks:
                if target in t["title"].lower():
                    t["column"] = cmd.get("column", t["column"])
                    break
            save(tasks)
            push_assistant(cmd.get("reply", "Done!"))

        elif action == "delete":
            target = cmd.get("task_title", "").lower()
            tasks = [t for t in tasks if target not in t["title"].lower()]
            save(tasks)
            push_assistant(cmd.get("reply", "Done!"))

        elif action == "edit":
            target = cmd.get("task_title", "").lower()
            for t in tasks:
                if target in t["title"].lower():
                    if cmd.get("notes"):
                        t["notes"] = cmd["notes"]
                    if cmd.get("project"):
                        t["project"] = cmd["project"]
                    break
            save(tasks)
            push_assistant(cmd.get("reply", "Done!"))

        else:
            push_assistant(cmd.get("reply", "Not sure what you mean — try 'add task: ...'"))

        st.rerun()

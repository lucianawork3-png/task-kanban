import os
from datetime import datetime, time
from zoneinfo import ZoneInfo

LISBON = ZoneInfo("Europe/Lisbon")

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _get_creds() -> Credentials:
    refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN", "")
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")

    if not refresh_token:
        raise RuntimeError("GOOGLE_REFRESH_TOKEN not set")

    token_data = {
        "refresh_token": refresh_token.strip(),
        "client_id": client_id.strip(),
        "client_secret": client_secret.strip(),
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    creds = Credentials.from_authorized_user_info(token_data, SCOPES)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return creds


def _service():
    return build("calendar", "v3", credentials=_get_creds(), cache_discovery=False)


def list_calendars() -> list[dict]:
    items = _service().calendarList().list().execute().get("items", [])
    return [
        {"id": c["id"], "label": c.get("summary", c["id"])}
        for c in items
        if c.get("accessRole") in ("owner", "writer")
    ]


def list_events_between(start_date, end_date) -> list[dict]:
    """Events across all writable calendars from start_date 00:00 to end_date 23:59 (local dates)."""
    time_min = datetime.combine(start_date, time(0, 0, 0), tzinfo=LISBON).isoformat()
    time_max = datetime.combine(end_date, time(23, 59, 59), tzinfo=LISBON).isoformat()

    service = _service()
    events = []
    for cal in list_calendars():
        items = (
            service.events()
            .list(
                calendarId=cal["id"],
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
            .get("items", [])
        )
        for e in items:
            start = e["start"].get("dateTime", e["start"].get("date"))
            end = e["end"].get("dateTime", e["end"].get("date"))
            events.append({
                "title": e.get("summary", "(no title)"),
                "start": start,
                "end": end,
                "all_day": "date" in e["start"],
                "calendar": cal["label"],
            })
    return events

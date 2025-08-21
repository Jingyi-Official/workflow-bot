from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2 import service_account
import os

def get_calendar_service():
    json_path = "service_account.json"
    with open(json_path, "w") as f:
        f.write(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])

    creds = service_account.Credentials.from_service_account_file(
        json_path,
        scopes=["https://www.googleapis.com/auth/calendar.readonly"],
    )
    return build("calendar", "v3", credentials=creds)

def fetch_todays_events(calendar_id="primary"):
    service = get_calendar_service()
    now = datetime.utcnow()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
    end = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=start,
        timeMax=end,
        singleEvents=True,
        orderBy="startTime"
    ).execute()
    return events_result.get("items", [])

def events_to_markdown(events):
    if not events:
        return "No events scheduled today.\n"
    lines = ["### 🗓 Today's Calendar\n"]
    for ev in events:
        start = ev["start"].get("dateTime", ev["start"].get("date"))
        summary = ev.get("summary", "No Title")
        location = ev.get("location", "")
        line = f"- {start} · **{summary}**"
        if location:
            line += f" @ {location}"
        lines.append(line)
    return "\n".join(lines) + "\n"
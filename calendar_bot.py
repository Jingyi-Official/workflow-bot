# calendar_bot.py
"""
Google Calendar -> Markdown summary

Setup:
1) Enable Calendar API & OAuth in Google Cloud Console.
   Save OAuth client credentials as ./credentials_calendar.json
2) On first run, a browser window will pop up for authorization.
   A token will then be stored at ./token_calendar.json
3) Optional environment variables:
   - CALENDAR_TIMEZONE: IANA timezone string (default "Europe/London")
   - CALENDAR_ID: calendar ID to fetch (default 'primary')
"""

import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
CRED_PATH = os.getenv("CALENDAR_CREDENTIALS_PATH", "credentials_calendar.json")
TOKEN_PATH = os.getenv("CALENDAR_TOKEN_PATH", "token_calendar.json")


def _get_tz() -> timezone:
    """Get timezone from env variable, fallback to Europe/London, else UTC."""
    import zoneinfo
    tz_name = os.getenv("CALENDAR_TIMEZONE", "Europe/London")
    try:
        return zoneinfo.ZoneInfo(tz_name)
    except Exception:
        return timezone.utc


def _authorize():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CRED_PATH):
                raise RuntimeError(f"Missing OAuth client file: {CRED_PATH}")
            flow = InstalledAppFlow.from_client_secrets_file(CRED_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())
    return creds


def fetch_todays_events(calendar_id: str | None = None) -> List[Dict]:
    """
    读取当天（本地时区）所有单次展开后的事件，按开始时间排序。
    返回 events 原始列表（Google Calendar Events 资源的子集）。
    """
    tz = _get_tz()
    now = datetime.now(tz)
    start_of_day = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=tz)
    end_of_day = start_of_day + timedelta(days=1)

    creds = _authorize()
    service = build("calendar", "v3", credentials=creds)

    calendar_id = calendar_id or os.getenv("CALENDAR_ID", "primary")

    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=start_of_day.isoformat(),
        timeMax=end_of_day.isoformat(),
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    return events_result.get("items", [])


def events_to_markdown(events: List[Dict]) -> str:
    """
    把事件列表转为 Markdown：表格 + 会议链接提取
    """
    if not events:
        return "_(No events today)_\n"

    def _fmt_time(tobj: Dict) -> str:
        # tobj 可能有 'dateTime' 或 'date'
        val = tobj.get("dateTime") or tobj.get("date")
        if not val:
            return "N/A"
        # 直接把 ISO 时间中 'T' 换空格，去掉秒尾部的 'Z'
        if "T" in val:
            val = val.replace("T", " ").replace("Z", "")
            # 仅保留 hh:mm
            try:
                hhmm = val.split(" ")[1][:5]
                return hhmm
            except Exception:
                return val
        # 全天事件
        return "All-day"

    md = []
    md.append("| Time | Title | Location | Link |")
    md.append("|---|---|---|---|")
    for ev in events:
        title = ev.get("summary") or "(No title)"
        start = _fmt_time(ev.get("start", {}))
        loc = ev.get("location", "") or ""
        # 寻找会议链接
        link = ""
        hangout = (ev.get("hangoutLink") or "")  # 旧字段
        meet = ev.get("conferenceData", {}).get("entryPoints", [])
        if hangout:
            link = hangout
        elif meet:
            for ep in meet:
                if ep.get("entryPointType") in {"video", "more"} and ep.get("uri"):
                    link = ep["uri"]
                    break
        # 退化到 htmlLink（事件网页）
        if not link:
            link = ev.get("htmlLink", "")

        # 转义 |
        def esc(s: str) -> str:
            return (s or "").replace("|", "\\|")

        md.append(f"| {esc(start)} | {esc(title)} | {esc(loc)} | {esc(link)} |")

    return "\n".join(md) + "\n"

def events_to_html(events: List[Dict]) -> str:
    """
    Render calendar events as an HTML schedule card.
    """
    def _fmt_time(tobj: Dict) -> str:
        """Format start/end time to hh:mm, or All-day."""
        val = tobj.get("dateTime") or tobj.get("date")
        if not val:
            return "N/A"
        if "T" in val:
            val = val.replace("T", " ").replace("Z", "")
            try:
                hhmm = val.split(" ")[1][:5]
                return hhmm
            except Exception:
                return val
        return "All-day"

    if not events:
        return """
        <div style="font-family: sans-serif; font-size:14px; color:#555;">
          (No events today)
        </div>
        """

    rows = []
    for ev in events:
        title = ev.get("summary") or "(No title)"
        start = _fmt_time(ev.get("start", {}))
        end = _fmt_time(ev.get("end", {}))
        time_range = f"{start} - {end}" if start != end else start
        loc = ev.get("location", "") or ""

        # Try to find meeting link
        link = ""
        hangout = ev.get("hangoutLink") or ""
        meet = ev.get("conferenceData", {}).get("entryPoints", [])
        if hangout:
            link = hangout
        elif meet:
            for ep in meet:
                if ep.get("entryPointType") in {"video", "more"} and ep.get("uri"):
                    link = ep["uri"]
                    break
        if not link:
            link = ev.get("htmlLink", "")

        link_html = f'<a href="{link}" target="_blank">Link</a>' if link else ""

        rows.append(f"""
          <tr>
            <td style="padding:10px 14px; border-top:1px solid #e5e7eb; font-size:14px; color:#111827; width:160px;">
              {time_range}
            </td>
            <td style="padding:10px 14px; border-top:1px solid #e5e7eb; font-size:14px; color:#111827;">
              {title}
            </td>
            <td style="padding:10px 14px; border-top:1px solid #e5e7eb; font-size:14px; color:#374151;">
              {loc}
            </td>
            <td style="padding:10px 14px; border-top:1px solid #e5e7eb; font-size:14px;">
              {link_html}
            </td>
          </tr>
        """)

    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Noto Sans CJK SC', Arial, sans-serif;
                background:#fff; border:1px solid #e5e7eb; border-radius:12px; overflow:hidden;
                box-shadow:0 2px 6px rgba(0,0,0,0.05); max-width:720px; margin:20px auto;">
      <div style="padding:16px; font-size:18px; font-weight:600; border-bottom:1px solid #e5e7eb; color:#111827;">
        今日行程
      </div>
      <table role="presentation" cellspacing="0" cellpadding="0" style="width:100%; border-collapse:collapse;">
        <thead>
          <tr style="background:#f9fafb;">
            <th align="left" style="padding:10px 14px; font-size:12px; color:#374151; text-transform:uppercase;">时间</th>
            <th align="left" style="padding:10px 14px; font-size:12px; color:#374151; text-transform:uppercase;">事项</th>
            <th align="left" style="padding:10px 14px; font-size:12px; color:#374151; text-transform:uppercase;">地点</th>
            <th align="left" style="padding:10px 14px; font-size:12px; color:#374151; text-transform:uppercase;">链接</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows)}
        </tbody>
      </table>
    </div>
    """
    return html
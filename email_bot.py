# email_bot.py
"""
Send emails via Gmail API (Markdown/plaintext body, supports attachments).

Setup:
1) Enable Gmail API & OAuth in Google Cloud Console.
   Save OAuth client credentials as ./credentials_gmail.json
2) On first run, a browser window will pop up for authorization.
   A token will then be stored at ./token_gmail.json
3) Environment variables:
   - EMAIL_FROM: sender Gmail address
   - EMAIL_TO: recipient email address
   - EMAIL_SUBJECT_PREFIX: subject prefix (optional)

pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
"""

import base64
import os
from typing import List, Optional
from email.message import EmailMessage

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
CRED_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials_gmail.json")
TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH", "token_gmail.json")


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


# def _create_message(
#     sender: str,
#     to: str,
#     subject: str,
#     body_text: str,
#     attachments: Optional[List[str]] = None,
# ) -> dict:
#     msg = EmailMessage()
#     msg["To"] = to
#     msg["From"] = sender
#     msg["Subject"] = subject
#     msg.set_content(body_text, subtype="plain", charset="utf-8")

#     for path in attachments or []:
#         if not os.path.exists(path):
#             continue
#         filename = os.path.basename(path)
#         with open(path, "rb") as f:
#             data = f.read()
#         # 按通用 octet-stream 处理；Gmail 会正确接收
#         msg.add_attachment(
#             data,
#             maintype="application",
#             subtype="octet-stream",
#             filename=filename,
#         )

#     raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
#     return {"raw": raw}


# def send_email(
#     subject: str,
#     body_markdown: str,
#     attachments: Optional[List[str]] = None,
#     to: Optional[str] = None,
#     sender: Optional[str] = None,
# ):
#     sender = sender or os.getenv("EMAIL_FROM")
#     to = to or os.getenv("EMAIL_TO")
#     if not sender or not to:
#         raise RuntimeError("EMAIL_FROM / EMAIL_TO must be set (env vars).")

#     creds = _authorize()
#     service = build("gmail", "v1", credentials=creds)

#     msg = _create_message(
#         sender=sender,
#         to=to,
#         subject=subject,
#         body_text=body_markdown,
#         attachments=attachments,
#     )
#     service.users().messages().send(userId="me", body=msg).execute()

# --- inside email_bot.py ---

def _create_message(
    sender: str,
    to: str,
    subject: str,
    body_text: str,                  # plain text / markdown fallback
    attachments: list[str] | None = None,
    html_body: str | None = None,    # NEW
) -> EmailMessage:
    msg = EmailMessage()
    msg["To"] = to
    msg["From"] = sender
    msg["Subject"] = subject
    msg.set_content(body_text or "", subtype="plain", charset="utf-8")
    if html_body:  # HTML alternative shown by most clients
        msg.add_alternative(html_body, subtype="html")
    for path in attachments or []:
        if not os.path.exists(path):
            continue
        with open(path, "rb") as f:
            data = f.read()
        msg.add_attachment(data, maintype="application", subtype="octet-stream", filename=os.path.basename(path))
    return msg

def send_email(
    subject: str,
    body_markdown: str,
    attachments: list[str] | None = None,
    to: str | None = None,
    sender: str | None = None,
    html_body: str | None = None,    # NEW
):
    sender = sender or os.getenv("EMAIL_FROM")
    to = to or os.getenv("EMAIL_TO")
    if not sender or not to:
        raise RuntimeError("EMAIL_FROM / EMAIL_TO must be set (env vars).")

    msg = _create_message(
        sender=sender,
        to=to,
        subject=subject,
        body_text=body_markdown,
        attachments=attachments,
        html_body=html_body,          # pass-through
    )

    creds = _authorize()
    service = build("gmail", "v1", credentials=creds)
    import base64
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    service.users().messages().send(userId="me", body={"raw": raw}).execute()

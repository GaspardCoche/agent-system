#!/usr/bin/env python3
"""
Sends the daily digest by email via Gmail API.
Reads /tmp/digest_body.md and sends it to the user.

Requires env vars:
  GMAIL_TOKEN_JSON   → OAuth2 token JSON
  GMAIL_USER_EMAIL   → recipient (self)
"""
import base64
import json
import os
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

try:
    import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False


def get_service():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    token_json = os.environ.get("GMAIL_TOKEN_JSON")
    if not token_json:
        raise ValueError("GMAIL_TOKEN_JSON not set")

    d = json.loads(token_json)
    creds = Credentials(
        token=d.get("token"),
        refresh_token=d["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=d["client_id"],
        client_secret=d["client_secret"],
        scopes=d.get("scopes", ["https://mail.google.com/"])
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("gmail", "v1", credentials=creds)


def send_digest(service, recipient: str, digest_path: str):
    content = Path(digest_path).read_text(encoding="utf-8")
    today = datetime.now().strftime("%Y-%m-%d")
    subject = f"Daily Digest — {today}"

    msg = MIMEMultipart("alternative")
    msg["to"] = recipient
    msg["from"] = recipient
    msg["subject"] = subject

    msg.attach(MIMEText(content, "plain", "utf-8"))

    if HAS_MARKDOWN:
        html = markdown.markdown(content, extensions=["tables", "fenced_code"])
        html_body = f"""<html><body style="font-family: -apple-system, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px; line-height: 1.5;">{html}</body></html>"""
        msg.attach(MIMEText(html_body, "html", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    result = service.users().messages().send(
        userId="me", body={"raw": raw}
    ).execute()

    print(f"Digest sent to {recipient} (message ID: {result['id']})", file=sys.stderr)
    return result


def main():
    digest_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/digest_body.md"
    recipient = os.environ.get("GMAIL_USER_EMAIL")

    if not recipient:
        print("GMAIL_USER_EMAIL not set", file=sys.stderr)
        sys.exit(1)

    if not Path(digest_path).exists():
        print(f"Digest file not found: {digest_path}", file=sys.stderr)
        sys.exit(1)

    service = get_service()
    send_digest(service, recipient, digest_path)


if __name__ == "__main__":
    main()

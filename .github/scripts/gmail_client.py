#!/usr/bin/env python3
"""
Gmail API client for the email agent.
- Fetches emails from the last N hours
- Creates Gmail drafts for suggested replies
- Applies labels

Requires env vars:
  GMAIL_TOKEN_JSON   → OAuth2 token JSON (from gmail_auth_setup.py)
  GMAIL_USER_EMAIL   → your Gmail address
"""
import base64
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from pathlib import Path


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


def fetch_emails(service, hours_back: int = 24) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    # Exclude promotions and social tabs, only unread or recent
    query = f"after:{int(since.timestamp())} -category:promotions -category:social"

    result = service.users().messages().list(
        userId="me", q=query, maxResults=100
    ).execute()

    emails = []
    for ref in result.get("messages", []):
        msg = service.users().messages().get(
            userId="me", id=ref["id"], format="full"
        ).execute()
        parsed = _parse(msg)
        if parsed:
            emails.append(parsed)
    return emails


def _parse(msg: dict) -> dict | None:
    headers = {h["name"].lower(): h["value"]
               for h in msg["payload"].get("headers", [])}

    body = ""
    payload = msg["payload"]
    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                    break
    elif payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    return {
        "id": msg["id"],
        "thread_id": msg["threadId"],
        "from": headers.get("from", "unknown"),
        "to": headers.get("to", ""),
        "subject": headers.get("subject", "(no subject)"),
        "date": headers.get("date", ""),
        "snippet": msg.get("snippet", ""),
        "body_preview": body[:2000] + ("..." if len(body) > 2000 else ""),
        "labels": msg.get("labelIds", []),
        "is_unread": "UNREAD" in msg.get("labelIds", [])
    }


def create_drafts(service, triage_path: str):
    """Create Gmail drafts for emails with suggested replies."""
    triage = json.loads(Path(triage_path).read_text())
    created = []

    for email in triage.get("critique", []) + triage.get("interne", []):
        reply = email.get("suggested_reply")
        if not reply:
            continue

        subject = email["subject"]
        subject = f"Re: {subject}" if not subject.startswith("Re:") else subject

        msg = MIMEText(reply)
        msg["to"] = email["from"]
        msg["subject"] = subject
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

        draft_body: dict = {"message": {"raw": raw}}
        if email.get("thread_id"):
            draft_body["message"]["threadId"] = email["thread_id"]

        draft = service.users().drafts().create(userId="me", body=draft_body).execute()
        created.append({"draft_id": draft["id"], "to": email["from"], "subject": subject})
        print(f"  Draft created: {subject}", file=sys.stderr)

    Path("/tmp/drafts_created.json").write_text(json.dumps(created, indent=2))
    print(f"Total: {len(created)} drafts created", file=sys.stderr)
    return created


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours-back",    type=int, default=24)
    parser.add_argument("--output",        default="/tmp/raw_emails.json")
    parser.add_argument("--create-drafts", action="store_true")
    parser.add_argument("--triage-file",   default="/tmp/email_triage.json")
    args = parser.parse_args()

    service = get_service()

    if args.create_drafts:
        if not Path(args.triage_file).exists():
            print("No triage file found", file=sys.stderr)
            return
        create_drafts(service, args.triage_file)
    else:
        print(f"Fetching emails (last {args.hours_back}h)...", file=sys.stderr)
        emails = fetch_emails(service, args.hours_back)
        print(f"Found {len(emails)} emails", file=sys.stderr)
        Path(args.output).write_text(
            json.dumps(emails, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"Written to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()

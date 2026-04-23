#!/usr/bin/env python3
"""
Sends the CRM health report as an HTML email.
Reads /tmp/crm_health_report.md and /tmp/crm_health_snapshot.json.
"""
import base64
import json
import os
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
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
        token=d.get("token"), refresh_token=d["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=d["client_id"], client_secret=d["client_secret"],
        scopes=d.get("scopes", ["https://mail.google.com/"])
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("gmail", "v1", credentials=creds)


def render_html(report_md: str, snapshot: dict) -> str:
    score = snapshot.get("score", 0)
    metrics = snapshot.get("metrics", {})

    if score >= 80:
        score_color, score_bg = "#059669", "#ECFDF5"
    elif score >= 60:
        score_color, score_bg = "#D97706", "#FFFBEB"
    else:
        score_color, score_bg = "#DC2626", "#FEF2F2"

    try:
        import markdown
        body_html = markdown.markdown(report_md, extensions=["tables"])
    except ImportError:
        body_html = report_md.replace("\n", "<br>")

    today = datetime.now().strftime("%d/%m/%Y")
    return f'''<!DOCTYPE html>
<html lang="fr">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#F1F5F9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F1F5F9;">
<tr><td align="center" style="padding:16px;">
<table width="680" cellpadding="0" cellspacing="0" style="max-width:680px;width:100%;">

  <tr><td style="background:linear-gradient(145deg,#0a0a1a,#1e293b);border-radius:16px 16px 0 0;padding:0;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr><td style="height:3px;background:linear-gradient(90deg,#10B981,#059669,#047857);"></td></tr>
      <tr><td style="padding:28px 32px 0;text-align:center;">
        <span style="font-size:11px;font-weight:600;letter-spacing:4px;color:#6EE7B7;text-transform:uppercase;">Health Check</span>
      </td></tr>
      <tr><td style="text-align:center;padding:12px 32px 0;">
        <h1 style="color:#F8FAFC;font-size:28px;font-weight:300;margin:0;font-family:Georgia,serif;">CRM Report</h1>
      </td></tr>
      <tr><td style="text-align:center;padding:8px 32px 24px;">
        <span style="color:#64748B;font-size:12px;">{today}</span>
      </td></tr>
    </table>
  </td></tr>

  <tr><td style="background:{score_bg};padding:20px 28px;text-align:center;">
    <span style="font-size:48px;font-weight:700;color:{score_color};">{score}</span>
    <span style="font-size:20px;color:{score_color};opacity:0.7;">/100</span>
    <br/><span style="font-size:13px;color:{score_color};font-weight:600;">Score de sante</span>
  </td></tr>

  <tr><td style="background:#fff;padding:12px 28px;">
    <table width="100%" cellpadding="0" cellspacing="0"><tr>
      <td style="text-align:center;padding:8px;">
        <span style="font-size:20px;font-weight:700;color:#1E293B;">{metrics.get('open_deals', 0)}</span><br/>
        <span style="font-size:10px;color:#9CA3AF;">Deals ouverts</span>
      </td>
      <td style="text-align:center;padding:8px;">
        <span style="font-size:20px;font-weight:700;color:#1E293B;">{metrics.get('new_contacts_7d', 0)}</span><br/>
        <span style="font-size:10px;color:#9CA3AF;">Contacts (7j)</span>
      </td>
      <td style="text-align:center;padding:8px;">
        <span style="font-size:20px;font-weight:700;color:#1E293B;">{metrics.get('stale_deals', 0)}</span><br/>
        <span style="font-size:10px;color:#9CA3AF;">Deals stagnants</span>
      </td>
      <td style="text-align:center;padding:8px;">
        <span style="font-size:20px;font-weight:700;color:#1E293B;">{metrics.get('incomplete_contacts', 0)}</span><br/>
        <span style="font-size:10px;color:#9CA3AF;">Incomplets</span>
      </td>
    </tr></table>
  </td></tr>

  <tr><td style="background:#F8FAFC;padding:24px 28px;">
    <div style="font-size:14px;line-height:1.6;color:#334155;">
      {body_html}
    </div>
  </td></tr>

  <tr><td style="background:linear-gradient(145deg,#0a0a1a,#111827);border-radius:0 0 16px 16px;padding:16px 28px;text-align:center;">
    <p style="color:#4B5563;font-size:10px;margin:0;">Agent System — CRM Health Check hebdomadaire</p>
  </td></tr>

</table>
</td></tr></table>
</body></html>'''


def main():
    report_path = Path("/tmp/crm_health_report.md")
    snapshot_path = Path("/tmp/crm_health_snapshot.json")

    if not report_path.exists():
        print("No report found", file=sys.stderr)
        sys.exit(1)

    report_md = report_path.read_text(encoding="utf-8")
    snapshot = {}
    if snapshot_path.exists():
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))

    recipient = os.environ.get("GMAIL_USER_EMAIL")
    if not recipient:
        print("GMAIL_USER_EMAIL not set", file=sys.stderr)
        sys.exit(1)

    score = snapshot.get("score", "?")
    subject = f"CRM Health: {score}/100 — Rapport hebdomadaire"

    msg = MIMEMultipart("alternative")
    msg["to"] = recipient
    msg["from"] = recipient
    msg["subject"] = subject

    msg.attach(MIMEText(report_md, "plain", "utf-8"))
    msg.attach(MIMEText(render_html(report_md, snapshot), "html", "utf-8"))

    service = get_service()
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    result = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    print(f"CRM report sent to {recipient} (ID: {result['id']})", file=sys.stderr)


if __name__ == "__main__":
    main()

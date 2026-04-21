#!/usr/bin/env python3
"""
Sends the AI digest as a professionally formatted HTML email.
Reads /tmp/ai_digest.json (structured) and /tmp/digest_body.md (fallback).

Requires env vars:
  GMAIL_TOKEN_JSON   -> OAuth2 token JSON
  GMAIL_USER_EMAIL   -> recipient (self)
"""
import base64
import json
import os
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from html import escape


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


CATEGORY_ICONS = {
    "Models": "\U0001f9e0",
    "Tools & Platforms": "\U0001f6e0\ufe0f",
    "Research": "\U0001f52c",
    "Business & Funding": "\U0001f4b0",
    "Open Source": "\U0001f310",
    "Regulation": "\u2696\ufe0f",
}

IMPORTANCE_STYLES = {
    "must_read": ("border-left: 4px solid #e74c3c;", "\U0001f534"),
    "important": ("border-left: 4px solid #f39c12;", "\U0001f7e0"),
    "worth_noting": ("border-left: 4px solid #95a5a6;", "\u26aa"),
}


def render_article(article: dict) -> str:
    imp = article.get("importance", "worth_noting")
    style, dot = IMPORTANCE_STYLES.get(imp, IMPORTANCE_STYLES["worth_noting"])
    cat = article.get("category", "")
    icon = CATEGORY_ICONS.get(cat, "\U0001f4cc")
    title = escape(article.get("title", "Sans titre"))
    url = article.get("url", "#")
    source = escape(article.get("source", ""))
    summary = escape(article.get("summary", ""))
    tags = ", ".join(escape(t) for t in article.get("company_tags", []))

    return f"""
    <div style="background: #ffffff; {style} padding: 16px 20px; margin-bottom: 12px; border-radius: 0 8px 8px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
      <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
        <span style="font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: #7f8c8d; font-weight: 600;">{icon} {escape(cat)}</span>
        <span style="font-size: 10px; color: #bdc3c7;">&bull;</span>
        <span style="font-size: 10px; color: #95a5a6;">{escape(source)}</span>
      </div>
      <a href="{escape(url)}" style="color: #2c3e50; text-decoration: none; font-size: 16px; font-weight: 600; line-height: 1.3;">{dot} {title}</a>
      <p style="color: #555; font-size: 14px; line-height: 1.6; margin: 8px 0 6px;">{summary}</p>
      {"<div style='margin-top: 4px;'><span style=\"font-size: 11px; color: #3498db;\">" + tags + "</span></div>" if tags else ""}
      <a href="{escape(url)}" style="font-size: 12px; color: #3498db; text-decoration: none; font-weight: 500;">Lire l'article &rarr;</a>
    </div>"""


def render_digest_html(digest: dict) -> str:
    today = datetime.now().strftime("%A %d %B %Y")
    headline = escape(digest.get("headline", "Digest IA de la semaine"))
    one_liner = escape(digest.get("one_liner", ""))
    articles = digest.get("articles", [])
    trends = digest.get("trends", [])
    stats = digest.get("stats", {})

    must_reads = [a for a in articles if a.get("importance") == "must_read"]
    important = [a for a in articles if a.get("importance") == "important"]
    worth_noting = [a for a in articles if a.get("importance") == "worth_noting"]

    must_read_html = "".join(render_article(a) for a in must_reads)
    important_html = "".join(render_article(a) for a in important)
    worth_noting_html = "".join(render_article(a) for a in worth_noting)

    trends_html = "".join(
        f'<li style="padding: 8px 0; border-bottom: 1px solid #f0f0f0; color: #444; font-size: 14px;">{escape(t)}</li>'
        for t in trends
    )

    return f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin: 0; padding: 0; background-color: #f4f6f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">

  <!-- Container -->
  <div style="max-width: 640px; margin: 0 auto; padding: 20px;">

    <!-- Header -->
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); border-radius: 12px 12px 0 0; padding: 32px 28px; text-align: center;">
      <div style="font-size: 32px; margin-bottom: 8px;">\U0001f916\U0001f4e1</div>
      <h1 style="color: #ffffff; font-size: 24px; font-weight: 700; margin: 0 0 4px;">AI Intelligence Briefing</h1>
      <p style="color: #a8b2d1; font-size: 13px; margin: 0;">{today}</p>
    </div>

    <!-- Headline -->
    <div style="background: #e8f4f8; padding: 20px 28px; border-left: 4px solid #3498db;">
      <p style="font-size: 18px; font-weight: 600; color: #2c3e50; margin: 0 0 8px;">{headline}</p>
      {"<p style='font-size: 14px; color: #555; margin: 0; font-style: italic;'>" + one_liner + "</p>" if one_liner else ""}
    </div>

    <!-- Must Read -->
    {"<div style='padding: 24px 0 8px;'><h2 style=\"font-size: 16px; color: #e74c3c; text-transform: uppercase; letter-spacing: 2px; margin: 0 0 16px; padding: 0 4px;\">" + chr(0x1f534) + " A ne pas rater</h2>" + must_read_html + "</div>" if must_reads else ""}

    <!-- Important -->
    {"<div style='padding: 16px 0 8px;'><h2 style=\"font-size: 16px; color: #f39c12; text-transform: uppercase; letter-spacing: 2px; margin: 0 0 16px; padding: 0 4px;\">" + chr(0x1f7e0) + " Important</h2>" + important_html + "</div>" if important else ""}

    <!-- Worth Noting -->
    {"<div style='padding: 16px 0 8px;'><h2 style=\"font-size: 16px; color: #95a5a6; text-transform: uppercase; letter-spacing: 2px; margin: 0 0 16px; padding: 0 4px;\">" + chr(0x26aa) + " A noter</h2>" + worth_noting_html + "</div>" if worth_noting else ""}

    <!-- Trends -->
    {"<div style='background: #fff; border-radius: 8px; padding: 20px 24px; margin-top: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);'><h2 style=\"font-size: 16px; color: #2c3e50; margin: 0 0 12px;\">" + chr(0x1f4c8) + " Tendances</h2><ul style=\"list-style: none; padding: 0; margin: 0;\">" + trends_html + "</ul></div>" if trends else ""}

    <!-- Footer -->
    <div style="text-align: center; padding: 24px 0; border-top: 1px solid #e0e0e0; margin-top: 24px;">
      <p style="font-size: 11px; color: #999; margin: 0;">
        {stats.get("articles_extracted", len(articles))} articles &bull; {stats.get("sources_scraped", 10)} sources
        &bull; Genere automatiquement par Agent System
      </p>
      <p style="font-size: 11px; color: #bbb; margin: 4px 0 0;">
        \u26a1 Powered by Gemini + Claude &bull; github.com/GaspardCoche/agent-system
      </p>
    </div>

  </div>
</body>
</html>"""


def render_fallback_html(md_content: str) -> str:
    try:
        import markdown
        html = markdown.markdown(md_content, extensions=["tables", "fenced_code"])
    except ImportError:
        html = md_content.replace("\n", "<br>")

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, sans-serif; max-width: 640px; margin: 0 auto; padding: 20px; line-height: 1.6; color: #333;">
{html}
</body></html>"""


def build_plain_text(digest: dict) -> str:
    lines = []
    lines.append(f"AI INTELLIGENCE BRIEFING — {datetime.now().strftime('%Y-%m-%d')}")
    lines.append("=" * 50)
    lines.append("")
    lines.append(digest.get("headline", ""))
    lines.append(digest.get("one_liner", ""))
    lines.append("")

    for article in digest.get("articles", []):
        imp = article.get("importance", "")
        marker = "[!!!]" if imp == "must_read" else "[!!]" if imp == "important" else "[.]"
        lines.append(f"{marker} {article.get('title', '')}")
        lines.append(f"    {article.get('source', '')} — {article.get('category', '')}")
        lines.append(f"    {article.get('summary', '')}")
        lines.append(f"    {article.get('url', '')}")
        lines.append("")

    if digest.get("trends"):
        lines.append("TENDANCES:")
        for t in digest["trends"]:
            lines.append(f"  - {t}")

    return "\n".join(lines)


def send_digest(service, recipient: str, digest_path: str, md_fallback: str = None):
    today = datetime.now().strftime("%Y-%m-%d")
    subject = f"\U0001f916 AI Intelligence Briefing — {today}"

    digest_json = None
    if Path(digest_path).exists():
        try:
            digest_json = json.loads(Path(digest_path).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, Exception):
            pass

    msg = MIMEMultipart("alternative")
    msg["to"] = recipient
    msg["from"] = recipient
    msg["subject"] = subject

    if digest_json and "articles" in digest_json:
        plain = build_plain_text(digest_json)
        html = render_digest_html(digest_json)
    elif md_fallback and Path(md_fallback).exists():
        plain = Path(md_fallback).read_text(encoding="utf-8")
        html = render_fallback_html(plain)
    else:
        plain = "Digest vide — aucun contenu disponible."
        html = render_fallback_html(plain)

    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    result = service.users().messages().send(
        userId="me", body={"raw": raw}
    ).execute()

    print(f"Digest sent to {recipient} (message ID: {result['id']})", file=sys.stderr)
    return result


def main():
    digest_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ai_digest.json"
    md_fallback = sys.argv[2] if len(sys.argv) > 2 else "/tmp/digest_body.md"
    recipient = os.environ.get("GMAIL_USER_EMAIL")

    if not recipient:
        print("GMAIL_USER_EMAIL not set", file=sys.stderr)
        sys.exit(1)

    service = get_service()
    send_digest(service, recipient, digest_path, md_fallback)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Sends the AI digest as a premium HTML newsletter email.
Reads /tmp/ai_digest.json (structured) and /tmp/digest_body.md (fallback).
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
import locale

try:
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
except locale.Error:
    pass


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


CAT_COLORS = {
    "Modeles": "#8B5CF6",
    "Outils & Plateformes": "#0EA5E9",
    "Recherche": "#10B981",
    "Business & Levees": "#F59E0B",
    "Open Source": "#6366F1",
    "Regulation & Ethique": "#EF4444",
    "Models": "#8B5CF6",
    "Tools & Platforms": "#0EA5E9",
    "Research": "#10B981",
    "Business & Funding": "#F59E0B",
}

CAT_ICONS = {
    "Modeles": "\U0001f9e0", "Models": "\U0001f9e0",
    "Outils & Plateformes": "\u2699\ufe0f", "Tools & Platforms": "\u2699\ufe0f",
    "Recherche": "\U0001f52c", "Research": "\U0001f52c",
    "Business & Levees": "\U0001f4b0", "Business & Funding": "\U0001f4b0",
    "Open Source": "\U0001f310",
    "Regulation & Ethique": "\u2696\ufe0f", "Regulation": "\u2696\ufe0f",
}


def _favicon(url: str) -> str:
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc or url
    except Exception:
        domain = url
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=32"


def _cat_pill(cat: str) -> str:
    color = CAT_COLORS.get(cat, "#6B7280")
    icon = CAT_ICONS.get(cat, "\U0001f4cc")
    return (f'<span style="display:inline-block;background:{color}15;color:{color};'
            f'font-size:11px;font-weight:600;padding:3px 10px;border-radius:12px;'
            f'letter-spacing:0.5px;">{icon} {escape(cat)}</span>')


def _render_top_story(story: dict) -> str:
    title = escape(story.get("title", ""))
    url = story.get("url", "#")
    source = escape(story.get("source", ""))
    summary = escape(story.get("summary", ""))
    image_url = story.get("image_url", "")
    cat = story.get("category", "")
    tags = story.get("company_tags", [])
    tags_html = " ".join(
        f'<span style="display:inline-block;background:#EFF6FF;color:#3B82F6;font-size:10px;'
        f'padding:2px 8px;border-radius:8px;margin:2px 2px 0 0;">{escape(t)}</span>'
        for t in tags[:4]
    )

    image_block = ""
    if image_url:
        image_block = (
            f'<tr><td style="padding:0 0 16px 0;">'
            f'<a href="{escape(url)}" style="text-decoration:none;">'
            f'<img src="{escape(image_url)}" alt="" '
            f'style="width:100%;max-height:280px;object-fit:cover;border-radius:12px;display:block;" />'
            f'</a></td></tr>'
        )

    return f'''
    <table width="100%" cellpadding="0" cellspacing="0" style="margin:24px 0 8px;">
      <tr><td style="padding:0 0 12px;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#FFF7ED;border-radius:8px;overflow:hidden;">
          <tr><td style="padding:4px 16px;">
            <span style="font-size:12px;font-weight:700;color:#EA580C;text-transform:uppercase;letter-spacing:2px;">\u2b50 Article phare</span>
          </td></tr>
        </table>
      </td></tr>
      {image_block}
      <tr><td style="background:#ffffff;border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,0.08);overflow:hidden;">
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr><td style="padding:24px 28px 0;">
            {_cat_pill(cat)}
          </td></tr>
          <tr><td style="padding:12px 28px 0;">
            <a href="{escape(url)}" style="color:#1a1a2e;text-decoration:none;font-size:22px;font-weight:700;line-height:1.3;display:block;">{title}</a>
          </td></tr>
          <tr><td style="padding:8px 28px 0;">
            <table cellpadding="0" cellspacing="0"><tr>
              <td style="padding-right:8px;"><img src="{_favicon(url)}" width="16" height="16" style="border-radius:4px;vertical-align:middle;" /></td>
              <td><span style="font-size:12px;color:#6B7280;">{source}</span></td>
            </tr></table>
          </td></tr>
          <tr><td style="padding:16px 28px;">
            <p style="color:#374151;font-size:15px;line-height:1.7;margin:0;">{summary}</p>
          </td></tr>
          <tr><td style="padding:0 28px 20px;">
            {tags_html}
            <a href="{escape(url)}" style="display:inline-block;margin-top:12px;background:#1a1a2e;color:#fff;text-decoration:none;font-size:13px;font-weight:600;padding:10px 24px;border-radius:8px;">Lire l\'article &rarr;</a>
          </td></tr>
        </table>
      </td></tr>
    </table>'''


def _render_card(article: dict) -> str:
    title = escape(article.get("title", ""))
    url = article.get("url", "#")
    source = escape(article.get("source", ""))
    summary = escape(article.get("summary", ""))
    cat = article.get("category", "")
    image_url = article.get("image_url", "")
    tags = article.get("company_tags", [])

    image_html = ""
    if image_url:
        image_html = (
            f'<tr><td style="padding:0;">'
            f'<a href="{escape(url)}"><img src="{escape(image_url)}" alt="" '
            f'style="width:100%;height:140px;object-fit:cover;display:block;border-radius:12px 12px 0 0;" /></a>'
            f'</td></tr>'
        )

    tags_html = ""
    if tags:
        tags_html = " ".join(
            f'<span style="font-size:10px;color:#6366F1;background:#EEF2FF;padding:1px 6px;border-radius:6px;">{escape(t)}</span>'
            for t in tags[:3]
        )

    return f'''
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,0.06);margin-bottom:16px;overflow:hidden;">
      {image_html}
      <tr><td style="padding:16px 20px 0;">
        {_cat_pill(cat)}
      </td></tr>
      <tr><td style="padding:10px 20px 0;">
        <a href="{escape(url)}" style="color:#1E293B;text-decoration:none;font-size:16px;font-weight:600;line-height:1.35;display:block;">{title}</a>
      </td></tr>
      <tr><td style="padding:6px 20px 0;">
        <table cellpadding="0" cellspacing="0"><tr>
          <td style="padding-right:6px;"><img src="{_favicon(url)}" width="14" height="14" style="border-radius:3px;vertical-align:middle;" /></td>
          <td><span style="font-size:11px;color:#9CA3AF;">{source}</span></td>
        </tr></table>
      </td></tr>
      <tr><td style="padding:10px 20px;">
        <p style="color:#4B5563;font-size:13px;line-height:1.6;margin:0;">{summary}</p>
      </td></tr>
      <tr><td style="padding:0 20px 16px;">
        {tags_html}
        <a href="{escape(url)}" style="display:inline-block;margin-top:8px;color:#3B82F6;text-decoration:none;font-size:12px;font-weight:600;">Lire &rarr;</a>
      </td></tr>
    </table>'''


def _render_compact(article: dict) -> str:
    title = escape(article.get("title", ""))
    url = article.get("url", "#")
    source = escape(article.get("source", ""))
    summary = escape(article.get("summary", ""))
    cat = article.get("category", "")
    color = CAT_COLORS.get(cat, "#6B7280")

    return f'''
    <tr><td style="padding:12px 0;border-bottom:1px solid #F3F4F6;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td width="4" style="background:{color};border-radius:2px;"></td>
          <td style="padding:0 16px;">
            <a href="{escape(url)}" style="color:#1E293B;text-decoration:none;font-size:14px;font-weight:600;line-height:1.3;">{title}</a>
            <br/>
            <span style="font-size:11px;color:#9CA3AF;">{source} &bull; {escape(cat)}</span>
            <p style="color:#6B7280;font-size:12px;line-height:1.5;margin:4px 0 0;">{summary}</p>
          </td>
          <td width="60" style="text-align:right;vertical-align:top;padding-top:2px;">
            <img src="{_favicon(url)}" width="24" height="24" style="border-radius:6px;" />
          </td>
        </tr>
      </table>
    </td></tr>'''


def _render_trend(trend) -> str:
    if isinstance(trend, dict):
        title = escape(trend.get("title", ""))
        desc = escape(trend.get("description", ""))
        return (f'<tr><td style="padding:12px 0;border-bottom:1px solid #F3F4F6;">'
                f'<span style="font-size:14px;font-weight:600;color:#1E293B;">{title}</span><br/>'
                f'<span style="font-size:13px;color:#6B7280;line-height:1.5;">{desc}</span>'
                f'</td></tr>')
    return (f'<tr><td style="padding:10px 0;border-bottom:1px solid #F3F4F6;">'
            f'<span style="font-size:13px;color:#374151;">{escape(str(trend))}</span>'
            f'</td></tr>')


def render_digest_html(digest: dict) -> str:
    now = datetime.now()
    days_fr = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]
    months_fr = ["","janvier","fevrier","mars","avril","mai","juin","juillet","aout","septembre","octobre","novembre","decembre"]
    date_str = f"{days_fr[now.weekday()]} {now.day} {months_fr[now.month]} {now.year}"

    headline = escape(digest.get("headline", "Digest IA"))
    one_liner = escape(digest.get("one_liner", ""))
    articles = digest.get("articles", [])
    trends = digest.get("trends", [])
    stats = digest.get("stats", {})
    top_story = digest.get("top_story")

    must_reads = [a for a in articles if a.get("importance") == "must_read"]
    important = [a for a in articles if a.get("importance") == "important"]
    worth_noting = [a for a in articles if a.get("importance") == "worth_noting"]

    top_story_html = _render_top_story(top_story) if top_story else ""
    must_read_cards = "".join(_render_card(a) for a in must_reads)
    important_cards = "".join(_render_card(a) for a in important)
    compact_rows = "".join(_render_compact(a) for a in worth_noting)
    trends_rows = "".join(_render_trend(t) for t in trends)

    n_articles = stats.get("articles_extracted", len(articles) + (1 if top_story else 0))
    n_sources = stats.get("sources_scraped", 10)

    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Intelligence Briefing</title>
</head>
<body style="margin:0;padding:0;background-color:#F1F5F9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;-webkit-font-smoothing:antialiased;">

<!-- Wrapper -->
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#F1F5F9;">
<tr><td align="center" style="padding:16px;">

<!-- Main container -->
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">

  <!-- Header -->
  <tr><td style="background:linear-gradient(135deg,#0F172A 0%,#1E293B 40%,#334155 100%);border-radius:16px 16px 0 0;padding:0;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr><td style="padding:36px 32px 12px;text-align:center;">
        <span style="font-size:40px;">\U0001f916</span>
      </td></tr>
      <tr><td style="text-align:center;padding:0 32px;">
        <h1 style="color:#F8FAFC;font-size:26px;font-weight:800;margin:0;letter-spacing:-0.5px;">AI Intelligence Briefing</h1>
      </td></tr>
      <tr><td style="text-align:center;padding:8px 32px 12px;">
        <span style="color:#94A3B8;font-size:13px;">{date_str}</span>
      </td></tr>
      <tr><td style="padding:0 32px 28px;text-align:center;">
        <table cellpadding="0" cellspacing="0" style="margin:0 auto;">
          <tr>
            <td style="background:rgba(255,255,255,0.1);border-radius:20px;padding:6px 16px;">
              <span style="color:#CBD5E1;font-size:12px;">{n_articles} articles</span>
              <span style="color:#475569;padding:0 6px;">&bull;</span>
              <span style="color:#CBD5E1;font-size:12px;">{n_sources} sources</span>
            </td>
          </tr>
        </table>
      </td></tr>
    </table>
  </td></tr>

  <!-- Headline bar -->
  <tr><td style="background:linear-gradient(90deg,#DBEAFE,#EDE9FE);padding:20px 28px;">
    <p style="font-size:17px;font-weight:700;color:#1E293B;margin:0 0 6px;line-height:1.4;">\U0001f4a1 {headline}</p>
    {"<p style='font-size:14px;color:#475569;margin:0;line-height:1.5;font-style:italic;'>" + one_liner + "</p>" if one_liner else ""}
  </td></tr>

  <!-- Content area -->
  <tr><td style="background:#F8FAFC;padding:8px 24px 24px;">

    <!-- Top Story -->
    {top_story_html}

    <!-- Must Read -->
    {"<table width='100%' cellpadding='0' cellspacing='0' style='margin:28px 0 12px;'><tr><td><span style=\"font-size:13px;font-weight:700;color:#DC2626;text-transform:uppercase;letter-spacing:2px;\">" + chr(0x1f534) + " A ne pas rater</span><hr style=\"border:none;border-top:2px solid #FEE2E2;margin:8px 0 16px;\"/></td></tr></table>" + must_read_cards if must_reads else ""}

    <!-- Important -->
    {"<table width='100%' cellpadding='0' cellspacing='0' style='margin:24px 0 12px;'><tr><td><span style=\"font-size:13px;font-weight:700;color:#D97706;text-transform:uppercase;letter-spacing:2px;\">" + chr(0x1f7e0) + " Important</span><hr style=\"border:none;border-top:2px solid #FEF3C7;margin:8px 0 16px;\"/></td></tr></table>" + important_cards if important else ""}

    <!-- Worth Noting -->
    {"<table width='100%' cellpadding='0' cellspacing='0' style='margin:24px 0 12px;'><tr><td><span style=\"font-size:13px;font-weight:700;color:#6B7280;text-transform:uppercase;letter-spacing:2px;\">" + chr(0x26aa) + " En bref</span><hr style=\"border:none;border-top:2px solid #E5E7EB;margin:8px 0 4px;\"/></td></tr>" + compact_rows + "</table>" if worth_noting else ""}

    <!-- Trends -->
    {"<table width='100%' cellpadding='0' cellspacing='0' style='background:#fff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,0.04);margin:28px 0 0;overflow:hidden;'><tr><td style='background:linear-gradient(90deg,#ECFDF5,#F0FDF4);padding:14px 20px;'><span style=\"font-size:13px;font-weight:700;color:#059669;text-transform:uppercase;letter-spacing:2px;\">" + chr(0x1f4c8) + " Tendances cles</span></td></tr><tr><td style='padding:4px 20px 12px;'><table width='100%' cellpadding='0' cellspacing='0'>" + trends_rows + "</table></td></tr></table>" if trends else ""}

  </td></tr>

  <!-- Footer -->
  <tr><td style="background:#1E293B;border-radius:0 0 16px 16px;padding:24px 28px;text-align:center;">
    <p style="color:#64748B;font-size:11px;margin:0 0 4px;">
      Genere automatiquement par <span style="color:#94A3B8;">Agent System</span>
    </p>
    <p style="color:#475569;font-size:10px;margin:0;">
      \u26a1 Gemini + Claude &bull; Chaque matin a 9h30
    </p>
  </td></tr>

</table>
<!-- /Main container -->

</td></tr>
</table>
<!-- /Wrapper -->

</body>
</html>'''


def build_plain_text(digest: dict) -> str:
    lines = [f"AI INTELLIGENCE BRIEFING — {datetime.now().strftime('%Y-%m-%d')}", "=" * 55, ""]
    lines.append(digest.get("headline", ""))
    if digest.get("one_liner"):
        lines.append(digest["one_liner"])
    lines.append("")

    top = digest.get("top_story")
    if top:
        lines.append(f"*** TOP STORY: {top.get('title', '')}")
        lines.append(f"    {top.get('source', '')} — {top.get('category', '')}")
        lines.append(f"    {top.get('summary', '')}")
        lines.append(f"    {top.get('url', '')}")
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
            if isinstance(t, dict):
                lines.append(f"  - {t.get('title','')}: {t.get('description','')}")
            else:
                lines.append(f"  - {t}")
    return "\n".join(lines)


def render_fallback_html(md_content: str) -> str:
    try:
        import markdown
        html = markdown.markdown(md_content, extensions=["tables", "fenced_code"])
    except ImportError:
        html = md_content.replace("\n", "<br>")
    return f'''<!DOCTYPE html><html><head><meta charset="utf-8"></head>
<body style="font-family:-apple-system,sans-serif;max-width:600px;margin:0 auto;padding:20px;line-height:1.6;color:#333;">{html}</body></html>'''


def send_digest(service, recipient, digest_path, md_fallback=None):
    today = datetime.now().strftime("%Y-%m-%d")
    subject = f"\U0001f916 AI Intelligence Briefing — {today}"

    digest_json = None
    if Path(digest_path).exists() and Path(digest_path).stat().st_size > 10:
        try:
            digest_json = json.loads(Path(digest_path).read_text(encoding="utf-8"))
        except Exception:
            pass

    msg = MIMEMultipart("alternative")
    msg["to"] = recipient
    msg["from"] = recipient
    msg["subject"] = subject

    if digest_json and (digest_json.get("articles") or digest_json.get("top_story")):
        plain = build_plain_text(digest_json)
        html = render_digest_html(digest_json)
    elif md_fallback and Path(md_fallback).exists():
        plain = Path(md_fallback).read_text(encoding="utf-8")
        html = render_fallback_html(plain)
    else:
        plain = "Digest vide."
        html = render_fallback_html(plain)

    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    result = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    print(f"Digest sent to {recipient} (ID: {result['id']})", file=sys.stderr)
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

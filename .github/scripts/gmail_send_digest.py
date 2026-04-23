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
from urllib.parse import quote
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


SOURCE_BRAND_IMAGES = {
    "Anthropic News": "https://cdn.prod.website-files.com/67ce28cfec624e2b733f8a52/68309ab48369f7ad9b4a40e1_open-graph.jpg",
    "OpenAI Blog": "https://images.ctfassets.net/kftzwdyauwt9/3KGOHkSXu53naMuSFNaiwv/cdb0e2f899f524abb71314ab20e09c9c/OAI-white-on-black.png",
    "Google DeepMind": "",
    "HuggingFace Blog": "https://huggingface.co/front/thumbnails/v2-2.png",
    "Mistral News": "https://cms.mistral.ai/assets/060bdeb1-fbff-419c-b2ae-b32b5e441864",
    "TechCrunch AI": "https://techcrunch.com/wp-content/uploads/2015/02/cropped-cropped-favicon-gradient.png",
    "VentureBeat AI": "",
    "AI News": "https://www.artificialintelligence-news.com/wp-content/uploads/2025/01/New-site-SEO-social-banner-1200x600-1.jpg",
    "Ars Technica AI": "https://cdn.arstechnica.net/wp-content/uploads/2016/10/cropped-ars-logo-512_480.png",
    "Google AI Blog": "https://blog.google/static/blogv2/images/google-200x200.png",
    "The Batch": "https://home-wordpress.deeplearning.ai/wp-content/uploads/2024/06/homepage-preview.png",
    "Simon Willison": "https://simonwillison.net/favicon.ico",
    "The Decoder": "",
    "The Verge AI": "https://cdn.vox-cdn.com/uploads/hub/sbnu_logo_minimal/441/large_The_Verge_logo.png",
    "GitHub Blog": "https://github.githubassets.com/assets/GitHub-Mark-ea2971cee799.png",
    "MIT Tech Review AI": "https://wp.technologyreview.com/wp-content/uploads/2023/10/MIT_TR_Logo_RGB_Master-1.png",
    "Wired AI": "",
    "MarkTechPost": "",
}


def _resolve_image(article: dict) -> str:
    img = article.get("image_url", "")
    if img and "s2/favicons" not in img and "sz=" not in img.split("?")[-1:][0]:
        return img
    source = article.get("source", "")
    brand = SOURCE_BRAND_IMAGES.get(source, "")
    if brand:
        return brand
    return ""


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


VAULT_REPO = os.environ.get("GITHUB_REPOSITORY", "GaspardCoche/agent-system")


def _vault_btn(article: dict) -> str:
    title = article.get("title", "Article")
    body_lines = [
        f"source: {article.get('source', '')}",
        f"url: {article.get('url', '')}",
        f"category: {article.get('category', '')}",
        f"image: {article.get('image_url', '')}",
        f"importance: {article.get('importance', '')}",
        f"tags: {', '.join(article.get('company_tags', []))}",
        "---",
        "",
        article.get("summary", ""),
    ]
    encoded_title = quote(f"\U0001f4cc {title}"[:120])
    encoded_body = quote("\n".join(body_lines))
    url = f"https://github.com/{VAULT_REPO}/issues/new?labels=vault-save&title={encoded_title}&body={encoded_body}"
    return (f'<a href="{url}" style="display:inline-block;margin-left:8px;background:#EEF2FF;'
            f'color:#4F46E5;text-decoration:none;font-size:11px;font-weight:600;'
            f'padding:4px 10px;border-radius:6px;vertical-align:middle;">'
            f'\U0001f4cc Vault</a>')


def _deep_dive_btn(article: dict) -> str:
    title = article.get("title", "Article")
    body_lines = [
        f"source: {article.get('source', '')}",
        f"url: {article.get('url', '')}",
        f"category: {article.get('category', '')}",
        "---",
        "",
        f"Analyse approfondie demandee pour : {title}",
        "",
        article.get("summary", ""),
    ]
    encoded_title = quote(f"\U0001f50d Deep dive : {title}"[:120])
    encoded_body = quote("\n".join(body_lines))
    url = f"https://github.com/{VAULT_REPO}/issues/new?labels=deep-dive&title={encoded_title}&body={encoded_body}"
    return (f'<a href="{url}" style="display:inline-block;margin-left:8px;background:#FDF2F8;'
            f'color:#BE185D;text-decoration:none;font-size:11px;font-weight:600;'
            f'padding:4px 10px;border-radius:6px;vertical-align:middle;">'
            f'\U0001f50d Brief</a>')


def _render_top_story(story: dict) -> str:
    title = escape(story.get("title", ""))
    url = story.get("url", "#")
    source = escape(story.get("source", ""))
    summary = escape(story.get("summary", ""))
    image_url = _resolve_image(story)
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
            f'style="width:100%;max-height:340px;object-fit:cover;border-radius:12px;display:block;" />'
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
            {_vault_btn(story)}
            {_deep_dive_btn(story)}
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
    image_url = _resolve_image(article)
    tags = article.get("company_tags", [])

    color = CAT_COLORS.get(cat, "#6B7280")
    if image_url:
        image_html = (
            f'<tr><td style="padding:0;">'
            f'<a href="{escape(url)}"><img src="{escape(image_url)}" alt="" '
            f'style="width:100%;height:180px;object-fit:cover;display:block;border-radius:12px 12px 0 0;" /></a>'
            f'</td></tr>'
        )
    else:
        image_html = (
            f'<tr><td style="padding:0;height:6px;background:linear-gradient(90deg,{color},{color}88);'
            f'border-radius:12px 12px 0 0;"></td></tr>'
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
        {_vault_btn(article)}
        {_deep_dive_btn(article)}
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
            {_vault_btn(article)}
            {_deep_dive_btn(article)}
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


def _validate_urls(digest: dict) -> dict:
    """Remove articles with obviously fabricated URLs and validate the rest."""
    import urllib.request as _ur

    def _check(url: str) -> bool:
        if not url or not url.startswith("http"):
            return False
        try:
            req = _ur.Request(url, method="HEAD", headers={
                "User-Agent": "Mozilla/5.0"
            })
            with _ur.urlopen(req, timeout=5) as resp:
                return resp.status < 400
        except Exception:
            try:
                req = _ur.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with _ur.urlopen(req, timeout=5) as resp:
                    _ = resp.read(512)
                    return resp.status < 400
            except Exception:
                return False

    checked = set()

    def _fix(article: dict) -> dict:
        url = article.get("url", "")
        if url in checked:
            return article
        if url and not _check(url):
            print(f"  [URL 404] {url} — replacing with source page", file=sys.stderr)
            from urllib.parse import urlparse
            parsed = urlparse(url)
            article["url"] = f"{parsed.scheme}://{parsed.netloc}"
            article["_url_fallback"] = True
        checked.add(url)
        return article

    if digest.get("top_story"):
        digest["top_story"] = _fix(digest["top_story"])
    digest["articles"] = [_fix(a) for a in digest.get("articles", [])]
    return digest


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
<table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;">

  <!-- Header -->
  <tr><td style="background:linear-gradient(145deg,#0a0a1a 0%,#111827 50%,#1a1a3e 100%);border-radius:16px 16px 0 0;padding:0;position:relative;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <!-- Accent line top -->
      <tr><td style="padding:0;">
        <table width="100%" cellpadding="0" cellspacing="0"><tr>
          <td style="height:3px;background:linear-gradient(90deg,#6366F1,#8B5CF6,#A78BFA,#C4B5FD,#8B5CF6,#6366F1);"></td>
        </tr></table>
      </td></tr>
      <!-- Top spacer with subtle branding -->
      <tr><td style="padding:32px 32px 0;text-align:center;">
        <table cellpadding="0" cellspacing="0" style="margin:0 auto;"><tr>
          <td style="width:32px;height:1px;background:linear-gradient(90deg,transparent,#4F46E5);"></td>
          <td style="padding:0 14px;">
            <span style="font-size:11px;font-weight:600;letter-spacing:4px;text-transform:uppercase;color:#818CF8;">Intelligence</span>
          </td>
          <td style="width:32px;height:1px;background:linear-gradient(90deg,#4F46E5,transparent);"></td>
        </tr></table>
      </td></tr>
      <!-- Main title -->
      <tr><td style="text-align:center;padding:14px 32px 0;">
        <h1 style="color:#F8FAFC;font-size:32px;font-weight:300;margin:0;letter-spacing:2px;font-family:Georgia,'Times New Roman',serif;">AI Briefing</h1>
      </td></tr>
      <!-- Date -->
      <tr><td style="text-align:center;padding:12px 32px 0;">
        <span style="color:#64748B;font-size:12px;letter-spacing:1.5px;text-transform:uppercase;">{date_str}</span>
      </td></tr>
      <!-- Stats pills -->
      <tr><td style="padding:18px 32px 30px;text-align:center;">
        <table cellpadding="0" cellspacing="0" style="margin:0 auto;"><tr>
          <td style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.25);border-radius:20px;padding:6px 18px;">
            <span style="color:#A5B4FC;font-size:12px;font-weight:500;">{n_articles} articles</span>
          </td>
          <td style="width:10px;"></td>
          <td style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.25);border-radius:20px;padding:6px 18px;">
            <span style="color:#A5B4FC;font-size:12px;font-weight:500;">{n_sources} sources</span>
          </td>
        </tr></table>
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
  <tr><td style="background:linear-gradient(145deg,#0a0a1a,#111827);border-radius:0 0 16px 16px;padding:0;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr><td style="height:1px;background:linear-gradient(90deg,transparent,rgba(99,102,241,0.2),transparent);"></td></tr>
      <tr><td style="padding:20px 28px;text-align:center;">
        <p style="color:#4B5563;font-size:10px;margin:0 0 4px;letter-spacing:0.5px;">
          Genere par <span style="color:#818CF8;">Agent System</span> &mdash; Gemini + Claude
        </p>
        <p style="color:#374151;font-size:9px;margin:0;">Chaque matin a 7h30</p>
      </td></tr>
    </table>
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
<body style="font-family:-apple-system,sans-serif;max-width:720px;margin:0 auto;padding:20px;line-height:1.6;color:#333;">{html}</body></html>'''


def send_digest(service, recipient, digest_path, md_fallback=None):
    today = datetime.now().strftime("%d/%m")

    digest_json = None
    if Path(digest_path).exists() and Path(digest_path).stat().st_size > 10:
        try:
            digest_json = json.loads(Path(digest_path).read_text(encoding="utf-8"))
        except Exception:
            pass

    headline = ""
    if digest_json:
        headline = digest_json.get("headline", "")
    if headline:
        subject = f"{headline} — AI Briefing {today}"
    else:
        subject = f"AI Intelligence Briefing — {today}"

    msg = MIMEMultipart("alternative")
    msg["to"] = recipient
    msg["from"] = recipient
    msg["subject"] = subject

    if digest_json and (digest_json.get("articles") or digest_json.get("top_story")):
        print("Validating article URLs...", file=sys.stderr)
        digest_json = _validate_urls(digest_json)
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


def render_weekly_html(digest: dict) -> str:
    now = datetime.now()
    days_fr = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]
    months_fr = ["","janvier","fevrier","mars","avril","mai","juin","juillet","aout","septembre","octobre","novembre","decembre"]
    date_str = f"{days_fr[now.weekday()]} {now.day} {months_fr[now.month]} {now.year}"

    headline = escape(digest.get("headline", "Recap Hebdomadaire"))
    top_3 = digest.get("top_3", [])
    sections = digest.get("sections", [])
    outlook = escape(digest.get("outlook", ""))
    stats = digest.get("stats", {})

    top_3_html = ""
    for i, story in enumerate(top_3, 1):
        medal = ["\U0001f947", "\U0001f948", "\U0001f949"][i-1] if i <= 3 else ""
        title = escape(story.get("title", ""))
        summary = escape(story.get("summary", ""))
        url = story.get("url", "#")
        cat = story.get("category", "")
        day = escape(story.get("day", ""))
        top_3_html += f'''
        <tr><td style="padding:16px 0;border-bottom:1px solid #E5E7EB;">
          <table width="100%" cellpadding="0" cellspacing="0"><tr>
            <td width="50" style="vertical-align:top;text-align:center;padding-top:4px;">
              <span style="font-size:28px;">{medal}</span>
            </td>
            <td style="padding-left:8px;">
              <a href="{escape(url)}" style="color:#1E293B;text-decoration:none;font-size:16px;font-weight:700;line-height:1.3;">{title}</a>
              <br/><span style="font-size:11px;color:#9CA3AF;">{day} &bull; {escape(cat)}</span>
              <p style="color:#4B5563;font-size:13px;line-height:1.6;margin:6px 0 0;">{summary}</p>
            </td>
          </tr></table>
        </td></tr>'''

    sections_html = ""
    for section in sections:
        theme = escape(section.get("theme", ""))
        articles = section.get("articles", [])
        items = ""
        for a in articles:
            t = escape(a.get("title", ""))
            s = escape(a.get("summary", ""))
            u = a.get("url", "#")
            src = escape(a.get("source", ""))
            items += f'''<tr><td style="padding:8px 0;border-bottom:1px solid #F3F4F6;">
              <a href="{escape(u)}" style="color:#1E293B;text-decoration:none;font-size:13px;font-weight:600;">{t}</a>
              <span style="font-size:11px;color:#9CA3AF;"> — {src}</span>
              <br/><span style="font-size:12px;color:#6B7280;">{s}</span>
            </td></tr>'''
        sections_html += f'''
        <table width="100%" cellpadding="0" cellspacing="0" style="margin:20px 0 0;">
          <tr><td style="padding:10px 16px;background:#F8FAFC;border-radius:8px 8px 0 0;">
            <span style="font-size:14px;font-weight:700;color:#334155;">{theme}</span>
          </td></tr>
          <tr><td style="padding:4px 16px 12px;">
            <table width="100%" cellpadding="0" cellspacing="0">{items}</table>
          </td></tr>
        </table>'''

    return f'''<!DOCTYPE html>
<html lang="fr">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Weekly AI Recap</title></head>
<body style="margin:0;padding:0;background-color:#F1F5F9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#F1F5F9;">
<tr><td align="center" style="padding:16px;">
<table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;">

  <!-- Header -->
  <tr><td style="background:linear-gradient(145deg,#0a0a1a 0%,#0f172a 50%,#1e1b4b 100%);border-radius:16px 16px 0 0;padding:0;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr><td style="height:3px;background:linear-gradient(90deg,#8B5CF6,#6366F1,#4F46E5,#6366F1,#8B5CF6);"></td></tr>
      <tr><td style="padding:32px 32px 0;text-align:center;">
        <table cellpadding="0" cellspacing="0" style="margin:0 auto;"><tr>
          <td style="width:32px;height:1px;background:linear-gradient(90deg,transparent,#8B5CF6);"></td>
          <td style="padding:0 14px;"><span style="font-size:11px;font-weight:600;letter-spacing:4px;text-transform:uppercase;color:#A78BFA;">Recap Hebdo</span></td>
          <td style="width:32px;height:1px;background:linear-gradient(90deg,#8B5CF6,transparent);"></td>
        </tr></table>
      </td></tr>
      <tr><td style="text-align:center;padding:14px 32px 0;">
        <h1 style="color:#F8FAFC;font-size:30px;font-weight:300;margin:0;letter-spacing:2px;font-family:Georgia,'Times New Roman',serif;">Weekly AI Briefing</h1>
      </td></tr>
      <tr><td style="text-align:center;padding:12px 32px 0;">
        <span style="color:#64748B;font-size:12px;letter-spacing:1.5px;text-transform:uppercase;">{date_str}</span>
      </td></tr>
      <tr><td style="padding:18px 32px 30px;text-align:center;">
        <table cellpadding="0" cellspacing="0" style="margin:0 auto;"><tr>
          <td style="background:rgba(139,92,246,0.15);border:1px solid rgba(139,92,246,0.25);border-radius:20px;padding:6px 18px;">
            <span style="color:#C4B5FD;font-size:12px;font-weight:500;">{stats.get('daily_digests', 0)} digests</span>
          </td>
          <td style="width:10px;"></td>
          <td style="background:rgba(139,92,246,0.15);border:1px solid rgba(139,92,246,0.25);border-radius:20px;padding:6px 18px;">
            <span style="color:#C4B5FD;font-size:12px;font-weight:500;">{stats.get('total_articles', 0)} articles</span>
          </td>
          <td style="width:10px;"></td>
          <td style="background:rgba(139,92,246,0.15);border:1px solid rgba(139,92,246,0.25);border-radius:20px;padding:6px 18px;">
            <span style="color:#C4B5FD;font-size:12px;font-weight:500;">{stats.get('vault_saves', 0)} sauvegardes</span>
          </td>
        </tr></table>
      </td></tr>
    </table>
  </td></tr>

  <!-- Headline -->
  <tr><td style="background:linear-gradient(90deg,#EDE9FE,#DDD6FE);padding:20px 28px;">
    <p style="font-size:17px;font-weight:700;color:#1E293B;margin:0;line-height:1.4;">\U0001f4ca {headline}</p>
  </td></tr>

  <!-- Content -->
  <tr><td style="background:#F8FAFC;padding:24px;">

    <!-- Top 3 -->
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,0.06);overflow:hidden;">
      <tr><td style="background:linear-gradient(90deg,#FEF3C7,#FDE68A);padding:14px 20px;">
        <span style="font-size:13px;font-weight:700;color:#92400E;text-transform:uppercase;letter-spacing:2px;">\U0001f3c6 Top 3 de la semaine</span>
      </td></tr>
      <tr><td style="padding:8px 20px 16px;">
        <table width="100%" cellpadding="0" cellspacing="0">{top_3_html}</table>
      </td></tr>
    </table>

    <!-- Sections -->
    {sections_html}

    <!-- Outlook -->
    {"<table width='100%' cellpadding='0' cellspacing='0' style='background:#fff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,0.04);margin:24px 0 0;overflow:hidden;'><tr><td style='background:linear-gradient(90deg,#ECFDF5,#D1FAE5);padding:14px 20px;'><span style=\"font-size:13px;font-weight:700;color:#059669;text-transform:uppercase;letter-spacing:2px;\">" + chr(0x1f52e) + " Semaine prochaine</span></td></tr><tr><td style='padding:16px 20px;'><p style='color:#374151;font-size:14px;line-height:1.6;margin:0;'>" + outlook + "</p></td></tr></table>" if outlook else ""}

  </td></tr>

  <!-- Footer -->
  <tr><td style="background:linear-gradient(145deg,#0a0a1a,#111827);border-radius:0 0 16px 16px;padding:0;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr><td style="height:1px;background:linear-gradient(90deg,transparent,rgba(139,92,246,0.2),transparent);"></td></tr>
      <tr><td style="padding:20px 28px;text-align:center;">
        <p style="color:#4B5563;font-size:10px;margin:0 0 4px;letter-spacing:0.5px;">
          Genere par <span style="color:#A78BFA;">Agent System</span> &mdash; Recap hebdomadaire
        </p>
        <p style="color:#374151;font-size:9px;margin:0;">Chaque dimanche matin</p>
      </td></tr>
    </table>
  </td></tr>

</table>
</td></tr></table>
</body></html>'''


def build_weekly_plain(digest: dict) -> str:
    lines = [f"WEEKLY AI RECAP — {datetime.now().strftime('%Y-%m-%d')}", "=" * 55, ""]
    lines.append(digest.get("headline", ""))
    lines.append("")

    for i, story in enumerate(digest.get("top_3", []), 1):
        lines.append(f"#{i} {story.get('title', '')}")
        lines.append(f"   {story.get('summary', '')}")
        lines.append(f"   {story.get('url', '')}")
        lines.append("")

    for section in digest.get("sections", []):
        lines.append(f"\n--- {section.get('theme', '')} ---")
        for a in section.get("articles", []):
            lines.append(f"  - {a.get('title', '')} ({a.get('source', '')})")
            lines.append(f"    {a.get('summary', '')}")

    if digest.get("outlook"):
        lines.append(f"\nPROCHAINE SEMAINE: {digest['outlook']}")
    return "\n".join(lines)


def send_weekly(service, recipient, weekly_path):
    today = datetime.now().strftime("%d/%m")

    try:
        digest = json.loads(Path(weekly_path).read_text(encoding="utf-8"))
    except Exception:
        print(f"Cannot read weekly digest: {weekly_path}", file=sys.stderr)
        return

    headline = digest.get("headline", "Recap Hebdomadaire")
    subject = f"\U0001f4ca {headline} — Weekly AI Briefing {today}"

    msg = MIMEMultipart("alternative")
    msg["to"] = recipient
    msg["from"] = recipient
    msg["subject"] = subject

    plain = build_weekly_plain(digest)
    html = render_weekly_html(digest)

    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    result = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    print(f"Weekly digest sent to {recipient} (ID: {result['id']})", file=sys.stderr)

    md_lines = [f"# {headline}\n"]
    for i, s in enumerate(digest.get("top_3", []), 1):
        md_lines.append(f"## #{i} {s.get('title', '')}")
        md_lines.append(f"{s.get('summary', '')}\n")
        md_lines.append(f"[Lire]({s.get('url', '')})\n")
    for sec in digest.get("sections", []):
        md_lines.append(f"### {sec.get('theme', '')}")
        for a in sec.get("articles", []):
            md_lines.append(f"- [{a.get('title', '')}]({a.get('url', '')}) — {a.get('summary', '')}")
    if digest.get("outlook"):
        md_lines.append(f"\n---\n**Semaine prochaine:** {digest['outlook']}")
    Path("/tmp/weekly_body.md").write_text("\n".join(md_lines), encoding="utf-8")

    return result


def main():
    import argparse as _ap
    parser = _ap.ArgumentParser()
    parser.add_argument("--weekly", default=None)
    parser.add_argument("digest_path", nargs="?", default="/tmp/ai_digest.json")
    parser.add_argument("md_fallback", nargs="?", default="/tmp/digest_body.md")
    args = parser.parse_args()

    recipient = os.environ.get("GMAIL_USER_EMAIL")
    if not recipient:
        print("GMAIL_USER_EMAIL not set", file=sys.stderr)
        sys.exit(1)
    service = get_service()

    if args.weekly:
        send_weekly(service, recipient, args.weekly)
    else:
        send_digest(service, recipient, args.digest_path, args.md_fallback)


if __name__ == "__main__":
    main()

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


# ---------------------------------------------------------------------------
# Brand images — used as fallback when article has no og:image
# ---------------------------------------------------------------------------
SOURCE_BRAND_IMAGES = {
    "Anthropic News": "https://cdn.prod.website-files.com/67ce28cfec624e2b733f8a52/68309ab48369f7ad9b4a40e1_open-graph.jpg",
    "OpenAI Blog": "https://images.ctfassets.net/kftzwdyauwt9/3KGOHkSXu53naMuSFNaiwv/cdb0e2f899f524abb71314ab20e09c9c/OAI-white-on-black.png",
    "Google DeepMind": "https://lh3.googleusercontent.com/pKyaXkzFJCqwFqNqmShiVnVpKbYaEPcMrYbfHRdWXag9lnBPK6MmwBJQSrjZFKJzDvjPE3gY7sNSUH9W8Q",
    "HuggingFace Blog": "https://huggingface.co/front/thumbnails/v2-2.png",
    "Mistral News": "https://cms.mistral.ai/assets/060bdeb1-fbff-419c-b2ae-b32b5e441864",
    "TechCrunch AI": "https://techcrunch.com/wp-content/uploads/2015/02/cropped-cropped-favicon-gradient.png",
    "VentureBeat AI": "https://venturebeat.com/wp-content/uploads/2022/09/VB_Logo_Orange.png",
    "AI News": "https://www.artificialintelligence-news.com/wp-content/uploads/2025/01/New-site-SEO-social-banner-1200x600-1.jpg",
    "Ars Technica AI": "https://cdn.arstechnica.net/wp-content/uploads/2016/10/cropped-ars-logo-512_480.png",
    "Google AI Blog": "https://blog.google/static/blogv2/images/google-200x200.png",
    "The Batch": "https://home-wordpress.deeplearning.ai/wp-content/uploads/2024/06/homepage-preview.png",
    "Simon Willison": "https://simonwillison.net/favicon.ico",
    "The Decoder": "https://the-decoder.com/wp-content/uploads/2023/01/the-decoder-logo-dark.png",
    "The Verge AI": "https://cdn.vox-cdn.com/uploads/hub/sbnu_logo_minimal/441/large_The_Verge_logo.png",
    "GitHub Blog": "https://github.githubassets.com/assets/GitHub-Mark-ea2971cee799.png",
    "MIT Tech Review AI": "https://wp.technologyreview.com/wp-content/uploads/2023/10/MIT_TR_Logo_RGB_Master-1.png",
    "Wired AI": "https://www.wired.com/verso/static/wired/assets/logo-header.svg",
    "MarkTechPost": "https://www.marktechpost.com/wp-content/uploads/2022/04/logo-1.png",
    "Latent Space": "https://substackcdn.com/image/fetch/f_auto,q_auto:good,fl_progressive:steep/https://substack-post-media.s3.amazonaws.com/public/images/latent-space-logo.png",
    "AI Snake Oil": "https://substackcdn.com/image/fetch/f_auto,q_auto:good,fl_progressive:steep/https://substack-post-media.s3.amazonaws.com/public/images/ai-snake-oil-logo.png",
    "Last Week in AI": "https://substackcdn.com/image/fetch/f_auto,q_auto:good,fl_progressive:steep/https://substack-post-media.s3.amazonaws.com/public/images/last-week-ai-logo.png",
    "Interconnects": "https://substackcdn.com/image/fetch/f_auto,q_auto:good,fl_progressive:steep/https://substack-post-media.s3.amazonaws.com/public/images/interconnects-logo.png",
    "Ahead of AI": "https://substackcdn.com/image/fetch/f_auto,q_auto:good,fl_progressive:steep/https://substack-post-media.s3.amazonaws.com/public/images/ahead-of-ai-logo.png",
}

# Category → gradient for placeholder image blocks
CAT_GRADIENTS = {
    "Modeles": "linear-gradient(135deg,#7C3AED,#4F46E5)",
    "Outils & Plateformes": "linear-gradient(135deg,#0284C7,#06B6D4)",
    "Recherche": "linear-gradient(135deg,#059669,#10B981)",
    "Business & Levees": "linear-gradient(135deg,#D97706,#F59E0B)",
    "Open Source": "linear-gradient(135deg,#4F46E5,#7C3AED)",
    "Regulation & Ethique": "linear-gradient(135deg,#DC2626,#EF4444)",
    "Models": "linear-gradient(135deg,#7C3AED,#4F46E5)",
    "Tools & Platforms": "linear-gradient(135deg,#0284C7,#06B6D4)",
    "Research": "linear-gradient(135deg,#059669,#10B981)",
    "Business & Funding": "linear-gradient(135deg,#D97706,#F59E0B)",
}

CAT_COLORS = {
    "Modeles": "#7C3AED", "Outils & Plateformes": "#0284C7",
    "Recherche": "#059669", "Business & Levees": "#D97706",
    "Open Source": "#4F46E5", "Regulation & Ethique": "#DC2626",
    "Models": "#7C3AED", "Tools & Platforms": "#0284C7",
    "Research": "#059669", "Business & Funding": "#D97706",
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def _favicon(url: str) -> str:
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc or url
    except Exception:
        domain = url
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=32"


def _resolve_image(article: dict) -> str:
    img = article.get("image_url", "")
    if img and "s2/favicons" not in img and len(img) > 20:
        qs = img.split("?")[-1] if "?" in img else ""
        if "sz=" not in qs:
            return img
    source = article.get("source", "")
    brand = SOURCE_BRAND_IMAGES.get(source, "")
    if brand:
        return brand
    return ""


def _placeholder_block(article: dict, height: int = 160) -> str:
    cat = article.get("category", "")
    gradient = CAT_GRADIENTS.get(cat, "linear-gradient(135deg,#334155,#475569)")
    source = escape(article.get("source", "AI"))
    favicon = _favicon(article.get("url", ""))
    return (
        f'<td style="background:{gradient};height:{height}px;text-align:center;vertical-align:middle;">'
        f'<img src="{favicon}" width="40" height="40" '
        f'style="border-radius:10px;border:2px solid rgba(255,255,255,0.3);display:inline-block;" />'
        f'<br/><span style="color:rgba(255,255,255,0.7);font-size:11px;font-weight:500;'
        f'letter-spacing:1px;margin-top:8px;display:inline-block;">{source}</span>'
        f'</td>'
    )


def _cat_pill(cat: str) -> str:
    color = CAT_COLORS.get(cat, "#6B7280")
    return (f'<span style="display:inline-block;background:{color}12;color:{color};'
            f'font-size:10px;font-weight:700;padding:4px 12px;border-radius:20px;'
            f'letter-spacing:0.8px;text-transform:uppercase;">{escape(cat)}</span>')


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
        "---", "", article.get("summary", ""),
    ]
    encoded_title = quote(f"\U0001f4cc {title}"[:120])
    encoded_body = quote("\n".join(body_lines))
    url = f"https://github.com/{VAULT_REPO}/issues/new?labels=vault-save&title={encoded_title}&body={encoded_body}"
    return (f'<a href="{url}" style="display:inline-block;background:#F0F0FF;'
            f'color:#4F46E5;text-decoration:none;font-size:10px;font-weight:700;'
            f'padding:5px 12px;border-radius:6px;letter-spacing:0.3px;">SAVE</a>')


def _deep_dive_btn(article: dict) -> str:
    title = article.get("title", "Article")
    body_lines = [
        f"source: {article.get('source', '')}",
        f"url: {article.get('url', '')}",
        f"category: {article.get('category', '')}",
        "---", "",
        f"Analyse approfondie demandee pour : {title}",
        "", article.get("summary", ""),
    ]
    encoded_title = quote(f"\U0001f50d Deep dive : {title}"[:120])
    encoded_body = quote("\n".join(body_lines))
    url = f"https://github.com/{VAULT_REPO}/issues/new?labels=deep-dive&title={encoded_title}&body={encoded_body}"
    return (f'<a href="{url}" style="display:inline-block;background:#FFF0F6;'
            f'color:#BE185D;text-decoration:none;font-size:10px;font-weight:700;'
            f'padding:5px 12px;border-radius:6px;letter-spacing:0.3px;">DEEP DIVE</a>')


def _action_row(article: dict) -> str:
    url = article.get("url", "#")
    return (
        f'<table cellpadding="0" cellspacing="0" style="margin-top:14px;"><tr>'
        f'<td style="padding-right:6px;">'
        f'<a href="{escape(url)}" style="display:inline-block;background:#111827;'
        f'color:#fff;text-decoration:none;font-size:11px;font-weight:700;'
        f'padding:7px 18px;border-radius:6px;letter-spacing:0.3px;">LIRE</a></td>'
        f'<td style="padding-right:6px;">{_vault_btn(article)}</td>'
        f'<td>{_deep_dive_btn(article)}</td>'
        f'</tr></table>'
    )


# ---------------------------------------------------------------------------
# Render functions — individual article templates
# ---------------------------------------------------------------------------
def _render_top_story(story: dict) -> str:
    title = escape(story.get("title", ""))
    url = story.get("url", "#")
    source = escape(story.get("source", ""))
    summary = escape(story.get("summary", ""))
    image_url = _resolve_image(story)
    cat = story.get("category", "")
    tags = story.get("company_tags", [])

    if image_url:
        image_cell = (
            f'<td style="padding:0;">'
            f'<a href="{escape(url)}" style="text-decoration:none;">'
            f'<img src="{escape(image_url)}" alt="" '
            f'style="width:100%;height:220px;object-fit:cover;display:block;" />'
            f'</a></td>'
        )
    else:
        image_cell = _placeholder_block(story, 200)

    tags_html = " ".join(
        f'<span style="display:inline-block;background:#EFF6FF;color:#3B82F6;font-size:9px;'
        f'font-weight:600;padding:3px 8px;border-radius:10px;margin:2px 3px 0 0;">{escape(t)}</span>'
        for t in tags[:4]
    )

    return f'''
    <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 24px;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.08);">
      <tr>{image_cell}</tr>
      <tr><td style="padding:24px 28px 0;">
        <table cellpadding="0" cellspacing="0"><tr>
          <td style="padding-right:10px;">{_cat_pill(cat)}</td>
          <td><span style="font-size:10px;font-weight:700;color:#EA580C;background:#FFF7ED;padding:4px 10px;border-radius:20px;letter-spacing:0.8px;text-transform:uppercase;">TOP STORY</span></td>
        </tr></table>
      </td></tr>
      <tr><td style="padding:14px 28px 0;">
        <a href="{escape(url)}" style="color:#0F172A;text-decoration:none;font-size:22px;font-weight:800;line-height:1.3;display:block;font-family:Georgia,'Times New Roman',serif;">{title}</a>
      </td></tr>
      <tr><td style="padding:10px 28px 0;">
        <table cellpadding="0" cellspacing="0"><tr>
          <td style="padding-right:8px;"><img src="{_favicon(url)}" width="16" height="16" style="border-radius:4px;vertical-align:middle;" /></td>
          <td><span style="font-size:12px;color:#64748B;font-weight:500;">{source}</span></td>
        </tr></table>
      </td></tr>
      <tr><td style="padding:16px 28px 0;">
        <p style="color:#334155;font-size:15px;line-height:1.75;margin:0;">{summary}</p>
      </td></tr>
      <tr><td style="padding:8px 28px 0;">{tags_html}</td></tr>
      <tr><td style="padding:4px 28px 24px;">{_action_row(story)}</td></tr>
    </table>'''


def _render_card(article: dict) -> str:
    title = escape(article.get("title", ""))
    url = article.get("url", "#")
    source = escape(article.get("source", ""))
    summary = escape(article.get("summary", ""))
    cat = article.get("category", "")
    image_url = _resolve_image(article)

    if image_url:
        image_cell = (
            f'<td style="padding:0;">'
            f'<a href="{escape(url)}" style="text-decoration:none;">'
            f'<img src="{escape(image_url)}" alt="" '
            f'style="width:100%;height:160px;object-fit:cover;display:block;" /></a></td>'
        )
    else:
        image_cell = _placeholder_block(article, 140)

    return f'''
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:10px;overflow:hidden;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
      <tr>{image_cell}</tr>
      <tr><td style="padding:16px 22px 0;">
        {_cat_pill(cat)}
      </td></tr>
      <tr><td style="padding:10px 22px 0;">
        <a href="{escape(url)}" style="color:#0F172A;text-decoration:none;font-size:16px;font-weight:700;line-height:1.35;display:block;">{title}</a>
      </td></tr>
      <tr><td style="padding:8px 22px 0;">
        <table cellpadding="0" cellspacing="0"><tr>
          <td style="padding-right:6px;"><img src="{_favicon(url)}" width="14" height="14" style="border-radius:3px;vertical-align:middle;" /></td>
          <td><span style="font-size:11px;color:#94A3B8;font-weight:500;">{source}</span></td>
        </tr></table>
      </td></tr>
      <tr><td style="padding:12px 22px 0;">
        <p style="color:#475569;font-size:13px;line-height:1.65;margin:0;">{summary}</p>
      </td></tr>
      <tr><td style="padding:4px 22px 20px;">
        {_action_row(article)}
      </td></tr>
    </table>'''


def _render_compact(article: dict) -> str:
    title = escape(article.get("title", ""))
    url = article.get("url", "#")
    source = escape(article.get("source", ""))
    summary = escape(article.get("summary", ""))
    cat = article.get("category", "")
    color = CAT_COLORS.get(cat, "#94A3B8")
    image_url = _resolve_image(article)

    if image_url:
        thumb = (f'<img src="{escape(image_url)}" width="56" height="56" '
                 f'style="border-radius:8px;object-fit:cover;display:block;" />')
    else:
        thumb = (f'<div style="width:56px;height:56px;border-radius:8px;'
                 f'background:{CAT_GRADIENTS.get(cat, "linear-gradient(135deg,#334155,#475569)")};'
                 f'text-align:center;line-height:56px;">'
                 f'<img src="{_favicon(url)}" width="24" height="24" style="border-radius:4px;vertical-align:middle;" />'
                 f'</div>')

    return f'''
    <tr><td style="padding:14px 0;border-bottom:1px solid #F1F5F9;">
      <table width="100%" cellpadding="0" cellspacing="0"><tr>
        <td width="56" style="vertical-align:top;padding-right:16px;">
          <a href="{escape(url)}" style="text-decoration:none;">{thumb}</a>
        </td>
        <td style="vertical-align:top;">
          <span style="display:inline-block;width:3px;height:3px;border-radius:50%;background:{color};margin-right:5px;vertical-align:middle;"></span>
          <span style="font-size:10px;color:{color};font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">{escape(cat)}</span>
          <br/>
          <a href="{escape(url)}" style="color:#0F172A;text-decoration:none;font-size:14px;font-weight:600;line-height:1.35;">{title}</a>
          <br/>
          <span style="font-size:11px;color:#94A3B8;">{source}</span>
          <p style="color:#64748B;font-size:12px;line-height:1.55;margin:5px 0 0;">{summary}</p>
          <table cellpadding="0" cellspacing="0" style="margin-top:8px;"><tr>
            <td style="padding-right:6px;">{_vault_btn(article)}</td>
            <td>{_deep_dive_btn(article)}</td>
          </tr></table>
        </td>
      </tr></table>
    </td></tr>'''


def _render_trend(trend) -> str:
    if isinstance(trend, dict):
        title = escape(trend.get("title", ""))
        desc = escape(trend.get("description", ""))
        return (f'<tr><td style="padding:14px 0;border-bottom:1px solid #F1F5F9;">'
                f'<span style="font-size:14px;font-weight:700;color:#0F172A;">{title}</span><br/>'
                f'<span style="font-size:13px;color:#64748B;line-height:1.55;">{desc}</span>'
                f'</td></tr>')
    return (f'<tr><td style="padding:12px 0;border-bottom:1px solid #F1F5F9;">'
            f'<span style="font-size:13px;color:#334155;">{escape(str(trend))}</span>'
            f'</td></tr>')


# ---------------------------------------------------------------------------
# URL validation
# ---------------------------------------------------------------------------
def _validate_urls(digest: dict) -> dict:
    import urllib.request as _ur

    def _check(url: str) -> bool:
        if not url or not url.startswith("http"):
            return False
        try:
            req = _ur.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
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


# ---------------------------------------------------------------------------
# Section header helper
# ---------------------------------------------------------------------------
def _section_header(label: str, color: str, border_color: str) -> str:
    return (f'<table width="100%" cellpadding="0" cellspacing="0" style="margin:32px 0 16px;">'
            f'<tr><td>'
            f'<span style="font-size:11px;font-weight:800;color:{color};text-transform:uppercase;'
            f'letter-spacing:3px;">{label}</span>'
            f'<table width="100%" cellpadding="0" cellspacing="0" style="margin-top:8px;"><tr>'
            f'<td style="width:40px;height:2px;background:{border_color};"></td>'
            f'<td style="height:2px;background:{border_color}22;"></td>'
            f'</tr></table>'
            f'</td></tr></table>')


# ---------------------------------------------------------------------------
# Main render — full HTML newsletter
# ---------------------------------------------------------------------------
def render_digest_html(digest: dict) -> str:
    now = datetime.now()
    days_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    months_fr = ["", "janvier", "fevrier", "mars", "avril", "mai", "juin",
                 "juillet", "aout", "septembre", "octobre", "novembre", "decembre"]
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

    must_read_section = ""
    if must_reads:
        must_read_section = _section_header("A ne pas rater", "#DC2626", "#DC2626") + must_read_cards

    important_section = ""
    if important:
        important_section = _section_header("Important", "#D97706", "#D97706") + important_cards

    compact_section = ""
    if worth_noting:
        compact_section = (
            _section_header("En bref", "#64748B", "#94A3B8")
            + f'<table width="100%" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:10px;'
            f'overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
            f'<tr><td style="padding:4px 22px 10px;">'
            f'<table width="100%" cellpadding="0" cellspacing="0">{compact_rows}</table>'
            f'</td></tr></table>'
        )

    trends_section = ""
    if trends:
        trends_section = (
            _section_header("Tendances", "#059669", "#059669")
            + f'<table width="100%" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:10px;'
            f'overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
            f'<tr><td style="padding:6px 22px 14px;">'
            f'<table width="100%" cellpadding="0" cellspacing="0">{trends_rows}</table>'
            f'</td></tr></table>'
        )

    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Briefing</title>
</head>
<body style="margin:0;padding:0;background-color:#F8FAFC;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;-webkit-font-smoothing:antialiased;">

<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#F8FAFC;">
<tr><td align="center" style="padding:24px 16px;">

<table width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;">

  <!-- Header -->
  <tr><td style="background:#0F172A;border-radius:12px 12px 0 0;padding:0;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr><td style="height:2px;background:linear-gradient(90deg,#6366F1,#8B5CF6,#A78BFA,#6366F1);"></td></tr>
      <tr><td style="padding:36px 36px 0;text-align:center;">
        <table cellpadding="0" cellspacing="0" style="margin:0 auto;"><tr>
          <td style="width:24px;height:1px;background:linear-gradient(90deg,transparent,#6366F180);"></td>
          <td style="padding:0 12px;">
            <span style="font-size:10px;font-weight:700;letter-spacing:5px;text-transform:uppercase;color:#818CF8;">Intelligence</span>
          </td>
          <td style="width:24px;height:1px;background:linear-gradient(90deg,#6366F180,transparent);"></td>
        </tr></table>
      </td></tr>
      <tr><td style="text-align:center;padding:12px 36px 0;">
        <span style="color:#F8FAFC;font-size:30px;font-weight:300;letter-spacing:3px;font-family:Georgia,'Times New Roman',serif;">AI Briefing</span>
      </td></tr>
      <tr><td style="text-align:center;padding:14px 36px 0;">
        <span style="color:#475569;font-size:11px;letter-spacing:2px;text-transform:uppercase;font-weight:500;">{date_str}</span>
      </td></tr>
      <tr><td style="padding:20px 36px 32px;text-align:center;">
        <table cellpadding="0" cellspacing="0" style="margin:0 auto;"><tr>
          <td style="background:rgba(99,102,241,0.12);border-radius:20px;padding:5px 16px;">
            <span style="color:#A5B4FC;font-size:11px;font-weight:600;">{n_articles} articles</span>
          </td>
          <td style="width:8px;"></td>
          <td style="background:rgba(99,102,241,0.12);border-radius:20px;padding:5px 16px;">
            <span style="color:#A5B4FC;font-size:11px;font-weight:600;">{n_sources} sources</span>
          </td>
        </tr></table>
      </td></tr>
    </table>
  </td></tr>

  <!-- Headline -->
  <tr><td style="background:#fff;padding:24px 36px;border-bottom:1px solid #E2E8F0;">
    <p style="font-size:18px;font-weight:800;color:#0F172A;margin:0 0 6px;line-height:1.4;font-family:Georgia,'Times New Roman',serif;">{headline}</p>
    {"<p style='font-size:14px;color:#64748B;margin:0;line-height:1.5;'>" + one_liner + "</p>" if one_liner else ""}
  </td></tr>

  <!-- Content -->
  <tr><td style="background:#F8FAFC;padding:8px 28px 32px;">

    {top_story_html}
    {must_read_section}
    {important_section}
    {compact_section}
    {trends_section}

  </td></tr>

  <!-- Footer -->
  <tr><td style="background:#0F172A;border-radius:0 0 12px 12px;padding:0;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr><td style="height:1px;background:linear-gradient(90deg,transparent,#6366F130,transparent);"></td></tr>
      <tr><td style="padding:24px 36px;text-align:center;">
        <p style="color:#475569;font-size:11px;margin:0 0 4px;letter-spacing:0.5px;">
          <span style="color:#818CF8;">Agent System</span> &mdash; Gemini + Claude
        </p>
        <p style="color:#334155;font-size:10px;margin:0;">Chaque matin a 7h30 &bull; {n_sources} sources scannees</p>
      </td></tr>
    </table>
  </td></tr>

</table>
</td></tr>
</table>

</body>
</html>'''


# ---------------------------------------------------------------------------
# Plain text version
# ---------------------------------------------------------------------------
def build_plain_text(digest: dict) -> str:
    lines = [f"AI BRIEFING — {datetime.now().strftime('%Y-%m-%d')}", "=" * 50, ""]
    lines.append(digest.get("headline", ""))
    if digest.get("one_liner"):
        lines.append(digest["one_liner"])
    lines.append("")

    top = digest.get("top_story")
    if top:
        lines.append(f"*** TOP STORY: {top.get('title', '')}")
        lines.append(f"    {top.get('source', '')} | {top.get('category', '')}")
        lines.append(f"    {top.get('summary', '')}")
        lines.append(f"    {top.get('url', '')}")
        lines.append("")

    for article in digest.get("articles", []):
        imp = article.get("importance", "")
        marker = "[!!!]" if imp == "must_read" else "[!!]" if imp == "important" else "[.]"
        lines.append(f"{marker} {article.get('title', '')}")
        lines.append(f"    {article.get('source', '')} | {article.get('category', '')}")
        lines.append(f"    {article.get('summary', '')}")
        lines.append(f"    {article.get('url', '')}")
        lines.append("")

    if digest.get("trends"):
        lines.append("TENDANCES:")
        for t in digest["trends"]:
            if isinstance(t, dict):
                lines.append(f"  - {t.get('title', '')}: {t.get('description', '')}")
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
<body style="font-family:-apple-system,sans-serif;max-width:640px;margin:0 auto;padding:20px;line-height:1.6;color:#333;">{html}</body></html>'''


# ---------------------------------------------------------------------------
# Send functions
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Weekly digest
# ---------------------------------------------------------------------------
def render_weekly_html(digest: dict) -> str:
    now = datetime.now()
    days_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    months_fr = ["", "janvier", "fevrier", "mars", "avril", "mai", "juin",
                 "juillet", "aout", "septembre", "octobre", "novembre", "decembre"]
    date_str = f"{days_fr[now.weekday()]} {now.day} {months_fr[now.month]} {now.year}"

    headline = escape(digest.get("headline", "Recap Hebdomadaire"))
    top_3 = digest.get("top_3", [])
    sections = digest.get("sections", [])
    outlook = escape(digest.get("outlook", ""))
    stats = digest.get("stats", {})

    top_3_html = ""
    for i, story in enumerate(top_3, 1):
        medal = ["\U0001f947", "\U0001f948", "\U0001f949"][i - 1] if i <= 3 else ""
        title = escape(story.get("title", ""))
        summary = escape(story.get("summary", ""))
        url = story.get("url", "#")
        cat = story.get("category", "")
        day = escape(story.get("day", ""))
        top_3_html += f'''
        <tr><td style="padding:18px 0;border-bottom:1px solid #F1F5F9;">
          <table width="100%" cellpadding="0" cellspacing="0"><tr>
            <td width="48" style="vertical-align:top;text-align:center;padding-top:2px;">
              <span style="font-size:28px;">{medal}</span>
            </td>
            <td style="padding-left:8px;">
              <a href="{escape(url)}" style="color:#0F172A;text-decoration:none;font-size:16px;font-weight:700;line-height:1.3;">{title}</a>
              <br/><span style="font-size:10px;color:#94A3B8;font-weight:500;">{day} &bull; {escape(cat)}</span>
              <p style="color:#475569;font-size:13px;line-height:1.6;margin:6px 0 0;">{summary}</p>
            </td>
          </tr></table>
        </td></tr>'''

    sections_html = ""
    for section in sections:
        theme = escape(section.get("theme", ""))
        items = ""
        for a in section.get("articles", []):
            t = escape(a.get("title", ""))
            s = escape(a.get("summary", ""))
            u = a.get("url", "#")
            src = escape(a.get("source", ""))
            items += f'''<tr><td style="padding:10px 0;border-bottom:1px solid #F1F5F9;">
              <a href="{escape(u)}" style="color:#0F172A;text-decoration:none;font-size:13px;font-weight:600;">{t}</a>
              <span style="font-size:11px;color:#94A3B8;"> — {src}</span>
              <br/><span style="font-size:12px;color:#64748B;">{s}</span>
            </td></tr>'''
        sections_html += f'''
        <table width="100%" cellpadding="0" cellspacing="0" style="margin:20px 0 0;">
          <tr><td style="padding:10px 16px;background:#F8FAFC;border-radius:8px 8px 0 0;">
            <span style="font-size:12px;font-weight:800;color:#334155;text-transform:uppercase;letter-spacing:1px;">{theme}</span>
          </td></tr>
          <tr><td style="padding:4px 16px 12px;">
            <table width="100%" cellpadding="0" cellspacing="0">{items}</table>
          </td></tr>
        </table>'''

    outlook_section = ""
    if outlook:
        outlook_section = (
            f'<table width="100%" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:10px;'
            f'overflow:hidden;margin:28px 0 0;box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
            f'<tr><td style="padding:16px 22px;border-left:3px solid #059669;">'
            f'<span style="font-size:11px;font-weight:800;color:#059669;text-transform:uppercase;letter-spacing:2px;">Semaine prochaine</span>'
            f'<p style="color:#334155;font-size:14px;line-height:1.6;margin:8px 0 0;">{outlook}</p>'
            f'</td></tr></table>'
        )

    return f'''<!DOCTYPE html>
<html lang="fr">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#F8FAFC;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#F8FAFC;">
<tr><td align="center" style="padding:24px 16px;">
<table width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;">

  <tr><td style="background:#0F172A;border-radius:12px 12px 0 0;padding:0;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr><td style="height:2px;background:linear-gradient(90deg,#8B5CF6,#6366F1,#4F46E5,#6366F1,#8B5CF6);"></td></tr>
      <tr><td style="padding:36px 36px 0;text-align:center;">
        <span style="font-size:10px;font-weight:700;letter-spacing:5px;color:#A78BFA;text-transform:uppercase;">Recap Hebdo</span>
      </td></tr>
      <tr><td style="text-align:center;padding:12px 36px 0;">
        <span style="color:#F8FAFC;font-size:28px;font-weight:300;letter-spacing:3px;font-family:Georgia,'Times New Roman',serif;">Weekly AI Briefing</span>
      </td></tr>
      <tr><td style="text-align:center;padding:14px 36px 0;">
        <span style="color:#475569;font-size:11px;letter-spacing:2px;text-transform:uppercase;">{date_str}</span>
      </td></tr>
      <tr><td style="padding:20px 36px 32px;text-align:center;">
        <table cellpadding="0" cellspacing="0" style="margin:0 auto;"><tr>
          <td style="background:rgba(139,92,246,0.12);border-radius:20px;padding:5px 16px;">
            <span style="color:#C4B5FD;font-size:11px;font-weight:600;">{stats.get('daily_digests', 0)} digests</span>
          </td>
          <td style="width:8px;"></td>
          <td style="background:rgba(139,92,246,0.12);border-radius:20px;padding:5px 16px;">
            <span style="color:#C4B5FD;font-size:11px;font-weight:600;">{stats.get('total_articles', 0)} articles</span>
          </td>
        </tr></table>
      </td></tr>
    </table>
  </td></tr>

  <tr><td style="background:#fff;padding:24px 36px;border-bottom:1px solid #E2E8F0;">
    <p style="font-size:18px;font-weight:800;color:#0F172A;margin:0;font-family:Georgia,'Times New Roman',serif;">{headline}</p>
  </td></tr>

  <tr><td style="background:#F8FAFC;padding:8px 28px 32px;">

    <table width="100%" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:10px;overflow:hidden;margin:24px 0 0;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
      <tr><td style="padding:18px 22px;border-bottom:1px solid #F1F5F9;">
        <span style="font-size:11px;font-weight:800;color:#D97706;text-transform:uppercase;letter-spacing:2px;">Top 3 de la semaine</span>
      </td></tr>
      <tr><td style="padding:4px 22px 14px;">
        <table width="100%" cellpadding="0" cellspacing="0">{top_3_html}</table>
      </td></tr>
    </table>

    {sections_html}
    {outlook_section}

  </td></tr>

  <tr><td style="background:#0F172A;border-radius:0 0 12px 12px;padding:0;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr><td style="height:1px;background:linear-gradient(90deg,transparent,#8B5CF620,transparent);"></td></tr>
      <tr><td style="padding:24px 36px;text-align:center;">
        <p style="color:#475569;font-size:11px;margin:0 0 4px;"><span style="color:#A78BFA;">Agent System</span> &mdash; Recap hebdomadaire</p>
        <p style="color:#334155;font-size:10px;margin:0;">Chaque dimanche matin</p>
      </td></tr>
    </table>
  </td></tr>

</table>
</td></tr></table>
</body></html>'''


def build_weekly_plain(digest: dict) -> str:
    lines = [f"WEEKLY AI RECAP — {datetime.now().strftime('%Y-%m-%d')}", "=" * 50, ""]
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
        lines.append(f"\nSEMAINE PROCHAINE: {digest['outlook']}")
    return "\n".join(lines)


def send_weekly(service, recipient, weekly_path):
    today = datetime.now().strftime("%d/%m")

    try:
        digest = json.loads(Path(weekly_path).read_text(encoding="utf-8"))
    except Exception:
        print(f"Cannot read weekly digest: {weekly_path}", file=sys.stderr)
        return

    headline = digest.get("headline", "Recap Hebdomadaire")
    subject = f"{headline} — Weekly AI Briefing {today}"

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


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------
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

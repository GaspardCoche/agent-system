#!/usr/bin/env python3
"""
Generates static HTML pages for digest archive on GitHub Pages.
Input: /tmp/ai_digest.json
Output: docs/digest/YYYY-MM-DD.html + docs/digest/index.html (updated)
"""
import json
import sys
from datetime import datetime
from html import escape
from pathlib import Path

SITE_URL = "https://gaspardcoche.github.io/agent-system"

CAT_COLORS = {
    "Modeles": "#7C3AED", "Outils & Plateformes": "#0284C7",
    "Recherche": "#059669", "Business & Levees": "#D97706",
    "Open Source": "#4F46E5", "Regulation & Ethique": "#DC2626",
    "Code & Dev": "#EA580C", "Google & Cloud": "#0891B2",
    "Tech & Business": "#6D28D9",
}

CAT_ICONS = {
    "Modeles": "\U0001f9e0", "Outils & Plateformes": "⚙️",
    "Recherche": "\U0001f52c", "Business & Levees": "\U0001f4b0",
    "Open Source": "\U0001f310", "Regulation & Ethique": "⚖️",
    "Code & Dev": "\U0001f4bb", "Google & Cloud": "☁️",
    "Tech & Business": "\U0001f4c8",
}

IMP_LABELS = {
    "must_read": ("Must Read", "#DC2626", "#FEF2F2"),
    "important": ("Important", "#D97706", "#FFFBEB"),
    "worth_noting": ("A noter", "#64748B", "#F8FAFC"),
}

DAYS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
MONTHS_FR = ["", "janvier", "février", "mars", "avril", "mai", "juin",
             "juillet", "août", "septembre", "octobre", "novembre", "décembre"]


def _favicon(url: str) -> str:
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc or url
    except Exception:
        domain = url
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=32"


def _format_date_fr(date_str: str) -> str:
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return f"{DAYS_FR[dt.weekday()]} {dt.day} {MONTHS_FR[dt.month]} {dt.year}"
    except Exception:
        return date_str


def _article_card(article: dict, featured: bool = False) -> str:
    title = escape(article.get("title", ""))
    url = article.get("url", "#")
    source = escape(article.get("source", ""))
    summary = escape(article.get("summary", ""))
    cat = article.get("category", "")
    color = CAT_COLORS.get(cat, "#6B7280")
    icon = CAT_ICONS.get(cat, "")
    image_url = article.get("image_url", "")
    importance = article.get("importance", "")
    tags = article.get("company_tags", [])

    imp_html = ""
    if importance in IMP_LABELS:
        label, fg, bg = IMP_LABELS[importance]
        imp_html = f'<span class="imp-badge" style="color:{fg};background:{bg};">{label}</span>'

    if image_url and len(image_url) > 20 and "s2/favicons" not in image_url:
        img_html = (
            f'<a href="{escape(url)}" class="card-img-link">'
            f'<img src="{escape(image_url)}" alt="" class="card-img" loading="lazy" />'
            f'</a>'
        )
    else:
        img_html = (
            f'<div class="card-placeholder" style="background:linear-gradient(135deg,{color}18,{color}08);">'
            f'<img src="{_favicon(url)}" width="36" height="36" style="border-radius:8px;opacity:0.7;" />'
            f'</div>'
        )

    tags_html = "".join(f'<span class="tag">{escape(t)}</span>' for t in tags[:3])
    cls = "card card-featured" if featured else "card"

    return f'''<article class="{cls}">
      {img_html}
      <div class="card-body">
        <div class="card-meta">
          <span class="cat-pill" style="--c:{color};">{icon} {escape(cat)}</span>
          {imp_html}
        </div>
        <h3><a href="{escape(url)}">{title}</a></h3>
        <div class="source-line">
          <img src="{_favicon(url)}" width="14" height="14" />
          <span>{source}</span>
        </div>
        <p class="summary">{summary}</p>
        {f'<div class="card-tags">{tags_html}</div>' if tags_html else ''}
        <a href="{escape(url)}" class="read-link">Lire l'article &rarr;</a>
      </div>
    </article>'''


def _trend_item(trend) -> str:
    if isinstance(trend, dict):
        title = escape(trend.get("title", ""))
        desc = escape(trend.get("description", ""))
        return f'<div class="trend-item"><strong>{title}</strong><p>{desc}</p></div>'
    return f'<div class="trend-item"><p>{escape(str(trend))}</p></div>'


def _ext_row(article: dict) -> str:
    title = escape(article.get("title", ""))
    url = article.get("url", "#")
    source = escape(article.get("source", ""))
    summary = escape(article.get("summary", ""))
    cat = article.get("category", "")
    color = CAT_COLORS.get(cat, "#6B7280")

    return f'''<div class="ext-row">
      <div class="ext-dot" style="background:{color};"></div>
      <div class="ext-body">
        <a href="{escape(url)}" class="ext-title">{title}</a>
        <span class="ext-source">{source}</span>
        <p class="ext-summary">{summary}</p>
      </div>
    </div>'''


def render_page(digest: dict, date_str: str) -> str:
    headline = escape(digest.get("headline", "Digest IA"))
    one_liner = escape(digest.get("one_liner", ""))
    articles = digest.get("articles", [])
    extended = digest.get("extended", [])
    trends = digest.get("trends", [])
    stats = digest.get("stats", {})
    top_story = digest.get("top_story")

    must_reads = [a for a in articles if a.get("importance") == "must_read"]
    important = [a for a in articles if a.get("importance") == "important"]
    worth_noting = [a for a in articles if a.get("importance") == "worth_noting"]

    n_articles = stats.get("articles_extracted", len(articles) + (1 if top_story else 0))
    n_sources = stats.get("sources_scraped", 10)
    n_extended = len(extended)
    date_fr = _format_date_fr(date_str)

    top_html = _article_card(top_story, featured=True) if top_story else ""
    must_html = "".join(_article_card(a) for a in must_reads)
    important_html = "".join(_article_card(a) for a in important)
    noting_html = "".join(_article_card(a) for a in worth_noting)
    trends_html = "".join(_trend_item(t) for t in trends)

    ext_by_cat: dict[str, list] = {}
    for a in extended:
        c = a.get("category", "Autre")
        ext_by_cat.setdefault(c, []).append(a)

    ext_sections = ""
    for cat, items in ext_by_cat.items():
        color = CAT_COLORS.get(cat, "#6B7280")
        icon = CAT_ICONS.get(cat, "")
        rows = "".join(_ext_row(a) for a in items)
        ext_sections += f'''
        <div class="ext-section">
          <h3 class="ext-cat-title" style="--c:{color};">{icon} {escape(cat)}</h3>
          {rows}
        </div>'''

    nav_items = ""
    if top_story:
        nav_items += '<a href="#top-story">Top Story</a>'
    if must_reads:
        nav_items += '<a href="#must-read">Must Read</a>'
    if important:
        nav_items += '<a href="#important">Important</a>'
    if worth_noting:
        nav_items += '<a href="#worth-noting">En bref</a>'
    if trends:
        nav_items += '<a href="#trends">Tendances</a>'
    if extended:
        nav_items += f'<a href="#bonus">Bonus (+{n_extended})</a>'

    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{headline} — AI Briefing {date_str}</title>
  <meta name="description" content="{one_liner}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@400;700;800&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #F7F8FA;
      --surface: #FFFFFF;
      --border: #E8ECF1;
      --border-light: #F1F5F9;
      --text: #0F172A;
      --text-secondary: #475569;
      --text-muted: #94A3B8;
      --accent: #4F46E5;
      --accent-light: #EEF2FF;
      --radius: 16px;
      --shadow-sm: 0 1px 2px rgba(0,0,0,0.04);
      --shadow-md: 0 4px 16px rgba(0,0,0,0.06);
      --shadow-lg: 0 12px 40px rgba(0,0,0,0.1);
      --max-w: 1120px;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: var(--bg); color: var(--text); font-family: 'Inter', -apple-system, system-ui, sans-serif; -webkit-font-smoothing: antialiased; line-height: 1.6; }}

    /* ── Header ───────────────────────────────────── */
    .hero {{
      background: #0F172A;
      color: #F8FAFC;
      position: relative;
      overflow: hidden;
    }}
    .hero::before {{
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
      background: linear-gradient(90deg, #6366F1, #8B5CF6, #EC4899, #8B5CF6, #6366F1);
      background-size: 200% 100%;
      animation: shimmer 6s ease-in-out infinite;
    }}
    @keyframes shimmer {{ 0%,100% {{ background-position: 0% 50%; }} 50% {{ background-position: 100% 50%; }} }}

    .hero-inner {{
      max-width: var(--max-w);
      margin: 0 auto;
      padding: 56px 32px 48px;
      text-align: center;
    }}
    .hero-label {{
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 6px;
      text-transform: uppercase;
      color: #818CF8;
      display: inline-flex;
      align-items: center;
      gap: 12px;
    }}
    .hero-label::before, .hero-label::after {{
      content: '';
      width: 24px;
      height: 1px;
      background: linear-gradient(90deg, transparent, #818CF860);
    }}
    .hero-label::after {{
      background: linear-gradient(90deg, #818CF860, transparent);
    }}
    .hero h1 {{
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 42px;
      font-weight: 400;
      letter-spacing: 2px;
      margin: 16px 0 8px;
    }}
    .hero-date {{
      color: #64748B;
      font-size: 12px;
      letter-spacing: 2px;
      text-transform: uppercase;
      font-weight: 500;
    }}
    .hero-pills {{
      display: flex;
      justify-content: center;
      gap: 8px;
      margin-top: 20px;
      flex-wrap: wrap;
    }}
    .hero-pill {{
      background: rgba(99,102,241,0.1);
      border: 1px solid rgba(99,102,241,0.15);
      border-radius: 20px;
      padding: 5px 16px;
      color: #A5B4FC;
      font-size: 11px;
      font-weight: 600;
    }}

    /* ── Headline bar ─────────────────────────────── */
    .headline-bar {{
      background: var(--surface);
      border-bottom: 1px solid var(--border);
    }}
    .headline-inner {{
      max-width: var(--max-w);
      margin: 0 auto;
      padding: 28px 32px;
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 24px;
    }}
    .headline-text h2 {{
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 24px;
      font-weight: 800;
      color: var(--text);
      line-height: 1.3;
    }}
    .headline-text p {{
      color: var(--text-secondary);
      font-size: 15px;
      margin-top: 4px;
    }}

    /* ── Nav ───────────────────────────────────────── */
    .nav {{
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      position: sticky;
      top: 0;
      z-index: 100;
      backdrop-filter: blur(12px);
      background: rgba(255,255,255,0.92);
    }}
    .nav-inner {{
      max-width: var(--max-w);
      margin: 0 auto;
      padding: 0 32px;
      display: flex;
      gap: 4px;
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
      scrollbar-width: none;
    }}
    .nav-inner::-webkit-scrollbar {{ display: none; }}
    .nav a {{
      padding: 12px 16px;
      font-size: 12px;
      font-weight: 600;
      color: var(--text-muted);
      text-decoration: none;
      white-space: nowrap;
      border-bottom: 2px solid transparent;
      transition: color 0.2s, border-color 0.2s;
    }}
    .nav a:hover {{ color: var(--accent); border-bottom-color: var(--accent); }}

    /* ── Container ─────────────────────────────────── */
    .container {{ max-width: var(--max-w); margin: 0 auto; padding: 0 32px; }}

    /* ── Section ───────────────────────────────────── */
    .section {{ margin: 40px 0; scroll-margin-top: 60px; }}
    .section-header {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 20px;
    }}
    .section-title {{
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 3px;
      color: var(--section-color, #334155);
    }}
    .section-line {{
      flex: 1;
      height: 1px;
      background: var(--border);
    }}
    .section-count {{
      font-size: 11px;
      color: var(--text-muted);
      font-weight: 500;
    }}

    /* ── Grid ──────────────────────────────────────── */
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
      gap: 20px;
    }}

    /* ── Cards ─────────────────────────────────────── */
    .card {{
      background: var(--surface);
      border-radius: var(--radius);
      overflow: hidden;
      box-shadow: var(--shadow-sm);
      border: 1px solid var(--border-light);
      transition: box-shadow 0.25s ease, transform 0.25s ease;
      display: flex;
      flex-direction: column;
    }}
    .card:hover {{
      box-shadow: var(--shadow-lg);
      transform: translateY(-3px);
    }}
    .card-featured {{
      background: var(--surface);
      border-radius: var(--radius);
      overflow: hidden;
      box-shadow: var(--shadow-md);
      border: 1px solid var(--border-light);
      transition: box-shadow 0.25s ease, transform 0.25s ease;
      grid-column: 1 / -1;
      display: grid;
      grid-template-columns: 1fr 1fr;
    }}
    .card-featured:hover {{
      box-shadow: var(--shadow-lg);
      transform: translateY(-2px);
    }}
    .card-img-link {{ display: block; }}
    .card-img {{
      width: 100%;
      height: 200px;
      object-fit: cover;
      display: block;
    }}
    .card-featured .card-img {{ height: 100%; min-height: 300px; }}
    .card-placeholder {{
      height: 140px;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .card-featured .card-placeholder {{ height: 100%; min-height: 300px; }}
    .card-body {{
      padding: 24px;
      display: flex;
      flex-direction: column;
      flex: 1;
    }}
    .card-featured .card-body {{ padding: 32px; justify-content: center; }}
    .card-meta {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 12px;
      flex-wrap: wrap;
    }}
    .cat-pill {{
      font-size: 10px;
      font-weight: 700;
      padding: 4px 12px;
      border-radius: 20px;
      letter-spacing: 0.8px;
      text-transform: uppercase;
      background: color-mix(in srgb, var(--c) 8%, transparent);
      color: var(--c);
    }}
    .imp-badge {{
      font-size: 9px;
      font-weight: 700;
      padding: 3px 10px;
      border-radius: 10px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .card-body h3 {{
      font-size: 17px;
      font-weight: 700;
      line-height: 1.35;
      margin-bottom: 8px;
    }}
    .card-featured .card-body h3 {{
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 24px;
      line-height: 1.3;
    }}
    .card-body h3 a {{
      color: var(--text);
      text-decoration: none;
      transition: color 0.15s;
    }}
    .card-body h3 a:hover {{ color: var(--accent); }}
    .source-line {{
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      color: var(--text-muted);
      margin-bottom: 12px;
    }}
    .source-line img {{ border-radius: 3px; }}
    .summary {{
      font-size: 14px;
      color: var(--text-secondary);
      line-height: 1.7;
      flex: 1;
    }}
    .card-tags {{
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
      margin-top: 14px;
    }}
    .tag {{
      font-size: 10px;
      color: var(--accent);
      background: var(--accent-light);
      padding: 3px 10px;
      border-radius: 8px;
      font-weight: 500;
    }}
    .read-link {{
      display: inline-block;
      margin-top: 16px;
      font-size: 12px;
      font-weight: 600;
      color: var(--accent);
      text-decoration: none;
      transition: gap 0.2s;
    }}
    .read-link:hover {{ text-decoration: underline; }}

    /* ── Trends ────────────────────────────────────── */
    .trends-card {{
      background: var(--surface);
      border-radius: var(--radius);
      padding: 28px;
      box-shadow: var(--shadow-sm);
      border: 1px solid var(--border-light);
    }}
    .trend-item {{
      padding: 16px 0;
      border-bottom: 1px solid var(--border-light);
    }}
    .trend-item:last-child {{ border: none; padding-bottom: 0; }}
    .trend-item:first-child {{ padding-top: 0; }}
    .trend-item strong {{
      display: block;
      font-size: 15px;
      font-weight: 700;
      color: var(--text);
      margin-bottom: 4px;
    }}
    .trend-item p {{
      font-size: 13px;
      color: var(--text-secondary);
      line-height: 1.6;
    }}

    /* ── Extended / Bonus ──────────────────────────── */
    .bonus-divider {{
      display: flex;
      align-items: center;
      gap: 16px;
      margin: 56px 0 32px;
    }}
    .bonus-divider::before, .bonus-divider::after {{
      content: '';
      flex: 1;
      height: 1px;
      background: var(--border);
    }}
    .bonus-divider span {{
      font-size: 11px;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 3px;
      white-space: nowrap;
    }}

    .ext-section {{
      margin-bottom: 32px;
    }}
    .ext-cat-title {{
      font-size: 13px;
      font-weight: 700;
      color: var(--c);
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 2px solid color-mix(in srgb, var(--c) 20%, transparent);
      display: inline-block;
    }}
    .ext-row {{
      display: flex;
      gap: 14px;
      padding: 14px 0;
      border-bottom: 1px solid var(--border-light);
    }}
    .ext-row:last-child {{ border: none; }}
    .ext-dot {{
      width: 6px;
      height: 6px;
      border-radius: 50%;
      margin-top: 7px;
      flex-shrink: 0;
    }}
    .ext-body {{ flex: 1; }}
    .ext-title {{
      font-size: 14px;
      font-weight: 600;
      color: var(--text);
      text-decoration: none;
      line-height: 1.35;
    }}
    .ext-title:hover {{ color: var(--accent); }}
    .ext-source {{
      font-size: 11px;
      color: var(--text-muted);
      margin-left: 8px;
    }}
    .ext-summary {{
      font-size: 13px;
      color: var(--text-secondary);
      margin-top: 4px;
      line-height: 1.55;
    }}

    /* ── Footer ────────────────────────────────────── */
    .footer {{
      background: #0F172A;
      padding: 40px 32px;
      text-align: center;
      margin-top: 64px;
    }}
    .footer p {{ color: #64748B; font-size: 12px; line-height: 1.8; }}
    .footer a {{ color: #818CF8; text-decoration: none; }}
    .footer a:hover {{ text-decoration: underline; }}
    .footer-brand {{
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 18px;
      color: #E2E8F0;
      font-weight: 400;
      letter-spacing: 1px;
      margin-bottom: 8px;
    }}

    /* ── Responsive ────────────────────────────────── */
    @media (max-width: 768px) {{
      .hero-inner {{ padding: 40px 20px 36px; }}
      .hero h1 {{ font-size: 30px; }}
      .headline-inner {{ flex-direction: column; padding: 20px; }}
      .headline-text h2 {{ font-size: 20px; }}
      .container {{ padding: 0 16px; }}
      .grid {{ grid-template-columns: 1fr; }}
      .card-featured {{ grid-template-columns: 1fr; }}
      .card-featured .card-img {{ min-height: 200px; height: 200px; }}
      .card-featured .card-placeholder {{ min-height: 120px; height: 120px; }}
      .card-featured .card-body {{ padding: 24px; }}
      .card-featured .card-body h3 {{ font-size: 20px; }}
      .nav-inner {{ padding: 0 16px; }}
      .section {{ margin: 28px 0; }}
    }}

    @media (max-width: 480px) {{
      .hero h1 {{ font-size: 24px; letter-spacing: 1px; }}
      .card-body h3 {{ font-size: 15px; }}
    }}
  </style>
</head>
<body>

<div class="hero">
  <div class="hero-inner">
    <div class="hero-label">Intelligence</div>
    <h1>AI Briefing</h1>
    <div class="hero-date">{date_fr}</div>
    <div class="hero-pills">
      <span class="hero-pill">{n_articles} articles</span>
      <span class="hero-pill">{n_sources} sources</span>
      {"<span class='hero-pill'>+" + str(n_extended) + " bonus</span>" if n_extended else ""}
    </div>
  </div>
</div>

<div class="headline-bar">
  <div class="headline-inner">
    <div class="headline-text">
      <h2>{headline}</h2>
      {"<p>" + one_liner + "</p>" if one_liner else ""}
    </div>
    <a href="{SITE_URL}/digest/" style="font-size:13px;color:var(--accent);text-decoration:none;font-weight:600;white-space:nowrap;">&larr; Archives</a>
  </div>
</div>

<nav class="nav">
  <div class="nav-inner">
    {nav_items}
  </div>
</nav>

<div class="container">

  {"<section class='section' id='top-story'><div class='section-header'><span class='section-title' style='--section-color:#EA580C;'>Top Story</span><div class='section-line'></div></div><div class='grid'>" + top_html + "</div></section>" if top_html else ""}

  {"<section class='section' id='must-read'><div class='section-header'><span class='section-title' style='--section-color:#DC2626;'>A ne pas rater</span><div class='section-line'></div><span class='section-count'>" + str(len(must_reads)) + " articles</span></div><div class='grid'>" + must_html + "</div></section>" if must_reads else ""}

  {"<section class='section' id='important'><div class='section-header'><span class='section-title' style='--section-color:#D97706;'>Important</span><div class='section-line'></div><span class='section-count'>" + str(len(important)) + " articles</span></div><div class='grid'>" + important_html + "</div></section>" if important else ""}

  {"<section class='section' id='worth-noting'><div class='section-header'><span class='section-title' style='--section-color:#94A3B8;'>En bref</span><div class='section-line'></div><span class='section-count'>" + str(len(worth_noting)) + " articles</span></div><div class='grid'>" + noting_html + "</div></section>" if worth_noting else ""}

  {"<section class='section' id='trends'><div class='section-header'><span class='section-title' style='--section-color:#059669;'>Tendances</span><div class='section-line'></div></div><div class='trends-card'>" + trends_html + "</div></section>" if trends else ""}

  {"<div class='bonus-divider' id='bonus'><span>Bonus — " + str(n_extended) + " articles supplementaires</span></div>" + ext_sections if extended else ""}

</div>

<div class="footer">
  <div class="footer-brand">AI Briefing</div>
  <p>
    Généré par <a href="https://github.com/GaspardCoche/agent-system">Agent System</a> &mdash; Gemini + Claude<br>
    Chaque matin à 7h30 &bull; {n_sources} sources scannées
  </p>
</div>

</body>
</html>'''


def render_index(digests: list) -> str:
    rows = ""
    for d in sorted(digests, key=lambda x: x["date"], reverse=True):
        date = escape(d["date"])
        date_fr = _format_date_fr(d["date"])
        headline = escape(d.get("headline", "Digest"))
        n = d.get("n_articles", 0)
        rows += f'''
        <a href="{date}.html" class="digest-row">
          <div class="row-date">
            <span class="row-day">{date}</span>
            <span class="row-day-fr">{date_fr}</span>
          </div>
          <div class="row-content">
            <span class="row-headline">{headline}</span>
            <span class="row-count">{n} articles</span>
          </div>
          <span class="row-arrow">&rarr;</span>
        </a>'''

    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Briefing — Archives</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #F7F8FA;
      --surface: #FFFFFF;
      --border: #E8ECF1;
      --text: #0F172A;
      --text-secondary: #475569;
      --text-muted: #94A3B8;
      --accent: #4F46E5;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: var(--bg); color: var(--text); font-family: 'Inter', -apple-system, system-ui, sans-serif; -webkit-font-smoothing: antialiased; }}

    .hero {{
      background: #0F172A;
      color: #F8FAFC;
      position: relative;
      overflow: hidden;
    }}
    .hero::before {{
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
      background: linear-gradient(90deg, #6366F1, #8B5CF6, #EC4899, #8B5CF6, #6366F1);
      background-size: 200% 100%;
      animation: shimmer 6s ease-in-out infinite;
    }}
    @keyframes shimmer {{ 0%,100% {{ background-position: 0% 50%; }} 50% {{ background-position: 100% 50%; }} }}

    .hero-inner {{
      max-width: 800px;
      margin: 0 auto;
      padding: 56px 32px 48px;
      text-align: center;
    }}
    .hero-label {{
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 6px;
      text-transform: uppercase;
      color: #818CF8;
    }}
    .hero h1 {{
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 38px;
      font-weight: 400;
      letter-spacing: 2px;
      margin: 16px 0 8px;
    }}
    .hero p {{
      color: #64748B;
      font-size: 14px;
    }}

    .container {{
      max-width: 800px;
      margin: 0 auto;
      padding: 32px 24px 80px;
    }}

    .digest-row {{
      display: flex;
      align-items: center;
      padding: 20px 24px;
      background: var(--surface);
      border-radius: 12px;
      margin-bottom: 8px;
      text-decoration: none;
      color: var(--text);
      border: 1px solid var(--border);
      transition: box-shadow 0.2s, transform 0.15s, border-color 0.2s;
      gap: 20px;
    }}
    .digest-row:hover {{
      box-shadow: 0 8px 24px rgba(0,0,0,0.06);
      transform: translateY(-2px);
      border-color: rgba(79,70,229,0.2);
    }}
    .row-date {{
      min-width: 120px;
      flex-shrink: 0;
    }}
    .row-day {{
      display: block;
      font-size: 14px;
      color: var(--accent);
      font-weight: 700;
      font-variant-numeric: tabular-nums;
    }}
    .row-day-fr {{
      display: block;
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 2px;
    }}
    .row-content {{
      flex: 1;
      min-width: 0;
    }}
    .row-headline {{
      display: block;
      font-size: 15px;
      font-weight: 600;
      line-height: 1.35;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .row-count {{
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 2px;
      display: block;
    }}
    .row-arrow {{
      color: var(--text-muted);
      font-size: 16px;
      transition: transform 0.2s, color 0.2s;
    }}
    .digest-row:hover .row-arrow {{
      transform: translateX(4px);
      color: var(--accent);
    }}

    .footer {{
      text-align: center;
      padding: 32px;
      color: var(--text-muted);
      font-size: 12px;
    }}
    .footer a {{ color: #818CF8; text-decoration: none; }}

    @media (max-width: 640px) {{
      .hero h1 {{ font-size: 28px; }}
      .digest-row {{ flex-wrap: wrap; gap: 8px; padding: 16px; }}
      .row-date {{ min-width: auto; }}
    }}
  </style>
</head>
<body>

<div class="hero">
  <div class="hero-inner">
    <div class="hero-label">Archives</div>
    <h1>AI Briefing</h1>
    <p>Tous les digests quotidiens</p>
  </div>
</div>

<div class="container">
  {rows}
</div>

<div class="footer">
  <p><a href="{SITE_URL}/">&larr; Dashboard</a> &bull; <a href="https://github.com/GaspardCoche/agent-system">Agent System</a></p>
</div>

</body>
</html>'''


def main():
    digest_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ai_digest.json"

    if not Path(digest_path).exists():
        print("No digest found — skipping archive", file=sys.stderr)
        sys.exit(0)

    digest = json.loads(Path(digest_path).read_text(encoding="utf-8"))
    today = datetime.now().strftime("%Y-%m-%d")

    out_dir = Path("docs/digest")
    out_dir.mkdir(parents=True, exist_ok=True)

    page_html = render_page(digest, today)
    page_path = out_dir / f"{today}.html"
    page_path.write_text(page_html, encoding="utf-8")
    print(f"Archive page: {page_path}", file=sys.stderr)

    json_path = out_dir / f"{today}.json"
    json_path.write_text(json.dumps(digest, indent=2, ensure_ascii=False), encoding="utf-8")

    digests_meta = []
    for f in sorted(out_dir.glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            n = len(d.get("articles", [])) + (1 if d.get("top_story") else 0) + len(d.get("extended", []))
            digests_meta.append({
                "date": f.stem,
                "headline": d.get("headline", ""),
                "n_articles": n,
            })
        except Exception:
            pass

    index_html = render_index(digests_meta)
    (out_dir / "index.html").write_text(index_html, encoding="utf-8")
    print(f"Index updated: {len(digests_meta)} digests", file=sys.stderr)

    archive_url = f"{SITE_URL}/digest/{today}.html"
    Path("/tmp/digest_archive_url.txt").write_text(archive_url)
    print(f"Archive URL: {archive_url}", file=sys.stderr)


if __name__ == "__main__":
    main()

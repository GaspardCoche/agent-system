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
    "Code & Dev": "#F97316", "Google & Cloud": "#0891B2",
    "Tech & Business": "#6D28D9",
}

CAT_ICONS = {
    "Modeles": "\U0001f9e0", "Outils & Plateformes": "⚙️",
    "Recherche": "\U0001f52c", "Business & Levees": "\U0001f4b0",
    "Open Source": "\U0001f310", "Regulation & Ethique": "⚖️",
    "Code & Dev": "\U0001f4bb", "Google & Cloud": "☁️",
    "Tech & Business": "\U0001f4c8",
}


def _favicon(url: str) -> str:
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc or url
    except Exception:
        domain = url
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=32"


def _article_card(article: dict, large: bool = False) -> str:
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

    imp_badge = ""
    if importance == "must_read":
        imp_badge = '<span class="badge badge-red">Must Read</span>'
    elif importance == "important":
        imp_badge = '<span class="badge badge-amber">Important</span>'

    img_html = ""
    if image_url and len(image_url) > 20:
        h = "240px" if large else "180px"
        img_html = f'<a href="{escape(url)}"><img src="{escape(image_url)}" alt="" class="card-img" style="height:{h};" loading="lazy" /></a>'
    else:
        h = "120px" if large else "80px"
        img_html = (f'<div class="card-placeholder" style="height:{h};background:linear-gradient(135deg,{color}22,{color}11);">'
                    f'<img src="{_favicon(url)}" width="32" height="32" style="border-radius:6px;" />'
                    f'</div>')

    tags_html = "".join(f'<span class="tag">{escape(t)}</span>' for t in tags[:3])
    size_class = "card-large" if large else "card"

    return f'''
    <article class="{size_class}">
      {img_html}
      <div class="card-body">
        <div class="card-meta">
          <span class="cat-pill" style="--cat-color:{color};">{icon} {escape(cat)}</span>
          {imp_badge}
        </div>
        <h3><a href="{escape(url)}">{title}</a></h3>
        <div class="source"><img src="{_favicon(url)}" width="14" height="14" /> {source}</div>
        <p>{summary}</p>
        <div class="card-tags">{tags_html}</div>
      </div>
    </article>'''


def _trend_item(trend) -> str:
    if isinstance(trend, dict):
        title = escape(trend.get("title", ""))
        desc = escape(trend.get("description", ""))
        return f'<div class="trend"><strong>{title}</strong><span>{desc}</span></div>'
    return f'<div class="trend"><span>{escape(str(trend))}</span></div>'


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

    top_html = _article_card(top_story, large=True) if top_story else ""
    must_html = "".join(_article_card(a) for a in must_reads)
    important_html = "".join(_article_card(a) for a in important)
    noting_html = "".join(_article_card(a) for a in worth_noting)
    trends_html = "".join(_trend_item(t) for t in trends)

    # Group extended by category
    ext_by_cat = {}
    for a in extended:
        c = a.get("category", "Autre")
        ext_by_cat.setdefault(c, []).append(a)

    ext_sections = ""
    for cat, items in ext_by_cat.items():
        color = CAT_COLORS.get(cat, "#6B7280")
        icon = CAT_ICONS.get(cat, "")
        cards = "".join(_article_card(a) for a in items)
        ext_sections += f'''
        <section class="section">
          <h2 class="section-title" style="--accent:{color};">{icon} {escape(cat)}</h2>
          <div class="grid">{cards}</div>
        </section>'''

    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{headline} — AI Briefing {date_str}</title>
  <meta name="description" content="{one_liner}">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #F8FAFC; color: #0F172A; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; -webkit-font-smoothing: antialiased; line-height: 1.6; }}

    .header {{ background: #0F172A; color: #F8FAFC; padding: 48px 24px 40px; text-align: center; }}
    .header::before {{ content: ''; display: block; height: 3px; background: linear-gradient(90deg, #6366F1, #8B5CF6, #A78BFA, #6366F1); margin: -48px -24px 32px; }}
    .header .label {{ font-size: 11px; font-weight: 700; letter-spacing: 5px; text-transform: uppercase; color: #818CF8; }}
    .header h1 {{ font-size: 36px; font-weight: 300; letter-spacing: 3px; font-family: Georgia, 'Times New Roman', serif; margin: 12px 0; }}
    .header .date {{ color: #64748B; font-size: 12px; letter-spacing: 2px; text-transform: uppercase; }}
    .header .stats {{ margin-top: 20px; display: flex; justify-content: center; gap: 8px; }}
    .header .pill {{ background: rgba(99,102,241,0.12); border-radius: 20px; padding: 5px 16px; color: #A5B4FC; font-size: 11px; font-weight: 600; }}

    .headline-bar {{ background: #fff; padding: 28px 24px; border-bottom: 1px solid #E2E8F0; max-width: 1200px; margin: 0 auto; }}
    .headline-bar h2 {{ font-size: 22px; font-weight: 800; font-family: Georgia, serif; color: #0F172A; margin-bottom: 6px; }}
    .headline-bar p {{ color: #64748B; font-size: 15px; }}

    .container {{ max-width: 1200px; margin: 0 auto; padding: 0 24px; }}

    .section {{ margin: 40px 0; }}
    .section-title {{ font-size: 13px; font-weight: 800; text-transform: uppercase; letter-spacing: 3px; color: var(--accent, #334155); margin-bottom: 16px; padding-bottom: 8px; border-bottom: 2px solid var(--accent, #E2E8F0); display: inline-block; }}

    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; }}

    .card, .card-large {{ background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.06); transition: box-shadow 0.2s, transform 0.2s; }}
    .card:hover, .card-large:hover {{ box-shadow: 0 8px 30px rgba(0,0,0,0.1); transform: translateY(-2px); }}
    .card-large {{ grid-column: 1 / -1; }}
    .card-img {{ width: 100%; object-fit: cover; display: block; }}
    .card-placeholder {{ display: flex; align-items: center; justify-content: center; }}
    .card-body {{ padding: 20px; }}
    .card-meta {{ display: flex; align-items: center; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }}
    .cat-pill {{ font-size: 10px; font-weight: 700; padding: 4px 12px; border-radius: 20px; letter-spacing: 0.8px; text-transform: uppercase; background: color-mix(in srgb, var(--cat-color) 10%, transparent); color: var(--cat-color); }}
    .badge {{ font-size: 9px; font-weight: 700; padding: 3px 8px; border-radius: 10px; text-transform: uppercase; letter-spacing: 0.5px; }}
    .badge-red {{ background: #FEF2F2; color: #DC2626; }}
    .badge-amber {{ background: #FFFBEB; color: #D97706; }}
    .card-body h3 {{ font-size: 18px; font-weight: 700; line-height: 1.3; margin-bottom: 8px; }}
    .card-large .card-body h3 {{ font-size: 24px; font-family: Georgia, serif; }}
    .card-body h3 a {{ color: #0F172A; text-decoration: none; }}
    .card-body h3 a:hover {{ color: #4F46E5; }}
    .source {{ font-size: 12px; color: #94A3B8; display: flex; align-items: center; gap: 6px; margin-bottom: 10px; }}
    .source img {{ border-radius: 3px; }}
    .card-body p {{ font-size: 14px; color: #475569; line-height: 1.65; }}
    .card-tags {{ margin-top: 12px; display: flex; gap: 4px; flex-wrap: wrap; }}
    .tag {{ font-size: 10px; color: #6366F1; background: #EEF2FF; padding: 2px 8px; border-radius: 8px; font-weight: 500; }}

    .trends-section {{ background: #fff; border-radius: 12px; padding: 24px; margin: 40px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }}
    .trends-section h2 {{ font-size: 13px; font-weight: 800; text-transform: uppercase; letter-spacing: 3px; color: #059669; margin-bottom: 16px; }}
    .trend {{ padding: 14px 0; border-bottom: 1px solid #F1F5F9; }}
    .trend:last-child {{ border: none; }}
    .trend strong {{ display: block; font-size: 15px; color: #0F172A; margin-bottom: 4px; }}
    .trend span {{ font-size: 13px; color: #64748B; }}

    .extended-label {{ margin: 48px 0 8px; text-align: center; }}
    .extended-label span {{ background: #F8FAFC; padding: 0 20px; font-size: 12px; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 3px; position: relative; }}
    .extended-label::before {{ content: ''; display: block; height: 1px; background: #E2E8F0; position: relative; top: 10px; }}

    .footer {{ background: #0F172A; padding: 32px 24px; text-align: center; margin-top: 48px; }}
    .footer p {{ color: #475569; font-size: 12px; }}
    .footer a {{ color: #818CF8; text-decoration: none; }}

    .back-link {{ display: inline-block; margin: 24px 0; font-size: 13px; color: #6366F1; text-decoration: none; font-weight: 600; }}
    .back-link:hover {{ text-decoration: underline; }}

    @media (max-width: 640px) {{
      .grid {{ grid-template-columns: 1fr; }}
      .header h1 {{ font-size: 28px; }}
      .headline-bar h2 {{ font-size: 18px; }}
    }}
  </style>
</head>
<body>

<div class="header">
  <div class="label">Intelligence</div>
  <h1>AI Briefing</h1>
  <div class="date">{date_str}</div>
  <div class="stats">
    <span class="pill">{n_articles} articles</span>
    <span class="pill">{n_sources} sources</span>
    {"<span class='pill'>+" + str(n_extended) + " en bonus</span>" if n_extended else ""}
  </div>
</div>

<div class="headline-bar">
  <h2>{headline}</h2>
  {"<p>" + one_liner + "</p>" if one_liner else ""}
  <a href="{SITE_URL}/digest/" class="back-link">&larr; Tous les digests</a>
</div>

<div class="container">

  {"<section class='section'>" + top_html + "</section>" if top_html else ""}

  {"<section class='section'><h2 class='section-title' style='--accent:#DC2626;'>A ne pas rater</h2><div class='grid'>" + must_html + "</div></section>" if must_reads else ""}

  {"<section class='section'><h2 class='section-title' style='--accent:#D97706;'>Important</h2><div class='grid'>" + important_html + "</div></section>" if important else ""}

  {"<section class='section'><h2 class='section-title' style='--accent:#94A3B8;'>En bref</h2><div class='grid'>" + noting_html + "</div></section>" if worth_noting else ""}

  {"<div class='trends-section'><h2>Tendances</h2>" + trends_html + "</div>" if trends else ""}

  {"<div class='extended-label'><span>Bonus — Plus d'articles</span></div>" + ext_sections if extended else ""}

</div>

<div class="footer">
  <p>Genere par <a href="https://github.com/GaspardCoche/agent-system">Agent System</a> &mdash; Gemini + Claude</p>
  <p style="margin-top:4px;color:#334155;font-size:11px;">Chaque matin a 7h30 &bull; {n_sources} sources scannees</p>
</div>

</body>
</html>'''


def render_index(digests: list) -> str:
    rows = ""
    for d in sorted(digests, key=lambda x: x["date"], reverse=True):
        date = escape(d["date"])
        headline = escape(d.get("headline", "Digest"))
        n = d.get("n_articles", 0)
        rows += f'''
        <a href="{date}.html" class="digest-row">
          <span class="digest-date">{date}</span>
          <span class="digest-headline">{headline}</span>
          <span class="digest-count">{n} articles</span>
        </a>'''

    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Briefing — Archives</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #F8FAFC; color: #0F172A; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; }}
    .header {{ background: #0F172A; color: #F8FAFC; padding: 48px 24px; text-align: center; }}
    .header::before {{ content: ''; display: block; height: 3px; background: linear-gradient(90deg, #6366F1, #8B5CF6, #A78BFA, #6366F1); margin: -48px -24px 32px; }}
    .header .label {{ font-size: 11px; font-weight: 700; letter-spacing: 5px; text-transform: uppercase; color: #818CF8; }}
    .header h1 {{ font-size: 32px; font-weight: 300; letter-spacing: 3px; font-family: Georgia, serif; margin: 12px 0 8px; }}
    .header p {{ color: #64748B; font-size: 13px; }}
    .container {{ max-width: 720px; margin: 0 auto; padding: 32px 24px; }}
    .digest-row {{ display: flex; align-items: center; padding: 18px 20px; background: #fff; border-radius: 10px; margin-bottom: 8px; text-decoration: none; color: #0F172A; box-shadow: 0 1px 3px rgba(0,0,0,0.04); transition: box-shadow 0.2s, transform 0.15s; gap: 16px; }}
    .digest-row:hover {{ box-shadow: 0 4px 16px rgba(0,0,0,0.08); transform: translateY(-1px); }}
    .digest-date {{ font-size: 13px; color: #6366F1; font-weight: 700; font-variant-numeric: tabular-nums; white-space: nowrap; min-width: 90px; }}
    .digest-headline {{ flex: 1; font-size: 15px; font-weight: 600; }}
    .digest-count {{ font-size: 11px; color: #94A3B8; white-space: nowrap; }}
    .footer {{ text-align: center; padding: 32px; color: #94A3B8; font-size: 12px; }}
    .footer a {{ color: #818CF8; text-decoration: none; }}
  </style>
</head>
<body>

<div class="header">
  <div class="label">Archives</div>
  <h1>AI Briefing</h1>
  <p>Tous les digests quotidiens</p>
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

    # Also save the JSON for future use
    json_path = out_dir / f"{today}.json"
    json_path.write_text(json.dumps(digest, indent=2, ensure_ascii=False), encoding="utf-8")

    # Rebuild index from all existing JSON files
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

    # Output the archive URL for use in email CTA
    archive_url = f"{SITE_URL}/digest/{today}.html"
    Path("/tmp/digest_archive_url.txt").write_text(archive_url)
    print(f"Archive URL: {archive_url}", file=sys.stderr)


if __name__ == "__main__":
    main()

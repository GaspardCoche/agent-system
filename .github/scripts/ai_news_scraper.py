#!/usr/bin/env python3
"""
Scrapes AI news sources via RSS feeds (preferred) + HTTP fallback.
Output: /tmp/ai_news_raw.txt

RSS feeds provide guaranteed-valid article URLs.
For sources without RSS, falls back to HTML scraping.
"""
import concurrent.futures
import json
import os
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path

SOURCES = [
    # Tier 1 — AI labs + developer/MCP coverage (scraped first)
    {"name": "Anthropic News",      "url": "https://www.anthropic.com/news",          "domain": "anthropic.com"},
    {"name": "Simon Willison",       "url": "https://simonwillison.net/",              "domain": "simonwillison.net",
     "rss": "https://simonwillison.net/atom/everything/",                              "format": "atom"},
    {"name": "OpenAI Blog",          "url": "https://openai.com/blog",                 "domain": "openai.com",
     "rss": "https://openai.com/blog/rss.xml"},
    {"name": "Google DeepMind",      "url": "https://deepmind.google/discover/blog/",  "domain": "deepmind.google",
     "rss": "https://deepmind.google/blog/rss.xml"},
    {"name": "HuggingFace Blog",     "url": "https://huggingface.co/blog",             "domain": "huggingface.co",
     "rss": "https://huggingface.co/blog/feed.xml"},
    {"name": "GitHub Blog",          "url": "https://github.blog/",                    "domain": "github.blog",
     "rss": "https://github.blog/feed/"},
    {"name": "Latent Space",        "url": "https://www.latent.space/",               "domain": "latent.space",
     "rss": "https://www.latent.space/feed"},
    # Tier 2 — Major tech press + AI-focused outlets
    {"name": "The Verge AI",         "url": "https://www.theverge.com/ai-artificial-intelligence",
     "domain": "theverge.com",
     "rss": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"},
    {"name": "TechCrunch AI",        "url": "https://techcrunch.com/category/artificial-intelligence/",
     "domain": "techcrunch.com",
     "rss": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"name": "Ars Technica AI",      "url": "https://arstechnica.com/ai/",             "domain": "arstechnica.com",
     "rss": "https://feeds.arstechnica.com/arstechnica/technology-lab"},
    {"name": "The Decoder",          "url": "https://the-decoder.com/",                "domain": "the-decoder.com",
     "rss": "https://the-decoder.com/feed/"},
    {"name": "Mistral News",         "url": "https://mistral.ai/news/",                "domain": "mistral.ai"},
    {"name": "AI Snake Oil",        "url": "https://www.aisnakeoil.com/",             "domain": "aisnakeoil.com",
     "rss": "https://www.aisnakeoil.com/feed"},
    {"name": "Last Week in AI",     "url": "https://lastweekin.ai/",                  "domain": "lastweekin.ai",
     "rss": "https://lastweekin.ai/feed"},
    {"name": "Interconnects",       "url": "https://www.interconnects.ai/",           "domain": "interconnects.ai",
     "rss": "https://www.interconnects.ai/feed"},
    # Tier 3 — Broader coverage
    {"name": "VentureBeat AI",       "url": "https://venturebeat.com/category/ai/",    "domain": "venturebeat.com",
     "rss": "https://venturebeat.com/category/ai/feed/"},
    {"name": "AI News",              "url": "https://artificialintelligence-news.com/", "domain": "artificialintelligence-news.com",
     "rss": "https://www.artificialintelligence-news.com/feed/"},
    {"name": "MIT Tech Review AI",   "url": "https://www.technologyreview.com/topic/artificial-intelligence/",
     "domain": "technologyreview.com",
     "rss": "https://www.technologyreview.com/topic/artificial-intelligence/feed"},
    {"name": "Google AI Blog",       "url": "https://blog.google/technology/ai/",      "domain": "blog.google",
     "rss": "https://blog.google/technology/ai/rss/"},
    {"name": "Wired AI",             "url": "https://www.wired.com/tag/artificial-intelligence/",
     "domain": "wired.com",
     "rss": "https://www.wired.com/feed/tag/ai/latest/rss"},
    {"name": "MarkTechPost",         "url": "https://www.marktechpost.com/",           "domain": "marktechpost.com",
     "rss": "https://www.marktechpost.com/feed/"},
    {"name": "The Batch",            "url": "https://www.deeplearning.ai/the-batch/",   "domain": "deeplearning.ai"},
    {"name": "Ahead of AI",         "url": "https://magazine.sebastianraschka.com/",  "domain": "magazine.sebastianraschka.com",
     "rss": "https://magazine.sebastianraschka.com/feed"},
    # Tier 4 — Coding, Google, Tech
    # Dev/Coding
    {"name": "Hacker News",          "url": "https://news.ycombinator.com/",            "domain": "news.ycombinator.com",
     "rss": "https://hnrss.org/best?count=10"},
    {"name": "Dev.to",               "url": "https://dev.to/",                          "domain": "dev.to",
     "rss": "https://dev.to/feed"},
    {"name": "Changelog",            "url": "https://changelog.com/",                   "domain": "changelog.com",
     "rss": "https://changelog.com/feed"},
    {"name": "CSS-Tricks",           "url": "https://css-tricks.com/",                  "domain": "css-tricks.com",
     "rss": "https://css-tricks.com/feed/"},
    # Google ecosystem
    {"name": "Google Blog",          "url": "https://blog.google/",                     "domain": "blog.google",
     "rss": "https://blog.google/rss/"},
    {"name": "Chrome Blog",          "url": "https://blog.chromium.org/",               "domain": "blog.chromium.org",
     "rss": "https://blog.chromium.org/feeds/posts/default?alt=rss"},
    {"name": "Android Developers",   "url": "https://android-developers.googleblog.com/", "domain": "android-developers.googleblog.com",
     "rss": "https://android-developers.googleblog.com/feeds/posts/default?alt=rss"},
    # Broader Tech
    {"name": "The Verge",            "url": "https://www.theverge.com/tech",            "domain": "theverge.com",
     "rss": "https://www.theverge.com/rss/index.xml"},
    {"name": "Platformer",           "url": "https://www.platformer.news/",             "domain": "platformer.news",
     "rss": "https://www.platformer.news/feed"},
    {"name": "Stratechery",          "url": "https://stratechery.com/",                 "domain": "stratechery.com",
     "rss": "https://stratechery.com/feed/"},
    {"name": "Benedict Evans",       "url": "https://www.ben-evans.com/",               "domain": "ben-evans.com",
     "rss": "https://www.ben-evans.com/benedictevans?format=rss"},
]

MAX_CHARS_PER_SOURCE = 3000
MAX_TOTAL_CHARS = 65000
MAX_AGE_HOURS = 36
SEEN_URLS_PATH = Path("docs/vault/ai-news/seen_urls.json")


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    for fmt in [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
    ]:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    try:
        return parsedate_to_datetime(date_str)
    except Exception:
        return None


def _is_fresh(pub_date: datetime | None, max_hours: int = MAX_AGE_HOURS) -> bool:
    if pub_date is None:
        return True
    now = datetime.now(timezone.utc)
    return (now - pub_date) < timedelta(hours=max_hours)


def load_seen_urls() -> dict:
    if SEEN_URLS_PATH.exists():
        try:
            data = json.loads(SEEN_URLS_PATH.read_text(encoding="utf-8"))
            cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            return {url: ts for url, ts in data.items() if ts > cutoff}
        except Exception:
            return {}
    return {}


def save_seen_urls(seen: dict) -> None:
    SEEN_URLS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SEEN_URLS_PATH.write_text(
        json.dumps(seen, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _extract_og_image(html: str) -> str:
    for pattern in [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']',
    ]:
        m = re.search(pattern, html, re.IGNORECASE)
        if m and not m.group(1).endswith(('.ico', 'favicon')):
            return m.group(1)
    for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE):
        src = m.group(1)
        if any(skip in src.lower() for skip in ['favicon', 'icon', 'logo', 'pixel', 'tracking', '1x1', 'avatar', 'emoji']):
            continue
        if any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
            if 'wp-content/uploads' in src or 'storage.googleapis' in src or 'cdn' in src or 'images' in src:
                return src
    return ""


def fetch_article_meta(url: str) -> dict:
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            head = resp.read(16384).decode("utf-8", errors="replace")
        image = _extract_og_image(head)
        title_m = re.search(r'<title[^>]*>([^<]+)</title>', head, re.IGNORECASE)
        title = title_m.group(1).strip() if title_m else ""
        return {"image": image, "valid": True, "page_title": title}
    except Exception:
        return {"image": "", "valid": False, "page_title": ""}


ATOM_NS = "http://www.w3.org/2005/Atom"


def parse_rss(rss_url: str, max_items: int = 5, feed_format: str = "rss") -> tuple[list[dict], int, int]:
    """Returns (items, total_entries_seen, stale_count)."""
    try:
        req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            xml_data = resp.read().decode("utf-8", errors="replace")
        root = ET.fromstring(xml_data)

        is_atom = feed_format == "atom" or root.tag == f"{{{ATOM_NS}}}feed"

        items = []
        total_entries = 0
        stale_count = 0
        if is_atom:
            for entry in root.findall(f"{{{ATOM_NS}}}entry"):
                title_el = entry.find(f"{{{ATOM_NS}}}title")
                link_el = entry.find(f"{{{ATOM_NS}}}link[@rel='alternate']")
                if link_el is None:
                    link_el = entry.find(f"{{{ATOM_NS}}}link")
                summary_el = entry.find(f"{{{ATOM_NS}}}summary")
                if summary_el is None:
                    summary_el = entry.find(f"{{{ATOM_NS}}}content")
                updated_el = entry.find(f"{{{ATOM_NS}}}updated")
                if updated_el is None:
                    updated_el = entry.find(f"{{{ATOM_NS}}}published")
                href = link_el.get("href", "") if link_el is not None else ""
                if title_el is not None and href:
                    total_entries += 1
                    pub_date = _parse_date(updated_el.text if updated_el is not None else "")
                    if not _is_fresh(pub_date):
                        stale_count += 1
                        continue
                    desc = ""
                    if summary_el is not None and summary_el.text:
                        desc = re.sub(r'<[^>]+>', '', summary_el.text).strip()[:300]
                    items.append({
                        "title": (title_el.text or "").strip(),
                        "url": href.strip(),
                        "description": desc,
                        "pub_date": pub_date.isoformat() if pub_date else "",
                    })
                if len(items) >= max_items:
                    break
        else:
            for item in root.iter("item"):
                title_el = item.find("title")
                link_el = item.find("link")
                desc_el = item.find("description")
                pub_el = item.find("pubDate")
                if title_el is not None and link_el is not None and link_el.text:
                    total_entries += 1
                    pub_date = _parse_date(pub_el.text if pub_el is not None else "")
                    if not _is_fresh(pub_date):
                        stale_count += 1
                        continue
                    desc = ""
                    if desc_el is not None and desc_el.text:
                        desc = re.sub(r'<[^>]+>', '', desc_el.text).strip()[:300]
                    items.append({
                        "title": (title_el.text or "").strip(),
                        "url": link_el.text.strip(),
                        "description": desc,
                        "pub_date": pub_date.isoformat() if pub_date else "",
                    })
                if len(items) >= max_items:
                    break
        return items, total_entries, stale_count
    except Exception as e:
        print(f"    RSS parse failed: {e}", file=sys.stderr)
        return [], 0, 0


def scrape_page(url: str, api_key: str | None) -> str:
    if api_key:
        content = _scrape_firecrawl(url, api_key)
        if not content.startswith("[Firecrawl error"):
            return content
        print(f"    Firecrawl failed, falling back to basic HTTP", file=sys.stderr)
    return _scrape_basic(url)


def _scrape_firecrawl(url: str, api_key: str) -> str:
    payload = json.dumps({
        "url": url,
        "formats": ["markdown"],
        "onlyMainContent": True,
        "excludeTags": ["nav", "footer", "aside", "script", "style"],
        "waitFor": 1000
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.firecrawl.dev/v1/scrape",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            return data.get("data", {}).get("markdown", "")[:MAX_CHARS_PER_SOURCE]
    except Exception as e:
        return f"[Firecrawl error for {url}: {e}]"


def _scrape_basic(url: str) -> str:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:MAX_CHARS_PER_SOURCE]
    except Exception as e:
        return f"[Fetch error for {url}: {e}]"


def main():
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    out = Path("/tmp/ai_news_raw.txt")
    today = datetime.now().strftime("%Y-%m-%d")

    seen = load_seen_urls()
    print(f"Loaded {len(seen)} previously seen URLs", file=sys.stderr)

    print(f"Scraping {len(SOURCES)} AI sources ({today})...", file=sys.stderr)
    sections = [f"# AI News — {today}\n\nScraping context for daily digest.\nToday's date: {today}. Only include articles from the last 36 hours.\n"]
    total = 0
    all_rss_articles = []
    skipped_seen = 0
    total_rss_found = 0
    total_filtered_stale = 0
    sources_scraped = 0

    for src in SOURCES:
        if total >= MAX_TOTAL_CHARS:
            print(f"Token limit reached, skipping remaining sources", file=sys.stderr)
            break

        print(f"  [{src['name']}]...", file=sys.stderr)
        favicon = f"https://www.google.com/s2/favicons?domain={src['domain']}&sz=128"
        sources_scraped += 1

        rss_items = []
        if src.get("rss"):
            rss_items, feed_total, feed_stale = parse_rss(src["rss"], max_items=8, feed_format=src.get("format", "rss"))
            total_rss_found += feed_total
            total_filtered_stale += feed_stale
            if rss_items:
                print(f"    RSS: {len(rss_items)} fresh articles found", file=sys.stderr)

        rss_block = ""
        if rss_items:
            rss_block = "\nArticles from RSS feed (URLs are canonical):"
            for item in rss_items:
                if item["url"] in seen:
                    skipped_seen += 1
                    continue
                rss_block += f"\n  - {item['title']}"
                rss_block += f"\n    URL: {item['url']}"
                if item.get("pub_date"):
                    rss_block += f"\n    Published: {item['pub_date']}"
                if item.get("description"):
                    rss_block += f"\n    Summary: {item['description']}"
                all_rss_articles.append({
                    "title": item["title"],
                    "url": item["url"],
                    "source_name": src["name"],
                    "description": item.get("description", ""),
                    "pub_date": item.get("pub_date", ""),
                })

        content = scrape_page(src["url"], api_key)
        section = f"\n\n## {src['name']}\nSource: {src['url']}\nLogo: {favicon}{rss_block}\n\n{content}"
        sections.append(section)
        total += len(section)
        time.sleep(0.3)

    print(f"\n  Validating {len(all_rss_articles)} RSS article URLs & fetching images...", file=sys.stderr)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        future_map = {pool.submit(fetch_article_meta, a["url"]): a for a in all_rss_articles}
        for future in concurrent.futures.as_completed(future_map):
            article = future_map[future]
            try:
                meta = future.result()
                article["valid"] = meta["valid"]
                if meta["image"]:
                    article["image"] = meta["image"]
                if meta["page_title"]:
                    article["page_title"] = meta["page_title"]
            except Exception:
                article["valid"] = False

    valid = [a for a in all_rss_articles if a.get("valid")]
    images = sum(1 for a in valid if a.get("image"))
    invalid = len(all_rss_articles) - len(valid)
    print(f"  {len(valid)} valid, {invalid} rejected, {images} with images", file=sys.stderr)
    print(f"  {skipped_seen} skipped (already in previous digests)", file=sys.stderr)

    if valid:
        verified = "\n\n## VERIFIED Article Links (use ONLY these URLs in the digest)\n"
        verified += "CRITICAL: Every URL below has been validated (HTTP 200). ONLY use these exact URLs.\n"
        verified += "DO NOT construct, modify, or guess any URL. Copy them character-for-character.\n"
        verified += f"Today is {today}. Only include articles published in the last 36 hours.\n\n"
        for a in valid:
            title = a.get("page_title") or a["title"]
            verified += f"- [VERIFIED] {title}\n"
            verified += f"  URL: {a['url']}\n"
            verified += f"  Source: {a['source_name']}\n"
            if a.get("pub_date"):
                verified += f"  Published: {a['pub_date']}\n"
            if a.get("image"):
                verified += f"  Image: {a['image']}\n"
            if a.get("description"):
                verified += f"  Description: {a['description']}\n"
            verified += "\n"
        sections.append(verified)
        total += len(verified)

    now_iso = datetime.now(timezone.utc).isoformat()
    for a in valid:
        seen[a["url"]] = now_iso
    save_seen_urls(seen)
    print(f"  Saved {len(seen)} URLs to seen_urls.json", file=sys.stderr)

    raw = "".join(sections)
    out.write_text(raw, encoding="utf-8")
    print(f"Scraped ~{total // 4:,} tokens -> {out}", file=sys.stderr)

    # Write quality metrics
    articles_published = len(valid) if valid else 0
    fresh_after_filter = total_rss_found - total_filtered_stale
    freshness_rate = round(fresh_after_filter / total_rss_found, 2) if total_rss_found > 0 else 0.0
    dedup_rate = round(skipped_seen / fresh_after_filter, 2) if fresh_after_filter > 0 else 0.0
    metrics = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sources_scraped": sources_scraped,
        "total_rss_articles_found": total_rss_found,
        "filtered_stale": total_filtered_stale,
        "filtered_dedup": skipped_seen,
        "articles_published": articles_published,
        "freshness_rate": freshness_rate,
        "dedup_rate": dedup_rate,
        "content_chars": total,
    }
    metrics_path = Path("/tmp/scraper_metrics.json")
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"  Metrics written to {metrics_path}", file=sys.stderr)


if __name__ == "__main__":
    main()

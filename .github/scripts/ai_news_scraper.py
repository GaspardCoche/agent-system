#!/usr/bin/env python3
"""
Scrapes AI news sources and prepares content for Gemini synthesis.
Output: /tmp/ai_news_raw.txt

Extracts og:image and article links for richer digest rendering.

Requires (optional):
  FIRECRAWL_API_KEY -> better scraping quality. Falls back to basic HTTP.
"""
import concurrent.futures
import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

SOURCES = [
    {"name": "Anthropic News",      "url": "https://www.anthropic.com/news",          "domain": "anthropic.com"},
    {"name": "OpenAI Blog",          "url": "https://openai.com/blog",                 "domain": "openai.com"},
    {"name": "Google DeepMind Blog", "url": "https://deepmind.google/discover/blog/",  "domain": "deepmind.google"},
    {"name": "HuggingFace Blog",     "url": "https://huggingface.co/blog",             "domain": "huggingface.co"},
    {"name": "Mistral News",         "url": "https://mistral.ai/news/",                "domain": "mistral.ai"},
    {"name": "TechCrunch AI",        "url": "https://techcrunch.com/category/artificial-intelligence/", "domain": "techcrunch.com"},
    {"name": "VentureBeat AI",       "url": "https://venturebeat.com/category/ai/",    "domain": "venturebeat.com"},
    {"name": "The Batch",            "url": "https://www.deeplearning.ai/the-batch/",   "domain": "deeplearning.ai"},
    {"name": "AI News",              "url": "https://artificialintelligence-news.com/", "domain": "artificialintelligence-news.com"},
    {"name": "Ars Technica AI",      "url": "https://arstechnica.com/ai/",             "domain": "arstechnica.com"},
]

MAX_CHARS_PER_SOURCE = 4000
MAX_TOTAL_CHARS = 35000


def _extract_og_image(html: str) -> str:
    for pattern in [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
    ]:
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            return m.group(1)
    return ""


def fetch_article_image(url: str) -> str:
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            head = resp.read(12288).decode("utf-8", errors="replace")
        return _extract_og_image(head)
    except Exception:
        return ""


def extract_meta(html: str, base_url: str) -> dict:
    meta = {}
    og_img = _extract_og_image(html)
    if og_img:
        meta["og_image"] = og_img

    links = []
    for m in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]{10,80})</a>', html):
        href, text = m.group(1), m.group(2).strip()
        if any(skip in href for skip in ["#", "javascript:", "mailto:", "/tag/", "/category/", "/author/"]):
            continue
        full_url = urljoin(base_url, href)
        if any(kw in href for kw in ["/blog/", "/news/", "/article", "/post/", "/discover/", "/the-batch/"]):
            links.append({"url": full_url, "title": text})
    meta["article_links"] = links[:8]
    return meta


def scrape_firecrawl(url: str, api_key: str) -> tuple[str, dict]:
    payload = json.dumps({
        "url": url,
        "formats": ["markdown", "rawHtml"],
        "onlyMainContent": True,
        "excludeTags": ["nav", "footer", "aside", "script", "style"],
        "waitFor": 1000
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.firecrawl.dev/v1/scrape",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            md = data.get("data", {}).get("markdown", "")[:MAX_CHARS_PER_SOURCE]
            html = data.get("data", {}).get("rawHtml", "")
            meta = extract_meta(html, url) if html else {}
            return md, meta
    except Exception as e:
        return f"[Firecrawl error for {url}: {e}]", {}


def scrape_basic(url: str) -> tuple[str, dict]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        meta = extract_meta(html, url)
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:MAX_CHARS_PER_SOURCE], meta
    except Exception as e:
        return f"[Fetch error for {url}: {e}]", {}


def scrape(url: str, api_key: str | None) -> tuple[str, dict]:
    if api_key:
        content, meta = scrape_firecrawl(url, api_key)
        if not content.startswith("[Firecrawl error"):
            return content, meta
        print(f"    Firecrawl failed, falling back to basic HTTP", file=sys.stderr)
    return scrape_basic(url)


def main():
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    out = Path("/tmp/ai_news_raw.txt")
    today = datetime.now().strftime("%Y-%m-%d")

    print(f"Scraping {len(SOURCES)} AI sources ({today})...", file=sys.stderr)
    sections = [f"# AI News — {today}\n\nScraping context for daily digest.\n"]
    total = 0

    all_article_links = []

    for src in SOURCES:
        if total >= MAX_TOTAL_CHARS:
            print(f"Token limit reached, skipping remaining sources", file=sys.stderr)
            break

        print(f"  [{src['name']}]...", file=sys.stderr)
        content, meta = scrape(src["url"], api_key)

        for link in meta.get("article_links", [])[:3]:
            link["source_name"] = src["name"]
            all_article_links.append(link)

        meta_block = ""
        if meta.get("og_image"):
            meta_block += f"\nPage image: {meta['og_image']}"
        if meta.get("article_links"):
            meta_block += "\nRecent articles:"
            for link in meta["article_links"][:5]:
                meta_block += f"\n  - [{link['title']}]({link['url']})"

        favicon = f"https://www.google.com/s2/favicons?domain={src['domain']}&sz=128"
        section = f"\n\n## {src['name']}\nSource: {src['url']}\nLogo: {favicon}{meta_block}\n\n{content}"
        sections.append(section)
        total += len(section)
        time.sleep(0.5)

    print(f"  Fetching article images ({len(all_article_links)} links)...", file=sys.stderr)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        future_map = {pool.submit(fetch_article_image, l["url"]): l for l in all_article_links}
        for future in concurrent.futures.as_completed(future_map):
            link = future_map[future]
            try:
                img = future.result()
                if img:
                    link["image"] = img
            except Exception:
                pass

    images_found = sum(1 for l in all_article_links if l.get("image"))
    print(f"  Found {images_found}/{len(all_article_links)} article images", file=sys.stderr)

    if all_article_links:
        img_section = "\n\n## Article Images (for digest rendering)\n"
        for link in all_article_links:
            if link.get("image"):
                img_section += f"\n- [{link['title']}]({link['url']})"
                img_section += f"\n  Image: {link['image']}"
                img_section += f"\n  Source: {link['source_name']}"
        sections.append(img_section)
        total += len(img_section)

    raw = "".join(sections)
    out.write_text(raw, encoding="utf-8")
    print(f"Scraped ~{total//4:,} tokens -> {out}", file=sys.stderr)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Scrapes AI news sources and prepares content for Gemini synthesis.
Output: /tmp/ai_news_raw.txt

Requires (optional):
  FIRECRAWL_API_KEY → better scraping quality. Falls back to basic HTTP.
"""
import json
import os
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

SOURCES = [
    {"name": "Anthropic News",      "url": "https://www.anthropic.com/news"},
    {"name": "OpenAI Blog",          "url": "https://openai.com/blog"},
    {"name": "Google DeepMind Blog", "url": "https://deepmind.google/discover/blog/"},
    {"name": "HuggingFace Blog",     "url": "https://huggingface.co/blog"},
    {"name": "Mistral News",         "url": "https://mistral.ai/news/"},
    {"name": "TechCrunch AI",        "url": "https://techcrunch.com/category/artificial-intelligence/"},
    {"name": "VentureBeat AI",       "url": "https://venturebeat.com/category/ai/"},
    {"name": "The Batch (DeepLearning.AI)", "url": "https://www.deeplearning.ai/the-batch/"},
    {"name": "AI News",              "url": "https://artificialintelligence-news.com/"},
    {"name": "Ars Technica AI",      "url": "https://arstechnica.com/ai/"},
]

MAX_CHARS_PER_SOURCE = 3000   # ~750 tokens
MAX_TOTAL_CHARS = 28000       # ~7000 tokens → Gemini Flash handles easily


def scrape_firecrawl(url: str, api_key: str) -> str:
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
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            return data.get("data", {}).get("markdown", "")[:MAX_CHARS_PER_SOURCE]
    except Exception as e:
        return f"[Firecrawl error for {url}: {e}]"


def scrape_basic(url: str) -> str:
    import re
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:MAX_CHARS_PER_SOURCE]
    except Exception as e:
        return f"[Fetch error for {url}: {e}]"


def scrape(url: str, api_key: str | None) -> str:
    if api_key:
        content = scrape_firecrawl(url, api_key)
        if not content.startswith("[Firecrawl error"):
            return content
        print(f"    Firecrawl failed, falling back to basic HTTP", file=sys.stderr)
    return scrape_basic(url)


def main():
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    out = Path("/tmp/ai_news_raw.txt")
    today = datetime.now().strftime("%Y-%m-%d")

    print(f"Scraping {len(SOURCES)} AI sources ({today})...", file=sys.stderr)
    sections = [f"# AI News — {today}\n\nScraping context for daily digest.\n"]
    total = 0

    for src in SOURCES:
        if total >= MAX_TOTAL_CHARS:
            print(f"Token limit reached, skipping remaining sources", file=sys.stderr)
            break

        print(f"  [{src['name']}]...", file=sys.stderr)
        content = scrape(src["url"], api_key)
        section = f"\n\n## {src['name']}\nSource: {src['url']}\n\n{content}"
        sections.append(section)
        total += len(section)
        time.sleep(0.5)  # respectful rate limiting

    raw = "".join(sections)
    out.write_text(raw, encoding="utf-8")
    print(f"Scraped ~{total//4:,} tokens → {out}", file=sys.stderr)


if __name__ == "__main__":
    main()

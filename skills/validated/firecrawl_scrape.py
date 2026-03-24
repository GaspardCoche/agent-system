#!/usr/bin/env python3
"""
Skill: firecrawl_scrape
Remplace: mcp__firecrawl__firecrawl_scrape
Validé le: 2026-03-20

Usage:
  python3 skills/validated/firecrawl_scrape.py --url URL [--format markdown]

Variables d'env requises:
  FIRECRAWL_API_KEY

Sortie: JSON avec data.markdown (ou data.html selon format)
"""
import argparse
import json
import os
import sys
import time

try:
    import requests
except ImportError:
    print("pip install requests", file=sys.stderr)
    sys.exit(1)


def scrape(url: str, formats: list[str], only_main_content: bool = True, max_retries: int = 3) -> dict:
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        print("Error: FIRECRAWL_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    payload = {
        "url": url,
        "formats": formats,
        "onlyMainContent": only_main_content,
    }

    for attempt in range(max_retries):
        try:
            resp = requests.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30,
            )

            if resp.status_code == 429:
                wait = 2 ** attempt
                print(f"Rate limited, waiting {wait}s...", file=sys.stderr)
                time.sleep(wait)
                continue

            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.Timeout:
            print(f"Timeout on attempt {attempt + 1}/{max_retries}", file=sys.stderr)
            if attempt == max_retries - 1:
                raise

    return {"success": False, "error": "Max retries exceeded"}


def main():
    parser = argparse.ArgumentParser(description="Scrape a URL with Firecrawl")
    parser.add_argument("--url", required=True, help="URL to scrape")
    parser.add_argument(
        "--format",
        default="markdown",
        choices=["markdown", "html", "links", "screenshot"],
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--all-content",
        action="store_true",
        help="Include non-main content (ads, nav, etc.)",
    )
    args = parser.parse_args()

    result = scrape(
        url=args.url,
        formats=[args.format],
        only_main_content=not args.all_content,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

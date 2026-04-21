#!/usr/bin/env python3
"""Parse a GitHub issue body and create a vault note in docs/vault/ai-news/."""
import os
import re
from datetime import datetime
from pathlib import Path


def main():
    body = os.environ.get("ISSUE_BODY", "")
    raw_title = os.environ.get("ISSUE_TITLE", "Article")
    title = re.sub(r'^[\U0001f4cc\U0001f4cd\u2b50\s]+', '', raw_title).strip()

    meta = {}
    for line in body.split("\n"):
        if "---" in line.strip() and len(line.strip()) <= 4:
            break
        if ":" in line:
            key, val = line.split(":", 1)
            meta[key.strip().lower()] = val.strip()

    summary_parts = body.split("---")
    summary = summary_parts[-1].strip() if len(summary_parts) > 1 else body.strip()

    date = datetime.now().strftime("%Y-%m-%d")
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower())[:60].strip('-')
    note_dir = Path("docs/vault/ai-news")
    note_dir.mkdir(parents=True, exist_ok=True)
    note_path = note_dir / f"{date}-{slug}.md"

    source = meta.get("source", "")
    url = meta.get("url", "")
    category = meta.get("category", "")
    image = meta.get("image", "")
    importance = meta.get("importance", "")
    tags_raw = meta.get("tags", "")
    tags_list = [t.strip() for t in tags_raw.split(",") if t.strip()]

    tags_fmt = ", ".join(f'"{t}"' for t in tags_list)
    image_block = f"\n![{title}]({image})\n" if image else ""

    note = f"""---
title: "{title}"
source: "{source}"
url: "{url}"
category: "{category}"
importance: "{importance}"
date: {date}
tags: [{tags_fmt}]
---

# {title}
{image_block}
**Source:** [{source}]({url}) | **Categorie:** {category} | **Importance:** {importance}

{summary}

---
*Sauvegarde depuis AI Intelligence Briefing du {date}*
"""
    note_path.write_text(note, encoding="utf-8")
    print(f"Note created: {note_path}")


if __name__ == "__main__":
    main()

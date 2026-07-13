#!/usr/bin/env python3
"""Blanchit les image_url mortes ou non-image du digest JSON.

Une image_url qui 404, timeout ou ne renvoie pas un content-type image/*
casse le rendu (icône « image manquante » dans Gmail). On la vide : les
templates retombent alors sur le placeholder dégradé + favicon de la source.

Usage: validate_images.py /tmp/ai_digest.json
"""
import json
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = {"User-Agent": "Mozilla/5.0 (compatible; DigestBot/1.0)"}
TIMEOUT = 6


def _is_live_image(url: str) -> bool:
    if not url or not url.startswith("http") or "s2/favicons" in url:
        return False
    try:
        req = urllib.request.Request(url, method="HEAD", headers=UA)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            ct = resp.headers.get("Content-Type", "")
            return resp.status < 400 and (not ct or ct.startswith("image/"))
    except Exception:
        try:
            req = urllib.request.Request(url, headers={**UA, "Range": "bytes=0-2047"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                ct = resp.headers.get("Content-Type", "")
                return resp.status < 400 and ct.startswith("image/")
        except Exception:
            return False


def main(path: str) -> None:
    digest = json.load(open(path, encoding="utf-8"))

    entries = []
    if digest.get("top_story"):
        entries.append(digest["top_story"])
    entries += digest.get("articles", [])
    entries += digest.get("extended", [])

    urls = {e.get("image_url", "") for e in entries if e.get("image_url")}
    if not urls:
        print("No image URLs to check")
        return

    with ThreadPoolExecutor(max_workers=8) as pool:
        alive = dict(zip(urls, pool.map(_is_live_image, urls)))

    removed = 0
    for e in entries:
        img = e.get("image_url", "")
        if img and not alive.get(img, False):
            e["image_url"] = ""
            removed += 1

    json.dump(digest, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Images: {len(urls)} checked, {removed} dead → placeholder")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/ai_digest.json")

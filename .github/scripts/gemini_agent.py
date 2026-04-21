#!/usr/bin/env python3
"""
Gemini agent for large-context analysis tasks.
Uses Google GenAI SDK (google-genai).
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path


def get_client():
    from google import genai
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    return genai.Client(api_key=api_key)


def select_model(token_count: int) -> str:
    return "gemini-2.5-pro" if token_count > 200_000 else "gemini-2.5-flash"


TASK_PROMPTS = {
    "analyze": (
        "Analyze the following content and return ONLY valid JSON "
        "(no markdown fences):\n"
        '{"findings":[{"description":"str","severity":"critical|high|medium|low",'
        '"location":"str"}],"summary":"str","recommendations":["str"],'
        '"metrics":{"complexity":"str","maintainability":"str"}}\n\nCONTENT:\n'
    ),
    "synthesize": (
        "Synthesize the following raw research results into ONLY valid JSON "
        "(no markdown fences):\n"
        '{"key_findings":["str"],"sources":["str"],"recommendations":["str"],'
        '"confidence":0.8,"summary":"str"}\n\nRAW RESEARCH:\n'
    ),
    "ai_digest": (
        "You are a senior AI analyst creating a premium intelligence briefing for a B2B tech executive.\n"
        "Your reader is a CFO/CEO who needs to understand AI trends affecting business strategy.\n\n"
        "From the raw scraped content below, create a structured digest. Return ONLY valid JSON (no markdown fences).\n\n"
        "CRITICAL RULES:\n"
        "- Extract 10-15 distinct news items (deduplicate across sources)\n"
        "- The FIRST article must be the TOP STORY — the single most impactful news of the period\n"
        "- For the top story: write a 4-5 sentence detailed analysis with business implications\n"
        "- For other articles: 2-3 sentence summaries focused on 'so what?' for business leaders\n"
        "- ALL text (headline, summaries, trends, one_liner) MUST be in French\n"
        "- SOURCE DIVERSITY: Include articles from at least 5 different sources. Maximum 3 articles from any single source.\n\n"
        "URL RULES (CRITICAL — violations cause broken links):\n"
        "- Look for the 'VERIFIED Article Links' section — these URLs have been validated (HTTP 200)\n"
        "- ONLY use URLs marked as [VERIFIED] in that section. Copy them EXACTLY, character for character\n"
        "- NEVER construct, guess, modify, or shorten URLs. If you cannot find a verified URL for an article, use the source listing page URL (e.g. https://www.anthropic.com/news)\n"
        "- For image_url: use the 'Image:' URL listed under each verified link. If none, use the source 'Logo:' URL\n\n"
        "CATEGORIES (pick the best fit):\n"
        "  Modeles (new models, benchmarks, capabilities)\n"
        "  Outils & Plateformes (dev tools, APIs, platforms, SDKs)\n"
        "  Recherche (papers, breakthroughs, scientific advances)\n"
        "  Business & Levees (funding, acquisitions, partnerships, revenue)\n"
        "  Open Source (new OSS releases, community projects)\n"
        "  Regulation & Ethique (laws, governance, safety, alignment)\n\n"
        "IMPORTANCE LEVELS:\n"
        "  must_read — game-changing, affects strategy (max 3-4)\n"
        "  important — significant, worth understanding (4-6)\n"
        "  worth_noting — interesting, good to know (3-5)\n\n"
        "JSON STRUCTURE:\n"
        "{\n"
        '  "date": "YYYY-MM-DD",\n'
        '  "headline": "string — bold, punchy theme in French (like a newspaper headline)",\n'
        '  "one_liner": "string — the #1 insight in one sentence, French",\n'
        '  "top_story": {\n'
        '    "title": "string — original title",\n'
        '    "source": "string — source name",\n'
        '    "url": "string — article URL",\n'
        '    "image_url": "string — og:image or source logo URL",\n'
        '    "summary": "string — 4-5 sentence deep analysis in French, business impact focus",\n'
        '    "category": "string",\n'
        '    "company_tags": ["string"]\n'
        "  },\n"
        '  "articles": [\n'
        "    {\n"
        '      "title": "string — original title",\n'
        '      "source": "string — source name",\n'
        '      "url": "string — article URL",\n'
        '      "image_url": "string — og:image URL or source logo/favicon URL",\n'
        '      "summary": "string — 2-3 sentences in French, business angle",\n'
        '      "category": "Modeles | Outils & Plateformes | Recherche | Business & Levees | Open Source | Regulation & Ethique",\n'
        '      "importance": "must_read | important | worth_noting",\n'
        '      "company_tags": ["string"]\n'
        "    }\n"
        "  ],\n"
        '  "trends": [\n'
        "    {\n"
        '      "title": "string — trend name in French",\n'
        '      "description": "string — 1-2 sentence explanation in French"\n'
        "    }\n"
        "  ],\n"
        '  "stats": {"sources_scraped": 10, "articles_extracted": 0}\n'
        "}\n\n"
        "RAW SCRAPED CONTENT:\n"
    ),
    "review": (
        "Review the following code and return ONLY valid JSON (no markdown fences):\n"
        '{"issues":[{"line":"str","severity":"str","description":"str",'
        '"suggestion":"str"}],"overall_quality":"excellent|good|fair|poor",'
        '"summary":"str","approved":true}\n\nCODE:\n'
    ),
}


def call_with_retry(client, model: str, prompt: str, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        try:
            resp = client.models.generate_content(model=model, contents=prompt)
            return resp.text
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                wait = (2 ** attempt) * 30
                print(f"Rate limited. Waiting {wait}s (attempt {attempt+1}/{max_retries})...",
                      file=sys.stderr)
                time.sleep(wait)
                if attempt == max_retries - 1 and model == "gemini-2.5-pro":
                    print("Falling back to gemini-2.5-flash", file=sys.stderr)
                    model = "gemini-2.5-flash"
            else:
                raise
    raise RuntimeError("Max retries exceeded")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task",   required=True, choices=list(TASK_PROMPTS))
    parser.add_argument("--input",  required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model",  default=None)
    args = parser.parse_args()

    content = Path(args.input).read_text(encoding="utf-8")
    token_estimate = len(content) // 4
    model = args.model or select_model(token_estimate)

    print(f"Task={args.task} | ~{token_estimate:,} tokens | Model={model}", file=sys.stderr)

    prompt = TASK_PROMPTS[args.task] + content
    client = get_client()
    raw = call_with_retry(client, model, prompt)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group())
            except json.JSONDecodeError:
                result = {"raw_response": raw, "parse_error": True}
        else:
            result = {"raw_response": raw, "parse_error": True}

    result["_meta"] = {
        "model": model,
        "task": args.task,
        "tokens_estimate": token_estimate,
        "source": "gemini_agent"
    }

    log_path = Path("/tmp/token_usage.jsonl")
    with open(log_path, "a") as f:
        f.write(json.dumps({
            "ts": time.time(),
            "task": args.task,
            "model": model,
            "tokens": token_estimate
        }) + "\n")

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Result written to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()

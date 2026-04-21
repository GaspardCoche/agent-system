#!/usr/bin/env python3
"""
Gemini agent for large-context analysis tasks.
Uses Google GenAI SDK (google-genai).

Usage:
  python3 gemini_agent.py --task analyze    --input /tmp/input.txt --output /tmp/output.json
  python3 gemini_agent.py --task synthesize --input /tmp/raw.txt  --output /tmp/synth.json
  python3 gemini_agent.py --task ai_digest  --input /tmp/raw.txt  --output /tmp/digest.json
  python3 gemini_agent.py --task review     --input /tmp/code.txt --output /tmp/review.json
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
        "You are an AI news analyst creating a weekly intelligence briefing for a B2B tech executive.\n\n"
        "From the raw scraped content below, extract the most important AI news and return ONLY valid JSON (no markdown fences).\n\n"
        "Rules:\n"
        "- Extract 8-15 distinct articles/announcements (skip duplicates across sources)\n"
        "- For each article, reconstruct the most likely URL from the source domain + article slug\n"
        "- Categorize each: Models, Tools & Platforms, Research, Business & Funding, Open Source, Regulation\n"
        "- Rate importance: must_read (top 3-4), important, worth_noting\n"
        "- Write summaries in French, 2-3 sentences, focusing on business impact\n"
        "- Include a headline (French) summarizing the week's theme\n"
        "- Include 2-3 key trends observed across sources\n"
        "- Include a one_liner: the single most important takeaway\n\n"
        "Return this exact JSON structure:\n"
        "{\n"
        '  "headline": "string — one-line theme of the week in French",\n'
        '  "one_liner": "string — the #1 takeaway in French",\n'
        '  "articles": [\n'
        "    {\n"
        '      "title": "string — original article title",\n'
        '      "source": "string — source name (e.g. Anthropic, OpenAI, TechCrunch)",\n'
        '      "url": "string — best guess URL for the article",\n'
        '      "summary": "string — 2-3 sentence summary in French, business impact focus",\n'
        '      "category": "Models | Tools & Platforms | Research | Business & Funding | Open Source | Regulation",\n'
        '      "importance": "must_read | important | worth_noting",\n'
        '      "company_tags": ["string — companies mentioned"]\n'
        "    }\n"
        "  ],\n"
        '  "trends": ["string — 2-3 macro trends in French"],\n'
        '  "stats": {\n'
        '    "sources_scraped": 0,\n'
        '    "articles_extracted": 0\n'
        "  }\n"
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

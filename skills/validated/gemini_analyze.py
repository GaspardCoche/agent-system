#!/usr/bin/env python3
"""
Skill: gemini_analyze
Remplace: appels directs à gemini_agent.py pour analyses longues
Validé le: 2026-03-24

Usage:
  # Analyser un fichier
  python3 skills/validated/gemini_analyze.py --file rapport.md --prompt "Résume les 5 points clés"

  # Analyser du texte direct
  python3 skills/validated/gemini_analyze.py --text "..." --prompt "Identifie les actions"

  # Analyser plusieurs fichiers
  python3 skills/validated/gemini_analyze.py --file a.md --file b.md --prompt "Compare"

Variables d'env requises:
  GEMINI_API_KEY

Sortie: JSON avec response (texte) et usage (tokens)

Utiliser pour: fichiers > 20KB, analyses multi-documents, synthèses longues
"""
import argparse
import json
import os
import sys

try:
    import google.generativeai as genai
except ImportError:
    try:
        from google import genai as genai_new
        USE_NEW_SDK = True
    except ImportError:
        print("pip install google-generativeai", file=sys.stderr)
        sys.exit(1)
    else:
        USE_NEW_SDK = True
else:
    USE_NEW_SDK = False


def analyze_with_gemini(prompt: str, contents: list[str], model: str = "gemini-2.0-flash") -> dict:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    # Build full prompt
    if len(contents) == 1:
        full_prompt = f"{prompt}\n\n---\n\n{contents[0]}"
    else:
        parts = "\n\n---\n\n".join(f"### Document {i+1}\n{c}" for i, c in enumerate(contents))
        full_prompt = f"{prompt}\n\n{parts}"

    if USE_NEW_SDK:
        from google import genai as g
        client = g.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=full_prompt,
        )
        text = response.text
        usage = {}
        if hasattr(response, 'usage_metadata'):
            usage = {
                "input_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0),
                "output_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0),
            }
    else:
        genai.configure(api_key=api_key)
        m = genai.GenerativeModel(model)
        response = m.generate_content(full_prompt)
        text = response.text
        usage = {}

    return {"response": text, "usage": usage, "model": model}


def main():
    parser = argparse.ArgumentParser(description="Analyze content with Gemini")
    parser.add_argument("--prompt", required=True, help="Analysis prompt / question")
    parser.add_argument("--file", action="append", default=[], dest="files",
                        help="File(s) to analyze (repeatable)")
    parser.add_argument("--text", help="Direct text to analyze")
    parser.add_argument("--model", default="gemini-2.0-flash",
                        help="Gemini model (default: gemini-2.0-flash)")
    args = parser.parse_args()

    contents = []
    for f in args.files:
        with open(f) as fh:
            contents.append(fh.read())
    if args.text:
        contents.append(args.text)

    if not contents:
        print("Error: provide --file or --text", file=sys.stderr)
        sys.exit(1)

    result = analyze_with_gemini(args.prompt, contents, args.model)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

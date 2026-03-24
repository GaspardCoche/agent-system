#!/usr/bin/env python3
"""
Merges results from multiple prior agents into one compressed task JSON.
Prevents token bloat when passing context between agents.

Usage:
  python3 context_compressor.py \
    --inputs /tmp/prior_results/ \
    --output /tmp/agent_task.json \
    --task '{"task_id":"123","description":"..."}' \
    --max-tokens 8000
"""
import argparse
import json
from pathlib import Path

CHARS_PER_TOKEN = 4


def truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + f"\n[...{len(text)-max_chars} chars truncated...]\n" + text[-half:]


def compress(result: dict, budget: int) -> dict:
    """Keep only essential fields, truncate large content."""
    out = {k: result[k] for k in ["agent", "status", "summary", "task_id"] if k in result}
    # Keep first 5 items of arrays
    for key in ["findings", "recommendations", "key_findings", "issues", "tldr"]:
        if key in result:
            out[key] = result[key][:5]
    # Include raw_response only if budget allows
    remaining = budget - len(json.dumps(out))
    if "raw_response" in result and remaining > 500:
        out["raw_response"] = truncate(result["raw_response"], remaining)
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--inputs",     required=True, help="Directory of prior result JSON files")
    p.add_argument("--output",     required=True, help="Output merged task JSON path")
    p.add_argument("--task",       help="Original task JSON string")
    p.add_argument("--task-file",  help="Path to task JSON file (alternative to --task)")
    p.add_argument("--max-tokens", type=int, default=8000)
    args = p.parse_args()

    if not args.task and not args.task_file:
        p.error("Either --task or --task-file is required")

    max_chars = args.max_tokens * CHARS_PER_TOKEN
    if args.task_file:
        base_task = json.loads(Path(args.task_file).read_text())
    else:
        base_task = json.loads(args.task)

    # Load all prior results
    prior = {}
    for f in sorted(Path(args.inputs).rglob("agent_result.json")):
        try:
            data = json.loads(f.read_text())
            role = data.get("agent", f.parent.name)
            prior[role] = data
        except Exception:
            pass

    # Allocate budget per result
    base_size = len(json.dumps(base_task))
    per_budget = (max_chars - base_size) // max(len(prior), 1)

    merged = {
        **base_task,
        "prior_agent_results": {r: compress(d, per_budget) for r, d in prior.items()},
        "_note": f"Compressed to ~{args.max_tokens} tokens. Full data in artifacts."
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(merged, indent=2, ensure_ascii=False))

    total = len(json.dumps(merged))
    print(f"Merged context: ~{total//CHARS_PER_TOKEN} tokens written to {args.output}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Skill Tracker — Analyseur de patterns MCP pour Sage
Usage: python3 skill_tracker.py --retrospectives-dir DIR --registry skills/registry.json
"""
import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import date


def load_retrospectives(directory: str) -> list[dict]:
    """Charge tous les fichiers JSON contenant des rétrospectives."""
    retros = []
    if not os.path.isdir(directory):
        return retros

    for root, _, files in os.walk(directory):
        for fname in files:
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(root, fname)
            try:
                data = json.load(open(fpath))
                if isinstance(data, list):
                    for item in data:
                        if "retrospective" in item:
                            retros.append(item)
                elif isinstance(data, dict) and "retrospective" in data:
                    retros.append(data)
            except Exception:
                pass
    return retros


def analyze_patterns(retrospectives: list[dict]) -> dict[str, int]:
    """Agrège les patterns MCP par fréquence."""
    patterns = defaultdict(int)
    for retro in retrospectives:
        mcp_patterns = retro.get("retrospective", {}).get("mcp_patterns", [])
        for pattern in mcp_patterns:
            parts = pattern.split(":")
            if len(parts) >= 3:
                tool, context, count_str = parts[0], parts[1], parts[2].rstrip("x")
                try:
                    count = int(count_str)
                except ValueError:
                    count = 1
                key = f"{tool}:{context}"
                patterns[key] += count
    return dict(patterns)


def update_registry(registry_path: str, new_candidates: dict[str, int], threshold: int = 3) -> dict:
    """Met à jour le registry avec les nouveaux candidats."""
    if os.path.exists(registry_path):
        registry = json.load(open(registry_path))
    else:
        registry = {"version": "1.0", "skills": [], "validation_threshold": {}}

    today = date.today().isoformat()
    existing_names = {s["name"] for s in registry["skills"]}
    added = []

    for pattern, count in new_candidates.items():
        if count < threshold:
            continue

        tool, context = pattern.split(":", 1)
        skill_name = f"{tool}_{context}"

        if skill_name in existing_names:
            # Mettre à jour le compteur
            for s in registry["skills"]:
                if s["name"] == skill_name:
                    s["usage_count"] = s.get("usage_count", 0) + count
            continue

        # Nouveau candidat
        new_skill = {
            "name": skill_name,
            "mcp_tool": f"mcp__{tool.replace('-', '__')}__{tool}",
            "context": context,
            "status": "candidate",
            "usage_count": count,
            "created_date": today,
            "validated_date": None,
            "script": None,
            "description": f"Auto-detected: {tool} used for {context}",
        }
        registry["skills"].append(new_skill)
        existing_names.add(skill_name)
        added.append(skill_name)

    registry["last_updated"] = today

    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    return {"added": added, "total_skills": len(registry["skills"])}


def main():
    parser = argparse.ArgumentParser(description="Track MCP patterns and update skill registry")
    parser.add_argument("--retrospectives-dir", default="/tmp/retrospectives", help="Directory with retrospective JSON files")
    parser.add_argument("--registry", default="skills/registry.json", help="Path to skills registry")
    parser.add_argument("--threshold", type=int, default=3, help="Min uses to become a candidate")
    parser.add_argument("--report", action="store_true", help="Print analysis report")
    args = parser.parse_args()

    retrospectives = load_retrospectives(args.retrospectives_dir)
    print(f"Loaded {len(retrospectives)} retrospectives", file=sys.stderr)

    patterns = analyze_patterns(retrospectives)
    print(f"Found {len(patterns)} unique patterns", file=sys.stderr)

    result = update_registry(args.registry, patterns, args.threshold)

    if args.report:
        print("\n=== MCP Pattern Analysis ===")
        for pattern, count in sorted(patterns.items(), key=lambda x: -x[1]):
            status = "✅ candidate" if count >= args.threshold else "⏳ below threshold"
            print(f"  {pattern}: {count}x — {status}")

        print(f"\n=== Registry Update ===")
        print(f"  New candidates added: {result['added']}")
        print(f"  Total skills in registry: {result['total_skills']}")

    output = {
        "patterns": patterns,
        "update_result": result,
        "retrospectives_analyzed": len(retrospectives),
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Generate a markdown report for a workflow run and update docs/data/runs.json
for the GitHub Pages dashboard.

Usage:
  python3 generate_report.py \
    --run-id 12345678 \
    --workflow orchestrator \
    --title "Fix auth bug" \
    --status success \
    --event issues \
    --repo owner/repo \
    --results-dir /tmp/all_results \
    --output-dir reports \
    --dashboard-file docs/data/runs.json \
    [--summary "Optional summary text"] \
    [--task-id 42]
"""
import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--run-id",        required=True)
    p.add_argument("--workflow",      required=True)
    p.add_argument("--title",         default="")
    p.add_argument("--status",        required=True, choices=["success", "partial", "failed"])
    p.add_argument("--event",         default="")
    p.add_argument("--repo",          default="")
    p.add_argument("--results-dir",   default="/tmp/all_results")
    p.add_argument("--output-dir",    default="reports")
    p.add_argument("--dashboard-file", default="docs/data/runs.json")
    p.add_argument("--summary",       default="")
    p.add_argument("--task-id",       default="")
    return p.parse_args()


def load_agent_results(results_dir: str) -> list[dict]:
    """Load all agent_result.json files from subdirectories."""
    results = []
    for f in sorted(Path(results_dir).rglob("agent_result.json")):
        try:
            data = json.loads(f.read_text())
            results.append(data)
        except Exception:
            pass
    return results


def status_emoji(s: str) -> str:
    return {"success": "✅", "failed": "❌", "partial": "⚠️", "needs_retry": "🔄"}.get(s, "❓")


def generate_markdown(args, agent_results: list[dict]) -> str:
    now = datetime.now(timezone.utc)
    title = args.title or f"Run #{args.run_id}"
    repo_url = f"https://github.com/{args.repo}/actions/runs/{args.run_id}" if args.repo else ""

    lines = [
        f"# {status_emoji(args.status)} {title}",
        "",
        f"**Workflow**: `{args.workflow}` · **Run**: [{args.run_id}]({repo_url}) · **Date**: {now.strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Status**: `{args.status}` · **Event**: `{args.event or 'manual'}`",
        "",
    ]

    if args.summary:
        lines += [f"> {args.summary}", ""]

    if agent_results:
        lines += ["## Agent Results", ""]
        lines += ["| Agent | Status | Summary |", "|-------|--------|---------|"]
        for r in agent_results:
            agent = r.get("agent", "unknown")
            s = r.get("status", "failed")
            summary = re.sub(r'\s+', ' ', r.get("summary", "—")).strip()[:120]
            lines.append(f"| **{agent}** | {status_emoji(s)} `{s}` | {summary} |")
        lines.append("")

        # Retrospectives
        retros = [(r.get("agent", "?"), r["retrospective"]) for r in agent_results if "retrospective" in r]
        if retros:
            lines += ["## Retrospectives", ""]
            for agent, retro in retros:
                lines += [
                    f"### {agent}",
                    f"- **Ce qui a marché** : {retro.get('what_worked', '—')}",
                    f"- **Ce qui a échoué** : {retro.get('what_failed', '—')}",
                ]
                if retro.get("improvement_suggestion"):
                    lines.append(f"- **Amélioration** : {retro['improvement_suggestion']}")
                patterns = retro.get("mcp_patterns", [])
                if patterns:
                    lines.append(f"- **MCP patterns** : `{'`, `'.join(patterns)}`")
                lines.append("")

    lines += ["---", f"*Généré automatiquement le {now.strftime('%Y-%m-%d %H:%M UTC')} · [Dashboard](/agent-system)*"]
    return "\n".join(lines)


def update_dashboard(args, agent_results: list[dict], dashboard_file: str) -> None:
    path = Path(dashboard_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        runs: list = json.loads(path.read_text()) if path.exists() else []
    except Exception:
        runs = []

    # Remove old entry for same run_id if re-running
    runs = [r for r in runs if str(r.get("run_id")) != str(args.run_id)]

    agents_summary = [
        {"name": r.get("agent", "?"), "status": r.get("status", "failed")}
        for r in agent_results
    ]

    entry = {
        "run_id": args.run_id,
        "workflow": args.workflow,
        "title": args.title or f"Run #{args.run_id}",
        "status": args.status,
        "event": args.event,
        "repo": args.repo,
        "task_id": args.task_id,
        "summary": args.summary[:200] if args.summary else "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agents": agents_summary,
    }
    runs.append(entry)

    # Keep last 100 runs
    runs = runs[-100:]
    path.write_text(json.dumps(runs, indent=2, ensure_ascii=False))
    print(f"Dashboard updated: {path} ({len(runs)} runs)")


def main():
    args = parse_args()
    agent_results = load_agent_results(args.results_dir)

    # Generate markdown report
    md = generate_markdown(args, agent_results)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    slug = re.sub(r'[^a-zA-Z0-9-]', '-', args.title.lower())[:40] if args.title else args.run_id
    filename = f"{now.strftime('%Y-%m-%d')}-{args.workflow}-{slug}.md"
    report_path = output_dir / filename
    report_path.write_text(md)
    print(f"Report written: {report_path}")

    # Update dashboard JSON
    update_dashboard(args, agent_results, args.dashboard_file)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Generate a markdown report for a workflow run and update docs/data/runs.json.
Reports are written to docs/reports/ so Netlify can serve them to the dashboard.

Usage:
  python3 generate_report.py \
    --run-id 12345678 \
    --workflow orchestrator \
    --title "Fix auth bug" \
    --status success \
    --event issues \
    --repo owner/repo \
    --results-dir /tmp/all_results \
    [--summary "Optional summary text"] \
    [--task-id 42]
"""
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

DASHBOARD_FILE = "docs/data/runs.json"
REPORTS_DIR = "docs/reports"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--run-id",        required=True)
    p.add_argument("--workflow",      required=True)
    p.add_argument("--title",         default="")
    p.add_argument("--status",        required=True, choices=["success", "partial", "failed"])
    p.add_argument("--event",         default="")
    p.add_argument("--repo",          default="")
    p.add_argument("--results-dir",   default="/tmp/all_results")
    p.add_argument("--summary",       default="")
    p.add_argument("--task-id",       default="")
    p.add_argument("--output-dir",    default=REPORTS_DIR,
                   help="Directory to write report markdown (default: docs/reports)")
    p.add_argument("--dashboard-file", default=DASHBOARD_FILE,
                   help="Path to runs.json dashboard file (default: docs/data/runs.json)")
    return p.parse_args()


def load_agent_results(results_dir: str) -> list[dict]:
    results = []
    for f in sorted(Path(results_dir).rglob("agent_result.json")):
        try:
            data = json.loads(f.read_text())
            results.append(data)
        except Exception:
            pass
    return results


def status_emoji(s: str) -> str:
    return {
        "success": "✅", "complete": "✅", "passed": "✅",
        "failed": "❌", "error": "❌",
        "partial": "⚠️", "warning": "⚠️", "needs_retry": "🔄",
        "pending_approval": "⏳", "skipped": "⏭️",
    }.get(str(s).lower(), "🔵")


def extract_summary(agent_results: list[dict]) -> str:
    """Build a one-line summary from all agent results."""
    parts = []
    for r in agent_results:
        s = r.get("summary", "").strip()
        if s:
            parts.append(s[:150])
    return " · ".join(parts[:3])


def extract_next_actions(agent_results: list[dict]) -> list[str]:
    """Collect next_actions from all agents."""
    actions = []
    for r in agent_results:
        for a in r.get("next_actions", []):
            if a not in actions:
                actions.append(a)
    return actions


def generate_markdown(args, agent_results: list[dict]) -> str:
    now = datetime.now(timezone.utc)
    title = args.title or f"Run #{args.run_id}"
    repo_url = f"https://github.com/{args.repo}/actions/runs/{args.run_id}" if args.repo else ""
    overall_emoji = status_emoji(args.status)

    lines = [
        f"# {overall_emoji} {title}",
        "",
        f"| | |",
        f"|---|---|",
        f"| **Workflow** | `{args.workflow}` |",
        f"| **Run** | [{args.run_id}]({repo_url}) |",
        f"| **Date** | {now.strftime('%Y-%m-%d %H:%M UTC')} |",
        f"| **Status** | `{args.status}` |",
        f"| **Trigger** | `{args.event or 'manual'}` |",
        "",
    ]

    # Next actions — top of report, most visible
    next_actions = extract_next_actions(agent_results)
    if next_actions:
        lines += ["## ⚡ Actions à faire", ""]
        for a in next_actions:
            lines.append(f"- [ ] {a}")
        lines.append("")

    # Summary
    summary = args.summary or extract_summary(agent_results)
    if summary:
        lines += [f"> {summary}", ""]

    # Agent results table
    if agent_results:
        lines += ["## Résultats agents", ""]
        lines += ["| Agent | Status | Résumé |", "|-------|--------|--------|"]
        for r in agent_results:
            agent = r.get("agent", "unknown")
            s = r.get("status", "failed")
            summ = re.sub(r'\s+', ' ', r.get("summary", "—")).strip()[:200]
            lines.append(f"| {status_emoji(s)} **{agent}** | `{s}` | {summ} |")
        lines.append("")

        # Findings
        all_findings = []
        for r in agent_results:
            for f in r.get("findings", r.get("key_findings", [])):
                if isinstance(f, str) and f not in all_findings:
                    all_findings.append(f)
        if all_findings:
            lines += ["## 🔍 Findings", ""]
            for f in all_findings[:10]:
                lines.append(f"- {f}")
            lines.append("")

        # Artifacts
        all_artifacts = []
        for r in agent_results:
            all_artifacts.extend(r.get("artifacts", []))
        if all_artifacts:
            lines += ["## 📁 Artifacts produits", ""]
            for a in all_artifacts[:10]:
                lines.append(f"- `{a}`")
            lines.append("")

        # Retrospectives
        retros = [(r.get("agent", "?"), r["retrospective"]) for r in agent_results if "retrospective" in r]
        if retros:
            lines += ["## 🔁 Retrospectives", ""]
            for agent, retro in retros:
                lines += [f"### {agent}", ""]
                if retro.get("what_worked"):
                    lines.append(f"**✅ Ce qui a marché :** {retro['what_worked']}")
                if retro.get("what_failed"):
                    lines.append(f"**❌ Ce qui a échoué :** {retro['what_failed']}")
                if retro.get("improvement_suggestion"):
                    lines.append(f"**💡 Amélioration :** {retro['improvement_suggestion']}")
                patterns = retro.get("mcp_patterns", [])
                if patterns:
                    lines.append(f"**🔧 MCP patterns :** `{'`, `'.join(patterns)}`")
                lines.append("")

    gh_run = f"[GitHub Actions]({repo_url})" if repo_url else "GitHub Actions"
    lines += [
        "---",
        f"*Généré le {now.strftime('%Y-%m-%d %H:%M UTC')} · {gh_run}*"
    ]
    return "\n".join(lines)


def update_dashboard(args, agent_results: list[dict], report_filename: str) -> None:
    path = Path(args.dashboard_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        runs: list = json.loads(path.read_text()) if path.exists() else []
    except Exception:
        runs = []

    runs = [r for r in runs if str(r.get("run_id")) != str(args.run_id)]

    summary = args.summary or extract_summary(agent_results)
    next_actions = extract_next_actions(agent_results)

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
        "summary": summary[:250] if summary else "",
        "next_actions": next_actions[:5],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agents": agents_summary,
        "report_file": f"reports/{report_filename}",
    }
    runs.append(entry)
    runs = runs[-100:]
    path.write_text(json.dumps(runs, indent=2, ensure_ascii=False))
    print(f"Dashboard updated: {path} ({len(runs)} runs)")


def main():
    args = parse_args()
    agent_results = load_agent_results(args.results_dir)

    md = generate_markdown(args, agent_results)

    # Write to output dir (served by Netlify when docs/reports/)
    docs_reports = Path(args.output_dir)
    docs_reports.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    slug = re.sub(r'[^a-zA-Z0-9-]', '-', args.title.lower())[:50].strip('-') if args.title else args.run_id
    slug = slug or "untitled"
    filename = f"{now.strftime('%Y-%m-%d')}-{args.workflow}-{slug}.md"
    report_path = docs_reports / filename
    report_path.write_text(md)
    print(f"Report written: {report_path}")

    # Also keep a mirror in reports/ for git browsing
    mirror = Path("reports")
    mirror.mkdir(parents=True, exist_ok=True)
    (mirror / filename).write_text(md)

    update_dashboard(args, agent_results, filename)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Reads a dispatch plan and triggers GitHub Actions workflows via gh CLI.

Dispatch plan schema:
{
  "task_id": "123",
  "agents": [
    {"role": "researcher", "input": "...", "parallel": true},
    {"role": "coder",      "input": "...", "parallel": false, "depends_on": [...]}
  ]
}
"""
import json
import os
import subprocess
import sys
from pathlib import Path


WORKFLOW_MAP = {
    "researcher": "agent-researcher.yml",
    "analyzer":   "agent-analyzer.yml",
    "coder":      "agent-coder.yml",
    "tester":     "agent-tester.yml",
}


def dispatch(repo: str, workflow: str, task_json: dict, token: str) -> bool:
    result = subprocess.run(
        ["gh", "workflow", "run", workflow,
         "--repo", repo,
         "--field", f"task_json={json.dumps(task_json)}"],
        capture_output=True, text=True,
        env={**os.environ, "GITHUB_TOKEN": token}
    )
    if result.returncode != 0:
        print(f"Failed to dispatch {workflow}: {result.stderr}", file=sys.stderr)
        return False
    print(f"Dispatched: {workflow}", file=sys.stderr)
    return True


def main():
    plan_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/dispatch_plan.json")
    plan = json.loads(plan_path.read_text())

    repo  = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")

    parallel   = [a for a in plan["agents"] if a.get("parallel", False)]
    sequential = [a for a in plan["agents"] if not a.get("parallel", False)]

    print(f"Dispatching {len(parallel)} parallel agents, "
          f"{len(sequential)} sequential (handled by workflow needs: chain)",
          file=sys.stderr)

    for agent in parallel:
        wf = WORKFLOW_MAP.get(agent["role"])
        if wf:
            dispatch(repo, wf, {
                "task_id":    plan["task_id"],
                "role":       agent["role"],
                "input":      agent["input"],
                "depends_on": agent.get("depends_on", [])
            }, token)

    print("Done dispatching parallel agents.", file=sys.stderr)


if __name__ == "__main__":
    main()

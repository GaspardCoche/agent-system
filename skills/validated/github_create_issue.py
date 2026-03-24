#!/usr/bin/env python3
"""
Skill: github_create_issue
Remplace: mcp__github__create_issue
Validé le: 2026-03-24

Usage:
  python3 skills/validated/github_create_issue.py \
    --title "Bug: ..." \
    --body "Description..." \
    --label "bug" \
    --repo "owner/repo"

Variables d'env requises:
  GITHUB_TOKEN  (ou GH_TOKEN)

Sortie: JSON avec html_url, number
"""
import argparse
import json
import os
import sys

try:
    import requests
except ImportError:
    print("pip install requests", file=sys.stderr)
    sys.exit(1)


def create_issue(repo: str, title: str, body: str, labels: list[str]) -> dict:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN or GH_TOKEN not set", file=sys.stderr)
        sys.exit(1)

    resp = requests.post(
        f"https://api.github.com/repos/{repo}/issues",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={"title": title, "body": body, "labels": labels},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def comment_issue(repo: str, issue_number: int, body: str) -> dict:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN or GH_TOKEN not set", file=sys.stderr)
        sys.exit(1)

    resp = requests.post(
        f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={"body": body},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description="Create or comment on a GitHub issue")
    parser.add_argument("--title", required=True, help="Issue title")
    parser.add_argument("--body", default="", help="Issue body (markdown)")
    parser.add_argument("--label", action="append", default=[], dest="labels",
                        help="Label to add (repeatable)")
    parser.add_argument("--repo", help="owner/repo (defaults to GITHUB_REPOSITORY env)")
    parser.add_argument("--comment-on", type=int, help="Add a comment to existing issue number instead")
    args = parser.parse_args()

    repo = args.repo or os.environ.get("GITHUB_REPOSITORY", "")
    if not repo:
        print("Error: --repo or GITHUB_REPOSITORY required", file=sys.stderr)
        sys.exit(1)

    if args.comment_on:
        result = comment_issue(repo, args.comment_on, args.body)
        print(json.dumps({"ok": True, "comment_url": result.get("html_url"), "id": result.get("id")}, indent=2))
    else:
        result = create_issue(repo, args.title, args.body, args.labels)
        print(json.dumps({
            "ok": True,
            "number": result.get("number"),
            "html_url": result.get("html_url"),
            "title": result.get("title"),
        }, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Skill: slack_notify
Remplace: curl Slack dans les workflows
Validé le: 2026-03-24

Usage:
  python3 skills/validated/slack_notify.py \
    --message "✅ Scout terminé — 47 prospects enrichis" \
    --run-url "https://github.com/org/repo/actions/runs/12345"

  # Message formaté avec sections
  python3 skills/validated/slack_notify.py \
    --message "Rapport disponible" \
    --title "Nexus Weekly Audit" \
    --status "complete" \
    --next-actions "Configurer les enchères,Pauser les mots-clés faibles"

Variables d'env requises:
  SLACK_WEBHOOK_URL

Sortie: JSON avec ok
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


STATUS_EMOJI = {
    "complete": "✅",
    "success": "✅",
    "failed": "❌",
    "partial": "⚠️",
    "needs_retry": "🔄",
    "running": "⏳",
}


def send_notification(
    message: str,
    title: str = "",
    status: str = "",
    run_url: str = "",
    next_actions: list[str] = [],
) -> dict:
    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook:
        print("Warning: SLACK_WEBHOOK_URL not set — skipping", file=sys.stderr)
        return {"ok": False, "skipped": True}

    emoji = STATUS_EMOJI.get(status, "🤖")
    blocks = []

    # Header
    header_text = f"{emoji} *{title}*" if title else f"{emoji} {message}"
    blocks.append({
        "type": "section",
        "text": {"type": "mrkdwn", "text": header_text}
    })

    # Body message (if title was set separately)
    if title and message:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": message}
        })

    # Next actions
    if next_actions:
        actions_text = "\n".join(f"• {a}" for a in next_actions[:5])
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Actions à faire :*\n{actions_text}"}
        })

    # Footer with run link
    if run_url:
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"<{run_url}|Voir le run GitHub Actions>"}]
        })

    payload = {"blocks": blocks, "text": header_text}  # text = fallback for notifications

    resp = requests.post(webhook, json=payload, timeout=10)
    if resp.status_code == 200:
        return {"ok": True}
    else:
        return {"ok": False, "status": resp.status_code, "body": resp.text}


def main():
    parser = argparse.ArgumentParser(description="Send a Slack notification")
    parser.add_argument("--message", required=True, help="Main message text")
    parser.add_argument("--title", default="", help="Block header title (optional)")
    parser.add_argument("--status", default="", choices=list(STATUS_EMOJI.keys()) + [""],
                        help="Run status (influences emoji)")
    parser.add_argument("--run-url", default="", help="Link to GitHub Actions run")
    parser.add_argument("--next-action", action="append", default=[], dest="next_actions",
                        help="Next action item (repeatable, max 5)")
    args = parser.parse_args()

    result = send_notification(
        message=args.message,
        title=args.title,
        status=args.status,
        run_url=args.run_url,
        next_actions=args.next_actions,
    )
    print(json.dumps(result, indent=2))
    if not result.get("ok") and not result.get("skipped"):
        sys.exit(1)


if __name__ == "__main__":
    main()

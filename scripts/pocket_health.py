#!/usr/bin/env python3.12
"""Écrit pocket-data/health.json : santé des systèmes Pocket pour le panneau
de l'app. Vérifie l'auth Claude (résultat d'un run canari) + la présence des
secrets d'intégration. Pousse une alerte si le token est mort.

Usage: pocket_health.py --token-ok true|false [--exec-file PATH]
Env: GH_TOKEN, GITHUB_REPOSITORY ; HAS_<SYS>=1/0 pour la présence des secrets ;
     VAPID_PRIVATE_KEY/VAPID_SUBJECT (optionnel, pour l'alerte push).
Ne lève jamais (best-effort).
"""
import argparse
import base64
import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone

HEALTH_PATH = "pocket-data/health.json"
API = "https://api.github.com"
SYSTEMS = ["hubspot", "lemlist", "fullenrich", "phantombuster", "tavily",
           "firecrawl", "vault", "google_sa"]


def _req(method, url, token, data=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "pocket-health")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, json.loads(r.read().decode() or "{}")


def read_cost(path):
    try:
        data = json.load(open(path))
    except Exception:
        return 0.0
    events = data if isinstance(data, list) else [data]
    res = [e for e in events if isinstance(e, dict) and e.get("type") == "result"]
    return round(float(res[-1].get("total_cost_usd") or 0), 4) if res else 0.0


def get_sha(repo, token):
    try:
        _, data = _req("GET", f"{API}/repos/{repo}/contents/{HEALTH_PATH}", token)
        return data.get("sha")
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token-ok", required=True)
    ap.add_argument("--exec-file", default="/home/runner/work/_temp/claude-execution-output.json")
    args = ap.parse_args()

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        print("pocket_health: GH_TOKEN/GITHUB_REPOSITORY manquants", file=sys.stderr)
        return

    token_ok = args.token_ok.lower() == "true"
    secrets = {s: os.environ.get(f"HAS_{s.upper()}", "0") == "1" for s in SYSTEMS}

    health = {
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "token_ok": token_ok,
        "model": os.environ.get("CANARY_MODEL", ""),
        "cost_usd": read_cost(args.exec_file),
        "secrets": secrets,
    }
    content = base64.b64encode(json.dumps(health, indent=2).encode()).decode()
    body = {"message": "pocket: update health.json", "content": content}
    sha = get_sha(repo, token)
    if sha:
        body["sha"] = sha
    try:
        _req("PUT", f"{API}/repos/{repo}/contents/{HEALTH_PATH}", token, body)
        print(f"pocket_health: écrit (token_ok={token_ok})")
    except Exception as e:
        print(f"pocket_health: échec écriture {e}", file=sys.stderr)

    # Alerte push si le token est mort.
    if not token_ok and os.environ.get("VAPID_PRIVATE_KEY"):
        try:
            subprocess.run(
                ["python3", "scripts/pocket_push.py", "--title", "Claude Pocket ⚠️",
                 "--body", "Le token Claude est expiré/invalide — renouvelle-le pour réactiver l'agent.",
                 "--url", "./"],
                check=False, timeout=60)
        except Exception:
            pass


if __name__ == "__main__":
    main()

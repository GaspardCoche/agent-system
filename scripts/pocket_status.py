#!/usr/bin/env python3.12
"""Enregistre le résultat d'un run Pocket dans pocket-data/status.json (via
Contents API GitHub) : succès/échec, coût réel, durée, système, source.

C'est la source de vérité pour le panneau « Santé des systèmes » et le suivi
de coût de l'app. Lit le coût/durée/erreur depuis le JSON de sortie de
claude-code-action ; déduit le système depuis les labels cat:* de l'issue.

Usage: pocket_status.py --issue N [--exec-file PATH]
Env requis: GH_TOKEN, GITHUB_REPOSITORY. Ne lève jamais (best-effort).
"""
import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

EXEC_DEFAULT = "/home/runner/work/_temp/claude-execution-output.json"
STATUS_PATH = "pocket-data/status.json"
MAX_RECORDS = 60
API = "https://api.github.com"


def _req(method, url, token, data=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "pocket-status")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, json.loads(r.read().decode() or "{}")


def read_exec(path):
    """Retourne (ok, cost_usd, duration_s) depuis le flux d'événements."""
    try:
        with open(path) as f:
            data = json.load(f)
    except Exception:
        return False, 0.0, 0
    events = data if isinstance(data, list) else [data]
    results = [e for e in events if isinstance(e, dict) and e.get("type") == "result"]
    if not results:
        return False, 0.0, 0
    r = results[-1]
    ok = not r.get("is_error")
    cost = round(float(r.get("total_cost_usd") or 0), 4)
    dur = round(float(r.get("duration_ms") or 0) / 1000, 1)
    return ok, cost, dur


def derive_system_source(repo, issue, token):
    system, source = "other", "phone"
    try:
        _, data = _req("GET", f"{API}/repos/{repo}/issues/{issue}", token)
        names = [l.get("name", "") for l in data.get("labels", [])]
        for n in names:
            if n.startswith("cat:"):
                system = n[4:]
                break
        if "via:phone" in names:
            source = "phone"
        elif any(n == "scheduled" for n in names):
            source = "scheduled"
    except Exception:
        pass
    return system, source


def load_status(repo, token):
    """Retourne (records, sha) ; sha=None si le fichier n'existe pas."""
    try:
        _, data = _req("GET", f"{API}/repos/{repo}/contents/{STATUS_PATH}", token)
        content = base64.b64decode(data.get("content", "")).decode()
        obj = json.loads(content)
        return obj.get("runs", []), data.get("sha")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return [], None
        raise
    except Exception:
        return [], None


def save_status(repo, token, runs, sha):
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runs": runs[-MAX_RECORDS:],
    }
    content = base64.b64encode(json.dumps(payload, indent=2).encode()).decode()
    body = {"message": "pocket: update status.json", "content": content}
    if sha:
        body["sha"] = sha
    _req("PUT", f"{API}/repos/{repo}/contents/{STATUS_PATH}", token, body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--issue", required=True)
    ap.add_argument("--exec-file", default=EXEC_DEFAULT)
    args = ap.parse_args()

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        print("pocket_status: GH_TOKEN/GITHUB_REPOSITORY manquants", file=sys.stderr)
        return

    ok, cost, dur = read_exec(args.exec_file)
    system, source = derive_system_source(repo, args.issue, token)
    record = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "issue": int(args.issue) if str(args.issue).isdigit() else args.issue,
        "system": system,
        "source": source,
        "ok": ok,
        "cost_usd": cost,
        "duration_s": dur,
    }

    # Retry sur conflit 409 (runs concurrents) : recharge le sha et réessaie.
    for attempt in range(3):
        try:
            runs, sha = load_status(repo, token)
            runs.append(record)
            save_status(repo, token, runs, sha)
            print(f"pocket_status: enregistré {record}")
            return
        except urllib.error.HTTPError as e:
            if e.code == 409 and attempt < 2:
                time.sleep(1 + attempt)
                continue
            print(f"pocket_status: échec HTTP {e.code}", file=sys.stderr)
            return
        except Exception as e:
            print(f"pocket_status: {e}", file=sys.stderr)
            return


if __name__ == "__main__":
    main()

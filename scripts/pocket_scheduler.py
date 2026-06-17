#!/usr/bin/env python3.12
"""Planificateur Claude Pocket : déclenche les modes programmés.

Lit pocket-schedules/*.json. Pour le 1er planning « dû » dans la fenêtre courante
(tz Europe/Brussels par défaut), crée une issue Pocket (label pocket) via l'API,
écrit /tmp/agent_task.json, et signale `fired` au workflow (qui lance l'agent inline).
Met à jour last_fired (dédup : un déclenchement max par jour et par planning).

Env requis : GITHUB_REPOSITORY, GH_TOKEN. Écrit dans GITHUB_OUTPUT : fired, issue.
"""
import os, json, glob, datetime, urllib.request
from zoneinfo import ZoneInfo

REPO = os.environ["GITHUB_REPOSITORY"]
TOKEN = os.environ["GH_TOKEN"]
OUT = os.environ.get("GITHUB_OUTPUT", "/dev/stdout")


def create_issue(title, body):
    data = json.dumps({"title": title, "body": body, "labels": ["pocket"]}).encode()
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/issues", data=data, method="POST")
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())["number"]


def is_due(s, now):
    if not s.get("enabled"):
        return False
    if s.get("freq") == "weekly" and now.weekday() != int(s.get("weekday", 0)):
        return False
    target = now.replace(hour=int(s["hour"]), minute=int(s.get("minute", 0)), second=0, microsecond=0)
    delta = (now - target).total_seconds()
    if not (0 <= delta < 70 * 60):  # fenêtre de 70 min (cron horaire + retards GitHub)
        return False
    if (s.get("last_fired", "") or "").startswith(now.strftime("%Y-%m-%d")):
        return False  # déjà déclenché aujourd'hui
    return True


def main():
    fired = None
    for f in sorted(glob.glob("pocket-schedules/*.json")):
        try:
            s = json.load(open(f))
        except Exception:
            continue
        now = datetime.datetime.now(ZoneInfo(s.get("tz", "Europe/Brussels")))
        if is_due(s, now):
            body = f"### Demande\n\n{s['demande']}\n\n### Autoriser l'écriture ?\n\nnon\n\n### Mode\n\n{s['mode']}"
            num = create_issue(f"[Pocket] ⏰ {s.get('name', s['mode'])}", body)
            s["last_fired"] = now.isoformat()
            json.dump(s, open(f, "w"), indent=2, ensure_ascii=False)
            json.dump({"source": "pocket-schedule", "issue_number": str(num), "description": body,
                       "approved": False, "is_followup": False, "latest_message": ""},
                      open("/tmp/agent_task.json", "w"))
            fired = num
            break  # un seul déclenchement par tick (les autres suivront au tick suivant)

    with open(OUT, "a") as o:
        o.write(f"fired={'true' if fired else 'false'}\n")
        if fired:
            o.write(f"issue={fired}\n")
    print("fired:", fired)


if __name__ == "__main__":
    main()

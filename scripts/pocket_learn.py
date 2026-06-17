#!/usr/bin/env python3.12
"""Enregistre un apprentissage durable dans la mémoire d'expertise de Pocket.

Ajoute une puce datée à pocket-knowledge/<domaine>.md via l'API Contents
(robuste, pas de git push). Dédup simple. Env : GH_TOKEN, GITHUB_REPOSITORY.

Usage : pocket_learn.py <domaine> "<apprentissage concis>"
  domaines : crm | web | vault | enrich | outreach | code | other
"""
import os, sys, json, base64, datetime, urllib.request, urllib.error

REPO = os.environ.get("GITHUB_REPOSITORY", "")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN", "")
VALID = {"crm", "web", "vault", "enrich", "outreach", "code", "other"}


def api(method, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}{path}", data=data, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, {}


def main():
    if len(sys.argv) < 3 or not TOKEN or not REPO:
        print("usage: pocket_learn.py <domaine> \"<apprentissage>\" (et env GH_TOKEN/GITHUB_REPOSITORY)")
        return
    domain = sys.argv[1].strip().lower()
    if domain not in VALID:
        domain = "other"
    learning = " ".join(sys.argv[2:]).strip().replace("\n", " ")
    if len(learning) < 5:
        print("trop court — ignoré")
        return
    path = f"pocket-knowledge/{domain}.md"
    st, cur = api("GET", f"/contents/{path}")
    if st == 200:
        content = base64.b64decode(cur["content"]).decode("utf-8", "ignore")
        sha = cur.get("sha")
    else:
        content = f"# Expertise {domain} — appris par Pocket\n"
        sha = None
    if learning.lower() in content.lower():
        print("déjà connu — ignoré")
        return
    bullet = f"- ({datetime.date.today().isoformat()}) {learning}\n"
    new = content.rstrip("\n") + "\n" + bullet
    body = {"message": f"knowledge: {domain}", "content": base64.b64encode(new.encode()).decode()}
    if sha:
        body["sha"] = sha
    st2, _ = api("PUT", f"/contents/{path}", body)
    print("enregistré" if st2 in (200, 201) else f"échec PUT {st2}")


if __name__ == "__main__":
    main()

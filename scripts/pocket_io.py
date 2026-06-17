#!/usr/bin/env python3.12
"""Helper Pocket : écrit un output (CSV/texte) dans pocket-data/outputs/ via l'API
Contents GitHub et renvoie l'URL raw (téléchargeable depuis l'app). Env : GITHUB_REPOSITORY, GH_TOKEN."""
import os, json, base64, csv, io, urllib.request, urllib.error


def _api(method, path, payload=None):
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN", "")
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}{path}", data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, json.loads(r.read() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, {}


def save_text(name, text):
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    path = f"pocket-data/outputs/{name}"
    st, cur = _api("GET", f"/contents/{path}")
    body = {"message": f"pocket: output {name}", "content": base64.b64encode(text.encode()).decode()}
    if st == 200 and cur.get("sha"):
        body["sha"] = cur["sha"]
    st2, _ = _api("PUT", f"/contents/{path}", body)
    return f"https://raw.githubusercontent.com/{repo}/main/{path}" if st2 in (200, 201) else None


def rows_to_csv(rows, columns=None):
    if not rows:
        return "(vide)\n"
    if not columns:
        columns = []
        for r in rows:
            for k in r.keys():
                if k not in columns:
                    columns.append(k)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({c: r.get(c, "") for c in columns})
    return buf.getvalue()


def save_csv(name, rows, columns=None):
    return save_text(name, rows_to_csv(rows, columns))

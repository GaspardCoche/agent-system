#!/usr/bin/env python3.12
"""Accès en LECTURE au vault Obsidian privé (GaspardCoche/claude-knowledge-vault).

Clone le vault via une clé de déploiement read-only (secret VAULT_DEPLOY_KEY),
en cache dans /tmp/kvault. Recherche plein-texte + lecture de notes markdown.

Usage :
  pocket_vault.py search "<requête>" [--limit 6]
  pocket_vault.py read "<chemin/relatif.md>"
  pocket_vault.py list ["<sous-dossier>"]
"""
import os, sys, json, argparse, subprocess, glob

REPO_SSH = os.environ.get("VAULT_REPO_SSH", "git@github.com:GaspardCoche/claude-knowledge-vault.git")
DIR = "/tmp/kvault"


def ensure_clone():
    if os.path.isdir(os.path.join(DIR, ".git")):
        return None
    key = os.environ.get("VAULT_DEPLOY_KEY", "").strip()
    if not key:
        return "VAULT_DEPLOY_KEY absent — accès vault indisponible."
    kp = "/tmp/vault_key"
    with open(kp, "w") as f:
        f.write(key + "\n")
    os.chmod(kp, 0o600)
    env = dict(os.environ)
    env["GIT_SSH_COMMAND"] = f"ssh -i {kp} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    r = subprocess.run(["git", "clone", "--depth", "1", REPO_SSH, DIR],
                       env=env, capture_output=True, text=True)
    if r.returncode != 0:
        return f"Échec clone vault : {r.stderr.strip()[:300]}"
    return None


def md_files():
    return [p for p in glob.glob(f"{DIR}/**/*.md", recursive=True) if "/.git/" not in p]


def cmd_search(a):
    err = ensure_clone()
    if err:
        return {"error": err}
    terms = [t.lower() for t in a.query.split() if t]
    results = []
    for p in md_files():
        try:
            txt = open(p, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        low = txt.lower()
        if all(t in low for t in terms):
            score = sum(low.count(t) for t in terms)
            idx = low.find(terms[0]) if terms else 0
            snippet = txt[max(0, idx - 80):idx + 220].replace("\n", " ").strip()
            results.append({"file": os.path.relpath(p, DIR), "score": score, "snippet": snippet})
    results.sort(key=lambda x: -x["score"])
    return {"query": a.query, "matches": len(results), "results": results[: a.limit]}


def cmd_read(a):
    err = ensure_clone()
    if err:
        return {"error": err}
    path = os.path.normpath(os.path.join(DIR, a.path))
    if not path.startswith(DIR) or not os.path.isfile(path):
        return {"error": f"Fichier introuvable : {a.path}"}
    txt = open(path, encoding="utf-8", errors="ignore").read()
    return {"file": a.path, "truncated": len(txt) > 8000, "content": txt[:8000]}


def cmd_list(a):
    err = ensure_clone()
    if err:
        return {"error": err}
    base = os.path.join(DIR, a.subdir) if a.subdir else DIR
    files = [os.path.relpath(p, DIR) for p in glob.glob(f"{base}/**/*.md", recursive=True) if "/.git/" not in p]
    return {"count": len(files), "files": sorted(files)[:200]}


def main():
    p = argparse.ArgumentParser(prog="pocket_vault")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search"); s.add_argument("query"); s.add_argument("--limit", type=int, default=6); s.set_defaults(fn=cmd_search)
    r = sub.add_parser("read"); r.add_argument("path"); r.set_defaults(fn=cmd_read)
    l = sub.add_parser("list"); l.add_argument("subdir", nargs="?", default=""); l.set_defaults(fn=cmd_list)
    a = p.parse_args()
    print(json.dumps(a.fn(a), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

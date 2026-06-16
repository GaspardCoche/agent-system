#!/usr/bin/env python3.12
"""Outil PhantomBuster déterministe pour Claude Pocket (API v2).

Token : env PHANTOMBUSTER_API_KEY (header X-Phantombuster-Key).
LECTURE (agents/agent/containers/output/result) libre.
LANCEMENT (launch) = scraping réel → exige --confirm (après approbation `approved`).

Usage :
  pocket_phantombuster.py agents                      # liste les phantoms
  pocket_phantombuster.py agent <agentId>             # détail d'un phantom
  pocket_phantombuster.py containers <agentId>        # exécutions d'un phantom
  pocket_phantombuster.py output <containerId>        # logs d'une exécution
  pocket_phantombuster.py result <containerId>        # résultat JSON d'une exécution
  pocket_phantombuster.py launch <agentId> [--argument-file args.json] --confirm
"""
import sys, os, json, argparse, urllib.request, urllib.error, urllib.parse

BASE = "https://api.phantombuster.com/api/v2"


def _hdrs():
    t = os.environ.get("PHANTOMBUSTER_API_KEY", "").strip()
    if not t:
        print(json.dumps({"error": "PHANTOMBUSTER_API_KEY absent de l'environnement"}))
        sys.exit(2)
    return {"X-Phantombuster-Key": t, "Content-Type": "application/json"}


def _req(method, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(f"{BASE}/{path}", data=data, method=method, headers=_hdrs())
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            txt = r.read().decode()
            try:
                return r.status, json.loads(txt or "{}")
            except Exception:
                return r.status, {"raw": txt[:4000]}
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            body = json.loads(body)
        except Exception:
            pass
        return e.code, {"http_error": e.code, "body": body}


def cmd_agents(a):
    return _req("GET", "agents/fetch-all")[1]


def cmd_agent(a):
    return _req("GET", f"agents/fetch?id={urllib.parse.quote(a.agentId)}")[1]


def cmd_containers(a):
    return _req("GET", f"containers/fetch-all?agentId={urllib.parse.quote(a.agentId)}")[1]


def cmd_output(a):
    return _req("GET", f"containers/fetch-output?id={urllib.parse.quote(a.containerId)}")[1]


def cmd_result(a):
    return _req("GET", f"containers/fetch-result-object?id={urllib.parse.quote(a.containerId)}")[1]


def cmd_launch(a):
    if not a.confirm:
        return {"dry_run": True, "would_launch_agent": a.agentId,
                "note": "Scraping réel — relancer avec --confirm (après approbation)."}
    payload = {"id": a.agentId}
    if a.argument_file:
        payload["argument"] = json.load(open(a.argument_file))
    return _req("POST", "agents/launch", payload)[1]


def main():
    p = argparse.ArgumentParser(prog="pocket_phantombuster")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("agents").set_defaults(fn=cmd_agents)
    g = sub.add_parser("agent"); g.add_argument("agentId"); g.set_defaults(fn=cmd_agent)
    c = sub.add_parser("containers"); c.add_argument("agentId"); c.set_defaults(fn=cmd_containers)
    o = sub.add_parser("output"); o.add_argument("containerId"); o.set_defaults(fn=cmd_output)
    r = sub.add_parser("result"); r.add_argument("containerId"); r.set_defaults(fn=cmd_result)
    l = sub.add_parser("launch"); l.add_argument("agentId"); l.add_argument("--argument-file", dest="argument_file", default=""); l.add_argument("--confirm", action="store_true"); l.set_defaults(fn=cmd_launch)

    a = p.parse_args()
    print(json.dumps(a.fn(a), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

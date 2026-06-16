#!/usr/bin/env python3.12
"""Outil HubSpot déterministe pour Claude Pocket.

Lit le token depuis l'env HUBSPOT_PRIVATE_APP_TOKEN (Private App).
Appelle directement l'API REST HubSpot (stdlib, pas de MCP).
LECTURE par défaut ; les écritures exigent --confirm (le runner ne l'ajoute
que si le label `approved` est présent).

Usage :
  pocket_hubspot.py count <objectType> <property> <value>
      ex : count contacts lifecyclestage lead
  pocket_hubspot.py search <objectType> <property> <value> [--limit N] [--props a,b,c]
  pocket_hubspot.py read <objectType> <id> [--props a,b,c]
  pocket_hubspot.py whoami           # vérifie le token (token-details)
"""
import sys, os, json, argparse, urllib.request, urllib.error

BASE = "https://api.hubapi.com"


def _token() -> str:
    t = os.environ.get("HUBSPOT_PRIVATE_APP_TOKEN", "").strip()
    if not t:
        print(json.dumps({"error": "HUBSPOT_PRIVATE_APP_TOKEN absent de l'environnement"}))
        sys.exit(2)
    return t


def _req(method: str, path: str, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Authorization", f"Bearer {_token()}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            body = json.loads(body)
        except Exception:
            pass
        return e.code, {"http_error": e.code, "body": body}


def _search(object_type, prop, value, limit=10, props=None):
    payload = {
        "filterGroups": [{"filters": [{"propertyName": prop, "operator": "EQ", "value": value}]}],
        "limit": min(int(limit), 100),
    }
    if props:
        payload["properties"] = props
    return _req("POST", f"/crm/v3/objects/{object_type}/search", payload)


def cmd_count(a):
    status, body = _search(a.objectType, a.property, a.value, limit=1)
    if status != 200:
        return body
    return {"objectType": a.objectType, "filter": f"{a.property}={a.value}", "total": body.get("total")}


def cmd_search(a):
    props = a.props.split(",") if a.props else None
    status, body = _search(a.objectType, a.property, a.value, limit=a.limit, props=props)
    if status != 200:
        return body
    return {
        "total": body.get("total"),
        "results": [{"id": r["id"], **r.get("properties", {})} for r in body.get("results", [])],
    }


def cmd_read(a):
    qs = f"?properties={a.props}" if a.props else ""
    status, body = _req("GET", f"/crm/v3/objects/{a.objectType}/{a.id}{qs}")
    return body if status == 200 else body


def cmd_whoami(a):
    status, body = _req("GET", f"/oauth/v1/private-apps/v3/token-info")
    if status != 200:
        # endpoint alternatif : un simple appel authentifié
        status, body = _req("GET", "/crm/v3/objects/contacts?limit=1")
        return {"auth_ok": status == 200, "status": status}
    return body


def main():
    p = argparse.ArgumentParser(prog="pocket_hubspot")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("count"); c.add_argument("objectType"); c.add_argument("property"); c.add_argument("value"); c.set_defaults(fn=cmd_count)
    s = sub.add_parser("search"); s.add_argument("objectType"); s.add_argument("property"); s.add_argument("value"); s.add_argument("--limit", default=10); s.add_argument("--props", default=""); s.set_defaults(fn=cmd_search)
    r = sub.add_parser("read"); r.add_argument("objectType"); r.add_argument("id"); r.add_argument("--props", default=""); r.set_defaults(fn=cmd_read)
    w = sub.add_parser("whoami"); w.set_defaults(fn=cmd_whoami)

    a = p.parse_args()
    print(json.dumps(a.fn(a), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

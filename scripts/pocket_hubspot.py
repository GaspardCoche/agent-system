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
        status, body = _req("GET", "/crm/v3/objects/contacts?limit=1")
        return {"auth_ok": status == 200, "status": status}
    return body


def cmd_describe(a):
    """Propriétés d'un objet (contacts/companies/deals…) — pour comprendre l'objet."""
    status, body = _req("GET", f"/crm/v3/properties/{a.objectType}")
    if status != 200:
        return body
    props = [{"name": p["name"], "label": p.get("label"), "type": p.get("type")} for p in body.get("results", [])]
    return {"objectType": a.objectType, "nb_propriétés": len(props), "propriétés": props[: a.limit]}


def cmd_lists(a):
    """Liste les listes/segments HubSpot (recherche)."""
    status, body = _req("POST", "/crm/v3/lists/search", {"query": a.query, "count": 50})
    if status != 200:
        return body
    return {"lists": [{"listId": l.get("listId"), "name": l.get("name"), "size": l.get("size"), "type": l.get("processingType")} for l in body.get("lists", [])]}


def _list_member_ids(list_id, limit=200):
    ids, after = [], None
    while len(ids) < limit:
        qs = f"?limit=100" + (f"&after={after}" if after else "")
        status, body = _req("GET", f"/crm/v3/lists/{list_id}/memberships{qs}")
        if status != 200:
            break
        ids += [r.get("recordId") for r in body.get("results", [])]
        after = (body.get("paging", {}).get("next") or {}).get("after")
        if not after:
            break
    return ids[:limit]


def _batch_read(object_type, ids, props):
    rows = []
    for i in range(0, len(ids), 100):
        chunk = ids[i:i + 100]
        status, body = _req("POST", f"/crm/v3/objects/{object_type}/batch/read",
                            {"properties": props, "inputs": [{"id": str(x)} for x in chunk]})
        if status == 200:
            rows += [{"id": r["id"], **r.get("properties", {})} for r in body.get("results", [])]
    return rows


def cmd_list_members(a):
    """Membres d'une liste HubSpot (pour enrichir un segment)."""
    ids = _list_member_ids(a.listId, limit=int(a.limit))
    props = (a.props.split(",") if a.props else ["email", "firstname", "lastname", "company", "jobtitle"])
    rows = _batch_read("contacts", ids, props)
    return {"listId": a.listId, "membres": len(rows), "results": rows}


def cmd_export(a):
    """Recherche un segment et écrit un CSV téléchargeable."""
    import sys as _s, os as _o
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    from pocket_io import save_csv
    props = a.props.split(",") if a.props else ["email", "firstname", "lastname", "company"]
    status, body = _search(a.objectType, a.property, a.value, limit=int(a.limit), props=props)
    if status != 200:
        return body
    rows = [{"id": r["id"], **r.get("properties", {})} for r in body.get("results", [])]
    url = save_csv(f"hubspot-{a.objectType}-{a.property}-{a.value}.csv".replace(" ", "_")[:60], rows, ["id"] + props)
    return {"total": body.get("total"), "exporté": len(rows), "csv_url": url or "(échec écriture)"}


def cmd_export_list(a):
    import sys as _s, os as _o
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    from pocket_io import save_csv
    ids = _list_member_ids(a.listId, limit=int(a.limit))
    props = (a.props.split(",") if a.props else ["email", "firstname", "lastname", "company", "jobtitle"])
    rows = _batch_read("contacts", ids, props)
    url = save_csv(f"hubspot-list-{a.listId}.csv", rows, ["id"] + props)
    return {"listId": a.listId, "membres": len(rows), "csv_url": url or "(échec écriture)"}


def main():
    p = argparse.ArgumentParser(prog="pocket_hubspot")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("count"); c.add_argument("objectType"); c.add_argument("property"); c.add_argument("value"); c.set_defaults(fn=cmd_count)
    s = sub.add_parser("search"); s.add_argument("objectType"); s.add_argument("property"); s.add_argument("value"); s.add_argument("--limit", default=10); s.add_argument("--props", default=""); s.set_defaults(fn=cmd_search)
    r = sub.add_parser("read"); r.add_argument("objectType"); r.add_argument("id"); r.add_argument("--props", default=""); r.set_defaults(fn=cmd_read)
    w = sub.add_parser("whoami"); w.set_defaults(fn=cmd_whoami)
    d = sub.add_parser("describe"); d.add_argument("objectType"); d.add_argument("--limit", type=int, default=60); d.set_defaults(fn=cmd_describe)
    li = sub.add_parser("lists"); li.add_argument("query", nargs="?", default=""); li.set_defaults(fn=cmd_lists)
    lm = sub.add_parser("list-members"); lm.add_argument("listId"); lm.add_argument("--limit", default=200); lm.add_argument("--props", default=""); lm.set_defaults(fn=cmd_list_members)
    ex = sub.add_parser("export"); ex.add_argument("objectType"); ex.add_argument("property"); ex.add_argument("value"); ex.add_argument("--limit", default=100); ex.add_argument("--props", default=""); ex.set_defaults(fn=cmd_export)
    el = sub.add_parser("export-list"); el.add_argument("listId"); el.add_argument("--limit", default=200); el.add_argument("--props", default=""); el.set_defaults(fn=cmd_export_list)

    a = p.parse_args()
    print(json.dumps(a.fn(a), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3.12
"""Outil FullEnrich déterministe pour Claude Pocket (API v2, flux bulk async).

Token : env FULLENRICH_API_KEY (Bearer).
LECTURE (status) libre. SOUMISSION (submit/enrich-one) consomme des crédits →
exige --confirm (le runner/l'agent ne l'ajoute qu'après approbation `approved`).

Usage :
  pocket_fullenrich.py status <enrichment_id>
  pocket_fullenrich.py enrich-one --firstname F --lastname L --domain D
        [--linkedin URL] [--phones] [--hubspot-id ID] --confirm
  pocket_fullenrich.py submit --file contacts.json [--name NAME] [--phones] --confirm
      (contacts.json = liste de dicts : firstname,lastname,domain|company_name,linkedin_url,custom)

Garde-fous : max 100/batch ; `contact_info.phones` seulement avec --phones
(coûte plus cher) ; minimum par contact = (firstname+lastname+domain) OU linkedin_url.
"""
import sys, os, json, argparse, urllib.request, urllib.error

BASE = "https://app.fullenrich.com/api/v2"


def _hdrs():
    t = os.environ.get("FULLENRICH_API_KEY", "").strip()
    if not t:
        print(json.dumps({"error": "FULLENRICH_API_KEY absent de l'environnement"}))
        sys.exit(2)
    return {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}


def _req(method, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=_hdrs())
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            body = json.loads(body)
        except Exception:
            pass
        return e.code, {"http_error": e.code, "body": body}


def _enrich_fields(phones):
    fields = ["contact_info.emails"]
    if phones:
        fields.append("contact_info.phones")
    return fields


def _validate(contacts):
    for i, c in enumerate(contacts):
        has_name = c.get("firstname") and c.get("lastname") and (c.get("domain") or c.get("company_name"))
        if not (has_name or c.get("linkedin_url")):
            return f"contact #{i} invalide : il faut (firstname+lastname+domain/company_name) OU linkedin_url"
    if len(contacts) > 100:
        return f"{len(contacts)} contacts > 100 max par batch"
    return None


def cmd_status(a):
    status, body = _req("GET", f"/contact/enrich/bulk/{a.enrichment_id}")
    return body


def cmd_submit(a, contacts=None, name=None):
    if contacts is None:
        contacts = json.load(open(a.file))
    err = _validate(contacts)
    if err:
        return {"error": err}
    if not a.confirm:
        return {"dry_run": True, "would_submit": len(contacts), "phones": bool(a.phones),
                "note": "Action consommant des crédits — relancer avec --confirm (après approbation)."}
    fields = _enrich_fields(a.phones)
    for c in contacts:
        c.setdefault("enrich_fields", fields)
    payload = {"name": name or getattr(a, "name", None) or "pocket-batch", "datas": contacts}
    status, body = _req("POST", "/contact/enrich/bulk", payload)
    return body


def cmd_enrich_one(a):
    c = {"firstname": a.firstname, "lastname": a.lastname}
    if a.domain:
        c["domain"] = a.domain
    if a.linkedin:
        c["linkedin_url"] = a.linkedin
    if a.hubspot_id:
        c["custom"] = {"hubspot_contact_id": a.hubspot_id}
    return cmd_submit(a, contacts=[c], name=f"pocket-{a.lastname}")


def cmd_results_csv(a):
    import sys as _s, os as _o
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    from pocket_io import save_csv
    status, body = _req("GET", f"/contact/enrich/bulk/{a.enrichment_id}")
    if status != 200:
        return body
    datas = body.get("datas") or body.get("results") or body.get("contacts") or []

    def _first(lst, *keys):
        for x in (lst or []):
            if isinstance(x, dict):
                for k in keys:
                    if x.get(k):
                        return x[k]
            elif x:
                return x
        return ""

    rows = []
    for d in datas:
        c = d.get("contact") or d
        ci = d.get("contact_info") or d.get("enrichment") or {}
        emails = ci.get("emails") or d.get("emails") or []
        phones = ci.get("phones") or d.get("phones") or []
        rows.append({
            "firstname": c.get("firstname", ""), "lastname": c.get("lastname", ""),
            "domain": c.get("domain", "") or c.get("company_name", ""),
            "email": _first(emails, "email", "value", "address"),
            "phone": _first(phones, "number", "value", "phone"),
            "linkedin": c.get("linkedin_url", ""),
            "hubspot_contact_id": (c.get("custom") or {}).get("hubspot_contact_id", ""),
        })
    cols = ["firstname", "lastname", "domain", "email", "phone", "linkedin", "hubspot_contact_id"]
    url = save_csv(f"fullenrich-{a.enrichment_id}.csv", rows, cols)
    return {"status": body.get("status"), "lignes": len(rows),
            "csv_url": url or "(échec écriture — GH_TOKEN/GITHUB_REPOSITORY ?)"}


def main():
    p = argparse.ArgumentParser(prog="pocket_fullenrich")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("status"); s.add_argument("enrichment_id"); s.set_defaults(fn=cmd_status)
    rc = sub.add_parser("results-csv"); rc.add_argument("enrichment_id"); rc.set_defaults(fn=cmd_results_csv)

    e = sub.add_parser("enrich-one")
    e.add_argument("--firstname", required=True); e.add_argument("--lastname", required=True)
    e.add_argument("--domain", default=""); e.add_argument("--linkedin", default="")
    e.add_argument("--hubspot-id", dest="hubspot_id", default="")
    e.add_argument("--phones", action="store_true"); e.add_argument("--confirm", action="store_true")
    e.set_defaults(fn=cmd_enrich_one)

    b = sub.add_parser("submit")
    b.add_argument("--file", required=True); b.add_argument("--name", default="")
    b.add_argument("--phones", action="store_true"); b.add_argument("--confirm", action="store_true")
    b.set_defaults(fn=cmd_submit)

    a = p.parse_args()
    print(json.dumps(a.fn(a), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

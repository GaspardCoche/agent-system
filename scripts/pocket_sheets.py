#!/usr/bin/env python3.12
"""Pilotage Google Sheets pour Pocket.

LECTURE / EXPORT : via l'export CSV public (aucune auth) — marche sur les sheets
publics ou « accessibles avec le lien ».
ÉCRITURE / APPEND : via un compte de service (secret GOOGLE_SA_JSON, partager le
sheet avec l'email du SA). Gaté par --confirm.

Usage :
  pocket_sheets.py read <sheetId> [--gid 0] [--limit 50]
  pocket_sheets.py export <sheetId> [--gid 0]           -> CSV téléchargeable
  pocket_sheets.py append <sheetId> <onglet> --row "a,b,c" --confirm
  pocket_sheets.py write <sheetId> <range> --values-file rows.json --confirm
"""
import os, sys, json, csv, io, argparse, urllib.request, urllib.parse, urllib.error


def _csv_export(sheet_id, gid):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            data = r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code} (sheet privé ? partage-le ou rends-le accessible avec le lien)"
    if data.lstrip().lower().startswith("<!doctype html") or "<html" in data[:200].lower():
        return None, "Sheet non public — partage-le 'avec le lien' ou avec le compte de service."
    return data, None


def cmd_read(a):
    data, err = _csv_export(a.sheetId, a.gid)
    if err:
        return {"error": err}
    rows = list(csv.reader(io.StringIO(data)))
    return {"sheetId": a.sheetId, "gid": a.gid, "lignes": len(rows), "aperçu": rows[: a.limit]}


def cmd_export(a):
    import sys as _s, os as _o
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    from pocket_io import save_text
    data, err = _csv_export(a.sheetId, a.gid)
    if err:
        return {"error": err}
    url = save_text(f"sheet-{a.sheetId}-{a.gid}.csv", data)
    return {"sheetId": a.sheetId, "csv_url": url or "(échec écriture)"}


def _sa_token(scope):
    raw = os.environ.get("GOOGLE_SA_JSON", "").strip()
    if not raw:
        return None, "GOOGLE_SA_JSON absent (ajoute le JSON du compte de service en secret)."
    try:
        sa = json.loads(raw)
        import time, base64
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding
        except ImportError:
            import subprocess
            subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "cryptography"], check=False)
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding

        def b64u(b):
            return base64.urlsafe_b64encode(b).rstrip(b"=").decode()
        now = int(time.time())
        head = b64u(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
        claim = b64u(json.dumps({"iss": sa["client_email"], "scope": scope,
                                 "aud": "https://oauth2.googleapis.com/token", "iat": now, "exp": now + 3600}).encode())
        key = serialization.load_pem_private_key(sa["private_key"].encode(), password=None)
        sig = b64u(key.sign(f"{head}.{claim}".encode(), padding.PKCS1v15(), hashes.SHA256()))
        assertion = f"{head}.{claim}.{sig}"
        body = urllib.parse.urlencode({"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": assertion}).encode()
        with urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", data=body), timeout=30) as r:
            return json.loads(r.read())["access_token"], None
    except Exception as e:
        return None, f"Auth compte de service échouée : {e}"


def _sheets_api(method, path, token, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(f"https://sheets.googleapis.com/v4/spreadsheets/{path}", data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()[:300]}


def cmd_append(a):
    if not a.confirm:
        return {"dry_run": True, "note": "Écriture réelle — relancer avec --confirm (après approbation)."}
    token, err = _sa_token("https://www.googleapis.com/auth/spreadsheets")
    if err:
        return {"error": err}
    row = [c.strip() for c in a.row.split(",")]
    rng = urllib.parse.quote(a.tab)
    st, body = _sheets_api("POST", f"{a.sheetId}/values/{rng}:append?valueInputOption=USER_ENTERED", token, {"values": [row]})
    return body if st == 200 else {"error": body}


def cmd_write(a):
    if not a.confirm:
        return {"dry_run": True, "note": "Écriture réelle — relancer avec --confirm (après approbation)."}
    token, err = _sa_token("https://www.googleapis.com/auth/spreadsheets")
    if err:
        return {"error": err}
    values = json.load(open(a.values_file))
    rng = urllib.parse.quote(a.range)
    st, body = _sheets_api("PUT", f"{a.sheetId}/values/{rng}?valueInputOption=USER_ENTERED", token, {"values": values})
    return body if st == 200 else {"error": body}


def main():
    p = argparse.ArgumentParser(prog="pocket_sheets")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("read"); r.add_argument("sheetId"); r.add_argument("--gid", default="0"); r.add_argument("--limit", type=int, default=50); r.set_defaults(fn=cmd_read)
    e = sub.add_parser("export"); e.add_argument("sheetId"); e.add_argument("--gid", default="0"); e.set_defaults(fn=cmd_export)
    ap = sub.add_parser("append"); ap.add_argument("sheetId"); ap.add_argument("tab"); ap.add_argument("--row", required=True); ap.add_argument("--confirm", action="store_true"); ap.set_defaults(fn=cmd_append)
    wr = sub.add_parser("write"); wr.add_argument("sheetId"); wr.add_argument("range"); wr.add_argument("--values-file", dest="values_file", required=True); wr.add_argument("--confirm", action="store_true"); wr.set_defaults(fn=cmd_write)
    a = p.parse_args()
    print(json.dumps(a.fn(a), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

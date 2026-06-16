#!/usr/bin/env python3.12
"""Envoie une notification Web Push aux appareils abonnés (Claude Pocket).

Lit les abonnements dans pocket-data/sub-*.json (écrits par la PWA).
Signe avec la clé VAPID privée (secret GitHub VAPID_PRIVATE_KEY, format PEM).
Sans abonné ou sans clé → ne fait rien (silencieux, ne plante pas).

Usage : pocket_push.py --title T --body B [--url ./]
"""
import os, json, glob, argparse


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--body", required=True)
    ap.add_argument("--url", default="./")
    a = ap.parse_args()

    pem = os.environ.get("VAPID_PRIVATE_KEY", "").strip()
    subject = os.environ.get("VAPID_SUBJECT", "mailto:admin@example.com").strip()
    if not pem:
        print("VAPID_PRIVATE_KEY absent — pas de notification.")
        return

    subs = glob.glob("pocket-data/sub-*.json")
    if not subs:
        print("Aucun appareil abonné aux notifications.")
        return

    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        print("pywebpush non installé — notification ignorée.")
        return

    with open("/tmp/vapid.pem", "w") as f:
        f.write(pem)
    payload = json.dumps({"title": a.title, "body": a.body, "url": a.url, "tag": "pocket"})

    sent = 0
    for path in subs:
        try:
            info = json.load(open(path))
            webpush(subscription_info=info, data=payload,
                    vapid_private_key="/tmp/vapid.pem", vapid_claims={"sub": subject})
            sent += 1
        except WebPushException as e:
            code = getattr(getattr(e, "response", None), "status_code", "?")
            print(f"Échec push {path}: HTTP {code}")
        except Exception as e:
            print(f"Échec push {path}: {e}")
    print(f"Notification envoyée à {sent}/{len(subs)} appareil(s).")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
CRM Health Check — weekly audit of HubSpot pipeline.
Outputs: /tmp/crm_health_report.md + /tmp/crm_health_snapshot.json
"""
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

TOKEN = os.environ.get("HUBSPOT_PRIVATE_APP_TOKEN", "")
BASE = "https://api.hubapi.com"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

ICP_MIN_EMPLOYEES = 50
ICP_MIN_REVENUE = 10_000_000
STALE_DEAL_DAYS = 30
INCOMPLETE_THRESHOLD = 0.5


def _api(method: str, endpoint: str, body: dict | None = None) -> dict:
    url = f"{BASE}{endpoint}"
    data = json.dumps(body).encode() if body else None
    req = Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        if e.code == 429:
            time.sleep(11)
            with urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        raise


def _search(object_type: str, filters: list, properties: list, limit: int = 100) -> list:
    results = []
    after = None
    for _ in range(10):
        body = {
            "filterGroups": [{"filters": filters}],
            "properties": properties,
            "limit": min(limit, 100),
        }
        if after:
            body["after"] = after
        data = _api("POST", f"/crm/v3/objects/{object_type}/search", body)
        results.extend(data.get("results", []))
        paging = data.get("paging", {}).get("next")
        if not paging or len(results) >= limit:
            break
        after = paging.get("after")
    return results[:limit]


def check_stale_deals() -> dict:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=STALE_DEAL_DAYS)).strftime("%Y-%m-%d")
    deals = _search("deals", [
        {"propertyName": "dealstage", "operator": "NOT_IN", "values": ["closedwon", "closedlost"]},
        {"propertyName": "hs_lastmodifieddate", "operator": "LT", "value": cutoff},
    ], ["dealname", "dealstage", "amount", "hs_lastmodifieddate", "hubspot_owner_id"], limit=50)

    stale = []
    for d in deals:
        props = d.get("properties", {})
        last_mod = props.get("hs_lastmodifieddate", "")[:10]
        stale.append({
            "name": props.get("dealname", "?"),
            "stage": props.get("dealstage", "?"),
            "amount": props.get("amount", "0"),
            "last_modified": last_mod,
            "id": d.get("id"),
        })
    return {"count": len(stale), "deals": stale[:20]}


def check_incomplete_contacts() -> dict:
    required_fields = ["email", "firstname", "lastname", "company", "jobtitle"]
    contacts = _search("contacts", [
        {"propertyName": "hs_lead_status", "operator": "IN", "values": ["NEW", "OPEN", "IN_PROGRESS"]},
    ], required_fields + ["hs_lead_status", "createdate"], limit=200)

    incomplete = []
    for c in contacts:
        props = c.get("properties", {})
        missing = [f for f in required_fields if not props.get(f)]
        completeness = 1 - len(missing) / len(required_fields)
        if completeness < INCOMPLETE_THRESHOLD or len(missing) >= 2:
            incomplete.append({
                "email": props.get("email", "?"),
                "name": f"{props.get('firstname', '')} {props.get('lastname', '')}".strip() or "?",
                "missing": missing,
                "completeness": round(completeness, 2),
                "status": props.get("hs_lead_status", "?"),
            })
    return {"total_checked": len(contacts), "incomplete_count": len(incomplete), "contacts": incomplete[:30]}


def check_pipeline_summary() -> dict:
    stages = {}
    deals = _search("deals", [
        {"propertyName": "dealstage", "operator": "NOT_IN", "values": ["closedwon", "closedlost"]},
    ], ["dealname", "dealstage", "amount"], limit=200)

    total_value = 0
    for d in deals:
        props = d.get("properties", {})
        stage = props.get("dealstage", "unknown")
        amt = float(props.get("amount") or 0)
        stages.setdefault(stage, {"count": 0, "value": 0})
        stages[stage]["count"] += 1
        stages[stage]["value"] += amt
        total_value += amt

    return {"total_open_deals": len(deals), "total_value": total_value, "by_stage": stages}


def check_recent_activity() -> dict:
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    new_contacts = _search("contacts", [
        {"propertyName": "createdate", "operator": "GTE", "value": week_ago},
    ], ["email", "firstname", "lastname", "company"], limit=200)

    new_deals = _search("deals", [
        {"propertyName": "createdate", "operator": "GTE", "value": week_ago},
    ], ["dealname", "amount", "dealstage"], limit=50)

    won_deals = _search("deals", [
        {"propertyName": "dealstage", "operator": "EQ", "value": "closedwon"},
        {"propertyName": "hs_lastmodifieddate", "operator": "GTE", "value": week_ago},
    ], ["dealname", "amount"], limit=20)

    return {
        "new_contacts_7d": len(new_contacts),
        "new_deals_7d": len(new_deals),
        "won_deals_7d": len(won_deals),
        "won_value_7d": sum(float(d.get("properties", {}).get("amount") or 0) for d in won_deals),
    }


def check_unqualified_backlog() -> dict:
    unqualified = _search("contacts", [
        {"propertyName": "hs_lead_status", "operator": "EQ", "value": "UNQUALIFIED"},
    ], ["email", "createdate"], limit=200)

    six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
    archivable = 0
    for c in unqualified:
        created = c.get("properties", {}).get("createdate", "")
        if created:
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if dt < six_months_ago:
                    archivable += 1
            except ValueError:
                pass

    return {"total_unqualified": len(unqualified), "archivable_6m": archivable}


def generate_report(results: dict) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"# CRM Health Report — {now}\n"]

    activity = results["activity"]
    lines.append("## Activite de la semaine\n")
    lines.append(f"| Indicateur | Valeur |")
    lines.append(f"|------------|--------|")
    lines.append(f"| Nouveaux contacts | **{activity['new_contacts_7d']}** |")
    lines.append(f"| Nouveaux deals | **{activity['new_deals_7d']}** |")
    lines.append(f"| Deals gagnes | **{activity['won_deals_7d']}** |")
    lines.append(f"| Valeur gagnee | **{activity['won_value_7d']:,.0f} EUR** |")
    lines.append("")

    pipeline = results["pipeline"]
    lines.append("## Pipeline ouvert\n")
    lines.append(f"**{pipeline['total_open_deals']}** deals ouverts pour **{pipeline['total_value']:,.0f} EUR**\n")
    if pipeline["by_stage"]:
        lines.append("| Stage | Deals | Valeur |")
        lines.append("|-------|-------|--------|")
        for stage, data in sorted(pipeline["by_stage"].items(), key=lambda x: -x[1]["value"]):
            lines.append(f"| {stage} | {data['count']} | {data['value']:,.0f} EUR |")
        lines.append("")

    stale = results["stale_deals"]
    if stale["count"] > 0:
        lines.append(f"## Deals stagnants ({stale['count']})\n")
        lines.append(f"> Deals sans activite depuis plus de {STALE_DEAL_DAYS} jours\n")
        lines.append("| Deal | Stage | Montant | Derniere MAJ |")
        lines.append("|------|-------|---------|-------------|")
        for d in stale["deals"][:15]:
            lines.append(f"| {d['name']} | {d['stage']} | {float(d['amount'] or 0):,.0f} EUR | {d['last_modified']} |")
        lines.append("")

    incomplete = results["incomplete_contacts"]
    if incomplete["incomplete_count"] > 0:
        lines.append(f"## Contacts incomplets ({incomplete['incomplete_count']}/{incomplete['total_checked']})\n")
        lines.append(f"> Contacts actifs avec plus de 2 champs manquants\n")
        lines.append("| Contact | Email | Champs manquants | Completude |")
        lines.append("|---------|-------|-----------------|------------|")
        for c in incomplete["contacts"][:20]:
            missing_str = ", ".join(c["missing"])
            pct = f"{c['completeness']*100:.0f}%"
            lines.append(f"| {c['name']} | {c['email']} | {missing_str} | {pct} |")
        lines.append("")

    unq = results["unqualified"]
    if unq["total_unqualified"] > 0:
        lines.append(f"## Contacts non qualifies\n")
        lines.append(f"- **{unq['total_unqualified']}** contacts UNQUALIFIED au total")
        lines.append(f"- **{unq['archivable_6m']}** archivables (> 6 mois)")
        if unq["archivable_6m"] > 10:
            lines.append(f"\n> **Action recommandee** : archiver les {unq['archivable_6m']} contacts UNQUALIFIED de plus de 6 mois")
        lines.append("")

    score = _health_score(results)
    lines.append(f"## Score de sante global : **{score}/100**\n")
    if score >= 80:
        lines.append("> Excellent — pipeline propre et actif")
    elif score >= 60:
        lines.append("> Correct — quelques actions d'entretien recommandees")
    else:
        lines.append("> Attention — nettoyage et mise a jour necessaires")

    lines.append(f"\n---\n*Genere automatiquement par Agent System — {now}*")
    return "\n".join(lines)


def _health_score(results: dict) -> int:
    score = 100

    stale_ratio = results["stale_deals"]["count"] / max(results["pipeline"]["total_open_deals"], 1)
    score -= min(int(stale_ratio * 40), 30)

    if results["incomplete_contacts"]["total_checked"] > 0:
        inc_ratio = results["incomplete_contacts"]["incomplete_count"] / results["incomplete_contacts"]["total_checked"]
        score -= min(int(inc_ratio * 30), 20)

    if results["unqualified"]["archivable_6m"] > 50:
        score -= 10
    elif results["unqualified"]["archivable_6m"] > 20:
        score -= 5

    if results["activity"]["new_contacts_7d"] == 0:
        score -= 10

    if results["activity"]["won_deals_7d"] == 0 and results["pipeline"]["total_open_deals"] > 10:
        score -= 5

    return max(0, min(100, score))


def main():
    if not TOKEN:
        print("HUBSPOT_PRIVATE_APP_TOKEN not set — exiting", file=sys.stderr)
        sys.exit(1)

    print("Running CRM health check...", file=sys.stderr)
    results = {}

    print("  Checking recent activity...", file=sys.stderr)
    results["activity"] = check_recent_activity()

    print("  Checking pipeline...", file=sys.stderr)
    results["pipeline"] = check_pipeline_summary()

    print("  Checking stale deals...", file=sys.stderr)
    results["stale_deals"] = check_stale_deals()

    print("  Checking incomplete contacts...", file=sys.stderr)
    results["incomplete_contacts"] = check_incomplete_contacts()

    print("  Checking unqualified backlog...", file=sys.stderr)
    results["unqualified"] = check_unqualified_backlog()

    report = generate_report(results)
    Path("/tmp/crm_health_report.md").write_text(report, encoding="utf-8")
    print(f"Report written to /tmp/crm_health_report.md", file=sys.stderr)

    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "score": _health_score(results),
        "metrics": {
            "open_deals": results["pipeline"]["total_open_deals"],
            "pipeline_value": results["pipeline"]["total_value"],
            "stale_deals": results["stale_deals"]["count"],
            "incomplete_contacts": results["incomplete_contacts"]["incomplete_count"],
            "unqualified_archivable": results["unqualified"]["archivable_6m"],
            "new_contacts_7d": results["activity"]["new_contacts_7d"],
            "won_deals_7d": results["activity"]["won_deals_7d"],
        },
    }
    Path("/tmp/crm_health_snapshot.json").write_text(
        json.dumps(snapshot, indent=2), encoding="utf-8"
    )
    print(f"Snapshot written to /tmp/crm_health_snapshot.json", file=sys.stderr)
    print(f"Health score: {snapshot['score']}/100", file=sys.stderr)


if __name__ == "__main__":
    main()

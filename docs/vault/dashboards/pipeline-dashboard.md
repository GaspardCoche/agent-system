---
title: Dashboard Pipeline Lead Generation
id: dashboards-pipeline-dashboard
type: dashboard
tags: [dashboard, leadgen, pipeline, crm, monitoring]
agents: [scout, aria, lumen]
updated: 2026-03-28
---

# Dashboard Pipeline Lead Generation

*Lie a [[INDEX]], [[leadgen/pipeline-overview]], [[crm/hubspot-properties]], [[crm/hubspot-lifecycle]], [[prospects/pipeline]], [[operations/kpis]]*

> [!info] Vue d'ensemble du pipeline de generation de leads.

---

## Etapes du Pipeline

```dataview
TABLE title AS "Titre", tags AS "Tags", updated AS "Derniere MAJ"
FROM "leadgen"
SORT id ASC
```

---

## Configuration CRM

```dataview
TABLE title AS "Titre", tags AS "Tags", updated AS "Derniere MAJ"
FROM "crm"
SORT title ASC
```

---

## Agents impliques dans le pipeline

```dataview
LIST
FROM "agents"
WHERE contains(tags, "leadgen") OR contains(tags, "crm") OR contains(tags, "enrichment")
SORT title ASC
```

---

## Decisions ouvertes liees au pipeline

```dataview
TASK
FROM "operations/decisions"
WHERE !completed AND (contains(text, "pipeline") OR contains(text, "leadgen") OR contains(text, "Lemlist") OR contains(text, "HubSpot"))
```

---

## KPIs Pipeline

```dataview
LIST
FROM "operations/kpis"
WHERE contains(tags, "pipeline") OR contains(tags, "leadgen")
```

---

## Vue croisee : Campagnes & Sequences

```dataview
TABLE title AS "Titre", tags AS "Tags", updated AS "Derniere MAJ"
FROM "campaigns"
SORT updated DESC
```

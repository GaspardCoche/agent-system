---
title: Dashboard Agents
id: dashboards-agent-dashboard
type: dashboard
tags: [dashboard, agents, status, monitoring]
agents: [all]
updated: 2026-03-28
---

# Dashboard Agents

*Lie a [[INDEX]], [[agents/error-patterns]], [[agents/tool-matrix]], [[operations/kpis]], [[operations/agent-workflows]]*

> [!info] Vue en temps reel de tous les agents et leur etat.

---

## Tous les agents

```dataview
TABLE title AS "Titre", tags AS "Tags", updated AS "Derniere MAJ"
FROM "agents"
WHERE type = "agent"
SORT updated DESC
```

---

## Notes mises a jour recemment (7 derniers jours)

```dataview
TABLE file.folder AS "Dossier", file.mday AS "Modifie le"
FROM ""
WHERE file.mtime >= date(today) - dur(7 days)
SORT file.mday DESC
LIMIT 25
```

---

## Notes par categorie

```dataview
TABLE length(rows) AS "Nombre de notes"
FROM ""
WHERE type
GROUP BY type
SORT length(rows) DESC
```

---

## Connexions les plus denses

```dataview
TABLE length(file.outlinks) AS "Liens sortants", length(file.inlinks) AS "Liens entrants", (length(file.outlinks) + length(file.inlinks)) AS "Total"
FROM ""
SORT (length(file.outlinks) + length(file.inlinks)) DESC
LIMIT 15
```

---

## Notes avec le moins de connexions

> [!warning] Ces notes ont peu de liens et pourraient beneficier de plus de cross-references.

```dataview
TABLE length(file.outlinks) AS "Liens sortants", length(file.inlinks) AS "Liens entrants", (length(file.outlinks) + length(file.inlinks)) AS "Total"
FROM ""
WHERE file.name != "INDEX"
SORT (length(file.outlinks) + length(file.inlinks)) ASC
LIMIT 10
```

---

## Taches ouvertes dans le vault

```dataview
TASK
FROM ""
WHERE !completed
```

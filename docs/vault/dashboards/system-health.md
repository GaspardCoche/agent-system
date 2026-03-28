---
title: Dashboard Sante Systeme
id: dashboards-system-health
type: dashboard
tags: [dashboard, health, system, secrets, maintenance]
agents: [sentinel, sage]
updated: 2026-03-28
---

# Dashboard Sante Systeme

*Lie a [[INDEX]], [[operations/maintenance]], [[operations/secrets-matrix]], [[operations/kpis]], [[agents/error-patterns]], [[agents/sentinel-memory]]*

> [!info] Etat de sante global du systeme multi-agents.

---

## Couverture du Vault

```dataviewjs
const pages = dv.pages('""');
const total = pages.length;
const types = {};
for (const p of pages) {
  const t = p.type || "non-type";
  types[t] = (types[t] || 0) + 1;
}

const today = dv.date("today");
const updatedToday = pages.filter(p => p.file.mday && p.file.mday.toISODate() === today.toISODate()).length;
const weekAgo = today.minus({ days: 7 });
const updatedWeek = pages.filter(p => p.file.mday && p.file.mday >= weekAgo).length;
const monthAgo = today.minus({ days: 30 });
const updatedMonth = pages.filter(p => p.file.mday && p.file.mday >= monthAgo).length;

const avgOutlinks = Math.round(pages.map(p => p.file.outlinks.length).reduce((a, b) => a + b, 0) / total);
const avgInlinks = Math.round(pages.map(p => p.file.inlinks.length).reduce((a, b) => a + b, 0) / total);

dv.header(3, "Metriques globales");
dv.table(
  ["Metrique", "Valeur"],
  [
    ["Notes totales", total],
    ["Connexions moyennes (sortantes)", avgOutlinks],
    ["Connexions moyennes (entrantes)", avgInlinks],
    ["MAJ aujourd'hui", updatedToday],
    ["MAJ cette semaine", updatedWeek],
    ["MAJ ce mois", updatedMonth],
  ]
);

dv.header(3, "Repartition par type");
dv.table(
  ["Type", "Nombre"],
  Object.entries(types).sort((a, b) => b[1] - a[1]).map(([k, v]) => [k, v])
);
```

---

## Notes les plus anciennes (pas mises a jour recemment)

> [!warning] Ces notes n'ont pas ete mises a jour depuis longtemps et pourraient necessiter une revision.

```dataview
TABLE title AS "Titre", updated AS "Derniere MAJ YAML", file.mday AS "Derniere modif fichier"
FROM ""
WHERE updated
SORT updated ASC
LIMIT 10
```

---

## Fichiers par dossier

```dataviewjs
const pages = dv.pages('""');
const folders = {};
for (const p of pages) {
  const folder = p.file.folder || "(racine)";
  folders[folder] = (folders[folder] || 0) + 1;
}

dv.table(
  ["Dossier", "Nombre de fichiers"],
  Object.entries(folders).sort((a, b) => b[1] - a[1]).map(([k, v]) => [k, v])
);
```

---

## Erreurs documentees

```dataview
TABLE title AS "Titre", tags AS "Tags", updated AS "Derniere MAJ"
FROM "agents/error-patterns"
```

> [!tip] Voir [[agents/error-patterns]] pour le catalogue complet des 15 erreurs documentees.

---

## Maintenance a venir

> [!note] Calendrier de maintenance du systeme multi-agents.

Voir [[operations/maintenance]] pour le planning complet (quotidien, hebdomadaire, mensuel, trimestriel).

```dataview
TASK
FROM "operations/maintenance"
WHERE !completed
```

---

## Secrets non configures

> [!caution] Verifier regulierement l'etat des secrets GitHub.

Voir [[operations/secrets-matrix]] pour la matrice complete des 15 secrets, leur statut et le calendrier de rotation.

```dataview
TABLE title AS "Titre", tags AS "Tags", updated AS "Derniere MAJ"
FROM "operations/secrets-matrix"
```

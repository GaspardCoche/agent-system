---
title: Décisions & Architecture
id: operations-decisions
type: operations
tags: [decisions, architecture, system, dispatch, sage]
agents: [dispatch, sage]
updated: 2026-03-24
---

# Décisions & Architecture

*Lié à [[INDEX]], [[agents/sage-memory]], [[agents/dispatch-log]]*

> Journal des décisions importantes du système. Toute décision d'architecture, de stratégie ou d'implémentation doit être documentée ici.

---

## Décisions actives

### 2026-03-24 — Architecture Vault + Knowledge Graph

**Décision :** Migrer vers un système "Vault-Driven" où chaque agent lit et écrit dans `docs/vault/`.

**Pourquoi :** Permettre aux agents de maintenir un contexte persistant entre les runs et de construire une base de connaissance cumulative.

**Impact :**
- Tous les agents lisent `vault/INDEX.md` avant d'agir
- Chaque agent a son fichier mémoire dans `vault/agents/`
- Le dashboard affiche le graph des connexions
- Obsidian peut ouvrir `docs/vault/` pour la vue graphique locale

---

### 2026-03-24 — Dashboard Multi-Tab

**Décision :** Dashboard Netlify avec tabs Runs / Status / Graph

**Pourquoi :** Vue unifiée des runs, santé des agents, et knowledge graph

**URL :** https://agent-system.netlify.app (à configurer)

---

### 2026-03-24 — Rapports dans docs/reports/

**Décision :** Les rapports agents vont dans `docs/reports/` (Netlify-accessible) et mirroring dans `reports/`

**Pourquoi :** Les rapports en `reports/` n'étaient pas accessibles depuis le dashboard Netlify

---

## Template pour nouvelles décisions

```markdown
### YYYY-MM-DD — [Titre court]

**Décision :** [Quoi]

**Pourquoi :** [Motivation, contexte]

**Impact :** [Ce qui change]

**Réversible :** Oui/Non — [Comment revenir en arrière si besoin]
```

---

*Sage et Dispatch mettent à jour ce fichier. Lire avant toute décision importante.*

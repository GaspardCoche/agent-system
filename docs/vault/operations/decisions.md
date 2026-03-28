---
title: Décisions & Architecture
id: operations-decisions
type: operations
tags: [decisions, architecture, system, dispatch, sage]
agents: [dispatch, sage]
updated: 2026-03-28
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

**Décision :** Dashboard GitHub Pages avec tabs Runs / Status / Graph / Agents

**Pourquoi :** Vue unifiée des runs, santé des agents, et knowledge graph

**URL :** https://gaspardcoche.github.io/agent-system/

---

### 2026-03-27 — Migration Netlify vers GitHub Pages

**Décision :** Abandonner Netlify, passer a GitHub Pages + appels GitHub API directs

**Pourquoi :** Netlify trop limitant. GitHub Pages est gratuit, auto-deploye, et integre nativement au repo.

**Impact :**
- Plus de `netlify.toml` ni de `netlify/functions/`
- Dashboard appelle l'API GitHub directement (PAT en localStorage)
- Workflow `deploy-pages.yml` deploie automatiquement
- Zero dependance externe

---

### 2026-03-24 — Rapports dans docs/reports/

**Décision :** Les rapports agents vont dans `docs/reports/` (accessible par GitHub Pages) et mirroring dans `reports/`

**Pourquoi :** Les rapports doivent etre accessibles depuis le dashboard

---

### 2026-03-28 — Integration Leadgen Pipeline

**Decision :** Integration du leadgen-vault dans le vault agent-system.

**Pourquoi :** Centraliser toute la connaissance dans un seul second cerveau. Le leadgen-vault contenait des notes isolees sur le pipeline de prospection, les sources, le scoring et les sequences -- les fusionner dans le vault principal permet une meilleure interconnexion et evite les doublons.

**Impact :**
- 13 nouvelles notes ajoutees dans `docs/vault/` (sous `leadgen/`, `campaigns/`, `crm/`)
- Knowledge graph enrichi : 39 nodes, 144 edges
- Les agents (Scout, Aria, Lumen) ont acces a la connaissance leadgen directement dans le vault
- Ref : [[leadgen/pipeline-overview]], [[leadgen/lead-scoring]], [[leadgen/sources-web]]

---

### 2026-03-28 — Lemlist vs HubSpot Sequences (OPEN)

**Decision :** A prendre -- choix entre Lemlist et HubSpot Sequences pour l'outreach automatise.

**Pourquoi :** Les deux outils couvrent le meme besoin (sequences d'emails automatisees) mais avec des approches differentes. Il faut trancher pour eviter la duplication d'efforts.

**Options :**

| Critere | Lemlist | HubSpot Sequences |
|---------|---------|-------------------|
| Deliverability | Excellent (warmup integre, rotation domaines) | Correct (pas de warmup natif) |
| Integration LinkedIn | Oui (steps LinkedIn natifs) | Non |
| Integration CRM | Via API/Zapier | Native (meme plateforme) |
| Prix | Abonnement separe | Inclus dans HubSpot Sales Hub |
| Reporting | Bon (open/click/reply) | Integre au CRM |

**A decider :** Q2 2026. Ref : [[campaigns/lemlist-sequences]]

---

### 2026-03-28 — Lead Scoring Model

**Decision :** Adopter un modele de scoring composite sur 100 points avec seuils MQL=60 et SQL=80.

**Pourquoi :** Permettre a Aria et au pipeline leadgen de prioriser automatiquement les leads et de router les plus qualifies vers le CRM / les sequences outreach.

**Criteres de scoring :**

| Critere | Points max | Detail |
|---------|-----------|--------|
| Job Title | 25 | CFO/DAF=25, Controller=20, CEO=15, autre finance=10 |
| Seniority | 15 | C-level=15, VP=12, Director=10, Manager=5 |
| Email professionnel | 10 | Email corporate=10, generique=0 |
| Industrie | 15 | Industrie cible ICP=15, adjacente=8, hors cible=0 |
| Taille entreprise | 10 | 50-500 employes=10, 500-5000=8, <50=3, >5000=5 |
| Geographie | 10 | Belgique/France/Lux=10, DACH=7, autre EU=5 |
| Completude profil | 15 | LinkedIn=5, email=5, telephone=5 |

**Seuils :** MQL >= 60, SQL >= 80
**Ref :** [[leadgen/lead-scoring]], [[leadgen/pipeline-overview]]

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

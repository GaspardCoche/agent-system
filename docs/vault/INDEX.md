---
title: VAULT-INDEX
id: index
type: index
tags: [index, hub, system]
agents: [all]
updated: 2026-03-27
---

# VAULT-INDEX -- Centre de Connaissance

> Base de connaissance vivante du systeme multi-agents. **Lire ce fichier en debut de chaque session.**
> Chaque agent enrichit ce vault apres chaque run. Le graph est visible dans le dashboard -- onglet Graph.

---

## Business

- [[business/vision]] -- Vision & Mission de l'entreprise
- [[business/strategy]] -- Strategie business actuelle
- [[business/roadmap]] -- Roadmap & priorites

## Prospects & CRM

- [[prospects/pipeline]] -- Pipeline leads actif (Scout + Aria)

## Campagnes Marketing

- [[campaigns/google-ads]] -- Etat campagnes Google Ads (Nexus)

## Operations

- [[operations/daily-digest]] -- Digest email du jour (Iris)
- [[operations/decisions]] -- Decisions d'architecture & strategiques
- [[operations/runbooks]] -- Procedures operationnelles standard
- [[operations/kpis]] -- Metriques et KPIs systeme

## Contenu

- [[content/social-media]] -- Strategie contenu & idees
- [[content/brand-voice]] -- Brand voice & ton editorial
- [[content/editorial-calendar]] -- Calendrier editorial

## Technique

- [[tech/infrastructure]] -- Architecture & infrastructure
- [[tech/integrations]] -- Integrations & APIs externes

## Securite

- [[security/access-control]] -- Controle d'acces & politique de securite

## Memoire Agents

- [[agents/dispatch-log]] -- Dispatch : historique orchestrations
- [[agents/nexus-memory]] -- Nexus : patterns ads, historique optimisations
- [[agents/iris-memory]] -- Iris : profils expediteurs, patterns email
- [[agents/scout-memory]] -- Scout : sources web validees, patterns scraping
- [[agents/sage-memory]] -- Sage : ameliorations, skills candidats
- [[agents/forge-memory]] -- Forge : patterns dev, fichiers critiques
- [[agents/sentinel-memory]] -- Sentinel : QA, tests, couverture
- [[agents/ralph-memory]] -- Ralph : automatisations, crons, webhooks
- [[agents/lumen-memory]] -- Lumen : analyses, insights accumules
- [[agents/aria-memory]] -- Aria : leads, enrichissement, CRM

---

## Contexte Systeme

```
Agents actifs : Orchestrator, Iris, Scout, Aria, Nexus, Sage, Ralph, Forge, Sentinel, Lumen
Repo GitHub   : GaspardCoche/agent-system
Dashboard     : GitHub Pages (https://gaspardcoche.github.io/agent-system/)
Vault         : docs/vault/ (ce repertoire)
Obsidian      : Ouvrir docs/vault/ comme vault Obsidian
```

## Comment utiliser ce vault

| Qui | Quand | Quoi |
|-----|-------|------|
| **Agents** | Debut de chaque tache | Lire INDEX + fichier memoire de l'agent |
| **Agents** | Fin de chaque run | Mettre a jour le(s) fichier(s) concerne(s) |
| **Toi** | Session de travail | Lire INDEX pour contexte complet |
| **Toi** | Revue hebdo | Ouvrir dans Obsidian, explorer le graph |
| **Sage** | Dimanche | Analyser vault, proposer ameliorations |

---

## Derniere mise a jour systeme

| Agent | Dernier run | Statut |
|-------|------------|--------|
| Nexus | 2026-03-24 | Audit dry-run termine |
| Sage | 2026-03-24 | Weekly run termine |
| Iris | -- | A configurer (GMAIL_TOKEN_JSON) |
| Scout | -- | A configurer (FIRECRAWL_API_KEY) |
| Aria | -- | A configurer (FULLENRICH + HUBSPOT) |
| Forge | -- | Operationnel |
| Sentinel | -- | Operationnel |
| Ralph | -- | Operationnel |
| Lumen | -- | Operationnel |

---

## Statistiques Vault

| Metrique | Valeur |
|----------|--------|
| Notes totales | 23 |
| Categories | 7 (business, operations, campaigns, content, tech, security, agents) |
| Agents avec memoire | 10/10 |
| Derniere mise a jour | 2026-03-27 |

---

*Ce fichier est le noeud central du knowledge graph. Chaque `[[lien]]` est une connexion dans le graph.*

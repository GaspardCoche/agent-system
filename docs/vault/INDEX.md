---
title: VAULT-INDEX
id: index
type: index
tags: [index, hub, system]
agents: [all]
updated: 2026-03-28
---

# VAULT-INDEX -- Second Cerveau

> Base de connaissance vivante du systeme multi-agents et du pipeline lead generation.
> **Lire ce fichier en debut de chaque session.** Chaque agent enrichit ce vault apres chaque run.
> Le graph est visible dans Obsidian (Cmd+Shift+G) et dans le dashboard -- onglet Graph.

---

## Dashboards (Dataview)

- [[dashboards/agent-dashboard]] -- Tous les agents, notes recentes, connexions, taches
- [[dashboards/pipeline-dashboard]] -- Pipeline lead gen, CRM, decisions ouvertes
- [[dashboards/system-health]] -- Sante systeme, couverture vault, maintenance

## Business & Strategie

- [[business/vision]] -- Vision, mission, ICP, proposition de valeur EMAsphere
- [[business/strategy]] -- Strategie CRM & Marketing Digital 2026
- [[business/roadmap]] -- Roadmap 4 phases & jalons cles
- [[business/icp-personas]] -- ICP & 4 buyer personas detailles

## Lead Generation Pipeline

- [[leadgen/pipeline-overview]] -- Vue d'ensemble end-to-end du pipeline
- [[leadgen/sources-linkedin]] -- Sources LinkedIn Sales Navigator
- [[leadgen/sources-web]] -- Sources web alternatives (EasyScraper, Trendstop, Moulinette)
- [[leadgen/enrichment-phantom]] -- Extraction PhantomBuster (API v2, rate limits)
- [[leadgen/enrichment-fullenrich]] -- Enrichissement FullEnrich (email, phone, company)
- [[leadgen/cleaning-rules]] -- 22 regles de nettoyage Contact & Company (P0-P3)
- [[leadgen/cleaning-gmt]] -- GMT Google Sheet hub de nettoyage & bases de donnees
- [[leadgen/lead-scoring]] -- Scoring composite 100pts (MQL>=60, SQL>=80)
- [[leadgen/geographic-hubs]] -- 5 hubs geographiques & routing automatique
- [[leadgen/monitoring]] -- Monitoring pipeline, alertes, health checks

## CRM -- HubSpot

- [[crm/hubspot-properties]] -- 36 proprietes (21 Contact + 15 Company), mapping & enums
- [[crm/hubspot-api]] -- API integration, endpoints, rate limits, stubs
- [[crm/hubspot-backlog]] -- 16 taches d'optimisation CRM (Q1-Q4 2026)
- [[crm/hubspot-lifecycle]] -- 8 lifecycle stages & regles de transition
- [[crm/hubspot-workflows]] -- Workflows d'attribution, lifecycle, data quality

## Prospects & Funnel

- [[prospects/pipeline]] -- Funnel de qualification (Lead → MQL → SQL → Client)

## Campagnes Marketing

- [[campaigns/google-ads]] -- Campagnes Google Ads EMAsphere (Customer ID: 7251903503)
- [[campaigns/lemlist-sequences]] -- Sequences outreach Lemlist multilingues (FR/NL/EN)

## Operations

- [[operations/daily-digest]] -- Digest email quotidien (Iris)
- [[operations/decisions]] -- Decisions d'architecture & strategiques
- [[operations/runbooks]] -- Procedures operationnelles standard
- [[operations/kpis]] -- KPIs systeme, pipeline, business & health checks
- [[operations/agent-workflows]] -- Chaines d'agents & orchestration
- [[operations/secrets-matrix]] -- 15 secrets GitHub, status & rotation
- [[operations/maintenance]] -- Calendrier de maintenance (quotidien, hebdo, mensuel, trimestriel)

## Contenu

- [[content/social-media]] -- Strategie contenu & reseaux sociaux
- [[content/brand-voice]] -- Brand voice & ton editorial
- [[content/editorial-calendar]] -- Calendrier editorial

## Technique

- [[tech/infrastructure]] -- Architecture multi-agents & infrastructure
- [[tech/integrations]] -- Integrations API (MCP, PhantomBuster, FullEnrich, Sheets)
- [[tech/data-schemas]] -- Schemas Zod & TypeScript (7 schemas de validation)
- [[tech/code-repository]] -- Repository lead-pipeline (structure, stubs, lookup data)
- [[tech/mcp-servers]] -- 10 serveurs MCP & configuration agents
- [[tech/skills-registry]] -- 4 skills valides, cycle de vie MCP → Script
- [[tech/token-budget]] -- Budget tokens & couts par agent (~$80/mois)

## Securite

- [[security/access-control]] -- Controle d'acces agents & politique de securite

## Ingenierie Agents

- [[agents/creation-guide]] -- Guide complet de creation d'un nouvel agent (7 etapes)
- [[agents/prompt-engineering]] -- Patterns de prompts, anti-patterns, metriques qualite
- [[agents/communication-protocol]] -- Protocole JSON inter-agents (task/result/retrospective)
- [[agents/error-patterns]] -- 15 erreurs documentees, diagnostic & prevention
- [[agents/tool-matrix]] -- Matrice des permissions outils par agent (R/W/RW)
- [[agents/testing-patterns]] -- 4 niveaux de test, checklists de validation

## Memoire Agents

- [[agents/dispatch-log]] -- Dispatch : historique orchestrations
- [[agents/nexus-memory]] -- Nexus : patterns Google Ads, historique optimisations
- [[agents/iris-memory]] -- Iris : profils expediteurs, patterns email
- [[agents/scout-memory]] -- Scout : sources web validees, patterns scraping
- [[agents/sage-memory]] -- Sage : ameliorations, skills candidats, prompt engineering
- [[agents/forge-memory]] -- Forge : patterns dev, fichiers critiques, stack
- [[agents/sentinel-memory]] -- Sentinel : QA, tests, couverture, regressions
- [[agents/ralph-memory]] -- Ralph : automatisations, crons, webhooks
- [[agents/lumen-memory]] -- Lumen : analyses, insights accumules
- [[agents/aria-memory]] -- Aria : leads, enrichissement, CRM, RGPD

---

## Contexte Systeme

```
Agents actifs : Orchestrator, Iris, Scout, Aria, Nexus, Sage, Ralph, Forge, Sentinel, Lumen
Repo GitHub   : GaspardCoche/agent-system
Dashboard     : https://gaspardcoche.github.io/agent-system/
Vault         : docs/vault/ (ce repertoire)
Obsidian      : Ouvrir docs/vault/ comme vault dans l'app Obsidian
Lead Pipeline : hwinssinger/lead-pipeline (TypeScript, 16 stubs a remplacer)
```

## Comment utiliser ce vault

| Qui | Quand | Quoi |
|-----|-------|------|
| **Agents** | Debut de chaque tache | Lire INDEX + fichier memoire de l'agent + fichiers pertinents |
| **Agents** | Fin de chaque run | Mettre a jour le(s) fichier(s) concerne(s) + retrospective |
| **Toi** | Session de travail | Lire INDEX pour contexte complet |
| **Toi** | Revue hebdo | Ouvrir dans Obsidian, explorer le graph (Cmd+Shift+G) |
| **Sage** | Dimanche | Analyser vault, proposer ameliorations de prompts et skills |

---

## Derniere mise a jour systeme

| Agent | Dernier run | Statut |
|-------|------------|--------|
| Sage | 2026-04-05 | Weekly run terminé (0 retrospectives, 3e semaine, root causes identifiées — fix requis email-agent.yml + reusable) |
| Nexus | 2026-03-24 | Audit dry-run termine (score 58/100) |
| Iris | -- | En attente (GMAIL_TOKEN_JSON) |
| Scout | -- | Operationnel (FIRECRAWL_API_KEY configure) |
| Aria | -- | En attente (FULLENRICH + HUBSPOT) |
| Forge | -- | Operationnel |
| Sentinel | -- | Operationnel |
| Ralph | -- | Operationnel |
| Lumen | -- | Operationnel |

---

## Statistiques Vault

| Metrique | Valeur |
|----------|--------|
| Notes totales | 57 |
| Connexions (edges) | 360 |
| Categories | 11 (business, leadgen, crm, prospects, campaigns, operations, content, tech, security, agents, index) |
| Agents avec memoire | 10/10 |
| Derniere mise a jour | 2026-03-29 |

---

*Ce fichier est le noeud central du knowledge graph. Chaque `[[lien]]` est une connexion dans le graph.*

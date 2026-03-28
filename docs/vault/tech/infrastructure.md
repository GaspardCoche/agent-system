---
title: Infrastructure & Architecture Technique
id: tech-infrastructure
type: tech
tags: [infrastructure, architecture, github-actions, github-pages, deployment]
agents: [forge, sentinel]
updated: 2026-03-28
---

# Infrastructure & Architecture Technique

*Lie a [[INDEX]], [[operations/decisions]], [[tech/integrations]]*

> Architecture technique du systeme multi-agents. Reference pour tout agent travaillant sur l'infra.

---

## Architecture globale

```
                    +-------------------+
                    |   GitHub Issues   |
                    |   / Dispatch /    |
                    |   Cron Schedule   |
                    +---------+---------+
                              |
                    +---------v---------+
                    |   Orchestrator    |
                    |  (dispatch.md)    |
                    +---------+---------+
                              |
              +---------------+---------------+
              |               |               |
     +--------v--+    +------v----+   +------v------+
     | Researcher|    | Analyzer  |   |   Scout     |
     | (parallel)|    | (parallel)|   | (parallel)  |
     +-----------+    +-----------+   +-------------+
              |               |               |
              +---------------+---------------+
                              |
                    +---------v---------+
                    |      Forge        |
                    |  (sequential)     |
                    +---------+---------+
                              |
                    +---------v---------+
                    |    Sentinel       |
                    |  (tests & QA)     |
                    +---------+---------+
                              |
                    +---------v---------+
                    |    Aggregate      |
                    | (report + notify) |
                    +-------------------+
```

---

## Composants

### GitHub Actions (Orchestration)

| Workflow | Trigger | Role |
|----------|---------|------|
| `orchestrator.yml` | Issues (label `agent`), PRs, cron Lun-Ven 8h, manual | Pipeline complete |
| `_reusable-claude.yml` | `workflow_call` | Base commune tous agents |
| `email-agent.yml` | cron 7h30 UTC, manual | Iris email digest |
| `scout.yml` | `repository_dispatch`, manual | Veille web |
| `aria.yml` | `repository_dispatch`, manual | Enrichissement leads |
| `nexus.yml` | cron Lundi 6h UTC, manual | Audit Google Ads |
| `sage.yml` | cron Dimanche, manual | Auto-amelioration |
| `ralph.yml` | `repository_dispatch` | Routage webhooks |
| `health-check.yml` | manual | Verification secrets |
| `vault-sync.yml` | push sur `docs/vault/**`, manual | Rebuild knowledge graph |

### GitHub Pages (Dashboard)

| Element | Role |
|---------|------|
| `docs/index.html` | Dashboard single-page (Runs, Status, Graph, Agents) |
| `docs/data/*.json` | Donnees statiques (agents, runs, graph, health) |
| `docs/reports/*.md` | Rapports agents rendus en markdown |
| `.github/workflows/deploy-pages.yml` | Deploy automatique a chaque push sur docs/ |

Le dashboard appelle l'API GitHub directement (PAT stocke en localStorage) pour declencher les workflows.

### Obsidian Vault (Knowledge)

| Dossier | Contenu |
|---------|---------|
| `docs/vault/` | Racine du vault Obsidian |
| `docs/vault/agents/` | Memoire persistante de chaque agent |
| `docs/vault/business/` | Vision, strategie, roadmap |
| `docs/vault/campaigns/` | Etat des campagnes marketing |
| `docs/vault/content/` | Strategie contenu et social media |
| `docs/vault/operations/` | Operations quotidiennes et decisions |
| `docs/vault/prospects/` | Pipeline prospects et CRM |
| `docs/vault/tech/` | Documentation technique |
| `docs/vault/security/` | Securite et acces |

---

## Flux de donnees

```
Agent run → /tmp/agent_result.json → generate_report.py → docs/data/runs.json + docs/reports/
Vault edit → vault_builder.py → docs/data/graph.json → Dashboard Graph tab
Health check → health-check.yml → docs/data/health.json → Dashboard Status tab
```

---

## Secrets requis

| Secret | Utilise par | Criticite |
|--------|-----------|----------|
| `CLAUDE_CODE_OAUTH_TOKEN` | Tous les agents | Obligatoire |
| `GEMINI_API_KEY` | Lumen, Sage, context_compressor | Optionnel |
| `GMAIL_TOKEN_JSON` | Iris | Requis pour Iris |
| `GMAIL_USER_EMAIL` | Iris | Requis pour Iris |
| `FIRECRAWL_API_KEY` | Scout | Requis pour Scout |
| `HUBSPOT_API_KEY` | Aria | Requis pour Aria |
| `FULLENRICH_API_KEY` | Aria | Requis pour Aria |
| `GOOGLE_ADS_*` (4 secrets) | Nexus | Requis pour Nexus |
| `SLACK_WEBHOOK_URL` | Notifications | Optionnel |

---

## Couts estimes

| Service | Plan | Cout |
|---------|------|------|
| GitHub Actions | Free (2000 min/mois) | Gratuit |
| GitHub Pages | Free | Gratuit |
| Claude Code OAuth | Inclus abonnement | -- |
| Gemini API | Free tier | Gratuit |
| Firecrawl | Free tier (500 credits) | Gratuit |

---

*Forge et Dispatch mettent a jour ce fichier. Lire avant tout changement d'infrastructure.*

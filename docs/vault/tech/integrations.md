---
title: Integrations & APIs
id: tech-integrations
type: tech
tags: [integrations, mcp, apis, tools, external-services]
updated: 2026-03-27
---

# Integrations & APIs

*Lie a [[INDEX]], [[tech/infrastructure]], [[operations/decisions]]*

> Catalogue de toutes les integrations externes. Reference pour tout agent utilisant des APIs.

---

## MCP Servers configures

| MCP Server | Outils principaux | Utilise par |
|-----------|------------------|-----------|
| `@modelcontextprotocol/server-filesystem` | read_file, write_file, list_directory | Forge, tous |
| `@modelcontextprotocol/server-github` | create_issue, add_comment, search_code | Dispatch, Forge, Sage |
| `@playwright/mcp` | navigate, get_visible_text, screenshot | Scout, Researcher |
| `firecrawl-mcp` | scrape, search, crawl | Scout |
| `@modelcontextprotocol/server-memory` | add_observations, search_nodes | Tous |

---

## APIs externes

### Google Ads API (Nexus)

| Endpoint | Usage | Rate limit |
|----------|-------|-----------|
| `googleads.search` | Requetes GAQL | 10000/jour |

**Regles critiques :**
- JAMAIS `.type` dans `conditions` -> cascade d'erreurs
- JAMAIS appels paralleles -> annulation en cascade si 1 echoue
- JAMAIS `metrics.optimization_score` avec segments de date
- JAMAIS metriques sur `ad_group_criterion` -> utiliser `keyword_view`
- Toujours sequentiel, 1 requete a la fois

### Gmail API (Iris)

| Scope | Usage |
|-------|-------|
| `gmail.readonly` | Lire les emails |
| `gmail.modify` | Creer des drafts |

### FullEnrich API (Aria)

| Endpoint | Usage |
|----------|-------|
| `/enrich` | Enrichir nom+entreprise -> email+tel |

### HubSpot API (Aria)

| Endpoint | Usage | Rate limit |
|----------|-------|-----------|
| `/contacts` | CRUD contacts | 150 req/10s |
| `/companies` | CRUD companies | 150 req/10s |

### Firecrawl API (Scout)

| Endpoint | Usage |
|----------|-------|
| `/scrape` | Scraper une URL -> markdown |
| `/search` | Recherche web |
| `/crawl` | Crawler un site complet |

### Gemini API (Lumen, Sage)

| Modele | Usage | Context |
|--------|-------|---------|
| `gemini-2.0-flash` | Analyse gros fichiers (> 50KB) | 1M tokens |

---

## Skills valides (alternatives aux MCPs)

| Skill | Remplace | Script | Avantage |
|-------|---------|--------|----------|
| `firecrawl_scrape` | `mcp__firecrawl__firecrawl_scrape` | `skills/validated/firecrawl_scrape.py` | Moins de tokens |
| `github_create_issue` | `mcp__github__create_issue` | `skills/validated/github_create_issue.py` | Plus rapide |
| `gemini_analyze` | Appels directs Gemini | `skills/validated/gemini_analyze.py` | Standardise |
| `slack_notify` | curl webhook | `skills/validated/slack_notify.py` | Formate |

---

## Declenchement de workflows

Le dashboard appelle directement l'API GitHub pour declencher les workflows :
```
POST https://api.github.com/repos/GaspardCoche/agent-system/actions/workflows/{workflow}/dispatches
Authorization: Bearer <PAT>
Body: { "ref": "main", "inputs": {...} }
```

---

*Mettre a jour quand une nouvelle integration est ajoutee ou modifiee.*

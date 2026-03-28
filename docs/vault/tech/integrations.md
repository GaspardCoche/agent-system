---
title: Integrations & APIs
id: tech-integrations
type: tech
tags: [integrations, mcp, apis, tools, external-services, leadgen, phantombuster, fullenrich]
agents: [scout, aria, forge]
updated: 2026-03-28
---

# Integrations & APIs

*Lie a [[INDEX]], [[tech/infrastructure]], [[tech/code-repository]], [[operations/decisions]], [[leadgen/enrichment-phantom]], [[leadgen/enrichment-fullenrich]], [[leadgen/cleaning-gmt]]*

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

### PhantomBuster API v2 (Scout)

> Utilise pour le scraping de listes Sales Navigator et l'extraction de profils LinkedIn. Voir [[leadgen/enrichment-phantom]].

| Attribut | Valeur |
|----------|--------|
| **Base URL** | `https://api.phantombuster.com/api/v2` |
| **Authentification** | Header `X-Phantombuster-Key` |
| **Rate limits** | 1 requete/seconde, 10 000 requetes/jour |

**Endpoints principaux :**

| Endpoint | Methode | Usage |
|----------|---------|-------|
| `/agents/fetch` | GET | Recuperer le statut d'un phantom |
| `/agents/launch` | POST | Lancer un phantom (scraping) |
| `/agents/fetch-output` | GET | Recuperer les resultats d'un run |
| `/containers/fetch-result-object` | GET | Telecharger le fichier de resultats |

**Mapping colonnes typique (Sales Navigator -> Pipeline) :**

| Colonne PhantomBuster | Colonne Pipeline | Notes |
|-----------------------|-----------------|-------|
| `firstName` | `first_name` | -- |
| `lastName` | `last_name` | -- |
| `title` | `job_title` | Nettoyage requis (titres bruts) |
| `companyName` | `company_name` | -- |
| `companyUrl` | `company_linkedin_url` | URL LinkedIn de l'entreprise |
| `linkedinUrl` | `linkedin_url` | Verifier format `/in/xxx` |
| `location` | `location` | Parsing pays/ville requis |
| `connectionDegree` | -- | Non utilise dans le pipeline |

> **Attention** : Les rate limits sont strictes. Toujours implementer un backoff exponentiel. Ne jamais lancer plusieurs phantoms en parallele sur le meme compte.

---

### FullEnrich API (Aria)

> Enrichissement email et telephone a partir du nom + entreprise. Voir [[leadgen/enrichment-fullenrich]].

| Attribut | Valeur |
|----------|--------|
| **Base URL** | `https://api.fullenrich.com/v1` |
| **Authentification** | Header `Authorization: Bearer <token>` |
| **Modele** | Asynchrone (submit + poll) |

**Flow d'enrichissement :**

```
1. POST /enrich     → Soumettre un batch de contacts (nom + entreprise)
                      Retourne un task_id
2. GET /enrich/{id} → Poller le statut (pending / processing / completed / failed)
                      Intervalle recommande : 30s
3. GET /enrich/{id} → Quand completed, recuperer les resultats enrichis
```

**Champs en entree :**

| Champ | Requis | Description |
|-------|--------|-------------|
| `first_name` | Oui | Prenom du contact |
| `last_name` | Oui | Nom du contact |
| `company_name` | Oui | Nom de l'entreprise |
| `company_domain` | Non | Domaine web (ameliore la precision) |
| `linkedin_url` | Non | URL profil LinkedIn (ameliore la precision) |

**Champs en sortie :**

| Champ | Description |
|-------|-------------|
| `email` | Email professionnel trouve |
| `email_confidence` | Score de confiance (high/medium/low) |
| `phone` | Numero de telephone |
| `company_domain` | Domaine de l'entreprise |

**Gestion des credits :**

- Chaque enrichissement consomme 1 credit (meme si aucun resultat)
- Suivre la consommation dans [[operations/kpis]]
- Alerte si > 80% du budget mensuel consomme

---

### Google Sheets API (GMT Management)

> Gestion du Google Master Table (GMT) pour le nettoyage des leads. Voir [[leadgen/cleaning-gmt]].

| Attribut | Valeur |
|----------|--------|
| **API** | Google Sheets API v4 |
| **Authentification** | Service Account (JSON key) |
| **Scopes** | `spreadsheets`, `drive.file` |

**Operations principales :**

| Operation | Endpoint | Usage dans le pipeline |
|-----------|----------|----------------------|
| Lecture | `spreadsheets.values.get` | Lire les leads a nettoyer |
| Ecriture | `spreadsheets.values.update` | Ecrire les resultats du nettoyage |
| Batch update | `spreadsheets.values.batchUpdate` | Mise a jour en masse des colonnes |
| Formatage | `spreadsheets.batchUpdate` | Coloration par statut (clean/bin/review) |

> Le GMT est le point central de controle qualite entre l'enrichissement et l'upload CRM.

---

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

> Voir [[campaigns/google-ads]] et [[agents/nexus-memory]] pour le contexte compte EMAsphere.

---

### Gmail API (Iris)

| Scope | Usage |
|-------|-------|
| `gmail.readonly` | Lire les emails |
| `gmail.modify` | Creer des drafts |

---

### HubSpot API (Aria)

| Endpoint | Usage | Rate limit |
|----------|-------|-----------|
| `/contacts` | CRUD contacts | 150 req/10s |
| `/companies` | CRUD companies | 150 req/10s |
| `/associations` | Lier contacts a entreprises | 150 req/10s |
| `/properties` | Gestion des proprietes custom | 150 req/10s |

> Voir [[crm/hubspot-properties]] pour le mapping des proprietes et [[crm/hubspot-backlog]] pour le backlog de nettoyage.

---

### Firecrawl API (Scout)

| Endpoint | Usage |
|----------|-------|
| `/scrape` | Scraper une URL -> markdown |
| `/search` | Recherche web |
| `/crawl` | Crawler un site complet |

---

### Gemini API (Lumen, Sage)

| Modele | Usage | Context |
|--------|-------|---------|
| `gemini-2.0-flash` | Analyse gros fichiers (> 50KB) | 1M tokens |

---

## Repository lead-pipeline

> Le code source du pipeline de generation de leads est dans un repository dedie.

| Attribut | Valeur |
|----------|--------|
| **Repository** | Voir [[tech/code-repository]] |
| **Langage** | Python |
| **Modules** | scraping, enrichment, cleaning (GMT), upload (HubSpot) |
| **Orchestration** | GitHub Actions workflows |

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

*Mettre a jour quand une nouvelle integration est ajoutee ou modifiee. Voir [[leadgen/pipeline-overview]] pour le flux complet des donnees entre ces APIs.*

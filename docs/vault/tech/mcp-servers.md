---
title: "Serveurs MCP -- Configuration & Outils"
id: tech-mcp-servers
type: tech
tags: [tech, mcp, servers, tools, configuration, claude]
agents: [all]
updated: 2026-03-28
---

# Serveurs MCP -- Configuration & Outils

> [!info] Vue d'ensemble
> Les serveurs MCP (Model Context Protocol) fournissent aux agents Claude Code un acces structure aux APIs et outils externes. Ils sont configures dans le workflow GitHub Actions `_reusable-claude.yml` et disponibles selon les besoins de chaque agent.

---

## Matrice des Serveurs MCP

| Serveur | Package / Nom | Usage | Agents | Secret(s) Requis | Status |
|---------|--------------|-------|--------|-------------------|--------|
| **GitHub** | `@anthropic-ai/github-mcp-server` | GitHub API (issues, PRs, fichiers, repos) | Tous | `GITHUB_TOKEN` | Actif |
| **Firecrawl** | `@anthropic-ai/firecrawl-mcp-server` | Web scraping RGPD-compliant | [[agents/scout-memory\|Scout]], [[agents/iris-memory\|Iris]] | `FIRECRAWL_API_KEY` | Actif |
| **Google Ads** | `google-ads` MCP | Google Ads API (campagnes, metriques, reporting) | [[agents/nexus-memory\|Nexus]] | `GOOGLE_ADS_DEVELOPER_TOKEN`, `GOOGLE_ADS_CLIENT_ID`, `GOOGLE_ADS_CLIENT_SECRET`, `GOOGLE_ADS_REFRESH_TOKEN`, `GOOGLE_ADS_ACCOUNT_ID` | Non configure |
| **Google Analytics** | `google-analytics` MCP | Analytics reporting (sessions, conversions, audiences) | [[agents/lumen-memory\|Lumen]] | GA credentials | Non configure |
| **HubSpot** | `hubspot` MCP | CRM operations (contacts, deals, workflows) | [[agents/aria-memory\|Aria]] | `HUBSPOT_API_KEY` | Non configure |
| **Lemlist** | `lemlist` MCP | Email sequences (campagnes, leads, stats) | [[agents/iris-memory\|Iris]], [[agents/aria-memory\|Aria]] | `LEMLIST_API_KEY` | Non configure |
| **Memory** | `memory` MCP | Knowledge graph persistant (entites, relations, observations) | Tous | -- (local) | Actif |
| **Filesystem** | `filesystem` MCP | Operations fichiers (lecture, ecriture, navigation) | Tous | -- (local) | Actif |
| **Playwright** | `playwright` MCP | Browser automation (navigation, scraping, screenshots) | [[agents/scout-memory\|Scout]] | -- (local) | Actif |
| **Sequential Thinking** | `sequential-thinking` MCP | Raisonnement structure, decomposition de problemes | Tous | -- (local) | Actif |

---

## Configuration Type dans un Workflow

La configuration MCP est passee aux agents Claude Code via le parametre `mcpServers` dans le workflow GitHub Actions.

### Exemple : Configuration GitHub MCP

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/github-mcp-server"],
      "env": {
        "GITHUB_TOKEN": "${{ secrets.GITHUB_TOKEN }}"
      }
    }
  }
}
```

### Exemple : Configuration Firecrawl MCP

```json
{
  "mcpServers": {
    "firecrawl": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/firecrawl-mcp-server"],
      "env": {
        "FIRECRAWL_API_KEY": "${{ secrets.FIRECRAWL_API_KEY }}"
      }
    }
  }
}
```

### Exemple : Configuration Google Ads MCP

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "npx",
      "args": ["-y", "google-ads-mcp-server"],
      "env": {
        "GOOGLE_ADS_DEVELOPER_TOKEN": "${{ secrets.GOOGLE_ADS_DEVELOPER_TOKEN }}",
        "GOOGLE_ADS_CLIENT_ID": "${{ secrets.GOOGLE_ADS_CLIENT_ID }}",
        "GOOGLE_ADS_CLIENT_SECRET": "${{ secrets.GOOGLE_ADS_CLIENT_SECRET }}",
        "GOOGLE_ADS_REFRESH_TOKEN": "${{ secrets.GOOGLE_ADS_REFRESH_TOKEN }}",
        "GOOGLE_ADS_ACCOUNT_ID": "${{ secrets.GOOGLE_ADS_ACCOUNT_ID }}"
      }
    }
  }
}
```

### Exemple : Configuration Multiple (Agent Scout)

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/github-mcp-server"],
      "env": { "GITHUB_TOKEN": "${{ secrets.GITHUB_TOKEN }}" }
    },
    "firecrawl": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/firecrawl-mcp-server"],
      "env": { "FIRECRAWL_API_KEY": "${{ secrets.FIRECRAWL_API_KEY }}" }
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/memory-mcp-server"]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/filesystem-mcp-server"],
      "env": { "ALLOWED_DIRS": "/tmp" }
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/playwright-mcp-server"]
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/sequential-thinking-mcp-server"]
    }
  }
}
```

---

## Details par Serveur

### GitHub MCP

| Outil MCP | Description | Exemple d'Usage |
|-----------|-------------|-----------------|
| `create_issue` | Creer une issue GitHub | Agent cree une issue pour un bug detecte |
| `get_issue` | Lire une issue | Agent recupere les instructions d'une tache |
| `list_issues` | Lister les issues | Agent verifie le backlog |
| `create_pull_request` | Creer une PR | Forge soumet du code |
| `get_file_contents` | Lire un fichier du repo | Agent lit la config ou la doc |
| `push_files` | Pousser des fichiers | Agent met a jour des fichiers |

### Firecrawl MCP

| Outil MCP | Description | Exemple d'Usage |
|-----------|-------------|-----------------|
| `firecrawl_scrape` | Scraper une page web | Scout extrait des donnees d'un site prospect |
| `firecrawl_crawl` | Crawler un site complet | Scout indexe un site pour analyse |
| `firecrawl_search` | Recherche web | Scout cherche des informations sectorielles |
| `firecrawl_map` | Mapper la structure d'un site | Scout analyse l'arborescence d'un site |

> [!warning] Regles Google Ads MCP
> Le serveur Google Ads MCP a des regles critiques a respecter imperativement :
> - **JAMAIS `.type` dans les `conditions`** des requetes GAQL (provoque erreur + annulation en cascade)
> - **JAMAIS d'appels paralleles** (si 1 echoue, tous sont annules)
> - **JAMAIS `metrics.optimization_score` avec des segments de date**
> - **JAMAIS de metriques sur `ad_group_criterion`** -- utiliser `keyword_view` a la place
> - Toujours executer les requetes **sequentiellement**, une a la fois
>
> Voir le fichier `google-ads-mcp.md` dans la memoire projet pour les details complets.

### Memory MCP

| Outil MCP | Description | Exemple d'Usage |
|-----------|-------------|-----------------|
| `create_entities` | Creer des entites dans le knowledge graph | Agent stocke un nouveau concept |
| `add_observations` | Ajouter des observations a une entite | Agent enrichit une entite existante |
| `create_relations` | Creer des relations entre entites | Agent lie deux concepts |
| `search_nodes` | Rechercher dans le graphe | Agent retrouve une information |
| `read_graph` | Lire le graphe complet | Agent charge le contexte |

### HubSpot MCP

| Outil MCP | Description | Exemple d'Usage |
|-----------|-------------|-----------------|
| `hubspot-search-objects` | Rechercher des contacts/deals | Aria cherche des doublons |
| `hubspot-batch-create-objects` | Creer des contacts en batch | Aria importe des leads |
| `hubspot-batch-update-objects` | Mettre a jour en batch | Aria met a jour les scores |
| `hubspot-list-workflows` | Lister les workflows | Aria verifie la configuration |
| `hubspot-list-properties` | Lister les proprietes | Aria valide le schema |

---

## Regles d'Utilisation

> [!important] Skills avant MCP
> Avant d'utiliser un serveur MCP directement, les agents DOIVENT verifier `skills/registry.json` (voir [[tech/skills-registry]]). Si un **skill valide** existe pour l'operation, il doit etre utilise a la place du MCP.

### Avantages des Skills vs MCP Direct

| Critere | MCP Direct | Skill Valide |
|---------|-----------|--------------|
| Tokens consommes | Eleve (handshake + tool calls) | Faible (script direct) |
| Temps d'execution | Lent (demarrage serveur) | Rapide (script Python) |
| Fiabilite | Dependant du serveur | Teste et valide |
| Cout | Tokens Claude + API | API seulement |

### Hierarchie d'Utilisation

1. **Skill valide** (`skills/validated/`) --> toujours prefere
2. **Skill candidat** (`skills/candidates/`) --> acceptable si urgent
3. **MCP direct** --> uniquement si aucun skill n'existe

---

## Patterns MCP Detectes par Sage

[[agents/sage-memory|Sage]] collecte les patterns d'utilisation MCP dans les retrospectives des agents. Quand un pattern atteint **usage_count >= 5**, il devient candidat pour conversion en skill autonome.

| Pattern | Usage Count | Status | Skill Futur |
|---------|-------------|--------|-------------|
| `firecrawl_scrape` pour extraction prospect | 12 | **Converti** | `firecrawl_scrape.py` |
| `github.create_issue` pour taches agents | 8 | **Converti** | `github_create_issue.py` |
| `hubspot.batch_create` pour import leads | 3 | Candidat | `hubspot_batch_create.py` |
| `lemlist.add_lead_to_campaign` | 1 | Observe | -- |

Voir [[tech/skills-registry]] pour le registre complet et le cycle de vie des skills.

---

## Configuration dans _reusable-claude.yml

Le fichier `.github/workflows/_reusable-claude.yml` centralise la configuration MCP pour tous les workflows agents.

```yaml
# Extrait simplifie
jobs:
  claude-agent:
    steps:
      - name: Run Claude Code
        env:
          ANTHROPIC_API_KEY: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          MCP_SERVERS: |
            {
              "github": { ... },
              "memory": { ... },
              "filesystem": { ... },
              "sequential-thinking": { ... }
            }
```

Chaque workflow agent peut **etendre** cette configuration de base avec des serveurs MCP specifiques a son role.

---

## Securite

| Mesure | Detail |
|--------|--------|
| Secrets GitHub | Tous les API keys sont stockes dans GitHub Secrets (voir [[operations/secrets-matrix]]) |
| Acces minimal | Chaque agent n'a acces qu'aux MCP necessaires a son role |
| Pas de secrets en clair | Jamais de clef API dans le code ou les logs |
| Rotation | Voir [[security/access-control]] pour la politique de rotation |
| Audit | Les appels MCP sont logges dans les artefacts GitHub Actions |

---

## Liens

- [[tech/infrastructure]] -- Infrastructure globale du systeme
- [[tech/integrations]] -- Integrations externes
- [[tech/skills-registry]] -- Registry des skills (MCP --> scripts)
- [[agents/sage-memory]] -- Sage (detection patterns MCP)
- [[operations/secrets-matrix]] -- Matrice des secrets et status
- [[security/access-control]] -- Politique de securite et acces

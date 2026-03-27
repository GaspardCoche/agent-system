# Agent System

Systeme multi-agents autonome orchestre via GitHub Actions et Claude Code. Chaque agent a un role specialise, une memoire persistante (Obsidian Vault), et un protocole de communication standardise.

## Architecture

```
GitHub Issues / Cron / Manual
         |
    Orchestrator ──── decompose la tache
         |
    +----+----+
    |         |
Researcher  Analyzer    (parallele)
    |         |
    +----+----+
         |
       Forge ──── implemente
         |
      Sentinel ──── teste & valide
         |
      Aggregate ──── rapport + notification
```

## Agents

| Agent | Role | Trigger |
|-------|------|---------|
| **Orchestrator** | Decompose, route, supervise | Issues, PRs, cron, manual |
| **Forge** | Implementation code | Dispatch |
| **Sentinel** | Tests & QA | Dispatch |
| **Iris** | Email triage & digest | Cron 7h30, manual |
| **Scout** | Veille web, enrichissement | Dispatch, manual |
| **Aria** | Lead generation, CRM | Dispatch, manual |
| **Nexus** | Audit Google Ads | Cron Lundi, manual |
| **Sage** | Auto-amelioration systeme | Cron Dimanche, manual |
| **Ralph** | Automatisation, webhooks | repository_dispatch |
| **Lumen** | Analyse donnees & insights | Dispatch |

## Vault (Knowledge Base)

Le vault Obsidian dans `docs/vault/` est la memoire persistante du systeme. Chaque agent :
1. **Lit** `INDEX.md` + son fichier memoire au debut de chaque run
2. **Ecrit** ses apprentissages apres chaque run
3. Le knowledge graph est automatiquement reconstruit via `vault-sync.yml`

### Structure du Vault

```
docs/vault/
  INDEX.md                    -- Hub central, point d'entree
  business/
    vision.md                 -- Vision & mission
    strategy.md               -- Strategie business
    roadmap.md                -- Roadmap & priorites
  prospects/
    pipeline.md               -- Pipeline leads (Scout + Aria)
  campaigns/
    google-ads.md             -- Etat campagnes (Nexus)
  operations/
    daily-digest.md           -- Digest email (Iris)
    decisions.md              -- Decisions d'architecture
    runbooks.md               -- Procedures operationnelles
    kpis.md                   -- Metriques systeme
  content/
    social-media.md           -- Strategie contenu
    brand-voice.md            -- Ton editorial
    editorial-calendar.md     -- Calendrier editorial
  tech/
    infrastructure.md         -- Architecture technique
    integrations.md           -- APIs & MCP servers
  security/
    access-control.md         -- Controle d'acces
  agents/
    dispatch-log.md           -- Journal orchestrations
    nexus-memory.md           -- Memoire Nexus
    iris-memory.md            -- Memoire Iris
    scout-memory.md           -- Memoire Scout
    sage-memory.md            -- Memoire Sage
    forge-memory.md           -- Memoire Forge
    sentinel-memory.md        -- Memoire Sentinel
    ralph-memory.md           -- Memoire Ralph
    lumen-memory.md           -- Memoire Lumen
    aria-memory.md            -- Memoire Aria
  templates/
    vault-note.md             -- Template note generique
    agent-memory.md           -- Template memoire agent
```

### Ouvrir dans Obsidian

```bash
open -a Obsidian docs/vault
```

Obsidian affiche le graph interactif des connexions entre les notes (Cmd+Shift+G).

## Dashboard

Dashboard web deploye sur GitHub Pages (https://gaspardcoche.github.io/agent-system/) avec 4 onglets :

- **Runs** -- Historique des runs, lancement d'agents, rapports inline
- **Status** -- Sante des agents, secrets configures/manquants
- **Agents** -- Documentation, inputs, instructions de setup
- **Graph** -- Knowledge graph interactif (D3.js)

## Skills

Systeme de skills qui transforme les patterns MCP frequents en scripts Python autonomes :

| Skill | Description |
|-------|-------------|
| `firecrawl_scrape` | Scrape URL -> markdown |
| `github_create_issue` | Creer/commenter issues |
| `gemini_analyze` | Analyse gros fichiers via Gemini |
| `slack_notify` | Notification Slack formatee |

Les skills sont geres par **Sage** qui analyse les retrospectives et propose de nouveaux skills.

## Setup

### Prerequis

- GitHub repo avec Actions activees
- Secrets GitHub configures (voir ci-dessous)
- GitHub Pages active sur le repo (deploy depuis `docs/`)

### Secrets GitHub requis

| Secret | Agent(s) | Notes |
|--------|---------|-------|
| `CLAUDE_CODE_OAUTH_TOKEN` | Tous | `claude setup-token` en local |
| `GEMINI_API_KEY` | Lumen, Sage | Google AI Studio |
| `GMAIL_TOKEN_JSON` | Iris | OAuth Gmail |
| `GMAIL_USER_EMAIL` | Iris | Adresse Gmail |
| `FIRECRAWL_API_KEY` | Scout | firecrawl.dev |
| `HUBSPOT_API_KEY` | Aria | HubSpot private app |
| `FULLENRICH_API_KEY` | Aria | fullenrich.com |
| `GOOGLE_ADS_DEVELOPER_TOKEN` | Nexus | Google Ads API Center |
| `GOOGLE_ADS_CLIENT_ID` | Nexus | Google Cloud OAuth |
| `GOOGLE_ADS_CLIENT_SECRET` | Nexus | Google Cloud OAuth |
| `GOOGLE_ADS_REFRESH_TOKEN` | Nexus | OAuth flow |
| `SLACK_WEBHOOK_URL` | Notifications | Slack Incoming Webhook |

### Lancer un agent

```bash
# Via GitHub CLI
gh workflow run orchestrator.yml -f task_description="Description de la tache"

# Agent specifique
gh workflow run nexus.yml -f report_type=weekly_audit -f dry_run=true

# Via le dashboard GitHub Pages
# Ouvrir https://gaspardcoche.github.io/agent-system/ -> Config (PAT) -> Run agent
```

### Rebuild le knowledge graph

```bash
python3 .github/scripts/vault_builder.py --vault-dir docs/vault --output docs/data/graph.json
```

## Protocole de communication inter-agents

Chaque agent lit sa tache depuis `/tmp/agent_task.json` et ecrit ses resultats dans `/tmp/agent_result.json` :

```json
{
  "agent": "<nom>",
  "task_id": "<id>",
  "status": "complete|failed|needs_retry|pending_approval",
  "summary": "<max 150 mots>",
  "artifacts": ["<filepath>"],
  "next_agent": "<nom ou null>",
  "retrospective": {
    "what_worked": "...",
    "what_failed": "...",
    "mcp_patterns": ["<tool:pattern:count>"],
    "improvement_suggestion": "..."
  }
}
```

## Self-Improvement

1. Chaque agent remplit `retrospective` dans son resultat JSON
2. **Sage** lit toutes les retrospectives chaque dimanche
3. Sage propose des ameliorations de prompts via PR
4. Les erreurs repetees vont dans `memory/lessons_learned.md`
5. Les patterns MCP frequents deviennent des skills valides

## Fichiers cles

| Fichier | Role |
|---------|------|
| `CLAUDE.md` | Instructions globales pour tous les agents |
| `.github/workflows/_reusable-claude.yml` | Base workflow commune |
| `.github/scripts/vault_builder.py` | Genere le knowledge graph |
| `.github/scripts/generate_report.py` | Genere les rapports |
| `docs/index.html` | Dashboard complet |
| `docs/data/agents.json` | Config agents pour le dashboard |
| `skills/registry.json` | Registry des skills |
| `memory/lessons_learned.md` | Erreurs a ne pas repeter |

## Licence

Projet prive.

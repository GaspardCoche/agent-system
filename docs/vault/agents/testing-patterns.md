---
title: "Patterns de Test -- Validation des Agents"
id: agents-testing-patterns
type: agent
tags: [agent, testing, validation, qa, sentinel, patterns]
agents: [sentinel, sage]
created: 2026-03-27
updated: 2026-03-27
---

# Patterns de Test -- Validation des Agents

Reference complete pour la validation des agents du systeme. Utilise par [[agents/sentinel-memory|Sentinel]] pour les checks automatises et par [[agents/sage-memory|Sage]] pour les revues de qualite.

---

## Niveaux de test

Chaque agent doit passer les 4 niveaux de validation avant d'etre considere comme stable. Voir [[agents/creation-guide]] pour le processus complet de creation.

> [!info] Niveau 1 -- Smoke Test (avant premier deploy)
> - L'agent demarre sans erreur
> - Le prompt est lu correctement depuis `agent_prompts/{agent}.md`
> - Le vault est accessible ([[INDEX|INDEX.md]] + [[agents/{agent}-memory|memory]])
> - Le format de sortie `/tmp/agent_result.json` est valide (voir [[tech/data-schemas]])
> - La retrospective est remplie (champs non-vides)

> [!info] Niveau 2 -- Dry Run (avant mise en production)
> - `DRY_RUN=true` → aucune modification externe (pas de commit, pas de notification)
> - Les artifacts attendus sont produits (rapports, fichiers, JSON)
> - Le summary est coherent avec la tache assignee
> - Les `mcp_patterns` sont loggues dans la retrospective
> - La memoire agent est mise a jour (`docs/vault/agents/{agent}-memory.md`)

> [!info] Niveau 3 -- Integration (en production)
> - **Chaining** : l'agent suivant dans la chaine recoit les bons artifacts (voir [[agents/communication-protocol]])
> - **Vault update** : commit effectue correctement via `obsidian-git`
> - **Report generation** : rapport genere dans `docs/reports/` avec format attendu
> - **Dashboard update** : `runs.json` mis a jour avec le resultat du run
> - **Slack notification** : envoyee si `SLACK_WEBHOOK_URL` configure

> [!info] Niveau 4 -- Regression (continu)
> - L'agent ne refait pas une erreur deja documentee dans [[agents/error-patterns]]
> - Le taux de succes reste **>90%** (suivi dans [[operations/kpis]])
> - Le cout en tokens ne depasse pas le budget alloue dans [[tech/token-budget]]
> - Les retrospectives restent informatives (pas de contenu generique/repetitif)

---

## Checklist de validation par agent

Table de reference pour valider qu'un agent est correctement configure dans le systeme. Remplacer `{agent}` par le nom de l'agent (ex: `sage`, `iris`, `nexus`).

| Check | Commande | Expected |
|-------|---------|----------|
| Prompt exists | `ls agent_prompts/{agent}.md` | File exists |
| Memory exists | `ls docs/vault/agents/{agent}-memory.md` | File exists |
| Workflow exists | `ls .github/workflows/{agent}.yml` | File exists |
| agents.json entry | `jq '.[] \| select(.name=="{agent}")' docs/data/agents.json` | Entry found |
| CLAUDE.md roster | `grep {agent} CLAUDE.md` | Agent listed |
| Dry run succeeds | `gh workflow run {agent}.yml -f dry_run=true` | Status: success |
| Result JSON valid | Check `/tmp/agent_result.json` schema | Valid JSON |
| Retrospective filled | Check retrospective fields non-empty | All filled |

> [!warning] Ordre important
> Executer les checks **dans l'ordre du tableau**. Si un check echoue, corriger avant de passer au suivant. Un prompt manquant rend le dry run inutile.

---

## Health Check Workflow

Le workflow `health-check.yml` (voir [[operations/agent-workflows]]) valide automatiquement l'integrite du systeme :

### Secrets valides (15 secrets requis)

```bash
# Liste des secrets attendus
ANTHROPIC_API_KEY
GOOGLE_ADS_DEVELOPER_TOKEN
GOOGLE_ADS_CLIENT_ID
GOOGLE_ADS_CLIENT_SECRET
GOOGLE_ADS_REFRESH_TOKEN
GOOGLE_ANALYTICS_CREDENTIALS
HUBSPOT_ACCESS_TOKEN
SLACK_WEBHOOK_URL
GITHUB_TOKEN  # auto-fourni
LEMLIST_API_KEY
GEMINI_API_KEY
NETLIFY_AUTH_TOKEN
NETLIFY_SITE_ID
OBSIDIAN_GIT_TOKEN
FIRECRAWL_API_KEY
```

### Accessibilite des MCPs

Verifie que chaque [[tech/mcp-servers|serveur MCP]] repond correctement :

| MCP | Test | Timeout |
|-----|------|---------|
| `github` | `list_issues` | 10s |
| `google-ads` | `list_accessible_customers` | 15s |
| `hubspot` | `hubspot-get-user-details` | 10s |
| `filesystem` | `list_directory` | 5s |
| `memory` | `read_graph` | 5s |

### Derniere date de run par agent

```bash
# Verifie que chaque agent a run dans sa fenetre attendue
gh run list --workflow={agent}.yml --limit 1 --json createdAt \
  --repo GaspardCoche/agent-system
```

> [!tip] Seuils d'alerte
> - Agent quotidien (Iris) : alerte si dernier run > 36h
> - Agent hebdomadaire (Sage, Nexus) : alerte si dernier run > 10 jours
> - Agent variable (Forge, Sentinel) : pas d'alerte temporelle

---

## Sentinel -- Checks automatises sur PRs

[[agents/sentinel-memory|Sentinel]] execute automatiquement les checks suivants sur chaque Pull Request :

### Lint YAML workflows

```bash
# Valide la syntaxe de tous les workflows
for f in .github/workflows/*.yml; do
  python3 -c "import yaml; yaml.safe_load(open('$f'))" || echo "FAIL: $f"
done
```

### Validate JSON schemas

```bash
# Valide agents.json, runs.json, graph.json
python3 -c "
import json, sys
for f in ['docs/data/agents.json', 'docs/data/runs.json', 'docs/data/graph.json']:
    try:
        json.load(open(f))
        print(f'OK: {f}')
    except Exception as e:
        print(f'FAIL: {f} -- {e}')
        sys.exit(1)
"
```

### Check for security issues

- Aucun secret en clair dans le code (`grep -r "sk-ant-" .` doit retourner vide)
- Aucun token dans les fichiers committes
- Permissions minimales dans les workflows (`permissions:` explicite)

### Run affected tests

- Si un prompt est modifie → dry run de l'agent concerne
- Si un workflow est modifie → validation YAML + dry run
- Si un schema est modifie → validation JSON + check des dependances

---

## Matrice de couverture

| Agent | Niveau 1 | Niveau 2 | Niveau 3 | Niveau 4 |
|-------|----------|----------|----------|----------|
| Orchestrator | ok | ok | ok | actif |
| [[agents/sage-memory\|Sage]] | ok | ok | ok | actif |
| [[agents/nexus-memory\|Nexus]] | ok | ok | ok | actif |
| [[agents/iris-memory\|Iris]] | ok | ok | ok | actif |
| [[agents/scout-memory\|Scout]] | ok | ok | ok | actif |
| [[agents/forge-memory\|Forge]] | ok | ok | en cours | -- |
| [[agents/sentinel-memory\|Sentinel]] | ok | ok | en cours | -- |
| [[agents/lumen-memory\|Lumen]] | ok | ok | en cours | -- |
| [[agents/ralph-memory\|Ralph]] | ok | ok | en cours | -- |
| [[agents/aria-memory\|Aria]] | ok | ok | en cours | -- |

---

## Voir aussi

- [[agents/creation-guide]] -- Processus complet de creation d'un agent
- [[agents/error-patterns]] -- Catalogue des erreurs connues et corrections
- [[agents/communication-protocol]] -- Protocole de communication inter-agents
- [[tech/token-budget]] -- Budget tokens et couts par agent
- [[operations/kpis]] -- Metriques de succes et suivi

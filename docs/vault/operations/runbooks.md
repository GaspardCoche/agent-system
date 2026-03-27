---
title: Runbooks Operationnels
id: operations-runbooks
type: operations
tags: [runbooks, procedures, troubleshooting, operations]
updated: 2026-03-27
---

# Runbooks Operationnels

*Lie a [[INDEX]], [[tech/infrastructure]], [[operations/decisions]]*

> Procedures standard pour les operations courantes. A suivre par tout agent ou humain.

---

## Ajouter un nouveau secret GitHub

```bash
# 1. Via gh CLI
gh secret set SECRET_NAME --repo GaspardCoche/agent-system

# 2. Verifier
gh secret list --repo GaspardCoche/agent-system

# 3. Lancer le health check pour valider
gh workflow run health-check.yml --repo GaspardCoche/agent-system
```

---

## Declencher un agent manuellement

### Via GitHub CLI
```bash
# Orchestrator avec description
gh workflow run orchestrator.yml \
  --repo GaspardCoche/agent-system \
  -f task_description="Analyser les campagnes Google Ads"

# Agent specifique (ex: Nexus)
gh workflow run nexus.yml \
  --repo GaspardCoche/agent-system \
  -f report_type=weekly_audit \
  -f dry_run=true

# Sage (auto-amelioration)
gh workflow run sage.yml \
  --repo GaspardCoche/agent-system
```

### Via Dashboard Netlify
1. Ouvrir le dashboard -> onglet Runs
2. Cliquer sur la carte de l'agent souhaite
3. Remplir les inputs
4. Cliquer "Run"

### Via API (repository_dispatch)
```bash
curl -X POST \
  -H "Authorization: Bearer $(gh auth token)" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/GaspardCoche/agent-system/dispatches \
  -d '{"event_type":"run_scout","client_payload":{"sheet_id":"XXX"}}'
```

---

## Regenerer le token Claude OAuth

```bash
# 1. Regenerer en local
claude setup-token

# 2. Copier le token affiche
# 3. Mettre a jour le secret GitHub
gh secret set CLAUDE_CODE_OAUTH_TOKEN --repo GaspardCoche/agent-system

# 4. Verifier avec un run simple
gh workflow run sage.yml --repo GaspardCoche/agent-system
```

**Detection d'expiration :** `HTTP 401 Unauthorized` dans les logs Actions.

---

## Rebuild le knowledge graph

```bash
cd /Users/gaspardcoche/agent-system
python3 .github/scripts/vault_builder.py \
  --vault-dir docs/vault \
  --output docs/data/graph.json
```

Ou via workflow :
```bash
gh workflow run vault-sync.yml --repo GaspardCoche/agent-system
```

---

## Ajouter un nouveau fichier au Vault

1. Creer le fichier `.md` dans `docs/vault/<categorie>/`
2. Ajouter le frontmatter YAML :
   ```yaml
   ---
   title: Titre
   id: categorie-nom
   type: categorie
   tags: [tag1, tag2]
   agents: [agent1]
   updated: YYYY-MM-DD
   ---
   ```
3. Ajouter des `[[wikilinks]]` vers les fichiers lies
4. Mettre a jour `INDEX.md` avec le lien
5. Rebuild le graph : `python3 .github/scripts/vault_builder.py`
6. Commit et push

---

## Ajouter un nouvel agent

1. Creer le prompt dans `agent_prompts/<nom>.md`
2. Creer la memoire dans `docs/vault/agents/<nom>-memory.md`
3. Creer le workflow dans `.github/workflows/<nom>.yml` (ou utiliser `_reusable-claude.yml`)
4. Ajouter l'agent dans `docs/data/agents.json`
5. Mettre a jour `CLAUDE.md` (Agent Roster)
6. Mettre a jour `docs/vault/INDEX.md`
7. Rebuild le graph

---

## Troubleshooting

### Workflow echoue avec `startup_failure`
- Cause : YAML invalide ou `default: ""` sur un input workflow_call
- Fix : Utiliser `default: "none"` (jamais de chaine vide)

### Agent ne trouve pas son prompt
- Cause : Nom du fichier dans `agent_prompts/` ne correspond pas au `agent_role` passe
- Fix : Verifier que `agent_prompts/${{ inputs.agent_role }}.md` existe

### Dashboard n'affiche pas les runs
- Cause : `docs/data/runs.json` pas mis a jour ou vide
- Fix : Verifier que `generate_report.py` est appele avec `--dashboard-file docs/data/runs.json`

### Graph vide dans le dashboard
- Cause : `docs/data/graph.json` pas regenere apres ajout de fichiers vault
- Fix : Lancer `python3 .github/scripts/vault_builder.py`

---

*Mettre a jour quand une nouvelle procedure est etablie ou qu'un troubleshooting est resolu.*

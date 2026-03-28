---
title: Guide de Creation d'Agent
id: agents-creation-guide
type: agent
tags: [agent, creation, guide, workflow, prompt, howto]
agents: [sage, forge]
updated: 2026-03-28
---

# Guide de Creation d'Agent

*Lie a [[INDEX]] -- [[agents/prompt-engineering]] -- [[agents/communication-protocol]] -- [[agents/error-patterns]] -- [[agents/tool-matrix]]*

> [!info] Ce guide couvre la creation complete d'un agent, de la definition du role au premier run en production.
> **Chaque agent du systeme a ete cree en suivant ces etapes.** Les raccourcis menent inevitablement aux erreurs documentees dans [[agents/error-patterns]].

---

## Etape 1 -- Definir le role, le perimetre et les triggers

Avant d'ecrire une seule ligne de code, repondre a ces questions :

### 1.1 Quel probleme l'agent resout

| Question | Reponse attendue | Exemple (Scout) |
|----------|-----------------|-----------------|
| Quel probleme specifique ? | Description en 1 phrase | "Enrichir les leads depuis des sources web en respectant le RGPD" |
| Existe-t-il deja un agent pour ca ? | Verifier [[INDEX]] section Memoire Agents | Non, Aria fait le CRM mais pas le scraping |
| Peut-on etendre un agent existant ? | Souvent preferable a un nouvel agent | Non, le scraping est un domaine separe |
| Quelle est la frequence ? | Quotidien, hebdo, a la demande | A la demande (dispatch) |
| Quel est le cout token estime ? | Simple (<50K), Moyen (<150K), Complexe (>150K) | Moyen (~100K par run) |

### 1.2 Inputs et Outputs

```
Inputs:
  - Source de donnees (Sheet ID, URL, fichier CSV, issue GitHub)
  - Parametres de configuration (colonnes, filtres, limites)
  - Contexte vault (fichiers memoire, regles metier)

Outputs:
  - Artifacts generes (fichiers, rapports, PRs)
  - Mise a jour vault (memoire agent, fichiers domaine)
  - Result JSON (format [[agents/communication-protocol]])
```

> [!warning] Tout agent DOIT produire un `/tmp/agent_result.json` conforme au protocole de communication. Sans ca, l'orchestrateur ne peut pas chainer.

### 1.3 Triggers

| Type de trigger | Quand l'utiliser | Configuration |
|----------------|-----------------|---------------|
| `workflow_dispatch` | Lancement manuel depuis GitHub Actions | `on: workflow_dispatch` avec inputs |
| `repository_dispatch` | Appel par un autre agent via Ralph | `on: repository_dispatch` avec `types: [agent-name]` |
| `schedule` | Execution periodique (cron) | `on: schedule` avec expression cron |
| `pull_request` | Reaction a une PR (Sentinel, Forge) | `on: pull_request` avec filtres `paths:` |
| `issues` | Reaction a une issue (Dispatch) | `on: issues` avec filtres `types: [labeled]` |

> [!tip] La plupart des agents utilisent `workflow_dispatch` + `repository_dispatch`. Le schedule est reserve a Iris (quotidien) et Sage (hebdo).

---

## Etape 2 -- Creer le prompt dans `agent_prompts/<nom>.md`

Le prompt est le cerveau de l'agent. Sa qualite determine directement la qualite des outputs.

### 2.1 Structure obligatoire

Voir [[agents/prompt-engineering]] pour le guide complet. Le prompt DOIT contenir ces sections dans cet ordre :

```markdown
# {Nom de l'Agent}

## Role
Tu es {nom}, l'agent {role} du systeme multi-agents.
{Description precise en 2-3 phrases.}

## Contexte Systeme
- Repo: GaspardCoche/agent-system
- Vault: docs/vault/ (knowledge graph persistant)
- Skills: skills/registry.json
- Dashboard: https://gaspardcoche.github.io/agent-system/

## Protocole Vault (OBLIGATOIRE)
1. Lire docs/vault/INDEX.md
2. Lire docs/vault/agents/{nom}-memory.md
3. Lire les fichiers vault pertinents a la tache
4. Apres execution: mettre a jour ta memoire

## Outils Disponibles
- {liste des MCPs et tools autorises -- voir [[agents/tool-matrix]]}
- TOUJOURS verifier skills/registry.json avant d'utiliser un MCP

## Format de Sortie
Ecrire dans /tmp/agent_result.json:
{schema JSON -- voir [[agents/communication-protocol]]}

## Contraintes
- DRY_RUN: si true, preview seulement
- Max {N} turns (3 simple / 8 moyen / 12 complexe)
- Budget tokens: {estimation}
- Ne jamais marquer complete sans artifacts

## Exemples
{2-3 exemples concrets de taches et reponses attendues}
```

### 2.2 Regles critiques du prompt

> [!danger] Le prompt DOIT inclure les 3 lectures vault suivantes, sinon l'agent demarre sans contexte :
> 1. Lecture de `INDEX.md`
> 2. Lecture de la memoire agent `agents/{nom}-memory.md`
> 3. Lecture des fichiers vault pertinents a la tache

- Les outils autorises doivent etre **specifiques** -- ne jamais donner acces a tous les MCPs
- Les exemples sont essentiels -- sans eux, l'agent improvise et consomme plus de tokens
- La section Contraintes evite les depassements de budget et les runs infinis

### 2.3 Validation du prompt

Avant de passer a l'etape suivante, verifier :

- [ ] Le prompt fait moins de 2000 tokens (au-dela, l'agent perd le focus)
- [ ] Chaque section est presente et non vide
- [ ] Les outils listes correspondent a [[agents/tool-matrix]]
- [ ] Au moins 2 exemples sont fournis
- [ ] Le format de sortie JSON est complet et valide
- [ ] Les contraintes incluent `DRY_RUN`, `max_turns`, et le budget tokens

---

## Etape 3 -- Creer la memoire dans `docs/vault/agents/<nom>-memory.md`

### 3.1 Utiliser le template

Copier le template [[templates/agent-memory]] et remplacer les variables :

```bash
cp docs/vault/templates/agent-memory.md docs/vault/agents/<nom>-memory.md
```

Remplacer :
- `{{Agent}}` par le nom de l'agent (ex: Scout)
- `{{agent}}` par le nom en minuscules (ex: scout)
- `{{date}}` par la date du jour (format YYYY-MM-DD)

### 3.2 Sections de la memoire

| Section | Contenu | Mise a jour |
|---------|---------|------------|
| **Configuration** | Status, version prompt, derniere execution | A chaque run |
| **Patterns decouverts** | Patterns recurrents detectes (utiles pour skills) | Quand un pattern est identifie |
| **Historique des runs** | Date, type, resume, run ID | A chaque run |
| **Erreurs rencontrees** | Date, erreur, resolution | A chaque erreur |

### 3.3 Initialisation

Le fichier memoire doit etre cree avec des valeurs initiales vides (les `--` du template). L'agent le remplira lors de son premier run.

> [!note] La memoire est la source de verite pour l'etat de l'agent. Si elle est corrompue ou perdue, l'agent perd tout son contexte accumule. Toujours commiter les mises a jour memoire.

---

## Etape 4 -- Creer le workflow dans `.github/workflows/<nom>.yml`

### Option A : Utiliser `_reusable-claude.yml` (recommande)

Pour les agents simples a moyens, utiliser le workflow reutilisable :

```yaml
name: "Agent -- {Nom}"

on:
  workflow_dispatch:
    inputs:
      dry_run:
        description: "Dry run (preview only)"
        required: false
        default: "false"
        type: choice
        options: ["true", "false"]
      task:
        description: "Tache a executer"
        required: false
        default: "none"
        type: string
  repository_dispatch:
    types: [{nom}]

jobs:
  run-agent:
    uses: ./.github/workflows/_reusable-claude.yml
    with:
      agent_role: "{nom}"
      task: ${{ github.event.inputs.task || github.event.client_payload.task || 'default task description' }}
      dry_run: ${{ github.event.inputs.dry_run || github.event.client_payload.dry_run || 'false' }}
      max_turns: 8
      allowed_tools: "Bash,Read,Write,Edit,Glob,Grep,mcp__github__*,mcp__filesystem__*"
    secrets: inherit
```

> [!warning] `default: ""` (chaine vide) sur un input `workflow_call` provoque un `startup_failure`. Toujours utiliser `default: "none"` ou une valeur non vide. Voir [[agents/error-patterns]] erreur #1.

### Option B : Workflow standalone

Pour les agents avec des steps custom (Nexus, Iris), creer un workflow complet :

```yaml
name: "Agent -- {Nom}"

on:
  workflow_dispatch:
    inputs:
      dry_run:
        description: "Dry run"
        required: false
        default: "false"
        type: choice
        options: ["true", "false"]
  repository_dispatch:
    types: [{nom}]

permissions:
  contents: write
  issues: write
  pull-requests: write

jobs:
  run:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.PAT_TOKEN }}

      - name: Setup MCP config
        run: |
          # Creer .mcp.json avec les serveurs necessaires
          cat > .mcp.json << 'EOF'
          {
            "mcpServers": {
              "github": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "${{ secrets.PAT_TOKEN }}" }
              }
            }
          }
          EOF

      - name: Run Claude
        uses: anthropics/claude-code-action@v1
        with:
          model: claude-sonnet-4-20250514
          prompt_file: agent_prompts/{nom}.md
          max_turns: 8
          allowed_tools: "Bash,Read,Write,Edit"
        env:
          CLAUDE_CODE_OAUTH_TOKEN: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          DRY_RUN: ${{ github.event.inputs.dry_run || 'false' }}

      - name: Generate report
        if: always()
        run: |
          python3 .github/scripts/generate_report.py \
            --agent {nom} \
            --output-dir docs/reports \
            --dashboard-file docs/data/runs.json

      - name: Commit vault updates
        if: always()
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add docs/vault/ docs/reports/ docs/data/
          git diff --cached --quiet || git commit -m "vault: update {nom} memory"
          git pull --rebase origin main
          git push
```

### 4.1 Parametres cles

| Parametre | Valeur | Quand |
|-----------|--------|-------|
| `max_turns` | 3 | Agent simple (lecture seule, rapport) |
| `max_turns` | 8 | Agent moyen (lecture + ecriture limitee) |
| `max_turns` | 12 | Agent complexe (multi-step, self-correction) |
| `allowed_tools` | Specifique par agent | Voir [[agents/tool-matrix]] |
| `timeout-minutes` | 10-15 | Standard |
| `timeout-minutes` | 25-30 | Agents avec scraping ou API lentes |

### 4.2 Steps obligatoires

Tout workflow agent DOIT inclure ces steps :

1. **Checkout** avec `PAT_TOKEN` (pour pouvoir push)
2. **MCP config** si l'agent utilise des MCPs
3. **Claude action** avec prompt, max_turns, allowed_tools
4. **Report generation** (`generate_report.py`) -- toujours avec `if: always()`
5. **Vault commit** -- toujours avec `if: always()` et `git pull --rebase` avant push

> [!danger] Oublier `git pull --rebase origin main` avant le push provoque des rejets si un autre workflow a pousse entre-temps. Voir [[agents/error-patterns]] erreur #13.

---

## Etape 5 -- Enregistrer l'agent

### 5.1 Ajouter dans `docs/data/agents.json`

```json
{
  "name": "{nom}",
  "description": "Description courte de l'agent",
  "status": "active",
  "inputs": ["input1", "input2"],
  "outputs": ["output1"],
  "secrets": ["SECRET_1", "SECRET_2"],
  "trigger": "workflow_dispatch, repository_dispatch",
  "schedule": null,
  "max_turns": 8,
  "prompt_file": "agent_prompts/{nom}.md",
  "memory_file": "docs/vault/agents/{nom}-memory.md"
}
```

### 5.2 Ajouter dans `CLAUDE.md`

Dans la section **Agent Roster**, ajouter une ligne au tableau :

```markdown
| **{Nom}** | {Role} | {Trigger} |
```

### 5.3 Ajouter dans `docs/vault/INDEX.md`

Dans la section **Memoire Agents**, ajouter :

```markdown
- [[agents/{nom}-memory]] -- {Nom} : {description courte}
```

### 5.4 Ajouter dans Ralph (si dispatch necessaire)

Si l'agent doit etre declenche par d'autres agents via `repository_dispatch`, ajouter l'event type dans le workflow Ralph ou dans la configuration de l'orchestrateur :

```bash
# Exemple d'appel dispatch
gh api repos/GaspardCoche/agent-system/dispatches \
  -f event_type="{nom}" \
  -f client_payload='{"task":"...", "dry_run":"false"}'
```

---

## Etape 6 -- Tester

### 6.1 Test en dry_run

```bash
# Depuis GitHub Actions UI
# Lancer le workflow avec dry_run = true

# Ou via CLI
gh workflow run "{nom}.yml" -f dry_run=true -f task="test initial"
```

### 6.2 Checklist de verification

| Verification | Comment | Attendu |
|-------------|---------|---------|
| Le prompt lit le vault | Verifier les logs du run | Lectures INDEX.md + memoire presentes |
| La retrospective est remplie | Lire `/tmp/agent_result.json` dans les logs | Champs `what_worked`, `what_failed` non vides |
| La memoire est mise a jour | Verifier le commit vault | `docs/vault/agents/{nom}-memory.md` modifie |
| Le dashboard est a jour | Verifier `docs/data/runs.json` | Nouveau run ajoute |
| Les artifacts existent | Verifier les artifacts uploades | Fichiers presents et non vides |
| Le status est correct | Verifier `agent_result.json` | `complete` ou `failed` avec raison |

### 6.3 Debug

Si le run echoue :

1. Verifier les logs GitHub Actions step par step
2. Verifier que le YAML est valide : `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/{nom}.yml'))"`
3. Verifier que le prompt existe : `ls agent_prompts/{nom}.md`
4. Verifier les secrets : `gh secret list | grep SECRET_NAME`
5. Consulter [[agents/error-patterns]] pour les erreurs connues

---

## Etape 7 -- Documenter

### 7.1 Mettre a jour les fichiers vault

| Fichier | Quoi ajouter |
|---------|-------------|
| [[operations/agent-workflows]] | Nouvelle chaine d'agents si applicable |
| [[operations/secrets-matrix]] | Nouveaux secrets si applicable |
| [[tech/mcp-servers]] | Nouveaux serveurs MCP si applicable |
| [[agents/tool-matrix]] | Ligne pour le nouvel agent |
| [[security/access-control]] | Permissions du nouvel agent |

### 7.2 Rebuilder le graph

```bash
python3 .github/scripts/vault_builder.py
```

Cela regenere `docs/data/graph.json` pour que le dashboard et Obsidian reflectent les nouvelles connexions.

---

## Checklist finale

> [!success] Checklist de validation avant mise en production

| # | Etape | Fait |
|---|-------|------|
| 1 | Role, perimetre et triggers definis | [ ] |
| 2 | Prompt cree dans `agent_prompts/<nom>.md` | [ ] |
| 3 | Prompt respecte la structure obligatoire ([[agents/prompt-engineering]]) | [ ] |
| 4 | Memoire creee dans `docs/vault/agents/<nom>-memory.md` | [ ] |
| 5 | Workflow cree dans `.github/workflows/<nom>.yml` | [ ] |
| 6 | `allowed_tools` configure (principe du moindre privilege) | [ ] |
| 7 | Agent enregistre dans `docs/data/agents.json` | [ ] |
| 8 | Agent ajoute dans `CLAUDE.md` (Agent Roster) | [ ] |
| 9 | Agent ajoute dans `docs/vault/INDEX.md` | [ ] |
| 10 | Event dispatch ajoute dans Ralph (si necessaire) | [ ] |
| 11 | Test dry_run reussi | [ ] |
| 12 | Test reel reussi (retrospective remplie, memoire a jour) | [ ] |
| 13 | Documentation mise a jour (workflows, secrets, MCPs, tool-matrix) | [ ] |
| 14 | Graph rebuilde (`vault_builder.py`) | [ ] |

---

## Erreurs frequentes

> [!danger] Erreurs les plus courantes lors de la creation d'un agent

Voir [[agents/error-patterns]] pour la liste complete. Les plus frequentes :

| Erreur | Impact | Prevention |
|--------|--------|-----------|
| YAML invalide | `startup_failure` du workflow | Valider avec `python3 -c "import yaml; ..."` |
| `default: ""` sur input | Workflow ne demarre pas | Toujours `default: "none"` |
| Prompt sans lecture vault | Agent sans contexte, resultats pauvres | Suivre la structure obligatoire |
| `allowed_tools` trop large | Surconsommation tokens, actions non desirees | Configurer par agent via [[agents/tool-matrix]] |
| Pas de `git pull --rebase` | Push rejete | Toujours rebase avant push |
| Pas de `if: always()` sur report | Dashboard pas a jour si le run echoue | Ajouter sur report + commit steps |
| Memoire non creee | Agent crash au demarrage (fichier manquant) | Creer AVANT le premier run |

---

## Fichiers lies

- [[agents/prompt-engineering]] -- Comment ecrire et ameliorer les prompts
- [[agents/communication-protocol]] -- Format des inputs/outputs JSON
- [[agents/error-patterns]] -- Diagnostic et prevention des erreurs
- [[agents/tool-matrix]] -- Matrice des outils par agent
- [[operations/agent-workflows]] -- Chaines d'agents et orchestration
- [[operations/secrets-matrix]] -- Secrets GitHub necessaires
- [[tech/mcp-servers]] -- Configuration des serveurs MCP
- [[tech/skills-registry]] -- Skills valides (alternative aux MCPs)
- [[security/access-control]] -- Politique de controle d'acces
- [[templates/agent-memory]] -- Template de memoire agent

---

*Derniere mise a jour : 2026-03-28 -- Maintenu par [[agents/sage-memory|Sage]] et [[agents/forge-memory|Forge]]*

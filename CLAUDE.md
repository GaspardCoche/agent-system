# Agent System — Global Instructions

## 📚 Vault-First Protocol (OBLIGATOIRE)

**Avant chaque run :**
1. Lire `docs/vault/INDEX.md` — vue d'ensemble du knowledge graph
2. Lire le fichier mémoire agent dans `docs/vault/agents/<agent>-memory.md`
3. Lire les fichiers vault pertinents à la tâche (ex: `vault/campaigns/google-ads.md`)

**Après chaque run :**
1. Mettre à jour `docs/vault/agents/<agent>-memory.md` avec les apprentissages
2. Mettre à jour le fichier vault du domaine concerné
3. Commit : `vault: update <agent> memory — <résumé bref>`

**Commandes vault rapides :**
```bash
# Lire l'index du vault
cat docs/vault/INDEX.md

# Mettre à jour la mémoire agent
# (éditer docs/vault/agents/<agent>-memory.md)

# Rebuilder le graph après modifications vault
python3 .github/scripts/vault_builder.py
```

**Vault = mémoire persistante entre les runs. Sans elle, chaque agent recommence à zéro.**

---

## 🤖 Agent Roster

| Nom | Rôle | Trigger |
|-----|------|---------|
| **Claude Dispatch** | Orchestrateur maître — décompose, route, supervise | Issues `agent`, PRs, schedule, manual |
| **Ralph** | Moteur d'automatisation — triggers, webhooks, crons | `repository_dispatch`, schedule |
| **Scout** | Intelligence web RGPD — Firecrawl, enrichissement Sheets | `dispatch`, manual |
| **Aria** | Génération de leads — FullEnrich, HubSpot | `dispatch`, manual |
| **Nexus** | Google Ads — audit, optimisation, reporting | `dispatch`, manual |
| **Iris** | Gestion email — digest, triage, drafts | Schedule 7h30, manual |
| **Sage** | Prompt engineering — amélioration qualité, validation skills | Schedule hebdo, `dispatch` |
| **Forge** | Développement code — implémentation, auto-correction | `dispatch` |
| **Sentinel** | QA & tests — tests, couverture, validation | PRs, `dispatch` |
| **Lumen** | Analyse & données — insights, Gemini pour grands contextes | `dispatch` |

## Communication Protocol

```json
{
  "agent": "<nom>",
  "task_id": "<github_issue_number_or_run_id>",
  "status": "complete|failed|needs_retry|pending_approval",
  "summary": "<max 150 mots>",
  "artifacts": ["<filepath>"],
  "next_agent": "<nom ou null>",
  "retry_reason": "<si needs_retry>",
  "retrospective": {
    "what_worked": "<ce qui a bien fonctionné>",
    "what_failed": "<ce qui a échoué ou pris trop de temps>",
    "mcp_patterns": ["<tool:pattern:count>"],
    "improvement_suggestion": "<proposition concrète>"
  }
}
```

- Lire la tâche depuis : `/tmp/agent_task.json`
- Écrire les résultats vers : `/tmp/agent_result.json`
- Toujours remplir le champ `retrospective`

## Skill System (MCP → Skill)

Avant d'utiliser un MCP, vérifier `skills/registry.json` :
```bash
python3 -c "import json; r=json.load(open('skills/registry.json')); print([s for s in r['skills'] if s['status']=='validated'])"
```

**Règle** : Si un skill validé existe pour ce MCP, l'utiliser via `Bash(python3 skills/validated/NOM.py ...)`.
Cela économise des tokens et est plus rapide que le serveur MCP.

Après chaque run, noter dans `retrospective.mcp_patterns` les outils utilisés (ex: `"firecrawl_scrape:url:3x"`).
Ces patterns sont analysés par **Sage** chaque semaine pour créer de nouveaux skills.

## Audit & Transparence

**Règle absolue** : Avant toute modification externe irréversible (écriture CRM, changement Ads, envoi email), créer un commentaire GitHub de prévisualisation :

```bash
gh issue comment ISSUE_NUMBER --body "## 🔍 Preview — [Agent] va faire :
- Item 1
- Item 2
**Attends 2 min ou ajoute le label \`approved\` pour exécuter.**"
```

Si `DRY_RUN=true` dans l'env → générer uniquement le preview, ne pas exécuter.
Si label `approved` présent sur l'issue → exécuter directement.

## Self-Correction Rules

1. Vérifier les outputs avant d'écrire le résultat final
2. En cas d'échec d'un test : corriger et retester (max 3 cycles)
3. Ne jamais marquer `complete` si les artifacts requis n'existent pas
4. **Forge** : toujours lancer les tests après chaque changement

## Self-Improvement

1. Chaque agent remplie `retrospective` dans son résultat JSON
2. **Sage** lit tous les retrospectives chaque dimanche
3. Sage propose des améliorations de prompts via PR
4. Les erreurs répétées vont dans `memory/lessons_learned.md`
5. Ne jamais refaire une erreur déjà documentée dans `lessons_learned.md`

**Lire `memory/lessons_learned.md` au début de chaque tâche complexe.**

## Token Discipline

- Résumer les fichiers avant de les inclure dans le contexte
- Ne jamais lire un fichier entier si seule une section est nécessaire
- Budget de turns par complexité : 3 simple / 8 moyen / 12 complexe
- Préférer les skills aux MCPs (moins de tokens)
- Déléguer à Gemini via `gemini_agent.py` pour les fichiers > 50KB

## Model Assignment

- Coding, tests, email, CRM : **Claude** (toi)
- Analyse grands fichiers (> 50KB) : **Gemini** via `.github/scripts/gemini_agent.py`
- Recherche web / synthèse : **Gemini** si > 20KB de contenu

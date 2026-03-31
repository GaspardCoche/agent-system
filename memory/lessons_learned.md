# Lessons Learned

Erreurs et solutions documentées par les agents. **Lire au début de chaque tâche complexe.**

---

## 2026-03-20 — GitHub Actions `startup_failure`

**Problème :** Les workflows `workflow_call` (reusables) échouent avec `startup_failure` et 0 jobs exécutés.

**Contexte :** Survient lors de la validation du workflow par GitHub, avant même l'exécution. Aucun log disponible.

**Cause identifiée :** `default: ""` (chaîne vide) sur un input `workflow_call` est rejeté par le validateur GitHub.

**Solution :** Utiliser `default: "none"` (ou toute chaîne non-vide) et gérer la valeur dans la logique :
```yaml
inputs:
  allowed_tools:
    required: false
    type: string
    default: "none"  # ← jamais ""
```
Dans le script : `if [[ "$EXTRA" == "none" || -z "$EXTRA" ]]; then ...`

**Agents concernés :** Tous (pattern dans `_reusable-claude.yml`)

---

## 2026-03-20 — Inputs `workflow_call` : types

**Problème :** L'input `max_turns` de type `number` peut causer des comportements inattendus.

**Solution :** Utiliser `type: string` pour tous les inputs numériques dans `workflow_call`, passer les valeurs entre guillemets : `max_turns: "8"`.

---

## 2026-03-20 — `secrets: inherit` dupliqué

**Problème :** GitHub rejette un workflow avec `secrets: inherit` déclaré deux fois dans le même job.

**Erreur :** `(Line: 14, Col: 5): 'secrets' is already defined`

**Solution :** Ne déclarer `secrets: inherit` qu'une seule fois par job appelant un reusable workflow.

---

## 2026-03-20 — CLAUDE_CODE_OAUTH_TOKEN expiré (401)

**Problème :** `anthropics/claude-code-action@v1` retourne 401 malgré la présence du secret.

**Cause :** Le token OAuth Claude a une durée de vie limitée.

**Solution :** Régénérer via `claude setup-token` en local, puis mettre à jour le secret GitHub `CLAUDE_CODE_OAUTH_TOKEN`.

**Détection :** Log dans l'action : `"HTTP 401 Unauthorized"` ou `"Invalid bearer token"`.

---

## 2026-03-24 — Nexus : credentials Google Ads non configurés → mode template silencieux

**Problème :** Nexus s'exécute entièrement en mode template lorsque `GOOGLE_ADS_ACCOUNT_ID` ou les tokens OAuth sont absents, sans signaler d'erreur claire au démarrage.

**Contexte :** L'agent découvre les credentials manquants en cours d'exécution (lors des appels API), ce qui consomme des turns inutilement et produit un rapport template trompeur.

**Solution :** Pre-flight credential check ajouté dans `nexus.yml` (step `preflight`). Le champ `task.credentials_ok` est passé à l'agent qui adapte son comportement (template vs live). **CORRIGÉ le 2026-03-31.**

**Agents concernés :** Nexus (pattern applicable à tout agent dépendant de credentials externes)

---

## 2026-03-24 — Sage : `all_retrospectives.json` vide ≠ absence d'activité

**Problème :** Sage conclut "aucune activité cette semaine" quand `all_retrospectives.json` est vide, alors que la vraie cause peut être un échec de la pipeline de collecte d'artifacts.

**Contexte :** Le collecteur d'artifacts GitHub Actions peut échouer silencieusement si les runs précédents n'ont pas uploadé d'artifacts (retention expirée, upload-artifact raté, etc.).

**Solution :** Cross-check implémenté dans `sage.yml` : le collecteur utilise `gh run list` pour vérifier les runs agents de la semaine et compare avec les artifacts trouvés. Le champ `diagnostic.pipeline_status` (ok/broken/idle) est passé à l'agent. **CORRIGÉ le 2026-03-31.**

**Agents concernés :** Sage (workflow de collecte)

---

## 2026-03-29 — Iris : agent actif mais retrospective non collectée (2ème semaine consécutive)

**Problème :** Iris (Email Agent) a tourné avec succès le 2026-03-28 mais aucune rétrospective n'a été capturée dans `all_retrospectives.json`. Même constat la semaine précédente (2026-03-27).

**Cause racine identifiée :** Deux problèmes combinés :
1. La rétention des artifacts était à **1 jour** dans la plupart des workflows. Sage tourne le **dimanche** — les artifacts de la semaine étaient déjà expirés.
2. Le workflow `agent-tester.yml` (Sentinel sur PRs) n'avait **pas de step upload-artifact** du tout.
3. L'Email Agent multi-jobs uploadait les artifacts intermédiaires (raw-emails, triage) à 1 jour, donc inaccessibles à Sage.

**Solution appliquée (2026-03-31) :**
- Rétention des artifacts passée à **7 jours** dans tous les workflows : `_reusable-claude.yml`, `orchestrator.yml`, `email-agent.yml`, `scout.yml`, `aria.yml`, `agent-tester.yml`
- Step `upload-artifact` ajouté à `agent-tester.yml`
- Collecteur Sage amélioré avec cross-check `gh run list` et filtre `expired == false`

**Agents concernés :** Tous

---

## 2026-03-31 — Orchestrator : startup_failure et schedule sans issue/PR

**Problème 1 :** L'orchestrateur (cron lundi-vendredi 8h) a échoué avec `startup_failure` à son premier run. Aucun log disponible — GitHub rejette le workflow avant de créer les jobs.

**Cause racine identifiée :** Le bloc `permissions:` dans `_reusable-claude.yml` (workflow_call) provoque un `startup_failure` chez TOUS les callers. **GitHub Actions ne permet pas de definir `permissions` dans un reusable workflow** — elles doivent etre declarees cote caller.

**Solution :** Supprime `permissions` de `_reusable-claude.yml`, ajoute `permissions: {contents: write, pull-requests: write, issues: write}` dans chaque job caller : `orchestrator.yml` (run-researcher, run-analyzer, run-tester), `ralph.yml` (run-agent). **CORRIGE le 2026-03-31 — verifie en production.**

Egalement : simplifie la notification Slack, ajoute un concurrency group.

**Problème 2 :** L'aggregate job tentait de poster un commentaire sur `github.event.issue.number || github.event.pull_request.number` même sur un trigger `schedule` (où aucun des deux n'existe).

**Solution :** Ajouté `if: github.event.issue.number || github.event.pull_request.number` sur le step "Post final summary".

**Agents concernés :** Orchestrator

---

## 2026-03-31 — Firecrawl : 402 Payment Required sur toutes les sources

**Problème :** Le secret `FIRECRAWL_API_KEY` est configuré mais l'API retourne 402 sur toutes les sources d'actualités IA (Anthropic, OpenAI, etc.).

**Cause :** Compte Firecrawl ayant dépassé son quota ou sans forfait actif.

**Impact :** Email Agent ne peut pas scraper les news IA — digest vide dans la section IA.

**Solution appliquée :** Ajouté `continue-on-error: true` et un fallback JSON si le scraping échoue. L'agent génère quand même un digest (limité aux emails si Gmail configuré).

**Action manuelle requise :** Vérifier le compte Firecrawl (billing, quota).

---

## 2026-03-31 — Heredocs YAML dans GitHub Actions : indentation et parsing

**Problème :** Les heredocs multi-lignes (JSON MCP config) dans les blocs `run: |` créent du JSON indenté. Bien que fonctionnel en théorie (JSON ignore les espaces), cela ajoute de la complexité et peut causer des edge cases avec `sed` sur du contenu multi-ligne.

**Solution :** Standardiser sur `printf '...' > file` en une ligne (JSON compact) pour les MCP configs simples. Réserver les heredocs uniquement pour le contenu réellement multi-ligne (scripts Python).

**Agents concernés :** `_reusable-claude.yml`, `scout.yml` (corrigés)

---

## 2026-03-24 — Netlify env vars : PUT vs POST

**Problème :** `POST /api/v1/accounts/{slug}/env/{key}` retourne 422 si la variable existe déjà.

**Solution :** Utiliser `PUT` pour créer ou mettre à jour. `POST` = create-only, `PUT` = upsert.

**API :** `PUT https://api.netlify.com/api/v1/accounts/{slug}/env/{key}` avec body `{"value": "..."}`.

**Autre piège :** Le champ `"scopes"` n'est pas disponible sur le plan gratuit Netlify → retourne 403 "Upgrade your account". Ne jamais envoyer `scopes` sur le plan free.

---

## 2026-03-24 — Netlify : rapports non visibles depuis le dashboard

**Problème :** Les rapports dans `reports/` ne sont pas accessibles depuis le dashboard Netlify car Netlify ne sert que le dossier `docs/`.

**Solution :**
1. Écrire les rapports dans `docs/reports/` (accessible par Netlify)
2. Faire une copie miroir dans `reports/` pour la navigation git
3. Dans `runs.json`, le champ `report_file` doit pointer vers `"reports/filename.md"` (relatif à `docs/`)

**Pattern dans les workflows :** `--output-dir docs/reports --dashboard-file docs/data/runs.json`

---

## 2026-03-24 — generate_report.py : arguments --output-dir et --dashboard-file

**Problème :** Les workflows appellent `generate_report.py` avec `--output-dir` et `--dashboard-file` mais ces arguments n'existaient pas dans le script.

**Solution :** Ajouter `--output-dir` (défaut : `docs/reports`) et `--dashboard-file` (défaut : `docs/data/runs.json`) dans `parse_args()`, et utiliser `args.output_dir` / `args.dashboard_file` dans le code.

**Important :** Toujours vérifier que les arguments CLI dans le script correspondent aux appels dans les workflows.

---

## 2026-03-24 — GitHub Actions PAT scope `workflow` requis pour workflow_dispatch

**Problème :** Le PAT utilisé pour déclencher des workflows via l'API GitHub (`POST /repos/{owner}/{repo}/actions/workflows/{workflow}/dispatches`) doit avoir le scope `workflow`.

**Vérification :** `curl -sI -H "Authorization: Bearer $TOKEN" https://api.github.com/user | grep x-oauth-scopes`

**Solution :** Utiliser `gh auth token` pour obtenir le token OAuth de session (qui a déjà `workflow` scope si authentifié via `gh auth login --scopes workflow`).

---

## 2026-03-31 — Git push race condition dans les workflows CI

**Probleme :** `git push` echoue avec `non-fast-forward` quand plusieurs workflows commettent sur main en parallele (orchestrator aggregate, sage, health-check, etc.).

**Cause :** Le checkout est fait en debut de job. Si un autre workflow pousse entre le checkout et le push, le repo local est en retard.

**Solution :** Ajouter `git pull --rebase origin main 2>/dev/null || true` avant chaque `git push` dans tous les workflows qui commettent. **CORRIGE le 2026-03-31** dans : orchestrator, sage, nexus, email-agent, scout, aria, ralph, health-check, vault-sync.

**Agents concernes :** Tous (pattern dans chaque workflow ayant un step "Commit")

---

## 2026-03-31 — MCP config : sed injection avec secrets

**Probleme :** `sed -i "s/PLACEHOLDER/${{ secrets.TOKEN }}/g"` casse si le secret contient `/`, `&`, ou `\` (caracteres speciaux sed). Risque de fuite de secret dans les logs en cas d'erreur.

**Solution :** Remplacer par Python `json.dump` avec `os.environ` :
```yaml
- name: Write MCP config
  env:
    GH_TOKEN_MCP: ${{ secrets.GITHUB_TOKEN }}
  run: |
    python3 -c "
    import json, os
    cfg = {'mcpServers': {'github': {'command': 'npx', 'args': ['-y', '@modelcontextprotocol/server-github'], 'env': {'GITHUB_PERSONAL_ACCESS_TOKEN': os.environ['GH_TOKEN_MCP']}}}}
    json.dump(cfg, open('/tmp/mcp-config.json', 'w'))
    "
```
**CORRIGE le 2026-03-31** dans tous les workflows.

**Agents concernes :** Tous

---

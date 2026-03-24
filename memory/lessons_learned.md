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

**Solution :** Ajouter une validation pre-flight au début de la tâche Nexus :
```python
required_secrets = ["GOOGLE_ADS_DEVELOPER_TOKEN", "GOOGLE_ADS_CLIENT_ID",
                    "GOOGLE_ADS_REFRESH_TOKEN"]
missing = [s for s in required_secrets if not os.environ.get(s)]
if missing or not account_id:
    result = {"status": "failed", "summary": f"Credentials manquants: {missing}"}
    json.dump(result, open("/tmp/agent_result.json", "w"))
    sys.exit(0)
```

**Agents concernés :** Nexus (pattern applicable à tout agent dépendant de credentials externes)

---

## 2026-03-24 — Sage : `all_retrospectives.json` vide ≠ absence d'activité

**Problème :** Sage conclut "aucune activité cette semaine" quand `all_retrospectives.json` est vide, alors que la vraie cause peut être un échec de la pipeline de collecte d'artifacts.

**Contexte :** Le collecteur d'artifacts GitHub Actions peut échouer silencieusement si les runs précédents n'ont pas uploadé d'artifacts (retention expirée, upload-artifact raté, etc.).

**Solution :** Sage doit distinguer les deux cas :
1. Vérifier si des workflows agents ont tourné cette semaine via `gh run list`
2. Si runs trouvés mais retrospectives vides → alerter (pipeline collecte cassée)
3. Si aucun run → confirmer l'absence d'activité

**Agents concernés :** Sage (workflow de collecte)

---

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

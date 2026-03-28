---
title: "Maintenance & Hygiene du Systeme"
id: operations-maintenance
type: operations
tags: [operations, maintenance, hygiene, cleanup, vault, graph]
agents: [sage, ralph]
created: 2026-03-27
updated: 2026-03-27
---

# Maintenance & Hygiene du Systeme

Guide de maintenance pour le systeme multi-agent. Responsabilite partagee entre [[agents/sage-memory|Sage]] (analyse, recommandations) et [[agents/ralph-memory|Ralph]] (execution, nettoyage).

---

## Taches quotidiennes (automatisees)

| Heure (UTC) | Tache | Workflow | Agent |
|-------------|-------|----------|-------|
| **06:00** | Health check | `health-check.yml` | -- (systeme) |
| **07:30** | Email digest | `iris.yml` | [[agents/iris-memory\|Iris]] |
| **08:00** (Lun-Ven) | Taches planifiees | `orchestrator.yml` | Orchestrator |

> [!note] Monitoring
> Les trois workflows quotidiens sont surveilles via [[operations/kpis]]. Un echec declenche une notification Slack si `SLACK_WEBHOOK_URL` est configure.

---

## Taches hebdomadaires

| Jour | Heure (UTC) | Tache | Responsable |
|------|-------------|-------|-------------|
| **Dimanche** | 09:00 | Sage analysis (retrospectives, skills, prompts) | [[agents/sage-memory\|Sage]] |
| **Lundi** | 08:00 | Nexus audit (Google Ads) | [[agents/nexus-memory\|Nexus]] |
| **Sur push** | auto | Vault graph rebuild | `vault-sync.yml` |
| **Manuel** | -- | Revue des runs echoues | Operateur humain |

### Revue des runs echoues

```bash
# Lister les 10 derniers echecs
gh run list --status failure --limit 10 --repo GaspardCoche/agent-system

# Detail d'un run specifique
gh run view {run_id} --repo GaspardCoche/agent-system --log-failed
```

Chaque echec doit etre documente dans [[agents/error-patterns]] s'il revele un pattern nouveau.

---

## Taches mensuelles

| Tache | Description | Reference |
|-------|-------------|-----------|
| **Rotation des tokens** | Verifier et renouveler les tokens expires (OAuth, API keys) | [[operations/secrets-matrix]] |
| **Nettoyage rapports** | Supprimer les rapports >30 jours dans `docs/reports/` | Voir commande ci-dessous |
| **Revue backlog HubSpot** | Verifier les deals stales, contacts non-assignes | [[crm/hubspot-backlog]] |
| **Revue KPIs** | Analyser taux de succes, couts, tendances | [[operations/kpis]] |
| **Mise a jour roadmap** | Avancement des phases, repriorisation | [[business/roadmap]] |

### Nettoyage des rapports anciens

```bash
# Lister les rapports de plus de 30 jours
find docs/reports/ -type f -mtime +30 -name "*.md"

# Supprimer (apres verification)
find docs/reports/ -type f -mtime +30 -name "*.md" -delete

# Commit le nettoyage
git add docs/reports/ && git commit -m "chore: cleanup reports older than 30 days"
```

> [!warning] Avant suppression
> Verifier qu'aucun rapport mensuel ou trimestriel n'est inclus dans le lot. Les rapports de synthese (prefixes `summary-` ou `quarterly-`) doivent etre conserves.

---

## Taches trimestrielles

| Tache | Description | Reference |
|-------|-------------|-----------|
| **Audit de securite** | Permissions, secrets, acces, logs | [[security/access-control]] |
| **Revue des prompts** | Efficacite, cout, taux de succes par agent | [[agents/prompt-engineering]] |
| **Archivage vault** | Notes obsoletes → `archive/` (Phase 4 roadmap) | [[business/roadmap]] |
| **Budget review** | Cout reel vs budget previsionnel | [[tech/token-budget]] |

> [!tip] Audit de securite trimestriel
> Checklist minimale :
> - [ ] Tous les secrets sont valides (`gh secret list`)
> - [ ] Aucun token en clair dans le code (`grep -r "sk-ant-" .`)
> - [ ] Permissions workflows minimales (`permissions:` explicite)
> - [ ] Acces repo limites aux collaborateurs necessaires
> - [ ] Logs des 90 derniers jours revus pour anomalies

---

## Commandes utiles

```bash
# Runs echoues cette semaine
gh run list --status failure --limit 10 --repo GaspardCoche/agent-system

# Cout estime (nombre de runs reussis * cout moyen)
gh run list --limit 50 --json conclusion | jq '[.[] | select(.conclusion=="success")] | length'

# Rebuild graph du vault
python3 .github/scripts/vault_builder.py

# Verifier les secrets configures
gh secret list --repo GaspardCoche/agent-system

# Lancer health check manuellement
gh workflow run health-check.yml --repo GaspardCoche/agent-system

# Voir le statut de tous les workflows
gh workflow list --repo GaspardCoche/agent-system

# Derniere execution par workflow
for w in orchestrator sage nexus iris scout forge sentinel lumen ralph aria; do
  echo "--- $w ---"
  gh run list --workflow="${w}.yml" --limit 1 --repo GaspardCoche/agent-system
done

# Taille du vault
du -sh docs/vault/

# Fichiers vault modifies recemment
find docs/vault/ -type f -name "*.md" -mtime -7 | sort
```

---

## Alertes et escalation

| Condition | Action | Responsable |
|-----------|--------|-------------|
| **3 echecs consecutifs** d'un agent | Issue automatique creee par Sage | [[agents/sage-memory\|Sage]] |
| **Secret expire** (erreur 401) | Regenerer immediatement | Operateur humain (voir [[operations/runbooks]]) |
| **Vault graph casse** | Relancer `vault_builder.py` + commit | [[operations/runbooks\|Runbook]] |
| **Dashboard down** | Verifier GitHub Pages deployment | Operateur humain |
| **Cout mensuel > $120** | Revue des runs, optimisation tokens | [[tech/token-budget]] |
| **Taux de succes < 80%** | Analyse des erreurs, revue prompts | [[agents/error-patterns]] |

> [!danger] Escalation critique
> Si un secret est compromis (expose dans un log, commit, ou rapport) :
> 1. **Revoquer immediatement** le token/cle concerne
> 2. Generer un nouveau secret
> 3. Mettre a jour dans GitHub Secrets (`gh secret set`)
> 4. Verifier les logs pour usage non-autorise
> 5. Documenter l'incident dans [[operations/decisions]]

---

## Calendrier recapitulatif

```
QUOTIDIEN     06:00  Health check
              07:30  Iris digest
              08:00  Orchestrator (Lun-Ven)

HEBDOMADAIRE  Dim 09:00  Sage analysis
              Lun 08:00  Nexus audit
              Sur push   Vault graph rebuild
              Manuel     Revue echecs

MENSUEL       Rotation tokens
              Nettoyage rapports
              Revue KPIs + backlog
              Mise a jour roadmap

TRIMESTRIEL   Audit securite
              Revue prompts
              Archivage vault
              Budget review
```

---

## Voir aussi

- [[operations/runbooks]] -- Procedures de resolution des incidents
- [[operations/kpis]] -- Metriques de suivi du systeme
- [[operations/secrets-matrix]] -- Matrice des secrets et tokens
- [[operations/agent-workflows]] -- Configuration des workflows GitHub Actions
- [[agents/error-patterns]] -- Catalogue des erreurs connues
- [[tech/token-budget]] -- Budget tokens et optimisation des couts

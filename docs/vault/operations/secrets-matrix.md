---
title: "Matrice des Secrets -- Configuration & Status"
id: operations-secrets-matrix
type: operations
tags: [operations, secrets, configuration, github, api-keys]
agents: [ralph, sentinel]
updated: 2026-03-28
---

# Matrice des Secrets -- Configuration & Status

> [!info] Vue d'ensemble
> Cette matrice recense les **15 secrets** necessaires au fonctionnement complet du systeme multi-agents. Chaque secret est stocke dans GitHub Secrets et injecte dans les workflows via `${{ secrets.SECRET_NAME }}`.

---

## Matrice Complete

| # | Secret | Agents | Status | Ou le Trouver | Rotation |
|---|--------|--------|--------|--------------|----------|
| 1 | `CLAUDE_CODE_OAUTH_TOKEN` | Tous | **Configure** | `claude setup-token` (CLI) | Quand expire (erreur 401) |
| 2 | `GEMINI_API_KEY` | Orchestrator, Sage, Nexus, Iris, Lumen | **Configure** | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | Annuel |
| 3 | `FIRECRAWL_API_KEY` | Scout, Iris | **Configure** | [firecrawl.dev](https://firecrawl.dev) --> Dashboard --> API Keys | Annuel |
| 4 | `SLACK_WEBHOOK_URL` | Tous (notifications) | **Non configure** | Slack --> Apps --> Incoming Webhooks --> Create | Jamais (sauf compromission) |
| 5 | `GMAIL_TOKEN_JSON` | Iris | **Non configure** | GCP Console --> APIs --> Gmail API --> OAuth 2.0 | 6 mois (refresh token) |
| 6 | `GMAIL_USER_EMAIL` | Iris | **Non configure** | Adresse email utilisee pour le digest | Jamais |
| 7 | `INTERNAL_EMAIL_DOMAIN` | Iris | **Non configure** | Domaine entreprise (ex: `emasphere.com`) | Jamais |
| 8 | `GOOGLE_SHEETS_TOKEN` | Scout | **Non configure** | GCP Console --> Service Accounts --> Create Key (JSON) | Annuel |
| 9 | `FULLENRICH_API_KEY` | Aria | **Non configure** | [fullenrich.com](https://fullenrich.com) --> Account --> API | Annuel |
| 10 | `HUBSPOT_API_KEY` | Aria | **Non configure** | HubSpot --> Settings --> Integrations --> Private Apps --> Create | Annuel |
| 11 | `GOOGLE_ADS_DEVELOPER_TOKEN` | Nexus | **Non configure** | Google Ads --> Tools --> API Center --> Developer Token | Jamais (permanent) |
| 12 | `GOOGLE_ADS_CLIENT_ID` | Nexus | **Non configure** | GCP Console --> APIs --> Credentials --> OAuth 2.0 Client ID | Annuel |
| 13 | `GOOGLE_ADS_CLIENT_SECRET` | Nexus | **Non configure** | GCP Console --> APIs --> Credentials --> OAuth 2.0 Client Secret | Annuel |
| 14 | `GOOGLE_ADS_REFRESH_TOKEN` | Nexus | **Non configure** | OAuth flow (google-ads-api-auth) | Quand expire |
| 15 | `GOOGLE_ADS_ACCOUNT_ID` | Nexus | **Non configure** | Google Ads --> ID compte : **7251903503** | Jamais |

---

## Status Global

| Status | Nombre | Pourcentage |
|--------|--------|-------------|
| **Configure** | 3 | 20% |
| **Non configure** | 12 | 80% |

> [!warning] Fonctionnalites Bloquees
> Les 12 secrets non configures bloquent les fonctionnalites suivantes :
> - **Slack** (#4) : Notifications agents (alertes, rapports)
> - **Gmail** (#5-7) : Email digest Iris
> - **Google Sheets** (#8) : Export donnees Scout
> - **FullEnrich** (#9) : Enrichissement contacts Aria
> - **HubSpot** (#10) : Toutes les operations CRM Aria
> - **Google Ads** (#11-15) : Audit et reporting Nexus

---

## Commandes de Gestion

### Ajouter un Secret

```bash
# Ajouter un secret au repository
gh secret set SECRET_NAME --repo GaspardCoche/agent-system

# Ajouter un secret depuis un fichier (pour les JSON longs)
gh secret set GMAIL_TOKEN_JSON --repo GaspardCoche/agent-system < token.json

# Ajouter un secret avec une valeur directe
echo "sk-xxxxxxxxxxxx" | gh secret set HUBSPOT_API_KEY --repo GaspardCoche/agent-system
```

### Lister les Secrets

```bash
# Lister tous les secrets configures
gh secret list --repo GaspardCoche/agent-system
```

> [!note] Securite
> `gh secret list` montre uniquement les **noms** des secrets, jamais les valeurs. Les valeurs ne sont accessibles que dans les workflows GitHub Actions via `${{ secrets.SECRET_NAME }}`.

### Supprimer un Secret

```bash
# Supprimer un secret (ex: rotation)
gh secret delete OLD_SECRET_NAME --repo GaspardCoche/agent-system
```

### Verifier un Secret dans un Workflow

```yaml
# Dans un workflow GitHub Actions
- name: Check secret availability
  run: |
    if [ -z "${{ secrets.HUBSPOT_API_KEY }}" ]; then
      echo "::error::HUBSPOT_API_KEY is not configured"
      exit 1
    fi
```

---

## Health Check

Le workflow `health-check.yml` valide la presence et la validite de tous les 15 secrets.

### Fonctionnement

```yaml
# .github/workflows/health-check.yml (extrait)
name: Health Check
on:
  schedule:
    - cron: '0 6 * * *'  # Tous les jours a 6h UTC
  workflow_dispatch:

jobs:
  check-secrets:
    runs-on: ubuntu-latest
    steps:
      - name: Validate secrets
        run: |
          MISSING=0

          # Secrets critiques (bloquent les agents)
          for SECRET in CLAUDE_CODE_OAUTH_TOKEN GEMINI_API_KEY FIRECRAWL_API_KEY; do
            if [ -z "${!SECRET}" ]; then
              echo "::error::CRITICAL: $SECRET is missing"
              MISSING=$((MISSING + 1))
            fi
          done

          # Secrets optionnels (fonctionnalites reduites)
          for SECRET in SLACK_WEBHOOK_URL HUBSPOT_API_KEY GOOGLE_ADS_DEVELOPER_TOKEN; do
            if [ -z "${!SECRET}" ]; then
              echo "::warning::OPTIONAL: $SECRET is not configured"
            fi
          done

          if [ $MISSING -gt 0 ]; then
            echo "::error::$MISSING critical secrets are missing"
            exit 1
          fi
        env:
          CLAUDE_CODE_OAUTH_TOKEN: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          FIRECRAWL_API_KEY: ${{ secrets.FIRECRAWL_API_KEY }}
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
          HUBSPOT_API_KEY: ${{ secrets.HUBSPOT_API_KEY }}
          GOOGLE_ADS_DEVELOPER_TOKEN: ${{ secrets.GOOGLE_ADS_DEVELOPER_TOKEN }}
          # ... autres secrets
```

### Niveaux de Criticite

| Niveau | Secrets | Impact si Manquant |
|--------|---------|-------------------|
| **CRITICAL** | `CLAUDE_CODE_OAUTH_TOKEN` | Aucun agent ne peut s'executer |
| **HIGH** | `GEMINI_API_KEY`, `FIRECRAWL_API_KEY` | Agents degrades (pas d'analyse Gemini, pas de scraping) |
| **MEDIUM** | `HUBSPOT_API_KEY`, `GOOGLE_ADS_*` | Fonctionnalites CRM et Ads indisponibles |
| **LOW** | `SLACK_WEBHOOK_URL`, `GMAIL_*`, `GOOGLE_SHEETS_TOKEN` | Notifications et integrations secondaires |

---

## Politique de Rotation

| Frequence | Secrets | Process |
|-----------|---------|---------|
| **Quand expire** | `CLAUDE_CODE_OAUTH_TOKEN`, `GOOGLE_ADS_REFRESH_TOKEN` | Detecte par erreur 401 dans les workflows --> regenerer et `gh secret set` |
| **6 mois** | `GMAIL_TOKEN_JSON` | Rappel calendrier --> regenerer OAuth token --> `gh secret set` |
| **Annuel** | `GEMINI_API_KEY`, `FIRECRAWL_API_KEY`, `GOOGLE_SHEETS_TOKEN`, `FULLENRICH_API_KEY`, `HUBSPOT_API_KEY`, `GOOGLE_ADS_CLIENT_ID`, `GOOGLE_ADS_CLIENT_SECRET` | Rappel calendrier --> regenerer sur la plateforme --> `gh secret set` |
| **Jamais** | `SLACK_WEBHOOK_URL`, `GMAIL_USER_EMAIL`, `INTERNAL_EMAIL_DOMAIN`, `GOOGLE_ADS_DEVELOPER_TOKEN`, `GOOGLE_ADS_ACCOUNT_ID` | Valeurs statiques, rotation uniquement en cas de compromission |

> [!danger] En Cas de Compromission
> Si un secret est compromis :
> 1. **Immediatement** : revoquer la clef sur la plateforme source
> 2. Generer une nouvelle clef
> 3. `gh secret set SECRET_NAME` avec la nouvelle valeur
> 4. Verifier les logs GitHub Actions pour usage non autorise
> 5. Documenter l'incident dans [[security/access-control]]

---

## Dependances par Agent

| Agent | Secrets Requis | Secrets Optionnels |
|-------|---------------|-------------------|
| **Tous** | `CLAUDE_CODE_OAUTH_TOKEN` | `SLACK_WEBHOOK_URL` |
| **Orchestrator** | `GEMINI_API_KEY` | -- |
| [[agents/scout-memory\|Scout]] | `FIRECRAWL_API_KEY` | `GOOGLE_SHEETS_TOKEN` |
| [[agents/aria-memory\|Aria]] | `HUBSPOT_API_KEY` | `FULLENRICH_API_KEY` |
| [[agents/nexus-memory\|Nexus]] | `GOOGLE_ADS_DEVELOPER_TOKEN`, `GOOGLE_ADS_CLIENT_ID`, `GOOGLE_ADS_CLIENT_SECRET`, `GOOGLE_ADS_REFRESH_TOKEN`, `GOOGLE_ADS_ACCOUNT_ID` | `GEMINI_API_KEY` |
| [[agents/iris-memory\|Iris]] | `FIRECRAWL_API_KEY` | `GMAIL_TOKEN_JSON`, `GMAIL_USER_EMAIL`, `INTERNAL_EMAIL_DOMAIN`, `GEMINI_API_KEY` |
| [[agents/lumen-memory\|Lumen]] | `GEMINI_API_KEY` | -- |
| [[agents/sage-memory\|Sage]] | `GEMINI_API_KEY` | -- |
| [[agents/forge-memory\|Forge]] | -- | -- |
| [[agents/sentinel-memory\|Sentinel]] | -- | -- |
| [[agents/ralph-memory\|Ralph]] | -- | `SLACK_WEBHOOK_URL` |

---

## Prochaines Etapes de Configuration

| Priorite | Secret | Prerequis | Fonctionnalite Debloquee |
|----------|--------|-----------|-------------------------|
| **P0** | `HUBSPOT_API_KEY` | Compte HubSpot + Private App creee | Pipeline CRM complet (Aria) |
| **P0** | `SLACK_WEBHOOK_URL` | Workspace Slack + App configuree | Notifications agents |
| **P1** | `GOOGLE_ADS_*` (5 secrets) | Compte Google Ads API approuve | Audit Ads (Nexus) |
| **P1** | `FULLENRICH_API_KEY` | Compte FullEnrich actif | Enrichissement contacts |
| **P2** | `GMAIL_*` (3 secrets) | GCP OAuth configure pour Gmail | Email digest (Iris) |
| **P2** | `GOOGLE_SHEETS_TOKEN` | Service Account GCP | Export donnees |

---

## Liens

- [[operations/runbooks]] -- Procedures operationnelles (incluant rotation secrets)
- [[security/access-control]] -- Politique de securite et acces
- [[tech/infrastructure]] -- Infrastructure technique
- [[tech/mcp-servers]] -- Serveurs MCP et leurs secrets associes
- [[agents/ralph-memory]] -- Ralph (dispatch, health check)
- [[agents/sentinel-memory]] -- Sentinel (validation securite)

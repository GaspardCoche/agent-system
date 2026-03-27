---
title: Securite & Controle d'Acces
id: security-access-control
type: security
tags: [security, access, secrets, permissions, audit]
updated: 2026-03-27
---

# Securite & Controle d'Acces

*Lie a [[INDEX]], [[tech/infrastructure]], [[operations/decisions]]*

> Politique de securite et controle d'acces du systeme. Reference obligatoire avant toute modification d'acces.

---

## Principes de securite

1. **Moindre privilege** -- Chaque agent n'a acces qu'aux outils dont il a besoin
2. **Audit trail** -- Toute action externe est previewee avant execution
3. **Dry run par defaut** -- Les agents qui modifient des systemes externes sont en dry_run par defaut
4. **Secrets isoles** -- Les secrets ne sont jamais logues ou inclus dans les artifacts
5. **Approbation humaine** -- Les actions irreversibles necessitent le label `approved`

---

## Matrice d'acces agents

| Agent | Filesystem | GitHub | Web (Playwright) | Firecrawl | Gmail | HubSpot | Google Ads |
|-------|-----------|--------|-----------------|-----------|-------|---------|-----------|
| Orchestrator | Lecture | Issues, Comments | -- | -- | -- | -- | -- |
| Forge | Lecture/Ecriture | Issues, PRs | -- | -- | -- | -- | -- |
| Sentinel | Lecture/Ecriture | Issues | -- | -- | -- | -- | -- |
| Scout | Lecture | -- | Navigation | Scrape | -- | -- | -- |
| Aria | Lecture | Issues | -- | -- | -- | CRUD contacts | -- |
| Nexus | Lecture | Issues | -- | -- | -- | -- | Lecture + Ecriture |
| Iris | Lecture | -- | -- | -- | Lecture + Drafts | -- | -- |
| Sage | Lecture/Ecriture | PRs | -- | -- | -- | -- | -- |
| Lumen | Lecture | -- | -- | -- | -- | -- | -- |
| Ralph | Lecture | Dispatch events | -- | -- | -- | -- | -- |

---

## Tokens et secrets

| Secret | Scope | Rotation | Derniere rotation |
|--------|-------|----------|------------------|
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude API | A l'expiration (detecte par 401) | -- |
| `GITHUB_TOKEN` | Auto-genere par Actions | Chaque run | Auto |
| `FIRECRAWL_API_KEY` | Firecrawl API | Annuel | -- |
| `GMAIL_TOKEN_JSON` | Gmail OAuth | A l'expiration | -- |
| `HUBSPOT_API_KEY` | HubSpot private app | Annuel | -- |
| `GOOGLE_ADS_REFRESH_TOKEN` | Google Ads OAuth | A l'expiration | -- |

---

## Protocole d'approbation

Avant toute **modification externe irreversible** :

1. L'agent cree un commentaire GitHub "Preview" sur l'issue
2. Attente de 2 minutes ou du label `approved`
3. Si `DRY_RUN=true` dans l'env -> preview uniquement, pas d'execution

Actions soumises a approbation :
- Ecriture HubSpot (Aria)
- Modification encheres Google Ads (Nexus)
- Envoi d'emails (Iris)
- Push de code (Forge)

---

## Incidents de securite

| Date | Incident | Impact | Resolution |
|------|---------|--------|-----------|
| -- | -- | -- | -- |

---

*Dispatch et Sage mettent a jour ce fichier. Lire avant tout changement d'acces.*

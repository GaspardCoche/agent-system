---
title: Securite & Controle d'Acces
id: security-access-control
type: security
tags: [security, access, secrets, permissions, audit]
agents: [sentinel, sage]
updated: 2026-03-28
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

## Conformite RGPD -- Donnees Leadgen

> Ref : [[leadgen/sources-web]], [[leadgen/pipeline-overview]], [[crm/hubspot-api]]

### Regles de scraping

| Regle | Detail |
|-------|--------|
| **Verification robots.txt** | Obligatoire avant tout scraping. Si `Disallow`, ne pas scraper. |
| **Verification ToS** | Verifier les conditions d'utilisation du site avant scraping. Pas de scraping si interdit. |
| **Donnees publiques uniquement** | Ne scraper que des donnees accessibles publiquement (LinkedIn public, sites web entreprises) |
| **Pas de scraping massif** | Respecter les rate limits, pas de requetes en rafale |
| **Agent responsable** | Scout verifie la conformite avant chaque campagne de scraping |

### Acces aux donnees leadgen par agent

| Agent | Acces | Restrictions |
|-------|-------|-------------|
| **Aria** | Lecture + Ecriture CRM (HubSpot) | Seul agent autorise a ecrire dans le CRM. Toute ecriture soumise a approbation. |
| **Lumen** | Lecture seule CRM (HubSpot) | Analyse et reporting uniquement. Aucune modification. |
| **Scout** | Scraping web, enrichissement | Verification robots.txt/ToS obligatoire. Pas d'acces CRM direct. |
| **Nexus** | Aucun acces leadgen | Scope limite a Google Ads |

### FullEnrich -- Controle des credits

| Regle | Detail |
|-------|--------|
| Budget cap par batch | Maximum 100 credits par batch d'enrichissement |
| Monitoring | Suivi des credits consommes dans [[leadgen/monitoring]] |
| Alerte seuil | Notification si > 80% du budget mensuel consomme |
| Approbation | Batches > 50 credits necessitent le label `approved` |

### PhantomBuster -- Rate limits

| Regle | Detail |
|-------|--------|
| Enforcement | Rate limits configures au niveau de l'agent (Scout) |
| LinkedIn scraping | Max 80 profils/jour pour eviter les restrictions LinkedIn |
| Cooldown | Pause minimum de 5 secondes entre les requetes |
| Slots | Respecter les limites de slots du plan PhantomBuster |

### Retention des donnees personnelles (RGPD)

| Type de donnee | Retention | Action a expiration |
|----------------|-----------|---------------------|
| Email professionnel | 12 mois apres dernier contact | Suppression ou anonymisation |
| Telephone | 12 mois apres dernier contact | Suppression |
| Profil LinkedIn (URL) | Illimite (donnee publique) | -- |
| Nom / Prenom | 12 mois apres dernier contact | Anonymisation |
| Donnees entreprise | Illimite (donnee publique) | -- |

**Droit a l'oubli :** Toute demande de suppression doit etre traitee sous 30 jours. Aria supprime les donnees du CRM, Scout supprime les donnees des sources.

---

## Incidents de securite

| Date | Incident | Impact | Resolution |
|------|---------|--------|-----------|
| -- | -- | -- | -- |

---

*Lie a [[operations/secrets-matrix]], [[leadgen/sources-web]], [[crm/hubspot-api]]*

*Dispatch et Sage mettent a jour ce fichier. Lire avant tout changement d'acces.*

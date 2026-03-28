---
title: Daily Digest — Email
id: operations-daily-digest
type: operations
tags: [email, iris, digest, daily]
agents: [iris]
updated: 2026-03-28
---

# Daily Digest — Email & AI News

*Lie a [[INDEX]], [[agents/iris-memory]], [[operations/decisions]], [[operations/runbooks]], [[operations/secrets-matrix]], [[tech/mcp-servers]]*

> **Iris met a jour ce fichier chaque matin apres le digest email et le scraping AI news.**
> Tu peux lire ce fichier pour avoir le contexte email + veille IA de la journee.

---

## Workflow Iris -- Digest quotidien

```
1. FETCH    — Recuperation emails via Gmail API (GMAIL_TOKEN_JSON)
2. SCRAPE   — Scraping sources AI news via Firecrawl
3. TRIAGE   — Classification des emails par categorie et priorite
4. DRAFT    — Generation de brouillons de reponse pour les emails prioritaires
5. POST     — Ecriture du digest dans ce fichier + notification interne
```

### Schedule

| Jour | Heure (UTC) | Contenu |
|------|-------------|---------|
| Lundi - Vendredi | 07h30 | Digest complet (emails + AI news) |
| Samedi - Dimanche | 09h30 | Digest allege (emails urgents uniquement) |

---

## Categories d'emails

| Categorie | Priorite | Action Iris |
|-----------|----------|-------------|
| **Urgent** | Haute | Remonte immediatement, draft de reponse genere |
| **Action Required** | Haute | Liste dans "Ne pas louper", draft si possible |
| **Interne** | Moyenne | Resume dans la section Interne |
| **FYI** | Basse | Mentionne brievement |
| **Newsletter** | Basse | Extrait les points cles pertinents |
| **Spam / Promo** | Aucune | Ignore, archive automatique |

---

## Sources AI News (Firecrawl)

> Sources configurables -- Iris scrape ces URLs chaque matin

| Source | URL | Frequence | Focus |
|--------|-----|-----------|-------|
| The Batch (Andrew Ng) | deeplearning.ai/the-batch | Quotidien | AI industry trends |
| Hacker News - AI | news.ycombinator.com (filtre AI/ML) | Quotidien | Tech community, papers |
| AI News (Jack Clark) | importai.substack.com | Hebdo | Politique AI, recherche |
| Anthropic Blog | anthropic.com/blog | Ad hoc | Claude updates, safety |
| OpenAI Blog | openai.com/blog | Ad hoc | GPT updates, API changes |
| TechCrunch AI | techcrunch.com/category/artificial-intelligence | Quotidien | Startups, levees, produits |

---

## Format du digest

### Section emails

| Colonne | Description |
|---------|-------------|
| Expediteur | Nom + email |
| Sujet | Objet de l'email |
| Categorie | Urgent / Action Required / Interne / FYI / Newsletter |
| Resume | 1-2 phrases de resume par Iris |
| Action | Draft pret / A repondre / FYI / Archive |

### Section AI News

| Colonne | Description |
|---------|-------------|
| Source | Nom de la source |
| Titre | Titre de l'article/news |
| Pertinence | Haute / Moyenne / Basse (par rapport a EMAsphere et agent-system) |
| Resume | 2-3 phrases cles |

---

## Aujourd'hui -- [Date]

> *Iris ecrit ici apres chaque run*

### URGENT -- Ne pas louper
*--*

### Interne
*--*

### Integrations & Alertes
*--*

### AI News -- A retenir
*--*

---

## Emails en attente de reponse

> *Iris liste ici les emails avec draft pret*

| De | Sujet | Priorite | Draft |
|----|-------|---------|-------|
| -- | -- | -- | -- |

---

## Historique recent

| Date | Emails traites | Urgents | Drafts generes | AI News |
|------|---------------|---------|----------------|---------|
| 2026-03-24 | -- | -- | -- | -- |

---

## Configuration Iris

```
Gmail: [EN ATTENTE — GMAIL_TOKEN_JSON + GMAIL_USER_EMAIL]
Domain interne: [EN ATTENTE — INTERNAL_EMAIL_DOMAIN]
Firecrawl: Configure (FIRECRAWL_API_KEY present)
Schedule semaine: cron 30 7 * * 1-5
Schedule weekend: cron 30 9 * * 0,6
```

**Status : En attente configuration GMAIL_TOKEN_JSON**
Les tokens Gmail OAuth doivent etre ajoutes aux secrets GitHub Actions avant activation du workflow.
Voir [[operations/secrets-matrix]] pour la liste complete des secrets requis.

---

## Patterns detectes par Iris

> *Iris met a jour cette section avec les patterns recurrents*
> Exemples : expediteurs frequents, sujets recurrents, heures de pointe, types d'emails dominants

*--*

---

*Iris met a jour ce fichier chaque matin. Lire pour le briefing email + AI quotidien.*

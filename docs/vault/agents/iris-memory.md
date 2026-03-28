---
title: Iris — Mémoire & Patterns Email
id: agents-iris-memory
type: agent
tags: [iris, email, memory, gmail]
agents: [iris]
updated: 2026-03-28
---

# Iris — Mémoire & Patterns Email

*Lie a [[INDEX]], [[operations/daily-digest]], [[prospects/pipeline]], [[campaigns/lemlist-sequences]], [[crm/hubspot-workflows]], [[leadgen/geographic-hubs]]*

> Iris met à jour ce fichier après chaque traitement email.
> **Lire avant chaque run email pour les profils expéditeurs.**

---

## Configuration Gmail

```
Status         : ⚙️ Non configuré
GMAIL_TOKEN_JSON : [À configurer]
GMAIL_USER_EMAIL : [À configurer]
Domain interne : [À configurer — INTERNAL_EMAIL_DOMAIN]
Schedule       : 7h30 UTC quotidien
```

---

## Profils expéditeurs connus

> *Iris enrichit cette liste au fil des runs*

| Expéditeur | Catégorie | Notes |
|-----------|----------|-------|
| GitHub notifications | 🔵 Alertes | Jamais de draft |
| Stripe | 🔵 Alertes | Draft si erreur paiement |
| — | — | — |

---

## Patterns de triage

> *Patterns appris par Iris*

### Priorité 🔴 (Ne pas louper)
- Mots-clés : "urgent", "problème", "contrat", "impayé", "devis"
- Prospects/clients directs
- Factures & finance

### Priorité 🟡 (Interne)
- Domaine : `@[INTERNAL_EMAIL_DOMAIN]`
- Collaboration, réunions, projets

### Priorité 🔵 (Alertes)
- GitHub, Stripe, Slack, monitoring
- Notifications automatiques

---

## Statistiques récentes

| Date | Emails | Critiques | Drafts créés |
|------|--------|---------|------------|
| — | — | — | — |

---

## Emails récurrents détectés

> *Iris note ici les patterns récurrents pour les ignorer ou traiter différemment*

*Aucun pattern enregistré — en attente de configuration Gmail*

---

## Role dans le pipeline leadgen

> Iris intervient **post-MQL** : sequences d'outreach email pour les leads qualifies.
> Les leads arrivent depuis [[agents/aria-memory|Aria]] apres enrichissement et scoring.

---

## Integration Lemlist

Voir [[campaigns/lemlist-sequences]] pour la configuration des sequences.

Lemlist est utilise pour :
- Envoi de sequences email automatisees
- Suivi des ouvertures, clics, reponses
- Gestion des desinscriptions

---

## Templates multilingues

| Langue | Marche cible | Status |
|--------|-------------|--------|
| FR | Belgique francophone, France | A creer |
| NL | Belgique neerlandophone, Pays-Bas | A creer |
| EN | International, UK, DACH (fallback) | A creer |

Le routage linguistique suit les regles de [[leadgen/geographic-hubs]].

---

## Workflows HubSpot

Voir [[crm/hubspot-workflows]] pour les workflows de suivi post-outreach (reponses, relances, conversion).

---

*Iris met a jour ce fichier apres chaque run email.*

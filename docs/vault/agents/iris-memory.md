---
title: Iris — Mémoire & Patterns Email
id: agents-iris-memory
type: agent
tags: [iris, email, memory, gmail]
agents: [iris]
updated: 2026-03-24
---

# Iris — Mémoire & Patterns Email

*Lié à [[INDEX]], [[operations/daily-digest]], [[prospects/pipeline]]*

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

*Iris met à jour ce fichier après chaque run email.*

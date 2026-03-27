---
title: Aria -- Memoire & Leads
id: agents-aria-memory
type: agent
tags: [aria, leads, crm, hubspot, fullenrich, memory]
agents: [aria]
updated: 2026-03-27
---

# Aria -- Memoire & Leads

*Lie a [[INDEX]], [[prospects/pipeline]], [[agents/scout-memory]]*

> Aria met a jour ce fichier apres chaque enrichissement ou import CRM.
> **Lire avant chaque run pour connaitre l'etat du pipeline et les doublons.**

---

## Configuration CRM

```
HubSpot          : Non configure (HUBSPOT_API_KEY)
FullEnrich       : Non configure (FULLENRICH_API_KEY)
Mode actuel      : dry_run (par defaut)
```

---

## Pipeline summary

| Metrique | Valeur |
|----------|--------|
| Total contacts enrichis | 0 |
| Total importes HubSpot | 0 |
| Score moyen leads | -- |
| Taux enrichissement | -- |

---

## Regles de scoring

| Critere | Points |
|---------|--------|
| Email verifie | +30 |
| Telephone verifie | +20 |
| LinkedIn verifie | +15 |
| Entreprise > 50 employes | +10 |
| Site web fonctionnel | +10 |
| Secteur cible | +15 |

**Segmentation :**
- 80-100 : `hot_lead`
- 50-79 : `warm_lead`
- < 50 : `cold_lead`

---

## Regles RGPD

- Ne stocker que les emails professionnels (domaine = entreprise)
- Ne jamais stocker d'emails personnels (@gmail, @yahoo, etc.)
- Conserver la source d'enrichissement pour audit
- Toujours preview avant import CRM (`DRY_RUN=true`)

---

## Doublons detectes

| Email | Source 1 | Source 2 | Resolution |
|-------|---------|---------|-----------|
| -- | -- | -- | -- |

---

## Historique des runs

| Date | Source | Contacts | Enrichis | Importes | Run ID |
|------|--------|---------|---------|---------|--------|
| -- | -- | -- | -- | -- | -- |

---

*Aria met a jour ce fichier apres chaque enrichissement ou import CRM.*

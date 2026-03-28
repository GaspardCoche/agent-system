---
title: Aria -- Memoire & Leads
id: agents-aria-memory
type: agent
tags: [aria, leads, crm, hubspot, fullenrich, memory]
agents: [aria]
updated: 2026-03-28
---

# Aria -- Memoire & Leads

*Lie a [[INDEX]], [[prospects/pipeline]], [[agents/scout-memory]], [[leadgen/pipeline-overview]], [[leadgen/geographic-hubs]], [[tech/data-schemas]]*

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

## Role dans le pipeline

> Aria est **Stage 2-3** du pipeline leadgen : Enrichissement + Import CRM.
> Recoit les leads bruts de [[agents/scout-memory|Scout]] (Stage 1), les enrichit et les importe dans HubSpot.

---

## Integration FullEnrich

Voir [[leadgen/enrichment-fullenrich]] pour la configuration et les quotas.

FullEnrich est utilise pour :
- Verification et enrichissement d'emails professionnels
- Recherche de numeros de telephone
- Validation des profils LinkedIn

---

## Import HubSpot

| Composant | Documentation |
|-----------|---------------|
| API HubSpot | [[crm/hubspot-api]] |
| Proprietes custom | [[crm/hubspot-properties]] |

---

## Regles de nettoyage

| Regle | Documentation |
|-------|---------------|
| Nettoyage general | [[leadgen/cleaning-rules]] |
| Nettoyage GMT (noms, formats) | [[leadgen/cleaning-gmt]] |

---

## Lead scoring

Voir [[leadgen/lead-scoring]] pour le detail des criteres et seuils.

---

## Routage geographique

Voir [[leadgen/geographic-hubs]] pour les regles d'attribution par zone geographique (BE, FR, NL, DACH, etc.).

---

*Aria met a jour ce fichier apres chaque enrichissement ou import CRM.*

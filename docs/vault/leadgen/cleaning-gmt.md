---
title: "GMT -- Google Sheet Hub de Nettoyage"
id: leadgen-cleaning-gmt
type: leadgen
tags: [leadgen, cleaning, gmt, google-sheets, databases, lookups]
agents: [aria, forge]
updated: 2026-03-28
---

# GMT -- Google Sheet Hub de Nettoyage

Le GMT (Google Master Table) est le hub central de nettoyage et de controle qualite. Il sert a la fois de zone tampon entre le cleaning automatise et l'upload CRM, et de repertoire des bases de donnees de reference utilisees par les scripts de nettoyage.

---

## Structure du GMT -- 6 Onglets

### 1. Data Import (actif)

Onglet principal recevant les leads nettoyes en attente de review humain.

**21 colonnes :**

| # | Colonne | Description | Source |
|---|---------|-------------|--------|
| 1 | `firstName` | Prenom | PhantomBuster |
| 2 | `lastName` | Nom | PhantomBuster |
| 3 | `fullName` | Nom complet | PhantomBuster |
| 4 | `gender` | Genre (M/F/Unknown) | Script cleaning |
| 5 | `preferredLanguage` | Langue preferee | Script cleaning |
| 6 | `jobTitle` | Intitule du poste | PhantomBuster |
| 7 | `department` | Departement classifie | Script cleaning |
| 8 | `level` | Niveau hierarchique | Script cleaning |
| 9 | `email` | Email professionnel | FullEnrich |
| 10 | `bounceStatus` | Statut email | FullEnrich |
| 11 | `phone` | Telephone | FullEnrich |
| 12 | `companyName` | Nom entreprise | PhantomBuster |
| 13 | `companyDomain` | Domaine web | FullEnrich |
| 14 | `companyLinkedinUrl` | URL LinkedIn entreprise | PhantomBuster |
| 15 | `industry` | Industrie HubSpot | Script cleaning |
| 16 | `country` | Pays | Script cleaning |
| 17 | `postalCode` | Code postal | FullEnrich |
| 18 | `employees` | Categorie effectif | Script cleaning |
| 19 | `linkedInProfileUrl` | URL profil LinkedIn | PhantomBuster |
| 20 | `batchId` | ID du batch source | Pipeline |
| 21 | `creationTag` | Tag SDR de tracabilite | Pipeline |

### 2. Bin (rejetes)

Leads rejetes par le cleaning automatique ou la review manuelle. Chaque entree inclut la raison de rejet.

| Raison typique | Frequence |
|---------------|-----------|
| Job title exclu | ~35% |
| Email invalid/bounced | ~25% |
| Doublon detecte | ~20% |
| Donnees insuffisantes | ~10% |
| Hors perimetre geographique | ~10% |

> [!info] Recovery
> Les leads en Bin peuvent etre recuperes si la raison de rejet est corrigee (ex: email mis a jour). Le taux de recovery est suivi dans les health checks post-sheets. Voir [[leadgen/monitoring]].

### 3. Log (historique)

Journal de toutes les operations effectuees sur le GMT : imports, reviews, corrections manuelles, uploads CRM.

### 4. IndustryDB

Base de mapping industrie LinkedIn → HubSpot. Voir section bases de donnees ci-dessous.

### 5. NameGenderDB

Base de reference nom → genre. Voir section bases de donnees ci-dessous.

### 6. Archive

Leads traites et uploades vers HubSpot. Conservation pour audit et deduplication inter-batches.

---

## Scripts GMT

### Gender Auto-Population

```
Declencheur : Nouvelle ligne dans Data Import avec gender vide
Action : Lookup firstName dans nameGenderDb → Si match, remplir gender
Fallback : Appel MCP gender-detector si pas de match local
```

### Industry Mapping

```
Declencheur : Nouvelle ligne avec industry LinkedIn brute
Action : Lookup dans industryDb → Retourner industrie HubSpot mappee
Fallback : Flag pour review manuelle si similarite Jaro-Winkler < 0.85
```

### Job Title Filtering

```
Declencheur : Nouvelle ligne dans Data Import
Action : Evaluation jobTitle contre jobTitleRules (include/exclude)
Resultat : Score net = sum(include weights) - sum(exclude weights)
Decision : Score > 0 → Keep | Score <= 0 → Bin (raison: job title exclu)
```

---

## Orchestrateur

L'orchestrateur gere l'execution du pipeline end-to-end avec 6 checkpoints permettant des reprises partielles.

### Checkpoints

```
[1] Source (extraction PhantomBuster)
    |
[2] Enrich (FullEnrich)
    |
[3] Clean (pipeline TypeScript)
    |
[4] Sheets (push vers GMT)
    |
[5] Review (attente validation humaine)
    |
[6] HubSpot (upload CRM)
```

### Modes de reprise

| Flag | Reprend depuis | Cas d'usage |
|------|---------------|-------------|
| `--from-enrich` | Checkpoint 2 | Scrape OK, enrichissement echoue |
| `--from-clean` | Checkpoint 3 | Enrichissement OK, cleaning echoue |
| `--from-sheets` | Checkpoint 4 | Cleaning OK, push GMT echoue |
| `--from-hubspot` | Checkpoint 6 | Review OK, upload CRM echoue |
| `--dry-run` | Tous | Simulation sans ecriture (logs uniquement) |

> [!tip] Reprise apres erreur
> En cas d'echec a une etape, l'orchestrateur sauvegarde l'etat et peut reprendre au checkpoint precedent. Le Batch ID est preserve a travers tous les checkpoints pour la tracabilite.

### Format Batch ID

```
{YYYYMMDD}-{random6}
```

**Exemples :**
- `20260328-k7m3p9`
- `20260315-a2f8q1`

Le Batch ID est genere au checkpoint 1 (source) et suit le batch a travers tout le pipeline.

---

## GMT Suite -- Bases de Donnees

### `lists` (~25 listes actives)

Registre de toutes les listes Sales Navigator actives avec leurs metadonnees.

| Colonne | Description | Exemple |
|---------|-------------|---------|
| `listName` | Nom de la liste | CFO_France |
| `companyType` | Type d'entreprise cible | Corporate |
| `region` | Hub geographique | France |
| `creationTag` | Tag SDR | SDR-SN-20260315-a3f8k2 |
| `salesNavURL` | Lien vers la liste SN | https://linkedin.com/sales/... |
| `status` | Statut (active/paused/archived) | active |
| `lastScraped` | Date du dernier scrape | 2026-03-15 |

Voir [[leadgen/sources-linkedin]] pour les details de chaque liste.

### `languageMap` (~100 pays)

Mapping pays → langue preferee pour l'attribution automatique.

| Colonne | Description | Exemple |
|---------|-------------|---------|
| `country` | Nom du pays | Belgium |
| `preferredLanguage` | Langue par defaut | -- |
| `resolution` | Methode de resolution | Postal code |

> [!warning] Resolution Belgique
> La Belgique ne peut pas etre resolue par pays seul. La resolution se fait par code postal :
> - **Wallonie** (codes postaux 1300-1499, 4000-7999) → French
> - **Flandre** (codes postaux 1500-3999, 8000-9999) → Dutch
> - **Bruxelles** (codes postaux 1000-1299) → Selon langue profil LinkedIn, defaut French

### `industryDb` (~400 mappings)

Mapping industrie LinkedIn → industrie HubSpot standardisee.

| Colonne | Description | Exemple |
|---------|-------------|---------|
| `linkedinIndustry` | Industrie LinkedIn brute | Computer Software |
| `hubspotIndustry` | Industrie HubSpot mappee | COMPUTER_SOFTWARE |
| `confidence` | Score de confiance du mapping | 0.95 |
| `lastReviewed` | Date de derniere revision | 2026-02-15 |

> [!info] Maintenance
> Les mappings avec un score de confiance < 0.85 sont flags pour review. Les nouvelles industries LinkedIn non mappees sont ajoutees au backlog de review mensuel.

### `nameGenderDb` (legacy ~199 noms)

Base historique de mapping prenom → genre.

| Colonne | Description |
|---------|-------------|
| `firstName` | Prenom |
| `gender` | Genre (M/F) |

> [!tip] Migration vers MCP
> Cette base legacy de ~199 noms a ete remplacee par le MCP gender-detector qui couvre ~40 000 prenoms avec support multilingue. Le `nameGenderDb` est conserve comme fallback et pour les prenoms specifiques non couverts par le MCP.

### `jobTitleRules`

Regles de filtrage des job titles avec systeme de poids.

**Keywords Include (poids 1-3) :**

| Keyword | Langue | Poids |
|---------|--------|-------|
| CFO | EN | 3 |
| Chief Financial Officer | EN | 3 |
| Finance Director | EN | 2 |
| Head of Finance | EN | 2 |
| DAF | FR | 3 |
| Directeur Financier | FR | 3 |
| Directeur Administratif et Financier | FR | 2 |
| Financieel Directeur | NL | 3 |
| Hoofd Financien | NL | 2 |
| CEO | EN | 1 |
| Managing Director | EN | 1 |
| COO | EN | 1 |
| Directeur General | FR | 1 |

**Keywords Exclude (poids 1-2) :**

| Keyword | Langue | Poids |
|---------|--------|-------|
| Marketing | Multi | 2 |
| HR | EN | 2 |
| Human Resources | EN | 2 |
| Sales | EN | 1 |
| Ressources Humaines | FR | 2 |
| Commercial | FR | 1 |
| IT Director | EN | 1 |
| CTO | EN | 1 |

> [!info] Scoring
> Le score net = somme des poids include - somme des poids exclude. Un lead avec "CFO" (poids 3) et "Marketing" (poids 2) obtient un score net de 1 → conserve. Un lead avec seulement "Sales Director" obtient -1 → rejete.

### Onglets Operationnels

| Onglet | Fonction | Frequence de MAJ |
|--------|----------|-----------------|
| `rotationHistory` | Historique de rotation SDR par region | A chaque batch |
| `scrapingProgress` | Suivi avancement des scrapes en cours | Temps reel |
| `emailLog` | Log des emails envoyes (sequences) | Quotidien |
| `requests` | Requetes Moulinette en attente/traitees | Temps reel |

---

## Liens

- [[leadgen/pipeline-overview]]
- [[leadgen/cleaning-rules]]
- [[leadgen/sources-linkedin]]
- [[crm/hubspot-properties]]

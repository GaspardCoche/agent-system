---
title: "Sources Web -- Alternatives LinkedIn"
id: leadgen-sources-web
type: leadgen
tags: [leadgen, sources, web, scraping, rgpd]
agents: [scout]
updated: 2026-03-28
---

# Sources Web -- Alternatives LinkedIn

En complement de Sales Navigator, plusieurs sources web permettent de diversifier l'acquisition de leads. Ce document couvre les outils actifs, en evaluation, et deprecies.

---

## EasyScraper

EasyScraper genere des scripts headless pilotes par IA pour extraire des donnees structurees depuis des sites web cibles.

### Fonctionnement

```
Site cible (URL)
    |
    v
EasyScraper (generation script IA)
    |
    v
Script headless (Puppeteer/Playwright)
    |
    v
CSV structure → Pipeline enrichissement
```

### Cas d'usage

- Extraction de listes de dirigeants depuis des sites corporate
- Scraping d'annuaires professionnels sectoriels
- Collecte de donnees depuis des portails d'evenements (speakers, sponsors)

> [!warning] RGPD -- Verification obligatoire
> Avant toute extraction via EasyScraper, une verification RGPD est **obligatoire** :
> 1. Verification du fichier `robots.txt` du site cible
> 2. Lecture des Conditions Generales d'Utilisation (ToS)
> 3. Documentation de la base legale (interet legitime B2B)
> 4. Stockage limite dans le temps (max 12 mois sans interaction)
>
> Voir [[security/access-control]] pour les procedures de conformite.

### Statut

| Aspect | Detail |
|--------|--------|
| Statut | En decision |
| Blocage | Validation juridique RGPD en cours |
| Alternative | Collecte manuelle via Sales Portal |

---

## La Moulinette (Sales Portal)

Le Sales Portal interne offre un systeme de requetes ad-hoc appele "La Moulinette", permettant aux SDR de soumettre des demandes d'enrichissement ponctuelles.

### 3 Chemins de Requete

| Chemin | Input | Output | Temps |
|--------|-------|--------|-------|
| **Site web entreprise** | URL du site corporate | Contacts C-level enrichis | 24-48h |
| **LinkedIn entreprise** | URL page LinkedIn company | Contacts cibles avec email | 24-48h |
| **Profil LinkedIn direct** | URL profil LinkedIn individuel | Contact enrichi complet | 12-24h |

### Processus

1. Le SDR soumet une requete via le formulaire Sales Portal
2. Le systeme identifie le chemin et lance l'extraction appropriee
3. Les resultats passent par le meme pipeline de cleaning que les sources batch
4. Le lead enrichi est pousse vers HubSpot avec l'attribution au SDR demandeur

> [!tip] Quand utiliser La Moulinette
> Privilegier La Moulinette pour :
> - Des leads strategiques identifies manuellement (ABM)
> - Des contacts rencontres en evenement (post-salon)
> - Des referrals ou introductions necessitant un enrichissement rapide
>
> Ne **pas** utiliser pour du volume -- les sources batch (Sales Navigator) sont beaucoup plus efficaces.

---

## Trendstop

Base de donnees d'entreprises specifique a la Belgique, offrant des donnees firmographiques detaillees.

### Donnees Disponibles

| Champ | Description | Utilite |
|-------|-------------|---------|
| Code NACE | Secteur d'activite normalise | Filtrage industrie |
| Effectif | Nombre d'employes | Segmentation taille |
| Chiffre d'affaires | Revenus annuels | Qualification financiere |
| Siege social | Adresse complete | Routing geographique |
| Forme juridique | SA, SPRL, etc. | Filtrage type entreprise |

### Integration Pipeline

```
Trendstop (export filtre)
    |
    v
Mapping colonnes → Format standard
    |
    v
Enrichissement contact (FullEnrich)
    |
    v
Pipeline cleaning standard
```

> [!info] Specificite Belgique
> Trendstop est la meilleure source pour la couverture belge. Les donnees NACE permettent un ciblage sectoriel plus precis que les industries LinkedIn, souvent imprecises pour les PME belges. La resolution Wallonie/Flandre se fait via le code postal du siege social.

---

## Sources Deprecees

### Kaspr

| Aspect | Detail |
|--------|--------|
| Statut | **Deprecie** |
| Raison | Cout eleve, qualite email insuffisante, doublons avec FullEnrich |
| Migration | Toutes les fonctionnalites couvertes par FullEnrich |

### Google Custom Search

| Aspect | Detail |
|--------|--------|
| Statut | **Deprecie** |
| Raison | Resultats non structures, taux de conversion tres faible |
| Migration | Remplace par EasyScraper (en evaluation) |

> [!warning] Ne pas reactiver
> Ces sources ont ete deprecees apres evaluation. Toute demande de reactivation doit passer par une revue complete incluant cout, qualite, et conformite RGPD.

---

## Comparatif des Sources

| Source | Volume | Qualite | Cout | Couverture | Statut |
|--------|--------|---------|------|------------|--------|
| Sales Navigator | Eleve | Bonne | Licence SN | Global | Actif |
| Trendstop | Moyen | Tres bonne (BE) | Abonnement | Belgique | Actif |
| La Moulinette | Faible | Variable | Interne | Global | Actif |
| EasyScraper | Variable | A evaluer | Faible | Cible | En decision |
| Kaspr | -- | -- | -- | -- | Deprecie |
| Google Custom Search | -- | -- | -- | -- | Deprecie |

---

## Liens

- [[leadgen/pipeline-overview]]
- [[leadgen/sources-linkedin]]
- [[security/access-control]]

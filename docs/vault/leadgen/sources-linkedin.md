---
title: "Sources LinkedIn -- Sales Navigator"
id: leadgen-sources-linkedin
type: leadgen
tags: [leadgen, sources, linkedin, sales-navigator, phantom]
agents: [scout]
updated: 2026-03-28
---

# Sources LinkedIn -- Sales Navigator

Sales Navigator est la source principale de leads. Chaque source correspond a une liste Sales Navigator, alimentee dans PhantomBuster pour extraction.

## Principe de fonctionnement

```
Sales Navigator (liste filtree)
    |
    v
PhantomBuster (scrape par batch)
    |
    v
CSV brut → Enrichissement → Cleaning
```

> [!info] Convention
> Chaque liste Sales Navigator est associee a un Phantom specifique dans PhantomBuster. Le lien entre les deux est maintenu dans le GMT, onglet `lists`. Voir [[leadgen/cleaning-gmt]].

---

## Types de comptes et Batching

Le batching differe selon le type de compte Sales Navigator utilise.

### Comptes SafeSearch

Les comptes SafeSearch sont soumis a des limites plus strictes de LinkedIn. Pour eviter les restrictions :

- **Plusieurs batches par liste** : une liste est decoupee en segments de taille reduite
- Chaque batch est lance avec un delai minimum entre les executions
- Le Phantom est configure pour respecter les limites de scrolling

### Comptes Lead

Les comptes Lead ont des limites plus souples :

- **1 batch par liste** : la liste entiere est traitee en une seule execution
- Pas de decoupage necessaire
- Execution plus rapide mais toujours soumise aux rate limits PhantomBuster

> [!warning] Rate Limits
> Quelle que soit la methode, les limites globales PhantomBuster s'appliquent : 100 invitations/jour, 2500 profils/jour (sans email), 250 profils/jour (avec email). Voir [[leadgen/enrichment-phantom]] pour le detail.

---

## Convention de Nommage

Toutes les listes suivent le format strict :

```
{nom_liste}_{MOIS_EN_MAJUSCULE}
```

**Exemples :**
- `CFO_France_MARCH`
- `Finance_Director_UK_FEBRUARY`
- `DAF_Wallonie_APRIL`

> [!tip] Tracabilite
> Le mois en majuscules permet d'identifier immediatement la fraicheur des donnees et d'eviter les doublons inter-mensuels. Le Batch ID ajoute un identifiant unique : `{YYYYMMDD}-{random6}`.

---

## Registre des Listes

Le tableau ci-dessous sert de template pour le suivi des listes actives. La version operationnelle est maintenue dans le GMT (onglet `lists`).

| Nom Liste | Region | CompanyType | Batch Count | Last Scraped |
|-----------|--------|-------------|-------------|--------------|
| CFO_France | France | Corporate | 3 | -- |
| DAF_Wallonie | BE South | Mid-Market | 2 | -- |
| Finance_Director_UK | UK | Enterprise | 1 | -- |
| CFO_Flandre | BE North | Mid-Market | 2 | -- |
| Head_Finance_ROW | ROW | Corporate | 1 | -- |

> [!info] Mise a jour
> Ce tableau est un template. Pour les donnees en temps reel, consulter le GMT onglet `lists` qui contient ~25 listes actives avec CreationTag SDR, SalesNavURL, et statut de scraping. Voir [[leadgen/cleaning-gmt]].

---

## Criteres de Filtrage Sales Navigator

Les listes Sales Navigator sont construites avec les filtres suivants (variables selon la region) :

### Filtres Contact
- **Job Title** : CFO, DAF, Finance Director, Head of Finance, Chief Financial Officer (multilingue)
- **Seniority** : C-Suite, VP, Director
- **Geography** : Selon le hub cible

### Filtres Entreprise
- **Company Headcount** : 50-5000 (variable selon region)
- **Industry** : Toutes sauf exclues (public sector, education, non-profit)
- **Company Type** : Corporate, Mid-Market, Enterprise (selon liste)

> [!warning] Maintenance des filtres
> Les filtres doivent etre revus mensuellement. Un filtre trop large genere du bruit (leads non qualifies), un filtre trop strict reduit le volume. L'equilibre cible est un taux de cleaning pass de 60-75%.

---

## Processus Mensuel

1. **Semaine 1** : Revue et mise a jour des filtres Sales Navigator
2. **Semaine 1-2** : Lancement des Phantoms par batch selon le calendrier
3. **Semaine 2-3** : Enrichissement et cleaning des resultats
4. **Semaine 3-4** : Upload CRM et lancement sequences
5. **Continu** : Monitoring des metriques de volume et qualite

---

## Liens

- [[leadgen/pipeline-overview]]
- [[leadgen/enrichment-phantom]]
- [[leadgen/cleaning-gmt]]

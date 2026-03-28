---
title: Scout — Mémoire & Veille
id: agents-scout-memory
type: agent
tags: [scout, veille, firecrawl, memory, web]
agents: [scout]
updated: 2026-03-28
---

# Scout — Mémoire & Veille

*Lie a [[INDEX]], [[business/strategy]], [[prospects/pipeline]], [[leadgen/pipeline-overview]], [[leadgen/geographic-hubs]], [[tech/mcp-servers]]*

> Scout met à jour ce fichier après chaque run de veille.
> **Lire avant chaque run pour éviter les doublons et connaître les sources actives.**

---

## Role dans le pipeline

> Scout est **Stage 1** du pipeline leadgen : Sources + Extraction.
> Les leads extraits par Scout alimentent [[agents/aria-memory|Aria]] (Stage 2-3 : Enrichissement + Import CRM).

Voir [[leadgen/pipeline-overview]] pour la vue complete du pipeline.

---

## Configuration Firecrawl

```
Status          : Configure
FIRECRAWL_API_KEY : Set (2026-03-27)
Sources actives : LinkedIn, Web scraping
Schedule        : Selon demande ou cron (a configurer)
```

---

## Sources surveillées

> *Scout enrichit cette liste au fil des runs*

| Source | URL | Fréquence | Catégorie | Dernière visite |
|--------|-----|-----------|----------|----------------|
| — | — | — | — | — |

---

## Dernières découvertes

> *Scout note ici les insights clés par run*

| Date | Source | Insight | Pertinence | Action suggérée |
|------|--------|---------|-----------|----------------|
| — | — | — | — | — |

---

## Concurrents trackés

> *Noms, URLs et signaux détectés*

| Concurrent | URL | Signal détecté | Date |
|-----------|-----|---------------|------|
| — | — | — | — |

---

## Opportunités détectées

> *Prospects, partenaires, marchés identifiés par Scout*

| Date | Type | Description | Priorité | Statut |
|------|------|-------------|---------|--------|
| — | — | — | — | — |

---

## Historique des runs

| Date | Sources scannées | Insights | Run ID |
|------|----------------|---------|--------|
| — | — | — | — |

---

## Patterns de contenu détectés

> *Ce qui revient souvent dans la veille*

*Aucun pattern enregistré — en attente de configuration Firecrawl*

---

## Sources leadgen

> Sources d'extraction de leads pour le pipeline.

| Source | Integration | Documentation |
|--------|------------|---------------|
| LinkedIn (Sales Navigator, profils) | [[leadgen/sources-linkedin]] | PhantomBuster scraping |
| Web (sites entreprises, annuaires) | [[leadgen/sources-web]] | Firecrawl scraping |

---

## Integration PhantomBuster

Voir [[leadgen/enrichment-phantom]] pour les details de configuration.

PhantomBuster est utilise pour :
- Extraction de profils LinkedIn (Sales Navigator exports)
- Scraping de listes de contacts depuis LinkedIn
- Enrichissement de donnees de profil

---

## Regles RGPD pour le web scraping

- Ne scraper que des donnees professionnelles publiquement accessibles
- Ne jamais stocker d'emails personnels (@gmail, @yahoo, etc.)
- Respecter les fichiers `robots.txt` des sites scraped
- Conserver la trace de la source pour chaque donnee extraite
- Limiter la frequence de scraping pour eviter le blocage IP
- Ne pas scraper de donnees sensibles (opinions politiques, sante, etc.)

---

*Scout met a jour ce fichier apres chaque run de veille.*

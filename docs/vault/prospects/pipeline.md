---
title: Pipeline Prospects
id: prospects-pipeline
type: prospects
tags: [leads, crm, scout, aria, hubspot, funnel, qualification]
agents: [scout, aria]
updated: 2026-03-28
---

# Pipeline Prospects

*Lié à [[INDEX]], [[agents/scout-memory]], [[agents/aria-memory]], [[campaigns/google-ads]], [[business/strategy]], [[leadgen/pipeline-overview]], [[leadgen/sources-linkedin]], [[crm/hubspot-properties]], [[operations/kpis]]*

---

## Lead Funnel -- Étapes

```
Lead non qualifié → MQL → SQL-SDR → SQL-Sales → Client → Retention
```

| Étape | Définition | Propriétaire | Action principale |
|-------|-----------|-------------|-------------------|
| **Lead non qualifié** | Contact entré dans le CRM, pas encore évalué | Système (Aria) | Enrichissement, scoring automatique |
| **MQL** (Marketing Qualified Lead) | Répond aux critères ICP + scoring suffisant | Marketing Automation Manager | Nurturing, notification SDR |
| **SQL-SDR** (Sales Development Rep) | MQL accepté par le SDR, premier contact établi | SDR | Qualification BANT, prise de RDV |
| **SQL-Sales** | Opportunité confirmée, en négociation | Commercial Lead | Démo, proposition, négociation |
| **Client** | Deal signé, onboarding en cours | Account Manager | Onboarding, activation |
| **Retention** | Client actif, suivi satisfaction | Account Manager | Upsell, renouvellement, NPS |

---

## Statut pipeline -- Dernière mise à jour

> Mis à jour automatiquement par Scout (enrichissement) et Aria (CRM import)

| Étape | Nombre | MRR potentiel |
|-------|--------|--------------|
| Lead non qualifié | -- | -- |
| MQL | -- | -- |
| SQL-SDR | -- | -- |
| SQL-Sales | -- | -- |
| Client | -- | -- |
| Retention | -- | -- |

---

## Sources de leads

> Scout met à jour cette section après chaque run d'enrichissement. Voir [[leadgen/sources-linkedin]] pour le détail des listes.

| Source | Description | Volume estimé | Qualité |
|--------|-------------|--------------|---------|
| **Sales Navigator Lists** | Listes ciblées par persona, secteur, géo | Variable par campagne | Haute |
| **Web Scraping** | Extraction de contacts depuis sites cibles via Firecrawl | Variable | Moyenne |
| **Trendstop** | Données d'intention d'achat et signaux business | Variable | Haute |
| **HubSpot Intent** | Visiteurs web identifiés, formulaires, comportement | Continu | Haute |
| **Google Ads** | Leads entrants via campagnes Search | Dépend du budget | Variable |

### Dernières sources traitées

| Date | Source | Leads | Qualité | Agent |
|------|--------|-------|---------|-------|
| -- | -- | -- | -- | -- |

---

## Routing géographique

> Chaque lead est routé vers le hub approprié selon son pays et sa langue. Les règles de routing sont appliquées lors du nettoyage (GMT) et de l'upload HubSpot.

| Hub | Pays couverts | Langue(s) | Équipe commerciale | Règle de routing |
|-----|--------------|-----------|-------------------|------------------|
| **France** | France, Monaco, Luxembourg (FR), Suisse (FR) | FR | Commercial FR | `country IN (FR, MC) OR (country=LU AND lang=FR)` |
| **BE South** | Belgique francophone | FR | Commercial BE-FR | `country=BE AND lang=FR` |
| **BE North** | Belgique néerlandophone | NL | Commercial BE-NL | `country=BE AND lang=NL` |
| **UK** | Royaume-Uni, Irlande | EN | Commercial UK | `country IN (GB, IE)` |
| **ROW** | Tous les autres | EN/FR | Pool commercial | Fallback par défaut |

> La détection de la langue pour la Belgique repose sur la résolution du genre/langue dans le GMT (voir [[leadgen/cleaning-gmt]]).

---

## Critères de qualification MQL

> Un lead passe en MQL lorsqu'il satisfait un ensemble de critères basés sur les données enrichies.

### Règles de titre de poste (job title)

| Catégorie | Titres qualifiants | Score |
|-----------|-------------------|-------|
| **Décideur finance** | CFO, DAF, Chief Financial Officer, Finance Director, Directeur Financier, Head of Finance | +30 |
| **Direction générale** | CEO, Managing Director, Directeur Général, COO, General Manager | +25 |
| **Finance opérationnel** | Financial Controller, Comptable en chef, Head of Accounting, Trésorier | +15 |
| **IT / Data** | CIO, CTO, Head of Data, IT Director | +10 |
| **Autre** | Tout autre titre | 0 |

### Critères d'industrie

| Match | Score |
|-------|-------|
| Industrie manufacturière, services financiers, services professionnels | +20 |
| Retail, technologie, santé | +15 |
| Éducation, non-profit, administration | 0 (exclu) |

### Critères de taille d'entreprise

| Taille (employés) | Score |
|-------------------|-------|
| 50-200 | +10 |
| 200-1000 | +20 |
| 1000-5000 | +15 |
| < 50 ou > 5000 | 0 |

### Seuil MQL

> **Score total >= 50** pour qualification MQL automatique.
> **Score 30-49** : lead en review pour qualification manuelle.
> **Score < 30** : lead non qualifié, reste en nurturing ou archivé.

---

## Métriques pipeline à suivre

> Ces métriques sont consolidées dans [[operations/kpis]].

| Métrique | Description | Fréquence de mesure |
|----------|-------------|-------------------|
| **Volume par étape** | Nombre de leads à chaque étape du funnel | Hebdomadaire |
| **Taux de conversion inter-étapes** | % de passage d'une étape à la suivante | Hebdomadaire |
| **Temps moyen par étape** | Durée moyenne passée dans chaque étape | Mensuel |
| **Attribution source** | Répartition des leads par source d'acquisition | Hebdomadaire |
| **Vélocité pipeline** | Vitesse de progression des deals dans le funnel | Mensuel |
| **Taux de bin** | % de leads rejetés au nettoyage (voir [[leadgen/monitoring]]) | Par run |
| **Coût par MQL** | Budget marketing / nombre de MQL générés | Mensuel |

---

## Google Sheet actif

> Feuille de travail utilisée par Scout et le pipeline leadgen.

```
Sheet ID: [Renseigné dans les secrets GitHub]
Onglet principal: Prospects
Colonnes enrichies: description, sector, size, hq_city, contact_email,
                    first_name, last_name, job_title, company_name,
                    linkedin_url, phone, gender, language, hub
```

---

## Notes Scout et Aria

*Scout écrit ici après chaque enrichissement :*

> --

*Aria écrit ici après chaque import CRM :*

> --

---

*Mis à jour par Scout (enrichissement web) et Aria (import HubSpot). Lire avant tout run Scout/Aria. Voir [[leadgen/pipeline-overview]] pour l'architecture technique du pipeline.*

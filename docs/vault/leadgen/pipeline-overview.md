---
title: "Pipeline Lead Generation -- Vue d'ensemble"
id: leadgen-pipeline-overview
type: leadgen
tags: [leadgen, pipeline, overview, lead-generation, funnel]
agents: [scout, aria]
updated: 2026-03-28
---

# Pipeline Lead Generation -- Vue d'ensemble

Vue complete du pipeline de generation de leads, de la source brute jusqu'au client signe. Ce document sert de carte de navigation pour l'ensemble du systeme leadgen.

## Architecture du Pipeline

```
Sources (LinkedIn / Web)
    |
    v
Extraction (PhantomBuster)
    |
    v
Enrichissement (FullEnrich)
    |
    v
Cleaning (TypeScript + GMT)
    |
    v
CRM (HubSpot)
    |
    v
Workflows (HubSpot Automation)
    |
    v
Sequences (Lemlist / HubSpot)
    |
    v
Funnel (MQL → SQL → Client)
```

> [!info] Flux principal
> Chaque etape est instrumentee avec des health checks et des alertes. Voir [[leadgen/monitoring]] pour le detail des seuils et metriques.

---

## Etapes du Pipeline

### 1. Sources

Les leads proviennent de plusieurs canaux, chacun avec ses regles et contraintes specifiques.

| Source | Type | Couverture | Statut |
|--------|------|-----------|--------|
| Sales Navigator | LinkedIn | Global | Actif |
| FullEnrich | Enrichissement | Global | Actif |
| LeadInfo | Intent Web | EU | En evaluation |
| HubSpot Intent | Comportemental | Existants | En evaluation |
| Trendstop | Base entreprises | Belgique | Actif |
| EasyScraper | Web scraping | Cible | En decision |

Details : [[leadgen/sources-linkedin]] et [[leadgen/sources-web]]

### 2. Extraction (PhantomBuster)

PhantomBuster execute les scrapes Sales Navigator par batch, avec des limites strictes de rate limiting (100 invitations/jour, 2500 profils/jour sans email).

Details : [[leadgen/enrichment-phantom]]

### 3. Enrichissement (FullEnrich)

Le CSV PhantomBuster est soumis a FullEnrich pour obtenir emails valides, donnees entreprise, et optionnellement les numeros de telephone.

Details : [[leadgen/enrichment-fullenrich]]

### 4. Cleaning (TypeScript + GMT)

Pipeline TypeScript en 9 etapes : deduplication, filtrage job title, normalisation Unicode, detection genre, attribution langue, inference pays, validation email/telephone, nettoyage noms. Le GMT (Google Sheet) sert de hub de controle humain.

Details : [[leadgen/cleaning-rules]] et [[leadgen/cleaning-gmt]]

### 5. CRM (HubSpot)

Les leads nettoyes sont uploades vers HubSpot avec mapping des proprietes, creation/mise a jour conditionnelle, et association entreprise automatique.

Details : [[crm/hubspot-properties]] et [[crm/hubspot-api]]

### 6. Workflows et Sequences

HubSpot Workflows pour le routing automatique, Lemlist ou HubSpot Sequences pour l'outreach multicanal.

---

## Hubs Geographiques et Routing

Le pipeline route automatiquement les leads selon leur geographie vers le bon SDR et la bonne sequence.

| Hub | Regions | Langue(s) | SDR Assigne |
|-----|---------|-----------|-------------|
| France | France metropolitaine | FR | Rotation FR |
| BE South | Wallonie, Bruxelles (FR) | FR | Rotation BE-FR |
| BE North | Flandre, Bruxelles (NL) | NL | Rotation BE-NL |
| UK | Royaume-Uni, Irlande | EN | Rotation UK |
| ROW | Reste du monde | EN (defaut) | Rotation ROW |

> [!tip] Resolution Belgique
> La Belgique necessite un traitement special : le code postal determine si le lead est Wallonie (FR) ou Flandre (NL). Bruxelles est attribue selon la langue du profil LinkedIn. Voir [[leadgen/cleaning-gmt]] pour la table `languageMap`.

---

## Funnel de Qualification

```
Lead non qualifie
    |  Cleaning + enrichissement OK
    v
MQL (Marketing Qualified Lead)
    |  Engagement sequence + scoring
    v
SQL-SDR (Sales Qualified - SDR)
    |  Premier appel qualifie
    v
SQL-Sales (Sales Qualified - Sales)
    |  Demo / Proposition
    v
Client
    |  Signature
    v
Retention
```

Chaque transition est tracee dans HubSpot via les proprietes lifecycle stage et lead status. Le scoring combine intent signals, engagement outreach, et fit firmographique.

Details funnel : [[prospects/pipeline]]

---

## Points de Friction Identifies

> [!warning] Pain Points Actuels

### Qualite des donnees
- Emails bounced non detectes avant envoi sequence
- Doublons entre listes et entre sources
- Job titles mal categorises (multilingue FR/NL/EN)
- `linkedInProfileUrl` souvent null dans les exports PhantomBuster

### Temps et efficacite
- Process FullEnrich encore manuel (upload/download CSV)
- Review GMT necessitant intervention humaine frequente
- Pas de retry automatique sur les erreurs API

### Automatisation manquante
- Pas de webhook FullEnrich (polling necessaire)
- Orchestration batch non encore implementee end-to-end
- Alertes monitoring partiellement deployees

### Cleaning incomplet
- Regles P2 et P3 pas encore implementees (LinkedIn URL, employees, postal code, turnover)
- Detection de changement d'entreprise non automatisee
- Resolution multi-sites/entites absente

---

## Ameliorations Planifiees

### Court terme
- **Lemlist configuration avancee** : Warmup, rotation sender, A/B testing sequences
- **HubSpot automation** : Workflows de routing geographique automatiques, scoring refine
- **Monitoring complet** : Deploiement des 5 etapes de health check -- voir [[leadgen/monitoring]]

### Moyen terme
- **FullEnrich API** : Automatisation complete avec polling/webhook
- **AI expansion** : Scoring predictif, personnalisation contenu sequence par LLM
- **Orchestrateur batch** : Pipeline end-to-end sans intervention humaine

### Long terme
- **Intent-driven outreach** : LeadInfo + HubSpot Intent comme triggers de sequence
- **Multi-channel** : LinkedIn + Email + Phone synchronises

---

## Decisions Ouvertes

| Decision | Options | Impact | Statut |
|----------|---------|--------|--------|
| LeadInfo comme source | Activer / Reporter | Volume MQL | En evaluation |
| HubSpot Intent | Activer / Reporter | Precision scoring | En evaluation |
| EasyScraper | Implementer / Abandonner | Diversification sources | En decision |
| Lemlist vs HubSpot Sequences | Lemlist seul / HubSpot seul / Hybride | Stack outreach | En discussion |

---

## Agents Responsables

- **[[agents/scout-memory]]** : Extraction, sources, PhantomBuster
- **[[agents/aria-memory]]** : Enrichissement, cleaning, orchestration

---

## Liens

- [[leadgen/sources-linkedin]]
- [[leadgen/sources-web]]
- [[leadgen/enrichment-fullenrich]]
- [[leadgen/enrichment-phantom]]
- [[leadgen/cleaning-rules]]
- [[leadgen/cleaning-gmt]]
- [[crm/hubspot-properties]]
- [[crm/hubspot-api]]
- [[leadgen/monitoring]]
- [[prospects/pipeline]]

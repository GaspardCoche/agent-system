---
title: Stratégie Business
id: business-strategy
type: business
tags: [strategy, gtm, growth, crm, marketing-digital]
updated: 2026-03-28
---

# Stratégie Business

*Lié à [[INDEX]], [[business/vision]], [[business/roadmap]], [[prospects/pipeline]], [[campaigns/google-ads]], [[leadgen/pipeline-overview]], [[operations/kpis]]*

---

## Priorités Q2 2026

1. **Optimisation CRM HubSpot** -- Assainir la base, standardiser les propriétés, automatiser les workflows de qualification (voir [[crm/hubspot-backlog]])
2. **Accélération leadgen multi-géo** -- Lancer les campagnes multilingues FR/NL/EN avec attribution source complète (voir [[leadgen/pipeline-overview]])
3. **Alignement marketing-sales** -- Réduire le cycle MQL-to-SQL via scoring automatisé et routing géographique (voir [[prospects/pipeline]])

---

## Plan d'Actions CRM

> Chantier de nettoyage et d'optimisation du CRM HubSpot -- détails dans [[crm/hubspot-backlog]] et [[crm/hubspot-properties]]

| # | Action | Priorité | Statut | Responsable |
|---|--------|----------|--------|-------------|
| 1 | Déduplication contacts et entreprises | Critique | A faire | CRM Operations |
| 2 | Standardisation des propriétés (naming, types, options) | Critique | A faire | CRM Operations |
| 3 | Archivage et suppression des contacts obsolètes | Haute | A faire | CRM Operations |
| 4 | Audit des workflows actifs (désactiver les orphelins) | Haute | A faire | Marketing Automation Manager |
| 5 | Nettoyage des données business (secteurs, tailles, pays) | Haute | A faire | CRM Operations |
| 6 | Revue des rôles et permissions utilisateurs | Moyenne | A faire | CRM Operations |
| 7 | Audit des intégrations tierces (connecteurs, syncs) | Moyenne | A faire | CRM Operations |
| 8 | Formation équipes sur bonnes pratiques CRM | Moyenne | A faire | Marketing Automation Manager |
| 9 | Optimisation des rapports et dashboards | Moyenne | A faire | Marketing Automation Manager |
| 10 | Mise en place de règles anti-doublon | Haute | A faire | CRM Operations |
| 11 | Classification lifecycle stage (leads, MQL, SQL, client) | Critique | A faire | Marketing Automation Manager |
| 12 | Structuration hiérarchie entreprises (parent/child) | Moyenne | A faire | CRM Operations |
| 13 | Nettoyage des segments et listes statiques | Basse | A faire | Marketing Automation Manager |

---

## Marketing Digital -- Axes 2026

> Les axes stratégiques pour le marketing digital d'EMAsphere en 2026.

### 1. Campagnes multilingues

- Déploiement de campagnes Google Ads en FR, NL, EN selon les hubs géographiques
- Adaptation des messages et landing pages par langue et marché
- Voir [[campaigns/google-ads]] pour le détail du compte

### 2. Content et SEO local

- Stratégie de contenu par persona (CFO, Finance Director, Managing Director)
- SEO localisé par marché : France, Belgique (Wallonie + Flandre), UK
- Calendrier éditorial aligné sur les cycles budgétaires des CFO

### 3. Landing pages et conversions

- Création de landing pages dédiées par campagne et par langue
- A/B testing systématique sur les formulaires de conversion
- Tracking UTM standardisé (voir section UTM ci-dessous)

### 4. Alignement marketing-sales

- Définition commune des critères MQL/SQL entre marketing et commercial
- SLA de traitement des MQL par les équipes sales (< 24h)
- Feedback loop : sales renseignent la qualité des leads dans HubSpot

### 5. Reporting stratégique

- Dashboard unifié Google Data Studio : acquisition, pipeline, ROI par canal
- Attribution multi-touch pour mesurer l'impact réel de chaque levier
- Revue hebdomadaire des KPIs pipeline (voir [[operations/kpis]])

### 6. Formation équipes

- Formation continue sur HubSpot (workflows, scoring, reporting)
- Bonnes pratiques SEO pour les Content Managers
- Utilisation des outils d'analyse (GA4, SEMrush, Google Ads)

### 7. Standardisation UTM

| Paramètre | Convention | Exemple |
|-----------|-----------|---------|
| `utm_source` | Plateforme d'origine | `google`, `linkedin`, `email` |
| `utm_medium` | Type de canal | `cpc`, `organic`, `newsletter` |
| `utm_campaign` | Nom de campagne | `q2-2026-cfo-fr`, `webinar-finance-nl` |
| `utm_content` | Variante créative | `cta-demo`, `cta-trial` |
| `utm_term` | Mot-clé (si applicable) | `financial-reporting-tool` |

### 8. Emailing avancé

- Séquences automatisées par lifecycle stage dans HubSpot
- Nurturing multi-langue avec contenu personnalisé par ICP
- Scoring comportemental (ouvertures, clics, pages vues)

---

## Go-To-Market -- Canaux d'acquisition

| Canal | Description | Priorité | Lien vault |
|-------|-------------|----------|------------|
| Google Ads | Campagnes Search multilingues FR/NL/EN | Haute | [[campaigns/google-ads]] |
| Outbound (Scout/Aria) | Scraping, enrichissement, import CRM automatisé | Haute | [[leadgen/pipeline-overview]] |
| Content/SEO | Blog, whitepapers, webinaires par marché | Moyenne | -- |
| Email nurturing | Séquences HubSpot par segment | Moyenne | -- |
| LinkedIn Ads | Campagnes ABM ciblées sur ICP | A évaluer | -- |

---

## Stack Outils

| Outil | Usage principal | Responsable |
|-------|----------------|-------------|
| **HubSpot** | CRM, workflows, emailing, scoring | Marketing Automation Manager, CRM Operations |
| **Google Analytics (GA4)** | Tracking web, attribution, conversions | Marketing Automation Manager |
| **Google Ads** | Acquisition payante, campagnes multilingues | Marketing Automation Manager |
| **SEMrush** | SEO audit, keyword research, competitive analysis | SEO Specialist |
| **Google Data Studio** | Dashboards, reporting unifié | Marketing Automation Manager |

---

## Équipes cibles

| Rôle | Périmètre |
|------|-----------|
| **Marketing Automation Manager** | Workflows, scoring, campagnes, reporting, formation |
| **Content Managers** | Rédaction, SEO, calendrier éditorial, localisation |
| **CRM Operations** | Nettoyage données, propriétés, intégrations, permissions |
| **SEO Specialist** | Audit technique, keyword strategy, local SEO |
| **Commercial Leads** | Feedback qualité leads, suivi SLA, conversion SQL-to-client |

---

## Pipeline cible Q2 2026

| Métrique | Objectif mois | Source de mesure |
|----------|--------------|-----------------|
| Leads générés | A définir | [[leadgen/pipeline-overview]] |
| MQL | A définir | HubSpot |
| SQL | A définir | HubSpot |
| Deals closés | A définir | HubSpot |
| MRR incrémental | A définir | HubSpot |

---

*Mis à jour par Dispatch lors des revues stratégiques. Voir aussi [[business/vision]] et [[business/roadmap]].*

---
title: KPIs & Metriques Systeme
id: operations-kpis
type: operations
tags: [kpis, metrics, performance, monitoring, leadgen, pipeline]
agents: [lumen, sage, sentinel]
updated: 2026-03-28
---

# KPIs & Metriques Systeme

*Lie a [[INDEX]], [[operations/decisions]], [[tech/infrastructure]], [[leadgen/monitoring]], [[leadgen/pipeline-overview]], [[business/strategy]], [[prospects/pipeline]]*

> Metriques de performance du systeme multi-agents et du pipeline leadgen. Mise a jour par Sage, Lumen et les agents du pipeline.

---

## KPIs Pipeline Leadgen

### Metriques operationnelles

| KPI | Description | Objectif | Actuel | Source |
|-----|-------------|---------|--------|--------|
| Leads scrapes / semaine | Volume brut extrait par Scout | 100-500 | -- | Scout |
| Taux d'enrichissement | % de leads avec email trouve | > 60% | -- | FullEnrich |
| Taux de clean | % de leads passes en clean apres GMT | > 70% | -- | GMT |
| Taux de succes upload | % de leads uploades sans erreur dans HubSpot | > 95% | -- | Aria |
| Leads en review | Nombre de leads en attente de qualification manuelle | < 20% du total | -- | GMT |
| Taux de bin | % de leads rejetes au nettoyage | < 15% | -- | GMT |

### Health Checks par etape

> Seuils de monitoring definis pour chaque etape du pipeline. Voir [[leadgen/monitoring]] pour les alertes.

#### Post-Scraping

| Check | Seuil sain | Alerte si | Action |
|-------|-----------|----------|--------|
| Volume de leads | 20-500 par run | < 20 ou > 500 | Verifier la source / la liste |
| Taux de doublons | < 10% | > 10% | Verifier deduplication amont |
| Validite URL LinkedIn | > 95% | < 95% | Verifier le format d'extraction |
| Completude champs requis | > 90% | < 90% | Ajuster le mapping colonnes |

#### Post-Enrichissement

| Check | Seuil sain | Alerte si | Action |
|-------|-----------|----------|--------|
| Taux email trouve | > 60% | < 40% | Verifier qualite des inputs (nom + entreprise) |
| Taux domaine entreprise | > 80% | < 60% | Verifier le champ company_website |
| Credits consommes vs budget | < 80% budget mensuel | > 80% | Ajuster le volume ou le fournisseur |
| Temps de polling moyen | < 120s | > 300s | Verifier la charge FullEnrich |

#### Post-Nettoyage (GMT)

| Check | Seuil sain | Alerte si | Action |
|-------|-----------|----------|--------|
| Ratio clean / total | > 70% | < 50% | Reviser les regles de nettoyage |
| Ratio bin / total | < 15% | > 25% | Analyser les raisons de rejet |
| Ratio review / total | < 20% | > 30% | Affiner les regles automatiques |
| Resolution genre/langue | > 90% | < 80% | Enrichir la table de mapping prenoms |
| Completude hub geographique | 100% | < 100% | Verifier les regles de routing pays |

#### Post-Upload (HubSpot)

| Check | Seuil sain | Alerte si | Action |
|-------|-----------|----------|--------|
| Taux d'erreur upload | < 5% | > 10% | Verifier le format des proprietes |
| Ratio create vs update | Variable | Trop d'updates = doublons | Verifier la deduplication |
| Echecs d'association | < 5% | > 10% | Verifier les IDs entreprise |
| Proprietes manquantes | 0 | > 0 | Creer les proprietes dans HubSpot |

---

## KPIs Business

| KPI | Objectif | Actuel | Source | Frequence |
|-----|---------|--------|--------|-----------|
| MQL / mois | A definir | -- | HubSpot | Mensuel |
| Taux conversion MQL -> SQL | > 30% | -- | HubSpot | Mensuel |
| Taux conversion SQL -> Client | > 20% | -- | HubSpot | Mensuel |
| Pipeline value (EUR) | A definir | -- | HubSpot | Mensuel |
| Attribution par source | -- | -- | HubSpot + GA4 | Mensuel |
| ROAS Google Ads | > 3x | -- | [[campaigns/google-ads]] | Mensuel |
| Cout par MQL | A definir | -- | Budget / MQL | Mensuel |
| Leads generes / semaine | A definir | 0 | Scout + Aria | Hebdo |
| Emails traites / jour | -- | 0 | Iris | Quotidien |
| Contenu publie / semaine | -- | 0 | -- | Hebdo |

---

## KPIs Agents

| KPI | Objectif | Actuel | Tendance |
|-----|---------|--------|---------|
| Taux de succes des runs | > 90% | -- | -- |
| Temps moyen par run | < 5 min | -- | -- |
| Tokens moyens par run | < 50K | -- | -- |
| Skills valides / candidats | Croissant | 4 / 0 | -- |
| Prompts ameliores par Sage | Croissant | 0 | -- |
| Erreurs recurrentes | 0 | -- | -- |
| Couverture vault (notes remplies) | > 80% | ~40% | -- |
| Runs pipeline / semaine | > 3 | -- | -- |
| Taux de succes pipeline end-to-end | > 80% | -- | -- |
| Temps moyen pipeline complet | < 30 min | -- | -- |

---

## Metriques de cout

| Composant | Cout mensuel estime | Budget max |
|-----------|-------------------|-----------|
| GitHub Actions minutes | 0 (free tier) | 2000 min/mois |
| GitHub Pages | 0 (free) | 100 GB/mois |
| Firecrawl credits | 0 | 500 credits/mois |
| Claude tokens | Inclus abo | -- |
| Gemini tokens | 0 (free tier) | -- |
| FullEnrich credits | Variable | A definir |
| PhantomBuster credits | Variable | A definir |
| Google Ads budget | Variable | A definir |

---

## Historique hebdomadaire

| Semaine | Runs | Succes | Echecs | Insights | Skills | Leads scrapes | Leads uploades |
|---------|------|--------|--------|---------|--------|--------------|----------------|
| 2026-03-24 | 2 | 2 | 0 | 0 | 0 | -- | -- |

---

*Sage et Lumen mettent a jour ce fichier. Les agents du pipeline (Scout, Aria) alimentent les metriques leadgen. Lire lors des revues hebdo. Voir [[leadgen/monitoring]] pour les alertes en temps reel.*

---
title: "HubSpot -- Backlog Management"
id: crm-hubspot-backlog
type: crm
tags: [crm, hubspot, backlog, optimization, q2-2026]
agents: [aria, lumen]
updated: 2026-03-28
---

# HubSpot -- Backlog Management

Backlog de 16 taches pour l'optimisation du CRM HubSpot, couvrant Q1-Q4 2026. Ce document sert de reference unique pour le suivi de l'avancement et la priorisation.

---

## Vue d'ensemble

| Indicateur | Valeur |
|------------|--------|
| Nombre total de taches | 16 |
| Taches Haute priorite | 5 |
| Taches Moyenne priorite | 6 |
| Taches Basse priorite | 5 |
| Debut | Q1 2026 |
| Fin estimee | Q4 2026 |
| Agents responsables | [[agents/aria-memory|Aria]] (CRM), [[agents/lumen-memory|Lumen]] (strategie) |

---

## Backlog detaille

### Tache 1 -- Lead Scoring Review

| Champ | Valeur |
|-------|--------|
| Effort | Medium |
| Priorite | Haute |
| Periode | Q1-Q2 2026 |
| Statut | En cours |

**Description** : Revoir le modele de lead scoring existant. Verifier l'alignement des criteres de scoring avec l'ICP actuel (taille entreprise, industrie, niveau hierarchique, region). Identifier les leads mal scores et ajuster les poids.

**Actions** :
- [ ] Exporter les leads scores > 80 et verifier la qualite
- [ ] Comparer le scoring actuel vs les deals fermes (last 12 months)
- [ ] Proposer un nouveau modele de scoring base sur les donnees reelles
- [ ] Tester le nouveau modele en parallele pendant 1 mois

---

### Tache 2 -- Workflow Audit & Optimisation

| Champ | Valeur |
|-------|--------|
| Effort | High |
| Priorite | Haute |
| Periode | Ongoing |
| Statut | En cours |

**Description** : Audit complet des workflows actifs dans HubSpot. Identification des workflows casses, redondants, ou obsoletes. Optimisation des workflows d'attribution post-import.

**Actions** :
- [ ] Lister tous les workflows actifs (nombre, declencheurs, actions)
- [ ] Identifier les workflows avec taux d'erreur > 5%
- [ ] Supprimer ou archiver les workflows obsoletes
- [ ] Documenter chaque workflow restant
- [ ] Optimiser le workflow d'attribution (voir [[crm/hubspot-properties]])

---

### Tache 3 -- Property Standardization

| Champ | Valeur |
|-------|--------|
| Effort | High |
| Priorite | Haute |
| Periode | Q2-Q3-Q4 2026 |
| Statut | Planifie |

> [!warning] Tache critique
> Cette tache impacte directement le mapping entre le pipeline et HubSpot. Toute modification des proprietes peut casser les imports existants et les schemas Zod (voir [[tech/data-schemas]]).

**Description** : Standardisation complete des proprietes Contact et Company. Alignement des enumerations entre les sources de donnees (PhantomBuster, FullEnrich, Google Sheets) et HubSpot. Voir le detail dans [[crm/hubspot-properties]].

**Actions** :
- [ ] Phase 1 (Q2) : Audit des proprietes -- inventaire complet
- [ ] Phase 2 (Q2-Q3) : Alignement des schemas Zod
- [ ] Phase 3 (Q3) : Migration des donnees existantes
- [ ] Phase 4 (Q4) : Validation end-to-end et documentation

**Risques** :
- Mapping casse si les enums changent sans mise a jour des schemas
- Donnees historiques incoherentes si migration incomplete
- Workflows d'attribution impactes par le renommage de proprietes

---

### Tache 4 -- Archivage des donnees obsoletes

| Champ | Valeur |
|-------|--------|
| Effort | Medium |
| Priorite | Haute |
| Periode | 2x/an (Q2 + Q4) |
| Statut | Planifie |

**Description** : Archivage biannuel des contacts et companies obsoletes. Criteres : inactifs depuis > 12 mois, statut UNQUALIFIED depuis > 6 mois, emails invalides (hard bounce).

**Actions** :
- [ ] Definir les criteres d'archivage (liste + workflow)
- [ ] Exporter les donnees avant archivage (backup)
- [ ] Archiver les contacts (premiere passe : Q2 2026)
- [ ] Mettre en place un rapport automatique de suivi

---

### Tache 5 -- Formation equipe & Champions

| Champ | Valeur |
|-------|--------|
| Effort | High |
| Priorite | Haute |
| Periode | Ongoing Q3-Q4 |
| Statut | Planifie |

**Description** : Former l'equipe commerciale a l'utilisation optimale de HubSpot. Identifier des "champions" CRM dans chaque equipe pour assurer l'adoption et la qualite des donnees.

**Actions** :
- [ ] Identifier 1 champion par equipe SDR
- [ ] Creer un guide d'utilisation HubSpot (conventions, proprietes, workflows)
- [ ] Organiser des sessions de formation mensuelles
- [ ] Mettre en place des metriques d'adoption (taux de remplissage des champs)

---

### Tache 6 -- Nettoyage des taches SDR

| Champ | Valeur |
|-------|--------|
| Effort | Low |
| Priorite | Moyenne |
| Periode | Q2 2026 |
| Statut | Planifie |

**Description** : Supprimer les taches SDR obsoletes, reassigner les taches orphelines, nettoyer les queues de taches.

---

### Tache 7 -- Deduplication

| Champ | Valeur |
|-------|--------|
| Effort | High |
| Priorite | Moyenne |
| Periode | Q2-Q3 2026 |
| Statut | Planifie |

**Description** : Deduplication globale du CRM. Identification des doublons par email, domaine, nom+entreprise. Evaluation d'Operations Hub pour l'automatisation.

> [!info] Lien avec le pipeline
> La dedup intra-batch est geree par le pipeline (voir [[crm/hubspot-api]]). Cette tache concerne la dedup historique des donnees deja presentes dans le CRM.

---

### Tache 8 -- Optimisation des rapports

| Champ | Valeur |
|-------|--------|
| Effort | Medium |
| Priorite | Moyenne |
| Periode | Q2 2026 |
| Statut | Planifie |

**Description** : Revoir les dashboards et rapports existants. Supprimer les rapports inutilises. Creer les rapports manquants (funnel par source, taux de conversion par region, performance SDR).

---

### Tache 9 -- Revision Lifecycle Stages

| Champ | Valeur |
|-------|--------|
| Effort | Medium |
| Priorite | Moyenne |
| Periode | Q2-Q3 2026 |
| Statut | Planifie |

**Description** : Revoir les lifecycle stages et les criteres de passage d'un stage a l'autre. S'assurer de l'alignement avec le processus commercial reel.

**Stages actuels** : Subscriber -> Lead -> MQL -> SQL -> Opportunity -> Customer -> Evangelist

---

### Tache 10 -- Buyer Intent Tracking

| Champ | Valeur |
|-------|--------|
| Effort | Medium |
| Priorite | Moyenne |
| Periode | Q3 2026 |
| Statut | Planifie |

**Description** : Mettre en place un tracking des signaux d'intent (visites site, telechargements, interactions email). Integrer ces signaux dans le lead scoring.

---

### Tache 11 -- Audit des integrations

| Champ | Valeur |
|-------|--------|
| Effort | Medium |
| Priorite | Moyenne |
| Periode | Q2 2026 |
| Statut | Planifie |

**Description** : Inventaire de toutes les integrations connectees a HubSpot. Verification du fonctionnement, des permissions, des flux de donnees. Voir [[tech/integrations]].

---

### Tache 12 -- Nettoyage des segments

| Champ | Valeur |
|-------|--------|
| Effort | Low |
| Priorite | Basse |
| Periode | Q3 2026 |
| Statut | Planifie |

**Description** : Revoir les listes actives et statiques. Supprimer les segments obsoletes. Standardiser la nomenclature des listes.

---

### Tache 13 -- Enrichissement ICP

| Champ | Valeur |
|-------|--------|
| Effort | Medium |
| Priorite | Basse |
| Periode | Q3-Q4 2026 |
| Statut | Planifie |

**Description** : Enrichir les donnees des contacts et companies correspondant a l'ICP. Completer les champs manquants via FullEnrich ou sources tierces.

---

### Tache 14 -- Roles & Permissions

| Champ | Valeur |
|-------|--------|
| Effort | Low |
| Priorite | Basse |
| Periode | Q3 2026 |
| Statut | Planifie |

**Description** : Revoir les roles et permissions des utilisateurs HubSpot. S'assurer du principe du moindre privilege.

---

### Tache 15 -- Nettoyage des fichiers

| Champ | Valeur |
|-------|--------|
| Effort | Low |
| Priorite | Basse |
| Periode | Q4 2026 |
| Statut | Planifie |

**Description** : Nettoyer le gestionnaire de fichiers HubSpot. Supprimer les fichiers orphelins, les images inutilisees, les documents obsoletes.

---

### Tache 16 -- Verification HubDB

| Champ | Valeur |
|-------|--------|
| Effort | Low |
| Priorite | Basse |
| Periode | Q4 2026 |
| Statut | Planifie |

**Description** : Evaluer les fonctionnalites HubDB pour le stockage de donnees structurees (lookup tables, configurations). Determiner si HubDB peut remplacer certains fichiers de configuration du pipeline.

---

## Impact sur le pipeline

> [!warning] Dependances critiques
> Plusieurs taches du backlog ont un impact direct sur le pipeline de lead generation ([[leadgen/pipeline-overview]]). Coordination requise entre les agents [[agents/aria-memory|Aria]] et [[agents/forge-memory|Forge]].

| Tache | Impact pipeline |
|-------|----------------|
| #3 Property standardization | Le mapping peut casser si les enumerations changent. Les schemas Zod doivent etre mis a jour simultanement. |
| #7 Deduplication CRM-wide | Necessite potentiellement Operations Hub (licence Pro+). La dedup intra-batch est deja couverte par le pipeline. |
| #9 Lifecycle stages | La revision des stages peut impacter les workflows d'attribution et le statut par defaut des leads importes. |
| #1 Lead scoring | Le scoring impacte la priorisation des leads dans les queues SDR. Changement de scoring = changement de comportement. |

---

## Matrice de priorisation

```
          HAUTE                   BASSE
EFFORT    +---------+---------+
HAUT      | T2, T3  | T7, T5  |
          | T9      |         |
          +---------+---------+
BAS       | T1, T4  | T6, T8  |
          | T10, T11| T12-T16 |
          +---------+---------+
          HAUTE     BASSE
                PRIORITE
```

> [!tip] Recommandation
> Commencer par les taches a haute priorite et effort bas/moyen (T1, T4) pour des quick wins, puis attaquer les taches structurantes (T2, T3) en parallele.

---

## Liens

- [[crm/hubspot-properties]] -- Proprietes et mapping
- [[crm/hubspot-api]] -- API et integration technique
- [[business/roadmap]] -- Roadmap globale du projet
- [[business/strategy]] -- Strategie et objectifs

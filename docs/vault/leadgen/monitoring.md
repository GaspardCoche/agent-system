---
title: "Monitoring & Alertes Pipeline"
id: leadgen-monitoring
type: leadgen
tags: [leadgen, monitoring, alerts, health-checks, logging]
agents: [sentinel, lumen]
updated: 2026-03-28
---

# Monitoring & Alertes Pipeline

Systeme de monitoring couvrant l'ensemble du pipeline leadgen, des health checks par etape aux alertes Slack, en passant par le reporting batch et le logging structure.

---

## Rapport de Batch

Chaque batch genere un rapport automatique a la fin de son execution, resumant les metriques cles.

### Metriques du Rapport

| Metrique | Description | Exemple |
|----------|-------------|---------|
| Leads scraped | Volume brut extrait par PhantomBuster | 450 |
| Leads enriched | Volume apres enrichissement FullEnrich | 420 |
| Leads cleaned | Volume apres cleaning (pass) | 310 |
| Leads binned | Volume rejete (bin) | 95 |
| Leads review | Volume en attente review | 15 |
| Leads uploaded | Volume uploade vers HubSpot | 305 |
| Errors | Nombre d'erreurs techniques | 5 |
| Credits consumed | Credits FullEnrich utilises | 420 |

### Resume Funnel

```
Scraped:  450  (100%)
    |
Enriched: 420  (93.3%)  -- 30 skipped (deja enrichis)
    |
Cleaned:  310  (68.9%)  -- 95 bin, 15 review
    |
Uploaded: 305  (67.8%)  -- 5 erreurs upload
```

> [!info] Seuils de reference
> Un batch sain presente un taux enrichment > 90%, un taux cleaning pass entre 60-75%, et un taux upload > 95% des leads cleaned.

---

## Systeme d'Alertes

### Types d'Alertes

| Type | Canal | Severite | Declencheur |
|------|-------|----------|-------------|
| **Review Required** | Slack | Medium | Leads en attente de review manuelle dans le GMT |
| **API Error** | Slack | High | Erreur API (PhantomBuster, FullEnrich, HubSpot) |
| **Batch Success** | Slack | Low | Batch termine avec succes |
| **Health Red** | Slack | High | Un ou plusieurs health checks au rouge |

### Format des Alertes Slack

```
[ALERT] {severite} | {type}
Batch: {batchId}
Agent: {agent}
Detail: {message}
Action requise: {oui/non}
Timestamp: {ISO 8601}
```

> [!warning] Alertes High
> Les alertes de severite High necessitent une action dans les 2 heures. L'absence de reaction declenche une escalade automatique apres 4 heures.

---

## Health Checks -- 5 Etapes

Chaque etape du pipeline dispose de health checks avec des seuils yellow (attention) et red (critique).

### 1. Post-Scraping

| Check | Yellow | Red | Description |
|-------|--------|-----|-------------|
| Volume | < 50 ou > 400 | < 20 ou > 500 | Nombre de leads scrapes par batch |
| Colonnes presentes | 1-2 manquantes | > 2 manquantes | Colonnes obligatoires dans le CSV |
| Taux de doublons | > 10% | > 25% | Doublons intra-batch (email ou LinkedIn URL) |
| Validite LinkedIn URL | < 90% | < 75% | Pourcentage de linkedInProfileUrl non null |

> [!tip] Volume anormal
> Un volume trop bas indique un probleme de filtre Sales Navigator ou un rate limit LinkedIn. Un volume trop haut peut indiquer un filtre trop large ou un batch mal delimite.

### 2. Post-Enrichment

| Check | Yellow | Red | Description |
|-------|--------|-----|-------------|
| Email found rate | < 80% | < 60% | Pourcentage de leads avec email valide |
| Company domain rate | < 85% | < 70% | Pourcentage de leads avec domaine entreprise |
| Credits vs budget | > 80% budget mensuel | > 95% budget mensuel | Consommation credits FullEnrich |
| API response time | > 30s par lead | > 60s par lead | Temps moyen de reponse API |

### 3. Post-Cleaning

| Check | Yellow | Red | Description |
|-------|--------|-----|-------------|
| Clean ratio | < 60% | < 45% | Pourcentage de leads passant le cleaning |
| Bin ratio | > 35% | > 50% | Pourcentage de leads rejetes |
| Review ratio | > 10% | > 20% | Pourcentage de leads necessitant review |
| Gender resolution | < 85% | < 70% | Pourcentage de genres resolus (non Unknown) |
| Language resolution | < 90% | < 75% | Pourcentage de langues attribuees |
| Bin reason distribution | 1 raison > 60% | 1 raison > 80% | Concentration des rejets sur une seule cause |

> [!warning] Concentration des rejets
> Si une seule raison de bin depasse 60%, cela indique un probleme systematique en amont (ex: filtre Sales Navigator mal configure, source de mauvaise qualite). Investiguer la cause racine plutot que corriger les symptomes.

### 4. Post-Sheets

| Check | Yellow | Red | Description |
|-------|--------|-----|-------------|
| Review wait time | > 24h | > 48h | Temps d'attente moyen pour review humaine |
| Manual corrections | > 15% des leads | > 30% des leads | Pourcentage de leads corriges manuellement |
| Bin recovery rate | < 5% | < 2% | Pourcentage de leads recuperes du bin |

### 5. Post-Upload

| Check | Yellow | Red | Description |
|-------|--------|-----|-------------|
| Error rate | > 2% | > 5% | Pourcentage d'erreurs lors de l'upload HubSpot |
| Create vs update ratio | > 80% create | > 90% create | Ratio nouveaux contacts vs mises a jour |
| Association failures | > 5% | > 15% | Echecs d'association contact-entreprise |
| Rate limit hits | > 3 par batch | > 10 par batch | Nombre de rate limits HubSpot atteints |

> [!info] Ratio create/update
> Un ratio create trop eleve peut indiquer un probleme de deduplication : les leads existent deja dans HubSpot mais ne sont pas detectes. Verifier la logique de matching (email, LinkedIn URL, nom+entreprise).

---

## Dashboard de Sante

Vue synthetique de l'etat du pipeline :

```
Pipeline Health Dashboard
========================

Post-Scraping:    [GREEN]  Volume: 350 | Doublons: 4% | URL valid: 94%
Post-Enrichment:  [GREEN]  Email: 87%  | Domain: 92% | Credits: 45%
Post-Cleaning:    [YELLOW] Clean: 58%  | Bin: 32%    | Review: 10%
Post-Sheets:      [GREEN]  Wait: 18h   | Corrections: 8%
Post-Upload:      [GREEN]  Errors: 1%  | Assoc fail: 3%

Overall: [YELLOW] -- Attention requise sur le cleaning ratio
```

---

## Format de Log

Tous les logs du pipeline utilisent le format Pino JSON pour une exploitation structuree.

### Schema

```json
{
  "level": "info | warn | error | debug",
  "time": "2026-03-28T14:30:00.000Z",
  "batch_id": "20260328-k7m3p9",
  "agent": "aria | scout | sentinel | forge",
  "action": "scrape | enrich | clean | upload | alert",
  "detail": "Description lisible de l'evenement",
  "count": 350,
  "meta": {}
}
```

### Exemples

```json
{"level":"info","time":"2026-03-28T14:30:00.000Z","batch_id":"20260328-k7m3p9","agent":"scout","action":"scrape","detail":"PhantomBuster extraction completed","count":350}

{"level":"warn","time":"2026-03-28T15:45:00.000Z","batch_id":"20260328-k7m3p9","agent":"aria","action":"clean","detail":"Cleaning ratio below yellow threshold","count":58}

{"level":"error","time":"2026-03-28T16:00:00.000Z","batch_id":"20260328-k7m3p9","agent":"aria","action":"enrich","detail":"FullEnrich API timeout after 10 retries","count":0}

{"level":"info","time":"2026-03-28T17:00:00.000Z","batch_id":"20260328-k7m3p9","agent":"sentinel","action":"alert","detail":"Batch report sent to Slack","count":1}
```

### Niveaux de Log

| Niveau | Usage | Retention |
|--------|-------|-----------|
| `debug` | Details techniques de chaque etape | 7 jours |
| `info` | Evenements normaux du pipeline | 30 jours |
| `warn` | Seuils yellow atteints, anomalies | 90 jours |
| `error` | Erreurs techniques, seuils red | 1 an |

---

## Agents Responsables

| Agent | Role monitoring |
|-------|----------------|
| **[[agents/sentinel-memory]]** | Health checks, alertes, escalades |
| **[[agents/lumen-memory]]** | Reporting, dashboard, analyse tendances |

---

## Liens

- [[leadgen/pipeline-overview]]
- [[operations/kpis]]
- [[tech/infrastructure]]

---
title: Ralph -- Memoire & Automatisations
id: agents-ralph-memory
type: agent
tags: [ralph, automation, webhooks, cron, memory]
agents: [ralph]
updated: 2026-03-28
---

# Ralph -- Memoire & Automatisations

*Lie a [[INDEX]], [[agents/dispatch-log]], [[operations/decisions]], [[operations/agent-workflows]], [[operations/secrets-matrix]], [[leadgen/monitoring]]*

> Ralph met a jour ce fichier apres chaque run d'automatisation.
> **Lire pour connaitre les crons actifs et les webhooks configures.**

---

## Crons actifs

| Agent | Schedule | Workflow | Status |
|-------|----------|---------|--------|
| Orchestrator | Lun-Ven 8h UTC | orchestrator.yml | Actif |
| Iris | Quotidien 7h30 UTC | email-agent.yml | En attente config |
| Sage | Dimanche | sage.yml | Actif |
| Nexus | Lundi 6h UTC | nexus.yml | En attente config |
| Health Check | -- | health-check.yml | Manuel |

---

## Webhooks configures

| Source | Event | Action | Status |
|--------|-------|--------|--------|
| GitHub Issues | `labeled: agent` | Declenche Orchestrator | Actif |
| GitHub PRs | `opened, synchronize` | Declenche Orchestrator | Actif |
| Dashboard (GitHub API) | `POST /dispatches` | `workflow_dispatch` | Actif (via PAT localStorage) |

---

## Repository Dispatch events

> *Ralph ecoute ces events via `repository_dispatch`*

| Event type | Description | Agents declenches |
|-----------|-------------|------------------|
| `run_scout` | Lancer une veille web | Scout |
| `run_aria` | Lancer enrichissement leads | Aria |
| `run_nexus` | Lancer audit Google Ads | Nexus |
| `run_iris` | Lancer triage email | Iris |

---

## Historique des automatisations

| Date | Type | Trigger | Agents | Status |
|------|------|---------|--------|--------|
| -- | -- | -- | -- | -- |

---

## Erreurs d'automatisation

| Date | Erreur | Cause | Resolution |
|------|--------|-------|-----------|
| -- | -- | -- | -- |

---

## Chaine pipeline complete

Voir [[operations/agent-workflows]] pour la documentation complete des chaines d'agents.

Chaine leadgen : `Scout -> Aria -> Iris -> Dispatch (resume)`

---

## Repository dispatch events -- leadgen

| Event type | Description | Agents declenches | Chaine |
|-----------|-------------|-------------------|--------|
| `scout-enrich` | Scout a termine l'extraction, lancer enrichissement | Aria | Scout -> Aria |
| `aria-leads` | Aria a termine l'import CRM, leads prets pour outreach | Iris | Aria -> Iris |

---

## Monitoring workflow

Voir [[leadgen/monitoring]] pour les metriques de sante des workflows leadgen.

Verifications a effectuer :
- Tous les secrets requis sont configures (voir [[operations/secrets-matrix]])
- Les events `repository_dispatch` sont bien recus et traites
- Les timeouts ne sont pas depasses

---

*Ralph met a jour ce fichier apres chaque run d'automatisation.*

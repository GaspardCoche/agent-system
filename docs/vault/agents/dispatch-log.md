---
title: Dispatch — Journal d'Orchestration
id: agents-dispatch-log
type: agent
tags: [dispatch, orchestration, routing, log]
agents: [dispatch]
updated: 2026-03-28
---

# Dispatch — Journal d'Orchestration

*Lie a [[INDEX]], [[operations/decisions]], [[agents/sage-memory]], [[operations/agent-workflows]], [[operations/secrets-matrix]], [[tech/skills-registry]]*

> Journal de toutes les orchestrations effectuées par Dispatch.
> **Lire pour comprendre le contexte des campagnes en cours et éviter les doublons.**

---

## Campagnes actives

> *Tâches multi-agents en cours*

| ID | Description | Agents impliqués | Statut | Lancé le |
|----|-------------|-----------------|--------|---------|
| — | — | — | — | — |

---

## Journal des runs

> *Dispatch enrichit cette section après chaque orchestration*

| Date | Task | Agents routés | Statut | Issue GitHub | Notes |
|------|------|--------------|--------|-------------|-------|
| 2026-03-24 | Audit Nexus dry_run | nexus | Complet | -- | Premier run systeme |
| 2026-03-27 | Sage analyse hebdo | sage | Complet | -- | 0 retrospectives, 4 skills valides |
| -- | -- | -- | -- | -- | -- |

---

## Règles de routage actives

> *Comment Dispatch décide quel agent appeler*

### Triggers → Agents

| Trigger / Mot-clé | Agent prioritaire | Agent secondaire |
|-------------------|------------------|-----------------|
| "google ads", "campagne", "enchères" | nexus | — |
| "email", "inbox", "digest" | iris | — |
| "leads", "prospects", "enrichissement" | aria | — |
| "site web", "scraping", "veille" | scout | — |
| "code", "bug", "implémentation" | forge | sentinel |
| "analyse", "données", "insights" | lumen | — |
| "prompt", "skill", "amélioration" | sage | — |
| "automatisation", "cron", "webhook" | ralph | — |

---

## Orchestrations complexes (multi-agents)

> *Séquences d'agents utilisées*

### Séquence "Lead Generation Complète"
```
scout (veille) → aria (enrichissement) → iris (email outreach) → dispatch (résumé)
```

### Séquence "Audit Marketing"
```
nexus (ads) + scout (concurrents) → lumen (analyse) → dispatch (rapport)
```

### Séquence "Qualité Système"
```
sentinel (tests) → sage (analyse) → forge (corrections) → sentinel (re-tests)
```

---

## Erreurs d'orchestration

| Date | Erreur | Agent concerné | Résolution |
|------|--------|---------------|-----------|
| — | — | — | — |

---

## Prochaines orchestrations planifiées

- [ ] Premier run complet pipeline Lead Generation (dès configuration secrets)
- [ ] Audit Marketing complet (Nexus + Scout)
- [ ] Baseline QA système (Sentinel full scan)

---

## Documentation des chaines d'agents

Voir [[operations/agent-workflows]] pour la documentation complete des chaines multi-agents.

### Chaines leadgen actives

| Chaine | Etapes | Trigger |
|--------|--------|---------|
| Lead Generation Complete | Scout -> Aria -> Iris -> Dispatch | `scout-enrich` / `aria-leads` |
| Audit Marketing | Nexus + Scout -> Lumen -> Dispatch | Manuel |
| Qualite Systeme | Sentinel -> Sage -> Forge -> Sentinel | Manuel / PR |

---

## Gestion des secrets

Voir [[operations/secrets-matrix]] pour la matrice des secrets requis par agent et par workflow.

---

*Dispatch met a jour ce fichier apres chaque orchestration.*

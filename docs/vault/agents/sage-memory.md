---
title: Sage — Mémoire & Améliorations
id: agents-sage-memory
type: agent
tags: [sage, prompts, skills, memory, improvement]
agents: [sage]
updated: 2026-03-28
---

# Sage — Mémoire & Améliorations

*Lie a [[INDEX]], [[operations/decisions]], [[agents/dispatch-log]], [[tech/skills-registry]], [[tech/mcp-servers]], [[operations/agent-workflows]]*

> Sage est le cerveau méta-système. Il améliore les autres agents.
> **Lire avant chaque run d'amélioration pour connaître l'état des optimisations passées.**

---

## État du système

```
Dernière analyse    : 2026-03-24
Skills validés      : 4 (firecrawl_scrape, github_create_issue, gemini_analyze, slack_notify)
Skills candidats    : 0
Prompts améliorés   : 0
Prochaine analyse   : Dimanche 2026-03-31
```

---

## Patterns MCP détectés

> *Sage lit les `retrospective.mcp_patterns` de tous les agents*

| Agent | Pattern | Fréquence | Skill créé | Date |
|-------|---------|-----------|-----------|------|
| nexus | google_ads:audit:1x | — | — | 2026-03-24 |
| — | — | — | — | — |

---

## Skills en cours de développement

> *Candidats à valider*

| Skill | Agent source | Raison | Status | PR |
|-------|-------------|--------|--------|-----|
| — | — | — | — | — |

---

## Améliorations de prompts

> *Modifications proposées et appliquées*

| Agent | Avant | Après | Raison | PR | Status |
|-------|-------|-------|--------|-----|--------|
| — | — | — | — | — | — |

---

## Leçons apprises consolidées

> *Erreurs récurrentes à ne jamais répéter*

Voir `memory/lessons_learned.md` pour la liste complète.

**Résumé des erreurs critiques :**
- generate_report.py : toujours passer `--output-dir` et `--dashboard-file`
- PAT GitHub : scope `workflow` obligatoire pour modifier les workflows
- Rapports : toujours dans `docs/reports/` (GitHub Pages accessible)

---

## Analyse hebdomadaire — Dernière

| Semaine | Agents analysés | Patterns trouvés | Skills créés | Prompts améliorés |
|---------|----------------|-----------------|-------------|------------------|
| 2026-03-24 | 1 (nexus dry_run) | 0 | 0 | 0 |

---

## Propositions en attente d'approbation

| Type | Description | Impact estimé | Issue | Date |
|------|-------------|-------------|-------|------|
| — | — | — | — | — |

---

## Historique des runs Sage

| Date | Type | Résumé | Run ID |
|------|------|--------|--------|
| — | — | — | — |

---

## Gestion du registre de skills

Voir [[tech/skills-registry]] pour le registre complet des skills valides et candidats.

Sage est responsable de :
- Analyser les `retrospective.mcp_patterns` de tous les agents
- Identifier les patterns MCP recurrents a convertir en skills
- Valider les skills candidats et les promouvoir en `validated`

---

## Patterns MCP du pipeline leadgen a surveiller

| Pattern MCP | Agent source | Skill potentiel | Priorite |
|------------|-------------|-----------------|----------|
| `hubspot:batch_create:Nx` | Aria | `hubspot_batch_create` | Haute |
| `phantombuster:launch:Nx` | Scout | `phantom_launch` | Haute |
| `fullenrich:submit:Nx` | Aria | `fullenrich_submit` | Haute |

Ces patterns doivent etre surveilles lors des analyses hebdomadaires.
Des qu'un pattern depasse 3 occurrences, creer le skill correspondant.

---

*Sage met a jour ce fichier apres chaque analyse hebdomadaire.*

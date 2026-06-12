---
title: Sage — Mémoire & Améliorations
id: agents-sage-memory
type: agent
tags: [sage, prompts, skills, memory, improvement]
agents: [sage]
updated: 2026-06-12
---

# Sage — Mémoire & Améliorations

*Lie a [[INDEX]], [[operations/decisions]], [[agents/dispatch-log]], [[tech/skills-registry]], [[tech/mcp-servers]], [[operations/agent-workflows]]*

> Sage est le cerveau méta-système. Il améliore les autres agents.
> **Lire avant chaque run d'amélioration pour connaître l'état des optimisations passées.**

---

## État du système

```
Dernière analyse    : 2026-06-12 (run manuel — 68 jours de retard, Sage weekly a échoué toutes les semaines)
Skills validés      : 4 (firecrawl_scrape, github_create_issue, gemini_analyze, slack_notify)
Skills candidats    : 1 (gh_run_artifacts — non encore scripté)
Prompts améliorés   : 0
Prochaine analyse   : Dimanche 2026-06-15 (schedule normal)
Alerte active       :
  1. CRITIQUE — Sage weekly en échec depuis 5+ semaines (max_turns=15 insuffisant, doit passer à 25)
  2. CRITIQUE — Pipeline rétrospectives cassée : 9e semaine consécutive
  3. URGENT — Node.js 20 deprecation deadline : 16 juin 2026 (4 jours)
  4. BLOQUÉ — Nexus template mode depuis 85 jours (credentials Google Ads manquants)
Actions requises    :
  - Modifier sage.yml : --max-turns 15 → --max-turns 25
  - Vérifier que les fixes retrospective pipeline (2026-06-07) ont réellement été appliqués
  - Tester les workflows avec FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true avant le 16 juin
```

---

## Patterns MCP détectés

> *Sage lit les `retrospective.mcp_patterns` de tous les agents*

| Agent | Pattern | Fréquence | Skill créé | Date |
|-------|---------|-----------|-----------|------|
| nexus | google_ads:audit:1x | — | — | 2026-03-24 |
| sage | gh:run_list:50 + api:artifacts:N | hebdo | gh_run_artifacts (candidat) | 2026-06-12 |
| — | — | — | — | — |

> Note : Pipeline rétrospectives cassée depuis 9 semaines. Patterns ci-dessus = inférés des logs de workflow, pas de retrospective.mcp_patterns réels.

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

| Semaine | Agents analysés | Patterns trouvés | Skills créés | Prompts améliorés | Notes |
|---------|----------------|-----------------|-------------|------------------|-------|
| 2026-03-24 | 1 (nexus dry_run) | 0 | 0 | 0 | — |
| 2026-03-27 | 0 (rétros vides) | 0 | 0 | 0 | Collecte artifacts KO |
| 2026-03-29 | 0 (rétros vides) | 0 | 0 | 0 | Iris ran, collecte KO (2e semaine) |
| 2026-04-05 | 0 (rétros vides) | 0 | 0 | 0 | pipeline_status: broken (3e semaine) |
| 2026-04-12 | 0 (rétros vides) | 0 | 0 | 0 | pipeline_status: broken (4e semaine) |
| 2026-04-19 | 0 (rétros vides) | 0 | 0 | 0 | pipeline_status: broken (5e semaine) |
| 2026-05-03 | 0 (rétros vides) | 0 | 0 | 0 | pipeline_status: broken (6e semaine) |
| 2026-05-10 | ÉCHEC (max_turns) | 0 | 0 | 0 | Sage weekly failed — max_turns=15 trop court |
| 2026-05-17 | ÉCHEC (max_turns) | 0 | 0 | 0 | Sage weekly failed |
| 2026-05-24 | ÉCHEC (max_turns) | 0 | 0 | 0 | Sage weekly failed |
| 2026-05-31 | ÉCHEC (max_turns) | 0 | 0 | 0 | Sage weekly failed — 7e semaine pipeline cassée |
| 2026-06-07 | ÉCHEC (max_turns) | 0 | 0 | 0 | Sage weekly failed — 8e semaine pipeline cassée |
| 2026-06-12 | run manuel (68j retard) | 1 (gh_run_artifacts) | 0 | 0 | Analyse via git log + reports, pipeline cassée 9e semaine |

---

## Propositions en attente d'approbation

| Type | Description | Impact estimé | Issue | Date |
|------|-------------|-------------|-------|------|
| — | — | — | — | — |

---

## Historique des runs Sage

| Date | Type | Résumé | Run ID |
|------|------|--------|--------|
| 2026-03-24 | weekly | Analyse 1 rétro (Nexus), 0 skills, 0 PRs | — |
| 2026-03-27 | weekly | 0 rétros (collecte KO), maintenance | 23653853117 |
| 2026-03-29 | weekly | 0 rétros (Iris ran, collecte KO), alerte pipeline | 23706128370 |
| 2026-04-05 | weekly | 0 rétros (32 runs, 3 artifacts, 0 retrospective field) — 2 root causes documentées | 23998816293 |
| 2026-04-12 | weekly | 0 rétros — pipeline broken 4e semaine | — |
| 2026-04-19 | weekly | 0 rétros — pipeline broken 5e semaine, fixes "appliqués" | — |
| 2026-05-03 | weekly | 0 rétros — pipeline broken 6e semaine, fixes RÉELLEMENT appliqués | — |
| 2026-05-10 | weekly ÉCHEC | max_turns=15 atteint — run interrompu | — |
| 2026-05-17 | weekly ÉCHEC | max_turns=15 atteint | 25988149420 |
| 2026-05-24 | weekly ÉCHEC | max_turns=15 atteint | 26358765635 |
| 2026-05-31 | weekly ÉCHEC | max_turns=15 atteint — pipeline broken 7e semaine | 26710641346 |
| 2026-06-07 | weekly ÉCHEC | max_turns=15 atteint — pipeline broken 8e semaine | 27090737680 |
| 2026-06-12 | manuel (ce run) | Analyse via git log + reports. 3 nouvelles leçons. 1 skill candidat identifié. | 27413450637 |

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

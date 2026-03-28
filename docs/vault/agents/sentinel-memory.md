---
title: Sentinel -- Memoire & QA
id: agents-sentinel-memory
type: agent
tags: [sentinel, qa, tests, coverage, memory]
agents: [sentinel]
updated: 2026-03-28
---

# Sentinel -- Memoire & QA

*Lie a [[INDEX]], [[agents/forge-memory]], [[operations/decisions]], [[tech/data-schemas]], [[leadgen/cleaning-rules]], [[tech/code-repository]]*

> Sentinel met a jour ce fichier apres chaque cycle de tests.
> **Lire pour connaitre l'etat de la qualite du systeme.**

---

## Etat de la qualite

| Metrique | Valeur | Objectif | Status |
|----------|--------|---------|--------|
| Tests passes | -- | 100% | -- |
| Couverture code | -- | > 80% | -- |
| Erreurs recurrentes | -- | 0 | -- |
| Derniere validation | -- | < 7 jours | -- |

---

## Tests critiques

| Test | Fichier | Dernier run | Status |
|------|---------|------------|--------|
| Vault builder output valide | vault_builder.py | -- | -- |
| Graph.json schema correct | graph.json | -- | -- |
| Dashboard load sans erreur | index.html | -- | -- |
| Workflows YAML valides | .github/workflows/*.yml | -- | -- |
| Agent prompts coherents | agent_prompts/*.md | -- | -- |

---

## Regressions detectees

| Date | Regression | Cause | Fix | Agent responsable |
|------|-----------|-------|-----|------------------|
| 2026-03-24 | Stack overflow switchTab | Recursion infinie | Supprime override recursif | Forge |

---

## Historique des runs QA

| Date | Type | Couverture | Passes | Echecs | Run ID |
|------|------|-----------|--------|--------|--------|
| -- | -- | -- | -- | -- | -- |

---

## Checklist de validation pre-deploy

- [ ] Tous les YAML workflows valides (`yamllint`)
- [ ] `vault_builder.py` genere un graph.json valide
- [ ] Dashboard charge sans erreur JS console
- [ ] Tous les liens [[wikilink]] dans le vault resolvent
- [ ] `agents.json` coherent avec les workflows existants

---

## Validation schemas pipeline

Voir [[tech/data-schemas]] pour les schemas de validation des donnees du pipeline leadgen.

Sentinel doit verifier la conformite des donnees a chaque etape :
- Schema des leads bruts (sortie Scout)
- Schema des leads enrichis (sortie FullEnrich)
- Schema d'import HubSpot (entree Aria)

---

## Controles qualite donnees

Voir [[leadgen/cleaning-rules]] pour les regles de nettoyage a valider.
Voir [[leadgen/monitoring]] pour les metriques de qualite du pipeline.

Controles a executer :
- Emails professionnels uniquement (pas de @gmail, @yahoo, etc.)
- Champs obligatoires remplis (nom, prenom, entreprise, email)
- Format telephone international valide
- Pas de doublons dans le batch

---

## Sante du pipeline

Voir [[operations/kpis]] pour les KPIs de sante du pipeline leadgen.

---

## Tests du code repository

Voir [[tech/code-repository]] (hwinssinger/lead-pipeline) pour les tests TypeScript a executer.

---

*Sentinel met a jour ce fichier apres chaque cycle QA.*

---
title: Forge -- Memoire & Patterns Dev
id: agents-forge-memory
type: agent
tags: [forge, code, development, memory, implementation]
agents: [forge]
updated: 2026-03-27
---

# Forge -- Memoire & Patterns Dev

*Lie a [[INDEX]], [[agents/sentinel-memory]], [[operations/decisions]]*

> Forge met a jour ce fichier apres chaque implementation.
> **Lire avant chaque tache de code pour connaitre les patterns du projet.**

---

## Patterns de code valides

> *Forge enrichit cette section apres chaque run*

| Pattern | Contexte | Valide par |
|---------|---------|-----------|
| Self-correction loop (max 3 cycles) | Toute implementation | CLAUDE.md |
| Commit format: `agent(forge): <task_id> - <desc>` | Chaque commit | Convention |
| Toujours lancer les tests apres modification | Post-implementation | CLAUDE.md |
| Verifier syntaxe avant de marquer complete | Pre-completion | Self-correction rules |

---

## Stack technique du projet

```
Orchestration  : GitHub Actions + claude-code-action@v1
Language       : Python 3.12 (scripts), JavaScript (Netlify functions)
Dashboard      : HTML/CSS/JS statique (D3.js pour le graph)
Knowledge      : Obsidian Vault (Markdown + YAML frontmatter)
Deploiement    : Netlify (docs/) + GitHub Pages (vault)
CI/CD          : GitHub Actions (reusable workflows)
```

---

## Fichiers critiques -- ne pas casser

| Fichier | Role | Impact si casse |
|---------|------|----------------|
| `.github/workflows/_reusable-claude.yml` | Base de tous les agents | Tous les workflows cassent |
| `.github/scripts/vault_builder.py` | Genere le knowledge graph | Dashboard graph tab inutilisable |
| `.github/scripts/generate_report.py` | Genere les rapports | Dashboard runs tab vide |
| `docs/index.html` | Dashboard complet | Pas de monitoring |
| `docs/data/agents.json` | Config agents dashboard | Agents non-launcables |

---

## Erreurs passees

| Date | Erreur | Fix | Lecon |
|------|--------|-----|-------|
| 2026-03-20 | `startup_failure` workflows | `default: "none"` pas `""` | Jamais de default vide sur workflow_call |
| 2026-03-24 | Rapports non visibles Netlify | Ecrire dans `docs/reports/` | Toujours penser au publish directory |

---

## Historique des runs

| Date | Tache | Fichiers modifies | Status | Run ID |
|------|-------|------------------|--------|--------|
| -- | -- | -- | -- | -- |

---

*Forge met a jour ce fichier apres chaque implementation.*

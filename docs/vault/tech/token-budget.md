---
title: "Budget Tokens & Couts par Agent"
id: tech-token-budget
type: tech
tags: [tech, tokens, budget, cost, optimization, claude]
agents: [sage, lumen]
created: 2026-03-27
updated: 2026-03-27
---

# Budget Tokens & Couts par Agent

Estimation des couts d'utilisation de l'API Claude pour le systeme multi-agent. Ce document sert de reference pour [[agents/prompt-engineering]], [[operations/kpis]] et les decisions d'optimisation de [[agents/sage-memory|Sage]] et [[agents/lumen-memory|Lumen]].

---

## Modele de cout Claude (Opus 4.6)

| Parametre | Valeur |
|-----------|--------|
| **Input** | $15 / 1M tokens |
| **Output** | $75 / 1M tokens |
| **Turn moyen** | ~2-5K tokens input + ~1-2K tokens output |
| **Context window** | 200K tokens |

> [!warning] Attention au cout output
> Le ratio input/output est de **1:5** -- chaque token genere coute 5x plus qu'un token lu. Privilegier les reponses concises et les formats structures ([[tech/data-schemas|schemas JSON]]).

---

## Budget par complexite de tache

| Complexite | Turns | Input estimee | Output estimee | Cout estimee |
|------------|-------|---------------|----------------|-------------|
| **Simple** | 3 | ~15K tokens | ~6K tokens | **~$0.67** |
| **Moyen** | 8 | ~40K tokens | ~16K tokens | **~$1.80** |
| **Complexe** | 12 | ~60K tokens | ~24K tokens | **~$2.70** |

> [!note] Calcul
> `cout = (input_tokens * $15 / 1M) + (output_tokens * $75 / 1M)`
> Exemple moyen : `(40000 * 0.000015) + (16000 * 0.000075) = $0.60 + $1.20 = $1.80`

---

## Budget par agent (estimation mensuelle)

Basee sur le [[operations/agent-workflows|schedule actuel]] des workflows GitHub Actions.

| Agent | Frequence | Turns/run | Cout estime/mois |
|-------|-----------|-----------|-----------------|
| **Orchestrator** | 5x/semaine | 8 | ~$36 |
| **[[agents/sage-memory\|Sage]]** | 1x/semaine | 8 | ~$7.20 |
| **[[agents/nexus-memory\|Nexus]]** | 1x/semaine | 8 | ~$7.20 |
| **[[agents/iris-memory\|Iris]]** | 7x/semaine | 5 | ~$23.50 |
| **[[agents/scout-memory\|Scout]]** | 2x/semaine | 5 | ~$6.70 |
| **[[agents/forge-memory\|Forge]]** | variable | 12 | variable |
| **[[agents/sentinel-memory\|Sentinel]]** | variable | 5 | variable |
| **[[agents/lumen-memory\|Lumen]]** | variable | 5 | variable |
| **[[agents/ralph-memory\|Ralph]]** | variable | 8 | variable |
| **[[agents/aria-memory\|Aria]]** | variable | 8 | variable |
| **Total fixe** | -- | -- | **~$80/mois** |

> [!tip] Budget variable
> Les agents a frequence variable (Forge, Sentinel, Lumen, Ralph, Aria) ajoutent un cout supplementaire selon la charge. Prevoir **~$30-50/mois** de marge pour les runs ad hoc et les re-runs apres echec.

---

## Strategies d'optimisation

### Skills vs MCP

| Methode | Cout en tokens | Quand utiliser |
|---------|---------------|----------------|
| **Skill** (`.claude/commands/`) | **0 tokens** | Taches repetitives, workflows standardises |
| **MCP call** | ~500-2000 tokens/appel | Acces a des donnees externes, API tierces |

Voir [[tech/skills-registry]] pour le catalogue complet des skills disponibles.

### Delegation Gemini

Pour les fichiers volumineux (>50KB), deleguer l'analyse a Gemini via `gemini_analyze` :

```bash
# Cout Gemini ~10x moins cher que Claude Opus
# Ideal pour : rapports longs, logs, CSV, revue de code bulk
gemini_analyze --file large_report.csv --prompt "Resume les tendances"
```

> [!important] Regle de delegation
> Si le fichier depasse 50KB ou si la tache est purement extractive (pas de raisonnement complexe), **toujours deleguer a Gemini**.

### Parametres de controle

```yaml
# Dans le workflow GitHub Actions
max_turns: 8          # Reduire au minimum necessaire
allowed_tools:        # Restreindre pour eviter exploration inutile
  - Read
  - Write
  - Grep
  - Bash(git:*)
```

### Vault protocol

- Lire **seulement les fichiers pertinents**, pas tout le vault
- Utiliser `INDEX.md` comme point d'entree pour naviguer
- Resumer avant d'inclure dans le contexte
- Ne pas lire un fichier en entier si une section suffit (parametre `offset` + `limit`)

### Token discipline (de CLAUDE.md)

- Resumer les contenus longs avant injection dans le prompt
- Preferer les references (`[[wikilink]]`) aux citations completes
- Structurer les prompts pour minimiser le contexte necessaire
- Utiliser des formats compacts (JSON, tableaux) plutot que prose

---

## KPIs de suivi

| KPI | Formule | Cible |
|-----|---------|-------|
| **Cout/run** | tokens * tarif | < $2.00 moyen |
| **Cout/agent/mois** | somme des runs mensuels | < budget alloue |
| **Ratio skills/MCP** | nb skills / nb MCP calls | > 2:1 |
| **Taux de delegation Gemini** | runs Gemini / runs totaux | > 30% pour taches extractives |

Suivi dans [[operations/kpis]] et le [[tech/infrastructure|dashboard Netlify]].

---

## Voir aussi

- [[tech/skills-registry]] -- Catalogue des skills (cout zero)
- [[tech/mcp-servers]] -- Serveurs MCP et leur cout en tokens
- [[operations/kpis]] -- Metriques globales du systeme
- [[agents/prompt-engineering]] -- Optimisation des prompts pour reduire les tokens

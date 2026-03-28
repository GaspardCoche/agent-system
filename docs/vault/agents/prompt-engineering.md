---
title: "Prompt Engineering -- Guide & Patterns"
id: agents-prompt-engineering
type: agent
tags: [agent, prompt, engineering, patterns, optimization, sage]
agents: [sage]
updated: 2026-03-28
---

# Prompt Engineering -- Guide & Patterns

*Lie a [[INDEX]] -- [[agents/creation-guide]] -- [[agents/communication-protocol]] -- [[agents/sage-memory]]*

> [!info] Ce guide definit comment ecrire, evaluer et ameliorer les prompts des agents du systeme.
> **Sage utilise ce fichier comme reference chaque dimanche** pour analyser et proposer des ameliorations.
> Un bon prompt = runs fiables, tokens optimises, retrospectives riches.

---

## Structure obligatoire d'un prompt agent

Chaque prompt dans `agent_prompts/<nom>.md` DOIT suivre cette structure exacte. L'ordre des sections est important car il influence la hierarchie d'attention du modele.

```markdown
# {Agent Name}

## Role
Tu es {nom}, l'agent {role} du systeme multi-agents.
{Description precise du role en 2-3 phrases. Inclure le perimetre
et ce que l'agent ne doit PAS faire.}

## Contexte Systeme
- Repo: GaspardCoche/agent-system
- Vault: docs/vault/ (knowledge graph persistant)
- Skills: skills/registry.json
- Dashboard: https://gaspardcoche.github.io/agent-system/

## Protocole Vault (OBLIGATOIRE)
1. Lire docs/vault/INDEX.md
2. Lire docs/vault/agents/{nom}-memory.md
3. Lire les fichiers vault pertinents a la tache
4. Apres execution: mettre a jour ta memoire
5. Commit: `vault: update {nom} memory — {resume bref}`

## Outils Disponibles
- {liste exhaustive des MCPs et tools autorises}
- TOUJOURS verifier skills/registry.json avant d'utiliser un MCP
- Si un skill valide existe, l'utiliser via Bash(python3 skills/validated/NOM.py ...)

## Format de Sortie
Ecrire dans /tmp/agent_result.json:
```json
{
  "agent": "{nom}",
  "task_id": "{source}",
  "status": "complete | failed | needs_retry | pending_approval",
  "summary": "150 mots max",
  "findings": [],
  "next_actions": [],
  "artifacts": [],
  "next_agent": "null",
  "retry_reason": "null",
  "retrospective": {
    "what_worked": "",
    "what_failed": "",
    "mcp_patterns": [],
    "improvement_suggestion": ""
  }
}
```

## Contraintes
- DRY_RUN: si true, generer preview sans executer
- Max {N} turns (3 simple / 8 moyen / 12 complexe)
- Budget tokens: {estimation}
- Ne jamais marquer complete sans que tous les artifacts requis existent
- Lire memory/lessons_learned.md avant toute tache complexe

## Exemples
### Exemple 1 : {Tache simple}
Input: {description}
Actions: {etapes}
Output: {resultat attendu}

### Exemple 2 : {Tache avec erreur}
Input: {description}
Erreur: {ce qui echoue}
Self-correction: {comment corriger}
Output: {resultat attendu}
```

> [!warning] Ne pas depasser 2000 tokens pour le prompt complet. Au-dela, le modele perd le focus sur les sections finales (contraintes, exemples) qui sont pourtant critiques.

---

## Patterns efficaces

### Pattern 1 : Chain-of-thought

Force l'agent a planifier avant d'agir. Reduit les erreurs sur les taches complexes.

```markdown
## Methode de travail
Avant toute action :
1. Lis les fichiers vault pertinents
2. Explique ton plan en 3 etapes maximum
3. Execute chaque etape en verifiant le resultat
4. Si une etape echoue, diagnostique avant de continuer
```

**Quand l'utiliser** : Taches multi-step (Nexus audit, Scout enrichissement, Forge implementation).
**Impact mesure** : Taux de succes +15%, tokens +10% (compromis acceptable).

### Pattern 2 : Vault-first

Garantit que l'agent a le contexte avant d'agir. Evite les actions basees sur des hypotheses.

```markdown
## Protocole Vault (OBLIGATOIRE)
AVANT toute action :
1. Lire docs/vault/INDEX.md -- vue d'ensemble
2. Lire docs/vault/agents/{nom}-memory.md -- ton contexte accumule
3. Lire les fichiers vault cites dans la tache
Ne commence PAS la tache tant que ces lectures ne sont pas faites.
```

**Quand l'utiliser** : Tous les agents, sans exception.
**Impact mesure** : Qualite des outputs +25%, erreurs repetees -40%.

### Pattern 3 : Self-correction

Permet a l'agent de recuperer d'une erreur sans intervention humaine.

```markdown
## Auto-correction
Si un test echoue ou si le resultat est invalide :
1. Diagnostique la cause (lire l'erreur, verifier les inputs)
2. Corrige l'approche
3. Re-execute
Maximum 3 cycles de correction. Si l'erreur persiste apres 3 cycles,
marque status: "needs_retry" avec retry_reason detaille.
```

**Quand l'utiliser** : Forge (tests), Sentinel (validation), Nexus (API calls).
**Impact mesure** : Taux de completion +20%, mais tokens +30% en cas de correction.

### Pattern 4 : DRY_RUN gate

Protege contre les actions irreversibles en mode preview.

```markdown
## Mode DRY_RUN
Si la variable d'environnement DRY_RUN=true :
- Generer un preview complet de ce qui SERAIT fait
- Ecrire le preview dans /tmp/agent_result.json avec status: "pending_approval"
- NE PAS executer d'actions externes (pas d'ecriture CRM, pas de modif Ads, pas d'envoi email)
- Le preview doit etre suffisamment detaille pour valider avant execution
```

**Quand l'utiliser** : Tout agent qui modifie des donnees externes (Aria/CRM, Nexus/Ads, Iris/Email).
**Impact mesure** : Zero actions irreversibles non desirees depuis l'implementation.

### Pattern 5 : Retrospective obligatoire

Alimente le cycle d'amelioration Sage.

```markdown
## Retrospective
TOUJOURS remplir le champ retrospective dans le resultat JSON, meme si tout a fonctionne :
- what_worked: ce qui a bien fonctionne (patterns, approches, outils)
- what_failed: ce qui a echoue ou pris trop de temps (meme les petits problemes)
- mcp_patterns: liste des outils utilises au format {tool_name}:{context}:{count}x
- improvement_suggestion: une proposition concrete d'amelioration
Une retrospective vide est INACCEPTABLE -- c'est le feedback pour Sage.
```

**Quand l'utiliser** : Tous les agents, sans exception.
**Impact mesure** : Permet a Sage d'identifier les prompts a ameliorer et les skills candidats.

### Pattern 6 : Preflight validation

Verifie les preconditions avant de lancer une tache couteuse.

```markdown
## Verification pre-execution
Avant de commencer la tache principale :
1. Verifier que tous les secrets necessaires sont disponibles
2. Verifier que les fichiers sources existent
3. Verifier que les APIs sont accessibles (ping rapide)
Si une precondition echoue, marque status: "failed" immediatement
avec un message clair. Ne pas gaspiller de tokens a tenter l'impossible.
```

**Quand l'utiliser** : Agents dependant d'APIs externes (Nexus, Aria, Scout, Iris).
**Impact mesure** : Reduction de 60% des runs echoues apres 5+ turns.

---

## Anti-patterns a eviter

> [!danger] Ces erreurs de prompt sont les plus couteuses en tokens et en qualite.

| # | Anti-pattern | Symptome | Solution |
|---|-------------|----------|----------|
| 1 | **Prompt trop long** (>2000 tokens) | Agent perd le focus sur les dernieres sections | Couper, resumer, deplacer les details dans le vault |
| 2 | **Pas de format de sortie clair** | Output JSON inconsistant, orchestrateur crash | Inclure le schema JSON complet dans le prompt |
| 3 | **Pas de contraintes** | Agent fait trop (surconsommation) ou pas assez (incomplete) | Definir max_turns, budget tokens, DRY_RUN |
| 4 | **Pas d'exemples** | Agent improvise, resultats imprevisibles | Minimum 2 exemples (succes + erreur) |
| 5 | **Outils trop larges** | Agent utilise des MCPs inutiles, tokens gaspilles | `allowed_tools` specifique par agent ([[agents/tool-matrix]]) |
| 6 | **Instructions contradictoires** | Agent hesite, produit des resultats partiels | Relire le prompt, eliminer les ambiguites |
| 7 | **Pas de lecture vault** | Agent sans contexte, refait des erreurs deja documentees | Pattern Vault-first obligatoire |
| 8 | **Retrospective optionnelle** | Sage n'a pas de feedback, pas d'amelioration | Pattern Retrospective obligatoire |
| 9 | **Role trop vague** | Agent depasse son perimetre ou sous-performe | "Tu es X" + "Tu ne fais PAS Y" |
| 10 | **Pas de gestion d'erreur** | Run echoue sans information utile | Pattern Self-correction + Preflight |

---

## Metriques de qualite d'un prompt

### Metriques quantitatives

| Metrique | Seuil bon | Seuil a ameliorer | Source |
|----------|----------|-------------------|--------|
| Taux de succes des runs | > 90% | < 75% | `docs/data/runs.json` |
| Tokens moyens par run (simple) | < 50K | > 80K | Logs GitHub Actions |
| Tokens moyens par run (complexe) | < 150K | > 250K | Logs GitHub Actions |
| Temps moyen d'execution | < 5 min | > 10 min | GitHub Actions |
| Retrospective `what_failed` non-vide | Indicateur, pas seuil | Si > 50% des runs | `agent_result.json` |

### Metriques qualitatives

| Metrique | Comment evaluer | Frequence |
|----------|----------------|-----------|
| **Artifact completion** | Tous les artifacts requis sont produits et non vides | Chaque run |
| **Coherence memoire** | La memoire agent est a jour et coherente | Sage hebdo |
| **Pertinence findings** | Les findings sont utiles et actionnables | Revue humaine mensuelle |
| **Self-correction efficace** | Correction reussie vs echec apres 3 cycles | Sage hebdo |
| **Vault contribution** | L'agent enrichit le vault (pas juste lecture) | Sage hebdo |

---

## Cycle d'amelioration Sage

[[agents/sage-memory|Sage]] est responsable de l'amelioration continue des prompts. Voici le cycle :

### Etape 1 : Collecte (dimanche, automatique)

```
Sage lit :
- Toutes les retrospectives de la semaine (agent_result.json des runs)
- Les metriques de runs.json (taux succes, tokens)
- Les erreurs dans agents/error-patterns
- Le vault pour le contexte
```

### Etape 2 : Analyse

```
Pour chaque agent :
1. Taux de succes < 90% ? → Prompt a revoir
2. Tokens moyens > budget ? → Prompt trop verbeux ou outils trop larges
3. what_failed recurrent ? → Pattern a corriger
4. mcp_patterns repetitifs ? → Candidat skill (voir [[tech/skills-registry]])
5. improvement_suggestion coherente ? → Integrer dans le prompt
```

### Etape 3 : Proposition

```
Si une amelioration est identifiee :
1. Sage cree une branche feat/sage-improve-{agent}-{date}
2. Modifie le prompt dans agent_prompts/{agent}.md
3. Cree une PR avec :
   - Avant/apres du prompt
   - Justification basee sur les metriques
   - Impact attendu
4. Tag la PR avec "sage-improvement"
```

### Etape 4 : Validation

```
1. Review humain ou automatique (Sentinel)
2. Si approuvee : merge dans main
3. Sage met a jour sa memoire avec le resultat
4. Au prochain run de l'agent, le nouveau prompt est utilise
5. Sage compare les metriques avant/apres au cycle suivant
```

> [!tip] Le cycle d'amelioration est le mecanisme principal d'auto-optimisation du systeme. Chaque retrospective alimente Sage, qui ameliore les prompts, ce qui ameliore les retrospectives.

---

## Exemples de prompts par complexite

### Simple (3 turns, <50K tokens)

Agents : Iris (digest), Ralph (routing)

```markdown
Caracteristiques :
- 1 action principale, pas de branchement
- Pas de self-correction necessaire
- Outils limites (2-3 MCPs max)
- Exemples : 1 suffit
- Prompt : ~800 tokens
```

### Moyen (8 turns, <150K tokens)

Agents : Scout (enrichissement), Sentinel (QA), Lumen (analyse)

```markdown
Caracteristiques :
- 2-4 actions enchainées
- Self-correction avec 1-2 cycles max
- 3-5 MCPs
- Exemples : 2 minimum (succes + erreur)
- Prompt : ~1200 tokens
```

### Complexe (12 turns, >150K tokens)

Agents : Nexus (audit Ads), Forge (implementation), Aria (enrichissement CRM)

```markdown
Caracteristiques :
- 5+ actions avec branchements conditionnels
- Self-correction avec 3 cycles
- 5+ MCPs + skills
- Exemples : 3 minimum (succes + erreur + edge case)
- Prompt : ~1800 tokens (max 2000)
- Preflight validation obligatoire
- DRY_RUN gate obligatoire
```

---

## Checklist de review d'un prompt

Utiliser cette checklist lors de la review d'une PR de modification de prompt :

| # | Critere | Verifie |
|---|---------|---------|
| 1 | Structure obligatoire respectee (7 sections) | [ ] |
| 2 | Role precis avec perimetre positif ET negatif | [ ] |
| 3 | Protocole Vault present avec les 3 lectures | [ ] |
| 4 | Outils alignes avec [[agents/tool-matrix]] | [ ] |
| 5 | Format de sortie JSON complet | [ ] |
| 6 | Contraintes : DRY_RUN, max_turns, budget tokens | [ ] |
| 7 | Exemples : minimum 2, dont 1 cas d'erreur | [ ] |
| 8 | Prompt < 2000 tokens | [ ] |
| 9 | Pas d'instructions contradictoires | [ ] |
| 10 | Patterns pertinents utilises (vault-first, etc.) | [ ] |
| 11 | Anti-patterns absents | [ ] |
| 12 | Retrospective obligatoire mentionnee | [ ] |

---

## Fichiers lies

- [[agents/creation-guide]] -- Guide complet de creation d'agent
- [[agents/communication-protocol]] -- Format JSON des inputs/outputs
- [[agents/error-patterns]] -- Erreurs connues et prevention
- [[agents/tool-matrix]] -- Matrice des outils par agent
- [[agents/sage-memory]] -- Memoire et historique de Sage
- [[tech/skills-registry]] -- Skills valides (alternative aux MCPs)
- [[operations/kpis]] -- KPIs systeme et metriques de qualite

---

*Derniere mise a jour : 2026-03-28 -- Maintenu par [[agents/sage-memory|Sage]]*

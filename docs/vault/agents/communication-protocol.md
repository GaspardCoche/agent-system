---
title: Protocole de Communication Inter-Agents
id: agents-communication-protocol
type: agent
tags: [agent, protocol, communication, json, task, result, retrospective]
agents: [all]
updated: 2026-03-28
---

# Protocole de Communication Inter-Agents

*Lie a [[INDEX]] -- [[agents/creation-guide]] -- [[agents/prompt-engineering]] -- [[operations/agent-workflows]]*

> [!info] Ce fichier definit le contrat exact de communication entre tous les agents du systeme.
> **Chaque agent DOIT respecter ce protocole.** C'est la base de l'orchestration, du chaining, du reporting et de l'amelioration continue via [[agents/sage-memory|Sage]].

---

## Vue d'ensemble -- Flux de communication

```
┌─────────────────────────────────────────────────────────────────────┐
│                     FLUX INTER-AGENTS                               │
│                                                                     │
│  Trigger                                                            │
│    │                                                                │
│    ▼                                                                │
│  Ralph (router) ──────► /tmp/agent_task.json                       │
│    │                         │                                      │
│    │                         ▼                                      │
│    │                    Agent(s) executent                          │
│    │                         │                                      │
│    │                         ▼                                      │
│    │                    /tmp/agent_result.json                      │
│    │                         │                                      │
│    ▼                         ▼                                      │
│  Orchestrator (aggregate) ◄──┘                                     │
│    │                                                                │
│    ├──► Report (docs/reports/)                                     │
│    ├──► Dashboard (docs/data/runs.json)                            │
│    ├──► Vault update (docs/vault/agents/{nom}-memory.md)           │
│    │                                                                │
│    ▼                                                                │
│  Sage (weekly retrospective analysis)                              │
│    │                                                                │
│    ├──► Prompt improvements (PRs)                                  │
│    ├──► Skill candidates (skills/registry.json)                    │
│    └──► Error patterns (agents/error-patterns.md)                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Input -- `/tmp/agent_task.json`

Ce fichier est cree par l'orchestrateur (Dispatch) ou Ralph avant le lancement de l'agent. L'agent le lit au debut de son execution.

### Schema complet

```json
{
  "task_id": "issue_42 | run_12345",
  "agent": "scout",
  "description": "Enrichir les leads depuis la feuille Google Sheets",
  "context": {
    "source": "workflow_dispatch | repository_dispatch | orchestrator",
    "trigger_by": "user | ralph | orchestrator",
    "dry_run": false,
    "priority": "normal | high | critical",
    "parent_task_id": "null | task_id du parent si sous-tache",
    "chain_position": 1,
    "chain_total": 3
  },
  "inputs": {
    "sheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms",
    "columns_to_enrich": ["email", "phone"],
    "max_rows": 100,
    "filters": {
      "status": "new",
      "source": "linkedin"
    }
  },
  "vault_files": [
    "docs/vault/INDEX.md",
    "docs/vault/agents/scout-memory.md",
    "docs/vault/leadgen/sources-web.md",
    "docs/vault/leadgen/cleaning-rules.md"
  ],
  "previous_results": [
    {
      "agent": "aria",
      "task_id": "run_12340",
      "status": "complete",
      "summary": "50 leads qualifies prets pour enrichissement",
      "artifacts": ["/tmp/qualified_leads.csv"]
    }
  ],
  "constraints": {
    "max_turns": 8,
    "budget_tokens": 150000,
    "timeout_minutes": 15,
    "allowed_tools": ["Bash", "Read", "Write", "mcp__firecrawl__*", "mcp__filesystem__*"]
  }
}
```

### Description des champs

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| `task_id` | string | Oui | Identifiant unique : numero d'issue ou ID de run |
| `agent` | string | Oui | Nom de l'agent cible |
| `description` | string | Oui | Description humaine de la tache |
| `context.source` | enum | Oui | Origine du trigger |
| `context.trigger_by` | enum | Oui | Qui a declenche (user, ralph, orchestrator) |
| `context.dry_run` | boolean | Oui | Mode preview si true |
| `context.priority` | enum | Non | `normal` (defaut), `high`, `critical` |
| `context.parent_task_id` | string | Non | Si sous-tache d'une tache plus large |
| `context.chain_position` | number | Non | Position dans une chaine d'agents (1-based) |
| `context.chain_total` | number | Non | Nombre total d'agents dans la chaine |
| `inputs` | object | Oui | Parametres specifiques a la tache (varies par agent) |
| `vault_files` | array | Oui | Fichiers vault a lire en priorite |
| `previous_results` | array | Non | Resultats des agents precedents dans la chaine |
| `constraints` | object | Non | Limites d'execution (sinon, defauts du workflow) |

> [!tip] `vault_files` est une liste **ordonnee** : l'agent doit les lire dans cet ordre. Le premier est toujours `INDEX.md`, le deuxieme est toujours la memoire agent.

---

## Output -- `/tmp/agent_result.json`

Ce fichier est ecrit par l'agent a la fin de son execution. L'orchestrateur le lit pour le reporting, le chaining et le dashboard.

### Schema complet

```json
{
  "agent": "scout",
  "task_id": "run_12345",
  "status": "complete",
  "summary": "150 leads enrichis depuis Google Sheets. 142 emails trouves, 98 telephones. 8 leads exclus (RGPD opt-out). Temps total: 4 min.",
  "findings": [
    "Le taux d'enrichissement email est de 94.7% (142/150)",
    "8 leads avaient un opt-out RGPD et ont ete exclus",
    "La source LinkedIn a le meilleur taux d'enrichissement (97%)"
  ],
  "next_actions": [
    "Aria devrait integrer les 142 leads enrichis dans HubSpot",
    "Verifier les 8 leads RGPD pour mise a jour du registre opt-out"
  ],
  "artifacts": [
    "/tmp/enriched_leads.csv",
    "docs/reports/scout-enrichment-20260328.md"
  ],
  "next_agent": "aria",
  "retry_reason": null,
  "retrospective": {
    "what_worked": "Le skill firecrawl_scrape a fonctionne parfaitement. Le cache vault a evite 20 requetes inutiles.",
    "what_failed": "3 URLs ont timeout (>30s). Le fallback sur un second scraper n'etait pas configure.",
    "mcp_patterns": [
      "firecrawl_scrape:url:45x",
      "firecrawl_search:domain:12x",
      "mcp__filesystem__read_file:csv:3x",
      "mcp__filesystem__write_file:csv:1x"
    ],
    "improvement_suggestion": "Ajouter un timeout de 15s avec fallback sur firecrawl_search pour les URLs lentes."
  }
}
```

### Description des champs

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| `agent` | string | Oui | Nom de l'agent qui a execute |
| `task_id` | string | Oui | Repris du task input |
| `status` | enum | Oui | Voir section "Regles de status" ci-dessous |
| `summary` | string | Oui | Resume en 150 mots max de ce qui a ete fait |
| `findings` | array | Oui | Liste de faits decouverts (peut etre vide `[]`) |
| `next_actions` | array | Oui | Actions recommandees (peut etre vide `[]`) |
| `artifacts` | array | Oui | Chemins des fichiers produits (peut etre vide `[]`) |
| `next_agent` | string/null | Oui | Agent suivant dans la chaine, ou `null` |
| `retry_reason` | string/null | Oui | Raison du retry si `status: needs_retry`, sinon `null` |
| `retrospective` | object | Oui | TOUJOURS rempli -- voir section dediee |

---

## Regles de status

> [!warning] Le champ `status` determine le comportement de l'orchestrateur. Un mauvais status peut bloquer ou corrompre une chaine.

| Status | Signification | Comportement orchestrateur | Quand l'utiliser |
|--------|--------------|---------------------------|-----------------|
| `complete` | Tache terminee avec succes | Passe au `next_agent` si defini, sinon cloture | Tous les artifacts requis existent et sont valides |
| `failed` | Erreur non recuperable | Alerte, pas de chaining, log dans error-patterns | API down, secret manquant, erreur logique fatale |
| `needs_retry` | Erreur recuperable | Re-lance l'agent avec `retry_reason` dans le contexte | Timeout, rate limit, erreur transitoire |
| `pending_approval` | Action irreversible en attente | Poste un commentaire GitHub, attend label `approved` | Ecriture CRM, modification Ads, envoi email |

### Regles strictes

1. **Ne jamais marquer `complete` si un artifact requis est absent ou vide.** Verifier avec `ls -la` avant d'ecrire le status.

2. **`failed` doit toujours inclure un `summary` explicatif.** "Ca n'a pas marche" n'est pas acceptable -- decrire l'erreur, sa cause probable, et ce qui a ete tente.

3. **`needs_retry` doit toujours inclure un `retry_reason` actionnable.** L'orchestrateur ou l'agent au retry doit pouvoir corriger sans deviner.

4. **`pending_approval` ne s'applique qu'aux actions irreversibles.** Ne pas l'utiliser pour des actions internes (ecriture vault, generation rapport).

---

## Chaining -- Enchainement d'agents

Quand `next_agent` est non-null, l'orchestrateur lance automatiquement l'agent suivant.

### Mecanisme

```
Agent A (status: complete, next_agent: "B")
    │
    ▼
Orchestrator lit agent_result.json de A
    │
    ├── Copie les artifacts de A dans les inputs de B
    ├── Ajoute le result de A dans previous_results de B
    ├── Cree /tmp/agent_task.json pour B
    │
    ▼
Agent B demarre avec le contexte de A
```

### Chaines courantes

| Chaine | Agents | Trigger | Description |
|--------|--------|---------|-------------|
| Enrichissement lead | Scout → Aria | dispatch | Scout enrichit, Aria integre en CRM |
| QA code | Forge → Sentinel | PR | Forge implemente, Sentinel valide |
| Analyse Ads | Nexus → Lumen | dispatch | Nexus collecte, Lumen analyse en profondeur |
| Audit complet | Scout → Aria → Nexus → Lumen | issue | Pipeline complet de qualification |

### Regles de chaining

1. **Maximum 4 agents dans une chaine.** Au-dela, le contexte se dilue et les tokens explosent.
2. **Chaque agent de la chaine a acces aux `previous_results`.** Il peut lire les findings et artifacts des agents precedents.
3. **Si un agent echoue, la chaine s'arrete.** L'orchestrateur ne lance pas le `next_agent` sur un `failed`.
4. **`needs_retry` bloque la chaine** jusqu'a resolution du retry.
5. **`pending_approval` bloque la chaine** jusqu'a validation humaine.

---

## Retrospective -- Format et regles

> [!danger] La retrospective est OBLIGATOIRE, meme si tout a fonctionne parfaitement. C'est le mecanisme d'auto-amelioration du systeme via [[agents/sage-memory|Sage]].

### Champs

| Champ | Format | Exemple | Utilise par |
|-------|--------|---------|-------------|
| `what_worked` | Texte libre, 1-3 phrases | "Le skill firecrawl_scrape a fonctionne. Le cache vault a evite 20 requetes." | Sage (renforcement positif) |
| `what_failed` | Texte libre, 1-3 phrases | "3 URLs ont timeout. Le fallback n'etait pas configure." | Sage (identification problemes) |
| `mcp_patterns` | Array de strings format `{tool}:{context}:{count}x` | `["firecrawl_scrape:url:45x", "github__add_issue_comment:1x"]` | Sage (detection skills candidats) |
| `improvement_suggestion` | Texte libre, 1 phrase actionnable | "Ajouter un timeout de 15s avec fallback." | Sage (proposition PR) |

### Format `mcp_patterns`

```
{nom_outil}:{contexte}:{nombre}x

Exemples:
  firecrawl_scrape:url:45x          → 45 appels a firecrawl_scrape sur des URLs
  firecrawl_search:domain:12x       → 12 recherches par domaine
  github__add_issue_comment:1x      → 1 commentaire GitHub
  mcp__hubspot__hubspot-search-objects:contact:8x → 8 recherches HubSpot
```

> [!tip] Sage analyse ces patterns chaque semaine. Si un pattern apparait > 10x par semaine avec le meme contexte, Sage le propose comme candidat skill dans [[tech/skills-registry]]. Un skill valide remplace les appels MCP et economise des tokens.

### Retrospective en cas de succes total

Meme si tout a fonctionne, remplir :

```json
{
  "what_worked": "Toutes les etapes ont fonctionne sans erreur. Le prompt actuel est efficace pour cette tache.",
  "what_failed": "Rien a signaler.",
  "mcp_patterns": ["outil:contexte:Nx"],
  "improvement_suggestion": "RAS ou suggestion d'optimisation mineure."
}
```

### Retrospective en cas d'echec

```json
{
  "what_worked": "La lecture vault et la planification etaient correctes.",
  "what_failed": "L'API HubSpot a renvoye 429 (rate limit) apres 50 requetes. Le batch n'est pas implemente.",
  "mcp_patterns": ["hubspot-search-objects:contact:50x", "hubspot-search-objects:429_error:1x"],
  "improvement_suggestion": "Implementer le batching HubSpot (max 100/10s) ou creer un skill avec rate limiting integre."
}
```

---

## Mise a jour vault post-execution

Chaque agent DOIT mettre a jour sa memoire apres execution :

### Quoi mettre a jour

| Fichier | Quoi | Quand |
|---------|------|-------|
| `docs/vault/agents/{nom}-memory.md` | Historique des runs, patterns, erreurs | Chaque run |
| Fichier vault du domaine concerne | Nouvelles informations decouvertes | Si applicable |
| `docs/data/runs.json` | Nouveau run (via `generate_report.py`) | Chaque run (step report) |

### Format du commit

```
vault: update {agent} memory — {resume bref}
```

Exemples :
- `vault: update scout memory — 150 leads enrichis, 3 timeouts detectes`
- `vault: update nexus memory — audit Google Ads score 58/100`
- `vault: update sage memory — 2 prompts ameliores, 1 skill propose`

> [!warning] Le commit doit etre fait avec `git pull --rebase origin main` avant le push. Sinon, risque de rejet si un autre agent a pousse entre-temps. Voir [[agents/error-patterns]] erreur #13.

---

## Validation -- Schema JSON

Pour valider qu'un `agent_result.json` est conforme, utiliser ce script :

```python
import json
import sys

REQUIRED_FIELDS = ["agent", "task_id", "status", "summary", "findings",
                   "next_actions", "artifacts", "next_agent", "retry_reason",
                   "retrospective"]
VALID_STATUSES = ["complete", "failed", "needs_retry", "pending_approval"]
RETRO_FIELDS = ["what_worked", "what_failed", "mcp_patterns", "improvement_suggestion"]

def validate(path):
    with open(path) as f:
        data = json.load(f)
    errors = []
    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"Champ manquant: {field}")
    if data.get("status") not in VALID_STATUSES:
        errors.append(f"Status invalide: {data.get('status')}")
    if data.get("status") == "needs_retry" and not data.get("retry_reason"):
        errors.append("needs_retry sans retry_reason")
    retro = data.get("retrospective", {})
    for field in RETRO_FIELDS:
        if field not in retro:
            errors.append(f"Retrospective champ manquant: {field}")
    if not errors:
        print("VALID")
    else:
        print("ERRORS:", errors)
        sys.exit(1)

if __name__ == "__main__":
    validate(sys.argv[1])
```

---

## Fichiers lies

- [[agents/creation-guide]] -- Guide complet de creation d'agent
- [[agents/prompt-engineering]] -- Comment ecrire les prompts
- [[agents/error-patterns]] -- Erreurs connues et prevention
- [[agents/tool-matrix]] -- Matrice des outils par agent
- [[agents/dispatch-log]] -- Historique des orchestrations
- [[operations/agent-workflows]] -- Chaines d'agents et orchestration
- [[tech/mcp-servers]] -- Serveurs MCP et configuration
- [[tech/data-schemas]] -- Schemas de validation

---

*Derniere mise a jour : 2026-03-28 -- Ce protocole s'applique a tous les agents sans exception.*

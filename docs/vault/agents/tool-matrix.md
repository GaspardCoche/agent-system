---
title: Matrice des Outils par Agent
id: agents-tool-matrix
type: agent
tags: [agent, tools, mcp, permissions, matrix]
agents: [all]
updated: 2026-03-28
---

# Matrice des Outils par Agent

*Lie a [[INDEX]] -- [[tech/mcp-servers]] -- [[tech/skills-registry]] -- [[security/access-control]] -- [[agents/creation-guide]]*

> [!info] Cette matrice definit les permissions exactes de chaque agent sur chaque outil.
> **Chaque workflow DOIT configurer `allowed_tools` en accord avec cette matrice.**
> Le principe du moindre privilege s'applique : un agent n'a acces qu'aux outils strictement necessaires a son role.

---

## Matrice de permissions

| Outil / MCP | Dispatch | Scout | Aria | Nexus | Iris | Sage | Forge | Sentinel | Lumen | Ralph |
|-------------|----------|-------|------|-------|------|------|-------|----------|-------|-------|
| **Bash** | R | R | R | R | R | R | RW | R | R | R |
| **Read/Write/Edit** | RW | R | R | R | R | RW | RW | R | R | R |
| **GitHub MCP** | RW | R | R | R | R | RW | RW | R | R | RW |
| **Firecrawl** | - | RW | - | - | RW | - | - | - | - | - |
| **Google Ads MCP** | - | - | - | RW | - | - | - | - | R | - |
| **HubSpot MCP** | - | - | RW | - | - | - | - | - | R | - |
| **Google Sheets** | - | RW | R | - | - | - | - | - | R | - |
| **Playwright** | - | RW | - | - | - | - | - | - | - | - |
| **Memory MCP** | RW | RW | RW | RW | RW | RW | RW | RW | RW | RW |
| **Filesystem** | RW | RW | RW | RW | RW | RW | RW | RW | RW | RW |
| **Gemini (skill)** | - | - | - | R | R | R | - | - | RW | - |
| **Slack (skill)** | W | W | W | W | W | W | W | W | W | W |
| **Lemlist MCP** | - | - | RW | - | - | - | - | - | R | - |
| **Google Analytics** | - | - | - | R | - | - | - | - | RW | - |
| **Puppeteer** | - | RW | - | - | - | - | - | - | - | - |

**Legende** : R = Read only, W = Write only, RW = Read+Write, - = Aucun acces

---

## Outils critiques -- Agents autorises

> [!danger] Ces outils peuvent modifier des donnees externes. L'acces est strictement limite.

### HubSpot MCP (CRM)

| Permission | Agent | Justification |
|-----------|-------|---------------|
| RW | Aria | Seul agent autorise a ecrire dans le CRM (creation/update contacts, companies, deals) |
| R | Lumen | Lecture seule pour analyse et reporting |
| - | Tous les autres | Aucun acces -- le CRM est la source de verite business |

**Risques** : Creation de doublons, ecrasement de donnees, violation RGPD.
**Controle** : Aria doit utiliser `DRY_RUN` + `pending_approval` pour toute ecriture CRM.

### Google Ads MCP (Campagnes)

| Permission | Agent | Justification |
|-----------|-------|---------------|
| RW | Nexus | Seul agent autorise a modifier les campagnes Google Ads |
| R | Lumen | Lecture seule pour analyse cross-channel |
| - | Tous les autres | Aucun acces -- les modifications Ads impactent le budget |

**Risques** : Modification de budget, pause de campagnes performantes, erreurs GAQL en cascade.
**Controle** : Nexus DOIT respecter les [[agents/error-patterns]] erreurs #9-12.

> [!warning] Rappel -- Regles absolues Google Ads MCP :
> - JAMAIS `.type` dans les conditions GAQL
> - JAMAIS d'appels paralleles
> - JAMAIS `metrics.optimization_score` avec segments de date
> - JAMAIS de metriques sur `ad_group_criterion`
> Customer ID EMAsphere : **7251903503**

### Firecrawl (Scraping web)

| Permission | Agent | Justification |
|-----------|-------|---------------|
| RW | Scout | Scraping de sources web pour enrichissement leads |
| RW | Iris | Scraping pour veille email et extraction de contenu |
| - | Tous les autres | Aucun acces -- le scraping consomme des credits API |

**Risques** : Surconsommation credits API, scraping de sites interdits, violation RGPD.
**Controle** : Toujours verifier `robots.txt` et respecter les rate limits.

### Lemlist MCP (Outreach)

| Permission | Agent | Justification |
|-----------|-------|---------------|
| RW | Aria | Gestion des campagnes et leads Lemlist |
| R | Lumen | Lecture stats pour reporting |
| - | Tous les autres | Aucun acces -- envoi d'emails automatises |

**Risques** : Envoi d'emails non souhaites, ajout de leads non qualifies, degradation reputation domaine.
**Controle** : Aria doit utiliser `pending_approval` avant tout envoi.

---

## Outils partages -- Tous agents

### Memory MCP

Tous les agents ont un acces RW au Memory MCP pour la gestion du knowledge graph persistent.

```
Utilisation : Stocker et recuperer des entites, relations et observations.
Frequence : Chaque run (lecture en debut, ecriture en fin).
Risque : Faible (donnees internes, pas d'impact externe).
```

### Filesystem MCP

Tous les agents ont un acces RW au Filesystem MCP pour la lecture et ecriture de fichiers locaux.

```
Utilisation : Lire le vault, ecrire les resultats, generer des rapports.
Repertoires autorises : /tmp/, docs/vault/, docs/reports/, docs/data/
Restriction : Ne JAMAIS ecrire dans .github/ ou agent_prompts/ (sauf Sage via PR).
```

### Slack (skill)

Tous les agents ont un acces W (ecriture seule) au skill Slack pour les notifications.

```
Utilisation : Envoyer des notifications sur les runs, erreurs, et resultats importants.
Canaux autorises : #agent-system, #alerts
Restriction : Pas de lecture des messages Slack.
```

---

## Configuration `allowed_tools` par agent

Pour configurer les permissions dans le workflow, utiliser le parametre `allowed_tools` du reusable workflow ou de l'action Claude :

### Dispatch (Orchestrateur)

```yaml
allowed_tools: "Bash(read),Read,Write,Edit,Glob,Grep,mcp__github__*,mcp__memory__*,mcp__filesystem__*"
```

### Scout (Intelligence web)

```yaml
allowed_tools: "Bash(read),Read,Glob,Grep,mcp__firecrawl__*,mcp__filesystem__*,mcp__memory__*,mcp__playwright__*"
```

### Aria (Leads & CRM)

```yaml
allowed_tools: "Bash(read),Read,Glob,Grep,mcp__hubspot__*,mcp__lemlist__*,mcp__filesystem__*,mcp__memory__*"
```

### Nexus (Google Ads)

```yaml
allowed_tools: "Bash(read),Read,Glob,Grep,mcp__google-ads__*,mcp__google-analytics__*,mcp__filesystem__*,mcp__memory__*"
```

### Iris (Email & digest)

```yaml
allowed_tools: "Bash(read),Read,Glob,Grep,mcp__firecrawl__*,mcp__filesystem__*,mcp__memory__*"
```

### Sage (Prompt engineering)

```yaml
allowed_tools: "Bash(read),Read,Write,Edit,Glob,Grep,mcp__github__*,mcp__filesystem__*,mcp__memory__*"
```

### Forge (Developpement)

```yaml
allowed_tools: "Bash,Read,Write,Edit,Glob,Grep,mcp__github__*,mcp__filesystem__*,mcp__memory__*"
```

### Sentinel (QA & tests)

```yaml
allowed_tools: "Bash(read),Read,Glob,Grep,mcp__github__*,mcp__filesystem__*,mcp__memory__*"
```

### Lumen (Analyse & donnees)

```yaml
allowed_tools: "Bash(read),Read,Glob,Grep,mcp__google-ads__search,mcp__google-analytics__*,mcp__hubspot__hubspot-search-objects,mcp__hubspot__hubspot-list-objects,mcp__filesystem__*,mcp__memory__*"
```

### Ralph (Automatisation)

```yaml
allowed_tools: "Bash(read),Read,Glob,Grep,mcp__github__*,mcp__filesystem__*,mcp__memory__*"
```

> [!tip] Noter les differences :
> - `Bash` vs `Bash(read)` -- Seul Forge a un acces Bash complet en ecriture
> - `mcp__google-ads__*` vs `mcp__google-ads__search` -- Lumen n'a acces qu'a la lecture
> - `mcp__hubspot__*` vs `mcp__hubspot__hubspot-search-objects` -- Lumen n'a acces qu'a la recherche

---

## Skills vs MCPs

> [!tip] Toujours verifier `skills/registry.json` avant d'utiliser un MCP. Un skill valide est plus rapide et consomme moins de tokens.

| Critere | MCP | Skill |
|---------|-----|-------|
| **Tokens** | Eleve (protocole MCP complet) | Faible (appel Python direct) |
| **Vitesse** | Moyenne (startup serveur) | Rapide (script local) |
| **Flexibilite** | Haute (toutes les operations) | Limitee (operations precodees) |
| **Fiabilite** | Variable (timeout, crash) | Haute (teste et valide) |
| **Quand utiliser** | Nouvelle operation, exploration | Operation repetitive et validee |

### Cycle de vie MCP → Skill

```
1. Agent utilise un MCP pour une tache
2. Le pattern apparait dans mcp_patterns de la retrospective
3. Sage detecte le pattern recurrent (>10x/semaine)
4. Sage propose la creation d'un skill dans skills/registry.json
5. Forge implemente le skill dans skills/validated/
6. Sentinel valide le skill
7. Le skill est marque "validated" dans le registry
8. Les agents utilisent le skill au lieu du MCP
```

Voir [[tech/skills-registry]] pour la liste des skills valides et candidats.

---

## Ajout d'un nouvel outil

Quand un nouvel outil (MCP ou skill) est ajoute au systeme :

1. **Mettre a jour cette matrice** avec les permissions par agent
2. **Mettre a jour [[tech/mcp-servers]]** avec la configuration du serveur
3. **Mettre a jour [[operations/secrets-matrix]]** si de nouveaux secrets sont requis
4. **Mettre a jour [[security/access-control]]** avec la politique d'acces
5. **Mettre a jour les workflows** des agents concernes (`allowed_tools`)
6. **Mettre a jour les prompts** des agents concernes (section Outils Disponibles)
7. **Tester** avec un dry_run sur chaque agent autorise

Suivre la procedure complete dans [[agents/creation-guide]] Etape 7.

---

## Audit de permissions

Sage verifie chaque semaine que les permissions reelles (dans les workflows) correspondent a cette matrice :

```bash
# Extraire les allowed_tools de chaque workflow
for f in .github/workflows/*.yml; do
  echo "=== $(basename $f) ==="
  grep -A1 "allowed_tools" "$f" 2>/dev/null || echo "  (not found)"
done
```

Si une divergence est detectee, Sage cree une issue avec le label `permission-drift`.

---

## Fichiers lies

- [[tech/mcp-servers]] -- Configuration detaillee des 10+ serveurs MCP
- [[tech/skills-registry]] -- 4 skills valides, cycle MCP → Skill
- [[security/access-control]] -- Politique de securite et controle d'acces
- [[agents/creation-guide]] -- Guide de creation d'agent (Etape 4 : allowed_tools)
- [[agents/prompt-engineering]] -- Section Outils Disponibles du prompt
- [[agents/error-patterns]] -- Erreurs liees aux outils (#9-12 Google Ads, #14 MCP timeout)
- [[operations/secrets-matrix]] -- Secrets necessaires pour chaque MCP

---

*Derniere mise a jour : 2026-03-28 -- Maintenu par [[agents/sage-memory|Sage]] en collaboration avec [[agents/sentinel-memory|Sentinel]]*

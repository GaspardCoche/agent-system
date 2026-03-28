---
title: "Patterns d'Erreurs -- Diagnostic & Prevention"
id: agents-error-patterns
type: agent
tags: [agent, errors, patterns, troubleshooting, lessons-learned, prevention]
agents: [sage, sentinel]
updated: 2026-03-28
---

# Patterns d'Erreurs -- Diagnostic & Prevention

*Lie a [[INDEX]] -- [[agents/creation-guide]] -- [[agents/prompt-engineering]] -- [[operations/runbooks]] -- [[agents/sage-memory]]*

> [!danger] Ce fichier documente toutes les erreurs connues du systeme multi-agents.
> **Lire ce fichier avant toute tache complexe.** Ne jamais refaire une erreur deja documentee ici.
> Chaque nouvelle erreur DOIT etre ajoutee ici ET dans `memory/lessons_learned.md`.

---

## Tableau de reference rapide

> [!danger] Erreurs critiques documentees

| # | Erreur | Cause | Prevention | Agent(s) |
|---|--------|-------|-----------|----------|
| 1 | `startup_failure` workflow | YAML invalide ou `default: ""` sur input workflow_call | Toujours utiliser `default: "none"` (jamais chaine vide) | Tous |
| 2 | Agent ne trouve pas son prompt | `agent_prompts/${{ inputs.agent_role }}.md` n'existe pas | Verifier que le fichier existe avant de lancer | Tous |
| 3 | Dashboard n'affiche pas les runs | `runs.json` pas mis a jour | Toujours passer `--output-dir` et `--dashboard-file` a `generate_report.py` | Tous |
| 4 | Graph vide | `graph.json` pas regenere | Lancer `vault_builder.py` apres modification du vault | Tous |
| 5 | HTTP 401 Unauthorized | CLAUDE_CODE_OAUTH_TOKEN expire | Regenerer via `claude setup-token` + `gh secret set` | Tous |
| 6 | PAT scope insuffisant | Scope `workflow` manquant | PAT doit avoir scope `repo` + `workflow` | Forge |
| 7 | Nexus silent failure | Pas de credentials Google Ads → mode template | Pre-flight validation des secrets avant execution | Nexus |
| 8 | Retrospective vide ≠ pas d'activite | Artifacts non collectes vs agents non lances | Verifier `gh run list` pour confirmer | Sage |
| 9 | Google Ads MCP `.type` dans conditions | Cause erreur cascade + annulation | JAMAIS utiliser `.type` dans les conditions GAQL | Nexus |
| 10 | Google Ads appels paralleles | Si 1 echoue, tous annules | TOUJOURS sequentiel, 1 requete a la fois | Nexus |
| 11 | `metrics.optimization_score` + date segments | Incompatible dans Google Ads API | Ne jamais combiner ces deux | Nexus |
| 12 | Metriques sur `ad_group_criterion` | Pas de metriques disponibles sur cette ressource | Utiliser `keyword_view` a la place | Nexus |
| 13 | Push rejete (remote ahead) | Un autre workflow a push entre-temps | `git pull --rebase origin main` avant push | Tous |
| 14 | MCP server timeout | npm install trop lent ou serveur crash | Ajouter retry, verifier version npm | Tous |
| 15 | Artifacts non uploades | Step upload skip si fichier absent | Verifier existence fichier avant upload step | Tous |

---

## Fiches detaillees par erreur

### Erreur #1 -- `startup_failure` workflow

> [!bug] Severite : CRITIQUE -- Le workflow ne demarre meme pas

**Symptome** : Le workflow apparait comme `startup_failure` dans GitHub Actions. Aucun step n'est execute.

**Cause racine** : Le YAML du workflow est invalide. La cause la plus frequente est un `default: ""` (chaine vide) sur un input de type `workflow_call`. GitHub Actions interprete la chaine vide comme une valeur absente et refuse de demarrer.

**Autre cause** : Indentation incorrecte, caractere special non echappe, ou syntaxe YAML invalide.

**Solution immediate** :
```bash
# Valider le YAML
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/{nom}.yml'))"
```

**Prevention long-terme** :
- Toujours utiliser `default: "none"` ou `default: "false"` -- jamais `default: ""`
- Valider le YAML avant chaque commit
- Utiliser l'editeur VS Code avec l'extension YAML pour la validation en temps reel

**References** : [[agents/creation-guide]] Etape 4, [[operations/runbooks]]

---

### Erreur #2 -- Agent ne trouve pas son prompt

> [!bug] Severite : CRITIQUE -- L'agent ne peut pas fonctionner sans prompt

**Symptome** : Le run echoue immediatement avec une erreur de fichier introuvable dans les logs Claude.

**Cause racine** : Le fichier `agent_prompts/<nom>.md` n'existe pas ou le nom ne correspond pas a la valeur de `inputs.agent_role` dans le workflow.

**Solution immediate** :
```bash
ls agent_prompts/
# Verifier que le fichier existe avec le bon nom
```

**Prevention long-terme** :
- Suivre la checklist de [[agents/creation-guide]] -- l'etape 2 cree le prompt AVANT l'etape 4 (workflow)
- Le workflow devrait inclure un step de verification :
```yaml
- name: Verify prompt exists
  run: |
    if [ ! -f "agent_prompts/${{ inputs.agent_role }}.md" ]; then
      echo "::error::Prompt file not found: agent_prompts/${{ inputs.agent_role }}.md"
      exit 1
    fi
```

---

### Erreur #3 -- Dashboard n'affiche pas les runs

> [!bug] Severite : MOYENNE -- Le dashboard est desynchronise mais les agents fonctionnent

**Symptome** : Le dashboard Netlify affiche des donnees obsoletes ou le run n'apparait pas.

**Cause racine** : Le step `generate_report.py` n'est pas execute (step conditionnel sans `if: always()`) ou les arguments `--output-dir` et `--dashboard-file` sont manquants.

**Solution immediate** :
```bash
# Regenerer manuellement
python3 .github/scripts/generate_report.py \
  --agent {nom} \
  --output-dir docs/reports \
  --dashboard-file docs/data/runs.json
```

**Prevention long-terme** :
- Le step report DOIT avoir `if: always()` pour s'executer meme si le run echoue
- Toujours passer les deux arguments obligatoires
- Verifier que le commit vault inclut `docs/data/runs.json`

---

### Erreur #4 -- Graph vide

> [!bug] Severite : MOYENNE -- Le graph Obsidian et dashboard ne montrent pas les connexions

**Symptome** : Le graph dans le dashboard (onglet Graph) est vide ou incomplet. Obsidian ne montre pas les liens.

**Cause racine** : `vault_builder.py` n'a pas ete lance apres une modification du vault. Le fichier `docs/data/graph.json` est obsolete.

**Solution immediate** :
```bash
python3 .github/scripts/vault_builder.py
git add docs/data/graph.json
git commit -m "vault: rebuild graph"
git push
```

**Prevention long-terme** :
- Ajouter un step `vault_builder.py` dans tout workflow qui modifie le vault
- Sage devrait verifier la coherence graph/vault lors de son run hebdomadaire

---

### Erreur #5 -- HTTP 401 Unauthorized

> [!bug] Severite : CRITIQUE -- Aucun agent ne peut fonctionner

**Symptome** : Tous les agents echouent avec `HTTP 401`. Le message mentionne un token invalide ou expire.

**Cause racine** : `CLAUDE_CODE_OAUTH_TOKEN` a expire. Ce token a une duree de vie limitee.

**Solution immediate** :
```bash
# 1. Regenerer le token
claude setup-token

# 2. Mettre a jour le secret GitHub
gh secret set CLAUDE_CODE_OAUTH_TOKEN
# (coller le nouveau token)
```

**Prevention long-terme** :
- Documenter la date d'expiration dans [[operations/secrets-matrix]]
- Configurer un rappel calendrier 1 semaine avant expiration
- Sentinel devrait verifier la validite du token lors de ses runs

---

### Erreur #6 -- PAT scope insuffisant

> [!bug] Severite : HAUTE -- Forge ne peut pas creer de branches ou de PRs

**Symptome** : Forge echoue avec `403 Forbidden` lors de la creation de branche ou de PR.

**Cause racine** : Le `PAT_TOKEN` n'a pas le scope `workflow`. Il faut `repo` + `workflow`.

**Solution immediate** :
```bash
# 1. Aller sur GitHub > Settings > Developer Settings > Personal Access Tokens
# 2. Editer le token
# 3. Cocher "workflow" en plus de "repo"
# 4. Mettre a jour
gh secret set PAT_TOKEN
```

**Prevention long-terme** :
- Documenter les scopes requis dans [[operations/secrets-matrix]]
- Lors de la creation d'un nouveau PAT, toujours cocher `repo` + `workflow`

---

### Erreur #7 -- Nexus silent failure

> [!bug] Severite : HAUTE -- Nexus produit un rapport template au lieu de donnees reelles

**Symptome** : Nexus termine avec `status: complete` mais le rapport contient des placeholders ou des donnees generiques.

**Cause racine** : Les credentials Google Ads ne sont pas configures. Nexus bascule en mode template sans signaler l'erreur.

**Solution immediate** :
- Verifier les secrets : `gh secret list | grep GOOGLE`
- Verifier que `GOOGLE_ADS_DEVELOPER_TOKEN`, `GOOGLE_ADS_CLIENT_ID`, `GOOGLE_ADS_CLIENT_SECRET`, `GOOGLE_ADS_REFRESH_TOKEN` sont tous configures

**Prevention long-terme** :
- Ajouter un step preflight dans le workflow Nexus :
```yaml
- name: Preflight check
  run: |
    if [ -z "$GOOGLE_ADS_DEVELOPER_TOKEN" ]; then
      echo "::error::Google Ads credentials missing"
      exit 1
    fi
```
- Pattern Preflight validation dans le prompt ([[agents/prompt-engineering]])

---

### Erreur #8 -- Retrospective vide ≠ pas d'activite

> [!bug] Severite : MOYENNE -- Sage tire de mauvaises conclusions

**Symptome** : Sage rapporte "0 retrospectives" alors que des agents ont tourne durant la semaine.

**Cause racine** : Les artifacts `agent_result.json` ne sont pas collectes correctement. Sage lit les fichiers mais ils sont absents ou vides. Cela ne signifie PAS que les agents n'ont pas tourne.

**Solution immediate** :
```bash
# Verifier les runs reels
gh run list --workflow="{agent}.yml" --limit=10
```

**Prevention long-terme** :
- Sage doit verifier `gh run list` en plus des retrospectives
- Les workflows doivent uploader `agent_result.json` comme artifact
- Distinguer "pas de retrospective" de "pas de run" dans le rapport Sage

---

### Erreurs #9-12 -- Google Ads MCP

> [!bug] Severite : CRITIQUE -- Ces erreurs causent des cascades d'annulation

Ces 4 erreurs sont specifiques au Google Ads MCP et sont documentees en detail dans les regles critiques du systeme.

#### #9 -- `.type` dans les conditions GAQL

```
INTERDIT:
  WHERE campaign.status = 'ENABLED' AND campaign.advertising_channel_type = 'SEARCH'

CORRECT:
  WHERE campaign.status = 'ENABLED'
  (filtrer .type cote client apres la requete)
```

**Pourquoi** : Le champ `.type` dans une condition GAQL provoque une erreur qui annule la requete ET toutes les requetes suivantes si elles sont en parallele.

#### #10 -- Appels paralleles

```
INTERDIT:
  Promise.all([query1(), query2(), query3()])

CORRECT:
  result1 = await query1()
  result2 = await query2()
  result3 = await query3()
```

**Pourquoi** : Si une requete echoue dans un batch parallele, toutes les autres sont annulees. Toujours sequentiel, 1 requete a la fois.

#### #11 -- `metrics.optimization_score` avec segments de date

```
INTERDIT:
  SELECT metrics.optimization_score, segments.date FROM campaign

CORRECT:
  SELECT metrics.optimization_score FROM campaign
  (sans aucun segment de date)
```

**Pourquoi** : `optimization_score` est incompatible avec les segments de date dans l'API Google Ads.

#### #12 -- Metriques sur `ad_group_criterion`

```
INTERDIT:
  SELECT metrics.clicks FROM ad_group_criterion

CORRECT:
  SELECT metrics.clicks FROM keyword_view
```

**Pourquoi** : `ad_group_criterion` ne supporte pas les metriques. Utiliser `keyword_view` a la place.

> [!warning] Ces 4 regles sont NON NEGOCIABLES. Nexus DOIT les respecter a chaque run. Voir aussi les regles dans `CLAUDE.md` et dans la memoire utilisateur.

---

### Erreur #13 -- Push rejete (remote ahead)

> [!bug] Severite : HAUTE -- Le commit vault est perdu

**Symptome** : Le step "Commit vault updates" echoue avec `error: failed to push some refs to 'origin'` ou `Updates were rejected because the remote contains work that you do not have locally`.

**Cause racine** : Un autre workflow (ou un autre agent) a pousse un commit entre le checkout et le push de cet agent.

**Solution immediate** :
```bash
git pull --rebase origin main
git push
```

**Prevention long-terme** :
- TOUJOURS inclure `git pull --rebase origin main` avant `git push` dans le step commit
- Pattern recommande :
```yaml
- name: Commit vault updates
  if: always()
  run: |
    git config user.name "github-actions[bot]"
    git config user.email "github-actions[bot]@users.noreply.github.com"
    git add docs/vault/ docs/reports/ docs/data/
    git diff --cached --quiet || git commit -m "vault: update {nom} memory"
    git pull --rebase origin main || true
    git push || echo "::warning::Push failed, vault update will be retried"
```

---

### Erreur #14 -- MCP server timeout

> [!bug] Severite : MOYENNE -- L'agent perd du temps et des tokens

**Symptome** : Le run est lent et les logs montrent des timeouts de connexion MCP. Souvent `npm install` prend trop longtemps ou le serveur MCP crash silencieusement.

**Cause racine** : Installation npm lente (reseau GitHub Actions), version npm incompatible, ou serveur MCP instable.

**Solution immediate** :
- Relancer le run (souvent transitoire)
- Verifier les versions npm dans `.mcp.json`

**Prevention long-terme** :
- Utiliser des versions fixes (`@modelcontextprotocol/server-github@0.6.0`) au lieu de `latest`
- Ajouter un timeout sur le step MCP setup
- Preferer les skills valides aux MCPs quand possible ([[tech/skills-registry]])

---

### Erreur #15 -- Artifacts non uploades

> [!bug] Severite : MOYENNE -- Le chaining echoue car l'agent suivant n'a pas les fichiers

**Symptome** : Le run est `complete` mais les artifacts listes dans `agent_result.json` n'existent pas dans les artifacts GitHub.

**Cause racine** : Le step `actions/upload-artifact` est skip si le fichier n'existe pas (pas d'erreur, juste un skip silencieux).

**Solution immediate** :
- Verifier les logs du step upload
- Verifier que les fichiers existent avant l'upload

**Prevention long-terme** :
```yaml
- name: Upload artifacts
  if: always()
  run: |
    for f in /tmp/agent_result.json /tmp/enriched_leads.csv; do
      if [ -f "$f" ]; then
        echo "Found: $f"
      else
        echo "::warning::Artifact missing: $f"
      fi
    done

- uses: actions/upload-artifact@v4
  if: always()
  with:
    name: agent-results
    path: |
      /tmp/agent_result.json
      /tmp/*.csv
    if-no-files-found: warn
```

---

## Regles d'or

> [!success] 4 regles absolues pour la gestion des erreurs

### Regle 1 : Lire avant d'agir

```
Au debut de chaque tache complexe :
1. Lire memory/lessons_learned.md
2. Lire docs/vault/agents/error-patterns.md (ce fichier)
3. Verifier si l'erreur est deja documentee
4. Appliquer la prevention AVANT de rencontrer l'erreur
```

### Regle 2 : Ne jamais refaire une erreur documentee

```
Si une erreur documentee ici se reproduit :
→ C'est un echec du processus, pas de l'agent
→ Le prompt doit etre ameliore pour inclure la prevention
→ Sage doit creer une PR de correction
```

### Regle 3 : Toujours documenter les nouvelles erreurs

```
Quand une nouvelle erreur est rencontree :
1. Ajouter une entree dans ce fichier (tableau + fiche detaillee)
2. Ajouter dans memory/lessons_learned.md
3. Mettre a jour la memoire agent concernee
4. Si applicable, mettre a jour le prompt pour prevenir la recurrence
```

### Regle 4 : Escalade automatique

```
Si une erreur se repete 3 fois en 2 semaines :
→ Sage cree automatiquement une issue GitHub avec :
  - Label: "recurring-error"
  - Description: erreur, frequence, agents impactes
  - Proposition de correction
→ L'issue est assignee pour resolution humaine
```

---

## Metriques d'erreurs

| Metrique | Seuil acceptable | Seuil critique | Source |
|----------|-----------------|----------------|--------|
| Taux d'erreur global | < 10% | > 25% | `docs/data/runs.json` |
| Erreurs recurrentes (meme erreur 3x) | 0 | > 0 | Ce fichier + issues |
| Temps moyen de resolution | < 1 run | > 3 runs | Historique runs |
| Erreurs non documentees | 0 | > 2 | Retrospectives |

Ces metriques sont suivies dans [[operations/kpis]] et analysees par Sage chaque semaine.

---

## Fichiers lies

- [[agents/creation-guide]] -- Guide de creation (prevention par design)
- [[agents/prompt-engineering]] -- Amelioration des prompts (prevention par prompt)
- [[agents/communication-protocol]] -- Format des resultats (status, retry)
- [[agents/sage-memory]] -- Sage analyse les erreurs chaque semaine
- [[agents/sentinel-memory]] -- Sentinel detecte les regressions
- [[operations/runbooks]] -- Procedures de resolution
- [[operations/kpis]] -- Metriques de suivi
- [[operations/secrets-matrix]] -- Status des secrets (erreurs #5, #6, #7)
- [[tech/mcp-servers]] -- Configuration MCP (erreur #14)

---

*Derniere mise a jour : 2026-03-28 -- Maintenu par [[agents/sage-memory|Sage]] et [[agents/sentinel-memory|Sentinel]]*

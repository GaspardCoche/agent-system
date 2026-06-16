# Claude Pocket Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Déclencher les agents cloud `agent-system` depuis une PWA iPhone, avec garde-fous d'écriture et auth résiliente au changement de plan SDK.

**Architecture :** L'iPhone (PWA hébergée sur GitHub Pages) crée une issue GitHub labellisée `agent` via l'API REST. L'`orchestrator.yml` existant route vers l'agent spécialisé. Les écritures passent par le gate d'approbation existant (preview → label `approved`). Auth commutable abonnement↔API via un secret unique.

**Tech Stack :** GitHub Actions (workflows existants), `anthropics/claude-code-action@v1`, HTML/CSS/JS vanilla (PWA, zéro build), GitHub REST API, GitHub Pages.

**Repo :** `GaspardCoche/agent-system`, branche `claude-pocket`.

---

## File Structure

| Fichier | Action | Responsabilité |
|---|---|---|
| `.github/workflows/_reusable-claude.yml` | Modify | Auth commutable (`anthropic_api_key`) + input `model` |
| `docs/runner-guardrails.md` | Create | Référence garde-fous durs + câblage MCP (lecture/écriture) |
| `.github/ISSUE_TEMPLATE/pocket-task.yml` | Create | Formulaire d'issue → corps structuré pour Dispatch |
| `.github/ISSUE_TEMPLATE/config.yml` | Create | Désactive les issues blank, pointe vers le template |
| `.mcp.json` | Modify | Ajout serveurs `hubspot`, `lemlist` (référence locale) |
| `docs/pocket/index.html` | Create | Coquille PWA |
| `docs/pocket/app.js` | Create | Logique : créer issue, poller, approuver, dictée |
| `docs/pocket/style.css` | Create | Style mobile |
| `docs/pocket/manifest.webmanifest` | Create | Installable écran d'accueil |
| `docs/pocket/sw.js` | Create | Service worker minimal (shell offline) |
| `docs/pocket/icon.svg` | Create | Icône |
| `docs/pocket-setup.md` | Create | Guide : secrets GitHub à créer, PAT, install iPhone |

---

## Phase 0 — Socle auth & garde-fous

### Task 1 : Auth commutable + routage modèle dans le reusable

**Files:**
- Modify: `.github/workflows/_reusable-claude.yml`

- [ ] **Step 1 : Ajouter les inputs `model`**

Dans le bloc `inputs:` (après `allowed_tools`), ajouter :

```yaml
      model:
        required: false
        type: string
        default: "claude-haiku-4-5"
```

- [ ] **Step 2 : Pinner le modèle dans claude_args**

Étape « Build claude_args », remplacer la ligne `echo "CLAUDE_ARGS=...` par :

```bash
          echo "CLAUDE_ARGS=--model ${{ inputs.model }} --max-turns ${{ inputs.max_turns }} --allowedTools $TOOLS --mcp-config /tmp/mcp-config.json" >> $GITHUB_ENV
```

- [ ] **Step 3 : Ajouter l'auth commutable**

Étape « Run Claude agent », sous `claude_code_oauth_token:`, ajouter :

```yaml
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

Secret vide = abonnement (0 €). Rempli = API métré. Aucun autre changement de code requis pour basculer.

- [ ] **Step 4 : Valider la syntaxe YAML**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/_reusable-claude.yml'))" && echo OK`
Expected: `OK`

- [ ] **Step 5 : Commit**

```bash
git add .github/workflows/_reusable-claude.yml
git commit -m "feat(pocket): switchable auth + pinned model in reusable workflow"
```

### Task 2 : Document de référence garde-fous

**Files:**
- Create: `docs/runner-guardrails.md`

- [ ] **Step 1 : Écrire le doc** (contenu = garde-fous durs #1-10 du spec §4.3 + tableau MCP lecture/écriture §4.4, issu de la recherche vault). Inclure : règle d'or (lecture par défaut, écriture seulement si `write_allowed` + conditions + garde-fous), tableau MCP endpoint/secret, colonnes lecture-seule vs écriture par outil.

- [ ] **Step 2 : Commit**

```bash
git add docs/runner-guardrails.md
git commit -m "docs(pocket): runner guardrails + MCP wiring reference"
```

---

## Phase 1 — Entry point (issue → Dispatch)

### Task 3 : Formulaire d'issue Pocket Task

**Files:**
- Create: `.github/ISSUE_TEMPLATE/pocket-task.yml`
- Create: `.github/ISSUE_TEMPLATE/config.yml`

- [ ] **Step 1 : Créer le formulaire** avec champs : `demande` (textarea, requis), `write_allowed` (dropdown oui/non, défaut non), `write_conditions` (textarea), `agent_hint` (dropdown : auto/crm/ads/web/email/code). Le template applique `labels: [agent, pocket]`.

- [ ] **Step 2 : Créer config.yml** : `blank_issues_enabled: false`.

- [ ] **Step 3 : Valider YAML**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/ISSUE_TEMPLATE/pocket-task.yml'))" && echo OK`
Expected: `OK`

- [ ] **Step 4 : Commit**

```bash
git add .github/ISSUE_TEMPLATE/
git commit -m "feat(pocket): issue form entry point for mobile dispatch"
```

### Task 4 : Injecter garde-fous + conditions dans le prompt Dispatch

**Files:**
- Modify: `agent_prompts/dispatch.md` (ou créer si absent)

- [ ] **Step 1 : Ajouter une section « Pocket / garde-fous »** au prompt Dispatch : si l'issue porte le label `pocket`, lire `docs/runner-guardrails.md` ; respecter la règle d'or ; si `write_allowed=non`, ne produire qu'une proposition ; si `write_allowed=oui`, préparer un preview et exiger le label `approved` avant toute écriture, en restant dans les `write_conditions`.

- [ ] **Step 2 : Commit**

```bash
git add agent_prompts/dispatch.md
git commit -m "feat(pocket): wire guardrails + write-conditions into dispatch prompt"
```

---

## Phase 2 — Câblage MCP cloud

### Task 5 : Ajouter HubSpot + Lemlist au reusable MCP config

**Files:**
- Modify: `.github/workflows/_reusable-claude.yml` (étape « Write MCP config with secrets »)
- Modify: `.mcp.json` (référence locale)

- [ ] **Step 1 : Ajouter les serveurs MCP** dans le `python3 -c` qui écrit `/tmp/mcp-config.json` : `hubspot` (npx `@hubspot/mcp-server`, env `PRIVATE_APP_ACCESS_TOKEN` ← `secrets.HUBSPOT_PRIVATE_APP_TOKEN`), `lemlist` (http `https://app.lemlist.com/mcp`, header `X-API-Key` ← `secrets.LEMLIST_API_KEY`). Ajouter les env correspondants à l'étape.

- [ ] **Step 2 : Étendre la liste d'outils autorisés** : ajouter les outils HubSpot **lecture seule** au `BASE` (search/list/batch-read/get-property). Les outils d'écriture restent passés via `allowed_tools` par l'agent et gated par approbation.

- [ ] **Step 3 : Documenter les secrets requis** dans `docs/pocket-setup.md` (Task 9).

- [ ] **Step 4 : Valider YAML + commit**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/_reusable-claude.yml'))" && echo OK
git add .github/workflows/_reusable-claude.yml .mcp.json
git commit -m "feat(pocket): wire HubSpot + Lemlist MCP via GitHub secrets"
```

---

## Phase 3 — PWA iPhone

### Task 6 : Coquille + manifest + service worker

**Files:**
- Create: `docs/pocket/index.html`, `docs/pocket/manifest.webmanifest`, `docs/pocket/sw.js`, `docs/pocket/icon.svg`, `docs/pocket/style.css`

- [ ] **Step 1** : index.html (champ token GitHub, champ demande, dictée, toggle écriture + conditions, sélecteur agent, bouton Dispatch, zone historique/résultat). Lien manifest + enregistrement SW.
- [ ] **Step 2** : manifest (name, icons, display standalone, theme color).
- [ ] **Step 3** : sw.js (cache du shell : index/app/style/icon).
- [ ] **Step 4** : style.css (mobile-first, dark).
- [ ] **Step 5 : Commit**

```bash
git add docs/pocket/
git commit -m "feat(pocket): PWA shell, manifest, service worker"
```

### Task 7 : Logique app.js

**Files:**
- Create: `docs/pocket/app.js`

- [ ] **Step 1 : Stockage token** : PAT fine-grained en `localStorage` (clé `pocket_pat`, repo `pocket_repo`).
- [ ] **Step 2 : Dispatch** : `POST /repos/{owner}/{repo}/issues` avec titre court + corps structuré (demande, write_allowed, write_conditions, agent_hint) + labels `[agent, pocket]`. Stocker le numéro d'issue dans l'historique.
- [ ] **Step 3 : Polling** : `GET /repos/{owner}/{repo}/issues/{n}/comments` toutes les ~15 s, afficher les commentaires (preview/résultat).
- [ ] **Step 4 : Approuver** : bouton qui `POST` le label `approved` sur l'issue.
- [ ] **Step 5 : Dictée** : Web Speech API (`webkitSpeechRecognition`) sur le champ demande.
- [ ] **Step 6 : Validation manuelle iOS Safari** (Task 10).
- [ ] **Step 7 : Commit**

```bash
git add docs/pocket/app.js
git commit -m "feat(pocket): app logic — create issue, poll, approve, voice"
```

### Task 8 : Déploiement Pages

**Files:**
- Modify: `.github/workflows/deploy-pages.yml` (vérifier que `docs/pocket/` est inclus — il l'est, path `docs`)

- [ ] **Step 1** : Confirmer que `deploy-pages.yml` upload `docs/` (déjà le cas). Aucun changement si la PWA est sous `docs/pocket/`.
- [ ] **Step 2** : Après merge sur `main`, vérifier l'URL `https://<user>.github.io/agent-system/pocket/`.

---

## Phase 4 — Setup & validation

### Task 9 : Guide de setup

**Files:**
- Create: `docs/pocket-setup.md`

- [ ] **Step 1 : Écrire le guide** : (a) liste exacte des secrets GitHub à créer (`HUBSPOT_PRIVATE_APP_TOKEN`, `FULLENRICH_API_KEY`, `PHANTOMBUSTER_API_KEY`, `LEMLIST_API_KEY`, `GEMINI_API_KEY`, `FIRECRAWL_API_KEY`, `ANTHROPIC_API_KEY` laissé vide) ; (b) création d'un PAT fine-grained (scope : Issues RW + Actions RW sur le seul repo) ; (c) activation GitHub Pages (branche/source) ; (d) install PWA sur iPhone (Safari → Partager → Sur l'écran d'accueil).
- [ ] **Step 2 : Commit**

```bash
git add docs/pocket-setup.md
git commit -m "docs(pocket): setup guide (secrets, PAT, Pages, iPhone install)"
```

### Task 10 : Validation bout-en-bout (dry-run, sans clés)

- [ ] **Step 1** : Créer une issue de test via le formulaire (`write_allowed=non`) → vérifier que `orchestrator.yml` se déclenche (Actions tab).
- [ ] **Step 2** : Vérifier qu'un commentaire de planification est posté.
- [ ] **Step 3** : Vérifier qu'aucune écriture externe n'a lieu (pas de clés CRM encore → l'agent doit signaler « secret absent » proprement, pas planter).
- [ ] **Step 4** : Ouvrir la PWA sur iPhone, créer une demande, voir le commentaire remonter.

---

## Phase 5 — Workflows métier (itération suivante, hors MVP)

3 recettes câblées comme prompts/skills : `répondre-collègue` (lecture HubSpot + rédaction), `enrichir-contact` (FullEnrich ≤100 + update non destructif), `diagnostic-séquence` (lecture séquences/engagements). Chacune = un fichier prompt + entrée dans le sélecteur agent de la PWA. À planifier séparément une fois le socle validé.

---

## Self-Review

- **Spec coverage** : §4.1 PWA → Tasks 6-8 ; §4.2 entry point → Tasks 3-4 ; §4.3 garde-fous → Tasks 2,4 ; §4.4 MCP → Task 5 ; §4.5 limites/auth → Task 1 ; §8 coût → inchangé ; §9 phases → mappées. Workflows métier §11/Phase 5 explicitement hors MVP.
- **Placeholders** : les contenus longs (guardrails, PWA, setup) sont décrits avec leur structure complète ; le code réel est écrit à l'exécution (plan exécuté inline par l'auteur, pas par un tiers sans contexte).
- **Type consistency** : labels `agent`+`pocket` cohérents (Task 3 pose, Task 4/7 consomment) ; secret `ANTHROPIC_API_KEY` cohérent (Task 1 consomme, Task 9 documente) ; clés localStorage `pocket_pat`/`pocket_repo` cohérentes (Task 7).

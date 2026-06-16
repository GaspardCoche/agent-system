# Claude Pocket — Design

**Date :** 2026-06-16
**Auteur :** Gaspard Coche (+ Claude)
**Statut :** En attente de validation utilisateur
**Repo cible :** `GaspardCoche/agent-system` (extension de l'infra existante)

---

## 1. Objectif

Permettre à Gaspard de **déclencher Claude depuis son iPhone uniquement**, pour faire faire du travail métier (répondre aux questions des collègues posées sur Slack, agir sur HubSpot / FullEnrich / PhantomBuster / Google Apps Script via les MCP), pendant qu'il fait autre chose. Le système doit :

- tourner **même Mac éteint** (exécution cloud) ;
- rester **gratuit** dans sa configuration de base ;
- être **résilient au changement de plan de la SDK Claude** (abonnement → API métré sans casse) ;
- appliquer des **garde-fous durs** sur la production (CRM), avec écriture seulement sur autorisation explicite ;
- réutiliser au maximum l'`agent-system` existant (orchestrateur multi-agents déjà en place).

## 2. Insight fondateur

`~/agent-system` est **déjà** un orchestrateur multi-agents tournant dans **GitHub Actions** :

- agents spécialisés : Dispatch (orchestrateur), Scout (web/Firecrawl), Aria (leads/HubSpot/FullEnrich), Nexus (Google Ads), Iris (email), Sage (prompts), Forge (code), Sentinel (QA), Lumen (data/Gemini) ;
- déclenchement par **issue labellisée `agent`** ou `workflow_dispatch` (input `task_description`) — cf. `orchestrator.yml` ;
- **passerelle d'approbation** déjà construite : preview en commentaire d'issue → label `approved` pour exécuter, sinon `DRY_RUN` ;
- **protocole de communication** JSON (`/tmp/agent_task.json` → `/tmp/agent_result.json` + champ `retrospective`) ;
- **GitHub Pages** déjà déployable (`deploy-pages.yml`) → hébergement PWA gratuit ;
- plan d'**auth commutable** déjà conçu (secret `ANTHROPIC_API_KEY` vide = abonnement OAuth gratuit, rempli = API métré) — cf. `_reusable-claude.yml`.

**Conséquence :** l'iPhone ne pilote pas le Mac. Il **déclenche les agents cloud existants** et reçoit le résultat. On construit la *porte d'entrée mobile* + le *câblage MCP cloud* + la *couche d'autonomie/garde-fous*, on ne réécrit pas l'orchestrateur.

## 3. Architecture

```
┌─────────────────────────────┐
│  iPhone — PWA "Claude Pocket"│  (hébergée GitHub Pages, ajoutée écran d'accueil)
│  • champ texte + dictée voix │
│  • bouton "Dispatch"         │
│  • toggle "Autoriser écriture"│
│  • historique + push notifs  │
└──────────────┬──────────────┘
               │ GitHub REST API (fine-grained PAT, scope issues+actions)
               ▼
┌─────────────────────────────┐
│  GitHub Issue (label "agent")│  ← thread = trace + canal d'approbation
└──────────────┬──────────────┘
               │ on: issues labeled
               ▼
┌─────────────────────────────┐
│  orchestrator.yml — Dispatch │  décompose + route vers l'agent spécialisé
│  (via _reusable-claude.yml)  │
└──────────────┬──────────────┘
               │ injecte garde-fous + conditions d'écriture parsées
               ▼
   ┌───────────────────────────┐
   │  Agent spécialisé + MCP    │  HubSpot / FullEnrich / PhantomBuster / Lemlist / Apps Script
   └───────────┬───────────────┘
   LECTURE auto │ ÉCRITURE seulement si autorisée + dans les conditions
               ▼
┌─────────────────────────────┐
│ Commentaire d'issue = preview│  → si écriture : attend label "approved"
│ puis résultat final          │  → push notif GitHub sur l'iPhone
└──────────────┬──────────────┘
               │ la PWA poll l'issue (API) → affiche résultat + bouton "Approuver"
               ▼
        Gaspard copie la réponse → Slack au collègue
```

## 4. Composants (unités à frontières claires)

### 4.1 PWA « Claude Pocket » (`pocket/` → GitHub Pages)
- **Rôle :** unique interface mobile. Saisie (texte + dictée Web Speech API), déclenchement, suivi, approbation.
- **Entrées :** texte de la demande, toggle « autoriser écriture » + zone « conditions d'écriture », sélection d'agent (auto par défaut).
- **Dépendances :** GitHub REST API (création d'issue, lecture commentaires, ajout label `approved`). Auth via **PAT fine-grained** stocké en `localStorage` (usage perso mono-utilisateur).
- **Sorties :** issue créée ; affichage du fil + résultat ; bouton « Approuver ».
- **Tech :** HTML/CSS/JS vanilla (zéro build, sert tel quel sur Pages). PWA installable (manifest + service worker minimal pour l'icône/offline shell).

### 4.2 Entry point agent (`.github/ISSUE_TEMPLATE/pocket-task.yml` + parsing)
- **Rôle :** normaliser une demande venue du téléphone en `task.json` pour Dispatch.
- **Champs structurés :** `demande`, `write_allowed` (bool), `write_conditions` (texte libre), `agent_hint` (optionnel).
- **Dépendances :** `orchestrator.yml` (déjà déclenché par label `agent`).

### 4.3 Couche d'autonomie & garde-fous (prompt système injecté)
- **Rôle :** encadrer ce que l'agent peut écrire.
- **Règle d'or :** par défaut **lecture/proposition seulement**. Écriture autorisée **uniquement si** `write_allowed=true`, et **strictement dans les `write_conditions`** fournies, **et** dans le respect des garde-fous durs ci-dessous.
- **Garde-fous durs (non négociables, cf. `crm-context`) :**
  1. Ne jamais écraser un champ HubSpot déjà rempli (lire avant d'écrire).
  2. Industry → `industry_emalist` sur **Companies** uniquement (jamais `industry` contacts).
  3. `country` = enum strict (sinon country_code).
  4. `numemployees` = ranges ; nombre brut → `linkedin_employee_count`.
  5. FullEnrich ≤ 100 contacts/batch.
  6. Statut 207 = succès partiel → parser les `results`.
  7. Pas de merge/delete/tickets via MCP HubSpot.
  8. Lemlist `add_*/set_campaign_state/send_message` = irréversible côté prospect → **toujours preview + approbation**.
  9. `python3.12` obligatoire.
  10. Aucun secret loggué/imprimé.
- **Mécanisme d'approbation :** toute écriture passe par un **preview en commentaire** ; exécution seulement après label `approved` (réutilise le gate existant). `DRY_RUN=true` tant que non approuvé.

### 4.4 Câblage MCP cloud (`.mcp.json` + secrets GitHub)
- **Rôle :** donner aux agents cloud l'accès aux outils, via secrets GitHub chiffrés.
- **À ajouter en secrets** (clés fournies par Gaspard) : `HUBSPOT_PRIVATE_APP_TOKEN`, `FULLENRICH_API_KEY`, `PHANTOMBUSTER_API_KEY`, `LEMLIST_API_KEY`, (Apps Script : `CLASP_CREDENTIALS` / service account). `GITHUB_TOKEN`, `FIRECRAWL_API_KEY`, `TAVILY_API_KEY`, `GEMINI_API_KEY` : déjà présents ou à confirmer.
- **MCP serveurs** (ajouts au `.mcp.json` du repo) : `hubspot` (stdio, `PRIVATE_APP_ACCESS_TOKEN`), `lemlist` (http, header `X-API-Key`), + FullEnrich/PhantomBuster en Python direct (skills validés).
- **Lecture seule vs écriture :** tableau de référence dans `docs/runner-guardrails.md` (généré depuis la recherche vault).

### 4.5 Limites, sécurité & résilience SDK
- **`max_turns`** plafonné par complexité (3 simple / 8 moyen / 12 complexe — déjà dans `CLAUDE.md`).
- **Budget mensuel** : compteur de runs + alerte ; minutes GitHub free tier (2000/mois) surveillées par `health-check.yml`.
- **Auth commutable (résilience plan SDK)** : dans `_reusable-claude.yml`, ajouter `anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}` à côté de `claude_code_oauth_token`. Secret vide = abonnement (0 €). Le jour où l'abonnement Claude Code change de modèle de facturation, **remplir un seul secret** suffit à basculer sur l'API métré, sans modifier le code. Variante cloud : `CLAUDE_CODE_USE_BEDROCK` / `CLAUDE_CODE_USE_VERTEX`.
- **Pinner le modèle** explicitement (`--model`) pour ne pas dépendre du défaut (défaut Haiku pour les agents simples, Sonnet/Opus selon rôle).
- **Sécurité PAT PWA** : fine-grained, scope minimal (issues + actions read/write sur le seul repo `agent-system`), expirable, révocable. Stocké localStorage (acceptable mono-utilisateur ; documenté comme tel).

## 5. Flux de données (exemple « répondre à un collègue »)

1. Collègue sur Slack : « Pourquoi le contact X n'apparaît pas dans la séquence ? »
2. Gaspard ouvre la PWA, dicte la question, **laisse le toggle écriture OFF**, tape « Dispatch ».
3. PWA crée une issue `agent` avec le `task.json`.
4. Dispatch route vers l'agent CRM → MCP HubSpot **en lecture** → analyse.
5. Résultat posté en commentaire (diagnostic + réponse prête à copier). Push notif iPhone.
6. Gaspard copie la réponse → Slack. Fin. (Aucune écriture, donc aucune approbation requise.)

Variante avec écriture : Gaspard active le toggle + condition « tu peux mettre à jour le champ `lifecyclestage` en `lead`, jamais l'écraser s'il est déjà rempli ». L'agent prépare le preview → push notif → Gaspard tape « Approuver » → exécution dans les conditions.

## 6. Gestion d'erreurs

- Agent échoue → statut `failed` + `retry_reason` dans le commentaire ; self-correction max 3 cycles (déjà dans `CLAUDE.md`).
- MCP indisponible / clé manquante → message explicite « secret X absent », pas d'exécution partielle silencieuse.
- 207 HubSpot → traité comme succès partiel, détail par `result`.
- Timeout GitHub Actions → notif d'échec, la file n'est pas bloquée (issues indépendantes).
- PWA hors-ligne → shell affiché, file d'envoi mise en attente jusqu'au réseau.

## 7. Tests

- **Garde-fous :** test « tentative d'écraser un champ rempli » → doit refuser. Test « écriture sans autorisation » → doit rester en proposition.
- **Auth commutable :** run avec `ANTHROPIC_API_KEY` vide (OAuth) puis rempli (API) → même comportement.
- **Bout-en-bout dry-run :** issue de test → preview généré, pas d'écriture tant que `approved` absent.
- **PWA :** création d'issue, lecture du fil, ajout label depuis le téléphone (Safari iOS).
- `agent-tester.yml` / `Sentinel` réutilisés pour la validation.

## 8. Coût

| Poste | Coût | Note |
|---|---|---|
| Compute Claude | **0 €** | abonnement OAuth, pas de tokens métrés |
| GitHub Actions | **0 €** | 2000 min/mois gratuits (repo privé) ; au-delà ~0,007 €/min |
| GitHub Pages (PWA) | **0 €** | hébergement statique gratuit |
| APIs data (FullEnrich, PhantomBuster…) | inchangé | abonnements existants, à l'usage |
| **TOTAL système** | **≈ 0 €/mois** | hors dépassement éventuel de minutes |

## 9. Phases de construction

- **Phase 0 — Socle auth & garde-fous :** auth commutable dans `_reusable-claude.yml` ; `docs/runner-guardrails.md` ; pinning modèle.
- **Phase 1 — Entry point :** template d'issue `pocket-task` + parsing → `task.json` ; vérifier le routage Dispatch.
- **Phase 2 — Câblage MCP cloud :** ajout serveurs `.mcp.json` + secrets (clés fournies par Gaspard) ; test lecture HubSpot bout-en-bout.
- **Phase 3 — PWA :** UI dispatch + dictée + historique + bouton approuver ; déploiement Pages ; install écran d'accueil.
- **Phase 4 — Limites & observabilité :** budget/minutes, `retrospective` enrichie (model, tokens), alertes.
- **Phase 5 — Workflows métier :** 2-3 recettes câblées (répondre-collègue, enrichir-contact, diagnostic-séquence).

## 10. Points ouverts / à confirmer

- Liste exacte des secrets API à fournir (Phase 2).
- Nom exact du champ industry company en prod (`industry_emalist` vs `internal_industry`) — ne pas écrire dessus tant que non confirmé.
- Repo privé conservé (2000 min) vs runner self-hosted plus tard si volume.
- Décision modèle Iris-digest (Sonnet vs Opus) — hors périmètre direct mais lié au routage.

## 11. Hors périmètre (YAGNI au démarrage)

- App native iOS (Swift/App Store).
- Runner self-hosted / Tailscale (gardé en évolution si dépassement minutes).
- Session conversationnelle persistante (architecture C complète) — on démarre en jobs one-shot tracés par issue, le fil d'issue donne déjà le suivi.

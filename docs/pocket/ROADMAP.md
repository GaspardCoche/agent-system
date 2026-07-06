# Claude Pocket — Roadmap d'amélioration

> Document de planification (2026-07-06). Objectif : cadrer tout ce qui pourrait
> être ajouté pour rapprocher l'app de sa vision, priorisé pour implémentation
> ultérieure. Rien ici n'est encore implémenté sauf mention « ✅ fait ».

## 🎯 Vision (north star)

**Piloter tous les systèmes de Gaspard depuis le téléphone, en langage naturel,
avec confiance.** L'iPhone est la télécommande ; GitHub Actions est le cerveau
cloud (Mac éteint OK) ; l'agent Claude comprend l'intention, choisit le bon
système et agit — lecture par défaut, écriture gatée.

Trois axes de progrès : **(1) Confiance** (savoir que ça marche), **(2) Couverture**
(tous les systèmes, pas juste HubSpot/web), **(3) Fluidité** (l'usage doit être
plus rapide que d'ouvrir un laptop).

## 📍 État actuel (juillet 2026)

**Systèmes câblés :** HubSpot (CRM), FullEnrich, PhantomBuster, Lemlist (lecture),
Tavily + Firecrawl (web), Vault Obsidian (lecture), Google Sheets, GitHub.
**Front :** dashboard, composer (voix + fichiers + modes), historique multi-source,
chat itératif, modes agentiques CRUD + planifiés, base de connaissances, monitoring.
**Fiabilité :** ✅ échecs d'agent désormais surfacés (PR #141), token OAuth renouvelé.

**Manques structurels identifiés :** pas de vue « santé des systèmes » ; couverture
limitée aux systèmes growth (ni Ads, ni Gmail, ni Calendar, ni écriture vault) ;
pas de suivi de coût réel ; alerte proactive d'expiration de token absente.

---

## 🗂️ Catalogue des améliorations (par thème)

Notation effort : **S** (≤½ j) · **M** (1-2 j) · **L** (>2 j). Impact : ⭐→⭐⭐⭐.

### A. Confiance & fiabilité (fondation)

| # | Amélioration | Impact | Effort | Notes |
|---|---|---|---|---|
| A1 | **Panneau « Santé des systèmes »** dans l'app : statut vert/rouge par intégration (token Claude, HubSpot, Lemlist, secrets…), âge du token, dernier run OK par système. Lit un `pocket-data/status.json` écrit à chaque run + un check périodique. | ⭐⭐⭐ | M | Réutilise `pocket-smoke.yml`. C'est la réponse directe à « l'app semblait morte sans le dire ». |
| A2 | **Alerte proactive d'expiration de token** : cron hebdo qui lance un run trivial ; si `is_error`/coût 0 → notif push « ⚠️ auth à renouveler ». | ⭐⭐⭐ | S | Empêche la panne vécue de se reproduire en silence. S'appuie sur `pocket_check_result.py` (✅ déjà là). |
| A3 | **Bouton « Relancer » sur une tâche échouée** (1 tap → nouveau commentaire déclencheur). | ⭐⭐ | S | Aujourd'hui il faut re-commenter à la main. |
| A4 | **Taxonomie d'erreurs** : le commentaire de repli détecte le type (secret manquant / rate limit / erreur outil / auth) et donne le remède ciblé. | ⭐⭐ | M | Étend le fallback de la PR #141. |
| A5 | **Fiabiliser `pocket-schedule.yml`** (même correctif anti-échec-silencieux que pocket.yml). | ⭐⭐ | S | Les modes programmés échoueraient sinon en silence. |

### B. Couverture des systèmes (la vision « tout piloter »)

| # | Amélioration | Impact | Effort | Notes |
|---|---|---|---|---|
| B1 | **Google Ads** — `pocket_ads.py` : lecture (spend, perf campagnes) + actions gatées (pause/budget). « Mets en pause la campagne X ». | ⭐⭐⭐ | M | Auth déjà en Keychain (`google-ads-*`), logique Nexus existante à réutiliser. Fort ROI métier. |
| B2 | **Gmail** — lire/triager la boîte, **rédiger un draft** de réponse depuis le téléphone. « Réponds à ce mail ». | ⭐⭐⭐ | M | `GMAIL_TOKEN_JSON` déjà en secret (agent Iris). Écriture = draft only, jamais d'envoi auto. |
| B3 | **Écriture Vault** — capturer une note dans le vault Obsidian depuis le tel (aujourd'hui lecture seule). « Note dans le vault : … ». | ⭐⭐ | M | La deploy key est read-only → besoin d'un PAT écriture sur le repo vault + garde-fous. |
| B4 | **Google Calendar** — voir l'agenda du jour, créer un événement. | ⭐⭐ | M | Nécessite creds Calendar en CI (OAuth séparé de Gmail). |
| B5 | **Lemlist écriture** — ajouter un lead à une campagne / pause séquence (gaté `approved`). + ajouter `LEMLIST_API_KEY` (manquant). | ⭐⭐ | S | Débloque le pilier outreach (aujourd'hui muet côté secret). |
| B6 | **Notion / Slack** — si usage récurrent (audit Charleroi = Notion ; « répondre aux collègues » = Slack, vision initiale). | ⭐⭐ | M | À câbler seulement si besoin réel confirmé. |
| B7 | **Google Analytics** — lecture trafic/conversions rapide. | ⭐ | M | Nice-to-have, complète le tableau growth. |

### C. Fluidité & UX

| # | Amélioration | Impact | Effort | Notes |
|---|---|---|---|---|
| C1 | **Sortie en quasi-temps-réel** dans le détail (streaming des étapes de l'agent au lieu du polling des commentaires). | ⭐⭐ | M | Sensation « Claude en direct ». |
| C2 | **Bibliothèque de prompts paramétrés** (au-delà des 3 chips) : « enrichir liste ___ », « stats campagne ___ » avec champs à remplir. | ⭐⭐ | M | Accélère les tâches récurrentes. |
| C3 | **Rendu riche des résultats** : CSV → tableau triable + aperçu ; distributions (lifecyclestage…) → mini bar-chart ; images inline. | ⭐⭐ | M | Markdown déjà là ; ajoute tables/charts. |
| C4 | **iOS Shortcuts / Siri** : « Dis à Pocket de … » lance une tâche à la voix sans ouvrir l'app. | ⭐⭐ | M | Raccourci → API GitHub. Très « télécommande ». |
| C5 | **Preview d'écriture structurée** avant approbation (diff clair de ce qui va changer dans HubSpot/…) au lieu d'un texte libre. | ⭐⭐ | M | Renforce la confiance sur les écritures. |
| C6 | **File d'attente offline** : composer hors-ligne, envoi à la reconnexion. | ⭐ | M | Confort mobile. |
| C7 | **Push-to-talk** : maintenir pour dicter, relâcher pour envoyer directement. | ⭐ | S | Améliore la voix existante. |

### D. Intelligence & autonomie

| # | Amélioration | Impact | Effort | Notes |
|---|---|---|---|---|
| D1 | **Feed proactif** : surfacer dans l'app les sorties des agents existants (morning-briefing, weekly-audit, digest Iris) — un onglet « Fil » avec les rapports. | ⭐⭐⭐ | M | Ces agents tournent déjà ; leurs résultats ne sont pas visibles dans Pocket. Gros levier, faible coût. |
| D2 | **Routage de modèle** : Haiku/Sonnet pour les lectures simples, Opus pour le complexe → coût maîtrisé, réponses plus rapides. | ⭐⭐ | M | Décision : nécessite tolérance au métré ou reste sur abonnement. |
| D3 | **Suivi de coût réel** : `total_cost_usd` par run est déjà loggé → agréger un « coût du jour / mois » dans l'onglet Système (vrais chiffres, plus d'estimation). | ⭐⭐ | S | Données déjà disponibles. |
| D4 | **Knowledge relié au Brain/RAG** : l'agent cite la connaissance utilisée et peut interroger le RAG local `brain.py`. | ⭐ | L | Puissant mais lourd (RAG en CI). |

### E. Observabilité / ops

| # | Amélioration | Impact | Effort | Notes |
|---|---|---|---|---|
| E1 | **`pocket-data/status.json`** écrit à chaque run (système touché, succès, coût, durée, dernière erreur) → source de vérité pour A1/D3. | ⭐⭐⭐ | S | Brique transverse : débloque le panneau santé et le suivi coût. |
| E2 | **Historique coût + durée par tâche** dans le détail. | ⭐ | S | Découle de E1. |

---

## 🚦 Roadmap proposée (séquencée par ROI)

### Phase 0 — Fiabiliser & rendre visible (fondation, ~1-2 j)
Petit effort, gros retour de confiance. **Prérequis à tout le reste.**
- **E1** `status.json` par run (brique transverse)
- **A1** Panneau « Santé des systèmes »
- **A2** Alerte proactive expiration token
- **A5** Fix robustesse scheduler
- **B5** Ajouter `LEMLIST_API_KEY` (débloque outreach immédiatement)
- **D3** Suivi de coût réel (dérive de E1)

### Phase 1 — Étendre la couverture métier (~3-4 j)
Rapproche vraiment de « tout piloter depuis le tel ».
- **B1** Google Ads (fort ROI, auth déjà là)
- **B2** Gmail (draft de réponse)
- **D1** Feed proactif (surfacer les agents existants)
- **A3** Bouton « Relancer »

### Phase 2 — Fluidité & confiance sur l'écriture (~3-4 j)
- **C5** Preview d'écriture structurée
- **C2** Bibliothèque de prompts paramétrés
- **C3** Rendu riche (tables/charts)
- **B3** Écriture vault
- **C4** iOS Shortcuts / Siri

### Phase 3 — Raffinements (au besoin)
- **C1** Streaming temps-réel · **A4** Taxonomie d'erreurs · **D2** Routage modèle
- **B4** Calendar · **B6** Notion/Slack · **B7** Analytics · **C6/C7** offline/PTT · **D4** RAG

---

## ❓ Décisions à trancher (avant implémentation)

1. **Coût** : rester 100 % abonnement (0 €) ou accepter un métré (`ANTHROPIC_API_KEY`)
   pour le routage de modèle (D2) et plus de volume ? → conditionne D2, la fréquence
   des crons, et le choix de modèle par défaut.
2. **Systèmes prioritaires** : parmi Ads / Gmail / Vault-write / Calendar / Slack /
   Notion — lesquels d'abord ? (la roadmap parie Ads + Gmail).
3. **Écriture vault** (B3) : accepte-t-on un PAT en écriture sur le repo vault
   (garde-fous requis) ?
4. **Périmètre** : outil solo (statu quo) ou besoin futur de partage/multi-user ?

---

## 🔩 Notes d'implémentation transverses
- Tout nouveau système = un `scripts/pocket_<systeme>.py` déterministe (REST + stdlib,
  token via env du step) — **pas** de MCP fragile (leçon plumbing env).
- Écritures toujours gatées par le label `approved` (pattern existant).
- Bump du cache SW (`sw.js`) à chaque version front, sinon iOS sert l'ancienne.
- Push sur `main` bloqué par le classifieur → **branche + PR** systématique.
- Réindexer le RAG / mettre à jour la mémoire après changements structurels.

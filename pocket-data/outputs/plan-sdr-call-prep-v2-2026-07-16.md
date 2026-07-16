# Plan complet V2 — Assistant « Prep de call » SDR

> Issue #170 · 2026-07-16 · V2 approfondie du plan initial ([V1 ici](plan-sdr-call-prep-2026-07-16.md)).
> Idée d'origine : la manageuse de Gaspard. Investigation : Claude Pocket, ancrée sur le vault EMAsphere (projet [[SDR-Agent-IA]], playbook [[SDR-Agent-Sales-Ops-Playbook]], stack [[PhantomBuster]]) et sur des données HubSpot vérifiées en prod le 2026-07-16.

---

## 0. Résumé exécutif

**L'idée** : chaque matin, le SDR annonce « je contacte la liste X » ; l'assistant produit un **brief de 5 lignes par contact** (société, personne, historique CRM, activité LinkedIn récente, angle d'attaque), délivré **un contact à la fois** sur « OK suivant », pour ramener la prep de call de 5-10 min à ~1 min.

**Verdict** : idée solide, ROI déjà chiffré au playbook (**5 min gagnées × ~93 calls/sem ≈ 8 h/SDR/semaine** ; 1 call ≈ 97 € de valeur au funnel de référence 93 calls → 28 conversations → 7 deals → 1 client = 9 000 €). Surtout : **~70 % de l'infrastructure existe déjà** (projet SDR Agent IA : extension Chrome + `/api/brief` construits, `/api/focus` déjà sur la roadmap Phase 2). La nouveauté réelle = la **couche LinkedIn live** et le **rythme un-par-un** — c'est là que se concentrent les décisions (§5) et les risques (§6).

**Recommandation** : démarrer la **Phase 0 sans aucun dev** (prototype via Pocket, LinkedIn en lecture manuelle) dès cette semaine avec 1 SDR pilote, pendant que la manageuse tranche la question LinkedIn (scraping léger vs Sales Navigator). Industrialiser ensuite dans l'extension SDR Agent.

**Les 3 décisions à prendre** (détail §10) :
1. Couche LinkedIn : scraping PhantomBuster (risque ToS, ~0 € marginal) vs Sales Navigator Advanced (conforme, licence payante) vs lecture manuelle (gratuit, 30-60 s de plus par call).
2. SDR pilote + liste pilote pour la Phase 0.
3. Canal de consommation cible : sidebar HubSpot (recommandé, Phase 2) vs fil Pocket vs Slack.

---

## 1. Parcours SDR cible (minute par minute)

### 08:50 — Ouverture de session
Le SDR ouvre sa session (Phase 0 : issue Pocket ; Phase 2 : sidebar HubSpot, bouton « Session du jour ») et désigne sa liste : *« Je contacte la liste "Relance MQL webinar juin" »*.

L'assistant répond en ~30 s :
- confirme la liste (nom, taille, propriétaire) et annonce l'ordre de passage ;
- **pré-génère en batch** les lignes 1-2-3-5 de TOUS les briefs (HubSpot + vault, zéro quota) ;
- signale d'emblée les contacts sans lien LinkedIn (« ligne 4 indisponible pour 3 contacts sur 12 ») et les contacts à donnée douteuse (email bounce, société fermée) pour que le SDR les traite en connaissance de cause.

### 08:52 — Contact 1
L'assistant fetch l'activité LinkedIn du contact 1 **uniquement** (~20-30 s), fusionne la ligne 4, et livre le brief complet. Le SDR le lit en **≤ 1 minute**, passe son call.

### 09:05 — « OK suivant »
Pendant que le SDR loggue son call (note HubSpot), l'assistant fetch le LinkedIn du contact 2. Le brief suivant est prêt quand le SDR l'est. Le rythme naturel entre deux calls (~10-15 min) absorbe entièrement la latence LinkedIn.

Commandes de session supportées : `OK suivant` · `skip` (passer sans fetch LinkedIn) · `pause` / `reprends` · `stop` (fin de session + récap) · `refais l'angle` (regénérer la ligne 5 avec une contrainte, ex. « angle multi-entités plutôt que clôture »).

### 12:30 — Fin de session
`stop` → l'assistant poste un **récap de session** : contacts traités / skippés, temps moyen, angles utilisés, et propose les notes de call à créer (écriture HubSpot **gatée par approbation**, cf. garde-fous). Rien de LinkedIn n'est persisté (§6 RGPD).

**Point d'attention adoption** (issu du playbook, règle d'usage n°4) : le brief se prépare **avant/entre** les calls, jamais pendant — l'assistant prépare et propose, le SDR décide et parle.

---

## 2. Spécification du brief (le livrable cœur)

### 2.1 Format — 5 lignes, ~80 mots max, scannable en 20 s

```
🏢 SOCIÉTÉ   — Groupe Dupont SA (Liège) · distribution · ~120 emp. · multi-entités (4 filiales BE/FR) · fit ICP : FORT
👤 PERSONNE  — Marie Lambert, CFO depuis 03/2025 (ex-Deloitte) · FR · décideuse probable (motion Direct-to-CFO)
📋 HISTORIQUE — MQL 04/2026 (webinar conso) · 2 emails ouverts, 0 réponse · dernier call SDR 12/05 : « rappeler après clôture »
💬 LINKEDIN  — A commenté il y a 3 j un post sur les délais de clôture multi-entités ; a reposté l'annonce d'acquisition d'une filiale FR
🎯 ANGLE     — Accroche : l'acquisition récente → complexité de conso. Pain probable : clôture > 15 j. Réf. à citer : [client distribution BE]. Ouvrir en N.E.A.T., pas de pitch.
```

### 2.2 Sources et règles, ligne par ligne

| Ligne | Sources | Règles de génération | Dégradation si donnée absente |
|---|---|---|---|
| 🏢 Société | Company HubSpot (`name`, `city`, `industry_emalist`, `numemployees`/`linkedin_employee_count`, `multiple_legal_entities_`, props CA) + `icp.json` | Fit ICP calculé sur la matrice Fit du playbook (CA 10-500 M€, >50 emp., multi-entités, BE/FR). ⚠️ `multiple_legal_entities_` = enum `Yes`/`No` (pas un booléen) et rempli à 17,6 % seulement → afficher « multi-entités : inconnu » plutôt que « non ». | « Société : données partielles (X manquant) » — jamais inventer |
| 👤 Personne | Contact HubSpot (`jobtitle`, `firstname/lastname`, langue) + détection de motion (jobtitle + industry, logique déjà codée dans `/api/brief`) | Motion Direct-to-CFO vs Channel. Ancienneté au poste via `pb_job_started_since` si dispo (~14 % rempli). | Rôle brut sans interprétation |
| 📋 Historique | Engagements HubSpot (emails, calls, meetings, notes via associations API) + `lifecyclestage`, activité de séquence | Max 3 faits, les plus récents et les plus signifiants (une réponse > 10 ouvertures). Citer la dernière note de call verbatim si elle existe. | « Aucune interaction loggée » (info utile en soi : cold call) |
| 💬 LinkedIn | URL coalescée (§3.1) → activité récente (posts, commentaires, reposts, changement de poste) | **Seule ligne au rythme un-par-un.** Fenêtre : 90 jours. Prioriser : contenu propre > commentaire > repost > like. Si rien : le signaler (c'est aussi un signal — profil passif → l'email pèse plus). | « Activité LI indisponible » + lien profil cliquable pour lecture manuelle — ne jamais bloquer la session |
| 🎯 Angle | Synthèse lignes 1-4 × vault (`icp.json`, `references.json`, `pitches.json`, script CFO, N.E.A.T.) | Toujours 4 éléments : accroche (idéalement ligne 4), pain probable, référence client à citer (même géo/secteur via `references.json`), méthode d'ouverture. **Chaque affirmation traçable à une source visible dans les lignes 1-4** — un brief faux est pire que pas de brief. | Angle générique par segment ICP, marqué « (générique) » |

### 2.3 Règles transverses

- **Langue** : brief dans la langue du SDR ; éléments à dire au prospect (accroche) dans la langue du contact (fr-be / nl-be / fr). Le champ langue HubSpot fait foi ; défaut = FR.
- **Fraîcheur** : brief généré le jour même, timestampé. Jamais de cache > 24 h pour les lignes 3-4.
- **Honnêteté sur l'incertitude** : « décideuse **probable** », « pain **probable** » — le brief propose, le SDR juge (périmètre agent/humain du playbook).
- **Anti-hallucination** : tout fait du brief doit provenir d'une propriété HubSpot, d'un engagement, du scrape LI du jour, ou d'un fichier vault nommé. Le prompt exige la source par fait ; en Phase 3 on audite par échantillonnage.

---

## 3. Données & faisabilité (vérifié en prod le 2026-07-16)

### 3.1 Couverture LinkedIn : ~7 contacts sur 10

Portail ≈ 278k contacts, 6 propriétés URL LinkedIn concurrentes. Ordre de coalescence :

| Priorité | Propriété | Remplie sur |
|---|---|---|
| 1 | `lemlistlinkedinurl` | 197 112 (~71 %) |
| 2 | `lgm_linkedinurl` | 196 572 (~71 %) |
| 3 | `linkedin_url` | 106 962 |
| 4 | `pb_linkedin_profile_url` | 68 632 |
| 5 | `hs_linkedin_url` | 38 987 |

→ Sur une liste de call typique (leads travaillés, donc plutôt mieux enrichis que la moyenne), on peut attendre **≥ 70 % de briefs avec ligne 4**. Pour les autres : dégradation propre (lien de recherche LinkedIn pré-rempli nom+société pour lecture manuelle en 20 s).

### 3.2 Historique d'interactions
Engagements HubSpot (notes, emails, calls, meetings) lisibles via associations API v3/v4 — lecture seule, déjà accessible avec le token actuel. Le client `getFullContactContext` du backend SDR Agent les récupère déjà.

### 3.3 Listes de call
Listes HubSpot statiques/actives lisibles par API (`lists`, `list-members` — déjà câblé dans `pocket_hubspot.py`). Aucun prérequis : les SDR utilisent leurs listes existantes telles quelles.

### 3.4 Qualité de données — impact connu (audit du 2026-07-10)
- `numemployees` quasi mort (~1 %) → utiliser `linkedin_employee_count` pour la taille.
- 3 propriétés CA concurrentes (~50 % de couverture combinée) → coalescer, sinon « CA : inconnu ».
- `multiple_legal_entities_` : critère ICP le plus vide (17,6 %) — le brief doit le dire quand il ne sait pas.
- Doublons Koalify (4 957 companies) : si le contact pointe vers une company doublonnée, le signaler dans la ligne 1.

---

## 4. Architecture

### 4.1 Principe : hybride batch + un-par-un

Le un-par-un ne s'applique **qu'à LinkedIn**. Les lignes HubSpot+vault sont de l'API sans quota : les générer une par une ferait attendre le SDR pour rien.

```
  SDR : « je contacte la liste X »
        │
        ▼
┌──────────────────────────┐   t=0, batch, ~30 s au total
│ 1. Lire la liste (API)    │
│ 2. Coalescer URLs LI      │
│ 3. Générer lignes 1-3+5   │──▶ file de briefs partiels (en mémoire de session)
│    pour TOUS les contacts │
└──────────────────────────┘
        │  « OK suivant » (répété)
        ▼
┌──────────────────────────┐   un contact à la fois, ~20-30 s
│ 4. Fetch LinkedIn du      │
│    contact N uniquement   │──▶ fusion ligne 4 → brief complet → livraison
│    (+ regen ligne 5 si    │
│    l'activité LI change   │
│    l'angle)               │
└──────────────────────────┘
        │  « stop »
        ▼
  Récap session + proposition de notes (écriture gatée `approved`)
```

Pacing LinkedIn résultant : **~15-30 profils/jour/SDR** au rythme des calls — confortablement sous l'ordre de grandeur prudent documenté (~80-100 profils/jour/compte), avec en plus un **plafond dur logiciel** (60/jour/compte, compteur persistant) et étalement heures de bureau.

### 4.2 Composants par phase

| Composant | Phase 0 (prototype) | Phase 2 (cible) |
|---|---|---|
| Interface SDR | Fil d'issue Pocket (mobile/desktop) | Sidebar Chrome dans HubSpot, bouton « Suivant » |
| Orchestration session | Claude Pocket (issue itérative) | `GET/POST /api/focus` (Next.js/Vercel, déjà sur roadmap) |
| Brief HubSpot+vault | Pocket (scripts + vault) | `/api/brief` existant, réutilisé tel quel |
| État de session (file, position, compteur LI) | Fil d'issue (implicite) | `localStorage` extension + store serveur léger (KV Vercel) |
| Couche LinkedIn | Lecture manuelle (lien fourni) | Selon décision §5 |
| Knowledge métier | Vault (ICP, références, scripts) | Les 5 JSON de la KB (`icp`, `references`, `pitches`…) |

### 4.3 Spec indicative `/api/focus` (Phase 2)

- `POST /api/focus/start` `{listId}` → crée la session : membres, URLs coalescées, briefs partiels ; retourne `{sessionId, queue[], warnings[]}`.
- `GET /api/focus/next?sessionId=` → fetch LI du contact courant (si activé et sous plafond), fusionne, retourne le brief complet + `remaining`.
- `POST /api/focus/skip|pause|stop` → gestion de file ; `stop` retourne le récap.
- Garde-fous serveur : plafond LI/jour/compte, timeout LI 45 s → dégradation, aucun stockage du contenu LinkedIn au-delà de la session (TTL ≤ 24 h).

---

## 5. La décision structurante : la couche LinkedIn (matrice d'options)

| | **A. PhantomBuster (cookie `li_at`)** | **B. Sales Navigator ↔ HubSpot** | **C. Lecture manuelle assistée** | D. « Embedded » (extension lit l'onglet LI du SDR) |
|---|---|---|---|---|
| Conformité ToS LinkedIn | ❌ Contraire aux CGU (automatisation via session) | ✅ Intégration officielle | ✅ | ⚠️ Zone grise (automatise la lecture d'une session humaine) |
| Risque compte | Restriction possible du compte dont on utilise le cookie | Aucun | Aucun | Faible mais non nul |
| Fraîcheur/richesse activité | ✅ Posts, commentaires, reposts | ⚠️ Icebreakers/alertes dans la fiche, moins granulaire | ✅ (l'humain voit tout) | ✅ |
| Automatisation ligne 4 | ✅ Totale | ⚠️ Partielle (affichage fiche, pas d'API publique d'activité) | ❌ +30-60 s/call pour le SDR | ✅ |
| Coût marginal | ~0 € (compte PB existant ; consomme l'execution time mensuel du plan) | Licence Sales Nav **Advanced** par SDR (ordre de grandeur ~130-150 €/mois/siège — à confirmer, tarif entreprise négociable) | 0 € | Dev extension non trivial (~1-2 sem) |
| Fragilité opérationnelle | Cookie expire (2FA, logout) → échecs **silencieux** ; sélecteurs cassés par MAJ LinkedIn | Faible | Nulle | MAJ DOM LinkedIn |
| Effort de mise en place | 2-4 j (phantom Activity Extractor + plafonds + monitoring) | Config admin + achat licences | 0 | 1-2 sem |

**Recommandation** : Phase 0 en **option C** (gratuite, immédiate, mesure déjà 80 % du gain). Pour la suite, la décision A vs B appartient à la manageuse car c'est un arbitrage **risque ToS vs budget licence** — pas un arbitrage technique. Si A est choisi : un cookie **par SDR** (jamais un compte partagé qui concentre le risque), plafond dur 60/j, heures de bureau, monitoring des résultats vides (cookie mort = premier réflexe), et acceptation écrite du risque. L'option D peut servir de plan B conforme-mieux si B est jugée trop chère et A trop risquée.

---

## 6. Conformité & garde-fous

### 6.1 RGPD
- **Base légale** : intérêt légitime (prospection B2B, données professionnelles publiques) — défendable pour un brief **éphémère** de préparation de call.
- **Minimisation / non-persistance** : l'activité LinkedIn n'est **jamais écrite dans HubSpot** ni stockée au-delà de la session (TTL ≤ 24 h). Seul l'angle retenu peut aller en note de call, reformulé, si le SDR le décide.
- **Exactitude** : le brief cite ses sources ; pas de scoring caché ni de profilage persistant.
- À faire en Phase 1 : passage rapide devant le référent RGPD (registre des traitements : nouvelle finalité « préparation d'appel », mention de LinkedIn comme source).

### 6.2 Garde-fous techniques (hérités des runner-guardrails, non négociables)
- Lecture seule par défaut ; toute écriture HubSpot (notes de call du récap) = preview + label `approved`, jamais d'écrasement de champ rempli.
- Plafond LinkedIn dur + compteur/jour/compte + kill switch (désactiver la ligne 4 sans casser la session).
- Aucun secret loggué ; cookies/API keys via secrets GitHub / Keychain ; `python3.12` pour les scripts locaux.
- Échec LinkedIn = dégradation propre, jamais de blocage de session ; `finished` avec 0 résultats ≠ succès (piège PhantomBuster documenté).

### 6.3 Qualité (le risque n°1 pour l'adoption)
Un brief faux détruit la confiance plus vite que dix bons briefs ne la construisent. Trois mécanismes :
1. Traçabilité par fait (§2.3) ;
2. Bouton/commande « signaler une erreur » → chaque signalement corrige la KB ou le prompt (boucle du playbook) ;
3. Audit hebdo par échantillonnage : 5 briefs relus vs les fiches sources (Sentinel/Gaspard) pendant les 4 premières semaines.

---

## 7. Plan d'exécution détaillé

### Phase 0 — Prototype sans dev, via Pocket (S29, 1-2 jours de mise en place)
**Objectif** : valider le format du brief et mesurer le gain réel avec 1 SDR pilote, avant tout investissement.

| # | Tâche | Qui | Effort |
|---|---|---|---|
| 0.1 | Choisir SDR pilote + liste pilote (10-15 contacts, motion Direct-to-CFO) | Manageuse + Gaspard | 15 min |
| 0.2 | Gabarit d'issue « 📞 Prep calls — [liste] » (protocole OK suivant/skip/stop documenté) | Gaspard (avec Pocket) | 30 min |
| 0.3 | Session test à blanc : Gaspard déroule 3 briefs, ajuste le format | Gaspard + Pocket | 1 h |
| 0.4 | 1re session réelle avec le SDR (shadow : chrono de prep, feedback ligne par ligne) | SDR + Gaspard | ½ j |
| 0.5 | 2 semaines d'usage, ~20 calls, mesure (grille §8) | SDR pilote | fil de l'eau |

**Critères de sortie** : temps de prep < 2 min ressenti ; ≥ 80 % des briefs jugés « fiables et utiles » ; le SDR redemande l'outil spontanément. **Si échec** : le problème est le format ou la donnée, pas la tech — itérer sur le brief avant d'écrire la moindre ligne de code.

### Phase 1 — Couche LinkedIn automatisée (S31-S32, 2-4 jours de dev, conditionnée à la décision §5)
| # | Tâche | Effort |
|---|---|---|
| 1.1 | Décision A/B/C actée par la manageuse (+ acceptation risque écrite si A) | — |
| 1.2 | Si A : phantom « Activity Extractor » appelé un-par-un, parsing activité 90 j, plafond dur + compteur | 1-2 j |
| 1.3 | Fusion ligne 4 + regénération conditionnelle de l'angle | ½ j |
| 1.4 | Monitoring : alerte cookie mort / 0-résultats, kill switch | ½ j |
| 1.5 | Validation RGPD (registre, non-persistance vérifiée) | ½ j |

### Phase 2 — Industrialisation dans le SDR Agent IA (S33-S35, 1-2 semaines de dev)
| # | Tâche | Effort |
|---|---|---|
| 2.1 | `POST /api/focus/start` + `next/skip/stop` (spec §4.3), réutilise `/api/brief` | 3-4 j |
| 2.2 | UI sidebar : sélecteur de liste, file, bouton « Suivant », brief streamé, badge « restants » | 2-3 j |
| 2.3 | Récap de session + création de notes gatée (preview + approbation) | 1 j |
| 2.4 | Onboarding des autres SDR (protocole playbook : shadow 5 calls, règles d'usage, J+7) | ½ j/SDR |
| 2.5 | Boucle d'apprentissage : objections entendues → `pitches.json` (via `/api/objection`) | fil de l'eau |

### Phase 3 — Mesure & généralisation (S36+, fil de l'eau)
Dashboard des KPIs §8, revue à J+30 avec la manageuse : généraliser, ajuster, ou arrêter.

---

## 8. Mesure : KPIs et méthode

**Baseline à capturer AVANT la Phase 0** (sinon rien n'est démontrable) : temps de prep actuel auto-déclaré sur 10 calls + conversation-rate des 4 dernières semaines du SDR pilote.

| KPI | Baseline | Cible | Méthode |
|---|---|---|---|
| Temps de prep / call | ~5-10 min (à mesurer) | **< 2 min** (cible playbook) | Chrono déclaratif Phase 0, timestamps `/api/focus` en Phase 2 |
| Couverture ligne 4 (LinkedIn) | — | ≥ 70 % des briefs | Compteur automatique |
| Fiabilité perçue | — | ≥ 80 % « fiable et utile » | Pouce haut/bas par brief + audit hebdo échantillonné |
| Conversation-rate (calls → conversations) | ~30 % (28/93 funnel réf.) | ↑ vs cohorte non préparée | Comparaison calls avec brief vs sans (les SDR non pilotes = groupe témoin naturel) |
| Utilisation de l'accroche LI | — | suivi (pas de cible) | Question au récap de session |
| Adoption | — | Le SDR relance des sessions sans qu'on lui demande | Nombre de sessions/semaine |

**Valeur si ça marche** : 8 h/SDR/semaine libérées = ~1 journée réinvestie en calls ; à 97 €/call de valeur théorique, même +5 calls/semaine ≈ +485 €/semaine/SDR de valeur funnel — largement au-dessus du coût de fonctionnement (§9).

---

## 9. Coûts (ordres de grandeur)

| Poste | Estimation | Note |
|---|---|---|
| Phase 0 | **0 €** + ~1 j de temps Gaspard | Pocket + HubSpot existants |
| Génération briefs (Claude API) | ~0,02-0,05 €/brief → **< 25 €/mois/SDR** à 20 briefs/j | Sur l'infra Vercel existante |
| Option A — PhantomBuster | 0 € marginal (plan actuel) ; consomme l'execution time mensuel | Vérifier le quota restant du plan avant Phase 1 |
| Option B — Sales Nav Advanced | ~130-150 €/mois/siège (à confirmer en tarif entreprise) | Seul vrai poste de coût récurrent |
| Dev Phases 1-2 | ~2-3 semaines réparties | Interne (Gaspard + Forge), pas de presta |

---

## 10. Décisions demandées & questions ouvertes

**Pour la manageuse :**
1. **LinkedIn** : option A (scraping léger, risque ToS accepté et documenté, cookie par SDR), B (budget Sales Nav Advanced), ou C prolongée (manuel assisté) ? — c'est un arbitrage risque/budget, pas technique.
2. **Pilote** : quel SDR, quelle liste, quelle semaine ? (Proposition : S29, un SDR volontaire motion Direct-to-CFO, liste de 10-15 relances.)
3. **Ambition** : outil d'équipe SDR uniquement, ou aussi AE (les briefs serviraient au handoff SQL, JC/Yacine/Chris) ?

**Pour Gaspard :**
4. Canal cible Phase 2 : sidebar HubSpot (recommandé — les SDR y vivent déjà) vs Slack vs Pocket ?
5. Brief bilingue FR/NL selon la langue du contact : dès la Phase 0 ou en Phase 2 ?
6. Backend SDR Agent : le TODO du projet note que le déploiement Vercel/extension n'est pas finalisé partout — à vérifier avant la Phase 2 (sinon l'inclure dans 2.1).

---

## 11. Risques (registre consolidé)

| Risque | Prob. | Impact | Mitigation |
|---|---|---|---|
| Restriction compte LinkedIn (option A) | Moyenne | Fort (compte SDR) | Un-par-un, plafond 60/j, cookie par SDR, heures bureau, kill switch ; ou option B |
| Brief erroné → perte de confiance SDR | Moyenne | Fort (adoption morte) | Traçabilité par fait, signalement 1-clic, audit hebdo, honnêteté sur l'incertitude |
| Cookie `li_at` expiré → échecs silencieux | Haute (récurrent) | Moyen | Alerte 0-résultats, dégradation propre, lien manuel en secours |
| Données HubSpot lacunaires (multi-entités 17,6 %, CA ~50 %) | Certaine | Moyen | Le brief dit « inconnu », jamais il n'invente ; nourrit au passage le backlog data quality |
| RGPD (persistance activité LI) | Faible si règle tenue | Fort | Non-persistance par design, TTL session, revue référent RGPD Phase 1 |
| Non-adoption (« encore un outil ») | Moyenne | Fort | Phase 0 avec un volontaire, co-construction du format, mesure du gain AVANT généralisation |
| Dérive d'usage (brief lu pendant le call) | Faible | Faible | Règle d'usage playbook rappelée à l'onboarding |

---

## 12. Prochaine action immédiate

**Cette semaine, sans attendre aucune décision** : lancer la Phase 0. Il suffit que Gaspard donne le nom d'une liste HubSpot et Pocket déroule la première session de test (brief du contact 1 → « OK suivant » → contact 2). Coût : zéro. Apprentissage : immédiat.

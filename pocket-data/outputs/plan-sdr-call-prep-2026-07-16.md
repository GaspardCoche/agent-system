# Plan — Assistant « Prep de call » SDR (brief 1 minute par contact)

> Issue #170 · 2026-07-16 · Idée proposée par la manageuse de Gaspard, investiguée par Claude Pocket.

## 1. L'idée en une phrase

Chaque matin, le SDR dit « je contacte les personnes de la liste X » ; l'assistant produit, **un contact à la fois** (« OK suivant »), un **brief de 5 lignes** combinant HubSpot (société, personne, historique) et LinkedIn (activité récente = point d'accroche), croisé avec le playbook ICP → un angle d'attaque prêt à l'emploi, **1 minute de prep par call** au lieu de 5-10.

## 2. Verdict : très bonne idée — et on part de 70 % d'existant

L'idée est solide, et elle est **déjà à moitié construite** chez EMAsphere :

| Brique | État | Où |
|---|---|---|
| Brief prospect généré par IA (HubSpot + knowledge base ICP/concurrents/références) | ✅ construit | Projet **SDR Agent IA** : extension Chrome + API Next.js/Vercel, endpoint `GET /api/brief` |
| Mode « session de calls du jour » | 📋 déjà sur la roadmap | `/api/focus` listé en Phase 2 du projet SDR Agent IA |
| Playbooks ICP / qualification / script CFO | ✅ dans le vault | `ICP-Qualification.md`, `Discovery-Call-Framework.md`, `SDR-Agent-Sales-Ops-Playbook.md` |
| Scraping LinkedIn (profil + activité) | ✅ outillé | PhantomBuster (API v2, phantoms profil/activity) |
| Listes de call | ✅ natif HubSpot | Listes statiques/actives, lisibles par API (`lists`, `list-members`) |
| Boucle interactive « OK suivant » | ✅ existe déjà | Pocket lui-même (fil d'issue itératif) — prototype possible **sans aucun dev** |

Le ROI est déjà chiffré dans le playbook SDR : **5 min de prep gagnées × ~93 calls/semaine ≈ 8 h/SDR/semaine** (1 call ≈ 97 € de valeur au funnel de référence). La cible du playbook est « temps de prep < 2 min » — cette idée y répond directement.

**La vraie nouveauté de l'idée = la couche LinkedIn « live »** (activité récente comme accroche) + le **rythme un-par-un**. C'est aussi là que se concentrent les risques (§6).

## 3. Le brief type (5 lignes)

```
🏢 SOCIÉTÉ   — Groupe Dupont SA (Liège) · distribution · ~120 emp. · multi-entités (4 filiales BE/FR) · fit ICP : FORT
👤 PERSONNE  — Marie Lambert, CFO depuis 03/2025 (ex-Deloitte) · FR · décideur probable (motion Direct-to-CFO)
📋 HISTORIQUE — MQL 04/2026 (webinar conso) · 2 emails ouverts, 0 réponse · dernier call SDR 12/05 : « rappeler après clôture »
💬 LINKEDIN  — A commenté il y a 3 j un post sur les délais de clôture multi-entités ; a reposté l'annonce d'acquisition d'une filiale FR
🎯 ANGLE     — Accroche : l'acquisition récente → complexité de conso. Pain probable : clôture > 15 j. Réf. à citer : [client secteur distribution BE]. Ouvrir en N.E.A.T., pas de pitch.
```

Lignes 1-3 et 5 = HubSpot + vault (zéro risque, instantané). Ligne 4 = LinkedIn (la seule qui nécessite le rythme un-par-un).

## 4. Données : c'est faisable aujourd'hui (vérifié en prod)

Vérifié ce jour sur le portail (≈278k contacts) — couverture des URLs LinkedIn sur les contacts :

| Propriété | Contacts remplis |
|---|---|
| `lemlistlinkedinurl` | 197 112 (~71 %) |
| `lgm_linkedinurl` | 196 572 (~71 %) |
| `linkedin_url` | 106 962 |
| `pb_linkedin_profile_url` | 68 632 |
| `hs_linkedin_url` | 38 987 |

→ En coalesçant (`lemlistlinkedinurl` → `lgm_linkedinurl` → `linkedin_url` → `pb_linkedin_profile_url` → `hs_linkedin_url`), **~7 contacts sur 10 ont un lien LinkedIn exploitable**. Pour les autres : brief sans ligne 4 (dégradé propre), ou résolution du profil à la volée.

Les « dernières interactions » viennent des engagements HubSpot (notes, emails, calls, meetings via associations API) — lecture seule, déjà accessible.

## 5. Architecture recommandée : hybride batch + un-par-un

Nuance importante par rapport à l'idée initiale : le rythme un-par-un ne doit s'appliquer **qu'à LinkedIn**. Tout le reste (HubSpot + vault) est de l'API sans quota — le générer un-par-un ferait attendre le SDR 30-60 s entre chaque call pour rien. Donc :

1. **Au démarrage de session** (« je contacte la liste X ») : lecture de la liste, génération immédiate des lignes 1-3 + 5 pour TOUS les contacts (batch, quelques secondes par contact, zéro risque).
2. **« OK suivant »** : fetch LinkedIn du contact N+1 uniquement (1 profil + activité), fusion dans le brief, livraison. ~30 s, ce qui colle au rythme naturel entre deux calls.
3. Le pacing LinkedIn qui en résulte (~15-30 profils/jour/SDR au rythme des calls) est **confortablement sous** l'ordre de grandeur sûr documenté (~80-100 profils/jour/compte).

## 6. Risques & garde-fous (à dire à la manageuse)

- **ToS LinkedIn** : le scraping via cookie de session (`li_at`, méthode PhantomBuster) est contraire aux CGU LinkedIn. Le risque (restriction du compte) porte sur le **compte dont on utilise le cookie**. Mitigations : volume faible (le un-par-un de la manageuse est le bon instinct), heures de bureau, un cookie par SDR (pas un compte partagé qui concentre le risque), et décision explicite d'accepter ce risque — ou alternative officielle :
  - **Alternative sans risque** : l'intégration native **LinkedIn Sales Navigator ↔ HubSpot** (licence Sales Nav Advanced) affiche les icebreakers/activité dans la fiche contact sans scraping. Moins automatisable, mais 100 % conforme. À chiffrer si le risque ToS est refusé.
- **Fragilité du cookie** : `li_at` expire à chaque déconnexion/2FA → les phantoms échouent *silencieusement* (0 résultats). Le brief doit dégrader proprement (« activité LI indisponible ») et alerter, jamais bloquer la session.
- **RGPD** : l'activité LinkedIn est une donnée personnelle publique ; l'utiliser en éphémère pour préparer un call B2B = intérêt légitime défendable. **Garde-fou : ne pas persister l'activité LinkedIn dans HubSpot** (le brief est jetable, seul l'angle retenu va en note de call si le SDR le décide).
- **Qualité** : un brief faux est pire que pas de brief (le SDR perd confiance). Chaque affirmation de la ligne 5 doit être traçable (source HubSpot ou LI visible).

## 7. Plan de mise en œuvre

### Phase 0 — Prototype sans dev, via Pocket (1-2 jours, dès validation)
- Le SDR (ou Gaspard) ouvre une issue Pocket : « Prep calls — liste [nom] ».
- Pocket lit la liste (`pocket_hubspot.py list-members`), génère le brief HubSpot+vault du contact 1, le poste en commentaire ; « OK suivant » (follow-up) → contact 2, etc.
- LinkedIn en Phase 0 : lecture *manuelle* par le SDR via le lien fourni dans le brief (zéro risque, zéro dev) — on mesure déjà le gain de temps des lignes 1-3-5.
- **Critère de succès** : temps de prep ressenti < 2 min, brief jugé fiable par 1 SDR pilote sur ~20 calls.

### Phase 1 — Couche LinkedIn automatisée (2-4 jours de dev)
- Décision préalable : PhantomBuster (risque ToS accepté, cookie par SDR) **ou** Sales Nav embarqué (licence).
- Si PhantomBuster : phantom « Activity Extractor » appelé un-par-un au « OK suivant », fusion ligne 4, dégradation propre si échec, compteur de profils/jour avec plafond dur (ex. 60).

### Phase 2 — Industrialisation dans le SDR Agent IA (1-2 semaines)
- Implémenter `/api/focus` (déjà sur la roadmap) : sélection de la liste dans la sidebar Chrome, file de contacts, bouton « Suivant », brief streamé.
- Boucle d'apprentissage : l'issue/le call log nourrit `pitches.json` (objections réelles) — cf. playbook SDR.

### Phase 3 — Mesure
- Suivre les métriques du playbook : temps de prep/call, reply-rate/conversation-rate des calls préparés vs non préparés, feedback SDR à J+7.

## 8. Questions ouvertes (pour la manageuse)

1. Accepte-t-on le risque ToS LinkedIn (scraping léger, cookie par SDR) ou budget Sales Navigator Advanced ?
2. Quel SDR pilote, et sur quelle liste, pour la Phase 0 ?
3. Le brief doit-il être bilingue (FR/NL) selon le contact ?
4. Où le SDR consomme-t-il le brief : fil Pocket (Phase 0), sidebar HubSpot (Phase 2), ou Slack ?

# Rapport complet — Automatiser le workflow « profil LinkedIn → téléphone → message → HubSpot »

> Issue #171 · 2026-07-16 · Analyse approfondie demandée par Gaspard, suite à l'échange avec le collègue TA (et la réponse initiale de « Claudy »).
> Sources : vault EMAsphere ([[FullEnrich]], [[Lead-Enrichment]], [[SDR-Agent-IA]], playbook Sales Ops), données HubSpot vérifiées en prod (audits 2026-07-10 et 2026-07-16), plan V2 issue #170.

---

## 0. Résumé exécutif

**La question du collègue** : comment accélérer « je vois un profil LinkedIn intéressant → je récupère son téléphone → je lui envoie un message LinkedIn → je loggue tout dans HubSpot » ?

**Verdict en 5 points :**

1. **Sur les 4 étapes, une seule doit rester manuelle : le clic « envoyer »** (ToS LinkedIn). Tout le reste — brief du profil, téléphone, rédaction, logging — est automatisable avec des outils **déjà payés et câblés** chez EMAsphere.
2. **La réponse de Claudy est juste sur les interdits mais incomplète sur la stack** : elle ignore FullEnrich (le téléphone EST enrichissable, conformément, sans toucher à LinkedIn) et le projet SDR Agent IA (le brief de profil est déjà industrialisé).
3. **Le collègue se trompe sur le téléphone** (« can't be enriched that way anyway ») : le pipeline standard `LinkedIn URL → FullEnrich → HubSpot` produit un **mobile vérifié dans ~60-65 % des cas** (64 % mesuré sur la base SDR). C'est la correction factuelle n°1 à faire passer.
4. **Sa proposition de séquenceur est valable mais répond à un autre cas d'usage** (volume programmatique vs profil high-intent repéré à la main). Les deux se combinent ; aucun des deux ne rend l'envoi automatique conforme aux ToS LinkedIn — « more naturally » = moins détectable, pas plus légal.
5. **Signal organisationnel fort** : le collègue construit la même chose que le projet SDR Agent / plan #170. Sans synchronisation, EMAsphere aura deux flux parallèles, deux conventions de logging et deux expositions au risque ToS. **Recommandation : un sync à trois (Gaspard + collègue + manageuse) avant tout build.**

**Gain chiffrable** : le workflow manuel coûte ~15-25 min par profil ; le flux cible le ramène à **~2-3 min de temps humain** (lecture du brief + clic d'envoi). Sur 5 profils/jour, c'est **~1h15-1h50 récupérées par jour et par personne**.

---

## 1. Analyse étape par étape du workflow (où part le temps, qu'est-ce qui s'automatise)

| # | Étape | Temps manuel estimé | Automatisable ? | Comment (outil en stock) | Ce qui reste humain |
|---|---|---|---|---|---|
| 1 | Lire le profil, prendre des notes de contexte | 3-5 min | ✅ Oui | **SDR Agent IA** — extension Chrome sidebar dans HubSpot, `GET /api/brief` : fit ICP, motion, triggers, concurrents, référence à citer, accroche. Backend construit, déploiement Vercel + chargement extension à finaliser. En attendant : Pocket fait le brief à partir de l'URL. | Juger la pertinence du profil (le « intéressant » initial) |
| 2 | Trouver le téléphone | 2-5 min, souvent en vain (LinkedIn ne l'affiche presque jamais) | ✅ Oui — **mais pas via LinkedIn** | **FullEnrich** (waterfall multi-fournisseurs, mobile-only) : input `linkedin_url` ou nom+domaine → `mobilephone` HubSpot, écriture non-destructive. Match rate ~60-65 %. | Rien — juste accepter que ~1/3 des contacts n'auront pas de mobile |
| 3 | Rédiger le message personnalisé | 5-10 min | ✅ Oui (rédaction) / ❌ Non (envoi) | `GET /api/pitch` (canal LinkedIn, motion-aware, langue-aware) ou draft Claude 1:1. **L'envoi reste un copier-coller humain** (ToS). | Le clic « envoyer » (~10 s) + jugement final sur le texte |
| 4 | Logger dans HubSpot | 3-5 min | ✅ Oui, totalement | Nom + URL LinkedIn + contexte → check d'existence (≈71 % de la base a déjà une URL LinkedIn), create/update contact, activité native « LinkedIn message », note avec le contenu. | Rien |
| | **Total** | **~15-25 min/profil** | | | **~2-3 min/profil** |

**Lecture clé** : l'étape que le collègue croyait la plus bloquante (le téléphone) est en réalité la mieux outillée ; l'étape qu'il voulait automatiser en priorité (l'envoi) est la seule qu'il ne faut PAS automatiser.

---

## 2. Le téléphone : correction factuelle complète (FullEnrich)

Le collègue affirme « the phone number can't be enriched that way anyway ». C'est faux — voici le mécanisme exact, vérifié dans le vault et en prod :

- **Principe** : FullEnrich est un **waterfall d'enrichissement** — il interroge en cascade plusieurs fournisseurs de données B2B conformes jusqu'à trouver un numéro validé. Aucune donnée n'est extraite de LinkedIn : l'URL LinkedIn ne sert que de **clé d'identification** de la personne.
- **Mobile-only by design** (vérifié 2026-06-16) : les lignes fixes et standards sont exclues et non facturées ; validation en 4 étapes (format → service → détection mobile → name-matching avec le titulaire). Ce qu'on récupère est donc un **mobile direct**, exactement ce qu'un SDR veut pour un cold call.
- **Performance mesurée** : match rate téléphone **~60-65 %** (référence : 64 % atteint sur la base SDR). Match rate global > 70 %.
- **Intégration** : pipeline standard déjà écrit (`scripts/pocket_fullenrich.py`, playbook [[Lead-Enrichment]]) → le numéro atterrit dans `mobilephone` HubSpot, **sans jamais écraser un champ déjà rempli** (règle non-destructive absolue).
- **Coût & discipline** : les crédits « phone » coûtent nettement plus cher que les emails → règle d'or : **filtrer en amont les contacts qui ont déjà un `mobilephone`** (fill rate actuel du téléphone sur les contacts : ~20 %) et ne demander `contact_info.phones` que sur champ vide. Batches ≤ 100 contacts.
- **Conformité** : les fournisseurs du waterfall sont des data providers B2B avec leurs propres bases légales ; c'est la voie RGPD-défendable, à l'opposé du scraping de la section « contact info » LinkedIn (contraire aux ToS + collecte sans base légale claire).

**Conséquence pratique pour le collègue** : son étape 2 disparaît entièrement. Il donne l'URL LinkedIn → le mobile arrive dans HubSpot en quelques minutes, dans ~2 cas sur 3.

---

## 3. Que logguer dans HubSpot (réponse structurée à sa question)

Réponse actée dans le plan #170 (règle RGPD de minimisation) — **trois choses à logguer, une à ne jamais logguer** :

| ✅ / ❌ | Quoi | Comment dans HubSpot | Pourquoi |
|---|---|---|---|
| ✅ | **Le contact** (créé ou mis à jour) | Check d'existence d'abord — ~71 % des 278k contacts ont déjà une URL LinkedIn (coalescence de 6 propriétés : `lemlistlinkedinurl` 197k > `lgm_linkedinurl` 196k > `linkedin_url` 107k > `pb_linkedin_profile_url` > `hs_linkedin_url`) → **toujours chercher avant de créer** | Éviter les doublons (déjà 4 957 companies doublonnées détectées par Koalify) |
| ✅ | **L'activité d'outreach** | Type d'activité natif « LinkedIn message » (Communications API) — timeline au même titre qu'un email ou un call | Continuité commerciale : n'importe qui reprenant le fil voit qu'un message LinkedIn est parti, et quand |
| ✅ | **Le contenu du message envoyé** | Corps de l'activité / note associée | Le successeur sait exactement ce qui a été dit ; base pour le follow-up |
| ❌ | **L'activité LinkedIn du prospect** (posts, commentaires lus pour trouver l'accroche) | Jamais persistée. Seul **l'angle retenu**, reformulé, peut aller en note si le SDR le décide | RGPD — minimisation : le contexte de lecture est éphémère par design (règle actée plan #170, TTL session) |

Cette distinction répond exactement à sa question (« the message you sent or simply an activity log? ») : **les deux** — activité native + contenu — plus le contact lui-même ; et rien de ce qu'on a lu chez le prospect.

---

## 4. Panorama des outils (ce qu'on a déjà vs ce qu'il propose)

| Outil | Statut chez EMAsphere | Rôle dans ce workflow | Limite / risque |
|---|---|---|---|
| **FullEnrich** | ✅ Payé, câblé, scripté | Téléphone (+ email, emploi, company) depuis l'URL LinkedIn | Crédits phone chers → discipline champ-vide ; ~35 % de non-match |
| **SDR Agent IA** (extension Chrome + API) | 🟡 Construit, déploiement à finaliser | Brief profil (`/api/brief`), message par canal (`/api/pitch`), objections, battle cards — dans la sidebar HubSpot | Pas encore déployé partout (TODO Vercel + extension) — cette demande est un argument de plus pour finir |
| **Lemlist** | ✅ Câblé (MCP + intégration) | Séquences multicanal programmatiques (invite → message → follow-up) — le cas « volume » | Envoi LinkedIn auto = contraire ToS quel que soit l'habillage ; actions `add_leads`/`send` irréversibles → toujours preview + approbation |
| **La Growth Machine** | 🟡 Utilisée par le passé (d'où les 196k `lgm_linkedinurl`) | Même famille que Lemlist | Idem ToS ; doublonnerait Lemlist |
| **PhantomBuster** | ✅ Compte actif, scripté | Scraping LinkedIn (listes, activité) — option A du plan #170 | Contraire ToS (cookie de session) ; cookie expire → échecs silencieux |
| **Sales Navigator ↔ HubSpot** | ❌ Non souscrit (Advanced ~130-150 €/mois/siège) | Activité LinkedIn affichée dans la fiche contact — l'option 100 % conforme | Coût récurrent ; moins granulaire qu'un scrape |
| **Claude (Pocket / API)** | ✅ Opérationnel | Orchestration : brief, draft 1:1, logging HubSpot en un échange | L'envoi LinkedIn reste hors périmètre (volontairement) |

**Point important sur sa suggestion de séquenceur** : il a raison sur l'existence de ces outils (on les a), mais « automate the first outreach more naturally than Claude » mérite d'être décodé : *naturally* = pacing pseudo-humain = **moindre risque de détection**. La conformité ToS, elle, ne change pas : tout envoi automatisé (invitation comprise) viole les CGU LinkedIn, séquenceur ou pas. C'est donc une **décision d'acceptation de risque au niveau équipe** (comptes par SDR, plafonds de volume, acceptation écrite) — exactement l'arbitrage PhantomBuster vs Sales Nav déjà posé à la manageuse dans #170 — pas un setup personnel.

---

## 5. Les deux cas d'usage à ne pas confondre

Le désaccord apparent entre « son » approche (séquenceur) et « notre » flux (Claude 1:1) disparaît quand on sépare les cas :

| | **Cas A — Volume programmatique** | **Cas B — Profil high-intent repéré à la main** |
|---|---|---|
| Déclencheur | Liste construite (segment, event, scraping) | « Je viens de voir un profil intéressant » — le sujet exact de sa question |
| Volume | 50-500 contacts | 1-5 par jour |
| Personnalisation | Template + variables | Vraiment individuelle (son post, son actu, sa boîte) |
| Bon outil | **Lemlist** (séquence invite → message → follow) | **Claude** : brief + draft 1:1 + logging |
| Envoi | Automatisé par le séquenceur = risque ToS assumé en connaissance de cause, décision d'équipe | Copier-coller humain (10 s) — zéro risque |
| Téléphone | FullEnrich en batch sur le segment (≤100/batch) | FullEnrich `enrich-one` au fil de l'eau |
| Logging | Intégration Lemlist ↔ HubSpot native | Claude : contact + activité + contenu en un échange |

**Le pont entre les deux** (la vraie bonne idée à lui proposer) : Claude rédige l'icebreaker personnalisé et l'injecte comme **variable custom dans la séquence Lemlist**. On garde l'automatisation du cas A avec la personnalisation du cas B. C'est le meilleur des deux mondes et ça réutilise 100 % de l'existant.

---

## 6. Conformité — synthèse des lignes rouges

1. **Scraper le téléphone sur LinkedIn** : ❌ interdit (ToS) + risque RGPD (collecte sans base légale). Inutile de toute façon : FullEnrich fait mieux, légalement.
2. **Envoi automatisé de messages/invitations LinkedIn** : ❌ contraire aux ToS, quel que soit l'outil. Si l'équipe choisit d'assumer ce risque via séquenceur : décision explicite de la manageuse, comptes individuels, plafonds (~60-100 actions/j/compte), heures de bureau, kill switch — jamais un bricolage individuel.
3. **Lire un profil pour préparer un message** : ✅ acceptable (donnée professionnelle publique, intérêt légitime B2B), à condition de **ne rien persister** de l'activité du prospect dans le CRM (règle §3).
4. **Enrichissement via data providers** (FullEnrich) : ✅ voie conforme standard du marché B2B.
5. **Logging HubSpot de notre propre outreach** : ✅ aucun problème — c'est même une bonne pratique de gouvernance.

---

## 7. Architecture cible recommandée (flux combiné)

```
                    ┌─ Cas B (high-intent, 1-5/j) ─────────────────────────┐
Profil repéré ──▶ URL LinkedIn ──▶ Claude/SDR Agent : brief (/api/brief)   │
                                   ├─▶ FullEnrich enrich-one → mobilephone │
                                   ├─▶ Draft message (/api/pitch)          │
                                   │      └─▶ HUMAIN : copier-coller,      │
                                   │           clic envoyer (10 s)         │
                                   └─▶ HubSpot : contact (check existant)  │
                                        + activité « LinkedIn message »    │
                                        + contenu du message               │
                    └──────────────────────────────────────────────────────┘

                    ┌─ Cas A (volume) ─────────────────────────────────────┐
Segment HubSpot ──▶ FullEnrich batch (≤100) ──▶ Lemlist séquence           │
                    (phones sur champs vides)   (icebreaker Claude injecté │
                                                 en variable custom)       │
                    Décision ToS envoi auto = manageuse, plafonds, comptes │
                    individuels                                            │
                    └──────────────────────────────────────────────────────┘
```

Ce qui manque pour que ça tourne : **finaliser le déploiement du SDR Agent** (Vercel + extension — quelques heures), et **une décision d'équipe** sur l'envoi auto (cas A). Tout le reste existe.

---

## 8. Chiffrage du gain

Hypothèses prudentes, base « profil high-intent » (cas B) :

| Poste | Manuel | Flux cible | Gain |
|---|---|---|---|
| Lecture profil + notes | 3-5 min | brief généré, lu en ~1 min | 2-4 min |
| Recherche téléphone | 2-5 min (souvent vaine) | 0 (FullEnrich async) | 2-5 min |
| Rédaction message | 5-10 min | relecture/ajustement draft ~1 min | 4-9 min |
| Logging HubSpot | 3-5 min | 0 (automatique) | 3-5 min |
| **Total/profil** | **~15-25 min** | **~2-3 min** | **~12-22 min** |

À 5 profils/jour/personne : **~1h15-1h50/jour récupérées**. Pour mémoire, le playbook Sales Ops chiffre déjà la prep de call à 8 h/SDR/semaine récupérables (funnel de référence : 93 calls → 28 conversations → 7 deals → 1 client ≈ 9 000 €) — ce workflow-ci est le cousin « outbound LinkedIn » du même gisement.

Coûts marginaux : crédits FullEnrich phone (uniquement champs vides), ~0,02-0,05 €/génération Claude. Aucun nouvel abonnement nécessaire pour le cas B.

---

## 9. Signal organisationnel (le point le plus important du rapport)

Le collègue écrit : *« I was just looking into something for the SDR outreach using Claude, HubSpot and LinkedIn too »*. Croisé avec l'issue #170 (plan prep-de-call SDR, idée de la manageuse), cela fait **trois initiatives qui convergent sur le même problème** :

1. Le plan prep-de-call #170 (Gaspard + manageuse) — brief avant call, un-par-un, décision LinkedIn pendante ;
2. Le projet SDR Agent IA (Gaspard) — extension + API, 70 % construit ;
3. La démarche du collègue TA — outreach LinkedIn outillé, exploration séquenceurs.

**Risques si rien n'est fait** : deux flux parallèles, conventions de logging divergentes (sa question « quoi logguer » le montre : rien n'est encore partagé), double exposition ToS non arbitrée, et du temps de build dupliqué.

**Recommandation** : un sync de 30 min à trois (Gaspard + collègue + manageuse) avec cet ordre du jour :
1. Démo du pipeline FullEnrich (lever sa fausse croyance sur le téléphone) ;
2. Convention de logging commune (§3 — à adopter telle quelle) ;
3. Arbitrage unique envoi auto LinkedIn (séquenceur/PhantomBuster/Sales Nav) — une seule décision pour toute l'équipe, portée par la manageuse ;
4. Rattacher son besoin au SDR Agent (déployer l'extension pour lui aussi) plutôt qu'un outil de plus.

---

## 10. Plan d'action

| # | Action | Qui | Quand | Effort |
|---|---|---|---|---|
| 1 | Envoyer la réponse au collègue (drafts déjà postés dans l'issue) + proposer le sync | Gaspard | Cette semaine | 10 min |
| 2 | Test grandeur nature du cas B sur 2-3 profils réels qu'il fournit (brief + FullEnrich + draft + logging) — preuve par l'exemple | Pocket (enrichissement gaté `approved`) | Cette semaine | 1 h |
| 3 | Finaliser le déploiement SDR Agent (Vercel + extension) — débloque §1 et §3 du workflow pour toute l'équipe | Gaspard (+ Forge) | S30 | ½-1 j |
| 4 | Sync à trois : convention de logging + arbitrage envoi auto | Gaspard + collègue + manageuse | S30 | 30 min |
| 5 | Si cas A validé : POC icebreaker Claude → variable custom Lemlist sur une mini-séquence (10 leads) | Gaspard + Pocket | S31 | ½ j |
| 6 | Consolider avec la Phase 0 du plan #170 (même infrastructure de brief, même règles) | — | continu | — |

---

*Rapport généré le 2026-07-16 par Claude Pocket. Données vérifiées : audits HubSpot 2026-07-10 & 2026-07-16 (278k contacts, couverture LinkedIn ~71 %, phone ~20 %), vault EMAsphere (FullEnrich 2026-06-16, playbook Lead-Enrichment, SDR-Agent-IA), plan V2 issue #170.*

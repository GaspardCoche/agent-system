# Retour à la manageuse — options « Claude → HubSpot » pour le flux LinkedIn TA

> Contexte : issue #171, 2026-07-16. La manageuse propose LinkedHelper/Waalaxy pour les séquences LinkedIn, et deux architectures pour l'ingestion des contacts par Claude : (1) accès HubSpot partiel avec champs dédiés + workflow de nettoyage, ou (2) Google Sheet intermédiaire uploadé chaque jour par JC, avec tâche « Call back in 3 days » automatique. Ce document contient l'analyse pour Gaspard puis la réponse prête à envoyer (en anglais).

---

## 1. Analyse (pour Gaspard)

### Sur LinkedHelper / Waalaxy

- **« Caps the amount per day to stay within the LinkedIn ToS » est une idée fausse** (fréquente, entretenue par le marketing de ces outils) : les plafonds réduisent le **risque de détection**, pas l'exposition ToS. Toute automatisation d'invitations/messages viole les ToS LinkedIn, quel que soit l'outil et quel que soit le volume. À corriger avec tact : elle a raison sur l'outil-catégorie, pas sur le cadre juridique.
- Réalité 2026 (playbook vault `LinkedIn-Outreach.md`, MAJ 2026-07-07) : **~100 invitations/semaine = plafond dur tous tiers** (Sales Nav inclus), <80/sem sans Sales Nav ; acceptation <30 % ou rythme non humain → « feature-restricted state » (bouton invitation retiré 1-3 semaines) ; cas sévères → restriction totale + vérification d'identité.
- **La catégorie d'outil est déjà dans notre stack** : Lemlist (câblé, fait du multicanal LinkedIn), PhantomBuster (payé, €56/mois), La Growth Machine utilisée avant (196k `lgm_linkedinurl` dans HubSpot). Waalaxy a déjà été évalué dans le playbook (« UI plus simple, limites moins flexibles ») et écarté au profit de PhantomBuster. Pas besoin d'acheter un 3e outil — besoin d'une **décision d'acceptation de risque au niveau équipe** (comptes par SDR, caps, qui porte le risque de restriction de compte).

### Option 1 — accès HubSpot partiel pour Claude

- **Faisable, et c'est en substance ce que l'agent-system fait déjà** : toute écriture HubSpot passe par un preview posté en commentaire + label `approved` avant exécution, et le garde-fou dur n° 1 est « ne jamais écraser un champ rempli ».
- **Nuance technique à lui donner** : les tokens HubSpot (private app) se scopent **par objet** (`crm.objects.contacts.write`), **pas par champ**. Le « set of fields » n'est donc pas imposable par l'API — il s'impose par convention : propriétés dédiées (groupe « LinkedIn intake », préfixe type `li_`), règle non-destructive, gate humain, puis workflow HubSpot de normalisation. C'est exactement sa proposition, avec un gate humain en plus.
- **Gros avantage vs option 2 : le dédoublonnage.** ~71 % de nos 278k contacts ont déjà une URL LinkedIn (6 propriétés à coalescer) → Claude cherche avant de créer. 

### Option 2 — Google Sheet + upload quotidien par JC

- Fonctionne, zéro accès en écriture, piste d'audit naturelle. Mais trois coûts réels :
  1. **Doublons** : l'import HubSpot déduplique les contacts **par email uniquement** ; un contact sourcé LinkedIn n'a souvent **pas d'email au moment de l'intake** → chaque upload peut créer des doublons. Le check-before-create doit donc exister quelque part — et c'est Claude qui le fait le mieux (URL LinkedIn vs les 6 propriétés).
  2. **JC = point de défaillance quotidien** + latence jusqu'à 24 h (congés, oublis).
  3. **Double manipulation FullEnrich** : FullEnrich écrit nativement dans `mobilephone` HubSpot (non destructif, réassociation par `hubspot_contact_id` en champ custom) ; passer par le Sheet casse ce câblage.
- **FullEnrich, 5/jour** : volume trivial (~150/mois), mobile vérifié dans ~60-65 % des cas, mobile-only by design. Discipline crédits : ne demander les phones que si `mobilephone` est vide.

### Recommandation

**Option 2 en pilote 2 semaines** (rapide, zéro confiance requise) mais avec **le dédoublonnage fait par Claude avant que le Sheet parte chez JC** (colonne `existing_hubspot_id` : update vs create). En parallèle, définir le set de champs dédiés. Puis **basculer l'écriture finale vers le flux Claude gaté** (option 1) une fois la convention validée — le gate `approved` donne le même contrôle humain que l'upload de JC, sans la latence ni le risque de doublons. La tâche « Call back in 3 days » vient d'un **workflow HubSpot déclenché sur une propriété d'intake** → fonctionne dans les deux options, aucune raison d'en faire un critère de choix.

---

## 2. Réponse prête à envoyer (anglais)

> Thanks — both options are workable, and the good news is we're closer than you think: most of the plumbing already exists. My take, option by option, plus one correction on the sequencing tools.
>
> **On LinkedHelper/Waalaxy first, one important nuance:** daily caps lower the *detection* risk, but they don't make automation ToS-compliant — auto-sending invites/messages breaks LinkedIn's ToS at any volume, whatever the tool claims. The real 2026 numbers: ~100 invites/week is a hard cap on all tiers (Sales Nav included), and accounts with <30% acceptance or non-human pacing get feature-restricted (invite button removed for 1–3 weeks; severe cases require ID verification). Also, we already own this tool category: **Lemlist** (wired in, does LinkedIn steps), **PhantomBuster** (paid), and we've used La Growth Machine before. So rather than adding a third tool, the decision needed is an explicit **team-level risk acceptance** (which tool, per-SDR accounts, volume caps, who owns the account-restriction risk) — happy to prep that comparison if useful.
>
> **Option 1 (partial HubSpot access for Claude): feasible, and largely already built.** One technical nuance: HubSpot app tokens are scoped per *object*, not per *field* — so the "set of fields" isn't enforceable at the API level. But we get the same data-quality guarantee by convention, and it's already running in our agent setup: (a) dedicated intake properties (own property group, e.g. `li_` prefix) so nothing touches your core fields, (b) a hard rule of never overwriting a filled field, (c) **every write is previewed and requires a human approval label before executing** — so a human still signs off on every batch, same control as JC's upload, without the delay, and (d) your HubSpot cleanup workflow normalizes and assigns the "Call back in 3 days" task. Bonus: ~71% of our 278k contacts already have a LinkedIn URL, so Claude checks for an existing record before creating anything.
>
> **Option 2 (Google Sheet + daily upload by JC): works, but three hidden costs.** (1) *Duplicates*: HubSpot import dedupes contacts by **email only**, and LinkedIn-sourced contacts usually have no email at intake — so daily uploads will create dupes unless someone dedupes first. (2) JC becomes a daily single point of failure, with up to 24h latency. (3) FullEnrich can write the phone straight into HubSpot's `mobilephone` field (non-destructively, keyed to the contact ID) — routing through a sheet breaks that and means double handling. On your FullEnrich question: yes, that's exactly its job — verified **mobile** numbers via waterfall enrichment from the LinkedIn URL, ~60–65% hit rate in our experience, and 5/day is a trivial volume. We only request phones when the field is empty (phone credits are the expensive ones).
>
> **My suggestion — start with 2, converge to 1:** run Option 2 as a two-week pilot (fastest to start, zero access needed), **but with Claude doing the dedupe before the sheet goes to JC** (an `existing_hubspot_id` column: update vs. create). Meanwhile we define the dedicated field set together. Once the convention is validated, switch the final write to the gated Claude flow — human approval stays, latency and dupes go. Note the "Call back in 3 days" task should be a HubSpot workflow triggered on an intake property either way, so it works identically in both options.
>
> Since JC, you and I are clearly circling the same problem (this is the third initiative on SDR outreach this month), can we do a 30-min sync? I'd rather we ship one flow than three.

---

## 3. Sources

- Vault `03-Playbooks/01-Outbound-Leadgen/LinkedIn-Outreach.md` (MAJ 2026-07-07) — plafonds LinkedIn 2026, feature-restricted state, comparatif Waalaxy/Expandi/Lemlist/PhantomBuster.
- Vault `04-Reference/07-Growth-CRM/HubSpot-Data-Management.md` — règles d'import (dédup contacts par email uniquement ; records créés par API non dédupliqués).
- Vault `02-Stack/02-Growth-Tools/FullEnrich.md` — flux bulk v2, mobile-only, `custom.hubspot_contact_id`, discipline crédits phones.
- `pocket-knowledge/crm.md` — 278k contacts, ~71 % avec URL LinkedIn (6 propriétés), garde-fous d'écriture, projet SDR Agent IA, décisions #170.
- `docs/runner-guardrails.md` — gate preview + `approved`, règle non-destructive.

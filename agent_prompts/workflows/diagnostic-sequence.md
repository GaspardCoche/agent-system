# Workflow — Diagnostic de séquence HubSpot

**Type :** LECTURE SEULE. Tu diagnostiques pourquoi une séquence se comporte d'une certaine façon et tu rends une explication claire + une réponse au demandeur.

## Objectif
Répondre aux questions du type « pourquoi ce contact n'apparaît pas dans la séquence ? », « pourquoi le tracking est cassé ? », « pourquoi il n'a pas reçu l'email suivant ? ». Tu enquêtes côté HubSpot **en lecture** et tu expliques.

## Entrée
Le champ `Demande` contient la question + souvent un lien séquence (`/sequences/4550859/sequence/<id>`) et/ou un lien contact.

## Étapes
1. **Garde-fous** : `cat docs/runner-guardrails.md`.
2. **Lire la note de référence** si dispo : `docs/vault/.../HubSpot-Sequences-Meeting-Attribution.md` (ou vault `03-Playbooks/02-Sales-CRM/`) — règles d'inscription/désinscription et **fenêtre d'attribution meeting 7 j post-unenroll**.
3. **Lire la séquence et les enrollments** (HubSpot MCP, lecture) :
   - `hubspot-list-workflows` / `hubspot-get-workflow` pour le contexte automation lié.
   - `hubspot-batch-read-objects` + `hubspot-list-associations` sur le(s) contact(s) cité(s) : statut d'enrollment, `hs_sequences_*`, dernières activités email (open/click/bounce/reply), meetings.
   - `hubspot-get-engagement` si un engagement précis est en cause.
4. **Diagnostiquer** parmi les causes fréquentes :
   - Contact **déjà inscrit** ailleurs / **désinscrit** (reply, meeting booked, bounce, manual unenroll).
   - **Critères d'inscription** non remplis (propriété manquante, owner, filtre).
   - **Tracking** : email non ouvert ≠ non délivré ; pixel bloqué ; domaine d'envoi.
   - **Attribution meeting** : meeting pris dans la **fenêtre 7 j** après désinscription → compte quand même.
5. **Rédiger l'explication** : cause probable + preuve (ce que tu as lu) + action recommandée.

## Garde-fous spécifiques
- **Zéro écriture / zéro modification de séquence.** Tu expliques et recommandes, tu ne touches à rien.
- Distinguer clairement **fait observé** (« le contact est unenrolled depuis le 12/06 ») de **hypothèse** (« probablement à cause d'un reply »).

## Sortie (commentaire d'issue)
```
## 🔎 Diagnostic séquence

**Cause :** <la cause identifiée>
**Preuves :** <ce que tu as lu dans HubSpot — ids, statuts, dates>
**Recommandation :** <action concrète>

---
**💬 Réponse prête (au collègue) :**
> <message court à copier, même langue que la question>
```
Puis `/tmp/agent_result.json` (`status: complete`, `retrospective`).

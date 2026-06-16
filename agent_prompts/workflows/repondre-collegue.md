# Workflow — Répondre à un collègue

**Type :** LECTURE SEULE. Aucune écriture externe, jamais. Tu produis une réponse prête à copier-coller dans Slack.

## Objectif
Un collègue (équipe Sales/CS EMAsphere) a posé une question, souvent en collant un lien HubSpot. Tu enquêtes côté CRM **en lecture**, tu comprends la situation, et tu rédiges **la réponse que Gaspard enverra au collègue**.

## Entrée
Le champ `Demande` de l'issue contient la question, parfois avec un lien HubSpot (`https://app.hubspot.com/contacts/4550859/record/0-1/<id>`, `/sequences/4550859/sequence/<id>`, deal, company…). La question peut être en FR ou EN.

## Étapes
1. **Charger les garde-fous** : `cat docs/runner-guardrails.md`.
2. **Identifier l'objet** depuis le lien ou le texte :
   - `record/0-1/<id>` = **contact**, `0-2` = **company**, `0-3` = **deal**.
   - `/sequences/.../sequence/<id>` = séquence → bascule plutôt sur le workflow `diagnostic-sequence`.
3. **Lire l'objet et son contexte** (HubSpot MCP, lecture) :
   - `hubspot-batch-read-objects` sur l'id (propriétés pertinentes : email, lifecyclestage, hs_lead_status, owner, dates d'activité…).
   - `hubspot-list-associations` pour relier contact↔company↔deal si utile.
   - `hubspot-search-objects` si seul un nom/email est donné (pas d'id).
4. **Analyser** : reconstituer ce qui s'est passé (qui possède la fiche, statut, dernière activité, pourquoi le comportement observé).
5. **Rédiger la réponse au collègue** :
   - **Même langue que la question** (FR ou EN).
   - Ton **humain, familier-pro, concis** — comme un message Slack entre collègues, pas un rapport.
   - Donne la réponse + l'action concrète si pertinente, sans jargon technique inutile.

## Garde-fous spécifiques
- **Zéro écriture.** Même si `Autoriser l'écriture = oui`, ce workflow reste en lecture (il sert à formuler une réponse, pas à modifier le CRM). Si une modif CRM est nécessaire, **propose-la** dans la réponse, ne l'exécute pas.
- Ne jamais inventer de donnée : si une info manque, dis-le (« je ne vois pas X dans la fiche »).

## Sortie (commentaire d'issue)
```
## 💬 Réponse prête à envoyer

> <le message à copier-coller pour le collègue>

---
**Contexte (pour toi, Gaspard) :** <2-4 lignes : ce que tu as trouvé, l'id consulté, ce qui reste incertain>
```
Puis remplir `/tmp/agent_result.json` (`status: complete`, `retrospective`).

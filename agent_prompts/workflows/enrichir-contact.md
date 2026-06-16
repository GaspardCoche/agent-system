# Workflow — Enrichir un (des) contact(s)

**Type :** LECTURE par défaut · ÉCRITURE possible (FullEnrich → HubSpot) **seulement si** `Autoriser l'écriture = oui` + conditions + label `approved`. Agent porteur : **Aria**.

## Objectif
Compléter des contacts HubSpot incomplets (email pro, téléphone mobile, LinkedIn, taille, industrie…) via FullEnrich, **sans jamais écraser une donnée existante**, en respectant l'ICP et le mapping EMAsphere.

## Entrée
Le champ `Demande` désigne la cible : un email/nom, une liste, ou un segment HubSpot (« les contacts sans téléphone de la company X »). Les `Conditions d'écriture` bornent ce qui peut être modifié.

## Étapes
1. **Garde-fous** : `cat docs/runner-guardrails.md` + `cat ~/crm-context/icp_and_data_rules.md` si présent (sinon vault).
2. **Lire l'existant** (HubSpot, lecture) : `hubspot-search-objects` / `hubspot-batch-read-objects` → repérer **les champs VIDES** à compléter (GF #1 : ne jamais écraser un champ rempli).
3. **Enrichir via FullEnrich** (Python direct, API v2) :
   - Par lots de **≤ 100 contacts** (GF #6).
   - Téléphone : ne garder que le **mobile** (politique FullEnrich vault).
4. **Mapper vers HubSpot** :
   - Industry → `industry_emalist` sur **Companies** (format « Catégorie - Sous-catégorie », mapping IndustryDB). ⚠️ ne pas écrire si nom de champ non confirmé en prod.
   - `numemployees` = range ; nombre brut → `linkedin_employee_count`.
   - `country` = enum strict (sinon `country_code`). `domain` = extrait de l'email (pas de propriété contact).
5. **Preview obligatoire** (commentaire) : tableau des updates proposés (contact, champ, ancienne valeur=vide, nouvelle valeur). **Attendre `approved`.**
6. **Exécuter** (si `approved`) : `hubspot-batch-update-objects` **non destructif** (champs vides uniquement). Traiter **207 = succès partiel** (GF #7), logguer les `results`.

## Garde-fous spécifiques
- Jamais écraser un champ rempli (revérifier juste avant l'update).
- Respecter strictement les `Conditions d'écriture` (ex : « seulement le téléphone »).
- Hors ICP (CA < 10M ou > 500M) → signaler, ne pas forcer.

## Sortie (commentaire d'issue)
```
## 🔍 Preview enrichissement (N contacts)
| Contact | Champ | Nouvelle valeur |
|---|---|---|
| … | mobilephone | +32… |

**Tape ✅ Approuver pour exécuter** (sinon DRY_RUN).
```
Après exécution : commentaire récap (X mis à jour, Y inchangés, Z échecs) + `/tmp/agent_result.json`.

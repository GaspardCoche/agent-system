# Audit des propriétés HubSpot — Contacts & Companies

**Date** : 2026-07-10 · **Portée** : base entière (lecture seule) · **Compte** : 4550859
**Volumes** : 276 635 contacts · 155 178 companies

---

## 1. Inventaire

| Objet | Propriétés totales | Custom | HubSpot standard |
|---|---|---|---|
| Contacts | 779 | 364 | 415 |
| Companies | 503 | 239 | 264 |

Principaux groupes custom **contacts** : contactinformation (116), glue_addresses (36), conversioninformation (29), paperform_fields (28), zym (18), phantombuster (18), lead_ads (14), bnp_client_information (13), clearoutinformation (12).

Principaux groupes custom **companies** : companyinformation (74), glue_addresses (33), customer_information (22), conversioninformation (17), implementation_information (15), phantombuster (13), lemlist (12), koalify_duplicates (5).

⚠️ **~150+ propriétés contacts sont des champs one-shot** (quiz reporting/cash FR+NL, paperform, événements EMAclub/BNP breakfast, candidatures RH) — bruit important dans l'UI et les exports.

## 2. Taux de complétion — Contacts (sur 276 635)

### Solide (>70 %)
| Propriété | Rempli | % |
|---|---|---|
| lifecyclestage | 276 618 | 100 % |
| hs_analytics_source | 276 635 | 100 % |
| email | 271 731 | 98,2 % |
| firstname / lastname | ~271 500 | 98,1 % |
| hubspot_owner_id | 270 096 | 97,6 % |
| company (texte) | 251 539 | 90,9 % |
| hs_language | 251 116 | 90,8 % |
| department | 247 514 | 89,5 % |
| jobtitle | 243 002 | 87,8 % |
| level | 224 747 | 81,2 % |
| polite_form__gender_based_ | 207 880 | 75,1 % |
| lemlistlinkedinurl | 198 033 | 71,6 % |
| lgm_linkedinurl | 197 493 | 71,4 % |

### Faible (levier d'enrichissement ou à trancher)
| Propriété | Rempli | % | Commentaire |
|---|---|---|---|
| master_language | 126 286 | 45,7 % | doublon apparent de hs_language (90,8 %) |
| country | 101 354 | 36,6 % | la géo fiable est côté company (87 %) |
| phone | 56 829 | 20,5 % | levier FullEnrich classique |
| mobilephone | 39 762 | 14,4 % | levier FullEnrich classique |
| co_status (Clearout) | 18 641 | 6,7 % | vérif email très partielle |
| industry (contact) | 5 849 | 2,1 % | résidu — la règle = industrie sur company |
| numemployees | 2 778 | 1,0 % | quasi mort côté contact |
| linkedin_employee_count | 2 424 | 0,9 % | idem |
| lead_source_category | 2 189 | 0,8 % | récent ou abandonné ? |
| turnover__company_ / role_segment / segment | ≤135 | ~0 % | morts |

**Constat structurel** : `internal_industry` **n'existe plus sur les contacts** (référencé dans les playbooks/guardrails). La segmentation industrie ne vit que sur companies (`industry_emalist`). Le sizing (employés, CA) est lui aussi de facto un attribut company.

## 3. Taux de complétion — Companies (sur 155 178)

### Solide (>70 %)
| Propriété | Rempli | % |
|---|---|---|
| lifecyclestage | 155 176 | 100 % |
| name | 153 331 | 98,8 % |
| hubspot_owner_id | 139 512 | 89,9 % |
| website / domain | ~139 000 | 89,5 % |
| country | 135 307 | 87,2 % |
| country_dropdown | 131 471 | 84,7 % |
| city | 120 006 | 77,3 % |
| national_administrative_division__nad_ | 116 063 | 74,8 % |
| industry_emalist | 115 432 | 74,4 % |

### Moyen (40–70 %)
| Propriété | % | Commentaire |
|---|---|---|
| size_category | 68,1 % | |
| linkedin_company_page | 65,5 % | |
| numberofemployees / employees | 64,4 / 64,2 % | ~55 800 companies sans effectif |
| industry (standard HubSpot) | 62,7 % | concurrent de industry_emalist |
| type_of_icp | 57,6 % | |
| turnover | 50,1 % | 3 props CA en parallèle : turnover, |
| turnover_category | 46,6 % | annualrevenue, turnover_category |
| annualrevenue | 46,4 % | |
| segment | 43,8 % | |

### Faible — dont critères ICP clés
| Propriété | Rempli | % | Commentaire |
|---|---|---|---|
| **multiple_legal_entities_** | 27 319 | **17,6 %** | critère ICP n°1 (multi-entités) ! |
| vat | 12 852 | 8,3 % | clé pour enrichir via registres BCE/Pappers |
| **number_of_legal_entities** | 12 363 | **8,0 %** | idem multi-entités |
| lemlistindustry | 1 577 | 1,0 % | enrichissement Lemlist company inutilisé |
| total_arr | 717 | 0,5 % | |
| employees_range / count_of_employees_on_linkedin / potential | ≤223 | ~0,1 % | pipeline PhantomBuster→company jamais déployé |

## 4. Vitalité des intégrations

| Intégration | Signal mesuré | Verdict |
|---|---|---|
| **Lemlist (contacts)** | lemlistlinkedinurl 71,6 % | ✅ vivante, principale source LinkedIn |
| **Lemlist (companies)** | lemlist_linkedin_url 2,4 % | ❌ quasi inutilisée côté company |
| **LGM** | lgm_linkedinurl 71,4 % | ✅ historique riche (redondant avec Lemlist ?) |
| **PhantomBuster** | 5,7 % contacts / 5,6 % companies créés | ⚠️ usage ponctuel, pipeline effectifs jamais scalé |
| **Zym (intent)** | data_source 1,5 % / 1,1 % | ❌ morte (confirmé playbook) |
| **Aircall** | 3 820 contacts appelés (1,4 %) | ✅ normale (seuls les appelés) |
| **Clearout** | co_status 6,7 % | ⚠️ vérif email très partielle |
| **Koalify (dédup)** | 66 % companies scannées | ✅ active — voir §5 |
| **Bounces HubSpot** | hs_email_hard_bounce_reason : 0 | ℹ️ l'emailing sortant ne passe pas par HubSpot |

## 5. Doublons (Koalify)

- 102 656 companies scannées (66,2 %)
- **4 957 companies avec ≥1 doublon détecté**
- **2 419 marquées "primary duplicate"** → backlog de merge quantifié (merge = UI uniquement, irréversible)

## 6. Potentiel d'enrichissement (estimations)

| Cible | Manquants | Voie |
|---|---|---|
| phone/mobile contacts | ~220 000 / ~237 000 | FullEnrich (waterfall) sur segments prioritaires — 71,6 % ont le LinkedIn URL requis |
| industry_emalist companies | ~39 700 | Lemlist company enrich / IndustryDB via domaine (89,5 % ont un domaine) |
| effectifs companies | ~55 300 | LinkedIn (PhantomBuster/Lemlist) → count_of_employees_on_linkedin |
| CA companies | ~77 500 | registres officiels (BCE/Pappers) — mais VAT seulement 8,3 % rempli, à enrichir d'abord via nom+pays |
| multi-entités | ~127 900 | BCE/Pappers (liens capitalistiques) — critère ICP le plus discriminant et le plus vide |
| emails vérifiés | ~253 000 non vérifiés | Clearout/bulk avant toute campagne |

## 7. Limites de cet audit

- **Base entière** : les taux sur les segments actifs (lead/MQL/SQL, listes campagne) peuvent être très différents — à mesurer au prochain tour si confirmé.
- **Deals non audités** : le token Pocket n'a pas le scope deals (403).
- Une propriété « remplie » n'est pas une propriété « juste » (valeurs obsolètes non détectables par ce comptage).

---
*Généré par Claude Pocket — issue #163 · lecture seule, aucune écriture HubSpot.*

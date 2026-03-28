---
title: "HubSpot -- Workflows & Automatisations"
id: crm-hubspot-workflows
type: crm
tags: [crm, hubspot, workflows, automation, sequences]
agents: [aria, ralph]
updated: 2026-03-28
---

# HubSpot -- Workflows & Automatisations

> [!info] Vue d'ensemble
> Les workflows HubSpot automatisent l'attribution, les transitions de lifecycle, et la qualite des donnees. Ils constituent le moteur operationnel entre l'import de leads et l'outreach commercial.

---

## Workflows d'Attribution par Hub Geographique

5 workflows gerent l'assignation automatique des contacts au bon SDR selon leur [[leadgen/geographic-hubs|hub geographique]].

### wf-france

| Parametre | Valeur |
|-----------|--------|
| **Trigger** | Contact cree ou propriete `country` modifiee |
| **Condition** | `country` = France |
| **Actions** | 1. Set `geographic_hub` = France |
| | 2. Set `hubspot_owner_id` = SDR France |
| | 3. Set `hs_language` = FR (si vide) |
| **Priorite** | 1 (execute en premier) |

### wf-be-south

| Parametre | Valeur |
|-----------|--------|
| **Trigger** | Contact cree ou propriete `country` modifiee |
| **Condition** | `country` = Belgium AND `nad` IN (Hainaut, Liege, Luxembourg, Namur, Brabant wallon) |
| **Condition alt** | `country` = Belgium AND `nad` = Bruxelles AND (`hs_language` = FR OR `hs_language` vide) |
| **Actions** | 1. Set `geographic_hub` = BE South |
| | 2. Set `hubspot_owner_id` = SDR BE-FR |
| | 3. Set `hs_language` = FR (si vide) |
| **Priorite** | 2 |

### wf-be-north

| Parametre | Valeur |
|-----------|--------|
| **Trigger** | Contact cree ou propriete `country` modifiee |
| **Condition** | `country` = Belgium AND `nad` IN (Antwerpen, Limburg, Oost-Vlaanderen, West-Vlaanderen, Vlaams-Brabant) |
| **Condition alt** | `country` = Belgium AND `nad` = Bruxelles AND `hs_language` = NL |
| **Actions** | 1. Set `geographic_hub` = BE North |
| | 2. Set `hubspot_owner_id` = SDR BE-NL |
| | 3. Set `hs_language` = NL (si vide) |
| **Priorite** | 3 |

### wf-uk

| Parametre | Valeur |
|-----------|--------|
| **Trigger** | Contact cree ou propriete `country` modifiee |
| **Condition** | `country` IN (United Kingdom, Ireland) |
| **Actions** | 1. Set `geographic_hub` = UK |
| | 2. Set `hubspot_owner_id` = SDR UK |
| | 3. Set `hs_language` = EN (si vide) |
| **Priorite** | 4 |

### wf-row

| Parametre | Valeur |
|-----------|--------|
| **Trigger** | Contact cree ou propriete `country` modifiee |
| **Condition** | **Fallback** -- aucun des workflows precedents n'a matche |
| **Actions** | 1. Set `geographic_hub` = ROW |
| | 2. Set `hubspot_owner_id` = SDR ROW |
| | 3. Set `hs_language` = EN (si vide) |
| **Priorite** | 5 (dernier) |

> [!warning] Ordre d'execution
> Les workflows sont mutuellement exclusifs grace aux conditions. Si un contact match plusieurs conditions (cas theoriquement impossible), la **priorite** determine lequel s'execute. Verifier regulierement qu'il n'y a pas de contacts sans hub assigne.

Voir [[leadgen/geographic-hubs]] pour la logique de resolution complete, notamment le cas Belgique.

---

## Workflows de Lifecycle

Ces workflows gerent les transitions automatiques entre les [[crm/hubspot-lifecycle|lifecycle stages]].

### wf-new-lead

| Parametre | Valeur |
|-----------|--------|
| **Trigger** | Contact cree (source: import API, fichier, formulaire) |
| **Conditions** | `lifecyclestage` est vide |
| **Actions** | 1. Set `lifecyclestage` = Lead |
| | 2. Set `hs_lead_status` = NEW |
| | 3. Executer workflow hub (wf-france/wf-be-south/etc.) |
| | 4. Calculer `lead_score_total` |
| | 5. Logger dans [[agents/dispatch-log]] |

### wf-mql

| Parametre | Valeur |
|-----------|--------|
| **Trigger** | Propriete `lead_score_total` modifiee |
| **Condition** | `lead_score_total` >= 60 AND `lifecyclestage` = Lead |
| **Actions** | 1. Set `lifecyclestage` = MQL |
| | 2. Set `hs_lead_status` = OPEN |
| | 3. Enrollment [[campaigns/lemlist-sequences|sequence Lemlist]] (par hub/langue) |
| | 4. Notifier marketing (email interne) |

> [!note] Seuil MQL
> Le seuil de 60 points est defini dans [[leadgen/lead-scoring]]. Il peut etre ajuste sans modifier le workflow -- seule la propriete `lead_score_total` est evaluee.

### wf-sql

| Parametre | Valeur |
|-----------|--------|
| **Trigger** | Propriete `lead_score_total` modifiee OU engagement detecte |
| **Condition** | `lead_score_total` >= 80 AND engagement (email ouvert OU clic OU reponse OU visite site) AND `lifecyclestage` = MQL |
| **Actions** | 1. Set `lifecyclestage` = SQL-SDR |
| | 2. Set `hs_lead_status` = OPEN |
| | 3. Notifier SDR (notification HubSpot + email) |
| | 4. Creer tache HubSpot "Premier contact sous 24h" |

### wf-nurture

| Parametre | Valeur |
|-----------|--------|
| **Trigger** | Date-based: 30 jours apres creation du contact |
| **Condition** | `lead_score_total` < 60 AND `lifecyclestage` = Lead AND `hs_lead_status` != UNQUALIFIED |
| **Actions** | 1. Enrollment sequence nurture (contenu educatif) |
| | 2. Set `hs_lead_status` = IN_PROGRESS |

---

## Workflows de Data Quality

Ces workflows maintiennent la proprete et la fiabilite des donnees CRM.

### wf-dedup -- Deduplication

| Parametre | Valeur |
|-----------|--------|
| **Trigger** | Schedule: chaque lundi 6h UTC |
| **Prerequis** | Operations Hub Professional (ou superieur) |
| **Logique** | 1. Identifier doublons par email (exact match) |
| | 2. Identifier doublons par nom + entreprise (fuzzy match) |
| | 3. Fusionner: conserver le contact avec le plus de donnees |
| | 4. Logger les fusions dans [[agents/dispatch-log]] |
| **Volume estime** | 2-5% des imports |

> [!tip] Operations Hub
> La deduplication automatique necessite **Operations Hub Professional**. Sans cet abonnement, la dedup doit etre manuelle ou via un script Python (voir [[tech/skills-registry]] pour un futur skill `hubspot_batch_dedup`).

### wf-bounce -- Gestion des Bounces

| Parametre | Valeur |
|-----------|--------|
| **Trigger** | Email bounce detecte (hard bounce) |
| **Actions** | 1. Set propriete `email_bounced` = true |
| | 2. Set `hs_lead_status` = ATTEMPTED_TO_CONTACT |
| | 3. Tenter re-enrichissement via [[leadgen/enrichment-fullenrich|FullEnrich]] |
| | 4. Si nouvel email trouve: mettre a jour et relancer scoring |
| | 5. Si aucun email: verifier si phone/LinkedIn disponible |
| | 6. Si aucun canal alternatif: disqualifier (score = 0) |

### wf-stale -- Contacts Inactifs

| Parametre | Valeur |
|-----------|--------|
| **Trigger** | Date-based: 90 jours sans activite |
| **Condition** | `lifecyclestage` IN (MQL, SQL-SDR) AND derniere activite > 90 jours |
| **Actions** | 1. Set `hs_lead_status` = UNQUALIFIED |
| | 2. Set `lifecyclestage` = Lead (retrogradation) |
| | 3. Logger raison: "Inactif 90 jours" |
| | 4. Retirer de toute sequence active |

> [!warning] Retrogradation
> La retrogradation est **irreversible automatiquement**. Un contact retrogade ne sera pas re-promu automatiquement. Il faudra un re-scoring manuel ou un nouvel engagement significatif pour le remonter. Voir [[crm/hubspot-lifecycle#Regles de Retrogradation]].

---

## Integration Lemlist

L'enrollment dans les [[campaigns/lemlist-sequences|sequences Lemlist]] se fait de deux manieres :

### Option 1 : Webhook HubSpot --> Lemlist

```
HubSpot Workflow Action: Webhook POST
URL: https://api.lemlist.com/api/campaigns/{campaignId}/leads
Headers: Authorization: Bearer {LEMLIST_API_KEY}
Body: {
  "email": "{{contact.email}}",
  "firstName": "{{contact.firstname}}",
  "lastName": "{{contact.lastname}}",
  "companyName": "{{contact.company}}",
  "variables": {
    "jobTitle": "{{contact.jobtitle}}",
    "hub": "{{contact.geographic_hub}}",
    "industry": "{{contact.industry}}"
  }
}
```

### Option 2 : API Directe (via Aria)

```python
# Appel depuis le workflow agent Aria
import requests

def enroll_lead_lemlist(contact, campaign_id):
    url = f"https://api.lemlist.com/api/campaigns/{campaign_id}/leads"
    payload = {
        "email": contact["email"],
        "firstName": contact["firstname"],
        "lastName": contact["lastname"],
        "companyName": contact["company"]
    }
    response = requests.post(url, json=payload, headers={
        "Authorization": f"Bearer {LEMLIST_API_KEY}"
    })
    return response.json()
```

> [!note] Decision en attente
> Le choix entre Lemlist et HubSpot Sequences n'est pas encore finalise. Voir [[campaigns/lemlist-sequences]] pour l'analyse comparative. L'integration ci-dessus est preparee pour Lemlist mais peut etre adaptee pour HubSpot Sequences.

---

## Backlog d'Optimisation

Ref: [[crm/hubspot-backlog]] Task 2 -- "Optimiser les workflows d'automatisation"

| Priorite | Amelioration | Status |
|----------|-------------|--------|
| P1 | Implementer wf-dedup avec Operations Hub | En attente souscription |
| P1 | Connecter wf-mql a Lemlist (ou HubSpot Sequences) | En attente decision outil |
| P2 | Ajouter scoring dynamique (re-scoring sur engagement) | Planifie |
| P2 | Workflow de reactivation BAD_TIMING (date-based) | Planifie |
| P3 | A/B test sur timing des sequences par hub | Backlog |
| P3 | Alertes Slack pour SQL-SDR (notification temps reel) | En attente SLACK_WEBHOOK_URL |

---

## Matrice de Dependances

| Workflow | Depend de | Declenche |
|----------|-----------|-----------|
| wf-new-lead | Import (API/fichier) | wf-france/wf-be-south/wf-be-north/wf-uk/wf-row |
| wf-france | wf-new-lead | -- |
| wf-be-south | wf-new-lead | -- |
| wf-be-north | wf-new-lead | -- |
| wf-uk | wf-new-lead | -- |
| wf-row | wf-new-lead | -- |
| wf-mql | Scoring (calcul score) | Enrollment Lemlist |
| wf-sql | wf-mql + engagement | Notification SDR |
| wf-nurture | wf-new-lead (30j) | Sequence nurture |
| wf-dedup | Schedule lundi | -- |
| wf-bounce | Email bounce event | Re-enrichissement |
| wf-stale | Schedule (90j check) | Retrogradation lifecycle |

---

## Liens

- [[crm/hubspot-lifecycle]] -- Lifecycle stages et transitions
- [[crm/hubspot-properties]] -- Proprietes HubSpot utilisees
- [[crm/hubspot-backlog]] -- Backlog d'optimisation
- [[crm/hubspot-api]] -- API HubSpot et configuration
- [[leadgen/geographic-hubs]] -- Hubs geographiques et routing
- [[leadgen/lead-scoring]] -- Regles de scoring
- [[leadgen/pipeline-overview]] -- Vue d'ensemble pipeline leadgen
- [[campaigns/lemlist-sequences]] -- Sequences outreach
- [[agents/aria-memory]] -- Agent Aria (CRM operations)
- [[agents/ralph-memory]] -- Agent Ralph (routing et dispatch)

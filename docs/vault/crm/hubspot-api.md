---
title: "HubSpot -- API & Integration"
id: crm-hubspot-api
type: crm
tags: [crm, hubspot, api, integration, batch]
agents: [aria, forge]
updated: 2026-03-28
---

# HubSpot -- API & Integration

Ce document decrit l'architecture d'integration avec l'API HubSpot, les endpoints utilises, les contraintes techniques, et le flux de donnees entre le pipeline lead-gen et le CRM.

---

## Authentification

### Private App Token

```
Authorization: Bearer {HUBSPOT_PRIVATE_APP_TOKEN}
```

| Parametre | Valeur |
|-----------|--------|
| Type | Private App |
| Methode | Bearer Token |
| Rotation | Manuelle (pas d'expiration auto) |
| Stockage | Variable d'environnement `HUBSPOT_PRIVATE_APP_TOKEN` |

### Scopes requis

| Scope | Lecture | Ecriture | Usage |
|-------|---------|----------|-------|
| `crm.objects.contacts.read` | Oui | -- | Recherche, deduplication |
| `crm.objects.contacts.write` | -- | Oui | Creation, mise a jour |
| `crm.objects.companies.read` | Oui | -- | Recherche par domaine |
| `crm.objects.companies.write` | -- | Oui | Creation de companies |

> [!warning] Securite
> Le token ne doit jamais etre commite dans le repository. Il est stocke dans le fichier `.env` local et dans les secrets GitHub Actions. Voir [[tech/code-repository]] pour le template de variables d'environnement.

---

## Endpoints principaux

### Contacts

| Operation | Methode | Endpoint | Usage |
|-----------|---------|----------|-------|
| Creer un contact | `POST` | `/crm/v3/objects/contacts` | Creation unitaire |
| Mettre a jour un contact | `PATCH` | `/crm/v3/objects/contacts/{contactId}` | Mise a jour par ID |
| Rechercher un contact | `POST` | `/crm/v3/objects/contacts/search` | Dedup par email |
| Batch create contacts | `POST` | `/crm/v3/objects/contacts/batch/create` | Creation en lot |
| Batch update contacts | `POST` | `/crm/v3/objects/contacts/batch/update` | Mise a jour en lot |

### Companies

| Operation | Methode | Endpoint | Usage |
|-----------|---------|----------|-------|
| Creer une company | `POST` | `/crm/v3/objects/companies` | Creation unitaire |
| Rechercher par domaine | `POST` | `/crm/v3/objects/companies/search` | Recherche par `domain` |

### Associations

| Operation | Methode | Endpoint | Usage |
|-----------|---------|----------|-------|
| Associer contact a company | `PUT` | `/crm/v4/objects/contacts/{contactId}/associations/companies/{companyId}` | Association apres creation |

---

## Rate Limits

> [!warning] Limites strictes
> Le non-respect des rate limits entraine un HTTP 429 et un blocage temporaire de l'app.

| Type d'app | Limite | Fenetre |
|------------|--------|---------|
| Private App | 100 requetes | 10 secondes |
| Batch | Max 100 items | Par requete |
| Search | 4 requetes | 1 seconde |
| Daily | 500 000 requetes | 24 heures |

### Implementation du rate limiter

```typescript
// Sliding window rate limiter
class HubSpotRateLimiter {
  private requests: number[] = [];
  private readonly maxRequests = 100;
  private readonly windowMs = 10_000; // 10 secondes

  async waitForSlot(): Promise<void> {
    const now = Date.now();
    this.requests = this.requests.filter(t => now - t < this.windowMs);

    if (this.requests.length >= this.maxRequests) {
      const oldestInWindow = this.requests[0];
      const waitTime = this.windowMs - (now - oldestInWindow) + 100; // +100ms marge
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }

    this.requests.push(Date.now());
  }
}
```

> [!tip] Architecture
> Le rate limiter est isole dans un module utilitaire (`utils/rate-limiter.ts`). Tous les appels API passent par ce module, garantissant le respect des limites meme en cas d'appels concurrents.

---

## Architecture Agent

### Couche API isolee

```
orchestrator.ts
  |
  +-- agents/hubspot.ts         (logique metier)
  |     |
  |     +-- api/hubspot-api.ts  (couche API pure)
  |           |
  |           +-- utils/rate-limiter.ts
  |           +-- utils/logger.ts
  |
  +-- types/hubspot.ts          (schemas & types)
```

> [!info] Principe de separation
> La couche API (`hubspot-api.ts`) ne contient aucune logique metier. Elle encapsule les appels HTTP bruts. L'agent (`hubspot.ts`) orchestre les operations (dedup, batch, association). Cette separation permet de tester unitairement chaque couche.

---

## Flux d'upload complet

Le flux d'upload des leads vers HubSpot suit ces etapes dans l'ordre :

```
1. Dedup check par email
   |
   +-- POST /contacts/search (filterGroups: email)
   |   Resultat: existingContacts[], newContacts[]
   |
2. Batch create (contacts nouveaux)
   |
   +-- POST /contacts/batch/create (chunks de 100)
   |   Resultat: createdContacts[] + errors[]
   |
3. Batch update (contacts existants)
   |
   +-- POST /contacts/batch/update (chunks de 100)
   |   Resultat: updatedContacts[] + errors[]
   |
4. Extraction des companies
   |
   +-- Extraction des domaines uniques depuis les contacts
   |
5. Company creation/search
   |
   +-- POST /companies/search (filterGroups: domain)
   |   Si inexistante: POST /companies (creation)
   |
6. Association Contact -> Company
   |
   +-- PUT /associations/contacts/{id}/companies/{id}
```

> [!warning] Ordre critique
> Les etapes doivent etre executees sequentiellement. L'etape 6 depend des IDs generes aux etapes 2, 3 et 5. Ne jamais paralleliser les etapes.

### Chunking des batchs

```typescript
function chunkArray<T>(array: T[], size: number = 100): T[][] {
  const chunks: T[][] = [];
  for (let i = 0; i < array.length; i += size) {
    chunks.push(array.slice(i, i + size));
  }
  return chunks;
}
```

Chaque chunk de 100 est envoye sequentiellement avec un `await` entre chaque appel, en respectant le rate limiter.

---

## Stubs API (6)

> [!info] Stubs a remplacer
> Ces fonctions sont actuellement des stubs dans le repository [[tech/code-repository]]. Elles compilent mais retournent des donnees mock. Remplacement prevu Q2 2026.

| # | Fonction | Signature | Statut |
|---|----------|-----------|--------|
| 1 | `searchContactByEmail` | `(email: string) => Promise<HubSpotContact \| null>` | Stub |
| 2 | `batchCreateContacts` | `(contacts: HubSpotContactSchema[]) => Promise<UploadResult>` | Stub |
| 3 | `batchUpdateContacts` | `(contacts: HubSpotContactSchema[]) => Promise<UploadResult>` | Stub |
| 4 | `searchCompanyByDomain` | `(domain: string) => Promise<HubSpotCompany \| null>` | Stub |
| 5 | `createCompany` | `(company: HubSpotCompanySchema) => Promise<HubSpotCompany>` | Stub |
| 6 | `associateContactToCompany` | `(contactId: string, companyId: string) => Promise<void>` | Stub |

---

## Types TypeScript

### HubSpotContactSchema (16 champs)

```typescript
const HubSpotContactSchema = z.object({
  email:                z.string().email(),
  firstname:            z.string(),
  lastname:             z.string(),
  jobtitle:             z.string().optional(),
  gender:               z.enum(["Mr", "Ms"]).optional(),
  hs_language:          z.string().optional(),        // ISO locale
  creation_tag_sdr:     z.string().optional(),
  hs_lead_status:       z.enum(["NEW", "OPEN", "IN_PROGRESS", "OPEN_DEAL",
                          "UNQUALIFIED", "ATTEMPTED_TO_CONTACT",
                          "CONNECTED", "BAD_TIMING"]).default("NEW"),
  phone:                z.string().optional(),
  mobilephone:          z.string().optional(),
  hs_linkedin_url:      z.string().url().optional(),
  hs_linkedin_headline: z.string().optional(),
  job_start_date:       z.string().optional(),
  department:           z.string().optional(),
  level:                z.string().optional(),
  company:              z.string().optional(),
});
```

### HubSpotCompanySchema (16 champs)

```typescript
const HubSpotCompanySchema = z.object({
  name:                   z.string(),
  domain:                 z.string(),
  country:                z.string().optional(),
  country_dropdown:       z.string().optional(),
  description:            z.string().optional(),
  linkedin_company_page:  z.string().url().optional(),
  founded_year:           z.string().optional(),
  industry_emalist:       z.string().optional(),
  city:                   z.string().optional(),
  zip:                    z.string().optional(),
  address:                z.string().optional(),
  numberofemployees:      z.number().optional(),
  employees_category:     z.enum(["1-10","11-50","51-200","201-500","501-1000","1001+"]).optional(),
  type:                   z.enum(["PROSPECT","PARTNER","RESELLER","VENDOR","OTHER"]).optional(),
  national_administrative_division__nad_:       z.string().optional(),
  national_administrative_sub_division__nas_:   z.string().optional(),
});
```

### UploadResult & UploadError

```typescript
interface UploadResult {
  created: number;
  updated: number;
  errors: UploadError[];
  duration: number;
}

interface UploadError {
  email: string;
  reason: string;
  httpStatus?: number;
  retryable: boolean;
}
```

---

## Deduplication

### Strategie intra-batch

Avant l'envoi, le pipeline deduplique les contacts au sein du meme batch :

1. **Cle de dedup** : `email` (lowercase, trim)
2. **Conflit** : le dernier enregistrement gagne (last-write-wins)
3. **Log** : chaque doublon intra-batch est logue avec les deux enregistrements

### Strategie historique (CRM existant)

| Methode | Disponibilite | Automatisation |
|---------|---------------|----------------|
| Search API par email | Toujours | Oui (etape 1 du flux) |
| Operations Hub dedup | Si licence Pro+ | Semi-auto (regles a configurer) |
| Export + merge manuel | Toujours | Non |

> [!warning] Limite de la dedup par email
> Un contact peut apparaitre avec un email different mais le meme profil LinkedIn (`hs_linkedin_url`). Ce cas n'est pas couvert par la dedup actuelle. Decision ouverte : voir section Decisions ouvertes.

---

## Decisions ouvertes

| # | Question | Contexte | Statut |
|---|----------|----------|--------|
| 1 | CSV import vs API ? | L'import CSV natif HubSpot est plus simple mais moins controlable. L'API permet la dedup et le logging. | **Decision : API** (confirme) |
| 2 | Contact avec email different mais meme LinkedIn URL ? | Risque de doublons non detectes. Solutions possibles : dedup secondaire par `hs_linkedin_url`, merge post-import, Operations Hub. | **Ouvert** |
| 3 | Gestion des erreurs batch ? | Si 1 contact sur 100 echoue dans un batch create, les 99 autres sont crees. Faut-il retry le contact en erreur unitairement ? | **Ouvert** |

---

## Liens

- [[crm/hubspot-properties]] -- Proprietes et mapping complets
- [[crm/hubspot-backlog]] -- Backlog d'optimisation CRM
- [[tech/integrations]] -- Vue d'ensemble des integrations
- [[leadgen/pipeline-overview]] -- Pipeline de lead generation

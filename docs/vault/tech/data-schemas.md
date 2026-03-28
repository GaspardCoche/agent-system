---
title: "Schemas de Donnees -- Zod & TypeScript"
id: tech-data-schemas
type: tech
tags: [tech, schemas, zod, typescript, validation, data-model]
agents: [forge, sentinel]
updated: 2026-03-28
---

# Schemas de Donnees -- Zod & TypeScript

Ce document reference l'ensemble des schemas Zod utilises dans le pipeline `lead-pipeline`. Chaque schema valide les donnees a un point precis du flux : ingestion, nettoyage, enrichissement, et upload CRM.

---

## Vue d'ensemble des schemas

```
RawLead (ingestion)
  |
  +-- CleaningResult
  |     +-- cleanLeads[]    -> EnrichedLead
  |     +-- reviewLeads[]   -> EnrichedLead
  |     +-- binLeads[]      -> BinLead
  |
  +-- EnrichedLead (post-enrichissement)
  |     |
  |     +-- HubSpotContactSchema (mapping CRM)
  |     +-- HubSpotCompanySchema (extraction company)
  |
  +-- PipelineConfig (configuration)
  +-- BatchMeta (metadata)
```

---

## HubSpotContactSchema (16 champs)

Schema de validation pour les contacts a envoyer vers HubSpot. Aligne sur les proprietes CRM documentees dans [[crm/hubspot-properties]].

```typescript
import { z } from "zod";

export const HubSpotContactSchema = z.object({
  // --- Identite ---
  email:                z.string().email(),
  firstname:            z.string().min(1),
  lastname:             z.string().min(1),
  jobtitle:             z.string().optional(),
  gender:               z.enum(["Mr", "Ms"]).optional(),

  // --- Localisation & langue ---
  hs_language:          z.string().optional(),  // ISO locale: "fr", "en", "nl", "de"

  // --- Tracking & statut ---
  creation_tag_sdr:     z.string().optional(),
  hs_lead_status:       z.enum([
                          "NEW",
                          "OPEN",
                          "IN_PROGRESS",
                          "OPEN_DEAL",
                          "UNQUALIFIED",
                          "ATTEMPTED_TO_CONTACT",
                          "CONNECTED",
                          "BAD_TIMING",
                        ]).default("NEW"),

  // --- Coordonnees ---
  phone:                z.string().optional(),
  mobilephone:          z.string().optional(),

  // --- LinkedIn ---
  hs_linkedin_url:      z.string().url().optional(),
  hs_linkedin_headline: z.string().optional(),

  // --- Poste ---
  job_start_date:       z.string().optional(),  // Format YYYY-MM-DD
  department:           z.enum([
                          "Finance", "Marketing", "Sales", "Operations",
                          "IT", "HR", "Legal", "Engineering", "Product",
                          "Customer Success", "Executive", "Consulting", "Other",
                        ]).optional(),
  level:                z.enum([
                          "C-Level", "VP", "Director", "Manager",
                          "Senior", "Junior", "Intern",
                        ]).optional(),

  // --- Entreprise ---
  company:              z.string().optional(),
});

export type HubSpotContact = z.infer<typeof HubSpotContactSchema>;
```

> [!info] Alignement avec HubSpot
> Les noms de champs correspondent exactement aux noms internes HubSpot. Voir [[crm/hubspot-properties]] pour le mapping complet et les enumerations.

---

## HubSpotCompanySchema (16 champs)

Schema de validation pour les companies a creer/mettre a jour dans HubSpot.

```typescript
export const HubSpotCompanySchema = z.object({
  // --- Identite ---
  name:                   z.string().min(1),
  domain:                 z.string().min(1),

  // --- Geographie ---
  country:                z.string().optional(),
  country_dropdown:       z.string().optional(),  // ISO 3166-1, 249 valeurs
  city:                   z.string().optional(),
  zip:                    z.string().optional(),
  address:                z.string().optional(),

  // --- Description ---
  description:            z.string().optional(),
  linkedin_company_page:  z.string().url().optional(),
  founded_year:           z.string().optional(),

  // --- Classification ---
  industry_emalist:       z.string().optional(),  // 136 industries EMAsphere
  numberofemployees:      z.number().int().nonnegative().optional(),
  employees_category:     z.enum([
                            "1-10", "11-50", "51-200",
                            "201-500", "501-1000", "1001+",
                          ]).optional(),
  type:                   z.enum([
                            "PROSPECT", "PARTNER", "RESELLER",
                            "VENDOR", "OTHER",
                          ]).optional(),

  // --- Divisions administratives ---
  national_administrative_division__nad_:     z.string().optional(),   // 25 regions
  national_administrative_sub_division__nas_: z.string().optional(),   // 116 departements
});

export type HubSpotCompany = z.infer<typeof HubSpotCompanySchema>;
```

---

## RawLead (~20 champs)

Schema brut des leads tels qu'extraits par PhantomBuster depuis Sales Navigator. Ce schema represente les donnees avant tout nettoyage ou enrichissement.

```typescript
export const RawLeadSchema = z.object({
  // --- Identite ---
  firstName:            z.string().optional(),
  lastName:             z.string().optional(),
  fullName:             z.string().optional(),

  // --- Contact ---
  email:                z.string().optional(),
  phone:                z.string().optional(),

  // --- Professionnel ---
  jobTitle:             z.string().optional(),
  company:              z.string().optional(),
  companyUrl:           z.string().optional(),
  industry:             z.string().optional(),

  // --- LinkedIn ---
  linkedinUrl:          z.string().optional(),
  linkedinHeadline:     z.string().optional(),
  linkedinProfileImage: z.string().optional(),
  connectionDegree:     z.string().optional(),

  // --- Localisation ---
  location:             z.string().optional(),
  country:              z.string().optional(),
  region:               z.string().optional(),

  // --- Entreprise ---
  companySize:          z.string().optional(),
  companyLinkedinUrl:   z.string().optional(),
  companyDomain:        z.string().optional(),

  // --- Meta ---
  salesNavUrl:          z.string().optional(),
  extractedAt:          z.string().optional(),
});

export type RawLead = z.infer<typeof RawLeadSchema>;
```

> [!warning] Donnees non fiables
> Les donnees brutes de PhantomBuster peuvent contenir des valeurs manquantes, mal formatees, ou incoherentes. Le pipeline de nettoyage ([[leadgen/cleaning-rules]]) applique les transformations necessaires avant enrichissement.

---

## EnrichedLead

Extension du `RawLead` avec les donnees issues de l'enrichissement (FullEnrich, gender-detector, language-map).

```typescript
export const EnrichedLeadSchema = RawLeadSchema.extend({
  // --- Enrichissement email ---
  enrichedEmail:        z.string().email().optional(),
  enrichedPhone:        z.string().optional(),
  enrichmentStatus:     z.enum(["enriched", "partial", "failed", "skipped"]),

  // --- Enrichissement identite ---
  gender:               z.enum(["Mr", "Ms"]).optional(),
  language:             z.string().optional(),        // ISO locale

  // --- Enrichissement entreprise ---
  mappedIndustry:       z.string().optional(),        // industry_emalist
  employeesCategory:    z.string().optional(),        // enum 6 tranches
  countryDropdown:      z.string().optional(),        // ISO 3166-1
  nad:                  z.string().optional(),        // region
  nas:                  z.string().optional(),        // departement

  // --- Scoring nettoyage ---
  cleaningScore:        z.number().min(0).max(100).optional(),
  cleaningFlags:        z.array(z.string()).optional(),
});

export type EnrichedLead = z.infer<typeof EnrichedLeadSchema>;
```

---

## BinLead

Schema pour les leads rejetes pendant le nettoyage. Conserves pour audit et recuperation eventuelle.

```typescript
export const BinLeadSchema = z.object({
  firstName:    z.string().optional(),
  lastName:     z.string().optional(),
  email:        z.string().optional(),
  jobTitle:     z.string().optional(),
  company:      z.string().optional(),
  linkedinUrl:  z.string().optional(),
  binReason:    z.string(),                // Raison du rejet
  recoverable:  z.boolean().default(false), // Recuperable apres correction manuelle ?
});

export type BinLead = z.infer<typeof BinLeadSchema>;
```

> [!tip] Recuperation
> Les leads avec `recoverable: true` peuvent etre reinjectes dans le pipeline apres correction manuelle. Cas typiques : email manquant mais LinkedIn present, nom mal parse.

---

## CleaningResult

Resultat du processus de nettoyage. Trois categories de sortie.

```typescript
export const CleaningResultSchema = z.object({
  cleanLeads:   z.array(EnrichedLeadSchema),   // Prets pour upload
  reviewLeads:  z.array(EnrichedLeadSchema),    // Necessitent revue manuelle
  binLeads:     z.array(BinLeadSchema),         // Rejetes
});

export type CleaningResult = z.infer<typeof CleaningResultSchema>;
```

| Categorie | Description | Action suivante |
|-----------|-------------|-----------------|
| `cleanLeads` | Leads valides, enrichis, prets a etre mappes vers HubSpot | Upload automatique |
| `reviewLeads` | Leads avec des anomalies non bloquantes (doublon potentiel, champ suspect) | Revue manuelle dans Google Sheets |
| `binLeads` | Leads invalides (critere d'exclusion, donnees insuffisantes) | Archivage avec raison |

---

## PipelineConfig

Configuration d'execution du pipeline. Passee a l'orchestrateur au lancement.

```typescript
export const PipelineConfigSchema = z.object({
  phantomId:      z.string(),                 // ID de l'agent PhantomBuster
  salesNavUrl:    z.string().url(),            // URL de la recherche Sales Navigator
  batchName:      z.string(),                 // Nom du batch (ex: "BE-IT-Q2-2026")
  batchId:        z.string().uuid(),          // ID unique du batch
  listRegion:     z.string(),                 // Region cible (ex: "Belgium", "France")
  batchSize:      z.number().int().positive(), // Nombre de leads a extraire
  dryRun:         z.boolean().default(false),  // Mode simulation (pas d'ecriture CRM)
  from:           z.enum([
                    "phantombuster",
                    "csv",
                    "google-sheets",
                    "manual",
                  ]),
});

export type PipelineConfig = z.infer<typeof PipelineConfigSchema>;
```

> [!info] Mode dryRun
> En mode `dryRun: true`, le pipeline execute toutes les etapes (extraction, nettoyage, enrichissement, mapping) mais n'ecrit rien dans HubSpot ni Google Sheets. Utile pour les tests et la validation des schemas.

---

## BatchMeta

Metadonnees d'un batch, generees automatiquement par l'orchestrateur.

```typescript
export const BatchMetaSchema = z.object({
  id:         z.string().uuid(),
  batchName:  z.string(),
  startedAt:  z.string().datetime(),
  source:     z.enum(["phantombuster", "csv", "google-sheets", "manual"]),
  counts:     z.object({
    extracted:  z.number().int().nonnegative(),
    cleaned:    z.number().int().nonnegative(),
    enriched:   z.number().int().nonnegative(),
    uploaded:   z.number().int().nonnegative(),
    binned:     z.number().int().nonnegative(),
    review:     z.number().int().nonnegative(),
    errors:     z.number().int().nonnegative(),
  }),
});

export type BatchMeta = z.infer<typeof BatchMetaSchema>;
```

---

## Relations entre schemas

```
PipelineConfig ─────> Orchestrator
                          |
                    RawLead[] (extraction)
                          |
                    CleaningResult
                     /    |    \
              clean[]  review[]  bin[]
                |         |
          EnrichedLead  EnrichedLead
                |
         ┌──────┴──────┐
  HubSpotContact  HubSpotCompany
         |              |
    batch create    company create
         |              |
         └──────┬───────┘
           association
                |
           BatchMeta (resultat)
```

---

## Conventions de validation

| Convention | Regle |
|------------|-------|
| `gender` | Toujours `Mr` ou `Ms` (pas de Mr./Mrs./Mme) |
| `hs_language` | ISO 639-1 locale (`fr`, `en`, `nl`, `de`) |
| `industry_emalist` | Valeur exacte de l'enum HubSpot (136 valeurs) |
| `employees_category` | Une des 6 tranches exactes |
| `country_dropdown` | Nom complet du pays en anglais (ISO 3166-1) |
| `national_administrative_division__nad_` | Nom de region exact (25 valeurs) |
| Emails | Validation format + exclusion domaines generiques |
| URLs LinkedIn | Doit commencer par `https://www.linkedin.com/` |

> [!warning] Coherence schemas-CRM
> Les schemas Zod doivent rester synchronises avec les proprietes HubSpot. Toute modification de propriete dans le CRM (tache #3 du [[crm/hubspot-backlog]]) doit etre repercutee ici. Voir aussi [[crm/hubspot-properties]].

---

## Liens

- [[crm/hubspot-properties]] -- Proprietes HubSpot et enumerations
- [[leadgen/cleaning-rules]] -- Regles de nettoyage appliquees aux RawLeads
- [[tech/code-repository]] -- Structure du code et stubs

---
title: "Code Repository -- lead-pipeline"
id: tech-code-repository
type: tech
tags: [tech, code, typescript, repository, lead-pipeline]
agents: [forge, sentinel]
updated: 2026-03-28
---

# Code Repository -- lead-pipeline

Documentation technique du repository `lead-pipeline`, le moteur central du pipeline de generation de leads.

---

## Informations generales

| Champ | Valeur |
|-------|--------|
| Repository | `hwinssinger/lead-pipeline` |
| Visibilite | Prive |
| Runtime | Node.js |
| Langage | TypeScript (ESM) |
| Validation | Zod |
| Statut | Compile, non-fonctionnel (stubs) |

> [!warning] Statut actuel
> Le projet compile sans erreur mais reste non-fonctionnel. Toutes les integrations externes sont implementees sous forme de stubs qui retournent des donnees mock. Le remplacement des stubs par les implementations reelles est la priorite Q2 2026.

---

## Structure du repository

```
lead-pipeline/
|
+-- src/
|   |
|   +-- orchestrator.ts              # Point d'entree principal
|   +-- types/
|   |   +-- index.ts                 # Re-exports
|   |   +-- hubspot.ts               # HubSpotContactSchema, HubSpotCompanySchema
|   |   +-- leads.ts                 # RawLead, EnrichedLead, BinLead
|   |   +-- pipeline.ts              # PipelineConfig, BatchMeta, CleaningResult
|   |   +-- errors.ts                # UploadResult, UploadError
|   |
|   +-- config/
|   |   +-- index.ts                 # Configuration centrale
|   |   +-- env.ts                   # Variables d'environnement
|   |
|   +-- agents/
|   |   +-- phantom.ts               # Agent PhantomBuster (3 stubs)
|   |   +-- enrich.ts                # Agent FullEnrich (3 stubs)
|   |   +-- cleaning.ts              # Agent nettoyage (regles)
|   |   +-- sheets.ts                # Agent Google Sheets (3 stubs)
|   |   +-- hubspot.ts               # Agent HubSpot (6 stubs)
|   |
|   +-- lookups/
|   |   +-- gender-db.ts             # Base genres par prenom
|   |   +-- language-map.ts          # Mapping pays -> langue
|   |   +-- industry-db.ts           # Mapping industries -> industry_emalist
|   |   +-- job-title-rules.ts       # Regles extraction department/level
|   |
|   +-- utils/
|       +-- fuzzy.ts                 # Matching flou (noms, industries)
|       +-- text-utils.ts            # Normalisation texte, trim, case
|       +-- validators.ts            # Validation email, URL, telephone
|       +-- dedup.ts                 # Deduplication intra-batch
|       +-- logger.ts                # Logger structure (Winston)
|       +-- rate-limiter.ts          # Rate limiter HubSpot API
|
+-- tests/                           # Tests unitaires (vitest)
+-- scripts/                         # Scripts utilitaires
+-- .env.example                     # Template variables d'environnement
+-- package.json
+-- tsconfig.json
+-- vitest.config.ts
```

---

## Stubs a remplacer

### Vue d'ensemble

| Service | Agent | Stubs | Fonction |
|---------|-------|-------|----------|
| PhantomBuster | `phantom.ts` | 3 | Extraction Sales Navigator |
| FullEnrich | `enrich.ts` | 3 | Enrichissement email/telephone |
| Google Sheets | `sheets.ts` | 3 | Lecture/ecriture feuilles |
| HubSpot | `hubspot.ts` | 6 | CRUD CRM |
| MCP gender-detector | `cleaning.ts` | 1 | Detection genre par prenom |
| **Total** | | **16** | |

### Detail des stubs

#### PhantomBuster (3 stubs)

```typescript
// phantom.ts
async function launchAgent(phantomId: string, config: object): Promise<string>
// -> Lance un agent PB, retourne containerId

async function getAgentStatus(containerId: string): Promise<"running" | "finished" | "error">
// -> Verifie le statut d'un agent

async function getAgentResult(containerId: string): Promise<RawLead[]>
// -> Recupere les resultats d'extraction
```

#### FullEnrich (3 stubs)

```typescript
// enrich.ts
async function enrichByEmail(email: string): Promise<EnrichmentResult>
// -> Enrichissement a partir d'un email

async function enrichByLinkedIn(linkedinUrl: string): Promise<EnrichmentResult>
// -> Enrichissement a partir d'un profil LinkedIn

async function getBulkEnrichmentStatus(batchId: string): Promise<EnrichmentBatch>
// -> Statut d'un batch d'enrichissement
```

#### Google Sheets (3 stubs)

```typescript
// sheets.ts
async function readSheet(spreadsheetId: string, range: string): Promise<string[][]>
// -> Lecture d'une plage de cellules

async function writeSheet(spreadsheetId: string, range: string, values: string[][]): Promise<void>
// -> Ecriture d'une plage de cellules

async function appendSheet(spreadsheetId: string, range: string, values: string[][]): Promise<void>
// -> Ajout de lignes en fin de feuille
```

#### HubSpot (6 stubs)

Voir [[crm/hubspot-api]] pour le detail complet des 6 stubs HubSpot.

```typescript
// hubspot.ts
async function searchContactByEmail(email: string): Promise<HubSpotContact | null>
async function batchCreateContacts(contacts: HubSpotContactSchema[]): Promise<UploadResult>
async function batchUpdateContacts(contacts: HubSpotContactSchema[]): Promise<UploadResult>
async function searchCompanyByDomain(domain: string): Promise<HubSpotCompany | null>
async function createCompany(company: HubSpotCompanySchema): Promise<HubSpotCompany>
async function associateContactToCompany(contactId: string, companyId: string): Promise<void>
```

#### MCP gender-detector (1 stub)

```typescript
// cleaning.ts (utilise dans le flux de nettoyage)
async function detectGender(firstName: string): Promise<"Mr" | "Ms" | null>
// -> Detection du genre via MCP tool, fallback sur gender-db local
```

---

## Donnees de lookup peuplees

| Fichier | Contenu | Statut | Completude |
|---------|---------|--------|------------|
| `industry-db.ts` | Mapping industrie source -> `industry_emalist` | Peuple | ~380 mappings |
| `gender-db.ts` | Prenoms -> genre (`Mr`/`Ms`) | Echantillon | 7/199 prenoms (3.5%) |
| `language-map.ts` | Pays -> `hs_language` (ISO locale) | Partiel | 20/~100 pays (20%) |
| `job-title-rules.ts` | Regex titres -> `department` + `level` | Peuple | ~50 regles |

> [!warning] Completude gender-db et language-map
> Ces deux bases sont significativement incompletes. Le fallback pour `gender-db` est le MCP gender-detector (stub). Le fallback pour `language-map` est une detection par TLD du domaine email. L'enrichissement de ces bases est prevu Q2-Q3 2026.

---

## Alignement des schemas

Les schemas Zod dans `types/` sont alignes avec les proprietes HubSpot :

| Schema | Propriete | Alignement |
|--------|-----------|------------|
| `gender` | `Mr` / `Ms` | Aligne avec enum HubSpot custom |
| `hs_language` | ISO locale (`fr`, `en`, `nl`) | Aligne avec HubSpot native |
| `industry_emalist` | 136 valeurs EMAsphere | Aligne via `industry-db` mapping |
| `national_administrative_division__nad_` | 25 regions | Aligne avec enum HubSpot custom |
| `employees_category` | 6 tranches | Aligne avec enum HubSpot custom |
| `country_dropdown` | 249 pays ISO 3166-1 | Aligne avec enum HubSpot custom |

Voir [[tech/data-schemas]] pour le code complet des schemas et [[crm/hubspot-properties]] pour la reference des proprietes CRM.

---

## Variables d'environnement

> [!warning] Securite
> Ne jamais commiter le fichier `.env`. Utiliser `.env.example` comme template.

```bash
# --- PhantomBuster ---
PHANTOMBUSTER_API_KEY=pb_xxxxxxxxxxxxxxxx
PHANTOMBUSTER_AGENT_ID=1234567890

# --- FullEnrich ---
FULLENRICH_API_KEY=fe_xxxxxxxxxxxxxxxx
FULLENRICH_WEBHOOK_URL=https://example.com/webhook/fullenrich

# --- Google Sheets ---
GOOGLE_SERVICE_ACCOUNT_EMAIL=pipeline@project.iam.gserviceaccount.com
GOOGLE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"
GOOGLE_SPREADSHEET_ID=1AbCdEfGhIjKlMnOpQrStUvWxYz

# --- HubSpot ---
HUBSPOT_PRIVATE_APP_TOKEN=pat-xx-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
HUBSPOT_PORTAL_ID=12345678

# --- Pipeline ---
PIPELINE_ENV=development          # development | staging | production
PIPELINE_DRY_RUN=true             # true | false
PIPELINE_LOG_LEVEL=debug          # debug | info | warn | error
PIPELINE_BATCH_SIZE=100           # Taille des batchs HubSpot

# --- MCP ---
MCP_GENDER_DETECTOR_URL=http://localhost:3001/detect-gender
```

---

## Commandes

```bash
# Installation
npm install

# Build
npm run build

# Tests
npm run test

# Lancer le pipeline (mode dry-run)
npm run start -- --dry-run --batch-name "TEST-Q2-2026"

# Lancer le pipeline (production)
npm run start -- --batch-name "BE-IT-Q2-2026" --region "Belgium"

# Lint
npm run lint

# Type check
npm run typecheck
```

---

## Prochaines etapes

| Priorite | Tache | Dependance |
|----------|-------|------------|
| 1 | Remplacement stubs HubSpot (6) | Token Private App |
| 2 | Remplacement stubs Google Sheets (3) | Service Account |
| 3 | Remplacement stubs PhantomBuster (3) | API Key PB |
| 4 | Remplacement stubs FullEnrich (3) | API Key FE |
| 5 | Remplacement stub MCP gender-detector (1) | MCP server |
| 6 | Completion gender-db (7 -> 199+) | Donnees prenoms |
| 7 | Completion language-map (20 -> 100+) | Recherche pays/langues |

---

## Liens

- [[tech/data-schemas]] -- Schemas Zod complets
- [[tech/infrastructure]] -- Infrastructure et deploiement
- [[tech/integrations]] -- Integrations externes
- [[leadgen/pipeline-overview]] -- Vue d'ensemble du pipeline

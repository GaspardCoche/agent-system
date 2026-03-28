---
title: "Regles de Nettoyage -- Contact & Company"
id: leadgen-cleaning-rules
type: leadgen
tags: [leadgen, cleaning, rules, typescript, data-quality]
agents: [aria, forge]
updated: 2026-03-28
---

# Regles de Nettoyage -- Contact & Company

Ce document consolide l'ensemble des regles de nettoyage appliquees aux leads, couvrant les 22 features (10 Contact + 12 Company) avec leurs priorites, algorithmes, et statuts d'implementation.

---

## Vue d'ensemble du Pipeline TypeScript

Le cleaning agent est un pipeline TypeScript en 9 etapes sequentielles :

```
CSV enrichi (PhantomBuster + FullEnrich)
    |
    v
1. Deduplication (email + LinkedIn URL)
    |
    v
2. Filtrage Job Title (include/exclude rules)
    |
    v
3. Normalisation Unicode (NFD → NFC)
    |
    v
4. Detection Genre (nameGenderDb / MCP)
    |
    v
5. Attribution Langue (languageMap + pays)
    |
    v
6. Inference Pays (location / postal code / domain)
    |
    v
7. Validation Email (format + bounce status)
    |
    v
8. Validation Telephone (format E.164)
    |
    v
9. Nettoyage Noms (capitalisation, accents, prefixes)
    |
    v
CSV nettoye → GMT ou HubSpot
```

---

## Features Contact (10)

### P0 -- Critique

| # | Feature | Methode | Script | Statut |
|---|---------|---------|--------|--------|
| C1 | **Gender** | Lookup `nameGenderDb` → MCP gender-detector (~40k noms). Fallback : analyse prenom + suffixes linguistiques | `cleanGender.ts` | Implemente |
| C2 | **Preferred Language** | Lookup `languageMap` (~100 pays). Belgique : resolution Wallonie/Flandre par code postal | `cleanLanguage.ts` | Implemente |
| C3 | **Job Title Filtering** | Keywords include (CFO, CEO, Finance Director, etc. poids 1-3) vs exclude (Marketing, HR, Sales, etc. poids 1-2). Multilingue FR/NL/EN | `filterJobTitle.ts` | Implemente |
| C4 | **Email Bounced** | Verification `bounceStatus` FullEnrich. Reject si invalid, flag si unknown | `validateEmail.ts` | Implemente |

### P1 -- Important

| # | Feature | Methode | Script | Statut |
|---|---------|---------|--------|--------|
| C5 | **Email Address** | Validation format RFC 5322, blacklist domaines personnels (gmail, hotmail, yahoo), detection catch-all | `validateEmail.ts` | Implemente |
| C6 | **Company Associated** | Association via `companyDomain` ou `companyName` exact match dans HubSpot | `associateCompany.ts` | Implemente |
| C7 | **Department** | Classification par algorithme **Levenshtein** sur le job title. Categories : Finance, Executive, Operations, IT, Legal | `classifyDepartment.ts` | Implemente |

### P2 -- Souhaitable

| # | Feature | Methode | Script | Statut |
|---|---------|---------|--------|--------|
| C8 | **LinkedIn URL (Contact)** | Validation format, reconstruction depuis vmid si absent | `validateLinkedIn.ts` | Partiel |
| C9 | **Postal Code** | Extraction depuis location, validation format par pays | `cleanPostalCode.ts` | Non implemente |

### P3 -- Futur

| # | Feature | Methode | Script | Statut |
|---|---------|---------|--------|--------|
| C10 | **Level** | Classification hierarchique par algorithme **Jaro-Winkler** sur job title. Niveaux : C-Suite, VP, Director, Manager, Individual | `classifyLevel.ts` | Non implemente |

---

## Features Company (12)

### P0 -- Critique

| # | Feature | Methode | Script | Statut |
|---|---------|---------|--------|--------|
| E1 | **Company Name** | Nettoyage : suppression suffixes juridiques (SA, SAS, SPRL, Ltd, GmbH), normalisation Unicode, capitalisation | `cleanCompanyName.ts` | Implemente |
| E2 | **Domain** | Inference depuis email, validation DNS, fallback depuis companyLinkedinUrl | `inferDomain.ts` | Implemente |
| E3 | **Country** | Inference multi-source : location, postal code, domain TLD, langue. Priorite : postal code > location > domain | `inferCountry.ts` | Implemente |
| E4 | **Company Type** | Classification : Corporate, Mid-Market, Enterprise, SMB selon headcount et chiffre d'affaires | `classifyCompanyType.ts` | Implemente |

### P1 -- Important

| # | Feature | Methode | Script | Statut |
|---|---------|---------|--------|--------|
| E5 | **Address** | Parsing adresse structuree (rue, ville, code postal, pays) depuis champ location brut | `parseAddress.ts` | Partiel |
| E6 | **Industry** | Mapping LinkedIn → HubSpot par algorithme **Jaro-Winkler** + lookup `industryDb` (~400 mappings) | `mapIndustry.ts` | Implemente |

### P2 -- Souhaitable

| # | Feature | Methode | Script | Statut |
|---|---------|---------|--------|--------|
| E7 | **LinkedIn URL (Company)** | Validation format, normalisation (trailing slash, www) | `validateCompanyLinkedIn.ts` | Partiel |
| E8 | **Employees** | Formatage en categories : 1-10, 11-50, 51-200, 201-500, 501-1000, 1001-5000, 5000+ | `formatEmployees.ts` | Non implemente |
| E9 | **Postal Code** | Extraction et validation format par pays | `cleanPostalCode.ts` | Non implemente |

### P3 -- Futur

| # | Feature | Methode | Script | Statut |
|---|---------|---------|--------|--------|
| E10 | **Contact qui change d'entreprise** | Detection via comparaison historique LinkedIn | `detectJobChange.ts` | Non implemente |
| E11 | **Turnover (CA)** | Enrichissement depuis Trendstop (BE) ou estimation | `enrichTurnover.ts` | Non implemente |
| E12 | **Multiple sites/entites** | Resolution groupe vs filiale, deduplication entites | `resolveEntities.ts` | Non implemente |

---

## Algorithmes de Matching

### Levenshtein (Department)

Utilise pour la classification departement. Calcule la distance d'edition entre le job title et les labels de departement de reference.

```typescript
// Seuil : distance <= 3 pour match
// Exemple : "Chief Financal Officer" → distance 1 de "Chief Financial Officer" → match Finance
levenshtein(jobTitle, departmentLabel) <= threshold
```

### Jaro-Winkler (Level + Industry)

Utilise pour la classification niveau hierarchique et le mapping industrie. Favorise les correspondances en debut de chaine (prefixe commun).

```typescript
// Seuil : similarite >= 0.85 pour match
// Exemple : "Finance Director" → similarite 0.92 avec "Financial Director" → match
jaroWinkler(input, reference) >= threshold
```

### Exact Match

Utilise pour les lookups deterministes (pays, langue, genre pour les noms connus).

### Unicode NFD → NFC

Normalisation des caracteres accentues. Decomposition canonique (NFD) suivie de composition canonique (NFC) pour uniformiser les encodages.

```typescript
// "Rene" avec accent combine → "Rene" avec caractere precompose
input.normalize('NFD').replace(/[\u0300-\u036f]/g, '').normalize('NFC')
```

### Date Parsing

Parsing multi-format pour les dates d'enrichissement et de scraping.

```typescript
// Formats supportes : ISO 8601, DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD
parseDate(input, locale) → Date
```

### Employee Category Formatting

Conversion des valeurs numeriques brutes en categories standardisees HubSpot.

```typescript
// 150 → "51-200"
// 3500 → "1001-5000"
formatEmployeeCategory(count: number) → string
```

---

## Matrice de Statut

| Priorite | Total | Implemente | Partiel | Non implemente |
|----------|-------|-----------|---------|----------------|
| P0 | 8 | 8 | 0 | 0 |
| P1 | 5 | 4 | 1 | 0 |
| P2 | 4 | 0 | 2 | 2 |
| P3 | 5 | 0 | 0 | 5 |
| **Total** | **22** | **12** | **3** | **7** |

> [!tip] Progression
> Les features P0 et P1 couvrent les besoins critiques du pipeline actuel. Les P2 ameliorent la qualite des donnees CRM. Les P3 sont des objectifs moyen-terme lies a l'intelligence du systeme.

---

## Dependances

| Script | Dependances externes |
|--------|---------------------|
| `cleanGender.ts` | MCP gender-detector, `nameGenderDb` (GMT) |
| `cleanLanguage.ts` | `languageMap` (GMT) |
| `filterJobTitle.ts` | `jobTitleRules` (GMT) |
| `mapIndustry.ts` | `industryDb` (GMT) |
| `inferCountry.ts` | `languageMap` (GMT), libphonenumber |
| `validateEmail.ts` | Donnees FullEnrich |
| `associateCompany.ts` | API HubSpot |

---

## Liens

- [[leadgen/pipeline-overview]]
- [[leadgen/cleaning-gmt]]
- [[leadgen/enrichment-fullenrich]]
- [[crm/hubspot-properties]]

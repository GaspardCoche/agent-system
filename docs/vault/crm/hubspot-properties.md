---
title: "HubSpot -- Proprietes & Mapping"
id: crm-hubspot-properties
type: crm
tags: [crm, hubspot, properties, mapping, contact, company]
agents: [aria]
updated: 2026-03-28
---

# HubSpot -- Proprietes & Mapping

Ce document centralise l'ensemble des proprietes Contact et Company utilisees dans le CRM HubSpot, leurs noms internes, types, enumerations, ainsi que les regles de mapping entre les sources de donnees et le CRM.

---

## Proprietes Contact (21)

> [!info] Convention de nommage
> Les noms internes HubSpot utilisent le format `snake_case`. Les proprietes prefixees `hs_` sont des proprietes natives HubSpot. Les autres sont soit natives (ex: `firstname`) soit custom (ex: `creation_tag_sdr`).

| # | Label | Nom interne | Type | Enum / Format | Custom |
|---|-------|-------------|------|---------------|--------|
| 1 | Prenom | `firstname` | single-line text | -- | Non |
| 2 | Nom | `lastname` | single-line text | -- | Non |
| 3 | Genre | `gender` | enumeration | `Mr`, `Ms` | Oui |
| 4 | Titre LinkedIn | `hs_linkedin_headline` | single-line text | -- | Non |
| 5 | URL LinkedIn | `hs_linkedin_url` | single-line text | URL format | Non |
| 6 | Poste | `jobtitle` | single-line text | -- | Non |
| 7 | Date debut poste | `job_start_date` | date | `YYYY-MM-DD` | Non |
| 8 | Email | `email` | single-line text | Email format | Non |
| 9 | Mobile | `mobilephone` | single-line text | International format | Non |
| 10 | Langue preferee | `hs_language` | enumeration | ISO locale (`fr`, `en`, `nl`, `de`, etc.) | Non |
| 11 | Departement | `department` | enumeration | Voir enum ci-dessous | Oui |
| 12 | Niveau hierarchique | `level` | enumeration | Voir enum ci-dessous | Oui |
| 13 | Tag SDR creation | `creation_tag_sdr` | single-line text | Nom du SDR/batch | Oui |
| 14 | Statut Lead | `hs_lead_status` | enumeration | Defaut: `NEW` | Non |
| 15 | Entreprise | `company` | single-line text | -- | Non |
| 16 | Telephone | `phone` | phone number | International format | Non |
| 17 | URL LinkedIn Headline | `hs_linkedin_headline` | single-line text | -- | Non |
| 18 | Pays | `country` | single-line text | -- | Non |
| 19 | Ville | `city` | single-line text | -- | Non |
| 20 | Code postal | `zip` | single-line text | -- | Non |
| 21 | Adresse | `address` | single-line text | -- | Non |

### Enum `department`

```
Finance, Marketing, Sales, Operations, IT, HR, Legal, Engineering,
Product, Customer Success, Executive, Consulting, Other
```

### Enum `level`

```
C-Level, VP, Director, Manager, Senior, Junior, Intern
```

### Enum `hs_lead_status`

```
NEW (defaut), OPEN, IN_PROGRESS, OPEN_DEAL, UNQUALIFIED,
ATTEMPTED_TO_CONTACT, CONNECTED, BAD_TIMING
```

---

## Proprietes Company (15)

| # | Label | Nom interne | Type | Enum / Format | Custom |
|---|-------|-------------|------|---------------|--------|
| 1 | Nom | `name` | single-line text | -- | Non |
| 2 | Domaine | `domain` | single-line text | `example.com` | Non |
| 3 | Pays (dropdown) | `country_dropdown` | enumeration | 249 valeurs (ISO 3166-1) | Oui |
| 4 | Description | `description` | multi-line text | -- | Non |
| 5 | Page LinkedIn | `linkedin_company_page` | single-line text | URL format | Non |
| 6 | Annee de fondation | `founded_year` | single-line text | `YYYY` | Non |
| 7 | Industrie EMAsphere | `industry_emalist` | enumeration | 136 valeurs | Oui |
| 8 | Ville | `city` | single-line text | -- | Non |
| 9 | Code postal | `zip` | single-line text | -- | Non |
| 10 | Adresse | `address` | single-line text | -- | Non |
| 11 | Nombre d'employes | `numberofemployees` | number | Entier | Non |
| 12 | Categorie employes | `employees_category` | enumeration | 6 tranches | Oui |
| 13 | Type d'entreprise | `type` | enumeration | 5 valeurs | Oui |
| 14 | Region (NAD) | `national_administrative_division__nad_` | enumeration | 25 regions | Oui |
| 15 | Departement (NAS) | `national_administrative_sub_division__nas_` | enumeration | 116 departements | Oui |

### Enum `employees_category`

| Valeur | Plage |
|--------|-------|
| `1-10` | Micro-entreprise |
| `11-50` | Petite entreprise |
| `51-200` | PME |
| `201-500` | ETI basse |
| `501-1000` | ETI haute |
| `1001+` | Grande entreprise |

### Enum `type`

```
PROSPECT, PARTNER, RESELLER, VENDOR, OTHER
```

### Enum `country_dropdown`

> [!tip] 249 valeurs ISO 3166-1
> La liste complete est alignee sur le standard ISO 3166-1 alpha-2. Les valeurs les plus utilisees dans notre contexte : `Belgium`, `France`, `Luxembourg`, `Netherlands`, `Germany`, `Switzerland`, `United Kingdom`, `United States`.

### Enum `industry_emalist`

> [!info] 136 industries
> Liste proprietaire EMAsphere. Exemples : `Accounting`, `Banking`, `Construction`, `Education`, `Energy`, `Healthcare`, `Insurance`, `IT Services`, `Legal Services`, `Manufacturing`, `Real Estate`, `Retail`, `Telecommunications`, `Transportation`... La liste complete est maintenue dans le fichier `lookups/industry-db` du repository [[tech/code-repository]].

### Enum `national_administrative_division__nad_` (25 regions)

Regions belges, francaises et luxembourgeoises. Exemples : `Wallonie`, `Flandre`, `Bruxelles-Capitale`, `Ile-de-France`, `Auvergne-Rhone-Alpes`, `Grand Est`, `Luxembourg`.

### Enum `national_administrative_sub_division__nas_` (116 departements)

Sous-divisions regionales (provinces belges, departements francais). Exemples : `Liege`, `Namur`, `Hainaut`, `Brabant wallon`, `Paris`, `Hauts-de-Seine`, `Rhone`.

---

## Proprietes Custom -- Recapitulatif

> [!warning] Proprietes non-standard
> Ces proprietes sont des creations custom dans le portail HubSpot. Elles doivent etre documentees et maintenues separement car elles ne sont pas couvertes par les sauvegardes natives HubSpot.

| Propriete | Objet | Raison |
|-----------|-------|--------|
| `creation_tag_sdr` | Contact | Tracabilite de l'origine du lead par SDR/batch |
| `gender` | Contact | Civilite Mr/Ms pour personnalisation outreach |
| `level` | Contact | Niveau hierarchique du contact |
| `department` | Contact | Departement fonctionnel du contact |
| `national_administrative_division__nad_` | Company | Region pour segmentation geographique |
| `national_administrative_sub_division__nas_` | Company | Departement/province pour attribution SDR |
| `industry_emalist` | Company | Classification industrie specifique EMAsphere |
| `employees_category` | Company | Tranches d'employes pour segmentation ICP |
| `country_dropdown` | Company | Pays avec dropdown standardise (249 valeurs) |

---

## Association Contact -- Company

L'association entre un Contact et une Company se fait via le champ `domain` :

1. Le domaine email du contact est extrait (ex: `jean@example.com` -> `example.com`)
2. Une recherche Company par `domain` est effectuee dans HubSpot
3. Si la Company existe, le Contact est associe (association type `contact_to_company`)
4. Si la Company n'existe pas, elle est creee puis associee

> [!warning] Cas limites
> - Domaines generiques (`gmail.com`, `outlook.com`, etc.) : ne pas creer de Company
> - Contacts avec email personnel : association manuelle requise
> - Contacts multiples avec emails differents pour la meme entreprise : couverts par la dedup domaine

---

## Fichier d'import HubSpot

### Difference avec le fichier GMT (Google Master Table)

| Fichier | Colonnes | Specificites |
|---------|----------|--------------|
| GMT (source) | 21 colonnes | Inclut `postal code` + `phone` |
| Import HubSpot | 20 colonnes | Retire `postal code` + `phone`, ajoute `preferred language` |

### Colonnes du fichier d'import HubSpot (20)

```
firstname, lastname, gender, email, mobilephone, jobtitle,
job_start_date, hs_linkedin_url, hs_linkedin_headline,
hs_language, department, level, creation_tag_sdr,
hs_lead_status, company, domain, country, city, address,
industry_emalist
```

> [!info] Transformation GMT -> Import
> Le pipeline de [[leadgen/cleaning-rules]] effectue la transformation automatiquement. La langue preferee (`hs_language`) est derivee du pays + TLD du domaine email via le fichier `lookups/language-map`.

---

## Workflow d'attribution post-import

Apres chaque import, un workflow HubSpot automatise l'attribution des leads aux SDR selon :

1. **Pays** (`country_dropdown`) -- Filtre primaire de region
2. **Code postal** (derive de `zip` ou `address`) -- Sous-region
3. **Langue** (`hs_language`) -- Attribution vers SDR francophone/neerlandophone/anglophone
4. **TLD** (derive de `domain`) -- Indicateur supplementaire de marche

> [!tip] Objectif Q3 2026
> Migrer vers un workflow base sur les proprietes `NAD` et `NAS` pour une attribution plus fine, en remplacement du code postal.

---

## Standardisation en cours (Q2-Q4 2026)

> [!warning] Chantier majeur
> La standardisation des proprietes est le task #3 du backlog HubSpot (voir [[crm/hubspot-backlog]]). Impact potentiel sur tout le pipeline.

### Axes de standardisation

- **Enumerations** : Alignement des valeurs `industry_emalist`, `employees_category`, `country_dropdown` entre les sources (PhantomBuster, FullEnrich, Google Sheets) et HubSpot
- **Nommage** : Conventions de nommage uniformes pour les proprietes custom
- **Types** : Verification des types de donnees (ex: `founded_year` pourrait passer en `number`)
- **Validation** : Schemas Zod alignes sur les proprietes HubSpot (voir [[tech/data-schemas]])
- **Nettoyage** : Suppression des proprietes obsoletes ou en double

### Planning

| Phase | Periode | Scope |
|-------|---------|-------|
| Audit | Q2 2026 | Inventaire complet des proprietes, identification des ecarts |
| Alignement schemas | Q2-Q3 2026 | Mise a jour des schemas Zod et du mapping |
| Migration donnees | Q3 2026 | Mise a jour des valeurs existantes en base |
| Validation | Q4 2026 | Tests end-to-end, documentation finale |

---

## Liens

- [[crm/hubspot-api]] -- Endpoints API et integration technique
- [[crm/hubspot-backlog]] -- Backlog d'optimisation CRM
- [[leadgen/cleaning-rules]] -- Regles de nettoyage du pipeline
- [[leadgen/pipeline-overview]] -- Vue d'ensemble du pipeline leadgen

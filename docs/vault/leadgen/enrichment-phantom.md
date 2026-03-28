---
title: "Enrichissement -- PhantomBuster"
id: leadgen-enrichment-phantom
type: leadgen
tags: [leadgen, enrichment, phantombuster, scraping, api]
agents: [scout]
updated: 2026-03-28
---

# Enrichissement -- PhantomBuster

PhantomBuster est l'outil d'extraction principal pour les sources Sales Navigator. Il scrape les profils LinkedIn et genere des CSV structures alimentant le reste du pipeline.

---

## API

| Parametre | Valeur |
|-----------|--------|
| Version | v2 |
| Base URL | `https://api.phantombuster.com/api/v2` |
| Authentification | API Key (header `X-Phantombuster-Key`) |
| Format reponse | JSON |

> [!info] Usage exclusif
> PhantomBuster est utilise **exclusivement** pour les sources Sales Navigator. Les autres sources (web, Trendstop) passent par des chemins differents. Voir [[leadgen/sources-linkedin]] et [[leadgen/sources-web]].

---

## Rate Limits

| Limite | Valeur | Periode | Notes |
|--------|--------|---------|-------|
| Invitations LinkedIn | 100 | par jour | Limite LinkedIn, pas PhantomBuster |
| Profils scrapes (sans email) | 2 500 | par jour | Limite PhantomBuster |
| Profils scrapes (avec email) | 250 | par jour | Extraction email tres coutere en quotas |

> [!warning] Respect des limites
> Depasser les rate limits LinkedIn entraine un risque de restriction temporaire ou permanente du compte Sales Navigator. Les Phantoms doivent etre configures avec des delais entre requetes et des limites de volume par session.

---

## Mapping des Colonnes

### Colonnes fournies par PhantomBuster

| Colonne PhantomBuster | Colonne Pipeline | Description |
|-----------------------|-----------------|-------------|
| `firstName` | `firstName` | Prenom |
| `lastName` | `lastName` | Nom de famille |
| `fullName` | `fullName` | Nom complet |
| `title` | `jobTitle` | Intitule du poste (mapping `title` → `jobTitle`) |
| `companyName` | `companyName` | Nom de l'entreprise |
| `regularCompanyUrl` | `companyLinkedinUrl` | URL LinkedIn entreprise (mapping `regularCompanyUrl` → `companyLinkedinUrl`) |
| `linkedInProfileUrl` | `linkedInProfileUrl` | URL profil LinkedIn du contact |
| `location` | `location` | Localisation declaree |
| `headline` | `headline` | Headline du profil |
| `connectionDegree` | `connectionDegree` | Degre de connexion (1er, 2e, 3e) |
| `vmid` | `vmid` | Identifiant interne LinkedIn |
| `salesNavigatorUrl` | `salesNavigatorUrl` | URL Sales Navigator du profil |

### Colonnes NON fournies par PhantomBuster

> [!warning] Champs manquants
> Ces champs ne sont **pas** disponibles dans les exports PhantomBuster. Ils doivent etre obtenus via FullEnrich ou d'autres sources.

| Colonne | Source alternative |
|---------|-------------------|
| `email` | FullEnrich |
| `phone` | FullEnrich (conditionnel) |
| `domain` | FullEnrich / Inference depuis companyName |
| `postalCode` | FullEnrich / Trendstop |
| `address` | FullEnrich / Trendstop |
| `employees` | FullEnrich / Trendstop |
| `yearFounded` | FullEnrich |
| `companyType` | FullEnrich |
| `jobStartDate` | FullEnrich |

---

## Tracabilite des Batches

Chaque batch PhantomBuster est tague avec un identifiant de creation pour assurer la tracabilite dans le pipeline.

### Format du CreationTag

```
SDR-{source}-{YYYYMMDD}-{random6}
```

**Exemples :**
- `SDR-SN-20260315-a3f8k2`
- `SDR-SN-20260328-m7p2q9`

> [!tip] Chaine de tracabilite
> Le CreationTag SDR suit le lead de l'extraction jusqu'au CRM. Il permet de remonter a tout moment la source, la date, et le batch d'origine d'un lead. Ce tag est preserve dans HubSpot comme propriete custom.

---

## Stubs API

> [!warning] Implementation incomplete
> Les 3 stubs ci-dessous couvrent les operations principales de l'API PhantomBuster v2. L'implementation complete depend de la finalisation de l'orchestrateur batch.

### Stub 1 : `launchPhantom`

```typescript
async function launchPhantom(phantomId: string, args: PhantomArgs): Promise<string> {
  // POST /api/v2/agents/launch
  // Headers: { 'X-Phantombuster-Key': API_KEY }
  // Body: { id: phantomId, argument: JSON.stringify(args) }
  // Response: { containerId: string }
  throw new Error('Not implemented: awaiting orchestrator');
}
```

### Stub 2 : `getPhantomStatus`

```typescript
async function getPhantomStatus(containerId: string): Promise<PhantomStatus> {
  // GET /api/v2/containers/fetch?id={containerId}
  // Response: { status: 'running' | 'finished' | 'error', progress: number }
  throw new Error('Not implemented: awaiting orchestrator');
}
```

### Stub 3 : `downloadResult`

```typescript
async function downloadResult(containerId: string): Promise<string> {
  // GET /api/v2/containers/fetch-result-object?id={containerId}
  // Response: { resultObject: string } // URL du CSV resultat
  throw new Error('Not implemented: awaiting orchestrator');
}
```

---

## Problemes Connus

### `linkedInProfileUrl` souvent null

Le champ `linkedInProfileUrl` est frequemment absent des exports Sales Navigator via PhantomBuster. Causes possibles :

- Profils avec parametres de confidentialite restrictifs
- Profils sans URL publique (comptes recents)
- Bug intermittent du Phantom Sales Navigator Search Export

**Contournement actuel** : reconstruction de l'URL a partir du `vmid` ou du `salesNavigatorUrl` quand disponible.

### Convention de nommage des batches

La convention de nommage des batches PhantomBuster n'est pas encore alignee avec celle du pipeline global. Points a clarifier :

- Nom du Phantom vs nom de la liste Sales Navigator
- Inclusion du hub geographique dans le nom
- Versionning des Phantoms (mise a jour de configuration)

---

## Decisions Ouvertes

| Decision | Options | Statut |
|----------|---------|--------|
| Reconstruction linkedInProfileUrl | vmid / salesNavigatorUrl / skip | En evaluation |
| Convention nommage batch | Aligner sur GMT / Propre convention | En discussion |
| Gestion multi-comptes SN | Rotation / Fixe par region | En discussion |

---

## Liens

- [[leadgen/pipeline-overview]]
- [[leadgen/sources-linkedin]]
- [[leadgen/enrichment-fullenrich]]

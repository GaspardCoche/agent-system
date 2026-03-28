---
title: "Enrichissement -- FullEnrich"
id: leadgen-enrichment-fullenrich
type: leadgen
tags: [leadgen, enrichment, fullenrich, api, automation]
agents: [aria]
updated: 2026-03-28
---

# Enrichissement -- FullEnrich

FullEnrich est le moteur d'enrichissement principal du pipeline. Il recoit les CSV issus de PhantomBuster et retourne des donnees de contact enrichies (email, telephone, donnees entreprise).

---

## Processus Actuel (Manuel)

```
PhantomBuster CSV
    |  (telechargement manuel)
    v
Upload FullEnrich (interface web)
    |  (attente traitement)
    v
Download CSV enrichi (interface web)
    |  (telechargement manuel)
    v
Merge avec donnees source → Pipeline cleaning
```

> [!warning] Processus a automatiser
> Le flux actuel est entierement manuel : upload du CSV via l'interface web, attente du traitement, puis telechargement du resultat. Chaque cycle prend 15-30 minutes d'intervention humaine. L'objectif est une automatisation complete via API.

---

## Objectif : Automatisation API

### Architecture cible

```
PhantomBuster CSV (automatique)
    |
    v
Split en batches (si > seuil)
    |
    v
Submit batch (API FullEnrich)
    |
    v
Poll status (interval 10s, timeout 10min)
    |
    v
Download results (API FullEnrich)
    |
    v
Merge avec donnees source
    |
    v
Track credits consommes
    |
    v
Pipeline cleaning
```

---

## Colonnes Enrichies

### Donnees Contact

| Colonne | Source | Description |
|---------|--------|-------------|
| `email` | FullEnrich | Adresse email professionnelle |
| `bounceStatus` | FullEnrich | Statut de validite (valid / invalid / unknown) |
| `phone` | FullEnrich (conditionnel) | Numero de telephone professionnel |

### Donnees LinkedIn (via FullEnrich)

| Colonne | Source | Description |
|---------|--------|-------------|
| `companyName` | LinkedIn enrichi | Nom de l'entreprise |
| `companyDomain` | LinkedIn enrichi | Domaine web de l'entreprise |
| `companyLinkedinUrl` | LinkedIn enrichi | URL page LinkedIn entreprise |
| `jobTitle` | LinkedIn enrichi | Intitule du poste |
| `headline` | LinkedIn enrichi | Headline du profil LinkedIn |
| `companyIndustry` | LinkedIn enrichi | Secteur d'activite |
| `companyHeadcount` | LinkedIn enrichi | Tranche d'effectifs |
| `companyType` | LinkedIn enrichi | Type d'entreprise |
| `location` | LinkedIn enrichi | Localisation du contact |

---

## Regles d'Enrichissement Conditionnel

### Enrichissement Telephone

> [!info] Enrichissement selectif
> L'enrichissement telephone consomme significativement plus de credits que l'email seul. Il n'est active que pour certains lifecycle stages avances.

| Condition | Enrichissement telephone |
|-----------|------------------------|
| Lead non qualifie | Non |
| MQL | Non |
| SQL-SDR | Oui |
| SQL-Sales | Oui |
| Client existant (re-enrichissement) | Oui |

### Regles de Skip

Pour optimiser la consommation de credits, certains leads sont exclus de l'enrichissement :

| Regle | Condition de skip |
|-------|------------------|
| Email + phone deja valides | `email` non vide ET `bounceStatus` = valid ET `phone` non vide |
| Deja enrichi dans un batch precedent | `lastEnrichedDate` < 90 jours |
| Email personnel detecte | Domaine dans blacklist (gmail, hotmail, yahoo, etc.) |

---

## Implementation Agent

### Pipeline en 6 etapes

```typescript
// Etape 1 : Split
// Decoupe le CSV source en batches de taille optimale
splitIntoBatches(csvData, batchSize)

// Etape 2 : Submit
// Soumet chaque batch a l'API FullEnrich
submitBatch(batchData) → batchId

// Etape 3 : Poll
// Verifie le statut toutes les 10 secondes, timeout a 10 minutes
pollStatus(batchId, interval=10000, timeout=600000) → status

// Etape 4 : Download
// Recupere les resultats une fois le batch termine
downloadResults(batchId) → enrichedData

// Etape 5 : Merge
// Fusionne les resultats enrichis avec les donnees source
mergeResults(sourceData, enrichedData) → mergedData

// Etape 6 : Track
// Enregistre la consommation de credits
trackCredits(batchId, creditsUsed)
```

### Logique de Merge

| Champ | Regle de merge |
|-------|---------------|
| `email` | Prendre si `Row Status` = Success |
| `bounceStatus` | Toujours prendre du resultat enrichi |
| `phone` | Prendre si enrichissement telephone active |
| Donnees entreprise (company*) | Toujours prendre des champs LinkedIn enrichi |
| `jobTitle`, `headline` | Prendre si non vide dans le resultat enrichi |

> [!tip] Priorite des sources
> En cas de conflit entre les donnees PhantomBuster et FullEnrich, les donnees FullEnrich priment pour l'email et le bounce status. Pour les donnees entreprise, les champs LinkedIn enrichis par FullEnrich sont plus complets et a jour.

---

## Stubs API

> [!warning] Implementation incomplete
> Les 3 stubs ci-dessous representent les points d'integration API non encore implementes. Les endpoints exacts et le format de requete doivent etre confirmes avec la documentation FullEnrich.

### Stub 1 : `submitBatch`

```typescript
async function submitBatch(contacts: Contact[]): Promise<string> {
  // TODO: Endpoint exact a confirmer
  // POST /api/v1/batch ? /api/v1/enrich/batch ?
  // Body: { contacts: [...], options: { includePhone: boolean } }
  // Response: { batchId: string, estimatedTime: number }
  throw new Error('Not implemented: awaiting API documentation');
}
```

### Stub 2 : `pollStatus`

```typescript
async function pollStatus(batchId: string): Promise<BatchStatus> {
  // TODO: Webhook vs polling a confirmer
  // GET /api/v1/batch/{batchId}/status ?
  // Response: { status: 'pending' | 'processing' | 'completed' | 'failed', progress: number }
  throw new Error('Not implemented: awaiting API documentation');
}
```

### Stub 3 : `downloadResults`

```typescript
async function downloadResults(batchId: string): Promise<EnrichedContact[]> {
  // TODO: Format de reponse a confirmer
  // GET /api/v1/batch/{batchId}/results ?
  // Response: { results: [...], credits: { used: number, remaining: number } }
  throw new Error('Not implemented: awaiting API documentation');
}
```

---

## Points Ouverts

| Question | Impact | Statut |
|----------|--------|--------|
| Endpoints API exacts | Bloque implementation stubs | En attente doc |
| Webhook vs polling | Architecture du monitoring | En attente doc |
| Limite de taille batch API | Strategie de split | En attente doc |
| Format CSV vs JSON | Adaptation du parser | En attente doc |
| Gestion des credits par batch | Alertes budget | En attente doc |

---

## Liens

- [[leadgen/pipeline-overview]]
- [[leadgen/enrichment-phantom]]
- [[leadgen/cleaning-rules]]
- [[tech/integrations]]

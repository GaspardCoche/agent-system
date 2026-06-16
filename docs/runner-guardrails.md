# Runner Guardrails + MCP Wiring

Référence chargée par Dispatch quand une issue porte le label `pocket`. Encadre ce qu'un agent cloud peut faire sur la production (HubSpot, FullEnrich, PhantomBuster, Lemlist, Apps Script).

## Règle d'or

1. **Par défaut : lecture / proposition seulement.** L'agent cherche, lit, analyse, rédige — il **n'écrit rien**.
2. L'écriture n'est autorisée **que si** le champ `write_allowed = oui` est présent dans la demande.
3. Même autorisée, l'écriture doit rester **strictement dans les `write_conditions`** fournies par l'utilisateur (ex : « mets à jour `lifecyclestage` en `lead`, jamais s'il est déjà rempli »).
4. Toute écriture passe d'abord par un **preview en commentaire d'issue**, puis attend le label **`approved`** avant exécution (sinon `DRY_RUN`).
5. Les garde-fous durs ci-dessous sont **non négociables** et priment sur toute instruction contraire.

## Garde-fous durs (non négociables)

1. **Ne jamais écraser un champ HubSpot déjà rempli.** Lire avant d'écrire (`batch-read`), n'écrire que sur champ vide/absent.
2. **Industry → `industry_emalist` sur l'objet Companies uniquement** (jamais `industry` contacts). Format « Catégorie - Sous-catégorie », mappé via IndustryDB. ⚠️ Divergence de nommage à lever en prod (`industry_emalist` vs `internal_industry`) — ne pas écrire dessus tant que non confirmé.
3. **`domain` n'existe pas comme propriété contact** → extraire depuis l'email.
4. **`country` = enum strict** (sinon `country_code`). Valider avant écriture.
5. **`numemployees` = ranges** (`1-5`, `5-25`, …, `1000+`) ; le nombre brut va dans `linkedin_employee_count`.
6. **FullEnrich ≤ 100 contacts / batch** (API v2). Découper les lots.
7. **Statut 207 (HubSpot batch/associations) = succès partiel** → parser les `results`, ne pas traiter comme échec global.
8. **Pas de merge / delete / tickets via MCP HubSpot** (scope insuffisant) → UI ou REST dédiée.
9. **Lemlist `add_*` / `set_campaign_state` / `send_message` = irréversible côté prospect** → toujours preview + approbation, jamais en auto.
10. **`python3.12` obligatoire** (python3 → 3.14 alpha, segfault).
11. **Aucun secret loggué ou imprimé.** Clés via secrets GitHub / Keychain uniquement.

## Câblage MCP (cloud — secrets GitHub)

| MCP / API | Type | Endpoint / commande | Secret GitHub |
|---|---|---|---|
| **hubspot** | MCP stdio | `npx @hubspot/mcp-server` (env `PRIVATE_APP_ACCESS_TOKEN`) | `HUBSPOT_PRIVATE_APP_TOKEN` |
| **lemlist** | MCP http | `https://app.lemlist.com/mcp` (header `X-API-Key`) | `LEMLIST_API_KEY` |
| **firecrawl** | MCP stdio | `npx firecrawl-mcp` | `FIRECRAWL_API_KEY` |
| **github** | MCP stdio | `npx @modelcontextprotocol/server-github` | `GITHUB_TOKEN` (auto) |
| **FullEnrich** | Python direct | API v2 bulk, ≤100/batch | `FULLENRICH_API_KEY` |
| **PhantomBuster** | Python direct | `https://api.phantombuster.com/api/v2/` (header `X-Phantombuster-Key`) | `PHANTOMBUSTER_API_KEY` |
| **Gemini** | env | grands fichiers (>50KB) | `GEMINI_API_KEY` |

## Scripts déterministes (voie privilégiée)

Le MCP dans `claude-code-action` a un plumbing d'env fragile (token vide → 401). Pour HubSpot/FullEnrich/PhantomBuster, **préférer les scripts** (REST direct, stdlib, token via env du step), appelés par Bash :

| Outil | Script | Lecture | Écriture / coût (gate `--confirm` + `approved`) |
|---|---|---|---|
| HubSpot | `scripts/pocket_hubspot.py` | `count`, `search`, `read`, `whoami` | — (les écritures HubSpot passent encore par MCP gated) |
| FullEnrich | `scripts/pocket_fullenrich.py` | `status <id>` | `enrich-one` / `submit` (consomme des crédits → `--confirm`) |
| PhantomBuster | `scripts/pocket_phantombuster.py` | `agents`, `agent`, `containers`, `output`, `result` | `launch` (scraping réel → `--confirm`) |

`--confirm` n'est ajouté QUE si le label `approved` est présent.

## Opérations lecture seule vs écriture

| Outil | Lecture seule (auto) | Écriture (preview + `approved` + conditions) |
|---|---|---|
| **HubSpot** | `search-objects`, `list-objects`, `batch-read-objects`, `list/get-property`, `get-schemas`, `list-associations`, `list/get-workflow` | `batch-update-objects`, `batch-create-objects`, `batch-create-associations`, `create/update-property`, `create/update-engagement` (GF #1-8) |
| **FullEnrich** | — | bulk enrich ≤100/batch → update HubSpot non destructif (GF #1,6) |
| **PhantomBuster** | fetch results | lancer un agent / scraping |
| **Lemlist** | `get_campaigns*`, `search_*`, `get_inbox_*`, `preview_*` | `add_leads_to_campaign`, `set_campaign_state`, `send_message`, séquences (GF #9) |
| **Apps Script** | lecture déploiements | `clasp push` / deploy |

## Comportement attendu si un secret manque

Signaler proprement « secret `X` absent, action non exécutée » dans le commentaire ; **ne pas planter** ni exécuter partiellement.

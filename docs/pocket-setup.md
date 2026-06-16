# Claude Pocket — Guide de setup

Étapes pour activer le système (≈ 15 min, une seule fois). Rien à installer sur le Mac : tout est dans GitHub + ton iPhone.

## 1. Fusionner la branche

```bash
cd ~/agent-system
git push -u origin claude-pocket
# Ouvre la PR claude-pocket → main sur GitHub, puis merge.
```

Le merge sur `main` déclenche `deploy-pages.yml` qui publie la PWA.

## 2. Activer GitHub Pages

Repo → **Settings → Pages** → Source = **GitHub Actions** (le workflow `deploy-pages.yml` s'en charge).
URL de la PWA : `https://<ton-user-github>.github.io/agent-system/pocket/`

## 3. Créer les secrets (Settings → Secrets and variables → Actions → New repository secret)

| Secret | Valeur | Obligatoire ? |
|---|---|---|
| `CLAUDE_CODE_OAUTH_TOKEN` | ton token abonnement Claude | ✅ (sûrement déjà présent) |
| `ANTHROPIC_API_KEY` | **laisser VIDE** (ne pas créer) | — bascule API plus tard |
| `HUBSPOT_PRIVATE_APP_TOKEN` | PAT app privée HubSpot | pour les actions CRM |
| `LEMLIST_API_KEY` | clé API Lemlist | pour Lemlist |
| `FULLENRICH_API_KEY` | clé FullEnrich | pour l'enrichissement |
| `PHANTOMBUSTER_API_KEY` | clé PhantomBuster | pour PhantomBuster |
| `FIRECRAWL_API_KEY` | clé Firecrawl | recherche web (souvent déjà là) |
| `GEMINI_API_KEY` | clé Gemini | gros fichiers (souvent déjà là) |

> Tant qu'un secret manque, l'agent te le signale proprement (« secret X absent ») sans planter. Tu peux donc démarrer avec seulement HubSpot et ajouter les autres au fil de l'eau.

## 4. Créer un PAT fine-grained pour la PWA

GitHub → **Settings (compte) → Developer settings → Personal access tokens → Fine-grained tokens → Generate**

- **Resource owner** : ton compte
- **Repository access** : *Only select repositories* → `agent-system`
- **Permissions → Repository** :
  - **Issues** : Read and write
  - **Actions** : Read and write
  - **Metadata** : Read (auto)
- Expiration : 90 jours (renouvelable). Copie le token (`github_pat_…`).

## 5. Installer la PWA sur l'iPhone

1. Ouvre `https://<user>.github.io/agent-system/pocket/` dans **Safari**.
2. Bouton **Partager** → **Sur l'écran d'accueil**.
3. Ouvre l'app depuis l'écran d'accueil → ⚙️ → renseigne :
   - **Repo** : `GaspardCoche/agent-system`
   - **GitHub PAT** : le token de l'étape 4
   - **Enregistrer**.

## 6. Premier test (sans risque)

1. Tape une demande simple, laisse **Autoriser l'écriture = OFF**, **Dispatch**.
2. Onglet **Actions** du repo → `Orchestrator` se lance.
3. Un commentaire de planification apparaît sur l'issue → il remonte dans la PWA (poll 15 s).
4. Pour une écriture : active le toggle + écris les conditions → l'agent poste un **preview** → tu tapes **✅ Approuver** → exécution.

## Sécurité

- Le PAT vit en `localStorage` sur ton iPhone (usage perso mono-appareil). Révocable à tout moment (Developer settings).
- Les clés API métier sont en **secrets GitHub chiffrés**, jamais dans le code ni les logs.
- Toute écriture externe est gated par le label `approved` (rien ne part sans ton tap).

## Bascule abonnement → API (le jour où le plan SDK change)

Remplir le secret `ANTHROPIC_API_KEY`. C'est tout — aucun code à changer. Le vider = retour à l'abonnement.

## Coût

≈ **0 €/mois** : compute via abonnement, GitHub Actions (2000 min/mois gratuits) + Pages gratuits. Seuls tes abonnements data existants (FullEnrich, PhantomBuster) restent à l'usage.

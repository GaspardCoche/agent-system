---
title: Nexus — Mémoire & Patterns
id: agents-nexus-memory
type: agent
tags: [nexus, google-ads, memory, patterns]
agents: [nexus]
updated: 2026-04-06
---

# Nexus — Mémoire & Patterns

*Lie a [[INDEX]], [[campaigns/google-ads]], [[operations/decisions]], [[business/strategy]], [[tech/mcp-servers]], [[operations/kpis]]*

> Nexus met à jour ce fichier après chaque run avec ses apprentissages.
> **Lire avant chaque audit Google Ads.**

---

## Compte Google Ads -- Etat

```
Status config  : Configure
Account ID     : 7251903503 (EMAsphere)
Derniere connexion : --
Dry run mode   : true (defaut jusqu'a config)
```

---

## Regles critiques Google Ads MCP

> **Ces regles sont absolues. Les enfreindre provoque des erreurs en cascade.**

1. **JAMAIS `.type` dans `conditions`** -- provoque une erreur "type" + cascade d'annulation
2. **JAMAIS d'appels paralleles** -- si 1 echoue, tous sont annules. Toujours sequentiel, 1 requete a la fois
3. **JAMAIS `metrics.optimization_score` avec des segments de date** -- incompatible
4. **JAMAIS de metriques sur `ad_group_criterion`** -- utiliser `keyword_view` a la place

Voir [[tech/mcp-servers]] pour la configuration MCP complete.

---

## Patterns d'optimisation découverts

> *Nexus enrichit cette section après chaque analyse*

| Pattern | Impact | Fréquence | Validé |
|---------|--------|----------|--------|
| Mots-clés négatifs manquants | Élevé | Très fréquent | — |
| Enchères mobile surestimées | Moyen | Fréquent | — |
| RSA assets < 5 | Moyen | Fréquent | — |
| Extensions incomplètes (sitelinks/callouts) | Moyen | Fréquent | — |

---

## Historique des runs

| Date | Type | Score | Résumé | Run ID |
|------|------|-------|--------|--------|
| 2026-04-06 | weekly_audit (template) | 58/100 (estimé) | Template — credentials_ok=false (2e run consécutif) | #24025730664 |
| 2026-03-24 | dry_run | 58/100 | Template — compte non configuré | #23487432218 |

---

## Erreurs rencontrées

| Date | Erreur | Résolution |
|------|--------|-----------|
| — | — | — |

---

## Optimisations appliquées (live)

> *Uniquement les optimisations exécutées en mode réel (dry_run=false)*

*Aucune encore — en attente de configuration du compte*

---

## Prochains runs planifiés

- [ ] Configurer les 4 secrets Google Ads (DEVELOPER_TOKEN, CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)
- [ ] Relancer après configuration pour obtenir un audit réel
- [ ] Audit hebdo : chaque lundi 6h UTC (à configurer dans nexus.yml)

## Note escalade

> 2026-04-06 : **2e run consécutif en template mode** (2026-03-24 + 2026-04-06).
> Suggéré : alerter via Iris si configuration non faite après 3 runs template consécutifs.

---

*Nexus met à jour ce fichier après chaque run.*

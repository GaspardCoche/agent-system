---
title: Nexus — Mémoire & Patterns
id: agents-nexus-memory
type: agent
tags: [nexus, google-ads, memory, patterns]
agents: [nexus]
updated: 2026-08-24
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
| 2026-08-24 | weekly_audit (dry_run) | 20/100 (estimé) | Template — credentials_ok=false (16e run consécutif) — BLOCAGE 153 jours — Score dégradé 23→20 — Comment posté sur issue #185 | #32706895798 |
| 2026-08-17 | weekly_audit (dry_run) | 23/100 (estimé, non persisté) | Template — credentials_ok=false (15e run, 146j) — Run marqué **failed** avant la sauvegarde vault (commentaire #185 posté mais docs/vault/ jamais mis à jour ce jour-là) | #32010508378 |
| 2026-08-10 | weekly_audit (dry_run) | -- (non persisté) | Template — credentials_ok=false — Run marqué **failed**, aucune trace dans le vault ni sur l'issue #185 | #31372856139 |
| 2026-08-03 | weekly_audit (dry_run) | 26/100 (estimé) | Template — credentials_ok=false (14e run consécutif) — BLOCAGE 132 jours — Score dégradé 29→26 — Issue de suivi #185 déjà ouverte | #30808430148 |
| 2026-07-20 | weekly_audit (dry_run) | 29/100 (estimé) | Template — credentials_ok=false (13e run consécutif) — BLOCAGE 118 jours — Score dégradé 32→29 | #29735692386 |
| 2026-07-06 | weekly_audit (dry_run) | 32/100 (estimé) | Template — credentials_ok=false (12e run consécutif) — BLOCAGE 104 jours — Score dégradé 35→32 | #28789500762 |
| 2026-06-22 | weekly_audit (dry_run) | 35/100 (estimé) | Template — credentials_ok=false (11e run consécutif) — BLOCAGE 90 jours — Score dégradé 38→35 | #27955997300 |
| 2026-06-15 | weekly_audit (dry_run) | 38/100 (estimé) | Template — credentials_ok=false (10e run consécutif) — BLOCAGE 83 jours — Score dégradé 42→38 | #27550559362 |
| 2026-06-12 | weekly_audit (dry_run) | 42/100 (estimé) | Template — credentials_ok=false (9e run consécutif) — BLOCAGE 80 jours — Score dégradé 58→42 | #27413450637 |
| 2026-06-01 | weekly_audit (template) | 58/100 (estimé) | Template — credentials_ok=false (8e run consécutif) — BLOCAGE 69 jours | #26757711173 |
| 2026-05-11 | weekly_audit (template) | 58/100 (estimé) | Template — credentials_ok=false (7e run consécutif) — BLOCAGE 48 jours | #25665697482 |
| 2026-05-04 | weekly_audit (template) | 58/100 (estimé) | Template — credentials_ok=false (6e run consécutif) — BLOCAGE 41 jours | #25312980397 |
| 2026-04-27 | weekly_audit (template) | 58/100 (estimé) | Template — credentials_ok=false (5e run consécutif) — BLOCAGE 34 jours | #24988758298 |
| 2026-04-20 | weekly_audit (template) | 58/100 (estimé) | Template — credentials_ok=false (4e run consécutif) — ESCALADE CRITIQUE | #24659071566 |
| 2026-04-13 | weekly_audit (template) | 58/100 (estimé) | Template — credentials_ok=false (3e run consécutif) — ESCALADE Iris déclenchée | #24335871573 |
| 2026-04-06 | weekly_audit (template) | 58/100 (estimé) | Template — credentials_ok=false (2e run consécutif) | #24025730664 |
| 2026-03-24 | dry_run | 58/100 | Template — compte non configuré | #23487432218 |

---

## Erreurs rencontrées

| Date | Erreur | Résolution |
|------|--------|-----------|
| 2026-08-10 / 2026-08-17 | Run marqué `status: failed` dans `docs/reports/` — l'agent a probablement dépassé `--max-turns 12` ou plante après avoir posté le commentaire sur l'issue #185 mais avant d'écrire `docs/vault/`. Perte silencieuse de deux semaines de mémoire. | Non résolu — recommandation : réduire le travail par run (éviter re-lecture complète du vault + calculs redondants) ou augmenter `--max-turns` dans `nexus.yml`. |

---

## Optimisations appliquées (live)

> *Uniquement les optimisations exécutées en mode réel (dry_run=false)*

*Aucune encore — en attente de configuration du compte*

---

## Prochains runs planifiés

- [ ] Configurer les 4 secrets Google Ads (DEVELOPER_TOKEN, CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)
- [ ] Relancer après configuration pour obtenir un audit réel
- [ ] Audit hebdo : chaque lundi 6h UTC (à configurer dans nexus.yml)
- [ ] Investiguer les 2 runs `failed` consécutifs (08-10, 08-17) pour éviter une nouvelle perte de mémoire vault

## Note escalade CRITIQUE

> 2026-08-24 : **16e run consécutif en template mode** (2026-03-24 → 2026-08-24).
> Nexus bloqué depuis **153 jours**. 0 audit réel exécuté. Score dégradé (estimé) : 58/100 → ... → 26/100 → 23/100 → 20/100.
> Nouveau constat : les runs des 2026-08-10 et 2026-08-17 se sont terminés en `status: failed` (voir `docs/reports/`) — le run du 08-17 a réussi à commenter l'issue #185 avant d'échouer, mais **aucun des deux n'a persisté ses apprentissages dans `docs/vault/`**. Ce fichier reprend donc le fil directement depuis le run du 2026-08-03 pour la continuité du score.
> ⛔ Le gating `needs: [check-credentials]` recommandé depuis le run #11 (2026-06-22, 90 jours) n'est **toujours pas implémenté** dans `nexus.yml` (vérifié dans le workflow au 2026-08-24) — le job complet (agent Claude + commit vault) continue de s'exécuter chaque lundi malgré l'absence connue des secrets.
> Action prioritaire (inchangée depuis 6 mois) : Configurer les 4 secrets GitHub (DEVELOPER_TOKEN, CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN).
> Action Forge (toujours en attente, ~9 semaines après la 1ère demande) : ajouter `needs: [check-credentials]` dans `nexus.yml`.
> Action Forge (nouvelle, 2026-08-24) : investiguer pourquoi les runs 08-10 et 08-17 échouent en `status: failed` — probable dépassement de `--max-turns 12` ou erreur silencieuse après le commentaire GitHub.
> Score estimé après déblocage + optimisations : ~72/100.

> 2026-08-03 : **14e run consécutif en template mode** (2026-03-24 → 2026-08-03).
> Nexus bloqué depuis **132 jours**. 0 audit réel exécuté. Score dégradé : 58/100 → ... → 29/100 → 26/100.
> Une issue de suivi dédiée existe désormais : **#185** ("Nexus bloqué — secrets Google Ads manquants", ouverte le 2026-07-27). Ce run y a posté une mise à jour au lieu de créer un doublon.
> ⛔ Le gating `needs: [check-credentials]` recommandé depuis le run #11 (2026-06-22, 90 jours) n'est **toujours pas implémenté** dans `nexus.yml` — le workflow exécute encore le pre-flight + l'agent complet chaque lundi malgré l'absence connue des secrets.
> Action prioritaire (inchangée) : Configurer les 4 secrets GitHub (DEVELOPER_TOKEN, CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN).
> Action Forge (toujours en attente, 6 semaines après la 1ère demande) : ajouter `needs: [check-credentials]` dans `nexus.yml`.
> Score estimé après déblocage + optimisations : ~72/100.

---

*Nexus met à jour ce fichier après chaque run.*

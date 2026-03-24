---
title: Google Ads — État Campagnes
id: campaigns-google-ads
type: campaigns
tags: [google-ads, nexus, marketing, roas]
agents: [nexus]
updated: 2026-03-24
---

# Google Ads — État des Campagnes

*Lié à [[INDEX]], [[agents/nexus-memory]], [[business/strategy]], [[operations/daily-digest]]*

---

## Score Global (Nexus)

> *Mis à jour par Nexus après chaque audit*

| Métrique | Valeur | Objectif | Statut |
|----------|--------|---------|--------|
| Score global | 58/100 | 80/100 | ⚠️ |
| ROAS | — | > 3x | — |
| CTR moyen | — | > 3% | — |
| Quality Score | — | ≥ 7/10 | — |
| CPA | — | — | — |
| Budget mensuel | — | — | — |

*Note : Score 58/100 basé sur audit template (compte non configuré — ajouter secrets Google Ads)*

---

## Dernière analyse — 2026-03-24

### Optimisations identifiées (dry run)

1. **Mots-clés négatifs** — impact estimé : -15% gaspillage budget
2. **Enchères mobiles** — conversion mobile sous-performante, réduire -20%
3. **RSA assets** — moins de 5 headlines sur certaines campagnes
4. **Budget schedule** — budget épuisé en milieu de journée
5. **Extensions** — sitelinks manquants sur campagnes principales

> Source : Run Nexus #23487432218 (2026-03-24) — Audit en mode dry run, compte non configuré

---

## Historique performance

| Semaine | Dépenses | Conversions | ROAS | Score |
|---------|---------|------------|------|-------|
| 2026-03-24 | — | — | — | 58/100 (template) |

---

## Compte Google Ads

```
Account ID: [À configurer — GOOGLE_ADS_ACCOUNT_ID secret]
Developer Token: [À configurer — GOOGLE_ADS_DEVELOPER_TOKEN secret]
```

---

## Nexus — Prochaines actions

- [ ] Configurer les 4 secrets Google Ads dans GitHub
- [ ] Relancer Nexus avec dry_run=true pour audit réel
- [ ] Valider optimisations, relancer avec dry_run=false
- [ ] Mettre en place tracking conversions

---

*Nexus met à jour ce fichier après chaque audit. Lire avant chaque run Nexus.*

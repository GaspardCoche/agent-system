---
title: Google Ads -- Etat Campagnes
id: campaigns-google-ads
type: campaigns
tags: [google-ads, nexus, marketing, roas, emasphere]
agents: [nexus]
updated: 2026-03-28
---

# Google Ads -- Etat des Campagnes

*Lie a [[INDEX]], [[agents/nexus-memory]], [[business/strategy]], [[business/vision]], [[operations/kpis]], [[operations/daily-digest]]*

---

## Compte EMAsphere

| Attribut | Valeur |
|----------|--------|
| **Customer ID** | `7251903503` |
| **Type de compte** | Standard |
| **Marches cibles** | France, Belgique (FR + NL), UK |
| **Langues des campagnes** | Francais, Neerlandais, Anglais |
| **Agent responsable** | [[agents/nexus-memory]] |

> **Regles critiques pour les requetes GAQL** (voir aussi [[tech/integrations]]) :
> - JAMAIS `.type` dans `conditions` -- provoque une erreur "type" + cascade d'annulation
> - JAMAIS appels paralleles -- si 1 echoue, tous sont annules
> - JAMAIS `metrics.optimization_score` avec segments de date
> - JAMAIS metriques sur `ad_group_criterion` -- utiliser `keyword_view`
> - Toujours sequentiel, 1 requete a la fois

---

## Score Global (Nexus)

> Mis a jour par Nexus apres chaque audit

| Metrique | Valeur | Objectif | Statut |
|----------|--------|---------|--------|
| Score global | 58/100 | 80/100 | A ameliorer |
| ROAS | -- | > 3x | -- |
| CTR moyen | -- | > 3% | -- |
| Quality Score | -- | >= 7/10 | -- |
| CPA | -- | -- | -- |
| Budget mensuel | -- | -- | -- |

*Note : Score 58/100 base sur audit template (compte non configure -- ajouter secrets Google Ads)*

---

## Audits automatises par Nexus

L'agent [[agents/nexus-memory]] realise des audits automatises du compte Google Ads selon le protocole suivant :

### Perimetre d'audit

| Dimension | Metriques analysees | Frequence |
|-----------|-------------------|-----------|
| **Performance campagnes** | Impressions, clics, CTR, CPC, conversions, ROAS | Hebdomadaire |
| **Mots-cles** | Quality Score, taux d'impression, CPC moyen | Hebdomadaire |
| **Annonces (RSA)** | Nombre d'assets, force de l'annonce, CTR | Bimensuel |
| **Budget** | Repartition, epuisement horaire, opportunites | Hebdomadaire |
| **Extensions** | Sitelinks, callouts, structured snippets | Mensuel |
| **Encheres** | Strategie, ajustements device/geo/audience | Mensuel |

### Flow d'audit Nexus

```
1. Lecture vault : campaigns/google-ads.md + agents/nexus-memory.md
2. Requetes GAQL sequentielles (JAMAIS en parallele)
3. Analyse des donnees et scoring
4. Generation des recommandations
5. Mise a jour de ce fichier + nexus-memory
6. Si dry_run=false : application des optimisations
```

---

## Derniere analyse -- 2026-03-24

### Optimisations identifiees (dry run)

1. **Mots-cles negatifs** -- impact estime : -15% gaspillage budget
2. **Encheres mobiles** -- conversion mobile sous-performante, reduire -20%
3. **RSA assets** -- moins de 5 headlines sur certaines campagnes
4. **Budget schedule** -- budget epuise en milieu de journee
5. **Extensions** -- sitelinks manquants sur campagnes principales

> Source : Run Nexus #23487432218 (2026-03-24) -- Audit en mode dry run, compte non configure

---

## Structure de campagnes cible

> Structure recommandee pour le compte EMAsphere, alignee sur la [[business/strategy]].

| Campagne | Marche | Langue | Objectif | Budget |
|----------|--------|--------|---------|--------|
| Search -- CFO FR | France | FR | Leads demo | A definir |
| Search -- Finance BE-FR | Belgique (Wallonie) | FR | Leads demo | A definir |
| Search -- Finance BE-NL | Belgique (Flandre) | NL | Leads demo | A definir |
| Search -- Finance UK | UK | EN | Leads demo | A definir |
| Brand | Tous | Multi | Protection marque | A definir |

---

## Historique performance

| Semaine | Depenses | Conversions | ROAS | Score |
|---------|---------|------------|------|-------|
| 2026-03-24 | -- | -- | -- | 58/100 (template) |

---

## KPIs Google Ads suivis

> Consolides dans [[operations/kpis]].

| KPI | Objectif | Mesure |
|-----|---------|--------|
| ROAS | > 3x | Depenses / valeur conversions |
| CTR | > 3% | Clics / impressions |
| Quality Score moyen | >= 7/10 | Moyenne ponderee par impressions |
| CPA | A definir | Depenses / conversions |
| Taux d'impression Search | > 70% | Impressions / impressions eligibles |
| Budget utilise | > 90% | Depenses / budget alloue |

---

## Nexus -- Prochaines actions

- [ ] Configurer les 4 secrets Google Ads dans GitHub
- [ ] Relancer Nexus avec `dry_run=true` pour audit reel
- [ ] Valider optimisations, relancer avec `dry_run=false`
- [ ] Mettre en place tracking conversions
- [ ] Creer la structure de campagnes multilingues
- [ ] Definir les budgets par marche
- [ ] Implementer les mots-cles negatifs identifies

---

*Nexus met a jour ce fichier apres chaque audit. Lire avant chaque run Nexus. Voir [[agents/nexus-memory]] pour l'historique des apprentissages et [[business/strategy]] pour l'alignement strategique.*

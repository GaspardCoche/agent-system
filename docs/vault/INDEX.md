---
title: VAULT-INDEX
id: index
type: index
tags: [index, hub, system]
agents: [all]
updated: 2026-03-24
---

# VAULT-INDEX — Centre de Connaissance

> Base de connaissance vivante du système multi-agents. **Lire ce fichier en début de chaque session.**
> Chaque agent enrichit ce vault après chaque run. Le graph est visible dans le dashboard → onglet Graph.

---

## Business

- [[business/vision]] — Vision & Mission de l'entreprise
- [[business/strategy]] — Stratégie business actuelle
- [[business/roadmap]] — Roadmap & priorités

## Prospects & CRM

- [[prospects/pipeline]] — Pipeline leads actif (Scout + Aria)

## Campagnes Marketing

- [[campaigns/google-ads]] — État campagnes Google Ads (Nexus)

## Opérations Quotidiennes

- [[operations/daily-digest]] — Digest email du jour (Iris)
- [[operations/decisions]] — Décisions d'architecture & stratégiques

## Contenu

- [[content/social-media]] — Stratégie contenu & idées

## Mémoire Agents

- [[agents/nexus-memory]] — Nexus : patterns ads, historique optimisations
- [[agents/iris-memory]] — Iris : profils expéditeurs, patterns email
- [[agents/scout-memory]] — Scout : sources web validées, patterns scraping
- [[agents/sage-memory]] — Sage : améliorations, skills candidats
- [[agents/dispatch-log]] — Dispatch : historique orchestrations

---

## Contexte Système

```
Agents actifs : Orchestrator, Iris, Scout, Aria, Nexus, Sage, Ralph, Forge, Sentinel, Lumen
Repo GitHub   : gcoche-bit/agent-system
Dashboard     : Netlify (onglets Runs / Status / Graph)
Vault         : docs/vault/ (ce répertoire)
```

## Comment utiliser ce vault

| Qui | Quand | Quoi |
|-----|-------|------|
| **Agents** | Début de chaque tâche | Lire INDEX + fichier mémoire de l'agent |
| **Agents** | Fin de chaque run | Mettre à jour le(s) fichier(s) concerné(s) |
| **Toi** | Session de travail | Lire INDEX pour contexte complet |
| **Toi** | Revue hebdo | Ouvrir dans Obsidian, explorer le graph |
| **Sage** | Dimanche | Analyser vault, proposer améliorations |

---

## Dernière mise à jour système

| Agent | Dernier run | Statut |
|-------|------------|--------|
| Nexus | 2026-03-24 | ✅ Audit dry-run terminé |
| Sage | 2026-03-24 | ✅ Weekly run terminé |
| Iris | — | ⚙️ Configurer GMAIL_TOKEN_JSON |
| Scout | — | ⚙️ Configurer FIRECRAWL_API_KEY |
| Aria | — | ⚙️ Configurer FULLENRICH + HUBSPOT |

---

*Ce fichier est le nœud central du knowledge graph. Chaque `[[lien]]` est une connexion dans le graph.*

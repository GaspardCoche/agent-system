---
title: "Datasette 1.0a38 corrige une faille d'injection SQL"
source: "Simon Willison"
url: "https://simonwillison.net/2026/Aug/6/datasette/#atom-everything"
category: "Code & Dev"
importance: "must_read"
date: 2026-08-07
tags: ["Datasette"]
---

# Datasette 1.0a38 corrige une faille d'injection SQL

**Source:** [Simon Willison](https://simonwillison.net/2026/Aug/6/datasette/#atom-everything) | **Categorie:** Code & Dev | **Importance:** must_read

Cette version corrige une vulnérabilité d'injection SQL touchant les instances Datasette qui exposent un mélange de tables publiques et privées dans la même base avec le système de permissions. Le correctif est aussi rétroporté dans Datasette 0.65.3 pour les installations restées sur l'ancienne branche. Un patch à appliquer sans attendre si tu sers des données privées.

---
*Sauvegarde depuis AI Intelligence Briefing du 2026-08-07*

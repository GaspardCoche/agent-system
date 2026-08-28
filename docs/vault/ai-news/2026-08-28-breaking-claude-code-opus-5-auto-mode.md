---
title: "Breaking Claude Code Opus 5 Auto Mode"
source: "Simon Willison"
url: "https://simonwillison.net/2026/Aug/27/breaking-claude-code-opus-5-auto-mode/"
category: "Code & Dev"
importance: "must_read (top story)"
date: 2026-08-28
tags: ["Anthropic", "Claude Code"]
---

# Breaking Claude Code Opus 5 Auto Mode

**Source:** [Simon Willison](https://simonwillison.net/2026/Aug/27/breaking-claude-code-opus-5-auto-mode/) | **Categorie:** Code & Dev | **Importance:** must_read (top story)

Anthropic mise beaucoup sur le mode Auto de Claude Code, devenu le défaut, pour protéger son agent de code contre les injections de prompt. Le chercheur Johann Rehberger — l'une des références du domaine — décrit une attaque qui fonctionne 80 % du temps : Claude Code télécharge et décompresse une archive zip, puis exécute du code qui importe `base64` sans voir qu'un fichier local `struct.py` malveillant extrait de l'archive s'exécute au passage. Pire, dans plusieurs cas le classifieur de sécurité a autorisé la création du processus malveillant… puis bloqué la commande de Claude qui tentait de le tuer — le garde-fou devient partie du problème. La conclusion partagée : le seul moyen sûr d'exécuter un agent exposé à un adversaire est un vrai bac à sable (conteneur/VM), avec egress réseau restreint et sans accès aux clés SSH, credentials cloud ou répertoire home. Un signal d'alarme direct pour quiconque fait tourner des agents de code en continu.

---
*Sauvegarde depuis AI Intelligence Briefing du 2026-08-28*

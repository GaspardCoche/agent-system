    ---
    title: "External sandboxes for coding agents"
    source: "Simon Willison"
    url: "https://simonwillison.net/2026/Nov/17/external-sandboxes-for-coding-agents/"
    category: "Code & Dev"
    importance: "must_read"
    date: 2026-11-18
    tags: ["Prime Radiant"]
    ---

    # External sandboxes for coding agents

![External sandboxes for coding agents](https://static.simonwillison.net/static/2026/sandbox-proxy.png)

    **Source:** [Simon Willison](https://simonwillison.net/2026/Nov/17/external-sandboxes-for-coding-agents/) | **Categorie:** Code & Dev | **Importance:** must_read

    Willison détaille, avec Prime Radiant, le pattern « external sandbox » : le code exécuté par l'agent tourne dans un bac à sable dédié pendant que l'agent reste à l'extérieur, limitant les dégâts en cas d'erreur ou d'injection de prompt. Trois implémentations open-source sont publiées (v86/WebAssembly, Apple Containers, Quicksand/QEMU) exposant la même API localhost, branchable sur Claude Code, Codex ou Pi. Un proxy allow-list HTTP/HTTPS et un mécanisme de substitution de credentials évitent de partager tes secrets avec l'agent.

    ---
    *Sauvegarde depuis AI Intelligence Briefing du 2026-11-18*

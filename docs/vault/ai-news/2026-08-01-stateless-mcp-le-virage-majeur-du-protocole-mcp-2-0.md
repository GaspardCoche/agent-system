    ---
    title: "Stateless MCP : le virage majeur du protocole (MCP 2.0)"
    source: "Simon Willison"
    url: "https://simonwillison.net/2026/Jul/31/stateless-mcp/#atom-everything"
    category: "Outils & Plateformes"
    importance: "must_read (top story)"
    date: 2026-08-01
    tags: ["Anthropic", "MCP"]
    ---

    # Stateless MCP : le virage majeur du protocole (MCP 2.0)

![Stateless MCP : le virage majeur du protocole (MCP 2.0)](https://raw.githubusercontent.com/simonw/til/refs/heads/main/llms/claude-add-custom-connector-dialog.webp)

    **Source:** [Simon Willison](https://simonwillison.net/2026/Jul/31/stateless-mcp/#atom-everything) | **Categorie:** Outils & Plateformes | **Importance:** must_read (top story)

    Le spec Model Context Protocol du 28 juillet 2026 (surnommé MCP 2.0) introduit un mode 'stateless' qui constitue le changement le plus important depuis le lancement du protocole. En supprimant l'état de session côté serveur, il rend les serveurs MCP nettement plus faciles à déployer et à scaler derrière des load balancers classiques — exactement le blocage qui freinait l'adoption en entreprise (Ars Technica souligne le même point). Une nouvelle politique de dépréciation garantit aussi que les fonctionnalités ne disparaîtront plus du jour au lendemain, ce qui rassure les équipes qui bâtissent en production. Cela a immédiatement relancé l'écosystème d'outils (mcp-explorer, datasette-mcp, llm-mcp-client). Pour qui construit sur MCP, c'est le moment de tester la migration.

    ---
    *Sauvegarde depuis AI Intelligence Briefing du 2026-08-01*

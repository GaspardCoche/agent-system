# Skill System

Les skills remplacent les appels MCP répétitifs par des scripts Python autonomes.
**Avantage** : moins de tokens, démarrage plus rapide, testables en local.

## Comment utiliser un skill

1. Vérifier le registry :
```bash
python3 -c "import json; r=json.load(open('skills/registry.json')); print([s for s in r['skills'] if s['status']=='validated'])"
```

2. Si skill validé → utiliser le script Python :
```bash
python3 skills/validated/firecrawl_scrape.py --url https://example.com
```

3. Sinon → utiliser le MCP correspondant et noter le pattern dans `retrospective.mcp_patterns`

## Pipeline de validation

```
MCP utilisé 3+ fois/semaine
         ↓
  Sage détecte le pattern
         ↓
  Skill ajouté comme "candidate"
         ↓
  Sage écrit skills/candidates/<name>.py
         ↓
  Tests d'équivalence (3 exemples réels)
         ↓
  Skill promu "validated" → skills/validated/
         ↓
  registry.json mis à jour
         ↓
  CLAUDE.md : les agents utilisent désormais le script
```

## Structure des fichiers

```
skills/
├── README.md           # Ce fichier
├── registry.json       # État de tous les skills
├── candidates/         # Scripts en cours de validation
│   └── <skill>.py
└── validated/          # Scripts prêts à l'emploi
    └── <skill>.py
```

## Ajouter un skill manuellement

1. Écrire `skills/candidates/<nom>.py` (voir template ci-dessous)
2. Tester sur 3 exemples réels
3. Si ok : copier dans `skills/validated/`
4. Mettre à jour `skills/registry.json` : status → "validated"

## Template skill

```python
#!/usr/bin/env python3
"""
Skill: <nom>
Remplace: <mcp_tool_name>
Usage: python3 skills/validated/<nom>.py --arg1 VALUE
Variables d'env: API_KEY_NAME
"""
import argparse, json, os, sys
try:
    import requests
except ImportError:
    print("pip install requests", file=sys.stderr); sys.exit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arg1", required=True)
    args = parser.parse_args()

    api_key = os.environ.get("API_KEY_NAME")
    if not api_key:
        print("Error: API_KEY_NAME not set", file=sys.stderr); sys.exit(1)

    # Logique principale
    result = {}
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
```

#!/usr/bin/env python3.12
"""Lit le JSON de sortie de claude-code-action et détermine si le run a réussi.

claude-code-action écrit le flux d'événements dans
/home/runner/work/_temp/claude-execution-output.json. Le dernier événement
`type=result` porte `is_error`. On considère le run réussi seulement s'il
existe un événement result sans is_error.

Sort 'true' (succès) ou 'false' (échec). Ne lève jamais : fichier absent /
illisible / pas de result = 'false' (fail-safe : on préfère signaler un
faux échec qu'un faux succès silencieux).

Usage: pocket_check_result.py [chemin]
"""
import json
import sys

DEFAULT = "/home/runner/work/_temp/claude-execution-output.json"


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    try:
        with open(path) as f:
            data = json.load(f)
    except Exception:
        print("false")
        return
    events = data if isinstance(data, list) else [data]
    results = [e for e in events if isinstance(e, dict) and e.get("type") == "result"]
    print("true" if (results and not results[-1].get("is_error")) else "false")


if __name__ == "__main__":
    main()

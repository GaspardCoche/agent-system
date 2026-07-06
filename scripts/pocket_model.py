#!/usr/bin/env python3.12
"""Déduit l'ID de modèle Claude à partir du corps d'une tâche Pocket.

Le composer écrit une ligne « ### Modèle: <nom> » dans l'issue. On mappe le nom
convivial vers l'ID exact. Défaut = Opus 4.8 (meilleure qualité). Tous ces
modèles tournent sous l'abonnement (0 € API).

Entrée : texte sur stdin (ou 1er argument). Sortie : l'ID de modèle.
"""
import re
import sys

DEFAULT = "claude-opus-4-8"
MAP = {
    "fable": "claude-fable-5",
    "fable-5": "claude-fable-5",
    "fable 5": "claude-fable-5",
    "opus": "claude-opus-4-8",
    "opus-4-8": "claude-opus-4-8",
    "opus 4.8": "claude-opus-4-8",
    "sonnet": "claude-sonnet-5",
    "sonnet-5": "claude-sonnet-5",
    "haiku": "claude-haiku-4-5-20251001",
}


def resolve(text):
    text = (text or "").lower()
    m = re.search(r"#{0,3}\s*mod[eè]le\s*[:=]\s*([a-z0-9 .\-]+)", text)
    token = ""
    if m:
        token = m.group(1).strip()
    else:
        # Repli : un nom de modèle mentionné n'importe où.
        for name in ("fable", "sonnet", "haiku", "opus"):
            if name in text:
                token = name
                break
    if not token:
        return DEFAULT
    # Normalise et cherche la meilleure correspondance.
    for key in sorted(MAP, key=len, reverse=True):
        if token.startswith(key) or key in token:
            return MAP[key]
    return DEFAULT


if __name__ == "__main__":
    data = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    print(resolve(data))

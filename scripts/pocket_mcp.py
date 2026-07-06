#!/usr/bin/env python3.12
"""Gère les serveurs MCP ajoutés par l'utilisateur depuis l'app (panneau admin).

Source : pocket-config/mcp.json — liste de serveurs MCP décrits par l'app :
[
  {
    "name": "playwright",
    "enabled": true,
    "transport": "stdio",                # "stdio" | "http"
    "command": "npx", "args": ["-y", "@playwright/mcp@latest"],
    "url": "", "headers": {},            # si transport http
    "env": {"KEY": "..."},
    "allowedTools": ["*"]                # "*" = tous les outils de ce serveur
  }
]

Sous-commandes :
  merge --into <config.json>  : fusionne les serveurs activés dans la config MCP
                                passée à claude-code-action.
  tools                       : imprime la liste d'outils autorisés (CSV) pour
                                --allowedTools (mcp__<name>__* si "*").

Best-effort : fichier absent / illisible = no-op. Ne lève jamais.
"""
import argparse
import json

CONFIG = "pocket-config/mcp.json"


def load_servers():
    try:
        with open(CONFIG) as f:
            data = json.load(f)
    except Exception:
        return []
    servers = data if isinstance(data, list) else data.get("servers", [])
    return [s for s in servers if isinstance(s, dict) and s.get("enabled", True) and s.get("name")]


def to_mcp_entry(s):
    if s.get("transport") == "http":
        entry = {"type": "http", "url": s.get("url", "")}
        if s.get("headers"):
            entry["headers"] = s["headers"]
    else:
        entry = {"command": s.get("command", "npx"), "args": s.get("args", [])}
        if s.get("env"):
            entry["env"] = s["env"]
    return entry


def cmd_merge(into):
    servers = load_servers()
    if not servers:
        return
    try:
        with open(into) as f:
            cfg = json.load(f)
    except Exception:
        cfg = {"mcpServers": {}}
    cfg.setdefault("mcpServers", {})
    for s in servers:
        cfg["mcpServers"][s["name"]] = to_mcp_entry(s)
    with open(into, "w") as f:
        json.dump(cfg, f)
    print(f"pocket_mcp: fusionné {len(servers)} serveur(s) utilisateur")


def cmd_tools():
    out = []
    for s in load_servers():
        allowed = s.get("allowedTools") or ["*"]
        if "*" in allowed:
            out.append(f"mcp__{s['name']}__*")
        else:
            out.extend(f"mcp__{s['name']}__{t}" for t in allowed)
    print(",".join(out))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("merge")
    m.add_argument("--into", required=True)
    sub.add_parser("tools")
    args = ap.parse_args()
    if args.cmd == "merge":
        cmd_merge(args.into)
    elif args.cmd == "tools":
        cmd_tools()


if __name__ == "__main__":
    main()

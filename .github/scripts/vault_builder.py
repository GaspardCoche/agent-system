#!/usr/bin/env python3
"""
vault_builder.py — Parses docs/vault/*.md → docs/data/graph.json

Reads all Markdown files in docs/vault/, extracts:
  - YAML frontmatter (id, title, type, tags, agents, updated)
  - [[wikilinks]] as edges

Outputs docs/data/graph.json for D3.js visualization in the dashboard.
"""

import json
import os
import re
import sys
from pathlib import Path

VAULT_DIR = Path("docs/vault")
OUTPUT_FILE = Path("docs/data/graph.json")

# Node type → color mapping (matches dashboard CSS)
TYPE_COLORS = {
    "index":      "#e8e84a",
    "business":   "#58a6ff",
    "leadgen":    "#2ea043",
    "crm":        "#417723",
    "prospects":  "#3fb950",
    "campaigns":  "#ffa657",
    "operations": "#bc8cff",
    "content":    "#d29922",
    "agent":      "#f85149",
    "tech":       "#79c0ff",
    "security":   "#f778ba",
}

DEFAULT_COLOR = "#8b949e"


def parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from markdown content."""
    fm = {}
    if not content.startswith("---"):
        return fm
    end = content.find("\n---", 3)
    if end == -1:
        return fm
    yaml_block = content[4:end]
    for line in yaml_block.split("\n"):
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        # Parse lists like [a, b, c]
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1]
            fm[key] = [v.strip() for v in inner.split(",") if v.strip()]
        else:
            fm[key] = val
    return fm


def extract_wikilinks(content: str) -> list[str]:
    """Extract all [[wikilink]] targets from markdown content."""
    # Match [[target]] or [[target|alias]]
    raw = re.findall(r"\[\[([^\]]+)\]\]", content)
    targets = []
    for r in raw:
        # Strip alias (e.g. [[path/file|Alias]] → path/file)
        target = r.split("|")[0].strip()
        targets.append(target)
    return targets


def normalize_id(path_or_id: str) -> str:
    """Normalize a wikilink target to a node ID."""
    s = path_or_id
    if s.endswith(".md"):
        s = s[:-3]
    # Convert path separators to dashes
    s = s.replace("/", "-").replace("\\", "-")
    # Lowercase
    return s.lower()


def get_node_id(frontmatter: dict, rel_path: str) -> str:
    """Get node ID: use frontmatter id if set, else derive from path."""
    if "id" in frontmatter and frontmatter["id"]:
        return frontmatter["id"]
    # Derive from relative path: docs/vault/agents/nexus.md → agents-nexus
    stem = rel_path.replace("docs/vault/", "").replace(".md", "")
    return stem.replace("/", "-").lower()


def build_graph(vault_dir: Path = None) -> dict:
    """Parse all vault files and build nodes + edges."""
    if vault_dir is None:
        vault_dir = VAULT_DIR
    if not vault_dir.exists():
        print(f"ERROR: Vault directory not found: {vault_dir}", file=sys.stderr)
        sys.exit(1)

    nodes = []
    edges = []
    node_ids: dict[str, dict] = {}  # id → node
    # Map: stem → node_id (for wikilink resolution)
    stem_to_id: dict[str, str] = {}

    # First pass: collect all nodes
    for md_file in sorted(vault_dir.rglob("*.md")):
        # Skip .obsidian config files and templates
        if ".obsidian" in str(md_file) or "/templates/" in str(md_file):
            continue

        rel = str(md_file).replace(str(vault_dir) + "/", "")
        content = md_file.read_text(encoding="utf-8")
        fm = parse_frontmatter(content)

        node_id = get_node_id(fm, str(md_file))
        title = fm.get("title", rel.replace(".md", "").replace("/", " / "))
        node_type = fm.get("type", "unknown")
        tags = fm.get("tags", [])
        agents = fm.get("agents", [])
        updated = fm.get("updated", "")

        # Count outgoing links (computed in second pass)
        wikilinks = extract_wikilinks(content)

        node = {
            "id": node_id,
            "label": title,
            "type": node_type,
            "path": rel,
            "tags": tags if isinstance(tags, list) else [tags],
            "agents": agents if isinstance(agents, list) else [agents],
            "updated": updated,
            "color": TYPE_COLORS.get(node_type, DEFAULT_COLOR),
            "connections": 0,  # updated in second pass
            "_wikilinks": wikilinks,
        }

        nodes.append(node)
        node_ids[node_id] = node

        # Register stems for resolution
        stem = md_file.stem.lower()
        stem_to_id[stem] = node_id
        # Also register full relative path without extension
        full_stem = rel.replace(".md", "").lower()
        stem_to_id[full_stem] = node_id
        # And the normalized version
        norm = normalize_id(rel)
        stem_to_id[norm] = node_id

    # Second pass: resolve wikilinks → edges
    edge_set = set()
    for node in nodes:
        for wl in node["_wikilinks"]:
            # Try to resolve: exact match, stem match, normalized
            target_id = None

            # Try as-is (already an id)
            if wl in node_ids:
                target_id = wl
            # Try stem
            elif wl.lower() in stem_to_id:
                target_id = stem_to_id[wl.lower()]
            # Try normalized
            else:
                norm = normalize_id(wl)
                if norm in node_ids:
                    target_id = norm
                elif norm in stem_to_id:
                    target_id = stem_to_id[norm]
                else:
                    # Try just the last part (filename stem)
                    last = wl.split("/")[-1].lower().replace(".md", "")
                    if last in stem_to_id:
                        target_id = stem_to_id[last]

            if target_id and target_id != node["id"]:
                edge_key = tuple(sorted([node["id"], target_id]))
                if edge_key not in edge_set:
                    edge_set.add(edge_key)
                    edges.append({"source": node["id"], "target": target_id})
                    # Increment connection counts
                    node_ids[node["id"]]["connections"] += 1
                    if target_id in node_ids:
                        node_ids[target_id]["connections"] += 1

    # Clean internal _wikilinks field before output
    for node in nodes:
        del node["_wikilinks"]

    return {
        "nodes": nodes,
        "edges": edges,
        "generated": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "stats": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "types": list({n["type"] for n in nodes}),
        },
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Build knowledge graph from vault")
    parser.add_argument("--vault-dir", default=str(VAULT_DIR))
    parser.add_argument("--output", default=str(OUTPUT_FILE))
    parser.add_argument("--pretty", action="store_true", default=True)
    args = parser.parse_args()

    vault_dir = Path(args.vault_dir)
    output_file = Path(args.output)

    print(f"Building graph from {vault_dir}...")
    graph = build_graph(vault_dir)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    indent = 2 if args.pretty else None
    output_file.write_text(json.dumps(graph, ensure_ascii=False, indent=indent))

    print(f"✅ Graph built: {graph['stats']['total_nodes']} nodes, {graph['stats']['total_edges']} edges")
    print(f"   Types: {', '.join(sorted(graph['stats']['types']))}")
    print(f"   Output: {output_file}")


if __name__ == "__main__":
    main()

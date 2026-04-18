from __future__ import annotations

"""High fidelity visualization utilities for KG_Instance."""

""" 
This code is the reimplementation of KG-Gen Visualization to match our custom schema
Source code: https://github.com/stair-lab/kg-gen/blob/main/src/kg_gen/utils/visualize_kg.py
"""

import hashlib
import json
import colorsys
import webbrowser
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Iterable

from core.schema.graph import KG_Instance, EduNode, EduEdge, NodeType

def _string_to_color(label: str) -> str:
    """Generate a deterministic pastel-like color for a given label."""
    digest = hashlib.sha1(label.encode("utf-8")).hexdigest()
    hue = int(digest[:2], 16) / 255.0
    saturation = 0.55 + (int(digest[2:4], 16) / 255.0) * 0.3
    lightness = 0.45 + (int(digest[4:6], 16) / 255.0) * 0.25
    r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"

def _sorted_ignore_case(items: Iterable[str]) -> list[str]:
    return sorted(items, key=lambda value: value.lower())

def _get_node_label(node: EduNode) -> str:
    """Helper to colour different types of nodes."""
    if getattr(node, "typeNode", None) == NodeType.CONCEPT:
        return node.name if node.name else str(node.id)
    
    if getattr(node, "typeNode", None) == NodeType.RHETORICAL:
        role = getattr(node, "rrole", "Info")
        content = getattr(node, "content", "")
        short_content = (content[:20] + "...") if len(content) > 20 else content # Cut context for display purpose
        return f"[{role}] {short_content}" if short_content else f"[{role}]"
        
    return getattr(node, "name", str(node.id)) or str(node.id)

def _build_view_model(kg: KG_Instance) -> dict[str, Any]:

    all_node_ids = _sorted_ignore_case(kg.nodes.keys())
    
    cluster_view: list[dict[str, Any]] = []
    node_to_cluster_id: dict[str, str] = {}
    node_color_lookup: dict[str, str] = {}

    sorted_clusters = sorted(kg.clusters.values(), key=lambda c: c.label.lower())
    for cluster in sorted_clusters:
        valid_members = [m for m in cluster.member_ids if m in kg.nodes]
        if not valid_members:
            continue
            
        ordered_members = _sorted_ignore_case(valid_members)
        c_color = _string_to_color(f"cluster::{cluster.label}")
        
        cluster_view.append({
            "id": cluster.id,
            "label": cluster.label,
            "members": ordered_members,
            "size": len(ordered_members),
            "color": c_color,
        })
        
        for member_id in valid_members:
            node_to_cluster_id[member_id] = cluster.id
            node_color_lookup[member_id] = c_color

    for nid in all_node_ids:
        if nid not in node_color_lookup:
            node_type = getattr(kg.nodes[nid], "typeNode", "default")
            node_color_lookup[nid] = _string_to_color(f"type::{node_type}")

    # 3. Process Relations (Edges)
    degree = Counter()
    indegree = Counter()
    outdegree = Counter()
    predicate_counts = Counter()

    adjacency: dict[str, set[str]] = defaultdict(set)
    node_neighbors: dict[str, set[str]] = defaultdict(set)
    node_edges_map: dict[str, dict[str, list[str]]] = defaultdict(
        lambda: {"incoming": [], "outgoing": []}
    )

    edges_view: list[dict[str, Any]] = []
    
    sorted_edges = sorted(
        kg.edges.items(), 
        key=lambda item: (item[1].name, item[1].source.id, item[1].target.id)
    )

    for idx, (edge_key, edge) in enumerate(sorted_edges):
        s_id = edge.source.id
        t_id = edge.target.id
        pred = edge.name

        predicate_counts[pred] += 1
        degree[s_id] += 1
        degree[t_id] += 1
        outdegree[s_id] += 1
        indegree[t_id] += 1
        
        adjacency[s_id].add(t_id)
        adjacency[t_id].add(s_id) 
        node_neighbors[s_id].add(t_id)
        node_neighbors[t_id].add(s_id)

        edge_viz_id = f"e{idx}"
        edge_color = _string_to_color(f"pred::{pred}")

        edges_view.append({
            "id": edge_viz_id,
            "source": s_id,
            "target": t_id,
            "predicate": pred,
            "cluster": None,  # Legacy code from kggen, unused
            "color": edge_color,
            "tooltip": f"{_get_node_label(edge.source)} —{pred}→ {_get_node_label(edge.target)}"
        })

        node_edges_map[s_id]["outgoing"].append(edge_viz_id)
        node_edges_map[t_id]["incoming"].append(edge_viz_id)

    # 4. Identify Isolated Entities
    isolated_entities = [nid for nid in all_node_ids if degree[nid] == 0]

    # 5. Connected Components Analysis (BFS)
    def get_connected_components() -> list[dict[str, Any]]:
        visited: set[str] = set()
        comps: list[dict[str, Any]] = []
        
        for nid in all_node_ids:
            if nid in visited:
                continue
            
            queue: deque[str] = deque([nid])
            visited.add(nid)
            members: list[str] = []
            
            while queue:
                curr = queue.popleft()
                members.append(curr)
                # Traverse neighbors
                for neighbor in adjacency[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            
            comps.append({
                "size": len(members),
                "members": _sorted_ignore_case(members)
            })
            
        comps.sort(key=lambda c: (-c["size"], c["members"][0] if c["members"] else ""))
        return comps

    components = get_connected_components()

    # 6. Build Final Nodes View
    nodes_view: list[dict[str, Any]] = []
    for nid in all_node_ids:
        node_obj = kg.nodes[nid]
        cluster_id = node_to_cluster_id.get(nid)
        
        # Radius calculation: Base 18 + scaled by degree
        radius = 18 + min(degree[nid], 8) * 2
        
        nodes_view.append({
            "id": nid,
            "label": _get_node_label(node_obj),
            "cluster": cluster_id,
            "color": node_color_lookup.get(nid, "#64748b"),
            "degree": degree[nid],
            "indegree": indegree[nid],
            "outdegree": outdegree[nid],
            "isRepresentative": False, # Legacy code from kggen, unused
            "radius": radius,
            "neighbors": _sorted_ignore_case(node_neighbors[nid]),
            "edgeIds": node_edges_map[nid],
            "type": getattr(node_obj, "typeNode", "unknown")
        })

    # 7. Top Lists (Stats)
    top_entities = sorted(
        [
            {
                "label": n["label"],
                "degree": n["degree"],
                "indegree": n["indegree"],
                "outdegree": n["outdegree"],
                "cluster": n["cluster"]
            }
            for n in nodes_view
        ],
        key=lambda x: (-x["degree"], x["label"].lower())
    )[:10]

    top_relations = sorted(
        [
            {
                "predicate": pred,
                "count": count,
                "cluster": None,
                "color": _string_to_color(f"pred::{pred}")
            }
            for pred, count in predicate_counts.items()
        ],
        key=lambda x: (-x["count"], x["predicate"].lower())
    )[:10]

    # 8. Global Stats
    stats = {
        "entities": len(all_node_ids),
        "relations": len(edges_view),
        "relationTypes": len(predicate_counts),
        "entityClusters": len(cluster_view),
        "edgeClusters": 0,
        "isolatedEntities": len(isolated_entities),
        "components": len(components),
        "averageDegree": round(sum(degree.values()) / len(all_node_ids), 2) if all_node_ids else 0,
        "density": round(len(edges_view) / (len(all_node_ids) * (len(all_node_ids) - 1)), 3) if len(all_node_ids) > 1 else 0
    }

    # 9. Relations Records (Table View data)
    relation_records = [
        {
            "source": e["source"], 
            "predicate": e["predicate"],
            "target": e["target"],
            "edgeId": e["id"],
            "color": e["color"]
        }
        for e in edges_view
    ]

    return {
        "nodes": nodes_view,
        "edges": edges_view,
        "clusters": cluster_view,
        "edgeClusters": [], 
        "topEntities": top_entities,
        "topRelations": top_relations,
        "stats": stats,
        "isolatedEntities": isolated_entities,
        "components": components,
        "relations": relation_records
    }

# --- EXPORT FUNCTION ---
HTML_TEMPLATE = (Path(__file__).parent / "template.html").read_text(encoding="utf-8")

def visualize(
    kg: KG_Instance,
    output_path: str | None = None,
    *,
    open_in_browser: bool = False,
):
    """Render an interactive dashboard for a KG_Instance."""
    
    if not kg or not kg.nodes:
        # Empty graph cases
        print("Graph is empty. Generating empty visualization.")
        empty_view = _build_view_model(KG_Instance()) # Mock empty
        json_str = json.dumps(empty_view)
    else:
        view_model = _build_view_model(kg)
        json_str = json.dumps(view_model, ensure_ascii=False, indent=2)

    # Inject data into template
    html = HTML_TEMPLATE.replace("<!--DATA-->", json_str)

    # Force sidebar visible (Back to source code for better understanding)
    html = html.replace(
        "display: none; /* Hidden by default - controlled by main app */",
        "display: block; /* Visible in standalone mode */",
    )

    destination = Path(output_path or "test/graph_const/kg_dashboard.html").resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(html, encoding="utf-8")

    if open_in_browser:
        webbrowser.open(destination.as_uri())

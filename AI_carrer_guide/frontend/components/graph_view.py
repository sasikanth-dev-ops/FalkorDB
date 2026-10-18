"""Pyvis and Plotly interactive knowledge graph visualizer."""

from __future__ import annotations

import json
from typing import Any

from pyvis.network import Network
import streamlit.components.v1 as components


NODE_COLOR_MAP = {
    "Student": {"background": "#6366f1", "border": "#818cf8", "highlight": "#a5b4fc"},
    "Skill": {"background": "#10b981", "border": "#34d399", "highlight": "#6ee7b7"},
    "Goal": {"background": "#f59e0b", "border": "#fbbf24", "highlight": "#fde68a"},
    "Project": {"background": "#06b6d4", "border": "#38bdf8", "highlight": "#7dd3fc"},
    "Event": {"background": "#ec4899", "border": "#f472b6", "highlight": "#fbcfe8"},
    "Opportunity": {"background": "#ec4899", "border": "#f472b6", "highlight": "#fbcfe8"},
    "Course": {"background": "#8b5cf6", "border": "#a78bfa", "highlight": "#c4b5fd"},
}

EDGE_COLOR_MAP = {
    "HAS_SKILL": "#10b981",
    "HAS_GOAL": "#f59e0b",
    "BUILDING_PROJECT": "#06b6d4",
    "REQUIRES_SKILL": "#ec4899",
    "TEACHES_SKILL": "#8b5cf6",
}


def render_knowledge_graph(graph_data: dict[str, Any], height: str = "560px") -> None:
    """Render an interactive Pyvis physics network graph from FalkorDB graph_data."""
    if not graph_data or not graph_data.get("nodes"):
        components.html(
            "<div style='color: #94a3b8; text-align: center; padding: 2rem; font-family: sans-serif;'>"
            "No graph entities currently loaded for this student.</div>",
            height=120,
        )
        return

    net = Network(
        height=height,
        width="100%",
        bgcolor="#0c111d",
        font_color="#f8fafc",
        directed=True,
    )

    # Physics configuration for smooth dynamic layout
    net.set_options(
        json.dumps(
            {
                "physics": {
                    "forceAtlas2Based": {
                        "gravitationalConstant": -50,
                        "centralGravity": 0.015,
                        "springLength": 100,
                        "springConstant": 0.08,
                    },
                    "maxVelocity": 40,
                    "solver": "forceAtlas2Based",
                    "timestep": 0.35,
                    "stabilization": {"iterations": 150},
                },
                "interaction": {
                    "hover": True,
                    "tooltipDelay": 150,
                    "navigationButtons": True,
                    "zoomView": True,
                },
            }
        )
    )

    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    added_node_ids = set()

    for node in nodes:
        node_id = str(node.get("id"))
        labels = node.get("labels", [])
        props = node.get("properties", {})

        primary_label = labels[0] if labels else "Unknown"

        # Determine node display label
        if primary_label == "Student":
            display_title = props.get("name") or f"Student ({props.get('id', node_id)})"
            size = 32
            shape = "dot"
        elif primary_label == "Skill":
            display_title = props.get("name") or "Skill"
            size = 20
            shape = "dot"
        elif primary_label == "Goal":
            display_title = (props.get("description") or "Goal")[:28] + "..."
            size = 22
            shape = "diamond"
        elif primary_label == "Project":
            display_title = props.get("title") or "Project"
            size = 24
            shape = "square"
        elif primary_label in ("Event", "Opportunity"):
            display_title = (props.get("title") or "Opportunity")[:28] + "..."
            size = 26
            shape = "star"
        elif primary_label == "Course":
            display_title = (props.get("title") or "Course")[:25]
            size = 20
            shape = "triangle"
        else:
            display_title = props.get("name") or props.get("title") or primary_label
            size = 18
            shape = "dot"

        color_cfg = NODE_COLOR_MAP.get(primary_label, {"background": "#64748b", "border": "#94a3b8"})

        # Tooltip HTML
        tooltip_lines = [f"<b>{primary_label}</b>: {display_title}"]
        for k, v in props.items():
            if k not in ("name", "title") and v is not None:
                tooltip_lines.append(f"<span style='color: #94a3b8;'>{k}:</span> {v}")
        tooltip = "<br/>".join(tooltip_lines)

        net.add_node(
            node_id,
            label=display_title,
            title=tooltip,
            color=color_cfg,
            size=size,
            shape=shape,
            font={"size": 13, "face": "Plus Jakarta Sans, sans-serif", "color": "#f1f5f9"},
        )
        added_node_ids.add(node_id)

    for edge in edges:
        source = str(edge.get("source"))
        target = str(edge.get("target"))
        edge_type = edge.get("type", "CONNECTED_TO")

        if source in added_node_ids and target in added_node_ids:
            color = EDGE_COLOR_MAP.get(edge_type, "rgba(148, 163, 184, 0.4)")
            net.add_edge(
                source,
                target,
                label=edge_type,
                color=color,
                arrows="to",
                font={"size": 10, "color": "#94a3b8", "align": "horizontal"},
            )

    html_string = net.generate_html()
    components.html(html_string, height=int(height.replace("px", "")), scrolling=False)

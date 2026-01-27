# whatsrunning/components/network_graph.py
import plotly.graph_objects as go
from typing import List, Dict, Set


def build_network_graph(
    containers: List[Dict],
    networks: List[str],
    npm_mappings: List[Dict],
    host_ports: List[int],
    expanded_containers: Set[str],
) -> go.Figure:
    """
    Build interactive network graph with nodes and edges.

    expanded_containers: Set of container IDs with expanded port groups
    """

    # Node storage
    nodes = []  # {id, x, y, label, color, size, type, data}
    edges = []  # {source_id, target_id, color, dash}

    # Helper to generate x positions with spacing
    def spread_x(items, center=0, spacing=150):
        count = len(items)
        start = center - (count - 1) * spacing / 2
        return [start + i * spacing for i in range(count)]

    # === NPM NODES (Layer 3) ===
    npm_x = spread_x(npm_mappings, spacing=200)
    for i, npm in enumerate(npm_mappings):
        nodes.append(
            {
                "id": f"npm:{npm['domain']}",
                "x": npm_x[i],
                "y": 3,
                "label": npm["domain"],
                "color": "#ef4444",  # red
                "size": 20,
                "type": "npm",
                "data": npm,
            }
        )

    # === CONTAINER NODES (Layer 2) ===
    container_x = spread_x(containers, spacing=180)
    for i, container in enumerate(containers):
        nodes.append(
            {
                "id": f"container:{container['id']}",
                "x": container_x[i],
                "y": 2,
                "label": container["name"],
                "color": "#3b82f6",  # blue
                "size": 20,
                "type": "container",
                "data": container,
            }
        )

        # Port group node (collapsed state)
        container_id = container["id"]
        is_expanded = container_id in expanded_containers
        port_count = len(container.get("internal_ports", []))

        if port_count > 0:
            if not is_expanded:
                # Collapsed: single port group node
                nodes.append(
                    {
                        "id": f"ports:{container_id}",
                        "x": container_x[i],
                        "y": 1.5,
                        "label": f"{port_count} ports",
                        "color": "#8b5cf6",  # purple
                        "size": 12,
                        "type": "port_group",
                        "data": {
                            "container_id": container_id,
                            "ports": container["internal_ports"],
                        },
                    }
                )

                # Edge: container -> port group
                edges.append(
                    {
                        "source_id": f"container:{container_id}",
                        "target_id": f"ports:{container_id}",
                        "color": "#8b5cf6",
                        "dash": "solid",
                    }
                )
            else:
                # Expanded: show individual ports
                port_x = spread_x(container["internal_ports"], center=container_x[i], spacing=30)
                for j, port in enumerate(container["internal_ports"]):
                    nodes.append(
                        {
                            "id": f"port:{container_id}:{port}",
                            "x": port_x[j],
                            "y": 1.5,
                            "label": str(port),
                            "color": "#8b5cf6",
                            "size": 8,
                            "type": "port",
                            "data": {"container_id": container_id, "port": port},
                        }
                    )

                    # Edge: container -> individual port
                    edges.append(
                        {
                            "source_id": f"container:{container_id}",
                            "target_id": f"port:{container_id}:{port}",
                            "color": "#8b5cf6",
                            "dash": "solid",
                        }
                    )

                    # Edge: internal port -> exposed port (if mapped)
                    exposed_ports = container.get("exposed_ports", {})
                    if port in exposed_ports:
                        host_port = exposed_ports[port]
                        edges.append(
                            {
                                "source_id": f"port:{container_id}:{port}",
                                "target_id": f"exposed:{host_port}",
                                "color": "#f59e0b",
                                "dash": "solid",
                            }
                        )

    # === NETWORK NODES (Layer 0) ===
    network_x = spread_x(networks, spacing=200)
    for i, network in enumerate(networks):
        nodes.append(
            {
                "id": f"network:{network}",
                "x": network_x[i],
                "y": 0,
                "label": network,
                "color": "#10b981",  # green
                "size": 18,
                "type": "network",
                "data": {"name": network},
            }
        )

    # === EXPOSED PORT NODES (Layer 1, right cluster) ===
    exposed_x = 1000  # Fixed x position (far right)
    exposed_y_start = 0.5
    for i, port in enumerate(sorted(set(host_ports))):
        nodes.append(
            {
                "id": f"exposed:{port}",
                "x": exposed_x,
                "y": exposed_y_start + i * 0.1,
                "label": str(port),
                "color": "#f59e0b",  # orange
                "size": 10,
                "type": "exposed_port",
                "data": {"port": port},
            }
        )

    # === EDGES: Container -> Network ===
    for container in containers:
        for network in container.get("networks", []):
            edges.append(
                {
                    "source_id": f"container:{container['id']}",
                    "target_id": f"network:{network}",
                    "color": "#10b981",
                    "dash": "dash",
                }
            )

    # === EDGES: NPM -> Exposed Port ===
    for npm in npm_mappings:
        target_port = npm.get("target_port")
        if target_port in host_ports:
            edges.append(
                {
                    "source_id": f"npm:{npm['domain']}",
                    "target_id": f"exposed:{target_port}",
                    "color": "#ef4444",
                    "dash": "solid",
                }
            )

    # === BUILD PLOTLY FIGURE ===

    # Create node lookup
    node_lookup = {node["id"]: i for i, node in enumerate(nodes)}

    # Edge traces (one trace per edge for proper hover)
    edge_traces = []
    for edge in edges:
        source = nodes[node_lookup[edge["source_id"]]]
        target = nodes[node_lookup[edge["target_id"]]]

        edge_traces.append(
            go.Scatter(
                x=[source["x"], target["x"]],
                y=[source["y"], target["y"]],
                mode="lines",
                line=dict(width=1, color=edge["color"], dash=edge["dash"]),
                hoverinfo="none",
                showlegend=False,
            )
        )

    # Node trace
    node_trace = go.Scatter(
        x=[node["x"] for node in nodes],
        y=[node["y"] for node in nodes],
        mode="markers+text",
        text=[node["label"] for node in nodes],
        textposition="top center",
        marker=dict(
            size=[node["size"] for node in nodes],
            color=[node["color"] for node in nodes],
            line=dict(width=2, color="white"),
        ),
        hoverinfo="text",
        hovertext=[f"{node['type']}: {node['label']}" for node in nodes],
        customdata=[node["id"] for node in nodes],  # For click events
        showlegend=False,
    )

    # Combine
    fig = go.Figure(data=edge_traces + [node_trace])

    fig.update_layout(
        showlegend=False,
        hovermode="closest",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="#f8f9fa",
        height=700,
        margin=dict(l=20, r=20, t=40, b=20),
        title="Network Topology",
    )

    return fig

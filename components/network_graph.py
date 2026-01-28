# whatsrunning/components/network_graph.py
import plotly.graph_objects as go
from typing import List, Dict, Set


def generate_stack_colors(stacks: List[Dict]) -> Dict[str, str]:
    """
    Generate distinct colors for each stack using HSL color space.
    Standalone stack gets a neutral gray.
    """
    colors = {}

    # Standalone always gets gray
    if any(s["name"] == "Standalone" for s in stacks):
        colors["Standalone"] = "#6b7280"  # gray

    # Generate colors for other stacks
    non_standalone = [s for s in stacks if s["name"] != "Standalone"]
    count = len(non_standalone)

    if count == 0:
        return colors

    # Distribute hue evenly around color wheel
    for i, stack in enumerate(non_standalone):
        hue = int(360 * i / count)
        # Use HSL: distinct hue, moderate saturation, medium-dark lightness
        colors[stack["name"]] = f"hsl({hue}, 65%, 55%)"

    return colors


def build_network_graph(
    containers: List[Dict],
    networks: List[str],
    npm_mappings: List[Dict],
    host_ports: List[int],
    expanded_containers: Set[str],
    stacks: List[Dict],
    expanded_stacks: Set[str],
    stack_filter: str = None,
) -> go.Figure:
    """
    Build interactive network graph with nodes and edges.

    expanded_containers: Set of container IDs with expanded port groups
    stacks: List of stack metadata
    expanded_stacks: Set of stack names that are expanded
    stack_filter: If provided, only show nodes related to this stack
    """

    # Filter containers and stacks if stack_filter is set
    if stack_filter:
        containers = [c for c in containers if c["stack"] == stack_filter]
        stacks = [s for s in stacks if s["name"] == stack_filter]

    # Node storage
    nodes = []  # {id, x, y, label, color, size, type, data}
    edges = []  # {source_id, target_id, color, dash}

    # Helper to generate x positions with spacing
    def spread_x(items, center=0, spacing=150):
        count = len(items)
        start = center - (count - 1) * spacing / 2
        return [start + i * spacing for i in range(count)]

    # === NPM NODES (Layer 3) ===
    npm_x = spread_x(npm_mappings, spacing=400)
    for i, npm in enumerate(npm_mappings):
        # Truncate long domain names for display
        domain = npm["domain"]
        label = domain if len(domain) <= 25 else domain[:22] + "..."

        nodes.append(
            {
                "id": f"npm:{npm['domain']}",
                "x": npm_x[i],
                "y": 3,
                "label": label,
                "color": "#ef4444",  # red
                "size": 20,
                "type": "npm",
                "data": npm,
            }
        )

    # === STACK NODES (Layer 2.5) ===
    stack_colors = generate_stack_colors(stacks)

    # Group containers by stack for positioning
    stack_to_containers = {}
    for container in containers:
        stack_name = container["stack"]
        if stack_name not in stack_to_containers:
            stack_to_containers[stack_name] = []
        stack_to_containers[stack_name].append(container)

    stack_x = spread_x(stacks, spacing=250)
    for i, stack in enumerate(stacks):
        stack_name = stack["name"]
        is_expanded = stack_name in expanded_stacks
        container_count = stack["container_count"]
        running_count = stack["running_count"]

        if not is_expanded:
            # Collapsed: single stack group node
            label = f"{stack_name} ({running_count}/{container_count})"
            nodes.append({
                "id": f"stack:{stack_name}",
                "x": stack_x[i],
                "y": 2.5,
                "label": label,
                "color": stack_colors[stack_name],
                "size": 25,
                "type": "stack_group",
                "data": stack,
            })
        else:
            # Expanded: show individual stack node + visible containers
            nodes.append({
                "id": f"stack:{stack_name}",
                "x": stack_x[i],
                "y": 2.5,
                "label": f"{stack_name}",
                "color": stack_colors[stack_name],
                "size": 20,
                "type": "stack",
                "data": stack,
            })

    # === CONTAINER NODES (Layer 2) ===
    # Create a mapping of stack name to X position for positioning
    stack_x_map = {stacks[i]["name"]: stack_x[i] for i in range(len(stacks))}

    # Group containers by stack for positioning
    containers_by_stack = {}
    for container in containers:
        stack_name = container.get("stack", "Standalone")
        if stack_name not in containers_by_stack:
            containers_by_stack[stack_name] = []
        containers_by_stack[stack_name].append(container)

    # Create container nodes
    for stack_name, stack_containers in containers_by_stack.items():
        is_stack_expanded = stack_name in expanded_stacks

        # Get stack center X position (default to 0 if stack not in stacks list)
        stack_center_x = stack_x_map.get(stack_name, 0)

        # Spread containers around stack's center when expanded
        if is_stack_expanded and len(stack_containers) > 0:
            container_x_positions = spread_x(stack_containers, center=stack_center_x, spacing=180)
        else:
            # When collapsed, position at stack center
            container_x_positions = [stack_center_x] * len(stack_containers)

        for i, container in enumerate(stack_containers):
            # Use stack color for container when stack is expanded
            container_color = stack_colors.get(stack_name, "#3b82f6") if is_stack_expanded else "#3b82f6"

            nodes.append(
                {
                    "id": f"container:{container['id']}",
                    "x": container_x_positions[i],
                    "y": 2,
                    "label": container["name"],
                    "color": container_color,
                    "size": 20,
                    "type": "container",
                    "data": container,
                }
            )

            # Add edge from stack to container (only if stack exists and is expanded)
            if is_stack_expanded and stack_name in stack_x_map:
                edges.append({
                    "source_id": f"stack:{stack_name}",
                    "target_id": f"container:{container['id']}",
                    "color": stack_colors.get(stack_name, "#3b82f6"),
                    "dash": "solid",
                })

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
                            "x": container_x_positions[i],
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
                    port_x = spread_x(container["internal_ports"], center=container_x_positions[i], spacing=30)
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
    network_x = spread_x(networks, spacing=400)
    for i, network in enumerate(networks):
        # Simplify network names: remove common suffixes and truncate
        label = network.replace("_default", "").replace("-network", "")
        label = label if len(label) <= 20 else label[:17] + "..."

        nodes.append(
            {
                "id": f"network:{network}",
                "x": network_x[i],
                "y": 0,
                "label": label,
                "color": "#10b981",  # green
                "size": 18,
                "type": "network",
                "data": {"name": network},
            }
        )

    # === EXPOSED PORT NODES (Layer 1, right cluster) ===
    exposed_x = 1000  # Fixed x position (far right)
    exposed_y_start = 0.5
    unique_ports = sorted(set(host_ports))
    port_count = len(unique_ports)

    # Adaptive spacing: more ports = tighter spacing, but never below 0.15
    port_spacing = max(0.15, min(0.5, 2.0 / port_count if port_count > 0 else 0.5))

    for i, port in enumerate(unique_ports):
        nodes.append(
            {
                "id": f"exposed:{port}",
                "x": exposed_x,
                "y": exposed_y_start + i * port_spacing,
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

        # Convert color to rgba with opacity for less clutter
        color = edge["color"]
        if color.startswith("#"):
            # Convert hex to rgba with 0.3 opacity
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            color = f"rgba({r},{g},{b},0.3)"

        edge_traces.append(
            go.Scatter(
                x=[source["x"], target["x"]],
                y=[source["y"], target["y"]],
                mode="lines",
                line=dict(width=0.8, color=color, dash=edge["dash"]),
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
        textfont=dict(
            size=10,
            color="#1f2937",  # dark gray for better readability
        ),
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
        height=900,  # Increased height for better vertical spacing
        margin=dict(l=40, r=40, t=60, b=40),  # More margin for labels
        title="Network Topology",
        dragmode="pan",  # Enable panning by default (shift+drag to zoom)
    )

    return fig

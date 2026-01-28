# whatsrunning/callbacks/graph_callbacks.py
from dash import callback, Input, Output, State, html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from services.data_store import DataStore
from components.network_graph import build_network_graph


@callback(
    Output("network-graph", "figure"),
    [
        Input("refresh-interval", "n_intervals"),
        Input("refresh-button", "n_clicks"),
        Input("expanded-containers", "data"),
        Input("expanded-stacks", "data"),
        Input("stack-filter-state", "data"),
    ],
)
def update_graph(n_intervals, n_clicks, expanded_containers, expanded_stacks, stack_filter):
    """Update network graph visualization"""
    store = DataStore.get_instance()
    data = store.get_all()

    figure = build_network_graph(
        containers=data["containers"],
        networks=data["networks"],
        npm_mappings=data["npm_mappings"],
        host_ports=data["host_ports"],
        expanded_containers=set(expanded_containers or []),
        stacks=data.get("stacks", []),
        expanded_stacks=set(expanded_stacks or []),
        stack_filter=stack_filter,
    )

    return figure


@callback(
    Output("expanded-containers", "data"),
    Input("network-graph", "clickData"),
    State("expanded-containers", "data"),
)
def handle_node_click(clickData, expanded_containers):
    """Handle node clicks to expand/collapse port groups"""
    if not clickData:
        raise PreventUpdate

    expanded = set(expanded_containers or [])

    # Get clicked node ID
    node_id = clickData["points"][0]["customdata"]

    # If clicked a port group, toggle expansion
    if node_id.startswith("ports:"):
        container_id = node_id.split(":")[1]
        if container_id in expanded:
            expanded.remove(container_id)
        else:
            expanded.add(container_id)

        return list(expanded)

    raise PreventUpdate


@callback(
    Output("expanded-stacks", "data"),
    Input("network-graph", "clickData"),
    State("expanded-stacks", "data"),
)
def handle_stack_click(clickData, expanded_stacks):
    """Handle stack node clicks to expand/collapse stack groups"""
    if not clickData:
        raise PreventUpdate

    expanded = set(expanded_stacks or [])
    node_id = clickData["points"][0]["customdata"]

    # If clicked a stack group, toggle expansion
    if node_id.startswith("stack:"):
        stack_name = node_id.split(":", 1)[1]
        if stack_name in expanded:
            expanded.remove(stack_name)
        else:
            expanded.add(stack_name)
        return list(expanded)

    raise PreventUpdate


def build_relationship_helpers(data):
    """
    Build efficient lookup tables for relationship traversal.

    Returns:
        dict with:
        - exposed_to_container: {host_port: (container_obj, internal_port)}
        - container_to_npm: {container_id: [npm_obj, ...]}
        - network_to_containers: {network_name: [container_obj, ...]}
        - port_to_npm: {host_port: [npm_obj, ...]}
    """
    helpers = {
        "exposed_to_container": {},
        "container_to_npm": {},
        "network_to_containers": {},
        "port_to_npm": {}
    }

    # Build exposed_to_container mapping
    for container in data["containers"]:
        for internal_port, host_port in container["exposed_ports"].items():
            helpers["exposed_to_container"][host_port] = (container, internal_port)

    # Build port_to_npm mapping
    for npm in data["npm_mappings"]:
        port = npm["target_port"]
        if port not in helpers["port_to_npm"]:
            helpers["port_to_npm"][port] = []
        helpers["port_to_npm"][port].append(npm)

    # Build container_to_npm mapping
    for npm in data["npm_mappings"]:
        port = npm["target_port"]
        if port in helpers["exposed_to_container"]:
            container, _ = helpers["exposed_to_container"][port]
            if container["id"] not in helpers["container_to_npm"]:
                helpers["container_to_npm"][container["id"]] = []
            helpers["container_to_npm"][container["id"]].append(npm)

    # Build network_to_containers mapping
    for container in data["containers"]:
        for network in container["networks"]:
            if network not in helpers["network_to_containers"]:
                helpers["network_to_containers"][network] = []
            helpers["network_to_containers"][network].append(container)

    return helpers


def build_relationship_card(title, items, color="secondary"):
    """
    Build a Bootstrap card for displaying relationships.

    Args:
        title: Card header text
        items: List of Dash components or strings to display
        color: Bootstrap color (danger, primary, warning, success, info, secondary)

    Returns:
        dbc.Card component
    """
    if not items:
        items = [html.Div("None", className="text-muted fst-italic")]

    return dbc.Card(
        [
            dbc.CardHeader(title, className=f"bg-{color} text-white"),
            dbc.CardBody(
                html.Ul(
                    [html.Li(item) if not isinstance(item, (html.Li, html.Div))
                     else item for item in items],
                    className="mb-0"
                )
            )
        ],
        className="mb-2",
        outline=True,
        color=color
    )


def build_chain_arrow():
    """Build a styled arrow for chain visualization"""
    return html.Span(" → ", className="text-muted mx-2 fs-5")


def build_badge(text, color):
    """Build a colored badge"""
    return dbc.Badge(text, color=color, className="me-1")


def show_npm_details(node_id, data, helpers):
    """Show details for NPM proxy node"""
    domain = node_id.split(":")[1]
    npm = next((n for n in data["npm_mappings"] if n["domain"] == domain), None)

    if not npm:
        return "NPM proxy not found"

    target_port = npm["target_port"]
    container_info = helpers["exposed_to_container"].get(target_port)

    # Basic info card
    basic_card = build_relationship_card(
        f"NPM Proxy: {domain}",
        [
            html.Div([html.Strong("Target: "), f"{npm['target_host']}:{target_port}"]),
            html.Div([html.Strong("SSL: "), "Yes" if npm["ssl"] else "No"])
        ],
        color="danger"
    )

    # Connection chain card
    if container_info:
        container, internal_port = container_info
        chain_items = [
            html.Div([
                build_badge("NPM", "danger"),
                domain,
                build_chain_arrow(),
                build_badge("Exposed", "warning"),
                str(target_port),
                build_chain_arrow(),
                build_badge("Internal", "secondary"),
                str(internal_port),
                build_chain_arrow(),
                build_badge("Container", "primary"),
                container["name"]
            ]),
            html.Hr(),
            html.Div([html.Strong("Container Status: "), container["status"]]),
            html.Div([html.Strong("Image: "), container["image"]])
        ]
        chain_card = build_relationship_card("Connection Path", chain_items, color="info")

        # Networks card
        network_items = [html.Div(net) for net in container["networks"]]
        network_card = build_relationship_card("Networks", network_items, color="success")

        return html.Div([basic_card, chain_card, network_card])
    else:
        # NPM pointing to non-existent port
        warning_card = dbc.Alert(
            f"⚠️ This NPM proxy targets port {target_port}, but no container is mapped to it.",
            color="warning"
        )
        return html.Div([basic_card, warning_card])


def show_container_details(node_id, data, helpers):
    """Show details for container node"""
    container_id = node_id.split(":")[1]
    container = next((c for c in data["containers"] if c["id"] == container_id), None)

    if not container:
        return "Container not found"

    # Basic info card
    basic_card = build_relationship_card(
        f"Container: {container['name']}",
        [
            html.Div([html.Strong("Stack: "), container.get("stack", "Unknown")]),
            html.Div([html.Strong("Image: "), container["image"]]),
            html.Div([html.Strong("Status: "), container["status"]]),
            html.Div([html.Strong("ID: "), container["id"][:12]])
        ],
        color="primary"
    )

    # Port mappings card
    port_items = []
    if container["exposed_ports"]:
        for internal, host in container["exposed_ports"].items():
            port_items.append(
                html.Div([
                    build_badge("Internal", "secondary"),
                    str(internal),
                    build_chain_arrow(),
                    build_badge("Exposed", "warning"),
                    str(host)
                ])
            )

    # Add unmapped internal ports
    for internal in container["internal_ports"]:
        if internal not in container["exposed_ports"]:
            port_items.append(
                html.Div([
                    build_badge("Internal", "secondary"),
                    str(internal),
                    html.Span(" (not exposed)", className="text-muted fst-italic")
                ])
            )

    port_card = build_relationship_card("Port Mappings", port_items, color="secondary")

    # Incoming NPM proxies card
    npm_list = helpers["container_to_npm"].get(container["id"], [])
    npm_items = [
        html.Div([
            build_badge("NPM", "danger"),
            npm["domain"],
            " → ",
            build_badge("Port", "warning"),
            str(npm["target_port"])
        ])
        for npm in npm_list
    ]
    npm_card = build_relationship_card("NPM Proxies", npm_items, color="danger")

    # Networks card
    network_items = [html.Div(net) for net in container["networks"]]
    network_card = build_relationship_card("Networks", network_items, color="success")

    return html.Div([basic_card, port_card, npm_card, network_card])


def show_exposed_port_details(node_id, data, helpers):
    """Show details for exposed port node"""
    port = int(node_id.split(":")[1])

    basic_card = build_relationship_card(
        f"Exposed Port: {port}",
        [html.Div("Host port accessible from outside")],
        color="warning"
    )

    # Find source container
    container_info = helpers["exposed_to_container"].get(port)
    if container_info:
        container, internal_port = container_info
        chain_items = [
            html.Div([
                build_badge("Container", "primary"),
                container["name"],
                build_chain_arrow(),
                build_badge("Internal", "secondary"),
                str(internal_port),
                build_chain_arrow(),
                build_badge("Exposed", "warning"),
                str(port)
            ]),
            html.Hr(),
            html.Div([html.Strong("Container Status: "), container["status"]]),
            html.Div([html.Strong("Networks: "), ", ".join(container["networks"])])
        ]
        chain_card = build_relationship_card("Source", chain_items, color="info")
    else:
        chain_card = dbc.Alert(
            "⚠️ This port is exposed but no container is mapped to it.",
            color="warning"
        )

    # Find NPM proxies targeting this port
    npm_list = helpers["port_to_npm"].get(port, [])
    npm_items = [
        html.Div([build_badge("NPM", "danger"), npm["domain"]])
        for npm in npm_list
    ]
    npm_card = build_relationship_card("NPM Proxies", npm_items, color="danger")

    return html.Div([basic_card, chain_card, npm_card])


def show_network_details(node_id, data, helpers):
    """Show details for network node"""
    network_name = node_id.split(":")[1]

    basic_card = build_relationship_card(
        f"Network: {network_name}",
        [html.Div("Docker bridge network")],
        color="success"
    )

    # Find all containers on this network
    containers = helpers["network_to_containers"].get(network_name, [])
    container_items = [
        html.Div([
            build_badge("Container", "primary"),
            c["name"],
            " - ",
            html.Span(c["status"], className="text-muted")
        ])
        for c in containers
    ]
    container_card = build_relationship_card(
        "Connected Containers",
        container_items,
        color="primary"
    )

    return html.Div([basic_card, container_card])


def show_port_details(node_id, data, helpers):
    """Show details for internal port node"""
    parts = node_id.split(":")
    container_id = parts[1]
    port = int(parts[2])

    container = next((c for c in data["containers"] if c["id"] == container_id), None)
    if not container:
        return "Container not found"

    # Check if exposed
    host_port = container["exposed_ports"].get(port)

    if host_port:
        # Port is exposed
        basic_card = build_relationship_card(
            f"Internal Port: {port}",
            [
                html.Div([html.Strong("Container: "), container["name"]]),
                html.Div([html.Strong("Exposed as: "), str(host_port)])
            ],
            color="secondary"
        )

        # Build full chain
        npm_list = helpers["port_to_npm"].get(host_port, [])
        if npm_list:
            chain_items = []
            for npm in npm_list:
                chain_items.append(html.Div([
                    build_badge("NPM", "danger"),
                    npm["domain"],
                    build_chain_arrow(),
                    build_badge("Exposed", "warning"),
                    str(host_port),
                    build_chain_arrow(),
                    build_badge("Internal", "secondary"),
                    str(port),
                    build_chain_arrow(),
                    build_badge("Container", "primary"),
                    container["name"]
                ]))
            chain_card = build_relationship_card("Full Chain", chain_items, color="info")
        else:
            chain_card = dbc.Alert("This port is exposed but no NPM proxy uses it.", color="info")
    else:
        # Port not exposed
        basic_card = build_relationship_card(
            f"Internal Port: {port}",
            [
                html.Div([html.Strong("Container: "), container["name"]]),
                html.Div(["This port is ", html.Strong("not exposed"), " to the host"], className="text-muted")
            ],
            color="secondary"
        )
        chain_card = None

    # Container info
    container_card = build_relationship_card(
        "Container Details",
        [
            html.Div([html.Strong("Name: "), container["name"]]),
            html.Div([html.Strong("Status: "), container["status"]]),
            html.Div([html.Strong("Networks: "), ", ".join(container["networks"])])
        ],
        color="primary"
    )

    return html.Div([basic_card, chain_card, container_card] if chain_card else [basic_card, container_card])


def show_stack_details(node_id, data, helpers):
    """Show details for stack node"""
    stack_name = node_id.split(":", 1)[1]
    stack = next((s for s in data.get("stacks", []) if s["name"] == stack_name), None)

    if not stack:
        return "Stack not found"

    # Basic info card
    basic_items = [
        html.Div([html.Strong("Containers: "), f"{stack['running_count']}/{stack['container_count']} running"]),
    ]

    if stack.get("compose_version"):
        basic_items.append(html.Div([html.Strong("Compose Version: "), stack["compose_version"]]))

    if stack.get("compose_working_dir"):
        basic_items.append(html.Div([html.Strong("Working Dir: "), stack["compose_working_dir"]]))

    basic_card = build_relationship_card(
        f"Stack: {stack_name}",
        basic_items,
        color="info"
    )

    # Containers in this stack
    stack_containers = [c for c in data["containers"] if c["stack"] == stack_name]
    container_items = [
        html.Div([
            build_badge("Container", "primary"),
            c["name"],
            " - ",
            html.Span(c["status"], className=f"text-{'success' if c['status'] == 'running' else 'danger'}")
        ])
        for c in stack_containers
    ]
    container_card = build_relationship_card("Containers", container_items, color="primary")

    # NPM proxies pointing to this stack
    stack_npm = []
    for container in stack_containers:
        npm_list = helpers["container_to_npm"].get(container["id"], [])
        for npm in npm_list:
            if npm not in stack_npm:
                stack_npm.append(npm)

    npm_items = [
        html.Div([
            build_badge("NPM", "danger"),
            npm["domain"],
            " → ",
            html.Span(f"port {npm['target_port']}", className="text-muted")
        ])
        for npm in stack_npm
    ]
    npm_card = build_relationship_card("NPM Proxies", npm_items, color="danger")

    # Networks used by this stack
    stack_networks = set()
    for container in stack_containers:
        stack_networks.update(container["networks"])

    network_items = [html.Div(net) for net in sorted(stack_networks)]
    network_card = build_relationship_card("Networks", network_items, color="success")

    return html.Div([basic_card, container_card, npm_card, network_card])


@callback(Output("node-details", "children"), Input("network-graph", "clickData"))
def show_node_details(clickData):
    """Show enhanced details with relationship chains for clicked node"""
    if not clickData:
        return html.Div(
            [
                html.I(className="bi bi-info-circle me-2"),
                "Click any node in the graph to see its details and relationships"
            ],
            className="text-muted text-center p-4"
        )

    node_id = clickData["points"][0]["customdata"]
    store = DataStore.get_instance()
    data = store.get_all()

    # Build relationship lookup tables once
    helpers = build_relationship_helpers(data)

    # Route to appropriate handler
    if node_id.startswith("npm:"):
        return show_npm_details(node_id, data, helpers)
    elif node_id.startswith("stack:"):
        return show_stack_details(node_id, data, helpers)
    elif node_id.startswith("container:"):
        return show_container_details(node_id, data, helpers)
    elif node_id.startswith("exposed:"):
        return show_exposed_port_details(node_id, data, helpers)
    elif node_id.startswith("network:"):
        return show_network_details(node_id, data, helpers)
    elif node_id.startswith("port:"):
        return show_port_details(node_id, data, helpers)
    elif node_id.startswith("ports:"):
        # Port group node (collapsed) - show container details
        container_id = node_id.split(":")[1]
        return show_container_details(f"container:{container_id}", data, helpers)

    return "Unknown node type"


@callback(
    Output("stack-filter", "options"),
    Input("refresh-interval", "n_intervals"),
)
def update_stack_filter_options(n_intervals):
    """Update stack filter dropdown options"""
    store = DataStore.get_instance()
    data = store.get_all()

    stacks = data.get("stacks", [])
    options = [{"label": f"{s['name']} ({s['running_count']}/{s['container_count']})",
                "value": s['name']}
               for s in stacks]

    return options


@callback(
    Output("stack-filter-state", "data"),
    Input("stack-filter", "value"),
)
def update_stack_filter_state(filter_value):
    """Update filter state when dropdown changes"""
    return filter_value


@callback(Output("last-updated", "children"), Input("refresh-interval", "n_intervals"))
def update_timestamp(n):
    """Update last updated timestamp"""
    store = DataStore.get_instance()
    last_updated = store.get("last_updated")
    return f"Last updated: {last_updated}" if last_updated else "Not yet updated"

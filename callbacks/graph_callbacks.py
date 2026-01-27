# whatsrunning/callbacks/graph_callbacks.py
from dash import callback, Input, Output, State, html
from dash.exceptions import PreventUpdate
from services.data_store import DataStore
from components.network_graph import build_network_graph


@callback(
    Output("network-graph", "figure"),
    [
        Input("refresh-interval", "n_intervals"),
        Input("refresh-button", "n_clicks"),
        Input("expanded-containers", "data"),
    ],
)
def update_graph(n_intervals, n_clicks, expanded_containers):
    """Update network graph visualization"""
    store = DataStore.get_instance()
    data = store.get_all()

    figure = build_network_graph(
        containers=data["containers"],
        networks=data["networks"],
        npm_mappings=data["npm_mappings"],
        host_ports=data["host_ports"],
        expanded_containers=set(expanded_containers or []),
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


@callback(Output("node-details", "children"), Input("network-graph", "clickData"))
def show_node_details(clickData):
    """Show details for clicked node"""
    if not clickData:
        return "Click a node to see details"

    node_id = clickData["points"][0]["customdata"]
    store = DataStore.get_instance()
    data = store.get_all()

    # Parse node type and find data
    if node_id.startswith("container:"):
        container_id = node_id.split(":")[1]
        container = next((c for c in data["containers"] if c["id"] == container_id), None)
        if container:
            return html.Div(
                [
                    html.Strong("Container: "),
                    container["name"],
                    html.Br(),
                    html.Strong("Image: "),
                    container["image"],
                    html.Br(),
                    html.Strong("Status: "),
                    container["status"],
                    html.Br(),
                    html.Strong("Networks: "),
                    ", ".join(container["networks"]),
                ]
            )

    elif node_id.startswith("npm:"):
        domain = node_id.split(":")[1]
        npm = next((n for n in data["npm_mappings"] if n["domain"] == domain), None)
        if npm:
            return html.Div(
                [
                    html.Strong("Domain: "),
                    npm["domain"],
                    html.Br(),
                    html.Strong("Target: "),
                    f"{npm['target_host']}:{npm['target_port']}",
                    html.Br(),
                    html.Strong("SSL: "),
                    "Yes" if npm["ssl"] else "No",
                ]
            )

    elif node_id.startswith("network:"):
        network_name = node_id.split(":")[1]
        return html.Div(
            [
                html.Strong("Network: "),
                network_name,
                html.Br(),
                html.Strong("Type: "),
                "Docker Network",
            ]
        )

    elif node_id.startswith("exposed:"):
        port = node_id.split(":")[1]
        return html.Div([html.Strong("Exposed Port: "), port, html.Br()])

    elif node_id.startswith("port:"):
        parts = node_id.split(":")
        container_id = parts[1]
        port = parts[2]
        return html.Div(
            [
                html.Strong("Internal Port: "),
                port,
                html.Br(),
                html.Strong("Container ID: "),
                container_id[:12],
            ]
        )

    return "Node details not found"


@callback(Output("last-updated", "children"), Input("refresh-interval", "n_intervals"))
def update_timestamp(n):
    """Update last updated timestamp"""
    store = DataStore.get_instance()
    last_updated = store.get("last_updated")
    return f"Last updated: {last_updated}" if last_updated else "Not yet updated"

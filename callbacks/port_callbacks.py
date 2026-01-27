# whatsrunning/callbacks/port_callbacks.py
from dash import callback, Input, Output
from services.data_store import DataStore
from components.port_timeline import build_port_timeline


@callback(
    Output("port-timeline", "figure"),
    [Input("refresh-interval", "n_intervals"), Input("refresh-button", "n_clicks")],
)
def update_port_timeline(n_intervals, n_clicks):
    """Update port timeline visualization"""
    store = DataStore.get_instance()

    figure = build_port_timeline(
        free_ranges=store.get("free_ranges"),
        used_ports=store.get("used_ports"),
        scan_range=store.get("scan_range"),
    )

    return figure

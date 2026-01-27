# whatsrunning/pages/dashboard.py
import reflex as rx
from state import AppState
from components.header import header
from components.available_ports import available_ports_panel
from components.node_details import node_details_panel

def dashboard_page() -> rx.Component:
    """Main dashboard with visualization"""
    return rx.cond(
        AppState.is_authenticated,
        rx.vstack(
            header(),

            rx.container(
                rx.vstack(
                    # Placeholder for graph visualization
                    rx.card(
                        rx.vstack(
                            rx.heading("Network Visualization", size="6"),
                            rx.text("Graph visualization will go here", color="gray"),
                            rx.text(f"Containers: {AppState.containers.length()}", size="2"),
                            rx.text(f"Networks: {AppState.networks.length()}", size="2"),
                            rx.text(f"NPM Mappings: {AppState.npm_mappings.length()}", size="2"),
                            spacing="2",
                        ),
                        min_height="400px",
                    ),

                    # Bottom panels
                    rx.hstack(
                        node_details_panel(),
                        available_ports_panel(),
                        spacing="4",
                        width="100%",
                    ),

                    spacing="4",
                    width="100%",
                ),
                size="4",
                padding="2em",
            ),

            width="100%",
            spacing="0",
        ),
        rx.redirect("/login"),
    )

import reflex as rx
from state import AppState
from components.header import header
from components.available_ports import available_ports_panel
from components.node_details import node_details_panel
from components.network_graph import network_graph

def dashboard_page() -> rx.Component:
    """Main dashboard with visualization"""
    return rx.cond(
        AppState.is_authenticated,
        rx.vstack(
            header(),

            rx.container(
                rx.vstack(
                    # Network graph visualization
                    rx.card(
                        rx.vstack(
                            rx.heading("Network Visualization", size="6"),
                            network_graph(),
                            spacing="3",
                        ),
                        width="100%",
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
        rx.text("Redirecting to login...", on_mount=rx.redirect("/login")),
    )

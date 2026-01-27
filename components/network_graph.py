# whatsrunning/components/network_graph.py
import reflex as rx
from state import AppState


def container_node(container: dict) -> rx.Component:
    """Render a container node"""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("box", size=20, color="blue"),
                rx.heading(container["name"], size="3"),
                spacing="2",
                align="center",
            ),
            rx.badge(container["status"], color_scheme="blue"),
            rx.text(container["image"], size="1", color="gray"),
            spacing="2",
            align="start",
        ),
        on_click=AppState.select_node(container),
        _hover={"cursor": "pointer", "border_color": "var(--blue-9)"},
        max_width="300px",
    )


def network_node(network: str) -> rx.Component:
    """Render a network node"""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("network", size=20, color="green"),
                rx.heading(network, size="3"),
                spacing="2",
                align="center",
            ),
            rx.badge("Network", color_scheme="green"),
            spacing="2",
            align="start",
        ),
        max_width="250px",
    )


def npm_node(npm: dict) -> rx.Component:
    """Render an NPM mapping node"""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("globe", size=20, color="orange"),
                rx.heading(npm["domain"], size="3"),
                spacing="2",
                align="center",
            ),
            rx.badge("NPM Proxy", color_scheme="orange"),
            rx.text("Port: ", npm["forward_port"], size="2", color="gray"),
            spacing="2",
            align="start",
        ),
        on_click=AppState.select_node(npm),
        _hover={"cursor": "pointer", "border_color": "var(--orange-9)"},
        max_width="300px",
    )


def network_graph() -> rx.Component:
    """Network graph visualization component"""

    has_data = (AppState.containers.length() > 0) | (AppState.networks.length() > 0) | (AppState.npm_mappings.length() > 0)

    return rx.cond(
        has_data,
        rx.vstack(
            # Legend
            rx.hstack(
                rx.hstack(
                    rx.icon("box", size=16, color="blue"),
                    rx.text("Container", size="2"),
                    spacing="1",
                ),
                rx.hstack(
                    rx.icon("network", size=16, color="green"),
                    rx.text("Network", size="2"),
                    spacing="1",
                ),
                rx.hstack(
                    rx.icon("globe", size=16, color="orange"),
                    rx.text("NPM Proxy", size="2"),
                    spacing="1",
                ),
                spacing="4",
                padding="1em",
                border_bottom="1px solid var(--gray-5)",
            ),

            # Graph area with nodes
            rx.box(
                rx.vstack(
                    # NPM Mappings (top row)
                    rx.cond(
                        AppState.npm_mappings.length() > 0,
                        rx.vstack(
                            rx.text("NPM Proxies", size="2", color="gray", weight="bold"),
                            rx.hstack(
                                rx.foreach(
                                    AppState.npm_mappings,
                                    npm_node,
                                ),
                                spacing="3",
                                wrap="wrap",
                                justify="center",
                            ),
                            spacing="2",
                            width="100%",
                        ),
                    ),

                    rx.divider(),

                    # Containers (middle row)
                    rx.cond(
                        AppState.containers.length() > 0,
                        rx.vstack(
                            rx.text("Containers", size="2", color="gray", weight="bold"),
                            rx.hstack(
                                rx.foreach(
                                    AppState.containers,
                                    container_node,
                                ),
                                spacing="3",
                                wrap="wrap",
                                justify="center",
                            ),
                            spacing="2",
                            width="100%",
                        ),
                    ),

                    rx.divider(),

                    # Networks (bottom row)
                    rx.cond(
                        AppState.networks.length() > 0,
                        rx.vstack(
                            rx.text("Networks", size="2", color="gray", weight="bold"),
                            rx.hstack(
                                rx.foreach(
                                    AppState.networks,
                                    network_node,
                                ),
                                spacing="3",
                                wrap="wrap",
                                justify="center",
                            ),
                            spacing="2",
                            width="100%",
                        ),
                    ),

                    spacing="4",
                    padding="2em",
                    width="100%",
                    align="center",
                ),
                width="100%",
                min_height="400px",
            ),

            spacing="0",
            width="100%",
        ),
        # Empty state
        rx.card(
            rx.vstack(
                rx.icon("circle_alert", size=32, color="gray"),
                rx.heading("No Data", size="5", color="gray"),
                rx.text("Click 'Refresh' to load containers, networks, and NPM mappings", color="gray", size="2"),
                spacing="3",
                align="center",
                padding="4em",
            ),
            width="100%",
        )
    )

# whatsrunning/components/node_details.py
import reflex as rx
from whatsrunning.state import AppState

def node_details_panel() -> rx.Component:
    """Panel showing selected node details"""
    return rx.card(
        rx.cond(
            AppState.selected_node != {},
            rx.vstack(
                rx.heading("Node Details", size="5"),
                rx.divider(),
                rx.foreach(
                    AppState.selected_node.items(),
                    lambda item: rx.hstack(
                        rx.text(f"{item[0]}:", weight="bold", size="2"),
                        rx.text(f"{item[1]}", size="2"),
                    ),
                ),
                spacing="2",
                width="100%",
            ),
            rx.text("Click a node to see details", color="gray", size="2"),
        ),
    )

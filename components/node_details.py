# whatsrunning/components/node_details.py
import reflex as rx
from state import AppState

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
                        rx.text(item[0], ":", weight="bold", size="2"),
                        rx.text(item[1], size="2", word_break="break-word"),
                        spacing="2",
                        align="start",
                    ),
                ),
                spacing="2",
                width="100%",
            ),
            rx.text("Click a node to see details", color="gray", size="2"),
        ),
    )

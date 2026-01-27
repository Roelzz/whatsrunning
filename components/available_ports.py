# whatsrunning/components/available_ports.py
import reflex as rx
from state import AppState

def available_ports_panel() -> rx.Component:
    """Panel showing available ports"""
    return rx.card(
        rx.vstack(
            rx.heading("Available Ports", size="5"),
            rx.text(
                f"Scan range: {AppState.available_ports.get('scan_range', 'N/A')}",
                color="gray",
                size="2",
            ),

            rx.divider(),

            rx.heading("Free Ranges", size="3"),
            rx.box(
                rx.foreach(
                    AppState.available_ports.get("free_ranges", []),
                    lambda range_tuple: rx.text(
                        f"{range_tuple[0]}-{range_tuple[1]}",
                        size="2",
                    ),
                ),
                max_height="200px",
                overflow_y="auto",
            ),

            rx.divider(),

            rx.heading("Next Available", size="3"),
            rx.text(
                rx.foreach(
                    AppState.available_ports.get("next_available", []),
                    lambda port: f"{port}, ",
                ),
                size="2",
            ),

            spacing="3",
            width="100%",
        ),
    )

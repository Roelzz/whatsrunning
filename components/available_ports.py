import reflex as rx
from state import AppState

def available_ports_panel() -> rx.Component:
    """Panel showing available ports"""
    return rx.card(
        rx.vstack(
            rx.heading("Available Ports", size="5"),
            rx.text(
                f"Scan range: {AppState.scan_range}",
                color="gray",
                size="2",
            ),

            rx.divider(),

            rx.heading("Free Ranges", size="3"),
            rx.box(
                rx.foreach(
                    AppState.free_ranges,
                    lambda range_list: rx.text(
                        f"{range_list[0]}-{range_list[1]}",
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
                    AppState.next_available,
                    lambda port: f"{port}, ",
                ),
                size="2",
            ),

            spacing="3",
            width="100%",
        ),
    )

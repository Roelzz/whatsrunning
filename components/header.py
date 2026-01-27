# whatsrunning/components/header.py
import reflex as rx
from state import AppState

def header() -> rx.Component:
    """Header with title and logout button"""
    return rx.hstack(
        rx.heading("whatsrunning", size="7"),
        rx.spacer(),
        rx.text(f"Last updated: {AppState.last_updated}", color="gray", size="2"),
        rx.button(
            "Refresh",
            on_click=AppState.refresh_data,
            loading=AppState.is_loading,
            size="2",
        ),
        rx.button(
            "Logout",
            on_click=AppState.logout,
            variant="soft",
            size="2",
        ),
        width="100%",
        padding="1em",
        border_bottom="1px solid var(--gray-5)",
    )

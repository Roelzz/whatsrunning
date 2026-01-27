# whatsrunning/whatsrunning.py
"""Main Reflex application"""
import reflex as rx
from pages import login_page, dashboard_page
from state import AppState
from services.poller import BackgroundPoller

def index() -> rx.Component:
    """Root route checks auth and shows appropriate content"""
    return rx.fragment(
        rx.cond(
            AppState.is_authenticated,
            rx.text("Redirecting to dashboard...", on_mount=rx.redirect("/dashboard")),
            rx.text("Redirecting to login...", on_mount=rx.redirect("/login")),
        )
    )

app = rx.App()

# Start background poller
poller = BackgroundPoller(AppState.refresh_data)
poller.start()

app.add_page(index, route="/")
app.add_page(login_page, route="/login")
app.add_page(dashboard_page, route="/dashboard", on_load=AppState.refresh_data)

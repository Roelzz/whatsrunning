# whatsrunning/whatsrunning.py
"""Main Reflex application"""
import reflex as rx
from whatsrunning.pages import login_page, dashboard_page
from whatsrunning.state import AppState
from whatsrunning.services.poller import BackgroundPoller

def index() -> rx.Component:
    """Root route redirects to dashboard"""
    return rx.cond(
        AppState.is_authenticated,
        rx.redirect("/dashboard"),
        rx.redirect("/login"),
    )

app = rx.App()

# Start background poller
poller = BackgroundPoller(AppState.refresh_data)
poller.start()

app.add_page(index, route="/")
app.add_page(login_page, route="/login")
app.add_page(dashboard_page, route="/dashboard", on_load=AppState.refresh_data)

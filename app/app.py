# whatsrunning/whatsrunning.py
"""Main Reflex application"""
import reflex as rx
from pages import login_page, dashboard_page
from state import AppState
from services.poller import BackgroundPoller

app = rx.App()

# Start background poller
poller = BackgroundPoller(AppState.refresh_data)
poller.start()

# Root redirects to login
app.add_page(rx.fragment(), route="/", on_load=rx.redirect("/login"))
app.add_page(login_page, route="/login")
app.add_page(dashboard_page, route="/dashboard", on_load=AppState.refresh_data)

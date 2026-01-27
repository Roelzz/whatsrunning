# whatsrunning/app/dash_app.py
import dash
import dash_bootstrap_components as dbc
from flask_login import LoginManager
from services.poller import BackgroundPoller
import os


def create_app():
    """Create and configure Dash app"""
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=True,
    )

    # Flask-Login setup
    server = app.server
    server.secret_key = os.getenv("SESSION_SECRET_KEY", "dev-secret-key-change-me")

    login_manager = LoginManager()
    login_manager.init_app(server)
    login_manager.login_view = "/login"

    # Start background poller
    poller = BackgroundPoller()
    poller.start()

    return app, login_manager

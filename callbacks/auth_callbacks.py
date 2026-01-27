# whatsrunning/callbacks/auth_callbacks.py
from dash import callback, Input, Output, State, no_update
from flask_login import login_user, logout_user, UserMixin
import secrets
import os


class User(UserMixin):
    """Simple user class for Flask-Login"""

    def __init__(self, username):
        self.id = username


@callback(
    [Output("url", "pathname"), Output("login-error", "children")],
    Input("login-button", "n_clicks"),
    [State("login-username", "value"), State("login-password", "value")],
    prevent_initial_call=True,
)
def login(n_clicks, username, password):
    """Handle login authentication"""
    if not username or not password:
        return no_update, "Please enter username and password"

    expected_user = os.getenv("AUTH_USERNAME", "admin")
    expected_pass = os.getenv("AUTH_PASSWORD", "changeme")

    if secrets.compare_digest(username, expected_user) and secrets.compare_digest(
        password, expected_pass
    ):
        user = User(username)
        login_user(user)
        return "/dashboard", ""
    else:
        return no_update, "Invalid credentials"


@callback(
    Output("url", "pathname", allow_duplicate=True),
    Input("logout-button", "n_clicks"),
    prevent_initial_call=True,
)
def logout(n_clicks):
    """Handle logout"""
    logout_user()
    return "/login"

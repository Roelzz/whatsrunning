# whatsrunning/main.py
"""Main Dash application entry point"""

from dotenv import load_dotenv

load_dotenv()  # Load .env before other imports

import os  # noqa: E402
from app.dash_app import create_app  # noqa: E402
from layouts import login_layout, dashboard_layout  # noqa: E402
from dash import html, dcc  # noqa: E402
from dash.dependencies import Input, Output  # noqa: E402

# Import callbacks (registers them with app)
import callbacks.auth_callbacks  # noqa: E402, F401
import callbacks.graph_callbacks  # noqa: E402, F401
import callbacks.port_callbacks  # noqa: E402, F401

# Create app
app, login_manager = create_app()
server = app.server


# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    from callbacks.auth_callbacks import User

    return User(user_id)


# Define layout with routing
app.layout = html.Div([dcc.Location(id="url", refresh=False), html.Div(id="page-content")])


# Routing callback
@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    """Handle page routing"""
    if pathname == "/dashboard":
        # Check if user is authenticated (simplified for now)
        return dashboard_layout()
    else:
        # Default to login
        return login_layout()


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=3000, debug=os.getenv("LOG_LEVEL") == "DEBUG")

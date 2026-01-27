# whatsrunning/pages/login.py
import reflex as rx
from state import AppState

def login_page() -> rx.Component:
    """Login page with username/password form"""
    return rx.container(
        rx.vstack(
            rx.heading("whatsrunning", size="9"),
            rx.text("Docker & NPM Port Mapping Visualization", color="gray"),

            rx.card(
                rx.vstack(
                    rx.input(
                        placeholder="Username",
                        value=AppState.login_username,
                        on_change=AppState.set_login_username,
                        size="3",
                    ),
                    rx.input(
                        placeholder="Password",
                        value=AppState.login_password,
                        on_change=AppState.set_login_password,
                        type="password",
                        size="3",
                    ),
                    rx.button(
                        "Login",
                        on_click=AppState.login,
                        size="3",
                        width="100%",
                    ),
                    rx.cond(
                        AppState.error_message != "",
                        rx.text(
                            AppState.error_message,
                            color="red",
                            size="2",
                        ),
                    ),
                    spacing="4",
                    width="100%",
                ),
                size="4",
            ),

            spacing="6",
            justify="center",
            min_height="100vh",
        ),
        size="1",
    )

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
                    rx.form(
                        rx.vstack(
                            rx.input(
                                placeholder="Username",
                                name="username",
                                size="3",
                            ),
                            rx.input(
                                placeholder="Password",
                                name="password",
                                type="password",
                                size="3",
                            ),
                            rx.button(
                                "Login",
                                type="submit",
                                size="3",
                                width="100%",
                            ),
                            spacing="3",
                        ),
                        on_submit=lambda form_data: AppState.login(
                            form_data["username"],
                            form_data["password"]
                        ),
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

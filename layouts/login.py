# whatsrunning/layouts/login.py
import dash_bootstrap_components as dbc
from dash import html


def layout():
    """Login page layout"""
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H2(
                                                "whatsrunning",
                                                className="text-center mb-4",
                                            ),
                                            dbc.Input(
                                                id="login-username",
                                                placeholder="Username",
                                                type="text",
                                                className="mb-3",
                                            ),
                                            dbc.Input(
                                                id="login-password",
                                                placeholder="Password",
                                                type="password",
                                                className="mb-3",
                                            ),
                                            dbc.Button(
                                                "Login",
                                                id="login-button",
                                                color="primary",
                                                className="w-100 mb-2",
                                            ),
                                            html.Div(
                                                id="login-error",
                                                className="text-danger text-center",
                                            ),
                                        ]
                                    )
                                ],
                                className="mt-5",
                            )
                        ],
                        width=4,
                    )
                ],
                justify="center",
            )
        ],
        fluid=True,
    )

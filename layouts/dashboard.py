# whatsrunning/layouts/dashboard.py
import dash_bootstrap_components as dbc
from dash import html, dcc


def layout():
    """Dashboard page layout"""
    return dbc.Container(
        [
            # Header
            dbc.Row(
                [
                    dbc.Col(html.H2("whatsrunning"), width="auto"),
                    dbc.Col(html.Div(id="last-updated", className="text-muted"), width="auto"),
                    dbc.Col(
                        [
                            dbc.Button(
                                "Refresh",
                                id="refresh-button",
                                size="sm",
                                className="me-2",
                            ),
                            dbc.Button("Logout", id="logout-button", size="sm", color="secondary"),
                        ],
                        width="auto",
                        className="ms-auto",
                    ),
                ],
                className="mb-4 align-items-center",
            ),
            # Filter controls row
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Filter by Stack:", className="me-2"),
                            dcc.Dropdown(
                                id="stack-filter",
                                options=[],
                                placeholder="All Stacks",
                                clearable=True,
                                className="d-inline-block",
                                style={"width": "200px"}
                            ),
                        ],
                        width="auto",
                    ),
                ],
                className="mb-3 align-items-center",
            ),
            # Main network graph
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            dcc.Graph(
                                                id="network-graph",
                                                config={"displayModeBar": True},
                                            )
                                        ]
                                    )
                                ]
                            )
                        ]
                    )
                ],
                className="mb-3",
            ),
            # Port timeline
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("Port Availability"),
                                    dbc.CardBody(
                                        [
                                            dcc.Graph(
                                                id="port-timeline",
                                                config={"displayModeBar": False},
                                            )
                                        ]
                                    ),
                                ]
                            )
                        ]
                    )
                ],
                className="mb-3",
            ),
            # Node details panel
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("Node Details"),
                                    dbc.CardBody(id="node-details"),
                                ]
                            )
                        ]
                    )
                ]
            ),
            # Hidden interval for auto-refresh
            dcc.Interval(id="refresh-interval", interval=10 * 1000, n_intervals=0),
            # Hidden store for expanded containers
            dcc.Store(id="expanded-containers", data=[]),
            # Hidden store for expanded stacks
            dcc.Store(id="expanded-stacks", data=[]),
            # Hidden store for stack filter
            dcc.Store(id="stack-filter-state", data=None),
        ],
        fluid=True,
        className="p-4",
    )

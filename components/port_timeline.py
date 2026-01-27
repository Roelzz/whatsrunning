# whatsrunning/components/port_timeline.py
import plotly.graph_objects as go
from typing import List, Tuple


def build_port_timeline(
    free_ranges: List[Tuple[int, int]], used_ports: List[int], scan_range: str
) -> go.Figure:
    """Build Gantt-style timeline showing port availability"""

    fig = go.Figure()

    # Free ranges as green bars
    for start, end in free_ranges:
        fig.add_trace(
            go.Bar(
                x=[end - start + 1],
                y=["Available"],
                base=start,
                orientation="h",
                marker=dict(color="#10b981", line=dict(width=0)),
                hovertemplate=f"Free Range: {start}-{end}<br>Count: {end - start + 1}<extra></extra>",
                showlegend=False,
            )
        )

    # Used ports as red markers
    for port in used_ports:
        fig.add_trace(
            go.Scatter(
                x=[port],
                y=["Used"],
                mode="markers",
                marker=dict(color="#ef4444", size=6),
                hovertemplate=f"Port: {port}<extra></extra>",
                showlegend=False,
            )
        )

    # Layout
    fig.update_layout(
        xaxis_title=f"Port Number (Range: {scan_range})",
        yaxis=dict(categoryorder="array", categoryarray=["Used", "Available"]),
        height=200,
        margin=dict(l=80, r=20, t=20, b=40),
        barmode="overlay",
        plot_bgcolor="#f8f9fa",
    )

    return fig

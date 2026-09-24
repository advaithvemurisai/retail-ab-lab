from __future__ import annotations

import html

import plotly.graph_objects as go
import streamlit as st

from retaillab.decision import Verdict

from .theme import COLORS


def header(eyebrow: str, title: str, lede: str = "") -> None:
    lede_html = f'<p class="lede">{html.escape(lede)}</p>' if lede else ""
    st.markdown(
        f'<div class="eyebrow">{html.escape(eyebrow)}</div><h1>{html.escape(title)}</h1>'
        f"{lede_html}",
        unsafe_allow_html=True,
    )


def verdict_card(verdict: Verdict, context: str) -> None:
    reasons = " ".join(html.escape(reason) for reason in verdict.reasons)
    st.markdown(
        f'<div class="verdict {verdict.tone}"><div class="eyebrow">Recommendation · '
        f"{html.escape(context)}</div><h2>{html.escape(verdict.label)}</h2><p>{reasons}</p>"
        f"<p><b>Next:</b> {html.escape(verdict.next_step)}</p></div>",
        unsafe_allow_html=True,
    )


def money(value: float, signed: bool = False, markdown: bool = False) -> str:
    """Whole dollars. Pass markdown=True inside st.markdown text, where $ starts LaTeX."""
    sign = "+" if signed and value > 0 else "-" if value < 0 else ""
    symbol = "\\$" if markdown else "$"
    return f"{sign}{symbol}{abs(value):,.0f}"


def style(fig: go.Figure, height: int = 340) -> go.Figure:
    fig.update_layout(
        height=height,
        margin={"l": 10, "r": 10, "t": 30, "b": 10},
        font={"family": "DM Sans, sans-serif", "color": COLORS["ink"]},
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
    )
    fig.update_xaxes(gridcolor=COLORS["line"], zerolinecolor=COLORS["line"])
    fig.update_yaxes(gridcolor=COLORS["line"], zerolinecolor=COLORS["muted"])
    return fig


def chart(fig: go.Figure, height: int = 340) -> None:
    st.plotly_chart(style(fig, height), width="stretch", config={"displayModeBar": False})

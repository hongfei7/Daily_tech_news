"""Shared UI helpers for a consistent light dashboard style."""

from __future__ import annotations

import streamlit as st


LIGHT_THEME_CSS = """
<style>
.stApp {
    background:
        radial-gradient(circle at top left, rgba(162, 213, 255, 0.22), transparent 28%),
        radial-gradient(circle at top right, rgba(255, 231, 184, 0.30), transparent 24%),
        linear-gradient(180deg, #f8fbff 0%, #eef6f4 52%, #faf6ef 100%);
    color: #18322f;
}
.block-container {
    max-width: 1280px;
    padding-top: 1.8rem;
    padding-bottom: 3rem;
}
h1, h2, h3 {
    color: #18322f !important;
    letter-spacing: -0.02em;
}
[data-testid="stMetricValue"], [data-testid="stMetricLabel"], p, li, label, span, div {
    color: #244540;
}
[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.86);
}
[data-testid="stDataFrame"], [data-testid="stPlotlyChart"] {
    background: rgba(255,255,255,0.78);
    border-radius: 18px;
    padding: 0.4rem;
}
.panel-card, .hero-card, .topic-card {
    background: rgba(255,255,255,0.82);
    border: 1px solid rgba(36, 69, 64, 0.08);
    border-radius: 18px;
    box-shadow: 0 12px 30px rgba(39, 88, 78, 0.08);
    padding: 1rem 1.2rem;
}
.hero-card {
    min-height: 220px;
}
.topic-card {
    min-height: 220px;
}
.topic-card p {
    white-space: normal !important;
    overflow-wrap: anywhere;
    line-height: 1.7;
    margin-bottom: 0.8rem;
}
.muted {
    color: #5d7b73 !important;
    font-size: 0.95rem;
}
.badge {
    display: inline-block;
    padding: 0.28rem 0.65rem;
    border-radius: 999px;
    background: #e6f4ef;
    color: #1d5a4f !important;
    font-size: 0.84rem;
    margin-right: 0.45rem;
}
</style>
"""


def apply_light_theme() -> None:
    st.markdown(LIGHT_THEME_CSS, unsafe_allow_html=True)


def apply_plot_style(fig):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0.72)",
        font=dict(color="#244540"),
        margin=dict(l=10, r=10, t=30, b=10),
    )
    return fig

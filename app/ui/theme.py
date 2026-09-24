from __future__ import annotations

import streamlit as st

COLORS = {
    "ink": "#18252b",
    "muted": "#65727a",
    "accent": "#087f8c",
    "success": "#16845b",
    "warning": "#b7791f",
    "danger": "#c94b4b",
    "line": "#dbe4e6",
    "control": "#9aa7ad",
}
ARM_COLORS = {"control": COLORS["control"], "mens": COLORS["accent"], "womens": "#6b5bb5"}


def inject_theme() -> None:
    st.markdown(
        """<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Space+Grotesk:wght@500;700&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; color: #18252b; }
    h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; letter-spacing: 0; }
    .hero { padding: 1.5rem 0 .5rem; max-width: 900px; }
    .hero h1 { font-size: clamp(2.4rem, 6vw, 4.5rem); line-height: 1; margin: .3rem 0 1rem; }
    .hero p, .lede { color: #65727a; font-size: 1.1rem; line-height: 1.6; max-width: 780px; }
    .eyebrow { color: #087f8c; font-size: .75rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; }
    .verdict { border-left: 6px solid #087f8c; background: #f2f8f8; padding: 1.1rem 1.4rem; border-radius: 8px; margin: 1rem 0 1.5rem; }
    .verdict.success { border-color: #16845b; background: #eef7f2; }
    .verdict.warning { border-color: #b7791f; background: #fbf5ea; }
    .verdict.danger, .verdict.invalid { border-color: #c94b4b; background: #fbefef; }
    .verdict h2 { margin: .2rem 0 .5rem; }
    .verdict p { margin: .2rem 0; }
    .muted { color: #65727a; }
    .step { border: 1px solid #dbe4e6; border-radius: 8px; padding: 1rem; min-height: 110px; }
    </style>""",
        unsafe_allow_html=True,
    )

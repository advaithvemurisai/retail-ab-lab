"""Shared data loading, sidebar assumptions, and the cached campaign readout."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))
from retaillab.analysis import Assumptions, Readout, analyze
from retaillab.data import VARIANTS, fetch_public_files, load_experiment
from retaillab.finance import load_margins

CUSTOM_MARGIN = "Custom margin"
DEFAULTS = {
    "variant": "any",
    "margin_source": "Apparel",
    "custom_margin": 0.40,
    "email_cost": 0.18,
    "minimum_roi": 0,
    "weekly_customers": 10_000,
    "use_cuped": True,
}


@st.cache_resource(show_spinner="Downloading the Hillstrom experiment and Damodaran margins...")
def ensure_public_files() -> None:
    """Fetch the public data once per server, so a fresh deploy runs on real data."""
    if os.environ.get("RETAILLAB_DEMO") == "1":
        return
    try:
        fetch_public_files()
    except OSError:
        pass  # Offline: the loaders fall back to labelled demo data.


@st.cache_data(show_spinner=False)
def load_data() -> tuple[pd.DataFrame, str]:
    return load_experiment()


@st.cache_data(show_spinner=False)
def load_margin_table() -> dict[str, object]:
    return load_margins(force_demo=os.environ.get("RETAILLAB_DEMO") == "1")


@st.cache_data(show_spinner="Estimating lift, contribution, and power...")
def _readout(assumptions: Assumptions, source: str) -> Readout:
    data, _ = load_data()
    return analyze(data, assumptions)


def gross_margin() -> float:
    source = st.session_state.get("margin_source", DEFAULTS["margin_source"])
    if source == CUSTOM_MARGIN:
        return float(st.session_state.get("custom_margin", DEFAULTS["custom_margin"]))
    return float(load_margin_table()["margins"][source]["gross_margin"])


def assumptions(variant: str | None = None) -> Assumptions:
    state = st.session_state
    return Assumptions(
        variant=variant or state.get("variant", DEFAULTS["variant"]),
        gross_margin=gross_margin(),
        contact_cost=float(state.get("email_cost", DEFAULTS["email_cost"])),
        minimum_roi=state.get("minimum_roi", DEFAULTS["minimum_roi"]) / 100,
        weekly_customers=int(state.get("weekly_customers", DEFAULTS["weekly_customers"])),
        use_cuped=bool(state.get("use_cuped", DEFAULTS["use_cuped"])),
    )


def get_readout(variant: str | None = None) -> Readout:
    return _readout(assumptions(variant), load_data()[1])


def render_sidebar() -> None:
    for key, value in DEFAULTS.items():
        st.session_state.setdefault(key, value)
    ensure_public_files()
    data, source = load_data()
    margins = load_margin_table()
    with st.sidebar:
        st.markdown("### RetailLab")
        if source == "hillstrom":
            st.caption(f"Data: Hillstrom e-mail experiment, {len(data):,} customers.")
        else:
            st.warning(
                "Synthetic demo data. Run `python scripts/get_data.py` for the Hillstrom "
                "experiment and Damodaran margins.",
                icon=":material/science:",
            )
        st.selectbox(
            "E-mail tested", list(VARIANTS), format_func=VARIANTS.get, key="variant",
            help="Compare no e-mail with one creative, or with either creative pooled.",
        )
        st.selectbox(
            "Gross margin basis", [*margins["margins"], CUSTOM_MARGIN], key="margin_source",
            help=f"Damodaran sector averages ({margins['as_of']})."
            if margins["source"] == "damodaran"
            else "Placeholder margins until data/raw/margin.xls is downloaded.",
        )
        if st.session_state.margin_source == CUSTOM_MARGIN:
            st.slider("Gross margin", 0.05, 0.80, step=0.01, key="custom_margin")
        else:
            st.caption(f"Gross margin in use: **{gross_margin():.1%}**")
        st.number_input(
            "Cost per e-mail ($)", 0.0, 2.0, step=0.01, key="email_cost",
            help="Fully loaded: send, creative, and offer cost per customer contacted.",
        )
        st.slider(
            "Minimum ROI to ship (%)", -50, 200, step=5, key="minimum_roi",
            help="Contribution divided by e-mail cost. 0% means it must at least break even.",
        )
        st.number_input(
            "Customers mailable per week", 1_000, 500_000, step=1_000, key="weekly_customers",
            help="Used to turn required sample size into weeks.",
        )
        st.toggle(
            "CUPED adjustment", key="use_cuped",
            help="Adjust revenue with past-year spend to reduce variance.",
        )

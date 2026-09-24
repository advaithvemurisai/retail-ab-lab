from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))
from retaillab.demo import demo_email
from retaillab.estimate import bootstrap_ci, proportion_effect
from retaillab.finance import benchmark_margins, pnl
from retaillab.validity import srm
from retaillab.variance import cuped


@st.cache_data(show_spinner=False)
def load_data(sample_pct: int = 100):
    raw_path = Path(__file__).parents[2] / "data" / "raw" / "hillstrom.csv"
    if raw_path.exists():
        raw = pd.read_csv(raw_path)
        frame = raw.rename(
            columns={"segment": "arm", "conversion": "conversion", "spend": "revenue"}
        )
        frame["arm"] = frame["arm"].replace(
            {"No E-Mail": "control", "Mens E-Mail": "treatment", "Womens E-Mail": "treatment"}
        )
        frame["unit_id"] = range(len(frame))
        frame["pre_spend"] = frame["history"]
        frame["segment"] = frame["history_segment"]
        return frame[["unit_id", "arm", "conversion", "revenue", "pre_spend", "segment"]]
    return demo_email(max(500, int(12000 * sample_pct / 100)))


@st.cache_data(show_spinner=False)
def load_benchmark_margin() -> float:
    path = Path(__file__).parents[2] / "data" / "raw" / "margin.xls"
    if path.exists():
        return float(benchmark_margins(str(path))["margins"]["Apparel"]["gross_margin"])
    return 0.4


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### RetailLab")
        st.caption("Marketing, sales, and finance in one decision.")
        st.selectbox(
            "Question",
            [
                "Campaign ROI",
                "Attributed vs incremental",
                "Who to send to",
                "Promotion rollout",
                "Same lift, different economics",
                "Test planning",
            ],
            key="question",
        )
        st.selectbox("Margin basis", ["Benchmark", "Override"], key="margin_basis")
        if st.session_state.margin_basis == "Override":
            st.slider("Gross margin", 0.05, 0.8, 0.4, 0.01, key="margin")
        else:
            st.session_state["margin"] = load_benchmark_margin()
        st.number_input("Email cost", 0.0, 2.0, 0.18, 0.01, key="email_cost")
        st.number_input("Annual campaigns", 1, 52, 12, key="campaigns")
        st.slider("Sample used", 10, 100, 100, 5, key="sample_pct")
        st.checkbox("CUPED adjustment", True, key="use_cuped")
        st.caption(
            "Benchmark mode uses Damodaran Apparel gross margin when data/raw is populated."
        )


def get_context():
    data = load_data(st.session_state.get("sample_pct", 100))
    primary = proportion_effect(data, "conversion")
    revenue = bootstrap_ci(data, "revenue", draws=500)
    economics = pnl(
        data, st.session_state.get("margin", 0.4), st.session_state.get("email_cost", 0.18)
    )
    validity = srm(data)
    adjusted = cuped(data) if st.session_state.get("use_cuped", True) else None
    return data, primary, revenue, economics, validity, adjusted

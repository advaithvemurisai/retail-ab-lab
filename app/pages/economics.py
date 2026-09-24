from pathlib import Path

import streamlit as st

from app.ui.context import get_context
from retaillab.finance import benchmark_margins, break_even_lift

data, *_ = get_context()
st.markdown(
    '<div class="eyebrow">Question 5</div><h1>Can the same lift pay in another sector?</h1>',
    unsafe_allow_html=True,
)
baseline = data[data.arm == "control"].revenue.mean()
margin_path = Path(__file__).parents[2] / "data" / "raw" / "margin.xls"
if margin_path.exists():
    source = benchmark_margins(str(margin_path))["margins"]
else:
    source = {
        "Apparel": {"gross_margin": 0.45},
        "Retail (Grocery and Food)": {"gross_margin": 0.28},
        "Restaurant/Dining": {"gross_margin": 0.62},
    }
rows = [
    {
        "sector": sector,
        "margin": values["gross_margin"],
        "break_even_lift": break_even_lift(0.18, baseline, values["gross_margin"]),
    }
    for sector, values in source.items()
]
st.dataframe(rows, hide_index=True)
st.caption("Margins are read from Damodaran's January 2026 workbook when available.")

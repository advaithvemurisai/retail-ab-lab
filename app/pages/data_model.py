import streamlit as st

st.markdown(
    '<div class="eyebrow">Evidence</div><h1>One model across three domains</h1>',
    unsafe_allow_html=True,
)
st.code(
    "dim_customer -> fact_exposure -> mart_experiment\ndim_campaign -> fact_sales -> mart_pnl\ndim_sector_finance -> mart_pnl",
    language="text",
)
st.write(
    "DuckDB keeps dimensions, exposure, sales, pre-period covariates, experiment outcomes, and P&L marts queryable in one local file."
)

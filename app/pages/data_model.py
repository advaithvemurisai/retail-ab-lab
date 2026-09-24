import duckdb
import streamlit as st

from app.ui.components import header
from app.ui.context import assumptions, load_data, load_margin_table
from retaillab.warehouse import SQL, build_warehouse, table_counts


@st.cache_resource(show_spinner="Building the DuckDB warehouse...")
def warehouse(source: str, contact_cost: float) -> duckdb.DuckDBPyConnection:
    data, _ = load_data()
    return build_warehouse(":memory:", data, load_margin_table(), contact_cost)


a = assumptions()
_, source = load_data()
connection = warehouse(source, a.contact_cost)
header(
    "Evidence",
    "One model across marketing, sales, and finance",
    "Every number in the app can be rebuilt from this star schema. It is built in memory here "
    "from sql/warehouse.sql; scripts/build_warehouse.py writes the same tables to "
    "data/retaillab.duckdb.",
)

st.code(
    """dim_customer ───┐
                ├── fact_exposure (customer_id, arm) ──┐
dim_campaign ───┘                                      ├── mart_experiment ──┐
                    fact_sales (customer_id, revenue) ─┘                     ├── mart_pnl
dim_sector_finance (sector, gross_margin, as_of) ────────────────────────────┘""",
    language="text",
)
left, right = st.columns([1, 2])
with left:
    st.markdown("**Tables**")
    st.dataframe(table_counts(connection), hide_index=True)
with right:
    st.markdown("**mart_pnl**: each e-mail's measured lift, priced at each sector's margin")
    st.dataframe(
        connection.execute(
            "SELECT arm, sector, customers, incremental_revenue, gross_profit, marketing_cost, "
            "contribution FROM mart_pnl"
        ).df(),
        hide_index=True,
        column_config={
            column: st.column_config.NumberColumn(format="$%.0f")
            for column in ["incremental_revenue", "gross_profit", "marketing_cost", "contribution"]
        },
    )
st.caption(
    "mart_pnl uses raw revenue and point estimates. The decision pages add CUPED, confidence "
    "intervals, and power on top of the same joins."
)
with st.expander("sql/warehouse.sql"):
    st.code(SQL.read_text(), language="sql")

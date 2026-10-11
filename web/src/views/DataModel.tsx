import { Header, Table } from '../components/ui'
import { money, num } from '../lib/format'
import { useApp } from '../state'

const DIAGRAM = `dim_customer ───┐
                ├── fact_exposure (customer_id, arm) ──┐
dim_campaign ───┘                                      ├── mart_experiment ──┐
                    fact_sales (customer_id, revenue) ─┘                     ├── mart_pnl
dim_sector_finance (sector, gross_margin, as_of) ────────────────────────────┘`

export default function DataModel() {
  const { data, readout } = useApp()
  const { warehouse } = data
  // mart_pnl re-priced by the API at the sidebar's cost; the arm-grain lift comes from the DuckDB build.
  const pnl = readout.mart_pnl
  return (
    <>
      <Header
        eyebrow="Evidence"
        title="One model across marketing, sales, and finance"
        lede="Marketing, sales and finance usually report from different systems and disagree on what a campaign earned. Here every number is rebuilt from one star schema, built in DuckDB from sql/warehouse.sql."
      />
      <pre aria-label="Star schema diagram">{DIAGRAM}</pre>
      <h3>Tables</h3>
      <Table
        rows={warehouse.tables}
        columns={[
          { label: 'Table', value: (row) => <code>{row.table}</code>, text: true },
          { label: 'Rows', value: (row) => num(row.rows) },
        ]}
      />
      <h3>mart_pnl: each e-mail's measured lift, priced at each sector's margin</h3>
      <Table
        rows={pnl}
        columns={[
          { label: 'arm', value: (row) => row.arm, text: true },
          { label: 'sector', value: (row) => row.sector, text: true },
          { label: 'customers', value: (row) => num(row.customers) },
          { label: 'incremental_revenue', value: (row) => money(row.incremental_revenue) },
          { label: 'gross_profit', value: (row) => money(row.gross_profit) },
          { label: 'marketing_cost', value: (row) => money(row.marketing_cost) },
          { label: 'contribution', value: (row) => money(row.contribution) },
        ]}
      />
      <p className="caption">
        mart_pnl uses raw revenue and point estimates at the sidebar's cost per e-mail. The decision pages add CUPED, confidence intervals, and power on
        top of the same joins.
      </p>
      <details>
        <summary>sql/warehouse.sql</summary>
        <pre>{warehouse.sql}</pre>
      </details>
    </>
  )
}

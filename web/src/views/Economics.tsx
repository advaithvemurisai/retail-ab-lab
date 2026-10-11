import { Header, RangePlot, Table } from '../components/ui'
import { money, pct } from '../lib/format'
import { breakEvenLift } from '../lib/readout'
import { useApp } from '../state'

export default function Economics() {
  const { data, readout } = useApp()
  const r = readout()
  const a = r.assumptions
  const [low, high] = r.revenue_lift_ci
  const { margins } = data
  const rows = margins.sectors.map(({ sector, gross_margin }) => {
    const needed = breakEvenLift(a.contact_cost, r.baseline_revenue, gross_margin)
    return {
      sector,
      gross_margin,
      needed,
      contribution: (r.revenue.difference * gross_margin - a.contact_cost) * 10_000,
      verdict: low > needed ? 'Pays' : high < needed ? "Doesn't pay" : 'Uncertain',
    }
  })
  return (
    <>
      <Header
        eyebrow="Question 5"
        title="Would the same lift pay in another sector?"
        lede="The e-mail's measured revenue lift is held fixed. Only the gross margin changes, so this shows how much unit economics alone move the decision."
      />
      <RangePlot
        title="Break-even revenue lift by sector, against the observed lift and its 95% interval"
        rows={rows.map((row) => ({ label: row.sector, value: row.needed, bar: true, color: 'var(--control)', text: pct(row.needed) }))}
        band={{ low, high }}
        refs={[{ x: r.revenue_lift, label: `Observed lift ${pct(r.revenue_lift)}`, color: 'var(--accent)' }]}
        format={(value) => pct(value)}
        labelWidth={190}
      />
      <p className="caption">Revenue lift needed to break even. The shaded band is the 95% interval on the observed lift.</p>
      <Table
        rows={rows}
        columns={[
          { label: 'Sector', value: (row) => row.sector, text: true },
          { label: 'Gross margin', value: (row) => pct(row.gross_margin, 1) },
          { label: 'Break-even lift', value: (row) => pct(row.needed, 1) },
          { label: 'Contribution / 10k sends', value: (row) => money(row.contribution) },
          { label: 'Verdict', value: (row) => row.verdict, text: true },
        ]}
      />
      <p className="caption">
        A sector pays when the whole band clears its break-even bar.{' '}
        {margins.source === 'damodaran'
          ? `Margins: Damodaran sector averages for US public companies, ${margins.as_of}. They are benchmarks, not any one retailer's books.`
          : 'Margins are illustrative placeholders.'}
      </p>
    </>
  )
}

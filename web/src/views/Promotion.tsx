import { Bar, BarChart, CartesianGrid, Cell, ErrorBar, LabelList, Tooltip, XAxis, YAxis } from 'recharts'
import { ChartBox, Header, Table } from '../components/ui'
import { ARM_COLORS, axisProps, gridProps, tooltipStyle } from '../lib/chart'
import { cents, money, num, pct, pValue } from '../lib/format'
import { metricKey } from '../lib/readout'
import { useApp } from '../state'

export default function Promotion() {
  const { data, assumptions } = useApp()
  const a = assumptions()
  const { summary, pairs } = data.promotion[metricKey(a)]
  const control = summary.find((row) => row.arm === 'control')!.revenue
  const rows = summary.map((row) => ({
    ...row,
    label: data.arm_labels[row.arm],
    err: 1.96 * (row.sd / Math.sqrt(row.customers)),
    contribution: row.arm === 'control' ? 0 : ((row.revenue - control) * a.gross_margin - a.contact_cost) * 10_000,
  }))
  const [best, runnerUp] = rows.filter((row) => row.arm !== 'control').sort((x, y) => y.contribution - x.contribution)
  const headToHead = pairs.find((pair) => new Set([pair.left, pair.right, best.arm, runnerUp.arm]).size === 2)!
  const label = (arm: keyof typeof data.arm_labels) => data.arm_labels[arm].toLowerCase()
  return (
    <>
      <Header
        eyebrow="Question 4"
        title="Which e-mail should roll out?"
        lede="Men's and women's creatives were tested side by side against no e-mail. Compare all three with a correction for making three comparisons at once."
      />
      {best.contribution <= 0 ? (
        <div className="callout danger">Neither e-mail earns back its cost at these assumptions. Send neither.</div>
      ) : headToHead.significant ? (
        <div className="callout success">
          <b>Roll out the {label(best.arm)}.</b> It beats the {label(runnerUp.arm)} after BH correction and earns {money(best.contribution)} of
          contribution per 10,000 sends.
        </div>
      ) : (
        <div className="callout warning">
          <b>The {label(best.arm)} leads, but not decisively.</b> The gap to the {label(runnerUp.arm)} does not survive BH correction. Ship the leader
          if a choice is needed now, or extend the head-to-head test.
        </div>
      )}
      <ChartBox>
        <BarChart data={rows} margin={{ top: 24, right: 8, bottom: 4, left: 8 }}>
          <CartesianGrid {...gridProps} />
          <XAxis dataKey="label" {...axisProps} />
          <YAxis {...axisProps} tickFormatter={(value: number) => `$${value.toFixed(2)}`} width={56} />
          <Tooltip {...tooltipStyle} cursor={{ fill: 'var(--grid)' }} formatter={(value: number) => [`${cents(value)} per customer`, 'Revenue']} />
          <Bar dataKey="revenue" isAnimationActive={false}>
            {rows.map((row) => <Cell key={row.arm} fill={ARM_COLORS[row.arm]} />)}
            <ErrorBar dataKey="err" width={10} stroke="var(--ink)" />
            <LabelList dataKey="revenue" position="insideBottom" formatter={(value: number) => cents(value)} style={{ fill: '#fff', fontSize: 12, fontWeight: 600 }} />
          </Bar>
        </BarChart>
      </ChartBox>
      <p className="caption">Revenue per customer over two weeks, with 95% intervals.</p>
      <Table
        rows={rows}
        columns={[
          { label: 'Arm', value: (row) => row.label, text: true },
          { label: 'Customers', value: (row) => num(row.customers) },
          { label: 'Conversion', value: (row) => pct(row.conversion, 2) },
          { label: 'Revenue / customer', value: (row) => cents(row.revenue) },
          { label: 'Contribution / 10k sends', value: (row) => money(row.contribution) },
        ]}
      />
      <h2>Pairwise comparisons</h2>
      <Table
        rows={pairs}
        columns={[
          { label: 'Comparison', value: (pair) => `${data.arm_labels[pair.right]} vs ${data.arm_labels[pair.left]}`, text: true },
          { label: 'Revenue difference', value: (pair) => cents(pair.difference) },
          { label: '95% CI low', value: (pair) => cents(pair.ci_low) },
          { label: '95% CI high', value: (pair) => cents(pair.ci_high) },
          { label: 'p', value: (pair) => pValue(pair.p_value) },
          { label: 'BH-adjusted p', value: (pair) => pValue(pair.p_adjusted) },
          { label: 'Significant', value: (pair) => (pair.significant ? 'Yes' : 'No') },
        ]}
      />
    </>
  )
}

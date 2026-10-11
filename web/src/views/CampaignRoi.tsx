import { Bar, BarChart, CartesianGrid, Cell, LabelList, Tooltip, XAxis, YAxis } from 'recharts'
import { ChartBox, Header, Kpi } from '../components/ui'
import { axisProps, gridProps, tooltipStyle } from '../lib/chart'
import { cents, formatRoi, money } from '../lib/format'
import { VARIANT_OPTIONS, useApp } from '../state'

export default function CampaignRoi() {
  const { readout } = useApp()
  const r = readout()
  const a = r.assumptions
  const e = r.economics
  const costOfGoods = e.incremental_revenue - e.gross_profit
  // Waterfall as range bars: each step spans [start, end] of the running total.
  const steps = [
    { name: 'Incremental revenue', range: [0, e.incremental_revenue], value: e.incremental_revenue, kind: 'step' },
    { name: 'Cost of goods', range: [e.gross_profit, e.incremental_revenue], value: -costOfGoods, kind: 'step' },
    { name: 'Gross profit', range: [0, e.gross_profit], value: e.gross_profit, kind: 'total' },
    { name: 'E-mail cost', range: [e.contribution, e.gross_profit], value: -e.marketing_cost, kind: 'step' },
    { name: 'Contribution', range: [0, e.contribution], value: e.contribution, kind: 'total' },
  ].map((step) => ({ ...step, range: [Math.min(...step.range), Math.max(...step.range)] }))
  const color = (step: (typeof steps)[number]) =>
    step.kind === 'total' ? 'var(--ink)' : step.value >= 0 ? 'var(--accent)' : 'var(--danger)'
  return (
    <>
      <Header
        eyebrow="Question 1"
        title="Did the campaign pay for itself?"
        lede={`${VARIANT_OPTIONS.find((o) => o.value === a.variant)!.label} sent to ${e.customers_contacted.toLocaleString('en-US')} customers, measured against a randomized no-e-mail control over the two-week window.`}
      />
      <div className="grid kpis">
        <Kpi label="Contribution" value={money(e.contribution)} note={`95% CI ${money(r.contribution.ci_low)} to ${money(r.contribution.ci_high)}`} />
        <Kpi label="ROI" value={formatRoi(e.roi)} title="Contribution divided by e-mail cost." />
        <Kpi label="Gross profit per $1 of e-mail" value={e.marketing_cost ? cents(e.gross_profit / e.marketing_cost) : 'n/a'} />
      </div>
      <ChartBox size="tall">
        <BarChart data={steps} margin={{ top: 28, right: 8, bottom: 4, left: 8 }}>
          <CartesianGrid {...gridProps} />
          <XAxis dataKey="name" {...axisProps} interval={0} tick={{ ...axisProps.tick, fontSize: 11 }} />
          <YAxis {...axisProps} tickFormatter={(value: number) => money(value)} width={70} />
          <Tooltip {...tooltipStyle} cursor={{ fill: 'var(--grid)' }} formatter={(_, __, item) => [money(item.payload.value), item.payload.name]} />
          <Bar dataKey="range" isAnimationActive={false}>
            {steps.map((step) => <Cell key={step.name} fill={color(step)} />)}
            <LabelList dataKey="value" position="top" formatter={(value: number) => money(value)} style={{ fill: 'var(--ink)', fontSize: 12 }} />
          </Bar>
        </BarChart>
      </ChartBox>
      <p className="caption">
        Gross margin {(a.gross_margin * 100).toFixed(1)}%, e-mail cost {cents(a.contact_cost)} per customer. Change either in the sidebar. Revenue is a
        two-week window; lasting effects are not counted.
      </p>
    </>
  )
}

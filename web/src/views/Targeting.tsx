import { useState } from 'react'
import { Header, Kpi, NumberInput, RangePlot, Table } from '../components/ui'
import type { SegmentColumn } from '../data/types'
import { cents, money, num } from '../lib/format'
import { targetingPlan } from '../lib/readout'
import { useApp } from '../state'

export default function Targeting() {
  const { data, assumptions } = useApp()
  const a = assumptions()
  const [by, setBy] = useState<SegmentColumn>('history_segment')
  const [cap, setCap] = useState(data.customers)
  const [requireSignificant, setRequireSignificant] = useState(false)
  const plan = targetingPlan(data, a, by, cap, requireSignificant)
  const sum = (values: number[]) => values.reduce((total, value) => total + value, 0)
  const planned = sum(plan.map((row) => row.send_count * row.profit_per_send))
  const everyone = sum(plan.map((row) => row.audience * row.profit_per_send))
  const ordered = [...plan].sort((x, y) => y.profit_per_send - x.profit_per_send)
  return (
    <>
      <Header
        eyebrow="Question 3"
        title="Who should receive the next send?"
        lede="Rank segments by the profit the e-mail caused in each one, not by how much they already spend. Then fill the send budget from the top."
      />
      <div className="controls">
        <label className="field">
          <span>Segment by</span>
          <select value={by} onChange={(event) => setBy(event.target.value as SegmentColumn)}>
            {(Object.keys(data.segment_columns) as SegmentColumn[]).map((column) => (
              <option key={column} value={column}>{data.segment_columns[column]}</option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Send budget (customers)</span>
          <NumberInput value={cap} min={0} max={data.customers} step={1000} onChange={(value) => setCap(Math.round(value))} />
        </label>
        <label className="toggle" title="Send only where the lift survives Benjamini-Hochberg correction across segments.">
          <input type="checkbox" checked={requireSignificant} onChange={(event) => setRequireSignificant(event.target.checked)} />
          Only BH-significant segments
        </label>
      </div>
      <div className="grid kpis">
        <Kpi label="Customers to e-mail" value={num(sum(plan.map((row) => row.send_count)))} />
        <Kpi label="Expected contribution" value={money(planned)} />
        <Kpi label="vs e-mailing everyone" value={money(planned - everyone, true)}
          note={`E-mailing all ${num(sum(plan.map((row) => row.audience)))} customers: ${money(everyone)}`} />
      </div>
      <RangePlot
        title="Incremental contribution per e-mail by segment, with 95% intervals"
        rows={ordered.map((row) => ({
          label: row.segment, value: row.profit_per_send, low: row.profit_low, high: row.profit_high,
          color: row.selected ? 'var(--accent)' : 'var(--control)',
        }))}
        refs={[{ x: 0, dashed: true }]}
        format={(value) => cents(value)}
        labelWidth={150}
      />
      <p className="caption">Incremental contribution per e-mail (95% CI). Teal segments are in the send plan.</p>
      <Table
        rows={plan}
        columns={[
          { label: data.segment_columns[by], value: (row) => row.segment, text: true },
          { label: 'Customers', value: (row) => num(row.audience) },
          { label: 'Revenue lift / customer', value: (row) => cents(row.difference) },
          { label: 'Contribution / send', value: (row) => cents(row.profit_per_send) },
          { label: 'p', value: (row) => row.p_value.toFixed(3) },
          { label: 'BH-adjusted p', value: (row) => row.p_adjusted.toFixed(3) },
          { label: 'Significant', value: (row) => (row.significant ? 'Yes' : 'No') },
          { label: 'Send', value: (row) => num(row.send_count) },
        ]}
      />
      <p className="caption">
        Segment estimates are noisier than the overall result. Point estimates drive the plan; turn on the BH filter to act only on segment differences
        that survive correction.
      </p>
    </>
  )
}

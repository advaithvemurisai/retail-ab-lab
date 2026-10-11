import { CartesianGrid, Line, LineChart, ReferenceLine, Tooltip, XAxis, YAxis } from 'recharts'
import { ChartBox, Header, Kpi, Table } from '../components/ui'
import { axisProps, gridProps, tooltipStyle } from '../lib/chart'
import { pct } from '../lib/format'
import { useApp } from '../state'

export default function Pitfalls() {
  const { data } = useApp()
  const { looks, peeking, broken_split: broken, placebo } = data.pitfalls
  const curve = looks.map((count, i) => ({ looks: count, rate: peeking[i] }))
  return (
    <>
      <Header
        eyebrow="Evidence"
        title="What can fool the team?"
        lede="Three ways a team ends up shipping a campaign that doesn't work, even when the arithmetic is right. Each one is caught by a check that runs before the verdict."
      />
      <h2>1. Peeking at a test that has no effect</h2>
      <ChartBox>
        <LineChart data={curve} margin={{ top: 16, right: 16, bottom: 22, left: 0 }}>
          <CartesianGrid {...gridProps} />
          <XAxis dataKey="looks" type="number" scale="log" domain={[1, 20]} ticks={looks} {...axisProps}
            label={{ value: 'Interim looks, stopping at the first p < 0.05', position: 'insideBottom', offset: -12, fill: 'var(--muted)', fontSize: 12 }} />
          <YAxis domain={[0, 0.3]} ticks={[0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3]} {...axisProps} tickFormatter={(value: number) => pct(value)} width={48} />
          <Tooltip {...tooltipStyle} labelFormatter={(value: number) => `${value} looks`} formatter={(value: number) => [pct(value, 1), 'False wins']} />
          <ReferenceLine y={0.05} stroke="var(--muted)" strokeDasharray="5 4" label={{ value: 'Promised 5%', position: 'insideTopLeft', fill: 'var(--muted)', fontSize: 12 }} />
          <Line dataKey="rate" stroke="var(--danger)" strokeWidth={2} isAnimationActive={false} />
        </LineChart>
      </ChartBox>
      <p className="caption">
        Checking a test {looks[looks.length - 2]} times and stopping at the first significant result declares a winner {pct(peeking[peeking.length - 2])} of
        the time when nothing works. Fix the sample size up front, or use sequential (always-valid) tests. Hillstrom has no timestamps, so this is a
        simulation of 2,000 A/A tests per schedule.
      </p>

      <h2>2. A broken split</h2>
      <div className="grid kpis">
        <Kpi label="True revenue lift" value={pct(broken.true_lift, 0, true)} />
        <Kpi label="Reported after the bug" value={pct(broken.reported_lift, 0, true)} />
        <Kpi label="SRM check" value={broken.srm_failed ? 'FAILED' : 'passed'} note={`p = ${broken.srm_p.toExponential(1)}`} />
      </div>
      <p className="caption">
        Simulated bug: 5% of e-mailed customers who did not buy go missing from the logs (think bounced sends silently filtered). The lift inflates,
        and only the split check catches it.
      </p>

      <h2>3. Slicing until something is significant</h2>
      <Table
        rows={placebo}
        columns={[
          { label: 'Slice', value: (row) => row.slice, text: true },
          { label: 'False lead, unadjusted', value: (row) => pct(row.raw) },
          { label: 'False lead, after BH', value: (row) => pct(row.bh) },
        ]}
      />
      <p className="caption">
        Assignment is shuffled 100 times, so every true effect is zero. The table shows how often at least one segment still looks significant. BH
        correction pulls each slice back toward the 5% target; slicing four ways and reporting whichever works multiplies the risk again.
      </p>
    </>
  )
}

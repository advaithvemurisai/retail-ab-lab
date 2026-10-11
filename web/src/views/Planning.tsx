import { useState } from 'react'
import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, Tooltip, XAxis, YAxis } from 'recharts'
import { ChartBox, Header, Kpi, Loading, NumberInput } from '../components/ui'
import type { PlanningResponse } from '../data/types'
import { useApi } from '../lib/api'
import { axisProps, gridProps, tooltipStyle } from '../lib/chart'
import { finite, num, pct } from '../lib/format'
import { useApp } from '../state'

const POWERS = [0.7, 0.8, 0.9, 0.95]
const SHARES = [0.5, 2 / 3, 0.8, 0.9]

export default function Planning() {
  const { data, readout, assumptions: a, params } = useApp()
  const r = readout.readouts[a.variant]
  const block = data.variants[a.variant]
  // The lift box defaults to break-even and follows the sidebar until the viewer types a value.
  const defaultLift = Math.round(r.planned_lift * 1000) / 10
  const [override, setOverride] = useState<{ base: number; value: number }>()
  const liftPct = override && override.base === defaultLift ? override.value : defaultLift
  const [targetPower, setTargetPower] = useState(0.8)
  const [share, setShare] = useState(0.5)
  const api = useApi<PlanningResponse>('/api/planning', { ...params, lift: liftPct / 100, power: targetPower, share })
  const plan = api.data
  const end = plan ? plan.curve[plan.curve.length - 1].weeks : 2
  return (
    <>
      <Header
        eyebrow="Evidence"
        title="How long should the next test run?"
        lede="A test that is too short can't tell a profitable e-mail from noise; one that runs too long keeps a holdout group from being mailed and costs sales. Size the next test to detect the smallest lift that pays for itself, using this experiment's own revenue spread."
      />
      <div className="controls">
        <div className="field">
          <span>Power</span>
          <div className="seg" role="group" aria-label="Power">
            {POWERS.map((value) => <button key={value} type="button" aria-pressed={value === targetPower} onClick={() => setTargetPower(value)}>{pct(value)}</button>)}
          </div>
        </div>
        <label className="field">
          <span>Lift to detect (%)</span>
          <NumberInput value={liftPct} min={1} max={500} step={1} onChange={(value) => setOverride({ base: defaultLift, value })} />
          <span className="hint">Defaults to the break-even revenue lift at the sidebar margin and cost.</span>
        </label>
        <div className="field">
          <span>Share of customers e-mailed</span>
          <div className="seg" role="group" aria-label="Share of customers e-mailed">
            {SHARES.map((value) => <button key={value} type="button" aria-pressed={value === share} onClick={() => setShare(value)}>{pct(value)}</button>)}
          </div>
          <span className="hint">A bigger holdout costs lost sales; a smaller one needs more customers overall.</span>
        </div>
      </div>
      {api.error && <div className="callout danger" role="alert">{api.error}</div>}
      {!plan ? !api.error && <Loading /> : (
        <>
          <div className="grid kpis">
            <Kpi label="Customers needed" value={num(finite(plan.n_used))} note={`Both arms together, CUPED ${a.use_cuped ? 'on' : 'off'}`} />
            <Kpi label="Weeks at current volume" value={finite(plan.weeks).toFixed(1)} />
            <Kpi label="Weeks saved by CUPED" value={finite(plan.weeks_saved).toFixed(2)}
              title="CUPED cuts required sample by the share of variance past-year spend explains." />
          </div>
          <ChartBox>
            <LineChart data={plan.curve} margin={{ top: 10, right: 12, bottom: 18, left: 0 }}>
              <CartesianGrid {...gridProps} />
              <XAxis dataKey="weeks" type="number" domain={[0.25, end]} {...axisProps} tickFormatter={(value: number) => value.toFixed(1)}
                label={{ value: 'Weeks of traffic', position: 'insideBottom', offset: -10, fill: 'var(--muted)', fontSize: 12 }} />
              <YAxis domain={[0, 1]} {...axisProps} tickFormatter={(value: number) => pct(value)} width={48} />
              <Tooltip {...tooltipStyle} labelFormatter={(value: number) => `${value.toFixed(1)} weeks`} formatter={(value: number) => pct(value)} />
              <Legend verticalAlign="top" height={28} wrapperStyle={{ fontSize: 13 }} />
              <ReferenceLine y={targetPower} stroke="var(--danger)" strokeDasharray="2 4" />
              <Line dataKey="raw" name="Without CUPED" stroke="var(--control)" strokeDasharray="6 4" dot={false} strokeWidth={2} isAnimationActive={false} />
              <Line dataKey="cuped" name="With CUPED" stroke="var(--accent)" dot={false} strokeWidth={2} isAnimationActive={false} />
            </LineChart>
          </ChartBox>
        </>
      )}
      <h2>Why CUPED barely helps here</h2>
      <p className="prose">
        CUPED removes the share of variance a pre-period covariate explains, which is the squared correlation. Past-year spend and two-week spend
        correlate at ρ = {block.cuped.correlation.toFixed(3)}, so the reduction is {pct(block.cuped.variance_reduction, 2)}. Most customers buy
        nothing in the window, and annual history does not predict who will. A covariate with ρ = 0.5 would cut the sample by 25%.
      </p>
    </>
  )
}

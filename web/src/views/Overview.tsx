import { Kpi, RangePlot, Table, VerdictCard } from '../components/ui'
import type { Arm } from '../data/types'
import { cents, finite, formatRoi, money, num, pct } from '../lib/format'
import { VARIANT_OPTIONS, useApp } from '../state'

export default function Overview() {
  const { data, readout, assumptions: a } = useApp()
  const r = readout.readouts[a.variant]
  const block = data.variants[a.variant]
  const [low, high] = r.revenue_lift_ci
  const breakEven = finite(r.break_even_lift)
  const variantLabel = VARIANT_OPTIONS.find((option) => option.value === a.variant)!.label
  const { any: pooled, mens, womens } = readout.readouts
  let leader = { name: "men's", r: mens }
  let trailer = { name: "women's", r: womens }
  if (finite(womens.economics.roi) > finite(mens.economics.roi)) [leader, trailer] = [trailer, leader]
  const attribution = data.variants.any.attribution
  const questions = [
    ['Did the campaign pay for itself?',
      `${pooled.verdict.label.charAt(0)}${pooled.verdict.label.slice(1).toLowerCase()}: ${money(pooled.economics.contribution)} contribution after e-mail costs, with a ${pct(pooled.contribution.chance_of_loss)} chance it lost money.`,
      'roi'],
    ['How much revenue did the e-mail actually cause?',
      `${pct(attribution.gap_pct ?? 0)} of revenue credited to the e-mail would have come in anyway.`, 'attribution'],
    ['Who should get the next send?', 'Segments ranked by the profit the e-mail caused in each, filled to a send budget.', 'targeting'],
    ['Which e-mail should roll out?',
      `The ${leader.name} e-mail: ${formatRoi(leader.r.economics.roi)} ROI against ${formatRoi(trailer.r.economics.roi)} for the ${trailer.name} e-mail.`,
      'promotion'],
    ['Would it pay in a different business?', 'The same lift priced at apparel, grocery and restaurant margins. Margin decides the answer.', 'economics'],
    ['How long should the next test run?', 'Customers and weeks needed to detect the smallest lift that pays for itself.', 'planning'],
  ]
  const v = data.validity
  return (
    <>
      <div className="eyebrow">Retail decision lab</div>
      <h1>RetailLab</h1>
      <p className="lede">
        Marketing says the e-mail worked. Sales says revenue is up. Finance asks what it actually earned. RetailLab prices a randomized
        e-mail test at the margin and contact cost you set, then says whether to ship.
      </p>
      <VerdictCard verdict={r.verdict} context={`${variantLabel} vs no e-mail`} />

      <div className="grid kpis">
        <Kpi label="Incremental revenue" value={money(r.economics.incremental_revenue)}
          title="Treatment minus control revenue per customer, times customers e-mailed (CUPED-adjusted when the toggle is on)." />
        <Kpi label="Contribution" value={money(r.economics.contribution)}
          note={`95% CI ${money(r.contribution.ci_low)} to ${money(r.contribution.ci_high)}`} title="Incremental gross profit minus e-mail cost." />
        <Kpi label="ROI" value={formatRoi(r.economics.roi)} title="Contribution divided by e-mail cost. +100% means each $1 spent returned $2 of gross profit." />
        <Kpi label="Chance of loss" value={pct(r.contribution.chance_of_loss)} title="Share of bootstrap draws where contribution is below zero." />
      </div>

      <h2>Does the lift clear break-even?</h2>
      <RangePlot
        title="Observed revenue lift with 95% interval against the break-even lift"
        rows={[{ label: 'Observed revenue lift', value: r.revenue_lift, low, high, bar: true }]}
        refs={Number.isFinite(breakEven) ? [{ x: breakEven, label: `Break-even ${pct(breakEven)}`, dashed: true }] : []}
        format={(value) => pct(value)}
      />
      <p className="caption">
        Customers who got no e-mail spent {cents(r.baseline_revenue)} each on average. At {pct(a.gross_margin)} gross margin and {cents(a.contact_cost)} per
        e-mail, revenue must rise {pct(breakEven)} to pay for the send. Conversion moved {pct(block.conversion.relative_lift, 0, true)} (95%
        CI {pct(block.conversion.lift_ci_low, 0, true)} to {pct(block.conversion.lift_ci_high, 0, true)}).
      </p>

      <h2>The questions a retailer needs answered</h2>
      <div className="grid three">
        {questions.map(([question, answer, page]) => (
          <a key={page} className="card question" href={`#/${page}`}>
            <strong>{question}</strong>
            <span>{answer}</span>
            <em>Open →</em>
          </a>
        ))}
      </div>

      <h2>How it works</h2>
      <div className="grid three">
        {[
          ['Randomize', "Customers were split at random into no e-mail, men's e-mail, and women's e-mail."],
          ['Price', 'Incremental revenue meets sector gross margin and the cost of each send.'],
          ['Decide', 'Validity, profit, downside risk, and power feed one rule-based verdict.'],
        ].map(([title, body]) => <div key={title} className="card"><b>{title}</b><p className="muted">{body}</p></div>)}
      </div>

      <details>
        <summary>How we know</summary>
        <p>
          <b>Split check (SRM).</b> The design sends one third of customers to each arm. Chi-square p = {v.p_value.toFixed(2)}, so the split{' '}
          {v.failed ? <b>failed</b> : 'matches the design'} (threshold p &lt; 0.001).
        </p>
        <Table
          rows={Object.keys(v.counts) as Arm[]}
          columns={[
            { label: 'Arm', value: (arm) => data.arm_labels[arm], text: true },
            { label: 'Customers', value: (arm) => num(v.counts[arm]) },
            { label: 'Expected', value: (arm) => num(Math.round(v.expected[arm])) },
          ]}
        />
        <p><b>Covariate balance.</b> Standardized mean differences below 0.1 are balanced.</p>
        <Table
          rows={block.balance}
          columns={[
            { label: 'Covariate', value: (row) => row.covariate, text: true },
            { label: 'SMD', value: (row) => row.smd.toFixed(4) },
            { label: 'Balanced', value: (row) => (row.balanced ? 'Yes' : 'No') },
          ]}
        />
        <p>
          <b>Methods.</b> Revenue per customer uses a Welch test, the primary decision metric. Contribution uncertainty comes from 1,000 bootstrap
          resamples of the revenue difference, scaled by customers e-mailed, margin, and cost. Conversion uses a two-proportion z-test with a
          delta-method interval. Power is computed for the break-even lift at the current sample size ({pct(r.power)}).{' '}
          {a.use_cuped
            ? `CUPED is on: past-year spend explains ${pct(block.cuped.variance_reduction, 2)} of revenue variance here, so it barely changes the estimate.`
            : 'CUPED is off.'}
        </p>
      </details>
    </>
  )
}

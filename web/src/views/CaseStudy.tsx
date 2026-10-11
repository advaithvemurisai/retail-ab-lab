import { Header } from '../components/ui'
import { cents, finite, formatRoi, money, num, pct } from '../lib/format'
import { useApp } from '../state'

export default function CaseStudy() {
  const { data, readout, assumptions: a } = useApp()
  const { any: pooled, mens, womens } = readout.readouts
  const attribution = data.variants.any.attribution
  const mensLeads = finite(mens.economics.roi) >= finite(womens.economics.roi)
  const [leader, trailer] = mensLeads ? [mens, womens] : [womens, mens]
  const [leaderName, trailerName] = mensLeads ? ["men's", "women's"] : ["women's", "men's"]
  const { margins } = data
  return (
    <div className="prose">
      <Header eyebrow="Portfolio" title="Case study" />
      {data.source === 'demo' && <div className="callout warning">Figures below come from synthetic demo data.</div>}
      <h2>Problem</h2>
      <p>
        A retailer's marketing team reports that an e-mail campaign drove {money(attribution.attributed)} in attributed revenue. Finance wants to know
        what it earned, and whether to keep sending.
      </p>
      <h2>Approach</h2>
      <ul>
        <li>
          <b>Randomized evidence.</b> {num(data.customers)} customers split into thirds: no e-mail, men's e-mail, women's e-mail (Hillstrom, 2008). A
          split check (SRM) runs before anything is interpreted.
        </li>
        <li>
          <b>Unit economics.</b> Revenue lift is priced at {pct(a.gross_margin, 1)} gross margin (
          {margins.source === 'damodaran' ? `Damodaran, ${margins.as_of}` : 'placeholder'}) and {cents(a.contact_cost)} per e-mail, then reported as
          contribution with a bootstrap interval.
        </li>
        <li><b>One decision rule.</b> Validity, downside, segment harm, ROI hurdle, and power feed one verdict.</li>
      </ul>
      <h2>Findings</h2>
      <ul>
        <li>
          <b>Pooled campaign: {pooled.verdict.label}.</b> Revenue per customer rose {pct(pooled.revenue_lift, 0, true)} against a{' '}
          {pct(finite(pooled.break_even_lift))} break-even bar; contribution {money(pooled.economics.contribution)} (95% CI {money(pooled.contribution.ci_low)} to{' '}
          {money(pooled.contribution.ci_high)}).
        </li>
        <li>
          <b>The {leaderName} e-mail carries it.</b> {pct(leader.revenue_lift, 0, true)} lift and {formatRoi(leader.economics.roi)} ROI,
          against {pct(trailer.revenue_lift, 0, true)} and {formatRoi(trailer.economics.roi)} for the {trailerName} e-mail, whose
          chance of loss is {pct(trailer.contribution.chance_of_loss)}.
        </li>
        <li>
          <b>Attribution overstates.</b> {pct(attribution.gap_pct ?? 0)} of revenue from e-mailed customers would have happened without the e-mail.
        </li>
        <li>
          <b>CUPED is not free sensitivity.</b> Past-year spend explains {pct(data.variants.any.cuped.variance_reduction, 2)} of two-week spend variance here,
          so it saves almost nothing.
        </li>
      </ul>
      <h2>Limitations</h2>
      <p>
        Contact cost is an assumption. Damodaran margins are US public-company sector averages, not this retailer's books. Hillstrom has no
        timestamps, so peeking is simulated. Revenue is a two-week window and ignores longer-run effects such as unsubscribes.
      </p>
    </div>
  )
}

import { Header, Kpi } from '../components/ui'
import { money, pct } from '../lib/format'
import { useApp } from '../state'

export default function Attribution() {
  const { data, settings } = useApp()
  const result = data.variants[settings.variant].attribution
  const positive = result.incremental > 0
  const share = positive ? result.baseline / result.attributed : 1
  return (
    <>
      <Header
        eyebrow="Question 2"
        title="How much revenue was incremental?"
        lede="A click-through report credits the e-mail with every purchase an e-mailed customer made. The randomized control shows how much of that would have happened anyway."
      />
      <div className="grid kpis">
        <Kpi label="E-mail-attributed revenue" value={money(result.attributed)} />
        <Kpi label="Incremental revenue" value={money(result.incremental)} />
        <Kpi label="Would have happened anyway" value={result.gap_pct === null ? 'n/a' : pct(result.gap_pct)} />
      </div>
      {positive && (
        <div className="stack-bar" role="img" aria-label={`Attributed revenue: ${money(result.baseline)} would have happened anyway, ${money(result.incremental)} caused by the e-mail`}>
          <div style={{ flex: share, background: 'var(--control)' }} title="Would have happened anyway">{money(result.baseline)}</div>
          <div style={{ flex: 1 - share, background: 'var(--accent)' }} title="Caused by the e-mail">{money(result.incremental)}</div>
        </div>
      )}
      <p>
        {positive
          ? `Grey is revenue the control group predicts e-mailed customers would have spent regardless (${money(result.baseline)}). Teal is the causal lift (${money(result.incremental)}). Budgeting on attributed revenue would overstate the e-mail's return by ${(result.attributed / result.incremental).toFixed(1)}x.`
          : "The e-mail produced no measurable incremental revenue."}
      </p>
    </>
  )
}

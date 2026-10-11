import { Suspense, lazy, useEffect, useState } from 'react'
import { ErrorBoundary, Loading, NumberInput } from './components/ui'
import type { Data, Variant } from './data/types'
import { pct } from './lib/format'
import { AppProvider, CUSTOM_MARGIN, VARIANT_OPTIONS, useApp } from './state'

// Same pages and order as the Streamlit app's navigation.
const views = {
  overview: { label: 'Overview', group: 'Decision', component: lazy(() => import('./views/Overview')) },
  roi: { label: 'Campaign ROI', group: 'Decision', component: lazy(() => import('./views/CampaignRoi')) },
  attribution: { label: 'Attributed vs incremental', group: 'Decision', component: lazy(() => import('./views/Attribution')) },
  targeting: { label: 'Who to send to', group: 'Decision', component: lazy(() => import('./views/Targeting')) },
  promotion: { label: 'Which e-mail', group: 'Decision', component: lazy(() => import('./views/Promotion')) },
  economics: { label: 'Same lift, different economics', group: 'Decision', component: lazy(() => import('./views/Economics')) },
  planning: { label: 'Test planning', group: 'Evidence', component: lazy(() => import('./views/Planning')) },
  pitfalls: { label: 'Pitfalls lab', group: 'Evidence', component: lazy(() => import('./views/Pitfalls')) },
  model: { label: 'Data model', group: 'Evidence', component: lazy(() => import('./views/DataModel')) },
  research: { label: 'Research', group: 'Evidence', component: lazy(() => import('./views/Research')) },
  case: { label: 'Case study', group: 'Portfolio', component: lazy(() => import('./views/CaseStudy')) },
} as const
type ViewKey = keyof typeof views
const KEYS = Object.keys(views) as ViewKey[]
const GROUPS = ['Decision', 'Evidence', 'Portfolio'] as const

const readRoute = (): ViewKey => {
  const key = window.location.hash.replace(/^#\/?/, '') as ViewKey
  return key in views ? key : 'overview'
}

export default function App() {
  const [data, setData] = useState<Data>()
  const [error, setError] = useState<string>()
  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/readout.json`)
      .then((response) => {
        if (!response.ok) throw new Error(`Could not load the experiment data (${response.status})`)
        return response.json() as Promise<Data>
      })
      .then(setData, (reason: Error) => setError(reason.message))
  }, [])
  if (error) return <main><div className="callout danger" role="alert">{error}</div></main>
  if (!data) return <main><Loading /></main>
  return <AppProvider data={data}><Shell /></AppProvider>
}

function Shell() {
  const [route, setRoute] = useState<ViewKey>(readRoute)
  useEffect(() => {
    const onHash = () => {
      setRoute(readRoute())
      window.scrollTo(0, 0)
    }
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])
  useEffect(() => { document.title = route === 'overview' ? 'RetailLab' : `${views[route].label} · RetailLab` }, [route])
  const View = views[route].component
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="mobile-bar">
          <a className="brand" href="#/overview">RetailLab</a>
          <select aria-label="Page" value={route} onChange={(event) => { window.location.hash = `#/${event.target.value}` }}>
            {GROUPS.map((group) => (
              <optgroup key={group} label={group}>
                {KEYS.filter((key) => views[key].group === group).map((key) => <option key={key} value={key}>{views[key].label}</option>)}
              </optgroup>
            ))}
          </select>
          <details>
            <summary>Assumptions</summary>
            <Assumptions />
          </details>
        </div>
        <div className="assumptions-desktop">
          <a className="brand" href="#/overview">RetailLab</a>
          <nav aria-label="Pages">
            {GROUPS.map((group) => (
              <div key={group} style={{ display: 'contents' }}>
                <span className="group">{group}</span>
                {KEYS.filter((key) => views[key].group === group).map((key) => (
                  <a key={key} href={`#/${key}`} aria-current={key === route ? 'page' : undefined}>{views[key].label}</a>
                ))}
              </div>
            ))}
          </nav>
          <Assumptions />
        </div>
      </aside>
      <main>
        <SourceBanner />
        <ErrorBoundary key={route}>
          <Suspense fallback={<Loading />}><View /></Suspense>
        </ErrorBoundary>
      </main>
    </div>
  )
}

function SourceBanner() {
  const { data, updating, apiError } = useApp()
  return (
    <>
      {data.source !== 'hillstrom' && <div className="banner">Synthetic demo data. These numbers are illustrative, not the published Hillstrom result.</div>}
      {apiError && <div className="banner" role="alert">Could not update the readout: {apiError}. Showing the last result.</div>}
      <div className={`updating${updating ? ' on' : ''}`} role="status" aria-live="polite">{updating ? 'Updating…' : ''}</div>
    </>
  )
}

function Assumptions() {
  const { data, settings, update, reset, assumptions } = useApp()
  const { margins } = data
  return (
    <section className="assumptions" aria-label="Assumptions">
      <h2>Assumptions</h2>
      <p className="hint">
        {data.source === 'hillstrom' ? `Hillstrom e-mail experiment, ${data.customers.toLocaleString('en-US')} customers.` : 'Synthetic demo data.'}
      </p>
      <label className="field">
        <span>E-mail tested</span>
        <select value={settings.variant} onChange={(event) => update({ variant: event.target.value as Variant })}>
          {VARIANT_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
        </select>
      </label>
      <label className="field">
        <span>Gross margin basis</span>
        <select value={settings.marginSource} onChange={(event) => update({ marginSource: event.target.value })}>
          {margins.sectors.map((row) => <option key={row.sector} value={row.sector}>{row.sector}</option>)}
          <option value={CUSTOM_MARGIN}>{CUSTOM_MARGIN}</option>
        </select>
        <span className="hint">
          {margins.source === 'damodaran' ? `Damodaran sector averages (${margins.as_of}).` : 'Placeholder margins.'}
        </span>
      </label>
      {settings.marginSource === CUSTOM_MARGIN ? (
        <label className="field">
          <span className="row"><span>Gross margin</span><span className="value">{pct(settings.customMargin)}</span></span>
          <input type="range" min={0.05} max={0.8} step={0.01} value={settings.customMargin}
            onChange={(event) => update({ customMargin: Number(event.target.value) })} />
        </label>
      ) : (
        <p className="hint">Gross margin in use: <b>{pct(assumptions.gross_margin, 1)}</b></p>
      )}
      <label className="field">
        <span>Cost per e-mail ($)</span>
        <NumberInput value={settings.emailCost} min={0} max={2} step={0.01} onChange={(emailCost) => update({ emailCost })} />
        <span className="hint">Fully loaded: send, creative and offer cost per customer contacted.</span>
      </label>
      <label className="field">
        <span className="row"><span>Minimum ROI to ship</span><span className="value">{settings.minimumRoiPct}%</span></span>
        <input type="range" min={-50} max={200} step={5} value={settings.minimumRoiPct}
          onChange={(event) => update({ minimumRoiPct: Number(event.target.value) })} />
      </label>
      <label className="field">
        <span>Customers mailable per week</span>
        <NumberInput value={settings.weeklyCustomers} min={1000} max={500_000} step={1000} onChange={(weeklyCustomers) => update({ weeklyCustomers })} />
      </label>
      <label className="toggle">
        <input type="checkbox" checked={settings.useCuped} onChange={(event) => update({ useCuped: event.target.checked })} />
        CUPED adjustment
      </label>
      <p className="hint">Adjusts revenue with past-year spend to reduce variance.</p>
      <button type="button" className="reset" onClick={reset}>
        Reset to defaults
      </button>
    </section>
  )
}

/* eslint-disable react-refresh/only-export-components -- the provider and its hook belong together */
// Sidebar assumptions shared by every page, and the API readout priced at them.

import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'
import { Loading } from './components/ui'
import type { Data, ReadoutResponse, Variant } from './data/types'
import { useApi, type Params } from './lib/api'

export const CUSTOM_MARGIN = 'Custom margin'
export const VARIANT_OPTIONS: { value: Variant; label: string }[] = [
  { value: 'any', label: 'Any e-mail (pooled)' },
  { value: 'mens', label: "Men's e-mail" },
  { value: 'womens', label: "Women's e-mail" },
]

export interface Settings {
  variant: Variant
  marginSource: string
  customMargin: number
  emailCost: number
  minimumRoiPct: number
  weeklyCustomers: number
  useCuped: boolean
}

export const DEFAULTS: Settings = {
  variant: 'any',
  marginSource: 'Apparel',
  customMargin: 0.4,
  emailCost: 0.18,
  minimumRoiPct: 0,
  weeklyCustomers: 10_000,
  useCuped: true,
}

/** The assumptions as the pages display them; the API receives the same values as `params`. */
export interface Assumptions {
  variant: Variant
  gross_margin: number
  contact_cost: number
  minimum_roi: number
  weekly_customers: number
  use_cuped: boolean
}

const STORAGE_KEY = 'retaillab.settings'

function loadSettings(): Settings {
  try {
    return { ...DEFAULTS, ...JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '{}') }
  } catch {
    return DEFAULTS
  }
}

interface AppState {
  data: Data
  settings: Settings
  update: (patch: Partial<Settings>) => void
  reset: () => void
  assumptions: Assumptions
  /** Query parameters every API call carries. */
  params: Params
  readout: ReadoutResponse
  /** True while a newer readout than the one on screen is on its way. */
  updating: boolean
  /** Set when the latest request failed; the last good readout stays on screen. */
  apiError?: string
}

const Context = createContext<AppState | null>(null)

export function AppProvider({ data, children }: { data: Data; children: ReactNode }) {
  const [settings, setSettings] = useState<Settings>(loadSettings)
  const sector = data.margins.sectors.find((row) => row.sector === settings.marginSource)
  const assumptions: Assumptions = {
    variant: settings.variant,
    gross_margin: sector ? sector.gross_margin : settings.customMargin,
    contact_cost: settings.emailCost,
    minimum_roi: settings.minimumRoiPct / 100,
    weekly_customers: settings.weeklyCustomers,
    use_cuped: settings.useCuped,
  }
  const params: Params = {
    variant: assumptions.variant,
    margin: assumptions.gross_margin,
    cost: assumptions.contact_cost,
    min_roi: assumptions.minimum_roi,
    weekly: assumptions.weekly_customers,
    cuped: assumptions.use_cuped,
  }
  const api = useApi<ReadoutResponse>('/api/readout', params)
  const value = useMemo(() => {
    if (!api.data) return null
    const save = (next: Settings) => {
      try { localStorage.setItem(STORAGE_KEY, JSON.stringify(next)) } catch { /* private mode: keep in memory */ }
      return next
    }
    return {
      data, settings, assumptions, params, readout: api.data, updating: api.loading, apiError: api.error,
      update: (patch: Partial<Settings>) => setSettings((previous) => save({ ...previous, ...patch })),
      reset: () => setSettings(save(DEFAULTS)),
    }
    // assumptions and params derive from settings and data
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, settings, api.data, api.loading, api.error])
  if (!value) {
    return api.error
      ? <main><div className="callout danger" role="alert">Could not reach the RetailLab API. {api.error}</div></main>
      : <main><Loading /></main>
  }
  return <Context.Provider value={value}>{children}</Context.Provider>
}

export function useApp(): AppState {
  const value = useContext(Context)
  if (!value) throw new Error('useApp outside AppProvider')
  return value
}

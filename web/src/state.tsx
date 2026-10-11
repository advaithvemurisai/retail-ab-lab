/* eslint-disable react-refresh/only-export-components -- the provider and its hook belong together */
// Sidebar assumptions shared by every page, and the readouts built from them.

import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'
import type { Data, Variant } from './data/types'
import { analyze, type Assumptions, type Readout } from './lib/readout'

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

const STORAGE_KEY = 'retaillab.settings'

function loadSettings(): Settings {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '{}')
    return { ...DEFAULTS, ...saved }
  } catch {
    return DEFAULTS
  }
}

interface AppState {
  data: Data
  settings: Settings
  update: (patch: Partial<Settings>) => void
  reset: () => void
  grossMargin: number
  assumptions: (variant?: Variant) => Assumptions
  readout: (variant?: Variant) => Readout
}

const Context = createContext<AppState | null>(null)

export function AppProvider({ data, children }: { data: Data; children: ReactNode }) {
  const [settings, setSettings] = useState<Settings>(loadSettings)
  const value = useMemo<AppState>(() => {
    const sector = data.margins.sectors.find((row) => row.sector === settings.marginSource)
    const grossMargin = sector ? sector.gross_margin : settings.customMargin
    const assumptions = (variant?: Variant): Assumptions => ({
      variant: variant ?? settings.variant,
      gross_margin: grossMargin,
      contact_cost: settings.emailCost,
      minimum_roi: settings.minimumRoiPct / 100,
      weekly_customers: settings.weeklyCustomers,
      use_cuped: settings.useCuped,
      alpha: 0.05,
    })
    const cache = new Map<Variant, Readout>()
    const readout = (variant?: Variant) => {
      const a = assumptions(variant)
      if (!cache.has(a.variant)) cache.set(a.variant, analyze(data, a))
      return cache.get(a.variant)!
    }
    const save = (next: Settings) => {
      try { localStorage.setItem(STORAGE_KEY, JSON.stringify(next)) } catch { /* private mode: keep in memory */ }
      return next
    }
    return {
      data,
      settings,
      update: (patch) => setSettings((previous) => save({ ...previous, ...patch })),
      reset: () => setSettings(save(DEFAULTS)),
      grossMargin,
      assumptions,
      readout,
    }
  }, [data, settings])
  return <Context.Provider value={value}>{children}</Context.Provider>
}

export function useApp(): AppState {
  const value = useContext(Context)
  if (!value) throw new Error('useApp outside AppProvider')
  return value
}

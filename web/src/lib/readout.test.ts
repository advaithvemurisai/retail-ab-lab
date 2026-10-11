import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import type { Data } from '../data/types'
import { analyze, decide, type Assumptions } from './readout'
import { normCdf, normPpf, quantile } from './stats'

// Both files come from `npm run data` (scripts/build_web_data.py), so the Python readouts and the
// precomputed statistics always describe the same data.
const read = (path: string) => JSON.parse(readFileSync(resolve(__dirname, path), 'utf8'))
const data: Data = read('../../public/data/readout.json')
const cases: {
  assumptions: Assumptions
  verdict: { label: string; tone: string; reasons: string[]; next_step: string; additional_weeks: number }
  revenue_lift: number
  revenue_lift_ci: [number, number]
  economics: Record<string, number | null>
  contribution: Record<string, number>
  break_even_lift: number
  planned_lift: number
  power: number
  required_n: number
  additional_weeks: number
}[] = read('../fixtures/parity.json')

const close = (actual: number, expected: number | null, tolerance = 1e-9) => {
  if (expected === null) return expect(Number.isFinite(actual)).toBe(false) // Python's inf
  expect(Math.abs(actual - expected)).toBeLessThanOrEqual(tolerance * Math.max(1, Math.abs(expected)))
}

describe('normal distribution', () => {
  it('matches scipy at the values the app uses', () => {
    close(normPpf(0.975), 1.959963984540054, 1e-12)
    close(normPpf(0.8), 0.8416212335729143, 1e-12)
    close(normPpf(0.95), 1.6448536269514722, 1e-12)
    close(normCdf(-1.959963984540054), 0.025, 1e-12)
    close(normCdf(0), 0.5, 1e-15)
  })

  it('interpolates quantiles like numpy', () => {
    expect(quantile([1, 2, 3, 4], 0.5)).toBe(2.5)
    expect(quantile([1, 2, 3, 4], 0.025)).toBeCloseTo(1.075)
  })
})

describe('readout matches Python', () => {
  it.each(cases.map((c) => [JSON.stringify(c.assumptions), c] as const))('%s', (_, expected) => {
    const r = analyze(data, expected.assumptions)
    expect(r.verdict).toEqual(expected.verdict)
    close(r.revenue_lift, expected.revenue_lift)
    close(r.revenue_lift_ci[0], expected.revenue_lift_ci[0])
    close(r.revenue_lift_ci[1], expected.revenue_lift_ci[1])
    for (const [key, value] of Object.entries(expected.economics)) {
      close(r.economics[key as keyof typeof r.economics], value)
    }
    // Draws are stored to 9 decimals, so scaled to the campaign they can move by about a cent.
    close(r.contribution.ci_low, expected.contribution.ci_low, 1e-6)
    close(r.contribution.ci_high, expected.contribution.ci_high, 1e-6)
    expect(r.contribution.chance_of_loss).toBe(expected.contribution.chance_of_loss)
    close(r.break_even_lift, expected.break_even_lift)
    close(r.planned_lift, expected.planned_lift)
    close(r.power, expected.power, 1e-9)
    expect(r.required_n).toBe(expected.required_n)
    expect(r.additional_weeks).toBe(expected.additional_weeks)
  })

  it('covers every verdict branch the fixtures can reach', () => {
    expect(new Set(cases.map((c) => c.verdict.label)).size).toBeGreaterThan(1)
  })
})

describe('decision rules', () => {
  const base = { validity_failed: false, primary_lift: 0.2, primary_p: 0.01, contribution_low: 10, contribution_high: 100, roi: 0.5 }
  it('distrusts a broken split before anything else', () => {
    expect(decide({ ...base, validity_failed: true }).label).toBe("DON'T TRUST")
  })
  it('ships a significant, profitable lift', () => {
    expect(decide(base).label).toBe('SHIP')
  })
  it('keeps testing an underpowered null result', () => {
    const verdict = decide({ ...base, primary_p: 0.3, power: 0.4, additional_weeks: 3 })
    expect(verdict.label).toBe('KEEP TESTING')
    expect(verdict.additional_weeks).toBe(3)
  })
  it('rejects a lift that misses the ROI hurdle', () => {
    expect(decide({ ...base, minimum_roi: 1 }).reasons[1]).toBe('but ROI of +50% misses the +100% hurdle.')
  })
})

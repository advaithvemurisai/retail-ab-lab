// TypeScript port of src/retaillab/analysis.py, decision.py and the arithmetic in finance.py and
// power.py. Everything that needs the customer-level data is precomputed by
// scripts/build_web_data.py; this file only applies the assumptions to it. readout.test.ts checks
// the result against Python readouts, so a change to either side must be made in both.

import type { Data, MetricBlock, MetricKey, SegmentColumn, Variant, VariantBlock, Welch } from '../data/types'
import { pct } from './format'
import { normCdf, normPpf, quantile } from './stats'

export const MINIMUM_PLANNED_LIFT = 0.05

export interface Assumptions {
  variant: Variant
  gross_margin: number
  contact_cost: number
  minimum_roi: number
  weekly_customers: number
  use_cuped: boolean
  alpha: number
}

export type Tone = 'success' | 'warning' | 'danger' | 'invalid'

export interface Verdict {
  label: string
  tone: Tone
  reasons: string[]
  next_step: string
  additional_weeks: number
}

export interface Economics {
  customers_contacted: number
  incremental_revenue: number
  gross_profit: number
  marketing_cost: number
  contribution: number
  roi: number
}

export interface Readout {
  assumptions: Assumptions
  block: VariantBlock
  metric: MetricBlock
  revenue: Welch
  baseline_revenue: number
  revenue_lift: number
  revenue_lift_ci: [number, number]
  economics: Economics
  contribution: { ci_low: number; ci_high: number; chance_of_loss: number }
  break_even_lift: number
  planned_lift: number
  power: number
  required_n: number
  additional_weeks: number
  verdict: Verdict
}

export const metricKey = (a: Pick<Assumptions, 'use_cuped'>): MetricKey => (a.use_cuped ? 'cuped' : 'raw')

export function breakEvenLift(costPerContact: number, baselineRevenue: number, grossMargin: number): number {
  if (baselineRevenue <= 0 || grossMargin <= 0) return Infinity
  return costPerContact / (baselineRevenue * grossMargin)
}

export function powerTwoMeans(delta: number, sdControl: number, sdTreatment: number, nControl: number, nTreatment: number, alpha = 0.05): number {
  if (nControl <= 0 || nTreatment <= 0) return 0
  const se = Math.sqrt(sdControl ** 2 / nControl + sdTreatment ** 2 / nTreatment)
  if (se === 0) return 1
  const z = normPpf(1 - alpha / 2)
  const shift = Math.abs(delta) / se
  return normCdf(shift - z) + normCdf(-shift - z)
}

export function requiredTotalN(delta: number, sd: number, treatmentShare = 0.5, alpha = 0.05, power = 0.8, sdTreatment?: number): number {
  if (delta === 0) return Infinity
  const sdT = sdTreatment ?? sd
  const z = normPpf(1 - alpha / 2) + normPpf(power)
  const variance = sd ** 2 / (1 - treatmentShare) + sdT ** 2 / treatmentShare
  return Math.ceil((z ** 2 * variance) / delta ** 2)
}

export const weeksNeeded = (totalN: number, weeklyCustomers: number): number =>
  weeklyCustomers <= 0 ? Infinity : totalN / weeklyCustomers

export function decide(input: {
  validity_failed: boolean
  primary_lift: number
  primary_p: number
  contribution_low: number
  contribution_high: number
  segment_harm?: boolean
  roi?: number
  minimum_roi?: number
  power?: number
  additional_weeks?: number
  alpha?: number
  chance_of_loss?: number
}): Verdict {
  const { validity_failed, primary_lift, primary_p, contribution_high } = input
  const { segment_harm = false, roi = 0, minimum_roi = 0, power = 0, additional_weeks = 0, alpha = 0.05, chance_of_loss = 0 } = input
  const verdict = (label: string, tone: Tone, reasons: string[], next_step: string, weeks = 0): Verdict =>
    ({ label, tone, reasons, next_step, additional_weeks: weeks })
  if (validity_failed) {
    return verdict("DON'T TRUST", 'invalid', ['Arm sizes do not match the designed split (sample ratio mismatch).'],
      'Find the assignment or logging fault and rerun the test.')
  }
  if (primary_p < alpha && primary_lift < 0) {
    return verdict("DON'T SHIP", 'danger', [`Revenue per customer is significantly lower (${pct(primary_lift, 1, true)}).`],
      'Keep the current experience.')
  }
  if (contribution_high < 0) {
    return verdict("DON'T SHIP", 'danger', ['Even the optimistic end of the contribution interval loses money.'],
      'Do not roll out a money-losing campaign.')
  }
  if (segment_harm) {
    return verdict("DON'T SHIP", 'danger', ['At least one customer segment is significantly worse off after BH correction.'],
      'Investigate the harmed segment before rollout.')
  }
  if (primary_p < alpha && primary_lift > 0) {
    if (roi >= minimum_roi) {
      const reasons = [
        `Revenue per customer is significantly higher (${pct(primary_lift, 1, true)}).`,
        Number.isFinite(roi)
          ? `ROI of ${pct(roi, 0, true)} clears the ${pct(minimum_roi, 0, true)} hurdle.`
          : 'The e-mail costs nothing to send, so any profitable lift clears the hurdle.',
      ]
      if (chance_of_loss > 0.1) {
        return verdict('SHIP', 'success', [...reasons, `There is still a ${pct(chance_of_loss)} chance it loses money.`],
          'Roll out to a holdout-backed share first and watch contribution.')
      }
      return verdict('SHIP', 'success', reasons, 'Roll out with monitoring.')
    }
    return verdict("DON'T SHIP", 'danger',
      [`Revenue per customer is significantly higher (${pct(primary_lift, 1, true)}),`, `but ROI of ${pct(roi, 0, true)} misses the ${pct(minimum_roi, 0, true)} hurdle.`],
      'Cut contact cost or target higher-return segments, then retest.')
  }
  if (power >= 0.8) {
    return verdict("DON'T SHIP", 'danger', [`No significant lift, and the test had ${pct(power)} power to detect break-even.`],
      'Keep the current experience.')
  }
  const weeks = Math.max(1, additional_weeks)
  return verdict('KEEP TESTING', 'warning',
    ['The evidence is not decisive yet.', `Power to detect a break-even lift is ${pct(power)}, below the 80% target.`],
    `Run about ${weeks} more week(s) or improve sensitivity.`, weeks)
}

export function analyze(data: Data, a: Assumptions): Readout {
  const block = data.variants[a.variant]
  const metric = block.metrics[metricKey(a)]
  const revenue = metric.revenue
  const baseline = block.baseline_revenue
  const revenueLift = revenue.difference / baseline

  // finance.pnl: the treatment arm's incremental P&L against control.
  const contacted = revenue.n_treatment
  const incremental = revenue.difference * contacted
  const grossProfit = incremental * a.gross_margin
  const marketingCost = contacted * a.contact_cost
  const contributionValue = grossProfit - marketingCost
  const economics: Economics = {
    customers_contacted: contacted,
    incremental_revenue: incremental,
    gross_profit: grossProfit,
    marketing_cost: marketingCost,
    contribution: contributionValue,
    roi: marketingCost ? contributionValue / marketingCost : Infinity,
  }

  // finance.contribution_distribution over the precomputed bootstrap draws.
  const outcomes = metric.draws.map((d) => (d * a.gross_margin - a.contact_cost) * contacted).sort((x, y) => x - y)
  const contribution = {
    ci_low: quantile(outcomes, 0.025),
    ci_high: quantile(outcomes, 0.975),
    chance_of_loss: outcomes.filter((value) => value < 0).length / outcomes.length,
  }

  const breakEven = breakEvenLift(a.contact_cost, baseline, a.gross_margin)
  const plannedLift = breakEven > 0 && breakEven < Infinity ? breakEven : MINIMUM_PLANNED_LIFT
  const delta = plannedLift * baseline
  const power = powerTwoMeans(delta, revenue.control_sd, revenue.treatment_sd, revenue.n_control, revenue.n_treatment, a.alpha)
  const nTotal = revenue.n_control + revenue.n_treatment
  const requiredN = requiredTotalN(delta, revenue.control_sd, revenue.n_treatment / nTotal, a.alpha, 0.8, revenue.treatment_sd)
  const shortfall = Math.max(0, requiredN - nTotal)
  const additionalWeeks = a.weekly_customers ? Math.ceil(shortfall / a.weekly_customers) : 0

  const segmentHarm = metric.segments.history_segment.some((row) => row.significant && row.difference < 0)
  // The pooled e-mail is the prespecified primary; picking one creative is one of two looks.
  const verdictP = a.variant === 'any' ? revenue.p_value : Math.min(1, revenue.p_value * 2)
  const verdict = decide({
    validity_failed: data.validity.failed,
    primary_lift: revenueLift,
    primary_p: verdictP,
    contribution_low: contribution.ci_low,
    contribution_high: contribution.ci_high,
    segment_harm: segmentHarm,
    roi: economics.roi,
    minimum_roi: a.minimum_roi,
    power,
    additional_weeks: additionalWeeks,
    alpha: a.alpha,
    chance_of_loss: contribution.chance_of_loss,
  })
  return {
    assumptions: a,
    block,
    metric,
    revenue,
    baseline_revenue: baseline,
    revenue_lift: revenueLift,
    revenue_lift_ci: [revenue.ci_low / baseline, revenue.ci_high / baseline],
    economics,
    contribution,
    break_even_lift: breakEven,
    planned_lift: plannedLift,
    power,
    required_n: requiredN,
    additional_weeks: additionalWeeks,
    verdict,
  }
}

export interface PlanRow {
  segment: string
  audience: number
  difference: number
  profit_per_send: number
  profit_low: number
  profit_high: number
  profit_per_dollar: number
  p_value: number
  p_adjusted: number
  significant: boolean
  selected: boolean
  send_count: number
}

/** Targeting page: segment rows priced per send, then finance.greedy_allocation to a cap. */
export function targetingPlan(data: Data, a: Assumptions, by: SegmentColumn, cap: number, requireSignificant: boolean): PlanRow[] {
  const rows = data.variants[a.variant].metrics[metricKey(a)].segments[by].map((row) => {
    const profit = row.difference * a.gross_margin - a.contact_cost
    return {
      segment: row.segment,
      audience: data.audience[by][row.segment],
      difference: row.difference,
      profit_per_send: profit,
      profit_low: row.ci_low * a.gross_margin - a.contact_cost,
      profit_high: row.ci_high * a.gross_margin - a.contact_cost,
      profit_per_dollar: a.contact_cost ? profit / a.contact_cost : profit,
      p_value: row.p_value,
      p_adjusted: row.p_adjusted,
      significant: row.significant,
      selected: false,
      send_count: 0,
    }
  })
  rows.sort((x, y) => y.profit_per_dollar - x.profit_per_dollar)
  let remaining = cap
  for (const row of rows) {
    const eligible = row.profit_per_dollar > 0 && (!requireSignificant || row.significant)
    const amount = eligible ? Math.min(remaining, row.audience) : 0
    row.selected = amount > 0
    row.send_count = amount
    remaining -= amount
  }
  return rows
}

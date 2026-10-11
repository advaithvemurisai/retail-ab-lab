// Shapes written by scripts/build_web_data.py. Field names follow the Python dicts they come from.

export type Variant = 'any' | 'mens' | 'womens'
export type Arm = 'control' | 'mens' | 'womens'
export type SegmentColumn = 'history_segment' | 'channel' | 'zip_code' | 'newbie'
export type MetricKey = 'raw' | 'cuped'

export interface Welch {
  control_mean: number
  treatment_mean: number
  control_sd: number
  treatment_sd: number
  n_control: number
  n_treatment: number
  difference: number
  se: number
  ci_low: number
  ci_high: number
  p_value: number
}

export interface SegmentRow {
  segment: string
  customers: number
  control_mean: number
  treatment_mean: number
  difference: number
  ci_low: number
  ci_high: number
  p_value: number
  p_adjusted: number
  significant: boolean
}

export interface MetricBlock {
  revenue: Welch
  /** 1,000 bootstrap draws of the treatment-minus-control mean, per customer. */
  draws: number[]
  segments: Record<SegmentColumn, SegmentRow[]>
}

export interface VariantBlock {
  label: string
  baseline_revenue: number
  conversion: {
    control_rate: number
    treatment_rate: number
    relative_lift: number
    lift_ci_low: number
    lift_ci_high: number
    p_value: number
  }
  cuped: { theta: number; correlation: number; variance_reduction: number }
  balance: { covariate: string; smd: number; balanced: boolean }[]
  attribution: { attributed: number; incremental: number; baseline: number; gap_pct: number | null }
  pooled_sd: Record<MetricKey, number>
  metrics: Record<MetricKey, MetricBlock>
}

export interface Sector {
  sector: string
  gross_margin: number
  operating_margin: number
}

export interface PromotionBlock {
  summary: { arm: Arm; customers: number; conversion: number; revenue: number; sd: number }[]
  pairs: {
    left: Arm
    right: Arm
    difference: number
    ci_low: number
    ci_high: number
    p_value: number
    p_adjusted: number
    significant: boolean
  }[]
}

export interface Data {
  source: 'hillstrom' | 'demo'
  customers: number
  arm_labels: Record<Arm, string>
  segment_columns: Record<SegmentColumn, string>
  margins: { as_of: string; source: 'damodaran' | 'placeholder'; sectors: Sector[] }
  validity: {
    counts: Record<Arm, number>
    expected: Record<Arm, number>
    chi2: number
    p_value: number
    failed: boolean
  }
  variants: Record<Variant, VariantBlock>
  audience: Record<SegmentColumn, Record<string, number>>
  promotion: Record<MetricKey, PromotionBlock>
  pitfalls: {
    looks: number[]
    peeking: number[]
    broken_split: { true_lift: number; reported_lift: number; srm_failed: boolean; srm_p: number }
    placebo: { slice: string; raw: number; bh: number }[]
  }
  warehouse: {
    tables: { table: string; rows: number }[]
    arms: { arm: Arm; customers: number; incremental_revenue: number }[]
    sql: string
  }
}

// Responses from the API (src/retaillab/api.py). Python's inf arrives as null.

export interface Verdict {
  label: string
  tone: 'success' | 'warning' | 'danger' | 'invalid'
  reasons: string[]
  next_step: string
  additional_weeks: number
}

export interface Priced {
  baseline_revenue: number
  revenue_lift: number
  revenue_lift_ci: [number, number]
  economics: {
    customers_contacted: number
    incremental_revenue: number
    gross_profit: number
    marketing_cost: number
    contribution: number
    roi: number | null
  }
  contribution: { ci_low: number; ci_high: number; chance_of_loss: number }
  break_even_lift: number | null
  planned_lift: number
  power: number
  required_n: number | null
  additional_weeks: number
  verdict: Verdict
}

export interface ReadoutResponse {
  readouts: Record<Variant, Priced>
  sectors: { sector: string; gross_margin: number; break_even_lift: number | null; contribution_per_10k: number; verdict: string }[]
  promotion: {
    arms: { arm: Arm; contribution_per_10k: number }[]
    best: Arm
    runner_up: Arm
    best_contribution_per_10k: number
    decision: 'roll_out' | 'lean' | 'send_neither'
  }
  mart_pnl: {
    arm: Arm
    sector: string
    customers: number
    incremental_revenue: number
    gross_profit: number
    marketing_cost: number
    contribution: number
  }[]
}

export interface TargetingResponse {
  rows: (SegmentRow & {
    audience: number
    profit_per_send: number
    profit_low: number
    profit_high: number
    profit_per_dollar: number
    selected: boolean
    send_count: number
  })[]
  customers: number
  planned: number
  everyone: number
  audience: number
}

export interface PlanningResponse {
  n_raw: number | null
  n_cuped: number | null
  n_used: number | null
  weeks: number | null
  weeks_saved: number | null
  curve: { weeks: number; raw: number; cuped: number }[]
}

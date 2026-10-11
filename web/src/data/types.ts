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

export const ARM_COLORS = { control: 'var(--control)', mens: 'var(--accent)', womens: 'var(--violet)' } as const
export const axisProps = { stroke: 'var(--line)', tick: { fill: 'var(--muted)', fontSize: 12 }, tickLine: false } as const
export const gridProps = { stroke: 'var(--grid)', vertical: false } as const
export const tooltipStyle = {
  contentStyle: { background: 'var(--card)', border: '1px solid var(--line)', borderRadius: 8, color: 'var(--ink)', fontSize: 13 },
  labelStyle: { color: 'var(--ink)', fontWeight: 600 },
  itemStyle: { color: 'var(--ink)' },
} as const

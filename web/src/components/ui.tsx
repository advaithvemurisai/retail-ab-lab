import { Component, useEffect, useRef, useState, type ReactElement, type ReactNode } from 'react'
import { ResponsiveContainer } from 'recharts'
import type { Verdict } from '../lib/readout'

export function Header({ eyebrow, title, lede }: { eyebrow: string; title: string; lede?: ReactNode }) {
  return (
    <header>
      <div className="eyebrow">{eyebrow}</div>
      <h1>{title}</h1>
      {lede && <p className="lede">{lede}</p>}
    </header>
  )
}

export function VerdictCard({ verdict, context }: { verdict: Verdict; context: string }) {
  return (
    <section className={`verdict ${verdict.tone}`} aria-live="polite">
      <div className="eyebrow">Recommendation · {context}</div>
      <h2>{verdict.label}</h2>
      <p>{verdict.reasons.join(' ')}</p>
      <p><b>Next:</b> {verdict.next_step}</p>
    </section>
  )
}

export function Kpi({ label, value, note, title }: { label: string; value: string; note?: string; title?: string }) {
  return (
    <div className="card kpi" title={title}>
      <span className="label">{label}</span>
      <span className="value">{value}</span>
      {note && <span className="note">{note}</span>}
    </div>
  )
}

export interface Column<T> {
  label: string
  value: (row: T) => ReactNode
  text?: boolean
}

export function Table<T>({ rows, columns, caption }: { rows: T[]; columns: Column<T>[]; caption?: string }) {
  return (
    <div className="table-wrap">
      <table>
        {caption && <caption className="sr-only">{caption}</caption>}
        <thead>
          <tr>{columns.map((column) => <th key={column.label} className={column.text ? 'text' : undefined}>{column.label}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>{columns.map((column) => <td key={column.label} className={column.text ? 'text' : undefined}>{column.value(row)}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function ChartBox({ children, size = '' }: { children: ReactElement; size?: 'tall' | 'short' | '' }) {
  return <div className={`chart ${size}`}><ResponsiveContainer width="100%" height="100%">{children}</ResponsiveContainer></div>
}

export function Loading() {
  return <div className="skeleton" role="status" aria-label="Loading" />
}

export class ErrorBoundary extends Component<{ children: ReactNode }, { error?: Error }> {
  state: { error?: Error } = {}
  static getDerivedStateFromError(error: Error) { return { error } }
  render() {
    return this.state.error
      ? <div className="callout danger" role="alert"><strong>Could not render this page.</strong> <span className="muted">{this.state.error.message}</span></div>
      : this.props.children
  }
}

function useWidth<T extends HTMLElement>(): [React.RefObject<T>, number] {
  const ref = useRef<T>(null)
  const [width, setWidth] = useState(640)
  useEffect(() => {
    if (!ref.current) return
    const observer = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width))
    observer.observe(ref.current)
    return () => observer.disconnect()
  }, [])
  return [ref, width]
}

function niceTicks(lo: number, hi: number, count = 5): number[] {
  const span = hi - lo || 1
  const step0 = span / count
  const magnitude = 10 ** Math.floor(Math.log10(step0))
  const step = [1, 2, 2.5, 5, 10].map((m) => m * magnitude).find((s) => s >= step0) ?? step0
  const ticks: number[] = []
  for (let t = Math.ceil(lo / step) * step; t <= hi + step * 1e-9; t += step) ticks.push(Math.round(t / step) * step)
  return ticks
}

export interface RangeRow {
  label: string
  value: number
  low?: number
  high?: number
  color?: string
  /** Draw a bar from zero instead of a dot. */
  bar?: boolean
  text?: string
}

export interface RangeRef {
  x: number
  label?: string
  color?: string
  dashed?: boolean
}

/**
 * Horizontal estimates with intervals: one row per label, optional reference lines and a shaded
 * band. Used wherever the Streamlit app had a horizontal bar or dot with error bars.
 */
export function RangePlot({ rows, refs = [], band, format, includeZero = true, labelWidth = 170, title }: {
  rows: RangeRow[]
  refs?: RangeRef[]
  band?: { low: number; high: number; color?: string }
  format: (value: number) => string
  includeZero?: boolean
  labelWidth?: number
  title: string
}) {
  const [ref, width] = useWidth<HTMLDivElement>()
  const narrow = width < 520
  const left = narrow ? 8 : labelWidth
  const right = 48
  const top = refs.some((r) => r.label) ? 34 : 12
  const rowHeight = narrow ? 52 : 40
  const height = top + rows.length * rowHeight + 26
  const values = [
    ...rows.flatMap((row) => [row.value, row.low ?? row.value, row.high ?? row.value]),
    ...refs.map((r) => r.x), ...(band ? [band.low, band.high] : []), ...(includeZero ? [0] : []),
  ].filter(Number.isFinite)
  let lo = Math.min(...values)
  let hi = Math.max(...values)
  const pad = (hi - lo || 1) * 0.06
  lo = includeZero && lo >= 0 ? 0 : lo - pad
  hi += pad
  const x = (value: number) => left + ((value - lo) / (hi - lo)) * (width - left - right)
  const ticks = niceTicks(lo, hi, narrow ? 3 : 5)
  const rowY = (i: number) => top + i * rowHeight + (narrow ? 34 : rowHeight / 2)
  return (
    <div ref={ref}>
      <svg className="plot" width={width} height={height} role="img" aria-label={title}>
        {ticks.map((t) => (
          <g key={t}>
            <line x1={x(t)} x2={x(t)} y1={top - 4} y2={height - 22} stroke="var(--grid)" />
            <text x={x(t)} y={height - 6} textAnchor="middle">{format(t)}</text>
          </g>
        ))}
        {band && <rect x={x(band.low)} width={Math.max(1, x(band.high) - x(band.low))} y={top - 4} height={height - top - 18} fill={band.color ?? 'var(--accent)'} opacity={0.14} />}
        {rows.map((row, i) => {
          const y = rowY(i)
          const color = row.color ?? 'var(--accent)'
          return (
            <g key={row.label}>
              <text className="label" x={narrow ? left : left - 10} y={narrow ? y - 18 : y + 4} textAnchor={narrow ? 'start' : 'end'}>{row.label}</text>
              {row.bar && <rect x={Math.min(x(0), x(row.value))} width={Math.abs(x(row.value) - x(0))} y={y - 11} height={22} rx={3} fill={color} />}
              {row.low !== undefined && row.high !== undefined && (
                <g stroke="var(--ink)" strokeWidth={1.5}>
                  <line x1={x(row.low)} x2={x(row.high)} y1={y} y2={y} />
                  <line x1={x(row.low)} x2={x(row.low)} y1={y - 6} y2={y + 6} />
                  <line x1={x(row.high)} x2={x(row.high)} y1={y - 6} y2={y + 6} />
                </g>
              )}
              {!row.bar && <circle cx={x(row.value)} cy={y} r={6} fill={color} stroke="var(--card)" strokeWidth={1.5}><title>{`${row.label}: ${format(row.value)}`}</title></circle>}
              {row.text && <text x={x(row.bar ? row.value : row.high ?? row.value) + 6} y={y + 4} className="label">{row.text}</text>}
            </g>
          )
        })}
        {refs.map((r, i) => (
          <g key={i}>
            <line x1={x(r.x)} x2={x(r.x)} y1={top - 6} y2={height - 22} stroke={r.color ?? 'var(--danger)'} strokeWidth={1.5} strokeDasharray={r.dashed ? '5 4' : undefined} />
            {r.label && <text x={x(r.x)} y={top - 12} textAnchor={x(r.x) > width - 90 ? 'end' : 'middle'} className="label" style={{ fill: r.color ?? 'var(--danger)' }}>{r.label}</text>}
          </g>
        ))}
      </svg>
    </div>
  )
}

/** A number box that lets the viewer type freely and clamps only valid values into state. */
export function NumberInput({ value, min, max, step, onChange }: { value: number; min: number; max: number; step: number; onChange: (value: number) => void }) {
  const [text, setText] = useState(String(value))
  useEffect(() => setText(String(value)), [value])
  return (
    <input type="number" inputMode="decimal" value={text} min={min} max={max} step={step}
      onChange={(event) => {
        setText(event.target.value)
        const next = Number(event.target.value)
        if (event.target.value !== '' && Number.isFinite(next) && next >= min && next <= max) onChange(next)
      }}
      onBlur={() => setText(String(value))} />
  )
}

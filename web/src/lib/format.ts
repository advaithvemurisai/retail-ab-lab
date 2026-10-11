// Mirrors Python's format specs ("{:+.0%}", "{:,.0f}") so page text matches the API's verdict text.

/** Python "{:.Nf%}" and, with signed, "{:+.Nf%}". */
export const pct = (value: number, digits = 0, signed = false): string => {
  const text = `${(value * 100).toFixed(digits)}%`
  return signed && !text.startsWith('-') ? `+${text}` : text
}

/** Whole dollars, "-" for losses; signed adds "+" to gains. */
export const money = (value: number, signed = false): string => {
  const sign = signed && value > 0 ? '+' : value < 0 ? '-' : ''
  return `${sign}$${Math.abs(value).toLocaleString('en-US', { maximumFractionDigits: 0 })}`
}

export const cents = (value: number): string => `${value < 0 ? '-' : ''}$${Math.abs(value).toFixed(2)}`

export const num = (value: number, digits = 0): string =>
  value.toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits })

/** ROI is undefined (null from the API) when the campaign costs nothing to send. */
export const formatRoi = (roi: number | null): string => (roi === null ? 'n/a (no e-mail cost)' : pct(roi, 0, true))

/** Python's inf arrives from the API as null. */
export const finite = (value: number | null): number => value ?? Infinity

export const pValue = (p: number, digits = 4): string => (p < 10 ** -digits ? `<${(10 ** -digits).toFixed(digits)}` : p.toFixed(digits))

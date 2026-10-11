/** Standard normal CDF (Hart 1968 via West 2005), accurate to double precision. */
export function normCdf(z: number): number {
  const x = Math.abs(z)
  let tail = 0
  if (x < 37) {
    const e = Math.exp((-x * x) / 2)
    if (x < 7.07106781186547) {
      let b = 3.52624965998911e-2 * x + 0.700383064443688
      b = b * x + 6.37396220353165
      b = b * x + 33.912866078383
      b = b * x + 112.079291497871
      b = b * x + 221.213596169931
      b = b * x + 220.206867912376
      tail = e * b
      b = 8.83883476483184e-2 * x + 1.75566716318264
      b = b * x + 16.064177579207
      b = b * x + 86.7807322029461
      b = b * x + 296.564248779674
      b = b * x + 637.333633378831
      b = b * x + 793.826512519948
      b = b * x + 440.413735824752
      tail /= b
    } else {
      let b = x + 0.65
      b = x + 4 / b
      b = x + 3 / b
      b = x + 2 / b
      b = x + 1 / b
      tail = e / b / 2.506628274631
    }
  }
  return z > 0 ? 1 - tail : tail
}

/** Inverse normal CDF: Acklam's rational approximation, polished by one Halley step. */
export function normPpf(p: number): number {
  if (p <= 0) return -Infinity
  if (p >= 1) return Infinity
  const a = [-3.969683028665376e1, 2.209460984245205e2, -2.759285104469687e2, 1.38357751867269e2, -3.066479806614716e1, 2.506628277459239]
  const b = [-5.447609879822406e1, 1.615858368580409e2, -1.556989798598866e2, 6.680131188771972e1, -1.328068155288572e1]
  const c = [-7.784894002430293e-3, -3.223964580411365e-1, -2.400758277161838, -2.549732539343734, 4.374664141464968, 2.938163982698783]
  const d = [7.784695709041462e-3, 3.224671290700398e-1, 2.445134137142996, 3.754408661907416]
  const low = 0.02425
  let x: number
  if (p < low) {
    const q = Math.sqrt(-2 * Math.log(p))
    x = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
  } else if (p > 1 - low) {
    const q = Math.sqrt(-2 * Math.log(1 - p))
    x = -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
  } else {
    const q = p - 0.5
    const r = q * q
    x = ((((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q) / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
  }
  const e = normCdf(x) - p
  const u = e * Math.sqrt(2 * Math.PI) * Math.exp((x * x) / 2)
  return x - u / (1 + (x * u) / 2)
}

/** Quantile with linear interpolation between order statistics (numpy's default). */
export function quantile(sorted: number[], q: number): number {
  const h = (sorted.length - 1) * q
  const lo = Math.floor(h)
  const hi = Math.min(lo + 1, sorted.length - 1)
  return sorted[lo] + (h - lo) * (sorted[hi] - sorted[lo])
}

import { useEffect, useState } from 'react'

export type Params = Record<string, string | number | boolean>

const cache = new Map<string, Promise<unknown>>()

function load<T>(url: string, signal: AbortSignal): Promise<T> {
  let pending = cache.get(url) as Promise<T> | undefined
  if (!pending) {
    pending = fetch(url, { signal }).then(async (response) => {
      if (!response.ok) throw new Error(`The API answered ${response.status}${response.status === 422 ? ': an assumption is out of range' : ''}`)
      return response.json() as Promise<T>
    })
    pending.catch(() => cache.delete(url)) // let a retry actually retry
    cache.set(url, pending)
  }
  return pending
}

export const apiUrl = (path: string, params: Params): string =>
  `${path}?${new URLSearchParams(Object.entries(params).sort().map(([key, value]) => [key, String(value)]))}`

/**
 * GET an API endpoint whenever its parameters change. Rapid changes (a slider drag) are debounced,
 * and the previous answer stays on screen until the next one arrives.
 */
export function useApi<T>(path: string, params: Params, delay = 150): { data?: T; error?: string; loading: boolean } {
  const url = apiUrl(path, params)
  const [state, setState] = useState<{ url?: string; data?: T; error?: string }>({})
  useEffect(() => {
    const controller = new AbortController()
    const timer = window.setTimeout(() => {
      load<T>(url, controller.signal).then(
        (data) => setState({ url, data }),
        (reason: Error) => { if (reason.name !== 'AbortError') setState((previous) => ({ ...previous, url, error: reason.message })) },
      )
    }, cache.has(url) ? 0 : delay)
    return () => {
      window.clearTimeout(timer)
      controller.abort()
    }
  }, [url, delay])
  return { data: state.data, error: state.url === url ? state.error : undefined, loading: state.url !== url }
}

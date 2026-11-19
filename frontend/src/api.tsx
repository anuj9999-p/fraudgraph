import { useEffect, useState, useCallback } from 'react'
let apiKey = ''
export const setApiKey = (k: string) => { apiKey = k }
export async function api(path: string, init: RequestInit = {}): Promise<any> {
  const headers: Record<string, string> = init.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }
  if (apiKey) headers['X-API-Key'] = apiKey
  const r = await fetch(path, { ...init, headers: { ...headers, ...(init.headers as object) } })
  const body = (await r.json().catch(() => ({}))) ?? {}
  if (!r.ok) throw new Error(typeof body.detail === 'string' ? body.detail : `HTTP ${r.status}`)
  return body
}
export function useApi(path: string | null) {
  const [data, setData] = useState<any>(null); const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false); const [n, setN] = useState(0)
  useEffect(() => {
    if (!path) return; let live = true; setLoading(true); setError(null)
    api(path).then(d => live && setData(d)).catch(e => live && (setError(e.message), setData(null))).finally(() => live && setLoading(false))
    return () => { live = false }
  }, [path, n])
  return { data, error, loading, reload: useCallback(() => setN(x => x + 1), []) }
}
export const catColor: Record<string, string> = { low: '#64748b', medium: '#eab308', high: '#f97316', critical: '#ef4444' }
export const Badge = ({ c }: { c: string }) => <span className="rounded px-1.5 py-0.5 text-xs font-medium" style={{ background: catColor[c] + '33', color: catColor[c] }}>{c}</span>
export const Status = ({ loading, error }: { loading: boolean; error: string | null }) =>
  loading ? <p className="text-slate-400 text-sm" role="status">Loading…</p> : error ? <p className="text-red-400 text-sm" role="alert">{error}</p> : null

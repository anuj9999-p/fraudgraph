import { vi } from 'vitest'
export type Route = [string, number, any]
export function mockFetch(routes: Route[]) {
  const calls: { key: string; init?: RequestInit }[] = []
  vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
    const key = `${init?.method ?? 'GET'} ${url}`; calls.push({ key, init })
    const r = routes.find(([p]) => key.startsWith(p)) ?? [key, 404, { detail: 'no route ' + key }]
    return { ok: r[1] < 400, status: r[1], json: async () => r[2] } as Response
  }))
  return calls
}

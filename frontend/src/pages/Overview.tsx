import { useState } from 'react'
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Cell } from 'recharts'
import { api, useApi, catColor, Badge, Status } from '../api'
export default function Overview({ status, reload }: { status: any; reload: () => void }) {
  const [busy, setBusy] = useState(false); const [err, setErr] = useState<string | null>(null)
  const loaded = !!status?.dataset_loaded
  const cats = ['low', 'medium', 'high', 'critical']
  const c0 = useApi(loaded ? '/api/v1/transactions?category=low&page_size=1' : null), c1 = useApi(loaded ? '/api/v1/transactions?category=medium&page_size=1' : null)
  const c2 = useApi(loaded ? '/api/v1/transactions?category=high&page_size=1' : null), c3 = useApi(loaded ? '/api/v1/transactions?category=critical&page_size=1' : null)
  const alerts = useApi(loaded ? '/api/v1/alerts?page_size=5' : null)
  const trends = useApi(loaded ? '/api/v1/stats/trends?buckets=24' : null)
  const day = (t: number) => Math.round((t / 86400) * 10) / 10
  const tb = (trends.data?.buckets ?? []).map((b: any) => ({ day: day(b.t_start), transactions: b.transactions, alerts: b.alerts }))
  const ct = (trends.data?.cluster_timeline ?? []).map((c: any) => ({ day: day(c.t), clusters: c.clusters, flagged_accounts: c.flagged_accounts }))
  const dist = [c0, c1, c2, c3].map((c, i) => ({ category: cats[i], count: c.data?.total ?? 0 }))
  async function load() { setBusy(true); setErr(null); try { await api('/api/v1/demo/load', { method: 'POST' }); reload() } catch (e: any) { setErr(e.message) } setBusy(false) }
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between"><h1 className="text-xl font-semibold">Executive Overview</h1>
        <button className="btn" onClick={load} disabled={busy}>{busy ? 'Loading demo…' : loaded ? 'Reload demo data' : 'Load synthetic demo'}</button></div>
      <Status loading={false} error={err} />
      {!loaded ? <div className="card text-slate-400">No dataset loaded. Load the synthetic demo to begin.</div> : <>
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {[['Transactions scored', status.transactions], ['Alerts (high+)', alerts.data?.total ?? '…'], ['Suspicious clusters', status.clusters], ['Model', status.model]].map(([k, v]) =>
            <div className="card" key={k as string}><div className="text-xs text-slate-400">{k}</div><div className="text-2xl font-semibold">{v}</div></div>)}
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="card"><h2 className="mb-2 text-sm font-medium">Transactions and alerts over time (days from first event)</h2><Status loading={trends.loading} error={trends.error} />
            <div className="h-56"><ResponsiveContainer><LineChart data={tb}><CartesianGrid stroke="#1e293b" /><XAxis dataKey="day" stroke="#94a3b8" /><YAxis stroke="#94a3b8" /><Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155' }} /><Legend />
              <Line type="monotone" dataKey="transactions" stroke="#38bdf8" dot={false} isAnimationActive={false} /><Line type="monotone" dataKey="alerts" stroke="#ef4444" dot={false} isAnimationActive={false} /></LineChart></ResponsiveContainer></div></div>
          <div className="card"><h2 className="mb-2 text-sm font-medium">Suspicious clusters over time (time-sliced detection)</h2>
            <div className="h-56"><ResponsiveContainer><LineChart data={ct}><CartesianGrid stroke="#1e293b" /><XAxis dataKey="day" stroke="#94a3b8" /><YAxis allowDecimals={false} stroke="#94a3b8" /><Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155' }} /><Legend />
              <Line type="stepAfter" dataKey="clusters" stroke="#f97316" dot={false} isAnimationActive={false} /><Line type="stepAfter" dataKey="flagged_accounts" stroke="#a78bfa" dot={false} isAnimationActive={false} /></LineChart></ResponsiveContainer></div></div>
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="card"><h2 className="mb-2 text-sm font-medium">Risk distribution (model predictions)</h2>
            <div className="h-56"><ResponsiveContainer><BarChart data={dist}><CartesianGrid stroke="#1e293b" /><XAxis dataKey="category" stroke="#94a3b8" /><YAxis stroke="#94a3b8" /><Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155' }} />
              <Bar dataKey="count">{dist.map(d => <Cell key={d.category} fill={catColor[d.category]} />)}</Bar></BarChart></ResponsiveContainer></div></div>
          <div className="card"><h2 className="mb-2 text-sm font-medium">Recent top alerts (unreviewed model predictions)</h2>
            <Status loading={alerts.loading} error={alerts.error} />
            <table className="w-full"><thead><tr><th>Alert</th><th>Account</th><th>Risk</th><th>Cat.</th></tr></thead><tbody>
              {alerts.data?.items.map((a: any) => <tr key={a.alert_id}><td>{a.alert_id}</td><td>{a.account}</td><td>{a.risk.toFixed(3)}</td><td><Badge c={a.category} /></td></tr>)}</tbody></table></div>
        </div></>}
    </div>)
}

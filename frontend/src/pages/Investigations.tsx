import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api, setApiKey, useApi, Badge, Status } from '../api'
const STATES = ['open', 'under_review', 'escalated', 'resolved', 'dismissed']
export default function Investigations() {
  const [flt, setFlt] = useState(''); const [sel, setSel] = useState<any>(null); const [note, setNote] = useState(''); const [msg, setMsg] = useState<string | null>(null); const [key, setKey] = useState('')
  const { data, error, loading, reload } = useApi('/api/v1/alerts?page_size=30' + (flt ? '&status=' + flt : '')), d = useApi(sel ? '/api/v1/transactions/' + sel.tx_id : null)
  async function save(status: string) { if (key) setApiKey(key); try { await api('/api/v1/alerts/' + sel.alert_id, { method: 'PATCH', body: JSON.stringify({ status, note: note || undefined }) }); setMsg('Saved'); setNote(''); setSel({ ...sel, status }); reload() } catch (e: any) { setMsg('Error: ' + e.message) } }
  return (
    <div className="space-y-3"><div className="flex items-center justify-between"><h1 className="text-xl font-semibold">Fraud Investigation</h1><div className="flex gap-2"><a className="btn" href="/api/v1/exports/alerts?format=csv" download>Export alerts CSV</a><a className="btn" href="/api/v1/exports/alerts?format=json" download>JSON</a></div></div>
      <label className="text-sm">API key (analyst or admin)<input className="inp ml-2 w-32" type="password" aria-label="API key" value={key} onChange={e => setKey(e.target.value)} /></label>
      <select className="inp ml-2" aria-label="Case status filter" value={flt} onChange={e => setFlt(e.target.value)}><option value="">All statuses</option>{STATES.map(s => <option key={s}>{s}</option>)}</select>
      <Status loading={loading} error={error} />
      <div className="grid gap-4 lg:grid-cols-2"><div className="card max-h-[32rem] overflow-auto"><table className="w-full"><thead><tr><th>Alert</th><th>Risk</th><th>Cat.</th><th>Case</th></tr></thead><tbody>
        {data?.items.map((a: any) => <tr key={a.alert_id} className="cursor-pointer hover:bg-slate-800" onClick={() => { setSel(a); setMsg(null) }}><td>{a.alert_id}</td><td>{a.risk.toFixed(3)}</td><td><Badge c={a.category} /></td><td>{a.status}</td></tr>)}</tbody></table></div>
        <div className="card space-y-2 text-sm">{!sel ? <span className="text-slate-400">Select an alert.</span> : <>
          <div className="font-semibold">{sel.alert_id} · {sel.account} · case: {sel.status}</div>
          <Status loading={d.loading} error={d.error} />{d.data && <p>{d.data.explanation.summary}</p>}
          <Link className="text-cyan-400 underline" to={'/graph?entity=' + sel.account}>Open graph neighborhood →</Link>
          <textarea className="inp w-full" rows={3} maxLength={2000} placeholder="Analyst note" aria-label="Analyst note" value={note} onChange={e => setNote(e.target.value)} />
          <div className="flex flex-wrap gap-2">{STATES.map(s => <button key={s} className="btn" onClick={() => save(s)}>{s.replace('_', ' ')}</button>)}</div>
          {msg && <p role="status" className={msg.startsWith('Error') ? 'text-red-400' : 'text-emerald-400'}>{msg}</p>}</>}</div></div>
    </div>)
}

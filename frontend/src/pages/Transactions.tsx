import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api, useApi, Badge, Status } from '../api'
function WhatIf() {
  const st = useApi('/api/v1/system/status'); const t0 = st.data?.latest_event_t
  const [f, setF] = useState({ account: '', amount: '', device: '', email: '' }); const [res, setRes] = useState<any>(null); const [err, setErr] = useState<string | null>(null)
  async function run() {
    setErr(null); setRes(null)
    const identifiers = [f.device && { type: 'device', value: f.device }, f.email && { type: 'email', value: f.email }].filter(Boolean)
    try { setRes(await api('/api/v1/transactions/score', { method: 'POST', body: JSON.stringify({ account: f.account, amount: Number(f.amount), t: t0 + 60, identifiers }) })) } catch (e: any) { setErr(e.message) }
  }
  return (<div className="card space-y-2 text-sm"><h2 className="font-medium">What-if scoring (dry run)</h2>
    <p className="text-xs text-slate-400">Scores a hypothetical transaction one minute after the latest event. Nothing is stored or changes the model state.</p>
    {t0 === undefined ? <p className="text-slate-400">Load a dataset to enable.</p> : <>
      <div className="flex flex-wrap gap-2">
        <input className="inp" aria-label="Account" placeholder="Account ID" value={f.account} onChange={e => setF({ ...f, account: e.target.value })} />
        <input className="inp w-28" type="number" min="0" aria-label="Amount" placeholder="Amount" value={f.amount} onChange={e => setF({ ...f, amount: e.target.value })} />
        <input className="inp" aria-label="Device" placeholder="Device (optional)" value={f.device} onChange={e => setF({ ...f, device: e.target.value })} />
        <input className="inp" aria-label="Email" placeholder="Email id (optional)" value={f.email} onChange={e => setF({ ...f, email: e.target.value })} />
        <button className="btn" disabled={!f.account || f.amount === ''} onClick={run}>Score (dry run)</button></div>
      {err && <p className="text-red-400" role="status">Error: {err}</p>}
      {res && <div className="space-y-1" aria-live="polite"><div>Risk <b>{res.risk}</b> <Badge c={res.category} /> <span className="text-xs text-slate-400">(dry run, uncalibrated score)</span></div><p>{res.explanation.summary}</p>
        {res.explanation.warnings.map((w: string) => <p key={w} className="text-amber-300">{w}</p>)}</div>}</>}</div>)
}

export default function Transactions() {
  const [q, setQ] = useState({ search: '', category: '', min_amount: '0', sort: '-risk', page: 1 }); const [sel, setSel] = useState<string | null>(null)
  const p = new URLSearchParams({ sort: q.sort, min_amount: q.min_amount || '0', page: String(q.page), page_size: '25' })
  if (q.search) p.set('search', q.search); if (q.category) p.set('category', q.category)
  const { data, error, loading } = useApi('/api/v1/transactions?' + p), d = useApi(sel ? '/api/v1/transactions/' + sel : null)
  const set = (k: string, v: any) => setQ({ ...q, [k]: v, page: k === 'page' ? v : 1 })
  return (
    <div className="space-y-3"><h1 className="text-xl font-semibold">Transaction Explorer</h1>
      <div className="flex flex-wrap gap-2">
        <input className="inp" placeholder="Transaction ID" aria-label="Search by transaction ID" value={q.search} onChange={e => set('search', e.target.value)} />
        <select className="inp" aria-label="Risk category" value={q.category} onChange={e => set('category', e.target.value)}><option value="">All categories</option>{['low', 'medium', 'high', 'critical'].map(c => <option key={c}>{c}</option>)}</select>
        <input className="inp w-28" type="number" min="0" aria-label="Minimum amount" value={q.min_amount} onChange={e => set('min_amount', e.target.value)} />
        <select className="inp" aria-label="Sort" value={q.sort} onChange={e => set('sort', e.target.value)}><option value="-risk">Risk ↓</option><option value="-amount">Amount ↓</option><option value="t">Time ↑</option></select></div>
      <WhatIf />
      <Status loading={loading} error={error} />
      {data && <div className="grid gap-4 lg:grid-cols-3"><div className="card overflow-x-auto lg:col-span-2">
        <table className="w-full"><thead><tr><th>ID</th><th>Account</th><th>Amount</th><th>Risk</th><th>Cat.</th></tr></thead><tbody>
          {data.items.length === 0 && <tr><td colSpan={5} className="text-slate-400">No transactions match.</td></tr>}
          {data.items.map((t: any) => <tr key={t.tx_id} className="cursor-pointer hover:bg-slate-800" onClick={() => setSel(t.tx_id)}><td>{t.tx_id}</td><td>{t.account}</td><td>{t.amount}</td><td>{t.risk.toFixed(3)}</td><td><Badge c={t.category} /></td></tr>)}</tbody></table>
        <div className="mt-2 flex items-center gap-2 text-sm"><button className="btn" disabled={q.page <= 1} onClick={() => set('page', q.page - 1)}>Prev</button><span>Page {q.page} · {data.total} results</span><button className="btn" disabled={q.page * 25 >= data.total} onClick={() => set('page', q.page + 1)}>Next</button></div></div>
        <div className="card text-sm" aria-live="polite">{!sel ? <span className="text-slate-400">Select a transaction.</span> : <><Status loading={d.loading} error={d.error} />
          {d.data && <div className="space-y-2"><div className="font-semibold">{d.data.tx_id} <Badge c={d.data.category} /></div><p>{d.data.explanation.summary}</p>
            {d.data.explanation.warnings.map((w: string) => <p key={w} className="text-amber-300">{w}</p>)}
            <ul className="text-slate-300">{d.data.explanation.ranked_signals.map((s: any) => <li key={s.signal}>{s.signal}: {s.contribution}</li>)}</ul>
            <Link className="text-cyan-400 underline" to={'/graph?entity=' + d.data.account}>Investigate in graph →</Link></div>}</>}</div></div>}
    </div>)
}

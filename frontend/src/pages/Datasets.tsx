import { useEffect, useState } from 'react'
import { api, setApiKey, useApi, Status } from '../api'
const LABELS: Record<string, string> = { rows_read: 'Rows read', rows_kept: 'Rows kept', duplicate_ids_dropped: 'Duplicate IDs dropped', invalid_rows_dropped: 'Invalid rows dropped',
  with_identity: 'With identity record', unmatched_kept: 'Unmatched (kept)', missing_device_pct: 'Missing device %', accounts: 'Account proxies', fraud_rows: 'Fraud labels (dataset ground truth)', fraud_rate: 'Fraud rate' }
function Quality({ q }: { q: any }) {
  return (<div className="grid grid-cols-2 gap-2 text-sm md:grid-cols-3">
    {Object.keys(LABELS).filter(k => q[k] !== undefined).map(k => <div key={k} className="rounded border border-slate-700 p-2"><div className="text-xs text-slate-400">{LABELS[k]}</div><div className="font-semibold">{q[k]}</div></div>)}
    {!q.has_labels && <p className="col-span-full text-amber-300">No isFraud column: scoring uses unfitted default weights and no class-imbalance summary is available.</p>}</div>)
}
export default function Datasets({ onDone }: { onDone: () => void }) {
  const [key, setKey] = useState(''); const [tx, setTx] = useState<File | null>(null); const [idf, setIdf] = useState<File | null>(null)
  const [job, setJob] = useState<any>(null); const [err, setErr] = useState<string | null>(null); const [busy, setBusy] = useState(false)
  const jobs = useApi('/api/v1/pipelines/jobs'); const dsets = useApi('/api/v1/datasets')
  async function submit() {
    if (!tx) return; setErr(null); setBusy(true); setApiKey(key)
    const f = new FormData(); f.append('transactions', tx); if (idf) f.append('identity', idf)
    try { setJob(await api('/api/v1/datasets/upload', { method: 'POST', body: f })) } catch (e: any) { setErr(e.message); setBusy(false) }
  }
  useEffect(() => {
    if (!job || job.status === 'done' || job.status === 'failed') { if (job) { setBusy(false); jobs.reload(); dsets.reload(); if (job.status === 'done') onDone() } return }
    const t = setTimeout(async () => { try { setJob(await api('/api/v1/pipelines/jobs/' + job.job_id)) } catch (e: any) { setErr(e.message); setBusy(false) } }, 2000)
    return () => clearTimeout(t)
  }, [job])
  return (
    <div className="space-y-4"><h1 className="text-xl font-semibold">Dataset &amp; Pipeline</h1>
      <div className="card max-w-xl space-y-3 text-sm">
        <p className="text-slate-400">Upload IEEE-CIS style CSVs (see docs/dataset.md). Needs TransactionID, TransactionDT, TransactionAmt, card1. isFraud is used only to fit weights on the earliest 60% of time.</p>
        <label className="block">Transactions CSV (required)<input className="inp mt-1 block w-full" type="file" accept=".csv" aria-label="Transactions CSV" onChange={e => setTx(e.target.files?.[0] ?? null)} /></label>
        <label className="block">Identity CSV (optional)<input className="inp mt-1 block w-full" type="file" accept=".csv" aria-label="Identity CSV" onChange={e => setIdf(e.target.files?.[0] ?? null)} /></label>
        <label className="block">API key<input className="inp mt-1 block w-full" type="password" value={key} onChange={e => setKey(e.target.value)} /></label>
        <button className="btn" disabled={!tx || busy} onClick={submit}>{busy ? 'Processing…' : 'Upload and process'}</button>
        <Status loading={false} error={err} /></div>
      {job && <div className="card space-y-2 text-sm" aria-live="polite"><div>Job <b>{job.job_id}</b>: <b className={job.status === 'failed' ? 'text-red-400' : job.status === 'done' ? 'text-emerald-400' : 'text-cyan-300'}>{job.status}</b>{job.stage && job.status !== 'done' ? ` (${job.stage})` : ''}</div>
        {job.error && <p className="text-red-400" role="alert">{job.error}</p>}{job.quality && <Quality q={job.quality} />}</div>}
      {dsets.data?.items.length > 0 && <div className="card text-sm"><h2 className="mb-2 font-medium">Datasets</h2>
        <p className="mb-1 text-xs text-slate-400">Metadata persists; the data itself is held in memory and must be reloaded after a server restart.</p>
        <table className="w-full"><thead><tr><th>ID</th><th>Source</th><th>Rows</th><th>Weights</th><th></th></tr></thead><tbody>
          {dsets.data.items.map((d: any) => <tr key={d.id}><td>{d.id}</td><td>{d.source}</td><td>{d.rows}</td><td>{d.weights}</td><td>{d.active && <span className="text-emerald-400">active</span>}</td></tr>)}</tbody></table></div>}
      <div className="card text-sm"><h2 className="mb-2 font-medium">Job history (this server session)</h2><Status loading={jobs.loading} error={jobs.error} />
        {jobs.data?.items.length === 0 && <span className="text-slate-400">No jobs yet.</span>}
        <table className="w-full"><tbody>{jobs.data?.items.map((j: any) => <tr key={j.job_id}><td>{j.job_id}</td><td>{j.status}</td><td>{j.quality ? `${j.quality.rows_kept} rows` : j.error ?? ''}</td></tr>)}</tbody></table></div>
    </div>)
}

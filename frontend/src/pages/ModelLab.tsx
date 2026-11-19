import { useEffect, useState } from 'react'
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api, setApiKey, useApi, Status } from '../api'
const f = (x: any) => (x === null || x === undefined ? 'Not evaluated' : Number(x).toFixed(3))
const COLORS = ['#38bdf8', '#a78bfa', '#34d399', '#fbbf24', '#f472b6', '#94a3b8', '#fb923c', '#2dd4bf', '#ef4444']
const pts = (a: number[], b: number[], x: string, y: string) => a.map((v, i) => ({ [x]: v, [y]: b[i] }))
function Curve({ title, models, kind }: { title: string; models: [string, any][]; kind: 'roc' | 'pr' }) {
  const [xk, yk] = kind === 'roc' ? ['fpr', 'tpr'] : ['recall', 'precision']
  return (<div className="card"><h2 className="mb-2 text-sm font-medium">{title}</h2><div className="h-64"><ResponsiveContainer><LineChart>
    <CartesianGrid stroke="#1e293b" /><XAxis type="number" dataKey={xk} domain={[0, 1]} stroke="#94a3b8" name={xk} /><YAxis type="number" domain={[0, 1]} stroke="#94a3b8" />
    <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155' }} /><Legend />
    {models.map(([k, v], i) => <Line key={k} name={k} data={pts(v.curves[kind][xk], v.curves[kind][yk], xk, yk)} dataKey={yk} dot={false} isAnimationActive={false}
      stroke={COLORS[i % COLORS.length]} strokeWidth={k.startsWith('FULL') ? 3 : 1.5} />)}</LineChart></ResponsiveContainer></div></div>)
}
export default function ModelLab() {
  const [runId, setRunId] = useState(''); const [sel, setSel] = useState('')
  const [scenario, setScenario] = useState('base'); const [seed, setSeed] = useState('42'); const [key, setKey] = useState(''); const [msg, setMsg] = useState<string | null>(null)
  const lat = useApi('/api/v1/system/latency'); const runs = useApi('/api/v1/experiments'); const m = useApi(runId ? `/api/v1/experiments/${runId}/metrics` : '/api/v1/experiments/latest/metrics')
  const { data, error, loading } = m; const items: any[] = runs.data?.items ?? []
  const active = items.some(r => r.status === 'queued' || r.status === 'running'); const doneCount = items.filter(r => r.status === 'done').length
  useEffect(() => { if (!active) return; const t = setInterval(runs.reload, 3000); return () => clearInterval(t) }, [active])
  useEffect(() => { if (doneCount) m.reload() }, [doneCount])
  async function launch() {
    setApiKey(key); setMsg(null)
    try { const r = await api('/api/v1/experiments', { method: 'POST', body: JSON.stringify({ scenario, seed: Number(seed) }) }); setMsg(`Started ${r.id}`); runs.reload() }
    catch (e: any) { setMsg('Error: ' + e.message) }
  }
  const entries: [string, any][] = data ? Object.entries(data.models) : []
  const withCurves = entries.filter(([, v]) => v.curves?.roc && v.curves?.pr); const cm = data?.models[sel || entries[entries.length - 1]?.[0]]?.test
  return (
    <div className="space-y-3"><div className="flex items-center justify-between"><h1 className="text-xl font-semibold">Model Lab</h1>
      <div className="flex gap-2"><a className="btn" href="/api/v1/exports/evaluation?format=csv" download>Export CSV</a><a className="btn" href="/api/v1/exports/evaluation?format=json" download>Export JSON</a></div></div>
      <div className="card space-y-2 text-sm"><h2 className="font-medium">Run an experiment (synthetic data)</h2>
        <div className="flex flex-wrap items-end gap-2">
          <label>Scenario<select className="inp ml-1" aria-label="Scenario" value={scenario} onChange={e => setScenario(e.target.value)}>{['base', 'decay', 'decay_hard'].map(x => <option key={x}>{x}</option>)}</select></label>
          <label>Seed<input className="inp ml-1 w-24" type="number" min="0" aria-label="Seed" value={seed} onChange={e => setSeed(e.target.value)} /></label>
          <label>Key<input className="inp ml-1 w-28" type="password" aria-label="API key" value={key} onChange={e => setKey(e.target.value)} /></label>
          <button className="btn" onClick={launch} disabled={active}>Run experiment</button></div>
        {msg && <p role="status" className={msg.startsWith('Error') ? 'text-red-400' : 'text-emerald-400'}>{msg}</p>}
        <Status loading={false} error={runs.error} />
        {items.length > 0 && <table className="w-full"><thead><tr><th>Run</th><th>Scenario</th><th>Seed</th><th>Status</th><th></th></tr></thead><tbody>
          {items.map(r => <tr key={r.id}><td>{r.id}</td><td>{r.scenario}</td><td>{r.seed}</td><td className={r.status === 'failed' ? 'text-red-400' : ''}>{r.status === 'running' ? `running: ${r.stage}` : r.status}{r.error ? ` (${r.error})` : ''}</td>
            <td>{r.status === 'done' && <button className="text-cyan-400 underline" onClick={() => setRunId(r.id)}>View</button>}</td></tr>)}</tbody></table>}
        {runId && <button className="text-cyan-400 underline" onClick={() => setRunId('')}>Show latest run</button>}</div>
      <div className="card text-sm" data-testid="latency"><h2 className="mb-1 font-medium">Scoring latency (per event, in-process)</h2>
        {lat.data ? <><table className="w-full"><thead><tr><th>Mode</th><th>p50 ms</th><th>p95 ms</th><th>p99 ms</th><th>max ms</th></tr></thead><tbody>
          {Object.entries(lat.data.modes).map(([k, v]: any) => <tr key={k}><td>{k}</td><td>{v.p50_ms}</td><td>{v.p95_ms}</td><td>{v.p99_ms}</td><td>{v.max_ms}</td></tr>)}</tbody></table>
          <p className="mt-1 text-xs text-slate-400">{lat.data.dataset} · {lat.data.warm_events} warm events, {lat.data.timed_events} timed · {lat.data.hardware.cpu} ({lat.data.hardware.logical_cpus} logical CPUs), Python {lat.data.hardware.python}. Excludes: {lat.data.excludes}.</p></>
          : <span className="text-slate-400">Not evaluated{lat.loading ? '…' : ' (run python3 -m app.ml.latency)'}.</span>}</div>
      <Status loading={loading} error={error} />
      {data && <><div className="card text-sm"><b>{data.dataset}</b> · seed {data.seed} · split {JSON.stringify(data.split)} · threshold: {data.threshold_selection}
          {data.decay_tuning && <> · decay tau: {data.decay_tuning.selected_tau_days} d (by {data.decay_tuning.criterion})</>}</div>
        <div className="card overflow-x-auto"><table className="w-full"><thead><tr><th>Model</th><th>Precision</th><th>Recall</th><th>F1</th><th>FPR</th><th>ROC-AUC</th><th>PR-AUC</th></tr></thead><tbody>
          {entries.map(([k, v]: any) => <tr key={k}><td>{k}</td>{['precision', 'recall', 'f1', 'fpr', 'roc_auc', 'pr_auc'].map(m => <td key={m}>{f(v.test[m])}</td>)}</tr>)}</tbody></table>
          <p className="mt-2 text-xs text-slate-400">Test-period metrics from a single synthetic run; small test set. Not a benchmark result.</p></div>
        {withCurves.length === 0 ? <div className="card text-sm text-slate-400">Curves not available for this run (re-run the experiment to generate them).</div> :
          <div className="grid gap-3 lg:grid-cols-2"><Curve title="ROC curves (test period)" models={withCurves} kind="roc" /><Curve title="Precision-recall curves (test period)" models={withCurves} kind="pr" /></div>}
        <div className="card text-sm"><div className="mb-2 flex items-center gap-2"><h2 className="font-medium">Confusion matrix (test period)</h2>
          <select className="inp" aria-label="Model" value={sel || entries[entries.length - 1]?.[0]} onChange={e => setSel(e.target.value)}>{entries.map(([k]) => <option key={k}>{k}</option>)}</select></div>
          {cm && <table className="w-64"><thead><tr><th></th><th>Pred. fraud</th><th>Pred. normal</th></tr></thead><tbody>
            <tr><td>Actual fraud</td><td>TP: {cm.tp}</td><td>FN: {cm.fn}</td></tr><tr><td>Actual normal</td><td>FP: {cm.fp}</td><td>TN: {cm.tn}</td></tr></tbody></table>}
          <p className="mt-1 text-xs text-slate-400">Threshold {f(cm?.threshold)} chosen on validation data only.</p></div></>}
    </div>)
}

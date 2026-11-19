import { useEffect, useState } from 'react'
import { api, setApiKey, useApi, Status } from '../api'
export default function Config() {
  const { data, error, loading, reload } = useApi('/api/v1/config'); const [form, setForm] = useState<any>({}); const [key, setKey] = useState(''); const [msg, setMsg] = useState<string | null>(null)
  useEffect(() => { if (data) setForm(data) }, [data])
  async function save() { setApiKey(key); try { await api('/api/v1/config', { method: 'PATCH', body: JSON.stringify(Object.fromEntries(Object.entries(form).map(([k, v]) => [k, Number(v)]))) }); setMsg('Saved'); reload() } catch (e: any) { setMsg('Error: ' + e.message) } }
  return (
    <div className="space-y-3"><h1 className="text-xl font-semibold">Configuration</h1><Status loading={loading} error={error} />
      <div className="card max-w-md space-y-2 text-sm">
        {Object.keys(form).map(k => <label key={k} className="flex items-center justify-between gap-2">{k}<input className="inp w-28" type="number" step="0.05" value={form[k]} onChange={e => setForm({ ...form, [k]: e.target.value })} /></label>)}
        <label className="flex items-center justify-between gap-2">API key (required to save)<input className="inp w-28" type="password" value={key} onChange={e => setKey(e.target.value)} /></label>
        <button className="btn" onClick={save}>Save changes</button>{msg && <p role="status" className={msg.startsWith('Error') ? 'text-red-400' : 'text-emerald-400'}>{msg}</p>}</div>
    </div>)
}

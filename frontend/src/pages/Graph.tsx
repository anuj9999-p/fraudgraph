import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import cytoscape from 'cytoscape'
import { api, useApi, Status } from '../api'
const color = (n: any) => n.type === 'device' ? '#38bdf8' : n.type === 'email' ? '#a78bfa' : (n.risk ?? 0) >= 0.9 ? '#ef4444' : (n.risk ?? 0) >= 0.6 ? '#f97316' : '#64748b'
export default function Graph() {
  const [sp, setSp] = useSearchParams(); const entity = sp.get('entity') || ''; const [input, setInput] = useState(entity)
  const el = useRef<HTMLDivElement>(null); const cy = useRef<cytoscape.Core | null>(null)
  const [sel, setSel] = useState<any>(null); const [err, setErr] = useState<string | null>(null); const clusters = useApi('/api/v1/graph/clusters')
  async function expand(id: string) {
    try { setErr(null); const g = await api(`/api/v1/graph/entities/${encodeURIComponent(id)}/neighbors?limit=30`); const c = cy.current!
      c.add([...g.nodes.filter((n: any) => c.getElementById(n.id).empty()).map((n: any) => ({ data: { ...n, color: color(n), label: n.id } })),
        ...g.edges.filter((e: any) => c.getElementById(`${e.source}>${e.target}`).empty()).map((e: any) => ({ data: { id: `${e.source}>${e.target}`, ...e } }))])
      c.layout({ name: 'cose', animate: false }).run(); c.fit(undefined, 30) } catch (e: any) { setErr(e.message) }
  }
  useEffect(() => {
    if (!el.current) return
    cy.current = cytoscape({ container: el.current, style: [
      { selector: 'node', style: { 'background-color': 'data(color)', label: 'data(label)', color: '#cbd5e1', 'font-size': 9, width: 18, height: 18 } },
      { selector: 'node[type="device"]', style: { shape: 'diamond' } }, { selector: 'node[type="email"]', style: { shape: 'round-rectangle' } },
      { selector: 'edge', style: { width: 1.5, 'line-color': '#475569' } }, { selector: ':selected', style: { 'border-width': 3, 'border-color': '#22d3ee' } }] })
    cy.current.on('tap', 'node', ev => { setSel(ev.target.data()); expand(ev.target.id()) })
    return () => cy.current?.destroy()
  }, [])
  useEffect(() => { if (entity && cy.current) { cy.current.elements().remove(); expand(entity) } }, [entity])
  return (
    <div className="space-y-3"><h1 className="text-xl font-semibold">Graph Intelligence</h1>
      <form className="flex gap-2" onSubmit={e => { e.preventDefault(); setSp({ entity: input }) }}><input className="inp" aria-label="Entity ID" placeholder="e.g. ring0_0" value={input} onChange={e => setInput(e.target.value)} /><button className="btn">Load neighborhood</button>
        <button type="button" className="btn" onClick={() => cy.current?.fit(undefined, 30)}>Fit</button></form>
      <Status loading={false} error={err} />
      <div className="grid gap-3 lg:grid-cols-4"><div ref={el} className="card h-[28rem] lg:col-span-3" role="img" aria-label="Entity graph" />
        <div className="card space-y-2 text-sm"><div className="text-xs text-slate-400">Legend: ● account (grey/orange/red by risk) · ◆ device · ▢ email</div>
          {sel ? <div><div className="font-semibold">{sel.id}</div><div>type: {sel.type}</div>{sel.risk !== undefined && <div>risk: {sel.risk}</div>}<div className="text-slate-400">Click a node to expand its neighbors.</div></div> : <div className="text-slate-400">Select a node.</div>}
          <h2 className="pt-2 font-medium">Suspicious clusters</h2><Status loading={clusters.loading} error={clusters.error} />
          {clusters.data?.items.map((c: any) => <button key={c.cluster_id} className="block w-full rounded border border-slate-700 p-2 text-left hover:bg-slate-800" onClick={() => { setInput(c.members[0]); setSp({ entity: c.members[0] }) }}>
            {c.cluster_id} · {c.size} accounts · risk {c.mean_risk}{c.detected_at != null && ` · first detected day ${Math.round((c.detected_at / 86400) * 10) / 10}`}</button>)}</div></div>
    </div>)
}

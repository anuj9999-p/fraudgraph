import { NavLink, Route, Routes } from 'react-router-dom'
import { Activity, Database, Network, Search, ShieldAlert, FlaskConical, Settings } from 'lucide-react'
import { useApi } from './api'
import Overview from './pages/Overview'
import Transactions from './pages/Transactions'
import Graph from './pages/Graph'
import Investigations from './pages/Investigations'
import ModelLab from './pages/ModelLab'
import Config from './pages/Config'
import Datasets from './pages/Datasets'
const nav = [['/', 'Overview', Activity], ['/transactions', 'Transactions', Search], ['/graph', 'Graph', Network],
  ['/investigations', 'Investigations', ShieldAlert], ['/model-lab', 'Model Lab', FlaskConical], ['/datasets', 'Datasets', Database], ['/config', 'Config', Settings]] as const
export default function App() {
  const { data: st, reload } = useApi('/api/v1/system/status')
  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <nav className="flex gap-1 border-b border-slate-800 bg-slate-950 p-2 md:w-52 md:flex-col md:border-b-0 md:border-r" aria-label="Main">
        <div className="hidden px-2 py-3 text-lg font-semibold text-cyan-400 md:block">FraudGraph AI</div>
        {nav.map(([to, label, Icon]) => (
          <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) =>
            `flex items-center gap-2 rounded-md px-3 py-2 text-sm ${isActive ? 'bg-cyan-600/20 text-cyan-300' : 'text-slate-300 hover:bg-slate-800'}`}>
            <Icon size={16} />{label}</NavLink>))}
      </nav>
      <main className="flex-1 p-4 md:p-6">
        {st?.data_source?.includes('SYNTHETIC') && <div className="mb-4 rounded-md border border-amber-500/40 bg-amber-500/10 px-3 py-1.5 text-sm text-amber-300" role="note">
          Synthetic Demo Data: results here are not IEEE-CIS benchmark results. Risk scores are not confirmed fraud.</div>}
        <Routes>
          <Route path="/" element={<Overview status={st} reload={reload} />} />
          <Route path="/transactions" element={<Transactions />} />
          <Route path="/graph" element={<Graph />} />
          <Route path="/investigations" element={<Investigations />} />
          <Route path="/model-lab" element={<ModelLab />} />
          <Route path="/datasets" element={<Datasets onDone={reload} />} />
          <Route path="/config" element={<Config />} />
        </Routes>
      </main>
    </div>)
}

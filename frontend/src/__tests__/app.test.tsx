import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent, cleanup } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { mockFetch } from './helpers'
import { api } from '../api'
import Overview from '../pages/Overview'
import Transactions from '../pages/Transactions'
import Investigations from '../pages/Investigations'
import Config from '../pages/Config'
import Datasets from '../pages/Datasets'
import Graph from '../pages/Graph'
import ModelLab from '../pages/ModelLab'

const cyMock = vi.hoisted(() => ({ on: vi.fn(), add: vi.fn(), getElementById: vi.fn(() => ({ empty: () => true })),
  layout: vi.fn(() => ({ run: vi.fn() })), fit: vi.fn(), destroy: vi.fn(), elements: vi.fn(() => ({ remove: vi.fn() })) }))
vi.mock('cytoscape', () => ({ default: vi.fn(() => cyMock) }))
const wrap = (ui: JSX.Element, path = '/') => render(<MemoryRouter initialEntries={[path]}>{ui}</MemoryRouter>)
const explanation = { summary: 'Elevated risk: test evidence', warnings: ['Cold start: little history'], ranked_signals: [{ signal: 'behavioral deviation', contribution: 1.2 }] }
beforeEach(() => { cleanup(); vi.clearAllMocks() })

describe('api client', () => {
  it('surfaces backend detail and falls back to HTTP status', async () => {
    mockFetch([['GET /a', 409, { detail: 'No dataset loaded' }], ['GET /b', 500, null]])
    await expect(api('/a')).rejects.toThrow('No dataset loaded'); await expect(api('/b')).rejects.toThrow('HTTP 500')
  })
})
describe('Overview', () => {
  it('shows an empty state when no dataset is loaded', () => {
    mockFetch([]); wrap(<Overview status={{ dataset_loaded: false }} reload={() => {}} />)
    expect(screen.getByText(/No dataset loaded/)).toBeInTheDocument()
  })
  it('renders backend-derived counts and alerts', async () => {
    mockFetch([['GET /api/v1/alerts', 200, { total: 2, items: [{ alert_id: 'A-T1', account: 'acct_1', risk: 0.9, category: 'high' }] }], ['GET /api/v1/transactions', 200, { total: 5, items: [] }]])
    wrap(<Overview status={{ dataset_loaded: true, transactions: 123, clusters: 3, model: 'atfrp-v1' }} reload={() => {}} />)
    expect(await screen.findByText('A-T1')).toBeInTheDocument(); expect(screen.getByText('123')).toBeInTheDocument()
  })
  it('renders time trends and cluster timeline from the backend', async () => {
    mockFetch([['GET /api/v1/stats/trends', 200, { buckets: [{ t_start: 0, t_end: 86400, transactions: 5, alerts: 1 }], cluster_timeline: [{ t: 86400, clusters: 1, flagged_accounts: 4 }] }],
      ['GET /api/v1/alerts', 200, { total: 0, items: [] }], ['GET /api/v1/transactions', 200, { total: 0, items: [] }]])
    wrap(<Overview status={{ dataset_loaded: true, transactions: 5, clusters: 1, model: 'atfrp-v1' }} reload={() => {}} />)
    expect(await screen.findByText(/Transactions and alerts over time/)).toBeInTheDocument(); expect(screen.getByText(/time-sliced detection/)).toBeInTheDocument()
  })
  it('shows an error when loading the demo fails', async () => {
    mockFetch([['POST /api/v1/demo/load', 500, { detail: 'boom' }]]); wrap(<Overview status={{ dataset_loaded: false }} reload={() => {}} />)
    fireEvent.click(screen.getByRole('button', { name: /Load synthetic demo/ })); expect(await screen.findByRole('alert')).toHaveTextContent('boom')
  })
})
describe('Transactions', () => {
  const routes: any[] = [['GET /api/v1/transactions/T1', 200, { tx_id: 'T1', account: 'acct_1', category: 'high', explanation }],
    ['GET /api/v1/transactions', 200, { total: 1, items: [{ tx_id: 'T1', account: 'acct_1', amount: 50, risk: 0.9, category: 'high' }] }]]
  it('searches by ID and shows evidence-based detail', async () => {
    const calls = mockFetch(routes); wrap(<Transactions />)
    fireEvent.change(screen.getByLabelText('Search by transaction ID'), { target: { value: 'T9' } })
    await waitFor(() => expect(calls.some(c => c.key.includes('search=T9'))).toBe(true))
    fireEvent.click(await screen.findByText('T1')); expect(await screen.findByText(/Elevated risk: test evidence/)).toBeInTheDocument()
    expect(screen.getByText(/Cold start/)).toBeInTheDocument()
  })
  it('shows an error state and never renders a fraud label', async () => {
    mockFetch([['GET /api/v1/transactions', 409, { detail: 'No dataset loaded. POST /api/v1/demo/load first.' }]]); wrap(<Transactions />)
    expect(await screen.findByRole('alert')).toHaveTextContent('No dataset loaded'); expect(document.body.textContent).not.toMatch(/isFraud/)
  })
})
describe('What-if scoring', () => {
  const status = ['GET /api/v1/system/status', 200, { latest_event_t: 1000 }]
  const list = ['GET /api/v1/transactions', 200, { total: 0, items: [] }]
  it('sends a dry-run score request after the latest event and shows evidence', async () => {
    const calls = mockFetch([status, ['POST /api/v1/transactions/score', 200, { dry_run: true, risk: 0.83, category: 'high', explanation: { ...explanation } }], list] as any)
    wrap(<Transactions />); fireEvent.change(await screen.findByLabelText('Account'), { target: { value: 'ring0_0' } })
    fireEvent.change(screen.getByLabelText('Amount'), { target: { value: '900' } }); fireEvent.change(screen.getByLabelText('Device'), { target: { value: 'ring_dev_0' } })
    fireEvent.click(screen.getByRole('button', { name: 'Score (dry run)' })); expect(await screen.findByText(/Elevated risk: test evidence/)).toBeInTheDocument()
    const body = JSON.parse(String(calls.find(c => c.key.startsWith('POST'))!.init!.body))
    expect(body).toEqual({ account: 'ring0_0', amount: 900, t: 1060, identifiers: [{ type: 'device', value: 'ring_dev_0' }] })
  })
  it('shows backend validation errors and a hint when no dataset is loaded', async () => {
    mockFetch([status, ['POST /api/v1/transactions/score', 422, { detail: 'event time precedes already-processed history' }], list] as any)
    wrap(<Transactions />); fireEvent.change(await screen.findByLabelText('Account'), { target: { value: 'a' } }); fireEvent.change(screen.getByLabelText('Amount'), { target: { value: '1' } })
    fireEvent.click(screen.getByRole('button', { name: 'Score (dry run)' })); expect(await screen.findByText(/event time precedes/)).toBeInTheDocument(); cleanup()
    mockFetch([['GET /api/v1/system/status', 200, {}], list] as any); wrap(<Transactions />); expect(await screen.findByText('Load a dataset to enable.')).toBeInTheDocument()
  })
})
describe('Investigations', () => {
  const alerts = ['GET /api/v1/alerts', 200, { total: 1, items: [{ alert_id: 'A-T1', tx_id: 'T1', account: 'acct_1', risk: 0.9, category: 'high', status: 'open' }] }]
  const tx = ['GET /api/v1/transactions/T1', 200, { explanation }]
  it('persists a status change with a note', async () => {
    const calls = mockFetch([['PATCH /api/v1/alerts/A-T1', 200, { status: 'escalated' }], tx, alerts] as any)
    wrap(<Investigations />); fireEvent.click(await screen.findByText('A-T1'))
    fireEvent.change(screen.getByLabelText('Analyst note'), { target: { value: 'checked ring' } })
    fireEvent.click(screen.getByRole('button', { name: 'escalated' })); expect(await screen.findByText('Saved')).toBeInTheDocument()
    const body = JSON.parse(String(calls.find(c => c.key.startsWith('PATCH'))!.init!.body)); expect(body).toEqual({ status: 'escalated', note: 'checked ring' })
  })
  it('shows the API error when unauthorized', async () => {
    mockFetch([['PATCH /api/v1/alerts/A-T1', 401, { detail: 'invalid API key' }], tx, alerts] as any)
    wrap(<Investigations />); fireEvent.click(await screen.findByText('A-T1')); fireEvent.click(screen.getByRole('button', { name: 'resolved' }))
    expect(await screen.findByText('Error: invalid API key')).toBeInTheDocument()
  })
})
describe('Investigations roles and limits', () => {
  const alerts = ['GET /api/v1/alerts', 200, { total: 1, items: [{ alert_id: 'A-T1', tx_id: 'T1', account: 'acct_1', risk: 0.9, category: 'high', status: 'open' }] }]
  const tx = ['GET /api/v1/transactions/T1', 200, { explanation }]
  it('sends the entered analyst key and shows 403/429 messages from the backend', async () => {
    const calls = mockFetch([['PATCH /api/v1/alerts/A-T1', 429, { detail: 'rate limit exceeded; retry later' }], tx, alerts] as any)
    wrap(<Investigations />); fireEvent.change(screen.getByLabelText('API key'), { target: { value: 'ana' } })
    fireEvent.click(await screen.findByText('A-T1')); fireEvent.click(screen.getByRole('button', { name: 'resolved' }))
    expect(await screen.findByText('Error: rate limit exceeded; retry later')).toBeInTheDocument()
    expect((calls.find(c => c.key.startsWith('PATCH'))!.init!.headers as Record<string, string>)['X-API-Key']).toBe('ana')
  })
})
describe('Config', () => {
  it('displays backend validation errors for bad thresholds', async () => {
    mockFetch([['PATCH /api/v1/config', 422, { detail: 'need 0<=medium<=high<=critical<=1' }], ['GET /api/v1/config', 200, { medium: 0.3, high: 0.6, critical: 0.9 }]])
    wrap(<Config />); await screen.findByDisplayValue('0.6'); fireEvent.click(screen.getByRole('button', { name: 'Save changes' }))
    expect(await screen.findByText(/Error: need 0<=medium/)).toBeInTheDocument()
  })
})
describe('Graph', () => {
  const nodes = { nodes: [{ id: 'ring0_0', type: 'account', risk: 0.95 }, { id: 'device:d1', type: 'device' }], edges: [{ source: 'ring0_0', target: 'device:d1', last_seen: 1 }], cluster: 'C-1' }
  it('loads a cluster member neighborhood into the graph', async () => {
    const calls = mockFetch([['GET /api/v1/graph/clusters', 200, { items: [{ cluster_id: 'C-1', size: 6, mean_risk: 0.9, members: ['ring0_0'], detected_at: 518400 }] }], ['GET /api/v1/graph/entities/ring0_0/neighbors', 200, nodes]])
    wrap(<Graph />, '/graph'); fireEvent.click(await screen.findByText(/C-1 · 6 accounts.*first detected day 6/))
    await waitFor(() => expect(cyMock.add).toHaveBeenCalled()); expect(cyMock.add.mock.calls[0][0]).toHaveLength(3)
    expect(calls.some(c => c.key.includes('/neighbors'))).toBe(true)
  })
  it('shows an error for an unknown entity', async () => {
    mockFetch([['GET /api/v1/graph/clusters', 200, { items: [] }], ['GET /api/v1/graph/entities/zzz', 404, { detail: 'entity not found' }]])
    wrap(<Graph />, '/graph'); fireEvent.change(screen.getByLabelText('Entity ID'), { target: { value: 'zzz' } })
    fireEvent.click(screen.getByRole('button', { name: 'Load neighborhood' })); expect(await screen.findByText('entity not found')).toBeInTheDocument()
  })
})
describe('Datasets list', () => {
  it('lists registered datasets and marks the active one', async () => {
    mockFetch([['GET /api/v1/datasets', 200, { items: [{ id: 'demo:42', source: 'SYNTHETIC demo data', rows: 10227, weights: 'fitted', active: true }, { id: 'upload:x', source: 'IEEE-CIS upload', rows: 5, weights: 'UNFITTED', active: false }] }], ['GET /api/v1/pipelines/jobs', 200, { items: [] }]])
    wrap(<Datasets onDone={() => {}} />); expect(await screen.findByText('demo:42')).toBeInTheDocument(); expect(screen.getByText('active')).toBeInTheDocument(); expect(screen.getByText('upload:x')).toBeInTheDocument()
  })
})
describe('Datasets', () => {
  it('requires a file and surfaces upload errors', async () => {
    mockFetch([['POST /api/v1/datasets/upload', 401, { detail: 'invalid API key' }], ['GET /api/v1/pipelines/jobs', 200, { items: [] }]])
    wrap(<Datasets onDone={() => {}} />); const btn = screen.getByRole('button', { name: /Upload and process/ }); expect(btn).toBeDisabled()
    fireEvent.change(screen.getByLabelText('Transactions CSV'), { target: { files: [new File(['a'], 't.csv')] } })
    await waitFor(() => expect(btn).toBeEnabled()); fireEvent.click(btn); expect(await screen.findByRole('alert')).toHaveTextContent('invalid API key')
  })
})

describe('ModelLab', () => {
  const t = (o: any = {}) => ({ precision: 0.9, recall: 0.8, f1: 0.85, fpr: 0.01, roc_auc: 0.99, pr_auc: 0.95, threshold: 0.5, tp: 8, fp: 1, fn: 2, tn: 90, ...o })
  const curves = { roc: { fpr: [0, 0.5, 1], tpr: [0, 0.8, 1] }, pr: { recall: [0, 0.8, 1], precision: [1, 0.9, 0.1] } }
  const base = { dataset: 'SYNTHETIC', seed: 1, split: {}, threshold_selection: 'max F1 on validation', latency: 'Not evaluated' }
  it('shows metrics, confusion matrix, export links and "Not evaluated" for missing scores', async () => {
    mockFetch([['GET /api/v1/experiments/latest/metrics', 200, { ...base, models: { A: { test: t({ roc_auc: null }), curves }, FULL: { test: t(), curves } } }], ['GET /api/v1/experiments', 200, { items: [] }]])
    wrap(<ModelLab />); expect(await screen.findByText('ROC curves (test period)')).toBeInTheDocument()
    expect(screen.getByText('Not evaluated', { selector: 'td' })).toBeInTheDocument(); expect(screen.getByText('TP: 8')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Export CSV' })).toHaveAttribute('href', '/api/v1/exports/evaluation?format=csv')
  })
  it('explains when curves are unavailable and when nothing was evaluated', async () => {
    mockFetch([['GET /api/v1/experiments/latest/metrics', 200, { ...base, models: { FULL: { test: t(), curves: null } } }], ['GET /api/v1/experiments', 200, { items: [] }]])
    wrap(<ModelLab />); expect(await screen.findByText(/Curves not available/)).toBeInTheDocument(); cleanup()
    mockFetch([['GET /api/v1/experiments/latest/metrics', 404, { detail: 'Not evaluated: run python3 -m app.ml.experiment' }], ['GET /api/v1/experiments', 200, { items: [] }]])
    wrap(<ModelLab />); expect(await screen.findByRole('alert')).toHaveTextContent('Not evaluated')
  })
})

describe('ModelLab experiments', () => {
  const ok = { dataset: 'SYNTHETIC', seed: 1, split: {}, threshold_selection: 'x', latency: 'Not evaluated', models: { FULL: { test: { precision: 1, recall: 1, f1: 1, fpr: 0, roc_auc: 1, pr_auc: 1, threshold: 0.5, tp: 1, fp: 0, fn: 0, tn: 1 }, curves: null } } }
  it('launches an experiment with the chosen scenario, seed and key', async () => {
    const calls = mockFetch([['POST /api/v1/experiments', 202, { id: 'e1', scenario: 'decay_hard', seed: 7, status: 'queued' }], ['GET /api/v1/experiments/latest/metrics', 200, ok], ['GET /api/v1/experiments', 200, { items: [] }]])
    wrap(<ModelLab />); await screen.findByText(/Curves not available/)
    fireEvent.change(screen.getByLabelText('Scenario'), { target: { value: 'decay_hard' } }); fireEvent.change(screen.getByLabelText('Seed'), { target: { value: '7' } })
    fireEvent.change(screen.getByLabelText('API key'), { target: { value: 'k' } }); fireEvent.click(screen.getByRole('button', { name: 'Run experiment' }))
    expect(await screen.findByText('Started e1')).toBeInTheDocument()
    const post = calls.find(c => c.key.startsWith('POST'))!; expect(JSON.parse(String(post.init!.body))).toEqual({ scenario: 'decay_hard', seed: 7 })
    expect((post.init!.headers as Record<string, string>)['X-API-Key']).toBe('k')
  })
  it('shows run progress, blocks launching while active, and surfaces launch errors', async () => {
    mockFetch([['POST /api/v1/experiments', 409, { detail: 'an experiment is already queued or running' }], ['GET /api/v1/experiments/latest/metrics', 200, ok],
      ['GET /api/v1/experiments', 200, { items: [{ id: 'e2', scenario: 'base', seed: 3, status: 'running', stage: 'tuning decay rate' }, { id: 'e0', scenario: 'base', seed: 1, status: 'failed', error: 'boom' }] }]])
    wrap(<ModelLab />); expect(await screen.findByText('running: tuning decay rate')).toBeInTheDocument(); expect(screen.getByText(/failed \(boom\)/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Run experiment' })).toBeDisabled()
  })
})

describe('ModelLab latency', () => {
  const ok = { dataset: 'SYNTHETIC', seed: 1, split: {}, threshold_selection: 'x', latency: 'Not evaluated', models: { FULL: { test: { precision: 1, recall: 1, f1: 1, fpr: 0, roc_auc: 1, pr_auc: 1, threshold: 0.5, tp: 1, fp: 0, fn: 0, tn: 1 }, curves: null } } }
  const lat = { dataset: 'SYNTHETIC scenario=base seed=42', warm_events: 100, timed_events: 20, excludes: 'HTTP', hardware: { cpu: 'TestCPU', logical_cpus: 2, python: '3.12' },
    modes: { score_only: { p50_ms: 0.011, p95_ms: 0.02, p99_ms: 0.03, max_ms: 0.5 } } }
  it('shows measured latency with hardware, or "Not evaluated" when absent', async () => {
    mockFetch([['GET /api/v1/system/latency', 200, lat], ['GET /api/v1/experiments/latest/metrics', 200, ok], ['GET /api/v1/experiments', 200, { items: [] }]])
    wrap(<ModelLab />); expect(await screen.findByText(/TestCPU/)).toBeInTheDocument(); expect(screen.getByText('0.011')).toBeInTheDocument(); cleanup()
    mockFetch([['GET /api/v1/system/latency', 404, { detail: 'Not evaluated' }], ['GET /api/v1/experiments/latest/metrics', 200, ok], ['GET /api/v1/experiments', 200, { items: [] }]])
    wrap(<ModelLab />); await waitFor(() => expect(screen.getByTestId('latency')).toHaveTextContent('Not evaluated (run python3'))
  })
})

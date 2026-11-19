# Evaluation methodology
**Protocol.** Events are sorted by time and split 60/20/20 (train/validation/test). Everything fitted (scalers, logistic/tree models, ATFRP weights)
uses train rows only; the ATFRP decay rate tau and every model's decision threshold are chosen on validation only (tau by validation PR-AUC from
{0.25,1,4,16} days; threshold by max F1 on validation); metrics are computed once on test. Tests assert the split is chronological, features ignore
future events, events carry no label, and that corrupting test labels does not change the selected tau.
**Models.** A: logistic regression, gradient-boosted tree (transaction + prior-history features); B: static graph (counts of other accounts sharing an
identifier, no decay/propagation); C: temporal-behavioral; D: ATFRP without recency (no decay, no T); D1: no decay only; D2: no T only; E: no neighborhood; Full ATFRP.
**Metrics.** Precision, recall, F1, FPR, ROC-AUC, PR-AUC, confusion counts (`metrics.json`, `report.md`). Scoring latency: see below. Time-to-detect for clusters is visible per cluster (`detected_at`, checkpoint resolution) but not benchmarked.
ROC/PR curve points and confusion counts (test period) are stored in `metrics.json` and drawn in Model Lab; exports via `/api/v1/exports/evaluation`. Not produced: calibration analysis. Base-scenario artifacts for seeds 1-8 were regenerated with the current pipeline (curves and tuning table included).
**Data.** SYNTHETIC only (scenarios `base`, `decay`, `decay_hard`, authored by the project). No IEEE-CIS benchmark has been run.
**Measured results (test period, mean +- sd over seeds).**
- `base`, 8 seeds, current pipeline (decay rate tuned on validation; it selected tau=0.25 day on 7 of 8 seeds and 1 day on one; ~30-36 test fraud rows per seed): Full ATFRP F1 0.961±0.032, PR-AUC 0.983±0.037; gradient-boosted tree F1 0.788±0.144, PR-AUC 0.990±0.010; static graph F1 0.927±0.090, PR-AUC 0.993±0.005; no-neighborhood F1 0.773±0.098, PR-AUC 0.747±0.133; no-T-only F1 0.961±0.042, PR-AUC 0.984±0.038; no-recency F1 0.906±0.102, PR-AUC 0.956±0.074. Paired PR-AUC, Full minus: no-neighborhood +0.236 (wins 8/8, a clear effect); tree -0.007 (wins 5/8) and static graph -0.009 (wins 5/8), i.e. not distinguishable from the strong simple baselines here; no-recency +0.028 (sd 0.086, wins 4/8): no measurable recency effect on this scenario. This supersedes the earlier 5-seed figures (Full PR-AUC 0.997) that were produced with a fixed 1-day decay before tuning existed: validation-based tuning on a small validation set (~30 fraud rows) picked a shorter decay on most seeds and the test result was worse and more variable, which is a reminder that tuning noise is real with so few positives.
- `decay_hard`, 8 seeds (tuned tau; selected 1 day on all 8): Full ATFRP F1 0.979+-0.022, PR-AUC 0.997+-0.003, FPR 0.09%; gradient-boosted tree F1 0.925+-0.021, PR-AUC 0.975+-0.004; removing decay only: PR-AUC drops 0.19 on 8/8 seeds; removing T only: no reliable difference (full wins 3/8).
**Caveats.** Seeds change timing/noise, not structure, so they are not independent datasets; scenarios were designed by the authors; test sets hold ~30-80 fraud rows;
max-F1 thresholds are noisy for weak models (compare PR-AUC); results say nothing about real-world performance.

## Scoring latency (measured)
Method (`python3 -m app.ml.latency`): warm an engine by replaying the first 80% of a synthetic dataset, then process the next events one at a time and time each with `perf_counter_ns`; three separate passes (score only; score + state/graph update; score + update + explanation text).
Excludes HTTP/serialization, database writes, cluster detection and process startup. Single run, not repeated; no concurrent load.
Hardware: Intel(R) Xeon(R) Processor @ 2.10GHz, 1 logical CPU, Python 3.12.3, Linux-6.18.44-fc-v114-x86_64-with-glibc2.39.
Workload: SYNTHETIC scenario=base seed=42; 8181 warm events, 2000 timed events.
| Pass | mean ms | p50 ms | p95 ms | p99 ms | max ms |
|---|---|---|---|---|---|
| score_only | 0.013 | 0.0117 | 0.02 | 0.0344 | 0.2132 |
| score_and_update | 0.0136 | 0.0123 | 0.0202 | 0.0359 | 0.0603 |
| score_update_explain | 0.0197 | 0.0172 | 0.0311 | 0.052 | 0.114 |
Caveats: the synthetic graph has small neighborhoods; real data with identifiers shared by many accounts (up to `max_fanout`, default 50) will be slower, and per-event cost grows with neighborhood size.
These are in-process microsecond-scale figures, not end-to-end request latency; a full HTTP request adds framework overhead, and persistence of alerts is not part of the scoring path.

## Decay-rate selection rule (FG_TUNE_RULE)
Candidates `FG_TUNE_TAUS_DAYS` (default 0.25, 1, 4, 16 days) plus the default (1 day). **conservative** (default): keep the default tau unless another tau beats it in >= `FG_TUNE_CONFIDENCE` (0.95) of `FG_TUNE_BOOTSTRAP` (200) paired cluster-bootstrap resamples of the validation accounts (PR-AUC); then take the best such tau. **argmax**: best validation PR-AUC. Validation labels only; deterministic.
Rule and thresholds were fixed before the evaluations below, but the idea came from seeing argmax pick a worse tau on seeds 1-8 (base), so those seeds are not evidence for it. Evaluations used fresh seeds. Test-period metrics, 8 seeds each, paired by seed (PR-AUC, full model):
- `base`, seeds 101-108: conservative kept 1 day on all 8 seeds (argmax chose 0.25 day on 7): conservative 0.992+-0.009 vs argmax 0.988+-0.012; conservative minus argmax +0.004 (5 wins, 3 ties, 0 losses). Full vs tree +0.015 (wins 6/8), vs static graph -0.005 (3/8).
- `decay_hard`, seeds 101-108: identical choices and results for both rules (PR-AUC 0.976+-0.058, one weak seed drives the spread); full minus no-decay-only +0.299 (8/8), minus static graph +0.087 (7/8), minus tree +0.005 (7/8, sd 0.067).
- `decay_hard` with all timestamps divided by 8 (so the 1-day default is wrong), seeds 201-208: fixed default 0.930+-0.127; conservative 0.951+-0.081 (switched on 2/8); argmax 0.959+-0.083 (switched on 6/8). Conservative minus fixed +0.021 (2 wins, 0 losses); conservative minus argmax -0.008 (0 wins, 3 losses).
Reading: conservative never did worse than the fixed default in these tests, while argmax did (base, -0.004); but when the default is wrong, conservative under-switches and argmax recovers more. It is a variance/safety trade-off, not a clear improvement; differences are small compared with seed noise (sd 0.02-0.08), seeds share the same group structure, and the 0.25-day grid minimum is coarse for the compressed case. Set `FG_TUNE_RULE=argmax` to prefer responsiveness.
Raw results: `artifacts/experiments/tune_rule_comparison_*.json`.

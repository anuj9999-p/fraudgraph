"""Measured per-event scoring latency of the in-process online path (NOT training time, NOT HTTP, NOT DB writes, NOT cluster detection).
A warm engine replays the first `warm_frac` of events; each later event is then processed one at a time and timed with perf_counter_ns.
Three separate passes: score only; score + state/graph update; score + update + explanation text."""
import argparse, json, os, platform, sys, time
import numpy as np
from app.algorithms.atfrp import ATFRPEngine, ATFRPParams
from app.core.settings import get_settings, atfrp_defaults
from app.data.synthetic import generate
from app.explainability.explain import explain
from app.ml.experiment import _events

def _hw():
    cpu = ""
    try: cpu = next(l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name"))
    except Exception: pass
    return dict(platform=platform.platform(), cpu=cpu or platform.processor() or "unknown", logical_cpus=os.cpu_count(), python=sys.version.split()[0])

def _stats(ns):
    a = np.array(ns) / 1e6
    return dict(mean_ms=round(float(a.mean()), 4), p50_ms=round(float(np.percentile(a, 50)), 4), p95_ms=round(float(np.percentile(a, 95)), 4),
                p99_ms=round(float(np.percentile(a, 99)), 4), max_ms=round(float(a.max()), 4))

def benchmark(df, params, warm_frac=0.8, max_timed=2000):
    evs = sorted(_events(df), key=lambda e: (e.t, e.tx_id)); k = int(len(evs) * warm_frac); warm, timed = evs[:k], evs[k:k + max_timed]
    modes = {}
    for mode in ("score_only", "score_and_update", "score_update_explain"):
        eng = ATFRPEngine(params); eng.replay(warm); lat = []
        for e in timed:
            t0 = time.perf_counter_ns()
            if mode == "score_only":
                s = eng.process(e, commit=False); lat.append(time.perf_counter_ns() - t0); eng._apply(e, s)     # state advanced outside the timer
            else:
                s = eng.process(e)
                if mode == "score_update_explain": explain(s, params, None)
                lat.append(time.perf_counter_ns() - t0)
        modes[mode] = _stats(lat)
    return dict(warm_events=len(warm), timed_events=len(timed), modes=modes, hardware=_hw(),
                excludes="HTTP/serialization, database writes, cluster detection, process startup", measured_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--scenario", default="base"); ap.add_argument("--seed", type=int, default=None); a = ap.parse_args()
    g = get_settings(); seed = g.seed if a.seed is None else a.seed
    out = benchmark(generate(seed, scenario=a.scenario), ATFRPParams(**atfrp_defaults()))
    out.update(dataset=f"SYNTHETIC scenario={a.scenario} seed={seed}", params="algorithm defaults + FG_ATFRP_* overrides (latency does not depend on fitted weights)")
    d = g.artifact_dir / "experiments"; d.mkdir(parents=True, exist_ok=True); (d / f"latency_{a.scenario}_seed{seed}.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))

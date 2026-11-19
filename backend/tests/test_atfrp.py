import dataclasses, math, random, pytest
from app.algorithms.atfrp import *

def ev(i, t, acct="a", amt=10.0, ids=()): return Event(f"t{i}", t, acct, amt, tuple(ids))

def test_sigmoid_bounds():
    assert sigmoid(0) == 0.5 and 0 <= sigmoid(-1e4) < 1e-6 and sigmoid(1e4) <= 1.0

def test_event_has_no_label_field():
    assert "isFraud" not in {f.name for f in dataclasses.fields(Event)}
    assert not any("fraud" in f.name.lower() or "label" in f.name.lower() for f in dataclasses.fields(Event))

def test_neighborhood_bounds_and_decay():
    p = ATFRPParams(lam=0.1)
    fresh = neighborhood_risk([(2, 100.0, 1.0)], 100.0, p)
    old = neighborhood_risk([(2, 0.0, 1.0)], 100.0, p)
    assert fresh == pytest.approx(1.0) and 0 <= old < fresh
    assert neighborhood_risk([], 5.0, p) == 0.0
    assert 0 <= neighborhood_risk([(1, 0, 1), (5, 0, 1)], 0, p) <= 1

def test_aggregation_row_normalised():
    p = ATFRPParams(lam=0.0)
    assert neighborhood_risk([(1, 0, 1.0), (3, 0, 0.0)], 0, p) == pytest.approx(0.25)

def test_concentration():
    p = ATFRPParams(high_threshold=0.5, conc_ref=2)
    assert structural_concentration([], p) == 0
    assert structural_concentration([0.9, 0.9], p) == 1.0
    assert structural_concentration([0.9, 0.1], p) == pytest.approx(0.25)

def test_cold_start_and_deviation():
    p = ATFRPParams(min_history=3)
    assert behavioral_deviation([10, 10], 999, p) == (0.0, True)
    b, cold = behavioral_deviation([10, 11, 9, 10], 14, p)
    b2, _ = behavioral_deviation([10, 11, 9, 10], 10, p)
    assert not cold and 0 <= b2 < b <= 1

def test_param_validation():
    for bad in ({"lam": -1}, {"z_scale": 0}, {"entity_ewma": 0}, {"wB": float("nan")}, {"conc_ref": 0}):
        with pytest.raises(ValueError): ATFRPParams(**bad)

def _stream():
    ids = [("device", "d1")]
    e = [ev(i, i * 100.0, "a", 10 + i % 2, ids) for i in range(6)] + \
        [ev(10, 700.0, "a", 5000, ids), ev(11, 800.0, "b", 12, ids), ev(12, 900.0, "b", 12, ids)]
    return e

def test_all_scores_bounded():
    for s in ATFRPEngine().replay(_stream()):
        assert all(0 <= x <= 1 for x in (s.B, s.N, s.C, s.T, s.risk))

def test_deterministic_and_order_invariant():
    e = _stream(); sh = e[:]; random.Random(1).shuffle(sh)
    r1 = [(s.tx_id, s.risk) for s in ATFRPEngine().replay(e)]
    r2 = [(s.tx_id, s.risk) for s in ATFRPEngine().replay(sh)]
    assert r1 == r2

def test_future_events_do_not_change_earlier_scores():
    e = _stream(); cut = 7
    full = {s.tx_id: s.risk for s in ATFRPEngine().replay(e)}
    pre = {s.tx_id: s.risk for s in ATFRPEngine().replay(e[:cut])}
    assert all(full[k] == v for k, v in pre.items())

def test_same_timestamp_no_leakage():
    ids = [("device", "d1")]
    warm = [ev(i, i, "a", 10, ids) for i in range(5)]
    only = ATFRPEngine().replay(warm + [ev(99, 100.0, "a", 9999, ids)])
    both = ATFRPEngine().replay(warm + [ev(99, 100.0, "a", 9999, ids), ev(98, 100.0, "b", 9999, ids)])
    assert next(s for s in only if s.tx_id == "t99").risk == next(s for s in both if s.tx_id == "t99").risk

def test_risky_neighbor_raises_N_and_decays():
    ids = [("device", "d1")]
    def run(gap):
        evs = [ev(i, i * 10.0, "bad", 10, ids) for i in range(5)] + [ev(50, 50.0, "bad", 9e4, ids)]
        eng = ATFRPEngine(ATFRPParams(lam=1 / 1000)); eng.replay(evs)
        return eng.replay([ev(60, 50.0 + gap, "new", 10, ids)])[0].N
    assert run(10) > run(5000) > 0

def test_ablation_no_neighborhood_and_no_recency():
    ids = [("device", "d1")]
    evs = [ev(i, i, "x", 10, ids) for i in range(4)] + [ev(9, 10, "y", 10, ids)]
    s = ATFRPEngine(ATFRPParams(use_neighborhood=False)).replay(evs)[-1]
    assert s.N == 0 and s.C == 0
    s = ATFRPEngine(ATFRPParams(use_recency=False)).replay(evs)[-1]
    assert s.T == 0

def test_first_event_is_cold_start_low_risk():
    s = ATFRPEngine().replay([ev(1, 0.0)])[0]
    assert s.cold_start and s.N == 0 and s.T == 0 and s.risk < 0.1

def test_decay_only_and_T_only_ablations_are_separate():
    ids = [("device", "d1")]
    old = [ev(i, i * 10.0, "bad", 10, ids) for i in range(5)] + [ev(50, 50.0, "bad", 9e4, ids)]
    def n_at_late(**kw):
        eng = ATFRPEngine(ATFRPParams(lam=1 / 1000, **kw)); eng.replay(old)
        return eng.replay([ev(60, 1e6, "new", 10, ids)])[0]
    full, nodecay, noT = n_at_late(), n_at_late(use_decay=False), n_at_late(use_T=False)
    assert nodecay.N > full.N and nodecay.T == full.T          # decay removed, T kept
    assert noT.N == full.N and noT.T == 0                      # T removed, decay kept

def test_on_batch_sees_only_past_state_per_timestamp():
    seen = []
    evs = [ev(1, 1.0, "a"), ev(2, 1.0, "b"), ev(3, 5.0, "c")]
    ATFRPEngine().replay(evs, on_batch=lambda t, e: seen.append((t, sorted(e.risk))))
    assert seen == [(1.0, ["a", "b"]), (5.0, ["a", "b", "c"])]

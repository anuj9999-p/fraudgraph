"""ATFRP: Adaptive Temporal Fraud-Risk Propagation (pure algorithm, no UI/DB deps).

Per event at time t, for account i (all state strictly BEFORE t):
  B  behavioral deviation  = tanh(robust_z(amount | past amounts) / z_scale)   in [0,1] (saturates at 1.0 for extreme outliers)
  N  neighborhood risk     = sum_j A_ij * exp(-lam*dt_ij) * R_j(t-1)           in [0,1]
       j: other accounts sharing a device/email identifier with i.
       A_ij = shared_count_ij / sum_k shared_count_ik (row-normalised, self excluded)
       dt_ij = t - last time the shared link was observed. R_j = entity risk EWMA.
  C  structural concentration = frac_high_neighbors * min(1, n_high / conc_ref)
  T  temporal recency = exp(-lam_t * gap since account's previous event); 0 if none
  R  = sigmoid(wB*B + wN*N + wC*C + wT*T + b)   -- a RISK SCORE, not a calibrated probability.
Leakage guards: Event has no label field; events are replayed in (t, tx_id) order; all
events sharing a timestamp are scored before any state update (no same-time leakage);
an event never influences its own score. Weights here are manually configured defaults.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field, replace
from collections import defaultdict
from typing import Iterable


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x)) if x >= 0 else math.exp(x) / (1.0 + math.exp(x))


@dataclass(frozen=True)
class ATFRPParams:
    wB: float = 2.0; wN: float = 2.5; wC: float = 1.5; wT: float = 0.5; bias: float = -3.0
    lam: float = 1.0 / 86400.0          # neighborhood decay per second (1/day)
    lam_t: float = 1.0 / 3600.0         # recency decay per second (1/hour)
    min_history: int = 3                # events needed before B is defined
    z_scale: float = 3.0
    high_threshold: float = 0.5         # neighbor counted "high risk" for C
    conc_ref: int = 2
    entity_ewma: float = 0.5            # weight of newest risk in entity risk
    use_recency: bool = True            # ablation D
    use_neighborhood: bool = True       # ablation E
    use_decay: bool = True              # ablation D1: remove only exp(-lam*dt) in N (needs use_recency)
    use_T: bool = True                  # ablation D2: remove only the recency signal T (needs use_recency)
    max_fanout: int = 50                # ignore identifiers already shared by > this many accounts (as of now)

    def __post_init__(self):
        for n in ("lam", "lam_t", "z_scale"):
            if not getattr(self, n) >= 0 or not math.isfinite(getattr(self, n)):
                raise ValueError(f"{n} must be finite and >= 0")
        if self.z_scale == 0 or self.max_fanout < 1 or self.conc_ref < 1 or self.min_history < 1:
            raise ValueError("z_scale>0, conc_ref>=1, min_history>=1 required")
        if not (0 < self.entity_ewma <= 1 and 0 <= self.high_threshold <= 1):
            raise ValueError("entity_ewma in (0,1], high_threshold in [0,1]")
        for n in ("wB", "wN", "wC", "wT", "bias"):
            if not math.isfinite(getattr(self, n)):
                raise ValueError(f"{n} must be finite")


@dataclass(frozen=True)
class Event:  # deliberately NO label field
    tx_id: str
    t: float
    account: str
    amount: float
    identifiers: tuple = ()  # ((type, value), ...), e.g. ("device","d1")


@dataclass
class Score:
    tx_id: str; t: float; account: str
    B: float; N: float; C: float; T: float; risk: float
    cold_start: bool
    contributors: list = field(default_factory=list)  # (neighbor, A*decay*R) top-k


def behavioral_deviation(history: list, amount: float, p: ATFRPParams) -> tuple[float, bool]:
    if len(history) < p.min_history or not math.isfinite(amount):
        return 0.0, True
    s = sorted(history); n = len(s)
    med = s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])
    d = sorted(abs(x - med) for x in s)
    mad = d[n // 2] if n % 2 else 0.5 * (d[n // 2 - 1] + d[n // 2])
    scale = 1.4826 * mad + max(1e-6, 0.05 * abs(med))  # floor avoids div-by-zero
    return math.tanh(abs(amount - med) / scale / p.z_scale), False


def neighborhood_risk(neighbors: list, t: float, p: ATFRPParams) -> float:
    """neighbors: [(shared_count, last_seen_t, risk_j)]; returns N in [0,1]."""
    total = sum(c for c, _, _ in neighbors)
    if total <= 0:
        return 0.0
    lam = p.lam if (p.use_recency and p.use_decay) else 0.0
    return sum((c / total) * math.exp(-lam * max(0.0, t - ts)) * r for c, ts, r in neighbors)


def structural_concentration(risks: list, p: ATFRPParams) -> float:
    if not risks:
        return 0.0
    n_high = sum(r >= p.high_threshold for r in risks)
    return (n_high / len(risks)) * min(1.0, n_high / p.conc_ref)


class ATFRPEngine:
    def __init__(self, params: ATFRPParams | None = None):
        self.p = params or ATFRPParams()
        self.amounts = defaultdict(list); self.last_t = {}; self.risk = {}
        self.ids = defaultdict(set)                                  # account -> identifiers
        self.links = defaultdict(lambda: defaultdict(lambda: [0, 0.0]))  # ident -> acct -> [count,last_t]

    def _score(self, e: Event) -> Score:
        p = self.p; shared = {}
        for ident in self.ids.get(e.account, set()) | set(e.identifiers):
            lk = self.links.get(ident, {})
            if len(lk) > p.max_fanout:   # generic identifier (hub): uninformative, uses only past state
                continue
            for j, (c, ts) in lk.items():
                if j != e.account:
                    cur = shared.get(j, [0, 0.0]); shared[j] = [cur[0] + c, max(cur[1], ts)]
        nbrs = [(c, ts, self.risk.get(j, 0.0)) for j, (c, ts) in shared.items()]
        B, cold = behavioral_deviation(self.amounts.get(e.account, []), e.amount, p)
        N = neighborhood_risk(nbrs, e.t, p) if p.use_neighborhood else 0.0
        C = structural_concentration([r for _, _, r in nbrs], p) if p.use_neighborhood else 0.0
        T = 0.0
        if p.use_recency and p.use_T and e.account in self.last_t:
            T = math.exp(-p.lam_t * max(0.0, e.t - self.last_t[e.account]))
        R = sigmoid(p.wB * B + p.wN * N + p.wC * C + p.wT * T + p.bias)
        tot = sum(c for c, _, _ in nbrs) or 1
        lam = p.lam if (p.use_recency and p.use_decay) else 0.0
        contrib = sorted(((j, c / tot * math.exp(-lam * max(0, e.t - ts)) * self.risk.get(j, 0.0))
                          for j, (c, ts) in shared.items()), key=lambda x: (-x[1], x[0]))[:3]
        return Score(e.tx_id, e.t, e.account, B, N, C, T, R, cold, contrib)

    def _apply(self, e: Event, s: Score):
        a = self.p.entity_ewma
        self.risk[e.account] = s.risk if e.account not in self.risk else a * s.risk + (1 - a) * self.risk[e.account]
        self.amounts[e.account].append(e.amount); self.last_t[e.account] = e.t
        for ident in e.identifiers:
            self.ids[e.account].add(ident); l = self.links[ident][e.account]
            l[0] += 1; l[1] = e.t

    def process(self, e: Event, commit: bool = True) -> Score:
        """Online path for ONE event arriving after all processed history. commit=False scores without changing any state."""
        s = self._score(e)
        if commit: self._apply(e, s)
        return s

    def replay(self, events: Iterable[Event], on_batch=None) -> list[Score]:
        """on_batch(t, engine) is called after each distinct timestamp is fully applied (state = events with time <= t only)."""
        evs = sorted(events, key=lambda e: (e.t, e.tx_id)); out = []; i = 0
        while i < len(evs):
            j = i
            while j < len(evs) and evs[j].t == evs[i].t:
                j += 1
            batch = [(e, self._score(e)) for e in evs[i:j]]   # score all first...
            for e, s in batch:                                # ...then update state
                self._apply(e, s); out.append(s)
            if on_batch: on_batch(evs[i].t, self)
            i = j
        return out

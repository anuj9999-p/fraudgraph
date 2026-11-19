"""Suspicious-cluster detection: connected components of high-risk accounts linked by shared
identifiers. A cluster is a structural pattern worth review, NOT confirmed fraud."""
import hashlib, networkx as nx

def detect_clusters(engine, risk_threshold=0.6, min_size=3):
    hi = {a for a, r in engine.risk.items() if r >= risk_threshold}
    g = nx.Graph(); g.add_nodes_from(hi); shared = {}
    for ident, accts in engine.links.items():
        m = sorted(a for a in accts if a in hi)
        for i, a in enumerate(m):
            for b in m[i + 1:]:
                g.add_edge(a, b); shared.setdefault((a, b), []).append(list(ident))
    out = []
    for comp in nx.connected_components(g):
        if len(comp) < min_size: continue
        mem = sorted(comp); cid = "C-" + hashlib.sha1("|".join(mem).encode()).hexdigest()[:10]
        idents = sorted({tuple(i) for (a, b), v in shared.items() if a in comp for i in v})
        risk = sum(engine.risk[a] for a in mem) / len(mem)
        out.append(dict(cluster_id=cid, members=mem, size=len(mem), mean_risk=round(risk, 4),
                        shared_identifiers=[list(i) for i in idents],
                        detected_at=max(engine.last_t[a] for a in mem),
                        explanation=(f"{len(mem)} accounts with elevated risk are connected through "
                                     f"{len(idents)} shared identifier(s) (mean risk {risk:.2f}). "
                                     "This is a structural pattern for review, not confirmed fraud.")))
    return sorted(out, key=lambda c: (-c["mean_risk"], c["cluster_id"]))

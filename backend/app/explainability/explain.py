"""Explanations generated from computed evidence only (no LLM)."""
def explain(score, params, cluster=None):
    c = {"behavioral deviation": params.wB * score.B, "neighborhood risk": params.wN * score.N,
         "structural concentration": params.wC * score.C, "recency": params.wT * score.T}
    ranked = sorted(c.items(), key=lambda kv: -kv[1]); parts = []
    if score.B > 0.5: parts.append("the amount deviates substantially from the account's own history")
    if score.N > 0.1:
        who = ", ".join(n for n, v in score.contributors if v > 0) or "linked accounts"
        parts.append(f"it shares identifiers with previously risky accounts ({who})")
    if score.C > 0.3: parts.append("risk is concentrated among its linked accounts")
    if score.T > 0.5 and params.wT > 0: parts.append("it follows very recent activity on the same account")
    if cluster: parts.append(f"the account belongs to suspicious cluster {cluster['cluster_id']}")
    text = ("Elevated risk: " + "; ".join(parts) + "." if parts
            else "No dominant risk signal; score reflects the baseline.")
    warn = ["Cold start: too little account history for behavioral deviation."] if score.cold_start else []
    return dict(summary=text, ranked_signals=[dict(signal=k, contribution=round(v, 4)) for k, v in ranked],
                signals=dict(B=score.B, N=score.N, C=score.C, T=score.T), warnings=warn,
                neighbors=[dict(entity=n, weighted_risk=round(v, 4)) for n, v in score.contributors])

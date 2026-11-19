# Evaluation (SYNTHETIC data, test period)

{'train': 6063, 'val': 2021, 'test': 2021, 'test_fraud': 30}

| model | precision | recall | F1 | FPR | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| A_logreg | 1.000 | 0.433 | 0.605 | 0.0000 | 0.999 | 0.957 |
| A_hgb | 1.000 | 0.767 | 0.868 | 0.0000 | 1.000 | 0.981 |
| B_static_graph | 1.000 | 0.933 | 0.966 | 0.0000 | 1.000 | 0.987 |
| C_temporal_behavioral | 1.000 | 0.467 | 0.636 | 0.0000 | 0.994 | 0.831 |
| D_atfrp_no_recency | 0.968 | 1.000 | 0.984 | 0.0005 | 1.000 | 0.998 |
| D1_atfrp_no_decay_only | 0.968 | 1.000 | 0.984 | 0.0005 | 1.000 | 0.999 |
| D2_atfrp_no_T_only | 0.967 | 0.967 | 0.967 | 0.0005 | 1.000 | 0.995 |
| E_atfrp_no_neighborhood | 0.786 | 0.733 | 0.759 | 0.0030 | 0.947 | 0.588 |
| FULL_fraudgraph_atfrp | 0.967 | 0.967 | 0.967 | 0.0005 | 1.000 | 0.994 |

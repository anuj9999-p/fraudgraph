# Evaluation (SYNTHETIC data, test period)

{'train': 6136, 'val': 2045, 'test': 2046, 'test_fraud': 37}

| model | precision | recall | F1 | FPR | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| A_logreg | 1.000 | 0.595 | 0.746 | 0.0000 | 0.999 | 0.951 |
| A_hgb | 1.000 | 0.703 | 0.825 | 0.0000 | 0.995 | 0.957 |
| B_static_graph | 0.974 | 1.000 | 0.987 | 0.0005 | 1.000 | 1.000 |
| C_temporal_behavioral | 1.000 | 0.568 | 0.724 | 0.0000 | 0.991 | 0.838 |
| D_atfrp_no_recency | 0.974 | 1.000 | 0.987 | 0.0005 | 1.000 | 0.994 |
| D1_atfrp_no_decay_only | 0.972 | 0.946 | 0.959 | 0.0005 | 1.000 | 0.994 |
| D2_atfrp_no_T_only | 1.000 | 1.000 | 1.000 | 0.0000 | 1.000 | 1.000 |
| E_atfrp_no_neighborhood | 1.000 | 0.568 | 0.724 | 0.0000 | 0.947 | 0.873 |
| FULL_fraudgraph_atfrp | 1.000 | 0.946 | 0.972 | 0.0000 | 1.000 | 1.000 |

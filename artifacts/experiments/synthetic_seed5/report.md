# Evaluation (SYNTHETIC data, test period)

{'train': 6213, 'val': 2071, 'test': 2072, 'test_fraud': 32}

| model | precision | recall | F1 | FPR | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| A_logreg | 1.000 | 0.531 | 0.694 | 0.0000 | 0.999 | 0.930 |
| A_hgb | 1.000 | 0.656 | 0.792 | 0.0000 | 1.000 | 0.996 |
| B_static_graph | 1.000 | 1.000 | 1.000 | 0.0000 | 1.000 | 1.000 |
| C_temporal_behavioral | 1.000 | 0.375 | 0.545 | 0.0000 | 0.994 | 0.903 |
| D_atfrp_no_recency | 0.500 | 1.000 | 0.667 | 0.0157 | 0.994 | 0.769 |
| D1_atfrp_no_decay_only | 0.492 | 0.969 | 0.653 | 0.0157 | 0.994 | 0.770 |
| D2_atfrp_no_T_only | 1.000 | 1.000 | 1.000 | 0.0000 | 1.000 | 1.000 |
| E_atfrp_no_neighborhood | 1.000 | 0.750 | 0.857 | 0.0000 | 0.963 | 0.906 |
| FULL_fraudgraph_atfrp | 1.000 | 0.969 | 0.984 | 0.0000 | 1.000 | 1.000 |

# Evaluation (SYNTHETIC data, test period)

{'train': 6135, 'val': 2045, 'test': 2046, 'test_fraud': 32}

| model | precision | recall | F1 | FPR | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| A_logreg | 1.000 | 0.250 | 0.400 | 0.0000 | 0.999 | 0.969 |
| A_hgb | 1.000 | 0.281 | 0.439 | 0.0000 | 1.000 | 1.000 |
| B_static_graph | 1.000 | 0.906 | 0.951 | 0.0000 | 1.000 | 1.000 |
| C_temporal_behavioral | 1.000 | 0.250 | 0.400 | 0.0000 | 0.986 | 0.829 |
| D_atfrp_no_recency | 1.000 | 0.938 | 0.968 | 0.0000 | 1.000 | 1.000 |
| D1_atfrp_no_decay_only | 0.968 | 0.938 | 0.952 | 0.0005 | 1.000 | 0.996 |
| D2_atfrp_no_T_only | 1.000 | 0.938 | 0.968 | 0.0000 | 1.000 | 1.000 |
| E_atfrp_no_neighborhood | 0.708 | 0.531 | 0.607 | 0.0035 | 0.949 | 0.570 |
| FULL_fraudgraph_atfrp | 0.967 | 0.906 | 0.935 | 0.0005 | 1.000 | 0.992 |

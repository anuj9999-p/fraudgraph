# Evaluation (SYNTHETIC data, test period)

{'train': 6172, 'val': 2057, 'test': 2058, 'test_fraud': 35}

| model | precision | recall | F1 | FPR | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| A_logreg | 1.000 | 0.571 | 0.727 | 0.0000 | 0.999 | 0.971 |
| A_hgb | 1.000 | 0.571 | 0.727 | 0.0000 | 0.999 | 0.973 |
| B_static_graph | 1.000 | 0.914 | 0.955 | 0.0000 | 1.000 | 0.992 |
| C_temporal_behavioral | 1.000 | 0.371 | 0.542 | 0.0000 | 0.989 | 0.878 |
| D_atfrp_no_recency | 0.971 | 0.943 | 0.957 | 0.0005 | 1.000 | 0.994 |
| D1_atfrp_no_decay_only | 0.970 | 0.914 | 0.941 | 0.0005 | 1.000 | 0.993 |
| D2_atfrp_no_T_only | 1.000 | 0.943 | 0.971 | 0.0000 | 1.000 | 1.000 |
| E_atfrp_no_neighborhood | 1.000 | 0.629 | 0.772 | 0.0000 | 0.945 | 0.814 |
| FULL_fraudgraph_atfrp | 1.000 | 0.914 | 0.955 | 0.0000 | 1.000 | 0.999 |

# Evaluation (SYNTHETIC data, test period)

{'train': 6080, 'val': 2027, 'test': 2027, 'test_fraud': 34}

| model | precision | recall | F1 | FPR | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| A_logreg | 1.000 | 0.441 | 0.612 | 0.0000 | 0.999 | 0.973 |
| A_hgb | 1.000 | 0.735 | 0.847 | 0.0000 | 1.000 | 0.998 |
| B_static_graph | 0.970 | 0.941 | 0.955 | 0.0005 | 1.000 | 0.986 |
| C_temporal_behavioral | 1.000 | 0.235 | 0.381 | 0.0000 | 0.985 | 0.716 |
| D_atfrp_no_recency | 0.969 | 0.912 | 0.939 | 0.0005 | 1.000 | 0.988 |
| D1_atfrp_no_decay_only | 0.970 | 0.941 | 0.955 | 0.0005 | 1.000 | 0.993 |
| D2_atfrp_no_T_only | 1.000 | 0.912 | 0.954 | 0.0000 | 1.000 | 0.990 |
| E_atfrp_no_neighborhood | 0.941 | 0.471 | 0.627 | 0.0005 | 0.823 | 0.599 |
| FULL_fraudgraph_atfrp | 1.000 | 0.941 | 0.970 | 0.0000 | 1.000 | 0.996 |

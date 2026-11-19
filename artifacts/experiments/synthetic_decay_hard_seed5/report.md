# Evaluation (SYNTHETIC data, test period)

{'train': 6462, 'val': 2154, 'test': 2154, 'test_fraud': 69}

| model | precision | recall | F1 | FPR | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| A_logreg | 0.815 | 0.957 | 0.880 | 0.0072 | 0.997 | 0.838 |
| A_hgb | 0.908 | 1.000 | 0.952 | 0.0034 | 0.999 | 0.978 |
| B_static_graph | 0.873 | 1.000 | 0.932 | 0.0048 | 0.997 | 0.824 |
| C_temporal_behavioral | 0.948 | 0.797 | 0.866 | 0.0014 | 0.999 | 0.976 |
| D_atfrp_no_recency | 0.391 | 0.391 | 0.391 | 0.0201 | 0.950 | 0.510 |
| D1_atfrp_no_decay_only | 0.335 | 0.986 | 0.500 | 0.0647 | 0.972 | 0.592 |
| D2_atfrp_no_T_only | 0.627 | 1.000 | 0.771 | 0.0197 | 0.993 | 0.799 |
| E_atfrp_no_neighborhood | 0.885 | 0.667 | 0.760 | 0.0029 | 0.872 | 0.719 |
| FULL_fraudgraph_atfrp | 1.000 | 0.986 | 0.993 | 0.0000 | 1.000 | 1.000 |

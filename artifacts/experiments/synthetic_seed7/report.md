# Evaluation (SYNTHETIC data, test period)

{'train': 6232, 'val': 2077, 'test': 2078, 'test_fraud': 36}

| model | precision | recall | F1 | FPR | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| A_logreg | 0.968 | 0.833 | 0.896 | 0.0005 | 0.999 | 0.976 |
| A_hgb | 1.000 | 0.694 | 0.820 | 0.0000 | 1.000 | 1.000 |
| B_static_graph | 1.000 | 0.889 | 0.941 | 0.0000 | 1.000 | 0.997 |
| C_temporal_behavioral | 1.000 | 0.556 | 0.714 | 0.0000 | 0.997 | 0.894 |
| D_atfrp_no_recency | 1.000 | 0.778 | 0.875 | 0.0000 | 0.999 | 0.966 |
| D1_atfrp_no_decay_only | 1.000 | 0.833 | 0.909 | 0.0000 | 0.999 | 0.966 |
| D2_atfrp_no_T_only | 1.000 | 0.750 | 0.857 | 0.0000 | 0.991 | 0.884 |
| E_atfrp_no_neighborhood | 0.963 | 0.722 | 0.825 | 0.0005 | 0.943 | 0.789 |
| FULL_fraudgraph_atfrp | 1.000 | 0.806 | 0.892 | 0.0000 | 0.992 | 0.886 |

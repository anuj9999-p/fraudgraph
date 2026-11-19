# Evaluation (SYNTHETIC data, test period)

{'train': 6433, 'val': 2145, 'test': 2145, 'test_fraud': 77}

| model | precision | recall | F1 | FPR | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| A_logreg | 0.841 | 0.961 | 0.897 | 0.0068 | 0.997 | 0.873 |
| A_hgb | 0.854 | 0.987 | 0.916 | 0.0063 | 0.999 | 0.975 |
| B_static_graph | 0.854 | 0.987 | 0.916 | 0.0063 | 0.997 | 0.888 |
| C_temporal_behavioral | 0.944 | 0.870 | 0.905 | 0.0019 | 0.997 | 0.943 |
| D_atfrp_no_recency | 0.691 | 0.727 | 0.709 | 0.0121 | 0.991 | 0.809 |
| D1_atfrp_no_decay_only | 0.726 | 1.000 | 0.842 | 0.0140 | 0.996 | 0.905 |
| D2_atfrp_no_T_only | 0.987 | 0.974 | 0.980 | 0.0005 | 1.000 | 0.998 |
| E_atfrp_no_neighborhood | 0.810 | 0.610 | 0.696 | 0.0053 | 0.842 | 0.588 |
| FULL_fraudgraph_atfrp | 0.987 | 1.000 | 0.994 | 0.0005 | 1.000 | 0.999 |

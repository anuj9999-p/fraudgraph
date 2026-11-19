# Evaluation (SYNTHETIC data, test period)

{'train': 6283, 'val': 2095, 'test': 2095, 'test_fraud': 75}

| model | precision | recall | F1 | FPR | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| A_logreg | 0.877 | 0.853 | 0.865 | 0.0045 | 0.997 | 0.911 |
| A_hgb | 0.941 | 0.853 | 0.895 | 0.0020 | 0.999 | 0.977 |
| B_static_graph | 0.924 | 0.973 | 0.948 | 0.0030 | 0.998 | 0.896 |
| C_temporal_behavioral | 0.952 | 0.787 | 0.861 | 0.0015 | 0.998 | 0.958 |
| D_atfrp_no_recency | 0.557 | 0.973 | 0.709 | 0.0287 | 0.990 | 0.777 |
| D1_atfrp_no_decay_only | 0.661 | 0.987 | 0.791 | 0.0188 | 0.994 | 0.861 |
| D2_atfrp_no_T_only | 1.000 | 0.973 | 0.986 | 0.0000 | 1.000 | 1.000 |
| E_atfrp_no_neighborhood | 0.904 | 0.627 | 0.740 | 0.0025 | 0.817 | 0.625 |
| FULL_fraudgraph_atfrp | 1.000 | 0.960 | 0.980 | 0.0000 | 1.000 | 0.999 |

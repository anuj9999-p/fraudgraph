# Evaluation (SYNTHETIC data, test period)

{'train': 6373, 'val': 2124, 'test': 2125, 'test_fraud': 72}

| model | precision | recall | F1 | FPR | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| A_logreg | 0.838 | 0.931 | 0.882 | 0.0063 | 0.997 | 0.852 |
| A_hgb | 0.939 | 0.861 | 0.899 | 0.0019 | 0.999 | 0.972 |
| B_static_graph | 0.861 | 0.944 | 0.901 | 0.0054 | 0.997 | 0.844 |
| C_temporal_behavioral | 0.968 | 0.847 | 0.904 | 0.0010 | 0.999 | 0.953 |
| D_atfrp_no_recency | 0.826 | 0.264 | 0.400 | 0.0019 | 0.950 | 0.451 |
| D1_atfrp_no_decay_only | 0.543 | 0.958 | 0.693 | 0.0283 | 0.985 | 0.671 |
| D2_atfrp_no_T_only | 1.000 | 1.000 | 1.000 | 0.0000 | 1.000 | 1.000 |
| E_atfrp_no_neighborhood | 0.982 | 0.764 | 0.859 | 0.0005 | 0.872 | 0.803 |
| FULL_fraudgraph_atfrp | 1.000 | 0.958 | 0.979 | 0.0000 | 1.000 | 1.000 |

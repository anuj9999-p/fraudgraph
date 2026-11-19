# Evaluation (SYNTHETIC data, test period)

{'train': 6030, 'val': 2010, 'test': 2010, 'test_fraud': 33}

| model | precision | recall | F1 | FPR | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| A_logreg | 1.000 | 0.182 | 0.308 | 0.0000 | 0.999 | 0.951 |
| A_hgb | 1.000 | 0.879 | 0.935 | 0.0000 | 1.000 | 0.994 |
| B_static_graph | 1.000 | 0.909 | 0.952 | 0.0000 | 1.000 | 0.988 |
| C_temporal_behavioral | 1.000 | 0.273 | 0.429 | 0.0000 | 0.977 | 0.771 |
| D_atfrp_no_recency | 0.795 | 0.939 | 0.861 | 0.0040 | 0.999 | 0.930 |
| D1_atfrp_no_decay_only | 0.800 | 0.970 | 0.877 | 0.0040 | 0.999 | 0.931 |
| D2_atfrp_no_T_only | 1.000 | 0.939 | 0.969 | 0.0000 | 1.000 | 1.000 |
| E_atfrp_no_neighborhood | 1.000 | 0.758 | 0.862 | 0.0000 | 0.881 | 0.794 |
| FULL_fraudgraph_atfrp | 1.000 | 0.970 | 0.985 | 0.0000 | 1.000 | 1.000 |

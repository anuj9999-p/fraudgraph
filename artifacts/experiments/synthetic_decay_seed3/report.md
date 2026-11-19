# Evaluation (SYNTHETIC data, test period)

{'train': 6339, 'val': 2113, 'test': 2114, 'test_fraud': 79}

| model | precision | recall | F1 | FPR | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| A_logreg | 0.902 | 0.937 | 0.919 | 0.0039 | 0.999 | 0.984 |
| A_hgb | 1.000 | 0.975 | 0.987 | 0.0000 | 0.999 | 0.990 |
| B_static_graph | 0.949 | 0.937 | 0.943 | 0.0020 | 1.000 | 0.987 |
| C_temporal_behavioral | 0.937 | 0.937 | 0.937 | 0.0025 | 1.000 | 0.986 |
| D_atfrp_no_recency | 0.574 | 0.987 | 0.726 | 0.0285 | 0.988 | 0.706 |
| E_atfrp_no_neighborhood | 0.936 | 0.557 | 0.698 | 0.0015 | 0.811 | 0.640 |
| FULL_fraudgraph_atfrp | 0.988 | 1.000 | 0.994 | 0.0005 | 1.000 | 0.999 |

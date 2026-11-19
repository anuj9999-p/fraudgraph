# Evaluation (SYNTHETIC data, test period)

{'train': 6325, 'val': 2109, 'test': 2109, 'test_fraud': 72}

| model | precision | recall | F1 | FPR | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| A_logreg | 0.955 | 0.889 | 0.921 | 0.0015 | 1.000 | 0.989 |
| A_hgb | 1.000 | 0.889 | 0.941 | 0.0000 | 1.000 | 0.997 |
| B_static_graph | 0.986 | 0.958 | 0.972 | 0.0005 | 1.000 | 0.993 |
| C_temporal_behavioral | 0.938 | 0.847 | 0.891 | 0.0020 | 0.999 | 0.963 |
| D_atfrp_no_recency | 0.844 | 0.375 | 0.519 | 0.0025 | 0.964 | 0.568 |
| E_atfrp_no_neighborhood | 0.794 | 0.750 | 0.771 | 0.0069 | 0.880 | 0.615 |
| FULL_fraudgraph_atfrp | 0.857 | 1.000 | 0.923 | 0.0059 | 1.000 | 0.992 |

# Evaluation (SYNTHETIC data, test period)

{'train': 6325, 'val': 2109, 'test': 2109, 'test_fraud': 72}

| model | precision | recall | F1 | FPR | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| A_logreg | 0.831 | 0.889 | 0.859 | 0.0064 | 0.996 | 0.789 |
| A_hgb | 0.893 | 0.931 | 0.912 | 0.0039 | 0.999 | 0.966 |
| B_static_graph | 0.863 | 0.958 | 0.908 | 0.0054 | 0.997 | 0.823 |
| C_temporal_behavioral | 0.938 | 0.847 | 0.891 | 0.0020 | 0.999 | 0.963 |
| D_atfrp_no_recency | 0.844 | 0.375 | 0.519 | 0.0025 | 0.964 | 0.568 |
| D1_atfrp_no_decay_only | 0.632 | 1.000 | 0.774 | 0.0206 | 0.991 | 0.787 |
| D2_atfrp_no_T_only | 0.900 | 1.000 | 0.947 | 0.0039 | 1.000 | 0.994 |
| E_atfrp_no_neighborhood | 0.794 | 0.750 | 0.771 | 0.0069 | 0.880 | 0.615 |
| FULL_fraudgraph_atfrp | 0.857 | 1.000 | 0.923 | 0.0059 | 1.000 | 0.992 |

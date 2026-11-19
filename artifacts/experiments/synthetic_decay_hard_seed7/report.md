# Evaluation (SYNTHETIC data, test period)

{'train': 6487, 'val': 2162, 'test': 2163, 'test_fraud': 77}

| model | precision | recall | F1 | FPR | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| A_logreg | 0.849 | 0.948 | 0.896 | 0.0062 | 0.998 | 0.930 |
| A_hgb | 0.912 | 0.948 | 0.930 | 0.0034 | 0.999 | 0.980 |
| B_static_graph | 0.902 | 0.961 | 0.931 | 0.0038 | 0.998 | 0.933 |
| C_temporal_behavioral | 0.972 | 0.909 | 0.940 | 0.0010 | 0.999 | 0.978 |
| D_atfrp_no_recency | 0.846 | 0.571 | 0.682 | 0.0038 | 0.990 | 0.800 |
| D1_atfrp_no_decay_only | 0.758 | 0.974 | 0.852 | 0.0115 | 0.995 | 0.888 |
| D2_atfrp_no_T_only | 1.000 | 0.961 | 0.980 | 0.0000 | 0.999 | 0.990 |
| E_atfrp_no_neighborhood | 0.934 | 0.740 | 0.826 | 0.0019 | 0.874 | 0.759 |
| FULL_fraudgraph_atfrp | 1.000 | 0.987 | 0.993 | 0.0000 | 0.999 | 0.992 |

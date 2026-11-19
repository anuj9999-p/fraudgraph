# Evaluation (SYNTHETIC data, test period)

{'train': 6391, 'val': 2130, 'test': 2131, 'test_fraud': 76}

| model | precision | recall | F1 | FPR | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| A_logreg | 0.857 | 0.947 | 0.900 | 0.0058 | 0.997 | 0.868 |
| A_hgb | 0.869 | 0.961 | 0.912 | 0.0054 | 0.999 | 0.972 |
| B_static_graph | 0.864 | 1.000 | 0.927 | 0.0058 | 0.997 | 0.852 |
| C_temporal_behavioral | 0.968 | 0.803 | 0.878 | 0.0010 | 0.998 | 0.955 |
| D_atfrp_no_recency | 0.700 | 0.461 | 0.556 | 0.0073 | 0.979 | 0.677 |
| D1_atfrp_no_decay_only | 0.589 | 1.000 | 0.741 | 0.0258 | 0.991 | 0.799 |
| D2_atfrp_no_T_only | 0.644 | 1.000 | 0.784 | 0.0204 | 0.993 | 0.838 |
| E_atfrp_no_neighborhood | 0.846 | 0.724 | 0.780 | 0.0049 | 0.868 | 0.666 |
| FULL_fraudgraph_atfrp | 0.974 | 1.000 | 0.987 | 0.0010 | 1.000 | 0.997 |

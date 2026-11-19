# Evaluation (SYNTHETIC data, test period)

{'train': 6391, 'val': 2130, 'test': 2131, 'test_fraud': 76}

| model | precision | recall | F1 | FPR | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| A_logreg | 0.937 | 0.974 | 0.955 | 0.0024 | 1.000 | 0.989 |
| A_hgb | 0.961 | 0.961 | 0.961 | 0.0015 | 1.000 | 0.995 |
| B_static_graph | 0.974 | 1.000 | 0.987 | 0.0010 | 1.000 | 1.000 |
| C_temporal_behavioral | 0.968 | 0.803 | 0.878 | 0.0010 | 0.998 | 0.955 |
| D_atfrp_no_recency | 0.700 | 0.461 | 0.556 | 0.0073 | 0.979 | 0.677 |
| E_atfrp_no_neighborhood | 0.846 | 0.724 | 0.780 | 0.0049 | 0.868 | 0.666 |
| FULL_fraudgraph_atfrp | 0.987 | 1.000 | 0.993 | 0.0005 | 1.000 | 0.998 |

# Evaluation (SYNTHETIC data, test period)

{'train': 6373, 'val': 2124, 'test': 2125, 'test_fraud': 72}

| model | precision | recall | F1 | FPR | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| A_logreg | 0.895 | 0.944 | 0.919 | 0.0039 | 0.999 | 0.980 |
| A_hgb | 0.947 | 0.986 | 0.966 | 0.0019 | 1.000 | 0.998 |
| B_static_graph | 0.958 | 0.944 | 0.951 | 0.0015 | 1.000 | 0.993 |
| C_temporal_behavioral | 0.968 | 0.847 | 0.904 | 0.0010 | 0.999 | 0.953 |
| D_atfrp_no_recency | 0.826 | 0.264 | 0.400 | 0.0019 | 0.950 | 0.451 |
| E_atfrp_no_neighborhood | 0.982 | 0.764 | 0.859 | 0.0005 | 0.872 | 0.803 |
| FULL_fraudgraph_atfrp | 1.000 | 0.958 | 0.979 | 0.0000 | 1.000 | 1.000 |

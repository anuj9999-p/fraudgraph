# Evaluation (SYNTHETIC data, test period)

{'train': 6390, 'val': 2130, 'test': 2130, 'test_fraud': 71}

| model | precision | recall | F1 | FPR | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| A_logreg | 0.892 | 0.930 | 0.910 | 0.0039 | 0.998 | 0.853 |
| A_hgb | 0.909 | 0.986 | 0.946 | 0.0034 | 0.999 | 0.974 |
| B_static_graph | 0.899 | 1.000 | 0.947 | 0.0039 | 0.998 | 0.860 |
| C_temporal_behavioral | 0.969 | 0.873 | 0.919 | 0.0010 | 0.999 | 0.959 |
| D_atfrp_no_recency | 0.535 | 0.972 | 0.690 | 0.0291 | 0.984 | 0.635 |
| D1_atfrp_no_decay_only | 0.677 | 0.944 | 0.788 | 0.0155 | 0.992 | 0.757 |
| D2_atfrp_no_T_only | 1.000 | 0.972 | 0.986 | 0.0000 | 1.000 | 1.000 |
| E_atfrp_no_neighborhood | 0.836 | 0.718 | 0.773 | 0.0049 | 0.853 | 0.615 |
| FULL_fraudgraph_atfrp | 0.986 | 0.972 | 0.979 | 0.0005 | 1.000 | 0.999 |

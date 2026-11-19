# Evaluation (SYNTHETIC data, test period)

{'train': 6120, 'val': 2040, 'test': 2041, 'test_fraud': 34}

| model | precision | recall | F1 | FPR | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| A_logreg | 1.000 | 0.588 | 0.741 | 0.0000 | 0.999 | 0.959 |
| A_hgb | 0.964 | 0.794 | 0.871 | 0.0005 | 1.000 | 0.981 |
| B_static_graph | 1.000 | 0.529 | 0.692 | 0.0000 | 1.000 | 0.991 |
| C_temporal_behavioral | 1.000 | 0.265 | 0.419 | 0.0000 | 0.995 | 0.907 |
| D_atfrp_no_recency | 1.000 | 1.000 | 1.000 | 0.0000 | 1.000 | 1.000 |
| D1_atfrp_no_decay_only | 1.000 | 1.000 | 1.000 | 0.0000 | 1.000 | 1.000 |
| D2_atfrp_no_T_only | 1.000 | 1.000 | 1.000 | 0.0000 | 1.000 | 1.000 |
| E_atfrp_no_neighborhood | 0.964 | 0.794 | 0.871 | 0.0005 | 0.987 | 0.920 |
| FULL_fraudgraph_atfrp | 1.000 | 1.000 | 1.000 | 0.0000 | 1.000 | 1.000 |

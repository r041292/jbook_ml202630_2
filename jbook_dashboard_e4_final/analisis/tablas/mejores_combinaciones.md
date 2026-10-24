:::{table} Tabla maestra de mejores combinaciones de los 7 modelos base (bucle externo, media ± DE muestral de 5 folds).
:label: tab-mejores-combinaciones

| # | Modelo | Método final | Método por fold (1–5) | Hiperparámetros finales | RMSE | MAE | R² | RMSE test | MCS (7) |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 | **XGBoost** | Bayesiana TPE | Grid · TPE · TPE · DEAP · DEAP | n_estimators = 442; max_depth = 2; learning_rate = 0,0152 | 0,8156 ± 0,0344 | 0,6447 ± 0,0264 | 0,4646 ± 0,0484 | 0,9137 | Sí (1,000) |
| 2 | SVM lineal | Bayesiana TPE | Grid · DEAP · Grid · TPE · Random | C = 0,2438; epsilon = 0,513 | 0,8241 ± 0,0479 | 0,6503 ± 0,0408 | 0,4530 ± 0,0640 | 0,9299 | Sí (0,766) |
| 3 | Ridge | Bayesiana TPE | DEAP · Grid · Grid · TPE · TPE | alpha = 9,847 | 0,8253 ± 0,0520 | 0,6514 ± 0,0399 | 0,4514 ± 0,0672 | 0,9170 | Sí (0,766) |
| 4 | Lasso | Genética DEAP | Random · Random · Random · TPE · TPE | alpha = 0,0006685 | 0,8288 ± 0,0561 | 0,6542 ± 0,0439 | 0,4465 ± 0,0727 | 0,9197 | No (0,076) |
| 5 | Random Forest | Grid Search | Grid · Grid · TPE · Random · Grid | max_depth = 6; min_samples_leaf = 5; n_estimators = 500 | 0,8297 ± 0,0294 | 0,6619 ± 0,0291 | 0,4457 ± 0,0502 | 0,9396 | No (0,000) |
| 6 | KNN | Genética DEAP | DEAP · Grid · Grid · TPE · TPE | n_neighbors = 26; weights = distance; p = 2 | 0,8550 ± 0,0400 | 0,6809 ± 0,0308 | 0,4121 ± 0,0482 | 0,9239 | No (0,000) |
| 7 | Decision Tree | Random Search | TPE · Random · TPE · Random · Random | max_depth = 8; min_samples_leaf = 24; ccp_alpha = 0,001281 | 0,8948 ± 0,0325 | 0,7123 ± 0,0335 | 0,3552 ± 0,0613 | 1,0104 | No (0,000) |
:::

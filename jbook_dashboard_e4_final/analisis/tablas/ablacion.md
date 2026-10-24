:::{table} Ablación con predicciones OOF existentes (mismos folds). Δ < 0 favorece al modelo completo.
:label: tab-ablacion

| Modelo completo | Variante sin el componente | RMSE CV variante | RMSE CV completo | Δ RMSE OOF | IC 95 % BCa | p BCa | p permutación |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GPR–XGBoost | GPR solo (ejecución histórica gpr_xgb, 1 reinicio) | 0,8013 ± 0,0407 | 0,8028 | 0,0016 | [−0,0010; 0,0041] | 0,2292 | 0,2205 |
| GPR–XGBoost | XGBoost solo (clásico) | 0,8156 ± 0,0344 | 0,8028 | −0,0125 | [−0,0219; −0,0030] | 0,0102 | 0,0106 |
| KRR centrado | TN-KRR (solver truncado, sin centrar) | 0,8056 ± 0,0453 | 0,8010 | −0,0047 | [−0,0144; 0,0002] | 0,0592 | 0,1848 |
:::

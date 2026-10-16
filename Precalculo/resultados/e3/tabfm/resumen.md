# TabFM en E3

TabFM v1.0.0, checkpoint de regresión de Google, inferencia CPU local; no se ajustaron sus pesos.
Mismas variables, limpieza, grupos y test temporal E3. La selección es fija: no hay tuning.
Se conserva el test hasta completar los cinco folds externos y ajustar el estimador final.

## Validación agrupada

| Métrica | Media 5 folds | SD | OOF agrupado | Test temporal |
|---|---:|---:|---:|---:|
| RMSE | 0.812895 | 0.056542 | 0.814860 | 0.908725 |
| MAE | 0.635041 | 0.041816 | 0.635043 | 0.723177 |
| MAPE (%) | 23.757152 | 2.194258 | 23.756748 | 28.418015 |
| R² | 0.466371 | 0.075506 | 0.468392 | 0.451687 |

## Contrastes pareados

Permutación por estudiante: 99.999 reasignaciones; bootstrap: 10.000; semilla 42.
Holm global 23: 17 pares históricos vs. SVM, 4 previos vs. XGBoost y 2 de TabFM.
RMSE y R² comparten el contraste SSE y no se cuentan como hipótesis distintas.

| Referencia | Δ RMSE | IC95% marginal | p bilateral | p Holm global23 |
|---|---:|---:|---:|---:|
| SVM lineal | -0.018980 | [-0.048964, +0.011127] | 0.21684 | 1.00000 |
| XGBoost | +0.002452 | [-0.021853, +0.027191] | 0.85098 | 1.00000 |

Los IC son marginales. La comparación temporal es exploratoria por reutilización del test.
No rechazar H0 no demuestra equivalencia; una cohorte futura reservada daría una confirmación independiente.

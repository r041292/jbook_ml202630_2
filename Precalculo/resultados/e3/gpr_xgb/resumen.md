# GPR–XGBoost en E3

En el [ranking vigente de 26 modelos](../resumen_completo/resumen.md), esta
adaptación ocupa el puesto 22 (RMSE 0.959044) y no mejora a XGBoost original (0.906274).

Adaptación del stack GPR→XGBoost de arXiv:2610.15862. GPR genera media e incertidumbre; XGBoost aprende residuos con esas señales y las variables E3.
GPR out-of-fold por estudiante; cinco folds externos canónicos; hiperparámetros fijos antes de evaluar el test temporal.

## Métricas

| Métrica | Media 5 folds | SD | OOF agrupado | Test 202530 |
|---|---:|---:|---:|---:|
| RMSE | 0.844127 | 0.042008 | 0.845152 | 0.959044 |
| MAE | 0.659225 | 0.043228 | 0.659207 | 0.768130 |
| MAPE (%) | 24.416304 | 2.147952 | 24.415111 | 29.841323 |
| R² | 0.425000 | 0.067524 | 0.428132 | 0.389282 |

## Ablación GPR sola

| Métrica | Media 5 folds | OOF agrupado | Test 202530 |
|---|---:|---:|---:|
| RMSE | 0.801291 | 0.802113 | 0.905838 |
| MAE | 0.630181 | 0.630179 | 0.729975 |
| MAPE (%) | 23.734379 | 23.733865 | 28.420093 |
| R² | 0.482889 | 0.484894 | 0.455165 |

Intervalo conformal agrupado nominal 95%: radio=1.682736; cobertura observada en test=0.9255 (descriptiva).

## Contrastes pareados

Permutación por estudiante: 99.999 reasignaciones; bootstrap: 10.000; semilla 42.
Holm global 33: familia histórica de 23 más diez contrastes contra SVM, XGBoost, TabICLv2, TabPFN original/fine-tuned, TabFM, TCR-XGBoost, Kernel Ridge, CatBoost y GPR solo.
RMSE y R² comparten el contraste SSE; los IC son marginales.

| Referencia | Δ RMSE | IC95% marginal | p bilateral | p Holm global33 |
|---|---:|---:|---:|---:|
| SVM lineal | +0.031338 | [-0.017082, +0.078935] | 0.20154 | 1.00000 |
| XGBoost | +0.052770 | [+0.012543, +0.092420] | 0.01064 | 0.29792 |
| TabICLv2 | +0.061229 | [+0.023214, +0.099128] | 0.00236 | 0.07552 |
| TabPFN 2.5 original | +0.060767 | [+0.021912, +0.099710] | 0.00314 | 0.09420 |
| TabFM 1.0.0 (PyTorch CPU, 32 vistas) | +0.050319 | [+0.013321, +0.087689] | 0.01064 | 0.29792 |
| TCR-XGBoost | +0.051349 | [+0.009570, +0.093433] | 0.01826 | 0.41998 |
| Kernel Ridge RBF | +0.054163 | [+0.012639, +0.095115] | 0.01214 | 0.30350 |
| CatBoost | +0.053375 | [+0.011570, +0.095604] | 0.01414 | 0.33936 |
| TabPFN 2.5 fine-tuned | +0.057674 | [+0.018202, +0.096815] | 0.00566 | 0.16414 |
| GPR solo | +0.053206 | [+0.012487, +0.093341] | 0.01158 | 0.30108 |

La partición aleatoria del preprint y sus resultados de ingeniería no se comparan directamente con E3.
El test temporal ya fue consultado en experimentos anteriores; interpretar los contrastes como exploratorios.

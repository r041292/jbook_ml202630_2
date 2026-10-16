# LinXGBoost — Entregable 3

Implementación E3 independiente inspirada en [LinXGBoost (de Vito, 2017)](https://arxiv.org/abs/1710.03634).
Las hojas ajustan Ridge con todas las columnas numéricas y one-hot; el escalado de las 67
columnas se aprende dentro de cada fit. Se evalúa con GroupKFold anidado 5×5 y el test temporal se usa al final.
Los cortes continuos se aproximan con hasta 12 cuantiles para reducir coste de búsqueda.
El test ya se consultó en rondas anteriores, por lo que la comparación es exploratoria.
La ablation previa con hojas solo numéricas obtuvo RMSE test 1.017309; queda archivada en
`ablation_numeric_leaves/`. No se calculó un contraste estadístico entre ambas implementaciones.

## Resultado de LinXGBoost

| Métrica | Test | CV media ± SD | OOF agrupado |
|---|---:|---:|---:|
| RMSE | 1.012583 | 0.873296 ± 0.032662 | 0.873899 |
| MAE | 0.852756 | 0.724814 ± 0.026248 | 0.724807 |
| MAPE (%) | 33.395243 | 27.956415 ± 1.846332 | 27.955662 |
| R² | 0.319192 | 0.387108 ± 0.037265 | 0.388569 |

Parámetros finales seleccionados dentro de todo train: `{"modelo__gamma": 0.05, "modelo__learning_rate": 0.16, "modelo__max_depth": 2, "modelo__min_samples_leaf": 160, "modelo__n_estimators": 5, "modelo__reg_lambda": 0.9541624171184552}`.

## Comparadores

| Modelo | RMSE test | MAE | MAPE (%) | R² | ΔRMSE vs XGBoost |
|---|---:|---:|---:|---:|---:|
| XGBoost | 0.906274 | 0.728918 | 28.4048 | 0.454641 | +0.000000 |
| SVR RBF | 0.892225 | 0.713154 | 28.2860 | 0.471418 | -0.014049 |
| TabICLv2 | 0.897815 | 0.717104 | 28.4121 | 0.464774 | -0.008459 |
| SVM lineal | 0.927706 | 0.755443 | 29.6646 | 0.428543 | +0.021432 |
| XGBoost ampliado (gbtree) | 0.909207 | 0.736379 | 28.6695 | 0.451105 | +0.002933 |
| DART-XGBoost | 0.922167 | 0.751176 | 29.3505 | 0.435346 | +0.015893 |
| DenseWeight-XGBoost | 0.913037 | 0.734107 | 28.3404 | 0.446471 | +0.006763 |
| LinXGBoost (hojas completas E3) | 1.012583 | 0.852756 | 33.3952 | 0.319192 | +0.106310 |

## Contrastes pareados de RMSE

Holm7 corrige los siete contrastes del nuevo candidato frente a XGBoost, SVR RBF, TabICLv2,
SVM lineal y las tres variantes XGBoost. Las correcciones anteriores Holm55 y Holm12 se mantienen separadas.

| Referencia | ΔRMSE | IC95% | p bruto | p Holm7 |
|---|---:|---:|---:|---:|
| XGBoost | +0.106310 | [+0.059512, +0.154021] | 0.00004 | 0.00020 |
| SVR RBF | +0.120358 | [+0.075151, +0.167008] | 0.00002 | 0.00014 |
| TabICLv2 | +0.114768 | [+0.073549, +0.158360] | 0.00002 | 0.00014 |
| SVM lineal | +0.084878 | [+0.041171, +0.128942] | 0.00018 | 0.00024 |
| XGBoost ampliado (gbtree) | +0.103376 | [+0.057890, +0.149512] | 0.00006 | 0.00024 |
| DART-XGBoost | +0.090417 | [+0.049665, +0.132418] | 0.00006 | 0.00024 |
| DenseWeight-XGBoost | +0.099546 | [+0.053346, +0.147030] | 0.00006 | 0.00024 |

## Ranking RMSE de los 26 modelos

El ranking es descriptivo. Los p-valores pertenecen a familias de contraste distintas y no se
combinan como si formaran una sola corrección global.

| Puesto | Modelo | RMSE test | ΔRMSE vs XGBoost |
|---:|---|---:|---:|
| 1 | SVR RBF | 0.892225 | -0.014049 |
| 2 | TabICLv2 | 0.897815 | -0.008459 |
| 3 | TabPFN 2.5 original | 0.898277 | -0.007996 |
| 4 | TabPFN 2.5 fine-tuned | 0.901370 | -0.004903 |
| 5 | Kernel Ridge RBF | 0.904881 | -0.001393 |
| 6 | CatBoost | 0.905669 | -0.000604 |
| 7 | XGBoost | 0.906274 | +0.000000 |
| 8 | TCR-XGBoost | 0.907695 | +0.001422 |
| 9 | TabFM 1.0.0 (PyTorch CPU, 32 vistas) | 0.908725 | +0.002452 |
| 10 | XGBoost ampliado (gbtree) | 0.909207 | +0.002933 |
| 11 | RaFFLE | 0.912925 | +0.006652 |
| 12 | DenseWeight-XGBoost | 0.913037 | +0.006763 |
| 13 | Ridge | 0.917090 | +0.010817 |
| 14 | Lasso | 0.919650 | +0.013376 |
| 15 | DART-XGBoost | 0.922167 | +0.015893 |
| 16 | KNN | 0.923270 | +0.016996 |
| 17 | HRT-Boost | 0.923720 | +0.017446 |
| 18 | logicDT propio (adaptado) | 0.926438 | +0.020164 |
| 19 | SVM lineal | 0.927706 | +0.021432 |
| 20 | Random Forest | 0.939635 | +0.033362 |
| 21 | GPR–XGBoost (OOF agrupado) | 0.959044 | +0.052770 |
| 22 | RIM (port E3) | 0.967213 | +0.060939 |
| 23 | XBART (GFR) | 0.967515 | +0.061241 |
| 24 | coPILOT | 0.970603 | +0.064329 |
| 25 | LinXGBoost (hojas completas E3) | 1.012583 | +0.106310 |
| 26 | Dummy media | 1.256059 | +0.349785 |

Los resultados de CV, con parámetros elegidos de forma anidada, se leen junto con el test y los
contrastes pareados; el test no se usa para elegir hiperparámetros.

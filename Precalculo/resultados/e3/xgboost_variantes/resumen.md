# Variantes metodológicas de XGBoost — E3

Este informe conserva el corte histórico de 25 modelos anterior a LinXGBoost.
El [ranking vigente incluye 26](../resumen_completo/resumen.md): XGBoost ampliado
ocupa el puesto 11, DenseWeight el 13 y DART el 16, frente a XGBoost original
en el 8. Ninguna variante mejora su RMSE temporal.

Selección anidada 5×5 por GroupKFold de estudiante. El control gbtree amplía la búsqueda
del XGBoost original; DART aplica dropout de árboles; DenseWeight-XGBoost pondera la loss
según la rareza estimada de y dentro de cada fit. Selección solo con train; test 202530 al final.
El test fue consultado en experimentos anteriores, por lo que las comparaciones son exploratorias.

## Ranking descriptivo por RMSE test: 25 modelos

| Rango | Modelo | RMSE test | ΔRMSE vs XGBoost |
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
| 25 | Dummy media | 1.256059 | +0.349785 |

Los 22 modelos históricos conservan Holm55 de la comparación E3 anterior; los tres
candidatos nuevos se contrastan en una familia separada Holm12, cuyos p-valores aparecen abajo.

## Métricas test de las variantes y sus referencias

Esta tabla de seis modelos facilita comparar los candidatos con XGBoost original y con los dos
mejores comparadores previos. p Holm12 se muestra solo para cada contraste candidato–XGBoost.

| Modelo | RMSE | MAE | MAPE (%) | R² | ΔRMSE vs XGBoost | p Holm12 vs XGBoost |
|---|---:|---:|---:|---:|---:|---:|
| SVR RBF | 0.892225 | 0.713154 | 28.2860 | 0.471418 | -0.014049 | — |
| TabICLv2 | 0.897815 | 0.717104 | 28.4121 | 0.464774 | -0.008459 | — |
| XGBoost | 0.906274 | 0.728918 | 28.4048 | 0.454641 | +0.000000 | — |
| XGBoost ampliado (gbtree) | 0.909207 | 0.736379 | 28.6695 | 0.451105 | +0.002933 | 1.00000 |
| DenseWeight-XGBoost | 0.913037 | 0.734107 | 28.3404 | 0.446471 | +0.006763 | 1.00000 |
| DART-XGBoost | 0.922167 | 0.751176 | 29.3505 | 0.435346 | +0.015893 | 0.52200 |

## Contrastes pareados

La familia de 12 incluye cada nueva variante frente a XGBoost, SVR RBF y TabICLv2, más los tres
contrastes entre variantes. Los intervalos son bootstrap por estudiante; RMSE/R² comparten SSE.

| Candidato | Referencia | ΔRMSE | IC95% | p bruto | p Holm12 |
|---|---|---:|---:|---:|---:|
| XGBoost ampliado (gbtree) | XGBoost | +0.002933 | [-0.005029, +0.010826] | 0.47478 | 1.00000 |
| XGBoost ampliado (gbtree) | SVR RBF | +0.016982 | [-0.008327, +0.043052] | 0.19374 | 1.00000 |
| XGBoost ampliado (gbtree) | TabICLv2 | +0.011392 | [-0.010948, +0.035132] | 0.33148 | 1.00000 |
| DART-XGBoost | XGBoost | +0.015893 | [-0.000180, +0.031867] | 0.05220 | 0.52200 |
| DART-XGBoost | SVR RBF | +0.029942 | [+0.001975, +0.057585] | 0.03578 | 0.42936 |
| DART-XGBoost | TabICLv2 | +0.024352 | [+0.001233, +0.048353] | 0.04076 | 0.44836 |
| DenseWeight-XGBoost | XGBoost | +0.006763 | [-0.011545, +0.025289] | 0.47194 | 1.00000 |
| DenseWeight-XGBoost | SVR RBF | +0.020812 | [-0.009085, +0.051295] | 0.17204 | 1.00000 |
| DenseWeight-XGBoost | TabICLv2 | +0.015222 | [-0.010173, +0.040051] | 0.23516 | 1.00000 |
| XGBoost ampliado (gbtree) | DART-XGBoost | -0.012960 | [-0.026543, +0.000747] | 0.06796 | 0.61164 |
| XGBoost ampliado (gbtree) | DenseWeight-XGBoost | -0.003830 | [-0.024023, +0.016032] | 0.70924 | 1.00000 |
| DART-XGBoost | DenseWeight-XGBoost | +0.009130 | [-0.014215, +0.031800] | 0.44604 | 1.00000 |

## Validación agrupada

| Modelo | RMSE medio CV | SD | OOF |
|---|---:|---:|---:|
| XGBoost ampliado (gbtree) | 0.811859 | 0.038683 | 0.812773 |
| DART-XGBoost | 0.813206 | 0.033708 | 0.813899 |
| DenseWeight-XGBoost | 0.809715 | 0.034338 | 0.810435 |

## Errores OOF por tramo de nota

Descriptivo y calculado solo con predicciones out-of-fold de train. Sesgo positivo indica subpredicción.

| Modelo | Tramo | n | RMSE OOF | Sesgo nota−predicción |
|---|---|---:|---:|---:|
| XGBoost original | ≤1 | 28 | 1.571312 | -1.424060 |
| XGBoost original | (1,2] | 149 | 1.126832 | -0.925994 |
| XGBoost original | (2,3] | 298 | 0.765946 | -0.461837 |
| XGBoost original | (3,4] | 328 | 0.584220 | +0.036872 |
| XGBoost original | >4 | 506 | 0.800179 | +0.603015 |
| XGBoost ampliado (gbtree) | ≤1 | 28 | 1.540316 | -1.392670 |
| XGBoost ampliado (gbtree) | (1,2] | 149 | 1.118855 | -0.914464 |
| XGBoost ampliado (gbtree) | (2,3] | 298 | 0.766218 | -0.449429 |
| XGBoost ampliado (gbtree) | (3,4] | 328 | 0.601070 | +0.040850 |
| XGBoost ampliado (gbtree) | >4 | 506 | 0.793148 | +0.596983 |
| DART-XGBoost | ≤1 | 28 | 1.619707 | -1.498494 |
| DART-XGBoost | (1,2] | 149 | 1.132636 | -0.963587 |
| DART-XGBoost | (2,3] | 298 | 0.760981 | -0.490737 |
| DART-XGBoost | (3,4] | 328 | 0.564395 | +0.030500 |
| DART-XGBoost | >4 | 506 | 0.802008 | +0.624764 |
| DenseWeight-XGBoost | ≤1 | 28 | 1.510560 | -1.358387 |
| DenseWeight-XGBoost | (1,2] | 149 | 1.085387 | -0.875997 |
| DenseWeight-XGBoost | (2,3] | 298 | 0.761126 | -0.433523 |
| DenseWeight-XGBoost | (3,4] | 328 | 0.596812 | +0.060191 |
| DenseWeight-XGBoost | >4 | 506 | 0.808638 | +0.609498 |

DenseWeight reduce RMSE OOF en ≤1 de 1.5713 a 1.5106, pero en >4 cambia de 0.8002 a 0.8086. Ese intercambio explica por qué un mejor tail score no garantiza un RMSE global menor.

DenseWeight cambia el coste relativo de los errores; una mejora en notas raras puede aumentar
el RMSE global. Para ello se revisan también errores por tramo de nota y no se interpreta esa
ponderación como prueba de mejora global si el RMSE total no baja.

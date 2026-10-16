# LinXGBoost — Entregable 3

Implementación independiente cotejada con el repositorio de [LinXGBoost (de Vito, 2017)](https://github.com/ldv1/LinXGBoost).
Las hojas ajustan Ridge con las 67 columnas numéricas y one-hot, escaladas dentro de cada fit.
Se alinea con el repositorio en la inicialización cero, profundidad raíz=1, poda, penalización lambda
y aporte sin shrinkage del árbol final. Los cortes continuos se aproximan con 12 cuantiles; el
repositorio barre todos los cortes distintos, así que esta es una aproximación de cómputo.
Al puntuar cortes candidatos, este motor usa Ridge regularizado y `lstsq` si el solver falla; el
repositorio además aplica un umbral explícito de condición y fallback constante por candidato.
Se evalúa con GroupKFold anidado 5×5 y el test temporal se usa al final.
El test ya se consultó en rondas anteriores, por lo que la comparación es exploratoria.
El full-one-hot anterior (RMSE 1.012583) usaba convenciones distintas y queda supersedido.
Una corrida previa de hojas solo numéricas obtuvo RMSE test 1.017309, pero usaba convenciones
distintas de inicialización y shrinkage; está supersedida y no es una ablation comparable.
Su reporte se conserva en `ablation_numeric_leaves/` por trazabilidad.

## Resultado de LinXGBoost

| Métrica | Test | CV media ± SD | OOF agrupado |
|---|---:|---:|---:|
| RMSE | 0.899069 | 0.844282 ± 0.043081 | 0.845385 |
| MAE | 0.720464 | 0.665239 ± 0.041808 | 0.665242 |
| MAPE (%) | 28.234859 | 24.698145 ± 1.957916 | 24.697646 |
| R² | 0.463278 | 0.424701 ± 0.069635 | 0.427817 |

Parámetros finales seleccionados dentro de todo train: `{"modelo__gamma": 0.05, "modelo__learning_rate": 0.16, "modelo__max_depth": 2, "modelo__min_samples_leaf": 120, "modelo__n_estimators": 5, "modelo__reg_lambda": 34.16658290996042}`.

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
| LinXGBoost (hojas completas E3) | 0.899069 | 0.720464 | 28.2349 | 0.463278 | -0.007205 |

## Contrastes pareados de RMSE

Holm7 corrige los siete contrastes del nuevo candidato frente a XGBoost, SVR RBF, TabICLv2,
SVM lineal y las tres variantes XGBoost. Las correcciones anteriores Holm55 y Holm12 se mantienen separadas.

| Referencia | ΔRMSE | IC95% | p bruto | p Holm7 |
|---|---:|---:|---:|---:|
| XGBoost | -0.007205 | [-0.036278, +0.021475] | 0.62662 | 1.00000 |
| SVR RBF | +0.006844 | [-0.019447, +0.034461] | 0.61372 | 1.00000 |
| TabICLv2 | +0.001254 | [-0.023455, +0.028165] | 0.92756 | 1.00000 |
| SVM lineal | -0.028637 | [-0.054233, -0.003261] | 0.03070 | 0.21490 |
| XGBoost ampliado (gbtree) | -0.010138 | [-0.039127, +0.018147] | 0.48932 | 1.00000 |
| DART-XGBoost | -0.023098 | [-0.052170, +0.005473] | 0.11912 | 0.71472 |
| DenseWeight-XGBoost | -0.013968 | [-0.045529, +0.017781] | 0.38370 | 1.00000 |

## Ranking RMSE de los 26 modelos

El ranking es descriptivo. Los p-valores pertenecen a familias de contraste distintas y no se
combinan como si formaran una sola corrección global.

| Puesto | Modelo | RMSE test | ΔRMSE vs XGBoost |
|---:|---|---:|---:|
| 1 | SVR RBF | 0.892225 | -0.014049 |
| 2 | TabICLv2 | 0.897815 | -0.008459 |
| 3 | TabPFN 2.5 original | 0.898277 | -0.007996 |
| 4 | LinXGBoost (hojas completas E3) | 0.899069 | -0.007205 |
| 5 | TabPFN 2.5 fine-tuned | 0.901370 | -0.004903 |
| 6 | Kernel Ridge RBF | 0.904881 | -0.001393 |
| 7 | CatBoost | 0.905669 | -0.000604 |
| 8 | XGBoost | 0.906274 | +0.000000 |
| 9 | TCR-XGBoost | 0.907695 | +0.001422 |
| 10 | TabFM 1.0.0 (PyTorch CPU, 32 vistas) | 0.908725 | +0.002452 |
| 11 | XGBoost ampliado (gbtree) | 0.909207 | +0.002933 |
| 12 | RaFFLE | 0.912925 | +0.006652 |
| 13 | DenseWeight-XGBoost | 0.913037 | +0.006763 |
| 14 | Ridge | 0.917090 | +0.010817 |
| 15 | Lasso | 0.919650 | +0.013376 |
| 16 | DART-XGBoost | 0.922167 | +0.015893 |
| 17 | KNN | 0.923270 | +0.016996 |
| 18 | HRT-Boost | 0.923720 | +0.017446 |
| 19 | logicDT propio (adaptado) | 0.926438 | +0.020164 |
| 20 | SVM lineal | 0.927706 | +0.021432 |
| 21 | Random Forest | 0.939635 | +0.033362 |
| 22 | GPR–XGBoost (OOF agrupado) | 0.959044 | +0.052770 |
| 23 | RIM (port E3) | 0.967213 | +0.060939 |
| 24 | XBART (GFR) | 0.967515 | +0.061241 |
| 25 | coPILOT | 0.970603 | +0.064329 |
| 26 | Dummy media | 1.256059 | +0.349785 |

Los resultados de CV, con parámetros elegidos de forma anidada, se leen junto con el test y los
contrastes pareados; el test no se usa para elegir hiperparámetros.

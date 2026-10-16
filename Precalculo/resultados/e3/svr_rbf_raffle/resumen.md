# SVR RBF y RaFFLE en E3

Evaluación con cinco folds externos canónicos y cinco folds internos GroupKFold por estudiante.
La preparación se ajusta dentro de cada fit; el test temporal 202530 se predice al final.
La inferencia del test es exploratoria porque ese periodo ya se consultó en experimentos anteriores.

## Métricas y ranking temporal

| Rango | Modelo | RMSE test | Δ RMSE vs. SVM | Holm vs. SVM (21) | Holm global (55) |
|---:|---|---:|---:|---:|---:|
| 1 | SVR RBF | 0.892225 | -0.035481 | 0.20360 | 0.49882 |
| 2 | TabICLv2 | 0.897815 | -0.029891 | 0.49856 | 1.00000 |
| 3 | TabPFN 2.5 original | 0.898277 | -0.029428 | 1.00000 | 1.00000 |
| 4 | TabPFN 2.5 fine-tuned | 0.901370 | -0.026336 | 1.00000 | 1.00000 |
| 5 | Kernel Ridge RBF | 0.904881 | -0.022825 | 1.00000 | 1.00000 |
| 6 | CatBoost | 0.905669 | -0.022036 | 1.00000 | 1.00000 |
| 7 | XGBoost | 0.906274 | -0.021432 | 1.00000 | 1.00000 |
| 8 | TCR-XGBoost | 0.907695 | -0.020010 | 1.00000 | 1.00000 |
| 9 | TabFM 1.0.0 (PyTorch CPU, 32 vistas) | 0.908725 | -0.018980 | 1.00000 | 1.00000 |
| 10 | RaFFLE | 0.912925 | -0.014780 | 1.00000 | 1.00000 |
| 11 | Ridge | 0.917090 | -0.010615 | 1.00000 | 1.00000 |
| 12 | Lasso | 0.919650 | -0.008056 | 1.00000 | 1.00000 |
| 13 | KNN | 0.923270 | -0.004436 | 1.00000 | 1.00000 |
| 14 | HRT-Boost | 0.923720 | -0.003986 | 1.00000 | 1.00000 |
| 15 | logicDT propio (adaptado) | 0.926438 | -0.001268 | 1.00000 | 1.00000 |
| 16 | SVM lineal | 0.927706 | +0.000000 | — | — |
| 17 | Random Forest | 0.939635 | +0.011930 | 1.00000 | 1.00000 |
| 18 | GPR–XGBoost (OOF agrupado) | 0.959044 | +0.031338 | 1.00000 | 1.00000 |
| 19 | RIM (port E3) | 0.967213 | +0.039507 | 1.00000 | 1.00000 |
| 20 | XBART (GFR) | 0.967515 | +0.039809 | 1.00000 | 1.00000 |
| 21 | coPILOT | 0.970603 | +0.042897 | 1.00000 | 1.00000 |
| 22 | Dummy media | 1.256059 | +0.328353 | 0.00042 | 0.00110 |

## Contrastes pareados en test

ΔRMSE negativo favorece al candidato. Los intervalos son marginales; Holm corrige la familia acumulada.

| Candidato | Referencia | Δ RMSE | IC95% | p bilateral | p Holm global 55 |
|---|---|---:|---:|---:|---:|
| SVR RBF | SVM lineal | -0.035481 | [-0.065319, -0.008465] | 0.01018 | 0.49882 |
| SVR RBF | XGBoost | -0.014049 | [-0.040119, +0.011420] | 0.28846 | 1.00000 |
| SVR RBF | TabICLv2 | -0.005590 | [-0.025163, +0.014880] | 0.58678 | 1.00000 |
| SVR RBF | TabPFN 2.5 original | -0.006053 | [-0.028532, +0.016043] | 0.58798 | 1.00000 |
| SVR RBF | TabFM 1.0.0 (PyTorch CPU, 32 vistas) | -0.016500 | [-0.042323, +0.006273] | 0.18970 | 1.00000 |
| SVR RBF | TCR-XGBoost | -0.015470 | [-0.039416, +0.007889] | 0.20078 | 1.00000 |
| SVR RBF | Kernel Ridge RBF | -0.012656 | [-0.030976, +0.005320] | 0.16744 | 1.00000 |
| SVR RBF | CatBoost | -0.013445 | [-0.042478, +0.014058] | 0.35666 | 1.00000 |
| SVR RBF | TabPFN 2.5 fine-tuned | -0.009145 | [-0.029736, +0.011245] | 0.36668 | 1.00000 |
| SVR RBF | GPR–XGBoost (OOF agrupado) | -0.066819 | [-0.112349, -0.021320] | 0.00526 | 0.26826 |
| SVR RBF | GPR sola | -0.013614 | [-0.032596, +0.004760] | 0.14972 | 1.00000 |
| RaFFLE | SVM lineal | -0.014780 | [-0.046827, +0.015617] | 0.34570 | 1.00000 |
| RaFFLE | XGBoost | +0.006652 | [-0.016319, +0.028273] | 0.56558 | 1.00000 |
| RaFFLE | TabICLv2 | +0.015110 | [-0.005382, +0.035581] | 0.15480 | 1.00000 |
| RaFFLE | TabPFN 2.5 original | +0.014648 | [-0.011334, +0.039517] | 0.27180 | 1.00000 |
| RaFFLE | TabFM 1.0.0 (PyTorch CPU, 32 vistas) | +0.004200 | [-0.020528, +0.028605] | 0.73804 | 1.00000 |
| RaFFLE | TCR-XGBoost | +0.005230 | [-0.020460, +0.030441] | 0.69310 | 1.00000 |
| RaFFLE | Kernel Ridge RBF | +0.008044 | [-0.015458, +0.030889] | 0.50292 | 1.00000 |
| RaFFLE | CatBoost | +0.007256 | [-0.016497, +0.030084] | 0.55050 | 1.00000 |
| RaFFLE | TabPFN 2.5 fine-tuned | +0.011555 | [-0.012114, +0.035074] | 0.34768 | 1.00000 |
| RaFFLE | GPR–XGBoost (OOF agrupado) | -0.046119 | [-0.085265, -0.007605] | 0.02184 | 0.91728 |
| RaFFLE | GPR sola | +0.007087 | [-0.016126, +0.029359] | 0.55000 | 1.00000 |

## Contraste directo entre SVR RBF y RaFFLE

Análisis adicional exploratorio, no incluido en la familia Holm global de 55 contrastes.

| Métrica | SVR RBF menos RaFFLE | IC95% | p bilateral sin ajuste |
|---|---:|---:|---:|
| RMSE | -0.020700 | [-0.050974, +0.009548] | 0.18704 |
| R² | +0.024812 | [-0.011442, +0.062359] | 0.18704 |

## Métricas de validación agrupada

| Modelo | Métrica | Media 5 folds | SD | OOF agrupado |
|---|---|---:|---:|---:|
| SVR RBF | RMSE | 0.807765 | 0.037862 | 0.808659 |
| SVR RBF | MAE | 0.631816 | 0.035955 | 0.631823 |
| SVR RBF | MAPE (%) | 23.683225 | 1.999980 | 23.682814 |
| SVR RBF | R² | 0.474014 | 0.055552 | 0.476452 |
| RaFFLE | RMSE | 0.823022 | 0.034194 | 0.823737 |
| RaFFLE | MAE | 0.647831 | 0.030906 | 0.647841 |
| RaFFLE | MAPE (%) | 24.344758 | 1.969359 | 24.344677 |
| RaFFLE | R² | 0.453895 | 0.056446 | 0.456747 |

La prueba pareada permuta SSE agregado por estudiante (99.999 reasignaciones); el bootstrap también remuestrea estudiantes (10.000 réplicas). RMSE y R² comparten contraste y no se cuentan como pruebas independientes.

# Validación completa con R² — E3

22 modelos en el mismo test temporal 202530 (188 estudiantes). Mayor R² es mejor.
Delta=modelo−SVM lineal: positivo indica mejora. Permutación bilateral por estudiante y bootstrap pareado
(10.000 réplicas; semilla 42). Holm vs. SVM corrige 21 comparaciones; Holm global55 extiende la familia.

| Método | R² test | Δ R² vs. SVM | p bruto | Holm vs. SVM (21) | Holm global (55) |
|---|---:|---:|---:|---:|---:|
| SVR RBF | 0.471418 | +0.042876 | 0.01018 | 0.20360 | 0.49882 |
| TabICLv2 | 0.464774 | +0.036232 | 0.02624 | 0.49856 | 1.00000 |
| TabPFN 2.5 original | 0.464223 | +0.035680 | 0.06888 | 1.00000 | 1.00000 |
| TabPFN 2.5 fine-tuned | 0.460527 | +0.031984 | 0.08018 | 1.00000 | 1.00000 |
| Kernel Ridge RBF | 0.456316 | +0.027774 | 0.09620 | 1.00000 | 1.00000 |
| CatBoost | 0.455368 | +0.026826 | 0.21864 | 1.00000 | 1.00000 |
| XGBoost | 0.454641 | +0.026099 | 0.21102 | 1.00000 | 1.00000 |
| TCR-XGBoost | 0.452929 | +0.024387 | 0.24432 | 1.00000 | 1.00000 |
| TabFM 1.0.0 (PyTorch CPU, 32 vistas) | 0.451687 | +0.023144 | 0.21684 | 1.00000 | 1.00000 |
| RaFFLE | 0.446607 | +0.018064 | 0.34570 | 1.00000 | 1.00000 |
| Ridge | 0.441545 | +0.013003 | 0.31128 | 1.00000 | 1.00000 |
| Lasso | 0.438424 | +0.009881 | 0.15770 | 1.00000 | 1.00000 |
| KNN | 0.433995 | +0.005452 | 0.82690 | 1.00000 | 1.00000 |
| HRT-Boost | 0.433442 | +0.004900 | 0.78618 | 1.00000 | 1.00000 |
| logicDT propio (adaptado) | 0.430104 | +0.001561 | 0.94434 | 1.00000 | 1.00000 |
| SVM lineal | 0.428543 | +0.000000 | — | — | — |
| Random Forest | 0.413751 | -0.014791 | 0.51846 | 1.00000 | 1.00000 |
| GPR–XGBoost (OOF agrupado) | 0.389282 | -0.039260 | 0.20154 | 1.00000 | 1.00000 |
| RIM (port E3) | 0.378834 | -0.049709 | 0.16266 | 1.00000 | 1.00000 |
| XBART (GFR) | 0.378447 | -0.050096 | 0.12166 | 1.00000 | 1.00000 |
| coPILOT | 0.374472 | -0.054071 | 0.06606 | 1.00000 | 1.00000 |
| Dummy media | -0.047571 | -0.476113 | 0.00002 | 0.00042 | 0.00110 |

## Resultado e interpretación

SVR RBF obtiene el mayor R² puntual (0.471418), frente a 0.464774 de TabICLv2. La diferencia en R² es
+0.006644; IC95% [-0.014880; 0.025163], p=0.58678 y Holm55=1.00000. No hay evidencia de mejora significativa
tras la corrección. Ningún contraste de los nuevos candidatos sobrevive Holm global55. Dummy sigue siendo
significativamente peor que SVM tras corrección.

RMSE y R² comparten el contraste pareado de SSE sobre las mismas observaciones; coinciden en el ranking y
no son hipótesis independientes. El test ya se había consultado en trabajos anteriores: estos resultados son
exploratorios y no demuestran equivalencia.

## Validación cruzada

`validacion_cruzada_r2.csv` resume 22 modelos; `folds_r2.csv` contiene 105 evaluaciones externas.
TabPFN fine-tuned no tiene OOF independiente porque sus pesos finales vieron todo train.

[Panorama general por RMSE](../resumen_completo/resumen.md).

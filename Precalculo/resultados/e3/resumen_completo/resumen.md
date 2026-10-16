# Panorama completo de modelos — Entregable 3

18 métodos ordenados de menor a mayor RMSE. Mismo test temporal202530:188
estudiantes; datos reales sin aumento, mismas15 variables y objetivo
nota_primer_parcial. SVM lineal es la referencia. Delta=candidato−SVM:
negativo indica menor error; positivo indica deterioro.

Los p-valores son bilaterales por permutación pareada por estudiante99999,
semilla42. La tabla corrige con Holm los17 contrastes frente a SVM, incluido
Dummy. El CSV conserva además Holm global21: esos17 más4 contrastes nuevos
frente a XGBoost. Ambas familias están explícitamente identificadas.

| Método | RMSE test | Δ RMSE vs. SVM | p sin corrección | p Holm (17 vs. SVM) |
|---|---:|---:|---:|---:|
| TabICLv2 | 0.897815 | -0.029891 | 0.02624 | 0.41984 |
| TabPFN 2.5 original | 0.898277 | -0.029428 | 0.06888 | 0.99090 |
| TabPFN 2.5 fine-tuned | 0.901370 | -0.026336 | 0.08018 | 1.00000 |
| Kernel Ridge RBF | 0.904881 | -0.022825 | 0.09620 | 1.00000 |
| CatBoost | 0.905669 | -0.022036 | 0.21864 | 1.00000 |
| XGBoost | 0.906274 | -0.021432 | 0.21102 | 1.00000 |
| TCR-XGBoost | 0.907695 | -0.020010 | 0.24432 | 1.00000 |
| Ridge | 0.917090 | -0.010615 | 0.31128 | 1.00000 |
| Lasso | 0.919650 | -0.008056 | 0.15770 | 1.00000 |
| KNN | 0.923270 | -0.004436 | 0.82690 | 1.00000 |
| HRT-Boost | 0.923720 | -0.003986 | 0.78618 | 1.00000 |
| logicDT propio (adaptado) | 0.926438 | -0.001268 | 0.94434 | 1.00000 |
| SVM lineal | 0.927706 | +0.000000 | — | — |
| Random Forest | 0.939635 | +0.011930 | 0.51846 | 1.00000 |
| RIM (port E3) | 0.967213 | +0.039507 | 0.16266 | 1.00000 |
| XBART (GFR) | 0.967515 | +0.039809 | 0.12166 | 1.00000 |
| coPILOT | 0.970603 | +0.042897 | 0.06606 | 0.99090 |
| Dummy media | 1.256059 | +0.328353 | 0.00002 | 0.00034 |

## Interpretación

- TabICLv2 tiene el menor RMSE puntual y es la única mejora nominalmente
  significativa frente a SVM: p0.02624. Con Holm17, p0.41984; con Holm21,
  p0.47232. No conserva significancia tras corregir.
- Ningún método mejora significativamente frente a SVM después de Holm.
- Dummy es significativamente peor: p0.00002 y Holm17=0.00034
  (Holm21=0.00042). Revisar siempre la dirección del delta.
- Kernel Ridge y CatBoost mejoran puntualmente a XGBoost, sin significancia;
  sus contrastes frente a XGBoost están en ../scopus/contrastes_pareados.csv.
- RMSE y R² comparten el contraste sobre SSE en el mismo test; no se tratan
  como hipótesis independientes.

La inferencia sigue siendo exploratoria por el uso repetido del test y es
condicional a los modelos entrenados, sin variabilidad de reentrenamiento.
No rechazar H0 no demuestra equivalencia. Los resultados describen las
implementaciones evaluadas: logicDT/RIM adaptados, XBART GFR de stochtree,
KRR con solución exacta y coPILOT de los autores.

No se reentrena ni se modifica ningún modelo al generar este resumen.
Los archivos históricos de14 modelos y su Holm13 se preservan como historial.

[Validación completa con R²: test, CV e intervalos](../validacion_r2/resumen.md).

# Panorama completo de modelos — Entregable 3

22 modelos ordenados de menor a mayor RMSE en el test temporal 202530 (188 estudiantes).
Datos reales sin aumentación; 15 predictores y `nota_primer_parcial`. Delta=candidato−SVM lineal:
un valor negativo indica menor RMSE. La selección de parámetros se hizo dentro de train.

Los p-valores son bilaterales por permutación pareada de SSE por estudiante (99.999 reasignaciones).
Holm vs. SVM corrige 21 comparaciones. Holm global55 incorpora 17 resultados históricos vs. SVM,
4 contrastes Scopus vs. XGBoost, TabFM, GPR/ablación y las comparaciones de los dos nuevos candidatos.

| Rango | Método | RMSE test | Δ vs. SVM | p bruto | Holm vs. SVM (21) | Holm global (55) |
|---:|---|---:|---:|---:|---:|---:|
| 1 | SVR RBF | 0.892225 | -0.035481 | 0.01018 | 0.20360 | 0.49882 |
| 2 | TabICLv2 | 0.897815 | -0.029891 | 0.02624 | 0.49856 | 1.00000 |
| 3 | TabPFN 2.5 original | 0.898277 | -0.029428 | 0.06888 | 1.00000 | 1.00000 |
| 4 | TabPFN 2.5 fine-tuned | 0.901370 | -0.026336 | 0.08018 | 1.00000 | 1.00000 |
| 5 | Kernel Ridge RBF | 0.904881 | -0.022825 | 0.09620 | 1.00000 | 1.00000 |
| 6 | CatBoost | 0.905669 | -0.022036 | 0.21864 | 1.00000 | 1.00000 |
| 7 | XGBoost | 0.906274 | -0.021432 | 0.21102 | 1.00000 | 1.00000 |
| 8 | TCR-XGBoost | 0.907695 | -0.020010 | 0.24432 | 1.00000 | 1.00000 |
| 9 | TabFM 1.0.0 (PyTorch CPU, 32 vistas) | 0.908725 | -0.018980 | 0.21684 | 1.00000 | 1.00000 |
| 10 | RaFFLE | 0.912925 | -0.014780 | 0.34570 | 1.00000 | 1.00000 |
| 11 | Ridge | 0.917090 | -0.010615 | 0.31128 | 1.00000 | 1.00000 |
| 12 | Lasso | 0.919650 | -0.008056 | 0.15770 | 1.00000 | 1.00000 |
| 13 | KNN | 0.923270 | -0.004436 | 0.82690 | 1.00000 | 1.00000 |
| 14 | HRT-Boost | 0.923720 | -0.003986 | 0.78618 | 1.00000 | 1.00000 |
| 15 | logicDT propio (adaptado) | 0.926438 | -0.001268 | 0.94434 | 1.00000 | 1.00000 |
| 16 | SVM lineal | 0.927706 | +0.000000 | — | — | — |
| 17 | Random Forest | 0.939635 | +0.011930 | 0.51846 | 1.00000 | 1.00000 |
| 18 | GPR–XGBoost (OOF agrupado) | 0.959044 | +0.031338 | 0.20154 | 1.00000 | 1.00000 |
| 19 | RIM (port E3) | 0.967213 | +0.039507 | 0.16266 | 1.00000 | 1.00000 |
| 20 | XBART (GFR) | 0.967515 | +0.039809 | 0.12166 | 1.00000 | 1.00000 |
| 21 | coPILOT | 0.970603 | +0.042897 | 0.06606 | 1.00000 | 1.00000 |
| 22 | Dummy media | 1.256059 | +0.328353 | 0.00002 | 0.00042 | 0.00110 |

## Conclusión

SVR RBF tiene el menor RMSE puntual (0.892225), 0.005590 por debajo de TabICLv2 (0.897815).
La diferencia pareada frente a TabICLv2 tiene IC95% [-0.025163; 0.014880], p=0.58678 y Holm55=1.00000.
Ninguna mejora de los nuevos candidatos sobrevive la corrección global. El test se ha usado en iteraciones
anteriores y estos contrastes son exploratorios; RMSE y R² comparten el mismo SSE y no son evidencia independiente.

El contraste adicional SVR RBF menos RaFFLE es -0.020700 RMSE (IC95% [-0.050974; 0.009548],
p=0.18704 sin ajuste Holm); se presenta por separado de la familia global de 55.

[Validación completa con R²](../validacion_r2/resumen.md).

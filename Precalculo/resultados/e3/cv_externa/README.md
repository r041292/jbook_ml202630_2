# CV externa: comparación exploratoria frente al SVM

La comparación principal de procedimientos usa CV externa; el test temporal contrasta el periodo posterior.
Los rankings distintos responden a muestras y objetivos de generalización diferentes. No elegir familia por test.

## Método y alcance

Se reutilizan los cinco folds externos canónicos, sin entrenar ni usar métricas o predicciones de test en el cálculo. Se empareja el RMSE de cada modelo con SVM en el mismo fold.
Adaptación aproximada del test t corregido de Nadeau–Bengio: `SE²=(1/5+q)*s²`, `t=media(delta)/SE`, 4 grados de libertad, p bilateral.
`s²` usa ddof=1; `q` es la media de estudiantes_validación/estudiantes_fit (0.250000280). El RMSE sigue ponderando registros dentro de cada fold.
Holm corrige conjuntamente los **25 contrastes RMSE vs SVM**, incluido TR-KRR. SVM y TabPFN fine-tuned no entran en la familia. GPR sola fue retirada por trazabilidad del artefacto original; el híbrido GPR–XGBoost sigue siendo un experimento distinto.
Se conserva la misma familia en el tablero clásico; no se recalcula Holm sobre sus cinco modelos.

Hay una sola partición 1×5, no CV repetida: la corrección es una aproximación exploratoria, con poca potencia. Los folds no son observaciones independientes.
No se usa t ordinaria ni permutación IID de filas OOF. No se garantiza calibración exacta de p para GroupKFold. Los IC95% son marginales.
La familia y las grillas se han explorado sobre el mismo train; esto no evalúa de forma independiente un selector de familia anidado.

## Resultados

| Modelo | RMSE medio CV | Δ vs SVM | p bilateral corregida | p Holm25 | Conclusión |
|---|---:|---:|---:|---:|---|
| Kernel Ridge RBF | 0.801325 | -0.024815 | 0.164753 | 1.000000 | No significativa |
| TabPFN 2.5 original | 0.807118 | -0.019022 | 0.336587 | 1.000000 | No significativa |
| TabICLv2 | 0.807163 | -0.018978 | 0.233413 | 1.000000 | No significativa |
| SVR RBF | 0.807765 | -0.018375 | 0.309248 | 1.000000 | No significativa |
| Truncated Newton KRR RBF | 0.809646 | -0.016494 | 0.168940 | 1.000000 | No significativa |
| DenseWeight-XGBoost | 0.809715 | -0.016425 | 0.449661 | 1.000000 | No significativa |
| XGBoost ampliado (gbtree) | 0.811859 | -0.014281 | 0.512022 | 1.000000 | No significativa |
| TabFM 1.0.0 (PyTorch CPU, 32 vistas) | 0.812895 | -0.013246 | 0.371026 | 1.000000 | No significativa |
| DART-XGBoost | 0.813206 | -0.012935 | 0.541465 | 1.000000 | No significativa |
| XGBoost | 0.814264 | -0.011876 | 0.570766 | 1.000000 | No significativa |
| TCR-XGBoost | 0.814476 | -0.011664 | 0.563310 | 1.000000 | No significativa |
| CatBoost | 0.816276 | -0.009864 | 0.596941 | 1.000000 | No significativa |
| HRT-Boost | 0.817264 | -0.008877 | 0.304795 | 1.000000 | No significativa |
| RaFFLE | 0.823022 | -0.003119 | 0.865542 | 1.000000 | No significativa |
| Ridge | 0.824343 | -0.001797 | 0.800338 | 1.000000 | No significativa |
| SVM lineal | 0.826140 | 0.000000 | — | — | Referencia |
| Lasso | 0.828437 | 0.002297 | 0.804423 | 1.000000 | No significativa |
| Random Forest | 0.829569 | 0.003429 | 0.873928 | 1.000000 | No significativa |
| logicDT propio (adaptado) | 0.840809 | 0.014669 | 0.430332 | 1.000000 | No significativa |
| GPR–XGBoost (OOF agrupado) | 0.844127 | 0.017987 | 0.510959 | 1.000000 | No significativa |
| LinXGBoost (hojas completas E3) | 0.844282 | 0.018142 | 0.239733 | 1.000000 | No significativa |
| KNN | 0.855902 | 0.029762 | 0.253750 | 1.000000 | No significativa |
| coPILOT | 0.859075 | 0.032935 | 0.198399 | 1.000000 | No significativa |
| RIM (port E3) | 0.865105 | 0.038965 | 0.169252 | 1.000000 | No significativa |
| XBART (GFR) | 0.882018 | 0.055878 | 0.098449 | 1.000000 | No significativa |
| Dummy media | 1.118000 | 0.291860 | 0.001215 | 0.030374 | Deterioro significativo |
| TabPFN 2.5 fine-tuned | — | — | — | — | Sin OOF independiente |

## Conclusión

Kernel Ridge RBF lidera numéricamente CV: RMSE medio 0.801325; p bilateral 0.164753, Holm25 1.000000 frente al SVM.
0 mejoras frente al SVM sobreviven Holm25. Ausencia de significancia no prueba igualdad.
El mínimo de CV es un candidato para validación futura, no un ganador confirmado. SVR RBF conserva el mínimo descriptivo del test, sin reemplazar el criterio CV.

## Referencias

- https://doi.org/10.1023/A:1024068626366
- https://scikit-learn.org/stable/auto_examples/model_selection/plot_grid_search_stats.html
- https://www.jmlr.org/papers/v5/grandvalet04a.html

Reproducir: `venv/Scripts/python.exe significancia_cv_externa_e3.py`. No reentrena ni cambia predicciones.

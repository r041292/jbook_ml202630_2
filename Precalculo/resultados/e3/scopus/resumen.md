# Comparación Scopus E3

Informe histórico de la etapa de 18 modelos. El [panorama vigente de 26 modelos](../resumen_completo/resumen.md)
incluye los experimentos posteriores; los contrastes de esta etapa conservan
las referencias y familias de ajuste indicadas en sus archivos.

Mismo test temporal202530:188 estudiantes. Delta negativo de RMSE favorece al candidato.
Los resultados y contrastes son exploratorios por reutilización del test.

| Modelo | RMSE | MAE | MAPE (%) | R² | delta_RMSE_vs_SVM | delta_RMSE_vs_XGBoost |
| --- | --- | --- | --- | --- | --- | --- |
| Kernel Ridge RBF | 0.904881 | 0.727607 | 28.324540 | 0.456316 | -0.022825 | -0.001393 |
| CatBoost | 0.905669 | 0.731892 | 28.722883 | 0.455368 | -0.022036 | -0.000604 |
| XGBoost | 0.906274 | 0.728918 | 28.404775 | 0.454641 | -0.021432 | 0.000000 |
| SVM lineal | 0.927706 | 0.755443 | 29.664556 | 0.428543 | 0.000000 | 0.021432 |
| XBART (GFR) | 0.967515 | 0.794435 | 31.849667 | 0.378447 | 0.039809 | 0.061241 |
| coPILOT | 0.970603 | 0.793968 | 30.540858 | 0.374472 | 0.042897 | 0.064329 |

## Contrastes pareados RMSE

| Modelo | Referencia | metrica | diferencia_ajustado_menos_referencia | IC_2.5% | IC_97.5% | p_bilateral | p_Holm_global_21 | p_Holm_4_por_referencia |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| XBART (GFR) | SVM lineal | RMSE | 0.039809 | -0.010972 | 0.090111 | 0.121660 | 1.000000 | 0.288600 |
| XBART (GFR) | XGBoost | RMSE | 0.061241 | 0.008304 | 0.114403 | 0.023880 | 0.453720 | 0.071640 |
| CatBoost | SVM lineal | RMSE | -0.022036 | -0.056768 | 0.013772 | 0.218640 | 1.000000 | 0.288600 |
| CatBoost | XGBoost | RMSE | -0.000604 | -0.021020 | 0.020201 | 0.956700 | 1.000000 | 1.000000 |
| Kernel Ridge RBF | SVM lineal | RMSE | -0.022825 | -0.050050 | 0.003077 | 0.096200 | 1.000000 | 0.288600 |
| Kernel Ridge RBF | XGBoost | RMSE | -0.001393 | -0.024788 | 0.021450 | 0.904360 | 1.000000 | 1.000000 |
| coPILOT | SVM lineal | RMSE | 0.042897 | -0.004053 | 0.088527 | 0.066060 | 1.000000 | 0.264240 |
| coPILOT | XGBoost | RMSE | 0.064329 | 0.023059 | 0.106720 | 0.002820 | 0.056400 | 0.011280 |

## Todos los modelos probados

| Modelo | RMSE_test | delta_RMSE_vs_SVM | p_bilateral | p_Holm_global_21 |
| --- | --- | --- | --- | --- |
| TabICLv2 | 0.897815 | -0.029891 | 0.026240 | 0.472320 |
| TabPFN 2.5 original | 0.898277 | -0.029428 | 0.068880 | 1.000000 |
| TabPFN 2.5 fine-tuned | 0.901370 | -0.026336 | 0.080180 | 1.000000 |
| Kernel Ridge RBF | 0.904881 | -0.022825 | 0.096200 | 1.000000 |
| CatBoost | 0.905669 | -0.022036 | 0.218640 | 1.000000 |
| XGBoost | 0.906274 | -0.021432 | 0.211020 | 1.000000 |
| TCR-XGBoost | 0.907695 | -0.020010 | 0.244320 | 1.000000 |
| Ridge | 0.917090 | -0.010615 | 0.311280 | 1.000000 |
| Lasso | 0.919650 | -0.008056 | 0.157700 | 1.000000 |
| KNN | 0.923270 | -0.004436 | 0.826900 | 1.000000 |
| HRT-Boost | 0.923720 | -0.003986 | 0.786180 | 1.000000 |
| logicDT propio (adaptado) | 0.926438 | -0.001268 | 0.944340 | 1.000000 |
| SVM lineal | 0.927706 | 0.000000 | — | — |
| Random Forest | 0.939635 | 0.011930 | 0.518460 | 1.000000 |
| RIM (port E3) | 0.967213 | 0.039507 | 0.162660 | 1.000000 |
| XBART (GFR) | 0.967515 | 0.039809 | 0.121660 | 1.000000 |
| coPILOT | 0.970603 | 0.042897 | 0.066060 | 1.000000 |
| Dummy media | 1.256059 | 0.328353 | 0.000020 | 0.000420 |

Holm global21:13 pares históricos frente a SVM +4 nuevos frente a SVM +4 nuevos frente a XGBoost.
RMSE y R² comparten contraste SSE. Los IC95% son marginales; no simultáneos.
La interpretación exige revisar dirección y p corregido; no rechazar H0 no demuestra equivalencia.

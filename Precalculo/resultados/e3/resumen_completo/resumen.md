# Panorama actual de los 26 modelos — Entregable 3

Ranking descriptivo por RMSE en el mismo test temporal 202530 (188 estudiantes).
Se mantienen los datos reales sin aumentación, 15 predictores y objetivo `nota_primer_parcial`.
Train tiene 1309 filas de 1293 estudiantes. El preprocesamiento y la selección
de parámetros se realizan dentro de train con validación agrupada por estudiante.

Los 26 incluyen 22 modelos históricos, tres variantes XGBoost y LinXGBoost.
Las corridas LinXGBoost supersedidas y el diagnóstico preliminar de stacking quedan fuera.

| Puesto | Modelo | RMSE test | R² test | ΔRMSE vs XGBoost |
|---:|---|---:|---:|---:|
| 1 | SVR RBF | 0.892225 | 0.471418 | -0.014049 |
| 2 | TabICLv2 | 0.897815 | 0.464774 | -0.008459 |
| 3 | TabPFN 2.5 original | 0.898277 | 0.464223 | -0.007996 |
| 4 | LinXGBoost (hojas completas E3) | 0.899069 | 0.463278 | -0.007205 |
| 5 | TabPFN 2.5 fine-tuned | 0.901370 | 0.460527 | -0.004903 |
| 6 | Kernel Ridge RBF | 0.904881 | 0.456316 | -0.001393 |
| 7 | CatBoost | 0.905669 | 0.455368 | -0.000604 |
| 8 | XGBoost | 0.906274 | 0.454641 | +0.000000 |
| 9 | TCR-XGBoost | 0.907695 | 0.452929 | +0.001422 |
| 10 | TabFM 1.0.0 (PyTorch CPU, 32 vistas) | 0.908725 | 0.451687 | +0.002452 |
| 11 | XGBoost ampliado (gbtree) | 0.909207 | 0.451105 | +0.002933 |
| 12 | RaFFLE | 0.912925 | 0.446607 | +0.006652 |
| 13 | DenseWeight-XGBoost | 0.913037 | 0.446471 | +0.006763 |
| 14 | Ridge | 0.917090 | 0.441545 | +0.010817 |
| 15 | Lasso | 0.919650 | 0.438424 | +0.013376 |
| 16 | DART-XGBoost | 0.922167 | 0.435346 | +0.015893 |
| 17 | KNN | 0.923270 | 0.433995 | +0.016996 |
| 18 | HRT-Boost | 0.923720 | 0.433442 | +0.017446 |
| 19 | logicDT propio (adaptado) | 0.926438 | 0.430104 | +0.020164 |
| 20 | SVM lineal | 0.927706 | 0.428543 | +0.021432 |
| 21 | Random Forest | 0.939635 | 0.413751 | +0.033362 |
| 22 | GPR–XGBoost (OOF agrupado) | 0.959044 | 0.389282 | +0.052770 |
| 23 | RIM (port E3) | 0.967213 | 0.378834 | +0.060939 |
| 24 | XBART (GFR) | 0.967515 | 0.378447 | +0.061241 |
| 25 | coPILOT | 0.970603 | 0.374472 | +0.064329 |
| 26 | Dummy media | 1.256059 | -0.047571 | +0.349785 |

## Conclusiones y alcance

La comparación principal de procedimientos usa **CV externa**; este ranking
test es un contraste temporal complementario y no selecciona la familia.
Kernel Ridge RBF lidera CV entre los 26 candidatos activos (0.801325), con
pipeline original guardado y verificado. GPR sola se retiró del flujo activo;
el híbrido GPR–XGBoost se conserva. La inferencia CV se calcula por separado:
[método, resultados y límites](../cv_externa/README.md). Regenerar tras esta
consolidación con `python significancia_cv_externa_e3.py`; no confundir sus
p y Holm24 con los contrastes de test presentados aquí.

SVR RBF conserva el menor RMSE (0.892225) y el mayor R² (0.471418).
Su reducción puntual de RMSE frente a XGBoost es 0.014049 (1.55%). Frente a
TabICLv2, ΔRMSE=-0.005590, IC95% [-0.025163; 0.014880] y Holm55=1.000:
el primer puesto no acredita superioridad estadística sobre el segundo.

LinXGBoost queda cuarto (RMSE 0.899069). Frente a XGBoost, ΔRMSE=-0.007205,
IC95% [-0.036278; 0.021475], p=0.62662 y Holm7=1.000. Tampoco se distingue
significativamente de SVR RBF ni TabICLv2. Su RMSE OOF (0.845385) supera
al de XGBoost original (0.814822), por lo que no demuestra una mejora consistente.
La implementación independiente usa 67 columnas, 12 cuantiles para los cortes
y diferencias numéricas al puntuar candidatos descritas en [su reporte](../linxgboost/resumen.md).
Las corridas previas de RMSE 1.012583 y 1.017309 están supersedidas.

XGBoost original ocupa el puesto 8. La búsqueda ampliada, DenseWeight y DART
quedan en los puestos 11, 13 y 16, respectivamente: ninguna reduce su RMSE test
ni demuestra una mejora ajustada. RaFFLE queda 12 y TabFM 10.
Para la preferencia de evitar deep learning, SVR RBF es el líder puntual del test;
LinXGBoost es la modificación metodológica reciente mejor situada, sin mejora significativa demostrada.

## Interpretación de los CSV y la inferencia

Los contrastes de los reportes usan permutación pareada de SSE por estudiante
con 99.999 reasignaciones y bootstrap pareado con 10.000 réplicas, semilla 42.
Esta consolidación reutiliza esas pruebas sin calcular otras nuevas.

- [modelos.csv](modelos.csv) integra los 26, RMSE/R², deltas, descripciones,
  referencia inferencial y p ajustado de la familia correspondiente.
- [contrastes_actuales.csv](contrastes_actuales.csv) reúne los contrastes
  publicados para SVR/RaFFLE, variantes XGBoost y LinXGBoost, además de los cuatro
  contrastes históricos R² Scopus–XGBoost, con referencia,
  IC95%, familia, p bruto, p ajustado y fuente. No es una matriz de todos los pares.
- Holm55 conserva la familia histórica; Holm12 corrige los 12 pares de las
  variantes y Holm7 los siete pares de LinXGBoost. No se ha calculado un Holm
  global único para los 26. Los p ajustados de familias distintas no se comparan
  como una escala de rendimiento.
- En `modelos.csv`, `p_bilateral` y las columnas históricas Holm21/Holm55 son
  frente a SVM lineal. `Referencia_inferencia` identifica el comparador de
  `p_bilateral_referencia`, `p_Holm_familia_principal` y `significancia_ajustada`.
  Una celda vacía significa no disponible o no perteneciente a esa familia, nunca p=0.
- RMSE y R² comparten SSE sobre las mismas observaciones y no son evidencia independiente.
  Los IC95% son marginales, no intervalos simultáneos corregidos por multiplicidad.
- El test ya fue consultado en varias rondas. El ranking y los contrastes
  son exploratorios; no rechazar una diferencia no demuestra equivalencia.
  Un nuevo test temporal permitiría confirmar las mejoras sin esa reutilización.

[Validación R², CV y folds](../validacion_r2/resumen.md).
Los reportes de 18, 22 y 25 modelos conservan el contexto de cada etapa.
Las fuentes de 22 de este resumen se conservan en `historico_22/`.
Para regenerar la vista actual sin entrenar: `python actualizar_comparaciones_e3.py`.

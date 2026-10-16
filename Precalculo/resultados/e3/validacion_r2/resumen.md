# Validación actual con R² — 26 modelos E3

Los 26 modelos se comparan en el test temporal 202530 de 188 estudiantes.
SVR RBF tiene el mayor R² (0.471418), seguido de TabICLv2 (0.464774),
TabPFN 2.5 original (0.464223) y LinXGBoost (0.463278).
El ranking coincide con el de RMSE porque ambos dependen de SSE en el mismo test.

## Archivos vigentes

- `modelos_r2.csv`: 26 resultados test, deltas, referencia y familia de cada contraste.
  Los 22 históricos usan SVM lineal como referencia principal; los cuatro
  recientes usan XGBoost. `delta_R2` e IC95% de delta corresponden a `Referencia`.
  `delta_R2_vs_SVM` y `delta_R2_vs_XGBoost` son deltas descriptivos comunes a los 26.
  Los IC absolutos de R² de los cuatro recientes no están en los reportes agregados
  y quedan vacíos. Holm21/Holm55 no se extienden a modelos ajenos a esas familias.
- `validacion_cruzada_r2.csv`: 26 filas con R² medio, SD poblacional (ddof=0),
  OOF reunido y test. TabPFN fine-tuned conserva sus campos CV vacíos porque sus
  pesos finales vieron todo train y no ofrecen una nueva OOF independiente.
- `folds_r2.csv`: 125 evaluaciones externas de los 25 modelos con OOF independiente.
- `contrastes_r2_vs_xgboost.csv`: contrastes publicados frente a XGBoost en las
  fuentes consolidadas, con su familia e IC95% de delta. No contiene todos los pares posibles.

La media de R² por fold, el R² OOF reunido y el R² test son cantidades distintas.
Los modelos se seleccionaron por RMSE en train; no se reoptimizó por R² ni
se ajustaron modelos al consolidar estas tablas.

## Conclusión estadística

LinXGBoost tiene ΔR²=+0.008637 frente a XGBoost, con Holm7=1.000.
Su R² OOF 0.427817 es inferior al de XGBoost original (0.468442).
El primer puesto de SVR RBF es descriptivo; frente a TabICLv2, ΔR²=+0.006644,
IC95% [-0.014880; 0.025163], Holm55=1.000.
Las variantes XGBoost no mejoran el resultado temporal del modelo original.

Holm55, Holm12 y Holm7 son familias distintas; no existe un ajuste único global
para los 26. RMSE y R² comparten contraste SSE y no son dos pruebas independientes.
El uso repetido del test hace exploratoria la inferencia. La falta de significancia
no demuestra equivalencia entre modelos.

[Ranking, métricas y conclusiones de los 26 modelos](../resumen_completo/resumen.md).
Las fuentes históricas se conservan en `historico_22/`.
Regeneración desde agregados: `python actualizar_comparaciones_e3.py`.

---
title: Conclusiones y limitaciones
description: Hallazgos, evaluación de novedad, implementación propia y superioridad de cada modelo original, limitaciones, trabajo futuro y uso de herramientas de IA.
---

(sec-conclusiones)=
# Conclusiones y limitaciones

(sec-hallazgos)=
## Hallazgos

1. **La información disponible antes del primer parcial predice la nota de forma parcial.** El mejor modelo base reduce el error frente a predecir la media, pero el RMSE de test sigue cerca de 0,9 puntos en una escala de 0 a 5 y el R² de test ronda 0,45. Saber 11 global es la variable más influyente en todas las familias; el dominio inicial y final de ALEK, la asignatura y el programa completan la señal.
2. **La familia del modelo importa más que la estrategia de búsqueda.** Las cinco estrategias llegan a valores de RMSE interno separados por milésimas; TPE fue la más elegida y más barata que el Grid ({ref}`sec-busqueda`).
3. **El mejor benchmark es XGBoost** (0,8156 ± 0,0344), indistinguible del SVM lineal y de Ridge entre los modelos base ({ref}`sec-mejores-combinaciones`).
4. **Los tres modelos originales tienen menor error medio que los siete benchmarks**: KRR centrado 0,8010, GPR–XGBoost 0,8028 y TN-KRR 0,8056. La no linealidad suave de los kernels parece captar mejor la relación entre dominio, Saber 11 y nota que los árboles con unos 1.300 estudiantes.
5. **Los originales superan al SVM lineal de forma estadísticamente verificada.** Los tres lo superan en al menos tres pruebas con p ajustado por Holm; el TN-KRR y el KRR centrado, también con el ajuste de Holm sobre las 105 comparaciones. Frente a XGBoost, el KRR centrado y el GPR–XGBoost son superiores con Holm por prueba y con Benjamini–Hochberg ({ref}`sec-veredicto-r3`).
6. **El componente propio del híbrido no aporta en la ablación**: el GPR solo iguala al GPR–XGBoost ({ref}`sec-ablacion`).
7. **Todos los modelos comparten los mismos defectos de forma**: heterocedasticidad, regresión hacia la media, subestimación en 202530 y el mismo caso de mayor error. Son propiedades de la nota acotada y de la información disponible, no de una familia.

(sec-veredicto)=
## Veredicto R1, R2 y R3

La {numref}`tab-veredicto-final` resume la evaluación de cada original frente a las tres condiciones de la guía —novedad en la aplicación (R1), implementación algorítmica propia (R2) y superioridad estadísticamente verificada (R3)— con la evidencia de los capítulos de literatura, modelo original y validación estadística.

:::{table} Novedad, implementación propia y superioridad estadística de cada modelo original.
:label: tab-veredicto-final

| Modelo | R1 · novedad en la aplicación | R2 · implementación propia | R3 · superioridad estadísticamente verificada |
| --- | --- | --- | --- |
| KRR centrado | **Discutible.** Sin aplicaciones del KRR centrado al problema, pero KRR ya se usó como comparador para notas de Matemáticas de Ingeniería {cite:p}`ahmed2022` ({ref}`sec-declaraciones-novedad`). | **Discutible.** Composición de `KernelRidge`, `TransformedTargetRegressor` y `StandardScaler` sin clase propia ({ref}`sec-krr-r2`). | **Sí.** Frente al SVM lineal: permutación, BCa, DM-HLN y MCS con Holm por prueba; permutación, BCa y MCS también con Holm global. Frente a XGBoost: permutación, BCa y MCS con Holm por prueba y BH. |
| TN-KRR | **Sí.** Solo existen el artículo del método y una aplicación a porosidad ({ref}`sec-declaraciones-novedad`). | **Sí.** Clase propia con el solver CG truncado en NumPy, verificada contra la solución exacta; el algoritmo es publicado ({ref}`sec-tnkrr-r2`). | **Sí frente al SVM lineal**, su referencia: menor RMSE en los cinco folds; permutación (p Holm = 0,0030), BCa (0,0008), DM-HLN (0,0041) y MCS, las tres primeras también con Holm global (0,021; 0,005; 0,022); δ = −0,20, $d_z$ = −1,03 ({ref}`sec-tnkrr-svm`). Frente a XGBoost solo el MCS lo separa. |
| GPR–XGBoost | **Sí.** Sin aplicaciones educativas del híbrido; los cercanos son de ingeniería ({ref}`sec-trabajos-cercanos`). | **Condicionado.** Clase propia con regla de combinación OOF agrupada, pero la ablación no demuestra que esa regla mejore al GPR solo, como exige el Cuadro 1 para híbridos ({ref}`sec-ablacion`). | **Sí** con Holm por prueba y con BH, frente al SVM lineal (permutación, BCa y MCS) y frente a XGBoost (permutación, BCa y MCS). |
:::

En síntesis, el **TN-KRR** es el modelo con la contribución más clara en los tres frentes: es nuevo para el problema, su solver está implementado y verificado contra la solución exacta, y supera al SVM lineal con el criterio de multiplicidad más exigente. El **KRR centrado** obtiene el menor error y supera a ambos benchmarks, con la novedad y la implementación propia más acotadas. El **GPR–XGBoost** supera a ambos benchmarks con el ajuste por prueba, y su ventaja proviene del componente GPR.

(sec-limitaciones)=
## Limitaciones

- **Cinco folds dependientes y una sola partición.** Los entrenamientos comparten cerca del 75 % de los estudiantes; Wilcoxon no puede rechazar con cinco folds y la t corregida tiene 4 grados de libertad.
- **Un solo conjunto de datos.** La guía recomienda evaluar en al menos tres conjuntos adicionales de la misma tarea; este proyecto usa solo los datos del nivelatorio.
- **Efectos de contexto no modelados.** El error estándar por estudiante no incorpora efectos compartidos de sección, cohorte o periodo; el test 202530 muestra un cambio de nivel que todos los modelos subestiman.
- **Selección sobre la misma validación.** Los originales se eligieron entre varias alternativas evaluadas en la misma CV; ninguna corrección cubre esa selección.
- **Disponibilidad temporal de las predictoras.** El dominio final y las categorías finales deben conocerse antes del primer parcial; un uso operativo exige verificar esas fechas.

(sec-trabajo-futuro)=
## Trabajo futuro

1. Repetir la validación cruzada externa (por ejemplo, 5 × 5) para los diez modelos y recalcular la t corregida y Friedman con más bloques.
2. Completar la ablación: KRR exacto sin centrar y TN-KRR con objetivo centrado, con la misma búsqueda; GPR solo con cinco reinicios.
3. Medir el tiempo de entrenamiento al variar *n* y *p* para contrastar la complejidad $O(n^3)$ frente a $O(n^2p+Tn^2)$.
4. Validar en otros periodos y, si es posible, en datos de otras instituciones.
5. Modelar la nota como variable acotada (regresión beta u ordinal) o estimar la varianza condicional para atender la heterocedasticidad.
6. Calcular SHAP para TN-KRR y GPR–XGBoost y añadir al simulador un intervalo de predicción y la explicación local del caso ingresado.
7. Repetir el análisis cuando sea posible obtener más variables que ayuden a explicar el desempeño de los estudiantes, como la asistencia a clases.

(sec-declaracion-ia)=
## Uso de herramientas de IA

El proyecto fue asistido por herramientas de inteligencia artificial generativa (Claude, de Anthropic) en la escritura y revisión de código y en la redacción de este informe. El diseño, las decisiones metodológicas y la interpretación de los resultados son responsabilidad de los autores, Rubiel Velasquez y Valentina Figueroa.

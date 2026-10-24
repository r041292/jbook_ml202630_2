---
title: Revisión de literatura y novedad
description: Protocolo de búsqueda en tres bases, matriz de novedad, trabajos cercanos por familia algorítmica y declaración de novedad de cada modelo original.
---

(sec-literatura)=
# Revisión de literatura y novedad

La guía exige que la novedad en la aplicación (condición R1) se **demuestre** con una búsqueda documentada y no solo se declare (§5.2). Este capítulo registra el protocolo, la matriz de novedad con las búsquedas realmente ejecutadas, los trabajos más cercanos por familia algorítmica y una declaración de novedad para cada uno de los tres modelos originales: el **Kernel Ridge RBF con objetivo centrado** (KRR centrado), el **Truncated Newton KRR** (TN-KRR) y el **híbrido GPR–XGBoost**.

(sec-protocolo-busqueda)=
## Protocolo

- **Fecha de consulta:** 24 de octubre de 2026 (America/Bogota). Cada fila registra además la hora exacta en `analisis/salidas/busqueda_literatura.json`.
- **Bases consultadas (3):** OpenAlex (filtro sobre título y resumen), arXiv (todos los campos) y Semantic Scholar (búsqueda masiva con operadores booleanos). Se consultaron por sus API públicas con `analisis/busqueda_literatura.py`, que guarda el total que informa cada base y los 25 primeros registros por relevancia con título, año, DOI y resumen.
- **Búsqueda previa en Scopus:** una búsqueda exploratoria en Scopus (15 de octubre de 2026, `Precalculo/investigacion_scopus_no_deep_learning_e3.md`) sirvió para **elegir** las familias de modelos; la evaluación de novedad se hizo con las tres bases anteriores, que permiten registrar consultas reproducibles.
- **Cadenas (8):** combinan (i) la familia del modelo, (ii) el problema —nota de examen, rendimiento académico, *student performance*, pruebas de ubicación, precálculo, ALEKS— y (iii) sinónimos en inglés y en español. Tres cadenas son solo de familia (S2, S3, S6) para identificar trabajos cercanos de otras aplicaciones, como pide el Cuadro 1.
- **Revisión:** se leyó el título de todos los registros devueltos (hasta 25 por consulta, por relevancia) y el resumen de los que parecían pertinentes; los artículos de referencia de cada modelo se estudiaron en texto completo. Un registro es relevante si aplica la familia del modelo a la predicción de notas o rendimiento estudiantil, o si es un trabajo cercano de la misma familia. La valoración manual queda registrada en `analisis/matriz_novedad.py`.

(sec-matriz-novedad)=
## Matriz de novedad

La {numref}`tab-matriz-novedad` sigue el formato del Cuadro 2 de la guía. Los resultados son los totales que informó cada base el día de la consulta; pueden variar con el tiempo y se solapan entre bases.

```{include} analisis/tablas/matriz_novedad.md
```

Tres lecturas se desprenden de la matriz. Primera, las cadenas específicas de los dos modelos con mecanismo propio no devuelven ninguna aplicación educativa: TN-KRR solo aparece en sus dos artículos de origen (S3) y la combinación con gradiente conjugado y estudiantes no tiene resultados en ninguna base (S4); el híbrido GPR–XGBoost no tiene aplicaciones educativas (S5) y sí varias en ingeniería (S6). Segunda, **Kernel Ridge sí se ha usado en problemas educativos cercanos**: Ahmed et al. lo emplean como comparador para predecir la nota de Matemáticas de Ingeniería {cite:p}`ahmed2022` y Cherfane et al. lo incluyen en un ensamble que predice el puntaje MCAT {cite:p}`cherfane2026`. Tercera, los trabajos sobre pruebas de ubicación y precálculo (S7) usan métodos estadísticos o de minería de datos distintos de los propuestos.

(sec-trabajos-cercanos)=
## Trabajos cercanos por familia algorítmica

La {numref}`tab-trabajos-cercanos` compara la propuesta con los trabajos más cercanos de cada familia, independientemente de su aplicación, y precisa qué se conserva, qué cambia y por qué esos métodos no resuelven por sí solos la limitación que se aborda: predecir una nota acotada y heterogénea con unos 1.300 estudiantes, variables mixtas y validación agrupada por estudiante.

:::{table} Trabajos cercanos por familia: qué hacen y en qué se diferencia la propuesta.
:label: tab-trabajos-cercanos

| Trabajo | Familia | Qué hace | Qué conserva la propuesta | Qué cambia | Por qué no resuelve la limitación |
| --- | --- | --- | --- | --- | --- |
| {cite:t}`ahmed2022` | KRR (comparador) y MARS | Predice la nota ponderada de Matemáticas de Ingeniería con quizzes, tareas y exámenes; KRR es uno de los modelos de referencia frente a MARS. | Regresión de la nota de un curso de matemáticas con un kernel. | Predictoras previas al parcial (ALEK, Saber 11), objetivo centrado, partición temporal y GroupKFold anidado por estudiante. | Usa evaluaciones del propio curso (no anticipa el primer parcial), partición aleatoria 60/40 y no centra el objetivo. |
| {cite:t}`cherfane2026` | Ensamble con kernel ridge | Predice el MCAT de aspirantes de medicina con GPA y entrevistas. | Kernel ridge como regresor de un resultado académico. | Objetivo distinto (nota del primer parcial), modelo individual y validación por estudiante. | Otra tarea (puntaje de admisión) y otro fenómeno. |
| {cite:t}`elkhalil2019` | KRR centrado (teoría) | Analiza el riesgo de la «centered KRR» (KRR con desplazamiento) en alta dimensión. | La idea de no penalizar el nivel medio. | Implementación aplicada y evaluación empírica en datos educativos. | Resultado asintótico con datos gaussianos; sin aplicación. |
| {cite:t}`eckhard2014` | KRR con objetivo centrado | Estima espectros de reflectancia restando la media del entrenamiento y sumándola al predecir. | El procedimiento de centrado del objetivo. | Problema, kernel RBF sobre 67 columnas mixtas y búsqueda anidada de `alpha` y `gamma`. | Otra aplicación; no compara con y sin centrado. |
| {cite:t}`maalouf2014` | TN-KRR | Propone resolver el sistema dual de KRR con Newton truncado (gradiente conjugado lineal). | El solver y sus controles (200 iteraciones, norma 0,5, 25 sin mejora). | Implementación propia en NumPy, integrada al pipeline E3 y a cinco estrategias de búsqueda. | Lo compara con la solución cerrada de KRR, SVM y LS-SVM en seis conjuntos de datos generales; sin datos educativos. |
| {cite:t}`abdulla2022` | TN-KRR aplicado | Predice la porosidad de piezas de SS316L fabricadas por manufactura aditiva. | El mismo solver truncado. | Datos educativos con 15 predictoras mixtas y validación agrupada. | Cuatro predictores de fabricación y validación de 10 folds sin grupos. |
| {cite:t}`de2026` | Híbrido GPR → XGBoost | XGBoost corrige el residuo de un GPR para predecir el factor de reducción del pandeo de cascarones. | Las dos etapas y el kernel del GPR. | Meta-variables OOF agrupadas por estudiante y búsqueda anidada de XGBoost. | 582 datos de ingeniería con partición aleatoria 80/20; sin control de fuga por grupos. |
| {cite:t}`janani2025` | XGBoost + GPR del residuo | XGBoost modela la tendencia y un GPR los residuos para mantenimiento de turbinas. | Combinar boosting y proceso gaussiano. | Orden inverso (GPR primero) y construcción fuera del fold. | Serie de sensores SCADA; otra estructura de dependencia. |
| {cite:t}`hu2026` | XGBoost → GPR en cascada | XGBoost genera una variable aumentada que alimenta un GPR para la salud de baterías. | Cascada entre los dos modelos. | El GPR es la primera etapa y XGBoost aprende su residuo con la media y la DE del GPR. | Variables electroquímicas; el objetivo es un intervalo de confianza del GPR. |
| {cite:t}`rai2026` | Corrección de residuos con meta-modelo XGBoost | Un ensamble (GBRT, SVR, GPR) combinado por XGBoost corrige el residuo de un modelo físico de carbonatación. | Aprender el residuo de un modelo base con XGBoost. | Base estadística (GPR) en lugar de un modelo físico, y OOF por estudiante. | Datos experimentales de concreto. |
:::

En la aplicación, {cite:t}`madison2014` relacionan una prueba de ubicación de álgebra y cálculo con la nota del primer curso universitario de matemáticas mediante análisis de regresión, y {cite:t}`sen2012` predicen puntajes de una prueba de ubicación de secundaria con minería de datos (según el título; la base no ofrece el resumen). Ninguno usa información de una plataforma adaptativa como ALEK ni los modelos propuestos.

(sec-declaraciones-novedad)=
## Declaraciones de novedad

:::{admonition} KRR centrado
:class: note
Al mejor de nuestro conocimiento y según la búsqueda descrita, no se encontraron estudios que apliquen Kernel Ridge RBF con objetivo centrado dentro de cada ajuste a la predicción de la nota del primer parcial de asignaturas de matemáticas a partir de las mediciones de una plataforma adaptativa (ALEK) y del puntaje Saber 11. **Sin embargo, Kernel Ridge como familia sí se ha usado en un problema muy cercano**: {cite:t}`ahmed2022` lo emplean como comparador para predecir la nota de Matemáticas de Ingeniería, aunque con evaluaciones del propio curso, partición aleatoria y sin centrar el objetivo. El trabajo más cercano en el mecanismo de centrado es {cite:t}`eckhard2014`, en otra aplicación. Por eso la novedad de este modelo es la **más débil** de los tres: depende de la combinación de centrado, predictoras previas al parcial y protocolo agrupado, no de la familia.
:::

:::{admonition} TN-KRR
:class: note
Al mejor de nuestro conocimiento y según la búsqueda descrita, no se encontraron estudios que apliquen Kernel Ridge resuelto con Newton truncado (gradiente conjugado truncado) a la predicción de notas o del rendimiento estudiantil. Los únicos trabajos hallados son el que propone el método {cite:p}`maalouf2014` y su aplicación a la porosidad de piezas metálicas {cite:p}`abdulla2022`. La propuesta se diferencia en la aplicación, en la implementación propia del solver y en su integración a una validación anidada por estudiante.
:::

:::{admonition} GPR–XGBoost
:class: note
Al mejor de nuestro conocimiento y según la búsqueda descrita, no se encontraron estudios que apliquen un híbrido de proceso gaussiano y XGBoost a la predicción de notas o del rendimiento estudiantil. Los híbridos más cercanos están en ingeniería: el de referencia {cite:p}`de2026`, la combinación inversa de {cite:t}`janani2025`, la cascada de {cite:t}`hu2026` y la corrección de residuos de {cite:t}`rai2026`. La propuesta se diferencia por construir las meta-variables del GPR **fuera del fold y agrupadas por estudiante**, lo que evita que XGBoost aprenda de predicciones que ya vieron la nota.
:::

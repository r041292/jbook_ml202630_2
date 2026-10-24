---
title: Introducción
description: Resumen ejecutivo, problema, pregunta de investigación, objetivos y mapa del informe final del proyecto de Precálculo.
---

(sec-introduccion)=
# Introducción

Este informe técnico documenta el Tercer Entregable del proyecto de Machine Learning sobre el **nivelatorio de Precálculo** de la Universidad del Norte. Reúne en un solo libro los datos y su análisis exploratorio, los siete modelos de referencia, la revisión de literatura, los tres modelos originales, su validación estadística, el dashboard publicado y las condiciones de reproducción. Su estructura sigue el Cuadro 4 de la guía del entregable.

**Autores:** Rubiel Velasquez y Valentina Figueroa. **Institución:** Universidad del Norte. **Corte de resultados:** ejecuciones activas `20261018_102325_af643f83` (modelos base) y `20261020_153034_consolidada` (modelos originales); análisis nuevos del 24 de octubre de 2026.

:::{note} Productos publicados
- **Dashboard interactivo (Render):** <https://precalculo-dashboard.onrender.com/>
- **Repositorio:** <https://github.com/r041292/jbook_ml202630_2>
- **Informe previo del dashboard (se conserva sin cambios):** <https://r041292.github.io/jbook_ml202630_2/>
:::

(sec-resumen-ejecutivo)=
## Resumen ejecutivo

El proyecto predice la nota del primer parcial (escala 0–5) de la asignatura de matemáticas que cursa cada estudiante después del nivelatorio, a partir de las mediciones de la plataforma ALEK, del puntaje Saber 11 y de su información académica. Se usan solo datos reales: 1.309 registros de 1.293 estudiantes para entrenar (periodos 202310–202510) y 188 del periodo 202530 como prueba temporal, sin estudiantes compartidos.

Siete modelos base se optimizaron con cinco estrategias de búsqueda dentro de una validación anidada por estudiante. El mejor fue **XGBoost** (RMSE externo 0,8156 ± 0,0344). Se proponen tres modelos originales: **Kernel Ridge RBF con objetivo centrado** (0,8010 ± 0,0419), **Truncated Newton KRR** (0,8056 ± 0,0453) y un **híbrido GPR–XGBoost** con construcción fuera del fold por estudiante (0,8028 ± 0,0429). Los tres tienen menor error medio que los siete modelos base.

La validación estadística muestra que los tres originales superan al SVM lineal de referencia en la permutación por estudiante, el bootstrap BCa y el MCS, y el KRR centrado y el TN-KRR también en el contraste tipo Diebold–Mariano, con p ajustado por Holm; en el TN-KRR esa superioridad se mantiene incluso con el ajuste de Holm sobre las 105 comparaciones. Frente a XGBoost, el KRR centrado y el GPR–XGBoost superan el criterio de tres pruebas con p ajustado por Holm dentro de cada prueba, aunque esa ventaja no sobrevive al ajuste conjunto de las 105 comparaciones ni se reproduce en el test temporal. El {ref}`sec-conclusiones` resume la evaluación de novedad, implementación propia y superioridad de cada modelo.

(sec-problema)=
## Problema académico

El nivelatorio busca fortalecer los fundamentos matemáticos antes de cursar Álgebra y Trigonometría (MAT1011), Cálculo I ANEC (MAT1100), Cálculo I (MAT1101) y Matemáticas Fundamentales (MAT4190). La plataforma ALEK evalúa el dominio inicial de temas, propone un plan individual y mide el dominio final; el curso registra además los tiempos de trabajo. La institución dispone así de información del proceso antes del primer parcial y cabe preguntarse cuánto anticipa esa información el resultado de la primera evaluación.

La predicción es una herramienta de análisis académico, no una prueba causal. Que un modelo use el dominio final para predecir la nota no demuestra que aumentar el dominio cause una mejor nota: para esa conclusión haría falta un diseño de evaluación de intervención que este proyecto no contiene.

(sec-pregunta)=
## Pregunta de investigación y objetivos

**Pregunta de investigación.** ¿En qué medida las mediciones de ALEK, el puntaje Saber 11 y la información académica disponibles antes del primer parcial permiten predecir la nota de ese parcial, y puede un modelo original de la familia de métodos de kernel o un híbrido de proceso gaussiano reducir el error de los modelos de referencia de forma estadísticamente verificable?

**Objetivo general.** Construir, validar y publicar un sistema reproducible de predicción de la nota del primer parcial, con un modelo original comparado estadísticamente contra los mejores modelos de referencia.

**Objetivos específicos.**

1. Trabajar con datos reales, una partición temporal con purga de estudiantes y una validación anidada agrupada por estudiante, y describirlos con un ETL auditable y un EDA interpretado ({ref}`sec-datos`).
2. Seleccionar con criterio estadístico la mejor combinación de método de búsqueda e hiperparámetros para cada uno de los siete modelos base ({ref}`sec-benchmarks`).
3. Documentar la novedad de los modelos propuestos con una búsqueda sistemática de literatura ({ref}`sec-literatura`).
4. Formular, implementar y probar los tres modelos originales ({ref}`sec-modelo-original`).
5. Contrastar su superioridad con al menos tres pruebas de hipótesis, con ajuste por comparaciones múltiples y tamaños del efecto ({ref}`sec-validacion`).
6. Publicar los resultados en un dashboard en Render y en este informe ({ref}`sec-dashboard`, {ref}`sec-reproducibilidad`).

(sec-mapa)=
## Mapa del libro

La {numref}`tab-mapa` relaciona cada capítulo con el bloque de la guía (Figura 1 de la guía: B mejores combinaciones, C modelo original, D pruebas, E dashboard, F despliegue, G informe) que documenta.

:::{table} Capítulos del informe y bloque de la guía que cubren.
:label: tab-mapa

| N.° | Capítulo | Pregunta que responde | Bloque |
| ---: | --- | --- | --- |
| 0 | [Introducción](#sec-introduccion) | ¿Qué problema se resuelve y cómo está organizado el informe? | G |
| 1 | [Datos: ETL y EDA](#sec-datos) | ¿Qué datos se usan, cómo se depuran y qué muestran? | G |
| 2 | [Modelos benchmark](#sec-benchmarks) | ¿Cuál es la mejor combinación de cada modelo base? | B |
| 3 | [Revisión de literatura y novedad](#sec-literatura) | ¿Son nuevos los modelos propuestos para este problema? | C |
| 4 | [Modelo original](#sec-modelo-original) | ¿Cómo se formulan, implementan y prueban los tres originales? | C |
| 5 | [Validación estadística](#sec-validacion) | ¿Superan los originales a los benchmarks con significancia? | D |
| 6 | [Dashboard y despliegue](#sec-dashboard) | ¿Cómo se publica y se usa el producto? | E, F |
| 7 | [Conclusiones y limitaciones](#sec-conclusiones) | ¿Qué se concluye sobre la novedad, la implementación propia y la superioridad de los originales? | G |
| 8 | [Reproducibilidad y bibliografía](#sec-reproducibilidad) | ¿Cómo se reproduce cada cifra? | G |
:::

```{figure} images/01_introduccion.jpg
:alt: Página de introducción del dashboard con el contexto institucional, la fuente, las asignaturas y la pregunta de investigación.
:name: fig-intro-dashboard

Página «01 Introducción» del dashboard publicado, con el contexto del nivelatorio, la fuente de 1.527 registros y las cuatro asignaturas relacionadas.
```

La {numref}`fig-intro-dashboard` muestra cómo el dashboard presenta el mismo planteamiento a una persona no experta: las tarjetas describen la fuente original y la pregunta, mientras que el análisis y los modelos trabajan con las particiones preparadas que se describen en el {ref}`sec-datos`.

:::{important} Convenciones
Todas las métricas de error (RMSE, MAE) están en **puntos de nota** (escala 0–5). Salvo indicación, «media ± DE» se refiere a los cinco folds externos de la validación anidada con desviación estándar muestral (ddof = 1). El test temporal 202530 es descriptivo: nunca se usa para elegir modelos, métodos ni hiperparámetros.
:::

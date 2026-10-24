---
title: "Datos: ETL y EDA"
description: Fuente, reglas de negocio, exclusiones, partición temporal con purga, validación agrupada y análisis exploratorio interpretado del entrenamiento válido.
---

(sec-datos)=
# Datos: ETL y EDA

Este capítulo describe el recorrido completo de los datos, desde la fuente institucional hasta las particiones que usan todos los modelos, y el análisis exploratorio (EDA) que justifica cada decisión del pipeline. El orden es el del proceso: fuente, reglas de negocio, exclusiones, partición temporal y purga de estudiantes, validación agrupada, EDA univariado, bivariado, faltantes y atípicos, y conclusiones. Cada figura procede del dashboard publicado y va acompañada de su lectura.

Las cifras provienen de `Precalculo/resultados/e3/particion.json` y `eda.json` y de las vistas del dashboard sin filtros (programa y asignatura en «Todos»). El EDA usa **solo el entrenamiento válido**; el test temporal no participa en ninguna decisión.

(sec-etl)=
## Flujo ETL

La [](#fig-etl) resume el flujo. Su punto central es que la separación entre entrenamiento y prueba se hace **antes** de cualquier imputación, escalado o selección, y que la unidad de agrupación es el estudiante.

::::{figure}
:label: fig-etl

```{mermaid}
flowchart TD
  A["Datos_Brutos.csv<br/>1.527 registros · 1.506 estudiantes · 31 columnas"] --> B["Esquema estandarizado<br/>17 columnas; nota_final solo para auditoría"]
  B --> C["Excluir 30 filas sin nota del primer parcial"]
  C --> D["Reglas de negocio<br/>0 incumplimientos"]
  D --> E{"Periodo 202530"}
  E -- "sí" --> T["Test temporal<br/>188 registros · 188 estudiantes"]
  E -- "no" --> P["Purga de estudiantes del periodo reservado<br/>0 filas"]
  P --> R["Train válido<br/>1.309 registros · 1.293 estudiantes"]
  R --> G["GroupKFold 5 × 5 por estudiante<br/>búsqueda y OOF"]
  G --> M["Ajuste final en todo train"]
  M --> T
```

Flujo ETL del Entregable 3. Las transformaciones aprendidas (imputación, escalado, codificación) ocurren dentro de cada ajuste, nunca antes de separar.
::::

(sec-fuente)=
## Fuente y diccionario de variables

La fuente `Data/Datos_Brutos.csv` reúne seis periodos entre 2023 y 2025 (202310, 202330, 202410, 202430, 202510 y 202530) con **1.527 registros de 1.506 estudiantes** y 31 columnas. Se lee con separador `;`, coma decimal y codificación UTF-8 con BOM, y nunca se sobrescribe. Contiene nombres y correos, por lo que permanece fuera del repositorio público; el dashboard solo recibe datos derivados sin identificadores.

El archivo `cabeceras.csv` define el esquema estandarizado de 17 columnas. El modelo usa **15 predictoras** (ocho numéricas y siete categóricas); `nota_primer_parcial` es el objetivo y `nota_final` se conserva solo para auditar la fuga de información. La {numref}`tab-diccionario` resume su significado (tomado de `Precalculo/00_seleccion_base_datos.md`).

:::{table} Diccionario del esquema estandarizado.
:label: tab-diccionario

| Variable | Tipo | Significado | Uso |
| --- | --- | --- | --- |
| `Icfes_nuevo` | Numérica | Puntaje global en la prueba Saber 11. | Predictora |
| `Icfes_Matematicas` | Numérica | Puntaje del componente de Matemáticas de Saber 11. | Predictora |
| `Tiempo_empleado_en_la_verificación_de_conocimientos` | Numérica (h) | Tiempo de la verificación inicial (pretest) en ALEK. | Predictora |
| `Dominio_Inicial` | Numérica (temas) | Temas dominados en la prueba inicial de ALEK. | Predictora |
| `avance_precalculo_aleks` | Numérica (temas) | Diferencia entre los temas al final y al inicio. | Predictora |
| `Dominio_Final` | Numérica (temas) | Temas alcanzados en la prueba final de ALEK. | Predictora |
| `Tiempo_Total_Tiempo` | Numérica (h) | Tiempo total de trabajo en ALEK. | Predictora |
| `Tiempo_total_Aprendidos_hora` | Numérica (temas/h) | Tasa de temas aprendidos por hora. | Predictora |
| `Categoria_temas_inicial` | Categórica | Nivel de temas dominados al inicio. | Predictora |
| `Categoria_temas_final` | Categórica | Nivel de temas alcanzados al final. | Predictora |
| `programa_en_matricula` | Categórica | Programa académico matriculado. | Predictora |
| `division_en_matricula` | Categórica | División académica del programa. | Predictora |
| `Mat_Curso_Asignatura_Relacionada` | Categórica | Código de la asignatura relacionada. | Predictora |
| `avance_cuartiles` | Categórica | Cuartil de avance por asignatura y semestre. | Predictora |
| `cumplimiento_temas` | Categórica | Si el estudiante alcanzó la meta de temas. | Predictora |
| `nota_primer_parcial` | Numérica (0–5) | Nota del primer parcial de la asignatura relacionada. | **Objetivo** |
| `nota_final` | Numérica (0–5) | Nota final de la asignatura. Posterior al parcial. | Excluida (fuga) |
:::

```{figure} images/02_diccionario.jpg
:alt: Diccionario del proyecto en el dashboard con las 17 columnas del esquema estandarizado.
:name: fig-diccionario

Diccionario mostrado en «Variables y contexto»; `nota_final` se identifica como excluida del modelo.
```

La [](#fig-diccionario) confirma que el dashboard comunica la misma exclusión. El dominio inicial mide la entrada, el final la salida y el avance su diferencia exacta; las categorías de temas, cumplimiento y cuartiles resumen información que también está en las variables numéricas, de modo que **parte de la información es redundante** por construcción. La disponibilidad de las predictoras antes del primer parcial es un supuesto de este ejercicio que debe verificarse para cada horizonte de uso.

(sec-reglas)=
## Reglas de negocio y exclusiones

Se excluyen **30 filas sin nota del primer parcial**, porque no pueden supervisar el aprendizaje. Antes de imputar se aplican tres reglas: (1) dominio final ≥ dominio inicial; (2) si el tiempo total es cero, los dominios deben ser iguales; (3) si la tasa de temas aprendidos por hora es cero, los dominios deben ser iguales. Un registro que incumpla una regla es una inconsistencia, no un faltante, y se excluye en lugar de imputarse.

```{figure} images/03_reglas.jpg
:alt: Reglas de negocio y resultado de integridad con cero incumplimientos en train y test.
:name: fig-reglas

Reglas de negocio validadas y resultado de integridad en las dos particiones.
```

Como muestra la [](#fig-reglas), ninguna partición presenta incumplimientos y no se excluyen filas en esta etapa. Los valores extremos válidos se **conservan**: representan comportamiento real de la población y no se eliminan atípicos en ningún punto del flujo.

(sec-particion)=
## Partición temporal y purga de estudiantes

El periodo **202530** se reserva como prueba; el entrenamiento usa los cinco periodos anteriores. Todos los estudiantes que aparecen en el periodo reservado se purgan de train, aunque su nota de test falte; en esta fuente no hay solapamiento y la purga retira cero filas. La {numref}`tab-conteos` sigue cada etapa con las cifras de `particion.json`.

```{include} analisis/tablas/conteos.md
```

```{figure} images/11_split_test.jpg
:alt: Diagrama de separación temporal entre train y test por periodo académico.
:name: fig-split-test

Test por periodo académico: el periodo 202530 queda fuera del entrenamiento.
```

La [](#fig-split-test) muestra que la evaluación final mide dos cosas a la vez: generalización a **estudiantes nuevos** y a un **periodo posterior**. Esto la hace más exigente que una partición aleatoria y explica parte del deterioro de las métricas entre validación y test que se observa en los capítulos siguientes.

El código de `Precalculo/entregable3.py` que implementa la separación conserva las decisiones centrales y verifica que no haya estudiantes compartidos:

```{literalinclude} analisis/codigo/entregable3.py
:language: python
:start-at: def load_partitions
:end-before: def grouped_splits
:caption: Partición temporal, purga y reglas de negocio en `load_partitions()`.
:label: cod-particion
```

(sec-groupkfold)=
## Validación anidada agrupada por estudiante

Dentro de train, `GroupKFold` forma **cinco folds externos** con estudiantes completos: si una persona tiene más de un registro, todos quedan del mismo lado. En cada entrenamiento externo, los estudiantes se redistribuyen en **cinco folds internos** donde se ejecuta la búsqueda de hiperparámetros; el fold externo reservado no participa. Así cada predicción de validación es **fuera del fold (OOF)**: ningún registro de ese estudiante intervino en el ajuste ni en la selección.

```{figure} images/12_split_groupkfold.jpg
:alt: Esquema de cinco folds externos con bloques de entrenamiento y validación por estudiante.
:name: fig-groupkfold

GroupKFold por estudiante: cinco folds externos de 261–262 registros y validación fuera del fold.
```

La [](#fig-groupkfold) es la base de toda la comparación estadística del {ref}`sec-validacion`: los diez modelos comparados usan **los mismos cinco folds**, la misma semilla 42 y el mismo preprocesamiento por familia, de modo que sus errores son pareables fold a fold y estudiante a estudiante. Los entrenamientos de los folds comparten cerca del 75 % de los estudiantes; por eso los folds no son independientes, una limitación que condiciona la potencia de las pruebas.

```{figure} images/13_split_pipeline.jpg
:alt: Flujo del pipeline de modelos lineales con entradas, unión de transformaciones, regresión y salida.
:name: fig-pipeline

Pipeline compartido de los modelos lineales y de kernel: 15 predictoras, 67 columnas transformadas y salida en la escala original.
```

El pipeline de la [](#fig-pipeline) imputa con la mediana, aplica `log1p` a los tres tiempos, estandariza las numéricas, imputa la moda y codifica *one-hot* con una categoría de referencia. Todo se aprende dentro de cada ajuste; las categorías no vistas se codifican como ceros. Los modelos de árboles usan variantes sin escalado, descritas en el {ref}`sec-benchmarks`.

(sec-eda-univariado)=
## EDA univariado

La exploración usa **1.309 registros de 1.293 estudiantes**. Las ausencias no se rellenan para describir, y los contrastes se calculan sobre los datos disponibles; como 16 estudiantes tienen dos registros, esa dependencia no se corrige en estos contrastes exploratorios.

```{figure} images/04_eda_distribucion.jpg
:alt: Histograma de la nota del primer parcial y cajas por asignatura sobre el entrenamiento válido.
:name: fig-eda-distribucion

Distribución de la nota del primer parcial (puntos, 0–5) y cajas por asignatura.
```

**Lectura de la [](#fig-eda-distribucion).** La nota tiene media 3,499, mediana 3,700 y desviación 1,118; la mediana mayor que la media indica una cola hacia notas bajas. Shapiro–Wilk rechaza la normalidad marginal (W = 0,9458; p < 0,0001), lo que no obliga a transformar la escala. Kruskal–Wallis detecta diferencias entre asignaturas (H = 19,9458; gl = 3; p = 0,0002): la mayor mediana es 4,10 (MAT1011) y la menor 3,50 (MAT1101). *Insight:* la asignatura explica parte de la nota y debe entrar como predictora, pero el contraste no identifica qué pares difieren.

```{figure} images/07_eda_densidades.jpg
:alt: Rejilla de nueve distribuciones numéricas con histograma de densidad y curva KDE.
:name: fig-eda-densidades

Densidad de las ocho predictoras numéricas y de la nota (cada panel en sus unidades: puntos, temas u horas).
```

**Lectura de la [](#fig-eda-densidades).** Los tiempos son muy asimétricos (la mayor asimetría es la del tiempo de pretest, 1,779) y el dominio inicial se concentra cerca de cero. *Insight:* justifica `log1p` en los tiempos y explica por qué los modelos lineales sin transformación serían sensibles a la cola derecha.

```{figure} images/08_eda_categoricas.jpg
:alt: Rejilla de siete distribuciones categóricas del entrenamiento válido.
:name: fig-eda-categoricas

Proporción de cada categoría en las siete predictoras categóricas.
```

**Lectura de la [](#fig-eda-categoricas).** MAT1101 concentra cerca del 61 % de los registros y MAT4190 alrededor del 9 %; programa y división tienen representación desigual. *Insight:* los promedios globales están dominados por los grupos grandes, y las métricas por subgrupo pequeño del dashboard deben leerse como inestables.

(sec-eda-bivariado)=
## EDA bivariado

```{figure} images/05_eda_asociaciones.jpg
:alt: Dispersión de dominio final frente a nota y matriz de correlaciones de Spearman de las variables numéricas.
:name: fig-eda-asociaciones

Dominio final (temas) frente a la nota (puntos) y matriz de Spearman.
```

**Lectura de la [](#fig-eda-asociaciones).** El dominio final y la nota tienen una relación monótona positiva (ρ = 0,456) con dispersión considerable. Saber 11 global presenta la mayor asociación con la nota (ρ = 0,537), seguido del dominio inicial (0,497), el dominio final (0,456) y Saber 11 matemáticas (0,428). Hay redundancia fuerte entre predictoras: Saber 11 global y matemáticas (0,835), avance y dominio final (0,843), avance y tiempo de trabajo (0,795). *Insight:* ninguna variable sola determina la nota; la redundancia anticipa que los coeficientes y las atribuciones SHAP repartirán la señal entre variables correlacionadas.

```{figure} images/06_eda_dominio.jpg
:alt: Frecuencias de cumplimiento de la meta y cajas de nota por intervalos de dominio final.
:name: fig-eda-dominio

Cumplimiento de la meta y nota por intervalos de dominio final (cuartiles de train).
```

**Lectura de la [](#fig-eda-dominio).** El cumplimiento de la meta se reparte casi por mitades (49,3 % y 50,7 %; χ² = 0,2758; p = 0,5995), mientras que la mediana de la nota pasa de 2,60 en el intervalo de 0 a 16 temas a 4,50 en el de 49 a 143 temas (Kruskal–Wallis H = 261,8282; p < 0,0001). *Insight:* la relación entre dominio y nota es fuerte pero no lineal; motiva probar modelos con no linealidad (kernels, árboles).

(sec-eda-faltantes)=
## Faltantes y atípicos

```{figure} images/09_eda_faltantes.jpg
:alt: Porcentaje de ausencias por variable numérica en el entrenamiento válido.
:name: fig-eda-faltantes

Porcentaje de celdas faltantes por variable (sin imputación).
```

**Lectura de la [](#fig-eda-faltantes).** Hay 31 celdas faltantes: 21 en el tiempo de pretest (1,6 %), 5 en el tiempo de trabajo (0,4 %) y 5 en la tasa de temas por hora (0,4 %). La Q de Cochran rechaza que las variables falten con igual frecuencia (Q = 108,7382; gl = 7; p < 0,0001), pero no identifica el mecanismo. *Insight:* las ausencias se concentran en mediciones de tiempo y no deben confundirse con ceros de actividad; se imputan con la mediana aprendida en cada fold.

Los atípicos se describen pero se conservan: puntajes Saber 11 de 0, tiempos de más de 100 horas y dominios de hasta 143 temas son registros reales que cumplen las reglas de negocio.

(sec-eda-conclusiones)=
## Conclusiones del EDA y tratamientos

```{figure} images/10_eda_conclusion.jpg
:alt: Conclusión del EDA con media, mediana, asociaciones y tabla de tratamientos del pipeline.
:name: fig-eda-conclusion

Conclusiones del EDA y tratamientos que sustentan el pipeline del Entregable 3.
```

La [](#fig-eda-conclusion) traslada los hallazgos a decisiones: mantener la escala del objetivo, imputar dentro del pipeline, aplicar `log1p` a los tiempos, usar *one-hot* con referencia, conservar los extremos válidos y excluir `nota_final`. Dos hallazgos condicionan los capítulos siguientes: la **relación no lineal y heterogénea** entre dominio y nota, que motiva los modelos de kernel y el híbrido, y la **cola de notas bajas**, que anticipa errores mayores y heterocedasticidad en ese extremo.

:::{note} Uso de los filtros del dashboard
Al filtrar por programa o asignatura cambian el tamaño, las distribuciones y las asociaciones del subgrupo, pero no el modelo: los filtros evalúan el modelo global sobre un subconjunto. Con menos de 30 filas el dashboard señala lectura inestable.
:::

# Introducción, Selección de la base de datos y propósito del proyecto

Este documento presenta el primer entregable del Proyecto de Investigación de la asignatura [MACHINE LEARNING_202630_NRC 5646](https://cursos.uninorte.edu.co/d2l/home/177738).

**Objetivo del entregable:** establecer las bases del proyecto mediante (i) la selección de una base de datos pertinente; (ii) un análisis exploratorio de datos (EDA) riguroso y exhaustivo; y (iii) la implementación de un modelo base como referencia inicial, comparado con una línea base trivial.

## Contexto académico e institucional

En la Universidad del Norte, algunos programas de pregrado, como Ingeniería, Administración y otros afines, ofrecen este curso corto unas semanas antes del inicio de clases. Este curso es conocido internamente como **nivelatorio de precálculo**, su propósito es que los estudiantes alcancen una base mínima para afrontar las asignaturas de matemáticas de su primer semestre. Se busca así contribuir a un mejor desempeño en la primera evaluación parcial de esas asignaturas.

Los contenidos y la meta de aprendizaje del nivelatorio se definen de acuerdo con los requerimientos de cada programa. Como los temas siguen una secuencia, el avance registrado permite identificar hasta qué punto ha llegado cada estudiante respecto de la meta establecida.

El proceso se apoya en la plataforma ALEK, que evalúa los conocimientos al inicio, propone un plan de trabajo individual y realiza evaluaciones durante el curso para ajustar ese plan. Al finalizar, aplica una evaluación de salida. El curso también cuenta con un profesor y con estudiantes universitarios que participan como tutores. En conjunto, los registros de ALEK permiten describir el nivel de entrada y de salida, los temas aprendidos y el tiempo de trabajo en la plataforma, entre otros aspectos del proceso.

Las evaluaciones de entrada y salida registran el dominio de los estudiantes en distintos temas de cálculo. En conjunto, el nivelatorio busca proporcionar fundamentos matemáticos que apoyen el desempeño y la aprobación de las asignaturas cursadas durante el primer semestre.

Las asignaturas relacionadas con este curso son las siguientes:

| Código | Asignatura |
| --- | --- |
| `MAT1011` | Álgebra y Trigonometría |
| `MAT1100` | Cálculo I (ANEC) |
| `MAT1101` | Cálculo I |
| `MAT4190` | Matemáticas Fundamentales |

La base de datos que se usará en este proyecto registra información del **nivelatorio de precálculo** durante los periodos académicos comprendidos entre 2023 y 2025.

## Propósito del proyecto

El objetivo es explorar la información académica generada durante el curso de precálculo y construir una primera aproximación para predecir el resultado de cada estudiante en el primer parcial de la asignatura relacionada. La variable objetivo es `nota_primer_parcial`, y se consideran como posibles predictores los resultados de las evaluaciones de entrada y salida, el avance en la plataforma ALEK, el tiempo de trabajo, los resultados de la prueba Saber 11, el programa académico, la división y la asignatura relacionada.

La predicción debe entenderse como una herramienta de análisis académico. Antes de utilizarla en un escenario operativo, es necesario verificar que cada variable esté disponible en el momento en que se desea realizar la predicción y que no incorpore información posterior al primer parcial.

## Estado original de la base de datos

La fuente original utilizada para el proceso de preparación es `Data/Datos_Brutos.csv`. El archivo conserva el registro detallado proveniente del curso, con identificadores anonimizados, información académica, resultados de la plataforma ALEK, asignatura relacionada y calificaciones.

| Característica | Estado observado |
| --- | --- |
| Periodos | `202310`, `202330`, `202410`, `202430`, `202510` y `202530` |
| Registros originales | 1.527 |
| Columnas originales | 31 |
| Estudiantes identificados | 1.506 |
| Filas duplicadas completas | 0 |
| Registros con `nota primer parcial` disponible | 1.497 |
| Registros sin `nota primer parcial` | 30 |
| Separador | `; ` |
| Codificación | UTF-8 con BOM |

Con esta cantidad de observaciones no se alcanza el mínimo de 20.000 registros solicitado para el proyecto. Además, para el aprendizaje supervisado solo se pueden utilizar las filas que tienen valor en la variable objetivo. Por esta razón, el conjunto original requiere un proceso controlado de aumentación de datos.

## Esquema estandarizado para el modelado

El archivo `cabeceras.csv` se utiliza como referencia del formato final y de los nombres estandarizados de las columnas. No contiene registros de estudiantes; su función en este flujo es definir el esquema de salida que utilizarán los notebooks de análisis y modelado.

En particular, los nombres de las columnas objetivo se normalizan de la siguiente manera:

| Fuente original | Esquema estandarizado |
| --- | --- |
| `nota primer parcial` | `nota_primer_parcial` |
| `nota final` | `nota_final` |

El esquema final contiene 17 columnas:

`Icfes_nuevo`, `Icfes_Matematicas`, `Tiempo_empleado_en_la_verificación_de_conocimientos`, `Dominio_Inicial`, `Categoria_temas_inicial`, `avance_precalculo_aleks`, `Dominio_Final`, `Categoria_temas_final`, `Tiempo_Total_Tiempo`, `Tiempo_total_Aprendidos_hora`, `programa_en_matricula`, `division_en_matricula`, `Mat_Curso_Asignatura_Relacionada`, `avance_cuartiles`, `cumplimiento_temas`, `nota_primer_parcial` y `nota_final`.

La columna `nota_final` se conserva en los archivos preparados para facilitar la revisión de resultados, pero no debe utilizarse como predictor de `nota_primer_parcial` debido al riesgo de fuga de información.

## Descripción de las variables del esquema final

La siguiente tabla resume el significado operativo de las 17 columnas que se conservan en el esquema estandarizado.

| Variable | Explicación |
| --- | --- |
| `Icfes_nuevo` | Puntaje global del estudiante en la prueba Saber 11 reportado por la institución. |
| `Icfes_Matematicas` | Puntaje del estudiante en el componente de Matemáticas de la prueba Saber 11. |
| `Tiempo_empleado_en_la_verificación_de_conocimientos` | Tiempo empleado por el estudiante, expresado en horas, en la verificación inicial de conocimientos de la plataforma ALEK. |
| `Dominio_Inicial` | Cantidad de temas dominados por el estudiante como conclusión de una prueba inicial (pretest) realizada en la plataforma ALEK. |
| `Categoria_temas_inicial` | Categoría descriptiva que resume el nivel o la cantidad de temas dominados al inicio. |
| `avance_precalculo_aleks` | Diferencia entre la cantidad de temas al inicio y la cantidad de temas al final del proceso en la plataforma ALEK. |
| `Dominio_Final` | Cantidad de temas alcanzados luego del curso nivelatorio, verificados mediante una prueba final (posttest) en la plataforma ALEK. |
| `Categoria_temas_final` | Categoría descriptiva del nivel o la cantidad de temas alcanzados en la medición final. |
| `Tiempo_Total_Tiempo` | Tiempo total de trabajo del estudiante en la plataforma ALEK, expresado en horas. |
| `Tiempo_total_Aprendidos_hora` | Tasa de temas aprendidos por hora, calculada o registrada para el estudiante. |
| `programa_en_matricula` | Programa académico en el que estaba matriculado el estudiante. |
| `division_en_matricula` | División académica a la que corresponde el programa matriculado por el estudiante. |
| `Mat_Curso_Asignatura_Relacionada` | Código de la asignatura relacionada con el curso de precálculo. |
| `avance_cuartiles` | Categoría por cuartiles generada por asignatura y por semestre, relativa a la distribución del grupo correspondiente. |
| `cumplimiento_temas` | Indicador categórico de si el estudiante alcanzó la meta de temas definida para el curso. |
| `nota_primer_parcial` | Calificación obtenida por el estudiante en el primer parcial de la asignatura relacionada. Es la variable objetivo del modelado. |
| `nota_final` | Calificación final de la asignatura relacionada. Se conserva para auditoría, pero no debe utilizarse como predictor de `nota_primer_parcial` por ser un resultado posterior y posible fuente de fuga. |

## Necesidad y estrategia de aumentación

El conjunto original contiene 1.527 registros, por debajo del mínimo de 20.000 observaciones establecido para el proyecto. Por esta razón, se requiere aplicar un proceso de aumentación de datos antes del análisis y el modelado.

Para seleccionar la estrategia, se compararon dos alternativas: **alternativa 1, perturbaciones locales controladas**, y **alternativa 2, interpolación entre vecinos adaptada de SMOTE para regresión**. La comparación utilizó únicamente entrenamiento y cinco semillas, evaluando cuánto se conservaban las distribuciones y las asociaciones de los datos originales. **La alternativa 1 fue la mejor aproximación en las cinco pruebas**, porque produjo menores diferencias en las variables numéricas, la nota del primer parcial y sus asociaciones. Por ello, se eligió para generar los archivos finales.

El flujo genera 30.000 registros: 24.000 para entrenamiento y 6.000 para prueba, con el esquema de 17 columnas. Primero se separan los estudiantes y después se aumenta cada partición por separado; se excluyen las filas sin objetivo y se verifican rangos, reglas de negocio, avance, duplicados y separación entre particiones. Las variantes sintéticas no representan nuevos estudiantes; también se conserva el test original para evaluar los modelos. La comparación y sus conclusiones se detallan en el notebook [Generación reproducible del dataset aumentado](precalculo_generar_split_augmented_2.ipynb).

## EDA: análisis exploratorio de datos

El notebook [EDA comprehensivo](precalculo_eda_comprehensivo.ipynb) utiliza los
datos de la **alternativa 1, perturbación local**, seleccionada en aumentación.
Caracteriza calidad, distribuciones, asociaciones, redundancias, grupos y riesgos
de fuga usando exclusivamente entrenamiento. El test se mantiene reservado.

Conclusiones principales:

- Las tres reglas de negocio se cumplen: **0 inconsistencias** y
  **24,000 registros válidos** para el EDA.
- La nota tiene media 3.519, mediana 3.700
  y asimetría -0.439. Se mantiene su escala original.
- Los outliers válidos se conservan. Los 548 faltantes observados
  se concentran en variables de tiempo; la imputación se aprende dentro del pipeline.
- `nota_final` queda excluida de las entradas y correlaciones por temporalidad.
  Avance, dominio final y dominio inicial cumplen una identidad matemática exacta,
  por lo que se revisa su redundancia antes de interpretar coeficientes.

## Modelo lineal base

El notebook [Regresión lineal base](precalculo_regresion_lineal.ipynb) usa la misma
fuente de **perturbación local** del EDA y del dashboard. Compara DummyRegressor
(nota media) con LinearSVR en un pipeline que imputa dentro de cada fold, aplica
log1p a tres variables de tiempo, escala numéricas y codifica categorías.
El test se reservó por estudiante antes de la aumentación; no se vuelve a dividir.

La ejecución vigente conserva **24,000 filas de train** y
**6,000 filas de test**, sin exclusiones por reglas de negocio:

| Modelo | RMSE | MAPE | R² | MAE |
| --- | ---: | ---: | ---: | ---: |
| Dummy media | 1.1532 | 39.7168 % | -0.0006 | 0.9935 |
| SVM lineal | 0.9083 | 27.7552 % | 0.3792 | 0.7314 |

El intervalo bootstrap del 95 % del SVM es
RMSE [0.8925; 0.9241],
MAPE [26.8587 %; 28.6862 %] y
R² [0.3575; 0.4008].
Los remuestreos son por filas del test aumentado: las variantes no equivalen a
nuevos estudiantes independientes. LinearSVR no acota las notas predichas.

Conclusiones principales:

- El SVM reduce RMSE en 21.23 %
  y MAPE en 30.12 % frente a Dummy.
  Su R² de 0.3792 y MAE de 0.7314 puntos indican capacidad parcial.
- Validación cruzada: RMSE medio 0.7974 y R² 0.5064.
  El desempeño superior al test aconseja cautela: sin identificador persistente,
  los folds no pueden agruparse por estudiante y variantes cercanas pueden
  repartirse entre folds. Se recomienda evaluar también el test original conservado.
- Normalidad de residuos: p = 1.47e-11; Breusch–Pagan:
  p = 2.05e-30; Spearman entre predicción y error absoluto:
  -0.1535. El modelo sirve como referencia
  predictiva, no como inferencia causal ni modelo final de alta precisión.

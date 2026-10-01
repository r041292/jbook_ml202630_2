---
title: Interpretaciones de resultados
description: Recorrido visual, página por página, del dashboard de Precálculo con lectura de cada resultado.
---

# Interpretaciones de resultados

El recorrido sigue las páginas del dashboard: Introducción, EDA (Variables y contexto, Aumentación de datos y Exploración interactiva) y Modelos lineales. Cada captura proviene del tablero local que utiliza los mismos datos preparados para Render. Se documenta la vista **General**, con programa y asignatura en **Todos**, test como partición de evaluación y nota del primer parcial como variable de comparación de aumentación. El simulador es la única captura con una entrada modificada, indicada en su explicación.

Las cifras tienen cuatro decimales cuando interesa comparar métricas. Los gráficos del tablero pueden redondear a dos o tres decimales. Todas las distribuciones corresponden a filas de la muestra aumentada; sus conteos no deben leerse como alumnos independientes. Una asociación o diferencia descriptiva no demuestra causalidad.

## Página 1 · Introducción

La pantalla inicial sitúa el nivelatorio en la Universidad del Norte, identifica la fuente de 1.527 registros de 2023–2025 y presenta cuatro asignaturas. Esas tarjetas describen la fuente original, mientras que EDA y modelos trabajan con las particiones preparadas. Los tamaños no se contradicen: corresponden a etapas distintas del proceso.

La pregunta es predictiva: relacionar mediciones académicas disponibles con la nota del primer parcial. La plataforma ALEK aporta dominio de temas, avance y tiempos; Saber 11 e información institucional amplían el contexto. La introducción no presenta una prueba de que asistir al nivelatorio cause un aumento de nota. Para esa conclusión haría falta un diseño de evaluación de intervención que este proyecto no contiene.


```{figure} images/01_introduccion.jpg
:alt: Página de Introducción: contexto, fuente original, asignaturas y pregunta de investigación.
:name: fig-01-introduccion

Página de Introducción: contexto, fuente original, asignaturas y pregunta de investigación.
```


## Página 2 · EDA: Variables y contexto

### Diccionario y temporalidad

El diccionario distingue las ocho predictoras numéricas, siete categóricas y el objetivo. El dominio inicial mide entrada; el final mide salida; el avance es su diferencia. Las categorías de temas, cumplimiento y cuartiles resumen aspectos que también aparecen en las variables numéricas, por lo que parte de la información es redundante.

El esquema conserva `nota_final` para auditar fuga, pero el tablero no la incorpora en matrices de correlación ni datos de predicción. La calificación final ocurre después del primer parcial y usarla produciría un pronóstico con información futura. La disponibilidad de las otras variables antes del parcial es un supuesto de este ejercicio que debe verificarse para cada horizonte de uso.


```{figure} images/02_diccionario.jpg
:alt: Diccionario mostrado en Variables y contexto; nota_final se identifica como variable excluida del modelo.
:name: fig-02-diccionario

Diccionario mostrado en Variables y contexto; nota_final se identifica como variable excluida del modelo.
```


### Necesidad de aumentar y reglas de negocio

El requisito académico solicita al menos 20.000 registros, mientras que la fuente tiene 1.497 filas con nota disponible. Se construyen 30.000 filas de trabajo a partir de esas observaciones, sin afirmar que la generación crea información equivalente a observar más estudiantes.

Tres reglas se aplican antes de imputar: dominio final ≥ inicial; tiempo total cero implica dominios iguales; tasa de temas aprendidos por hora cero implica dominios iguales. En train y test seleccionados no hay incumplimientos y no se excluyen filas en esta etapa. Un valor extremo válido se conserva; una inconsistencia se rechaza. Tampoco se reemplaza un cero real por un faltante.


```{figure} images/03_reglas.jpg
:alt: Reglas de negocio y resultado de integridad: cero incumplimientos en las particiones seleccionadas.
:name: fig-03-reglas

Reglas de negocio y resultado de integridad: cero incumplimientos en las particiones seleccionadas.
```


## Página 2 · EDA: Aumentación de datos

### Separación externa antes de generar variantes

Tras excluir 30 filas sin objetivo se dividen los estudiantes, dejando 1.196 filas de 1.184 personas en train y 301 filas de 297 personas en test, sin IDs compartidos. Cada partición genera sus variantes por separado: 24.000 y 6.000 filas finales. Esta secuencia protege la separación externa; aumentar primero y dividir después podría colocar variantes de un mismo original en ambos lados.


```{figure} images/09_separacion.jpg
:alt: Separación por estudiante previa a la aumentación, con los tamaños originales y aumentados.
:name: fig-09-separacion

Separación por estudiante previa a la aumentación, con los tamaños originales y aumentados.
```


### Dos técnicas y criterio de selección

**Técnica 1 · Perturbación local controlada.** Se selecciona un registro original de la partición y se construye una variante cercana, conservando sus categorías y aplicando cambios pequeños a determinadas mediciones numéricas. Los puntajes Saber 11 reciben ruido aditivo correlacionado, los tiempos se modifican mediante factores multiplicativos y la nota del primer parcial recibe una variación acotada. Los valores se restringen a sus rangos permitidos y el avance se recalcula como dominio final menos dominio inicial. Antes de incorporar la variante se comprueban las reglas de negocio y se rechazan los duplicados. El propósito es ampliar la muestra alrededor de los perfiles observados conservando su estructura, sin introducir combinaciones categóricas nuevas. La intensidad de las variaciones se define con información de la partición que se está aumentando; los originales se mantienen intactos.

**Técnica 2 · Interpolación entre vecinos compatibles para regresión.** Se selecciona un registro original y se buscan hasta cinco vecinos cercanos en el espacio de predictoras numéricas estandarizadas. La búsqueda se restringe a registros con las mismas categorías, patrón de faltantes y estados cero de las mediciones de actividad. Después se elige uno de esos vecinos y se genera un punto intermedio: para cada valor numérico disponible en ambos registros se aplica la combinación $x_{nuevo}=x_a+\lambda(x_b-x_a)$, con un peso aleatorio $\lambda$ entre cero y uno; la nota también se interpola. El avance se recalcula y la nueva fila debe superar las mismas comprobaciones de coherencia y duplicados. Cuando el estrato no tiene vecinos, se recurre a la perturbación local, lo que ocurre en el **7,80 %** de las filas nuevas de train de la semilla ilustrada. Se trata de una adaptación híbrida para este proyecto, no de una implementación estándar de SMOTER o SMOGN ni de un procedimiento de balanceo de notas raras.

La elección compara la **fidelidad de los sintéticos a los originales de train**, no el rendimiento predictivo en test. Se evalúan distribuciones numéricas, proporciones categóricas, faltantes, asociaciones de Spearman y combinaciones de categorías. Cada técnica se repite con cinco semillas sobre la misma partición original; el puntaje resume seis distancias y favorece valores menores. Las dos alternativas conservan los originales, de modo que su comparación debe centrarse en las filas nuevas.

Solo se comparan **22.804 filas sintéticas nuevas por técnica** frente a **1.196 originales de train**. Si se incluyeran los originales en ambas alternativas, su presencia reduciría artificialmente las diferencias visuales. Las curvas usan la primera semilla de las cinco comparadas; el puntaje global resume las cinco.

### Densidades y proporciones acumuladas

Las densidades tienen área uno. Una curva más alta significa concentración por unidad de nota, no más filas. Para el objetivo, la perturbación conserva aproximadamente la forma y la dispersión original; la interpolación comprime la dispersión. La suavización KDE puede extenderse más allá de los límites observados, de modo que se interpreta junto con la acumulada y las estadísticas.


```{figure} images/10_aumentacion_densidad.jpg
:alt: Densidades de la nota: originales de train, sintéticos por perturbación e interpolación.
:name: fig-10-aumentacion-densidad

Densidades de la nota: originales de train, sintéticos por perturbación e interpolación.
```


```{figure} images/11_aumentacion_acumulada.jpg
:alt: Proporciones acumuladas de la nota; la separación vertical frente al original permite entender KS.
:name: fig-11-aumentacion-acumulada

Proporciones acumuladas de la nota; la separación vertical frente al original permite entender KS.
```


La acumulada expresa la fracción de notas menores o iguales a un umbral. El máximo alejamiento vertical es la distancia KS; no es un p-valor. La proximidad de la perturbación a los originales indica fidelidad de esta distribución. La comparación de una sola variable no basta para seleccionar una técnica, por eso el criterio incluye seis distancias.


```{figure} images/12_aumentacion_resumen.jpg
:alt: Media, mediana y desviación de la nota en originales y sintéticos nuevos para la semilla ilustrada.
:name: fig-12-aumentacion-resumen

Media, mediana y desviación de la nota en originales y sintéticos nuevos para la semilla ilustrada.
```


Los originales tienen media **3,5340**, mediana **3,7000** y desviación **1,1349**; la perturbación, **3,5182**, **3,7000** y **1,1351**; la interpolación, **3,5418**, **3,6800** y **1,0190**. La interpolación aproxima la media, pero reduce la dispersión. Conservar una media similar no garantiza conservar colas, faltantes, categorías o relaciones entre variables.

### Estabilidad y distancias de fidelidad


```{figure} images/13_aumentacion_semillas.jpg
:alt: Puntaje de fidelidad en cinco semillas: valores menores indican más parecido con originales de train.
:name: fig-13-aumentacion-semillas

Puntaje de fidelidad en cinco semillas: valores menores indican más parecido con originales de train.
```


```{figure} images/14_aumentacion_distancias.jpg
:alt: Distancias de distribuciones y asociaciones promediadas entre las cinco semillas.
:name: fig-14-aumentacion-distancias

Distancias de distribuciones y asociaciones promediadas entre las cinco semillas.
```


El puntaje medio es **0,013587** para perturbación y **0,029090** para interpolación: reducción relativa **53,30 %**. Perturbación gana en las cinco semillas y conserva la selección en las seis comprobaciones que retiran un componente del puntaje. Esto respalda la estabilidad de la elección entre estas alternativas bajo el criterio empleado.

El puntaje promedia KS de numéricas, Wasserstein normalizada, variación total categórica, diferencia de faltantes, cambio de Spearman y variación total de combinaciones categóricas. Las barras ayudan a localizar el tipo de cambio. No deben sumarse ni interpretarse como errores de predicción: tienen definiciones y escalas distintas. La fidelidad observada no demuestra una mejora del modelo frente a entrenar solo con originales.

### Conclusión de la aumentación: por qué se eligió la técnica 1

Se seleccionó la **perturbación local controlada** porque conservó mejor la estructura de los datos originales de entrenamiento bajo el criterio de fidelidad definido en la primera entrega. La decisión se sustenta en varias evidencias complementarias:

- **Menor distancia global:** su puntaje medio de seis diagnósticos fue **0,013587**, frente a **0,029090** de interpolación, una reducción relativa de **53,30 %**. El criterio considera distribuciones numéricas, categorías, faltantes, relaciones entre variables y combinaciones categóricas, en lugar de comparar únicamente la media de la nota.
- **Estabilidad de la selección:** la técnica 1 obtuvo el mejor puntaje en **las cinco semillas** y mantuvo la ventaja en **las seis comprobaciones que retiran un componente** del puntaje. La elección no dependió de una sola generación ni de un único diagnóstico.
- **Conservación de la dispersión del objetivo:** en la semilla ilustrada, la desviación de la nota de los sintéticos por perturbación fue **1,1351**, cercana a **1,1349** de los originales; la interpolación la redujo a **1,0190**. Las densidades y acumuladas respaldan que una media similar no basta si se comprime la variabilidad de las notas.
- **Coherencia de los archivos seleccionados:** train y test de la técnica 1 cumplen las reglas de negocio, mantienen la identidad del avance y no requieren exclusiones por inconsistencias. Son condiciones necesarias para usar la muestra; por sí solas no distinguen una técnica de otra, porque ambas se someten a esos controles.

La selección se realizó **sin utilizar test para elegir la metodología**. Por esa evidencia se adoptó la alternativa 1 como fuente común del EDA, los modelos y el dashboard. Su ventaja corresponde a fidelidad distribucional entre las dos opciones estudiadas; no demuestra que aumentar la muestra mejore la predicción frente a usar solo originales, ni convierte las variantes en nuevos estudiantes independientes.

## Página 2 · EDA: Exploración interactiva

### Tarjetas, histograma y cajas por asignatura

La vista general tiene **24.000 filas**, nota media **3,5190**, mediana **3,7000** y desviación **1,1351**. La mediana mayor que la media es coherente con una cola hacia notas bajas (asimetría −0,4388). La escala va de 0,5 a 5,0 y el extremo superior concentra observaciones. No hay extremos IQR en el objetivo; eso no implica ausencia de extremos en las predictoras.


```{figure} images/04_eda_distribucion.jpg
:alt: Histograma de la nota y cajas por asignatura sobre train válido, sin filtros.
:name: fig-04-eda-distribucion

Histograma de la nota y cajas por asignatura sobre train válido, sin filtros.
```


Las cajas comparan mediana e intervalo intercuartílico. MAT1011 concentra notas altas, mientras que las otras asignaturas presentan centros menores y dispersión amplia. La tabla siguiente hace explícitos los tamaños y centros de cada distribución; no mide un efecto causal de cursar una asignatura.

| Asignatura | Filas | Media | Mediana | Desviación |
| --- | --- | --- | --- | --- |
| MAT1011 | 390 | 4,3663 | 4,4150 | 0,6691 |
| MAT1100 | 8141 | 3,6838 | 3,9500 | 1,0962 |
| MAT1101 | 14430 | 3,3992 | 3,5500 | 1,1593 |
| MAT4190 | 1039 | 3,5745 | 3,6900 | 0,9105 |


Al comparar por programa o asignatura, el histograma normaliza porcentajes dentro de cada categoría. Se compara forma relativa y no tamaño absoluto. Al cambiar los filtros se recalculan las tarjetas con las filas seleccionadas. Los extremos permanecen en los cálculos aunque las cajas no los dibujen individualmente.

### Scatter, Spearman y redundancia


```{figure} images/05_eda_asociaciones.jpg
:alt: Scatter de dominio final frente a nota y matriz de Spearman calculada sobre todas las filas disponibles.
:name: fig-05-eda-asociaciones

Scatter de dominio final frente a nota y matriz de Spearman calculada sobre todas las filas disponibles.
```


El scatter inicial relaciona dominio final con nota: **ρ = 0,4633**. Hay una tendencia monotónica positiva, pero una dispersión considerable: el dominio final por sí solo no determina la nota. Los 2.500 puntos dibujados son una muestra reproducible; el coeficiente utiliza las filas disponibles completas.

Saber 11 global presenta la mayor asociación monotónica numérica con la nota (**ρ = 0,5281**), seguido de dominio inicial (**0,4683**) y dominio final (**0,4633**). La matriz permite además revisar la redundancia entre predictoras: Saber 11 global y Matemáticas tienen ρ = **0,8265**, y avance/dominio final, **0,8437**. Avance = final − inicial es una dependencia exacta, más fuerte conceptualmente que cualquier umbral de correlación.

| Predictora | Pares disponibles | Spearman con nota |
| --- | --- | --- |
| Saber 11 · global | 24000 | 0,5281 |
| Saber 11 · matemáticas | 24000 | 0,4075 |
| Tiempo de pretest (horas) | 23574 | 0,3603 |
| Dominio inicial (temas) | 24000 | 0,4683 |
| Avance en ALEK (temas) | 24000 | 0,2978 |
| Dominio final (temas) | 24000 | 0,4633 |
| Tiempo de trabajo (horas) | 23939 | 0,0662 |
| Temas aprendidos por hora | 23939 | 0,3768 |


Tiempo total tiene una asociación monotónica pequeña con la nota. Eso no prueba que el tiempo de práctica carezca de valor: mide cantidad registrada, se combina con conocimientos iniciales y contexto, y no representa un tratamiento aleatorio. Tampoco una correlación positiva implica que aumentar unilateralmente una variable causará una nota mayor.

### Frecuencias y nota por dominio final


```{figure} images/06_eda_dominio.jpg
:alt: Frecuencias de cumplimiento y cajas de nota por intervalos fijos de dominio final.
:name: fig-06-eda-dominio

Frecuencias de cumplimiento y cajas de nota por intervalos fijos de dominio final.
```


El gráfico categórico seleccionable muestra porcentajes y conteos del grupo filtrado. Las cajas por dominio final usan límites obtenidos una vez de los cuartiles de todo train, que se mantienen al filtrar. Sus centros cambian con el dominio, pero la superposición confirma que alumnos con dominio similar pueden tener notas distintas.

| Intervalo de temas | Filas | Media de nota | Mediana de nota |
| --- | --- | --- | --- |
| 0–17 | 6028 | 2,8313 | 2,6100 |
| 17–32 | 5980 | 3,3228 | 3,2700 |
| 32–49 | 6036 | 3,7087 | 3,8700 |
| 49–143 | 5956 | 4,2198 | 4,4900 |


### Nueve distribuciones numéricas

Cada histograma expresa densidad, con curva KDE sobre todos los valores disponibles, sin imputar ni recortar extremos. Las alturas no se comparan entre variables con unidades diferentes. Las estadísticas siguientes ayudan a leer concentración, sesgo y dispersión de cada gráfico.


#### Saber 11 · global


```{figure} images/densidad_1.jpg
:alt: Distribución y densidad de saber 11 · global en train general.
:name: fig-densidad-1

Distribución y densidad de saber 11 · global en train general.
```

**Lectura numérica:** 24.000 valores disponibles y 0 ausentes; media **340,7495**, mediana **346,0000**, desviación **47,1422**, cuartiles **313,0000–369,0000** y asimetría **-0,8850**.


El puntaje global resume conocimientos previos y muestra una relación positiva con la nota. La concentración central no elimina la heterogeneidad académica; la fuerte asociación con Saber 11 Matemáticas aconseja interpretar ambos coeficientes en conjunto.


#### Saber 11 · matemáticas


```{figure} images/densidad_2.jpg
:alt: Distribución y densidad de saber 11 · matemáticas en train general.
:name: fig-densidad-2

Distribución y densidad de saber 11 · matemáticas en train general.
```

**Lectura numérica:** 24.000 valores disponibles y 0 ausentes; media **68,4145**, mediana **69,0000**, desviación **9,9626**, cuartiles **64,0000–74,0000** y asimetría **-1,0341**.


El componente matemático también se asocia positivamente con la nota. Su distribución usa otra escala que el puntaje global. Su asociación marginal positiva puede coexistir con un coeficiente negativo al incluir variables correlacionadas en el SVM.


#### Tiempo de pretest (horas)


```{figure} images/densidad_3.jpg
:alt: Distribución y densidad de tiempo de pretest (horas) en train general.
:name: fig-densidad-3

Distribución y densidad de tiempo de pretest (horas) en train general.
```

**Lectura numérica:** 23,574 valores disponibles y 426 ausentes; media **0,7405**, mediana **0,5356**, desviación **0,6196**, cuartiles **0,3058–0,9661** y asimetría **1,6947**.


La cola hacia tiempos altos explica la asimetría positiva. El tiempo requerido para el pretest puede reflejar dificultad, ritmo o dedicación, y no es una medida causal aislada. Los faltantes se conservan en EDA y se imputan dentro del pipeline.


#### Dominio inicial (temas)


```{figure} images/densidad_4.jpg
:alt: Distribución y densidad de dominio inicial (temas) en train general.
:name: fig-densidad-4

Distribución y densidad de dominio inicial (temas) en train general.
```

**Lectura numérica:** 24.000 valores disponibles y 0 ausentes; media **8,9832**, mediana **2,0000**, desviación **15,4203**, cuartiles **0,0000–10,0000** y asimetría **3,1628**.


La mediana baja y la cola positiva indican que numerosas filas parten de dominio inicial reducido, mientras algunas ya dominan muchos temas. Es una diferencia de conocimientos previos que ayuda a contextualizar el avance posterior.


#### Avance en ALEK (temas)


```{figure} images/densidad_5.jpg
:alt: Distribución y densidad de avance en alek (temas) en train general.
:name: fig-densidad-5

Distribución y densidad de avance en alek (temas) en train general.
```

**Lectura numérica:** 24.000 valores disponibles y 0 ausentes; media **27,7274**, mediana **26,0000**, desviación **20,0618**, cuartiles **11,0000–38,0000** y asimetría **0,8591**.


Resume el incremento de temas, calculado como dominio final menos inicial. El mismo avance puede corresponder a niveles iniciales muy distintos; además es redundante con ambos dominios y no equivale por sí solo a aprendizaje demostrado en el parcial.


#### Dominio final (temas)


```{figure} images/densidad_6.jpg
:alt: Distribución y densidad de dominio final (temas) en train general.
:name: fig-densidad-6

Distribución y densidad de dominio final (temas) en train general.
```

**Lectura numérica:** 24.000 valores disponibles y 0 ausentes; media **36,7106**, mediana **32,0000**, desviación **26,4369**, cuartiles **17,0000–49,0000** y asimetría **1,1809**.


Mide temas dominados al terminar el nivelatorio. Su asociación positiva y las cajas por intervalos justifican explorarlo, pero no permiten convertir un número de temas en una nota sin considerar el resto de características.


#### Tiempo de trabajo (horas)


```{figure} images/densidad_7.jpg
:alt: Distribución y densidad de tiempo de trabajo (horas) en train general.
:name: fig-densidad-7

Distribución y densidad de tiempo de trabajo (horas) en train general.
```

**Lectura numérica:** 23,939 valores disponibles y 61 ausentes; media **18,4466**, mediana **16,4471**, desviación **12,6901**, cuartiles **8,6199–25,6660** y asimetría **1,2421**.


La distribución conserva tiempos de trabajo bajos y altos válidos. La asociación marginal con nota es pequeña. log1p permite moderar la escala de los valores altos en el modelo sin borrarlos ni reinterpretar un cero real como ausente.


#### Temas aprendidos por hora


```{figure} images/densidad_8.jpg
:alt: Distribución y densidad de temas aprendidos por hora en train general.
:name: fig-densidad-8

Distribución y densidad de temas aprendidos por hora en train general.
```

**Lectura numérica:** 23,939 valores disponibles y 61 ausentes; media **1,5523**, mediana **1,4184**, desviación **0,9008**, cuartiles **1,0027–1,9772** y asimetría **1,3186**.


Es una tasa, no una duración. Sus valores dependen del avance y del tiempo medido; las colas y ceros requieren lectura conjunta con las reglas de negocio. Una tasa elevada no determina la calidad de las respuestas en el parcial.


#### Nota del primer parcial


```{figure} images/densidad_9.jpg
:alt: Distribución y densidad de nota del primer parcial en train general.
:name: fig-densidad-9

Distribución y densidad de nota del primer parcial en train general.
```

**Lectura numérica:** 24.000 valores disponibles y 0 ausentes; media **3,5190**, mediana **3,7000**, desviación **1,1351**, cuartiles **2,6200–4,5300** y asimetría **-0,4388**.


La mayor concentración está hacia notas altas y la mediana supera la media. La escala se mantiene sin transformación para que MAE y RMSE tengan interpretación en puntos de nota. La densidad suavizada no crea observaciones fuera de los límites reales.


### Siete distribuciones categóricas

Cada figura conserva todas las categorías. Una barra extensa indica concentración dentro de la muestra aumentada. Las categorías raras siguen visibles y no se fusionan automáticamente; sus inferencias tienen menos respaldo. Los conteos se refieren a filas y no a estudiantes distintos.


#### Categoría de temas iniciales


```{figure} images/categorica_1.jpg
:alt: Frecuencias completas de categoría de temas iniciales en train general.
:name: fig-categorica-1

Frecuencias completas de categoría de temas iniciales en train general.
```

Hay **11 categorías**. La más frecuente es **1 Repaso de álgebra y geometría**, con **11,812 filas (49,22 %)**; una de las menos frecuentes es **2 Ecuaciones racionales que se reducen a lineales**, con **16 filas (0,07 %)**.


Ordena descripciones del punto de partida académico. Las etiquetas contienen temas que pueden pertenecer a currículos distintos, por lo que su texto no define una escala numérica universal. Su asociación con nota describe diferencias de perfiles iniciales.


#### Categoría de temas finales


```{figure} images/categorica_2.jpg
:alt: Frecuencias completas de categoría de temas finales en train general.
:name: fig-categorica-2

Frecuencias completas de categoría de temas finales en train general.
```

Hay **12 categorías**. La más frecuente es **3 Temas Parcial 1 Cálculo I**, con **7,914 filas (32,98 %)**; una de las menos frecuentes es **2 Ecuaciones racionales que se reducen a lineales**, con **23 filas (0,10 %)**.


Describe los contenidos alcanzados al cierre y comparte información con dominio final y cumplimiento. La fuerte dependencia con otras categorías no permite atribuir el rendimiento exclusivamente a una etiqueta final.


#### Programa


```{figure} images/categorica_3.jpg
:alt: Frecuencias completas de programa en train general.
:name: fig-categorica-3

Frecuencias completas de programa en train general.
```

Hay **16 categorías**. La más frecuente es **Ingeniería Sistemas Y Computac**, con **5,080 filas (21,17 %)**; una de las menos frecuentes es **Curso libre pregrado**, con **23 filas (0,10 %)**.


La representación desigual implica que el promedio general está más influido por programas con más filas. No indica qué programa es mejor; comparar errores exige atender a la asignatura, composición y tamaño de cada grupo.


#### División académica


```{figure} images/categorica_4.jpg
:alt: Frecuencias completas de división académica en train general.
:name: fig-categorica-4

Frecuencias completas de división académica en train general.
```

Hay **6 categorías**. La más frecuente es **División de Ingenierías**, con **13,089 filas (54,54 %)**; una de las menos frecuentes es **Centro de Educ. Continuada**, con **182 filas (0,76 %)**.


Agrupa programas por unidad institucional. Programa y división están estrechamente relacionados, de modo que sus frecuencias y coeficientes contienen información redundante.


#### Asignatura


```{figure} images/categorica_5.jpg
:alt: Frecuencias completas de asignatura en train general.
:name: fig-categorica-5

Frecuencias completas de asignatura en train general.
```

Hay **4 categorías**. La más frecuente es **MAT1101**, con **14,430 filas (60,12 %)**; una de las menos frecuentes es **MAT1011**, con **390 filas (1,62 %)**.


Las cuatro asignaturas tienen tamaños distintos y diferentes distribuciones de nota. La mezcla influye en las métricas generales. Un filtro por asignatura evalúa el mismo SVM global y no un modelo reentrenado para ese curso.


#### Categoría de avance por cuartiles


```{figure} images/categorica_6.jpg
:alt: Frecuencias completas de categoría de avance por cuartiles en train general.
:name: fig-categorica-6

Frecuencias completas de categoría de avance por cuartiles en train general.
```

Hay **16 categorías**. La más frecuente es **1 Avance entre [ 19 - 40 temas]**, con **6,198 filas (25,82 %)**; una de las menos frecuentes es **1 Avance entre [ 15 - 23 temas]**, con **44 filas (0,18 %)**.


Las categorías combinan rangos definidos originalmente por asignatura y semestre. No son cuartiles globales equivalentes: alcanzar el mismo intervalo puede tener significado distinto según el contexto. El formulario no reconstruye esos umbrales.


#### Cumplimiento de la meta


```{figure} images/categorica_7.jpg
:alt: Frecuencias completas de cumplimiento de la meta en train general.
:name: fig-categorica-7

Frecuencias completas de cumplimiento de la meta en train general.
```

Hay **2 categorías**. La más frecuente es **Cumplimiento meta**, con **12,368 filas (51,53 %)**; una de las menos frecuentes es **No alcanzo meta**, con **11,632 filas (48,47 %)**.


Distingue si se alcanzó la meta del curso. Su frecuencia describe cumplimiento en la muestra. Que una categoría predomine o tenga otra media no establece que cambiar el indicador provoque una variación en la nota.


### Faltantes y decisiones del EDA


```{figure} images/07_eda_faltantes.jpg
:alt: Porcentaje de ausencias por variable numérica; se calculan sin imputación en EDA.
:name: fig-07-eda-faltantes

Porcentaje de ausencias por variable numérica; se calculan sin imputación en EDA.
```


Hay **548 celdas faltantes**: 426 en tiempo de pretest (**1,7750 %** de train), 61 en tiempo total (**0,2542 %**) y 61 en tasa de temas aprendidos por hora (**0,2542 %**). Son conteos por celda y no necesariamente 548 filas diferentes. Las demás variables no presentan ausencias en esta versión.

El patrón se concentra en mediciones de tiempo. No se puede concluir que las ausencias sean completamente aleatorias ni confundirlas con ceros de actividad. El modelo usa mediana aprendida en cada fold; EDA conserva los faltantes al describir disponibilidad.


```{figure} images/08_eda_conclusion.jpg
:alt: Conclusión del EDA y tabla de evidencias que respaldan los tratamientos del pipeline.
:name: fig-08-eda-conclusion

Conclusión del EDA y tabla de evidencias que respaldan los tratamientos del pipeline.
```


El cierre conecta los gráficos con decisiones: mantener escala del objetivo, imputar dentro del pipeline, aplicar log1p en tiempos, usar one-hot y conservar extremos válidos. Son decisiones del análisis global y no se vuelven a seleccionar al filtrar. La nota depende de múltiples características y los gráficos no justifican efectos causales aislados.

## Página 3 · Modelos lineales

### Separación, validación y pipeline


```{figure} images/15_modelos_separacion.jpg
:alt: Flujo de train/test aumentado después de la separación original por estudiante.
:name: fig-15-modelos-separacion

Flujo de train/test aumentado después de la separación original por estudiante.
```


```{figure} images/16_modelos_folds.jpg
:alt: Esquema conceptual de cinco folds estratificados; el test permanece fuera del ajuste.
:name: fig-16-modelos-folds

Esquema conceptual de cinco folds estratificados; el test permanece fuera del ajuste.
```


La separación externa mantiene 24.000 filas válidas de train y 6.000 de test. En cada fold las transformaciones y el modelo aprenden solo del bloque de entrenamiento. Sin IDs persistentes, la validación interna no puede agrupar variantes del mismo estudiante. Por esa razón su buen resultado se contrasta con test y no se presenta como garantía de generalización.

El pipeline imputa mediana numérica y moda categórica, aplica log1p a tiempos, estandariza numéricas y codifica categorías con referencia. Se compara DummyRegressor (media de train) con LinearSVR: C = 1, ε = 0,1, máximo 20.000 iteraciones y semilla 42. El objetivo permanece en su escala original.

### Métricas generales y comparación con Dummy


```{figure} images/17_modelos_metricas.jpg
:alt: Comparación de RMSE, MAE y R² entre Dummy y SVM en validación y test.
:name: fig-17-modelos-metricas

Comparación de RMSE, MAE y R² entre Dummy y SVM en validación y test.
```


```{figure} images/18_modelos_tabla.jpg
:alt: Tabla de estadísticas y conclusiones del modelo global, con media de folds y test.
:name: fig-18-modelos-tabla

Tabla de estadísticas y conclusiones del modelo global, con media de folds y test.
```

| Modelo | Evaluación | n | RMSE | MAE | MAPE (%) | R² |
| --- | --- | --- | --- | --- | --- | --- |
| Dummy media | Validación (5 folds) | 24000 | 1,1350 | 0,9770 | 38,5956 | -0,0000 |
| Dummy media | Test reservado | 6000 | 1,1532 | 0,9935 | 39,7168 | -0,0006 |
| SVM lineal | Validación (5 folds) | 24000 | 0,7974 | 0,6155 | 23,3775 | 0,5064 |
| SVM lineal | Test reservado | 6000 | 0,9083 | 0,7314 | 27,7552 | 0,3792 |


En test, el SVM tiene **RMSE 0,9083**, **MAE 0,7314**, **MAPE 27,7552 %** y **R² 0,3792**. Dummy tiene RMSE **1,1532**, MAE **0,9935**, MAPE **39,7168 %** y R² **−0,0006**. El SVM reduce el RMSE **21,23 %** y MAPE **30,12 %**; mejora una referencia trivial, pero deja una fracción considerable de variación sin explicar.

R² = 0,3792 no significa 37,92 % de predicciones correctas. Describe la reducción de error cuadrático relativa a la media de la muestra. El MAE de 0,7314 es un error absoluto promedio y no un límite garantizado para cada estudiante. RMSE mayor que MAE indica que errores grandes tienen peso apreciable.

En validación el SVM alcanza RMSE medio **0,7974** y R² medio **0,5064**. El rendimiento es mejor que en test, por lo que la evaluación externa es menos favorable que la interna. La dependencia de variantes en folds distintos es una posible explicación que no está comprobada de forma causal. Las barras tienen ejes separados: una altura de R² no se compara directamente con una altura de RMSE.

### Predicción frente a realidad


```{figure} images/19_modelos_prediccion.jpg
:alt: Predicciones de SVM frente a notas reales, con diagonal ideal y muestra de 3.000 filas de test.
:name: fig-19-modelos-prediccion

Predicciones de SVM frente a notas reales, con diagonal ideal y muestra de 3.000 filas de test.
```

En la diagonal coinciden predicción y nota real; por encima hay sobreestimación y por debajo, subestimación. La dispersión muestra que el modelo no reproduce cada resultado individual. Hay **219 predicciones fuera de 0,5–5,0** (**3,65 %** del test). LinearSVR no acota la salida y no se recortan los valores para evaluar.



La nube representa 3.000 de las 6.000 filas con semilla fija; las métricas utilizan las 6.000. La concentración en zonas de la nube también refleja las distribuciones de nota y de los datos sintéticos. No debe interpretarse cada punto como un estudiante independiente.

### Residuos y predicción media por intervalo


```{figure} images/20_modelos_residuos.jpg
:alt: Residuos definidos como nota real menos predicción; cero representa coincidencia.
:name: fig-20-modelos-residuos

Residuos definidos como nota real menos predicción; cero representa coincidencia.
```


```{figure} images/21_modelos_calibracion.jpg
:alt: Notas predichas medias de SVM y Dummy en nueve intervalos de nota real.
:name: fig-21-modelos-calibracion

Notas predichas medias de SVM y Dummy en nueve intervalos de nota real.
```


Un residuo positivo indica que el modelo subestima; uno negativo, que sobreestima. El residuo medio SVM es **−0,0355**, equivalente a una leve sobreestimación promedio. Ese promedio cercano a cero no prueba ausencia de sesgo en extremos, pues errores opuestos pueden compensarse.

El resumen por nota real muestra tendencia a sobreestimar notas bajas y subestimar notas altas: las predicciones se acercan al centro. Dummy es casi horizontal porque ofrece la media de entrenamiento a todos; SVM reproduce más variación, aunque no sigue perfectamente la diagonal. El resumen usa todas las filas y nueve intervalos, cuyos tamaños pueden ser distintos.

La normalidad de residuos se rechaza en el diagnóstico actual (p ≈ 1,47×10⁻¹¹), al igual que la homocedasticidad bajo Breusch–Pagan (p ≈ 2,05×10⁻³⁰). Spearman entre predicción y error absoluto es **−0,1535**, una asociación débil negativa. Son diagnósticos sobre la muestra aumentada; no justifican pruebas t de los coeficientes del SVM.

| Intervalo real | Filas | Real | SVM | Dummy |
| --- | --- | --- | --- | --- |
| (0.49, 0.992] | 83 | 0,9323 | 2,6073 | 3,5190 |
| (0.992, 1.494] | 250 | 1,2070 | 2,3609 | 3,5190 |
| (1.494, 1.997] | 429 | 1,8034 | 2,8164 | 3,5190 |
| (1.997, 2.499] | 617 | 2,2478 | 3,0118 | 3,5190 |
| (2.499, 3.001] | 698 | 2,7419 | 3,0954 | 3,5190 |
| (3.001, 3.503] | 727 | 3,2338 | 3,3580 | 3,5190 |
| (3.503, 4.006] | 754 | 3,7921 | 3,6843 | 3,5190 |
| (4.006, 4.508] | 919 | 4,2667 | 3,8103 | 3,5190 |
| (4.508, 5.01] | 1523 | 4,8357 | 4,2074 | 3,5190 |


### Profundizar: intervalos bootstrap


```{figure} images/22_modelos_intervalos.jpg
:alt: Intervalos globales del 95 % obtenidos con 1.000 remuestreos de filas de test aumentado.
:name: fig-22-modelos-intervalos

Intervalos globales del 95 % obtenidos con 1.000 remuestreos de filas de test aumentado.
```


El intervalo de RMSE SVM es **[0,8925; 0,9241]**, el de MAPE **[26,8587 %; 28,6862 %]** y el de R² **[0,3575; 0,4008]**. La mejora frente a la referencia persiste en el remuestreo de estas filas. Sin embargo, no son intervalos de error de una persona ni sustituyen evaluar estudiantes independientes.

Esta sección muestra resultados globales del notebook y no cambia con los filtros. Es importante no atribuir estos intervalos al programa o asignatura seleccionado en otra parte del tablero.

### Profundizar: curva de aprendizaje


```{figure} images/23_modelos_aprendizaje.jpg
:alt: RMSE de entrenamiento y validación a medida que aumenta el número de filas de ajuste en los folds.
:name: fig-23-modelos-aprendizaje

RMSE de entrenamiento y validación a medida que aumenta el número de filas de ajuste en los folds.
```


La curva alcanza, con **19.200 filas de entrenamiento por fold**, RMSE de train **0,7947** y de validación **0,7974**. La brecha interna es pequeña; la curva de validación cambia poco después de los tamaños iniciales. Esto sugiere ganancias marginales limitadas al añadir variantes bajo este procedimiento, no que más estudiantes reales sean innecesarios.

Una brecha pequeña tampoco valida independencia de observaciones ni demuestra que no haya sobreajuste de ningún tipo. El test presenta RMSE 0,9083, mayor que el de validación, y debe formar parte de la lectura conjunta.

### Profundizar: coeficientes y referencias


```{figure} images/24_modelos_coeficientes.jpg
:alt: Doce coeficientes de mayor magnitud del SVM en el espacio transformado.
:name: fig-24-modelos-coeficientes

Doce coeficientes de mayor magnitud del SVM en el espacio transformado.
```


El gráfico conserva signos y magnitudes, pero no es un ranking causal ni una prueba de significancia. Numéricas estandarizadas y categorías one-hot tienen interpretaciones distintas. La redundancia entre dominios, avance y variables institucionales permite redistribuir señales entre términos; por ello un signo negativo puede coexistir con una correlación marginal positiva.

Por ejemplo, Saber 11 global tiene coeficiente aproximado **0,5121**, mientras Matemáticas tiene **−0,1507** aunque su Spearman marginal con nota sea positivo. Ambas variables están correlacionadas. El término de «No alcanzó meta» es positivo en este ajuste, pero no se puede concluir que incumplir una meta mejore la nota. La categoría final, los dominios, el programa y las demás variables condicionan esa lectura.

El reporte completo incluye intercepto **1,6554**, todos los términos estimados y siete referencias con β fijado en cero. LinearSVR no calcula p-valores; asignarle valores de OLS sería describir otro modelo. El [tercer capítulo](03_metodologia.md) reproduce el reporte completo en una tabla accesible.

### Ejemplo de predicción


```{figure} images/25_modelos_simulador.jpg
:alt: Formulario del ejemplo con tiempo total de trabajo de 25,5 horas y nota predicha 3,642.
:name: fig-25-modelos-simulador

Formulario del ejemplo con tiempo total de trabajo de 25,5 horas y nota predicha 3,642.
```


En el ejemplo inicial se cambia únicamente el tiempo total a **25,5 horas**. El pipeline guardado devuelve **3,642**. No es una nota observada ni un resultado garantizado. El MAE global de 0,731 no convierte esa salida en un intervalo individual «3,642 ± 0,731».

El avance se calcula como dominio final − inicial; no acepta una entrada independiente que contradiga esa identidad. Los dominios son necesarios para comprobar coherencia, y los tiempos cero con avance positivo se rechazan. Los campos numéricos ausentes permitidos se imputan con las medianas aprendidas. Programa, asignatura y división deben corresponder a una combinación observada en train; los cuartiles y categorías se seleccionan como características conocidas porque sus reglas por semestre no se reconstruyen con el esquema público.

### Conclusión de la página de modelos

El SVM supera Dummy y aporta una referencia predictiva parcial, con capacidad menor en test que en validación interna. Los gráficos muestran dispersión, regresión hacia el centro, errores de variabilidad no uniforme y algunas predicciones fuera de escala. La conclusión es mantenerlo como base de comparación y evaluar por estudiante, en test original y en otros periodos antes de un uso operativo.

## Cómo trasladar la lectura a un filtro

Al elegir programa o asignatura cambian tamaño, distribuciones, asociaciones y errores del grupo seleccionado. El modelo y sus parámetros se mantienen. Conviene leer primero el número de filas, después MAE/RMSE y finalmente R² junto con la variación de la nota. Un R² menor puede reflejar que el grupo tenga notas más homogéneas y no necesariamente un aumento equivalente del error absoluto.

Con menos de 30 filas el tablero señala lectura inestable. Con una sola fila o nota constante no calcula R². Una combinación vacía muestra un mensaje y no un resultado cero. Las secciones de intervalos, aprendizaje y coeficientes siguen siendo globales, y el simulador tiene entradas independientes de los filtros de evaluación.

## Evidencia que queda documentada

Las capturas muestran cada tipo de resultado y los dieciséis gráficos numéricos/categóricos de exploración. Los valores y tablas provienen de la caché y de las exportaciones canónicas verificadas. El detalle adicional de diagnósticos, fórmulas, coeficientes y reproducción se presenta en [Metodología y detalles adicionales](03_metodologia.md).

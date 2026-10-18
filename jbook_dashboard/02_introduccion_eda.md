---
title: Introducción y EDA
description: Lectura de las páginas de contexto y análisis exploratorio del dashboard sobre datos reales.
---

# Introducción y EDA

Este capítulo recorre las dos primeras páginas del dashboard: **01 Introducción** y **02 EDA**. La lectura describe qué contienen los datos reales del nivelatorio, cómo se documentan las variables y qué muestran las distribuciones y asociaciones del entrenamiento válido. Las cifras corresponden a la vista general, con programa y asignatura en **Todos**; los filtros del tablero recalculan las mismas evidencias sobre el subgrupo elegido.

El recorrido avanza en el mismo orden que el tablero. Primero se fija el contexto institucional y la pregunta de investigación. Después se revisa el diccionario de variables y las reglas de negocio que determinan qué registros son válidos. Finalmente, la exploración interactiva describe la distribución de la nota, las asociaciones entre variables, las frecuencias categóricas, los faltantes y las decisiones que alimentan el pipeline. Cada sección conecta una lectura del tablero con la cifra que la respalda.

## Página 1 · Introducción

Antes de explorar los datos conviene entender de dónde vienen y qué pregunta guía el ejercicio. Esta página cumple esa función: presenta el proyecto y su alcance sin entrar todavía en el análisis estadístico.

La pantalla inicial sitúa el nivelatorio en la Universidad del Norte, identifica la fuente de **1.527 registros de 2023–2025** y presenta cuatro asignaturas. Esas tarjetas describen la fuente original, mientras que EDA y modelos trabajan con las particiones preparadas. Los tamaños no se contradicen: corresponden a etapas distintas del proceso.

La pregunta es predictiva: relacionar mediciones académicas disponibles con la nota del primer parcial. La plataforma ALEK aporta dominio de temas, avance y tiempos; Saber 11 e información institucional amplían el contexto. La introducción no presenta una prueba de que asistir al nivelatorio cause un aumento de nota. Para esa conclusión haría falta un diseño de evaluación de intervención que este proyecto no contiene.

Con ese marco claro, el siguiente paso es revisar cómo se traduce la información disponible en variables concretas. La captura de esta página se conserva en el [capítulo de desarrollo](01_desarrollo.md#desarrollo-introduccion).

## Página 2 · EDA: Variables y contexto

El EDA comienza por el diccionario y las reglas, porque toda cifra posterior depende de cómo se define cada variable y de qué registros se consideran válidos. Esta parte responde qué mide cada columna, cómo se relaciona con el objetivo y cómo se evita usar información futura.

### Diccionario y temporalidad

El diccionario distingue las ocho predictoras numéricas, siete categóricas y el objetivo. El dominio inicial mide entrada; el final mide salida; el avance es su diferencia. Las categorías de temas, cumplimiento y cuartiles resumen aspectos que también aparecen en las variables numéricas, por lo que parte de la información es redundante.

El esquema conserva `nota_final` para auditar fuga, pero el tablero no la incorpora en matrices de correlación ni datos de predicción. La calificación final ocurre después del primer parcial y usarla produciría un pronóstico con información futura. La disponibilidad de las otras variables antes del parcial es un supuesto de este ejercicio que debe verificarse para cada horizonte de uso.

```{figure} images/02_diccionario.jpg
:alt: Diccionario del proyecto con las 17 columnas del esquema estandarizado.
:name: eda-diccionario

Diccionario mostrado en Variables y contexto; nota_final se identifica como variable excluida del modelo.
```

### Fuente y reglas de negocio

Con el esquema claro, el siguiente paso es revisar la fuente y las reglas que determinan qué filas entran al análisis. Esa revisión conecta la definición de las variables con la calidad de los registros.

La fuente contiene **1.527 registros**. Se excluyen **30 filas sin nota del parcial** del análisis supervisado y se conservan los outliers válidos. Los identificadores se usan solo para separar estudiantes y no se exportan al dashboard ni entran como predictores.

Tres reglas se aplican antes de imputar: dominio final ≥ inicial; tiempo total cero implica dominios iguales; tasa de temas aprendidos por hora cero implica dominios iguales. En train y test no hay incumplimientos y no se excluyen filas en esta etapa. Un valor extremo válido se conserva; una inconsistencia se rechaza. Tampoco se reemplaza un cero real por un faltante.

```{figure} images/03_reglas.jpg
:alt: Reglas de negocio y resultado de integridad: cero incumplimientos en las particiones.
:name: eda-reglas

Reglas de negocio validadas y resultado de integridad en train y test.
```

## Página 2 · EDA: Exploración interactiva

Una vez definidos el esquema y las reglas, la exploración se concentra en el entrenamiento válido. El recorrido va de lo general a lo específico: primero la forma de la nota y las diferencias entre grupos; después las asociaciones y la redundancia; luego las frecuencias y las densidades; finalmente los faltantes y las decisiones que alimentan el pipeline.

La exploración usa únicamente el entrenamiento válido: **1.309 registros de 1.293 estudiantes**. Las ausencias no se rellenan para EDA; las pruebas estadísticas se calculan sobre los datos disponibles del grupo filtrado. Algunos estudiantes pueden tener más de un registro y esa dependencia no se corrige en estos contrastes exploratorios.

### Distribución de la nota y diferencias entre grupos

La nota tiene **media 3,499**, **mediana 3,700** y **desviación 1,118** en la escala de 0,5 a 5,0. La mediana mayor que la media es compatible con una cola hacia notas bajas. Shapiro–Wilk rechaza la normalidad marginal (**W = 0,9458; p < 0,0001; n = 1.309**), lo que no obliga a eliminar valores extremos ni a cambiar la escala.

Las cajas comparan mediana e intervalo intercuartílico por asignatura. Kruskal–Wallis detecta diferencias entre al menos dos grupos (**H = 19,9458; gl = 3; p = 0,0002**). La mayor mediana es **4,10** (MAT1011 · Álgebra y Trigonometría) y la menor, **3,50** (MAT1101 · Cálculo I). El contraste global no identifica qué pares difieren ni demuestra un efecto causal de cursar una asignatura.

```{figure} images/04_eda_distribucion.jpg
:alt: Histograma de la nota del primer parcial y cajas por asignatura sobre train válido.
:name: eda-distribucion

Distribución de la nota y diferencias entre grupos en la vista general del EDA.
```

### Asociaciones y redundancia

Después de describir la nota y su separación por grupos, conviene revisar qué variables se mueven con ella y cuánta información comparten entre sí. Esa doble lectura —asociación con el objetivo y redundancia entre predictoras— ayuda a interpretar los modelos posteriores.

El scatter relaciona dominio final con nota: **ρ = 0,456**. Hay una tendencia monotónica positiva, pero una dispersión considerable: el dominio final por sí solo no determina la nota. Los 2.500 puntos dibujados son una muestra reproducible; el coeficiente utiliza las filas completas del grupo.

Saber 11 global presenta la mayor asociación monotónica numérica con la nota (**ρ = 0,537**), seguido de dominio inicial (**0,497**), dominio final (**0,456**) y Saber 11 matemáticas (**0,428**). La matriz permite además revisar la redundancia entre predictoras: Saber 11 global y matemáticas tienen **ρ = 0,835**; avance y dominio final, **0,843**; dominio inicial y tiempo de pretest, **0,761**; avance y tiempo de trabajo, **0,795**. Avance = final − inicial es una dependencia exacta, más fuerte conceptualmente que cualquier umbral de correlación.

```{figure} images/05_eda_asociaciones.jpg
:alt: Scatter de dominio final frente a nota y matriz de Spearman de las variables numéricas.
:name: eda-asociaciones

Relación entre dominio final y nota, y matriz de asociaciones de Spearman.
```

### Frecuencias, dominio final y distribuciones numéricas

Las asociaciones numéricas se complementan con la revisión de las categorías y de la nota a lo largo de los intervalos de dominio final. Esta parte muestra si los grupos se reparten de forma desigual y si la nota cambia cuando cambia el nivel de dominio.

La frecuencia de cumplimiento se reparte entre **49,3 %** que alcanzó la meta y **50,7 %** que no la alcanzó; la prueba chi-cuadrado de bondad de ajuste no detecta diferencias claras en los conteos (**χ² = 0,2758; gl = 1; p = 0,5995**). La nota por intervalos de dominio final sí cambia: la mediana es **2,60** en el intervalo de 0 a 16 temas y **4,50** en el de 49 a 143 temas (**Kruskal–Wallis H = 261,8282; gl = 3; p < 0,0001**). Los límites de los intervalos provienen de los cuartiles de todo train y se mantienen al filtrar.

```{figure} images/06_eda_dominio.jpg
:alt: Frecuencias de cumplimiento de la meta y cajas de nota por intervalos de dominio final.
:name: eda-dominio

Frecuencias categóricas y nota del primer parcial por intervalos de dominio final.
```

Los nueve histogramas numéricos expresan densidad, con curva KDE sobre todos los valores disponibles, sin imputar ni recortar extremos. Las alturas no se comparan entre variables con unidades diferentes. En la vista general, Saber 11 global tiene 1.309 valores disponibles; el tiempo de pretest, 1.288; el tiempo de trabajo y la tasa de temas por hora, 1.304 cada uno. Las lecturas por variable acompañan cada tarjeta del tablero.

```{figure} images/07_eda_densidades.jpg
:alt: Rejilla de nueve distribuciones numéricas con densidad y prueba de normalidad.
:name: eda-densidades

Distribución y densidad de las ocho predictoras numéricas y de la nota del primer parcial.
```

### Distribuciones categóricas

Las variables categóricas tienen un tratamiento distinto: no se describen con medias ni correlaciones, sino con la proporción de cada categoría dentro del grupo filtrado. Esa lectura permite identificar concentración, categorías poco representadas y diferencias de composición entre grupos.

Las siete variables categóricas se muestran completas: categorías de temas iniciales y finales, programa, división académica, asignatura, cuartiles de avance y cumplimiento de la meta. Cada barra representa la proporción dentro del grupo filtrado; las categorías poco frecuentes se conservan y no se fusionan automáticamente. En la vista general, por ejemplo, la asignatura MAT1101 concentra cerca del **61 %** de las filas y MAT4190 alrededor del **9 %**; programa y división tienen una representación desigual, de modo que el promedio general está más influido por los grupos con más registros.

```{figure} images/08_eda_categoricas.jpg
:alt: Rejilla de siete distribuciones categóricas del entrenamiento válido.
:name: eda-categoricas

Distribución de las siete variables categóricas en train.
```

### Faltantes

La disponibilidad de las mediciones es otra dimensión de la calidad: no todas las variables están completas y el patrón de ausencia puede concentrarse en ciertos tipos de registro. Antes de imputar, conviene identificar dónde falta la información y si las ausencias se reparten de forma homogénea.

Hay **31 celdas faltantes** en el entrenamiento: **21** en tiempo de pretest (**1,6 %**), **5** en tiempo total de trabajo (**0,4 %**) y **5** en tasa de temas aprendidos por hora (**0,4 %**). Son conteos por celda y no necesariamente 31 filas diferentes. Las demás variables no presentan ausencias en esta versión. La prueba Q de Cochran sobre los indicadores de ausencia emparejados rechaza que falten con la misma frecuencia (**Q = 108,7382; gl = 7; p < 0,0001**), pero no identifica el mecanismo ni permite concluir MCAR, MAR o MNAR.

El patrón se concentra en mediciones de tiempo. No se puede concluir que las ausencias sean completamente aleatorias ni confundirlas con ceros de actividad. El modelo usa mediana aprendida en cada fold; EDA conserva los faltantes al describir disponibilidad.

```{figure} images/09_eda_faltantes.jpg
:alt: Porcentaje de ausencias por variable numérica sobre el entrenamiento válido.
:name: eda-faltantes

Porcentaje de faltantes por variable; se calculan sin imputación en EDA.
```

### Conclusiones del EDA y tratamientos

El recorrido anterior se cierra con una síntesis que conecta cada hallazgo con una decisión del pipeline. Esta síntesis es la que se traslada a la preparación del modelo y la que explica por qué se conservan o transforman ciertas variables.

El cierre conecta los gráficos con decisiones: mantener la escala del objetivo, imputar dentro del pipeline, aplicar log1p en tiempos, usar one-hot con referencia y conservar extremos válidos. Son decisiones del análisis global y no se vuelven a seleccionar al filtrar. La nota depende de múltiples características y los gráficos no justifican efectos causales aislados.

La mayor asimetría de tiempos aparece en el tiempo de pretest (**1,779**): sus densidades permiten inspeccionar la cola. Los filtros describen subgrupos y no vuelven a elegir transformaciones. `nota_final` se excluye por ser posterior al parcial. Las reglas de negocio se auditan antes de imputar y se conservan los outliers válidos de los registros reales.

```{figure} images/10_eda_conclusion.jpg
:alt: Conclusión del EDA con media, mediana, asociaciones y tabla de tratamientos del pipeline.
:name: eda-conclusion

Conclusiones del EDA y tratamientos de datos que sustentan el pipeline de E3.
```

## Cómo trasladar la lectura a un filtro

Las secciones anteriores describen la vista general. El tablero también permite acotar el análisis por programa o asignatura, y esa decisión cambia la composición de la muestra. La siguiente lectura explica cómo interpretar ese cambio sin confundirlo con un modelo distinto.

Al elegir programa o asignatura cambian tamaño, distribuciones, asociaciones y errores del grupo seleccionado. El modelo y sus parámetros se mantienen. Conviene leer primero el número de filas, después la forma de la distribución y finalmente las asociaciones. Con menos de 30 filas el tablero señala lectura inestable; con una sola fila o nota constante no calcula R². Una combinación vacía muestra un mensaje y no un resultado cero.

Con el contexto y el EDA documentados, el siguiente capítulo entra en la metodología compartida de separación y validación y en los resultados de los modelos lineales.

---
title: Metodología y detalles adicionales
description: Fórmulas, análisis complementarios del EDA, trazabilidad y límites de generalización.
---

# Metodología y detalles adicionales

Este capítulo amplía lo que aparece en el tablero. Explica el significado de las métricas, las precauciones de la validación, los diagnósticos exploratorios adicionales y las condiciones para reproducir la versión documentada. Los resultados pertenecen a la alternativa 1, perturbación local, y no se mezclan con análisis históricos de otras fuentes.

## Unidad de análisis y dependencia de las observaciones

La separación externa se hace por estudiante: 1.184 estudiantes en train y 297 en test, sin IDs compartidos. Después de aumentar aparecen 24.000 y 6.000 filas, respectivamente. La separación impide que una persona original cruce la frontera externa de entrenamiento/prueba. Sin embargo, dentro de train el esquema final no conserva un identificador que permita agrupar cada estudiante y sus variantes en un solo fold.

Los cinco folds estratifican filas según intervalos de nota. Es posible que variantes cercanas se distribuyan entre folds y hagan optimista la validación interna. La diferencia entre R² de validación y test es compatible con esa limitación, pero no identifica su causa: también pueden intervenir variación de la muestra y diferencias distribucionales. No se puede cuantificar el sesgo sin recuperar trazabilidad de estudiantes y variantes.

El test de 6.000 filas también contiene variantes, generadas exclusivamente desde la partición test. Sus métricas describen esa construcción; no prueban generalización a 6.000 alumnos nuevos. Se preservó un test original de 301 filas de 297 estudiantes para una evaluación posterior. No es el test utilizado en las métricas actuales.

## Fórmulas y lectura de las métricas

Para una nota real $y_i$, predicción $\hat y_i$ y $n$ filas:

$$
\operatorname{MAE}=\frac{1}{n}\sum_{i=1}^{n}|y_i-\hat y_i|,
\qquad
\operatorname{RMSE}=\sqrt{\frac{1}{n}\sum_{i=1}^{n}(y_i-\hat y_i)^2}.
$$

Ambas se expresan en puntos de nota. MAE describe la magnitud absoluta media de los errores; RMSE penaliza más los errores grandes. Ninguna es una garantía de que cada predicción caerá dentro de ese margen.

$$
R^2=1-\frac{\sum_i(y_i-\hat y_i)^2}{\sum_i(y_i-\bar y)^2},
\qquad
\operatorname{MAPE}=\frac{100}{n}\sum_i\left|\frac{y_i-\hat y_i}{y_i}\right|.
$$

R² compara el error cuadrático con la dispersión alrededor de la media de la muestra evaluada. Un valor negativo significa que el predictor falla más que usar esa media como referencia en ese conjunto. Si hay una sola fila o la nota es constante, el tablero muestra R² no definido. MAPE divide por la nota real: para el mismo error absoluto, una nota baja produce un porcentaje mayor. No significa «porcentaje de predicciones incorrectas».

La reducción relativa del RMSE frente a Dummy se obtiene con $100(1-\operatorname{RMSE}_{SVM}/\operatorname{RMSE}_{Dummy})$. La comparación de R² usa otra referencia matemática: la media del conjunto evaluado, mientras que Dummy predice la media aprendida en entrenamiento. Por eso R² de Dummy en test puede ser ligeramente negativo.

## Media de folds y métricas OOF agrupadas

Cada fila de train recibe una predicción de un modelo que no usó esa fila en su ajuste: es una predicción fuera del fold, OOF. Sin filtros, la tabla de validación presenta las medias de métricas por fold para reproducir el notebook. Al filtrar, calcula una métrica sobre todas las predicciones OOF disponibles del grupo.

Promediar RMSE de folds y calcular RMSE de los errores agrupados son operaciones diferentes por la raíz cuadrada. Con R² también cambia el denominador al variar la dispersión de la nota. Las tarjetas OOF usan la métrica agrupada; por ello no se exige que sean idénticas a la media de la tabla. MAE de validación fue añadido por el dashboard a partir de las predicciones guardadas.

La vista filtrada no valida un modelo específico del grupo. Evalúa el modelo global sobre ese subconjunto. Comparar subgrupos con pocas filas o varianza muy distinta puede producir R² inestable y conclusiones que cambian por el denominador, incluso con errores absolutos similares.

## Pipeline y formulación del SVM lineal

Las columnas numéricas se imputan con mediana; las tres medidas de tiempo se transforman con $\log(1+x)$ y todas las numéricas se estandarizan. Las categóricas se imputan con moda y se codifican one-hot con una referencia excluida. Las categorías desconocidas se ignoran en la codificación; el formulario restringe las opciones a las observadas y verifica la combinación institucional.

LinearSVR estima una función lineal en ese espacio transformado:

$$\hat y=\beta_0+\sum_{j=1}^{p}\beta_j z_j.$$

El ajuste emplea $C=1$, $\epsilon=0,1$, `max_iter=20000` y semilla 42. La pérdida con zona de tolerancia y la regularización pertenecen al SVM; no equivalen al ajuste OLS. Los parámetros se mantienen como referencia del proyecto, sin búsqueda de hiperparámetros basada en test.

Un coeficiente numérico se refiere a una unidad estandarizada, no a un punto bruto de Saber 11 ni a una hora. Para los tiempos, además, el cambio es lineal en el logaritmo transformado. Un coeficiente categórico compara su indicador con la referencia y se interpreta junto al resto de indicadores. Las relaciones entre programa/división/asignatura y la identidad avance = dominio final − inicial dificultan atribuir un efecto independiente a cada β.

## Intervalos y diagnósticos

Los intervalos bootstrap del 95 % remuestrean 1.000 veces filas del test aumentado. No son intervalos de predicción individual ni intervalos por estudiante. Las variantes de un mismo original no son independientes, por lo que remuestrear filas puede representar mal la incertidumbre de una población de estudiantes. Una extensión apropiada requeriría remuestreo por estudiante o evaluación de la partición original.

La prueba de normalidad y Breusch–Pagan se calculan sobre los residuos del modelo. Sus p-valores pequeños son diagnósticos de la muestra actual. No son p-valores de los coeficientes, ni certifican efectos causales. Con muchos registros dependientes, la lectura inferencial requiere cautela. El residuo medio permite estudiar sesgo promedio; la curva por intervalos permite detectar sesgos locales que pueden compensarse en el promedio.

La curva de calibración del tablero agrupa por **nota real**, no por predicción. Describe sesgo medio a lo largo de la escala observada; no estima calibración probabilística ni proporciona intervalos de incertidumbre de cada punto.

## Temporalidad y prevención de fuga

El proyecto supone que las 15 predictoras están disponibles antes del primer parcial. Para un uso real hay que comprobar fechas: dominio final, categorías finales y cumplimiento de metas deben conocerse en el momento de pronóstico. Si se desea intervenir antes de terminar el nivelatorio, las variables de salida pueden no estar disponibles y habrá que definir otro modelo con ese horizonte.

`nota_final` es un resultado posterior y se excluye siempre de predictoras y correlaciones. Las variables se imputan, escalan y codifican dentro del pipeline de cada fold. El test no selecciona la técnica de aumentación, transformaciones ni parámetros. Estas precauciones previenen usos directos de información futura; no resuelven por sí solas la dependencia entre variantes.

## Análisis complementarios del EDA

Además de los gráficos del dashboard, el notebook incluye Pearson, información mutua, tamaños de efecto, corrección FDR, redundancia, PCA, detección multivariada de extremos, clustering y una auditoría univariada. Los resúmenes que siguen se leen de `resultados/eda.json`. Su finalidad es ampliar la descripción, no presentar nuevos modelos elegidos con test.

<!-- COMPLEMENTOS_AUTOGENERADOS -->

### Asociaciones lineales, monotónicas e información mutua

Pearson resume relación lineal; Spearman, orden monotónico; la información mutua detecta dependencia más general. Sus magnitudes no son intercambiables y no establecen importancia causal. Los p/q-valores exportados se calculan bajo supuestos que no garantizan independencia de variantes. Un cero numérico puede representar precisión limitada y no probabilidad exactamente cero.

| Variable | Pearson | Spearman | Información mutua | Pares |
| --- | --- | --- | --- | --- |
| Saber 11 · global | 0,4939 | 0,5281 | 0,3234 | 24000 |
| Saber 11 · matemáticas | 0,3400 | 0,4075 | 0,2327 | 24000 |
| Tiempo de pretest (horas) | 0,3272 | 0,3603 | 0,2099 | 23574 |
| Dominio inicial (temas) | 0,3342 | 0,4683 | 0,2414 | 24000 |
| Avance en ALEK (temas) | 0,2996 | 0,2978 | 0,2548 | 24000 |
| Dominio final (temas) | 0,4223 | 0,4633 | 0,5915 | 24000 |
| Tiempo de trabajo (horas) | 0,0660 | 0,0662 | 0,1839 | 23939 |
| Temas aprendidos por hora | 0,3286 | 0,3768 | 0,2157 | 23939 |


### Diferencias categóricas y tamaños de efecto

El EDA compara nota entre categorías con Kruskal–Wallis, eta² y epsilon². Estos tamaños describen separación de distribuciones en train; no son el R² del SVM. El resultado depende de la composición de grupos y la generación sintética. Categorías iniciales/finales aportan separación mayor que las variables institucionales, sin que ello identifique un mecanismo causal.

| Categoría | Grupos | eta² | epsilon² |
| --- | --- | --- | --- |
| Categoría de temas iniciales | 11 | 0,2398 | 0,2434 |
| Categoría de temas finales | 12 | 0,2223 | 0,2303 |
| Cumplimiento de la meta | 2 | 0,1525 | 0,1547 |
| Categoría de avance por cuartiles | 16 | 0,1279 | 0,1276 |
| Programa | 16 | 0,0635 | 0,0580 |
| División académica | 6 | 0,0257 | 0,0275 |
| Asignatura | 4 | 0,0230 | 0,0237 |


### Dependencia categórica y categorías poco representadas

Programa/división, asignatura/cuartiles y categoría final/cumplimiento presentan V de Cramér cercana a uno en las exportaciones. Reflejan asociaciones estructurales entre las etiquetas. No deben tratarse como siete fuentes totalmente independientes de información. Algunas tablas contienen celdas con frecuencias esperadas pequeñas, lo que debilita aproximaciones asintóticas de chi-cuadrado.

La auditoría marca **19 categorías poco representadas** bajo su criterio. Se conservan; esa cifra no es el número de variables ni justifica fusionar categorías con significado distinto.


### Redundancia y VIF

La correlación elevada de Saber 11 global/Matemáticas y avance/dominio final se combina con la identidad exacta entre avance y ambos dominios. El notebook calcula indicadores VIF usando pseudoinversa; con dependencia exacta no equivalen a los VIF clásicos finitos y no permiten certificar ausencia de multicolinealidad. Por esa razón no se usa un umbral de la tabla como prueba para interpretar β por separado.


### PCA y dimensionalidad

La codificación exploratoria tiene **75 columnas**. Se requieren **8 componentes** para explicar 80 % de su variación, **14** para 90 % y **21** para 95 %. Son proporciones de variación de las características codificadas, no de la nota. PCA no se incorpora como transformación del SVM documentado.


### Extremos multivariados

Mahalanobis marca **1281 filas**, Isolation Forest **823** y ambos métodos coinciden en **451**. Las etiquetas dependen del método y sus parámetros. Un extremo multivariado no es automáticamente un error de datos; se conservan todas las filas que cumplen las reglas de negocio. La ausencia de extremos IQR en la nota tampoco impide extremos en otras dimensiones.


### Clustering exploratorio

El análisis de clusters usa una muestra de 10.000 filas de train, como se verifica sumando los tamaños en k = 2. Se comparan entre dos y seis grupos. Las siluetas cercanas a 0,2 sugieren separación modesta; no certifican perfiles académicos naturales ni grupos de riesgo. El valor preferido por silueta es una descripción de esa muestra y no se usa para reentrenar por cluster.

| k | Silueta | Tamaño mínimo | Tamaño máximo |
| --- | --- | --- | --- |
| 2 | 0,2272 | 4938 | 5062 |
| 3 | 0,2262 | 1746 | 4562 |
| 4 | 0,2074 | 1231 | 4479 |
| 5 | 0,1804 | 1199 | 2788 |
| 6 | 0,1920 | 1136 | 2764 |


### Auditoría univariada y disponibilidad temporal

La auditoría estudia cada variable por separado. No selecciona un nuevo modelo final, ni sus R² univariados se suman. `nota_final` tiene asociación elevada, pero se descarta por temporalidad. Ese contraste muestra por qué una variable puede predecir bien y seguir siendo inadmisible para el objetivo. Los valores siguientes pertenecen exclusivamente a la auditoría; nota_final no se usó en la matriz activa ni el SVM.

| Variable auditada | R² OOF univariado medio | Disponibilidad | Alerta |
| --- | --- | --- | --- |
| nota_final | 0,6885 | descartar | Sí |
| Icfes_nuevo | 0,2793 | disponible antes del primer parcial | No |
| Dominio_Final | 0,2642 | disponible antes del primer parcial | No |
| Categoria_temas_inicial | 0,2393 | disponible antes del primer parcial | No |
| Dominio_Inicial | 0,2249 | disponible antes del primer parcial | No |
| Categoria_temas_final | 0,2216 | disponible antes del primer parcial | No |
| Icfes_Matematicas | 0,1799 | disponible antes del primer parcial | No |
| Tiempo_total_Aprendidos_hora | 0,1654 | disponible antes del primer parcial | No |
| cumplimiento_temas | 0,1523 | disponible antes del primer parcial | No |
| Tiempo_empleado_en_la_verificación_de_conocimientos | 0,1464 | disponible antes del primer parcial | No |
| avance_cuartiles | 0,1267 | disponible antes del primer parcial | No |
| avance_precalculo_aleks | 0,1152 | disponible antes del primer parcial | No |
| programa_en_matricula | 0,0618 | disponible antes del primer parcial | No |
| division_en_matricula | 0,0249 | disponible antes del primer parcial | No |
| Mat_Curso_Asignatura_Relacionada | 0,0223 | disponible antes del primer parcial | No |
| Tiempo_Total_Tiempo | 0,0171 | disponible antes del primer parcial | No |

<!-- FIN_COMPLEMENTOS_AUTOGENERADOS -->

## Reporte completo del modelo

El cuadro siguiente conserva intercepto, todos los coeficientes estimados y las siete referencias categóricas. Una referencia con β = 0 significa que se excluyó esa columna para codificar la comparación; no significa ausencia de asociación ni un efecto estimado exactamente nulo. LinearSVR no entrega errores estándar o p-valores para estos términos.

<!-- COEFICIENTES_AUTOGENERADOS -->

| Variable / término | β | Rol |
| --- | --- | --- |
| Intercepto (β₀) | 1,6554 | Intercepto estimado |
| num_log__Tiempo_empleado_en_la_verificación_de_conocimientos | 0,1470 | Coeficiente estimado |
| num_log__Tiempo_Total_Tiempo | -0,2234 | Coeficiente estimado |
| num_log__Tiempo_total_Aprendidos_hora | 0,0912 | Coeficiente estimado |
| num_plain__Icfes_nuevo | 0,5121 | Coeficiente estimado |
| num_plain__Icfes_Matematicas | -0,1507 | Coeficiente estimado |
| num_plain__Dominio_Inicial | 0,1396 | Coeficiente estimado |
| num_plain__avance_precalculo_aleks | 0,2530 | Coeficiente estimado |
| num_plain__Dominio_Final | 0,2735 | Coeficiente estimado |
| cat__Categoria_temas_inicial_1 Geometría | 0,2559 | Coeficiente estimado |
| cat__Categoria_temas_inicial_1 Repaso de álgebra y geometría | 0,2900 | Coeficiente estimado |
| cat__Categoria_temas_inicial_2 Ecuaciones racionales que se reducen a lineales | 0,2136 | Coeficiente estimado |
| cat__Categoria_temas_inicial_2 Ecuaciones y desigualdades | 0,2131 | Coeficiente estimado |
| cat__Categoria_temas_inicial_3 Gráficos y funciones | 0,6092 | Coeficiente estimado |
| cat__Categoria_temas_inicial_3 Plano de coordenadas, distancia y punto medio | -0,6617 | Coeficiente estimado |
| cat__Categoria_temas_inicial_3 Temas Parcial 1 Cálculo I | 0,1250 | Coeficiente estimado |
| cat__Categoria_temas_inicial_4 Funciones polinómicas y racionales | 0,0059 | Coeficiente estimado |
| cat__Categoria_temas_inicial_4 Pendientes y ecuaciones de rectas | 0,1280 | Coeficiente estimado |
| cat__Categoria_temas_inicial_4 Temas Parcial 2 Cálculo I | -0,0981 | Coeficiente estimado |
| cat__Categoria_temas_final_1 Geometría | 0,4207 | Coeficiente estimado |
| cat__Categoria_temas_final_1 Repaso de Álgebra y Geometría | -0,4248 | Coeficiente estimado |
| cat__Categoria_temas_final_2 Ecuaciones racionales que se reducen a lineales | 0,8395 | Coeficiente estimado |
| cat__Categoria_temas_final_2 Ecuaciones y desigualdades | -0,1601 | Coeficiente estimado |
| cat__Categoria_temas_final_3 Gráficos y funciones | -1,5892 | Coeficiente estimado |
| cat__Categoria_temas_final_3 Plano de coordenadas, distancia y punto medio | -0,2784 | Coeficiente estimado |
| cat__Categoria_temas_final_3 Temas Parcial 1 Cálculo I | 0,8103 | Coeficiente estimado |
| cat__Categoria_temas_final_4 Funciones polinómicas y racionales | -0,8924 | Coeficiente estimado |
| cat__Categoria_temas_final_4 Pendientes y ecuaciones de rectas | -0,1057 | Coeficiente estimado |
| cat__Categoria_temas_final_4 Temas Parcial 2 Cálculo I | 0,6516 | Coeficiente estimado |
| cat__Categoria_temas_final_5 Funciones trigonométricas | -0,5389 | Coeficiente estimado |
| cat__programa_en_matricula_Arquitectura | 0,8761 | Coeficiente estimado |
| cat__programa_en_matricula_Básico Negoc Internacionales | 0,2457 | Coeficiente estimado |
| cat__programa_en_matricula_Ciencia de Datos | 0,1989 | Coeficiente estimado |
| cat__programa_en_matricula_Contaduría Pública | 0,5179 | Coeficiente estimado |
| cat__programa_en_matricula_Curso libre pregrado | -0,6929 | Coeficiente estimado |
| cat__programa_en_matricula_Economía | 0,2816 | Coeficiente estimado |
| cat__programa_en_matricula_Geología | -0,1502 | Coeficiente estimado |
| cat__programa_en_matricula_Ingeniería Civil | 0,0992 | Coeficiente estimado |
| cat__programa_en_matricula_Ingeniería Electrónica | -0,0455 | Coeficiente estimado |
| cat__programa_en_matricula_Ingeniería Eléctrica | -0,2631 | Coeficiente estimado |
| cat__programa_en_matricula_Ingeniería Industrial | 0,3799 | Coeficiente estimado |
| cat__programa_en_matricula_Ingeniería Mecánica | 0,0882 | Coeficiente estimado |
| cat__programa_en_matricula_Ingeniería Sistemas Y Computac | 0,0170 | Coeficiente estimado |
| cat__programa_en_matricula_Matemáticas | 0,2717 | Coeficiente estimado |
| cat__programa_en_matricula_Negocios Internacionales | 0,0323 | Coeficiente estimado |
| cat__division_en_matricula_Div Humanidades, Artes y Cs. S | 0,2816 | Coeficiente estimado |
| cat__division_en_matricula_División de Ciencias Básicas | 0,3204 | Coeficiente estimado |
| cat__division_en_matricula_División de Ingenierías | 0,2757 | Coeficiente estimado |
| cat__division_en_matricula_Escuela Arquitectura Urb y Dis | 0,8761 | Coeficiente estimado |
| cat__division_en_matricula_Escuela de Negocios | 0,3488 | Coeficiente estimado |
| cat__Mat_Curso_Asignatura_Relacionada_MAT1100 | 0,8761 | Coeficiente estimado |
| cat__Mat_Curso_Asignatura_Relacionada_MAT1101 | 0,3087 | Coeficiente estimado |
| cat__Mat_Curso_Asignatura_Relacionada_MAT4190 | -0,4055 | Coeficiente estimado |
| cat__avance_cuartiles_0 Avance menor a 18 temas | 0,3283 | Coeficiente estimado |
| cat__avance_cuartiles_0 Avance menor a 19 temas | 0,1586 | Coeficiente estimado |
| cat__avance_cuartiles_0 Avance menor a 25 temas | 0,1405 | Coeficiente estimado |
| cat__avance_cuartiles_1 Avance entre [ 15 - 23 temas] | -0,4109 | Coeficiente estimado |
| cat__avance_cuartiles_1 Avance entre [ 18 - 37 temas] | 0,3572 | Coeficiente estimado |
| cat__avance_cuartiles_1 Avance entre [ 19 - 40 temas] | 0,0606 | Coeficiente estimado |
| cat__avance_cuartiles_1 Avance entre [ 25 - 55 temas] | -0,3626 | Coeficiente estimado |
| cat__avance_cuartiles_2 Avance entre [ 23 - 29 temas] | 0,4578 | Coeficiente estimado |
| cat__avance_cuartiles_2 Avance entre [ 37 - 55 temas] | 0,2367 | Coeficiente estimado |
| cat__avance_cuartiles_2 Avance entre [ 40 - 60 temas] | -0,0525 | Coeficiente estimado |
| cat__avance_cuartiles_2 Avance entre [ 55 - 80 temas] | -0,0886 | Coeficiente estimado |
| cat__avance_cuartiles_3 Avance superior a 29 temas | 0,8108 | Coeficiente estimado |
| cat__avance_cuartiles_3 Avance superior a 55 temas | -0,0462 | Coeficiente estimado |
| cat__avance_cuartiles_3 Avance superior a 60 temas | 0,1420 | Coeficiente estimado |
| cat__avance_cuartiles_3 Avance superior a 80 temas | -0,0948 | Coeficiente estimado |
| cat__cumplimiento_temas_No alcanzo meta | 0,8381 | Coeficiente estimado |
| Categoria_temas_inicial = 0 No dominó temas | 0,0000 | Categoría de referencia: fijado en 0 |
| Categoria_temas_final = 0 No dominó temas | 0,0000 | Categoría de referencia: fijado en 0 |
| programa_en_matricula = Administración de Empresas | 0,0000 | Categoría de referencia: fijado en 0 |
| division_en_matricula = Centro de Educ. Continuada | 0,0000 | Categoría de referencia: fijado en 0 |
| Mat_Curso_Asignatura_Relacionada = MAT1011 | 0,0000 | Categoría de referencia: fijado en 0 |
| avance_cuartiles = 0 Avance menor a 15 temas | 0,0000 | Categoría de referencia: fijado en 0 |
| cumplimiento_temas = Cumplimiento meta | 0,0000 | Categoría de referencia: fijado en 0 |

<!-- FIN_COEFICIENTES_AUTOGENERADOS -->

## Trazabilidad, privacidad y reproducción

`source_manifest.json` registra hashes SHA-256 de los resultados, la selección, los datos preparados, el modelo y el código utilizados para escribir este informe, junto con los hashes de las capturas. Permite identificar el corte documentado sin incluir la base bruta de nombres y correos. Una captura congela una vista de la interfaz; no responde a cambios posteriores en los filtros o los datos.

En el espacio local completo se utiliza únicamente `Precalculo/venv/`. Si cambian las fuentes, el orden de trabajo es: actualizar el análisis, preparar la caché de Dash, ejecutar pruebas, capturar las vistas y regenerar este informe. Construir el HTML no ejecuta el modelo ni los notebooks:

```powershell
# Desde la raíz del espacio de trabajo:
.\Precalculo\venv\Scripts\python.exe .\Precalculo\actualizar_analisis.py
.\Precalculo\venv\Scripts\python.exe .\Dash\prepare_data.py
.\Precalculo\venv\Scripts\python.exe .\Dash\test_dashboard.py
# Después de actualizar capturas y textos:
Set-Location .\jbook_dashboard
$env:BASE_URL = '/jbook_ml202630_2'
..\Precalculo\venv\Scripts\jupyter-book.exe build --html --strict
```

El informe público y el dashboard comparten repositorio, pero tienen ejecuciones diferentes: GitHub Pages sirve HTML/CSS/imágenes estáticas y Render sirve Dash con Gunicorn. Los outputs `_build/`, los contextos, los archivos AGENTS y los scripts internos no se versionan. La construcción automática del Book utiliza solo sus Markdown y assets.

## Trabajo pendiente antes de un uso operativo

| Pendiente | Qué resolvería | Condición de evaluación |
| --- | --- | --- |
| Evaluar las 301 filas originales de test | Rendimiento sin inflar la muestra con variantes | Modelo fijado antes de consultar resultados |
| Recuperar IDs persistentes de originales y variantes | Folds y bootstrap agrupados por estudiante | Mantener separados estudiantes de train/test |
| Validar en periodos posteriores | Generalización temporal | Definir horizonte y disponibilidad de predictoras |
| Comparar otras familias de modelos | Posible mejora de patrones no lineales | Seleccionar dentro de train, reservando evaluación final |
| Revisar errores por asignatura y programa | Detectar desempeño desigual | Reportar tamaño y composición real de cada grupo |
| Evaluar incertidumbre individual | Expresar confianza de una predicción | Método calibrado sobre observaciones independientes |

El resultado actual es una referencia académica reproducible y una herramienta de exploración. No establece que aumentar datos mejore el aprendizaje real ni que un cambio en una variable vaya a causar una mejora en la nota. Una intervención o decisión individual requeriría evidencia adicional, revisión institucional y validación externa.

## Fuentes para ampliar la lectura

- [LinearSVR: documentación de scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.svm.LinearSVR.html).
- [Métricas de regresión: documentación de scikit-learn](https://scikit-learn.org/stable/modules/model_evaluation.html#regression-metrics).
- [Validación cruzada y grupos: documentación de scikit-learn](https://scikit-learn.org/stable/modules/cross_validation.html).
- [Publicación de Jupyter Book en GitHub Pages](https://jupyterbook.org/stable/get-started/publish/).
- [MyST: rutas base y publicación estática](https://mystmd.org/guide/deployment).
- [Resultados canónicos de EDA](https://github.com/r041292/jbook_ml202630_2/blob/main/Precalculo/resultados/eda.json) y [modelos lineales](https://github.com/r041292/jbook_ml202630_2/blob/main/Precalculo/resultados/modelos_lineales.json).

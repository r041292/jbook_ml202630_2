---
title: Metodología y detalles adicionales
description: Fórmulas, validación, diagnósticos del EDA y límites de generalización del flujo E3.
---

# Metodología y detalles adicionales

Este capítulo amplía lo que aparece en el tablero. Explica el significado de las métricas, las precauciones de la validación agrupada, los diagnósticos exploratorios adicionales y las condiciones para reproducir la versión documentada. Los resultados corresponden al flujo E3 con datos reales y al modelo lineal que sirve de referencia.

El capítulo se organiza en cuatro bloques: la unidad de análisis y las fórmulas; el pipeline y los diagnósticos; los análisis complementarios del EDA; y la trazabilidad, el trabajo pendiente y las fuentes.

## Unidad de análisis y dependencia de las observaciones

La separación externa se hace por estudiante y por periodo: **1.309 registros de 1.293 estudiantes** en train (202310–202510) y **188 registros de 188 estudiantes** en test (202530), sin identificadores compartidos. El test es temporal y cada estudiante aparece una sola vez en él.

Dentro de train, GroupKFold mantiene juntas todas las filas de una persona en cada fold. La validación externa separa estudiantes, pero no estratifica por nota ni impone orden temporal: la evaluación en un periodo posterior la aporta el test reservado. Las métricas se calculan por registro; agrupar no asigna automáticamente el mismo peso a cada estudiante si tiene varias filas. En el dashboard se reporta la media de las métricas de los cinco folds externos cuando no hay filtros.

Antes de interpretar los resultados conviene fijar qué mide cada métrica y cómo se relaciona con la escala de la nota.

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

Una misma métrica puede resumirse de dos maneras: promediando folds o agrupando predicciones. Esta sección explica por qué no son intercambiables.

## Media de folds y métricas OOF agrupadas

Cada fila de train recibe una predicción de un modelo que no usó esa fila en su ajuste: es una predicción fuera del fold, OOF. Sin filtros, la tabla de validación presenta las medias de métricas por fold para reproducir el análisis. Al filtrar, calcula una métrica sobre todas las predicciones OOF disponibles del grupo.

Promediar RMSE de folds y calcular RMSE de los errores agrupados son operaciones diferentes por la raíz cuadrada. Con R² también cambia el denominador al variar la dispersión de la nota. Las tarjetas OOF usan la métrica agrupada; por ello no se exige que sean idénticas a la media de la tabla. MAE de validación fue añadido por el dashboard a partir de las predicciones guardadas.

La vista filtrada no valida un modelo específico del grupo. Evalúa el modelo global sobre ese subconjunto. Comparar subgrupos con pocas filas o varianza muy distinta puede producir R² inestable y conclusiones que cambian por el denominador, incluso con errores absolutos similares.

Con las métricas definidas, el siguiente paso es describir el modelo que las produce y el espacio en el que se ajusta.

## Pipeline y formulación del SVM lineal

Las columnas numéricas se imputan con mediana; las tres medidas de tiempo se transforman con $\log(1+x)$ y todas las numéricas se estandarizan. Las categóricas se imputan con moda y se codifican one-hot con una referencia excluida. Las categorías desconocidas se ignoran en la codificación; el formulario restringe las opciones a las observadas y verifica la combinación institucional. El ajuste final produce 67 columnas transformadas.

LinearSVR estima una función lineal en ese espacio transformado:

$$\hat y=\beta_0+\sum_{j=1}^{p}\beta_j z_j.$$

El ajuste final emplea $C=0{,}2438$, $\epsilon=0{,}5130$, `max_iter=1000000`, `tol=1e-4` y semilla 42. La pérdida con zona de tolerancia y la regularización pertenecen al SVM; no equivalen al ajuste OLS. Los parámetros se eligieron por RMSE interno con GroupKFold anidado, comparando Grid Search, Random Search, Optuna/TPE, DEAP y Successive Halving. El test no participó en la selección.

Un coeficiente numérico se refiere a una unidad estandarizada, no a un punto bruto de Saber 11 ni a una hora. Para los tiempos, además, el cambio es lineal en el logaritmo transformado. Un coeficiente categórico compara su indicador con la referencia y se interpreta junto al resto de indicadores. Las relaciones entre programa/división/asignatura y la identidad avance = dominio final − inicial dificultan atribuir un efecto independiente a cada β.

Las métricas puntuales se complementan con intervalos y diagnósticos que describen la estabilidad y el comportamiento de los residuos.

## Intervalos y diagnósticos

Los intervalos bootstrap del 95 % remuestrean 1.000 veces **por estudiante** en el test: los registros de una misma persona se remuestrean juntos. Para el SVM, RMSE **[0,8416; 1,0175]**, MAPE **[23,9972 %; 36,4560 %]** y R² **[0,3185; 0,5079]**. No son intervalos de predicción individual ni intervalos por estudiante; describen esta muestra y no sustituyen una evaluación externa.

La prueba de normalidad y Breusch–Pagan se calculan sobre los residuos del modelo. Sus p-valores pequeños son diagnósticos de la muestra actual. No son p-valores de los coeficientes, ni certifican efectos causales. Con registros repetidos por estudiante, la lectura inferencial requiere cautela. El residuo medio permite estudiar sesgo promedio; la curva por intervalos permite detectar sesgos locales que pueden compensarse en el promedio.

White evalúa la constancia de la varianza de los errores (homocedasticidad) usando las ocho predictoras numéricas originales, con constante, cuadrados e interacciones; no incluye las categóricas. BDS evalúa la independencia de los residuos y su hipótesis incluye también que tengan la misma distribución (IID). En validación, los residuos OOF reúnen cinco ajustes distintos y no forman una trayectoria temporal individual. Un p mayor no demuestra que los supuestos se cumplan.

La curva de calibración agrupa por **nota real**, no por predicción. Describe sesgo medio a lo largo de la escala observada; no estima calibración probabilística ni proporciona intervalos de incertidumbre de cada punto.

Además de la validación, el informe debe explicar qué información estaba disponible en el momento del pronóstico.

## Temporalidad y prevención de fuga

El proyecto supone que las 15 predictoras están disponibles antes del primer parcial. Para un uso real hay que comprobar fechas: dominio final, categorías finales y cumplimiento de metas deben conocerse en el momento de pronóstico. Si se desea intervenir antes de terminar el nivelatorio, las variables de salida pueden no estar disponibles y habrá que definir otro modelo con ese horizonte.

`nota_final` es un resultado posterior y se excluye siempre de predictoras y correlaciones. Las variables se imputan, escalan y codifican dentro del pipeline de cada fold. El test no selecciona transformaciones ni parámetros. Estas precauciones previenen usos directos de información futura.

El EDA del tablero se complementa con un conjunto de contrastes y resúmenes que no siempre aparecen en las figuras principales. Esta sección los documenta.

## Análisis complementarios del EDA

El reporte `Precalculo/resultados/e3/eda.json` resume el perfil numérico y las correlaciones de Spearman sobre train válido. El dashboard añade contrastes calculados en tiempo de ejecución sobre el subgrupo filtrado: Shapiro–Wilk para normalidad marginal, Kruskal–Wallis para diferencias entre grupos, chi-cuadrado de bondad de ajuste para frecuencias categóricas y Q de Cochran para ausencias emparejadas. No se imputan valores para EDA ni se usa test en estos contrastes.

El perfil numérico resume la posición y la dispersión de cada variable antes de cualquier transformación.

### Perfil numérico

| Variable | n | Media | Desv. | Mediana | Mín. | Máx. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Saber 11 · global | 1.309 | 341,157 | 47,900 | 345 | 0 | 477 |
| Saber 11 · matemáticas | 1.309 | 68,474 | 10,210 | 69 | 0 | 100 |
| Tiempo de pretest (horas) | 1.288 | 0,737 | 0,614 | 0,533 | 0,017 | 4,600 |
| Dominio inicial (temas) | 1.309 | 9,038 | 16,169 | 2 | 0 | 140 |
| Avance en ALEK (temas) | 1.309 | 27,513 | 20,387 | 26 | 0 | 121 |
| Dominio final (temas) | 1.309 | 36,552 | 27,169 | 32 | 0 | 143 |
| Tiempo de trabajo (horas) | 1.304 | 18,045 | 12,615 | 16,033 | 0 | 122,450 |
| Temas aprendidos por hora | 1.304 | 1,554 | 0,914 | 1,440 | 0 | 6,938 |
| Nota del primer parcial | 1.309 | 3,499 | 1,118 | 3,700 | 0,500 | 5,000 |

Hay **31 celdas faltantes**: 21 en tiempo de pretest, 5 en tiempo de trabajo y 5 en temas aprendidos por hora. El resumen por celda no implica 31 filas distintas. `nota_final` no aparece en el perfil activo ni en la matriz de correlaciones.

El perfil se complementa con la matriz de Spearman, que describe tanto la relación con la nota como la información compartida entre predictoras.

### Asociaciones y redundancia

La matriz de Spearman sobre train muestra las asociaciones con la nota y entre predictoras. Los valores siguientes se leen de `eda.json`.

| Variable | ρ con la nota |
| --- | ---: |
| Saber 11 · global | 0,537 |
| Dominio inicial (temas) | 0,497 |
| Dominio final (temas) | 0,456 |
| Saber 11 · matemáticas | 0,428 |
| Temas aprendidos por hora | 0,382 |
| Tiempo de pretest (horas) | 0,365 |
| Avance en ALEK (temas) | 0,288 |
| Tiempo de trabajo (horas) | 0,053 |

Entre predictoras destacan Saber 11 global/matemáticas (**0,835**), avance/dominio final (**0,843**), avance/tiempo de trabajo (**0,795**) y dominio inicial/tiempo de pretest (**0,761**). La identidad avance = dominio final − inicial es una dependencia exacta. Estas relaciones ayudan a interpretar los coeficientes en conjunto; no justifican eliminar variables por sí solas.

La nube del tablero compara Spearman con Pearson mediante una diferencia Δ = ρ − r y un bootstrap pareado sobre los mismos registros. No es un contraste de superioridad entre métodos. La matriz presenta ρ, n, p bilateral y p ajustado por Holm; el ajuste cubre los pares de la vista actual y no la exploración de muchos filtros. Los p asumen registros independientes y no corrigen la dependencia por estudiante.

Los contrastes siguientes resumen la evidencia estadística que el tablero muestra al aplicar los filtros.

### Contrastes visibles en la vista general

- **Normalidad de la nota:** Shapiro–Wilk W = 0,9458; p < 0,0001; n = 1.309.
- **Diferencias por asignatura:** Kruskal–Wallis H = 19,9458; gl = 3; p = 0,0002.
- **Diferencias por dominio final:** Kruskal–Wallis H = 261,8282; gl = 3; p < 0,0001.
- **Cumplimiento de la meta:** χ² = 0,2758; gl = 1; p = 0,5995.
- **Ausencias emparejadas:** Q de Cochran = 108,7382; gl = 7; p < 0,0001.

Son resultados exploratorios: algunos estudiantes pueden tener más de un registro y aquí no se corrige esa dependencia. Los contrastes categóricos usan la uniformidad como referencia descriptiva; el rechazo de la uniformidad no exige equilibrio institucional. Q es asintótico y pierde precisión con ausencias raras. No se interpreta un resultado no significativo como equivalencia o normalidad.

Además de los doce coeficientes principales, el modelo completo permite revisar todos los términos y las referencias.

## Reporte completo del modelo

El reporte conserva el intercepto, todos los coeficientes estimados y las siete referencias categóricas. Una referencia con β = 0 significa que se excluyó esa columna para codificar la comparación; no significa ausencia de asociación. Los términos se ordenan por magnitud absoluta y las referencias quedan al final.

| Variable / término | β | Rol |
| --- | ---: | --- |
| Intercepto (β₀) | 1,7552 | Intercepto estimado |
| `Mat_Curso_Asignatura_Relacionada_MAT1100` | 0,7894 | Coeficiente estimado |
| `Categoria_temas_final_4 Temas Parcial 2 Cálculo I` | 0,6594 | Coeficiente estimado |
| `Categoria_temas_final_3 Temas Parcial 1 Cálculo I` | 0,6416 | Coeficiente estimado |
| `cumplimiento_temas_No alcanzo meta` | 0,5508 | Coeficiente estimado |
| `Categoria_temas_inicial_1 Geometría` | 0,5383 | Coeficiente estimado |
| `programa_en_matricula_Arquitectura` | 0,5383 | Coeficiente estimado |
| `division_en_matricula_Escuela Arquitectura Urb y Dis` | 0,5383 | Coeficiente estimado |
| `num_plain__Icfes_nuevo` | 0,5008 | Coeficiente estimado |
| `Categoria_temas_final_3 Gráficos y funciones` | −0,4602 | Coeficiente estimado |
| `Mat_Curso_Asignatura_Relacionada_MAT1101` | 0,4517 | Coeficiente estimado |
| `division_en_matricula_Escuela de Negocios` | 0,4517 | Coeficiente estimado |
| `num_log__Tiempo_Total_Tiempo` | −0,2604 | Coeficiente estimado |
| `num_plain__Dominio_Final` | 0,2115 | Coeficiente estimado |
| `num_plain__avance_precalculo_aleks` | 0,2026 | Coeficiente estimado |
| `num_plain__Icfes_Matematicas` | −0,1604 | Coeficiente estimado |
| `num_log__Tiempo_empleado_en_la_verificación_de_conocimientos` | 0,1092 | Coeficiente estimado |
| `num_plain__Dominio_Inicial` | 0,1000 | Coeficiente estimado |
| `num_log__Tiempo_total_Aprendidos_hora` | 0,0799 | Coeficiente estimado |
| `Categoria_temas_inicial = 0 No dominó temas` | 0,0000 | Categoría de referencia |
| `Categoria_temas_final = 0 No dominó temas` | 0,0000 | Categoría de referencia |
| `programa_en_matricula = Administración de Empresas` | 0,0000 | Categoría de referencia |
| `division_en_matricula = Centro de Educ. Continuada` | 0,0000 | Categoría de referencia |
| `Mat_Curso_Asignatura_Relacionada = MAT1011` | 0,0000 | Categoría de referencia |
| `avance_cuartiles = 0 Avance menor a 15 temas` | 0,0000 | Categoría de referencia |
| `cumplimiento_temas = Cumplimiento meta` | 0,0000 | Categoría de referencia |

El CSV completo y el reporte descargable están disponibles en el dashboard. LinearSVR no entrega errores estándar ni p-valores para estos términos; no se les atribuye inferencia de OLS.

Para que el informe sea reproducible, es necesario registrar qué fuentes y artefactos produjeron cada cifra.

## Trazabilidad, privacidad y reproducción

`source_manifest.json` registra hashes SHA-256 de los resultados, los datos preparados, el modelo y las capturas utilizadas para escribir este informe. Permite identificar el corte documentado sin incluir la base bruta de nombres y correos. Una captura congela una vista de la interfaz; no responde a cambios posteriores en los filtros o los datos.

En el espacio local completo se utiliza únicamente `Precalculo/venv/`. Si cambian las fuentes, el orden de trabajo es: actualizar el análisis, preparar la caché de Dash, ejecutar pruebas, capturar las vistas y regenerar este informe. Construir el HTML no ejecuta el modelo ni los notebooks:

```powershell
# Desde la raíz del espacio de trabajo:
.\Precalculo\venv\Scripts\python.exe .\Precalculo\entregable3.py
.\Precalculo\venv\Scripts\python.exe .\Dash\prepare_data.py
.\Precalculo\venv\Scripts\python.exe -m unittest discover -s Dash -p 'test_*.py'
# Después de actualizar capturas y textos:
Set-Location .\jbook_dashboard
$env:BASE_URL = '/jbook_ml202630_2'
..\Precalculo\venv\Scripts\jupyter-book.exe build --html --strict
```

El informe público y el dashboard comparten repositorio, pero tienen ejecuciones diferentes: GitHub Pages sirve HTML/CSS/imágenes estáticas y Render sirve Dash con Gunicorn. Los outputs `_build/`, los contextos, los archivos AGENTS y los scripts internos no se versionan. La construcción automática del Book utiliza solo sus Markdown y assets.

Los resultados actuales son una referencia académica; esta sección explicita qué falta antes de un uso operativo.

## Trabajo pendiente antes de un uso operativo

| Pendiente | Qué resolvería | Condición de evaluación |
| --- | --- | --- |
| Ampliar la evaluación temporal | Generalización a otros periodos y cohortes | Definir horizonte y disponibilidad de predictoras |
| Revisar estabilidad por estudiante | Confirmar el desempeño fuera de los folds actuales | Mantener separados estudiantes de train/test |
| Comparar otras familias de modelos | Posible mejora de patrones no lineales | Seleccionar dentro de train, reservando evaluación final |
| Revisar errores por asignatura y programa | Detectar desempeño desigual | Reportar tamaño y composición real de cada grupo |
| Evaluar incertidumbre individual | Expresar confianza de una predicción | Método calibrado sobre observaciones independientes |
| Comprobar la disponibilidad temporal de las variables | Evitar fuga en un uso real | Verificar fechas de cada predictora antes del parcial |

El resultado actual es una referencia académica reproducible y una herramienta de exploración. No establece que una intervención educativa vaya a causar una mejora en la nota. Una decisión individual requeriría evidencia adicional, revisión institucional y validación externa.

Las siguientes referencias permiten ampliar la lectura metodológica y verificar las definiciones usadas.

## Fuentes para ampliar la lectura

- [LinearSVR: documentación de scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.svm.LinearSVR.html).
- [Métricas de regresión: documentación de scikit-learn](https://scikit-learn.org/stable/modules/model_evaluation.html#regression-metrics).
- [Validación cruzada y grupos: documentación de scikit-learn](https://scikit-learn.org/stable/modules/cross_validation.html).
- [Publicación de Jupyter Book en GitHub Pages](https://jupyterbook.org/stable/get-started/publish/).
- [MyST: rutas base y publicación estática](https://mystmd.org/guide/deployment).
- [Resultados canónicos de EDA](https://github.com/r041292/jbook_ml202630_2/blob/main/Precalculo/resultados/e3/eda.json) y [modelos lineales](https://github.com/r041292/jbook_ml202630_2/blob/main/Precalculo/resultados/e3/modelos_lineales.json).

---
title: Modelos benchmark
description: Definición de los siete modelos base, cinco estrategias de búsqueda en validación anidada, tabla maestra de mejores combinaciones con media ± DE, tiempos y serialización.
---

(sec-benchmarks)=
# Modelos benchmark

Este capítulo responde al Bloque B de la guía: para cada uno de los **siete modelos base** se elige la mejor combinación de método de optimización e hiperparámetros con un criterio estadístico —la métrica media del bucle externo de la validación anidada—, se identifica la mejor combinación global y se verifica su pertenencia al conjunto de finalistas. En regresión no hay técnica de balanceo; por eso el universo de combinaciones de este proyecto es 7 modelos × 5 métodos = 35, y no 140 (que en clasificación incluiría cuatro técnicas de balanceo).

Todas las cifras salen de la ejecución activa `20261018_102325_af643f83` (`Precalculo/resultados/e3/busquedas/`) y se regeneran con `analisis/tabla_mejores_combinaciones.py` sin reentrenar. Coinciden con las del capítulo «Modelos clásicos» del libro previo.

(sec-modelos-base)=
## Definición de los modelos base

Los siete regresores cubren los principales sesgos inductivos de la regresión tabular: lineales con distinta penalización, un método local, un árbol y dos ensambles de árboles ({numref}`tab-modelos-base`).

:::{table} Modelos base, preparación de variables dentro del pipeline e hiperparámetros buscados.
:label: tab-modelos-base

| Modelo | Familia e idea central | Preparación dentro del pipeline | Hiperparámetros buscados | Referencia |
| --- | --- | --- | --- | --- |
| SVM lineal (`LinearSVR`) | Lineal, pérdida ε-insensible: ignora errores menores que ε. | Mediana, `log1p` en tiempos, `StandardScaler`; moda y *one-hot* con referencia (67 columnas). | `C`, `epsilon` | {cite:t}`smola2004` |
| KNN | Promedia la nota de los *k* estudiantes más parecidos. | Igual que el SVM. | `n_neighbors`, `weights`, `p` | {cite:t}`altman1992` |
| Ridge | Mínimos cuadrados con penalización L2. | Igual que el SVM. | `alpha` | {cite:t}`hoerl1970` |
| Lasso | Mínimos cuadrados con penalización L1 (selección de variables). | Igual que el SVM. | `alpha` | {cite:t}`tibshirani1996` |
| Random Forest | Bagging de árboles con `max_features = 0,7`. | Mediana, moda y `OrdinalEncoder`; sin escalado. | `n_estimators`, `max_depth`, `min_samples_leaf` | {cite:t}`breiman2001` |
| XGBoost | Boosting de árboles con gradiente de segundo orden. | Mediana y moda; categorías nativas aprendidas en cada `fit`. | `n_estimators`, `max_depth`, `learning_rate` | {cite:t}`chen2016` |
| Decision Tree | Árbol CART; cada hoja predice la media de su grupo. | Mediana, moda y *one-hot* completo. | `max_depth`, `min_samples_leaf`, `ccp_alpha` | {cite:t}`pedregosa2011` |
:::

Random Forest usa códigos ordinales porque scikit-learn exige entradas numéricas: esto introduce un orden artificial en variables nominales. XGBoost evita ese problema con particiones categóricas nativas, y una categoría nueva en validación o test pasa a faltante en lugar de recibir un código inventado. El fragmento siguiente construye los pipelines de las familias clásicas:

```{literalinclude} analisis/codigo/modelos_clasicos.py
:language: python
:start-at: def classic_pipeline
:end-before: def tune
:caption: Pipelines de KNN, Ridge, Lasso, Random Forest y XGBoost (`Precalculo/modelos_clasicos.py`).
:label: cod-pipelines-clasicos
```

Todos los modelos se evalúan con las mismas métricas, en puntos de nota:

$$
\operatorname{RMSE}=\sqrt{\frac{1}{n}\sum_{i=1}^{n}(y_i-\hat y_i)^2},\qquad
\operatorname{MAE}=\frac{1}{n}\sum_{i=1}^{n}\lvert y_i-\hat y_i\rvert,\qquad
R^2=1-\frac{\sum_i(y_i-\hat y_i)^2}{\sum_i(y_i-\bar y)^2}.
$$ (eq-metricas)

La [](#eq-metricas) se calcula por fold externo; la tabla maestra reporta su media y desviación estándar muestral sobre los cinco folds. RMSE penaliza más los errores grandes y es el criterio de selección en todo el proyecto.

(sec-busqueda)=
## Optimización de hiperparámetros

Esta sección explica qué métodos de optimización se aplicaron, cómo se integraron en la validación anidada, qué dominios exploraron, qué encontró cada uno y cuánto costó. Los cinco métodos se aplicaron con los mismos presupuestos a **los siete modelos base** y a **los tres modelos originales** ({ref}`sec-convergencia-hpo`).

(sec-metodos-hpo)=
### Métodos aplicados

Se aplicaron cinco estrategias de búsqueda, implementadas en `Precalculo/busquedas_hiperparametros_e3.py` sobre una misma función de evaluación: cada configuración se evalúa con un pipeline nuevo por fold interno, entrenado solo con el entrenamiento de ese fold y medido por RMSE en su validación. Así todas compiten con la misma medida de calidad ({numref}`tab-estrategias`).

:::{table} Estrategias de búsqueda y presupuestos, idénticos para los siete modelos base (salvo el Grid, que conserva cada grilla histórica).
:label: tab-estrategias

| Estrategia | Cómo explora | Presupuesto por búsqueda | Configuración | Referencia |
| --- | --- | --- | --- | --- |
| Grid Search | Recorre exhaustivamente una grilla discreta fija. | Tamaño de la grilla (8 a 72 puntos) | `ParameterGrid` histórico, determinista | — |
| Random Search | Muestrea configuraciones independientes en dominios continuos. | 16 sorteos | Semilla 42; uniforme en enteros y categorías, log-uniforme en `C`, `alpha` y `learning_rate` | {cite:t}`bergstra2012` |
| Bayesiana (Optuna/TPE) | Modela las densidades $l(x)$ de las configuraciones buenas y $g(x)$ de las demás y propone donde $l(x)/g(x)$ es alto. | 20 ensayos (6 aleatorios iniciales) | `TPESampler` univariado; 24 candidatos para aproximar *Expected Improvement* | {cite:t}`akiba2019` |
| Genética (DEAP) | Evoluciona una población con selección, cruce y mutación. | Población 8, inicial + 3 generaciones | Torneo 3; cruce uniforme (p = 0,8; 0,5 por gen); mutación por reinicio (p = 0,3; 1/d por gen); élite 1 | — |
| Successive Halving | Evalúa muchos candidatos con poca fidelidad y elimina la mitad peor por ronda. | 16 → 8 → 4 candidatos | Factor 2; 25 %, 50 % y 100 % de los estudiantes del entrenamiento interno | — |
:::

**Grid Search** es la referencia determinista: cubre todos los puntos definidos, pero su costo crece con el producto de los tamaños de cada eje y no alcanza valores intermedios. **Random Search** muestrea el mismo dominio sin aprender de los intentos previos; cuando pocas dimensiones son relevantes suele encontrar buenas zonas con menos evaluaciones que la grilla {cite:p}`bergstra2012`.

**Optuna/TPE** es una búsqueda bayesiana. Tras seis ensayos aleatorios divide los ensayos observados en un grupo bueno y uno malo según su RMSE, estima sus densidades $l(x)$ y $g(x)$ y elige, entre 24 candidatos muestreados de $l(x)$, el que maximiza $l(x)/g(x)$, cantidad proporcional al *Expected Improvement*: busca reducir el mejor RMSE considerando la magnitud esperada de la mejora y no solo su probabilidad. Se eligió porque los dominios son mixtos —categorías (`weights`, `max_depth` del bosque), enteros (`n_neighbors`, `n_estimators`) y continuos en escala logarítmica (`C`, `alpha`, `learning_rate`)— y TPE los maneja sin imponer un kernel gaussiano ni una distancia ordinal entre categorías.

**DEAP** implementa un algoritmo genético. Cada individuo es un vector de genes en $[0,1]$ que se decodifica al dominio de cada hiperparámetro, en escala logarítmica cuando corresponde. El torneo de tamaño 3 funciona con un fitness que se minimiza (RMSE) sin exigir valores positivos, como sí lo haría la ruleta; el cruce uniforme recombina dimensiones sin suponer cercanía entre categorías, y el elitismo de un individuo evita perder la mejor solución. Las configuraciones repetidas reutilizan el fitness ya calculado.

```{literalinclude} analisis/codigo/busquedas_hiperparametros_e3.py
:language: python
:start-at: def decode
:end-before: def suggest
:caption: Decodificación de los genes de DEAP y de los sorteos de Random y Halving al dominio de cada hiperparámetro.
:label: cod-decode
```

**Successive Halving** reparte el presupuesto por fidelidad: evalúa 16 candidatos con el 25 % de los estudiantes del entrenamiento interno, conserva los 8 mejores para el 50 % y los 4 mejores para el 100 %. Solo compiten en la selección final los candidatos evaluados a fidelidad completa, porque un RMSE calculado con menos estudiantes no es comparable.

El núcleo de las cinco estrategias es corto porque todas delegan en la misma evaluación:

```{literalinclude} analisis/codigo/busquedas_hiperparametros_e3.py
:language: python
:start-at: def run_method
:end-before: trials = self.trials[before:]
:caption: Ejecución de cada estrategia sobre los mismos folds internos (`Search.run_method`).
:label: cod-run-method
```

(sec-protocolo-anidado)=
### Selección anidada del método y los hiperparámetros

En **cada uno de los cinco entrenamientos externos** se ejecutan las cinco estrategias sobre los **mismos cinco folds internos** por estudiante y se elige, entre todas, la configuración de menor RMSE interno a fidelidad completa; los empates numéricos (≤ 10⁻¹²) se resuelven por el orden fijado antes de ejecutar (Grid, Random, TPE, DEAP, Halving). El modelo elegido se reajusta en el entrenamiento externo y predice su fold (OOF). Después se repite la comparación en **todo train** para obtener el modelo final, el único que predice el test. **Ningún criterio de tiempo ni de test interviene en la selección.** Como cada fold externo elige su propio método, las métricas externas miden el procedimiento completo y no una configuración fija.

Random Search y Successive Halving parten del mismo generador con semilla 42, de modo que los 16 candidatos iniciales de Halving son los 16 sorteos de Random: Halving solo puede igualar o empeorar al mejor de Random y, ante un empate, el orden favorece a Random. Por eso Halving nunca resulta elegido, aunque en varias búsquedas iguala a Random con menos costo.

(sec-espacios)=
### Espacios de búsqueda

Los dominios estocásticos amplían los puntos de la grilla histórica, de modo que Random, TPE, DEAP y Halving alcanzan cualquier valor del Grid y también los intermedios ({numref}`tab-espacios`).

:::{table} Grilla, dominio estocástico y justificación de los rangos de cada modelo base.
:label: tab-espacios

| Modelo | Grid (histórico) | Dominio estocástico | Justificación del rango |
| --- | --- | --- | --- |
| SVM lineal | `C` ∈ {0,01; 0,03; 0,1; 0,3; 1; 10}; `epsilon` ∈ {0; 0,05; 0,1; 0,2; 0,3; 0,5; 0,75; 1} (48) | `C` log[0,01; 10]; `epsilon` [0; 1] | `C` abarca tres órdenes de magnitud; `epsilon` en puntos de nota, con máximo de un punto en una escala 0–5. |
| KNN | `n_neighbors` ∈ {5, …, 101}; `weights`; `p` ∈ {1, 2} (32) | entero [5; 101]; uniform/distance; p 1/2 | *k* = 5 da un ajuste muy local y *k* ≈ 100 (≈ 10 % de la muestra) uno muy suavizado. |
| Ridge | `alpha` ∈ {0,01; …; 1.000} (8) | log[0,01; 1.000] | Cinco órdenes de magnitud, de casi mínimos cuadrados a coeficientes muy encogidos. |
| Lasso | `alpha` ∈ {0,0001; …; 0,1} (9) | log[0,0001; 0,1] | Con variables estandarizadas, `alpha` ≥ 0,1 anula casi todos los coeficientes. |
| Random Forest | `n_estimators` {150, 300, 500}; `max_depth` {4, 6, None}; `min_samples_leaf` {2, 5, 10} (27) | entero [150; 500]; {4, 6, 8, 12, None}; entero [2; 20] | Más de 150 árboles estabiliza el promedio; profundidad y hoja controlan la varianza. |
| XGBoost | `n_estimators` {150, 300, 500}; `max_depth` {1, 2, 4}; `learning_rate` {0,01; 0,03; 0,1} (27) | entero [150; 500]; entero [1; 6]; log[0,01; 0,1] | Árboles poco profundos limitan interacciones; tasa y número de árboles se compensan. |
| Decision Tree | `max_depth` {2, 3, 4, 6, 8, None}; `min_samples_leaf` {2, 5, 10, 20}; `ccp_alpha` {0; 0,001; 0,01} (72) | {2, …, None}; entero [2; 30]; [0; 0,01] | Profundidad, hoja mínima y poda acotan la varianza de un árbol individual. |
:::

La comparación **no es a igual presupuesto**: el Grid tiene entre 8 y 72 puntos discretos y los demás métodos exploran dominios continuos con 16 a 20 evaluaciones.

(sec-resultados-hpo)=
### Resultados de la búsqueda

La {numref}`tab-hpo-rmse-interno` muestra el mejor RMSE interno que alcanzó cada estrategia en la búsqueda final; es una métrica de selección, optimista frente al desempeño externo.

```{include} analisis/tablas/hpo_rmse_interno.md
```

Las diferencias entre estrategias son de milésimas: la mayor es de 6 milésimas (DEAP en Decision Tree), mientras que la desviación estándar entre los folds internos es de 0,019 a 0,050. **La elección de la estrategia mueve el criterio mucho menos que el ruido de la partición**; importa mucho más la familia del modelo. En los cinco folds externos y en el ajuste final (42 búsquedas), el método ganador fue TPE 15 veces, Grid 11, Random 9 y DEAP 7; la columna «Método por fold» de la {numref}`tab-mejores-combinaciones` muestra la elección de cada búsqueda.

```{figure} images/14_modelos_busqueda.jpg
:alt: Mapa de calor del RMSE medio interno de Grid Search para las 48 combinaciones de C y epsilon del SVM lineal.
:name: fig-busqueda-svm

RMSE medio interno (puntos de nota) de las 48 combinaciones de `C` y `epsilon` del Grid del SVM lineal en todo train.
```

La [](#fig-busqueda-svm) ilustra la superficie que exploran las estrategias en el SVM: una franja amplia de valores de `epsilon` entre 0,3 y 0,75 con RMSE casi igual, lo que explica que TPE (C = 0,2438; ε = 0,5130) supere al mejor punto del Grid por solo 0,0006.

```{figure} images/clasicos/hpo_anytime_evaluaciones.png
:alt: Siete paneles con curvas escalonadas del mejor RMSE interno frente al número de evaluaciones equivalentes para cinco estrategias.
:name: fig-anytime-base

Mejor RMSE interno (puntos) hasta la evaluación *t* (evaluaciones completas equivalentes) en la búsqueda final de cada modelo.
```

La [](#fig-anytime-base) muestra que TPE y DEAP alcanzan casi todo su progreso en las primeras cinco evaluaciones, que el Grid depende del orden de su grilla (empieza por los valores pequeños de cada parámetro) y que Random se estanca. En DEAP el mejor individuo ya está en la generación 0 en los siete modelos y la diversidad de la población cae rápidamente: con 8 individuos y 3 generaciones, su ventaja proviene más del muestreo inicial que de la evolución.

(sec-tiempos-hpo)=
### Presupuesto computacional y tiempos de la búsqueda

Toda la ejecución se instrumentó con `time.perf_counter()` antes de lanzarla (registro central `TIEMPOS_EJECUCION.md`, eventos en `tiempos/20261018_102325_af643f83/`). Hardware: CPU, sin GPU; cada evaluación ajusta sus cinco folds internos en cuatro procesos con un hilo cada uno; estrategias, ensayos y modelos se ejecutan en secuencia. El tiempo de búsqueda incluye preparación, ajuste, *scoring* y coordinación, y **excluye el refit**, que se mide aparte. La ejecución completa realizó 210 búsquedas, 22.650 ajustes internos, 57 refits y 131 inferencias, sin ajustes fallidos, en 3.484,6 s de pared.

```{include} analisis/tablas/hpo_evaluaciones.md
```

DEAP evalúa solo las configuraciones distintas: aunque su presupuesto nominal es 8 × 4 = 32 individuos, los duplicados reutilizan el fitness (9 a 16 evaluaciones reales). Halving evalúa 28 configuraciones, pero 16 al 25 % y 8 al 50 % de los estudiantes, de modo que su costo equivale a unas 12 evaluaciones completas ({numref}`tab-hpo-evaluaciones`).

```{include} analisis/tablas/hpo_tiempo_final.md
```

```{include} analisis/tablas/hpo_tiempo_externas.md
```

La {numref}`tab-hpo-tiempo-final` corresponde a la búsqueda que fija el modelo final y la {numref}`tab-hpo-tiempo-externas` a la suma de las cinco búsquedas de los folds externos, ejecutadas en secuencia; no se suman los ajustes internos paralelos.

```{include} analisis/tablas/hpo_s_evaluacion.md
```

El costo por evaluación lo determina el **modelo**, no la estrategia ({numref}`tab-hpo-s-evaluacion`): XGBoost tarda unos 4,8 s por evaluación (≈ 3 s por ajuste, con categorías nativas y hasta 500 árboles), Random Forest ≈ 1,3 s y los lineales menos de 0,2 s. El tiempo por evaluación del Grid en Ridge y Lasso (0,7–0,8 s) está inflado por el arranque del grupo de procesos, que se reparte entre solo 8–9 configuraciones.

```{include} analisis/tablas/hpo_agregado.md
```

```{figure} images/clasicos/hpo_tiempos.png
:alt: Barras en escala logarítmica del tiempo de la búsqueda final por modelo base y estrategia.
:name: fig-tiempos-base

Tiempo de pared (s, escala logarítmica) de la búsqueda final por modelo y estrategia.
```

La {numref}`tab-hpo-agregado` y la [](#fig-tiempos-base) resumen la relación costo-beneficio: **TPE es la estrategia elegida con más frecuencia (15 de 42) y consume un 35 % menos de tiempo que el Grid**; DEAP es la más barata (un tercio del Grid) y queda a menos de una milésima del mejor en cinco de los siete modelos; Successive Halving no ahorra tiempo de pared con esta muestra, porque hace más ajustes y la coordinación de rondas pesa tanto como el ahorro de filas. Estos tiempos dependen de la CPU, del paralelismo y del tamaño de la muestra, y no se usaron para elegir hiperparámetros.

(sec-mejores-combinaciones)=
## Tabla maestra de mejores combinaciones

La {numref}`tab-mejores-combinaciones` es la tabla maestra que exige §4.1 de la guía. El orden es por **RMSE medio del bucle externo**; el método e hiperparámetros finales son los guardados en `seleccion_antes_test.json` antes de inferir sobre test; la columna «Método por fold» muestra que cada fold externo eligió su propio método, de modo que las métricas externas miden el **procedimiento completo** de selección. El RMSE de test es solo descriptivo.

```{include} analisis/tablas/mejores_combinaciones.md
```

**Mejor combinación global.** **XGBoost con búsqueda bayesiana TPE** (442 árboles, profundidad 2, `learning_rate` = 0,0152) tiene el menor RMSE medio externo, 0,8156 ± 0,0344, y el menor RMSE de test, 0,9137. Pertenece al Model Confidence Set de los siete modelos base (p MCS = 1), junto con el SVM lineal y Ridge (p = 0,766); Lasso, Random Forest, KNN y Decision Tree quedan fuera. Su ventaja sobre el SVM lineal (0,0085 puntos de RMSE) no es estadísticamente distinguible entre los modelos base (contraste por estudiante p = 0,356, sección [](#sec-dm-svm) del {ref}`sec-validacion`).

```{figure} images/clasicos/eval_resumen_rmse_mae.png
:alt: Barras horizontales de RMSE y MAE por modelo base en entrenamiento, validación y prueba, con barras de error de ±1 DE en validación.
:name: fig-eval-base

RMSE y MAE (puntos de nota) de los siete modelos base en entrenamiento, validación externa y prueba; en validación, ±1 DE entre folds.
```

La [](#fig-eval-base) muestra el mismo patrón en los siete modelos: el error crece de entrenamiento a validación (sobreajuste) y de validación a prueba (cambio de periodo, entre 0,08 y 0,12 puntos). KNN tiene RMSE de entrenamiento 0 porque, con `weights = distance`, cada registro es su propio vecino: es un artefacto del método, no un ajuste perfecto. Decision Tree es claramente inferior en los tres conjuntos.

```{figure} images/clasicos/eval_xgboost.png
:alt: XGBoost: predicción frente a nota real y residuos frente a predicción en entrenamiento, validación OOF y test.
:name: fig-eval-xgboost

XGBoost, mejor benchmark: nota predicha frente a real (arriba) y residuos frente a la predicción con su media por decil (abajo), en puntos de nota.
```

En la [](#fig-eval-xgboost) la media por decil del residuo de validación es casi plana: el mejor benchmark no deja sesgo sistemático por nivel de predicción, aunque la dispersión es mayor en las predicciones bajas y comprime los extremos (regresión hacia la media). Estos mismos rasgos aparecen en los modelos originales ({ref}`sec-modelo-original`).

(sec-tiempos-base)=
## Tiempos de búsqueda, entrenamiento e inferencia por modelo

La {numref}`tab-tiempos-base` se toma del registro central (`TIEMPOS_EJECUCION.md`, eventos crudos en `tiempos/20261018_102325_af643f83/`). Hardware: CPU, sin GPU; cada evaluación ajusta sus cinco folds internos en cuatro procesos con un hilo cada uno; las estrategias se ejecutan en secuencia. La búsqueda excluye el refit, que se mide aparte, y no se suman ajustes paralelos como tiempo de pared.

```{include} analisis/tablas/tiempos_base.md
```

La {numref}`tab-tiempos-base` reúne, para cada modelo, las tres etapas: XGBoost necesita 436 s para sus cinco búsquedas finales y Random Forest 121 s, frente a 12–28 s de los lineales; el refit final tarda menos de 1,4 s en todos los modelos y la inferencia de los 188 estudiantes del test menos de 0,1 s. Estos tiempos se reportan, pero no se usaron para seleccionar.



(sec-serializacion)=
## Reentrenamiento final y serialización

Cada pipeline final (preprocesamiento + modelo) se reentrenó sobre los 1.309 registros de train con los hiperparámetros de la tabla maestra y se serializó con `joblib`: `Precalculo/resultados/e3/busquedas/20261018_102325_af643f83/model.joblib` (SVM) y `clasicos/{knn,ridge,lasso,forest,xgboost,decision_tree}.joblib`, más el *booster* nativo `xgboost.ubj`. El dashboard copia esos artefactos a `Dash/data/` y verifica sus SHA-256 antes de servir; **nunca reentrena ni busca hiperparámetros**. Para cada uno de los siete modelos, el registro de tiempos incluye una inferencia de «verificación de serialización»: el pipeline se carga desde el archivo y se comprueba, con igualdad exacta, que sus predicciones sobre el test coinciden con las del modelo en memoria (prueba de ida y vuelta en `Precalculo/evaluar_busquedas_e3.py:151-153`). Las versiones de librerías y la semilla se documentan en el {ref}`sec-reproducibilidad`.

---
title: Modelos originales
description: SVR RBF, Kernel Ridge, TR-KRR, DenseWeight-XGBoost, TCR-XGBoost, LinXGBoost, logicDT, GPR–XGBoost y RIM frente al SVM lineal; explicación de cada modelo con su artículo, optimización de hiperparámetros, evaluación, residuos, interpretabilidad SHAP/LIME, robustez y comparación estadística.
---

# Modelos originales

Este capítulo amplía la subpestaña **Modelos originales** de **03 Modelos predictivos** del dashboard. Allí se presenta el panorama de las implementaciones propias y adaptaciones evaluadas en E3 —con su ficha, su artículo de fundamento, sus tablas y sus contrastes—; aquí se documenta además **qué es cada modelo y cómo funciona**, cómo se optimizaron sus hiperparámetros con las cinco estrategias del protocolo, cómo se comportan sus residuos, qué explica SHAP del líder y qué dice la comparación estadística. Mantiene la estructura del capítulo [Modelos clásicos](04_modelos_clasicos.md), con un apartado nuevo de explicación individual de los modelos.

El capítulo se organiza en cinco bloques:

1. **Introducción:** qué son los modelos originales, qué los distingue de los clásicos y de los modelos de librería, y una **explicación de cada uno con el vínculo a su artículo de referencia**.
2. **Optimización de hiperparámetros:** las cinco estrategias, los dominios, los resultados, el presupuesto computacional, los tiempos y la convergencia.
3. **Evaluación de modelos:** RMSE y MAE en entrenamiento, validación y prueba, diagnósticos de White y BDS, patrones de residuos, interpretabilidad SHAP y LIME del modelo líder, y robustez frente a los folds.
4. **Comparación estadística:** prueba de Friedman, post hoc (Nemenyi y Model Confidence Set), contraste tipo Diebold–Mariano por estudiante frente al SVM y tamaños de efecto.
5. **Resultados finales y conclusiones.**

Todas las cifras provienen de la ejecución activa de Originales `20261020_153034_consolidada` (`Precalculo/resultados/e3/originales_busquedas/`), la misma que alimenta el dashboard, y de los análisis estadísticos `20261020_174028_5ff56a2e`. Las tablas y figuras se regeneran con `jbook_dashboard/analisis_originales/generar_originales.py`; el script **no reentrena ni vuelve a buscar hiperparámetros**. Su única inferencia nueva es la predicción en entrenamiento (*in-sample*) de los pipelines finales ya guardados, medida con `time.perf_counter()` y registrada en `TIEMPOS_EJECUCION.md`. El resto sale de predicciones, folds, ensayos y explicaciones ya almacenados.

## Introducción

Todos los modelos de este capítulo son **regresores**: predicen la nota del primer parcial en la escala 0–5. Comparten exactamente el protocolo descrito en [Modelos lineales](03_modelos.md): los mismos 1.309 registros de train (1.293 estudiantes), el mismo test temporal del periodo 202530 (188 registros), los **mismos cinco folds externos** `GroupKFold` por estudiante y cinco folds internos por estudiante para la búsqueda. Sus métricas son, por tanto, comparables fold a fold con las del SVM lineal y con las de los seis clásicos.

### Qué son los «modelos originales»

En el dashboard, la pestaña **Modelos originales** reúne todo lo que se evaluó en E3 más allá del SVM lineal y los clásicos. Contiene tres tipos de modelos:

- **Implementaciones propias, adaptaciones y variantes** de métodos descritos en la literatura (nueve modelos): son el foco de este capítulo. Aquí se incluye **Kernel Ridge RBF**, aunque su estimador base proviene de una librería (`sklearn.kernel_ridge.KernelRidge`): se aplica **encapsulado en un transformador del objetivo** que modifica su resultado, por lo que se trata como un modelo distinto y no como una simple importación (véase su explicación más abajo).
- **Modelos de librería importada o preentrenados** (once: TabICLv2, TabPFN 2.5 original y *fine-tuned*, CatBoost, TabFM, XGBoost ampliado, RaFFLE, DART-XGBoost, HRT-Boost, XBART y coPILOT). El 20 de octubre de 2026 se decidió que el proyecto se centra en los clásicos y en las implementaciones propias: esos once se conservan como referencia, **se ocultan por defecto en el tablero y quedan fuera de todas las pruebas estadísticas**. Este capítulo tampoco los analiza.
- **Referencias de comparación:** el SVM lineal y los clásicos KNN, Ridge, Lasso, Random Forest y XGBoost, que el tablero incluye en la misma comparación. El Dummy (media del objetivo) solo sirve de control y el Decision Tree no forma parte de la comparación de Originales.

Por eso las pruebas de las secciones estadísticas de este capítulo comparan **15 modelos**: los nueve originales, el SVM lineal y cinco clásicos (KNN, Ridge, Lasso, Random Forest y XGBoost), exactamente como el tablero. En las tablas de evaluación se muestran los nueve originales y el SVM como referencia.

### Modelos implementados

| Modelo | Familia | Idea central | Hiperparámetros buscados | Artículo |
| --- | --- | --- | --- | --- |
| **SVR RBF** | Kernel, pérdida ε-insensible | Regresión de vectores de soporte con kernel gaussiano: ignora errores menores que ε y modela relaciones no lineales. | `C`, `epsilon`, `gamma` | [Smola y Schölkopf (2004)](https://doi.org/10.1023/B:STCO.0000035301.49549.88) |
| **Kernel Ridge RBF** | Kernel, pérdida cuadrática | Ridge en el espacio del kernel gaussiano; solución cerrada exacta. | `alpha`, `gamma` | [Abdulla et al. (2022)](https://doi.org/10.3390/app12094252) (variante exacta) |
| **TR-KRR RBF** | Kernel, solver iterativo | El mismo Kernel Ridge, pero el sistema dual se resuelve con gradiente conjugado truncado (Newton truncado). | `alpha`, `gamma` | [Abdulla et al. (2022)](https://doi.org/10.3390/app12094252) |
| **DenseWeight-XGBoost** | Boosting con pesos | XGBoost con peso por observación según la rareza de su nota. | `n_estimators`, `max_depth`, `learning_rate`, `min_child_weight`, `reg_lambda`, `weight_alpha` | [Steininger et al. (2021)](https://doi.org/10.1007/s10994-021-06023-5) |
| **TCR-XGBoost** | Boosting con pesos | Reduce el peso de las observaciones con baja robustez local antes de ajustar XGBoost. | `fraction`, `weight` | [Zühlke y Kudenko (2025)](https://link.springer.com/article/10.1007/s10994-024-06704-x) |
| **LinXGBoost** | Boosting con hojas lineales | Árboles de boosting cuyas hojas ajustan regresiones Ridge locales en lugar de constantes. | `n_estimators`, `learning_rate`, `min_samples_leaf`, `reg_lambda`, `gamma` | [de Vito (2017)](https://arxiv.org/abs/1710.03634) |
| **logicDT adaptado** | Árbol de conjunciones lógicas | Árbol sobre conjunciones booleanas de indicadores, con modelos lineales en las hojas; términos buscados por recocido simulado. | `max_conj`, `extra_vars`, `nodesize_frac` | [Lau, Schikowski y Schwender (2023)](https://doi.org/10.1007/s10994-023-06488-6) |
| **GPR–XGBoost** | Híbrido de dos etapas | Un proceso gaussiano estima la nota y XGBoost corrige su residuo con meta-variables fuera de muestra. | `n_estimators`, `learning_rate`, `max_leaves`, `reg_lambda` | [De, Majumder et al. (2026, preprint)](https://arxiv.org/abs/2610.15862) |
| **RIM** | Recuperación + red neuronal | Recupera estudiantes parecidos con BM25 y combina sus notas con una red. | `n_neighbors`, `epochs`, `weight_decay` | [Qin et al. (2021)](https://arxiv.org/abs/2108.05252) |

El SVM lineal y los seis clásicos se describen en [Modelos lineales](03_modelos.md) y [Modelos clásicos](04_modelos_clasicos.md). La elección cubre cuatro ideas distintas de mejorar una regresión tabular: **no linealidad por kernels** (SVR, Kernel Ridge, TR-KRR), **reponderar observaciones** en un modelo ya competitivo (DenseWeight, TCR), **modelos locales y estructuras lógicas** (LinXGBoost, logicDT) e **híbridos que combinan fuentes de predicción** (GPR–XGBoost, RIM). Los artículos describen los métodos y sus resultados en sus propios conjuntos de datos: **ninguno demuestra por sí mismo una mejora en estos datos**, que es lo que evalúan las secciones siguientes.

### Explicación de cada modelo

Cada subsección explica qué hace el modelo, cómo se implementó en este proyecto, qué se busca de sus hiperparámetros y qué conviene tener presente al leer sus resultados. El enlace del título lleva al artículo de referencia. La preparación de las variables es la misma del SVM —mediana numérica, `log1p` en los tiempos, `StandardScaler`, moda y *one-hot* con categoría de referencia— salvo que se indique otra; todo se aprende dentro de cada `fit`.

#### SVR RBF · [Smola y Schölkopf, «A tutorial on support vector regression», *Statistics and Computing*, 2004](https://doi.org/10.1023/B:STCO.0000035301.49549.88)

La regresión de vectores de soporte (SVR) busca una función $f(x)$ lo más plana posible que se desvíe de las notas observadas como máximo $\varepsilon$; los errores menores que $\varepsilon$ no se penalizan y los mayores se penalizan linealmente con peso $C$. Es el mismo principio del SVM lineal de referencia, pero aquí el producto interno se sustituye por un **kernel gaussiano (RBF)**,

$$
k(x, x') = \exp\!\big(-\gamma\,\lVert x - x'\rVert^2\big),
$$

de modo que la función aprendida, $f(x)=\sum_i(\alpha_i-\alpha_i^*)\,k(x_i,x)+b$, puede ser **no lineal** en las variables. Solo los estudiantes con error mayor o igual que $\varepsilon$ (los vectores de soporte) tienen coeficientes distintos de cero. Los tres hiperparámetros tienen una lectura directa: `C` controla cuánto cuesta equivocarse, `epsilon` define el ancho de la banda sin penalización (en puntos de nota) y `gamma` el alcance del kernel (un `gamma` grande hace que solo los vecinos muy cercanos influyan en la predicción). Es el vínculo natural entre el SVM lineal y el resto de los métodos de kernel de este capítulo, y se implementa con `sklearn.svm.SVR`.

#### Kernel Ridge RBF · [Abdulla, Maalouf, Barsoum y An, *Applied Sciences*, 2022](https://doi.org/10.3390/app12094252)

Kernel Ridge Regression (KRR) resuelve una regresión Ridge en el espacio de características que induce el kernel RBF: minimiza el error cuadrático más una penalización $\alpha\lVert f\rVert^2$ sobre la norma de la función. A diferencia del SVR, la pérdida es **cuadrática** (todo error cuenta, no hay banda $\varepsilon$) y la solución es **densa** y **exacta**,

$$
\hat{c} = (K + \alpha I)^{-1} y, \qquad f(x) = \sum_{i=1}^{n} \hat{c}_i\,k(x_i, x),
$$

donde $K$ es la matriz de kernels entre los estudiantes de entrenamiento. El objetivo se centra dentro de cada ajuste. Sus dos hiperparámetros son `alpha` (regularización: mayor `alpha`, función más suave) y `gamma` (alcance del kernel). En este proyecto es la variante **exacta** (inversión directa del sistema); el artículo de referencia aplica un solver iterativo, que se implementa aparte en el modelo siguiente. Resulta ser el líder descriptivo del capítulo.

**Por qué no es una simple importación.** El estimador `KernelRidge` de scikit-learn **no tiene intercepto**: la función aprendida es $f(x)=\sum_i \hat c_i\,k(x_i,x)$ y la penalización $\alpha\lVert f\rVert^2$ empuja las predicciones hacia **cero**, no hacia la nota media. Como las notas están en la escala 0–5 con media cercana a 3,5, un `KernelRidge` directo sería sesgado cuanto mayor fuera `alpha` o más lejos estuviera un estudiante de los de entrenamiento. Por eso el modelo evaluado envuelve al estimador en un `TransformedTargetRegressor` con `StandardScaler(with_std=False)`: **dentro de cada `fit` se resta la media de las notas de entrenamiento, el kernel aprende la desviación respecto de esa media y la predicción se devuelve en la escala original sumando la media de nuevo**.

```python
model = TransformedTargetRegressor(regressor=KernelRidge(kernel='rbf', **params),
                                   transformer=StandardScaler(with_std=False))   # centra y solo dentro de fit
```

Este cambio es relevante por tres razones. **Cambia el resultado:** el nivel medio deja de penalizarse y, ante un estudiante lejano de los de entrenamiento, el modelo revierte hacia la nota media (≈ 3,5) y no hacia 0; además puede modificar qué valores de `alpha` resultan óptimos, de modo que sus hiperparámetros y su RMSE no tendrían por qué coincidir con los de un `KernelRidge` sin envoltura (esa comparación directa no se ejecutó aquí). **Es lo que lo distingue de TR-KRR**, que resuelve el mismo sistema con gradiente conjugado y **no centra el objetivo**; la diferencia entre ambos no es solo el solver. Y **justifica incluirlo entre los modelos que no son solo importados**: el estimador es de librería, pero el pipeline que se evalúa (preparación de variables, centrado del objetivo y búsqueda anidada de `alpha` y `gamma`) es una construcción del proyecto. La centralización se aprende únicamente con las notas de cada entrenamiento (interno, externo o final), de modo que no filtra información de validación ni de test.

#### TR-KRR RBF · [Abdulla et al., «Truncated Newton Kernel Ridge Regression…», *Applied Sciences*, 2022](https://doi.org/10.3390/app12094252)

Es el mismo modelo del apartado anterior, pero el sistema $(K+\alpha I)c=y$ **no se invierte: se resuelve con el método de gradiente conjugado truncado**, la iteración interna del método de Newton truncado. Como la solución se detiene antes de converger por completo, el número de iteraciones actúa como una **regularización implícita** adicional a `alpha`. La implementación del proyecto (`tn_krr_e3.py`) reproduce los controles del artículo: como máximo 200 iteraciones, parada cuando la norma del residuo baja de 0,5 o tras 25 iteraciones sin mejora, y arranque con coeficientes cero (el objetivo **no** se centra, a diferencia de la variante exacta). El núcleo del solver es el bucle clásico de gradiente conjugado:

```python
residual, direction = y.copy(), y.copy()                      # arranque con coeficientes cero
for iteration in range(1, max_iter + 1):
    system_direction = system @ direction                     # (K + alpha·I) @ d
    step = residual_sq / float(direction @ system_direction)
    coefficients += step * direction
    residual -= step * system_direction
    residual_norm = np.sqrt(residual @ residual)
    if residual_norm <= cg_tolerance:                         # 0,5 del artículo
        break
    no_improvement = 0 if residual_norm < best_residual_norm else no_improvement + 1
    if no_improvement >= max_no_improve:                      # 25 iteraciones sin mejora
        break
    direction = residual + (next_residual_sq / residual_sq) * direction
```

Sus hiperparámetros son los mismos `alpha` y `gamma`. Como comparte el kernel con Kernel Ridge, la diferencia entre ambos mide únicamente el efecto de resolver el sistema de forma truncada.

#### DenseWeight-XGBoost · [Steininger, Kobs, Davidson y Krause, «Density-based weighting for imbalanced regression», *Machine Learning*, 2021](https://doi.org/10.1007/s10994-021-06023-5)

En regresión desbalanceada, los valores raros del objetivo (aquí, las notas extremas) aparecen poco y el modelo tiende a ignorarlos. DenseWeight estima la **densidad** del objetivo con un estimador de núcleo (KDE) y asigna a cada observación un peso mayor cuanto más rara es su nota:

$$
w_i = \max\!\big(1 - \alpha\,\hat\phi(y_i),\ \varepsilon\big),
$$

con $\hat\phi$ la densidad normalizada a $[0,1]$ y $\alpha$ (`weight_alpha`) la intensidad: con $\alpha=0$ todos los pesos son 1 y el modelo equivale a **XGBoost sin ponderar**. En este proyecto los pesos se calculan **solo con las notas del entrenamiento de cada ajuste** y se pasan como `sample_weight` a un XGBoost con categorías nativas (sin *one-hot*, `log1p` ni escalado). El artículo original propone DenseLoss para redes neuronales; esta combinación con XGBoost es una **adaptación** y así se declara. Además de `weight_alpha` se buscan `n_estimators`, `max_depth`, `learning_rate`, `min_child_weight` y `reg_lambda`. Un resultado importante, que se verá en la optimización, es que la configuración final elige `weight_alpha = 0`: en estos datos la ponderación no mejoró el criterio interno.

#### TCR-XGBoost · [Zühlke y Kudenko, «TCR: topologically consistent reweighting for XGBoost in regression tasks», *Machine Learning*, 2025](https://link.springer.com/article/10.1007/s10994-024-06704-x)

TCR mide, para cada estudiante, qué tan **robusta** es su nota respecto de sus vecinos en el espacio de variables: una observación cuyo objetivo cambia mucho aunque sus variables cambien poco es localmente inconsistente. La robustez usada en el proyecto es

$$
r_i = \frac{1}{1 + \max_{j}\ \lvert y_i - y_j\rvert\,/\,(\lVert x_i - x_j\rVert_2 + \epsilon)},
$$

con el objetivo y las variables escalados a $[0,1]$. Las observaciones de menor robustez (la fracción `fraction`) reciben un peso reducido `weight` y el resto peso 1; **no se elimina ninguna fila**. Con `fraction = 0` o `weight = 1` el modelo equivale a XGBoost sin reponderar. En el protocolo del artículo (implementado el 20 de octubre) TCR se aplica como *retrofit* sobre el XGBoost ya ajustado **en el mismo entrenamiento externo** (el del XGBoost clásico: 442 árboles, profundidad 2, `learning_rate` 0,0152), y solo se buscan `fraction` y `weight` en un Grid de 10 candidatos. El código que construye los pesos es:

```python
def positive_weights(values, fraction, weight):
    output = np.ones(len(values))
    n = int(fraction * len(values))
    output[np.argsort(values, kind='stable')[:n]] = weight   # las n observaciones menos robustas
    return output
```

#### LinXGBoost · [de Vito, «LinXGBoost: Extension of XGBoost to Generalized Local Linear Models», 2017](https://arxiv.org/abs/1710.03634)

LinXGBoost conserva el esquema de XGBoost —árboles ajustados con gradiente y hessiana de segundo orden, con regularización— pero **cada hoja contiene un modelo lineal local (Ridge) en lugar de un valor constante**, de modo que el árbol aproxima la función por tramos lineales en vez de por escalones. El proyecto lo implementa de forma independiente (no hay paquete oficial): cortes exactos en cada nodo, profundidad alta limitada por `min_samples_leaf`, y una escala adicional de todas las columnas para las hojas lineales. La búsqueda es especial: el 20 de octubre de 2026 se decidió usar **solo Optuna/TPE**, con 40 ensayos (10 iniciales aleatorios) sobre un dominio ampliado, porque una primera búsqueda con las cinco estrategias dejó los óptimos en el borde del dominio. Se buscan `n_estimators` (1 a 5), `learning_rate`, `min_samples_leaf` (30 a 450), `reg_lambda` y `gamma`.

#### logicDT adaptado · [Lau, Schikowski y Schwender, «logicDT: a procedure for identifying response-associated interactions between binary predictors», *Machine Learning*, 2023](https://doi.org/10.1007/s10994-023-06488-6)

logicDT construye un árbol de decisión cuyas divisiones no son sobre una variable sino sobre **conjunciones lógicas** de indicadores binarios (por ejemplo, «programa = Sistemas **y** asignatura = MAT1101 **y no** cumplimiento = sí»). Los términos se buscan con **recocido simulado adaptativo**, y cada hoja ajusta un **modelo lineal** con las covariables numéricas; las divisiones se evalúan por razón de verosimilitud (con $\alpha=0{,}5$). El proyecto lo implementa de forma fiel al artículo en `logicdt_fiel.py` (no es el paquete R): predictores binarios = variables *one-hot*, covariables numéricas en las hojas, vecindad de la Fig. 3 del artículo y presupuesto acotado a 10.000 iteraciones. La versión anterior, más simple, se conserva en `logicdt_propio.py` como evidencia histórica. Los hiperparámetros buscados son `max_conj` (máximo de variables por conjunción), `extra_vars` (variables adicionales permitidas) y `nodesize_frac` (tamaño mínimo de hoja como fracción de la muestra).

#### GPR–XGBoost · [De, Majumder et al., «A Hybrid Gaussian Process–Extreme Gradient Boosting Machine Learning Framework…», preprint arXiv, 2026](https://arxiv.org/abs/2610.15862)

Es un **híbrido de dos etapas**. Primero, un proceso gaussiano (GPR) con kernel $C\cdot(\text{Matérn}_{5/2}+\text{RBF})+\text{White}$ y cinco reinicios del optimizador estima la nota y su incertidumbre. Después, XGBoost aprende el **residuo** del GPR a partir de las variables, la media y la desviación del GPR:

```python
stack = np.column_stack([Z, stage['mean_oof'], stage['std_oof']])   # variables + media y SD del GPR (OOF)
self.xgb_ = XGBRegressor(**params).fit(stack, y - stage['mean_oof'])  # XGBoost corrige el residuo del GPR
...
mean, std = self.gpr_.predict(Z, return_std=True)
return mean + self.xgb_.predict(np.column_stack([Z, mean, std]))      # predicción = GPR + corrección
```

Para que XGBoost no aprenda de predicciones del GPR que ya vieron la nota, las meta-variables de entrenamiento se generan **fuera de muestra y agrupadas por estudiante** (*cross-fitting* con `GroupKFold`). Dos advertencias condicionan su lectura. Primera, el preprint se evaluó con 582 datos de ingeniería y partición aleatoria 80/20: sus métricas no predicen las de E3. Segunda, el GPR exacto es costoso (la etapa GPR se calcula una vez por conjunto de ajuste y se reutiliza entre candidatos). Se buscan los hiperparámetros de XGBoost (`n_estimators`, `learning_rate`, `max_leaves`, `reg_lambda`); el kernel del GPR queda fijo.

#### RIM · [Qin et al., «Retrieval & Interaction Machine for Tabular Data Prediction», KDD 2021](https://arxiv.org/abs/2108.05252)

RIM predice la nota de un estudiante **recuperando a los estudiantes más parecidos del entrenamiento**, no solo aprendiendo una función global. Cada registro se convierte en una consulta de texto (campo = valor), un índice **BM25** recupera sus `n_neighbors` vecinos más similares y una red neuronal (MLP de 64 y 32 unidades, con `LayerNorm`) combina las variables del estudiante con las **notas de los vecinos recuperados**, discretizadas en cuantiles. En este *port* E3: el IDF de BM25 es el del artículo (Ec. 7), las variables numéricas se discretizan y se representan con *embeddings* en lugar de *one-hot*, y el conjunto de recuperación es el propio ajuste **excluyendo al estudiante consultado** para no filtrar su nota. Se buscan `n_neighbors` (5 o 15), `epochs` (30 o 60) y `weight_decay` (0,001 o 0,01): solo 8 candidatos. Es probable que sea el modelo más sensible al tamaño de la muestra, porque la red tiene muchos parámetros para unos 1.000 registros (esta sospecha no se contrasta aquí).

### Preparación de las variables y métricas

La representación de las variables no es la misma para todas las familias. Los kernels y la red de RIM necesitan escalas comparables y codificación *one-hot* o *embeddings*; los modelos con XGBoost (DenseWeight, TCR y GPR–XGBoost en su etapa de árboles) usan las categorías de forma **nativa**, con el vocabulario aprendido en cada `fit` y las categorías nuevas convertidas en faltantes. Las métricas se calculan con la misma función para todos los modelos y conjuntos:

```python
def metrics(y, pred):
    return {'RMSE': float(np.sqrt(mean_squared_error(y, pred))),
            'MAE': float(mean_absolute_error(y, pred)),
            'MAPE (%)': float(100 * mean_absolute_percentage_error(y, pred)),
            'R²': float(r2_score(y, pred))}
```

Con los modelos y su preparación definidos, la siguiente sección explica cómo se eligieron sus hiperparámetros.

## Optimización de hiperparámetros

Esta sección responde cuatro preguntas: qué estrategias de búsqueda se aplicaron, qué dominios se exploraron, qué encontró cada estrategia y cuánto costó. Al final se analiza la convergencia de las búsquedas bayesiana y genética mediante curvas de desempeño en cualquier momento.

> Esta sección usa los mismos métodos de búsqueda descritos en la sección *Optimización de hiperparámetros* del capítulo [Modelos clásicos](04_modelos_clasicos.md#estrategias-de-búsqueda-y-presupuestos); para mayor información sobre la metodología se puede consultar allí.

### Protocolo de selección anidada

El protocolo es el mismo de los clásicos: en **cada uno de los cinco entrenamientos externos** se ejecutan Grid, Random, Bayesiana (Optuna/TPE), Genética (DEAP) y Successive Halving sobre los **mismos cinco folds internos** por estudiante; se elige, entre todas, la configuración de menor RMSE interno a fidelidad completa (los empates ≤ 10⁻¹² se resuelven por el orden Grid, Random, TPE, DEAP y Halving); el modelo elegido se reajusta y predice su fold externo (predicción OOF); y el procedimiento se repite sobre **todo train** para obtener el modelo final, el único que predice el test. Ni el fold externo ni el test participan en la búsqueda, y **ningún criterio de tiempo interviene en la selección**. Los presupuestos son los de [Modelos clásicos](04_modelos_clasicos.md): Random 16 sorteos, TPE 20 ensayos (6 iniciales aleatorios, 24 candidatos para aproximar *Expected Improvement*), DEAP con población 8 y tres generaciones (torneo 3, cruce 0,8, mutación 0,3, élite 1), y Halving 16 → 8 → 4 candidatos con el 25 %, 50 % y 100 % de los estudiantes. El resultado completo de los nueve modelos se consolidó a partir de cinco ejecuciones sin reentrenar.

**Excepciones.** Tres modelos no siguen exactamente el esquema de cinco estrategias por razones declaradas:

- **LinXGBoost** usa **solo TPE**, con 40 ensayos (10 iniciales) y un dominio ampliado, por una decisión del proyecto. No tiene Grid, Random, DEAP ni Halving, así que no aparece en las comparaciones entre estrategias.
- **TCR-XGBoost** busca solo `fraction` y `weight` (Grid de 10 candidatos) sobre el XGBoost ya ajustado, por lo que su presupuesto es menor (6 a 12 evaluaciones).
- **RIM** tiene una grilla de solo 8 candidatos; con tan pocos puntos, las cinco estrategias convergen a la misma configuración.

Cada evaluación crea un pipeline nuevo por fold interno y verifica que no haya estudiantes compartidos, exactamente como en los clásicos. El Successive Halving sigue partiendo del mismo generador con semilla 42 que Random, de modo que los 16 candidatos iniciales de ambos coinciden y Halving solo puede igualar o empeorar al mejor de Random; por eso **nunca resulta elegido**.

### Espacios de búsqueda y justificación de los rangos

Los dominios estocásticos amplían los puntos de la grilla histórica, de modo que Random, TPE, DEAP y Halving alcanzan cualquier valor del Grid y también los intermedios.

| Modelo | Grid | Dominio estocástico | Justificación del rango |
| --- | --- | --- | --- |
| SVR RBF | `C` {0,01; 1; 100}; `epsilon` {0,01; 0,1; 1}; `gamma` {scale; 0,001; 0,03} (27) | `C` log[0,001; 1.000]; `epsilon` log[0,01; 1,5]; `gamma` categórica {scale, auto, 10⁻⁵ … 10} | `C` y `gamma` abarcan de modelos casi constantes a muy flexibles; `epsilon` en puntos de nota, con máximo 1,5 en una escala 0–5. |
| Kernel Ridge RBF y TR-KRR | `alpha` {0,01; 0,1; 1; 10; 100}; `gamma` {0,001 … 1} (35) | `alpha` log[0,01; 100]; `gamma` log[0,001; 1] | Cinco órdenes de magnitud en `alpha`; con 67 columnas estandarizadas, un `gamma` mayor que 1 hace el kernel casi diagonal (memoriza). |
| DenseWeight-XGBoost | 96 candidatos: `n_estimators` {250; 600}, `max_depth` {2; 4}, `learning_rate` {0,02; 0,08}, `min_child_weight` {1; 5}, `reg_lambda` {1; 10}, `weight_alpha` {0; 0,5; 1} | 10 dimensiones: incluye `subsample`, `colsample_bytree`, `gamma`, `reg_alpha` y `weight_alpha` hasta 1,25 | Grid grueso documentado (`weight_alpha = 0` equivale a XGBoost sin ponderar); las demás estrategias exploran el dominio histórico completo. |
| TCR-XGBoost | `fraction` {0; 0,05; 0,1; 0,2}; `weight` {0,3; 0,6; 0,9; 1} (10 candidatos distintos) | categóricas sobre los mismos valores | Dominio fijado por el artículo; el XGBoost base proviene del clásico. |
| LinXGBoost | — (solo TPE) | `n_estimators` 1–5; `learning_rate` log[0,02; 0,4]; `min_samples_leaf` 30–450; `reg_lambda` log[0,1; 1.000]; `gamma` log[0,001; 50] | Dominio ampliado porque una primera búsqueda dejó los óptimos en el borde. |
| logicDT adaptado | `max_conj` {1…4}; `extra_vars` {0, 1, 2}; `nodesize_frac` {0,01; 0,05; 0,1} (33) | enteros 1–4 y 0–2; `nodesize_frac` log[0,01; 0,1] | Conjunciones de hasta 4 términos mantienen la interpretabilidad; hojas de al menos el 1 al 10 % de la muestra evitan ajustar regresiones lineales a muy pocos estudiantes. |
| GPR–XGBoost | `n_estimators` {300; 600; 1.000}, `learning_rate` {0,005; 0,01; 0,03}, `max_leaves` {7; 15; 31}, `reg_lambda` {1; 10} (54) | enteros 200–1.200 y 4–63; `learning_rate` log[0,003; 0,1]; `reg_lambda` log[0,1; 50] | Hojas limitadas porque con unos 1.000 registros un XGBoost profundo sobreajusta el residuo del GPR. |
| RIM | `epochs` {30; 60}; `n_neighbors` {15; 5}; `weight_decay` {0,001; 0,01} (8) | categóricas sobre los mismos valores | Grilla histórica reducida por el costo de la red y del índice BM25 en cada fit. |

La comparación **no es a igual presupuesto**: el Grid tiene entre 8 y 96 puntos discretos y los demás métodos exploran dominios continuos con 16 a 20 evaluaciones (Halving, 28 evaluaciones parciales con un costo equivalente a unas 12 completas).

### Resultados de la búsqueda final

La tabla muestra el mejor RMSE interno (media de cinco folds internos sobre todo train) que alcanzó cada estrategia; en negrita, el método elegido. Es una métrica **de selección**: está optimizada sobre los mismos folds y es optimista respecto del desempeño externo. LinXGBoost solo tiene TPE.

| Modelo | Grid | Random | TPE | DEAP | Halving |
| --- | ---: | ---: | ---: | ---: | ---: |
| SVR RBF | 0,805791 | 0,809234 | **0,804131** | 0,805191 | 0,809234 |
| Kernel Ridge RBF | 0,800408 | 0,811287 | **0,798165** | 0,800460 | 0,811287 |
| TR-KRR RBF | 0,803685 | 0,816305 | **0,801160** | 0,802747 | 0,816305 |
| DenseWeight-XGB | **0,805878** | 0,819743 | 0,806163 | 0,808760 | 0,819743 |
| TCR-XGBoost | **0,807753** | 0,807753 | 0,807753 | 0,807753 | 0,808075 |
| LinXGBoost | — | — | **0,828292** | — | — |
| logicDT adaptado | **0,832436** | 0,834567 | 0,834567 | 0,848536 | 0,842107 |
| GPR–XGBoost | 0,804104 | 0,815841 | 0,803197 | **0,802333** | 0,815841 |
| RIM | **0,864571** | 0,864571 | 0,864571 | 0,864571 | 0,864571 |

Las diferencias entre estrategias, expresadas como brecha respecto de la mejor de cada modelo en milésimas de RMSE, son:

| Modelo | Grid | Random | TPE | DEAP | Halving |
| --- | ---: | ---: | ---: | ---: | ---: |
| SVR RBF | 1,659 | 5,102 | 0,000 | 1,060 | 5,102 |
| Kernel Ridge RBF | 2,242 | 13,122 | 0,000 | 2,295 | 13,122 |
| TR-KRR RBF | 2,525 | 15,144 | 0,000 | 1,587 | 15,144 |
| DenseWeight-XGB | 0,000 | 13,865 | 0,285 | 2,882 | 13,865 |
| TCR-XGBoost | 0,000 | 0,000 | 0,000 | 0,000 | 0,322 |
| LinXGBoost | — | — | 0,000 | — | — |
| logicDT adaptado | 0,000 | 2,131 | 2,131 | 16,100 | 9,671 |
| GPR–XGBoost | 1,771 | 13,508 | 0,865 | 0,000 | 13,508 |
| RIM | 0,000 | 0,000 | 0,000 | 0,000 | 0,000 |

En los tres métodos de kernel y en los modelos con XGBoost, las estrategias de búsqueda inteligente (TPE, DEAP) y el Grid quedan separados por **menos de 3 milésimas**, mientras Random y Halving —que comparten los mismos 16 candidatos— se quedan entre 5 y 15 milésimas por detrás en SVR, Kernel Ridge, TR-KRR, DenseWeight y GPR–XGBoost: 16 sorteos aleatorios no bastan para ubicar el óptimo en un espacio de dos a diez dimensiones. En RIM y TCR-XGBoost la brecha es nula o de unas décimas de milésima (las cinco estrategias llegan al mismo punto de una grilla minúscula). La mayor brecha del capítulo, 16 milésimas, es la de DEAP en logicDT, cuyo mejor individuo ya estaba en la generación 0. Para comparar, la desviación estándar del RMSE entre los cinco folds internos es de 0,025 a 0,060 (véase `SD interna` en `analisis_originales/salidas/hpo_resumen.csv`): **salvo Random y Halving, la elección de estrategia mueve el criterio mucho menos que el ruido de la propia partición**.

Los hiperparámetros finales, guardados en `seleccion_antes_test.json` antes de inferir sobre test, son:

| Modelo | Método final | Hiperparámetros finales |
| --- | --- | --- |
| SVR RBF | TPE | `C` = 20,8041; `epsilon` = 0,4658; `gamma` = 0,0030 |
| Kernel Ridge RBF | TPE | `alpha` = 0,3002; `gamma` = 0,0104 |
| TR-KRR RBF | TPE | `alpha` = 0,0643; `gamma` = 0,0055 |
| DenseWeight-XGB | Grid | `learning_rate` = 0,0200; `max_depth` = 2; `min_child_weight` = 1; `n_estimators` = 600; `reg_lambda` = 10,0000; `weight_alpha` = 0,0000 |
| TCR-XGBoost | Grid | `fraction` = 0,2000; `weight` = 0,3000; XGBoost base: `n_estimators` = 442; `max_depth` = 2; `learning_rate` = 0,0152 |
| LinXGBoost | TPE | `n_estimators` = 3; `learning_rate` = 0,1464; `min_samples_leaf` = 137; `reg_lambda` = 0,2082; `gamma` = 48,7307 |
| logicDT adaptado | Grid | `extra_vars` = 2; `max_conj` = 3; `nodesize_frac` = 0,1000 |
| GPR–XGBoost | DEAP | `n_estimators` = 226; `learning_rate` = 0,0033; `max_leaves` = 9; `reg_lambda` = 2,3117 |
| RIM | Grid | `epochs` = 30; `n_neighbors` = 15; `weight_decay` = 0,0100 |

Tres observaciones sobre esos valores. **DenseWeight eligió `weight_alpha` = 0**: la mejor configuración desactiva la ponderación y es, de hecho, un XGBoost clásico de 600 árboles, profundidad 2 y `reg_lambda` = 10. **TCR eligió el peso más fuerte de su dominio** (`weight` = 0,3) sobre la fracción máxima (`fraction` = 0,2), un valor en el borde: no se puede descartar que un dominio más amplio hubiera favorecido otra combinación, aunque la diferencia en RMSE interno entre candidatos de TCR es de milésimas. **LinXGBoost terminó con `gamma` = 48,7**, a un 3 % del límite superior (50), y `n_estimators` = 3, de un máximo de 5; **logicDT terminó con `nodesize_frac` = 0,1**, el límite superior del dominio. Esos «óptimos en el borde» son una señal de que el dominio podría extenderse y se declaran como limitación.

El método ganador de cada búsqueda no se fija de antemano. En los cinco folds externos y en el ajuste final (54 búsquedas, de las cuales seis de LinXGBoost son solo TPE), la estrategia elegida fue:

| Modelo | Fold 1 | Fold 2 | Fold 3 | Fold 4 | Fold 5 | Final |
| --- | --- | --- | --- | --- | --- | --- |
| SVR RBF | DEAP | TPE | TPE | Grid | Grid | TPE |
| Kernel Ridge RBF | DEAP | TPE | TPE | Grid | TPE | TPE |
| TR-KRR RBF | DEAP | TPE | TPE | TPE | TPE | TPE |
| DenseWeight-XGB | DEAP | DEAP | TPE | Grid | Grid | Grid |
| TCR-XGBoost | Grid | Grid | Grid | Grid | Grid | Grid |
| LinXGBoost | TPE | TPE | TPE | TPE | TPE | TPE |
| logicDT adaptado | Grid | Grid | Grid | TPE | Grid | Grid |
| GPR–XGBoost | DEAP | DEAP | TPE | DEAP | TPE | DEAP |
| RIM | Grid | Grid | Grid | Grid | Grid | Grid |

Excluyendo LinXGBoost (48 búsquedas con las cinco estrategias disponibles), el Grid ganó 23 veces, TPE 16 y DEAP 9; **Random y Halving no ganaron ninguna**. Como cada fold externo elige su propio método, la evaluación OOF de la sección siguiente mide el **procedimiento completo** (comparar cinco estrategias y quedarse con la mejor) y no una configuración fija.

### Presupuesto computacional y tiempos de ejecución

Toda la ejecución se instrumentó con `time.perf_counter()` antes de lanzarla (registro central `TIEMPOS_EJECUCION.md`; eventos crudos en `tiempos/<ejecución>/`). Hardware: CPU, sin GPU; cada evaluación ajusta sus cinco folds internos en **4 procesos con un hilo por proceso**; estrategias, ensayos y modelos se ejecutan secuencialmente. El tiempo de búsqueda incluye preparación, ajuste, scoring y coordinación, y **excluye el refit**, que se mide aparte. Los nueve modelos se ejecutaron en cinco corridas: SVR, Kernel Ridge y TR-KRR (`20261019_083039_147f9845`), DenseWeight (`20261019_144732_b7acf148`), TCR y logicDT (`20261020_100140_8f327baf`), GPR–XGBoost y RIM (`20261020_103916_fb6c8c6d`) y LinXGBoost con su búsqueda ampliada (`20261020_150908_3a07b335`). Cada modelo conserva el identificador de su ejecución en `catalog.json`.

**Número de evaluaciones y ajustes internos** de la búsqueda final (configuraciones evaluadas / ajustes de pipeline; cada configuración a fidelidad completa cuesta cinco ajustes):

| Modelo | Grid | Random | TPE | DEAP | Halving |
| --- | ---: | ---: | ---: | ---: | ---: |
| SVR RBF | 27 / 135 | 16 / 80 | 20 / 100 | 13 / 65 | 28 / 140 |
| Kernel Ridge RBF | 35 / 175 | 16 / 80 | 20 / 100 | 16 / 80 | 28 / 140 |
| TR-KRR RBF | 35 / 175 | 16 / 80 | 20 / 100 | 16 / 80 | 28 / 140 |
| DenseWeight-XGB | 96 / 480 | 16 / 80 | 20 / 100 | 23 / 115 | 28 / 140 |
| TCR-XGBoost | 10 / 50 | 6 / 30 | 8 / 40 | 6 / 30 | 12 / 60 |
| LinXGBoost | — | — | 40 / 200 | — | — |
| logicDT adaptado | 33 / 165 | 16 / 80 | 20 / 100 | 10 / 50 | 28 / 140 |
| GPR–XGBoost | 54 / 270 | 16 / 80 | 20 / 100 | 23 / 115 | 28 / 140 |
| RIM | 8 / 40 | 8 / 40 | 6 / 30 | 5 / 25 | 16 / 80 |

DEAP evalúa solo las configuraciones **fenotípicamente únicas**: aunque su presupuesto nominal es 8 × 4 = 32 individuos, los duplicados reutilizan el fitness (5 a 23 evaluaciones reales). Halving evalúa 28 configuraciones, pero 16 al 25 % y 8 al 50 % de los estudiantes: su costo equivale a unas **12 evaluaciones completas**.

**Tiempo total de la búsqueda final en todo train** (segundos de pared):

| Modelo | Grid | Random | TPE | DEAP | Halving |
| --- | ---: | ---: | ---: | ---: | ---: |
| SVR RBF | 10,41 | 5,24 | 8,17 | 4,57 | 4,82 |
| Kernel Ridge RBF | 8,55 | 2,75 | 3,48 | 2,89 | 2,53 |
| TR-KRR RBF | 5,36 | 2,26 | 2,93 | 2,19 | 2,31 |
| DenseWeight-XGB | 76,25 | 10,31 | 12,53 | 17,99 | 14,66 |
| TCR-XGBoost | 8,29 | 5,08 | 6,74 | 5,04 | 8,63 |
| LinXGBoost | — | — | 284,37 | — | — |
| logicDT adaptado | 127,89 | 77,91 | 88,67 | 41,64 | 81,40 |
| GPR–XGBoost | 215,71 | 97,77 | 91,87 | 115,02 | 244,38 |
| RIM | 127,26 | 120,99 | 103,07 | 80,70 | 114,54 |

**Suma de las cinco búsquedas en los folds externos** (segundos de pared; cinco búsquedas secuenciales, sin sumar los ajustes internos paralelos ni la búsqueda final):

| Modelo | Grid | Random | TPE | DEAP | Halving |
| --- | ---: | ---: | ---: | ---: | ---: |
| SVR RBF | 44,10 | 19,61 | 29,76 | 15,82 | 19,22 |
| Kernel Ridge RBF | 34,71 | 15,65 | 19,65 | 15,89 | 18,68 |
| TR-KRR RBF | 25,49 | 10,69 | 15,56 | 11,99 | 14,30 |
| DenseWeight-XGB | 378,34 | 51,69 | 62,93 | 76,30 | 76,14 |
| TCR-XGBoost | 39,90 | 21,91 | 25,00 | 27,41 | 35,03 |
| LinXGBoost | — | — | 957,35 | — | — |
| logicDT adaptado | 547,58 | 335,52 | 277,37 | 133,76 | 315,57 |
| GPR–XGBoost | 2.512,14 | 417,37 | 389,75 | 468,98 | 827,42 |
| RIM | 475,09 | 525,85 | 365,32 | 302,24 | 356,44 |

**Tiempo por evaluación individual** (búsqueda final ÷ configuraciones evaluadas; cada evaluación ajusta cinco pipelines en paralelo) y **tiempo medio de un ajuste interno** (un solo pipeline):

| Modelo | s/eval. Grid | s/eval. Random | s/eval. TPE | s/eval. DEAP | s/eval. Halving | Ajuste interno medio (TPE, s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SVR RBF | 0,385 | 0,328 | 0,409 | 0,352 | 0,172 | 0,1680 |
| Kernel Ridge RBF | 0,244 | 0,172 | 0,174 | 0,180 | 0,090 | 0,0746 |
| TR-KRR RBF | 0,153 | 0,142 | 0,147 | 0,137 | 0,083 | 0,0593 |
| DenseWeight-XGB | 0,794 | 0,645 | 0,626 | 0,782 | 0,524 | 0,3073 |
| TCR-XGBoost | 0,829 | 0,846 | 0,842 | 0,840 | 0,720 | 0,4224 |
| LinXGBoost | — | — | 7,109 | — | — | 4,1258 |
| logicDT adaptado | 3,876 | 4,870 | 4,433 | 4,164 | 2,907 | 2,5279 |
| GPR–XGBoost | 3,995 | 6,111 | 4,593 | 5,001 | 8,728 | 2,3674 |
| RIM | 15,908 | 15,124 | 17,178 | 16,140 | 7,159 | 9,3344 |

El costo por evaluación lo determina el **modelo**, no la estrategia, y varía en dos órdenes de magnitud: los kernels cuestan 0,1 a 0,4 s por evaluación; los XGBoost con pesos, 0,5 a 0,85 s; logicDT, 3 a 5 s; GPR–XGBoost, 4 a 9 s; LinXGBoost, 7 s y RIM, 7 a 17 s. La búsqueda final de LinXGBoost (40 ensayos de TPE) tardó 284 s y la de RIM (cinco estrategias) entre 81 y 127 s cada una, frente a 2 a 10 s de los kernels. En GPR–XGBoost los tiempos de las evaluaciones **no incluyen el cómputo de la etapa GPR**, que se calcula una vez por conjunto de ajuste y se comparte entre candidatos (91 y 182 cómputos en las dos corridas, con 2.444,7 s y 9.920,2 s de CPU acumulada de proceso, en cuatro procesos paralelos; no son tiempo de pared ni se suman a los tiempos por candidato). Es probable que por eso las búsquedas externas de Grid de GPR–XGBoost parezcan mucho más costosas que las de las otras estrategias (la primera estrategia de cada búsqueda paga el cómputo de la etapa GPR); esa atribución no se verificó a nivel de ensayo.

Agregando los ocho modelos con las cinco estrategias (se excluye LinXGBoost, que solo tiene TPE), el consumo por estrategia fue:

| Estrategia | Ajustes internos (final) | Evaluaciones (final) | Costo equivalente completo | Tiempo final (s) | Tiempo 5 externas (s) | Total (s) | Veces elegida (de 48) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Grid | 1.490 | 298 | 298,0 | 579,7 | 4.057,4 | 4.637,1 | 23 |
| Random | 550 | 110 | 110,0 | 322,3 | 1.398,3 | 1.720,6 | 0 |
| TPE | 670 | 134 | 134,0 | 317,4 | 1.185,4 | 1.502,8 | 16 |
| DEAP | 560 | 112 | 112,0 | 270,0 | 1.052,4 | 1.322,4 | 9 |
| Halving | 980 | 196 | 85,0 | 473,3 | 1.662,8 | 2.136,1 | 0 |

La lectura costo-beneficio coincide con la de los clásicos: **TPE y el Grid son las estrategias más elegidas, pero TPE cuesta bastante menos**: en los ocho modelos con las cinco estrategias, TPE sumó 1.503 s (búsquedas finales y externas) frente a 4.637 s del Grid, un 68 % menos (el total del Grid incluye 2.512 s de las búsquedas externas de GPR–XGBoost, inflados por el cómputo de su etapa GPR; sin ese modelo la diferencia es menor, pero TPE sigue siendo más barata). DEAP es la más barata. Halving no ahorra tiempo de pared a este tamaño de muestra. Estas cifras dependen de la CPU, del paralelismo y de la muestra, y no se usaron para elegir hiperparámetros.

```{figure} images/originales/hpo_tiempos.png
:alt: Barras en escala logarítmica del tiempo de la búsqueda final por modelo y estrategia.
:name: originales-hpo-tiempos

Tiempo de pared de la búsqueda final por modelo y estrategia (escala logarítmica).
```

**Entrenamiento (refit) e inferencia.** Los tiempos de ajuste de los modelos finales y de inferencia se tomaron de los eventos ya registrados (el refit final sobre los 1.309 registros, los cinco refits externos y la inferencia, sin reentrenar):

| Modelo | Refit final (s) | Refits externos, suma de 5 (s) | Inferencia OOF, 5 lotes (s) | Inferencia test, 188 filas (s) |
| --- | ---: | ---: | ---: | ---: |
| SVR RBF | 0,098 | 0,403 | 0,163 | 0,0131 |
| Kernel Ridge RBF | 0,078 | 0,414 | 0,081 | 0,0096 |
| TR-KRR RBF | 0,047 | 0,241 | 0,074 | 0,0096 |
| DenseWeight-XGB | 0,453 | 1,641 | 0,066 | 0,0307 |
| TCR-XGBoost | 0,412 | 1,732 | 0,080 | 0,0116 |
| LinXGBoost | 6,924 | 13,486 | 0,039 | 0,0103 |
| logicDT adaptado | 1,578 | 7,707 | 0,042 | 0,0053 |
| GPR–XGBoost | 294,258 | 1.252,853 | 0,315 | 0,0846 |
| RIM | 7,460 | 24,985 | 0,292 | 0,0526 |

Cinco modelos se entrenan en menos de medio segundo; LinXGBoost, logicDT y RIM tardan entre 1,6 y 7,5 s; **GPR–XGBoost necesita 294 s** (dominada por el GPR exacto y sus reinicios), tres órdenes de magnitud más que un kernel. La inferencia, en cambio, es barata para todos: menos de 0,1 s para los 188 estudiantes del test, incluso en RIM y en GPR–XGBoost, que dependen de BM25 y del GPR exacto respectivamente. Para un uso interactivo en el tablero, el costo relevante es el de la búsqueda y el refit, no el de la predicción.

### Convergencia: desempeño en cualquier momento

La curva de desempeño en cualquier momento (*anytime performance*) grafica, para cada evaluación *t*, el mejor RMSE interno encontrado hasta *t*, calculado de los registros de ensayos (`trials_<modelo>_<búsqueda>.jsonl`). Para que Halving sea comparable, el eje horizontal usa **evaluaciones completas equivalentes**: una evaluación al 25 % de los estudiantes cuenta 0,25, y las evaluaciones parciales no entran en la curva porque su RMSE no es comparable.

```{figure} images/originales/hpo_anytime_evaluaciones.png
:alt: Nueve paneles con curvas escalonadas del mejor RMSE interno frente al número de evaluaciones equivalentes para cinco estrategias.
:name: originales-hpo-anytime

Mejor RMSE interno hasta la evaluación *t* en la búsqueda final, por modelo y estrategia. El punto marca el final de cada estrategia.
```

```{figure} images/originales/hpo_anytime_tiempo.png
:alt: Nueve paneles con el mejor RMSE interno frente a los segundos de pared acumulados en escala logarítmica.
:name: originales-hpo-anytime-tiempo

La misma curva en función del tiempo de pared acumulado (escala logarítmica).
```

Tres patrones se repiten en los kernels, en DenseWeight y en GPR–XGBoost. Primero, **TPE y DEAP alcanzan casi todo su progreso en las primeras 6 a 10 evaluaciones**; en Kernel Ridge, TPE iguala al mejor punto del Grid (35 evaluaciones) hacia la evaluación 10 y lo supera después. Segundo, el Grid depende del **orden** de la grilla y su desempeño en cualquier momento es pobre aunque su valor final sea competitivo, sobre todo en DenseWeight (96 candidatos) y GPR–XGBoost (54): ahí el Grid gasta decenas de evaluaciones antes de superar a las otras estrategias, pero acaba igualándolas porque la grilla ya contenía la zona óptima. Tercero, Random y Halving se estancan en el mejor de sus 16 sorteos, 5 a 15 milésimas por encima. En TCR-XGBoost y RIM las curvas son casi planas porque el dominio es diminuto.

```{figure} images/originales/hpo_convergencia_tpe_deap.png
:alt: Curvas de TPE y DEAP relativas al mejor Grid en las seis búsquedas de cada modelo.
:name: originales-hpo-convergencia

Convergencia de TPE (verde) y DEAP (amarillo) relativa al mejor punto del Grid; trazo fino = folds externos, grueso = búsqueda final.
```

TPE alcanza el nivel del Grid (brecha ≈ 0) en menos de 12 evaluaciones en casi todas las búsquedas de los kernels, y lo supera en milésimas (valores negativos) en SVR, Kernel Ridge, TR-KRR y GPR–XGBoost, donde los dominios continuos permiten valores intermedios que la grilla no contiene (por ejemplo, `alpha` = 0,300 y `gamma` = 0,0104 en Kernel Ridge). DEAP converge rápido pero se detiene antes, y en logicDT y DenseWeight varias de sus curvas quedan por encima del Grid. En LinXGBoost no hay Grid de referencia.

```{figure} images/originales/hpo_deap_generaciones.png
:alt: Para cada modelo con DEAP, mejor RMSE y RMSE medio por generación, y fracción única y entropía genética.
:name: originales-hpo-deap

DEAP en la búsqueda final: mejor RMSE y media de la población (arriba); diversidad fenotípica y entropía genética (abajo).
```

En **TR-KRR, TCR, logicDT y RIM el mejor individuo ya está en la generación 0** y no mejora después; en SVR, Kernel Ridge, DenseWeight y GPR–XGBoost mejora en las dos primeras generaciones y se estanca. En todos los modelos la media de la población desciende y la diversidad cae: la fracción de configuraciones únicas baja a 0,12–0,50 y la entropía genética llega a 0 en logicDT y RIM. La combinación de **estancamiento del mejor fitness y pérdida de diversidad** es la señal de **convergencia prematura** de un presupuesto exploratorio de 8 individuos y tres generaciones: la ventaja de DEAP proviene más de un buen muestreo inicial que de la evolución, y gana pocas veces (9 de 48). Ni los 20 ensayos de TPE ni las cuatro poblaciones de DEAP demuestran convergencia a un óptimo global.

Las secciones anteriores describieron cómo se eligieron los hiperparámetros. La siguiente evalúa los modelos resultantes.

## Evaluación de modelos

Esta sección presenta, para los nueve modelos originales y el SVM de referencia, el error en entrenamiento, validación externa y prueba; los diagnósticos de residuos; la interpretabilidad SHAP y LIME del modelo líder; y la robustez de las métricas. Los tres conjuntos tienen los mismos significados que en los clásicos:

- **Entrenamiento:** predicciones del modelo final sobre las mismas 1.309 filas con que se ajustó (*in-sample*). Mide capacidad de ajuste, no generalización.
- **Validación (OOF):** predicciones de los cinco modelos externos sobre sus folds reservados. Se reporta la media ± desviación estándar de los cinco folds y la métrica OOF reunida.
- **Prueba (test 202530):** 188 registros de un periodo posterior, predichos solo por el modelo final.

### RMSE y MAE por conjunto

Las desviaciones estándar entre folds de este capítulo son muestrales (ddof = 1); el dashboard muestra la SD poblacional (ddof = 0), por eso sus cifras son algo menores. Los modelos se ordenan por RMSE de validación.

| Modelo | RMSE train | RMSE CV (media ± SD) | RMSE OOF reunido | RMSE test | MAE train | MAE CV (media ± SD) | MAE test | R² CV | R² test |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Kernel Ridge RBF | 0,7576 | 0,8010 ± 0,0419 | 0,8018 | 0,9091 | 0,5938 | 0,6300 ± 0,0367 | 0,7337 | 0,4832 | 0,4512 |
| GPR–XGBoost | 0,0386 | 0,8028 ± 0,0429 | 0,8037 | 0,9029 | 0,0277 | 0,6296 ± 0,0391 | 0,7242 | 0,4807 | 0,4587 |
| TR-KRR RBF | 0,7508 | 0,8056 ± 0,0453 | 0,8066 | 0,9096 | 0,5864 | 0,6335 ± 0,0383 | 0,7308 | 0,4774 | 0,4506 |
| SVR RBF | 0,7681 | 0,8075 ± 0,0418 | 0,8083 | 0,9050 | 0,5991 | 0,6302 ± 0,0405 | 0,7297 | 0,4743 | 0,4562 |
| DenseWeight-XGB | 0,7163 | 0,8143 ± 0,0406 | 0,8151 | 0,9087 | 0,5635 | 0,6434 ± 0,0333 | 0,7301 | 0,4658 | 0,4518 |
| TCR-XGBoost | 0,7459 | 0,8157 ± 0,0343 | 0,8163 | 0,9089 | 0,5874 | 0,6446 ± 0,0266 | 0,7382 | 0,4644 | 0,4515 |
| SVM lineal | 0,7962 | 0,8241 ± 0,0479 | 0,8252 | 0,9299 | 0,6259 | 0,6503 ± 0,0408 | 0,7581 | 0,4530 | 0,4258 |
| logicDT adaptado | 0,7871 | 0,8451 ± 0,0605 | 0,8468 | 0,9689 | 0,6213 | 0,6677 ± 0,0401 | 0,7852 | 0,4231 | 0,3767 |
| LinXGBoost | 0,7758 | 0,8457 ± 0,0565 | 0,8472 | 0,9152 | 0,6102 | 0,6679 ± 0,0502 | 0,7401 | 0,4230 | 0,4438 |
| RIM | 0,5895 | 0,8646 ± 0,0276 | 0,8649 | 0,9883 | 0,4544 | 0,6715 ± 0,0333 | 0,8079 | 0,3981 | 0,3515 |

```{figure} images/originales/eval_resumen_rmse_mae.png
:alt: Barras horizontales de RMSE y MAE por modelo en entrenamiento, validación y prueba, con barras de error en validación.
:name: originales-eval-resumen

RMSE y MAE por modelo y conjunto. En validación, la barra de error es ± 1 desviación estándar entre los cinco folds externos.
```

Como en los clásicos, **el error crece de entrenamiento a validación y de validación a prueba** en casi todos los modelos; la primera brecha mide sobreajuste y la segunda, el cambio de periodo. Los kernels, con RMSE de entrenamiento de 0,75 a 0,77 y de validación de 0,80 a 0,81, tienen una brecha de 4 a 6 centésimas; DenseWeight (0,716 → 0,815) y TCR (0,746 → 0,816) tienen una algo mayor, de 7 a 10 centésimas. **RIM entrena con 0,5895 y valida con 0,8649**, la mayor brecha entre los modelos con error de entrenamiento informativo: la red ajusta ruido del entrenamiento. **GPR–XGBoost muestra un RMSE de entrenamiento de 0,0386, que no es un ajuste perfecto sino un artefacto del método**: al predecir las mismas filas con que se ajustó, el proceso gaussiano exacto (con ruido numérico de 10⁻⁸) las reproduce casi sin error, igual que KNN con `weights = distance` en los clásicos. Su desempeño real es el de validación (0,8037) y prueba (0,9029), que sí usan meta-variables fuera de muestra.

En prueba, todos los modelos pierden entre 0,07 y 0,12 puntos de RMSE respecto de la validación. **logicDT (0,9689) y RIM (0,9883) son los que más pierden (0,12) y quedan peores que el SVM lineal (0,9299)**, mientras los otros siete originales lo superan. El orden en prueba es GPR–XGBoost (0,9029), SVR RBF (0,9050), DenseWeight (0,9087), TCR (0,9089), Kernel Ridge (0,9091), TR-KRR (0,9096) y LinXGBoost (0,9152): los seis primeros abarcan solo 0,007 puntos, es decir, **el orden en prueba entre esos modelos no es informativo**. En cambio, el orden en validación sí coloca a Kernel Ridge (0,8010) primero y a GPR–XGBoost segundo (0,8028).

### Ajuste visual en entrenamiento, validación y prueba

Cada figura muestra, en la fila superior, la nota predicha frente a la real para los tres conjuntos (la diagonal discontinua es la predicción perfecta) y, en la inferior, los residuos (real − predicha) frente a la predicción con la **media del residuo por decil de la predicción**, que permite detectar sesgos sistemáticos.

```{figure} images/originales/eval_m5.png
:alt: Kernel Ridge RBF: predicción frente a nota real y residuos frente a predicción en entrenamiento, validación OOF y test.
:name: originales-eval-m5

Kernel Ridge RBF: ajuste en entrenamiento, validación externa (OOF) y prueba.
```

Kernel Ridge, el líder en validación, deja una media por decil del residuo casi plana: no hay un sesgo sistemático por nivel de predicción, aunque la dispersión es mayor en predicciones bajas. Predice 20 de los 1.309 registros fuera de [0, 5] en validación, menos que el SVM lineal (39).

```{figure} images/originales/eval_m0.png
:alt: SVR RBF: predicción frente a nota real y residuos frente a predicción en entrenamiento, validación OOF y test.
:name: originales-eval-m0

SVR RBF: ajuste en entrenamiento, validación externa (OOF) y prueba.
```

SVR RBF es visualmente casi idéntico a Kernel Ridge: ambos comparten el kernel y difieren en la pérdida (ε-insensible frente a cuadrática). Su RMSE de prueba (0,9050) es el segundo mejor.

```{figure} images/originales/eval_m19.png
:alt: TR-KRR RBF: predicción frente a nota real y residuos frente a predicción en entrenamiento, validación OOF y test.
:name: originales-eval-m19

TR-KRR RBF: ajuste en entrenamiento, validación externa (OOF) y prueba.
```

TR-KRR reproduce a Kernel Ridge con una diferencia de validación de 0,005 puntos de RMSE: la solución iterativa truncada es prácticamente la exacta en estos datos, lo que confirma que el límite de 200 iteraciones no deteriora el ajuste.

```{figure} images/originales/eval_m11.png
:alt: DenseWeight-XGBoost: predicción frente a nota real y residuos frente a predicción en entrenamiento, validación OOF y test.
:name: originales-eval-m11

DenseWeight-XGBoost: ajuste en entrenamiento, validación externa (OOF) y prueba.
```

DenseWeight-XGB comprime las predicciones (rango de validación 1,03 a 5,27) y solo produce 5 predicciones fuera de [0, 5], por la cota suave que imponen los árboles. Como eligió `weight_alpha` = 0, su ajuste es el de un XGBoost clásico con otros hiperparámetros.

```{figure} images/originales/eval_m7.png
:alt: TCR-XGBoost: predicción frente a nota real y residuos frente a predicción en entrenamiento, validación OOF y test.
:name: originales-eval-m7

TCR-XGBoost: ajuste en entrenamiento, validación externa (OOF) y prueba.
```

TCR-XGBoost produce un patrón casi idéntico al de DenseWeight: ajusta algo menos el entrenamiento (0,7459 frente a 0,7163, porque su XGBoost base es el clásico de 442 árboles) y valida prácticamente igual (0,8163 frente a 0,8151).

```{figure} images/originales/eval_m3.png
:alt: LinXGBoost: predicción frente a nota real y residuos frente a predicción en entrenamiento, validación OOF y test.
:name: originales-eval-m3

LinXGBoost: ajuste en entrenamiento, validación externa (OOF) y prueba.
```

LinXGBoost, con solo tres árboles de hojas lineales, se comporta como un modelo lineal regularizado: sus predicciones se extienden a [0,93; 5,70] en validación (21 fuera de [0, 5]), como en el SVM lineal, y su error de validación (0,8472) es peor que el del SVM lineal (0,8252).

```{figure} images/originales/eval_m14.png
:alt: logicDT adaptado: predicción frente a nota real y residuos frente a predicción en entrenamiento, validación OOF y test.
:name: originales-eval-m14

logicDT adaptado: ajuste en entrenamiento, validación externa (OOF) y prueba.
```

logicDT muestra las predicciones más extremas de los nueve modelos: **48 de 1.309 quedan fuera de [0, 5] en validación, con un mínimo de −0,34**. Las hojas con modelos lineales extrapolan cuando una combinación de covariables se sale de lo observado en esa hoja; en el test pierde 0,12 puntos y queda peor que el SVM (0,9689).

```{figure} images/originales/eval_m15.png
:alt: GPR–XGBoost: predicción frente a nota real y residuos frente a predicción en entrenamiento, validación OOF y test.
:name: originales-eval-m15

GPR–XGBoost: ajuste en entrenamiento, validación externa (OOF) y prueba.
```

En entrenamiento GPR–XGBoost cae sobre la diagonal (artefacto descrito arriba); en validación y prueba la nube es tan ancha como la de los kernels. Es el mejor del test (0,9029).

```{figure} images/originales/eval_m16.png
:alt: RIM: predicción frente a nota real y residuos frente a predicción en entrenamiento, validación OOF y test.
:name: originales-eval-m16

RIM: ajuste en entrenamiento, validación externa (OOF) y prueba.
```

RIM presenta la nube más ancha de validación y el mayor sesgo en prueba (residuo medio de +0,24 puntos: subestima de forma sistemática). Con 1.309 registros, es probable que la red no logre aprovechar la información recuperada, aunque este análisis no lo contrasta.

```{figure} images/originales/eval_svm.png
:alt: SVM lineal: predicción frente a nota real y residuos frente a predicción en entrenamiento, validación OOF y test.
:name: originales-eval-svm

SVM lineal (referencia): ajuste en entrenamiento, validación externa (OOF) y prueba.
```

### Estadísticos y diagnósticos de residuos: White y BDS

Los residuos se diagnostican en validación (OOF reunida, 1.309 filas) y en prueba (188 filas) con la misma función del dashboard (`Dash/residual_diagnostics.py`), igual que en [Modelos clásicos](04_modelos_clasicos.md):

- **Test de White** (homocedasticidad): regresión auxiliar de los residuos al cuadrado sobre las predictoras numéricas, sus cuadrados e interacciones (35 grados de libertad tras retirar la dependencia exacta avance = dominio final − inicial). H₀: varianza constante.
- **Test BDS** (independencia): dimensión de inclusión 2 y ε = 1,5 desviaciones estándar, sobre los residuos **en el orden del archivo**. H₀: residuos IID.
- Complementos: normalidad de D'Agostino, Breusch–Pagan frente a la predicción, correlación de Spearman entre |residuo| y predicción, asimetría y conteo de predicciones fuera de la escala.

| Modelo | Conjunto | n | RMSE | Residuo medio | p White | p BDS | p normalidad | p Breusch–Pagan | Spearman \|e\| vs ŷ | Asimetría | Fuera de [0,5] |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Kernel Ridge RBF | Validación OOF | 1309 | 0,8018 | 0,001 | 5,23×10⁻⁷ | 0,0010 | 2,06×10⁻⁴ | 1,65×10⁻⁵ | −0,192 | −0,264 | 20 |
| Kernel Ridge RBF | Test 202530 | 188 | 0,9091 | 0,142 | 0,8241 | 0,4629 | 0,0014 | 4,75×10⁻⁴ | −0,335 | −0,653 | 3 |
| GPR–XGBoost | Validación OOF | 1309 | 0,8037 | 0,002 | 1,03×10⁻⁶ | 0,0014 | 7,87×10⁻⁵ | 3,41×10⁻⁵ | −0,192 | −0,274 | 13 |
| GPR–XGBoost | Test 202530 | 188 | 0,9029 | 0,148 | 0,7124 | 0,4860 | 9,48×10⁻⁴ | 4,70×10⁻⁴ | −0,327 | −0,661 | 1 |
| TR-KRR RBF | Validación OOF | 1309 | 0,8066 | 0,005 | 4,67×10⁻¹⁰ | 0,0018 | 5,96×10⁻⁴ | 4,07×10⁻⁶ | −0,192 | −0,235 | 25 |
| TR-KRR RBF | Test 202530 | 188 | 0,9096 | 0,136 | 0,7996 | 0,3946 | 0,0025 | 3,36×10⁻⁴ | −0,335 | −0,621 | 3 |
| SVR RBF | Validación OOF | 1309 | 0,8083 | −0,018 | 3,19×10⁻⁷ | 0,0017 | 1,83×10⁻⁴ | 3,08×10⁻⁵ | −0,185 | −0,236 | 22 |
| SVR RBF | Test 202530 | 188 | 0,9050 | 0,100 | 0,9232 | 0,4757 | 0,0021 | 8,40×10⁻⁴ | −0,347 | −0,627 | 5 |
| DenseWeight-XGB | Validación OOF | 1309 | 0,8151 | −0,002 | 2,68×10⁻⁶ | 0,0125 | 2,53×10⁻⁴ | 2,63×10⁻⁵ | −0,181 | −0,252 | 5 |
| DenseWeight-XGB | Test 202530 | 188 | 0,9087 | 0,120 | 0,6590 | 0,5918 | 0,0014 | 5,97×10⁻⁴ | −0,308 | −0,649 | 1 |
| TCR-XGBoost | Validación OOF | 1309 | 0,8163 | 0,002 | 3,77×10⁻⁶ | 0,0388 | 3,58×10⁻⁴ | 2,73×10⁻⁵ | −0,167 | −0,252 | 5 |
| TCR-XGBoost | Test 202530 | 188 | 0,9089 | 0,114 | 0,7439 | 0,7148 | 0,0012 | 4,40×10⁻⁴ | −0,300 | −0,673 | 1 |
| SVM lineal | Validación OOF | 1309 | 0,8252 | 0,009 | 4,99×10⁻¹⁹ | 0,0030 | 0,0045 | 6,43×10⁻⁸ | −0,196 | −0,151 | 39 |
| SVM lineal | Test 202530 | 188 | 0,9299 | 0,107 | 0,8178 | 0,5275 | 0,0092 | 1,81×10⁻⁴ | −0,359 | −0,553 | 5 |
| logicDT adaptado | Validación OOF | 1309 | 0,8468 | 0,005 | 1,14×10⁻⁶⁹ | 0,0149 | 8,55×10⁻⁵ | 7,33×10⁻¹⁴ | −0,153 | −0,007 | 48 |
| logicDT adaptado | Test 202530 | 188 | 0,9689 | 0,180 | 0,9099 | 0,2817 | 0,0061 | 2,09×10⁻⁴ | −0,333 | −0,585 | 5 |
| LinXGBoost | Validación OOF | 1309 | 0,8472 | −0,001 | 4,96×10⁻¹³ | 0,0070 | 0,0197 | 3,40×10⁻⁷ | −0,197 | −0,151 | 21 |
| LinXGBoost | Test 202530 | 188 | 0,9152 | 0,098 | 0,8594 | 0,5438 | 0,0072 | 1,74×10⁻⁴ | −0,351 | −0,568 | 5 |
| RIM | Validación OOF | 1309 | 0,8649 | 0,036 | 1,33×10⁻⁶ | 0,0511 | 0,0147 | 2,74×10⁻⁶ | −0,199 | −0,119 | 10 |
| RIM | Test 202530 | 188 | 0,9883 | 0,242 | 0,4974 | 0,7948 | 0,0045 | 7,08×10⁻⁴ | −0,263 | −0,596 | 2 |

**Homocedasticidad.** En validación, White rechaza la varianza constante en los diez modelos (p < 10⁻⁵), y Breusch–Pagan lo confirma en validación y en prueba (p < 10⁻³ en prueba). La correlación negativa entre |residuo| y predicción (−0,15 a −0,20 en validación y −0,26 a −0,36 en prueba) indica que el error es mayor cuando el modelo predice notas bajas. En prueba White no rechaza (p entre 0,50 y 0,92), pero con 188 filas y 35 grados de libertad tiene poca potencia: no rechazar no demuestra homocedasticidad. El caso extremo es **logicDT en validación (p White ≈ 10⁻⁶⁹; p Breusch–Pagan ≈ 10⁻¹⁴)**: sus predicciones fuera de escala generan residuos de varianza muy desigual según el valor de las covariables.

**Independencia.** BDS rechaza IID en validación para ocho de los nueve originales y el SVM (p entre 0,001 y 0,039); RIM queda justo por encima (p = 0,051); en prueba no rechaza en ningún modelo (p entre 0,28 y 0,79). Como en los clásicos, la dependencia en validación refleja la estructura por periodo y programa que las predictoras no capturan (los registros conservan el orden del archivo y la OOF reúne cinco modelos distintos), no autocorrelación temporal en sentido estricto.

**Normalidad y forma.** La normalidad se rechaza en todos los casos (p < 0,02). La asimetría es negativa en prueba (−0,55 a −0,67): hay una cola de residuos muy negativos, estudiantes con nota real baja a quienes el modelo asigna una nota alta. En validación logicDT es prácticamente simétrico (−0,007), y RIM (−0,12) y LinXGBoost (−0,15) tienen una asimetría menor que los kernels (−0,24 a −0,27). El residuo medio en prueba es positivo para todos (+0,10 a +0,24): en 202530 **todos los modelos subestiman en promedio**, una señal de cambio de nivel entre periodos.

### Patrones en los residuos

Las figuras de ajuste muestran los mismos tres patrones que en los clásicos, lo que confirma que son propiedades de la nota y de la información disponible y no de una familia:

1. **Regresión hacia la media.** Las nubes de predicción frente a realidad son más planas que la diagonal: las notas bajas se sobreestiman y las altas se subestiman. En el test, ninguno de los nueve modelos predice menos de 1,37 aunque hay notas reales de 1,0 (los mínimos de las predicciones en prueba oscilan entre 1,37 y 2,10).
2. **Bandas diagonales en los residuos.** Las líneas paralelas descendentes corresponden a notas reales discretas: para una nota fija, residuo = nota − predicción es una recta de pendiente −1, y el techo de la escala (nota 5) acota los residuos positivos. La escala acotada y discreta genera heterocedasticidad por construcción.
3. **Varianza decreciente con la predicción.** La dispersión es mayor a la izquierda: los estudiantes con predicción baja son un grupo heterogéneo.

Un modelo más flexible reduce el error medio pero **no corrige la forma**: los kernels y los híbridos no eliminan la heterocedasticidad ni el sesgo de subestimación en prueba. Las alternativas para el trabajo futuro son modelar la nota como variable acotada (regresión beta u ordinal), estimar la varianza condicional o recortar las predicciones al rango válido. Esto último beneficia a SVM, SVR, Kernel Ridge, TR-KRR, LinXGBoost y especialmente logicDT, que predicen valores fuera de [0, 5].

### Interpretabilidad global y local con SHAP

Los valores de Shapley reparten la diferencia entre la predicción de un caso y una predicción de referencia (la base) entre las variables, de forma que **base + suma de aportes = predicción**. Para la variable *j*:

$$
\phi_j = \sum_{S \subseteq F \setminus \{j\}} \frac{|S|!\,(p-|S|-1)!}{p!}\,\big[v(S \cup \{j\}) - v(S)\big]
$$

donde *F* son las 15 variables originales, *p* = 15 y *v(S)* es la predicción esperada cuando solo se conocen las variables de *S*.

**Alcance de esta sección.** A diferencia de los clásicos, donde se explicaron los siete modelos, en Originales el dashboard explica **solo al modelo líder por RMSE medio de validación cruzada: Kernel Ridge RBF** (0,8010). Calcular SHAP por permutaciones es costoso: con 64 caminos, 16 coaliciones y 32 filas de referencia, cada caso requiere unas 33.000 predicciones del pipeline completo, y para modelos como RIM (recuperación BM25 en cada predicción) o GPR–XGBoost (proceso gaussiano exacto) sería aún más lento. Por eso este capítulo reproduce las explicaciones ya calculadas y guardadas por el dashboard (`explanations.json`), sin recomputarlas, y no las extiende a los otros ocho modelos.

El método es un estimador de **permutaciones antitéticas** sobre las 15 variables originales y el pipeline completo (64 caminos, referencia empírica de 32 filas de train, semilla 42), aplicado a las 1.497 filas con objetivo válido; aquí se usan las 188 del test. No es TreeSHAP ni *permutation feature importance*. La suma de base y aportes reproduce la predicción con un residuo máximo de 9 × 10⁻¹⁶, pero eso **no vuelve exacta la estimación de Shapley**; la diferencia media absoluta entre dos mitades de las referencias es de 0,0455 puntos, un diagnóstico de sensibilidad (no un intervalo ni una garantía de convergencia).

```{figure} images/originales/shap_lider.png
:alt: Kernel Ridge RBF: gráfico resumen SHAP en el test y waterfalls de los casos con menor y mayor error absoluto.
:name: originales-shap-lider

Kernel Ridge RBF: resumen SHAP (arriba) y waterfalls de los casos con menor y mayor error absoluto (abajo).
```

Importancia relativa por variable (media de |SHAP| como porcentaje del total, en el test):

| Variable | % de la suma de media \|SHAP\| |
| --- | ---: |
| Saber 11 · global | 23,1 |
| División académica | 9,0 |
| Asignatura | 9,0 |
| Dominio inicial | 7,2 |
| Tiempo de trabajo | 6,6 |
| Temas por hora | 6,1 |
| Tiempo de pretest | 6,1 |
| Dominio final | 6,0 |

**Saber 11 · global es la variable más importante** (23,1 % de la atribución), 14 puntos porcentuales por encima de la segunda, lo que coincide con lo observado en los clásicos. Siguen División académica y Asignatura (9,0 % cada una), Dominio inicial (7,2 %) y las variables de tiempo. Cada punto del resumen es un estudiante del test; a la derecha eleva la predicción y a la izquierda la reduce, y el color indica valor bajo (azul) o alto (rojo). Saber 11 global y Dominio inicial muestran una relación monótona clara (valores altos elevan la predicción); **Saber 11 · matemáticas aparece con signo invertido** (valores altos en rojo a la izquierda): dado el puntaje global, un puntaje alto en matemáticas aporta negativamente, un efecto de redundancia entre variables correlacionadas, no un efecto causal. Cumplimiento de la meta casi no atribuye (aportes concentrados cerca de cero).

**Caso bien predicho: registro 72 del test** (nota real 3,40; predicción 3,40; base 3,55). El aporte dominante es **Saber 11 · global = 226 con −1,018 puntos**, compensado por Dominio inicial = 65 (+0,421), Dominio final = 71 (+0,174), la categoría de temas finales (+0,119) y la división académica (+0,108). La predicción es correcta porque aportes grandes y opuestos se anulan, no porque el modelo identifique una causa: que un caso tenga error pequeño no valida el modelo.

**Caso con error elevado: registro 118 del test** (nota real 1,00; predicción 4,04). Es **el mismo registro** que obtuvo el mayor error en seis de los siete clásicos. Saber 11 · global = 407 aporta +0,715 y los aportes negativos (asignatura MAT1101, −0,142; división de Ingenierías, −0,141; tiempo de trabajo, −0,116) son pequeños. El modelo no se equivoca por una variable mal leída: el perfil del estudiante es el de alguien con nota alta, y nada en las 15 variables anticipa su resultado. SHAP describe **cómo se construye** la predicción, no por qué el estudiante obtuvo 1,0; ese error es irreducible con la información disponible.

#### Comparación con LIME

LIME ajusta una **regresión lineal ponderada** en un vecindario del caso y sus pesos explican ese sustituto local, no el modelo; SHAP reparte exactamente la predicción del modelo. El dashboard calcula LIME empírico (1.000 filas de train, regresión Ridge local, semilla 42) sobre los mismos dos casos.

**Caso 72 · menor error absoluto.** Predicción de Kernel Ridge 3,399; sustituto LIME 4,127; fidelidad R² 0,798; brecha 0,728 puntos.

| Variable | Condición LIME | Peso LIME | SHAP (permutaciones) |
| --- | --- | ---: | ---: |
| Asignatura | Asignatura = MAT1100 | 0,624 | 0,101 |
| Saber 11 · global | Saber 11 · global <= 314.00 | −0,583 | −1,018 |
| Dominio inicial | Dominio inicial > 10.00 | 0,356 | 0,421 |
| Temas por hora | Temas por hora <= 0.99 | −0,347 | −0,091 |
| Cumplimiento de la meta | Cumplimiento de la meta = Cumplimiento meta | 0,316 | 0,012 |
| Cat. temas finales | Cat. temas finales = 4 Temas Parcial 2 Cálculo I | 0,285 | 0,119 |

**Caso 118 · mayor error absoluto.** Predicción de Kernel Ridge 4,040; sustituto LIME 4,214; fidelidad R² 0,677; brecha 0,173 puntos.

| Variable | Condición LIME | Peso LIME | SHAP (permutaciones) |
| --- | --- | ---: | ---: |
| Cumplimiento de la meta | Cumplimiento de la meta = Cumplimiento meta | 1,116 | 0,022 |
| Saber 11 · global | Saber 11 · global > 370.00 | 0,775 | 0,715 |
| Asignatura | Asignatura = MAT1101 | −0,493 | −0,142 |
| Cat. temas finales | Cat. temas finales = 3 Temas Parcial 1 Cálculo I | −0,395 | 0,062 |
| Cat. temas iniciales | Cat. temas iniciales = 1 Repaso de álgebra y geometría | 0,185 | 0,095 |
| Avance en ALEK | 26.00 < Avance en ALEK <= 38.00 | −0,115 | 0,038 |

Las diferencias son de método, no de cálculo. **Un buen R² del vecindario no garantiza que el sustituto coincida con la predicción**: en el caso 72 el R² local es alto (0,798) y, sin embargo, el sustituto está 0,728 puntos por encima del modelo (4,13 frente a 3,40). Los pesos de LIME más el intercepto suman el sustituto, no la predicción, mientras los aportes SHAP suman exactamente la predicción. En el caso 118, LIME asigna el mayor peso a **Cumplimiento de la meta (+1,12)**, mientras su SHAP es de apenas 0,022 puntos: en el vecindario de filas reales, «cumplir la meta» está correlacionado con dominios y avance altos, y la regresión local atribuye a esa variable binaria una señal que el modelo obtiene de otras. Es el mismo contraste que apareció con XGBoost en los clásicos. En cambio, para Saber 11 · global ambas técnicas coinciden en dirección y magnitud aproximada (+0,78 de LIME y +0,72 de SHAP en el caso 118). Ninguna de las dos explicaciones es causal: describen el comportamiento del modelo y no permiten afirmar que intervenir sobre una variable cambie la nota de un estudiante.

### Robustez y estabilidad de las métricas

La partición (qué estudiantes caen en cada fold) y la aleatoriedad del algoritmo (inicializaciones, submuestreo) son las dos fuentes de variabilidad de una métrica. En este capítulo solo se cuantifica la primera: **no se repitió la validación con semillas distintas** para los modelos originales, porque no se contempló reentrenar los modelos solo para ese fin y los artefactos activos conservan una sola semilla (42). En los clásicos, la desviación por semilla del estimador fue de 0,00004 a 0,0008 y la de la búsqueda inferior a 0,004, un orden de magnitud menor que la variabilidad entre folds; no hay motivo para esperar un comportamiento distinto en los kernels (deterministas dado el kernel), pero sí en los modelos con aleatoriedad intrínseca (XGBoost, logicDT, RIM, GPR–XGBoost), y esa verificación queda pendiente.

#### Media ± desviación estándar entre folds externos

Métricas de validación externa como media ± desviación estándar muestral de los cinco folds:

| Modelo | RMSE | MAE | MAPE (%) | R² | Por fold (1–5) |
| --- | --- | --- | --- | --- | --- |
| Kernel Ridge RBF | 0,8010 ± 0,0419 | 0,6300 ± 0,0367 | 23,64 ± 2,17 | 0,4832 ± 0,0561 | 0,731 · 0,836 · 0,829 · 0,800 · 0,808 |
| GPR–XGBoost | 0,8028 ± 0,0429 | 0,6296 ± 0,0391 | 23,65 ± 2,18 | 0,4807 ± 0,0586 | 0,728 · 0,836 · 0,827 · 0,808 · 0,815 |
| TR-KRR RBF | 0,8056 ± 0,0453 | 0,6335 ± 0,0383 | 23,69 ± 2,23 | 0,4774 ± 0,0585 | 0,735 · 0,854 · 0,833 · 0,793 · 0,812 |
| SVR RBF | 0,8075 ± 0,0418 | 0,6302 ± 0,0405 | 23,61 ± 2,04 | 0,4743 ± 0,0627 | 0,741 · 0,851 · 0,829 · 0,817 · 0,799 |
| DenseWeight-XGB | 0,8143 ± 0,0406 | 0,6434 ± 0,0333 | 24,11 ± 2,34 | 0,4658 ± 0,0590 | 0,742 · 0,836 · 0,839 · 0,828 · 0,827 |
| TCR-XGBoost | 0,8157 ± 0,0343 | 0,6446 ± 0,0266 | 24,12 ± 2,14 | 0,4644 ± 0,0485 | 0,756 · 0,835 · 0,841 · 0,818 · 0,828 |
| SVM lineal | 0,8241 ± 0,0479 | 0,6503 ± 0,0408 | 24,16 ± 2,06 | 0,4530 ± 0,0640 | 0,770 · 0,895 · 0,841 · 0,794 · 0,820 |
| logicDT adaptado | 0,8451 ± 0,0605 | 0,6677 ± 0,0401 | 24,77 ± 2,19 | 0,4231 ± 0,0907 | 0,770 · 0,935 · 0,861 · 0,840 · 0,819 |
| LinXGBoost | 0,8457 ± 0,0565 | 0,6679 ± 0,0502 | 24,86 ± 2,36 | 0,4230 ± 0,0809 | 0,763 · 0,921 · 0,854 · 0,836 · 0,854 |
| RIM | 0,8646 ± 0,0276 | 0,6715 ± 0,0333 | 24,41 ± 2,15 | 0,3981 ± 0,0538 | 0,820 · 0,887 · 0,883 · 0,876 · 0,856 |

```{figure} images/originales/robustez_folds.png
:alt: RMSE de validación por fold externo de los nueve modelos originales y el SVM lineal.
:name: originales-robustez

RMSE de validación por fold externo.
```

La desviación entre folds es de **0,028 a 0,061 puntos de RMSE**, del mismo orden que las diferencias entre los modelos de cabeza (0,002 a 0,008). Las líneas se mueven juntas: el fold 2 es el más difícil para casi todos (0,84 a 0,93) y el fold 1 el más fácil (0,73 a 0,82), de modo que **la variación entre folds es mayor que la separación entre la mayoría de los modelos dentro de un mismo fold**. RIM es el más estable (SD 0,028) pero con el peor nivel; logicDT y LinXGBoost son los más variables (0,057 a 0,061) porque sus hojas lineales extrapolan en folds con perfiles atípicos.

#### ¿Son las diferencias entre modelos mayores que la variabilidad intrínseca?

La tabla compara la diferencia de RMSE medio de CV de cada modelo frente a Kernel Ridge con la desviación entre folds del propio modelo:

| Modelo frente a Kernel Ridge | Δ RMSE medio CV | SD entre folds del modelo | Δ / SD folds | Folds en que gana Kernel Ridge |
| --- | ---: | ---: | ---: | ---: |
| SVM lineal | 0,0231 | 0,0479 | 0,48 | 4 de 5 |
| SVR RBF | 0,0065 | 0,0418 | 0,16 | 4 de 5 |
| TR-KRR RBF | 0,0046 | 0,0453 | 0,10 | 4 de 5 |
| DenseWeight-XGB | 0,0133 | 0,0406 | 0,33 | 4 de 5 |
| TCR-XGBoost | 0,0148 | 0,0343 | 0,43 | 4 de 5 |
| LinXGBoost | 0,0447 | 0,0565 | 0,79 | 5 de 5 |
| logicDT adaptado | 0,0441 | 0,0605 | 0,73 | 5 de 5 |
| GPR–XGBoost | 0,0018 | 0,0429 | 0,04 | 2 de 5 |
| RIM | 0,0636 | 0,0276 | 2,30 | 5 de 5 |

Solo LinXGBoost, logicDT y RIM quedan a más de 0,5 desviaciones por detrás del líder (0,79; 0,73 y 2,30 SD): RIM es el único que se separa con claridad. Frente a SVR RBF y TR-KRR la diferencia es de 0,005 a 0,007 puntos (0,10 a 0,16 SD) y Kernel Ridge los supera en 4 de 5 folds; frente a GPR–XGBoost es de 0,002 puntos (0,04 SD) y **Kernel Ridge solo gana en 2 de 5 folds**. Ante el SVM lineal, DenseWeight y TCR, la ventaja de Kernel Ridge es de 0,013 a 0,023 puntos, entre un tercio y la mitad de la desviación entre folds. Con solo cinco folds dependientes, la inspección de medias y desviaciones no basta para decidir si una diferencia es real: hacen falta pruebas formales con emparejamiento y control de comparaciones múltiples, como las de la sección siguiente.

## Comparación estadística

La comparación sigue el diseño del dashboard en tres etapas: una prueba global que decide si hay alguna diferencia, comparaciones post hoc que identifican cuáles y un contraste por estudiante de los primeros del MCS frente al SVM, complementados con tamaños de efecto. Las etapas 1 y 2 usan exclusivamente las métricas de los cinco folds externos; la etapa 3 usa las predicciones fuera de muestra de esa misma validación y presenta el test solo como complemento descriptivo. El test no participa en la elección de modelos. **Las pruebas cubren 15 modelos** (nueve originales, SVM lineal y cinco clásicos); los once modelos de librería importada y el Dummy quedan fuera.

### Etapa 1 · Prueba global de Friedman

Cada fold externo es un bloque, cada modelo un tratamiento, y se ordena el RMSE dentro de cada fold (rango 1 = menor error; empates promediados). La hipótesis nula es que todos los modelos tienen el mismo rango promedio:

$$
\chi^2_F = \frac{12N}{k(k+1)}\left[\sum_{j=1}^{k} \bar R_j^{\,2} - \frac{k(k+1)^2}{4}\right],\qquad N = 5 \text{ folds},\; k = 15 \text{ modelos}
$$

```{figure} images/originales/stats_friedman_nemenyi.png
:alt: Mapa de rangos por fold y diagrama de diferencia crítica de Nemenyi con los rangos promedio de 15 modelos.
:name: originales-friedman

Rangos del RMSE en cada fold externo (izquierda) y rangos promedio con la diferencia crítica de Nemenyi (derecha).
```

| Modelo | Fold 1 | Fold 2 | Fold 3 | Fold 4 | Fold 5 | Rango promedio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GPR–XGBoost | 1 | 3 | 1 | 6 | 4 | 3,0 |
| Kernel Ridge RBF | 2 | 5 | 2 | 5 | 2 | 3,2 |
| TR-KRR RBF | 3 | 8 | 4 | 3 | 3 | 4,2 |
| SVR RBF | 4 | 7 | 3 | 7 | 1 | 4,4 |
| DenseWeight-XGB | 5 | 4 | 5 | 10 | 8 | 6,4 |
| XGBoost | 6 | 1 | 8 | 8,5 | 10,5 | 6,8 |
| TCR-XGBoost | 7 | 2 | 6 | 8,5 | 10,5 | 6,8 |
| SVM lineal | 11 | 11 | 7 | 4 | 6 | 7,8 |
| Ridge | 10 | 12 | 10 | 1 | 7 | 8,0 |
| Lasso | 8 | 13 | 12 | 2 | 9 | 8,8 |
| Random Forest | 13 | 6 | 9 | 12 | 12 | 10,4 |
| LinXGBoost | 9 | 14 | 11 | 11 | 13 | 11,6 |
| logicDT adaptado | 12 | 15 | 13 | 13 | 5 | 11,6 |
| KNN | 14 | 9 | 15 | 14 | 15 | 13,4 |
| RIM | 15 | 10 | 14 | 15 | 14 | 13,6 |

| Estadístico de Friedman (χ²) | gl | p-valor asintótico | Decisión (α = 0,05) |
| ---: | ---: | ---: | --- |
| 43,4711 | 14 | 7,2×10⁻⁵ | Se rechaza H₀ · exploratorio |

**Se rechaza la hipótesis de rangos iguales**: al menos dos de los 15 modelos difieren. El rechazo es exploratorio por las mismas razones que en los clásicos: cinco bloques y quince modelos están muy por debajo de la recomendación de SciPy para la aproximación χ² (más de diez bloques), y los folds no son independientes porque sus entrenamientos comparten cerca del 75 % de los estudiantes. Además, el rechazo global no identifica qué pares difieren. El rango promedio ordena los modelos casi igual que el RMSE medio, con una diferencia: GPR–XGBoost (rango 3,0) queda por delante de Kernel Ridge (3,2) porque es el primero en dos folds, aunque su RMSE medio es mayor y Kernel Ridge es más regular (rangos 2, 5, 2, 5 y 2). **RIM, KNN, logicDT y LinXGBoost ocupan los cuatro últimos lugares** y concentran buena parte del estadístico.

### Etapa 2 · Comparaciones post hoc

#### Nemenyi (complemento de este informe)

El post hoc clásico para Friedman es la prueba de **Nemenyi** (Demšar, 2006): dos modelos difieren si sus rangos promedio se separan más que la diferencia crítica

$$
CD = q_{\alpha}\sqrt{\frac{k(k+1)}{6N}} = 3{,}391\sqrt{\frac{15 \cdot 16}{6 \cdot 5}} = 9{,}59 ,
$$

con $q_{0,05}$ = 3,391 para 15 modelos (cuantil del rango estudentizado dividido por √2). **Solo cuatro de los 105 pares superan la diferencia crítica**: GPR–XGBoost frente a RIM (Δ rango = 10,6) y frente a KNN (10,4), y Kernel Ridge RBF frente a RIM (10,4) y frente a KNN (10,2). Con 15 modelos y solo cinco folds, la diferencia crítica (9,6) es casi el rango completo de las posiciones (1 a 15), así que Nemenyi no puede distinguir a casi ningún otro par: no es evidencia de equivalencia sino de falta de potencia. Nemenyi no forma parte del dashboard; se añade porque es el compañero habitual de Friedman.

#### Model Confidence Set (MCS · dashboard)

El dashboard usa el **Model Confidence Set** de Hansen, Lunde y Nason: elimina secuencialmente el peor modelo mientras se rechace la igualdad de capacidad predictiva del conjunto restante. La pérdida es el MSE de cada fold; el estadístico es T_R = max |t_ij|, y el bootstrap **enumera los 3.125 remuestreos posibles** de cinco folds con reemplazo (sin semilla ni error Monte Carlo). Se conservan los modelos con p MCS ≥ 0,10:

| Modelo | Rango promedio de pérdida | MSE medio CV | p-valor MCS | En MCS (α = 0,10) | Paso de eliminación |
| --- | ---: | ---: | ---: | ---: | ---: |
| GPR–XGBoost | 3,0 | 0,6459 | 0,4464 | Sí | 14 |
| Kernel Ridge RBF | 3,2 | 0,6429 | 1,0000 | Sí | 15 |
| TR-KRR RBF | 4,2 | 0,6506 | 0,3488 | Sí | 13 |
| SVR RBF | 4,4 | 0,6534 | 0,3488 | Sí | 12 |
| DenseWeight-XGB | 6,4 | 0,6644 | 9,60×10⁻⁴ | No | 5 |
| XGBoost | 6,8 | 0,6661 | 9,60×10⁻⁴ | No | 7 |
| TCR-XGBoost | 6,8 | 0,6663 | 9,60×10⁻⁴ | No | 6 |
| SVM lineal | 7,8 | 0,6810 | 0,0346 | No | 11 |
| Ridge | 8,0 | 0,6832 | 0,0336 | No | 10 |
| Lasso | 8,8 | 0,6895 | 0,0192 | No | 9 |
| Random Forest | 10,4 | 0,6891 | < 10⁻³⁰⁰ | No | 3 |
| LinXGBoost | 11,6 | 0,7177 | < 10⁻³⁰⁰ | No | 4 |
| logicDT adaptado | 11,6 | 0,7171 | 0,0045 | No | 8 |
| KNN | 13,4 | 0,7324 | < 10⁻³⁰⁰ | No | 2 |
| RIM | 13,6 | 0,7481 | < 10⁻³⁰⁰ | No | 1 |

**Cómo leer las columnas del MCS.**

- **Rango promedio de pérdida.** En cada fold externo se ordenan los modelos por su MSE (rango 1 = menor pérdida) y se promedian los cinco rangos. Es una medida descriptiva de regularidad: un valor bajo indica que el modelo suele estar entre los mejores de cada fold. No es el criterio que decide el conjunto; por eso el orden por rango puede diferir del orden por MSE medio (por ejemplo, GPR–XGBoost tiene rango 3,0 y Kernel Ridge 3,2, pero Kernel Ridge tiene menor MSE medio).
- **Paso de eliminación.** Es el orden en que el procedimiento retira modelos: parte de los 15 y, en cada paso, elimina el peor mientras se rechace que todos los restantes tengan igual capacidad predictiva. El **paso 1 es el primer eliminado** (el peor, aquí RIM) y el **paso 15 corresponde al último sobreviviente** (aquí Kernel Ridge RBF). Un número alto significa, por tanto, que el modelo resistió más.
- **p-valor MCS.** Es el valor p asociado a cada modelo en el procedimiento secuencial: la probabilidad, bajo la hipótesis de igualdad de capacidad predictiva del conjunto vigente, de observar un estadístico T_R al menos tan extremo como el observado, tomando como valor del modelo el **mayor p alcanzado hasta su eliminación** (así el p-valor no decrece a medida que el modelo sobrevive más). Por construcción, el último sobreviviente tiene p = 1 y por eso Kernel Ridge aparece con 1,0000; que dos modelos compartan el mismo p (TR-KRR y SVR, 0,3488) es resultado de esa regla. **No es la probabilidad de que el modelo sea el mejor.**
- **En MCS (α = 0,10).** Un modelo pertenece al conjunto de confianza si su p-valor MCS es **mayor o igual que 0,10**; con un p menor, el procedimiento lo rechazó como equivalente al mejor. «Sí» quiere decir que los datos **no permiten descartarlo**, no que sea demostrablemente igual de bueno que los demás; «No» quiere decir que fue eliminado con evidencia en su contra.

Leída la tabla de arriba abajo: Kernel Ridge (paso 15, p = 1) y GPR–XGBoost (paso 14, p = 0,45), TR-KRR (paso 13, p = 0,35) y SVR (paso 12, p = 0,35) superan el umbral de 0,10 y entran. DenseWeight, XGBoost y TCR (pasos 5 a 7, p ≈ 0,001) y todos los demás quedan por debajo y salen. Con solo cinco folds el MCS tiene poca potencia y el umbral de 0,10 es una convención, no una garantía.

El conjunto exploratorio conserva **cuatro modelos: Kernel Ridge RBF, GPR–XGBoost, TR-KRR y SVR RBF**, es decir, los tres kernels y el híbrido. **Ningún modelo basado solo en árboles (XGBoost, DenseWeight, TCR, Random Forest) ni lineal (SVM, Ridge, Lasso) entra en el conjunto**, y RIM, KNN y Random Forest son los primeros eliminados. Este conjunto **no tiene una cobertura del 90 % demostrada**: el remuestreo de cinco folds dependientes no corrige esa dependencia, y un p MCS no es la probabilidad de que un modelo sea el mejor.

#### Comparaciones dirigidas entre finalistas · métodos explorados

Tras el MCS se compararon entre sí los cuatro finalistas (seis pares). La tabla muestra el intervalo percentil de las diferencias de MSE por folds (descriptivo, no estacionario) y la adaptación del contraste de Diebold–Mariano con corrección de Harvey, Leybourne y Newbold (HLN) por estudiante, con 1.293 estudiantes y error estándar agrupado por estudiante, que se explica en la Etapa 3:

| Modelo A | Modelo B | Δ MSE (A − B) | IC 95 % Δ MSE · folds | Δ RMSE | IC 95 % Δ RMSE · estudiantes | p crudo | p con HLN |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Kernel Ridge RBF | GPR–XGBoost | −0,0030 | [−0,0091; 0,0032] | −0,0019 | [−0,0055; 0,0018] | 0,3244 | 0,3247 |
| Kernel Ridge RBF | TR-KRR RBF | −0,0076 | [−0,0204; 0,0041] | −0,0047 | [−0,0118; 0,0012] | 0,1622 | 0,1626 |
| Kernel Ridge RBF | SVR RBF | −0,0104 | [−0,0237; 0,0039] | −0,0065 | [−0,0134; 0,0004] | 0,0649 | 0,0653 |
| GPR–XGBoost | TR-KRR RBF | −0,0046 | [−0,0197; 0,0124] | −0,0029 | [−0,0121; 0,0051] | 0,5165 | 0,5167 |
| GPR–XGBoost | SVR RBF | −0,0075 | [−0,0209; 0,0099] | −0,0046 | [−0,0127; 0,0034] | 0,2632 | 0,2636 |
| TR-KRR RBF | SVR RBF | −0,0028 | [−0,0211; 0,0122] | −0,0018 | [−0,0090; 0,0053] | 0,6297 | 0,6299 |

**Ningún par de finalistas difiere**: el menor p crudo es el de Kernel Ridge frente a SVR RBF (0,065), y los seis intervalos incluyen el cero tanto por folds como por estudiantes. Los cuatro finalistas son estadísticamente indistinguibles entre sí; la ventaja descriptiva de Kernel Ridge sobre SVR (0,0065 puntos de RMSE) es menor que una sexta parte de la desviación entre folds. Las pruebas de Giacomini–White, Clark–West y el bootstrap estacionario **no son aplicables** a este diseño: no hay una serie ordenada de pronósticos con horizonte definido, ni una pareja anidada restringida/ampliada, ni una secuencia estacionaria. Los folds no son tiempo.

### Etapa 3 · Contraste tipo Diebold–Mariano por estudiante frente al SVM

Las etapas anteriores ordenan los modelos, pero no responden la pregunta práctica: **¿algún modelo original se equivoca significativamente menos que el SVM lineal?** Esta etapa usa el mismo contraste que la de los clásicos. Para cada estudiante se mide cuánto más (o menos) se equivoca el modelo candidato que el SVM, con el error cuadrático como pérdida, y se promedia esa diferencia entre estudiantes. La hipótesis nula es que **en promedio ambos modelos se equivocan lo mismo**; una diferencia negativa favorece al candidato. El DM y la corrección HLN se diseñaron para series de tiempo; aquí la observación es el **estudiante** (1.309 registros de 1.293 estudiantes; 16 con dos registros, siempre en el mismo periodo), el error estándar es robusto por estudiante en lugar de HAC (equivale en la práctica a una prueba pareada), la corrección HLN se aplica con h = 1, las pérdidas son las predicciones fuera de muestra de la validación cruzada y el IC 95 % se obtiene remuestreando estudiantes (9.999 réplicas, semilla 20261020). La adaptación es exploratoria.

Sea $D_i$ la suma, sobre los registros del estudiante $i$, de la diferencia de error cuadrático entre el modelo y el SVM, $n_i$ su número de registros y $G$ el número de estudiantes. Entonces

$$
\bar d = \frac{\sum_i D_i}{\sum_i n_i},\qquad
\widehat{SE} = \frac{1}{\sum_i n_i}\sqrt{\frac{G}{G-1}\sum_{i=1}^{G}\left(D_i - \bar d\, n_i\right)^2},\qquad
z = \frac{\bar d}{\widehat{SE}} ,
$$

y la corrección HLN multiplica $z$ por $\sqrt{(G-1)/G}$ y compara con una $t$ de Student con $G-1$ grados de libertad.

```python
def clustered_test(loss_ref, loss_new, groups):
    d = pd.DataFrame({'d': loss_new - loss_ref, 'g': groups}).groupby('g')['d'].agg(['sum', 'size'])
    G, total = len(d), d['size'].sum()
    mean = d['sum'].sum() / total
    se = np.sqrt(G / (G - 1) * ((d['sum'] - mean * d['size']) ** 2).sum()) / total
    z = mean / se
    z_hln = z * np.sqrt((G - 1) / G)                                # HLN, h = 1
    return z, 2 * norm.sf(abs(z)), 2 * t.sf(abs(z_hln), G - 1)      # p normal y p con HLN
```

**Qué modelos se comparan.** Los cinco primeros del MCS, en el orden en que el propio MCS los elimina y omitiendo al SVM, que es la referencia: Kernel Ridge RBF, GPR–XGBoost, TR-KRR, SVR RBF y, para completar los cinco, Ridge (el siguiente en el orden de eliminación). Cada modelo se compara únicamente contra el SVM, como una pregunta propia; no se comparan entre sí. Como no se declara una conclusión conjunta, **no se aplica la corrección de Holm**; el costo es que, con cinco pruebas separadas, la probabilidad de que alguna resulte significativa por azar supera el 5 %.

| Modelo vs SVM | Posición MCS | Δ MSE | Δ RMSE (puntos) | IC 95 % ΔRMSE | p crudo | p con HLN | p t corregida (CV) | Conclusión |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Kernel Ridge RBF | 1 | −0,0380 | −0,0234 | [−0,0384; −0,0099] | 0,0016 | 0,0016 | 0,2466 | Mejora significativa |
| GPR–XGBoost | 2 | −0,0351 | −0,0215 | [−0,0384; −0,0062] | 0,0095 | 0,0096 | 0,3349 | Mejora significativa |
| TR-KRR RBF | 3 | −0,0304 | −0,0187 | [−0,0287; −0,0087] | 0,0003 | 0,0003 | 0,1937 | Mejora significativa |
| SVR RBF | 4 | −0,0276 | −0,0169 | [−0,0297; −0,0047] | 0,0090 | 0,0092 | 0,3768 | Mejora significativa |
| Ridge | 5 | 0,0022 | 0,0014 | [−0,0064; 0,0096] | 0,7488 | 0,7490 | 0,7807 | Diferencia no significativa |

**Los cuatro primeros —los tres kernels y el híbrido— son significativamente mejores que el SVM lineal en la prueba por estudiante** (p crudo entre 0,0003 y 0,0095; ΔRMSE entre −0,017 y −0,023 puntos), mientras Ridge, quinto, no se distingue del SVM (p = 0,749). Es un resultado distinto del de los clásicos, donde ningún modelo mejoró al SVM. Dos advertencias son indispensables. Primero, la **prueba conservadora** de la última columna antes de la conclusión (t corregida de Nadeau–Bengio con los cinco folds y 4 grados de libertad) **no confirma ninguna de las cuatro mejoras** (p entre 0,19 y 0,38): la prueba por estudiante trata los modelos como fijos y no incluye la variabilidad de reentrenar con otros datos, así que tiende a ser optimista, y la conservadora, con solo cinco observaciones y un error estándar agrandado por el solapamiento de los entrenamientos, tiene muy poca potencia. Segundo, los cinco modelos se eligieron por su desempeño en esta misma validación (MCS) y la multiplicidad no se corrige. La lectura honesta es que **hay evidencia exploratoria de que los kernels y el híbrido superan al SVM lineal en esta muestra, pero no evidencia de que lo seguirían haciendo con otros estudiantes**.

**Complemento en el test temporal (202530).** El mismo contraste sobre los 188 estudiantes del periodo reservado sirve para ver si el signo se mantiene fuera de la validación cruzada. Los modelos son fijos y el test ya había sido revisado, de modo que es descriptivo y con menor potencia:

| Modelo vs SVM | Δ RMSE (puntos) | IC 95 % ΔRMSE | p crudo | p con HLN | Conclusión |
| --- | ---: | ---: | ---: | ---: | --- |
| Kernel Ridge RBF | −0,0208 | [−0,0458; 0,0018] | 0,0927 | 0,0952 | Diferencia no significativa |
| GPR–XGBoost | −0,0270 | [−0,0550; −0,0010] | 0,0512 | 0,0534 | Diferencia no significativa |
| TR-KRR RBF | −0,0203 | [−0,0441; 0,0020] | 0,0882 | 0,0908 | Diferencia no significativa |
| SVR RBF | −0,0249 | [−0,0485; −0,0049] | 0,0261 | 0,0277 | Mejora significativa |
| Ridge | −0,0129 | [−0,0345; 0,0037] | 0,1998 | 0,2026 | Diferencia no significativa |

En el test **los cinco modelos mantienen el signo favorable** (ΔRMSE entre −0,013 y −0,027), pero solo SVR RBF alcanza significancia (p = 0,026; con HLN 0,028); GPR–XGBoost queda en el límite (p = 0,051), y Kernel Ridge y TR-KRR no la alcanzan (p ≈ 0,09). El signo se conserva en los cinco, un respaldo cualitativo a la validación, pero **la magnitud y la significancia no son estables entre los dos conjuntos**, y con 188 estudiantes el intervalo de cada diferencia incluye el cero para Kernel Ridge, TR-KRR y Ridge.

**Alcance y límites.** (1) El p por estudiante no incorpora la variabilidad de reentrenar con otros estudiantes ni posibles efectos compartidos de contexto (sección del curso, cohorte). (2) Los cinco modelos se eligieron por su desempeño en esta misma validación; ni esa selección ni la multiplicidad están corregidas. (3) Ningún modelo ni parámetro se elige con el test. (4) En la comparación entre los 15 modelos del tablero, la prueba complementaria del test frente al SVM con bootstrap-t y Holm sobre una familia de 14 no encuentra ninguna diferencia con p ajustado < 0,05 (el menor p ajustado es 0,48). Es una prueba más conservadora que la anterior y deja el mismo mensaje: **ninguna diferencia respecto del SVM sobrevive a una corrección por multiplicidad**.

### Tamaño del efecto

La significancia no implica relevancia práctica y la falta de significancia no implica ausencia de efecto. Para los 105 pares de los 15 modelos se calculan, sobre el MSE de los cinco folds, el **delta de Cliff** (δ = P(L_A > L_B) − P(L_A < L_B) sobre las 25 comparaciones cruzadas de folds; no conserva el emparejamiento) y la **d de Cohen emparejada** (d_z = media(L_A − L_B)/SD(L_A − L_B)). Se muestran los efectos de **Kernel Ridge RBF frente a cada uno de los otros 14** y los de **cada modelo frente al SVM lineal**:

| Modelo A | Modelo B | Δ MSE (A − B) | Delta de Cliff | d_z de Cohen | Magnitud (Cliff) |
| --- | --- | ---: | ---: | ---: | --- |
| Kernel Ridge RBF | GPR–XGBoost | −0,0030 | 0,04 | −0,37 | despreciable |
| Kernel Ridge RBF | TR-KRR RBF | −0,0076 | −0,12 | −0,52 | despreciable |
| Kernel Ridge RBF | SVR RBF | −0,0104 | −0,12 | −0,59 | despreciable |
| Kernel Ridge RBF | DenseWeight-XGB | −0,0214 | −0,28 | −1,25 | pequeña |
| Kernel Ridge RBF | XGBoost | −0,0232 | −0,28 | −1,40 | pequeña |
| Kernel Ridge RBF | TCR-XGBoost | −0,0234 | −0,28 | −1,46 | pequeña |
| Kernel Ridge RBF | SVM lineal | −0,0380 | −0,20 | −0,89 | pequeña |
| Kernel Ridge RBF | Ridge | −0,0403 | −0,20 | −0,91 | pequeña |
| Kernel Ridge RBF | Lasso | −0,0465 | −0,20 | −0,96 | pequeña |
| Kernel Ridge RBF | Random Forest | −0,0462 | −0,60 | −2,14 | grande |
| Kernel Ridge RBF | logicDT adaptado | −0,0742 | −0,52 | −1,26 | grande |
| Kernel Ridge RBF | LinXGBoost | −0,0748 | −0,60 | −1,73 | grande |
| Kernel Ridge RBF | KNN | −0,0894 | −0,68 | −3,26 | grande |
| Kernel Ridge RBF | RIM | −0,1051 | −0,84 | −4,05 | grande |

| Modelo (A) | Δ MSE (A − SVM) | Delta de Cliff | d_z de Cohen | Magnitud (Cliff) |
| --- | ---: | ---: | ---: | --- |
| SVR RBF | −0,0276 | −0,12 | −0,66 | despreciable |
| Kernel Ridge RBF | −0,0380 | −0,20 | −0,89 | pequeña |
| TR-KRR RBF | −0,0304 | −0,20 | −1,03 | pequeña |
| DenseWeight-XGB | −0,0166 | −0,04 | −0,28 | despreciable |
| TCR-XGBoost | −0,0146 | −0,12 | −0,27 | despreciable |
| LinXGBoost | 0,0368 | 0,28 | 1,16 | pequeña |
| logicDT adaptado | 0,0361 | 0,20 | 0,96 | pequeña |
| GPR–XGBoost | −0,0350 | −0,20 | −0,73 | pequeña |
| RIM | 0,0671 | 0,44 | 1,23 | mediana |
| KNN | 0,0514 | 0,36 | 0,88 | mediana |
| Ridge | 0,0022 | 0,04 | 0,24 | despreciable |
| Lasso | 0,0085 | 0,04 | 0,54 | despreciable |
| Random Forest | 0,0081 | 0,20 | 0,15 | pequeña |
| XGBoost | −0,0149 | −0,04 | −0,27 | despreciable |

Con los umbrales convencionales de Cliff (|δ| < 0,147 despreciable; < 0,33 pequeño; < 0,474 mediano; ≥ 0,474 grande; Romano et al., 2006), **los efectos de Kernel Ridge frente a SVR, TR-KRR y GPR–XGBoost son despreciables** (|δ| ≤ 0,12): sus distribuciones de MSE por fold se solapan casi por completo. Frente a los modelos con XGBoost y los lineales, δ es pequeño (−0,20 a −0,28) aunque d_z es grande (−0,9 a −1,5), porque las diferencias, pequeñas, tienen el mismo signo en la mayoría de los folds; frente a Random Forest, logicDT, LinXGBoost, KNN y RIM los efectos son grandes (δ de −0,52 a −0,84). Los dos tamaños de efecto miden cosas distintas y deben leerse con la diferencia absoluta, que en RMSE medio de CV va de 0,002 puntos (frente a GPR–XGBoost) a 0,064 (frente a RIM), pequeña en la escala de la nota. No existe un umbral educativo acordado de relevancia práctica.

## Resultados finales y conclusiones

| Modelo | Método de búsqueda final | RMSE CV (media ± SD) | MAE CV | RMSE test | MAE test | Rango Friedman | En MCS | vs SVM en CV (p crudo por estudiante) |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | ---: |
| Kernel Ridge RBF | TPE | 0,8010 ± 0,0419 | 0,6300 | 0,9091 | 0,7337 | 3,2 | Sí | 0,0016 |
| GPR–XGBoost | DEAP | 0,8028 ± 0,0429 | 0,6296 | 0,9029 | 0,7242 | 3,0 | Sí | 0,0095 |
| TR-KRR RBF | TPE | 0,8056 ± 0,0453 | 0,6335 | 0,9096 | 0,7308 | 4,2 | Sí | 0,0003 |
| SVR RBF | TPE | 0,8075 ± 0,0418 | 0,6302 | 0,9050 | 0,7297 | 4,4 | Sí | 0,0090 |
| DenseWeight-XGB | Grid | 0,8143 ± 0,0406 | 0,6434 | 0,9087 | 0,7301 | 6,4 | No | No evaluado |
| TCR-XGBoost | Grid | 0,8157 ± 0,0343 | 0,6446 | 0,9089 | 0,7382 | 6,8 | No | No evaluado |
| SVM lineal | — | 0,8241 ± 0,0479 | 0,6503 | 0,9299 | 0,7581 | 7,8 | No | — |
| logicDT adaptado | Grid | 0,8451 ± 0,0605 | 0,6677 | 0,9689 | 0,7852 | 11,6 | No | No evaluado |
| LinXGBoost | TPE | 0,8457 ± 0,0565 | 0,6679 | 0,9152 | 0,7401 | 11,6 | No | No evaluado |
| RIM | Grid | 0,8646 ± 0,0276 | 0,6715 | 0,9883 | 0,8079 | 13,6 | No | No evaluado |

**Sobre la optimización de hiperparámetros.** Las estrategias de búsqueda inteligente (TPE, DEAP) y el Grid llegan a valores de RMSE interno separados por menos de 3 milésimas en los kernels, en los modelos con XGBoost y en GPR–XGBoost, muy por debajo del ruido entre folds; Random y Halving, con 16 candidatos, quedan hasta 15 milésimas por detrás en los espacios de dos a diez dimensiones. **TPE y el Grid fueron las estrategias más elegidas, pero TPE con un costo bastante menor**; DEAP es la más barata y converge de forma prematura; Halving no aporta ventajas a este tamaño de muestra. Los modelos más costosos (GPR–XGBoost y RIM, más LinXGBoost con su TPE ampliado) concentran el consumo de cómputo sin ventaja predictiva. Varios óptimos quedaron en el borde de su dominio (TCR, LinXGBoost, logicDT) y DenseWeight eligió desactivar su ponderación.

**Sobre el desempeño.** **Kernel Ridge RBF obtiene el menor RMSE medio en validación externa (0,8010)**, seguido de GPR–XGBoost (0,8028), TR-KRR (0,8056) y SVR RBF (0,8075); en prueba el mejor es GPR–XGBoost (0,9029). Los cuatro forman el conjunto MCS y son indistinguibles entre sí. Los tres modelos con XGBoost (DenseWeight, TCR y el XGBoost clásico) quedan en una zona intermedia (0,814 a 0,816), algo mejor que los lineales; **LinXGBoost, logicDT y RIM no mejoran al SVM lineal en validación y los dos últimos tampoco en prueba**. La ventaja de los kernels y del híbrido sobre el SVM (0,017 a 0,023 puntos de RMSE) es significativa en la prueba por estudiante pero no en la conservadora, de modo que es **una indicación consistente en signo (también en el test) y no una demostración**. Con tamaños de efecto despreciables entre los cuatro líderes, la elección entre ellos no se justifica por el error.

**Sobre los residuos.** Todos los modelos comparten heterocedasticidad (White y Breusch–Pagan), dependencia por grupo en validación (BDS), asimetría negativa y regresión hacia la media, además de la subestimación sistemática de 202530. Son propiedades de la nota acotada y discreta y de la información disponible, no de una familia: más flexibilidad no corrige su forma. logicDT y el SVM lineal producen predicciones fuera de [0, 5] con más frecuencia (48 y 39 de 1.309), un defecto corregible con un recorte.

**Sobre la interpretabilidad.** Para el líder, Kernel Ridge, SHAP muestra que el puntaje global de Saber 11 es la variable más influyente (23 %), seguido de la división académica, la asignatura y el dominio inicial, y que el mayor error del test es el mismo registro 118 de los clásicos: un estudiante con perfil de nota alta que obtuvo 1,0. LIME puede atribuir un peso grande a una variable que el modelo casi no usa (cumplimiento de la meta). Las explicaciones describen el modelo, no causas, y solo se calcularon para el líder.

**Decisión.** **Kernel Ridge RBF es el modelo original recomendado para continuar la comparación**, por su menor error medio, su solución exacta y determinista, su costo mínimo (una búsqueda de 3,5 s y un refit de 0,08 s) y su ficha ya explicada con SHAP y LIME; TR-KRR y SVR RBF son alternativas equivalentes. GPR–XGBoost obtiene resultados comparables, pero cuesta unos 300 s de entrenamiento y una cadena de dos etapas que no se justifica con una ventaja indistinguible del kernel simple. Debe tenerse presente que el **respaldo estadístico es exploratorio**: con cinco folds dependientes y una selección hecha sobre la misma validación, la mejora sobre el SVM lineal no está demostrada. Antes de un uso operativo conviene validar en otros periodos, repetir la validación cruzada para aumentar los bloques de Friedman, verificar la sensibilidad a semillas de los modelos estocásticos, ampliar los dominios que tocaron su borde (TCR, LinXGBoost, logicDT) y explorar formulaciones para notas acotadas.

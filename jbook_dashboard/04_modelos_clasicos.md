---
title: Modelos clásicos
description: KNN, Ridge, Lasso, Random Forest, XGBoost y Decision Tree frente al SVM lineal; optimización de hiperparámetros, evaluación, residuos, interpretabilidad SHAP/LIME, robustez y comparación estadística.
---

# Modelos clásicos

Este capítulo amplía la subpestaña **Modelos clásicos** de **03 Modelos predictivos** del dashboard. Allí se presentan las fichas, las tablas y los contrastes de seis regresores clásicos frente al SVM lineal del capítulo anterior; aquí se documenta además **cómo** se obtuvieron, con fragmentos del código real, tablas que no aparecen en el tablero, curvas de convergencia de la búsqueda, diagnósticos de residuos para cada modelo, explicaciones SHAP de los siete regresores y un análisis nuevo de sensibilidad a semillas.

El capítulo se organiza en cinco bloques:

1. **Introducción:** qué modelos se implementaron, qué idea los sostiene y qué comparten con el SVM.
2. **Optimización de hiperparámetros:** las cinco estrategias de búsqueda, la justificación de los rangos, los resultados, el presupuesto computacional, los tiempos y la convergencia.
3. **Evaluación de modelos:** RMSE y MAE en entrenamiento, validación y prueba, diagnósticos de White y BDS, análisis de residuos, interpretabilidad SHAP y comparación con LIME, y robustez frente a folds y semillas.
4. **Comparación estadística:** prueba ómnibus de Friedman, post hoc (Nemenyi, Model Confidence Set y DM-HLN adaptado entre finalistas), contraste por estudiante de los cinco primeros del MCS frente al SVM y tamaños de efecto.
5. **Resultados finales y conclusiones.**

Todas las cifras provienen de la ejecución activa `20261018_102325_af643f83` (`Precalculo/resultados/e3/busquedas/`), la misma que alimenta el dashboard. Las tablas y figuras nuevas se regeneran con `jbook_dashboard/analisis_clasicos/generar_clasicos.py` y la sensibilidad a semillas con `experimentos_semillas.py`; ninguno de los dos reentrena los modelos canónicos ni consulta el test para elegir parámetros.

## Introducción

Todos los modelos de este capítulo son **regresores**: predicen la nota del primer parcial en la escala 0–5. Comparten exactamente el protocolo descrito en [Modelos lineales](03_modelos.md): los mismos 1.309 registros de train (1.293 estudiantes), el mismo test temporal del periodo 202530 (188 registros), los **mismos cinco folds externos** `GroupKFold` por estudiante y cinco folds internos por estudiante para la búsqueda. Por eso sus métricas son comparables fold a fold y se pueden contrastar con pruebas de medidas repetidas.

### Modelos implementados

| Modelo | Familia | Idea central | Preparación dentro del pipeline | Hiperparámetros buscados |
| --- | --- | --- | --- | --- |
| **SVM lineal** (referencia) | Lineal, pérdida ε-insensible | Recta en el espacio transformado que ignora errores menores que ε y penaliza el resto linealmente. | Mediana, `log1p` en tiempos, `StandardScaler`; moda y one-hot con referencia. | `C`, `epsilon` |
| **KNN** | Basado en instancias | Promedia la nota de los *k* estudiantes más parecidos (distancia Minkowski), opcionalmente ponderados por cercanía. | Igual al SVM; las distancias se calculan sobre variables escaladas. | `n_neighbors`, `weights`, `p` |
| **Ridge** | Lineal con penalización L2 | Mínimos cuadrados que encogen todos los coeficientes hacia cero; estabiliza variables correlacionadas. | Igual al SVM. | `alpha` |
| **Lasso** | Lineal con penalización L1 | Mínimos cuadrados que pueden anular coeficientes; realiza selección de variables. | Igual al SVM. | `alpha` |
| **Random Forest** | Ensamble de árboles (bagging) | Promedia muchos árboles entrenados con remuestreo y subconjuntos de variables (`max_features = 0,7`). | Mediana numérica, moda y `OrdinalEncoder`; sin escalado. | `n_estimators`, `max_depth`, `min_samples_leaf` |
| **XGBoost** | Ensamble de árboles (boosting) | Suma árboles poco profundos, cada uno corrige el error del anterior con gradiente de segundo orden y regularización. | Mediana y moda; categorías **nativas** aprendidas en cada fit; `subsample = colsample = 0,8`. | `n_estimators`, `max_depth`, `learning_rate` |
| **Decision Tree** | Árbol CART | Particiones binarias que minimizan el error cuadrático; cada hoja predice la media de su grupo. | Mediana; moda y one-hot completo; sin escalado. | `max_depth`, `min_samples_leaf`, `ccp_alpha` |

La elección cubre los principales sesgos inductivos de la regresión tabular: lineales con distinta penalización (SVM, Ridge, Lasso), un método local no paramétrico (KNN), un árbol interpretable (Decision Tree) y dos ensambles de árboles que capturan no linealidades e interacciones (Random Forest y XGBoost). Las referencias de fundamento enlazadas en el dashboard son [Vapnik/Smola (SVR)](https://doi.org/10.1023/B:STCO.0000035301.49549.88), [Altman (KNN)](https://doi.org/10.2307/2685209), [Hoerl y Kennard (Ridge)](https://doi.org/10.1080/00401706.1970.10488634), [Tibshirani (Lasso)](https://doi.org/10.1111/j.2517-6161.1996.tb02080.x), [Breiman (Random Forest)](https://doi.org/10.1023/A:1010933404324), [Chen y Guestrin (XGBoost)](https://doi.org/10.1145/2939672.2939785) y la [documentación de CART en scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeRegressor.html).

La representación de las variables no es la misma para todas las familias. Los modelos basados en distancias o coeficientes necesitan escalas comparables y codificación one-hot; los árboles no requieren escalado y se benefician de evitar columnas dispersas. Random Forest usa códigos ordinales porque scikit-learn exige entradas numéricas: esto **introduce un orden artificial** en variables nominales, que el árbol puede explotar o ignorar. XGBoost evita ese problema con particiones categóricas nativas. El fragmento siguiente, de `Precalculo/modelos_clasicos.py`, construye cada pipeline; toda imputación, vocabulario y escalado se aprende dentro de cada `fit`:

```python
def classic_pipeline(key):
    if key in ['knn', 'ridge', 'lasso']:
        estimator = {'knn': KNeighborsRegressor(n_jobs=1), 'ridge': Ridge(),
                     'lasso': Lasso(max_iter=100000, tol=1e-4, random_state=42)}[key]
        prep = clone(make_pipeline().named_steps['preprocesamiento'])   # mismo prep. del SVM
    elif key == 'forest':
        prep = ColumnTransformer([
            ('num', SimpleImputer(strategy='median'), NUMERIC),
            ('cat', Pipeline([('imputer', SimpleImputer(strategy='most_frequent')),
                              ('ordinal', OrdinalEncoder(handle_unknown='use_encoded_value',
                                                         unknown_value=-1))]), CATEGORICAL)])
        estimator = RandomForestRegressor(random_state=42, n_jobs=1, max_features=.7)
    elif key == 'xgboost':
        imputation = ColumnTransformer([
            ('num', SimpleImputer(strategy='median'), NUMERIC),
            ('cat', SimpleImputer(strategy='most_frequent'), CATEGORICAL)]).set_output(transform='pandas')
        prep = Pipeline([('imputation', imputation), ('categories', NativeCategories())])
        estimator = XGBRegressor(objective='reg:squarederror', tree_method='hist',
                                 enable_categorical=True, max_cat_to_onehot=1, min_child_weight=3,
                                 subsample=.8, colsample_bytree=.8, reg_lambda=3,
                                 random_state=42, n_jobs=1)
    return Pipeline([('preprocesamiento', prep), ('modelo', estimator)])
```

`NativeCategories` aprende el vocabulario de cada variable categórica solo en entrenamiento; una categoría nueva en validación o test pasa a faltante en lugar de recibir un código inventado. El Decision Tree se construye en `evaluar_decision_tree_e3.py` con mediana, moda y one-hot completo (sin categoría de referencia), porque un árbol no sufre la colinealidad exacta que obliga a eliminar una columna en los modelos lineales.

Las métricas se calculan con la misma función para todos los modelos y conjuntos:

```python
def metrics(y, pred):
    return {'RMSE': float(np.sqrt(mean_squared_error(y, pred))),
            'MAE': float(mean_absolute_error(y, pred)),
            'MAPE (%)': float(100 * mean_absolute_percentage_error(y, pred)),
            'R²': float(r2_score(y, pred))}
```

Con los modelos y su preparación definidos, la siguiente sección explica cómo se eligieron sus hiperparámetros.

## Optimización de hiperparámetros

Esta sección responde cuatro preguntas: qué estrategias de búsqueda se compararon, por qué se eligieron esos rangos, qué encontró cada estrategia y cuánto costó. Al final se analiza la convergencia de las búsquedas bayesiana y genética mediante curvas de desempeño en cualquier momento.

### Protocolo de selección anidada

En **cada uno de los cinco entrenamientos externos** se ejecutan las cinco estrategias sobre los **mismos cinco folds internos** por estudiante. Cada estrategia devuelve su mejor configuración a fidelidad completa y se elige, entre todas, la de menor RMSE medio interno; los empates numéricos (≤ 10⁻¹²) se resuelven por un orden fijado antes de ejecutar: Grid, Random, TPE, DEAP y Halving. El modelo así elegido se reajusta en el entrenamiento externo y predice su fold de validación (predicción OOF). Después se repite exactamente el mismo procedimiento sobre **todo train** para obtener el modelo final, que es el único que predice el test. Ni el fold externo ni el test participan en la búsqueda, y **ningún criterio de tiempo interviene en la selección**.

El bucle externo, de `Precalculo/evaluar_busquedas_e3.py`, resume ese diseño:

```python
for fold, (fit, val) in enumerate(grouped_splits(train), 1):
    fitting, validation = train.iloc[fit], train.iloc[val]
    search = Search(key, fitting, f'externo_{fold}', timing, evidence)   # 5 estrategias × 5 folds internos
    selection = search.run()                                            # menor RMSE interno entre todas
    estimator = timed_fit(timing, key, selection['best_params'], fitting, f'externo {fold}')
    oof[val] = timed_predict(timing, estimator, validation, f'OOF fold {fold}', key)
final = Search(key, train, 'final_train', timing, evidence).run()          # misma comparación en todo train
estimator = timed_fit(timing, key, final['best_params'], train, 'final train')
# Los siete conjuntos de parámetros se guardan en seleccion_antes_test.json antes de predecir test.
```

Cada evaluación de una configuración crea **un pipeline nuevo por fold interno**: el preprocesamiento y el modelo se ajustan solo con el entrenamiento de ese fold, y se verifica que no haya estudiantes compartidos. Esta función es la misma para las cinco estrategias, de modo que todas compiten con la misma medida de calidad:

```python
def manual_fold(key, parameters, frame, fit, val, fidelity, fold):
    groups = frame.iloc[fit][GROUP].unique()
    order = np.random.default_rng(42 + fold).permutation(groups)
    selected = order[:max(2, math.ceil(len(order) * fidelity))]       # fidelidad = fracción de estudiantes
    actual = fit[frame.iloc[fit][GROUP].isin(selected).to_numpy()]
    fitting, validation = frame.iloc[actual], frame.iloc[val]
    assert not set(fitting[GROUP]) & set(validation[GROUP])
    model = pipeline_for(key).set_params(**parameters)                # pipeline nuevo en cada evaluación
    model.fit(fitting[FEATURES], fitting[TARGET])
    pred = model.predict(validation[FEATURES])
    return {'RMSE': metrics(validation[TARGET], pred)['RMSE'], ...}
```

### Estrategias de búsqueda y presupuestos

Los presupuestos se fijaron antes de ejecutar y son idénticos para los siete modelos (salvo el Grid, que conserva cada grilla histórica):

| Estrategia | Cómo explora | Presupuesto por búsqueda | Configuración |
| --- | --- | --- | --- |
| **Grid Search** | Recorre exhaustivamente una grilla discreta fija. | Tamaño de la grilla (8 a 72 puntos) | `ParameterGrid` histórico, determinista |
| **Random Search** | Muestrea configuraciones independientes en dominios continuos. | 16 sorteos | Semilla 42; uniforme en enteros/categorías, loguniforme en `C`, `alpha`, `learning_rate` |
| **Bayesiana · Optuna/TPE** | Modela densidades l(x) de configuraciones buenas y g(x) de las demás, y propone donde l(x)/g(x) es alto. | 20 ensayos (6 aleatorios iniciales) | `TPESampler` independiente, 24 candidatos para aproximar *Expected Improvement* |
| **Genética · DEAP** | Evoluciona una población con selección, cruce y mutación. | Población 8, inicial + 3 generaciones | Torneo 3, cruce uniforme (p = 0,8; 0,5 por gen), mutación por reinicio (p = 0,3; 1/d por gen), élite 1 |
| **Successive Halving** | Evalúa muchos candidatos con poca fidelidad y elimina la mitad peor por ronda. | 16 → 8 → 4 candidatos | Factor 2; 25 %, 50 % y 100 % de los estudiantes del entrenamiento interno |

**Por qué TPE y Expected Improvement.** Los dominios son mixtos: categorías (`weights`, `max_depth` del bosque), enteros (`n_neighbors`, `n_estimators`) y continuos en escala logarítmica (`C`, `alpha`, `learning_rate`). TPE los maneja sin imponer un kernel gaussiano ni una distancia ordinal entre categorías. La adquisición aproxima *Expected Improvement*: busca reducir el mejor RMSE considerando la magnitud esperada de la mejora, no solo su probabilidad (PI) ni una cota de confianza (UCB).

**Por qué estos operadores genéticos.** El torneo de tamaño 3 funciona con un fitness que se minimiza (RMSE) y no exige valores positivos como la ruleta. El cruce uniforme recombina dimensiones sin suponer cercanía ordinal entre categorías, y el elitismo de un individuo evita perder la mejor solución. Los genes se codifican en [0, 1] y se decodifican al dominio, en escala logarítmica cuando corresponde:

```python
def decode(genes, key):
    params = {}
    for gene, (name, spec) in zip(genes, SPACES[key].items()):
        u = min(max(float(gene), 0.), np.nextafter(1., 0.))
        if spec[0] == 'cat':   params[name] = spec[1][min(int(u * len(spec[1])), len(spec[1]) - 1)]
        elif spec[0] == 'int': params[name] = min(spec[2], spec[1] + int(u * (spec[2] - spec[1] + 1)))
        elif spec[0] == 'log': params[name] = float(math.exp(math.log(spec[1]) + u * math.log(spec[2] / spec[1])))
        else:                  params[name] = float(spec[1] + u * (spec[2] - spec[1]))
    return params
```

El núcleo de cada estrategia, en `Precalculo/busquedas_hiperparametros_e3.py`, es corto porque todas delegan la evaluación en la misma función `evaluate` (cinco folds internos en paralelo):

```python
if method == 'Grid Search':
    for params in ParameterGrid(GRIDS_ALL[self.key]): self.evaluate(params)
elif method == 'Random Search':
    for _ in range(16): self.evaluate(decode(rng.random(len(SPACES[self.key])), self.key))
elif method == 'Bayesiana TPE':
    sampler = optuna.samplers.TPESampler(seed=seed, multivariate=False,
                                         n_startup_trials=6, n_ei_candidates=24)
    study = optuna.create_study(direction='minimize', sampler=sampler)
    study.optimize(lambda trial: self.evaluate(suggest(trial, self.key))['RMSE'], n_trials=20)
elif method == 'Genética DEAP':
    self.genetic()                              # torneo 3, cxUniform, reinicio uniforme, élite 1
else:                                           # Successive Halving manual
    candidates = [decode(rng.random(len(SPACES[self.key])), self.key) for _ in range(16)]
    for fraction in [.25, .5, 1.]:
        results = sorted((self.evaluate(p, fraction) for p in candidates), key=lambda t: t['RMSE'])
        if fraction < 1:
            candidates = [t['params'] for t in results[:math.ceil(len(results) / 2)]]
```

Un detalle de implementación condiciona la lectura de los resultados: Random Search y Successive Halving parten del **mismo generador con semilla 42**, de modo que los 16 candidatos iniciales de Halving son exactamente los 16 sorteos de Random. Halving solo puede igualar o empeorar el mejor de Random (si elimina prematuramente al ganador), y ante un empate exacto el orden preestablecido favorece a Random. Por eso Halving **nunca resulta elegido** en las 42 búsquedas, aunque en varias iguala a Random con menos costo.

### Espacios de búsqueda y justificación de los rangos

Los rangos estocásticos amplían los puntos discretos de la grilla histórica, de modo que Random, TPE, DEAP y Halving pueden alcanzar cualquier valor del Grid y también los intermedios. La tabla justifica cada dominio:

| Modelo | Grid (histórico) | Dominio estocástico | Justificación del rango |
| --- | --- | --- | --- |
| SVM lineal | `C` ∈ {0,01; 0,03; 0,1; 0,3; 1; 10}; `epsilon` ∈ {0; 0,05; …; 1} (48) | `C` log[0,01; 10]; `epsilon` [0; 1] | `C` abarca tres órdenes de magnitud, de regularización fuerte a débil; la escala log es natural para un factor multiplicativo. `epsilon` se expresa en puntos de nota: 1 punto equivale a ignorar errores de una unidad, el máximo razonable en una escala 0–5. |
| KNN | `n_neighbors` ∈ {5, …, 101}; `weights`; `p` ∈ {1, 2} (32) | entero [5; 101]; uniform/distance; p 1/2 | Con unos 1.000 registros por entrenamiento, *k* = 5 da un ajuste muy local y *k* ≈ 100 (≈ 10 % de la muestra) uno muy suavizado. `p` compara distancia Manhattan y euclidiana; `distance` pondera por cercanía. |
| Ridge | `alpha` ∈ {0,01; …; 1.000} (8) | log[0,01; 1.000] | Cinco órdenes de magnitud: desde casi mínimos cuadrados hasta coeficientes muy encogidos. Con 67 columnas transformadas y variables correlacionadas, el óptimo esperado está en la zona media. |
| Lasso | `alpha` ∈ {0,0001; …; 0,1} (9) | log[0,0001; 0,1] | Con variables estandarizadas, `alpha` ≥ 0,1 anula casi todos los coeficientes; el límite inferior se acerca a mínimos cuadrados. La grilla se densificó cerca del óptimo histórico (0,0005). |
| Random Forest | `n_estimators` {150, 300, 500}; `max_depth` {4, 6, None}; `min_samples_leaf` {2, 5, 10} (27) | entero [150; 500]; {4, 6, 8, 12, None}; entero [2; 20] | Más de 150 árboles estabiliza el promedio; más de 500 añade costo con ganancias marginales. Profundidad y tamaño de hoja controlan la varianza de cada árbol en una muestra pequeña. |
| XGBoost | `n_estimators` {150, 300, 500}; `max_depth` {1, 2, 4}; `learning_rate` {0,01; 0,03; 0,1} (27) | entero [150; 500]; entero [1; 6]; log[0,01; 0,1] | Árboles poco profundos (1–6) limitan interacciones de alto orden; `learning_rate` y número de árboles se compensan entre sí, por eso se exploran juntos y en escala log. |
| Decision Tree | `max_depth` {2, 3, 4, 6, 8, None}; `min_samples_leaf` {2, 5, 10, 20}; `ccp_alpha` {0; 0,001; 0,01} (72) | {2, …, None}; entero [2; 30]; [0; 0,01] | Un árbol individual sobreajusta con facilidad: profundidad, hoja mínima y poda por complejidad acotan esa varianza. `ccp_alpha` > 0,01 poda casi todo el árbol en esta escala de error. |

Las grillas de Ridge, Lasso, Random Forest y XGBoost se ampliaron el 14 de octubre alrededor de los óptimos de una primera versión (`historial_grillas_20261014.json`), y el Grid conserva esos puntos para trazabilidad. La comparación **no es a igual presupuesto**: el Grid tiene entre 8 y 72 puntos discretos y los demás métodos exploran dominios continuos con 16–20 evaluaciones.

### Resultados de la búsqueda final

La tabla siguiente muestra el mejor RMSE interno (media de cinco folds internos sobre todo train) que alcanzó cada estrategia; en negrita, el método elegido. Es una métrica **de selección**: está optimizada sobre los mismos folds y es optimista respecto del desempeño externo.

| Modelo | Grid | Random | TPE | DEAP | Halving |
| --- | ---: | ---: | ---: | ---: | ---: |
| SVM lineal | 0,821690 | 0,825022 | **0,821073** | 0,823890 | 0,825022 |
| KNN | 0,848200 | 0,850712 | 0,849469 | **0,848119** | 0,850712 |
| Ridge | 0,824343 | 0,824612 | **0,824343** | 0,824557 | 0,824612 |
| Lasso | 0,827306 | 0,827328 | 0,827245 | **0,827237** | 0,828192 |
| Random Forest | **0,827908** | 0,828914 | 0,828961 | 0,828495 | 0,829165 |
| XGBoost | 0,808483 | 0,808481 | **0,808075** | 0,808085 | 0,808481 |
| Decision Tree | 0,907126 | **0,902634** | 0,902769 | 0,908661 | 0,902634 |

Las diferencias entre estrategias son pequeñas. La siguiente tabla las expresa como brecha respecto de la mejor estrategia de cada modelo, en milésimas de RMSE:

| Modelo | Grid | Random | TPE | DEAP | Halving |
| --- | ---: | ---: | ---: | ---: | ---: |
| SVM lineal | 0,617 | 3,949 | 0,000 | 2,816 | 3,949 |
| KNN | 0,082 | 2,593 | 1,350 | 0,000 | 2,593 |
| Ridge | 0,000 | 0,269 | 0,000 | 0,214 | 0,269 |
| Lasso | 0,069 | 0,091 | 0,009 | 0,000 | 0,956 |
| Random Forest | 0,000 | 1,006 | 1,053 | 0,587 | 1,258 |
| XGBoost | 0,408 | 0,406 | 0,000 | 0,010 | 0,406 |
| Decision Tree | 4,492 | 0,000 | 0,135 | 6,027 | 0,000 |

La mayor brecha es de **6 milésimas** de punto (DEAP en Decision Tree); en los modelos lineales y en XGBoost las estrategias quedan a menos de 4 milésimas. Para comparar, la desviación estándar del RMSE entre los cinco folds internos es de 0,019 a 0,050 (véase `SD interna` en `analisis_clasicos/salidas/hpo_resumen.csv`): **la elección de estrategia mueve el criterio mucho menos que el ruido de la propia partición**. En Ridge, Grid y TPE llegan al mismo `alpha ≈ 10`; en XGBoost cuatro estrategias convergen a `max_depth = 2` con distintas combinaciones de tasa y número de árboles que se compensan entre sí.

Los hiperparámetros finales elegidos, guardados en `seleccion_antes_test.json` antes de inferir sobre test, son:

| Modelo | Método final | Hiperparámetros finales |
| --- | --- | --- |
| SVM lineal | Bayesiana TPE | `C` = 0,2438; `epsilon` = 0,5130 |
| KNN | Genética DEAP | `n_neighbors` = 26; `weights` = distance; `p` = 2 |
| Ridge | Bayesiana TPE | `alpha` = 9,8467 |
| Lasso | Genética DEAP | `alpha` = 0,000668 |
| Random Forest | Grid Search | `n_estimators` = 500; `max_depth` = 6; `min_samples_leaf` = 5 |
| XGBoost | Bayesiana TPE | `n_estimators` = 442; `max_depth` = 2; `learning_rate` = 0,0152 |
| Decision Tree | Random Search | `max_depth` = 8; `min_samples_leaf` = 24; `ccp_alpha` = 0,00128 |

La selección no se fija de antemano. En los cinco folds externos y en el ajuste final (42 búsquedas en total), el método ganador fue TPE 15 veces, Grid 11, Random 9 y DEAP 7:

| Modelo | Fold 1 | Fold 2 | Fold 3 | Fold 4 | Fold 5 | Final |
| --- | --- | --- | --- | --- | --- | --- |
| SVM lineal | Grid | DEAP | Grid | TPE | Random | TPE |
| KNN | DEAP | Grid | Grid | TPE | TPE | DEAP |
| Ridge | DEAP | Grid | Grid | TPE | TPE | TPE |
| Lasso | Random | Random | Random | TPE | TPE | DEAP |
| Random Forest | Grid | Grid | TPE | Random | Grid | Grid |
| XGBoost | Grid | TPE | TPE | DEAP | DEAP | TPE |
| Decision Tree | TPE | Random | TPE | Random | Random | Random |

Como cada fold externo elige su propio método, la evaluación OOF de la sección siguiente mide el **procedimiento completo** (comparar cinco estrategias y quedarse con la mejor), no una configuración fija.

### Presupuesto computacional y tiempos de ejecución

Toda la ejecución activa se instrumentó con `time.perf_counter()` antes de lanzarla (registro central `TIEMPOS_EJECUCION.md`, eventos crudos en `tiempos/20261018_102325_af643f83/`). Hardware: CPU, sin GPU; cada evaluación ajusta sus cinco folds internos en **4 procesos loky con un hilo por proceso**; estrategias, ensayos y modelos se ejecutan secuencialmente. El tiempo de búsqueda incluye preparación, ajuste, scoring, coordinación y registro, y **excluye el refit**, que se mide aparte. La ejecución completa realizó **210 búsquedas**, **22.650 ajustes internos**, 57 refits y 131 inferencias, sin ajustes fallidos, en **3.484,6 s** de pared.

**Número de evaluaciones y ajustes internos** de la búsqueda final (configuraciones evaluadas / ajustes de pipeline; cada configuración a fidelidad completa cuesta cinco ajustes):

| Modelo | Grid | Random | TPE | DEAP | Halving |
| --- | ---: | ---: | ---: | ---: | ---: |
| SVM lineal | 48 / 240 | 16 / 80 | 20 / 100 | 16 / 80 | 28 / 140 |
| KNN | 32 / 160 | 15 / 75 | 20 / 100 | 9 / 45 | 27 / 135 |
| Ridge | 8 / 40 | 16 / 80 | 20 / 100 | 12 / 60 | 28 / 140 |
| Lasso | 9 / 45 | 16 / 80 | 20 / 100 | 12 / 60 | 28 / 140 |
| Random Forest | 27 / 135 | 16 / 80 | 20 / 100 | 13 / 65 | 28 / 140 |
| XGBoost | 27 / 135 | 16 / 80 | 20 / 100 | 11 / 55 | 28 / 140 |
| Decision Tree | 72 / 360 | 16 / 80 | 20 / 100 | 11 / 55 | 28 / 140 |

DEAP evalúa solo las configuraciones **fenotípicamente únicas**: aunque su presupuesto nominal es 8 × 4 = 32 individuos, los duplicados reutilizan el fitness de la caché (9 a 16 evaluaciones reales). Random de KNN evalúa 15 porque un sorteo repitió configuración. Halving evalúa 28 configuraciones, pero 16 al 25 % y 8 al 50 % de los estudiantes: su costo equivale a unas **12 evaluaciones completas** (16 × 0,25 + 8 × 0,5 + 4 × 1).

**Tiempo total de la búsqueda final en todo train** (segundos de pared):

| Modelo | Grid | Random | TPE | DEAP | Halving |
| --- | ---: | ---: | ---: | ---: | ---: |
| SVM lineal | 15,47 | 2,77 | 3,22 | 2,79 | 3,70 |
| KNN | 8,19 | 1,35 | 1,75 | 1,21 | 2,97 |
| Ridge | 6,72 | 1,08 | 1,40 | 0,84 | 1,85 |
| Lasso | 6,18 | 1,26 | 1,96 | 1,16 | 2,01 |
| Random Forest | 34,86 | 21,77 | 24,19 | 16,08 | 24,57 |
| XGBoost | 127,33 | 76,97 | 97,48 | 37,15 | 97,43 |
| Decision Tree | 14,48 | 1,61 | 2,05 | 1,13 | 2,50 |

**Suma de las cinco búsquedas en los folds externos** (segundos de pared; cinco búsquedas secuenciales, sin sumar los ajustes internos paralelos ni la búsqueda final):

| Modelo | Grid | Random | TPE | DEAP | Halving |
| --- | ---: | ---: | ---: | ---: | ---: |
| SVM lineal | 72,76 | 12,79 | 14,53 | 12,87 | 16,88 |
| KNN | 53,28 | 9,58 | 12,51 | 5,65 | 13,81 |
| Ridge | 36,28 | 7,99 | 10,05 | 6,03 | 13,50 |
| Lasso | 30,57 | 6,06 | 8,71 | 4,95 | 9,62 |
| Random Forest | 160,50 | 104,88 | 131,50 | 86,60 | 122,11 |
| XGBoost | 427,26 | 283,99 | 363,07 | 165,92 | 514,33 |
| Decision Tree | 59,56 | 5,77 | 7,54 | 4,77 | 9,96 |

**Tiempo por evaluación individual** (búsqueda final ÷ configuraciones evaluadas, en segundos; cada evaluación ajusta cinco pipelines en paralelo) y **tiempo medio de un ajuste interno** (un solo pipeline, en segundos):

| Modelo | s/evaluación Grid | Random | TPE | DEAP | Halving | Ajuste interno medio (TPE) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SVM lineal | 0,322 | 0,173 | 0,161 | 0,174 | 0,132 | 0,0621 |
| KNN | 0,256 | 0,090 | 0,088 | 0,134 | 0,110 | 0,0219 |
| Ridge | 0,840 | 0,067 | 0,070 | 0,070 | 0,066 | 0,0216 |
| Lasso | 0,687 | 0,079 | 0,098 | 0,097 | 0,072 | 0,0351 |
| Random Forest | 1,291 | 1,361 | 1,209 | 1,237 | 0,877 | 0,6078 |
| XGBoost | 4,716 | 4,810 | 4,874 | 3,378 | 3,480 | 3,1282 |
| Decision Tree | 0,201 | 0,101 | 0,103 | 0,102 | 0,089 | 0,0308 |

El costo por evaluación lo determina el **modelo**, no la estrategia: XGBoost tarda unos 4,8 s por evaluación (≈ 3 s por ajuste, con categorías nativas y hasta 500 árboles), Random Forest ≈ 1,3 s y los lineales menos de 0,2 s. El tiempo por evaluación del Grid en Ridge y Lasso (0,7–0,8 s) está inflado por el arranque del grupo de procesos al inicio de cada búsqueda, que se reparte entre solo 8–9 configuraciones. Halving tiene el menor costo por evaluación porque dos de sus tres rondas usan menos estudiantes.

Agregando los siete modelos (búsqueda final + cinco búsquedas externas), el consumo total por estrategia fue:

| Estrategia | Ajustes internos (final) | Evaluaciones (final) | Costo equivalente completo | Tiempo final (s) | Tiempo 5 externas (s) | Total (s) | Veces elegida (de 42) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Grid Search | 1.115 | 223 | 223,0 | 213,24 | 840,21 | 1.053,45 | 11 |
| Random Search | 555 | 111 | 111,0 | 106,80 | 431,07 | 537,88 | 9 |
| Bayesiana TPE | 700 | 140 | 140,0 | 132,06 | 547,91 | 679,97 | 15 |
| Genética DEAP | 420 | 84 | 84,0 | 60,36 | 286,80 | 347,15 | 7 |
| Successive Halving | 975 | 195 | 83,8 | 135,02 | 700,22 | 835,24 | 0 |

```{figure} images/clasicos/hpo_tiempos.png
:alt: Barras en escala logarítmica del tiempo de la búsqueda final por modelo y estrategia.
:name: clasicos-hpo-tiempos

Tiempo de pared de la búsqueda final por modelo y estrategia (escala logarítmica).
```

La lectura de costo-beneficio es clara: **TPE es la estrategia elegida con más frecuencia y consume un 35 % menos de tiempo que el Grid**; DEAP es la más barata (un tercio del Grid) y queda a menos de una milésima del mejor en cinco de los siete modelos finales. Halving no ahorra tiempo de pared en este conjunto pequeño: hace más ajustes y la coordinación de rondas pesa tanto como el ahorro de filas; además, en XGBoost sus cinco búsquedas externas fueron las más lentas (514 s). Estas cifras dependen de la CPU, del paralelismo y del tamaño de la muestra, y no se usaron para elegir hiperparámetros.

### Convergencia: desempeño en cualquier momento

Una búsqueda se evalúa no solo por su resultado final sino por **cuán rápido llega a él**. La curva de desempeño en cualquier momento (*anytime performance*) grafica, para cada evaluación *t*, el mejor RMSE interno encontrado hasta *t*. Se calcula directamente de los registros de ensayos (`trials_<modelo>_<búsqueda>.jsonl`), en el orden en que se evaluaron:

```python
best, cost = np.inf, 0.
for t, trial in enumerate(trials_of_method, 1):
    cost += trial['fidelity']                       # Halving: 0,25 o 0,5 por evaluación parcial
    if trial['fidelity'] == 1 and trial['RMSE'] is not None:
        best = min(best, trial['RMSE'])             # solo fidelidad completa es comparable
    anytime.append({'t': t, 'costo_equivalente': cost, 'mejor_hasta_t': best})
```

Para que Halving sea comparable, el eje horizontal usa **evaluaciones completas equivalentes**: una evaluación al 25 % de los estudiantes cuenta 0,25. Las evaluaciones a fidelidad parcial no entran en la curva porque su RMSE no es comparable con el de fidelidad completa.

```{figure} images/clasicos/hpo_anytime_evaluaciones.png
:alt: Siete paneles con curvas escalonadas del mejor RMSE interno frente al número de evaluaciones equivalentes para cinco estrategias.
:name: clasicos-hpo-anytime

Mejor RMSE interno hasta la evaluación *t* en la búsqueda final, por modelo y estrategia. El punto marca el final de cada estrategia.
```

```{figure} images/clasicos/hpo_anytime_tiempo.png
:alt: Siete paneles con el mejor RMSE interno frente a los segundos de pared acumulados en escala logarítmica.
:name: clasicos-hpo-anytime-tiempo

La misma curva en función del tiempo de pared acumulado (escala logarítmica).
```

Tres patrones se repiten. Primero, **TPE y DEAP alcanzan casi todo su progreso en las primeras 5 evaluaciones** y después mejoran poco: en XGBoost, TPE llega a 0,8081 en la quinta evaluación y DEAP en la sexta, mientras el Grid necesita catorce para llegar a 0,8085. Segundo, el Grid tiene curvas escalonadas que dependen del **orden** de la grilla (empieza por los valores más pequeños de cada parámetro), por lo que su desempeño en cualquier momento es pobre aunque su valor final sea competitivo. Tercero, Random es eficaz al principio pero se estanca, como corresponde a un muestreo que no aprende de los intentos previos.

Para separar la convergencia de la variabilidad de cada búsqueda, la figura siguiente repite las curvas de TPE y DEAP en las seis búsquedas de cada modelo (cinco externas en trazo fino y la final en grueso), medidas como diferencia respecto del mejor punto del Grid **de la misma búsqueda**. Un valor por debajo de cero indica que la estrategia superó a toda la grilla.

```{figure} images/clasicos/hpo_convergencia_tpe_deap.png
:alt: Curvas de TPE y DEAP relativas al mejor Grid en las seis búsquedas de cada modelo.
:name: clasicos-hpo-convergencia

Convergencia de TPE (verde) y DEAP (amarillo) relativa al mejor punto del Grid; trazo fino = folds externos, grueso = búsqueda final.
```

TPE alcanza el nivel del Grid (brecha ≈ 0) en casi todas las búsquedas en menos de 10 evaluaciones y lo supera en XGBoost, SVM y Decision Tree, donde los dominios continuos permiten valores intermedios que la grilla no contiene (por ejemplo, `learning_rate = 0,0152` o `min_samples_leaf = 24`). DEAP converge aún más rápido en número de evaluaciones, pero se detiene antes: en Random Forest y Decision Tree varias de sus curvas quedan por encima del Grid.

La explicación de esa detención está en la diversidad de la población. Para cada generación se registran el mejor fitness, el fitness medio, la fracción de configuraciones distintas y la entropía media normalizada de los genes:

```{figure} images/clasicos/hpo_deap_generaciones.png
:alt: Para cada modelo, mejor RMSE y RMSE medio por generación de DEAP, y fracción única y entropía genética.
:name: clasicos-hpo-deap

DEAP en la búsqueda final: mejor RMSE y media de la población (arriba); diversidad fenotípica y entropía genética (abajo).
```

En los siete modelos **el mejor individuo ya está en la generación 0** y no mejora después; la media de la población sí desciende, lo que muestra que la selección concentra la población alrededor del élite. La fracción de configuraciones únicas cae de 0,88–1,00 a 0,13–0,38 y la entropía genética llega a 0 en KNN y Random Forest. La combinación de **estancamiento del mejor fitness y pérdida de diversidad** es la señal clásica de **convergencia prematura**: con 8 individuos y 3 generaciones, el presupuesto deliberadamente exploratorio no basta para escapar del primer buen candidato. Esto no invalida el resultado —en Lasso y KNN DEAP fue el mejor método final— pero indica que su ventaja proviene más de un buen muestreo inicial que de la evolución. Ni 20 ensayos de TPE ni 4 generaciones de DEAP demuestran convergencia a un óptimo global.

Las dos secciones anteriores describieron cómo se eligieron los hiperparámetros. La siguiente evalúa los modelos resultantes.

## Evaluación de modelos

Esta sección presenta, para cada uno de los siete regresores, el error en entrenamiento, validación externa y prueba; los diagnósticos de residuos; la interpretabilidad global y local con SHAP; y la robustez de las métricas. Los tres conjuntos tienen significados distintos:

- **Entrenamiento:** predicciones del modelo final sobre las mismas 1.309 filas con que se ajustó (in-sample). Mide capacidad de ajuste, no generalización.
- **Validación (OOF):** predicciones de los cinco modelos externos sobre sus folds reservados; cada registro se predice sin que su estudiante haya participado en el ajuste ni en la búsqueda. Se reporta la media ± desviación estándar de los cinco folds y la métrica OOF reunida.
- **Prueba (test 202530):** 188 registros de un periodo posterior, predichos solo por el modelo final.

### RMSE y MAE por conjunto

Las desviaciones estándar entre folds de este capítulo son muestrales (ddof = 1); el dashboard muestra la SD poblacional (ddof = 0), por eso sus cifras son algo menores.

| Modelo | RMSE train | RMSE CV (media ± SD) | RMSE OOF reunido | RMSE test | MAE train | MAE CV (media ± SD) | MAE test | R² CV | R² test |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| XGBoost | 0,7404 | 0,8156 ± 0,0344 | 0,8162 | 0,9137 | 0,5869 | 0,6447 ± 0,0264 | 0,7391 | 0,4646 | 0,4457 |
| SVM lineal | 0,7962 | 0,8241 ± 0,0479 | 0,8252 | 0,9299 | 0,6259 | 0,6503 ± 0,0408 | 0,7581 | 0,4530 | 0,4258 |
| Ridge | 0,7965 | 0,8253 ± 0,0520 | 0,8266 | 0,9170 | 0,6281 | 0,6514 ± 0,0399 | 0,7544 | 0,4514 | 0,4416 |
| Lasso | 0,7937 | 0,8288 ± 0,0561 | 0,8303 | 0,9197 | 0,6259 | 0,6542 ± 0,0439 | 0,7548 | 0,4465 | 0,4383 |
| Random Forest | 0,6842 | 0,8297 ± 0,0294 | 0,8301 | 0,9396 | 0,5475 | 0,6619 ± 0,0291 | 0,7658 | 0,4457 | 0,4138 |
| KNN | 0,0000 | 0,8550 ± 0,0400 | 0,8558 | 0,9239 | 0,0000 | 0,6809 ± 0,0308 | 0,7517 | 0,4121 | 0,4332 |
| Decision Tree | 0,7730 | 0,8948 ± 0,0325 | 0,8953 | 1,0104 | 0,6133 | 0,7123 ± 0,0335 | 0,8262 | 0,3552 | 0,3221 |

```{figure} images/clasicos/eval_resumen_rmse_mae.png
:alt: Barras horizontales de RMSE y MAE por modelo en entrenamiento, validación y prueba, con barras de error en validación.
:name: clasicos-eval-resumen

RMSE y MAE por modelo y conjunto. En validación, la barra de error es ± 1 desviación estándar entre los cinco folds externos.
```

El patrón es común a los siete modelos: **el error crece de entrenamiento a validación y de validación a prueba**. La primera brecha mide sobreajuste; la segunda, el cambio de periodo. Los lineales tienen una brecha de entrenamiento a validación de unas 3 centésimas de RMSE, mínima porque su capacidad es baja. Random Forest tiene la mayor brecha entre los modelos con error de entrenamiento informativo (0,684 → 0,830): sus árboles de profundidad 6 memorizan parte del ruido, aunque el promedio del bosque contiene el sobreajuste en validación. **KNN muestra RMSE = 0 en entrenamiento**: con `weights = distance` cada registro es su propio vecino a distancia cero y recibe peso infinito, así que reproduce exactamente su nota; esa cifra no es un ajuste perfecto sino un artefacto del método. XGBoost ofrece el mejor equilibrio: menor error en validación (0,8156 ± 0,0344) y en prueba (0,9137) con una brecha moderada.

En prueba, todos los modelos pierden entre 0,08 y 0,12 puntos de RMSE respecto de la validación. Ese deterioro es común y no reordena drásticamente el ranking —XGBoost sigue primero y Decision Tree último—, aunque Ridge, Lasso y KNN superan al SVM en el test mientras quedan por detrás en validación. Como se discute en la sección estadística, esas diferencias son menores que la variabilidad de las métricas.

### Ajuste visual en entrenamiento, validación y prueba

Cada figura muestra, en la fila superior, la nota predicha frente a la real para los tres conjuntos (la diagonal discontinua es la predicción perfecta) y, en la inferior, los residuos (real − predicha) frente a la predicción con la **media del residuo por decil de la predicción**, que permite detectar sesgos sistemáticos.

```{figure} images/clasicos/eval_xgboost.png
:alt: XGBoost: predicción frente a nota real y residuos frente a predicción en entrenamiento, validación OOF y test.
:name: clasicos-eval-xgboost

XGBoost: ajuste en entrenamiento, validación externa (OOF) y prueba.
```

La media por decil del residuo es casi plana en validación: XGBoost no deja un sesgo sistemático por nivel de predicción, aunque la dispersión es mayor en predicciones bajas.

```{figure} images/clasicos/eval_svm.png
:alt: SVM lineal: predicción frente a nota real y residuos frente a predicción en entrenamiento, validación OOF y test.
:name: clasicos-eval-svm

SVM lineal: ajuste en entrenamiento, validación externa (OOF) y prueba.
```

El SVM lineal produce algunas predicciones fuera de la escala 0–5 en validación (39 de 1.309) porque no acota su salida; la media por decil muestra una ligera subestimación en predicciones altas.

```{figure} images/clasicos/eval_ridge.png
:alt: Ridge: predicción frente a nota real y residuos frente a predicción en entrenamiento, validación OOF y test.
:name: clasicos-eval-ridge

Ridge: ajuste en entrenamiento, validación externa (OOF) y prueba.
```

Ridge reproduce casi exactamente el patrón del SVM: ambos son lineales en el mismo espacio transformado y sus coeficientes encogidos son muy parecidos.

```{figure} images/clasicos/eval_lasso.png
:alt: Lasso: predicción frente a nota real y residuos frente a predicción en entrenamiento, validación OOF y test.
:name: clasicos-eval-lasso

Lasso: ajuste en entrenamiento, validación externa (OOF) y prueba.
```

Lasso es visualmente indistinguible de Ridge; la penalización L1 anula pocos coeficientes con `alpha` = 0,00067.

```{figure} images/clasicos/eval_forest.png
:alt: Random Forest: predicción frente a nota real y residuos frente a predicción en entrenamiento, validación OOF y test.
:name: clasicos-eval-forest

Random Forest: ajuste en entrenamiento, validación externa (OOF) y prueba.
```

Random Forest comprime el rango de predicción (≈ 1,6–4,9 en validación) más que los lineales: el promedio de 500 árboles suaviza los extremos y acentúa la regresión hacia la media.

```{figure} images/clasicos/eval_knn.png
:alt: KNN: predicción frente a nota real y residuos frente a predicción en entrenamiento, validación OOF y test.
:name: clasicos-eval-knn

KNN: ajuste en entrenamiento, validación externa (OOF) y prueba.
```

En entrenamiento KNN coincide exactamente con la diagonal porque con `weights = distance` cada registro es su propio vecino; en validación y prueba muestra la nube más ancha entre los modelos competitivos.

```{figure} images/clasicos/eval_decision_tree.png
:alt: Decision Tree: predicción frente a nota real y residuos frente a predicción en entrenamiento, validación OOF y test.
:name: clasicos-eval-decision-tree

Decision Tree: ajuste en entrenamiento, validación externa (OOF) y prueba.
```

Las predicciones del árbol se agrupan en columnas verticales: cada hoja asigna la misma nota a todos sus registros, lo que produce residuos escalonados y el mayor error de los siete modelos.


### Estadísticos y diagnósticos de residuos: White y BDS

Los residuos se diagnostican en validación (OOF reunida, 1.309 filas) y en prueba (188 filas) con la misma función del dashboard (`Dash/residual_diagnostics.py`):

- **Test de White** (homocedasticidad): regresión auxiliar de los residuos al cuadrado sobre las predictoras numéricas, sus cuadrados e interacciones (35 grados de libertad tras retirar la dependencia exacta avance = dominio final − inicial). H₀: varianza constante.
- **Test BDS** (independencia): con dimensión de inclusión 2 y ε = 1,5 desviaciones estándar, contrasta si los residuos son IID **en el orden del archivo**. H₀: residuos independientes e idénticamente distribuidos.
- Complementos: normalidad de D'Agostino, Breusch–Pagan frente a la predicción y correlación de Spearman entre |residuo| y predicción.

```python
def residual_diagnostics(frame, target, prediction, numeric):
    residuals = frame[target] - frame[prediction]
    z = estandarizar(frame[numeric]); z = retirar_columnas_dependientes(z)   # QR con pivoteo
    exog = np.column_stack([np.ones(len(z)), z])
    lm, white_p, _, _ = het_white(residuals, exog)                        # cuadrados e interacciones
    statistic, bds_p = bds(residuals, max_dim=2, epsilon=1.5 * np.std(residuals, ddof=1))
    return {'white_p': white_p, 'bds_p': bds_p, ...}
```

| Modelo | Conjunto | n | RMSE | MAE | Residuo medio | p White | p BDS | p normalidad | p Breusch–Pagan | Spearman \|e\| vs ŷ | Asimetría |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| XGBoost | Validación OOF | 1309 | 0,8162 | 0,6447 | 0,001 | 3,79×10⁻⁶ | 0,0331 | 0,0005 | 1,94×10⁻⁵ | −0,168 | −0,246 |
| XGBoost | Test 202530 | 188 | 0,9137 | 0,7391 | 0,118 | 0,6695 | 0,6009 | 0,0008 | 0,0008 | −0,302 | −0,683 |
| SVM lineal | Validación OOF | 1309 | 0,8252 | 0,6503 | 0,009 | 4,99×10⁻¹⁹ | 0,0030 | 0,0045 | 6,43×10⁻⁸ | −0,196 | −0,151 |
| SVM lineal | Test 202530 | 188 | 0,9299 | 0,7581 | 0,107 | 0,8178 | 0,5275 | 0,0092 | 0,0002 | −0,359 | −0,553 |
| Ridge | Validación OOF | 1309 | 0,8266 | 0,6514 | 0,005 | 1,80×10⁻³⁵ | 0,0012 | 0,0014 | 1,33×10⁻⁹ | −0,195 | −0,141 |
| Ridge | Test 202530 | 188 | 0,9170 | 0,7544 | 0,115 | 0,8958 | 0,5700 | 0,0029 | 0,0003 | −0,332 | −0,630 |
| Lasso | Validación OOF | 1309 | 0,8303 | 0,6542 | 0,004 | 1,30×10⁻³⁶ | 0,0018 | 0,0022 | 1,79×10⁻⁹ | −0,194 | −0,131 |
| Lasso | Test 202530 | 188 | 0,9197 | 0,7548 | 0,111 | 0,8844 | 0,6865 | 0,0040 | 0,0003 | −0,345 | −0,609 |
| Random Forest | Validación OOF | 1309 | 0,8301 | 0,6619 | 0,003 | 1,18×10⁻⁷ | 0,0022 | 0,0010 | 1,01×10⁻⁶ | −0,185 | −0,253 |
| Random Forest | Test 202530 | 188 | 0,9396 | 0,7658 | 0,173 | 0,5998 | 0,3166 | 0,0006 | 0,0002 | −0,306 | −0,708 |
| KNN | Validación OOF | 1309 | 0,8558 | 0,6809 | −0,004 | 1,67×10⁻⁶ | 0,0041 | 4,23×10⁻⁵ | 0,0004 | −0,160 | −0,299 |
| KNN | Test 202530 | 188 | 0,9239 | 0,7517 | 0,145 | 0,7069 | 0,6042 | 0,0007 | 9,30×10⁻⁵ | −0,297 | −0,710 |
| Decision Tree | Validación OOF | 1309 | 0,8953 | 0,7123 | −0,009 | 3,78×10⁻⁶ | 2,37×10⁻⁶ | 0,0054 | 0,0001 | −0,172 | −0,218 |
| Decision Tree | Test 202530 | 188 | 1,0104 | 0,8262 | 0,216 | 0,1720 | 0,3921 | 0,0035 | 0,0002 | −0,328 | −0,621 |

**Homocedasticidad.** En validación, White rechaza la varianza constante en los siete modelos (p < 10⁻⁴) y Breusch–Pagan lo confirma también en prueba. La correlación negativa entre |residuo| y predicción (−0,16 a −0,36) indica que el error es mayor cuando el modelo predice notas bajas. En prueba White no rechaza (p entre 0,17 y 0,90), pero con 188 filas y 35 grados de libertad la regresión auxiliar tiene poca potencia: no rechazar no demuestra homocedasticidad, y Breusch–Pagan, con un solo regresor, sí detecta la heterocedasticidad ligada a la predicción.

**Independencia.** BDS rechaza IID en validación para los siete modelos (p entre 2×10⁻⁶ y 0,033) y no rechaza en prueba. En validación los registros conservan el orden del archivo, agrupado por periodo y programa, y la OOF reúne cinco modelos distintos; la dependencia detectada refleja estructura por grupo que las predictoras no capturan, no autocorrelación temporal en sentido estricto. Decision Tree muestra el BDS más extremo (estadístico 4,72), coherente con predicciones escalonadas por hoja que dejan residuos agrupados.

**Normalidad y forma.** La normalidad se rechaza en todos los casos. La asimetría es negativa (−0,13 a −0,71): hay una cola de residuos muy negativos, estudiantes con nota real baja a quienes el modelo asigna una nota alta. El residuo medio en prueba es positivo (0,11 a 0,22): en 202530 todos los modelos **subestiman** en promedio, una señal de cambio de nivel entre periodos.

### Patrones en los residuos

Las figuras de ajuste muestran tres patrones que indican especificación incompleta, comunes a todas las familias:

1. **Regresión hacia la media.** Las nubes de predicción frente a realidad son más planas que la diagonal: las notas bajas se sobreestiman y las altas se subestiman. En el test ninguna predicción baja de 1,5 aunque hay notas reales de 1,0.
2. **Bandas diagonales en los residuos.** Las líneas paralelas descendentes de la fila inferior corresponden a notas reales discretas (1,0; 2,0; …; 5,0): para una nota fija, residuo = nota − predicción es una recta de pendiente −1. La banda superior marcada es el techo de la escala (nota 5): un modelo que predice 4,5 a un estudiante con 5 no puede tener un residuo mayor que 0,5. La escala acotada y discreta genera heterocedasticidad por construcción.
3. **Varianza decreciente con la predicción.** La dispersión es mayor a la izquierda (predicciones bajas). Los estudiantes con predicción baja son un grupo heterogéneo, mientras los de predicción alta se concentran cerca del techo.

Estos patrones son de la **variable objetivo y la información disponible**, no de una familia concreta: aparecen igual en modelos lineales, KNN y ensambles. Un modelo más flexible reduce el error medio pero no corrige la forma. Las alternativas para el trabajo futuro son modelar la nota como variable acotada (regresión beta u ordinal), estimar la varianza condicional o incorporar predictoras de los grupos con mayor error.

### Interpretabilidad global y local con SHAP

Los valores de Shapley reparten la diferencia entre la predicción de un caso y una predicción de referencia (la base) entre las variables, de forma que **base + suma de aportes = predicción** (propiedad de eficiencia). Para la variable *j*:

$$
\phi_j = \sum_{S \subseteq F \setminus \{j\}} \frac{|S|!\,(p-|S|-1)!}{p!}\,\big[v(S \cup \{j\}) - v(S)\big]
$$

donde *F* son las 15 variables originales, *p* = 15 y *v(S)* es la predicción esperada cuando solo se conocen las variables de *S*. Las explicaciones se calculan sobre las **15 variables originales** (no sobre las 67 columnas one-hot) y sobre las **188 filas del test temporal**, con el pipeline final guardado y sin reentrenar. El método depende de la familia:

| Modelo | Explicador | Exactitud | Referencia *v(S)* |
| --- | --- | --- | --- |
| SVM, Ridge, Lasso | Fórmula lineal: φⱼ = Σ βₖ (zₖ − z̄ₖ) sobre las columnas de la variable *j* | **Exacta** (el modelo es aditivo en las variables originales) | Intervencional, 50 filas de train |
| XGBoost | TreeSHAP nativo (`pred_contribs=True`, `approx_contribs=False`) | **Exacta** para el juego tree-path-dependent | Cobertura de los árboles aprendida en train |
| KNN, Random Forest, Decision Tree | Muestreo de 16 permutaciones antitéticas | **Aproximada** (Monte Carlo), eficiencia exacta por construcción | Intervencional, 50 filas de train |

El estimador por permutaciones recorre cada permutación de las variables, incorpora una a una las del caso sobre las filas de referencia y atribuye a cada variable el cambio de la predicción media:

```python
for order in permutaciones_antitéticas(rng, p=15, m=16):
    coaliciones = [order[:k] for k in range(16)]            # ∅, {j1}, {j1, j2}, …, F
    filas = mezclar(caso, fondo, coaliciones)                # 16 × 50 filas sintéticas
    v = model.predict(filas).reshape(16, 50).mean(axis=1)    # predicción media por coalición
    phi[order] += np.diff(v)                                 # aporte marginal de cada variable
phi /= 16                                                    # base = v[0], suma = f(x) − base
```

En los siete modelos se verificó que base + Σφ reproduce la predicción del pipeline (brecha máxima 2 × 10⁻¹⁵ en los exactos y por permutaciones; 6 × 10⁻⁶ en XGBoost por aritmética float32). El error Monte Carlo medio del estimador por permutaciones es 0,013 puntos en KNN, 0,009 en Decision Tree y 0,002 en Random Forest. Como control, el mismo estimador aplicado a Ridge reproduce la solución exacta lineal (correlación 1,0000) y aplicado a XGBoost se compara con TreeSHAP:

```{figure} images/clasicos/shap_validacion_estimador.png
:alt: Dispersión de SHAP exacto frente a SHAP por permutaciones para Ridge y XGBoost.
:name: clasicos-shap-validacion

Control del estimador por permutaciones: coincide con la solución exacta en Ridge; en XGBoost difiere ligeramente de TreeSHAP porque ambos usan referencias distintas.
```

En XGBoost la correlación es 0,995 y la diferencia media 0,008 puntos: no es error numérico sino **dos definiciones distintas de *v(S)***. TreeSHAP path-dependent usa la cobertura de los árboles (una aproximación a la distribución condicional), mientras el estimador intervencional reemplaza variables con filas de referencia independientes. El orden de importancia coincide salvo un intercambio entre Programa y Dominio inicial.

#### Interpretabilidad global

```{figure} images/clasicos/shap_importancia_modelos.png
:alt: Mapa de calor con el porcentaje de importancia SHAP de cada variable por modelo.
:name: clasicos-shap-importancia

Importancia relativa: media |SHAP| de cada variable como porcentaje del total de cada modelo, en el test temporal.
```

**Saber 11 · global es la variable más importante en los siete modelos** (14 % a 28 % de la atribución total). Más allá de ese acuerdo, las familias usan la información de forma distinta:

- Los **árboles** (XGBoost, Random Forest, Decision Tree) concentran la atribución en Saber 11 global, **Dominio inicial** (16–20 %) y la asignatura o el programa; casi no usan las categorías de temas.
- Los **lineales** reparten la señal en más variables y dan peso a las **categorías de temas finales**, la **división académica**, el **tiempo de trabajo** y, en el SVM, al **cumplimiento de la meta** (11,4 %), que XGBoost y Lasso no usan en absoluto.
- **Lasso** anula Dominio inicial y Cumplimiento de la meta (0 %) y traslada su señal a Dominio final (12 %): con dominios inicial, final y avance linealmente dependientes, la penalización L1 conserva una sola representación.
- **XGBoost atribuye 0 % a la asignatura** pero 16 % al programa, mientras Random Forest y Decision Tree hacen lo contrario: ambas variables están anidadas (cada programa cursa una asignatura) y los árboles eligen una u otra para el mismo corte.

Estas diferencias son una advertencia: **la importancia SHAP describe el modelo, no el fenómeno**. Cuando las variables son redundantes, cada familia elige una representación distinta con un error casi igual.

#### Resumen y casos locales por modelo

Para cada modelo, la figura combina el **gráfico resumen** (cada punto es un registro del test; a la derecha eleva la predicción y a la izquierda la reduce; el color indica valor numérico bajo en azul o alto en rojo, y gris para categóricas) con dos explicaciones **tipo waterfall**: el registro del test con **menor error absoluto** de ese modelo y el de **mayor error absoluto**. Las barras parten de la base (línea punteada) y acumulan los aportes hasta la predicción (línea continua); la línea violeta discontinua marca la nota real. En regresión no existe una "clasificación correcta": se usa el menor error absoluto como caso bien predicho.

```{figure} images/clasicos/shap_xgboost.png
:alt: XGBoost: gráfico resumen SHAP en el test y waterfalls de los casos con menor y mayor error absoluto.
:name: clasicos-shap-xgboost

XGBoost: resumen SHAP (arriba) y waterfalls de los casos con menor y mayor error absoluto (abajo).
```

XGBoost (TreeSHAP exacto) concentra la atribución en Saber 11 global, Dominio inicial y Programa, con una relación monótona clara: valores altos de Saber 11 (rojo) elevan la predicción y bajos (azul) la reducen. Asignatura y Cumplimiento de la meta tienen SHAP idénticamente cero.

```{figure} images/clasicos/shap_svm.png
:alt: SVM lineal: gráfico resumen SHAP en el test y waterfalls de los casos con menor y mayor error absoluto.
:name: clasicos-shap-svm

SVM lineal: resumen SHAP (arriba) y waterfalls de los casos con menor y mayor error absoluto (abajo).
```

En el SVM, cada variable numérica dibuja una franja ordenada por color porque su aporte es lineal en la variable transformada. Las categóricas forman grupos discretos: Categoría de temas finales y Cumplimiento de la meta aportan entre 0,3 y 0,45 puntos en valor absoluto en los casos locales.

```{figure} images/clasicos/shap_ridge.png
:alt: Ridge: gráfico resumen SHAP en el test y waterfalls de los casos con menor y mayor error absoluto.
:name: clasicos-shap-ridge

Ridge: resumen SHAP (arriba) y waterfalls de los casos con menor y mayor error absoluto (abajo).
```

Ridge reparte la señal de forma más pareja que el SVM: Saber 11 global domina y División académica, Tiempo de trabajo y Categoría de temas finales le siguen. El aporte negativo de Saber 11 matemáticas, pese a su correlación positiva con la nota, refleja la redundancia con el puntaje global.

```{figure} images/clasicos/shap_lasso.png
:alt: Lasso: gráfico resumen SHAP en el test y waterfalls de los casos con menor y mayor error absoluto.
:name: clasicos-shap-lasso

Lasso: resumen SHAP (arriba) y waterfalls de los casos con menor y mayor error absoluto (abajo).
```

Lasso muestra un patrón casi igual al de Ridge, salvo que Dominio inicial y Cumplimiento de la meta tienen aporte nulo: la penalización L1 eliminó esas columnas y su señal pasa a Dominio final.

```{figure} images/clasicos/shap_forest.png
:alt: Random Forest: gráfico resumen SHAP en el test y waterfalls de los casos con menor y mayor error absoluto.
:name: clasicos-shap-forest

Random Forest: resumen SHAP (arriba) y waterfalls de los casos con menor y mayor error absoluto (abajo).
```

Random Forest (permutaciones) atribuye importancia similar a Saber 11 global, Dominio inicial y Asignatura. Sus aportes son más pequeños que los de los lineales porque el promedio de árboles comprime las predicciones.

```{figure} images/clasicos/shap_knn.png
:alt: KNN: gráfico resumen SHAP en el test y waterfalls de los casos con menor y mayor error absoluto.
:name: clasicos-shap-knn

KNN: resumen SHAP (arriba) y waterfalls de los casos con menor y mayor error absoluto (abajo).
```

En KNN los aportes son más dispersos y menos ordenados por color: la predicción depende de la vecindad completa y no de una función suave de cada variable, y el error Monte Carlo (≈ 0,013 puntos) es el mayor de los tres modelos por permutaciones.

```{figure} images/clasicos/shap_decision_tree.png
:alt: Decision Tree: gráfico resumen SHAP en el test y waterfalls de los casos con menor y mayor error absoluto.
:name: clasicos-shap-decision-tree

Decision Tree: resumen SHAP (arriba) y waterfalls de los casos con menor y mayor error absoluto (abajo).
```

En el Decision Tree pocas variables reciben casi toda la atribución (Saber 11 global, Dominio inicial y Asignatura); las que el árbol no usa en sus cortes tienen aporte nulo.


**Caso con error elevado.** El registro 118 del test tiene **el mayor error absoluto en seis de los siete modelos**: nota real 1,0 y predicciones entre 3,83 (KNN) y 4,14 (XGBoost). Todos los modelos lo explican del mismo modo: Saber 11 global = 407, muy por encima de la media, aporta entre +0,27 (KNN) y +0,65 puntos (SVM); en los árboles se suma un dominio inicial bajo (4 temas) que el modelo asocia con margen de avance; los aportes negativos —programa Ingeniería de Sistemas, tiempo de trabajo alto— son pequeños. El modelo no se equivoca por una variable mal leída: el perfil del estudiante es el de alguien con nota alta, y nada en las 15 variables anticipa su resultado. SHAP describe **cómo se construye** la predicción, no por qué el estudiante obtuvo 1,0; ese error es irreducible con la información disponible. El Decision Tree es la excepción: su mayor error es el registro 158 (real 1,0; predicha 3,57), con aportes positivos de dominio inicial bajo y avance alto.

**Caso bien predicho.** Los casos de menor error varían por modelo (registros 7, 39, 88, 124 y 137) y casi siempre combinan aportes que se compensan. En XGBoost (registro 124: real 3,70, predicha 3,68), Dominio inicial = 13 suma +0,25 y Programa = Ingeniería Civil resta −0,14. En KNN y Decision Tree (registro 39), un Saber 11 global bajo (234) y pocos temas por hora llevan la predicción por debajo de la base, en la dirección correcta. Que un caso tenga error pequeño no valida el modelo: puede ser coincidencia de aportes opuestos.

**Diferencias entre ambos casos.** Comparando los waterfalls de XGBoost, la mayor diferencia de aporte entre el caso de mayor y menor error es Saber 11 global (+0,575 puntos), seguida de tiempo de trabajo (−0,06) y dominio inicial (−0,06). El caso de error alto se distingue por una variable con aporte muy grande que el resultado real contradice.

#### Comparación con LIME

LIME y SHAP responden preguntas distintas. **LIME** genera un vecindario alrededor del caso, obtiene las predicciones del modelo y ajusta una **regresión lineal ponderada** por cercanía; sus pesos explican ese sustituto local, no el modelo. **SHAP** reparte exactamente la predicción del modelo entre las variables según los axiomas de Shapley (eficiencia, simetría, nulidad y aditividad). Para contrastarlos se ejecutó el LIME del dashboard (`Dash/lime_xgboost.py`: vecindario empírico de 1.000 filas de train, discretización por cuartiles, semilla 42) sobre los mismos dos casos de XGBoost:

**Caso 124 · menor error absoluto.** Predicción XGBoost 3,680; sustituto LIME 4,180; fidelidad R² 0,591.

| Variable | Condición LIME | Peso LIME | SHAP (TreeSHAP) |
| --- | --- | ---: | ---: |
| Cumplimiento de la meta | Cumplimiento de la meta = Cumplimiento meta | 1,124 | 0,000 |
| Dominio inicial | Dominio inicial > 10.00 | 0,485 | 0,252 |
| Cat. temas finales | Cat. temas finales = 3 Temas Parcial 1 Cálculo I | −0,480 | 0,060 |
| Asignatura | Asignatura = MAT1101 | −0,298 | 0,000 |
| Tiempo de pretest | 0.53 < Tiempo de pretest <= 0.93 | 0,191 | 0,030 |
| Saber 11 · global | 345.00 < Saber 11 · global <= 370.00 | 0,183 | −0,006 |

**Caso 118 · mayor error absoluto.** Predicción XGBoost 4,139; sustituto LIME 4,296; fidelidad R² 0,673.

| Variable | Condición LIME | Peso LIME | SHAP (TreeSHAP) |
| --- | --- | ---: | ---: |
| Cumplimiento de la meta | Cumplimiento de la meta = Cumplimiento meta | 1,052 | 0,000 |
| Saber 11 · global | Saber 11 · global > 370.00 | 0,756 | 0,569 |
| Asignatura | Asignatura = MAT1101 | −0,498 | 0,000 |
| Cat. temas finales | Cat. temas finales = 3 Temas Parcial 1 Cálculo I | −0,360 | 0,048 |
| Dominio inicial | 2.00 < Dominio inicial <= 10.00 | 0,236 | 0,194 |
| Cat. temas iniciales | Cat. temas iniciales = 1 Repaso de álgebra y geometría | 0,136 | 0,027 |

Las diferencias son de método, no de cálculo:

- **Cumplimiento de la meta** es el mayor peso LIME en ambos casos (+1,12 y +1,05) y su SHAP es **exactamente 0**: XGBoost no usa esa variable en ningún corte. LIME la destaca porque, en el vecindario de filas reales, "cumplir la meta" está correlacionado con dominios y avance altos; la regresión local atribuye a la variable binaria una señal que el modelo obtiene de otras. SHAP, por la propiedad de nulidad, asigna cero a una variable que el modelo no consulta.
- El sustituto LIME **no reproduce la predicción**: 4,18 frente a 3,68 en el caso 124 y 4,30 frente a 4,14 en el 118, con fidelidad R² de 0,59 y 0,67. Sus pesos más el intercepto suman el sustituto, no la predicción; SHAP suma exactamente la predicción.
- LIME discretiza numéricas por cuartiles: "Saber 11 global > 370" explica el caso 118 con un peso de +0,76, cercano al +0,57 de SHAP, pero la condición agrupa a todos los estudiantes del cuartil superior y pierde la magnitud del valor 407.

**Cuándo divergen.** Las técnicas tienden a coincidir en modelos aproximadamente lineales y variables poco correlacionadas. Divergen cuando (1) el modelo tiene saltos o interacciones —árboles y ensambles—, que una recta local no captura; (2) las variables son redundantes o derivadas —dominio inicial, final y avance; programa, división y asignatura—, porque el vecindario LIME y la referencia SHAP reparten la señal compartida de forma distinta; (3) las perturbaciones generan combinaciones imposibles (avance ≠ final − inicial); y (4) cambian la semilla, el ancho del núcleo o la discretización de LIME, o la referencia de SHAP. Ninguna de las dos explicaciones es causal: describen el comportamiento del modelo y no permiten afirmar que intervenir sobre una variable cambie la nota de un estudiante.

### Robustez y estabilidad de las métricas

Una métrica reportada como un único número oculta dos fuentes de variabilidad: la **partición** (qué estudiantes caen en cada fold) y la **aleatoriedad del algoritmo** (semillas de bootstrap, submuestreo o inicialización). Esta sección cuantifica ambas.

#### Media ± desviación estándar entre folds externos

Métricas de validación externa como media ± desviación estándar muestral de los cinco folds:

| Modelo | RMSE | MAE | MAPE (%) | R² | RMSE mín.–máx. por fold |
| --- | --- | --- | --- | --- | --- |
| XGBoost | 0,8156 ± 0,0344 | 0,6447 ± 0,0264 | 24,12 ± 2,14 | 0,4646 ± 0,0484 | 0,7560–0,8416 |
| SVM lineal | 0,8241 ± 0,0479 | 0,6503 ± 0,0408 | 24,16 ± 2,06 | 0,4530 ± 0,0640 | 0,7697–0,8948 |
| Ridge | 0,8253 ± 0,0520 | 0,6514 ± 0,0399 | 24,41 ± 2,19 | 0,4514 ± 0,0672 | 0,7642–0,8978 |
| Lasso | 0,8288 ± 0,0561 | 0,6542 ± 0,0439 | 24,46 ± 2,33 | 0,4465 ± 0,0727 | 0,7616–0,9065 |
| Random Forest | 0,8297 ± 0,0294 | 0,6619 ± 0,0291 | 24,92 ± 2,01 | 0,4457 ± 0,0502 | 0,7789–0,8495 |
| KNN | 0,8550 ± 0,0400 | 0,6809 ± 0,0308 | 25,77 ± 2,23 | 0,4121 ± 0,0482 | 0,7934–0,8968 |
| Decision Tree | 0,8948 ± 0,0325 | 0,7123 ± 0,0335 | 26,50 ± 2,05 | 0,3552 ± 0,0613 | 0,8424–0,9260 |

La desviación entre folds es de **0,029 a 0,056 puntos de RMSE**, del mismo orden que las diferencias entre modelos (0,009 de XGBoost a SVM; 0,079 de XGBoost a Decision Tree). Random Forest, Decision Tree y XGBoost son los más estables entre folds (SD 0,029–0,034); Ridge y Lasso los menos (0,052–0,056), porque los coeficientes lineales se ven más afectados por los estudiantes atípicos de cada fold.

```{figure} images/clasicos/robustez_folds_semillas.png
:alt: Izquierda, RMSE por fold de los siete modelos; derecha, RMSE medio de cinco folds con once semillas para cuatro modelos estocásticos.
:name: clasicos-robustez

Izquierda: RMSE de validación por fold externo. Derecha: RMSE medio de los cinco folds con 11 semillas del estimador.
```

El panel izquierdo muestra por qué conviene comparar por fold: **las líneas se mueven juntas**. El fold 1 es el más fácil para los siete modelos (RMSE 0,76–0,84) y el fold 2 el más difícil para cinco de ellos (0,83–0,93); la variación entre folds es mayor que la separación entre la mayoría de los modelos dentro de un mismo fold. Por eso las pruebas de la siguiente sección comparan rangos y diferencias **emparejadas por fold**, no medias marginales.

#### Sensibilidad a la semilla del estimador

Para los modelos con componente aleatoria (Random Forest: bootstrap y selección de variables; XGBoost: `subsample` y `colsample_bytree`; Decision Tree: desempate entre cortes; LinearSVR: orden del descenso coordinado) se repitió la validación externa con **11 semillas** (42 y 0–9). En cada fold se reutilizaron los hiperparámetros que ese fold había elegido y solo cambió `random_state`; con la semilla 42 se reproducen exactamente las métricas canónicas. KNN, Ridge y Lasso son deterministas con este solver y no se repiten.

```python
def fit_predict(key, params, seed, fitting, targets):
    model = pipeline_for(key).set_params(**params, modelo__random_state=seed)
    model.fit(fitting[FEATURES], fitting[TARGET])
    return [model.predict(frame[FEATURES]) for frame in targets]

for seed in [42, *range(10)]:
    for fold, (fit, val) in enumerate(splits, 1):
        params = fold_audit[fold - 1]['best_params']           # hiperparámetros elegidos por ese fold
        pred, = fit_predict(key, params, seed, train.iloc[fit], [train.iloc[val]])
```

| Modelo | RMSE CV semilla 42 | Media 11 semillas | SD entre semillas | Mín.–máx. | SD media por fold | RMSE test media ± SD | Test mín.–máx. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| XGBoost | 0,815581 | 0,815786 | 0,000509 | 0,8147–0,8166 | 0,00201 | 0,9123 ± 0,0012 | 0,9108–0,9138 |
| SVM lineal | 0,824106 | 0,824159 | 0,000041 | 0,8241–0,8242 | 0,00010 | 0,9299 ± 0,0001 | 0,9296–0,9300 |
| Random Forest | 0,829715 | 0,830179 | 0,000800 | 0,8288–0,8315 | 0,00168 | 0,9412 ± 0,0016 | 0,9390–0,9437 |
| Decision Tree | 0,894830 | 0,894982 | 0,000295 | 0,8944–0,8955 | 0,00039 | 1,0095 ± 0,0012 | 1,0080–1,0104 |

La variabilidad por semilla es **un orden de magnitud menor que la variabilidad entre folds**: la desviación estándar del RMSE medio de CV es 0,0008 en Random Forest, 0,0005 en XGBoost, 0,0003 en Decision Tree y 0,00004 en el SVM, frente a SD entre folds de 0,029 a 0,056. El rango de XGBoost entre semillas (0,8147–0,8166) no se cruza con el de Random Forest (0,8288–0,8315) ni con el valor del SVM (0,8241): **el orden XGBoost < SVM < Random Forest en CV no depende de la semilla**. En el test, la semilla mueve el RMSE de XGBoost entre 0,9108 y 0,9138 y el de Random Forest entre 0,9390 y 0,9437.

#### Sensibilidad a la semilla de la búsqueda

Las estrategias estocásticas también dependen de su semilla. Se repitió la búsqueda final en todo train de Random, TPE, DEAP y Halving con tres semillas nuevas (1, 2 y 3), además de la 42 original:

RMSE interno de la búsqueda final con cuatro semillas (42, 1, 2 y 3); el Grid es determinista y se muestra como referencia:

| Modelo | Random (media ± SD) | TPE (media ± SD) | DEAP (media ± SD) | Halving (media ± SD) | Mejor por semilla (mín.–máx.) | Grid (fijo) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SVM lineal | 0,8230 ± 0,0020 | 0,8212 ± 0,0004 | 0,8228 ± 0,0015 | 0,8230 ± 0,0020 | 0,8208–0,8211 | 0,8217 |
| KNN | 0,8498 ± 0,0014 | 0,8504 ± 0,0006 | 0,8493 ± 0,0012 | 0,8498 ± 0,0014 | 0,8481–0,8505 | 0,8482 |
| Ridge | 0,8245 ± 0,0001 | 0,8244 ± 0,0000 | 0,8246 ± 0,0003 | 0,8245 ± 0,0001 | 0,8243–0,8243 | 0,8243 |
| Lasso | 0,8273 ± 0,0001 | 0,8273 ± 0,0001 | 0,8273 ± 0,0002 | 0,8284 ± 0,0002 | 0,8272–0,8272 | 0,8273 |
| Random Forest | 0,8288 ± 0,0005 | 0,8283 ± 0,0005 | 0,8288 ± 0,0005 | 0,8289 ± 0,0005 | 0,8278–0,8285 | 0,8279 |
| XGBoost | 0,8083 ± 0,0012 | 0,8075 ± 0,0007 | 0,8106 ± 0,0028 | 0,8083 ± 0,0012 | 0,8066–0,8081 | 0,8085 |
| Decision Tree | 0,9022 ± 0,0023 | 0,9021 ± 0,0029 | 0,9044 ± 0,0042 | 0,9045 ± 0,0053 | 0,8990–0,9026 | 0,9071 |

TPE es la estrategia más estable frente a su semilla: su desviación estándar del RMSE interno no supera 0,0007 salvo en Decision Tree, frente a 0,0028 de DEAP en XGBoost y 0,0020 de Random en el SVM. Con cualquiera de las cuatro semillas, la media de TPE mejora al Grid en el SVM, XGBoost y Decision Tree. El **método ganador sí cambia con la semilla**: en XGBoost gana TPE con las semillas 1, 2 y 42 y Random con la 3; en Ridge, KNN y Random Forest el Grid recupera el primer lugar con varias semillas. Sin embargo, el mejor RMSE interno entre semillas varía como máximo 0,0036 (Decision Tree) y menos de 0,0025 en los demás modelos. La conclusión del apartado de búsqueda se mantiene: la estrategia concreta importa poco frente a la familia del modelo, y la estrategia que "gana" en una ejecución no es una propiedad estable.

#### ¿Son las diferencias entre modelos mayores que la variabilidad intrínseca?

La tabla compara la diferencia de RMSE medio de CV de cada modelo frente a XGBoost con tres fuentes de variabilidad: la desviación entre folds, la desviación por semilla del estimador y la desviación por semilla de la búsqueda (mejor RMSE interno entre las cuatro semillas).

| Modelo frente a XGBoost | Δ RMSE medio CV | SD entre folds del modelo | Δ / SD folds | SD semilla estimador | SD semilla búsqueda (RMSE interno) | Folds en que gana XGBoost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SVM lineal | 0,0085 | 0,0479 | 0,18 | 0,00004 | 0,00010 | 2 de 5 |
| Ridge | 0,0097 | 0,0520 | 0,19 | determinista | 0,00000 | 3 de 5 |
| Lasso | 0,0132 | 0,0561 | 0,24 | determinista | 0,00001 | 3 de 5 |
| Random Forest | 0,0141 | 0,0294 | 0,48 | 0,00080 | 0,00031 | 5 de 5 |
| KNN | 0,0395 | 0,0400 | 0,99 | determinista | 0,00112 | 5 de 5 |
| Decision Tree | 0,0792 | 0,0325 | 2,44 | 0,00029 | 0,00160 | 5 de 5 |

Solo la diferencia con **Decision Tree** supera con claridad la desviación entre folds (2,4 SD) y la de **KNN** la iguala (≈ 1 SD); XGBoost gana a ambos, y a Random Forest, en los cinco folds. Entre XGBoost, SVM, Ridge y Lasso, las diferencias de RMSE medio (0,009 a 0,013) son **menores que una cuarta parte de la desviación entre folds** y XGBoost solo gana en dos o tres de los cinco folds. Las semillas, del estimador y de la búsqueda, mueven el RMSE menos de 0,002: son una fuente de variación despreciable frente a la partición, de modo que **el ruido que limita las comparaciones es el de los folds, no el de la aleatoriedad algorítmica**. Con solo cinco folds dependientes, la inspección de medias y desviaciones no basta para decidir si una diferencia es real: hacen falta pruebas formales que usen el emparejamiento por fold y controlen las comparaciones múltiples. Eso motiva directamente la sección siguiente.

## Comparación estadística

La comparación sigue el diseño del dashboard en tres etapas: una prueba global que decide si hay alguna diferencia, comparaciones post hoc que identifican cuáles, y un contraste por estudiante de los cinco primeros del MCS frente al SVM, complementados siempre con tamaños de efecto. Las etapas 1 y 2 usan exclusivamente las métricas de los cinco folds externos; la etapa 3 usa las predicciones fuera de muestra de esa misma validación y presenta el test solo como complemento descriptivo. El test no participa en la elección de modelos.

### Etapa 1 · Prueba global de Friedman

Antes de cualquier comparación por pares se contrasta si al menos un modelo difiere de los demás. El **test de Friedman** es el análogo no paramétrico del ANOVA de medidas repetidas: cada fold externo es un bloque, cada modelo un tratamiento, y se ordena el RMSE **dentro de cada fold** (rango 1 = menor error; empates promediados). La hipótesis nula es que todos los modelos tienen el mismo rango promedio:

$$
\chi^2_F = \frac{12N}{k(k+1)}\left[\sum_{j=1}^{k} \bar R_j^{\,2} - \frac{k(k+1)^2}{4}\right],\qquad N = 5 \text{ folds},\; k = 7 \text{ modelos}
$$

```python
def friedman_comparison(folds, models):
    matrix = folds.pivot(index='Fold', columns='Modelo', values='RMSE')[models]
    ranks = matrix.rank(axis=1, method='average', ascending=True)     # rango 1 = menor RMSE en el fold
    statistic, p = friedmanchisquare(*[ranks[name] for name in models])
    return {'statistic': statistic, 'pvalue': p, 'df': len(models) - 1,
            'ranking': ranks.mean().sort_values()}
```

```{figure} images/clasicos/stats_friedman_nemenyi.png
:alt: Mapa de rangos por fold y diagrama de diferencia crítica de Nemenyi con los rangos promedio.
:name: clasicos-friedman

Rangos del RMSE en cada fold externo (izquierda) y rangos promedio con la diferencia crítica de Nemenyi (derecha).
```

| Modelo | Fold 1 | Fold 2 | Fold 3 | Fold 4 | Fold 5 | Rango promedio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| XGBoost | 1 | 1 | 2 | 4 | 4 | **2,4** |
| SVM lineal | 4 | 4 | 1 | 3 | 1 | 2,6 |
| Ridge | 3 | 5 | 4 | 1 | 2 | 3,0 |
| Lasso | 2 | 6 | 5 | 2 | 3 | 3,6 |
| Random Forest | 5 | 2 | 3 | 5 | 5 | 4,0 |
| KNN | 6 | 3 | 6 | 6 | 6 | 5,4 |
| Decision Tree | 7 | 7 | 7 | 7 | 7 | 7,0 |

| Estadístico de Friedman (χ²) | gl | p-valor asintótico | Decisión (α = 0,05) |
| ---: | ---: | ---: | --- |
| 17,8286 | 6 | 0,00668 | Se rechaza H₀ · exploratorio |

**Se rechaza la hipótesis de rangos iguales**: al menos dos modelos difieren. El rechazo es exploratorio por dos razones: con cinco bloques y siete modelos se está por debajo de la recomendación de SciPy para la aproximación χ² (más de diez bloques), y los folds no son independientes porque sus entrenamientos comparten el 75 % de los estudiantes. Además, el rechazo global no identifica qué pares difieren ni demuestra que el primero supere al SVM. Decision Tree es último en los cinco folds y KNN en cuatro: buena parte del estadístico proviene de esos dos modelos.

### Etapa 2 · Comparaciones post hoc

#### Nemenyi (complemento de este informe)

El post hoc clásico para Friedman es la prueba de **Nemenyi** (Demšar, 2006): dos modelos difieren si sus rangos promedio se separan más que la diferencia crítica

$$
CD = q_{\alpha}\sqrt{\frac{k(k+1)}{6N}} = 2{,}949\sqrt{\frac{7 \cdot 8}{6 \cdot 5}} = 4{,}03 .
$$

Solo dos de los 21 pares superan la diferencia crítica: **XGBoost frente a Decision Tree** (Δ rango = 4,6) y **SVM lineal frente a Decision Tree** (4,4); Ridge frente a Decision Tree queda en el límite (4,0). Ningún par entre XGBoost, SVM, Ridge, Lasso, Random Forest y KNN es distinguible: la diferencia crítica es muy grande porque cinco folds aportan poca información por par. Nemenyi no forma parte del dashboard; se añade aquí porque es el compañero habitual de Friedman y usa los mismos rangos.

#### Model Confidence Set (MCS · dashboard)

El dashboard usa el **Model Confidence Set** de Hansen, Lunde y Nason: en lugar de comparar todos los pares, elimina secuencialmente el peor modelo mientras se rechace la igualdad de capacidad predictiva del conjunto restante. La pérdida es el MSE de cada fold; el estadístico es T_R = max |t_ij| con t_ij = media(L_i − L_j)/SE_bootstrap, y el bootstrap **enumera los 3.125 remuestreos posibles** de cinco folds con reemplazo (sin semilla ni error Monte Carlo). Los modelos con p MCS ≥ 0,10 se conservan:

| Modelo | Rango promedio de pérdida | MSE medio CV | p-valor MCS | En MCS (α = 0,10) | Paso de eliminación |
| --- | ---: | ---: | ---: | --- | ---: |
| XGBoost | 2,4 | 0,6661 | 1,0000 | Sí | 7 |
| SVM lineal | 2,6 | 0,6810 | 0,7664 | Sí | 6 |
| Ridge | 3,0 | 0,6832 | 0,7664 | Sí | 5 |
| Lasso | 3,6 | 0,6895 | 0,0765 | No | 4 |
| Random Forest | 4,0 | 0,6891 | 0,0003 | No | 3 |
| KNN | 5,4 | 0,7324 | 0,0000 | No | 2 |
| Decision Tree | 7,0 | 0,8016 | 0,0000 | No | 1 |

El conjunto exploratorio conserva **XGBoost, SVM lineal y Ridge**. Que Random Forest salga antes que Lasso pese a un MSE medio similar se debe a que sus diferencias frente a los demás son más consistentes entre folds (menor error estándar). Este conjunto **no tiene cobertura del 90 % demostrada**: el remuestreo de cinco folds dependientes no corrige esa dependencia, y un p MCS no es la probabilidad de que un modelo sea el mejor.

#### Comparaciones dirigidas entre finalistas (DM-HLN adaptado · dashboard)

Entre los tres finalistas se comparan los tres pares con dos lecturas de la misma diferencia. Las columnas **«folds»** son intervalos percentiles de los mismos remuestreos de folds: descriptivos, no estacionarios y sin valor inferencial por sí solos. Las columnas **«por estudiante»** y los p provienen de un contraste del tipo **Diebold–Mariano con corrección HLN, adaptado** a este diseño, que es el mismo que usa la etapa siguiente frente al SVM:

| Modelo A | Modelo B | Δ MSE (A − B) | IC 95 % · folds | Δ RMSE (A − B) · por estudiante | IC 95 % · estudiantes | p crudo | p con HLN |
| --- | --- | ---: | --- | ---: | --- | ---: | ---: |
| XGBoost | SVM lineal | −0,0149 | [−0,0631; 0,0215] | −0,0091 | [−0,0290; 0,0095] | 0,3560 | 0,3564 |
| XGBoost | Ridge | −0,0171 | [−0,0680; 0,0219] | −0,0104 | [−0,0340; 0,0098] | 0,3542 | 0,3546 |
| SVM lineal | Ridge | −0,0022 | [−0,0095; 0,0050] | −0,0014 | [−0,0096; 0,0064] | 0,7488 | 0,7490 |

**Ninguno de los tres pares difiere significativamente** (p crudo < 0,05): XGBoost tiene el menor error de los tres, pero ni frente al SVM ni frente a Ridge se distingue del azar, y SVM y Ridge son prácticamente indistinguibles. Esto no demuestra equivalencia; indica que los datos no permiten separarlos.

**Por qué se adapta el DM-HLN y qué adaptación se hizo.** El contraste de Diebold–Mariano y su corrección de Harvey, Leybourne y Newbold (HLN) se diseñaron para series de tiempo: comparan los errores de dos pronósticos hechos en fechas sucesivas, con un horizonte *h*, y corrigen la dependencia entre fechas vecinas con una varianza HAC. Aquí no hay secuencia de pronósticos ni horizonte: el índice de fold y el orden de las filas no son tiempo, y con cinco folds la prueba tendría solo cinco observaciones con entrenamientos solapados. Lo que sí existe es otra dependencia, la de un mismo estudiante que aparece en varios periodos. Por eso se conserva la idea central, probar que la pérdida media de dos predictores es la misma, y se adapta así:

1. la observación es el **estudiante**, no la fecha;
2. el error estándar es **robusto por estudiante** (cluster) en lugar de HAC;
3. la corrección HLN se aplica con **h = 1**: el estadístico se multiplica por $\sqrt{(G-1)/G}$ y se compara con una $t$ de Student con $G-1$ grados de libertad; no hay horizonte de varios pasos porque no existen pronósticos solapados;
4. las pérdidas son las **predicciones fuera de muestra de la validación cruzada**, de modo que cada nota la predice un modelo que no vio a ese estudiante;
5. el IC 95 % se obtiene **remuestreando estudiantes**, no con un bootstrap estacionario.

Cada par se contrasta de forma independiente y **sin corrección de Holm**: son preguntas separadas y no se pretende afirmar nada sobre el conjunto. La adaptación es exploratoria: no incorpora la variabilidad de reentrenar con otros estudiantes y los finalistas se eligieron con esta misma validación. Las fórmulas completas están en la etapa siguiente.

Las pruebas de Giacomini–White, Clark–West y el bootstrap estacionario **no son aplicables** a este diseño: no hay una serie ordenada de pronósticos con horizonte definido, ni una pareja anidada restringida/ampliada, ni una secuencia estacionaria. Los folds no son tiempo.

### Etapa 3 · Contraste tipo Diebold–Mariano por estudiante frente al SVM

Las etapas anteriores ordenan los modelos, pero no responden la pregunta práctica: **¿algún clásico se equivoca significativamente menos que el SVM lineal?** Esta etapa la contesta con un contraste del tipo **Diebold–Mariano**, que compara la pérdida promedio de dos predictores. Para cada estudiante se mide cuánto más (o menos) se equivoca el modelo candidato que el SVM, con el error cuadrático como pérdida, y se promedia esa diferencia entre estudiantes. La hipótesis nula es que **en promedio ambos modelos se equivocan lo mismo**; una diferencia negativa favorece al candidato. No es la versión de series de tiempo: aquí no hay secuencia de pronósticos, y la dependencia que se corrige es la de las filas de un mismo estudiante, que aparece en varios periodos y no puede tratarse como independiente. Por eso la unidad de análisis es el estudiante y las predicciones son las **fuera de muestra de la validación cruzada** (cada nota la predice un modelo que no vio a ese estudiante), con lo que participan los 1.293 estudiantes de entrenamiento (1.309 registros) y no solo los 188 del test.

Sea $D_i$ la suma, sobre los registros del estudiante $i$, de la diferencia de error cuadrático entre el modelo y el SVM, $n_i$ su número de registros y $G$ el número de estudiantes. La diferencia media y su error estándar agrupado por estudiante son

$$
\bar d = \frac{\sum_i D_i}{\sum_i n_i},\qquad
\widehat{SE} = \frac{1}{\sum_i n_i}\sqrt{\frac{G}{G-1}\sum_{i=1}^{G}\left(D_i - \bar d\, n_i\right)^2},\qquad
z = \frac{\bar d}{\widehat{SE}} .
$$

Para muestras finitas se añade la **corrección de Harvey, Leybourne y Newbold (HLN)** en su versión para horizonte $h=1$: el estadístico se multiplica por $\sqrt{(G-1)/G}$ y se compara con una $t$ de Student con $G-1$ grados de libertad. No se usa la forma con $h>1$ porque las observaciones son estudiantes y no periodos consecutivos. Con $G = 1.293$ el efecto es mínimo y no cambia ningún veredicto; se reporta para que quede visible que la corrección se aplicó.

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

**Qué modelos se comparan.** Se toman los cinco primeros del MCS de la etapa anterior, en el orden en que el propio MCS los elimina y omitiendo al SVM, que es la referencia. El MCS conserva solo dos modelos distintos del SVM (XGBoost y Ridge); para llegar a cinco se completa con los siguientes en su orden de eliminación: Lasso, Random Forest y KNN. Decision Tree, el primero en ser eliminado, queda fuera de esta etapa. Los intervalos de confianza de ΔRMSE se obtienen remuestreando estudiantes completos (9.999 réplicas, semilla 20261020).

**Comparaciones independientes, sin corrección de Holm.** Cada modelo se compara únicamente contra el SVM, como una pregunta propia («¿este modelo mejora al SVM?»); **no se comparan entre sí**. Como no se pretende afirmar nada sobre el conjunto completo, no se aplicó la corrección de Holm, que solo es necesaria cuando se declara una conclusión conjunta sobre toda la familia de pruebas. Cada resultado se juzga con su propio p crudo (α = 0,05). El costo es que, al realizar cinco pruebas separadas, la probabilidad de que alguna resulte significativa por azar supera el 5 %; esto se tiene presente al leer los resultados.

| Posición MCS | Modelo vs SVM | Δ MSE | Δ RMSE (puntos) | IC 95 % ΔRMSE | p crudo | p con HLN | p t corregida (CV) | Conclusión |
| ---: | --- | ---: | ---: | --- | ---: | ---: | ---: | --- |
| 1 | XGBoost | −0,0149 | −0,0091 | [−0,0290; 0,0095] | 0,3560 | 0,3564 | 0,7142 | Diferencia no significativa |
| 2 | Ridge | 0,0022 | 0,0014 | [−0,0064; 0,0096] | 0,7488 | 0,7490 | 0,7807 | Diferencia no significativa |
| 3 | Lasso | 0,0085 | 0,0051 | [−0,0031; 0,0140] | 0,2561 | 0,2565 | 0,4982 | Diferencia no significativa |
| 4 | Random Forest | 0,0081 | 0,0049 | [−0,0161; 0,0257] | 0,6441 | 0,6443 | 0,8105 | Diferencia no significativa |
| 5 | KNN | 0,0514 | 0,0306 | [0,0077; 0,0525] | **0,0082** | **0,0083** | 0,2459 | **Deterioro significativo** |

**Ninguno de los cinco modelos presentó un resultado significativamente mejor que el SVM lineal, y solo se identificó uno con un resultado inferior: KNN** (ΔRMSE = +0,0306). XGBoost, el de menor error medio, queda 0,009 puntos de RMSE por debajo del SVM, pero esa diferencia es compatible con el azar (p = 0,356); Ridge, Lasso y Random Forest tienen diferencias aún menores y de signo contrario. "Diferencia no significativa" no significa equivalencia: indica que los datos no permiten distinguir a esos modelos del SVM.

**La prueba conservadora.** La última columna antes de la conclusión es una comprobación de cautela que hace la misma comparación con otra fuente de azar. En lugar de 1.293 estudiantes usa como observaciones los **cinco folds de validación** y agranda su error estándar, porque los entrenamientos de esos folds comparten la mayor parte de los datos (corrección de Nadeau–Bengio, con 4 grados de libertad). Responde a una pregunta distinta: *si el algoritmo se reentrenara con otros datos, ¿seguiría siendo mejor (o peor) que el SVM?* La prueba por estudiante trata los modelos como fijos y no incluye esa variabilidad de reentrenamiento, por lo que tiende a ser optimista; la conservadora tiende a ser exigente. La lectura conjunta es:

- Para **KNN**, la prueba por estudiante indica que es peor que el SVM en esta muestra (p = 0,008), pero la conservadora no lo confirma (p = 0,246). El deterioro es **probable, pero no confirmado**.
- Para los otros cuatro, ninguna de las dos pruebas detecta diferencia.

**Por qué la prueba conservadora rara vez resulta significativa aquí.** (1) Solo tiene cinco observaciones, es decir 4 grados de libertad: el valor crítico de la $t$ es 2,78 y no ≈ 1,96. (2) Cada fold deja fuera unos 260 estudiantes y los entrenamientos comparten cerca del 80 % de los datos; la corrección lo reconoce y multiplica el error estándar por ≈ 1,5. (3) La dificultad cambia entre folds, de modo que la diferencia de RMSE de un mismo modelo varía bastante de un fold a otro. Con el error estándar típico de la tabla (≈ 0,022), un modelo tendría que mejorar al SVM en ≈ 0,060 puntos de RMSE para alcanzar p < 0,05, el doble de la mayor diferencia observada (0,031). Más repeticiones de la validación cruzada ayudarían poco, pues parte del error proviene del tamaño del conjunto (1.309 registros de 1.293 estudiantes) y no del número de particiones. Un p alto en esa prueba significa, entonces, «no hay potencia para confirmarlo», y no «el modelo no sirve».

**Complemento en el test temporal (202530).** El mismo contraste sobre los 188 estudiantes del periodo reservado sirve para ver si el signo se mantiene fuera de la validación cruzada. Los modelos son fijos y el test ya había sido revisado, de modo que es descriptivo y con menor potencia:

| Modelo vs SVM | Δ RMSE (puntos) | IC 95 % ΔRMSE | p crudo | p con HLN | Conclusión |
| --- | ---: | --- | ---: | ---: | --- |
| XGBoost | −0,0162 | [−0,0493; 0,0171] | 0,3349 | 0,3374 | Diferencia no significativa |
| Ridge | −0,0129 | [−0,0345; 0,0037] | 0,1998 | 0,2026 | Diferencia no significativa |
| Lasso | −0,0102 | [−0,0244; 0,0015] | 0,1287 | 0,1314 | Diferencia no significativa |
| Random Forest | 0,0097 | [−0,0258; 0,0455] | 0,5922 | 0,5938 | Diferencia no significativa |
| KNN | −0,0060 | [−0,0442; 0,0318] | 0,7609 | 0,7619 | Diferencia no significativa |

En el test ningún modelo difiere significativamente del SVM. Además, **el deterioro de KNN observado en validación no se reproduce** (ΔRMSE = −0,006, p = 0,761), lo que refuerza que ese resultado debe leerse con cautela. XGBoost, Ridge y Lasso muestran diferencias negativas, favorables al candidato, pero con intervalos que incluyen el cero.

**Alcance y límites.** (1) El p por estudiante no incorpora la variabilidad de reentrenar con otros estudiantes. (2) Los cinco modelos se eligieron por su desempeño en esta misma validación cruzada (MCS); ni esa selección ni la multiplicidad están corregidas, de modo que la inferencia es exploratoria. (3) Ningún modelo ni parámetro se elige con el test. Esta etapa sustituye al contraste por bootstrap-t con Holm sobre los 188 estudiantes del test que usaba la versión anterior del informe: al usar las predicciones de validación cruzada se dispone de 1.293 estudiantes en lugar de 188 y las comparaciones se plantean de forma independiente, tal como se formulan las preguntas.

### Tamaño del efecto

La significancia no implica relevancia práctica y la falta de significancia no implica ausencia de efecto. Para los 21 pares se calculan, sobre el MSE de los cinco folds:

- **Delta de Cliff**: δ = P(L_A > L_B) − P(L_A < L_B) sobre las 25 comparaciones cruzadas de folds; varía entre −1 y 1, es no paramétrica y coherente con el uso de rangos de Friedman–Nemenyi. Resume dominancia marginal y no conserva el emparejamiento.
- **d de Cohen emparejado (d_z)**: media(L_A − L_B)/SD(L_A − L_B) con SD muestral; razonable si las diferencias de pérdida son aproximadamente simétricas, algo que cinco diferencias no permiten verificar.

```python
def effect_sizes(a, b):
    delta = float(np.sign(a[:, None] - b[None, :]).mean())    # Cliff: 5 × 5 comparaciones cruzadas
    difference = a - b
    dz = difference.mean() / difference.std(ddof=1)            # Cohen emparejado
    return delta, dz
```

| Modelo A | Modelo B | Δ MSE (A − B) | Delta de Cliff | d_z de Cohen | Magnitud (Cliff) |
| --- | --- | ---: | ---: | ---: | --- |
| XGBoost | SVM lineal | −0,0149 | −0,04 | −0,27 | despreciable |
| XGBoost | Ridge | −0,0171 | −0,12 | −0,30 | despreciable |
| XGBoost | Lasso | −0,0234 | −0,12 | −0,37 | despreciable |
| XGBoost | Random Forest | −0,0230 | −0,44 | −1,62 | mediana |
| XGBoost | KNN | −0,0663 | −0,60 | −2,94 | grande |
| XGBoost | Decision Tree | −0,1354 | −1,00 | −5,75 | grande |
| SVM lineal | Ridge | −0,0022 | −0,04 | −0,24 | despreciable |
| SVM lineal | Lasso | −0,0085 | −0,04 | −0,54 | despreciable |
| SVM lineal | Random Forest | −0,0081 | −0,20 | −0,15 | pequeña |
| SVM lineal | KNN | −0,0514 | −0,36 | −0,88 | mediana |
| SVM lineal | Decision Tree | −0,1206 | −0,84 | −2,57 | grande |
| Ridge | Lasso | −0,0062 | −0,12 | −0,85 | despreciable |
| Ridge | Random Forest | −0,0059 | −0,12 | −0,10 | despreciable |
| Ridge | KNN | −0,0492 | −0,36 | −0,85 | mediana |
| Ridge | Decision Tree | −0,1183 | −0,76 | −2,30 | grande |
| Lasso | Random Forest | 0,0004 | −0,04 | 0,01 | despreciable |
| Lasso | KNN | −0,0429 | −0,36 | −0,69 | mediana |
| Lasso | Decision Tree | −0,1121 | −0,68 | −1,99 | grande |
| Random Forest | KNN | −0,0433 | −0,52 | −1,23 | grande |
| Random Forest | Decision Tree | −0,1124 | −0,84 | −7,58 | grande |
| KNN | Decision Tree | −0,0692 | −0,68 | −1,66 | grande |

Con los umbrales convencionales de Cliff (|δ| < 0,147 despreciable; < 0,33 pequeño; < 0,474 mediano; ≥ 0,474 grande; Romano et al., 2006), **los efectos frente a Decision Tree son grandes** en todos los casos (δ entre −0,68 y −1,00) y los efectos frente a KNN son medianos o grandes. Entre XGBoost, SVM, Ridge y Lasso los δ son despreciables (|δ| ≤ 0,12): sus distribuciones de MSE por fold se solapan casi por completo. La d de Cohen puede ser grande aun con δ pequeño —XGBoost frente a Random Forest: δ = −0,44 pero d_z = −1,62— porque d_z usa el emparejamiento: XGBoost gana a Random Forest en los cinco folds por márgenes pequeños pero consistentes. Los dos tamaños de efecto miden cosas distintas y deben leerse juntos con la diferencia absoluta (0,02 puntos² de MSE, ≈ 0,014 puntos de RMSE), que es pequeña en la escala de la nota. No existe un umbral educativo acordado de relevancia práctica.

## Resultados finales y conclusiones

| Modelo | Método de búsqueda final | RMSE CV (media ± SD) | MAE CV | RMSE test | MAE test | Rango Friedman | En MCS | vs SVM en CV (p crudo por estudiante) |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | ---: |
| XGBoost | TPE | **0,8156 ± 0,0344** | **0,6447** | **0,9137** | **0,7391** | **2,4** | Sí | 0,356 |
| SVM lineal | TPE | 0,8241 ± 0,0479 | 0,6503 | 0,9299 | 0,7581 | 2,6 | Sí | — |
| Ridge | TPE | 0,8253 ± 0,0520 | 0,6514 | 0,9170 | 0,7544 | 3,0 | Sí | 0,749 |
| Lasso | DEAP | 0,8288 ± 0,0561 | 0,6542 | 0,9197 | 0,7548 | 3,6 | No | 0,256 |
| Random Forest | Grid | 0,8297 ± 0,0294 | 0,6619 | 0,9396 | 0,7658 | 4,0 | No | 0,644 |
| KNN | DEAP | 0,8550 ± 0,0400 | 0,6809 | 0,9239 | 0,7517 | 5,4 | No | **0,008** (peor) |
| Decision Tree | Random | 0,8948 ± 0,0325 | 0,7123 | 1,0104 | 0,8262 | 7,0 | No | No evaluado |

**Sobre la optimización de hiperparámetros.** Las cinco estrategias llegan a valores de RMSE interno separados por menos de 6 milésimas, muy por debajo del ruido entre folds. **TPE fue la estrategia más eficaz** (elegida en 15 de 42 búsquedas, incluidas las finales de XGBoost, SVM y Ridge) con un 35 % menos de tiempo que el Grid; DEAP fue la más barata pero mostró convergencia prematura en todos los modelos, y Successive Halving no aportó ventajas en una muestra de este tamaño. En este problema, la elección de la familia de modelos importa mucho más que la de la estrategia de búsqueda.

**Sobre el desempeño.** XGBoost obtiene el menor error en validación externa y en el test, el mejor rango promedio de Friedman y una variabilidad entre folds y semillas baja. Sin embargo, su ventaja sobre el SVM lineal es de 0,0085 puntos de RMSE en CV y 0,016 en el test: **no es estadísticamente distinguible** (Nemenyi, MCS y el contraste por estudiante coinciden: p = 0,356) y su tamaño de efecto por fold es despreciable (δ = −0,04). El grupo XGBoost–SVM–Ridge forma el conjunto de modelos con desempeño indistinguible; Decision Tree es claramente inferior, con efectos grandes frente a todos. En el contraste por estudiante ningún clásico supera significativamente al SVM y solo KNN resulta peor (p = 0,008), un deterioro que la prueba conservadora no confirma (p = 0,246) y que no se reproduce en el test.

**Sobre los residuos.** Todos los modelos comparten heterocedasticidad (White y Breusch–Pagan), dependencia por grupo en validación (BDS), asimetría negativa y regresión hacia la media. Son propiedades de la nota acotada y discreta y de la información disponible, no de una familia: más flexibilidad no corrige su forma. El caso de mayor error —un estudiante con perfil de nota alta que obtuvo 1,0— es el mismo para seis modelos.

**Sobre la interpretabilidad.** SHAP muestra que el puntaje global de Saber 11 es la variable más influyente en todas las familias, seguido del dominio inicial en los árboles y de las categorías de temas y la división en los lineales. Las familias reparten de forma distinta la señal de variables redundantes, y LIME puede atribuir peso a variables que el modelo no usa (cumplimiento de la meta en XGBoost). Las explicaciones describen el modelo, no causas.

**Decisión.** XGBoost es el clásico recomendado para continuar la comparación con otras familias, por su menor error medio y su estabilidad, pero con la advertencia explícita de que su superioridad sobre el SVM lineal y Ridge **no está demostrada**: con cinco folds dependientes, la evidencia es exploratoria. Un modelo lineal regularizado ofrece un error casi igual con mayor transparencia. Antes de un uso operativo conviene validar en otros periodos, con validación cruzada repetida que aumente los bloques de Friedman, y explorar formulaciones para notas acotadas que atiendan la heterocedasticidad.

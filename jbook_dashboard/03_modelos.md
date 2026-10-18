---
title: Modelos
description: Split y validación cruzada, búsqueda de hiperparámetros y resultados de los modelos lineales.
---

# Modelos

Este capítulo sigue la pestaña **03 Modelos predictivos** del dashboard y documenta el modelo lineal que sirve de referencia para las demás familias. Todas las familias descritas en el tablero usan la misma separación y los mismos folds externos.

El capítulo se organiza en dos bloques. **Split y CV** fija la metodología que comparten todas las familias: cómo se reserva el test, cómo se agrupan los estudiantes y cómo se construye el pipeline. **Modelos lineales** documenta la implementación concreta del SVM, la comparación de estrategias de búsqueda, la evaluación frente a Dummy y el análisis de errores que sirve de base para las demás familias.

## Split y CV

Esta sección responde tres preguntas: qué datos se reservan para evaluar, cómo se evita que un estudiante participe a la vez en entrenamiento y validación, y qué transformaciones se aplican antes de ajustar cualquier modelo. Las decisiones se comparten con todas las familias para que las comparaciones posteriores sean homogéneas.

### Test por periodo académico

El periodo **202530** se reserva como test. Train contiene los cinco periodos anteriores (202310, 202330, 202410, 202430 y 202510). Se excluyen de train **0 filas de estudiantes presentes en el periodo reservado**; las **0 inconsistencias** de negocio detectadas tampoco requieren purga adicional. Así se evalúan un periodo posterior y estudiantes que no participaron en entrenamiento.

Los **1.497 registros con nota** se reparten en **1.309 de train** (1.293 estudiantes) y **188 de test** (188 estudiantes). La tabla siguiente resume la auditoría de la partición.

| Partición | Periodos | Filas | Estudiantes | Reglas incumplidas |
| --- | --- | ---: | ---: | ---: |
| Train | 202310–202510 | 1.309 | 1.293 | 0 |
| Test | 202530 | 188 | 188 | 0 |
| Total con objetivo | — | 1.497 | — | 0 |

```{figure} images/11_split_test.jpg
:alt: Diagrama de separación temporal entre train y test por periodo académico.
:name: split-test

Test por periodo académico: el periodo 202530 queda fuera del entrenamiento.
```

### GroupKFold por estudiante

La separación temporal define el test; la validación interna necesita además agrupar por estudiante. Esta sección describe cómo se construyen los folds y cómo se generan las predicciones OOF que se usan para comparar modelos.

Un grupo es un estudiante y un fold contiene varios estudiantes completos. Si una persona tiene más de un registro, todos permanecen juntos: nunca participa a la vez en entrenamiento y validación de una misma iteración. Los 1.309 registros forman cinco folds externos con tamaños equilibrados.

| Fold | Filas de ajuste | Filas de validación | Estudiantes en validación | Método elegido |
| ---: | ---: | ---: | ---: | --- |
| 1 | 1.047 | 262 | 258 | Grid Search |
| 2 | 1.047 | 262 | 259 | Genética DEAP |
| 3 | 1.047 | 262 | 259 | Grid Search |
| 4 | 1.047 | 262 | 259 | Bayesiana TPE |
| 5 | 1.048 | 261 | 258 | Random Search |

En cada iteración externa, solo los estudiantes de los cuatro bloques de entrenamiento se redistribuyen en **cinco folds internos**, manteniendo otra vez juntas todas las filas de cada persona. La búsqueda de hiperparámetros se ejecuta dentro de esos folds internos; el fold externo reservado no participa. Imputación, escalado y codificación también se aprenden dentro de cada ajuste. Las predicciones resultantes son **OOF (fuera del fold)**: cada registro se predice sin que ningún registro de ese estudiante haya participado en el ajuste o en la selección de sus parámetros.

```{figure} images/12_split_groupkfold.jpg
:alt: Esquema de cinco folds externos con bloques de entrenamiento y validación por estudiante.
:name: split-groupkfold

GroupKFold por estudiante: cinco folds externos y validación fuera del fold.
```

### Código de la separación y las particiones

Las decisiones anteriores no son solo conceptuales: están implementadas en funciones concretas. Los fragmentos siguientes muestran cómo se reserva el periodo test, se purgan estudiantes y se verifica que no haya solapamientos entre entrenamiento y validación.

La separación temporal y la purga de estudiantes se implementan en `load_partitions()`. El fragmento siguiente conserva las decisiones centrales: reservar todos los identificadores del periodo test, excluir filas sin objetivo, aplicar las reglas de negocio y comprobar que no haya estudiantes compartidos.

```python
TEST_PERIOD = 202530
TARGET = 'nota_primer_parcial'
GROUP = 'estudiante'

held_ids = set(frame.loc[frame[PERIOD].eq(TEST_PERIOD), GROUP])
missing = frame[TARGET].isna()
valid_target = frame.loc[~missing].copy()
test_raw = valid_target.loc[valid_target[PERIOD].eq(TEST_PERIOD)]
earlier = valid_target.loc[valid_target[PERIOD].lt(TEST_PERIOD)]
purged = earlier[GROUP].isin(held_ids)
train_raw = earlier.loc[~purged]

train_rules, test_rules = business_violations(train_raw), business_violations(test_raw)
train = train_raw.loc[~train_rules.any(axis=1)].reset_index(drop=True)
test = test_raw.loc[~test_rules.any(axis=1)].reset_index(drop=True)
assert not set(train[GROUP]) & set(test[GROUP])
assert train[PERIOD].max() < test[PERIOD].min()
```

La validación agrupada se obtiene con `GroupKFold` y se verifica que ningún estudiante aparezca a la vez en ajuste y validación:

```python
def grouped_splits(frame, n_splits=5):
    splits = list(GroupKFold(n_splits=n_splits).split(
        frame[FEATURES], frame[TARGET], frame[GROUP]))
    for fit, val in splits:
        assert not set(frame.iloc[fit][GROUP]) & set(frame.iloc[val][GROUP])
    return splits
```

### Pipeline compartido

Con las particiones definidas, el siguiente paso es transformar las variables. El pipeline debe aprender sus estadísticas dentro de cada fold y aplicarlas después a la validación y al test; de otro modo, la evaluación dejaría de ser externa.

LinearSVR, Ridge y Lasso comparten la preparación: mediana en numéricas, `log1p` en las tres medidas de tiempo, `StandardScaler` en las numéricas, moda en categóricas y one-hot con una categoría de referencia. El ajuste final produce **67 columnas transformadas** a partir de **15 variables predictoras**. La nota se mantiene en su escala original y no se normaliza.

```{figure} images/13_split_pipeline.jpg
:alt: Flujo del pipeline de modelos lineales con entradas, unión, regresión y salida.
:name: split-pipeline

Pipeline de los modelos lineales: 15 predictoras, 67 columnas transformadas y salida en escala original.
```

```python
def make_pipeline(dummy=False):
    times = [c for c in NUMERIC if c.startswith('Tiempo')]
    plain = [c for c in NUMERIC if c not in times]
    preprocessor = ColumnTransformer([
        ('num_log', Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('log1p', FunctionTransformer(np.log1p, feature_names_out='one-to-one')),
            ('scaler', StandardScaler())]), times),
        ('num_plain', Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())]), plain),
        ('cat', Pipeline([
            ('imputer', SimpleImputer(strategy='most_frequent')),
            ('onehot', OneHotEncoder(handle_unknown='ignore', drop='first',
                                     sparse_output=False))]), CATEGORICAL),
    ])
    model = DummyRegressor(strategy='mean') if dummy else LinearSVR(
        loss='epsilon_insensitive', max_iter=1_000_000, random_state=42, tol=1e-4)
    return Pipeline([('preprocesamiento', preprocessor), ('modelo', model)])
```

Cada fold interno ajusta de nuevo imputadores, escaladores y vocabulario categórico. La validación y el test solo se transforman con lo aprendido en entrenamiento. Las categorías no vistas se codifican como ceros mediante `handle_unknown='ignore'`.

Con la separación, los folds y el pipeline ya documentados, el capítulo pasa al modelo que se usa como referencia. Las decisiones de esta sección se mantienen fijas en todos los experimentos lineales.

## Modelos lineales

Esta sección detalla la implementación de los modelos lineales y la comparación de estrategias de búsqueda. Primero se describe cómo se entrena el SVM epsilon-sensible y el modelo Dummy que sirve de comparación; después se presentan las cinco estrategias de hiperparámetros, las métricas en validación y test, los errores, los intervalos, la curva de aprendizaje, los coeficientes y el simulador. El objetivo no es solo reportar un resultado, sino dejar explícito cómo se obtuvo y qué límites tiene.

### Pipeline y parametrización

Usando el pipeline descrito anteriormente, se entrenó un **LinearSVR** con pérdida epsilon-insensible. Este modelo busca una función lineal en el espacio transformado y tolera errores menores que `epsilon` sin penalizarlos. El ajuste final emplea `C = 0,2438`, `epsilon = 0,5130`, `max_iter = 1.000.000`, `tol = 1e-4` y semilla 42. Como referencia se entrenó un **DummyRegressor** que predice la media aprendida en entrenamiento; no usa las predictoras y permite medir cuánto aporta el SVM más allá de una respuesta trivial. Todo el preprocesamiento se ajusta dentro de cada fold.

### Búsqueda de hiperparámetros

Los valores finales de `C` y `epsilon` no se fijaron a mano. Esta sección explica cómo se eligieron y qué estrategias compitieron para encontrarlos.

La búsqueda compara cinco estrategias sobre el mismo espacio de hiperparámetros:

- **Grid Search:** recorre de forma exhaustiva una grilla fija de `C` y `epsilon` (48 combinaciones en este proyecto). Es la referencia determinista y cubre todos los puntos definidos.
- **Random Search:** muestrea combinaciones al azar dentro de los mismos rangos. No garantiza cubrir la grilla, pero explora el espacio con menos ajustes y puede encontrar buenas zonas rápidamente.
- **Optuna/TPE:** búsqueda bayesiana que modela la relación entre hiperparámetros y RMSE y propone nuevas combinaciones donde espera mejorar. Aprende de los intentos anteriores en lugar de recorrer una lista fija.
- **Genética DEAP:** mantiene una población de configuraciones y la evoluciona con selección, cruce y mutación. Conserva las mejores soluciones y explora variantes alrededor de ellas.
- **Successive Halving:** evalúa muchos candidatos con poca fidelidad y elimina por rondas los de peor desempeño, reservando más evaluaciones para los prometedores.

El espacio de Grid conserva `C ∈ {0,01; 0,03; 0,1; 0,3; 1; 10}` y `epsilon ∈ {0; 0,05; 0,1; 0,2; 0,3; 0,5; 0,75; 1}`. Cada fold externo elige método y parámetros por **menor RMSE interno**; en Successive Halving solo compiten las configuraciones que alcanzan la fidelidad completa. El ajuste final repite la comparación sobre todo train y el test no participa en la selección.

La siguiente tabla resume la búsqueda final sobre todo el entrenamiento. Los tiempos son de pared y corresponden a la búsqueda en el ajuste final; no se suman con el refit ni con la inferencia.

| Método | Configuración elegida | RMSE interno | Desv. | Configuraciones | Ajustes | Tiempo (s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Grid Search | C = 0,3; ε = 0,5 | 0,821690 | 0,045407 | 48 | 240 | 15,474 |
| Random Search | C = 3,040140; ε = 0,631664 | 0,825022 | 0,045259 | 16 | 80 | 2,765 |
| Bayesiana TPE | C = 0,243800; ε = 0,512986 | **0,821073** | 0,046356 | 20 | 100 | 3,221 |
| Genética DEAP | C = 0,890540; ε = 0,544941 | 0,823890 | 0,048360 | 16 | 80 | 2,786 |
| Successive Halving | C = 3,040140; ε = 0,631664 | 0,825022 | 0,045259 | 28 (4 completas) | 140 | 3,697 |

El método ganador en el ajuste final fue **Optuna/TPE**, con `C = 0,2438` y `epsilon = 0,5130`. Su RMSE interno de selección fue **0,821073**, distinto de la media externa por fold (**0,824106**) porque corresponden a estimaciones y particiones diferentes. La selección por fold externo también alternó Grid, TPE, DEAP y Random: el método no se fija de antemano.

```python
def tune(frame):
    search = GridSearchCV(
        make_pipeline(), GRID, scoring='neg_root_mean_squared_error',
        cv=grouped_splits(frame), refit=True, n_jobs=4, error_score='raise')
    with warnings.catch_warnings():
        warnings.simplefilter('error', ConvergenceWarning)
        warnings.filterwarnings('ignore', message='Found unknown categories',
                                category=UserWarning)
        with joblib.parallel_backend('loky', inner_max_num_threads=1):
            search.fit(frame[FEATURES], frame[TARGET])
    return search
```

El bucle externo mantiene la selección dentro de cada entrenamiento y guarda predicciones OOF:

```python
for fold, (fit, val) in enumerate(grouped_splits(train), 1):
    fit_frame, val_frame = train.iloc[fit], train.iloc[val]
    search = tune(fit_frame)
    for name, col, model in [
            ('SVM lineal', 'svm', search.best_estimator_),
            ('Dummy media', 'dummy',
             make_pipeline(True).fit(fit_frame[FEATURES], fit_frame[TARGET]))]:
        pred = model.predict(val_frame[FEATURES])
        train.loc[val, col] = pred
        folds.append({'Modelo': name, 'Fold': fold,
                      **metrics(val_frame[TARGET], pred)})
```

```{figure} images/14_modelos_busqueda.jpg
:alt: Mapa de calor del RMSE medio de Grid Search para las combinaciones de C y epsilon.
:name: modelos-busqueda

Resultados de la búsqueda en train: RMSE medio de las 48 combinaciones de C y epsilon.
```

### Métricas frente a Dummy

Una vez elegida la configuración, el modelo se evalúa en los folds externos y en el test reservado. La comparación con Dummy permite separar el aporte de las predictoras del simple uso de la media.

| Evaluación | Modelo | n | RMSE | MAE | MAPE (%) | R² |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Validación (5 folds) | Dummy media | 1.309 | 1,1180 | 0,9624 | 37,2988 | −0,0035 |
| Validación (5 folds) | SVM lineal | 1.309 | 0,8241 | 0,6503 | 24,1574 | 0,4530 |
| Test reservado | Dummy media | 188 | 1,2561 | 1,1045 | 42,3145 | −0,0476 |
| Test reservado | SVM lineal | 188 | **0,9299** | **0,7581** | **29,6462** | **0,4258** |

En test, el SVM reduce el RMSE **25,97 %** y el MAPE **29,94 %** frente a Dummy. R² = 0,4258 no significa 42,58 % de predicciones correctas: describe la reducción del error cuadrático relativa a la media de la muestra. El MAE de 0,7581 es un error absoluto promedio y no un límite garantizado para cada estudiante.

La validación externa es más favorable que el test: RMSE medio **0,8241** y R² medio **0,4530**, frente a **0,9299** y **0,4258**. Ambas evaluaciones usan estudiantes separados; el test añade la generalización a un periodo posterior. Los RMSE por fold fueron 0,7697, 0,8948, 0,8414, 0,7942 y 0,8204.

```{figure} images/15_modelos_barras.jpg
:alt: Barras de RMSE y MAE para Dummy y SVM en validación y test.
:name: modelos-barras

Comparación de RMSE y MAE entre Dummy y SVM en validación y test.
```

```{figure} images/16_modelos_tabla.jpg
:alt: Tabla de estadísticos, intervalos y diagnósticos White y BDS para Dummy y SVM.
:name: modelos-tabla

Estadísticos y lectura de resultados, incluidos los p-valores de White y BDS.
```

Las columnas de White y BDS son diagnósticos exploratorios. En validación, White rechaza varianza constante (p = 4,988×10⁻¹⁹) y BDS rechaza IID (p = 2,993×10⁻³) para el SVM; en test no se detecta evidencia en contra (White p = 0,8178; BDS p = 0,5275). No rechazar no demuestra que los supuestos se cumplan. Los p de OOF reúnen cinco ajustes distintos y no son promedios de p por fold.

### Predicción, residuos y calibración

Las métricas resumen el error global, pero no muestran dónde se produce. Las siguientes figuras descomponen el desempeño punto a punto: predicción frente a realidad, residuos y calibración por intervalos de nota.

La diagonal del scatter representa coincidencia perfecta. Por encima de ella el modelo sobreestima; por debajo, subestima. LinearSVR no acota la salida y no se recortan las predicciones para evaluar. La nube dibuja una muestra reproducible de 3.000 de las 188 filas de test; las métricas usan todas.

En esta vista, la nube se reparte a ambos lados de la diagonal y mantiene una dispersión amplia. Eso indica que el modelo captura la tendencia general pero comete errores en los dos sentidos: algunas notas se sobreestiman y otras se subestiman, sin un sesgo único que se corrija con un desplazamiento constante. Para el proyecto, la lectura es que la predicción sirve como referencia poblacional y no como pronóstico individual preciso; la incertidumbre por estudiante sigue siendo alta.

```{figure} images/17_modelos_prediccion.jpg
:alt: Predicciones del SVM frente a notas reales con diagonal ideal.
:name: modelos-prediccion

Predicción frente a realidad en el test reservado.
```

El residuo se define como nota real menos predicción. Un valor positivo indica subestimación. El residuo medio del SVM es **0,1071**, una leve subestimación promedio. Ese promedio no prueba ausencia de sesgo en los extremos, pues errores opuestos pueden compensarse. La prueba de normalidad da p = 0,0092; Breusch–Pagan, p = 0,00018; y la asociación entre predicción y error absoluto es **−0,3587**.

La dispersión alrededor de cero no es uniforme. La asociación negativa entre predicción y error absoluto (**−0,3587**) indica que los errores tienden a ser mayores cuando el modelo predice notas bajas y menores cuando predice notas altas. Además, Breusch–Pagan rechaza varianza constante y la normalidad también se rechaza, de modo que la incertidumbre no es la misma en toda la escala. Para el proyecto, esto significa que la predicción es menos fiable justo en los casos de nota baja, que suelen ser los de mayor interés para una alerta temprana.

```{figure} images/18_modelos_residuos.jpg
:alt: Residuos del SVM frente a la nota predicha, con línea en cero.
:name: modelos-residuos

Residuos del SVM en el test; cero representa coincidencia.
```

La curva de calibración agrupa por nota real en nueve intervalos. El SVM reproduce más variación que Dummy, pero tiende a acercarse al centro: sobreestima notas bajas y subestima notas altas. El resumen usa todas las filas y los tamaños de intervalo pueden ser distintos.

Ese comportamiento es una regresión hacia la media: el modelo evita los extremos y concentra sus predicciones en la zona central. La consecuencia práctica es que puede pasar por alto a estudiantes con notas muy bajas o muy altas, y que sus salidas no deben interpretarse como una estimación calibrada de la nota individual. Para el proyecto, refuerza la idea de usar el modelo como apoyo descriptivo y no como un clasificador de riesgo.

```{figure} images/19_modelos_calibracion.jpg
:alt: Nota predicha media de SVM y Dummy por intervalos de nota real.
:name: modelos-calibracion

Predicción media a lo largo de la escala de nota real.
```

### Intervalos bootstrap

Además de las métricas puntuales, interesa conocer cuánto pueden variar al remuestrear la muestra de test. Los intervalos bootstrap acotan esa variabilidad y ayudan a distinguir un resultado estable de uno que depende de pocas observaciones.

Los intervalos del 95 % remuestrean **1.000 veces por estudiante** en el test: los registros de una misma persona se remuestrean juntos. Para el SVM, RMSE **[0,8416; 1,0175]**, MAPE **[23,9972 %; 36,4560 %]** y R² **[0,3185; 0,5079]**. Describen esta muestra y no sustituyen una evaluación externa ni constituyen intervalos de predicción individual.

La amplitud del intervalo de RMSE (aproximadamente 0,18 puntos) muestra que la magnitud exacta del error depende de la muestra remuestreada. El límite superior (1,0175) sigue por debajo del RMSE de Dummy (1,2561), de modo que la ventaja frente a la media se mantiene en todo el intervalo; sin embargo, R² puede bajar hasta 0,3185, lo que deja una fracción importante de variación sin explicar. Para el proyecto, conviene reportar el rango y no solo el valor puntual: la conclusión cualitativa es estable, pero la precisión numérica es limitada.

```{figure} images/20_modelos_intervalos.jpg
:alt: Intervalos bootstrap del 95 por ciento para RMSE, MAPE y R cuadrado del SVM.
:name: modelos-intervalos

Intervalos bootstrap del 95 % en el test reservado.
```

### Curva de aprendizaje

Otra pregunta relevante es si el modelo se beneficiaría de más datos. La curva de aprendizaje responde cómo cambia el error al aumentar el tamaño de entrenamiento, manteniendo grupos completos y seleccionando parámetros solo dentro de cada subconjunto.

La curva usa grupos completos y parámetros seleccionados solo dentro de cada subconjunto. Con **1.047 filas de entrenamiento por fold**, el RMSE de entrenamiento es **0,7970** y el de validación **0,8241**. La brecha interna es pequeña y la validación cambia poco después de los tamaños iniciales. Esto sugiere ganancias marginales limitadas al añadir filas bajo este procedimiento, no que más estudiantes reales sean innecesarios.

La lectura práctica es que el límite principal no parece ser la cantidad de filas de entrenamiento, sino la información contenida en las predictoras y la forma del modelo. Añadir más registros parecidos probablemente no reduciría mucho el error. Además, la validación interna (0,8241) es más optimista que el test (0,9299), así que la curva describe el comportamiento dentro de los folds y no garantiza el mismo nivel en un periodo nuevo. Para el proyecto, esto sugiere priorizar nuevas variables o familias de modelos antes que ampliar la muestra.

```{figure} images/21_modelos_aprendizaje.jpg
:alt: Curva de aprendizaje con RMSE de entrenamiento y validación por tamaño de ajuste.
:name: modelos-aprendizaje

Curva de aprendizaje del modelo lineal con grupos completos.
```

### Coeficientes y reporte completo

Después de evaluar el error, conviene revisar qué términos usa el modelo. Los coeficientes permiten inspeccionar la dirección y la magnitud de cada contribución en el espacio transformado, aunque no deben leerse como efectos causales.

El gráfico conserva los doce coeficientes de mayor magnitud en el espacio transformado. No es un ranking causal ni una prueba de significancia. Numéricas estandarizadas y categorías one-hot tienen interpretaciones distintas, y la redundancia entre dominios, avance y variables institucionales permite redistribuir señales entre términos.

```{figure} images/22_modelos_coeficientes.jpg
:alt: Doce coeficientes de mayor magnitud del SVM en el espacio transformado.
:name: modelos-coeficientes

Doce coeficientes de mayor magnitud del SVM.
```

| Variable / término | β |
| --- | ---: |
| Intercepto (β₀) | 1,7552 |
| `Mat_Curso_Asignatura_Relacionada_MAT1100` | 0,7894 |
| `Categoria_temas_final_4 Temas Parcial 2 Cálculo I` | 0,6594 |
| `Categoria_temas_final_3 Temas Parcial 1 Cálculo I` | 0,6416 |
| `cumplimiento_temas_No alcanzo meta` | 0,5508 |
| `Categoria_temas_inicial_1 Geometría` | 0,5383 |
| `programa_en_matricula_Arquitectura` | 0,5383 |
| `division_en_matricula_Escuela Arquitectura Urb y Dis` | 0,5383 |
| `num_plain__Icfes_nuevo` | 0,5008 |
| `Categoria_temas_final_3 Gráficos y funciones` | −0,4602 |
| `Mat_Curso_Asignatura_Relacionada_MAT1101` | 0,4517 |
| `division_en_matricula_Escuela de Negocios` | 0,4517 |

Saber 11 global tiene coeficiente aproximado **0,5008**, mientras Saber 11 matemáticas tiene **−0,1604** aunque su correlación marginal con la nota sea positiva (ρ = 0,428). Ambas variables están correlacionadas (ρ = 0,835). El término «No alcanzó meta» es positivo en este ajuste, pero no se puede concluir que incumplir una meta mejore la nota: la categoría final, los dominios, el programa y las demás variables condicionan esa lectura.

En conjunto, el modelo concentra buena parte de su señal en la asignatura relacionada, en las categorías de temas finales y en el cumplimiento de la meta. Esa concentración es coherente con el EDA, pero también muestra una dependencia de variables correlacionadas: por eso un coeficiente puede tener signo contrario a su asociación marginal. Para el proyecto, el reporte sirve para describir qué información usa el modelo, no para atribuir efectos independientes a cada variable ni para diseñar intervenciones.

Los coeficientes se extraen del pipeline final y se ordenan por magnitud absoluta; las referencias quedan al final con β = 0:

```python
names = final.best_estimator_.named_steps['preprocesamiento'].get_feature_names_out()
coefficients = final.best_estimator_.named_steps['modelo'].coef_
pd.DataFrame({'Variable': names, 'Coeficiente': coefficients}).to_csv(
    OUTPUT / 'coefficients.csv', index=False)
```

LinearSVR no calcula p-valores, errores estándar ni pruebas t para sus coeficientes. Asignarle valores de OLS describiría otro modelo. El reporte completo incluye intercepto, todos los términos estimados y las referencias; el tablero permite descargarlo como CSV. La figura siguiente muestra el panel completo.

```{figure} images/23_modelos_reporte.jpg
:alt: Reporte completo de coeficientes del SVM con explicación de lectura y botón de descarga.
:name: modelos-reporte

Reporte completo de coeficientes (β) y disponibilidad de p-valores.
```

### Ejemplo de predicción

El análisis anterior describe el modelo en conjunto. El simulador permite ver cómo se aplica el pipeline guardado a un registro concreto y qué precauciones acompañan esa salida.

El simulador carga un registro válido de ejemplo y ejecuta el mismo pipeline guardado. En la captura se modifica únicamente el tiempo total de trabajo; el pipeline devuelve **3,065**. No es una nota observada ni un resultado garantizado. El MAE global de 0,758 describe el error medio en el test y no convierte esa salida en un intervalo individual «3,065 ± 0,758».

El ejemplo confirma que el pipeline guardado reproduce una predicción coherente y que las transformaciones se aplican igual que en la evaluación. Su valor para el proyecto es demostrativo: permite inspeccionar el efecto de cambiar una característica, pero no sustituye una validación individual ni debe usarse para tomar decisiones académicas sobre una persona.

El avance se calcula como dominio final − inicial; no acepta una entrada independiente que contradiga esa identidad. Los dominios son necesarios para comprobar coherencia, y los tiempos cero con avance positivo se rechazan. Los campos numéricos ausentes permitidos se imputan con las medianas aprendidas. Programa, asignatura y división deben corresponder a una combinación observada en train.

```{figure} images/24_modelos_simulador.jpg
:alt: Formulario del simulador con la nota predicha 3,065 para el ejemplo.
:name: modelos-simulador

Formulario del ejemplo y predicción del pipeline guardado.
```

### Conclusión

Con las métricas, los errores, la estabilidad y los coeficientes revisados, la conclusión integra la evidencia y fija el papel de este modelo en el resto del proyecto.

El SVM supera a Dummy y aporta una referencia predictiva parcial, con capacidad menor en test que en validación interna. La mejora del RMSE frente a Dummy es **25,97 %** y la del MAPE, **29,94 %**. Conviene distinguir esas cifras relativas de las cantidades absolutas: el RMSE pasa de **1,2561** a **0,9299** puntos de nota y el MAE de **1,1045** a **0,7581**; el porcentaje indica cuánto se reduce el error respecto a Dummy, no que la nota o el error bajen 25,97 puntos. Los puntos describen el error en la escala académica; los porcentajes dependen de la referencia y no son intercambiables entre métricas.

Para esta sección, el SVM con la búsqueda anidada fue el mejor resultado y se usará como base de comparación con las demás familias de modelos en etapas posteriores. Los gráficos muestran dispersión, regresión hacia el centro, errores de variabilidad no uniforme y algunas predicciones fuera de escala. La conclusión es mantenerlo como referencia y evaluar su estabilidad por estudiante, en el test reservado y en otros periodos antes de un uso operativo.

```{figure} images/25_modelos_conclusion.jpg
:alt: Tarjeta de conclusión del modelo lineal con métricas y diagnósticos.
:name: modelos-conclusion

Conclusión de la página de modelos lineales.
```

## Cómo trasladar la lectura a un filtro

Las cifras anteriores corresponden a la vista general. Al filtrar por programa o asignatura, el tablero evalúa el mismo modelo sobre un subconjunto; la siguiente sección explica cómo leer ese cambio sin interpretarlo como un modelo distinto.

Al elegir programa o asignatura cambian tamaño, distribuciones, asociaciones y errores del grupo seleccionado. El modelo y sus parámetros se mantienen: los filtros evalúan el modelo global sobre un subconjunto, no entrenan modelos independientes. Conviene leer primero el número de filas, después MAE/RMSE y finalmente R² junto con la variación de la nota. Un R² menor puede reflejar que el grupo tenga notas más homogéneas y no necesariamente un aumento equivalente del error absoluto. Con menos de 30 filas el tablero señala lectura inestable; con una sola fila o nota constante no calcula R².

Con esta base metodológica y el desempeño del modelo lineal documentados, los capítulos siguientes pueden comparar otras familias con el mismo criterio.

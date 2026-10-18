# Decision Tree · regresión E3 · 18 de octubre de 2026

Se incorpora un árbol CART a **Modelos clásicos**. Predice la nota del primer
parcial mediante cortes binarios y medias de las hojas. Implementación:
`evaluar_decision_tree_e3.py`, con `sklearn.tree.DecisionTreeRegressor`,
criterio `squared_error` y semilla 42.
[Documentación oficial](https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeRegressor.html).

## Preparación y evaluación

Datos reales de `Data/Datos_Brutos.csv`, con las reglas E3 y sin aumentación.
1.309 registros de train, 1.293 estudiantes; 188 registros del test temporal
202530, sin estudiantes compartidos. No se usan IDs, periodo ni `nota_final`
como predictores; los outliers válidos se conservan.

Mediana para numéricas; moda y one-hot completo para categorías, con categorías
desconocidas codificadas en ceros. Sin log1p ni escalado. La preparación se
aprende en cada fit. Esta representación evita el orden artificial de los
códigos ordinales en categorías nominales, aunque los cortes one-hot pueden
necesitar más niveles para agrupar categorías.

Los cinco folds externos son idénticos a los del SVM. Cada búsqueda utiliza
cinco folds internos por estudiante, scoring RMSE y 72 combinaciones:

| Parámetro | Valores |
| --- | --- |
| max_depth | 2, 3, 4, 6, 8, None |
| min_samples_leaf | 2, 5, 10, 20 |
| ccp_alpha | 0, 0.001, 0.01 |

Se realizaron 2.160 ajustes internos y seis refits separados; GridSearchCV usa
`refit=False`, cuatro procesos loky y un hilo interno por proceso. Cada árbol
se ajusta de forma secuencial. Los pools disponibles del proceso principal
figuran en la evidencia; no se limitó globalmente su número de hilos.
La selección final se guardó en `seleccion_decision_tree_antes_test.json`
antes de evaluar el test. No se reentrenaron los otros modelos.

## Resultados

| Evaluación | RMSE | MAE | MAPE (%) | R² |
| --- | ---: | ---: | ---: | ---: |
| CV externa, media de cinco folds | 0.913228 | 0.725198 | 26.864919 | 0.328895 |
| Test temporal, 188 registros | 1.029797 | 0.843608 | 30.367095 | 0.295848 |

El grid final en train seleccionó profundidad 6, mínimo de 20 muestras por
hoja y `ccp_alpha=0`; RMSE interno 0.907126. Estas métricas internas se usan
para selección; la evaluación independiente es la CV externa y el test.
Las predicciones se conservan sin recorte; ninguna predicción test queda fuera
de 0,5–5,0. Hay una categoría desconocida en test para Categoria_temas_inicial.

El árbol presenta mayor error que los clásicos existentes en los cinco folds;
su incorporación no cambia el modelo inicialmente mostrado, elegido por CV.
No se amplió el grid después de consultar test.

La comparación clásica muestra seis clásicos más SVM, sin Dummy. Friedman
usa 35 RMSE, χ²=17.485714, gl=6, p asintótico=0.00765454. Rechazo global
exploratorio: no identifica diferencias entre pares ni un ganador. Los cinco
folds y sus entrenamientos solapados limitan la interpretación del p-valor.
Test y subgrupos son descriptivos. Bootstrap por estudiante: 1.000 réplicas
pareadas, semilla 42, incluye al árbol; sin ajuste múltiple.
El inventario de Originales y sus familias de contrastes se conservan.

## Artefactos y reproducción

Resultados canónicos en `resultados/e3/clasicos/`: `decision_tree.joblib`,
`grid_decision_tree.csv`, grids por fold/final, selección previa a test,
columnas nuevas en predicciones train/test, cinco filas en fold_metrics.csv y
la entrada en comparacion.json. No se modifican CSV fuente ni notebooks.

Desde la raíz, con los datos privados locales y los resultados E3 existentes:

```powershell
.\Precalculo\venv\Scripts\python.exe .\Precalculo\evaluar_decision_tree_e3.py
.\Precalculo\venv\Scripts\python.exe .\Dash\run_measured.py .\Dash\prepare_data.py
.\Precalculo\venv\Scripts\python.exe .\Dash\run_measured.py --tests
```

El paquete público incluye el pipeline y resultados derivados sin IDs;
no incluye el CSV bruto. La sección ofrece documentación/grilla, tablas CV/test,
cuatro barras por métrica, rangos/Friedman, bootstrap, diagnósticos, filtros y
simulador del pipeline guardado.

Los tiempos se registraron con `perf_counter()` antes de ejecutar:
[registro central](../TIEMPOS_EJECUCION.md), ejecución
`20261018_095829_5b05000d`, con metadata y eventos crudos en `../tiempos/`.
Total directo del experimento 16.725403 s, incluida E/S y validaciones.
No se suma con las etapas ni se interpreta como latencia de una consulta.
No se añaden componentes de tiempos al dashboard.

---
title: Reproducibilidad y bibliografía
description: Entorno, semillas, orden de ejecución, scripts de este informe, tabla maestra de experimentos y referencias.
---

(sec-reproducibilidad)=
# Reproducibilidad y bibliografía

Este capítulo reúne lo necesario para reconstruir cada cifra: el entorno, las semillas, el orden de ejecución del análisis, los scripts propios de este informe, la tabla maestra de experimentos y las referencias. Los resultados costosos se entregan **precalculados y versionados** junto con el código que los genera (§9.2 de la guía): construir el libro no ejecuta modelos ni requiere los datos privados.

(sec-entorno)=
## Entorno

:::{table} Entorno compartido `Precalculo/venv/` (versiones verificadas el 24 de octubre de 2026).
:label: tab-entorno

| Componente | Versión |
| --- | --- |
| Python | 3.12.14 (`.python-version`) |
| scikit-learn | 1.9.1 |
| NumPy / pandas / SciPy | 2.3.5 / 3.0.1 / 1.18.1 |
| XGBoost | 3.4.1 |
| Optuna / DEAP | 5.0.0 / 1.4 |
| statsmodels / joblib | 0.15.0 / 1.6.0 |
| Dash / Plotly | 4.4.1 / 7.1.0 |
| pytest | 8.3.3 |
| Jupyter Book | 2.1.6 (MyST) |
| Hardware de las ejecuciones | CPU, sin GPU; búsquedas con 4 procesos de un hilo |
:::

Las dependencias del dashboard están fijadas en `Dash/requirements.txt`; las del análisis, en `Precalculo/requirements*.txt`. No se crea otro entorno: desde la raíz se usa `Precalculo\venv\Scripts\python.exe`.

(sec-semillas)=
## Semillas y aleatoriedad

- **Semilla global 42:** particiones auxiliares, modelos con aleatoriedad (`random_state`), Random Search, Halving, DEAP, TPE (`TPESampler(seed)`) y el bootstrap y las permutaciones de `analisis/pruebas_r3.py`.
- **20261020:** bootstrap del contraste por estudiante del dashboard (`Dash/student_dm.py`).
- **`GroupKFold`** es determinista: con el mismo orden de filas produce los mismos cinco folds para todos los modelos.
- El MCS enumera los 3.125 remuestreos de cinco folds: no usa semilla.

(sec-orden-ejecucion)=
## Orden de ejecución del análisis

Desde `Precalculo/`, con semilla 42 (detalle en `README.md` y `Precalculo/README_E3.md`):

1. `entregable3.py`: partición (test 202530), SVM base y exportaciones canónicas.
2. `modelos_clasicos.py` y `evaluar_decision_tree_e3.py`: clásicos y árbol sobre los mismos folds.
3. `evaluar_busquedas_e3.py` y `activar_busqueda_e3.py <run_id>`: cinco estrategias para SVM y clásicos (ejecución activa `20261018_102325_af643f83`).
4. `evaluar_originales_busquedas_e3.py`: modelos originales con las cinco estrategias (ejecución activa `20261020_153034_consolidada`).
5. `Dash/prepare_data.py` y `prepare_originals.py`: caché verificada del dashboard.

Estos pasos **reentrenan** y deben registrar sus tiempos en `TIEMPOS_EJECUCION.md`. Este informe no los ejecutó.

(sec-scripts-informe)=
## Scripts de este informe

Desde `jbook_dashboard_e4_final/`, con el entorno compartido. Ninguno entrena ni ejecuta `predict`:

```bash
../Precalculo/venv/Scripts/python.exe analisis/tabla_mejores_combinaciones.py
../Precalculo/venv/Scripts/python.exe analisis/pruebas_r3.py
../Precalculo/venv/Scripts/python.exe analisis/diagnostico_modelos.py
../Precalculo/venv/Scripts/python.exe analisis/tabla_maestra_experimentos.py
../Precalculo/venv/Scripts/python.exe analisis/matriz_novedad.py
../Precalculo/venv/Scripts/python.exe analisis/tablas_md.py
../Precalculo/venv/Scripts/python.exe analisis/manifiesto.py
../Precalculo/venv/Scripts/python.exe -m pytest analisis -q
./build.sh
```

`busqueda_literatura.py` y `bibliografia.py` consultan servicios externos (OpenAlex, arXiv, Semantic Scholar, Crossref); sus resultados quedan guardados y **no** deben volver a ejecutarse sin registrar la nueva fecha, porque los conteos cambian con el tiempo. `pruebas_r3.py` y `tabla_mejores_combinaciones.py` leen las particiones privadas en memoria para agrupar por estudiante; solo exportan agregados. `source_manifest.json` registra el SHA-256 de cada archivo copiado (con su origen) y de cada capítulo, figura y salida.

(sec-tabla-maestra)=
## Tabla maestra de experimentos

`analisis/salidas/tabla_maestra_experimentos.csv` ([descargar](analisis/salidas/tabla_maestra_experimentos.csv)) une 76 combinaciones modelo × método de búsqueda —35 de los 7 modelos base, 15 de los 3 originales y 26 de los otros 6 modelos de la pestaña Originales— con su RMSE interno, configuraciones, ajustes, tiempos de búsqueda, hiperparámetros, semilla y ejecución, más 16 filas de «procedimiento anidado» con las métricas del bucle externo. Las métricas externas pertenecen al procedimiento y no a un método aislado, porque cada fold externo eligió su propio método. Como el problema es de regresión, no hay técnicas de balanceo y el universo base es de 35 combinaciones, no 140. La {numref}`tab-maestra-extracto` muestra las filas de procedimiento.

```{include} analisis/tablas/maestra_extracto.md
```

Los tiempos de cada combinación provienen del registro central; las combinaciones sin evento registrado figurarían como «No medido» (en esta tabla no hay ninguna). El tiempo de la etapa GPR del híbrido se registró aparte (CPU acumulada de proceso) y no se suma a los tiempos por candidato.

(sec-privacidad)=
## Privacidad y publicación

La fuente `Datos_Brutos.csv` contiene nombres y correos y nunca se publica. El repositorio público contiene datos derivados sin identificadores ni `nota_final`, los resultados agregados, este libro y sus scripts. Las salidas de `analisis/salidas/` son agregados por modelo, fold o prueba; ninguna contiene identificadores de estudiante.

(sec-referencias)=
## Referencias

Referencias metodológicas sugeridas por la guía: comparación de clasificadores y regresores {cite:p}`demsar2006,benavoli2017,dietterich1998`, áreas bajo la curva {cite:p}`delong1988`, error de generalización {cite:p}`nadeau2003`, capacidad predictiva {cite:p}`diebold1995,harvey1997,giacomini2006,clark2007`, conjuntos de confianza y *data snooping* {cite:p}`hansen2011,hansen2005`, bootstrap estacionario {cite:p}`politis1994`, tamaños del efecto {cite:p}`romano2006`, interpretabilidad {cite:p}`lundberg2017` y optimización {cite:p}`akiba2019`. Todas las entradas con DOI se comprobaron en Crossref (`analisis/salidas/bibliografia_verificacion.csv`); las de JMLR, NeurIPS, actas sin registro y arXiv se citan con su URL estable.

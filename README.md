# Dashboard de Precálculo

Proyecto académico de Machine Learning de la Universidad del Norte. Explora los datos reales del nivelatorio de Precálculo en ALEK y compara modelos de regresión para predecir la **nota del primer parcial** (escala 0–5). El dashboard presenta la validación cruzada externa por estudiante, el contraste en un periodo temporal reservado, la comparación estadística de los modelos frente al SVM lineal y un simulador de predicción con el pipeline de Kernel Ridge RBF.

**Autores:** Rubiel Velásquez y Valentina Figueroa.

## Enlaces

- [Dashboard publicado en Render](https://precalculo-dashboard.onrender.com/).
- [Jupyter Book del proyecto: informe del dashboard](https://r041292.github.io/jbook_ml202630_2/): desarrollo, EDA, modelos lineales, clásicos y originales, y metodología.
- [Jupyter Book del entregable 1: datos, EDA y modelo base](https://r041292.github.io/jbook_ml202630_1/).

## Datos y protocolo

- **Fuente:** 1.527 registros de 1.506 estudiantes en seis periodos (2023–2025). Tras excluir las filas sin objetivo quedan 1.497 registros válidos y 15 variables predictoras. `nota_final` nunca se usa como predictora.
- **Partición:** el periodo 202530 (188 registros) se reserva como **test temporal**; el entrenamiento son 1.309 registros de 1.293 estudiantes de los periodos anteriores.
- **Validación:** `GroupKFold` anidado por estudiante, con cinco folds externos y cinco internos. El preprocesamiento se aprende dentro de cada fold y **el test nunca selecciona hiperparámetros ni modelos**.
- **Búsqueda de hiperparámetros:** Grid Search, Random Search, Optuna/TPE, DEAP (genética) y Successive Halving. Cada entrenamiento externo elige método y parámetros por RMSE interno, y el procedimiento se repite en todo el entrenamiento para el ajuste final. El tiempo no interviene en la selección.
- **Comparación estadística:** prueba de Friedman, post hoc de Nemenyi y Model Confidence Set, contraste tipo Diebold–Mariano por estudiante frente al SVM con corrección HLN (adaptado a este diseño) y tamaños de efecto. Con cinco folds dependientes la evidencia es **exploratoria**.

## Modelos

| Grupo | Modelos |
| --- | --- |
| Referencia | SVM lineal |
| Clásicos | KNN, Ridge, Lasso, Random Forest, XGBoost y Decision Tree |
| Originales (implementaciones propias y adaptaciones) | SVR RBF, Kernel Ridge RBF, TR-KRR RBF, DenseWeight-XGBoost, TCR-XGBoost, LinXGBoost, logicDT adaptado, GPR–XGBoost y RIM |
| Librerías y preentrenados (referencia, ocultos por defecto) | TabICLv2, TabPFN 2.5 (original y *fine-tuned*), CatBoost, TabFM, XGBoost ampliado, RaFFLE, DART-XGBoost, HRT-Boost, XBART y coPILOT |

Las pruebas estadísticas de Originales cubren 15 modelos: los nueve originales, el SVM y cinco clásicos. Los modelos de librería importada o preentrenados se conservan como referencia y quedan fuera de esas pruebas. Cada ficha enlaza el artículo en que se basa el modelo.

## Resultados vigentes

- **Kernel Ridge RBF** tiene el menor RMSE medio de validación cruzada entre los modelos originales (0,8010) y es el único modelo al que el dashboard le calcula SHAP (por permutaciones) y LIME. GPR–XGBoost obtiene el menor RMSE en el test (0,9029).
- Kernel Ridge RBF, GPR–XGBoost, TR-KRR y SVR RBF forman el conjunto del Model Confidence Set y no se distinguen entre sí. Frente al SVM mejoran en la prueba por estudiante, pero la prueba conservadora (t corregida) no confirma esa mejora: es una indicación exploratoria, no una demostración.
- En los modelos clásicos, ningún modelo supera significativamente al SVM lineal.
- Cifras, tablas y procedimiento completos: [capítulos del informe](https://r041292.github.io/jbook_ml202630_2/).

## Estructura del repositorio

| Carpeta o archivo | Contenido |
| --- | --- |
| `Dash/` | Aplicación Dash (`app.py`), módulos de modelos, estadística e interpretabilidad, y los datos preparados del tablero. |
| `Precalculo/` | Datos, scripts de entrenamiento y búsqueda, y resultados versionados de la revisión E3 ([README E3](Precalculo/README_E3.md)). |
| `jbook_dashboard/` | Capítulos Markdown del informe, figuras y el código que genera las tablas de los capítulos de clásicos y originales. |
| `TIEMPOS_EJECUCION.md` y `tiempos/` | Registro de los tiempos de búsqueda, entrenamiento e inferencia, con su evidencia. |
| `render.yaml` | Configuración del despliegue en Render. |
| `.github/workflows/` | Validación del dashboard y publicación del informe en GitHub Pages. |

## Ejecución local

El proyecto usa un único entorno virtual, `Precalculo/venv/`. Con él instalado y activo, desde la raíz del repositorio:

```bash
pip install -r Dash/requirements.txt
cd Dash
python app.py
```

El dashboard queda en `http://127.0.0.1:8050/`. Para construir el informe:

```bash
cd jbook_dashboard
BASE_URL=/jbook_ml202630_2 jupyter-book build --html --strict
```

## Tecnologías

Python, Dash, Plotly, scikit-learn, XGBoost, Optuna, DEAP, LIME y Jupyter Book.

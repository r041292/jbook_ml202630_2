---
title: Dashboard y despliegue
description: Arquitectura del dashboard de Precálculo, cobertura de los requisitos de la guía, decisiones de diseño, guía de despliegue en Render y URL pública.
---

(sec-dashboard)=
# Dashboard y despliegue

El dashboard convierte el análisis en una herramienta de consulta para una persona no experta: contexto del problema, exploración de los datos y uso de los modelos para predecir. Este capítulo describe su arquitectura, cómo cubre el contenido mínimo de §7.3 de la guía, las decisiones de diseño y la guía de despliegue en Render (§8).

:::{important} URL pública
**<https://precalculo-dashboard.onrender.com/>** · servicio web de Render (plan gratuito) con verificación de salud en `/healthz`. El 24 de octubre de 2026 la URL respondió: primero mostró la pantalla de arranque de Render («service waking up», el plan gratuito suspende el servicio tras un periodo de inactividad) y después cargó las tres secciones, incluida la pestaña «Modelos originales» con 16 modelos visibles y 11 de librería ocultos.
:::

(sec-arquitectura)=
## Arquitectura

El cálculo académico y la consulta interactiva están separados. `Precalculo/` produce los resultados canónicos; `Dash/prepare_*.py` los convierte en archivos livianos con hash verificado; `Dash/app.py` los sirve. El servidor **nunca entrena ni busca hiperparámetros**: carga una vez los artefactos al iniciar y responde a los filtros con cálculos sobre datos ya preparados ([](#fig-arquitectura)).

::::{figure}
:label: fig-arquitectura

```{mermaid}
flowchart LR
  subgraph P["Precalculo/ (local, datos privados)"]
    A["Datos_Brutos.csv"] --> B["entregable3.py<br/>particiones y SVM"]
    B --> C["busquedas_hiperparametros_e3.py<br/>evaluar_busquedas_e3.py<br/>7 modelos base"]
    B --> D["busquedas_originales_e3.py<br/>KRR centrado, TN-KRR, GPR–XGBoost"]
    C --> R["resultados/e3/<br/>OOF, métricas, .joblib"]
    D --> R
  end
  R --> E["Dash/prepare_data.py<br/>prepare_originals.py<br/>hashes SHA-256"]
  E --> F["Dash/data/<br/>sin IDs ni nota_final"]
  F --> G["Dash/app.py<br/>pestañas y callbacks"]
  G --> H["Render<br/>gunicorn app:server"]
  R --> I["jbook_dashboard_e4_final/<br/>este informe"]
  I --> J["GitHub Pages"]
```

Arquitectura de datos y publicación: el dashboard y el informe consumen los mismos resultados canónicos; los datos privados no salen del espacio local.
::::

| Componente | Responsabilidad |
| --- | --- |
| `Dash/app.py` | Layout con pestañas, filtros globales, callbacks y ruta `/healthz`. |
| `Dash/charts.py`, `eda_statistics.py` | Figuras y contrastes del EDA sobre el subgrupo filtrado. |
| `Dash/prediction.py` | Formulario generado desde el esquema, validación de reglas y predicción con el pipeline guardado. |
| `Dash/classic_models.py`, `original_models.py` | Fichas, tablas y diagnósticos de los modelos base y originales. |
| `Dash/classic_posthoc.py`, `student_dm.py`, `nemenyi.py` | Friedman, MCS, Nemenyi y contraste por estudiante. |
| `Dash/model_interpretation.py`, `lime_xgboost.py` | SHAP y LIME a partir de valores precalculados. |
| `Dash/deployment.py`, `validate_package.py` | Verificación de hashes de artefactos y fuentes públicas del paquete. |

(sec-cobertura)=
## Cobertura de los requisitos de §7.3

La {numref}`tab-cobertura` relaciona cada requisito con su implementación y con la captura que lo muestra.

:::{table} Requisitos del dashboard (§7.3), cómo se cubren y evidencia.
:label: tab-cobertura

| Sección | Requisito | Cómo lo cubre el dashboard | Evidencia |
| --- | --- | --- | --- |
| Contexto | Problema, relevancia y cifra de contexto citada | Pestaña «01 Introducción» con el nivelatorio, la fuente y las asignaturas | [](#fig-dash-intro) |
| Contexto | Pregunta de investigación y objetivos | Tarjeta de pregunta en la introducción | [](#fig-dash-intro) |
| Contexto | Datos: fuente, periodo, n, diccionario, objetivo y tarea | «Variables y contexto»: diccionario y reglas | [](#fig-diccionario), [](#fig-reglas) |
| Contexto | Diagrama de la metodología | «Split y CV»: test temporal, GroupKFold y pipeline | [](#fig-split-test), [](#fig-pipeline) |
| Contexto | Limitaciones, ética, autores | Textos de alcance y límites en cada pestaña; autores e institución en la introducción | [](#fig-dash-intro) |
| EDA | Filtros globales con callbacks | Programa y asignatura recalculan todas las figuras | [](#fig-eda-distribucion) |
| EDA | Distribución del objetivo | Histograma y cajas por asignatura | [](#fig-eda-distribucion) |
| EDA | Univariadas y explorador bivariado | Densidades, frecuencias y selector de variable numérica | [](#fig-eda-densidades), [](#fig-eda-asociaciones) |
| EDA | Correlación, faltantes y atípicos | Matriz de Spearman, faltantes por variable, extremos conservados | [](#fig-eda-asociaciones), [](#fig-eda-faltantes) |
| EDA | Frase de interpretación por gráfico | Lectura bajo cada tarjeta | [](#fig-eda-conclusion) |
| Modelos | Tabla de líderes (media ± DE, tiempos) | Tablas de clásicos y originales con media ± DE; tiempos de búsqueda y refit | [](#fig-dash-tabla) |
| Modelos | Predicción en vivo con validación de entradas | Simuladores con reglas de negocio que aplican el pipeline guardado (SVM y cada clásico) | [](#fig-dash-simulador) |
| Modelos | Explicación local SHAP | Waterfalls SHAP de casos del test para cada clásico y para el líder original, con comparación LIME en XGBoost y en el líder | [](#fig-shap-krr) |
| Modelos | Diagnóstico: real vs predicho, residuos | Dispersión, residuos, calibración e intervalos bootstrap | [](#fig-dash-residuos) |
| Modelos | Interpretabilidad global | Resumen SHAP del modelo seleccionado | [](#fig-shap-krr) |
| Modelos | Comparación estadística: tabla del MCS con el original | Friedman, MCS y contraste por estudiante en Originales | [](#tab-her-mcs15) |
| Modelos | Subsección de los modelos originales | Fichas con artículo, notación matemática, búsqueda, diagnósticos y contrastes frente al SVM | [](#tab-her-dm-cv) |
:::


(sec-capturas)=
## Capturas de las tres secciones

Las capturas son las del corte del 18 de octubre de 2026 (las mismas del informe previo), copiadas a `images/`; las cifras del EDA y del SVM no han cambiado desde entonces.

```{figure} images/01_introduccion.jpg
:alt: Página de contexto del dashboard con el problema, la fuente y las asignaturas.
:name: fig-dash-intro

Contexto: la página de introducción presenta el nivelatorio, la fuente de 1.527 registros, las cuatro asignaturas y la pregunta.
```

La [](#fig-dash-intro) responde a quien llega por primera vez qué se predice y con qué datos, antes de cualquier gráfico.

```{figure} images/16_modelos_tabla.jpg
:alt: Tabla de estadísticos del SVM y Dummy en validación y test con intervalos y diagnósticos White y BDS.
:name: fig-dash-tabla

Modelos: tabla de estadísticos con RMSE, MAE, MAPE y R² en validación y test, intervalos y p de White y BDS.
```

La [](#fig-dash-tabla) muestra el formato de las tablas de resultados: cada métrica aparece en validación y test, con su intervalo y los diagnósticos de residuos, para que la comparación no se limite a un valor puntual.

```{figure} images/18_modelos_residuos.jpg
:alt: Residuos del SVM frente a la nota predicha con línea en cero.
:name: fig-dash-residuos

Modelos: residuos (puntos de nota) frente a la predicción en el test.
```

La [](#fig-dash-residuos) es el diagnóstico de regresión que pide la guía: la dispersión es mayor en las predicciones bajas, el mismo patrón de los originales ({ref}`sec-evaluacion-originales`).

```{figure} images/24_modelos_simulador.jpg
:alt: Formulario del simulador con la predicción 3,065 para el ejemplo.
:name: fig-dash-simulador

Modelos: simulador con validación de entradas; el pipeline guardado devuelve 3,065 para el ejemplo.
```

En la [](#fig-dash-simulador) el avance se calcula como dominio final menos inicial, los tiempos cero con avance positivo se rechazan y programa, asignatura y división deben formar una combinación observada en train. La salida no es una nota garantizada: el MAE del test (0,758) describe el error medio, no un intervalo individual.

(sec-decisiones-diseno)=
## Decisiones de diseño e ingeniería

- **Navegación por la lógica del proyecto:** 01 Introducción, 02 EDA (Variables y contexto; Exploración interactiva) y 03 Modelos predictivos (Split y CV; Modelos lineales; Modelos clásicos; Modelos originales).
- **Rendimiento:** datos y modelos se cargan una vez; los desplegables difieren su contenido (`lazy_content.py`) y los gráficos se desmontan al cerrarlos; las respuestas JSON admiten gzip. Los *scatter* dibujan hasta 2.500 filas en EDA y 3.000 en modelos con semilla fija; las métricas usan todas las filas.
- **Robustez:** grupos vacíos con mensaje explícito, R² no definido cuando el grupo no lo permite, validación de entradas del simulador y verificación de hashes al arrancar.
- **Privacidad:** el paquete público no contiene la base bruta, identificadores ni `nota_final`.
- **Interpretación sin causalidad:** cada figura lleva una frase de lectura que distingue asociación de efecto.

(sec-despliegue)=
## Guía de despliegue en Render

El despliegue usa el `render.yaml` versionado en la raíz del repositorio:

```{literalinclude} analisis/codigo/render.yaml
:language: yaml
:caption: Configuración del servicio en Render (`render.yaml`).
:label: cod-render
```

**Pasos (§8.1).**

1. Verificar localmente que la aplicación arranca (`..\Precalculo\venv\Scripts\python.exe app.py` desde `Dash/`) y que `app.server` está expuesto.
2. Fijar dependencias exactas en `Dash/requirements.txt` (incluye `gunicorn==23.0.0` para Linux) y la versión de Python (`PYTHON_VERSION = 3.12.14`).
3. Exportar el paquete público a `RenderDeploy/` (checkout de `r041292/jbook_ml202630_2`, rama `main`) con los datos preparados y sus hashes; nunca la base bruta.
4. En Render, el *Blueprint* lee `render.yaml`: construye con `pip install -r Dash/requirements.txt` y arranca con `gunicorn --chdir Dash app:server` (un *worker*, dos hilos, *timeout* 120 s) y `healthCheckPath: /healthz`. Cada *commit* en `main` dispara un despliegue automático.
5. Revisar los registros de construcción y comprobar en la URL pública que las pestañas y los *callbacks* responden.

Cada *push* que toca `Dash/` o los resultados ejecuta además el *workflow* de validación del paquete:

```{literalinclude} analisis/codigo/dashboard-ci.yml
:language: yaml
:caption: Validación del paquete del dashboard en GitHub Actions (`.github/workflows/dashboard-ci.yml`).
:label: cod-dashboard-ci
```

**Plan gratuito de Render.** El servicio se suspende tras un periodo de inactividad y el primer acceso puede tardar en responder (se comprobó el 24 de octubre de 2026). Los hilos de BLAS se fijan en 1 para contener la memoria. Buenas prácticas: abrir la URL unos minutos antes de la sustentación, mantener los artefactos livianos y no entrenar nada en el servidor. El GPR–XGBoost (294 s de refit) **no** podría reentrenarse en el servidor; solo se cargan artefactos ya ajustados.

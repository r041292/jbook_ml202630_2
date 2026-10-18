---
title: Informe del desarrollo
description: Objetivos, arquitectura, decisiones de diseño y publicación del dashboard de Precálculo.
---

# Informe del desarrollo

El dashboard convierte el análisis del nivelatorio de Precálculo en una herramienta de consulta: permite explorar las características académicas de los registros reales, revisar la separación y la validación cruzada por estudiante y evaluar una primera predicción de la nota del primer parcial. Este Book documenta cómo se construyó, cómo se leen sus resultados y qué limitaciones deben acompañar esa lectura.

El flujo vigente es el **Entregable 3 (E3)**: trabaja exclusivamente con datos reales de ALEK. La preparación, la selección de variables, la validación agrupada y el modelo base se documentan en este mismo espacio de trabajo y se resumen en el [informe del entregable 1](https://r041292.github.io/jbook_ml202630_1/) solo como antecedente metodológico.

**Autores:** Rubiel Velasquez y Valentina Figueroa. **Institución:** Universidad del Norte. **Corte de resultados y capturas:** 18 de octubre de 2026.

[Abrir el dashboard interactivo en Render](https://precalculo-dashboard.onrender.com/).

::::{note}
La evidencia principal es una reducción del RMSE de **25,97 %** frente a predecir la media, con **R² = 0,4258** en el test temporal 202530. La utilidad predictiva es parcial. La evaluación externa usa estudiantes separados y un periodo posterior; no es una prueba de despliegue operativo.
::::

## Cómo está organizado el informe

| Capítulo | Pregunta que responde |
| --- | --- |
| [Informe del desarrollo](01_desarrollo.md) | ¿Cómo se transformó el análisis en un dashboard reproducible y publicable? |
| [Introducción y EDA](02_introduccion_eda.md) | ¿Qué describen los datos reales y qué muestran las páginas de contexto y exploración? |
| [Modelos](03_modelos.md) | ¿Cómo se separan los datos, cómo se valida el modelo y qué resultados producen los modelos lineales? |
| [Metodología y detalles adicionales](04_metodologia.md) | ¿Cómo se calculan las métricas, qué diagnósticos complementarios existen y qué falta validar? |

El recorrido completo sigue un mismo hilo: describir los datos, evaluar un modelo y explicar sus límites. La siguiente sección delimita el problema y la muestra que se usa en todo el informe.

## Problema académico y alcance

El nivelatorio busca fortalecer fundamentos matemáticos antes de cursar Álgebra y Trigonometría (MAT1011), Cálculo I (ANEC, MAT1100), Cálculo I (MAT1101) y Matemáticas Fundamentales (MAT4190). La pregunta del proyecto es en qué medida las mediciones de ALEK y la información académica disponible permiten anticipar la nota del primer parcial de la asignatura relacionada.

La fuente reúne seis periodos entre 2023 y 2025: 202310, 202330, 202410, 202430, 202510 y 202530. Contiene **1.527 registros de 1.506 estudiantes** y 31 columnas. Se excluyen **30 filas sin objetivo**; las **1.497 restantes** se reparten en **1.309 registros de train** (1.293 estudiantes, periodos 202310–202510) y **188 registros de test** (188 estudiantes, periodo 202530). No hay estudiantes compartidos ni filas purgadas por solapamiento. El esquema estandarizado conserva 17 columnas, pero el modelo utiliza **15 predictoras**: ocho numéricas y siete categóricas. `nota_final` queda fuera del entrenamiento y de las correlaciones por ser posterior al resultado que se intenta predecir.

El tablero describe datos y desempeño de un modelo global. Los filtros seleccionan subconjuntos para consultar su comportamiento; no crean modelos por programa ni por asignatura. El simulador ejecuta el mismo pipeline guardado que se evaluó en el análisis.

## Requerimientos implementados

La siguiente tabla relaciona cada necesidad del proyecto con la solución implementada en el tablero y con la evidencia que permite verificarla.

| Necesidad | Solución en el dashboard | Evidencia de verificación |
| --- | --- | --- |
| Contextualizar la investigación | Introducción, fuente, asignaturas y objetivo | Revisión del contenido y recursos locales |
| Documentar las variables | Diccionario, temporalidad y reglas de negocio | Esquema compartido con el análisis |
| Realizar el análisis exploratorio de datos (EDA) | Exploración de train válido con filtros, histogramas, densidades, cajas, asociaciones de Spearman, frecuencias categóricas y faltantes | Correspondencia de filas y estadísticas con `resultados/e3/eda.json`; exclusión de nota_final y conservación de extremos válidos |
| Compartir la metodología | Split y CV: test por periodo, GroupKFold anidado y flujo del pipeline | Mismos folds para todas las familias y sin estudiantes compartidos |
| Evaluar un modelo base | Dummy media y SVM lineal, validación y test | Métricas coincidentes con las exportaciones canónicas |
| Comparar estrategias de búsqueda | Grid Search, Random Search, Optuna/TPE, DEAP y Successive Halving con selección por RMSE interno | Presupuestos, configuraciones y tiempos registrados por fold |
| Mostrar errores y límites | Predicción frente a realidad, residuos, calibración, intervalos y diagnósticos White/BDS | Callbacks HTTP, estados vacíos y supuestos documentados |
| Hacer una predicción consistente | Validación de entradas e inferencia con el modelo guardado | Igualdad con las predicciones del pipeline |
| Publicar una ejecución estable | Paquete de datos preparados, Gunicorn y comprobaciones SHA-256 | Arranque del checkout mínimo y `/healthz` |

## Arquitectura y trazabilidad

En el espacio de trabajo, los procedimientos, notebooks, resultados y artefactos del análisis se encuentran en la carpeta `Precalculo/`. La carpeta `Dash/` consume desde allí los datos derivados y las exportaciones estructuradas, y prepara con ellos los archivos que utiliza la interfaz. Así se separan el cálculo académico y la consulta interactiva, manteniendo la trazabilidad con el código que produjo cada cifra. El servidor no ejecuta notebooks ni entrena un modelo cuando alguien modifica un filtro.

```text
Fuente original privada (Datos_Brutos.csv)
  → esquema, reglas de negocio y auditoría
  → separación temporal por estudiante (train 202310–202510 / test 202530)
  → EDA sobre train válido
  → GroupKFold anidado 5 × 5 y búsqueda de hiperparámetros
  → ajuste final y evaluación en el test reservado
  → exportaciones JSON/CSV y pipeline guardado
  → caché verificada de Dash
  → dashboard en Render + informe estático en GitHub Pages
```

| Componente | Responsabilidad |
| --- | --- |
| `Precalculo/entregable3.py` | Carga, reglas, particiones, pipeline SVM, búsqueda y exportaciones canónicas |
| `Precalculo/busquedas_hiperparametros_e3.py` | Grid, Random, TPE, DEAP y Successive Halving con selección anidada |
| `Precalculo/modelos_clasicos.py` y `evaluar_decision_tree_e3.py` | Modelos clásicos sobre los mismos folds externos |
| `Dash/app.py` | Pestañas, filtros, callbacks, métricas por grupo y ruta de salud |
| `Dash/charts.py` | Densidades y comparaciones visuales |
| `Dash/prediction.py` | Formulario, reglas de entrada, predicción y reporte de coeficientes |
| `Dash/prepare_data.py` | Reproducir pipeline y folds; también proveer constantes y funciones al servidor |
| `Dash/data/` | Train/test preparados, predicciones OOF, métricas, coeficientes y modelo ajustado |
| `Dash/deployment.py` | Verificar los artefactos y las fuentes públicas del paquete |
| `jbook_dashboard/` | Este informe: capítulos Markdown, capturas y configuración del Book |

La preparación comprueba las métricas del modelo contra `Precalculo/resultados/e3/modelos_lineales.json` con tolerancia de 10⁻¹⁰. El manifiesto registra hashes de las fuentes, los resultados y el modelo. El paquete público verifica todos sus artefactos antes de servir el tablero. Estos controles detectan cambios de archivos y caché desactualizada; no reemplazan una auditoría estadística ni constituyen una firma criptográfica de autoría.

## Decisiones de interfaz

Las decisiones de presentación buscan que el tablero se pueda leer sin perder el rigor del análisis. Esta sección describe esas elecciones y su alcance.

Se adoptó un fondo claro, tarjetas blancas, colores diferenciados por categoría y títulos que describen la pregunta de cada gráfico. La navegación sigue el razonamiento del proyecto: **01 Introducción**, **02 EDA** (Variables y contexto, Exploración interactiva) y **03 Modelos predictivos** (Split y CV, Modelos lineales, Modelos clásicos, Modelos originales). Este Book documenta las secciones hasta Modelos lineales; las familias clásicas y los modelos originales se conservan en el tablero y se incorporarán a una revisión posterior.

Los filtros de programa y asignatura se combinan. Los grupos sin registros tienen un mensaje explícito; R² se muestra como no definido cuando el grupo no permite calcularlo. Las leyendas permiten aislar categorías y Plotly conserva herramientas de zoom, hover y descarga PNG.

Para mantener fluidez, los scatter dibujan hasta 2.500 filas en EDA y 3.000 en modelos, con semilla fija. Las métricas, correlaciones, densidades y resúmenes se calculan con todas las filas disponibles del subconjunto. En este informe las capturas son estáticas: muestran la vista general del dashboard y el ejemplo de predicción descrito en el capítulo de Modelos.

```{figure} images/01_introduccion.jpg
:alt: Página de introducción del dashboard con contexto institucional, fuente, asignaturas y pregunta de investigación.
:name: desarrollo-introduccion

Introducción del tablero local, correspondiente a la versión de resultados preparada para Render.
```

## Verificación del desarrollo

La implementación se acompaña de verificaciones automáticas y de una revisión visual. Estas comprobaciones resumen qué se validó y con qué alcance.

La suite del dashboard verifica la concordancia con la fuente y las métricas del análisis, las reglas de negocio y la conservación de extremos válidos, los filtros, los callbacks HTTP, los recursos locales, los estados vacíos, la comparación entre familias, el reporte de coeficientes y la predicción. En el paquete público se repiten las pruebas funcionales que no dependen de la base bruta completa.

Un checkout construido exclusivamente con los archivos versionados arranca y responde 200 en inicio, `/healthz`, layout, dependencias de Dash, imagen y CSS. La alteración de un artefacto o una fuente pública es rechazada por el control de hashes. Las dependencias declaradas se resuelven como wheels de Linux x86_64 para Python 3.12. Esa comprobación no mide consumo de memoria ni equivale a una prueba de carga de Render.

La revisión visual comprobó las pestañas principales, los filtros, los títulos de métricas y el simulador. El reporte de β conserva todos los términos y referencias. Los p-valores no se inventan: LinearSVR no los calcula.

## Publicación y mantenimiento

La versión revisada se publica en dos destinos distintos: el tablero en Render y este informe en GitHub Pages. Esta sección describe ese proceso y las condiciones para actualizarlo.

El repositorio público es [r041292/jbook_ml202630_2](https://github.com/r041292/jbook_ml202630_2). El dashboard se despliega como servicio web en Render; este informe se construye como HTML estático para GitHub Pages. El checkout de publicación local está en `RenderDeploy/` y conserva la estructura `Dash/`, `Precalculo/` y `jbook_dashboard/`.

El servicio usa Python 3.12.14, Gunicorn, un worker y dos threads. Lee datos preparados y responde a la ruta `/healthz`. El repositorio versiona los datos derivados y el modelo con autorización expresa del responsable. La fuente bruta contiene datos personales y permanece fuera del paquete público. Los archivos de contexto, instrucciones, entornos virtuales y outputs del build también quedan fuera de Git.

El workflow de Pages construye únicamente los capítulos Markdown con Jupyter Book 2.1.6, conserva la ruta base del repositorio y publica el artefacto HTML. Cada cambio del informe requiere reconstruir, comprobar imágenes y enlaces, y revisar que las cifras sigan correspondiendo a la versión del dashboard. Si cambian datos o modelo, se regeneran los resultados, la caché, las capturas y las interpretaciones antes de publicar.

## Conclusión del desarrollo

El capítulo cierra con una síntesis del alcance conseguido y de lo que queda pendiente.

Se consiguió una consulta interactiva del flujo académico con correspondencia comprobada entre los resultados del análisis y el tablero. El principal aporte del desarrollo es hacer inspeccionables los datos, los errores y las decisiones metodológicas. La publicación facilita la revisión del proyecto; la evaluación por estudiante, la validación en otros periodos y la revisión de estabilidad siguen siendo trabajo pendiente antes de adoptar la predicción en un proceso académico real.

El siguiente capítulo entra en el contenido del tablero: primero el contexto y el análisis exploratorio, y después la metodología de modelos y sus resultados.

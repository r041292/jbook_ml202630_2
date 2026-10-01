---
title: Informe del desarrollo
description: Objetivos, arquitectura, decisiones de diseño y publicación del dashboard de Precálculo.
---

# Informe del desarrollo

El dashboard convierte el análisis del nivelatorio de Precálculo en una herramienta de consulta: permite explorar las características académicas, comparar la aumentación de datos y evaluar una primera predicción de la nota del primer parcial. Este Book documenta cómo se construyó, cómo se leen sus resultados y qué limitaciones deben acompañar esa lectura.

Su construcción se basa en la [primera entrega del proyecto](https://r041292.github.io/jbook_ml202630_1/), donde se documentaron la selección de la base de datos, la preparación y aumentación de la muestra, el análisis exploratorio de datos (EDA) y el modelo base. El dashboard lleva esos procedimientos y resultados a una interfaz interactiva, y este informe explica su desarrollo y su interpretación.

**Autores:** Rubiel Velasquez y Valentina Figueroa. **Institución:** Universidad del Norte. **Corte de resultados y capturas:** 1 de octubre de 2026.

[Abrir el dashboard interactivo en Render](https://precalculo-dashboard.onrender.com/).

::::{note}
La evidencia principal es una reducción del RMSE de **21,23 %** frente a predecir la media, con **R² = 0,3792** en el test aumentado. La utilidad predictiva es parcial y todavía requiere evaluación sobre estudiantes originales. Las 30.000 filas de trabajo incluyen variantes sintéticas; no representan 30.000 estudiantes.
::::

## Cómo está organizado el informe

| Capítulo | Pregunta que responde |
| --- | --- |
| [Informe del desarrollo](01_desarrollo.md) | ¿Cómo se transformó el análisis en un dashboard reproducible y publicable? |
| [Interpretaciones de resultados](02_interpretaciones.md) | ¿Qué muestra cada página del tablero y qué se puede concluir de sus gráficos? |
| [Metodología y detalles adicionales](03_metodologia.md) | ¿Cómo se calculan las métricas, qué análisis complementarios existen y qué falta validar? |

## Problema académico y alcance

El nivelatorio busca fortalecer fundamentos matemáticos antes de cursar Álgebra y Trigonometría (MAT1011), Cálculo I (ANEC, MAT1100), Cálculo I (MAT1101) y Matemáticas Fundamentales (MAT4190). La pregunta del proyecto es en qué medida las mediciones de ALEK y la información académica disponible permiten anticipar la nota del primer parcial de la asignatura relacionada.

La fuente reúne seis periodos entre 2023 y 2025: 202310, 202330, 202410, 202430, 202510 y 202530. Contiene 1.527 registros de 1.506 estudiantes y 31 columnas. Se excluyen 30 filas sin objetivo; las 1.497 restantes se separan por estudiante antes de generar variantes. El esquema estandarizado conserva 17 columnas, pero el modelo utiliza 15 predictoras: ocho numéricas y siete categóricas. `nota_final` queda fuera del entrenamiento y de las correlaciones por ser posterior al resultado que se intenta predecir.

El tablero describe datos y desempeño de un modelo global. Los filtros seleccionan subconjuntos para consultar su comportamiento; no crean modelos por programa ni por asignatura. El simulador ejecuta el mismo pipeline guardado que se evaluó en el análisis.

## Requerimientos implementados

| Necesidad | Solución en el dashboard | Evidencia de verificación |
| --- | --- | --- |
| Contextualizar la investigación | Introducción, fuente, asignaturas y objetivo | Revisión del contenido y recursos locales |
| Documentar las variables | Diccionario, temporalidad y reglas de negocio | Esquema compartido con el análisis |
| Explicar la aumentación | Comparación de dos técnicas, densidades, acumuladas y cinco semillas | Concordancia de puntajes con el notebook |
| Realizar el análisis exploratorio de datos (EDA) | Exploración de train válido con filtros, histogramas, densidades, cajas, asociaciones de Spearman, frecuencias categóricas y faltantes | Correspondencia de filas y estadísticas con el EDA de la primera entrega; exclusión de nota_final y conservación de extremos válidos |
| Evaluar un modelo base | Dummy media y SVM lineal, validación y test | Métricas coincidentes con exportaciones canónicas |
| Mostrar errores y límites | Predicción frente a realidad, residuos, calibración e intervalos | Callbacks HTTP y estados vacíos |
| Hacer una predicción consistente | Validación de entradas e inferencia con modelo guardado | Igualdad con predicciones del pipeline |
| Publicar una ejecución estable | Paquete de datos preparados, Gunicorn y comprobaciones SHA-256 | Arranque del checkout mínimo y `/healthz` |

## Arquitectura y trazabilidad

En la [primera entrega del proyecto](https://r041292.github.io/jbook_ml202630_1/) se establecieron las metodologías y los flujos de preparación, auditoría, separación por estudiante, aumentación, EDA y modelado que sustentan el dashboard. En el espacio de trabajo, esos procedimientos, notebooks y resultados se encuentran en la carpeta `Precalculo/`.

La carpeta `Dash/` consume desde `Precalculo/` las fuentes seleccionadas y las exportaciones estructuradas del análisis, y prepara con ellas los archivos que utiliza la interfaz. Así se separan el cálculo académico y la consulta interactiva, manteniendo la trazabilidad con la primera entrega. El servidor no ejecuta notebooks ni entrena un modelo cuando alguien modifica un filtro.

```text
Fuente original privada
  → esquema y auditoría
  → separación por estudiante
  → comparación de aumentación usando train
  → selección de perturbación local
  → EDA y modelo del notebook
  → exportaciones JSON y pipeline guardado
  → caché verificada de Dash
  → dashboard en Render + informe estático en GitHub Pages
```

| Componente | Responsabilidad |
| --- | --- |
| `Precalculo/` | Metodologías, flujos, notebooks y resultados de la primera entrega que alimentan el dashboard |
| `app.py` | Pestañas, filtros, callbacks, métricas por grupo y ruta de salud |
| `charts.py` | Densidades y comparación visual de originales y sintéticos |
| `prediction.py` | Formulario, reglas de entrada, predicción y reporte de coeficientes |
| `prepare_data.py` | Reproducir pipeline y folds; también proveer constantes y funciones al servidor |
| `data/` | Train/test preparados, predicciones OOF, métricas, coeficientes y modelo ajustado |
| `deployment.py` | Verificar los artefactos y las fuentes públicas del paquete |
| `assets/style.css` e `img.jpeg` | Presentación y recurso visual local |
| `render.yaml` | Configuración de ejecución Python/Gunicorn |
| `jbook_dashboard/` | Tres capítulos Markdown, capturas y configuración del Book |

La preparación comprueba las métricas del modelo contra `Precalculo/resultados/modelos_lineales.json` con tolerancia de 10⁻¹⁰. El manifiesto registra hashes de las fuentes y del modelo. El paquete público verifica todos sus artefactos antes de servir el tablero. Estos controles detectan cambios de archivos y caché desactualizada; no reemplazan una auditoría estadística ni constituyen una firma criptográfica de autoría.

## Decisiones de interfaz

Se adoptó un fondo claro, tarjetas blancas, colores diferenciados por categoría y títulos que describen la pregunta de cada gráfico. La navegación sigue el razonamiento del proyecto: contexto, datos y evaluación. Las explicaciones se colocan junto a las figuras; las tablas añaden la precisión numérica que una barra o una nube de puntos no puede mostrar por sí sola.

Los filtros de programa y asignatura se combinan. Los grupos sin registros tienen un mensaje explícito; R² se muestra como no definido cuando el grupo no permite calcularlo. Las leyendas permiten aislar categorías y Plotly conserva herramientas de zoom, hover y descarga PNG.

Para mantener fluidez, los scatter dibujan hasta 2.500 filas en EDA y 3.000 en modelos, con semilla fija. Las métricas, correlaciones, densidades y resúmenes se calculan con todas las filas disponibles del subconjunto. En este informe las capturas son estáticas: muestran la vista general del dashboard y el ejemplo de predicción descrito en el segundo capítulo.

```{figure} images/01_introduccion.jpg
:alt: Página de introducción del dashboard con contexto institucional, fuente, asignaturas y pregunta de investigación.
:name: desarrollo-introduccion

Introducción del tablero local, correspondiente a la versión de resultados preparada para Render.
```

## Verificación del desarrollo

Las nueve pruebas del dashboard verifican concordancia con la fuente y las métricas del notebook, reglas de negocio y conservación de extremos válidos, filtros, callbacks HTTP, assets, estados vacíos, comparación de aumentación, reporte de coeficientes y predicción. En el paquete público se repitieron ocho pruebas funcionales; la prueba que requiere los CSV fuente completos corresponde al espacio local privado.

Un checkout construido exclusivamente con los archivos versionados arrancó y respondió 200 en inicio, `/healthz`, layout, dependencias de Dash, imagen y CSS. La alteración de un artefacto o una fuente pública fue rechazada por el control de hashes. Las dependencias declaradas se resolvieron como wheels de Linux x86_64 para Python 3.12. Esa comprobación no mide consumo de memoria ni equivale a una prueba de carga de Render.

La revisión visual comprobó las pestañas principales, filtros, títulos de métricas y simulador. El reporte de β conserva todos los términos y referencias. Los p-valores no se inventan: LinearSVR no los calcula.

## Publicación y mantenimiento

El repositorio público es [r041292/jbook_ml202630_2](https://github.com/r041292/jbook_ml202630_2). El dashboard se despliega como servicio web en Render; este informe se construye como HTML estático para GitHub Pages. El checkout de publicación local está en `RenderDeploy/` y conserva la estructura `Dash/`, `Precalculo/` y `jbook_dashboard/`.

El servicio usa Python 3.12.14, Gunicorn, un worker y dos threads. Lee datos preparados y responde a la ruta `/healthz`. El repositorio versiona los datos derivados y el modelo con autorización expresa del responsable. La fuente bruta contiene datos personales y permanece fuera del paquete público. Los archivos de contexto, instrucciones, entornos virtuales y outputs del build también quedan fuera de Git.

El workflow de Pages construye únicamente los tres documentos Markdown con Jupyter Book 2.1.6, conserva la ruta base del repositorio y publica el artefacto HTML. Cada cambio del informe requiere reconstruir, comprobar imágenes/enlaces y revisar que las cifras sigan correspondiendo a la versión del dashboard. Si cambian datos o modelo, se regeneran los resultados, la caché, las capturas y las interpretaciones antes de publicar.

## Conclusión del desarrollo

Se consiguió una consulta interactiva del flujo académico con correspondencia comprobada entre los resultados del notebook y el tablero. El principal aporte del desarrollo es hacer inspeccionables los datos, los errores y las decisiones metodológicas. La publicación facilita la revisión del proyecto; la evaluación por estudiante, el test original y la validación temporal siguen siendo trabajo pendiente antes de adoptar la predicción en un proceso académico real.

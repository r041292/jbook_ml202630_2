# Contexto del dashboard de Precálculo

## Estado vigente · 2026-10-01

Despliegue preparado para https://github.com/r041292/jbook_ml202630_2 en `main`.
`../RenderDeploy/` es el checkout independiente de publicación: no incorpora el
historial anterior ni datos brutos con nombres, IDs o correos. `prepare_deployment.py`
verifica todas las fuentes contra el manifiesto local y exporta código, assets,
los ocho artefactos de `data/` y cinco fuentes públicas (introducción, comparación,
selección y resultados EDA/modelos). `deployment.py` verifica en ese paquete los
hashes de los ocho artefactos y las cinco fuentes públicas. La ejecución local
completa conserva la comprobación original de todas las fuentes. No se reentrena.
Se añadió `/healthz`, Gunicorn para Linux, Python 3.12.14 y `../render.yaml` con
un worker y dos threads, puerto de Render, timeout 120 y despliegue por commit.
Render debe usar raíz vacía para acceder a Dash y Precalculo; `.gitattributes`
conserva bytes para las comprobaciones SHA-256. README documenta Blueprint,
configuración manual, actualización y suspensión por inactividad del plan Free.
La publicación de GitHub no constituye todavía un despliegue en Render.
El repositorio destino se confirmó público. Tras el bloqueo inicial de la
revisión automática, el usuario autorizó explícitamente publicar train.csv.gz,
test.csv.gz, augmentation.csv.gz y model.joblib en ese repositorio público.
Los datos brutos con nombres/correos permanecen excluidos del paquete.
Validación del paquete: nueve pruebas locales pasan; ocho pruebas funcionales
también pasan importando exclusivamente el checkout público. `/healthz` responde
200; modificar un artefacto o una fuente pública provoca rechazo de integridad.
Las dependencias declaradas y Gunicorn se resolvieron y descargaron como wheels
compatibles con Linux x86_64/Python 3.12. El servidor Gunicorn no se ejecutó en
Windows; el arranque real en Linux y el consumo de memoria se validarán en Render.

Último ajuste editorial: «Reglas de negocio validadas» incluye introducción y
explicaciones numeradas de las tres condiciones. Aumentación incorpora una
introducción general y una explicación previa del propósito de la separación.
Después de las densidades numéricas se muestran siete distribuciones categóricas
completas con porcentajes, conteos al pasar el cursor y filtros combinados.
El título R² de la comparación de métricas usa superíndice HTML y color explícito
para mantenerlo visible. La tabla y el CSV de coeficientes ya no incluyen la
columna p-valor; permanece la explicación de la limitación en el texto.
El cierre de modelos se titula «Conclusión». Validación visual completada.
La inspección detectó que la barra flotante de Plotly se superponía al título
del panel R². Se reservó margen superior adicional y se separaron los títulos
de la barra, conservando las herramientas y la altura útil del gráfico.
Se verificaron en navegador los tres títulos (RMSE, MAE y R²), los encabezados
del reporte (variable/término, β y rol), las siete distribuciones categóricas
y las nuevas introducciones. Nueve pruebas pasan; la consola no reporta errores.
Se dejaron fuera de ejecución las instancias antiguas que compartían 8050 y se
confirmó una sola instancia actualizada. `preview_metricas.jpg` muestra R² visible
incluso con la barra flotante activa. Para reiniciar, detener primero el servidor
existente y evitar ejecutar varias instancias sobre el mismo puerto.

Revisión editorial y ampliación completada: títulos concretos, introducción ordenada,
comparación gráfica de originales/sintéticos, densidades, frecuencias categóricas,
cajas por dominio final, conclusión EDA y simulador de predicción.
`prepare_comparison.py` reproduce la alternativa 2 solo para gráficos usando los
originales preservados en el prefijo de train; no vuelve a dividir ni lee test,
ni escribe en Precalculo. Se verifican sus métricas contra las cinco semillas
del notebook (la primera para las curvas). El modelo principal conserva técnica 1.
La preparación también conserva el pipeline ajustado en `data/model.joblib`;
su hash se registra antes de cargarlo para el ejemplo. Los p-valores no están
definidos por LinearSVR: se mostrará el reporte completo de coeficientes con
esa limitación explícita, sin inventar inferencia OLS ni cambiar el modelo.
`prediction.py` añade formulario, validación de puntajes/dominios/tiempos y
compatibilidad programa-asignatura-división. El avance se calcula a partir de
los dominios. Reporta intercepto, todos los coeficientes y referencias categóricas.
`charts.py` calcula densidades KDE y funciones acumuladas para comparar los
originales con sintéticos de ambas alternativas; usa todos los valores disponibles.
Interfaz reorganizada: se retiró «Laboratorio de evidencia»; introducción en orden
punto de partida/contexto/pregunta; títulos concretos, necesidad de 20.000 filas
y alternativas con bullets. Aumentación ahora incorpora densidades/acumuladas
interactivas, resumen de comparación y cierre «Conclusión» con fidelidad/estabilidad.
EDA conserva todos los gráficos y suma nueve densidades, frecuencias de siete
variables categóricas, cajas por intervalos de dominio final y conclusiones con
tabla de evidencias/tratamientos. Reporte completo de β y descarga en Profundizar;
ejemplo de predicción en acordeón propio. Nueve pruebas pasan y la revisión visual está completada.
Se añadieron pruebas de correspondencia de las curvas de aumentación, reporte
completo de coeficientes sin p-valores inventados, igualdad del simulador con
predicciones test del pipeline guardado y rechazo de inconsistencias.
La primera ejecución ampliada pasó nueve pruebas. El simulador ignora cualquier
avance enviado por separado y lo deriva siempre de los dominios, incluso si se
manipula el valor del campo deshabilitado. README actualizado con gráficos,
artefactos de comparación/modelo y limitación de los p-valores de LinearSVR.
Verificación en navegador: tiempo de trabajo cambiado a 25,5 horas produce 3,642,
coincidente con la inferencia directa del pipeline. El tiempo cero con avance
se rechaza mediante las reglas de negocio. La consola no reporta errores.
Se actualizaron `preview.jpg` y `preview_modelos.jpg` y se creó
`preview_prediccion.jpg`. Los hashes de la fuente y de todos los CSV seleccionados
se comprobaron contra `seleccion.json`: permanecen intactos.
La captura del ejemplo se verificó con el resultado terminado y visible (3,642),
sin el indicador de carga. El dashboard queda abierto en ese acordeón.

El dashboard en `Dash/` usa exclusivamente **la alternativa 1: perturbación local**,
seleccionada en el notebook de aumentación. EDA, modelos y dashboard usan los
mismos CSV de `../Precalculo/comparacion_aumentacion/` y sus resultados recalculados.
Se retiraron los avisos de diferencias entre versiones; las cifras anteriores
se sustituyeron por las ejecuciones vigentes. Los CSV anteriores se conservan
como históricos y no se utilizan como fuente activa.

Dash 4.4.1 y Plotly 7.1.0 están instalados en `../Precalculo/venv/`.
No crear otro entorno virtual. La imagen original `img.jpeg` se sirve localmente
sin editar. Estilo claro, tarjetas blancas y categorías diferenciadas.

## Fuentes únicas

- Texto/diccionario: `../Precalculo/00_seleccion_base_datos.md`.
- Datos EDA/modelos: `comparacion_aumentacion/Datos_Aleks_Augmented_30000_r_2_train.csv`
  y `Datos_Aleks_Augmented_30000_r_2_test.csv` bajo Precalculo.
- Comparación de técnicas: `comparacion_aumentacion/comparacion_train.csv` y `seleccion.json`.
- Resultados canónicos: `../Precalculo/resultados/eda.json` y `modelos_lineales.json`.
  Se exportan al reejecutar notebooks con `Precalculo/actualizar_analisis.py`.
- Fuente del pipeline: `../Precalculo/precalculo_regresion_lineal.ipynb`.

Se comprobaron **24.000 train y 6.000 test válidos**, sin incumplimientos.
La división por estudiante precede a la aumentación. No mezclar ni volver a dividir.
`nota_final` no ingresa al modelo, matrices de correlación ni caché del dashboard.
Los outliers válidos se conservan. El test original de 301 filas, de la misma
preparación, queda reservado para una evaluación posterior sin variantes sintéticas.

## Interfaz

1. Introducción: fotografía, contexto institucional, objetivo y asignaturas.
   El diccionario de variables queda en EDA.
2. EDA: variables/contexto, comparación y proceso de aumentación, exploración
   interactiva. Histograma, cajas, scatter con predictor elegible, Spearman y faltantes,
   nueve densidades, frecuencias de las categóricas y cajas por intervalos de dominio final.
3. Modelos: diagrama de separación, esquema de cinco folds, pipeline, métricas,
   tabla de estadísticos y conclusiones, predicción vs realidad, residuos y calibración.
   Sección ampliable con bootstrap, aprendizaje y todos los coeficientes; acordeón de predicción.

Programa/asignatura son filtros combinables. EDA permite comparar general,
por programa o por asignatura. Modelos permite inspeccionar test o validación OOF.
Cada gráfico lleva explicación, leyendas, hover, zoom y descarga PNG.
Las combinaciones sin datos tienen estado vacío explícito.
Las conclusiones de la tabla se calculan por grupo según mejora frente a Dummy y R².

## Resultados vigentes y correspondencia

SVM test: RMSE **0.9083227217**, MAE **0.7314463368**,
MAPE **27.7551644858 %**, R² **0.3792266124**.
Validación SVM: RMSE medio **0.7973619090**, R² **0.5064455051**.
Mejora RMSE test frente a Dummy: **21.23 %**.

`prepare_data.py` ejecuta las celdas de configuración/auditoría/pipeline del
notebook vigente y reproduce sus cinco folds. Genera predicciones OOF por fila
sin usar esa fila en su entrenamiento, y test tras ajuste con todo train.
Verifica métricas frente a `resultados/modelos_lineales.json` con tolerancia 1e-10.

Sin filtros, la tabla de validación muestra la media de métricas de cinco folds,
como el notebook. Con filtros, muestra métricas agrupadas de las predicciones OOF.
MAE de validación es un cálculo adicional del dashboard. Las tarjetas de
predicciones OOF presentan métricas agrupadas y no la media de folds.
Los filtros evalúan el modelo global, sin reentrenar ni ajustar con test.

IC bootstrap, diagnósticos, curva de aprendizaje y conclusión global se leen
siempre de las exportaciones canónicas; no mantener valores escritos a mano.
El diagrama refleja 24.000/6.000 filas sin exclusiones.

## Archivos y ejecución

- `app.py`: interfaz/callbacks; `assets/style.css`: estilo local sin dependencias visuales remotas.
- `prepare_data.py`: preparación y controles de fuente.
- `data/train.csv.gz`, `test.csv.gz`: filas válidas y predicciones; sin `nota_final` ni IDs.
- `data/fold_metrics.csv`, `coefficients.csv`: resultados derivados.
- `data/manifest.json`: técnica y hashes de CSV, selección, notebooks, introducción y exportaciones.
  El inicio se detiene ante fuentes distintas de la caché.
- `data/model.joblib`: pipeline ajustado, con hash verificado al cargarlo.
- `prepare_comparison.py`, `data/augmentation.csv.gz`, `comparison_details.json`:
  contraste reproducido de originales de train y sintéticos de ambas alternativas.
- `charts.py`: densidades y acumuladas; `prediction.py`: formulario, validación y reporte completo de β.
- `requirements.txt`, `README.md`, `test_dashboard.py` y `.gitignore`.
- `preview.jpg`: referencia visual de la introducción.
- `preview_modelos.jpg`: comprobación visual de los resultados unificados.
- `preview_prediccion.jpg`: formulario y resultado de ejemplo.
- `preview_metricas.jpg`: comparación de métricas con los tres títulos visibles.

Desde la raíz del espacio de trabajo:

```powershell
.\Precalculo\venv\Scripts\python.exe .\Dash\app.py
```

Desde Dash: `..\Precalculo\venv\Scripts\python.exe app.py`.
URL: `http://127.0.0.1:8050/`, loopback, debug desactivado.

Para actualizar todo el flujo, ejecutar en este orden desde la raíz:

```powershell
.\Precalculo\venv\Scripts\python.exe .\Precalculo\actualizar_analisis.py
.\Precalculo\venv\Scripts\python.exe .\Dash\prepare_data.py
.\Precalculo\venv\Scripts\python.exe .\Dash\test_dashboard.py
```

Actualizar ambos contextos, reconstruir el Book y reiniciar el servidor.

## Validaciones y límites

Las nueve pruebas pasan: igualdad de fuente entre EDA/modelos, igualdad de filas
con el CSV seleccionado, coincidencia numérica de métricas con el notebook,
reglas de negocio y outliers, filtros, callbacks HTTP, assets y estados vacíos,
comparación de aumentación, reporte completo de β y simulador contra predicciones test.
Ambos notebooks se ejecutaron completos sin errores guardados.
El navegador comprobó la vista general: 6.000 filas test, R² 0,379, MAE 0,731
y reducción de RMSE 21,2 %. La consola no reporta errores. El filtro MAT1101
también se comprobó: 3.353 filas de test y R² 0,459.
La exportación HTML del Book terminó con código 0; sus cuatro páginas incluyen
los resultados vigentes (R² 0,3792 en la página de regresión).
Se revisó el diseño estrecho y escritorio; los gráficos reservan altura explícita
para evitar recorte con responsive=True. Se conservan etiquetas y leyendas legibles.

Los scatter muestrean reproduciblemente hasta 2.500 filas EDA y 3.000 modelos;
todos los cálculos usan las filas filtradas completas, según explica la interfaz.
Las filas aumentadas no son estudiantes independientes. Los folds carecen de
ID para agruparse por estudiante. Los IC remuestrean filas aumentadas.
R² no definido para una fila o nota constante. MAPE sensible a notas bajas.
Coeficientes no causales; LinearSVR no acota predicciones y no se recortan.

## Protocolo obligatorio

**Actualizar este archivo en cada modificación del dashboard.** Registrar
fuentes, decisiones, validaciones y limitaciones. Leer también
`../Precalculo/CONTEXT.md`. Mantener la alternativa 1 como fuente única del flujo
activo y sincronizar resultados canónicos antes de publicar cifras nuevas.

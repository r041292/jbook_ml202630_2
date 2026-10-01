# Dashboard de Precálculo

## Publicar en Render con GitHub

Repositorio: https://github.com/r041292/jbook_ml202630_2, rama `main`.
El checkout de publicación local está en `../RenderDeploy/`. Contiene únicamente
el código, los assets, los datos derivados sin IDs ni nota_final y cinco fuentes
públicas de resultados/texto. Los datos brutos con nombres/correos y los notebooks
no se publican. El historial anterior de Precalculo permanece en su repositorio local.

En Render, usar **New > Blueprint**, conectar GitHub y seleccionar este repositorio.
Render lee `render.yaml` y crea `precalculo-dashboard` con plan Free. Revisar el
servicio y confirmar su creación. Esperar estado Live y abrir su URL HTTPS.

También se puede usar **New > Web Service** con estos valores:

| Campo | Valor |
| --- | --- |
| Branch | `main` |
| Language | Python 3 |
| Root Directory | Vacío (raíz del repositorio) |
| Build Command | `pip install -r Dash/requirements.txt` |
| Start Command | `gunicorn --chdir Dash app:server --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 --access-logfile - --error-logfile -` |
| Health Check Path | `/healthz` |
| Instance Type | Free |
| Auto Deploy | On Commit |
| Environment | `PYTHON_VERSION=3.12.14`, `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`, `MKL_NUM_THREADS=1` |

No seleccionar `Dash` como Root Directory: Render excluye los archivos externos
a ese directorio y el tablero necesita `Precalculo/`. No entrenar ni ejecutar
notebooks durante el build. Los artefactos ya ajustados están versionados.
El paquete verifica hashes de todos los artefactos y de las cinco fuentes públicas
antes de servir solicitudes; las fuentes completas se verifican al exportar localmente.
`.gitattributes` conserva los bytes de los archivos para no alterar esos hashes.

El plan Free suspende el servicio tras 15 minutos sin tráfico; la siguiente visita
puede demorar aproximadamente un minuto. No necesita base de datos ni disco persistente.

Para publicar una actualización, ejecutar las pruebas locales, exportar y subir:

```powershell
.\Precalculo\venv\Scripts\python.exe .\Dash\test_dashboard.py
.\Precalculo\venv\Scripts\python.exe .\Dash\prepare_deployment.py
git -C RenderDeploy add Dash Precalculo render.yaml .python-version .gitattributes .gitignore
git -C RenderDeploy commit -m "Actualiza dashboard de Precalculo"
git -C RenderDeploy push origin main
```

La regeneración de datos se realiza en el espacio local completo, siguiendo el
procedimiento descrito abajo. El checkout público sirve el modelo ya ajustado.

Tres pestañas: Introducción, EDA (variables, aumentación y exploración) y Modelos lineales.
Filtros combinables por programa/asignatura y gráficos interactivos con descarga PNG.
Incluye contraste gráfico de aumentación con originales, densidades numéricas,
frecuencias categóricas, cajas de nota por dominio final y conclusiones con tratamientos.
Modelos incorpora el reporte completo de coeficientes y un acordeón para predecir
con el pipeline ajustado. LinearSVR no define p-valores; esa limitación se muestra
en el reporte, junto a las categorías de referencia.

## Iniciar

Desde `C:\Users\Rubiel\Documents\Machine Learning Maestria`:

```powershell
.\Precalculo\venv\Scripts\python.exe .\Dash\app.py
```

Abrir [dashboard local](http://127.0.0.1:8050/). Detener con Ctrl+C en la terminal del servidor.
Desde `Dash`, usar `..\Precalculo\venv\Scripts\python.exe app.py`.
Antes de reiniciar, detener la instancia existente. Mantener un solo servidor en
el puerto 8050 para que el navegador muestre siempre la versión actualizada.

## Dependencias y preparación

Las dependencias ya están instaladas en el venv compartido. Para reinstalarlas:

```powershell
.\Precalculo\venv\Scripts\python.exe -m pip install -r .\Dash\requirements.txt
```

Los resultados derivados se entregan en `data/`. Si cambian notebook o CSV fuente:

```powershell
.\Precalculo\venv\Scripts\python.exe .\Dash\prepare_data.py
```

La preparación reproduce el pipeline del notebook y verifica sus métricas. No modifica fuentes.
El dashboard comprueba hashes al iniciar y rechaza caché desactualizada.
Guarda el pipeline en `data/model.joblib`, con hash verificado antes de cargarlo.
Reproduce la alternativa 2 únicamente para el contraste de aumentación, sobre los
originales ya preservados de train: no repite el split ni utiliza test. Comprueba
sus métricas frente al notebook y guarda `data/augmentation.csv.gz`.

## Lectura de resultados

- EDA, modelos y dashboard usan exclusivamente los CSV de `Precalculo/comparacion_aumentacion/`, generados con la alternativa 1 seleccionada: perturbación local.
- Los notebooks se reejecutaron sobre esta fuente: 24.000 filas de train y 6.000 de test, sin incumplimientos. Los CSV anteriores se conservan como históricos.
- Métricas, intervalos, diagnósticos y curva de aprendizaje provienen de `Precalculo/resultados/` y se actualizan al ejecutar `Precalculo/actualizar_analisis.py`.
- Validación global: media de cinco folds. Validación filtrada: métricas agrupadas OOF.
- Los filtros evalúan el modelo global; no entrenan modelos independientes.
- El test evaluado contiene variantes sintéticas y no equivale al test original de 301 filas recomendado para futuras evaluaciones.

Consultar `CONTEXT.md` para decisiones, cifras y limitaciones. Mantenerlo actualizado en cada modificación según `AGENTS.md`.

Verificación desde la raíz:

```powershell
.\Precalculo\venv\Scripts\python.exe .\Dash\test_dashboard.py
```

Nueve pruebas validan correspondencia con el notebook, integridad, filtros,
callbacks HTTP, recursos locales, contraste de aumentación, reporte de β y predicción.

Para actualizar todo el análisis después de modificar la generación seleccionada:

```powershell
.\Precalculo\venv\Scripts\python.exe .\Precalculo\actualizar_analisis.py
.\Precalculo\venv\Scripts\python.exe .\Dash\prepare_data.py
.\Precalculo\venv\Scripts\python.exe .\Dash\test_dashboard.py
```

Después, actualizar ambos documentos de contexto y reiniciar el servidor.

Referencias técnicas: [callbacks de Dash](https://dash.plotly.com/basic-callbacks) y [pestañas de Dash](https://dash.plotly.com/dash-core-components/tabs).

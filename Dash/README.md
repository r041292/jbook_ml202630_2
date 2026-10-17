# Dashboard · Entregable 3

El flujo activo usa datos reales, test 202530 y GroupKFold anidado por estudiante.
Modelos predictivos se organiza en Split y CV, Modelos lineales, Clásicos y Originales.
Ejecutar también Precalculo/modelos_clasicos.py después de entregable3.py y antes
 de prepare_data.py para evaluar KNN, Ridge, Lasso, Random Forest y XGBoost.
El notebook nuevo precalculo_modelos_clasicos_e3.ipynb inspecciona esos resultados.
Desde la raíz ejecutar entregable3.py, Dash/prepare_data.py y Dash/app.py usando
Precalculo/venv/Scripts/python.exe. Resultados en Precalculo/resultados/e3/.
No ejecutar actualizar_analisis.py: los notebooks anteriores permanecen intactos.
El trabajo vigente del dashboard continúa en main; los Books publicados
son antecedentes y se producirá uno nuevo. Ver CONTEXT.md para la reproducción completa.

## Interpretación del pipeline, betas y XGBoost

Al final de Split y CV se muestra el flujo del pipeline compartido por LinearSVR,
Ridge y Lasso: mediana, log1p en tiempos/tasa, StandardScaler, moda y one-hot con
referencia. El número de columnas, estadísticas y referencias se leen del
artefacto guardado. Se distingue fit en train de transform en validación/test.

El reporte completo de betas y su CSV se ordenan por |β| descendente. Incluye
intercepto y referencias en cero, interpretación por desviación estándar, cambios
en unidades originales y la fórmula exacta de log1p. Son asociaciones matemáticas
condicionales, sin p inventados; avance y dominios no pueden variarse independientemente.

Clásicos incorpora LIME para el XGBoost guardado (no cambia con el selector de
familia). Permite elegir un caso anónimo de test o train y respeta los filtros.
En train explica el ajuste final, nunca su predicción OOF. Los parámetros del
explicador usan solo train, sin usar notas de test ni reentrenar XGBoost.

Por defecto se usa una **variante empírica**: remuestreo de filas completas de
train y núcleo/regresión local de la librería LIME. Se conservan las relaciones
de las filas observadas, pero puede faltar soporte cercano al caso. Se ofrece
también LIME estándar con perturbaciones independientes y diagnóstico de
coherencia dominios/avance. Esta comprobación no valida todas las restricciones.
Semilla42, cuartiles y todos los15 términos. Se muestran predicción XGBoost,
aproximación LIME, error local, fidelidad R² ponderada y descomposición aditiva.
Ese R² es ajuste del sustituto sobre su vecindario, no rendimiento predictivo ni
validación externa. Un R² alto puede coexistir con un error grande en el caso.
Los aportes no son causas ni importancia global; semilla fija no garantiza
estabilidad ante otras semillas. Las explicaciones se generan solo al pulsar el
botón y se limpian al cambiar caso/filtros/método. Dependencia:lime==0.2.0.1.

Referencias: [artículo LIME](https://arxiv.org/abs/1602.04938),
[API oficial](https://lime-ml.readthedocs.io/en/latest/lime.html) y
[tutorial de regresión](https://marcotcr.github.io/lime/tutorials/Using%2Blime%2Bfor%2Bregression.html).

## Comparación vigente: CV externa y test temporal

**Kernel Ridge RBF** es el candidato activo con menor RMSE medio de CV externa
(0.801325). Su pipeline original guardado reproduce las188 predicciones de test
(error máximo1.3e-15), sin reentrenamiento. La sección de exploración y el
simulador usan ese artefacto. Abre en OOF; RMSE reunido0.802245 difiere de la
media entre folds0.801325. Las tablas y gráficos siguen RMSE ascendente.

GPR sola se retiró del inventario activo, la inferencia CV, la matriz de errores
y el simulador por solicitud del usuario. Se conservan los antecedentes
archivados; el híbrido GPR–XGBoost permanece como experimento distinto.
La nueva familia **Holm24 CV vs SVM** incluye los24 competidores activos con
OOF frente al SVM; se conserva también al mostrar solo Clásicos. Kernel Ridge
p=0.16475/Holm24=1.00000: ninguna mejora evaluada es significativa tras Holm24.

La t pareada corregida por solapamiento (aproximación Nadeau–Bengio) usa5 folds
sin repeticiones y4 grados de libertad: inferencia exploratoria de baja potencia,
sin garantía de calibración exacta para GroupKFold. Test202530 se mantiene como
contraste temporal; no selecciona familias. No se trasladan p globales a filtros.
TabPFN fine-tuned carece de CV independiente. Los p/familias de test se conservan
como inferencia histórica separada. No se entrena al arrancar el dashboard.

Ver [README E3](../Precalculo/README_E3.md) y
[método y resultados CV](../Precalculo/resultados/e3/cv_externa/README.md).
Desde la raíz, con el entorno compartido:

```powershell
.\Precalculo\venv\Scripts\python.exe .\Precalculo\significancia_cv_externa_e3.py
.\Precalculo\venv\Scripts\python.exe .\Dash\prepare_data.py
.\Precalculo\venv\Scripts\python.exe -m unittest discover -s Dash -p 'test_*.py'
```

## Documentación histórica

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

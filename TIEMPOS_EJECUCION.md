# Registro de tiempos de ejecución de modelos

## Propósito y vigencia

Directriz acordada el 17 de octubre de 2026 (America/Bogota). Desde este punto,
toda nueva ejecución relacionada con búsqueda de hiperparámetros, entrenamiento
(incluidos reentrenamientos y refits) e inferencia debe quedar registrada aquí,
para todos los modelos implementados. La medición se incorpora antes de ejecutar.
El historial permitirá incorporar métricas en distintas partes del dashboard;
El 18-oct-2026 el usuario autorizó mostrarlas en las fichas de modelos clásicos
y en los resultados de búsqueda SVM, con tiempos de búsqueda/refit por separado.

## Estado inicial

Documento creado sin ejecutar entrenamientos, búsquedas ni inferencias nuevas.
No se han recopilado tiempos históricos en esta tarea. La ausencia de una medida
se expresa como **No medido**, nunca como cero. Solo se podrán incorporar cifras
anteriores si existen logs o artefactos verificables que documenten su alcance.

## Protocolo de medición

1. Asignar un ID único de ejecución y registrar fecha/hora con zona horaria,
   modelo/variante, motivo (nuevo, reentrenamiento o evaluación) y procedencia.
2. Medir duración de pared en segundos con `time.perf_counter()` alrededor de
   cada operación. En GPU, sincronizar antes y después de operaciones asíncronas.
   Registrar también comienzo/fin con zona horaria; no usar el reloj civil para
   calcular duración. Medir sin modificar las particiones o el protocolo científico.
3. Separar las etapas:
   - **Búsqueda de hiperparámetros:** tiempo completo de cada búsqueda interna
     por fold externo y de la búsqueda final. Registrar grilla/espacio, estrategia,
     número de candidatos y folds, ajustes previstos/completados y paralelismo.
     Indicar si incluye preprocesamiento, scoring y refit automático.
   - **Entrenamiento/refit:** tiempo del ajuste por fold externo y del ajuste final,
     incluyendo el preprocesamiento aprendido dentro del pipeline cuando corresponda.
     Si una búsqueda incluye refit, instrumentarlo por separado cuando sea posible
     (p. ej., `refit_time_`) y marcarlo como incluido en la búsqueda. No repetir
     ajustes solo para medir ni sumar dos veces el mismo trabajo.
   - **Inferencia:** tiempo de `predict` por lote de validación externa/OOF, test
     o aplicación, con el pipeline y sus transformaciones. Registrar carga del
     artefacto y E/S por separado si se miden; no mezclarlas con `predict`.
4. En cada etapa indicar el alcance exacto. Conservar medidas por fold/lote y
   el tiempo total de pared del experimento, si se mide. La suma de tareas que
   corren en paralelo no equivale a la duración de pared. Los `mean_fit_time` de
   un buscador son estadísticas auxiliares, no el tiempo total de la búsqueda.
5. Registrar tamaño del lote y número de repeticiones de inferencia. Distinguir
   primera ejecución (fría), calentamiento y repeticiones posteriores. Si hay
   varias repeticiones, conservar sus valores y resumir mediana y dispersión.
   Los milisegundos por registro calculados de un lote son un promedio por
   registro, no la latencia de una petición individual. No comparar lotes,
   equipos o configuraciones distintos sin explicar esas diferencias.
6. Conservar logs o artefactos crudos (preferentemente CSV/JSON) junto al
   experimento y enlazarlos aquí. Registrar también ejecuciones interrumpidas o
   fallidas y su duración parcial; no presentarlas como resultados completos.
7. Añadir una ficha por ejecución y filas por etapa/fold/lote. No sobrescribir
   mediciones anteriores. Cualquier resumen debe poder rastrearse a la evidencia.

## Plantilla por ejecución

Copiar este bloque para cada ejecución real y sustituir los campos. Los campos
no medidos o no aplicables deben quedar explícitos, sin cifras supuestas.

### Ejecución `<ID único>`

- **Fecha/hora y zona:** `<inicio/fin, America/Bogota o zona explícita>`.
- **Modelo y variante:** `<nombre, versión, nuevo/reentrenamiento/evaluación>`.
- **Código:** `<script/notebook, commit o hash y comando ejecutado>`.
- **Datos:** `<versión/hash, partición, filas, variables, grupos, esquema de CV>`.
- **Configuración:** `<hiperparámetros o espacio de búsqueda, semilla, folds, candidatos>`.
- **Entorno:** `<SO, Python y versiones relevantes, CPU/GPU, RAM/VRAM, hilos/n_jobs>`.
- **Alcance:** `<preprocesamiento, scoring, refit, E/S y carga incluidos/excluidos; solapamientos>`.
- **Inferencia:** `<lote, repeticiones, frío/caliente, calentamiento y sincronización GPU>`.
- **Estado:** `<completa/parcial/fallida; motivo y limitaciones>`.
- **Evidencia:** `<enlaces a logs y artefactos de medición>`.

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Búsqueda | `<fold externo o búsqueda final>` | No medido | No aplica | `<n>` | Pendiente | `<alcance/log>` |
| Entrenamiento/refit | `<fold externo o ajuste final>` | No medido | No aplica | `<n>` | Pendiente | `<refit incluido en búsqueda o ajuste separado>` |
| Inferencia | `<validación externa, test o aplicación>` | No medido | `<n>` | `<n>` | Pendiente | `<predict del pipeline/log>` |
| Total del experimento | `<alcance completo>` | No medido | No aplica | No aplica | Pendiente | `<medida directa; no suma de tareas paralelas>` |

## Ejecuciones registradas

Las fichas reales se conservan a continuación, en orden de incorporación.
La plantilla anterior no representa una ejecución real.

### Ejecución `20261018_095829_5b05000d`

- **Modelo/motivo:** Decision Tree · nuevo modelo E3.
- **Fecha/zona:** 2026-10-18T09:58:29.130728-05:00 a 2026-10-18T09:58:45.855566-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_095829_5b05000d/metadata.json](tiempos/20261018_095829_5b05000d/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_095829_5b05000d/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Búsqueda | fold_1 | 5.672240400 | 1047 | 1 | completa | Total; eventos.jsonl línea 1 |
| Entrenamiento/refit | fold_1 | 0.014265500 | 1047 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | OOF fold 1 | 0.004468600 | 262 | 1 | completa | Total; eventos.jsonl línea 3 |
| Inferencia | train fold 1 | 0.005630300 | 1047 | 1 | completa | Total; eventos.jsonl línea 4 |
| Búsqueda | fold_2 | 1.795983600 | 1047 | 1 | completa | Total; eventos.jsonl línea 5 |
| Entrenamiento/refit | fold_2 | 0.012183100 | 1047 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | OOF fold 2 | 0.004156800 | 262 | 1 | completa | Total; eventos.jsonl línea 7 |
| Inferencia | train fold 2 | 0.004457800 | 1047 | 1 | completa | Total; eventos.jsonl línea 8 |
| Búsqueda | fold_3 | 1.821375400 | 1047 | 1 | completa | Total; eventos.jsonl línea 9 |
| Entrenamiento/refit | fold_3 | 0.013190400 | 1047 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | OOF fold 3 | 0.004081800 | 262 | 1 | completa | Total; eventos.jsonl línea 11 |
| Inferencia | train fold 3 | 0.004957600 | 1047 | 1 | completa | Total; eventos.jsonl línea 12 |
| Búsqueda | fold_4 | 1.789795600 | 1047 | 1 | completa | Total; eventos.jsonl línea 13 |
| Entrenamiento/refit | fold_4 | 0.013020400 | 1047 | 1 | completa | Total; eventos.jsonl línea 14 |
| Inferencia | OOF fold 4 | 0.004190700 | 262 | 1 | completa | Total; eventos.jsonl línea 15 |
| Inferencia | train fold 4 | 0.004563400 | 1047 | 1 | completa | Total; eventos.jsonl línea 16 |
| Búsqueda | fold_5 | 1.791408200 | 1048 | 1 | completa | Total; eventos.jsonl línea 17 |
| Entrenamiento/refit | fold_5 | 0.011974000 | 1048 | 1 | completa | Total; eventos.jsonl línea 18 |
| Inferencia | OOF fold 5 | 0.005395600 | 261 | 1 | completa | Total; eventos.jsonl línea 19 |
| Inferencia | train fold 5 | 0.005672800 | 1048 | 1 | completa | Total; eventos.jsonl línea 20 |
| Búsqueda | final | 1.953947500 | 1309 | 1 | completa | Total; eventos.jsonl línea 21 |
| Entrenamiento/refit | final | 0.014147800 | 1309 | 1 | completa | Total; eventos.jsonl línea 22 |
| Inferencia | test temporal | 0.005285400 | 188 | 1 | completa | Total; eventos.jsonl línea 23 |
| Inferencia | test verificación serialización | 0.004091900 | 188 | 1 | completa | Total; eventos.jsonl línea 24 |
| Inferencia | train final | 0.006036400 | 1309 | 1 | completa | Total; eventos.jsonl línea 25 |
| Total del experimento | Decision Tree · nuevo modelo E3 | 16.725402700 | No aplica | 1 | completa | Total; eventos.jsonl línea 26 |

### Ejecución `20261018_095916_5e654386`

- **Modelo/motivo:** Verificación/preparación · .\Dash\prepare_data.py.
- **Fecha/zona:** 2026-10-18T09:59:16.469663-05:00 a 2026-10-18T09:59:20.826601-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_095916_5e654386/metadata.json](tiempos/20261018_095916_5e654386/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_095916_5e654386/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | TransformedTargetRegressor | 0.044534700 | 188 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | TruncatedNewtonKernelRidgeRegressor | 0.011276200 | 188 | 1 | completa | Total; eventos.jsonl línea 2 |
| Total del experimento | Verificación/preparación · .\Dash\prepare_data.py | 4.354787600 | No aplica | 1 | completa | Total; eventos.jsonl línea 3 |

### Ejecución `20261018_100025_db27d1d1`

- **Modelo/motivo:** KNeighborsRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T10:00:25.537084-05:00 a 2026-10-18T10:00:25.561998-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100025_db27d1d1/metadata.json](tiempos/20261018_100025_db27d1d1/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100025_db27d1d1/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.015425400 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | KNeighborsRegressor · inferencia de aplicación | 0.025847400 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_100025_8c2952aa`

- **Modelo/motivo:** Ridge · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T10:00:25.595154-05:00 a 2026-10-18T10:00:25.617175-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100025_8c2952aa/metadata.json](tiempos/20261018_100025_8c2952aa/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100025_8c2952aa/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.007541100 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Ridge · inferencia de aplicación | 0.013718600 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_100025_30a53d24`

- **Modelo/motivo:** Lasso · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T10:00:25.628567-05:00 a 2026-10-18T10:00:25.649421-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100025_30a53d24/metadata.json](tiempos/20261018_100025_30a53d24/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100025_30a53d24/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.006964300 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Lasso · inferencia de aplicación | 0.013975000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_100025_abe68287`

- **Modelo/motivo:** RandomForestRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T10:00:25.862483-05:00 a 2026-10-18T10:00:25.907015-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100025_abe68287/metadata.json](tiempos/20261018_100025_abe68287/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100025_abe68287/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.028463000 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | RandomForestRegressor · inferencia de aplicación | 0.037340200 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_100026_ca4ef351`

- **Modelo/motivo:** XGBRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T10:00:26.018416-05:00 a 2026-10-18T10:00:26.048802-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100026_ca4ef351/metadata.json](tiempos/20261018_100026_ca4ef351/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100026_ca4ef351/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.020941600 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | XGBRegressor · inferencia de aplicación | 0.028545300 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_100026_78ec18b0`

- **Modelo/motivo:** DecisionTreeRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T10:00:26.080077-05:00 a 2026-10-18T10:00:26.094004-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100026_78ec18b0/metadata.json](tiempos/20261018_100026_78ec18b0/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100026_78ec18b0/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.006022600 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | DecisionTreeRegressor · inferencia de aplicación | 0.013979700 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_100031_4d301c79`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T10:00:31.828365-05:00 a 2026-10-18T10:00:31.844569-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100031_4d301c79/metadata.json](tiempos/20261018_100031_4d301c79/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100031_4d301c79/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.005805100 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.010688600 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_100031_541140ee`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T10:00:31.861645-05:00 a 2026-10-18T10:00:31.878511-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100031_541140ee/metadata.json](tiempos/20261018_100031_541140ee/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100031_541140ee/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.008096500 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.013011700 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_100031_1edaed9c`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T10:00:31.884058-05:00 a 2026-10-18T10:00:31.898797-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100031_1edaed9c/metadata.json](tiempos/20261018_100031_1edaed9c/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100031_1edaed9c/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.006206400 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.011531900 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_100031_edc6dbb1`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T10:00:31.911138-05:00 a 2026-10-18T10:00:31.916059-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100031_edc6dbb1/metadata.json](tiempos/20261018_100031_edc6dbb1/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100031_edc6dbb1/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.005714500 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.011218500 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_100031_596b8637`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T10:00:31.928592-05:00 a 2026-10-18T10:00:31.944559-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100031_596b8637/metadata.json](tiempos/20261018_100031_596b8637/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100031_596b8637/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.006147700 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.011536700 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_100037_67b6dfc1`

- **Modelo/motivo:** TransformedTargetRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T10:00:37.597470-05:00 a 2026-10-18T10:00:37.626138-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100037_67b6dfc1/metadata.json](tiempos/20261018_100037_67b6dfc1/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100037_67b6dfc1/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.028084200 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TransformedTargetRegressor · inferencia de aplicación | 0.034473900 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_100019_e5ff36be`

- **Modelo/motivo:** Verificación/preparación · --tests.
- **Fecha/zona:** 2026-10-18T10:00:19.807468-05:00 a 2026-10-18T10:00:42.610201-05:00; America/Bogota.
- **Estado:** fallida. **Entorno/configuración/código/datos:** [tiempos/20261018_100019_e5ff36be/metadata.json](tiempos/20261018_100019_e5ff36be/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100019_e5ff36be/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | KNeighborsRegressor | 0.014620400 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | KNeighborsRegressor | 0.014333400 | 1 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | Ridge | 0.006984600 | 1 | 1 | completa | Total; eventos.jsonl línea 3 |
| Inferencia | Ridge | 0.005845700 | 1 | 1 | completa | Total; eventos.jsonl línea 4 |
| Inferencia | Lasso | 0.006412500 | 1 | 1 | completa | Total; eventos.jsonl línea 5 |
| Inferencia | Lasso | 0.007074100 | 1 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | RandomForestRegressor | 0.027763400 | 1 | 1 | completa | Total; eventos.jsonl línea 7 |
| Inferencia | RandomForestRegressor | 0.030077800 | 1 | 1 | completa | Total; eventos.jsonl línea 8 |
| Inferencia | XGBRegressor | 0.020143000 | 1 | 1 | completa | Total; eventos.jsonl línea 9 |
| Inferencia | XGBRegressor | 0.015032400 | 1 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | DecisionTreeRegressor | 0.005390700 | 1 | 1 | completa | Total; eventos.jsonl línea 11 |
| Inferencia | DecisionTreeRegressor | 0.004954000 | 1 | 1 | completa | Total; eventos.jsonl línea 12 |
| Inferencia | LinearSVR | 0.005301100 | 1 | 1 | completa | Total; eventos.jsonl línea 13 |
| Inferencia | LinearSVR | 0.004728400 | 1 | 1 | completa | Total; eventos.jsonl línea 14 |
| Inferencia | LinearSVR | 0.007347500 | 1 | 1 | completa | Total; eventos.jsonl línea 15 |
| Inferencia | LinearSVR | 0.005581700 | 1 | 1 | completa | Total; eventos.jsonl línea 16 |
| Inferencia | LinearSVR | 0.005206200 | 1 | 1 | completa | Total; eventos.jsonl línea 17 |
| Inferencia | LinearSVR | 0.005560200 | 1 | 1 | completa | Total; eventos.jsonl línea 18 |
| Inferencia | DecisionTreeRegressor | 0.006227600 | 188 | 1 | completa | Total; eventos.jsonl línea 19 |
| Inferencia | LinearSVR | 0.005753300 | 1 | 1 | completa | Total; eventos.jsonl línea 20 |
| Inferencia | LinearSVR | 0.004844600 | 1 | 1 | completa | Total; eventos.jsonl línea 21 |
| Inferencia | LinearSVR | 0.004664400 | 1 | 1 | completa | Total; eventos.jsonl línea 22 |
| Inferencia | LinearSVR | 0.008108200 | 1 | 1 | completa | Total; eventos.jsonl línea 23 |
| Inferencia | XGBRegressor | 0.014146900 | 188 | 1 | completa | Total; eventos.jsonl línea 24 |
| Inferencia | XGBRegressor | 0.013770400 | 188 | 1 | completa | Total; eventos.jsonl línea 25 |
| Inferencia | XGBRegressor | 0.013577700 | 1 | 1 | completa | Total; eventos.jsonl línea 26 |
| Inferencia | XGBRegressor | 0.013688400 | 1 | 1 | completa | Total; eventos.jsonl línea 27 |
| Inferencia | XGBRegressor | 0.013531400 | 1 | 1 | completa | Total; eventos.jsonl línea 28 |
| Inferencia | XGBRegressor | 0.016859800 | 1000 | 1 | completa | Total; eventos.jsonl línea 29 |
| Entrenamiento/refit | Ridge | 0.003033500 | 1000 | 1 | completa | Total; eventos.jsonl línea 30 |
| Inferencia | XGBRegressor | 0.012311800 | 1 | 1 | completa | Total; eventos.jsonl línea 31 |
| Inferencia | XGBRegressor | 0.014768900 | 1 | 1 | completa | Total; eventos.jsonl línea 32 |
| Inferencia | XGBRegressor | 0.017443000 | 1000 | 1 | completa | Total; eventos.jsonl línea 33 |
| Entrenamiento/refit | Ridge | 0.001330400 | 1000 | 1 | completa | Total; eventos.jsonl línea 34 |
| Inferencia | XGBRegressor | 0.012287400 | 1 | 1 | completa | Total; eventos.jsonl línea 35 |
| Inferencia | XGBRegressor | 0.011410000 | 1 | 1 | completa | Total; eventos.jsonl línea 36 |
| Inferencia | XGBRegressor | 0.016596700 | 1000 | 1 | completa | Total; eventos.jsonl línea 37 |
| Entrenamiento/refit | Ridge | 0.001069400 | 1000 | 1 | completa | Total; eventos.jsonl línea 38 |
| Inferencia | XGBRegressor | 0.013105700 | 1 | 1 | completa | Total; eventos.jsonl línea 39 |
| Inferencia | XGBRegressor | 0.015678100 | 1000 | 1 | completa | Total; eventos.jsonl línea 40 |
| Entrenamiento/refit | Ridge | 0.001037500 | 1000 | 1 | completa | Total; eventos.jsonl línea 41 |
| Inferencia | XGBRegressor | 0.013161700 | 1 | 1 | completa | Total; eventos.jsonl línea 42 |
| Inferencia | XGBRegressor | 0.014574300 | 1000 | 1 | completa | Total; eventos.jsonl línea 43 |
| Entrenamiento/refit | Ridge | 0.000996200 | 1000 | 1 | completa | Total; eventos.jsonl línea 44 |
| Inferencia | TransformedTargetRegressor | 0.025272600 | 1 | 1 | completa | Total; eventos.jsonl línea 45 |
| Inferencia | TransformedTargetRegressor | 0.011965200 | 188 | 1 | completa | Total; eventos.jsonl línea 46 |
| Total del experimento | Verificación/preparación · --tests | 22.802809200 | No aplica | 1 | fallida | Total; eventos.jsonl línea 47 |

### Ejecución `20261018_100131_8e528bd9`

- **Modelo/motivo:** KNeighborsRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T10:01:31.843763-05:00 a 2026-10-18T10:01:31.873947-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100131_8e528bd9/metadata.json](tiempos/20261018_100131_8e528bd9/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100131_8e528bd9/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.016420500 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | KNeighborsRegressor · inferencia de aplicación | 0.027500700 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_100131_564d0402`

- **Modelo/motivo:** Ridge · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T10:01:31.904733-05:00 a 2026-10-18T10:01:31.924321-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100131_564d0402/metadata.json](tiempos/20261018_100131_564d0402/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100131_564d0402/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.012651800 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Ridge · inferencia de aplicación | 0.019573200 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_100131_4c482a6e`

- **Modelo/motivo:** Lasso · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T10:01:31.953461-05:00 a 2026-10-18T10:01:31.973662-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100131_4c482a6e/metadata.json](tiempos/20261018_100131_4c482a6e/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100131_4c482a6e/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.013127600 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Lasso · inferencia de aplicación | 0.019977000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_100132_1301ac92`

- **Modelo/motivo:** RandomForestRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T10:01:32.202727-05:00 a 2026-10-18T10:01:32.337360-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100132_1301ac92/metadata.json](tiempos/20261018_100132_1301ac92/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100132_1301ac92/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.125476300 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | RandomForestRegressor · inferencia de aplicación | 0.135509900 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_100132_6d1fe7fa`

- **Modelo/motivo:** XGBRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T10:01:32.509170-05:00 a 2026-10-18T10:01:32.546408-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100132_6d1fe7fa/metadata.json](tiempos/20261018_100132_6d1fe7fa/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100132_6d1fe7fa/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.028711000 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | XGBRegressor · inferencia de aplicación | 0.036534800 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_100132_ef36b9e5`

- **Modelo/motivo:** DecisionTreeRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T10:01:32.587659-05:00 a 2026-10-18T10:01:32.600863-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100132_ef36b9e5/metadata.json](tiempos/20261018_100132_ef36b9e5/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100132_ef36b9e5/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.007659300 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | DecisionTreeRegressor · inferencia de aplicación | 0.012898200 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_100138_715d9b25`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T10:01:38.210388-05:00 a 2026-10-18T10:01:38.226564-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100138_715d9b25/metadata.json](tiempos/20261018_100138_715d9b25/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100138_715d9b25/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.010085700 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.015091600 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_100138_8d8d2b22`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T10:01:38.248905-05:00 a 2026-10-18T10:01:38.268557-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100138_8d8d2b22/metadata.json](tiempos/20261018_100138_8d8d2b22/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100138_8d8d2b22/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.010159000 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.015512000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_100138_b9a95ca6`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T10:01:38.277462-05:00 a 2026-10-18T10:01:38.291387-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100138_b9a95ca6/metadata.json](tiempos/20261018_100138_b9a95ca6/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100138_b9a95ca6/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.009241400 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.014773000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_100138_880c2a5a`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T10:01:38.303520-05:00 a 2026-10-18T10:01:38.318812-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100138_880c2a5a/metadata.json](tiempos/20261018_100138_880c2a5a/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100138_880c2a5a/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.009670800 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.014747600 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_100138_4dab16a6`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T10:01:38.328992-05:00 a 2026-10-18T10:01:38.345091-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100138_4dab16a6/metadata.json](tiempos/20261018_100138_4dab16a6/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100138_4dab16a6/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.010212400 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.015654400 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_100143_784a72de`

- **Modelo/motivo:** TransformedTargetRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T10:01:43.950315-05:00 a 2026-10-18T10:01:43.972604-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100143_784a72de/metadata.json](tiempos/20261018_100143_784a72de/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100143_784a72de/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.021802100 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TransformedTargetRegressor · inferencia de aplicación | 0.028374700 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_100126_38464220`

- **Modelo/motivo:** Verificación/preparación · --tests.
- **Fecha/zona:** 2026-10-18T10:01:26.588011-05:00 a 2026-10-18T10:01:49.766430-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100126_38464220/metadata.json](tiempos/20261018_100126_38464220/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100126_38464220/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | KNeighborsRegressor | 0.011147600 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | KNeighborsRegressor | 0.006784800 | 1 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | Ridge | 0.000147500 | 1 | 1 | completa | Total; eventos.jsonl línea 3 |
| Inferencia | Ridge | 0.007499100 | 1 | 1 | completa | Total; eventos.jsonl línea 4 |
| Inferencia | Ridge | 0.000135500 | 1 | 1 | completa | Total; eventos.jsonl línea 5 |
| Inferencia | Ridge | 0.007864200 | 1 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | Lasso | 0.006697200 | 1 | 1 | completa | Total; eventos.jsonl línea 7 |
| Inferencia | Lasso | 0.005910700 | 1 | 1 | completa | Total; eventos.jsonl línea 8 |
| Inferencia | RandomForestRegressor | 0.027619100 | 1 | 1 | completa | Total; eventos.jsonl línea 9 |
| Inferencia | RandomForestRegressor | 0.027342600 | 1 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | XGBRegressor | 0.017853400 | 1 | 1 | completa | Total; eventos.jsonl línea 11 |
| Inferencia | XGBRegressor | 0.016149200 | 1 | 1 | completa | Total; eventos.jsonl línea 12 |
| Inferencia | DecisionTreeRegressor | 0.004024800 | 1 | 1 | completa | Total; eventos.jsonl línea 13 |
| Inferencia | DecisionTreeRegressor | 0.004001600 | 1 | 1 | completa | Total; eventos.jsonl línea 14 |
| Inferencia | LinearSVR | 0.005110700 | 1 | 1 | completa | Total; eventos.jsonl línea 15 |
| Inferencia | LinearSVR | 0.005916600 | 1 | 1 | completa | Total; eventos.jsonl línea 16 |
| Inferencia | LinearSVR | 0.006127500 | 1 | 1 | completa | Total; eventos.jsonl línea 17 |
| Inferencia | LinearSVR | 0.005066700 | 1 | 1 | completa | Total; eventos.jsonl línea 18 |
| Inferencia | LinearSVR | 0.005249100 | 1 | 1 | completa | Total; eventos.jsonl línea 19 |
| Inferencia | LinearSVR | 0.005132100 | 1 | 1 | completa | Total; eventos.jsonl línea 20 |
| Inferencia | DecisionTreeRegressor | 0.004013400 | 188 | 1 | completa | Total; eventos.jsonl línea 21 |
| Inferencia | DecisionTreeRegressor | 0.004119700 | 2 | 1 | completa | Total; eventos.jsonl línea 22 |
| Inferencia | LinearSVR | 0.006067600 | 1 | 1 | completa | Total; eventos.jsonl línea 23 |
| Inferencia | LinearSVR | 0.005584200 | 1 | 1 | completa | Total; eventos.jsonl línea 24 |
| Inferencia | LinearSVR | 0.008064100 | 1 | 1 | completa | Total; eventos.jsonl línea 25 |
| Inferencia | LinearSVR | 0.007955600 | 1 | 1 | completa | Total; eventos.jsonl línea 26 |
| Inferencia | XGBRegressor | 0.018190700 | 188 | 1 | completa | Total; eventos.jsonl línea 27 |
| Inferencia | XGBRegressor | 0.019504900 | 188 | 1 | completa | Total; eventos.jsonl línea 28 |
| Inferencia | XGBRegressor | 0.014442100 | 1 | 1 | completa | Total; eventos.jsonl línea 29 |
| Inferencia | XGBRegressor | 0.012845700 | 1 | 1 | completa | Total; eventos.jsonl línea 30 |
| Inferencia | XGBRegressor | 0.012128200 | 1 | 1 | completa | Total; eventos.jsonl línea 31 |
| Inferencia | XGBRegressor | 0.015487700 | 1000 | 1 | completa | Total; eventos.jsonl línea 32 |
| Entrenamiento/refit | Ridge | 0.001039000 | 1000 | 1 | completa | Total; eventos.jsonl línea 33 |
| Inferencia | Ridge | 0.000141300 | 1000 | 1 | completa | Total; eventos.jsonl línea 34 |
| Inferencia | Ridge | 0.000103200 | 1 | 1 | completa | Total; eventos.jsonl línea 35 |
| Inferencia | XGBRegressor | 0.011578200 | 1 | 1 | completa | Total; eventos.jsonl línea 36 |
| Inferencia | XGBRegressor | 0.011836900 | 1 | 1 | completa | Total; eventos.jsonl línea 37 |
| Inferencia | XGBRegressor | 0.016530700 | 1000 | 1 | completa | Total; eventos.jsonl línea 38 |
| Entrenamiento/refit | Ridge | 0.001025000 | 1000 | 1 | completa | Total; eventos.jsonl línea 39 |
| Inferencia | Ridge | 0.000151000 | 1000 | 1 | completa | Total; eventos.jsonl línea 40 |
| Inferencia | Ridge | 0.000099300 | 1 | 1 | completa | Total; eventos.jsonl línea 41 |
| Inferencia | XGBRegressor | 0.011296300 | 1 | 1 | completa | Total; eventos.jsonl línea 42 |
| Inferencia | XGBRegressor | 0.011927100 | 1 | 1 | completa | Total; eventos.jsonl línea 43 |
| Inferencia | XGBRegressor | 0.015742200 | 1000 | 1 | completa | Total; eventos.jsonl línea 44 |
| Entrenamiento/refit | Ridge | 0.001168100 | 1000 | 1 | completa | Total; eventos.jsonl línea 45 |
| Inferencia | Ridge | 0.000141300 | 1000 | 1 | completa | Total; eventos.jsonl línea 46 |
| Inferencia | Ridge | 0.000103800 | 1 | 1 | completa | Total; eventos.jsonl línea 47 |
| Inferencia | XGBRegressor | 0.011711700 | 1 | 1 | completa | Total; eventos.jsonl línea 48 |
| Inferencia | XGBRegressor | 0.016336300 | 1000 | 1 | completa | Total; eventos.jsonl línea 49 |
| Entrenamiento/refit | Ridge | 0.000998400 | 1000 | 1 | completa | Total; eventos.jsonl línea 50 |
| Inferencia | Ridge | 0.000191600 | 1000 | 1 | completa | Total; eventos.jsonl línea 51 |
| Inferencia | Ridge | 0.000106900 | 1 | 1 | completa | Total; eventos.jsonl línea 52 |
| Inferencia | XGBRegressor | 0.012236000 | 1 | 1 | completa | Total; eventos.jsonl línea 53 |
| Inferencia | XGBRegressor | 0.015937600 | 1000 | 1 | completa | Total; eventos.jsonl línea 54 |
| Entrenamiento/refit | Ridge | 0.001974400 | 1000 | 1 | completa | Total; eventos.jsonl línea 55 |
| Inferencia | Ridge | 0.000249600 | 1000 | 1 | completa | Total; eventos.jsonl línea 56 |
| Inferencia | Ridge | 0.000115300 | 1 | 1 | completa | Total; eventos.jsonl línea 57 |
| Inferencia | TransformedTargetRegressor | 0.015641900 | 1 | 1 | completa | Total; eventos.jsonl línea 58 |
| Inferencia | TransformedTargetRegressor | 0.010363900 | 188 | 1 | completa | Total; eventos.jsonl línea 59 |
| Total del experimento | Verificación/preparación · --tests | 23.174080700 | No aplica | 1 | completa | Total; eventos.jsonl línea 60 |

### Ejecución `20261018_100246_21e39a33`

- **Modelo/motivo:** Verificación/preparación · .\Dash\prepare_deployment.py.
- **Fecha/zona:** 2026-10-18T10:02:46.308749-05:00 a 2026-10-18T10:02:49.805361-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100246_21e39a33/metadata.json](tiempos/20261018_100246_21e39a33/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100246_21e39a33/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Total del experimento | Verificación/preparación · .\Dash\prepare_deployment.py | 3.494007000 | No aplica | 1 | completa | Total; eventos.jsonl línea 1 |

### Ejecución `20261018_100443_a8f6ec0f`

- **Modelo/motivo:** Verificación/preparación · .\Dash\prepare_deployment.py.
- **Fecha/zona:** 2026-10-18T10:04:43.270123-05:00 a 2026-10-18T10:04:46.910537-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100443_a8f6ec0f/metadata.json](tiempos/20261018_100443_a8f6ec0f/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100443_a8f6ec0f/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Total del experimento | Verificación/preparación · .\Dash\prepare_deployment.py | 3.637942300 | No aplica | 1 | completa | Total; eventos.jsonl línea 1 |

### Ejecución `20261018_100320_b8079482`

- **Modelo/motivo:** TransformedTargetRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T10:03:20.923059-05:00 a 2026-10-18T10:03:20.966555-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100320_b8079482/metadata.json](tiempos/20261018_100320_b8079482/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100320_b8079482/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.013185400 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TransformedTargetRegressor · inferencia de aplicación | 0.031263400 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |


### Ejecución `20261018_100320_ad9e3078`

- **Modelo/motivo:** TruncatedNewtonKernelRidgeRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T10:03:20.979901-05:00 a 2026-10-18T10:03:20.997647-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100320_ad9e3078/metadata.json](tiempos/20261018_100320_ad9e3078/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100320_ad9e3078/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.010864000 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TruncatedNewtonKernelRidgeRegressor · inferencia de aplicación | 0.016022900 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |


### Ejecución `20261018_100313_8be85269`

- **Modelo/motivo:** Verificación/preparación · .\RenderDeploy\Dash\validate_package.py.
- **Fecha/zona:** 2026-10-18T10:03:13.667999-05:00 a 2026-10-18T10:03:21.207048-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100313_8be85269/metadata.json](tiempos/20261018_100313_8be85269/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100313_8be85269/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | TransformedTargetRegressor | 0.021048100 | 188 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | TruncatedNewtonKernelRidgeRegressor | 0.010678200 | 188 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | TransformedTargetRegressor | 0.007252000 | 1 | 1 | completa | Total; eventos.jsonl línea 3 |
| Inferencia | TruncatedNewtonKernelRidgeRegressor | 0.005281600 | 1 | 1 | completa | Total; eventos.jsonl línea 4 |
| Inferencia | XGBRegressor | 0.020674900 | 1 | 1 | completa | Total; eventos.jsonl línea 5 |
| Inferencia | XGBRegressor | 0.017386600 | 1000 | 1 | completa | Total; eventos.jsonl línea 6 |
| Entrenamiento/refit | Ridge | 0.001257900 | 1000 | 1 | completa | Total; eventos.jsonl línea 7 |
| Inferencia | Ridge | 0.000153700 | 1000 | 1 | completa | Total; eventos.jsonl línea 8 |
| Inferencia | Ridge | 0.000119200 | 1 | 1 | completa | Total; eventos.jsonl línea 9 |
| Inferencia | XGBRegressor | 0.012601600 | 1 | 1 | completa | Total; eventos.jsonl línea 10 |
| Total del experimento | Verificación/preparación · .\RenderDeploy\Dash\validate_package.py | 7.538374600 | No aplica | 1 | completa | Total; eventos.jsonl línea 11 |


### Ejecución `20261018_100522_1456e8c8`

- **Modelo/motivo:** TransformedTargetRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T10:05:22.942923-05:00 a 2026-10-18T10:05:22.994987-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100522_1456e8c8/metadata.json](tiempos/20261018_100522_1456e8c8/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100522_1456e8c8/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.017599200 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TransformedTargetRegressor · inferencia de aplicación | 0.050582000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |


### Ejecución `20261018_100523_bcb63db1`

- **Modelo/motivo:** TruncatedNewtonKernelRidgeRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T10:05:23.015474-05:00 a 2026-10-18T10:05:23.043698-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100523_bcb63db1/metadata.json](tiempos/20261018_100523_bcb63db1/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100523_bcb63db1/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.020797400 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TruncatedNewtonKernelRidgeRegressor · inferencia de aplicación | 0.030862000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |


### Ejecución `20261018_100512_c1d9be9e`

- **Modelo/motivo:** Verificación/preparación · .\RenderDeploy\Dash\validate_package.py.
- **Fecha/zona:** 2026-10-18T10:05:12.049297-05:00 a 2026-10-18T10:05:23.367498-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_100512_c1d9be9e/metadata.json](tiempos/20261018_100512_c1d9be9e/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_100512_c1d9be9e/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | TransformedTargetRegressor | 0.032279400 | 188 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | TruncatedNewtonKernelRidgeRegressor | 0.018189400 | 188 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | TransformedTargetRegressor | 0.008925100 | 1 | 1 | completa | Total; eventos.jsonl línea 3 |
| Inferencia | TruncatedNewtonKernelRidgeRegressor | 0.010560900 | 1 | 1 | completa | Total; eventos.jsonl línea 4 |
| Inferencia | DecisionTreeRegressor | 0.007998200 | 188 | 1 | completa | Total; eventos.jsonl línea 5 |
| Inferencia | XGBRegressor | 0.026347400 | 1 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | XGBRegressor | 0.029027400 | 1000 | 1 | completa | Total; eventos.jsonl línea 7 |
| Entrenamiento/refit | Ridge | 0.001750300 | 1000 | 1 | completa | Total; eventos.jsonl línea 8 |
| Inferencia | Ridge | 0.000234200 | 1000 | 1 | completa | Total; eventos.jsonl línea 9 |
| Inferencia | Ridge | 0.000217400 | 1 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | XGBRegressor | 0.020232900 | 1 | 1 | completa | Total; eventos.jsonl línea 11 |
| Total del experimento | Verificación/preparación · .\RenderDeploy\Dash\validate_package.py | 11.313952200 | No aplica | 1 | completa | Total; eventos.jsonl línea 12 |

### Ejecución `20261018_102249_23ffd9b9`

- **Modelo/motivo:** Smoke de búsquedas · cinco estrategias.
- **Fecha/zona:** 2026-10-18T10:22:49.435341-05:00 a 2026-10-18T10:22:53.802640-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_102249_23ffd9b9/metadata.json](tiempos/20261018_102249_23ffd9b9/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_102249_23ffd9b9/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Búsqueda | decision_tree / smoke / Grid Search | 0.346537100 | 80 | 1 | completa | Total; eventos.jsonl línea 1 |
| Búsqueda | decision_tree / smoke / Random Search | 0.327468400 | 80 | 1 | completa | Total; eventos.jsonl línea 2 |
| Búsqueda | decision_tree / smoke / Bayesiana TPE | 0.687971000 | 80 | 1 | completa | Total; eventos.jsonl línea 3 |
| Búsqueda | decision_tree / smoke / Genética DEAP | 0.974824400 | 80 | 1 | completa | Total; eventos.jsonl línea 4 |
| Búsqueda | decision_tree / smoke / Successive Halving | 1.360378500 | 80 | 1 | completa | Total; eventos.jsonl línea 5 |
| Total del experimento | Smoke de búsquedas · cinco estrategias | 4.361547300 | No aplica | 1 | completa | Total; eventos.jsonl línea 6 |

### Ejecución `20261018_102325_af643f83`

- **Modelo/motivo:** SVM y seis clásicos · cinco búsquedas anidadas.
- **Fecha/zona:** 2026-10-18T10:23:25.441103-05:00 a 2026-10-18T11:21:30.022486-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_102325_af643f83/metadata.json](tiempos/20261018_102325_af643f83/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_102325_af643f83/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Búsqueda | svm / externo_1 / Grid Search | 14.289403000 | 1047 | 1 | completa | Total; eventos.jsonl línea 1 |
| Búsqueda | svm / externo_1 / Random Search | 2.637711700 | 1047 | 1 | completa | Total; eventos.jsonl línea 2 |
| Búsqueda | svm / externo_1 / Bayesiana TPE | 2.734520800 | 1047 | 1 | completa | Total; eventos.jsonl línea 3 |
| Búsqueda | svm / externo_1 / Genética DEAP | 2.503732100 | 1047 | 1 | completa | Total; eventos.jsonl línea 4 |
| Búsqueda | svm / externo_1 / Successive Halving | 3.545041500 | 1047 | 1 | completa | Total; eventos.jsonl línea 5 |
| Entrenamiento/refit | svm / externo 1 | 0.123707500 | 1047 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | svm / OOF fold 1 | 0.019688900 | 262 | 1 | completa | Total; eventos.jsonl línea 7 |
| Inferencia | svm / train fold 1 | 0.025422900 | 1047 | 1 | completa | Total; eventos.jsonl línea 8 |
| Entrenamiento/refit | svm / curva fold 1, fracción 0.25 | 0.031867100 | 260 | 1 | completa | Total; eventos.jsonl línea 9 |
| Inferencia | svm / curva train fold 1, fracción 0.25 | 0.015686700 | 260 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | svm / curva validación fold 1, fracción 0.25 | 0.027444000 | 262 | 1 | completa | Total; eventos.jsonl línea 11 |
| Entrenamiento/refit | svm / curva fold 1, fracción 0.5 | 0.033170600 | 520 | 1 | completa | Total; eventos.jsonl línea 12 |
| Inferencia | svm / curva train fold 1, fracción 0.5 | 0.028425100 | 520 | 1 | completa | Total; eventos.jsonl línea 13 |
| Inferencia | svm / curva validación fold 1, fracción 0.5 | 0.016213700 | 262 | 1 | completa | Total; eventos.jsonl línea 14 |
| Entrenamiento/refit | svm / curva fold 1, fracción 0.75 | 0.033927300 | 780 | 1 | completa | Total; eventos.jsonl línea 15 |
| Inferencia | svm / curva train fold 1, fracción 0.75 | 0.026640400 | 780 | 1 | completa | Total; eventos.jsonl línea 16 |
| Inferencia | svm / curva validación fold 1, fracción 0.75 | 0.014601200 | 262 | 1 | completa | Total; eventos.jsonl línea 17 |
| Inferencia | svm / curva train fold 1, fracción 1.0 | 0.026707000 | 1047 | 1 | completa | Total; eventos.jsonl línea 18 |
| Inferencia | svm / curva validación fold 1, fracción 1.0 | 0.025299000 | 262 | 1 | completa | Total; eventos.jsonl línea 19 |
| Búsqueda | svm / externo_2 / Grid Search | 15.320200700 | 1047 | 1 | completa | Total; eventos.jsonl línea 20 |
| Búsqueda | svm / externo_2 / Random Search | 2.530393900 | 1047 | 1 | completa | Total; eventos.jsonl línea 21 |
| Búsqueda | svm / externo_2 / Bayesiana TPE | 3.154776800 | 1047 | 1 | completa | Total; eventos.jsonl línea 22 |
| Búsqueda | svm / externo_2 / Genética DEAP | 2.506556200 | 1047 | 1 | completa | Total; eventos.jsonl línea 23 |
| Búsqueda | svm / externo_2 / Successive Halving | 3.078374600 | 1047 | 1 | completa | Total; eventos.jsonl línea 24 |
| Entrenamiento/refit | svm / externo 2 | 0.115576600 | 1047 | 1 | completa | Total; eventos.jsonl línea 25 |
| Inferencia | svm / OOF fold 2 | 0.014802000 | 262 | 1 | completa | Total; eventos.jsonl línea 26 |
| Inferencia | svm / train fold 2 | 0.014704200 | 1047 | 1 | completa | Total; eventos.jsonl línea 27 |
| Entrenamiento/refit | svm / curva fold 2, fracción 0.25 | 0.033106000 | 262 | 1 | completa | Total; eventos.jsonl línea 28 |
| Inferencia | svm / curva train fold 2, fracción 0.25 | 0.014236800 | 262 | 1 | completa | Total; eventos.jsonl línea 29 |
| Inferencia | svm / curva validación fold 2, fracción 0.25 | 0.016129500 | 262 | 1 | completa | Total; eventos.jsonl línea 30 |
| Entrenamiento/refit | svm / curva fold 2, fracción 0.5 | 0.041580800 | 524 | 1 | completa | Total; eventos.jsonl línea 31 |
| Inferencia | svm / curva train fold 2, fracción 0.5 | 0.014917400 | 524 | 1 | completa | Total; eventos.jsonl línea 32 |
| Inferencia | svm / curva validación fold 2, fracción 0.5 | 0.014627800 | 262 | 1 | completa | Total; eventos.jsonl línea 33 |
| Entrenamiento/refit | svm / curva fold 2, fracción 0.75 | 0.046028600 | 786 | 1 | completa | Total; eventos.jsonl línea 34 |
| Inferencia | svm / curva train fold 2, fracción 0.75 | 0.015240400 | 786 | 1 | completa | Total; eventos.jsonl línea 35 |
| Inferencia | svm / curva validación fold 2, fracción 0.75 | 0.015952200 | 262 | 1 | completa | Total; eventos.jsonl línea 36 |
| Inferencia | svm / curva train fold 2, fracción 1.0 | 0.014583100 | 1047 | 1 | completa | Total; eventos.jsonl línea 37 |
| Inferencia | svm / curva validación fold 2, fracción 1.0 | 0.015061200 | 262 | 1 | completa | Total; eventos.jsonl línea 38 |
| Búsqueda | svm / externo_3 / Grid Search | 14.165883900 | 1047 | 1 | completa | Total; eventos.jsonl línea 39 |
| Búsqueda | svm / externo_3 / Random Search | 2.464991900 | 1047 | 1 | completa | Total; eventos.jsonl línea 40 |
| Búsqueda | svm / externo_3 / Bayesiana TPE | 2.826137000 | 1047 | 1 | completa | Total; eventos.jsonl línea 41 |
| Búsqueda | svm / externo_3 / Genética DEAP | 2.521047000 | 1047 | 1 | completa | Total; eventos.jsonl línea 42 |
| Búsqueda | svm / externo_3 / Successive Halving | 3.205966400 | 1047 | 1 | completa | Total; eventos.jsonl línea 43 |
| Entrenamiento/refit | svm / externo 3 | 0.109920400 | 1047 | 1 | completa | Total; eventos.jsonl línea 44 |
| Inferencia | svm / OOF fold 3 | 0.014588800 | 262 | 1 | completa | Total; eventos.jsonl línea 45 |
| Inferencia | svm / train fold 3 | 0.024962200 | 1047 | 1 | completa | Total; eventos.jsonl línea 46 |
| Entrenamiento/refit | svm / curva fold 3, fracción 0.25 | 0.018318200 | 262 | 1 | completa | Total; eventos.jsonl línea 47 |
| Inferencia | svm / curva train fold 3, fracción 0.25 | 0.014610300 | 262 | 1 | completa | Total; eventos.jsonl línea 48 |
| Inferencia | svm / curva validación fold 3, fracción 0.25 | 0.014767900 | 262 | 1 | completa | Total; eventos.jsonl línea 49 |
| Entrenamiento/refit | svm / curva fold 3, fracción 0.5 | 0.029672900 | 526 | 1 | completa | Total; eventos.jsonl línea 50 |
| Inferencia | svm / curva train fold 3, fracción 0.5 | 0.016177600 | 526 | 1 | completa | Total; eventos.jsonl línea 51 |
| Inferencia | svm / curva validación fold 3, fracción 0.5 | 0.014951100 | 262 | 1 | completa | Total; eventos.jsonl línea 52 |
| Entrenamiento/refit | svm / curva fold 3, fracción 0.75 | 0.029096600 | 786 | 1 | completa | Total; eventos.jsonl línea 53 |
| Inferencia | svm / curva train fold 3, fracción 0.75 | 0.014615300 | 786 | 1 | completa | Total; eventos.jsonl línea 54 |
| Inferencia | svm / curva validación fold 3, fracción 0.75 | 0.014687900 | 262 | 1 | completa | Total; eventos.jsonl línea 55 |
| Inferencia | svm / curva train fold 3, fracción 1.0 | 0.015206700 | 1047 | 1 | completa | Total; eventos.jsonl línea 56 |
| Inferencia | svm / curva validación fold 3, fracción 1.0 | 0.014611900 | 262 | 1 | completa | Total; eventos.jsonl línea 57 |
| Búsqueda | svm / externo_4 / Grid Search | 13.806357500 | 1047 | 1 | completa | Total; eventos.jsonl línea 58 |
| Búsqueda | svm / externo_4 / Random Search | 2.689651300 | 1047 | 1 | completa | Total; eventos.jsonl línea 59 |
| Búsqueda | svm / externo_4 / Bayesiana TPE | 3.003953100 | 1047 | 1 | completa | Total; eventos.jsonl línea 60 |
| Búsqueda | svm / externo_4 / Genética DEAP | 2.852850400 | 1047 | 1 | completa | Total; eventos.jsonl línea 61 |
| Búsqueda | svm / externo_4 / Successive Halving | 3.416978500 | 1047 | 1 | completa | Total; eventos.jsonl línea 62 |
| Entrenamiento/refit | svm / externo 4 | 0.101349500 | 1047 | 1 | completa | Total; eventos.jsonl línea 63 |
| Inferencia | svm / OOF fold 4 | 0.014927400 | 262 | 1 | completa | Total; eventos.jsonl línea 64 |
| Inferencia | svm / train fold 4 | 0.025395500 | 1047 | 1 | completa | Total; eventos.jsonl línea 65 |
| Entrenamiento/refit | svm / curva fold 4, fracción 0.25 | 0.029123800 | 261 | 1 | completa | Total; eventos.jsonl línea 66 |
| Inferencia | svm / curva train fold 4, fracción 0.25 | 0.013732400 | 261 | 1 | completa | Total; eventos.jsonl línea 67 |
| Inferencia | svm / curva validación fold 4, fracción 0.25 | 0.014345100 | 262 | 1 | completa | Total; eventos.jsonl línea 68 |
| Entrenamiento/refit | svm / curva fold 4, fracción 0.5 | 0.030097700 | 523 | 1 | completa | Total; eventos.jsonl línea 69 |
| Inferencia | svm / curva train fold 4, fracción 0.5 | 0.014923500 | 523 | 1 | completa | Total; eventos.jsonl línea 70 |
| Inferencia | svm / curva validación fold 4, fracción 0.5 | 0.015900600 | 262 | 1 | completa | Total; eventos.jsonl línea 71 |
| Entrenamiento/refit | svm / curva fold 4, fracción 0.75 | 0.032062600 | 783 | 1 | completa | Total; eventos.jsonl línea 72 |
| Inferencia | svm / curva train fold 4, fracción 0.75 | 0.017500500 | 783 | 1 | completa | Total; eventos.jsonl línea 73 |
| Inferencia | svm / curva validación fold 4, fracción 0.75 | 0.015549400 | 262 | 1 | completa | Total; eventos.jsonl línea 74 |
| Inferencia | svm / curva train fold 4, fracción 1.0 | 0.026105200 | 1047 | 1 | completa | Total; eventos.jsonl línea 75 |
| Inferencia | svm / curva validación fold 4, fracción 1.0 | 0.015190600 | 262 | 1 | completa | Total; eventos.jsonl línea 76 |
| Búsqueda | svm / externo_5 / Grid Search | 15.167647400 | 1048 | 1 | completa | Total; eventos.jsonl línea 77 |
| Búsqueda | svm / externo_5 / Random Search | 2.458613200 | 1048 | 1 | completa | Total; eventos.jsonl línea 78 |
| Búsqueda | svm / externo_5 / Bayesiana TPE | 2.802861300 | 1048 | 1 | completa | Total; eventos.jsonl línea 79 |
| Búsqueda | svm / externo_5 / Genética DEAP | 2.484437900 | 1048 | 1 | completa | Total; eventos.jsonl línea 80 |
| Búsqueda | svm / externo_5 / Successive Halving | 3.628294300 | 1048 | 1 | completa | Total; eventos.jsonl línea 81 |
| Entrenamiento/refit | svm / externo 5 | 0.123768500 | 1048 | 1 | completa | Total; eventos.jsonl línea 82 |
| Inferencia | svm / OOF fold 5 | 0.014926300 | 261 | 1 | completa | Total; eventos.jsonl línea 83 |
| Inferencia | svm / train fold 5 | 0.014625600 | 1048 | 1 | completa | Total; eventos.jsonl línea 84 |
| Entrenamiento/refit | svm / curva fold 5, fracción 0.25 | 0.018317800 | 263 | 1 | completa | Total; eventos.jsonl línea 85 |
| Inferencia | svm / curva train fold 5, fracción 0.25 | 0.015465500 | 263 | 1 | completa | Total; eventos.jsonl línea 86 |
| Inferencia | svm / curva validación fold 5, fracción 0.25 | 0.015356100 | 261 | 1 | completa | Total; eventos.jsonl línea 87 |
| Entrenamiento/refit | svm / curva fold 5, fracción 0.5 | 0.029321100 | 524 | 1 | completa | Total; eventos.jsonl línea 88 |
| Inferencia | svm / curva train fold 5, fracción 0.5 | 0.016498800 | 524 | 1 | completa | Total; eventos.jsonl línea 89 |
| Inferencia | svm / curva validación fold 5, fracción 0.5 | 0.025611500 | 261 | 1 | completa | Total; eventos.jsonl línea 90 |
| Entrenamiento/refit | svm / curva fold 5, fracción 0.75 | 0.031454200 | 786 | 1 | completa | Total; eventos.jsonl línea 91 |
| Inferencia | svm / curva train fold 5, fracción 0.75 | 0.015468700 | 786 | 1 | completa | Total; eventos.jsonl línea 92 |
| Inferencia | svm / curva validación fold 5, fracción 0.75 | 0.015313100 | 261 | 1 | completa | Total; eventos.jsonl línea 93 |
| Inferencia | svm / curva train fold 5, fracción 1.0 | 0.016094700 | 1048 | 1 | completa | Total; eventos.jsonl línea 94 |
| Inferencia | svm / curva validación fold 5, fracción 1.0 | 0.014847200 | 261 | 1 | completa | Total; eventos.jsonl línea 95 |
| Búsqueda | svm / final_train / Grid Search | 15.472892000 | 1309 | 1 | completa | Total; eventos.jsonl línea 96 |
| Búsqueda | svm / final_train / Random Search | 2.764402700 | 1309 | 1 | completa | Total; eventos.jsonl línea 97 |
| Búsqueda | svm / final_train / Bayesiana TPE | 3.220271500 | 1309 | 1 | completa | Total; eventos.jsonl línea 98 |
| Búsqueda | svm / final_train / Genética DEAP | 2.785138000 | 1309 | 1 | completa | Total; eventos.jsonl línea 99 |
| Búsqueda | svm / final_train / Successive Halving | 3.696314800 | 1309 | 1 | completa | Total; eventos.jsonl línea 100 |
| Entrenamiento/refit | svm / final train | 0.087807900 | 1309 | 1 | completa | Total; eventos.jsonl línea 101 |
| Inferencia | svm / train final | 0.026939000 | 1309 | 1 | completa | Total; eventos.jsonl línea 102 |
| Búsqueda | knn / externo_1 / Grid Search | 11.319830900 | 1047 | 1 | completa | Total; eventos.jsonl línea 103 |
| Búsqueda | knn / externo_1 / Random Search | 2.001233500 | 1047 | 1 | completa | Total; eventos.jsonl línea 104 |
| Búsqueda | knn / externo_1 / Bayesiana TPE | 2.651048400 | 1047 | 1 | completa | Total; eventos.jsonl línea 105 |
| Búsqueda | knn / externo_1 / Genética DEAP | 1.169360200 | 1047 | 1 | completa | Total; eventos.jsonl línea 106 |
| Búsqueda | knn / externo_1 / Successive Halving | 3.099848800 | 1047 | 1 | completa | Total; eventos.jsonl línea 107 |
| Entrenamiento/refit | knn / externo 1 | 0.082303400 | 1047 | 1 | completa | Total; eventos.jsonl línea 108 |
| Inferencia | knn / OOF fold 1 | 0.029850600 | 262 | 1 | completa | Total; eventos.jsonl línea 109 |
| Inferencia | knn / train fold 1 | 0.039543400 | 1047 | 1 | completa | Total; eventos.jsonl línea 110 |
| Búsqueda | knn / externo_2 / Grid Search | 11.006271700 | 1047 | 1 | completa | Total; eventos.jsonl línea 111 |
| Búsqueda | knn / externo_2 / Random Search | 2.017983700 | 1047 | 1 | completa | Total; eventos.jsonl línea 112 |
| Búsqueda | knn / externo_2 / Bayesiana TPE | 2.674665100 | 1047 | 1 | completa | Total; eventos.jsonl línea 113 |
| Búsqueda | knn / externo_2 / Genética DEAP | 1.215046600 | 1047 | 1 | completa | Total; eventos.jsonl línea 114 |
| Búsqueda | knn / externo_2 / Successive Halving | 3.252874700 | 1047 | 1 | completa | Total; eventos.jsonl línea 115 |
| Entrenamiento/refit | knn / externo 2 | 0.099041500 | 1047 | 1 | completa | Total; eventos.jsonl línea 116 |
| Inferencia | knn / OOF fold 2 | 0.030633200 | 262 | 1 | completa | Total; eventos.jsonl línea 117 |
| Inferencia | knn / train fold 2 | 0.100696600 | 1047 | 1 | completa | Total; eventos.jsonl línea 118 |
| Búsqueda | knn / externo_3 / Grid Search | 11.508604600 | 1047 | 1 | completa | Total; eventos.jsonl línea 119 |
| Búsqueda | knn / externo_3 / Random Search | 2.114946500 | 1047 | 1 | completa | Total; eventos.jsonl línea 120 |
| Búsqueda | knn / externo_3 / Bayesiana TPE | 2.838932200 | 1047 | 1 | completa | Total; eventos.jsonl línea 121 |
| Búsqueda | knn / externo_3 / Genética DEAP | 1.308302900 | 1047 | 1 | completa | Total; eventos.jsonl línea 122 |
| Búsqueda | knn / externo_3 / Successive Halving | 3.163380100 | 1047 | 1 | completa | Total; eventos.jsonl línea 123 |
| Entrenamiento/refit | knn / externo 3 | 0.090524600 | 1047 | 1 | completa | Total; eventos.jsonl línea 124 |
| Inferencia | knn / OOF fold 3 | 0.016685600 | 262 | 1 | completa | Total; eventos.jsonl línea 125 |
| Inferencia | knn / train fold 3 | 0.037996500 | 1047 | 1 | completa | Total; eventos.jsonl línea 126 |
| Búsqueda | knn / externo_4 / Grid Search | 11.432216800 | 1047 | 1 | completa | Total; eventos.jsonl línea 127 |
| Búsqueda | knn / externo_4 / Random Search | 2.160821500 | 1047 | 1 | completa | Total; eventos.jsonl línea 128 |
| Búsqueda | knn / externo_4 / Bayesiana TPE | 2.687157800 | 1047 | 1 | completa | Total; eventos.jsonl línea 129 |
| Búsqueda | knn / externo_4 / Genética DEAP | 1.205302000 | 1047 | 1 | completa | Total; eventos.jsonl línea 130 |
| Búsqueda | knn / externo_4 / Successive Halving | 2.316861700 | 1047 | 1 | completa | Total; eventos.jsonl línea 131 |
| Entrenamiento/refit | knn / externo 4 | 0.081092300 | 1047 | 1 | completa | Total; eventos.jsonl línea 132 |
| Inferencia | knn / OOF fold 4 | 0.029275100 | 262 | 1 | completa | Total; eventos.jsonl línea 133 |
| Inferencia | knn / train fold 4 | 0.075233800 | 1047 | 1 | completa | Total; eventos.jsonl línea 134 |
| Búsqueda | knn / externo_5 / Grid Search | 8.006078300 | 1048 | 1 | completa | Total; eventos.jsonl línea 135 |
| Búsqueda | knn / externo_5 / Random Search | 1.278426100 | 1048 | 1 | completa | Total; eventos.jsonl línea 136 |
| Búsqueda | knn / externo_5 / Bayesiana TPE | 1.651980100 | 1048 | 1 | completa | Total; eventos.jsonl línea 137 |
| Búsqueda | knn / externo_5 / Genética DEAP | 0.746193000 | 1048 | 1 | completa | Total; eventos.jsonl línea 138 |
| Búsqueda | knn / externo_5 / Successive Halving | 1.978427200 | 1048 | 1 | completa | Total; eventos.jsonl línea 139 |
| Entrenamiento/refit | knn / externo 5 | 0.075943500 | 1048 | 1 | completa | Total; eventos.jsonl línea 140 |
| Inferencia | knn / OOF fold 5 | 0.028701200 | 261 | 1 | completa | Total; eventos.jsonl línea 141 |
| Inferencia | knn / train fold 5 | 0.071159600 | 1048 | 1 | completa | Total; eventos.jsonl línea 142 |
| Búsqueda | knn / final_train / Grid Search | 8.189257700 | 1309 | 1 | completa | Total; eventos.jsonl línea 143 |
| Búsqueda | knn / final_train / Random Search | 1.352960700 | 1309 | 1 | completa | Total; eventos.jsonl línea 144 |
| Búsqueda | knn / final_train / Bayesiana TPE | 1.749728900 | 1309 | 1 | completa | Total; eventos.jsonl línea 145 |
| Búsqueda | knn / final_train / Genética DEAP | 1.207473600 | 1309 | 1 | completa | Total; eventos.jsonl línea 146 |
| Búsqueda | knn / final_train / Successive Halving | 2.969481200 | 1309 | 1 | completa | Total; eventos.jsonl línea 147 |
| Entrenamiento/refit | knn / final train | 0.062696300 | 1309 | 1 | completa | Total; eventos.jsonl línea 148 |
| Inferencia | knn / train final | 0.046162100 | 1309 | 1 | completa | Total; eventos.jsonl línea 149 |
| Búsqueda | ridge / externo_1 / Grid Search | 7.312695000 | 1047 | 1 | completa | Total; eventos.jsonl línea 150 |
| Búsqueda | ridge / externo_1 / Random Search | 1.647963400 | 1047 | 1 | completa | Total; eventos.jsonl línea 151 |
| Búsqueda | ridge / externo_1 / Bayesiana TPE | 2.053436100 | 1047 | 1 | completa | Total; eventos.jsonl línea 152 |
| Búsqueda | ridge / externo_1 / Genética DEAP | 1.240221100 | 1047 | 1 | completa | Total; eventos.jsonl línea 153 |
| Búsqueda | ridge / externo_1 / Successive Halving | 2.754861300 | 1047 | 1 | completa | Total; eventos.jsonl línea 154 |
| Entrenamiento/refit | ridge / externo 1 | 0.075831100 | 1047 | 1 | completa | Total; eventos.jsonl línea 155 |
| Inferencia | ridge / OOF fold 1 | 0.014401800 | 262 | 1 | completa | Total; eventos.jsonl línea 156 |
| Inferencia | ridge / train fold 1 | 0.025461300 | 1047 | 1 | completa | Total; eventos.jsonl línea 157 |
| Búsqueda | ridge / externo_2 / Grid Search | 7.178542900 | 1047 | 1 | completa | Total; eventos.jsonl línea 158 |
| Búsqueda | ridge / externo_2 / Random Search | 1.589243000 | 1047 | 1 | completa | Total; eventos.jsonl línea 159 |
| Búsqueda | ridge / externo_2 / Bayesiana TPE | 1.998812200 | 1047 | 1 | completa | Total; eventos.jsonl línea 160 |
| Búsqueda | ridge / externo_2 / Genética DEAP | 1.206707800 | 1047 | 1 | completa | Total; eventos.jsonl línea 161 |
| Búsqueda | ridge / externo_2 / Successive Halving | 2.689993700 | 1047 | 1 | completa | Total; eventos.jsonl línea 162 |
| Entrenamiento/refit | ridge / externo 2 | 0.089510200 | 1047 | 1 | completa | Total; eventos.jsonl línea 163 |
| Inferencia | ridge / OOF fold 2 | 0.014090800 | 262 | 1 | completa | Total; eventos.jsonl línea 164 |
| Inferencia | ridge / train fold 2 | 0.025259900 | 1047 | 1 | completa | Total; eventos.jsonl línea 165 |
| Búsqueda | ridge / externo_3 / Grid Search | 7.189547500 | 1047 | 1 | completa | Total; eventos.jsonl línea 166 |
| Búsqueda | ridge / externo_3 / Random Search | 1.557755500 | 1047 | 1 | completa | Total; eventos.jsonl línea 167 |
| Búsqueda | ridge / externo_3 / Bayesiana TPE | 2.010284600 | 1047 | 1 | completa | Total; eventos.jsonl línea 168 |
| Búsqueda | ridge / externo_3 / Genética DEAP | 1.177687400 | 1047 | 1 | completa | Total; eventos.jsonl línea 169 |
| Búsqueda | ridge / externo_3 / Successive Halving | 2.678978200 | 1047 | 1 | completa | Total; eventos.jsonl línea 170 |
| Entrenamiento/refit | ridge / externo 3 | 0.089026400 | 1047 | 1 | completa | Total; eventos.jsonl línea 171 |
| Inferencia | ridge / OOF fold 3 | 0.014334300 | 262 | 1 | completa | Total; eventos.jsonl línea 172 |
| Inferencia | ridge / train fold 3 | 0.015504800 | 1047 | 1 | completa | Total; eventos.jsonl línea 173 |
| Búsqueda | ridge / externo_4 / Grid Search | 7.355604200 | 1047 | 1 | completa | Total; eventos.jsonl línea 174 |
| Búsqueda | ridge / externo_4 / Random Search | 1.598985300 | 1047 | 1 | completa | Total; eventos.jsonl línea 175 |
| Búsqueda | ridge / externo_4 / Bayesiana TPE | 1.962731200 | 1047 | 1 | completa | Total; eventos.jsonl línea 176 |
| Búsqueda | ridge / externo_4 / Genética DEAP | 1.194304300 | 1047 | 1 | completa | Total; eventos.jsonl línea 177 |
| Búsqueda | ridge / externo_4 / Successive Halving | 2.635260200 | 1047 | 1 | completa | Total; eventos.jsonl línea 178 |
| Entrenamiento/refit | ridge / externo 4 | 0.090972000 | 1047 | 1 | completa | Total; eventos.jsonl línea 179 |
| Inferencia | ridge / OOF fold 4 | 0.024975300 | 262 | 1 | completa | Total; eventos.jsonl línea 180 |
| Inferencia | ridge / train fold 4 | 0.025648700 | 1047 | 1 | completa | Total; eventos.jsonl línea 181 |
| Búsqueda | ridge / externo_5 / Grid Search | 7.238022800 | 1048 | 1 | completa | Total; eventos.jsonl línea 182 |
| Búsqueda | ridge / externo_5 / Random Search | 1.594774100 | 1048 | 1 | completa | Total; eventos.jsonl línea 183 |
| Búsqueda | ridge / externo_5 / Bayesiana TPE | 2.022320200 | 1048 | 1 | completa | Total; eventos.jsonl línea 184 |
| Búsqueda | ridge / externo_5 / Genética DEAP | 1.207797200 | 1048 | 1 | completa | Total; eventos.jsonl línea 185 |
| Búsqueda | ridge / externo_5 / Successive Halving | 2.733956000 | 1048 | 1 | completa | Total; eventos.jsonl línea 186 |
| Entrenamiento/refit | ridge / externo 5 | 0.080703500 | 1048 | 1 | completa | Total; eventos.jsonl línea 187 |
| Inferencia | ridge / OOF fold 5 | 0.014355000 | 261 | 1 | completa | Total; eventos.jsonl línea 188 |
| Inferencia | ridge / train fold 5 | 0.014684400 | 1048 | 1 | completa | Total; eventos.jsonl línea 189 |
| Búsqueda | ridge / final_train / Grid Search | 6.715950900 | 1309 | 1 | completa | Total; eventos.jsonl línea 190 |
| Búsqueda | ridge / final_train / Random Search | 1.078659100 | 1309 | 1 | completa | Total; eventos.jsonl línea 191 |
| Búsqueda | ridge / final_train / Bayesiana TPE | 1.402367000 | 1309 | 1 | completa | Total; eventos.jsonl línea 192 |
| Búsqueda | ridge / final_train / Genética DEAP | 0.840983400 | 1309 | 1 | completa | Total; eventos.jsonl línea 193 |
| Búsqueda | ridge / final_train / Successive Halving | 1.847793300 | 1309 | 1 | completa | Total; eventos.jsonl línea 194 |
| Entrenamiento/refit | ridge / final train | 0.067238000 | 1309 | 1 | completa | Total; eventos.jsonl línea 195 |
| Inferencia | ridge / train final | 0.025438800 | 1309 | 1 | completa | Total; eventos.jsonl línea 196 |
| Búsqueda | lasso / externo_1 / Grid Search | 6.190495900 | 1047 | 1 | completa | Total; eventos.jsonl línea 197 |
| Búsqueda | lasso / externo_1 / Random Search | 1.198897400 | 1047 | 1 | completa | Total; eventos.jsonl línea 198 |
| Búsqueda | lasso / externo_1 / Bayesiana TPE | 1.623806000 | 1047 | 1 | completa | Total; eventos.jsonl línea 199 |
| Búsqueda | lasso / externo_1 / Genética DEAP | 0.934086100 | 1047 | 1 | completa | Total; eventos.jsonl línea 200 |
| Búsqueda | lasso / externo_1 / Successive Halving | 1.868813300 | 1047 | 1 | completa | Total; eventos.jsonl línea 201 |
| Entrenamiento/refit | lasso / externo 1 | 0.077112300 | 1047 | 1 | completa | Total; eventos.jsonl línea 202 |
| Inferencia | lasso / OOF fold 1 | 0.014527200 | 262 | 1 | completa | Total; eventos.jsonl línea 203 |
| Inferencia | lasso / train fold 1 | 0.014774400 | 1047 | 1 | completa | Total; eventos.jsonl línea 204 |
| Búsqueda | lasso / externo_2 / Grid Search | 5.908639200 | 1047 | 1 | completa | Total; eventos.jsonl línea 205 |
| Búsqueda | lasso / externo_2 / Random Search | 1.166318500 | 1047 | 1 | completa | Total; eventos.jsonl línea 206 |
| Búsqueda | lasso / externo_2 / Bayesiana TPE | 1.659774200 | 1047 | 1 | completa | Total; eventos.jsonl línea 207 |
| Búsqueda | lasso / externo_2 / Genética DEAP | 1.029282800 | 1047 | 1 | completa | Total; eventos.jsonl línea 208 |
| Búsqueda | lasso / externo_2 / Successive Halving | 1.889483300 | 1047 | 1 | completa | Total; eventos.jsonl línea 209 |
| Entrenamiento/refit | lasso / externo 2 | 0.091153000 | 1047 | 1 | completa | Total; eventos.jsonl línea 210 |
| Inferencia | lasso / OOF fold 2 | 0.014950600 | 262 | 1 | completa | Total; eventos.jsonl línea 211 |
| Inferencia | lasso / train fold 2 | 0.014564700 | 1047 | 1 | completa | Total; eventos.jsonl línea 212 |
| Búsqueda | lasso / externo_3 / Grid Search | 6.209553500 | 1047 | 1 | completa | Total; eventos.jsonl línea 213 |
| Búsqueda | lasso / externo_3 / Random Search | 1.259756700 | 1047 | 1 | completa | Total; eventos.jsonl línea 214 |
| Búsqueda | lasso / externo_3 / Bayesiana TPE | 1.796638100 | 1047 | 1 | completa | Total; eventos.jsonl línea 215 |
| Búsqueda | lasso / externo_3 / Genética DEAP | 0.947073300 | 1047 | 1 | completa | Total; eventos.jsonl línea 216 |
| Búsqueda | lasso / externo_3 / Successive Halving | 1.908952700 | 1047 | 1 | completa | Total; eventos.jsonl línea 217 |
| Entrenamiento/refit | lasso / externo 3 | 0.079419900 | 1047 | 1 | completa | Total; eventos.jsonl línea 218 |
| Inferencia | lasso / OOF fold 3 | 0.014568400 | 262 | 1 | completa | Total; eventos.jsonl línea 219 |
| Inferencia | lasso / train fold 3 | 0.014144100 | 1047 | 1 | completa | Total; eventos.jsonl línea 220 |
| Búsqueda | lasso / externo_4 / Grid Search | 6.145370400 | 1047 | 1 | completa | Total; eventos.jsonl línea 221 |
| Búsqueda | lasso / externo_4 / Random Search | 1.164605800 | 1047 | 1 | completa | Total; eventos.jsonl línea 222 |
| Búsqueda | lasso / externo_4 / Bayesiana TPE | 1.797869300 | 1047 | 1 | completa | Total; eventos.jsonl línea 223 |
| Búsqueda | lasso / externo_4 / Genética DEAP | 0.974140600 | 1047 | 1 | completa | Total; eventos.jsonl línea 224 |
| Búsqueda | lasso / externo_4 / Successive Halving | 2.020665800 | 1047 | 1 | completa | Total; eventos.jsonl línea 225 |
| Entrenamiento/refit | lasso / externo 4 | 0.086669500 | 1047 | 1 | completa | Total; eventos.jsonl línea 226 |
| Inferencia | lasso / OOF fold 4 | 0.014300100 | 262 | 1 | completa | Total; eventos.jsonl línea 227 |
| Inferencia | lasso / train fold 4 | 0.024815800 | 1047 | 1 | completa | Total; eventos.jsonl línea 228 |
| Búsqueda | lasso / externo_5 / Grid Search | 6.112855800 | 1048 | 1 | completa | Total; eventos.jsonl línea 229 |
| Búsqueda | lasso / externo_5 / Random Search | 1.271649800 | 1048 | 1 | completa | Total; eventos.jsonl línea 230 |
| Búsqueda | lasso / externo_5 / Bayesiana TPE | 1.824438000 | 1048 | 1 | completa | Total; eventos.jsonl línea 231 |
| Búsqueda | lasso / externo_5 / Genética DEAP | 1.060823100 | 1048 | 1 | completa | Total; eventos.jsonl línea 232 |
| Búsqueda | lasso / externo_5 / Successive Halving | 1.932744000 | 1048 | 1 | completa | Total; eventos.jsonl línea 233 |
| Entrenamiento/refit | lasso / externo 5 | 0.098057100 | 1048 | 1 | completa | Total; eventos.jsonl línea 234 |
| Inferencia | lasso / OOF fold 5 | 0.015367200 | 261 | 1 | completa | Total; eventos.jsonl línea 235 |
| Inferencia | lasso / train fold 5 | 0.016283200 | 1048 | 1 | completa | Total; eventos.jsonl línea 236 |
| Búsqueda | lasso / final_train / Grid Search | 6.178569800 | 1309 | 1 | completa | Total; eventos.jsonl línea 237 |
| Búsqueda | lasso / final_train / Random Search | 1.256717800 | 1309 | 1 | completa | Total; eventos.jsonl línea 238 |
| Búsqueda | lasso / final_train / Bayesiana TPE | 1.963792800 | 1309 | 1 | completa | Total; eventos.jsonl línea 239 |
| Búsqueda | lasso / final_train / Genética DEAP | 1.160061800 | 1309 | 1 | completa | Total; eventos.jsonl línea 240 |
| Búsqueda | lasso / final_train / Successive Halving | 2.005502300 | 1309 | 1 | completa | Total; eventos.jsonl línea 241 |
| Entrenamiento/refit | lasso / final train | 0.111894100 | 1309 | 1 | completa | Total; eventos.jsonl línea 242 |
| Inferencia | lasso / train final | 0.015672100 | 1309 | 1 | completa | Total; eventos.jsonl línea 243 |
| Búsqueda | forest / externo_1 / Grid Search | 38.783678000 | 1047 | 1 | completa | Total; eventos.jsonl línea 244 |
| Búsqueda | forest / externo_1 / Random Search | 29.464978700 | 1047 | 1 | completa | Total; eventos.jsonl línea 245 |
| Búsqueda | forest / externo_1 / Bayesiana TPE | 30.483290300 | 1047 | 1 | completa | Total; eventos.jsonl línea 246 |
| Búsqueda | forest / externo_1 / Genética DEAP | 23.992240800 | 1047 | 1 | completa | Total; eventos.jsonl línea 247 |
| Búsqueda | forest / externo_1 / Successive Halving | 25.540807400 | 1047 | 1 | completa | Total; eventos.jsonl línea 248 |
| Entrenamiento/refit | forest / externo 1 | 0.815601300 | 1047 | 1 | completa | Total; eventos.jsonl línea 249 |
| Inferencia | forest / OOF fold 1 | 0.028800500 | 262 | 1 | completa | Total; eventos.jsonl línea 250 |
| Inferencia | forest / train fold 1 | 0.037561900 | 1047 | 1 | completa | Total; eventos.jsonl línea 251 |
| Búsqueda | forest / externo_2 / Grid Search | 30.534346300 | 1047 | 1 | completa | Total; eventos.jsonl línea 252 |
| Búsqueda | forest / externo_2 / Random Search | 18.219996500 | 1047 | 1 | completa | Total; eventos.jsonl línea 253 |
| Búsqueda | forest / externo_2 / Bayesiana TPE | 32.873182600 | 1047 | 1 | completa | Total; eventos.jsonl línea 254 |
| Búsqueda | forest / externo_2 / Genética DEAP | 22.923928600 | 1047 | 1 | completa | Total; eventos.jsonl línea 255 |
| Búsqueda | forest / externo_2 / Successive Halving | 31.230661800 | 1047 | 1 | completa | Total; eventos.jsonl línea 256 |
| Entrenamiento/refit | forest / externo 2 | 1.158598500 | 1047 | 1 | completa | Total; eventos.jsonl línea 257 |
| Inferencia | forest / OOF fold 2 | 0.040264600 | 262 | 1 | completa | Total; eventos.jsonl línea 258 |
| Inferencia | forest / train fold 2 | 0.059900400 | 1047 | 1 | completa | Total; eventos.jsonl línea 259 |
| Búsqueda | forest / externo_3 / Grid Search | 29.969504100 | 1047 | 1 | completa | Total; eventos.jsonl línea 260 |
| Búsqueda | forest / externo_3 / Random Search | 18.471003500 | 1047 | 1 | completa | Total; eventos.jsonl línea 261 |
| Búsqueda | forest / externo_3 / Bayesiana TPE | 21.427654000 | 1047 | 1 | completa | Total; eventos.jsonl línea 262 |
| Búsqueda | forest / externo_3 / Genética DEAP | 13.204713400 | 1047 | 1 | completa | Total; eventos.jsonl línea 263 |
| Búsqueda | forest / externo_3 / Successive Halving | 21.430015800 | 1047 | 1 | completa | Total; eventos.jsonl línea 264 |
| Entrenamiento/refit | forest / externo 3 | 0.742551000 | 1047 | 1 | completa | Total; eventos.jsonl línea 265 |
| Inferencia | forest / OOF fold 3 | 0.028258200 | 262 | 1 | completa | Total; eventos.jsonl línea 266 |
| Inferencia | forest / train fold 3 | 0.038116100 | 1047 | 1 | completa | Total; eventos.jsonl línea 267 |
| Búsqueda | forest / externo_4 / Grid Search | 29.379085800 | 1047 | 1 | completa | Total; eventos.jsonl línea 268 |
| Búsqueda | forest / externo_4 / Random Search | 18.220393700 | 1047 | 1 | completa | Total; eventos.jsonl línea 269 |
| Búsqueda | forest / externo_4 / Bayesiana TPE | 20.029745600 | 1047 | 1 | completa | Total; eventos.jsonl línea 270 |
| Búsqueda | forest / externo_4 / Genética DEAP | 13.190856900 | 1047 | 1 | completa | Total; eventos.jsonl línea 271 |
| Búsqueda | forest / externo_4 / Successive Halving | 21.728193800 | 1047 | 1 | completa | Total; eventos.jsonl línea 272 |
| Entrenamiento/refit | forest / externo 4 | 1.027785500 | 1047 | 1 | completa | Total; eventos.jsonl línea 273 |
| Inferencia | forest / OOF fold 4 | 0.037341000 | 262 | 1 | completa | Total; eventos.jsonl línea 274 |
| Inferencia | forest / train fold 4 | 0.052967800 | 1047 | 1 | completa | Total; eventos.jsonl línea 275 |
| Búsqueda | forest / externo_5 / Grid Search | 31.834613400 | 1048 | 1 | completa | Total; eventos.jsonl línea 276 |
| Búsqueda | forest / externo_5 / Random Search | 20.505093800 | 1048 | 1 | completa | Total; eventos.jsonl línea 277 |
| Búsqueda | forest / externo_5 / Bayesiana TPE | 26.685074700 | 1048 | 1 | completa | Total; eventos.jsonl línea 278 |
| Búsqueda | forest / externo_5 / Genética DEAP | 13.289308700 | 1048 | 1 | completa | Total; eventos.jsonl línea 279 |
| Búsqueda | forest / externo_5 / Successive Halving | 22.182907600 | 1048 | 1 | completa | Total; eventos.jsonl línea 280 |
| Entrenamiento/refit | forest / externo 5 | 1.246022900 | 1048 | 1 | completa | Total; eventos.jsonl línea 281 |
| Inferencia | forest / OOF fold 5 | 0.046327100 | 261 | 1 | completa | Total; eventos.jsonl línea 282 |
| Inferencia | forest / train fold 5 | 0.062903700 | 1048 | 1 | completa | Total; eventos.jsonl línea 283 |
| Búsqueda | forest / final_train / Grid Search | 34.861609000 | 1309 | 1 | completa | Total; eventos.jsonl línea 284 |
| Búsqueda | forest / final_train / Random Search | 21.770923100 | 1309 | 1 | completa | Total; eventos.jsonl línea 285 |
| Búsqueda | forest / final_train / Bayesiana TPE | 24.189002300 | 1309 | 1 | completa | Total; eventos.jsonl línea 286 |
| Búsqueda | forest / final_train / Genética DEAP | 16.083702900 | 1309 | 1 | completa | Total; eventos.jsonl línea 287 |
| Búsqueda | forest / final_train / Successive Halving | 24.569042700 | 1309 | 1 | completa | Total; eventos.jsonl línea 288 |
| Entrenamiento/refit | forest / final train | 1.317463200 | 1309 | 1 | completa | Total; eventos.jsonl línea 289 |
| Inferencia | forest / train final | 0.060664300 | 1309 | 1 | completa | Total; eventos.jsonl línea 290 |
| Búsqueda | xgboost / externo_1 / Grid Search | 74.070889600 | 1047 | 1 | completa | Total; eventos.jsonl línea 291 |
| Búsqueda | xgboost / externo_1 / Random Search | 46.542834500 | 1047 | 1 | completa | Total; eventos.jsonl línea 292 |
| Búsqueda | xgboost / externo_1 / Bayesiana TPE | 48.849391800 | 1047 | 1 | completa | Total; eventos.jsonl línea 293 |
| Búsqueda | xgboost / externo_1 / Genética DEAP | 24.874591400 | 1047 | 1 | completa | Total; eventos.jsonl línea 294 |
| Búsqueda | xgboost / externo_1 / Successive Halving | 76.819020700 | 1047 | 1 | completa | Total; eventos.jsonl línea 295 |
| Entrenamiento/refit | xgboost / externo 1 | 0.939589600 | 1047 | 1 | completa | Total; eventos.jsonl línea 296 |
| Inferencia | xgboost / OOF fold 1 | 0.026137400 | 262 | 1 | completa | Total; eventos.jsonl línea 297 |
| Inferencia | xgboost / train fold 1 | 0.029842400 | 1047 | 1 | completa | Total; eventos.jsonl línea 298 |
| Búsqueda | xgboost / externo_2 / Grid Search | 71.522782200 | 1047 | 1 | completa | Total; eventos.jsonl línea 299 |
| Búsqueda | xgboost / externo_2 / Random Search | 46.146270900 | 1047 | 1 | completa | Total; eventos.jsonl línea 300 |
| Búsqueda | xgboost / externo_2 / Bayesiana TPE | 59.355092700 | 1047 | 1 | completa | Total; eventos.jsonl línea 301 |
| Búsqueda | xgboost / externo_2 / Genética DEAP | 28.964623100 | 1047 | 1 | completa | Total; eventos.jsonl línea 302 |
| Búsqueda | xgboost / externo_2 / Successive Halving | 78.665559400 | 1047 | 1 | completa | Total; eventos.jsonl línea 303 |
| Entrenamiento/refit | xgboost / externo 2 | 0.983590800 | 1047 | 1 | completa | Total; eventos.jsonl línea 304 |
| Inferencia | xgboost / OOF fold 2 | 0.024229600 | 262 | 1 | completa | Total; eventos.jsonl línea 305 |
| Inferencia | xgboost / train fold 2 | 0.029578500 | 1047 | 1 | completa | Total; eventos.jsonl línea 306 |
| Búsqueda | xgboost / externo_3 / Grid Search | 69.945055200 | 1047 | 1 | completa | Total; eventos.jsonl línea 307 |
| Búsqueda | xgboost / externo_3 / Random Search | 48.136976900 | 1047 | 1 | completa | Total; eventos.jsonl línea 308 |
| Búsqueda | xgboost / externo_3 / Bayesiana TPE | 65.530858700 | 1047 | 1 | completa | Total; eventos.jsonl línea 309 |
| Búsqueda | xgboost / externo_3 / Genética DEAP | 33.840885300 | 1047 | 1 | completa | Total; eventos.jsonl línea 310 |
| Búsqueda | xgboost / externo_3 / Successive Halving | 135.704633500 | 1047 | 1 | completa | Total; eventos.jsonl línea 311 |
| Entrenamiento/refit | xgboost / externo 3 | 1.637570100 | 1047 | 1 | completa | Total; eventos.jsonl línea 312 |
| Inferencia | xgboost / OOF fold 3 | 0.032635300 | 262 | 1 | completa | Total; eventos.jsonl línea 313 |
| Inferencia | xgboost / train fold 3 | 0.039436100 | 1047 | 1 | completa | Total; eventos.jsonl línea 314 |
| Búsqueda | xgboost / externo_4 / Grid Search | 124.717631000 | 1047 | 1 | completa | Total; eventos.jsonl línea 315 |
| Búsqueda | xgboost / externo_4 / Random Search | 82.840257400 | 1047 | 1 | completa | Total; eventos.jsonl línea 316 |
| Búsqueda | xgboost / externo_4 / Bayesiana TPE | 90.025273400 | 1047 | 1 | completa | Total; eventos.jsonl línea 317 |
| Búsqueda | xgboost / externo_4 / Genética DEAP | 27.805580600 | 1047 | 1 | completa | Total; eventos.jsonl línea 318 |
| Búsqueda | xgboost / externo_4 / Successive Halving | 89.050160700 | 1047 | 1 | completa | Total; eventos.jsonl línea 319 |
| Entrenamiento/refit | xgboost / externo 4 | 1.122613900 | 1047 | 1 | completa | Total; eventos.jsonl línea 320 |
| Inferencia | xgboost / OOF fold 4 | 0.026579500 | 262 | 1 | completa | Total; eventos.jsonl línea 321 |
| Inferencia | xgboost / train fold 4 | 0.029574100 | 1047 | 1 | completa | Total; eventos.jsonl línea 322 |
| Búsqueda | xgboost / externo_5 / Grid Search | 87.002734800 | 1048 | 1 | completa | Total; eventos.jsonl línea 323 |
| Búsqueda | xgboost / externo_5 / Random Search | 60.321541200 | 1048 | 1 | completa | Total; eventos.jsonl línea 324 |
| Búsqueda | xgboost / externo_5 / Bayesiana TPE | 99.309941900 | 1048 | 1 | completa | Total; eventos.jsonl línea 325 |
| Búsqueda | xgboost / externo_5 / Genética DEAP | 50.427309500 | 1048 | 1 | completa | Total; eventos.jsonl línea 326 |
| Búsqueda | xgboost / externo_5 / Successive Halving | 134.089867000 | 1048 | 1 | completa | Total; eventos.jsonl línea 327 |
| Entrenamiento/refit | xgboost / externo 5 | 1.325668600 | 1048 | 1 | completa | Total; eventos.jsonl línea 328 |
| Inferencia | xgboost / OOF fold 5 | 0.031108700 | 261 | 1 | completa | Total; eventos.jsonl línea 329 |
| Inferencia | xgboost / train fold 5 | 0.036963200 | 1048 | 1 | completa | Total; eventos.jsonl línea 330 |
| Búsqueda | xgboost / final_train / Grid Search | 127.333132700 | 1309 | 1 | completa | Total; eventos.jsonl línea 331 |
| Búsqueda | xgboost / final_train / Random Search | 76.966651300 | 1309 | 1 | completa | Total; eventos.jsonl línea 332 |
| Búsqueda | xgboost / final_train / Bayesiana TPE | 97.479070700 | 1309 | 1 | completa | Total; eventos.jsonl línea 333 |
| Búsqueda | xgboost / final_train / Genética DEAP | 37.153396500 | 1309 | 1 | completa | Total; eventos.jsonl línea 334 |
| Búsqueda | xgboost / final_train / Successive Halving | 97.428622100 | 1309 | 1 | completa | Total; eventos.jsonl línea 335 |
| Entrenamiento/refit | xgboost / final train | 1.326401600 | 1309 | 1 | completa | Total; eventos.jsonl línea 336 |
| Inferencia | xgboost / train final | 0.030179100 | 1309 | 1 | completa | Total; eventos.jsonl línea 337 |
| Búsqueda | decision_tree / externo_1 / Grid Search | 10.405311600 | 1047 | 1 | completa | Total; eventos.jsonl línea 338 |
| Búsqueda | decision_tree / externo_1 / Random Search | 1.098558600 | 1047 | 1 | completa | Total; eventos.jsonl línea 339 |
| Búsqueda | decision_tree / externo_1 / Bayesiana TPE | 1.356854000 | 1047 | 1 | completa | Total; eventos.jsonl línea 340 |
| Búsqueda | decision_tree / externo_1 / Genética DEAP | 0.985480300 | 1047 | 1 | completa | Total; eventos.jsonl línea 341 |
| Búsqueda | decision_tree / externo_1 / Successive Halving | 1.752412200 | 1047 | 1 | completa | Total; eventos.jsonl línea 342 |
| Entrenamiento/refit | decision_tree / externo 1 | 0.077657700 | 1047 | 1 | completa | Total; eventos.jsonl línea 343 |
| Inferencia | decision_tree / OOF fold 1 | 0.013933300 | 262 | 1 | completa | Total; eventos.jsonl línea 344 |
| Inferencia | decision_tree / train fold 1 | 0.014318400 | 1047 | 1 | completa | Total; eventos.jsonl línea 345 |
| Búsqueda | decision_tree / externo_2 / Grid Search | 10.660180100 | 1047 | 1 | completa | Total; eventos.jsonl línea 346 |
| Búsqueda | decision_tree / externo_2 / Random Search | 1.073003000 | 1047 | 1 | completa | Total; eventos.jsonl línea 347 |
| Búsqueda | decision_tree / externo_2 / Bayesiana TPE | 1.353112000 | 1047 | 1 | completa | Total; eventos.jsonl línea 348 |
| Búsqueda | decision_tree / externo_2 / Genética DEAP | 0.870658400 | 1047 | 1 | completa | Total; eventos.jsonl línea 349 |
| Búsqueda | decision_tree / externo_2 / Successive Halving | 1.728610200 | 1047 | 1 | completa | Total; eventos.jsonl línea 350 |
| Entrenamiento/refit | decision_tree / externo 2 | 0.072395700 | 1047 | 1 | completa | Total; eventos.jsonl línea 351 |
| Inferencia | decision_tree / OOF fold 2 | 0.014341600 | 262 | 1 | completa | Total; eventos.jsonl línea 352 |
| Inferencia | decision_tree / train fold 2 | 0.014316900 | 1047 | 1 | completa | Total; eventos.jsonl línea 353 |
| Búsqueda | decision_tree / externo_3 / Grid Search | 13.851724800 | 1047 | 1 | completa | Total; eventos.jsonl línea 354 |
| Búsqueda | decision_tree / externo_3 / Random Search | 1.077244600 | 1047 | 1 | completa | Total; eventos.jsonl línea 355 |
| Búsqueda | decision_tree / externo_3 / Bayesiana TPE | 1.532497300 | 1047 | 1 | completa | Total; eventos.jsonl línea 356 |
| Búsqueda | decision_tree / externo_3 / Genética DEAP | 0.865344700 | 1047 | 1 | completa | Total; eventos.jsonl línea 357 |
| Búsqueda | decision_tree / externo_3 / Successive Halving | 1.697863100 | 1047 | 1 | completa | Total; eventos.jsonl línea 358 |
| Entrenamiento/refit | decision_tree / externo 3 | 0.076333500 | 1047 | 1 | completa | Total; eventos.jsonl línea 359 |
| Inferencia | decision_tree / OOF fold 3 | 0.014399000 | 262 | 1 | completa | Total; eventos.jsonl línea 360 |
| Inferencia | decision_tree / train fold 3 | 0.014764000 | 1047 | 1 | completa | Total; eventos.jsonl línea 361 |
| Búsqueda | decision_tree / externo_4 / Grid Search | 10.890248500 | 1047 | 1 | completa | Total; eventos.jsonl línea 362 |
| Búsqueda | decision_tree / externo_4 / Random Search | 1.058011400 | 1047 | 1 | completa | Total; eventos.jsonl línea 363 |
| Búsqueda | decision_tree / externo_4 / Bayesiana TPE | 1.351024300 | 1047 | 1 | completa | Total; eventos.jsonl línea 364 |
| Búsqueda | decision_tree / externo_4 / Genética DEAP | 0.796050600 | 1047 | 1 | completa | Total; eventos.jsonl línea 365 |
| Búsqueda | decision_tree / externo_4 / Successive Halving | 2.322189900 | 1047 | 1 | completa | Total; eventos.jsonl línea 366 |
| Entrenamiento/refit | decision_tree / externo 4 | 0.074836600 | 1047 | 1 | completa | Total; eventos.jsonl línea 367 |
| Inferencia | decision_tree / OOF fold 4 | 0.014049700 | 262 | 1 | completa | Total; eventos.jsonl línea 368 |
| Inferencia | decision_tree / train fold 4 | 0.014103900 | 1047 | 1 | completa | Total; eventos.jsonl línea 369 |
| Búsqueda | decision_tree / externo_5 / Grid Search | 13.747748400 | 1048 | 1 | completa | Total; eventos.jsonl línea 370 |
| Búsqueda | decision_tree / externo_5 / Random Search | 1.460991500 | 1048 | 1 | completa | Total; eventos.jsonl línea 371 |
| Búsqueda | decision_tree / externo_5 / Bayesiana TPE | 1.943339200 | 1048 | 1 | completa | Total; eventos.jsonl línea 372 |
| Búsqueda | decision_tree / externo_5 / Genética DEAP | 1.254170600 | 1048 | 1 | completa | Total; eventos.jsonl línea 373 |
| Búsqueda | decision_tree / externo_5 / Successive Halving | 2.453937900 | 1048 | 1 | completa | Total; eventos.jsonl línea 374 |
| Entrenamiento/refit | decision_tree / externo 5 | 0.082530300 | 1048 | 1 | completa | Total; eventos.jsonl línea 375 |
| Inferencia | decision_tree / OOF fold 5 | 0.014386500 | 261 | 1 | completa | Total; eventos.jsonl línea 376 |
| Inferencia | decision_tree / train fold 5 | 0.015110700 | 1048 | 1 | completa | Total; eventos.jsonl línea 377 |
| Búsqueda | decision_tree / final_train / Grid Search | 14.479198500 | 1309 | 1 | completa | Total; eventos.jsonl línea 378 |
| Búsqueda | decision_tree / final_train / Random Search | 1.608630800 | 1309 | 1 | completa | Total; eventos.jsonl línea 379 |
| Búsqueda | decision_tree / final_train / Bayesiana TPE | 2.049855400 | 1309 | 1 | completa | Total; eventos.jsonl línea 380 |
| Búsqueda | decision_tree / final_train / Genética DEAP | 1.124916200 | 1309 | 1 | completa | Total; eventos.jsonl línea 381 |
| Búsqueda | decision_tree / final_train / Successive Halving | 2.500625100 | 1309 | 1 | completa | Total; eventos.jsonl línea 382 |
| Entrenamiento/refit | decision_tree / final train | 0.079171100 | 1309 | 1 | completa | Total; eventos.jsonl línea 383 |
| Inferencia | decision_tree / train final | 0.014883800 | 1309 | 1 | completa | Total; eventos.jsonl línea 384 |
| Inferencia | svm / test temporal | 0.015542900 | 188 | 1 | completa | Total; eventos.jsonl línea 385 |
| Inferencia | svm / verificación serialización test | 0.014945200 | 188 | 1 | completa | Total; eventos.jsonl línea 386 |
| Inferencia | knn / test temporal | 0.022124300 | 188 | 1 | completa | Total; eventos.jsonl línea 387 |
| Inferencia | knn / verificación serialización test | 0.018026800 | 188 | 1 | completa | Total; eventos.jsonl línea 388 |
| Inferencia | ridge / test temporal | 0.015681500 | 188 | 1 | completa | Total; eventos.jsonl línea 389 |
| Inferencia | ridge / verificación serialización test | 0.015516300 | 188 | 1 | completa | Total; eventos.jsonl línea 390 |
| Inferencia | lasso / test temporal | 0.015203800 | 188 | 1 | completa | Total; eventos.jsonl línea 391 |
| Inferencia | lasso / verificación serialización test | 0.015037600 | 188 | 1 | completa | Total; eventos.jsonl línea 392 |
| Inferencia | forest / test temporal | 0.080316900 | 188 | 1 | completa | Total; eventos.jsonl línea 393 |
| Inferencia | forest / verificación serialización test | 0.074063400 | 188 | 1 | completa | Total; eventos.jsonl línea 394 |
| Inferencia | xgboost / test temporal | 0.034609500 | 188 | 1 | completa | Total; eventos.jsonl línea 395 |
| Inferencia | xgboost / verificación serialización test | 0.038533200 | 188 | 1 | completa | Total; eventos.jsonl línea 396 |
| Inferencia | decision_tree / test temporal | 0.013377800 | 188 | 1 | completa | Total; eventos.jsonl línea 397 |
| Inferencia | decision_tree / verificación serialización test | 2.798202800 | 188 | 1 | completa | Total; eventos.jsonl línea 398 |
| Total del experimento | SVM y seis clásicos · cinco búsquedas anidadas | 3484.579787700 | No aplica | 1 | completa | Total; eventos.jsonl línea 399 |

### Ejecución `20261018_112418_33d314f9`

- **Modelo/motivo:** Verificación/preparación · .\Dash\prepare_data.py.
- **Fecha/zona:** 2026-10-18T11:24:18.532287-05:00 a 2026-10-18T11:24:21.408000-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112418_33d314f9/metadata.json](tiempos/20261018_112418_33d314f9/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112418_33d314f9/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | TransformedTargetRegressor | 0.021640800 | 188 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | TruncatedNewtonKernelRidgeRegressor | 0.019734000 | 188 | 1 | completa | Total; eventos.jsonl línea 2 |
| Total del experimento | Verificación/preparación · .\Dash\prepare_data.py | 2.874795400 | No aplica | 1 | completa | Total; eventos.jsonl línea 3 |

### Ejecución `20261018_112447_2860e648`

- **Modelo/motivo:** KNeighborsRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:24:47.986205-05:00 a 2026-10-18T11:24:48.022506-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112447_2860e648/metadata.json](tiempos/20261018_112447_2860e648/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112447_2860e648/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.023879900 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | KNeighborsRegressor · inferencia de aplicación | 0.035545100 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_112448_9a65ba44`

- **Modelo/motivo:** Ridge · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:24:48.055150-05:00 a 2026-10-18T11:24:48.081629-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112448_9a65ba44/metadata.json](tiempos/20261018_112448_9a65ba44/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112448_9a65ba44/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.014750900 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Ridge · inferencia de aplicación | 0.021851700 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_112448_fc77755c`

- **Modelo/motivo:** Lasso · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:24:48.114815-05:00 a 2026-10-18T11:24:48.135885-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112448_fc77755c/metadata.json](tiempos/20261018_112448_fc77755c/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112448_fc77755c/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.012418000 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Lasso · inferencia de aplicación | 0.020213400 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_112448_e25b614a`

- **Modelo/motivo:** RandomForestRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:24:48.440382-05:00 a 2026-10-18T11:24:48.573626-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112448_e25b614a/metadata.json](tiempos/20261018_112448_e25b614a/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112448_e25b614a/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.126129300 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | RandomForestRegressor · inferencia de aplicación | 0.138128000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_112448_212a3347`

- **Modelo/motivo:** XGBRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:24:48.775707-05:00 a 2026-10-18T11:24:48.830376-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112448_212a3347/metadata.json](tiempos/20261018_112448_212a3347/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112448_212a3347/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.038981700 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | XGBRegressor · inferencia de aplicación | 0.053290800 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_112448_418244f3`

- **Modelo/motivo:** DecisionTreeRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:24:48.874919-05:00 a 2026-10-18T11:24:48.900129-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112448_418244f3/metadata.json](tiempos/20261018_112448_418244f3/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112448_418244f3/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.012798800 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | DecisionTreeRegressor · inferencia de aplicación | 0.022793000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_112454_299b5c51`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:24:54.963897-05:00 a 2026-10-18T11:24:54.980329-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112454_299b5c51/metadata.json](tiempos/20261018_112454_299b5c51/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112454_299b5c51/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.010685500 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.016039800 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_112455_bdfbd4d3`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:24:55.013766-05:00 a 2026-10-18T11:24:55.036023-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112455_bdfbd4d3/metadata.json](tiempos/20261018_112455_bdfbd4d3/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112455_bdfbd4d3/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.009123600 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.015503000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_112455_ae0e6946`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:24:55.046486-05:00 a 2026-10-18T11:24:55.062902-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112455_ae0e6946/metadata.json](tiempos/20261018_112455_ae0e6946/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112455_ae0e6946/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.010945800 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.015814800 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_112455_d0d8190e`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:24:55.071217-05:00 a 2026-10-18T11:24:55.087024-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112455_d0d8190e/metadata.json](tiempos/20261018_112455_d0d8190e/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112455_d0d8190e/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.009343100 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.015520800 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_112455_701db6e9`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:24:55.099689-05:00 a 2026-10-18T11:24:55.115487-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112455_701db6e9/metadata.json](tiempos/20261018_112455_701db6e9/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112455_701db6e9/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.010440900 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.015520500 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_112501_6bd346dc`

- **Modelo/motivo:** TransformedTargetRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:25:01.192454-05:00 a 2026-10-18T11:25:01.219187-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112501_6bd346dc/metadata.json](tiempos/20261018_112501_6bd346dc/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112501_6bd346dc/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.024970400 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TransformedTargetRegressor · inferencia de aplicación | 0.032424000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_112441_8adfb8c8`

- **Modelo/motivo:** Verificación/preparación · --tests.
- **Fecha/zona:** 2026-10-18T11:24:41.958101-05:00 a 2026-10-18T11:25:07.881595-05:00; America/Bogota.
- **Estado:** fallida. **Entorno/configuración/código/datos:** [tiempos/20261018_112441_8adfb8c8/metadata.json](tiempos/20261018_112441_8adfb8c8/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112441_8adfb8c8/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | KNeighborsRegressor | 0.015907400 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | KNeighborsRegressor | 0.008213500 | 1 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | Ridge | 0.000205700 | 1 | 1 | completa | Total; eventos.jsonl línea 3 |
| Inferencia | Ridge | 0.008885200 | 1 | 1 | completa | Total; eventos.jsonl línea 4 |
| Inferencia | Ridge | 0.000141200 | 1 | 1 | completa | Total; eventos.jsonl línea 5 |
| Inferencia | Ridge | 0.006905000 | 1 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | Lasso | 0.006620800 | 1 | 1 | completa | Total; eventos.jsonl línea 7 |
| Inferencia | Lasso | 0.005659200 | 1 | 1 | completa | Total; eventos.jsonl línea 8 |
| Inferencia | RandomForestRegressor | 0.029662800 | 1 | 1 | completa | Total; eventos.jsonl línea 9 |
| Inferencia | RandomForestRegressor | 0.030110200 | 1 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | XGBRegressor | 0.019150700 | 1 | 1 | completa | Total; eventos.jsonl línea 11 |
| Inferencia | XGBRegressor | 0.020795300 | 1 | 1 | completa | Total; eventos.jsonl línea 12 |
| Inferencia | DecisionTreeRegressor | 0.006733400 | 1 | 1 | completa | Total; eventos.jsonl línea 13 |
| Inferencia | DecisionTreeRegressor | 0.006790600 | 1 | 1 | completa | Total; eventos.jsonl línea 14 |
| Inferencia | LinearSVR | 0.005558800 | 1 | 1 | completa | Total; eventos.jsonl línea 15 |
| Inferencia | LinearSVR | 0.006150800 | 1 | 1 | completa | Total; eventos.jsonl línea 16 |
| Inferencia | LinearSVR | 0.005052500 | 1 | 1 | completa | Total; eventos.jsonl línea 17 |
| Inferencia | LinearSVR | 0.006878900 | 1 | 1 | completa | Total; eventos.jsonl línea 18 |
| Inferencia | LinearSVR | 0.005220200 | 1 | 1 | completa | Total; eventos.jsonl línea 19 |
| Inferencia | LinearSVR | 0.005161600 | 1 | 1 | completa | Total; eventos.jsonl línea 20 |
| Inferencia | DecisionTreeRegressor | 0.004954400 | 188 | 1 | completa | Total; eventos.jsonl línea 21 |
| Inferencia | DecisionTreeRegressor | 0.003957100 | 2 | 1 | completa | Total; eventos.jsonl línea 22 |
| Inferencia | LinearSVR | 0.005949000 | 1 | 1 | completa | Total; eventos.jsonl línea 23 |
| Inferencia | LinearSVR | 0.004515100 | 1 | 1 | completa | Total; eventos.jsonl línea 24 |
| Inferencia | LinearSVR | 0.006023900 | 1 | 1 | completa | Total; eventos.jsonl línea 25 |
| Inferencia | LinearSVR | 0.007596700 | 1 | 1 | completa | Total; eventos.jsonl línea 26 |
| Inferencia | XGBRegressor | 0.015260500 | 188 | 1 | completa | Total; eventos.jsonl línea 27 |
| Inferencia | XGBRegressor | 0.014063400 | 188 | 1 | completa | Total; eventos.jsonl línea 28 |
| Inferencia | XGBRegressor | 0.011948000 | 1 | 1 | completa | Total; eventos.jsonl línea 29 |
| Inferencia | XGBRegressor | 0.012859400 | 1 | 1 | completa | Total; eventos.jsonl línea 30 |
| Inferencia | XGBRegressor | 0.015666700 | 1 | 1 | completa | Total; eventos.jsonl línea 31 |
| Inferencia | XGBRegressor | 0.018034000 | 1000 | 1 | completa | Total; eventos.jsonl línea 32 |
| Entrenamiento/refit | Ridge | 0.001043800 | 1000 | 1 | completa | Total; eventos.jsonl línea 33 |
| Inferencia | Ridge | 0.000124700 | 1000 | 1 | completa | Total; eventos.jsonl línea 34 |
| Inferencia | Ridge | 0.000380700 | 1 | 1 | completa | Total; eventos.jsonl línea 35 |
| Inferencia | XGBRegressor | 0.013709000 | 1 | 1 | completa | Total; eventos.jsonl línea 36 |
| Inferencia | XGBRegressor | 0.015179700 | 1 | 1 | completa | Total; eventos.jsonl línea 37 |
| Inferencia | XGBRegressor | 0.017631800 | 1000 | 1 | completa | Total; eventos.jsonl línea 38 |
| Entrenamiento/refit | Ridge | 0.001042300 | 1000 | 1 | completa | Total; eventos.jsonl línea 39 |
| Inferencia | Ridge | 0.000140300 | 1000 | 1 | completa | Total; eventos.jsonl línea 40 |
| Inferencia | Ridge | 0.000104800 | 1 | 1 | completa | Total; eventos.jsonl línea 41 |
| Inferencia | XGBRegressor | 0.011836400 | 1 | 1 | completa | Total; eventos.jsonl línea 42 |
| Inferencia | XGBRegressor | 0.013902600 | 1 | 1 | completa | Total; eventos.jsonl línea 43 |
| Inferencia | XGBRegressor | 0.018659400 | 1000 | 1 | completa | Total; eventos.jsonl línea 44 |
| Entrenamiento/refit | Ridge | 0.001767300 | 1000 | 1 | completa | Total; eventos.jsonl línea 45 |
| Inferencia | Ridge | 0.000214900 | 1000 | 1 | completa | Total; eventos.jsonl línea 46 |
| Inferencia | Ridge | 0.000118400 | 1 | 1 | completa | Total; eventos.jsonl línea 47 |
| Inferencia | XGBRegressor | 0.013916900 | 1 | 1 | completa | Total; eventos.jsonl línea 48 |
| Inferencia | XGBRegressor | 0.019407200 | 1000 | 1 | completa | Total; eventos.jsonl línea 49 |
| Entrenamiento/refit | Ridge | 0.000976200 | 1000 | 1 | completa | Total; eventos.jsonl línea 50 |
| Inferencia | Ridge | 0.000130000 | 1000 | 1 | completa | Total; eventos.jsonl línea 51 |
| Inferencia | Ridge | 0.000111100 | 1 | 1 | completa | Total; eventos.jsonl línea 52 |
| Inferencia | XGBRegressor | 0.013865000 | 1 | 1 | completa | Total; eventos.jsonl línea 53 |
| Inferencia | XGBRegressor | 0.017800700 | 1000 | 1 | completa | Total; eventos.jsonl línea 54 |
| Entrenamiento/refit | Ridge | 0.001088200 | 1000 | 1 | completa | Total; eventos.jsonl línea 55 |
| Inferencia | Ridge | 0.000131300 | 1000 | 1 | completa | Total; eventos.jsonl línea 56 |
| Inferencia | Ridge | 0.000117200 | 1 | 1 | completa | Total; eventos.jsonl línea 57 |
| Inferencia | TransformedTargetRegressor | 0.017898300 | 1 | 1 | completa | Total; eventos.jsonl línea 58 |
| Inferencia | TransformedTargetRegressor | 0.011949700 | 188 | 1 | completa | Total; eventos.jsonl línea 59 |
| Total del experimento | Verificación/preparación · --tests | 25.922271500 | No aplica | 1 | fallida | Total; eventos.jsonl línea 60 |

### Ejecución `20261018_112555_a440fc5b`

- **Modelo/motivo:** KNeighborsRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:25:55.415377-05:00 a 2026-10-18T11:25:55.447506-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112555_a440fc5b/metadata.json](tiempos/20261018_112555_a440fc5b/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112555_a440fc5b/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.019098800 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | KNeighborsRegressor · inferencia de aplicación | 0.031341100 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_112555_1ead4750`

- **Modelo/motivo:** Ridge · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:25:55.487252-05:00 a 2026-10-18T11:25:55.507530-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112555_1ead4750/metadata.json](tiempos/20261018_112555_1ead4750/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112555_1ead4750/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.013458300 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Ridge · inferencia de aplicación | 0.022397700 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_112555_08a164c1`

- **Modelo/motivo:** Lasso · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:25:55.542709-05:00 a 2026-10-18T11:25:55.563282-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112555_08a164c1/metadata.json](tiempos/20261018_112555_08a164c1/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112555_08a164c1/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.012420200 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Lasso · inferencia de aplicación | 0.019914300 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_112555_360ecad2`

- **Modelo/motivo:** RandomForestRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:25:55.906124-05:00 a 2026-10-18T11:25:56.058724-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112555_360ecad2/metadata.json](tiempos/20261018_112555_360ecad2/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112555_360ecad2/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.141519400 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | RandomForestRegressor · inferencia de aplicación | 0.151605300 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_112556_a50f59d1`

- **Modelo/motivo:** XGBRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:25:56.244597-05:00 a 2026-10-18T11:25:56.286132-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112556_a50f59d1/metadata.json](tiempos/20261018_112556_a50f59d1/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112556_a50f59d1/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.030223400 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | XGBRegressor · inferencia de aplicación | 0.038594500 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_112556_10db210d`

- **Modelo/motivo:** DecisionTreeRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:25:56.327326-05:00 a 2026-10-18T11:25:56.337183-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112556_10db210d/metadata.json](tiempos/20261018_112556_10db210d/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112556_10db210d/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.008579100 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | DecisionTreeRegressor · inferencia de aplicación | 0.013692100 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_112603_f99bb4a6`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:26:03.073890-05:00 a 2026-10-18T11:26:03.099675-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112603_f99bb4a6/metadata.json](tiempos/20261018_112603_f99bb4a6/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112603_f99bb4a6/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.017689800 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.026341400 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_112603_b81bc501`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:26:03.133549-05:00 a 2026-10-18T11:26:03.155380-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112603_b81bc501/metadata.json](tiempos/20261018_112603_b81bc501/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112603_b81bc501/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.014582600 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.020552000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_112603_454e4ffb`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:26:03.163678-05:00 a 2026-10-18T11:26:03.185732-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112603_454e4ffb/metadata.json](tiempos/20261018_112603_454e4ffb/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112603_454e4ffb/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.010814500 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.016847900 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_112603_968dfc80`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:26:03.199491-05:00 a 2026-10-18T11:26:03.221351-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112603_968dfc80/metadata.json](tiempos/20261018_112603_968dfc80/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112603_968dfc80/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.014511100 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.022880200 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_112603_146f4e1c`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:26:03.239327-05:00 a 2026-10-18T11:26:03.254103-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112603_146f4e1c/metadata.json](tiempos/20261018_112603_146f4e1c/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112603_146f4e1c/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.010962900 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.018644600 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_112608_51356d0a`

- **Modelo/motivo:** TransformedTargetRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:26:08.823735-05:00 a 2026-10-18T11:26:08.859757-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112608_51356d0a/metadata.json](tiempos/20261018_112608_51356d0a/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112608_51356d0a/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.017388000 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TransformedTargetRegressor · inferencia de aplicación | 0.040591000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_112608_cd6a7431`

- **Modelo/motivo:** TruncatedNewtonKernelRidgeRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:26:08.879640-05:00 a 2026-10-18T11:26:08.903724-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112608_cd6a7431/metadata.json](tiempos/20261018_112608_cd6a7431/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112608_cd6a7431/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.015674500 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TruncatedNewtonKernelRidgeRegressor · inferencia de aplicación | 0.023032400 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_112559_6ecd1517`

- **Modelo/motivo:** Verificación/preparación · .\Dash\validate_package.py.
- **Fecha/zona:** 2026-10-18T11:25:59.116092-05:00 a 2026-10-18T11:26:09.569686-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112559_6ecd1517/metadata.json](tiempos/20261018_112559_6ecd1517/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112559_6ecd1517/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | TransformedTargetRegressor | 0.026280000 | 188 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | TruncatedNewtonKernelRidgeRegressor | 0.014205700 | 188 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | TransformedTargetRegressor | 0.009583200 | 1 | 1 | completa | Total; eventos.jsonl línea 3 |
| Inferencia | TruncatedNewtonKernelRidgeRegressor | 0.008118900 | 1 | 1 | completa | Total; eventos.jsonl línea 4 |
| Inferencia | DecisionTreeRegressor | 0.005917100 | 188 | 1 | completa | Total; eventos.jsonl línea 5 |
| Inferencia | LinearSVR | 0.007803000 | 188 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | KNeighborsRegressor | 0.018101600 | 188 | 1 | completa | Total; eventos.jsonl línea 7 |
| Inferencia | Ridge | 0.000195400 | 188 | 1 | completa | Total; eventos.jsonl línea 8 |
| Inferencia | Ridge | 0.008240100 | 188 | 1 | completa | Total; eventos.jsonl línea 9 |
| Inferencia | Lasso | 0.008162800 | 188 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | RandomForestRegressor | 0.039717100 | 188 | 1 | completa | Total; eventos.jsonl línea 11 |
| Inferencia | XGBRegressor | 0.018321200 | 188 | 1 | completa | Total; eventos.jsonl línea 12 |
| Inferencia | DecisionTreeRegressor | 0.005919400 | 188 | 1 | completa | Total; eventos.jsonl línea 13 |
| Inferencia | XGBRegressor | 0.019001300 | 1 | 1 | completa | Total; eventos.jsonl línea 14 |
| Inferencia | XGBRegressor | 0.026547100 | 1000 | 1 | completa | Total; eventos.jsonl línea 15 |
| Entrenamiento/refit | Ridge | 0.001713800 | 1000 | 1 | completa | Total; eventos.jsonl línea 16 |
| Inferencia | Ridge | 0.000318200 | 1000 | 1 | completa | Total; eventos.jsonl línea 17 |
| Inferencia | Ridge | 0.000146700 | 1 | 1 | completa | Total; eventos.jsonl línea 18 |
| Inferencia | XGBRegressor | 0.018392900 | 1 | 1 | completa | Total; eventos.jsonl línea 19 |
| Total del experimento | Verificación/preparación · .\Dash\validate_package.py | 10.451934400 | No aplica | 1 | completa | Total; eventos.jsonl línea 20 |

### Ejecución `20261018_112610_7ca29c8e`

- **Modelo/motivo:** TransformedTargetRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:26:10.909456-05:00 a 2026-10-18T11:26:10.939608-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112610_7ca29c8e/metadata.json](tiempos/20261018_112610_7ca29c8e/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112610_7ca29c8e/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.025948100 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TransformedTargetRegressor · inferencia de aplicación | 0.031622000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_112549_eb0c5a91`

- **Modelo/motivo:** Verificación/preparación · --tests.
- **Fecha/zona:** 2026-10-18T11:25:49.253104-05:00 a 2026-10-18T11:26:17.729253-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112549_eb0c5a91/metadata.json](tiempos/20261018_112549_eb0c5a91/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112549_eb0c5a91/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | KNeighborsRegressor | 0.013416500 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | KNeighborsRegressor | 0.006969900 | 1 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | Ridge | 0.000155300 | 1 | 1 | completa | Total; eventos.jsonl línea 3 |
| Inferencia | Ridge | 0.008380700 | 1 | 1 | completa | Total; eventos.jsonl línea 4 |
| Inferencia | Ridge | 0.000119900 | 1 | 1 | completa | Total; eventos.jsonl línea 5 |
| Inferencia | Ridge | 0.008466900 | 1 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | Lasso | 0.006237800 | 1 | 1 | completa | Total; eventos.jsonl línea 7 |
| Inferencia | Lasso | 0.006943500 | 1 | 1 | completa | Total; eventos.jsonl línea 8 |
| Inferencia | RandomForestRegressor | 0.030186900 | 1 | 1 | completa | Total; eventos.jsonl línea 9 |
| Inferencia | RandomForestRegressor | 0.034151600 | 1 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | XGBRegressor | 0.017928400 | 1 | 1 | completa | Total; eventos.jsonl línea 11 |
| Inferencia | XGBRegressor | 0.016728700 | 1 | 1 | completa | Total; eventos.jsonl línea 12 |
| Inferencia | DecisionTreeRegressor | 0.004524600 | 1 | 1 | completa | Total; eventos.jsonl línea 13 |
| Inferencia | DecisionTreeRegressor | 0.003794000 | 1 | 1 | completa | Total; eventos.jsonl línea 14 |
| Inferencia | LinearSVR | 0.010477300 | 1 | 1 | completa | Total; eventos.jsonl línea 15 |
| Inferencia | LinearSVR | 0.008503100 | 1 | 1 | completa | Total; eventos.jsonl línea 16 |
| Inferencia | LinearSVR | 0.008678500 | 1 | 1 | completa | Total; eventos.jsonl línea 17 |
| Inferencia | LinearSVR | 0.005747800 | 1 | 1 | completa | Total; eventos.jsonl línea 18 |
| Inferencia | LinearSVR | 0.007470100 | 1 | 1 | completa | Total; eventos.jsonl línea 19 |
| Inferencia | LinearSVR | 0.006430000 | 1 | 1 | completa | Total; eventos.jsonl línea 20 |
| Inferencia | DecisionTreeRegressor | 0.006050900 | 188 | 1 | completa | Total; eventos.jsonl línea 21 |
| Inferencia | DecisionTreeRegressor | 0.005972700 | 2 | 1 | completa | Total; eventos.jsonl línea 22 |
| Inferencia | LinearSVR | 0.007329700 | 1 | 1 | completa | Total; eventos.jsonl línea 23 |
| Inferencia | LinearSVR | 0.007586500 | 1 | 1 | completa | Total; eventos.jsonl línea 24 |
| Inferencia | LinearSVR | 0.006589800 | 1 | 1 | completa | Total; eventos.jsonl línea 25 |
| Inferencia | LinearSVR | 0.006763000 | 1 | 1 | completa | Total; eventos.jsonl línea 26 |
| Inferencia | XGBRegressor | 0.022492400 | 188 | 1 | completa | Total; eventos.jsonl línea 27 |
| Inferencia | XGBRegressor | 0.017580600 | 188 | 1 | completa | Total; eventos.jsonl línea 28 |
| Inferencia | XGBRegressor | 0.019339100 | 1 | 1 | completa | Total; eventos.jsonl línea 29 |
| Inferencia | XGBRegressor | 0.018915900 | 1 | 1 | completa | Total; eventos.jsonl línea 30 |
| Inferencia | XGBRegressor | 0.016932300 | 1 | 1 | completa | Total; eventos.jsonl línea 31 |
| Inferencia | XGBRegressor | 0.026825500 | 1000 | 1 | completa | Total; eventos.jsonl línea 32 |
| Entrenamiento/refit | Ridge | 0.001510600 | 1000 | 1 | completa | Total; eventos.jsonl línea 33 |
| Inferencia | Ridge | 0.000166800 | 1000 | 1 | completa | Total; eventos.jsonl línea 34 |
| Inferencia | Ridge | 0.000141200 | 1 | 1 | completa | Total; eventos.jsonl línea 35 |
| Inferencia | XGBRegressor | 0.014701500 | 1 | 1 | completa | Total; eventos.jsonl línea 36 |
| Inferencia | XGBRegressor | 0.015625200 | 1 | 1 | completa | Total; eventos.jsonl línea 37 |
| Inferencia | XGBRegressor | 0.020563000 | 1000 | 1 | completa | Total; eventos.jsonl línea 38 |
| Entrenamiento/refit | Ridge | 0.001359100 | 1000 | 1 | completa | Total; eventos.jsonl línea 39 |
| Inferencia | Ridge | 0.000158100 | 1000 | 1 | completa | Total; eventos.jsonl línea 40 |
| Inferencia | Ridge | 0.000156300 | 1 | 1 | completa | Total; eventos.jsonl línea 41 |
| Inferencia | XGBRegressor | 0.016138200 | 1 | 1 | completa | Total; eventos.jsonl línea 42 |
| Inferencia | XGBRegressor | 0.014285400 | 1 | 1 | completa | Total; eventos.jsonl línea 43 |
| Inferencia | XGBRegressor | 0.026199700 | 1000 | 1 | completa | Total; eventos.jsonl línea 44 |
| Entrenamiento/refit | Ridge | 0.001318600 | 1000 | 1 | completa | Total; eventos.jsonl línea 45 |
| Inferencia | Ridge | 0.000171400 | 1000 | 1 | completa | Total; eventos.jsonl línea 46 |
| Inferencia | Ridge | 0.000141200 | 1 | 1 | completa | Total; eventos.jsonl línea 47 |
| Inferencia | XGBRegressor | 0.019172100 | 1 | 1 | completa | Total; eventos.jsonl línea 48 |
| Inferencia | XGBRegressor | 0.030071500 | 1000 | 1 | completa | Total; eventos.jsonl línea 49 |
| Entrenamiento/refit | Ridge | 0.001305100 | 1000 | 1 | completa | Total; eventos.jsonl línea 50 |
| Inferencia | Ridge | 0.000283100 | 1000 | 1 | completa | Total; eventos.jsonl línea 51 |
| Inferencia | Ridge | 0.000173500 | 1 | 1 | completa | Total; eventos.jsonl línea 52 |
| Inferencia | XGBRegressor | 0.018937200 | 1 | 1 | completa | Total; eventos.jsonl línea 53 |
| Inferencia | XGBRegressor | 0.018742000 | 1000 | 1 | completa | Total; eventos.jsonl línea 54 |
| Entrenamiento/refit | Ridge | 0.001189900 | 1000 | 1 | completa | Total; eventos.jsonl línea 55 |
| Inferencia | Ridge | 0.000161500 | 1000 | 1 | completa | Total; eventos.jsonl línea 56 |
| Inferencia | Ridge | 0.000104500 | 1 | 1 | completa | Total; eventos.jsonl línea 57 |
| Inferencia | XGBRegressor | 0.017292200 | 1 | 1 | completa | Total; eventos.jsonl línea 58 |
| Inferencia | TransformedTargetRegressor | 0.018684900 | 1 | 1 | completa | Total; eventos.jsonl línea 59 |
| Inferencia | TransformedTargetRegressor | 0.011388900 | 188 | 1 | completa | Total; eventos.jsonl línea 60 |
| Total del experimento | Verificación/preparación · --tests | 28.470259900 | No aplica | 1 | completa | Total; eventos.jsonl línea 61 |

### Ejecución `20261018_112728_c54d95b1`

- **Modelo/motivo:** Verificación/preparación · .\Dash\prepare_deployment.py.
- **Fecha/zona:** 2026-10-18T11:27:28.193705-05:00 a 2026-10-18T11:27:33.271910-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112728_c54d95b1/metadata.json](tiempos/20261018_112728_c54d95b1/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112728_c54d95b1/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Total del experimento | Verificación/preparación · .\Dash\prepare_deployment.py | 5.081596600 | No aplica | 1 | completa | Total; eventos.jsonl línea 1 |

### Ejecución `20261018_112829_978c13f0`

- **Modelo/motivo:** TransformedTargetRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:28:29.727171-05:00 a 2026-10-18T11:28:29.772278-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112829_978c13f0/metadata.json](tiempos/20261018_112829_978c13f0/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112829_978c13f0/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.021332000 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TransformedTargetRegressor · inferencia de aplicación | 0.049674100 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |


### Ejecución `20261018_112829_87314f79`

- **Modelo/motivo:** TruncatedNewtonKernelRidgeRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:28:29.796956-05:00 a 2026-10-18T11:28:29.838196-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112829_87314f79/metadata.json](tiempos/20261018_112829_87314f79/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112829_87314f79/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.023147800 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TruncatedNewtonKernelRidgeRegressor · inferencia de aplicación | 0.035701400 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |


### Ejecución `20261018_112817_ad7efb0d`

- **Modelo/motivo:** Verificación/preparación · .\RenderDeploy\Dash\validate_package.py.
- **Fecha/zona:** 2026-10-18T11:28:17.023043-05:00 a 2026-10-18T11:28:30.791027-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_112817_ad7efb0d/metadata.json](tiempos/20261018_112817_ad7efb0d/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_112817_ad7efb0d/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | TransformedTargetRegressor | 0.033439200 | 188 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | TruncatedNewtonKernelRidgeRegressor | 0.021832300 | 188 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | TransformedTargetRegressor | 0.011133300 | 1 | 1 | completa | Total; eventos.jsonl línea 3 |
| Inferencia | TruncatedNewtonKernelRidgeRegressor | 0.011912600 | 1 | 1 | completa | Total; eventos.jsonl línea 4 |
| Inferencia | DecisionTreeRegressor | 0.010650600 | 188 | 1 | completa | Total; eventos.jsonl línea 5 |
| Inferencia | LinearSVR | 0.011974900 | 188 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | KNeighborsRegressor | 0.028915300 | 188 | 1 | completa | Total; eventos.jsonl línea 7 |
| Inferencia | Ridge | 0.000316000 | 188 | 1 | completa | Total; eventos.jsonl línea 8 |
| Inferencia | Ridge | 0.012171500 | 188 | 1 | completa | Total; eventos.jsonl línea 9 |
| Inferencia | Lasso | 0.011589200 | 188 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | RandomForestRegressor | 0.057614300 | 188 | 1 | completa | Total; eventos.jsonl línea 11 |
| Inferencia | XGBRegressor | 0.029740400 | 188 | 1 | completa | Total; eventos.jsonl línea 12 |
| Inferencia | DecisionTreeRegressor | 0.011711400 | 188 | 1 | completa | Total; eventos.jsonl línea 13 |
| Inferencia | XGBRegressor | 0.021217400 | 1 | 1 | completa | Total; eventos.jsonl línea 14 |
| Inferencia | XGBRegressor | 0.031983600 | 1000 | 1 | completa | Total; eventos.jsonl línea 15 |
| Entrenamiento/refit | Ridge | 0.001769000 | 1000 | 1 | completa | Total; eventos.jsonl línea 16 |
| Inferencia | Ridge | 0.000392900 | 1000 | 1 | completa | Total; eventos.jsonl línea 17 |
| Inferencia | Ridge | 0.000195600 | 1 | 1 | completa | Total; eventos.jsonl línea 18 |
| Inferencia | XGBRegressor | 0.021156300 | 1 | 1 | completa | Total; eventos.jsonl línea 19 |
| Total del experimento | Verificación/preparación · .\RenderDeploy\Dash\validate_package.py | 13.772214900 | No aplica | 1 | completa | Total; eventos.jsonl línea 20 |

# Registro de tiempos de ejecución de modelos

## Propósito y vigencia

Directriz acordada el 17 de octubre de 2026 (America/Bogota). Desde este punto,
toda nueva ejecución relacionada con búsqueda de hiperparámetros, entrenamiento
(incluidos reentrenamientos y refits) e inferencia debe quedar registrada aquí,
para todos los modelos implementados. La medición se incorpora antes de ejecutar.
El historial permitirá incorporar métricas en distintas partes del dashboard;
su ubicación y presentación aún no están definidas.

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

Todavía no hay ejecuciones registradas bajo esta directriz. La plantilla anterior
no representa una ejecución real.

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

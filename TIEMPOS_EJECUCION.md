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

### Ejecución `20261018_114744_dfe7d41c`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T11:47:44.165088-05:00 a 2026-10-18T11:47:44.354567-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_114744_dfe7d41c/metadata.json](tiempos/20261018_114744_dfe7d41c/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_114744_dfe7d41c/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.011386300 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.187490600 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_173428_8a38b3cf`

- **Modelo/motivo:** KNeighborsRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:34:28.868259-05:00 a 2026-10-18T17:34:28.951373-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_173428_8a38b3cf/metadata.json](tiempos/20261018_173428_8a38b3cf/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_173428_8a38b3cf/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.056697500 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | KNeighborsRegressor · inferencia de aplicación | 0.077090900 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_173429_ed9d0d10`

- **Modelo/motivo:** Ridge · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:34:29.000078-05:00 a 2026-10-18T17:34:29.037503-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_173429_ed9d0d10/metadata.json](tiempos/20261018_173429_ed9d0d10/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_173429_ed9d0d10/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.020829900 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Ridge · inferencia de aplicación | 0.032738800 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_173429_fdfe9cc2`

- **Modelo/motivo:** Lasso · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:34:29.089088-05:00 a 2026-10-18T17:34:29.114973-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_173429_fdfe9cc2/metadata.json](tiempos/20261018_173429_fdfe9cc2/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_173429_fdfe9cc2/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.018169600 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Lasso · inferencia de aplicación | 0.028831300 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_173429_da54c01c`

- **Modelo/motivo:** RandomForestRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:34:29.547743-05:00 a 2026-10-18T17:34:29.846097-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_173429_da54c01c/metadata.json](tiempos/20261018_173429_da54c01c/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_173429_da54c01c/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.277111700 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | RandomForestRegressor · inferencia de aplicación | 0.297106400 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_173430_f47a4ec3`

- **Modelo/motivo:** XGBRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:34:30.182132-05:00 a 2026-10-18T17:34:30.242430-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_173430_f47a4ec3/metadata.json](tiempos/20261018_173430_f47a4ec3/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_173430_f47a4ec3/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.049894500 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | XGBRegressor · inferencia de aplicación | 0.061159400 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_173430_123b5b0b`

- **Modelo/motivo:** DecisionTreeRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:34:30.294300-05:00 a 2026-10-18T17:34:30.322475-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_173430_123b5b0b/metadata.json](tiempos/20261018_173430_123b5b0b/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_173430_123b5b0b/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.022639600 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | DecisionTreeRegressor · inferencia de aplicación | 0.033553900 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_173438_a604d950`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:34:38.658910-05:00 a 2026-10-18T17:34:38.675298-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_173438_a604d950/metadata.json](tiempos/20261018_173438_a604d950/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_173438_a604d950/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.014310700 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.022482600 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_173438_db870a2e`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:34:38.724644-05:00 a 2026-10-18T17:34:38.754836-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_173438_db870a2e/metadata.json](tiempos/20261018_173438_db870a2e/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_173438_db870a2e/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.014330200 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.022277300 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_173438_4389e05b`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:34:38.765572-05:00 a 2026-10-18T17:34:38.790580-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_173438_4389e05b/metadata.json](tiempos/20261018_173438_4389e05b/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_173438_4389e05b/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.014741400 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.022742800 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_173438_dbbff274`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:34:38.816819-05:00 a 2026-10-18T17:34:38.840525-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_173438_dbbff274/metadata.json](tiempos/20261018_173438_dbbff274/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_173438_dbbff274/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.014375800 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.022310100 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_173438_88e451dd`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:34:38.849034-05:00 a 2026-10-18T17:34:38.879973-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_173438_88e451dd/metadata.json](tiempos/20261018_173438_88e451dd/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_173438_88e451dd/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.015641400 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.023155100 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_173448_3613d21e`

- **Modelo/motivo:** TransformedTargetRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:34:48.399169-05:00 a 2026-10-18T17:34:48.465976-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_173448_3613d21e/metadata.json](tiempos/20261018_173448_3613d21e/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_173448_3613d21e/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.051903600 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TransformedTargetRegressor · inferencia de aplicación | 0.064085000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_173421_97102884`

- **Modelo/motivo:** Verificación/preparación · --tests.
- **Fecha/zona:** 2026-10-18T17:34:21.760139-05:00 a 2026-10-18T17:34:58.840333-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_173421_97102884/metadata.json](tiempos/20261018_173421_97102884/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_173421_97102884/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | KNeighborsRegressor | 0.033827500 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | KNeighborsRegressor | 0.011142800 | 1 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | Ridge | 0.000261800 | 1 | 1 | completa | Total; eventos.jsonl línea 3 |
| Inferencia | Ridge | 0.012415600 | 1 | 1 | completa | Total; eventos.jsonl línea 4 |
| Inferencia | Ridge | 0.000393700 | 1 | 1 | completa | Total; eventos.jsonl línea 5 |
| Inferencia | Ridge | 0.013358200 | 1 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | Lasso | 0.011160500 | 1 | 1 | completa | Total; eventos.jsonl línea 7 |
| Inferencia | Lasso | 0.010035400 | 1 | 1 | completa | Total; eventos.jsonl línea 8 |
| Inferencia | RandomForestRegressor | 0.069095000 | 1 | 1 | completa | Total; eventos.jsonl línea 9 |
| Inferencia | RandomForestRegressor | 0.056823500 | 1 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | XGBRegressor | 0.032055600 | 1 | 1 | completa | Total; eventos.jsonl línea 11 |
| Inferencia | XGBRegressor | 0.020840000 | 1 | 1 | completa | Total; eventos.jsonl línea 12 |
| Inferencia | DecisionTreeRegressor | 0.006426800 | 1 | 1 | completa | Total; eventos.jsonl línea 13 |
| Inferencia | DecisionTreeRegressor | 0.006102800 | 1 | 1 | completa | Total; eventos.jsonl línea 14 |
| Inferencia | LinearSVR | 0.007773300 | 1 | 1 | completa | Total; eventos.jsonl línea 15 |
| Inferencia | LinearSVR | 0.008733600 | 1 | 1 | completa | Total; eventos.jsonl línea 16 |
| Inferencia | LinearSVR | 0.008134600 | 1 | 1 | completa | Total; eventos.jsonl línea 17 |
| Inferencia | LinearSVR | 0.008010800 | 1 | 1 | completa | Total; eventos.jsonl línea 18 |
| Inferencia | LinearSVR | 0.007869200 | 1 | 1 | completa | Total; eventos.jsonl línea 19 |
| Inferencia | LinearSVR | 0.008673300 | 1 | 1 | completa | Total; eventos.jsonl línea 20 |
| Inferencia | DecisionTreeRegressor | 0.006537000 | 188 | 1 | completa | Total; eventos.jsonl línea 21 |
| Inferencia | DecisionTreeRegressor | 0.006006200 | 2 | 1 | completa | Total; eventos.jsonl línea 22 |
| Inferencia | LinearSVR | 0.008933700 | 1 | 1 | completa | Total; eventos.jsonl línea 23 |
| Inferencia | LinearSVR | 0.008757400 | 1 | 1 | completa | Total; eventos.jsonl línea 24 |
| Inferencia | LinearSVR | 0.009011300 | 1 | 1 | completa | Total; eventos.jsonl línea 25 |
| Inferencia | LinearSVR | 0.007219300 | 1 | 1 | completa | Total; eventos.jsonl línea 26 |
| Inferencia | XGBRegressor | 0.030064600 | 188 | 1 | completa | Total; eventos.jsonl línea 27 |
| Inferencia | XGBRegressor | 0.023307100 | 188 | 1 | completa | Total; eventos.jsonl línea 28 |
| Inferencia | XGBRegressor | 0.022045200 | 1 | 1 | completa | Total; eventos.jsonl línea 29 |
| Inferencia | XGBRegressor | 0.020690000 | 1 | 1 | completa | Total; eventos.jsonl línea 30 |
| Inferencia | XGBRegressor | 0.021811200 | 1 | 1 | completa | Total; eventos.jsonl línea 31 |
| Inferencia | XGBRegressor | 0.029903100 | 1000 | 1 | completa | Total; eventos.jsonl línea 32 |
| Entrenamiento/refit | Ridge | 0.006678400 | 1000 | 1 | completa | Total; eventos.jsonl línea 33 |
| Inferencia | Ridge | 0.000248300 | 1000 | 1 | completa | Total; eventos.jsonl línea 34 |
| Inferencia | Ridge | 0.000173900 | 1 | 1 | completa | Total; eventos.jsonl línea 35 |
| Inferencia | XGBRegressor | 0.020110000 | 1 | 1 | completa | Total; eventos.jsonl línea 36 |
| Inferencia | XGBRegressor | 0.021315500 | 1 | 1 | completa | Total; eventos.jsonl línea 37 |
| Inferencia | XGBRegressor | 0.027975800 | 1000 | 1 | completa | Total; eventos.jsonl línea 38 |
| Entrenamiento/refit | Ridge | 0.001686700 | 1000 | 1 | completa | Total; eventos.jsonl línea 39 |
| Inferencia | Ridge | 0.000283000 | 1000 | 1 | completa | Total; eventos.jsonl línea 40 |
| Inferencia | Ridge | 0.000118700 | 1 | 1 | completa | Total; eventos.jsonl línea 41 |
| Inferencia | XGBRegressor | 0.019323800 | 1 | 1 | completa | Total; eventos.jsonl línea 42 |
| Inferencia | XGBRegressor | 0.020893600 | 1 | 1 | completa | Total; eventos.jsonl línea 43 |
| Inferencia | XGBRegressor | 0.027937900 | 1000 | 1 | completa | Total; eventos.jsonl línea 44 |
| Entrenamiento/refit | Ridge | 0.001732100 | 1000 | 1 | completa | Total; eventos.jsonl línea 45 |
| Inferencia | Ridge | 0.000147500 | 1000 | 1 | completa | Total; eventos.jsonl línea 46 |
| Inferencia | Ridge | 0.000111700 | 1 | 1 | completa | Total; eventos.jsonl línea 47 |
| Inferencia | XGBRegressor | 0.022522100 | 1 | 1 | completa | Total; eventos.jsonl línea 48 |
| Inferencia | XGBRegressor | 0.030034600 | 1000 | 1 | completa | Total; eventos.jsonl línea 49 |
| Entrenamiento/refit | Ridge | 0.001753400 | 1000 | 1 | completa | Total; eventos.jsonl línea 50 |
| Inferencia | Ridge | 0.000233300 | 1000 | 1 | completa | Total; eventos.jsonl línea 51 |
| Inferencia | Ridge | 0.000216700 | 1 | 1 | completa | Total; eventos.jsonl línea 52 |
| Inferencia | XGBRegressor | 0.022061800 | 1 | 1 | completa | Total; eventos.jsonl línea 53 |
| Inferencia | XGBRegressor | 0.026745600 | 1000 | 1 | completa | Total; eventos.jsonl línea 54 |
| Entrenamiento/refit | Ridge | 0.001629200 | 1000 | 1 | completa | Total; eventos.jsonl línea 55 |
| Inferencia | Ridge | 0.000217800 | 1000 | 1 | completa | Total; eventos.jsonl línea 56 |
| Inferencia | Ridge | 0.000171600 | 1 | 1 | completa | Total; eventos.jsonl línea 57 |
| Inferencia | XGBRegressor | 0.018154100 | 1 | 1 | completa | Total; eventos.jsonl línea 58 |
| Inferencia | TransformedTargetRegressor | 0.040689500 | 1 | 1 | completa | Total; eventos.jsonl línea 59 |
| Inferencia | TransformedTargetRegressor | 0.040305300 | 188 | 1 | completa | Total; eventos.jsonl línea 60 |
| Total del experimento | Verificación/preparación · --tests | 37.083117700 | No aplica | 1 | completa | Total; eventos.jsonl línea 61 |

### Ejecución `20261018_174317_ae0ab44c`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-18T17:43:17.696391-05:00 a 2026-10-18T17:43:18.541185-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174317_ae0ab44c/metadata.json](tiempos/20261018_174317_ae0ab44c/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174317_ae0ab44c/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.042319800 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.041470500 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.271509900 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000497000 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.845805500 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261018_174429_60521007`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-18T17:44:29.142884-05:00 a 2026-10-18T17:44:29.395404-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174429_60521007/metadata.json](tiempos/20261018_174429_60521007/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174429_60521007/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.019735800 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.047893200 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.152465500 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000433100 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.253895700 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261018_174432_249f326f`

- **Modelo/motivo:** KNeighborsRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:44:32.896536-05:00 a 2026-10-18T17:44:32.930979-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174432_249f326f/metadata.json](tiempos/20261018_174432_249f326f/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174432_249f326f/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.017431900 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | KNeighborsRegressor · inferencia de aplicación | 0.032044500 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_174432_0f75197c`

- **Modelo/motivo:** Ridge · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:44:32.953420-05:00 a 2026-10-18T17:44:32.971919-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174432_0f75197c/metadata.json](tiempos/20261018_174432_0f75197c/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174432_0f75197c/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.012238300 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Ridge · inferencia de aplicación | 0.020118300 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_174432_b4218695`

- **Modelo/motivo:** Lasso · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:44:32.998488-05:00 a 2026-10-18T17:44:33.026608-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174432_b4218695/metadata.json](tiempos/20261018_174432_b4218695/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174432_b4218695/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.009748900 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Lasso · inferencia de aplicación | 0.027102000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_174433_4926dc51`

- **Modelo/motivo:** RandomForestRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:44:33.242089-05:00 a 2026-10-18T17:44:33.399655-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174433_4926dc51/metadata.json](tiempos/20261018_174433_4926dc51/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174433_4926dc51/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.132607500 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | RandomForestRegressor · inferencia de aplicación | 0.150430500 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_174433_3619d7cc`

- **Modelo/motivo:** XGBRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:44:33.521137-05:00 a 2026-10-18T17:44:33.546072-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174433_3619d7cc/metadata.json](tiempos/20261018_174433_3619d7cc/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174433_3619d7cc/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.020171000 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | XGBRegressor · inferencia de aplicación | 0.025841800 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_174433_d959878b`

- **Modelo/motivo:** DecisionTreeRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:44:33.589772-05:00 a 2026-10-18T17:44:33.604110-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174433_d959878b/metadata.json](tiempos/20261018_174433_d959878b/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174433_d959878b/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.007954200 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | DecisionTreeRegressor · inferencia de aplicación | 0.014655900 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_174439_49d1a026`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:44:39.142133-05:00 a 2026-10-18T17:44:39.156742-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174439_49d1a026/metadata.json](tiempos/20261018_174439_49d1a026/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174439_49d1a026/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.009341900 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.014162000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_174439_d3acc1fb`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:44:39.175669-05:00 a 2026-10-18T17:44:39.207116-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174439_d3acc1fb/metadata.json](tiempos/20261018_174439_d3acc1fb/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174439_d3acc1fb/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.013613100 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.031082600 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_174439_21a3fec2`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:44:39.214639-05:00 a 2026-10-18T17:44:39.251350-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174439_21a3fec2/metadata.json](tiempos/20261018_174439_21a3fec2/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174439_21a3fec2/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.014869700 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.031333000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_174439_5052a9cd`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:44:39.264799-05:00 a 2026-10-18T17:44:39.285651-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174439_5052a9cd/metadata.json](tiempos/20261018_174439_5052a9cd/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174439_5052a9cd/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.011778100 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.018137000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_174439_4e3511f3`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:44:39.300639-05:00 a 2026-10-18T17:44:39.319222-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174439_4e3511f3/metadata.json](tiempos/20261018_174439_4e3511f3/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174439_4e3511f3/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.012460600 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.019923200 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_174445_f10ace9d`

- **Modelo/motivo:** TransformedTargetRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:44:45.578986-05:00 a 2026-10-18T17:44:45.612099-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174445_f10ace9d/metadata.json](tiempos/20261018_174445_f10ace9d/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174445_f10ace9d/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.025196900 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TransformedTargetRegressor · inferencia de aplicación | 0.031645300 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_174447_1d2540d2`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-18T17:44:47.108166-05:00 a 2026-10-18T17:44:47.344891-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174447_1d2540d2/metadata.json](tiempos/20261018_174447_1d2540d2/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174447_1d2540d2/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.019457600 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.040464900 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.158055400 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000554100 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.235820500 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261018_174425_1038abf3`

- **Modelo/motivo:** Verificación/preparación · --tests.
- **Fecha/zona:** 2026-10-18T17:44:25.833978-05:00 a 2026-10-18T17:44:54.454958-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174425_1038abf3/metadata.json](tiempos/20261018_174425_1038abf3/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174425_1038abf3/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | XGBRegressor | 0.020603100 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | KNeighborsRegressor | 0.012292500 | 1 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | KNeighborsRegressor | 0.005097500 | 1 | 1 | completa | Total; eventos.jsonl línea 3 |
| Inferencia | Ridge | 0.000127000 | 1 | 1 | completa | Total; eventos.jsonl línea 4 |
| Inferencia | Ridge | 0.007647900 | 1 | 1 | completa | Total; eventos.jsonl línea 5 |
| Inferencia | Ridge | 0.000107700 | 1 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | Ridge | 0.005620800 | 1 | 1 | completa | Total; eventos.jsonl línea 7 |
| Inferencia | Lasso | 0.004926100 | 1 | 1 | completa | Total; eventos.jsonl línea 8 |
| Inferencia | Lasso | 0.004720900 | 1 | 1 | completa | Total; eventos.jsonl línea 9 |
| Inferencia | RandomForestRegressor | 0.033568700 | 1 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | RandomForestRegressor | 0.028492400 | 1 | 1 | completa | Total; eventos.jsonl línea 11 |
| Inferencia | XGBRegressor | 0.011782500 | 1 | 1 | completa | Total; eventos.jsonl línea 12 |
| Inferencia | XGBRegressor | 0.011728400 | 1 | 1 | completa | Total; eventos.jsonl línea 13 |
| Inferencia | DecisionTreeRegressor | 0.004232100 | 1 | 1 | completa | Total; eventos.jsonl línea 14 |
| Inferencia | DecisionTreeRegressor | 0.005168900 | 1 | 1 | completa | Total; eventos.jsonl línea 15 |
| Inferencia | LinearSVR | 0.005728100 | 1 | 1 | completa | Total; eventos.jsonl línea 16 |
| Inferencia | LinearSVR | 0.004584000 | 1 | 1 | completa | Total; eventos.jsonl línea 17 |
| Inferencia | LinearSVR | 0.008339100 | 1 | 1 | completa | Total; eventos.jsonl línea 18 |
| Inferencia | LinearSVR | 0.009543400 | 1 | 1 | completa | Total; eventos.jsonl línea 19 |
| Inferencia | LinearSVR | 0.006573200 | 1 | 1 | completa | Total; eventos.jsonl línea 20 |
| Inferencia | LinearSVR | 0.007068500 | 1 | 1 | completa | Total; eventos.jsonl línea 21 |
| Inferencia | DecisionTreeRegressor | 0.004249800 | 188 | 1 | completa | Total; eventos.jsonl línea 22 |
| Inferencia | DecisionTreeRegressor | 0.003540400 | 2 | 1 | completa | Total; eventos.jsonl línea 23 |
| Inferencia | LinearSVR | 0.005828900 | 1 | 1 | completa | Total; eventos.jsonl línea 24 |
| Inferencia | LinearSVR | 0.005301500 | 1 | 1 | completa | Total; eventos.jsonl línea 25 |
| Inferencia | LinearSVR | 0.005513200 | 1 | 1 | completa | Total; eventos.jsonl línea 26 |
| Inferencia | LinearSVR | 0.005587800 | 1 | 1 | completa | Total; eventos.jsonl línea 27 |
| Inferencia | XGBRegressor | 0.013555500 | 188 | 1 | completa | Total; eventos.jsonl línea 28 |
| Inferencia | XGBRegressor | 0.014547600 | 188 | 1 | completa | Total; eventos.jsonl línea 29 |
| Inferencia | XGBRegressor | 0.014989700 | 1 | 1 | completa | Total; eventos.jsonl línea 30 |
| Inferencia | XGBRegressor | 0.013517400 | 1 | 1 | completa | Total; eventos.jsonl línea 31 |
| Inferencia | XGBRegressor | 0.013741000 | 1 | 1 | completa | Total; eventos.jsonl línea 32 |
| Inferencia | XGBRegressor | 0.018450900 | 1000 | 1 | completa | Total; eventos.jsonl línea 33 |
| Entrenamiento/refit | Ridge | 0.001092000 | 1000 | 1 | completa | Total; eventos.jsonl línea 34 |
| Inferencia | Ridge | 0.000142500 | 1000 | 1 | completa | Total; eventos.jsonl línea 35 |
| Inferencia | Ridge | 0.000134800 | 1 | 1 | completa | Total; eventos.jsonl línea 36 |
| Inferencia | XGBRegressor | 0.013227400 | 1 | 1 | completa | Total; eventos.jsonl línea 37 |
| Inferencia | XGBRegressor | 0.013640600 | 1 | 1 | completa | Total; eventos.jsonl línea 38 |
| Inferencia | XGBRegressor | 0.019229200 | 1000 | 1 | completa | Total; eventos.jsonl línea 39 |
| Entrenamiento/refit | Ridge | 0.001191800 | 1000 | 1 | completa | Total; eventos.jsonl línea 40 |
| Inferencia | Ridge | 0.000170800 | 1000 | 1 | completa | Total; eventos.jsonl línea 41 |
| Inferencia | Ridge | 0.000106100 | 1 | 1 | completa | Total; eventos.jsonl línea 42 |
| Inferencia | XGBRegressor | 0.013271100 | 1 | 1 | completa | Total; eventos.jsonl línea 43 |
| Inferencia | XGBRegressor | 0.014673200 | 1 | 1 | completa | Total; eventos.jsonl línea 44 |
| Inferencia | XGBRegressor | 0.030768500 | 1000 | 1 | completa | Total; eventos.jsonl línea 45 |
| Entrenamiento/refit | Ridge | 0.001535200 | 1000 | 1 | completa | Total; eventos.jsonl línea 46 |
| Inferencia | Ridge | 0.000262100 | 1000 | 1 | completa | Total; eventos.jsonl línea 47 |
| Inferencia | Ridge | 0.000186200 | 1 | 1 | completa | Total; eventos.jsonl línea 48 |
| Inferencia | XGBRegressor | 0.019015000 | 1 | 1 | completa | Total; eventos.jsonl línea 49 |
| Inferencia | XGBRegressor | 0.017641400 | 1000 | 1 | completa | Total; eventos.jsonl línea 50 |
| Entrenamiento/refit | Ridge | 0.000997800 | 1000 | 1 | completa | Total; eventos.jsonl línea 51 |
| Inferencia | Ridge | 0.000176900 | 1000 | 1 | completa | Total; eventos.jsonl línea 52 |
| Inferencia | Ridge | 0.000114500 | 1 | 1 | completa | Total; eventos.jsonl línea 53 |
| Inferencia | XGBRegressor | 0.012596500 | 1 | 1 | completa | Total; eventos.jsonl línea 54 |
| Inferencia | XGBRegressor | 0.016978700 | 1000 | 1 | completa | Total; eventos.jsonl línea 55 |
| Entrenamiento/refit | Ridge | 0.001063700 | 1000 | 1 | completa | Total; eventos.jsonl línea 56 |
| Inferencia | Ridge | 0.000131000 | 1000 | 1 | completa | Total; eventos.jsonl línea 57 |
| Inferencia | Ridge | 0.000107200 | 1 | 1 | completa | Total; eventos.jsonl línea 58 |
| Inferencia | XGBRegressor | 0.012375900 | 1 | 1 | completa | Total; eventos.jsonl línea 59 |
| Inferencia | TransformedTargetRegressor | 0.017675800 | 1 | 1 | completa | Total; eventos.jsonl línea 60 |
| Inferencia | TransformedTargetRegressor | 0.012528700 | 188 | 1 | completa | Total; eventos.jsonl línea 61 |
| Inferencia | XGBRegressor | 0.021500300 | 1497 | 1 | completa | Total; eventos.jsonl línea 62 |
| Total del experimento | Verificación/preparación · --tests | 28.621905000 | No aplica | 1 | completa | Total; eventos.jsonl línea 63 |

### Ejecución `20261018_174528_b52fe7d0`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-18T17:45:28.143921-05:00 a 2026-10-18T17:45:28.406433-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174528_b52fe7d0/metadata.json](tiempos/20261018_174528_b52fe7d0/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174528_b52fe7d0/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.014767300 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.017400000 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.147786200 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000281100 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.263334700 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261018_174634_0b16191c`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-18T17:46:34.297621-05:00 a 2026-10-18T17:46:34.537825-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174634_0b16191c/metadata.json](tiempos/20261018_174634_0b16191c/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174634_0b16191c/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.022207000 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.049138100 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.147883300 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000615700 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.241980700 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261018_174638_788a8716`

- **Modelo/motivo:** KNeighborsRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:46:38.076605-05:00 a 2026-10-18T17:46:38.106524-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174638_788a8716/metadata.json](tiempos/20261018_174638_788a8716/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174638_788a8716/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.018732900 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | KNeighborsRegressor · inferencia de aplicación | 0.025375000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_174638_5f90a48f`

- **Modelo/motivo:** Ridge · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:46:38.135036-05:00 a 2026-10-18T17:46:38.154249-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174638_5f90a48f/metadata.json](tiempos/20261018_174638_5f90a48f/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174638_5f90a48f/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.009632500 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Ridge · inferencia de aplicación | 0.016593400 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_174638_56138d5f`

- **Modelo/motivo:** Lasso · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:46:38.175658-05:00 a 2026-10-18T17:46:38.195828-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174638_56138d5f/metadata.json](tiempos/20261018_174638_56138d5f/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174638_56138d5f/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.011219100 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Lasso · inferencia de aplicación | 0.018949600 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_174638_d17dbdfe`

- **Modelo/motivo:** RandomForestRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:46:38.426211-05:00 a 2026-10-18T17:46:38.572271-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174638_d17dbdfe/metadata.json](tiempos/20261018_174638_d17dbdfe/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174638_d17dbdfe/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.118628200 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | RandomForestRegressor · inferencia de aplicación | 0.145470100 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_174638_ea04d485`

- **Modelo/motivo:** XGBRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:46:38.692003-05:00 a 2026-10-18T17:46:38.716550-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174638_ea04d485/metadata.json](tiempos/20261018_174638_ea04d485/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174638_ea04d485/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.020588400 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | XGBRegressor · inferencia de aplicación | 0.026400000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_174638_e6edbd56`

- **Modelo/motivo:** DecisionTreeRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:46:38.761906-05:00 a 2026-10-18T17:46:38.775615-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174638_e6edbd56/metadata.json](tiempos/20261018_174638_e6edbd56/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174638_e6edbd56/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.008156200 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | DecisionTreeRegressor · inferencia de aplicación | 0.014832400 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_174644_03345319`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:46:44.197325-05:00 a 2026-10-18T17:46:44.213630-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174644_03345319/metadata.json](tiempos/20261018_174644_03345319/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174644_03345319/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.010218500 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.015308500 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_174644_21821e94`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:46:44.245908-05:00 a 2026-10-18T17:46:44.264178-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174644_21821e94/metadata.json](tiempos/20261018_174644_21821e94/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174644_21821e94/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.010421900 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.016006500 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_174644_9c8a01fe`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:46:44.272602-05:00 a 2026-10-18T17:46:44.291301-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174644_9c8a01fe/metadata.json](tiempos/20261018_174644_9c8a01fe/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174644_9c8a01fe/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.010667200 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.017458700 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_174644_542c5ad8`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:46:44.304992-05:00 a 2026-10-18T17:46:44.321615-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174644_542c5ad8/metadata.json](tiempos/20261018_174644_542c5ad8/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174644_542c5ad8/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.009614200 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.017027100 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_174644_87600b45`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:46:44.333192-05:00 a 2026-10-18T17:46:44.349517-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174644_87600b45/metadata.json](tiempos/20261018_174644_87600b45/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174644_87600b45/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.009737800 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.015535800 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_174650_6e45e4bb`

- **Modelo/motivo:** TransformedTargetRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T17:46:50.095408-05:00 a 2026-10-18T17:46:50.120347-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174650_6e45e4bb/metadata.json](tiempos/20261018_174650_6e45e4bb/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174650_6e45e4bb/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.023307000 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TransformedTargetRegressor · inferencia de aplicación | 0.028981400 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_174651_653e9c3e`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-18T17:46:51.502304-05:00 a 2026-10-18T17:46:51.747947-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174651_653e9c3e/metadata.json](tiempos/20261018_174651_653e9c3e/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174651_653e9c3e/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.014339700 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.039519200 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.159604000 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000551900 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.240208700 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261018_174630_6364af59`

- **Modelo/motivo:** Verificación/preparación · --tests.
- **Fecha/zona:** 2026-10-18T17:46:30.924200-05:00 a 2026-10-18T17:46:58.240748-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174630_6364af59/metadata.json](tiempos/20261018_174630_6364af59/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174630_6364af59/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | XGBRegressor | 0.021011400 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | KNeighborsRegressor | 0.013789100 | 1 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | KNeighborsRegressor | 0.006128400 | 1 | 1 | completa | Total; eventos.jsonl línea 3 |
| Inferencia | Ridge | 0.000119900 | 1 | 1 | completa | Total; eventos.jsonl línea 4 |
| Inferencia | Ridge | 0.005551300 | 1 | 1 | completa | Total; eventos.jsonl línea 5 |
| Inferencia | Ridge | 0.000108200 | 1 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | Ridge | 0.005485400 | 1 | 1 | completa | Total; eventos.jsonl línea 7 |
| Inferencia | Lasso | 0.005529100 | 1 | 1 | completa | Total; eventos.jsonl línea 8 |
| Inferencia | Lasso | 0.004498900 | 1 | 1 | completa | Total; eventos.jsonl línea 9 |
| Inferencia | RandomForestRegressor | 0.028528100 | 1 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | RandomForestRegressor | 0.029208600 | 1 | 1 | completa | Total; eventos.jsonl línea 11 |
| Inferencia | XGBRegressor | 0.011969700 | 1 | 1 | completa | Total; eventos.jsonl línea 12 |
| Inferencia | XGBRegressor | 0.013185500 | 1 | 1 | completa | Total; eventos.jsonl línea 13 |
| Inferencia | DecisionTreeRegressor | 0.004651500 | 1 | 1 | completa | Total; eventos.jsonl línea 14 |
| Inferencia | DecisionTreeRegressor | 0.003337400 | 1 | 1 | completa | Total; eventos.jsonl línea 15 |
| Inferencia | LinearSVR | 0.005124700 | 1 | 1 | completa | Total; eventos.jsonl línea 16 |
| Inferencia | LinearSVR | 0.004830200 | 1 | 1 | completa | Total; eventos.jsonl línea 17 |
| Inferencia | LinearSVR | 0.006235800 | 1 | 1 | completa | Total; eventos.jsonl línea 18 |
| Inferencia | LinearSVR | 0.005827100 | 1 | 1 | completa | Total; eventos.jsonl línea 19 |
| Inferencia | LinearSVR | 0.005056100 | 1 | 1 | completa | Total; eventos.jsonl línea 20 |
| Inferencia | LinearSVR | 0.005400300 | 1 | 1 | completa | Total; eventos.jsonl línea 21 |
| Inferencia | DecisionTreeRegressor | 0.004107800 | 188 | 1 | completa | Total; eventos.jsonl línea 22 |
| Inferencia | DecisionTreeRegressor | 0.003983900 | 2 | 1 | completa | Total; eventos.jsonl línea 23 |
| Inferencia | LinearSVR | 0.004956900 | 1 | 1 | completa | Total; eventos.jsonl línea 24 |
| Inferencia | LinearSVR | 0.005023100 | 1 | 1 | completa | Total; eventos.jsonl línea 25 |
| Inferencia | LinearSVR | 0.004692600 | 1 | 1 | completa | Total; eventos.jsonl línea 26 |
| Inferencia | LinearSVR | 0.004385900 | 1 | 1 | completa | Total; eventos.jsonl línea 27 |
| Inferencia | XGBRegressor | 0.013090200 | 188 | 1 | completa | Total; eventos.jsonl línea 28 |
| Inferencia | XGBRegressor | 0.016443800 | 188 | 1 | completa | Total; eventos.jsonl línea 29 |
| Inferencia | XGBRegressor | 0.013894200 | 1 | 1 | completa | Total; eventos.jsonl línea 30 |
| Inferencia | XGBRegressor | 0.012624300 | 1 | 1 | completa | Total; eventos.jsonl línea 31 |
| Inferencia | XGBRegressor | 0.012499000 | 1 | 1 | completa | Total; eventos.jsonl línea 32 |
| Inferencia | XGBRegressor | 0.016861100 | 1000 | 1 | completa | Total; eventos.jsonl línea 33 |
| Entrenamiento/refit | Ridge | 0.001072000 | 1000 | 1 | completa | Total; eventos.jsonl línea 34 |
| Inferencia | Ridge | 0.000160300 | 1000 | 1 | completa | Total; eventos.jsonl línea 35 |
| Inferencia | Ridge | 0.000100800 | 1 | 1 | completa | Total; eventos.jsonl línea 36 |
| Inferencia | XGBRegressor | 0.011949800 | 1 | 1 | completa | Total; eventos.jsonl línea 37 |
| Inferencia | XGBRegressor | 0.012833600 | 1 | 1 | completa | Total; eventos.jsonl línea 38 |
| Inferencia | XGBRegressor | 0.017200500 | 1000 | 1 | completa | Total; eventos.jsonl línea 39 |
| Entrenamiento/refit | Ridge | 0.001089800 | 1000 | 1 | completa | Total; eventos.jsonl línea 40 |
| Inferencia | Ridge | 0.000138400 | 1000 | 1 | completa | Total; eventos.jsonl línea 41 |
| Inferencia | Ridge | 0.000115900 | 1 | 1 | completa | Total; eventos.jsonl línea 42 |
| Inferencia | XGBRegressor | 0.013696000 | 1 | 1 | completa | Total; eventos.jsonl línea 43 |
| Inferencia | XGBRegressor | 0.011693200 | 1 | 1 | completa | Total; eventos.jsonl línea 44 |
| Inferencia | XGBRegressor | 0.018295600 | 1000 | 1 | completa | Total; eventos.jsonl línea 45 |
| Entrenamiento/refit | Ridge | 0.001023000 | 1000 | 1 | completa | Total; eventos.jsonl línea 46 |
| Inferencia | Ridge | 0.000231300 | 1000 | 1 | completa | Total; eventos.jsonl línea 47 |
| Inferencia | Ridge | 0.000135300 | 1 | 1 | completa | Total; eventos.jsonl línea 48 |
| Inferencia | XGBRegressor | 0.021881300 | 1 | 1 | completa | Total; eventos.jsonl línea 49 |
| Inferencia | XGBRegressor | 0.018063200 | 1000 | 1 | completa | Total; eventos.jsonl línea 50 |
| Entrenamiento/refit | Ridge | 0.000979300 | 1000 | 1 | completa | Total; eventos.jsonl línea 51 |
| Inferencia | Ridge | 0.000133500 | 1000 | 1 | completa | Total; eventos.jsonl línea 52 |
| Inferencia | Ridge | 0.000102600 | 1 | 1 | completa | Total; eventos.jsonl línea 53 |
| Inferencia | XGBRegressor | 0.012210400 | 1 | 1 | completa | Total; eventos.jsonl línea 54 |
| Inferencia | XGBRegressor | 0.017049600 | 1000 | 1 | completa | Total; eventos.jsonl línea 55 |
| Entrenamiento/refit | Ridge | 0.001059800 | 1000 | 1 | completa | Total; eventos.jsonl línea 56 |
| Inferencia | Ridge | 0.000155200 | 1000 | 1 | completa | Total; eventos.jsonl línea 57 |
| Inferencia | Ridge | 0.000169600 | 1 | 1 | completa | Total; eventos.jsonl línea 58 |
| Inferencia | XGBRegressor | 0.011849200 | 1 | 1 | completa | Total; eventos.jsonl línea 59 |
| Inferencia | TransformedTargetRegressor | 0.015292000 | 1 | 1 | completa | Total; eventos.jsonl línea 60 |
| Inferencia | TransformedTargetRegressor | 0.011631400 | 188 | 1 | completa | Total; eventos.jsonl línea 61 |
| Inferencia | XGBRegressor | 0.020035800 | 1497 | 1 | completa | Total; eventos.jsonl línea 62 |
| Total del experimento | Verificación/preparación · --tests | 27.312035100 | No aplica | 1 | completa | Total; eventos.jsonl línea 63 |

### Ejecución `20261018_174803_623b72d7`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-18T17:48:03.275783-05:00 a 2026-10-18T17:48:03.548025-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174803_623b72d7/metadata.json](tiempos/20261018_174803_623b72d7/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174803_623b72d7/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.016468000 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.017215700 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.149179900 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000330100 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.272504000 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261018_174910_24710c1f`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-18T17:49:10.287276-05:00 a 2026-10-18T17:49:10.924602-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174910_24710c1f/metadata.json](tiempos/20261018_174910_24710c1f/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174910_24710c1f/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.020176300 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.021110100 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.173717200 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000420400 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.637574100 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261018_174931_e7c32c6a`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-18T17:49:31.045387-05:00 a 2026-10-18T17:49:31.336534-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_174931_e7c32c6a/metadata.json](tiempos/20261018_174931_e7c32c6a/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_174931_e7c32c6a/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.015125500 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.022000900 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.161805700 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000343400 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.292218800 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261018_175510_d7ad2eba`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-18T17:55:10.735395-05:00 a 2026-10-18T17:55:11.229481-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_175510_d7ad2eba/metadata.json](tiempos/20261018_175510_d7ad2eba/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_175510_d7ad2eba/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.028234200 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.029603200 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.302019500 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000592900 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.495277900 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261018_175641_34f23995`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-18T17:56:41.614172-05:00 a 2026-10-18T17:56:41.989110-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_175641_34f23995/metadata.json](tiempos/20261018_175641_34f23995/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_175641_34f23995/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.016392000 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.019885300 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.226538700 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000396600 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.373709400 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261018_182405_58b79981`

- **Modelo/motivo:** Comparación por estudiante · seis clásicos frente a SVM · test.
- **Fecha/zona:** 2026-10-18T18:24:05.787301-05:00 a 2026-10-18T18:24:07.807261-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_182405_58b79981/metadata.json](tiempos/20261018_182405_58b79981/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_182405_58b79981/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Preparación estadística | Validación de partición y agregación privada | 0.061062400 | No aplica | 1 | completa | Total; eventos.jsonl línea 1 |
| Análisis estadístico | Bootstrap-t, BCa y Holm6 | 1.195748800 | 188 | 1 | completa | Total; eventos.jsonl línea 2 |
| Total del experimento | Comparación por estudiante · seis clásicos frente a SVM · test | 2.012051200 | No aplica | 1 | completa | Total; eventos.jsonl línea 3 |

### Ejecución `20261018_182511_cbb1f2a0`

- **Modelo/motivo:** Comparación por estudiante · seis clásicos frente a SVM · test.
- **Fecha/zona:** 2026-10-18T18:25:11.454976-05:00 a 2026-10-18T18:25:13.486113-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_182511_cbb1f2a0/metadata.json](tiempos/20261018_182511_cbb1f2a0/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_182511_cbb1f2a0/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Preparación estadística | Validación de partición y agregación privada | 0.055272400 | No aplica | 1 | completa | Total; eventos.jsonl línea 1 |
| Análisis estadístico | Bootstrap-t, BCa y Holm6 | 1.138061200 | 188 | 1 | completa | Total; eventos.jsonl línea 2 |
| Total del experimento | Comparación por estudiante · seis clásicos frente a SVM · test | 2.018187400 | No aplica | 1 | completa | Total; eventos.jsonl línea 3 |

### Ejecución `20261018_182550_62defed2`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-18T18:25:50.375165-05:00 a 2026-10-18T18:25:50.642944-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_182550_62defed2/metadata.json](tiempos/20261018_182550_62defed2/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_182550_62defed2/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.019798300 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.048597800 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.174201000 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000418700 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.266881800 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261018_182554_ce81088a`

- **Modelo/motivo:** KNeighborsRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T18:25:54.117310-05:00 a 2026-10-18T18:25:54.141280-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_182554_ce81088a/metadata.json](tiempos/20261018_182554_ce81088a/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_182554_ce81088a/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.017087600 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | KNeighborsRegressor · inferencia de aplicación | 0.021748400 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_182554_aab6e407`

- **Modelo/motivo:** Ridge · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T18:25:54.164326-05:00 a 2026-10-18T18:25:54.181552-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_182554_aab6e407/metadata.json](tiempos/20261018_182554_aab6e407/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_182554_aab6e407/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.012083400 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Ridge · inferencia de aplicación | 0.017790400 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_182554_5b495c44`

- **Modelo/motivo:** Lasso · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T18:25:54.208538-05:00 a 2026-10-18T18:25:54.224964-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_182554_5b495c44/metadata.json](tiempos/20261018_182554_5b495c44/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_182554_5b495c44/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.009645700 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Lasso · inferencia de aplicación | 0.015334700 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_182554_00bf737c`

- **Modelo/motivo:** RandomForestRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T18:25:54.449271-05:00 a 2026-10-18T18:25:54.588477-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_182554_00bf737c/metadata.json](tiempos/20261018_182554_00bf737c/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_182554_00bf737c/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.130427200 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | RandomForestRegressor · inferencia de aplicación | 0.138911000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_182554_f25c23c2`

- **Modelo/motivo:** XGBRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T18:25:54.698829-05:00 a 2026-10-18T18:25:54.732200-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_182554_f25c23c2/metadata.json](tiempos/20261018_182554_f25c23c2/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_182554_f25c23c2/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.019980700 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | XGBRegressor · inferencia de aplicación | 0.025262600 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_182554_3e1bb8d9`

- **Modelo/motivo:** DecisionTreeRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T18:25:54.761991-05:00 a 2026-10-18T18:25:54.773224-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_182554_3e1bb8d9/metadata.json](tiempos/20261018_182554_3e1bb8d9/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_182554_3e1bb8d9/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.007028900 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | DecisionTreeRegressor · inferencia de aplicación | 0.013617300 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_182600_860778d4`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T18:26:00.035932-05:00 a 2026-10-18T18:26:00.054595-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_182600_860778d4/metadata.json](tiempos/20261018_182600_860778d4/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_182600_860778d4/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.010387700 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.015623900 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_182600_a26e3d09`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T18:26:00.081611-05:00 a 2026-10-18T18:26:00.097828-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_182600_a26e3d09/metadata.json](tiempos/20261018_182600_a26e3d09/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_182600_a26e3d09/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.009794500 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.015258900 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_182600_a23642d5`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T18:26:00.104734-05:00 a 2026-10-18T18:26:00.121826-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_182600_a23642d5/metadata.json](tiempos/20261018_182600_a23642d5/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_182600_a23642d5/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.010057800 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.015239200 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_182600_2582deff`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T18:26:00.129880-05:00 a 2026-10-18T18:26:00.138122-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_182600_2582deff/metadata.json](tiempos/20261018_182600_2582deff/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_182600_2582deff/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.009671400 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.015724000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_182600_a5eaf031`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T18:26:00.152477-05:00 a 2026-10-18T18:26:00.169469-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_182600_a5eaf031/metadata.json](tiempos/20261018_182600_a5eaf031/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_182600_a5eaf031/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.010672000 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.016954900 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_182605_0816e7de`

- **Modelo/motivo:** TransformedTargetRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T18:26:05.690234-05:00 a 2026-10-18T18:26:05.723745-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_182605_0816e7de/metadata.json](tiempos/20261018_182605_0816e7de/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_182605_0816e7de/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.022053700 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TransformedTargetRegressor · inferencia de aplicación | 0.027434000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_182607_f91fb57c`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-18T18:26:07.058035-05:00 a 2026-10-18T18:26:07.291725-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_182607_f91fb57c/metadata.json](tiempos/20261018_182607_f91fb57c/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_182607_f91fb57c/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.014467200 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.039011100 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.153834200 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000352000 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.227911200 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261018_182547_7dd384f1`

- **Modelo/motivo:** Verificación/preparación · --tests.
- **Fecha/zona:** 2026-10-18T18:25:47.044661-05:00 a 2026-10-18T18:26:14.490780-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_182547_7dd384f1/metadata.json](tiempos/20261018_182547_7dd384f1/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_182547_7dd384f1/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | XGBRegressor | 0.021237100 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | KNeighborsRegressor | 0.012105300 | 1 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | KNeighborsRegressor | 0.006206500 | 1 | 1 | completa | Total; eventos.jsonl línea 3 |
| Inferencia | Ridge | 0.000141200 | 1 | 1 | completa | Total; eventos.jsonl línea 4 |
| Inferencia | Ridge | 0.006867700 | 1 | 1 | completa | Total; eventos.jsonl línea 5 |
| Inferencia | Ridge | 0.000135900 | 1 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | Ridge | 0.005559400 | 1 | 1 | completa | Total; eventos.jsonl línea 7 |
| Inferencia | Lasso | 0.004774300 | 1 | 1 | completa | Total; eventos.jsonl línea 8 |
| Inferencia | Lasso | 0.006678800 | 1 | 1 | completa | Total; eventos.jsonl línea 9 |
| Inferencia | RandomForestRegressor | 0.034175100 | 1 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | RandomForestRegressor | 0.027441600 | 1 | 1 | completa | Total; eventos.jsonl línea 11 |
| Inferencia | XGBRegressor | 0.011616500 | 1 | 1 | completa | Total; eventos.jsonl línea 12 |
| Inferencia | XGBRegressor | 0.011505100 | 1 | 1 | completa | Total; eventos.jsonl línea 13 |
| Inferencia | DecisionTreeRegressor | 0.003909000 | 1 | 1 | completa | Total; eventos.jsonl línea 14 |
| Inferencia | DecisionTreeRegressor | 0.003550900 | 1 | 1 | completa | Total; eventos.jsonl línea 15 |
| Inferencia | LinearSVR | 0.005700900 | 1 | 1 | completa | Total; eventos.jsonl línea 16 |
| Inferencia | LinearSVR | 0.005032900 | 1 | 1 | completa | Total; eventos.jsonl línea 17 |
| Inferencia | LinearSVR | 0.005252000 | 1 | 1 | completa | Total; eventos.jsonl línea 18 |
| Inferencia | LinearSVR | 0.005311600 | 1 | 1 | completa | Total; eventos.jsonl línea 19 |
| Inferencia | LinearSVR | 0.005032800 | 1 | 1 | completa | Total; eventos.jsonl línea 20 |
| Inferencia | LinearSVR | 0.005030000 | 1 | 1 | completa | Total; eventos.jsonl línea 21 |
| Inferencia | DecisionTreeRegressor | 0.003886700 | 188 | 1 | completa | Total; eventos.jsonl línea 22 |
| Inferencia | DecisionTreeRegressor | 0.003746600 | 2 | 1 | completa | Total; eventos.jsonl línea 23 |
| Inferencia | LinearSVR | 0.004984800 | 1 | 1 | completa | Total; eventos.jsonl línea 24 |
| Inferencia | LinearSVR | 0.004592200 | 1 | 1 | completa | Total; eventos.jsonl línea 25 |
| Inferencia | LinearSVR | 0.005409600 | 1 | 1 | completa | Total; eventos.jsonl línea 26 |
| Inferencia | LinearSVR | 0.004469500 | 1 | 1 | completa | Total; eventos.jsonl línea 27 |
| Inferencia | XGBRegressor | 0.015538600 | 188 | 1 | completa | Total; eventos.jsonl línea 28 |
| Inferencia | XGBRegressor | 0.013263900 | 188 | 1 | completa | Total; eventos.jsonl línea 29 |
| Inferencia | XGBRegressor | 0.012519200 | 1 | 1 | completa | Total; eventos.jsonl línea 30 |
| Inferencia | XGBRegressor | 0.013251400 | 1 | 1 | completa | Total; eventos.jsonl línea 31 |
| Inferencia | XGBRegressor | 0.011469200 | 1 | 1 | completa | Total; eventos.jsonl línea 32 |
| Inferencia | XGBRegressor | 0.017393600 | 1000 | 1 | completa | Total; eventos.jsonl línea 33 |
| Entrenamiento/refit | Ridge | 0.001036900 | 1000 | 1 | completa | Total; eventos.jsonl línea 34 |
| Inferencia | Ridge | 0.000152300 | 1000 | 1 | completa | Total; eventos.jsonl línea 35 |
| Inferencia | Ridge | 0.000102100 | 1 | 1 | completa | Total; eventos.jsonl línea 36 |
| Inferencia | XGBRegressor | 0.011590700 | 1 | 1 | completa | Total; eventos.jsonl línea 37 |
| Inferencia | XGBRegressor | 0.011252000 | 1 | 1 | completa | Total; eventos.jsonl línea 38 |
| Inferencia | XGBRegressor | 0.016765600 | 1000 | 1 | completa | Total; eventos.jsonl línea 39 |
| Entrenamiento/refit | Ridge | 0.000965200 | 1000 | 1 | completa | Total; eventos.jsonl línea 40 |
| Inferencia | Ridge | 0.000160000 | 1000 | 1 | completa | Total; eventos.jsonl línea 41 |
| Inferencia | Ridge | 0.000101400 | 1 | 1 | completa | Total; eventos.jsonl línea 42 |
| Inferencia | XGBRegressor | 0.011898000 | 1 | 1 | completa | Total; eventos.jsonl línea 43 |
| Inferencia | XGBRegressor | 0.011267900 | 1 | 1 | completa | Total; eventos.jsonl línea 44 |
| Inferencia | XGBRegressor | 0.016008700 | 1000 | 1 | completa | Total; eventos.jsonl línea 45 |
| Entrenamiento/refit | Ridge | 0.001038000 | 1000 | 1 | completa | Total; eventos.jsonl línea 46 |
| Inferencia | Ridge | 0.000141900 | 1000 | 1 | completa | Total; eventos.jsonl línea 47 |
| Inferencia | Ridge | 0.000103100 | 1 | 1 | completa | Total; eventos.jsonl línea 48 |
| Inferencia | XGBRegressor | 0.017939400 | 1 | 1 | completa | Total; eventos.jsonl línea 49 |
| Inferencia | XGBRegressor | 0.029705400 | 1000 | 1 | completa | Total; eventos.jsonl línea 50 |
| Entrenamiento/refit | Ridge | 0.001452400 | 1000 | 1 | completa | Total; eventos.jsonl línea 51 |
| Inferencia | Ridge | 0.000333100 | 1000 | 1 | completa | Total; eventos.jsonl línea 52 |
| Inferencia | Ridge | 0.000181100 | 1 | 1 | completa | Total; eventos.jsonl línea 53 |
| Inferencia | XGBRegressor | 0.012807400 | 1 | 1 | completa | Total; eventos.jsonl línea 54 |
| Inferencia | XGBRegressor | 0.016720100 | 1000 | 1 | completa | Total; eventos.jsonl línea 55 |
| Entrenamiento/refit | Ridge | 0.000952900 | 1000 | 1 | completa | Total; eventos.jsonl línea 56 |
| Inferencia | Ridge | 0.000127300 | 1000 | 1 | completa | Total; eventos.jsonl línea 57 |
| Inferencia | Ridge | 0.000101400 | 1 | 1 | completa | Total; eventos.jsonl línea 58 |
| Inferencia | XGBRegressor | 0.012251500 | 1 | 1 | completa | Total; eventos.jsonl línea 59 |
| Inferencia | TransformedTargetRegressor | 0.015858000 | 1 | 1 | completa | Total; eventos.jsonl línea 60 |
| Inferencia | TransformedTargetRegressor | 0.009774500 | 188 | 1 | completa | Total; eventos.jsonl línea 61 |
| Inferencia | XGBRegressor | 0.020455600 | 1497 | 1 | completa | Total; eventos.jsonl línea 62 |
| Total del experimento | Verificación/preparación · --tests | 27.448932900 | No aplica | 1 | completa | Total; eventos.jsonl línea 63 |

### Ejecución `20261018_182708_67a070dc`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-18T18:27:08.666460-05:00 a 2026-10-18T18:27:08.982124-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_182708_67a070dc/metadata.json](tiempos/20261018_182708_67a070dc/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_182708_67a070dc/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.018477700 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.018904900 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.150928800 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000859200 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.314990800 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261018_182823_7c2873c7`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-18T18:28:23.589059-05:00 a 2026-10-18T18:28:23.916545-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_182823_7c2873c7/metadata.json](tiempos/20261018_182823_7c2873c7/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_182823_7c2873c7/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.014551900 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.017973800 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.156594100 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000686100 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.326736600 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261018_183014_ae5a6642`

- **Modelo/motivo:** Comparación por estudiante · seis clásicos frente a SVM · test.
- **Fecha/zona:** 2026-10-18T18:30:14.758393-05:00 a 2026-10-18T18:30:16.725713-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_183014_ae5a6642/metadata.json](tiempos/20261018_183014_ae5a6642/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_183014_ae5a6642/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Preparación estadística | Validación de partición y agregación privada | 0.052842300 | No aplica | 1 | completa | Total; eventos.jsonl línea 1 |
| Análisis estadístico | Bootstrap-t, BCa y Holm6 | 1.164203100 | 188 | 1 | completa | Total; eventos.jsonl línea 2 |
| Total del experimento | Comparación por estudiante · seis clásicos frente a SVM · test | 1.958802400 | No aplica | 1 | completa | Total; eventos.jsonl línea 3 |

### Ejecución `20261018_183048_9b990011`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-18T18:30:48.819800-05:00 a 2026-10-18T18:30:49.101498-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_183048_9b990011/metadata.json](tiempos/20261018_183048_9b990011/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_183048_9b990011/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.018347900 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.019225700 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.152608600 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000335100 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.283896300 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261018_183216_b1b8e726`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-18T18:32:16.747125-05:00 a 2026-10-18T18:32:17.002487-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_183216_b1b8e726/metadata.json](tiempos/20261018_183216_b1b8e726/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_183216_b1b8e726/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.020655500 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.047116800 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.155842800 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000618100 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.254915000 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261018_183220_f3f8ee69`

- **Modelo/motivo:** KNeighborsRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T18:32:20.440314-05:00 a 2026-10-18T18:32:20.468658-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_183220_f3f8ee69/metadata.json](tiempos/20261018_183220_f3f8ee69/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_183220_f3f8ee69/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.017581200 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | KNeighborsRegressor · inferencia de aplicación | 0.022565100 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_183220_9a0c4511`

- **Modelo/motivo:** Ridge · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T18:32:20.497164-05:00 a 2026-10-18T18:32:20.521910-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_183220_9a0c4511/metadata.json](tiempos/20261018_183220_9a0c4511/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_183220_9a0c4511/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.012288800 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Ridge · inferencia de aplicación | 0.025392200 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_183220_f1e716ed`

- **Modelo/motivo:** Lasso · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T18:32:20.546652-05:00 a 2026-10-18T18:32:20.567407-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_183220_f1e716ed/metadata.json](tiempos/20261018_183220_f1e716ed/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_183220_f1e716ed/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.011327400 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Lasso · inferencia de aplicación | 0.018224500 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_183220_3192c95d`

- **Modelo/motivo:** RandomForestRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T18:32:20.803488-05:00 a 2026-10-18T18:32:20.931659-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_183220_3192c95d/metadata.json](tiempos/20261018_183220_3192c95d/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_183220_3192c95d/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.118732400 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | RandomForestRegressor · inferencia de aplicación | 0.128713900 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_183221_5f573b7a`

- **Modelo/motivo:** XGBRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T18:32:21.067560-05:00 a 2026-10-18T18:32:21.112029-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_183221_5f573b7a/metadata.json](tiempos/20261018_183221_5f573b7a/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_183221_5f573b7a/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.030183300 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | XGBRegressor · inferencia de aplicación | 0.043811900 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_183221_178781fb`

- **Modelo/motivo:** DecisionTreeRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T18:32:21.141863-05:00 a 2026-10-18T18:32:21.168403-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_183221_178781fb/metadata.json](tiempos/20261018_183221_178781fb/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_183221_178781fb/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.009067500 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | DecisionTreeRegressor · inferencia de aplicación | 0.024208600 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_183226_cc08c432`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T18:32:26.511016-05:00 a 2026-10-18T18:32:26.537713-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_183226_cc08c432/metadata.json](tiempos/20261018_183226_cc08c432/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_183226_cc08c432/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.009952900 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.024725700 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_183226_0e1b7a1b`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T18:32:26.565730-05:00 a 2026-10-18T18:32:26.583884-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_183226_0e1b7a1b/metadata.json](tiempos/20261018_183226_0e1b7a1b/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_183226_0e1b7a1b/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.011235600 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.017338900 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_183226_dc64e0b1`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T18:32:26.601317-05:00 a 2026-10-18T18:32:26.616295-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_183226_dc64e0b1/metadata.json](tiempos/20261018_183226_dc64e0b1/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_183226_dc64e0b1/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.009318500 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.016131100 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_183226_32fa6a94`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T18:32:26.626219-05:00 a 2026-10-18T18:32:26.648203-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_183226_32fa6a94/metadata.json](tiempos/20261018_183226_32fa6a94/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_183226_32fa6a94/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.010394400 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.018184600 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_183226_f77caa9d`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T18:32:26.659377-05:00 a 2026-10-18T18:32:26.676496-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_183226_f77caa9d/metadata.json](tiempos/20261018_183226_f77caa9d/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_183226_f77caa9d/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.009568800 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.017336400 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_183232_d70005e9`

- **Modelo/motivo:** TransformedTargetRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T18:32:32.213294-05:00 a 2026-10-18T18:32:32.262893-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_183232_d70005e9/metadata.json](tiempos/20261018_183232_d70005e9/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_183232_d70005e9/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.030681600 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TransformedTargetRegressor · inferencia de aplicación | 0.044998300 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_183233_086869e4`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-18T18:32:33.620539-05:00 a 2026-10-18T18:32:33.850892-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_183233_086869e4/metadata.json](tiempos/20261018_183233_086869e4/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_183233_086869e4/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.014174300 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.039768900 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.160250500 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000361200 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.229245000 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261018_183213_56a83a91`

- **Modelo/motivo:** Verificación/preparación · --tests.
- **Fecha/zona:** 2026-10-18T18:32:13.509626-05:00 a 2026-10-18T18:32:41.304626-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_183213_56a83a91/metadata.json](tiempos/20261018_183213_56a83a91/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_183213_56a83a91/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | XGBRegressor | 0.020016300 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | KNeighborsRegressor | 0.012639400 | 1 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | KNeighborsRegressor | 0.006379100 | 1 | 1 | completa | Total; eventos.jsonl línea 3 |
| Inferencia | Ridge | 0.000142400 | 1 | 1 | completa | Total; eventos.jsonl línea 4 |
| Inferencia | Ridge | 0.006801100 | 1 | 1 | completa | Total; eventos.jsonl línea 5 |
| Inferencia | Ridge | 0.000129100 | 1 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | Ridge | 0.005999400 | 1 | 1 | completa | Total; eventos.jsonl línea 7 |
| Inferencia | Lasso | 0.005966500 | 1 | 1 | completa | Total; eventos.jsonl línea 8 |
| Inferencia | Lasso | 0.005962100 | 1 | 1 | completa | Total; eventos.jsonl línea 9 |
| Inferencia | RandomForestRegressor | 0.028877200 | 1 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | RandomForestRegressor | 0.036612700 | 1 | 1 | completa | Total; eventos.jsonl línea 11 |
| Inferencia | XGBRegressor | 0.018184900 | 1 | 1 | completa | Total; eventos.jsonl línea 12 |
| Inferencia | XGBRegressor | 0.012476900 | 1 | 1 | completa | Total; eventos.jsonl línea 13 |
| Inferencia | DecisionTreeRegressor | 0.004085400 | 1 | 1 | completa | Total; eventos.jsonl línea 14 |
| Inferencia | DecisionTreeRegressor | 0.003536200 | 1 | 1 | completa | Total; eventos.jsonl línea 15 |
| Inferencia | LinearSVR | 0.005992400 | 1 | 1 | completa | Total; eventos.jsonl línea 16 |
| Inferencia | LinearSVR | 0.004711200 | 1 | 1 | completa | Total; eventos.jsonl línea 17 |
| Inferencia | LinearSVR | 0.006191900 | 1 | 1 | completa | Total; eventos.jsonl línea 18 |
| Inferencia | LinearSVR | 0.004920300 | 1 | 1 | completa | Total; eventos.jsonl línea 19 |
| Inferencia | LinearSVR | 0.005844800 | 1 | 1 | completa | Total; eventos.jsonl línea 20 |
| Inferencia | LinearSVR | 0.005272500 | 1 | 1 | completa | Total; eventos.jsonl línea 21 |
| Inferencia | DecisionTreeRegressor | 0.005387900 | 188 | 1 | completa | Total; eventos.jsonl línea 22 |
| Inferencia | DecisionTreeRegressor | 0.003406600 | 2 | 1 | completa | Total; eventos.jsonl línea 23 |
| Inferencia | LinearSVR | 0.004520300 | 1 | 1 | completa | Total; eventos.jsonl línea 24 |
| Inferencia | LinearSVR | 0.004585600 | 1 | 1 | completa | Total; eventos.jsonl línea 25 |
| Inferencia | LinearSVR | 0.005096400 | 1 | 1 | completa | Total; eventos.jsonl línea 26 |
| Inferencia | LinearSVR | 0.004625600 | 1 | 1 | completa | Total; eventos.jsonl línea 27 |
| Inferencia | XGBRegressor | 0.014386300 | 188 | 1 | completa | Total; eventos.jsonl línea 28 |
| Inferencia | XGBRegressor | 0.012936900 | 188 | 1 | completa | Total; eventos.jsonl línea 29 |
| Inferencia | XGBRegressor | 0.011879200 | 1 | 1 | completa | Total; eventos.jsonl línea 30 |
| Inferencia | XGBRegressor | 0.012702700 | 1 | 1 | completa | Total; eventos.jsonl línea 31 |
| Inferencia | XGBRegressor | 0.014167800 | 1 | 1 | completa | Total; eventos.jsonl línea 32 |
| Inferencia | XGBRegressor | 0.018484200 | 1000 | 1 | completa | Total; eventos.jsonl línea 33 |
| Entrenamiento/refit | Ridge | 0.001100500 | 1000 | 1 | completa | Total; eventos.jsonl línea 34 |
| Inferencia | Ridge | 0.000134100 | 1000 | 1 | completa | Total; eventos.jsonl línea 35 |
| Inferencia | Ridge | 0.000106600 | 1 | 1 | completa | Total; eventos.jsonl línea 36 |
| Inferencia | XGBRegressor | 0.011780200 | 1 | 1 | completa | Total; eventos.jsonl línea 37 |
| Inferencia | XGBRegressor | 0.012061000 | 1 | 1 | completa | Total; eventos.jsonl línea 38 |
| Inferencia | XGBRegressor | 0.016424700 | 1000 | 1 | completa | Total; eventos.jsonl línea 39 |
| Entrenamiento/refit | Ridge | 0.000946400 | 1000 | 1 | completa | Total; eventos.jsonl línea 40 |
| Inferencia | Ridge | 0.000132300 | 1000 | 1 | completa | Total; eventos.jsonl línea 41 |
| Inferencia | Ridge | 0.000120100 | 1 | 1 | completa | Total; eventos.jsonl línea 42 |
| Inferencia | XGBRegressor | 0.011565600 | 1 | 1 | completa | Total; eventos.jsonl línea 43 |
| Inferencia | XGBRegressor | 0.014553100 | 1 | 1 | completa | Total; eventos.jsonl línea 44 |
| Inferencia | XGBRegressor | 0.016921200 | 1000 | 1 | completa | Total; eventos.jsonl línea 45 |
| Entrenamiento/refit | Ridge | 0.000944400 | 1000 | 1 | completa | Total; eventos.jsonl línea 46 |
| Inferencia | Ridge | 0.000199400 | 1000 | 1 | completa | Total; eventos.jsonl línea 47 |
| Inferencia | Ridge | 0.000107100 | 1 | 1 | completa | Total; eventos.jsonl línea 48 |
| Inferencia | XGBRegressor | 0.021912000 | 1 | 1 | completa | Total; eventos.jsonl línea 49 |
| Inferencia | XGBRegressor | 0.027425000 | 1000 | 1 | completa | Total; eventos.jsonl línea 50 |
| Entrenamiento/refit | Ridge | 0.001307400 | 1000 | 1 | completa | Total; eventos.jsonl línea 51 |
| Inferencia | Ridge | 0.000172300 | 1000 | 1 | completa | Total; eventos.jsonl línea 52 |
| Inferencia | Ridge | 0.000133000 | 1 | 1 | completa | Total; eventos.jsonl línea 53 |
| Inferencia | XGBRegressor | 0.013029900 | 1 | 1 | completa | Total; eventos.jsonl línea 54 |
| Inferencia | XGBRegressor | 0.016635300 | 1000 | 1 | completa | Total; eventos.jsonl línea 55 |
| Entrenamiento/refit | Ridge | 0.001875200 | 1000 | 1 | completa | Total; eventos.jsonl línea 56 |
| Inferencia | Ridge | 0.000239600 | 1000 | 1 | completa | Total; eventos.jsonl línea 57 |
| Inferencia | Ridge | 0.000111900 | 1 | 1 | completa | Total; eventos.jsonl línea 58 |
| Inferencia | XGBRegressor | 0.011990500 | 1 | 1 | completa | Total; eventos.jsonl línea 59 |
| Inferencia | TransformedTargetRegressor | 0.024089800 | 1 | 1 | completa | Total; eventos.jsonl línea 60 |
| Inferencia | TransformedTargetRegressor | 0.009980800 | 188 | 1 | completa | Total; eventos.jsonl línea 61 |
| Inferencia | XGBRegressor | 0.019967100 | 1497 | 1 | completa | Total; eventos.jsonl línea 62 |
| Total del experimento | Verificación/preparación · --tests | 27.793955300 | No aplica | 1 | completa | Total; eventos.jsonl línea 63 |

### Ejecución `20261018_183243_253d607c`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-18T18:32:43.279338-05:00 a 2026-10-18T18:32:43.523032-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_183243_253d607c/metadata.json](tiempos/20261018_183243_253d607c/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_183243_253d607c/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.022025400 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.047580100 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.150613400 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000586100 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.243625300 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261018_183239_7cebda3a`

- **Modelo/motivo:** Verificación/preparación · Dash/prepare_deployment.py.
- **Fecha/zona:** 2026-10-18T18:32:39.950481-05:00 a 2026-10-18T18:32:44.327441-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_183239_7cebda3a/metadata.json](tiempos/20261018_183239_7cebda3a/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_183239_7cebda3a/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | XGBRegressor | 0.019287300 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Verificación/preparación · Dash/prepare_deployment.py | 4.378434700 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_183312_3d9689df`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-18T18:33:12.103305-05:00 a 2026-10-18T18:33:12.346511-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_183312_3d9689df/metadata.json](tiempos/20261018_183312_3d9689df/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_183312_3d9689df/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.023785300 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.046853400 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.153475100 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000591800 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.243922900 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261018_183316_9b1d8ab7`

- **Modelo/motivo:** TransformedTargetRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T18:33:16.663657-05:00 a 2026-10-18T18:33:16.697109-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_183316_9b1d8ab7/metadata.json](tiempos/20261018_183316_9b1d8ab7/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_183316_9b1d8ab7/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.011403400 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TransformedTargetRegressor · inferencia de aplicación | 0.023011900 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_183316_ceab67b9`

- **Modelo/motivo:** TruncatedNewtonKernelRidgeRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-18T18:33:16.710350-05:00 a 2026-10-18T18:33:16.726954-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_183316_ceab67b9/metadata.json](tiempos/20261018_183316_ceab67b9/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_183316_ceab67b9/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.009732800 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TruncatedNewtonKernelRidgeRegressor · inferencia de aplicación | 0.015476600 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261018_183308_4af79244`

- **Modelo/motivo:** Verificación/preparación · RenderDeploy/Dash/validate_package.py.
- **Fecha/zona:** 2026-10-18T18:33:08.592421-05:00 a 2026-10-18T18:33:18.649592-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_183308_4af79244/metadata.json](tiempos/20261018_183308_4af79244/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_183308_4af79244/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | XGBRegressor | 0.020448200 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | TransformedTargetRegressor | 0.022670500 | 188 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | TruncatedNewtonKernelRidgeRegressor | 0.016170200 | 188 | 1 | completa | Total; eventos.jsonl línea 3 |
| Inferencia | TransformedTargetRegressor | 0.006236600 | 1 | 1 | completa | Total; eventos.jsonl línea 4 |
| Inferencia | TruncatedNewtonKernelRidgeRegressor | 0.004895100 | 1 | 1 | completa | Total; eventos.jsonl línea 5 |
| Inferencia | DecisionTreeRegressor | 0.004246500 | 188 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | LinearSVR | 0.006742800 | 188 | 1 | completa | Total; eventos.jsonl línea 7 |
| Inferencia | KNeighborsRegressor | 0.017337700 | 188 | 1 | completa | Total; eventos.jsonl línea 8 |
| Inferencia | Ridge | 0.000175900 | 188 | 1 | completa | Total; eventos.jsonl línea 9 |
| Inferencia | Ridge | 0.007254600 | 188 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | Lasso | 0.006064800 | 188 | 1 | completa | Total; eventos.jsonl línea 11 |
| Inferencia | RandomForestRegressor | 0.031222800 | 188 | 1 | completa | Total; eventos.jsonl línea 12 |
| Inferencia | XGBRegressor | 0.013485100 | 188 | 1 | completa | Total; eventos.jsonl línea 13 |
| Inferencia | DecisionTreeRegressor | 0.004554800 | 188 | 1 | completa | Total; eventos.jsonl línea 14 |
| Inferencia | XGBRegressor | 0.011836400 | 1 | 1 | completa | Total; eventos.jsonl línea 15 |
| Inferencia | XGBRegressor | 0.016981600 | 1000 | 1 | completa | Total; eventos.jsonl línea 16 |
| Entrenamiento/refit | Ridge | 0.001116200 | 1000 | 1 | completa | Total; eventos.jsonl línea 17 |
| Inferencia | Ridge | 0.000164400 | 1000 | 1 | completa | Total; eventos.jsonl línea 18 |
| Inferencia | Ridge | 0.000101900 | 1 | 1 | completa | Total; eventos.jsonl línea 19 |
| Inferencia | XGBRegressor | 0.011730500 | 1 | 1 | completa | Total; eventos.jsonl línea 20 |
| Total del experimento | Verificación/preparación · RenderDeploy/Dash/validate_package.py | 10.055321600 | No aplica | 1 | completa | Total; eventos.jsonl línea 21 |

### Ejecución `20261018_192047_5135922c`

- **Modelo/motivo:** Book · evaluación, diagnósticos y SHAP de clásicos.
- **Fecha/zona:** 2026-10-18T19:20:47.183015-05:00 a 2026-10-18T19:22:38.978447-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_192047_5135922c/metadata.json](tiempos/20261018_192047_5135922c/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_192047_5135922c/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | svm / train completo in-sample | 0.012985000 | 1309 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | svm / test verificación | 0.022344700 | 188 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | knn / train completo in-sample | 0.026672800 | 1309 | 1 | completa | Total; eventos.jsonl línea 3 |
| Inferencia | knn / test verificación | 0.007957600 | 188 | 1 | completa | Total; eventos.jsonl línea 4 |
| Inferencia | ridge / train completo in-sample | 0.008383200 | 1309 | 1 | completa | Total; eventos.jsonl línea 5 |
| Inferencia | ridge / test verificación | 0.005594800 | 188 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | lasso / train completo in-sample | 0.006774000 | 1309 | 1 | completa | Total; eventos.jsonl línea 7 |
| Inferencia | lasso / test verificación | 0.005276200 | 188 | 1 | completa | Total; eventos.jsonl línea 8 |
| Inferencia | forest / train completo in-sample | 0.057442700 | 1309 | 1 | completa | Total; eventos.jsonl línea 9 |
| Inferencia | forest / test verificación | 0.039646900 | 188 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | xgboost / train completo in-sample | 0.022456100 | 1309 | 1 | completa | Total; eventos.jsonl línea 11 |
| Inferencia | xgboost / test verificación | 0.013556400 | 188 | 1 | completa | Total; eventos.jsonl línea 12 |
| Inferencia | decision_tree / train completo in-sample | 0.005480200 | 1309 | 1 | completa | Total; eventos.jsonl línea 13 |
| Inferencia | decision_tree / test verificación | 0.003732400 | 188 | 1 | completa | Total; eventos.jsonl línea 14 |
| Explicación SHAP | svm / test temporal | 0.014214800 | 188 | 1 | completa | Total; eventos.jsonl línea 15 |
| Explicación SHAP | knn / test temporal | 34.408128900 | 188 | 1 | completa | Total; eventos.jsonl línea 16 |
| Explicación SHAP | ridge / test temporal | 0.010129900 | 188 | 1 | completa | Total; eventos.jsonl línea 17 |
| Explicación SHAP | lasso / test temporal | 0.010303900 | 188 | 1 | completa | Total; eventos.jsonl línea 18 |
| Explicación SHAP | forest / test temporal | 34.654336900 | 188 | 1 | completa | Total; eventos.jsonl línea 19 |
| Explicación SHAP | xgboost / test temporal | 0.031310000 | 188 | 1 | completa | Total; eventos.jsonl línea 20 |
| Explicación SHAP | decision_tree / test temporal | 7.164881500 | 188 | 1 | completa | Total; eventos.jsonl línea 21 |
| Explicación SHAP | ridge / test · permutaciones de control | 7.273981200 | 188 | 1 | completa | Total; eventos.jsonl línea 22 |
| Explicación SHAP | xgboost / test · permutaciones de control | 17.605537700 | 188 | 1 | completa | Total; eventos.jsonl línea 23 |
| Explicación LIME | xgboost / test #124 | 0.069362600 | 1000 | 1 | completa | Total; eventos.jsonl línea 24 |
| Explicación LIME | xgboost / test #118 | 0.061732600 | 1000 | 1 | completa | Total; eventos.jsonl línea 25 |
| Total del experimento | Book · evaluación, diagnósticos y SHAP de clásicos | 111.794376600 | No aplica | 1 | completa | Total; eventos.jsonl línea 26 |

### Ejecución `20261018_191720_da359999`

- **Modelo/motivo:** Book · sensibilidad a semillas de clásicos y búsquedas.
- **Fecha/zona:** 2026-10-18T19:17:20.703204-05:00 a 2026-10-18T19:27:07.215359-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_191720_da359999/metadata.json](tiempos/20261018_191720_da359999/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_191720_da359999/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Entrenamiento/refit + inferencia | svm / sensibilidad semilla estimador | 4.019477000 | 1309 | 1 | completa | Total; eventos.jsonl línea 1 |
| Entrenamiento/refit | svm / semilla 42 / 1 | 0.069102700 | 1047 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | svm / semilla 42 / OOF 1 | 0.005401700 | 262 | 1 | completa | Total; eventos.jsonl línea 3 |
| Entrenamiento/refit | svm / semilla 42 / 2 | 0.076742000 | 1047 | 1 | completa | Total; eventos.jsonl línea 4 |
| Inferencia | svm / semilla 42 / OOF 2 | 0.007195800 | 262 | 1 | completa | Total; eventos.jsonl línea 5 |
| Entrenamiento/refit | svm / semilla 42 / 3 | 0.076958200 | 1047 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | svm / semilla 42 / OOF 3 | 0.005331300 | 262 | 1 | completa | Total; eventos.jsonl línea 7 |
| Entrenamiento/refit | svm / semilla 42 / 4 | 0.068423400 | 1047 | 1 | completa | Total; eventos.jsonl línea 8 |
| Inferencia | svm / semilla 42 / OOF 4 | 0.005454600 | 262 | 1 | completa | Total; eventos.jsonl línea 9 |
| Entrenamiento/refit | svm / semilla 42 / 5 | 0.021726700 | 1048 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | svm / semilla 42 / OOF 5 | 0.006563000 | 261 | 1 | completa | Total; eventos.jsonl línea 11 |
| Entrenamiento/refit | svm / semilla 42 / final | 0.018291900 | 1309 | 1 | completa | Total; eventos.jsonl línea 12 |
| Inferencia | svm / semilla 42 / test final | 0.006496100 | 188 | 1 | completa | Total; eventos.jsonl línea 13 |
| Entrenamiento/refit | svm / semilla 0 / 1 | 0.019576400 | 1047 | 1 | completa | Total; eventos.jsonl línea 14 |
| Inferencia | svm / semilla 0 / OOF 1 | 0.008481900 | 262 | 1 | completa | Total; eventos.jsonl línea 15 |
| Entrenamiento/refit | svm / semilla 0 / 2 | 0.029667100 | 1047 | 1 | completa | Total; eventos.jsonl línea 16 |
| Inferencia | svm / semilla 0 / OOF 2 | 0.008059200 | 262 | 1 | completa | Total; eventos.jsonl línea 17 |
| Entrenamiento/refit | svm / semilla 0 / 3 | 0.016157100 | 1047 | 1 | completa | Total; eventos.jsonl línea 18 |
| Inferencia | svm / semilla 0 / OOF 3 | 0.006601700 | 262 | 1 | completa | Total; eventos.jsonl línea 19 |
| Entrenamiento/refit | svm / semilla 0 / 4 | 0.015522400 | 1047 | 1 | completa | Total; eventos.jsonl línea 20 |
| Inferencia | svm / semilla 0 / OOF 4 | 0.007487800 | 262 | 1 | completa | Total; eventos.jsonl línea 21 |
| Entrenamiento/refit | svm / semilla 0 / 5 | 0.022204300 | 1048 | 1 | completa | Total; eventos.jsonl línea 22 |
| Inferencia | svm / semilla 0 / OOF 5 | 0.005504500 | 261 | 1 | completa | Total; eventos.jsonl línea 23 |
| Entrenamiento/refit | svm / semilla 0 / final | 0.022239100 | 1309 | 1 | completa | Total; eventos.jsonl línea 24 |
| Inferencia | svm / semilla 0 / test final | 0.006384600 | 188 | 1 | completa | Total; eventos.jsonl línea 25 |
| Entrenamiento/refit | svm / semilla 1 / 1 | 0.015210900 | 1047 | 1 | completa | Total; eventos.jsonl línea 26 |
| Inferencia | svm / semilla 1 / OOF 1 | 0.005622300 | 262 | 1 | completa | Total; eventos.jsonl línea 27 |
| Entrenamiento/refit | svm / semilla 1 / 2 | 0.032285500 | 1047 | 1 | completa | Total; eventos.jsonl línea 28 |
| Inferencia | svm / semilla 1 / OOF 2 | 0.006253700 | 262 | 1 | completa | Total; eventos.jsonl línea 29 |
| Entrenamiento/refit | svm / semilla 1 / 3 | 0.017077100 | 1047 | 1 | completa | Total; eventos.jsonl línea 30 |
| Inferencia | svm / semilla 1 / OOF 3 | 0.005653400 | 262 | 1 | completa | Total; eventos.jsonl línea 31 |
| Entrenamiento/refit | svm / semilla 1 / 4 | 0.016088300 | 1047 | 1 | completa | Total; eventos.jsonl línea 32 |
| Inferencia | svm / semilla 1 / OOF 4 | 0.005859100 | 262 | 1 | completa | Total; eventos.jsonl línea 33 |
| Entrenamiento/refit | svm / semilla 1 / 5 | 0.016654200 | 1048 | 1 | completa | Total; eventos.jsonl línea 34 |
| Inferencia | svm / semilla 1 / OOF 5 | 0.006578100 | 261 | 1 | completa | Total; eventos.jsonl línea 35 |
| Entrenamiento/refit | svm / semilla 1 / final | 0.019217900 | 1309 | 1 | completa | Total; eventos.jsonl línea 36 |
| Inferencia | svm / semilla 1 / test final | 0.007596200 | 188 | 1 | completa | Total; eventos.jsonl línea 37 |
| Entrenamiento/refit | svm / semilla 2 / 1 | 0.015438300 | 1047 | 1 | completa | Total; eventos.jsonl línea 38 |
| Inferencia | svm / semilla 2 / OOF 1 | 0.006154200 | 262 | 1 | completa | Total; eventos.jsonl línea 39 |
| Entrenamiento/refit | svm / semilla 2 / 2 | 0.031160300 | 1047 | 1 | completa | Total; eventos.jsonl línea 40 |
| Inferencia | svm / semilla 2 / OOF 2 | 0.005564900 | 262 | 1 | completa | Total; eventos.jsonl línea 41 |
| Entrenamiento/refit | svm / semilla 2 / 3 | 0.015096400 | 1047 | 1 | completa | Total; eventos.jsonl línea 42 |
| Inferencia | svm / semilla 2 / OOF 3 | 0.006372500 | 262 | 1 | completa | Total; eventos.jsonl línea 43 |
| Entrenamiento/refit | svm / semilla 2 / 4 | 0.015716100 | 1047 | 1 | completa | Total; eventos.jsonl línea 44 |
| Inferencia | svm / semilla 2 / OOF 4 | 0.006069300 | 262 | 1 | completa | Total; eventos.jsonl línea 45 |
| Entrenamiento/refit | svm / semilla 2 / 5 | 0.016667600 | 1048 | 1 | completa | Total; eventos.jsonl línea 46 |
| Inferencia | svm / semilla 2 / OOF 5 | 0.006785100 | 261 | 1 | completa | Total; eventos.jsonl línea 47 |
| Entrenamiento/refit | svm / semilla 2 / final | 0.018629400 | 1309 | 1 | completa | Total; eventos.jsonl línea 48 |
| Inferencia | svm / semilla 2 / test final | 0.005302600 | 188 | 1 | completa | Total; eventos.jsonl línea 49 |
| Entrenamiento/refit | svm / semilla 3 / 1 | 0.015697700 | 1047 | 1 | completa | Total; eventos.jsonl línea 50 |
| Inferencia | svm / semilla 3 / OOF 1 | 0.005216600 | 262 | 1 | completa | Total; eventos.jsonl línea 51 |
| Entrenamiento/refit | svm / semilla 3 / 2 | 0.027679500 | 1047 | 1 | completa | Total; eventos.jsonl línea 52 |
| Inferencia | svm / semilla 3 / OOF 2 | 0.005576300 | 262 | 1 | completa | Total; eventos.jsonl línea 53 |
| Entrenamiento/refit | svm / semilla 3 / 3 | 0.015472400 | 1047 | 1 | completa | Total; eventos.jsonl línea 54 |
| Inferencia | svm / semilla 3 / OOF 3 | 0.006076300 | 262 | 1 | completa | Total; eventos.jsonl línea 55 |
| Entrenamiento/refit | svm / semilla 3 / 4 | 0.016056600 | 1047 | 1 | completa | Total; eventos.jsonl línea 56 |
| Inferencia | svm / semilla 3 / OOF 4 | 0.005204400 | 262 | 1 | completa | Total; eventos.jsonl línea 57 |
| Entrenamiento/refit | svm / semilla 3 / 5 | 0.016734000 | 1048 | 1 | completa | Total; eventos.jsonl línea 58 |
| Inferencia | svm / semilla 3 / OOF 5 | 0.006378100 | 261 | 1 | completa | Total; eventos.jsonl línea 59 |
| Entrenamiento/refit | svm / semilla 3 / final | 0.019947600 | 1309 | 1 | completa | Total; eventos.jsonl línea 60 |
| Inferencia | svm / semilla 3 / test final | 0.006490100 | 188 | 1 | completa | Total; eventos.jsonl línea 61 |
| Entrenamiento/refit | svm / semilla 4 / 1 | 0.015638600 | 1047 | 1 | completa | Total; eventos.jsonl línea 62 |
| Inferencia | svm / semilla 4 / OOF 1 | 0.005496800 | 262 | 1 | completa | Total; eventos.jsonl línea 63 |
| Entrenamiento/refit | svm / semilla 4 / 2 | 0.033301600 | 1047 | 1 | completa | Total; eventos.jsonl línea 64 |
| Inferencia | svm / semilla 4 / OOF 2 | 0.007869800 | 262 | 1 | completa | Total; eventos.jsonl línea 65 |
| Entrenamiento/refit | svm / semilla 4 / 3 | 0.016044700 | 1047 | 1 | completa | Total; eventos.jsonl línea 66 |
| Inferencia | svm / semilla 4 / OOF 3 | 0.005649400 | 262 | 1 | completa | Total; eventos.jsonl línea 67 |
| Entrenamiento/refit | svm / semilla 4 / 4 | 0.020902200 | 1047 | 1 | completa | Total; eventos.jsonl línea 68 |
| Inferencia | svm / semilla 4 / OOF 4 | 0.007987100 | 262 | 1 | completa | Total; eventos.jsonl línea 69 |
| Entrenamiento/refit | svm / semilla 4 / 5 | 0.017022500 | 1048 | 1 | completa | Total; eventos.jsonl línea 70 |
| Inferencia | svm / semilla 4 / OOF 5 | 0.005879100 | 261 | 1 | completa | Total; eventos.jsonl línea 71 |
| Entrenamiento/refit | svm / semilla 4 / final | 0.018389100 | 1309 | 1 | completa | Total; eventos.jsonl línea 72 |
| Inferencia | svm / semilla 4 / test final | 0.005938400 | 188 | 1 | completa | Total; eventos.jsonl línea 73 |
| Entrenamiento/refit | svm / semilla 5 / 1 | 0.016518300 | 1047 | 1 | completa | Total; eventos.jsonl línea 74 |
| Inferencia | svm / semilla 5 / OOF 1 | 0.005329500 | 262 | 1 | completa | Total; eventos.jsonl línea 75 |
| Entrenamiento/refit | svm / semilla 5 / 2 | 0.026573000 | 1047 | 1 | completa | Total; eventos.jsonl línea 76 |
| Inferencia | svm / semilla 5 / OOF 2 | 0.005577300 | 262 | 1 | completa | Total; eventos.jsonl línea 77 |
| Entrenamiento/refit | svm / semilla 5 / 3 | 0.021034300 | 1047 | 1 | completa | Total; eventos.jsonl línea 78 |
| Inferencia | svm / semilla 5 / OOF 3 | 0.005763100 | 262 | 1 | completa | Total; eventos.jsonl línea 79 |
| Entrenamiento/refit | svm / semilla 5 / 4 | 0.016444900 | 1047 | 1 | completa | Total; eventos.jsonl línea 80 |
| Inferencia | svm / semilla 5 / OOF 4 | 0.006501500 | 262 | 1 | completa | Total; eventos.jsonl línea 81 |
| Entrenamiento/refit | svm / semilla 5 / 5 | 0.016209500 | 1048 | 1 | completa | Total; eventos.jsonl línea 82 |
| Inferencia | svm / semilla 5 / OOF 5 | 0.006617500 | 261 | 1 | completa | Total; eventos.jsonl línea 83 |
| Entrenamiento/refit | svm / semilla 5 / final | 0.022824300 | 1309 | 1 | completa | Total; eventos.jsonl línea 84 |
| Inferencia | svm / semilla 5 / test final | 0.008069300 | 188 | 1 | completa | Total; eventos.jsonl línea 85 |
| Entrenamiento/refit | svm / semilla 6 / 1 | 0.015174400 | 1047 | 1 | completa | Total; eventos.jsonl línea 86 |
| Inferencia | svm / semilla 6 / OOF 1 | 0.006714600 | 262 | 1 | completa | Total; eventos.jsonl línea 87 |
| Entrenamiento/refit | svm / semilla 6 / 2 | 0.030111200 | 1047 | 1 | completa | Total; eventos.jsonl línea 88 |
| Inferencia | svm / semilla 6 / OOF 2 | 0.007727600 | 262 | 1 | completa | Total; eventos.jsonl línea 89 |
| Entrenamiento/refit | svm / semilla 6 / 3 | 0.015666200 | 1047 | 1 | completa | Total; eventos.jsonl línea 90 |
| Inferencia | svm / semilla 6 / OOF 3 | 0.005163500 | 262 | 1 | completa | Total; eventos.jsonl línea 91 |
| Entrenamiento/refit | svm / semilla 6 / 4 | 0.016244200 | 1047 | 1 | completa | Total; eventos.jsonl línea 92 |
| Inferencia | svm / semilla 6 / OOF 4 | 0.006182200 | 262 | 1 | completa | Total; eventos.jsonl línea 93 |
| Entrenamiento/refit | svm / semilla 6 / 5 | 0.021289000 | 1048 | 1 | completa | Total; eventos.jsonl línea 94 |
| Inferencia | svm / semilla 6 / OOF 5 | 0.008072100 | 261 | 1 | completa | Total; eventos.jsonl línea 95 |
| Entrenamiento/refit | svm / semilla 6 / final | 0.017552000 | 1309 | 1 | completa | Total; eventos.jsonl línea 96 |
| Inferencia | svm / semilla 6 / test final | 0.005658900 | 188 | 1 | completa | Total; eventos.jsonl línea 97 |
| Entrenamiento/refit | svm / semilla 7 / 1 | 0.015903400 | 1047 | 1 | completa | Total; eventos.jsonl línea 98 |
| Inferencia | svm / semilla 7 / OOF 1 | 0.005295400 | 262 | 1 | completa | Total; eventos.jsonl línea 99 |
| Entrenamiento/refit | svm / semilla 7 / 2 | 0.027354700 | 1047 | 1 | completa | Total; eventos.jsonl línea 100 |
| Inferencia | svm / semilla 7 / OOF 2 | 0.010570300 | 262 | 1 | completa | Total; eventos.jsonl línea 101 |
| Entrenamiento/refit | svm / semilla 7 / 3 | 0.015202900 | 1047 | 1 | completa | Total; eventos.jsonl línea 102 |
| Inferencia | svm / semilla 7 / OOF 3 | 0.005521300 | 262 | 1 | completa | Total; eventos.jsonl línea 103 |
| Entrenamiento/refit | svm / semilla 7 / 4 | 0.015504800 | 1047 | 1 | completa | Total; eventos.jsonl línea 104 |
| Inferencia | svm / semilla 7 / OOF 4 | 0.006421400 | 262 | 1 | completa | Total; eventos.jsonl línea 105 |
| Entrenamiento/refit | svm / semilla 7 / 5 | 0.016474100 | 1048 | 1 | completa | Total; eventos.jsonl línea 106 |
| Inferencia | svm / semilla 7 / OOF 5 | 0.005500100 | 261 | 1 | completa | Total; eventos.jsonl línea 107 |
| Entrenamiento/refit | svm / semilla 7 / final | 0.021345200 | 1309 | 1 | completa | Total; eventos.jsonl línea 108 |
| Inferencia | svm / semilla 7 / test final | 0.007718600 | 188 | 1 | completa | Total; eventos.jsonl línea 109 |
| Entrenamiento/refit | svm / semilla 8 / 1 | 0.015699400 | 1047 | 1 | completa | Total; eventos.jsonl línea 110 |
| Inferencia | svm / semilla 8 / OOF 1 | 0.005098300 | 262 | 1 | completa | Total; eventos.jsonl línea 111 |
| Entrenamiento/refit | svm / semilla 8 / 2 | 0.026474600 | 1047 | 1 | completa | Total; eventos.jsonl línea 112 |
| Inferencia | svm / semilla 8 / OOF 2 | 0.006057500 | 262 | 1 | completa | Total; eventos.jsonl línea 113 |
| Entrenamiento/refit | svm / semilla 8 / 3 | 0.014630300 | 1047 | 1 | completa | Total; eventos.jsonl línea 114 |
| Inferencia | svm / semilla 8 / OOF 3 | 0.005386600 | 262 | 1 | completa | Total; eventos.jsonl línea 115 |
| Entrenamiento/refit | svm / semilla 8 / 4 | 0.017817300 | 1047 | 1 | completa | Total; eventos.jsonl línea 116 |
| Inferencia | svm / semilla 8 / OOF 4 | 0.007101300 | 262 | 1 | completa | Total; eventos.jsonl línea 117 |
| Entrenamiento/refit | svm / semilla 8 / 5 | 0.018210200 | 1048 | 1 | completa | Total; eventos.jsonl línea 118 |
| Inferencia | svm / semilla 8 / OOF 5 | 0.005601600 | 261 | 1 | completa | Total; eventos.jsonl línea 119 |
| Entrenamiento/refit | svm / semilla 8 / final | 0.017588800 | 1309 | 1 | completa | Total; eventos.jsonl línea 120 |
| Inferencia | svm / semilla 8 / test final | 0.007592800 | 188 | 1 | completa | Total; eventos.jsonl línea 121 |
| Entrenamiento/refit | svm / semilla 9 / 1 | 0.014066600 | 1047 | 1 | completa | Total; eventos.jsonl línea 122 |
| Inferencia | svm / semilla 9 / OOF 1 | 0.008566400 | 262 | 1 | completa | Total; eventos.jsonl línea 123 |
| Entrenamiento/refit | svm / semilla 9 / 2 | 0.029408000 | 1047 | 1 | completa | Total; eventos.jsonl línea 124 |
| Inferencia | svm / semilla 9 / OOF 2 | 0.006786300 | 262 | 1 | completa | Total; eventos.jsonl línea 125 |
| Entrenamiento/refit | svm / semilla 9 / 3 | 0.017621500 | 1047 | 1 | completa | Total; eventos.jsonl línea 126 |
| Inferencia | svm / semilla 9 / OOF 3 | 0.007792100 | 262 | 1 | completa | Total; eventos.jsonl línea 127 |
| Entrenamiento/refit | svm / semilla 9 / 4 | 0.015058900 | 1047 | 1 | completa | Total; eventos.jsonl línea 128 |
| Inferencia | svm / semilla 9 / OOF 4 | 0.005025800 | 262 | 1 | completa | Total; eventos.jsonl línea 129 |
| Entrenamiento/refit | svm / semilla 9 / 5 | 0.017378000 | 1048 | 1 | completa | Total; eventos.jsonl línea 130 |
| Inferencia | svm / semilla 9 / OOF 5 | 0.006055700 | 261 | 1 | completa | Total; eventos.jsonl línea 131 |
| Entrenamiento/refit | svm / semilla 9 / final | 0.020402500 | 1309 | 1 | completa | Total; eventos.jsonl línea 132 |
| Inferencia | svm / semilla 9 / test final | 0.005102200 | 188 | 1 | completa | Total; eventos.jsonl línea 133 |
| Entrenamiento/refit + inferencia | forest / sensibilidad semilla estimador | 16.995388300 | 1309 | 1 | completa | Total; eventos.jsonl línea 134 |
| Entrenamiento/refit | forest / semilla 42 / 1 | 0.631620100 | 1047 | 1 | completa | Total; eventos.jsonl línea 135 |
| Inferencia | forest / semilla 42 / OOF 1 | 0.020308000 | 262 | 1 | completa | Total; eventos.jsonl línea 136 |
| Entrenamiento/refit | forest / semilla 42 / 2 | 0.993543300 | 1047 | 1 | completa | Total; eventos.jsonl línea 137 |
| Inferencia | forest / semilla 42 / OOF 2 | 0.038666700 | 262 | 1 | completa | Total; eventos.jsonl línea 138 |
| Entrenamiento/refit | forest / semilla 42 / 3 | 0.599687100 | 1047 | 1 | completa | Total; eventos.jsonl línea 139 |
| Inferencia | forest / semilla 42 / OOF 3 | 0.020660900 | 262 | 1 | completa | Total; eventos.jsonl línea 140 |
| Entrenamiento/refit | forest / semilla 42 / 4 | 0.863808900 | 1047 | 1 | completa | Total; eventos.jsonl línea 141 |
| Inferencia | forest / semilla 42 / OOF 4 | 0.031034200 | 262 | 1 | completa | Total; eventos.jsonl línea 142 |
| Entrenamiento/refit | forest / semilla 42 / 5 | 1.108283000 | 1048 | 1 | completa | Total; eventos.jsonl línea 143 |
| Inferencia | forest / semilla 42 / OOF 5 | 0.034579000 | 261 | 1 | completa | Total; eventos.jsonl línea 144 |
| Entrenamiento/refit | forest / semilla 42 / final | 1.105620100 | 1309 | 1 | completa | Total; eventos.jsonl línea 145 |
| Inferencia | forest / semilla 42 / test final | 0.036698600 | 188 | 1 | completa | Total; eventos.jsonl línea 146 |
| Entrenamiento/refit | forest / semilla 0 / 1 | 0.590954400 | 1047 | 1 | completa | Total; eventos.jsonl línea 147 |
| Inferencia | forest / semilla 0 / OOF 1 | 0.020537100 | 262 | 1 | completa | Total; eventos.jsonl línea 148 |
| Entrenamiento/refit | forest / semilla 0 / 2 | 0.983363400 | 1047 | 1 | completa | Total; eventos.jsonl línea 149 |
| Inferencia | forest / semilla 0 / OOF 2 | 0.041773300 | 262 | 1 | completa | Total; eventos.jsonl línea 150 |
| Entrenamiento/refit | forest / semilla 0 / 3 | 0.531769300 | 1047 | 1 | completa | Total; eventos.jsonl línea 151 |
| Inferencia | forest / semilla 0 / OOF 3 | 0.025995000 | 262 | 1 | completa | Total; eventos.jsonl línea 152 |
| Entrenamiento/refit | forest / semilla 0 / 4 | 0.850499800 | 1047 | 1 | completa | Total; eventos.jsonl línea 153 |
| Inferencia | forest / semilla 0 / OOF 4 | 0.029146800 | 262 | 1 | completa | Total; eventos.jsonl línea 154 |
| Entrenamiento/refit | forest / semilla 0 / 5 | 1.141446300 | 1048 | 1 | completa | Total; eventos.jsonl línea 155 |
| Inferencia | forest / semilla 0 / OOF 5 | 0.039618800 | 261 | 1 | completa | Total; eventos.jsonl línea 156 |
| Entrenamiento/refit | forest / semilla 0 / final | 1.124461300 | 1309 | 1 | completa | Total; eventos.jsonl línea 157 |
| Inferencia | forest / semilla 0 / test final | 0.031585500 | 188 | 1 | completa | Total; eventos.jsonl línea 158 |
| Entrenamiento/refit | forest / semilla 1 / 1 | 0.578992700 | 1047 | 1 | completa | Total; eventos.jsonl línea 159 |
| Inferencia | forest / semilla 1 / OOF 1 | 0.020332000 | 262 | 1 | completa | Total; eventos.jsonl línea 160 |
| Entrenamiento/refit | forest / semilla 1 / 2 | 0.980107100 | 1047 | 1 | completa | Total; eventos.jsonl línea 161 |
| Inferencia | forest / semilla 1 / OOF 2 | 0.034612700 | 262 | 1 | completa | Total; eventos.jsonl línea 162 |
| Entrenamiento/refit | forest / semilla 1 / 3 | 0.548368500 | 1047 | 1 | completa | Total; eventos.jsonl línea 163 |
| Inferencia | forest / semilla 1 / OOF 3 | 0.024273200 | 262 | 1 | completa | Total; eventos.jsonl línea 164 |
| Entrenamiento/refit | forest / semilla 1 / 4 | 0.852112700 | 1047 | 1 | completa | Total; eventos.jsonl línea 165 |
| Inferencia | forest / semilla 1 / OOF 4 | 0.054396200 | 262 | 1 | completa | Total; eventos.jsonl línea 166 |
| Entrenamiento/refit | forest / semilla 1 / 5 | 1.220093400 | 1048 | 1 | completa | Total; eventos.jsonl línea 167 |
| Inferencia | forest / semilla 1 / OOF 5 | 0.053076000 | 261 | 1 | completa | Total; eventos.jsonl línea 168 |
| Entrenamiento/refit | forest / semilla 1 / final | 1.186203400 | 1309 | 1 | completa | Total; eventos.jsonl línea 169 |
| Inferencia | forest / semilla 1 / test final | 0.048364700 | 188 | 1 | completa | Total; eventos.jsonl línea 170 |
| Entrenamiento/refit | forest / semilla 2 / 1 | 0.640518800 | 1047 | 1 | completa | Total; eventos.jsonl línea 171 |
| Inferencia | forest / semilla 2 / OOF 1 | 0.030287400 | 262 | 1 | completa | Total; eventos.jsonl línea 172 |
| Entrenamiento/refit | forest / semilla 2 / 2 | 1.113734400 | 1047 | 1 | completa | Total; eventos.jsonl línea 173 |
| Inferencia | forest / semilla 2 / OOF 2 | 0.051538000 | 262 | 1 | completa | Total; eventos.jsonl línea 174 |
| Entrenamiento/refit | forest / semilla 2 / 3 | 0.618240000 | 1047 | 1 | completa | Total; eventos.jsonl línea 175 |
| Inferencia | forest / semilla 2 / OOF 3 | 0.029283800 | 262 | 1 | completa | Total; eventos.jsonl línea 176 |
| Entrenamiento/refit | forest / semilla 2 / 4 | 1.006665500 | 1047 | 1 | completa | Total; eventos.jsonl línea 177 |
| Inferencia | forest / semilla 2 / OOF 4 | 0.047157500 | 262 | 1 | completa | Total; eventos.jsonl línea 178 |
| Entrenamiento/refit | forest / semilla 2 / 5 | 1.344836200 | 1048 | 1 | completa | Total; eventos.jsonl línea 179 |
| Inferencia | forest / semilla 2 / OOF 5 | 0.058975700 | 261 | 1 | completa | Total; eventos.jsonl línea 180 |
| Entrenamiento/refit | forest / semilla 2 / final | 1.314907000 | 1309 | 1 | completa | Total; eventos.jsonl línea 181 |
| Inferencia | forest / semilla 2 / test final | 0.051284100 | 188 | 1 | completa | Total; eventos.jsonl línea 182 |
| Entrenamiento/refit | forest / semilla 3 / 1 | 0.695505400 | 1047 | 1 | completa | Total; eventos.jsonl línea 183 |
| Inferencia | forest / semilla 3 / OOF 1 | 0.033234700 | 262 | 1 | completa | Total; eventos.jsonl línea 184 |
| Entrenamiento/refit | forest / semilla 3 / 2 | 1.184444400 | 1047 | 1 | completa | Total; eventos.jsonl línea 185 |
| Inferencia | forest / semilla 3 / OOF 2 | 0.053510200 | 262 | 1 | completa | Total; eventos.jsonl línea 186 |
| Entrenamiento/refit | forest / semilla 3 / 3 | 0.647668400 | 1047 | 1 | completa | Total; eventos.jsonl línea 187 |
| Inferencia | forest / semilla 3 / OOF 3 | 0.029304800 | 262 | 1 | completa | Total; eventos.jsonl línea 188 |
| Entrenamiento/refit | forest / semilla 3 / 4 | 1.138634000 | 1047 | 1 | completa | Total; eventos.jsonl línea 189 |
| Inferencia | forest / semilla 3 / OOF 4 | 0.039261800 | 262 | 1 | completa | Total; eventos.jsonl línea 190 |
| Entrenamiento/refit | forest / semilla 3 / 5 | 1.491390600 | 1048 | 1 | completa | Total; eventos.jsonl línea 191 |
| Inferencia | forest / semilla 3 / OOF 5 | 0.061906000 | 261 | 1 | completa | Total; eventos.jsonl línea 192 |
| Entrenamiento/refit | forest / semilla 3 / final | 1.525382000 | 1309 | 1 | completa | Total; eventos.jsonl línea 193 |
| Inferencia | forest / semilla 3 / test final | 0.051179300 | 188 | 1 | completa | Total; eventos.jsonl línea 194 |
| Entrenamiento/refit | forest / semilla 4 / 1 | 0.821476100 | 1047 | 1 | completa | Total; eventos.jsonl línea 195 |
| Inferencia | forest / semilla 4 / OOF 1 | 0.039678500 | 262 | 1 | completa | Total; eventos.jsonl línea 196 |
| Entrenamiento/refit | forest / semilla 4 / 2 | 1.322911700 | 1047 | 1 | completa | Total; eventos.jsonl línea 197 |
| Inferencia | forest / semilla 4 / OOF 2 | 0.065930200 | 262 | 1 | completa | Total; eventos.jsonl línea 198 |
| Entrenamiento/refit | forest / semilla 4 / 3 | 0.760674600 | 1047 | 1 | completa | Total; eventos.jsonl línea 199 |
| Inferencia | forest / semilla 4 / OOF 3 | 0.035286900 | 262 | 1 | completa | Total; eventos.jsonl línea 200 |
| Entrenamiento/refit | forest / semilla 4 / 4 | 1.152374400 | 1047 | 1 | completa | Total; eventos.jsonl línea 201 |
| Inferencia | forest / semilla 4 / OOF 4 | 0.044944800 | 262 | 1 | completa | Total; eventos.jsonl línea 202 |
| Entrenamiento/refit | forest / semilla 4 / 5 | 1.462535000 | 1048 | 1 | completa | Total; eventos.jsonl línea 203 |
| Inferencia | forest / semilla 4 / OOF 5 | 0.048059700 | 261 | 1 | completa | Total; eventos.jsonl línea 204 |
| Entrenamiento/refit | forest / semilla 4 / final | 1.379054100 | 1309 | 1 | completa | Total; eventos.jsonl línea 205 |
| Inferencia | forest / semilla 4 / test final | 0.037235800 | 188 | 1 | completa | Total; eventos.jsonl línea 206 |
| Entrenamiento/refit | forest / semilla 5 / 1 | 0.750178400 | 1047 | 1 | completa | Total; eventos.jsonl línea 207 |
| Inferencia | forest / semilla 5 / OOF 1 | 0.027251900 | 262 | 1 | completa | Total; eventos.jsonl línea 208 |
| Entrenamiento/refit | forest / semilla 5 / 2 | 1.164172200 | 1047 | 1 | completa | Total; eventos.jsonl línea 209 |
| Inferencia | forest / semilla 5 / OOF 2 | 0.038510400 | 262 | 1 | completa | Total; eventos.jsonl línea 210 |
| Entrenamiento/refit | forest / semilla 5 / 3 | 0.643904600 | 1047 | 1 | completa | Total; eventos.jsonl línea 211 |
| Inferencia | forest / semilla 5 / OOF 3 | 0.031331500 | 262 | 1 | completa | Total; eventos.jsonl línea 212 |
| Entrenamiento/refit | forest / semilla 5 / 4 | 0.976939000 | 1047 | 1 | completa | Total; eventos.jsonl línea 213 |
| Inferencia | forest / semilla 5 / OOF 4 | 0.032985200 | 262 | 1 | completa | Total; eventos.jsonl línea 214 |
| Entrenamiento/refit | forest / semilla 5 / 5 | 1.296745200 | 1048 | 1 | completa | Total; eventos.jsonl línea 215 |
| Inferencia | forest / semilla 5 / OOF 5 | 0.048933300 | 261 | 1 | completa | Total; eventos.jsonl línea 216 |
| Entrenamiento/refit | forest / semilla 5 / final | 1.300351300 | 1309 | 1 | completa | Total; eventos.jsonl línea 217 |
| Inferencia | forest / semilla 5 / test final | 0.050859500 | 188 | 1 | completa | Total; eventos.jsonl línea 218 |
| Entrenamiento/refit | forest / semilla 6 / 1 | 0.693291000 | 1047 | 1 | completa | Total; eventos.jsonl línea 219 |
| Inferencia | forest / semilla 6 / OOF 1 | 0.028325900 | 262 | 1 | completa | Total; eventos.jsonl línea 220 |
| Entrenamiento/refit | forest / semilla 6 / 2 | 1.165956700 | 1047 | 1 | completa | Total; eventos.jsonl línea 221 |
| Inferencia | forest / semilla 6 / OOF 2 | 0.054901800 | 262 | 1 | completa | Total; eventos.jsonl línea 222 |
| Entrenamiento/refit | forest / semilla 6 / 3 | 0.638067000 | 1047 | 1 | completa | Total; eventos.jsonl línea 223 |
| Inferencia | forest / semilla 6 / OOF 3 | 0.032051900 | 262 | 1 | completa | Total; eventos.jsonl línea 224 |
| Entrenamiento/refit | forest / semilla 6 / 4 | 1.004865700 | 1047 | 1 | completa | Total; eventos.jsonl línea 225 |
| Inferencia | forest / semilla 6 / OOF 4 | 0.036152500 | 262 | 1 | completa | Total; eventos.jsonl línea 226 |
| Entrenamiento/refit | forest / semilla 6 / 5 | 1.322376300 | 1048 | 1 | completa | Total; eventos.jsonl línea 227 |
| Inferencia | forest / semilla 6 / OOF 5 | 0.038266500 | 261 | 1 | completa | Total; eventos.jsonl línea 228 |
| Entrenamiento/refit | forest / semilla 6 / final | 1.280815100 | 1309 | 1 | completa | Total; eventos.jsonl línea 229 |
| Inferencia | forest / semilla 6 / test final | 0.029339200 | 188 | 1 | completa | Total; eventos.jsonl línea 230 |
| Entrenamiento/refit | forest / semilla 7 / 1 | 0.684334900 | 1047 | 1 | completa | Total; eventos.jsonl línea 231 |
| Inferencia | forest / semilla 7 / OOF 1 | 0.037005300 | 262 | 1 | completa | Total; eventos.jsonl línea 232 |
| Entrenamiento/refit | forest / semilla 7 / 2 | 1.055782000 | 1047 | 1 | completa | Total; eventos.jsonl línea 233 |
| Inferencia | forest / semilla 7 / OOF 2 | 0.037514900 | 262 | 1 | completa | Total; eventos.jsonl línea 234 |
| Entrenamiento/refit | forest / semilla 7 / 3 | 0.569757600 | 1047 | 1 | completa | Total; eventos.jsonl línea 235 |
| Inferencia | forest / semilla 7 / OOF 3 | 0.019798500 | 262 | 1 | completa | Total; eventos.jsonl línea 236 |
| Entrenamiento/refit | forest / semilla 7 / 4 | 0.839737300 | 1047 | 1 | completa | Total; eventos.jsonl línea 237 |
| Inferencia | forest / semilla 7 / OOF 4 | 0.034549100 | 262 | 1 | completa | Total; eventos.jsonl línea 238 |
| Entrenamiento/refit | forest / semilla 7 / 5 | 1.133360400 | 1048 | 1 | completa | Total; eventos.jsonl línea 239 |
| Inferencia | forest / semilla 7 / OOF 5 | 0.035382000 | 261 | 1 | completa | Total; eventos.jsonl línea 240 |
| Entrenamiento/refit | forest / semilla 7 / final | 1.088667400 | 1309 | 1 | completa | Total; eventos.jsonl línea 241 |
| Inferencia | forest / semilla 7 / test final | 0.032042200 | 188 | 1 | completa | Total; eventos.jsonl línea 242 |
| Entrenamiento/refit | forest / semilla 8 / 1 | 0.567504900 | 1047 | 1 | completa | Total; eventos.jsonl línea 243 |
| Inferencia | forest / semilla 8 / OOF 1 | 0.021342400 | 262 | 1 | completa | Total; eventos.jsonl línea 244 |
| Entrenamiento/refit | forest / semilla 8 / 2 | 0.991738800 | 1047 | 1 | completa | Total; eventos.jsonl línea 245 |
| Inferencia | forest / semilla 8 / OOF 2 | 0.037916900 | 262 | 1 | completa | Total; eventos.jsonl línea 246 |
| Entrenamiento/refit | forest / semilla 8 / 3 | 0.549358000 | 1047 | 1 | completa | Total; eventos.jsonl línea 247 |
| Inferencia | forest / semilla 8 / OOF 3 | 0.020301900 | 262 | 1 | completa | Total; eventos.jsonl línea 248 |
| Entrenamiento/refit | forest / semilla 8 / 4 | 0.856552300 | 1047 | 1 | completa | Total; eventos.jsonl línea 249 |
| Inferencia | forest / semilla 8 / OOF 4 | 0.029418300 | 262 | 1 | completa | Total; eventos.jsonl línea 250 |
| Entrenamiento/refit | forest / semilla 8 / 5 | 1.131819700 | 1048 | 1 | completa | Total; eventos.jsonl línea 251 |
| Inferencia | forest / semilla 8 / OOF 5 | 0.035038800 | 261 | 1 | completa | Total; eventos.jsonl línea 252 |
| Entrenamiento/refit | forest / semilla 8 / final | 1.103494700 | 1309 | 1 | completa | Total; eventos.jsonl línea 253 |
| Inferencia | forest / semilla 8 / test final | 0.030584100 | 188 | 1 | completa | Total; eventos.jsonl línea 254 |
| Entrenamiento/refit | forest / semilla 9 / 1 | 0.573548900 | 1047 | 1 | completa | Total; eventos.jsonl línea 255 |
| Inferencia | forest / semilla 9 / OOF 1 | 0.021132300 | 262 | 1 | completa | Total; eventos.jsonl línea 256 |
| Entrenamiento/refit | forest / semilla 9 / 2 | 0.962472200 | 1047 | 1 | completa | Total; eventos.jsonl línea 257 |
| Inferencia | forest / semilla 9 / OOF 2 | 0.042508800 | 262 | 1 | completa | Total; eventos.jsonl línea 258 |
| Entrenamiento/refit | forest / semilla 9 / 3 | 0.543220800 | 1047 | 1 | completa | Total; eventos.jsonl línea 259 |
| Inferencia | forest / semilla 9 / OOF 3 | 0.019622400 | 262 | 1 | completa | Total; eventos.jsonl línea 260 |
| Entrenamiento/refit | forest / semilla 9 / 4 | 0.814877700 | 1047 | 1 | completa | Total; eventos.jsonl línea 261 |
| Inferencia | forest / semilla 9 / OOF 4 | 0.030847100 | 262 | 1 | completa | Total; eventos.jsonl línea 262 |
| Entrenamiento/refit | forest / semilla 9 / 5 | 1.094187800 | 1048 | 1 | completa | Total; eventos.jsonl línea 263 |
| Inferencia | forest / semilla 9 / OOF 5 | 0.036184600 | 261 | 1 | completa | Total; eventos.jsonl línea 264 |
| Entrenamiento/refit | forest / semilla 9 / final | 1.075205000 | 1309 | 1 | completa | Total; eventos.jsonl línea 265 |
| Inferencia | forest / semilla 9 / test final | 0.032415200 | 188 | 1 | completa | Total; eventos.jsonl línea 266 |
| Entrenamiento/refit + inferencia | xgboost / sensibilidad semilla estimador | 6.662322800 | 1309 | 1 | completa | Total; eventos.jsonl línea 267 |
| Entrenamiento/refit | xgboost / semilla 42 / 1 | 0.379993100 | 1047 | 1 | completa | Total; eventos.jsonl línea 268 |
| Inferencia | xgboost / semilla 42 / OOF 1 | 0.027054200 | 262 | 1 | completa | Total; eventos.jsonl línea 269 |
| Entrenamiento/refit | xgboost / semilla 42 / 2 | 0.335716700 | 1047 | 1 | completa | Total; eventos.jsonl línea 270 |
| Inferencia | xgboost / semilla 42 / OOF 2 | 0.013096800 | 262 | 1 | completa | Total; eventos.jsonl línea 271 |
| Entrenamiento/refit | xgboost / semilla 42 / 3 | 0.506743000 | 1047 | 1 | completa | Total; eventos.jsonl línea 272 |
| Inferencia | xgboost / semilla 42 / OOF 3 | 0.023960300 | 262 | 1 | completa | Total; eventos.jsonl línea 273 |
| Entrenamiento/refit | xgboost / semilla 42 / 4 | 0.411870500 | 1047 | 1 | completa | Total; eventos.jsonl línea 274 |
| Inferencia | xgboost / semilla 42 / OOF 4 | 0.014240300 | 262 | 1 | completa | Total; eventos.jsonl línea 275 |
| Entrenamiento/refit | xgboost / semilla 42 / 5 | 0.354627900 | 1048 | 1 | completa | Total; eventos.jsonl línea 276 |
| Inferencia | xgboost / semilla 42 / OOF 5 | 0.012684000 | 261 | 1 | completa | Total; eventos.jsonl línea 277 |
| Entrenamiento/refit | xgboost / semilla 42 / final | 0.446285400 | 1309 | 1 | completa | Total; eventos.jsonl línea 278 |
| Inferencia | xgboost / semilla 42 / test final | 0.014591400 | 188 | 1 | completa | Total; eventos.jsonl línea 279 |
| Entrenamiento/refit | xgboost / semilla 0 / 1 | 0.414139800 | 1047 | 1 | completa | Total; eventos.jsonl línea 280 |
| Inferencia | xgboost / semilla 0 / OOF 1 | 0.013313500 | 262 | 1 | completa | Total; eventos.jsonl línea 281 |
| Entrenamiento/refit | xgboost / semilla 0 / 2 | 0.315061900 | 1047 | 1 | completa | Total; eventos.jsonl línea 282 |
| Inferencia | xgboost / semilla 0 / OOF 2 | 0.013600200 | 262 | 1 | completa | Total; eventos.jsonl línea 283 |
| Entrenamiento/refit | xgboost / semilla 0 / 3 | 0.463075700 | 1047 | 1 | completa | Total; eventos.jsonl línea 284 |
| Inferencia | xgboost / semilla 0 / OOF 3 | 0.015155800 | 262 | 1 | completa | Total; eventos.jsonl línea 285 |
| Entrenamiento/refit | xgboost / semilla 0 / 4 | 0.389878300 | 1047 | 1 | completa | Total; eventos.jsonl línea 286 |
| Inferencia | xgboost / semilla 0 / OOF 4 | 0.014067500 | 262 | 1 | completa | Total; eventos.jsonl línea 287 |
| Entrenamiento/refit | xgboost / semilla 0 / 5 | 0.312312500 | 1048 | 1 | completa | Total; eventos.jsonl línea 288 |
| Inferencia | xgboost / semilla 0 / OOF 5 | 0.012954500 | 261 | 1 | completa | Total; eventos.jsonl línea 289 |
| Entrenamiento/refit | xgboost / semilla 0 / final | 0.404429100 | 1309 | 1 | completa | Total; eventos.jsonl línea 290 |
| Inferencia | xgboost / semilla 0 / test final | 0.011555000 | 188 | 1 | completa | Total; eventos.jsonl línea 291 |
| Entrenamiento/refit | xgboost / semilla 1 / 1 | 0.363918600 | 1047 | 1 | completa | Total; eventos.jsonl línea 292 |
| Inferencia | xgboost / semilla 1 / OOF 1 | 0.013379800 | 262 | 1 | completa | Total; eventos.jsonl línea 293 |
| Entrenamiento/refit | xgboost / semilla 1 / 2 | 0.309023400 | 1047 | 1 | completa | Total; eventos.jsonl línea 294 |
| Inferencia | xgboost / semilla 1 / OOF 2 | 0.013340000 | 262 | 1 | completa | Total; eventos.jsonl línea 295 |
| Entrenamiento/refit | xgboost / semilla 1 / 3 | 0.467126100 | 1047 | 1 | completa | Total; eventos.jsonl línea 296 |
| Inferencia | xgboost / semilla 1 / OOF 3 | 0.013461300 | 262 | 1 | completa | Total; eventos.jsonl línea 297 |
| Entrenamiento/refit | xgboost / semilla 1 / 4 | 0.398616700 | 1047 | 1 | completa | Total; eventos.jsonl línea 298 |
| Inferencia | xgboost / semilla 1 / OOF 4 | 0.013268700 | 262 | 1 | completa | Total; eventos.jsonl línea 299 |
| Entrenamiento/refit | xgboost / semilla 1 / 5 | 0.311095900 | 1048 | 1 | completa | Total; eventos.jsonl línea 300 |
| Inferencia | xgboost / semilla 1 / OOF 5 | 0.012186900 | 261 | 1 | completa | Total; eventos.jsonl línea 301 |
| Entrenamiento/refit | xgboost / semilla 1 / final | 0.396899500 | 1309 | 1 | completa | Total; eventos.jsonl línea 302 |
| Inferencia | xgboost / semilla 1 / test final | 0.016655000 | 188 | 1 | completa | Total; eventos.jsonl línea 303 |
| Entrenamiento/refit | xgboost / semilla 2 / 1 | 0.359765900 | 1047 | 1 | completa | Total; eventos.jsonl línea 304 |
| Inferencia | xgboost / semilla 2 / OOF 1 | 0.015283100 | 262 | 1 | completa | Total; eventos.jsonl línea 305 |
| Entrenamiento/refit | xgboost / semilla 2 / 2 | 0.296998500 | 1047 | 1 | completa | Total; eventos.jsonl línea 306 |
| Inferencia | xgboost / semilla 2 / OOF 2 | 0.012388500 | 262 | 1 | completa | Total; eventos.jsonl línea 307 |
| Entrenamiento/refit | xgboost / semilla 2 / 3 | 0.449801600 | 1047 | 1 | completa | Total; eventos.jsonl línea 308 |
| Inferencia | xgboost / semilla 2 / OOF 3 | 0.012852200 | 262 | 1 | completa | Total; eventos.jsonl línea 309 |
| Entrenamiento/refit | xgboost / semilla 2 / 4 | 0.379218800 | 1047 | 1 | completa | Total; eventos.jsonl línea 310 |
| Inferencia | xgboost / semilla 2 / OOF 4 | 0.012544400 | 262 | 1 | completa | Total; eventos.jsonl línea 311 |
| Entrenamiento/refit | xgboost / semilla 2 / 5 | 0.311991300 | 1048 | 1 | completa | Total; eventos.jsonl línea 312 |
| Inferencia | xgboost / semilla 2 / OOF 5 | 0.014280600 | 261 | 1 | completa | Total; eventos.jsonl línea 313 |
| Entrenamiento/refit | xgboost / semilla 2 / final | 0.402477300 | 1309 | 1 | completa | Total; eventos.jsonl línea 314 |
| Inferencia | xgboost / semilla 2 / test final | 0.011240300 | 188 | 1 | completa | Total; eventos.jsonl línea 315 |
| Entrenamiento/refit | xgboost / semilla 3 / 1 | 0.343135800 | 1047 | 1 | completa | Total; eventos.jsonl línea 316 |
| Inferencia | xgboost / semilla 3 / OOF 1 | 0.015447000 | 262 | 1 | completa | Total; eventos.jsonl línea 317 |
| Entrenamiento/refit | xgboost / semilla 3 / 2 | 0.306268000 | 1047 | 1 | completa | Total; eventos.jsonl línea 318 |
| Inferencia | xgboost / semilla 3 / OOF 2 | 0.012112000 | 262 | 1 | completa | Total; eventos.jsonl línea 319 |
| Entrenamiento/refit | xgboost / semilla 3 / 3 | 0.455135700 | 1047 | 1 | completa | Total; eventos.jsonl línea 320 |
| Inferencia | xgboost / semilla 3 / OOF 3 | 0.014388100 | 262 | 1 | completa | Total; eventos.jsonl línea 321 |
| Entrenamiento/refit | xgboost / semilla 3 / 4 | 0.383805100 | 1047 | 1 | completa | Total; eventos.jsonl línea 322 |
| Inferencia | xgboost / semilla 3 / OOF 4 | 0.016691900 | 262 | 1 | completa | Total; eventos.jsonl línea 323 |
| Entrenamiento/refit | xgboost / semilla 3 / 5 | 0.321669600 | 1048 | 1 | completa | Total; eventos.jsonl línea 324 |
| Inferencia | xgboost / semilla 3 / OOF 5 | 0.012192200 | 261 | 1 | completa | Total; eventos.jsonl línea 325 |
| Entrenamiento/refit | xgboost / semilla 3 / final | 0.412966600 | 1309 | 1 | completa | Total; eventos.jsonl línea 326 |
| Inferencia | xgboost / semilla 3 / test final | 0.013122800 | 188 | 1 | completa | Total; eventos.jsonl línea 327 |
| Entrenamiento/refit | xgboost / semilla 4 / 1 | 0.343778600 | 1047 | 1 | completa | Total; eventos.jsonl línea 328 |
| Inferencia | xgboost / semilla 4 / OOF 1 | 0.013520200 | 262 | 1 | completa | Total; eventos.jsonl línea 329 |
| Entrenamiento/refit | xgboost / semilla 4 / 2 | 0.301210400 | 1047 | 1 | completa | Total; eventos.jsonl línea 330 |
| Inferencia | xgboost / semilla 4 / OOF 2 | 0.012646800 | 262 | 1 | completa | Total; eventos.jsonl línea 331 |
| Entrenamiento/refit | xgboost / semilla 4 / 3 | 0.429364800 | 1047 | 1 | completa | Total; eventos.jsonl línea 332 |
| Inferencia | xgboost / semilla 4 / OOF 3 | 0.013149900 | 262 | 1 | completa | Total; eventos.jsonl línea 333 |
| Entrenamiento/refit | xgboost / semilla 4 / 4 | 0.383098500 | 1047 | 1 | completa | Total; eventos.jsonl línea 334 |
| Inferencia | xgboost / semilla 4 / OOF 4 | 0.012534600 | 262 | 1 | completa | Total; eventos.jsonl línea 335 |
| Entrenamiento/refit | xgboost / semilla 4 / 5 | 0.300709200 | 1048 | 1 | completa | Total; eventos.jsonl línea 336 |
| Inferencia | xgboost / semilla 4 / OOF 5 | 0.012485000 | 261 | 1 | completa | Total; eventos.jsonl línea 337 |
| Entrenamiento/refit | xgboost / semilla 4 / final | 0.396832200 | 1309 | 1 | completa | Total; eventos.jsonl línea 338 |
| Inferencia | xgboost / semilla 4 / test final | 0.013514500 | 188 | 1 | completa | Total; eventos.jsonl línea 339 |
| Entrenamiento/refit | xgboost / semilla 5 / 1 | 0.337694000 | 1047 | 1 | completa | Total; eventos.jsonl línea 340 |
| Inferencia | xgboost / semilla 5 / OOF 1 | 0.013387500 | 262 | 1 | completa | Total; eventos.jsonl línea 341 |
| Entrenamiento/refit | xgboost / semilla 5 / 2 | 0.290212100 | 1047 | 1 | completa | Total; eventos.jsonl línea 342 |
| Inferencia | xgboost / semilla 5 / OOF 2 | 0.012929700 | 262 | 1 | completa | Total; eventos.jsonl línea 343 |
| Entrenamiento/refit | xgboost / semilla 5 / 3 | 0.438302600 | 1047 | 1 | completa | Total; eventos.jsonl línea 344 |
| Inferencia | xgboost / semilla 5 / OOF 3 | 0.012095400 | 262 | 1 | completa | Total; eventos.jsonl línea 345 |
| Entrenamiento/refit | xgboost / semilla 5 / 4 | 0.385733700 | 1047 | 1 | completa | Total; eventos.jsonl línea 346 |
| Inferencia | xgboost / semilla 5 / OOF 4 | 0.013995800 | 262 | 1 | completa | Total; eventos.jsonl línea 347 |
| Entrenamiento/refit | xgboost / semilla 5 / 5 | 0.307931900 | 1048 | 1 | completa | Total; eventos.jsonl línea 348 |
| Inferencia | xgboost / semilla 5 / OOF 5 | 0.012867000 | 261 | 1 | completa | Total; eventos.jsonl línea 349 |
| Entrenamiento/refit | xgboost / semilla 5 / final | 0.386843300 | 1309 | 1 | completa | Total; eventos.jsonl línea 350 |
| Inferencia | xgboost / semilla 5 / test final | 0.012268900 | 188 | 1 | completa | Total; eventos.jsonl línea 351 |
| Entrenamiento/refit | xgboost / semilla 6 / 1 | 0.346903700 | 1047 | 1 | completa | Total; eventos.jsonl línea 352 |
| Inferencia | xgboost / semilla 6 / OOF 1 | 0.012132700 | 262 | 1 | completa | Total; eventos.jsonl línea 353 |
| Entrenamiento/refit | xgboost / semilla 6 / 2 | 0.295644400 | 1047 | 1 | completa | Total; eventos.jsonl línea 354 |
| Inferencia | xgboost / semilla 6 / OOF 2 | 0.012604100 | 262 | 1 | completa | Total; eventos.jsonl línea 355 |
| Entrenamiento/refit | xgboost / semilla 6 / 3 | 0.449503800 | 1047 | 1 | completa | Total; eventos.jsonl línea 356 |
| Inferencia | xgboost / semilla 6 / OOF 3 | 0.012890900 | 262 | 1 | completa | Total; eventos.jsonl línea 357 |
| Entrenamiento/refit | xgboost / semilla 6 / 4 | 0.403559500 | 1047 | 1 | completa | Total; eventos.jsonl línea 358 |
| Inferencia | xgboost / semilla 6 / OOF 4 | 0.018941100 | 262 | 1 | completa | Total; eventos.jsonl línea 359 |
| Entrenamiento/refit | xgboost / semilla 6 / 5 | 0.302091800 | 1048 | 1 | completa | Total; eventos.jsonl línea 360 |
| Inferencia | xgboost / semilla 6 / OOF 5 | 0.012863300 | 261 | 1 | completa | Total; eventos.jsonl línea 361 |
| Entrenamiento/refit | xgboost / semilla 6 / final | 0.397646100 | 1309 | 1 | completa | Total; eventos.jsonl línea 362 |
| Inferencia | xgboost / semilla 6 / test final | 0.012763400 | 188 | 1 | completa | Total; eventos.jsonl línea 363 |
| Entrenamiento/refit | xgboost / semilla 7 / 1 | 0.354426600 | 1047 | 1 | completa | Total; eventos.jsonl línea 364 |
| Inferencia | xgboost / semilla 7 / OOF 1 | 0.014794700 | 262 | 1 | completa | Total; eventos.jsonl línea 365 |
| Entrenamiento/refit | xgboost / semilla 7 / 2 | 0.322200600 | 1047 | 1 | completa | Total; eventos.jsonl línea 366 |
| Inferencia | xgboost / semilla 7 / OOF 2 | 0.012567500 | 262 | 1 | completa | Total; eventos.jsonl línea 367 |
| Entrenamiento/refit | xgboost / semilla 7 / 3 | 0.459788800 | 1047 | 1 | completa | Total; eventos.jsonl línea 368 |
| Inferencia | xgboost / semilla 7 / OOF 3 | 0.014566900 | 262 | 1 | completa | Total; eventos.jsonl línea 369 |
| Entrenamiento/refit | xgboost / semilla 7 / 4 | 0.405890100 | 1047 | 1 | completa | Total; eventos.jsonl línea 370 |
| Inferencia | xgboost / semilla 7 / OOF 4 | 0.012570400 | 262 | 1 | completa | Total; eventos.jsonl línea 371 |
| Entrenamiento/refit | xgboost / semilla 7 / 5 | 0.307952900 | 1048 | 1 | completa | Total; eventos.jsonl línea 372 |
| Inferencia | xgboost / semilla 7 / OOF 5 | 0.016471900 | 261 | 1 | completa | Total; eventos.jsonl línea 373 |
| Entrenamiento/refit | xgboost / semilla 7 / final | 0.404414400 | 1309 | 1 | completa | Total; eventos.jsonl línea 374 |
| Inferencia | xgboost / semilla 7 / test final | 0.012716400 | 188 | 1 | completa | Total; eventos.jsonl línea 375 |
| Entrenamiento/refit | xgboost / semilla 8 / 1 | 0.342407800 | 1047 | 1 | completa | Total; eventos.jsonl línea 376 |
| Inferencia | xgboost / semilla 8 / OOF 1 | 0.013311500 | 262 | 1 | completa | Total; eventos.jsonl línea 377 |
| Entrenamiento/refit | xgboost / semilla 8 / 2 | 0.314098500 | 1047 | 1 | completa | Total; eventos.jsonl línea 378 |
| Inferencia | xgboost / semilla 8 / OOF 2 | 0.012962400 | 262 | 1 | completa | Total; eventos.jsonl línea 379 |
| Entrenamiento/refit | xgboost / semilla 8 / 3 | 0.448822100 | 1047 | 1 | completa | Total; eventos.jsonl línea 380 |
| Inferencia | xgboost / semilla 8 / OOF 3 | 0.012141200 | 262 | 1 | completa | Total; eventos.jsonl línea 381 |
| Entrenamiento/refit | xgboost / semilla 8 / 4 | 0.384521000 | 1047 | 1 | completa | Total; eventos.jsonl línea 382 |
| Inferencia | xgboost / semilla 8 / OOF 4 | 0.019019500 | 262 | 1 | completa | Total; eventos.jsonl línea 383 |
| Entrenamiento/refit | xgboost / semilla 8 / 5 | 0.304307100 | 1048 | 1 | completa | Total; eventos.jsonl línea 384 |
| Inferencia | xgboost / semilla 8 / OOF 5 | 0.011571000 | 261 | 1 | completa | Total; eventos.jsonl línea 385 |
| Entrenamiento/refit | xgboost / semilla 8 / final | 0.411007200 | 1309 | 1 | completa | Total; eventos.jsonl línea 386 |
| Inferencia | xgboost / semilla 8 / test final | 0.016112800 | 188 | 1 | completa | Total; eventos.jsonl línea 387 |
| Entrenamiento/refit | xgboost / semilla 9 / 1 | 0.344640900 | 1047 | 1 | completa | Total; eventos.jsonl línea 388 |
| Inferencia | xgboost / semilla 9 / OOF 1 | 0.012674000 | 262 | 1 | completa | Total; eventos.jsonl línea 389 |
| Entrenamiento/refit | xgboost / semilla 9 / 2 | 0.296004600 | 1047 | 1 | completa | Total; eventos.jsonl línea 390 |
| Inferencia | xgboost / semilla 9 / OOF 2 | 0.016807300 | 262 | 1 | completa | Total; eventos.jsonl línea 391 |
| Entrenamiento/refit | xgboost / semilla 9 / 3 | 0.446933300 | 1047 | 1 | completa | Total; eventos.jsonl línea 392 |
| Inferencia | xgboost / semilla 9 / OOF 3 | 0.017005200 | 262 | 1 | completa | Total; eventos.jsonl línea 393 |
| Entrenamiento/refit | xgboost / semilla 9 / 4 | 0.395142000 | 1047 | 1 | completa | Total; eventos.jsonl línea 394 |
| Inferencia | xgboost / semilla 9 / OOF 4 | 0.012875600 | 262 | 1 | completa | Total; eventos.jsonl línea 395 |
| Entrenamiento/refit | xgboost / semilla 9 / 5 | 0.290491400 | 1048 | 1 | completa | Total; eventos.jsonl línea 396 |
| Inferencia | xgboost / semilla 9 / OOF 5 | 0.011394700 | 261 | 1 | completa | Total; eventos.jsonl línea 397 |
| Entrenamiento/refit | xgboost / semilla 9 / final | 0.371736600 | 1309 | 1 | completa | Total; eventos.jsonl línea 398 |
| Inferencia | xgboost / semilla 9 / test final | 0.011124200 | 188 | 1 | completa | Total; eventos.jsonl línea 399 |
| Entrenamiento/refit + inferencia | decision_tree / sensibilidad semilla estimador | 0.493537500 | 1309 | 1 | completa | Total; eventos.jsonl línea 400 |
| Entrenamiento/refit | decision_tree / semilla 42 / 1 | 0.022444100 | 1047 | 1 | completa | Total; eventos.jsonl línea 401 |
| Inferencia | decision_tree / semilla 42 / OOF 1 | 0.005031200 | 262 | 1 | completa | Total; eventos.jsonl línea 402 |
| Entrenamiento/refit | decision_tree / semilla 42 / 2 | 0.021876800 | 1047 | 1 | completa | Total; eventos.jsonl línea 403 |
| Inferencia | decision_tree / semilla 42 / OOF 2 | 0.005072800 | 262 | 1 | completa | Total; eventos.jsonl línea 404 |
| Entrenamiento/refit | decision_tree / semilla 42 / 3 | 0.020302400 | 1047 | 1 | completa | Total; eventos.jsonl línea 405 |
| Inferencia | decision_tree / semilla 42 / OOF 3 | 0.004599200 | 262 | 1 | completa | Total; eventos.jsonl línea 406 |
| Entrenamiento/refit | decision_tree / semilla 42 / 4 | 0.019182600 | 1047 | 1 | completa | Total; eventos.jsonl línea 407 |
| Inferencia | decision_tree / semilla 42 / OOF 4 | 0.004540100 | 262 | 1 | completa | Total; eventos.jsonl línea 408 |
| Entrenamiento/refit | decision_tree / semilla 42 / 5 | 0.013680400 | 1048 | 1 | completa | Total; eventos.jsonl línea 409 |
| Inferencia | decision_tree / semilla 42 / OOF 5 | 0.005552000 | 261 | 1 | completa | Total; eventos.jsonl línea 410 |
| Entrenamiento/refit | decision_tree / semilla 42 / final | 0.016578400 | 1309 | 1 | completa | Total; eventos.jsonl línea 411 |
| Inferencia | decision_tree / semilla 42 / test final | 0.006002100 | 188 | 1 | completa | Total; eventos.jsonl línea 412 |
| Entrenamiento/refit | decision_tree / semilla 0 / 1 | 0.012970300 | 1047 | 1 | completa | Total; eventos.jsonl línea 413 |
| Inferencia | decision_tree / semilla 0 / OOF 1 | 0.003959700 | 262 | 1 | completa | Total; eventos.jsonl línea 414 |
| Entrenamiento/refit | decision_tree / semilla 0 / 2 | 0.013897500 | 1047 | 1 | completa | Total; eventos.jsonl línea 415 |
| Inferencia | decision_tree / semilla 0 / OOF 2 | 0.004182700 | 262 | 1 | completa | Total; eventos.jsonl línea 416 |
| Entrenamiento/refit | decision_tree / semilla 0 / 3 | 0.012238200 | 1047 | 1 | completa | Total; eventos.jsonl línea 417 |
| Inferencia | decision_tree / semilla 0 / OOF 3 | 0.005972300 | 262 | 1 | completa | Total; eventos.jsonl línea 418 |
| Entrenamiento/refit | decision_tree / semilla 0 / 4 | 0.013403500 | 1047 | 1 | completa | Total; eventos.jsonl línea 419 |
| Inferencia | decision_tree / semilla 0 / OOF 4 | 0.003994300 | 262 | 1 | completa | Total; eventos.jsonl línea 420 |
| Entrenamiento/refit | decision_tree / semilla 0 / 5 | 0.014470100 | 1048 | 1 | completa | Total; eventos.jsonl línea 421 |
| Inferencia | decision_tree / semilla 0 / OOF 5 | 0.004152900 | 261 | 1 | completa | Total; eventos.jsonl línea 422 |
| Entrenamiento/refit | decision_tree / semilla 0 / final | 0.016232800 | 1309 | 1 | completa | Total; eventos.jsonl línea 423 |
| Inferencia | decision_tree / semilla 0 / test final | 0.005012000 | 188 | 1 | completa | Total; eventos.jsonl línea 424 |
| Entrenamiento/refit | decision_tree / semilla 1 / 1 | 0.013449700 | 1047 | 1 | completa | Total; eventos.jsonl línea 425 |
| Inferencia | decision_tree / semilla 1 / OOF 1 | 0.004872400 | 262 | 1 | completa | Total; eventos.jsonl línea 426 |
| Entrenamiento/refit | decision_tree / semilla 1 / 2 | 0.014723900 | 1047 | 1 | completa | Total; eventos.jsonl línea 427 |
| Inferencia | decision_tree / semilla 1 / OOF 2 | 0.005112800 | 262 | 1 | completa | Total; eventos.jsonl línea 428 |
| Entrenamiento/refit | decision_tree / semilla 1 / 3 | 0.014271000 | 1047 | 1 | completa | Total; eventos.jsonl línea 429 |
| Inferencia | decision_tree / semilla 1 / OOF 3 | 0.003930400 | 262 | 1 | completa | Total; eventos.jsonl línea 430 |
| Entrenamiento/refit | decision_tree / semilla 1 / 4 | 0.011993000 | 1047 | 1 | completa | Total; eventos.jsonl línea 431 |
| Inferencia | decision_tree / semilla 1 / OOF 4 | 0.004306400 | 262 | 1 | completa | Total; eventos.jsonl línea 432 |
| Entrenamiento/refit | decision_tree / semilla 1 / 5 | 0.013308600 | 1048 | 1 | completa | Total; eventos.jsonl línea 433 |
| Inferencia | decision_tree / semilla 1 / OOF 5 | 0.004296100 | 261 | 1 | completa | Total; eventos.jsonl línea 434 |
| Entrenamiento/refit | decision_tree / semilla 1 / final | 0.014185100 | 1309 | 1 | completa | Total; eventos.jsonl línea 435 |
| Inferencia | decision_tree / semilla 1 / test final | 0.005125900 | 188 | 1 | completa | Total; eventos.jsonl línea 436 |
| Entrenamiento/refit | decision_tree / semilla 2 / 1 | 0.012606800 | 1047 | 1 | completa | Total; eventos.jsonl línea 437 |
| Inferencia | decision_tree / semilla 2 / OOF 1 | 0.005675000 | 262 | 1 | completa | Total; eventos.jsonl línea 438 |
| Entrenamiento/refit | decision_tree / semilla 2 / 2 | 0.012559600 | 1047 | 1 | completa | Total; eventos.jsonl línea 439 |
| Inferencia | decision_tree / semilla 2 / OOF 2 | 0.005984500 | 262 | 1 | completa | Total; eventos.jsonl línea 440 |
| Entrenamiento/refit | decision_tree / semilla 2 / 3 | 0.012299600 | 1047 | 1 | completa | Total; eventos.jsonl línea 441 |
| Inferencia | decision_tree / semilla 2 / OOF 3 | 0.005769700 | 262 | 1 | completa | Total; eventos.jsonl línea 442 |
| Entrenamiento/refit | decision_tree / semilla 2 / 4 | 0.015319000 | 1047 | 1 | completa | Total; eventos.jsonl línea 443 |
| Inferencia | decision_tree / semilla 2 / OOF 4 | 0.004478900 | 262 | 1 | completa | Total; eventos.jsonl línea 444 |
| Entrenamiento/refit | decision_tree / semilla 2 / 5 | 0.012367200 | 1048 | 1 | completa | Total; eventos.jsonl línea 445 |
| Inferencia | decision_tree / semilla 2 / OOF 5 | 0.003946100 | 261 | 1 | completa | Total; eventos.jsonl línea 446 |
| Entrenamiento/refit | decision_tree / semilla 2 / final | 0.019915200 | 1309 | 1 | completa | Total; eventos.jsonl línea 447 |
| Inferencia | decision_tree / semilla 2 / test final | 0.005169400 | 188 | 1 | completa | Total; eventos.jsonl línea 448 |
| Entrenamiento/refit | decision_tree / semilla 3 / 1 | 0.013714200 | 1047 | 1 | completa | Total; eventos.jsonl línea 449 |
| Inferencia | decision_tree / semilla 3 / OOF 1 | 0.004054700 | 262 | 1 | completa | Total; eventos.jsonl línea 450 |
| Entrenamiento/refit | decision_tree / semilla 3 / 2 | 0.013186100 | 1047 | 1 | completa | Total; eventos.jsonl línea 451 |
| Inferencia | decision_tree / semilla 3 / OOF 2 | 0.004579000 | 262 | 1 | completa | Total; eventos.jsonl línea 452 |
| Entrenamiento/refit | decision_tree / semilla 3 / 3 | 0.013729300 | 1047 | 1 | completa | Total; eventos.jsonl línea 453 |
| Inferencia | decision_tree / semilla 3 / OOF 3 | 0.005037900 | 262 | 1 | completa | Total; eventos.jsonl línea 454 |
| Entrenamiento/refit | decision_tree / semilla 3 / 4 | 0.013684800 | 1047 | 1 | completa | Total; eventos.jsonl línea 455 |
| Inferencia | decision_tree / semilla 3 / OOF 4 | 0.005982500 | 262 | 1 | completa | Total; eventos.jsonl línea 456 |
| Entrenamiento/refit | decision_tree / semilla 3 / 5 | 0.014710100 | 1048 | 1 | completa | Total; eventos.jsonl línea 457 |
| Inferencia | decision_tree / semilla 3 / OOF 5 | 0.005709700 | 261 | 1 | completa | Total; eventos.jsonl línea 458 |
| Entrenamiento/refit | decision_tree / semilla 3 / final | 0.014855900 | 1309 | 1 | completa | Total; eventos.jsonl línea 459 |
| Inferencia | decision_tree / semilla 3 / test final | 0.004329000 | 188 | 1 | completa | Total; eventos.jsonl línea 460 |
| Entrenamiento/refit | decision_tree / semilla 4 / 1 | 0.012700100 | 1047 | 1 | completa | Total; eventos.jsonl línea 461 |
| Inferencia | decision_tree / semilla 4 / OOF 1 | 0.006022300 | 262 | 1 | completa | Total; eventos.jsonl línea 462 |
| Entrenamiento/refit | decision_tree / semilla 4 / 2 | 0.017309400 | 1047 | 1 | completa | Total; eventos.jsonl línea 463 |
| Inferencia | decision_tree / semilla 4 / OOF 2 | 0.004541400 | 262 | 1 | completa | Total; eventos.jsonl línea 464 |
| Entrenamiento/refit | decision_tree / semilla 4 / 3 | 0.012461400 | 1047 | 1 | completa | Total; eventos.jsonl línea 465 |
| Inferencia | decision_tree / semilla 4 / OOF 3 | 0.005025300 | 262 | 1 | completa | Total; eventos.jsonl línea 466 |
| Entrenamiento/refit | decision_tree / semilla 4 / 4 | 0.015393900 | 1047 | 1 | completa | Total; eventos.jsonl línea 467 |
| Inferencia | decision_tree / semilla 4 / OOF 4 | 0.005832700 | 262 | 1 | completa | Total; eventos.jsonl línea 468 |
| Entrenamiento/refit | decision_tree / semilla 4 / 5 | 0.013783000 | 1048 | 1 | completa | Total; eventos.jsonl línea 469 |
| Inferencia | decision_tree / semilla 4 / OOF 5 | 0.005852800 | 261 | 1 | completa | Total; eventos.jsonl línea 470 |
| Entrenamiento/refit | decision_tree / semilla 4 / final | 0.013650800 | 1309 | 1 | completa | Total; eventos.jsonl línea 471 |
| Inferencia | decision_tree / semilla 4 / test final | 0.004227300 | 188 | 1 | completa | Total; eventos.jsonl línea 472 |
| Entrenamiento/refit | decision_tree / semilla 5 / 1 | 0.013221500 | 1047 | 1 | completa | Total; eventos.jsonl línea 473 |
| Inferencia | decision_tree / semilla 5 / OOF 1 | 0.004007500 | 262 | 1 | completa | Total; eventos.jsonl línea 474 |
| Entrenamiento/refit | decision_tree / semilla 5 / 2 | 0.017017000 | 1047 | 1 | completa | Total; eventos.jsonl línea 475 |
| Inferencia | decision_tree / semilla 5 / OOF 2 | 0.004418400 | 262 | 1 | completa | Total; eventos.jsonl línea 476 |
| Entrenamiento/refit | decision_tree / semilla 5 / 3 | 0.012055400 | 1047 | 1 | completa | Total; eventos.jsonl línea 477 |
| Inferencia | decision_tree / semilla 5 / OOF 3 | 0.006063800 | 262 | 1 | completa | Total; eventos.jsonl línea 478 |
| Entrenamiento/refit | decision_tree / semilla 5 / 4 | 0.014418300 | 1047 | 1 | completa | Total; eventos.jsonl línea 479 |
| Inferencia | decision_tree / semilla 5 / OOF 4 | 0.005874000 | 262 | 1 | completa | Total; eventos.jsonl línea 480 |
| Entrenamiento/refit | decision_tree / semilla 5 / 5 | 0.012808300 | 1048 | 1 | completa | Total; eventos.jsonl línea 481 |
| Inferencia | decision_tree / semilla 5 / OOF 5 | 0.005003500 | 261 | 1 | completa | Total; eventos.jsonl línea 482 |
| Entrenamiento/refit | decision_tree / semilla 5 / final | 0.016080100 | 1309 | 1 | completa | Total; eventos.jsonl línea 483 |
| Inferencia | decision_tree / semilla 5 / test final | 0.004968400 | 188 | 1 | completa | Total; eventos.jsonl línea 484 |
| Entrenamiento/refit | decision_tree / semilla 6 / 1 | 0.016251000 | 1047 | 1 | completa | Total; eventos.jsonl línea 485 |
| Inferencia | decision_tree / semilla 6 / OOF 1 | 0.004112100 | 262 | 1 | completa | Total; eventos.jsonl línea 486 |
| Entrenamiento/refit | decision_tree / semilla 6 / 2 | 0.014244900 | 1047 | 1 | completa | Total; eventos.jsonl línea 487 |
| Inferencia | decision_tree / semilla 6 / OOF 2 | 0.004287300 | 262 | 1 | completa | Total; eventos.jsonl línea 488 |
| Entrenamiento/refit | decision_tree / semilla 6 / 3 | 0.016382300 | 1047 | 1 | completa | Total; eventos.jsonl línea 489 |
| Inferencia | decision_tree / semilla 6 / OOF 3 | 0.004761800 | 262 | 1 | completa | Total; eventos.jsonl línea 490 |
| Entrenamiento/refit | decision_tree / semilla 6 / 4 | 0.012611000 | 1047 | 1 | completa | Total; eventos.jsonl línea 491 |
| Inferencia | decision_tree / semilla 6 / OOF 4 | 0.004107100 | 262 | 1 | completa | Total; eventos.jsonl línea 492 |
| Entrenamiento/refit | decision_tree / semilla 6 / 5 | 0.012019400 | 1048 | 1 | completa | Total; eventos.jsonl línea 493 |
| Inferencia | decision_tree / semilla 6 / OOF 5 | 0.005027700 | 261 | 1 | completa | Total; eventos.jsonl línea 494 |
| Entrenamiento/refit | decision_tree / semilla 6 / final | 0.016749000 | 1309 | 1 | completa | Total; eventos.jsonl línea 495 |
| Inferencia | decision_tree / semilla 6 / test final | 0.004254000 | 188 | 1 | completa | Total; eventos.jsonl línea 496 |
| Entrenamiento/refit | decision_tree / semilla 7 / 1 | 0.014085200 | 1047 | 1 | completa | Total; eventos.jsonl línea 497 |
| Inferencia | decision_tree / semilla 7 / OOF 1 | 0.004474800 | 262 | 1 | completa | Total; eventos.jsonl línea 498 |
| Entrenamiento/refit | decision_tree / semilla 7 / 2 | 0.012353500 | 1047 | 1 | completa | Total; eventos.jsonl línea 499 |
| Inferencia | decision_tree / semilla 7 / OOF 2 | 0.004291500 | 262 | 1 | completa | Total; eventos.jsonl línea 500 |
| Entrenamiento/refit | decision_tree / semilla 7 / 3 | 0.012397100 | 1047 | 1 | completa | Total; eventos.jsonl línea 501 |
| Inferencia | decision_tree / semilla 7 / OOF 3 | 0.003954000 | 262 | 1 | completa | Total; eventos.jsonl línea 502 |
| Entrenamiento/refit | decision_tree / semilla 7 / 4 | 0.012220000 | 1047 | 1 | completa | Total; eventos.jsonl línea 503 |
| Inferencia | decision_tree / semilla 7 / OOF 4 | 0.004219700 | 262 | 1 | completa | Total; eventos.jsonl línea 504 |
| Entrenamiento/refit | decision_tree / semilla 7 / 5 | 0.013878700 | 1048 | 1 | completa | Total; eventos.jsonl línea 505 |
| Inferencia | decision_tree / semilla 7 / OOF 5 | 0.004121300 | 261 | 1 | completa | Total; eventos.jsonl línea 506 |
| Entrenamiento/refit | decision_tree / semilla 7 / final | 0.013721400 | 1309 | 1 | completa | Total; eventos.jsonl línea 507 |
| Inferencia | decision_tree / semilla 7 / test final | 0.004356900 | 188 | 1 | completa | Total; eventos.jsonl línea 508 |
| Entrenamiento/refit | decision_tree / semilla 8 / 1 | 0.013030700 | 1047 | 1 | completa | Total; eventos.jsonl línea 509 |
| Inferencia | decision_tree / semilla 8 / OOF 1 | 0.004097800 | 262 | 1 | completa | Total; eventos.jsonl línea 510 |
| Entrenamiento/refit | decision_tree / semilla 8 / 2 | 0.012537500 | 1047 | 1 | completa | Total; eventos.jsonl línea 511 |
| Inferencia | decision_tree / semilla 8 / OOF 2 | 0.004214900 | 262 | 1 | completa | Total; eventos.jsonl línea 512 |
| Entrenamiento/refit | decision_tree / semilla 8 / 3 | 0.011970900 | 1047 | 1 | completa | Total; eventos.jsonl línea 513 |
| Inferencia | decision_tree / semilla 8 / OOF 3 | 0.004490800 | 262 | 1 | completa | Total; eventos.jsonl línea 514 |
| Entrenamiento/refit | decision_tree / semilla 8 / 4 | 0.012094800 | 1047 | 1 | completa | Total; eventos.jsonl línea 515 |
| Inferencia | decision_tree / semilla 8 / OOF 4 | 0.005051800 | 262 | 1 | completa | Total; eventos.jsonl línea 516 |
| Entrenamiento/refit | decision_tree / semilla 8 / 5 | 0.015119100 | 1048 | 1 | completa | Total; eventos.jsonl línea 517 |
| Inferencia | decision_tree / semilla 8 / OOF 5 | 0.004728800 | 261 | 1 | completa | Total; eventos.jsonl línea 518 |
| Entrenamiento/refit | decision_tree / semilla 8 / final | 0.016907300 | 1309 | 1 | completa | Total; eventos.jsonl línea 519 |
| Inferencia | decision_tree / semilla 8 / test final | 0.005290600 | 188 | 1 | completa | Total; eventos.jsonl línea 520 |
| Entrenamiento/refit | decision_tree / semilla 9 / 1 | 0.013228500 | 1047 | 1 | completa | Total; eventos.jsonl línea 521 |
| Inferencia | decision_tree / semilla 9 / OOF 1 | 0.004186600 | 262 | 1 | completa | Total; eventos.jsonl línea 522 |
| Entrenamiento/refit | decision_tree / semilla 9 / 2 | 0.013628000 | 1047 | 1 | completa | Total; eventos.jsonl línea 523 |
| Inferencia | decision_tree / semilla 9 / OOF 2 | 0.004126700 | 262 | 1 | completa | Total; eventos.jsonl línea 524 |
| Entrenamiento/refit | decision_tree / semilla 9 / 3 | 0.013141200 | 1047 | 1 | completa | Total; eventos.jsonl línea 525 |
| Inferencia | decision_tree / semilla 9 / OOF 3 | 0.004208000 | 262 | 1 | completa | Total; eventos.jsonl línea 526 |
| Entrenamiento/refit | decision_tree / semilla 9 / 4 | 0.014171400 | 1047 | 1 | completa | Total; eventos.jsonl línea 527 |
| Inferencia | decision_tree / semilla 9 / OOF 4 | 0.004187200 | 262 | 1 | completa | Total; eventos.jsonl línea 528 |
| Entrenamiento/refit | decision_tree / semilla 9 / 5 | 0.015341800 | 1048 | 1 | completa | Total; eventos.jsonl línea 529 |
| Inferencia | decision_tree / semilla 9 / OOF 5 | 0.006522100 | 261 | 1 | completa | Total; eventos.jsonl línea 530 |
| Entrenamiento/refit | decision_tree / semilla 9 / final | 0.018749100 | 1309 | 1 | completa | Total; eventos.jsonl línea 531 |
| Inferencia | decision_tree / semilla 9 / test final | 0.005664300 | 188 | 1 | completa | Total; eventos.jsonl línea 532 |
| Búsqueda | svm / final_train_semilla_1 / Random Search | 1.473471100 | 1309 | 1 | completa | Total; eventos.jsonl línea 533 |
| Búsqueda | svm / final_train_semilla_1 / Bayesiana TPE | 1.908888500 | 1309 | 1 | completa | Total; eventos.jsonl línea 534 |
| Búsqueda | svm / final_train_semilla_1 / Genética DEAP | 1.451563300 | 1309 | 1 | completa | Total; eventos.jsonl línea 535 |
| Búsqueda | svm / final_train_semilla_1 / Successive Halving | 2.054632000 | 1309 | 1 | completa | Total; eventos.jsonl línea 536 |
| Búsqueda | svm / final_train_semilla_2 / Random Search | 1.465523700 | 1309 | 1 | completa | Total; eventos.jsonl línea 537 |
| Búsqueda | svm / final_train_semilla_2 / Bayesiana TPE | 2.027506800 | 1309 | 1 | completa | Total; eventos.jsonl línea 538 |
| Búsqueda | svm / final_train_semilla_2 / Genética DEAP | 1.433312300 | 1309 | 1 | completa | Total; eventos.jsonl línea 539 |
| Búsqueda | svm / final_train_semilla_2 / Successive Halving | 2.020053400 | 1309 | 1 | completa | Total; eventos.jsonl línea 540 |
| Búsqueda | svm / final_train_semilla_3 / Random Search | 1.436231600 | 1309 | 1 | completa | Total; eventos.jsonl línea 541 |
| Búsqueda | svm / final_train_semilla_3 / Bayesiana TPE | 1.764157100 | 1309 | 1 | completa | Total; eventos.jsonl línea 542 |
| Búsqueda | svm / final_train_semilla_3 / Genética DEAP | 1.655205100 | 1309 | 1 | completa | Total; eventos.jsonl línea 543 |
| Búsqueda | svm / final_train_semilla_3 / Successive Halving | 2.047412400 | 1309 | 1 | completa | Total; eventos.jsonl línea 544 |
| Búsqueda | knn / final_train_semilla_1 / Random Search | 1.367956800 | 1309 | 1 | completa | Total; eventos.jsonl línea 545 |
| Búsqueda | knn / final_train_semilla_1 / Bayesiana TPE | 1.674589500 | 1309 | 1 | completa | Total; eventos.jsonl línea 546 |
| Búsqueda | knn / final_train_semilla_1 / Genética DEAP | 1.376661900 | 1309 | 1 | completa | Total; eventos.jsonl línea 547 |
| Búsqueda | knn / final_train_semilla_1 / Successive Halving | 2.002186200 | 1309 | 1 | completa | Total; eventos.jsonl línea 548 |
| Búsqueda | knn / final_train_semilla_2 / Random Search | 1.433947500 | 1309 | 1 | completa | Total; eventos.jsonl línea 549 |
| Búsqueda | knn / final_train_semilla_2 / Bayesiana TPE | 1.784517400 | 1309 | 1 | completa | Total; eventos.jsonl línea 550 |
| Búsqueda | knn / final_train_semilla_2 / Genética DEAP | 1.385123000 | 1309 | 1 | completa | Total; eventos.jsonl línea 551 |
| Búsqueda | knn / final_train_semilla_2 / Successive Halving | 2.154465500 | 1309 | 1 | completa | Total; eventos.jsonl línea 552 |
| Búsqueda | knn / final_train_semilla_3 / Random Search | 1.382717100 | 1309 | 1 | completa | Total; eventos.jsonl línea 553 |
| Búsqueda | knn / final_train_semilla_3 / Bayesiana TPE | 1.622938100 | 1309 | 1 | completa | Total; eventos.jsonl línea 554 |
| Búsqueda | knn / final_train_semilla_3 / Genética DEAP | 1.065624700 | 1309 | 1 | completa | Total; eventos.jsonl línea 555 |
| Búsqueda | knn / final_train_semilla_3 / Successive Halving | 2.045555000 | 1309 | 1 | completa | Total; eventos.jsonl línea 556 |
| Búsqueda | ridge / final_train_semilla_1 / Random Search | 1.200172600 | 1309 | 1 | completa | Total; eventos.jsonl línea 557 |
| Búsqueda | ridge / final_train_semilla_1 / Bayesiana TPE | 1.479199800 | 1309 | 1 | completa | Total; eventos.jsonl línea 558 |
| Búsqueda | ridge / final_train_semilla_1 / Genética DEAP | 1.061944800 | 1309 | 1 | completa | Total; eventos.jsonl línea 559 |
| Búsqueda | ridge / final_train_semilla_1 / Successive Halving | 2.078955100 | 1309 | 1 | completa | Total; eventos.jsonl línea 560 |
| Búsqueda | ridge / final_train_semilla_2 / Random Search | 1.126838100 | 1309 | 1 | completa | Total; eventos.jsonl línea 561 |
| Búsqueda | ridge / final_train_semilla_2 / Bayesiana TPE | 1.413410200 | 1309 | 1 | completa | Total; eventos.jsonl línea 562 |
| Búsqueda | ridge / final_train_semilla_2 / Genética DEAP | 0.928569400 | 1309 | 1 | completa | Total; eventos.jsonl línea 563 |
| Búsqueda | ridge / final_train_semilla_2 / Successive Halving | 1.894566300 | 1309 | 1 | completa | Total; eventos.jsonl línea 564 |
| Búsqueda | ridge / final_train_semilla_3 / Random Search | 1.203406300 | 1309 | 1 | completa | Total; eventos.jsonl línea 565 |
| Búsqueda | ridge / final_train_semilla_3 / Bayesiana TPE | 1.454506500 | 1309 | 1 | completa | Total; eventos.jsonl línea 566 |
| Búsqueda | ridge / final_train_semilla_3 / Genética DEAP | 0.884372500 | 1309 | 1 | completa | Total; eventos.jsonl línea 567 |
| Búsqueda | ridge / final_train_semilla_3 / Successive Halving | 1.869660400 | 1309 | 1 | completa | Total; eventos.jsonl línea 568 |
| Búsqueda | lasso / final_train_semilla_1 / Random Search | 1.376465300 | 1309 | 1 | completa | Total; eventos.jsonl línea 569 |
| Búsqueda | lasso / final_train_semilla_1 / Bayesiana TPE | 2.002045200 | 1309 | 1 | completa | Total; eventos.jsonl línea 570 |
| Búsqueda | lasso / final_train_semilla_1 / Genética DEAP | 1.267310900 | 1309 | 1 | completa | Total; eventos.jsonl línea 571 |
| Búsqueda | lasso / final_train_semilla_1 / Successive Halving | 1.948197200 | 1309 | 1 | completa | Total; eventos.jsonl línea 572 |
| Búsqueda | lasso / final_train_semilla_2 / Random Search | 1.466141900 | 1309 | 1 | completa | Total; eventos.jsonl línea 573 |
| Búsqueda | lasso / final_train_semilla_2 / Bayesiana TPE | 2.096281100 | 1309 | 1 | completa | Total; eventos.jsonl línea 574 |
| Búsqueda | lasso / final_train_semilla_2 / Genética DEAP | 1.057411500 | 1309 | 1 | completa | Total; eventos.jsonl línea 575 |
| Búsqueda | lasso / final_train_semilla_2 / Successive Halving | 1.912018700 | 1309 | 1 | completa | Total; eventos.jsonl línea 576 |
| Búsqueda | lasso / final_train_semilla_3 / Random Search | 1.396321500 | 1309 | 1 | completa | Total; eventos.jsonl línea 577 |
| Búsqueda | lasso / final_train_semilla_3 / Bayesiana TPE | 1.894983400 | 1309 | 1 | completa | Total; eventos.jsonl línea 578 |
| Búsqueda | lasso / final_train_semilla_3 / Genética DEAP | 1.116013600 | 1309 | 1 | completa | Total; eventos.jsonl línea 579 |
| Búsqueda | lasso / final_train_semilla_3 / Successive Halving | 1.993762700 | 1309 | 1 | completa | Total; eventos.jsonl línea 580 |
| Búsqueda | forest / final_train_semilla_1 / Random Search | 19.570548300 | 1309 | 1 | completa | Total; eventos.jsonl línea 581 |
| Búsqueda | forest / final_train_semilla_1 / Bayesiana TPE | 31.426005300 | 1309 | 1 | completa | Total; eventos.jsonl línea 582 |
| Búsqueda | forest / final_train_semilla_1 / Genética DEAP | 15.881643800 | 1309 | 1 | completa | Total; eventos.jsonl línea 583 |
| Búsqueda | forest / final_train_semilla_1 / Successive Halving | 22.693788700 | 1309 | 1 | completa | Total; eventos.jsonl línea 584 |
| Búsqueda | forest / final_train_semilla_2 / Random Search | 19.991714600 | 1309 | 1 | completa | Total; eventos.jsonl línea 585 |
| Búsqueda | forest / final_train_semilla_2 / Bayesiana TPE | 27.050742200 | 1309 | 1 | completa | Total; eventos.jsonl línea 586 |
| Búsqueda | forest / final_train_semilla_2 / Genética DEAP | 25.981316800 | 1309 | 1 | completa | Total; eventos.jsonl línea 587 |
| Búsqueda | forest / final_train_semilla_2 / Successive Halving | 25.137294100 | 1309 | 1 | completa | Total; eventos.jsonl línea 588 |
| Búsqueda | forest / final_train_semilla_3 / Random Search | 22.918205400 | 1309 | 1 | completa | Total; eventos.jsonl línea 589 |
| Búsqueda | forest / final_train_semilla_3 / Bayesiana TPE | 30.855161300 | 1309 | 1 | completa | Total; eventos.jsonl línea 590 |
| Búsqueda | forest / final_train_semilla_3 / Genética DEAP | 19.448211000 | 1309 | 1 | completa | Total; eventos.jsonl línea 591 |
| Búsqueda | forest / final_train_semilla_3 / Successive Halving | 27.136703100 | 1309 | 1 | completa | Total; eventos.jsonl línea 592 |
| Búsqueda | xgboost / final_train_semilla_1 / Random Search | 12.019945200 | 1309 | 1 | completa | Total; eventos.jsonl línea 593 |
| Búsqueda | xgboost / final_train_semilla_1 / Bayesiana TPE | 16.249603100 | 1309 | 1 | completa | Total; eventos.jsonl línea 594 |
| Búsqueda | xgboost / final_train_semilla_1 / Genética DEAP | 10.001038600 | 1309 | 1 | completa | Total; eventos.jsonl línea 595 |
| Búsqueda | xgboost / final_train_semilla_1 / Successive Halving | 17.824121200 | 1309 | 1 | completa | Total; eventos.jsonl línea 596 |
| Búsqueda | xgboost / final_train_semilla_2 / Random Search | 13.641796600 | 1309 | 1 | completa | Total; eventos.jsonl línea 597 |
| Búsqueda | xgboost / final_train_semilla_2 / Bayesiana TPE | 15.365810300 | 1309 | 1 | completa | Total; eventos.jsonl línea 598 |
| Búsqueda | xgboost / final_train_semilla_2 / Genética DEAP | 15.420369600 | 1309 | 1 | completa | Total; eventos.jsonl línea 599 |
| Búsqueda | xgboost / final_train_semilla_2 / Successive Halving | 19.308113300 | 1309 | 1 | completa | Total; eventos.jsonl línea 600 |
| Búsqueda | xgboost / final_train_semilla_3 / Random Search | 12.800012900 | 1309 | 1 | completa | Total; eventos.jsonl línea 601 |
| Búsqueda | xgboost / final_train_semilla_3 / Bayesiana TPE | 16.846668200 | 1309 | 1 | completa | Total; eventos.jsonl línea 602 |
| Búsqueda | xgboost / final_train_semilla_3 / Genética DEAP | 9.889211700 | 1309 | 1 | completa | Total; eventos.jsonl línea 603 |
| Búsqueda | xgboost / final_train_semilla_3 / Successive Halving | 18.954694800 | 1309 | 1 | completa | Total; eventos.jsonl línea 604 |
| Búsqueda | decision_tree / final_train_semilla_1 / Random Search | 1.029471700 | 1309 | 1 | completa | Total; eventos.jsonl línea 605 |
| Búsqueda | decision_tree / final_train_semilla_1 / Bayesiana TPE | 1.363163800 | 1309 | 1 | completa | Total; eventos.jsonl línea 606 |
| Búsqueda | decision_tree / final_train_semilla_1 / Genética DEAP | 1.000784400 | 1309 | 1 | completa | Total; eventos.jsonl línea 607 |
| Búsqueda | decision_tree / final_train_semilla_1 / Successive Halving | 1.617653100 | 1309 | 1 | completa | Total; eventos.jsonl línea 608 |
| Búsqueda | decision_tree / final_train_semilla_2 / Random Search | 1.011497600 | 1309 | 1 | completa | Total; eventos.jsonl línea 609 |
| Búsqueda | decision_tree / final_train_semilla_2 / Bayesiana TPE | 1.351169800 | 1309 | 1 | completa | Total; eventos.jsonl línea 610 |
| Búsqueda | decision_tree / final_train_semilla_2 / Genética DEAP | 1.435232700 | 1309 | 1 | completa | Total; eventos.jsonl línea 611 |
| Búsqueda | decision_tree / final_train_semilla_2 / Successive Halving | 1.602278800 | 1309 | 1 | completa | Total; eventos.jsonl línea 612 |
| Búsqueda | decision_tree / final_train_semilla_3 / Random Search | 1.039870100 | 1309 | 1 | completa | Total; eventos.jsonl línea 613 |
| Búsqueda | decision_tree / final_train_semilla_3 / Bayesiana TPE | 1.332254200 | 1309 | 1 | completa | Total; eventos.jsonl línea 614 |
| Búsqueda | decision_tree / final_train_semilla_3 / Genética DEAP | 0.860544600 | 1309 | 1 | completa | Total; eventos.jsonl línea 615 |
| Búsqueda | decision_tree / final_train_semilla_3 / Successive Halving | 1.603349100 | 1309 | 1 | completa | Total; eventos.jsonl línea 616 |
| Total del experimento | Book · sensibilidad a semillas de clásicos y búsquedas | 586.510480100 | No aplica | 1 | completa | Total; eventos.jsonl línea 617 |

### Ejecución `20261018_192945_d0b41ede`

- **Modelo/motivo:** Book · evaluación, diagnósticos y SHAP de clásicos.
- **Fecha/zona:** 2026-10-18T19:29:45.558767-05:00 a 2026-10-18T19:31:26.294033-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261018_192945_d0b41ede/metadata.json](tiempos/20261018_192945_d0b41ede/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261018_192945_d0b41ede/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | svm / train completo in-sample | 0.007940300 | 1309 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | svm / test verificación | 0.005078600 | 188 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | knn / train completo in-sample | 0.026789900 | 1309 | 1 | completa | Total; eventos.jsonl línea 3 |
| Inferencia | knn / test verificación | 0.008130400 | 188 | 1 | completa | Total; eventos.jsonl línea 4 |
| Inferencia | ridge / train completo in-sample | 0.008208500 | 1309 | 1 | completa | Total; eventos.jsonl línea 5 |
| Inferencia | ridge / test verificación | 0.005481000 | 188 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | lasso / train completo in-sample | 0.007368300 | 1309 | 1 | completa | Total; eventos.jsonl línea 7 |
| Inferencia | lasso / test verificación | 0.005768500 | 188 | 1 | completa | Total; eventos.jsonl línea 8 |
| Inferencia | forest / train completo in-sample | 0.054246600 | 1309 | 1 | completa | Total; eventos.jsonl línea 9 |
| Inferencia | forest / test verificación | 0.032391200 | 188 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | xgboost / train completo in-sample | 0.018377000 | 1309 | 1 | completa | Total; eventos.jsonl línea 11 |
| Inferencia | xgboost / test verificación | 0.012160700 | 188 | 1 | completa | Total; eventos.jsonl línea 12 |
| Inferencia | decision_tree / train completo in-sample | 0.005584400 | 1309 | 1 | completa | Total; eventos.jsonl línea 13 |
| Inferencia | decision_tree / test verificación | 0.003918300 | 188 | 1 | completa | Total; eventos.jsonl línea 14 |
| Explicación SHAP | svm / test temporal | 0.010817600 | 188 | 1 | completa | Total; eventos.jsonl línea 15 |
| Explicación SHAP | knn / test temporal | 31.855950800 | 188 | 1 | completa | Total; eventos.jsonl línea 16 |
| Explicación SHAP | ridge / test temporal | 0.011572600 | 188 | 1 | completa | Total; eventos.jsonl línea 17 |
| Explicación SHAP | lasso / test temporal | 0.011232900 | 188 | 1 | completa | Total; eventos.jsonl línea 18 |
| Explicación SHAP | forest / test temporal | 31.260643200 | 188 | 1 | completa | Total; eventos.jsonl línea 19 |
| Explicación SHAP | xgboost / test temporal | 0.031232200 | 188 | 1 | completa | Total; eventos.jsonl línea 20 |
| Explicación SHAP | decision_tree / test temporal | 6.004391600 | 188 | 1 | completa | Total; eventos.jsonl línea 21 |
| Explicación SHAP | ridge / test · permutaciones de control | 6.458652800 | 188 | 1 | completa | Total; eventos.jsonl línea 22 |
| Explicación SHAP | xgboost / test · permutaciones de control | 15.191162400 | 188 | 1 | completa | Total; eventos.jsonl línea 23 |
| Explicación LIME | xgboost / test #124 | 0.060967100 | 1000 | 1 | completa | Total; eventos.jsonl línea 24 |
| Explicación LIME | xgboost / test #118 | 0.053030900 | 1000 | 1 | completa | Total; eventos.jsonl línea 25 |
| Total del experimento | Book · evaluación, diagnósticos y SHAP de clásicos | 100.734220700 | No aplica | 1 | completa | Total; eventos.jsonl línea 26 |

### Ejecución `20261019_083039_147f9845`

- **Modelo/motivo:** Originales · multibúsqueda de menor coste.
- **Fecha/zona:** 2026-10-19T08:30:39.022374-05:00 a 2026-10-19T08:37:02.711614-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_083039_147f9845/metadata.json](tiempos/20261019_083039_147f9845/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_083039_147f9845/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Búsqueda | m0 / external_1 / Grid Search | 12.816335100 | 1047 | 1 | completa | Total; eventos.jsonl línea 1 |
| Búsqueda | m0 / external_1 / Random Search | 3.615859500 | 1047 | 1 | completa | Total; eventos.jsonl línea 2 |
| Búsqueda | m0 / external_1 / Bayesiana TPE | 6.012259200 | 1047 | 1 | completa | Total; eventos.jsonl línea 3 |
| Búsqueda | m0 / external_1 / Genética DEAP | 2.983556300 | 1047 | 1 | completa | Total; eventos.jsonl línea 4 |
| Búsqueda | m0 / external_1 / Successive Halving | 3.674602500 | 1047 | 1 | completa | Total; eventos.jsonl línea 5 |
| Entrenamiento/refit | m0 / externo1 | 0.080939100 | 1047 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | m0 / OOF externo1 | 0.030650400 | 262 | 1 | completa | Total; eventos.jsonl línea 7 |
| Búsqueda | m0 / external_2 / Grid Search | 7.377212600 | 1047 | 1 | completa | Total; eventos.jsonl línea 8 |
| Búsqueda | m0 / external_2 / Random Search | 3.961480900 | 1047 | 1 | completa | Total; eventos.jsonl línea 9 |
| Búsqueda | m0 / external_2 / Bayesiana TPE | 5.778761000 | 1047 | 1 | completa | Total; eventos.jsonl línea 10 |
| Búsqueda | m0 / external_2 / Genética DEAP | 3.076194200 | 1047 | 1 | completa | Total; eventos.jsonl línea 11 |
| Búsqueda | m0 / external_2 / Successive Halving | 3.750318700 | 1047 | 1 | completa | Total; eventos.jsonl línea 12 |
| Entrenamiento/refit | m0 / externo2 | 0.067565800 | 1047 | 1 | completa | Total; eventos.jsonl línea 13 |
| Inferencia | m0 / OOF externo2 | 0.038261700 | 262 | 1 | completa | Total; eventos.jsonl línea 14 |
| Búsqueda | m0 / external_3 / Grid Search | 8.011888600 | 1047 | 1 | completa | Total; eventos.jsonl línea 15 |
| Búsqueda | m0 / external_3 / Random Search | 4.068416200 | 1047 | 1 | completa | Total; eventos.jsonl línea 16 |
| Búsqueda | m0 / external_3 / Bayesiana TPE | 5.782820900 | 1047 | 1 | completa | Total; eventos.jsonl línea 17 |
| Búsqueda | m0 / external_3 / Genética DEAP | 3.109879900 | 1047 | 1 | completa | Total; eventos.jsonl línea 18 |
| Búsqueda | m0 / external_3 / Successive Halving | 3.767657600 | 1047 | 1 | completa | Total; eventos.jsonl línea 19 |
| Entrenamiento/refit | m0 / externo3 | 0.075945800 | 1047 | 1 | completa | Total; eventos.jsonl línea 20 |
| Inferencia | m0 / OOF externo3 | 0.030127700 | 262 | 1 | completa | Total; eventos.jsonl línea 21 |
| Búsqueda | m0 / external_4 / Grid Search | 7.976791000 | 1047 | 1 | completa | Total; eventos.jsonl línea 22 |
| Búsqueda | m0 / external_4 / Random Search | 4.250440100 | 1047 | 1 | completa | Total; eventos.jsonl línea 23 |
| Búsqueda | m0 / external_4 / Bayesiana TPE | 6.455718600 | 1047 | 1 | completa | Total; eventos.jsonl línea 24 |
| Búsqueda | m0 / external_4 / Genética DEAP | 3.464234900 | 1047 | 1 | completa | Total; eventos.jsonl línea 25 |
| Búsqueda | m0 / external_4 / Successive Halving | 4.156181600 | 1047 | 1 | completa | Total; eventos.jsonl línea 26 |
| Entrenamiento/refit | m0 / externo4 | 0.086286900 | 1047 | 1 | completa | Total; eventos.jsonl línea 27 |
| Inferencia | m0 / OOF externo4 | 0.030259400 | 262 | 1 | completa | Total; eventos.jsonl línea 28 |
| Búsqueda | m0 / external_5 / Grid Search | 7.916320000 | 1048 | 1 | completa | Total; eventos.jsonl línea 29 |
| Búsqueda | m0 / external_5 / Random Search | 3.704669000 | 1048 | 1 | completa | Total; eventos.jsonl línea 30 |
| Búsqueda | m0 / external_5 / Bayesiana TPE | 5.730456500 | 1048 | 1 | completa | Total; eventos.jsonl línea 31 |
| Búsqueda | m0 / external_5 / Genética DEAP | 3.184033500 | 1048 | 1 | completa | Total; eventos.jsonl línea 32 |
| Búsqueda | m0 / external_5 / Successive Halving | 3.862455200 | 1048 | 1 | completa | Total; eventos.jsonl línea 33 |
| Entrenamiento/refit | m0 / externo5 | 0.091865400 | 1048 | 1 | completa | Total; eventos.jsonl línea 34 |
| Inferencia | m0 / OOF externo5 | 0.033763700 | 261 | 1 | completa | Total; eventos.jsonl línea 35 |
| Búsqueda | m0 / final / Grid Search | 10.404820200 | 1309 | 1 | completa | Total; eventos.jsonl línea 36 |
| Búsqueda | m0 / final / Random Search | 5.240710800 | 1309 | 1 | completa | Total; eventos.jsonl línea 37 |
| Búsqueda | m0 / final / Bayesiana TPE | 8.168990200 | 1309 | 1 | completa | Total; eventos.jsonl línea 38 |
| Búsqueda | m0 / final / Genética DEAP | 4.573740600 | 1309 | 1 | completa | Total; eventos.jsonl línea 39 |
| Búsqueda | m0 / final / Successive Halving | 4.817379900 | 1309 | 1 | completa | Total; eventos.jsonl línea 40 |
| Entrenamiento/refit | m0 / final | 0.097707500 | 1309 | 1 | completa | Total; eventos.jsonl línea 41 |
| Búsqueda | m5 / external_1 / Grid Search | 7.152705900 | 1047 | 1 | completa | Total; eventos.jsonl línea 42 |
| Búsqueda | m5 / external_1 / Random Search | 3.193628400 | 1047 | 1 | completa | Total; eventos.jsonl línea 43 |
| Búsqueda | m5 / external_1 / Bayesiana TPE | 4.052213800 | 1047 | 1 | completa | Total; eventos.jsonl línea 44 |
| Búsqueda | m5 / external_1 / Genética DEAP | 3.347286400 | 1047 | 1 | completa | Total; eventos.jsonl línea 45 |
| Búsqueda | m5 / external_1 / Successive Halving | 3.713788700 | 1047 | 1 | completa | Total; eventos.jsonl línea 46 |
| Entrenamiento/refit | m5 / externo1 | 0.093040100 | 1047 | 1 | completa | Total; eventos.jsonl línea 47 |
| Inferencia | m5 / OOF externo1 | 0.015583800 | 262 | 1 | completa | Total; eventos.jsonl línea 48 |
| Búsqueda | m5 / external_2 / Grid Search | 6.762412600 | 1047 | 1 | completa | Total; eventos.jsonl línea 49 |
| Búsqueda | m5 / external_2 / Random Search | 3.163301300 | 1047 | 1 | completa | Total; eventos.jsonl línea 50 |
| Búsqueda | m5 / external_2 / Bayesiana TPE | 3.765899900 | 1047 | 1 | completa | Total; eventos.jsonl línea 51 |
| Búsqueda | m5 / external_2 / Genética DEAP | 2.951930400 | 1047 | 1 | completa | Total; eventos.jsonl línea 52 |
| Búsqueda | m5 / external_2 / Successive Halving | 3.331320600 | 1047 | 1 | completa | Total; eventos.jsonl línea 53 |
| Entrenamiento/refit | m5 / externo2 | 0.071477900 | 1047 | 1 | completa | Total; eventos.jsonl línea 54 |
| Inferencia | m5 / OOF externo2 | 0.013918300 | 262 | 1 | completa | Total; eventos.jsonl línea 55 |
| Búsqueda | m5 / external_3 / Grid Search | 6.466135800 | 1047 | 1 | completa | Total; eventos.jsonl línea 56 |
| Búsqueda | m5 / external_3 / Random Search | 2.852697100 | 1047 | 1 | completa | Total; eventos.jsonl línea 57 |
| Búsqueda | m5 / external_3 / Bayesiana TPE | 3.796289800 | 1047 | 1 | completa | Total; eventos.jsonl línea 58 |
| Búsqueda | m5 / external_3 / Genética DEAP | 3.137064000 | 1047 | 1 | completa | Total; eventos.jsonl línea 59 |
| Búsqueda | m5 / external_3 / Successive Halving | 4.180973100 | 1047 | 1 | completa | Total; eventos.jsonl línea 60 |
| Entrenamiento/refit | m5 / externo3 | 0.086094400 | 1047 | 1 | completa | Total; eventos.jsonl línea 61 |
| Inferencia | m5 / OOF externo3 | 0.014855700 | 262 | 1 | completa | Total; eventos.jsonl línea 62 |
| Búsqueda | m5 / external_4 / Grid Search | 7.051003800 | 1047 | 1 | completa | Total; eventos.jsonl línea 63 |
| Búsqueda | m5 / external_4 / Random Search | 3.337697000 | 1047 | 1 | completa | Total; eventos.jsonl línea 64 |
| Búsqueda | m5 / external_4 / Bayesiana TPE | 4.000263500 | 1047 | 1 | completa | Total; eventos.jsonl línea 65 |
| Búsqueda | m5 / external_4 / Genética DEAP | 3.088848400 | 1047 | 1 | completa | Total; eventos.jsonl línea 66 |
| Búsqueda | m5 / external_4 / Successive Halving | 3.610724100 | 1047 | 1 | completa | Total; eventos.jsonl línea 67 |
| Entrenamiento/refit | m5 / externo4 | 0.090142300 | 1047 | 1 | completa | Total; eventos.jsonl línea 68 |
| Inferencia | m5 / OOF externo4 | 0.022142800 | 262 | 1 | completa | Total; eventos.jsonl línea 69 |
| Búsqueda | m5 / external_5 / Grid Search | 7.276130700 | 1048 | 1 | completa | Total; eventos.jsonl línea 70 |
| Búsqueda | m5 / external_5 / Random Search | 3.095758900 | 1048 | 1 | completa | Total; eventos.jsonl línea 71 |
| Búsqueda | m5 / external_5 / Bayesiana TPE | 4.032653000 | 1048 | 1 | completa | Total; eventos.jsonl línea 72 |
| Búsqueda | m5 / external_5 / Genética DEAP | 3.359868000 | 1048 | 1 | completa | Total; eventos.jsonl línea 73 |
| Búsqueda | m5 / external_5 / Successive Halving | 3.843391500 | 1048 | 1 | completa | Total; eventos.jsonl línea 74 |
| Entrenamiento/refit | m5 / externo5 | 0.073524400 | 1048 | 1 | completa | Total; eventos.jsonl línea 75 |
| Inferencia | m5 / OOF externo5 | 0.014693200 | 261 | 1 | completa | Total; eventos.jsonl línea 76 |
| Búsqueda | m5 / final / Grid Search | 8.552773100 | 1309 | 1 | completa | Total; eventos.jsonl línea 77 |
| Búsqueda | m5 / final / Random Search | 2.746374300 | 1309 | 1 | completa | Total; eventos.jsonl línea 78 |
| Búsqueda | m5 / final / Bayesiana TPE | 3.478243000 | 1309 | 1 | completa | Total; eventos.jsonl línea 79 |
| Búsqueda | m5 / final / Genética DEAP | 2.885726800 | 1309 | 1 | completa | Total; eventos.jsonl línea 80 |
| Búsqueda | m5 / final / Successive Halving | 2.525522900 | 1309 | 1 | completa | Total; eventos.jsonl línea 81 |
| Entrenamiento/refit | m5 / final | 0.077704000 | 1309 | 1 | completa | Total; eventos.jsonl línea 82 |
| Búsqueda | m19 / external_1 / Grid Search | 3.980381600 | 1047 | 1 | completa | Total; eventos.jsonl línea 83 |
| Búsqueda | m19 / external_1 / Random Search | 1.848432400 | 1047 | 1 | completa | Total; eventos.jsonl línea 84 |
| Búsqueda | m19 / external_1 / Bayesiana TPE | 3.961152300 | 1047 | 1 | completa | Total; eventos.jsonl línea 85 |
| Búsqueda | m19 / external_1 / Genética DEAP | 2.845620300 | 1047 | 1 | completa | Total; eventos.jsonl línea 86 |
| Búsqueda | m19 / external_1 / Successive Halving | 3.307967900 | 1047 | 1 | completa | Total; eventos.jsonl línea 87 |
| Entrenamiento/refit | m19 / externo1 | 0.055242400 | 1047 | 1 | completa | Total; eventos.jsonl línea 88 |
| Inferencia | m19 / OOF externo1 | 0.018151500 | 262 | 1 | completa | Total; eventos.jsonl línea 89 |
| Búsqueda | m19 / external_2 / Grid Search | 6.325453100 | 1047 | 1 | completa | Total; eventos.jsonl línea 90 |
| Búsqueda | m19 / external_2 / Random Search | 2.604913500 | 1047 | 1 | completa | Total; eventos.jsonl línea 91 |
| Búsqueda | m19 / external_2 / Bayesiana TPE | 3.397671800 | 1047 | 1 | completa | Total; eventos.jsonl línea 92 |
| Búsqueda | m19 / external_2 / Genética DEAP | 2.597294900 | 1047 | 1 | completa | Total; eventos.jsonl línea 93 |
| Búsqueda | m19 / external_2 / Successive Halving | 3.284707700 | 1047 | 1 | completa | Total; eventos.jsonl línea 94 |
| Entrenamiento/refit | m19 / externo2 | 0.059436900 | 1047 | 1 | completa | Total; eventos.jsonl línea 95 |
| Inferencia | m19 / OOF externo2 | 0.018034100 | 262 | 1 | completa | Total; eventos.jsonl línea 96 |
| Búsqueda | m19 / external_3 / Grid Search | 5.865672100 | 1047 | 1 | completa | Total; eventos.jsonl línea 97 |
| Búsqueda | m19 / external_3 / Random Search | 2.589881800 | 1047 | 1 | completa | Total; eventos.jsonl línea 98 |
| Búsqueda | m19 / external_3 / Bayesiana TPE | 3.555909300 | 1047 | 1 | completa | Total; eventos.jsonl línea 99 |
| Búsqueda | m19 / external_3 / Genética DEAP | 2.975443700 | 1047 | 1 | completa | Total; eventos.jsonl línea 100 |
| Búsqueda | m19 / external_3 / Successive Halving | 3.476015000 | 1047 | 1 | completa | Total; eventos.jsonl línea 101 |
| Entrenamiento/refit | m19 / externo3 | 0.052531400 | 1047 | 1 | completa | Total; eventos.jsonl línea 102 |
| Inferencia | m19 / OOF externo3 | 0.016917600 | 262 | 1 | completa | Total; eventos.jsonl línea 103 |
| Búsqueda | m19 / external_4 / Grid Search | 5.273652700 | 1047 | 1 | completa | Total; eventos.jsonl línea 104 |
| Búsqueda | m19 / external_4 / Random Search | 1.836864000 | 1047 | 1 | completa | Total; eventos.jsonl línea 105 |
| Búsqueda | m19 / external_4 / Bayesiana TPE | 2.361706300 | 1047 | 1 | completa | Total; eventos.jsonl línea 106 |
| Búsqueda | m19 / external_4 / Genética DEAP | 1.800836400 | 1047 | 1 | completa | Total; eventos.jsonl línea 107 |
| Búsqueda | m19 / external_4 / Successive Halving | 2.164572900 | 1047 | 1 | completa | Total; eventos.jsonl línea 108 |
| Entrenamiento/refit | m19 / externo4 | 0.036908800 | 1047 | 1 | completa | Total; eventos.jsonl línea 109 |
| Inferencia | m19 / OOF externo4 | 0.010896400 | 262 | 1 | completa | Total; eventos.jsonl línea 110 |
| Búsqueda | m19 / external_5 / Grid Search | 4.038075700 | 1048 | 1 | completa | Total; eventos.jsonl línea 111 |
| Búsqueda | m19 / external_5 / Random Search | 1.810206400 | 1048 | 1 | completa | Total; eventos.jsonl línea 112 |
| Búsqueda | m19 / external_5 / Bayesiana TPE | 2.280959400 | 1048 | 1 | completa | Total; eventos.jsonl línea 113 |
| Búsqueda | m19 / external_5 / Genética DEAP | 1.763909700 | 1048 | 1 | completa | Total; eventos.jsonl línea 114 |
| Búsqueda | m19 / external_5 / Successive Halving | 2.067824000 | 1048 | 1 | completa | Total; eventos.jsonl línea 115 |
| Entrenamiento/refit | m19 / externo5 | 0.036772100 | 1048 | 1 | completa | Total; eventos.jsonl línea 116 |
| Inferencia | m19 / OOF externo5 | 0.010494400 | 261 | 1 | completa | Total; eventos.jsonl línea 117 |
| Búsqueda | m19 / final / Grid Search | 5.361963900 | 1309 | 1 | completa | Total; eventos.jsonl línea 118 |
| Búsqueda | m19 / final / Random Search | 2.263569100 | 1309 | 1 | completa | Total; eventos.jsonl línea 119 |
| Búsqueda | m19 / final / Bayesiana TPE | 2.930947400 | 1309 | 1 | completa | Total; eventos.jsonl línea 120 |
| Búsqueda | m19 / final / Genética DEAP | 2.189979500 | 1309 | 1 | completa | Total; eventos.jsonl línea 121 |
| Búsqueda | m19 / final / Successive Halving | 2.311371600 | 1309 | 1 | completa | Total; eventos.jsonl línea 122 |
| Entrenamiento/refit | m19 / final | 0.046530600 | 1309 | 1 | completa | Total; eventos.jsonl línea 123 |
| Inferencia | m0 / test202530 | 0.013053800 | 188 | 1 | completa | Total; eventos.jsonl línea 124 |
| Inferencia | m5 / test202530 | 0.009580100 | 188 | 1 | completa | Total; eventos.jsonl línea 125 |
| Inferencia | m19 / test202530 | 0.009553800 | 188 | 1 | completa | Total; eventos.jsonl línea 126 |
| Total del experimento | Originales · multibúsqueda de menor coste | 383.686557500 | No aplica | 1 | completa | Total; eventos.jsonl línea 127 |

### Ejecución `20261019_083730_cead9181`

- **Modelo/motivo:** Originales · Friedman/MCS y contrastes por estudiante.
- **Fecha/zona:** 2026-10-19T08:37:30.900479-05:00 a 2026-10-19T08:37:36.570836-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_083730_cead9181/metadata.json](tiempos/20261019_083730_cead9181/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_083730_cead9181/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Análisis estadístico | Friedman/MCS Originales | 0.445519600 | 25 | 1 | completa | Total; eventos.jsonl línea 1 |
| Análisis estadístico | Bootstrap-t/BCa y Holm25 Originales | 2.951874400 | 188 | 1 | completa | Total; eventos.jsonl línea 2 |
| Total del experimento | Originales · Friedman/MCS y contrastes por estudiante | 5.659484600 | No aplica | 1 | completa | Total; eventos.jsonl línea 3 |

### Ejecución `20261019_083736_71f6920a`

- **Modelo/motivo:** Kernel Ridge RBF · SHAP aproximado por permutaciones y LIME.
- **Fecha/zona:** 2026-10-19T08:37:36.803403-05:00 a 2026-10-19T08:38:38.331710-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_083736_71f6920a/metadata.json](tiempos/20261019_083736_71f6920a/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_083736_71f6920a/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote0 | 0.064177700 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote1 | 0.006581300 | 32 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote2 | 0.061967200 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote3 | 0.062688300 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote4 | 0.064787200 | 1497 | 1 | completa | Total; eventos.jsonl línea 5 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote5 | 0.068499900 | 1497 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote6 | 0.060276000 | 1497 | 1 | completa | Total; eventos.jsonl línea 7 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote7 | 0.061050300 | 1497 | 1 | completa | Total; eventos.jsonl línea 8 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote8 | 0.061027200 | 1497 | 1 | completa | Total; eventos.jsonl línea 9 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote9 | 0.059900600 | 1497 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote10 | 0.069248600 | 1497 | 1 | completa | Total; eventos.jsonl línea 11 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote11 | 0.064017000 | 1497 | 1 | completa | Total; eventos.jsonl línea 12 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote12 | 0.064710900 | 1497 | 1 | completa | Total; eventos.jsonl línea 13 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote13 | 0.063194600 | 1497 | 1 | completa | Total; eventos.jsonl línea 14 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote14 | 0.067782800 | 1497 | 1 | completa | Total; eventos.jsonl línea 15 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote15 | 0.059067800 | 1497 | 1 | completa | Total; eventos.jsonl línea 16 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote16 | 0.058181400 | 1497 | 1 | completa | Total; eventos.jsonl línea 17 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote17 | 0.061007200 | 1497 | 1 | completa | Total; eventos.jsonl línea 18 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote18 | 0.060087100 | 1497 | 1 | completa | Total; eventos.jsonl línea 19 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote19 | 0.061743400 | 1497 | 1 | completa | Total; eventos.jsonl línea 20 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote20 | 0.061202300 | 1497 | 1 | completa | Total; eventos.jsonl línea 21 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote21 | 0.061104800 | 1497 | 1 | completa | Total; eventos.jsonl línea 22 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote22 | 0.062179700 | 1497 | 1 | completa | Total; eventos.jsonl línea 23 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote23 | 0.126550000 | 1497 | 1 | completa | Total; eventos.jsonl línea 24 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote24 | 0.064935800 | 1497 | 1 | completa | Total; eventos.jsonl línea 25 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote25 | 0.066182000 | 1497 | 1 | completa | Total; eventos.jsonl línea 26 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote26 | 0.061427100 | 1497 | 1 | completa | Total; eventos.jsonl línea 27 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote27 | 0.063423200 | 1497 | 1 | completa | Total; eventos.jsonl línea 28 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote28 | 0.059744100 | 1497 | 1 | completa | Total; eventos.jsonl línea 29 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote29 | 0.060604400 | 1497 | 1 | completa | Total; eventos.jsonl línea 30 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote30 | 0.063984800 | 1497 | 1 | completa | Total; eventos.jsonl línea 31 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote31 | 0.063187400 | 1497 | 1 | completa | Total; eventos.jsonl línea 32 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote32 | 0.064409500 | 1497 | 1 | completa | Total; eventos.jsonl línea 33 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote33 | 0.067086900 | 1497 | 1 | completa | Total; eventos.jsonl línea 34 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote34 | 0.060769500 | 1497 | 1 | completa | Total; eventos.jsonl línea 35 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote35 | 0.059776300 | 1497 | 1 | completa | Total; eventos.jsonl línea 36 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote36 | 0.061018100 | 1497 | 1 | completa | Total; eventos.jsonl línea 37 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote37 | 0.059918200 | 1497 | 1 | completa | Total; eventos.jsonl línea 38 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote38 | 0.062758700 | 1497 | 1 | completa | Total; eventos.jsonl línea 39 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote39 | 0.062864200 | 1497 | 1 | completa | Total; eventos.jsonl línea 40 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote40 | 0.062451700 | 1497 | 1 | completa | Total; eventos.jsonl línea 41 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote41 | 0.064954900 | 1497 | 1 | completa | Total; eventos.jsonl línea 42 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote42 | 0.060567000 | 1497 | 1 | completa | Total; eventos.jsonl línea 43 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote43 | 0.061267500 | 1497 | 1 | completa | Total; eventos.jsonl línea 44 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote44 | 0.060991800 | 1497 | 1 | completa | Total; eventos.jsonl línea 45 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote45 | 0.063163300 | 1497 | 1 | completa | Total; eventos.jsonl línea 46 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote46 | 0.063990500 | 1497 | 1 | completa | Total; eventos.jsonl línea 47 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote47 | 0.059250000 | 1497 | 1 | completa | Total; eventos.jsonl línea 48 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote48 | 0.061342900 | 1497 | 1 | completa | Total; eventos.jsonl línea 49 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote49 | 0.058511700 | 1497 | 1 | completa | Total; eventos.jsonl línea 50 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote50 | 0.063139600 | 1497 | 1 | completa | Total; eventos.jsonl línea 51 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote51 | 0.063975700 | 1497 | 1 | completa | Total; eventos.jsonl línea 52 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote52 | 0.063287000 | 1497 | 1 | completa | Total; eventos.jsonl línea 53 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote53 | 0.061889400 | 1497 | 1 | completa | Total; eventos.jsonl línea 54 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote54 | 0.064283700 | 1497 | 1 | completa | Total; eventos.jsonl línea 55 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote55 | 0.064716000 | 1497 | 1 | completa | Total; eventos.jsonl línea 56 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote56 | 0.070516600 | 1497 | 1 | completa | Total; eventos.jsonl línea 57 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote57 | 0.062210700 | 1497 | 1 | completa | Total; eventos.jsonl línea 58 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote58 | 0.063732200 | 1497 | 1 | completa | Total; eventos.jsonl línea 59 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote59 | 0.061522900 | 1497 | 1 | completa | Total; eventos.jsonl línea 60 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote60 | 0.062350900 | 1497 | 1 | completa | Total; eventos.jsonl línea 61 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote61 | 0.062911300 | 1497 | 1 | completa | Total; eventos.jsonl línea 62 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote62 | 0.063906000 | 1497 | 1 | completa | Total; eventos.jsonl línea 63 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote63 | 0.064140100 | 1497 | 1 | completa | Total; eventos.jsonl línea 64 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote64 | 0.068014000 | 1497 | 1 | completa | Total; eventos.jsonl línea 65 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote65 | 0.065027200 | 1497 | 1 | completa | Total; eventos.jsonl línea 66 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote66 | 0.065196200 | 1497 | 1 | completa | Total; eventos.jsonl línea 67 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote67 | 0.070302000 | 1497 | 1 | completa | Total; eventos.jsonl línea 68 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote68 | 0.065886100 | 1497 | 1 | completa | Total; eventos.jsonl línea 69 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote69 | 0.063270300 | 1497 | 1 | completa | Total; eventos.jsonl línea 70 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote70 | 0.062148100 | 1497 | 1 | completa | Total; eventos.jsonl línea 71 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote71 | 0.063913300 | 1497 | 1 | completa | Total; eventos.jsonl línea 72 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote72 | 0.067601500 | 1497 | 1 | completa | Total; eventos.jsonl línea 73 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote73 | 0.069000400 | 1497 | 1 | completa | Total; eventos.jsonl línea 74 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote74 | 0.064135500 | 1497 | 1 | completa | Total; eventos.jsonl línea 75 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote75 | 0.066511900 | 1497 | 1 | completa | Total; eventos.jsonl línea 76 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote76 | 0.065195900 | 1497 | 1 | completa | Total; eventos.jsonl línea 77 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote77 | 0.060371900 | 1497 | 1 | completa | Total; eventos.jsonl línea 78 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote78 | 0.058117200 | 1497 | 1 | completa | Total; eventos.jsonl línea 79 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote79 | 0.059940000 | 1497 | 1 | completa | Total; eventos.jsonl línea 80 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote80 | 0.060883900 | 1497 | 1 | completa | Total; eventos.jsonl línea 81 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote81 | 0.063457400 | 1497 | 1 | completa | Total; eventos.jsonl línea 82 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote82 | 0.062712700 | 1497 | 1 | completa | Total; eventos.jsonl línea 83 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote83 | 0.065968900 | 1497 | 1 | completa | Total; eventos.jsonl línea 84 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote84 | 0.063687200 | 1497 | 1 | completa | Total; eventos.jsonl línea 85 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote85 | 0.060855400 | 1497 | 1 | completa | Total; eventos.jsonl línea 86 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote86 | 0.059636500 | 1497 | 1 | completa | Total; eventos.jsonl línea 87 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote87 | 0.063198500 | 1497 | 1 | completa | Total; eventos.jsonl línea 88 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote88 | 0.062295100 | 1497 | 1 | completa | Total; eventos.jsonl línea 89 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote89 | 0.063820800 | 1497 | 1 | completa | Total; eventos.jsonl línea 90 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote90 | 0.064602100 | 1497 | 1 | completa | Total; eventos.jsonl línea 91 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote91 | 0.062478000 | 1497 | 1 | completa | Total; eventos.jsonl línea 92 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote92 | 0.063483100 | 1497 | 1 | completa | Total; eventos.jsonl línea 93 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote93 | 0.064331300 | 1497 | 1 | completa | Total; eventos.jsonl línea 94 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote94 | 0.063513800 | 1497 | 1 | completa | Total; eventos.jsonl línea 95 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote95 | 0.061817300 | 1497 | 1 | completa | Total; eventos.jsonl línea 96 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote96 | 0.061760900 | 1497 | 1 | completa | Total; eventos.jsonl línea 97 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote97 | 0.067507900 | 1497 | 1 | completa | Total; eventos.jsonl línea 98 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote98 | 0.062178700 | 1497 | 1 | completa | Total; eventos.jsonl línea 99 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote99 | 0.060280500 | 1497 | 1 | completa | Total; eventos.jsonl línea 100 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote100 | 0.061759900 | 1497 | 1 | completa | Total; eventos.jsonl línea 101 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote101 | 0.058377700 | 1497 | 1 | completa | Total; eventos.jsonl línea 102 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote102 | 0.060993200 | 1497 | 1 | completa | Total; eventos.jsonl línea 103 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote103 | 0.065810700 | 1497 | 1 | completa | Total; eventos.jsonl línea 104 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote104 | 0.063890900 | 1497 | 1 | completa | Total; eventos.jsonl línea 105 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote105 | 0.064350500 | 1497 | 1 | completa | Total; eventos.jsonl línea 106 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote106 | 0.061892900 | 1497 | 1 | completa | Total; eventos.jsonl línea 107 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote107 | 0.063222600 | 1497 | 1 | completa | Total; eventos.jsonl línea 108 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote108 | 0.061042900 | 1497 | 1 | completa | Total; eventos.jsonl línea 109 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote109 | 0.064444300 | 1497 | 1 | completa | Total; eventos.jsonl línea 110 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote110 | 0.062010600 | 1497 | 1 | completa | Total; eventos.jsonl línea 111 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote111 | 0.063213600 | 1497 | 1 | completa | Total; eventos.jsonl línea 112 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote112 | 0.062833300 | 1497 | 1 | completa | Total; eventos.jsonl línea 113 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote113 | 0.065299800 | 1497 | 1 | completa | Total; eventos.jsonl línea 114 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote114 | 0.068684800 | 1497 | 1 | completa | Total; eventos.jsonl línea 115 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote115 | 0.061831200 | 1497 | 1 | completa | Total; eventos.jsonl línea 116 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote116 | 0.065614200 | 1497 | 1 | completa | Total; eventos.jsonl línea 117 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote117 | 0.059729700 | 1497 | 1 | completa | Total; eventos.jsonl línea 118 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote118 | 0.060200400 | 1497 | 1 | completa | Total; eventos.jsonl línea 119 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote119 | 0.067315700 | 1497 | 1 | completa | Total; eventos.jsonl línea 120 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote120 | 0.059976300 | 1497 | 1 | completa | Total; eventos.jsonl línea 121 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote121 | 0.064765400 | 1497 | 1 | completa | Total; eventos.jsonl línea 122 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote122 | 0.067978400 | 1497 | 1 | completa | Total; eventos.jsonl línea 123 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote123 | 0.067580500 | 1497 | 1 | completa | Total; eventos.jsonl línea 124 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote124 | 0.063800600 | 1497 | 1 | completa | Total; eventos.jsonl línea 125 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote125 | 0.065684200 | 1497 | 1 | completa | Total; eventos.jsonl línea 126 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote126 | 0.064072200 | 1497 | 1 | completa | Total; eventos.jsonl línea 127 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote127 | 0.066525800 | 1497 | 1 | completa | Total; eventos.jsonl línea 128 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote128 | 0.066167700 | 1497 | 1 | completa | Total; eventos.jsonl línea 129 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote129 | 0.063736500 | 1497 | 1 | completa | Total; eventos.jsonl línea 130 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote130 | 0.063937700 | 1497 | 1 | completa | Total; eventos.jsonl línea 131 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote131 | 0.063017500 | 1497 | 1 | completa | Total; eventos.jsonl línea 132 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote132 | 0.059524500 | 1497 | 1 | completa | Total; eventos.jsonl línea 133 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote133 | 0.064453400 | 1497 | 1 | completa | Total; eventos.jsonl línea 134 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote134 | 0.065867400 | 1497 | 1 | completa | Total; eventos.jsonl línea 135 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote135 | 0.058901100 | 1497 | 1 | completa | Total; eventos.jsonl línea 136 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote136 | 0.064044600 | 1497 | 1 | completa | Total; eventos.jsonl línea 137 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote137 | 0.063360000 | 1497 | 1 | completa | Total; eventos.jsonl línea 138 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote138 | 0.067488300 | 1497 | 1 | completa | Total; eventos.jsonl línea 139 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote139 | 0.064704300 | 1497 | 1 | completa | Total; eventos.jsonl línea 140 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote140 | 0.064334200 | 1497 | 1 | completa | Total; eventos.jsonl línea 141 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote141 | 0.064542700 | 1497 | 1 | completa | Total; eventos.jsonl línea 142 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote142 | 0.061180400 | 1497 | 1 | completa | Total; eventos.jsonl línea 143 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote143 | 0.063025000 | 1497 | 1 | completa | Total; eventos.jsonl línea 144 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote144 | 0.064402200 | 1497 | 1 | completa | Total; eventos.jsonl línea 145 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote145 | 0.060407600 | 1497 | 1 | completa | Total; eventos.jsonl línea 146 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote146 | 0.063445300 | 1497 | 1 | completa | Total; eventos.jsonl línea 147 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote147 | 0.063826100 | 1497 | 1 | completa | Total; eventos.jsonl línea 148 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote148 | 0.062116000 | 1497 | 1 | completa | Total; eventos.jsonl línea 149 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote149 | 0.064083200 | 1497 | 1 | completa | Total; eventos.jsonl línea 150 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote150 | 0.063229200 | 1497 | 1 | completa | Total; eventos.jsonl línea 151 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote151 | 0.060334500 | 1497 | 1 | completa | Total; eventos.jsonl línea 152 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote152 | 0.065012600 | 1497 | 1 | completa | Total; eventos.jsonl línea 153 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote153 | 0.060763200 | 1497 | 1 | completa | Total; eventos.jsonl línea 154 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote154 | 0.059268500 | 1497 | 1 | completa | Total; eventos.jsonl línea 155 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote155 | 0.064688200 | 1497 | 1 | completa | Total; eventos.jsonl línea 156 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote156 | 0.062886200 | 1497 | 1 | completa | Total; eventos.jsonl línea 157 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote157 | 0.060730800 | 1497 | 1 | completa | Total; eventos.jsonl línea 158 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote158 | 0.061846600 | 1497 | 1 | completa | Total; eventos.jsonl línea 159 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote159 | 0.063427600 | 1497 | 1 | completa | Total; eventos.jsonl línea 160 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote160 | 0.062081800 | 1497 | 1 | completa | Total; eventos.jsonl línea 161 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote161 | 0.061129200 | 1497 | 1 | completa | Total; eventos.jsonl línea 162 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote162 | 0.063641900 | 1497 | 1 | completa | Total; eventos.jsonl línea 163 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote163 | 0.062407500 | 1497 | 1 | completa | Total; eventos.jsonl línea 164 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote164 | 0.063930200 | 1497 | 1 | completa | Total; eventos.jsonl línea 165 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote165 | 0.067188400 | 1497 | 1 | completa | Total; eventos.jsonl línea 166 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote166 | 0.063175300 | 1497 | 1 | completa | Total; eventos.jsonl línea 167 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote167 | 0.062414600 | 1497 | 1 | completa | Total; eventos.jsonl línea 168 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote168 | 0.061251600 | 1497 | 1 | completa | Total; eventos.jsonl línea 169 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote169 | 0.061036000 | 1497 | 1 | completa | Total; eventos.jsonl línea 170 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote170 | 0.062001800 | 1497 | 1 | completa | Total; eventos.jsonl línea 171 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote171 | 0.060032800 | 1497 | 1 | completa | Total; eventos.jsonl línea 172 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote172 | 0.058474000 | 1497 | 1 | completa | Total; eventos.jsonl línea 173 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote173 | 0.060763100 | 1497 | 1 | completa | Total; eventos.jsonl línea 174 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote174 | 0.059599700 | 1497 | 1 | completa | Total; eventos.jsonl línea 175 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote175 | 0.060744900 | 1497 | 1 | completa | Total; eventos.jsonl línea 176 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote176 | 0.062487000 | 1497 | 1 | completa | Total; eventos.jsonl línea 177 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote177 | 0.062225000 | 1497 | 1 | completa | Total; eventos.jsonl línea 178 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote178 | 0.070877200 | 1497 | 1 | completa | Total; eventos.jsonl línea 179 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote179 | 0.061232800 | 1497 | 1 | completa | Total; eventos.jsonl línea 180 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote180 | 0.063316000 | 1497 | 1 | completa | Total; eventos.jsonl línea 181 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote181 | 0.062624400 | 1497 | 1 | completa | Total; eventos.jsonl línea 182 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote182 | 0.062104500 | 1497 | 1 | completa | Total; eventos.jsonl línea 183 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote183 | 0.064372200 | 1497 | 1 | completa | Total; eventos.jsonl línea 184 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote184 | 0.064561600 | 1497 | 1 | completa | Total; eventos.jsonl línea 185 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote185 | 0.064778800 | 1497 | 1 | completa | Total; eventos.jsonl línea 186 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote186 | 0.060771900 | 1497 | 1 | completa | Total; eventos.jsonl línea 187 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote187 | 0.061737800 | 1497 | 1 | completa | Total; eventos.jsonl línea 188 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote188 | 0.062058300 | 1497 | 1 | completa | Total; eventos.jsonl línea 189 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote189 | 0.064977100 | 1497 | 1 | completa | Total; eventos.jsonl línea 190 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote190 | 0.067606300 | 1497 | 1 | completa | Total; eventos.jsonl línea 191 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote191 | 0.065563000 | 1497 | 1 | completa | Total; eventos.jsonl línea 192 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote192 | 0.064660400 | 1497 | 1 | completa | Total; eventos.jsonl línea 193 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote193 | 0.063233100 | 1497 | 1 | completa | Total; eventos.jsonl línea 194 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote194 | 0.063451900 | 1497 | 1 | completa | Total; eventos.jsonl línea 195 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote195 | 0.063610800 | 1497 | 1 | completa | Total; eventos.jsonl línea 196 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote196 | 0.063740100 | 1497 | 1 | completa | Total; eventos.jsonl línea 197 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote197 | 0.067573900 | 1497 | 1 | completa | Total; eventos.jsonl línea 198 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote198 | 0.063802300 | 1497 | 1 | completa | Total; eventos.jsonl línea 199 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote199 | 0.063287400 | 1497 | 1 | completa | Total; eventos.jsonl línea 200 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote200 | 0.061205000 | 1497 | 1 | completa | Total; eventos.jsonl línea 201 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote201 | 0.062983900 | 1497 | 1 | completa | Total; eventos.jsonl línea 202 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote202 | 0.062505000 | 1497 | 1 | completa | Total; eventos.jsonl línea 203 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote203 | 0.060460600 | 1497 | 1 | completa | Total; eventos.jsonl línea 204 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote204 | 0.061796900 | 1497 | 1 | completa | Total; eventos.jsonl línea 205 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote205 | 0.062414300 | 1497 | 1 | completa | Total; eventos.jsonl línea 206 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote206 | 0.059921500 | 1497 | 1 | completa | Total; eventos.jsonl línea 207 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote207 | 0.060997400 | 1497 | 1 | completa | Total; eventos.jsonl línea 208 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote208 | 0.061506400 | 1497 | 1 | completa | Total; eventos.jsonl línea 209 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote209 | 0.064191000 | 1497 | 1 | completa | Total; eventos.jsonl línea 210 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote210 | 0.065255800 | 1497 | 1 | completa | Total; eventos.jsonl línea 211 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote211 | 0.062509000 | 1497 | 1 | completa | Total; eventos.jsonl línea 212 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote212 | 0.067902300 | 1497 | 1 | completa | Total; eventos.jsonl línea 213 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote213 | 0.076460500 | 1497 | 1 | completa | Total; eventos.jsonl línea 214 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote214 | 0.068801300 | 1497 | 1 | completa | Total; eventos.jsonl línea 215 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote215 | 0.067453100 | 1497 | 1 | completa | Total; eventos.jsonl línea 216 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote216 | 0.061533800 | 1497 | 1 | completa | Total; eventos.jsonl línea 217 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote217 | 0.056785800 | 1497 | 1 | completa | Total; eventos.jsonl línea 218 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote218 | 0.058533600 | 1497 | 1 | completa | Total; eventos.jsonl línea 219 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote219 | 0.061055700 | 1497 | 1 | completa | Total; eventos.jsonl línea 220 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote220 | 0.065719200 | 1497 | 1 | completa | Total; eventos.jsonl línea 221 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote221 | 0.061636100 | 1497 | 1 | completa | Total; eventos.jsonl línea 222 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote222 | 0.060475000 | 1497 | 1 | completa | Total; eventos.jsonl línea 223 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote223 | 0.059248800 | 1497 | 1 | completa | Total; eventos.jsonl línea 224 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote224 | 0.060047000 | 1497 | 1 | completa | Total; eventos.jsonl línea 225 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote225 | 0.060723100 | 1497 | 1 | completa | Total; eventos.jsonl línea 226 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote226 | 0.059303000 | 1497 | 1 | completa | Total; eventos.jsonl línea 227 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote227 | 0.060772700 | 1497 | 1 | completa | Total; eventos.jsonl línea 228 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote228 | 0.062619900 | 1497 | 1 | completa | Total; eventos.jsonl línea 229 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote229 | 0.060234100 | 1497 | 1 | completa | Total; eventos.jsonl línea 230 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote230 | 0.059523100 | 1497 | 1 | completa | Total; eventos.jsonl línea 231 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote231 | 0.067741500 | 1497 | 1 | completa | Total; eventos.jsonl línea 232 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote232 | 0.063587600 | 1497 | 1 | completa | Total; eventos.jsonl línea 233 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote233 | 0.062125900 | 1497 | 1 | completa | Total; eventos.jsonl línea 234 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote234 | 0.059793400 | 1497 | 1 | completa | Total; eventos.jsonl línea 235 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote235 | 0.058776800 | 1497 | 1 | completa | Total; eventos.jsonl línea 236 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote236 | 0.058210100 | 1497 | 1 | completa | Total; eventos.jsonl línea 237 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote237 | 0.058128100 | 1497 | 1 | completa | Total; eventos.jsonl línea 238 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote238 | 0.056729200 | 1497 | 1 | completa | Total; eventos.jsonl línea 239 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote239 | 0.060174200 | 1497 | 1 | completa | Total; eventos.jsonl línea 240 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote240 | 0.062187100 | 1497 | 1 | completa | Total; eventos.jsonl línea 241 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote241 | 0.057297900 | 1497 | 1 | completa | Total; eventos.jsonl línea 242 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote242 | 0.057281000 | 1497 | 1 | completa | Total; eventos.jsonl línea 243 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote243 | 0.055954800 | 1497 | 1 | completa | Total; eventos.jsonl línea 244 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote244 | 0.058379600 | 1497 | 1 | completa | Total; eventos.jsonl línea 245 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote245 | 0.060436700 | 1497 | 1 | completa | Total; eventos.jsonl línea 246 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote246 | 0.061920800 | 1497 | 1 | completa | Total; eventos.jsonl línea 247 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote247 | 0.063615300 | 1497 | 1 | completa | Total; eventos.jsonl línea 248 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote248 | 0.062428800 | 1497 | 1 | completa | Total; eventos.jsonl línea 249 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote249 | 0.065332400 | 1497 | 1 | completa | Total; eventos.jsonl línea 250 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote250 | 0.061242600 | 1497 | 1 | completa | Total; eventos.jsonl línea 251 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote251 | 0.063319000 | 1497 | 1 | completa | Total; eventos.jsonl línea 252 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote252 | 0.061888300 | 1497 | 1 | completa | Total; eventos.jsonl línea 253 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote253 | 0.061209800 | 1497 | 1 | completa | Total; eventos.jsonl línea 254 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote254 | 0.062463800 | 1497 | 1 | completa | Total; eventos.jsonl línea 255 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote255 | 0.061744400 | 1497 | 1 | completa | Total; eventos.jsonl línea 256 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote256 | 0.060099400 | 1497 | 1 | completa | Total; eventos.jsonl línea 257 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote257 | 0.058731800 | 1497 | 1 | completa | Total; eventos.jsonl línea 258 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote258 | 0.057994400 | 1497 | 1 | completa | Total; eventos.jsonl línea 259 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote259 | 0.060195700 | 1497 | 1 | completa | Total; eventos.jsonl línea 260 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote260 | 0.058594800 | 1497 | 1 | completa | Total; eventos.jsonl línea 261 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote261 | 0.063776200 | 1497 | 1 | completa | Total; eventos.jsonl línea 262 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote262 | 0.060345100 | 1497 | 1 | completa | Total; eventos.jsonl línea 263 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote263 | 0.058151100 | 1497 | 1 | completa | Total; eventos.jsonl línea 264 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote264 | 0.061056900 | 1497 | 1 | completa | Total; eventos.jsonl línea 265 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote265 | 0.064479800 | 1497 | 1 | completa | Total; eventos.jsonl línea 266 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote266 | 0.065963700 | 1497 | 1 | completa | Total; eventos.jsonl línea 267 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote267 | 0.060075900 | 1497 | 1 | completa | Total; eventos.jsonl línea 268 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote268 | 0.056372400 | 1497 | 1 | completa | Total; eventos.jsonl línea 269 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote269 | 0.057321900 | 1497 | 1 | completa | Total; eventos.jsonl línea 270 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote270 | 0.056087600 | 1497 | 1 | completa | Total; eventos.jsonl línea 271 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote271 | 0.057240100 | 1497 | 1 | completa | Total; eventos.jsonl línea 272 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote272 | 0.059104400 | 1497 | 1 | completa | Total; eventos.jsonl línea 273 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote273 | 0.060570400 | 1497 | 1 | completa | Total; eventos.jsonl línea 274 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote274 | 0.057695400 | 1497 | 1 | completa | Total; eventos.jsonl línea 275 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote275 | 0.067234100 | 1497 | 1 | completa | Total; eventos.jsonl línea 276 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote276 | 0.057705500 | 1497 | 1 | completa | Total; eventos.jsonl línea 277 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote277 | 0.058799500 | 1497 | 1 | completa | Total; eventos.jsonl línea 278 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote278 | 0.060028000 | 1497 | 1 | completa | Total; eventos.jsonl línea 279 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote279 | 0.059506200 | 1497 | 1 | completa | Total; eventos.jsonl línea 280 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote280 | 0.060682800 | 1497 | 1 | completa | Total; eventos.jsonl línea 281 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote281 | 0.061413900 | 1497 | 1 | completa | Total; eventos.jsonl línea 282 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote282 | 0.056926700 | 1497 | 1 | completa | Total; eventos.jsonl línea 283 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote283 | 0.061060300 | 1497 | 1 | completa | Total; eventos.jsonl línea 284 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote284 | 0.059076600 | 1497 | 1 | completa | Total; eventos.jsonl línea 285 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote285 | 0.061753800 | 1497 | 1 | completa | Total; eventos.jsonl línea 286 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote286 | 0.056200400 | 1497 | 1 | completa | Total; eventos.jsonl línea 287 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote287 | 0.062137100 | 1497 | 1 | completa | Total; eventos.jsonl línea 288 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote288 | 0.055985700 | 1497 | 1 | completa | Total; eventos.jsonl línea 289 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote289 | 0.062324000 | 1497 | 1 | completa | Total; eventos.jsonl línea 290 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote290 | 0.059688000 | 1497 | 1 | completa | Total; eventos.jsonl línea 291 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote291 | 0.061707200 | 1497 | 1 | completa | Total; eventos.jsonl línea 292 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote292 | 0.061019400 | 1497 | 1 | completa | Total; eventos.jsonl línea 293 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote293 | 0.066232100 | 1497 | 1 | completa | Total; eventos.jsonl línea 294 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote294 | 0.063341800 | 1497 | 1 | completa | Total; eventos.jsonl línea 295 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote295 | 0.065498200 | 1497 | 1 | completa | Total; eventos.jsonl línea 296 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote296 | 0.062137200 | 1497 | 1 | completa | Total; eventos.jsonl línea 297 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote297 | 0.061303800 | 1497 | 1 | completa | Total; eventos.jsonl línea 298 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote298 | 0.060583000 | 1497 | 1 | completa | Total; eventos.jsonl línea 299 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote299 | 0.059951900 | 1497 | 1 | completa | Total; eventos.jsonl línea 300 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote300 | 0.059136800 | 1497 | 1 | completa | Total; eventos.jsonl línea 301 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote301 | 0.059765300 | 1497 | 1 | completa | Total; eventos.jsonl línea 302 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote302 | 0.059360600 | 1497 | 1 | completa | Total; eventos.jsonl línea 303 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote303 | 0.061087800 | 1497 | 1 | completa | Total; eventos.jsonl línea 304 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote304 | 0.059304600 | 1497 | 1 | completa | Total; eventos.jsonl línea 305 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote305 | 0.059255700 | 1497 | 1 | completa | Total; eventos.jsonl línea 306 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote306 | 0.057803400 | 1497 | 1 | completa | Total; eventos.jsonl línea 307 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote307 | 0.058038900 | 1497 | 1 | completa | Total; eventos.jsonl línea 308 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote308 | 0.057369500 | 1497 | 1 | completa | Total; eventos.jsonl línea 309 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote309 | 0.058792900 | 1497 | 1 | completa | Total; eventos.jsonl línea 310 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote310 | 0.061819800 | 1497 | 1 | completa | Total; eventos.jsonl línea 311 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote311 | 0.058664600 | 1497 | 1 | completa | Total; eventos.jsonl línea 312 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote312 | 0.058307400 | 1497 | 1 | completa | Total; eventos.jsonl línea 313 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote313 | 0.058298400 | 1497 | 1 | completa | Total; eventos.jsonl línea 314 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote314 | 0.060146500 | 1497 | 1 | completa | Total; eventos.jsonl línea 315 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote315 | 0.062157000 | 1497 | 1 | completa | Total; eventos.jsonl línea 316 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote316 | 0.056658800 | 1497 | 1 | completa | Total; eventos.jsonl línea 317 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote317 | 0.059550500 | 1497 | 1 | completa | Total; eventos.jsonl línea 318 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote318 | 0.061978600 | 1497 | 1 | completa | Total; eventos.jsonl línea 319 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote319 | 0.074346000 | 1497 | 1 | completa | Total; eventos.jsonl línea 320 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote320 | 0.102017200 | 1497 | 1 | completa | Total; eventos.jsonl línea 321 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote321 | 0.088353200 | 1497 | 1 | completa | Total; eventos.jsonl línea 322 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote322 | 0.082219500 | 1497 | 1 | completa | Total; eventos.jsonl línea 323 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote323 | 0.083108400 | 1497 | 1 | completa | Total; eventos.jsonl línea 324 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote324 | 0.079823100 | 1497 | 1 | completa | Total; eventos.jsonl línea 325 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote325 | 0.088315800 | 1497 | 1 | completa | Total; eventos.jsonl línea 326 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote326 | 0.082123000 | 1497 | 1 | completa | Total; eventos.jsonl línea 327 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote327 | 0.089177800 | 1497 | 1 | completa | Total; eventos.jsonl línea 328 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote328 | 0.079504200 | 1497 | 1 | completa | Total; eventos.jsonl línea 329 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote329 | 0.082887200 | 1497 | 1 | completa | Total; eventos.jsonl línea 330 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote330 | 0.083993900 | 1497 | 1 | completa | Total; eventos.jsonl línea 331 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote331 | 0.087576000 | 1497 | 1 | completa | Total; eventos.jsonl línea 332 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote332 | 0.081647500 | 1497 | 1 | completa | Total; eventos.jsonl línea 333 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote333 | 0.079575000 | 1497 | 1 | completa | Total; eventos.jsonl línea 334 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote334 | 0.081674800 | 1497 | 1 | completa | Total; eventos.jsonl línea 335 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote335 | 0.084798200 | 1497 | 1 | completa | Total; eventos.jsonl línea 336 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote336 | 0.090790300 | 1497 | 1 | completa | Total; eventos.jsonl línea 337 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote337 | 0.081745100 | 1497 | 1 | completa | Total; eventos.jsonl línea 338 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote338 | 0.078246300 | 1497 | 1 | completa | Total; eventos.jsonl línea 339 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote339 | 0.079090300 | 1497 | 1 | completa | Total; eventos.jsonl línea 340 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote340 | 0.079739900 | 1497 | 1 | completa | Total; eventos.jsonl línea 341 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote341 | 0.080634800 | 1497 | 1 | completa | Total; eventos.jsonl línea 342 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote342 | 0.074038500 | 1497 | 1 | completa | Total; eventos.jsonl línea 343 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote343 | 0.067631200 | 1497 | 1 | completa | Total; eventos.jsonl línea 344 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote344 | 0.061395400 | 1497 | 1 | completa | Total; eventos.jsonl línea 345 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote345 | 0.063027800 | 1497 | 1 | completa | Total; eventos.jsonl línea 346 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote346 | 0.060958300 | 1497 | 1 | completa | Total; eventos.jsonl línea 347 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote347 | 0.061785200 | 1497 | 1 | completa | Total; eventos.jsonl línea 348 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote348 | 0.061516900 | 1497 | 1 | completa | Total; eventos.jsonl línea 349 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote349 | 0.063526000 | 1497 | 1 | completa | Total; eventos.jsonl línea 350 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote350 | 0.063670500 | 1497 | 1 | completa | Total; eventos.jsonl línea 351 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote351 | 0.060155100 | 1497 | 1 | completa | Total; eventos.jsonl línea 352 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote352 | 0.058340100 | 1497 | 1 | completa | Total; eventos.jsonl línea 353 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote353 | 0.057181500 | 1497 | 1 | completa | Total; eventos.jsonl línea 354 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote354 | 0.057845200 | 1497 | 1 | completa | Total; eventos.jsonl línea 355 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote355 | 0.059833800 | 1497 | 1 | completa | Total; eventos.jsonl línea 356 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote356 | 0.059288900 | 1497 | 1 | completa | Total; eventos.jsonl línea 357 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote357 | 0.066872000 | 1497 | 1 | completa | Total; eventos.jsonl línea 358 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote358 | 0.060604000 | 1497 | 1 | completa | Total; eventos.jsonl línea 359 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote359 | 0.062483400 | 1497 | 1 | completa | Total; eventos.jsonl línea 360 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote360 | 0.061149600 | 1497 | 1 | completa | Total; eventos.jsonl línea 361 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote361 | 0.057969700 | 1497 | 1 | completa | Total; eventos.jsonl línea 362 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote362 | 0.056361600 | 1497 | 1 | completa | Total; eventos.jsonl línea 363 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote363 | 0.057626900 | 1497 | 1 | completa | Total; eventos.jsonl línea 364 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote364 | 0.059648500 | 1497 | 1 | completa | Total; eventos.jsonl línea 365 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote365 | 0.058943300 | 1497 | 1 | completa | Total; eventos.jsonl línea 366 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote366 | 0.059872700 | 1497 | 1 | completa | Total; eventos.jsonl línea 367 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote367 | 0.060216800 | 1497 | 1 | completa | Total; eventos.jsonl línea 368 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote368 | 0.060486600 | 1497 | 1 | completa | Total; eventos.jsonl línea 369 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote369 | 0.060689600 | 1497 | 1 | completa | Total; eventos.jsonl línea 370 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote370 | 0.059695800 | 1497 | 1 | completa | Total; eventos.jsonl línea 371 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote371 | 0.063640300 | 1497 | 1 | completa | Total; eventos.jsonl línea 372 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote372 | 0.062502000 | 1497 | 1 | completa | Total; eventos.jsonl línea 373 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote373 | 0.063078200 | 1497 | 1 | completa | Total; eventos.jsonl línea 374 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote374 | 0.059313100 | 1497 | 1 | completa | Total; eventos.jsonl línea 375 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote375 | 0.060011700 | 1497 | 1 | completa | Total; eventos.jsonl línea 376 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote376 | 0.059584300 | 1497 | 1 | completa | Total; eventos.jsonl línea 377 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote377 | 0.058986800 | 1497 | 1 | completa | Total; eventos.jsonl línea 378 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote378 | 0.057499900 | 1497 | 1 | completa | Total; eventos.jsonl línea 379 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote379 | 0.064018800 | 1497 | 1 | completa | Total; eventos.jsonl línea 380 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote380 | 0.072053800 | 1497 | 1 | completa | Total; eventos.jsonl línea 381 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote381 | 0.070003700 | 1497 | 1 | completa | Total; eventos.jsonl línea 382 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote382 | 0.079736400 | 1497 | 1 | completa | Total; eventos.jsonl línea 383 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote383 | 0.079383200 | 1497 | 1 | completa | Total; eventos.jsonl línea 384 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote384 | 0.078385800 | 1497 | 1 | completa | Total; eventos.jsonl línea 385 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote385 | 0.060226100 | 1497 | 1 | completa | Total; eventos.jsonl línea 386 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote386 | 0.063043200 | 1497 | 1 | completa | Total; eventos.jsonl línea 387 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote387 | 0.058353200 | 1497 | 1 | completa | Total; eventos.jsonl línea 388 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote388 | 0.057830300 | 1497 | 1 | completa | Total; eventos.jsonl línea 389 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote389 | 0.058153300 | 1497 | 1 | completa | Total; eventos.jsonl línea 390 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote390 | 0.058082600 | 1497 | 1 | completa | Total; eventos.jsonl línea 391 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote391 | 0.056507300 | 1497 | 1 | completa | Total; eventos.jsonl línea 392 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote392 | 0.065077600 | 1497 | 1 | completa | Total; eventos.jsonl línea 393 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote393 | 0.058623200 | 1497 | 1 | completa | Total; eventos.jsonl línea 394 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote394 | 0.062155700 | 1497 | 1 | completa | Total; eventos.jsonl línea 395 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote395 | 0.060909600 | 1497 | 1 | completa | Total; eventos.jsonl línea 396 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote396 | 0.062796300 | 1497 | 1 | completa | Total; eventos.jsonl línea 397 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote397 | 0.062156000 | 1497 | 1 | completa | Total; eventos.jsonl línea 398 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote398 | 0.064276900 | 1497 | 1 | completa | Total; eventos.jsonl línea 399 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote399 | 0.060204400 | 1497 | 1 | completa | Total; eventos.jsonl línea 400 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote400 | 0.060485300 | 1497 | 1 | completa | Total; eventos.jsonl línea 401 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote401 | 0.063510300 | 1497 | 1 | completa | Total; eventos.jsonl línea 402 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote402 | 0.060197300 | 1497 | 1 | completa | Total; eventos.jsonl línea 403 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote403 | 0.059703300 | 1497 | 1 | completa | Total; eventos.jsonl línea 404 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote404 | 0.057016500 | 1497 | 1 | completa | Total; eventos.jsonl línea 405 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote405 | 0.057383200 | 1497 | 1 | completa | Total; eventos.jsonl línea 406 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote406 | 0.060048600 | 1497 | 1 | completa | Total; eventos.jsonl línea 407 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote407 | 0.058763500 | 1497 | 1 | completa | Total; eventos.jsonl línea 408 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote408 | 0.062824100 | 1497 | 1 | completa | Total; eventos.jsonl línea 409 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote409 | 0.061109300 | 1497 | 1 | completa | Total; eventos.jsonl línea 410 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote410 | 0.058776300 | 1497 | 1 | completa | Total; eventos.jsonl línea 411 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote411 | 0.059593600 | 1497 | 1 | completa | Total; eventos.jsonl línea 412 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote412 | 0.061871000 | 1497 | 1 | completa | Total; eventos.jsonl línea 413 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote413 | 0.061635900 | 1497 | 1 | completa | Total; eventos.jsonl línea 414 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote414 | 0.069350300 | 1497 | 1 | completa | Total; eventos.jsonl línea 415 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote415 | 0.062518000 | 1497 | 1 | completa | Total; eventos.jsonl línea 416 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote416 | 0.059187400 | 1497 | 1 | completa | Total; eventos.jsonl línea 417 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote417 | 0.056453700 | 1497 | 1 | completa | Total; eventos.jsonl línea 418 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote418 | 0.060931300 | 1497 | 1 | completa | Total; eventos.jsonl línea 419 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote419 | 0.060262300 | 1497 | 1 | completa | Total; eventos.jsonl línea 420 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote420 | 0.056693800 | 1497 | 1 | completa | Total; eventos.jsonl línea 421 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote421 | 0.060958600 | 1497 | 1 | completa | Total; eventos.jsonl línea 422 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote422 | 0.059020100 | 1497 | 1 | completa | Total; eventos.jsonl línea 423 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote423 | 0.061336900 | 1497 | 1 | completa | Total; eventos.jsonl línea 424 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote424 | 0.059350200 | 1497 | 1 | completa | Total; eventos.jsonl línea 425 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote425 | 0.058687400 | 1497 | 1 | completa | Total; eventos.jsonl línea 426 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote426 | 0.061762000 | 1497 | 1 | completa | Total; eventos.jsonl línea 427 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote427 | 0.059914700 | 1497 | 1 | completa | Total; eventos.jsonl línea 428 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote428 | 0.060562900 | 1497 | 1 | completa | Total; eventos.jsonl línea 429 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote429 | 0.059361400 | 1497 | 1 | completa | Total; eventos.jsonl línea 430 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote430 | 0.061074000 | 1497 | 1 | completa | Total; eventos.jsonl línea 431 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote431 | 0.062991500 | 1497 | 1 | completa | Total; eventos.jsonl línea 432 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote432 | 0.059929300 | 1497 | 1 | completa | Total; eventos.jsonl línea 433 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote433 | 0.062397300 | 1497 | 1 | completa | Total; eventos.jsonl línea 434 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote434 | 0.061850100 | 1497 | 1 | completa | Total; eventos.jsonl línea 435 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote435 | 0.069536500 | 1497 | 1 | completa | Total; eventos.jsonl línea 436 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote436 | 0.060757200 | 1497 | 1 | completa | Total; eventos.jsonl línea 437 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote437 | 0.058356000 | 1497 | 1 | completa | Total; eventos.jsonl línea 438 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote438 | 0.062226200 | 1497 | 1 | completa | Total; eventos.jsonl línea 439 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote439 | 0.058878100 | 1497 | 1 | completa | Total; eventos.jsonl línea 440 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote440 | 0.062548500 | 1497 | 1 | completa | Total; eventos.jsonl línea 441 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote441 | 0.063272800 | 1497 | 1 | completa | Total; eventos.jsonl línea 442 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote442 | 0.062805200 | 1497 | 1 | completa | Total; eventos.jsonl línea 443 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote443 | 0.060904000 | 1497 | 1 | completa | Total; eventos.jsonl línea 444 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote444 | 0.061205900 | 1497 | 1 | completa | Total; eventos.jsonl línea 445 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote445 | 0.064116700 | 1497 | 1 | completa | Total; eventos.jsonl línea 446 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote446 | 0.065952600 | 1497 | 1 | completa | Total; eventos.jsonl línea 447 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote447 | 0.062990000 | 1497 | 1 | completa | Total; eventos.jsonl línea 448 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote448 | 0.060254500 | 1497 | 1 | completa | Total; eventos.jsonl línea 449 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote449 | 0.062479400 | 1497 | 1 | completa | Total; eventos.jsonl línea 450 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote450 | 0.061749400 | 1497 | 1 | completa | Total; eventos.jsonl línea 451 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote451 | 0.063547000 | 1497 | 1 | completa | Total; eventos.jsonl línea 452 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote452 | 0.057233600 | 1497 | 1 | completa | Total; eventos.jsonl línea 453 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote453 | 0.057788000 | 1497 | 1 | completa | Total; eventos.jsonl línea 454 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote454 | 0.055594800 | 1497 | 1 | completa | Total; eventos.jsonl línea 455 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote455 | 0.059568100 | 1497 | 1 | completa | Total; eventos.jsonl línea 456 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote456 | 0.057190000 | 1497 | 1 | completa | Total; eventos.jsonl línea 457 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote457 | 0.058985400 | 1497 | 1 | completa | Total; eventos.jsonl línea 458 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote458 | 0.058332300 | 1497 | 1 | completa | Total; eventos.jsonl línea 459 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote459 | 0.061226100 | 1497 | 1 | completa | Total; eventos.jsonl línea 460 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote460 | 0.062536800 | 1497 | 1 | completa | Total; eventos.jsonl línea 461 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote461 | 0.063451700 | 1497 | 1 | completa | Total; eventos.jsonl línea 462 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote462 | 0.060009000 | 1497 | 1 | completa | Total; eventos.jsonl línea 463 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote463 | 0.065147900 | 1497 | 1 | completa | Total; eventos.jsonl línea 464 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote464 | 0.062805700 | 1497 | 1 | completa | Total; eventos.jsonl línea 465 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote465 | 0.059802300 | 1497 | 1 | completa | Total; eventos.jsonl línea 466 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote466 | 0.061231100 | 1497 | 1 | completa | Total; eventos.jsonl línea 467 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote467 | 0.062377600 | 1497 | 1 | completa | Total; eventos.jsonl línea 468 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote468 | 0.060717600 | 1497 | 1 | completa | Total; eventos.jsonl línea 469 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote469 | 0.060517800 | 1497 | 1 | completa | Total; eventos.jsonl línea 470 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote470 | 0.061958700 | 1497 | 1 | completa | Total; eventos.jsonl línea 471 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote471 | 0.061065700 | 1497 | 1 | completa | Total; eventos.jsonl línea 472 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote472 | 0.060642400 | 1497 | 1 | completa | Total; eventos.jsonl línea 473 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote473 | 0.069458300 | 1497 | 1 | completa | Total; eventos.jsonl línea 474 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote474 | 0.057332300 | 1497 | 1 | completa | Total; eventos.jsonl línea 475 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote475 | 0.057552200 | 1497 | 1 | completa | Total; eventos.jsonl línea 476 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote476 | 0.058280200 | 1497 | 1 | completa | Total; eventos.jsonl línea 477 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote477 | 0.057527600 | 1497 | 1 | completa | Total; eventos.jsonl línea 478 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote478 | 0.057251700 | 1497 | 1 | completa | Total; eventos.jsonl línea 479 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote479 | 0.063113100 | 1497 | 1 | completa | Total; eventos.jsonl línea 480 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote480 | 0.062388300 | 1497 | 1 | completa | Total; eventos.jsonl línea 481 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote481 | 0.063118900 | 1497 | 1 | completa | Total; eventos.jsonl línea 482 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote482 | 0.061396600 | 1497 | 1 | completa | Total; eventos.jsonl línea 483 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote483 | 0.059760400 | 1497 | 1 | completa | Total; eventos.jsonl línea 484 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote484 | 0.063208000 | 1497 | 1 | completa | Total; eventos.jsonl línea 485 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote485 | 0.057226100 | 1497 | 1 | completa | Total; eventos.jsonl línea 486 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote486 | 0.057591500 | 1497 | 1 | completa | Total; eventos.jsonl línea 487 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote487 | 0.058283100 | 1497 | 1 | completa | Total; eventos.jsonl línea 488 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote488 | 0.058477300 | 1497 | 1 | completa | Total; eventos.jsonl línea 489 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote489 | 0.057875500 | 1497 | 1 | completa | Total; eventos.jsonl línea 490 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote490 | 0.062323600 | 1497 | 1 | completa | Total; eventos.jsonl línea 491 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote491 | 0.063056200 | 1497 | 1 | completa | Total; eventos.jsonl línea 492 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote492 | 0.065109200 | 1497 | 1 | completa | Total; eventos.jsonl línea 493 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote493 | 0.057839800 | 1497 | 1 | completa | Total; eventos.jsonl línea 494 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote494 | 0.057122300 | 1497 | 1 | completa | Total; eventos.jsonl línea 495 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote495 | 0.055561000 | 1497 | 1 | completa | Total; eventos.jsonl línea 496 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote496 | 0.058862700 | 1497 | 1 | completa | Total; eventos.jsonl línea 497 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote497 | 0.059837500 | 1497 | 1 | completa | Total; eventos.jsonl línea 498 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote498 | 0.062844300 | 1497 | 1 | completa | Total; eventos.jsonl línea 499 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote499 | 0.059666200 | 1497 | 1 | completa | Total; eventos.jsonl línea 500 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote500 | 0.068419100 | 1497 | 1 | completa | Total; eventos.jsonl línea 501 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote501 | 0.060989400 | 1497 | 1 | completa | Total; eventos.jsonl línea 502 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote502 | 0.059580300 | 1497 | 1 | completa | Total; eventos.jsonl línea 503 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote503 | 0.059690700 | 1497 | 1 | completa | Total; eventos.jsonl línea 504 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote504 | 0.059393300 | 1497 | 1 | completa | Total; eventos.jsonl línea 505 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote505 | 0.061203900 | 1497 | 1 | completa | Total; eventos.jsonl línea 506 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote506 | 0.056460300 | 1497 | 1 | completa | Total; eventos.jsonl línea 507 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote507 | 0.057825200 | 1497 | 1 | completa | Total; eventos.jsonl línea 508 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote508 | 0.057775400 | 1497 | 1 | completa | Total; eventos.jsonl línea 509 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote509 | 0.060215000 | 1497 | 1 | completa | Total; eventos.jsonl línea 510 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote510 | 0.058874800 | 1497 | 1 | completa | Total; eventos.jsonl línea 511 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote511 | 0.057943500 | 1497 | 1 | completa | Total; eventos.jsonl línea 512 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote512 | 0.065157900 | 1497 | 1 | completa | Total; eventos.jsonl línea 513 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote513 | 0.058792000 | 1497 | 1 | completa | Total; eventos.jsonl línea 514 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote514 | 0.059927300 | 1497 | 1 | completa | Total; eventos.jsonl línea 515 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote515 | 0.057492900 | 1497 | 1 | completa | Total; eventos.jsonl línea 516 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote516 | 0.058294300 | 1497 | 1 | completa | Total; eventos.jsonl línea 517 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote517 | 0.057972300 | 1497 | 1 | completa | Total; eventos.jsonl línea 518 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote518 | 0.056375700 | 1497 | 1 | completa | Total; eventos.jsonl línea 519 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote519 | 0.059500100 | 1497 | 1 | completa | Total; eventos.jsonl línea 520 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote520 | 0.058792500 | 1497 | 1 | completa | Total; eventos.jsonl línea 521 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote521 | 0.061201700 | 1497 | 1 | completa | Total; eventos.jsonl línea 522 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote522 | 0.063445600 | 1497 | 1 | completa | Total; eventos.jsonl línea 523 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote523 | 0.060479500 | 1497 | 1 | completa | Total; eventos.jsonl línea 524 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote524 | 0.060854900 | 1497 | 1 | completa | Total; eventos.jsonl línea 525 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote525 | 0.060775400 | 1497 | 1 | completa | Total; eventos.jsonl línea 526 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote526 | 0.061436900 | 1497 | 1 | completa | Total; eventos.jsonl línea 527 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote527 | 0.061578500 | 1497 | 1 | completa | Total; eventos.jsonl línea 528 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote528 | 0.062653100 | 1497 | 1 | completa | Total; eventos.jsonl línea 529 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote529 | 0.063531000 | 1497 | 1 | completa | Total; eventos.jsonl línea 530 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote530 | 0.063544600 | 1497 | 1 | completa | Total; eventos.jsonl línea 531 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote531 | 0.060304800 | 1497 | 1 | completa | Total; eventos.jsonl línea 532 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote532 | 0.059682100 | 1497 | 1 | completa | Total; eventos.jsonl línea 533 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote533 | 0.064515500 | 1497 | 1 | completa | Total; eventos.jsonl línea 534 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote534 | 0.061523100 | 1497 | 1 | completa | Total; eventos.jsonl línea 535 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote535 | 0.059702000 | 1497 | 1 | completa | Total; eventos.jsonl línea 536 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote536 | 0.059077100 | 1497 | 1 | completa | Total; eventos.jsonl línea 537 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote537 | 0.060991300 | 1497 | 1 | completa | Total; eventos.jsonl línea 538 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote538 | 0.060767200 | 1497 | 1 | completa | Total; eventos.jsonl línea 539 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote539 | 0.060529500 | 1497 | 1 | completa | Total; eventos.jsonl línea 540 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote540 | 0.059156300 | 1497 | 1 | completa | Total; eventos.jsonl línea 541 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote541 | 0.059267900 | 1497 | 1 | completa | Total; eventos.jsonl línea 542 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote542 | 0.062476000 | 1497 | 1 | completa | Total; eventos.jsonl línea 543 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote543 | 0.059686600 | 1497 | 1 | completa | Total; eventos.jsonl línea 544 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote544 | 0.061044100 | 1497 | 1 | completa | Total; eventos.jsonl línea 545 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote545 | 0.058915500 | 1497 | 1 | completa | Total; eventos.jsonl línea 546 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote546 | 0.060442900 | 1497 | 1 | completa | Total; eventos.jsonl línea 547 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote547 | 0.059592500 | 1497 | 1 | completa | Total; eventos.jsonl línea 548 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote548 | 0.066099000 | 1497 | 1 | completa | Total; eventos.jsonl línea 549 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote549 | 0.060075300 | 1497 | 1 | completa | Total; eventos.jsonl línea 550 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote550 | 0.062912400 | 1497 | 1 | completa | Total; eventos.jsonl línea 551 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote551 | 0.058264600 | 1497 | 1 | completa | Total; eventos.jsonl línea 552 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote552 | 0.057168500 | 1497 | 1 | completa | Total; eventos.jsonl línea 553 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote553 | 0.057131800 | 1497 | 1 | completa | Total; eventos.jsonl línea 554 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote554 | 0.056146700 | 1497 | 1 | completa | Total; eventos.jsonl línea 555 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote555 | 0.056547800 | 1497 | 1 | completa | Total; eventos.jsonl línea 556 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote556 | 0.066068100 | 1497 | 1 | completa | Total; eventos.jsonl línea 557 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote557 | 0.059870600 | 1497 | 1 | completa | Total; eventos.jsonl línea 558 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote558 | 0.059678400 | 1497 | 1 | completa | Total; eventos.jsonl línea 559 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote559 | 0.062951600 | 1497 | 1 | completa | Total; eventos.jsonl línea 560 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote560 | 0.062068500 | 1497 | 1 | completa | Total; eventos.jsonl línea 561 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote561 | 0.066592400 | 1497 | 1 | completa | Total; eventos.jsonl línea 562 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote562 | 0.064136800 | 1497 | 1 | completa | Total; eventos.jsonl línea 563 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote563 | 0.059984900 | 1497 | 1 | completa | Total; eventos.jsonl línea 564 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote564 | 0.059778300 | 1497 | 1 | completa | Total; eventos.jsonl línea 565 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote565 | 0.059424500 | 1497 | 1 | completa | Total; eventos.jsonl línea 566 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote566 | 0.060308600 | 1497 | 1 | completa | Total; eventos.jsonl línea 567 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote567 | 0.061565600 | 1497 | 1 | completa | Total; eventos.jsonl línea 568 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote568 | 0.066273800 | 1497 | 1 | completa | Total; eventos.jsonl línea 569 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote569 | 0.062495600 | 1497 | 1 | completa | Total; eventos.jsonl línea 570 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote570 | 0.060419300 | 1497 | 1 | completa | Total; eventos.jsonl línea 571 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote571 | 0.065553000 | 1497 | 1 | completa | Total; eventos.jsonl línea 572 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote572 | 0.059288400 | 1497 | 1 | completa | Total; eventos.jsonl línea 573 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote573 | 0.066481500 | 1497 | 1 | completa | Total; eventos.jsonl línea 574 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote574 | 0.063330900 | 1497 | 1 | completa | Total; eventos.jsonl línea 575 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote575 | 0.062009600 | 1497 | 1 | completa | Total; eventos.jsonl línea 576 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote576 | 0.060487400 | 1497 | 1 | completa | Total; eventos.jsonl línea 577 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote577 | 0.059047400 | 1497 | 1 | completa | Total; eventos.jsonl línea 578 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote578 | 0.060058300 | 1497 | 1 | completa | Total; eventos.jsonl línea 579 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote579 | 0.055847300 | 1497 | 1 | completa | Total; eventos.jsonl línea 580 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote580 | 0.055714300 | 1497 | 1 | completa | Total; eventos.jsonl línea 581 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote581 | 0.064457900 | 1497 | 1 | completa | Total; eventos.jsonl línea 582 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote582 | 0.060975800 | 1497 | 1 | completa | Total; eventos.jsonl línea 583 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote583 | 0.062314900 | 1497 | 1 | completa | Total; eventos.jsonl línea 584 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote584 | 0.060265400 | 1497 | 1 | completa | Total; eventos.jsonl línea 585 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote585 | 0.059454200 | 1497 | 1 | completa | Total; eventos.jsonl línea 586 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote586 | 0.057873200 | 1497 | 1 | completa | Total; eventos.jsonl línea 587 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote587 | 0.059863300 | 1497 | 1 | completa | Total; eventos.jsonl línea 588 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote588 | 0.059077200 | 1497 | 1 | completa | Total; eventos.jsonl línea 589 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote589 | 0.056958900 | 1497 | 1 | completa | Total; eventos.jsonl línea 590 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote590 | 0.058166500 | 1497 | 1 | completa | Total; eventos.jsonl línea 591 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote591 | 0.059432200 | 1497 | 1 | completa | Total; eventos.jsonl línea 592 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote592 | 0.062383000 | 1497 | 1 | completa | Total; eventos.jsonl línea 593 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote593 | 0.059295000 | 1497 | 1 | completa | Total; eventos.jsonl línea 594 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote594 | 0.060792800 | 1497 | 1 | completa | Total; eventos.jsonl línea 595 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote595 | 0.057039600 | 1497 | 1 | completa | Total; eventos.jsonl línea 596 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote596 | 0.058407500 | 1497 | 1 | completa | Total; eventos.jsonl línea 597 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote597 | 0.061733000 | 1497 | 1 | completa | Total; eventos.jsonl línea 598 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote598 | 0.062237200 | 1497 | 1 | completa | Total; eventos.jsonl línea 599 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote599 | 0.060188100 | 1497 | 1 | completa | Total; eventos.jsonl línea 600 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote600 | 0.060473900 | 1497 | 1 | completa | Total; eventos.jsonl línea 601 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote601 | 0.061893400 | 1497 | 1 | completa | Total; eventos.jsonl línea 602 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote602 | 0.063638100 | 1497 | 1 | completa | Total; eventos.jsonl línea 603 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote603 | 0.060054900 | 1497 | 1 | completa | Total; eventos.jsonl línea 604 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote604 | 0.060644300 | 1497 | 1 | completa | Total; eventos.jsonl línea 605 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote605 | 0.059455100 | 1497 | 1 | completa | Total; eventos.jsonl línea 606 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote606 | 0.058390600 | 1497 | 1 | completa | Total; eventos.jsonl línea 607 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote607 | 0.061663300 | 1497 | 1 | completa | Total; eventos.jsonl línea 608 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote608 | 0.062593300 | 1497 | 1 | completa | Total; eventos.jsonl línea 609 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote609 | 0.061423400 | 1497 | 1 | completa | Total; eventos.jsonl línea 610 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote610 | 0.059376300 | 1497 | 1 | completa | Total; eventos.jsonl línea 611 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote611 | 0.059143700 | 1497 | 1 | completa | Total; eventos.jsonl línea 612 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote612 | 0.056521300 | 1497 | 1 | completa | Total; eventos.jsonl línea 613 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote613 | 0.060142700 | 1497 | 1 | completa | Total; eventos.jsonl línea 614 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote614 | 0.059685500 | 1497 | 1 | completa | Total; eventos.jsonl línea 615 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote615 | 0.060506000 | 1497 | 1 | completa | Total; eventos.jsonl línea 616 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote616 | 0.069357200 | 1497 | 1 | completa | Total; eventos.jsonl línea 617 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote617 | 0.060608000 | 1497 | 1 | completa | Total; eventos.jsonl línea 618 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote618 | 0.061497800 | 1497 | 1 | completa | Total; eventos.jsonl línea 619 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote619 | 0.061297900 | 1497 | 1 | completa | Total; eventos.jsonl línea 620 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote620 | 0.061583200 | 1497 | 1 | completa | Total; eventos.jsonl línea 621 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote621 | 0.061104800 | 1497 | 1 | completa | Total; eventos.jsonl línea 622 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote622 | 0.058761800 | 1497 | 1 | completa | Total; eventos.jsonl línea 623 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote623 | 0.062004200 | 1497 | 1 | completa | Total; eventos.jsonl línea 624 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote624 | 0.060449300 | 1497 | 1 | completa | Total; eventos.jsonl línea 625 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote625 | 0.059204600 | 1497 | 1 | completa | Total; eventos.jsonl línea 626 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote626 | 0.063187500 | 1497 | 1 | completa | Total; eventos.jsonl línea 627 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote627 | 0.061251100 | 1497 | 1 | completa | Total; eventos.jsonl línea 628 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote628 | 0.060898400 | 1497 | 1 | completa | Total; eventos.jsonl línea 629 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote629 | 0.057003000 | 1497 | 1 | completa | Total; eventos.jsonl línea 630 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote630 | 0.063073000 | 1497 | 1 | completa | Total; eventos.jsonl línea 631 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote631 | 0.060849800 | 1497 | 1 | completa | Total; eventos.jsonl línea 632 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote632 | 0.065436800 | 1497 | 1 | completa | Total; eventos.jsonl línea 633 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote633 | 0.059481400 | 1497 | 1 | completa | Total; eventos.jsonl línea 634 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote634 | 0.058349700 | 1497 | 1 | completa | Total; eventos.jsonl línea 635 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote635 | 0.057688300 | 1497 | 1 | completa | Total; eventos.jsonl línea 636 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote636 | 0.059677300 | 1497 | 1 | completa | Total; eventos.jsonl línea 637 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote637 | 0.059525700 | 1497 | 1 | completa | Total; eventos.jsonl línea 638 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote638 | 0.063264500 | 1497 | 1 | completa | Total; eventos.jsonl línea 639 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote639 | 0.061464500 | 1497 | 1 | completa | Total; eventos.jsonl línea 640 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote640 | 0.062370300 | 1497 | 1 | completa | Total; eventos.jsonl línea 641 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote641 | 0.060666700 | 1497 | 1 | completa | Total; eventos.jsonl línea 642 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote642 | 0.064523600 | 1497 | 1 | completa | Total; eventos.jsonl línea 643 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote643 | 0.060724200 | 1497 | 1 | completa | Total; eventos.jsonl línea 644 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote644 | 0.057178700 | 1497 | 1 | completa | Total; eventos.jsonl línea 645 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote645 | 0.063893400 | 1497 | 1 | completa | Total; eventos.jsonl línea 646 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote646 | 0.067234100 | 1497 | 1 | completa | Total; eventos.jsonl línea 647 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote647 | 0.062641500 | 1497 | 1 | completa | Total; eventos.jsonl línea 648 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote648 | 0.058500100 | 1497 | 1 | completa | Total; eventos.jsonl línea 649 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote649 | 0.057787900 | 1497 | 1 | completa | Total; eventos.jsonl línea 650 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote650 | 0.059851700 | 1497 | 1 | completa | Total; eventos.jsonl línea 651 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote651 | 0.056602300 | 1497 | 1 | completa | Total; eventos.jsonl línea 652 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote652 | 0.062184400 | 1497 | 1 | completa | Total; eventos.jsonl línea 653 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote653 | 0.058937300 | 1497 | 1 | completa | Total; eventos.jsonl línea 654 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote654 | 0.060841300 | 1497 | 1 | completa | Total; eventos.jsonl línea 655 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote655 | 0.061916700 | 1497 | 1 | completa | Total; eventos.jsonl línea 656 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote656 | 0.060454000 | 1497 | 1 | completa | Total; eventos.jsonl línea 657 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote657 | 0.061232800 | 1497 | 1 | completa | Total; eventos.jsonl línea 658 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote658 | 0.063215100 | 1497 | 1 | completa | Total; eventos.jsonl línea 659 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote659 | 0.064200700 | 1497 | 1 | completa | Total; eventos.jsonl línea 660 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote660 | 0.066328900 | 1497 | 1 | completa | Total; eventos.jsonl línea 661 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote661 | 0.062420000 | 1497 | 1 | completa | Total; eventos.jsonl línea 662 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote662 | 0.060890600 | 1497 | 1 | completa | Total; eventos.jsonl línea 663 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote663 | 0.061088900 | 1497 | 1 | completa | Total; eventos.jsonl línea 664 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote664 | 0.061845300 | 1497 | 1 | completa | Total; eventos.jsonl línea 665 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote665 | 0.063314700 | 1497 | 1 | completa | Total; eventos.jsonl línea 666 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote666 | 0.061031100 | 1497 | 1 | completa | Total; eventos.jsonl línea 667 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote667 | 0.063775500 | 1497 | 1 | completa | Total; eventos.jsonl línea 668 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote668 | 0.063971100 | 1497 | 1 | completa | Total; eventos.jsonl línea 669 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote669 | 0.059225400 | 1497 | 1 | completa | Total; eventos.jsonl línea 670 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote670 | 0.057681300 | 1497 | 1 | completa | Total; eventos.jsonl línea 671 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote671 | 0.059370700 | 1497 | 1 | completa | Total; eventos.jsonl línea 672 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote672 | 0.058765000 | 1497 | 1 | completa | Total; eventos.jsonl línea 673 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote673 | 0.064606100 | 1497 | 1 | completa | Total; eventos.jsonl línea 674 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote674 | 0.063442900 | 1497 | 1 | completa | Total; eventos.jsonl línea 675 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote675 | 0.057685900 | 1497 | 1 | completa | Total; eventos.jsonl línea 676 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote676 | 0.063896500 | 1497 | 1 | completa | Total; eventos.jsonl línea 677 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote677 | 0.056878800 | 1497 | 1 | completa | Total; eventos.jsonl línea 678 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote678 | 0.058376600 | 1497 | 1 | completa | Total; eventos.jsonl línea 679 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote679 | 0.060867800 | 1497 | 1 | completa | Total; eventos.jsonl línea 680 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote680 | 0.056204100 | 1497 | 1 | completa | Total; eventos.jsonl línea 681 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote681 | 0.056882900 | 1497 | 1 | completa | Total; eventos.jsonl línea 682 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote682 | 0.057202600 | 1497 | 1 | completa | Total; eventos.jsonl línea 683 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote683 | 0.057717600 | 1497 | 1 | completa | Total; eventos.jsonl línea 684 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote684 | 0.061932400 | 1497 | 1 | completa | Total; eventos.jsonl línea 685 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote685 | 0.061424000 | 1497 | 1 | completa | Total; eventos.jsonl línea 686 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote686 | 0.060171200 | 1497 | 1 | completa | Total; eventos.jsonl línea 687 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote687 | 0.062772600 | 1497 | 1 | completa | Total; eventos.jsonl línea 688 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote688 | 0.059873800 | 1497 | 1 | completa | Total; eventos.jsonl línea 689 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote689 | 0.059833500 | 1497 | 1 | completa | Total; eventos.jsonl línea 690 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote690 | 0.061056900 | 1497 | 1 | completa | Total; eventos.jsonl línea 691 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote691 | 0.061121600 | 1497 | 1 | completa | Total; eventos.jsonl línea 692 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote692 | 0.062209700 | 1497 | 1 | completa | Total; eventos.jsonl línea 693 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote693 | 0.058870100 | 1497 | 1 | completa | Total; eventos.jsonl línea 694 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote694 | 0.061064000 | 1497 | 1 | completa | Total; eventos.jsonl línea 695 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote695 | 0.070280600 | 1497 | 1 | completa | Total; eventos.jsonl línea 696 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote696 | 0.062605300 | 1497 | 1 | completa | Total; eventos.jsonl línea 697 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote697 | 0.059262600 | 1497 | 1 | completa | Total; eventos.jsonl línea 698 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote698 | 0.060385000 | 1497 | 1 | completa | Total; eventos.jsonl línea 699 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote699 | 0.059965200 | 1497 | 1 | completa | Total; eventos.jsonl línea 700 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote700 | 0.065351100 | 1497 | 1 | completa | Total; eventos.jsonl línea 701 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote701 | 0.061452500 | 1497 | 1 | completa | Total; eventos.jsonl línea 702 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote702 | 0.061321700 | 1497 | 1 | completa | Total; eventos.jsonl línea 703 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote703 | 0.063693600 | 1497 | 1 | completa | Total; eventos.jsonl línea 704 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote704 | 0.059510600 | 1497 | 1 | completa | Total; eventos.jsonl línea 705 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote705 | 0.066805100 | 1497 | 1 | completa | Total; eventos.jsonl línea 706 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote706 | 0.063111100 | 1497 | 1 | completa | Total; eventos.jsonl línea 707 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote707 | 0.068097000 | 1497 | 1 | completa | Total; eventos.jsonl línea 708 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote708 | 0.069115200 | 1497 | 1 | completa | Total; eventos.jsonl línea 709 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote709 | 0.055785600 | 1497 | 1 | completa | Total; eventos.jsonl línea 710 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote710 | 0.060988700 | 1497 | 1 | completa | Total; eventos.jsonl línea 711 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote711 | 0.058915700 | 1497 | 1 | completa | Total; eventos.jsonl línea 712 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote712 | 0.056690400 | 1497 | 1 | completa | Total; eventos.jsonl línea 713 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote713 | 0.059751400 | 1497 | 1 | completa | Total; eventos.jsonl línea 714 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote714 | 0.059576300 | 1497 | 1 | completa | Total; eventos.jsonl línea 715 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote715 | 0.060820400 | 1497 | 1 | completa | Total; eventos.jsonl línea 716 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote716 | 0.058309800 | 1497 | 1 | completa | Total; eventos.jsonl línea 717 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote717 | 0.060735100 | 1497 | 1 | completa | Total; eventos.jsonl línea 718 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote718 | 0.059585800 | 1497 | 1 | completa | Total; eventos.jsonl línea 719 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote719 | 0.060867300 | 1497 | 1 | completa | Total; eventos.jsonl línea 720 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote720 | 0.060720000 | 1497 | 1 | completa | Total; eventos.jsonl línea 721 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote721 | 0.063226800 | 1497 | 1 | completa | Total; eventos.jsonl línea 722 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote722 | 0.058688300 | 1497 | 1 | completa | Total; eventos.jsonl línea 723 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote723 | 0.063419400 | 1497 | 1 | completa | Total; eventos.jsonl línea 724 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote724 | 0.058025200 | 1497 | 1 | completa | Total; eventos.jsonl línea 725 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote725 | 0.059842900 | 1497 | 1 | completa | Total; eventos.jsonl línea 726 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote726 | 0.058390600 | 1497 | 1 | completa | Total; eventos.jsonl línea 727 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote727 | 0.057295200 | 1497 | 1 | completa | Total; eventos.jsonl línea 728 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote728 | 0.056950800 | 1497 | 1 | completa | Total; eventos.jsonl línea 729 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote729 | 0.059613100 | 1497 | 1 | completa | Total; eventos.jsonl línea 730 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote730 | 0.061904100 | 1497 | 1 | completa | Total; eventos.jsonl línea 731 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote731 | 0.059350300 | 1497 | 1 | completa | Total; eventos.jsonl línea 732 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote732 | 0.059438900 | 1497 | 1 | completa | Total; eventos.jsonl línea 733 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote733 | 0.063458100 | 1497 | 1 | completa | Total; eventos.jsonl línea 734 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote734 | 0.057524500 | 1497 | 1 | completa | Total; eventos.jsonl línea 735 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote735 | 0.059100900 | 1497 | 1 | completa | Total; eventos.jsonl línea 736 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote736 | 0.061230700 | 1497 | 1 | completa | Total; eventos.jsonl línea 737 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote737 | 0.057467000 | 1497 | 1 | completa | Total; eventos.jsonl línea 738 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote738 | 0.061377300 | 1497 | 1 | completa | Total; eventos.jsonl línea 739 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote739 | 0.058180100 | 1497 | 1 | completa | Total; eventos.jsonl línea 740 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote740 | 0.060819700 | 1497 | 1 | completa | Total; eventos.jsonl línea 741 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote741 | 0.058525500 | 1497 | 1 | completa | Total; eventos.jsonl línea 742 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote742 | 0.056987300 | 1497 | 1 | completa | Total; eventos.jsonl línea 743 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote743 | 0.060034700 | 1497 | 1 | completa | Total; eventos.jsonl línea 744 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote744 | 0.059563900 | 1497 | 1 | completa | Total; eventos.jsonl línea 745 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote745 | 0.058344400 | 1497 | 1 | completa | Total; eventos.jsonl línea 746 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote746 | 0.058461700 | 1497 | 1 | completa | Total; eventos.jsonl línea 747 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote747 | 0.060743900 | 1497 | 1 | completa | Total; eventos.jsonl línea 748 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote748 | 0.062937000 | 1497 | 1 | completa | Total; eventos.jsonl línea 749 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote749 | 0.064185200 | 1497 | 1 | completa | Total; eventos.jsonl línea 750 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote750 | 0.063764500 | 1497 | 1 | completa | Total; eventos.jsonl línea 751 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote751 | 0.060520900 | 1497 | 1 | completa | Total; eventos.jsonl línea 752 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote752 | 0.062519100 | 1497 | 1 | completa | Total; eventos.jsonl línea 753 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote753 | 0.061893100 | 1497 | 1 | completa | Total; eventos.jsonl línea 754 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote754 | 0.063527300 | 1497 | 1 | completa | Total; eventos.jsonl línea 755 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote755 | 0.061274300 | 1497 | 1 | completa | Total; eventos.jsonl línea 756 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote756 | 0.065103400 | 1497 | 1 | completa | Total; eventos.jsonl línea 757 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote757 | 0.073740500 | 1497 | 1 | completa | Total; eventos.jsonl línea 758 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote758 | 0.072017200 | 1497 | 1 | completa | Total; eventos.jsonl línea 759 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote759 | 0.065049600 | 1497 | 1 | completa | Total; eventos.jsonl línea 760 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote760 | 0.069952700 | 1497 | 1 | completa | Total; eventos.jsonl línea 761 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote761 | 0.066425600 | 1497 | 1 | completa | Total; eventos.jsonl línea 762 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote762 | 0.062635800 | 1497 | 1 | completa | Total; eventos.jsonl línea 763 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote763 | 0.063199800 | 1497 | 1 | completa | Total; eventos.jsonl línea 764 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote764 | 0.066768200 | 1497 | 1 | completa | Total; eventos.jsonl línea 765 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote765 | 0.062352300 | 1497 | 1 | completa | Total; eventos.jsonl línea 766 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote766 | 0.064212900 | 1497 | 1 | completa | Total; eventos.jsonl línea 767 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote767 | 0.060540500 | 1497 | 1 | completa | Total; eventos.jsonl línea 768 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote768 | 0.062208400 | 1497 | 1 | completa | Total; eventos.jsonl línea 769 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote769 | 0.078932600 | 1497 | 1 | completa | Total; eventos.jsonl línea 770 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote770 | 0.068985500 | 1497 | 1 | completa | Total; eventos.jsonl línea 771 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote771 | 0.060780100 | 1497 | 1 | completa | Total; eventos.jsonl línea 772 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote772 | 0.060612300 | 1497 | 1 | completa | Total; eventos.jsonl línea 773 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote773 | 0.064735100 | 1497 | 1 | completa | Total; eventos.jsonl línea 774 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote774 | 0.079705300 | 1497 | 1 | completa | Total; eventos.jsonl línea 775 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote775 | 0.119289100 | 1497 | 1 | completa | Total; eventos.jsonl línea 776 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote776 | 0.126412500 | 1497 | 1 | completa | Total; eventos.jsonl línea 777 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote777 | 0.087371200 | 1497 | 1 | completa | Total; eventos.jsonl línea 778 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote778 | 0.074953900 | 1497 | 1 | completa | Total; eventos.jsonl línea 779 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote779 | 0.069252800 | 1497 | 1 | completa | Total; eventos.jsonl línea 780 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote780 | 0.069330400 | 1497 | 1 | completa | Total; eventos.jsonl línea 781 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote781 | 0.066713600 | 1497 | 1 | completa | Total; eventos.jsonl línea 782 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote782 | 0.077401300 | 1497 | 1 | completa | Total; eventos.jsonl línea 783 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote783 | 0.082112800 | 1497 | 1 | completa | Total; eventos.jsonl línea 784 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote784 | 0.098410800 | 1497 | 1 | completa | Total; eventos.jsonl línea 785 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote785 | 0.097936800 | 1497 | 1 | completa | Total; eventos.jsonl línea 786 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote786 | 0.099816500 | 1497 | 1 | completa | Total; eventos.jsonl línea 787 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote787 | 0.104038900 | 1497 | 1 | completa | Total; eventos.jsonl línea 788 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote788 | 0.103685900 | 1497 | 1 | completa | Total; eventos.jsonl línea 789 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote789 | 0.097128600 | 1497 | 1 | completa | Total; eventos.jsonl línea 790 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote790 | 0.098856200 | 1497 | 1 | completa | Total; eventos.jsonl línea 791 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote791 | 0.096489700 | 1497 | 1 | completa | Total; eventos.jsonl línea 792 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote792 | 0.094568500 | 1497 | 1 | completa | Total; eventos.jsonl línea 793 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote793 | 0.104532100 | 1497 | 1 | completa | Total; eventos.jsonl línea 794 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote794 | 0.097587800 | 1497 | 1 | completa | Total; eventos.jsonl línea 795 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote795 | 0.102899000 | 1497 | 1 | completa | Total; eventos.jsonl línea 796 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote796 | 0.099543600 | 1497 | 1 | completa | Total; eventos.jsonl línea 797 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote797 | 0.096115600 | 1497 | 1 | completa | Total; eventos.jsonl línea 798 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote798 | 0.100260300 | 1497 | 1 | completa | Total; eventos.jsonl línea 799 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote799 | 0.095271000 | 1497 | 1 | completa | Total; eventos.jsonl línea 800 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote800 | 0.094107200 | 1497 | 1 | completa | Total; eventos.jsonl línea 801 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote801 | 0.094777900 | 1497 | 1 | completa | Total; eventos.jsonl línea 802 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote802 | 0.101734200 | 1497 | 1 | completa | Total; eventos.jsonl línea 803 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote803 | 0.102204800 | 1497 | 1 | completa | Total; eventos.jsonl línea 804 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote804 | 0.110050700 | 1497 | 1 | completa | Total; eventos.jsonl línea 805 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote805 | 0.095165000 | 1497 | 1 | completa | Total; eventos.jsonl línea 806 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote806 | 0.095180700 | 1497 | 1 | completa | Total; eventos.jsonl línea 807 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote807 | 0.095076700 | 1497 | 1 | completa | Total; eventos.jsonl línea 808 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote808 | 0.101551900 | 1497 | 1 | completa | Total; eventos.jsonl línea 809 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote809 | 0.097967600 | 1497 | 1 | completa | Total; eventos.jsonl línea 810 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote810 | 0.098705500 | 1497 | 1 | completa | Total; eventos.jsonl línea 811 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote811 | 0.105463600 | 1497 | 1 | completa | Total; eventos.jsonl línea 812 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote812 | 0.107196900 | 1497 | 1 | completa | Total; eventos.jsonl línea 813 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote813 | 0.101727400 | 1497 | 1 | completa | Total; eventos.jsonl línea 814 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote814 | 0.098103800 | 1497 | 1 | completa | Total; eventos.jsonl línea 815 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote815 | 0.096599200 | 1497 | 1 | completa | Total; eventos.jsonl línea 816 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote816 | 0.096354200 | 1497 | 1 | completa | Total; eventos.jsonl línea 817 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote817 | 0.097924700 | 1497 | 1 | completa | Total; eventos.jsonl línea 818 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote818 | 0.098678800 | 1497 | 1 | completa | Total; eventos.jsonl línea 819 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote819 | 0.098328600 | 1497 | 1 | completa | Total; eventos.jsonl línea 820 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote820 | 0.103473400 | 1497 | 1 | completa | Total; eventos.jsonl línea 821 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote821 | 0.100258800 | 1497 | 1 | completa | Total; eventos.jsonl línea 822 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote822 | 0.094819400 | 1497 | 1 | completa | Total; eventos.jsonl línea 823 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote823 | 0.097074200 | 1497 | 1 | completa | Total; eventos.jsonl línea 824 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote824 | 0.099979600 | 1497 | 1 | completa | Total; eventos.jsonl línea 825 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote825 | 0.100891300 | 1497 | 1 | completa | Total; eventos.jsonl línea 826 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote826 | 0.100371500 | 1497 | 1 | completa | Total; eventos.jsonl línea 827 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote827 | 0.100327200 | 1497 | 1 | completa | Total; eventos.jsonl línea 828 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote828 | 0.095035600 | 1497 | 1 | completa | Total; eventos.jsonl línea 829 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote829 | 0.092494100 | 1497 | 1 | completa | Total; eventos.jsonl línea 830 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote830 | 0.094343700 | 1497 | 1 | completa | Total; eventos.jsonl línea 831 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote831 | 0.096771700 | 1497 | 1 | completa | Total; eventos.jsonl línea 832 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote832 | 0.096502400 | 1497 | 1 | completa | Total; eventos.jsonl línea 833 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote833 | 0.103698300 | 1497 | 1 | completa | Total; eventos.jsonl línea 834 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote834 | 0.096219500 | 1497 | 1 | completa | Total; eventos.jsonl línea 835 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote835 | 0.094530600 | 1497 | 1 | completa | Total; eventos.jsonl línea 836 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote836 | 0.095934500 | 1497 | 1 | completa | Total; eventos.jsonl línea 837 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote837 | 0.103912600 | 1497 | 1 | completa | Total; eventos.jsonl línea 838 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote838 | 0.098136900 | 1497 | 1 | completa | Total; eventos.jsonl línea 839 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote839 | 0.096409000 | 1497 | 1 | completa | Total; eventos.jsonl línea 840 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote840 | 0.094208600 | 1497 | 1 | completa | Total; eventos.jsonl línea 841 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote841 | 0.098714700 | 1497 | 1 | completa | Total; eventos.jsonl línea 842 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote842 | 0.099265900 | 1497 | 1 | completa | Total; eventos.jsonl línea 843 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote843 | 0.099115600 | 1497 | 1 | completa | Total; eventos.jsonl línea 844 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote844 | 0.098664800 | 1497 | 1 | completa | Total; eventos.jsonl línea 845 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote845 | 0.100799600 | 1497 | 1 | completa | Total; eventos.jsonl línea 846 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote846 | 0.101118900 | 1497 | 1 | completa | Total; eventos.jsonl línea 847 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote847 | 0.098995200 | 1497 | 1 | completa | Total; eventos.jsonl línea 848 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote848 | 0.098214900 | 1497 | 1 | completa | Total; eventos.jsonl línea 849 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote849 | 0.101220600 | 1497 | 1 | completa | Total; eventos.jsonl línea 850 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote850 | 0.095991200 | 1497 | 1 | completa | Total; eventos.jsonl línea 851 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote851 | 0.106342700 | 1497 | 1 | completa | Total; eventos.jsonl línea 852 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote852 | 0.098480600 | 1497 | 1 | completa | Total; eventos.jsonl línea 853 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote853 | 0.113551900 | 1497 | 1 | completa | Total; eventos.jsonl línea 854 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote854 | 0.112666200 | 1497 | 1 | completa | Total; eventos.jsonl línea 855 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote855 | 0.111708600 | 1497 | 1 | completa | Total; eventos.jsonl línea 856 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote856 | 0.096223600 | 1497 | 1 | completa | Total; eventos.jsonl línea 857 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote857 | 0.099570000 | 1497 | 1 | completa | Total; eventos.jsonl línea 858 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote858 | 0.113432300 | 1497 | 1 | completa | Total; eventos.jsonl línea 859 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote859 | 0.106268000 | 1497 | 1 | completa | Total; eventos.jsonl línea 860 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote860 | 0.105070400 | 1497 | 1 | completa | Total; eventos.jsonl línea 861 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote861 | 0.118336600 | 1497 | 1 | completa | Total; eventos.jsonl línea 862 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote862 | 0.108303300 | 1497 | 1 | completa | Total; eventos.jsonl línea 863 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote863 | 0.113820900 | 1497 | 1 | completa | Total; eventos.jsonl línea 864 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote864 | 0.109471800 | 1497 | 1 | completa | Total; eventos.jsonl línea 865 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote865 | 0.097591000 | 1497 | 1 | completa | Total; eventos.jsonl línea 866 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote866 | 0.100018600 | 1497 | 1 | completa | Total; eventos.jsonl línea 867 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote867 | 0.099340000 | 1497 | 1 | completa | Total; eventos.jsonl línea 868 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote868 | 0.096910100 | 1497 | 1 | completa | Total; eventos.jsonl línea 869 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote869 | 0.096355100 | 1497 | 1 | completa | Total; eventos.jsonl línea 870 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote870 | 0.103257500 | 1497 | 1 | completa | Total; eventos.jsonl línea 871 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote871 | 0.100076200 | 1497 | 1 | completa | Total; eventos.jsonl línea 872 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote872 | 0.099933400 | 1497 | 1 | completa | Total; eventos.jsonl línea 873 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote873 | 0.099768000 | 1497 | 1 | completa | Total; eventos.jsonl línea 874 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote874 | 0.097984200 | 1497 | 1 | completa | Total; eventos.jsonl línea 875 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote875 | 0.104549200 | 1497 | 1 | completa | Total; eventos.jsonl línea 876 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote876 | 0.094954200 | 1497 | 1 | completa | Total; eventos.jsonl línea 877 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote877 | 0.094821100 | 1497 | 1 | completa | Total; eventos.jsonl línea 878 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote878 | 0.091698800 | 1497 | 1 | completa | Total; eventos.jsonl línea 879 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote879 | 0.093084500 | 1497 | 1 | completa | Total; eventos.jsonl línea 880 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote880 | 0.098356000 | 1497 | 1 | completa | Total; eventos.jsonl línea 881 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote881 | 0.099200600 | 1497 | 1 | completa | Total; eventos.jsonl línea 882 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote882 | 0.098807300 | 1497 | 1 | completa | Total; eventos.jsonl línea 883 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote883 | 0.108793700 | 1497 | 1 | completa | Total; eventos.jsonl línea 884 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote884 | 0.094909100 | 1497 | 1 | completa | Total; eventos.jsonl línea 885 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote885 | 0.093312700 | 1497 | 1 | completa | Total; eventos.jsonl línea 886 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote886 | 0.099427200 | 1497 | 1 | completa | Total; eventos.jsonl línea 887 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote887 | 0.101446000 | 1497 | 1 | completa | Total; eventos.jsonl línea 888 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote888 | 0.100017300 | 1497 | 1 | completa | Total; eventos.jsonl línea 889 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote889 | 0.097100800 | 1497 | 1 | completa | Total; eventos.jsonl línea 890 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote890 | 0.102572200 | 1497 | 1 | completa | Total; eventos.jsonl línea 891 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote891 | 0.097332600 | 1497 | 1 | completa | Total; eventos.jsonl línea 892 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote892 | 0.097331800 | 1497 | 1 | completa | Total; eventos.jsonl línea 893 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote893 | 0.102499700 | 1497 | 1 | completa | Total; eventos.jsonl línea 894 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote894 | 0.102012100 | 1497 | 1 | completa | Total; eventos.jsonl línea 895 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote895 | 0.104967900 | 1497 | 1 | completa | Total; eventos.jsonl línea 896 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote896 | 0.100311900 | 1497 | 1 | completa | Total; eventos.jsonl línea 897 |
| Inferencia | Kernel Ridge RBF / máscaras SHAP lote897 | 0.106014600 | 1497 | 1 | completa | Total; eventos.jsonl línea 898 |
| Explicación SHAP | 64caminos/32referencias · completo | 61.178497200 | 1497 | 1 | completa | Total; eventos.jsonl línea 899 |
| Inferencia | Kernel Ridge RBF / LIME / Pipeline | 0.008138600 | 1 | 1 | completa | Total; eventos.jsonl línea 900 |
| Inferencia | Kernel Ridge RBF / LIME / Pipeline | 0.036016500 | 1000 | 1 | completa | Total; eventos.jsonl línea 901 |
| Entrenamiento/refit · sustituto LIME | Kernel Ridge RBF / LIME / Ridge | 0.001636500 | 1000 | 1 | completa | Total; eventos.jsonl línea 902 |
| Inferencia · sustituto LIME | Kernel Ridge RBF / LIME / Ridge | 0.000242800 | 1000 | 1 | completa | Total; eventos.jsonl línea 903 |
| Inferencia · sustituto LIME | Kernel Ridge RBF / LIME / Ridge | 0.000142200 | 1 | 1 | completa | Total; eventos.jsonl línea 904 |
| Inferencia | Kernel Ridge RBF / LIME / Pipeline | 0.008554000 | 1 | 1 | completa | Total; eventos.jsonl línea 905 |
| Inferencia | Kernel Ridge RBF / LIME / Pipeline | 0.035359000 | 1000 | 1 | completa | Total; eventos.jsonl línea 906 |
| Entrenamiento/refit · sustituto LIME | Kernel Ridge RBF / LIME / Ridge | 0.001750100 | 1000 | 1 | completa | Total; eventos.jsonl línea 907 |
| Inferencia · sustituto LIME | Kernel Ridge RBF / LIME / Ridge | 0.000381900 | 1000 | 1 | completa | Total; eventos.jsonl línea 908 |
| Inferencia · sustituto LIME | Kernel Ridge RBF / LIME / Ridge | 0.000145200 | 1 | 1 | completa | Total; eventos.jsonl línea 909 |
| Total del experimento | Kernel Ridge RBF · SHAP aproximado por permutaciones y LIME | 61.533104100 | No aplica | 1 | completa | Total; eventos.jsonl línea 910 |

### Ejecución `20261019_083727_753ea49c`

- **Modelo/motivo:** Originales · verificación y activación.
- **Fecha/zona:** 2026-10-19T08:37:27.595740-05:00 a 2026-10-19T08:39:27.388797-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_083727_753ea49c/metadata.json](tiempos/20261019_083727_753ea49c/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_083727_753ea49c/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | m0 / validación serialización test | 0.018142000 | 188 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | m5 / validación serialización test | 0.021783700 | 188 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | m19 / validación serialización test | 0.010890900 | 188 | 1 | completa | Total; eventos.jsonl línea 3 |
| Total del experimento | Originales · verificación y activación | 119.795232900 | No aplica | 1 | completa | Total; eventos.jsonl línea 4 |

### Ejecución `20261019_084112_f3ebc0c5`

- **Modelo/motivo:** Verificación/preparación · --tests.
- **Fecha/zona:** 2026-10-19T08:41:12.343704-05:00 a 2026-10-19T08:41:19.298912-05:00; America/Bogota.
- **Estado:** fallida. **Entorno/configuración/código/datos:** [tiempos/20261019_084112_f3ebc0c5/metadata.json](tiempos/20261019_084112_f3ebc0c5/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084112_f3ebc0c5/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Total del experimento | Verificación/preparación · --tests | 6.955273400 | No aplica | 1 | fallida | Total; eventos.jsonl línea 1 |

### Ejecución `20261019_084535_90cdefef`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T08:45:35.322126-05:00 a 2026-10-19T08:45:35.712837-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084535_90cdefef/metadata.json](tiempos/20261019_084535_90cdefef/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084535_90cdefef/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.035813400 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.063770700 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.257898600 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000750700 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.390493900 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_084542_2ca29629`

- **Modelo/motivo:** KNeighborsRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:45:42.249116-05:00 a 2026-10-19T08:45:42.300776-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084542_2ca29629/metadata.json](tiempos/20261019_084542_2ca29629/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084542_2ca29629/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.039261500 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | KNeighborsRegressor · inferencia de aplicación | 0.049762400 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084542_bdcdde74`

- **Modelo/motivo:** Ridge · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:45:42.347268-05:00 a 2026-10-19T08:45:42.377047-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084542_bdcdde74/metadata.json](tiempos/20261019_084542_bdcdde74/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084542_bdcdde74/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.017476300 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Ridge · inferencia de aplicación | 0.029983500 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084542_f69c74f3`

- **Modelo/motivo:** Lasso · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:45:42.419622-05:00 a 2026-10-19T08:45:42.449732-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084542_f69c74f3/metadata.json](tiempos/20261019_084542_f69c74f3/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084542_f69c74f3/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.015613100 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Lasso · inferencia de aplicación | 0.027894700 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084542_59e3cb3c`

- **Modelo/motivo:** RandomForestRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:45:42.834868-05:00 a 2026-10-19T08:45:43.042401-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084542_59e3cb3c/metadata.json](tiempos/20261019_084542_59e3cb3c/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084542_59e3cb3c/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.191459400 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | RandomForestRegressor · inferencia de aplicación | 0.204844700 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084543_946bffe8`

- **Modelo/motivo:** XGBRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:45:43.238806-05:00 a 2026-10-19T08:45:43.295806-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084543_946bffe8/metadata.json](tiempos/20261019_084543_946bffe8/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084543_946bffe8/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.042218100 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | XGBRegressor · inferencia de aplicación | 0.052362900 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084543_76c148a5`

- **Modelo/motivo:** DecisionTreeRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:45:43.355702-05:00 a 2026-10-19T08:45:43.378198-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084543_76c148a5/metadata.json](tiempos/20261019_084543_76c148a5/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084543_76c148a5/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.015490900 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | DecisionTreeRegressor · inferencia de aplicación | 0.024044500 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084551_08b33ce1`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:45:51.647121-05:00 a 2026-10-19T08:45:51.670324-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084551_08b33ce1/metadata.json](tiempos/20261019_084551_08b33ce1/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084551_08b33ce1/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.014493900 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.023858500 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084551_b314afbc`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:45:51.712433-05:00 a 2026-10-19T08:45:51.737189-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084551_b314afbc/metadata.json](tiempos/20261019_084551_b314afbc/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084551_b314afbc/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.014789300 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.022810400 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084551_7128439e`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:45:51.754015-05:00 a 2026-10-19T08:45:51.778925-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084551_7128439e/metadata.json](tiempos/20261019_084551_7128439e/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084551_7128439e/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.014874000 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.023423300 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084551_ee586e94`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:45:51.795536-05:00 a 2026-10-19T08:45:51.820185-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084551_ee586e94/metadata.json](tiempos/20261019_084551_ee586e94/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084551_ee586e94/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.014676000 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.023267500 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084551_bce7bd77`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:45:51.835955-05:00 a 2026-10-19T08:45:51.861292-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084551_bce7bd77/metadata.json](tiempos/20261019_084551_bce7bd77/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084551_bce7bd77/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.014998300 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.022629000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084604_85c4db66`

- **Modelo/motivo:** TransformedTargetRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:46:04.288958-05:00 a 2026-10-19T08:46:04.329427-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084604_85c4db66/metadata.json](tiempos/20261019_084604_85c4db66/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084604_85c4db66/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.031509200 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TransformedTargetRegressor · inferencia de aplicación | 0.039050700 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084606_c35b08a0`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T08:46:06.534081-05:00 a 2026-10-19T08:46:06.911333-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084606_c35b08a0/metadata.json](tiempos/20261019_084606_c35b08a0/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084606_c35b08a0/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.024832900 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.064775300 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.260287100 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000339600 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.370968800 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_084530_b62b0e87`

- **Modelo/motivo:** Verificación/preparación · --tests.
- **Fecha/zona:** 2026-10-19T08:45:30.548031-05:00 a 2026-10-19T08:46:11.752431-05:00; America/Bogota.
- **Estado:** fallida. **Entorno/configuración/código/datos:** [tiempos/20261019_084530_b62b0e87/metadata.json](tiempos/20261019_084530_b62b0e87/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084530_b62b0e87/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | XGBRegressor | 0.032918000 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | KNeighborsRegressor | 0.031591300 | 1 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | KNeighborsRegressor | 0.010872800 | 1 | 1 | completa | Total; eventos.jsonl línea 3 |
| Inferencia | Ridge | 0.000211300 | 1 | 1 | completa | Total; eventos.jsonl línea 4 |
| Inferencia | Ridge | 0.010078100 | 1 | 1 | completa | Total; eventos.jsonl línea 5 |
| Inferencia | Ridge | 0.000194900 | 1 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | Ridge | 0.009945800 | 1 | 1 | completa | Total; eventos.jsonl línea 7 |
| Inferencia | Lasso | 0.008636400 | 1 | 1 | completa | Total; eventos.jsonl línea 8 |
| Inferencia | Lasso | 0.007632500 | 1 | 1 | completa | Total; eventos.jsonl línea 9 |
| Inferencia | RandomForestRegressor | 0.045905800 | 1 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | RandomForestRegressor | 0.055618400 | 1 | 1 | completa | Total; eventos.jsonl línea 11 |
| Inferencia | XGBRegressor | 0.027994600 | 1 | 1 | completa | Total; eventos.jsonl línea 12 |
| Inferencia | XGBRegressor | 0.024998900 | 1 | 1 | completa | Total; eventos.jsonl línea 13 |
| Inferencia | DecisionTreeRegressor | 0.007908100 | 1 | 1 | completa | Total; eventos.jsonl línea 14 |
| Inferencia | DecisionTreeRegressor | 0.007523800 | 1 | 1 | completa | Total; eventos.jsonl línea 15 |
| Inferencia | LinearSVR | 0.008495100 | 1 | 1 | completa | Total; eventos.jsonl línea 16 |
| Inferencia | LinearSVR | 0.007189200 | 1 | 1 | completa | Total; eventos.jsonl línea 17 |
| Inferencia | LinearSVR | 0.008365300 | 1 | 1 | completa | Total; eventos.jsonl línea 18 |
| Inferencia | LinearSVR | 0.007786900 | 1 | 1 | completa | Total; eventos.jsonl línea 19 |
| Inferencia | LinearSVR | 0.008299500 | 1 | 1 | completa | Total; eventos.jsonl línea 20 |
| Inferencia | LinearSVR | 0.008617400 | 1 | 1 | completa | Total; eventos.jsonl línea 21 |
| Inferencia | DecisionTreeRegressor | 0.006274600 | 188 | 1 | completa | Total; eventos.jsonl línea 22 |
| Inferencia | DecisionTreeRegressor | 0.005342900 | 2 | 1 | completa | Total; eventos.jsonl línea 23 |
| Inferencia | LinearSVR | 0.007034300 | 1 | 1 | completa | Total; eventos.jsonl línea 24 |
| Inferencia | LinearSVR | 0.008796000 | 1 | 1 | completa | Total; eventos.jsonl línea 25 |
| Inferencia | LinearSVR | 0.007774400 | 1 | 1 | completa | Total; eventos.jsonl línea 26 |
| Inferencia | LinearSVR | 0.007174500 | 1 | 1 | completa | Total; eventos.jsonl línea 27 |
| Inferencia | XGBRegressor | 0.024380800 | 188 | 1 | completa | Total; eventos.jsonl línea 28 |
| Inferencia | XGBRegressor | 0.021562700 | 188 | 1 | completa | Total; eventos.jsonl línea 29 |
| Inferencia | XGBRegressor | 0.018106300 | 1 | 1 | completa | Total; eventos.jsonl línea 30 |
| Inferencia | XGBRegressor | 0.018692300 | 1 | 1 | completa | Total; eventos.jsonl línea 31 |
| Inferencia | XGBRegressor | 0.019521500 | 1 | 1 | completa | Total; eventos.jsonl línea 32 |
| Inferencia | XGBRegressor | 0.030518900 | 1000 | 1 | completa | Total; eventos.jsonl línea 33 |
| Entrenamiento/refit | Ridge | 0.001647300 | 1000 | 1 | completa | Total; eventos.jsonl línea 34 |
| Inferencia | Ridge | 0.000202900 | 1000 | 1 | completa | Total; eventos.jsonl línea 35 |
| Inferencia | Ridge | 0.000172200 | 1 | 1 | completa | Total; eventos.jsonl línea 36 |
| Inferencia | XGBRegressor | 0.020263300 | 1 | 1 | completa | Total; eventos.jsonl línea 37 |
| Inferencia | XGBRegressor | 0.019094500 | 1 | 1 | completa | Total; eventos.jsonl línea 38 |
| Inferencia | XGBRegressor | 0.026709600 | 1000 | 1 | completa | Total; eventos.jsonl línea 39 |
| Entrenamiento/refit | Ridge | 0.001974500 | 1000 | 1 | completa | Total; eventos.jsonl línea 40 |
| Inferencia | Ridge | 0.000305100 | 1000 | 1 | completa | Total; eventos.jsonl línea 41 |
| Inferencia | Ridge | 0.000183400 | 1 | 1 | completa | Total; eventos.jsonl línea 42 |
| Inferencia | XGBRegressor | 0.019633000 | 1 | 1 | completa | Total; eventos.jsonl línea 43 |
| Inferencia | XGBRegressor | 0.017827700 | 1 | 1 | completa | Total; eventos.jsonl línea 44 |
| Inferencia | XGBRegressor | 0.028007700 | 1000 | 1 | completa | Total; eventos.jsonl línea 45 |
| Entrenamiento/refit | Ridge | 0.001403700 | 1000 | 1 | completa | Total; eventos.jsonl línea 46 |
| Inferencia | Ridge | 0.000324400 | 1000 | 1 | completa | Total; eventos.jsonl línea 47 |
| Inferencia | Ridge | 0.000185500 | 1 | 1 | completa | Total; eventos.jsonl línea 48 |
| Inferencia | XGBRegressor | 0.018614800 | 1 | 1 | completa | Total; eventos.jsonl línea 49 |
| Inferencia | XGBRegressor | 0.026548200 | 1000 | 1 | completa | Total; eventos.jsonl línea 50 |
| Entrenamiento/refit | Ridge | 0.001504300 | 1000 | 1 | completa | Total; eventos.jsonl línea 51 |
| Inferencia | Ridge | 0.000210600 | 1000 | 1 | completa | Total; eventos.jsonl línea 52 |
| Inferencia | Ridge | 0.000173500 | 1 | 1 | completa | Total; eventos.jsonl línea 53 |
| Inferencia | XGBRegressor | 0.020525700 | 1 | 1 | completa | Total; eventos.jsonl línea 54 |
| Inferencia | XGBRegressor | 0.029524900 | 1000 | 1 | completa | Total; eventos.jsonl línea 55 |
| Entrenamiento/refit | Ridge | 0.001460100 | 1000 | 1 | completa | Total; eventos.jsonl línea 56 |
| Inferencia | Ridge | 0.000204800 | 1000 | 1 | completa | Total; eventos.jsonl línea 57 |
| Inferencia | Ridge | 0.000164000 | 1 | 1 | completa | Total; eventos.jsonl línea 58 |
| Inferencia | XGBRegressor | 0.022629200 | 1 | 1 | completa | Total; eventos.jsonl línea 59 |
| Inferencia | TransformedTargetRegressor | 0.021513400 | 1 | 1 | completa | Total; eventos.jsonl línea 60 |
| Inferencia | TransformedTargetRegressor | 0.034570500 | 188 | 1 | completa | Total; eventos.jsonl línea 61 |
| Inferencia | XGBRegressor | 0.032853700 | 1497 | 1 | completa | Total; eventos.jsonl línea 62 |
| Total del experimento | Verificación/preparación · --tests | 41.203902900 | No aplica | 1 | fallida | Total; eventos.jsonl línea 63 |

### Ejecución `20261019_084806_1c7d40f3`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T08:48:06.792678-05:00 a 2026-10-19T08:48:07.186133-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084806_1c7d40f3/metadata.json](tiempos/20261019_084806_1c7d40f3/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084806_1c7d40f3/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.030707200 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.063856500 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.257867200 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000665300 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.393460400 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_084813_f1e2131b`

- **Modelo/motivo:** KNeighborsRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:48:13.794753-05:00 a 2026-10-19T08:48:13.832580-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084813_f1e2131b/metadata.json](tiempos/20261019_084813_f1e2131b/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084813_f1e2131b/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.026467800 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | KNeighborsRegressor · inferencia de aplicación | 0.034158600 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084813_e77e215e`

- **Modelo/motivo:** Ridge · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:48:13.872558-05:00 a 2026-10-19T08:48:13.901239-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084813_e77e215e/metadata.json](tiempos/20261019_084813_e77e215e/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084813_e77e215e/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.018558100 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Ridge · inferencia de aplicación | 0.028598500 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084813_1fa7ee4f`

- **Modelo/motivo:** Lasso · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:48:13.946439-05:00 a 2026-10-19T08:48:13.972662-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084813_1fa7ee4f/metadata.json](tiempos/20261019_084813_1fa7ee4f/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084813_1fa7ee4f/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.015601100 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Lasso · inferencia de aplicación | 0.026184200 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084814_5043ae03`

- **Modelo/motivo:** RandomForestRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:48:14.373627-05:00 a 2026-10-19T08:48:14.580015-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084814_5043ae03/metadata.json](tiempos/20261019_084814_5043ae03/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084814_5043ae03/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.195174700 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | RandomForestRegressor · inferencia de aplicación | 0.208001500 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084814_51a6c581`

- **Modelo/motivo:** XGBRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:48:14.766893-05:00 a 2026-10-19T08:48:14.807891-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084814_51a6c581/metadata.json](tiempos/20261019_084814_51a6c581/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084814_51a6c581/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.032356300 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | XGBRegressor · inferencia de aplicación | 0.040271700 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084814_c030222d`

- **Modelo/motivo:** DecisionTreeRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:48:14.864628-05:00 a 2026-10-19T08:48:14.889268-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084814_c030222d/metadata.json](tiempos/20261019_084814_c030222d/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084814_c030222d/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.012835900 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | DecisionTreeRegressor · inferencia de aplicación | 0.022582000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084823_cbef5514`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:48:23.053518-05:00 a 2026-10-19T08:48:23.077843-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084823_cbef5514/metadata.json](tiempos/20261019_084823_cbef5514/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084823_cbef5514/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.017205800 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.024963600 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084823_4b7c3710`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:48:23.111421-05:00 a 2026-10-19T08:48:23.136264-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084823_4b7c3710/metadata.json](tiempos/20261019_084823_4b7c3710/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084823_4b7c3710/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.014415400 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.022536100 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084823_bf954312`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:48:23.152771-05:00 a 2026-10-19T08:48:23.177010-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084823_bf954312/metadata.json](tiempos/20261019_084823_bf954312/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084823_bf954312/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.014912400 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.022314100 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084823_afeb381a`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:48:23.191044-05:00 a 2026-10-19T08:48:23.209588-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084823_afeb381a/metadata.json](tiempos/20261019_084823_afeb381a/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084823_afeb381a/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.014903500 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.022427300 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084823_d718a425`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:48:23.226293-05:00 a 2026-10-19T08:48:23.250004-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084823_d718a425/metadata.json](tiempos/20261019_084823_d718a425/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084823_d718a425/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.014604200 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.022289000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084835_98681d8b`

- **Modelo/motivo:** TransformedTargetRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:48:35.423408-05:00 a 2026-10-19T08:48:35.464872-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084835_98681d8b/metadata.json](tiempos/20261019_084835_98681d8b/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084835_98681d8b/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.033266300 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TransformedTargetRegressor · inferencia de aplicación | 0.040827700 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084837_6b600649`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T08:48:37.504042-05:00 a 2026-10-19T08:48:37.866591-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084837_6b600649/metadata.json](tiempos/20261019_084837_6b600649/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084837_6b600649/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.022869200 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.063943600 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.253961000 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000544000 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.360127800 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_084802_886f574a`

- **Modelo/motivo:** Verificación/preparación · --tests.
- **Fecha/zona:** 2026-10-19T08:48:02.353386-05:00 a 2026-10-19T08:48:49.236284-05:00; America/Bogota.
- **Estado:** fallida. **Entorno/configuración/código/datos:** [tiempos/20261019_084802_886f574a/metadata.json](tiempos/20261019_084802_886f574a/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084802_886f574a/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | XGBRegressor | 0.034224000 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | KNeighborsRegressor | 0.018921700 | 1 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | KNeighborsRegressor | 0.009725800 | 1 | 1 | completa | Total; eventos.jsonl línea 3 |
| Inferencia | Ridge | 0.000230700 | 1 | 1 | completa | Total; eventos.jsonl línea 4 |
| Inferencia | Ridge | 0.010788600 | 1 | 1 | completa | Total; eventos.jsonl línea 5 |
| Inferencia | Ridge | 0.000206900 | 1 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | Ridge | 0.010233000 | 1 | 1 | completa | Total; eventos.jsonl línea 7 |
| Inferencia | Lasso | 0.007520400 | 1 | 1 | completa | Total; eventos.jsonl línea 8 |
| Inferencia | Lasso | 0.007990600 | 1 | 1 | completa | Total; eventos.jsonl línea 9 |
| Inferencia | RandomForestRegressor | 0.045955500 | 1 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | RandomForestRegressor | 0.045437400 | 1 | 1 | completa | Total; eventos.jsonl línea 11 |
| Inferencia | XGBRegressor | 0.020133400 | 1 | 1 | completa | Total; eventos.jsonl línea 12 |
| Inferencia | XGBRegressor | 0.020149700 | 1 | 1 | completa | Total; eventos.jsonl línea 13 |
| Inferencia | DecisionTreeRegressor | 0.006454100 | 1 | 1 | completa | Total; eventos.jsonl línea 14 |
| Inferencia | DecisionTreeRegressor | 0.011661600 | 1 | 1 | completa | Total; eventos.jsonl línea 15 |
| Inferencia | LinearSVR | 0.010739000 | 1 | 1 | completa | Total; eventos.jsonl línea 16 |
| Inferencia | LinearSVR | 0.008455500 | 1 | 1 | completa | Total; eventos.jsonl línea 17 |
| Inferencia | LinearSVR | 0.008105500 | 1 | 1 | completa | Total; eventos.jsonl línea 18 |
| Inferencia | LinearSVR | 0.007704500 | 1 | 1 | completa | Total; eventos.jsonl línea 19 |
| Inferencia | LinearSVR | 0.007750200 | 1 | 1 | completa | Total; eventos.jsonl línea 20 |
| Inferencia | LinearSVR | 0.007964100 | 1 | 1 | completa | Total; eventos.jsonl línea 21 |
| Inferencia | DecisionTreeRegressor | 0.007767900 | 188 | 1 | completa | Total; eventos.jsonl línea 22 |
| Inferencia | DecisionTreeRegressor | 0.006357400 | 2 | 1 | completa | Total; eventos.jsonl línea 23 |
| Inferencia | LinearSVR | 0.008793100 | 1 | 1 | completa | Total; eventos.jsonl línea 24 |
| Inferencia | LinearSVR | 0.007365600 | 1 | 1 | completa | Total; eventos.jsonl línea 25 |
| Inferencia | LinearSVR | 0.007018400 | 1 | 1 | completa | Total; eventos.jsonl línea 26 |
| Inferencia | LinearSVR | 0.007512000 | 1 | 1 | completa | Total; eventos.jsonl línea 27 |
| Inferencia | XGBRegressor | 0.021988200 | 188 | 1 | completa | Total; eventos.jsonl línea 28 |
| Inferencia | XGBRegressor | 0.019868000 | 188 | 1 | completa | Total; eventos.jsonl línea 29 |
| Inferencia | XGBRegressor | 0.021269900 | 1 | 1 | completa | Total; eventos.jsonl línea 30 |
| Inferencia | XGBRegressor | 0.020290300 | 1 | 1 | completa | Total; eventos.jsonl línea 31 |
| Inferencia | XGBRegressor | 0.024995600 | 1 | 1 | completa | Total; eventos.jsonl línea 32 |
| Inferencia | XGBRegressor | 0.032478700 | 1000 | 1 | completa | Total; eventos.jsonl línea 33 |
| Entrenamiento/refit | Ridge | 0.001596100 | 1000 | 1 | completa | Total; eventos.jsonl línea 34 |
| Inferencia | Ridge | 0.000207600 | 1000 | 1 | completa | Total; eventos.jsonl línea 35 |
| Inferencia | Ridge | 0.000178300 | 1 | 1 | completa | Total; eventos.jsonl línea 36 |
| Inferencia | XGBRegressor | 0.019143000 | 1 | 1 | completa | Total; eventos.jsonl línea 37 |
| Inferencia | XGBRegressor | 0.024899800 | 1 | 1 | completa | Total; eventos.jsonl línea 38 |
| Inferencia | XGBRegressor | 0.027323400 | 1000 | 1 | completa | Total; eventos.jsonl línea 39 |
| Entrenamiento/refit | Ridge | 0.001762400 | 1000 | 1 | completa | Total; eventos.jsonl línea 40 |
| Inferencia | Ridge | 0.000214400 | 1000 | 1 | completa | Total; eventos.jsonl línea 41 |
| Inferencia | Ridge | 0.000168800 | 1 | 1 | completa | Total; eventos.jsonl línea 42 |
| Inferencia | XGBRegressor | 0.018837700 | 1 | 1 | completa | Total; eventos.jsonl línea 43 |
| Inferencia | XGBRegressor | 0.019283100 | 1 | 1 | completa | Total; eventos.jsonl línea 44 |
| Inferencia | XGBRegressor | 0.026948300 | 1000 | 1 | completa | Total; eventos.jsonl línea 45 |
| Entrenamiento/refit | Ridge | 0.001724200 | 1000 | 1 | completa | Total; eventos.jsonl línea 46 |
| Inferencia | Ridge | 0.000208800 | 1000 | 1 | completa | Total; eventos.jsonl línea 47 |
| Inferencia | Ridge | 0.000179300 | 1 | 1 | completa | Total; eventos.jsonl línea 48 |
| Inferencia | XGBRegressor | 0.019101300 | 1 | 1 | completa | Total; eventos.jsonl línea 49 |
| Inferencia | XGBRegressor | 0.026945600 | 1000 | 1 | completa | Total; eventos.jsonl línea 50 |
| Entrenamiento/refit | Ridge | 0.001863700 | 1000 | 1 | completa | Total; eventos.jsonl línea 51 |
| Inferencia | Ridge | 0.000203300 | 1000 | 1 | completa | Total; eventos.jsonl línea 52 |
| Inferencia | Ridge | 0.000165500 | 1 | 1 | completa | Total; eventos.jsonl línea 53 |
| Inferencia | XGBRegressor | 0.020240800 | 1 | 1 | completa | Total; eventos.jsonl línea 54 |
| Inferencia | XGBRegressor | 0.026156200 | 1000 | 1 | completa | Total; eventos.jsonl línea 55 |
| Entrenamiento/refit | Ridge | 0.001418000 | 1000 | 1 | completa | Total; eventos.jsonl línea 56 |
| Inferencia | Ridge | 0.000201100 | 1000 | 1 | completa | Total; eventos.jsonl línea 57 |
| Inferencia | Ridge | 0.000167400 | 1 | 1 | completa | Total; eventos.jsonl línea 58 |
| Inferencia | XGBRegressor | 0.020962600 | 1 | 1 | completa | Total; eventos.jsonl línea 59 |
| Inferencia | TransformedTargetRegressor | 0.023409000 | 1 | 1 | completa | Total; eventos.jsonl línea 60 |
| Inferencia | TransformedTargetRegressor | 0.016231500 | 188 | 1 | completa | Total; eventos.jsonl línea 61 |
| Inferencia | XGBRegressor | 0.031730300 | 1497 | 1 | completa | Total; eventos.jsonl línea 62 |
| Total del experimento | Verificación/preparación · --tests | 46.880649900 | No aplica | 1 | fallida | Total; eventos.jsonl línea 63 |

### Ejecución `20261019_084925_3401df89`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T08:49:25.457970-05:00 a 2026-10-19T08:49:25.847934-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084925_3401df89/metadata.json](tiempos/20261019_084925_3401df89/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084925_3401df89/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.032637500 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.061033700 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.262046300 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000527000 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.387937400 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_084932_d567e32f`

- **Modelo/motivo:** KNeighborsRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:49:32.968876-05:00 a 2026-10-19T08:49:33.014306-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084932_d567e32f/metadata.json](tiempos/20261019_084932_d567e32f/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084932_d567e32f/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.033344800 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | KNeighborsRegressor · inferencia de aplicación | 0.043221700 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084933_ae4bee36`

- **Modelo/motivo:** Ridge · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:49:33.063580-05:00 a 2026-10-19T08:49:33.093642-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084933_ae4bee36/metadata.json](tiempos/20261019_084933_ae4bee36/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084933_ae4bee36/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.020532100 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Ridge · inferencia de aplicación | 0.028941300 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084933_a893abcc`

- **Modelo/motivo:** Lasso · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:49:33.134526-05:00 a 2026-10-19T08:49:33.161687-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084933_a893abcc/metadata.json](tiempos/20261019_084933_a893abcc/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084933_a893abcc/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.019354000 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Lasso · inferencia de aplicación | 0.028758600 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084933_7b6aae71`

- **Modelo/motivo:** RandomForestRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:49:33.657896-05:00 a 2026-10-19T08:49:33.951885-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084933_7b6aae71/metadata.json](tiempos/20261019_084933_7b6aae71/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084933_7b6aae71/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.276591900 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | RandomForestRegressor · inferencia de aplicación | 0.290452500 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084934_90decbd6`

- **Modelo/motivo:** XGBRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:49:34.201155-05:00 a 2026-10-19T08:49:34.245711-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084934_90decbd6/metadata.json](tiempos/20261019_084934_90decbd6/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084934_90decbd6/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.034974100 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | XGBRegressor · inferencia de aplicación | 0.045814500 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084934_4ed810a9`

- **Modelo/motivo:** DecisionTreeRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:49:34.311069-05:00 a 2026-10-19T08:49:34.327567-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084934_4ed810a9/metadata.json](tiempos/20261019_084934_4ed810a9/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084934_4ed810a9/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.013386000 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | DecisionTreeRegressor · inferencia de aplicación | 0.022111200 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084936_dbbeb1c8`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T08:49:36.201283-05:00 a 2026-10-19T08:49:36.668481-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084936_dbbeb1c8/metadata.json](tiempos/20261019_084936_dbbeb1c8/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084936_dbbeb1c8/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.023683800 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.027185100 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.286516000 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000517800 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.466344400 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_084943_d584848a`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:49:43.135010-05:00 a 2026-10-19T08:49:43.159673-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084943_d584848a/metadata.json](tiempos/20261019_084943_d584848a/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084943_d584848a/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.015727300 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.023804800 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084943_e2234461`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:49:43.195759-05:00 a 2026-10-19T08:49:43.216722-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084943_e2234461/metadata.json](tiempos/20261019_084943_e2234461/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084943_e2234461/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.015455700 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.023373200 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084943_1fe85146`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:49:43.234601-05:00 a 2026-10-19T08:49:43.258332-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084943_1fe85146/metadata.json](tiempos/20261019_084943_1fe85146/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084943_1fe85146/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.014990400 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.023265800 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084943_469d3ee0`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:49:43.273225-05:00 a 2026-10-19T08:49:43.289802-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084943_469d3ee0/metadata.json](tiempos/20261019_084943_469d3ee0/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084943_469d3ee0/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.013540500 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.021854100 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084943_6dcc9af7`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:49:43.314463-05:00 a 2026-10-19T08:49:43.339006-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084943_6dcc9af7/metadata.json](tiempos/20261019_084943_6dcc9af7/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084943_6dcc9af7/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.016305300 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.023930400 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084955_ba752451`

- **Modelo/motivo:** TransformedTargetRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:49:55.741196-05:00 a 2026-10-19T08:49:55.782986-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084955_ba752451/metadata.json](tiempos/20261019_084955_ba752451/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084955_ba752451/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.035463500 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TransformedTargetRegressor · inferencia de aplicación | 0.043369600 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_084957_d3813042`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T08:49:57.848129-05:00 a 2026-10-19T08:49:58.213669-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084957_d3813042/metadata.json](tiempos/20261019_084957_d3813042/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084957_d3813042/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.023671700 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.062899000 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.255930400 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000546500 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.362648900 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_084920_627272f4`

- **Modelo/motivo:** Verificación/preparación · --tests.
- **Fecha/zona:** 2026-10-19T08:49:20.946369-05:00 a 2026-10-19T08:50:09.274098-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_084920_627272f4/metadata.json](tiempos/20261019_084920_627272f4/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_084920_627272f4/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | XGBRegressor | 0.031698900 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | KNeighborsRegressor | 0.023245100 | 1 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | KNeighborsRegressor | 0.011237800 | 1 | 1 | completa | Total; eventos.jsonl línea 3 |
| Inferencia | Ridge | 0.000240100 | 1 | 1 | completa | Total; eventos.jsonl línea 4 |
| Inferencia | Ridge | 0.011403800 | 1 | 1 | completa | Total; eventos.jsonl línea 5 |
| Inferencia | Ridge | 0.000198000 | 1 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | Ridge | 0.010004900 | 1 | 1 | completa | Total; eventos.jsonl línea 7 |
| Inferencia | Lasso | 0.010537300 | 1 | 1 | completa | Total; eventos.jsonl línea 8 |
| Inferencia | Lasso | 0.011360900 | 1 | 1 | completa | Total; eventos.jsonl línea 9 |
| Inferencia | RandomForestRegressor | 0.072394800 | 1 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | RandomForestRegressor | 0.045340000 | 1 | 1 | completa | Total; eventos.jsonl línea 11 |
| Inferencia | XGBRegressor | 0.021251100 | 1 | 1 | completa | Total; eventos.jsonl línea 12 |
| Inferencia | XGBRegressor | 0.025552000 | 1 | 1 | completa | Total; eventos.jsonl línea 13 |
| Inferencia | DecisionTreeRegressor | 0.007928900 | 1 | 1 | completa | Total; eventos.jsonl línea 14 |
| Inferencia | DecisionTreeRegressor | 0.007866300 | 1 | 1 | completa | Total; eventos.jsonl línea 15 |
| Inferencia | LinearSVR | 0.008342800 | 1 | 1 | completa | Total; eventos.jsonl línea 16 |
| Inferencia | LinearSVR | 0.007525800 | 1 | 1 | completa | Total; eventos.jsonl línea 17 |
| Inferencia | LinearSVR | 0.008954800 | 1 | 1 | completa | Total; eventos.jsonl línea 18 |
| Inferencia | LinearSVR | 0.007681700 | 1 | 1 | completa | Total; eventos.jsonl línea 19 |
| Inferencia | LinearSVR | 0.007853600 | 1 | 1 | completa | Total; eventos.jsonl línea 20 |
| Inferencia | LinearSVR | 0.009608000 | 1 | 1 | completa | Total; eventos.jsonl línea 21 |
| Inferencia | DecisionTreeRegressor | 0.006852300 | 188 | 1 | completa | Total; eventos.jsonl línea 22 |
| Inferencia | DecisionTreeRegressor | 0.005662900 | 2 | 1 | completa | Total; eventos.jsonl línea 23 |
| Inferencia | LinearSVR | 0.012757500 | 1 | 1 | completa | Total; eventos.jsonl línea 24 |
| Inferencia | LinearSVR | 0.008489800 | 1 | 1 | completa | Total; eventos.jsonl línea 25 |
| Inferencia | LinearSVR | 0.008109200 | 1 | 1 | completa | Total; eventos.jsonl línea 26 |
| Inferencia | LinearSVR | 0.007022500 | 1 | 1 | completa | Total; eventos.jsonl línea 27 |
| Inferencia | XGBRegressor | 0.025656600 | 188 | 1 | completa | Total; eventos.jsonl línea 28 |
| Inferencia | XGBRegressor | 0.026323700 | 188 | 1 | completa | Total; eventos.jsonl línea 29 |
| Inferencia | XGBRegressor | 0.021501100 | 1 | 1 | completa | Total; eventos.jsonl línea 30 |
| Inferencia | XGBRegressor | 0.018711100 | 1 | 1 | completa | Total; eventos.jsonl línea 31 |
| Inferencia | XGBRegressor | 0.018277900 | 1 | 1 | completa | Total; eventos.jsonl línea 32 |
| Inferencia | XGBRegressor | 0.027266900 | 1000 | 1 | completa | Total; eventos.jsonl línea 33 |
| Entrenamiento/refit | Ridge | 0.001534000 | 1000 | 1 | completa | Total; eventos.jsonl línea 34 |
| Inferencia | Ridge | 0.000198000 | 1000 | 1 | completa | Total; eventos.jsonl línea 35 |
| Inferencia | Ridge | 0.000162900 | 1 | 1 | completa | Total; eventos.jsonl línea 36 |
| Inferencia | XGBRegressor | 0.017675300 | 1 | 1 | completa | Total; eventos.jsonl línea 37 |
| Inferencia | XGBRegressor | 0.019650400 | 1 | 1 | completa | Total; eventos.jsonl línea 38 |
| Inferencia | XGBRegressor | 0.025958800 | 1000 | 1 | completa | Total; eventos.jsonl línea 39 |
| Entrenamiento/refit | Ridge | 0.001398200 | 1000 | 1 | completa | Total; eventos.jsonl línea 40 |
| Inferencia | Ridge | 0.000198000 | 1000 | 1 | completa | Total; eventos.jsonl línea 41 |
| Inferencia | Ridge | 0.000245100 | 1 | 1 | completa | Total; eventos.jsonl línea 42 |
| Inferencia | XGBRegressor | 0.018777600 | 1 | 1 | completa | Total; eventos.jsonl línea 43 |
| Inferencia | XGBRegressor | 0.028734400 | 1 | 1 | completa | Total; eventos.jsonl línea 44 |
| Inferencia | XGBRegressor | 0.033928400 | 1000 | 1 | completa | Total; eventos.jsonl línea 45 |
| Entrenamiento/refit | Ridge | 0.002315900 | 1000 | 1 | completa | Total; eventos.jsonl línea 46 |
| Inferencia | Ridge | 0.000211000 | 1000 | 1 | completa | Total; eventos.jsonl línea 47 |
| Inferencia | Ridge | 0.000175700 | 1 | 1 | completa | Total; eventos.jsonl línea 48 |
| Inferencia | XGBRegressor | 0.020025700 | 1 | 1 | completa | Total; eventos.jsonl línea 49 |
| Inferencia | XGBRegressor | 0.026481000 | 1000 | 1 | completa | Total; eventos.jsonl línea 50 |
| Entrenamiento/refit | Ridge | 0.002044800 | 1000 | 1 | completa | Total; eventos.jsonl línea 51 |
| Inferencia | Ridge | 0.000298900 | 1000 | 1 | completa | Total; eventos.jsonl línea 52 |
| Inferencia | Ridge | 0.000236900 | 1 | 1 | completa | Total; eventos.jsonl línea 53 |
| Inferencia | XGBRegressor | 0.022065400 | 1 | 1 | completa | Total; eventos.jsonl línea 54 |
| Inferencia | XGBRegressor | 0.028257100 | 1000 | 1 | completa | Total; eventos.jsonl línea 55 |
| Entrenamiento/refit | Ridge | 0.001857100 | 1000 | 1 | completa | Total; eventos.jsonl línea 56 |
| Inferencia | Ridge | 0.000215500 | 1000 | 1 | completa | Total; eventos.jsonl línea 57 |
| Inferencia | Ridge | 0.000165500 | 1 | 1 | completa | Total; eventos.jsonl línea 58 |
| Inferencia | XGBRegressor | 0.020166000 | 1 | 1 | completa | Total; eventos.jsonl línea 59 |
| Inferencia | TransformedTargetRegressor | 0.025736800 | 1 | 1 | completa | Total; eventos.jsonl línea 60 |
| Inferencia | TransformedTargetRegressor | 0.018076600 | 188 | 1 | completa | Total; eventos.jsonl línea 61 |
| Inferencia | XGBRegressor | 0.032324000 | 1497 | 1 | completa | Total; eventos.jsonl línea 62 |
| Total del experimento | Verificación/preparación · --tests | 48.324416200 | No aplica | 1 | completa | Total; eventos.jsonl línea 63 |

### Ejecución `20261019_085514_848e5ebd`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T08:55:14.451122-05:00 a 2026-10-19T08:55:16.188722-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_085514_848e5ebd/metadata.json](tiempos/20261019_085514_848e5ebd/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_085514_848e5ebd/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.122945400 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.290170300 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 1.228329100 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.001617400 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 1.730178800 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_085550_0d6fa55a`

- **Modelo/motivo:** KNeighborsRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:55:50.712799-05:00 a 2026-10-19T08:55:50.928905-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_085550_0d6fa55a/metadata.json](tiempos/20261019_085550_0d6fa55a/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_085550_0d6fa55a/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.165326300 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | KNeighborsRegressor · inferencia de aplicación | 0.210062000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_085551_f6afa35f`

- **Modelo/motivo:** Ridge · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:55:51.131058-05:00 a 2026-10-19T08:55:51.282880-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_085551_f6afa35f/metadata.json](tiempos/20261019_085551_f6afa35f/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_085551_f6afa35f/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.105176400 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Ridge · inferencia de aplicación | 0.150347900 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_085551_a9ba2b06`

- **Modelo/motivo:** Lasso · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:55:51.496139-05:00 a 2026-10-19T08:55:51.637086-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_085551_a9ba2b06/metadata.json](tiempos/20261019_085551_a9ba2b06/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_085551_a9ba2b06/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.093491700 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Lasso · inferencia de aplicación | 0.136713200 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_085554_af5336d7`

- **Modelo/motivo:** RandomForestRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:55:54.288996-05:00 a 2026-10-19T08:55:55.770835-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_085554_af5336d7/metadata.json](tiempos/20261019_085554_af5336d7/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_085554_af5336d7/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 1.402906300 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | RandomForestRegressor · inferencia de aplicación | 1.479111100 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_085556_49c2ac49`

- **Modelo/motivo:** XGBRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:55:56.880757-05:00 a 2026-10-19T08:55:57.136279-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_085556_49c2ac49/metadata.json](tiempos/20261019_085556_49c2ac49/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_085556_49c2ac49/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.202368300 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | XGBRegressor · inferencia de aplicación | 0.244303500 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_085557_6e77282d`

- **Modelo/motivo:** DecisionTreeRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:55:57.465367-05:00 a 2026-10-19T08:55:57.596580-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_085557_6e77282d/metadata.json](tiempos/20261019_085557_6e77282d/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_085557_6e77282d/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.076729000 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | DecisionTreeRegressor · inferencia de aplicación | 0.122986700 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_085631_6b7465b3`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T08:56:31.449554-05:00 a 2026-10-19T08:56:33.753710-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_085631_6b7465b3/metadata.json](tiempos/20261019_085631_6b7465b3/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_085631_6b7465b3/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.149216900 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.423305400 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 1.598553000 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.007154000 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 2.299711400 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_085607_6b7a2842`

- **Modelo/motivo:** Verificación/preparación · Dash/validate_package.py.
- **Fecha/zona:** 2026-10-19T08:56:08.009033-05:00 a 2026-10-19T08:56:42.029376-05:00; America/Bogota.
- **Estado:** fallida. **Entorno/configuración/código/datos:** [tiempos/20261019_085607_6b7a2842/metadata.json](tiempos/20261019_085607_6b7a2842/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_085607_6b7a2842/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | XGBRegressor | 0.215619700 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Verificación/preparación · Dash/validate_package.py | 34.021126000 | No aplica | 1 | fallida | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_085649_c274be6e`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:56:49.301189-05:00 a 2026-10-19T08:56:49.449607-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_085649_c274be6e/metadata.json](tiempos/20261019_085649_c274be6e/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_085649_c274be6e/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.095809900 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.142690600 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_085649_d6448991`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:56:49.665783-05:00 a 2026-10-19T08:56:49.780010-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_085649_d6448991/metadata.json](tiempos/20261019_085649_d6448991/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_085649_d6448991/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.073789800 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.108250500 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_085649_51c7e77c`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:56:49.846254-05:00 a 2026-10-19T08:56:49.981000-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_085649_51c7e77c/metadata.json](tiempos/20261019_085649_51c7e77c/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_085649_51c7e77c/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.094338300 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.131697500 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_085650_b1626248`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:56:50.075108-05:00 a 2026-10-19T08:56:50.220364-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_085650_b1626248/metadata.json](tiempos/20261019_085650_b1626248/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_085650_b1626248/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.096211600 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.140559700 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_085650_04afe6bb`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:56:50.323494-05:00 a 2026-10-19T08:56:50.473075-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_085650_04afe6bb/metadata.json](tiempos/20261019_085650_04afe6bb/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_085650_04afe6bb/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.098882100 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.145360200 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_085718_250384b9`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T08:57:18.999206-05:00 a 2026-10-19T08:57:21.519832-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_085718_250384b9/metadata.json](tiempos/20261019_085718_250384b9/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_085718_250384b9/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.125553400 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.196575200 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 1.574893400 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.001489200 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 2.520368700 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_085802_46b45713`

- **Modelo/motivo:** TransformedTargetRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T08:58:02.595982-05:00 a 2026-10-19T08:58:02.823804-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_085802_46b45713/metadata.json](tiempos/20261019_085802_46b45713/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_085802_46b45713/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.176258700 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TransformedTargetRegressor · inferencia de aplicación | 0.224549800 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_085816_09373b93`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T08:58:16.055222-05:00 a 2026-10-19T08:58:18.104001-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_085816_09373b93/metadata.json](tiempos/20261019_085816_09373b93/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_085816_09373b93/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.139486500 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.364475700 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 1.472509000 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.001315400 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 2.045022200 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_085454_d435c640`

- **Modelo/motivo:** Verificación/preparación · --tests.
- **Fecha/zona:** 2026-10-19T08:54:54.358428-05:00 a 2026-10-19T08:59:28.801038-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_085454_d435c640/metadata.json](tiempos/20261019_085454_d435c640/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_085454_d435c640/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | XGBRegressor | 0.149920200 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | KNeighborsRegressor | 0.114582900 | 1 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | KNeighborsRegressor | 0.044540900 | 1 | 1 | completa | Total; eventos.jsonl línea 3 |
| Inferencia | Ridge | 0.001292200 | 1 | 1 | completa | Total; eventos.jsonl línea 4 |
| Inferencia | Ridge | 0.057666600 | 1 | 1 | completa | Total; eventos.jsonl línea 5 |
| Inferencia | Ridge | 0.000891700 | 1 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | Ridge | 0.054405500 | 1 | 1 | completa | Total; eventos.jsonl línea 7 |
| Inferencia | Lasso | 0.048322400 | 1 | 1 | completa | Total; eventos.jsonl línea 8 |
| Inferencia | Lasso | 0.040973100 | 1 | 1 | completa | Total; eventos.jsonl línea 9 |
| Inferencia | RandomForestRegressor | 0.341517900 | 1 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | RandomForestRegressor | 0.255309000 | 1 | 1 | completa | Total; eventos.jsonl línea 11 |
| Inferencia | XGBRegressor | 0.132371100 | 1 | 1 | completa | Total; eventos.jsonl línea 12 |
| Inferencia | XGBRegressor | 0.141169400 | 1 | 1 | completa | Total; eventos.jsonl línea 13 |
| Inferencia | DecisionTreeRegressor | 0.041060700 | 1 | 1 | completa | Total; eventos.jsonl línea 14 |
| Inferencia | DecisionTreeRegressor | 0.040915900 | 1 | 1 | completa | Total; eventos.jsonl línea 15 |
| Inferencia | LinearSVR | 0.056051900 | 1 | 1 | completa | Total; eventos.jsonl línea 16 |
| Inferencia | LinearSVR | 0.053648000 | 1 | 1 | completa | Total; eventos.jsonl línea 17 |
| Inferencia | LinearSVR | 0.045939900 | 1 | 1 | completa | Total; eventos.jsonl línea 18 |
| Inferencia | LinearSVR | 0.053955600 | 1 | 1 | completa | Total; eventos.jsonl línea 19 |
| Inferencia | LinearSVR | 0.056080200 | 1 | 1 | completa | Total; eventos.jsonl línea 20 |
| Inferencia | LinearSVR | 0.053766200 | 1 | 1 | completa | Total; eventos.jsonl línea 21 |
| Inferencia | DecisionTreeRegressor | 0.040660000 | 188 | 1 | completa | Total; eventos.jsonl línea 22 |
| Inferencia | DecisionTreeRegressor | 0.042249600 | 2 | 1 | completa | Total; eventos.jsonl línea 23 |
| Inferencia | LinearSVR | 0.054949700 | 1 | 1 | completa | Total; eventos.jsonl línea 24 |
| Inferencia | LinearSVR | 0.052265400 | 1 | 1 | completa | Total; eventos.jsonl línea 25 |
| Inferencia | LinearSVR | 0.049408100 | 1 | 1 | completa | Total; eventos.jsonl línea 26 |
| Inferencia | LinearSVR | 0.051891000 | 1 | 1 | completa | Total; eventos.jsonl línea 27 |
| Inferencia | XGBRegressor | 0.149057200 | 188 | 1 | completa | Total; eventos.jsonl línea 28 |
| Inferencia | XGBRegressor | 0.148897100 | 188 | 1 | completa | Total; eventos.jsonl línea 29 |
| Inferencia | XGBRegressor | 0.132758200 | 1 | 1 | completa | Total; eventos.jsonl línea 30 |
| Inferencia | XGBRegressor | 0.146584400 | 1 | 1 | completa | Total; eventos.jsonl línea 31 |
| Inferencia | XGBRegressor | 0.135994700 | 1 | 1 | completa | Total; eventos.jsonl línea 32 |
| Inferencia | XGBRegressor | 0.154526500 | 1000 | 1 | completa | Total; eventos.jsonl línea 33 |
| Entrenamiento/refit | Ridge | 0.008221100 | 1000 | 1 | completa | Total; eventos.jsonl línea 34 |
| Inferencia | Ridge | 0.001030400 | 1000 | 1 | completa | Total; eventos.jsonl línea 35 |
| Inferencia | Ridge | 0.000833600 | 1 | 1 | completa | Total; eventos.jsonl línea 36 |
| Inferencia | XGBRegressor | 0.113468300 | 1 | 1 | completa | Total; eventos.jsonl línea 37 |
| Inferencia | XGBRegressor | 0.125848400 | 1 | 1 | completa | Total; eventos.jsonl línea 38 |
| Inferencia | XGBRegressor | 0.196432100 | 1000 | 1 | completa | Total; eventos.jsonl línea 39 |
| Entrenamiento/refit | Ridge | 0.008498000 | 1000 | 1 | completa | Total; eventos.jsonl línea 40 |
| Inferencia | Ridge | 0.001130600 | 1000 | 1 | completa | Total; eventos.jsonl línea 41 |
| Inferencia | Ridge | 0.001051700 | 1 | 1 | completa | Total; eventos.jsonl línea 42 |
| Inferencia | XGBRegressor | 0.118745200 | 1 | 1 | completa | Total; eventos.jsonl línea 43 |
| Inferencia | XGBRegressor | 0.121628000 | 1 | 1 | completa | Total; eventos.jsonl línea 44 |
| Inferencia | XGBRegressor | 0.179382100 | 1000 | 1 | completa | Total; eventos.jsonl línea 45 |
| Entrenamiento/refit | Ridge | 0.009813900 | 1000 | 1 | completa | Total; eventos.jsonl línea 46 |
| Inferencia | Ridge | 0.001343900 | 1000 | 1 | completa | Total; eventos.jsonl línea 47 |
| Inferencia | Ridge | 0.001359600 | 1 | 1 | completa | Total; eventos.jsonl línea 48 |
| Inferencia | XGBRegressor | 0.132387600 | 1 | 1 | completa | Total; eventos.jsonl línea 49 |
| Inferencia | XGBRegressor | 0.161004200 | 1000 | 1 | completa | Total; eventos.jsonl línea 50 |
| Entrenamiento/refit | Ridge | 0.008478800 | 1000 | 1 | completa | Total; eventos.jsonl línea 51 |
| Inferencia | Ridge | 0.001158000 | 1000 | 1 | completa | Total; eventos.jsonl línea 52 |
| Inferencia | Ridge | 0.001052000 | 1 | 1 | completa | Total; eventos.jsonl línea 53 |
| Inferencia | XGBRegressor | 0.106917500 | 1 | 1 | completa | Total; eventos.jsonl línea 54 |
| Inferencia | XGBRegressor | 0.173287400 | 1000 | 1 | completa | Total; eventos.jsonl línea 55 |
| Entrenamiento/refit | Ridge | 0.009545000 | 1000 | 1 | completa | Total; eventos.jsonl línea 56 |
| Inferencia | Ridge | 0.001494200 | 1000 | 1 | completa | Total; eventos.jsonl línea 57 |
| Inferencia | Ridge | 0.001303400 | 1 | 1 | completa | Total; eventos.jsonl línea 58 |
| Inferencia | XGBRegressor | 0.138041200 | 1 | 1 | completa | Total; eventos.jsonl línea 59 |
| Inferencia | TransformedTargetRegressor | 0.116750700 | 1 | 1 | completa | Total; eventos.jsonl línea 60 |
| Inferencia | TransformedTargetRegressor | 0.111201300 | 188 | 1 | completa | Total; eventos.jsonl línea 61 |
| Inferencia | XGBRegressor | 0.182403800 | 1497 | 1 | completa | Total; eventos.jsonl línea 62 |
| Total del experimento | Verificación/preparación · --tests | 274.438939100 | No aplica | 1 | completa | Total; eventos.jsonl línea 63 |

### Ejecución `20261019_090042_b3d84e4a`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T09:00:42.456833-05:00 a 2026-10-19T09:00:44.775510-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_090042_b3d84e4a/metadata.json](tiempos/20261019_090042_b3d84e4a/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_090042_b3d84e4a/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.167733900 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.392711000 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 1.624725400 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.001913300 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 2.312199400 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_090134_e5376dcc`

- **Modelo/motivo:** TransformedTargetRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:01:34.614921-05:00 a 2026-10-19T09:01:34.839405-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_090134_e5376dcc/metadata.json](tiempos/20261019_090134_e5376dcc/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_090134_e5376dcc/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.113111600 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TransformedTargetRegressor · inferencia de aplicación | 0.225004100 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_090134_019a554f`

- **Modelo/motivo:** TruncatedNewtonKernelRidgeRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:01:34.947483-05:00 a 2026-10-19T09:01:35.114373-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_090134_019a554f/metadata.json](tiempos/20261019_090134_019a554f/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_090134_019a554f/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.107149000 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TruncatedNewtonKernelRidgeRegressor · inferencia de aplicación | 0.156179400 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_090017_649e03bf`

- **Modelo/motivo:** Verificación/preparación · Dash/validate_package.py.
- **Fecha/zona:** 2026-10-19T09:00:17.879327-05:00 a 2026-10-19T09:01:54.155224-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_090017_649e03bf/metadata.json](tiempos/20261019_090017_649e03bf/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_090017_649e03bf/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | XGBRegressor | 0.195888100 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | TransformedTargetRegressor | 0.164249700 | 188 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | TruncatedNewtonKernelRidgeRegressor | 0.090053700 | 188 | 1 | completa | Total; eventos.jsonl línea 3 |
| Inferencia | TransformedTargetRegressor | 0.062615600 | 1 | 1 | completa | Total; eventos.jsonl línea 4 |
| Inferencia | TruncatedNewtonKernelRidgeRegressor | 0.054963700 | 1 | 1 | completa | Total; eventos.jsonl línea 5 |
| Inferencia | DecisionTreeRegressor | 0.042288000 | 188 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | LinearSVR | 0.057910800 | 188 | 1 | completa | Total; eventos.jsonl línea 7 |
| Inferencia | KNeighborsRegressor | 0.150797000 | 188 | 1 | completa | Total; eventos.jsonl línea 8 |
| Inferencia | Ridge | 0.001267700 | 188 | 1 | completa | Total; eventos.jsonl línea 9 |
| Inferencia | Ridge | 0.064425400 | 188 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | Lasso | 0.059073300 | 188 | 1 | completa | Total; eventos.jsonl línea 11 |
| Inferencia | RandomForestRegressor | 0.400263400 | 188 | 1 | completa | Total; eventos.jsonl línea 12 |
| Inferencia | XGBRegressor | 0.144987600 | 188 | 1 | completa | Total; eventos.jsonl línea 13 |
| Inferencia | DecisionTreeRegressor | 0.044436200 | 188 | 1 | completa | Total; eventos.jsonl línea 14 |
| Inferencia | XGBRegressor | 0.123842800 | 1 | 1 | completa | Total; eventos.jsonl línea 15 |
| Inferencia | XGBRegressor | 0.197355200 | 1000 | 1 | completa | Total; eventos.jsonl línea 16 |
| Entrenamiento/refit | Ridge | 0.009936200 | 1000 | 1 | completa | Total; eventos.jsonl línea 17 |
| Inferencia | Ridge | 0.001284400 | 1000 | 1 | completa | Total; eventos.jsonl línea 18 |
| Inferencia | Ridge | 0.001189800 | 1 | 1 | completa | Total; eventos.jsonl línea 19 |
| Inferencia | XGBRegressor | 0.130732600 | 1 | 1 | completa | Total; eventos.jsonl línea 20 |
| Total del experimento | Verificación/preparación · Dash/validate_package.py | 96.274236000 | No aplica | 1 | completa | Total; eventos.jsonl línea 21 |

### Ejecución `20261019_091708_44a4301d`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T09:17:08.965587-05:00 a 2026-10-19T09:17:12.241673-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_091708_44a4301d/metadata.json](tiempos/20261019_091708_44a4301d/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_091708_44a4301d/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.175814300 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.267860700 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 1.555558900 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.001990500 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 3.273404900 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_092406_ebd27d72`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T09:24:06.633297-05:00 a 2026-10-19T09:24:10.451542-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_092406_ebd27d72/metadata.json](tiempos/20261019_092406_ebd27d72/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_092406_ebd27d72/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.231274800 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.280508900 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 1.871392500 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.002321200 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 3.815510800 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_092946_31a25f94`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T09:29:46.690114-05:00 a 2026-10-19T09:29:50.617851-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_092946_31a25f94/metadata.json](tiempos/20261019_092946_31a25f94/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_092946_31a25f94/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.236709100 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.334234100 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 1.931176300 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.003234400 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 3.923352100 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_093342_cdbfe655`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T09:33:42.095271-05:00 a 2026-10-19T09:33:44.094616-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_093342_cdbfe655/metadata.json](tiempos/20261019_093342_cdbfe655/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_093342_cdbfe655/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.139158200 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.377650400 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 1.386306400 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.001490400 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 1.995429200 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_093342_f8547616`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T09:33:42.029930-05:00 a 2026-10-19T09:33:44.421238-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_093342_f8547616/metadata.json](tiempos/20261019_093342_f8547616/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_093342_f8547616/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.154539700 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.181955000 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 1.316502300 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.001842200 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 2.388943400 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_093415_1c5c50a4`

- **Modelo/motivo:** KNeighborsRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:34:15.584850-05:00 a 2026-10-19T09:34:15.781141-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_093415_1c5c50a4/metadata.json](tiempos/20261019_093415_1c5c50a4/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_093415_1c5c50a4/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.154233600 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | KNeighborsRegressor · inferencia de aplicación | 0.191752400 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_093416_a0c58ff3`

- **Modelo/motivo:** Ridge · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:34:16.049199-05:00 a 2026-10-19T09:34:16.189825-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_093416_a0c58ff3/metadata.json](tiempos/20261019_093416_a0c58ff3/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_093416_a0c58ff3/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.087016400 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Ridge · inferencia de aplicación | 0.136965600 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_093416_fce04f3a`

- **Modelo/motivo:** Lasso · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:34:16.399269-05:00 a 2026-10-19T09:34:16.553253-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_093416_fce04f3a/metadata.json](tiempos/20261019_093416_fce04f3a/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_093416_fce04f3a/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.102287300 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Lasso · inferencia de aplicación | 0.148608100 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_093420_f9e7a25f`

- **Modelo/motivo:** RandomForestRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:34:20.976500-05:00 a 2026-10-19T09:34:22.173539-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_093420_f9e7a25f/metadata.json](tiempos/20261019_093420_f9e7a25f/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_093420_f9e7a25f/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 1.113403300 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | RandomForestRegressor · inferencia de aplicación | 1.192916100 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_093423_ac176852`

- **Modelo/motivo:** XGBRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:34:23.245408-05:00 a 2026-10-19T09:34:23.471917-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_093423_ac176852/metadata.json](tiempos/20261019_093423_ac176852/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_093423_ac176852/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.173800000 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | XGBRegressor · inferencia de aplicación | 0.216628800 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_093423_af22acf2`

- **Modelo/motivo:** DecisionTreeRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:34:23.721911-05:00 a 2026-10-19T09:34:23.832336-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_093423_af22acf2/metadata.json](tiempos/20261019_093423_af22acf2/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_093423_af22acf2/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.062286900 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | DecisionTreeRegressor · inferencia de aplicación | 0.104020700 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_093506_d324dbad`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:35:06.400051-05:00 a 2026-10-19T09:35:06.548464-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_093506_d324dbad/metadata.json](tiempos/20261019_093506_d324dbad/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_093506_d324dbad/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.100805900 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.143107400 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_093506_361ed191`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:35:06.757112-05:00 a 2026-10-19T09:35:06.874996-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_093506_361ed191/metadata.json](tiempos/20261019_093506_361ed191/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_093506_361ed191/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.087828200 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.121823900 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_093506_53f3b279`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:35:06.942154-05:00 a 2026-10-19T09:35:07.071429-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_093506_53f3b279/metadata.json](tiempos/20261019_093506_53f3b279/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_093506_53f3b279/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.074233100 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.115406200 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_093507_bab5a888`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:35:07.141566-05:00 a 2026-10-19T09:35:07.271390-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_093507_bab5a888/metadata.json](tiempos/20261019_093507_bab5a888/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_093507_bab5a888/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.081482000 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.117207600 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_093507_26a6b236`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:35:07.357835-05:00 a 2026-10-19T09:35:07.475856-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_093507_26a6b236/metadata.json](tiempos/20261019_093507_26a6b236/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_093507_26a6b236/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.086179500 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.125697700 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_093632_49fa1ac6`

- **Modelo/motivo:** TransformedTargetRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:36:32.996196-05:00 a 2026-10-19T09:36:33.273258-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_093632_49fa1ac6/metadata.json](tiempos/20261019_093632_49fa1ac6/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_093632_49fa1ac6/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.221294700 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TransformedTargetRegressor · inferencia de aplicación | 0.274360300 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_093650_c8096b3d`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T09:36:50.731035-05:00 a 2026-10-19T09:36:53.386583-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_093650_c8096b3d/metadata.json](tiempos/20261019_093650_c8096b3d/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_093650_c8096b3d/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.205183800 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.542443700 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 1.825627100 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.002222100 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 2.651257400 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_093700_8ebf99f9`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T09:37:00.481930-05:00 a 2026-10-19T09:37:03.461467-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_093700_8ebf99f9/metadata.json](tiempos/20261019_093700_8ebf99f9/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_093700_8ebf99f9/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.191903200 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.200005800 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 1.387794000 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.002249300 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 2.976999000 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_093317_66078f45`

- **Modelo/motivo:** Verificación/preparación · --tests.
- **Fecha/zona:** 2026-10-19T09:33:17.503425-05:00 a 2026-10-19T09:38:08.530624-05:00; America/Bogota.
- **Estado:** fallida. **Entorno/configuración/código/datos:** [tiempos/20261019_093317_66078f45/metadata.json](tiempos/20261019_093317_66078f45/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_093317_66078f45/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | XGBRegressor | 0.213837400 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | KNeighborsRegressor | 0.114557700 | 1 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | KNeighborsRegressor | 0.047804000 | 1 | 1 | completa | Total; eventos.jsonl línea 3 |
| Inferencia | Ridge | 0.001904200 | 1 | 1 | completa | Total; eventos.jsonl línea 4 |
| Inferencia | Ridge | 0.049938200 | 1 | 1 | completa | Total; eventos.jsonl línea 5 |
| Inferencia | Ridge | 0.001087100 | 1 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | Ridge | 0.062869900 | 1 | 1 | completa | Total; eventos.jsonl línea 7 |
| Inferencia | Lasso | 0.058214900 | 1 | 1 | completa | Total; eventos.jsonl línea 8 |
| Inferencia | Lasso | 0.053704900 | 1 | 1 | completa | Total; eventos.jsonl línea 9 |
| Inferencia | RandomForestRegressor | 0.265553800 | 1 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | RandomForestRegressor | 0.265137900 | 1 | 1 | completa | Total; eventos.jsonl línea 11 |
| Inferencia | XGBRegressor | 0.106872100 | 1 | 1 | completa | Total; eventos.jsonl línea 12 |
| Inferencia | XGBRegressor | 0.106192800 | 1 | 1 | completa | Total; eventos.jsonl línea 13 |
| Inferencia | DecisionTreeRegressor | 0.032171500 | 1 | 1 | completa | Total; eventos.jsonl línea 14 |
| Inferencia | DecisionTreeRegressor | 0.033448600 | 1 | 1 | completa | Total; eventos.jsonl línea 15 |
| Inferencia | LinearSVR | 0.063927000 | 1 | 1 | completa | Total; eventos.jsonl línea 16 |
| Inferencia | LinearSVR | 0.054853400 | 1 | 1 | completa | Total; eventos.jsonl línea 17 |
| Inferencia | LinearSVR | 0.055385900 | 1 | 1 | completa | Total; eventos.jsonl línea 18 |
| Inferencia | LinearSVR | 0.043827500 | 1 | 1 | completa | Total; eventos.jsonl línea 19 |
| Inferencia | LinearSVR | 0.044274900 | 1 | 1 | completa | Total; eventos.jsonl línea 20 |
| Inferencia | LinearSVR | 0.054604900 | 1 | 1 | completa | Total; eventos.jsonl línea 21 |
| Inferencia | DecisionTreeRegressor | 0.033853900 | 188 | 1 | completa | Total; eventos.jsonl línea 22 |
| Inferencia | DecisionTreeRegressor | 0.037712400 | 2 | 1 | completa | Total; eventos.jsonl línea 23 |
| Inferencia | LinearSVR | 0.041610200 | 1 | 1 | completa | Total; eventos.jsonl línea 24 |
| Inferencia | LinearSVR | 0.049677000 | 1 | 1 | completa | Total; eventos.jsonl línea 25 |
| Inferencia | LinearSVR | 0.046744800 | 1 | 1 | completa | Total; eventos.jsonl línea 26 |
| Inferencia | LinearSVR | 0.043675000 | 1 | 1 | completa | Total; eventos.jsonl línea 27 |
| Inferencia | XGBRegressor | 0.109049600 | 188 | 1 | completa | Total; eventos.jsonl línea 28 |
| Inferencia | XGBRegressor | 0.114009600 | 188 | 1 | completa | Total; eventos.jsonl línea 29 |
| Inferencia | XGBRegressor | 0.100620400 | 1 | 1 | completa | Total; eventos.jsonl línea 30 |
| Inferencia | XGBRegressor | 0.106152300 | 1 | 1 | completa | Total; eventos.jsonl línea 31 |
| Inferencia | XGBRegressor | 0.102246800 | 1 | 1 | completa | Total; eventos.jsonl línea 32 |
| Inferencia | XGBRegressor | 0.162936300 | 1000 | 1 | completa | Total; eventos.jsonl línea 33 |
| Entrenamiento/refit | Ridge | 0.007152400 | 1000 | 1 | completa | Total; eventos.jsonl línea 34 |
| Inferencia | Ridge | 0.001329900 | 1000 | 1 | completa | Total; eventos.jsonl línea 35 |
| Inferencia | Ridge | 0.000785500 | 1 | 1 | completa | Total; eventos.jsonl línea 36 |
| Inferencia | XGBRegressor | 0.106816600 | 1 | 1 | completa | Total; eventos.jsonl línea 37 |
| Inferencia | XGBRegressor | 0.113291600 | 1 | 1 | completa | Total; eventos.jsonl línea 38 |
| Inferencia | XGBRegressor | 0.235441200 | 1000 | 1 | completa | Total; eventos.jsonl línea 39 |
| Entrenamiento/refit | Ridge | 0.011039300 | 1000 | 1 | completa | Total; eventos.jsonl línea 40 |
| Inferencia | Ridge | 0.001862300 | 1000 | 1 | completa | Total; eventos.jsonl línea 41 |
| Inferencia | Ridge | 0.001917500 | 1 | 1 | completa | Total; eventos.jsonl línea 42 |
| Inferencia | XGBRegressor | 0.151173400 | 1 | 1 | completa | Total; eventos.jsonl línea 43 |
| Inferencia | XGBRegressor | 0.113572900 | 1 | 1 | completa | Total; eventos.jsonl línea 44 |
| Inferencia | XGBRegressor | 0.158692800 | 1000 | 1 | completa | Total; eventos.jsonl línea 45 |
| Entrenamiento/refit | Ridge | 0.009540600 | 1000 | 1 | completa | Total; eventos.jsonl línea 46 |
| Inferencia | Ridge | 0.001116900 | 1000 | 1 | completa | Total; eventos.jsonl línea 47 |
| Inferencia | Ridge | 0.000826000 | 1 | 1 | completa | Total; eventos.jsonl línea 48 |
| Inferencia | XGBRegressor | 0.114303300 | 1 | 1 | completa | Total; eventos.jsonl línea 49 |
| Inferencia | XGBRegressor | 0.148060900 | 1000 | 1 | completa | Total; eventos.jsonl línea 50 |
| Entrenamiento/refit | Ridge | 0.008481100 | 1000 | 1 | completa | Total; eventos.jsonl línea 51 |
| Inferencia | Ridge | 0.001175300 | 1000 | 1 | completa | Total; eventos.jsonl línea 52 |
| Inferencia | Ridge | 0.001047300 | 1 | 1 | completa | Total; eventos.jsonl línea 53 |
| Inferencia | XGBRegressor | 0.139576300 | 1 | 1 | completa | Total; eventos.jsonl línea 54 |
| Inferencia | XGBRegressor | 0.155551100 | 1000 | 1 | completa | Total; eventos.jsonl línea 55 |
| Entrenamiento/refit | Ridge | 0.007094100 | 1000 | 1 | completa | Total; eventos.jsonl línea 56 |
| Inferencia | Ridge | 0.001577800 | 1000 | 1 | completa | Total; eventos.jsonl línea 57 |
| Inferencia | Ridge | 0.000956500 | 1 | 1 | completa | Total; eventos.jsonl línea 58 |
| Inferencia | XGBRegressor | 0.109287400 | 1 | 1 | completa | Total; eventos.jsonl línea 59 |
| Inferencia | TransformedTargetRegressor | 0.136206200 | 1 | 1 | completa | Total; eventos.jsonl línea 60 |
| Inferencia | TransformedTargetRegressor | 0.206178700 | 188 | 1 | completa | Total; eventos.jsonl línea 61 |
| Inferencia | XGBRegressor | 0.305717300 | 1497 | 1 | completa | Total; eventos.jsonl línea 62 |
| Total del experimento | Verificación/preparación · --tests | 291.022340700 | No aplica | 1 | fallida | Total; eventos.jsonl línea 63 |

### Ejecución `20261019_094013_b649d3af`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T09:40:13.718701-05:00 a 2026-10-19T09:40:15.844295-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_094013_b649d3af/metadata.json](tiempos/20261019_094013_b649d3af/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_094013_b649d3af/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.170897500 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.362453600 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 1.450926100 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.003075300 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 2.116533700 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_094047_1e6e3d6a`

- **Modelo/motivo:** KNeighborsRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:40:47.197637-05:00 a 2026-10-19T09:40:47.373073-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_094047_1e6e3d6a/metadata.json](tiempos/20261019_094047_1e6e3d6a/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_094047_1e6e3d6a/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.131297900 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | KNeighborsRegressor · inferencia de aplicación | 0.164660900 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_094047_41b15f04`

- **Modelo/motivo:** Ridge · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:40:47.576557-05:00 a 2026-10-19T09:40:47.703715-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_094047_41b15f04/metadata.json](tiempos/20261019_094047_41b15f04/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_094047_41b15f04/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.081544700 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Ridge · inferencia de aplicación | 0.115800100 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_094047_6bbb9ed9`

- **Modelo/motivo:** Lasso · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:40:47.883245-05:00 a 2026-10-19T09:40:48.011962-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_094047_6bbb9ed9/metadata.json](tiempos/20261019_094047_6bbb9ed9/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_094047_6bbb9ed9/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.079772400 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Lasso · inferencia de aplicación | 0.124620200 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_094050_45549043`

- **Modelo/motivo:** RandomForestRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:40:50.089875-05:00 a 2026-10-19T09:40:51.199694-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_094050_45549043/metadata.json](tiempos/20261019_094050_45549043/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_094050_45549043/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 1.035789500 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | RandomForestRegressor · inferencia de aplicación | 1.106334800 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_094052_90e45074`

- **Modelo/motivo:** XGBRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:40:52.150414-05:00 a 2026-10-19T09:40:52.347564-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_094052_90e45074/metadata.json](tiempos/20261019_094052_90e45074/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_094052_90e45074/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.164951600 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | XGBRegressor · inferencia de aplicación | 0.199145100 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_094052_1e4a3d68`

- **Modelo/motivo:** DecisionTreeRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:40:52.609010-05:00 a 2026-10-19T09:40:52.705039-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_094052_1e4a3d68/metadata.json](tiempos/20261019_094052_1e4a3d68/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_094052_1e4a3d68/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.055752700 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | DecisionTreeRegressor · inferencia de aplicación | 0.095303000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_094135_002f7422`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:41:35.680606-05:00 a 2026-10-19T09:41:35.804706-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_094135_002f7422/metadata.json](tiempos/20261019_094135_002f7422/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_094135_002f7422/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.082321800 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.121340600 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_094136_8e2e7089`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:41:36.012742-05:00 a 2026-10-19T09:41:36.146806-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_094136_8e2e7089/metadata.json](tiempos/20261019_094136_8e2e7089/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_094136_8e2e7089/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.086279800 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.122332900 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_094136_2047d9ba`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:41:36.217002-05:00 a 2026-10-19T09:41:36.350459-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_094136_2047d9ba/metadata.json](tiempos/20261019_094136_2047d9ba/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_094136_2047d9ba/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.087187100 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.130133300 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_094136_62ee5300`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:41:36.462484-05:00 a 2026-10-19T09:41:36.638035-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_094136_62ee5300/metadata.json](tiempos/20261019_094136_62ee5300/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_094136_62ee5300/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.124582500 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.173059900 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_094136_03cdb2ff`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:41:36.777337-05:00 a 2026-10-19T09:41:36.961258-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_094136_03cdb2ff/metadata.json](tiempos/20261019_094136_03cdb2ff/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_094136_03cdb2ff/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.132000000 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.180155700 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_094244_bd480f27`

- **Modelo/motivo:** TransformedTargetRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:42:44.018553-05:00 a 2026-10-19T09:42:44.202920-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_094244_bd480f27/metadata.json](tiempos/20261019_094244_bd480f27/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_094244_bd480f27/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.155895100 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TransformedTargetRegressor · inferencia de aplicación | 0.190663600 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_094254_57ced150`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T09:42:54.593302-05:00 a 2026-10-19T09:42:56.316834-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_094254_57ced150/metadata.json](tiempos/20261019_094254_57ced150/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_094254_57ced150/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.123132100 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.318277600 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 1.218581400 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.001470300 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 1.716937900 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_093953_8c56a92b`

- **Modelo/motivo:** Verificación/preparación · --tests.
- **Fecha/zona:** 2026-10-19T09:39:53.949858-05:00 a 2026-10-19T09:43:53.920390-05:00; America/Bogota.
- **Estado:** fallida. **Entorno/configuración/código/datos:** [tiempos/20261019_093953_8c56a92b/metadata.json](tiempos/20261019_093953_8c56a92b/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_093953_8c56a92b/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | XGBRegressor | 0.192820700 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | KNeighborsRegressor | 0.091538200 | 1 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | KNeighborsRegressor | 0.038460000 | 1 | 1 | completa | Total; eventos.jsonl línea 3 |
| Inferencia | Ridge | 0.000908000 | 1 | 1 | completa | Total; eventos.jsonl línea 4 |
| Inferencia | Ridge | 0.048211200 | 1 | 1 | completa | Total; eventos.jsonl línea 5 |
| Inferencia | Ridge | 0.000992600 | 1 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | Ridge | 0.052966700 | 1 | 1 | completa | Total; eventos.jsonl línea 7 |
| Inferencia | Lasso | 0.046476600 | 1 | 1 | completa | Total; eventos.jsonl línea 8 |
| Inferencia | Lasso | 0.039931200 | 1 | 1 | completa | Total; eventos.jsonl línea 9 |
| Inferencia | RandomForestRegressor | 0.231175900 | 1 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | RandomForestRegressor | 0.236054400 | 1 | 1 | completa | Total; eventos.jsonl línea 11 |
| Inferencia | XGBRegressor | 0.100433800 | 1 | 1 | completa | Total; eventos.jsonl línea 12 |
| Inferencia | XGBRegressor | 0.105735900 | 1 | 1 | completa | Total; eventos.jsonl línea 13 |
| Inferencia | DecisionTreeRegressor | 0.029790900 | 1 | 1 | completa | Total; eventos.jsonl línea 14 |
| Inferencia | DecisionTreeRegressor | 0.029895500 | 1 | 1 | completa | Total; eventos.jsonl línea 15 |
| Inferencia | LinearSVR | 0.040867700 | 1 | 1 | completa | Total; eventos.jsonl línea 16 |
| Inferencia | LinearSVR | 0.051277200 | 1 | 1 | completa | Total; eventos.jsonl línea 17 |
| Inferencia | LinearSVR | 0.045403400 | 1 | 1 | completa | Total; eventos.jsonl línea 18 |
| Inferencia | LinearSVR | 0.054334600 | 1 | 1 | completa | Total; eventos.jsonl línea 19 |
| Inferencia | LinearSVR | 0.067456600 | 1 | 1 | completa | Total; eventos.jsonl línea 20 |
| Inferencia | LinearSVR | 0.076214100 | 1 | 1 | completa | Total; eventos.jsonl línea 21 |
| Inferencia | DecisionTreeRegressor | 0.033531300 | 188 | 1 | completa | Total; eventos.jsonl línea 22 |
| Inferencia | DecisionTreeRegressor | 0.033543300 | 2 | 1 | completa | Total; eventos.jsonl línea 23 |
| Inferencia | LinearSVR | 0.039989200 | 1 | 1 | completa | Total; eventos.jsonl línea 24 |
| Inferencia | LinearSVR | 0.046801700 | 1 | 1 | completa | Total; eventos.jsonl línea 25 |
| Inferencia | LinearSVR | 0.036430100 | 1 | 1 | completa | Total; eventos.jsonl línea 26 |
| Inferencia | LinearSVR | 0.038981800 | 1 | 1 | completa | Total; eventos.jsonl línea 27 |
| Inferencia | XGBRegressor | 0.118228400 | 188 | 1 | completa | Total; eventos.jsonl línea 28 |
| Inferencia | XGBRegressor | 0.122197600 | 188 | 1 | completa | Total; eventos.jsonl línea 29 |
| Inferencia | XGBRegressor | 0.110259300 | 1 | 1 | completa | Total; eventos.jsonl línea 30 |
| Inferencia | XGBRegressor | 0.106120900 | 1 | 1 | completa | Total; eventos.jsonl línea 31 |
| Inferencia | XGBRegressor | 0.111200400 | 1 | 1 | completa | Total; eventos.jsonl línea 32 |
| Inferencia | XGBRegressor | 0.169740500 | 1000 | 1 | completa | Total; eventos.jsonl línea 33 |
| Entrenamiento/refit | Ridge | 0.007176800 | 1000 | 1 | completa | Total; eventos.jsonl línea 34 |
| Inferencia | Ridge | 0.001325700 | 1000 | 1 | completa | Total; eventos.jsonl línea 35 |
| Inferencia | Ridge | 0.000948400 | 1 | 1 | completa | Total; eventos.jsonl línea 36 |
| Inferencia | XGBRegressor | 0.154256600 | 1 | 1 | completa | Total; eventos.jsonl línea 37 |
| Inferencia | XGBRegressor | 0.125707700 | 1 | 1 | completa | Total; eventos.jsonl línea 38 |
| Inferencia | XGBRegressor | 0.151726000 | 1000 | 1 | completa | Total; eventos.jsonl línea 39 |
| Entrenamiento/refit | Ridge | 0.007553000 | 1000 | 1 | completa | Total; eventos.jsonl línea 40 |
| Inferencia | Ridge | 0.001021800 | 1000 | 1 | completa | Total; eventos.jsonl línea 41 |
| Inferencia | Ridge | 0.001195400 | 1 | 1 | completa | Total; eventos.jsonl línea 42 |
| Inferencia | XGBRegressor | 0.112996600 | 1 | 1 | completa | Total; eventos.jsonl línea 43 |
| Inferencia | XGBRegressor | 0.126642100 | 1 | 1 | completa | Total; eventos.jsonl línea 44 |
| Inferencia | XGBRegressor | 0.169166700 | 1000 | 1 | completa | Total; eventos.jsonl línea 45 |
| Entrenamiento/refit | Ridge | 0.008386100 | 1000 | 1 | completa | Total; eventos.jsonl línea 46 |
| Inferencia | Ridge | 0.003168100 | 1000 | 1 | completa | Total; eventos.jsonl línea 47 |
| Inferencia | Ridge | 0.001363700 | 1 | 1 | completa | Total; eventos.jsonl línea 48 |
| Inferencia | XGBRegressor | 0.184720900 | 1 | 1 | completa | Total; eventos.jsonl línea 49 |
| Inferencia | XGBRegressor | 0.190561100 | 1000 | 1 | completa | Total; eventos.jsonl línea 50 |
| Entrenamiento/refit | Ridge | 0.008724300 | 1000 | 1 | completa | Total; eventos.jsonl línea 51 |
| Inferencia | Ridge | 0.001093900 | 1000 | 1 | completa | Total; eventos.jsonl línea 52 |
| Inferencia | Ridge | 0.000951200 | 1 | 1 | completa | Total; eventos.jsonl línea 53 |
| Inferencia | XGBRegressor | 0.110008100 | 1 | 1 | completa | Total; eventos.jsonl línea 54 |
| Inferencia | XGBRegressor | 0.144605500 | 1000 | 1 | completa | Total; eventos.jsonl línea 55 |
| Entrenamiento/refit | Ridge | 0.008921100 | 1000 | 1 | completa | Total; eventos.jsonl línea 56 |
| Inferencia | Ridge | 0.001167900 | 1000 | 1 | completa | Total; eventos.jsonl línea 57 |
| Inferencia | Ridge | 0.000937400 | 1 | 1 | completa | Total; eventos.jsonl línea 58 |
| Inferencia | XGBRegressor | 0.110274300 | 1 | 1 | completa | Total; eventos.jsonl línea 59 |
| Inferencia | TransformedTargetRegressor | 0.107026000 | 1 | 1 | completa | Total; eventos.jsonl línea 60 |
| Inferencia | TransformedTargetRegressor | 0.069363400 | 188 | 1 | completa | Total; eventos.jsonl línea 61 |
| Inferencia | XGBRegressor | 0.156659400 | 1497 | 1 | completa | Total; eventos.jsonl línea 62 |
| Total del experimento | Verificación/preparación · --tests | 239.965989000 | No aplica | 1 | fallida | Total; eventos.jsonl línea 63 |

### Ejecución `20261019_094733_8be77852`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T09:47:33.452406-05:00 a 2026-10-19T09:47:36.451497-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_094733_8be77852/metadata.json](tiempos/20261019_094733_8be77852/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_094733_8be77852/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.147311500 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.189080500 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 1.402157100 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.002466000 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 3.002394000 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_094827_5d29f6d0`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T09:48:27.743155-05:00 a 2026-10-19T09:48:30.067604-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_094827_5d29f6d0/metadata.json](tiempos/20261019_094827_5d29f6d0/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_094827_5d29f6d0/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.123684500 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.193654700 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 1.458721000 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.002477200 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 2.318962900 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_094925_70531600`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T09:49:25.468300-05:00 a 2026-10-19T09:49:27.934327-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_094925_70531600/metadata.json](tiempos/20261019_094925_70531600/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_094925_70531600/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.158117700 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.436937200 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 1.747587800 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.002591400 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 2.463507500 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_095009_53cbd9c9`

- **Modelo/motivo:** KNeighborsRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:50:09.643534-05:00 a 2026-10-19T09:50:09.918246-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_095009_53cbd9c9/metadata.json](tiempos/20261019_095009_53cbd9c9/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_095009_53cbd9c9/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.196593000 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | KNeighborsRegressor · inferencia de aplicación | 0.268693700 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_095010_ce27eeb0`

- **Modelo/motivo:** Ridge · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:50:10.290173-05:00 a 2026-10-19T09:50:10.459047-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_095010_ce27eeb0/metadata.json](tiempos/20261019_095010_ce27eeb0/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_095010_ce27eeb0/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.109418000 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Ridge · inferencia de aplicación | 0.164803000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_095010_c769f39b`

- **Modelo/motivo:** Lasso · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:50:10.710840-05:00 a 2026-10-19T09:50:10.871857-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_095010_c769f39b/metadata.json](tiempos/20261019_095010_c769f39b/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_095010_c769f39b/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.097097800 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Lasso · inferencia de aplicación | 0.153399000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_095015_63bec965`

- **Modelo/motivo:** RandomForestRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:50:15.320585-05:00 a 2026-10-19T09:50:17.179703-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_095015_63bec965/metadata.json](tiempos/20261019_095015_63bec965/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_095015_63bec965/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 1.767446300 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | RandomForestRegressor · inferencia de aplicación | 1.854756200 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_095018_8d2e1923`

- **Modelo/motivo:** XGBRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:50:18.585647-05:00 a 2026-10-19T09:50:18.857498-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_095018_8d2e1923/metadata.json](tiempos/20261019_095018_8d2e1923/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_095018_8d2e1923/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.205796900 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | XGBRegressor · inferencia de aplicación | 0.268960900 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_095019_9dd50309`

- **Modelo/motivo:** DecisionTreeRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:50:19.166119-05:00 a 2026-10-19T09:50:19.323485-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_095019_9dd50309/metadata.json](tiempos/20261019_095019_9dd50309/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_095019_9dd50309/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.101563300 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | DecisionTreeRegressor · inferencia de aplicación | 0.153121700 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_095110_caf08ff6`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:51:10.804393-05:00 a 2026-10-19T09:51:10.937551-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_095110_caf08ff6/metadata.json](tiempos/20261019_095110_caf08ff6/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_095110_caf08ff6/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.089193600 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.130199200 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_095111_b4ea2299`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:51:11.208934-05:00 a 2026-10-19T09:51:11.864537-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_095111_b4ea2299/metadata.json](tiempos/20261019_095111_b4ea2299/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_095111_b4ea2299/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.595495900 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.651716700 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_095111_17faba63`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:51:11.960344-05:00 a 2026-10-19T09:51:12.129588-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_095111_17faba63/metadata.json](tiempos/20261019_095111_17faba63/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_095111_17faba63/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.112874800 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.164265100 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_095112_bfaef409`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:51:12.241156-05:00 a 2026-10-19T09:51:12.400196-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_095112_bfaef409/metadata.json](tiempos/20261019_095112_bfaef409/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_095112_bfaef409/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.111429400 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.156372100 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_095112_f95180a2`

- **Modelo/motivo:** LinearSVR · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:51:12.517721-05:00 a 2026-10-19T09:51:12.752148-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_095112_f95180a2/metadata.json](tiempos/20261019_095112_f95180a2/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_095112_f95180a2/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.164123900 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | LinearSVR · inferencia de aplicación | 0.227554800 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_095244_11fba157`

- **Modelo/motivo:** TransformedTargetRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T09:52:44.011804-05:00 a 2026-10-19T09:52:44.257676-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_095244_11fba157/metadata.json](tiempos/20261019_095244_11fba157/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_095244_11fba157/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.207554700 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TransformedTargetRegressor · inferencia de aplicación | 0.243272000 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_095257_6795c6d6`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T09:52:57.248947-05:00 a 2026-10-19T09:52:59.194121-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_095257_6795c6d6/metadata.json](tiempos/20261019_095257_6795c6d6/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_095257_6795c6d6/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.146529700 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.363970500 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 1.374691800 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.001433600 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 1.942497900 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_094903_073f0ac0`

- **Modelo/motivo:** Verificación/preparación · --tests.
- **Fecha/zona:** 2026-10-19T09:49:03.915521-05:00 a 2026-10-19T09:54:07.682923-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_094903_073f0ac0/metadata.json](tiempos/20261019_094903_073f0ac0/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_094903_073f0ac0/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | XGBRegressor | 0.227134200 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | KNeighborsRegressor | 0.149001600 | 1 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | KNeighborsRegressor | 0.077281600 | 1 | 1 | completa | Total; eventos.jsonl línea 3 |
| Inferencia | Ridge | 0.000886900 | 1 | 1 | completa | Total; eventos.jsonl línea 4 |
| Inferencia | Ridge | 0.065815900 | 1 | 1 | completa | Total; eventos.jsonl línea 5 |
| Inferencia | Ridge | 0.000918400 | 1 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | Ridge | 0.057910800 | 1 | 1 | completa | Total; eventos.jsonl línea 7 |
| Inferencia | Lasso | 0.053588100 | 1 | 1 | completa | Total; eventos.jsonl línea 8 |
| Inferencia | Lasso | 0.074651300 | 1 | 1 | completa | Total; eventos.jsonl línea 9 |
| Inferencia | RandomForestRegressor | 0.420194200 | 1 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | RandomForestRegressor | 0.352404300 | 1 | 1 | completa | Total; eventos.jsonl línea 11 |
| Inferencia | XGBRegressor | 0.129274100 | 1 | 1 | completa | Total; eventos.jsonl línea 12 |
| Inferencia | XGBRegressor | 0.133690600 | 1 | 1 | completa | Total; eventos.jsonl línea 13 |
| Inferencia | DecisionTreeRegressor | 0.063398100 | 1 | 1 | completa | Total; eventos.jsonl línea 14 |
| Inferencia | DecisionTreeRegressor | 0.038956100 | 1 | 1 | completa | Total; eventos.jsonl línea 15 |
| Inferencia | LinearSVR | 0.054499800 | 1 | 1 | completa | Total; eventos.jsonl línea 16 |
| Inferencia | LinearSVR | 0.062924800 | 1 | 1 | completa | Total; eventos.jsonl línea 17 |
| Inferencia | LinearSVR | 0.554097200 | 1 | 1 | completa | Total; eventos.jsonl línea 18 |
| Inferencia | LinearSVR | 0.059203200 | 1 | 1 | completa | Total; eventos.jsonl línea 19 |
| Inferencia | LinearSVR | 0.055482500 | 1 | 1 | completa | Total; eventos.jsonl línea 20 |
| Inferencia | LinearSVR | 0.095518300 | 1 | 1 | completa | Total; eventos.jsonl línea 21 |
| Inferencia | DecisionTreeRegressor | 0.052384200 | 188 | 1 | completa | Total; eventos.jsonl línea 22 |
| Inferencia | DecisionTreeRegressor | 0.045901100 | 2 | 1 | completa | Total; eventos.jsonl línea 23 |
| Inferencia | LinearSVR | 0.066156200 | 1 | 1 | completa | Total; eventos.jsonl línea 24 |
| Inferencia | LinearSVR | 0.054219100 | 1 | 1 | completa | Total; eventos.jsonl línea 25 |
| Inferencia | LinearSVR | 0.047346200 | 1 | 1 | completa | Total; eventos.jsonl línea 26 |
| Inferencia | LinearSVR | 0.054753500 | 1 | 1 | completa | Total; eventos.jsonl línea 27 |
| Inferencia | XGBRegressor | 0.298204900 | 188 | 1 | completa | Total; eventos.jsonl línea 28 |
| Inferencia | XGBRegressor | 0.209277400 | 188 | 1 | completa | Total; eventos.jsonl línea 29 |
| Inferencia | XGBRegressor | 0.152320300 | 1 | 1 | completa | Total; eventos.jsonl línea 30 |
| Inferencia | XGBRegressor | 0.147537500 | 1 | 1 | completa | Total; eventos.jsonl línea 31 |
| Inferencia | XGBRegressor | 0.135536500 | 1 | 1 | completa | Total; eventos.jsonl línea 32 |
| Inferencia | XGBRegressor | 0.212754900 | 1000 | 1 | completa | Total; eventos.jsonl línea 33 |
| Entrenamiento/refit | Ridge | 0.009929100 | 1000 | 1 | completa | Total; eventos.jsonl línea 34 |
| Inferencia | Ridge | 0.001292400 | 1000 | 1 | completa | Total; eventos.jsonl línea 35 |
| Inferencia | Ridge | 0.001329300 | 1 | 1 | completa | Total; eventos.jsonl línea 36 |
| Inferencia | XGBRegressor | 0.147394500 | 1 | 1 | completa | Total; eventos.jsonl línea 37 |
| Inferencia | XGBRegressor | 0.114880600 | 1 | 1 | completa | Total; eventos.jsonl línea 38 |
| Inferencia | XGBRegressor | 0.175523900 | 1000 | 1 | completa | Total; eventos.jsonl línea 39 |
| Entrenamiento/refit | Ridge | 0.012440800 | 1000 | 1 | completa | Total; eventos.jsonl línea 40 |
| Inferencia | Ridge | 0.001319200 | 1000 | 1 | completa | Total; eventos.jsonl línea 41 |
| Inferencia | Ridge | 0.001188500 | 1 | 1 | completa | Total; eventos.jsonl línea 42 |
| Inferencia | XGBRegressor | 0.141840200 | 1 | 1 | completa | Total; eventos.jsonl línea 43 |
| Inferencia | XGBRegressor | 0.142169200 | 1 | 1 | completa | Total; eventos.jsonl línea 44 |
| Inferencia | XGBRegressor | 0.201709600 | 1000 | 1 | completa | Total; eventos.jsonl línea 45 |
| Entrenamiento/refit | Ridge | 0.008662300 | 1000 | 1 | completa | Total; eventos.jsonl línea 46 |
| Inferencia | Ridge | 0.001421500 | 1000 | 1 | completa | Total; eventos.jsonl línea 47 |
| Inferencia | Ridge | 0.001234900 | 1 | 1 | completa | Total; eventos.jsonl línea 48 |
| Inferencia | XGBRegressor | 0.147947800 | 1 | 1 | completa | Total; eventos.jsonl línea 49 |
| Inferencia | XGBRegressor | 0.218216300 | 1000 | 1 | completa | Total; eventos.jsonl línea 50 |
| Entrenamiento/refit | Ridge | 0.015756900 | 1000 | 1 | completa | Total; eventos.jsonl línea 51 |
| Inferencia | Ridge | 0.001165600 | 1000 | 1 | completa | Total; eventos.jsonl línea 52 |
| Inferencia | Ridge | 0.001168600 | 1 | 1 | completa | Total; eventos.jsonl línea 53 |
| Inferencia | XGBRegressor | 0.150105500 | 1 | 1 | completa | Total; eventos.jsonl línea 54 |
| Inferencia | XGBRegressor | 0.186249800 | 1000 | 1 | completa | Total; eventos.jsonl línea 55 |
| Entrenamiento/refit | Ridge | 0.009278400 | 1000 | 1 | completa | Total; eventos.jsonl línea 56 |
| Inferencia | Ridge | 0.001723000 | 1000 | 1 | completa | Total; eventos.jsonl línea 57 |
| Inferencia | Ridge | 0.002827500 | 1 | 1 | completa | Total; eventos.jsonl línea 58 |
| Inferencia | XGBRegressor | 0.120131800 | 1 | 1 | completa | Total; eventos.jsonl línea 59 |
| Inferencia | TransformedTargetRegressor | 0.137332100 | 1 | 1 | completa | Total; eventos.jsonl línea 60 |
| Inferencia | TransformedTargetRegressor | 0.081689300 | 188 | 1 | completa | Total; eventos.jsonl línea 61 |
| Inferencia | XGBRegressor | 0.190283700 | 1497 | 1 | completa | Total; eventos.jsonl línea 62 |
| Total del experimento | Verificación/preparación · --tests | 303.763790200 | No aplica | 1 | completa | Total; eventos.jsonl línea 63 |

### Ejecución `20261019_131238_91a9dd64`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T13:12:38.271557-05:00 a 2026-10-19T13:12:38.556089-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_131238_91a9dd64/metadata.json](tiempos/20261019_131238_91a9dd64/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_131238_91a9dd64/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.017324100 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.018639100 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.155801400 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000609400 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.283900800 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_131613_628ca1c8`

- **Modelo/motivo:** TransformedTargetRegressor · inferencia de aplicación.
- **Fecha/zona:** 2026-10-19T13:16:13.779942-05:00 a 2026-10-19T13:16:13.823405-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_131613_628ca1c8/metadata.json](tiempos/20261019_131613_628ca1c8/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_131613_628ca1c8/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | aplicación | 0.031303600 | 1 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | TransformedTargetRegressor · inferencia de aplicación | 0.042894900 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_131901_8ba82b58`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T13:19:01.398367-05:00 a 2026-10-19T13:19:01.655231-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_131901_8ba82b58/metadata.json](tiempos/20261019_131901_8ba82b58/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_131901_8ba82b58/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.021355300 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.046365000 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.153491000 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000395200 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.256725100 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_131858_f832a51c`

- **Modelo/motivo:** Verificación/preparación · Dash\test_original_models.py.
- **Fecha/zona:** 2026-10-19T13:18:58.381409-05:00 a 2026-10-19T13:19:06.036770-05:00; America/Bogota.
- **Estado:** fallida. **Entorno/configuración/código/datos:** [tiempos/20261019_131858_f832a51c/metadata.json](tiempos/20261019_131858_f832a51c/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_131858_f832a51c/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | XGBRegressor | 0.019100800 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Verificación/preparación · Dash\test_original_models.py | 7.659523300 | No aplica | 1 | fallida | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_131926_5a1e6da8`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T13:19:26.660229-05:00 a 2026-10-19T13:19:26.911639-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_131926_5a1e6da8/metadata.json](tiempos/20261019_131926_5a1e6da8/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_131926_5a1e6da8/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.021385700 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.050250600 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.151639500 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000351300 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.252189300 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_131923_33596b82`

- **Modelo/motivo:** Verificación/preparación · Dash\prepare_deployment.py.
- **Fecha/zona:** 2026-10-19T13:19:23.517064-05:00 a 2026-10-19T13:19:27.965449-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_131923_33596b82/metadata.json](tiempos/20261019_131923_33596b82/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_131923_33596b82/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | XGBRegressor | 0.020115000 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Total del experimento | Verificación/preparación · Dash\prepare_deployment.py | 4.438793800 | No aplica | 1 | completa | Total; eventos.jsonl línea 2 |

### Ejecución `20261019_131942_d9a2909e`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T13:19:42.673090-05:00 a 2026-10-19T13:19:42.909199-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_131942_d9a2909e/metadata.json](tiempos/20261019_131942_d9a2909e/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_131942_d9a2909e/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.018263700 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.042670100 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.152468500 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000520700 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.235402000 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_131939_efed6f19`

- **Modelo/motivo:** Verificación/preparación · ..\RenderDeploy\Dash\validate_package.py.
- **Fecha/zona:** 2026-10-19T13:19:39.445671-05:00 a 2026-10-19T13:19:50.219172-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_131939_efed6f19/metadata.json](tiempos/20261019_131939_efed6f19/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_131939_efed6f19/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | XGBRegressor | 0.020284700 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | TransformedTargetRegressor | 0.031255400 | 188 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | TruncatedNewtonKernelRidgeRegressor | 0.011932500 | 188 | 1 | completa | Total; eventos.jsonl línea 3 |
| Inferencia | DecisionTreeRegressor | 0.005135700 | 188 | 1 | completa | Total; eventos.jsonl línea 4 |
| Inferencia | LinearSVR | 0.005422200 | 188 | 1 | completa | Total; eventos.jsonl línea 5 |
| Inferencia | KNeighborsRegressor | 0.032111100 | 188 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | Ridge | 0.000149900 | 188 | 1 | completa | Total; eventos.jsonl línea 7 |
| Inferencia | Ridge | 0.008345400 | 188 | 1 | completa | Total; eventos.jsonl línea 8 |
| Inferencia | Lasso | 0.006252700 | 188 | 1 | completa | Total; eventos.jsonl línea 9 |
| Inferencia | RandomForestRegressor | 0.032162600 | 188 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | XGBRegressor | 0.012850200 | 188 | 1 | completa | Total; eventos.jsonl línea 11 |
| Inferencia | DecisionTreeRegressor | 0.003974000 | 188 | 1 | completa | Total; eventos.jsonl línea 12 |
| Inferencia | XGBRegressor | 0.012214100 | 1 | 1 | completa | Total; eventos.jsonl línea 13 |
| Inferencia | XGBRegressor | 0.022831400 | 1000 | 1 | completa | Total; eventos.jsonl línea 14 |
| Entrenamiento/refit | Ridge | 0.003975300 | 1000 | 1 | completa | Total; eventos.jsonl línea 15 |
| Inferencia | Ridge | 0.000184000 | 1000 | 1 | completa | Total; eventos.jsonl línea 16 |
| Inferencia | Ridge | 0.000104900 | 1 | 1 | completa | Total; eventos.jsonl línea 17 |
| Inferencia | XGBRegressor | 0.011272600 | 1 | 1 | completa | Total; eventos.jsonl línea 18 |
| Total del experimento | Verificación/preparación · ..\RenderDeploy\Dash\validate_package.py | 10.768957500 | No aplica | 1 | completa | Total; eventos.jsonl línea 19 |

### Ejecución `20261019_132158_1ab868b0`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T13:21:58.576157-05:00 a 2026-10-19T13:21:58.834401-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_132158_1ab868b0/metadata.json](tiempos/20261019_132158_1ab868b0/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_132158_1ab868b0/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.013772500 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.016205400 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.149046800 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000514200 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.259076300 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_132355_4b56185c`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T13:23:55.276940-05:00 a 2026-10-19T13:23:55.539753-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_132355_4b56185c/metadata.json](tiempos/20261019_132355_4b56185c/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_132355_4b56185c/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.014626100 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.016617900 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.149106000 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000589400 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.262731500 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_132840_b23080f2`

- **Modelo/motivo:** XGBoost · TreeSHAP exacto y verificación del pipeline.
- **Fecha/zona:** 2026-10-19T13:28:40.295670-05:00 a 2026-10-19T13:28:40.607288-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_132840_b23080f2/metadata.json](tiempos/20261019_132840_b23080f2/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_132840_b23080f2/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Transformación explicativa | Pipeline guardado sin fit | 0.026787300 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | Verificación pipeline final · train + test | 0.069632700 | 1497 | 1 | completa | Total; eventos.jsonl línea 2 |
| Explicación SHAP | TreeSHAP exacto · train + test | 0.179092100 | 1497 | 1 | completa | Total; eventos.jsonl línea 3 |
| Validación de aditividad | Base + aportes = predicción · todas las filas | 0.000617000 | 1497 | 1 | completa | Total; eventos.jsonl línea 4 |
| Total del experimento | XGBoost · TreeSHAP exacto y verificación del pipeline | 0.315055600 | No aplica | 1 | completa | Total; eventos.jsonl línea 5 |

### Ejecución `20261019_132835_7a7fe9cd`

- **Modelo/motivo:** Verificación/preparación · Dash/validate_package.py.
- **Fecha/zona:** 2026-10-19T13:28:35.261026-05:00 a 2026-10-19T13:28:47.185674-05:00; America/Bogota.
- **Estado:** completa. **Entorno/configuración/código/datos:** [tiempos/20261019_132835_7a7fe9cd/metadata.json](tiempos/20261019_132835_7a7fe9cd/metadata.json).
- **Alcance:** CPU, segundos de pared con perf_counter. Búsqueda incluye preprocesamiento y scoring; refit separado (refit=False). Inferencia incluye transformaciones, excluye carga y E/S; una repetición por lote, sin calentamiento explícito. Estado frío/caliente no controlado. No sumar llamadas anidadas ni etapas con el total.
- **Evidencia cruda:** [eventos](tiempos/20261019_132835_7a7fe9cd/eventos.jsonl).

| Etapa | Fold / partición / lote | Duración de pared (s) | Filas del lote | Repetición | Estado | Incluida en otra medida / evidencia |
| --- | --- | ---: | ---: | --- | --- | --- |
| Inferencia | XGBRegressor | 0.035414400 | 1497 | 1 | completa | Total; eventos.jsonl línea 1 |
| Inferencia | TransformedTargetRegressor | 0.034128500 | 188 | 1 | completa | Total; eventos.jsonl línea 2 |
| Inferencia | TruncatedNewtonKernelRidgeRegressor | 0.012112300 | 188 | 1 | completa | Total; eventos.jsonl línea 3 |
| Inferencia | DecisionTreeRegressor | 0.004179600 | 188 | 1 | completa | Total; eventos.jsonl línea 4 |
| Inferencia | LinearSVR | 0.013223400 | 188 | 1 | completa | Total; eventos.jsonl línea 5 |
| Inferencia | KNeighborsRegressor | 0.030682800 | 188 | 1 | completa | Total; eventos.jsonl línea 6 |
| Inferencia | Ridge | 0.000177900 | 188 | 1 | completa | Total; eventos.jsonl línea 7 |
| Inferencia | Ridge | 0.007586500 | 188 | 1 | completa | Total; eventos.jsonl línea 8 |
| Inferencia | Lasso | 0.007077400 | 188 | 1 | completa | Total; eventos.jsonl línea 9 |
| Inferencia | RandomForestRegressor | 0.036550700 | 188 | 1 | completa | Total; eventos.jsonl línea 10 |
| Inferencia | XGBRegressor | 0.014742200 | 188 | 1 | completa | Total; eventos.jsonl línea 11 |
| Inferencia | DecisionTreeRegressor | 0.005138700 | 188 | 1 | completa | Total; eventos.jsonl línea 12 |
| Inferencia | XGBRegressor | 0.017725300 | 1 | 1 | completa | Total; eventos.jsonl línea 13 |
| Inferencia | XGBRegressor | 0.019989000 | 1000 | 1 | completa | Total; eventos.jsonl línea 14 |
| Entrenamiento/refit | Ridge | 0.001098100 | 1000 | 1 | completa | Total; eventos.jsonl línea 15 |
| Inferencia | Ridge | 0.000141100 | 1000 | 1 | completa | Total; eventos.jsonl línea 16 |
| Inferencia | Ridge | 0.000129100 | 1 | 1 | completa | Total; eventos.jsonl línea 17 |
| Inferencia | XGBRegressor | 0.016018100 | 1 | 1 | completa | Total; eventos.jsonl línea 18 |
| Total del experimento | Verificación/preparación · Dash/validate_package.py | 11.924062800 | No aplica | 1 | completa | Total; eventos.jsonl línea 19 |

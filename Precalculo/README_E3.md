# Entregable 3: modelos predictivos y validación

Esta rama reúne los experimentos E3 y conserva la entrega anterior en `main`.
Los notebooks se pueden consultar con sus resultados ya ejecutados.

## Resultados completos

- [Panorama vigente de los 26 modelos: ranking, resultados y conclusiones](resultados/e3/resumen_completo/resumen.md).
- [CSV general de los 26 modelos: RMSE, R², descripciones y comparaciones](resultados/e3/resumen_completo/modelos.csv).
- [Contrastes publicados consolidados: referencia, IC95%, p y familia de ajuste](resultados/e3/resumen_completo/contrastes_actuales.csv).
- [Validación R² de los 26 modelos](resultados/e3/validacion_r2/resumen.md), con [CSV de resultados e intervalos disponibles](resultados/e3/validacion_r2/modelos_r2.csv).
- [R² de validación cruzada, OOF y test: 26 modelos](resultados/e3/validacion_r2/validacion_cruzada_r2.csv).
- [125 resultados R² por fold](resultados/e3/validacion_r2/folds_r2.csv) y [contrastes R² publicados frente a XGBoost](resultados/e3/validacion_r2/contrastes_r2_vs_xgboost.csv).
- [Comparación Scopus: etapa histórica de 18 modelos](resultados/e3/scopus/resumen.md).
- [Resultados de SVR RBF y RaFFLE: etapa histórica de 22 modelos](resultados/e3/svr_rbf_raffle/resumen.md), con [ranking de esa etapa](resultados/e3/svr_rbf_raffle/ranking_rmse_test.csv) y [contrastes Holm55](resultados/e3/svr_rbf_raffle/contrastes_pareados.csv).
- [Reporte TabFM](resultados/e3/tabfm/resumen.md) y [reporte GPR–XGBoost](resultados/e3/gpr_xgb/resumen.md).
- [Variantes metodológicas de XGBoost: etapa de 25 modelos](resultados/e3/xgboost_variantes/resumen.md), con [ranking de esa etapa](resultados/e3/xgboost_variantes/ranking_global_25_modelos.csv), [contrastes Holm12](resultados/e3/xgboost_variantes/contrastes_pareados.csv) y [errores OOF por tramo](resultados/e3/xgboost_variantes/oof_por_tramo.csv).
- [LinXGBoost con hojas lineales sobre las 67 columnas E3](resultados/e3/linxgboost/resumen.md), con [ranking RMSE de 26 modelos](resultados/e3/linxgboost/ranking_global_26_modelos.csv) y [contrastes pareados Holm7](resultados/e3/linxgboost/contrastes_pareados.csv).

## Estado actual y conclusiones

Se evaluaron 26 modelos y variantes. Los mejores resultados por RMSE test son:

| Puesto | Modelo | RMSE test | R² test |
|---:|---|---:|---:|
| 1 | SVR RBF | 0.892225 | 0.471418 |
| 2 | TabICLv2 | 0.897815 | 0.464774 |
| 3 | TabPFN 2.5 original | 0.898277 | 0.464223 |
| 4 | LinXGBoost | 0.899069 | 0.463278 |
| 5 | TabPFN 2.5 fine-tuned | 0.901370 | 0.460527 |
| 6 | Kernel Ridge RBF | 0.904881 | 0.456316 |
| 7 | CatBoost | 0.905669 | 0.455368 |
| 8 | XGBoost | 0.906274 | 0.454641 |

SVR RBF es el líder puntual y la mejor opción evaluada sin deep learning.
Reduce el RMSE de XGBoost en 0.014049 (1.55%). Su diferencia con TabICLv2
es pequeña: IC95% de ΔRMSE [-0.025163; 0.014880], p=0.58678 y Holm55=1.000.
El primer puesto no demuestra superioridad estadística sobre el segundo.

LinXGBoost es la modificación metodológica reciente mejor situada. Sus hojas
Ridge usan las 67 columnas E3. La auditoría con el repositorio del autor corrigió
inicialización, profundidad, poda, escala de regularización y aporte del último árbol.
Queda cuarto, con ΔRMSE=-0.007205 frente a XGBoost, IC95% [-0.036278; 0.021475]
y Holm7=1.000. No demuestra mejora significativa; su RMSE OOF 0.845385
también es mayor que el de XGBoost original (0.814822). Se aproxima el barrido
de cortes mediante 12 cuantiles y permanece una diferencia numérica al puntuar
candidatos. Las dos corridas previas están supersedidas y excluidas del ranking.

XGBoost ampliado, DenseWeight y DART quedan 11, 13 y 16; ninguna variante
supera el RMSE de XGBoost original. RaFFLE queda 12 y TabFM 10.
El ranking incluye los 22 métodos históricos más esas tres variantes y LinXGBoost.

Las familias Holm55 (histórica), Holm12 (variantes XGBoost) y Holm7 (LinXGBoost)
se conservan con sus referencias originales. No se calculó un ajuste global
único para los 26. Las celdas vacías no son p=0: indican resultados no disponibles
o pruebas ajenas a esa familia. RMSE y R² comparten SSE y no son evidencias
independientes. El test se consultó en varias rondas: las conclusiones son
exploratorias y necesitan confirmación temporal independiente.

El stacking tiene un [diagnóstico OOF preliminar](diagnostico_stacking_e3.md),
pero aún no es otro modelo entrenado y evaluado.

## Datos y protocolo

Se trabaja con datos reales sin aumentación, 15 predictores y objetivo
`nota_primer_parcial`. `nota_final` y el identificador de estudiante no son
predictores. Se mantienen outliers válidos y se excluyen inconsistencias de negocio.

Train: 1309 filas y 1293 estudiantes. Test temporal: periodo 202530, 188 estudiantes.
No hay estudiantes compartidos entre train y test. La selección usa GroupKFold
anidado 5×5 por estudiante y preparación aprendida dentro de cada fit. Las bases
preentrenadas de configuración fija usan los 5 externos sin búsqueda interna.
TabPFN ajustado tiene evaluación temporal, pero sus pesos finales no ofrecen
una nueva OOF independiente porque ya vieron todo train.

Los modelos se seleccionaron por RMSE. La validación R² compara esos mismos
modelos; no reoptimiza las grillas por R². El código de los autores y las
adaptaciones están identificados en los notebooks y reportes: XBART usa GFR
de stochtree; KRR usa solución exacta, no el optimizador Truncated Newton.

## Notebooks

- [Datos reales, partición y SVM](precalculo_entregable3.ipynb).
- [Regresores clásicos](precalculo_modelos_clasicos_e3.ipynb).
- [logicDT](precalculo_logicdt_e3.ipynb) y [RIM](precalculo_rim_e3.ipynb).
- [TabPFN original](precalculo_tabpfn_25_e3.ipynb) y [fine-tuning evaluado](precalculo_tabpfn25_finetuned_e3.ipynb).
- [TCR-XGBoost](precalculo_tcr_xgboost_e3.ipynb), [TabICLv2](precalculo_tabicl_v2_e3.ipynb) y [HRT-Boost](precalculo_hrt_boost_e3.ipynb).
- [XBART](precalculo_xbart_scopus_e3.ipynb), [CatBoost](precalculo_catboost_scopus_e3.ipynb),
  [Kernel Ridge](precalculo_kernel_ridge_scopus_e3.ipynb), [coPILOT](precalculo_copilot_scopus_e3.ipynb)
  y [comparación Scopus](precalculo_scopus_e3.ipynb).

## Reproducción local

Usar el mismo entorno de `Precalculo/venv` para análisis y dashboard.
Las dependencias de experimentos están en `requirements.txt`; las del dashboard
se conservan en `../Dash/requirements.txt`. Para CPU, instalar primero PyTorch:

```powershell
.\venv\Scripts\python.exe -m pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cpu
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

La ejecución completa requiere los datos autorizados en `Data/Datos_Brutos.csv`,
las exportaciones canónicas por registro y los checkpoints locales de
`modelos_preentrenados/`. Estos archivos privados no se publican en esta rama.
Los hashes de las fuentes originales permanecen en los reportes. Para TabPFN
se incluye `descargar_tabpfn25.py`; el checkpoint TabICL y el paquete fine-tuned
se identifican en sus respectivos reportes y deben estar disponibles localmente.

Para coPILOT se necesita el código original en `terceros/wPILOT`:

```powershell
git clone https://github.com/STAN-UAntwerp/wPILOT.git terceros/wPILOT
git -C terceros/wPILOT checkout 4ae908f4f1bd9ec93f1eeaebde958d6dd7ec5943
```

Con los datos, cachés y pesos disponibles, las entradas principales son
`entregable3.py`, `modelos_clasicos.py`, `evaluacion_nuevos_e3.py`,
`comparacion_seleccionados_e3.py`, `evaluar_scopus_e3.py`, `evaluar_tabfm_e3.py`,
`evaluar_gpr_xgb_e3.py`, `evaluar_svr_rbf_e3.py`, `evaluar_raffle_e3.py` y
`evaluar_svr_rbf_raffle_e3.py`, además de `evaluar_xgboost_variantes_e3.py` y
sus entradas `evaluar_xgboost_ampliado_e3.py`, `evaluar_xgboost_dart_e3.py` y
`evaluar_xgboost_denseweight_e3.py`, y `evaluar_linxgboost_e3.py`. Los scripts `evaluar_svr_rbf_e3.py` y
`evaluar_raffle_e3.py` ejecutan cada modelo por separado con el mismo motor y
folds. Después de ambos, `evaluar_svr_rbf_raffle_e3.py` genera las comparaciones
y el Holm global55. `requirements_svr_rbf_raffle_e3.txt` fija RaFFLE; las
dependencias compatibles de TabFM están en `requirements_tabfm_e3.txt`.
`finetune_tabpfn25_e3.py` prepara el entrenamiento local.

Para ejecutar los dos candidatos por separado y luego comparar sus resultados,
desde `Precalculo/`:

```powershell
.\venv\Scripts\python.exe .\evaluar_svr_rbf_e3.py
.\venv\Scripts\python.exe .\evaluar_raffle_e3.py
.\venv\Scripts\python.exe .\evaluar_svr_rbf_raffle_e3.py
```

Las variantes XGBoost se pueden ejecutar de forma independiente; cada entrada
usa el motor común y guarda checkpoints por fold. El comparador final reutiliza
esos resultados para generar la tabla de 25 modelos y los contrastes Holm12:

```powershell
.\venv\Scripts\python.exe .\evaluar_xgboost_ampliado_e3.py
.\venv\Scripts\python.exe .\evaluar_xgboost_dart_e3.py
.\venv\Scripts\python.exe .\evaluar_xgboost_denseweight_e3.py
.\venv\Scripts\python.exe .\evaluar_xgboost_variantes_e3.py
.\venv\Scripts\python.exe .\evaluar_linxgboost_e3.py
```

Para actualizar el panorama vigente, los CSV RMSE/R² y las conclusiones desde
los reportes agregados existentes, sin entrenar modelos:

```powershell
.\venv\Scripts\python.exe .\actualizar_comparaciones_e3.py
```

Este consolidado usa fuentes históricas de 22 modelos y los reportes de las
cuatro incorporaciones. Valida 26 resultados test, 125 resultados por fold y
la correspondencia RMSE/R². Los generadores `resumen_completo_e3.py` y
`validacion_r2_e3.py` corresponden a etapas históricas y no generan la vista vigente.

Se incluyen pruebas de particiones, preparación, métricas, serialización y modelos.

RaFFLE v0.0.5 calcula sus predicciones y métricas, pero su wrapper C++ nativo no
se puede guardar con joblib; se conservan selección, reportes y predicciones
agregadas, no un artefacto serializado del estimador.

## Investigación y auditoría

[Búsqueda Scopus](investigacion_scopus_no_deep_learning_e3.md),
[documentación de experimentos](experimentos_scopus_e3.md) y
[auditoría Scopus](resultados/e3/scopus/auditoria_final.json).
La auditoría Scopus verificó 2550 ajustes internos y que 20 modelos externos
restaurados reprodujeran sus predicciones OOF. Las 25 pruebas registradas
corresponden a aquella etapa. La consolidación actual valida los agregados y
sus fuentes, sin repetir los entrenamientos ni aquella batería de pruebas.
`publicacion_e3.json` registra los hashes de los archivos publicados.

El dashboard de esta rama conserva su interfaz E3 de modelos lineales/clásicos;
los experimentos posteriores se presentan en estos notebooks y resúmenes.
No se reescriben los informes ni notebooks de la primera entrega.

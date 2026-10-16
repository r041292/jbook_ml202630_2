# Entregable 3: modelos predictivos y validación

Esta rama reúne los experimentos E3 y conserva la entrega anterior en `main`.
Los notebooks se pueden consultar con sus resultados ya ejecutados.

## Resultados completos

- [Panorama de los 22 métodos: RMSE, diferencias y significancia](resultados/e3/resumen_completo/resumen.md).
- [CSV del panorama RMSE de los 22 métodos](resultados/e3/resumen_completo/modelos.csv).
- [Validación completa con R²](resultados/e3/validacion_r2/resumen.md).
- [CSV R², intervalos y significancia de los 22 métodos](resultados/e3/validacion_r2/modelos_r2.csv).
- [R² de validación cruzada, OOF y test](resultados/e3/validacion_r2/validacion_cruzada_r2.csv).
- [Resultados R² de cada fold](resultados/e3/validacion_r2/folds_r2.csv) y [contrastes Scopus–XGBoost](resultados/e3/validacion_r2/contrastes_r2_vs_xgboost.csv).
- [Comparación de las cuatro propuestas Scopus](resultados/e3/scopus/resumen.md).
- [Resultados detallados de SVR RBF y RaFFLE](resultados/e3/svr_rbf_raffle/resumen.md), con [ranking CSV](resultados/e3/svr_rbf_raffle/ranking_rmse_test.csv) y [contrastes CSV](resultados/e3/svr_rbf_raffle/contrastes_pareados.csv).
- [Reporte TabFM](resultados/e3/tabfm/resumen.md) y [reporte GPR–XGBoost](resultados/e3/gpr_xgb/resumen.md).

SVR RBF tiene el menor RMSE test puntual (0.892225) y el mayor R² (0.471418).
Frente al anterior mejor RMSE, TabICLv2 (0.897815), la diferencia es pequeña y
no significativa: IC95% [-0.025163; 0.014880], p=0.58678, Holm global55=1.
Ninguno de los nuevos candidatos mejora significativamente tras corrección
Holm global55. La prueba temporal ya fue consultada en experimentos previos,
por lo que estos contrastes son exploratorios. RMSE y R² comparten el contraste
SSE y no son evidencias independientes.

Los 22 métodos incluyen SVM lineal, Dummy, KNN, Ridge, Lasso, Random Forest,
XGBoost, logicDT adaptado, RIM adaptado, TabPFN2.5 original y ajustado,
TCR-XGBoost, TabICLv2, HRT-Boost, XBART GFR, Kernel Ridge RBF, CatBoost,
coPILOT, TabFM, GPR–XGBoost, SVR RBF y RaFFLE.
El stacking tiene un [diagnóstico OOF preliminar](diagnostico_stacking_e3.md),
pero aún no es un modelo 23 entrenado y evaluado.

## Datos y protocolo

Se trabaja con datos reales sin aumentación,15 predictores y objetivo
`nota_primer_parcial`. `nota_final` y el identificador de estudiante no son
predictores. Se mantienen outliers válidos y se excluyen inconsistencias de negocio.

Train:1309 filas y1293 estudiantes. Test temporal: periodo202530,188 estudiantes.
No hay estudiantes compartidos entre train y test. La selección usa GroupKFold
anidado5×5 por estudiante y preparación aprendida dentro de cada fit. Las bases
preentrenadas de configuración fija usan los5 externos sin búsqueda interna.
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
`evaluar_svr_rbf_raffle_e3.py`. Los scripts `evaluar_svr_rbf_e3.py` y
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

Se incluyen pruebas de particiones, preparación, métricas, serialización y modelos.

RaFFLE v0.0.5 calcula sus predicciones y métricas, pero su wrapper C++ nativo no
se puede guardar con joblib; se conservan selección, reportes y predicciones
agregadas, no un artefacto serializado del estimador.

## Investigación y auditoría

[Búsqueda Scopus](investigacion_scopus_no_deep_learning_e3.md),
[documentación de experimentos](experimentos_scopus_e3.md) y
[auditoría Scopus](resultados/e3/scopus/auditoria_final.json).
La auditoría verificó2550 ajustes internos y que20 modelos externos restaurados
reprodujeran sus predicciones OOF. Antes de esta publicación pasaron25 pruebas.
`publicacion_e3.json` registra los hashes de los archivos de análisis incorporados.

El dashboard de esta rama conserva su interfaz E3 de modelos lineales/clásicos;
los experimentos posteriores se presentan en estos notebooks y resúmenes.
No se reescriben los informes ni notebooks de la primera entrega.

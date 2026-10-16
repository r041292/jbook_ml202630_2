# Entregable 3: modelos predictivos y validación

Esta rama reúne los experimentos E3 y conserva la entrega anterior en `main`.
Los notebooks se pueden consultar con sus resultados ya ejecutados.

## Resultados completos

- [Panorama de los 18 métodos: RMSE, diferencias y significancia](resultados/e3/resumen_completo/resumen.md).
- [CSV del panorama RMSE](resultados/e3/resumen_completo/modelos.csv).
- [Validación completa con R²](resultados/e3/validacion_r2/resumen.md).
- [CSV R², intervalos y significancia](resultados/e3/validacion_r2/modelos_r2.csv).
- [R² de validación cruzada, OOF y test](resultados/e3/validacion_r2/validacion_cruzada_r2.csv).
- [Comparación de las cuatro propuestas Scopus](resultados/e3/scopus/resumen.md).

TabICLv2 tiene el menor RMSE test puntual,0.897815, y el mayor R²,0.464774.
Su contraste nominal frente a SVM tiene p0.02624; Holm17=.41984 y Holm21=.47232.
Ningún método mejora significativamente a SVM después de corrección múltiple.
Los contrastes siguen siendo exploratorios por la reutilización del test.
RMSE y R² comparten el contraste SSE; no son evidencias independientes.

Los18 métodos incluyen SVM lineal, Dummy, KNN, Ridge, Lasso, Random Forest,
XGBoost, logicDT adaptado, RIM adaptado, TabPFN2.5 original y ajustado,
TCR-XGBoost, TabICLv2, HRT-Boost, XBART GFR, Kernel Ridge RBF, CatBoost y coPILOT.
El stacking tiene un [diagnóstico OOF preliminar](diagnostico_stacking_e3.md),
pero aún no es un modelo19 entrenado y evaluado.

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
`comparacion_seleccionados_e3.py`, `evaluar_scopus_e3.py`, `resumen_completo_e3.py`
y `validacion_r2_e3.py`. `finetune_tabpfn25_e3.py` prepara el entrenamiento local.
Se incluyen pruebas de particiones, preparación, métricas, serialización y modelos.

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

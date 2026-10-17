# Experimentos de regresión Scopus — E3

Implementación autorizada el 15 de octubre de 2026 en branch e3. Cuatro familias:
XBART GFR, CatBoost Ordered, Kernel Ridge RBF y coPILOT. Las referencias y límites
de la evidencia están en investigacion_scopus_no_deep_learning_e3.md.

## Resultado de esta ejecución

| Modelo | RMSE temporal | Diferencia frente a SVM | Diferencia frente a XGBoost |
|---|---:|---:|---:|
| Kernel Ridge RBF | 0.904881 | −0.022825 | −0.001393 |
| CatBoost Ordered | 0.905669 | −0.022036 | −0.000604 |
| XBART GFR | 0.967515 | +0.039809 | +0.061241 |
| coPILOT | 0.970603 | +0.042897 | +0.064329 |

KRR y CatBoost mejoran puntualmente, sin significancia favorable incluso antes
de corrección: p frente a SVM0.09620/0.21864; frente a XGBoost0.90436/0.95670.
Holm global21 da1.0 en esos cuatro contrastes. XBART y coPILOT deterioran los
resultados; coPILOT frente a XGBoost tiene p.00282, Holm4.01128 y Holm21.05640:
la dirección es desfavorable. Los mejores RMSE históricos siguen siendo
TabICLv2 y TabPFN original. Detalle completo en resultados/e3/scopus/resumen.md.

Auditoría final:2550 ajustes internos;20 modelos externos restaurados reproducen
OOF, grillas completas y preparación aprendida dentro del fit. Cinco notebooks
ejecutados sin errores; gráficos inspeccionados visualmente. No se realizó merge.

## Reproducir y consultar

Desde Precalculo, usar exclusivamente el entorno compartido:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements_scopus_e3.txt
git clone https://github.com/STAN-UAntwerp/wPILOT.git terceros/wPILOT
git -C terceros/wPILOT checkout 4ae908f4f1bd9ec93f1eeaebde958d6dd7ec5943
.\venv\Scripts\python.exe -m unittest test_scopus_e3 -v
.\venv\Scripts\python.exe evaluar_scopus_e3.py all
```

El clone es necesario solo si falta terceros/wPILOT. Se conserva localmente el
código original de los autores sin modificaciones. No instalar todos los pins
antiguos del requirements de ese repositorio encima del entorno compartido:
requirements_scopus_e3.txt especifica las adiciones verificadas en este entorno.

Los resultados completos de igual procedencia se reutilizan. Las grillas guardan
progreso por candidato y fold. Un cambio de datos, modelos o grilla exige preservar
los resultados y usar una carpeta nueva. No regenerar los notebooks ya ejecutados
si se desea conservar sus salidas.

## Protocolo

Se reutilizan `evaluacion_nuevos_e3.partitions`, `entregable3.grouped_splits`
y `entregable3.metrics`. Fuente real sin aumento, mismas reglas de negocio,
15 predictores y nota_primer_parcial. nota_final y pidm están excluidos.
Train1309 registros, test temporal202530 con188 estudiantes, sin personas
compartidas. Cinco folds externos, cinco internos por selección, cinco internos
para el refit final. El test no elige hiperparámetros ni transformaciones.

La preparación se ajusta dentro de cada fit. XBART y KRR reutilizan el pipeline
SVM; CatBoost usa medianas/modas y categorías nativas; coPILOT usa medianas/modas,
ordinal y los índices nominales explícitos que admite su código. Estas diferencias
de representación son propias del estimador; la población y las variables
originales se mantienen. Ningún método elimina outliers ni aumenta observaciones.

| Familia | Grilla fijada en train | Detalle de implementación |
|---|---|---|
| XBART GFR | 50/150 árboles × profundidad2/4 × hoja10/30:8 | stochtree0.4.5,60 barridos GFR, descartados20; sin MCMC; tau muestreada; semilla42 |
| CatBoost Ordered | 300/600 iteraciones × profundidad2/4/6 × lr.03/.1 × L2 3/10:24 | CatBoost1.2.10 oficial, RMSE, sin early stopping externo, semilla42 |
| Kernel Ridge RBF | alpha.01/.1/1/10/100 × gamma.001/.003/.01/.03/.1/.3/1:35 | sklearn, objetivo centrado dentro de fit; solución exacta, no optimizador Truncated Newton |
| coPILOT | profundidad2/4/6 × hoja10/30 × alpha.2/.5/1:18 | código de autores, dos árboles, promedio, stop_earlyFalse; min_split2×hoja |

Los resultados son de estas implementaciones/configuraciones, no reproducciones
idénticas de todos los benchmarks publicados. XBART no usa el binario original
de JingyuHe: usa el algoritmo GFR que stochtree documenta como XBART standalone.
Su biblioteca advierte limitaciones con variables discretas/repetidas y one-hot;
no se añade MCMC para ocultar esa limitación. coPILOT conserva la truncación interna
aprendida solo en fit y los grados BIC convertidos a enteros del código original.
No hay recorte externo de predicciones ni ponderación transductiva con test.

## Artefactos

- modelos_scopus_e3.py: adaptadores y grillas.
- evaluar_scopus_e3.py: CV anidada, predicciones, métricas y comparación.
- paralelo_scopus_e3.py: distribuye folds independientes de XBART/CatBoost,
  reutilizando fit/predict/tune; seis procesos de un hilo. No correr mientras
  otro coordinador esté escribiendo las mismas grillas.
- precalculo_{xbart,catboost,kernel_ridge,copilot}_scopus_e3.ipynb: un notebook
  por familia; precalculo_scopus_e3.ipynb: comparación de los seis modelos,
  incluidas referencias SVM y XGBoost.
- resultados/e3/scopus/{familia}/: grillas, OOF, test, folds, auditoría y reporte.
- resultados/e3/scopus/comparacion_test.csv y contrastes_pareados.csv: resultados
  conjuntos y significancia. comparacion_metricas.png: cuatro paneles separados.
- modelos_preentrenados/scopus/: pipelines completos y modelos por fold, locales
  e ignorados en Git.

Durante esta ejecución se corrigió la lectura de la referencia clásica: su export
contiene solo predicciones, sin objetivo. Se valida su procedencia con base_report
y el orden canónico con partitions. El evaluador previo se conserva en
resultados/e3/scopus/evaluador_entrenamiento_original.py. El manifiesto
compatibilidad_comparacion.json admite únicamente los dos hashes auditados.
Los reportes mantienen el hash real del evaluador que los entrenó. Una prueba AST
verifica que fit/predict/tune/provenance y el cuerpo de entrenamiento de run no
cambiaron al corregir comparación/caché.

## Estadística

Permutación bilateral pareada99999 y bootstrap pareado10000 por estudiante,
semilla42. Diferencia=candidato−referencia. RMSE negativo y R² positivo favorecen
al candidato. RMSE y R² usan el mismo contraste SSE: no se cuentan dos hipótesis.
IC95% marginales, sin ajuste simultáneo. Holm4 por cada referencia como análisis
de la tanda actual; Holm global21 como análisis acumulado:13 pares históricos
frente a SVM,4 nuevos frente a SVM y4 nuevos frente a XGBoost.

La inferencia sigue siendo exploratoria por el uso repetido del test; condicional
a los modelos ajustados y sin variabilidad de reentrenamiento. No rechazar H0 no
demuestra equivalencia, y un p pequeño puede indicar deterioro. El dashboard y
los informes/notebooks históricos se conservan.

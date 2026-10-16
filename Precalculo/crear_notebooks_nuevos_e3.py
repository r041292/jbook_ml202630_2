"""Genera solo los dos notebooks experimentales nuevos de E3."""
from pathlib import Path
import sys
import nbformat as nbf

BOOK = Path(__file__).resolve().parent
md = nbf.v4.new_markdown_cell
code = nbf.v4.new_code_cell

COMMON = [
    md('''## Datos, variables y protocolo del tablero

Se importa la preparación canónica de `entregable3.py`, sin regenerar ni aumentar datos.
Se aplica el mismo filtro de objetivo faltante y reglas de negocio, conservando outliers válidos.
La respuesta es **nota_primer_parcial**. Son los mismos **8 predictores numéricos y 7 categóricos**.
`nota_final`, estudiante, periodo y fila fuente nunca se usan como predictores.

**Partición temporal:** train contiene los periodos anteriores a 202530 (1309 registros,
1293 estudiantes); test reserva 202530 (188 registros, 188 estudiantes). Se purgan de train
los estudiantes presentes en el periodo reservado, incluso si su objetivo de test falta.

**CV externa:** exactamente las mismas asignaciones de GroupKFold de cinco folds del tablero.
Los 1293 IDs son grupos indivisibles que se distribuyen entre cinco folds: cada fila recibe
una predicción OOF de un modelo que no vio ninguna fila de ese estudiante. Los folds no son
periodos: el periodo futuro constituye una evaluación separada. No se usa test para elegir parámetros.

**Preparación común al SVM/Ridge/Lasso/KNN:** mediana numérica, `log1p` en los tres tiempos,
StandardScaler, moda categórica y OneHotEncoder con referencia, ignorando categorías nuevas.
Cada preparación se ajusta únicamente en su subconjunto de fit, dentro del pipeline.
Las aserciones siguientes comprueban valores, orden de filas, hashes y folds contra los resultados del tablero.'''),
    code('''from pathlib import Path
import sys
import json
import numpy as np
import pandas as pd
from IPython.display import display

BOOK = Path.cwd()
if not (BOOK / 'entregable3.py').exists():
    BOOK = BOOK / 'Precalculo'
if not (BOOK / 'entregable3.py').exists():
    raise RuntimeError('Abre el notebook desde Precalculo o la raíz del proyecto.')
sys.path.insert(0, str(BOOK.resolve()))
from entregable3 import FEATURES, NUMERIC, CATEGORICAL, TARGET, GROUP, PERIOD, metrics
from evaluacion_nuevos_e3 import partitions, run_experiment, display_results

train, test, folds, audit = partitions()
display(pd.DataFrame([audit]))
display(pd.DataFrame({'variable': FEATURES, 'tipo': ['numérica']*8 + ['categórica']*7}))
display(pd.DataFrame([{'fold': k, 'fit_filas': len(fi), 'validacion_filas': len(va),
                      'fit_estudiantes': train.iloc[fi][GROUP].nunique(),
                      'validacion_estudiantes': train.iloc[va][GROUP].nunique(),
                      'estudiantes_compartidos': len(set(train.iloc[fi][GROUP]) & set(train.iloc[va][GROUP]))}
                     for k, (fi, va) in enumerate(folds, 1)]))
assert len(train) == 1309 and len(test) == 188
assert not set(train[GROUP]) & set(test[GROUP])
assert train[PERIOD].max() < test[PERIOD].min()
print('Integridad confirmada: fuente, 15 variables, filas, periodo y folds iguales al tablero.')'''),
]

METRICS = md('''## Métricas e interpretación

Se llama directamente a `entregable3.metrics`: **RMSE**, **MAE**, **MAPE (%)** y **R²**,
en la escala original de la nota, sin recortar las predicciones. Menor error es mejor;
mayor R² es mejor. MAPE conserva la definición del tablero y es sensible a notas cercanas a cero.

Se reportan los cinco resultados externos, su media y desviación estándar poblacional (`ddof=0`),
y las métricas sobre todas las predicciones OOF reunidas (no necesariamente iguales a la media por fold).
El test temporal se presenta por separado. Los IC del 95% se obtienen con 1000 réplicas bootstrap
por estudiante, semilla 42; la diferencia frente al SVM usa las mismas muestras en cada réplica.
Un intervalo de diferencia que incluye cero no respalda una mejora concluyente. Estos intervalos
son condicionales al modelo ajustado y no incluyen la variabilidad de volver a entrenarlo.

La comparación con los modelos existentes es descriptiva: el test del tablero ya fue inspeccionado
en fases anteriores. No equivale a una nueva prueba ciega. No se promete superar los modelos previos.''')

logic = [md('''# E3 — logicDT: implementación propia y evaluación comparable

Implementación experimental basada en [Lau, Schikowski y Schwender (2024)](https://link.springer.com/article/10.1007/s10994-023-06488-6).
El código propio está en `logicdt_propio.py`; no se usa una librería de logicDT.
El notebook ejecuta el pipeline y la validación; `evaluacion_nuevos_e3.py` evita duplicar las
reglas del proyecto. Los resultados quedan en `resultados/e3/logicdt/`, separados de los canónicos.

Usar el kernel del entorno compartido `Precalculo/venv/`. Ejecutar todas las celdas en orden.'''), *COMMON,
    md('''## Qué se implementa del método y qué se adapta

1. Un **literal** es una variable binaria o su negación. Un término es la conjunción AND de
   hasta dos literales, por ejemplo `(Dominio_Final > corte) AND NOT(categoría_programa)`.
2. Un estado es un conjunto de hasta 3 o 5 términos. El árbol recibe sus valores lógicos,
   no solamente los predictores individuales. Esto permite explorar interacciones con poco efecto marginal.
3. Se busca el conjunto mediante **recocido simulado**: añadir, eliminar o reemplazar un término,
   o negar un literal. Una propuesta mejor se acepta; una peor se acepta con probabilidad
   `exp((MSE_actual − MSE_propuesto)/temperatura)`. Se conserva siempre la mejor solución visitada.
4. El árbol binario se construye minimizando la suma de errores cuadrados de sus hojas.
   La profundidad y el mínimo de 40 registros por hoja limitan el sobreajuste.

**Adaptaciones explícitas:** el artículo está diseñado para entradas binarias. Las ocho variables
numéricas se convierten internamente en indicadores `x > cuantil`, con cuantiles .25, .50 y .75
aprendidos solo en fit; las dummies categóricas ya son binarias. Por tanto, se conservan las variables
originales y el preprocesamiento externo del tablero, pero existe una discretización adicional propia
del modelo. Las hojas se comparan como media (núcleo de logicDT) o **Ridge multivariable sobre los
ocho numéricos transformados**, una adaptación inspirada en la extensión de regresión en nodos del
artículo. No es la misma formulación ni el mismo criterio de razón de verosimilitud del paquete R.

Se usa enfriamiento geométrico, 120 propuestas por reinicio y 2 reinicios con semilla 42.
Es un presupuesto exploratorio acotado; el artículo recomienda búsquedas considerablemente mayores.
No se implementan bagging ni importancia de interacciones, y **no se atribuye la garantía asintótica
del artículo a esta adaptación finita**. Se puede ampliar `n_iter` en un nuevo experimento,
decidiéndolo con train/CV y no en respuesta al resultado de test.'''),
    code('''from evaluacion_nuevos_e3 import logic_pipeline, LOGIC_GRID
from logicdt_propio import LogicDTRegressor
from sklearn.model_selection import ParameterGrid
import inspect

pipeline = logic_pipeline()
display(pipeline)
display(pd.DataFrame(list(ParameterGrid(LOGIC_GRID))))
print('Configuraciones:', len(list(ParameterGrid(LOGIC_GRID))))
print('Ajustes en CV: 5 × 5 × 8 + 5 × 8 = 240, más 6 refits.')
# El código es propio y se puede inspeccionar/editar en el módulo adyacente.
print(inspect.getsource(LogicDTRegressor._terms_matrix))'''),
    md('''## Selección anidada sin fuga de información

Para cada fold externo, GridSearchCV compara ocho configuraciones en cinco folds internos
por estudiante del subconjunto externo de entrenamiento. Cada candidato vuelve a ajustar
imputación, escalas, vocabulario, cuantiles, términos y árbol. Selecciona el menor RMSE interno,
reajusta en todo ese fit externo y predice la validación externa. Finalmente se repite la búsqueda
interna usando todo train y se evalúa el test temporal una vez fijados los parámetros.

La grilla contiene cuatro árboles con hojas medias (3/5 términos × profundidad 2/3) y cuatro
con hojas Ridge (3/5 términos × alpha 1/10, profundidad 2). Las categorías no vistas se manejan
con el mismo encoder del SVM. No se escogen cortes ni términos usando datos de validación.'''),
    code('''# Reutiliza únicamente resultados completos cuyo manifiesto coincide con los archivos actuales.
# force=True ejecuta de nuevo toda la evaluación; no cambia el protocolo ni las grillas.
report = run_experiment('logicdt', force=False)
display(pd.DataFrame(report['fold_audit']))
print('Parámetros finales:', report['best_params'])'''),
    METRICS,
    code('''display_results(report)
display(pd.DataFrame(report['paired_vs_svm']).round(5))'''),
    md('''## Reglas del modelo final y trayectoria de búsqueda

Los cortes impresos están en la **escala transformada** por el pipeline, no en puntos brutos
de ICFES o ALEKS. `<=` representa la negación del indicador `>`. Un término seleccionado puede
no utilizarse en el árbol final; la tabla de nodos identifica los términos efectivamente usados.
En cada nodo, la rama izquierda corresponde a término falso y la derecha a verdadero.
Las reglas representan asociaciones predictivas, no efectos causales.'''),
    code('''import joblib
import matplotlib.pyplot as plt
folder = BOOK / 'resultados/e3/logicdt'
fitted = joblib.load(folder / 'modelo.joblib')
estimator = fitted.named_steps['modelo']
display(pd.DataFrame(estimator.describe_terms(fitted.named_steps['preprocesamiento'].get_feature_names_out())))
nodes = []
def visit(node, path='raíz'):
    nodes.append({'nodo': path, 'registros_fit': node['n'], 'termino_split': node.get('term'),
                  'tipo': 'nodo' if 'term' in node else estimator.leaf_model})
    if 'term' in node:
        visit(node['left'], path + ' → falso')
        visit(node['right'], path + ' → verdadero')
visit(estimator.tree_)
display(pd.DataFrame(nodes))
trace = pd.read_csv(folder / 'recocido_final.csv')
plt.figure(figsize=(10, 3))
plt.plot(trace.best_mse.to_numpy())
plt.xlabel('Propuestas acumuladas (2 reinicios)')
plt.ylabel('Mejor MSE de ajuste visitado')
plt.title('Búsqueda final: diagnóstico de optimización, no métrica de generalización')
plt.grid(alpha=.2)
plt.show()'''),
    md('''## Archivos y reproducibilidad

Se guardan reporte JSON, cuatro métricas por fold, ocho candidatos por búsqueda interna,
predicciones OOF/test sin IDs, términos, trayectoria y pipeline final serializado.
Los hashes vinculan fuente, protocolo y módulos de implementación; si cambian se recalcula.
El árbol serializado contiene coeficientes y reglas, no la tabla de estudiantes.
Los notebooks históricos y los resultados del tablero se preservan.'''),
    code("print(json.dumps(report['versions'], indent=2, ensure_ascii=False))\nprint('Resultados:', folder.resolve())")]

tab = [md('''# E3 — TabPFN 2.5: inferencia local y evaluación comparable

Basado en el [informe técnico TabPFN‑2.5, versión 2](https://arxiv.org/abs/2511.08667v2)
y el [checkpoint oficial de Prior Labs](https://huggingface.co/Prior-Labs/tabpfn_2_5).
Esta aproximación usa la librería Python oficial, como excepción al criterio de implementación
propia de la búsqueda anterior. No se reimplementa ni se preentrena la red fundacional.

Los resultados quedan en `resultados/e3/tabpfn_25/`. Se ejecuta en el equipo local:
los datos de estudiantes no se envían a un servicio de inferencia.'''),
    md('''## Instalación y checkpoint exacto

Usar el entorno compartido. Desde la raíz del proyecto:
```powershell
Precalculo\\venv\\Scripts\\python.exe -m pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cpu
Precalculo\\venv\\Scripts\\python.exe -m pip install -r Precalculo/requirements_tabpfn25.txt
Precalculo\\venv\\Scripts\\python.exe Precalculo/descargar_tabpfn25.py
```
Se fija el SDK `tabpfn==6.4.1` y se carga mediante ruta explícita
`tabpfn-v2.5-regressor-v2.5_default.ckpt`, con revisión y SHA‑256 registrados.
La versión del paquete **no** es la versión del modelo. No se permite reemplazar
silenciosamente los pesos por TabPFN 2 o por otra generación.

El checkpoint está preentrenado con datos sintéticos por sus autores; eso no aumenta ni altera
los registros de este proyecto. Su licencia permite investigación y evaluación interna y restringe
usos comerciales/productivos: [licencia de los pesos](https://huggingface.co/Prior-Labs/tabpfn_2_5/blob/main/LICENSE).
Los pesos se guardan localmente, fuera de Git; no se instalan componentes CUDA.'''),
    code('''from pathlib import Path
import os
import sys
book = Path.cwd() if (Path.cwd() / 'entregable3.py').exists() else Path.cwd() / 'Precalculo'
sys.path.insert(0, str(book.resolve()))
from evaluacion_nuevos_e3 import prepare_tabpfn_environment
prepare_tabpfn_environment()  # Desactivar telemetría ANTES de importar tabpfn.
import torch
import tabpfn
import importlib.metadata
print('SDK:', importlib.metadata.version('tabpfn'), '| PyTorch:', torch.__version__)
print('Dispositivo de este experimento: CPU. No se necesita token para el checkpoint público.')'''), *COMMON,
    md('''## Cómo se adapta TabPFN al protocolo

TabPFN realiza predicción **en contexto**: `fit` registra el conjunto de entrenamiento y
prepara la inferencia con pesos ya preentrenados; no corresponde a entrenar una red desde cero.
Solo los datos del fit externo constituyen el contexto para predecir ese fold.

Se reutiliza exactamente el preprocesamiento externo del SVM, aprendido dentro de cada fit.
TabPFN podría trabajar con una representación categórica diferente; aquí se elige la misma
matriz imputada/escalada/one-hot para controlar la comparación solicitada. Esto **no reproduce
la configuración óptima ni los benchmarks del artículo**. Las transformaciones internas del
ensamble de TabPFN siguen siendo parte del modelo. Las métricas se calculan sobre su predicción
media en la escala de la nota, usando la función común.

Se fijan de antemano cuatro estimadores del ensamble (el SDK ofrece ocho por defecto), CPU,
semilla 42, `low_memory`, `memory_saving_mode=True` y un trabajo de preparación. Se conservan
todas las filas de cada fit; no se submuestrean estudiantes para ahorrar recursos. Se desactivan
telemetría y aperturas automáticas de navegador.

**No se realiza búsqueda de hiperparámetros**: por ello no hay selección interna ni necesidad
de CV interna. Se usan los mismos cinco folds externos que el resto y un ajuste final en todo
train. Si posteriormente se ajusta el número de estimadores u otro parámetro, deberá hacerse
con CV interna por estudiante, conservando el test temporal reservado.'''),
    code('''from evaluacion_nuevos_e3 import tabpfn_pipeline, MODEL_DIR
pipeline = tabpfn_pipeline()
display(pipeline)
manifest = json.loads((MODEL_DIR / 'procedencia.json').read_text(encoding='utf-8'))
display(pd.DataFrame([manifest]))
assert 'v2.5-regressor-v2.5_default' in str(pipeline.named_steps['modelo'].model_path)
print('Checkpoint verificado por SHA-256; inferencia exclusivamente local.')'''),
    md('''## Evaluación de cinco folds y test temporal

La ejecución completa puede ser lenta en CPU. No se reducen las filas ni se sustituye
el modelo si faltan memoria o pesos: la ejecución informa el error y no inventa métricas.
La caché se usa únicamente cuando el reporte completo coincide con los hashes actuales.'''),
    code('''report = run_experiment('tabpfn_25', force=False)
display(pd.DataFrame(report['fold_audit']))
print('Configuración fijada:', report['best_params'])'''),
    METRICS,
    code('''display_results(report)
display(pd.DataFrame(report['paired_vs_svm']).round(5))'''),
    md('''## Reproducibilidad y límites

Se guardan las versiones, revisión de pesos, SHA‑256, auditoría de particiones,
predicciones OOF/test sin identificadores y métricas comparables al tablero. No se serializa
el objeto TabPFN ajustado, porque su contexto contiene ejemplos de entrenamiento; para
reproducir predicciones se carga el checkpoint y se ejecuta este protocolo sobre los datos locales.

Los resultados con cuatro estimadores, CPU y preparación común son propios de este experimento.
La superioridad en otros datasets publicada por los autores no garantiza una mejora aquí.
Las diferencias frente a XGBoost, Ridge y SVM se interpretan con CV y con los intervalos,
sin seleccionar configuraciones mirando test.'''),
    code("print(json.dumps(report['versions'], indent=2, ensure_ascii=False))\nprint('Resultados:', (BOOK / 'resultados/e3/tabpfn_25').resolve())")]

from significancia_tabpfn_svm import notebook_cells
tab.extend(notebook_cells())

for filename, cells in [('precalculo_logicdt_e3.ipynb', logic),
                        ('precalculo_tabpfn_25_e3.ipynb', tab)]:
    notebook = nbf.v4.new_notebook(cells=cells)
    notebook.metadata['kernelspec'] = {'display_name': 'Python (Precalculo/venv)',
                                       'language': 'python', 'name': 'python3'}
    notebook.metadata['language_info'] = {'name': 'python', 'version': sys.version.split()[0]}
    nbf.write(notebook, BOOK / filename)
    print(filename)

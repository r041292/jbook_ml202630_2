"""Genera exclusivamente el notebook experimental RIM."""
from pathlib import Path
import sys
import nbformat as nbf

BOOK = Path(__file__).resolve().parent
md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
nb = nbf.v4.new_notebook(cells=[
    md('''# E3 — Retrieval & Interaction Machine (RIM)

Implementación propia en PyTorch de los componentes de RIM para regresión, basada en
[Qin et al., KDD2021](https://arxiv.org/abs/2108.05252) y el
[código de referencia](https://github.com/qinjr/RIM) en la revisión
`a6b4cdb347f306f9cf54a98fc994bf7112b53e9e`. El original usa TensorFlow1 y Elasticsearch.
Esta adaptación local no necesita esos servicios ni instala otra librería de modelos.

Código del estimador: `rim_regresion_e3.py`. Evaluación: `evaluar_rim_e3.py`.
Usar el venv compartido. Los notebooks históricos permanecen intactos.'''),
    md('''## Arquitectura implementada

RIM trata la consulta como una fila y recupera filas relacionadas mediante BM25. Una atención
bilineal pondera sus embeddings y los de sus etiquetas. Se concatenan los quince campos de
la consulta, los quince agregados y el embedding agregado de etiqueta: 31 campos. Se calculan
sus 465 productos internos por pares y una MLP produce la nota, con conexión directa desde
la etiqueta agregada. La pérdida de regresión es MSE y la salida es lineal.

**Adaptaciones:** BM25 local con IDF positiva de Lucene; PyTorch; cuantiles para numéricos y
etiquetas recuperadas; MLP pequeña64/32 y LayerNorm en vez de la implementación histórica;
dropout0.1, objetivo estandarizado dentro de fit y Adam con weight_decay. La nota utilizada
como objetivo conserva sus decimales: solo se discretiza la representación de las notas de
vecinos. Se usa la conexión de etiquetas descrita en el artículo; el código de referencia no
la conecta en su rama de regresión. No es una reproducción exacta de sus benchmarks.'''),
    md('''## Datos y prevención de fugas

Se reutiliza `entregable3.py`: datos reales sin aumentación, mismas reglas y outliers,
8 variables numéricas y7 categóricas, objetivo nota_primer_parcial. Se excluyen nota_final,
ID, periodo y fila fuente como predictores. Train1309 filas/1293 estudiantes y test202530
con188 filas/188 estudiantes. Se comprueban hashes y asignaciones guardadas del tablero.

Se clona la preparación del SVM dentro de cada fit: mediana, log1p para tiempos, escalado,
moda y vocabulario categórico. RIM requiere campos discretos: añade8 bins por cuantiles
numéricos y usa embeddings de categorías en lugar de introducir la matriz one-hot a la red.
Esto mantiene limpieza, variables e imputación comunes, con una representación específica
del modelo. Cortes y vocabularios se aprenden exclusivamente en fit, nunca en validación/test.

**Pool:** las filas del fit constituyen la memoria de recuperación. Para entrenar una consulta,
se excluyen todas las filas del mismo estudiante, no solo la fila. Los folds de validación y
el test nunca entran al pool, ni siquiera sus variables. Solo se usan las notas de vecinos
etiquetados de fit; la nota de la consulta no se introduce en la red ni en BM25.
Este uso leave-student-out del fit adapta las tres tablas separadas del artículo para no
reservar un tercer subconjunto pequeño. Si no hay coincidencias, la atención devuelve cero
para la memoria y se predice con la consulta. Padding y categorías nuevas están contemplados.'''),
    code('''from pathlib import Path
import sys
import pandas as pd
from IPython.display import display
BOOK = Path.cwd() if (Path.cwd() / 'entregable3.py').exists() else Path.cwd() / 'Precalculo'
sys.path.insert(0, str(BOOK.resolve()))
from evaluacion_nuevos_e3 import partitions
from evaluar_rim_e3 import run, GRID, FIXED, REF
from sklearn.model_selection import ParameterGrid
from entregable3 import FEATURES
train, test, folds, audit = partitions()
display(pd.DataFrame([audit]))
display(pd.DataFrame(list(ParameterGrid(GRID))))
print('Parámetros fijos:', FIXED)
print('15 predictores:', FEATURES)'''),
    md('''## Selección anidada antes de evaluar test

Grilla de ocho configuraciones: vecinos5/15 × épocas30/60 × weight_decay0.001/0.01.
Embeddings8, bins numéricos8, bins de etiqueta10, batch256 y learning_rate0.001.
Semilla42 y un hilo CPU por ajuste. Las épocas son hiperparámetro de la grilla; no hay
early stopping sobre el fold que evalúa el candidato ni sobre el test.

Cinco folds externos y cinco internos por estudiante, idénticos a las asignaciones canónicas.
Cada candidato reconstruye preprocesador, discretización, IDF/pool, embeddings y pesos solo
con su fit interno. Selección por RMSE medio interno. Se predice el fold externo con un refit
del ganador. Son240 ajustes internos más6 refits. La última búsqueda usa todo train y
se fija su configuración antes de predecir test. Las salidas OOF son de modelos que no vieron
ninguna fila ni etiqueta del estudiante predicho.'''),
    code('''report = run(force=False)  # Caché solo si la evaluación completa conserva la misma procedencia.
display(pd.DataFrame(report['fold_audit']))
display(pd.DataFrame(report['cv']).round(6))
print('Configuración final:', report['best_params'])'''),
    md('''## Comparación de resultados

RMSE, MAE, MAPE(%) y R² usan exactamente la función de métricas del tablero y la escala
original de la nota, sin clipping. Menor error es mejor; mayor R² es mejor. MAPE es sensible
a notas próximas a cero. Media/SD de CV (ddof0), OOF reunido y test son cantidades distintas.
El gráfico de test separa unidades en cuatro paneles. TabPFN ajustado solo tiene test válido;
su selección de épocas no se presenta como CV externa.'''),
    code('''from evaluar_tabpfn25_finetuned_e3 import show
cv_paths = ['clasicos/fold_metrics.csv', 'logicdt/fold_metrics.csv',
            'tabpfn_25/fold_metrics.csv', 'rim/fold_metrics.csv']
external = pd.concat([pd.read_csv(BOOK / 'resultados/e3' / path) for path in cv_paths], ignore_index=True)
cv_table = external.groupby('Modelo')[['RMSE', 'MAE', 'MAPE (%)', 'R²']].mean().add_suffix(' media CV')
cv_table['RMSE SD CV (ddof0)'] = external.groupby('Modelo').RMSE.std(ddof=0)
display(cv_table.sort_values('RMSE media CV').round(6))
cv_table.to_csv(BOOK / 'resultados/e3/rim/comparacion_cv_externa.csv')
show(report)
display(pd.DataFrame(report['family_vs_svm']).round(6))'''),
    md('''## Significancia y búsqueda de varios métodos

Contrastes bilaterales de permutación pareada por estudiante99999; IC95% percentiles con
10000 réplicas bootstrap pareadas, semilla42. La diferencia es RIM menos referencia:
negativa favorece a RIM para RMSE, positiva para R². Un p pequeño también puede indicar
que RIM es **peor**: hay que comprobar la dirección de la diferencia.

RMSE y R² dan el mismo contraste de SSE en este test y no son dos evidencias independientes.
Se muestra Holm sobre los dos pares actuales (RIM vs TabPFN original y vs SVM). Además se
recalcula una familia fija de nueve candidatos observados frente al SVM: KNN, Ridge, Lasso,
RF, XGBoost, logicDT, TabPFN original, TabPFN ajustado y RIM, con Holm para esos nueve pares.
Los IC son marginales, sin ajuste simultáneo.

**Límite:** el test ya se ha consultado para múltiples métodos. La corrección de la familia
conocida no convierte una búsqueda adaptativa indefinida en un experimento confirmatorio.
Se reporta el resultado completo, favorable o desfavorable. Una mejora definitiva requerirá
datos nuevos reservados y un criterio de selección fijado antes de examinarlos. No se buscan
semillas ni grillas mirando test hasta obtener p<.05; no rechazar H0 tampoco prueba equivalencia.'''),
    code('''for comp in report['paired_comparisons']:
    row = comp['rows'][0]
    significant_improvement = (row['diferencia_ajustado_menos_referencia'] < 0
                               and row['p_Holm_dos_pares'] < .05)
    print(comp['referencia'], ': mejora significativa de RMSE (dos pares, Holm):', significant_improvement)
    print('  deltaRMSE=', row['diferencia_ajustado_menos_referencia'],
          'p bilateral=', row['p_bilateral'], 'p Holm=', row['p_Holm_dos_pares'])
print('Resultados:', report['outputs'])
print('Modelo local con memoria de entrenamiento:', report['private_model'])'''),
    md('''## Artefactos y reproducibilidad

`resultados/e3/rim/` contiene protocolo previo a test, grillas internas, auditoría, métricas
por fold, predicciones OOF/test sin IDs, comparaciones y procedencia con hashes/versiones.
El estimador serializado incluye la memoria de entrenamiento con etiquetas e identificadores
para excluir estudiantes: se guarda únicamente en `modelos_preentrenados/rim_e3/`, ignorado
en Git. No se publica el modelo ni se cambia automáticamente el modelo activo del dashboard.'''),
])
nb.metadata['kernelspec'] = {'display_name': 'Python (Precalculo/venv)', 'language': 'python', 'name': 'python3'}
nb.metadata['language_info'] = {'name': 'python', 'version': sys.version.split()[0]}
path = BOOK/'precalculo_rim_e3.ipynb'
nbf.write(nb, path)
print(path)

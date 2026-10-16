"""Crear notebooks nuevos y una comparación; nunca reescribe Books históricos."""
import sys
from pathlib import Path
import nbformat as nbf

from entregable3 import BOOK
from modelos_scopus_e3 import LABELS,GRIDS,REFERENCES
from sklearn.model_selection import ParameterGrid

md,code=nbf.v4.new_markdown_cell,nbf.v4.new_code_cell
DESCRIPTIONS={
    'xbart':'''Se usa `stochtree==0.4.5`, `BARTModel` con Grow-From-Root puro:
60 barridos GFR, cero MCMC y descarte de los primeros20 al promediar las40
predicciones restantes. Es la arquitectura XBART implementada en stochtree,
no una ejecución del binario original de JingyuHe. Se ajusta la varianza de
las hojas y se fija semilla42. Árboles50/150 × profundidad2/4 × hoja10/30.

Preparación canónica SVM dentro del fold, con one-hot. stochtree advierte
limitaciones del muestreo GFR en predictores discretos/repetidos; se conserva
esta representación para reutilizar el tratamiento canónico y se documenta
la limitación. No se añaden iteraciones MCMC porque sería otro estimador.
La media predictiva regresa en la escala original del objetivo.''',
    'catboost':'''Se usa `CatBoostRegressor` oficial, pérdida RMSE y
`boosting_type='Ordered'`, categorías nativas y semilla42. Se imputan medianas
numéricas y modas categóricas dentro de cada fit, sin one-hot, escalado o
logaritmos externos. El identificador de estudiante nunca es predictor.

Grilla24: iteraciones300/600 × profundidad2/4/6 × learning_rate.03/.1 ×
l2_leaf_reg3/10. No hay early stopping con test ni eval_set externo.
Un adaptador sklearn evita un problema de clone(cat_features) con sklearn1.9;
el entrenamiento interno sigue siendo íntegramente CatBoost.''',
    'kernel_ridge':'''Se usa `KernelRidge(kernel='rbf')` de scikit-learn:
la arquitectura KRR del artículo, con solución exacta, **sin reproducir el
optimizador Truncated Newton**. No llamamos TN-KRR a este experimento.

Preparación canónica SVM con log1p en tiempos, escalado y one-hot, aprendida
dentro del fold. Como KernelRidge no incorpora intercepto, el objetivo se
centra dentro de cada fit mediante TransformedTargetRegressor y se devuelve
a la escala original antes de medir. Grilla35: alpha.01/.1/1/10/100 ×
gamma.001/.003/.01/.03/.1/.3/1. Ridge lineal previo no cubría este modelo.''',
    'copilot':'''Se usa sin modificar el código de los autores de wPILOT,
commit4ae908f4f1bd9ec93f1eeaebde958d6dd7ec5943. Se entrenan exactamente dos
árboles: `max_n_estimators=2`, `stop_early=False` y predicción `Average`.
El segundo árbol pondera errores del primero; no genera datos sintéticos.

Mediana numérica, moda y codificación ordinal de categorías dentro del fold.
Los siete índices categóricos se pasan explícitamente al algoritmo para
sus divisiones nominales, no como pendientes numéricas. Sin escalado/log1p
externos. Grilla18: profundidad2/4/6 × hoja10/30 × alpha.2/.5/1;
min_sample_split=2×hoja y max_model_depth30. Se conserva la truncación interna
del algoritmo (basada solo en fit), sin recorte externo de predicciones.
El código original convierte los grados de libertad del BIC a enteros;
esa discretización de alpha se conserva y no reproduce aritmética fraccional
idealizada. No se usan pesos por covariate shift ni covariables de test.''',
}
COMMON='''## Protocolo compartido

Misma fuente real `Data/Datos_Brutos.csv`, reglas de negocio y15 predictores.
Objetivo `nota_primer_parcial`; nota_final, pidm, periodo e índice de fila no
son entradas. Sin aumentación ni eliminación de outliers válidos.
Train1309 filas/1293 estudiantes; test202530:188 estudiantes, sin solapamiento.

Cinco folds externos canónicos por estudiante, cinco internos en cada búsqueda
y cinco internos para elegir parámetros finales. RMSE medio interno selecciona
la configuración. Cada preprocesador y modelo se ajusta solo en su fit.
La selección final se guarda antes de predecir test. Mismas funciones del tablero:
RMSE, MAE, MAPE(%) y R²; métricas sin ponderación, escala original.
Media/SD entre folds, OOF reunido y test temporal se informan por separado.

Se guardan grillas, auditorías, hashes, OOF y predicciones test. El código puede
reanudar cálculos de igual procedencia; si cambia la procedencia exige una
carpeta nueva. Pesos/estimadores quedan locales en modelos_preentrenados/scopus.
No se reemplazan los modelos del dashboard ni se reescriben informes anteriores.'''
SETUP='''from pathlib import Path
import sys
BOOK=Path.cwd() if (Path.cwd()/'entregable3.py').exists() else Path.cwd()/'Precalculo'
sys.path.insert(0,str(BOOK.resolve()))
import pandas as pd
from IPython.display import display
from evaluar_scopus_e3 import run,compare,ROOT
'''


def write_notebook(path,cells):
    notebook=nbf.v4.new_notebook(cells=cells)
    notebook.metadata['kernelspec']={'display_name':'Python (Precalculo/venv)','language':'python','name':'python3'}
    notebook.metadata['language_info']={'name':'python','version':sys.version.split()[0]}
    nbf.write(notebook,path)
    print(path)


def create():
    for key,title in LABELS.items():
        write_notebook(BOOK/f'precalculo_{key}_scopus_e3.ipynb',[
            md(f'# E3 — {title}\n\n[Artículo]({REFERENCES[key]["paper"]}). Experimento solicitado de la búsqueda Scopus.'),
            md(DESCRIPTIONS[key]),md(COMMON),
            code(SETUP+f"\nreport=run({key!r})\ndisplay(pd.DataFrame(report['cv']).round(6))\nprint('Parámetros finales:',report['best_params'])"),
            md('## Test temporal y auditoría\n\nEl test no selecciona hiperparámetros.'),
            code("display(pd.DataFrame([report['test']]).round(6))\ndisplay(pd.DataFrame(report['fold_audit']))"),
            md('## Comparación conjunta\n\nTras completar los cuatro modelos, consultar precalculo_scopus_e3.ipynb y resultados/e3/scopus/comparacion.json.')])
    write_notebook(BOOK/'precalculo_scopus_e3.ipynb',[
        md('# E3 — Comparación de los cuatro métodos Scopus'),md(COMMON),
        code(SETUP+"\nreport=compare()\ndisplay(pd.DataFrame(report['test']).round(6))"),
        md('''## Comparación por métrica

Cada panel tiene una escala independiente: no se mezclan las magnitudes de
RMSE, MAE, MAPE y R². Azul identifica las referencias; verde, los candidatos.'''),
        code('''import matplotlib.pyplot as plt
table=pd.DataFrame(report['test'])
fig,axes=plt.subplots(2,2,figsize=(14,9),constrained_layout=True)
for ax,metric in zip(axes.flat,['RMSE','MAE','MAPE (%)','R²']):
    values=table.sort_values(metric,ascending=metric!='R²')
    bars=ax.barh(values.Modelo,values[metric],color=['#326d9c' if m in ['SVM lineal','XGBoost'] else '#20806b' for m in values.Modelo])
    ax.bar_label(bars,fmt='%.4f',padding=3)
    ax.invert_yaxis()
    ax.set_title(metric+(': mayor es mejor' if metric=='R²' else ': menor es mejor'))
    ax.margins(x=.2)
    ax.grid(axis='x',alpha=.2)
fig.savefig(ROOT/'comparacion_metricas.png',dpi=160)
plt.show()'''),
        md('''## Diferencias pareadas y significancia

Permutación bilateral99999 y bootstrap10000 por estudiante; semilla42.
Delta=candidato−referencia: negativo favorece al candidato para RMSE,
positivo para R². Ambas métricas comparten el contraste SSE y su p-valor.
Los IC95% son marginales. Se muestran p crudo, Holm para los cuatro nuevos
frente a cada referencia y Holm global21:13 pares históricos frente a SVM,
4 nuevos frente a SVM y4 nuevos frente a XGBoost. No se cuentan RMSE/R²
como dos hipótesis independientes.

Inferencia exploratoria por reutilización del test; condicional a estos
estimadores, sin variabilidad por reentrenamiento. Un p alto no demuestra
equivalencia. Una diferencia significativa puede representar deterioro:
revisar siempre la dirección.'''),
        code("contrasts=pd.DataFrame(report['contrasts'])\ndisplay(contrasts[contrasts.metrica.eq('RMSE')].round(6))\ndisplay(contrasts[contrasts.metrica.eq('R²')].round(6))"),
        md('## Validación externa por estudiante'),
        code("display(pd.DataFrame([{'Modelo':r['model'],**v} for r in report['models'].values() for v in r['cv']]).round(6))")])


if __name__=='__main__':create()

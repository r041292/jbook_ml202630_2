"""Notebooks separados de los tres métodos elegidos, en orden de evaluación."""
from pathlib import Path
import sys
import nbformat as nbf

BOOK=Path(__file__).resolve().parent
md,code=nbf.v4.new_markdown_cell,nbf.v4.new_code_cell
descriptions={
'tcr_xgboost': '''## TCR: qué se implementa

Se sigue [TCR (Zühlke y Kudenko,2025)](https://doi.org/10.1007/s10994-024-06704-x),
con [referencia oficial](https://github.com/montymaxzuehlke/tcr), commit
`b73caef801b002569dbb95fbb7b229f08e0a78c2`. La sensibilidad de cada fila es el máximo
de `|y_i−y_j| / (distancia(x_i,x_j)+1e-7)` en el fit; el objetivo se lleva a[0,1].
Robustez=`1/(1+sensibilidad)`. Se reduce el peso de la fracción menos robusta y se
reentrena XGBoost. Los pesos son positivos: ninguna fila se elimina.

Para distancias se usa preparación SVM y MinMax aprendido en fit. El XGBoost conserva
su propia mediana/moda y categorías nativas. Se reutilizan los hiperparámetros base
seleccionados en la búsqueda clásica **dentro del fit externo correspondiente**; para
el ajuste final se usan los elegidos con todo train. No se usan los parámetros finales
del train completo dentro de los folds externos. Es una selección secuencial de base
y ponderación en train, no una búsqueda conjunta de todos los hiperparámetros.

Grilla: control sin ponderación + fracción .05/.10/.20 × peso .3/.6/.9, diez candidatos.
Todos los cálculos de robustez se repiten con solo el fit interno. Las métricas de
validación/test se calculan sin pesos. Los outliers se conservan; robustez baja no
implica que una fila sea errónea. El archivo pesos_train.csv contiene robustez y pesos
en orden canónico, sin IDs ni notas.''',
'tabicl_v2': '''## TabICLv2 oficial: qué se ejecuta

Paquete `tabicl==2.2.0`, [implementación oficial](https://github.com/soda-inria/tabicl)
y [artículo ICML2026](https://proceedings.mlr.press/v306/qu26a.html). Checkpoint oficial
de regresión `tabicl-regressor-v2-20260212.ckpt`, revisión de HuggingFace
`4dcd344ece2c00be9e831fdd35bed57b5ad83e19`, SHA256
`0db9cb538f114e79026bf08f45f41ad8dd7ad2de2aaca9a5ca8cd3bd9748ae7a`.

Inferencia local en contexto, **sin fine-tuning**: ocho estimadores, CPU cuatro hilos,
batch de ensamble1, semilla42. Preparación externa idéntica a SVM/TabPFN original.
Configuración fijada antes de evaluar: `norm_methods=['none']` evita transformaciones
de potencia/cuantiles y ruido RTDL; `outlier_threshold=infinity` desactiva el tratamiento
de outliers. La normalización numérica interna del modelo sigue activa. Se conservan
todas las filas; no se submuestrean estudiantes. Esta configuración controlada no
reproduce exactamente todos los defaults ni los benchmarks del artículo.

Cinco folds externos idénticos; **no hay selección interna**, porque no se ajustan
hiperparámetros. Cada contexto contiene solo fit. Los pesos quedan fijos y locales.
Los modelos serializados conservan el contexto y una referencia al checkpoint, evitando
duplicar114MB de pesos por fold. No requieren enviar datos a APIs.''',
'hrt_boost': '''## HRT-Boost oficial: qué se ejecuta

Paquete `hrt-boost==0.1.0`, instalado desde el commit oficial
`ed3885d7e089e489415637556b818d0284b123a6` del
[repositorio](https://github.com/Hongyi-Li-sz/HRT-Boost).
[Artículo](https://arxiv.org/abs/2605.23422). Se utiliza su HRTBoostingRegressor
sin reescribir el algoritmo: boosting de residuos con árboles oblicuos y modelos
lineales regularizados. Los nodos se ajustan con el procedimiento hinge y damping
de la implementación publicada. No se atribuye una garantía de mejora en test a
un descenso de error empírico durante el entrenamiento.

Pipeline con preparación canónica SVM dentro de fit. Grilla de doce candidatos:
árboles10/30 × profundidad1/2 × ridge_alpha1/10/100. Learning_rate0.1,
min_points80, step_sizeauto y semilla42 fijados antes de test. Las hojas grandes
y la regularización buscan limitar la capacidad en esta muestra pequeña.
Cinco folds externos y cinco internos por estudiante; selección por RMSE.'''}

for key,title in [('tcr_xgboost','TCR-XGBoost'),('tabicl_v2','TabICLv2'),('hrt_boost','HRT-Boost')]:
    cells=[md(f'# E3 — {title}\n\nEvaluación local del método elegido por el usuario. '
              'Los resultados se guardan separados de los modelos previos y del dashboard.'),
        md(descriptions[key]),
        md('''## Datos y protocolo compartido

Misma fuente real y reglas de negocio de entregable3.py; sin aumentación, mismos15
predictores y objetivo nota_primer_parcial. ID, periodo, fila fuente y nota_final
excluidos como entradas. Train1309 filas/1293 estudiantes, test202530 con188 filas/
188 estudiantes, sin personas compartidas. Los cinco folds externos se verifican
contra los archivos canónicos. Todo preprocesador se aprende exclusivamente en fit.

La configuración final se guarda antes de predecir test. RMSE, MAE, MAPE(%) y R²
se calculan con la función del tablero en escala original, sin recortar predicciones.
Se separan media/SD de folds(ddof0), OOF reunido y test temporal. MAPE es sensible
a notas próximas a cero. Las métricas de CV no se mezclan con las de test.'''),
        code(f'''from pathlib import Path
import sys
import pandas as pd
from IPython.display import display
BOOK=Path.cwd() if (Path.cwd()/'entregable3.py').exists() else Path.cwd()/'Precalculo'
sys.path.insert(0,str(BOOK.resolve()))
from comparacion_seleccionados_e3 import run,candidate_grid
key={key!r}
display(pd.DataFrame(candidate_grid(key)))
report=run(key,force=False)
display(pd.DataFrame(report['cv']).round(6))
display(pd.DataFrame(report['fold_audit']))
print('Parámetros finales:',report['best_params'])
print('Base XGBoost:',report['xgboost_base_params'])'''),
        md('''## Comparación con las referencias anteriores

Cada panel tiene su propia métrica y escala. Naranja identifica este método;
verde, TabPFN original. La tabla incluye las etapas nuevas completadas hasta este
método, respetando el orden TCR → TabICL → HRT. Los modelos activos del dashboard
y los notebooks históricos se conservan.'''),
        code('''from evaluar_tabpfn25_finetuned_e3 import show
show(report)
display(pd.DataFrame(report['family_vs_svm']).round(6))'''),
        md('''## Contrastes estadísticos

Permutación bilateral pareada por estudiante99999 y bootstrap pareado10000,
semilla42. Diferencia=método actual menos referencia: negativa favorece al actual
para RMSE y positiva para R². El p-valor de ambas métricas coincide porque son el
mismo contraste sobre SSE en el mismo test, no dos evidencias independientes.

Se aplica Holm a los dos pares actuales (SVM y TabPFN original) y se muestra además
Holm para la familia acumulada de candidatos conocidos frente al SVM. Los IC son
marginales, sin ajuste simultáneo. No basta que p sea pequeño: debe comprobarse
la dirección de la diferencia. La inferencia sigue siendo exploratoria por uso
repetido de202530 y es condicional a estos modelos; no incluye variabilidad de
reentrenamiento ni demuestra equivalencia si no se rechaza H0.'''),
        code('''for comp in report['paired_comparisons']:
    row=comp['rows'][0]
    print(comp['referencia'],'deltaRMSE=',round(row['diferencia_ajustado_menos_referencia'],6),
          'p=',row['p_bilateral'],'p Holm=',row['p_Holm_dos_pares'])
print('Familia conocida:',len(report['family_vs_svm']),'candidatos vs SVM')
print('Resultados:',report['outputs'])
print('Modelo guardado localmente:',report['private_model'])'''),
        md('''## Reproducibilidad

Hashes de fuente, protocolo, módulos, versiones y referencias en reporte.json y
protocolo.json. Predicciones OOF/test sin IDs, grillas internas cuando corresponda,
auditoría y comparaciones CSV. Los estimadores/contextos se guardan únicamente en
modelos_preentrenados/, ignorado en Git. Usar el venv compartido y las versiones
de requirements_seleccionados_e3.txt; no se crea otro entorno.''')]
    nb=nbf.v4.new_notebook(cells=cells)
    nb.metadata['kernelspec']={'display_name':'Python (Precalculo/venv)','language':'python','name':'python3'}
    nb.metadata['language_info']={'name':'python','version':sys.version.split()[0]}
    path=BOOK/f'precalculo_{key}_e3.ipynb'
    nbf.write(nb,path)
    print(path)

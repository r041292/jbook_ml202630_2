"""Genera el notebook nuevo para evaluar pesos finales; no ajusta modelos."""
from pathlib import Path
import sys
import nbformat as nbf

book = Path(__file__).resolve().parent
md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
nb = nbf.v4.new_notebook(cells=[
    md('''# E3 — TabPFN 2.5 después de fine-tuning

Se evalúa el paquete local `20261015_091524_448419`, entregado por el usuario.
Checkpoint: `tabpfn_25_finetuned.ckpt`. Cinco épocas finales, 119 tensores de pesos
modificados respecto al checkpoint oficial. Se conserva el original como referencia.
Este notebook **solo realiza inferencia**, no vuelve a optimizar pesos.

El código de evaluación está en `evaluar_tabpfn25_finetuned_e3.py` y el de carga del paquete
en `finetune_tabpfn25_e3.load_bundle`. Usar el kernel del venv compartido del proyecto.'''),
    md('''## Integridad y protocolo

Se verifican los checksums de pesos, preprocesador y contexto; hashes de la fuente y del
script de entrenamiento; las 15 variables y el objetivo; la matriz transformada y las notas
del contexto frente a las 1309 filas de train canónico. El contexto excluye el test temporal.
La preparación es la misma del SVM: imputación, log1p en tiempos, escalado y one-hot.

Se predicen los mismos **188 estudiantes del periodo 202530**, con cuatro estimadores de
inferencia y semilla42, como TabPFN original. Se calculan RMSE, MAE, MAPE(%) y R² usando
la función del tablero, sin recortar notas predichas. Los resultados anteriores no se sobrescriben.

Las épocas se seleccionaron dentro de train con cinco folds por estudiante y se volvió a
partir del checkpoint oficial para el ajuste final con todo train. Los pesos finales ya vieron
todos esos estudiantes: **no pueden producir nuevas predicciones OOF válidas sobre train**.
La CV de selección de épocas tampoco constituye una CV externa anidada. Se compara aquí
el test temporal; obtener una nueva CV externa exigiría fine-tuning independiente dentro de
cada fit externo, incluyendo selección interna de épocas.'''),
    code('''from pathlib import Path
import sys
import pandas as pd
from IPython.display import display
BOOK = Path.cwd() if (Path.cwd() / 'entregable3.py').exists() else Path.cwd() / 'Precalculo'
sys.path.insert(0, str(BOOK.resolve()))
from evaluar_tabpfn25_finetuned_e3 import evaluate, show, DEFAULT_BUNDLE
report = evaluate(DEFAULT_BUNDLE, force=False)
print('Paquete:', report['bundle'])
print('Épocas finales:', report['epochs_final'])
print('Inferencia:', report['inference'])
print('Filas test:', report['partition']['test_valid'])'''),
    md('''## Comparación en el mismo test

Cada métrica tiene su propio panel y escala. Naranja identifica el modelo ajustado,
verde el TabPFN original y azul las referencias del tablero y logicDT.
Las diferencias estadísticas se calculan respecto al modelo original y al SVM.'''),
    code('''show(report)
table = pd.DataFrame(report['comparison_test'])
new = table.loc[table.Modelo.eq(report['model'])].iloc[0]
base = table.loc[table.Modelo.eq('TabPFN 2.5 original')].iloc[0]
print(f"Cambio RMSE frente al original: {new['RMSE']-base['RMSE']:+.6f}")
print(f"Reducción relativa de RMSE: {100*(base['RMSE']-new['RMSE'])/base['RMSE']:.3f}%")
print(f"Cambio R² frente al original: {new['R²']-base['R²']:+.6f}")'''),
    md('''## Contrastes pareados e incertidumbre

Se usa permutación pareada bilateral por estudiante (99999 permutaciones) y bootstrap
pareado por estudiante (10000 réplicas), semilla42. Los 188 estudiantes tienen una fila
cada uno. H0 supone intercambiabilidad de pérdidas cuadradas por estudiante.
La diferencia reportada es **ajustado menos referencia**: negativa favorece al ajustado
para RMSE y positiva para R². Los intervalos son IC95% percentiles sin ajuste simultáneo.

RMSE y R² dependen de la misma SSE en este test y dan el mismo contraste de permutación;
no se cuentan como evidencias independientes. Se aplica **Holm** a los dos pares de modelos
(ajustado vs original y ajustado vs SVM), a alpha .05. Se muestran p-valores crudos y ajustados.

La inferencia es exploratoria y condicional a estos modelos y este periodo: el test se ha
inspeccionado en etapas previas y no incluye variabilidad por reentrenar. No rechazar H0 no
demuestra equivalencia. Un buen valor puntual no basta para afirmar superioridad significativa.'''),
    code('''for comp in report['paired_comparisons']:
    row = comp['rows'][0]
    print(comp['referencia'])
    print(f"  p bilateral={row['p_bilateral']:.5f}; p Holm={row['p_Holm_dos_comparaciones']:.5f}")
    print('  Diferencia significativa al 5% (Holm):', row['significativa_al_5%_Holm'])
print('Resultados:', report['outputs'])'''),
    md('''## Artefactos

Reporte con procedencia y comparación, CSV de métricas y contrastes y predicciones test
comprimidas sin IDs en `resultados/e3/tabpfn_25_finetuned/20261015_091524_448419/`.
Los pesos y el contexto permanecen en su carpeta local original. El dashboard y sus modelos
activos se conservan; la evaluación permite decidir su posterior integración.'''),
])
nb.metadata['kernelspec'] = {'display_name': 'Python (Precalculo/venv)', 'language': 'python', 'name': 'python3'}
nb.metadata['language_info'] = {'name': 'python', 'version': sys.version.split()[0]}
path = book/'precalculo_tabpfn25_finetuned_e3.ipynb'
nbf.write(nb, path)
print(path)

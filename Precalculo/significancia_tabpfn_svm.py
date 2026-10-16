"""Prueba pareada condicional sobre el test temporal, sin reajustar modelos."""
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import permutation_test

from entregable3 import BOOK, OUTPUT, GROUP, TARGET, metrics, write_json
from evaluacion_nuevos_e3 import partitions, provenance


def compare(n_permutations=99999, n_bootstrap=10000, seed=42):
    import json
    _, test, _, _ = partitions()
    folder = OUTPUT / 'tabpfn_25'
    previous = json.loads((folder / 'reporte.json').read_text(encoding='utf-8'))
    if previous['provenance'] != provenance('tabpfn_25'):
        raise ValueError('Resultados TabPFN desactualizados respecto a su procedencia.')
    tab = pd.read_csv(folder / 'test_predictions.csv.gz')
    svm = pd.read_csv(OUTPUT / 'test.csv.gz')
    for frame in [tab, svm]:
        np.testing.assert_allclose(frame[TARGET], test[TARGET], rtol=0, atol=1e-12)
        np.testing.assert_array_equal(frame['periodo'], test['periodo'])
    y = test[TARGET].to_numpy(float)
    # El export TabPFN fue generado desde float32: recuperar sus valores binarios
    # originales antes de pasar a float64 evita pérdida por representación CSV.
    a = tab['prediccion'].to_numpy().astype(np.float32).astype(np.float64)
    b = svm['svm'].to_numpy(float)
    for metric, value in metrics(y, a).items():
        np.testing.assert_allclose(value, previous['test'][metric], atol=1e-12, rtol=0)
    ea, eb = np.square(y-a), np.square(y-b)
    codes, ids = pd.factorize(test[GROUP], sort=False)
    groups = len(ids)
    # Una sola decisión de intercambio por estudiante, incluso si tuviese varias filas.
    aggregate = lambda values: np.bincount(codes, weights=values, minlength=groups)
    se_a, se_b = aggregate(ea), aggregate(eb)
    delta = se_a-se_b
    result = permutation_test((delta,), lambda x, axis: np.sum(x, axis=axis),
                              permutation_type='samples', vectorized=True,
                              n_resamples=n_permutations, batch=512,
                              alternative='two-sided', rng=np.random.default_rng(seed))
    # Mantener la unidad estudiante también en los intervalos pareados.
    counts = aggregate(np.ones(len(y)))
    sy, sy2 = aggregate(y), aggregate(y*y)
    rng = np.random.default_rng(seed)
    draws_rmse, draws_r2 = [], []
    for start in range(0, n_bootstrap, 512):
        ix = rng.integers(groups, size=(min(512, n_bootstrap-start), groups))
        n = counts[ix].sum(axis=1)
        sa, sb = se_a[ix].sum(axis=1), se_b[ix].sum(axis=1)
        sst = sy2[ix].sum(axis=1) - sy[ix].sum(axis=1)**2/n
        if np.any(sst <= 0):
            raise ValueError('Bootstrap con varianza objetivo nula; revisar el procedimiento.')
        draws_rmse.extend(np.sqrt(sa/n)-np.sqrt(sb/n))
        draws_r2.extend((sb-sa)/sst)
    score_a, score_b = metrics(y, a), metrics(y, b)
    rows = []
    for metric, draws in [('RMSE', draws_rmse), ('R²', draws_r2)]:
        lo, hi = np.quantile(draws, [.025, .975])
        rows.append({'metrica': metric, 'TabPFN': score_a[metric], 'SVM': score_b[metric],
                     'TabPFN_menos_SVM': score_a[metric]-score_b[metric],
                     'IC_2.5%': float(lo), 'IC_97.5%': float(hi),
                     'p_bilateral': float(result.pvalue), 'alpha': .05,
                     'rechaza_H0': bool(result.pvalue < .05)})
    paths = ['significancia_tabpfn_svm.py', 'resultados/e3/test.csv.gz',
             'resultados/e3/tabpfn_25/test_predictions.csv.gz',
             'resultados/e3/tabpfn_25/reporte.json']
    report = {
        'test_period': 202530, 'n_rows': len(y), 'n_students': groups,
        'method': 'Permutación pareada bilateral de etiquetas de modelo por estudiante',
        'null': 'Intercambiabilidad de las pérdidas cuadradas pareadas de ambos modelos por estudiante',
        'statistic': 'Suma de pérdidas cuadradas TabPFN menos SVM',
        'n_permutations': n_permutations, 'n_bootstrap': n_bootstrap, 'seed': seed,
        'pvalue_monte_carlo_se_approx': float(2*np.sqrt((result.pvalue/2)*(1-result.pvalue/2)/(n_permutations+1))),
        'rows': rows,
        'equivalence': 'En el mismo test, RMSE=sqrt(SSE/n) y R2=1-SSE/SST. '
                       'Al intercambiar predicciones SSE_A+SSE_B es constante y SST/n no cambia. '
                       'Ambas diferencias son transformaciones monótonas impares de SSE_A-SSE_B, '
                       'por lo que el mismo contraste pareado produce el mismo p-valor. '
                       'No son dos evidencias independientes ni dos pruebas distintas.',
        'scope': 'Inferencia exploratoria condicional a estos dos modelos y al periodo 202530. '
                 'Supone estudiantes independientes e intercambiabilidad pareada bajo H0; '
                 'no incorpora variabilidad de reentrenamiento ni garantiza otros periodos. '
                 'El test ya fue inspeccionado previamente. No rechazar H0 no prueba equivalencia.',
        'source_sha256': {name: hashlib.sha256((BOOK/name).read_bytes()).hexdigest() for name in paths},
    }
    write_json(folder/'significancia_vs_svm.json', report)
    pd.DataFrame(rows).to_csv(folder/'significancia_vs_svm.csv', index=False)
    return report


def notebook_cells():
    import nbformat as nbf
    return [nbf.v4.new_markdown_cell('''## Pesos preentrenados y significancia frente al SVM

Los pesos oficiales de TabPFN 2.5 se mantienen fijos: **no se entrenaron desde cero
ni se hizo fine-tuning con estos estudiantes**. `fit(X_train, y_train)` aprende la preparación
y establece los ejemplos etiquetados como contexto para la inferencia. Por tanto, sí utiliza
las notas de train para predecir; no funciona únicamente con los pesos y una fila aislada.
En cada fold, el contexto excluye todos los estudiantes de validación. En el ajuste final,
el contexto son las 1309 filas de train y se predicen las 188 filas del periodo 202530.
Los cuatro estimadores son variantes de inferencia del ensamble, no cuatro redes reentrenadas.
Ver el [artículo](https://arxiv.org/html/2511.08667v2) y `tabpfn_pipeline()`.

Se realiza una **prueba bilateral de permutación pareada**, con 99999 permutaciones,
semilla 42 y alpha .05, sobre las predicciones ya obtenidas. Se intercambian las etiquetas
de modelo dentro de cada estudiante, manteniendo juntos todos sus registros; aquí son
188 estudiantes con una fila cada uno. H0 supone intercambiabilidad de las pérdidas
cuadradas pareadas. El estadístico es SSE_TabPFN − SSE_SVM. También se calculan IC95%
percentiles con 10000 réplicas bootstrap pareadas por estudiante.

Para el mismo test, `RMSE = sqrt(SSE/n)` y `R² = 1 − SSE/SST`, con SST común a ambos.
Durante las permutaciones la suma SSE_TabPFN + SSE_SVM se conserva. Las diferencias de RMSE
y R² son transformaciones monótonas (de signo opuesto) de la diferencia SSE; por eso este
contraste produce el mismo p-valor para las dos métricas. **No son dos evidencias independientes**.
No se aplica un t-test a los cinco folds, cuyos modelos comparten datos de entrenamiento.
Referencia: [permutación pareada en SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html).
'''), nbf.v4.new_code_cell('''from significancia_tabpfn_svm import compare
significance = compare()
display(pd.DataFrame(significance['rows']).round(6))
print('Permutaciones:', significance['n_permutations'])
print('Bootstrap:', significance['n_bootstrap'])
print('Conclusión al 5%:', 'diferencia significativa' if significance['rows'][0]['rechaza_H0']
      else 'no se rechaza H0; evidencia insuficiente para declarar una diferencia')
print(significance['scope'])'''), nbf.v4.new_markdown_cell('''La diferencia puntual favorece a TabPFN,
pero **p = 0.06888 > 0.05** y ambos intervalos incluyen cero. No se demuestra una mejora
estadísticamente significativa en RMSE o R², ni se demuestra que los modelos sean equivalentes.
El contraste es exploratorio, condicional a los modelos ajustados y a este periodo; no incluye
variabilidad por reentrenamiento. Los IC de esta sección usan 10000 réplicas, frente a las
1000 de la sección previa; las pequeñas diferencias numéricas no cambian la conclusión.''')]


if __name__ == '__main__':
    import json
    import sys
    print(json.dumps(compare(), ensure_ascii=False, indent=2))
    if '--update-notebook' in sys.argv:
        import nbformat as nbf
        path = BOOK/'precalculo_tabpfn_25_e3.ipynb'
        notebook = nbf.read(path, as_version=4)
        marker = '## Pesos preentrenados y significancia frente al SVM'
        indexes = [k for k, cell in enumerate(notebook.cells) if cell.source.startswith(marker)]
        if indexes:
            notebook.cells = notebook.cells[:indexes[0]]
        notebook.cells.extend(notebook_cells())
        nbf.write(notebook, path)

"""E3: contraste pareado tipo Diebold-Mariano agrupado por estudiante, modelo vs SVM lineal.

Usa solo predicciones OOF ya guardadas (un GroupKFold 5 canónico); no entrena ni lee el test.
Pérdida = error cuadrático por fila; se suma por estudiante y se prueba la media de la
diferencia con error estándar robusto por cluster. IC por bootstrap de estudiantes.
Ejecutar: Precalculo/venv/Scripts/python.exe Precalculo/contraste_estudiante_e3.py
"""
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

from entregable3 import GROUP, OUTPUT, TARGET, load_partitions, write_json

OUT = OUTPUT / 'contraste_estudiante'
ACTIVE = OUTPUT / 'originales_busquedas/20261020_153034_consolidada/train.csv.gz'
ACTIVE_KEYS = {'Kernel Ridge RBF': 'm5', 'GPR–XGBoost (OOF agrupado)': 'm15', 'Truncated Newton KRR RBF': 'm19'}
HISTORICAL = {'Kernel Ridge RBF': ('scopus/kernel_ridge/train_predictions.csv.gz', 'prediccion'),
          'GPR–XGBoost (OOF agrupado)': ('gpr_xgb/train_predictions.csv.gz', 'prediccion'),
          'Truncated Newton KRR RBF': ('tn_krr/train_predictions.csv.gz', 'prediccion')}


def clustered_test(e_ref, e_new, groups, boots=2000, seed=42):
    diff = e_new - e_ref
    s = pd.Series(diff).groupby(groups).sum()
    n = pd.Series(diff).groupby(groups).size()
    G, total = len(s), n.sum()
    mean = s.sum() / total
    se = np.sqrt(G / (G - 1) * ((s - mean * n) ** 2).sum()) / total
    t = mean / se
    ids = s.index
    sa = pd.Series(e_ref).groupby(groups).sum().reindex(ids).to_numpy()
    sb = pd.Series(e_new).groupby(groups).sum().reindex(ids).to_numpy()
    N = n.to_numpy()
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(boots):
        k = rng.integers(0, G, G)
        draws.append(np.sqrt(sb[k].sum() / N[k].sum()) - np.sqrt(sa[k].sum() / N[k].sum()))
    lo, hi = np.quantile(draws, [.025, .975])
    return {'estudiantes': G, 'delta_MSE': mean, 'SE_cluster': se, 'z': t,
            'p_bilateral': 2 * stats.norm.sf(abs(t)),
            'delta_RMSE': np.sqrt(e_new.mean()) - np.sqrt(e_ref.mean()),
            'IC95_boot_inf': lo, 'IC95_boot_sup': hi}


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    train, _, _ = load_partitions()
    y, groups = train[TARGET].to_numpy(float), train[GROUP].to_numpy()
    saved = pd.read_csv(OUTPUT / 'train.csv.gz')
    np.testing.assert_allclose(saved[TARGET], y, atol=1e-9)
    e_ref = (saved['svm'].to_numpy(float) - y) ** 2
    rows = []
    active = pd.read_csv(ACTIVE)
    np.testing.assert_array_equal(active['fold'].to_numpy(int), saved['fold'].to_numpy(int))
    for name, key in ACTIVE_KEYS.items():
        rows.append({'Version': 'activa (búsqueda HPO, dashboard)', 'Modelo': name, 'Referencia': 'SVM lineal',
                     **clustered_test(e_ref, (active[key].to_numpy(float) - y) ** 2, groups)})
    for name, (path, col) in HISTORICAL.items():
        a = pd.read_csv(OUTPUT / path)
        np.testing.assert_array_equal(a['fold'].to_numpy(int), saved['fold'].to_numpy(int))
        np.testing.assert_allclose(a[TARGET].to_numpy(float), y, atol=1e-9)
        rows.append({'Version': 'histórica (parámetros originales)', 'Modelo': name, 'Referencia': 'SVM lineal',
                     **clustered_test(e_ref, (a[col].to_numpy(float) - y) ** 2, groups)})
    frame = pd.DataFrame(rows)
    frame['p_Holm3'] = frame.groupby('Version')['p_bilateral'].transform(
        lambda p: multipletests(p, method='holm')[1])
    frame.to_csv(OUT / 'contrastes_vs_svm.csv', index=False)
    write_json(OUT / 'reporte.json', {'familia': 'Holm3 (3 contrastes pedidos)', 'filas': frame.to_dict('records'),
               'alcance': 'OOF de un solo GroupKFold 5; sin test; sin reentrenar; exploratorio'})
    print(frame.round(5).to_string())


if __name__ == '__main__':
    run()

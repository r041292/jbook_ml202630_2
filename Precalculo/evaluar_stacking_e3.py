"""E3: stacking con pesos convexos (no negativos, suma 1) sobre modelos propios.

Bases: solo implementaciones propias del proyecto (TN-KRR, LinXGBoost, HRT-Boost,
logicDT propio, RIM). Se excluyen los preentrenados (TabPFN, TabICLv2, TabFM) y los
que son un import directo (Kernel Ridge, SVR, XGBoost, CatBoost, GPR). No reentrena
las bases: usa sus predicciones OOF canónicas (mismos cinco folds externos).

Meta-modelo (Breiman 1996; van der Laan, Polley y Hubbard 2007): mínimos cuadrados
sobre el simplex, resuelto aquí con SLSQP. Para cada fold externo k los pesos se
estiman solo con las OOF de las filas de los otros folds y se aplican al fold k.
Limitación: esas OOF provienen de bases cuyo ajuste vio estudiantes del fold k, por lo
que la evaluación puede ser levemente optimista; una CV totalmente anidada exigiría
reentrenar todas las bases.
Ejecutar: Precalculo/venv/Scripts/python.exe Precalculo/evaluar_stacking_e3.py
"""
from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize
from statsmodels.stats.multitest import multipletests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'Dash'))
from model_timing import TimingRun, file_hash  # noqa: E402

from entregable3 import OUTPUT, TARGET, metrics, source_hashes, write_json  # noqa: E402

VARIANT = 'ampliado' if '--ampliado' in sys.argv else 'propios'
OUT = OUTPUT / ('stacking' if VARIANT == 'propios' else 'stacking_ampliado')
# nombre -> (archivo train/OOF, columna predicción, archivo test, columna predicción test)
BASES = {
    'TN-KRR': ('tn_krr/train_predictions.csv.gz', 'prediccion', 'tn_krr/test_predictions.csv.gz', 'prediccion'),
    'LinXGBoost': ('linxgboost/oof_predictions.csv.gz', 'prediction', 'linxgboost/test_predictions.csv.gz', 'prediction'),
    'HRT-Boost': ('hrt_boost/train_predictions.csv.gz', 'prediccion', 'hrt_boost/test_predictions.csv.gz', 'prediccion'),
    'logicDT propio': ('logicdt/train_predictions.csv.gz', 'prediccion', 'logicdt/test_predictions.csv.gz', 'prediccion'),
    'RIM': ('rim/train_predictions.csv.gz', 'prediccion', 'rim/test_predictions.csv.gz', 'prediccion'),
}
# Variante ampliada (a solicitud del usuario): se añaden modelos basados en librerías.
EXTRA = {
    'Kernel Ridge RBF': ('scopus/kernel_ridge/train_predictions.csv.gz', 'prediccion', 'scopus/kernel_ridge/test_predictions.csv.gz', 'prediccion'),
    'SVR RBF': ('svr_rbf_raffle/svr_rbf/train_predictions.csv.gz', 'prediccion', 'svr_rbf_raffle/svr_rbf/test_predictions.csv.gz', 'prediccion'),
    'XGBoost': ('clasicos/train_predictions.csv.gz', 'xgboost', 'clasicos/test_predictions.csv.gz', 'xgboost'),
    'CatBoost': ('scopus/catboost/train_predictions.csv.gz', 'prediccion', 'scopus/catboost/test_predictions.csv.gz', 'prediccion'),
    'GPR sola': ('gpr_xgb/train_predictions.csv.gz', 'gpr_solo_prediccion', 'gpr_xgb/test_predictions.csv.gz', 'gpr_solo_prediccion'),
}
if VARIANT == 'ampliado':
    BASES = {**BASES, **EXTRA}
EXCLUIDOS = ['TabPFN 2.5 original', 'TabPFN 2.5 fine-tuned', 'TabICLv2', 'TabFM']
if VARIANT == 'propios':
    EXCLUIDOS += ['Kernel Ridge RBF', 'SVR RBF', 'XGBoost y variantes', 'CatBoost', 'GPR sola']


def simplex_weights(P, y):
    """argmin ||P w - y||^2 con w >= 0 y sum(w) = 1."""
    k = P.shape[1]
    result = minimize(lambda w: np.mean((P @ w - y) ** 2), np.full(k, 1 / k),
                      jac=lambda w: 2 * P.T @ (P @ w - y) / len(y), method='SLSQP',
                      bounds=[(0, 1)] * k, constraints=[{'type': 'eq', 'fun': lambda w: w.sum() - 1}],
                      options={'ftol': 1e-14, 'maxiter': 500})
    assert result.success, result.message
    w = np.clip(result.x, 0, None)
    return w / w.sum()


def corrected_t(delta, ratio, label):
    delta = np.asarray(delta, float)
    n = len(delta)
    se = np.sqrt((1 / n + ratio) * delta.var(ddof=1))
    t = delta.mean() / se
    half = stats.t.ppf(.975, n - 1) * se
    return {'contraste': label, 'delta_RMSE_medio': delta.mean(), 'SE_corregido': se, 't': t,
            'df': n - 1, 'p_bilateral': 2 * stats.t.sf(abs(t), n - 1),
            'IC95_inferior': delta.mean() - half, 'IC95_superior': delta.mean() + half}


def load_inputs():
    train = pd.read_csv(OUTPUT / 'train.csv.gz')
    test = pd.read_csv(OUTPUT / 'test.csv.gz')
    folds = train['fold'].to_numpy(int)
    y, y_test = train[TARGET].to_numpy(float), test[TARGET].to_numpy(float)
    P, T = {}, {}
    for name, (tr, tr_col, te, te_col) in BASES.items():
        a, b = pd.read_csv(OUTPUT / tr), pd.read_csv(OUTPUT / te)
        assert len(a) == len(train) and len(b) == len(test), name
        ya = a['y_true'] if 'y_true' in a else a.get(TARGET)
        if ya is not None:
            np.testing.assert_allclose(ya.to_numpy(float), y, atol=1e-9, err_msg=name)
        if TARGET in b:
            np.testing.assert_allclose(b[TARGET].to_numpy(float), y_test, atol=1e-9)
        if 'fold' in a:
            np.testing.assert_array_equal(a['fold'].to_numpy(int), folds, err_msg=name)
        P[name], T[name] = a[tr_col].to_numpy(float), b[te_col].to_numpy(float)
        assert np.isfinite(P[name]).all() and np.isfinite(T[name]).all(), name
    return train, test, folds, y, y_test, pd.DataFrame(P), pd.DataFrame(T)


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    train, test, folds, y, y_test, P, T = load_inputs()
    timing = TimingRun(f'Stacking convexo ({VARIANT}) · evaluación', {
        'script': 'Precalculo/evaluar_stacking_e3.py', 'script_sha256': file_hash(__file__),
        'timing_sha256': file_hash(Path(__file__).parent.parent / 'Dash/model_timing.py'),
        'command': 'Precalculo/venv/Scripts/python.exe Precalculo/evaluar_stacking_e3.py' + (' --ampliado' if VARIANT == 'ampliado' else ''),
        'source_sha256': source_hashes(), 'bases': list(BASES), 'excluidos': EXCLUIDOS,
        'cv': '5 folds externos canónicos; pesos estimados con OOF de los otros 4 folds',
        'alcance_tiempos': ('Solo meta-modelo (pesos) e inferencia de la combinación; las bases no se '
                            'reentrenan: sus tiempos están en sus propias ejecuciones o No medido.'),
        'train_rows': len(train), 'test_rows': len(test), 'seed': 'No aplica (optimización determinista)'})
    status = 'fallida'
    try:
        names = list(P.columns)
        oof = {m: np.full(len(y), np.nan) for m in ['Stacking convexo', 'Promedio uniforme']}
        weights, rows = [], []
        for k in sorted(set(folds)):
            fit, val = folds != k, folds == k
            with timing.measure('Entrenamiento/refit', f'pesos fold {k}', int(fit.sum()), meta='SLSQP simplex'):
                w = simplex_weights(P.loc[fit].to_numpy(), y[fit])
            with timing.measure('Inferencia', f'OOF fold {k}', int(val.sum()), repetitions=1, warmup=0):
                oof['Stacking convexo'][val] = P.loc[val].to_numpy() @ w
            oof['Promedio uniforme'][val] = P.loc[val].mean(axis=1)
            weights.append({'fold': k, **dict(zip(names, w))})
            for m in oof:
                rows.append({'Modelo': m, 'Fold': k, **metrics(y[val], oof[m][val])})
            for n in names:
                rows.append({'Modelo': n, 'Fold': k, **metrics(y[val], P.loc[val, n])})
            rows.append({'Modelo': 'SVM lineal', 'Fold': k, **metrics(y[val], train.loc[val, 'svm'])})
        frame = pd.DataFrame(rows)
        wide = frame.pivot(index='Fold', columns='Modelo', values='RMSE')
        ratio = 0.25
        tests = [corrected_t(wide['Stacking convexo'] - wide['SVM lineal'], ratio, 'Stacking convexo - SVM lineal (primario)')]
        sec = [corrected_t(wide['Stacking convexo'] - wide['Promedio uniforme'], ratio, 'Stacking convexo - Promedio uniforme'),
               corrected_t(wide['Stacking convexo'] - wide['TN-KRR'], ratio, 'Stacking convexo - TN-KRR (mejor base)')]
        holm = multipletests([s['p_bilateral'] for s in sec], method='holm')[1]
        for s, p in zip(sec, holm):
            s['p_Holm2'] = float(p)
        tests += sec
        # Pesos finales con todas las OOF; test solo después de fijarlos.
        with timing.measure('Entrenamiento/refit', 'pesos final', len(y), meta='SLSQP simplex'):
            w_final = simplex_weights(P.to_numpy(), y)
        write_json(OUT / 'pesos_finales_antes_test.json', dict(zip(names, map(float, w_final))))
        with timing.measure('Inferencia', 'test temporal', len(y_test), repetitions=1, warmup=0):
            pred_test = T.to_numpy() @ w_final
        uniform_test = T.mean(axis=1).to_numpy()
        test_metrics = {'Stacking convexo': metrics(y_test, pred_test),
                        'Promedio uniforme': metrics(y_test, uniform_test),
                        **{n: metrics(y_test, T[n]) for n in names},
                        'SVM lineal': metrics(y_test, test['svm'])}
        frame.to_csv(OUT / 'fold_metrics.csv', index=False)
        pd.DataFrame(weights).to_csv(OUT / 'pesos_por_fold.csv', index=False)
        pd.DataFrame(tests).to_csv(OUT / 'contrastes_cv.csv', index=False)
        pd.DataFrame({'stacking': oof['Stacking convexo'], 'uniforme': oof['Promedio uniforme'],
                      'fold': folds}).to_csv(OUT / 'oof_stacking.csv.gz', index=False, compression='gzip')
        pd.DataFrame({'stacking': pred_test, 'uniforme': uniform_test}).to_csv(
            OUT / 'test_predictions.csv.gz', index=False, compression='gzip')
        corr = (P.sub(pd.Series(y), axis=0)).corr()
        report = {'bases': names, 'excluidos': EXCLUIDOS, 'pesos_finales': dict(zip(names, map(float, w_final))),
                  'RMSE_CV_media': wide.mean().to_dict(), 'RMSE_CV_SD': wide.std(ddof=0).to_dict(),
                  'RMSE_OOF_reunido': {'Stacking convexo': metrics(y, oof['Stacking convexo'])['RMSE'],
                                       'Promedio uniforme': metrics(y, oof['Promedio uniforme'])['RMSE'],
                                       **{n: metrics(y, P[n])['RMSE'] for n in names}},
                  'contrastes_cv': tests, 'test': test_metrics,
                  'correlacion_errores_OOF': corr.round(4).to_dict(),
                  'nota': ('Exploratorio: pesos de fold estimados con OOF cuyas bases vieron el fold evaluado; '
                           'test reutilizado, no selecciona nada.'),
                  'run_id': timing.run_id, 'source_sha256': source_hashes()}
        write_json(OUT / 'reporte.json', report)
        print(json.dumps(report, ensure_ascii=False, indent=1, default=float))
        status = 'completa'
    finally:
        timing.finish(status)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    run()

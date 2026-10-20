"""E3: CV agrupada repetida 5x5 con un contraste preespecificado SVR RBF vs SVM lineal.

Mismo protocolo anidado del proyecto (RMSE interno, GroupKFold por estudiante,
preprocesamiento dentro del pipeline) con cinco repeticiones de GroupKFold externo
barajado. No usa el test temporal ni modifica resultados previos.
Ejecutar desde la raíz: Precalculo/venv/Scripts/python.exe Precalculo/evaluar_cv_repetida_e3.py
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.exceptions import ConvergenceWarning
from sklearn.model_selection import GridSearchCV, GroupKFold, RandomizedSearchCV
from threadpoolctl import threadpool_limits

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'Dash'))
from model_timing import TimingRun, ZONE, file_hash  # noqa: E402

from entregable3 import (FEATURES, GRID, GROUP, OUTPUT, TARGET, BOOK, grouped_splits,  # noqa: E402
                         make_pipeline, metrics, source_hashes, write_json)
from evaluar_svr_rbf_raffle_e3 import (SVR_PARAM_DISTRIBUTIONS, SVR_SEARCH_ITERATIONS,  # noqa: E402
                                       _svr_pipeline, canonical_partitions)

KEY = 'cv_repetida'
OUT = OUTPUT / KEY
REPETITIONS, OUTER, SEED, N_JOBS = 5, 5, 42, 4
MODELS = {'SVM lineal': 'svm', 'SVR RBF': 'svr_rbf'}
PROTOCOL = {
    'contraste_preespecificado': 'RMSE(SVR RBF) - RMSE(SVM lineal) por (repetición, fold externo)',
    'motivo_de_la_eleccion': ('Misma familia de pérdida epsilon-insensible; solo cambia el kernel. '
                              'No se elige por tiempo ni por el test temporal.'),
    'estadistico': ('t remuestreado corregido de Nadeau-Bengio/Bouckaert-Frank: '
                    'SE^2=(1/J + n_val/n_fit)*s^2, J=25, s^2 muestral (ddof=1), df=J-1, bilateral'),
    'alfa': 0.05, 'multiplicidad': 'Familia de un solo contraste; sin ajuste de Holm',
    'alcance': ('Exploratorio: el candidato se identificó con resultados previos de CV/test del mismo '
                'conjunto. La repetición reduce varianza de partición, no la dependencia entre folds.'),
    'repeticiones': REPETITIONS, 'folds_externos': OUTER, 'folds_internos': 5,
    'barajado_externo': 'GroupKFold(shuffle=True, random_state=1000+r), r=1..5',
    'busqueda': {'SVM lineal': {'grilla': GRID, 'candidatos': 48},
                 'SVR RBF': {'distribuciones': 'SVR_PARAM_DISTRIBUTIONS (evaluar_svr_rbf_raffle_e3.py)',
                             'candidatos': SVR_SEARCH_ITERATIONS}},
    'test_temporal_usado': False,
}


def search(key, fit_frame, timing, batch):
    inner = grouped_splits(fit_frame)
    if key == 'svm':
        gs = GridSearchCV(make_pipeline(), GRID, scoring='neg_root_mean_squared_error', cv=inner,
                          refit=True, n_jobs=N_JOBS, error_score='raise')
        extra = {'candidates': 48}
    else:
        gs = RandomizedSearchCV(_svr_pipeline(), SVR_PARAM_DISTRIBUTIONS, n_iter=SVR_SEARCH_ITERATIONS,
                                scoring='neg_root_mean_squared_error', cv=inner, refit=True,
                                n_jobs=N_JOBS, random_state=SEED, error_score='raise')
        extra = {'candidates': SVR_SEARCH_ITERATIONS}
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='Found unknown categories')
        if key == 'svm':
            warnings.simplefilter('error', ConvergenceWarning)
        with threadpool_limits(limits=1), joblib.parallel_backend('loky', inner_max_num_threads=1):
            with timing.measure('Búsqueda', batch, len(fit_frame), model=key, inner_folds=5,
                                n_jobs=N_JOBS, refit_incluido=True, **extra):
                gs.fit(fit_frame[FEATURES], fit_frame[TARGET].to_numpy(float))
    # refit_time_ ya está dentro de la medida de búsqueda; no se suma otra vez.
    timing.record('Entrenamiento/refit (incluido en búsqueda)', batch, float(gs.refit_time_),
                  len(fit_frame), model=key, incluido_en='Búsqueda', best_params=gs.best_params_)
    return gs


def corrected_t(delta, ratio, label):
    delta = np.asarray(delta, float)
    j = len(delta)
    var = delta.var(ddof=1)
    se = np.sqrt((1 / j + ratio) * var)
    t = delta.mean() / se
    df = j - 1
    p = 2 * stats.t.sf(abs(t), df)
    half = stats.t.ppf(.975, df) * se
    return {'contraste': label, 'J': j, 'delta_RMSE_medio': delta.mean(), 'SD_delta': np.sqrt(var),
            'SE_corregido': se, 't': t, 'df': df, 'p_bilateral': p,
            'IC95_inferior': delta.mean() - half, 'IC95_superior': delta.mean() + half,
            'n_favor_SVR_RBF': int((delta < 0).sum()), 'ratio_val_fit': ratio}


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    protocol_path = OUT / 'protocolo_preespecificado.json'
    if not protocol_path.exists():
        write_json(protocol_path, {**PROTOCOL, 'fijado': datetime.now(ZONE).isoformat(),
                                   'script_sha256': file_hash(__file__), 'source_sha256': source_hashes()})
    train, test, _, _, audit = canonical_partitions()
    timing = TimingRun('SVM lineal vs SVR RBF · CV agrupada repetida 5x5', {
        'script': 'Precalculo/evaluar_cv_repetida_e3.py', 'script_sha256': file_hash(__file__),
        'timing_sha256': file_hash(Path(__file__).parent.parent / 'Dash/model_timing.py'),
        'command': 'Precalculo/venv/Scripts/python.exe Precalculo/evaluar_cv_repetida_e3.py',
        'source_sha256': source_hashes(), 'seed': SEED, 'protocol': PROTOCOL,
        'train_rows': len(train), 'train_students': train[GROUP].nunique(),
        'n_jobs_search': N_JOBS, 'inner_max_num_threads': 1,
        'cv': '5 repeticiones x 5 folds externos GroupKFold barajado; 5 internos por estudiante; test no usado',
        'expected_outer_fits': REPETITIONS * OUTER * len(MODELS)})
    status = 'fallida'
    try:
        rows, audits, oof = [], [], {k: np.full((REPETITIONS, len(train)), np.nan) for k in MODELS.values()}
        groups = train[GROUP].to_numpy()
        for r in range(1, REPETITIONS + 1):
            splitter = GroupKFold(n_splits=OUTER, shuffle=True, random_state=1000 + r)
            for fold, (fit, val) in enumerate(splitter.split(train[FEATURES], train[TARGET], groups), 1):
                fitting, validation = train.iloc[fit], train.iloc[val]
                assert not set(fitting[GROUP]) & set(validation[GROUP])
                audits.append({'rep': r, 'fold': fold, 'fit_rows': len(fit), 'val_rows': len(val),
                               'fit_students': fitting[GROUP].nunique(), 'val_students': validation[GROUP].nunique(),
                               'ratio_val_fit_students': validation[GROUP].nunique() / fitting[GROUP].nunique()})
                for name, key in MODELS.items():
                    batch = f'rep{r}_fold{fold}_{key}'
                    gs = search(key, fitting, timing, batch)
                    with timing.measure('Inferencia', 'OOF ' + batch, len(validation), repetitions=1, warmup=0):
                        pred = gs.best_estimator_.predict(validation[FEATURES])
                    oof[key][r - 1, val] = pred
                    rows.append({'Modelo': name, 'Repeticion': r, 'Fold': fold,
                                 **metrics(validation[TARGET], pred),
                                 'best_params': json.dumps(gs.best_params_, default=float),
                                 'RMSE_interno': float(-gs.best_score_)})
                    print(f'rep {r} fold {fold} {name}: RMSE {rows[-1]["RMSE"]:.6f}', flush=True)
                pd.DataFrame(rows).to_csv(OUT / 'fold_metrics_parcial.csv', index=False)
        frame = pd.DataFrame(rows)
        frame.to_csv(OUT / 'fold_metrics.csv', index=False)
        pd.DataFrame(audits).to_csv(OUT / 'auditoria_folds.csv', index=False)
        for key in MODELS.values():
            assert np.isfinite(oof[key]).all()
            pd.DataFrame(oof[key].T, columns=[f'rep{r}' for r in range(1, REPETITIONS + 1)]).to_csv(
                OUT / f'oof_{key}.csv.gz', index=False, compression='gzip')
        wide = frame.pivot_table(index=['Repeticion', 'Fold'], columns='Modelo', values='RMSE')
        delta = (wide['SVR RBF'] - wide['SVM lineal']).to_numpy()
        ratio = float(pd.DataFrame(audits)['ratio_val_fit_students'].mean())
        primary = corrected_t(delta, ratio, 'SVR RBF - SVM lineal (RMSE por repetición y fold)')
        r2 = frame.pivot_table(index=['Repeticion', 'Fold'], columns='Modelo', values='R²')
        by_rep = (wide['SVR RBF'] - wide['SVM lineal']).groupby(level=0).mean().tolist()
        naive_t = stats.ttest_1samp(delta, 0)
        report = {'protocolo': PROTOCOL, 'primario': primary,
                  'RMSE_medio': wide.mean().to_dict(), 'RMSE_SD': wide.std(ddof=1).to_dict(),
                  'R2_medio': r2.mean().to_dict(), 'delta_medio_por_repeticion': by_rep,
                  'p_t_ingenuo_no_valido': float(naive_t.pvalue),
                  'nota_p_ingenuo': 'Solo referencia: ignora la dependencia entre remuestreos y es optimista.',
                  'run_id': timing.run_id, 'source_sha256': source_hashes()}
        write_json(OUT / 'reporte.json', report)
        print(json.dumps(report, ensure_ascii=False, indent=1, default=float), flush=True)
        status = 'completa'
    finally:
        timing.finish(status)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    run()

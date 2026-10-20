"""Nested E3 evaluation for the paper-faithful TR-KRR solver."""
import gc
import hashlib
import importlib.metadata
import json
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import ParameterGrid
from threadpoolctl import threadpool_limits

from entregable3 import (BOOK, OUTPUT, FEATURES, GROUP, TARGET, grouped_splits,
                         metrics, source_hashes, write_json)
from evaluacion_nuevos_e3 import partitions
from tn_krr_e3 import make_model


LABEL = 'Truncated Newton KRR RBF'
GRID = {'alpha': [0.01, 0.1, 1.0, 10.0, 100.0],
        'gamma': [0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1.0]}
SOLVER = {'method': 'linear conjugate gradient on (K + alpha I) a = y',
          'max_iter': 200, 'cg_tolerance': 0.5, 'max_no_improve': 25,
          'initial_coefficients': 'zeros', 'early_stop_metric': 'L2 residual norm'}
ROOT = OUTPUT / 'tn_krr'
MODEL_DIR = BOOK / 'modelos_preentrenados/tn_krr'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def provenance():
    paths = ['tn_krr_e3.py', 'evaluar_tn_krr_e3.py', 'evaluacion_nuevos_e3.py',
             'resultados/e3/train.csv.gz', 'resultados/e3/test.csv.gz']
    return {**source_hashes(), **{p: sha256(BOOK / p) for p in paths},
            'versions': {name: importlib.metadata.version(name)
                         for name in ['numpy', 'pandas', 'scikit-learn', 'scipy']},
            'grid': list(ParameterGrid(GRID)), 'solver': SOLVER,
            'references': ['https://doi.org/10.3390/app12094252',
                           'https://doi.org/10.1016/j.knosys.2014.08.012']}


def fit(params, frame):
    with warnings.catch_warnings(), threadpool_limits(limits=1):
        warnings.filterwarnings('ignore', message='Found unknown categories')
        return make_model(**params).fit(frame[FEATURES], frame[TARGET])


def predict(model, frame):
    with warnings.catch_warnings(), threadpool_limits(limits=1):
        warnings.filterwarnings('ignore', message='Found unknown categories')
        values = np.asarray(model.predict(frame[FEATURES]), dtype=float)
    if values.shape != (len(frame),) or not np.isfinite(values).all():
        raise ValueError('Predicciones inválidas.')
    return values


def tune(frame, label, folder):
    candidates = list(ParameterGrid(GRID))
    path = folder / f'grid_{label}.csv'
    rows = pd.read_csv(path).to_dict('records') if path.exists() else []
    done = {(int(row['candidate']), int(row['inner_fold'])) for row in rows}
    splits = grouped_splits(frame)
    for candidate_id, params in enumerate(candidates, 1):
        for fold_id, (fit_idx, val_idx) in enumerate(splits, 1):
            if (candidate_id, fold_id) in done:
                continue
            started = time.perf_counter()
            model = fit(params, frame.iloc[fit_idx])
            estimator = model.named_steps['modelo']
            score = metrics(frame.iloc[val_idx][TARGET], predict(model, frame.iloc[val_idx]))
            rows.append({'candidate': candidate_id, 'inner_fold': fold_id, **params,
                         **score, 'cg_iterations': estimator.n_iter_,
                         'cg_residual_norm': estimator.residual_norm_,
                         'cg_converged': estimator.converged_,
                         'cg_stop_reason': estimator.stop_reason_,
                         'shared_students': len(set(frame.iloc[fit_idx][GROUP]) &
                                                set(frame.iloc[val_idx][GROUP])),
                         'seconds': time.perf_counter() - started})
            pd.DataFrame(rows).to_csv(path, index=False)
            del model
        values = [row['RMSE'] for row in rows if int(row['candidate']) == candidate_id]
        print(f'tn_krr {label}: {candidate_id}/{len(candidates)}, '
              f'RMSE={np.mean(values):.6f}', flush=True)
    scores = pd.DataFrame(rows).groupby('candidate').RMSE.mean()
    chosen = int(scores.idxmin())
    params = candidates[chosen - 1]
    return fit(params, frame), params, float(scores.loc[chosen])


def run():
    train, test, folds, audit = partitions()
    ROOT.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    stamp = provenance()
    protocol_path = ROOT / 'protocolo.json'
    previous = json.loads(protocol_path.read_text(encoding='utf-8')) if protocol_path.exists() else None
    if previous and previous['provenance'] != stamp:
        raise ValueError('Cambió la procedencia: preservar resultados y usar una carpeta nueva.')
    if (ROOT / 'reporte.json').exists():
        return json.loads((ROOT / 'reporte.json').read_text(encoding='utf-8'))
    if previous is None:
        write_json(protocol_path, {'provenance': stamp, 'test_used_for_selection': False,
            'method': '5 folds externos y 5 internos GroupKFold por estudiante; '
                      'RMSE interno; transformaciones ajustadas solo en fit.'})

    oof = np.full(len(train), np.nan)
    rows, audits = [], []
    for fold_id, (fit_idx, val_idx) in enumerate(folds, 1):
        metric_path = ROOT / f'externo_{fold_id}.json'
        prediction_path = ROOT / f'oof_{fold_id}.npy'
        model_path = MODEL_DIR / f'fold_{fold_id}.joblib'
        if metric_path.exists() and prediction_path.exists() and model_path.exists():
            saved = json.loads(metric_path.read_text(encoding='utf-8'))
            oof[val_idx] = np.load(prediction_path)
            rows.append(saved['metrics'])
            audits.append(saved['audit'])
            continue
        started = time.perf_counter()
        print(f'tn_krr: fold externo {fold_id}/5', flush=True)
        model, params, inner_rmse = tune(train.iloc[fit_idx], f'externo_{fold_id}', ROOT)
        oof[val_idx] = predict(model, train.iloc[val_idx])
        estimator = model.named_steps['modelo']
        metric_row = {'Modelo': LABEL, 'Fold': fold_id,
                      **metrics(train.iloc[val_idx][TARGET], oof[val_idx])}
        fold_audit = {'fold': fold_id, 'best_params': params, 'inner_rmse': inner_rmse,
                      'fit_rows': len(fit_idx), 'validation_rows': len(val_idx),
                      'shared_students': 0, 'cg_iterations': estimator.n_iter_,
                      'cg_residual_norm': estimator.residual_norm_,
                      'cg_converged': estimator.converged_,
                      'cg_stop_reason': estimator.stop_reason_,
                      'seconds': time.perf_counter() - started}
        joblib.dump(model, model_path)
        np.save(prediction_path, oof[val_idx])
        write_json(metric_path, {'metrics': metric_row, 'audit': fold_audit})
        rows.append(metric_row)
        audits.append(fold_audit)
        del model
        gc.collect()

    model, params, inner_rmse = tune(train, 'final', ROOT)
    joblib.dump(model, MODEL_DIR / 'modelo_final.joblib')
    write_json(ROOT / 'seleccion_antes_test.json',
               {'params': params, 'inner_rmse': inner_rmse, 'test_used': False})
    prediction = predict(model, test)
    restored = predict(joblib.load(MODEL_DIR / 'modelo_final.joblib'), test)
    np.testing.assert_allclose(restored, prediction, atol=1e-10, rtol=0)

    for split, frame, values in [('train', train, oof), ('test', test, prediction)]:
        table = frame[[TARGET, 'periodo', 'fila_fuente']].copy()
        table['prediccion'] = values
        if split == 'train':
            table['fold'] = pd.read_csv(OUTPUT / 'train.csv.gz').fold
        table.to_csv(ROOT / f'{split}_predictions.csv.gz', index=False, compression='gzip')
    fold_table = pd.DataFrame(rows)
    fold_table.to_csv(ROOT / 'fold_metrics.csv', index=False)
    score = metrics(test[TARGET], prediction)
    report = {'model': LABEL, 'key': 'tn_krr', 'test': score,
              'cv': [{'metric': name, 'mean_cv': float(fold_table[name].mean()),
                      'sd_cv_ddof0': float(fold_table[name].std(ddof=0)),
                      'oof_grouped': metrics(train[TARGET], oof)[name]} for name in score],
              'best_params': params, 'inner_rmse': inner_rmse, 'fold_audit': audits,
              'partition': audit, 'provenance': stamp, 'solver': SOLVER,
              'reference': 'https://doi.org/10.3390/app12094252; '
                           'solver details: https://doi.org/10.1016/j.knosys.2014.08.012',
              'private_model': str(MODEL_DIR / 'modelo_final.joblib')}
    write_json(ROOT / 'reporte.json', report)
    print(f'tn_krr TEST: {score}', flush=True)
    return report


if __name__ == '__main__':
    report = run()
    print(json.dumps({'model': report['model'], 'test': report['test'],
                      'best_params': report['best_params']}, ensure_ascii=False, indent=2))

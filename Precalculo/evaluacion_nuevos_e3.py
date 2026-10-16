"""Evaluación común de los experimentos logicDT y TabPFN 2.5, aislada del tablero."""
import gc
import hashlib
import importlib.metadata
import json
import os
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits

from entregable3 import (BOOK, OUTPUT, FEATURES, GROUP, NUMERIC, PERIOD, TARGET,
                        grouped_splits, load_partitions, make_pipeline, metrics,
                        source_hashes, write_json)
from logicdt_propio import LogicDTRegressor

LOGIC_GRID = [
    {'modelo__leaf_model': ['mean'], 'modelo__max_terms': [3, 5],
     'modelo__max_depth': [2, 3]},
    {'modelo__leaf_model': ['ridge'], 'modelo__max_terms': [3, 5],
     'modelo__max_depth': [2], 'modelo__ridge_alpha': [1., 10.]},
]
CHECKPOINT = 'tabpfn-v2.5-regressor-v2.5_default.ckpt'
MODEL_DIR = BOOK / 'modelos_preentrenados/tabpfn_25'


def partitions():
    train, test, audit = load_partitions()
    source = source_hashes()
    previous = json.loads((OUTPUT / 'modelos_lineales.json').read_text(encoding='utf-8'))
    if previous['source_sha256'] != source:
        raise ValueError('La fuente o protocolo cambió respecto al tablero; revisar antes de comparar.')
    # Comprobar TODAS las variables y su orden, además de objetivo y periodo.
    for frame, name in [(train, 'train'), (test, 'test')]:
        saved = pd.read_csv(OUTPUT / f'{name}.csv.gz')
        pd.testing.assert_frame_equal(frame[FEATURES+[TARGET, PERIOD]],
                                     saved[FEATURES+[TARGET, PERIOD]],
                                     check_dtype=False, check_exact=False)
    saved_folds = pd.read_csv(OUTPUT / 'train.csv.gz')['fold'].to_numpy()
    folds = grouped_splits(train)
    reproduced = np.zeros(len(train), dtype=int)
    for k, (_, val) in enumerate(folds, 1):
        reproduced[val] = k
    np.testing.assert_array_equal(reproduced, saved_folds)
    return train, test, folds, audit


def logic_pipeline():
    return Pipeline([('preprocesamiento', clone(make_pipeline().named_steps['preprocesamiento'])),
                     ('modelo', LogicDTRegressor(n_numeric=len(NUMERIC)))])


def prepare_tabpfn_environment():
    # Telemetría desactivada antes de importar la librería. Inferencia local.
    os.environ['TABPFN_DISABLE_TELEMETRY'] = '1'
    os.environ['DO_NOT_TRACK'] = '1'
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    os.environ['TABPFN_NO_BROWSER'] = '1'
    os.environ['TABPFN_ALLOW_CPU_LARGE_DATASET'] = 'true'
    os.environ['TABPFN_MODEL_CACHE_DIR'] = str(MODEL_DIR)


def tabpfn_pipeline():
    prepare_tabpfn_environment()
    import torch
    from tabpfn import TabPFNRegressor
    torch.set_num_threads(4)
    path = MODEL_DIR / CHECKPOINT
    if not path.is_file():
        raise FileNotFoundError(f'Faltan los pesos oficiales 2.5: {path}. Ejecuta descargar_tabpfn25.py.')
    manifest = json.loads((MODEL_DIR / 'procedencia.json').read_text(encoding='utf-8'))
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if manifest['filename'] != CHECKPOINT or manifest['sha256'] != actual:
        raise ValueError('El checkpoint no coincide con el manifiesto oficial descargado.')
    # model_path explícito evita sustituir 2.5 por la versión predeterminada del SDK.
    estimator = TabPFNRegressor(model_path=str(path), device='cpu', n_estimators=4,
                               random_state=42, n_preprocessing_jobs=1, fit_mode='low_memory',
                               memory_saving_mode=True,
                               ignore_pretraining_limits=True,
                               categorical_features_indices=[])
    return Pipeline([('preprocesamiento', clone(make_pipeline().named_steps['preprocesamiento'])),
                     ('modelo', estimator)])


def provenance(key):
    result = source_hashes()
    for name in ['evaluacion_nuevos_e3.py', 'logicdt_propio.py',
                 'resultados/e3/train.csv.gz', 'resultados/e3/test.csv.gz',
                 'resultados/e3/clasicos/comparacion.json']:
        result[name] = hashlib.sha256((BOOK / name).read_bytes()).hexdigest()
    result['experiment'] = key
    if key == 'tabpfn_25':
        result['checkpoint'] = json.loads((MODEL_DIR / 'procedencia.json').read_text(encoding='utf-8'))
    return result


def run_experiment(key, force=False):
    if key not in ('logicdt', 'tabpfn_25'):
        raise ValueError(key)
    train, test, folds, audit = partitions()
    folder = OUTPUT / key
    folder.mkdir(parents=True, exist_ok=True)
    signature = provenance(key)
    report_path = folder / 'reporte.json'
    if report_path.exists() and not force:
        cached = json.loads(report_path.read_text(encoding='utf-8'))
        if cached['provenance'] == signature:
            print(f'{key}: resultados completos verificados; force=True para recalcular.', flush=True)
            return cached
    name = 'logicDT propio (adaptado)' if key == 'logicdt' else 'TabPFN 2.5 (4 estimadores, CPU)'
    rows, audits, oof = [], [], np.full(len(train), np.nan)

    def fit(frame):
        if key == 'logicdt':
            search = GridSearchCV(logic_pipeline(), LOGIC_GRID, cv=grouped_splits(frame),
                                  scoring='neg_root_mean_squared_error', n_jobs=1,
                                  error_score='raise', refit=True)
            with threadpool_limits(limits=1):
                search.fit(frame[FEATURES], frame[TARGET])
            return search.best_estimator_, search.best_params_, pd.DataFrame(search.cv_results_)
        model = tabpfn_pipeline()
        model.fit(frame[FEATURES], frame[TARGET])
        return model, {'n_estimators': 4, 'device': 'cpu', 'model_path': CHECKPOINT,
                       'fit_mode': 'low_memory', 'random_state': 42}, None

    for k, (fi, va) in enumerate(folds, 1):
        start = time.perf_counter()
        print(f'{key}: fold externo {k}/5, fit={len(fi)}, validación={len(va)}', flush=True)
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', message='Found unknown categories')
            model, params, grid = fit(train.iloc[fi])
            oof[va] = model.predict(train.iloc[va][FEATURES])
        rows.append({'Modelo': name, 'Fold': k, **metrics(train.iloc[va][TARGET], oof[va])})
        audits.append({'fold': k, 'fit_rows': len(fi), 'validation_rows': len(va),
                       'shared_students': len(set(train.iloc[fi][GROUP]) & set(train.iloc[va][GROUP])),
                       'best_params': params, 'seconds': time.perf_counter()-start})
        if grid is not None:
            grid.to_csv(folder / f'grid_fold_{k}.csv', index=False)
        write_json(folder / 'progreso.json', {'folds': rows, 'audit': audits, 'provenance': signature})
        print(f'{key}: fold {k} RMSE={rows[-1]["RMSE"]:.6f}, {audits[-1]["seconds"]:.1f}s', flush=True)
        del model
        gc.collect()
    if not np.isfinite(oof).all():
        raise ValueError('Predicciones OOF incompletas')
    print(f'{key}: ajuste final exclusivamente en train; luego evaluación test 202530', flush=True)
    model, params, grid = fit(train)
    # El test se consulta para predicciones solo después de fijar el modelo.
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='Found unknown categories')
        pred = model.predict(test[FEATURES])
    score = metrics(test[TARGET], pred)
    fold_frame = pd.DataFrame(rows)
    fold_frame.to_csv(folder / 'fold_metrics.csv', index=False)
    if grid is not None:
        grid.to_csv(folder / 'grid_final.csv', index=False)
        joblib.dump(model, folder / 'modelo.joblib')
        prep, estimator = model.named_steps['preprocesamiento'], model.named_steps['modelo']
        write_json(folder / 'terminos.json', estimator.describe_terms(prep.get_feature_names_out()))
        pd.DataFrame(estimator.search_history_).to_csv(folder / 'recocido_final.csv', index=False)
    for label, frame, predictions in [('train', train, oof), ('test', test, pred)]:
        export = frame[[TARGET, PERIOD]].copy()
        export['prediccion'] = predictions
        export['residuo'] = export[TARGET] - predictions
        if label == 'train':
            export['fold'] = pd.read_csv(OUTPUT / 'train.csv.gz')['fold']
        export.to_csv(folder / f'{label}_predictions.csv.gz', index=False, compression='gzip')
    rng = np.random.default_rng(42)
    positions = [np.flatnonzero(test[GROUP].eq(g)) for g in test[GROUP].unique()]
    svm = pd.read_csv(OUTPUT / 'test.csv.gz')['svm'].to_numpy()
    boot, diffs = [], []
    for _ in range(1000):
        ix = np.concatenate([positions[j] for j in rng.integers(len(positions), size=len(positions))])
        a = metrics(test.iloc[ix][TARGET], pred[ix])
        b = metrics(test.iloc[ix][TARGET], svm[ix])
        boot.append(a)
        diffs.append({m: a[m]-b[m] for m in a if a[m] is not None and b[m] is not None})
    intervals, paired = [], []
    for m in score:
        lo, hi = np.quantile([x[m] for x in boot if x[m] is not None], [.025, .975])
        dlo, dhi = np.quantile([x[m] for x in diffs if m in x], [.025, .975])
        intervals.append({'metrica': m, 'estimacion': score[m], 'IC_2.5%': lo, 'IC_97.5%': hi})
        paired.append({'metrica': m, 'nuevo_menos_SVM': score[m]-metrics(test[TARGET], svm)[m],
                       'IC_2.5%': dlo, 'IC_97.5%': dhi})
    baseline = json.loads((OUTPUT / 'clasicos/comparacion.json').read_text(encoding='utf-8'))['test']
    summary = [{'metrica': m, 'media_cv': fold_frame[m].mean(),
                'sd_cv': fold_frame[m].std(ddof=0), 'OOF_agrupado': metrics(train[TARGET], oof)[m]}
               for m in score]
    report = {'model': name, 'partition': audit, 'provenance': signature,
              'features': FEATURES, 'target': TARGET, 'test': score,
              'cv': summary, 'fold_audit': audits, 'best_params': params,
              'bootstrap_test': intervals, 'paired_vs_svm': paired,
              'comparison_test': baseline + [{'Modelo': name, **score}],
              'method': ('GroupKFold externo 5 e interno 5, selección RMSE' if key == 'logicdt'
                         else 'GroupKFold externo 5; configuración fijada antes de evaluar, sin búsqueda'),
              'versions': {p: importlib.metadata.version(p) for p in
                           ['numpy', 'pandas', 'scikit-learn', 'scipy'] +
                           (['tabpfn', 'torch'] if key == 'tabpfn_25' else [])}}
    write_json(report_path, report)
    del model
    gc.collect()
    return report


def display_results(report):
    """Una escala independiente por métrica evita mezclar unidades y magnitudes."""
    from IPython.display import display
    import matplotlib.pyplot as plt
    display(pd.DataFrame(report['cv']).round(5))
    display(pd.DataFrame(report['bootstrap_test']).round(5))
    table = pd.DataFrame(report['comparison_test'])
    display(table.round(5))
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), constrained_layout=True)
    for ax, metric in zip(axes.flat, ['RMSE', 'MAE', 'MAPE (%)', 'R²']):
        ordered = table.sort_values(metric, ascending=metric != 'R²')
        colors = ['#cc5500' if n == report['model'] else '#326d9c' for n in ordered.Modelo]
        bars = ax.barh(ordered.Modelo, ordered[metric], color=colors)
        ax.bar_label(bars, fmt='%.3f', padding=3, fontsize=8)
        ax.invert_yaxis()
        ax.set_title(f'{metric} — {"mayor" if metric == "R²" else "menor"} es mejor')
        ax.margins(x=.2)
        ax.grid(axis='x', alpha=.2)
    plt.show()
    test = pd.read_csv(OUTPUT / ('logicdt' if report['model'].startswith('logicDT') else 'tabpfn_25') / 'test_predictions.csv.gz')
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), constrained_layout=True)
    axes[0].scatter(test[TARGET], test.prediccion, alpha=.6)
    limits = [min(test[TARGET].min(), test.prediccion.min()), max(test[TARGET].max(), test.prediccion.max())]
    axes[0].plot(limits, limits, '--', color='gray')
    axes[0].set(xlabel='Nota real', ylabel='Predicción', title='Test temporal: real vs. predicción')
    axes[1].scatter(test.prediccion, test.residuo, alpha=.6)
    axes[1].axhline(0, color='gray', linestyle='--')
    axes[1].set(xlabel='Predicción', ylabel='Real − predicción', title='Residuos en test')
    plt.show()


if __name__ == '__main__':
    import sys
    run_experiment(sys.argv[1], force='--force' in sys.argv)

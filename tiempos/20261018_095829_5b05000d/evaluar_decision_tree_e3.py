"""Añade únicamente CART regresor a los clásicos E3, conservando sus resultados.

Ejecutar con el venv compartido desde la raíz. No consulta test para selección.
"""
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import GridSearchCV, ParameterGrid
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeRegressor

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'Dash'))
from model_timing import TimingRun, file_hash
from entregable3 import (BOOK, OUTPUT as BASE, FEATURES, NUMERIC, CATEGORICAL,
                        GROUP, TARGET, load_partitions, grouped_splits, metrics, source_hashes, write_json)
from modelos_clasicos import OUTPUT, bootstrap_comparison, LABELS

KEY = 'decision_tree'
NAME = 'Decision Tree'
GRID = {'modelo__max_depth': [2, 3, 4, 6, 8, None],
        'modelo__min_samples_leaf': [2, 5, 10, 20],
        'modelo__ccp_alpha': [0.0, 0.001, 0.01]}
PREPARATION = ('CART de regresión: cortes binarios que reducen error cuadrático; cada hoja predice la media del fit. '
               'Mediana numérica; moda y one-hot categórico completo (desconocidas ignoradas). '
               'Sin escalado ni log1p; imputación y vocabulario aprendidos dentro de cada fit. '
               'Profundidad, mínimo por hoja y poda por complejidad se seleccionan solo en train. Semilla 42.')


def make_tree():
    prep = ColumnTransformer([
        ('num', SimpleImputer(strategy='median'), NUMERIC),
        ('cat', Pipeline([('imputer', SimpleImputer(strategy='most_frequent')),
                          ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))]), CATEGORICAL)])
    return Pipeline([('preprocesamiento', prep),
                     ('modelo', DecisionTreeRegressor(criterion='squared_error', random_state=42))])


def tune(frame, label, run):
    splits = grouped_splits(frame)
    for fit, val in splits:
        assert not set(frame.iloc[fit][GROUP]) & set(frame.iloc[val][GROUP])
    search = GridSearchCV(make_tree(), GRID, scoring='neg_root_mean_squared_error',
                          cv=splits, n_jobs=4, refit=False, error_score='raise')
    with run.measure('Búsqueda', label, len(frame), candidates=len(list(ParameterGrid(GRID))),
                     inner_folds=5, expected_fits=360, n_jobs=4, refit=False):
        with joblib.parallel_backend('loky', inner_max_num_threads=1):
            search.fit(frame[FEATURES], frame[TARGET])
    estimator = clone(make_tree()).set_params(**search.best_params_)
    with run.measure('Entrenamiento/refit', label, len(frame), best_params=search.best_params_, n_jobs=1):
        estimator.fit(frame[FEATURES], frame[TARGET])
    pd.DataFrame(search.cv_results_).to_csv(OUTPUT / f'grid_decision_tree_{label}.csv', index=False)
    return search, estimator


def predict(model, frame, label, run):
    with run.measure('Inferencia', label, len(frame), repetitions=1, warmup=0):
        return model.predict(frame[FEATURES])


def run():
    train, test, audit = load_partitions()
    report = json.loads((OUTPUT / 'comparacion.json').read_text(encoding='utf-8'))
    for source, digest in report['source_sha256'].items():
        assert file_hash(BOOK / source) == digest, source
    cached_train, cached_test = [pd.read_csv(BASE / f'{part}.csv.gz') for part in ['train', 'test']]
    for frame, cached in [(train, cached_train), (test, cached_test)]:
        pd.testing.assert_frame_equal(frame[FEATURES+[TARGET]].reset_index(drop=True),
                                      cached[FEATURES+[TARGET]], check_dtype=False, rtol=1e-12)
    assert not set(train[GROUP]) & set(test[GROUP])
    timing = TimingRun(NAME + ' · nuevo modelo E3', {
        'script': 'Precalculo/evaluar_decision_tree_e3.py', 'script_sha256': file_hash(__file__),
        'timing_sha256': file_hash(Path(__file__).parent.parent / 'Dash/model_timing.py'),
        'command': 'Precalculo/venv/Scripts/python.exe Precalculo/evaluar_decision_tree_e3.py',
        'source_sha256': source_hashes(), 'seed': 42, 'grid': GRID, 'candidates': 72,
        'n_jobs_search': 4, 'inner_max_num_threads': 1, 'fit_threads': 1,
        'train_rows': len(train), 'test_rows': len(test), 'features': FEATURES,
        'train_students': train[GROUP].nunique(), 'test_students': test[GROUP].nunique(),
        'cv': '5 externos x 5 internos GroupKFold; test 202530 purgado',
        'expected_internal_fits': 2160, 'expected_refits': 6})
    status = 'fallida'
    try:
        oof = np.full(len(train), np.nan)
        rows, folds_audit = [], []
        for fold, (fit, val) in enumerate(grouped_splits(train), 1):
            assert (cached_train.iloc[val]['fold'] == fold).all()
            fitting, validation = train.iloc[fit], train.iloc[val]
            assert not set(fitting[GROUP]) & set(validation[GROUP])
            search, estimator = tune(fitting, f'fold_{fold}', timing)
            pred = predict(estimator, validation, f'OOF fold {fold}', timing)
            oof[val] = pred
            train_pred = predict(estimator, fitting, f'train fold {fold}', timing)
            rows.append({'Modelo': NAME, 'Fold': fold, **metrics(validation[TARGET], pred),
                         'RMSE train': metrics(fitting[TARGET], train_pred)['RMSE']})
            folds_audit.append({'fold': fold, 'fit_rows': len(fit), 'validation_rows': len(val),
                                'fit_students': fitting[GROUP].nunique(), 'validation_students': validation[GROUP].nunique(),
                                'shared_students': 0, 'inner_folds': 5, 'best_params': search.best_params_})
            print(f'Externo {fold}/5: {rows[-1]["RMSE"]:.6f}; {search.best_params_}', flush=True)
        assert np.isfinite(oof).all()
        final, estimator = tune(train, 'final', timing)
        # Evidencia persistida antes de abrir la evaluación temporal.
        write_json(OUTPUT / 'seleccion_decision_tree_antes_test.json', {
            'run_id': timing.run_id, 'best_params': final.best_params_,
            'selection_rmse': -final.best_score_, 'grid': GRID, 'fold_audit': folds_audit,
            'source_sha256': source_hashes()})
        path = OUTPUT / f'{KEY}.joblib'
        joblib.dump(estimator, path)
        pred_test = predict(estimator, test, 'test temporal', timing)
        restored = predict(joblib.load(path), test, 'test verificación serialización', timing)
        np.testing.assert_array_equal(restored, pred_test)
        train_pred = predict(estimator, train, 'train final', timing)
        train_preds = pd.read_csv(OUTPUT / 'train_predictions.csv.gz')
        test_preds = pd.read_csv(OUTPUT / 'test_predictions.csv.gz')
        np.testing.assert_array_equal(train_preds['fold'], cached_train['fold'])
        train_preds[KEY], test_preds[KEY] = oof, pred_test
        folds = pd.read_csv(OUTPUT / 'fold_metrics.csv')
        folds = pd.concat([folds.loc[~folds.Modelo.eq(NAME)], pd.DataFrame(rows)], ignore_index=True)
        spec = {'name': NAME, 'grid': GRID, 'combinations': 72, 'preparation': PREPARATION,
                'best_params': final.best_params_, 'selection_rmse': -final.best_score_, 'fold_audit': folds_audit,
                'train_metrics': metrics(train[TARGET], train_pred), 'test_metrics': metrics(test[TARGET], pred_test),
                'outside_test': int(((pred_test < .5) | (pred_test > 5)).sum()),
                'unknown_test_categories': {c: int((test[c].notna() & ~test[c].isin(train[c].dropna())).sum()) for c in CATEGORICAL},
                'model_sha256': file_hash(path), 'timing_run_id': timing.run_id}
        report['models'][KEY] = spec
        LABELS[KEY] = NAME
        bootstrap, differences = bootstrap_comparison(test, {c: test_preds[c].to_numpy() for c in test_preds})
        report.update(bootstrap=bootstrap, paired_differences=differences)
        report['test'] = [r for r in report['test'] if r['Modelo'] != NAME] + [{'Modelo': NAME, **spec['test_metrics']}]
        means = folds.groupby('Modelo').RMSE.mean()
        report['selected_by_external_cv'] = min((v['name'] for v in report['models'].values()), key=means.get)
        report['decision_tree_provenance'] = {'script_sha256': file_hash(__file__),
            'source_sha256': source_hashes(), 'timing_run_id': timing.run_id}
        for part, frame in [('train', train_preds), ('test', test_preds)]:
            frame.to_csv(OUTPUT / f'{part}_predictions.csv.gz', index=False)
        folds.to_csv(OUTPUT / 'fold_metrics.csv', index=False)
        grid = pd.DataFrame(final.cv_results_)
        grid = grid[[c for c in grid if c.startswith('param_')] + ['mean_test_score', 'std_test_score', 'rank_test_score']]
        grid.assign(RMSE=-grid.mean_test_score).to_csv(OUTPUT / f'grid_{KEY}.csv', index=False)
        write_json(OUTPUT / 'comparacion.json', report)
        status = 'completa'
        print(json.dumps(spec, ensure_ascii=False), flush=True)
    finally:
        timing.finish(status)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    run()

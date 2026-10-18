"""Comparación E3: cinco regresores, CV anidada por estudiante y test temporal.

Reutiliza carga, reglas y particiones de entregable3, sin reescribir su SVM.
"""
import hashlib
import json
import sys
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
import xgboost
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Lasso, Ridge
from sklearn.model_selection import GridSearchCV, ParameterGrid
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder
from xgboost import XGBRegressor

from entregable3 import (BOOK, OUTPUT as BASE, CATEGORICAL, FEATURES, GROUP, NUMERIC,
                        TARGET, grouped_splits, load_partitions, make_pipeline,
                        metrics, source_hashes, write_json)
from preprocesamiento_clasicos import NativeCategories

OUTPUT = BASE / 'clasicos'
GRIDS = {
    'knn': {'modelo__n_neighbors': [5, 11, 21, 31, 41, 61, 81, 101], 'modelo__weights': ['uniform', 'distance'], 'modelo__p': [1, 2]},
    'ridge': {'modelo__alpha': [.01, .1, 1, 3, 10, 30, 100, 1000]},
    'lasso': {'modelo__alpha': [.0001, .0003, .0005, .001, .002, .003, .01, .03, .1]},
    'forest': {'modelo__n_estimators': [150, 300, 500], 'modelo__max_depth': [4, 6, None], 'modelo__min_samples_leaf': [2, 5, 10]},
    'xgboost': {'modelo__n_estimators': [150, 300, 500], 'modelo__max_depth': [1, 2, 4], 'modelo__learning_rate': [.01, .03, .1]},
}
LABELS = {'knn': 'KNN', 'ridge': 'Ridge', 'lasso': 'Lasso', 'forest': 'Random Forest', 'xgboost': 'XGBoost'}
PREPARATION = {
    'knn': 'Mediana, log1p en tiempos, StandardScaler; moda y one-hot con referencia. Distancias sobre variables transformadas.',
    'ridge': 'Mismo preprocesamiento del SVM: mediana, log1p en tiempos, escalado; moda y one-hot. Penalización L2.',
    'lasso': 'Mismo preprocesamiento del SVM: mediana, log1p en tiempos, escalado; moda y one-hot. Penalización L1.',
    'forest': 'Mediana numérica, moda categórica y OrdinalEncoder (desconocidas=-1). Sin one-hot, log1p ni escalado. Los códigos imponen un orden artificial en categorías nominales.',
    'xgboost': 'Mediana numérica y moda categórica; categorías nativas aprendidas en cada fit. Sin one-hot externo ni escalado; categorías nuevas pasan a faltantes. tree_method=hist, enable_categorical=True.',
}


def provenance():
    paths = ['modelos_clasicos.py', 'preprocesamiento_clasicos.py',
             'resultados/e3/modelos_lineales.json', 'resultados/e3/train.csv.gz',
             'resultados/e3/test.csv.gz', 'resultados/e3/fold_metrics.csv']
    return {**source_hashes(), **{p: hashlib.sha256((BOOK / p).read_bytes()).hexdigest() for p in paths}}


def classic_pipeline(key):
    if key in ['knn', 'ridge', 'lasso']:
        estimator = {'knn': KNeighborsRegressor(n_jobs=1), 'ridge': Ridge(),
                     'lasso': Lasso(max_iter=100000, tol=1e-4, random_state=42)}[key]
        prep = clone(make_pipeline().named_steps['preprocesamiento'])
    elif key == 'forest':
        prep = ColumnTransformer([
            ('num', SimpleImputer(strategy='median'), NUMERIC),
            ('cat', Pipeline([('imputer', SimpleImputer(strategy='most_frequent')),
                              ('ordinal', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1))]), CATEGORICAL)])
        estimator = RandomForestRegressor(random_state=42, n_jobs=1, max_features=.7)
    elif key == 'xgboost':
        imputation = ColumnTransformer([
            ('num', SimpleImputer(strategy='median'), NUMERIC),
            ('cat', SimpleImputer(strategy='most_frequent'), CATEGORICAL)]).set_output(transform='pandas')
        prep = Pipeline([('imputation', imputation), ('categories', NativeCategories())])
        estimator = XGBRegressor(objective='reg:squarederror', tree_method='hist', enable_categorical=True,
                                 max_cat_to_onehot=1, min_child_weight=3, subsample=.8,
                                 colsample_bytree=.8, reg_lambda=3, random_state=42, n_jobs=1)
    else:
        raise KeyError(key)
    return Pipeline([('preprocesamiento', prep), ('modelo', estimator)])


def tune(key, frame):
    search = GridSearchCV(classic_pipeline(key), GRIDS[key], cv=grouped_splits(frame),
                          scoring='neg_root_mean_squared_error', n_jobs=4, refit=True, error_score='raise')
    with warnings.catch_warnings():
        warnings.simplefilter('error', ConvergenceWarning)
        warnings.filterwarnings('ignore', message='Found unknown categories', category=UserWarning)
        with joblib.parallel_backend('loky', inner_max_num_threads=1):
            search.fit(frame[FEATURES], frame[TARGET])
    return search


def bootstrap_comparison(test, predictions):
    positions = [np.flatnonzero(test[GROUP].eq(g).to_numpy()) for g in test[GROUP].unique()]
    rng = np.random.default_rng(42)
    draws = {key: [] for key in predictions}
    y = test[TARGET].to_numpy()
    for _ in range(1000):
        ix = np.concatenate([positions[i] for i in rng.integers(0, len(positions), len(positions))])
        truth = y[ix]
        variance = np.sum((truth-truth.mean())**2)
        for key, pred in predictions.items():
            err = truth-pred[ix]
            draws[key].append({'RMSE': float(np.sqrt(np.mean(err**2))), 'MAE': float(np.mean(abs(err))),
                               'R²': float(1-np.sum(err**2)/variance) if variance else np.nan})
    rows, differences = [], []
    svm_rmse = np.array([s['RMSE'] for s in draws['svm']])
    for key, samples in draws.items():
        point = metrics(y, predictions[key])
        for metric in ['RMSE', 'MAE', 'R²']:
            values = [s[metric] for s in samples]
            low, high = np.nanquantile(values, [.025, .975])
            rows.append({'Modelo': LABELS.get(key, 'SVM lineal' if key == 'svm' else 'Dummy media'),
                         'Métrica': metric, 'Estimación': point[metric], 'IC 2.5%': low, 'IC 97.5%': high})
        if key in LABELS:
            delta = np.array([s['RMSE'] for s in samples])-svm_rmse
            low, high = np.quantile(delta, [.025, .975])
            differences.append({'Modelo': LABELS[key], 'Δ RMSE vs SVM': point['RMSE']-metrics(y, predictions['svm'])['RMSE'],
                                'IC 2.5%': low, 'IC 97.5%': high})
    return rows, differences


def run():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    train, test, audit = load_partitions()
    baseline = json.loads((BASE / 'modelos_lineales.json').read_text(encoding='utf-8'))
    assert baseline['source_sha256'] == source_hashes(), 'Revisar procedencia del SVM base.'
    cached_train, cached_test = pd.read_csv(BASE / 'train.csv.gz'), pd.read_csv(BASE / 'test.csv.gz')
    for source, cached in [(train, cached_train), (test, cached_test)]:
        pd.testing.assert_frame_equal(source[FEATURES+[TARGET]].reset_index(drop=True),
                                      cached[FEATURES+[TARGET]], check_dtype=False, rtol=1e-12)
    splits = grouped_splits(train)
    assignments = np.empty(len(train), dtype=int)
    for fold, (_, val) in enumerate(splits, 1): assignments[val] = fold
    np.testing.assert_array_equal(assignments, cached_train['fold'])
    train_preds, test_preds = cached_train[['fold', 'svm', 'dummy']].copy(), cached_test[['svm', 'dummy']].copy()
    fold_rows = pd.read_csv(BASE / 'fold_metrics.csv').to_dict('records')
    test_rows = [{'Modelo': name, **metrics(test[TARGET], cached_test[key])}
                 for key, name in [('svm', 'SVM lineal'), ('dummy', 'Dummy media')]]
    reports = {}
    before = provenance()
    for key, name in LABELS.items():
        started = time.monotonic()
        oof = np.full(len(train), np.nan)
        audit_folds = []
        print(f'{name}: {len(list(ParameterGrid(GRIDS[key])))} combinaciones; inicio', flush=True)
        for fold, (fit, val) in enumerate(splits, 1):
            fitting, validation = train.iloc[fit], train.iloc[val]
            search = tune(key, fitting)
            pred = search.predict(validation[FEATURES])
            oof[val] = pred
            train_score = metrics(fitting[TARGET], search.predict(fitting[FEATURES]))
            fold_rows.append({'Modelo': name, 'Fold': fold, **metrics(validation[TARGET], pred),
                              'RMSE train': train_score['RMSE']})
            audit_folds.append({'fold': fold, 'fit_rows': len(fit), 'validation_rows': len(val),
                                'fit_students': fitting[GROUP].nunique(), 'validation_students': validation[GROUP].nunique(),
                                'shared_students': 0, 'inner_folds': 5, 'best_params': search.best_params_})
            print(f'{name}: externo {fold}/5, {search.best_params_}', flush=True)
        assert np.isfinite(oof).all()
        final = tune(key, train)
        path = OUTPUT / f'{key}.joblib'
        joblib.dump(final.best_estimator_, path)
        # JSON/UBJSON conserva la información categórica del booster.
        if key == 'xgboost': final.best_estimator_.named_steps['modelo'].save_model(OUTPUT / 'xgboost.ubj')
        # pandas serializa float32 con menos dígitos; conservar todos al exportar.
        pred_test = np.asarray(final.predict(test[FEATURES]), dtype=np.float64)
        np.testing.assert_allclose(joblib.load(path).predict(test[FEATURES]), pred_test, atol=0, rtol=0)
        train_preds[key], test_preds[key] = oof, pred_test
        test_rows.append({'Modelo': name, **metrics(test[TARGET], pred_test)})
        grid = pd.DataFrame(final.cv_results_)
        columns = [c for c in grid if c.startswith('param_')] + ['mean_test_score', 'std_test_score', 'rank_test_score']
        grid = grid[columns].assign(RMSE=lambda f: -f['mean_test_score'])
        grid.to_csv(OUTPUT / f'grid_{key}.csv', index=False)
        train_metrics = metrics(train[TARGET], final.predict(train[FEATURES]))
        reports[key] = {'name': name, 'grid': GRIDS[key], 'combinations': len(grid),
                        'preparation': PREPARATION[key], 'best_params': final.best_params_,
                        'selection_rmse': -final.best_score_, 'fold_audit': audit_folds,
                        'train_metrics': train_metrics, 'test_metrics': metrics(test[TARGET], pred_test),
                        'outside_test': int(((pred_test < .5) | (pred_test > 5)).sum()),
                        'unknown_test_categories': {c: int((test[c].notna() & ~test[c].isin(train[c].dropna())).sum()) for c in CATEGORICAL},
                        'model_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'elapsed_seconds': time.monotonic()-started}
        print(f'{name}: final {final.best_params_}; test {metrics(test[TARGET], pred_test)}', flush=True)
    train_preds.to_csv(OUTPUT / 'train_predictions.csv.gz', index=False, compression='gzip')
    test_preds.to_csv(OUTPUT / 'test_predictions.csv.gz', index=False, compression='gzip')
    folds = pd.DataFrame(fold_rows)
    folds.to_csv(OUTPUT / 'fold_metrics.csv', index=False)
    bootstrap, differences = bootstrap_comparison(test, {c: test_preds[c].to_numpy() for c in test_preds})
    external = folds.groupby('Modelo')['RMSE'].mean()
    selected = min(LABELS.values(), key=lambda name: external[name])
    assert provenance() == before, 'Las fuentes cambiaron durante el ajuste.'
    report = {'source_sha256': before, 'partition': audit, 'models': reports,
              'test': test_rows, 'bootstrap': bootstrap, 'paired_differences': differences,
              'selected_by_external_cv': selected, 'selection_scope': 'Comparación exploratoria de familias por CV externa; test no selecciona modelos.',
              'versions': {'sklearn': sklearn.__version__, 'xgboost': xgboost.__version__},
              'method': 'Mismos cinco folds externos del SVM; cinco internos por estudiante en cada búsqueda; test 202530 purgado.'}
    write_json(OUTPUT / 'comparacion.json', report)
    print(json.dumps({'test': test_rows, 'best_external_cv': selected}, ensure_ascii=False), flush=True)
    return report


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    run()

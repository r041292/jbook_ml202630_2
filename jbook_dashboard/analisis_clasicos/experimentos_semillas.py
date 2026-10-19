"""Sensibilidad a semillas de los modelos clásicos y de sus búsquedas estocásticas.

Material complementario del capítulo «Modelos clásicos» del Book. No modifica
resultados canónicos ni la ejecución activa: escribe solo en
``jbook_dashboard/analisis_clasicos/salidas/semillas``. Test nunca selecciona.

A. Semilla del estimador. Para cada fold externo se reutilizan los
   hiperparámetros que ese fold eligió en la ejecución activa y solo cambia
   ``random_state``. Se reajusta el pipeline en el entrenamiento externo y se
   predice su validación (OOF). Mismo procedimiento en todo train para test.
B. Semilla de la búsqueda. Random, TPE, DEAP y Successive Halving se repiten
   en la búsqueda final sobre todo train con semillas nuevas; Grid es
   determinista y no se repite. Se registra el RMSE interno elegido por método.

Tiempos de pared con perf_counter mediante ``Dash/model_timing.TimingRun``.
"""
import json
import sys
import time
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path[:0] = [str(ROOT / 'Precalculo'), str(ROOT / 'Dash')]

import joblib
import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits

from entregable3 import FEATURES, TARGET, GROUP, load_partitions, grouped_splits, metrics
from busquedas_hiperparametros_e3 import Search, pipeline_for, METHODS, BUDGET
from model_timing import TimingRun, file_hash

RUN = ROOT / 'Precalculo/resultados/e3/busquedas/20261018_102325_af643f83'
OUTPUT = HERE / 'salidas' / 'semillas'
SEEDS = list(range(10))
SEARCH_SEEDS = [1, 2, 3]
STOCHASTIC = {'svm': 'SVM lineal', 'forest': 'Random Forest', 'xgboost': 'XGBoost',
              'decision_tree': 'Decision Tree'}
ALL = {'svm': 'SVM lineal', 'knn': 'KNN', 'ridge': 'Ridge', 'lasso': 'Lasso',
       'forest': 'Random Forest', 'xgboost': 'XGBoost', 'decision_tree': 'Decision Tree'}


def fit_predict(key, params, seed, fitting, targets):
    model = pipeline_for(key).set_params(**params, modelo__random_state=seed)
    with threadpool_limits(limits=1), warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='Found unknown categories', category=UserWarning)
        warnings.simplefilter('ignore', ConvergenceWarning)
        clock = time.perf_counter()
        model.fit(fitting[FEATURES], fitting[TARGET])
        fit_seconds = time.perf_counter()-clock
        clock = time.perf_counter()
        preds = [np.asarray(model.predict(frame[FEATURES]), dtype=float) for frame in targets]
        predict_seconds = time.perf_counter()-clock
    return preds, fit_seconds, predict_seconds


def estimator_seeds(train, test, splits, timing):
    rows = []
    for key, name in STOCHASTIC.items():
        audit = json.loads((RUN / f'parcial_{key}.json').read_text(encoding='utf-8'))['fold_audit']
        final = json.loads((RUN / 'seleccion_antes_test.json').read_text(encoding='utf-8'))['models'][key]['params']
        tasks = [(seed, fold) for seed in [42, *SEEDS] for fold in range(1, 7)]

        def task(seed, fold):
            if fold <= 5:
                fit, val = splits[fold-1]
                params = audit[fold-1]['best_params']
                (pred,), fs, ps = fit_predict(key, params, seed, train.iloc[fit], [train.iloc[val]])
                truth = train.iloc[val][TARGET]
                return {'Modelo': name, 'key': key, 'semilla': seed, 'Fold': fold, 'partición': 'OOF',
                        **metrics(truth, pred), 'fit_s': fs, 'predict_s': ps, 'filas_fit': len(fit), 'filas_pred': len(val)}
            (pred,), fs, ps = fit_predict(key, final, seed, train, [test])
            return {'Modelo': name, 'key': key, 'semilla': seed, 'Fold': 'final', 'partición': 'test',
                    **metrics(test[TARGET], pred), 'fit_s': fs, 'predict_s': ps, 'filas_fit': len(train), 'filas_pred': len(test)}

        with timing.measure('Entrenamiento/refit + inferencia', f'{key} / sensibilidad semilla estimador',
                            len(train), model=key, seeds=[42, *SEEDS], fits=len(tasks), n_jobs=4,
                            scope='Pared del lote paralelo: 5 refits OOF + refit final por semilla, con predict de validación y test'):
            result = joblib.Parallel(n_jobs=4)(joblib.delayed(task)(s, f) for s, f in tasks)
        rows.extend(result)
        for row in result:
            timing.record('Entrenamiento/refit', f'{key} / semilla {row["semilla"]} / {row["Fold"]}', row['fit_s'],
                          row['filas_fit'], model=key, seed=row['semilla'], included_in='lote paralelo de sensibilidad')
            timing.record('Inferencia', f'{key} / semilla {row["semilla"]} / {row["partición"]} {row["Fold"]}', row['predict_s'],
                          row['filas_pred'], model=key, seed=row['semilla'], repetitions=1, warmup=0,
                          included_in='lote paralelo de sensibilidad')
        print(f'{name}: sensibilidad de estimador completada', flush=True)
    return pd.DataFrame(rows)


def search_seeds(train, timing):
    rows = []
    for key, name in ALL.items():
        for seed in SEARCH_SEEDS:
            directory = OUTPUT / 'busquedas' / f'{key}_semilla_{seed}'
            directory.mkdir(parents=True, exist_ok=True)
            search = Search(key, train, f'final_train_semilla_{seed}', timing, directory, budget={'seed': seed})
            for method in METHODS[1:]:
                summary = search.run_method(method)
                rows.append({'Modelo': name, 'key': key, 'semilla': seed, 'Método': method,
                             'RMSE interno': summary['RMSE'], 'sd RMSE interno': summary['sd_RMSE'],
                             'best_params': json.dumps(summary['best_params']),
                             'evaluaciones': summary['evaluated_configurations'],
                             'búsqueda_s': summary['search_seconds']})
            (directory / 'evolucion_deap.json').write_text(json.dumps(search.evolution, indent=2), encoding='utf-8')
        print(f'{name}: sensibilidad de búsqueda completada', flush=True)
    return pd.DataFrame(rows)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    train, test, _ = load_partitions()
    cached = pd.read_csv(RUN / 'train.csv.gz')
    splits = grouped_splits(train)
    for fold, (_, val) in enumerate(splits, 1):
        assert cached.iloc[val]['fold'].eq(fold).all(), 'Los folds no coinciden con la ejecución activa.'
        assert not set(train.iloc[val][GROUP]) & set(train.drop(train.index[val])[GROUP])
    timing = TimingRun('Book · sensibilidad a semillas de clásicos y búsquedas', {
        'script': 'jbook_dashboard/analisis_clasicos/experimentos_semillas.py',
        'script_sha256': file_hash(__file__), 'active_run': RUN.name,
        'estimator_seeds': [42, *SEEDS], 'search_seeds': SEARCH_SEEDS, 'budget': BUDGET,
        'train_rows': len(train), 'test_rows': len(test), 'outer_folds': 5, 'inner_folds': 5,
        'device': 'CPU', 'parallelism': 'A: 4 procesos loky, 1 hilo; B: 4 procesos por fitness, métodos secuenciales',
        'scope': 'Sin selección por test. Hiperparámetros fijos de la ejecución activa en A; búsqueda final en B.'})
    status = 'fallida'
    try:
        estimators = estimator_seeds(train, test, splits, timing)
        estimators.to_csv(OUTPUT / 'semillas_estimador.csv', index=False)
        searches = search_seeds(train, timing)
        searches.to_csv(OUTPUT / 'semillas_busqueda.csv', index=False)
        (OUTPUT / 'procedencia.json').write_text(json.dumps({'timing_run_id': timing.run_id, 'active_run': RUN.name,
            'script_sha256': file_hash(__file__), 'seeds_estimator': [42, *SEEDS], 'seeds_search': SEARCH_SEEDS},
            indent=2), encoding='utf-8')
        status = 'completa'
    finally:
        timing.finish(status)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    with joblib.parallel_backend('loky', inner_max_num_threads=1):
        main()

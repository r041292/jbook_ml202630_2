"""Reevalúa SVM y seis clásicos con selección anidada entre cinco búsquedas.

Exporta una versión nueva; conserva E3 histórico. La activación es explícita
después de completar todos los modelos y sus verificaciones.
"""
import argparse
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import optuna
import deap
from sklearn.model_selection import ParameterGrid
from scipy import stats
from statsmodels.stats.diagnostic import het_breuschpagan
import statsmodels.api as sm
from threadpoolctl import threadpool_limits

from entregable3 import (BOOK, OUTPUT as BASE, FEATURES, TARGET, GROUP, CATEGORICAL,
                        load_partitions, grouped_splits, source_hashes, metrics, write_json)
from modelos_clasicos import LABELS, PREPARATION, bootstrap_comparison
from evaluar_decision_tree_e3 import PREPARATION as TREE_PREPARATION
from busquedas_hiperparametros_e3 import Search, pipeline_for, GRIDS_ALL, BUDGET, SPACES, METHODS
from model_timing import TimingRun, file_hash

NAMES = {'svm': 'SVM lineal', **LABELS, 'decision_tree': 'Decision Tree'}


def timed_predict(run, model, frame, label, key):
    with run.measure('Inferencia', f'{key} / {label}', len(frame), repetitions=1, warmup=0, model=key):
        return np.asarray(model.predict(frame[FEATURES]), dtype=float)


def timed_fit(run, key, parameters, frame, label):
    model = pipeline_for(key).set_params(**parameters)
    with run.measure('Entrenamiento/refit', f'{key} / {label}', len(frame),
                     model=key, parameters=parameters, includes_preprocessing=True, included_in_search=False):
        model.fit(frame[FEATURES], frame[TARGET])
    return model


def grid_export(search, path):
    rows = [{'params': t['params'], **{'param_'+p: v for p, v in t['params'].items()},
             'mean_test_score': -t['RMSE'], 'std_test_score': t['sd_RMSE']}
            for t in search.trials if t['method'] == METHODS[0] and t['RMSE'] is not None]
    frame = pd.DataFrame(rows)
    frame['rank_test_score'] = frame.mean_test_score.rank(ascending=False, method='min').astype(int)
    frame['RMSE'] = -frame.mean_test_score
    frame.to_csv(path, index=False)


def run():
    train, test, audit = load_partitions()
    old_report = json.loads((BASE / 'modelos_lineales.json').read_text(encoding='utf-8'))
    cached_train, cached_test = [pd.read_csv(BASE / f'{part}.csv.gz') for part in ['train', 'test']]
    for frame, cached in [(train, cached_train), (test, cached_test)]:
        pd.testing.assert_frame_equal(frame[FEATURES+[TARGET]].reset_index(drop=True), cached[FEATURES+[TARGET]], check_dtype=False, rtol=1e-12)
    assert not set(train[GROUP]) & set(test[GROUP])
    scripts = ['busquedas_hiperparametros_e3.py', 'evaluar_busquedas_e3.py', 'entregable3.py',
               'modelos_clasicos.py', 'evaluar_decision_tree_e3.py', 'preprocesamiento_clasicos.py']
    code = {p: file_hash(BOOK / p) for p in scripts}
    timing = TimingRun('SVM y seis clásicos · cinco búsquedas anidadas', {
        'scripts_sha256': code, 'source_sha256': source_hashes(), 'budget': BUDGET,
        'spaces': SPACES, 'grids': GRIDS_ALL, 'seed': 42, 'device': 'CPU',
        'train_rows': len(train), 'test_rows': len(test),
        'train_groups': train[GROUP].nunique(), 'test_groups': test[GROUP].nunique(),
        'features': FEATURES, 'outer_folds': 5, 'inner_folds': 5,
        'scope': 'Desde creación del registro, después de cargar/verificar particiones; incluye búsquedas, refits, inferencia, exportación. Sin selección por test.',
        'command': 'Precalculo/venv/Scripts/python.exe Precalculo/evaluar_busquedas_e3.py',
        'parallelism': '4 procesos loky por fitness (folds);1 hilo por proceso; métodos/ensayos/modelos secuenciales'})
    write_json(timing.directory / 'versions.json', {'optuna': optuna.__version__, 'deap': deap.__version__})
    output = BASE / 'busquedas' / timing.run_id
    output.mkdir(parents=True)
    (output / 'clasicos').mkdir()
    evidence = output / 'evidencia'
    evidence.mkdir()
    for script in scripts: shutil.copyfile(BOOK / script, evidence / script)
    write_json(output / 'protocolo.json', {'run_id': timing.run_id, 'source_sha256': source_hashes(),
               'code_sha256': code, 'methods': METHODS, 'budget': BUDGET, 'spaces': SPACES,
               'grids': GRIDS_ALL, 'partition': audit, 'test_used_for_selection': False,
               'selection': 'Menor RMSE medio de mismos5 folds internos a fidelidad1; empate<=1e-12 por orden Grid/Random/TPE/DEAP/SH.'})
    status = 'fallida'
    try:
        train_preds = cached_train[['fold', 'svm', 'dummy']].copy()
        test_preds = cached_test[['svm', 'dummy']].copy()
        rows = pd.read_csv(BASE / 'fold_metrics.csv').query("Modelo == 'Dummy media'").to_dict('records')
        specs, fitted, learning = {}, {}, []
        for key, name in NAMES.items():
            oof = np.full(len(train), np.nan)
            fold_audit, optimizations = [], []
            for fold, (fit, val) in enumerate(grouped_splits(train), 1):
                assert cached_train.iloc[val]['fold'].eq(fold).all()
                fitting, validation = train.iloc[fit], train.iloc[val]
                search = Search(key, fitting, f'externo_{fold}', timing, evidence)
                selection = search.run()
                optimizations.append(selection)
                estimator = timed_fit(timing, key, selection['best_params'], fitting, f'externo {fold}')
                pred = timed_predict(timing, estimator, validation, f'OOF fold {fold}', key)
                oof[val] = pred
                fitting_pred = timed_predict(timing, estimator, fitting, f'train fold {fold}', key)
                rows.append({'Modelo': name, 'Fold': fold, **metrics(validation[TARGET], pred),
                             'RMSE train': metrics(fitting[TARGET], fitting_pred)['RMSE']})
                fold_audit.append({'fold': fold, 'fit_rows': len(fit), 'validation_rows': len(val),
                    'fit_students': fitting[GROUP].nunique(), 'validation_students': validation[GROUP].nunique(),
                    'shared_students': 0, 'inner_folds': 5, 'best_params': selection['best_params'],
                    'selected_method': selection['selected_method']})
                if key == 'svm':
                    ids = np.random.default_rng(42).permutation(fitting[GROUP].unique())
                    for fraction in [.25, .5, .75, 1.]:
                        small = fitting.loc[fitting[GROUP].isin(ids[:max(5, int(len(ids)*fraction))])]
                        model = estimator if fraction == 1 else timed_fit(timing, key, selection['best_params'], small, f'curva fold {fold}, fracción {fraction}')
                        p_train = timed_predict(timing, model, small, f'curva train fold {fold}, fracción {fraction}', key)
                        p_val = timed_predict(timing, model, validation, f'curva validación fold {fold}, fracción {fraction}', key)
                        learning.append({'fraction': fraction, 'n': len(small),
                                         'train': metrics(small[TARGET], p_train)['RMSE'],
                                         'validation': metrics(validation[TARGET], p_val)['RMSE']})
                write_json(output / f'parcial_{key}.json', {'fold_audit': fold_audit, 'optimizations': optimizations})
            assert np.isfinite(oof).all()
            final_search = Search(key, train, 'final_train', timing, evidence)
            final = final_search.run()
            estimator = timed_fit(timing, key, final['best_params'], train, 'final train')
            fitted[key] = estimator
            artifact = output / 'model.joblib' if key == 'svm' else output / 'clasicos' / f'{key}.joblib'
            joblib.dump(estimator, artifact)
            if key == 'xgboost': estimator.named_steps['modelo'].save_model(output / 'clasicos/xgboost.ubj')
            grid_export(final_search, output / 'grid_search.csv' if key == 'svm' else output / 'clasicos' / f'grid_{key}.csv')
            train_preds[key] = oof
            p_train = timed_predict(timing, estimator, train, 'train final', key)
            specs[key] = {'name': name, 'grid': GRIDS_ALL[key],
                'combinations': len(list(ParameterGrid(GRIDS_ALL[key]))),
                'preparation': TREE_PREPARATION if key == 'decision_tree' else PREPARATION.get(key, 'Pipeline SVM canónico: mediana/log1p/escalado y moda/one-hot dentro de fit.'),
                'best_params': final['best_params'], 'selection_rmse': final['selection_rmse'],
                'fold_audit': fold_audit, 'train_metrics': metrics(train[TARGET], p_train),
                'model_sha256': file_hash(artifact), 'timing_run_id': timing.run_id,
                'optimization': {**final, 'external_selections': optimizations},
                'unknown_test_categories': {c: int((test[c].notna() & ~test[c].isin(train[c].dropna())).sum()) for c in CATEGORICAL}}
            print(f'{name}: selección final cerrada ({final["selected_method"]}); test pendiente.', flush=True)
        # Cerrar TODOS los parámetros antes de inferir por primera vez sobre test.
        write_json(output / 'seleccion_antes_test.json', {'run_id': timing.run_id,
            'models': {k: {'params': v['best_params'], 'method': v['optimization']['selected_method']} for k, v in specs.items()},
            'test_used_for_selection': False})
        for key, estimator in fitted.items():
            pred = timed_predict(timing, estimator, test, 'test temporal', key)
            test_preds[key] = pred
            artifact = output / 'model.joblib' if key == 'svm' else output / 'clasicos' / f'{key}.joblib'
            restored = timed_predict(timing, joblib.load(artifact), test, 'verificación serialización test', key)
            np.testing.assert_allclose(restored, pred, atol=0, rtol=0)
            specs[key].update(test_metrics=metrics(test[TARGET], pred), outside_test=int(((pred < .5) | (pred > 5)).sum()))
        folds = pd.DataFrame(rows)
        folds.loc[folds.Modelo.isin(['SVM lineal', 'Dummy media'])].to_csv(output / 'fold_metrics.csv', index=False)
        folds.to_csv(output / 'clasicos/fold_metrics.csv', index=False)
        for label, cached, predictions in [('train', cached_train, train_preds), ('test', cached_test, test_preds)]:
            data = cached.copy()
            data['svm'] = predictions.svm
            data.to_csv(output / f'{label}.csv.gz', index=False)
            predictions.to_csv(output / 'clasicos' / f'{label}_predictions.csv.gz', index=False)
        model = fitted['svm']
        pd.DataFrame({'Variable': model.named_steps['preprocesamiento'].get_feature_names_out(),
                      'Coeficiente': model.named_steps['modelo'].coef_}).to_csv(output / 'coefficients.csv', index=False)
        LABELS['decision_tree'] = 'Decision Tree'
        bootstrap, differences = bootstrap_comparison(test, {c: test_preds[c].to_numpy() for c in test_preds})
        for key, spec in specs.items():
            spec['optimization']['timings'] = [r for r in timing.rows if r.get('model') == key]
        classics = {'source_sha256': source_hashes(), 'run_id': timing.run_id,
                    'models': {k: v for k, v in specs.items() if k != 'svm'}, 'partition': audit,
                    'test': [{'Modelo': NAMES.get(k, 'Dummy media'), **metrics(test[TARGET], test_preds[k])} for k in test_preds],
                    'bootstrap': bootstrap, 'paired_differences': differences,
                    'selected_by_external_cv': min(LABELS.values(), key=folds.groupby('Modelo').RMSE.mean().get),
                    'selection_scope': 'Exploratoria entre familias; cada fold elige método e hiperparámetros solo en train interno.',
                    'method': '5x5 GroupKFold, selección conjunta de cinco estrategias; test202530 purgado.'}
        write_json(output / 'clasicos/comparacion.json', classics)
        report = {**old_report, **audit, 'source_sha256': source_hashes(), 'grid': GRIDS_ALL['svm'],
                  'best_params': specs['svm']['best_params'], 'selection_rmse': specs['svm']['selection_rmse'],
                  'fold_audit': specs['svm']['fold_audit'], 'optimization': specs['svm']['optimization'],
                  'run_id': timing.run_id, 'validation': 'GroupKFold anidado5x5; elección interna entre Grid, Random, TPE, DEAP y Halving'}
        svm_tests, cv, boot, residuals = [], [], [], []
        positions = [np.flatnonzero(test[GROUP].eq(g).to_numpy()) for g in test[GROUP].unique()]
        for key, name in [('svm', 'SVM lineal'), ('dummy', 'Dummy media')]:
            score = metrics(test[TARGET], test_preds[key])
            svm_tests.append({'modelo': name, 'RMSE': score['RMSE'], 'MAE': score['MAE'], 'MAPE_%': score['MAPE (%)'], 'R2': score['R²']})
            for metric, saved in [('RMSE', 'RMSE'), ('MAE', 'MAE'), ('MAPE (%)', 'MAPE'), ('R²', 'R2')]:
                values = folds.loc[folds.Modelo.eq(name), metric]
                cv.append({'modelo': name, 'metrica': saved, 'media_cv': values.mean(), 'sd_cv': values.std(ddof=0)})
            rng = np.random.default_rng(42)
            draws = []
            for _ in range(1000):
                ix = np.concatenate([positions[i] for i in rng.integers(0, len(positions), len(positions))])
                draws.append(metrics(test.iloc[ix][TARGET], test_preds[key].to_numpy()[ix]))
            for metric, saved in [('RMSE', 'RMSE'), ('MAPE (%)', 'MAPE_%'), ('R²', 'R2')]:
                low, high = np.quantile([d[metric] for d in draws], [.025, .975])
                boot.append({'modelo': name, 'metrica': saved, 'estimación': score[metric], 'IC_2.5%': low, 'IC_97.5%': high})
            residual = test[TARGET].to_numpy()-test_preds[key].to_numpy()
            variable = np.ptp(test_preds[key]) > 1e-12
            residuals.append({'modelo': name, 'media_residuo': residual.mean(), 'normaltest_p': stats.normaltest(residual).pvalue,
                'Breusch_Pagan_p': het_breuschpagan(residual, sm.add_constant(test_preds[key]))[3] if variable else None,
                'Spearman_abs_resid_vs_ajustado': stats.spearmanr(abs(residual), test_preds[key]).statistic if variable else None})
        lf = pd.DataFrame(learning)
        report.update(test=svm_tests, cv=cv, bootstrap=boot, residuals=residuals,
            learning=[{'n_entrenamiento': int(g.n.mean()), 'RMSE_train_media': g.train.mean(), 'RMSE_validacion_media': g.validation.mean()} for _, g in lf.groupby('fraction')],
            learning_method='Hiperparámetros seleccionados en train externo fijos para sus submuestras; grupos completos; sin nueva HPO por fracción.',
            improvement={'reducción_RMSE_vs_dummy_%': 100*(1-svm_tests[0]['RMSE']/svm_tests[1]['RMSE']),
                         'reducción_MAPE_vs_dummy_%': 100*(1-svm_tests[0]['MAPE_%']/svm_tests[1]['MAPE_%'])})
        write_json(output / 'modelos_lineales.json', report)
        assert code == {p: file_hash(BOOK / p) for p in scripts}, 'Código cambió durante la ejecución'
        write_json(output / 'completo.json', {'run_id': timing.run_id, 'models': list(NAMES), 'status': 'completa'})
        status = 'completa'
        print(f'EJECUCIÓN COMPLETA: {output}', flush=True)
    finally:
        timing.finish(status)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    with threadpool_limits(limits=1), joblib.parallel_backend('loky', inner_max_num_threads=1):
        run()

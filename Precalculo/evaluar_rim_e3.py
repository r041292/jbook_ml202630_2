"""RIM: CV anidada 5x5 por estudiante, test temporal y comparación exploratoria."""
import gc
import importlib.metadata
import json
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import ParameterGrid
from statsmodels.stats.multitest import multipletests

from entregable3 import (BOOK, OUTPUT, FEATURES, GROUP, TARGET, grouped_splits,
                        metrics, source_hashes, write_json)
from evaluacion_nuevos_e3 import partitions
from evaluar_tabpfn25_finetuned_e3 import paired_comparison
from finetune_tabpfn25_e3 import sha256
from rim_regresion_e3 import RIMRegressor

FOLDER = OUTPUT/'rim'
PRIVATE = BOOK/'modelos_preentrenados/rim_e3'
GRID = {'n_neighbors': [5, 15], 'epochs': [30, 60], 'weight_decay': [.001, .01]}
FIXED = {'embedding_dim': 8, 'n_bins': 8, 'label_bins': 10, 'learning_rate': .001,
         'batch_size': 256, 'dropout': .1, 'random_state': 42}
REF = {'paper': 'https://arxiv.org/abs/2108.05252', 'repository': 'https://github.com/qinjr/RIM',
       'revision': 'a6b4cdb347f306f9cf54a98fc994bf7112b53e9e',
       'files_consulted': ['code/rim.py', 'code/train_reg.py', 'code/data_ppl/es_reader.py',
                           'code/data_ppl/hori_split.py', 'configs/train_params.ini']}


def signature():
    paths = ['rim_regresion_e3.py', 'evaluar_rim_e3.py', 'evaluar_tabpfn25_finetuned_e3.py',
             'resultados/e3/train.csv.gz', 'resultados/e3/test.csv.gz',
             'resultados/e3/clasicos/comparacion.json', 'resultados/e3/clasicos/test_predictions.csv.gz',
             'resultados/e3/logicdt/reporte.json', 'resultados/e3/logicdt/test_predictions.csv.gz',
             'resultados/e3/tabpfn_25/reporte.json', 'resultados/e3/tabpfn_25/test_predictions.csv.gz',
             'resultados/e3/tabpfn_25_finetuned/20261015_091524_448419/reporte.json',
             'resultados/e3/tabpfn_25_finetuned/20261015_091524_448419/test_predictions.csv.gz']
    return {**source_hashes(), **{p: sha256(BOOK/p) for p in paths},
            'grid': GRID, 'fixed': FIXED,
            'versions': {p: importlib.metadata.version(p) for p in ['torch', 'scikit-learn', 'numpy', 'pandas']}}


def fit_model(frame, params):
    return RIMRegressor(**FIXED, **params).fit(frame[FEATURES], frame[TARGET], groups=frame[GROUP])


def tune(frame, label):
    splits = grouped_splits(frame)
    rows = []
    for candidate, params in enumerate(ParameterGrid(GRID), 1):
        errors = []
        for fold, (fi, va) in enumerate(splits, 1):
            fit, val = frame.iloc[fi], frame.iloc[va]
            model = fit_model(fit, params)
            pred = model.predict(val[FEATURES], query_groups=val[GROUP].to_numpy())
            score = metrics(val[TARGET], pred)
            errors.append(score['RMSE'])
            rows.append({'candidate': candidate, 'inner_fold': fold, **params, **score})
            del model
        print(f'{label}: candidato {candidate}/8 RMSE interno={np.mean(errors):.6f}', flush=True)
    grid = pd.DataFrame(rows)
    grouped = grid.groupby('candidate', sort=True).RMSE.mean()
    selected = int(grouped.idxmin())
    best_params = list(ParameterGrid(GRID))[selected-1]
    grid.to_csv(FOLDER/f'grid_{label}.csv', index=False)
    return fit_model(frame, best_params), best_params, float(grouped.loc[selected])


def run(force=False):
    train, test, splits, audit = partitions()
    FOLDER.mkdir(parents=True, exist_ok=True)
    PRIVATE.mkdir(parents=True, exist_ok=True)
    stamp = signature()
    path = FOLDER/'reporte.json'
    if path.exists() and not force:
        cached = json.loads(path.read_text(encoding='utf-8'))
        if cached['provenance'] == stamp:
            print('RIM: evaluación completa con procedencia verificada.', flush=True)
            return cached
    write_json(FOLDER/'protocolo.json', {'grid': GRID, 'fixed': FIXED, 'provenance': stamp,
        'test_used_for_selection': False, 'reference': REF,
        'primary_comparator': 'TabPFN 2.5 original',
        'statistics': 'Dos pares actuales con Holm; además familia acumulada de nueve candidatos vs SVM. '
                      'Esto no corrige completamente una búsqueda adaptativa indefinida sobre test ya visto.'})
    oof, fold_rows, audits = np.full(len(train), np.nan), [], []
    for k, (fi, va) in enumerate(splits, 1):
        print(f'RIM fold externo {k}/5', flush=True)
        started = time.perf_counter()
        fit, val = train.iloc[fi], train.iloc[va]
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', message='Found unknown categories')
            model, params, inner = tune(fit, f'externo_{k}')
            oof[va] = model.predict(val[FEATURES], query_groups=val[GROUP].to_numpy())
        fold_rows.append({'Modelo': 'RIM (port E3)', 'Fold': k, **metrics(val[TARGET], oof[va])})
        audits.append({'fold': k, 'best_params': params, 'best_inner_rmse': inner,
                       'fit_rows': len(fi), 'validation_rows': len(va), 'shared_students': 0,
                       'seconds': time.perf_counter()-started})
        joblib.dump(model, PRIVATE/f'fold_{k}.joblib')
        write_json(FOLDER/'progreso.json', {'fold_metrics': fold_rows, 'audit': audits, 'provenance': stamp})
        print(f'RIM externo {k}: RMSE={fold_rows[-1]["RMSE"]:.6f}; {audits[-1]["seconds"]:.1f}s', flush=True)
        del model
        gc.collect()
    if not np.isfinite(oof).all():
        raise ValueError('OOF incompleto.')
    print('RIM búsqueda final solo en train.', flush=True)
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='Found unknown categories')
        final, params, inner = tune(train, 'final')
    write_json(FOLDER/'seleccion_final_antes_test.json', {'best_params': params, 'inner_rmse': inner,
                                                       'provenance': stamp})
    joblib.dump(final, PRIVATE/'modelo_final.joblib')
    print('RIM configuración fijada; inferencia test202530.', flush=True)
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='Found unknown categories')
        pred = final.predict(test[FEATURES], query_groups=test[GROUP].to_numpy())
    score = metrics(test[TARGET], pred)
    for label, frame, values in [('train', train, oof), ('test', test, pred)]:
        export = frame[[TARGET, 'periodo']].copy()
        export['prediccion'] = values
        export['residuo'] = export[TARGET]-values
        if label == 'train':
            export['fold'] = pd.read_csv(OUTPUT/'train.csv.gz')['fold']
        export.to_csv(FOLDER/f'{label}_predictions.csv.gz', index=False, compression='gzip')
    fold_frame = pd.DataFrame(fold_rows)
    fold_frame.to_csv(FOLDER/'fold_metrics.csv', index=False)
    fine_folder = OUTPUT/'tabpfn_25_finetuned/20261015_091524_448419'
    previous = json.loads((fine_folder/'reporte.json').read_text(encoding='utf-8'))
    comparison = previous['comparison_test'] + [{'Modelo': 'RIM (port E3)', **score}]
    y = test[TARGET].to_numpy(float)
    svm = pd.read_csv(OUTPUT/'test.csv.gz').svm.to_numpy(float)
    base = pd.read_csv(OUTPUT/'tabpfn_25/test_predictions.csv.gz').prediccion.to_numpy().astype(np.float32).astype(float)
    paired = []
    for label, other in [('TabPFN 2.5 original', base), ('SVM lineal', svm)]:
        paired.append({'referencia': label, 'rows': paired_comparison(y, pred, other, test[GROUP])})
    adjusted = multipletests([c['rows'][0]['p_bilateral'] for c in paired], method='holm')[1]
    for comp, value in zip(paired, adjusted):
        for row in comp['rows']:
            row['p_Holm_dos_pares'] = float(value)
    # Familia acumulada fijada de métodos ya examinados en este proyecto vs SVM.
    old = pd.read_csv(OUTPUT/'clasicos/test_predictions.csv.gz')
    candidates = {name: old[key].to_numpy(float) for key, name in
                  [('knn', 'KNN'), ('ridge', 'Ridge'), ('lasso', 'Lasso'),
                   ('forest', 'Random Forest'), ('xgboost', 'XGBoost')]}
    candidates['logicDT'] = pd.read_csv(OUTPUT/'logicdt/test_predictions.csv.gz').prediccion.to_numpy(float)
    candidates['TabPFN original'] = base
    candidates['TabPFN ajustado'] = pd.read_csv(fine_folder/'test_predictions.csv.gz').prediccion.to_numpy(float)
    candidates['RIM'] = pred
    family = []
    for name, values in candidates.items():
        row = paired_comparison(y, values, svm, test[GROUP])[0]
        family.append({'modelo': name, **row})
    adjusted = multipletests([c['p_bilateral'] for c in family], method='holm')[1]
    for row, value in zip(family, adjusted):
        row['p_Holm_nueve_metodos'] = float(value)
    cv = [{'metrica': m, 'media_cv': fold_frame[m].mean(), 'sd_cv': fold_frame[m].std(ddof=0),
           'OOF_agrupado': metrics(train[TARGET], oof)[m]} for m in score]
    report = {'model': 'RIM (port E3)', 'provenance': stamp, 'reference': REF, 'partition': audit,
              'test': score, 'cv': cv, 'best_params': params, 'fixed_params': FIXED,
              'fold_audit': audits, 'comparison_test': comparison, 'paired_comparisons': paired,
              'family_vs_svm': family,
              'method': '5x5 GroupKFold por estudiante, selección RMSE y test temporal202530. '
                        'Índice/etiquetas de recuperación solo fit; autoestudiante excluido en train. '
                        'Sin early stopping sobre validación; épocas son parte de la grilla.',
              'adaptations': 'PyTorch, BM25 Lucene local, mismos15 campos y preparación canónica con '
                             'discretización numérica adicional y embeddings en lugar de one-hot; '
                             'pool=fit excluyendo estudiante consultado en vez de reservar tercera tabla; '
                             'MLP64/32, LayerNorm, target normalizado, etiquetas recuperadas discretizadas '
                             'en cuantiles; regresión lineal de salida y skip de etiquetas según artículo.',
              'statistics': 'Permutación pareada bilateral99999, bootstrap10000 por estudiante, seed42; '
                            'RMSE/R² comparten SSE. Holm dos pares y Holm familia conocida9vsSVM. '
                            'Resultados exploratorios por reutilización adaptativa del test; una mejora '
                            'confirmatoria exigiría nuevos datos reservados. No prometer alcanzar p<.05.',
              'outputs': str(FOLDER), 'private_model': str(PRIVATE/'modelo_final.joblib')}
    write_json(path, report)
    pd.DataFrame(comparison).to_csv(FOLDER/'comparacion_test.csv', index=False)
    pd.DataFrame([{'referencia': c['referencia'], **r} for c in paired for r in c['rows']]).to_csv(
        FOLDER/'comparaciones_pareadas.csv', index=False)
    pd.DataFrame(family).to_csv(FOLDER/'familia_vs_svm.csv', index=False)
    print(json.dumps(score, ensure_ascii=False), flush=True)
    return report


if __name__ == '__main__':
    import sys
    run(force='--force' in sys.argv)

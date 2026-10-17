"""Evaluación ordenada TCR-XGBoost -> TabICLv2 -> HRT-Boost, aislada del tablero."""
import argparse
import gc
import importlib
import importlib.metadata
import json
import time
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import ParameterGrid
from statsmodels.stats.multitest import multipletests
from threadpoolctl import threadpool_limits

from entregable3 import BOOK, OUTPUT, FEATURES, GROUP, TARGET, grouped_splits, metrics, source_hashes, write_json
from evaluacion_nuevos_e3 import partitions
from evaluar_tabpfn25_finetuned_e3 import paired_comparison
from finetune_tabpfn25_e3 import sha256

ORDER = ['tcr_xgboost', 'tabicl_v2', 'hrt_boost']
LABELS = {'tcr_xgboost': 'TCR-XGBoost', 'tabicl_v2': 'TabICLv2', 'hrt_boost': 'HRT-Boost'}
MODULES = {'tcr_xgboost': 'tcr_xgboost_e3', 'tabicl_v2': 'tabicl_modelo_e3', 'hrt_boost': 'hrt_modelo_e3'}


def base_report():
    from modelos_clasicos import provenance
    report = json.loads((OUTPUT/'clasicos/comparacion.json').read_text(encoding='utf-8'))
    if report['source_sha256'] != provenance():
        raise ValueError('La evaluación clásica está desactualizada.')
    return report


def make_model(key, params, base_params=None):
    module = importlib.import_module(MODULES[key])
    if key == 'tcr_xgboost':
        return module.TCRXGBRegressor(**params, base_params=base_params)
    return module.make_model(**params)


def candidate_grid(key):
    return list(ParameterGrid(importlib.import_module(MODULES[key]).GRID))


def fit_model(model, frame):
    with warnings.catch_warnings(), threadpool_limits(limits=1):
        warnings.filterwarnings('ignore', message='Found unknown categories')
        model.fit(frame[FEATURES], frame[TARGET])
    return model


def predict(model, frame):
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='Found unknown categories')
        return np.asarray(model.predict(frame[FEATURES]), dtype=float)


def tune(key, frame, folder, label, base_params):
    candidates = candidate_grid(key)
    # TabICL es una configuración prefijada sin HPO: no necesita selección interna.
    if len(candidates) == 1:
        return fit_model(make_model(key, candidates[0], base_params), frame), candidates[0], None
    rows = []
    for candidate, params in enumerate(candidates, 1):
        for fold, (fi, va) in enumerate(grouped_splits(frame), 1):
            model = fit_model(make_model(key, params, base_params), frame.iloc[fi])
            rows.append({'candidate': candidate, 'inner_fold': fold, **params,
                         **metrics(frame.iloc[va][TARGET], predict(model, frame.iloc[va]))})
            del model
        values = [r['RMSE'] for r in rows if r['candidate'] == candidate]
        print(f'{key} {label}: candidato{candidate}/{len(candidates)} RMSE={np.mean(values):.6f}', flush=True)
    table = pd.DataFrame(rows)
    table.to_csv(folder/f'grid_{label}.csv', index=False)
    scores = table.groupby('candidate').RMSE.mean()
    chosen = int(scores.idxmin())
    params = candidates[chosen-1]
    return fit_model(make_model(key, params, base_params), frame), params, float(scores.loc[chosen])


def provenance(key):
    module = importlib.import_module(MODULES[key])
    paths = ['comparacion_seleccionados_e3.py', MODULES[key]+'.py',
             'resultados/e3/train.csv.gz', 'resultados/e3/test.csv.gz',
             'resultados/e3/clasicos/comparacion.json', 'resultados/e3/rim/reporte.json']
    packages = ['numpy', 'pandas', 'scipy', 'scikit-learn', 'xgboost']
    packages += {'tcr_xgboost': [], 'tabicl_v2': ['tabicl', 'torch'], 'hrt_boost': ['hrt-boost']}[key]
    return {**source_hashes(), **{p: sha256(BOOK/p) for p in paths},
            'grid': candidate_grid(key), 'reference': module.REFERENCE,
            'versions': {p: importlib.metadata.version(p) for p in packages}}


def family_predictions(new_key, new_pred):
    classic = pd.read_csv(OUTPUT/'clasicos/test_predictions.csv.gz')
    values = {name: classic[key].to_numpy(float) for key, name in
              [('knn','KNN'), ('ridge','Ridge'), ('lasso','Lasso'), ('forest','Random Forest'), ('xgboost','XGBoost')]}
    for label, relative in [('logicDT', 'logicdt'), ('TabPFN ajustado','tabpfn_25_finetuned/20261015_091524_448419'), ('RIM','rim')]:
        values[label] = pd.read_csv(OUTPUT/relative/'test_predictions.csv.gz').prediccion.to_numpy(float)
    values['TabPFN original'] = pd.read_csv(OUTPUT/'tabpfn_25/test_predictions.csv.gz').prediccion.to_numpy().astype(np.float32).astype(float)
    for key in ORDER:
        if key == new_key:
            values[LABELS[key]] = new_pred
        elif (OUTPUT/key/'reporte.json').exists():
            values[LABELS[key]] = pd.read_csv(OUTPUT/key/'test_predictions.csv.gz').prediccion.to_numpy(float)
    return values


def run(key, force=False):
    train, test, folds, audit = partitions()
    original = base_report()
    folder, private = OUTPUT/key, BOOK/'modelos_preentrenados'/key
    folder.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)
    stamp = provenance(key)
    if (folder/'reporte.json').exists() and not force:
        cached = json.loads((folder/'reporte.json').read_text(encoding='utf-8'))
        if cached['provenance'] == stamp:
            print(f'{key}: resultado completo verificado.', flush=True)
            return cached
    write_json(folder/'protocolo.json', {'provenance': stamp, 'test_used_for_selection': False,
        'method': '5 folds externos por estudiante; 5 internos si hay grilla. '
                  'TCR reutiliza parámetros base XGBoost seleccionados solo dentro del fit externo original.'})
    oof, rows, audits = np.full(len(train), np.nan), [], []
    for k, (fi, va) in enumerate(folds, 1):
        start = time.perf_counter()
        base = original['models']['xgboost']['fold_audit'][k-1]['best_params'] if key == 'tcr_xgboost' else None
        print(f'{key}: fold externo{k}/5', flush=True)
        model, params, inner = tune(key, train.iloc[fi], folder, f'externo_{k}', base)
        oof[va] = predict(model, train.iloc[va])
        rows.append({'Modelo': LABELS[key], 'Fold': k, **metrics(train.iloc[va][TARGET], oof[va])})
        audits.append({'fold': k, 'fit_rows': len(fi), 'validation_rows': len(va),
            'shared_students': len(set(train.iloc[fi][GROUP]) & set(train.iloc[va][GROUP])),
            'best_params': params, 'xgboost_base_params': base, 'inner_rmse': inner,
            'seconds': time.perf_counter()-start})
        joblib.dump(model, private/f'fold_{k}.joblib')
        write_json(folder/'progreso.json', {'fold_metrics': rows, 'fold_audit': audits})
        print(f'{key}: externo{k} RMSE={rows[-1]["RMSE"]:.6f}, {audits[-1]["seconds"]:.1f}s', flush=True)
        del model
        gc.collect()
    base = original['models']['xgboost']['best_params'] if key == 'tcr_xgboost' else None
    print(f'{key}: selección/refit final solo train.', flush=True)
    model, params, inner = tune(key, train, folder, 'final', base)
    joblib.dump(model, private/'modelo_final.joblib')
    write_json(folder/'seleccion_antes_test.json', {'params': params, 'xgboost_base_params': base, 'inner_rmse': inner})
    pred = predict(model, test)
    score = metrics(test[TARGET], pred)
    if not np.isfinite(oof).all() or not np.isfinite(pred).all():
        raise ValueError('Predicciones incompletas/no finitas.')
    for split, frame, values in [('train',train,oof), ('test',test,pred)]:
        export = frame[[TARGET,'periodo']].copy()
        export['prediccion'], export['residuo'] = values, frame[TARGET]-values
        if split == 'train':
            export['fold'] = pd.read_csv(OUTPUT/'train.csv.gz').fold
        export.to_csv(folder/f'{split}_predictions.csv.gz', index=False, compression='gzip')
    fold_frame = pd.DataFrame(rows)
    fold_frame.to_csv(folder/'fold_metrics.csv', index=False)
    previous = json.loads((OUTPUT/'rim/reporte.json').read_text(encoding='utf-8'))['comparison_test']
    # Añadir las etapas ya completadas sin sobrescribir las referencias anteriores.
    comparison = list(previous)
    for old in ORDER:
        if old != key and (OUTPUT/old/'reporte.json').exists():
            r = json.loads((OUTPUT/old/'reporte.json').read_text(encoding='utf-8'))
            comparison.append({'Modelo': LABELS[old], **r['test']})
    comparison.append({'Modelo': LABELS[key], **score})
    y = test[TARGET].to_numpy(float)
    svm = pd.read_csv(OUTPUT/'test.csv.gz').svm.to_numpy(float)
    candidates = family_predictions(key, pred)
    paired = [{'referencia': name, 'rows': paired_comparison(y,pred,other,test[GROUP])}
              for name,other in [('SVM lineal',svm), ('TabPFN original', candidates['TabPFN original'])]]
    corrected = multipletests([c['rows'][0]['p_bilateral'] for c in paired], method='holm')[1]
    for comp,p in zip(paired,corrected):
        for row in comp['rows']:
            row['p_Holm_dos_pares'] = float(p)
    family = [{'modelo': name, **paired_comparison(y,values,svm,test[GROUP])[0]}
              for name,values in candidates.items()]
    corrected = multipletests([r['p_bilateral'] for r in family], method='holm')[1]
    for row,p in zip(family,corrected):
        row['p_Holm_familia_conocida'] = float(p)
    cv = [{'metrica':m,'media_cv':fold_frame[m].mean(),'sd_cv':fold_frame[m].std(ddof=0),
           'OOF_agrupado':metrics(train[TARGET],oof)[m]} for m in score]
    report = {'model':LABELS[key], 'key':key,'test':score,'cv':cv,'best_params':params,
        'xgboost_base_params':base,'partition':audit,'fold_audit':audits,'provenance':stamp,
        'comparison_test':comparison,'paired_comparisons':paired,'family_vs_svm':family,
        'method': 'Selección solo train, folds por estudiante, métricas sin pesos. '
                  'TabICLv2 fijo sin HPO; TCR/HRT usan 5x5 con selección interna. '
                  'TCR usa base XGBoost anidada original; no parámetros del train completo en folds externos.',
        'statistics':'Permutación bilateral99999, bootstrap10000 por estudiante; seed42; '
                     'Holm dos pares y familia acumulada conocida. RMSE/R² son el mismo contraste SSE. '
                     'Inferencia exploratoria por reutilización de test; no incorpora variabilidad por reentrenar.',
        'outputs':str(folder),'private_model':str(private/'modelo_final.joblib')}
    if key == 'tcr_xgboost':
        pd.DataFrame({'robustez':model.robustness_,'peso':model.sample_weights_}).to_csv(folder/'pesos_train.csv',index=False)
    write_json(folder/'reporte.json',report)
    pd.DataFrame(comparison).to_csv(folder/'comparacion_test.csv',index=False)
    pd.DataFrame(family).to_csv(folder/'familia_vs_svm.csv',index=False)
    pd.DataFrame([{'referencia':c['referencia'],**r} for c in paired for r in c['rows']]).to_csv(folder/'pareadas.csv',index=False)
    print(f'{key} TEST: '+json.dumps(score,ensure_ascii=False),flush=True)
    return report


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('model',choices=ORDER+['all'])
    p.add_argument('--force',action='store_true')
    args=p.parse_args()
    for name in (ORDER if args.model=='all' else [args.model]):
        run(name,args.force)

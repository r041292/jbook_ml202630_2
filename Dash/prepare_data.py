"""Reproduce el pipeline del notebook sin modificar sus fuentes ni los CSV."""
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from sklearn.base import clone
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error, r2_score

ROOT = Path(__file__).resolve().parent
BOOK = ROOT.parent / 'Precalculo'
CACHE = ROOT / 'data'
SOURCES = [BOOK / 'precalculo_regresion_lineal.ipynb',
           BOOK / 'comparacion_aumentacion/Datos_Aleks_Augmented_30000_r_2_train.csv',
           BOOK / 'comparacion_aumentacion/Datos_Aleks_Augmented_30000_r_2_test.csv',
           BOOK / 'comparacion_aumentacion/seleccion.json',
           BOOK / 'resultados/modelos_lineales.json',
           BOOK / 'resultados/eda.json',
           BOOK / 'precalculo_eda_comprehensivo.ipynb',
           BOOK / '00_seleccion_base_datos.md',
           BOOK / 'precalculo_generar_split_augmented_2.ipynb',
           BOOK / 'Data/Datos_Brutos.csv', BOOK / 'cabeceras.csv',
           BOOK / 'comparacion_aumentacion/comparacion_train.csv']


def hashes():
    return {p.relative_to(BOOK).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCES}


def metrics(y, pred):
    return {'RMSE': float(np.sqrt(mean_squared_error(y, pred))),
            'MAE': float(mean_absolute_error(y, pred)),
            'MAPE (%)': float(100 * mean_absolute_percentage_error(y, pred)),
            'R²': float(r2_score(y, pred)) if len(y) > 1 and np.var(y) > 0 else None}


def prepare():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    CACHE.mkdir(exist_ok=True)
    selection = json.loads(SOURCES[3].read_text(encoding='utf-8'))
    if selection['alternativa_seleccionada'] != 1:
        raise AssertionError('El dashboard debe usar la alternativa 1 seleccionada.')
    report = json.loads(SOURCES[4].read_text(encoding='utf-8'))
    for name, expected_hash in report['source_sha256'].items():
        if hashlib.sha256((BOOK / name).read_bytes()).hexdigest() != expected_hash:
            raise AssertionError('Los resultados del notebook no corresponden a los CSV seleccionados: ' + name)
    notebook = json.loads(SOURCES[0].read_text(encoding='utf-8'))
    namespace = {'display': lambda *args, **kwargs: None}
    previous = Path.cwd()
    try:
        os.chdir(BOOK)
        # Configuración, auditoría, roles, folds y pipeline exactos del notebook vigente.
        for index in [1, 3, 6, 8, 11]:
            exec(''.join(notebook['cells'][index]['source']), namespace)
        train = namespace['df_train'].drop(columns='nota_final').copy()
        test = namespace['df_test'].drop(columns='nota_final').copy()
        X, y = namespace['X_train'], namespace['y_train']
        rows = []
        for label, key, column in [('Dummy media', 'dummy_pipeline', 'dummy'),
                                   ('SVM lineal', 'linear_svm_pipeline', 'svm')]:
            oof = np.empty(len(train))
            for fold, (fit_idx, val_idx) in enumerate(namespace['cv_splits'], 1):
                model = clone(namespace[key]).fit(X.iloc[fit_idx], y.iloc[fit_idx])
                pred = model.predict(X.iloc[val_idx])
                oof[val_idx] = pred
                rows.append({'Modelo': label, 'Fold': fold, **metrics(y.iloc[val_idx], pred)})
                print(f'{label}: fold {fold}/5', flush=True)
            train[column] = oof
            model = namespace[key].fit(X, y)
            test[column] = model.predict(namespace['X_test'])
            if column == 'svm':
                joblib.dump(model, CACHE / 'model.joblib')
                names = model.named_steps['preprocesamiento'].get_feature_names_out()
                pd.DataFrame({'Variable': names, 'Coeficiente': model.named_steps['modelo'].coef_}).to_csv(
                    CACHE / 'coefficients.csv', index=False)
        train.to_csv(CACHE / 'train.csv.gz', index=False, compression='gzip')
        test.to_csv(CACHE / 'test.csv.gz', index=False, compression='gzip')
        pd.DataFrame(rows).to_csv(CACHE / 'fold_metrics.csv', index=False)
        final = metrics(test['nota_primer_parcial'], test['svm'])
        saved = next(r for r in report['test'] if r['modelo'] == 'SVM lineal')
        expected = {'RMSE': saved['RMSE'], 'MAE': saved['MAE'], 'R²': saved['R2'], 'MAPE (%)': saved['MAPE_%']}
        for metric, value in expected.items():
            if abs(final[metric] - value) > 1e-10:
                raise AssertionError(f'{metric}: {final[metric]} no reproduce {value}')
        from prepare_comparison import prepare_comparison
        prepare_comparison(BOOK, CACHE)
        (CACHE / 'manifest.json').write_text(json.dumps({
            'sha256': hashes(), 'train_valid': len(train), 'test_valid': len(test),
            'technique': 'perturbacion_local', 'selected_alternative': 1,
            'model_sha256': hashlib.sha256((CACHE / 'model.joblib').read_bytes()).hexdigest(),
            'test_metrics': final, 'method': 'OOF de cinco folds para validación; ajuste completo train para test',
        }, indent=2, ensure_ascii=False), encoding='utf-8')
        print(json.dumps(final), flush=True)
    finally:
        os.chdir(previous)


if __name__ == '__main__':
    prepare()

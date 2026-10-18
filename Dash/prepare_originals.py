"""Exportación sin entrenamiento: inventario E3 y predicciones alineadas, sin IDs."""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
BOOK = ROOT.parent / 'Precalculo'
RESULTS = BOOK / 'resultados/e3'
DEST = ROOT / 'data/originales'
FILES = ('catalog.json', 'train.csv.gz', 'test.csv.gz', 'folds.csv', 'contrasts.csv', 'inventory.csv', 'best.joblib',
         'tn_krr.joblib', 'cv_inference.csv', 'cv_inference.json')

# Nombre publicado, carpeta canónica, referencia de fundamento (no garantiza mejora E3).
EXPERIMENTS = [
    ('SVR RBF', 'svr_rbf_raffle/svr_rbf', 'https://doi.org/10.1023/B:STCO.0000035301.49549.88'),
    ('TabICLv2', 'tabicl_v2', 'https://proceedings.mlr.press/v306/qu26a.html'),
    ('TabPFN 2.5 original', 'tabpfn_25', 'https://arxiv.org/abs/2511.08667'),
    ('LinXGBoost (hojas completas E3)', 'linxgboost', 'https://arxiv.org/abs/1710.03634'),
    ('TabPFN 2.5 fine-tuned', 'tabpfn_25_finetuned/20261015_091524_448419', 'https://arxiv.org/abs/2511.08667'),
    ('Kernel Ridge RBF', 'scopus/kernel_ridge', 'https://doi.org/10.3390/app12094252'),
    ('CatBoost', 'scopus/catboost', 'https://proceedings.neurips.cc/paper/2018/hash/14491b756b3a51daac41c24863285549-Abstract.html'),
    ('TCR-XGBoost', 'tcr_xgboost', 'https://doi.org/10.1007/s10994-024-06704-x'),
    ('TabFM 1.0.0 (PyTorch CPU, 32 vistas)', 'tabfm', 'https://arxiv.org/abs/2609.37959'),
    ('XGBoost ampliado (gbtree)', 'xgboost_variantes/gbtree', 'https://doi.org/10.1145/2939672.2939785'),
    ('RaFFLE', 'svr_rbf_raffle/raffle', 'https://arxiv.org/abs/2502.10185'),
    ('DenseWeight-XGBoost', 'xgboost_variantes/denseweight', 'https://doi.org/10.1007/s10994-021-06023-5'),
    ('DART-XGBoost', 'xgboost_variantes/dart', 'https://proceedings.mlr.press/v38/korlakaivinayak15.html'),
    ('HRT-Boost', 'hrt_boost', 'https://arxiv.org/abs/2605.23422'),
    ('logicDT propio (adaptado)', 'logicdt', 'https://doi.org/10.1007/s10994-023-06488-6'),
    ('GPR–XGBoost (OOF agrupado)', 'gpr_xgb', 'https://arxiv.org/abs/2610.15862'),
    ('RIM (port E3)', 'rim', 'https://arxiv.org/abs/2108.05252'),
    ('XBART (GFR)', 'scopus/xbart', 'https://doi.org/10.1080/01621459.2021.1942012'),
    ('coPILOT', 'scopus/copilot', 'https://doi.org/10.1007/s11634-026-00683-8'),
    ('Truncated Newton KRR RBF', 'tn_krr', 'https://doi.org/10.3390/app12094252'),
]
CLASSIC_PAPERS = {
    'decision_tree': 'https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeRegressor.html',
    'svm': 'https://doi.org/10.1023/B:STCO.0000035301.49549.88',
    'knn': 'https://doi.org/10.2307/2685209',
    'ridge': 'https://doi.org/10.1080/00401706.1970.10488634',
    'lasso': 'https://doi.org/10.1111/j.2517-6161.1996.tb02080.x',
    'forest': 'https://doi.org/10.1023/A:1010933404324',
    'xgboost': 'https://doi.org/10.1145/2939672.2939785',
}
CANONICAL_PREP = 'Mediana numérica, log1p de tiempos y StandardScaler; moda y one-hot categórico con referencia. Todo se aprende en cada fit.'
DETAILS = {
    'svr_rbf_raffle/svr_rbf': ('SVR usa una banda epsilon de tolerancia al error y un kernel RBF para aprender relaciones no lineales.', CANONICAL_PREP),
    'tabicl_v2': ('Modelo preentrenado que usa las filas de train como contexto para inferir nuevas respuestas, sin HPO local.', CANONICAL_PREP),
    'tabpfn_25': ('Transformer preentrenado que aproxima inferencia predictiva en tablas mediante aprendizaje en contexto; sin ajuste local de pesos.', CANONICAL_PREP),
    'tabpfn_25_finetuned/20261015_091524_448419': ('TabPFN 2.5 con ajuste adicional de pesos usando train; no dispone de nueva evaluación OOF independiente.', CANONICAL_PREP),
    'linxgboost': ('Boosting de árboles cuyas hojas ajustan regresiones Ridge locales. Port independiente con cortes cuantílicos aproximados.', CANONICAL_PREP + ' Escalado adicional de todas las columnas para las hojas lineales.'),
    'scopus/kernel_ridge': ('Ridge en un kernel RBF: permite relaciones no lineales mediante una solución matricial exacta; no reproduce Truncated Newton del artículo.', CANONICAL_PREP + ' Objetivo centrado dentro de fit.'),
    'tn_krr': ('Kernel Ridge RBF con el sistema dual resuelto por gradiente conjugado truncado (TR-KRR), siguiendo el método del artículo.', CANONICAL_PREP + ' Sin centrar el objetivo. Límite CG: 200 iteraciones, residuo L2 ≤0.5 y 25 iteraciones sin mejora; inicia con coeficientes cero.'),
    'scopus/catboost': ('Boosting ordenado de árboles con tratamiento de variables categóricas.', 'Mediana/moda y tipos categóricos nativos; sin one-hot externo, log1p ni escalado.'),
    'scopus/copilot': ('Conjunto de árboles con modelos lineales locales basado en PILOT, usando el código de los autores.', 'Mediana/moda y códigos ordinales; sin escalado. Se conserva la truncación interna del algoritmo original.'),
    'scopus/xbart': ('Árboles bayesianos acelerados; variante GFR de stochtree, sin fase MCMC, distinta del binario XBART original.', CANONICAL_PREP),
    'tcr_xgboost': ('Reduce el peso de observaciones con baja robustez local antes de ajustar XGBoost; no elimina filas.', CANONICAL_PREP + ' MinMaxScaler para distancias; predictor XGBoost con categorías nativas y base ajustada dentro del fold.'),
    'hrt_boost': ('Boosting de árboles con regresiones Ridge locales; combina particiones con tendencias lineales regularizadas.', CANONICAL_PREP),
    'rim': ('Recupera ejemplos similares de train mediante BM25 y usa una red para combinar información local; port E3.', 'Preparación canónica, discretización numérica y embeddings; índice y etiquetas de recuperación solo del fit, con autoestudiante excluido.'),
    'logicdt': ('Busca interacciones lógicas y combina reglas con hojas de media o Ridge; adaptación propia, no el algoritmo R exacto.', CANONICAL_PREP),
    'gpr_xgb': ('Un proceso gaussiano estima la respuesta y XGBoost intenta corregir su residuo; las meta-features de train se generan mediante OOF agrupado.', CANONICAL_PREP),
    'svr_rbf_raffle/raffle': ('Bosque de árboles PILOT con modelos lineales locales y particiones adaptativas.', 'Mediana numérica, moda y códigos ordinales categóricos con índices explícitos; sin escalado.'),
    'tabfm': ('Modelo tabular preentrenado zero-shot, sin fine-tuning ni HPO, con 32 vistas de inferencia.', 'Preparación del modelo dentro de fit; se desactiva su recorte de extremos para conservar los outliers E3.'),
}


def source_paths():
    paths = [RESULTS / 'resumen_completo/modelos.csv', RESULTS / 'resumen_completo/contrastes_actuales.csv']
    for _, folder, _ in EXPERIMENTS:
        directory = RESULTS / folder
        paths += [directory / ('reporte_modelo.json' if folder == 'linxgboost' else 'reporte.json'),
                  directory / 'test_predictions.csv.gz']
        train = directory / ('oof_predictions.csv.gz' if folder == 'linxgboost' else 'train_predictions.csv.gz')
        if train.exists():
            paths.append(train)
        paths += list(directory.glob('grid*.csv')) + list(directory.glob('fold_metrics.csv'))
    paths += [BOOK / 'modelos_preentrenados/scopus/kernel_ridge/modelo_final.joblib']
    tn_directory = RESULTS / 'tn_krr'
    paths += [BOOK / 'tn_krr_e3.py', BOOK / 'evaluar_tn_krr_e3.py',
              BOOK / 'significancia_tn_krr_e3.py',
              BOOK / 'modelos_preentrenados/tn_krr/modelo_final.joblib']
    paths += [tn_directory / name for name in
              ['reporte.json', 'protocolo.json', 'seleccion_antes_test.json',
               'train_predictions.csv.gz', 'test_predictions.csv.gz', 'fold_metrics.csv',
               'contrastes_test.csv', 'contrastes_test.json']]
    paths += list(tn_directory.glob('grid*.csv'))
    paths += [BOOK / 'significancia_cv_externa_e3.py', RESULTS / 'cv_externa/contrastes_vs_svm.csv',
              RESULTS / 'cv_externa/reporte.json', RESULTS / 'cv_externa/fold_metrics.csv']
    return sorted(set(paths))


def text_list(value):
    return value if isinstance(value, list) else [str(value)] if value else []


def prepare_originals():
    from prepare_data import metrics
    DEST.mkdir(exist_ok=True)
    inventory = pd.read_csv(RESULTS / 'resumen_completo/modelos.csv').set_index('Modelo')
    tn_name = 'Truncated Newton KRR RBF'
    tn_report = json.loads((RESULTS / 'tn_krr/reporte.json').read_text(encoding='utf-8'))
    tn_score = tn_report['test']
    tn_contrasts = pd.read_csv(RESULTS / 'tn_krr/contrastes_test.csv')
    tn_vs_svm = tn_contrasts.loc[tn_contrasts.Referencia.eq('SVM lineal') & tn_contrasts.metrica.eq('RMSE')].iloc[0]
    tn_vs_xgb = tn_contrasts.loc[tn_contrasts.Referencia.eq('XGBoost') & tn_contrasts.metrica.eq('RMSE')].iloc[0]
    tn_svm_rmse = float(inventory.loc['SVM lineal', 'RMSE_test'])
    tn_xgb_rmse = float(inventory.loc['XGBoost', 'RMSE_test'])
    tn_row = {column: np.nan for column in inventory.columns}
    tn_row.update({
        'rango_RMSE': int((inventory['RMSE_test'] < tn_score['RMSE']).sum()) + 1,
        'RMSE_test': tn_score['RMSE'],
        'delta_RMSE_vs_SVM': tn_score['RMSE'] - tn_svm_rmse,
        'p_bilateral': tn_vs_svm.p_bilateral,
        'p_Holm_vs_SVM_21': np.nan,
        'p_Holm_global_55': np.nan,
        'significancia_sin_correccion': 'No evaluada',
        'significancia_Holm_vs_SVM_21': 'No evaluada',
        'significancia_Holm_global_55': 'No evaluada',
        'delta_RMSE_vs_XGBoost': tn_score['RMSE'] - tn_xgb_rmse,
        'descripcion': 'KRR RBF con Truncated Newton resuelto por gradiente conjugado truncado.',
        'estado': 'Evaluado; test temporal exploratorio; contrastes no recalculados',
        'R2_test': tn_score['R²'],
        'Referencia_inferencia': 'SVM lineal',
        'familia_principal': tn_vs_svm.familia_ajuste,
        'p_bilateral_referencia': tn_vs_svm.p_bilateral,
        'p_Holm_familia_principal': tn_vs_svm.p_ajustado,
        'significancia_ajustada': 'No significativa' if tn_vs_svm.p_ajustado >= 0.05 else 'Significativa',
        'p_bilateral_vs_XGBoost': tn_vs_xgb.p_bilateral,
        'p_Holm_LinXGBoost_family_7_vs_XGBoost': np.nan,
        'p_Holm_variantes_12_vs_XGBoost': np.nan,
    })
    inventory.loc[tn_name] = tn_row
    inventory = inventory.sort_values('RMSE_test', kind='stable')
    inventory['rango_RMSE'] = np.arange(1, len(inventory) + 1)
    classic = json.loads((RESULTS / 'clasicos/comparacion.json').read_text(encoding='utf-8'))
    frames = [pd.read_csv(RESULTS / f'{part}.csv.gz') for part in ['train', 'test']]
    predictions = [pd.read_csv(RESULTS / f'clasicos/{part}_predictions.csv.gz') for part in ['train', 'test']]
    catalog = {}
    # Decision Tree se incorpora a Clásicos; el inventario/contrastes de Originales
    # conservan sus 27 modelos y familias de hipótesis vigentes.
    for key, name in {'svm': 'SVM lineal', 'dummy': 'Dummy media', **{k: v['name'] for k, v in classic['models'].items() if k != 'decision_tree'}}.items():
        spec = classic['models'].get(key, {})
        catalog[key] = {'name': name, 'description': inventory.loc[name, 'descripcion'],
                        'paper': CLASSIC_PAPERS.get(key), 'preparation': spec.get('preparation', 'Pipeline SVM canónico; Dummy estima solo la media del fit.'),
                        'params': spec.get('best_params', {}), 'grid': spec.get('grid', {}),
                        'method': '5 folds externos y 5 internos por estudiante; Dummy no tiene búsqueda.'}
    svm = json.loads((RESULTS / 'modelos_lineales.json').read_text(encoding='utf-8'))
    catalog['svm'].update(params=svm['best_params'], grid=svm['grid'])
    folds = pd.read_csv(RESULTS / 'clasicos/fold_metrics.csv')
    folds = folds.loc[~folds.Modelo.eq('Decision Tree')].copy()
    predictions = [frame.drop(columns='decision_tree', errors='ignore') for frame in predictions]
    for index, (name, folder, paper) in enumerate(EXPERIMENTS):
        key = f'm{index}'
        directory = RESULTS / folder
        report = json.loads((directory / ('reporte_modelo.json' if folder == 'linxgboost' else 'reporte.json')).read_text(encoding='utf-8'))
        for source in ['Data/Datos_Brutos.csv', 'cabeceras.csv', 'entregable3.py']:
            if report['provenance'].get(source) != svm['source_sha256'][source]:
                raise ValueError(f'Fuente incompatible en {name}: {source}')
        catalog[key] = {'name': name, 'description': inventory.loc[name, 'descripcion'], 'paper': paper,
                        'params': report.get('best_params', {}), 'method': report.get('method', '5 folds externos y 5 internos por estudiante; selección por RMSE solo en train.'),
                        'preparation': 'Transformaciones ajustadas dentro de fit. ' + ' '.join(text_list(report.get('adaptations'))),
                        'limitations': text_list(report.get('limitations')), 'grid': {}}
        for grid_path in sorted(directory.glob('grid*.csv')):
            grid = pd.read_csv(grid_path)
            for col in grid.columns:
                if col.startswith('param_') or col in (report.get('best_params') or {}):
                    parameter = col[6:] if col.startswith('param_') else col
                    catalog[key]['grid'].setdefault(parameter, set()).update(grid[col].dropna().astype(str))
        catalog[key]['grid'] = {p: sorted(v) for p, v in catalog[key]['grid'].items()}
        if folder in DETAILS:
            description, preparation = DETAILS[folder]
            catalog[key].update(description=description, preparation=preparation + ' ' + ' '.join(text_list(report.get('adaptations'))))
        else:
            catalog[key]['preparation'] = 'Mediana/moda y categorías nativas de XGBoost; sin one-hot externo, log1p ni escalado. DenseWeight estima la densidad del objetivo solo dentro de fit; DART añade dropout de árboles.'
        configuration = report.get('provenance', {}).get('configuration', {})
        if folder == 'linxgboost':
            catalog[key]['grid'] = configuration['linxgboost_e3']['parameter_distributions']
            catalog[key]['method'] = '20 muestras aleatorias por búsqueda interna; 5×5 folds agrupados. Port independiente, cortes cuantílicos aproximados.'
        elif folder.startswith('xgboost_variantes/'):
            catalog[key]['grid'] = configuration['xgboost_variantes']['models'][folder.split('/')[-1]]['param_distributions']
            catalog[key]['method'] += ' 20 muestras aleatorias por búsqueda interna.'
        elif folder.endswith('/raffle'):
            catalog[key]['grid'] = {p: configuration['raffle'][p] for p in ['alpha', 'n_features_node', 'max_depth']}
        if folder == 'tcr_xgboost':
            catalog[key]['grid'] = {'fraction': [0, .05, .1, .2], 'weight': [.3, .6, .9, 1]}
            catalog[key]['method'] += ' Control: fraction=0, weight=1; otras fracciones se cruzan solo con pesos 0.3, 0.6 y 0.9.'
        if folder == 'gpr_xgb':
            catalog[key]['params'] = {'kernel_GPR': 'Constant*(Matern(2.5)+RBF)+White', 'XGBoost': '1000 árboles, learning_rate=0.01, max_leaves=31, subsample=colsample_bytree=0.8, reg_alpha=reg_lambda=1'}
        if folder == 'tabfm':
            catalog[key]['params'] = {'vistas': 32, 'CPU': 'BF16', 'fine_tuning': False, 'outlier_threshold': 1e12}
        if folder == 'tabicl_v2':
            catalog[key]['params'] = {'n_estimators': 8, 'device': 'cpu', 'norm_methods': ['none'], 'recorte_extremos': False}
        if 'fine-tuned' in name:
            catalog[key]['params'] = {'epochs_final': report['epochs_final'], 'inference': report['inference']}
        for i, part in enumerate(['train', 'test']):
            path = directory / ('oof_predictions.csv.gz' if part == 'train' and folder == 'linxgboost' else f'{part}_predictions.csv.gz')
            if not path.exists():
                if name != 'TabPFN 2.5 fine-tuned' or part != 'train':
                    raise ValueError(f'Faltan predicciones: {name} {part}')
                continue
            pred = pd.read_csv(path)
            assert len(pred) == len(frames[i]), (name, part)
            target = 'y_true' if 'y_true' in pred else 'nota_primer_parcial'
            np.testing.assert_allclose(pred[target], frames[i]['nota_primer_parcial'], atol=1e-12, rtol=0)
            if 'periodo' in pred:
                np.testing.assert_array_equal(pred.periodo, frames[i].periodo)
            if i == 0:
                np.testing.assert_array_equal(pred.fold, frames[i].fold)
            column = 'prediction' if 'prediction' in pred else 'prediccion'
            predictions[i][key] = pred[column].to_numpy()
            if i == 1:
                # TabPFN histórico fue exportado desde float32: desfase ~3e-9 frente al agregado.
                np.testing.assert_allclose(metrics(frames[i]['nota_primer_parcial'], pred[column])['RMSE'], inventory.loc[name, 'RMSE_test'], atol=1e-7, rtol=0)
        if (directory / 'fold_metrics.csv').exists():
            extra = pd.read_csv(directory / 'fold_metrics.csv')
            extra['Modelo'] = name
            folds = pd.concat([folds, extra], ignore_index=True)
    assert len(catalog) == 27 and folds.groupby('Modelo').size().eq(5).all()
    for part, frame in zip(['train', 'test'], predictions):
        # Solo predicciones y fold; las características públicas ya están en la caché común.
        frame.to_csv(DEST / f'{part}.csv.gz', index=False)
    folds.to_csv(DEST / 'folds.csv', index=False)
    canonical_cv = pd.read_csv(RESULTS / 'cv_externa/fold_metrics.csv')
    if tn_name not in set(canonical_cv.Modelo):
        tn_folds = pd.read_csv(RESULTS / 'tn_krr/fold_metrics.csv')
        tn_folds['Modelo'] = tn_name
        canonical_cv = pd.concat([canonical_cv, tn_folds], ignore_index=True)
    columns = ['Modelo', 'Fold', 'RMSE', 'MAE', 'MAPE (%)', 'R²']
    pd.testing.assert_frame_equal(folds[columns].sort_values(['Modelo', 'Fold']).reset_index(drop=True),
                                 canonical_cv[columns].sort_values(['Modelo', 'Fold']).reset_index(drop=True),
                                 check_exact=False, rtol=1e-12)
    shutil.copyfile(RESULTS / 'cv_externa/contrastes_vs_svm.csv', DEST / 'cv_inference.csv')
    shutil.copyfile(RESULTS / 'cv_externa/reporte.json', DEST / 'cv_inference.json')
    contrasts = pd.read_csv(RESULTS / 'resumen_completo/contrastes_actuales.csv')
    retired = {'GPR sola', 'GPR solo', 'GPR sola (ablación)'}
    contrasts = contrasts.loc[~contrasts.Modelo.isin(retired) & ~contrasts.Referencia.isin(retired)]
    contrasts = pd.concat([contrasts, tn_contrasts], ignore_index=True)
    contrasts.to_csv(DEST / 'contrasts.csv', index=False)
    inventory.reset_index().to_csv(DEST / 'inventory.csv', index=False)
    import joblib
    model_path = BOOK / 'modelos_preentrenados/scopus/kernel_ridge/modelo_final.joblib'
    if str(BOOK) not in sys.path:
        sys.path.insert(0, str(BOOK))
    model = joblib.load(model_path)
    np.testing.assert_allclose(model.predict(frames[1][list(model.feature_names_in_)]),
                               predictions[1]['m5'], atol=1e-12, rtol=0)
    shutil.copyfile(model_path, DEST / 'best.joblib')
    tn_model_path = BOOK / 'modelos_preentrenados/tn_krr/modelo_final.joblib'
    tn_model = joblib.load(tn_model_path)
    tn_prediction = predictions[1]['m19']
    np.testing.assert_allclose(tn_model.predict(frames[1][list(tn_model.feature_names_in_)]),
                               tn_prediction, atol=1e-10, rtol=0)
    shutil.copyfile(tn_model_path, DEST / 'tn_krr.joblib')
    catalog['m0']['grid'] = {'C': 'loguniform(0.001, 1000)', 'epsilon': 'loguniform(0.01, 1.5)',
                             'gamma': 'scale, auto y 25 valores logspace(1e-5, 10)', 'búsqueda': '64 muestras aleatorias por fit interno'}
    (DEST / 'catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding='utf-8')

"""E3: datos reales, test temporal y selección anidada por estudiante.

No ejecuta ni modifica notebooks históricos. Los IDs solo se usan localmente.
"""
import hashlib
import json
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler
from sklearn.svm import LinearSVR
from statsmodels.stats.diagnostic import het_breuschpagan
import statsmodels.api as sm

BOOK = Path(__file__).resolve().parent
OUTPUT = BOOK / 'resultados/e3'
TARGET = 'nota_primer_parcial'
GROUP = 'estudiante'
PERIOD = 'periodo'
TEST_PERIOD = 202530
NUMERIC = ['Icfes_nuevo', 'Icfes_Matematicas',
           'Tiempo_empleado_en_la_verificación_de_conocimientos', 'Dominio_Inicial',
           'avance_precalculo_aleks', 'Dominio_Final', 'Tiempo_Total_Tiempo',
           'Tiempo_total_Aprendidos_hora']
CATEGORICAL = ['Categoria_temas_inicial', 'Categoria_temas_final', 'programa_en_matricula',
               'division_en_matricula', 'Mat_Curso_Asignatura_Relacionada',
               'avance_cuartiles', 'cumplimiento_temas']
FEATURES = NUMERIC + CATEGORICAL
GRID = {'modelo__C': [0.01, 0.03, 0.1, 0.3, 1.0, 10.0],
        'modelo__epsilon': [0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0]}
RAW_COLUMNS = ['Icfes nuevo', 'Icfes Matemáticas',
               'Tiempo empleado en la verificación de conocimientos',
               'Dominados (cantidad de temas)', 'avance precalculo aleks',
               'Progreso (cantidad de temas)', 'Tiempo Total Tiempo',
               'Tiempo total - Aprendidos/hora', 'Categoria temas inicial',
               'Categoria temas final', 'programa en matricula', 'division en matricula',
               'Mat Curso Asignatura Relacionada', 'avance cuartiles', 'cumplimiento temas']


def source_hashes():
    return {name: hashlib.sha256((BOOK / name).read_bytes()).hexdigest()
            for name in ['Data/Datos_Brutos.csv', 'cabeceras.csv', 'entregable3.py']}


def metrics(y, pred):
    return {'RMSE': float(np.sqrt(mean_squared_error(y, pred))),
            'MAE': float(mean_absolute_error(y, pred)),
            'MAPE (%)': float(100 * mean_absolute_percentage_error(y, pred)),
            'R²': float(r2_score(y, pred)) if len(y) > 1 and np.var(y) > 0 else None}


def business_violations(frame):
    initial, final = frame['Dominio_Inicial'], frame['Dominio_Final']
    return pd.DataFrame({
        'dominio': initial.notna() & final.notna() & final.lt(initial),
        'tiempo_cero': frame['Tiempo_Total_Tiempo'].eq(0) & ~final.eq(initial),
        'aprendidos_cero': frame['Tiempo_total_Aprendidos_hora'].eq(0) & ~final.eq(initial),
    }, index=frame.index)


def load_partitions():
    raw = pd.read_csv(BOOK / 'Data/Datos_Brutos.csv', sep=';', decimal=',', encoding='utf-8-sig')
    frame = raw[RAW_COLUMNS].copy()
    frame.columns = FEATURES
    frame[TARGET] = pd.to_numeric(raw['nota primer parcial'], errors='raise')
    frame[GROUP] = raw['pidm en matricula'].astype('string')
    frame[PERIOD] = pd.to_numeric(raw['Periodo'], errors='raise').astype(int)
    frame['fila_fuente'] = np.arange(len(raw))
    if frame[GROUP].isna().any() or frame[GROUP].str.strip().eq('').any():
        raise ValueError('Se necesita un ID persistente en todas las filas.')
    for c in NUMERIC:
        frame[c] = pd.to_numeric(frame[c], errors='raise')
    for c in CATEGORICAL:
        frame[c] = frame[c].astype(object).where(frame[c].notna(), np.nan)
    # Reservar estudiantes del periodo test incluso si alguna de sus notas falta.
    held_ids = set(frame.loc[frame[PERIOD].eq(TEST_PERIOD), GROUP])
    if not held_ids or frame[PERIOD].max() != TEST_PERIOD:
        raise ValueError('Revisar explícitamente TEST_PERIOD si cambia la fuente.')
    missing = frame[TARGET].isna()
    valid_target = frame.loc[~missing].copy()
    test_raw = valid_target.loc[valid_target[PERIOD].eq(TEST_PERIOD)]
    earlier = valid_target.loc[valid_target[PERIOD].lt(TEST_PERIOD)]
    purged = earlier[GROUP].isin(held_ids)
    train_raw = earlier.loc[~purged]
    train_rules, test_rules = business_violations(train_raw), business_violations(test_raw)
    train = train_raw.loc[~train_rules.any(axis=1)].reset_index(drop=True)
    test = test_raw.loc[~test_rules.any(axis=1)].reset_index(drop=True)
    assert not set(train[GROUP]) & set(test[GROUP])
    assert train[PERIOD].max() < test[PERIOD].min()
    audit = {
        'source_rows': len(raw), 'source_students': frame[GROUP].nunique(),
        'missing_target': int(missing.sum()), 'test_period': TEST_PERIOD,
        'train_periods': sorted(train[PERIOD].unique().tolist()),
        'purged_overlap_rows': int(purged.sum()), 'purged_overlap_students': earlier.loc[purged, GROUP].nunique(),
        'train_raw': len(train_raw), 'test_raw': len(test_raw),
        'excluded_train': int(train_rules.any(axis=1).sum()),
        'excluded_test': int(test_rules.any(axis=1).sum()),
        'rules_train': train_rules.sum().astype(int).to_dict(),
        'rules_test': test_rules.sum().astype(int).to_dict(),
        'train_valid': len(train), 'test_valid': len(test),
        'train_students': train[GROUP].nunique(), 'test_students': test[GROUP].nunique(),
        'shared_students': 0, 'outliers_removed': 0,
    }
    return train, test, audit


def make_pipeline(dummy=False):
    times = [c for c in NUMERIC if c.startswith('Tiempo')]
    plain = [c for c in NUMERIC if c not in times]
    preprocessor = ColumnTransformer([
        ('num_log', Pipeline([('imputer', SimpleImputer(strategy='median')),
                             ('log1p', FunctionTransformer(np.log1p, feature_names_out='one-to-one')),
                             ('scaler', StandardScaler())]), times),
        ('num_plain', Pipeline([('imputer', SimpleImputer(strategy='median')),
                               ('scaler', StandardScaler())]), plain),
        ('cat', Pipeline([('imputer', SimpleImputer(strategy='most_frequent')),
                          ('onehot', OneHotEncoder(handle_unknown='ignore', drop='first', sparse_output=False))]), CATEGORICAL),
    ])
    model = DummyRegressor(strategy='mean') if dummy else LinearSVR(
        loss='epsilon_insensitive', max_iter=1000000, random_state=42, tol=1e-4)
    return Pipeline([('preprocesamiento', preprocessor), ('modelo', model)])


def grouped_splits(frame, n_splits=5):
    splits = list(GroupKFold(n_splits=n_splits).split(frame[FEATURES], frame[TARGET], frame[GROUP]))
    for fit, val in splits:
        assert not set(frame.iloc[fit][GROUP]) & set(frame.iloc[val][GROUP])
    return splits


def tune(frame):
    search = GridSearchCV(make_pipeline(), GRID, scoring='neg_root_mean_squared_error',
                          cv=grouped_splits(frame), refit=True, n_jobs=4, error_score='raise')
    with warnings.catch_warnings():
        warnings.simplefilter('error', ConvergenceWarning)
        warnings.filterwarnings('ignore', message='Found unknown categories', category=UserWarning)
        with joblib.parallel_backend('loky', inner_max_num_threads=1):
            search.fit(frame[FEATURES], frame[TARGET])
    return search


def write_json(path, payload):
    # JSON estricto, sin NaN que puedan romper clientes.
    def clean(obj):
        if isinstance(obj, dict): return {k: clean(v) for k, v in obj.items()}
        if isinstance(obj, list): return [clean(v) for v in obj]
        if isinstance(obj, np.generic): return clean(obj.item())
        if isinstance(obj, float) and not np.isfinite(obj): return None
        return obj
    path.write_text(json.dumps(clean(payload), ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def run():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    train, test, audit = load_partitions()
    print(json.dumps(audit, ensure_ascii=False), flush=True)
    folds, fold_audit, learning = [], [], []
    train['fold'] = 0
    train['svm'], train['dummy'] = np.nan, np.nan
    for fold, (fit, val) in enumerate(grouped_splits(train), 1):
        fit_frame, val_frame = train.iloc[fit], train.iloc[val]
        search = tune(fit_frame)
        for name, col, model in [('SVM lineal', 'svm', search.best_estimator_),
                                  ('Dummy media', 'dummy', make_pipeline(True).fit(fit_frame[FEATURES], fit_frame[TARGET]))]:
            pred = model.predict(val_frame[FEATURES])
            train.loc[val, col] = pred
            folds.append({'Modelo': name, 'Fold': fold, **metrics(val_frame[TARGET], pred)})
        train.loc[val, 'fold'] = fold
        fold_audit.append({'fold': fold, 'fit_rows': len(fit), 'validation_rows': len(val),
                           'fit_students': fit_frame[GROUP].nunique(), 'validation_students': val_frame[GROUP].nunique(),
                           'shared_students': 0, 'best_params': search.best_params_})
        # Curva con grupos completos y parámetros seleccionados exclusivamente en el subconjunto.
        ids = np.random.default_rng(42).permutation(fit_frame[GROUP].unique())
        for fraction in [.25, .5, .75, 1.0]:
            small = fit_frame.loc[fit_frame[GROUP].isin(ids[:max(5, int(len(ids)*fraction))])]
            model = search.best_estimator_ if fraction == 1 else tune(small).best_estimator_
            learning.append({'fraction': fraction, 'n': len(small),
                             'train': metrics(small[TARGET], model.predict(small[FEATURES]))['RMSE'],
                             'validation': metrics(val_frame[TARGET], model.predict(val_frame[FEATURES]))['RMSE']})
        print(f'GroupKFold externo {fold}/5: {search.best_params_}', flush=True)
    final = tune(train)
    joblib.dump(final.best_estimator_, OUTPUT / 'model.joblib')
    grid = pd.DataFrame(final.cv_results_)
    grid[['param_modelo__C', 'param_modelo__epsilon', 'mean_test_score', 'std_test_score', 'rank_test_score']].to_csv(OUTPUT / 'grid_search.csv', index=False)
    dummy = make_pipeline(True).fit(train[FEATURES], train[TARGET])
    test['svm'] = final.predict(test[FEATURES])
    test['dummy'] = dummy.predict(test[FEATURES])
    fold_frame = pd.DataFrame(folds)
    fold_frame.to_csv(OUTPUT / 'fold_metrics.csv', index=False)
    names = final.best_estimator_.named_steps['preprocesamiento'].get_feature_names_out()
    pd.DataFrame({'Variable': names, 'Coeficiente': final.best_estimator_.named_steps['modelo'].coef_}).to_csv(OUTPUT / 'coefficients.csv', index=False)
    # Datos derivados del dashboard: sin IDs, nombres, correos ni nota_final.
    for label, frame in [('train', train), ('test', test)]:
        frame.drop(columns=[GROUP, 'fila_fuente']).to_csv(OUTPUT / f'{label}.csv.gz', index=False, compression='gzip')
    bootstrap, residuals, tests, cv = [], [], [], []
    positions = [np.flatnonzero(test[GROUP].eq(g).to_numpy()) for g in test[GROUP].unique()]
    for name, col in [('SVM lineal', 'svm'), ('Dummy media', 'dummy')]:
        score = metrics(test[TARGET], test[col])
        tests.append({'modelo': name, 'RMSE': score['RMSE'], 'MAE': score['MAE'], 'MAPE_%': score['MAPE (%)'], 'R2': score['R²']})
        for metric, saved in [('RMSE', 'RMSE'), ('MAE', 'MAE'), ('MAPE (%)', 'MAPE'), ('R²', 'R2')]:
            values = fold_frame.loc[fold_frame.Modelo.eq(name), metric]
            cv.append({'modelo': name, 'metrica': saved, 'media_cv': values.mean(), 'sd_cv': values.std(ddof=0)})
        rng = np.random.default_rng(42)
        draws = []
        for _ in range(1000):
            ix = np.concatenate([positions[i] for i in rng.integers(0, len(positions), len(positions))])
            draws.append(metrics(test.iloc[ix][TARGET], test.iloc[ix][col]))
        for metric, saved in [('RMSE', 'RMSE'), ('MAPE (%)', 'MAPE_%'), ('R²', 'R2')]:
            values = [d[metric] for d in draws if d[metric] is not None]
            lo, hi = np.quantile(values, [.025, .975])
            bootstrap.append({'modelo': name, 'metrica': saved, 'estimación': score[metric], 'IC_2.5%': lo, 'IC_97.5%': hi})
        resid = test[TARGET].to_numpy() - test[col].to_numpy()
        variable = np.ptp(test[col]) > 1e-12
        residuals.append({'modelo': name, 'media_residuo': resid.mean(),
                          'normaltest_p': stats.normaltest(resid).pvalue,
                          'Breusch_Pagan_p': het_breuschpagan(resid, sm.add_constant(test[col]))[3] if variable else None,
                          'Spearman_abs_resid_vs_ajustado': stats.spearmanr(abs(resid), test[col]).statistic if variable else None})
    learning_frame = pd.DataFrame(learning)
    learning_rows = [{'n_entrenamiento': int(g['n'].mean()), 'RMSE_train_media': g['train'].mean(),
                     'RMSE_validacion_media': g['validation'].mean()} for _, g in learning_frame.groupby('fraction')]
    source = source_hashes()
    report = {**audit, 'technique': 'datos_reales', 'source_sha256': source,
              'validation': 'GroupKFold anidado: 5 folds externos y 5 internos; test temporal purgado',
              'grid': GRID, 'best_params': final.best_params_, 'selection_rmse': -final.best_score_,
              'fold_audit': fold_audit, 'test': tests, 'cv': cv, 'bootstrap': bootstrap,
              'residuals': residuals, 'learning': learning_rows,
              'improvement': {'reducción_RMSE_vs_dummy_%': 100*(1-tests[0]['RMSE']/tests[1]['RMSE']),
                              'reducción_MAPE_vs_dummy_%': 100*(1-tests[0]['MAPE_%']/tests[1]['MAPE_%'])}}
    write_json(OUTPUT / 'modelos_lineales.json', report)
    write_json(OUTPUT / 'eda.json', {**audit, 'excluded': audit['excluded_train'],
                                    'technique': 'datos_reales', 'source_sha256': source,
                                    'missing_cells': int(train[FEATURES].isna().sum().sum()),
                                    'numeric_profile': train[NUMERIC+[TARGET]].describe().to_dict(),
                                    'correlation_spearman': train[NUMERIC+[TARGET]].corr(method='spearman').to_dict()})
    write_json(OUTPUT / 'particion.json', audit)
    print(json.dumps({'best_params': final.best_params_, 'test': tests}, ensure_ascii=False), flush=True)
    return report


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    run()

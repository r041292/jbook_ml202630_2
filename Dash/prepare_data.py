"""Copia y verifica los artefactos canónicos de E3; no reentrena."""
import hashlib
import json
import shutil
from pathlib import Path
from prepare_originals import source_paths, prepare_originals, FILES as ORIGINAL_FILES
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error, r2_score
ROOT = Path(__file__).resolve().parent
BOOK = ROOT.parent / 'Precalculo'
CACHE = ROOT / 'data'
RESULTS = BOOK / 'resultados/e3'
ACTIVE_POINTER = RESULTS / 'busqueda_activa.json'
ACTIVE_RESULTS = RESULTS
if ACTIVE_POINTER.exists():
    active = json.loads(ACTIVE_POINTER.read_text(encoding='utf-8'))
    ACTIVE_RESULTS = RESULTS / 'busquedas' / active['run_id']
    if not (ACTIVE_RESULTS / 'completo.json').is_file():
        raise RuntimeError('La búsqueda activa no está completa.')
CLASSIC_KEYS = ('knn', 'ridge', 'lasso', 'forest', 'xgboost', 'decision_tree')
STUDENT_ARTIFACT = 'clasicos/comparacion_svm_bootstrap.json'
CLASSIC_FILES = ['comparacion.json', 'fold_metrics.csv', 'train_predictions.csv.gz', 'test_predictions.csv.gz', 'xgboost.ubj'] + [
    name for key in CLASSIC_KEYS for name in (f'{key}.joblib', f'grid_{key}.csv')]
SOURCES = [BOOK / name for name in ['Data/Datos_Brutos.csv', 'cabeceras.csv', 'entregable3.py',
    '00_seleccion_base_datos.md', 'resultados/e3/modelos_lineales.json', 'resultados/e3/eda.json',
    'resultados/e3/particion.json', 'resultados/e3/grid_search.csv', 'resultados/e3/train.csv.gz',
    'resultados/e3/test.csv.gz', 'resultados/e3/fold_metrics.csv', 'resultados/e3/coefficients.csv',
    'resultados/e3/model.joblib']]
SOURCES += [BOOK / 'modelos_clasicos.py', BOOK / 'preprocesamiento_clasicos.py']
SOURCES += [BOOK / 'evaluar_decision_tree_e3.py']
SOURCES += [RESULTS / 'clasicos' / name for name in CLASSIC_FILES]
SOURCES += source_paths()
SOURCES += [BOOK / 'busquedas_hiperparametros_e3.py', BOOK / 'evaluar_busquedas_e3.py', BOOK / 'activar_busqueda_e3.py']
if ACTIVE_RESULTS != RESULTS:
    SOURCES += [ACTIVE_POINTER, ACTIVE_RESULTS / 'modelos_lineales.json', ACTIVE_RESULTS / 'protocolo.json',
                ACTIVE_RESULTS / 'seleccion_antes_test.json', ACTIVE_RESULTS / 'completo.json']
    SOURCES += [ACTIVE_RESULTS / name for name in ['train.csv.gz', 'test.csv.gz', 'fold_metrics.csv',
                 'coefficients.csv', 'model.joblib', 'grid_search.csv']]
    SOURCES += [ACTIVE_RESULTS / 'clasicos' / name for name in CLASSIC_FILES]

def hashes():
    return {p.relative_to(BOOK).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCES}

def metrics(y, pred):
    return {'RMSE': float(np.sqrt(mean_squared_error(y, pred))),
            'MAE': float(mean_absolute_error(y, pred)),
            'MAPE (%)': float(100 * mean_absolute_percentage_error(y, pred)),
            'R²': float(r2_score(y, pred)) if len(y) > 1 and np.var(y) > 0 else None}

def prepare():
    report = json.loads((ACTIVE_RESULTS / 'modelos_lineales.json').read_text(encoding='utf-8'))
    classics = json.loads((ACTIVE_RESULTS / 'clasicos/comparacion.json').read_text(encoding='utf-8'))
    for name, digest in {**report['source_sha256'], **classics['source_sha256']}.items():
        if hashlib.sha256((BOOK / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError('Reejecuta entregable3.py: cambió la fuente ' + name)
    CACHE.mkdir(exist_ok=True)
    for name in ['train.csv.gz', 'test.csv.gz', 'fold_metrics.csv', 'coefficients.csv', 'model.joblib', 'grid_search.csv']:
        shutil.copyfile(ACTIVE_RESULTS / name, CACHE / name)
    shutil.copyfile(ACTIVE_RESULTS / 'modelos_lineales.json', CACHE / 'svm_report.json')
    (CACHE / 'clasicos').mkdir(exist_ok=True)
    for name in CLASSIC_FILES:
        shutil.copyfile(ACTIVE_RESULTS / 'clasicos' / name, CACHE / 'clasicos' / name)
    shutil.copyfile(BOOK / 'preprocesamiento_clasicos.py', ROOT / 'preprocesamiento_clasicos.py')
    prepare_originals()
    from student_comparison import prepare as prepare_student_comparison
    prepare_student_comparison(CACHE, BOOK, ACTIVE_RESULTS)
    artifacts = [p for p in CACHE.glob('*') if p.name in ['train.csv.gz', 'test.csv.gz', 'fold_metrics.csv',
                 'coefficients.csv', 'model.joblib', 'grid_search.csv']] + [CACHE / 'clasicos' / name for name in CLASSIC_FILES]
    artifacts += [CACHE / 'originales' / name for name in ORIGINAL_FILES] + [CACHE / 'svm_report.json']
    artifacts += [CACHE / STUDENT_ARTIFACT]
    (CACHE / 'manifest.json').write_text(json.dumps({
        'sha256': hashes(), 'train_valid': report['train_valid'], 'test_valid': report['test_valid'],
        'technique': 'datos_reales', 'test_period': report['test_period'], 'best_params': report['best_params'],
        'model_sha256': hashlib.sha256((CACHE / 'model.joblib').read_bytes()).hexdigest(),
        'method': report['validation'],
        'active_search': report.get('run_id'),
        'artifact_sha256': {p.relative_to(CACHE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts},
    }, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Dashboard sincronizado con E3.')

if __name__ == '__main__':
    prepare()

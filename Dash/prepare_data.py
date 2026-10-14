"""Copia y verifica los artefactos canónicos de E3; no reentrena."""
import hashlib
import json
import shutil
from pathlib import Path
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error, r2_score
ROOT = Path(__file__).resolve().parent
BOOK = ROOT.parent / 'Precalculo'
CACHE = ROOT / 'data'
RESULTS = BOOK / 'resultados/e3'
SOURCES = [BOOK / name for name in ['Data/Datos_Brutos.csv', 'cabeceras.csv', 'entregable3.py',
    '00_seleccion_base_datos.md', 'resultados/e3/modelos_lineales.json', 'resultados/e3/eda.json',
    'resultados/e3/particion.json', 'resultados/e3/grid_search.csv', 'resultados/e3/train.csv.gz',
    'resultados/e3/test.csv.gz', 'resultados/e3/fold_metrics.csv', 'resultados/e3/coefficients.csv',
    'resultados/e3/model.joblib']]

def hashes():
    return {p.relative_to(BOOK).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCES}

def metrics(y, pred):
    return {'RMSE': float(np.sqrt(mean_squared_error(y, pred))),
            'MAE': float(mean_absolute_error(y, pred)),
            'MAPE (%)': float(100 * mean_absolute_percentage_error(y, pred)),
            'R²': float(r2_score(y, pred)) if len(y) > 1 and np.var(y) > 0 else None}

def prepare():
    report = json.loads((RESULTS / 'modelos_lineales.json').read_text(encoding='utf-8'))
    for name, digest in report['source_sha256'].items():
        if hashlib.sha256((BOOK / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError('Reejecuta entregable3.py: cambió la fuente ' + name)
    CACHE.mkdir(exist_ok=True)
    for name in ['train.csv.gz', 'test.csv.gz', 'fold_metrics.csv', 'coefficients.csv', 'model.joblib', 'grid_search.csv']:
        shutil.copyfile(RESULTS / name, CACHE / name)
    (CACHE / 'manifest.json').write_text(json.dumps({
        'sha256': hashes(), 'train_valid': report['train_valid'], 'test_valid': report['test_valid'],
        'technique': 'datos_reales', 'test_period': report['test_period'], 'best_params': report['best_params'],
        'model_sha256': hashlib.sha256((CACHE / 'model.joblib').read_bytes()).hexdigest(),
        'method': report['validation'],
    }, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Dashboard sincronizado con E3.')

if __name__ == '__main__':
    prepare()

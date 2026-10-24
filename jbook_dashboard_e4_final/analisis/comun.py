"""Carga común de resultados ya guardados para los análisis del libro E4.

Nada de este módulo entrena, busca hiperparámetros ni ejecuta `predict`: solo lee
predicciones fuera del fold (OOF), métricas por fold y eventos de tiempo ya registrados.
Los identificadores de estudiante se usan en memoria para agrupar y nunca se exportan.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / 'salidas'
IMAGES = HERE.parent / 'images' / 'e4'
PRECALCULO = ROOT / 'Precalculo'
DASH = ROOT / 'Dash'
RESULTS = PRECALCULO / 'resultados' / 'e3'
RUN_BASE = RESULTS / 'busquedas' / '20261018_102325_af643f83'
RUN_ORIG = RESULTS / 'originales_busquedas' / '20261020_153034_consolidada'
EVENTS_BASE = ROOT / 'tiempos' / '20261018_102325_af643f83' / 'eventos.jsonl'
OLD_BOOK = ROOT / 'jbook_dashboard'
SEED = 42

for path in (PRECALCULO, DASH):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# Los siete modelos base (benchmarks) en el orden del capítulo 3 y los tres originales.
BASE = {'svm': 'SVM lineal', 'knn': 'KNN', 'ridge': 'Ridge', 'lasso': 'Lasso',
        'forest': 'Random Forest', 'xgboost': 'XGBoost', 'decision_tree': 'Decision Tree'}
ORIGINAL = {'m5': 'KRR centrado', 'm19': 'TN-KRR', 'm15': 'GPR–XGBoost'}
# Nombres con que cada modelo aparece en los CSV de métricas por fold.
FOLD_NAMES = {**{k: v for k, v in BASE.items()}, 'm5': 'Kernel Ridge RBF',
              'm19': 'Truncated Newton KRR RBF', 'm15': 'GPR–XGBoost (OOF agrupado)'}
LABELS = {**BASE, **ORIGINAL}


def partitions():
    """Train y test válidos de `entregable3.load_partitions` (fuente privada, solo local)."""
    from entregable3 import load_partitions
    train, test, _ = load_partitions()
    return train, test


def oof_predictions():
    """OOF de los 7 base y de los 3 originales, en el orden de filas de train."""
    base = pd.read_csv(DASH / 'data' / 'clasicos' / 'train_predictions.csv.gz')
    orig = pd.read_csv(DASH / 'data' / 'originales' / 'train.csv.gz')
    if not (base['fold'].to_numpy() == orig['fold'].to_numpy()).all():
        raise ValueError('Los folds de clásicos y originales no coinciden fila a fila.')
    frame = pd.concat([base[['fold', *BASE]], orig[list(ORIGINAL)]], axis=1)
    return frame


def test_predictions():
    base = pd.read_csv(DASH / 'data' / 'clasicos' / 'test_predictions.csv.gz')
    orig = pd.read_csv(DASH / 'data' / 'originales' / 'test.csv.gz')
    return pd.concat([base[list(BASE)], orig[list(ORIGINAL)]], axis=1)


def fold_metrics():
    """Métricas por fold externo (RMSE, MAE, R²) tal como se guardaron en cada ejecución."""
    base = pd.read_csv(RUN_BASE / 'clasicos' / 'fold_metrics.csv')
    orig = pd.read_csv(DASH / 'data' / 'originales' / 'folds.csv')
    names = {v: k for k, v in FOLD_NAMES.items()}
    frame = pd.concat([base.loc[base.Modelo.isin(BASE.values())],
                       orig.loc[orig.Modelo.isin([FOLD_NAMES[k] for k in ORIGINAL])]])
    frame = frame.assign(clave=frame.Modelo.map(names))
    return frame[['clave', 'Fold', 'RMSE', 'MAE', 'R²']].reset_index(drop=True)


def gpr_solo_oof(train):
    """OOF del GPR solo (ablación) registrado por la ejecución histórica `resultados/e3/gpr_xgb/`."""
    parts = pd.concat([pd.read_csv(RESULTS / 'gpr_xgb' / f'oof_{k}.csv.gz') for k in range(1, 6)])
    aligned = train[['fila_fuente']].merge(parts[['fila_fuente', 'fold', 'gpr_solo_prediccion', 'prediccion']],
                                           on='fila_fuente', how='left', validate='one_to_one')
    if aligned['gpr_solo_prediccion'].isna().any():
        raise ValueError('Faltan predicciones OOF del GPR solo para alguna fila de train.')
    return aligned


def timing_events():
    return [json.loads(line) for line in EVENTS_BASE.read_text(encoding='utf-8').splitlines() if line.strip()]


def rmse(y, p):
    return float(np.sqrt(np.mean((np.asarray(y, float) - np.asarray(p, float)) ** 2)))

"""GPR→XGBoost para la búsqueda anidada: solo se buscan hiperparámetros de XGBoost.

El kernel GPR y sus reinicios quedan fijos (como en evaluar_gpr_xgb_e3.py). La
etapa GPR (media/desviación OOF por estudiante y kernel optimizado) no depende de
los hiperparámetros de XGBoost, así que se calcula una vez por conjunto de ajuste
y se reutiliza entre candidatos. La caché se indexa por el contenido exacto
(X crudo, y, grupos): un candidato nunca ve información de su fold de validación.
Los segundos de cada cómputo GPR se registran aparte en `gpr_stage_log.jsonl`
para no atribuirlos solo al primer candidato.
"""
import hashlib
import json
import os
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.exceptions import ConvergenceWarning
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits
from xgboost import XGBRegressor

from entregable3 import OUTPUT
import evaluar_gpr_xgb_e3 as reference

CACHE_DIR = OUTPUT / 'gpr_xgb_hpo' / 'cache_gpr'
STAGE_LOG = CACHE_DIR / 'gpr_stage_log.jsonl'
GPR_RESTARTS = 5   # Apéndice B.1 del artículo: «multiple random restarts» (el histórico usaba 1)
STAGE_VERSION = f'gpr-stage-v3 (prep por fold GPR); Constant*(Matern2.5+RBF)+White; restarts={GPR_RESTARTS}; normalize_y; GroupKFold5'
# Valores históricos fijos; solo estos cuatro se buscan.
SEARCHED = ('n_estimators', 'learning_rate', 'max_leaves', 'reg_lambda')
GRID = {'modelo__n_estimators': [300, 600, 1000], 'modelo__learning_rate': [.005, .01, .03],
        'modelo__max_leaves': [7, 15, 31], 'modelo__reg_lambda': [1., 10.]}
SPACE = {'modelo__n_estimators': ('int', 200, 1200), 'modelo__learning_rate': ('log', .003, .1),
         'modelo__max_leaves': ('int', 4, 63), 'modelo__reg_lambda': ('log', .1, 50.)}


def _dense(values):
    return reference._dense(values)


def _preprocessor():
    return reference._preprocessor()


def _new_gpr():
    """Mismo kernel C·(Matérn 2.5 + RBF) + White de B.1, con más reinicios del optimizador."""
    return clone(reference._new_gpr()).set_params(n_restarts_optimizer=GPR_RESTARTS)


def _cache_key(X, y, groups):
    digest = hashlib.sha256(STAGE_VERSION.encode())
    digest.update(pd.util.hash_pandas_object(X, index=False).to_numpy().tobytes())
    digest.update(np.ascontiguousarray(y, dtype=np.float64).tobytes())
    digest.update('|'.join(map(str, groups)).encode())
    return digest.hexdigest()


def _compute_stage(X, y, groups):
    """Cross-fit idéntico a evaluar_gpr_xgb_e3: el preprocesamiento se reajusta en cada fold GPR."""
    mean_oof, std_oof = np.full(len(y), np.nan), np.full(len(y), np.nan)
    started = time.perf_counter()
    with warnings.catch_warnings(), threadpool_limits(limits=1):
        warnings.filterwarnings('ignore', category=ConvergenceWarning)
        warnings.filterwarnings('ignore', message='Found unknown categories')
        for fit, val in GroupKFold(n_splits=reference.INNER_FOLDS).split(X, y, groups):
            prep = _preprocessor()
            z_fit, z_val = _dense(prep.fit_transform(X.iloc[fit])), _dense(prep.transform(X.iloc[val]))
            gpr = _new_gpr().fit(z_fit, y[fit])
            mean_oof[val], std_oof[val] = gpr.predict(z_val, return_std=True)
        kernel = _new_gpr().fit(_dense(_preprocessor().fit_transform(X)), y).kernel_
    if not np.isfinite(mean_oof).all() or not np.isfinite(std_oof).all() or (std_oof < 0).any():
        raise ValueError('GPR produjo medias o incertidumbres inválidas.')
    return {'mean_oof': mean_oof, 'std_oof': std_oof, 'kernel': kernel,
            'seconds': time.perf_counter() - started}


def gpr_stage(X, y, groups, cache_dir=None):
    cache_dir = Path(cache_dir or CACHE_DIR)
    key = _cache_key(X, y, groups)
    path = cache_dir / f'{key}.joblib'
    if path.exists():
        try:
            return {**joblib.load(path), 'cache_hit': True}
        except Exception:  # archivo truncado por un proceso interrumpido
            path.unlink(missing_ok=True)
    entry = _compute_stage(X, y, groups)
    cache_dir.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f'.{os.getpid()}.tmp')
    joblib.dump(entry, temporary)
    os.replace(temporary, path)
    with (cache_dir / STAGE_LOG.name).open('a', encoding='utf-8') as stream:
        stream.write(json.dumps({'key': key, 'rows': int(len(y)), 'seconds': entry['seconds'],
                                 'clock': time.strftime('%Y-%m-%dT%H:%M:%S%z')}) + '\n')
    return {**entry, 'cache_hit': False}


class GPRStackXGBRegressor(RegressorMixin, BaseEstimator):
    """Stack GPR→XGBoost: XGBoost aprende y−ŷ_GPR con Z, media y SD de GPR."""

    def __init__(self, n_estimators=1000, learning_rate=.01, max_leaves=31, reg_lambda=1.,
                 subsample=.8, colsample_bytree=.8, reg_alpha=1., random_state=reference.SEED):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_leaves = max_leaves
        self.reg_lambda = reg_lambda
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.reg_alpha = reg_alpha
        self.random_state = random_state

    def fit(self, X, y, groups=None):
        if groups is None:
            raise ValueError('GPRStackXGBRegressor necesita groups (estudiante) para el cross-fit GPR.')
        X = X.reset_index(drop=True)
        y, groups = np.asarray(y, dtype=np.float64).reshape(-1), np.asarray(groups)
        stage = gpr_stage(X, y, groups)
        self.gpr_stage_cache_hit_, self.gpr_stage_seconds_ = stage['cache_hit'], stage['seconds']
        self.prep_ = _preprocessor()
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', message='Found unknown categories')
            Z = _dense(self.prep_.fit_transform(X))
        self.gpr_ = GaussianProcessRegressor(kernel=stage['kernel'], alpha=1e-8, normalize_y=True,
                                             optimizer=None, copy_X_train=False).fit(Z, y)
        params = {**reference.XGB_PARAMS, 'n_estimators': self.n_estimators,
                  'learning_rate': self.learning_rate, 'max_leaves': self.max_leaves,
                  'reg_lambda': self.reg_lambda, 'subsample': self.subsample,
                  'colsample_bytree': self.colsample_bytree, 'reg_alpha': self.reg_alpha,
                  'random_state': self.random_state, 'n_jobs': 1}
        stack = np.column_stack([Z, stage['mean_oof'], stage['std_oof']])
        self.xgb_ = XGBRegressor(**params).fit(stack, y - stage['mean_oof'])
        self.n_features_in_ = X.shape[1]
        return self

    def predict(self, X):
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', message='Found unknown categories')
            Z = _dense(self.prep_.transform(X))
        mean, std = self.gpr_.predict(Z, return_std=True)
        return mean + self.xgb_.predict(np.column_stack([Z, mean, std]))


def make_model():
    """Pipeline de un solo paso: el preprocesamiento vive dentro del estimador (se reajusta por fold GPR)."""
    return Pipeline([('modelo', GPRStackXGBRegressor())])

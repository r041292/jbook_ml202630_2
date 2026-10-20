"""TCR-XGBoost: robustez y ponderación aprendidas exclusivamente en fit."""
import numpy as np
from scipy.spatial.distance import cdist
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.preprocessing import MinMaxScaler
from sklearn.utils.validation import check_is_fitted

from entregable3 import FEATURES, make_pipeline
from modelos_clasicos import classic_pipeline

REFERENCE = {'paper': 'https://doi.org/10.1007/s10994-024-06704-x',
             'repository': 'https://github.com/montymaxzuehlke/tcr',
             'commit': 'b73caef801b002569dbb95fbb7b229f08e0a78c2'}
GRID = [{'fraction': [0.], 'weight': [1.]},
        {'fraction': [.05, .10, .20], 'weight': [.3, .6, .9]}]


def robustness(X, y, epsilon=1e-7):
    """r_i=1/(1+max_j |y_i-y_j|/(||x_i-x_j||_2+epsilon)), y en[0,1]."""
    X, y = np.asarray(X, float), np.asarray(y, float)
    target_range = np.ptp(y)
    if target_range == 0:
        return np.ones(len(y))
    y = (y-y.min())/target_range
    values = np.empty(len(y))
    for start in range(0, len(y), 128):
        distances = cdist(X[start:start+128], X, metric='euclidean')
        variation = np.abs(y[start:start+128, None]-y[None, :])
        sensitivity = (variation/(distances+epsilon)).max(axis=1)
        values[start:start+len(sensitivity)] = 1/(1+sensitivity)
    return values


def positive_weights(values, fraction, weight):
    if not 0 <= fraction < 1 or not 0 < weight <= 1:
        raise ValueError('TCR requiere fraction en[0,1) y weight en(0,1].')
    output = np.ones(len(values))
    n = int(fraction*len(values))
    output[np.argsort(values, kind='stable')[:n]] = weight
    return output


# Búsqueda conjunta (protocolo nuevo): TCR más tres hiperparámetros del XGBoost base.
# Grid grueso: (1 + 9) combinaciones TCR x 8 de XGBoost = 80 candidatos.
_XGB_GRID = {'n_estimators': [200, 450], 'max_depth': [2, 4], 'learning_rate': [.015, .06]}
JOINT_GRID = [{'fraction': [0.], 'weight': [1.], **_XGB_GRID},
              {'fraction': [.05, .10, .20], 'weight': [.3, .6, .9], **_XGB_GRID}]
JOINT_SPACE = {'fraction': ('cat', [0., .05, .10, .20]), 'weight': ('cat', [.3, .6, .9, 1.]),
               'n_estimators': ('int', 150, 500), 'max_depth': ('int', 1, 6),
               'learning_rate': ('log', .01, .1)}


class TCRXGBRegressor(RegressorMixin, BaseEstimator):
    """n_estimators/max_depth/learning_rate (si no son None) sustituyen a base_params del XGBoost."""

    def __init__(self, fraction=.1, weight=.6, base_params=None,
                 n_estimators=None, max_depth=None, learning_rate=None):
        self.fraction = fraction
        self.weight = weight
        self.base_params = base_params
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate

    def fit(self, X, y):
        self.distance_preprocessor_ = clone(make_pipeline().named_steps['preprocesamiento'])
        Z = self.distance_preprocessor_.fit_transform(X[FEATURES])
        self.distance_scaler_ = MinMaxScaler().fit(Z)
        self.robustness_ = robustness(self.distance_scaler_.transform(Z), y)
        self.sample_weights_ = positive_weights(self.robustness_, self.fraction, self.weight)
        overrides = {'modelo__'+name: value for name, value in (
            ('n_estimators', self.n_estimators), ('max_depth', self.max_depth),
            ('learning_rate', self.learning_rate)) if value is not None}
        self.pipeline_ = classic_pipeline('xgboost').set_params(**{**(self.base_params or {}), **overrides})
        self.pipeline_.fit(X[FEATURES], y, modelo__sample_weight=self.sample_weights_)
        self.n_features_in_ = len(FEATURES)
        return self

    def predict(self, X):
        check_is_fitted(self, 'pipeline_')
        return self.pipeline_.predict(X[FEATURES])

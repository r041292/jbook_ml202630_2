"""Cuatro familias Scopus: adaptadores locales, sin modificar fuentes/autores."""
import sys
from pathlib import Path

import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin, TransformerMixin, clone
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.impute import SimpleImputer
from sklearn.kernel_ridge import KernelRidge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder, StandardScaler

from entregable3 import BOOK, NUMERIC, CATEGORICAL, make_pipeline

VENDOR = BOOK/'terceros/wPILOT'
sys.path.insert(0, str(VENDOR)) if str(VENDOR) not in sys.path else None
LABELS = {'xbart':'XBART (GFR)', 'catboost':'CatBoost', 'kernel_ridge':'Kernel Ridge RBF', 'copilot':'coPILOT'}
GRIDS = {
    'xbart': {'trees':[50,150], 'depth':[2,4], 'leaf':[10,30]},
    'catboost': {'iterations':[300,600], 'depth':[2,4,6], 'learning_rate':[.03,.1], 'l2_leaf_reg':[3.,10.]},
    'kernel_ridge': {'alpha':[.01,.1,1.,10.,100.], 'gamma':[.001,.003,.01,.03,.1,.3,1.]},
    'copilot': {'depth':[2,4,6], 'leaf':[10,30], 'alpha':[.2,.5,1.]},
}
REFERENCES = {
    'xbart': {'paper':'https://doi.org/10.1080/01621459.2021.1942012',
        'implementation':'stochtree==0.4.5; BARTModel, GFR puro, sin MCMC',
        'fixed':{'num_gfr':60, 'discard_first':20, 'seed':42, 'sample_sigma2_leaf':True},
        'difference':'Implementación GFR de stochtree, no binario original JingyuHe/XBART; hiperparámetros propios.'},
    'catboost': {'paper':'https://proceedings.neurips.cc/paper/2018/hash/14491b756b3a51daac41c24863285549-Abstract.html',
        'implementation':'catboost==1.2.10, CatBoostRegressor, boosting_type=Ordered',
        'fixed':{'loss_function':'RMSE','random_seed':42,'thread_count':1,'allow_writing_files':False}},
    'kernel_ridge': {'paper':'https://doi.org/10.3390/app12094252',
        'implementation':'sklearn KernelRidge RBF, objetivo centrado dentro de cada fit',
        'difference':'Solución exacta de KRR; no se reproduce el optimizador Truncated Newton del artículo.'},
    'copilot': {'paper':'https://doi.org/10.1007/s11634-026-00683-8',
        'repository':'https://github.com/STAN-UAntwerp/wPILOT',
        'commit':'4ae908f4f1bd9ec93f1eeaebde958d6dd7ec5943',
        'fixed':{'max_n_estimators':2,'stop_early':False,'prediction_method':'Average'},
        'difference':'Código original sin cambios; conserva truncación interna y conversión de grados BIC a enteros.'},
}


class CatTypes(TransformerMixin, BaseEstimator):
    """Tipos nominales explícitos; imputadores previos se aprenden dentro del fold."""
    def fit(self, X, y=None):
        self.n_features_in_ = X.shape[1]
        return self

    def transform(self, X):
        X = X.copy()
        for col in X.columns[:len(NUMERIC)]:
            X[col] = X[col].astype(float)
        for col in X.columns[len(NUMERIC):]:
            X[col] = X[col].astype(str)
        return X


class CatBoostE3Regressor(RegressorMixin, BaseEstimator):
    """Evita la incompatibilidad de clone(cat_features) de CatBoost/sklearn1.9."""
    def __init__(self, iterations=300, depth=4, learning_rate=.03, l2_leaf_reg=3.):
        self.iterations,self.depth = iterations,depth
        self.learning_rate,self.l2_leaf_reg = learning_rate,l2_leaf_reg

    def fit(self, X, y):
        from catboost import CatBoostRegressor
        self.model_ = CatBoostRegressor(**self.get_params(),**REFERENCES['catboost']['fixed'],
            boosting_type='Ordered',cat_features=list(range(len(NUMERIC),15)),verbose=False)
        self.model_.fit(X,y)
        self.n_features_in_ = X.shape[1]
        return self

    def predict(self, X):
        return self.model_.predict(X)


class XBARTRegressor(RegressorMixin, BaseEstimator):
    """XBART como GFR standalone, según la API documentada de stochtree."""
    def __init__(self, trees=50, depth=2, leaf=10):
        self.trees, self.depth, self.leaf = trees, depth, leaf

    def fit(self, X, y):
        from stochtree import BARTModel
        self.model_ = BARTModel()
        self.model_.sample(X_train=np.asarray(X, dtype=float), y_train=np.asarray(y,dtype=float),
            num_gfr=60, num_burnin=0, num_mcmc=0,
            general_params={'random_seed':42, 'num_threads':1, 'keep_gfr':True},
            mean_forest_params={'num_trees':self.trees,'max_depth':self.depth,
                                'min_samples_leaf':self.leaf,'sample_sigma2_leaf':True})
        self.n_features_in_ = X.shape[1]
        return self

    def predict(self, X):
        draws = self.model_.predict(np.asarray(X,dtype=float),terms='y_hat',type='posterior')
        return np.asarray(draws)[:,20:].mean(axis=1)

    def __getstate__(self):
        state = self.__dict__.copy()
        if 'model_' in state:
            state['model_json_'] = state.pop('model_').to_json()
        return state

    def __setstate__(self, state):
        from stochtree import BARTModel
        self.__dict__.update(state)
        if 'model_json_' in state:
            self.model_ = BARTModel()
            self.model_.from_json(self.__dict__.pop('model_json_'))


class CoPILOTRegressor(RegressorMixin, BaseEstimator):
    """Interfaz sklearn sobre el algoritmo de los autores; dos árboles promediados."""
    def __init__(self, depth=4, leaf=10, alpha=1.):
        self.depth, self.leaf, self.alpha = depth, leaf, alpha

    def fit(self, X, y):
        import numba
        numba.set_num_threads(1)
        from pilot.copilot import coPILOT
        self.model_ = coPILOT(max_n_estimators=2,max_depth=self.depth,max_model_depth=30,
            min_sample_leaf=self.leaf,min_sample_split=2*self.leaf,alpha=self.alpha,random_state=42)
        self.model_.fit(np.asarray(X,dtype=float),np.asarray(y,dtype=float),
            categorical=np.arange(len(NUMERIC),len(NUMERIC)+len(CATEGORICAL),dtype=np.int64),
            stop_early=False)
        self.n_features_in_ = X.shape[1]
        return self

    def predict(self, X):
        return self.model_.predict(np.asarray(X,dtype=float),method='Average')


def make_model(key, **params):
    canonical = clone(make_pipeline().named_steps['preprocesamiento'])
    if key == 'kernel_ridge':
        # KRR no incorpora intercepto: centrar y en fit evita penalizar el nivel medio.
        model = TransformedTargetRegressor(regressor=KernelRidge(kernel='rbf',**params),
                                            transformer=StandardScaler(with_std=False))
        prep = canonical
    elif key == 'xbart':
        model, prep = XBARTRegressor(**params), canonical
    elif key == 'copilot':
        prep = ColumnTransformer([
            ('num',SimpleImputer(strategy='median'),NUMERIC),
            ('cat',Pipeline([('imputer',SimpleImputer(strategy='most_frequent')),
                ('ordinal',OrdinalEncoder(handle_unknown='use_encoded_value',unknown_value=-1))]),CATEGORICAL)])
        model = CoPILOTRegressor(**params)
    elif key == 'catboost':
        impute = ColumnTransformer([('num',SimpleImputer(strategy='median'),NUMERIC),
            ('cat',SimpleImputer(strategy='most_frequent'),CATEGORICAL)]).set_output(transform='pandas')
        prep = Pipeline([('impute',impute),('types',CatTypes())])
        model = CatBoostE3Regressor(**params)
    else:
        raise KeyError(key)
    return Pipeline([('preprocesamiento',prep),('modelo',model)])

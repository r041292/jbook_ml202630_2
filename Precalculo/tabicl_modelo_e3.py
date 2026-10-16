"""TabICLv2 oficial, configuración prefijada local y preparación común a SVM."""
import json
import os

import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.pipeline import Pipeline
from sklearn.utils.validation import check_is_fitted

from entregable3 import BOOK, make_pipeline
from finetune_tabpfn25_e3 import sha256

MODEL_DIR = BOOK/'modelos_preentrenados/tabicl_v2'
CHECKPOINT = 'tabicl-regressor-v2-20260212.ckpt'
REFERENCE = {'paper': 'https://proceedings.mlr.press/v306/qu26a.html',
    'repository':'https://github.com/soda-inria/tabicl', 'package':'tabicl==2.2.0',
    'model_revision':'4dcd344ece2c00be9e831fdd35bed57b5ad83e19',
    'checkpoint':CHECKPOINT,'sha256':'0db9cb538f114e79026bf08f45f41ad8dd7ad2de2aaca9a5ca8cd3bd9748ae7a',
    'configuration':'8 estimadores, CPU4 hilos, batch1, norm_methods=[none], '
                    'outlier_threshold=infinity, sin fine-tuning ni nuevos registros'}
GRID = [{}]


def new_estimator():
    os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
    from tabicl import TabICLRegressor
    path=MODEL_DIR/CHECKPOINT
    if not path.exists() or sha256(path)!=REFERENCE['sha256']:
        raise ValueError('Falta o cambió el checkpoint oficial TabICLv2 de regresión.')
    offload=MODEL_DIR/'offload'
    offload.mkdir(parents=True,exist_ok=True)
    return TabICLRegressor(model_path=str(path),checkpoint_version=CHECKPOINT,
        allow_auto_download=False,n_estimators=8,norm_methods=['none'],
        outlier_threshold=float('inf'),batch_size=1,device='cpu',n_jobs=4,
        kv_cache=False,offload_mode='auto',disk_offload_dir=str(offload),random_state=42,verbose=False)


class LocalTabICLRegressor(RegressorMixin,BaseEstimator):
    """Pickle ligero: conserva contexto; los pesos se recargan del checkpoint local."""
    def fit(self,X,y):
        self.context_X_=np.asarray(X,dtype=float).copy()
        self.context_y_=np.asarray(y,dtype=float).copy()
        self.model_=new_estimator()
        self.model_.fit(self.context_X_,self.context_y_)
        self.n_features_in_=self.context_X_.shape[1]
        return self

    def predict(self,X):
        check_is_fitted(self,'model_')
        return np.asarray(self.model_.predict(np.asarray(X,dtype=float)),dtype=float)

    def __getstate__(self):
        state=dict(self.__dict__)
        state.pop('model_',None)
        return state

    def __setstate__(self,state):
        self.__dict__.update(state)
        if 'context_X_' in state:
            self.model_=new_estimator().fit(self.context_X_,self.context_y_)


def make_model():
    return Pipeline([('preprocesamiento',clone(make_pipeline().named_steps['preprocesamiento'])),
                     ('modelo',LocalTabICLRegressor())])

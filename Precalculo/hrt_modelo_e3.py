"""HRT-Boost oficial en un pipeline con preparación canónica E3."""
from sklearn.base import clone
from sklearn.pipeline import Pipeline

from entregable3 import make_pipeline

REFERENCE = {'paper':'https://arxiv.org/abs/2605.23422',
    'repository':'https://github.com/Hongyi-Li-sz/HRT-Boost',
    'commit':'ed3885d7e089e489415637556b818d0284b123a6','package':'hrt-boost==0.1.0',
    'fixed':{'learning_rate':.1,'min_points':80,'step_size':'auto','random_state':42}}
GRID = {'n_estimators':[10,30],'max_depth':[1,2],'ridge_alpha':[1.,10.,100.]}


def make_model(n_estimators=30,max_depth=2,ridge_alpha=10.):
    from hrt_boost import HRTBoostingRegressor
    model=HRTBoostingRegressor(n_estimators=n_estimators,max_depth=max_depth,
        ridge_alpha=ridge_alpha,**REFERENCE['fixed'])
    return Pipeline([('preprocesamiento',clone(make_pipeline().named_steps['preprocesamiento'])),
                     ('modelo',model)])

"""Registro ampliable de búsquedas Originales; no modifica el motor histórico.

Por defecto solo m0/m5/m19. Los modelos costosos requieren selección explícita.
Los estimadores y sus transformaciones se clonan desde sus artefactos locales.
"""
import ast
import copy
import inspect
import json
import math
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
from sklearn.base import clone
from sklearn.model_selection import ParameterGrid
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits

import busquedas_hiperparametros_e3 as engine
from entregable3 import BOOK, FEATURES, GROUP, TARGET, grouped_splits, metrics

LOW_COST = ('m0', 'm5', 'm19')
FOLDERS = {'m0':'svr_rbf_raffle/svr_rbf', 'm3':'linxgboost',
           'm5':'scopus/kernel_ridge','m6':'scopus/catboost','m7':'tcr_xgboost',
           'm9':'xgboost_variantes/gbtree','m10':'svr_rbf_raffle/raffle',
           'm11':'xgboost_variantes/denseweight','m12':'xgboost_variantes/dart',
           'm13':'hrt_boost','m14':'logicdt','m16':'rim','m17':'scopus/xbart',
           'm15':'gpr_xgb_hpo','m18':'scopus/copilot','m19':'tn_krr'}
# Grid grueso (≤100 candidatos) para Grid Search; Random/TPE/DEAP/SH conservan el
# dominio histórico completo. Los valores históricos elegidos caben dentro de cada rango.
COARSE_GRIDS = {
    # 2^5 * 3 = 96 candidatos; weight_alpha=0 equivale a XGBoost sin ponderar
    'm11': {'modelo__n_estimators':[250,600], 'modelo__max_depth':[2,4], 'modelo__learning_rate':[.02,.08],
            'modelo__min_child_weight':[1,5], 'modelo__reg_lambda':[1.,10.], 'modelo__weight_alpha':[0.,.5,1.]},
}


def artifact_for(key):
    directory = BOOK/'modelos_preentrenados'/FOLDERS[key]
    candidates = list(directory.glob('*.joblib'))
    preferred = directory/'modelo_final.joblib'
    if preferred.exists():
        return preferred
    if len(candidates) != 1:
        raise ValueError(f'No hay un único pipeline reutilizable para {key}: {directory}')
    return candidates[0]


def pipeline_for(key):
    if key == 'm0':
        from evaluar_svr_rbf_raffle_e3 import _svr_pipeline
        return _svr_pipeline()
    if key == 'm5':
        from modelos_scopus_e3 import make_model
        return make_model('kernel_ridge')
    if key == 'm19':
        from tn_krr_e3 import make_model
        return make_model()
    if key=='m3':
        from linxgboost_fiel import make_model
        return make_model()
    if key in ('m6','m17','m18'):
        from modelos_scopus_e3 import make_model
        return make_model({'m6':'catboost','m17':'xbart','m18':'copilot'}[key])
    if key=='m7':
        from tcr_xgboost_e3 import TCRXGBRegressor
        return TCRXGBRegressor()
    if key in ('m9','m11','m12'):
        from evaluar_xgboost_variantes_e3 import _pipeline
        return _pipeline({'m9':'gbtree','m11':'denseweight','m12':'dart'}[key])
    if key=='m10':
        from evaluar_svr_rbf_raffle_e3 import _raffle_pipeline
        return _raffle_pipeline()
    if key=='m13':
        from hrt_modelo_e3 import make_model
        return make_model()
    if key=='m15':
        from gpr_xgb_hpo_e3 import make_model
        return make_model()
    if key=='m16':
        from rim_regresion_e3 import RIMRegressor
        from evaluar_rim_e3 import FIXED
        return RIMRegressor(**FIXED, idf='paper')
    if key=='m14':
        from logicdt_fiel import make_model
        return make_model()
    return clone(joblib.load(artifact_for(key)))


def configure(catalog):
    """Grids explícitos para bajo coste; planes pendientes preservan sus dominios."""
    for key in LOW_COST:
        if key == 'm0':
            grid = {'modelo__C':[.01,1.,100.], 'modelo__epsilon':[.01,.1,1.],
                    'modelo__gamma':['scale',.001,.03]}
            space = {'modelo__C':('log',.001,1000.),'modelo__epsilon':('log',.01,1.5),
                     'modelo__gamma':('cat',['scale','auto',1e-5,.001,.003,.01,.03,.1,1.,10.])}
        else:
            prefix = 'modelo__regressor__' if key == 'm5' else 'modelo__'
            grid = {prefix+'alpha':[.01,.1,1.,10.,100.],
                    prefix+'gamma':[.001,.003,.01,.03,.1,.3,1.]}
            space = {prefix+'alpha':('log',.01,100.),prefix+'gamma':('log',.001,1.)}
        engine.GRIDS_ALL[key], engine.SPACES[key] = grid, space
    plans = []
    for key,spec in catalog.items():
        if key in LOW_COST:
            state = 'Programado · menor coste'
        elif key in ('svm','knn','ridge','lasso','forest','xgboost'):
            state = 'Reutilizar multibúsqueda clásica activa'
        elif key in FOLDERS:
            state = 'Pendiente · alto coste · ejecución explícita'
        else:
            state = 'Configuración fija / sin HPO local; conservar histórico'
        plans.append({'key':key,'name':spec['name'],'state':state,
                      'historical_domain':spec.get('grid',{}),
                      'grid':engine.GRIDS_ALL.get(key), 'space':engine.SPACES.get(key),
                      'requires_group_fit':key=='m16',
                      'command':f'python Precalculo/evaluar_originales_busquedas_e3.py --models {key}' if key in FOLDERS else None})
    return plans


def prepare_expensive(key, catalog):
    """Construye un dominio ejecutable, sin fit; nunca lanza la búsqueda aquí."""
    model = pipeline_for(key)
    parameters = model.get_params(deep=True)
    grid, space = {}, {}
    for original, domain in ({} if key in ('m14','m3') else catalog[key]['grid']).items():
        name = original if original in parameters else 'modelo__'+original
        if key=='m12' and original in {'modelo__rate_drop','modelo__skip_drop','modelo__sample_type',
                                      'modelo__normalize_type','modelo__one_drop'}:
            # XGBRegressor admite estos parámetros nativos mediante **kwargs.
            name=original
            parameters[name]=None
        if name not in parameters:
            raise ValueError(f'Parámetro no soportado en {key}: {original}')
        if isinstance(domain,dict) and domain.get('distribution') in ('loguniform','uniform'):
            a,b = domain['args']
            lo,hi = (a,b) if domain['distribution']=='loguniform' else (a,a+b)
            kind = 'log' if domain['distribution']=='loguniform' else 'real'
            grid[name] = [lo,math.sqrt(lo*hi) if kind=='log' else (lo+hi)/2,hi]
            space[name] = (kind,lo,hi)
        elif isinstance(domain,str) and domain.startswith('loguniform('):
            lo,hi=ast.literal_eval('('+domain[len('loguniform('):-1]+')')
            grid[name]=[lo,math.sqrt(lo*hi),hi]; space[name]=('log',lo,hi)
        elif isinstance(domain,list):
            def parse(v):
                if not isinstance(v,str): return v
                try: return ast.literal_eval(v)
                except (ValueError,SyntaxError): return v
            values=[parse(v) for v in domain]
            grid[name]=values
            # Los dominios pendientes se mantienen discretos; no se extrapolan.
            space[name]=('cat',values)
        else:
            raise ValueError(f'Dominio pendiente de revisión: {key}/{original}')
    if key in COARSE_GRIDS:
        grid=COARSE_GRIDS[key]
        missing=set(grid)-set(space)
        if missing: raise ValueError(f'Grid grueso de {key} fuera del espacio histórico: {missing}')
    if key=='m15':
        from gpr_xgb_hpo_e3 import GRID as grid, SPACE as space
    if key=='m14':
        from logicdt_fiel import GRID as grid, SPACE as space
    if key=='m3':
        from linxgboost_fiel import GRID as grid, SPACE as space
    engine.GRIDS_ALL[key],engine.SPACES[key]=grid,space
    if key=='m7':
        # Protocolo del artículo (retrofit): se buscan solo fraction/weight sobre el XGBoost ya ajustado.
        from tcr_xgboost_e3 import GRID
        grid=GRID
        space={'fraction':('cat',[0.,.05,.1,.2]),'weight':('cat',[.3,.6,.9,1.])}
        engine.GRIDS_ALL[key],engine.SPACES[key]=grid,space
    return {'grid':grid,'space':space,'grid_size':len(ParameterGrid(grid)),
            'warning':'Revisar presupuesto antes de ejecutar; Grid puede ser muy grande.'}


def manual_fold(key, parameters, frame, fit, val, fidelity, fold):
    groups=frame.iloc[fit][GROUP].unique()
    selected=np.random.default_rng(42+fold).permutation(groups)[:max(2,math.ceil(len(groups)*fidelity))]
    actual=fit[frame.iloc[fit][GROUP].isin(selected).to_numpy()]
    fitting,validation=frame.iloc[actual],frame.iloc[val]
    assert not set(fitting[GROUP]) & set(validation[GROUP])
    model=pipeline_for(key).set_params(**parameters)
    info={'fold':fold,'fit_rows':len(actual),'validation_rows':len(val),
          'fit_groups':fitting[GROUP].nunique(),'validation_groups':validation[GROUP].nunique(),
          'shared_groups':0,'fidelity':fidelity,'fit_seconds':None,'predict_seconds':None,
          'fit_index_sha256':engine.hashlib.sha256(np.asarray(actual,dtype='int64').tobytes()).hexdigest()}
    clock=time.perf_counter()
    try:
        with threadpool_limits(limits=1),warnings.catch_warnings():
            warnings.filterwarnings('ignore',message='Found unknown categories',category=UserWarning)
            warnings.simplefilter('error',ConvergenceWarning)
            kwargs={}
            if 'groups' in inspect.signature(model.fit).parameters: kwargs['groups']=fitting[GROUP]
            elif hasattr(model,'steps') and 'groups' in inspect.signature(model.steps[-1][1].fit).parameters:
                kwargs['modelo__groups']=fitting[GROUP]
            model.fit(fitting[FEATURES],fitting[TARGET],**kwargs)
            info['fit_seconds']=time.perf_counter()-clock
            clock=time.perf_counter(); prediction=model.predict(validation[FEATURES])
            info['predict_seconds']=time.perf_counter()-clock
            info.update(status='completa',RMSE=metrics(validation[TARGET],prediction)['RMSE'])
    except Exception as error:
        info['fit_seconds' if info['fit_seconds'] is None else 'predict_seconds']=time.perf_counter()-clock
        info.update(status='fallida',RMSE=None,error=f'{type(error).__name__}: {error}')
    return info


_TCR_BASE={}


def tcr_base_params(label):
    """XGBoost base de TCR: el ajustado en el mismo entrenamiento externo (o en todo train para 'final')."""
    if not _TCR_BASE:
        classic=json.loads((BOOK.parent/'Dash/data/clasicos/comparacion.json').read_text(encoding='utf-8'))['models']['xgboost']
        for audit in classic['fold_audit']:
            _TCR_BASE[f"external_{audit['fold']}"]=audit['best_params']
        _TCR_BASE['final']=classic['best_params']
    return _TCR_BASE[label]


# Modelos con búsqueda restringida por decisión del usuario (20-oct-2026): solo Optuna/TPE, con dominio
# ampliado y más ensayos. El resto conserva las cinco estrategias.
SEARCH_METHODS={'m3':['Bayesiana TPE']}
SEARCH_BUDGET={'m3':{'bayes_trials':40,'startup_trials':10}}


def domain_description(key):
    """Dominio efectivo de la búsqueda como texto (para fichas cuando no hay un Grid ejecutado)."""
    names={'int':'entero','log':'logarítmico','real':'continuo','cat':'categórico'}
    return {name:(f'{names[spec[0]]} {list(spec[1])}' if spec[0]=='cat' else f'{names[spec[0]]} [{spec[1]}, {spec[2]}]')
            for name,spec in engine.SPACES[key].items()}


class OriginalSearch(engine.Search):
    def __init__(self,key,frame,outer,timing,directory,budget=None):
        super().__init__(key,frame,outer,timing,directory,{**SEARCH_BUDGET.get(key,{}),**(budget or {})})

    def run(self):
        methods=SEARCH_METHODS.get(self.key,engine.METHODS)
        for method in methods: self.run_method(method)
        optimum=min(s['RMSE'] for s in self.summaries)
        selected=next(s for s in self.summaries if s['RMSE']<=optimum+1e-12)
        result={'methods':self.summaries,'selected_method':selected['method'],'best_params':selected['best_params'],
                'selection_rmse':selected['RMSE'],'space':engine.SPACES[self.key],'budget':self.budget,
                'evolution':self.evolution,'outer':self.outer,'trials_file':self.trial_file.name,
                'methods_executed':methods}
        (self.directory/f'selection_{self.key}_{self.outer}.json').write_text(
            json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        return result

    def evaluate(self,params,fidelity=1.):
        if self.key=='m7':
            params={**params,'base_params':tcr_base_params(self.outer)}
            if params['fraction']==0 or params['weight']==1:
                params={**params,'fraction':0.,'weight':1.}
        token=(engine.fingerprint(params),fidelity)
        if token in self.cache: return self.cache[token]
        clock=time.perf_counter()
        scores=joblib.Parallel(n_jobs=self.budget['n_jobs'])(joblib.delayed(manual_fold)(
            self.key,params,self.frame,fit,val,fidelity,fold)
            for fold,(fit,val) in enumerate(self.splits,1))
        valid=all(s['status']=='completa' for s in scores)
        values=[s['RMSE'] for s in scores] if valid else []
        trial={'method':self.method,'params':params,'fidelity':fidelity,
               'RMSE':float(np.mean(values)) if valid else None,
               'sd_RMSE':float(np.std(values)) if valid else None,
               'seconds':time.perf_counter()-clock,'inner_folds':scores,
               'status':'completa' if valid else 'fallida','trial':len(self.trials)+1}
        self.trials.append(trial)
        with self.trial_file.open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(trial,ensure_ascii=False,default=lambda x:x.item())+'\n')
        self.cache[token]=trial
        return trial

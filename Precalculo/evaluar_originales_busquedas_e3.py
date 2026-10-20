"""Multibúsqueda versionada de Originales: bajo coste por defecto, resto explícito.

No activa automáticamente ni sobrescribe resultados anteriores. La selección
de familia usa solo medias CV; test se predice después de cerrar parámetros.
"""
import argparse
import inspect
import json
import shutil
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import ParameterGrid
from threadpoolctl import threadpool_limits

from entregable3 import BOOK, FEATURES, TARGET, GROUP, load_partitions, grouped_splits, metrics
sys.path.insert(0,str(BOOK.parent/'Dash'))
from model_timing import TimingRun, file_hash
from busquedas_originales_e3 import LOW_COST, FOLDERS, configure, prepare_expensive, pipeline_for, OriginalSearch, artifact_for, SEARCH_METHODS, SEARCH_BUDGET, domain_description
import busquedas_hiperparametros_e3 as engine


def dump(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,default=lambda v:v.item()),encoding='utf-8')


def fit_groups(model,frame):
    kwargs={}
    if 'groups' in inspect.signature(model.fit).parameters:kwargs['groups']=frame[GROUP]
    elif hasattr(model,'steps') and 'groups' in inspect.signature(model.steps[-1][1].fit).parameters:
        kwargs['modelo__groups']=frame[GROUP]
    return model.fit(frame[FEATURES],frame[TARGET],**kwargs)


def evaluate(models=LOW_COST, allow_large_grid=False):
    cache=BOOK.parent/'Dash/data'
    run=TimingRun('Originales · multibúsqueda de menor coste',{
        'script':__file__,'script_sha256':file_hash(__file__),
        'search_sha256':file_hash(BOOK/'busquedas_originales_e3.py'),
        'models':list(models),'budget':engine.BUDGET,
        'data':'Train1309/test188; GroupKFold5x5 por estudiante',
        'device':'CPU; 4 procesos internos, 1 hilo por proceso; GPU no utilizada',
        'scope':'Solo modelos elegidos; históricos/costosos y modelos fijos se conservan identificados'})
    output=BOOK/'resultados/e3/originales_busquedas'/run.run_id
    output.mkdir(parents=True)
    status='fallida'
    try:
        base=cache/'originales'
        (output/'historico').mkdir()
        for source in base.iterdir():
            if source.is_file(): shutil.copyfile(source,output/'historico'/source.name)
        catalog=json.loads((base/'catalog.json').read_text(encoding='utf-8'))
        plans=configure(catalog)
        dump(output/'pendientes.json',plans)
        folds=pd.read_csv(base/'folds.csv')
        predictions={part:pd.read_csv(base/f'{part}.csv.gz') for part in ('train','test')}
        train,test,_=load_partitions()
        canonical=pd.read_csv(cache/'test.csv.gz')
        pd.testing.assert_frame_equal(test[FEATURES+[TARGET]].reset_index(drop=True),canonical[FEATURES+[TARGET]],
                                      check_dtype=False,check_exact=False,rtol=1e-12)
        splits=grouped_splits(train)
        specifications={}
        fitted={}
        # Reutilización íntegra de la ejecución multibúsqueda clásica ya validada.
        classics=json.loads((cache/'clasicos/comparacion.json').read_text(encoding='utf-8'))
        svm=json.loads((cache/'svm_report.json').read_text(encoding='utf-8'))
        classic_folds=pd.read_csv(cache/'clasicos/fold_metrics.csv')
        for key in ('svm','knn','ridge','lasso','forest','xgboost'):
            spec=svm if key=='svm' else classics['models'][key]
            catalog[key].update(optimization=spec['optimization'],best_params=spec['best_params'],
                params=spec['best_params'],selection_rmse=spec['selection_rmse'],grid=spec['grid'],
                timing_run_id=classics.get('run_id'),status='Actualizado · cinco búsquedas clásicas reutilizadas')
            name=catalog[key]['name']
            folds=folds.loc[~folds.Modelo.eq(name)]
            folds=pd.concat([folds,classic_folds.loc[classic_folds.Modelo.eq(name)]],ignore_index=True)
            for part in predictions:
                predictions[part][key]=pd.read_csv(cache/f'clasicos/{part}_predictions.csv.gz')[key]
        dump(output/'protocolo.json',{'run_id':run.run_id,'models':list(models),
            'budget':engine.BUDGET,'test_used_for_selection':False,'source_sha256':{
                'Datos_Brutos.csv':file_hash(BOOK/'Data/Datos_Brutos.csv'),
                'catalog_historico':file_hash(output/'historico/catalog.json')},
            'active_classic_run':classics.get('run_id'),
            'policy':'Método/hiperparámetros por RMSE interno completo; familia por media externa, exploratoria'})
        for key in models:
            if key not in LOW_COST:
                plan=prepare_expensive(key,catalog)
                if plan['grid_size']>1000 and not allow_large_grid:
                    raise ValueError(f'Grid de {key} tiene {plan["grid_size"]} candidatos; revisar presupuesto y --allow-large-grid.')
            oof=np.full(len(train),np.nan)
            selections=[]
            records=[]
            for fold,(fi,va) in enumerate(splits,1):
                fitting=train.iloc[fi].reset_index(drop=True)
                selection=OriginalSearch(key,fitting,f'external_{fold}',run,output).run()
                model=pipeline_for(key).set_params(**selection['best_params'])
                with threadpool_limits(limits=1):
                    with run.measure('Entrenamiento/refit',f'{key} / externo{fold}',len(fi)):
                        fit_groups(model,fitting)
                    with run.measure('Inferencia',f'{key} / OOF externo{fold}',len(va),warmup=0,repetitions=1):
                        pred=model.predict(train.iloc[va][FEATURES])
                oof[va]=pred
                selections.append(selection)
                records.append({'Modelo':catalog[key]['name'],'Fold':fold,**metrics(train.iloc[va][TARGET],pred)})
            final=OriginalSearch(key,train,'final',run,output).run()
            model=pipeline_for(key).set_params(**final['best_params'])
            with threadpool_limits(limits=1),run.measure('Entrenamiento/refit',f'{key} / final',len(train)):
                fit_groups(model,train)
            joblib.dump(model,output/f'{key}.joblib')
            fitted[key]=model
            specifications[key]={'best_params':final['best_params'],'selection_rmse':final['selection_rmse'],
                'optimization':{**final,'external_selections':selections,
                    'timings':[r for r in run.rows if r['batch'].startswith(key+' /')]},
                'model_sha256':file_hash(output/f'{key}.joblib')}
            only=SEARCH_METHODS.get(key)
            catalog[key].update(**specifications[key],params=final['best_params'],
                grid=domain_description(key) if only else engine.GRIDS_ALL[key],
                timing_run_id=run.run_id,
                status=('Actualizado · solo Optuna/TPE (dominio ampliado)' if only else 'Actualizado · cinco estrategias anidadas'),
                method=(f"{', '.join(only)} únicamente (decisión del usuario, 20-oct-2026), dominio ampliado y "
                        f"{SEARCH_BUDGET[key]['bayes_trials']} ensayos; 5x5GroupKFold; selección por RMSE interno, sin test."
                        if only else 'Grid/Random/TPE/DEAP/SH;5x5GroupKFold; selección por RMSE interno, sin test.'))
            predictions['train'][key]=oof
            folds=folds.loc[~folds.Modelo.eq(catalog[key]['name'])]
            folds=pd.concat([folds,pd.DataFrame(records)],ignore_index=True)
            dump(output/f'completo_{key}.json',specifications[key])
        # Todos los parámetros de los modelos ejecutados se cierran antes de test.
        dump(output/'seleccion_antes_test.json',{'run_id':run.run_id,'models':specifications,
                                               'test_used_for_selection':False})
        for key,model in fitted.items():
            with threadpool_limits(limits=1),run.measure('Inferencia',f'{key} / test202530',len(test),repetitions=1,warmup=0):
                predictions['test'][key]=model.predict(test[FEATURES])
        for key,spec in catalog.items():
            spec.setdefault('status','Histórico · configuración fija' if not spec.get('grid') else 'Pendiente · alto coste, resultados históricos')
        eligible={key:spec for key,spec in catalog.items() if key!='dummy' and key in predictions['train'] and
                  len(folds.loc[folds.Modelo.eq(spec['name'])])==5}
        means=folds.groupby('Modelo').RMSE.mean()
        best=min(eligible,key=lambda key:means[eligible[key]['name']])
        if best in fitted: source=output/f'{best}.joblib'
        elif best=='m5': source=base/'best.joblib'
        elif best=='m19': source=base/'tn_krr.joblib'
        elif best in FOLDERS: source=artifact_for(best)
        elif best in ('svm','knn','ridge','lasso','forest','xgboost'):
            source=cache/'model.joblib' if best=='svm' else cache/f'clasicos/{best}.joblib'
        else: raise ValueError('El ganador requiere localizar un pipeline guardado: '+best)
        shutil.copyfile(source,output/'best.joblib')
        if 'm19' not in fitted: shutil.copyfile(base/'tn_krr.joblib',output/'tn_krr.joblib')
        else: shutil.copyfile(output/'m19.joblib',output/'tn_krr.joblib')
        for part,frame in predictions.items(): frame.to_csv(output/f'{part}.csv.gz',index=False)
        folds.to_csv(output/'folds.csv',index=False)
        for name in ('contrasts.csv','inventory.csv','cv_inference.csv','cv_inference.json'):
            shutil.copyfile(base/name,output/name)
        dump(output/'catalog.json',catalog)
        dump(output/'completo.json',{'run_id':run.run_id,'best_key':best,'best_name':catalog[best]['name'],
            'best_mean_cv':float(means[catalog[best]['name']]),'executed':list(models),
            'note':'Inventario mixto: actualizados/reutilizados/históricos explícitos; test no selecciona.',
            'files':{p.name:file_hash(p) for p in output.iterdir() if p.is_file() and p.suffix!='joblib'}})
        status='completa'
        print('COMPLETO',output,'GANADOR CV',best,catalog[best]['name'],flush=True)
        return output
    finally:
        run.finish(status)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--models',nargs='+',default=list(LOW_COST),choices=list(FOLDERS))
    parser.add_argument('--allow-large-grid',action='store_true')
    args=parser.parse_args()
    evaluate(args.models,args.allow_large_grid)

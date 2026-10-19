"""Valida, prepara análisis/explicaciones y activa una ejecución Originales completa."""
import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from prepare_data import BOOK,CACHE,RESULTS,CLASSIC_FILES,hashes
from prepare_originals import prepare_originals,FILES,ACTIVE_POINTER
from model_timing import TimingRun,file_hash


def activate(directory):
    directory=Path(directory).resolve()
    if directory.parent!=(RESULTS/'originales_busquedas').resolve():
        raise ValueError('Solo se activa una ejecución del directorio versionado Originales.')
    active=json.loads((directory/'completo.json').read_text(encoding='utf-8'))
    catalog=json.loads((directory/'catalog.json').read_text(encoding='utf-8'))
    run=TimingRun('Originales · verificación y activación',{'directory':str(directory),
        'script_sha256':file_hash(__file__),'scope':'Valida predicciones guardadas y prepara estadísticas/explicación; no refit global'})
    status='fallida'
    try:
        import shutil
        shutil.copyfile(directory/'historico/inventory.csv',directory/'historical_inventory.csv')
        train,test=[pd.read_csv(CACHE/f'{p}.csv.gz') for p in ('train','test')]
        predictions={p:pd.read_csv(directory/f'{p}.csv.gz') for p in ('train','test')}
        folds=pd.read_csv(directory/'folds.csv')
        from prepare_data import metrics
        for key,spec in catalog.items():
            if key not in predictions['train']:continue
            expected=folds.loc[folds.Modelo.eq(spec['name'])].set_index('Fold')
            assert len(expected)==5
            for fold,frame in train.groupby('fold'):
                score=metrics(frame.nota_primer_parcial,predictions['train'].loc[frame.index,key])
                for name,value in score.items():
                    np.testing.assert_allclose(value,expected.loc[fold,name],atol=1e-10,rtol=1e-10)
        for key in active['executed']:
            model=joblib.load(directory/f'{key}.joblib')
            with threadpool_limits(limits=1),run.measure('Inferencia',f'{key} / validación serialización test',len(test)):
                actual=model.predict(test[list(model.feature_names_in_)])
            np.testing.assert_allclose(actual,predictions['test'][key],atol=1e-10,rtol=0)
        inventory=pd.read_csv(directory/'inventory.csv')
        for key,spec in catalog.items():
            score=metrics(test.nota_primer_parcial,predictions['test'][key])
            ix=inventory.Modelo.eq(spec['name'])
            inventory.loc[ix,'RMSE_test']=score['RMSE']
            inventory.loc[ix,'R2_test']=score['R²']
            inventory.loc[ix,'delta_RMSE_vs_SVM']=score['RMSE']-metrics(test.nota_primer_parcial,predictions['test'].svm)['RMSE']
            inventory.loc[ix,'estado']=spec.get('status','Histórico')
        # Las inferencias antiguas solo permanecen en contrasts/cv_inference archivados.
        for col in inventory:
            if col.startswith('p_') or 'significancia' in col:inventory[col]=np.nan
        inventory=inventory.sort_values('RMSE_test',kind='stable')
        inventory['rango_RMSE']=np.arange(1,len(inventory)+1)
        inventory.to_csv(directory/'inventory.csv',index=False)
        from original_analysis import prepare as prepare_analysis
        analysis=prepare_analysis(directory,CACHE,BOOK)
        from original_interpretation import prepare as prepare_explanations
        prepare_explanations(directory,CACHE,BOOK)
        # Preparar planes costosos sin fit ni predict; errores/dependencias quedan explícitos.
        from busquedas_originales_e3 import prepare_expensive,FOLDERS,LOW_COST
        plans=json.loads((directory/'pendientes.json').read_text(encoding='utf-8'))
        for plan in plans:
            key=plan['key']
            if key in active['executed']:
                plan['state']='Completado · cinco estrategias de menor coste'
            if key in FOLDERS and key not in LOW_COST:
                try:
                    plan['prepared']=prepare_expensive(key,catalog)
                    plan['preparation_state']='Dominio/factory preparados; sin ejecutar'
                except Exception as error:
                    plan['preparation_state']='Requiere resolver dependencia/artefacto antes de ejecutar'
                    plan['preparation_error']=f'{type(error).__name__}: {error}'
        (directory/'pendientes.json').write_text(json.dumps(plans,ensure_ascii=False,indent=2),encoding='utf-8')
        active['artifact_sha256']={name:file_hash(directory/name) for name in FILES if name!='active.json'}
        (directory/'active.json').write_text(json.dumps(active,ensure_ascii=False,indent=2),encoding='utf-8')
        ACTIVE_POINTER.write_text(json.dumps({'run_id':active['run_id'],'best_key':active['best_key']},indent=2),encoding='utf-8')
        prepare_originals()
        manifest=json.loads((CACHE/'manifest.json').read_text(encoding='utf-8'))
        # prepare_data fue importado antes de activar: recalcular la lista de fuentes.
        import prepare_data,importlib
        importlib.reload(prepare_data)
        manifest['sha256']=prepare_data.hashes()
        for name in FILES:manifest['artifact_sha256']['originales/'+name]=file_hash(CACHE/'originales'/name)
        (CACHE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        status='completa'
        print(json.dumps({'active':active['run_id'],'best':active['best_name'],
            'friedman':analysis['omnibus'],'family_test':analysis['students']['family_size'],
            'pending':[p['name'] for p in plans if 'alto coste' in p['state']]},ensure_ascii=False),flush=True)
    finally:run.finish(status)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory');args=parser.parse_args()
    sys.path.insert(0,str(BOOK))
    activate(args.directory)

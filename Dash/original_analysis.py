"""Friedman/MCS de Originales y bootstrap-t/BCa frente a su SVM activo."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from dash import html

from classic_friedman import friedman_comparison, summary
from classic_posthoc import analyze
from student_comparison import compare, student_losses
from model_timing import TimingRun, file_hash
from model_groups import IMPORT_ONLY, validate as validate_groups
from student_dm import select_top, analyze as dm_analyze, render as render_dm
from student_dm import ADAPTATION_NOTE, finalist_pairs, pairs_table, pairs_reading


def prepare(directory, cache, book):
    import sys
    directory,cache,book=Path(directory),Path(cache),Path(book)
    if str(book) not in sys.path: sys.path.insert(0,str(book))
    from entregable3 import load_partitions, GROUP, TARGET, FEATURES
    catalog=json.loads((directory/'catalog.json').read_text(encoding='utf-8'))
    folds=pd.read_csv(directory/'folds.csv')
    pred={p:pd.read_csv(directory/f'{p}.csv.gz') for p in ('train','test')}
    validate_groups(catalog)
    # Los modelos de librería importada/preentrenados no entran en ninguna prueba (decisión del usuario, 20-oct-2026).
    eligible=[k for k,s in catalog.items() if k!='dummy' and k not in IMPORT_ONLY and k in pred['train'] and
              len(folds.loc[folds.Modelo.eq(s['name'])])==5]
    names=[catalog[k]['name'] for k in eligible]
    run=TimingRun('Originales · Friedman/MCS y contrastes por estudiante',{
        'script_sha256':file_hash(__file__),'models_cv':names,
        'scope':'Estadística de predicciones guardadas; sin fit/predict; CPU',
        'models_test':[s['name'] for k,s in catalog.items() if k!='dummy' and k not in IMPORT_ONLY],
        'excluded_library':[catalog[k]['name'] for k in IMPORT_ONLY],
        'configuration':{'folds':5,'reps_test':49999,'seed':20261018,
                         'family_test':len([k for k in catalog if k not in ('svm','dummy') and k not in IMPORT_ONLY and k in pred['test']])}})
    status='fallida'
    try:
        with run.measure('Análisis estadístico','Friedman/MCS Originales',len(names)):
            omnibus=friedman_comparison(folds,names)
            posthoc=analyze(folds,names,omnibus)
        train_private,private,_=load_partitions()
        test=pd.read_csv(cache/'test.csv.gz')
        pd.testing.assert_frame_equal(private[FEATURES+[TARGET]],test[FEATURES+[TARGET]],
                                      check_dtype=False,check_exact=False,rtol=1e-12)
        keys=['svm']+[k for k in catalog if k not in ('svm','dummy') and k not in IMPORT_ONLY and k in pred['test']]
        losses,sizes=student_losses(test[TARGET],pred['test'][keys],private[GROUP])
        with run.measure('Análisis estadístico','Bootstrap-t/BCa y Holm Originales',len(losses)):
            students,draws=compare(losses,[catalog[k]['name'] for k in keys])
        students.update(n_records=len(test),students_with_repeated_records=int((sizes>1).sum()))
        # Intervalos marginales BCa de RMSE, con mismos índices y jackknife por estudiante.
        from student_comparison import bca_interval
        rng=np.random.default_rng(20261018)
        boot=np.empty((49999,len(keys)))
        for start in range(0,len(boot),512):
            stop=min(start+512,len(boot)); ix=rng.integers(0,len(losses),(stop-start,len(losses)))
            boot[start:stop]=np.sqrt(losses[ix].mean(axis=1))
        jack=np.sqrt((losses.sum(axis=0)-losses)/(len(losses)-1))
        marginal=[{'Modelo':catalog[key]['name'],'RMSE':float(np.sqrt(losses[:,j].mean())),
                   **bca_interval(np.sqrt(losses[:,j].mean()),boot[:,j],jack[:,j])}
                  for j,key in enumerate(keys)]
        # Etapa 3: contraste tipo Diebold–Mariano por estudiante sobre OOF (CV) y, como complemento, test.
        train_cache=pd.read_csv(cache/'train.csv.gz')
        np.testing.assert_allclose(train_private[TARGET].to_numpy(float),train_cache[TARGET].to_numpy(float),atol=1e-9)
        top=select_top(posthoc['mcs'],5)
        name_key={s['name']:k for k,s in catalog.items()}
        corrected=pd.read_csv(directory/'cv_inference.csv').set_index('Modelo')
        with run.measure('Análisis estadístico','Diebold–Mariano por estudiante top 5 MCS (CV, test y pares)',len(train_private)):
            dm=dm_analyze(top,pred['train'],pred['test'],train_private[GROUP].to_numpy(),private[GROUP].to_numpy(),
                          train_private[TARGET].to_numpy(float),private[TARGET].to_numpy(float),name_key,'svm',corrected)
        dm['finalist_pairs']=finalist_pairs(posthoc['pairs'],pred['train'],train_private[GROUP].to_numpy(),
                                            train_private[TARGET].to_numpy(float),name_key)
        serialized={'dm':dm,'omnibus':{k:v for k,v in omnibus.items() if k!='ranking'},
            'ranking':omnibus['ranking'].to_dict('records'),
            'mcs':posthoc['mcs'].to_dict('records'),'pairs':posthoc['pairs'].to_dict('records'),
            'effects':posthoc['effects'].to_dict('records'),'finalists':posthoc['finalists'],
            'students':students,'marginal_rmse':marginal,
            'excluded_cv':[s['name'] for k,s in catalog.items() if k not in eligible and k not in IMPORT_ONLY],
            'excluded_library':[catalog[k]['name'] for k in IMPORT_ONLY],
            'analysis_run':run.run_id,'input_sha256':{n:file_hash(directory/n) for n in
                ('catalog.json','folds.csv','train.csv.gz','test.csv.gz')},
            'active':json.loads((directory/'completo.json').read_text(encoding='utf-8'))}
        (directory/'analysis.json').write_text(json.dumps(serialized,ensure_ascii=False,indent=2),encoding='utf-8')
        (run.directory/'resultados.json').write_text(json.dumps(serialized,ensure_ascii=False,indent=2),encoding='utf-8')
        np.savez_compressed(run.directory/'distribuciones_bootstrap.npz',**draws)
        status='completa'; return serialized
    finally: run.finish(status)


def table_statistics(scores, *, cv=False, global_view=True, analysis=None):
    values=scores.sort_values('RMSE',na_position='last',kind='stable').copy()
    if cv and global_view and analysis:
        values=values.merge(pd.DataFrame(analysis['ranking'])[['Modelo','Rango promedio']],on='Modelo',how='left')
    return values


def section(data,ui):
    md,table=ui['md'],ui['table']
    omnibus=data['omnibus']; dm=data['dm']; alpha=.05
    global_table=pd.DataFrame([{'χ² Friedman':omnibus['statistic'],'g.l.':omnibus['df'],
        'p asintótico':omnibus['pvalue'],'Conclusión':'Se rechaza H₀ · exploratorio' if omnibus['pvalue']<alpha else 'No se rechaza H₀'}])
    return html.Article([
        html.H3('Conclusiones y comparación estadística · Originales'),
        md('**Alcance de las pruebas:** clásicos, kernels (SVR RBF, Kernel Ridge, TR-KRR), híbridos e implementaciones propias. '
           '**Quedan fuera de todas estas pruebas** los modelos de librería importada o preentrenados (decisión del usuario, 20-oct-2026), '
           'que se conservan solo como referencia y se ocultan por defecto: '+', '.join(data.get('excluded_library',[]))+'. '
           'No es una comparación de eficiencia a presupuesto uniforme. '
           'La familia con menor RMSE medio CV se identifica de forma exploratoria; test no selecciona.'),
        html.H4('Etapa 1 · Prueba global de Friedman'),table(global_table),
        html.Details([html.Summary('Test de Friedman · explicación, hipótesis y limitaciones'),
            md(f'**{omnibus["n_models"]} modelos × cinco folds externos emparejados.** H₀: rangos promedio iguales. '
               'Menor RMSE obtiene rango1; empates promediados. P asintótico exploratorio: solo cinco bloques '
               'y entrenamientos solapados. Rechazo no identifica un par ganador y no corrige esa dependencia. '
               'Se excluyen del ómnibus: '+', '.join(data['excluded_cv'])+'. Dummy es control; '
               'TabPFN fine-tuned no tiene OOF independiente. No se inventan folds faltantes.')],className='details'),
        html.Details([html.Summary('Rangos por fold y promedio'),table(pd.DataFrame(data['ranking']))],className='details'),
        html.H4('Etapa 2 · Model Confidence Set (MCS)'),
        md('MSE por fold, 3.125 remuestreos emparejados exhaustivos, T_R/eliminación e_R, α0.10. '
           '**Adaptación exploratoria sin cobertura90% garantizada** por dependencia entre folds. '
           'Un p MCS no es probabilidad de ser el mejor; conservar varios modelos no demuestra equivalencia.'),
        table(pd.DataFrame(data['mcs'])) if data['mcs'] else md('MCS no ejecutado: no se rechaza Friedman.'),
        html.Details([html.Summary('Finalistas · IC por fold y DM-HLN adaptado por estudiante'),
            md(ADAPTATION_NOTE),
            md('ΔMSE=A−B; negativo favorece A. Las columnas «folds» son intervalos percentiles descriptivos, no estacionarios ni simultáneos. '
               'Las columnas «por estudiante» y los p son el DM-HLN adaptado; cada par es una pregunta independiente, sin Holm ni '
               'corrección por la selección del MCS. GW/CW y el IC estacionario no aplican: no hay diseño de pronóstico, horizonte ni anidamiento. '
               'No se convierten filas/folds en tiempo.'),
            table(pairs_table(pd.DataFrame(data['pairs']),dm.get('finalist_pairs',[])) if dm.get('finalist_pairs') else pd.DataFrame(data['pairs'])),
            md(pairs_reading(dm.get('finalist_pairs',[])))],className='details'),
        *render_dm(dm,ui),
        html.H4('Tamaño del efecto · pérdidas MSE por fold'),
        md('Cliff marginal y Cohen d_z emparejado, negativos favorecen A; descriptores sobre cinco folds. '
           'No implican causalidad ni relevancia educativa; SD cero no estimable.'),
        html.Details([html.Summary('Ver pares y tamaños del efecto por fold'),table(pd.DataFrame(data['effects']))],className='details'),
        html.Details([html.Summary('IC BCa95 de RMSE test por modelo'),
            md('Modelos fijos; remuestreo y jackknife por estudiante. IC individuales, no para seleccionar.'),
            table(pd.DataFrame(data['marginal_rmse'])[['Modelo','RMSE','low','high','state']].rename(
                columns={'low':'IC95 inferior','high':'IC95 superior','state':'Estado BCa'}))],className='details'),
    ],className='card classic-statistical-conclusions')

"""Evaluación reproducible 5x5 por estudiante de los cuatro métodos Scopus."""
import argparse
import gc
import importlib.metadata
import json
import time
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import ParameterGrid
from statsmodels.stats.multitest import multipletests
from threadpoolctl import threadpool_limits

from entregable3 import BOOK, OUTPUT, FEATURES, TARGET, GROUP, grouped_splits, metrics, source_hashes, write_json
from evaluacion_nuevos_e3 import partitions
from evaluar_tabpfn25_finetuned_e3 import paired_comparison
from finetune_tabpfn25_e3 import sha256
from modelos_scopus_e3 import GRIDS, LABELS, REFERENCES, make_model, VENDOR

ROOT = OUTPUT/'scopus'


def provenance(key):
    paths = ['modelos_scopus_e3.py','evaluar_scopus_e3.py','evaluacion_nuevos_e3.py',
        'evaluar_tabpfn25_finetuned_e3.py','resultados/e3/train.csv.gz','resultados/e3/test.csv.gz',
        'resultados/e3/clasicos/test_predictions.csv.gz']
    result = {**source_hashes(), **{p:sha256(BOOK/p) for p in paths},
        'versions':{p:importlib.metadata.version(p) for p in
            ['numpy','pandas','scikit-learn','scipy','stochtree','catboost','numba']},
        'grid':list(ParameterGrid(GRIDS[key])), 'reference':REFERENCES[key]}
    if key == 'copilot':
        result['vendor_sha256'] = {p.name:sha256(p) for p in (VENDOR/'pilot').glob('*.py')}
    return result


def fit(key, params, frame):
    with warnings.catch_warnings(), threadpool_limits(limits=1):
        warnings.filterwarnings('ignore',message='Found unknown categories')
        # GFR con columnas discretas genera avisos repetidos: su limitación se documenta.
        warnings.filterwarnings('ignore',message='Covariate.*',module='stochtree.bart')
        return make_model(key,**params).fit(frame[FEATURES],frame[TARGET])


def predict(model, frame):
    with warnings.catch_warnings(), threadpool_limits(limits=1):
        warnings.filterwarnings('ignore',message='Found unknown categories')
        values = np.asarray(model.predict(frame[FEATURES]),dtype=float)
    if values.shape != (len(frame),) or not np.isfinite(values).all():
        raise ValueError('Predicciones inválidas.')
    return values


def tune(key, frame, label, folder):
    candidates = list(ParameterGrid(GRIDS[key]))
    path = folder/f'grid_{label}.csv'
    rows = pd.read_csv(path).to_dict('records') if path.exists() else []
    done = {(int(r['candidate']),int(r['inner_fold'])) for r in rows}
    for c,params in enumerate(candidates,1):
        for k,(fi,va) in enumerate(grouped_splits(frame),1):
            if (c,k) in done:
                continue
            start = time.perf_counter()
            model = fit(key,params,frame.iloc[fi])
            score = metrics(frame.iloc[va][TARGET],predict(model,frame.iloc[va]))
            rows.append({'candidate':c,'inner_fold':k,**params,**score,
                'shared_students':len(set(frame.iloc[fi][GROUP]) & set(frame.iloc[va][GROUP])),
                'seconds':time.perf_counter()-start})
            pd.DataFrame(rows).to_csv(path,index=False)
            del model
        print(f'{key} {label}: {c}/{len(candidates)}, RMSE={np.mean([r["RMSE"] for r in rows if r["candidate"]==c]):.6f}',flush=True)
    scores = pd.DataFrame(rows).groupby('candidate').RMSE.mean()
    chosen = int(scores.idxmin())
    params = candidates[chosen-1]
    return fit(key,params,frame),params,float(scores.loc[chosen])


def run(key):
    train,test,folds,audit = partitions()
    folder,private = ROOT/key,BOOK/'modelos_preentrenados/scopus'/key
    folder.mkdir(parents=True,exist_ok=True)
    private.mkdir(parents=True,exist_ok=True)
    stamp = provenance(key)
    protocol = folder/'protocolo.json'
    if protocol.exists() and json.loads(protocol.read_text(encoding='utf-8'))['provenance'] != stamp:
        raise ValueError('Procedencia cambió: preservar resultados y usar una carpeta nueva antes de repetir.')
    write_json(protocol,{'provenance':stamp,'test_used_for_selection':False,
        'method':'5 folds externos, 5 internos GroupKFold por estudiante; HPO y preparación exclusivamente en fit.'})
    if (folder/'reporte.json').exists():
        return json.loads((folder/'reporte.json').read_text(encoding='utf-8'))
    oof = np.full(len(train),np.nan)
    rows,audits = [],[]
    for k,(fi,va) in enumerate(folds,1):
        saved = folder/f'externo_{k}.json'
        pred_path = folder/f'oof_{k}.npy'
        if saved.exists() and pred_path.exists():
            checkpoint=json.loads(saved.read_text(encoding='utf-8'))
            oof[va]=np.load(pred_path)
            rows.append(checkpoint['metrics']); audits.append(checkpoint['audit'])
            continue
        start=time.perf_counter()
        print(f'{key}: externo {k}/5',flush=True)
        model,params,inner=tune(key,train.iloc[fi],f'externo_{k}',folder)
        oof[va]=predict(model,train.iloc[va])
        row={'Modelo':LABELS[key],'Fold':k,**metrics(train.iloc[va][TARGET],oof[va])}
        fold_audit={'fold':k,'best_params':params,'inner_rmse':inner,'fit_rows':len(fi),
            'validation_rows':len(va),'shared_students':0,'seconds':time.perf_counter()-start}
        joblib.dump(model,private/f'fold_{k}.joblib')
        np.save(pred_path,oof[va])
        write_json(saved,{'metrics':row,'audit':fold_audit})
        rows.append(row);audits.append(fold_audit)
        print(f'{key}: externo {k} RMSE={row["RMSE"]:.6f}',flush=True)
        del model;gc.collect()
    model,params,inner=tune(key,train,'final',folder)
    joblib.dump(model,private/'modelo_final.joblib')
    write_json(folder/'seleccion_antes_test.json',{'params':params,'inner_rmse':inner,'test_used':False})
    # Primer acceso predictivo al test después de cerrar la selección.
    pred=predict(model,test)
    np.testing.assert_allclose(predict(joblib.load(private/'modelo_final.joblib'),test),pred,atol=1e-10,rtol=0)
    for split,frame,values in [('train',train,oof),('test',test,pred)]:
        table=frame[[TARGET,'periodo','fila_fuente']].copy()
        table['prediccion']=values
        if split=='train':
            table['fold']=pd.read_csv(OUTPUT/'train.csv.gz').fold
        table.to_csv(folder/f'{split}_predictions.csv.gz',index=False,compression='gzip')
    fold_table=pd.DataFrame(rows)
    fold_table.to_csv(folder/'fold_metrics.csv',index=False)
    score=metrics(test[TARGET],pred)
    report={'model':LABELS[key],'key':key,'test':score,
        'cv':[{'metrica':m,'media_cv':float(fold_table[m].mean()),'sd_cv':float(fold_table[m].std(ddof=0)),
            'OOF_agrupado':metrics(train[TARGET],oof)[m]} for m in score],
        'best_params':params,'inner_rmse':inner,'fold_audit':audits,'partition':audit,'provenance':stamp,
        'reference':REFERENCES[key], 'private_model':str(private/'modelo_final.joblib')}
    write_json(folder/'reporte.json',report)
    print(f'{key} TEST: {score}',flush=True)
    return report


def compare():
    train,test,_,_=partitions()
    reports={key:json.loads((ROOT/key/'reporte.json').read_text(encoding='utf-8')) for key in LABELS}
    y=test[TARGET].to_numpy(float)
    svm=pd.read_csv(OUTPUT/'test.csv.gz').svm.to_numpy(float)
    classic=pd.read_csv(OUTPUT/'clasicos/test_predictions.csv.gz')
    np.testing.assert_allclose(classic[TARGET],y,atol=1e-12,rtol=0)
    xgb=classic.xgboost.to_numpy(float)
    scores=[{'Modelo':'SVM lineal',**metrics(y,svm)},{'Modelo':'XGBoost',**metrics(y,xgb)}]
    contrasts=[]
    for key,r in reports.items():
        if r['provenance'] != provenance(key):
            raise ValueError(f'Resultado desactualizado: {key}')
        table=pd.read_csv(ROOT/key/'test_predictions.csv.gz')
        np.testing.assert_array_equal(table.fila_fuente,test.fila_fuente)
        np.testing.assert_allclose(table[TARGET],y,atol=1e-12,rtol=0)
        pred=table.prediccion.to_numpy(float)
        scores.append({'Modelo':LABELS[key],**metrics(y,pred)})
        for label,old in [('SVM lineal',svm),('XGBoost',xgb)]:
            for row in paired_comparison(y,pred,old,test[GROUP]):
                contrasts.append({'Modelo':LABELS[key],'Referencia':label,**row})
    contrasts=pd.DataFrame(contrasts)
    # Cuatro comparaciones por referencia y familia global acumulada de 21 pares:
    # 13 anteriores vs SVM + 4 nuevos vs SVM + 4 nuevos vs XGBoost.
    historical=pd.read_csv(OUTPUT/'seleccionados/listado_completo_significancia.csv')
    historical=historical[historical.p_bilateral.notna()]
    current=contrasts[contrasts.metrica.eq('RMSE')].copy()
    assert len(historical)==13 and len(current)==8
    all_p=np.r_[historical.p_bilateral,current.p_bilateral]
    adjusted=multipletests(all_p,method='holm')[1]
    current['p_Holm_global_21']=adjusted[len(historical):]
    current['p_Holm_4_por_referencia']=np.nan
    for label,group in current.groupby('Referencia',sort=False):
        current.loc[group.index,'p_Holm_4_por_referencia']=multipletests(group.p_bilateral,method='holm')[1]
    for row in current.to_dict('records'):
        mask=contrasts.Modelo.eq(row['Modelo']) & contrasts.Referencia.eq(row['Referencia'])
        for col in ['p_Holm_global_21','p_Holm_4_por_referencia']:
            contrasts.loc[mask,col]=row[col]
    contrasts.to_csv(ROOT/'contrastes_pareados.csv',index=False)
    summary=pd.DataFrame(scores).sort_values('RMSE')
    summary['delta_RMSE_vs_SVM']=summary.RMSE-metrics(y,svm)['RMSE']
    summary['delta_RMSE_vs_XGBoost']=summary.RMSE-metrics(y,xgb)['RMSE']
    summary.to_csv(ROOT/'comparacion_test.csv',index=False)
    historical['p_Holm_global_21']=adjusted[:len(historical)]
    historical.to_csv(ROOT/'historicos_Holm_global_21.csv',index=False)
    report={'test':summary.to_dict('records'),'contrasts':contrasts.to_dict('records'),
        'family_size':21,'historical_family_size':13,'references':['SVM lineal','XGBoost'],
        'statistics':'Permutación bilateral pareada99999 y bootstrap10000 por estudiante, seed42. '
            'RMSE/R² comparten contraste SSE. IC marginales. Holm4 por referencia y global21 pares. '
            'Condicional a los modelos; exploratorio por reutilización del test.',
        'models':reports}
    write_json(ROOT/'comparacion.json',report)
    print(summary.to_string(index=False),flush=True)
    print(current.to_string(index=False),flush=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model',choices=[*LABELS,'all','compare'])
    args=parser.parse_args()
    if args.model=='compare':compare()
    elif args.model=='all':
        for key in LABELS:run(key)
        compare()
    else:run(args.model)

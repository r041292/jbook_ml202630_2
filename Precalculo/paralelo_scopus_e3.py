"""Distribuir folds independientes; reutiliza sin cambios fit/predict/tune de E3."""
import gc
import json
import time

import joblib
import numpy as np
from joblib import Parallel,delayed,parallel_config

from entregable3 import BOOK,TARGET,GROUP,metrics,write_json
from evaluar_scopus_e3 import ROOT,provenance,compatible,tune,predict,run
from evaluacion_nuevos_e3 import partitions
from modelos_scopus_e3 import LABELS


def worker(key,fold):
    train,_,folds,_=partitions()
    folder,private=ROOT/key,BOOK/'modelos_preentrenados/scopus'/key
    actual=json.loads((folder/'protocolo.json').read_text(encoding='utf-8'))['provenance']
    if not compatible(actual,provenance(key)):
        raise ValueError('Procedencia incompatible.')
    if fold=='final':
        model,params,inner=tune(key,train,'final',folder)
        write_json(folder/'seleccion_train_paralela.json',{'params':params,'inner_rmse':inner,'test_used':False})
        del model
        return f'{key} selección train completa'
    k=int(fold)
    saved,pred_path=folder/f'externo_{k}.json',folder/f'oof_{k}.npy'
    if saved.exists() and pred_path.exists():
        return f'{key} externo{k} guardado'
    fi,va=folds[k-1]
    started=time.perf_counter()
    model,params,inner=tune(key,train.iloc[fi],f'externo_{k}',folder)
    pred=predict(model,train.iloc[va])
    row={'Modelo':LABELS[key],'Fold':k,**metrics(train.iloc[va][TARGET],pred)}
    audit={'fold':k,'best_params':params,'inner_rmse':inner,'fit_rows':len(fi),
        'validation_rows':len(va),'shared_students':len(set(train.iloc[fi][GROUP]) & set(train.iloc[va][GROUP])),
        'seconds':time.perf_counter()-started}
    joblib.dump(model,private/f'fold_{k}.joblib')
    np.save(pred_path,pred)
    write_json(saved,{'metrics':row,'audit':audit})
    del model;gc.collect()
    return f'{key} externo{k} RMSE={row["RMSE"]}'


if __name__=='__main__':
    # Se detuvieron los dos coordinadores secuenciales antes de ejecutar este archivo.
    # Cada tarea escribe una grilla distinta; no hay dos escritores por fold.
    tasks=[]
    for key in ['xbart','catboost']:
        for k in range(1,6):
            if not (ROOT/key/f'externo_{k}.json').exists():tasks.append((key,k))
        tasks.append((key,'final'))
    print('Tareas independientes:',tasks,flush=True)
    with parallel_config(backend='loky',inner_max_num_threads=1):
        for message in Parallel(n_jobs=6)(delayed(worker)(key,k) for key,k in tasks):
            print(message,flush=True)
    # Cerrar OOF, refit final y test solo una vez que termina la selección en train.
    for key in ['xbart','catboost']:run(key)

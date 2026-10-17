"""Auditar las ejecuciones reales: grillas completas, OOF y preparación por fit."""
import argparse
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import ParameterGrid

from entregable3 import BOOK,FEATURES,TARGET,NUMERIC,metrics,write_json
from evaluacion_nuevos_e3 import partitions
from evaluar_scopus_e3 import ROOT,predict,provenance,compatible
from modelos_scopus_e3 import GRIDS,LABELS


def audit(partial=False):
    train,test,folds,_=partitions()
    checked=[]
    for key in LABELS:
        folder=ROOT/key
        if partial and not (folder/'reporte.json').exists():continue
        report=json.loads((folder/'reporte.json').read_text(encoding='utf-8'))
        assert compatible(report['provenance'],provenance(key))
        candidates=list(ParameterGrid(GRIDS[key]))
        for label in [*(f'externo_{k}' for k in range(1,6)),'final']:
            grid=pd.read_csv(folder/f'grid_{label}.csv')
            assert len(grid)==len(candidates)*5
            assert not grid.duplicated(['candidate','inner_fold']).any()
            assert np.isfinite(grid[['RMSE','MAE','MAPE (%)','R²']]).all().all()
            assert grid.shared_students.eq(0).all()
            assert set(grid.candidate)==set(range(1,len(candidates)+1))
            assert grid.groupby('candidate').inner_fold.apply(lambda v:set(v)=={1,2,3,4,5}).all()
            chosen=candidates[int(grid.groupby('candidate').RMSE.mean().idxmin())-1]
            expected=report['best_params'] if label=='final' else report['fold_audit'][int(label[-1])-1]['best_params']
            assert chosen==expected
        exported=pd.read_csv(folder/'train_predictions.csv.gz')
        np.testing.assert_array_equal(exported.fila_fuente,train.fila_fuente)
        for k,(fi,va) in enumerate(folds,1):
            model=joblib.load(BOOK/'modelos_preentrenados/scopus'/key/f'fold_{k}.joblib')
            restored=predict(model,train.iloc[va])
            np.testing.assert_allclose(restored,exported.prediccion.iloc[va],rtol=0,atol=1e-10)
            prep=model.named_steps['preprocesamiento']
            if key in ['xbart','kernel_ridge']:
                for step in ['num_log','num_plain']:
                    assert prep.named_transformers_[step].named_steps['scaler'].n_samples_seen_==len(fi)
            else:
                imputer=(prep.named_steps['impute'] if key=='catboost' else prep).named_transformers_['num']
                np.testing.assert_allclose(imputer.statistics_,np.nanmedian(train.iloc[fi][NUMERIC],axis=0))
            if key=='kernel_ridge':
                np.testing.assert_allclose(model.named_steps['modelo'].transformer_.mean_,[train.iloc[fi][TARGET].mean()])
            if key=='copilot':
                assert len(model.named_steps['modelo'].model_.pilot_trees)==2
            scores=metrics(train.iloc[va][TARGET],restored)
            stored=json.loads((folder/f'externo_{k}.json').read_text(encoding='utf-8'))['metrics']
            for m,v in scores.items():np.testing.assert_allclose(v,stored[m],atol=1e-10,rtol=0)
        test_table=pd.read_csv(folder/'test_predictions.csv.gz')
        np.testing.assert_array_equal(test_table.fila_fuente,test.fila_fuente)
        for m,v in metrics(test[TARGET],test_table.prediccion).items():
            np.testing.assert_allclose(v,report['test'][m],atol=1e-10,rtol=0)
        checked.append({'model':key,'external_folds':5,'inner_fits':len(candidates)*5*6,
                        'oof_restored':True,'selection_train_only':True,'preparation_fit_rows_verified':True})
    write_json(ROOT/('auditoria_parcial.json' if partial else 'auditoria_final.json'),{'checked':checked})
    print(json.dumps(checked,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--partial',action='store_true')
    audit(p.parse_args().partial)

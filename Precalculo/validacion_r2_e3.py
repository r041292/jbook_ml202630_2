"""R² de los 18 modelos existentes: CV, test y contrastes por estudiante.

No reentrena ni cambia la selección de hiperparámetros realizada por RMSE.
"""
import sys

import numpy as np
import pandas as pd
from scipy.stats import permutation_test
from statsmodels.stats.multitest import multipletests

from entregable3 import BOOK,OUTPUT,TARGET,GROUP,metrics,source_hashes,write_json
from evaluacion_nuevos_e3 import partitions
from comparacion_seleccionados_e3 import base_report
from finetune_tabpfn25_e3 import sha256

FOLDER=OUTPUT/'validacion_r2'
CLASSIC={'SVM lineal':'svm','Dummy media':'dummy','KNN':'knn','Ridge':'ridge',
         'Lasso':'lasso','Random Forest':'forest','XGBoost':'xgboost'}
OTHER={'logicDT propio (adaptado)':'logicdt','TabPFN 2.5 original':'tabpfn_25',
    'TabPFN 2.5 fine-tuned':'tabpfn_25_finetuned/20261015_091524_448419',
    'RIM (port E3)':'rim','TCR-XGBoost':'tcr_xgboost','TabICLv2':'tabicl_v2',
    'HRT-Boost':'hrt_boost','Kernel Ridge RBF':'scopus/kernel_ridge',
    'CatBoost':'scopus/catboost','XBART (GFR)':'scopus/xbart','coPILOT':'scopus/copilot'}


def read_predictions(split,frame,folds,sources):
    classic_path=OUTPUT/f'clasicos/{split}_predictions.csv.gz'
    canonical_path=OUTPUT/f'{split}.csv.gz'
    classic=pd.read_csv(classic_path)
    canonical=pd.read_csv(canonical_path)
    assert len(classic)==len(frame)
    np.testing.assert_allclose(canonical[TARGET],frame[TARGET],atol=1e-12,rtol=0)
    sources.update([classic_path,canonical_path])
    result={name:classic[col].to_numpy(float) for name,col in CLASSIC.items()}
    for name,col in [('SVM lineal','svm'),('Dummy media','dummy')]:
        np.testing.assert_allclose(result[name],canonical[col],atol=1e-12,rtol=0)
    if split=='train':np.testing.assert_array_equal(classic.fold,folds)
    for name,folder in OTHER.items():
        path=OUTPUT/folder/f'{split}_predictions.csv.gz'
        if name=='TabPFN 2.5 fine-tuned' and split=='train':
            # Esos pesos ya vieron todo train; no atribuirles OOF independiente.
            continue
        table=pd.read_csv(path)
        sources.add(path)
        assert len(table)==len(frame)
        np.testing.assert_allclose(table[TARGET],frame[TARGET],atol=1e-12,rtol=0)
        np.testing.assert_array_equal(table.periodo,frame.periodo)
        if 'fila_fuente' in table:np.testing.assert_array_equal(table.fila_fuente,frame.fila_fuente)
        if split=='train':np.testing.assert_array_equal(table.fold,folds)
        pred=table.prediccion.to_numpy(float)
        if name=='TabPFN 2.5 original':pred=pred.astype(np.float32).astype(float)
        assert np.isfinite(pred).all()
        result[name]=pred
    return result


def contrast_r2(y,new,old,groups,reference=False):
    codes,ids=pd.factorize(groups,sort=False)
    aggregate=lambda v:np.bincount(codes,weights=v,minlength=len(ids))
    a,b=aggregate((y-new)**2),aggregate((y-old)**2)
    sst=float(np.sum((y-y.mean())**2))
    assert sst>0
    # Contraste DIRECTO en unidades R²: positivo favorece al candidato.
    p=None if reference else float(permutation_test((b-a,),
        lambda x,axis:np.sum(x,axis=axis)/sst,permutation_type='samples',
        vectorized=True,n_resamples=99999,batch=512,alternative='two-sided',
        rng=np.random.default_rng(42)).pvalue)
    n,sy,sy2=aggregate(np.ones(len(y))),aggregate(y),aggregate(y*y)
    rng=np.random.default_rng(42)
    delta_draws,r2_draws=[],[]
    for start in range(0,10000,512):
        ix=rng.integers(len(ids),size=(min(512,10000-start),len(ids)))
        counts=n[ix].sum(axis=1)
        total=sy2[ix].sum(axis=1)-sy[ix].sum(axis=1)**2/counts
        assert (total>0).all()
        sa,sb=a[ix].sum(axis=1),b[ix].sum(axis=1)
        delta_draws.extend((sb-sa)/total)
        r2_draws.extend(1-sa/total)
    return {'R2_test':metrics(y,new)['R²'],
        'delta_R2':float((b.sum()-a.sum())/sst),'p_bilateral':p,
        'IC95_delta_inferior':float(np.quantile(delta_draws,.025)),
        'IC95_delta_superior':float(np.quantile(delta_draws,.975)),
        'IC95_R2_inferior':float(np.quantile(r2_draws,.025)),
        'IC95_R2_superior':float(np.quantile(r2_draws,.975))}


def status(delta,p):
    if pd.isna(p):return 'Referencia'
    if p>=.05:return 'No significativa'
    return 'Mejora significativa' if delta>0 else 'Deterioro significativo'


def markdown(table):
    lines=['| Método | R² test | Δ R² vs. SVM | p bilateral | p Holm17 |',
           '|---|---:|---:|---:|---:|']
    for row in table.to_dict('records'):
        fmt=lambda v:'—' if pd.isna(v) else f'{v:.5f}'
        lines.append(f"| {row['Modelo']} | {row['R2_test']:.6f} | {row['delta_R2']:+.6f} | "
                     f"{fmt(row['p_bilateral'])} | {fmt(row['p_Holm_17_vs_SVM'])} |")
    return '\n'.join(lines)


def build():
    train,test,fold_pairs,audit=partitions()
    base_report()
    sources=set()
    folds=np.zeros(len(train),dtype=int)
    for k,(_,va) in enumerate(fold_pairs,1):folds[va]=k
    test_pred=read_predictions('test',test,folds,sources)
    train_pred=read_predictions('train',train,folds,sources)
    old_path=OUTPUT/'resumen_completo/modelos.csv'
    old=pd.read_csv(old_path).set_index('Modelo')
    sources.add(old_path)
    assert set(test_pred)==set(old.index) and len(test_pred)==18
    y=test[TARGET].to_numpy(float)
    svm=test_pred['SVM lineal']
    rows=[]
    cv_rows,fold_rows=[],[]
    for name,pred in test_pred.items():
        score=metrics(y,pred)
        np.testing.assert_allclose(score['RMSE'],old.loc[name,'RMSE_test'],atol=1e-12,rtol=0)
        np.testing.assert_allclose(score['R²'],1-score['RMSE']**2/np.var(y),atol=1e-12,rtol=0)
        row={'Modelo':name,'Referencia':'SVM lineal',**contrast_r2(y,pred,svm,test[GROUP],name=='SVM lineal')}
        if name!='SVM lineal':
            np.testing.assert_allclose(row['p_bilateral'],old.loc[name,'p_bilateral'],atol=1e-12,rtol=0)
        rows.append(row)
        if name in train_pred:
            values=train_pred[name]
            fold_scores=[]
            for k,(_,va) in enumerate(fold_pairs,1):
                r2=metrics(train.iloc[va][TARGET],values[va])['R²']
                fold_scores.append(r2)
                fold_rows.append({'Modelo':name,'Fold':k,'R2_validacion_externa':r2,'n':len(va)})
            cv_rows.append({'Modelo':name,'R2_media_CV':float(np.mean(fold_scores)),
                'R2_SD_CV_ddof0':float(np.std(fold_scores)),'R2_OOF_reunido':metrics(train[TARGET],values)['R²'],
                'R2_test':score['R²'],'CV_estado':'5 folds externos por estudiante'})
        else:
            cv_rows.append({'Modelo':name,'R2_media_CV':None,'R2_SD_CV_ddof0':None,'R2_OOF_reunido':None,
                'R2_test':score['R²'],'CV_estado':'No disponible: pesos finales ajustados con todo train; no OOF independiente'})
        print(f'{name}: R2={score["R²"]:.6f}',flush=True)
    table=pd.DataFrame(rows).sort_values('R2_test',ascending=False).reset_index(drop=True)
    assert list(table.Modelo)==list(old.sort_values('RMSE_test').index)
    nonref=table.Modelo.ne('SVM lineal')
    table['p_Holm_17_vs_SVM']=np.nan
    table.loc[nonref,'p_Holm_17_vs_SVM']=multipletests(table.loc[nonref,'p_bilateral'],method='holm')[1]
    np.testing.assert_allclose(table.loc[nonref,'p_Holm_17_vs_SVM'],
        old.loc[table.loc[nonref,'Modelo'],'p_Holm_17_vs_SVM'],atol=1e-12,rtol=0)
    extra=[]
    scopus_path=OUTPUT/'scopus/contrastes_pareados.csv'
    previous=pd.read_csv(scopus_path)
    sources.add(scopus_path)
    for name in ['Kernel Ridge RBF','CatBoost','XBART (GFR)','coPILOT']:
        row={'Modelo':name,'Referencia':'XGBoost',**contrast_r2(y,test_pred[name],test_pred['XGBoost'],test[GROUP])}
        prior=previous[previous.Modelo.eq(name) & previous.Referencia.eq('XGBoost') & previous.metrica.eq('R²')].iloc[0]
        np.testing.assert_allclose(row['p_bilateral'],prior.p_bilateral,atol=1e-12,rtol=0)
        np.testing.assert_allclose([row['IC95_delta_inferior'],row['IC95_delta_superior']],
            [prior['IC_2.5%'],prior['IC_97.5%']],atol=1e-12,rtol=0)
        extra.append(row)
    extra=pd.DataFrame(extra)
    extra['p_Holm_4_vs_XGBoost']=multipletests(extra.p_bilateral,method='holm')[1]
    adjusted=multipletests(np.r_[table.loc[nonref,'p_bilateral'],extra.p_bilateral],method='holm')[1]
    table['p_Holm_global_21']=np.nan
    table.loc[nonref,'p_Holm_global_21']=adjusted[:17]
    extra['p_Holm_global_21']=adjusted[17:]
    np.testing.assert_allclose(table.loc[nonref,'p_Holm_global_21'],
        old.loc[table.loc[nonref,'Modelo'],'p_Holm_global_21'],atol=1e-12,rtol=0)
    for col,suffix in [('p_bilateral','sin_correccion'),('p_Holm_17_vs_SVM','Holm17'),('p_Holm_global_21','Holm21')]:
        table['significancia_'+suffix]=[status(d,p) for d,p in zip(table.delta_R2,table[col])]
    FOLDER.mkdir(parents=True,exist_ok=True)
    for filename,frame in [('modelos_r2.csv',table),('contrastes_r2_vs_xgboost.csv',extra),
        ('validacion_cruzada_r2.csv',pd.DataFrame(cv_rows)),('folds_r2.csv',pd.DataFrame(fold_rows))]:
        frame.to_csv(FOLDER/filename,index=False,encoding='utf-8-sig')
    note='''# Validación completa con R² — E3

18 modelos actuales en el mismo test temporal202530:188 estudiantes. Mayor R²
es mejor. Delta=modelo−SVM: positivo indica mejora. Permutación bilateral directa
de la diferencia R² por estudiante99999 y bootstrap pareado10000; semilla42.
IC95% marginales de R² y su diferencia en modelos_r2.csv. Holm17 corresponde
a17 contrastes frente a SVM. Holm21 incorpora4 pares adicionales frente a XGBoost.

'''+markdown(table)+'''

## Resultado e interpretación

TabICLv2 tiene el mayor R² test:0.4647742613 frente a SVM0.4285425650;
diferencia+0.0362316963. Nominal p0.02624; Holm17=.41984; Holm21=.47232.
Ningún modelo mejora significativamente a SVM después de Holm. Dummy es
significativamente peor. R² puede ser negativo; no es el cuadrado de la
correlación entre nota y predicción.

Los p-valores y el ranking coinciden con RMSE por una razón matemática:
RMSE=sqrt(SSE/n) y R²=1−SSE/SST. Al comparar sobre las mismas observaciones,
n y SST son comunes. La diferencia R² es (SSE_referencia−SSE_modelo)/SST.
El intercambio pareado por estudiante produce el mismo contraste bilateral;
no son dos evidencias independientes. Se verificó la igualdad de los21
p-valores con los existentes y las mismas correcciones de Holm.

## Validación cruzada y alcance

validacion_cruzada_r2.csv contiene media y SD(ddof0) de los5 folds externos,
R² OOF reunido y R² temporal. folds_r2.csv detalla85 evaluaciones externas
de17 modelos. Media de R² por fold y R² de todas las OOF son cantidades
diferentes; no deben confundirse con el resultado temporal.

TabPFN ajustado tiene R² test, pero no una nueva CV OOF independiente: los
pesos finales ya se ajustaron con todo train. Sus campos de CV quedan vacíos.
No se reconstruye una CV ficticia con esos pesos.

Esta evaluación usa los modelos/grillas ya seleccionados por RMSE. No se
reoptimizaron hiperparámetros por R². En un mismo fold, maximizar R² equivale
a minimizar RMSE; promediar métricas entre folds sí puede cambiar la selección,
porque cambian las varianzas de y y la ponderación implícita de cada fold.

El test reutilizado mantiene carácter exploratorio; IC/p condicionales a
los modelos, sin variabilidad de reentrenamiento. No rechazar H0 no prueba
equivalencia. Datos, variables, grupos, modelos y sus resultados previos intactos.

[Definición oficial de R²](https://scikit-learn.org/stable/modules/model_evaluation.html#r2-score).
'''
    (FOLDER/'resumen.md').write_text(note,encoding='utf-8')
    write_json(FOLDER/'reporte.json',{'models':table.to_dict('records'),'cv':cv_rows,
        'vs_xgboost':extra.to_dict('records'),'partition':audit,'model_count':18,
        'family_vs_svm':17,'family_global':21,'permutations':99999,'bootstrap':10000,'seed':42,
        'hyperparameter_selection':'RMSE original; no reoptimización','training_performed':False,
        'provenance':{**source_hashes(),**{str(p.relative_to(BOOK)):sha256(p) for p in sources},
            'validacion_r2_e3.py':sha256(BOOK/'validacion_r2_e3.py')}})
    print(markdown(table))
    return table


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    build()

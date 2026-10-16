"""Consolidar las tres etapas y la corrección acumulada completa, sin entrenar."""
import json
import numpy as np
import pandas as pd

from entregable3 import OUTPUT,TARGET,metrics,write_json
from evaluacion_nuevos_e3 import partitions
from comparacion_seleccionados_e3 import ORDER,LABELS,provenance


def run():
    _,test,_,_=partitions()
    reports={key:json.loads((OUTPUT/key/'reporte.json').read_text(encoding='utf-8')) for key in ORDER}
    for key,report in reports.items():
        if report['provenance']!=provenance(key):
            raise ValueError(f'Resultado desactualizado: {key}')
    final=reports[ORDER[-1]]
    family={row['modelo']:row for row in final['family_vs_svm']}
    rows=[]
    selected={'SVM lineal','XGBoost','TabPFN 2.5 original',*LABELS.values()}
    for row in final['comparison_test']:
        if row['Modelo'] not in selected:
            continue
        item=dict(row)
        lookup='TabPFN original' if row['Modelo']=='TabPFN 2.5 original' else row['Modelo']
        if lookup in family:
            item['delta_RMSE_vs_SVM']=family[lookup]['diferencia_ajustado_menos_referencia']
            item['p_bilateral_vs_SVM']=family[lookup]['p_bilateral']
            item['p_Holm_familia_completa']=family[lookup]['p_Holm_familia_conocida']
        for key,label in LABELS.items():
            if row['Modelo']==label:
                item['RMSE_media_CV']=reports[key]['cv'][0]['media_cv']
        rows.append(item)
    folder=OUTPUT/'seleccionados'
    folder.mkdir(parents=True,exist_ok=True)
    table=pd.DataFrame(rows).sort_values('RMSE')
    table.to_csv(folder/'comparacion_final.csv',index=False)
    write_json(folder/'resumen.json',{'evaluation_order':ORDER,'comparison':rows,
        'family_size':len(family),'family_vs_svm':list(family.values()),
        'statistics':final['statistics'],'sources':{key:r['provenance'] for key,r in reports.items()}})
    # Diagnóstico descriptivo por subgrupos: los pesos TCR no eliminan casos raros.
    canonical=pd.read_csv(OUTPUT/'test.csv.gz')
    classical=pd.read_csv(OUTPUT/'clasicos/test_predictions.csv.gz')
    predictions={'SVM lineal':canonical.svm.to_numpy(float),'XGBoost':classical.xgboost.to_numpy(float),
        'TabPFN original':pd.read_csv(OUTPUT/'tabpfn_25/test_predictions.csv.gz').prediccion.to_numpy().astype(np.float32).astype(float)}
    predictions.update({LABELS[key]:pd.read_csv(OUTPUT/key/'test_predictions.csv.gz').prediccion.to_numpy(float) for key in ORDER})
    subgroups=[]
    for field in ['programa_en_matricula','division_en_matricula']:
        for value,frame in test.groupby(field,dropna=False):
            ix=frame.index.to_numpy()
            for label,pred in predictions.items():
                subgroups.append({'variable':field,'subgrupo':str(value),'n':len(ix),
                                  'Modelo':label,**metrics(frame[TARGET],pred[ix])})
    pd.DataFrame(subgroups).to_csv(folder/'metricas_subgrupos_descriptivas.csv',index=False)
    print(table.to_string(index=False))
    print('Familia completa:',len(family),'candidatos frente a SVM.')
    return table


if __name__=='__main__':
    run()

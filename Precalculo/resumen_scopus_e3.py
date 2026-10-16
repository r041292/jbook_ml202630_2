"""Consolidar los 18 modelos y representar contrastes sin mezclar escalas."""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from entregable3 import BOOK,OUTPUT
from evaluar_scopus_e3 import ROOT,compare
from finetune_tabpfn25_e3 import sha256


def markdown_table(frame):
    def value(x):
        if pd.isna(x):return '—'
        if isinstance(x,(float,np.floating)):return f'{x:.6f}'
        return str(x).replace('|','\\|')
    lines=['| '+' | '.join(frame.columns)+' |','| '+' | '.join(['---']*len(frame.columns))+' |']
    lines += ['| '+' | '.join(value(x) for x in row)+' |' for row in frame.itertuples(index=False,name=None)]
    return '\n'.join(lines)


def build():
    report=compare()
    current=pd.DataFrame(report['test'])
    contrasts=pd.DataFrame(report['contrasts'])
    rmse=contrasts[contrasts.metrica.eq('RMSE')]
    old=pd.read_csv(ROOT/'historicos_Holm_global_21.csv')
    old=old.drop(columns=['p_Holm_13'])
    baseline=pd.read_csv(OUTPUT/'seleccionados/listado_completo_significancia.csv')
    old=pd.concat([old,baseline[baseline.p_bilateral.isna()].drop(columns=['p_Holm_13'])],ignore_index=True)
    rows=[]
    for row in rmse[rmse.Referencia.eq('SVM lineal')].to_dict('records'):
        rows.append({'Modelo':row['Modelo'],'RMSE_test':float(current.loc[current.Modelo.eq(row['Modelo']),'RMSE'].iloc[0]),
            'delta_RMSE_vs_SVM':row['diferencia_ajustado_menos_referencia'],'p_bilateral':row['p_bilateral'],
            'p_Holm_global_21':row['p_Holm_global_21']})
    complete=pd.concat([old,pd.DataFrame(rows)],ignore_index=True).sort_values('RMSE_test')
    assert len(complete)==18 and complete.Modelo.is_unique
    complete.to_csv(ROOT/'listado_completo_18_modelos.csv',index=False)
    fig,axes=plt.subplots(1,2,figsize=(14,5),constrained_layout=True)
    for ax,reference in zip(axes,['SVM lineal','XGBoost']):
        subset=rmse[rmse.Referencia.eq(reference)].sort_values('diferencia_ajustado_menos_referencia')
        positions=np.arange(len(subset))
        for pos,row in zip(positions,subset.to_dict('records')):
            point=row['diferencia_ajustado_menos_referencia']
            ax.plot([row['IC_2.5%'],row['IC_97.5%']],[pos,pos],color='#326d9c',linewidth=2)
            ax.scatter([point],[pos],color='#20806b' if point<0 else '#bc5535',s=55,zorder=3)
        ax.set_yticks(positions,subset.Modelo)
        ax.invert_yaxis()
        ax.axvline(0,color='#555',linestyle='--')
        ax.set_title(f'Diferencia de RMSE frente a {reference}')
        ax.set_xlabel('Candidato − referencia; izquierda favorece al candidato')
        ax.grid(axis='x',alpha=.2)
    fig.suptitle('Estimaciones e IC95% marginales por estudiante; test temporal 202530')
    fig.savefig(ROOT/'diferencias_rmse.png',dpi=160)
    plt.close(fig)
    execution={'parallel_code_sha256':sha256(BOOK/'paralelo_scopus_e3.py'),
        'note':'Procesos independientes, 6 trabajadores de un hilo. Fit/predict/tune idénticos al evaluador auditado.',
        'summary_code_sha256':sha256(BOOK/'resumen_scopus_e3.py')}
    (ROOT/'ejecucion.json').write_text(json.dumps(execution,indent=2,ensure_ascii=False),encoding='utf-8')
    markdown=['# Comparación Scopus E3','',
        'Mismo test temporal202530:188 estudiantes. Delta negativo de RMSE favorece al candidato.',
        'Los resultados y contrastes son exploratorios por reutilización del test.','',
        markdown_table(current),'','## Contrastes pareados RMSE','',
        markdown_table(rmse),'','## Todos los modelos probados','',
        markdown_table(complete),'',
        'Holm global21:13 pares históricos frente a SVM +4 nuevos frente a SVM +4 nuevos frente a XGBoost.',
        'RMSE y R² comparten contraste SSE. Los IC95% son marginales; no simultáneos.',
        'La interpretación exige revisar dirección y p corregido; no rechazar H0 no demuestra equivalencia.']
    (ROOT/'resumen.md').write_text('\n'.join(markdown),encoding='utf-8')
    print(complete.to_string(index=False))
    # Panorama frente a SVM: Holm17; mantiene aparte la familia global21.
    from resumen_completo_e3 import build as build_overview
    build_overview()


if __name__=='__main__':build()

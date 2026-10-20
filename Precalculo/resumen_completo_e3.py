"""Panorama de los 18 métodos: RMSE temporal y significancia frente a SVM."""
import json
import sys

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

from entregable3 import BOOK,OUTPUT,write_json
from finetune_tabpfn25_e3 import sha256

FOLDER=OUTPUT/'resumen_completo'


def interpretation(delta,p):
    if pd.isna(p):return 'Referencia'
    if p>=.05:return 'No significativa'
    return 'Mejora significativa' if delta<0 else 'Deterioro significativo'


def display_table(table):
    rows=['| Método | RMSE test | Δ RMSE vs. SVM | p sin corrección | p Holm (17 vs. SVM) |',
          '|---|---:|---:|---:|---:|']
    for r in table.to_dict('records'):
        probability=lambda x:'—' if pd.isna(x) else f'{x:.5f}'
        rows.append(f"| {r['Modelo']} | {r['RMSE_test']:.6f} | {r['delta_RMSE_vs_SVM']:+.6f} | "
                    f"{probability(r['p_bilateral'])} | {probability(r['p_Holm_17_vs_SVM'])} |")
    return '\n'.join(rows)


def build():
    source=OUTPUT/'scopus/listado_completo_18_modelos.csv'
    contrasts_path=OUTPUT/'scopus/contrastes_pareados.csv'
    table=pd.read_csv(source).sort_values('RMSE_test').reset_index(drop=True)
    assert len(table)==18 and table.Modelo.is_unique
    baseline=table.Modelo.eq('SVM lineal')
    assert baseline.sum()==1
    mask=~baseline
    assert table.loc[mask,'p_bilateral'].notna().all()
    assert table.loc[baseline,'p_bilateral'].isna().all()
    svm=float(table.loc[baseline,'RMSE_test'].iloc[0])
    np.testing.assert_allclose(table.delta_RMSE_vs_SVM,table.RMSE_test-svm,atol=1e-12,rtol=0)
    assert table.loc[mask,'p_bilateral'].between(0,1).all()
    table['p_Holm_17_vs_SVM']=np.nan
    table.loc[mask,'p_Holm_17_vs_SVM']=multipletests(table.loc[mask,'p_bilateral'],method='holm')[1]
    # Verificar también la familia global21 informada en la etapa anterior.
    contrasts=pd.read_csv(contrasts_path)
    extra=contrasts.loc[contrasts.Referencia.eq('XGBoost') & contrasts.metrica.eq('RMSE'),'p_bilateral']
    assert len(extra)==4
    joint=np.r_[table.loc[mask,'p_bilateral'],extra]
    np.testing.assert_allclose(table.loc[mask,'p_Holm_global_21'],
                               multipletests(joint,method='holm')[1][:17],atol=1e-12,rtol=0)
    for pcol,label in [('p_bilateral','sin_correccion'),('p_Holm_17_vs_SVM','Holm_17_vs_SVM'),
                       ('p_Holm_global_21','Holm_global_21')]:
        table['significancia_'+label]=[interpretation(d,p) for d,p in zip(table.delta_RMSE_vs_SVM,table[pcol])]
    FOLDER.mkdir(parents=True,exist_ok=True)
    table.to_csv(FOLDER/'modelos.csv',index=False,encoding='utf-8-sig')
    note='''# Panorama completo de modelos — Entregable 3

18 métodos ordenados de menor a mayor RMSE. Mismo test temporal202530:188
estudiantes; datos reales sin aumento, mismas15 variables y objetivo
nota_primer_parcial. SVM lineal es la referencia. Delta=candidato−SVM:
negativo indica menor error; positivo indica deterioro.

Los p-valores son bilaterales por permutación pareada por estudiante99999,
semilla42. La tabla corrige con Holm los17 contrastes frente a SVM, incluido
Dummy. El CSV conserva además Holm global21: esos17 más4 contrastes nuevos
frente a XGBoost. Ambas familias están explícitamente identificadas.

'''+display_table(table)+'''

## Interpretación

- TabICLv2 tiene el menor RMSE puntual y es la única mejora nominalmente
  significativa frente a SVM: p0.02624. Con Holm17, p0.41984; con Holm21,
  p0.47232. No conserva significancia tras corregir.
- Ningún método mejora significativamente frente a SVM después de Holm.
- Dummy es significativamente peor: p0.00002 y Holm17=0.00034
  (Holm21=0.00042). Revisar siempre la dirección del delta.
- Kernel Ridge y CatBoost mejoran puntualmente a XGBoost, sin significancia;
  sus contrastes frente a XGBoost están en ../scopus/contrastes_pareados.csv.
- RMSE y R² comparten el contraste sobre SSE en el mismo test; no se tratan
  como hipótesis independientes.

La inferencia sigue siendo exploratoria por el uso repetido del test y es
condicional a los modelos entrenados, sin variabilidad de reentrenamiento.
No rechazar H0 no demuestra equivalencia. Los resultados describen las
implementaciones evaluadas: logicDT/RIM adaptados, XBART GFR de stochtree,
KRR con solución exacta y coPILOT de los autores.

No se reentrena ni se modifica ningún modelo al generar este resumen.
Los archivos históricos de14 modelos y su Holm13 se preservan como historial.

[Validación completa con R²: test, CV e intervalos](../validacion_r2/resumen.md).
'''
    (FOLDER/'resumen.md').write_text(note,encoding='utf-8')
    # Validaciones de los casos que determinan la interpretación del resumen.
    np.testing.assert_allclose(table.loc[table.Modelo.eq('TabICLv2'),'p_Holm_17_vs_SVM'],[.41984])
    np.testing.assert_allclose(table.loc[table.Modelo.eq('Dummy media'),'p_Holm_17_vs_SVM'],[.00034])
    assert not ((table.delta_RMSE_vs_SVM<0) & (table.p_Holm_17_vs_SVM<.05)).any()
    write_json(FOLDER/'resumen.json',{'models':table.where(pd.notna(table),None).to_dict('records'),
        'model_count':18,'reference':'SVM lineal','family_vs_svm':17,'family_global':21,
        'sources_sha256':{str(p.relative_to(BOOK)):sha256(p) for p in [source,contrasts_path]},
        'generator_sha256':sha256(BOOK/'resumen_completo_e3.py'),
        'training_performed':False})
    print(display_table(table))
    return table


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    build()

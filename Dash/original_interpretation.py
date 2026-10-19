"""SHAP por permutaciones y LIME solo para el líder CV de Originales.

La explicación se prepara fuera del servidor, sobre el pipeline completo.
No aplica TreeSHAP a Kernel Ridge/SVR ni atribuye exactitud al estimador SHAP.
"""
import json
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import plotly.express as px
from dash import Input, Output, dcc, html
from threadpoolctl import threadpool_limits

from lime_xgboost import TabularBridge, explain_xgboost
from shap_xgboost import summary_plot, waterfall, importance, local_rows
from model_timing import TimingRun, file_hash
from lazy_content import defer_details


def permutation_values(predict, observations, backgrounds, *, seed=42):
    """Promedio de caminos aleatorios antitéticos; aditividad por telescopado.

    predict recibe arrays codificados del puente, no predictores transformados.
    La función sirve también para pruebas analíticas sin entrenar modelos.
    """
    x,b=np.asarray(observations),np.asarray(backgrounds)
    n,p=x.shape
    full=np.asarray(predict(x),float)
    base_predictions=np.asarray(predict(b),float)
    rng=np.random.default_rng(seed)
    accumulated=np.zeros((n,p)); half=np.zeros((n,p))
    for i,background in enumerate(b):
        order=rng.permutation(p)
        for path in (order,order[::-1]):
            current=np.tile(background,(n,1)); previous=np.full(n,base_predictions[i])
            for step,j in enumerate(path):
                current[:,j]=x[:,j]
                value=full if step==p-1 else np.asarray(predict(current),float)
                contribution=value-previous
                accumulated[:,j]+=contribution
                if i<len(b)//2: half[:,j]+=contribution
                previous=value
    values=accumulated/(2*len(b))
    first=half/(2*(len(b)//2))
    second=(accumulated-half)/(2*(len(b)-len(b)//2))
    return values,float(base_predictions.mean()),full,float(np.abs(first-second).mean())


def prepare(directory,cache,book):
    directory,cache,book=Path(directory),Path(cache),Path(book)
    active=json.loads((directory/'completo.json').read_text(encoding='utf-8'))
    key,name=active['best_key'],active['best_name']
    model=joblib.load(directory/'best.joblib')
    train,test=[pd.read_csv(cache/f'{p}.csv.gz') for p in ('train','test')]
    columns=list(model.feature_names_in_)
    frame=pd.concat([train,test],ignore_index=True)
    bridge=TabularBridge(train,columns,{})
    encoded=bridge.encode(frame)
    background_indices=np.random.default_rng(42).choice(len(train),32,replace=False)
    backgrounds=bridge.background[background_indices]
    run=TimingRun(name+' · SHAP aproximado por permutaciones y LIME',{
        'script_sha256':file_hash(__file__),'model_sha256':file_hash(directory/'best.joblib'),
        'features':columns,'data':'Train1309+test188; sin IDs en evidencia',
        'background':'32filas completas de train, sin reemplazo; semilla42; referencia interventional empírica',
        'configuration':{'paths':64,'antithetic':True,'seed':42,'batch':256,'features':15,
                         'lime_samples':1000,'lime_neighborhood':'empirical'},
        'scope':'Sin fit del modelo global; LIME ajusta sustitutos Ridge locales. CPU, un hilo, sin GPU.'})
    status='fallida'
    calls=0
    try:
        def predict(values):
            nonlocal calls
            with run.measure('Inferencia',f'{name} / máscaras SHAP lote{calls}',len(values),
                             repetitions=1,warmup=0):
                calls+=1
                return np.concatenate([model.predict(bridge.decode(values[start:start+256]))
                                       for start in range(0,len(values),256)])
        with threadpool_limits(limits=1),warnings.catch_warnings(),run.measure('Explicación SHAP','64caminos/32referencias · completo',len(frame)):
            warnings.filterwarnings('ignore',message='Found unknown categories',category=UserWarning)
            values,base,prediction,dispersion=permutation_values(predict,encoded,backgrounds)
        saved=pd.read_csv(directory/'test.csv.gz')[key]
        np.testing.assert_allclose(prediction[len(train):],saved,atol=1e-10,rtol=0)
        np.testing.assert_allclose(base+values.sum(axis=1),prediction,atol=1e-10,rtol=0)
        actual=frame['nota_primer_parcial'].to_numpy()
        error=np.abs(prediction[len(train):]-actual[len(train):])
        cases=[int(np.argmin(error)),int(np.argmax(error))]
        lime=[]
        # Medir todos los predict/fit de los sustitutos antes de ejecutarlos.
        from sklearn.pipeline import Pipeline
        from sklearn.linear_model import Ridge
        from unittest.mock import patch
        def measured(original,stage):
            def wrapper(estimator,x,*args,**kwargs):
                with run.measure(stage,f'{name} / LIME / {type(estimator).__name__}',len(x)):
                    return original(estimator,x,*args,**kwargs)
            return wrapper
        with threadpool_limits(limits=1),patch.object(Pipeline,'predict',measured(Pipeline.predict,'Inferencia')),\
             patch.object(Ridge,'fit',measured(Ridge.fit,'Entrenamiento/refit · sustituto LIME')),\
             patch.object(Ridge,'predict',measured(Ridge.predict,'Inferencia · sustituto LIME')):
            for index in cases:
                explanation=explain_xgboost(model,train,test.iloc[[index]],{},1000,'empirical')
                explanation['rows']=explanation['rows'].to_dict('records')
                explanation['case']=index
                lime.append(explanation)
        result={'key':key,'name':name,'values':values.tolist(),'base':base,'prediction':prediction.tolist(),
                'n_train':len(train),'n_test':len(test),'features':columns,'cases':cases,'lime':lime,
                'half_difference_mean_abs':dispersion,'paths':64,'background_rows':32,
                'analysis_run':run.run_id,'model_sha256':file_hash(directory/'best.joblib'),
                'test_sha256':file_hash(directory/'test.csv.gz'),'method':'Permutation SHAP aproximado, pipeline completo',
                'max_additivity_residual':float(np.abs(base+values.sum(axis=1)-prediction).max())}
        (directory/'explanations.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
        status='completa';return result
    finally: run.finish(status)


def create_section(app,ui,directory):
    directory=Path(directory)
    data=json.loads((directory/'explanations.json').read_text(encoding='utf-8'))
    if file_hash(directory/'best.joblib')!=data['model_sha256'] or file_hash(directory/'test.csv.gz')!=data['test_sha256']:
        raise RuntimeError('Las explicaciones de Originales no corresponden al ganador/predicciones activos.')
    train,test=ui['TRAIN'],ui['TEST']
    bridge=TabularBridge(train,data['features'],ui['LABELS'])
    frame=pd.concat([train,test],ignore_index=True)
    result={'values':np.asarray(data['values']),'base':np.full(len(frame),data['base']),
            'predictions':np.asarray(data['prediction']),'actual':frame[ui['TARGET']].to_numpy(),
            'features':data['features'],'transformed':bridge.decode(bridge.encode(frame))}
    md,table,card=ui['md'],ui['table'],ui['card']
    layout=html.Div([
        ui['title']('INTERPRETABILIDAD DEL LÍDER CV',f'SHAP y LIME · {data["name"]}',
                    'Modelo con menor RMSE medio de CV externa; no ganador estadístico confirmado.'),
        md('**SHAP aproximado por permutaciones sobre el pipeline completo.** '
           'Resumen de las 1.497 filas válidas y 15 variables originales, sin muestrear las filas explicadas. '
           'Referencia: 32 filas de train y 64 caminos antitéticos, semilla 42. No se usa TreeSHAP en un modelo kernel. '
           'Las coaliciones sustituyen variables por valores de referencia: pueden romper correlaciones/avance. '
           'No son efectos causales. Train explica el ajuste final, no OOF; test no modifica el modelo ni la referencia.'),
        md(f'Diferencia media absoluta de aportes entre dos mitades de referencias: '
           f'**{data["half_difference_mean_abs"]:.4f} puntos**. Es un diagnóstico de sensibilidad Monte Carlo, '
           'no un IC ni prueba de convergencia. Aditividad verifica coherencia, no exactitud de los Shapley estimados.'),
        html.Div(id='original-shap-result'),
        html.Details([html.Summary('SHAP frente a LIME · metodología y divergencias'),
            dcc.Markdown(r'''Los valores de Shapley se definen mediante

$$\phi_j=\sum_{S\subseteq F\setminus\{j\}}
\frac{|S|!(p-|S|-1)!}{p!}\,[v(S\cup\{j\})-v(S)].$$

Aquí $F$ contiene las $p$ variables y $v(S)$ integra las variables ausentes con la referencia
empírica de train. Los caminos muestreados aproximan esta suma; no enumeran todas las coaliciones.
[Permutaciones y muestreo antitético](https://shap.readthedocs.io/en/stable/generated/shap.PermutationExplainer.html).
''',mathjax=True,className='prose shap-methods',link_target='_blank'),
            md('SHAP promedia contribuciones marginales de coaliciones y descompone aditivamente la predicción '
               'en base+suma de aportes, aunque los Shapley se estiman por muestreo. LIME ajusta un sustituto '
               'lineal ponderado sobre 1.000 filas de vecindario empírico de train, discretizado por cuartiles. '
               'Su intercepto y pesos explican el sustituto, no necesariamente la predicción exacta. '
               'Se reportan R² de fidelidad y brecha. Correlaciones, interacciones, referencia, núcleo y discretización '
               'pueden cambiar el reparto y los signos. Ni una atribución ni un peso LIME es causal. '
               'Solo se explica el líder CV; los selectores de otros modelos no cambian estas explicaciones. '
               '[SHAP](https://arxiv.org/abs/1705.07874) · [LIME](https://arxiv.org/abs/1602.04938).')],className='details'),
    ],className='shap-section')
    @app.callback(Output('original-shap-result','children'),Input('original-program','value'),Input('original-course','value'),
                  Input('original-shap-result','id'))
    def render(program,course,_ready=None):
        selected=ui['subset'](frame,program,course)
        if selected.empty:return ui['notice']('No hay filas para estos filtros.')
        chart=card('Interpretabilidad global · summary plot SHAP aproximado',
            f'{len(selected)} filas. Orden por media |SHAP|. Azul/bajo y rojo/alto solo en numéricas; '
            'categorías grises sin orden; derecha eleva y izquierda reduce la predicción respecto a la base. '
            'Importancias en puntos de nota. Desplaza horizontalmente en pantallas estrechas.',
            summary_plot(result,selected.index.to_numpy(),ui['LABELS']))
        chart.className+=' shap-chart'
        parts=[chart,html.Details([html.Summary('Importancia global y proporción relativa'),
                                 table(importance(result,selected.index.to_numpy(),ui['LABELS']))],className='details'),
               md('Los dos ejemplos siguientes son globales del test: menor y mayor error absoluto, '
                  'selección ilustrativa posterior a evaluación. No cambian con los filtros del resumen global.')]
        for label,index,lime in zip(('Menor error','Mayor error'),data['cases'],data['lime']):
            position=len(train)+index
            rows=local_rows(result,position,ui['LABELS'])
            pred,truth=result['predictions'][position],result['actual'][position]
            chart=card(f'Waterfall SHAP · {label} · Caso {index+1:04d}',
                f'Nota real **{truth:.3f}**, predicha **{pred:.3f}**, error absoluto **{abs(pred-truth):.3f}**. '
                f'Base {data["base"]:.4f} + 15 aportes = {pred:.4f}. Se explica la predicción, no el error ni la causa de la nota.',
                waterfall(result,position,ui['LABELS']))
            chart.className+=' shap-chart';parts.append(chart)
            top=rows.head(3)
            parts.append(md('**Mayores aportes:** '+', '.join(f'{r.Variable} ({r["SHAP (puntos)"]:+.3f})' for _,r in top.iterrows())+
                '. Las diferencias de estas contribuciones describen por qué el modelo predice distinto; '
                'no explican causalmente la discrepancia con la nota observada.'))
            lime_rows=pd.DataFrame(lime['rows'])
            lime_rows['Variable']=lime_rows.Variable.map(lambda name:ui['LABELS'].get(name,name))
            parts.extend([html.Details([html.Summary(f'Caso{index+1:04d} · valores y SHAP completos'),table(rows)],className='details'),
                html.Details([html.Summary(f'LIME · mismo caso {index+1:04d}'),
                    md(f'Predicción {lime["prediction"]:.4f}; sustituto {lime["local_prediction"]:.4f}; '
                       f'brecha {lime["absolute_gap"]:.4f}; fidelidad R² = {lime["fidelity"]}. '
                       'Intercepto+suma pesos reproduce LIME, no necesariamente el modelo. '
                       'Fidelidad menor que 0,5 o gran brecha exigen cautela; no es R² de test.'),
                    md(f'**Distingue los dos errores:** el error predictivo frente a la nota real es '
                       f'**{abs(pred-truth):.3f} puntos**; la brecha de LIME frente al modelo es '
                       f'**{lime["absolute_gap"]:.3f} puntos**. Un R² local alto no garantiza que '
                       'LIME aproxime bien la predicción individual. SHAP llega al modelo por aditividad, '
                       'pero sus aportes siguen siendo aproximaciones de Shapley.'),
                    card('Aportes de LIME · sustituto local',
                         'Pesos de las diez condiciones de mayor magnitud, no SHAP ni coeficientes globales.',
                         px.bar(lime_rows.head(10),x='Aporte local (puntos)',y='Variable',orientation='h',
                                color='Sentido',height=470)),table(lime_rows)],className='details')])
        return defer_details(html.Div(parts),'original-shap')
    return layout

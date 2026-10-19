"""Panorama de las implementaciones originales evaluadas en E3."""
import json
import sys
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from prepare_data import CACHE, metrics
from classic_models import metric_bar
from original_analysis import table_statistics, section as original_statistics
from classic_friedman import summary as friedman_summary
from search_results import optimization_section
from lazy_content import defer_details

ROOT = Path(__file__).resolve().parent
BOOK = ROOT.parent / 'Precalculo'
if BOOK.is_dir() and str(BOOK) not in sys.path:
    # The saved TR-KRR pipeline contains this project estimator class.
    sys.path.insert(0, str(BOOK))
DIRECTORY = CACHE / 'originales'
CATALOG = json.loads((DIRECTORY / 'catalog.json').read_text(encoding='utf-8'))
FOLDS = pd.read_csv(DIRECTORY / 'folds.csv')
CONTRASTS = pd.read_csv(DIRECTORY / 'contrasts.csv')
PREDICTIONS = {part: pd.read_csv(DIRECTORY / f'{part}.csv.gz') for part in ['train', 'test']}
ACTIVE = json.loads((DIRECTORY/'active.json').read_text(encoding='utf-8'))
ANALYSIS = json.loads((DIRECTORY/'analysis.json').read_text(encoding='utf-8'))
BEST = ACTIVE['best_key']
BEST_NAME = CATALOG[BEST]['name']
TN_KRR = 'm19'
MODEL_FILES = {BEST: 'best.joblib', TN_KRR: 'tn_krr.joblib'}
DIAGNOSTIC_MODELS = [key for key in CATALOG if key in PREDICTIONS['train'] and key in PREDICTIONS['test']]
ORDER = [spec['name'] for spec in CATALOG.values()]
COLORS = {name: f'hsl({i*137.5 % 360:.0f},48%,43%)' for i, name in enumerate(ORDER)}
SHORT_NAMES = {'TabFM 1.0.0 (PyTorch CPU, 32 vistas)': 'TabFM · 32 vistas',
               'LinXGBoost (hojas completas E3)': 'LinXGBoost E3', 'GPR–XGBoost (OOF agrupado)': 'GPR–XGBoost',
               'logicDT propio (adaptado)': 'logicDT adaptado', 'TabPFN 2.5 original': 'TabPFN original',
               'TabPFN 2.5 fine-tuned': 'TabPFN fine-tuned', 'XGBoost ampliado (gbtree)': 'XGBoost ampliado',
               'Truncated Newton KRR RBF': 'TR-KRR RBF'}


@lru_cache(maxsize=2)
def model_for(key):
    if key not in MODEL_FILES:
        raise KeyError('No hay un pipeline de predicción guardado para ' + str(key))
    return joblib.load(DIRECTORY / MODEL_FILES[key])


def best_model():
    return model_for(BEST)


def combined_frames(training, test):
    frames = []
    for part, base in [('train', training), ('test', test)]:
        predictions = PREDICTIONS[part]
        assert len(base) == len(predictions)
        frame = base.copy()
        for key in CATALOG:
            if key in predictions:
                frame[key] = predictions[key].to_numpy()
        frames.append(frame)
    return frames


def comparison_rows(frame, target, cv=False, global_view=True):
    if frame.empty:
        return pd.DataFrame(columns=['Modelo', 'RMSE', 'MAE', 'MAPE (%)', 'R²'])
    reference = metrics(frame[target], frame.svm)
    if cv and global_view:
        reference = FOLDS.loc[FOLDS.Modelo.eq('SVM lineal')].select_dtypes('number').mean()
    rows = []
    for key, spec in CATALOG.items():
        if key == 'dummy':
            continue
        if key not in frame:
            if cv:
                rows.append({'Modelo': spec['name'], 'Estado': 'Sin OOF independiente', 'n': 0})
            continue
        score = metrics(frame[target], frame[key])
        sd = None
        if cv and global_view:
            folds = FOLDS.loc[FOLDS.Modelo.eq(spec['name'])]
            score = folds[['RMSE', 'MAE', 'MAPE (%)', 'R²']].mean().to_dict()
            sd = float(folds.RMSE.std(ddof=0))
        rows.append({'Modelo': spec['name'], 'Estado': 'Media de 5 folds' if cv and global_view else 'OOF reunido' if cv else 'Test temporal',
                     'Estado de búsqueda':spec.get('status','Histórico'),
                     'n': len(frame), **score, 'SD RMSE folds': sd, 'Δ RMSE vs SVM': score['RMSE']-reference['RMSE']})
    return pd.DataFrame(rows).sort_values('RMSE', na_position='last')


def display_statistics(scores, *, cv=False, global_view=True):
    return table_statistics(scores,cv=cv,global_view=global_view,analysis=ANALYSIS)


def error_correlation(frame, target):
    """Pearson de residuos con signo sobre exactamente las mismas filas."""
    keys = [k for k in CATALOG if k in frame and k != 'dummy']
    errors = pd.DataFrame({CATALOG[k]['name']: frame[target]-frame[k] for k in keys})
    return errors.corr(min_periods=3)


def create_originals(app, ui):
    card, md, table, notice = (ui[k] for k in ['card', 'md', 'table', 'notice'])
    title, stats, subset = (ui[k] for k in ['title', 'stats', 'subset'])
    training, test = combined_frames(ui['TRAIN'], ui['TEST'])
    target, course, program = (ui[k] for k in ['TARGET', 'COURSE', 'PROGRAM'])
    docs = []
    for key, spec in CATALOG.items():
        params = spec.get('params') or {}
        grid = spec.get('grid') or {}
        parameters = pd.DataFrame([{'Parámetro': p.replace('modelo__', ''), 'Búsqueda evaluada': str(grid.get(p, 'Fijo / configuración del informe')),
                                    'Configuración final': str(params.get(p, params.get('modelo__'+p, 'Ver protocolo')))}
                                   for p in dict.fromkeys([*grid, *[p for p in params if p.replace('modelo__', '') not in grid]])])
        docs.append(html.Details([
            html.Summary(spec['name']), md(spec['description']),
            md(f'[Artículo de fundamento]({spec["paper"]})' if spec.get('paper') else 'Referencia de control: media del objetivo aprendida solo en fit; sin paper específico.'),
            md(spec.get('preparation', '')), md(spec.get('method', '')),
            table(parameters) if not parameters.empty else md('Sin grilla de hiperparámetros; configuración fija o ajuste propio del estimador.'),
            md('**Estado:** '+spec.get('status','Histórico')),
            optimization_section(spec,ui) if spec.get('optimization') else None,
            md(' '.join(spec.get('limitations', []))),
        ], className='details classic-pipeline'))
    layout = html.Div([
        title('MODELOS ORIGINALES', 'Panorama completo de modelos',
              f'{len(CATALOG)} modelos y variantes evaluados, incluidos los clásicos.'),
        notice('Datos reales, test temporal 202530 y cinco folds externos por estudiante. Las búsquedas usan solo train; '
               'los modelos preentrenados con configuración fija no requieren grilla. El test reutilizado y las comparaciones entre familias son exploratorios.'),
        notice('SVR RBF, Kernel Ridge y TR-KRR comparan Grid, Random, TPE, DEAP y Successive Halving. '
               'SVM y clásicos reutilizan su ejecución multibúsqueda activa. Los modelos costosos conservan '
               'resultados históricos identificados; los preentrenados fijos no reciben búsquedas ficticias. '
               'La familia con menor RMSE medio CV es exploratoria, no un ganador estadístico confirmado.'),
        html.Details([html.Summary('Modelos pendientes · coste, estado y preparación'),
            table(pd.DataFrame([{'Modelo':p['name'],'Estado':p['state'],
                'Preparación':p.get('preparation_state','No requiere nueva ejecución'),
                'Candidatos Grid pendientes':p.get('prepared',{}).get('grid_size'),
                'Revisar presupuesto Grid': 'Sí · más de 1.000 candidatos' if p.get('prepared',{}).get('grid_size',0)>1000 else 'Según coste del modelo'}
                for p in json.loads((DIRECTORY/'pendientes.json').read_text(encoding='utf-8'))])),
            md('La selección de ejecuciones de menor coste fue autorizada antes de ejecutarlas. '
               'El resto requiere revisión de presupuesto/dependencias; se conserva su evidencia histórica.')],className='details'),
        html.Details([html.Summary('Fundamento, documentación, preparación y búsqueda por modelo'),
            md('Cada ficha explica la implementación evaluada y enlaza su fundamento. Los ports, variantes y ablaciones se identifican explícitamente; '
               'el paper describe el método y no demuestra una mejora en estos datos. Los rangos de grilla reflejan los candidatos realmente evaluados.'), *docs], className='details'),
        ui['filters']('original'),
        notice('Los filtros evalúan subgrupos de modelos globales, sin reentrenar. CV global muestra medias y SD entre folds (ddof=0); '
               'CV filtrada usa OOF reunido. Las métricas ponderan registros. TabPFN fine-tuned carece de OOF independiente.'),
        html.Div([html.Label('Evaluación de los gráficos'), dcc.RadioItems([
            {'label': 'CV externa', 'value': 'cv'}, {'label': 'Test temporal', 'value': 'test'}], 'cv',
            id='original-comparison-partition', inline=True, className='radio')], className='variable-select'),
        dcc.Loading(html.Div(id='original-comparison')),
        html.Details([html.Summary('Diagnósticos · explorar predicciones de los modelos originales'),
        title('DIAGNÓSTICOS', 'Explorar predicciones de los modelos originales',
              f'Por defecto se muestra el líder de CV externa, {BEST_NAME} (RMSE medio {ACTIVE["best_mean_cv"]:.6f}). El selector permite revisar los demás modelos con predicciones OOF disponibles. '
              'Los diagnósticos OOF reúnen las predicciones de los cinco folds; su RMSE agrupado puede diferir de la media entre folds.'),
        html.Div([html.Label('Modelo'), dcc.Dropdown(
            [{'label': CATALOG[key]['name'], 'value': key} for key in DIAGNOSTIC_MODELS],
            value=BEST, id='original-diagnostic-model', clearable=False, searchable=True)],
            className='variable-select'),
        dcc.RadioItems([{'label': 'Test temporal', 'value': 'test'}, {'label': 'Validación OOF', 'value': 'cv'}],
                       'cv', id='original-diagnostic-partition', inline=True, className='radio'),
        dcc.Loading(html.Div(id='original-diagnostics'))],className='details'),
        html.Details([html.Summary('Complementariedad · correlación de errores'),
        title('COMPLEMENTARIEDAD', 'Correlación de errores entre modelos',
              'Residuos con signo: nota real − predicción. OOF permite explorar complementariedad sin ajustar pesos con test.'),
        dcc.RadioItems([{'label': 'OOF de entrenamiento', 'value': 'cv'}, {'label': 'Test temporal', 'value': 'test'}],
                      'cv', id='original-correlation-partition', inline=True, className='radio'),
        dcc.Loading(html.Div(id='original-correlation'))],className='details'),
    ])

    from original_interpretation import create_section as create_interpretation
    layout.children.append(html.Details([html.Summary('Interpretabilidad SHAP y LIME · abrir análisis del líder CV'),
        create_interpretation(app,ui,DIRECTORY)],className='details'))

    @app.callback(Output('original-comparison', 'children'), Input('original-program', 'value'),
                  Input('original-course', 'value'), Input('original-comparison-partition', 'value'))
    def compare(selected_program, selected_course, evaluation):
        tr, te = [subset(frame, selected_program, selected_course) for frame in [training, test]]
        if tr.empty and te.empty:
            return notice('No hay filas para estos filtros.')
        global_view = selected_program == selected_course == '__all__'
        cv, temporal = comparison_rows(tr, target, True, global_view), comparison_rows(te, target, False, global_view)
        scores = display_statistics(cv if evaluation == 'cv' else temporal,
                                    cv=evaluation == 'cv', global_view=global_view)
        plot_order = scores.loc[scores.RMSE.notna(), 'Modelo'].tolist()
        order_note = 'Orden de la tabla: RMSE de menor a mayor en los cuatro gráficos.'
        cards = []
        for metric in ['RMSE', 'MAE', 'MAPE (%)', 'R²']:
            figure = metric_bar(scores, metric, plot_order, COLORS)
            if figure is not None:
                figure.update_layout(height=850)
                figure.update_yaxes(tickvals=plot_order, ticktext=[SHORT_NAMES.get(name, name) for name in plot_order])
            cards.append(card(metric, order_note + ' Línea discontinua: SVM lineal. ' + ('Mayor es mejor.' if metric == 'R²' else 'Menor es mejor.'), figure))
        return defer_details(html.Div([
            html.Div(cards, className='comparison-metric-grid') if not scores.empty else notice('No hay filas en esta evaluación.'),
            html.Article([html.H3('Estadísticos de los modelos y contraste con el SVM'),
                md('Δ RMSE negativo favorece al modelo. SD describe variación entre folds, no un IC. MAPE en porcentaje. '
                   'R² no se define con una sola fila o nota constante.'),
                dcc.Tabs(value='cv', className='sub-tabs', children=[
                    dcc.Tab(label='Test temporal', value='test', children=table(display_statistics(temporal, global_view=global_view)), className='tab', selected_className='tab-selected'),
                    dcc.Tab(label='CV externa', value='cv', children=table(display_statistics(cv, cv=True, global_view=global_view)), className='tab', selected_className='tab-selected'),
                ])], className='card classic-comparison-table'),
            card('Conclusión de la revisión',
                 (friedman_summary(ANALYSIS['omnibus'])+f' **{BEST_NAME}** tiene el menor RMSE medio CV '
                  f'(**{ACTIVE["best_mean_cv"]:.6f}**); no se elige por test. Las etapas2/3 separan CV y test.'
                  if global_view else 'Las métricas del subgrupo son descriptivas; selecciona Todos/Todos para inferencia global.')),
            original_statistics(ANALYSIS,ui) if global_view else None]),'original-comparison')

    @app.callback(Output('original-diagnostics', 'children'), Input('original-program', 'value'),
                  Input('original-course', 'value'), Input('original-diagnostic-partition', 'value'),
                  Input('original-diagnostic-model', 'value'))
    def diagnostics(selected_program, selected_course, partition, model_key):
        data = subset(test if partition == 'test' else training, selected_program, selected_course)
        if data.empty:
            return notice('No hay filas en esta partición para los filtros seleccionados.')
        model_key = model_key if model_key in DIAGNOSTIC_MODELS else BEST
        model_name = CATALOG[model_key]['name']
        score = metrics(data[target], data[model_key])
        prediction = px.scatter(data, x=target, y=model_key, color=course, opacity=.5,
                                labels={target: 'Nota real', model_key: 'Nota predicha'}, hover_data=[program])
        low, high = min(.4, data[model_key].min()), max(5.1, data[model_key].max())
        prediction.add_trace(go.Scatter(x=[low, high], y=[low, high], mode='lines', name='Ideal', line={'dash': 'dash'}))
        residual = px.scatter(data.assign(Residuo=data[target]-data[model_key]), x=model_key, y='Residuo', color=course,
                              labels={model_key: 'Nota predicha'}, opacity=.5)
        residual.add_hline(y=0, line_dash='dash')
        errors = pd.DataFrame({model_name: abs(data[target]-data[model_key]), 'SVM lineal': abs(data[target]-data.svm)}).melt(var_name='Modelo', value_name='Error absoluto')
        return html.Div([stats([('Modelo', model_name, 'Selección del usuario'), ('Filas', str(len(data)), 'Test temporal' if partition == 'test' else 'OOF reunido'),
                               ('RMSE test' if partition == 'test' else 'RMSE OOF reunido', f'{score["RMSE"]:.4f}', 'Puntos de nota'), ('R²', '—' if score['R²'] is None else f'{score["R²"]:.4f}', 'Adimensional')]),
            html.Div([card('Predicción frente a realidad', 'Predicciones sin recorte.', prediction),
                      card('Residuos frente a predicción', 'Residuo positivo indica subestimación.', residual)], className='grid'),
            card('Distribución del error absoluto', 'Mismas filas para ambos modelos.', px.box(errors, x='Modelo', y='Error absoluto', color='Modelo', points=False))])

    @app.callback(Output('original-correlation', 'children'), Input('original-program', 'value'),
                  Input('original-course', 'value'), Input('original-correlation-partition', 'value'))
    def correlation(selected_program, selected_course, partition):
        frame = subset(test if partition == 'test' else training, selected_program, selected_course)
        if len(frame) < 3:
            return notice('Se requieren al menos tres filas para describir la correlación de errores.')
        corr = error_correlation(frame, target)
        pairs = corr.to_numpy()[np.triu_indices(len(corr), 1)]
        pairs = pairs[np.isfinite(pairs)]
        if not len(pairs):
            return notice('Correlación no definida: residuos constantes en este subgrupo.')
        figure = px.imshow(corr, zmin=-1, zmax=1, color_continuous_scale='RdBu_r', aspect='equal',
                            labels={'color': 'Pearson r'})
        figure.update_traces(hovertemplate='%{y}<br>%{x}<br>r = %{z:.4f}<extra></extra>')
        figure.update_layout(height=1000, margin={'l': 190, 'b': 220, 't': 30, 'r': 40})
        figure.update_xaxes(tickangle=-55, tickvals=corr.columns, ticktext=[SHORT_NAMES.get(n, n) for n in corr.columns])
        figure.update_yaxes(tickvals=corr.index, ticktext=[SHORT_NAMES.get(n, n) for n in corr.index])
        figure.update_layout(meta='original-errors')
        summary = f'{len(frame)} filas; {len(corr)} modelos; correlación entre pares: mínimo {pairs.min():.3f}, mediana {np.median(pairs):.3f}, máximo {pairs.max():.3f}.'
        interpretation = ('Los errores están altamente correlacionados: los modelos tienden a equivocarse en las mismas observaciones, '
                          'lo que limita la reducción de varianza esperable al promediarlos.' if pairs.min() >= .8 else
                          'La correlación varía entre modelos; revisa los pares antes de concluir que todos aportan información redundante.')
        matrix_card = card('Matriz de correlación de residuos', summary + ' ' + interpretation +
            ' Una correlación alta sugiere poco margen, pero no prueba que todo ensamble sea inútil. Validar un ensamble exige '
            'ajustar pesos dentro de train y evaluarlo con un protocolo independiente. Dummy se excluye porque es una referencia constante; '
            'TabPFN fine-tuned solo aparece en test por carecer de OOF independiente.', figure)
        matrix_card.className += ' original-error-matrix'
        return html.Div([matrix_card,
            html.Details([html.Summary('Valores de la matriz'), table(corr.reset_index(names='Modelo'))], className='details')])

    return layout

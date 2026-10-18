"""Interfaz de los regresores clásicos y comparación contra el SVM de E3."""
import hashlib
import json
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, State, dcc, html

from prepare_data import BOOK, CACHE, ROOT, metrics
from prediction import build_form, input_id, predict_record
from prepare_originals import CLASSIC_PAPERS
from classic_friedman import friedman_comparison, summary, display_statistics, conclusion, EXPLANATION

DIRECTORY = CACHE / 'clasicos'
REPORT = json.loads((DIRECTORY / 'comparacion.json').read_text(encoding='utf-8'))
FOLDS = pd.read_csv(DIRECTORY / 'fold_metrics.csv')
TRAIN_PREDICTIONS = pd.read_csv(DIRECTORY / 'train_predictions.csv.gz')
TEST_PREDICTIONS = pd.read_csv(DIRECTORY / 'test_predictions.csv.gz')
NAMES = {key: spec['name'] for key, spec in REPORT['models'].items()}
ALL_NAMES = {'svm': 'SVM lineal', **NAMES}
MODEL_ORDER = [ALL_NAMES[key] for key in ['svm', *NAMES]]
FRIEDMAN = friedman_comparison(FOLDS, ALL_NAMES.values())
MODEL_COLORS = {'SVM lineal': '#435568', 'KNN': '#5268b9', 'Ridge': '#bc9028',
                'Lasso': '#a573b3', 'Random Forest': '#3f925f', 'XGBoost': '#187b80',
                'Decision Tree': '#db7355'}


def metric_bar(scores, metric, order=None, colors=None):
    """Unidades y escalas independientes; mismo orden y color de modelos."""
    values = scores.loc[scores[metric].notna()].copy()
    if values.empty:
        return None
    figure = px.bar(values, x=metric, y='Modelo', color='Modelo', orientation='h',
                    text=metric, color_discrete_map=colors or MODEL_COLORS,
                    category_orders={'Modelo': order or MODEL_ORDER})
    template = '%{x:.1f} %' if metric == 'MAPE (%)' else '%{x:.3f}'
    figure.update_traces(texttemplate=template, textposition='outside', cliponaxis=False,
                         hovertemplate='%{y}<br>' + metric + ': ' + template + '<extra></extra>')
    reference = values.loc[values.Modelo.eq('SVM lineal'), metric]
    if len(reference):
        figure.add_vline(x=float(reference.iloc[0]), line_dash='dash', line_color='#435568', line_width=1.5)
    low, high = min(0., float(values[metric].min())), max(0., float(values[metric].max()))
    span = max(high-low, .05)
    figure.update_xaxes(range=[low-.4*span if low < 0 else 0, high+.2*span],
                        title={'RMSE': 'RMSE · puntos de nota', 'MAE': 'MAE · puntos de nota',
                               'MAPE (%)': 'MAPE · porcentaje', 'R²': 'R² · adimensional'}[metric])
    figure.update_yaxes(title=None)
    figure.update_layout(showlegend=False, height=400, bargap=.3)
    return figure


@lru_cache(maxsize=6)
def load_model(key):
    path = DIRECTORY / f'{key}.joblib'
    if hashlib.sha256(path.read_bytes()).hexdigest() != REPORT['models'][key]['model_sha256']:
        raise RuntimeError('El pipeline no corresponde a los resultados: ' + key)
    if key == 'xgboost':
        expected = REPORT['source_sha256']['preprocesamiento_clasicos.py']
        if hashlib.sha256((ROOT / 'preprocesamiento_clasicos.py').read_bytes()).hexdigest() != expected:
            raise RuntimeError('Cambió el preprocesamiento nativo de XGBoost.')
    return joblib.load(path)


def combined_frames(training, test):
    assert len(training) == len(TRAIN_PREDICTIONS) and len(test) == len(TEST_PREDICTIONS)
    np.testing.assert_array_equal(training['fold'], TRAIN_PREDICTIONS['fold'])
    frames = []
    for original, predictions in [(training, TRAIN_PREDICTIONS), (test, TEST_PREDICTIONS)]:
        data = original.copy()
        for column in NAMES:
            data[column] = predictions[column].to_numpy()
        frames.append(data)
    return frames


def comparison_rows(training, test, target, global_view):
    rows = []
    for label, frame in [('CV externa anidada', training), ('Test temporal', test)]:
        if frame.empty:
            continue
        is_cv = label.startswith('CV')
        svm = metrics(frame[target], frame['svm'])
        if is_cv and global_view:
            svm = FOLDS.loc[FOLDS.Modelo.eq('SVM lineal'), ['RMSE', 'MAE', 'MAPE (%)', 'R²']].mean().to_dict()
        for key, name in ALL_NAMES.items():
            score = metrics(frame[target], frame[key])
            sd = None
            if is_cv and global_view:
                fold = FOLDS.loc[FOLDS.Modelo.eq(name)]
                score = fold[['RMSE', 'MAE', 'MAPE (%)', 'R²']].mean().to_dict()
                sd = float(fold['RMSE'].std(ddof=0))
            rows.append({'Modelo': name, 'Evaluación': label, 'n': len(frame), **score,
                         'SD RMSE folds': sd, 'Δ RMSE vs SVM': score['RMSE']-svm['RMSE']})
    return pd.DataFrame(rows)


def create_classics(app, ui):
    card, md, table, notice = (ui[k] for k in ['card', 'md', 'table', 'notice'])
    title, stats, subset = (ui[k] for k in ['title', 'stats', 'subset'])
    training, test = combined_frames(ui['TRAIN'], ui['TEST'])
    target, course, program = (ui[k] for k in ['TARGET', 'COURSE', 'PROGRAM'])
    palette = ui['PALETTE']
    default = next(key for key, name in NAMES.items() if name == REPORT['selected_by_external_cv'])
    pipeline_cards = []
    for key, spec in REPORT['models'].items():
        parameters = pd.DataFrame([
            {'Parámetro': p.replace('modelo__', ''), 'Grid': str(values),
             'Elegido en train': str(spec['best_params'][p])}
            for p, values in spec['grid'].items()
        ])
        pipeline_cards.append(html.Details([
            html.Summary(spec['name'] + f' · {spec["combinations"]} combinaciones'),
            md(f'[Artículo de fundamento]({CLASSIC_PAPERS[key]})'),
            md(spec['preparation']), table(parameters),
            md(f'RMSE del grid final en train: **{spec["selection_rmse"]:.4f}**. '
               'Es una métrica de selección; la evaluación independiente usa los folds externos y el test.'),
        ], className='details classic-pipeline'))
    layout = html.Div([
        title('MODELOS CLÁSICOS', 'Comparación de modelos predictivos',
              'KNN, Ridge, Lasso, Random Forest, XGBoost y Decision Tree frente al SVM lineal.'),
        notice('Todos predicen la nota del primer parcial: son modelos de regresión. '
               'Comparten los datos reales, el test 202530 y los mismos cinco folds externos por estudiante del SVM. '
               'Cada modelo ajusta sus hiperparámetros en cinco folds internos; test no participa en la búsqueda.'),
        html.Details([html.Summary('Fundamento, documentación, preparación y grillas por modelo'),
            md('KNN, Ridge y Lasso reutilizan el preprocesamiento del SVM. Los árboles usan otra representación: '
               '**Decision Tree emplea one-hot completo**, sin escalado ni log1p, para evitar un orden artificial en las categorías. '
               '**Random Forest emplea códigos ordinales** porque requiere entradas numéricas; '
               'estos códigos introducen un orden artificial en variables nominales. '
               '**XGBoost usa particiones categóricas nativas**, sin columnas one-hot externas. '
               'Todas las imputaciones, vocabularios y transformaciones se aprenden únicamente dentro de cada ajuste.'),
            *pipeline_cards], className='details'),
        ui['filters']('classic'),
        notice('Los filtros describen subgrupos del mismo modelo global; no reentrenan. '
               'Sin filtros, CV muestra medias y desviaciones entre folds. Con filtros, se evalúan las '
               'predicciones OOF reunidas del subgrupo. Las métricas dan peso a cada registro.'),
        html.Div([html.Label('Evaluación de los gráficos comparativos'), dcc.RadioItems([
            {'label': 'Validación externa', 'value': 'cv'}, {'label': 'Test temporal', 'value': 'test'}],
            'cv', id='classic-comparison-partition', inline=True, className='radio')], className='variable-select'),
        dcc.Loading(html.Div(id='classic-comparison'), type='circle', color=palette[0]),
        title('DIAGNÓSTICOS', 'Explorar un modelo', 'Contrasta predicciones, residuos y error absoluto con el SVM lineal.'),
        html.Div([html.Label('Modelo clásico'), dcc.Dropdown(
            [{'label': name, 'value': key} for key, name in NAMES.items()], default,
            id='classic-model', clearable=False)], className='variable-select'),
        html.Div([html.Label('Evaluación'), dcc.RadioItems([
            {'label': 'Test temporal', 'value': 'test'}, {'label': 'Validación OOF', 'value': 'validation'}],
            'test', id='classic-partition', inline=True, className='radio')], className='variable-select'),
        dcc.Loading(html.Div(id='classic-diagnostics'), type='circle', color=palette[0]),
        html.Details([html.Summary('Incertidumbre global · bootstrap por estudiante'),
            md('Intervalos percentiles del 95 % con **1.000 remuestreos de estudiantes** del test. '
               'Las comparaciones usan los mismos estudiantes remuestreados para cada modelo y el SVM. '
               '**Δ RMSE = RMSE del modelo − RMSE del SVM**: valores negativos favorecen al modelo. '
               'Son comparaciones exploratorias de seis familias, sin corrección por comparaciones múltiples; '
               'los intervalos no justifican por sí solos declarar superioridad general ni elegir usando test.'),
            table(pd.DataFrame([row for row in REPORT['paired_differences'] if row['Modelo'] in ALL_NAMES.values()])),
            table(pd.DataFrame([row for row in REPORT['bootstrap'] if row['Modelo'] in ALL_NAMES.values()])),
        ], className='details classic-bootstrap'),
        html.Details([html.Summary('Ejemplo de predicción · modelo clásico seleccionado'),
            card('Predecir con el pipeline seleccionado',
                 'El formulario usa el modelo elegido en «Explorar un modelo» y su pipeline guardado. '
                 'El avance se deriva de los dominios y se aplican las mismas reglas de negocio del SVM. '
                 'Cambiar filtros de evaluación no modifica el formulario.'),
            html.Article([build_form(ui['TRAIN'], ui['NUMERIC'], ui['CATEGORICAL'], ui['LABELS'],
                                    ui['DEFAULTS'], prefix='classic')], className='card'),
        ], className='details'),
        card('Lectura de la comparación',
             f'Entre los modelos clásicos, **{REPORT["selected_by_external_cv"]}** tiene el menor RMSE medio '
             'de validación externa y se muestra inicialmente en los diagnósticos. '
             'La comparación entre familias es exploratoria: no es una estimación independiente de un proceso '
             'que también eligiera la familia dentro de cada fold. El test temporal se conserva como contraste final. '
             'Una mejora en test o en un subgrupo no implica que el modelo sea superior en todos los periodos.'),
    ])

    from lime_xgboost import create_lime_section
    layout.children.append(create_lime_section(app, ui, lambda: load_model('xgboost')))

    @app.callback(Output('classic-comparison', 'children'), Input('classic-program', 'value'),
                  Input('classic-course', 'value'), Input('classic-comparison-partition', 'value'))
    def compare(selected_program, selected_course, evaluation):
        tr, te = subset(training, selected_program, selected_course), subset(test, selected_program, selected_course)
        if tr.empty and te.empty:
            return notice('No hay filas para esta combinación. Cambia los filtros o selecciona Todos.')
        scores = comparison_rows(tr, te, target, selected_program == '__all__' and selected_course == '__all__')
        global_view = selected_program == selected_course == '__all__'
        temporal = scores.loc[scores['Evaluación'].eq('Test temporal')]
        cv = scores.loc[scores['Evaluación'].eq('CV externa anidada')]
        label = 'CV externa anidada' if evaluation == 'cv' else 'Test temporal'
        selected = scores.loc[scores['Evaluación'].eq(label)]
        selected = selected.sort_values('RMSE', na_position='last', kind='stable')
        plot_order = selected.loc[selected.RMSE.notna(), 'Modelo'].tolist()
        order_note = 'Orden de la tabla: RMSE de menor a mayor en los cuatro gráficos.'
        metric_cards = []
        for metric in ['RMSE', 'MAE', 'MAPE (%)', 'R²']:
            direction = 'Mayor es mejor' if metric == 'R²' else 'Menor es mejor'
            figure = metric_bar(selected, metric, plot_order)
            metric_cards.append(card(metric + ' · ' + direction,
                label + ' · ' + order_note + (' · Sin valores definidos para este grupo.' if figure is None else
                         ' · La línea discontinua marca el SVM lineal.'), figure))
        return html.Div([
            html.Article([html.H3('Comparación de resultados'),
                md('**Una métrica por gráfico y una evaluación a la vez.** Selecciona validación externa '
                   'o test temporal arriba. Los cuatro gráficos siguen el orden de la tabla de esa evaluación '
                   '(RMSE de menor a mayor) y conservan el color por modelo; '
                   'cada barra muestra su valor. Las escalas y unidades son propias de cada métrica: '
                   'compara modelos dentro de un gráfico. La línea discontinua señala la referencia del SVM.')], className='card'),
            (notice('No hay filas de ' + label + ' para estos filtros. La tabla conserva las evaluaciones disponibles.')
             if selected.empty else html.Div(metric_cards, className='comparison-metric-grid')),
            html.Article([html.H3('Estadísticos de los modelos y test de Friedman'),
                md('Cada fila resume un modelo, la evaluación y el número de registros (**n**). '
                   'El orden es de menor a mayor **RMSE**. RMSE y MAE se expresan en puntos de nota '
                   '(menor es mejor); MAPE en porcentaje (menor es mejor) y R² es adimensional '
                   '(mayor es mejor). **Δ RMSE vs SVM** resta el RMSE del SVM al del modelo: '
                   'un valor negativo indica menor error, sin implicar significancia estadística. '
                   + ('En CV global, las métricas son medias de cinco folds externos; '
                      '**SD RMSE folds** es su desviación estándar poblacional, no un intervalo de confianza. '
                      '**Rango promedio** promedia las posiciones por RMSE dentro de los folds: '
                      'menor rango es mejor y puede diferir del orden por RMSE medio. '
                      'Las métricas de test se calculan sobre los registros reservados.' if global_view else
                      'Las métricas del subgrupo se calculan sobre sus registros: predicciones OOF reunidas '
                      'en validación y predicciones reservadas en test. SD RMSE folds no se estima para el subgrupo; '
                      'no se asignan rangos ni p-valores globales a sus filas. ')
                   + ' R² no está definido si la nota es constante o solo hay una fila. '
                   'Los subgrupos pequeños requieren cautela.'),
                md(EXPLANATION),
                md(summary(FRIEDMAN)) if global_view else md('Friedman no se aplica a los subgrupos filtrados.'),
                html.Details([html.Summary('Rangos por fold y rango promedio · CV global'),
                    table(FRIEDMAN['ranking'])], className='details') if global_view else None,
                dcc.Tabs(value='cv', className='sub-tabs', children=[
                    dcc.Tab(label='Test temporal', value='test', children=table(display_statistics(temporal, global_view=global_view)), className='tab', selected_className='tab-selected'),
                    dcc.Tab(label='CV externa', value='cv', children=table(display_statistics(cv, cv=True, global_view=global_view, result=FRIEDMAN)), className='tab', selected_className='tab-selected'),
                ])], className='card classic-comparison-table'),
            card('Conclusión de la revisión', conclusion(temporal, cv, global_view, FRIEDMAN)),
        ])

    @app.callback(Output('classic-diagnostics', 'children'), Input('classic-program', 'value'),
                  Input('classic-course', 'value'), Input('classic-model', 'value'), Input('classic-partition', 'value'))
    def diagnostics(selected_program, selected_course, key, partition):
        data = subset(test if partition == 'test' else training, selected_program, selected_course)
        if data.empty:
            return notice('No hay filas en esta partición para los filtros seleccionados.')
        score, svm = metrics(data[target], data[key]), metrics(data[target], data['svm'])
        name = NAMES[key]
        pred = px.scatter(data, x=target, y=key, color=course, opacity=.5,
                          labels={target: 'Nota real', key: 'Nota predicha'}, hover_data=[program])
        low = min(.4, data[key].min()-.1)
        high = max(5.1, data[key].max()+.1)
        pred.add_trace(go.Scatter(x=[low, high], y=[low, high], mode='lines', name='Ideal', line={'dash': 'dash'}))
        residual_data = data.assign(Residuo=data[target]-data[key])
        residual = px.scatter(residual_data, x=key, y='Residuo', color=course, opacity=.5,
                              labels={key: 'Nota predicha'}, hover_data=[program])
        residual.add_hline(y=0, line_dash='dash')
        errors = pd.DataFrame({'Nota real': data[target], name: abs(data[target]-data[key]),
                               'SVM lineal': abs(data[target]-data['svm'])}).melt(
                                   id_vars='Nota real', var_name='Modelo', value_name='Error absoluto')
        error_fig = px.box(errors, x='Modelo', y='Error absoluto', color='Modelo', points=False,
                           color_discrete_sequence=[palette[2], palette[0]])
        return html.Div([
            stats([('Modelo', name, 'Pipeline global'), ('Filas evaluadas', f'{len(data):,}', 'Test temporal' if partition == 'test' else 'OOF'),
                   ('RMSE', f'{score["RMSE"]:.3f}', 'Puntos de nota'), ('Δ RMSE vs SVM', f'{score["RMSE"]-svm["RMSE"]:+.3f}', 'Negativo favorece al modelo')]),
            html.Div([card('Predicción frente a realidad', f'Predicciones de **{name}** sin recorte. La diagonal representa coincidencia perfecta.', pred),
                      card('Residuos frente a predicción', 'Residuo = nota real − predicción. Positivo indica subestimación.', residual)], className='grid'),
            card('Distribución del error absoluto', 'Compara la mediana y dispersión del error del modelo y el SVM sobre las mismas filas. '
                 'Los extremos permanecen en los cálculos aunque no se dibujen como puntos.', error_fig),
        ])

    @app.callback(Output(input_id('avance_precalculo_aleks', 'classic'), 'value'),
                  Input(input_id('Dominio_Inicial', 'classic'), 'value'), Input(input_id('Dominio_Final', 'classic'), 'value'))
    def advance(initial, final):
        return float(final)-float(initial) if initial is not None and final is not None else None

    @app.callback(Output('classic-prediction-result', 'children'), Input('classic-predict-button', 'n_clicks'),
                  Input('classic-model', 'value'),
                  *[State(input_id(column, 'classic'), 'value') for column in ui['NUMERIC']+ui['CATEGORICAL']])
    def predict(clicks, key, *values):
        if not clicks:
            return notice('Selecciona un modelo, configura las características y pulsa «Predecir nota».')
        try:
            prediction, _, extrapolated = predict_record(load_model(key), dict(zip(ui['NUMERIC']+ui['CATEGORICAL'], values)), ui['TRAIN'])
        except (ValueError, TypeError) as error:
            return notice('Revisa las características: ' + str(error))
        parts = [stats([('Nota predicha', f'{prediction:.3f}', NAMES[key]),
                        ('MAE global test', f'{REPORT["models"][key]["test_metrics"]["MAE"]:.3f}', 'No es un intervalo individual')])]
        if extrapolated:
            parts.append(notice('Valores fuera del rango de entrenamiento: ' + ', '.join(ui['LABELS'][c] for c in extrapolated)))
        if not .5 <= prediction <= 5:
            parts.append(notice('Predicción fuera de 0,5–5,0; se conserva sin recorte.'))
        return html.Div(parts)

    return layout

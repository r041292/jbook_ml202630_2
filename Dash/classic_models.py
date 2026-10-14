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

DIRECTORY = CACHE / 'clasicos'
REPORT = json.loads((DIRECTORY / 'comparacion.json').read_text(encoding='utf-8'))
FOLDS = pd.read_csv(DIRECTORY / 'fold_metrics.csv')
TRAIN_PREDICTIONS = pd.read_csv(DIRECTORY / 'train_predictions.csv.gz')
TEST_PREDICTIONS = pd.read_csv(DIRECTORY / 'test_predictions.csv.gz')
NAMES = {key: spec['name'] for key, spec in REPORT['models'].items()}
ALL_NAMES = {'dummy': 'Dummy media', 'svm': 'SVM lineal', **NAMES}


@lru_cache(maxsize=5)
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
            md(spec['preparation']), table(parameters),
            md(f'RMSE del grid final en train: **{spec["selection_rmse"]:.4f}**. '
               'Es una métrica de selección; la evaluación independiente usa los folds externos y el test.'),
        ], className='details classic-pipeline'))
    layout = html.Div([
        title('MODELOS CLÁSICOS', 'Comparación de modelos predictivos',
              'KNN, Ridge, Lasso, Random Forest y XGBoost frente al SVM lineal y la referencia de la media.'),
        notice('Todos predicen la nota del primer parcial: son modelos de regresión. '
               'Comparten los datos reales, el test 202530 y los mismos cinco folds externos por estudiante del SVM. '
               'Cada modelo ajusta sus hiperparámetros en cinco folds internos; test no participa en la búsqueda.'),
        html.Details([html.Summary('Preparación y grillas por modelo'),
            md('KNN, Ridge y Lasso reutilizan el preprocesamiento del SVM. Los árboles usan otra representación: '
               '**Random Forest emplea códigos ordinales** porque requiere entradas numéricas; '
               'estos códigos introducen un orden artificial en variables nominales. '
               '**XGBoost usa particiones categóricas nativas**, sin columnas one-hot externas. '
               'Todas las imputaciones, vocabularios y transformaciones se aprenden únicamente dentro de cada ajuste.'),
            *pipeline_cards], className='details'),
        ui['filters']('classic'),
        notice('Los filtros describen subgrupos del mismo modelo global; no reentrenan. '
               'Sin filtros, CV muestra medias y desviaciones entre folds. Con filtros, se evalúan las '
               'predicciones OOF reunidas del subgrupo. Las métricas dan peso a cada registro.'),
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
               'Son comparaciones exploratorias de cinco familias, sin corrección por comparaciones múltiples; '
               'los intervalos no justifican por sí solos declarar superioridad general ni elegir usando test.'),
            table(pd.DataFrame(REPORT['paired_differences'])),
            table(pd.DataFrame(REPORT['bootstrap'])),
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

    @app.callback(Output('classic-comparison', 'children'), Input('classic-program', 'value'), Input('classic-course', 'value'))
    def compare(selected_program, selected_course):
        tr, te = subset(training, selected_program, selected_course), subset(test, selected_program, selected_course)
        if tr.empty and te.empty:
            return notice('No hay filas para esta combinación. Cambia los filtros o selecciona Todos.')
        scores = comparison_rows(tr, te, target, selected_program == '__all__' and selected_course == '__all__')
        melted = scores.melt(id_vars=['Modelo', 'Evaluación'], value_vars=['RMSE', 'MAE', 'R²'],
                             var_name='Métrica', value_name='Valor')
        figure = px.scatter(melted, x='Valor', y='Modelo', color='Evaluación', symbol='Evaluación',
                            facet_col='Métrica', color_discrete_sequence=[palette[0], palette[1]])
        figure.update_xaxes(matches=None, showticklabels=True)
        figure.for_each_annotation(lambda a: a.update(text='R<sup>2</sup>' if a.text.endswith('R²') else a.text.split('=')[-1]))
        return html.Div([
            card('Comparación de resultados', 'Cada punto corresponde a un modelo y una evaluación. '
                 '**RMSE y MAE: menor es mejor; R²: mayor es mejor.** Los ejes de los tres paneles son independientes.', figure),
            html.Article([html.H3('Estadísticos de los modelos y contraste con el SVM'),
                md('**Δ RMSE negativo** indica menor error que el SVM en esa misma evaluación. '
                   'SD RMSE describe variación entre cinco folds externos y solo se muestra en CV global. '
                   'No es un intervalo de confianza. MAPE se expresa en porcentaje; R² no está definido '
                   'si la nota es constante o solo hay una fila. Los subgrupos pequeños requieren cautela.'),
                table(scores)], className='card classic-comparison-table'),
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

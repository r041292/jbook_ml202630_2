"""Formulario y validación del ejemplo: inferencia con el pipeline ya ajustado."""
import numpy as np
import pandas as pd
from dash import dcc, html


def input_id(column):
    return 'example-' + column


def build_form(training, numeric, categorical, labels, defaults):
    numeric_fields = []
    for column in numeric:
        derived = column == 'avance_precalculo_aleks'
        integer = column in ['Icfes_nuevo', 'Icfes_Matematicas', 'Dominio_Inicial', 'Dominio_Final', 'avance_precalculo_aleks']
        numeric_fields.append(html.Div([
            html.Label(labels.get(column, column), htmlFor=input_id(column)),
            dcc.Input(id=input_id(column), type='number', value=float(defaults[column]),
                      min=0, step=1 if integer else 'any', disabled=derived,
                      placeholder='Vacío: imputación del modelo', debounce=True),
            html.Small('Se calcula: dominio final − inicial.' if derived else
                       'Horas; admite decimales.' if 'Tiempo' in column and column != 'Tiempo_total_Aprendidos_hora' else
                       'Temas por hora.' if column == 'Tiempo_total_Aprendidos_hora' else 'Valor numérico.'),
        ], className='example-field'))
    category_fields = [html.Div([
        html.Label(labels.get(column, column), htmlFor=input_id(column)),
        dcc.Dropdown([{'label': value, 'value': value} for value in sorted(training[column].unique())],
            defaults[column], id=input_id(column), clearable=False),
    ], className='example-field') for column in categorical]
    return html.Div([
        html.H3('Características numéricas'), html.Div(numeric_fields, className='example-grid'),
        html.H3('Características categóricas'), html.Div(category_fields, className='example-grid'),
        html.Button('Predecir nota', id='predict-button', n_clicks=0, className='primary-button'),
        dcc.Loading(html.Div(id='prediction-result', role='status'), type='circle', color='#187b80'),
    ])


def predict_record(model, values, training):
    columns = list(model.feature_names_in_)
    record = {c: values.get(c) for c in columns}
    record['avance_precalculo_aleks'] = None  # Derivado: no aceptar un avance introducido por separado.
    numeric = training[columns].select_dtypes(include='number').columns
    for column in numeric:
        value = record[column]
        record[column] = np.nan if value is None else float(value)
        if not np.isnan(record[column]) and (not np.isfinite(record[column]) or record[column] < 0):
            raise ValueError('Los valores numéricos deben ser finitos y no negativos.')
    initial, final = record['Dominio_Inicial'], record['Dominio_Final']
    if not np.isfinite(initial) or not np.isfinite(final):
        raise ValueError('Introduce ambos dominios para verificar la progresión y calcular el avance.')
    if initial != int(initial) or final != int(final):
        raise ValueError('Los dominios son conteos de temas: usa números enteros.')
    if final < initial:
        raise ValueError('El dominio final debe ser mayor o igual que el inicial.')
    for column in ['Tiempo_Total_Tiempo', 'Tiempo_total_Aprendidos_hora']:
        if record[column] == 0 and final != initial:
            raise ValueError('Un tiempo total o una tasa de aprendizaje igual a cero exige dominios iguales.')
    for column, maximum in [('Icfes_nuevo', 500), ('Icfes_Matematicas', 100)]:
        value = record[column]
        if np.isfinite(value) and (value > maximum or value != int(value)):
            raise ValueError(f'{column}: introduce un puntaje entero entre 0 y {maximum}.')
    record['avance_precalculo_aleks'] = final - initial
    for column in columns:
        if column not in numeric and record[column] not in set(training[column].dropna()):
            raise ValueError('Selecciona una categoría disponible para cada variable.')
    institutional = ['programa_en_matricula', 'Mat_Curso_Asignatura_Relacionada', 'division_en_matricula']
    match = training[institutional].eq(pd.Series({c: record[c] for c in institutional})).all(axis=1)
    if not match.any():
        raise ValueError('La combinación de programa, asignatura y división no aparece en entrenamiento. Revisa las tres selecciones.')
    frame = pd.DataFrame([record], columns=columns)
    prediction = float(model.predict(frame)[0])
    extrapolated = [c for c in numeric if np.isfinite(record[c]) and
                    not training[c].min() <= record[c] <= training[c].max()]
    return prediction, record, extrapolated


def coefficient_report(model):
    preprocessor = model.named_steps['preprocesamiento']
    estimator = model.named_steps['modelo']
    terms = preprocessor.get_feature_names_out()
    rows = [{'Variable / término': 'Intercepto (β₀)', 'β': float(estimator.intercept_[0]),
             'Rol': 'Intercepto estimado'}]
    rows.extend({'Variable / término': name, 'β': float(beta), 'Rol': 'Coeficiente estimado'}
                for name, beta in zip(terms, estimator.coef_))
    cat_columns = next(columns for name, _, columns in preprocessor.transformers_ if name == 'cat')
    encoder = preprocessor.named_transformers_['cat'].named_steps['onehot']
    for column, categories, dropped in zip(cat_columns, encoder.categories_, encoder.drop_idx_):
        if dropped is not None:
            rows.append({'Variable / término': f'{column} = {categories[dropped]}', 'β': 0.0,
                         'Rol': 'Categoría de referencia: fijado en 0'})
    return pd.DataFrame(rows)

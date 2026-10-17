"""Flujo e interpretación del pipeline lineal, derivados del artefacto ajustado."""
import numpy as np
import pandas as pd
from dash import html


def linear_pipeline_section(model, ui):
    prep = model.named_steps['preprocesamiento']
    columns = {name: list(cols) for name, _, cols in prep.transformers_ if name != 'remainder'}
    labels = ui['LABELS']
    md, table, title = (ui[k] for k in ['md', 'table', 'title'])
    def step(kicker, heading, text, class_name=''):
        return html.Div([html.Small(kicker), html.H3(heading), html.P(text)], className='pipeline-step '+class_name)
    branches = []
    stats = []
    for key, heading, transform in [
        ('num_plain', 'Numéricas sin logaritmo', 'Mediana → StandardScaler'),
        ('num_log', 'Tiempos y tasa de aprendizaje', 'Mediana → log1p → StandardScaler'),
        ('cat', 'Variables categóricas', 'Moda → one-hot con categoría de referencia')]:
        names = columns[key]
        branches.append(html.Div([
            html.H4(heading), html.P(' · '.join(labels.get(c, c) for c in names)),
            html.Strong(transform),
            html.P('z = (x − μ) / σ' if key == 'num_plain' else
                   'z = [ln(1 + x) − μ_log] / σ_log' if key == 'num_log' else
                   'k categorías → k − 1 indicadores; la referencia tiene todos sus indicadores en 0.')
        ], className='pipeline-branch'))
        if key.startswith('num_'):
            fitted = prep.named_transformers_[key]
            for i, column in enumerate(names):
                stats.append({'Variable': labels.get(column, column), 'Mediana de imputación': fitted.named_steps['imputer'].statistics_[i],
                              'Transformación': 'ln(1 + x)' if key == 'num_log' else 'x',
                              'Media para escalar (μ)': fitted.named_steps['scaler'].mean_[i],
                              'Desviación para escalar (σ)': fitted.named_steps['scaler'].scale_[i]})
    cat = prep.named_transformers_['cat'].named_steps['onehot']
    references = pd.DataFrame([{'Variable': labels.get(c, c), 'Referencia': categories[int(dropped)],
                                'Indicadores': len(categories)-1}
                               for c, categories, dropped in zip(columns['cat'], cat.categories_, cat.drop_idx_)])
    n_features = len(prep.get_feature_names_out())
    return html.Div([
        title('TRANSFORMACIONES', 'Pipeline de los modelos lineales',
              'LinearSVR, Ridge y Lasso comparten esta preparación. Los parámetros de transformación se aprenden dentro de cada ajuste.'),
        html.Div([
            step('01 · ENTRADAS', f'{len(model.feature_names_in_)} variables predictoras',
                 'Datos reales válidos. ID, periodo y nota_final quedan fuera de X; el objetivo conserva su escala.'),
            html.Div('↓', className='pipeline-arrow', **{'aria-hidden': 'true'}),
            html.Div(branches, className='pipeline-branches'),
            html.Div('↓', className='pipeline-arrow', **{'aria-hidden': 'true'}),
            step('02 · UNIÓN', f'{n_features} columnas transformadas en el ajuste final',
                 'Se concatenan las tres ramas. El vocabulario y el número de columnas pueden variar dentro de los folds.'),
            html.Div('↓', className='pipeline-arrow', **{'aria-hidden': 'true'}),
            step('03 · REGRESIÓN', 'LinearSVR · Ridge · Lasso',
                 'LinearSVR usa pérdida epsilon-insensible; Ridge penalización L2 y Lasso L1. Cada familia selecciona sus propios parámetros en train.'),
            html.Div('↓', className='pipeline-arrow', **{'aria-hidden': 'true'}),
            step('04 · SALIDA', 'Nota predicha en la escala original',
                 'ŷ = β₀ + Σ βⱼzⱼ. No se normaliza el objetivo ni se recortan las predicciones a 0,5–5,0.'),
        ], className='pipeline-flow', role='group', **{'aria-label': 'Flujo del preprocesamiento de los modelos lineales'}),
        md('**Para qué sirve cada paso:** mediana y moda completan faltantes con estadísticas de train; '
           '`log1p` admite cero y comprime la cola derecha de tiempos/tasas, conservando los valores extremos. '
           'StandardScaler pone las numéricas en unidades comparables para la regularización. '
           'One-hot representa categorías nominales sin imponerles un orden numérico y elimina una categoría como referencia.'),
        ui['notice']('En cada fold interno, mediana, moda, log1p, escaladores y vocabulario se aplican dentro del pipeline: '
                     'las estadísticas se ajustan solo con su entrenamiento. Validación y test reciben transform, sin volver a ajustar. '
                     'log1p es una función fija; lo que se aprende son las imputaciones, medias, desviaciones y categorías.'),
        md('**Categorías no vistas:** el one-hot del pipeline lineal las codifica con todos los indicadores en cero '
           '(`handle_unknown="ignore"`), por lo que comparten esa representación con la referencia. '
           'No se aprende vocabulario del test. **KNN y Kernel Ridge reutilizan esta preparación, pero no son modelos lineales en las entradas.** '
           'Random Forest y XGBoost tienen otra preparación, descrita en sus fichas.'),
        html.Details([html.Summary('Ver estadísticas y referencias del pipeline final guardado'),
                      md('Estos valores se aprendieron al ajustar todo train; no son los valores particulares de cada fold. '
                         'La mediana se expresa antes del logaritmo; μ y σ corresponden a la variable que entra al escalador.'),
                      table(pd.DataFrame(stats)), table(references)], className='details'),
    ])


def beta_examples(model, labels):
    """Ejemplos matemáticos exactos en la escala transformada del modelo final."""
    prep = model.named_steps['preprocesamiento']
    beta = dict(zip(prep.get_feature_names_out(), model.named_steps['modelo'].coef_))
    rows = []
    for name, _, columns in prep.transformers_:
        if not name.startswith('num_'):
            continue
        fitted = prep.named_transformers_[name]
        for i, column in enumerate(columns):
            coefficient = float(beta[f'{name}__{column}'])
            scale = float(fitted.named_steps['scaler'].scale_[i])
            median = float(fitted.named_steps['imputer'].statistics_[i])
            delta = coefficient/scale if name == 'num_plain' else coefficient*np.log((median+2)/(median+1))/scale
            change = '+1 unidad original' if name == 'num_plain' else f'De {median:.3f} a {median+1:.3f} unidades originales'
            rows.append({'Variable': labels.get(column, column), 'Cambio ilustrativo': change,
                         'Cambio en predicción (puntos)': delta,
                         'Lectura': '+1 DE en la variable escalada aporta β; este ejemplo mantiene fijas las otras columnas transformadas.'})
    return pd.DataFrame(rows)

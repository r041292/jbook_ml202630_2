"""Dashboard académico. Ejecutar con el venv compartido de Precalculo."""
import json
import re
import hashlib
import textwrap
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html
import joblib
from flask import send_file

from prepare_data import BOOK, CACHE, ROOT, hashes, metrics
from deployment import verify_inputs
from charts import numeric_density
from prediction import build_form, coefficient_report, input_id, predict_record
from model_interpretation import linear_pipeline_section, beta_examples
from display_labels import COURSES, course_text, display_tree
from model_math import math_section
from eda_statistics import (normality, group_test, frequency_test, missing_test,
                            comparison_text, association_tests)
from residual_diagnostics import residual_diagnostics, format_p, diagnostic_reading

manifest_path = CACHE / 'manifest.json'
if not manifest_path.exists():
    raise RuntimeError('Primero ejecuta: ..\\Precalculo\\venv\\Scripts\\python.exe prepare_data.py')
MANIFEST = json.loads(manifest_path.read_text(encoding='utf-8'))
verify_inputs(MANIFEST)
if hashlib.sha256((CACHE / 'model.joblib').read_bytes()).hexdigest() != MANIFEST['model_sha256']:
    raise RuntimeError('El pipeline guardado cambió. Regenera los resultados antes de predecir.')
MODEL = joblib.load(CACHE / 'model.joblib')

TRAIN = pd.read_csv(CACHE / 'train.csv.gz')
TEST = pd.read_csv(CACHE / 'test.csv.gz')
FOLDS = pd.read_csv(CACHE / 'fold_metrics.csv')
COEFFICIENTS = pd.read_csv(CACHE / 'coefficients.csv')
FULL_COEFFICIENTS = coefficient_report(MODEL)
DOCUMENT = (BOOK / '00_seleccion_base_datos.md').read_text(encoding='utf-8')
MODEL_REPORT = json.loads((CACHE / 'svm_report.json').read_text(encoding='utf-8'))
EDA_REPORT = json.loads((BOOK / 'resultados/e3/eda.json').read_text(encoding='utf-8'))
SVM_RESULT = next(r for r in MODEL_REPORT['test'] if r['modelo'] == 'SVM lineal')
SVM_CV = {r['metrica']: r for r in MODEL_REPORT['cv'] if r['modelo'] == 'SVM lineal'}
SVM_CI = {r['metrica']: r for r in MODEL_REPORT['bootstrap'] if r['modelo'] == 'SVM lineal'}
SVM_DIAG = next(r for r in MODEL_REPORT['residuals'] if r['modelo'] == 'SVM lineal')
TARGET = 'nota_primer_parcial'
PROGRAM = 'programa_en_matricula'
COURSE = 'Mat_Curso_Asignatura_Relacionada'
FEATURES = list(MODEL.feature_names_in_)
NUMERIC = TRAIN[FEATURES].select_dtypes(include='number').columns.tolist()
CATEGORICAL = [c for c in FEATURES if c not in NUMERIC]
DEFAULTS = TRAIN[FEATURES].dropna().iloc[0].to_dict()
LABELS = {TARGET: 'Nota del primer parcial', 'Icfes_nuevo': 'Saber 11 · global',
          'Icfes_Matematicas': 'Saber 11 · matemáticas', 'Dominio_Inicial': 'Dominio inicial (temas)',
          'Dominio_Final': 'Dominio final (temas)', 'avance_precalculo_aleks': 'Avance en ALEK (temas)',
          'Tiempo_Total_Tiempo': 'Tiempo de trabajo (horas)',
          'Tiempo_total_Aprendidos_hora': 'Temas aprendidos por hora',
          'Tiempo_empleado_en_la_verificación_de_conocimientos': 'Tiempo de pretest (horas)',
          PROGRAM: 'Programa', COURSE: 'Asignatura', 'cumplimiento_temas': 'Cumplimiento de la meta',
          'Categoria_temas_inicial': 'Categoría de temas iniciales', 'Categoria_temas_final': 'Categoría de temas finales',
          'division_en_matricula': 'División académica', 'avance_cuartiles': 'Categoría de avance por cuartiles'}
PALETTE = ['#187b80', '#db7355', '#5268b9', '#a573b3', '#bc9028', '#3f925f', '#bd5681', '#6c8292']
GROUP_COLORS = {value: PALETTE[i % len(PALETTE)] if i < len(PALETTE) else
                f'hsl({(i * 137.5) % 360:.0f},55%,42%)'
                for i, value in enumerate(sorted(set(TRAIN[PROGRAM]) | set(TRAIN[COURSE])))}
MODEL_COLORS = {'SVM lineal': PALETTE[0], 'Dummy media': PALETTE[1]}
COMPARISON_COLORS = {'Originales de train': '#435568', 'Perturbación local': PALETTE[0],
                     'Interpolación entre vecinos': PALETTE[1]}

app = Dash(__name__, title='Precálculo | Evidencia académica', assets_folder=str(ROOT / 'assets'))
app.config.suppress_callback_exceptions = True
server = app.server
from lazy_content import defer_details, install as install_lazy_content
install_lazy_content(app)


@server.route('/healthz')
def health():
    return {'status': 'ok'}, 200


@server.route('/project-image')
def project_image():
    return send_file(ROOT / 'img.jpeg')


def section(text, title):
    match = re.search(r'^## ' + re.escape(title) + r'\s*\n(.*?)(?=^## |\Z)', text, re.M | re.S)
    return match.group(1).strip() if match else ''


def md(text):
    return dcc.Markdown(course_text(text), className='prose', link_target='_blank')


def notice(text):
    return html.Div(course_text(text), className='notice')


def card(title, text, figure=None, wide=False, details=None):
    children = [html.H3(title), md(text)]
    if details:
        children.append(html.Details([html.Summary('Cómo se analizó y cómo leer el gráfico'),
                                     md(details)], className='details'))
    if figure is not None:
        styled = style(figure)
        metric_comparison = any(a.text == 'R<sup>2</sup>' for a in (styled.layout.annotations or []))
        children.append(dcc.Graph(figure=styled, className='metric-comparison' if metric_comparison else '',
            style={'height': f'{styled.layout.height}px', 'width': '100%'},
            config={'displaylogo': False, 'scrollZoom': False,
            'toImageButtonOptions': {'format': 'png', 'scale': 2}}, responsive=True))
    return html.Article(children, className='card' + (' wide' if wide else ''))


def style(fig):
    fig = go.Figure(display_tree(fig.to_dict()))
    graph_height = fig.layout.height or 410
    fig.update_layout(template='plotly_white', font={'family': 'Segoe UI, Arial, sans-serif', 'size': 15, 'color': '#435568'},
        paper_bgcolor='white', plot_bgcolor='white', margin={'l': 40, 'r': 24, 't': 30, 'b': 70},
        legend={'orientation': 'h', 'y': -0.25, 'x': 0}, height=graph_height,
        colorway=PALETTE, hoverlabel={'bgcolor': '#fff', 'font_size': 16})
    fig.update_xaxes(gridcolor='#edf1f3', zerolinecolor='#dfe6e9', automargin=True)
    fig.update_yaxes(gridcolor='#edf1f3', zerolinecolor='#dfe6e9', automargin=True)
    if any(annotation.text == 'R<sup>2</sup>' for annotation in (fig.layout.annotations or [])):
        # Reservar espacio bajo la barra flotante para que no oculte R² al pasar el cursor.
        fig.update_layout(height=445, margin={'t': 65})
        fig.update_annotations(y=1.02, yanchor='bottom')
    if any(trace.type == 'heatmap' and len(trace.y) > 5 for trace in fig.data):
        fig.update_layout(height=570, margin={'l': 165, 'r': 40, 't': 20, 'b': 155})
        fig.update_xaxes(tickangle=-40, tickfont={'size': 13})
        fig.update_yaxes(tickfont={'size': 13})
    if fig.layout.meta == 'original-errors':
        fig.update_layout(height=1000, margin={'l': 160, 'r': 55, 't': 30, 'b': 200})
        fig.update_xaxes(tickangle=-55)
    if fig.layout.meta in ('shap-summary', 'shap-waterfall'):
        fig.update_layout(margin={'l': 220, 'r': 100, 't': 40, 'b': 100},
                          legend={'orientation': 'h', 'y': -.12, 'x': 0})
    return fig


def stats(items):
    return html.Div([html.Div([html.Small(label), html.Strong(value), html.Span(detail)], className='stat')
                     for label, value, detail in items], className='stats compact-stats' if len(items) == 2 else 'stats')


def table(frame):
    return html.Div(html.Table([html.Thead(html.Tr([html.Th(c) for c in frame.columns])),
        html.Tbody([html.Tr([html.Td('—' if pd.isna(v) else f'{v:.4f}' if isinstance(v, (float, np.floating)) else course_text(str(v)))
                            for v in row]) for row in frame.itertuples(index=False, name=None)])]), className='table-wrap')


def title(kicker, heading, description):
    return html.Div([html.Span(kicker, className='eyebrow'), html.H2(heading), html.P(description)], className='section-head')


def filters(prefix, mode=False):
    children = []
    if mode:
        children.append(html.Div([html.Label('Comparar resultados'), dcc.RadioItems(id=f'{prefix}-mode',
            options=[{'label': 'General', 'value': 'general'}, {'label': 'Por programa', 'value': PROGRAM},
                     {'label': 'Por asignatura', 'value': COURSE}], value='general', inline=True,
            className='radio', persistence=True, persistence_type='session')], className='view-select'))
    for column, suffix, label in [(PROGRAM, 'program', 'Programa académico'), (COURSE, 'course', 'Asignatura')]:
        values = sorted(set(TRAIN[column]) | set(TEST[column]))
        options = [{'label': 'Todos', 'value': '__all__'}] + [{'label': course_text(v), 'value': v} for v in values]
        children.append(html.Div([html.Label(label, htmlFor=f'{prefix}-{suffix}'),
            dcc.Dropdown(options, '__all__', id=f'{prefix}-{suffix}', clearable=False,
                persistence=True, persistence_type='session')], className='filter-field'))
    return html.Div(children, className='filters')


def subset(frame, program, course):
    result = frame
    for column, value in [(PROGRAM, program), (COURSE, course)]:
        if value and value != '__all__':
            result = result[result[column] == value]
    return result.copy()


INTRO = html.Div([
    html.Div([html.Div([html.Span('UNIVERSIDAD DEL NORTE · 2023–2025', className='eyebrow'),
        html.H1(['Del aprendizaje', html.Br(), 'a la evidencia.']),
        html.P('Un recorrido por el nivelatorio de precálculo: sus datos, los hallazgos y una primera aproximación al desempeño académico.'),
        html.Div([html.Span('ALEK'), html.Span('Precálculo'), html.Span('Machine Learning')], className='pills')], className='hero-copy'),
        html.Div([html.Img(src='/project-image', alt='Estudiantes trabajando en el aula de la Universidad del Norte'),
                  html.Span('Aprender hoy. Comprender los resultados mañana.', className='image-caption')], className='hero-image')], className='hero'),
    stats([('Periodo de estudio', '2023–2025', 'Seis periodos académicos'), ('Fuente original', '1.527', 'Registros académicos'),
           ('Asignaturas', '4', 'Matemáticas de primer semestre'), ('Objetivo', 'Primer parcial', 'Predicción en escala de nota')]),
    card('Punto de partida', 'Entregable 3: análisis de registros académicos de ALEK. Se evalúa la nota del primer parcial con una partición temporal y validación agrupada por estudiante.', wide=True),
    card('Contexto académico del proyecto', section(DOCUMENT, 'Contexto académico e institucional'), wide=True),
    card('La pregunta de investigación', 'Este proyecto busca responder la pregunta:\n\n'
         '**¿En qué medida los resultados del nivelatorio de precálculo y la información académica disponible '
         'permiten predecir la nota del primer parcial de la asignatura relacionada?**\n\n' +
         section(DOCUMENT, 'Propósito del proyecto'), wide=True),
    html.Div([html.Span('01'), html.Div([html.H3('Comprender los datos'), html.P('Datos reales, calidad y exploración interactiva.')]),
              html.Span('02'), html.Div([html.H3('Evaluar la predicción'), html.P('Validación, test y errores del modelo lineal.')])], className='journey'),
])

VARIABLES = html.Div([
    title('01 / VARIABLES', 'Variables del proyecto', 'Registros reales, calidad y separación temporal.'),
    card('Diccionario del proyecto', section(DOCUMENT, 'Descripción de las variables del esquema final'), wide=True),
    card('Fuente de datos reales',
         f'Se conservan los **{MODEL_REPORT["source_rows"]:,} registros originales**. '
         f'**{MODEL_REPORT["missing_target"]} filas sin nota del parcial** se excluyen del análisis supervisado. '
         'Se conservan los outliers válidos. Los identificadores se emplean localmente '
         'para separar estudiantes y no se incluyen como predictores ni se exportan al dashboard.'),
    card('Reglas de negocio validadas',
         'Antes de explorar los datos o entrenar el modelo, se comprueba que cada registro sea coherente '
         'con el proceso de aprendizaje en ALEK. Estas reglas distinguen una inconsistencia del registro '
         'de un valor extremo que sí puede representar un comportamiento real.\n\n'
         '1. **El dominio final no puede ser menor que el inicial:** los temas dominados al terminar '
         'deben ser al menos los registrados al inicio.\n'
         '2. **Si el tiempo total de trabajo es cero, los dominios deben ser iguales:** sin trabajo '
         'registrado en la plataforma no se admite un incremento de dominio.\n'
         '3. **Si los temas aprendidos por hora son cero, los dominios deben ser iguales:** '
         'una tasa de aprendizaje nula debe ser coherente con la ausencia de avance.\n\n'
         f'Se excluyen **{MODEL_REPORT["excluded_train"]} filas de train** y **{MODEL_REPORT["excluded_test"]} de test** por inconsistencias. '
         'Si aparece una inconsistencia, se excluye antes de imputar; no se corrige como si fuera un faltante. '
         'Los outliers válidos se conservan. `nota_final` se reserva para auditoría y nunca entra al modelo.'),
])


EDA = html.Div([
    title('03 / EXPLORACIÓN', 'Análisis exploratorio de los datos', 'Distribuciones, calidad y asociaciones sobre entrenamiento válido.'),
    notice(f'{len(TRAIN):,} registros válidos de train, '
           f'{EDA_REPORT["excluded"]} inconsistencias; se mantienen los outliers válidos.'),
    filters('eda', mode=True),
    html.Div([html.Label('Relacionar la nota con'), dcc.Dropdown([{'label': LABELS[c], 'value': c} for c in NUMERIC],
        'Dominio_Final', id='eda-variable', clearable=False)], className='variable-select'),
    html.Div([html.Label('Variable categórica para frecuencias'), dcc.Dropdown([{'label': LABELS[c], 'value': c} for c in CATEGORICAL],
        'cumplimiento_temas', id='eda-category', clearable=False)], className='variable-select'),
    dcc.Loading(html.Div(id='eda-results'), type='circle', color=PALETTE[0]),
])


def split_figure():
    train_n, test_n = MODEL_REPORT['train_raw'], MODEL_REPORT['test_raw']
    return go.Figure(go.Sankey(arrangement='snap', node={'pad': 35, 'thickness': 16,
        'label': [f'{train_n + test_n:,} registros reales', f'{len(TRAIN):,} train · 202310–202510',
                  f'{len(TEST):,} test · 202530'],
        'color': ['#879ba4', PALETTE[0], PALETTE[2]]},
        link={'source': [0, 0], 'target': [1, 2],
              'value': [len(TRAIN), len(TEST)], 'color': ['#cce7e5', '#dce2f5']}))


def cv_figure():
    z = np.zeros((5, 5), dtype=int)
    np.fill_diagonal(z, 1)
    return go.Figure(go.Heatmap(z=z, x=['Bloque 1', 'Bloque 2', 'Bloque 3', 'Bloque 4', 'Bloque 5'],
        y=['Fold 1', 'Fold 2', 'Fold 3', 'Fold 4', 'Fold 5'], colorscale=[[0, '#cce7e5'], [1, '#5268b9']], showscale=False,
        text=np.where(z == 1, 'Val.', 'Train'), texttemplate='%{text}', textfont={'size': 15},
        hovertext=np.where(z == 1, 'Validación', 'Entrenamiento'),
        hovertemplate='%{y} · %{x}<br>%{hovertext}<extra></extra>', xgap=5, ygap=5))


def groupkfold_card():
    explanation = card('GroupKFold por estudiante',
        f'**Un grupo es un estudiante; un fold contiene varios estudiantes completos.** '
        f'Los **{MODEL_REPORT["train_valid"]:,} registros de entrenamiento** corresponden a '
        f'**{MODEL_REPORT["train_students"]:,} grupos de estudiantes**, distribuidos entre **cinco folds externos**. '
        'Si una persona tiene varios registros, todos permanecen juntos: nunca participa a la vez '
        'en entrenamiento y validación de una misma iteración.\n\n'
        'Cada fila del esquema es una iteración: cuatro bloques entrenan y uno valida. '
        '**Verde = Train (entrenamiento); azul = Val. (validación).** '
        'El dibujo es conceptual: cada bloque contiene muchos estudiantes, no una sola persona.', cv_figure())
    fold_sizes = pd.DataFrame([
        {'Fold': f['fold'], 'Filas train': f['fit_rows'], 'Filas val.': f['validation_rows'],
         'Estudiantes val.': f['validation_students']}
        for f in MODEL_REPORT['fold_audit']
    ])
    explanation.children.append(html.Details([
        html.Summary('Paso a paso · grupos, folds y ajuste de parámetros'),
        md('**Por qué agrupamos por estudiante.** Una división por filas podría usar un registro de una '
           'persona para entrenar y otro de esa misma persona para validar. Para evitarlo, GroupKFold '
           'usa el identificador persistente del estudiante como restricción de separación. '
           '**El identificador no es una variable predictora.**\n\n'
           '**Agrupar estudiantes en folds no los fusiona.** Por ejemplo, si Ana tiene tres registros '
           'y Luis tiene uno, ambos pueden pertenecer al mismo fold: se reservan juntos, pero conservan '
           'sus cuatro filas y sus notas individuales. Sus registros no se promedian. '
           'Es un ejemplo ilustrativo; no representa identidades de la base.\n\n'
           '**Cinco folds externos para evaluar:**\n\n'
           '1. Se reserva un fold completo de estudiantes y se trabaja con los otros cuatro.\n'
           '2. Dentro de ese entrenamiento se seleccionan los parámetros con la validación interna descrita abajo.\n'
           '3. El pipeline ganador se ajusta con todo el entrenamiento externo y predice el fold reservado.\n'
           '4. Se repite hasta evaluar los cinco folds. Cada estudiante aparece una vez en validación externa.\n\n'
           'Así se obtienen predicciones **OOF (fuera del fold)**: cada registro se predice sin que ningún '
           'registro de ese estudiante haya participado en el ajuste o en la selección de sus parámetros.\n\n'
           '**Tamaños reales de los folds externos:**'),
        table(fold_sizes),
        md('**Cinco folds internos para seleccionar hiperparámetros.** En cada iteración externa, solo los '
           'estudiantes de sus cuatro bloques de entrenamiento se redistribuyen en cinco folds internos, '
           'manteniendo otra vez juntas todas las filas de cada persona. Se evalúan las combinaciones '
           'del grid y las propuestas de Random Search, TPE, DEAP y Successive Halving. Se elige método y configuración '
           'por menor RMSE medio interno a fidelidad completa. **El fold externo reservado no participa '
           'en esa búsqueda.** Imputación, escalado y codificación también se aprenden dentro de cada ajuste.\n\n'
           '**Modelo final y test por periodo.** Tras obtener la evaluación OOF, se ejecuta una nueva '
           'búsqueda agrupada sobre todo entrenamiento y se ajusta el modelo final. Solo entonces se evalúa '
           f'el test del periodo **{MODEL_REPORT["test_period"]}**, que permanece fuera de los folds y de la '
           'selección de parámetros.\n\n'
           '**Cómo interpretar la evaluación.** GroupKFold separa estudiantes, pero no estratifica por nota '
           'ni impone orden temporal: la evaluación en un periodo posterior la aporta el test reservado. '
           'Las métricas se calculan por registro; agrupar no asigna automáticamente el mismo peso a cada '
           'estudiante si tiene varias filas. En el dashboard se reporta la media de las métricas de los '
           'cinco folds externos cuando no hay filtros.'),
    ], className='details cv-explanation'))
    return explanation


SPLIT_CV = html.Div([
    title('METODOLOGÍA COMPARTIDA', 'Split y validación cruzada',
          'La misma separación por estudiante y periodo para todos los modelos predictivos.'),
    html.Div([card('Test por periodo académico',
        f'El periodo **{MODEL_REPORT["test_period"]}** se reserva como test. Train contiene los cinco periodos anteriores. '
        f'Se excluyen de train **{MODEL_REPORT["purged_overlap_rows"]} filas de estudiantes presentes en el periodo reservado**. '
        'Así se evalúan un periodo posterior y estudiantes que no participaron en entrenamiento. '
        'Las inconsistencias de negocio se excluyen antes de imputar.', split_figure()),
        groupkfold_card()], className='grid'),
])
SPLIT_CV.children.append(linear_pipeline_section(MODEL, {
    'LABELS': LABELS, 'md': md, 'table': table, 'title': title, 'notice': notice,
}))


MODELS = html.Div([
    title('MODELOS LINEALES', 'Evaluación del modelo lineal', 'Comparación con la referencia, generalización y análisis de errores.'),
    card('Pipeline y búsqueda de parámetros', '**Numéricas:** mediana, log1p en tiempos y StandardScaler. '
        '**Categóricas:** moda y one-hot. **Objetivo:** escala original. **Referencia:** Dummy (media). '
        f'**Grid de LinearSVR:** C = `{MODEL_REPORT["grid"]["modelo__C"]}`; epsilon = `{MODEL_REPORT["grid"]["modelo__epsilon"]}`. '
        f'**Selección final:** C = {MODEL_REPORT["best_params"]["modelo__C"]}, '
        f'epsilon = {MODEL_REPORT["best_params"]["modelo__epsilon"]}. '
        'Se minimiza RMSE agrupado usando únicamente train. Todo el preprocesamiento se ajusta dentro de cada fold. '
        'La configuración final resulta de comparar las cinco estrategias en validación interna, cuando están disponibles. '
        'ID, periodo y nota_final quedan fuera de las predictoras.'),
    math_section('svm'),
    card('Resultados de la búsqueda en train',
         'Grid Search conservada: RMSE medio de cinco folds agrupados para cada combinación. '
         'La selección final compara además Random, TPE, DEAP y Halving cuando están disponibles; '
         'la estimación OOF mostrada abajo proviene de validación anidada independiente.',
         px.density_heatmap(pd.read_csv(CACHE / 'grid_search.csv').assign(
             RMSE=lambda f: -f['mean_test_score'],
             C=lambda f: f['param_modelo__C'].astype(str),
             epsilon=lambda f: f['param_modelo__epsilon'].astype(str)),
             x='C', y='epsilon', z='RMSE', histfunc='avg', text_auto='.3f',
             color_continuous_scale='Teal', labels={'RMSE': 'RMSE medio', 'epsilon': 'Epsilon'})),
    filters('model'),
    notice('Los filtros evalúan el mismo modelo global sobre cada grupo; no entrenan modelos independientes. '
           'Validación usa predicciones fuera del fold (OOF). Test usa el modelo ajustado con todo train.'),
    html.Div([html.Label('Ver predicciones y residuos de'), dcc.RadioItems(id='model-partition',
        options=[{'label': 'Test reservado', 'value': 'test'}, {'label': 'Validación (OOF)', 'value': 'validation'}],
        value='test', inline=True, className='radio')], className='variable-select'),
    dcc.Loading(html.Div(id='model-results'), type='circle', color=PALETTE[0]),
    html.Details([html.Summary('Profundizar · intervalos, aprendizaje y coeficientes'),
        notice('Resultados globales de E3. Esta sección no cambia con los filtros.'),
        card('Intervalos bootstrap del 95 % · test',
             f'SVM lineal: **RMSE [{SVM_CI["RMSE"]["IC_2.5%"]:.4f}; {SVM_CI["RMSE"]["IC_97.5%"]:.4f}]**, '
             f'**MAPE [{SVM_CI["MAPE_%"]["IC_2.5%"]:.4f} %; {SVM_CI["MAPE_%"]["IC_97.5%"]:.4f} %]**, '
             f'**R² [{SVM_CI["R2"]["IC_2.5%"]:.4f}; {SVM_CI["R2"]["IC_97.5%"]:.4f}]**. '
             '1.000 remuestreos por estudiante del periodo test; sus registros se remuestrean juntos. '
             'Los intervalos describen esta muestra y no sustituyen una evaluación externa.'),
        html.Div(id='model-extra')], className='details'),
    card('Conclusión',
        f'El SVM reduce el **RMSE en {MODEL_REPORT["improvement"]["reducción_RMSE_vs_dummy_%"]:.2f} %** '
        f'y el **MAPE en {MODEL_REPORT["improvement"]["reducción_MAPE_vs_dummy_%"]:.2f} %** frente a Dummy. '
        f'Su capacidad predictiva es parcial. La validación externa (R² = {SVM_CV["R2"]["media_cv"]:.4f}) '
        f'se contrasta con test (R² = {SVM_RESULT["R2"]:.4f}). '
        'Ambas evaluaciones usan estudiantes separados; test también mide generalización a un periodo posterior. '
        f'Normalidad de residuos: p = {SVM_DIAG["normaltest_p"]:.3g}; '
        f'Breusch–Pagan: p = {SVM_DIAG["Breusch_Pagan_p"]:.3g}; '
        f'Spearman entre predicción y error absoluto = {SVM_DIAG["Spearman_abs_resid_vs_ajustado"]:.4f}. '
        'El modelo aporta una referencia predictiva, pero sus coeficientes no demuestran efectos causales. '
        'Los resultados describen esta muestra y este periodo; conviene comprobar estabilidad en periodos futuros.'),
])

from search_results import optimization_section
HISTORICAL_SVM = json.loads((BOOK / 'resultados/e3/modelos_lineales.json').read_text(encoding='utf-8'))
MODELS.children.insert(3, html.Details([
    html.Summary('Resultados de las cinco búsquedas en train · selección y tiempos'),
    optimization_section(MODEL_REPORT, {'md': md, 'table': table, 'card': card}),
    html.Details([html.Summary('Referencia histórica · Grid Search anterior'),
        md(f'Parámetros históricos: `{json.dumps(HISTORICAL_SVM["best_params"], ensure_ascii=False)}`. '
           f'RMSE interno histórico: **{HISTORICAL_SVM["selection_rmse"]:.6f}**. '
           'Sus reportes y predicciones se conservan en resultados/e3; la ejecución nueva tiene una carpeta versionada independiente.')
    ], className='details'),
], className='details'))

from classic_models import create_classics
MODEL_UI = {
    'TRAIN': TRAIN, 'TEST': TEST, 'MODEL_REPORT': MODEL_REPORT, 'FEATURES': FEATURES,
    'NUMERIC': NUMERIC, 'CATEGORICAL': CATEGORICAL, 'LABELS': LABELS, 'DEFAULTS': DEFAULTS,
    'COURSE': COURSE, 'PROGRAM': PROGRAM, 'TARGET': TARGET, 'PALETTE': PALETTE,
    'card': card, 'md': md, 'table': table, 'notice': notice, 'title': title, 'stats': stats,
    'filters': filters, 'subset': subset,
}
CLASSICS = create_classics(app, MODEL_UI)
from original_models import create_originals
ORIGINALS = create_originals(app, MODEL_UI)

def eda_navigation():
    return html.Div([dcc.Tabs(id='eda-tabs',value='explore',mobile_breakpoint=0,className='sub-tabs',
        persistence=True,persistence_type='session',children=[
            dcc.Tab(label='Variables y contexto',value='variables',className='tab',selected_className='tab-selected'),
            dcc.Tab(label='Exploración interactiva',value='explore',className='tab',selected_className='tab-selected')]),
        html.Div(id='eda-page')])


def predictive_navigation():
    return html.Div([dcc.Tabs(id='predictive-tabs',value='split',mobile_breakpoint=0,className='sub-tabs',
        persistence=True,persistence_type='session',children=[
            dcc.Tab(label='Split y CV',value='split',className='tab',selected_className='tab-selected'),
            dcc.Tab(label='Modelos lineales',value='linear',className='tab',selected_className='tab-selected'),
            dcc.Tab(label='Modelos clásicos',value='classic',className='tab',selected_className='tab-selected'),
            dcc.Tab(label='Modelos originales',value='original',className='tab',selected_className='tab-selected')]),
        html.Div(id='predictive-page')])


app.layout = html.Div([
    html.Header([html.A([html.Span('p', className='brand-mark'), html.Div([html.Strong('precálculo')])], href='/', className='brand'),
        html.Div([html.Span(className='status-dot'), 'Proyecto de investigación · 2026'], className='header-note')], className='topbar'),
    html.Main([dcc.Tabs(id='main-tabs', value='intro', mobile_breakpoint=0, className='main-tabs', children=[
        dcc.Tab(label='01  Introducción', value='intro', className='tab', selected_className='tab-selected'),
        dcc.Tab(label='02  EDA', value='eda', className='tab', selected_className='tab-selected'),
        dcc.Tab(label='03  Modelos predictivos', value='models', className='tab', selected_className='tab-selected'),
    ],persistence=True,persistence_type='session'),html.Div(id='main-page',children=defer_details(INTRO,'intro'))], className='container'),
    html.Footer([html.Strong('Precálculo · Universidad del Norte'),
                 html.Span('Autores: Rubiel Velásquez y Valentina Figueroa.'),
                 html.Span('Fuentes: datos originales de ALEK · Entregable 3 · Ejecución reproducible'),
                 html.Span('Interacción: pasa el cursor, selecciona leyendas, amplía y descarga los gráficos.')], className='footer'),
])


@app.callback(Output('main-page','children'),Input('main-tabs','value'))
def render_main_page(value):
    if value=='models':return predictive_navigation()
    if value=='eda':return eda_navigation()
    return defer_details(INTRO,'intro')


@app.callback(Output('eda-page','children'),Input('eda-tabs','value'))
def render_eda_page(value):
    return defer_details(VARIABLES if value=='variables' else EDA,'eda-'+str(value))


@app.callback(Output('predictive-page','children'),Input('predictive-tabs','value'))
def render_predictive_page(value):
    pages={'split':SPLIT_CV,'linear':MODELS,'classic':CLASSICS,'original':ORIGINALS}
    return defer_details(pages.get(value,SPLIT_CV),'predictive-'+str(value))


@app.callback(Output('eda-results', 'children'), Input('eda-program', 'value'), Input('eda-course', 'value'),
              Input('eda-mode', 'value'), Input('eda-variable', 'value'), Input('eda-category', 'value'))
def render_eda(program, course, mode, variable, category='cumplimiento_temas'):
    data = subset(TRAIN, program, course)
    if data.empty:
        return notice('Esta combinación no tiene registros de entrenamiento. Selecciona otro programa o asignatura, o vuelve a Todos.')
    group = None if mode == 'general' else mode
    distribution = px.histogram(data, x=TARGET, color=group, nbins=30, barmode='overlay', histnorm='percent',
        opacity=.65, labels=LABELS, color_discrete_map=GROUP_COLORS)
    distribution.update_xaxes(range=[.4, 5.1])
    distribution.update_yaxes(title='Porcentaje dentro de cada categoría')
    distribution.add_vline(x=data[TARGET].mean(), line_dash='dash', line_color='#243d52', annotation_text='Media filtrada')
    by = group or COURSE
    box = px.box(data, y=by, x=TARGET, color=by, points=False, labels=LABELS, color_discrete_map=GROUP_COLORS)
    box.update_layout(showlegend=False)
    box.update_layout(height=max(410, 110 + 30 * data[by].nunique()))
    box.update_yaxes(tickmode='array', tickvals=data[by].unique(),
        ticktext=['<br>'.join(textwrap.wrap(course_text(str(v)), width=28)) for v in data[by].unique()])
    box.update_xaxes(range=[.4, 5.1])
    sampled = data.sample(min(2500, len(data)), random_state=42)
    scatter = px.scatter(sampled, x=variable, y=TARGET, color=group or COURSE, labels=LABELS,
        color_discrete_map=GROUP_COLORS, opacity=.3, hover_data=[PROGRAM, COURSE])
    scatter.update_yaxes(range=[.4, 5.1])
    if group and data[group].nunique() > 6:
        distribution.update_layout(height=700)
        scatter.update_layout(height=700)
    rho = data[[variable, TARGET]].corr(method='spearman').iloc[0, 1]
    tests = eda_associations(program, course)
    significant = int(tests['p Holm'].lt(.05).sum())
    matrix_evidence = (f' **Resultado de la matriz:** {significant} de {len(tests)} pares de variables '
        'muestran evidencia de asociación después de corregir por las múltiples comparaciones (p Holm < 0.05).')
    correlation = data[NUMERIC + [TARGET]].corr(method='spearman')
    heatmap = go.Figure(go.Heatmap(z=correlation.to_numpy(), x=[LABELS[c] for c in correlation.columns],
        y=[LABELS[c] for c in correlation.index], zmin=-1, zmax=1, zmid=0,
        colorscale=['#bd5681', '#fbfcfc', '#187b80'], colorbar={'title': 'ρ'},
        hovertemplate='%{y}<br>%{x}<br>Spearman: %{z:.3f}<extra></extra>'))
    missing = data[NUMERIC].isna().mean().mul(100).rename('Faltantes (%)').reset_index().rename(columns={'index': 'Variable'})
    missing['Variable'] = missing['Variable'].map(LABELS)
    missfig = px.bar(missing, x='Faltantes (%)', y='Variable', orientation='h', color_discrete_sequence=[PALETTE[2]])
    missfig.update_xaxes(range=[0, max(.1, missing['Faltantes (%)'].max() * 1.2)])
    associations = data[NUMERIC + [TARGET]].corr(method='spearman')[TARGET].drop(TARGET).dropna()
    strongest = associations.abs().idxmax() if not associations.empty else None
    strongest_text = (f'En el grupo filtrado, **{LABELS[strongest]}** tiene la mayor asociación monotónica con la nota '
                      f'(ρ = {associations[strongest]:.3f}). La asociación no implica causalidad.') if strongest else 'No hay variación suficiente para estimar asociaciones.'
    paired_n = int(data[[variable, TARGET]].dropna().shape[0])
    direction = ('los valores más altos de esta variable tienden a acompañarse de notas más altas' if rho > 0 else
                 'los valores más altos de esta variable tienden a acompañarse de notas más bajas' if rho < 0 else
                 'no se observa una tendencia creciente o decreciente')
    scatter_summary = (f'Se revisó la relación entre **{LABELS[variable]}** y la **nota del primer parcial** '
        f'en **{paired_n:,} registros completos** del grupo filtrado. Con **Spearman (ρ = {rho:.3f})**, '
        f'{direction}. Se usa este método porque compara el orden de los valores y permite estudiar '
        'tendencias que no tienen que seguir una línea recta. La asociación no demuestra causalidad.'
        if pd.notna(rho) else
        f'Se revisó la relación entre **{LABELS[variable]}** y la **nota del primer parcial**, '
        'pero no hay suficientes valores con variación para calcular Spearman en este grupo.')
    predictor_pairs = tests.loc[tests['Variable A'].ne(LABELS[TARGET]) & tests['Variable B'].ne(LABELS[TARGET])]
    leading_pairs = (predictor_pairs.assign(magnitude=predictor_pairs['ρ'].abs()).nlargest(2, 'magnitude')
                     if not predictor_pairs.empty else predictor_pairs)
    redundancy_summary = (' Entre las predictoras, los pares con mayor asociación en valor absoluto son '
        + '; '.join(f'**{row["Variable A"]} / {row["Variable B"]}** (ρ = {row["ρ"]:.3f})'
                    for _, row in leading_pairs.iterrows())
        + '. Estas relaciones ayudan a revisar si aportan información parecida; no justifican eliminar variables por sí solas.'
        if not leading_pairs.empty else ' No hay pares de predictoras con datos suficientes y variación para resumir su asociación.')
    matrix_summary = (f'Con **Spearman**, se revisaron las asociaciones entre las variables numéricas. '
        + (f'**{LABELS[strongest]}** es la más asociada con la nota en valor absoluto '
           f'(ρ = {associations[strongest]:.3f}).' if strongest else
           'No hay variación suficiente para identificar la variable más asociada con la nota.')
        + redundancy_summary)
    counts = data[category].fillna('Sin dato').value_counts().rename_axis('Categoría').reset_index(name='Filas')
    counts['Porcentaje'] = 100 * counts['Filas'] / len(data)
    category_colors = {name: GROUP_COLORS.get(name, PALETTE[i] if i < len(PALETTE) else
                       f'hsl({(i * 137.5) % 360:.0f},55%,42%)') for i, name in enumerate(counts['Categoría'])}
    categorical = px.bar(counts.sort_values('Porcentaje'), x='Porcentaje', y='Categoría', color='Categoría', orientation='h',
        text='Porcentaje', custom_data=['Filas'], color_discrete_map=category_colors,
        color_discrete_sequence=PALETTE)
    categorical.update_traces(texttemplate='%{x:.1f} %', textposition='outside',
        hovertemplate='%{y}<br>%{customdata[0]} filas<br>%{x:.2f} %<extra></extra>')
    categorical.update_layout(showlegend=False, height=max(410, 110 + 32 * len(counts)), xaxis_title='Porcentaje del grupo filtrado')
    categorical.update_yaxes(tickmode='array', tickvals=counts['Categoría'],
        ticktext=['<br>'.join(textwrap.wrap(course_text(str(v)), width=28)) for v in counts['Categoría']])
    categorical.update_xaxes(range=[0, max(5, counts['Porcentaje'].max() * 1.16)])
    bins = np.unique(TRAIN['Dominio_Final'].quantile([0, .25, .5, .75, 1]).to_numpy())
    domain_data = data.copy()
    domain_data['Intervalo de dominio final'] = pd.cut(domain_data['Dominio_Final'], bins=bins, include_lowest=True)
    intervals = domain_data['Intervalo de dominio final'].cat.categories
    interval_labels = {v: f'{max(0, v.left):.0f} a {v.right:.0f} temas' for v in intervals}
    domain_data['Intervalo de dominio final'] = domain_data['Intervalo de dominio final'].map(interval_labels).astype('string')
    domain_box = px.box(domain_data, x='Intervalo de dominio final', y=TARGET, color='Intervalo de dominio final',
        labels=LABELS, points=False, category_orders={'Intervalo de dominio final': list(interval_labels.values())},
        color_discrete_sequence=PALETTE)
    domain_box.update_layout(showlegend=False)
    domain_box.update_yaxes(range=[.4, 5.1])
    time_skew = data[[c for c in NUMERIC if c.startswith('Tiempo')]].skew().dropna()
    skew_text = ('La mayor asimetría de tiempos aparece en **' + LABELS[time_skew.abs().idxmax()] +
                 f'** ({time_skew.loc[time_skew.abs().idxmax()]:.3f}); sus densidades permiten inspeccionar la cola.'
                 if len(time_skew) else 'No hay variación suficiente para estimar la asimetría de tiempos en este grupo.')
    treatment = pd.DataFrame([
        {'Elemento': 'Objetivo', 'Evidencia gráfica': 'Histograma, densidad de nota y cajas', 'Tratamiento': 'Conservar la escala original y reportar error en puntos de nota.'},
        {'Elemento': 'Faltantes', 'Evidencia gráfica': 'Porcentaje de faltantes por variable', 'Tratamiento': 'Mediana numérica y moda categórica aprendidas solo dentro del fold.'},
        {'Elemento': 'Tiempos', 'Evidencia gráfica': 'Densidades de las tres medidas de tiempo', 'Tratamiento': 'log1p después de imputar; StandardScaler en las numéricas.'},
        {'Elemento': 'Categorías', 'Evidencia gráfica': 'Frecuencias y cajas por grupos', 'Tratamiento': 'One-hot con referencia; conservar categorías reales poco frecuentes.'},
        {'Elemento': 'Extremos y redundancia', 'Evidencia gráfica': 'Densidades, cajas y matriz Spearman', 'Tratamiento': 'Conservar extremos válidos e interpretar coeficientes junto con la redundancia.'},
    ])
    conclusion = html.Article([html.H3('Conclusiones del EDA y tratamientos de datos'),
        md(f'En el grupo filtrado, la nota tiene **media {data[TARGET].mean():.3f}**, '
           f'**mediana {data[TARGET].median():.3f}** y rango **{data[TARGET].min():.2f}–{data[TARGET].max():.2f}**. '
           'El histograma, su densidad y las cajas muestran la distribución en la escala académica.\n\n' +
           strongest_text + ' La matriz de Spearman también permite revisar asociaciones entre predictoras antes de '
           'interpretar un efecto aislado. El scatter y las cajas por dominio final complementan esa lectura.\n\n' +
           skew_text + ' El gráfico de faltantes identifica dónde falta medición; las frecuencias categóricas '
           'describen concentración y categorías poco representadas. Las diferencias entre grupos son descriptivas.\n\n'
           '**Decisiones del pipeline de E3:** se detallan abajo, junto a los gráficos que las respaldan. '
           'Los filtros describen subgrupos; no vuelven a elegir ni ajustar transformaciones. '
           'Se excluye `nota_final` por ser posterior al parcial. Las reglas de negocio se auditan antes de imputar '
           'y se conservan los outliers válidos de los registros reales.'), table(treatment)], className='card')
    return html.Div([
        notice('Las pruebas usan los datos de entrenamiento que quedan al aplicar los filtros, sin rellenar los faltantes. '
               'En los resultados, n es la cantidad de registros y gl son los grados de libertad del contraste. '
               'Un p < 0.05 se interpreta como evidencia contra la situación de referencia que explica cada tarjeta; '
               'un p mayor no demuestra que esa situación sea cierta. Son resultados exploratorios: algunos estudiantes '
               'pueden tener más de un registro y aquí no se corrige esa dependencia. Solo la matriz ajusta sus p '
               'por realizar muchas comparaciones. Una asociación no demuestra que una variable cause cambios en otra.'),
        stats([('Registros de train', f'{len(data):,}', 'Después de aplicar filtros'), ('Nota media', f'{data[TARGET].mean():.2f}', 'Escala original'),
               ('Mediana', f'{data[TARGET].median():.2f}', 'Centro de la distribución'), ('Dispersión', f'{data[TARGET].std():.2f}', 'Desviación estándar')]),
        html.Div([card('Cómo se distribuyen las notas', 'Cada color representa una categoría de la vista seleccionada. '
            'Los porcentajes se normalizan dentro de cada categoría, por lo que permiten comparar grupos de distinto tamaño. '
            'La línea marca la media de todas las filas filtradas. Se conserva la escala original y los extremos válidos.\n\n' + normality(data[TARGET]), distribution),
            card('Diferencias entre grupos', 'La caja muestra el 50 % central y la línea interior, la mediana. '
            'Los bigotes describen la dispersión; los extremos siguen incluidos aunque no se dibujen como puntos. '
            'Las diferencias no demuestran un efecto del programa o de la asignatura.\n\n' + group_test(data, by, TARGET), box)], className='grid'),
        html.Div([card('Una relación para explorar', scatter_summary, scatter, details=
            f'La nube dibuja una muestra reproducible de **{len(sampled):,} de {len(data):,}** filas; '
            'los cálculos usan todos los registros completos del grupo filtrado. Cambia la variable arriba '
            'y usa la leyenda para aislar categorías.\n\n' +
            '**¿Por qué Spearman?** Queremos saber si, cuando una variable aumenta, la otra tiende a aumentar '
            'o disminuir, aunque esa relación no siga una línea recta. Spearman ordena los valores de menor a mayor '
            'y compara sus posiciones; por eso, un valor extremo influye menos por su tamaño. Pearson, en cambio, '
            'mide qué tan bien se describe la relación con una línea recta usando los valores originales. '
            'Que los datos no sigan una distribución normal no basta para descartar Pearson.\n\n' +
            comparison_text(data, variable, TARGET)),
            card('Asociaciones y redundancia', matrix_summary, heatmap, details=
            '**¿Qué muestra esta matriz?** Resume las relaciones entre todas las variables numéricas, '
            'incluida la nota del parcial. Busca una variable en las filas y otra en las columnas: '
            'la celda donde se cruzan representa su correlación de Spearman. Pasa el cursor para ver el valor.\n\n'
            '**Cómo leer los colores.** Verde azulado indica que ambas variables tienden a aumentar juntas; '
            'rosado indica que una tiende a disminuir cuando la otra aumenta. Un tono cercano al blanco '
            'indica poca relación de este tipo. Cuanto más intenso es el color, mayor es la correlación en '
            'valor absoluto. La diagonal vale 1 porque compara cada variable consigo misma; '
            'los dos lados de la diagonal repiten los mismos pares.\n\n'
            '**¿Dónde aparece la redundancia?** En las relaciones entre las propias predictoras: '
            'dos variables muy asociadas pueden aportar parte de la misma información al modelo. '
            'Por ejemplo, el avance se calcula como dominio final menos dominio inicial, por lo que estas '
            'tres medidas están relacionadas por definición. Esto ayuda a interpretar sus coeficientes '
            'con cautela; no es motivo suficiente para eliminar automáticamente una variable. '
            'La fila o columna de la nota, en cambio, permite revisar qué predictoras se asocian con el resultado académico.\n\n'
            '**¿Qué aporta la tabla de abajo?** Presenta cada par una sola vez, con el valor de la correlación, '
            'la cantidad de registros usados y la evidencia estadística. Permite distinguir una relación '
            'intensa de una relación con p pequeño: son aspectos diferentes. ' + matrix_evidence)], className='grid'),
        html.Details([html.Summary('Estadísticos de todas las asociaciones de la matriz'),
            md('**De la matriz a la tabla.** Cada fila desarrolla una celda de la matriz: '
               '**Variable A** y **Variable B** identifican el par comparado. No se incluyen la diagonal '
               'ni las repeticiones en orden inverso. Se muestran tanto relaciones entre predictoras '
               'como relaciones de una predictora con la nota; **no es una tabla de importancia del modelo**.\n\n'
               '**n** cuenta los registros que tienen ambos valores y puede cambiar entre filas por los datos '
               'faltantes. **ρ (Spearman)** es el número representado por el color de esa celda; '
               'su signo indica la dirección y su cercanía a −1 o +1, la intensidad. '
               'Las filas están ordenadas de menor a mayor **p ajustado (Holm)**, no por intensidad de correlación.\n\n'
               '**¿Por qué hay dos p? Ambos corresponden a Spearman; no son un p de Pearson y otro de Spearman.**\n\n'
               '- **p sin ajuste (Spearman):** evalúa la ausencia de asociación para ese par de variables, '
               'considerándolo de manera individual.\n'
               '- **p ajustado (Holm):** parte del mismo contraste y tiene en cuenta que se están revisando '
               'muchos pares a la vez. Esto reduce el riesgo de señalar asociaciones por azar. **Usamos esta '
               'columna para la conclusión de la matriz:** un valor menor que 0.05 indica evidencia de asociación.\n\n'
               'Estos p preguntan por la asociación entre variables; **no comparan Pearson con Spearman**. '
               'Esa es la función del p de la diferencia ρ − r mostrado junto a la nube de puntos. '
               'Un p pequeño tampoco significa que la relación sea fuerte: para eso se observa el tamaño de ρ.\n\n'
               '**Cálculo y límites.** «Asintótico» usa una aproximación para más de 500 registros; '
               '«Permutación» compara el resultado con 1999 reordenamientos al azar de una variable para '
               '500 registros o menos (semilla 42, corrección +1). Se omiten pares sin variación o con menos de '
               '5 registros completos. El ajuste Holm cubre los pares de esta vista, no la exploración de muchos filtros. '
               'La notación 1.0e−03 equivale a 0.001.'),
            table(tests.assign(**{c: tests[c].map(lambda p: f'{p:.3e}' if p > 0 else '< 1e-300') for c in ['p', 'p Holm']})
                  .rename(columns={'ρ': 'ρ (Spearman)', 'p': 'p sin ajuste (Spearman)',
                                   'p Holm': 'p ajustado (Holm)', 'Método p': 'Cómo se calculó p'})),
            md('Fuentes: [Shapiro–Wilk](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.shapiro.html), '
               '[Kruskal–Wallis](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.kruskal.html), '
               '[Spearman](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.spearmanr.html), '
               '[bootstrap pareado](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html).')], className='details'),
        html.Div([card('Frecuencias de las variables categóricas',
            f'Variable seleccionada: **{LABELS[category]}**. Cada barra muestra su participación en el grupo filtrado; '
            'el cursor indica el número de filas. Cambia la variable para revisar todas las categorías; '
            'no se agrupan ni eliminan las poco frecuentes.\n\n' + frequency_test(data[category]), categorical),
            card('Nota del primer parcial por dominio final',
            'El dominio final se divide en intervalos definidos por los cuartiles de todo train. '
            'Los límites se mantienen al filtrar, para que los grupos sean comparables. '
            'Las cajas permiten ver si el centro y la dispersión de la nota cambian con los temas dominados. '
            'Los extremos válidos permanecen incluidos aunque no se dibujen como puntos; esta asociación no demuestra causalidad.\n\n' +
            group_test(domain_data, 'Intervalo de dominio final', TARGET), domain_box)], className='grid'),
        html.Article([html.H3('Distribución y densidad de las variables numéricas'),
            md('Los histogramas muestran densidad (área total uno), no número de filas. Las curvas suaves **KDE** '
               'estiman dónde se concentran los valores: un pico más alto indica mayor concentración por unidad del eje. '
               'Se calculan sobre todos los valores disponibles del grupo filtrado; no se imputan ni recortan extremos. '
               'La suavización puede difuminar ceros o límites, por lo que se lee junto al histograma. '
               'Los ejes tienen unidades distintas: no se comparan alturas de densidad entre variables.'),
            html.Div(density_cards(program, course), className='density-grid')], className='card'),
        html.Article([html.H3('Distribución de las variables categóricas'),
            md('Cada gráfico muestra todas las categorías de una variable y su proporción dentro del grupo filtrado. '
               'Las barras permiten identificar categorías predominantes y poco representadas. '
               'El cursor muestra el número de filas y el porcentaje; los filtros de programa y asignatura '
               'se aplican a los siete gráficos.\n\n'
               '**Prueba utilizada: chi-cuadrado de bondad de ajuste.** Evalúa si los conteos difieren '
               'de una misma frecuencia por categoría. **χ²** es el estadístico de la prueba; '
               '**gl**, sus grados de libertad (número de categorías menos uno); y **p**, el valor que '
               'usamos para evaluar la diferencia. Un **p < 0.05** indica diferencias estadísticamente '
               'significativas entre los conteos.'),
            html.Div(categorical_cards(program, course), className='category-grid')], className='card'),
        card('Dónde faltan mediciones', 'Las ausencias se concentran en tiempos en el análisis global. '
            'La barra muestra el porcentaje del grupo filtrado. No se imputan para EDA; en el modelo, '
            'la mediana se aprende dentro del pipeline y del fold.\n\n' + missing_test(data[NUMERIC].rename(columns=LABELS)), missfig),
        conclusion,
    ])


@lru_cache(maxsize=24)
def eda_associations(program, course):
    return association_tests(subset(TRAIN, program, course), NUMERIC + [TARGET], LABELS)


@lru_cache(maxsize=24)
def density_cards(program, course):
    data = subset(TRAIN, program, course)
    return [card(LABELS[column], f'{int(data[column].notna().sum()):,} valores disponibles · '
        f'{int(data[column].isna().sum()):,} ausentes.\n\n' + normality(data[column]),
        numeric_density(data[column], LABELS[column], PALETTE[index % len(PALETTE)]))
        for index, column in enumerate(NUMERIC + [TARGET])]


@lru_cache(maxsize=24)
def categorical_cards(program, course):
    data = subset(TRAIN, program, course)
    cards = []
    for column in CATEGORICAL:
        counts = data[column].fillna('Sin dato').value_counts().rename_axis('Categoría').reset_index(name='Filas')
        counts['Porcentaje'] = 100 * counts['Filas'] / len(data)
        colors = {name: GROUP_COLORS.get(name, PALETTE[i] if i < len(PALETTE) else
                  f'hsl({(i * 137.5) % 360:.0f},55%,42%)') for i, name in enumerate(counts['Categoría'])}
        figure = px.bar(counts.sort_values('Porcentaje'), x='Porcentaje', y='Categoría', color='Categoría',
            orientation='h', custom_data=['Filas'], color_discrete_map=colors, text='Porcentaje')
        figure.update_traces(texttemplate='%{x:.1f} %', textposition='outside',
            hovertemplate='%{y}<br>%{customdata[0]} filas<br>%{x:.2f} %<extra></extra>')
        figure.update_yaxes(title=None, tickmode='array', tickvals=counts['Categoría'],
            ticktext=['<br>'.join(textwrap.wrap(course_text(str(value)), width=28)) for value in counts['Categoría']])
        figure.update_xaxes(title='Porcentaje del grupo filtrado', range=[0, max(5, counts['Porcentaje'].max() * 1.18)])
        figure.update_layout(showlegend=False, height=max(340, 140 + 38 * len(counts)))
        cards.append(card(LABELS[column], f'{len(counts)} categorías · {len(data):,} filas en el grupo filtrado.\n\n' + frequency_test(data[column]), figure))
    return cards


def metric_rows(train, test, global_view):
    rows = []
    for label, data in [('Validación (5 folds)', train), ('Test reservado', test)]:
        for name, column in [('Dummy media', 'dummy'), ('SVM lineal', 'svm')]:
            if data.empty:
                continue
            values = metrics(data[TARGET], data[column])
            if global_view and label.startswith('Validación'):
                values = FOLDS[FOLDS['Modelo'] == name][list(values)].mean().to_dict()
            if column == 'dummy':
                conclusion = 'Referencia: predice la media aprendida en entrenamiento.'
            else:
                dummy_values = metrics(data[TARGET], data['dummy'])
                conclusion = ('Reduce RMSE frente a Dummy.' if values['RMSE'] < dummy_values['RMSE'] else
                              'No reduce RMSE frente a Dummy en este grupo.')
                if values['R²'] is None:
                    conclusion += ' R² no definido: nota constante o una sola fila.'
                elif values['R²'] <= 0:
                    conclusion += ' No mejora la referencia de la media del grupo (R² ≤ 0).'
                else:
                    conclusion += f' Explica {100 * values["R²"]:.1f} % de la variación de la nota.'
                if label.startswith('Validación'):
                    conclusion += ' Contrastar con test.'
            if len(data) < 30:
                conclusion += ' Grupo con menos de 30 filas: lectura inestable.'
            diagnostic = residual_diagnostics(data, TARGET, column, NUMERIC)
            conclusion += ' ' + diagnostic_reading(diagnostic)
            rows.append({'Evaluación': label, 'Modelo': name, 'n': len(data), **values,
                         'p-valor (White)': diagnostic['white_p'], 'p-valor (BDS)': diagnostic['bds_p'],
                         'Conclusión': conclusion})
    return pd.DataFrame(rows)


@app.callback(Output('model-results', 'children'), Input('model-program', 'value'), Input('model-course', 'value'),
              Input('model-partition', 'value'))
def render_models(program, course, partition):
    train, test = subset(TRAIN, program, course), subset(TEST, program, course)
    if train.empty and test.empty:
        return notice('No hay filas para esta combinación. Cambia los filtros o selecciona Todos.')
    global_view = program == '__all__' and course == '__all__'
    results = metric_rows(train, test, global_view)
    melted = results.melt(id_vars=['Modelo', 'Evaluación'], value_vars=['RMSE', 'MAE'], var_name='Métrica', value_name='Valor')
    bars = px.bar(melted, x='Evaluación', y='Valor', color='Modelo', facet_col='Métrica',
        barmode='group', color_discrete_map=MODEL_COLORS)
    bars.update_yaxes(matches=None, showticklabels=True)
    bars.for_each_annotation(lambda a: a.update(
        text=a.text.split('=')[-1],
        font={'color': '#435568', 'size': 14}, opacity=1))
    data = test if partition == 'test' else train
    diagnostic_rows = []
    for label, frame in [('Validación (5 folds)', train), ('Test reservado', test)]:
        if frame.empty:
            continue
        for name, column in [('Dummy media', 'dummy'), ('SVM lineal', 'svm')]:
            diagnostic = residual_diagnostics(frame, TARGET, column, NUMERIC)
            diagnostic_rows.append({'Evaluación': label, 'Modelo': name,
                'n White': diagnostic['white_n'], 'LM White': diagnostic['white_lm'],
                'gl White': diagnostic['white_df'], 'Estado White': diagnostic['white_status'],
                'n BDS': diagnostic['bds_n'], 'Estadístico BDS': diagnostic['bds_stat'],
                'ε BDS': diagnostic['bds_epsilon'], 'Estado BDS': diagnostic['bds_status']})
    shown_results = results.assign(**{c: results[c].map(format_p) for c in ['p-valor (White)', 'p-valor (BDS)']})
    parts = [card('Resultados de validación y test', 'RMSE y MAE se expresan en puntos de nota: **menor es mejor**. '
        'Los ejes de cada panel son independientes.', bars),
        html.Article([html.H3('Estadísticos y lectura de resultados'),
            md('Sin filtros, validación muestra la **media de las métricas de cinco folds**, en el flujo E3. '
               'Con filtros, se calculan métricas agrupadas de predicciones **OOF** (incluido MAE, agregado para este dashboard). '
               'Test siempre usa predicciones de evaluación final. MAPE se expresa en porcentaje y es sensible a notas bajas.\n\n'
               '**White:** p < 0.05 indica evidencia de varianza no constante de los errores. '
               '**BDS:** p < 0.05 rechaza que los residuos sean independientes y tengan la misma distribución (IID). '
               'Un p mayor no demuestra que los supuestos se cumplan. Los diagnósticos de validación usan todos '
               'los residuos OOF reunidos, no el promedio de p de los folds. Son contrastes exploratorios sin ajuste múltiple.'),
            table(shown_results),
            html.Details([html.Summary('Cómo se calcularon White y BDS'),
                md('**Residuo = nota observada − predicción.** Se usan las predicciones guardadas de cada '
                   'modelo y el subgrupo filtrado, sin reentrenar.\n\n'
                   '**Test de White: evalúa la constancia de la varianza de los errores (homocedasticidad).** '
                   'El p-valor del estadístico LM contrasta varianza constante frente a cambios asociados '
                   'a las ocho predictoras numéricas, con constante, cuadrados e interacciones; no incluye las '
                   'categóricas. Se usan registros completos, sin imputar. Se escalan las numéricas para estabilidad '
                   'de cálculo y el rango del diseño determina los grados de libertad. Se requieren al menos '
                   '30 registros completos y 10 grados de libertad residuales en la regresión auxiliar.\n\n'
                   '**Test de BDS: evalúa la independencia de los residuos.** Su hipótesis incluye también '
                   'que los residuos tengan la misma distribución (IID). Se usa dimensión 2 y '
                   'ε = 1.5 veces la desviación estándar muestral de los residuos; '
                   'p bilateral. Se requieren al menos 30 residuos con variación. Se conserva el orden del CSV '
                   'al aplicar filtros: estos registros no forman una trayectoria temporal individual. '
                   'El resultado depende de ese orden y rechazar IID no identifica si falla la independencia, '
                   'la igualdad de distribución o ambas. En OOF se reúnen cinco modelos ajustados distintos.\n\n'
                   'Los registros repetidos de estudiantes no se corrigen por grupo en estas pruebas. '
                   '«No estimable» indica insuficiencia de datos, variables constantes o cálculo degenerado; '
                   'la tabla siguiente detalla el motivo.\n\n'
                   'Fuentes: [White](https://www.statsmodels.org/stable/generated/statsmodels.stats.diagnostic.het_white.html) '
                   'y [BDS](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.bds.html), statsmodels.'),
                table(pd.DataFrame(diagnostic_rows))], className='details')], className='card')]
    if data.empty:
        parts.append(notice('No hay filas en la partición elegida para estos filtros. Cambia a la otra partición.'))
        return html.Div(parts)
    score = metrics(data[TARGET], data['svm'])
    baseline = metrics(data[TARGET], data['dummy'])
    gain = (1 - score['RMSE'] / baseline['RMSE']) * 100 if baseline['RMSE'] else 0
    parts.insert(0, stats([('Filas evaluadas', f'{len(data):,}', 'Test' if partition == 'test' else 'Validación OOF'),
        ('RMSE · SVM', f'{score["RMSE"]:.3f}', 'Puntos de nota · menor es mejor'),
        ('Error absoluto', f'{score["MAE"]:.3f}', 'MAE · puntos de nota'), ('Mejora vs Dummy', f'{gain:.1f} %', 'Reducción del RMSE')]))
    sample = data.sample(min(3000, len(data)), random_state=42).copy()
    pred = px.scatter(sample, x=TARGET, y='svm', color=COURSE, labels={**LABELS, 'svm': 'Nota predicha · SVM'},
        color_discrete_map=GROUP_COLORS, opacity=.35, hover_data=[PROGRAM, COURSE])
    bounds = [min(.4, data['svm'].min() - .1), max(5.1, data['svm'].max() + .1)]
    pred.add_trace(go.Scatter(x=bounds, y=bounds, mode='lines', line={'color': '#243d52', 'dash': 'dash'}, name='Predicción ideal'))
    pred.update_xaxes(range=bounds)
    pred.update_yaxes(range=bounds)
    sample['Residuo'] = sample[TARGET] - sample['svm']
    residual = px.scatter(sample, x='svm', y='Residuo', color=COURSE, opacity=.35,
        labels={'svm': 'Nota predicha · SVM', COURSE: 'Asignatura'}, color_discrete_map=GROUP_COLORS,
        hover_data=[PROGRAM, TARGET])
    residual.add_hline(y=0, line_dash='dash', line_color='#243d52')
    bins = pd.cut(data[TARGET], bins=np.linspace(.49, 5.01, 10))
    calibration = data.groupby(bins, observed=True)[[TARGET, 'svm', 'dummy']].mean().reset_index(drop=True)
    counts = data.groupby(bins, observed=True).size().to_numpy()
    calibration['n'] = counts
    curve = go.Figure()
    for column, name in [('svm', 'SVM lineal'), ('dummy', 'Dummy media')]:
        curve.add_trace(go.Scatter(x=calibration[TARGET], y=calibration[column], mode='lines+markers', name=name,
            customdata=counts, hovertemplate='Real: %{x:.2f}<br>Predicción media: %{y:.2f}<br>Filas: %{customdata}<extra>%{fullData.name}</extra>',
            line={'color': MODEL_COLORS[name]}))
    curve.add_trace(go.Scatter(x=[.5, 5], y=[.5, 5], mode='lines', name='Ideal', line={'color': '#879ba4', 'dash': 'dash'}))
    curve.update_layout(xaxis_title='Nota real media por intervalo', yaxis_title='Nota predicha media')
    outside = int(((data['svm'] < .5) | (data['svm'] > 5)).sum())
    parts.extend([html.Div([card('Predicción frente a realidad', f'Cada punto es una fila; se dibujan **{len(sample):,} de {len(data):,}**. '
        'La diagonal representa coincidencia perfecta. Arriba de ella el modelo sobreestima; abajo, subestima. '
        f'LinearSVR no acota sus predicciones: **{outside:,}** quedan fuera de 0,5–5,0 en este grupo. No se recortan.', pred),
        card('En qué notas aparece el error', 'Residuo = nota real − predicción. Un valor positivo indica subestimación. '
        'La dispersión alrededor de cero permite inspeccionar errores sistemáticos y cambios de variabilidad. '
        'Se utiliza la misma muestra de puntos del gráfico anterior.', residual)], className='grid'),
        card('La predicción media a lo largo de la escala', 'Las filas se agrupan en nueve intervalos de nota real. '
        'Compara las medias del SVM y Dummy con la diagonal ideal; el cursor muestra el tamaño de cada intervalo. '
        'Este resumen usa todas las filas filtradas y ayuda a detectar sobreestimación de notas bajas o subestimación de notas altas.', curve)])
    return html.Div(parts)


learning = pd.DataFrame(MODEL_REPORT['learning'])[['n_entrenamiento', 'RMSE_train_media', 'RMSE_validacion_media']].rename(
    columns={'n_entrenamiento': 'Filas de entrenamiento', 'RMSE_train_media': 'Entrenamiento', 'RMSE_validacion_media': 'Validación'})
learning_fig = px.line(learning.melt(id_vars='Filas de entrenamiento', var_name='Evaluación', value_name='RMSE'),
    x='Filas de entrenamiento', y='RMSE', color='Evaluación', markers=True, color_discrete_sequence=PALETTE)
top = COEFFICIENTS.assign(magnitude=COEFFICIENTS['Coeficiente'].abs()).nlargest(12, 'magnitude')
top['Variable'] = top['Variable'].str.replace(r'^.*?__', '', regex=True)
coef_fig = px.bar(top, x='Coeficiente', y='Variable', orientation='h',
    color=np.where(top['Coeficiente'] >= 0, 'Positivo', 'Negativo'), color_discrete_sequence=PALETTE,
    category_orders={'Variable': top['Variable'].tolist()})
MODELS.children[-2].children.append(html.Div([
    card('Curva de aprendizaje',
         f'Resultados de datos reales: con {int(learning.iloc[-1]["Filas de entrenamiento"]):,} filas, '
         f'RMSE de entrenamiento = {learning.iloc[-1]["Entrenamiento"]:.4f} y validación = {learning.iloc[-1]["Validación"]:.4f}. '
         'La brecha interna se interpreta junto con el test reservado. '
         + MODEL_REPORT.get('learning_method', ''), learning_fig),
    card('Doce coeficientes de mayor magnitud', 'Coeficientes del modelo global reproducido, en el espacio transformado. '
         'Las numéricas están escaladas y las categorías se comparan contra referencias; la magnitud no es importancia causal '
         'y las redundancias dificultan interpretaciones aisladas.', coef_fig)], className='grid'))

DEEP_DETAILS = MODELS.children[-2]
DEEP_DETAILS.children.append(html.Article([
    html.H3('Reporte completo de coeficientes (β) y disponibilidad de p-valores'),
    md('Se reportan **todos los términos del SVM lineal**, su intercepto y las categorías de referencia. '
       '**Orden descendente de |β|**: los términos de mayor magnitud aparecen primero, incluido el intercepto; '
       'las referencias fijadas en cero quedan al final. El CSV descargado conserva ese mismo orden. '
       'Las numéricas están estandarizadas; los tiempos además pasan por log1p. Los coeficientes categóricos '
       'se interpretan frente a la referencia indicada (β fijado en cero, no estimado).\n\n'
       '**LinearSVR no calcula p-valores, errores estándar ni pruebas t para sus coeficientes.** '
       'Los p de las comparaciones entre modelos del tablero no evalúan sus β. '
       'Un p-valor de OLS correspondería a otro '
       'modelo y no puede atribuirse a este SVM. La dependencia entre avance y dominios y los registros repetidos por estudiante '
       'también requieren cautela antes de hacer inferencia. Las magnitudes no representan efectos causales.\n\n'
       '[Documentación del modelo](https://scikit-learn.org/stable/modules/generated/sklearn.svm.LinearSVR.html).'),
    md('**Cómo leer β.** Si una numérica entra como `z=(x−μ)/σ`, aumentar una unidad de z '
       '(una desviación estándar aprendida en train) cambia la predicción en β puntos, manteniendo fijas '
       'las demás columnas transformadas. En unidades originales el cambio es `β·Δx/σ`. '
       '**En tiempos/tasa con log1p**, de x a x+Δ el cambio es `β·ln[(1+x+Δ)/(1+x)]/σ_log`: '
       'β no representa el efecto de una hora adicional constante.\n\n'
       '**Categorías:** β es la diferencia respecto a la categoría de referencia, no respecto al promedio del grupo. '
       '**Intercepto:** corresponde a numéricas transformadas centradas y todas las categorías de referencia; '
       'esa combinación puede no existir como estudiante real. **|β| no es una importancia global:** '
       'compara cambios de 1 DE numérica con saltos 0→1 categóricos, unidades distintas.\n\n'
       '**Dependencias:** avance = dominio final − dominio inicial. No es factible cambiar el avance '
       'manteniendo ambos dominios fijos. Estos son contrastes algebraicos condicionales del modelo, '
       'no intervenciones educativas ni efectos causales. La regularización y la redundancia afectan los coeficientes.'),
    html.Details([html.Summary('Ejemplos de lectura en unidades originales'),
                  md('Cálculos obtenidos del escalador y los coeficientes guardados. Para log1p se usa la mediana train '
                     'como punto inicial; no son simulaciones de cambios conjuntamente factibles.'),
                  table(beta_examples(MODEL, LABELS))], className='details'),
    table(FULL_COEFFICIENTS),
    html.Button('Descargar reporte de coeficientes', id='download-coefficients-button', n_clicks=0, className='secondary-button'),
    dcc.Download(id='coefficient-download'),
], className='card coefficient-report'))

MODELS.children.insert(-1, html.Details([
    html.Summary('Ejemplo de predicción · configurar características'),
    html.Article([
        html.H3('Predecir una nota con el modelo ajustado'),
        md('El formulario carga un registro válido de ejemplo. Selecciona categorías y escribe las características '
           'numéricas para obtener una predicción con **el mismo pipeline evaluado en E3**. '
           'No se reentrena el modelo ni se emplea test para ajustar valores.\n\n'
           'El avance se calcula automáticamente como dominio final − inicial. '
           'Los campos numéricos vacíos se imputan con la mediana aprendida en train, salvo los dominios, '
           'necesarios para validar las reglas. Las categorías de temas, cuartiles y cumplimiento se eligen como '
           'características observadas: sus reglas por asignatura y semestre no pueden reconstruirse con este esquema. '
           'Programa, asignatura y división deben formar una combinación presente en entrenamiento.'),
        build_form(TRAIN, NUMERIC, CATEGORICAL, LABELS, DEFAULTS),
    ], className='card'),
], className='details prediction-details'))


@app.callback(Output(input_id('avance_precalculo_aleks'), 'value'),
              Input(input_id('Dominio_Inicial'), 'value'), Input(input_id('Dominio_Final'), 'value'))
def update_example_advance(initial, final):
    return float(final) - float(initial) if initial is not None and final is not None else None


@app.callback(Output('prediction-result', 'children'), Input('predict-button', 'n_clicks'),
              *[State(input_id(column), 'value') for column in NUMERIC + CATEGORICAL])
def render_prediction(clicks, *values):
    if not clicks:
        return notice('Ajusta las características y pulsa «Predecir nota». Los filtros de evaluación de arriba no cambian este formulario.')
    try:
        prediction, record, extrapolated = predict_record(MODEL, dict(zip(NUMERIC + CATEGORICAL, values)), TRAIN)
    except (TypeError, ValueError) as error:
        return html.Div([html.Strong('Revisa las características: '), str(error)], className='notice validation-error')
    result = [stats([('Nota predicha · SVM', f'{prediction:.3f}', 'Estimación sin recorte'),
                     ('Error medio en test', f'{SVM_RESULT["MAE"]:.3f}', 'MAE global · no es un intervalo individual')]),
              md('El resultado es una estimación del modelo, no una nota observada. '
                 'El MAE describe el error medio en el test completo y no garantiza el error de este caso.')]
    if extrapolated:
        result.append(notice('Estos valores quedan fuera del rango observado en train: ' + ', '.join(LABELS[c] for c in extrapolated) + '. La predicción extrapola.'))
    if not .5 <= prediction <= 5:
        result.append(notice('La predicción está fuera del rango observado de 0,5–5,0. LinearSVR no acota la salida; se muestra el resultado sin recortarlo.'))
    missing = [LABELS[c] for c in NUMERIC if pd.isna(record[c])]
    if missing:
        result.append(md('Campos imputados con el pipeline ajustado: **' + ', '.join(missing) + '**.'))
    return html.Div(result, className='prediction-output')


@app.callback(Output('coefficient-download', 'data'), Input('download-coefficients-button', 'n_clicks'), prevent_initial_call=True)
def download_coefficients(clicks):
    displayed = FULL_COEFFICIENTS.copy()
    displayed['Variable / término'] = displayed['Variable / término'].map(course_text)
    return dcc.send_data_frame(displayed.to_csv, 'coeficientes_svm_lineal.csv', index=False)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8050, debug=False)

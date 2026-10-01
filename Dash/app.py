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
from charts import numeric_density, comparison_figures
from prediction import build_form, coefficient_report, input_id, predict_record

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
AUGMENTATION_DATA = pd.read_csv(CACHE / 'augmentation.csv.gz')
COMPARISON_DETAILS = json.loads((CACHE / 'comparison_details.json').read_text(encoding='utf-8'))
AUG = pd.read_csv(BOOK / 'comparacion_aumentacion/comparacion_train.csv', sep=';', decimal=',', encoding='utf-8-sig')
SELECTION = json.loads((BOOK / 'comparacion_aumentacion/seleccion.json').read_text(encoding='utf-8'))
DOCUMENT = (BOOK / '00_seleccion_base_datos.md').read_text(encoding='utf-8')
MODEL_REPORT = json.loads((BOOK / 'resultados/modelos_lineales.json').read_text(encoding='utf-8'))
EDA_REPORT = json.loads((BOOK / 'resultados/eda.json').read_text(encoding='utf-8'))
SVM_RESULT = next(r for r in MODEL_REPORT['test'] if r['modelo'] == 'SVM lineal')
SVM_CV = {r['metrica']: r for r in MODEL_REPORT['cv'] if r['modelo'] == 'SVM lineal'}
SVM_CI = {r['metrica']: r for r in MODEL_REPORT['bootstrap'] if r['modelo'] == 'SVM lineal'}
SVM_DIAG = next(r for r in MODEL_REPORT['residuals'] if r['modelo'] == 'SVM lineal')
TARGET = 'nota_primer_parcial'
PROGRAM = 'programa_en_matricula'
COURSE = 'Mat_Curso_Asignatura_Relacionada'
NUMERIC = TRAIN.drop(columns=['dummy', 'svm', TARGET]).select_dtypes(include='number').columns.tolist()
FEATURES = list(MODEL.feature_names_in_)
CATEGORICAL = [c for c in FEATURES if c not in NUMERIC]
DEFAULTS = TRAIN[FEATURES].dropna().iloc[0].to_dict()
COURSES = {'MAT1011': 'Álgebra y Trigonometría', 'MAT1100': 'Cálculo I (ANEC)',
           'MAT1101': 'Cálculo I', 'MAT4190': 'Matemáticas Fundamentales'}
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
server = app.server


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
    return dcc.Markdown(text, className='prose', link_target='_blank')


def notice(text):
    return html.Div(text, className='notice')


def card(title, text, figure=None, wide=False):
    children = [html.H3(title), md(text)]
    if figure is not None:
        styled = style(figure)
        children.append(dcc.Graph(figure=styled, style={'height': f'{styled.layout.height}px', 'width': '100%'},
            config={'displaylogo': False, 'scrollZoom': False,
            'toImageButtonOptions': {'format': 'png', 'scale': 2}}, responsive=True))
    return html.Article(children, className='card' + (' wide' if wide else ''))


def style(fig):
    graph_height = fig.layout.height or 410
    fig.update_layout(template='plotly_white', font={'family': 'Segoe UI, Arial, sans-serif', 'size': 12, 'color': '#435568'},
        paper_bgcolor='white', plot_bgcolor='white', margin={'l': 40, 'r': 24, 't': 30, 'b': 70},
        legend={'orientation': 'h', 'y': -0.25, 'x': 0}, height=graph_height,
        colorway=PALETTE, hoverlabel={'bgcolor': '#fff', 'font_size': 13})
    fig.update_xaxes(gridcolor='#edf1f3', zerolinecolor='#dfe6e9', automargin=True)
    fig.update_yaxes(gridcolor='#edf1f3', zerolinecolor='#dfe6e9', automargin=True)
    if any(annotation.text == 'R<sup>2</sup>' for annotation in (fig.layout.annotations or [])):
        # Reservar espacio bajo la barra flotante para que no oculte R² al pasar el cursor.
        fig.update_layout(height=445, margin={'t': 65})
        fig.update_annotations(y=1.02, yanchor='bottom')
    if any(trace.type == 'heatmap' and len(trace.y) > 5 for trace in fig.data):
        fig.update_layout(height=570, margin={'l': 165, 'r': 40, 't': 20, 'b': 155})
        fig.update_xaxes(tickangle=-40, tickfont={'size': 10})
        fig.update_yaxes(tickfont={'size': 10})
    return fig


def stats(items):
    return html.Div([html.Div([html.Small(label), html.Strong(value), html.Span(detail)], className='stat')
                     for label, value, detail in items], className='stats compact-stats' if len(items) == 2 else 'stats')


def table(frame):
    return html.Div(html.Table([html.Thead(html.Tr([html.Th(c) for c in frame.columns])),
        html.Tbody([html.Tr([html.Td('—' if pd.isna(v) else f'{v:.4f}' if isinstance(v, (float, np.floating)) else str(v))
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
        options = [{'label': 'Todos', 'value': '__all__'}] + [{'label': f'{v} · {COURSES[v]}' if v in COURSES else v, 'value': v} for v in values]
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
    card('Punto de partida', DOCUMENT.split('## Contexto académico e institucional')[0].split('\n', 1)[1], wide=True),
    card('Contexto académico del proyecto', section(DOCUMENT, 'Contexto académico e institucional'), wide=True),
    card('La pregunta de investigación', 'Este proyecto busca responder la pregunta:\n\n'
         '**¿En qué medida los resultados del nivelatorio de precálculo y la información académica disponible '
         'permiten predecir la nota del primer parcial de la asignatura relacionada?**\n\n' +
         section(DOCUMENT, 'Propósito del proyecto'), wide=True),
    html.Div([html.Span('01'), html.Div([html.H3('Comprender los datos'), html.P('Variables, aumentación y exploración interactiva.')]),
              html.Span('02'), html.Div([html.H3('Evaluar la predicción'), html.P('Validación, test y errores del modelo lineal.')])], className='journey'),
])

VARIABLES = html.Div([
    title('01 / VARIABLES', 'Variables del proyecto', 'Definiciones, fuente original y necesidad de aumentación.'),
    card('Diccionario del proyecto', section(DOCUMENT, 'Descripción de las variables del esquema final'), wide=True),
    html.Div([card('Necesidad de aumentar la muestra', '**Los lineamientos del proyecto solicitan un mínimo de 20.000 registros.** '
                  'La base original no alcanza ese tamaño; por ello se exploran técnicas controladas de aumentación.\n\n' +
                  section(DOCUMENT, 'Estado original de la base de datos').split('Con esta cantidad de observaciones')[0]),
              card('Exploración de alternativas para aumentación de datos',
                  'Se evaluaron dos alternativas para ampliar la muestra conservando su estructura:\n\n'
                  '- **Perturbación local controlada:** ruido aditivo y multiplicativo acotado alrededor de registros originales.\n'
                  '- **Interpolación entre vecinos para regresión:** adaptación híbrida de SMOTE/SMOTER que combina '
                  'registros compatibles y usa perturbación como respaldo cuando no hay vecinos.\n\n'
                  'El proceso, los gráficos de comparación y la selección de técnica se encuentran en la subsección **Aumentación de datos**.')], className='grid'),
    notice('Las variantes sintéticas amplían el conjunto de trabajo, pero no equivalen a nuevos estudiantes ni a observaciones independientes.'),
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
         'Los archivos seleccionados cumplen las tres reglas: **cero incumplimientos en train y test**. '
         'Si aparece una inconsistencia, se excluye antes de imputar; no se corrige como si fuera un faltante. '
         'Los outliers válidos se conservan. `nota_final` se reserva para auditoría y nunca entra al modelo.'),
])


def augmentation():
    frame = AUG.copy()
    frame['Técnica'] = frame['alternativa'].map({1: 'Perturbación local', 2: 'Interpolación entre vecinos'})
    frame['Semilla'] = frame['semilla'].astype(str)
    scores = px.line(frame, x='Semilla', y='puntaje', color='Técnica', markers=True,
        labels={'puntaje': 'Distancia media (menor es mejor)'}, color_discrete_sequence=PALETTE)
    components = frame.groupby('Técnica')[['KS_media', 'Wasserstein_media', 'TV_categorica',
        'faltantes_media', 'Spearman_error', 'TV_combinaciones']].mean().reset_index().melt(id_vars='Técnica')
    components['variable'] = components['variable'].map({'KS_media': 'KS', 'Wasserstein_media': 'Wasserstein',
        'TV_categorica': 'Categorías', 'faltantes_media': 'Faltantes', 'Spearman_error': 'Spearman', 'TV_combinaciones': 'Combinaciones'})
    comparison = px.bar(components, x='variable', y='value', color='Técnica', barmode='group',
        labels={'variable': 'Componente del puntaje', 'value': 'Distancia media'}, color_discrete_sequence=PALETTE)
    improvement = 100 * (1 - SELECTION['puntajes_medios_train']['1'] / SELECTION['puntajes_medios_train']['2'])
    conclusion = card('Conclusión', '**La perturbación local conserva mejor las distribuciones entre estas dos técnicas. '
        'Esta comparación no demuestra una mejora predictiva.**\n\n'
        'Por ese criterio se seleccionó la **alternativa 1** para todo el proyecto: EDA, modelos y dashboard. '
        'Sus archivos de train y test cumplen las reglas de negocio sin exclusiones. La ventaja se mantiene '
        'en las cinco semillas y en seis comparaciones al retirar un componente del puntaje. '
        'Las variantes sintéticas amplían la base de trabajo, pero no representan nuevos estudiantes independientes.')
    conclusion.children.append(stats([('Reducción de la distancia media', f'{improvement:.2f} %', 'Perturbación frente a interpolación'),
                                     ('Estabilidad de la selección', '5 de 5', 'Semillas favorecen perturbación local')]))
    return html.Div([
        title('02 / AUMENTACIÓN', 'Comparación de técnicas de aumentación', 'Separación de estudiantes, generación de registros y contraste con la fuente original.'),
        card('Propósito y recorrido de la aumentación',
             'La base original no alcanza el mínimo de 20.000 registros solicitado en el proyecto. '
             'La aumentación crea variantes sintéticas de observaciones existentes para ampliar el conjunto '
             'de trabajo, procurando conservar sus distribuciones, categorías y relaciones académicas.\n\n'
             'Esta sección presenta el proceso en orden: **separar estudiantes y reservar test**, '
             '**generar registros con dos alternativas**, **contrastar los sintéticos con los originales de train** '
             'y **seleccionar la técnica de mayor fidelidad**. La elección se hace únicamente con entrenamiento; '
             'test permanece reservado para la evaluación posterior. Las variantes no equivalen a nuevos estudiantes.'),
        stats([('Originales con objetivo', '1.497', '1.196 train · 301 test'),
               ('Registros tras aumentar', '30.000', '24.000 train · 6.000 test')]),
        html.Div([card('Segmentación por estudiante antes de aumentar',
            'Antes de generar variantes, se establece qué estudiantes pertenecerán a entrenamiento y cuáles '
            'a prueba. Esta separación evita que registros de una misma persona y sus variantes sintéticas '
            'aparezcan en ambos conjuntos, lo que haría demasiado optimista la evaluación.\n\n'
            '**Excluir filas sin objetivo → separar estudiantes → aumentar cada partición.** '
            'Tras excluir 30 filas sin nota, se agrupan los registros por estudiante y se estratifica la separación '
            'usando intervalos del promedio de su nota. Train conserva 1.196 filas de 1.184 estudiantes; '
            'test, 301 filas de 297 estudiantes. No se comparten IDs. El test se reserva desde este momento y '
            'no interviene en la elección de técnica. Las variantes se generan por separado dentro de cada partición.'),
            card('Métodos de generación evaluados',
            '- **Perturbación estocástica local con ruido aditivo y multiplicativo:** '
            'modifica valores numéricos con variaciones acotadas, estimadas dentro de cada partición; recalcula el avance '
            'y rechaza inconsistencias y duplicados.\n'
            '- **Interpolación entre vecinos compatibles para regresión (adaptación híbrida de SMOTE/SMOTER):** '
            'combina hasta cinco vecinos con las mismas categorías, faltantes y estados cero. '
            'Si no hay vecinos, usa perturbación local como respaldo (7,80 % de nuevas filas de train en la semilla ilustrada).\n\n'
            'La comparación busca fidelidad distribucional; no balancea notas raras ni ensaya SMOTER/SMOGN estándar.')], className='grid'),
        title('CONTRASTE GRÁFICO', 'Datos originales frente a registros sintéticos',
              'Compara las dos técnicas con los 1.196 originales de train. Solo se contrastan las filas nuevas, para que conservar originales no oculte diferencias.'),
        html.Div([html.Label('Variable que se compara'), dcc.Dropdown([{'label': LABELS[c], 'value': c} for c in [TARGET] + NUMERIC],
            TARGET, id='aug-variable', clearable=False)], className='variable-select'),
        dcc.Loading(html.Div(id='augmentation-results'), type='circle', color=PALETTE[0]),
        html.Div([card('Estabilidad del puntaje en cinco semillas',
            'Se generan cinco versiones de cada alternativa sobre los mismos originales de train, cambiando la semilla '
            'que controla el azar. Para cada versión se promedian seis distancias de distribuciones y asociaciones; '
            '**menor puntaje significa mayor parecido con los originales**. La comparación nunca usa test. '
            'La perturbación obtiene un puntaje medio de **0,013587**, frente a **0,029090** de interpolación. '
            'La separación entre las curvas indica que la elección no depende de una sola generación.', scores),
            card('Distancias de distribuciones y asociaciones',
            'Cada barra es la media de un diagnóstico en las cinco semillas; menor distancia indica más fidelidad.\n\n'
            '- **Kolmogorov–Smirnov (KS):** mayor diferencia entre las proporciones acumuladas de originales y sintéticos. '
            'Por ejemplo, 0,05 equivale a una separación máxima de cinco puntos porcentuales. No es un p-valor.\n'
            '- **Wasserstein normalizada:** desplazamiento necesario para aproximar una distribución a otra, dividido por '
            'la desviación estándar original para comparar variables de distintas unidades.\n'
            '- **Variación total:** diferencia entre proporciones de categorías o combinaciones de categorías; cero significa igualdad.\n'
            '- **Faltantes:** diferencia de proporciones de valores ausentes.\n'
            '- **Cambio de Spearman:** cuánto cambian las asociaciones monotónicas entre variables.\n\n'
            'Las distancias describen aspectos distintos y sus valores no son errores de predicción.', comparison)], className='grid'),
        conclusion,
    ])


EDA = html.Div([
    title('03 / EXPLORACIÓN', 'Análisis exploratorio de los datos', 'Distribuciones, calidad y asociaciones sobre entrenamiento válido.'),
    notice(f'Técnica seleccionada: perturbación local. {len(TRAIN):,} registros válidos de train, '
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
    return go.Figure(go.Sankey(arrangement='snap', node={'pad': 26, 'thickness': 16,
        'label': [f'{train_n + test_n:,} registros · perturbación local', f'{train_n:,} train',
                  f'{test_n:,} test reservado', f'{len(TRAIN):,} train válido · 5 folds', f'{len(TEST):,} test válido'],
        'color': ['#879ba4', PALETTE[0], PALETTE[2], PALETTE[0], PALETTE[2]]},
        link={'source': [0, 0, 1, 2], 'target': [1, 2, 3, 4],
              'value': [train_n, test_n, len(TRAIN), len(TEST)], 'color': ['#cce7e5', '#dce2f5', '#cce7e5', '#dce2f5']}))


def cv_figure():
    z = np.zeros((5, 5), dtype=int)
    np.fill_diagonal(z, 1)
    return go.Figure(go.Heatmap(z=z, x=['Bloque 1', 'Bloque 2', 'Bloque 3', 'Bloque 4', 'Bloque 5'],
        y=['Fold 1', 'Fold 2', 'Fold 3', 'Fold 4', 'Fold 5'], colorscale=[[0, '#cce7e5'], [1, '#5268b9']], showscale=False,
        text=np.where(z == 1, 'Validación', 'Entrenamiento'), texttemplate='%{text}',
        hovertemplate='%{y} · %{x}<br>%{text}<extra></extra>', xgap=5, ygap=5))


MODELS = html.Div([
    title('MODELOS LINEALES', 'Evaluación del modelo lineal', 'Comparación con la referencia, generalización y análisis de errores.'),
    html.Div([card('Test reservado desde el inicio', 'Los estudiantes se separaron **antes de la aumentación**. Se reutilizan los archivos '
        'seleccionados de perturbación local, sin volver a dividirlos. El flujo muestra train y test después de '
        'la aumentación: cero incumplimientos de reglas de negocio y ninguna fila excluida.', split_figure()),
        card('Validación dentro del entrenamiento', '**Cinco folds estratificados por bins de nota.** En cada iteración, cuatro bloques entrenan '
             'y uno valida. Verde = entrenamiento; azul = validación. El esquema es conceptual: los bloques se forman con filas mezcladas. '
             'Test permanece fuera. Sin ID persistente, estos folds no pueden agruparse por estudiante.', cv_figure())], className='grid'),
    card('Un pipeline que aprende solo del entrenamiento', '**Numéricas:** mediana, log1p en las tres medidas de tiempo y StandardScaler. '
        '**Categóricas:** moda y one-hot. **Objetivo:** escala original. **Modelos:** DummyRegressor (media) y '
        'LinearSVR (C = 1, ε = 0,1, semilla 42). Las transformaciones se ajustan dentro de cada fold. `nota_final` permanece excluida.'),
    filters('model'),
    notice('Los filtros evalúan el mismo modelo global sobre cada grupo; no entrenan modelos independientes. '
           'Validación usa predicciones fuera del fold (OOF). Test usa el modelo ajustado con todo train.'),
    html.Div([html.Label('Ver predicciones y residuos de'), dcc.RadioItems(id='model-partition',
        options=[{'label': 'Test reservado', 'value': 'test'}, {'label': 'Validación (OOF)', 'value': 'validation'}],
        value='test', inline=True, className='radio')], className='variable-select'),
    dcc.Loading(html.Div(id='model-results'), type='circle', color=PALETTE[0]),
    html.Details([html.Summary('Profundizar · intervalos, aprendizaje y coeficientes'),
        notice('Resultados globales del notebook. Esta sección no cambia con los filtros.'),
        card('Intervalos bootstrap del 95 % · test',
             f'SVM lineal: **RMSE [{SVM_CI["RMSE"]["IC_2.5%"]:.4f}; {SVM_CI["RMSE"]["IC_97.5%"]:.4f}]**, '
             f'**MAPE [{SVM_CI["MAPE_%"]["IC_2.5%"]:.4f} %; {SVM_CI["MAPE_%"]["IC_97.5%"]:.4f} %]**, '
             f'**R² [{SVM_CI["R2"]["IC_2.5%"]:.4f}; {SVM_CI["R2"]["IC_97.5%"]:.4f}]**. '
             '1.000 remuestreos por filas del test aumentado; las variantes no representan estudiantes independientes. '
             'Los intervalos describen esta muestra y no sustituyen una evaluación externa.'),
        html.Div(id='model-extra')], className='details'),
    card('Conclusión',
        f'El SVM reduce el **RMSE en {MODEL_REPORT["improvement"]["reducción_RMSE_vs_dummy_%"]:.2f} %** '
        f'y el **MAPE en {MODEL_REPORT["improvement"]["reducción_MAPE_vs_dummy_%"]:.2f} %** frente a Dummy. '
        f'Su capacidad predictiva es parcial. La validación interna (R² = {SVM_CV["R2"]["media_cv"]:.4f}) '
        f'supera el test (R² = {SVM_RESULT["R2"]:.4f}); '
        'variantes sintéticas cercanas en folds distintos podrían hacer optimista la validación, hipótesis que requiere IDs persistentes. '
        f'Normalidad de residuos: p = {SVM_DIAG["normaltest_p"]:.3g}; '
        f'Breusch–Pagan: p = {SVM_DIAG["Breusch_Pagan_p"]:.3g}; '
        f'Spearman entre predicción y error absoluto = {SVM_DIAG["Spearman_abs_resid_vs_ajustado"]:.4f}. '
        'El modelo aporta una referencia predictiva, pero sus coeficientes no demuestran efectos causales. '
        'Se recomienda validar por estudiante y evaluar el test original antes de avanzar hacia un uso operativo.'),
])

app.layout = html.Div([
    html.Header([html.A([html.Span('p', className='brand-mark'), html.Div([html.Strong('precálculo')])], href='/', className='brand'),
        html.Div([html.Span(className='status-dot'), 'Proyecto de investigación · 2026'], className='header-note')], className='topbar'),
    html.Main([dcc.Tabs(id='main-tabs', value='intro', mobile_breakpoint=0, className='main-tabs', children=[
        dcc.Tab(label='01  Introducción', value='intro', children=INTRO, className='tab', selected_className='tab-selected'),
        dcc.Tab(label='02  EDA', value='eda', children=dcc.Tabs(id='eda-tabs', value='explore', mobile_breakpoint=0, className='sub-tabs', children=[
            dcc.Tab(label='Variables y contexto', value='variables', children=VARIABLES, className='tab', selected_className='tab-selected'),
            dcc.Tab(label='Aumentación de datos', value='augmentation', children=augmentation(), className='tab', selected_className='tab-selected'),
            dcc.Tab(label='Exploración interactiva', value='explore', children=EDA, className='tab', selected_className='tab-selected')]), className='tab', selected_className='tab-selected'),
        dcc.Tab(label='03  Modelos lineales', value='models', children=MODELS, className='tab', selected_className='tab-selected'),
    ])], className='container'),
    html.Footer([html.Strong('Precálculo · Universidad del Norte'), html.Span('Fuentes: Jupyter Book del proyecto · Resultados de la ejecución documentada'),
                 html.Span('Interacción: pasa el cursor, selecciona leyendas, amplía y descarga los gráficos.')], className='footer'),
])


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
    box.update_yaxes(tickmode='array', tickvals=data[by].unique(), ticktext=data[by].unique())
    box.update_xaxes(range=[.4, 5.1])
    sampled = data.sample(min(2500, len(data)), random_state=42)
    scatter = px.scatter(sampled, x=variable, y=TARGET, color=group or COURSE, labels=LABELS,
        color_discrete_map=GROUP_COLORS, opacity=.3, hover_data=[PROGRAM, COURSE])
    scatter.update_yaxes(range=[.4, 5.1])
    if group and data[group].nunique() > 6:
        distribution.update_layout(height=700)
        scatter.update_layout(height=700)
    rho = data[[variable, TARGET]].corr(method='spearman').iloc[0, 1]
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
           '**Decisiones del pipeline del notebook:** se detallan abajo, junto a los gráficos que las respaldan. '
           'Los filtros describen subgrupos; no vuelven a elegir ni ajustar transformaciones. '
           'Se excluye `nota_final` por ser posterior al parcial. Las reglas de negocio se auditan antes de imputar '
           'y las variantes sintéticas no equivalen a estudiantes independientes.'), table(treatment)], className='card')
    return html.Div([
        stats([('Registros de train', f'{len(data):,}', 'Después de aplicar filtros'), ('Nota media', f'{data[TARGET].mean():.2f}', 'Escala original'),
               ('Mediana', f'{data[TARGET].median():.2f}', 'Centro de la distribución'), ('Dispersión', f'{data[TARGET].std():.2f}', 'Desviación estándar')]),
        html.Div([card('Cómo se distribuyen las notas', 'Cada color representa una categoría de la vista seleccionada. '
            'Los porcentajes se normalizan dentro de cada categoría, por lo que permiten comparar grupos de distinto tamaño. '
            'La línea marca la media de todas las filas filtradas. El notebook conserva la escala original y los extremos válidos.', distribution),
            card('Diferencias entre grupos', 'La caja muestra el 50 % central y la línea interior, la mediana. '
            'Los bigotes describen la dispersión; los extremos siguen incluidos aunque no se dibujen como puntos. '
            'Las diferencias son descriptivas y no demuestran un efecto del programa o de la asignatura.', box)], className='grid'),
        html.Div([card('Una relación para explorar', f'Spearman sobre todas las filas filtradas: **ρ = {rho:.3f}**. '
            f'La nube dibuja una muestra reproducible de **{len(sampled):,} de {len(data):,}** filas para mantener fluidez; '
            'los cálculos usan el grupo completo. Cambia la variable arriba y usa la leyenda para aislar categorías.', scatter),
            card('Asociaciones y redundancia', strongest_text + ' El avance depende de los dominios inicial y final, '
            'por lo que sus asociaciones deben revisarse junto con la redundancia. `nota_final` está excluida. '
            'La matriz usa pares disponibles, sin imputación.', heatmap)], className='grid'),
        html.Div([card('Frecuencias de las variables categóricas',
            f'Variable seleccionada: **{LABELS[category]}**. Cada barra muestra su participación en el grupo filtrado; '
            'el cursor indica el número de filas. Cambia la variable para revisar todas las categorías; '
            'no se agrupan ni eliminan las poco frecuentes.', categorical),
            card('Nota del primer parcial por dominio final',
            'El dominio final se divide en intervalos definidos por los cuartiles de todo train. '
            'Los límites se mantienen al filtrar, para que los grupos sean comparables. '
            'Las cajas permiten ver si el centro y la dispersión de la nota cambian con los temas dominados. '
            'Los extremos válidos permanecen incluidos aunque no se dibujen como puntos; esta asociación no demuestra causalidad.', domain_box)], className='grid'),
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
               'se aplican a los siete gráficos. Las categorías no se agrupan ni se eliminan.'),
            html.Div(categorical_cards(program, course), className='category-grid')], className='card'),
        card('Dónde faltan mediciones', 'Las ausencias se concentran en tiempos en el análisis global. '
            'La barra muestra el porcentaje del grupo filtrado. No se imputan para EDA; en el modelo, '
            'la mediana se aprende dentro del pipeline y del fold.', missfig),
        conclusion,
    ])


@lru_cache(maxsize=24)
def density_cards(program, course):
    data = subset(TRAIN, program, course)
    return [card(LABELS[column], f'{int(data[column].notna().sum()):,} valores disponibles · '
        f'{int(data[column].isna().sum()):,} ausentes.',
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
            ticktext=['<br>'.join(textwrap.wrap(str(value), width=28)) for value in counts['Categoría']])
        figure.update_xaxes(title='Porcentaje del grupo filtrado', range=[0, max(5, counts['Porcentaje'].max() * 1.18)])
        figure.update_layout(showlegend=False, height=max(340, 140 + 38 * len(counts)))
        cards.append(card(LABELS[column], f'{len(counts)} categorías · {len(data):,} filas en el grupo filtrado.', figure))
    return cards


@app.callback(Output('augmentation-results', 'children'), Input('aug-variable', 'value'))
def render_augmentation(variable):
    density, cumulative, rows = comparison_figures(AUGMENTATION_DATA, variable, LABELS[variable], COMPARISON_COLORS)
    return html.Div([
        html.Div([card('Comparación de densidades: originales y sintéticos',
            'Las curvas estiman la concentración de valores de la variable seleccionada. '
            'Gris: originales de train; verde: perturbación local; coral: interpolación. '
            f'Se comparan **{COMPARISON_DETAILS["original_rows"]:,} originales** y '
            f'**{COMPARISON_DETAILS["synthetic_rows"]:,} filas nuevas por técnica**, '
            f'para la semilla {COMPARISON_DETAILS["seed"]} del notebook. '
            'El área de cada densidad se normaliza: las alturas no representan cantidades de estudiantes. '
            'Curvas próximas indican formas parecidas; la suavización se interpreta junto a la acumulada.', density),
            card('Comparación de proporciones acumuladas',
            'Para cada valor del eje horizontal, la curva indica qué proporción de registros queda por debajo o '
            'igual a ese valor. Curvas coincidentes describen distribuciones iguales; su separación revela diferencias. '
            'La mayor separación vertical frente a los originales es lo que resume KS. '
            'Las proporciones se calculan con todas las filas y se dibujan en hasta 800 umbrales observados. '
            'Usa el cursor y la leyenda para comparar las técnicas.', cumulative)], className='grid'),
        html.Article([html.H3('Resumen numérico de la comparación'),
            md('Las medias, medianas y desviaciones se calculan en las unidades de la variable seleccionada, '
               'sobre los valores disponibles. Los sintéticos se separan de los originales para contrastar cada técnica de forma justa.'),
            table(pd.DataFrame(rows))], className='card'),
    ])


def metric_rows(train, test, global_view):
    rows = []
    for name, column in [('Dummy media', 'dummy'), ('SVM lineal', 'svm')]:
        for label, data in [('Validación (5 folds)', train), ('Test reservado', test)]:
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
            rows.append({'Modelo': name, 'Evaluación': label, 'n': len(data), **values, 'Conclusión': conclusion})
    return pd.DataFrame(rows)


@app.callback(Output('model-results', 'children'), Input('model-program', 'value'), Input('model-course', 'value'),
              Input('model-partition', 'value'))
def render_models(program, course, partition):
    train, test = subset(TRAIN, program, course), subset(TEST, program, course)
    if train.empty and test.empty:
        return notice('No hay filas para esta combinación. Cambia los filtros o selecciona Todos.')
    global_view = program == '__all__' and course == '__all__'
    results = metric_rows(train, test, global_view)
    melted = results.melt(id_vars=['Modelo', 'Evaluación'], value_vars=['RMSE', 'MAE', 'R²'], var_name='Métrica', value_name='Valor')
    bars = px.bar(melted, x='Evaluación', y='Valor', color='Modelo', facet_col='Métrica',
        barmode='group', color_discrete_map=MODEL_COLORS)
    bars.update_yaxes(matches=None, showticklabels=True)
    bars.for_each_annotation(lambda a: a.update(
        text='R<sup>2</sup>' if a.text.split('=')[-1] == 'R²' else a.text.split('=')[-1],
        font={'color': '#435568', 'size': 14}, opacity=1))
    data = test if partition == 'test' else train
    parts = [card('Resultados de validación y test', 'RMSE y MAE se expresan en puntos de nota: **menor es mejor**. '
        'R² mide mejora frente a la media: **mayor es mejor** y puede ser negativo. Los ejes de cada panel son independientes.', bars),
        html.Article([html.H3('Estadísticos y lectura de resultados'),
            md('Sin filtros, validación muestra la **media de las métricas de cinco folds**, como el notebook. '
               'Con filtros, se calculan métricas agrupadas de predicciones **OOF** (incluido MAE, agregado para este dashboard). '
               'Test siempre usa predicciones de evaluación final. MAPE se expresa en porcentaje y es sensible a notas bajas.'), table(results)], className='card')]
    if data.empty:
        parts.append(notice('No hay filas en la partición elegida para estos filtros. Cambia a la otra partición.'))
        return html.Div(parts)
    score = metrics(data[TARGET], data['svm'])
    baseline = metrics(data[TARGET], data['dummy'])
    gain = (1 - score['RMSE'] / baseline['RMSE']) * 100 if baseline['RMSE'] else 0
    parts.insert(0, stats([('Filas evaluadas', f'{len(data):,}', 'Test' if partition == 'test' else 'Validación OOF'),
        ('R² · SVM', f'{score["R²"]:.3f}' if score['R²'] is not None else 'No definido', 'Grupo seleccionado'),
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
top = COEFFICIENTS.assign(magnitude=COEFFICIENTS['Coeficiente'].abs()).nlargest(12, 'magnitude').sort_values('Coeficiente')
top['Variable'] = top['Variable'].str.replace(r'^.*?__', '', regex=True)
coef_fig = px.bar(top, x='Coeficiente', y='Variable', orientation='h',
    color=np.where(top['Coeficiente'] >= 0, 'Positivo', 'Negativo'), color_discrete_sequence=PALETTE)
MODELS.children[-2].children.append(html.Div([
    card('Curva de aprendizaje',
         f'Resultados de la técnica seleccionada: con {int(learning.iloc[-1]["Filas de entrenamiento"]):,} filas, '
         f'RMSE de entrenamiento = {learning.iloc[-1]["Entrenamiento"]:.4f} y validación = {learning.iloc[-1]["Validación"]:.4f}. '
         'La brecha interna se interpreta junto con el test reservado.', learning_fig),
    card('Doce coeficientes de mayor magnitud', 'Coeficientes del modelo global reproducido, en el espacio transformado. '
         'Las numéricas están escaladas y las categorías se comparan contra referencias; la magnitud no es importancia causal '
         'y las redundancias dificultan interpretaciones aisladas.', coef_fig)], className='grid'))

DEEP_DETAILS = MODELS.children[-2]
DEEP_DETAILS.children.append(html.Article([
    html.H3('Reporte completo de coeficientes (β) y disponibilidad de p-valores'),
    md('Se reportan **todos los términos del SVM lineal**, su intercepto y las categorías de referencia. '
       'Las numéricas están estandarizadas; los tiempos además pasan por log1p. Los coeficientes categóricos '
       'se interpretan frente a la referencia indicada (β fijado en cero, no estimado).\n\n'
       '**LinearSVR no calcula p-valores, errores estándar ni pruebas t para sus coeficientes.** '
       'Un p-valor de OLS correspondería a otro '
       'modelo y no puede atribuirse a este SVM. La dependencia entre avance y dominios y las variantes sintéticas '
       'también requieren cautela antes de hacer inferencia. Las magnitudes no representan efectos causales.\n\n'
       '[Documentación del modelo](https://scikit-learn.org/stable/modules/generated/sklearn.svm.LinearSVR.html).'),
    table(FULL_COEFFICIENTS),
    html.Button('Descargar reporte de coeficientes', id='download-coefficients-button', n_clicks=0, className='secondary-button'),
    dcc.Download(id='coefficient-download'),
], className='card coefficient-report'))

MODELS.children.insert(-1, html.Details([
    html.Summary('Ejemplo de predicción · configurar características'),
    html.Article([
        html.H3('Predecir una nota con el modelo ajustado'),
        md('El formulario carga un registro válido de ejemplo. Selecciona categorías y escribe las características '
           'numéricas para obtener una predicción con **el mismo pipeline evaluado en el notebook**. '
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
    return dcc.send_data_frame(FULL_COEFFICIENTS.to_csv, 'coeficientes_svm_lineal.csv', index=False)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8050, debug=False)

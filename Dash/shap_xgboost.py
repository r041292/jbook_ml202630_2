"""TreeSHAP nativo exacto del XGBoost final, con categorías y pipeline guardados."""
import json
import textwrap

import joblib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import xgboost as xgb
from dash import Input, Output, dcc, html

from model_timing import TimingRun, file_hash


def markdown_value(value):
    """Evita que los intervalos categóricos se conviertan en enlaces Markdown."""
    text = str(value).replace('\\', '\\\\')
    for character in ('[', ']', '`', '*', '_'):
        text = text.replace(character, '\\'+character)
    return text


def compute_shap(model, training, test, target, saved_test_predictions=None):
    """Transforma sin fit y verifica eficiencia para todas las observaciones.

    Se explica el ajuste final, también en train (NO OOF). El fondo implícito
    es el cover de entrenamiento de los árboles, no los datos de test.
    """
    columns = list(model.feature_names_in_)
    frames = [training[columns], test[columns]]
    frame = pd.concat(frames, ignore_index=True)
    run = TimingRun('XGBoost · TreeSHAP exacto y verificación del pipeline', {
        'script': 'Dash/shap_xgboost.py', 'script_sha256': file_hash(__file__),
        'model_hash': joblib.hash(model), 'data_hash': joblib.hash(frame),
        'train_rows': len(training), 'test_rows': len(test), 'features': columns,
        'xgboost': xgb.__version__, 'configuration': model.named_steps['modelo'].get_params(),
        'data': 'Train válido y test temporal completos; sin valores personales en logs',
        'background': 'Cover de árboles aprendidos en train; tree_path_dependent',
        'method': 'pred_contribs=True; approx_contribs=False; CPU; DMatrix nthread=1',
        'scope': 'Sin búsqueda/refit. Predict incluye pipeline. TreeSHAP excluye transformación y DMatrix, medidos aparte.',
        'repetitions': 'Una por lote; sin calentamiento; frío/caliente no controlado',
    })
    status = 'fallida'
    try:
        booster = model.named_steps['modelo'].get_booster()
        objective = json.loads(booster.save_config())['learner']['objective']['name']
        if objective != 'reg:squarederror':
            raise ValueError('La explicación en puntos de nota requiere reg:squarederror.')
        with run.measure('Transformación explicativa', 'Pipeline guardado sin fit', len(frame)):
            transformed = model[:-1].transform(frame)
            features = list(transformed.columns)
            raw_names = [name.split('__', 1)[1] for name in features]
            if raw_names != columns or features != booster.feature_names:
                raise ValueError('Las columnas transformadas no corresponden uno a uno al esquema del modelo.')
            matrix = xgb.DMatrix(transformed, enable_categorical=True, nthread=1)
        with run.measure('Inferencia', 'Verificación pipeline final · train + test', len(frame)):
            predictions = np.asarray(model.predict(frame), dtype=float)
        with run.measure('Explicación SHAP', 'TreeSHAP exacto · train + test', len(frame)):
            values = np.asarray(booster.predict(matrix, pred_contribs=True, approx_contribs=False), dtype=float)
        if values.shape != (len(frame), len(columns)+1) or not np.isfinite(values).all():
            raise ValueError('TreeSHAP produjo dimensiones o valores inválidos.')
        residual = values.sum(axis=1) - predictions
        with run.measure('Validación de aditividad', 'Base + aportes = predicción · todas las filas', len(frame),
                         max_absolute_residual=float(np.abs(residual).max()), tolerance=1e-5):
            np.testing.assert_allclose(values.sum(axis=1), predictions, atol=1e-5, rtol=0)
            if saved_test_predictions is not None:
                np.testing.assert_allclose(predictions[len(training):], saved_test_predictions, atol=1e-12, rtol=0)
        status = 'completa'
        return {'values': values[:, :-1], 'base': values[:, -1], 'predictions': predictions,
                'features': columns, 'transformed': transformed, 'frame': frame,
                'actual': np.r_[training[target].to_numpy(), test[target].to_numpy()],
                'n_train': len(training), 'n_test': len(test), 'run_id': run.run_id,
                'max_residual': float(np.abs(residual).max())}
    finally:
        run.finish(status)


def importance(result, positions, labels):
    values = np.abs(result['values'][positions]).mean(axis=0)
    total = values.sum()
    return pd.DataFrame({'Variable': [labels.get(c, c) for c in result['features']],
                         'Media |SHAP| (puntos)': values,
                         'Importancia relativa (%)': 100*values/total if total else np.zeros_like(values)
                         }).sort_values('Media |SHAP| (puntos)', ascending=False, kind='stable')


def summary_plot(result, positions, labels):
    """Resumen de puntos con jitter visual, sin muestrear observaciones."""
    ranking = importance(result, positions, labels)
    names = ranking['Variable'].tolist()
    numeric_x, numeric_y, colors, numeric_hover = [], [], [], []
    category_x, category_y, category_hover = [], [], []
    rng = np.random.default_rng(42)  # Solo separación vertical de puntos.
    for j, column in enumerate(result['features']):
        label = labels.get(column, column)
        row = names.index(label)
        phi = result['values'][positions, j]
        data = result['transformed'].iloc[positions, j]
        jitter = rng.uniform(-.27, .27, len(positions))
        hover = [f'{label}: {value}<br>SHAP: {v:+.4f} puntos' for value, v in zip(data, phi)]
        if pd.api.types.is_numeric_dtype(data):
            lo, hi = float(data.min()), float(data.max())
            normalized = (data.to_numpy(dtype=float)-lo)/(hi-lo) if hi > lo else np.full(len(data), .5)
            numeric_x.extend(phi); numeric_y.extend(row+jitter)
            colors.extend(normalized); numeric_hover.extend(hover)
        else:
            category_x.extend(phi); category_y.extend(row+jitter); category_hover.extend(hover)
    figure = go.Figure()
    figure.add_trace(go.Scattergl(x=numeric_x, y=numeric_y, mode='markers', name='Numéricas',
        marker={'color': colors, 'colorscale': [[0, '#326ca8'], [1, '#cf3c5a']],
                'cmin': 0, 'cmax': 1, 'size': 4, 'opacity': .45,
                'colorbar': {'title': 'Valor<br>numérico', 'tickvals': [0, 1], 'ticktext': ['Bajo', 'Alto']}},
        text=numeric_hover, hovertemplate='%{text}<extra></extra>'))
    figure.add_trace(go.Scattergl(x=category_x, y=category_y, mode='markers', name='Categóricas (sin orden)',
        marker={'color': '#7d8792', 'size': 4, 'opacity': .4}, text=category_hover,
        hovertemplate='%{text}<extra></extra>'))
    figure.add_vline(x=0, line_color='#435568', line_width=1)
    figure.update_layout(meta='shap-summary', height=720, margin={'l': 220, 'r': 80, 't': 25, 'b': 90},
        xaxis_title='Aporte SHAP a la nota predicha (puntos)',
        yaxis={'tickvals': list(range(len(names))),
               'ticktext': ['<br>'.join(textwrap.wrap(name, 28)) for name in names],
               'range': [len(names)-.5, -.5], 'zeroline': False},
        legend={'orientation': 'h', 'y': -.12})
    return figure


def local_rows(result, position, labels):
    return pd.DataFrame({
        'Variable': [labels.get(c, c) for c in result['features']],
        'Valor usado por el modelo': [str(v) for v in result['transformed'].iloc[position]],
        'SHAP (puntos)': result['values'][position],
    }).sort_values('SHAP (puntos)', key=abs, ascending=False, kind='stable')


def waterfall(result, position, labels):
    rows = local_rows(result, position, labels)
    base, pred = result['base'][position], result['predictions'][position]
    names = ['Base del modelo'] + rows['Variable'].tolist() + ['Predicción XGBoost']
    values = [base] + rows['SHAP (puntos)'].tolist() + [0.]
    text = [f'{base:.4f}'] + [f'{v:+.4f}' for v in rows['SHAP (puntos)']] + [f'{pred:.4f}']
    figure = go.Figure(go.Waterfall(orientation='h',
        y=['<br>'.join(textwrap.wrap(name, 30)) for name in names], x=values,
        measure=['absolute']+['relative']*len(rows)+['total'], text=text, textposition='outside',
        increasing={'marker': {'color': '#187b80'}}, decreasing={'marker': {'color': '#db7355'}},
        totals={'marker': {'color': '#435568'}}, connector={'line': {'color': '#aab7bf'}},
        hovertemplate='%{y}<br>%{text} puntos<extra></extra>'))
    figure.add_vline(x=result['actual'][position], line_dash='dash', line_color='#7b5299',
                     annotation_text='Nota observada', annotation_position='top')
    figure.update_layout(meta='shap-waterfall', height=790, margin={'l': 220, 'r': 80, 't': 35, 'b': 40},
        yaxis={'autorange': 'reversed'}, xaxis_title='Nota y aportes acumulados · puntos', showlegend=False)
    return figure


COMPARISON = r"""
**LIME y SHAP responden preguntas distintas.** LIME ajusta una regresión lineal
ponderada en un vecindario del caso: sus pesos explican el sustituto. El LIME
existente discretiza numéricas por cuartiles, usa semilla 42 y permite remuestreo
empírico de filas completas de train o perturbaciones estándar. La fidelidad R²
y la brecha entre predicción real y sustituto indican cuánto confiar en él.
Los pesos dependen de la distancia, ancho del núcleo, discretización, regularización,
tamaño de muestra y semilla. Una buena fidelidad del vecindario no garantiza
que el sustituto coincida exactamente con el caso.

TreeSHAP reparte la diferencia entre una base del modelo y su predicción entre
las variables, mediante valores de Shapley para el juego definido por el
explicador:

$$
\phi_j = \sum_{S \subseteq F \setminus \{j\}}
\frac{|S|!\,(p-|S|-1)!}{p!}
\left[v\!\left(S \cup \{j\}\right)-v(S)\right]
$$

Aquí, $F$ es el conjunto de características, $p = |F|$, $S$ es un subconjunto
que no contiene a la característica $j$, y $v(S)$ es el valor asignado a esa
coalición según la referencia del explicador. El factor con factoriales pondera
cuánto aporta $j$ al incorporarse a cada posible subconjunto.

Aquí se usa **TreeSHAP exacto nativo de XGBoost**
(`pred_contribs=True`, `approx_contribs=False`), con referencia implícita de
cobertura de las rutas de los árboles aprendida en train (tree-path-dependent).
No se enumeran las 2^15 coaliciones ni se ajusta un sustituto. Se comprueba
base + suma de los 15 SHAP = predicción del pipeline en todas las filas,
con tolerancia absoluta 1e-5 por aritmética float32. La base no tiene por qué
coincidir con la media de predicciones sobre las filas mostradas ni con la nota real.

**Exacto no significa causal ni libre de supuestos.** Es exacto para esta
convención de referencia basada en árboles; no es una atribución interventional
ni estima automáticamente la distribución condicional real de atributos
correlacionados. Otros explicadores como KernelSHAP o el muestreo de coaliciones
aproximan los valores y pueden introducir variación Monte Carlo. No se usan aquí.

**Cuándo pueden divergir:** (1) árboles con saltos o interacciones: una recta
local puede perder curvatura mientras SHAP distribuye aportes del ensamble;
(2) atributos correlacionados o derivados —dominio inicial, final y avance—:
la referencia SHAP y el vecindario LIME pueden repartir de otra forma su señal;
(3) perturbaciones LIME que generan combinaciones imposibles o alejadas de los
datos; (4) cambios de semilla, núcleo o discretización en LIME; (5) cambios de
fondo o convención de dependencia en SHAP. Una discrepancia de signo no demuestra
que uno detecte la causa correcta: cambian las referencias y las cantidades explicadas.
Los pesos LIME son de condiciones discretizadas; los SHAP son aportes de variables
al modelo exacto. No deben compararse como coeficientes intercambiables.

**Interpretación del error.** Los SHAP de estos waterfalls descomponen la
predicción, no el error ni la pérdida. La nota observada se añade solo como
referencia. Comparar los aportes de ambos casos ayuda a describir el comportamiento
del modelo; no identifica por qué un estudiante obtuvo otra nota ni demuestra
que intervenir en una variable cambie su desempeño. Para reproducir LIME en el
mismo caso, elegir Test temporal y su número anónimo en el selector de abajo.

**Referencias:** [SHAP · Lundberg y Lee](https://arxiv.org/abs/1705.07874),
[TreeSHAP y referencia de rutas](https://shap.readthedocs.io/en/latest/generated/shap.TreeExplainer.html),
[XGBoost · predicciones y contribuciones](https://xgboost.readthedocs.io/en/stable/prediction.html),
[LIME · Ribeiro y colaboradores](https://arxiv.org/abs/1602.04938).
"""


def create_shap_section(app, ui, load_xgboost, report, saved_test_predictions):
    md, table, card, notice = (ui[k] for k in ['md', 'table', 'card', 'notice'])
    if report['selected_by_external_cv'] != 'XGBoost':
        return notice('SHAP pendiente para el modelo con menor RMSE medio CV actual; no se reutilizan explicaciones de otro modelo.')
    result = compute_shap(load_xgboost(), ui['TRAIN'], ui['TEST'], ui['TARGET'], saved_test_predictions)
    frame = pd.concat([ui['TRAIN'], ui['TEST']], ignore_index=True)
    frame['_shap_partition'] = ['train']*result['n_train'] + ['test']*result['n_test']
    layout = html.Div([
        ui['title']('INTERPRETABILIDAD GLOBAL Y LOCAL', 'SHAP · interpretar XGBoost',
                    'El modelo con menor RMSE medio CV externa; comparación de familias exploratoria, sin ganador estadístico confirmado.'),
        notice('Se explica el pipeline final guardado, sin reentrenarlo. Resumen por defecto: todas las filas válidas '
               f'({len(frame):,}: {result["n_train"]:,} train + {result["n_test"]:,} test). '
               'En train son predicciones del ajuste final, no OOF; no es una evaluación de generalización. '
               'Los datos de test no cambian el modelo ni la referencia de SHAP.'),
        html.Div([html.Label('DATOS DEL RESUMEN GLOBAL'), dcc.RadioItems([
            {'label': 'Conjunto válido completo · train + test', 'value': 'all'},
            {'label': 'Solo train · ajuste final', 'value': 'train'},
            {'label': 'Solo test temporal', 'value': 'test'}], value='all', id='classic-shap-scope',
            inline=True, className='radio')], className='variable-select'),
        html.Div(id='classic-shap-result'),
        html.Details([html.Summary('SHAP frente a LIME · método, exactitud, supuestos y posibles divergencias'),
                      dcc.Markdown(COMPARISON, mathjax=True, className='prose shap-methods',
                                   link_target='_blank')], className='details'),
    ], className='shap-section')

    @app.callback(Output('classic-shap-result', 'children'), Input('classic-program', 'value'),
                  Input('classic-course', 'value'), Input('classic-shap-scope', 'value'))
    def render(program, course, scope):
        if scope not in ('all', 'train', 'test'):
            return notice('Selecciona un conjunto disponible para el resumen SHAP.')
        subset = ui['subset'](frame, program, course)
        global_frame = subset if scope == 'all' else subset.loc[subset['_shap_partition'].eq(scope)]
        parts = []
        if global_frame.empty:
            parts.append(notice('No hay filas para el resumen SHAP con estos filtros.'))
        else:
            positions = global_frame.index.to_numpy()
            ranking = importance(result, positions, ui['LABELS'])
            top = ranking.iloc[0]
            chart = card('Interpretabilidad global · summary plot SHAP',
                f'**{len(positions):,} observaciones, las 15 variables y todos sus puntos, sin muestreo.** '
                'Las variables se ordenan de mayor a menor media |SHAP|. Cada punto representa el aporte '
                'de una variable para una fila: derecha eleva la predicción, izquierda la reduce respecto a la base. '
                'Azul = valor numérico bajo; rojo = alto, normalizados por variable en las filas mostradas. '
                'Gris = categórica sin orden alto/bajo; el valor aparece al pasar el cursor. '
                'La separación vertical es solo jitter visual con semilla 42, no otra variable. '
                'En pantallas estrechas puedes desplazar el gráfico horizontalmente.',
                summary_plot(result, positions, ui['LABELS']))
            chart.className += ' shap-chart'
            parts.extend([chart, md(f'**Mayor magnitud media en esta vista:** {top["Variable"]} '
                f'(**{top["Media |SHAP| (puntos)"]:.4f} puntos**, '
                f'**{top["Importancia relativa (%)"]:.1f}%** del total de medias absolutas). '
                'La importancia relativa mide reparto de atribuciones; no porcentaje de varianza explicada ni causalidad.'),
                html.Details([html.Summary('Importancia global · magnitud y proporción de las 15 variables'),
                              table(ranking)], className='details')])
        candidates = subset.loc[subset['_shap_partition'].eq('test')].index.to_numpy()
        parts.append(html.H3('Interpretabilidad local · dos casos del test temporal'))
        parts.append(md('Casos elegidos por menor y mayor error absoluto dentro del test y los filtros actuales '
                        '(empates por orden anónimo). Es una selección ilustrativa posterior a la evaluación; '
                        'no selecciona modelos. En regresión usamos **bajo error**, sin inventar un umbral de «clasificación correcta». '
                        'Los ejemplos no cambian al alternar el conjunto del resumen global.'))
        if not len(candidates):
            parts.append(notice('No hay casos de test con estos filtros para los waterfalls.'))
            return html.Div(parts)
        errors = np.abs(result['predictions'][candidates] - result['actual'][candidates])
        order = candidates[np.argsort(errors, kind='stable')]
        chosen = [('Menor error absoluto', order[0])]
        if len(order) > 1:
            chosen.append(('Mayor error absoluto', order[-1]))
        else:
            parts.append(notice('Solo hay un caso test disponible; se necesita al menos otro para contrastar dos observaciones.'))
        for label, position in chosen:
            case = int(position-result['n_train']+1)
            pred, actual = result['predictions'][position], result['actual'][position]
            rows = local_rows(result, position, ui['LABELS'])
            increases = rows.loc[rows['SHAP (puntos)'] > 0].head(2)
            decreases = rows.loc[rows['SHAP (puntos)'] < 0].head(2)
            def describe(selected):
                return ', '.join(f'{r["Variable"]} = {markdown_value(r["Valor usado por el modelo"])} '
                                 f'({r["SHAP (puntos)"]:+.3f})' for _, r in selected.iterrows()) or 'ningún aporte'
            text = (f'**Caso {case:04d} · {label.lower()}**. Nota observada **{actual:.3f}**, '
                    f'predicha **{pred:.3f}**, error absoluto **{abs(pred-actual):.3f}** puntos. '
                    f'Base **{result["base"][position]:.4f}** + suma SHAP '
                    f'**{result["values"][position].sum():+.4f}** = **{pred:.4f}**. '
                    'Verde suma, coral resta; la línea violeta marca la nota observada. '
                    'Se incluyen los 15 aportes, ordenados por magnitud, sin ocultar los restantes.')
            chart = card(f'Waterfall SHAP · {label} · Caso {case:04d}', text,
                         waterfall(result, position, ui['LABELS']))
            chart.className += ' shap-chart'
            parts.extend([chart, md('**Variables que elevan esta predicción:** ' + describe(increases)
                + '. **Variables que la reducen:** ' + describe(decreases) + '. '
                + ('El modelo queda cerca de la nota observada en este ejemplo.' if label.startswith('Menor') else
                   f'El modelo {"sobreestima" if pred > actual else "subestima"} la nota: sus aportes explican '
                   'cómo llega a la predicción, pero no explican por sí solos la discrepancia con la realidad.')),
                html.Details([html.Summary(f'Caso {case:04d} · valores y aportes completos'), table(rows)], className='details')])
        if len(chosen) == 2:
            low, high = chosen[0][1], chosen[1][1]
            difference = result['values'][high] - result['values'][low]
            changes = np.argsort(-abs(difference), kind='stable')[:3]
            description = ', '.join(f'{ui["LABELS"].get(result["features"][j], result["features"][j])} '
                                     f'({difference[j]:+.3f} puntos)' for j in changes)
            parts.append(card('Lectura conjunta de los dos casos',
                'Las mayores diferencias de aporte **caso de mayor error − caso de menor error** son: '
                + description + '. Son cambios en la atribución de las predicciones; no efectos causales '
                'ni una descomposición del error observado. La precisión del primer caso no valida por sí sola '
                'el modelo y el segundo ilustra una limitación de sus predicciones.'))
        return html.Div(parts)

    return layout

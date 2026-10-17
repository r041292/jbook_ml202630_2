"""LIME de regresión sobre el pipeline XGBoost guardado; referencia solo train."""
from functools import lru_cache
import textwrap

import numpy as np
import pandas as pd
import plotly.express as px
from dash import Input, Output, State, ctx, dcc, html
from threadpoolctl import threadpool_limits


class TabularBridge:
    """Representación numérica de LIME; decodifica al esquema original del pipeline."""
    def __init__(self, training, columns, labels):
        self.columns = list(columns)
        self.numeric = training[self.columns].select_dtypes(include='number').columns.tolist()
        self.medians = training[self.numeric].median()
        self.categories = {c: sorted(training[c].dropna().astype(str).unique().tolist())
                           for c in self.columns if c not in self.numeric}
        self.modes = {c: str(training[c].dropna().mode().iloc[0]) for c in self.categories}
        self.categorical_indices = [self.columns.index(c) for c in self.categories]
        self.categorical_names = {self.columns.index(c): values+['Categoría no vista en train']
                                  for c, values in self.categories.items()}
        self.names = [labels.get(c, c) for c in self.columns]
        self.background = self.encode(training)

    def encode(self, frame):
        columns = []
        for name in self.columns:
            if name in self.numeric:
                columns.append(frame[name].fillna(self.medians[name]).to_numpy(dtype=float))
            else:
                vocab = {value: i for i, value in enumerate(self.categories[name])}
                columns.append(frame[name].fillna(self.modes[name]).astype(str).map(vocab)
                               .fillna(len(vocab)).to_numpy(dtype=float))
        return np.column_stack(columns)

    def decode(self, values):
        values = np.atleast_2d(values)
        data = {}
        for i, name in enumerate(self.columns):
            if name in self.numeric:
                data[name] = values[:, i]
            else:
                categories = self.categories[name]
                # Una categoría desconocida llega al pipeline como desconocida, no como moda.
                data[name] = [categories[int(code)] if 0 <= int(code) < len(categories) else
                              '__LIME_CATEGORIA_NO_VISTA__' for code in values[:, i]]
        return pd.DataFrame(data, columns=self.columns)


def explain_xgboost(model, training, record, labels, samples=1000, neighborhood='empirical'):
    from lime.lime_tabular import LimeTabularExplainer
    if samples not in (1000, 3000, 5000):
        raise ValueError('Número de perturbaciones no permitido.')
    if neighborhood not in ('empirical', 'perturbed'):
        raise ValueError('Vecindario no permitido.')
    bridge = TabularBridge(training, model.feature_names_in_, labels)
    encoded = bridge.encode(record)[0]
    explainer = LimeTabularExplainer(bridge.background, mode='regression',
        feature_names=bridge.names, categorical_features=bridge.categorical_indices,
        categorical_names=bridge.categorical_names, discretize_continuous=True,
        discretizer='quartile', feature_selection='none', random_state=42)
    coherence = {}
    def predict(values):
        decoded = bridge.decode(values)
        initial, final = decoded.Dominio_Inicial, decoded.Dominio_Final
        valid = (decoded[bridge.numeric].ge(0).all(axis=1) & final.ge(initial) &
                 np.isclose(decoded.avance_precalculo_aleks, final-initial, atol=1e-6))
        for time in ['Tiempo_Total_Tiempo', 'Tiempo_total_Aprendidos_hora']:
            valid &= decoded[time].ne(0) | final.eq(initial)
        # Es un diagnóstico del vecindario artificial, no se filtra ni modifica el modelo.
        coherence['incoherent_fraction'] = float((~valid.iloc[1:]).mean())
        return np.asarray(model.predict(decoded), dtype=float)
    with threadpool_limits(limits=1):
        actual = float(model.predict(record[list(model.feature_names_in_)])[0])
        if neighborhood == 'perturbed':
            explanation = explainer.explain_instance(encoded, predict, num_features=len(bridge.columns), num_samples=samples)
            np.testing.assert_allclose(explanation.predicted_value, actual, atol=1e-10, rtol=0)
            weights = explanation.local_exp[1]
            mapped = explanation.domain_mapper.map_exp_ids(weights)
            intercept, surrogate, fidelity = float(explanation.intercept[1]), float(explanation.local_pred[0]), float(explanation.score)
            unique_rows = None
        else:
            # Variante empírica: núcleo y regresión LIME oficiales, sin mezclar atributos de alumnos distintos.
            indices = np.random.default_rng(42).choice(len(training), size=samples-1, replace=True)
            neighbors = np.vstack([encoded, bridge.background[indices]])
            discretized = explainer.discretizer.discretize(neighbors)
            binary = (discretized == discretized[0]).astype(float)
            distances = np.linalg.norm(binary-binary[0], axis=1)
            predictions = predict(neighbors)
            np.testing.assert_allclose(predictions[0], actual, atol=1e-10, rtol=0)
            intercept, weights, fidelity, local_pred = explainer.base.explain_instance_with_data(
                binary, predictions[:, None], distances, 0, num_features=len(bridge.columns), feature_selection='none')
            surrogate = float(local_pred[0])
            mapped = []
            for index, weight in weights:
                rule = (bridge.names[index]+' = '+bridge.categorical_names[index][int(encoded[index])]
                        if index in bridge.categorical_indices else explainer.discretizer.names[index][int(discretized[0,index])])
                mapped.append((rule, weight))
            unique_rows = len(np.unique(indices))
    rows = [{'Variable': labels.get(bridge.columns[index], bridge.columns[index]),
             'Valor del caso': record.iloc[0][bridge.columns[index]], 'Condición del caso': rule,
             'Aporte local (puntos)': float(weight), 'Sentido': 'Aumenta aproximación' if weight >= 0 else 'Disminuye aproximación'}
            for (index, weight), (rule, _) in zip(weights, mapped)]
    rows = pd.DataFrame(rows)
    rows = rows.iloc[rows['Aporte local (puntos)'].abs().sort_values(ascending=False, kind='stable').index].reset_index(drop=True)
    intercept = float(intercept)
    np.testing.assert_allclose(intercept+rows['Aporte local (puntos)'].sum(), surrogate, atol=1e-10)
    return {'rows': rows, 'prediction': actual, 'local_prediction': surrogate, 'intercept': intercept,
            'fidelity': float(fidelity) if np.isfinite(fidelity) else None,
            'absolute_gap': abs(actual-surrogate), 'samples': samples, 'seed': 42,
            'neighborhood': neighborhood, 'unique_reference_rows': unique_rows, **coherence}


def create_lime_section(app, ui, load_xgboost):
    card, md, table, notice, title, stats = (ui[k] for k in ['card', 'md', 'table', 'notice', 'title', 'stats'])
    training, test, target = (ui[k] for k in ['TRAIN', 'TEST', 'TARGET'])
    def select_frame(partition, program, course):
        return ui['subset'](test if partition == 'test' else training, program, course)
    layout = html.Div([
        title('INTERPRETACIÓN LOCAL', 'LIME · explicar una predicción de XGBoost',
              'El modelo permanece fijo: una regresión sencilla aproxima su comportamiento cerca del caso elegido.'),
        card('Cómo se construye la explicación',
             '**1. Caso real → 2. Vecindario → 3. Predicciones del XGBoost guardado → 4. Regresión local ponderada.** '
             '**Por defecto se usa una variante empírica de LIME:** se remuestrean filas completas de train '
             'y se aplica el núcleo de distancias y la regresión local de la librería LIME. Conserva las relaciones observadas '
             'entre los atributos; no es el generador gaussiano estándar ni garantiza abundancia de vecinos cercanos. '
             'También puedes comparar con **LIME estándar**, que perturba atributos de forma independiente. '
             'LIME discretiza numéricas por cuartiles y compara categorías con el valor del caso. '
             'Imputaciones, frecuencias, escalas y cuartiles de referencia usan solo train. '
             'Cada consulta atraviesa el pipeline XGBoost completo, con sus categorías nativas; estos códigos numéricos son solo el puente de LIME. '
             'El selector de modelo clásico no cambia esta sección: siempre explica **XGBoost**.\n\n'
             '[Artículo de LIME](https://arxiv.org/abs/1602.04938) · '
             '[LIME para regresión](https://marcotcr.github.io/lime/tutorials/Using%2Blime%2Bfor%2Bregression.html).'),
        notice('Es una explicación local del modelo, no una causa ni una importancia global. '
               'El vecindario empírico usa filas completas de train; el estándar genera consultas artificiales que pueden '
               'romper avance = dominio final − inicial o combinaciones institucionales. Ninguno añade registros a la base '
               'ni reentrena XGBoost. La comprobación de dominios/avance no certifica todas las restricciones posibles. '
               'Interpretar con cautela incluso si la fidelidad local es alta.'),
        html.Div([html.Label('Partición del caso'), dcc.RadioItems([
            {'label': 'Test temporal', 'value': 'test'}, {'label': 'Train · ajuste final, no OOF', 'value': 'train'}],
            'test', id='classic-lime-partition', inline=True, className='radio')], className='variable-select'),
        html.Div([html.Label('Caso anónimo · usa los filtros de programa/asignatura anteriores'),
                  dcc.Dropdown(id='classic-lime-case', clearable=False, placeholder='Selecciona un caso')], className='variable-select'),
        html.Div([html.Label('Construcción del vecindario'), dcc.Dropdown([
            {'label': 'Variante empírica · filas completas de train', 'value': 'empirical'},
            {'label': 'LIME estándar · perturbaciones independientes', 'value': 'perturbed'}],
            'empirical', id='classic-lime-neighborhood', clearable=False)], className='variable-select'),
        html.Div([html.Label('Tamaño del vecindario LIME'), dcc.Dropdown([
            {'label': f'{n:,} muestras', 'value': n} for n in [1000, 3000, 5000]],
            1000, id='classic-lime-samples', clearable=False)], className='variable-select'),
        html.Button('Generar explicación LIME', id='classic-lime-button', n_clicks=0, disabled=True, className='primary-button'),
        dcc.Loading(html.Div(id='classic-lime-result', children=notice('Selecciona un caso y genera su explicación.')), type='circle'),
    ])

    @app.callback(Output('classic-lime-case', 'options'), Output('classic-lime-case', 'value'), Output('classic-lime-button', 'disabled'),
                  Input('classic-program', 'value'), Input('classic-course', 'value'), Input('classic-lime-partition', 'value'))
    def cases(program, course, partition):
        frame = select_frame(partition, program, course)
        options = [{'label': f'Caso {int(i)+1:04d} · {row[ui["COURSE"]]}', 'value': int(i)} for i, row in frame.iterrows()]
        return options, options[0]['value'] if options else None, not bool(options)

    @lru_cache(maxsize=32)
    def cached(partition, index, samples, neighborhood):
        frame = test if partition == 'test' else training
        return explain_xgboost(load_xgboost(), training, frame.loc[[index]], ui['LABELS'], samples, neighborhood)

    @app.callback(Output('classic-lime-result', 'children'), Input('classic-lime-button', 'n_clicks'),
                  Input('classic-lime-case', 'value'), Input('classic-program', 'value'), Input('classic-course', 'value'),
                  Input('classic-lime-partition', 'value'), Input('classic-lime-samples', 'value'),
                  Input('classic-lime-neighborhood', 'value'), prevent_initial_call=True)
    def explain(clicks, index, program, course, partition, samples, neighborhood):
        frame = select_frame(partition, program, course)
        if frame.empty:
            return notice('No hay casos en esta partición con los filtros elegidos.')
        if not clicks or ctx.triggered_id != 'classic-lime-button':
            return notice('Genera la explicación del caso actual. Cambiar caso, partición o filtros limpia el resultado anterior.')
        if partition not in ['test', 'train'] or index not in frame.index:
            return notice('Selecciona un caso disponible en la partición y los filtros actuales.')
        if samples not in (1000, 3000, 5000) or neighborhood not in ('empirical', 'perturbed'):
            return notice('Elige uno de los tamaños de vecindario disponibles.')
        result = cached(partition, int(index), int(samples), neighborhood)
        rows = result['rows']
        plotted = rows.head(10).copy()
        plotted['Regla'] = plotted['Condición del caso'].map(lambda text: textwrap.shorten(text, width=57, placeholder='…'))
        figure = px.bar(plotted, x='Aporte local (puntos)', y='Regla', orientation='h', color='Sentido',
                        color_discrete_map={'Aumenta aproximación': '#187b80', 'Disminuye aproximación': '#db7355'},
                        category_orders={'Regla': plotted.Regla.tolist()}, hover_data=['Condición del caso'])
        figure.add_vline(x=0, line_color='#435568', line_width=1)
        figure.update_layout(height=530)
        fidelity = result['fidelity']
        contribution_card = card('Qué condiciones elevan o reducen la aproximación local',
                 'Diez aportes de mayor magnitud. Verde suma y coral resta respecto al intercepto local; '
                 'son pesos de las condiciones activas del caso, no coeficientes globales de XGBoost. '
                 'En pantallas estrechas puedes desplazar el gráfico horizontalmente.', figure)
        contribution_card.className += ' lime-contributions'
        return html.Div([
            stats([('XGBoost · predicción', f'{result["prediction"]:.3f}', f'Caso {int(index)+1:04d} · {partition}'),
                   ('Aproximación LIME', f'{result["local_prediction"]:.3f}', f'Error local {result["absolute_gap"]:.3f}'),
                   ('Fidelidad local R²', '—' if fidelity is None else f'{fidelity:.3f}', 'Sobre vecindario; no es R² de test'),
                   ('Nota observada', f'{frame.loc[index,target]:.3f}', 'Solo descriptiva; no se usa para ajustar LIME')]),
            notice(f'Vecindario {"empírico" if neighborhood == "empirical" else "estándar"}: '
                   f'{100*result["incoherent_fraction"]:.1f}% de las muestras incumple dominios/avance. '
                   'La aproximación no justifica cambios educativos causales o factibles.'),
            notice('Fidelidad local baja o indefinida: no uses los aportes como una explicación fiable de este caso.')
                if fidelity is None or fidelity < .5 else md('La fidelidad describe el ajuste del sustituto en este vecindario; no valida causalidad ni estabilidad frente a otras semillas.'),
            md('**Revisa también el error local:** un R² de fidelidad alto en el vecindario no garantiza '
               'que la aproximación coincida con la predicción de este caso. Los aportes descomponen LIME, no exactamente XGBoost.'),
            contribution_card,
            html.Article([html.H3('Descomposición completa de la aproximación'),
                md(f'Intercepto local **{result["intercept"]:.4f}** + suma de los {len(rows)} aportes '
                   f'**{rows["Aporte local (puntos)"].sum():+.4f}** = **{result["local_prediction"]:.4f}**. '
                   'El intercepto no es la media global ni una nota base causal. Las condiciones restantes también se incluyen en esta tabla.'),
                table(rows), md(f'Semilla {result["seed"]}; {result["samples"]:,} muestras; referencia train completa; '
                               'numéricas discretizadas por cuartiles. En train se explica el ajuste final, no las predicciones OOF.')], className='card'),
            md(f'En el remuestreo se usaron **{result["unique_reference_rows"]} filas distintas de train**, más el caso. '
               'Repetir filas no crea observaciones independientes. El R² de fidelidad se mide en el mismo vecindario ajustado, sin validación externa.')
               if neighborhood == 'empirical' else md('El muestreo estándar puede consultar combinaciones fuera de la distribución observada. Semilla fija hace reproducible este resultado, no demuestra estabilidad ante otras semillas.'),
        ])
    return layout

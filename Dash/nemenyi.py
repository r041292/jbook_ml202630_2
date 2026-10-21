"""Post hoc de Nemenyi para Friedman: diferencia crítica sobre los rangos promedio ya calculados.

No reajusta modelos ni usa test: parte de los rangos por fold de ``friedman_comparison``.
"""
from itertools import combinations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html
from scipy.stats import studentized_range

ALPHA = .05

EXPLANATION = (
    '**Prueba de Nemenyi (Demšar, 2006).** Es el post hoc clásico de Friedman: usa los mismos rangos promedio y declara que dos modelos '
    'difieren si sus rangos se separan más que la **diferencia crítica** CD = q_α · √(k(k+1) / (6N)), con k modelos, N folds y q_α el cuantil '
    '1 − α del rango estudentizado dividido por √2. No requiere nuevos cálculos sobre los modelos. **Es un complemento del informe: el MCS '
    'sigue siendo el post hoc de referencia del tablero.** Con cinco folds la CD es muy grande (cubre una parte importante de las posiciones '
    'posibles), así que la prueba tiene poca potencia: que un par no la supere **no demuestra equivalencia**. Los folds comparten entrenamientos, '
    'de modo que el resultado es exploratorio y no corrige esa dependencia.')


def critical_difference(k, n, alpha=ALPHA):
    q = float(studentized_range.ppf(1 - alpha, k, np.inf) / np.sqrt(2))
    return q, q * float(np.sqrt(k * (k + 1) / (6 * n)))


def pairs(ranking, cd):
    mean = ranking.set_index('Modelo')['Rango promedio']
    rows = [{'Modelo A': a, 'Modelo B': b, 'Δ rango (A − B)': mean[a] - mean[b], '|Δ| > CD': bool(abs(mean[a] - mean[b]) > cd)}
            for a, b in combinations(mean.index, 2)]
    return pd.DataFrame(rows)


def figure(ranking, cd):
    order = ranking.sort_values('Rango promedio', kind='stable')
    k = len(order)
    start = float(order['Rango promedio'].iloc[0])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=order['Rango promedio'], y=list(range(k, 0, -1)), mode='markers+text', text=order['Modelo'],
                             textposition='middle right', marker={'size': 9, 'color': '#187b80'}, showlegend=False,
                             hovertemplate='%{text}<br>Rango promedio: %{x:.2f}<extra></extra>'))
    fig.add_shape(type='line', x0=start, x1=start + cd, y0=k + 1, y1=k + 1, line={'color': '#2b2b2b', 'width': 4})
    fig.add_annotation(x=start + cd / 2, y=k + 1, text=f'CD = {cd:.2f}', showarrow=False, yshift=14)
    fig.update_xaxes(title='Rango promedio de RMSE (menor = mejor)', range=[.5, k + 1.5 + .35 * k])
    fig.update_yaxes(visible=False, range=[0, k + 2])
    fig.update_layout(height=max(320, 28 * k + 120), margin={'l': 10, 'r': 10, 't': 20, 'b': 40})
    return fig


def section(ranking, n_folds, ui):
    """Bloque colapsable que se coloca justo después de Friedman."""
    md, table = ui['md'], ui['table']
    ranking = pd.DataFrame(ranking)
    k = len(ranking)
    q, cd = critical_difference(k, n_folds)
    comparison = pairs(ranking, cd)
    exceeds = comparison.loc[comparison['|Δ| > CD']].copy()
    exceeds['|Δ| > CD'] = 'Sí'
    all_pairs = comparison.copy()
    all_pairs['|Δ| > CD'] = np.where(all_pairs['|Δ| > CD'], 'Sí', 'No')
    summary = (f'**k = {k} modelos, N = {n_folds} folds, α = {ALPHA}:** q = **{q:.3f}**, CD = q·√(k(k+1)/(6N)) = **{cd:.2f}** posiciones de rango. '
               f'Superan la CD **{len(exceeds)} de {len(comparison)}** pares.')
    return html.Details([
        html.Summary('Post hoc de Nemenyi · diferencia crítica sobre los rangos de Friedman'),
        md(EXPLANATION), md(summary),
        dcc.Graph(figure=figure(ranking, cd), config={'displayModeBar': False}),
        (table(exceeds) if len(exceeds) else md('Ningún par supera la diferencia crítica: con estos folds Nemenyi no distingue modelos.')),
        html.Details([html.Summary(f'Los {len(comparison)} pares · diferencia de rangos'), table(all_pairs)], className='details'),
        md('**Referencia:** [Demšar (2006), *Statistical comparisons of classifiers over multiple data sets*](https://www.jmlr.org/papers/v7/demsar06a.html).'),
    ], className='details')

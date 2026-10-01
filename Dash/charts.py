"""Gráficos complementarios. Cálculos sobre observaciones completas, sin recortes."""
import numpy as np
import plotly.graph_objects as go
from scipy.stats import gaussian_kde


def density_curve(series, points=140):
    values = series.dropna().astype(float).to_numpy()
    if len(values) < 2 or np.ptp(values) == 0:
        return values, None, None
    grid = np.linspace(values.min(), values.max(), points)
    return values, grid, gaussian_kde(values)(grid)


def numeric_density(series, label, color):
    values, grid, density = density_curve(series)
    figure = go.Figure(go.Histogram(x=values, histnorm='probability density', nbinsx=35,
        name='Densidad del histograma', marker_color=color, opacity=.35))
    if grid is not None:
        figure.add_trace(go.Scatter(x=grid, y=density, mode='lines', name='Curva KDE', line={'color': color, 'width': 2.5},
            hovertemplate='%{x:.3f}<br>Densidad: %{y:.4f}<extra>Estimación KDE</extra>'))
    else:
        figure.add_annotation(text='Sin variación suficiente para estimar una curva', x=.5, y=.9, xref='paper', yref='paper', showarrow=False)
    figure.update_layout(xaxis_title=label, yaxis_title='Densidad', showlegend=False, height=275)
    return figure


def comparison_figures(frame, variable, label, colors):
    density, cumulative = go.Figure(), go.Figure()
    rows = []
    for name, group in frame.groupby('Conjunto', sort=False):
        values, grid, curve = density_curve(group[variable], points=200)
        if grid is not None:
            density.add_trace(go.Scatter(x=grid, y=curve, name=name, mode='lines',
                line={'color': colors[name], 'width': 2.5}, hovertemplate='%{x:.3f}<br>Densidad: %{y:.4f}<extra>%{fullData.name}</extra>'))
        elif len(values):
            density.add_vline(x=float(values[0]), line_color=colors[name], annotation_text=name + ' · constante')
        ordered = np.sort(values)
        if len(ordered):
            # Proporciones exactas evaluadas en hasta 800 umbrales observados.
            x = np.unique(ordered[np.linspace(0, len(ordered)-1, min(800, len(ordered)), dtype=int)])
            y = np.searchsorted(ordered, x, side='right') / len(ordered)
            cumulative.add_trace(go.Scatter(x=x, y=y, name=name, mode='lines',
                line={'color': colors[name], 'shape': 'hv', 'width': 2},
                hovertemplate='Umbral: %{x:.3f}<br>Proporción ≤ umbral: %{y:.1%}<extra>%{fullData.name}</extra>'))
        rows.append({'Conjunto': name, 'Filas': len(group), 'Valores disponibles': len(values),
                     'Media': float(np.mean(values)) if len(values) else None,
                     'Mediana': float(np.median(values)) if len(values) else None,
                     'Desviación estándar': float(np.std(values, ddof=1)) if len(values) > 1 else None})
    density.update_layout(xaxis_title=label, yaxis_title='Densidad estimada')
    cumulative.update_layout(xaxis_title=label, yaxis_title='Proporción acumulada')
    cumulative.update_yaxes(range=[0, 1], tickformat='.0%')
    return density, cumulative, rows

"""Contrastes exploratorios de train; nunca consulta test ni ajusta modelos.

La unidad disponible es el registro: p e IC suponen filas independientes.
Con estudiantes repetidos su calibración es aproximada (ver aviso en EDA).
"""
from functools import lru_cache
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats

REPLICATES = 1999
ALPHA = .05


def p_text(p):
    return '< 0.0001' if p < .0001 else f'= {p:.4f}'


def decision(p, yes, no):
    return yes if p < ALPHA else no


def normality(series):
    values = np.asarray(series.dropna(), dtype=float)
    values = values[np.isfinite(values)]
    if len(values) < 3 or np.ptp(values) == 0:
        return '**Normalidad:** no estimable con menos de 3 valores o una variable constante.'
    # La caché vigente tiene 1309 filas. No extrapolar el p de Shapiro a n > 5000.
    if len(values) > 5000:
        result = stats.normaltest(values)
        name, statistic = 'D’Agostino–Pearson', 'K²'
    else:
        result = stats.shapiro(values)
        name, statistic = 'Shapiro–Wilk', 'W'
    return (f'**Normalidad · {name}: {statistic} = {result.statistic:.4f}; '
            f'p {p_text(result.pvalue)}; n = {len(values)}.**\n\n'
            '**¿Qué revisa?** Si los valores siguen aproximadamente la forma de una campana simétrica. '
            'El estadístico resume cuánto se parecen a esa forma; el valor p ayuda a evaluar la diferencia.\n\n'
            '**Lectura del resultado:** ' +
            decision(result.pvalue, 'los datos muestran una diferencia clara respecto a una distribución normal. '
                     'Esto no obliga a borrar valores extremos ni a cambiar la escala de la variable.',
                     'la prueba no encuentra una diferencia clara respecto a una distribución normal. '
                     'Esto no garantiza que los datos sean normales.'))


def group_test(frame, group, target):
    medians = frame.groupby(group, observed=True)[target].median().dropna()
    summary = (f'**Conclusión descriptiva:** la mayor mediana es {medians.max():.2f} '
               f'({medians.idxmax()}) y la menor es {medians.min():.2f} ({medians.idxmin()}). '
               if len(medians) > 1 and medians.max() != medians.min() else
               'Las medianas observadas coinciden. ' if len(medians) > 1 else '')
    groups = [part[target].dropna().to_numpy() for _, part in frame.groupby(group, observed=True)]
    if len(groups) < 2 or any(len(g) < 5 for g in groups):
        return summary + '**Kruskal–Wallis:** no se contrasta: se requieren al menos dos grupos y 5 notas por grupo; las cajas siguen siendo descriptivas.'
    if np.ptp(np.concatenate(groups)) == 0:
        return '**Kruskal–Wallis:** no estimable: todas las notas son iguales.'
    result = stats.kruskal(*groups)
    return (summary + f'**Kruskal–Wallis: H = {result.statistic:.4f}; gl = {len(groups)-1}; '
            f'p {p_text(result.pvalue)}; n = {sum(map(len, groups))}.**\n\n'
            '**¿Qué compara?** Si las notas tienden a ocupar posiciones más altas o más bajas en unos grupos que en otros. '
            'Ordena las notas y compara esas posiciones, sin exigir una distribución normal.\n\n'
            '**Lectura del resultado:** ' +
            decision(result.pvalue, 'se detectan diferencias entre al menos dos grupos. '
                     'Esta prueba conjunta no indica cuáles pares difieren; las medianas anteriores son una descripción.',
                     'no se detectan diferencias claras entre grupos. Esto no demuestra que sean iguales.') +
            ' Las diferencias pueden deberse al centro o a la forma de las distribuciones, no solo a sus medianas.')


def frequency_test(series):
    counts = series.fillna('Sin dato').value_counts()
    top = str(counts.index[0]) if len(counts) else '—'
    summary = f'**Conclusión:** predomina **{top}** ({100*counts.iloc[0]/counts.sum():.1f} %).' if len(counts) else 'Sin datos.'
    if len(counts) < 2 or counts.sum()/len(counts) < 5:
        return summary + ' Prueba chi-cuadrado no aplicable: se requieren dos categorías y frecuencia esperada ≥ 5.'
    result = stats.chisquare(counts.to_numpy())
    return (summary + '\n\n**Prueba chi-cuadrado de bondad de ajuste:** '
            f'**χ² = {result.statistic:.4f}; gl = {len(counts)-1}; p {p_text(result.pvalue)}.** '
            'Se comparan los conteos entre las diferentes categorías. ' +
            decision(result.pvalue, '**Lectura:** se detectan diferencias en los conteos.',
                     '**Lectura:** no se detectan diferencias claras en los conteos.'))


def missing_test(frame):
    flags = frame.isna().astype(int).to_numpy()
    n, k = flags.shape
    rows, columns = flags.sum(axis=1), flags.sum(axis=0)
    denominator = k*rows.sum() - np.sum(rows**2)
    maximum = frame.isna().mean().idxmax()
    summary = f'**Conclusión:** {maximum} registra el mayor porcentaje de ausencias ({100*frame[maximum].isna().mean():.1f} %). '
    if k < 2 or denominator == 0:
        return summary + 'Q de Cochran no estimable: los indicadores de ausencia no difieren dentro de las filas.'
    q = (k-1)*(k*np.sum(columns**2)-columns.sum()**2)/denominator
    p = stats.chi2.sf(q, k-1)
    return (summary + f'**Q de Cochran = {q:.4f}; gl = {k-1}; p {p_text(p)}; n = {n}.** '
            '\n\n**¿Qué compara?** Si los datos faltan con la misma frecuencia en todas las variables. '
            'Se revisan juntas las ausencias de cada registro. ' +
            decision(p, '**Lectura:** algunas variables presentan ausencias con mayor frecuencia que otras.',
                     '**Lectura:** no se detecta una diferencia clara en la frecuencia de ausencias.') +
            ' El resultado es aproximado y menos preciso cuando hay muy pocas ausencias. '
            'No permite saber por qué falta un dato ni si esa ausencia depende de su valor.')


def _row_corr(x, y):
    x, y = x-x.mean(axis=-1, keepdims=True), y-y.mean(axis=-1, keepdims=True)
    denominator = np.sqrt(np.sum(x*x, axis=-1)*np.sum(y*y, axis=-1))
    return np.divide(np.sum(x*y, axis=-1), denominator,
                     out=np.full_like(denominator, np.nan, dtype=float), where=denominator > 0)


@lru_cache(maxsize=96)
def correlation_comparison(x_values, y_values):
    """Bootstrap pareado de Δ=ρ−r. Recalcula rangos en cada réplica."""
    x, y = np.asarray(x_values), np.asarray(y_values)
    if len(x) < 8 or np.ptp(x) == 0 or np.ptp(y) == 0:
        return None
    r, rho = float(stats.pearsonr(x, y).statistic), float(stats.spearmanr(x, y).statistic)
    delta = rho-r
    rng, draws = np.random.default_rng(42), []
    for start in range(0, REPLICATES, 64):
        indices = rng.integers(0, len(x), size=(min(64, REPLICATES-start), len(x)))
        a, b = x[indices], y[indices]
        draws.extend(_row_corr(stats.rankdata(a, axis=1), stats.rankdata(b, axis=1))-_row_corr(a, b))
    draws = np.asarray(draws)
    draws = draws[np.isfinite(draws)]
    if len(draws) < .95*REPLICATES:
        return None
    lower, upper = np.quantile(draws, [.025, .975])
    # Contraste bilateral aproximado: distribución bootstrap centrada bajo H0.
    p = (1+np.count_nonzero(np.abs(draws-delta) >= abs(delta)))/(len(draws)+1)
    return {'n': len(x), 'r': r, 'rho': rho, 'delta': delta, 'low': lower, 'high': upper,
            'p': p, 'replicates': len(draws)}


def comparison_text(frame, variable, target):
    paired = frame[[variable, target]].replace([np.inf, -np.inf], np.nan).dropna()
    result = correlation_comparison(tuple(paired[variable]), tuple(paired[target]))
    if result is None:
        return '**Pearson frente a Spearman:** no hay suficientes datos con variación para realizar una comparación estable (se requieren al menos 8 registros completos).'
    return (f'**Pearson r = {result["r"]:.4f}; Spearman ρ = {result["rho"]:.4f}; n = {result["n"]}.** '
            '\n\n**¿Qué significa la comparación pareada?** Se calculan ambos coeficientes sobre exactamente '
            'los mismos registros de la variable elegida y de la nota. Luego se resta **ρ − r**, es decir, '
            'Spearman menos Pearson. Un resultado positivo indica que el valor numérico de Spearman es mayor; '
            'uno negativo indica que el de Pearson es mayor.\n\n'
            f'**Estadístico Δ = {result["delta"]:.4f}; intervalo de confianza del 95 % '
            f'({result["low"]:.4f}; {result["high"]:.4f}); p de la diferencia {p_text(result["p"])}.** '
            '**Lectura:** ' +
            decision(result['p'], 'se detecta una diferencia entre los coeficientes con este procedimiento aproximado.',
                     'no se detecta una diferencia clara entre los coeficientes; esto no demuestra que sean equivalentes.') +
            ' El intervalo describe la incertidumbre de la resta. El p pregunta si esa diferencia es compatible con cero, '
            'no si cada correlación es distinta de cero.\n\n'
            f'Para estimar esa incertidumbre se repite el cálculo en {result["replicates"]} muestras tomadas '
            'con reemplazo de los mismos registros (bootstrap pareado, semilla 42; p bilateral aproximado '
            'con la distribución centrada en cero). **Esta comparación no elige un ganador:** un coeficiente '
            'numéricamente mayor no demuestra que su método sea más adecuado.')


def association_tests(frame, columns, labels):
    """Una familia Holm para todos los pares de la matriz, no solo el máximo."""
    rows = []
    for a, b in combinations(columns, 2):
        paired = frame[[a, b]].dropna()
        if len(paired) < 5 or paired[a].nunique() < 2 or paired[b].nunique() < 2:
            continue
        x, y = paired[a].to_numpy(), paired[b].to_numpy()
        result = stats.spearmanr(x, y)
        p = result.pvalue
        if len(paired) <= 500:
            rng = np.random.default_rng(42)
            rx, ry = stats.rankdata(x), stats.rankdata(y)
            extreme = 0
            for start in range(0, REPLICATES, 64):
                permutations = np.array([rng.permutation(ry) for _ in range(min(64, REPLICATES-start))])
                extreme += np.count_nonzero(np.abs(_row_corr(np.broadcast_to(rx, permutations.shape), permutations)) >= abs(result.statistic)-1e-12)
            p = (extreme+1)/(REPLICATES+1)
        rows.append({'Variable A': labels[a], 'Variable B': labels[b], 'n': len(paired),
                     'ρ': float(result.statistic), 'p': float(p),
                     'Método p': 'Permutación (1999)' if len(paired) <= 500 else 'Asintótico'})
    if not rows:
        return pd.DataFrame(columns=['Variable A', 'Variable B', 'n', 'ρ', 'p', 'p Holm'])
    order = np.argsort([row['p'] for row in rows])
    adjusted = np.maximum.accumulate([(len(rows)-i)*rows[j]['p'] for i, j in enumerate(order)])
    for j, p in zip(order, adjusted):
        rows[j]['p Holm'] = min(1., float(p))
    return pd.DataFrame(rows).sort_values('p Holm', kind='stable')

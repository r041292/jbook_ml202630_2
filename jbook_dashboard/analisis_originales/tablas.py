"""Tablas Markdown del capítulo «Modelos originales», generadas desde ``salidas/``.

Cada función devuelve un bloque Markdown con decimales en coma. El ensamblador
(``ensamblar.py``) las inserta en la plantilla; así las cifras del capítulo
provienen de los mismos CSV que las figuras.
"""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
S = HERE / 'salidas'
DATA = HERE.parent.parent / 'Dash/data/originales'

ORDER = ['m0', 'm5', 'm19', 'm11', 'm7', 'm3', 'm14', 'm15', 'm16']
SHORT = {'svm': 'SVM lineal', 'm0': 'SVR RBF', 'm5': 'Kernel Ridge RBF', 'm19': 'TR-KRR RBF', 'm11': 'DenseWeight-XGB',
         'm7': 'TCR-XGBoost', 'm3': 'LinXGBoost', 'm14': 'logicDT adaptado', 'm15': 'GPR–XGBoost', 'm16': 'RIM'}
LONG_TO_SHORT = {'SVM lineal': 'SVM lineal', 'KNN': 'KNN', 'Ridge': 'Ridge', 'Lasso': 'Lasso', 'Random Forest': 'Random Forest',
                 'XGBoost': 'XGBoost', 'SVR RBF': 'SVR RBF', 'Kernel Ridge RBF': 'Kernel Ridge RBF',
                 'Truncated Newton KRR RBF': 'TR-KRR RBF', 'DenseWeight-XGBoost': 'DenseWeight-XGB', 'TCR-XGBoost': 'TCR-XGBoost',
                 'LinXGBoost (hojas completas E3)': 'LinXGBoost', 'logicDT propio (adaptado)': 'logicDT adaptado',
                 'GPR–XGBoost (OOF agrupado)': 'GPR–XGBoost', 'RIM (port E3)': 'RIM'}
METHOD = {'Grid Search': 'Grid', 'Random Search': 'Random', 'Bayesiana TPE': 'TPE', 'Genética DEAP': 'DEAP', 'Successive Halving': 'Halving'}
METHODS = list(METHOD)


def es(value, d=4):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return '—'
    text = f'{value:,.{d}f}'
    return text.replace(',', '@').replace('.', ',').replace('@', '.').replace('-', '−')


def pv(value):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return '—'
    if value == 0:
        return '< 10⁻³⁰⁰'
    if value < 1e-3:
        mantissa, exponent = f'{value:.2e}'.split('e')
        exponent = int(exponent)
        sup = str(abs(exponent)).translate(str.maketrans('0123456789', '⁰¹²³⁴⁵⁶⁷⁸⁹'))
        return f'{mantissa.replace(".", ",")}×10⁻{sup}'
    return es(value, 4)


def table(frame, align=None):
    cols = list(frame.columns)
    align = align or ['---'] + ['---:'] * (len(cols) - 1)
    lines = ['| ' + ' | '.join(cols) + ' |', '| ' + ' | '.join(align) + ' |']
    for row in frame.itertuples(index=False, name=None):
        lines.append('| ' + ' | '.join(str(v).replace('|', r'\|') for v in row) + ' |')
    return '\n'.join(lines)


def bold_best(values, fmt, best='min'):
    arr = np.array([np.nan if v is None else v for v in values], float)
    target = np.nanmin(arr) if best == 'min' else np.nanmax(arr)
    return [('**' + fmt(v) + '**') if (not np.isnan(v) and v == target) else fmt(v) for v in arr]


hpo = pd.read_csv(S / 'hpo_resumen.csv')
choices = pd.read_csv(S / 'hpo_metodo_por_busqueda.csv')
scores = pd.read_csv(S / 'eval_metricas.csv')
diag = pd.read_csv(S / 'eval_diagnosticos.csv')
folds = pd.read_csv(DATA / 'folds.csv')
timing = pd.read_csv(S / 'tiempos_refit_inferencia.csv')
CATALOG = json.loads((DATA / 'catalog.json').read_text(encoding='utf-8'))
ANALYSIS = json.loads((DATA / 'analysis.json').read_text(encoding='utf-8'))
NAMES = [SHORT[k] for k in ORDER]


def t_rmse_interno():
    pivot = hpo.pivot(index='Modelo', columns='Método', values='RMSE interno')
    chosen = hpo[hpo.Elegido].set_index('Modelo')['Método']
    rows = []
    for name in NAMES:
        row = {'Modelo': name}
        for m in METHODS:
            v = pivot.loc[name].get(m, np.nan)
            text = es(v, 6)
            row[METHOD[m]] = ('**' + text + '**') if chosen[name] == m else text
        rows.append(row)
    return table(pd.DataFrame(rows))


def t_brechas():
    pivot = hpo.pivot(index='Modelo', columns='Método', values='Brecha vs mejor (×10⁻³)')
    rows = [{'Modelo': n, **{METHOD[m]: es(pivot.loc[n].get(m, np.nan), 3) for m in METHODS}} for n in NAMES]
    return table(pd.DataFrame(rows))


def pretty_params(key, raw):
    params = json.loads(raw)
    out = []
    for k, v in params.items():
        if k == 'base_params':
            out.append('XGBoost base: ' + pretty_params(key, json.dumps(v)))
            continue
        name = k.replace('modelo__regressor__', '').replace('modelo__', '')
        out.append(f'`{name}` = {es(v, 4) if isinstance(v, float) else v}')
    return '; '.join(out)


def t_finales():
    rows = []
    for key in ORDER:
        r = hpo[(hpo.Clave == key) & hpo.Elegido].iloc[0]
        rows.append({'Modelo': SHORT[key], 'Método final': METHOD[r['Método']], 'Hiperparámetros finales': pretty_params(key, r['Parámetros'])})
    return table(pd.DataFrame(rows), ['---', '---', '---'])


def t_ganadores():
    pivot = choices.pivot(index='Modelo', columns='Búsqueda', values='Método elegido').map(lambda m: METHOD[m])
    pivot = pivot.loc[NAMES, [f'external_{i}' for i in range(1, 6)] + ['final']]
    pivot.columns = [f'Fold {i}' for i in range(1, 6)] + ['Final']
    return table(pivot.reset_index(), ['---'] * 7)


def wins():
    return choices['Método elegido'].map(METHOD).value_counts().to_dict()


def t_evaluaciones():
    rows = []
    for name in NAMES:
        row = {'Modelo': name}
        for m in METHODS:
            b = hpo[(hpo.Modelo == name) & (hpo['Método'] == m)]
            row[METHOD[m]] = '—' if b.empty else f'{int(b["Evaluaciones"].iloc[0])} / {int(b["Ajustes internos"].iloc[0])}'
        rows.append(row)
    return table(pd.DataFrame(rows))


def t_tiempo(column):
    rows = []
    for name in NAMES:
        row = {'Modelo': name}
        for m in METHODS:
            b = hpo[(hpo.Modelo == name) & (hpo['Método'] == m)]
            row[METHOD[m]] = '—' if b.empty else es(b[column].iloc[0], 2)
        rows.append(row)
    return table(pd.DataFrame(rows))


def t_por_evaluacion():
    rows = []
    for name in NAMES:
        row = {'Modelo': name}
        for m in METHODS:
            b = hpo[(hpo.Modelo == name) & (hpo['Método'] == m)]
            row[f's/eval. {METHOD[m]}'] = '—' if b.empty else es(b['s por evaluación'].iloc[0], 3)
        t = hpo[(hpo.Modelo == name) & (hpo['Método'] == 'Bayesiana TPE')]
        row['Ajuste interno medio (TPE, s)'] = es(t['fit interno medio (s)'].iloc[0], 4)
        rows.append(row)
    return table(pd.DataFrame(rows))


def strategy_totals(exclude=('LinXGBoost',)):
    sub = hpo[~hpo.Modelo.isin(exclude)]
    g = sub.groupby('Método').agg(fits=('Ajustes internos', 'sum'), evals=('Evaluaciones', 'sum'), cost=('Costo equivalente', 'sum'),
                                  final=('Búsqueda final (s)', 'sum'), outer=('5 búsquedas externas (s)', 'sum'))
    g['total'] = g.final + g.outer
    return g


def t_totales():
    g = strategy_totals()
    w = choices[choices.Modelo != 'LinXGBoost']['Método elegido'].value_counts()
    rows = []
    for m in METHODS:
        r = g.loc[m]
        rows.append({'Estrategia': METHOD[m] if m != 'Successive Halving' else 'Halving', 'Ajustes internos (final)': f'{int(r.fits):,}'.replace(',', '.'),
                     'Evaluaciones (final)': int(r.evals), 'Costo equivalente completo': es(r.cost, 1),
                     'Tiempo final (s)': es(r.final, 1), 'Tiempo 5 externas (s)': es(r.outer, 1), 'Total (s)': es(r.total, 1),
                     'Veces elegida (de 48)': int(w.get(m, 0))})
    return table(pd.DataFrame(rows))


def t_refit():
    rows = [{'Modelo': r['Modelo'], 'Refit final (s)': es(r['Refit final (s)'], 3), 'Refits externos, suma de 5 (s)': es(r['Refits externos, suma de 5 (s)'], 3),
             'Inferencia OOF, 5 lotes (s)': es(r['Inferencia OOF, suma de 5 lotes (s)'], 3), 'Inferencia test, 188 filas (s)': es(r['Inferencia test 188 filas (s)'], 4)}
            for _, r in timing.iterrows()]
    return table(pd.DataFrame(rows))


def part(name, conj):
    return scores[(scores.Modelo == name) & (scores.Conjunto == conj)].iloc[0]


def t_rmse_mae():
    names = list(scores[scores.Conjunto == 'Validación (OOF)'].sort_values('RMSE media folds').Modelo)
    rows = []
    for n in names:
        tr, va, te = part(n, 'Entrenamiento'), part(n, 'Validación (OOF)'), part(n, 'Prueba (test 202530)')
        rows.append({'Modelo': n, 'RMSE train': es(tr.RMSE), 'RMSE CV (media ± SD)': f'{es(va["RMSE media folds"])} ± {es(va["RMSE SD folds"])}',
                     'RMSE OOF reunido': es(va.RMSE), 'RMSE test': es(te.RMSE), 'MAE train': es(tr.MAE),
                     'MAE CV (media ± SD)': f'{es(va["MAE media folds"])} ± {es(va["MAE SD folds"])}', 'MAE test': es(te.MAE),
                     'R² CV': es(va['R² media folds']), 'R² test': es(te['R²'])})
    return table(pd.DataFrame(rows))


def t_diagnosticos():
    rows = []
    order = list(scores[scores.Conjunto == 'Validación (OOF)'].sort_values('RMSE media folds').Modelo)
    for n in order:
        for conj, label in [('Validación (OOF)', 'Validación OOF'), ('Prueba (test 202530)', 'Test 202530')]:
            r = diag[(diag.Modelo == n) & (diag.Conjunto == conj)].iloc[0]
            rows.append({'Modelo': n, 'Conjunto': label, 'n': int(r.n), 'RMSE': es(r.RMSE), 'Residuo medio': es(r['Residuo medio'], 3),
                         'p White': pv(r['White p']), 'p BDS': pv(r['BDS p']), 'p normalidad': pv(r['Normalidad p (D’Agostino)']),
                         'p Breusch–Pagan': pv(r['Breusch–Pagan p']), 'Spearman \\|e\\| vs ŷ': es(r['Spearman |e| vs ŷ'], 3),
                         'Asimetría': es(r['Asimetría'], 3), 'Fuera de [0,5]': int(r['Fuera de [0,5]'])})
    return table(pd.DataFrame(rows), ['---', '---'] + ['---:'] * 10)


def t_folds():
    rows = []
    for n in list(scores[scores.Conjunto == 'Validación (OOF)'].sort_values('RMSE media folds').Modelo):
        long = [k for k, v in LONG_TO_SHORT.items() if v == n][0]
        f = folds[folds.Modelo == long].sort_values('Fold')
        rows.append({'Modelo': n, 'RMSE': f'{es(f.RMSE.mean())} ± {es(f.RMSE.std(ddof=1))}', 'MAE': f'{es(f.MAE.mean())} ± {es(f.MAE.std(ddof=1))}',
                     'MAPE (%)': f'{es(f["MAPE (%)"].mean(), 2)} ± {es(f["MAPE (%)"].std(ddof=1), 2)}', 'R²': f'{es(f["R²"].mean())} ± {es(f["R²"].std(ddof=1))}',
                     'Por fold (1–5)': ' · '.join(es(v, 3) for v in f.RMSE)})
    return table(pd.DataFrame(rows), ['---'] * 6)


def t_variabilidad():
    lead = folds[folds.Modelo == 'Kernel Ridge RBF'].sort_values('Fold').RMSE.to_numpy()
    rows = []
    for long, n in LONG_TO_SHORT.items():
        if n in ('Kernel Ridge RBF', 'KNN', 'Ridge', 'Lasso', 'Random Forest', 'XGBoost'):
            continue
        f = folds[folds.Modelo == long].sort_values('Fold').RMSE.to_numpy()
        sd = f.std(ddof=1)
        d = f.mean() - lead.mean()
        rows.append({'Modelo frente a Kernel Ridge': n, 'Δ RMSE medio CV': es(d), 'SD entre folds del modelo': es(sd), 'Δ / SD folds': es(d / sd, 2),
                     'Folds en que gana Kernel Ridge': f'{int((lead < f).sum())} de 5'})
    return table(pd.DataFrame(rows))


def t_rangos():
    r = pd.DataFrame(ANALYSIS['ranking'])
    out = pd.DataFrame({'Modelo': r['Modelo'].map(LONG_TO_SHORT)})
    for i in range(1, 6):
        out[f'Fold {i}'] = r[f'Rango fold {i}'].map(lambda v: es(v, 1).replace(',0', ''))
    out['Rango promedio'] = r['Rango promedio'].map(lambda v: es(v, 1))
    return table(out)


def t_mcs():
    m = pd.DataFrame(ANALYSIS['mcs'])
    out = pd.DataFrame({'Modelo': m['Modelo'].map(LONG_TO_SHORT), 'Rango promedio de pérdida': m['Rango promedio de pérdida'].map(lambda v: es(v, 1)),
                        'MSE medio CV': m['MSE medio CV'].map(es), 'p-valor MCS': m['p-valor MCS exploratorio'].map(pv),
                        'En MCS (α = 0,10)': m['En MCS exploratorio (α = 0.10)'], 'Paso de eliminación': m['Paso de eliminación']})
    return table(out)


def t_finalistas():
    p = pd.DataFrame(ANALYSIS['dm']['finalist_pairs'])
    mcs = {r['a']: r for r in ANALYSIS['dm']['finalist_pairs']}
    f = pd.DataFrame(ANALYSIS['pairs'])
    rows = []
    for (_, a), (_, b) in zip(p.iterrows(), f.iterrows()):
        rows.append({'Modelo A': LONG_TO_SHORT[a.a], 'Modelo B': LONG_TO_SHORT[a.b], 'Δ MSE (A − B)': es(b['Δ MSE (A − B)']),
                     'IC 95 % Δ MSE · folds': f'[{es(b["IC 95% inferior · folds"])}; {es(b["IC 95% superior · folds"])}]',
                     'Δ RMSE': es(a.delta_rmse), 'IC 95 % Δ RMSE · estudiantes': f'[{es(a.ic_low)}; {es(a.ic_high)}]',
                     'p crudo': es(a.p_raw), 'p con HLN': es(a.p_hln)})
    return table(pd.DataFrame(rows), ['---', '---'] + ['---:'] * 6)


def t_dm(which):
    d = pd.DataFrame(ANALYSIS['dm'][which])
    cols = {'Modelo vs SVM': d['model'].map(LONG_TO_SHORT)}
    if which == 'cv':
        cols['Posición MCS'] = d['mcs_position']
        cols['Δ MSE'] = d['delta_mse'].map(es)
    cols['Δ RMSE (puntos)'] = d['delta_rmse'].map(es)
    cols['IC 95 % ΔRMSE'] = [f'[{es(a)}; {es(b)}]' for a, b in zip(d.ic_low, d.ic_high)]
    cols['p crudo'] = d['p_raw'].map(es)
    cols['p con HLN'] = d['p_hln'].map(es)
    if which == 'cv':
        cols['p t corregida (CV)'] = d['p_corrected_t'].map(es)
    cols['Conclusión'] = d['conclusion']
    out = pd.DataFrame(cols)
    for i in out.index:
        if 'significativa' in out.loc[i, 'Conclusión'] and 'no' not in out.loc[i, 'Conclusión'].lower().split('significativa')[0][-4:]:
            pass
    return table(out, ['---'] + ['---:'] * (len(out.columns) - 2) + ['---'])


def t_efectos_lider():
    e = pd.DataFrame(ANALYSIS['effects'])
    e = e[e['Modelo A'] == 'Kernel Ridge RBF']
    rows = []
    for _, r in e.iterrows():
        c = abs(r['Delta de Cliff'])
        mag = 'despreciable' if c < .147 else 'pequeña' if c < .33 else 'mediana' if c < .474 else 'grande'
        rows.append({'Modelo A': 'Kernel Ridge RBF', 'Modelo B': LONG_TO_SHORT[r['Modelo B']], 'Δ MSE (A − B)': es(r['Δ MSE (A − B)']),
                     'Delta de Cliff': es(r['Delta de Cliff'], 2), 'd_z de Cohen': es(r['d de Cohen emparejado (d_z)'], 2), 'Magnitud (Cliff)': mag})
    return table(pd.DataFrame(rows), ['---', '---', '---:', '---:', '---:', '---'])


def t_efectos_svm():
    e = pd.DataFrame(ANALYSIS['effects'])
    sel = e[((e['Modelo B'] == 'SVM lineal') | (e['Modelo A'] == 'SVM lineal'))]
    rows = []
    for _, r in sel.iterrows():
        a, b, sign = r['Modelo A'], r['Modelo B'], 1
        if a == 'SVM lineal':
            a, b, sign = b, a, -1
        c = sign * r['Delta de Cliff']
        mag = 'despreciable' if abs(c) < .147 else 'pequeña' if abs(c) < .33 else 'mediana' if abs(c) < .474 else 'grande'
        rows.append({'Modelo (A)': LONG_TO_SHORT[a], 'Δ MSE (A − SVM)': es(sign * r['Δ MSE (A − B)']), 'Delta de Cliff': es(c, 2),
                     'd_z de Cohen': es(sign * r['d de Cohen emparejado (d_z)'], 2), 'Magnitud (Cliff)': mag})
    out = pd.DataFrame(rows)
    keep = [SHORT[k] for k in ORDER] + ['KNN', 'Ridge', 'Lasso', 'Random Forest', 'XGBoost']
    out['o'] = out['Modelo (A)'].map({n: i for i, n in enumerate(keep)})
    return table(out.sort_values('o').drop(columns='o'), ['---', '---:', '---:', '---:', '---'])


def t_final():
    ranking = {LONG_TO_SHORT[r['Modelo']]: r['Rango promedio'] for r in ANALYSIS['ranking']}
    mcs = {LONG_TO_SHORT[r['Modelo']]: r['En MCS exploratorio (α = 0.10)'] for r in ANALYSIS['mcs']}
    dm = {LONG_TO_SHORT[r['model']]: r for r in ANALYSIS['dm']['cv']}
    rows = []
    for key in ['svm', *ORDER]:
        n = SHORT[key]
        va, te = part(n, 'Validación (OOF)'), part(n, 'Prueba (test 202530)')
        method = '—' if key == 'svm' else METHOD[hpo[(hpo.Clave == key) & hpo.Elegido].iloc[0]['Método']]
        p = '—' if key == 'svm' else (es(dm[n]['p_raw'], 4) if n in dm else 'No evaluado')
        rows.append({'Modelo': n, 'Método de búsqueda final': method, 'RMSE CV (media ± SD)': f'{es(va["RMSE media folds"])} ± {es(va["RMSE SD folds"])}',
                     'MAE CV': es(va['MAE media folds']), 'RMSE test': es(te.RMSE), 'MAE test': es(te.MAE),
                     'Rango Friedman': es(ranking[n], 1), 'En MCS': mcs[n], 'vs SVM en CV (p crudo por estudiante)': p,
                     '_k': float(va['RMSE media folds'])})
    out = pd.DataFrame(rows).sort_values('_k').drop(columns='_k')
    return table(out, ['---', '---', '---', '---:', '---:', '---:', '---:', '---', '---:'])


def t_shap():
    s = pd.read_csv(S / 'shap_importancia_pct_lider.csv')
    s.columns = ['Variable', '% de la suma de media \\|SHAP\\|']
    s['% de la suma de media \\|SHAP\\|'] = s['% de la suma de media \\|SHAP\\|'].map(lambda v: es(v, 1))
    return table(s.head(8), ['---', '---:'])


def t_lime(case):
    l = pd.read_csv(S / 'lime_casos_lider.csv')
    s = pd.read_csv(S / 'shap_casos_lider.csv')
    s = s[s['Posición test'] == case].set_index('Variable')['SHAP']
    from tablas_labels import LABELS
    l = l[l['Caso test'] == case].head(6)
    rows = [{'Variable': LABELS[r['Variable']], 'Condición LIME': r['Condición del caso'].replace(r['Variable'], LABELS[r['Variable']]),
             'Peso LIME': es(r['Aporte local (puntos)'], 3), 'SHAP (permutaciones)': es(s.get(LABELS[r['Variable']], np.nan), 3)} for _, r in l.iterrows()]
    return table(pd.DataFrame(rows), ['---', '---', '---:', '---:'])


def lime_meta(case):
    l = pd.read_csv(S / 'lime_casos_lider.csv')
    r = l[l['Caso test'] == case].iloc[0]
    return {'pred': r.prediction, 'sust': r.local_prediction, 'r2': r.fidelity, 'gap': r.absolute_gap}


def shap_value(case, variable):
    s = pd.read_csv(S / 'shap_casos_lider.csv')
    return float(s[(s['Posición test'] == case) & (s.Variable == variable)].SHAP.iloc[0])

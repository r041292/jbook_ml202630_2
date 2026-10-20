"""Contraste tipo Diebold–Mariano agrupado por estudiante (Etapa 3 de Originales).

Pérdida = error cuadrático por fila. Se suma por estudiante y se prueba que la media de la
diferencia de pérdidas (candidato − referencia) sea cero, con error estándar robusto por
cluster (estudiante) y aproximación normal. IC95% por bootstrap de estudiantes.
No es la versión de series de tiempo (HAC): la dependencia que se corrige es la de las filas
de un mismo estudiante. Sin entrenamiento ni consulta al test para seleccionar.
"""
import numpy as np
import pandas as pd
from dash import html
from scipy import stats

SEED = 20261020
BOOT = 9999
REFERENCE = 'SVM lineal'


def select_top(mcs, k=5, reference=REFERENCE):
    """Orden propio del MCS: los últimos en ser eliminados primero; se omite la referencia.

    Los modelos que sobreviven al MCS ocupan los primeros lugares; si son menos de k, se
    completa con los siguientes en el orden de eliminación.
    """
    table = pd.DataFrame(mcs).sort_values('Paso de eliminación', ascending=False, kind='stable')
    table = table.loc[table.Modelo.ne(reference)].head(k).reset_index(drop=True)
    table['Posición MCS'] = np.arange(1, len(table) + 1)
    return table


def clustered_test(loss_ref, loss_new, groups, boots=BOOT, seed=SEED):
    diff = np.asarray(loss_new, float) - np.asarray(loss_ref, float)
    frame = pd.DataFrame({'d': diff, 'a': np.asarray(loss_ref, float), 'b': np.asarray(loss_new, float), 'g': groups})
    sums = frame.groupby('g')[['d', 'a', 'b']].sum()
    n = frame.groupby('g').size().to_numpy(float)
    G, total = len(sums), n.sum()
    mean = sums.d.sum() / total
    se = np.sqrt(G / (G - 1) * ((sums.d.to_numpy() - mean * n) ** 2).sum()) / total
    z = mean / se if se > 0 else np.nan
    p = float(2 * stats.norm.sf(abs(z))) if se > 0 else None
    # Corrección tipo Harvey–Leybourne–Newbold (h = 1): z·√((G−1)/G) y t de Student con G−1 g.l.
    z_hln = z * np.sqrt((G - 1) / G) if se > 0 else np.nan
    p_hln = float(2 * stats.t.sf(abs(z_hln), G - 1)) if se > 0 else None
    rng = np.random.default_rng(seed)
    sa, sb = sums.a.to_numpy(), sums.b.to_numpy()
    draws = np.empty(boots)
    for start in range(0, boots, 1000):
        stop = min(start + 1000, boots)
        ix = rng.integers(0, G, (stop - start, G))
        draws[start:stop] = np.sqrt(sb[ix].sum(1) / n[ix].sum(1)) - np.sqrt(sa[ix].sum(1) / n[ix].sum(1))
    low, high = np.quantile(draws, [.025, .975])
    return {'n_students': int(G), 'n_records': int(total), 'delta_mse': float(mean), 'se_cluster': float(se),
            'z': None if se == 0 else float(z), 'p_raw': p,
            'z_hln': None if se == 0 else float(z_hln), 'p_hln': p_hln,
            'delta_rmse': float(np.sqrt(frame.b.mean()) - np.sqrt(frame.a.mean())),
            'ic_low': float(low), 'ic_high': float(high)}


def conclusion(row, alpha=.05):
    if row['p_raw'] is None:
        return 'No estimable'
    if row['p_raw'] < alpha:
        return 'Mejora significativa' if row['delta_mse'] < 0 else 'Deterioro significativo'
    return 'Diferencia no significativa'


def analyze(top, oof, test, groups_train, groups_test, y_train, y_test, names_to_keys, reference_key='svm',
            corrected=None):
    """top: tabla de select_top; oof/test: DataFrames de predicciones por clave de catálogo."""
    def losses(pred, y):
        return (np.asarray(pred, float) - np.asarray(y, float)) ** 2
    result = {}
    for label, preds, y, groups in (('cv', oof, y_train, groups_train), ('test', test, y_test, groups_test)):
        ref = losses(preds[reference_key], y)
        rows = []
        for _, t in top.iterrows():
            rows.append({'model': t['Modelo'], 'mcs_position': int(t['Posición MCS']),
                         'in_mcs': t['En MCS exploratorio (α = 0.10)'] == 'Sí',
                         **clustered_test(ref, losses(preds[names_to_keys[t['Modelo']]], y), groups)})
        for row in rows:
            row['conclusion'] = conclusion(row)
            if label == 'cv' and corrected is not None and row['model'] in corrected.index:
                saved = corrected.loc[row['model']]
                row['p_corrected_t'] = None if pd.isna(saved.p_bilateral) else float(saved.p_bilateral)
                row['se_corrected_t'] = float(saved.SE_corregido) if 'SE_corregido' in saved and pd.notna(saved.SE_corregido) else None
        result[label] = rows
    result.update(reps=BOOT, seed=SEED, top=top.to_dict('records'), reference=REFERENCE)
    return result


def render(dm, ui, scope='Originales', mcs_label='Etapa 2'):
    """Etapa 3 común a Originales y Clásicos: componentes Dash a partir de analyze()."""
    md, table = ui['md'], ui['table']
    alpha = .05
    fmt = lambda v: 'No estimable' if v is None else f'{v:.6f}'
    cv_rows = dm['cv']
    top_n = len(cv_rows)
    main = pd.DataFrame([{'Posición MCS': r['mcs_position'], 'Modelo vs SVM': r['model'],
        'En MCS (α = 0.10)': 'Sí' if r['in_mcs'] else 'No (siguiente en el orden)',
        'Δ MSE': r['delta_mse'], 'Δ RMSE': r['delta_rmse'],
        'IC95 inferior (Δ RMSE)': r['ic_low'], 'IC95 superior (Δ RMSE)': r['ic_high'],
        'p crudo': fmt(r['p_raw']), 'p crudo con corrección HLN': fmt(r.get('p_hln')),
        'p t corregida CV (sensibilidad)': fmt(r.get('p_corrected_t')), 'Conclusión': r['conclusion']}
        for r in cv_rows])
    test_rows = pd.DataFrame([{'Modelo vs SVM': r['model'], 'Estudiantes': r['n_students'], 'Δ RMSE': r['delta_rmse'],
        'IC95 inferior': r['ic_low'], 'IC95 superior': r['ic_high'], 'p crudo': fmt(r['p_raw']), 'p crudo con corrección HLN': fmt(r.get('p_hln')),
        'Conclusión': r['conclusion']} for r in dm['test']])
    significant = [r for r in cv_rows if r['p_raw'] is not None and r['p_raw'] < alpha]
    n_students = cv_rows[0]['n_students']
    better = [r for r in significant if r['delta_mse'] < 0]
    worse = [r for r in significant if r['delta_mse'] > 0]
    describe = lambda rows: ', '.join(f"{r['model']} (Δ RMSE {r['delta_rmse']:+.4f})" for r in rows)
    if better:
        conclusion = (f'{len(better)} de {top_n} modelos superan significativamente al SVM lineal (p crudo < 0.05): {describe(better)}')
        if worse:
            conclusion += f'; {len(worse)} resulta(n) significativamente peor(es): {describe(worse)}'
    elif worse:
        conclusion = (f'Ninguno de los {top_n} modelos presentó un resultado significativamente mejor que el SVM lineal (p crudo < 0.05), '
                      + (f'y solo se identificó uno con un resultado inferior: {describe(worse)}' if len(worse) == 1 else
                         f'y {len(worse)} presentaron un resultado inferior: {describe(worse)}'))
    else:
        conclusion = (f'Ninguno de los {top_n} modelos difiere significativamente del SVM lineal (p crudo < 0.05); '
                      'esto no demuestra que sean equivalentes.')
    conclusion += '.'
    sensitive_better = [r for r in better if r.get('p_corrected_t') is not None and r['p_corrected_t'] >= alpha]
    sensitive_worse = [r for r in worse if r.get('p_corrected_t') is not None and r['p_corrected_t'] >= alpha]
    names = lambda rows: ', '.join(r['model'] for r in rows)
    reading = []
    if sensitive_better:
        reading.append(f'**Cómo leer la diferencia entre las dos pruebas.** Para {names(sensitive_better)}, la prueba por estudiante detecta que la ventaja '
                       'sobre el SVM es **estable entre los estudiantes de esta muestra** (el modelo falla menos en la mayoría de los casos). '
                       'La prueba conservadora no llega a p < 0.05: **no puede descartar que esa ventaja dependa de los datos concretos con los que se '
                       'entrenó el modelo** y desaparezca al reentrenarlo con otros estudiantes. Por eso la mejora se considera probable, pero no confirmada.')
    if sensitive_worse:
        reading.append(f'**Lectura de {names(sensitive_worse)}.** La prueba por estudiante indica que el modelo es peor que el SVM en esta muestra; '
                       'la conservadora no confirma que lo sea al reentrenar con otros datos, así que el deterioro se considera probable, pero no confirmado.')
    changed = [r['model'] for part in ('cv', 'test') for r in dm[part]
               if r.get('p_hln') is not None and r['p_raw'] is not None and (r['p_raw'] < alpha) != (r['p_hln'] < alpha)]
    hln_note = (
        '**Corrección HLN (muestra finita).** El p crudo usa la distribución normal, que tiende a ser algo optimista cuando hay pocas observaciones. '
        'La columna «p crudo con corrección HLN» aplica la corrección de Harvey, Leybourne y Newbold (1997) en su versión para horizonte h = 1: '
        'el estadístico se multiplica por √((G−1)/G) y se compara con una t de Student de G−1 grados de libertad, donde G es el número de estudiantes. '
        'No se usa la forma con h > 1 porque aquí no hay una secuencia temporal de pronósticos: las observaciones son estudiantes y no periodos consecutivos. '
        + ('Con esta corrección **ningún veredicto cambia** (ni en CV ni en test): el efecto es menor porque G es grande, y por eso las conclusiones se siguen '
           'expresando con el p crudo. ' if not changed else
           f'Con esta corrección **cambia el veredicto de: {", ".join(sorted(set(changed)))}**; se recomienda leer la columna HLN. ') +
        'La columna de la prueba conservadora responde otra cuestión (reentrenamiento) y no se sustituye por esta.')
    ses = [r['se_corrected_t'] for r in cv_rows if r.get('se_corrected_t')]
    if ses:
        t_crit = float(stats.t.ppf(.975, 4))
        needed = t_crit * float(np.median(ses))
        best = max(abs(r['delta_rmse']) for r in cv_rows)
        power_note = (
            '**Por qué la prueba conservadora rara vez sale significativa aquí.** (1) Solo tiene **5 observaciones** (los folds), es decir 4 grados de libertad: '
            f'el valor crítico de la t es {t_crit:.2f} y no ≈1.96 como con cientos de estudiantes. '
            '(2) Cada fold deja fuera ~260 estudiantes y los entrenamientos de los 5 folds comparten ~80 % de los datos; la corrección de Nadeau–Bengio lo reconoce '
            'y agranda el error estándar ~1.5 veces. (3) La dificultad cambia entre folds, así que la diferencia de RMSE de un mismo modelo varía bastante de un fold a otro. '
            f'Con el error estándar típico de esta tabla (~{float(np.median(ses)):.3f}), un modelo necesitaría mejorar al SVM en ≈{needed:.3f} puntos de RMSE para llegar a p < 0.05; '
            f'la mayor diferencia observada entre estos modelos es {best:.3f}. '
            'Más repeticiones de la CV ayudarían poco: parte del error viene de que el conjunto es pequeño (1309 filas de 1293 estudiantes), no del número de particiones. '
            'Por eso un p alto aquí significa «no hay potencia para confirmarlo», no «el modelo no sirve».')
    else:
        power_note = ''
    return [
        html.H4(f'Etapa 3 · Diebold–Mariano por estudiante · los {top_n} primeros del MCS frente al SVM'),
        md('**Qué mide esta prueba.** Para cada estudiante se calcula cuánto más (o menos) se equivoca el modelo candidato '
           'que el SVM lineal, midiendo el error con el cuadrado de la diferencia entre nota real y nota predicha. '
           'Se promedia esa diferencia entre estudiantes. **H₀: en promedio ambos modelos se equivocan lo mismo.** '
           'Un **Δ MSE o Δ RMSE negativo favorece al candidato**; el p crudo indica qué tan raro sería ver una ventaja así '
           'si de verdad fueran igual de buenos. Es la idea de Diebold–Mariano (comparar la pérdida promedio de dos '
           'predictores), pero no la versión de series de tiempo: aquí el error estándar se agrupa por **estudiante**, '
           'porque las filas de una misma persona (varios periodos) no son independientes. '
           'Las predicciones son las **fuera de muestra de la CV** (cada nota predicha por un modelo que no vio a ese estudiante).'),
        md(f'**Qué modelos se comparan.** El MCS ({mcs_label}) conserva {sum(r["in_mcs"] for r in cv_rows)} modelo(s) distinto(s) del SVM con α 0.10; '
           f'para llegar a {top_n} se completa con los siguientes en su orden de eliminación (el SVM lineal, que es la referencia, se omite). '
           f'Se usan **{n_students} estudiantes** y un bootstrap de estudiantes ({dm["reps"]} réplicas, semilla {dm["seed"]}) para el IC95%.'),
        md('**Comparaciones independientes, sin corrección de Holm.** Cada modelo se compara únicamente contra el SVM lineal, como una pregunta propia '
           '(«¿este modelo mejora al SVM?»); **no se comparan entre sí**. Como no se declara una conclusión conjunta sobre todo el grupo, '
           'no se aplicó la corrección de Holm, que solo hace falta cuando se quiere afirmar algo sobre la familia completa. '
           f'Cada resultado se juzga con su propio p crudo a α 0.05. Tenga presente que, al hacer {top_n} pruebas separadas, '
           'la probabilidad de que alguna salga significativa por azar es mayor que 5 %. Los p y los IC son aproximaciones normales/percentiles, individuales.'),
        table(main), md('**Conclusión:** ' + conclusion),
        md(hln_note),
        md('**Qué es la «prueba conservadora» (columna «p t corregida CV»).** Hace la misma comparación contra el SVM, pero con otra fuente de azar: '
           f'en vez de {n_students} estudiantes usa como observaciones los **5 folds de validación** y agranda su error estándar, porque los entrenamientos de esos '
           'folds comparten la mayor parte de los datos (corrección de Nadeau–Bengio). Responde a otra pregunta: «si el algoritmo se reentrenara con '
           'otros datos, ¿seguiría siendo mejor que el SVM?». Con solo 5 observaciones es mucho más exigente y rara vez da p < 0.05, así que sirve '
           'como control de cautela y no como la prueba principal.'),
        *[md(text) for text in reading],
        md(power_note),
        md('**Límites.** (1) El p por estudiante no incluye la variabilidad de reentrenar con otros estudiantes, así que tiende a ser optimista. '
           f'(2) Los {top_n} modelos se eligieron por su desempeño en esta misma CV (MCS), por lo que la selección tampoco está corregida: '
           'la inferencia es exploratoria. (3) No se elige ningún modelo ni parámetro con test.'),
        html.Details([html.Summary('Complemento · mismo contraste en el test temporal (202530)'),
            md(f'{dm["test"][0]["n_students"]} estudiantes; modelos fijos y periodo ya revisado, sin incertidumbre de entrenamiento. '
               'Con menos estudiantes hay menos potencia; sirve para ver si el signo se mantiene fuera de la CV.'),
            table(test_rows)], className='details'),
    ]


def corrected_from_folds(folds, reference, ratio):
    """t corregida de Nadeau–Bengio (1×5 folds, df=4) de cada modelo vs la referencia; DataFrame por Modelo."""
    wide = folds.pivot(index='Fold', columns='Modelo', values='RMSE').sort_index()
    rows = {}
    for name in wide.columns.drop(reference):
        d = (wide[name] - wide[reference]).to_numpy(float)
        se = np.sqrt((1 / len(d) + ratio) * d.var(ddof=1))
        rows[name] = {'p_bilateral': float(2 * stats.t.sf(abs(d.mean() / se), len(d) - 1)) if se > 0 else np.nan,
                      'SE_corregido': float(se)}
    return pd.DataFrame.from_dict(rows, orient='index').rename_axis('Modelo')


ADAPTATION_NOTE = (
    '**Por qué se adapta el DM-HLN y qué adaptación se hizo.** El contraste de Diebold–Mariano, con la corrección de Harvey, '
    'Leybourne y Newbold (HLN), se diseñó para series de tiempo: compara los errores de dos pronósticos hechos en fechas sucesivas, con un '
    'horizonte h, y corrige la dependencia entre fechas vecinas (varianza HAC). Aquí no hay secuencia de pronósticos ni horizonte: el '
    'índice de fold y el orden de las filas no son tiempo, y cinco folds darían solo cinco observaciones con entrenamientos solapados. '
    'Lo que sí existe es otra dependencia: un mismo estudiante aparece en varios periodos y sus errores se parecen. Se conserva entonces la idea '
    'central (probar que la pérdida media de A y B es la misma) y se **adapta** así: '
    '(1) la observación es el **estudiante**, no la fecha; '
    '(2) el error estándar es **robusto por estudiante** (cluster) en lugar de HAC; '
    '(3) la corrección HLN se aplica con **h = 1**: el estadístico se multiplica por √((G−1)/G) y se compara con una t de Student de G−1 grados de libertad, '
    'sin horizonte de varios pasos porque no hay pronósticos solapados; '
    '(4) las pérdidas son las **predicciones fuera de muestra de la validación cruzada** (cada nota la predice un modelo que no vio al estudiante); '
    '(5) el IC95 se obtiene **remuestreando estudiantes** y no con bootstrap estacionario. '
    'Cada par se contrasta de forma independiente y **sin ajuste de Holm**. Es una adaptación exploratoria: no incluye la variabilidad de reentrenar '
    'con otros estudiantes y los finalistas se eligieron con esta misma validación.')


def finalist_pairs(fold_pairs, oof, groups, y, name_key):
    """DM-HLN adaptado para cada par (A, B) de finalistas; diferencia = pérdida A − pérdida B."""
    def loss(name):
        return (np.asarray(oof[name_key[name]], float) - np.asarray(y, float)) ** 2
    rows = []
    for a, b in zip(fold_pairs['Modelo A'], fold_pairs['Modelo B']):
        row = {'a': a, 'b': b, **clustered_test(loss(b), loss(a), groups)}
        row['conclusion'] = conclusion(row)
        rows.append(row)
    return rows


def pairs_table(fold_pairs, dm_pairs):
    """Une los IC descriptivos por folds con el DM-HLN adaptado por estudiante."""
    fmt = lambda v: 'No estimable' if v is None else f'{v:.6f}'
    rows = []
    for _, f in fold_pairs.iterrows():
        d = next((r for r in dm_pairs if r['a'] == f['Modelo A'] and r['b'] == f['Modelo B']), None)
        rows.append({'Modelo A': f['Modelo A'], 'Modelo B': f['Modelo B'], 'Δ MSE (A − B)': f['Δ MSE (A − B)'],
                     'IC 95% inferior · folds': f['IC 95% inferior · folds'],
                     'IC 95% superior · folds': f['IC 95% superior · folds'],
                     'Δ RMSE (A − B) · por estudiante': None if d is None else d['delta_rmse'],
                     'IC 95% inferior · estudiantes': None if d is None else d['ic_low'],
                     'IC 95% superior · estudiantes': None if d is None else d['ic_high'],
                     'p-valor crudo DM adaptado': 'No estimable' if d is None else fmt(d['p_raw']),
                     'p-valor con corrección HLN': 'No estimable' if d is None else fmt(d['p_hln']),
                     'Conclusión (p crudo < 0.05)': 'No estimable' if d is None else d['conclusion']})
    return pd.DataFrame(rows)


def pairs_reading(dm_pairs, alpha=.05):
    significant = [r for r in dm_pairs if r['p_raw'] is not None and r['p_raw'] < alpha]
    if not dm_pairs:
        return ''
    if not significant:
        return (f'**Lectura:** ninguno de los {len(dm_pairs)} pares de finalistas difiere significativamente (p crudo < 0.05). '
                'Esto no demuestra que sean equivalentes: indica que los datos no permiten distinguirlos.')
    return ('**Lectura:** difieren significativamente (p crudo < 0.05) ' +
            '; '.join(f"{r['a']} frente a {r['b']} (Δ RMSE {r['delta_rmse']:+.4f})" for r in significant) +
            f'. Los otros {len(dm_pairs) - len(significant)} pares no se distinguen.')

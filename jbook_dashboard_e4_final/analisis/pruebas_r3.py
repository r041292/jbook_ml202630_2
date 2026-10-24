"""Pruebas de hipótesis R3 (Bloque D, §6) sin reentrenar ni volver a predecir.

Compara cada modelo original (KRR centrado `m5`, TN-KRR `m19`, GPR–XGBoost `m15`) con cada
uno de los 7 modelos base sobre las MISMAS predicciones OOF (mismos 5 folds externos
GroupKFold por estudiante, misma semilla 42 y mismo preprocesamiento por familia):

Pruebas por pares (21 comparaciones = 3 originales × 7 base):
  1. Wilcoxon de rangos con signo sobre las diferencias de RMSE por fold (exacta, n = 5).
  2. Permutación pareada por estudiante (cambio de signo de la diferencia de error cuadrático
     sumada por estudiante; 9.999 permutaciones).
  3. t corregida de Nadeau–Bengio sobre las diferencias de RMSE por fold (gl = 4).
  4. Bootstrap pareado BCa por estudiante de ΔRMSE (9.999 réplicas; p por inversión del IC).
  5. Contraste tipo Diebold–Mariano por estudiante con corrección HLN (h = 1), el mismo del
     dashboard (`Dash/student_dm.py`).
Procedimientos globales (universo de 10 modelos: 7 base + 3 originales, y universo
complementario de 16: los 15 del dashboard + Decision Tree):
  6. Friedman → Nemenyi (diferencia crítica).
  7. Model Confidence Set (Hansen–Lunde–Nason, `Dash/classic_posthoc.mcs_range`).
Ajustes: Holm (principal) y Benjamini–Hochberg dentro de cada prueba (familia de 21) y Holm
global sobre las 105 comparaciones por pares. Tamaños de efecto sobre el MSE por fold:
δ de Cliff (umbrales de Romano et al., 2006) y d_z de Cohen.

Salidas en `salidas/`: pruebas_r3.csv, pruebas_r3_globales.csv, resumen_modelos.csv,
veredicto_r3.csv, mcs_u10.csv, mcs_u16.csv, friedman_u10.csv, ablacion.csv, pruebas_r3_meta.json
y la figura `images/e4/cd_u10.png`.
"""
import json
from itertools import product

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

from comun import (BASE, DASH, IMAGES, LABELS, OLD_BOOK, ORIGINAL, OUT, SEED, fold_metrics, gpr_solo_oof,
                   oof_predictions, partitions, rmse)
from classic_friedman import friedman_comparison
from classic_posthoc import bootstrap_indices, effect_sizes, mcs_range
from nemenyi import critical_difference
from student_dm import clustered_test

REPS = 9999
ALPHA, ALPHA_MCS = 0.05, 0.10
TARGET = 'nota_primer_parcial'
BEST_BENCHMARK = 'xgboost'   # menor RMSE medio externo de los 7 base (tabla_mejores_combinaciones.py)


# ----------------------------------------------------------------------------- utilidades
def cliff_magnitude(delta):
    a = abs(delta)
    return 'despreciable' if a < .147 else 'pequeña' if a < .33 else 'mediana' if a < .474 else 'grande'


def student_sums(y, pred, groups):
    """Suma del error cuadrático y número de registros por estudiante."""
    frame = pd.DataFrame({'se': (np.asarray(y) - np.asarray(pred)) ** 2, 'g': np.asarray(groups)})
    agg = frame.groupby('g')['se'].agg(['sum', 'size'])
    return agg['sum'].to_numpy(), agg['size'].to_numpy(float), agg.index


def permutation_test(sum_o, sum_b, n, reps=REPS, seed=SEED):
    """H0: intercambiabilidad de las etiquetas modelo dentro de cada estudiante.

    Intercambiar las predicciones de los dos modelos para un estudiante cambia el signo de
    D_i = Σ(e²_original − e²_base); el estadístico es la diferencia media de MSE ΣD/Σn.
    """
    d = sum_o - sum_b
    observed = d.sum() / n.sum()
    rng = np.random.default_rng(seed)
    exceed = 0
    for start in range(0, reps, 1000):
        signs = rng.choice((-1.0, 1.0), size=(min(1000, reps - start), len(d)))
        exceed += int((np.abs(signs @ d / n.sum()) >= abs(observed) - 1e-15).sum())
    return float(observed), (exceed + 1) / (reps + 1)


def bca_test(sum_o, sum_b, n, reps=REPS, seed=SEED):
    """Bootstrap pareado BCa (por estudiante) de ΔRMSE = RMSE_original − RMSE_base.

    IC 95 % BCa (Efron, 1987) con aceleración por jackknife de estudiantes. El p bilateral
    se obtiene invirtiendo el IC: el menor α para el que el IC BCa (1 − α) excluye el 0.
    """
    total = n.sum()
    point = np.sqrt(sum_o.sum() / total) - np.sqrt(sum_b.sum() / total)
    rng = np.random.default_rng(seed)
    draws = np.empty(reps)
    for start in range(0, reps, 500):
        stop = min(start + 500, reps)
        ix = rng.integers(0, len(n), (stop - start, len(n)))
        nn = n[ix].sum(1)
        draws[start:stop] = np.sqrt(sum_o[ix].sum(1) / nn) - np.sqrt(sum_b[ix].sum(1) / nn)
    jack = np.sqrt((sum_o.sum() - sum_o) / (total - n)) - np.sqrt((sum_b.sum() - sum_b) / (total - n))
    centered = jack.mean() - jack
    accel = float(np.sum(centered ** 3) / (6 * np.sum(centered ** 2) ** 1.5))
    z0 = float(stats.norm.ppf((np.mean(draws < point) + np.mean(draws <= point)) / 2))

    def bound(alpha):
        z = z0 + stats.norm.ppf(alpha)
        return float(np.quantile(draws, stats.norm.cdf(z0 + z / (1 - accel * z))))

    low, high = bound(.025), bound(.975)
    # Inversión: posición del 0 en la distribución bootstrap → nivel nominal equivalente.
    q = np.clip((np.mean(draws < 0) + np.mean(draws <= 0)) / 2, 1 / (reps + 1), reps / (reps + 1))
    w = stats.norm.ppf(q) - z0
    z_alpha = w / (1 + accel * w) - z0
    p = float(min(1.0, 2 * min(stats.norm.cdf(z_alpha), stats.norm.sf(z_alpha))))
    return float(point), low, high, p, z0, accel


def nadeau_bengio(rmse_o, rmse_b, ratio):
    """t corregida de Nadeau y Bengio (2003): var = s²(1/k + n_val/n_fit), gl = k − 1."""
    d = np.asarray(rmse_o) - np.asarray(rmse_b)
    k = len(d)
    se = np.sqrt(d.var(ddof=1) * (1 / k + ratio))
    t = d.mean() / se
    return float(d.mean()), float(t), float(2 * stats.t.sf(abs(t), k - 1)), float(se)


def wilcoxon_folds(rmse_o, rmse_b):
    d = np.asarray(rmse_o) - np.asarray(rmse_b)
    result = stats.wilcoxon(d, alternative='two-sided', method='exact')
    return float(result.statistic), float(result.pvalue)


def cd_figure(ranking, cd, path, highlight):
    order = ranking.sort_values('Rango promedio', kind='stable').reset_index(drop=True)
    k = len(order)
    fig, ax = plt.subplots(figsize=(8.6, 0.42 * k + 1.6))
    y = np.arange(k)[::-1]
    colors = ['#c2410c' if m in highlight else '#475569' for m in order.Modelo]
    ax.hlines(y, 1, order['Rango promedio'], color='#e2e8f0', lw=1)
    ax.scatter(order['Rango promedio'], y, c=colors, s=46, zorder=3)
    for yi, (m, r) in zip(y, order[['Modelo', 'Rango promedio']].to_numpy()):
        ax.text(r + .12, yi, f'{m} ({r:.1f})', va='center', fontsize=9, color='#0f172a')
    start = float(order['Rango promedio'].iloc[0])
    ax.plot([start, start + cd], [k, k], color='#0f172a', lw=3)
    ax.text(start + cd / 2, k + .35, f'Diferencia crítica de Nemenyi = {cd:.2f}', ha='center', fontsize=9)
    ax.set_xlim(.5, k + 3.2)
    ax.set_ylim(-1, k + 1)
    ax.set_yticks([])
    ax.set_xlabel('Rango promedio del RMSE en los 5 folds externos (1 = menor error; adimensional)')
    ax.set_title('Friedman–Nemenyi · 7 modelos base y 3 originales (naranja)', fontsize=11)
    for side in ('top', 'right', 'left'):
        ax.spines[side].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def interval_figure(tests, path):
    """ΔRMSE (original − base) con IC 95 % BCa por estudiante para las 21 comparaciones."""
    bca = tests.loc[tests.Prueba.eq('Bootstrap pareado BCa')].reset_index(drop=True)
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.9), sharex=True, sharey=True)
    for ax, (label, part) in zip(axes, bca.groupby('Original', sort=False)):
        y = np.arange(len(part))[::-1]
        color = np.where(part['p Holm (familia de 21)'] < ALPHA, '#c2410c', '#64748b')
        ax.errorbar(part['Estadístico'], y, xerr=[part['Estadístico'] - part['IC 95 % inferior'],
                                                  part['IC 95 % superior'] - part['Estadístico']],
                    fmt='none', ecolor=color, elinewidth=2)
        ax.scatter(part['Estadístico'], y, c=color, zorder=3, s=28)
        ax.axvline(0, color='#0f172a', lw=1, ls='--')
        ax.set_yticks(y, part['Base'])
        ax.set_title(label, fontsize=10)
        ax.set_xlabel('Δ RMSE (puntos de nota)')
        ax.grid(axis='x', color='#e2e8f0')
    fig.suptitle('Diferencia de RMSE OOF frente a cada modelo base · IC 95 % BCa por estudiante '
                 '(naranja: p Holm < 0,05)', fontsize=10.5)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


# ----------------------------------------------------------------------------- análisis
def main():
    train, test = partitions()
    y, groups = train[TARGET].to_numpy(), train['estudiante'].to_numpy()
    oof = oof_predictions()
    folds = fold_metrics()
    rmse_fold = folds.pivot(index='Fold', columns='clave', values='RMSE')
    mse_fold = rmse_fold ** 2

    # Verificación del emparejamiento: las métricas por fold guardadas se reproducen desde las OOF.
    for key in LABELS:
        recomputed = [rmse(y[oof.fold == f], oof.loc[oof.fold == f, key]) for f in range(1, 6)]
        assert np.allclose(recomputed, rmse_fold[key].to_numpy(), atol=1e-9), key

    # Proporción n_val/n_fit en estudiantes (la misma que usa cv_inference.csv del dashboard).
    ratio = float(np.mean([len(set(groups[oof.fold == f])) / len(set(groups[oof.fold != f])) for f in range(1, 6)]))

    sums = {key: student_sums(y, oof[key], groups) for key in LABELS}
    n_students = sums['svm'][1]

    rows = []
    for o, b in product(ORIGINAL, BASE):
        so, n, _ = sums[o]
        sb, _, _ = sums[b]
        w_stat, w_p = wilcoxon_folds(rmse_fold[o], rmse_fold[b])
        perm_d, perm_p = permutation_test(so, sb, n)
        nb_d, nb_t, nb_p, nb_se = nadeau_bengio(rmse_fold[o], rmse_fold[b], ratio)
        bca_d, bca_low, bca_high, bca_p, z0, accel = bca_test(so, sb, n)
        dm = clustered_test((y - oof[b]) ** 2, (y - oof[o]) ** 2, groups)
        delta, dz = effect_sizes(mse_fold[o], mse_fold[b])
        common = {'Original': ORIGINAL[o], 'clave_original': o, 'Base': BASE[b], 'clave_base': b,
                  'Δ RMSE medio CV (original − base)': float(rmse_fold[o].mean() - rmse_fold[b].mean()),
                  'Δ RMSE OOF reunido': rmse(y, oof[o]) - rmse(y, oof[b]),
                  'Delta de Cliff (MSE por fold)': delta, 'Magnitud Cliff': cliff_magnitude(delta),
                  'd_z de Cohen (MSE por fold)': dz,
                  'Folds en que gana el original': int((rmse_fold[o] < rmse_fold[b]).sum())}
        rows += [
            {**common, 'Prueba': 'Wilcoxon por fold', 'Unidad': '5 folds', 'Estadístico': w_stat,
             'Nombre del estadístico': 'W (suma de rangos)', 'p crudo': w_p, 'IC 95 % inferior': np.nan, 'IC 95 % superior': np.nan},
            {**common, 'Prueba': 'Permutación pareada por estudiante', 'Unidad': f'{len(n)} estudiantes',
             'Estadístico': perm_d, 'Nombre del estadístico': 'Δ MSE medio', 'p crudo': perm_p,
             'IC 95 % inferior': np.nan, 'IC 95 % superior': np.nan},
            {**common, 'Prueba': 't corregida de Nadeau–Bengio', 'Unidad': '5 folds', 'Estadístico': nb_t,
             'Nombre del estadístico': 't (gl = 4)', 'p crudo': nb_p,
             'IC 95 % inferior': nb_d - stats.t.ppf(.975, 4) * nb_se, 'IC 95 % superior': nb_d + stats.t.ppf(.975, 4) * nb_se},
            {**common, 'Prueba': 'Bootstrap pareado BCa', 'Unidad': f'{len(n)} estudiantes', 'Estadístico': bca_d,
             'Nombre del estadístico': 'Δ RMSE', 'p crudo': bca_p, 'IC 95 % inferior': bca_low, 'IC 95 % superior': bca_high},
            {**common, 'Prueba': 'Diebold–Mariano por estudiante (HLN)', 'Unidad': f'{dm["n_students"]} estudiantes',
             'Estadístico': dm['z_hln'], 'Nombre del estadístico': 'z·√((G−1)/G), t con G−1 gl', 'p crudo': dm['p_hln'],
             'IC 95 % inferior': dm['ic_low'], 'IC 95 % superior': dm['ic_high']},
        ]
    tests = pd.DataFrame(rows)
    tests['p Holm (familia de 21)'] = np.nan
    tests['p BH (familia de 21)'] = np.nan
    for name, idx in tests.groupby('Prueba').groups.items():
        tests.loc[idx, 'p Holm (familia de 21)'] = multipletests(tests.loc[idx, 'p crudo'], method='holm')[1]
        tests.loc[idx, 'p BH (familia de 21)'] = multipletests(tests.loc[idx, 'p crudo'], method='fdr_bh')[1]
    tests['p Holm global (105)'] = multipletests(tests['p crudo'], method='holm')[1]
    tests['p BH global (105)'] = multipletests(tests['p crudo'], method='fdr_bh')[1]
    tests['Rechaza H0 (Holm 21, α = 0,05)'] = tests['p Holm (familia de 21)'] < ALPHA
    tests['Rechaza H0 (Holm global 105)'] = tests['p Holm global (105)'] < ALPHA
    tests['Conclusión'] = np.where(
        ~tests['Rechaza H0 (Holm 21, α = 0,05)'], 'No se rechaza H0',
        np.where(tests['Δ RMSE OOF reunido'] < 0, 'Original mejor (significativo)', 'Original peor (significativo)'))
    tests.to_csv(OUT / 'pruebas_r3.csv', index=False, encoding='utf-8')
    interval_figure(tests, IMAGES / 'ic_bca_pares.png')

    # ---------------------------------------------------- procedimientos globales
    names10 = [*BASE, *ORIGINAL]
    long = folds.rename(columns={'clave': 'Modelo'})
    fr10 = friedman_comparison(long, names10)
    q10, cd10 = critical_difference(len(names10), 5)
    rank10 = fr10['ranking'].assign(Modelo=lambda d: d.Modelo.map(LABELS))
    rank10.to_csv(OUT / 'friedman_u10.csv', index=False, encoding='utf-8')
    indices = bootstrap_indices(5)
    mcs10 = mcs_range(mse_fold[names10].rename(columns=LABELS), indices, alpha=ALPHA_MCS)
    mcs10.to_csv(OUT / 'mcs_u10.csv', index=False, encoding='utf-8')
    cd_figure(rank10, cd10, IMAGES / 'cd_u10.png', set(ORIGINAL.values()))

    # Universo complementario de 16: los 15 del dashboard + Decision Tree (sus OOF ya existen).
    dash = pd.read_csv(DASH / 'data' / 'originales' / 'folds.csv')
    fifteen = pd.read_csv(OLD_BOOK / 'analisis_originales' / 'salidas' / 'stats_mcs.csv').Modelo.tolist()
    dash = dash.loc[dash.Modelo.isin(fifteen), ['Modelo', 'Fold', 'RMSE']]
    dt = folds.loc[folds.clave.eq('decision_tree'), ['Fold', 'RMSE']].assign(Modelo='Decision Tree')
    u16 = pd.concat([dash, dt])
    names16 = [*fifteen, 'Decision Tree']
    fr16 = friedman_comparison(u16, names16)
    q16, cd16 = critical_difference(len(names16), 5)
    mcs16 = mcs_range(u16.pivot(index='Fold', columns='Modelo', values='RMSE')[names16] ** 2, indices, alpha=ALPHA_MCS)
    mcs16.to_csv(OUT / 'mcs_u16.csv', index=False, encoding='utf-8')

    mean10 = fr10['ranking'].set_index('Modelo')['Rango promedio']
    global_rows = [
        {'Prueba': 'Friedman (universo de 10)', 'H0': 'Rangos promedio iguales en los 10 modelos', 'Estadístico': fr10['statistic'],
         'gl': fr10['df'], 'p crudo': fr10['pvalue'], 'Comparaciones': 1},
        {'Prueba': 'Friedman (universo de 16)', 'H0': 'Rangos promedio iguales en los 16 modelos', 'Estadístico': fr16['statistic'],
         'gl': fr16['df'], 'p crudo': fr16['pvalue'], 'Comparaciones': 1},
    ]
    nemenyi_rows = []
    for o, b in product(ORIGINAL, BASE):
        diff = float(mean10[o] - mean10[b])
        nemenyi_rows.append({'Original': ORIGINAL[o], 'Base': BASE[b], 'Rango original': float(mean10[o]),
                             'Rango base': float(mean10[b]), 'Δ rango': diff, 'CD': cd10,
                             'Supera la CD': abs(diff) > cd10})
    pd.DataFrame(nemenyi_rows).to_csv(OUT / 'nemenyi_u10_pares.csv', index=False, encoding='utf-8')
    pd.DataFrame(global_rows).to_csv(OUT / 'pruebas_r3_globales.csv', index=False, encoding='utf-8')

    # ---------------------------------------------------- resumen y veredicto
    from tabla_mejores_combinaciones import build as base_table
    base = base_table().set_index('Clave')
    hpo = pd.read_csv(OLD_BOOK / 'analisis_originales' / 'salidas' / 'hpo_resumen.csv')
    tim = pd.read_csv(OLD_BOOK / 'analisis_originales' / 'salidas' / 'tiempos_refit_inferencia.csv').set_index('Clave')
    test_pred = pd.concat([pd.read_csv(DASH / 'data' / 'clasicos' / 'test_predictions.csv.gz')[list(BASE)],
                           pd.read_csv(DASH / 'data' / 'originales' / 'test.csv.gz')[list(ORIGINAL)]], axis=1)
    summary = []
    for key, label in LABELS.items():
        f = folds.loc[folds.clave.eq(key)]
        s_o, n, _ = sums[key]
        boot = np.random.default_rng(SEED).integers(0, len(n), (REPS, len(n)))
        boot_rmse = np.sqrt(s_o[boot].sum(1) / n[boot].sum(1))
        if key in BASE:
            search, refit, infer = (base.loc[key, 'Búsqueda final, 5 estrategias (s)'], base.loc[key, 'Refit final (s)'],
                                    base.loc[key, 'Inferencia test, 188 filas (s)'])
            method = base.loc[key, 'Método ganador (búsqueda final)']
        else:
            h = hpo.loc[hpo.Clave.eq(key)]
            search, refit, infer = h['Búsqueda final (s)'].sum(), tim.loc[key, 'Refit final (s)'], tim.loc[key, 'Inferencia test 188 filas (s)']
            method = h.loc[h.Elegido, 'Método'].iloc[0]
        summary.append({'Modelo': label, 'Clave': key, 'Tipo': 'Original' if key in ORIGINAL else 'Base',
                        'Método final': method,
                        'RMSE externo media': f.RMSE.mean(), 'RMSE externo DE': f.RMSE.std(ddof=1),
                        'MAE externo media': f.MAE.mean(), 'MAE externo DE': f.MAE.std(ddof=1),
                        'RMSE OOF reunido': rmse(y, oof[key]),
                        'IC 95 % RMSE OOF (bootstrap estudiantes) inf': float(np.quantile(boot_rmse, .025)),
                        'IC 95 % RMSE OOF (bootstrap estudiantes) sup': float(np.quantile(boot_rmse, .975)),
                        'RMSE test 202530 (descriptivo)': rmse(test[TARGET], test_pred[key]),
                        'Búsqueda final (s)': float(search), 'Refit final (s)': float(refit),
                        'Inferencia test 188 filas (s)': float(infer),
                        'Rango Friedman (U10)': float(mean10[key]),
                        'p MCS (U10)': float(mcs10.set_index('Modelo').loc[label, 'p-valor MCS exploratorio']),
                        'En MCS (U10, α = 0,10)': mcs10.set_index('Modelo').loc[label, 'En MCS exploratorio (α = 0.10)']})
    summary = pd.DataFrame(summary).sort_values('RMSE externo media', kind='stable')
    summary.to_csv(OUT / 'resumen_modelos.csv', index=False, encoding='utf-8')

    best_base_rmse = summary.loc[summary.Tipo.eq('Base'), 'RMSE externo media'].min()
    mean_rmse = summary.set_index('Clave')['RMSE externo media']
    mcs_tab = mcs10.set_index('Modelo')
    nem = pd.DataFrame(nemenyi_rows)
    verdict = []
    # Superioridad estadísticamente verificada (R3) frente al mejor benchmark (XGBoost) y frente al
    # SVM lineal, la referencia histórica del proyecto. Mismas condiciones C1–C3 de §6.1 para ambas.
    for ref, (o, label) in product([BEST_BENCHMARK, 'svm'], ORIGINAL.items()):
        t = tests.loc[tests.clave_original.eq(o)]
        vs = t.loc[t.clave_base.eq(ref)]
        better = vs['Δ RMSE OOF reunido'] < 0
        favorable = vs.loc[vs['Rechaza H0 (Holm 21, α = 0,05)'] & better, 'Prueba'].tolist()
        strict = vs.loc[vs['Rechaza H0 (Holm global 105)'] & better, 'Prueba'].tolist()
        bh = vs.loc[(vs['p BH global (105)'] < ALPHA) & better, 'Prueba'].tolist()
        if nem.loc[nem.Original.eq(label) & nem.Base.eq(BASE[ref]), 'Supera la CD'].item():
            favorable.append('Nemenyi (U10)')
        if (mcs_tab.loc[label, 'En MCS exploratorio (α = 0.10)'] == 'Sí'
                and mcs_tab.loc[BASE[ref], 'p-valor MCS exploratorio'] < ALPHA_MCS):
            for group in (favorable, strict, bh):
                group.append('MCS (U10)')
        eff = vs.iloc[0]
        c1 = bool(mean_rmse[o] < mean_rmse[ref])
        c3 = bool(abs(eff['Delta de Cliff (MSE por fold)']) >= .147 or abs(eff['d_z de Cohen (MSE por fold)']) >= .2)
        verdict.append({'Original': label, 'Referencia': BASE[ref],
                        'RMSE medio original': mean_rmse[o], 'RMSE medio referencia': mean_rmse[ref],
                        'Menor RMSE medio que los 7 base': bool(mean_rmse[o] < best_base_rmse),
                        'C1 · menor RMSE medio que la referencia': c1,
                        'C2 · pruebas favorables (Holm por prueba)': len(favorable),
                        'Pruebas favorables (Holm por prueba)': '; '.join(favorable) or 'Ninguna',
                        'C3 · efecto no despreciable': c3,
                        'δ Cliff': eff['Delta de Cliff (MSE por fold)'], 'd_z': eff['d_z de Cohen (MSE por fold)'],
                        'Superioridad (Holm por prueba)': 'Sí' if c1 and len(favorable) >= 3 and c3 else 'No',
                        'Pruebas favorables (Holm global)': '; '.join(strict) or 'Ninguna',
                        'Superioridad (Holm global)': 'Sí' if c1 and len(strict) >= 3 and c3 else 'No',
                        'Pruebas favorables (BH global)': '; '.join(bh) or 'Ninguna',
                        'Superioridad (BH global)': 'Sí' if c1 and len(bh) >= 3 and c3 else 'No'})
    # Complemento descriptivo en el test temporal 202530 (188 estudiantes): mismo contraste DM-HLN.
    test_rows = []
    for o, b in product(ORIGINAL, ['xgboost', 'svm']):
        dm = clustered_test((test[TARGET] - test_pred[b]) ** 2, (test[TARGET] - test_pred[o]) ** 2, test['estudiante'].to_numpy())
        test_rows.append({'Original': ORIGINAL[o], 'Base': BASE[b], 'Δ RMSE test': dm['delta_rmse'],
                          'IC 95 % inf (percentil, estudiantes)': dm['ic_low'], 'IC 95 % sup': dm['ic_high'],
                          'p crudo HLN': dm['p_hln']})
    test_rows = pd.DataFrame(test_rows)
    test_rows['p Holm (6)'] = multipletests(test_rows['p crudo HLN'], method='holm')[1]
    test_rows.to_csv(OUT / 'pruebas_r3_test.csv', index=False, encoding='utf-8')
    pd.DataFrame(verdict).to_csv(OUT / 'veredicto_r3.csv', index=False, encoding='utf-8')

    # ---------------------------------------------------- ablación con resultados existentes
    gpr = gpr_solo_oof(train)
    assert (gpr['fold'].to_numpy() == oof['fold'].to_numpy()).all()
    abl = []
    for name, pred, ref in [('GPR solo (ejecución histórica gpr_xgb, 1 reinicio)', gpr['gpr_solo_prediccion'], 'm15'),
                            ('XGBoost solo (clásico)', oof['xgboost'], 'm15'),
                            ('TN-KRR (solver truncado, sin centrar)', oof['m19'], 'm5')]:
        so, n, _ = student_sums(y, pred, groups)
        sr, _, _ = student_sums(y, oof[ref], groups)
        per_fold = [rmse(y[oof.fold == f], np.asarray(pred)[oof.fold == f]) for f in range(1, 6)]
        point, low, high, p, _, _ = bca_test(sr, so, n)
        perm_d, perm_p = permutation_test(sr, so, n)
        abl.append({'Comparación': f'{LABELS[ref]} − {name}', 'Variante': name, 'Modelo completo': LABELS[ref],
                    'RMSE medio CV variante': float(np.mean(per_fold)), 'DE variante': float(np.std(per_fold, ddof=1)),
                    'RMSE medio CV completo': float(rmse_fold[ref].mean()),
                    'Δ RMSE OOF (completo − variante)': point, 'IC 95 % BCa inf': low, 'IC 95 % BCa sup': high,
                    'p BCa': p, 'p permutación': perm_p})
    pd.DataFrame(abl).to_csv(OUT / 'ablacion.csv', index=False, encoding='utf-8')

    meta = {'n_registros': int(len(y)), 'n_estudiantes': int(len(n_students)), 'folds': 5,
            'ratio_nval_nfit_estudiantes': ratio, 'replicas_bootstrap_y_permutacion': REPS, 'semilla': SEED,
            'familias': {'por_prueba': 21, 'global_por_pares': int(len(tests))},
            'friedman_u10': {k: fr10[k] for k in ('statistic', 'pvalue', 'df')}, 'nemenyi_u10': {'q': q10, 'cd': cd10},
            'friedman_u16': {k: fr16[k] for k in ('statistic', 'pvalue', 'df')}, 'nemenyi_u16': {'q': q16, 'cd': cd16},
            'mejor_benchmark': BASE[BEST_BENCHMARK],
            'wilcoxon_p_minimo_bilateral_n5': 2 / 2 ** 5}
    (OUT / 'pruebas_r3_meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf-8')
    print(pd.DataFrame(verdict)[['Original', 'Referencia', 'Pruebas favorables (Holm por prueba)', 'Superioridad (Holm por prueba)', 'Superioridad (Holm global)', 'Superioridad (BH global)']].to_string())


if __name__ == '__main__':
    main()

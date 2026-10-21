"""Tablas y figuras del capítulo «Modelos originales» del Book.

Lee la ejecución activa de Originales (``20261020_153034_consolidada``) tal como
la sirve el dashboard (``Dash/data/originales``) y su evidencia en
``Precalculo/resultados/e3/originales_busquedas/``. No reentrena ningún modelo
ni modifica ``resultados/``. Escribe tablas en ``salidas/`` y figuras PNG en
``../images/originales/``.

La única inferencia nueva es la predicción *in-sample* en train de los pipelines
finales guardados (para el RMSE de entrenamiento); se mide con perf_counter y
queda en ``TIEMPOS_EJECUCION.md`` mediante ``Dash/model_timing.TimingRun``. Los
diagnósticos de residuos, las curvas de convergencia, el estudio del tiempo y
las tablas estadísticas se calculan sobre predicciones y registros ya
guardados (no son ejecuciones de modelos).

Uso:  Precalculo\\venv\\Scripts\\python.exe -X utf8 jbook_dashboard\\analisis_originales\\generar_originales.py [--sin-inferencia]
"""
import json
import sys
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path[:0] = [str(ROOT / 'Precalculo'), str(ROOT / 'Dash')]

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.diagnostic import het_breuschpagan
from threadpoolctl import threadpool_limits

from entregable3 import FEATURES, NUMERIC, TARGET, load_partitions, metrics
from busquedas_hiperparametros_e3 import METHODS
from model_timing import TimingRun, file_hash
from residual_diagnostics import residual_diagnostics

DATA = ROOT / 'Dash/data/originales'
RUN = ROOT / 'Precalculo/resultados/e3/originales_busquedas/20261020_153034_consolidada'
TIEMPOS = ROOT / 'tiempos'
OUT = HERE / 'salidas'
IMAGES = HERE.parent / 'images' / 'originales'
CATALOG = json.loads((DATA / 'catalog.json').read_text(encoding='utf-8'))
ANALYSIS = json.loads((DATA / 'analysis.json').read_text(encoding='utf-8'))
ACTIVE = json.loads((DATA / 'active.json').read_text(encoding='utf-8'))

# Los nueve modelos originales (implementaciones propias o adaptaciones) en el orden del informe.
KEYS = ['m0', 'm5', 'm19', 'm11', 'm7', 'm3', 'm14', 'm15', 'm16']
REFERENCE = 'svm'
NAMES = {k: CATALOG[k]['name'] for k in [REFERENCE, *KEYS]}
SHORT = {'svm': 'SVM lineal', 'm0': 'SVR RBF', 'm5': 'Kernel Ridge RBF', 'm19': 'TR-KRR RBF',
         'm11': 'DenseWeight-XGB', 'm7': 'TCR-XGBoost', 'm3': 'LinXGBoost', 'm14': 'logicDT adaptado',
         'm15': 'GPR–XGBoost', 'm16': 'RIM'}
ALL = [REFERENCE, *KEYS]
# Colores estables por modelo (paleta del dashboard) y marcadores como codificación secundaria.
PALETTE = ['#435568', '#5268b9', '#187b80', '#3f925f', '#bc9028', '#db7355', '#a573b3', '#e34948', '#6250d6', '#8a8a84']
COLORS = dict(zip(ALL, PALETTE))
MARKERS = dict(zip(ALL, ['o', 's', 'D', '^', 'v', 'P', 'X', '<', '>', 'h']))
METHOD_COLORS = dict(zip(METHODS, ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4']))
METHOD_SHORT = dict(zip(METHODS, ['Grid', 'Random', 'TPE', 'DEAP', 'Halving']))
SPLIT_COLORS = {'Entrenamiento': '#2a78d6', 'Validación (OOF)': '#eb6834', 'Prueba (test 202530)': '#1baf7a'}
INK, MUTED, GRID = '#2b2b2b', '#6b6b6b', '#e4e4e0'
LABELS = {'Icfes_nuevo': 'Saber 11 · global', 'Icfes_Matematicas': 'Saber 11 · matemáticas',
          'Dominio_Inicial': 'Dominio inicial', 'Dominio_Final': 'Dominio final',
          'avance_precalculo_aleks': 'Avance en ALEK', 'Tiempo_Total_Tiempo': 'Tiempo de trabajo',
          'Tiempo_total_Aprendidos_hora': 'Temas por hora',
          'Tiempo_empleado_en_la_verificación_de_conocimientos': 'Tiempo de pretest',
          'programa_en_matricula': 'Programa', 'Mat_Curso_Asignatura_Relacionada': 'Asignatura',
          'cumplimiento_temas': 'Cumplimiento de la meta', 'Categoria_temas_inicial': 'Cat. temas iniciales',
          'Categoria_temas_final': 'Cat. temas finales', 'division_en_matricula': 'División académica',
          'avance_cuartiles': 'Avance por cuartiles'}
DIVERGING = LinearSegmentedColormap.from_list('azul_gris_rojo', ['#2a78d6', '#c9c9c4', '#e34948'])

plt.rcParams.update({'font.size': 9, 'axes.edgecolor': '#bdbdb8', 'axes.labelcolor': INK,
                     'xtick.color': MUTED, 'ytick.color': MUTED, 'axes.titlecolor': INK,
                     'axes.titlesize': 10, 'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': .6,
                     'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 110,
                     'savefig.dpi': 150, 'savefig.bbox': 'tight', 'legend.frameon': False})


def save(fig, name):
    fig.savefig(IMAGES / name, facecolor='white')
    plt.close(fig)


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


# ---------------------------------------------------------------- búsqueda
def search_tables():
    rows, choices, anytime, evolution = [], [], [], []
    for key in KEYS:
        name = SHORT[key]
        outer_seconds, outer_fits, outer_evals = {}, {}, {}
        for outer in [f'external_{i}' for i in range(1, 6)] + ['final']:
            selection = json.loads((RUN / f'selection_{key}_{outer}.json').read_text(encoding='utf-8'))
            trials = read_jsonl(RUN / selection['trials_file'])
            choices.append({'Modelo': name, 'Búsqueda': outer, 'Método elegido': selection['selected_method'],
                            'RMSE interno': selection['selection_rmse']})
            for method in [m['method'] for m in selection['methods']]:
                block = [t for t in trials if t['method'] == method]
                best, cost, clock = np.inf, 0., 0.
                for i, trial in enumerate(block, 1):
                    cost += trial['fidelity']
                    clock += trial['seconds']
                    if trial['fidelity'] == 1 and trial['RMSE'] is not None:
                        best = min(best, trial['RMSE'])
                    anytime.append({'Modelo': name, 'Búsqueda': outer, 'Método': method, 't': i,
                                    'costo_equivalente': cost, 'segundos_acumulados': clock,
                                    'fidelidad': trial['fidelity'], 'RMSE': trial['RMSE'],
                                    'mejor_hasta_t': best if np.isfinite(best) else np.nan})
            for summary in selection['methods']:
                method = summary['method']
                if outer != 'final':
                    outer_seconds[method] = outer_seconds.get(method, 0.) + summary['search_seconds']
                    continue
                block = [t for t in trials if t['method'] == method]
                fits = [f for t in block for f in t['inner_folds']]
                rows.append({'Modelo': name, 'Clave': key, 'Método': method,
                             'RMSE interno': summary['RMSE'], 'SD interna': summary['sd_RMSE'],
                             'Evaluaciones': summary['evaluated_configurations'],
                             'Al 100 %': summary['full_configurations'],
                             'Ajustes internos': summary['completed_fits'], 'Fallidos': summary['failed_fits'],
                             'Costo equivalente': sum(t['fidelity'] for t in block),
                             'Búsqueda final (s)': summary['search_seconds'],
                             's por evaluación': summary['search_seconds'] / summary['evaluated_configurations'],
                             'fit interno medio (s)': float(np.mean([f['fit_seconds'] for f in fits])),
                             'Parámetros': json.dumps(summary['best_params'], ensure_ascii=False)})
            if outer == 'final':
                for g in selection.get('evolution') or []:
                    evolution.append({'Modelo': name, **g})
        for row in rows:
            if row['Modelo'] == name:
                row['5 búsquedas externas (s)'] = outer_seconds.get(row['Método'], np.nan)
    table = pd.DataFrame(rows)
    table['Elegido'] = False
    for key in KEYS:
        selected = json.loads((RUN / f'selection_{key}_final.json').read_text(encoding='utf-8'))['selected_method']
        table.loc[table.Clave.eq(key) & table['Método'].eq(selected), 'Elegido'] = True
    best = table.groupby('Modelo')['RMSE interno'].transform('min')
    table['Brecha vs mejor (×10⁻³)'] = 1000 * (table['RMSE interno'] - best)
    return table, pd.DataFrame(choices), pd.DataFrame(anytime), pd.DataFrame(evolution)


def panel_grid(n):
    fig, axes = plt.subplots(3, 3, figsize=(13, 8.6))
    return fig, axes.flat


def plot_anytime(anytime, x, name, xlabel):
    final = anytime.loc[anytime['Búsqueda'].eq('final')]
    fig, axes = panel_grid(len(KEYS))
    for ax, key in zip(axes, KEYS):
        model = final.loc[final.Modelo.eq(SHORT[key])]
        for method in METHODS:
            block = model.loc[model['Método'].eq(method)].dropna(subset=['mejor_hasta_t'])
            if block.empty:
                continue
            ax.step(block[x], block['mejor_hasta_t'], where='post', color=METHOD_COLORS[method], lw=2, label=METHOD_SHORT[method])
            ax.plot(block[x].iloc[-1:], block['mejor_hasta_t'].iloc[-1:], 'o', ms=5, color=METHOD_COLORS[method])
        values = model['mejor_hasta_t'].dropna()
        low = values.min()
        ax.set_ylim(low - .002, min(values.quantile(.97), low + .06) + .002)
        if x == 'segundos_acumulados':
            ax.set_xscale('log')
        ax.set_title(SHORT[key])
        ax.set_xlabel(xlabel)
        ax.set_ylabel('Mejor RMSE interno hasta t')
    handles, labels = axes_legend(fig)
    fig.legend(handles, labels, loc='lower center', ncol=5, title='Estrategia', bbox_to_anchor=(.5, -.03))
    fig.suptitle('Desempeño en cualquier momento · búsqueda final en todo train', x=.01, ha='left', fontsize=12)
    fig.tight_layout()
    save(fig, name)


def axes_legend(fig):
    entries = {}
    for ax in fig.axes:
        for h, l in zip(*ax.get_legend_handles_labels()):
            entries.setdefault(l, h)
    return list(entries.values()), list(entries.keys())


def plot_convergence(anytime):
    fig, axes = panel_grid(len(KEYS))
    for ax, key in zip(axes, KEYS):
        model = anytime.loc[anytime.Modelo.eq(SHORT[key])]
        if not model['Método'].eq(METHODS[0]).any():
            ax.text(.5, .5, 'Solo TPE (40 ensayos)\nsin Grid de referencia', ha='center', va='center', transform=ax.transAxes, color=MUTED)
            ax.set_title(SHORT[key])
            ax.grid(False)
            continue
        for outer, block in model.groupby('Búsqueda'):
            grid_best = block.loc[block['Método'].eq(METHODS[0]), 'RMSE'].min()
            for method in ['Bayesiana TPE', 'Genética DEAP']:
                curve = block.loc[block['Método'].eq(method)]
                final = outer == 'final'
                ax.plot(curve.t, 1000 * (curve.mejor_hasta_t - grid_best), color=METHOD_COLORS[method],
                        lw=2.2 if final else .9, alpha=1 if final else .45,
                        label=METHOD_SHORT[method] + (' · final' if final else ' · folds externos'))
        ax.axhline(0, color=MUTED, lw=1, ls='--')
        ax.set_title(SHORT[key])
        ax.set_xlabel('Evaluación t')
        ax.set_ylabel('Mejor RMSE − mejor Grid (×10⁻³)')
        ax.set_ylim(-10, 30)
    handles, labels = axes_legend(fig)
    fig.legend(handles, labels, loc='lower center', ncol=4, bbox_to_anchor=(.5, -.03), title='Línea discontinua = mejor Grid')
    fig.suptitle('Convergencia de TPE y DEAP frente al mejor punto del Grid de la misma búsqueda', x=.01, ha='left', fontsize=12)
    fig.tight_layout()
    save(fig, 'hpo_convergencia_tpe_deap.png')


def plot_deap(evolution):
    keys = [k for k in KEYS if SHORT[k] in set(evolution.Modelo)]
    fig, axes = plt.subplots(2, len(keys), figsize=(2.3 * len(keys) + 1, 4.8), sharex=True)
    for j, key in enumerate(keys):
        block = evolution.loc[evolution.Modelo.eq(SHORT[key])]
        ax = axes[0, j]
        ax.plot(block.generation, block.best_RMSE, '-o', color=METHOD_COLORS['Genética DEAP'], lw=2, ms=4, label='Mejor')
        ax.plot(block.generation, block.mean_RMSE, '--s', color=MUTED, lw=1.4, ms=3, label='Media población')
        ax.set_title(SHORT[key], fontsize=9)
        if j == 0:
            ax.set_ylabel('RMSE interno')
            ax.legend(fontsize=7)
        ax = axes[1, j]
        ax.plot(block.generation, block.unique_fraction, '-o', color='#6250d6', lw=2, ms=4, label='Fracción única')
        ax.plot(block.generation, block.gene_entropy, '-^', color='#1baf7a', lw=2, ms=4, label='Entropía genética')
        ax.set_ylim(-.05, 1.05)
        ax.set_xlabel('Generación')
        if j == 0:
            ax.set_ylabel('Diversidad (0–1)')
            ax.legend(fontsize=7)
    fig.suptitle('DEAP · fitness y diversidad por generación (búsqueda final)', x=.01, ha='left', fontsize=12)
    fig.tight_layout()
    save(fig, 'hpo_deap_generaciones.png')


def plot_search_time(table):
    fig, ax = plt.subplots(figsize=(11, 3.9))
    x = np.arange(len(KEYS))
    width = .16
    for i, method in enumerate(METHODS):
        values = []
        for k in KEYS:
            v = table.loc[table.Clave.eq(k) & table['Método'].eq(method), 'Búsqueda final (s)']
            values.append(v.iloc[0] if len(v) else np.nan)
        ax.bar(x + (i - 2) * width, values, width * .9, color=METHOD_COLORS[method], label=METHOD_SHORT[method])
    ax.set_yscale('log')
    ax.set_xticks(x, [SHORT[k] for k in KEYS], rotation=15)
    ax.set_ylabel('Segundos de pared (escala log)')
    ax.legend(ncol=5, loc='upper left', fontsize=9)
    ax.set_title('Tiempo de la búsqueda final por estrategia (CPU, 4 procesos por evaluación)', loc='left')
    save(fig, 'hpo_tiempos.png')


def timing_events():
    """Refit final, refits externos e inferencia (OOF y test) de cada modelo, desde los eventos ya registrados."""
    rows = []
    for key in KEYS:
        run = CATALOG[key]['timing_run_id']
        events = read_jsonl(TIEMPOS / run / 'eventos.jsonl')
        mine = [e for e in events if e['batch'].startswith(key + ' /')]
        pick = lambda stage, suffix: [e for e in mine if e['stage'] == stage and e['batch'].endswith(suffix)]
        refit_ext = sum(e['seconds'] for e in mine if e['stage'] == 'Entrenamiento/refit' and '/ externo' in e['batch'])
        rows.append({'Modelo': SHORT[key], 'Clave': key, 'Ejecución de tiempos': run,
                     'Refit final (s)': pick('Entrenamiento/refit', '/ final')[0]['seconds'],
                     'Refits externos, suma de 5 (s)': refit_ext,
                     'Inferencia OOF, suma de 5 lotes (s)': sum(e['seconds'] for e in mine if e['stage'] == 'Inferencia' and 'OOF' in e['batch']),
                     'Inferencia test 188 filas (s)': pick('Inferencia', 'test202530')[0]['seconds']})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- evaluación
def load_models():
    paths = {k: RUN / f'{k}.joblib' for k in KEYS}
    paths[REFERENCE] = ROOT / 'Precalculo/resultados/e3/busquedas/20261018_102325_af643f83/model.joblib'
    import joblib
    return {k: joblib.load(p) for k, p in paths.items()}, {k: file_hash(p) for k, p in paths.items()}


def evaluation(models, train, test, oof, test_pred, folds, timing, saved_train_pred=None):
    train_pred, records, diagnostics = dict(saved_train_pred or {}), [], []
    for key in ALL:
        name = SHORT[key]
        if models is not None:
            with threadpool_limits(limits=1):
                with timing.measure('Inferencia', f'{key} / train completo in-sample', len(train), model=key,
                                    repetitions=1, warmup=0, scope='predict del pipeline final; excluye carga'):
                    train_pred[key] = np.asarray(models[key].predict(train[FEATURES]), dtype=float)
                with timing.measure('Inferencia', f'{key} / test verificación', len(test), model=key, repetitions=1, warmup=0):
                    check = np.asarray(models[key].predict(test[FEATURES]), dtype=float)
            gap = float(np.abs(check - test_pred[key]).max())
            print(f'{key}: brecha máxima test guardado vs recalculado {gap:.2e}', flush=True)
            assert gap < 1e-4, (key, gap)
        model_folds = folds.loc[folds.Modelo.eq(NAMES[key])]
        parts = {'Entrenamiento': (train[TARGET], train_pred.get(key)), 'Validación (OOF)': (train[TARGET], oof[key]),
                 'Prueba (test 202530)': (test[TARGET], test_pred[key])}
        for part, (truth, pred) in parts.items():
            if pred is None:
                continue
            row = {'Modelo': name, 'Clave': key, 'Conjunto': part, 'n': len(truth), **metrics(truth, pred)}
            if part == 'Validación (OOF)':
                for metric in ['RMSE', 'MAE', 'MAPE (%)', 'R²']:
                    row[metric + ' media folds'] = model_folds[metric].mean()
                    row[metric + ' SD folds'] = model_folds[metric].std(ddof=1)
            records.append(row)
            if part == 'Entrenamiento':
                continue
            frame = (train if part.startswith('Valid') else test)[NUMERIC].copy()
            frame['y'], frame['p'] = np.asarray(truth), pred
            result = residual_diagnostics(frame, 'y', 'p', NUMERIC)
            residual = np.asarray(truth) - pred
            diagnostics.append({'Modelo': name, 'Clave': key, 'Conjunto': part, 'n': len(truth),
                                'RMSE': row['RMSE'], 'MAE': row['MAE'], 'Residuo medio': residual.mean(),
                                'White p': result['white_p'], 'White LM': result['white_lm'], 'White gl': result['white_df'],
                                'BDS p': result['bds_p'], 'BDS estadístico': result['bds_stat'],
                                'Normalidad p (D’Agostino)': stats.normaltest(residual).pvalue,
                                'Breusch–Pagan p': het_breuschpagan(residual, sm.add_constant(pred))[3],
                                'Spearman |e| vs ŷ': stats.spearmanr(np.abs(residual), pred).statistic,
                                'Asimetría': stats.skew(residual), 'Curtosis exceso': stats.kurtosis(residual),
                                'Fuera de [0,5]': int(((pred < 0) | (pred > 5)).sum()),
                                'Mín. predicción': float(pred.min()), 'Máx. predicción': float(pred.max())})
    return train_pred, pd.DataFrame(records), pd.DataFrame(diagnostics)


def binned_mean(x, y, bins=10):
    edges = np.quantile(x, np.linspace(0, 1, bins + 1))
    index = np.clip(np.searchsorted(edges, x, side='right') - 1, 0, bins - 1)
    present = [b for b in range(bins) if (index == b).any()]
    return np.array([x[index == b].mean() for b in present]), np.array([y[index == b].mean() for b in present])


def plot_model_fit(key, train, test, train_pred, oof, test_pred, scores):
    name = SHORT[key]
    parts = [('Entrenamiento', train[TARGET].to_numpy(), train_pred[key]),
             ('Validación (OOF)', train[TARGET].to_numpy(), oof[key]),
             ('Prueba (test 202530)', test[TARGET].to_numpy(), test_pred[key])]
    fig, axes = plt.subplots(2, 3, figsize=(12.5, 7.2))
    for j, (part, truth, pred) in enumerate(parts):
        color = SPLIT_COLORS[part]
        score = scores.loc[scores.Clave.eq(key) & scores.Conjunto.eq(part)].iloc[0]
        ax = axes[0, j]
        ax.scatter(truth, pred, s=12, color=color, alpha=.45, edgecolors='white', linewidths=.3)
        ax.plot([0, 5], [0, 5], color=MUTED, ls='--', lw=1)
        ax.set_xlim(-.1, 5.2)
        ax.set_ylim(min(-.1, pred.min() - .1), max(5.2, pred.max() + .1))
        ax.set_title(f'{part} · n = {len(truth)}')
        ax.set_xlabel('Nota real')
        ax.set_ylabel('Nota predicha')
        ax.text(.03, .97, f'RMSE {score.RMSE:.4f}\nMAE {score.MAE:.4f}\nR² {score["R²"]:.4f}', transform=ax.transAxes,
                va='top', fontsize=9, color=INK, bbox={'facecolor': 'white', 'edgecolor': GRID, 'boxstyle': 'round'})
        ax = axes[1, j]
        residual = truth - pred
        ax.scatter(pred, residual, s=12, color=color, alpha=.45, edgecolors='white', linewidths=.3)
        cx, cy = binned_mean(pred, residual)
        ax.plot(cx, cy, '-o', color=INK, lw=1.8, ms=4, label='Media por decil de ŷ')
        ax.axhline(0, color=MUTED, ls='--', lw=1)
        ax.set_xlabel('Nota predicha')
        ax.set_ylabel('Residuo (real − predicha)')
        if j == 0:
            ax.legend(loc='lower left', fontsize=8)
    fig.suptitle(f'{name} · predicciones y residuos en entrenamiento, validación externa y prueba', x=.01, ha='left', fontsize=12)
    fig.tight_layout()
    save(fig, f'eval_{key}.png')


def plot_metric_overview(scores):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    val = scores.loc[scores.Conjunto.eq('Validación (OOF)')].sort_values('RMSE media folds')
    order = val.Clave.tolist()
    for ax, metric in zip(axes, ['RMSE', 'MAE']):
        for i, part in enumerate(SPLIT_COLORS):
            block = scores.loc[scores.Conjunto.eq(part)].set_index('Clave').loc[order]
            y = np.arange(len(order)) + (i - 1) * .26
            value = block[metric + ' media folds'] if part.startswith('Valid') else block[metric]
            ax.barh(y, value, .24, color=SPLIT_COLORS[part], label=part)
            if part.startswith('Valid'):
                ax.errorbar(value, y, xerr=block[metric + ' SD folds'], fmt='none', ecolor=INK, lw=1, capsize=2)
        ax.set_yticks(np.arange(len(order)), [SHORT[k] for k in order])
        ax.invert_yaxis()
        ax.set_xlim(0, None)
        ax.set_xlabel(f'{metric} (puntos de nota) · validación = media ± SD de 5 folds')
        ax.set_title(metric, loc='left')
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', ncol=3, bbox_to_anchor=(.5, 1.05))
    fig.tight_layout()
    save(fig, 'eval_resumen_rmse_mae.png')


# ---------------------------------------------------------------- SHAP / LIME del líder (explanations.json)
def feature_short(value):
    if isinstance(value, float):
        return f'{value:.1f}' if np.isfinite(value) else 'faltante'
    text = str(value)
    return text if len(text) <= 22 else text[:20] + '…'


def leader_shap(test):
    """Figura y tablas a partir de las explicaciones SHAP ya guardadas del líder (sin recomputar)."""
    e = json.loads((DATA / 'explanations.json').read_text(encoding='utf-8'))
    features = e['features']
    values_all = np.asarray(e['values'], float)
    n_train, n_test = e['n_train'], e['n_test']
    values = values_all[n_train:]
    prediction = np.asarray(e['prediction'], float)
    prediction = prediction[-n_test:] if len(prediction) != n_test else prediction
    base = e['base']
    order = np.argsort(np.abs(values).mean(axis=0))[::-1]
    mean_abs = pd.Series(np.abs(values).mean(axis=0), index=[LABELS[f] for f in features])
    share = (100 * mean_abs / mean_abs.sum()).sort_values(ascending=False)
    share.to_csv(OUT / 'shap_importancia_pct_lider.csv', header=['% de |SHAP| medio'])
    truth = test[TARGET].to_numpy()
    cases = {'Menor error absoluto': int(np.argmin(np.abs(truth - prediction))), 'Mayor error absoluto': int(np.argmax(np.abs(truth - prediction)))}
    fig = plt.figure(figsize=(13, 11.5))
    grid = fig.add_gridspec(2, 2, height_ratios=[1.1, 1], wspace=.95, hspace=.32)
    ax = fig.add_subplot(grid[0, :])
    rng = np.random.default_rng(42)
    for rank, j in enumerate(order):
        feature = features[j]
        y = rank + rng.uniform(-.28, .28, len(values))
        if feature in NUMERIC:
            column = test[feature].astype(float)
            low, high = column.quantile([.05, .95])
            color = DIVERGING(np.clip((column - low) / (high - low if high > low else 1), 0, 1).fillna(.5))
        else:
            color = '#9a9a94'
        ax.scatter(values[:, j], y, s=7, c=color, alpha=.75, linewidths=0)
    ax.set_yticks(range(len(order)), [LABELS[features[j]] for j in order])
    ax.invert_yaxis()
    ax.axvline(0, color=MUTED, lw=1)
    ax.set_xlabel('Valor SHAP (puntos de nota)')
    ax.set_title('Resumen global · 188 filas de test', loc='left')
    bar = fig.colorbar(plt.cm.ScalarMappable(cmap=DIVERGING), ax=ax, fraction=.03, pad=.02, ticks=[0, 1])
    bar.ax.set_yticklabels(['Bajo', 'Alto'])
    bar.set_label('Valor numérico (gris = categórica)')
    case_rows = []
    for g, (label, position) in enumerate(cases.items(), 1):
        ax = fig.add_subplot(grid[1, g - 1])
        contrib = values[position]
        top = np.argsort(np.abs(contrib))[::-1]
        shown, rest = top[:9], top[9:]
        items = [(LABELS[features[j]] + ' = ' + feature_short(test.iloc[position][features[j]]), contrib[j]) for j in shown]
        items.append((f'{len(rest)} variables restantes', contrib[rest].sum()))
        start = base
        path = start + np.cumsum([0] + [v for _, v in items])
        marks = np.r_[path, prediction[position], truth[position]]
        span = max(marks.max() - marks.min(), .05)
        for i, (text, value) in enumerate(items):
            ax.barh(i, value, left=start, color='#1baf7a' if value >= 0 else '#e34948', height=.7)
            end = start + value
            ax.text(max(start, end) + .003 * span, i, f'{value:+.3f}', va='center', ha='left', fontsize=7.5, color=INK)
            start = end
        ax.set_xlim(marks.min() - .08 * span, marks.max() + .3 * span)
        ax.axvline(base, color=MUTED, ls=':', lw=1)
        ax.axvline(prediction[position], color=INK, lw=1.2)
        ax.axvline(truth[position], color='#6250d6', lw=1.6, ls='--')
        ax.set_yticks(np.arange(len(items)), [t for t, _ in items], fontsize=7.5)
        ax.invert_yaxis()
        ax.set_xlabel('Nota (puntos)')
        ax.set_title(f'{label} · caso test #{position + 1}\nreal {truth[position]:.2f} · predicha {prediction[position]:.2f} · base {base:.2f}',
                     loc='left', fontsize=9)
        case_rows += [{'Caso': label, 'Posición test': position + 1, 'Variable': LABELS[features[j]],
                       'Valor': test.iloc[position][features[j]], 'SHAP': contrib[j]} for j in top]
    fig.suptitle('Kernel Ridge RBF · SHAP por permutaciones antitéticas (aproximado). Punteada = base; continua = predicción; violeta = nota real',
                 x=.01, ha='left', fontsize=11)
    save(fig, 'shap_lider.png')
    pd.DataFrame(case_rows).to_csv(OUT / 'shap_casos_lider.csv', index=False)
    lime_rows = []
    for case, item in zip(e['cases'], e['lime']):
        for row in item['rows']:
            lime_rows.append({'Caso test': case + 1, **{k: v for k, v in item.items() if k != 'rows'}, **row})
    pd.DataFrame(lime_rows).to_csv(OUT / 'lime_casos_lider.csv', index=False)
    meta = {k: e[k] for k in ['method', 'background_rows', 'paths', 'half_difference_mean_abs', 'max_additivity_residual', 'cases', 'base']}
    meta['casos_posicion_test_1_based'] = {k: v + 1 for k, v in cases.items()}
    (OUT / 'shap_meta_lider.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding='utf-8')


# ---------------------------------------------------------------- robustez y estadística
def plot_robustness(folds):
    fig, ax = plt.subplots(figsize=(9, 4.3))
    for key in ALL:
        block = folds.loc[folds.Modelo.eq(NAMES[key])].sort_values('Fold')
        ax.plot(block.Fold, block.RMSE, '-' + MARKERS[key], color=COLORS[key], lw=1.6, ms=6, label=SHORT[key])
    ax.set_xticks(range(1, 6))
    ax.set_xlabel('Fold externo')
    ax.set_ylabel('RMSE de validación')
    ax.set_title('RMSE por fold: la variación entre folds domina las diferencias entre modelos', loc='left')
    ax.legend(fontsize=8, ncol=2, bbox_to_anchor=(1.01, 1), loc='upper left')
    fig.tight_layout()
    save(fig, 'robustez_folds.png')


def nemenyi_cd(k, n):
    q = stats.studentized_range.ppf(.95, k, np.inf) / np.sqrt(2)
    return q, q * np.sqrt(k * (k + 1) / (6 * n))


def plot_friedman():
    ranking = pd.DataFrame(ANALYSIS['ranking']).set_index('Modelo')
    columns = [c for c in ranking.columns if c.startswith('Rango fold')]
    ranking = ranking.sort_values('Rango promedio')
    k, n = ANALYSIS['omnibus']['n_models'], ANALYSIS['omnibus']['n_folds']
    q, cd = nemenyi_cd(k, n)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.2), gridspec_kw={'width_ratios': [1, 1.3]})
    ax = axes[0]
    ax.imshow(ranking[columns].to_numpy(), cmap=LinearSegmentedColormap.from_list('r', ['#104281', '#86b6ef', '#f4f8fd']), vmin=1, vmax=k)
    ax.set_xticks(range(len(columns)), [c.replace('Rango fold ', 'F') for c in columns])
    ax.set_yticks(range(len(ranking)), ranking.index)
    ax.grid(False)
    for i in range(len(ranking)):
        for j in range(len(columns)):
            value = ranking[columns].iat[i, j]
            ax.text(j, i, f'{value:.0f}', ha='center', va='center', color='white' if value < k / 3 else INK, fontsize=8)
    ax.set_title('Rango por fold externo (1 = mejor)', loc='left')
    ax = axes[1]
    order = ranking['Rango promedio']
    ax.set_xlim(1, k + .5)
    ax.set_ylim(-1.2, len(order) + .8)
    ax.hlines(len(order) + .2, order.iloc[0], order.iloc[0] + cd, color=INK, lw=3)
    ax.text(order.iloc[0] + cd / 2, len(order) + .45, f'CD Nemenyi (α = 0,05) = {cd:.2f}', ha='center', fontsize=9)
    originals = set(NAMES.values())
    for i, (model, rank) in enumerate(order.items()):
        y = len(order) - 1 - i
        color = '#187b80' if model in originals else '#9a9a94'
        ax.plot(rank, y, 'o', color=color, ms=8)
        ax.text(rank + .12, y, f'{model} ({rank:.1f})', va='center', fontsize=8.5)
    ax.set_yticks([])
    ax.set_xlabel('Rango promedio (menor = mejor) · verde: originales y SVM; gris: clásicos')
    om = ANALYSIS['omnibus']
    fig.suptitle(f'Friedman χ² = {om["statistic"]:.2f}, gl = {om["df"]}, p = {om["pvalue"]:.2e} · diagrama de diferencia crítica (Nemenyi)', x=.01, ha='left', fontsize=11)
    fig.tight_layout()
    save(fig, 'stats_friedman_nemenyi.png')
    return q, cd


def nemenyi_pairs(cd):
    ranking = pd.DataFrame(ANALYSIS['ranking']).set_index('Modelo')['Rango promedio']
    rows = []
    names = list(ranking.index)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            rows.append({'Modelo A': a, 'Modelo B': b, 'Δ rango (A − B)': ranking[a] - ranking[b], '|Δ| > CD': abs(ranking[a] - ranking[b]) > cd})
    return pd.DataFrame(rows)


def write_stats(q, cd):
    pd.DataFrame(ANALYSIS['ranking']).to_csv(OUT / 'stats_rangos.csv', index=False)
    pd.DataFrame(ANALYSIS['mcs']).to_csv(OUT / 'stats_mcs.csv', index=False)
    pd.DataFrame(ANALYSIS['effects']).to_csv(OUT / 'stats_efectos.csv', index=False)
    pd.DataFrame(ANALYSIS['pairs']).to_csv(OUT / 'stats_pares_finalistas.csv', index=False)
    pd.DataFrame(ANALYSIS['dm']['finalist_pairs']).to_csv(OUT / 'stats_etapa2_dm_finalistas.csv', index=False)
    pd.DataFrame(ANALYSIS['dm']['cv']).to_csv(OUT / 'stats_etapa3_dm_cv.csv', index=False)
    pd.DataFrame(ANALYSIS['dm']['test']).to_csv(OUT / 'stats_etapa3_dm_test.csv', index=False)
    pd.DataFrame(ANALYSIS['dm']['top']).to_csv(OUT / 'stats_etapa3_top_mcs.csv', index=False)
    nemenyi_pairs(cd).to_csv(OUT / 'stats_nemenyi.csv', index=False)
    (OUT / 'stats_resumen.json').write_text(json.dumps({
        'omnibus': ANALYSIS['omnibus'], 'nemenyi_q': q, 'nemenyi_cd': cd, 'analysis_run': ANALYSIS['analysis_run'],
        'dm_reps': ANALYSIS['dm']['reps'], 'dm_seed': ANALYSIS['dm']['seed'], 'finalists': ANALYSIS['finalists']},
        indent=2, ensure_ascii=False), encoding='utf-8')


def main(infer=True):
    OUT.mkdir(parents=True, exist_ok=True)
    IMAGES.mkdir(parents=True, exist_ok=True)
    train, test, _ = load_partitions()
    cached = pd.read_csv(DATA / 'train.csv.gz')
    oof_all, test_all = cached, pd.read_csv(DATA / 'test.csv.gz')
    assert len(oof_all) == len(train) and len(test_all) == len(test)
    oof = {k: oof_all[k].to_numpy() for k in ALL}
    test_pred = {k: test_all[k].to_numpy() for k in ALL}
    folds = pd.read_csv(DATA / 'folds.csv')

    table, choices, anytime, evolution = search_tables()
    table.to_csv(OUT / 'hpo_resumen.csv', index=False)
    choices.to_csv(OUT / 'hpo_metodo_por_busqueda.csv', index=False)
    anytime.to_csv(OUT / 'hpo_anytime.csv', index=False)
    evolution.to_csv(OUT / 'hpo_deap_evolucion.csv', index=False)
    timing_events().to_csv(OUT / 'tiempos_refit_inferencia.csv', index=False)
    plot_anytime(anytime, 'costo_equivalente', 'hpo_anytime_evaluaciones.png', 'Evaluaciones completas equivalentes')
    plot_anytime(anytime, 'segundos_acumulados', 'hpo_anytime_tiempo.png', 'Segundos de pared acumulados (log)')
    plot_convergence(anytime)
    plot_deap(evolution)
    plot_search_time(table)

    if infer:
        models, hashes = load_models()
        timing = TimingRun('Book · evaluación de Originales (inferencia in-sample en train)', {
            'script': 'jbook_dashboard/analisis_originales/generar_originales.py', 'script_sha256': file_hash(__file__),
            'active_run': RUN.name, 'model_sha256': hashes, 'train_rows': len(train), 'test_rows': len(test),
            'seed': 42, 'device': 'CPU', 'parallelism': '1 hilo; secuencial',
            'scope': 'Sin búsqueda ni refit. Inferencia de pipelines guardados; diagnósticos sobre predicciones ya guardadas.'})
        status = 'fallida'
        try:
            train_pred, scores, diagnostics = evaluation(models, train, test, oof, test_pred, folds, timing)
            status = 'completa'
        finally:
            timing.finish(status)
        pd.DataFrame({k: v for k, v in train_pred.items()}).to_csv(OUT / 'train_insample_predicciones.csv.gz', index=False)
        meta = {'timing_run_id': timing.run_id}
    else:
        train_pred = {k: v for k, v in pd.read_csv(OUT / 'train_insample_predicciones.csv.gz').items()}
        train_pred = {k: v.to_numpy() for k, v in train_pred.items()}
        _, scores, diagnostics = evaluation(None, train, test, oof, test_pred, folds, None, train_pred)
        meta = {'timing_run_id': 'reutilizado'}
        scores, diagnostics = scores, diagnostics
    scores.to_csv(OUT / 'eval_metricas.csv', index=False)
    diagnostics.to_csv(OUT / 'eval_diagnosticos.csv', index=False)
    for key in ALL:
        plot_model_fit(key, train, test, train_pred, oof, test_pred, scores)
    plot_metric_overview(scores)

    leader_shap(test)
    plot_robustness(folds)
    q, cd = plot_friedman()
    write_stats(q, cd)
    (OUT / 'meta.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
    print('Listo', meta, flush=True)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    warnings.filterwarnings('ignore', category=FutureWarning)
    main(infer='--sin-inferencia' not in sys.argv)

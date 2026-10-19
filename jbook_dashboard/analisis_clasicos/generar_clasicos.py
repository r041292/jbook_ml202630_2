"""Tablas y figuras del capítulo «Modelos clásicos» del Book.

Lee la ejecución activa de búsquedas (sin reentrenar los modelos canónicos) y
produce en ``salidas/`` tablas CSV/JSON y en ``../images/clasicos/`` figuras
PNG estáticas. Las inferencias nuevas (predicción in-sample en train,
verificación de test y explicaciones SHAP) se miden con perf_counter y quedan
en ``TIEMPOS_EJECUCION.md`` mediante ``Dash/model_timing.TimingRun``.

SHAP: los modelos lineales usan la fórmula exacta para modelos aditivos con
referencia intervencional; XGBoost usa TreeSHAP exacto nativo
(``pred_contribs``); KNN, Random Forest y Decision Tree usan un estimador de
permutaciones antitéticas de valores de Shapley intervencionales (aproximado).
"""
import json
import sys
import time
import warnings
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path[:0] = [str(ROOT / 'Precalculo'), str(ROOT / 'Dash')]

import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import pandas as pd
import statsmodels.api as sm
import xgboost as xgb
from scipy import stats
from statsmodels.stats.diagnostic import het_breuschpagan
from threadpoolctl import threadpool_limits

from entregable3 import FEATURES, NUMERIC, CATEGORICAL, TARGET, GROUP, load_partitions, grouped_splits, metrics
from busquedas_hiperparametros_e3 import METHODS
from model_timing import TimingRun, file_hash
from residual_diagnostics import residual_diagnostics
from classic_friedman import friedman_comparison
from classic_posthoc import analyze

RUN = ROOT / 'Precalculo/resultados/e3/busquedas/20261018_102325_af643f83'
EVIDENCE = RUN / 'evidencia'
OUT = HERE / 'salidas'
IMAGES = HERE.parent / 'images' / 'clasicos'
KEYS = ['svm', 'knn', 'ridge', 'lasso', 'forest', 'xgboost', 'decision_tree']
NAMES = {'svm': 'SVM lineal', 'knn': 'KNN', 'ridge': 'Ridge', 'lasso': 'Lasso',
         'forest': 'Random Forest', 'xgboost': 'XGBoost', 'decision_tree': 'Decision Tree'}
# Colores estables del dashboard por entidad; los marcadores dan codificación secundaria.
MODEL_COLORS = {'SVM lineal': '#435568', 'KNN': '#5268b9', 'Ridge': '#bc9028', 'Lasso': '#a573b3',
                'Random Forest': '#3f925f', 'XGBoost': '#187b80', 'Decision Tree': '#db7355'}
MARKERS = {'SVM lineal': 'o', 'KNN': 's', 'Ridge': 'D', 'Lasso': '^', 'Random Forest': 'v',
           'XGBoost': 'P', 'Decision Tree': 'X'}
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
BACKGROUND_ROWS, PERMUTATIONS = 50, 16

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
    rows, choices, anytime = [], [], []
    for key in KEYS:
        name = NAMES[key]
        outer_seconds = {m: 0. for m in METHODS}
        for outer in [f'externo_{i}' for i in range(1, 6)] + ['final_train']:
            selection = json.loads((EVIDENCE / f'selection_{key}_{outer}.json').read_text(encoding='utf-8'))
            trials = read_jsonl(EVIDENCE / f'trials_{key}_{outer}.jsonl')
            choices.append({'Modelo': name, 'Búsqueda': outer, 'Método elegido': selection['selected_method'],
                            'RMSE interno': selection['selection_rmse']})
            for method in METHODS:
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
                if outer != 'final_train':
                    outer_seconds[summary['method']] += summary['search_seconds']
                    continue
                block = [t for t in trials if t['method'] == summary['method']]
                fits = [f for t in block for f in t['inner_folds']]
                rows.append({'Modelo': name, 'Método': summary['method'],
                             'RMSE interno': summary['RMSE'], 'SD interna': summary['sd_RMSE'],
                             'Evaluaciones': summary['evaluated_configurations'],
                             'Al 100 %': summary['full_configurations'],
                             'Ajustes internos': summary['completed_fits'],
                             'Fallidos': summary['failed_fits'],
                             'Costo equivalente': sum(t['fidelity'] for t in block),
                             'Búsqueda final (s)': summary['search_seconds'],
                             's por evaluación': summary['search_seconds']/summary['evaluated_configurations'],
                             'fit interno medio (s)': float(np.mean([f['fit_seconds'] for f in fits])),
                             'Mejores parámetros': json.dumps({k.replace('modelo__', ''): v for k, v in summary['best_params'].items()})})
        for row in rows:
            if row['Modelo'] == name:
                row['5 búsquedas externas (s)'] = outer_seconds[row['Método']]
    table = pd.DataFrame(rows)
    table['Elegido'] = False
    for key in KEYS:
        selected = json.loads((EVIDENCE / f'selection_{key}_final_train.json').read_text(encoding='utf-8'))['selected_method']
        table.loc[table.Modelo.eq(NAMES[key]) & table['Método'].eq(selected), 'Elegido'] = True
    best = table.groupby('Modelo')['RMSE interno'].transform('min')
    table['Brecha vs mejor (×10⁻³)'] = 1000*(table['RMSE interno']-best)
    return table, pd.DataFrame(choices), pd.DataFrame(anytime)


def plot_anytime(anytime, x, name, xlabel):
    final = anytime.loc[anytime['Búsqueda'].eq('final_train')]
    fig, axes = plt.subplots(2, 4, figsize=(13, 6.2))
    for ax, key in zip(axes.flat, KEYS):
        model = final.loc[final.Modelo.eq(NAMES[key])]
        for method in METHODS:
            block = model.loc[model['Método'].eq(method)].dropna(subset=['mejor_hasta_t'])
            ax.step(block[x], block['mejor_hasta_t'], where='post', color=METHOD_COLORS[method],
                    lw=2, label=METHOD_SHORT[method])
            ax.plot(block[x].iloc[-1:], block['mejor_hasta_t'].iloc[-1:], 'o', ms=5, color=METHOD_COLORS[method])
        lows = model.groupby('Método')['mejor_hasta_t'].min()
        top = model.loc[model['Método'].ne(METHODS[0]), 'mejor_hasta_t'].dropna()
        ax.set_ylim(lows.min()-.002, min(top.quantile(.97), lows.min()+.06)+.002)
        if x == 'segundos_acumulados':
            ax.set_xscale('log')
        ax.set_title(NAMES[key])
        ax.set_xlabel(xlabel)
        ax.set_ylabel('Mejor RMSE interno hasta t')
    axes.flat[-1].axis('off')
    handles, labels = axes.flat[0].get_legend_handles_labels()
    axes.flat[-1].legend(handles, labels, loc='center', title='Estrategia', fontsize=10)
    fig.suptitle('Desempeño en cualquier momento · búsqueda final en todo train', x=.01, ha='left', fontsize=12)
    fig.tight_layout()
    save(fig, name)


def plot_convergence(anytime):
    fig, axes = plt.subplots(2, 4, figsize=(13, 6.2))
    for ax, key in zip(axes.flat, KEYS):
        model = anytime.loc[anytime.Modelo.eq(NAMES[key])]
        for outer, block in model.groupby('Búsqueda'):
            grid_best = block.loc[block['Método'].eq(METHODS[0]), 'RMSE'].min()
            for method in ['Bayesiana TPE', 'Genética DEAP']:
                curve = block.loc[block['Método'].eq(method)]
                final = outer == 'final_train'
                ax.plot(curve.t, 1000*(curve.mejor_hasta_t-grid_best), color=METHOD_COLORS[method],
                        lw=2.2 if final else .9, alpha=1 if final else .45,
                        label=(METHOD_SHORT[method]+(' · final' if final else ' · folds externos')))
        ax.axhline(0, color=MUTED, lw=1, ls='--')
        ax.set_title(NAMES[key])
        ax.set_xlabel('Evaluación t')
        ax.set_ylabel('Mejor RMSE − mejor Grid (×10⁻³)')
        ax.set_ylim(-6, 25)
    axes.flat[-1].axis('off')
    handles, labels = axes.flat[0].get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    axes.flat[-1].legend(unique.values(), unique.keys(), loc='center', fontsize=10,
                         title='Línea discontinua = mejor Grid')
    fig.suptitle('Convergencia de TPE y DEAP frente al mejor punto del Grid de la misma búsqueda', x=.01, ha='left', fontsize=12)
    fig.tight_layout()
    save(fig, 'hpo_convergencia_tpe_deap.png')


def plot_deap():
    fig, axes = plt.subplots(2, 7, figsize=(15, 4.8), sharex=True)
    for j, key in enumerate(KEYS):
        evolution = pd.DataFrame(json.loads((EVIDENCE / f'selection_{key}_final_train.json').read_text(encoding='utf-8'))['evolution'])
        ax = axes[0, j]
        ax.plot(evolution.generation, evolution.best_RMSE, '-o', color=METHOD_COLORS['Genética DEAP'], lw=2, ms=4, label='Mejor')
        ax.plot(evolution.generation, evolution.mean_RMSE, '--s', color=MUTED, lw=1.4, ms=3, label='Media población')
        ax.set_title(NAMES[key])
        if j == 0:
            ax.set_ylabel('RMSE interno')
            ax.legend(fontsize=8)
        ax = axes[1, j]
        ax.plot(evolution.generation, evolution.unique_fraction, '-o', color='#6250d6', lw=2, ms=4, label='Fracción única')
        ax.plot(evolution.generation, evolution.gene_entropy, '-^', color='#1baf7a', lw=2, ms=4, label='Entropía genética')
        ax.set_ylim(-.05, 1.05)
        ax.set_xlabel('Generación')
        if j == 0:
            ax.set_ylabel('Diversidad (0–1)')
            ax.legend(fontsize=8)
    fig.suptitle('DEAP · fitness y diversidad por generación (búsqueda final)', x=.01, ha='left', fontsize=12)
    fig.tight_layout()
    save(fig, 'hpo_deap_generaciones.png')


def plot_search_time(table):
    fig, ax = plt.subplots(figsize=(10, 3.8))
    width = .16
    x = np.arange(len(KEYS))
    for i, method in enumerate(METHODS):
        values = [table.loc[table.Modelo.eq(NAMES[k]) & table['Método'].eq(method), 'Búsqueda final (s)'].iloc[0] for k in KEYS]
        ax.bar(x+(i-2)*width, values, width*.9, color=METHOD_COLORS[method], label=METHOD_SHORT[method])
    ax.set_yscale('log')
    ax.set_xticks(x, [NAMES[k] for k in KEYS])
    ax.set_ylabel('Segundos de pared (escala log)')
    ax.legend(ncol=5, loc='upper left', fontsize=9)
    ax.set_title('Tiempo de la búsqueda final por estrategia (CPU, 4 procesos por evaluación)', loc='left')
    save(fig, 'hpo_tiempos.png')


# ---------------------------------------------------------------- evaluación
def load_models():
    paths = {key: RUN / ('model.joblib' if key == 'svm' else f'clasicos/{key}.joblib') for key in KEYS}
    return {key: joblib.load(path) for key, path in paths.items()}, {k: file_hash(p) for k, p in paths.items()}


def evaluation(models, train, test, oof, test_pred, folds, timing):
    train_pred, records, diagnostics = {}, [], []
    for key in KEYS:
        name = NAMES[key]
        with threadpool_limits(limits=1):
            with timing.measure('Inferencia', f'{key} / train completo in-sample', len(train), model=key,
                                repetitions=1, warmup=0, scope='predict del pipeline final; excluye carga'):
                train_pred[key] = np.asarray(models[key].predict(train[FEATURES]), dtype=float)
            with timing.measure('Inferencia', f'{key} / test verificación', len(test), model=key, repetitions=1, warmup=0):
                check = np.asarray(models[key].predict(test[FEATURES]), dtype=float)
        np.testing.assert_allclose(check, test_pred[key], atol=1e-6, rtol=0)
        model_folds = folds.loc[folds.Modelo.eq(name)]
        parts = {'Entrenamiento': (train[TARGET], train_pred[key]), 'Validación (OOF)': (train[TARGET], oof[key]),
                 'Prueba (test 202530)': (test[TARGET], test_pred[key])}
        for part, (truth, pred) in parts.items():
            score = metrics(truth, pred)
            row = {'Modelo': name, 'Conjunto': part, 'n': len(truth), **score}
            if part == 'Validación (OOF)':
                for metric in ['RMSE', 'MAE', 'MAPE (%)', 'R²']:
                    row[metric+' media folds'] = model_folds[metric].mean()
                    row[metric+' SD folds'] = model_folds[metric].std(ddof=1)
            records.append(row)
            if part == 'Entrenamiento':
                continue
            frame = (train if part.startswith('Valid') else test)[NUMERIC].copy()
            frame['y'], frame['p'] = np.asarray(truth), pred
            result = residual_diagnostics(frame, 'y', 'p', NUMERIC)
            residual = np.asarray(truth)-pred
            diagnostics.append({'Modelo': name, 'Conjunto': part, 'Residuo medio': residual.mean(),
                                'White p': result['white_p'], 'White LM': result['white_lm'], 'White gl': result['white_df'],
                                'BDS p': result['bds_p'], 'BDS estadístico': result['bds_stat'],
                                'Normalidad p (D’Agostino)': stats.normaltest(residual).pvalue,
                                'Breusch–Pagan p': het_breuschpagan(residual, sm.add_constant(pred))[3],
                                'Spearman |e| vs ŷ': stats.spearmanr(np.abs(residual), pred).statistic,
                                'Asimetría': stats.skew(residual), 'Curtosis exceso': stats.kurtosis(residual),
                                'Fuera de [0,5]': int(((pred < 0) | (pred > 5)).sum())})
    return train_pred, pd.DataFrame(records), pd.DataFrame(diagnostics)


def binned_mean(x, y, bins=10):
    edges = np.quantile(x, np.linspace(0, 1, bins+1))
    index = np.clip(np.searchsorted(edges, x, side='right')-1, 0, bins-1)
    centers = [x[index == b].mean() for b in range(bins) if (index == b).any()]
    means = [y[index == b].mean() for b in range(bins) if (index == b).any()]
    return np.array(centers), np.array(means)


def plot_model_fit(key, train, test, train_pred, oof, test_pred, scores):
    name = NAMES[key]
    parts = [('Entrenamiento', train[TARGET].to_numpy(), train_pred[key]),
             ('Validación (OOF)', train[TARGET].to_numpy(), oof[key]),
             ('Prueba (test 202530)', test[TARGET].to_numpy(), test_pred[key])]
    fig, axes = plt.subplots(2, 3, figsize=(12.5, 7.2))
    for j, (part, truth, pred) in enumerate(parts):
        color = SPLIT_COLORS[part]
        score = scores.loc[scores.Modelo.eq(name) & scores.Conjunto.eq(part)].iloc[0]
        ax = axes[0, j]
        ax.scatter(truth, pred, s=12, color=color, alpha=.45, edgecolors='white', linewidths=.3)
        ax.plot([0, 5], [0, 5], color=MUTED, ls='--', lw=1)
        ax.set_xlim(-.1, 5.2)
        ax.set_ylim(min(-.1, pred.min()-.1), max(5.2, pred.max()+.1))
        ax.set_title(f'{part} · n = {len(truth)}')
        ax.set_xlabel('Nota real')
        ax.set_ylabel('Nota predicha')
        ax.text(.03, .97, f'RMSE {score.RMSE:.4f}\nMAE {score.MAE:.4f}\nR² {score["R²"]:.4f}', transform=ax.transAxes,
                va='top', fontsize=9, color=INK, bbox={'facecolor': 'white', 'edgecolor': GRID, 'boxstyle': 'round'})
        ax = axes[1, j]
        residual = truth-pred
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
    fig, axes = plt.subplots(1, 2, figsize=(12, 3.8))
    order = scores.loc[scores.Conjunto.eq('Validación (OOF)')].sort_values('RMSE media folds').Modelo.tolist()
    for ax, metric in zip(axes, ['RMSE', 'MAE']):
        for i, part in enumerate(SPLIT_COLORS):
            block = scores.loc[scores.Conjunto.eq(part)].set_index('Modelo').loc[order]
            y = np.arange(len(order))+(i-1)*.26
            value = block[metric+' media folds'] if part.startswith('Valid') else block[metric]
            ax.barh(y, value, .24, color=SPLIT_COLORS[part], label=part)
            if part.startswith('Valid'):
                ax.errorbar(value, y, xerr=block[metric+' SD folds'], fmt='none', ecolor=INK, lw=1, capsize=2)
        ax.set_yticks(np.arange(len(order)), order)
        ax.invert_yaxis()
        ax.set_xlim(0, None)
        ax.set_xlabel(f'{metric} (puntos de nota) · validación = media ± SD de 5 folds')
        ax.set_title(metric, loc='left')
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', ncol=3, bbox_to_anchor=(.5, 1.06))
    axes[0].text(.01, list(order).index('KNN')-.26, ' KNN train = 0 (weights=distance memoriza train)', fontsize=7.5, color=MUTED, va='center')
    fig.tight_layout()
    save(fig, 'eval_resumen_rmse_mae.png')


# ---------------------------------------------------------------- SHAP
def feature_of(column):
    raw = column.split('__', 1)[1]
    return max((f for f in FEATURES if raw == f or raw.startswith(f+'_')), key=len)


def linear_shap(model, background, frame):
    prep, estimator = model.named_steps['preprocesamiento'], model.named_steps['modelo']
    z_bg, z = np.asarray(prep.transform(background), float), np.asarray(prep.transform(frame), float)
    contrib = (z-z_bg.mean(axis=0))*np.ravel(estimator.coef_)
    owner = [feature_of(c) for c in prep.get_feature_names_out()]
    values = np.column_stack([contrib[:, [o == f for o in owner]].sum(axis=1) for f in FEATURES])
    base = float(np.ravel(estimator.intercept_)[0] + z_bg.mean(axis=0) @ np.ravel(estimator.coef_))
    return values, np.full(len(frame), base), np.zeros_like(values)


def permutation_shap(model, background, frame, seed=42):
    """Shapley intervencional: M permutaciones antitéticas; eficiencia exacta por construcción."""
    rng = np.random.default_rng(seed)
    bg = background[FEATURES].to_numpy(dtype=object)
    p, b = len(FEATURES), len(bg)
    numeric = [FEATURES.index(c) for c in NUMERIC]
    values, errors, bases = np.zeros((len(frame), p)), np.zeros((len(frame), p)), np.zeros(len(frame))
    for row, x in enumerate(frame[FEATURES].to_numpy(dtype=object)):
        orders = []
        for _ in range(PERMUTATIONS//2):
            order = rng.permutation(p)
            orders += [order, order[::-1]]
        samples = np.zeros((len(orders), p))
        masks = np.zeros((len(orders), p+1, p), dtype=bool)
        for m, order in enumerate(orders):
            for k in range(1, p+1):
                masks[m, k, order[:k]] = True
        data = np.where(masks[:, :, None, :], x[None, None, None, :], bg[None, None, :, :]).reshape(-1, p)
        batch = pd.DataFrame(data, columns=FEATURES)
        batch[[FEATURES[i] for i in numeric]] = batch[[FEATURES[i] for i in numeric]].astype(float)
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', message='Found unknown categories')
            v = np.asarray(model.predict(batch), float).reshape(len(orders), p+1, b).mean(axis=2)
        for m, order in enumerate(orders):
            samples[m, order] = np.diff(v[m])
        # Promedio de pares antitéticos para estimar el error Monte Carlo.
        pairs = samples.reshape(-1, 2, p).mean(axis=1)
        values[row], errors[row] = samples.mean(axis=0), pairs.std(axis=0, ddof=1)/np.sqrt(len(pairs))
        bases[row] = v[0, 0]
    return values, bases, errors


def tree_shap_xgboost(model, frame):
    transformed = model[:-1].transform(frame[FEATURES])
    matrix = xgb.DMatrix(transformed, enable_categorical=True, nthread=1)
    raw = np.asarray(model.named_steps['modelo'].get_booster().predict(matrix, pred_contribs=True, approx_contribs=False), float)
    names = [c.split('__', 1)[1] for c in transformed.columns]
    assert names == FEATURES
    return raw[:, :-1], raw[:, -1], np.zeros((len(frame), len(FEATURES)))


def explain_all(models, train, test, test_pred, timing):
    background = train.sample(BACKGROUND_ROWS, random_state=42)
    results = {}
    for key in KEYS:
        method = ('Lineal exacto (intervencional)' if key in ['svm', 'ridge', 'lasso'] else
                  'TreeSHAP exacto (tree-path-dependent)' if key == 'xgboost' else
                  f'Permutaciones antitéticas M={PERMUTATIONS}, fondo={BACKGROUND_ROWS} (intervencional)')
        with threadpool_limits(limits=1), timing.measure('Explicación SHAP', f'{key} / test temporal', len(test),
                                                          model=key, method=method, background_rows=BACKGROUND_ROWS,
                                                          repetitions=1, warmup=0,
                                                          scope='Incluye todas las predicciones auxiliares del explicador'):
            if key in ['svm', 'ridge', 'lasso']:
                values, base, err = linear_shap(models[key], background, test)
            elif key == 'xgboost':
                values, base, err = tree_shap_xgboost(models[key], test)
            else:
                values, base, err = permutation_shap(models[key], background, test)
        gap = np.abs(base+values.sum(axis=1)-test_pred[key]).max()
        assert gap < 1e-5, (key, gap)
        results[key] = {'values': values, 'base': base, 'error': err, 'method': method, 'efficiency_gap': float(gap)}
        print(f'SHAP {key}: {method}; brecha de eficiencia {gap:.2e}', flush=True)
    # Validaciones del estimador: Ridge exacto vs permutaciones; XGBoost path-dependent vs intervencional.
    checks = {}
    for key in ['ridge', 'xgboost']:
        with threadpool_limits(limits=1), timing.measure('Explicación SHAP', f'{key} / test · permutaciones de control', len(test),
                                                          model=key, method='Permutaciones de control', repetitions=1, warmup=0):
            values, base, err = permutation_shap(models[key], background, test)
        checks[key] = {'values': values, 'base': base, 'error': err}
    return results, checks, background


def plot_shap_model(key, results, test, test_pred):
    name = NAMES[key]
    values = results[key]['values']
    order = np.argsort(np.abs(values).mean(axis=0))[::-1]
    errors = np.abs(test[TARGET].to_numpy()-test_pred[key])
    cases = {'Menor error absoluto': int(np.argmin(errors)), 'Mayor error absoluto': int(np.argmax(errors))}
    fig = plt.figure(figsize=(13, 11.5))
    grid = fig.add_gridspec(2, 2, height_ratios=[1.1, 1], wspace=.95, hspace=.32)
    ax = fig.add_subplot(grid[0, :])
    rng = np.random.default_rng(42)
    for rank, j in enumerate(order):
        feature = FEATURES[j]
        y = rank+rng.uniform(-.28, .28, len(values))
        if feature in NUMERIC:
            column = test[feature].astype(float)
            low, high = column.quantile([.05, .95])
            color = DIVERGING(np.clip((column-low)/(high-low if high > low else 1), 0, 1).fillna(.5))
        else:
            color = '#9a9a94'
        ax.scatter(values[:, j], y, s=7, c=color, alpha=.75, linewidths=0)
    ax.set_yticks(range(len(order)), [LABELS[FEATURES[j]] for j in order])
    ax.invert_yaxis()
    ax.axvline(0, color=MUTED, lw=1)
    ax.set_xlabel('Valor SHAP (puntos de nota)')
    ax.set_title('Resumen global · 188 filas de test', loc='left')
    sm_ = plt.cm.ScalarMappable(cmap=DIVERGING)
    bar = fig.colorbar(sm_, ax=ax, fraction=.03, pad=.02, ticks=[0, 1])
    bar.ax.set_yticklabels(['Bajo', 'Alto'])
    bar.set_label('Valor numérico (gris = categórica)')
    case_rows = []
    for g, (label, position) in enumerate(cases.items(), 1):
        ax = fig.add_subplot(grid[1, g-1])
        contrib = values[position]
        top = np.argsort(np.abs(contrib))[::-1]
        shown, rest = top[:9], top[9:]
        items = [(LABELS[FEATURES[j]]+' = '+short(test.iloc[position][FEATURES[j]]), contrib[j]) for j in shown]
        items.append((f'{len(rest)} variables restantes', contrib[rest].sum()))
        start = results[key]['base'][position]
        positions = np.arange(len(items))
        path = start+np.cumsum([0]+[v for _, v in items])
        marks = np.r_[path, test_pred[key][position], test[TARGET].iloc[position]]
        span = max(marks.max()-marks.min(), .05)
        offset = .012*span*8
        for i, (text, value) in enumerate(items):
            ax.barh(i, value, left=start, color='#1baf7a' if value >= 0 else '#e34948', height=.7)
            end = start+value
            ax.text(max(start, end)+offset*.25, i, f'{value:+.3f}', va='center', ha='left', fontsize=7.5, color=INK)
            start = end
        ax.set_xlim(marks.min()-.08*span, marks.max()+.3*span)
        ax.axvline(results[key]['base'][position], color=MUTED, ls=':', lw=1)
        ax.axvline(test_pred[key][position], color=INK, lw=1.2)
        ax.axvline(test[TARGET].iloc[position], color='#6250d6', lw=1.6, ls='--')
        ax.set_yticks(positions, [t for t, _ in items], fontsize=7.5)
        ax.invert_yaxis()
        ax.set_xlabel('Nota (puntos)')
        ax.set_title(f'{label} · caso test #{position+1}\nreal {test[TARGET].iloc[position]:.2f} · '
                     f'predicha {test_pred[key][position]:.2f} · base {results[key]["base"][position]:.2f}', loc='left', fontsize=9)
        case_rows += [{'Modelo': name, 'Caso': label, 'Posición test': position+1, 'Variable': LABELS[FEATURES[j]],
                       'Valor': test.iloc[position][FEATURES[j]], 'SHAP': contrib[j]} for j in top]
    fig.suptitle(f'{name} · SHAP ({results[key]["method"]}). Línea punteada = base; continua = predicción; violeta = nota real',
                 x=.01, ha='left', fontsize=11)
    save(fig, f'shap_{key}.png')
    return case_rows


def short(value):
    if isinstance(value, float):
        return f'{value:.1f}' if np.isfinite(value) else 'faltante'
    text = str(value)
    return text if len(text) <= 22 else text[:20]+'…'


def plot_importance_heatmap(results):
    matrix = pd.DataFrame({NAMES[k]: np.abs(results[k]['values']).mean(axis=0) for k in KEYS},
                          index=[LABELS[f] for f in FEATURES])
    share = 100*matrix/matrix.sum()
    share = share.loc[share.mean(axis=1).sort_values(ascending=False).index]
    fig, ax = plt.subplots(figsize=(9, 6))
    image = ax.imshow(share.to_numpy(), cmap=LinearSegmentedColormap.from_list('azul', ['#f4f8fd', '#86b6ef', '#2a78d6', '#104281']), aspect='auto')
    ax.set_xticks(range(len(share.columns)), share.columns, rotation=25, ha='right')
    ax.set_yticks(range(len(share)), share.index)
    ax.grid(False)
    for i in range(share.shape[0]):
        for j in range(share.shape[1]):
            value = share.iat[i, j]
            ax.text(j, i, f'{value:.1f}', ha='center', va='center', fontsize=7.5, color='white' if value > 18 else INK)
    fig.colorbar(image, ax=ax, label='% de la suma de media |SHAP| del modelo')
    ax.set_title('Importancia relativa SHAP por modelo · test temporal', loc='left')
    save(fig, 'shap_importancia_modelos.png')
    return matrix, share


def plot_shap_checks(results, checks):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
    for ax, key, title in [(axes[0], 'ridge', 'Ridge · exacto lineal vs permutaciones'),
                           (axes[1], 'xgboost', 'XGBoost · TreeSHAP path-dependent vs intervencional')]:
        exact, approx = results[key]['values'].ravel(), checks[key]['values'].ravel()
        ax.scatter(exact, approx, s=6, alpha=.35, color=MODEL_COLORS[NAMES[key]], linewidths=0)
        limit = np.abs(np.r_[exact, approx]).max()*1.05
        ax.plot([-limit, limit], [-limit, limit], color=MUTED, ls='--', lw=1)
        r = np.corrcoef(exact, approx)[0, 1]
        mae = np.abs(exact-approx).mean()
        ax.set_title(f'{title}\ncorrelación {r:.4f} · |Δ| medio {mae:.4f}', loc='left', fontsize=9)
        ax.set_xlabel('SHAP de referencia (puntos)')
        ax.set_ylabel('SHAP por permutaciones (puntos)')
    fig.tight_layout()
    save(fig, 'shap_validacion_estimador.png')


def lime_cases(models, train, test, test_pred, timing):
    from lime_xgboost import explain_xgboost
    errors = np.abs(test[TARGET].to_numpy()-test_pred['xgboost'])
    rows = []
    for label, position in [('Menor error absoluto', int(np.argmin(errors))), ('Mayor error absoluto', int(np.argmax(errors)))]:
        record = test.iloc[[position]][FEATURES]
        with timing.measure('Explicación LIME', f'xgboost / test #{position+1}', 1000, model='xgboost',
                            method='LIME empírico, 1000 vecinos, semilla 42', repetitions=1, warmup=0):
            result = explain_xgboost(models['xgboost'], train[FEATURES], record, LABELS, samples=1000, neighborhood='empirical')
        for _, row in result['rows'].iterrows():
            rows.append({'Caso': label, 'Posición test': position+1, 'Variable': row['Variable'],
                         'Condición LIME': row['Condición del caso'], 'Peso LIME': row['Aporte local (puntos)'],
                         'Fidelidad R²': result['fidelity'], 'Predicción': result['prediction'],
                         'Sustituto': result['local_prediction'], 'Intercepto': result['intercept']})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- estadística
def statistics(folds):
    names = [NAMES[k] for k in KEYS]
    folds = folds.loc[folds.Modelo.isin(names)]
    omnibus = friedman_comparison(folds, names)
    post = analyze(folds, names, omnibus)
    ranking = omnibus['ranking']
    k, n = len(names), omnibus['n_folds']
    q = 2.949  # q_0.05 de Nemenyi para k = 7 (Demšar, 2006, tabla 5a)
    cd = q*np.sqrt(k*(k+1)/(6*n))
    mean_rank = ranking.set_index('Modelo')['Rango promedio']
    nemenyi = [{'Modelo A': a, 'Modelo B': b, 'Δ rango (A − B)': mean_rank[a]-mean_rank[b],
                '|Δ| > CD': abs(mean_rank[a]-mean_rank[b]) > cd}
               for a, b in combinations(mean_rank.index, 2)]
    return omnibus, post, cd, pd.DataFrame(nemenyi), mean_rank


def plot_friedman(omnibus, cd, mean_rank, folds):
    ranking = omnibus['ranking'].set_index('Modelo')
    columns = [c for c in ranking.columns if c.startswith('Rango fold')]
    fig, axes = plt.subplots(1, 2, figsize=(13, 3.9), gridspec_kw={'width_ratios': [1, 1.25]})
    ax = axes[0]
    image = ax.imshow(ranking[columns].to_numpy(), cmap=LinearSegmentedColormap.from_list('r', ['#104281', '#86b6ef', '#f4f8fd']), vmin=1, vmax=7)
    ax.set_xticks(range(len(columns)), [c.replace('Rango fold ', 'Fold ') for c in columns])
    ax.set_yticks(range(len(ranking)), ranking.index)
    ax.grid(False)
    for i in range(len(ranking)):
        for j in range(len(columns)):
            value = ranking[columns].iat[i, j]
            ax.text(j, i, f'{value:.0f}', ha='center', va='center', color='white' if value < 3 else INK)
    ax.set_title('Rango por fold externo (1 = mejor)', loc='left')
    ax = axes[1]
    order = mean_rank.sort_values()
    ax.set_xlim(.8, 7.2)
    ax.set_ylim(-1.2, len(order)+.2)
    ax.hlines(len(order)-.2, order.iloc[0], order.iloc[0]+cd, color=INK, lw=3)
    ax.text(order.iloc[0]+cd/2, len(order)+.05, f'CD Nemenyi (α=0.05) = {cd:.2f}', ha='center', fontsize=9)
    for i, (model, rank) in enumerate(order.items()):
        y = len(order)-1.2-i
        ax.plot(rank, y, MARKERS[model], color=MODEL_COLORS[model], ms=9)
        ax.text(rank+.08, y, f'{model} ({rank:.1f})', va='center', fontsize=9)
    ax.set_yticks([])
    ax.set_xlabel('Rango promedio (menor = mejor)')
    fig.suptitle(f'Friedman χ² = {omnibus["statistic"]:.2f}, gl = {omnibus["df"]}, p = {omnibus["pvalue"]:.4f} · diagrama de diferencia crítica (Nemenyi)', x=.01, ha='left', fontsize=11)
    fig.tight_layout()
    save(fig, 'stats_friedman_nemenyi.png')


def plot_robustness(folds, seeds):
    names = [NAMES[k] for k in KEYS]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.3))
    ax = axes[0]
    for name in names:
        block = folds.loc[folds.Modelo.eq(name)].sort_values('Fold')
        ax.plot(block.Fold, block.RMSE, '-'+MARKERS[name], color=MODEL_COLORS[name], lw=1.8, ms=6, label=name)
    ax.set_xticks(range(1, 6))
    ax.set_xlabel('Fold externo')
    ax.set_ylabel('RMSE de validación')
    ax.set_title('RMSE por fold: la variación entre folds domina las diferencias entre modelos', loc='left')
    ax.legend(fontsize=8, ncol=2)
    ax = axes[1]
    if seeds is not None:
        cv = (seeds.loc[seeds['partición'].eq('OOF')].groupby(['Modelo', 'semilla']).RMSE.mean().reset_index())
        present = [n for n in names if n in set(cv.Modelo)]
        for i, name in enumerate(present):
            values = cv.loc[cv.Modelo.eq(name), 'RMSE'].to_numpy()
            ax.scatter(np.full(len(values), i)+np.random.default_rng(i).uniform(-.12, .12, len(values)), values,
                       color=MODEL_COLORS[name], marker=MARKERS[name], s=28, label=name)
            ax.hlines(values.mean(), i-.25, i+.25, color=INK, lw=1.6)
        ax.set_xticks(range(len(present)), present)
        ax.set_ylabel('RMSE medio de 5 folds')
        ax.set_title('Sensibilidad a la semilla del estimador (11 semillas)', loc='left')
    fig.tight_layout()
    save(fig, 'robustez_folds_semillas.png')


# ---------------------------------------------------------------- principal
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    IMAGES.mkdir(parents=True, exist_ok=True)
    train, test, _ = load_partitions()
    cached_train = pd.read_csv(RUN / 'train.csv.gz')
    for fold, (_, val) in enumerate(grouped_splits(train), 1):
        assert cached_train.iloc[val]['fold'].eq(fold).all()
    oof = pd.read_csv(RUN / 'clasicos/train_predictions.csv.gz')
    test_pred = pd.read_csv(RUN / 'clasicos/test_predictions.csv.gz')
    folds = pd.read_csv(RUN / 'clasicos/fold_metrics.csv')
    folds = folds.rename(columns={c: 'R²' for c in folds.columns if c.startswith('R') and len(c) == 2})
    oof = {k: oof[k].to_numpy() for k in KEYS}
    test_pred = {k: test_pred[k].to_numpy() for k in KEYS}

    table, choices, anytime = search_tables()
    table.to_csv(OUT / 'hpo_resumen.csv', index=False)
    choices.to_csv(OUT / 'hpo_metodo_por_busqueda.csv', index=False)
    anytime.to_csv(OUT / 'hpo_anytime.csv', index=False)
    plot_anytime(anytime, 'costo_equivalente', 'hpo_anytime_evaluaciones.png', 'Evaluaciones completas equivalentes')
    plot_anytime(anytime, 'segundos_acumulados', 'hpo_anytime_tiempo.png', 'Segundos de pared acumulados (log)')
    plot_convergence(anytime)
    plot_deap()
    plot_search_time(table)

    models, hashes = load_models()
    timing = TimingRun('Book · evaluación, diagnósticos y SHAP de clásicos', {
        'script': 'jbook_dashboard/analisis_clasicos/generar_clasicos.py', 'script_sha256': file_hash(__file__),
        'active_run': RUN.name, 'model_sha256': hashes, 'train_rows': len(train), 'test_rows': len(test),
        'background_rows': BACKGROUND_ROWS, 'permutations': PERMUTATIONS, 'seed': 42, 'device': 'CPU',
        'parallelism': '1 hilo; secuencial', 'scope': 'Sin búsqueda ni refit. Inferencia de pipelines guardados y explicadores.'})
    status = 'fallida'
    try:
        train_pred, scores, diagnostics = evaluation(models, train, test, oof, test_pred, folds, timing)
        scores.to_csv(OUT / 'eval_metricas.csv', index=False)
        diagnostics.to_csv(OUT / 'eval_diagnosticos.csv', index=False)
        for key in KEYS:
            plot_model_fit(key, train, test, train_pred, oof, test_pred, scores)
        plot_metric_overview(scores)
        results, checks, _ = explain_all(models, train, test, test_pred, timing)
        cases = []
        for key in KEYS:
            cases += plot_shap_model(key, results, test, test_pred)
        pd.DataFrame(cases).to_csv(OUT / 'shap_casos.csv', index=False)
        raw, share = plot_importance_heatmap(results)
        raw.to_csv(OUT / 'shap_media_abs.csv')
        share.to_csv(OUT / 'shap_importancia_pct.csv')
        plot_shap_checks(results, checks)
        shap_meta = {k: {'method': r['method'], 'efficiency_gap': r['efficiency_gap'],
                         'mc_se_mean': float(r['error'].mean())} for k, r in results.items()}
        shap_meta['controles'] = {k: {'corr': float(np.corrcoef(results[k]['values'].ravel(), c['values'].ravel())[0, 1]),
                                      'mae': float(np.abs(results[k]['values']-c['values']).mean()),
                                      'mc_se_mean': float(c['error'].mean()),
                                      'top5_referencia': [LABELS[FEATURES[j]] for j in np.argsort(np.abs(results[k]['values']).mean(0))[::-1][:5]],
                                      'top5_permutacion': [LABELS[FEATURES[j]] for j in np.argsort(np.abs(c['values']).mean(0))[::-1][:5]]}
                                  for k, c in checks.items()}
        lime = lime_cases(models, train, test, test_pred, timing)
        lime.to_csv(OUT / 'lime_xgboost_casos.csv', index=False)
        status = 'completa'
    finally:
        timing.finish(status)
    shap_meta['timing_run_id'] = timing.run_id
    (OUT / 'shap_meta.json').write_text(json.dumps(shap_meta, indent=2, ensure_ascii=False), encoding='utf-8')

    omnibus, post, cd, nemenyi, mean_rank = statistics(folds)
    plot_friedman(omnibus, cd, mean_rank, folds)
    nemenyi.to_csv(OUT / 'stats_nemenyi.csv', index=False)
    post['mcs'].to_csv(OUT / 'stats_mcs.csv', index=False)
    post['effects'].to_csv(OUT / 'stats_efectos.csv', index=False)
    post['pairs'].to_csv(OUT / 'stats_pares_finalistas.csv', index=False)
    omnibus['ranking'].to_csv(OUT / 'stats_rangos.csv', index=False)
    seeds_path = OUT / 'semillas' / 'semillas_estimador.csv'
    seeds = pd.read_csv(seeds_path) if seeds_path.exists() else None
    plot_robustness(folds.loc[folds.Modelo.isin(NAMES.values())], seeds)
    (OUT / 'stats_resumen.json').write_text(json.dumps({'friedman': {k: omnibus[k] for k in ['statistic', 'pvalue', 'df', 'n_folds', 'n_models']},
        'nemenyi_cd': cd, 'mcs_finalists': post['finalists'], 'timing_run_id': timing.run_id}, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Listo:', timing.run_id, flush=True)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()

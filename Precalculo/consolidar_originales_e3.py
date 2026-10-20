"""Consolida en una ejecución versionada única las búsquedas Originales ya completas.

No entrena ni busca: parte de la ejecución base activa (SVR RBF, Kernel Ridge, TR-KRR),
superpone los modelos de las ejecuciones parciales (catálogo con parámetros finales,
OOF, test, folds, trazas y artefactos) y conserva intactas las ejecuciones fuente.
Después se activa con `Dash/activate_originals.py <directorio>`.
"""
import argparse
import hashlib
import json
import shutil
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from entregable3 import BOOK, FEATURES

ROOT = BOOK / 'resultados/e3/originales_busquedas'
BASE = '20261019_083039_147f9845'
SOURCES = {'20261019_144732_b7acf148': ('m11',),
           '20261020_100140_8f327baf': ('m7', 'm14'),
           '20261020_103916_fb6c8c6d': ('m15', 'm16'),
           '20261020_150908_3a07b335': ('m3',)}
# Se regeneran al activar o aquí; no se heredan de la base.
SKIP = {'active.json', 'analysis.json', 'explanations.json', 'completo.json'}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, default=lambda v: v.item()), encoding='utf-8')


NOTES = {
    'm3': 'Implementación fiel (cortes exactos en cada nodo, profundidad máxima alta limitada por min_samples_leaf). Búsqueda ampliada '
          '(20-oct-2026) solo con Optuna/TPE por decisión del usuario: 40 ensayos (10 aleatorios iniciales) sobre un dominio más amplio '
          '(min_samples_leaf 30–450, reg_lambda 0.1–1000, gamma 0.001–50, learning_rate 0.02–0.4, n_estimators 1–5). La primera búsqueda fiel '
          'con cinco estrategias (Grid de 48 candidatos; TPE fue el método más eficiente) tuvo sus óptimos en el borde del dominio y se conserva '
          'como evidencia en la ejecución 20261020_103916_fb6c8c6d.',
    'm11': 'Búsqueda nueva (19-oct-2026): Grid grueso documentado de 96 candidatos (n_estimators, max_depth, learning_rate, '
           'min_child_weight, reg_lambda y weight_alpha ∈ {0, 0.5, 1}; weight_alpha=0 equivale a XGBoost sin ponderar); '
           'las demás estrategias usan el dominio histórico completo.',
    'm7': 'Protocolo del artículo (20-oct-2026, retrofit): se busca solo fraction/weight sobre el XGBoost ya ajustado en el mismo '
          'entrenamiento externo (el del XGBoost clásico); Grid de 10 candidatos. weight=1 o fraction=0 equivale a XGBoost sin reponderar.',
    'm14': 'Implementación fiel al artículo (20-oct-2026, logicdt_fiel.py): predictores binarios = one-hot, covariables numéricas en modelos '
           'lineales de hoja con división por razón de verosimilitud (α=0.5), recocido simulado adaptativo (Apéndice 1) y vecindad de la Fig. 3. '
           'Hiperparámetros: max_conj, extra_vars (max_vars) y nodesize=conjsize; Grid de 33 candidatos. Presupuesto de iteraciones acotado (10,000).',
    'm15': 'Búsqueda de hiperparámetros de XGBoost solamente (n_estimators, learning_rate, max_leaves, reg_lambda; Grid de 54). Kernel GPR fijo '
           'C·(Matérn 2.5 + RBF) + White (Apéndice B.1) con 5 reinicios del optimizador; la etapa GPR (OOF por estudiante) se calcula una vez por '
           'conjunto de ajuste y se reutiliza entre candidatos.',
    'm16': 'Búsqueda sobre la grilla histórica de 8 candidatos (n_neighbors, epochs, weight_decay); BM25 con el IDF del artículo (Ec. 7, '
           'log((N−n+0.5)/(n+0.5))) y candidatos = filas que cumplen la consulta OR; el resto de RIM queda fijo.',
}
DESCRIPTIONS = {
    'm14': 'Árbol de decisión sobre conjunciones booleanas de indicadores binarios, con modelos lineales en las hojas para las covariables '
           'numéricas; los términos se buscan por recocido simulado adaptativo. Implementación fiel al artículo, no el paquete R.',
}


def merge_grid(grid):
    """Un Grid condicional (lista de dicts) se muestra como dominio por parámetro."""
    if not isinstance(grid, list):
        return grid
    merged = {}
    for block in grid:
        for name, values in block.items():
            merged.setdefault(name, set()).update(values)
    return {name: sorted(values) for name, values in merged.items()}


def consolidate():
    run_id = time.strftime('%Y%m%d_%H%M%S') + '_consolidada'
    output = ROOT / run_id
    shutil.copytree(ROOT / BASE, output, ignore=lambda _, names: [n for n in names if n in SKIP])
    catalog = load(output / 'catalog.json')
    folds = pd.read_csv(output / 'folds.csv')
    predictions = {part: pd.read_csv(output / f'{part}.csv.gz') for part in ('train', 'test')}
    executed = list(load(ROOT / BASE / 'completo.json')['executed'])
    selection = load(output / 'seleccion_antes_test.json')
    provenance = {BASE: executed.copy()}
    (output / 'evidencia_fuentes').mkdir(exist_ok=True)
    for source, keys in SOURCES.items():
        directory = ROOT / source
        done = load(directory / 'completo.json')
        source_catalog = load(directory / 'catalog.json')
        source_folds = pd.read_csv(directory / 'folds.csv')
        source_predictions = {part: pd.read_csv(directory / f'{part}.csv.gz') for part in ('train', 'test')}
        for part in predictions:
            # Mismas filas y mismas columnas de modelos no ejecutados que la base.
            for column in ('svm', 'knn', 'm0', 'm5', 'm19'):
                np.testing.assert_allclose(predictions[part][column], source_predictions[part][column], atol=1e-12, rtol=0)
        for key in keys:
            assert key in done['executed'] and source_catalog[key].get('status', '').startswith('Actualizado')
            name = source_catalog[key]['name']
            rows = source_folds.loc[source_folds.Modelo.eq(name)]
            assert len(rows) == 5, (key, len(rows))
            catalog[key] = source_catalog[key]
            catalog[key]['grid'] = merge_grid(catalog[key].get('grid'))
            catalog[key]['method'] = (catalog[key].get('method') or '') + ' ' + NOTES[key]
            if key in DESCRIPTIONS:
                catalog[key]['description'] = DESCRIPTIONS[key]
            if key == 'm15':
                log = ROOT.parent / 'gpr_xgb_hpo/cache_gpr/gpr_stage_log.jsonl'
                stage = [json.loads(line)['seconds'] for line in log.read_text(encoding='utf-8').splitlines() if line.strip()]
                catalog[key]['limitations'] = [*catalog[key].get('limitations', []),
                    f'Etapa GPR compartida entre candidatos: {len(stage)} cómputos, {sum(stage):.1f} s de CPU de proceso acumulados '
                    '(cuatro procesos en paralelo; no es tiempo de pared ni se suma a los tiempos por candidato). Bitácora: '
                    'resultados/e3/gpr_xgb_hpo/cache_gpr/gpr_stage_log.jsonl.']
            folds = pd.concat([folds.loc[~folds.Modelo.eq(name)], rows], ignore_index=True)
            for part in predictions:
                predictions[part][key] = source_predictions[part][key].to_numpy()
            for pattern in (f'completo_{key}.json', f'selection_{key}_*.json', f'trials_{key}_*.jsonl'):
                for file in directory.glob(pattern):
                    shutil.copyfile(file, output / file.name)
            model = joblib.load(directory / f'{key}.joblib')
            if not hasattr(model, 'feature_names_in_'):
                # El estimador sin Pipeline solo guardaba n_features_in_; se declara el orden de entrada.
                # Pipeline delega feature_names_in_ en su primer paso: se fija en ese estimador.
                estimator = model.steps[0][1] if hasattr(model, 'steps') else model
                estimator.feature_names_in_ = np.asarray(FEATURES, dtype=object)
            joblib.dump(model, output / f'{key}.joblib')
            selection['models'][key] = load(directory / 'seleccion_antes_test.json')['models'][key]
            executed.append(key)
        provenance[source] = list(keys)
        evidence = directory / 'evidencia'
        if evidence.exists():
            shutil.copytree(evidence, output / 'evidencia_fuentes' / source, dirs_exist_ok=True)
    for part, frame in predictions.items():
        frame.to_csv(output / f'{part}.csv.gz', index=False)
    folds.to_csv(output / 'folds.csv', index=False)
    dump(output / 'seleccion_antes_test.json', {**selection, 'run_id': run_id, 'test_used_for_selection': False})
    protocol = load(output / 'protocolo.json')
    protocol.update(run_id=run_id, models=executed, consolidated_from=provenance,
                    note='Consolidación sin nuevos entrenamientos; cada modelo conserva su ejecución y tiempos de origen.')
    dump(output / 'protocolo.json', protocol)
    eligible = {k: s for k, s in catalog.items() if k != 'dummy' and k in predictions['train']
                and len(folds.loc[folds.Modelo.eq(s['name'])]) == 5}
    means = folds.groupby('Modelo').RMSE.mean()
    best = min(eligible, key=lambda k: means[eligible[k]['name']])
    # best.joblib ya se heredó de la base (Kernel Ridge, m5); solo cambia si otro modelo lo supera en CV.
    if best != 'm5':
        shutil.copyfile(output / f'{best}.joblib', output / 'best.joblib')
    dump(output / 'catalog.json', catalog)
    dump(output / 'completo.json', {
        'run_id': run_id, 'best_key': best, 'best_name': catalog[best]['name'],
        'best_mean_cv': float(means[catalog[best]['name']]), 'executed': executed,
        'consolidated_from': provenance,
        'note': 'Ejecución consolidada: búsquedas anidadas (Grid/Random/TPE/DEAP/SH) por modelo; test no selecciona.',
        'files': {p.name: sha256(p) for p in sorted(output.iterdir()) if p.is_file()}})
    print('CONSOLIDADA', output, 'LÍDER CV', best, catalog[best]['name'], flush=True)
    return output


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    consolidate()

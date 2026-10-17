"""Evaluar un paquete ajustado en el test E3, sin volver a optimizar pesos."""
import argparse
import gc
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.stats import permutation_test
from sklearn.base import clone
from statsmodels.stats.multitest import multipletests

from entregable3 import BOOK, OUTPUT, FEATURES, GROUP, TARGET, make_pipeline, metrics, source_hashes, write_json
from evaluacion_nuevos_e3 import partitions
from finetune_tabpfn25_e3 import load_bundle, sha256

DEFAULT_BUNDLE = BOOK/'modelos_preentrenados/tabpfn_25/finetuning/20261015_091524_448419'


def paired_comparison(y, new, old, groups, seed=42):
    """Mismo contraste SSE para RMSE/R²; bootstrap por estudiante."""
    codes, ids = pd.factorize(groups, sort=False)
    aggregate = lambda v: np.bincount(codes, weights=v, minlength=len(ids))
    a, b = aggregate((y-new)**2), aggregate((y-old)**2)
    result = permutation_test((a-b,), lambda x, axis: x.sum(axis=axis),
        permutation_type='samples', vectorized=True, n_resamples=99999,
        batch=512, alternative='two-sided', rng=np.random.default_rng(seed))
    n, sy, sy2 = aggregate(np.ones(len(y))), aggregate(y), aggregate(y*y)
    rng = np.random.default_rng(seed)
    dr, d2 = [], []
    for start in range(0, 10000, 512):
        ix = rng.integers(len(ids), size=(min(512, 10000-start), len(ids)))
        counts, sa, sb = n[ix].sum(axis=1), a[ix].sum(axis=1), b[ix].sum(axis=1)
        sst = sy2[ix].sum(axis=1)-sy[ix].sum(axis=1)**2/counts
        if (sst <= 0).any():
            raise ValueError('Varianza nula en bootstrap.')
        dr.extend(np.sqrt(sa/counts)-np.sqrt(sb/counts))
        d2.extend((sb-sa)/sst)
    sa, sb = metrics(y, new), metrics(y, old)
    return [{'metrica': metric, 'diferencia_ajustado_menos_referencia': sa[metric]-sb[metric],
             'IC_2.5%': float(np.quantile(draws, .025)), 'IC_97.5%': float(np.quantile(draws, .975)),
             'p_bilateral': float(result.pvalue)} for metric, draws in [('RMSE', dr), ('R²', d2)]]


def evaluate(directory=DEFAULT_BUNDLE, force=False):
    directory = Path(directory).resolve()
    train, test, _, audit = partitions()
    manifest_path = directory/'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest['status'] != 'complete' or manifest['features'] != FEATURES or manifest['target'] != TARGET:
        raise ValueError('Paquete incompleto o variables distintas.')
    for name, expected in manifest['source_sha256'].items():
        if sha256(BOOK/name) != expected:
            raise ValueError(f'La procedencia del paquete difiere del proyecto actual: {name}')
    for name, expected in manifest['files_sha256'].items():
        if sha256(directory/name) != expected:
            raise ValueError(f'Archivo del paquete modificado: {name}')
    prep = joblib.load(directory/'preprocesador.joblib')
    canonical_prep = clone(make_pipeline().named_steps['preprocesamiento']).fit(train[FEATURES])
    np.testing.assert_array_equal(prep.get_feature_names_out(), canonical_prep.get_feature_names_out())
    np.testing.assert_allclose(prep.transform(train[FEATURES]), canonical_prep.transform(train[FEATURES]), atol=1e-12, rtol=0)
    with np.load(directory/'contexto_train.npz', allow_pickle=False) as context:
        np.testing.assert_allclose(context['X'], canonical_prep.transform(train[FEATURES]), atol=1e-12, rtol=0)
        np.testing.assert_array_equal(context['y'], train[TARGET].to_numpy())
    print(f'Paquete verificado: {manifest["epochs_final"]} épocas finales; '
          f'{manifest["changed_weight_tensors"]} tensores cambiaron. Contexto idéntico a train.', flush=True)
    folder = OUTPUT/'tabpfn_25_finetuned'/directory.name
    folder.mkdir(parents=True, exist_ok=True)
    paths = ['evaluar_tabpfn25_finetuned_e3.py', 'resultados/e3/test.csv.gz',
             'resultados/e3/tabpfn_25/test_predictions.csv.gz', 'resultados/e3/tabpfn_25/reporte.json',
             'resultados/e3/clasicos/comparacion.json', 'resultados/e3/logicdt/reporte.json']
    signature = {**source_hashes(), **{p: sha256(BOOK/p) for p in paths},
                 'bundle_manifest': sha256(manifest_path), **manifest['files_sha256']}
    report_path = folder/'reporte.json'
    if report_path.exists() and not force:
        cached = json.loads(report_path.read_text(encoding='utf-8'))
        if cached['provenance'] == signature:
            print('Reutilizando evaluación completa con procedencia verificada.', flush=True)
            return cached
    import torch
    torch.set_num_threads(4)
    print('Inferencia CPU: 188 estudiantes del test temporal 202530, sin fine-tuning adicional.', flush=True)
    pipeline = load_bundle(directory, device='cpu')
    new = np.asarray(pipeline.predict(test[FEATURES]), dtype=np.float64)
    del pipeline
    gc.collect()
    if not np.isfinite(new).all():
        raise ValueError('Predicciones no finitas.')
    y = test[TARGET].to_numpy(float)
    export = test[[TARGET, 'periodo']].copy()
    export['prediccion'] = new
    export['residuo'] = y-new
    export.to_csv(folder/'test_predictions.csv.gz', index=False, compression='gzip')
    previous = json.loads((OUTPUT/'tabpfn_25/reporte.json').read_text(encoding='utf-8'))
    base_frame = pd.read_csv(OUTPUT/'tabpfn_25/test_predictions.csv.gz')
    np.testing.assert_allclose(base_frame[TARGET], y, rtol=0, atol=1e-12)
    base = base_frame.prediccion.to_numpy().astype(np.float32).astype(float)
    for m, score in metrics(y, base).items():
        np.testing.assert_allclose(score, previous['test'][m], rtol=0, atol=1e-12)
    svm = pd.read_csv(OUTPUT/'test.csv.gz').svm.to_numpy(float)
    name = 'TabPFN 2.5 fine-tuned'
    score = metrics(y, new)
    classic = json.loads((OUTPUT/'clasicos/comparacion.json').read_text(encoding='utf-8'))['test']
    logic = json.loads((OUTPUT/'logicdt/reporte.json').read_text(encoding='utf-8'))
    table = classic + [{'Modelo': logic['model'], **logic['test']},
                       {'Modelo': 'TabPFN 2.5 original', **previous['test']}, {'Modelo': name, **score}]
    comparisons = []
    for label, old in [('TabPFN 2.5 original', base), ('SVM lineal', svm)]:
        comparisons.append({'referencia': label, 'rows': paired_comparison(y, new, old, test[GROUP])})
    # Dos contrastes de modelos; RMSE/R² son dos expresiones del MISMO contraste SSE.
    adjusted = multipletests([c['rows'][0]['p_bilateral'] for c in comparisons], alpha=.05, method='holm')[1]
    for comp, p in zip(comparisons, adjusted):
        for row in comp['rows']:
            row['p_Holm_dos_comparaciones'] = float(p)
            row['significativa_al_5%_Holm'] = bool(p < .05)
    report = {'model': name, 'test': score, 'comparison_test': table, 'provenance': signature,
              'partition': audit, 'bundle': str(directory), 'epochs_final': manifest['epochs_final'],
              'inference': manifest['inference'], 'paired_comparisons': comparisons,
              'method': 'Mismo test202530, 15 variables y preparación; contexto completo de train. '
                        'Pesos finales ajustados con todo train: no evaluar estos pesos en folds de train '
                        'como si fueran OOF, pues ya vieron esos estudiantes. Los folds del entrenamiento '
                        'seleccionaron épocas y no son una nueva CV externa anidada.',
              'statistics': 'Permutación pareada bilateral por estudiante, 99999 permutaciones, seed42; '
                            'IC95% bootstrap pareado10000. Holm para dos pares de modelos; RMSE/R² '
                            'comparten contraste SSE y p. Inferencia exploratoria condicional, test '
                            'previamente inspeccionado, sin variabilidad de reentrenamiento.',
              'outputs': str(folder)}
    write_json(report_path, report)
    pd.DataFrame(table).to_csv(folder/'comparacion_test.csv', index=False)
    pd.DataFrame([{'referencia': c['referencia'], **row} for c in comparisons for row in c['rows']]).to_csv(
        folder/'comparaciones_pareadas.csv', index=False)
    print(json.dumps(score, ensure_ascii=False), flush=True)
    return report


def show(report):
    from IPython.display import display
    import matplotlib.pyplot as plt
    table = pd.DataFrame(report['comparison_test'])
    display(table.sort_values('RMSE').round(6))
    display(pd.DataFrame([{'referencia': c['referencia'], **row} for c in report['paired_comparisons'] for row in c['rows']]).round(6))
    fig, axes = plt.subplots(2, 2, figsize=(15, 11), constrained_layout=True)
    for ax, metric in zip(axes.flat, ['RMSE', 'MAE', 'MAPE (%)', 'R²']):
        ordered = table.sort_values(metric, ascending=metric != 'R²')
        colors = ['#cc5500' if m == report['model'] else '#20806b' if m == 'TabPFN 2.5 original' else '#326d9c'
                  for m in ordered.Modelo]
        bars = ax.barh(ordered.Modelo, ordered[metric], color=colors)
        ax.bar_label(bars, fmt='%.3f', padding=3, fontsize=8)
        ax.invert_yaxis()
        ax.set_title(f'{metric}: {"mayor" if metric == "R²" else "menor"} es mejor')
        ax.margins(x=.2)
        ax.grid(axis='x', alpha=.2)
    plt.show()


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle', type=Path, default=DEFAULT_BUNDLE)
    p.add_argument('--force', action='store_true')
    a = p.parse_args()
    evaluate(a.bundle, a.force)

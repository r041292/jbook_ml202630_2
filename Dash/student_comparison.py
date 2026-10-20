"""Comparaciones de modelos finales vs SVM, por estudiante del test reservado.

No entrena ni predice: usa predicciones guardadas. Bootstrap-t bilateral bajo
H0 para media de diferencias MSE, Holm6 e IC BCa individuales. Los IDs solo
se usan en memoria durante la preparación privada, nunca se exportan.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm
from dash import html

from model_timing import TimingRun, file_hash

ARTIFACT = 'clasicos/comparacion_svm_bootstrap.json'
REPS = 49999
SEED = 20261018
INPUTS = ('test.csv.gz', 'train.csv.gz', 'clasicos/test_predictions.csv.gz', 'clasicos/train_predictions.csv.gz',
          'clasicos/fold_metrics.csv', 'clasicos/comparacion.json')


def student_losses(truth, predictions, groups):
    """Una fila por estudiante, peso igual; cada registro pesa 1/n_i en su grupo."""
    y = np.asarray(truth, dtype=float)
    p = np.asarray(predictions, dtype=float)
    g = pd.Series(groups).reset_index(drop=True)
    if p.ndim != 2 or len(y) != len(p) or len(g) != len(y) or g.isna().any():
        raise ValueError('Objetivos, predicciones y grupos deben estar completos y alineados.')
    if not np.isfinite(y).all() or not np.isfinite(p).all():
        raise ValueError('No se permiten pérdidas con faltantes o infinitos.')
    codes, _ = pd.factorize(g, sort=False)
    losses = pd.DataFrame((p-y[:, None])**2).groupby(codes, sort=True).mean().to_numpy()
    return losses, np.bincount(codes)


def holm(values):
    """Mantiene la familia completa: un p no estimable cuenta como 1 al ajustar."""
    p = np.asarray([1. if v is None else v for v in values])
    order = np.argsort(p, kind='stable')
    result = np.empty(len(p))
    result[order] = np.minimum(1., np.maximum.accumulate((len(p)-np.arange(len(p)))*p[order]))
    return [None if v is None else float(result[i]) for i, v in enumerate(values)]


def bca_interval(point, draws, jackknife):
    """BCa con jackknife por estudiante; no sustituye degeneraciones en silencio."""
    boot, jack = np.asarray(draws), np.asarray(jackknife)
    centered = jack.mean()-jack
    squares = np.sum(centered**2)
    score = (np.mean(boot < point)+np.mean(boot <= point))/2
    if squares == 0 or np.ptp(boot) == 0 or not 0 < score < 1:
        return {'low': None, 'high': None, 'state': 'No estimable · BCa degenerado',
                'bias_z0': None, 'acceleration': None, 'tail_warning': False}
    z0 = norm.ppf(score)
    acceleration = np.sum(centered**3)/(6*squares**1.5)
    z = z0+norm.ppf([.025, .975])
    denominator = 1-acceleration*z
    if np.any(denominator <= 0):
        return {'low': None, 'high': None, 'state': 'No estimable · BCa inestable',
                'bias_z0': float(z0), 'acceleration': float(acceleration), 'tail_warning': True}
    probabilities = norm.cdf(z0+z/denominator)
    low, high = np.quantile(boot, probabilities)
    return {'low': float(low), 'high': float(high), 'state': 'Calculado',
            'bias_z0': float(z0), 'acceleration': float(acceleration),
            'tail_warning': bool(np.min(np.minimum(probabilities, 1-probabilities))*len(boot) < 10)}


def compare(losses, names, *, reps=REPS, seed=SEED, batch=512):
    """SVM en columna 0; todas las comparaciones previstas, sin filtrar por MCS."""
    x = np.asarray(losses, dtype=float)
    if x.ndim != 2 or len(x) < 3 or x.shape[1] != len(names) or len(set(names)) != len(names):
        raise ValueError('Se requieren al menos tres estudiantes y nombres únicos alineados.')
    if not np.isfinite(x).all() or (x < 0).any() or reps < 99:
        raise ValueError('MSE finitos no negativos y al menos 99 réplicas requeridos.')
    n, k = x.shape
    d = x[:, 1:]-x[:, [0]]
    mean, sd = d.mean(axis=0), d.std(axis=0, ddof=1)
    estimable = sd > 0
    observed = np.divide(mean, sd/np.sqrt(n), out=np.zeros(k-1), where=estimable)
    rmse_delta = np.sqrt(x.mean(axis=0)[1:])-np.sqrt(x[:, 0].mean())
    boot_mse, boot_rmse, null_t = (np.empty((reps, k-1)) for _ in range(3))
    rng = np.random.default_rng(seed)
    zero_counts = np.zeros(k-1, dtype=int)
    for start in range(0, reps, batch):
        stop = min(start+batch, reps)
        ix = rng.integers(0, n, (stop-start, n))
        sample = x[ix]
        delta = d[ix]
        boot_mse[start:stop] = delta.mean(axis=1)
        averages = sample.mean(axis=1)
        boot_rmse[start:stop] = np.sqrt(averages[:, 1:])-np.sqrt(averages[:, [0]])
        # Centrado bajo H0; cada réplica usa su propio error estándar.
        numerator = boot_mse[start:stop]-mean
        se = delta.std(axis=1, ddof=1)/np.sqrt(n)
        zero_counts += (se == 0).sum(axis=0)
        t = np.divide(numerator, se, out=np.zeros_like(numerator), where=se > 0)
        t[(se == 0) & (numerator > 0)] = np.inf
        t[(se == 0) & (numerator < 0)] = -np.inf
        null_t[start:stop] = t
    # Quitar un estudiante completo, no una fila individual.
    jack_losses = (x.sum(axis=0)-x)/(n-1)
    jack_mse = jack_losses[:, 1:]-jack_losses[:, [0]]
    jack_rmse = np.sqrt(jack_losses[:, 1:])-np.sqrt(jack_losses[:, [0]])
    rows, raw = [], []
    for j in range(k-1):
        identical = np.all(d[:, j] == 0)
        count = int((np.abs(null_t[:, j]) >= abs(observed[j])).sum())
        p = float((count+1)/(reps+1)) if estimable[j] else 1. if identical else None
        raw.append(p)
        rows.append({'model': names[j+1], 'reference': names[0],
                     'delta_mse': float(mean[j]), 'delta_rmse': float(rmse_delta[j]),
                     't_observed': float(observed[j]) if estimable[j] else None,
                     'p_raw': p, 'null_exceedances': count if estimable[j] else None,
                     'mc_se_raw': float(np.sqrt(p*(1-p)/reps)) if estimable[j] else None,
                     'zero_se_resamples': int(zero_counts[j]),
                     'cohen_dz': float(mean[j]/sd[j]) if estimable[j] else None,
                     'bca_mse': bca_interval(mean[j], boot_mse[:, j], jack_mse[:, j]),
                     'bca_rmse': bca_interval(rmse_delta[j], boot_rmse[:, j], jack_rmse[:, j]),
                     'test_state': 'Calculado' if estimable[j] else 'Pérdidas idénticas' if identical else 'No estimable · SD cero'})
    for row, adjusted in zip(rows, holm(raw)):
        row['p_holm'] = adjusted
        row['conclusion'] = ('No estimable' if adjusted is None else
                             'Diferencia no detectada' if adjusted >= .05 else
                             'Mejora significativa' if row['delta_mse'] < 0 else 'Deterioro significativo')
    return {'n_students': n, 'n_models': k, 'family_size': k-1, 'reps': reps, 'seed': seed,
            'rows': rows}, {'delta_mse': boot_mse, 'delta_rmse': boot_rmse, 'null_t': null_t}


def prepare(cache, book, active):
    """Preparación privada: valida filas con la partición original antes de agrupar."""
    import sys
    if str(book) not in sys.path:
        sys.path.insert(0, str(book))
    from entregable3 import load_partitions, GROUP, TARGET, FEATURES, PERIOD
    cache, book, active = Path(cache), Path(book), Path(active)
    report = json.loads((cache/'clasicos/comparacion.json').read_text(encoding='utf-8'))
    keys = ['svm', *report['models']]
    names = ['SVM lineal', *[report['models'][key]['name'] for key in keys[1:]]]
    if len(keys) != 7:
        raise ValueError('Este protocolo define seis clásicos contra SVM.')
    hashes = {name: file_hash(cache/name) for name in INPUTS}
    run = TimingRun('Comparación por estudiante · seis clásicos frente a SVM · test', {
        'script': 'Dash/student_comparison.py', 'script_sha256': file_hash(__file__),
        'input_sha256': hashes, 'active_run': report.get('run_id'),
        'raw_sha256': file_hash(book/'Data/Datos_Brutos.csv'),
        'configuration': {'reps': REPS, 'seed': SEED, 'alpha': .05, 'family': names[1:],
                          'unit': 'Estudiante; media MSE de registros, peso igual por estudiante',
                          'test': 'Bootstrap-t bilateral centrado bajo H0; Holm6',
                          'ci': 'BCa95 individual, jackknife por estudiante'},
        'scope': 'Solo estadística de predicciones guardadas; sin búsqueda, entrenamiento ni inferencia',
        'device': 'CPU; un proceso; NumPy por lotes512; sin GPU'})
    status = 'fallida'
    try:
        with run.measure('Preparación estadística', 'Validación de partición y agregación privada'):
            expected_raw = report['source_sha256']['Data/Datos_Brutos.csv']
            if file_hash(book/'Data/Datos_Brutos.csv') != expected_raw:
                raise ValueError('La fuente privada no corresponde a las predicciones guardadas.')
            private_train, private_test, _ = load_partitions()
            test = pd.read_csv(cache/'test.csv.gz')
            pred = pd.read_csv(cache/'clasicos/test_predictions.csv.gz')
            pd.testing.assert_frame_equal(private_test[FEATURES+[TARGET, PERIOD]],
                                          test[FEATURES+[TARGET, PERIOD]], check_dtype=False,
                                          check_exact=False, rtol=1e-12, atol=1e-12)
            if len(pred) != len(test):
                raise ValueError('Las predicciones no corresponden a la partición.')
            for name in INPUTS:
                if file_hash(active/name) != hashes[name]:
                    raise ValueError('La caché no coincide con la ejecución canónica: '+name)
            np.testing.assert_allclose(test.svm, pred.svm, atol=1e-12, rtol=0)
            losses, sizes = student_losses(test[TARGET], pred[keys], private_test[GROUP])
        with run.measure('Análisis estadístico', 'Bootstrap-t, BCa y Holm6', len(losses)):
            result, draws = compare(losses, names)
        # Etapa 3 vigente: Diebold–Mariano por estudiante, 5 primeros del MCS, comparaciones independientes.
        from classic_friedman import friedman_comparison
        from classic_posthoc import analyze as posthoc_analyze
        from student_dm import select_top, analyze as dm_analyze, corrected_from_folds, finalist_pairs
        folds = pd.read_csv(cache/'clasicos/fold_metrics.csv')
        omnibus = friedman_comparison(folds, names)
        posthoc = posthoc_analyze(folds, names, omnibus)
        mcs = posthoc['mcs']
        train_cache = pd.read_csv(cache/'train.csv.gz')
        train_pred = pd.read_csv(cache/'clasicos/train_predictions.csv.gz')
        np.testing.assert_allclose(private_train[TARGET].to_numpy(float), train_cache[TARGET].to_numpy(float), atol=1e-9)
        np.testing.assert_array_equal(train_pred['fold'], train_cache['fold'])
        by_fold = pd.DataFrame({'g': private_train[GROUP].to_numpy(), 'f': train_cache['fold'].to_numpy()})
        total_students = by_fold.g.nunique()
        ratio = float(np.mean([by_fold.loc[by_fold.f == f, 'g'].nunique() /
                               (total_students - by_fold.loc[by_fold.f == f, 'g'].nunique())
                               for f in sorted(by_fold.f.unique())]))
        with run.measure('Análisis estadístico', 'Diebold–Mariano por estudiante top 5 MCS (CV, test)', len(private_train)):
            dm = dm_analyze(select_top(mcs, 5), train_pred, pred, private_train[GROUP].to_numpy(),
                            private_test[GROUP].to_numpy(), private_train[TARGET].to_numpy(float),
                            private_test[TARGET].to_numpy(float), dict(zip(names, keys)), 'svm',
                            corrected_from_folds(folds[folds.Modelo.isin(names)], 'SVM lineal', ratio))
        dm['finalist_pairs'] = finalist_pairs(posthoc['pairs'], train_pred, private_train[GROUP].to_numpy(),
                                              private_train[TARGET].to_numpy(float), dict(zip(names, keys)))
        result['dm'] = dm
        result.update(active_run=report.get('run_id'), analysis_run=run.run_id,
                      input_sha256=hashes, script_sha256=file_hash(__file__), n_records=len(test),
                      students_with_repeated_records=int((sizes > 1).sum()),
                      max_records_per_student=int(sizes.max()),
                      scope='Exploratorio posterior a revisión de test202530; modelos finales fijos; sin selección',
                      weighting='Igual por estudiante; RMSE = raíz de la media de MSE por estudiante')
        serialized = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
        (run.directory/'resultados.json').write_text(serialized, encoding='utf-8')
        np.savez_compressed(run.directory/'distribuciones_bootstrap.npz', **draws)
        (cache/ARTIFACT).write_text(serialized, encoding='utf-8')
        status = 'completa'
        return result
    finally:
        run.finish(status)


def load(cache):
    cache = Path(cache)
    result = json.loads((cache/ARTIFACT).read_text(encoding='utf-8'))
    if result['script_sha256'] != file_hash(__file__):
        raise RuntimeError('Regenera la comparación por estudiante: cambió su protocolo/código.')
    for name, digest in result['input_sha256'].items():
        if file_hash(cache/name) != digest:
            raise RuntimeError('Comparación por estudiante desactualizada: '+name)
    return result


METHOD = r"""
**Pregunta e hipótesis.** Seis comparaciones bilaterales, todos los clásicos
contra SVM, incluidos los descartados por MCS. H₀: media de diferencias MSE por
estudiante = 0. No se usa Friedman/MCS de CV como puerta para contrastes de test.
La familia, α = 0.05, 49.999 réplicas y semilla 20261018 se fijaron antes de
este cálculo; el test y sus métricas ya habían sido revisados anteriormente.

**Unidad y ponderación.** Cada estudiante es una unidad. Primero se promedia
el error cuadrático de todos sus registros para cada modelo. Después se
promedian las pérdidas de estudiantes con pesos iguales. RMSE es la raíz de
esa media, no la media de raíces por estudiante. Si hay registros repetidos,
esta ponderación puede diferir de las métricas por registro del dashboard.
La vinculación de estudiantes se reconstruye privadamente, comprobando orden,
predictores, objetivo, periodo y hashes de los artefactos activos. No se exportan IDs.

**Contraste bootstrap-t.** dᵢ = MSEᵢ,modelo − MSEᵢ,SVM;
t observado = media(d)/(SD(d)/√n), SD muestral. Se sortean n estudiantes con
reemplazo, usando los mismos índices en todos los modelos. Para cada réplica,
t* = [media(d*) − media(d)]/[SD(d*)/√n]: el numerador se centra bajo H₀.
p bilateral = [1 + número de |t*| ≥ |t observado|]/(B + 1).
Se reporta su error Monte Carlo aproximado √[p(1−p)/B]; no es un IC del efecto.
Las réplicas con SE cero usan t* = 0 si el numerador es cero, ±infinito en otro
caso, y se contabilizan para auditoría. Diferencias observadas constantes no
nulas dejan el contraste no estimable; pérdidas idénticas dan p = 1.

**Holm–Bonferroni.** Los seis p crudos forman una única familia, sin filtrarla
por MCS, signo o significancia. Se ordenan, se multiplican por 6,5,…,1 y se
aplica máximo acumulado, limitado a 1. Los contrastes no estimables conservan
su lugar en la familia y se muestran como no estimables. La conclusión usa
p Holm < 0.05; el signo de ΔMSE determina mejora/deterioro. «Diferencia no
detectada» no significa equivalencia. Holm solo controla multiplicidad si los
p originales están calibrados; no subsana dependencia o sesgos del diseño.

**Intervalos y efecto.** IC BCa95 individuales para ΔMSE y ΔRMSE, con las mismas
réplicas emparejadas y jackknife retirando un estudiante completo cada vez.
El sesgo z₀ usa la proporción de réplicas menores que la estimación, con medio
peso a empates; la aceleración se obtiene del jackknife. Se informa cuando BCa
es degenerado/inestable; no se sustituye por un percentil en silencio.
Estos IC no son simultáneos ni determinan la decisión de Holm; pueden diferir
de ella. Cohen d_z = media(d)/SD(d), descriptor emparejado sin suponer simetría
para el contraste bootstrap. Negativo favorece al clásico. No hay umbral
educativo de relevancia práctica acordado.

**Alcance.** Análisis exploratorio posterior a inspección del test202530,
condicionado a estos modelos ya entrenados y a estudiantes de este periodo.
Requiere estudiantes independientes e información suficiente en sus pérdidas;
no se ha demostrado ausencia de dependencia compartida por clase/cohorte.
Agrupar registros no corrige esa posible dependencia. No incluye variabilidad
de entrenamiento, cambios de periodo ni incertidumbre por selección previa.
No se reelige familia, método o hiperparámetros con estos resultados.

**Referencias:** [Contrastes bootstrap bajo H₀](https://www.stat.cmu.edu/~cshalizi/uADA/19/lectures/ch06.pdf),
[BCa y remuestreo emparejado](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html),
[Holm–Bonferroni](https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html).
"""


def section(result, ui):
    """Etapa 3 vigente de Clásicos: contraste tipo Diebold–Mariano por estudiante."""
    from student_dm import render
    return html.Div(render(result['dm'], ui, scope='Clásicos', mcs_label='Etapa 2'), className='student-svm-comparison')


if __name__ == '__main__':
    from prepare_data import CACHE, BOOK, ACTIVE_RESULTS
    result = prepare(CACHE, BOOK, ACTIVE_RESULTS)
    manifest_path = CACHE/'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest['artifact_sha256'][ARTIFACT] = file_hash(CACHE/ARTIFACT)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({'analysis_run': result['analysis_run'], 'n_students': result['n_students'],
                      'rows': result['rows']}, ensure_ascii=False, indent=2))

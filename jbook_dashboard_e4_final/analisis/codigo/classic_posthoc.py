"""Friedman/MCS de folds guardados, más presentación de contrastes test separados.

MCS T_R con eliminación e_R de Hansen–Lunde–Nason. El bootstrap emparejado
enumera los n**n remuestreos de folds (3125 para n=5). La independencia de
estos bloques NO se cumple por el solapamiento del entrenamiento: los p MCS
son exploratorios y no proporcionan cobertura nominal del 90 %.
"""
from itertools import combinations, product

import numpy as np
import pandas as pd
from dash import html

from classic_friedman import friedman_comparison
from student_comparison import section as student_section


def fold_panel(folds, models):
    # Comparte la validación estricta del ómnibus: sin omisiones silenciosas.
    friedman_comparison(folds, models)
    return (folds.loc[folds.Modelo.isin(models)]
            .pivot(index='Fold', columns='Modelo', values='RMSE')
            .reindex(columns=list(models)).sort_index())


def bootstrap_indices(n):
    if n < 2 or n**n > 100_000:
        raise ValueError('La enumeración exacta requiere entre 2 y 6 folds.')
    return np.array(list(product(range(n), repeat=n)), dtype=int)


def standardized(values, se):
    """0/0 = 0 para pérdidas idénticas; diferencias constantes dan ±inf."""
    result = np.zeros_like(values, dtype=float)
    np.divide(values, se, out=result, where=se > 0)
    np.copyto(result, np.inf, where=(se == 0) & (values > 0))
    np.copyto(result, -np.inf, where=(se == 0) & (values < 0))
    return result


def mcs_range(losses, indices, alpha=.10):
    """Matriz fold × modelo de MSE; mismos índices en todas las eliminaciones."""
    x = losses.to_numpy(dtype=float)
    if not 0 < alpha < 1 or not np.isfinite(x).all():
        raise ValueError('Pérdidas finitas y 0 < alfa < 1 requeridos.')
    mean = x.mean(axis=0)
    # Centrar primero evita redondeo de medias bootstrap de diferencias constantes.
    centered = (x - x[0]) - (x - x[0]).mean(axis=0)
    boot = centered[indices].mean(axis=1)
    pair_boot = boot[:, :, None] - boot[:, None, :]
    se = pair_boot.std(axis=0, ddof=0)
    observed = standardized(mean[:, None] - mean[None, :], se)
    simulated = standardized(pair_boot, se)
    active = list(range(x.shape[1]))
    pvalues = np.ones(x.shape[1])
    order = np.zeros(x.shape[1], dtype=int)
    monotone_p = 0.
    for step in range(1, x.shape[1]):
        stat = np.abs(observed[np.ix_(active, active)]).max()
        reference = np.abs(simulated[:, active][:, :, active]).max(axis=(1, 2))
        p = float(np.mean(reference >= stat))
        monotone_p = max(monotone_p, p)
        # e_R = argmax_i max_j t_ij; positivo significa más pérdida.
        worst = active[int(np.argmax(observed[np.ix_(active, active)].max(axis=1)))]
        pvalues[worst], order[worst] = monotone_p, step
        active.remove(worst)
    order[active[0]] = x.shape[1]
    return pd.DataFrame({
        'Modelo': losses.columns,
        'Rango promedio de pérdida': losses.rank(axis=1, method='average').mean().to_numpy(),
        'MSE medio CV': mean,
        'p-valor MCS exploratorio': pvalues,
        'En MCS exploratorio (α = 0.10)': np.where(pvalues >= alpha, 'Sí', 'No'),
        'Paso de eliminación': order,
    }).sort_values('Rango promedio de pérdida', kind='stable').reset_index(drop=True)


def effect_sizes(a, b):
    """Cliff marginal y Cohen d_z emparejado, ambos sobre MSE de fold."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    delta = float(np.sign(a[:, None] - b[None, :]).mean())
    difference = a - b
    sd = difference.std(ddof=1)
    dz = float(difference.mean()/sd) if sd > 0 else np.nan
    return delta, dz


def analyze(folds, models, omnibus):
    rmse = fold_panel(folds, list(models))
    losses = rmse**2
    indices = bootstrap_indices(len(losses))
    significant = np.isfinite(omnibus['pvalue']) and omnibus['pvalue'] < .05
    mcs = mcs_range(losses, indices) if significant else pd.DataFrame()
    # Orden descriptivo por RMSE medio: el mismo criterio que la tabla principal.
    ordered = rmse.mean().sort_values(kind='stable').index.tolist()
    finalists = (mcs.loc[mcs['En MCS exploratorio (α = 0.10)'].eq('Sí'), 'Modelo'].tolist()
                 if significant else [])
    pair_rows, effect_rows = [], []
    for a, b in combinations([name for name in ordered if name in finalists], 2):
        d = (losses[a] - losses[b]).to_numpy()
        low, high = np.quantile(d[indices].mean(axis=1), [.025, .975])
        pair_rows.append({'Modelo A': a, 'Modelo B': b, 'Δ MSE (A − B)': d.mean(),
                          'IC 95% inferior · folds': low, 'IC 95% superior · folds': high})
    # Incluye todos los pares y no solo los seleccionados: evita ocultar efectos.
    for a, b in combinations(ordered, 2):
        delta, dz = effect_sizes(losses[a], losses[b])
        effect_rows.append({'Modelo A': a, 'Modelo B': b,
                            'Δ MSE (A − B)': (losses[a] - losses[b]).mean(),
                            'Delta de Cliff': delta, 'd de Cohen emparejado (d_z)': dz})
    return {'mcs': mcs, 'pairs': pd.DataFrame(pair_rows), 'effects': pd.DataFrame(effect_rows),
            'finalists': finalists, 'top_two': ordered[:2], 'significant': significant,
            'resamples': len(indices)}


METHOD = r"""
**Etapa 1 · Prueba global (ómnibus).** H₀: rangos promedio iguales. Friedman
ordena el RMSE dentro de cada fold (rango 1 = menor error, empates promediados).
Con α = 0.05, solo un rechazo permite abrir el post hoc exploratorio. Si no se
rechaza, no hay evidencia suficiente para afirmar superioridad; tampoco prueba equivalencia.

**Etapa 2.1 · Model Confidence Set (MCS).** Universo completo: seis clásicos
y SVM. Pérdida = MSE de cada fold = RMSE²; cada fold pesa igual. Se contrasta
igual capacidad predictiva en el conjunto restante usando T_R = max |t_ij|,
t_ij = media(L_i − L_j) / SE_bootstrap(media(L_i − L_j)). Se elimina
argmax_i max_j t_ij y se repite hasta un único modelo; los p MCS se acumulan
con máximo monótono y el último recibe 1. Se retienen p ≥ 0.10.
Se enumeran los **3.125 remuestreos posibles de cinco folds con reemplazo**,
emparejados entre modelos y reutilizados en cada paso, centrados bajo H₀.
No hay semilla ni error Monte Carlo. La desviación bootstrap usa ddof = 0;
una diferencia constante no nula tiene t infinito y una idéntica tiene t = 0.
El rango de pérdida coincide con Friedman, pero la media MSE puede ordenar
distinto que la media RMSE. **Es una adaptación exploratoria**: cinco folds
con entrenamientos solapados no son bloques independientes. El remuestreo no
corrige esa dependencia y **no garantiza cobertura del 90 %**, ni produce un
subconjunto confirmatorio defendible. Un p MCS no es la probabilidad de que un modelo sea el mejor.

**Etapa 2.2 · Giacomini–White / Clark–West.** GW evalúa capacidad predictiva
condicional e incorpora incertidumbre de estimación; puede admitir modelos
anidados y no anidados, bajo sus condiciones. CW ajusta la diferencia de MSE
para comparar un modelo parsimonioso con una ampliación anidada adecuada.
Compartir predictores no demuestra anidamiento entre algoritmos penalizados,
árboles o kernels. Aquí no se ha establecido una pareja restringida/ampliada,
una secuencia de orígenes de pronóstico ni instrumentos condicionales definidos
antes de evaluar: ambos contrastes quedan **no aplicables al diseño actual**.

**Etapa 2.3 · Diebold–Mariano con corrección HLN (adaptado) y bootstrap estacionario.**
DM contrasta que el diferencial medio de pérdida entre dos predictores sea cero
con una varianza que recoge su dependencia; HLN corrige por tamaño de muestra y
por el horizonte h de los pronósticos. En su forma original supone una serie
temporal ordenada de pronósticos. Aquí no la hay: el índice de fold y el orden de
filas no constituyen tiempo, y con cinco folds solapados la prueba tendría solo
cinco observaciones. Se usa, por eso, una **adaptación por estudiante**: la observación
es el estudiante (suma de las diferencias de error cuadrático de sus registros),
las pérdidas son las predicciones fuera de muestra de la validación cruzada
(1.293 estudiantes), el error estándar es robusto por estudiante en lugar
de HAC (casi cada estudiante tiene un solo registro, por lo que equivale en la práctica
a una prueba pareada), y la corrección HLN se aplica con h = 1 —no hay pronósticos solapados que
justifiquen un horizonte mayor—: z·√((G−1)/G) con una t de Student de G−1 grados
de libertad. El IC95 sale de remuestrear estudiantes. El **bootstrap estacionario**
sigue sin aplicar: requiere una secuencia estacionaria y una longitud de bloque
justificada. Cada comparación se contrasta de forma independiente y **sin
ajuste de Holm**; los resultados (los cinco primeros del MCS frente al SVM) están
en la Etapa 3 y los IC por folds entre finalistas se conservan como descripción
(3.125 remuestreos). La adaptación no incluye la variabilidad de reentrenar y
los modelos se eligieron con la misma validación: es exploratoria. El orden se
define por RMSE medio CV, nunca por test.

**Tamaño del efecto.** La significancia no implica relevancia práctica.
Delta de Cliff = P(L_A > L_B) − P(L_A < L_B), calculado con las 25 comparaciones
cruzadas de MSE de cinco folds; está entre −1 y 1. Resume dominancia **marginal**,
no conserva el emparejamiento y no equivale a una prueba pareada.
Cohen emparejado d_z = media(L_A − L_B) / SD(L_A − L_B), SD muestral (ddof = 1).
Se informa como descriptor estandarizado; con cinco diferencias no se puede
establecer simetría con fiabilidad. No se usa como evidencia paramétrica;
si SD = 0 figura «No estimable». Negativos favorecen A en ambas medidas.
Se incluye Δ MSE en puntos de nota² para valorar magnitud absoluta, sin imponer
un umbral educativo no acordado. Los 21 pares se muestran sin pruebas de
significancia ni etiquetas automáticas de relevancia.

**Incertidumbre.** Los IC de diferencias por folds son percentiles 2.5/97.5 de
los mismos 3.125 remuestreos emparejados. Son condicionales y exploratorios,
no simultáneos ni corregidos por selección del MCS; no capturan incertidumbre
de reentrenamiento. La tabla principal de métricas reutiliza los IC del test
ya exportados: bootstrap por estudiante, 1.000 réplicas, modelos fijos. Son
descriptivos, no intervienen en Friedman, MCS o selección y tampoco permiten
elegir un ganador porque sus intervalos se solapen o dejen de solaparse.

**Referencias:** [Friedman · SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.friedmanchisquare.html),
[Hansen, Lunde y Nason · MCS](https://doi.org/10.3982/ECTA5771),
[Giacomini y White](https://doi.org/10.1111/j.1468-0262.2006.00718.x),
[Clark y West](https://www.kansascityfed.org/documents/5368/pdf-RWP05-05.pdf),
[Harvey, Leybourne y Newbold](https://doi.org/10.1016/S0169-2070(96)00719-4).
"""


def section(result, omnibus, report, ui, student_result=None, friedman_detail=(), nemenyi_block=None):
    md, table = ui['md'], ui['table']
    reject = result['significant']
    global_table = pd.DataFrame([{'Estadístico de Friedman (χ²)': omnibus['statistic'],
                                 'g.l.': omnibus['df'], 'p-valor asintótico': omnibus['pvalue'],
                                 'Conclusión': 'Se rechaza H₀ · exploratorio' if reject else
                                 'No estimable' if not np.isfinite(omnibus['pvalue']) else 'No se rechaza H₀'}])
    if reject:
        verdict = ('El ómnibus abre el post hoc exploratorio. El MCS conserva **'
                   + ', '.join(result['finalists']) + '** (α = 0.10). '
                   'Este conjunto no tiene cobertura del 90 % demostrada por la dependencia entre folds. ')
    else:
        verdict = ('No se abre el post hoc: el ómnibus no aporta evidencia suficiente. '
                   'Las diferencias y tamaños de efecto siguen siendo descriptivos. ')
    verdict += ('El menor RMSE medio CV corresponde a **' + result['top_two'][0]
                + '** y el segundo a **' + result['top_two'][1]
                + '**. Las comparaciones por folds no confirman superioridad por pares; GW/CW y el IC estacionario '
                  'no son aplicables con los artefactos actuales, y el DM-HLN se usa en una versión adaptada por estudiante '
                  '(ver Etapa 3). '
                  'La elección final no usa test, tiempos ni estos contrastes exploratorios.')
    ci = pd.DataFrame(report['bootstrap'])
    names = result['effects']['Modelo A'].tolist() + result['effects']['Modelo B'].tolist()
    ci = ci.loc[ci['Modelo'].isin(names) & ci['Métrica'].eq('RMSE')].copy()
    ci = ci.rename(columns={'IC 2.5%': 'IC 95% inferior', 'IC 97.5%': 'IC 95% superior'})
    ci['Evaluación'] = 'Test temporal · descriptivo'
    status = pd.DataFrame([
        {'Paso': 'MCS · universo completo', 'Estado': 'Calculado · exploratorio' if reject else 'Bloqueado por ómnibus',
         'Alcance': 'MSE de 5 folds; sin cobertura nominal garantizada'},
        {'Paso': 'Giacomini–White / Clark–West', 'Estado': 'No aplicable',
         'Alcance': 'Sin diseño de pronóstico/instrumentos ni anidamiento establecido'},
        {'Paso': 'DM-HLN adaptado por estudiante', 'Estado': 'Calculado · adaptación exploratoria',
         'Alcance': 'Ver Etapa 3: top 5 del MCS frente al SVM; predicciones de CV; HLN con h = 1; sin Holm'},
        {'Paso': 'IC bootstrap estacionario', 'Estado': 'No aplicable',
         'Alcance': 'Sin secuencia estacionaria ni longitud de bloque justificada'},
    ])
    effects = result['effects'].copy()
    effects['d de Cohen emparejado (d_z)'] = effects['d de Cohen emparejado (d_z)'].map(
        lambda value: round(value, 6) if np.isfinite(value) else 'No estimable')
    return html.Article([
        html.H3('Conclusiones y comparación estadística · CV global'),
        md('**Ejecución activa:** ' + report.get('run_id', 'Grid histórico') + '. '
           'Friedman/MCS: siete regresores y cinco folds externos, sin test. '
           'La Etapa 3 contrasta por estudiante, sobre las predicciones fuera de muestra de la validación cruzada, '
           'los cinco primeros del MCS frente al SVM; es exploratoria.'),
        md(verdict),
        html.H4('Etapa 1 · Prueba global de Friedman'), table(global_table), *friedman_detail, nemenyi_block,
        html.H4('Etapa 2 · Model Confidence Set (MCS)'),
        md('**Resultado exploratorio, no conjunto confirmatorio al 90 %.** Menor rango = menor pérdida; '
           'p MCS ≥ 0.10 conserva el modelo dentro de esta adaptación. La tabla se ordena por rango promedio; '
           '**Paso de eliminación** indica el orden en que el MCS descarta modelos (1 = primero, el mayor = sobreviviente). '
           'Ese orden usa el estadístico t estandarizado de las diferencias de MSE entre pares, no el MSE medio: '
           'un modelo con peor promedio puede salir después si sus diferencias son más variables entre folds.'),
        table(result['mcs']) if reject else md('Post hoc no ejecutado: no se rechaza H₀ o Friedman no es estimable.'),
        html.H4('Comparaciones dirigidas entre finalistas · métodos explorados'),
        md('Tras el MCS se exploraron las formas habituales de comparar modelos de manera dirigida; la tabla indica cuáles aplican a este '
           'diseño. Solo se calcula una adaptación del DM-HLN por estudiante: su justificación, la adaptación realizada y sus resultados están '
           'en la **Etapa 3**, más abajo. Los intervalos por folds entre finalistas se conservan como descripción.'),
        table(status),
        html.Details([html.Summary('IC descriptivos por folds entre finalistas'),
            md('Δ MSE = pérdida A − pérdida B; negativo favorece A. Intervalos percentiles de los 3.125 remuestreos de folds, '
               '**no estacionarios**: describen la dispersión entre folds y no justifican decisiones de significancia ni llevan '
               'ajuste por selección.'),
            table(result['pairs']) if not result['pairs'].empty else md('No hay pares de finalistas para comparar.')],
            className='details'),
        student_section(student_result, ui) if student_result is not None else None,
        html.H4('Tamaño del efecto · pérdidas MSE por fold'),
        md('Delta de Cliff describe dominancia marginal; Cohen d_z estandariza las diferencias emparejadas. '
           'Negativo favorece A. Con cinco folds son descriptores, sin afirmar simetría ni relevancia educativa. '
           'Consultar las fórmulas y límites en la documentación.'),
        html.Details([html.Summary('Ver los 21 pares · Cliff, Cohen y diferencia absoluta'), table(effects)], className='details'),
        html.H4('IC del 95 % de RMSE · test temporal descriptivo'),
        md('Bootstrap por estudiante ya exportado, 1.000 réplicas, pipelines fijos. '
           'Esta tabla resume incertidumbre del test; no selecciona modelos ni completa el post hoc de CV.'),
        table(ci),
        html.Details([html.Summary('Documentación · hipótesis, secuencia, fórmulas, supuestos y referencias'),
                      md(METHOD)], className='details'),
    ], className='card classic-statistical-conclusions')

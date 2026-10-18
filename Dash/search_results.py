"""Documentación, evidencia comparativa y tiempos de las búsquedas de E3."""
import json
import pandas as pd
import plotly.express as px
from dash import html

METHODOLOGY = '''
**Selección conjunta, sin test.** Dentro de cada entrenamiento externo se ejecutan
las cinco estrategias sobre los mismos cinco folds internos por estudiante.
Se elige el menor **RMSE medio interno a fidelidad completa** entre todos sus
candidatos válidos; los empates ≤1e-12 siguen el orden Grid, Random, TPE, DEAP,
Halving. Se repite el procedimiento en todo train para el ajuste final.
Los cinco folds externos evalúan ese proceso completo, incluida la elección
del método; sus métricas no seleccionan parámetros finales.

**Grid Search y Random Search.** Se conserva el grid exhaustivo original.
Random evalúa 16 sorteos: uniforme en categorías/enteros e intervalos lineales,
loguniforme en C, alpha y learning_rate. Los otros métodos exploran estos mismos
intervalos, además del grid discreto que se mantiene visible. Por tanto,
no es una comparación de algoritmos a igual presupuesto ni garantiza óptimo global.

**Bayesiana · Optuna.** Surrogate **Tree-structured Parzen Estimator (TPE)**:
estima densidades l(x) de configuraciones buenas y g(x) de las restantes.
Se elige TPE para estos dominios mixtos (categorías, enteros y continuos
logarítmicos), sin imponer una distancia ordinal o un kernel GP a las categorías.
La adquisición es **Mejora Esperada (Expected Improvement)** mediante el cociente
l(x)/g(x). No usa proceso gaussiano ni UCB/PI. De sus 20 ensayos, los primeros
6 son aleatorios para explorar; después propone según TPE, con 24 candidatos
para aproximar EI. Favorece explotar regiones prometedoras, manteniendo
exploración por muestreo y densidades probabilísticas; estos presupuestos
pequeños no garantizan convergencia. EI se elige porque busca reducir el mejor
RMSE encontrado considerando la ganancia esperada; no solo la probabilidad de
mejorar, como PI, ni una cota de confianza, como UCB. Estos presupuestos
son exploratorios. Cada ensayo crea y ajusta manualmente
un pipeline nuevo en cada fold interno, sin transformar previamente todo train.
[TPE y EI en Optuna](https://optuna.readthedocs.io/en/stable/reference/samplers/generated/optuna.samplers.TPESampler.html).

**Genética · DEAP.** Población de 8 y 3 generaciones después de la inicial.
Selección por **torneo de 3**: funciona con RMSE minimizado y controla la
presión selectiva sin requerir fitness positiva, como la ruleta.
Cruce **uniforme** con probabilidad de pareja 0.8 y de intercambio por gen 0.5:
recombina dimensiones sin suponer proximidad ordinal entre categorías.
Mutación por **reinicio uniforme** de un individuo con probabilidad 0.3;
cada gen se reinicia con probabilidad 1/d. Genes continuos normalizados se
decodifican al dominio, con escala logarítmica cuando corresponde.
Elitismo: se conserva **1 mejor individuo**; limita la pérdida de buenas
soluciones dejando 7 puestos para variación. Fitness: pipeline nuevo por fold,
preprocesamiento ajustado solo con su entrenamiento. Duplicados dentro del
método/fold/fidelidad reutilizan fitness, sin compartir caché entre estrategias.
Se reportan diversidad de configuraciones únicas y entropía media por gen;
una caída junto con estancamiento es señal de posible convergencia prematura,
no demostración. Ocho individuos y tres generaciones son un presupuesto
exploratorio deliberado; no certifican convergencia.
[Operadores DEAP](https://deap.readthedocs.io/en/master/api/tools.html).

**Multi-fidelidad · Successive Halving manual.** 16 configuraciones → 8 → 4;
factor de reducción **2**, con **25 %, 50 % y 100 % de grupos de estudiantes
del entrenamiento interno**. Se seleccionan grupos completos, anidados y
reproducibles, sin mirar y para muestrear; la validación interna permanece
completa e idéntica en todas las rondas. Ahorrar filas reduce preparación y fit
también en modelos sin árboles/épocas. No se truncan los registros de una persona
ni se reajusta un transformador aprendido en una ronda previa. La fidelidad
parcial puede ordenar mal configuraciones: solo los cuatro supervivientes
evaluados al 100 % compiten contra los otros métodos para el ajuste final.
[Eliminación sucesiva en scikit-learn](https://scikit-learn.org/stable/modules/grid_search.html#successive-halving).

**Tiempos y límites.** Segundos de pared CPU con perf_counter; búsqueda incluye
preparación, scoring, coordinación y registro, y excluye refit. Cuatro procesos
para folds internos, un hilo por proceso; estrategias y ensayos secuenciales.
Los tiempos de fits paralelos no se suman como tiempo de búsqueda. Refits y
predict se miden por separado. Una repetición por lote, sin calentamiento
explícito, estado frío/caliente no controlado. Datos/CPU/paralelismo condicionan
estas medidas; el tiempo no elige hiperparámetros. Test 202530 ya fue consultado
en trabajos anteriores: su reevaluación es descriptiva, no una nueva prueba ciega.
'''


def optimization_section(spec, ui):
    optimization = spec.get('optimization')
    if not optimization:
        return ui['md']('Esta ejecución histórica usó únicamente Grid Search; tiempos no medidos salvo evidencia registrada.')
    md, table, card = (ui[k] for k in ['md', 'table', 'card'])
    methods = pd.DataFrame([{
        'Método': row['method'] + (' · elegido' if row['method'] == optimization['selected_method'] else ''),
        'RMSE interno final': f'{row["RMSE"]:.8f}',
        'SD RMSE interno': f'{row["sd_RMSE"]:.6f}', 'Evaluaciones configuración/fidelidad': row['evaluated_configurations'],
        'Al 100 %': row['full_configurations'], 'Fits fallidos': row['failed_fits'],
        'Búsqueda final (s)': row['search_seconds'],
        'Búsquedas en 5 folds externos (s)': sum(next(r['search_seconds'] for r in outer['methods'] if r['method'] == row['method'])
                                                  for outer in optimization['external_selections'])
    } for row in optimization['methods']])
    space = pd.DataFrame([{'Parámetro': p.replace('modelo__', ''),
                           'Dominio estocástico': str(domain),
                           'Elección conjunta final': str(spec['best_params'][p])}
                          for p, domain in optimization['space'].items()])
    timings = optimization.get('timings', [])
    refits = pd.DataFrame([{'Ajuste': row['batch'], 'Filas': row['rows'],
                           'Entrenamiento/refit (s)': row['seconds'], 'Estado': row['status']}
                          for row in timings if row['stage'] == 'Entrenamiento/refit'])
    evolution = pd.DataFrame(optimization['evolution']).rename(columns={
        'generation': 'Generación', 'best_RMSE': 'Mejor RMSE', 'mean_RMSE': 'RMSE medio',
        'unique_fraction': 'Fracción única', 'gene_entropy': 'Entropía genética'})
    first, last = evolution.iloc[0], evolution.iloc[-1]
    stalled = len(evolution) > 1 and abs(last['Mejor RMSE']-evolution.iloc[-2]['Mejor RMSE']) <= 1e-12
    reduced = last['Fracción única'] < first['Fracción única'] or last['Entropía genética'] < first['Entropía genética']
    reading = (f'Fracción única: **{first["Fracción única"]:.3f} → {last["Fracción única"]:.3f}**; '
               f'entropía media: **{first["Entropía genética"]:.3f} → {last["Entropía genética"]:.3f}**. ')
    reading += ('Se reduce la diversidad y la mejor fitness se estanca en la última generación: '
                'son señales de posible convergencia prematura, sin demostrarla.' if stalled and reduced else
                'La trayectoria no reúne pérdida de diversidad y estancamiento final simultáneamente; '
                'tres generaciones no bastan para descartar convergencia prematura ni demostrar convergencia.')
    return html.Div([
        md(f'**Elección conjunta final: {optimization["selected_method"]}**, '
           f'RMSE interno **{spec["selection_rmse"]:.6f}**. Se compara contra todos los métodos, '
           'incluido Grid Search. Este RMSE es de selección; la evaluación OOF está fuera de la búsqueda.'),
        html.Details([html.Summary('Protocolo, surrogate, adquisición y operadores'), md(METHODOLOGY)], className='details'),
        table(space), table(methods),
        md('La columna de folds externos suma cinco búsquedas secuenciales completas de ese método; '
           'no suma los tiempos internos que corren en paralelo. No incluye la búsqueda final en todo train.'),
        html.Details([html.Summary('Mejores parámetros por estrategia · búsqueda final'),
            *[md(f'**{row["method"]}:** `{json.dumps(row["best_params"], ensure_ascii=False)}`') for row in optimization['methods']]
        ], className='details'),
        card('Diversidad genética · búsqueda final',
             'Fracción de configuraciones distintas y entropía media de genes (0–1). '
             'Para continuos se usan 10 intervalos; categorías y enteros conservan sus valores. '
             'Una caída sostenida con estancamiento sugiere convergencia prematura.',
             px.line(evolution.melt(id_vars='Generación', value_vars=['Fracción única', 'Entropía genética'],
                                   var_name='Indicador', value_name='Diversidad'),
                     x='Generación', y='Diversidad', color='Indicador', markers=True, range_y=[0, 1.05])),
        table(evolution), md(reading),
        html.Details([html.Summary('Diversidad DEAP y método elegido en cada fold externo'),
            *[html.Div([md(f'**Fold externo {i}: {outer["selected_method"]}**, RMSE interno {outer["selection_rmse"]:.6f}.'),
                        table(pd.DataFrame(outer['evolution']))]) for i, outer in enumerate(optimization['external_selections'], 1)]
        ], className='details'),
        html.H4('Tiempos de entrenamiento/refit · segundos de pared'), table(refits),
        md(f'Ejecución **{spec.get("timing_run_id", spec.get("run_id", "ver manifiesto"))}**. '
           'Registro central: TIEMPOS_EJECUCION.md; configuración, folds, ensayos y fallos se conservan en la evidencia del experimento.'),
    ], className='optimization-results')

"""Convierte los CSV de `salidas/` en tablas MyST (`tablas/*.md`) que los capítulos incluyen.

Las tablas no se escriben a mano: cada una sale de un CSV versionado. Formato en español
(coma decimal, punto de miles). Ejecutar después de los scripts de análisis.
"""
import json

import numpy as np
import pandas as pd

from comun import OUT, RESULTS

TABLES = OUT.parent / 'tablas'
HER = OUT / 'heredadas'


def num(value, digits=4):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return '—'
    if isinstance(value, (bool, np.bool_)):
        return 'Sí' if value else 'No'
    if isinstance(value, (int, np.integer)):
        return f'{value:,}'.replace(',', '.')
    text = f'{value:,.{digits}f}'
    return text.replace(',', '§').replace('.', ',').replace('§', '.').replace('-', '−')


def pval(p):
    if p is None or (isinstance(p, float) and np.isnan(p)):
        return '—'
    return '< 0,0001' if p < 1e-4 else num(float(p), 4)


def pm(mean, sd, digits=4):
    return f'{num(mean, digits)} ± {num(sd, digits)}'


def write(name, caption, label, header, rows, align=None):
    align = align or ['---'] + ['---:'] * (len(header) - 1)
    lines = [f':::{{table}} {caption}', f':label: {label}', '',
             '| ' + ' | '.join(header) + ' |', '| ' + ' | '.join(align) + ' |']
    lines += ['| ' + ' | '.join(str(c).replace('|', '\\|') for c in r) + ' |' for r in rows]
    lines += [':::', '']
    (TABLES / f'{name}.md').write_text('\n'.join(lines), encoding='utf-8')


H0 = {
    'Wilcoxon por fold': ('Mediana de las diferencias de RMSE por fold = 0',
                          'Diferencias simétricas; pares por fold. No se cumple la independencia (entrenamientos solapados); p mínimo bilateral con n = 5: 0,0625'),
    'Permutación pareada por estudiante': ('Las etiquetas de modelo son intercambiables dentro de cada estudiante (Δ MSE = 0)',
                                           'Estudiantes independientes (1.293; 16 con dos filas agrupadas); no requiere normalidad'),
    't corregida de Nadeau–Bengio': ('Δ RMSE esperado = 0 al reentrenar con otros datos',
                                     'Normalidad aproximada de 5 diferencias; corrige el solapamiento con n_val/n_fit = 0,25'),
    'Bootstrap pareado BCa': ('Δ RMSE = 0 (el IC 95 % BCa contiene el 0)',
                              'Estudiantes intercambiables; corrige sesgo y asimetría (BCa); modelos fijos'),
    'Diebold–Mariano por estudiante (HLN)': ('Δ MSE medio = 0',
                                             'Adaptación de corte transversal: SE robusto por estudiante y corrección HLN (h = 1); modelos fijos'),
}


def conclusion(p, delta, alpha=.05):
    if p >= alpha:
        return 'No se rechaza H0'
    return 'Original mejor' if delta < 0 else 'Original peor'


def main():
    TABLES.mkdir(exist_ok=True)
    part = json.loads((RESULTS / 'particion.json').read_text(encoding='utf-8'))
    write('conteos', 'Conteos por etapa del ETL (`resultados/e3/particion.json`).', 'tab-conteos',
          ['Etapa', 'Registros', 'Estudiantes', 'Observación'],
          [['Fuente `Datos_Brutos.csv` (6 periodos, 31 columnas)', num(part['source_rows']), num(part['source_students']), '2023–2025'],
           ['Sin nota del primer parcial', num(part['missing_target']), '—', 'Excluidas del aprendizaje supervisado'],
           ['Con objetivo', num(part['source_rows'] - part['missing_target']), '—', 'Base de la partición'],
           ['Purga de estudiantes del periodo reservado', num(part['purged_overlap_rows']), num(part['purged_overlap_students']), 'Ningún estudiante en ambos lados'],
           ['Incumplimientos de reglas de negocio (train / test)', f"{sum(part['rules_train'].values())} / {sum(part['rules_test'].values())}", '—', 'Ninguna fila excluida'],
           ['Train válido (202310–202510)', num(part['train_valid']), num(part['train_students']), 'EDA, búsqueda y validación anidada'],
           ['Test temporal (202530)', num(part['test_valid']), num(part['test_students']), 'Solo evaluación final'],
           ['Atípicos eliminados', num(part['outliers_removed']), '—', 'Se conservan los valores extremos válidos']],
          ['---', '---:', '---:', '---'])

    combos = pd.read_csv(OUT / 'mejores_combinaciones.csv')
    write('mejores_combinaciones', 'Tabla maestra de mejores combinaciones de los 7 modelos base (bucle externo, media ± DE muestral de 5 folds).',
          'tab-mejores-combinaciones',
          ['#', 'Modelo', 'Método final', 'Método por fold (1–5)', 'Hiperparámetros finales', 'RMSE', 'MAE', 'R²', 'RMSE test', 'MCS (7)'],
          [[r['Posición'], f"**{r.Modelo}**" if r['Posición'] == 1 else r.Modelo, r['Método ganador (búsqueda final)'],
            r['Métodos por fold externo (1–5)'], r['Hiperparámetros finales'].replace('.', ','),
            pm(r['RMSE externo media'], r['RMSE externo DE']), pm(r['MAE externo media'], r['MAE externo DE']),
            pm(r['R² externo media'], r['R² externo DE']), num(r['RMSE test 202530 (descriptivo)']),
            f"{r['En MCS clásicos (7 modelos, α = 0,10)']} ({num(r['p MCS clásicos'], 3)})"] for _, r in combos.iterrows()],
          ['---:', '---', '---', '---', '---', '---:', '---:', '---:', '---:', '---'])
    write('tiempos_base', 'Tiempos de pared (s) de la ejecución activa de los modelos base, desde `tiempos/20261018_102325_af643f83/eventos.jsonl`.',
          'tab-tiempos-base',
          ['Modelo', 'Búsqueda final (5 estrategias)', 'Búsquedas externas (5 folds)', 'Refit final', 'Inferencia OOF (5 lotes)', 'Inferencia test (188 filas)'],
          [[r.Modelo, num(r['Búsqueda final, 5 estrategias (s)'], 2), num(r['Búsquedas externas, suma de 5 folds (s)'], 2),
            num(r['Refit final (s)'], 3), num(r['Inferencia OOF, 5 lotes (s)'], 3), num(r['Inferencia test, 188 filas (s)'], 4)]
           for _, r in combos.iterrows()])

    hpo = pd.read_csv(HER / 'clasicos' / 'hpo_resumen.csv')
    methods = ['Grid Search', 'Random Search', 'Bayesiana TPE', 'Genética DEAP', 'Successive Halving']
    rows = []
    for model in combos.Modelo:
        part = hpo.loc[hpo.Modelo.eq(model)].set_index('Método')
        rows.append([model] + [f"**{num(part.loc[m, 'RMSE interno'], 6)}**" if part.loc[m, 'Elegido'] else num(part.loc[m, 'RMSE interno'], 6)
                               for m in methods] + [num(part['SD interna'].min(), 3) + '–' + num(part['SD interna'].max(), 3)])
    write('hpo_rmse_interno', 'RMSE interno de la búsqueda final (media de 5 folds internos en todo train) por estrategia; en negrita, la elegida.',
          'tab-hpo-rmse-interno', ['Modelo', 'Grid', 'Random', 'TPE', 'DEAP', 'Halving', 'DE interna'], rows)

    short = dict(zip(methods, ['Grid', 'Random', 'TPE', 'DEAP', 'Halving']))

    def matrix(name, caption, label, frame, models, value, digits=2):
        rows = []
        for model in models:
            part = frame.loc[frame.Modelo.eq(model)].set_index('Método')
            rows.append([model] + [value(part.loc[m]) for m in methods])
        write(name, caption, label, ['Modelo', *[short[m] for m in methods]], rows)

    order_b = combos.Modelo.tolist()
    matrix('hpo_evaluaciones', 'Configuraciones evaluadas / ajustes de pipeline en la búsqueda final de cada modelo base (cada configuración a fidelidad completa cuesta 5 ajustes).',
           'tab-hpo-evaluaciones', hpo, order_b, lambda r: f"{int(r.Evaluaciones)} / {int(r['Ajustes internos'])}")
    matrix('hpo_tiempo_final', 'Tiempo de pared (s) de la búsqueda final en todo train, por modelo base y estrategia.',
           'tab-hpo-tiempo-final', hpo, order_b, lambda r: num(r['Búsqueda final (s)'], 2))
    matrix('hpo_tiempo_externas', 'Suma del tiempo de pared (s) de las cinco búsquedas en los folds externos, por modelo base y estrategia.',
           'tab-hpo-tiempo-externas', hpo, order_b, lambda r: num(r['5 búsquedas externas (s)'], 2))
    rows = []
    for model in order_b:
        part = hpo.loc[hpo.Modelo.eq(model)].set_index('Método')
        rows.append([model] + [num(part.loc[m, 's por evaluación'], 3) for m in methods] + [num(part.loc['Bayesiana TPE', 'fit interno medio (s)'], 4)])
    write('hpo_s_evaluacion', 'Segundos por evaluación (búsqueda final ÷ configuraciones; cada evaluación ajusta 5 pipelines en paralelo) y tiempo medio de un ajuste interno individual.',
          'tab-hpo-s-evaluacion', ['Modelo', *[short[m] for m in methods], 'Ajuste interno medio (TPE, s)'], rows)
    chosen = pd.read_csv(HER / 'clasicos' / 'hpo_metodo_por_busqueda.csv')['Método elegido'].value_counts()
    rows = []
    for m in methods:
        part = hpo.loc[hpo['Método'].eq(m)]
        final, outer = part['Búsqueda final (s)'].sum(), part['5 búsquedas externas (s)'].sum()
        rows.append([m, num(int(part['Ajustes internos'].sum())), num(int(part.Evaluaciones.sum())), num(part['Costo equivalente'].sum(), 1),
                     num(final, 2), num(outer, 2), num(final + outer, 2), f"{int(chosen.get(m, 0))} de {int(chosen.sum())}"])
    write('hpo_agregado', 'Consumo agregado por estrategia en los siete modelos base (búsqueda final y cinco búsquedas externas) y número de veces que fue elegida.',
          'tab-hpo-agregado', ['Estrategia', 'Ajustes internos (final)', 'Evaluaciones (final)', 'Costo equivalente completo',
                               'Tiempo final (s)', 'Tiempo 5 externas (s)', 'Total (s)', 'Veces elegida'], rows)
    hpo_o = pd.read_csv(HER / 'originales' / 'hpo_resumen.csv')
    names_o = {'m5': 'KRR centrado', 'm19': 'TN-KRR', 'm15': 'GPR–XGBoost'}
    rows = []
    for key, label in names_o.items():
        part = hpo_o.loc[hpo_o.Clave.eq(key)].set_index('Método')
        for col, title in (('RMSE interno', 'RMSE interno'), ('Evaluaciones', 'Evaluaciones'),
                           ('Búsqueda final (s)', 'Búsqueda final (s)'), ('5 búsquedas externas (s)', '5 externas (s)')):
            rows.append([label if col == 'RMSE interno' else '', title] + [
                (f"**{num(part.loc[m, col], 6)}**" if part.loc[m, 'Elegido'] else num(part.loc[m, col], 6)) if col == 'RMSE interno'
                else str(int(part.loc[m, col])) if col == 'Evaluaciones' else num(part.loc[m, col], 2) for m in methods])
    write('hpo_originales', 'Búsqueda final de los tres originales por estrategia: RMSE interno (en negrita, la elegida), configuraciones evaluadas y tiempos de pared. En el GPR–XGBoost los tiempos excluyen la etapa GPR, calculada una vez por conjunto de ajuste.',
          'tab-hpo-originales', ['Modelo', 'Medida', *[short[m] for m in methods]], rows, ['---', '---'] + ['---:'] * 5)

    summary = pd.read_csv(OUT / 'resumen_modelos.csv')
    write('resumen_modelos', 'Resumen de los 3 originales y los 7 modelos base: bucle externo (media ± DE), IC 95 % del RMSE OOF por bootstrap de estudiantes y tiempos de pared.',
          'tab-resumen-modelos',
          ['Modelo', 'Tipo', 'RMSE externo', 'MAE externo', 'IC 95 % RMSE OOF', 'RMSE test', 'Búsqueda final (s)', 'Refit (s)', 'Inferencia test (s)', 'Rango U10', 'p MCS U10'],
          [[f'**{r.Modelo}**' if r.Tipo == 'Original' else r.Modelo, r.Tipo, pm(r['RMSE externo media'], r['RMSE externo DE']),
            pm(r['MAE externo media'], r['MAE externo DE']),
            f"[{num(r['IC 95 % RMSE OOF (bootstrap estudiantes) inf'])}; {num(r['IC 95 % RMSE OOF (bootstrap estudiantes) sup'])}]",
            num(r['RMSE test 202530 (descriptivo)']), num(r['Búsqueda final (s)'], 2), num(r['Refit final (s)'], 3),
            num(r['Inferencia test 188 filas (s)'], 4), num(r['Rango Friedman (U10)'], 1), pval(r['p MCS (U10)'])]
           for _, r in summary.iterrows()],
          ['---', '---', '---:', '---:', '---:', '---:', '---:', '---:', '---:', '---:', '---:'])

    tests = pd.read_csv(OUT / 'pruebas_r3.csv')
    nem = pd.read_csv(OUT / 'nemenyi_u10_pares.csv')
    mcs = pd.read_csv(OUT / 'mcs_u10.csv').set_index('Modelo')
    meta = json.loads((OUT / 'pruebas_r3_meta.json').read_text(encoding='utf-8'))
    for key, label, ref, ref_name, suffix in [('m5', 'KRR centrado', 'xgboost', 'XGBoost', ''), ('m19', 'TN-KRR', 'xgboost', 'XGBoost', ''),
                                              ('m15', 'GPR–XGBoost', 'xgboost', 'XGBoost', ''), ('m19', 'TN-KRR', 'svm', 'SVM lineal', '_svm')]:
        part = tests.loc[tests.clave_original.eq(key) & tests.clave_base.eq(ref)]
        eff = part.iloc[0]
        effect = f"δ = {num(eff['Delta de Cliff (MSE por fold)'], 2)} ({eff['Magnitud Cliff']}); d_z = {num(eff['d_z de Cohen (MSE por fold)'], 2)}"
        rows = []
        for _, r in part.iterrows():
            h0, assumptions = H0[r.Prueba]
            stat = num(r['Estadístico'], 4 if abs(r['Estadístico']) < 1 else 2)
            ic = '' if np.isnan(r['IC 95 % inferior']) else f" · IC [{num(r['IC 95 % inferior'])}; {num(r['IC 95 % superior'])}]"
            rows.append([r.Prueba, h0, assumptions, f"{r['Nombre del estadístico']} = {stat}{ic}", pval(r['p crudo']),
                         pval(r['p Holm (familia de 21)']), pval(r['p Holm global (105)']), effect,
                         conclusion(r['p Holm (familia de 21)'], r['Δ RMSE OOF reunido'])])
        n = nem.loc[nem.Original.eq(label) & nem.Base.eq(ref_name)].iloc[0]
        rows.append(['Friedman → Nemenyi (U10)', 'Rangos promedio iguales', 'Bloques = 5 folds (menos de los 10 recomendados); CD controla la familia',
                     f"χ² = {num(meta['friedman_u10']['statistic'], 2)} (gl 9); Δ rango = {num(n['Δ rango'], 1)}; CD = {num(n.CD, 2)}",
                     pval(meta['friedman_u10']['pvalue']), 'CD (familiar)', '—', effect,
                     'Supera la CD' if n['Supera la CD'] else 'No supera la CD'])
        rows.append(['Model Confidence Set (U10)', 'Igual capacidad predictiva del conjunto', 'Bootstrap exacto de 5 folds (3.125 remuestreos); folds dependientes',
                     f"p MCS original = {pval(mcs.loc[label, 'p-valor MCS exploratorio'])}; {ref_name} = {pval(mcs.loc[ref_name, 'p-valor MCS exploratorio'])}",
                     '—', 'α = 0,10 (procedimiento)', '—', effect,
                     (f'Original en el MCS y {ref_name} fuera' if mcs.loc[label, 'En MCS exploratorio (α = 0.10)'] == 'Sí'
                      and mcs.loc[ref_name, 'p-valor MCS exploratorio'] < .10 else 'Sin separación')])
        title = 'al mejor benchmark (XGBoost)' if ref == 'xgboost' else 'al SVM lineal'
        write(f'pruebas_{key}{suffix}', f'{label} frente {title}: pruebas de hipótesis con las columnas de §6.3.',
              f'tab-pruebas-{key}{suffix.replace("_", "-")}',
              ['Prueba', 'H0', 'Supuestos verificados', 'Estadístico', 'p crudo', 'p ajustado (Holm, 21)', 'p Holm global (105)', 'Tamaño del efecto (MSE por fold)', 'Conclusión'],
              rows, ['---'] * 4 + ['---:'] * 3 + ['---', '---'])

    order = ['SVM lineal', 'KNN', 'Ridge', 'Lasso', 'Random Forest', 'XGBoost', 'Decision Tree']
    rows = []
    for label in ['KRR centrado', 'TN-KRR', 'GPR–XGBoost']:
        for test in H0:
            part = tests.loc[tests.Original.eq(label) & tests.Prueba.eq(test)].set_index('Base')
            rows.append([label, test] + [
                f"{'**' if part.loc[b, 'p Holm (familia de 21)'] < .05 else ''}{pval(part.loc[b, 'p Holm (familia de 21)'])}"
                f"{'**' if part.loc[b, 'p Holm (familia de 21)'] < .05 else ''}" for b in order])
    write('matriz_holm', 'p ajustado por Holm (familia de 21 por prueba) de cada original frente a cada modelo base. En negrita, p < 0,05; en todas las celdas en negrita la diferencia favorece al original.',
          'tab-matriz-holm', ['Original', 'Prueba', *order], rows, ['---', '---'] + ['---:'] * 7)
    assert not ((tests['p Holm (familia de 21)'] < .05) & (tests['Δ RMSE OOF reunido'] > 0)).any()

    delta = tests.drop_duplicates(['Original', 'Base']).set_index(['Original', 'Base'])
    write('efectos_r3', 'Diferencia de RMSE medio externo y tamaños de efecto (MSE por fold) de cada original frente a cada base.',
          'tab-efectos-r3', ['Original', 'Base', 'Δ RMSE medio CV', 'Folds ganados', 'δ de Cliff', 'Magnitud', 'd_z de Cohen'],
          [[o, b, num(delta.loc[(o, b), 'Δ RMSE medio CV (original − base)']), f"{delta.loc[(o, b), 'Folds en que gana el original']} de 5",
            num(delta.loc[(o, b), 'Delta de Cliff (MSE por fold)'], 2), delta.loc[(o, b), 'Magnitud Cliff'],
            num(delta.loc[(o, b), 'd_z de Cohen (MSE por fold)'], 2)]
           for o in ['KRR centrado', 'TN-KRR', 'GPR–XGBoost'] for b in order],
          ['---', '---', '---:', '---:', '---:', '---', '---:'])

    m10 = pd.read_csv(OUT / 'mcs_u10.csv')
    write('mcs_u10', 'Model Confidence Set del universo de 10 modelos (7 base + 3 originales), α = 0,10.', 'tab-mcs-u10',
          ['Modelo', 'Rango promedio de pérdida', 'MSE medio CV', 'p MCS', 'En MCS', 'Paso de eliminación'],
          [[f'**{r.Modelo}**' if r.Modelo in ('KRR centrado', 'TN-KRR', 'GPR–XGBoost') else r.Modelo, num(r['Rango promedio de pérdida'], 1),
            num(r['MSE medio CV']), pval(r['p-valor MCS exploratorio']), r['En MCS exploratorio (α = 0.10)'], r['Paso de eliminación']]
           for _, r in m10.iterrows()])
    m16 = pd.read_csv(OUT / 'mcs_u16.csv')
    write('mcs_u16', 'Cálculo complementario: MCS de los 15 modelos del dashboard más Decision Tree (16), α = 0,10.', 'tab-mcs-u16',
          ['Modelo', 'Rango promedio de pérdida', 'MSE medio CV', 'p MCS', 'En MCS', 'Paso de eliminación'],
          [[r.Modelo, num(r['Rango promedio de pérdida'], 1), num(r['MSE medio CV']), pval(r['p-valor MCS exploratorio']),
            r['En MCS exploratorio (α = 0.10)'], r['Paso de eliminación']] for _, r in m16.iterrows()])

    verdict = pd.read_csv(OUT / 'veredicto_r3.csv')
    write('veredicto', 'Superioridad estadísticamente verificada de cada original según la definición operativa de §6.1, frente al mejor benchmark (XGBoost) y frente al SVM lineal.',
          'tab-veredicto',
          ['Original', 'Frente a', 'Menor RMSE medio', 'Pruebas favorables (p Holm por prueba)', 'Efecto (MSE por fold)',
           'Superior · Holm por prueba', 'Superior · BH global', 'Superior · Holm global'],
          [[r.Original, r.Referencia,
            f"{'Sí' if r['C1 · menor RMSE medio que la referencia'] else 'No'} ({num(r['RMSE medio original'])} vs {num(r['RMSE medio referencia'])})",
            f"{r['C2 · pruebas favorables (Holm por prueba)']}: {r['Pruebas favorables (Holm por prueba)']}",
            f"δ = {num(r['δ Cliff'], 2)}; d_z = {num(r['d_z'], 2)}",
            f"**{r['Superioridad (Holm por prueba)']}**", r['Superioridad (BH global)'], r['Superioridad (Holm global)']]
           for _, r in verdict.iterrows()], ['---'] * 8)

    tt = pd.read_csv(OUT / 'pruebas_r3_test.csv')
    write('test_complemento', 'Complemento descriptivo en el test temporal 202530 (188 estudiantes): contraste DM-HLN por estudiante.', 'tab-test-complemento',
          ['Original', 'Base', 'Δ RMSE test', 'IC 95 % (percentil)', 'p crudo', 'p Holm (6)'],
          [[r.Original, r.Base, num(r['Δ RMSE test']), f"[{num(r['IC 95 % inf (percentil, estudiantes)'])}; {num(r['IC 95 % sup'])}]",
            pval(r['p crudo HLN']), pval(r['p Holm (6)'])] for _, r in tt.iterrows()])

    abl = pd.read_csv(OUT / 'ablacion.csv')
    write('ablacion', 'Ablación con predicciones OOF existentes (mismos folds). Δ < 0 favorece al modelo completo.', 'tab-ablacion',
          ['Modelo completo', 'Variante sin el componente', 'RMSE CV variante', 'RMSE CV completo', 'Δ RMSE OOF', 'IC 95 % BCa', 'p BCa', 'p permutación'],
          [[r['Modelo completo'], r.Variante, pm(r['RMSE medio CV variante'], r['DE variante']), num(r['RMSE medio CV completo']),
            num(r['Δ RMSE OOF (completo − variante)']), f"[{num(r['IC 95 % BCa inf'])}; {num(r['IC 95 % BCa sup'])}]",
            pval(r['p BCa']), pval(r['p permutación'])] for _, r in abl.iterrows()],
          ['---', '---'] + ['---:'] * 6)

    shap_k = pd.read_csv(HER / 'originales' / 'shap_importancia_pct_lider.csv', index_col=0).iloc[:, 0]
    shap_x = pd.read_csv(HER / 'clasicos' / 'shap_importancia_pct.csv', index_col=0)['XGBoost']
    both = pd.DataFrame({'k': shap_k, 'x': shap_x}).fillna(0).sort_values('k', ascending=False)
    both['rk'], both['rx'] = both.k.rank(ascending=False).astype(int), both.x.rank(ascending=False, method='min').astype(int)
    write('shap_comparacion', 'Importancia SHAP relativa (% de la suma de |SHAP| medio): KRR centrado frente a XGBoost.', 'tab-shap-comparacion',
          ['Variable', 'KRR centrado (%)', 'Rango', 'XGBoost (%)', 'Rango'],
          [[v, num(r.k, 1), int(r.rk), num(r.x, 1), int(r.rx)] for v, r in both.iterrows()])

    nov = pd.read_csv(OUT / 'matriz_novedad.csv')
    write('matriz_novedad', 'Matriz de novedad: búsquedas ejecutadas el 24 de octubre de 2026 (`analisis/busqueda_literatura.py`).', 'tab-matriz-novedad',
          ['Id', 'Base de datos', 'Cadena de búsqueda', 'Result.', 'Revis.', 'Relev.', 'Observación'],
          [[r.Cadena, r['Base de datos'], f"`{r['Cadena de búsqueda']}`", num(int(r.Resultados)), num(int(r.Revisados)), num(int(r.Relevantes)), r['Observación']]
           for _, r in nov.iterrows()], ['---', '---', '---', '---:', '---:', '---:', '---'])

    master = pd.read_csv(OUT / 'tabla_maestra_experimentos.csv')
    proc = master.loc[master.Fila.str.startswith('Procedimiento')]
    write('maestra_extracto', 'Extracto de la tabla maestra: filas de procedimiento anidado (métricas del bucle externo).', 'tab-maestra-extracto',
          ['Grupo', 'Modelo', 'RMSE externo', 'MAE externo', 'R² externo', 'RMSE test', 'Semilla', 'Ejecución activa'],
          [[r.Grupo, r.Modelo, pm(r['RMSE externo media'], r['RMSE externo DE']), pm(r['MAE externo media'], r['MAE externo DE']),
            num(r['R² externo media']), num(r['RMSE test 202530 (descriptivo)']), r.Semilla, f"`{r['Ejecución activa']}`"]
           for _, r in proc.sort_values('RMSE externo media').iterrows()], ['---', '---'] + ['---:'] * 5 + ['---'])

    # Tablas heredadas del libro previo (dashboard), regeneradas desde sus CSV.
    dm = pd.read_csv(HER / 'originales' / 'stats_etapa3_dm_cv.csv')
    write('her_dm_cv', 'Dashboard: contraste tipo Diebold–Mariano por estudiante frente al SVM (CV, 1.293 estudiantes).', 'tab-her-dm-cv',
          ['Modelo vs SVM', 'Posición MCS', 'Δ MSE', 'Δ RMSE', 'IC 95 % Δ RMSE', 'p crudo', 'p HLN', 'p t corregida'],
          [[r.model, r.mcs_position, num(r.delta_mse), num(r.delta_rmse), f'[{num(r.ic_low)}; {num(r.ic_high)}]',
            pval(r.p_raw), pval(r.p_hln), pval(r.p_corrected_t)] for _, r in dm.iterrows()])
    dmt = pd.read_csv(HER / 'originales' / 'stats_etapa3_dm_test.csv')
    write('her_dm_test', 'Dashboard: mismo contraste en el test 202530 (188 estudiantes).', 'tab-her-dm-test',
          ['Modelo vs SVM', 'Δ RMSE', 'IC 95 % Δ RMSE', 'p crudo', 'p HLN'],
          [[r.model, num(r.delta_rmse), f'[{num(r.ic_low)}; {num(r.ic_high)}]', pval(r.p_raw), pval(r.p_hln)] for _, r in dmt.iterrows()])
    m15 = pd.read_csv(HER / 'originales' / 'stats_mcs.csv')
    write('her_mcs15', 'Dashboard: MCS de los 15 modelos del dashboard (sin Decision Tree), α = 0,10.', 'tab-her-mcs15',
          ['Modelo', 'Rango promedio de pérdida', 'MSE medio CV', 'p MCS', 'En MCS', 'Paso'],
          [[r.Modelo, num(r['Rango promedio de pérdida'], 1), num(r['MSE medio CV']), pval(r['p-valor MCS exploratorio']),
            r['En MCS exploratorio (α = 0.10)'], r['Paso de eliminación']] for _, r in m15.iterrows()])
    fin = pd.read_csv(HER / 'originales' / 'stats_etapa2_dm_finalistas.csv')
    write('her_finalistas', 'Dashboard: pares de finalistas del MCS de 15 modelos (contraste por estudiante con HLN).', 'tab-her-finalistas',
          ['Modelo A', 'Modelo B', 'Δ RMSE (A − B)', 'IC 95 % Δ RMSE', 'p crudo', 'p HLN', 'Conclusión'],
          [[r.a, r.b, num(r.delta_rmse), f'[{num(r.ic_low)}; {num(r.ic_high)}]', pval(r.p_raw), pval(r.p_hln), r.conclusion]
           for _, r in fin.iterrows()])
    print(f'{len(list(TABLES.glob("*.md")))} tablas escritas en {TABLES}')


if __name__ == '__main__':
    main()

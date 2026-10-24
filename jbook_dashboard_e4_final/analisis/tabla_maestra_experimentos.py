"""Tabla maestra de experimentos (§10.5) a partir de resultados ya guardados.

Une, sin reentrenar:
  * las 35 combinaciones modelo × método de búsqueda de los 7 modelos base
    (`jbook_dashboard/analisis_clasicos/salidas/hpo_resumen.csv`, run 20261018_102325_af643f83);
  * las combinaciones de los 9 modelos de la pestaña Originales, incluidos los 3 originales del
    proyecto (`analisis_originales/salidas/hpo_resumen.csv`, run 20261020_153034_consolidada);
  * una fila «procedimiento anidado» por modelo con las métricas del bucle externo, porque en la
    validación anidada cada fold externo elige su propio método: las métricas externas pertenecen
    al procedimiento completo, no a un método aislado.
En regresión no hay técnicas de balanceo; por eso el universo base es 7 × 5 = 35 y no 140.
Tiempos de pared tomados del registro central; los no registrados se escriben «No medido».

Uso: python tabla_maestra_experimentos.py → salidas/tabla_maestra_experimentos.csv
"""
import json

import pandas as pd

from comun import BASE, OLD_BOOK, ORIGINAL, OUT, RUN_ORIG, SEED

RUN_BASE_ID = '20261018_102325_af643f83'
RUN_ORIG_ID = '20261020_153034_consolidada'
PROJECT_ORIGINALS = {'Kernel Ridge RBF': 'KRR centrado', 'TR-KRR RBF': 'TN-KRR', 'GPR–XGBoost': 'GPR–XGBoost'}


def outer(metrics, name_col, name):
    row = metrics.loc[metrics[name_col].eq(name) & metrics.Conjunto.eq('Validación (OOF)')].iloc[0]
    test = metrics.loc[metrics[name_col].eq(name) & metrics.Conjunto.eq('Prueba (test 202530)')].iloc[0]
    return {'RMSE externo media': row['RMSE media folds'], 'RMSE externo DE': row['RMSE SD folds'],
            'MAE externo media': row['MAE media folds'], 'MAE externo DE': row['MAE SD folds'],
            'R² externo media': row['R² media folds'], 'RMSE test 202530 (descriptivo)': test['RMSE']}


def main():
    rows = []
    hpo_b = pd.read_csv(OLD_BOOK / 'analisis_clasicos' / 'salidas' / 'hpo_resumen.csv')
    eval_b = pd.read_csv(OLD_BOOK / 'analisis_clasicos' / 'salidas' / 'eval_metricas.csv')
    for _, r in hpo_b.iterrows():
        rows.append({'Fila': 'Combinación modelo × método', 'Grupo': 'Base (benchmark)', 'Modelo': r.Modelo,
                     'Método de búsqueda': r['Método'], 'Elegido en la búsqueda final': bool(r.Elegido),
                     'RMSE interno (búsqueda final)': r['RMSE interno'], 'DE interna': r['SD interna'],
                     'Configuraciones evaluadas': r.Evaluaciones, 'Ajustes internos': r['Ajustes internos'],
                     'Búsqueda final (s)': r['Búsqueda final (s)'], '5 búsquedas externas (s)': r['5 búsquedas externas (s)'],
                     'Hiperparámetros': r['Mejores parámetros'], 'Semilla': SEED, 'run_id': RUN_BASE_ID, 'Ejecución activa': RUN_BASE_ID})
    for name in BASE.values():
        rows.append({'Fila': 'Procedimiento anidado (5 estrategias)', 'Grupo': 'Base (benchmark)', 'Modelo': name,
                     'Método de búsqueda': 'Selección anidada', **outer(eval_b, 'Modelo', name),
                     'Semilla': SEED, 'run_id': RUN_BASE_ID, 'Ejecución activa': RUN_BASE_ID})
    hpo_o = pd.read_csv(OLD_BOOK / 'analisis_originales' / 'salidas' / 'hpo_resumen.csv')
    eval_o = pd.read_csv(OLD_BOOK / 'analisis_originales' / 'salidas' / 'eval_metricas.csv')
    catalog = json.loads((RUN_ORIG / 'catalog.json').read_text(encoding='utf-8'))
    for _, r in hpo_o.iterrows():
        group = 'Original del proyecto' if r.Modelo in PROJECT_ORIGINALS else 'Complementario (pestaña Originales)'
        rows.append({'Fila': 'Combinación modelo × método', 'Grupo': group,
                     'Modelo': PROJECT_ORIGINALS.get(r.Modelo, r.Modelo), 'Método de búsqueda': r['Método'],
                     'Elegido en la búsqueda final': bool(r.Elegido), 'RMSE interno (búsqueda final)': r['RMSE interno'],
                     'DE interna': r['SD interna'], 'Configuraciones evaluadas': r.Evaluaciones,
                     'Ajustes internos': r['Ajustes internos'], 'Búsqueda final (s)': r['Búsqueda final (s)'],
                     '5 búsquedas externas (s)': r['5 búsquedas externas (s)'], 'Hiperparámetros': r['Parámetros'],
                     'Semilla': SEED, 'Ejecución activa': RUN_ORIG_ID, 'run_id': catalog.get(r.Clave, {}).get('timing_run_id', RUN_ORIG_ID)})
    for key, name in eval_o.loc[eval_o.Clave.ne('svm'), ['Clave', 'Modelo']].drop_duplicates().to_numpy():
        group = 'Original del proyecto' if key in ORIGINAL else 'Complementario (pestaña Originales)'
        rows.append({'Fila': 'Procedimiento anidado (5 estrategias)', 'Grupo': group,
                     'Modelo': PROJECT_ORIGINALS.get(name, name), 'Método de búsqueda': 'Selección anidada',
                     **outer(eval_o, 'Clave', key), 'Semilla': SEED,
                     'run_id': catalog.get(key, {}).get('timing_run_id', RUN_ORIG_ID)})
    table = pd.DataFrame(rows)
    for col in ('Búsqueda final (s)', '5 búsquedas externas (s)'):
        table[col] = table[col].astype(object).where(table[col].notna() | table.Fila.ne('Combinación modelo × método'), 'No medido')
    table.to_csv(OUT / 'tabla_maestra_experimentos.csv', index=False, encoding='utf-8')
    print(table.groupby(['Grupo', 'Fila']).size().to_string())


if __name__ == '__main__':
    main()

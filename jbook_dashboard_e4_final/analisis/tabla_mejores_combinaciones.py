"""Tabla maestra de mejores combinaciones de los 7 modelos base (Bloque B, §4.1).

Lee la ejecución activa `busquedas/20261018_102325_af643f83` sin reentrenar:
método ganador e hiperparámetros (`seleccion_antes_test.json` y evidencia por búsqueda),
métricas del bucle externo (`clasicos/fold_metrics.csv`), RMSE de test solo descriptivo,
tiempos del registro central (`tiempos/<run>/eventos.jsonl`) y pertenencia al MCS de las
salidas del libro previo. Criterio de selección: RMSE medio del bucle externo; nunca test
ni tiempo.

Uso: python tabla_mejores_combinaciones.py  →  salidas/mejores_combinaciones.csv
"""
import json

import numpy as np
import pandas as pd

from comun import BASE, OLD_BOOK, OUT, RUN_BASE, fold_metrics, partitions, rmse, test_predictions, timing_events

SHORT = {'Grid Search': 'Grid', 'Random Search': 'Random', 'Bayesiana TPE': 'TPE',
         'Genética DEAP': 'DEAP', 'Successive Halving': 'Halving'}


def params_text(params):
    parts = []
    for name, value in params.items():
        name = name.replace('modelo__', '')
        parts.append(f'{name} = {value:.4g}' if isinstance(value, float) else f'{name} = {value}')
    return '; '.join(parts)


def timings(events, key):
    def total(stage, test):
        return float(sum(e['seconds'] for e in events if e['stage'] == stage and e.get('model') == key and test(e)))
    return {
        'Búsqueda final, 5 estrategias (s)': total('Búsqueda', lambda e: e.get('outer') == 'final_train'),
        'Búsquedas externas, suma de 5 folds (s)': total('Búsqueda', lambda e: str(e.get('outer', '')).startswith('externo')),
        'Refit final (s)': total('Entrenamiento/refit', lambda e: e['batch'].endswith('final train')),
        'Inferencia OOF, 5 lotes (s)': total('Inferencia', lambda e: ' OOF fold ' in e['batch']),
        'Inferencia test, 188 filas (s)': total('Inferencia', lambda e: e['batch'].endswith('test temporal')),
    }


def build():
    selection = json.loads((RUN_BASE / 'seleccion_antes_test.json').read_text(encoding='utf-8'))
    assert selection['test_used_for_selection'] is False
    folds = fold_metrics()
    events = timing_events()
    _, test = partitions()
    pred_test = test_predictions()
    mcs7 = pd.read_csv(OLD_BOOK / 'analisis_clasicos' / 'salidas' / 'stats_mcs.csv').set_index('Modelo')
    mcs15 = pd.read_csv(OLD_BOOK / 'analisis_originales' / 'salidas' / 'stats_mcs.csv').set_index('Modelo')
    rows = []
    for key, name in BASE.items():
        f = folds.loc[folds.clave.eq(key)].sort_values('Fold')
        assert len(f) == 5, key
        per_fold = [json.loads((RUN_BASE / 'evidencia' / f'selection_{key}_externo_{k}.json').read_text(encoding='utf-8'))
                    ['selected_method'] for k in range(1, 6)]
        rows.append({
            'Modelo': name, 'Clave': key,
            'Método ganador (búsqueda final)': selection['models'][key]['method'],
            'Métodos por fold externo (1–5)': ' · '.join(SHORT[m] for m in per_fold),
            'Hiperparámetros finales': params_text(selection['models'][key]['params']),
            'RMSE externo media': f.RMSE.mean(), 'RMSE externo DE': f.RMSE.std(ddof=1),
            'MAE externo media': f.MAE.mean(), 'MAE externo DE': f.MAE.std(ddof=1),
            'R² externo media': f['R²'].mean(), 'R² externo DE': f['R²'].std(ddof=1),
            'RMSE test 202530 (descriptivo)': rmse(test['nota_primer_parcial'], pred_test[key]),
            **timings(events, key),
            'En MCS clásicos (7 modelos, α = 0,10)': mcs7.loc[name, 'En MCS exploratorio (α = 0.10)'],
            'p MCS clásicos': mcs7.loc[name, 'p-valor MCS exploratorio'],
            'En MCS dashboard (15 modelos)': mcs15.loc[name, 'En MCS exploratorio (α = 0.10)'] if name in mcs15.index else 'Fuera del universo',
        })
    table = pd.DataFrame(rows).sort_values('RMSE externo media', kind='stable').reset_index(drop=True)
    table.insert(0, 'Posición', np.arange(1, len(table) + 1))
    best = table.loc[0, 'Modelo']
    table['Motivo de la selección'] = [
        (f'Mejor combinación global: menor RMSE medio externo de los 7 base; {"pertenece" if r["En MCS clásicos (7 modelos, α = 0,10)"] == "Sí" else "no pertenece"} al MCS de clásicos.'
         if r['Modelo'] == best else
         f'Configuración de menor RMSE interno en la búsqueda final ({SHORT[r["Método ganador (búsqueda final)"]]}); '
         f'{"dentro" if r["En MCS clásicos (7 modelos, α = 0,10)"] == "Sí" else "fuera"} del MCS de clásicos.')
        for _, r in table.iterrows()]
    return table


if __name__ == '__main__':
    table = build()
    table.to_csv(OUT / 'mejores_combinaciones.csv', index=False, encoding='utf-8')
    print(table[['Posición', 'Modelo', 'Método ganador (búsqueda final)', 'RMSE externo media', 'RMSE externo DE',
                 'Búsqueda final, 5 estrategias (s)', 'Refit final (s)', 'Inferencia test, 188 filas (s)']].to_string())

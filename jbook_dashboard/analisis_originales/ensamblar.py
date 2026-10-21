"""Ensambla ``../05_modelos_originales.md`` a partir de ``plantilla.md`` y las tablas de ``salidas/``."""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tablas as T

wins = T.wins()
w5 = T.choices[T.choices.Modelo != 'LinXGBoost']['Método elegido'].map(T.METHOD).value_counts().to_dict()
g = T.strategy_totals()
tpe_total, grid_total = g.loc['Bayesiana TPE', 'total'], g.loc['Grid Search', 'total']
l72, l118 = T.lime_meta(72), T.lime_meta(118)
S = {
    't_rmse_interno': T.t_rmse_interno(), 't_brechas': T.t_brechas(), 't_finales': T.t_finales(), 't_ganadores': T.t_ganadores(),
    't_evaluaciones': T.t_evaluaciones(), 't_tiempo_final': T.t_tiempo('Búsqueda final (s)'),
    't_tiempo_externo': T.t_tiempo('5 búsquedas externas (s)'), 't_por_evaluacion': T.t_por_evaluacion(), 't_totales': T.t_totales(),
    't_refit': T.t_refit(), 't_rmse_mae': T.t_rmse_mae(), 't_diagnosticos': T.t_diagnosticos(), 't_folds': T.t_folds(),
    't_variabilidad': T.t_variabilidad(), 't_rangos': T.t_rangos(), 't_mcs': T.t_mcs(), 't_finalistas': T.t_finalistas(),
    't_dm_cv': T.t_dm('cv'), 't_dm_test': T.t_dm('test'), 't_efectos_lider': T.t_efectos_lider(), 't_efectos_svm': T.t_efectos_svm(),
    't_final': T.t_final(), 't_shap': T.t_shap(), 't_lime72': T.t_lime(72), 't_lime118': T.t_lime(118),
    'wins_grid': str(w5.get('Grid', 0)), 'wins_tpe': str(w5.get('TPE', 0)), 'wins_deap': str(w5.get('DEAP', 0)),
    'ratio_tpe_grid': (f'en los ocho modelos con las cinco estrategias, TPE sumó {T.es(tpe_total, 0)} s (búsquedas finales y externas) frente a '
                       f'{T.es(grid_total, 0)} s del Grid, un {T.es(100 * (1 - tpe_total / grid_total), 0)} % menos (el total del Grid incluye 2.512 s de las búsquedas externas de GPR–XGBoost, inflados por el cómputo de su etapa GPR; sin ese modelo la diferencia es menor, pero TPE sigue siendo más barata)'),
    'lime72_pred': T.es(l72['pred'], 3), 'lime72_sust': T.es(l72['sust'], 3), 'lime72_r2': T.es(l72['r2'], 3), 'lime72_gap': T.es(l72['gap'], 3),
    'lime118_pred': T.es(l118['pred'], 3), 'lime118_sust': T.es(l118['sust'], 3), 'lime118_r2': T.es(l118['r2'], 3), 'lime118_gap': T.es(l118['gap'], 3),
    'shap118_cumpl': T.es(T.shap_value(118, 'Cumplimiento de la meta'), 3),
}
text = (HERE / 'plantilla.md').read_text(encoding='utf-8')
missing = [k for k in re.findall(r'<<(\w+)>>', text) if k not in S]
assert not missing, missing
text = re.sub(r'<<(\w+)>>', lambda m: S[m.group(1)], text)
(HERE.parent / '05_modelos_originales.md').write_text(text, encoding='utf-8')
print('listo', len(text))

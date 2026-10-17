"""Contrastes de RMSE contra SVM: CV corregida y test, sin extrapolar a subgrupos."""
import numpy as np
import pandas as pd

from prepare_data import CACHE

INVENTORY = pd.read_csv(CACHE / 'originales/inventory.csv').set_index('Modelo')
CONTRASTS = pd.read_csv(CACHE / 'originales/contrasts.csv')
CV_INFERENCE = pd.read_csv(CACHE / 'originales/cv_inference.csv').set_index('Modelo')
REFERENCE = 'SVM lineal'
P_RAW = 'p bilateral vs SVM'
P_HOLM = 'p Holm vs SVM'
RESULT = 'Conclusión vs SVM (Holm, α=0.05)'
EXPLANATION = (
    '**Referencia de todos los contrastes: SVM lineal.** Se contrasta la diferencia de RMSE '
    '(modelo − SVM); un delta negativo favorece al modelo. **Orden: RMSE de menor a mayor**, '
    'igual en la tabla y en los cuatro gráficos; los modelos sin RMSE disponible quedan al final de la tabla. '
    'El p-valor mide evidencia contra la igualdad, no el tamaño de la diferencia. '
    '**Significativa** significa p de Holm < 0.05; se distingue mejora de deterioro. '
    '**CV global:** t pareada corregida por el solapamiento de los entrenamientos '
    '(aproximación Nadeau–Bengio), cinco folds, 4 grados de libertad y **Holm24 CV vs SVM** '
    'sobre los 24 competidores activos con OOF. Una sola partición sin repeticiones: '
    'inferencia aproximada y exploratoria, de baja potencia; no se asumen folds independientes. '
    '**Test global:** se conservan las familias publicadas Holm55 o Holm7, distintas de la familia CV. '
    'La comparación de procedimientos se apoya principalmente en CV; el test contrasta el periodo posterior. '
    'Los subgrupos no tienen contraste calculado; TabPFN fine-tuned no tiene OOF independiente. '
    '«—» significa no evaluado, nunca p=0.'
)


def add_inference(scores, *, cv=False, global_view=True):
    """Solo unir contrastes cuya referencia y evaluación coinciden con la fila."""
    result = scores.copy()
    metadata = []
    for name in result['Modelo']:
        row = {'Referencia estadística': REFERENCE, P_RAW: np.nan, P_HOLM: np.nan,
               'Familia de Holm': '—', RESULT: 'No evaluada en subgrupo' if not global_view else 'Sin OOF independiente' if cv else 'Contraste no publicado'}
        if name == REFERENCE:
            row[RESULT] = 'Referencia'
        elif cv and global_view and name in CV_INFERENCE.index:
            saved = CV_INFERENCE.loc[name]
            if pd.notna(saved.p_Holm):
                expected = scores.loc[scores.Modelo.eq(name), 'Δ RMSE vs SVM'].iloc[0]
                if not np.isclose(expected, saved.delta_RMSE, atol=1e-10, rtol=0):
                    raise ValueError('El contraste CV no coincide con las métricas: ' + name)
                row.update({P_RAW: saved.p_bilateral, P_HOLM: saved.p_Holm,
                            'Familia de Holm': saved.familia_ajuste, RESULT: saved.conclusion})
        elif not cv and global_view:
            if name in INVENTORY.index:
                saved = INVENTORY.loc[name]
                row[P_RAW] = saved['p_bilateral']
                # No tomar familia_principal: algunas filas usan XGBoost como referencia.
                row[P_HOLM] = saved['p_Holm_global_55']
                if pd.notna(row[P_HOLM]):
                    row['Familia de Holm'] = 'Holm55'
            direct = CONTRASTS.loc[CONTRASTS.Modelo.eq(name) & CONTRASTS.Referencia.eq(REFERENCE) & CONTRASTS.metrica.eq('RMSE')]
            if len(direct) > 1:
                raise ValueError('Contraste ambiguo: ' + name)
            if len(direct):
                saved = direct.iloc[0]
                row.update({P_RAW: saved.p_bilateral, P_HOLM: saved.p_ajustado, 'Familia de Holm': saved.familia_ajuste})
            if pd.notna(row[P_HOLM]):
                delta = float(scores.loc[scores.Modelo.eq(name), 'Δ RMSE vs SVM'].iloc[0])
                row[RESULT] = ('Mejora significativa' if delta < 0 else 'Deterioro significativo') if row[P_HOLM] < .05 else 'No significativa'
        metadata.append(row)
    for column in ['Referencia estadística', P_RAW, P_HOLM, 'Familia de Holm', RESULT]:
        result[column] = [row[column] for row in metadata]
    result = result.sort_values('RMSE', na_position='last', kind='stable')
    return result


def conclusion(test_scores, cv_scores, global_view):
    if not global_view:
        return ('Los resultados filtrados describen este subgrupo; no hay contrastes publicados para él. '
                'La conclusión estadística global se consulta seleccionando Todos en ambos filtros.')
    available = cv_scores.dropna(subset=['RMSE']).sort_values('RMSE')
    if available.empty:
        return 'No hay CV externa disponible para concluir sobre esta selección.'
    best_cv = available.iloc[0]
    inference = add_inference(cv_scores, cv=True)
    row = inference.loc[inference.Modelo.eq(best_cv.Modelo)].iloc[0]
    text = f'**La comparación principal usa CV externa. {best_cv.Modelo}** tiene el menor RMSE medio (**{best_cv.RMSE:.6f}**). '
    if pd.notna(row[P_HOLM]):
        text += f'Frente al **SVM lineal**: p bilateral corregida = **{row[P_RAW]:.5f}**; p Holm24 = **{row[P_HOLM]:.5f}**. '
    if not inference[RESULT].eq('Mejora significativa').any():
        text += '**Ninguna mejora evaluada frente al SVM es significativa después de Holm24 en CV**; no hay un ganador estadístico demostrado. '
    if not test_scores.empty:
        best_test = test_scores.dropna(subset=['RMSE']).sort_values('RMSE').iloc[0]
        text += f'Como contraste temporal, **{best_test.Modelo}** lidera el test (**{best_test.RMSE:.6f}**); esto no reemplaza la elección basada en CV. '
    return text + 'Con solo cinco folds no repetidos, el contraste corregido es aproximado y exploratorio. Para confirmar, se requiere validación adicional; el test ya fue reutilizado.'


def display_statistics(scores, *, cv=False, global_view=True):
    result = add_inference(scores, cv=cv, global_view=global_view)
    for column in [P_RAW, P_HOLM]:
        result[column] = result[column].map(lambda p: '—' if pd.isna(p) else f'{p:.5f}')
    leading = [c for c in ['Modelo', 'Δ RMSE vs SVM', P_RAW, P_HOLM, RESULT, 'Referencia estadística', 'Familia de Holm'] if c in result]
    return result[leading + [c for c in result if c not in leading]]

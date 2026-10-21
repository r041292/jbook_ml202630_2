"""Friedman sobre bloques externos emparejados; no utiliza test ni reajusta modelos."""
import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare


EXPLANATION = (
    '**Test de Friedman:** análogo no paramétrico del ANOVA de medidas repetidas. '
    'Cada bloque es un fold externo y cada tratamiento es uno de los siete modelos '
    '(seis clásicos y SVM lineal). Se ordena el **RMSE dentro de cada fold**: '
    'rango 1 = menor error; los empates reciben el rango promedio. '
    '**H₀: todos los modelos tienen rendimiento equivalente en rangos (rangos promedio iguales).** '
    'Se muestra χ² de Friedman corregido por empates, gl = modelos − 1 y p asintótico, con α = 0.05. '
    'El contraste es global: rechazar H₀ indica diferencias entre al menos dos modelos, '
    'sin identificar pares ni demostrar que el primero supere al SVM. La sección principal documenta el post hoc MCS exploratorio, los tamaños de efecto y los límites de las comparaciones dirigidas. **Comparaciones frente al SVM:** Friedman se usa para tres o más modelos; no se aplica a pares modelo–SVM. Wilcoxon sería otro contraste, pero requiere diferencias independientes: los cinco folds con entrenamientos solapados no justifican ese supuesto. Por ello no se añaden p-valores Wilcoxon por pares. '
    '**Limitaciones:** solo hay cinco folds, por debajo de la recomendación de SciPy de más de '
    'diez bloques y más de seis modelos para la aproximación χ²; los entrenamientos se solapan y Friedman no corrige '
    'esa dependencia. La lectura es exploratoria. No rechazar H₀ no demuestra equivalencia. '
    'Friedman usa únicamente CV global; los subgrupos conservan métricas descriptivas. '
    'La ampliación bootstrap por estudiante del test se presenta aparte, con sus propios supuestos y ajuste Holm. '
    '[Friedman en SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.friedmanchisquare.html) · '
    '[Supuestos de Wilcoxon](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html).'
)


def friedman_comparison(folds, models):
    """Exige la matriz completa, sin omitir folds o modelos silenciosamente."""
    names = list(models)
    if len(names) < 3 or len(set(names)) != len(names):
        raise ValueError('Friedman requiere al menos tres modelos distintos.')
    selected = folds.loc[folds.Modelo.isin(names)]
    if selected[['Fold', 'Modelo']].isna().any().any() or selected.duplicated(['Fold', 'Modelo']).any():
        raise ValueError('Cada modelo debe tener un único RMSE por fold identificado.')
    matrix = selected.pivot(index='Fold', columns='Modelo', values='RMSE').reindex(columns=names).sort_index()
    if len(matrix) < 2 or not np.isfinite(matrix.to_numpy(dtype=float)).all():
        raise ValueError('Friedman requiere folds completos con RMSE finito para todos los modelos.')
    ranks = matrix.rank(axis=1, method='average', ascending=True)
    # Todos empatados en todos los bloques: la corrección por empates es cero.
    estimable = not matrix.nunique(axis=1).eq(1).all()
    statistic, p = friedmanchisquare(*[ranks[name].to_numpy() for name in names]) if estimable else (np.nan, np.nan)
    ranking = ranks.T.rename(columns=lambda fold: f'Rango fold {fold}')
    ranking['Rango promedio'] = ranks.mean()
    ranking = ranking.sort_values('Rango promedio', kind='stable').rename_axis('Modelo').reset_index()
    return {'statistic': float(statistic), 'pvalue': float(p), 'df': len(names)-1,
            'n_folds': len(matrix), 'n_models': len(names), 'ranking': ranking}


def summary(result):
    if not np.isfinite(result['pvalue']):
        return 'Friedman no estimable: todos los modelos empatan en todos los folds.'
    decision = ('Se rechaza H₀: hay diferencias globales de rangos entre los modelos.'
                if result['pvalue'] < .05 else
                'No se rechaza H₀: no hay evidencia suficiente de diferencias globales; esto no demuestra equivalencia.')
    return (f'**Friedman · RMSE CV global:** χ² = **{result["statistic"]:.4f}**, '
            f'gl = **{result["df"]}**, p asintótico = **{result["pvalue"]:.6g}** '
            f'({result["n_folds"]} folds × {result["n_models"]} modelos; α = 0.05). '
            + decision + ' Resultado exploratorio por los cinco folds y el solapamiento de entrenamientos. '
            'El post hoc exploratorio y sus límites se documentan en la sección principal; no se identifica un ganador estadístico confirmado.')


def display_statistics(scores, *, cv=False, global_view=True, result=None):
    values = scores.sort_values('RMSE', na_position='last', kind='stable').copy()
    if cv and global_view and result is not None:
        values = values.merge(result['ranking'][['Modelo', 'Rango promedio']], on='Modelo', how='left', validate='one_to_one')
    return values


def conclusion(test_scores, cv_scores, global_view, result):
    if not global_view:
        return ('Las métricas describen el subgrupo. Friedman solo se calcula para CV global; '
                'selecciona Todos en ambos filtros para consultar sus rangos y contraste.')
    available = cv_scores.dropna(subset=['RMSE']).sort_values('RMSE')
    text = ''
    if not available.empty:
        best = available.iloc[0]
        text = (f'**1. Mejor valor de la tabla.** En la CV externa, **{best.Modelo}** tiene el menor RMSE medio '
                f'(**{best.RMSE:.6f}**); es un orden descriptivo, que puede diferir del rango promedio. ')
    temporal = test_scores.dropna(subset=['RMSE']).sort_values('RMSE')
    if not temporal.empty:
        text += (f'En el test temporal el menor RMSE es de **{temporal.iloc[0].Modelo}** '
                 f'(**{temporal.iloc[0].RMSE:.6f}**); el test no participa en Friedman ni en la elección de modelos. ')
    if np.isfinite(result['pvalue']):
        decision = ('se rechaza H₀: hay diferencias globales de rangos entre los modelos'
                    if result['pvalue'] < .05 else
                    'no se rechaza H₀: no hay evidencia suficiente de diferencias globales, lo que no demuestra equivalencia')
        text += (f'\n\n**2. Resultado del test aplicado a continuación.** Friedman sobre el RMSE por fold '
                 f'(χ² = {result["statistic"]:.4f}, gl = {result["df"]}, p asintótico = {result["pvalue"]:.6g}; '
                 f'{result["n_folds"]} folds × {result["n_models"]} modelos, α = 0.05): {decision}. '
                 'Es exploratorio por los cinco folds y el solapamiento de entrenamientos.')
    else:
        text += '\n\n**2. Resultado del test aplicado a continuación.** Friedman no es estimable: todos los modelos empatan en todos los folds.'
    return text + ('\n\n**3. Continuación.** El análisis sigue en la sección **Conclusiones y comparación estadística**: '
                   'Friedman y Nemenyi, MCS, comparaciones dirigidas, Diebold–Mariano por estudiante y tamaños de efecto. '
                   'No se identifica un ganador estadístico confirmado.')

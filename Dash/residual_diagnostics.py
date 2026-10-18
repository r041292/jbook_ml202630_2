"""White y BDS exploratorios sobre residuos ya calculados, sin reentrenamiento."""
from functools import lru_cache
import warnings

import numpy as np
from scipy.linalg import qr
from statsmodels.stats.diagnostic import het_white
from statsmodels.tsa.stattools import bds
from threadpoolctl import threadpool_limits


def residual_diagnostics(frame, target, prediction, numeric):
    # Los bytes conservan el orden y permiten cachear también filas con NaN.
    values = np.ascontiguousarray(frame[[target, prediction, *numeric]], dtype=float)
    return dict(_calculate(len(values), len(numeric), values.tobytes()))


@lru_cache(maxsize=64)
def _calculate(n, width, payload):
    values = np.frombuffer(payload, dtype=float).reshape(n, width+2)
    valid = np.isfinite(values[:, :2]).all(axis=1)
    residuals = values[valid, 0]-values[valid, 1]
    x = values[valid, 2:]
    complete = np.isfinite(x).all(axis=1)
    white_residuals, x = residuals[complete], x[complete]
    result = {'white_p': None, 'white_lm': None, 'white_df': None,
              'white_n': len(x), 'white_status': 'Menos de 30 registros completos',
              'bds_p': None, 'bds_stat': None, 'bds_epsilon': None,
              'bds_n': len(residuals), 'bds_status': 'Menos de 30 residuos'}
    if len(x) >= 30:
        scales = x.std(axis=0)
        varying = scales > 1e-12
        if not varying.any():
            result['white_status'] = 'Predictoras numéricas constantes'
        elif np.ptp(white_residuals**2) <= 1e-12:
            result['white_status'] = 'Residuos al cuadrado constantes'
        else:
            # Escalar solo estabiliza el cálculo: no cambia el espacio de la auxiliar.
            z = (x[:, varying]-x[:, varying].mean(axis=0))/scales[varying]
            with threadpool_limits(limits=1):
                # Retirar dependencias exactas (avance = final − inicial) conserva
                # el espacio de cuadrados/interacciones y evita columnas duplicadas.
                _, _, pivots = qr(z, mode='economic', pivoting=True)
                z = z[:, pivots[:np.linalg.matrix_rank(z)]]
                exog = np.column_stack([np.ones(len(x)), z])
                a, b = np.triu_indices(exog.shape[1])
                rank = np.linalg.matrix_rank(exog[:, a]*exog[:, b])
                result['white_df'] = int(rank-1)
                if len(x)-rank < 10:
                    result['white_status'] = 'Menos de 10 grados de libertad residuales en la auxiliar'
                else:
                    try:
                        lm, p, _, _ = het_white(white_residuals, exog)
                        if np.isfinite(lm) and np.isfinite(p):
                            result.update(white_p=float(p), white_lm=float(lm), white_status='Calculado')
                        else:
                            result['white_status'] = 'Cálculo numérico no definido'
                    except (ValueError, np.linalg.LinAlgError, FloatingPointError):
                        result['white_status'] = 'Diseño auxiliar no estimable'
    if len(residuals) >= 30:
        if np.ptp(residuals) <= 1e-12:
            result['bds_status'] = 'Residuos constantes'
        else:
            epsilon = 1.5*np.std(residuals, ddof=1)
            result['bds_epsilon'] = float(epsilon)
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', RuntimeWarning)
                    statistic, p = bds(residuals, max_dim=2, epsilon=epsilon)
                if np.isfinite(statistic) and np.isfinite(p):
                    result.update(bds_p=float(p), bds_stat=float(statistic), bds_status='Calculado')
                else:
                    result['bds_status'] = 'Varianza del estadístico no estimable'
            except (ValueError, np.linalg.LinAlgError, FloatingPointError):
                result['bds_status'] = 'Cálculo numérico no definido'
    return result


def format_p(value):
    if value is None or not np.isfinite(value):
        return 'No estimable'
    if value >= .009:
        return f'{value:.4f}'
    return f'{value:.3e}' if value > 0 else '< 1e-300'


def diagnostic_reading(result):
    white = ('White: varianza no constante.' if result['white_p'] < .05 else
             'White: no se detecta varianza no constante.') if result['white_p'] is not None else 'White no estimable.'
    bds_text = ('BDS: se rechaza IID en el orden del archivo.' if result['bds_p'] < .05 else
                'BDS: no se rechaza IID en el orden del archivo.') if result['bds_p'] is not None else 'BDS no estimable.'
    return white+' '+bds_text

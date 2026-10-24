"""Ejecuta las pruebas unitarias de los originales midiendo cada fit/predict con `TimingRun`.

Las pruebas ajustan los tres modelos originales sobre datos SINTÉTICOS (60–120 filas); no son
reentrenamientos de los modelos del proyecto, pero se registran en TIEMPOS_EJECUCION.md por la
directriz de tiempos. Las llamadas anidadas (KernelRidge dentro de TransformedTargetRegressor)
quedan incluidas en la llamada superior.
"""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

import comun  # noqa: F401  (rutas a Precalculo/ y Dash/)
from model_timing import TimingRun, file_hash
from sklearn.compose import TransformedTargetRegressor
from tn_krr_e3 import TruncatedNewtonKernelRidgeRegressor
from gpr_xgb_hpo_e3 import GPRStackXGBRegressor

HERE = Path(__file__).resolve().parent
TESTS = HERE / 'test_modelos_originales.py'


def main():
    run = TimingRun('Pruebas unitarias sintéticas de los modelos originales (libro E4)', {
        'command': sys.argv, 'script_sha256': file_hash(__file__), 'target_sha256': file_hash(TESTS),
        'data': 'Datos sintéticos generados en las pruebas (60–120 filas); sin datos del proyecto',
        'scope': 'fit/predict de TransformedTargetRegressor (KRR centrado), TN-KRR y GPR–XGBoost; '
                 'la caché GPR va a una carpeta temporal de pytest',
        'repetitions': 'Una por llamada; sin calentamiento', 'device': 'CPU'})

    def wrap(original, stage):
        def measured(model, X, *args, **kwargs):
            with run.measure(stage, type(model).__name__, len(X), script=TESTS.name):
                return original(model, X, *args, **kwargs)
        return measured

    status = 'fallida'
    try:
        patches = [patch.object(cls, name, wrap(getattr(cls, name), stage))
                   for cls in (TransformedTargetRegressor, TruncatedNewtonKernelRidgeRegressor, GPRStackXGBRegressor)
                   for name, stage in (('fit', 'Entrenamiento/refit'), ('predict', 'Inferencia'))]
        for p in patches:
            p.start()
        try:
            code = pytest.main([str(TESTS), '-q', '-p', 'no:cacheprovider'])
        finally:
            for p in patches:
                p.stop()
        status = 'completa' if code == 0 else 'fallida'
    finally:
        run.finish(status)


if __name__ == '__main__':
    main()

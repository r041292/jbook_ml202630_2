"""Ejecuta preparación/validación midiendo los fits y predict de pipelines.

Uso: python Dash/run_measured.py Dash/prepare_data.py
     python Dash/run_measured.py --tests
No mide carga/E/S como inferencia. Las llamadas anidadas quedan incluidas en
la llamada superior y no se suman. La búsqueda del árbol se mide en su evaluador.
"""
import runpy
import sys
import unittest
import joblib
from pathlib import Path
from unittest.mock import patch

from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge
from model_timing import TimingRun, file_hash


def main():
    target = sys.argv[1]
    run = TimingRun('Verificación/preparación · ' + target, {
        'command': sys.argv, 'script_sha256': file_hash(__file__),
        'target_sha256': file_hash(target) if target != '--tests' else 'Suite test_*.py en Dash',
        'manifest_sha256': file_hash(Path(__file__).parent / 'data/manifest.json'),
        'python_sources_sha256': {p.name: file_hash(p) for p in Path(__file__).parent.glob('*.py')},
        'data': 'Artefactos canónicos E3; train 1309, test 188; formularios y lotes de prueba',
        'scope': 'Pipeline.fit/predict y Ridge.fit (sustituto LIME); solapamientos incluidos en llamada superior',
        'repetitions': 'Una por llamada; sin calentamiento; orden del log conservado',
        'device': 'CPU; n_jobs y parámetros del estimador en eventos; sin cambiar configuración'})
    def wrap(original, stage):
        def measured(model, x, *args, **kwargs):
            estimator = model.steps[-1][1] if hasattr(model, 'steps') else model
            with run.measure(stage, type(estimator).__name__, len(x),
                             input_sha256=joblib.hash(x), model_sha256=joblib.hash(model),
                             configuration=estimator.get_params(deep=False),
                             script=target):
                return original(model, x, *args, **kwargs)
        return measured
    status = 'fallida'
    try:
        with patch.object(Pipeline, 'predict', wrap(Pipeline.predict, 'Inferencia')), \
             patch.object(Pipeline, 'fit', wrap(Pipeline.fit, 'Entrenamiento/refit')), \
             patch.object(Ridge, 'fit', wrap(Ridge.fit, 'Entrenamiento/refit')), \
             patch.object(Ridge, 'predict', wrap(Ridge.predict, 'Inferencia')):
            if target == '--tests':
                suite = unittest.defaultTestLoader.discover(str(Path(__file__).parent), pattern='test_*.py')
                result = unittest.TextTestRunner(verbosity=2).run(suite)
                if not result.wasSuccessful():
                    raise SystemExit(1)
            else:
                sys.argv = sys.argv[1:]
                runpy.run_path(str(Path(target).resolve()), run_name='__main__')
        status = 'completa'
    finally:
        run.finish(status)


if __name__ == '__main__':
    main()

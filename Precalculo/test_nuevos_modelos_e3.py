"""Pruebas de interacciones, fugas, equivalencia de métricas y particiones."""
import unittest
import numpy as np
from sklearn.base import clone
from sklearn.metrics import mean_squared_error

from entregable3 import FEATURES, GROUP, TARGET, metrics
from evaluacion_nuevos_e3 import logic_pipeline, partitions, MODEL_DIR, CHECKPOINT, OUTPUT
from logicdt_propio import LogicDTRegressor


class NewModelsTests(unittest.TestCase):
    def test_xor_and_determinism(self):
        X = np.tile([[0, 0], [0, 1], [1, 0], [1, 1]], (40, 1))
        y = np.logical_xor(X[:, 0], X[:, 1]).astype(float)
        model = LogicDTRegressor(n_numeric=0, min_samples_leaf=10, n_iter=200)
        model.fit(X, y)
        np.testing.assert_allclose(model.predict(X), y)
        np.testing.assert_allclose(clone(model).fit(X, y).predict(X), model.predict(X))
        self.assertTrue(any(len(t) == 2 for t in model.terms_))

    def test_cutoffs_use_fit_only_and_constant_fallback(self):
        X = np.arange(80.).reshape(-1, 1)
        model = LogicDTRegressor(n_numeric=1, min_samples_leaf=10, n_iter=10, leaf_model='ridge')
        model.fit(X, X[:, 0]*.2)
        before = model.bit_definitions_.copy()
        self.assertTrue(np.isfinite(model.predict([[1e8]])).all())
        self.assertEqual(before, model.bit_definitions_)
        constant = LogicDTRegressor(n_numeric=0, min_samples_leaf=5).fit(np.zeros((20, 2)), np.arange(20))
        np.testing.assert_allclose(constant.predict(np.zeros((2, 2))), 9.5)

    def test_canonical_folds_and_unseen_category(self):
        train, test, folds, audit = partitions()
        self.assertEqual((len(train), len(test)), (1309, 188))
        self.assertEqual(len(FEATURES), 15)
        self.assertNotIn('nota_final', FEATURES)
        self.assertFalse(set(train[GROUP]) & set(test[GROUP]))
        fit, val = folds[0]
        pipeline = logic_pipeline().set_params(modelo__n_iter=5, modelo__n_restarts=1)
        pipeline.fit(train.iloc[fit][FEATURES], train.iloc[fit][TARGET])
        prep = pipeline.named_steps['preprocesamiento']
        medians = prep.named_transformers_['num_plain'].named_steps['imputer'].statistics_.copy()
        altered = train.iloc[val[:2]][FEATURES].copy()
        altered['programa_en_matricula'] = 'CATEGORIA_NUEVA'
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            self.assertTrue(np.isfinite(pipeline.predict(altered)).all())
        np.testing.assert_array_equal(medians, prep.named_transformers_['num_plain'].named_steps['imputer'].statistics_)

    def test_metrics_exact(self):
        y, p = np.array([1., 2., 4.]), np.array([1.1, 1.8, 3.5])
        self.assertEqual(set(metrics(y, p)), {'RMSE', 'MAE', 'MAPE (%)', 'R²'})
        self.assertEqual(metrics(y, p)['RMSE'], np.sqrt(mean_squared_error(y, p)))

    def test_checkpoint_identity(self):
        import hashlib
        import json
        path = MODEL_DIR / CHECKPOINT
        if not path.exists():
            self.skipTest('Pesos oficiales opcionales aún no descargados')
        manifest = json.loads((MODEL_DIR / 'procedencia.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['repository'], 'Prior-Labs/tabpfn_2_5')
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), manifest['sha256'])

    def test_saved_predictions_reproduce_reports(self):
        import json
        import pandas as pd
        import joblib
        train, test, folds, audit = partitions()
        for key in ['logicdt', 'tabpfn_25']:
            folder = OUTPUT / key
            if not (folder / 'reporte.json').exists():
                continue
            report = json.loads((folder / 'reporte.json').read_text(encoding='utf-8'))
            external = pd.read_csv(folder / 'train_predictions.csv.gz')
            heldout = pd.read_csv(folder / 'test_predictions.csv.gz')
            self.assertEqual(len(external), len(train))
            self.assertEqual(len(heldout), len(test))
            self.assertNotIn(GROUP, external.columns)
            np.testing.assert_array_equal(external['fold'], pd.read_csv(OUTPUT / 'train.csv.gz')['fold'])
            for metric, value in metrics(test[TARGET], heldout['prediccion']).items():
                # TabPFN devuelve float32; su CSV decimal conserva precisión
                # de float32, no doce decimales de una representación float64.
                self.assertAlmostEqual(value, report['test'][metric], delta=1e-6)
            if key == 'logicdt':
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    pred = joblib.load(folder / 'modelo.joblib').predict(test[FEATURES])
                np.testing.assert_allclose(pred, heldout['prediccion'], rtol=1e-12, atol=1e-12)


if __name__ == '__main__':
    unittest.main()

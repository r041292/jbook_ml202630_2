"""Pruebas de separación, categorías desconocidas y artefactos de regresión."""
import json
import unittest
import joblib
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
import modelos_clasicos as classic
from entregable3 import FEATURES, TARGET, NUMERIC, GROUP, load_partitions, grouped_splits, metrics


class ClassicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.train, cls.test, _ = load_partitions()
        cls.report = json.loads((classic.OUTPUT / 'comparacion.json').read_text(encoding='utf-8'))

    def test_same_outer_students_and_no_identifiers_in_models(self):
        predictions = pd.read_csv(classic.OUTPUT / 'train_predictions.csv.gz')
        assignment = np.empty(len(self.train), dtype=int)
        for fold, (fit, val) in enumerate(grouped_splits(self.train), 1):
            assignment[val] = fold
            self.assertFalse(set(self.train.iloc[fit][GROUP]) & set(self.train.iloc[val][GROUP]))
            for inner_fit, inner_val in grouped_splits(self.train.iloc[fit]):
                inner = self.train.iloc[fit]
                self.assertFalse(set(inner.iloc[inner_fit][GROUP]) & set(inner.iloc[inner_val][GROUP]))
        np.testing.assert_array_equal(assignment, predictions['fold'])
        self.assertNotIn(GROUP, predictions)
        self.assertEqual(self.report['source_sha256'], classic.provenance())

    def test_native_category_vocabulary_and_medians_are_fit_only(self):
        fitting = self.train.iloc[:100][FEATURES]
        prep = classic.classic_pipeline('xgboost').named_steps['preprocesamiento'].fit(fitting)
        values = fitting.iloc[:1].copy()
        values['programa_en_matricula'] = 'CATEGORIA_NUEVA_NO_OBSERVADA'
        values['Tiempo_Total_Tiempo'] = np.nan
        transformed = prep.transform(values)
        column = 'cat__programa_en_matricula'
        self.assertTrue(pd.isna(transformed[column].iloc[0]))
        self.assertNotIn('CATEGORIA_NUEVA_NO_OBSERVADA', prep.named_steps['categories'].categories_[column])
        self.assertAlmostEqual(transformed['num__Tiempo_Total_Tiempo'].iloc[0], fitting['Tiempo_Total_Tiempo'].median())
        self.assertEqual(transformed.shape[1], len(FEATURES))
        self.assertTrue(all(isinstance(transformed[c].dtype, pd.CategoricalDtype) for c in transformed if c.startswith('cat__')))

    def test_forest_unknown_categories_are_explicit_codes(self):
        fitting = self.train.iloc[:100][FEATURES]
        prep = classic.classic_pipeline('forest').named_steps['preprocesamiento'].fit(fitting)
        values = fitting.iloc[:1].copy()
        values['programa_en_matricula'] = 'CATEGORIA_NUEVA_NO_OBSERVADA'
        transformed = prep.transform(values)
        index = classic.CATEGORICAL.index('programa_en_matricula') + len(NUMERIC)
        self.assertEqual(transformed[0, index], -1)
        self.assertEqual(transformed.shape[1], len(FEATURES))

    def test_saved_pipelines_reproduce_all_test_metrics(self):
        predictions = pd.read_csv(classic.OUTPUT / 'test_predictions.csv.gz')
        for key in classic.LABELS:
            with self.subTest(model=key):
                pipeline = joblib.load(classic.OUTPUT / f'{key}.joblib')
                self.assertEqual(list(pipeline.feature_names_in_), FEATURES)
                for parameter, value in self.report['models'][key]['best_params'].items():
                    self.assertEqual(pipeline.get_params()[parameter], value)
                output = pipeline.predict(self.test[FEATURES])
                np.testing.assert_allclose(output, predictions[key], rtol=1e-12, atol=1e-12)
                for metric, value in metrics(self.test[TARGET], output).items():
                    self.assertAlmostEqual(value, self.report['models'][key]['test_metrics'][metric], places=10)
        pipeline = joblib.load(classic.OUTPUT / 'xgboost.joblib')
        booster = XGBRegressor(enable_categorical=True)
        booster.load_model(bytearray((classic.OUTPUT / 'xgboost.ubj').read_bytes()))
        np.testing.assert_array_equal(booster.predict(pipeline.named_steps['preprocesamiento'].transform(self.test[FEATURES])),
                                      pipeline.predict(self.test[FEATURES]))


if __name__ == '__main__':
    unittest.main()

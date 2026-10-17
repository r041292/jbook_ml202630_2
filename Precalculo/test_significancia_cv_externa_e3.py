"""Fórmula corregida, familia Holm y procedencia de la comparación externa."""
import hashlib
import json
import unittest

import numpy as np
import pandas as pd
from scipy.stats import t

import significancia_cv_externa_e3 as cv


class CVInferenceTests(unittest.TestCase):
    def test_corrected_formula_known_sample(self):
        values = np.array([1., 2., 3., 4., 5.])
        result = cv.corrected_test(values, .25)
        self.assertAlmostEqual(result['SE_corregido'], np.sqrt(1.125))
        self.assertAlmostEqual(result['t_corregida'], 3/np.sqrt(1.125))
        self.assertAlmostEqual(result['p_bilateral'], 2*t.sf(3/np.sqrt(1.125), 4))
        self.assertGreater(result['p_bilateral'], 2*t.sf(3/np.sqrt(.5), 4))
        negative = cv.corrected_test(-values, .25)
        self.assertAlmostEqual(result['p_bilateral'], negative['p_bilateral'])
        self.assertAlmostEqual(result['IC95_delta_inferior'], -negative['IC95_delta_superior'])
        self.assertIsNone(cv.corrected_test(np.ones(5), .25)['p_bilateral'])
        with self.assertRaises(ValueError):
            cv.corrected_test(values[:4], .25)

    def test_published_pairs_and_holm_family(self):
        table = pd.read_csv(cv.OUTPUT / 'contrastes_vs_svm.csv')
        folds = pd.read_csv(cv.OUTPUT / 'fold_metrics.csv')
        report = json.loads((cv.OUTPUT / 'reporte.json').read_text(encoding='utf-8'))
        reference = folds.loc[folds.Modelo.eq(cv.REFERENCE)].set_index('Fold').RMSE.sort_index()
        evaluated = table.dropna(subset=['p_bilateral']).copy()
        self.assertEqual(len(evaluated), 24)
        self.assertEqual(len(folds), 125)
        for row in evaluated.itertuples():
            candidate = folds.loc[folds.Modelo.eq(row.Modelo)].set_index('Fold').RMSE.sort_index()
            result = cv.corrected_test(candidate-reference, report['correction_ratio'])
            for column, value in result.items():
                self.assertAlmostEqual(getattr(row, column), value, places=12)
            self.assertAlmostEqual(row.RMSE_CV, candidate.mean())
        ordered = evaluated.sort_values('p_bilateral')
        raw = ordered.p_bilateral.to_numpy()
        expected_holm = np.minimum(1, np.maximum.accumulate(raw*np.arange(24, 0, -1)))
        np.testing.assert_allclose(ordered.p_Holm, expected_holm, atol=1e-12)
        self.assertFalse(table.conclusion.eq('Mejora significativa').any())
        self.assertEqual(table.loc[table.Modelo.eq('Dummy media'), 'conclusion'].item(), 'Deterioro significativo')
        missing = table.loc[table.Modelo.eq('TabPFN 2.5 fine-tuned')].iloc[0]
        self.assertEqual(missing.folds, 0)
        self.assertTrue(pd.isna(missing.p_Holm))
        self.assertEqual(table.iloc[0].Modelo, 'Kernel Ridge RBF')
        self.assertNotIn('GPR sola (ablación)', set(table.Modelo))

    def test_provenance_and_no_test_predictions(self):
        report = json.loads((cv.OUTPUT / 'reporte.json').read_text(encoding='utf-8'))
        self.assertFalse(report['training_performed'])
        self.assertFalse(report['test_used'])
        self.assertEqual(report['family_size'], 24)
        for path, digest in report['sources_sha256'].items():
            self.assertNotIn('test_predictions', path)
            self.assertEqual(hashlib.sha256((cv.BOOK / path).read_bytes()).hexdigest(), digest)
        self.assertEqual(hashlib.sha256((cv.BOOK / 'significancia_cv_externa_e3.py').read_bytes()).hexdigest(), report['generator_sha256'])
        self.assertAlmostEqual(report['correction_ratio'], .25, places=5)


if __name__ == '__main__':
    unittest.main()

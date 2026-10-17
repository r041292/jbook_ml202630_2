"""Verifica unidad de permutación y métricas de la evaluación nueva."""
import json
import unittest
import numpy as np
import pandas as pd

from evaluar_tabpfn25_finetuned_e3 import paired_comparison, DEFAULT_BUNDLE
from entregable3 import OUTPUT, TARGET, metrics


class FinetunedEvaluationTests(unittest.TestCase):
    def test_permutation_keeps_repeated_student_rows_together(self):
        y = np.arange(1., 13.)
        groups = np.repeat(np.arange(6), 2)
        result = paired_comparison(y, y, y+1, groups)
        # 6 unidades, no 12: prueba exacta de 2**6 signos, dos extremos.
        self.assertEqual(result[0]['p_bilateral'], 2/64)
        self.assertEqual(result[0]['p_bilateral'], result[1]['p_bilateral'])
        self.assertAlmostEqual(result[0]['diferencia_ajustado_menos_referencia'], -1.)
        self.assertLess(result[0]['IC_97.5%'], 0)
        self.assertGreater(result[1]['IC_2.5%'], 0)

    def test_identical_predictions(self):
        y = np.arange(1., 13.)
        result = paired_comparison(y, y+.1, y+.1, np.arange(12))
        self.assertTrue(all(row['p_bilateral'] == 1. for row in result))
        self.assertTrue(all(row['IC_2.5%'] == row['IC_97.5%'] == 0. for row in result))

    def test_export_reproduces_comparison(self):
        folder = OUTPUT/'tabpfn_25_finetuned'/DEFAULT_BUNDLE.name
        if not (folder/'reporte.json').exists():
            self.skipTest('Evaluación aún no completada.')
        report = json.loads((folder/'reporte.json').read_text(encoding='utf-8'))
        frame = pd.read_csv(folder/'test_predictions.csv.gz')
        self.assertEqual(len(frame), 188)
        self.assertNotIn('estudiante', frame.columns)
        for key, value in metrics(frame[TARGET], frame.prediccion).items():
            self.assertAlmostEqual(value, report['test'][key], places=12)
        self.assertEqual(report['epochs_final'], 5)
        for comp in report['paired_comparisons']:
            self.assertEqual(comp['rows'][0]['p_bilateral'], comp['rows'][1]['p_bilateral'])
            self.assertGreaterEqual(comp['rows'][0]['p_Holm_dos_comparaciones'], comp['rows'][0]['p_bilateral'])


if __name__ == '__main__':
    unittest.main()

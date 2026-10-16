"""Pruebas de RIM: recuperación sin fuga, atención y predicciones reproducibles."""
import json
import unittest
import numpy as np
import pandas as pd
import torch
from sklearn.base import clone

from entregable3 import FEATURES, GROUP, TARGET, OUTPUT, metrics
from evaluacion_nuevos_e3 import partitions
from rim_regresion_e3 import BM25Index, RIMNetwork, RIMRegressor, FieldTokenizer


class RIMTests(unittest.TestCase):
    def test_excludes_every_row_of_same_student_and_masks_no_match(self):
        tokens = np.array([[1, 5], [1, 5], [2, 5], [3, 6]])
        groups = np.array(['a', 'a', 'b', 'c'])
        index = BM25Index().fit(tokens, groups)
        result = index.retrieve(tokens[:1], 5, ['a'])[0]
        self.assertTrue(all(groups[i] != 'a' for i in result if i >= 0))
        self.assertEqual(result[0], 2)
        self.assertTrue((index.retrieve(np.array([[10, 20]]), 3) == -1).all())

    def test_bm25_prefers_rare_matching_field(self):
        tokens = np.array([[1, 9], [2, 8], [2, 7], [2, 6]])
        index = BM25Index().fit(tokens, np.arange(4))
        self.assertGreater(index.idf_[1], index.idf_[2])
        query = np.array([[1, 8]])
        self.assertEqual(index.retrieve(query, 2)[0].tolist(), [0, 1])

    def test_attention_is_order_invariant_and_empty_retrieval_is_finite(self):
        torch.manual_seed(42)
        net = RIMNetwork(100, 5, embedding_dim=4).eval()
        query = torch.randint(1, 100, (3, 15))
        neighbors = torch.randint(1, 100, (3, 4, 15))
        labels = torch.randint(1, 5, (3, 4))
        mask = torch.ones((3, 4), dtype=torch.bool)
        perm = [2, 0, 3, 1]
        with torch.no_grad():
            a = net(query, neighbors, labels, mask)
            b = net(query, neighbors[:, perm], labels[:, perm], mask[:, perm])
            torch.testing.assert_close(a, b)
            empty = net(query, torch.zeros_like(neighbors), torch.zeros_like(labels), torch.zeros_like(mask))
            self.assertTrue(torch.isfinite(empty).all())

    def test_retrieved_labels_have_direct_path_to_prediction(self):
        net = RIMNetwork(100, 5, embedding_dim=4).eval()
        with torch.no_grad():
            for p in net.parameters():
                p.zero_()
            net.label_embedding.weight[1, 0] = 1.
            net.label_embedding.weight[2, 0] = 2.
            net.output.weight[0, -4] = 1.
            query = torch.ones((1, 15), dtype=torch.long)
            neighbor = torch.ones((1, 1, 15), dtype=torch.long)
            mask = torch.ones((1, 1), dtype=torch.bool)
            a = net(query, neighbor, torch.ones((1, 1), dtype=torch.long), mask)
            b = net(query, neighbor, torch.full((1, 1), 2, dtype=torch.long), mask)
            self.assertAlmostEqual(float(b-a), 1.)

    def test_fit_only_tokenization_and_deterministic_training(self):
        train, test, _, _ = partitions()
        frame = train.iloc[:100]
        model = RIMRegressor(epochs=2, embedding_dim=4, n_neighbors=5)
        with self.assertRaises(ValueError):
            model.fit(frame[FEATURES], frame[TARGET])
        model.fit(frame[FEATURES], frame[TARGET], frame[GROUP])
        groups = frame[GROUP].to_numpy()
        for i, rows in enumerate(model.training_retrieval_):
            self.assertFalse(any(groups[j] == groups[i] for j in rows if j >= 0))
        medians = model.tokenizer_.preprocessor_.named_transformers_['num_plain'].named_steps['imputer'].statistics_.copy()
        unseen = test.iloc[:3][FEATURES].copy()
        unseen['programa_en_matricula'] = 'NUEVO_PROGRAMA'
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            a = model.predict(unseen)
            np.testing.assert_allclose(a, clone(model).fit(frame[FEATURES], frame[TARGET], groups).predict(unseen))
        self.assertTrue(np.isfinite(a).all())
        np.testing.assert_array_equal(medians, model.tokenizer_.preprocessor_.named_transformers_['num_plain'].named_steps['imputer'].statistics_)

    def test_saved_oof_and_test_metrics(self):
        folder = OUTPUT/'rim'
        if not (folder/'reporte.json').exists():
            self.skipTest('Evaluación todavía en ejecución.')
        report = json.loads((folder/'reporte.json').read_text(encoding='utf-8'))
        frame = pd.read_csv(folder/'test_predictions.csv.gz')
        for name, value in metrics(frame[TARGET], frame.prediccion).items():
            self.assertAlmostEqual(value, report['test'][name], places=12)
        oof = pd.read_csv(folder/'train_predictions.csv.gz')
        np.testing.assert_array_equal(oof.fold, pd.read_csv(OUTPUT/'train.csv.gz').fold)
        self.assertEqual(len(oof), 1309)
        self.assertEqual(len(frame), 188)
        self.assertNotIn(GROUP, oof)
        self.assertTrue(all(row['shared_students'] == 0 for row in report['fold_audit']))
        import joblib
        _, heldout, _, _ = partitions()
        saved = joblib.load(report['private_model'])
        np.testing.assert_allclose(saved.predict(heldout[FEATURES]), frame.prediccion, rtol=1e-12, atol=1e-12)
        self.assertEqual(len(report['family_vs_svm']), 9)
        self.assertTrue(all(row['p_Holm_nueve_metodos'] >= row['p_bilateral']
                            for row in report['family_vs_svm']))


if __name__ == '__main__':
    unittest.main()

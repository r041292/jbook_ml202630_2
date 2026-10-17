"""Verificación sin fine-tuning del modelo TabPFN ni cambios a pesos oficiales."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from finetune_tabpfn25_e3 import grouped_episodes, context_query_split, parser, native_save
from evaluacion_nuevos_e3 import prepare_tabpfn_environment


class FinetunePreparationTests(unittest.TestCase):
    def test_episodes_cover_every_row_and_preserve_repeated_students(self):
        groups = np.repeat(np.arange(53), np.arange(53) % 4 + 1)
        episodes = grouped_episodes(groups, 17, 42)
        np.testing.assert_array_equal(np.sort(np.concatenate(episodes)), np.arange(len(groups)))
        owners = {}
        for k, ix in enumerate(episodes):
            for group in np.unique(groups[ix]):
                self.assertNotIn(group, owners)
                owners[group] = k
            a, b = context_query_split(groups[ix], 42+k)
            self.assertFalse(set(groups[ix][a]) & set(groups[ix][b]))
            np.testing.assert_array_equal(np.sort(np.r_[a, b]), np.arange(len(ix)))
        again = grouped_episodes(groups, 17, 42)
        self.assertEqual([v.tolist() for v in episodes], [v.tolist() for v in again])

    def test_large_groups_and_single_group_remainder(self):
        groups = np.array(['a']*40+['b']*2+['c']+['d']+['e'])
        episodes = grouped_episodes(groups, 8, 9)
        self.assertTrue(all(len(np.unique(groups[ix])) >= 2 for ix in episodes))
        with self.assertRaises(ValueError):
            grouped_episodes(np.array(['a']*10), 8, 42)

    def test_atomic_native_checkpoint_write(self):
        prepare_tabpfn_environment()
        # Usar el workspace: el temporal del sandbox Windows puede tener ACL
        # que impiden incluso escribir el archivo recién creado.
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent/'modelos_preentrenados') as directory:
            path = Path(directory)/'weights.ckpt'
            def fake_save(model, save_path, additional_fields):
                self.assertEqual(additional_fields['epoch'], 3)
                Path(save_path).write_bytes(b'checkpoint_de_prueba')
            with patch('tabpfn.model_loading.save_tabpfn_model', side_effect=fake_save):
                native_save(SimpleNamespace(), path, 3)
            self.assertEqual(path.read_bytes(), b'checkpoint_de_prueba')
            self.assertFalse(path.with_suffix('.partial').exists())

    def test_default_does_not_evaluate_test(self):
        args = parser().parse_args([])
        self.assertFalse(args.evaluate_test)
        self.assertFalse(args.check_only)
        self.assertEqual(args.device, 'auto')
        self.assertEqual(args.eval_estimators, 4)


if __name__ == '__main__':
    unittest.main()

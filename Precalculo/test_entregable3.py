"""Controles de fuga por estudiante/periodo y correspondencia con filas reales."""
import unittest
from unittest.mock import patch
import pandas as pd
import entregable3 as e3


class E3Tests(unittest.TestCase):
    def test_students_stay_together_in_outer_and_inner_folds(self):
        train, test, audit = e3.load_partitions()
        self.assertFalse(set(train[e3.GROUP]) & set(test[e3.GROUP]))
        self.assertLess(train[e3.PERIOD].max(), test[e3.PERIOD].min())
        self.assertGreater(len(train) - train[e3.GROUP].nunique(), 0)
        seen = []
        for fit, val in e3.grouped_splits(train):
            self.assertFalse(set(train.iloc[fit][e3.GROUP]) & set(train.iloc[val][e3.GROUP]))
            seen.extend(val.tolist())
            inner = train.iloc[fit]
            for a, b in e3.grouped_splits(inner):
                self.assertFalse(set(inner.iloc[a][e3.GROUP]) & set(inner.iloc[b][e3.GROUP]))
        self.assertEqual(sorted(seen), list(range(len(train))))
        self.assertEqual(len(train) + len(test) + audit['missing_target'], audit['source_rows'])

    def test_test_targets_do_not_change_training_or_partition(self):
        expected, _, _ = e3.load_partitions()
        raw = pd.read_csv(e3.BOOK / 'Data/Datos_Brutos.csv', sep=';', decimal=',', encoding='utf-8-sig')
        raw.loc[raw['Periodo'].eq(e3.TEST_PERIOD), 'nota primer parcial'] = 0.5
        with patch.object(e3.pd, 'read_csv', return_value=raw):
            actual, _, _ = e3.load_partitions()
        pd.testing.assert_frame_equal(actual, expected)

    def test_repeated_test_student_is_purged_even_without_test_target(self):
        raw = pd.read_csv(e3.BOOK / 'Data/Datos_Brutos.csv', sep=';', decimal=',', encoding='utf-8-sig')
        idx = raw.index[raw['Periodo'].eq(e3.TEST_PERIOD)][0]
        earlier = raw.loc[raw['Periodo'].lt(e3.TEST_PERIOD) & raw['nota primer parcial'].notna()].iloc[0]
        raw.loc[idx, 'pidm en matricula'] = earlier['pidm en matricula']
        raw.loc[idx, 'nota primer parcial'] = float('nan')
        with patch.object(e3.pd, 'read_csv', return_value=raw):
            train, _, audit = e3.load_partitions()
        self.assertGreater(audit['purged_overlap_rows'], 0)
        self.assertNotIn(str(earlier['pidm en matricula']), set(train[e3.GROUP]))


if __name__ == '__main__':
    unittest.main()

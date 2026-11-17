import unittest

import pandas as pd

from interval_coverage import study
from kinetics import load_data


class CoverageTests(unittest.TestCase):
    def test_study_is_seeded_and_accounts_for_every_repeat(self):
        frame, _ = load_data()
        table = study(frame, repeats=2, seed=43)
        pd.testing.assert_frame_equal(table, study(frame, repeats=2, seed=43))
        self.assertEqual(len(table), 4)
        self.assertTrue((table.completed + table.failed == table.repeats).all())
        self.assertTrue((table.coverage == table.covered / table.completed).all())
        self.assertTrue((table.open_intervals <= table.completed).all())

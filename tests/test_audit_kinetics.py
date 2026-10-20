import tempfile
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from audit_kinetics import concentration_audit, run
from kinetics import ROOT, load_data, michaelis_menten


class ConcentrationAuditTests(unittest.TestCase):
    def test_all_rows_leave_once_and_repeated_levels_leave_together(self):
        frame, _ = load_data()
        table, _ = concentration_audit(frame)
        self.assertEqual(len(table), 12)
        self.assertEqual(table.omitted_rows.sum(), 23)
        ids = [int(i) for cell in table.omitted_row_ids for i in cell.split(';')]
        self.assertEqual(sorted(ids), sorted(frame.row_id.tolist()))
        for row in table.itertuples():
            subset = frame[(frame.state == row.state) & (frame.conc == row.omitted_concentration_ppm)]
            self.assertEqual(len(subset), row.omitted_rows)
        self.assertEqual((table.prediction_scope == 'within_retained_range').sum(), 8)

    def test_exact_curve_stays_stable_without_inventing_uncertainty(self):
        x = np.repeat([.01, .04, .1, .5, 1.], 2)
        frame = pd.DataFrame({'row_id': range(len(x)), 'state': ['synthetic'] * len(x),
                              'conc': x, 'rate': michaelis_menten(x, 200, .08)})
        table, _ = concentration_audit(frame)
        np.testing.assert_allclose(table.vmax_change_percent, 0, atol=1e-5)
        np.testing.assert_allclose(table.km_change_percent, 0, atol=1e-5)
        self.assertLess(table.omitted_rmse_counts_per_min_per_min.max(), 1e-6)

    def test_insufficient_levels_and_duplicate_ids_fail(self):
        frame, _ = load_data()
        with self.assertRaisesRegex(ValueError, 'three distinct'):
            concentration_audit(frame[frame.conc <= .06])
        with self.assertRaisesRegex(ValueError, 'unique row'):
            concentration_audit(pd.concat([frame, frame.iloc[:1]]))

    def test_run_records_verified_provenance_and_does_not_overwrite_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run(Path(tmp))
            self.assertEqual(result['refits'], 12)
            self.assertEqual(result['omitted_rows_total'], 23)
            self.assertIn('Puromycin.R', result['input_sha256'])
            for name in ['audit.json', 'report.md', 'concentration_sensitivity.csv']:
                self.assertTrue((Path(tmp) / name).is_file())
        with self.assertRaisesRegex(ValueError, 'separate'):
            run(ROOT / 'results')


if __name__ == '__main__':
    unittest.main()

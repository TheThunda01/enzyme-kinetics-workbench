import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from scipy.stats import chi2

import kinetics as k


class ModelTests(unittest.TestCase):
    def test_zero_half_saturation_and_asymptote(self):
        values = k.michaelis_menten([0, .1, 1e9], 200, .1)
        np.testing.assert_allclose(values[:2], [0, 100])
        self.assertAlmostEqual(values[2], 200, places=6)

    def test_invalid_model_values_fail(self):
        for substrate, vmax, km in [([-1], 2, 1), ([1], -2, 1), ([1], 2, 0), ([np.nan], 2, 1)]:
            with self.assertRaises(ValueError):
                k.michaelis_menten(substrate, vmax, km)

    def test_known_curve_parameters_recovered(self):
        x = np.array([.01, .03, .1, .2, .5, 1.])
        fit = k.fit_curve(x, k.michaelis_menten(x, 175, .08))
        self.assertAlmostEqual(fit['vmax'], 175, places=5)
        self.assertAlmostEqual(fit['km'], .08, places=7)
        self.assertLess(fit['rss'], 1e-12)

    def test_log_jacobian_matches_finite_difference(self):
        x = np.array([.02, .1, 1.])
        theta = np.log([210., .06])
        h = 1e-6
        numeric = np.column_stack([(k.michaelis_menten(x, *np.exp(theta + np.eye(2)[i] * h)) -
                                    k.michaelis_menten(x, *np.exp(theta - np.eye(2)[i] * h))) / (2 * h)
                                   for i in range(2)])
        np.testing.assert_allclose(k.log_parameter_jacobian(x, *np.exp(theta)), numeric, rtol=1e-6)

    def test_one_concentration_cannot_identify_two_parameters(self):
        with self.assertRaisesRegex(ValueError, 'One concentration'):
            k.fit_curve([.1, .1, .1], [5, 6, 7])

    def test_invalid_pairs_rejected(self):
        for x, y in [([1, 2], [2, 3]), ([1, 2, 3], [1, 2]), ([0, 1, 2], [1, 2, 3]),
                     ([1, 2, 3], [1, np.inf, 2]), ([1, 2, 3], [-1, 2, 3])]:
            with self.assertRaises(ValueError):
                k.validate_xy(x, y)


class DataAndProfileTests(unittest.TestCase):
    def test_source_conversion_and_documented_dimensions(self):
        frame, _ = k.load_data()
        self.assertEqual(frame.shape, (23, 4))
        self.assertEqual(frame.state.value_counts().to_dict(), {'treated': 12, 'untreated': 11})
        self.assertEqual((frame.conc.min(), frame.conc.max()), (.02, 1.1))

    def test_tampered_file_fails_before_analysis(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'x').write_text('tampered')
            (root / 'manifest.json').write_text(json.dumps({'files': [{'path':'x', 'bytes':0, 'sha256':'bad'}]}))
            with self.assertRaisesRegex(ValueError, 'fingerprint'):
                k.load_data(root)

    def test_profile_matches_fitted_minimum_and_interval_endpoints(self):
        data, _ = k.load_data()
        data = data[data.state == 'treated']
        fit = k.fit_curve(data.conc, data.rate)
        rss, vmax = k.profile_rss(fit['km'], data.conc, data.rate)
        self.assertAlmostEqual(rss, fit['rss'], places=7)
        self.assertAlmostEqual(vmax, fit['vmax'], places=4)
        profile, interval = k.profile_curve(data.conc, data.rate, fit)
        self.assertTrue(interval['lower_closed'] and interval['upper_closed'])
        for endpoint in ['approximate_95_percent_lower', 'approximate_95_percent_upper']:
            value, _ = k.profile_rss(interval[endpoint], data.conc, data.rate)
            statistic = len(data) * np.log(value / fit['rss'])
            self.assertAlmostEqual(statistic, chi2.ppf(.95, 1), places=6)
        self.assertGreaterEqual(float(profile.likelihood_ratio.min()), 0)

    def test_zero_residual_profile_does_not_invent_uncertainty(self):
        x = np.array([.01, .03, .1, .2, .5, 1.])
        y = k.michaelis_menten(x, 175, .08)
        fit = k.fit_curve(x, y)
        fit['rss'] = 0
        with self.assertRaisesRegex(ValueError, 'noise scale'):
            k.profile_curve(x, y, fit)

    def test_profile_respects_same_computational_vmax_bound_as_fit(self):
        x = np.array([.01, .1, 1.])
        rss, vmax = k.profile_rss(.1, x, np.full(3, 1e12))
        self.assertEqual(vmax, k.PARAMETER_BOUNDS[1])
        expected = np.sum((1e12 - k.michaelis_menten(x, vmax, .1)) ** 2)
        self.assertEqual(rss, expected)

    def test_information_scenarios_are_conditional_not_simulated_observations(self):
        summary, grids = k.information_scenarios()
        self.assertEqual(len(grids), 36)
        self.assertTrue((summary.points == 12).all())
        values = summary.set_index('scenario')
        self.assertGreater(values.loc['low_only', 'information_condition_number'],
                           values.loc['wide_range', 'information_condition_number'])
        self.assertTrue((summary.information_determinant > 0).all())

    def test_full_pipeline_generates_complete_finite_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            # Emulate a legacy Windows locale while preserving explicit encodings.
            with patch('io.text_encoding', side_effect=lambda encoding, stacklevel=2: encoding or 'cp1252'):
                summary = k.run(out=out)
            self.assertEqual(summary['fits']['treated']['full_range']['n'], 12)
            self.assertEqual(summary['fits']['untreated']['full_range']['n'], 11)
            self.assertEqual(json.loads((out / 'summary.json').read_text()), summary)
            for name in ['fitted_curves.png','residual_diagnostics.png','km_profiles.png','conditional_information.png']:
                self.assertGreater((out / name).stat().st_size, 1000)
            report = (out / 'report.md').read_text(encoding='utf-8')
            self.assertIn('asymptotic', report)
            self.assertIn('0.0489–0.0830', report)


if __name__ == '__main__':
    unittest.main()

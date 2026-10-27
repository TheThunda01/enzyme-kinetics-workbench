import csv
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.build_profile_explorer import load_profiles

ROOT = Path(__file__).resolve().parents[1]


class ProfileExplorerChecks(unittest.TestCase):
    def test_saved_profiles_validate_and_preserve_excluded_observations(self):
        groups = load_profiles()
        self.assertEqual(sum(len(g['points']) for g in groups), 964)
        self.assertEqual(len(groups), 4)
        for group in groups:
            observations = group['observations']
            self.assertEqual(len(observations), 12 if group['state'] == 'treated' else 11)
            self.assertEqual(sum(o['included'] for o in observations), group['fit']['n'])
            if group['scope'] == 'low_range_only':
                self.assertTrue(any(not o['included'] for o in observations))

    def test_changed_profile_objective_or_parameter_is_rejected(self):
        for field in ('profile_vmax','rss','likelihood_ratio'):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                path=Path(temp)
                shutil.copy(ROOT/'results/summary.json',path/'summary.json')
                with (ROOT/'results/km_profiles.csv').open(newline='',encoding='utf-8') as handle:
                    reader=csv.DictReader(handle)
                    rows=list(reader)
                    fields=reader.fieldnames
                rows[0][field]=str(float(rows[0][field])*1.1)
                with (path/'km_profiles.csv').open('w',newline='',encoding='utf-8') as handle:
                    writer=csv.DictWriter(handle,fieldnames=fields)
                    writer.writeheader();writer.writerows(rows)
                with self.assertRaisesRegex(ValueError,'does not reproduce'):
                    load_profiles(path)


if __name__=='__main__':
    unittest.main()

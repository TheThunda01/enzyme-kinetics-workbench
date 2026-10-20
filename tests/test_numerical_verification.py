import unittest
from pathlib import Path
import shutil
import tempfile
import numpy as np
import pandas as pd
from verify_kinetics import ROOT, main, scalar_fit, compare_fit, verify


class IndependentNumericalTests(unittest.TestCase):
    def test_exact_parameters_recovered_without_main_solver(self):
        x=np.array([.01,.03,.1,.3,1.]);y=180*x/(.07+x)
        result=scalar_fit(x,y)
        self.assertAlmostEqual(result['vmax'],180,places=5)
        self.assertAlmostEqual(result['km'],.07,places=7)

    def test_known_wrong_saved_parameters_fail_agreement(self):
        x=np.array([.01,.03,.1,.3,1.]);y=180*x/(.07+x)
        result=compare_fit(x,y,200,.1)
        self.assertFalse(result['vmax_agrees']);self.assertFalse(result['km_agrees'])
        self.assertFalse(result['rss_agrees'])

    def test_all_saved_scopes_are_checked(self):
        rows,report=verify()
        self.assertEqual(report['fits_checked'],16)
        self.assertEqual(report['status'],'passed')
        self.assertEqual(sum(r['scope']=='omitted_level' for r in rows),12)

    def test_invalid_data_fail(self):
        for x,y in [([1,1,1],[1,2,3]),([1,2,3],[1,float('nan'),3]),([0,1,2],[1,2,3])]:
            with self.assertRaises(ValueError):scalar_fit(x,y)

    def test_cli_checks_requested_result_paths_and_detects_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);results=root/'results';omitted=root/'omitted';results.mkdir();omitted.mkdir()
            shutil.copy(ROOT/'results/parameter_estimates.csv',results/'parameter_estimates.csv')
            shutil.copy(ROOT/'examples/concentration-audit/concentration_sensitivity.csv',omitted/'concentration_sensitivity.csv')
            args=['--results-dir',str(results),'--audit-dir',str(omitted),'--out',str(root/'checked')]
            self.assertEqual(main(args),0)
            table=pd.read_csv(results/'parameter_estimates.csv');table.loc[0,'vmax']*=1.2;table.to_csv(results/'parameter_estimates.csv',index=False)
            self.assertEqual(main(args),1)


if __name__=='__main__':unittest.main()

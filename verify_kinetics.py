"""Check saved fit parameters using a separate one-dimensional numerical route."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar

from kinetics import ROOT, load_data

RTOL, ATOL = 1e-5, 1e-7
BOUNDS = (1e-9, 1e9)


def scalar_fit(x, y):
    """Eliminate V analytically; scan log K then minimize each bracketed basin.

    Does not call the main model, residual, Jacobian, fit or profile functions.
    The scan is a finite numerical search, not a proof of global optimality.
    """
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if x.ndim != 1 or y.shape != x.shape or len(x) < 3 or len(set(x)) < 2:
        raise ValueError('Need three paired observations at two or more concentrations')
    if not np.isfinite(x).all() or not np.isfinite(y).all() or (x <= 0).any() or (y <= 0).any():
        raise ValueError('Observed values must be finite and positive')
    def objective(log_k, details=False):
        k = math.exp(log_k)
        g = [float(s) / (k + float(s)) for s in x]
        v = math.fsum(a * float(b) for a, b in zip(g, y)) / math.fsum(a*a for a in g)
        v = max(BOUNDS[0], min(BOUNDS[1], v))
        rss = math.fsum((float(b) - v*a)**2 for a, b in zip(g, y))
        return (v, k, rss) if details else rss
    grid = np.linspace(math.log(BOUNDS[0]), math.log(BOUNDS[1]), 801)
    values = [objective(t) for t in grid]
    candidates = [(values[0], grid[0]), (values[-1], grid[-1])]
    for i in range(1, len(grid)-1):
        if values[i] <= values[i-1] and values[i] <= values[i+1]:
            result = minimize_scalar(objective, bounds=(grid[i-1], grid[i+1]),
                                     method='bounded', options={'xatol': 1e-12, 'maxiter': 1000})
            if result.success and np.isfinite(result.fun):
                candidates.append((float(result.fun), float(result.x)))
    if len(candidates) == 2 and min(values) < min(values[0], values[-1]):
        raise ValueError('No interior scalar minimum converged')
    _, selected = min(candidates)
    v, k, rss = objective(selected, True)
    return {'vmax': v, 'km': k, 'rss': rss}


def compare_fit(x, y, saved_vmax, saved_km):
    saved_vmax, saved_km = float(saved_vmax), float(saved_km)
    if not np.isfinite([saved_vmax, saved_km]).all() or min(saved_vmax, saved_km) <= 0:
        raise ValueError('Saved parameters must be positive and finite')
    separate = scalar_fit(x, y)
    rss = math.fsum((float(rate) - saved_vmax * float(s) / (saved_km + float(s)))**2
                    for s, rate in zip(x, y))
    close = lambda a, b: math.isclose(a, b, rel_tol=RTOL, abs_tol=ATOL)
    return {'saved_vmax': saved_vmax, 'saved_km': saved_km,
            'independent_vmax': separate['vmax'], 'independent_km': separate['km'],
            'saved_parameter_rss': rss, 'independent_rss': separate['rss'],
            'vmax_agrees': close(saved_vmax, separate['vmax']),
            'km_agrees': close(saved_km, separate['km']), 'rss_agrees': close(rss, separate['rss'])}


def verify(data_dir=ROOT/'data', results_dir=ROOT/'results', audit_dir=ROOT/'examples/concentration-audit'):
    data, source = load_data(Path(data_dir))
    saved_path = Path(results_dir)/'parameter_estimates.csv'
    audit_path = Path(audit_dir)/'concentration_sensitivity.csv'
    saved, omissions = pd.read_csv(saved_path), pd.read_csv(audit_path)
    expected = {(s, scope) for s in data.state.unique() for scope in ('full_range', 'low_range_only')}
    keys = list(zip(saved.state, saved.scope))
    if set(keys) != expected or len(keys) != len(expected):
        raise ValueError('Saved fit keys differ from full and low-range contract')
    expected_omitted = {(s, float(c)) for s in data.state.unique() for c in data[data.state == s].conc.unique()}
    keys = list(zip(omissions.state, omissions.omitted_concentration_ppm))
    if set(keys) != expected_omitted or len(keys) != len(expected_omitted):
        raise ValueError('Saved omission keys differ from concentration contract')
    rows = []
    for row in saved.itertuples():
        selected = data[data.state == row.state]
        if row.scope == 'low_range_only': selected = selected[selected.conc <= .11]
        rows.append({'state': row.state, 'scope': row.scope, 'omitted_concentration_ppm': None,
                     'n': len(selected), **compare_fit(selected.conc, selected.rate, row.vmax, row.km)})
    for row in omissions.itertuples():
        selected = data[(data.state == row.state) & (data.conc != row.omitted_concentration_ppm)]
        rows.append({'state': row.state, 'scope': 'omitted_level',
                     'omitted_concentration_ppm': row.omitted_concentration_ppm, 'n': len(selected),
                     **compare_fit(selected.conc, selected.rate, row.vmax, row.km)})
    passed = all(row['vmax_agrees'] and row['km_agrees'] and row['rss_agrees'] for row in rows)
    return rows, {'schema_version': '1.0', 'status': 'passed' if passed else 'failed', 'fits_checked': len(rows),
                  'rtol': RTOL, 'atol': ATOL, 'bounds': list(BOUNDS),
                  'method': 'Analytic conditional Vmax; 801-point log-Km scan and bounded scalar minimization',
                  'input_sha256': {r['path']: r['sha256'] for r in source['files']},
                  'saved_result_sha256': {str(p.name): hashlib.sha256(p.read_bytes()).hexdigest() for p in (saved_path, audit_path)},
                  'scope': 'Same bounded least-squares objective, different numerical implementation. Agreement is not biological validation or proof of a global minimum.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT/'examples/numerical-verification')
    parser.add_argument('--data-dir', type=Path, default=ROOT/'data')
    parser.add_argument('--results-dir', type=Path, default=ROOT/'results')
    parser.add_argument('--audit-dir', type=Path, default=ROOT/'examples/concentration-audit')
    args = parser.parse_args(argv)
    try:
        rows, report = verify(args.data_dir, args.results_dir, args.audit_dir)
        if args.out.resolve() in {p.resolve() for p in (args.data_dir, args.results_dir, args.audit_dir)}:
            raise ValueError('Verification output must be separate from its inputs')
        args.out.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_csv(args.out/'fit_comparison.csv', index=False, float_format='%.12g')
        (args.out/'verification.json').write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False)+'\n')
        print(f"{report['status']}: {report['fits_checked']} saved fits checked; rtol={RTOL:g}, atol={ATOL:g}")
        return 0 if report['status'] == 'passed' else 1
    except (ValueError, OSError, KeyError, AttributeError) as error:
        print(f'Numerical verification stopped: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

"""Build an offline Plotly explorer from verified, saved profile tables.

The explorer changes only the displayed candidate curve; it does not refit data,
alter observations, or replace the archived analysis outputs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from kinetics import load_data  # noqa: E402


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_profiles(results_dir=ROOT / 'results'):
    results_dir = Path(results_dir)
    data, _ = load_data()
    summary = json.loads((results_dir / 'summary.json').read_text(encoding='utf-8'))
    with (results_dir / 'km_profiles.csv').open(newline='', encoding='utf-8') as handle:
        rows = list(csv.DictReader(handle))
    expected = {(state,scope) for state in ('treated','untreated') for scope in ('full_range','low_range_only')}
    if {(r['state'],r['scope']) for r in rows} != expected:
        raise ValueError('Expected exactly four label/range profile groups')
    groups = []
    for state, scope in sorted(expected):
        selected = [r for r in rows if r['state'] == state and r['scope'] == scope]
        points = [{key: float(r[key]) for key in ('km','profile_vmax','rss','likelihood_ratio')} for r in selected]
        if len(points) < 3 or any(not math.isfinite(v) for p in points for v in p.values()):
            raise ValueError('Profiles need at least three finite rows')
        if any(p['km'] <= 0 or p['profile_vmax'] <= 0 or p['rss'] <= 0 or p['likelihood_ratio'] < 0 for p in points):
            raise ValueError('Profile parameters and RSS must be positive; likelihood ratios nonnegative')
        if any(a['km'] >= b['km'] for a,b in zip(points,points[1:])):
            raise ValueError('Profile Km values must be unique and strictly increasing')
        obs = data[data.state == state]
        included = obs if scope == 'full_range' else obs[obs.conc <= .11]
        fit = summary['fits'][state][scope]
        # Re-evaluate the objective from archived observations; table hashes alone
        # cannot detect a coordinated change to the table and its manifest.
        rss_best = math.fsum((float(r.rate)-fit['vmax']*float(r.conc)/(fit['km']+float(r.conc)))**2 for r in included.itertuples())
        if not math.isclose(rss_best, fit['rss'], rel_tol=2e-8, abs_tol=1e-6):
            raise ValueError('Saved best-fit RSS disagrees with the source observations')
        if fit['n'] != len(included):
            raise ValueError('Saved observation count disagrees with the selected range')
        for p in points:
            g = [float(s)/(p['km']+float(s)) for s in included.conc]
            conditional_v = math.fsum(a*float(b) for a,b in zip(g,included.rate))/math.fsum(a*a for a in g)
            rss = math.fsum((float(y)-p['profile_vmax']*a)**2 for y,a in zip(included.rate,g))
            lr = max(0., len(included)*math.log(rss/rss_best))
            if not (math.isclose(conditional_v,p['profile_vmax'],rel_tol=2e-8,abs_tol=1e-7)
                    and math.isclose(rss,p['rss'],rel_tol=2e-8,abs_tol=1e-6)
                    and math.isclose(lr,p['likelihood_ratio'],rel_tol=2e-7,abs_tol=2e-7)):
                raise ValueError('Saved profile does not reproduce the conditional fit/objective')
        groups.append({'key': state + '/' + scope, 'state': state, 'scope': scope,
                       'label': state + (' — all concentrations' if scope == 'full_range' else ' — concentrations ≤ 0.11 ppm'),
                       'fit': fit, 'points': points,
                       'observations': [{'row_id': int(r.row_id), 'concentration': float(r.conc),
                                         'rate': float(r.rate), 'included': scope == 'full_range' or r.conc <= .11}
                                        for r in obs.itertuples()]})
    return groups


TEMPLATE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Enzyme kinetics · Profile explorer</title><style>
body{margin:0;background:#f3f6f8;color:#203449;font:16px/1.5 system-ui,sans-serif}main{max-width:1160px;margin:auto;padding:28px}
h1{font-size:32px;margin:0 0 10px}p{max-width:950px}.eyebrow{color:#007f7b;font-weight:650;letter-spacing:.05em;font-size:13px}
.controls{display:flex;flex-wrap:wrap;gap:18px;background:#fff;border:1px solid #dce4e9;border-radius:12px;padding:18px;align-items:center}
select,button{font:inherit;padding:7px}input{width:260px;vertical-align:middle}#selection{background:#e8f2f1;padding:12px 18px;border-radius:8px;font-variant-numeric:tabular-nums}
#curve,#profile{background:white;border-radius:12px;margin-top:16px;min-height:380px}details{background:#fff;padding:16px;margin-top:18px}a{color:#00716d}.note{font-size:14px;color:#596773}table{border-collapse:collapse}td,th{padding:6px 14px;border-bottom:1px solid #ddd;text-align:left}code{font-size:13px}
</style><script>__PLOTLY__</script></head><body><main>
<div class="eyebrow">ENZYME KINETICS WORKBENCH · ARCHIVED DATA</div><h1>Different parameters can draw similar curves</h1>
<p>Choose one archived label and concentration range. Move through the saved profile: each candidate half-saturation value (Km) has its maximum rate (Vmax) reoptimized. The candidate curve is a conditional fit, not another experiment.</p>
<div class="controls"><label>Saved fit <select id="group" aria-label="Saved fit"></select></label><label>Profile point <input id="point" type="range" min="0" aria-label="Profile point"></label><button id="reset">Return to best fit</button></div>
<p id="selection" aria-live="polite"></p><div id="curve" role="img" aria-label="Archived observations and selected candidate curve"></div>
<div id="profile" role="img" aria-label="Likelihood profile and maximum-rate tradeoff"></div>
<p class="note">Click a profile point or use the slider. Faded crosses mark observations excluded from a low-range fit. Dotted curve segments lie outside the fitted concentration range. The cutoff is an approximate asymptotic 95% profile criterion, not calibrated small-sample coverage or a confidence band for predicted rates.</p>
<details><summary>Values, assumptions and source record</summary><div id="values"></div>
<p>Rate units are counts/min/min: change in radioactive count rate per minute, not turnover per enzyme. Concentration is ppm, not molar binding affinity. Repeated rows do not establish independent biological replicates; the archived labels do not identify a causal treatment mechanism.</p>
<p>The profile assumes independent constant-variance Gaussian errors and the saturating mean curve. This viewer has no network calls. It uses saved numerical tables checked against the archived observations. Generated with Plotly __VERSION__; MIT-licensed Plotly.js is embedded with its license header.</p><pre id="sources"></pre></details>
</main><script>
const groups=__DATA__,sources=__SOURCES__;
const choice=document.getElementById('group'), slider=document.getElementById('point');
groups.forEach((g,i)=>choice.add(new Option(g.label,i)));
document.getElementById('sources').textContent=JSON.stringify(sources,null,2);
const cfg={responsive:true,displaylogo:false,toImageButtonOptions:{format:'svg',filename:'kinetics-profile-view'}};
const theme={paper_bgcolor:'#fff',plot_bgcolor:'#fff',font:{family:'Arial,sans-serif',color:'#203449'},margin:{l:80,r:30,t:55,b:65},hovermode:'closest'};
function current(){return groups[+choice.value];}
function selectBest(){const g=current();slider.max=g.points.length-1;slider.value=g.points.reduce((best,p,i)=>p.likelihood_ratio<g.points[best].likelihood_ratio?i:best,0);render();}
function render(){const g=current(),p=g.points[+slider.value],f=g.fit;
const obs=g.observations.filter(o=>o.included), excluded=g.observations.filter(o=>!o.included);
const low=f.concentration_min,high=f.concentration_max;
const x=Array.from({length:221},(_,i)=>1.1*i/220);
const predict=(v,k,s)=>v*s/(k+s);
const traces=[{x:obs.map(o=>o.concentration),y:obs.map(o=>o.rate),customdata:obs.map(o=>o.row_id),type:'scatter',mode:'markers',name:'Included observations',marker:{color:'#203449',size:9},hovertemplate:'Row %{customdata}<br>%{x:.3g} ppm<br>%{y:.4g} counts/min/min<extra></extra>'}];
if(excluded.length)traces.push({x:excluded.map(o=>o.concentration),y:excluded.map(o=>o.rate),type:'scatter',mode:'markers',name:'Excluded observations',marker:{color:'#8899a3',symbol:'x',size:9}});
for(const inside of [true,false]){const xx=x.filter(s=>(s>=low&&s<=high)===inside);if(!inside){
for(const bounds of [[0,low],[high,1.1]]){if(bounds[0]===bounds[1])continue;const xs=Array.from({length:65},(_,i)=>bounds[0]+(bounds[1]-bounds[0])*i/64);traces.push({x:xs,y:xs.map(s=>predict(p.profile_vmax,p.km,s)),type:'scatter',mode:'lines',name:'Outside fitted range',showlegend:bounds[0]===0,line:{color:'#c25e28',dash:'dot',width:2}});}}
else traces.push({x:xx,y:xx.map(s=>predict(p.profile_vmax,p.km,s)),type:'scatter',mode:'lines',name:'Selected profile curve',line:{color:'#c25e28',width:3}});}
traces.push({x:x.filter(s=>s>=low&&s<=high),y:x.filter(s=>s>=low&&s<=high).map(s=>predict(f.vmax,f.km,s)),type:'scatter',mode:'lines',name:'Best-fit curve',line:{color:'#007f7b',dash:'dash',width:2}});
Plotly.react('curve',traces,{...theme,xaxis:{title:{text:'Substrate concentration (ppm)'},range:[0,1.12]},yaxis:{title:{text:'Rate (counts/min/min)'},rangemode:'tozero'},legend:{orientation:'h',y:1.06},height:410},cfg);
const km=g.points.map(q=>q.km),lr=g.points.map(q=>q.likelihood_ratio),vv=g.points.map(q=>q.profile_vmax);
const dat=[{x:km,y:lr,type:'scatter',mode:'lines+markers',name:'Profile likelihood',marker:{size:4,color:'#007f7b'},line:{color:'#007f7b'},hovertemplate:'Km %{x:.5g} ppm<br>Likelihood ratio %{y:.5g}<extra></extra>'},{x:[p.km],y:[p.likelihood_ratio],type:'scatter',mode:'markers',showlegend:false,marker:{size:12,color:'#c25e28'}},{x:km,y:vv,xaxis:'x2',yaxis:'y2',type:'scatter',mode:'lines+markers',name:'Reoptimized Vmax',marker:{size:4,color:'#007f7b'},line:{color:'#007f7b'},hovertemplate:'Km %{x:.5g} ppm<br>Vmax %{y:.5g} counts/min/min<extra></extra>'},{x:[p.km],y:[p.profile_vmax],xaxis:'x2',yaxis:'y2',type:'scatter',mode:'markers',showlegend:false,marker:{size:12,color:'#c25e28'}}];
Plotly.react('profile',dat,{...theme,showlegend:false,height:390,title:{text:'How the candidate parameters trade off'},grid:{rows:1,columns:2,pattern:'independent'},xaxis:{type:'log',title:{text:'Candidate Km (ppm)'}},yaxis:{title:{text:'Likelihood-ratio statistic'},rangemode:'tozero'},xaxis2:{type:'log',title:{text:'Candidate Km (ppm)'}},yaxis2:{title:{text:'Vmax (counts/min/min)'},rangemode:'tozero'},shapes:[{type:'line',xref:'x domain',x0:0,x1:1,yref:'y',y0:f.km_profile.cutoff,y1:f.km_profile.cutoff,line:{color:'#9b4c39',dash:'dash'}}],annotations:[{xref:'x domain',x:0.02,yref:'y',y:f.km_profile.cutoff,text:'Approximate 95% cutoff',showarrow:false,yshift:13,font:{size:10,color:'#9b4c39'}}]},cfg);
document.getElementById('selection').textContent=`Km = ${p.km.toPrecision(5)} ppm · Vmax = ${p.profile_vmax.toPrecision(6)} counts/min/min · likelihood ratio = ${p.likelihood_ratio.toPrecision(4)} · ${p.likelihood_ratio<=f.km_profile.cutoff?'within':'outside'} the profile cutoff`;
document.getElementById('values').innerHTML=`<table><tr><th>Included rows</th><td>${f.n}</td></tr><tr><th>Fitted range (ppm)</th><td>${low}–${high}</td></tr><tr><th>Selected RSS</th><td>${p.rss.toPrecision(7)}</td></tr><tr><th>Best-fit Km (ppm)</th><td>${f.km.toPrecision(7)}</td></tr><tr><th>Best-fit Vmax</th><td>${f.vmax.toPrecision(7)}</td></tr></table>`;
}
choice.addEventListener('change',selectBest);slider.addEventListener('input',render);document.getElementById('reset').addEventListener('click',selectBest);
selectBest();document.getElementById('profile').on('plotly_click',event=>{const point=event.points[0];if(point.curveNumber===0||point.curveNumber===2){slider.value=point.pointIndex;render();}});
</script></body></html>'''


def build(results_dir, out):
    import plotly
    from plotly.offline import get_plotlyjs
    groups = load_profiles(results_dir)
    out = Path(out).resolve()
    if out == ROOT or out.is_relative_to(ROOT / 'data') or out.is_relative_to(Path(results_dir).resolve()):
        raise ValueError('Choose an output directory separate from source data and analysis results')
    out.mkdir(parents=True, exist_ok=True)
    sources = {p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else p.name: digest(p)
               for p in (ROOT/'data/puromycin.csv',Path(results_dir)/'summary.json',Path(results_dir)/'km_profiles.csv')}
    body = TEMPLATE.replace('__PLOTLY__',get_plotlyjs()).replace('__VERSION__',plotly.__version__)
    body = body.replace('__DATA__',json.dumps(groups,separators=(',',':')).replace('</','<\\/'))
    body = body.replace('__SOURCES__',json.dumps(sources,separators=(',',':')))
    (out/'profile-explorer.html').write_text(body,encoding='utf-8',newline='\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(10,4),constrained_layout=True)
    for g in groups:
        color='#007f7b' if g['state']=='treated' else '#b87824'
        style='-' if g['scope']=='full_range' else '--'
        axes[0].plot([p['km'] for p in g['points']],[p['likelihood_ratio'] for p in g['points']],color=color,ls=style,label=g['label'].replace(' — ',' / '))
        axes[1].plot([p['km'] for p in g['points']],[p['profile_vmax'] for p in g['points']],color=color,ls=style)
    axes[0].axhline(groups[0]['fit']['km_profile']['cutoff'],color='#586773',lw=.8,ls=':')
    axes[0].set(ylabel='Likelihood-ratio statistic',title='Conditional profile',ylim=(0,12))
    axes[1].set(ylabel='Reoptimized Vmax (counts/min/min)',title='Parameter tradeoff')
    for ax in axes:
        ax.set(xlabel='Candidate Km (ppm)',xscale='log')
        ax.spines[['top','right']].set_visible(False)
        ax.grid(alpha=.15)
    fig.legend(*axes[0].get_legend_handles_labels(),loc='outside lower center',ncol=2,fontsize=8,frameon=False)
    fig.savefig(out/'profile-preview.png',dpi=160)
    plt.close(fig)
    manifest={'schema_version':1,'input_sha256':sources,'builder_sha256':digest(__file__),
              'versions':{name:importlib.metadata.version(name) for name in ('plotly','numpy','matplotlib')},
              'profile_groups':len(groups),'profile_rows_checked':sum(len(g['points']) for g in groups),
              'checks':'All saved profile Vmax, RSS and likelihood ratios recomputed against archived observations before rendering.',
              'scope':'Visualization of saved conditional fits; no new fitting, biological inference, or interval calibration.',
              'output_sha256':{p.name:digest(p) for p in (out/'profile-explorer.html',out/'profile-preview.png')}}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results-dir',type=Path,default=ROOT/'results')
    parser.add_argument('--out',type=Path,default=ROOT/'examples/profile-explorer')
    args=parser.parse_args()
    try:
        print(json.dumps(build(args.results_dir.resolve(),args.out),indent=2))
    except (OSError,ValueError,KeyError) as exc:
        parser.exit(2,f'Profile explorer stopped: {exc}\n')

#!/usr/bin/env python3
"""Deterministic mathematical counterexamples; NOT the paper's analysis code.

Run: python diagnostics/diagnostic_examples.py
Only synthetic data and the Python standard library are used. No networking,
external commands, dependency installation, biological data, or random seed.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
import json
import math
import platform
import sys
import traceback
from typing import Sequence

@dataclass(frozen=True)
class Cell:
    sample: str
    id: str
    x: float
    y: float
    kind: str

def neighborhood(cells: Sequence[Cell], center: Cell, radius: float, *, include_self: bool) -> list[Cell]:
    """Toy contract: <= radius, same sample, explicit self policy, valid unique keys."""
    if not math.isfinite(radius) or radius <= 0:
        raise ValueError('radius must be finite and positive')
    keys = [(c.sample, c.id) for c in cells]
    if len(set(keys)) != len(keys):
        raise ValueError('duplicate (sample, cell_id)')
    if (center.sample, center.id) not in keys:
        raise ValueError('center not present')
    if any(not math.isfinite(v) for c in cells for v in (c.x, c.y)):
        raise ValueError('non-finite coordinate')
    return [c for c in cells if c.sample == center.sample
            and (include_self or c.id != center.id)
            and math.hypot(c.x-center.x,c.y-center.y) <= radius]

def composition(cells: Sequence[Cell]) -> dict[str, float] | None:
    """None is explicitly not an all-zero or fabricated pure-CAF composition."""
    if not cells:
        return None
    counts = Counter(c.kind for c in cells)
    return {k:v/len(cells) for k,v in sorted(counts.items())}

def nearest_k_mean(center: Cell, cells: Sequence[Cell], target: str, k: int) -> float:
    """Toy policy: insufficient target cells raise; paper's policy is unknown."""
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        raise ValueError('positive integer k required')
    d = sorted(math.hypot(c.x-center.x,c.y-center.y) for c in cells
               if c.sample == center.sample and c.kind == target and c.id != center.id)
    if len(d) < k:
        raise ValueError('insufficient target cells')
    return sum(d[:k])/k

def mm(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    if not a or not b or any(len(r)!=len(b) for r in a) or len({len(r) for r in b})!=1:
        raise ValueError('incompatible matrices')
    return [[sum(x*y for x,y in zip(r,c)) for c in zip(*b)] for r in a]

def pearson(x: Sequence[float], y: Sequence[float]) -> float:
    if len(x)!=len(y) or len(x)<2:
        raise ValueError('same nontrivial length required')
    mx,my=sum(x)/len(x),sum(y)/len(y)
    a,b=[v-mx for v in x],[v-my for v in y]
    den=math.sqrt(sum(v*v for v in a)*sum(v*v for v in b))
    if den==0:
        raise ValueError('constant vector')
    return sum(u*v for u,v in zip(a,b))/den

def logrank(times: Sequence[float], groups: Sequence[int], events: Sequence[int]) -> dict[str,float]:
    """Two-group log-rank with tied events and right censoring.

    Educational implementation. Not intended for clinical inference. All toy
    examples below have distinct times and observed events. Normal/chi-square
    asymptotic p value for one degree of freedom, using erfc.
    """
    if not (len(times)==len(groups)==len(events)) or len(times)<2:
        raise ValueError('invalid lengths')
    if any(not math.isfinite(t) or t<=0 for t in times):
        raise ValueError('invalid times')
    if set(groups)!={0,1} or not set(events).issubset({0,1}):
        raise ValueError('groups must include 0 and 1; binary events')
    oe,var=0.0,0.0
    event_times=sorted({t for t,e in zip(times,events) if e})
    for t in event_times:
        n1=sum(ti>=t and gi==1 for ti,gi in zip(times,groups))
        n0=sum(ti>=t and gi==0 for ti,gi in zip(times,groups))
        d1=sum(ti==t and gi==1 and ei==1 for ti,gi,ei in zip(times,groups,events))
        d0=sum(ti==t and gi==0 and ei==1 for ti,gi,ei in zip(times,groups,events))
        n,d=n0+n1,d0+d1
        if n==0:continue
        oe+=d1-d*n1/n
        if n>1:var+=d*n1*n0*(n-d)/(n*n*(n-1))
    if var<=0:raise ValueError('zero variance')
    chi2=oe*oe/var
    return {'chi2':chi2,'p':math.erfc(math.sqrt(chi2/2)),'observed_minus_expected':oe,'variance':var}

def require(condition: bool, message: str) -> None:
    if not condition:raise AssertionError(message)

def must_raise(fn, exc=ValueError) -> None:
    try:fn()
    except exc:return
    raise AssertionError('expected exception not raised')

def run_tests() -> tuple[list[dict],dict]:
    tests=[]; metrics={}
    def test(name,fn):
        try:
            fn();tests.append({'name':name,'passed':True})
        except Exception as e:
            tests.append({'name':name,'passed':False,'error':str(e),'traceback':traceback.format_exc()})
    c=Cell('s1','c',0,0,'CAF')
    t=Cell('s1','t',1,0,'T')
    cross=Cell('s2','t',0,0,'T')
    test('empty_neighborhood_is_unassigned',lambda:require(composition(neighborhood([c],c,80,include_self=False)) is None,'empty != missing'))
    test('self_inclusion_is_explicit_and_changes_composition',lambda:require(composition(neighborhood([c],c,80,include_self=True))=={'CAF':1.0},'self policy'))
    test('same_coordinates_other_sample_not_neighbor',lambda:require(neighborhood([c,cross],c,80,include_self=False)==[],'cross-sample leakage'))
    on=Cell('s1','on',3,4,'T');outside=Cell('s1','outside',3,4.001,'T')
    test('physical_radius_includes_boundary_only',lambda:require([x.id for x in neighborhood([c,on,outside],c,5,include_self=False)]==['on'],'radius boundary'))
    test('radius_does_not_force_fixed_neighbor_count',lambda:require(len(neighborhood([c,t],c,80,include_self=False))==1,'not fixed kNN'))
    test('duplicate_keys_rejected',lambda:must_raise(lambda:neighborhood([c,c],c,80,include_self=False)))
    test('nonfinite_coordinates_rejected',lambda:must_raise(lambda:neighborhood([c,Cell('s1','bad',float('nan'),0,'T')],c,80,include_self=False)))
    targets=[Cell('s1',str(i),float(d),0,'T') for i,d in enumerate([1,2,3,4,100])]
    test('nearest_five_are_averaged_not_minimized',lambda:require(nearest_k_mean(c,targets,'T',5)==22.0,'nearest-five mean'))
    test('insufficient_targets_fail_explicitly',lambda:must_raise(lambda:nearest_k_mean(c,[t],'T',5)))
    c2=Cell('s1','c2',2,0,'CAF')
    target_occurrences=[z for cc in [c,c2] for z in neighborhood([c,c2,t],cc,80,include_self=False) if z.kind=='T']
    metrics['overlapping_neighborhoods']={'target_occurrences':len(target_occurrences),'unique_targets':len({(z.sample,z.id) for z in target_occurrences})}
    test('overlap_duplicates_target_without_creating_new_cell',lambda:require(len(target_occurrences)==2 and len({z.id for z in target_occurrences})==1,'overlap example'))
    r=pearson([0.1,0.2,0.4,0.8],[0.9,0.8,0.6,0.2]);metrics['composition_only_correlation']=r
    test('closure_creates_negative_correlation_without_interaction',lambda:require(abs(r+1)<1e-12,'closure'))
    W=[[1.,2.],[3.,4.]];H=[[1.,0.],[0.,1.]]
    W2=[[row[0]/10,row[1]] for row in W];H2=[[10*x for x in H[0]],H[1]]
    old,new=mm(W,H),mm(W2,H2)
    d1=math.dist(W[0],W[1]);d2=math.dist(W2[0],W2[1])
    metrics['nmf_scaling']={'product_before':old,'product_after':new,'W_distance_before':d1,'W_distance_after':d2}
    test('nmf_product_is_scale_nonidentifiable',lambda:require(all(abs(a-b)<1e-12 for ra,rb in zip(old,new) for a,b in zip(ra,rb)),'product changed'))
    test('same_nmf_product_can_have_different_factor_distances',lambda:require(abs(d1-d2)>0.1,'distance unchanged'))
    metrics['background_normalization']={'same_local_fraction':0.2,'background_A':0.02,'background_B':0.2,'enrichment_A':10.,'enrichment_B':1.}
    test('equal_local_fraction_different_relative_enrichment',lambda:require(abs(.2/.02-10)<1e-12 and .2/.2==1,'enrichment'))
    times=list(range(1,61));events=[1]*60
    leaked=logrank(times,[int(t>30) for t in times],events)
    independent_rule=logrank(times,[i%2 for i in range(60)],events)
    metrics['survival_toy']={'n':60,'all_events_observed':True,'outcome_defined_group':leaked,'alternating_group':independent_rule,'not_paper_data':True}
    test('outcome_defined_groups_artificially_separate_survival',lambda:require(leaked['p']<1e-6,'expected artificial separation'))
    test('comparison_rule_not_defined_by_survival_order_halves',lambda:require(independent_rule['p']>0.05,'toy comparison failed'))
    test('logrank_is_group_label_symmetric',lambda:require(abs(leaked['p']-logrank(times,[int(t<=30) for t in times],events)['p'])<1e-12,'asymmetry'))
    test('logrank_invalid_event_labels_rejected',lambda:must_raise(lambda:logrank(times,[i%2 for i in range(60)],[2]*60)))
    return tests,metrics

if __name__=='__main__':
    tests,metrics=run_tests()
    result={'scope':'synthetic mathematical diagnostics only; NOT paper reproduction',
            'python':platform.python_version(),'randomness':'none','third_party_dependencies':[],
            'n_tests':len(tests),'n_passed':sum(t['passed'] for t in tests),
            'tests':tests,'metrics':metrics}
    print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))
    sys.exit(0 if all(t['passed'] for t in tests) else 1)

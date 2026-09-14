#!/usr/bin/env python3
"""Original, deterministic teaching examples; NOT PATH/GoT/TreeAlign code.
Calculations only use synthetic values. No patient data and no biological claims.
"""
from __future__ import annotations
import itertools
import json
import math
from typing import Sequence

def finite(v:float)->bool:
    return not isinstance(v,bool) and isinstance(v,(int,float)) and math.isfinite(v)

def miss_probability(m:int,p:float)->float:
    if type(m) is not int or m<0 or not finite(p) or not 0<=p<=1:
        raise ValueError('m must be a nonnegative integer and p a finite probability')
    return (1-p)**m

def transition_two_state(a:float,b:float,t:float)->list[list[float]]:
    if not all(finite(x) and x>=0 for x in (a,b,t)) or a+b<=0:
        raise ValueError('nonnegative finite rates/time required; total rate must be positive')
    s=a+b;e=math.exp(-s*t)
    return [[b/s+a/s*e,a/s*(1-e)],[b/s*(1-e),a/s+b/s*e]]

def stationary_two_state(a:float,b:float)->list[float]:
    transition_two_state(a,b,0)
    return [b/(a+b),a/(a+b)]

def moran_i(values:Sequence[float],weights:Sequence[Sequence[float]])->float:
    n=len(values)
    if n<2 or len(weights)!=n or any(len(row)!=n for row in weights):
        raise ValueError('requires n>=2 and n-by-n weights')
    if not all(finite(v) for v in values) or not all(finite(w) and w>=0 for row in weights for w in row):
        raise ValueError('requires finite values and nonnegative weights')
    if any(weights[i][i]!=0 for i in range(n)):
        raise ValueError('self-weights must be zero')
    centered=[x-sum(values)/n for x in values]
    denom=sum(x*x for x in centered);wsum=sum(map(sum,weights))
    if denom==0 or wsum<=0:
        raise ValueError('undefined for constant traits or zero total weight')
    return n/wsum*sum(weights[i][j]*centered[i]*centered[j] for i in range(n) for j in range(n))/denom

def expected_vaf(f:float,c:float,m:float)->float:
    if not all(finite(x) for x in (f,c,m)) or not 0<=f<=1 or not 0<=m<=c:
        raise ValueError('invalid mixture or copy counts')
    denom=f*c+2*(1-f)
    if denom<=0:raise ValueError('undefined allele fraction')
    return f*m/denom

def run_demo()->dict:
    x=[0,0,0,0,1,1,1,1]
    w=[[int(i!=j and (i<4)==(j<4)) for j in range(8)] for i in range(8)]
    observed=moran_i(x,w)
    null=[]
    for inds in itertools.combinations(range(8),4):
        chosen=set(inds);null.append(moran_i([int(i in chosen) for i in range(8)],w))
    normal_one_tail=.5*math.erfc(2/math.sqrt(2))
    return {
        'status':'executed_synthetic_teaching_only',
        'author_software_executed':False,'real_biological_data_used':False,
        'dropout':{'assumption':'m independent informative molecules; alternate probability p=0.5',
                   'values':[{'m':m,'p_no_alternate_given_mutant':miss_probability(m,.5)} for m in [0,1,4,10]]},
        'same_proportions_different_rates':[{'a':a,'b':a,'stationary':stationary_two_state(a,a),
                        'mean_dwell_time':1/a,'P_at_t_1':transition_two_state(a,a,1)} for a in [.05,5]],
        'moran':{'weights':'same synthetic 4-leaf group, zero diagonal',
                 'grouped_labels_I':observed,'interleaved_labels_I':moran_i([0,1,0,1,0,1,0,1],w),
                 'exact_permutations':len(null),'null_mean':sum(null)/len(null),
                 'expected_null_mean':-1/7,'exact_upper_tail_p':sum(v>=observed-1e-12 for v in null)/len(null),
                 'warning':'exact synthetic label permutation only; not an author PATH significance test'},
        'composition_confounding':{'low_background_mean':1,'high_background_mean':10,
                 'WT_low_high_counts':[90,10],'mutant_low_high_counts':[10,90],
                 'WT_overall_mean':(90*1+10*10)/100,'mutant_overall_mean':(10*1+90*10)/100,
                 'within_background_difference':0},
        'normal_tail_at_Z_2':{'one_sided_upper':normal_one_tail,'two_sided':2*normal_one_tail,
                 'note':'arithmetic illustration of the audited xcor return-field naming issue; R not executed'},
        'vaf_assumptions':{'diploid_normal_background':True,'equal_per_copy_contribution':True},
        'vaf_examples':[{'true_tumor_fraction':.4,'tumor_total_copy':c,'mutant_copy':1,
                  'expected_vaf':expected_vaf(.4,c,1),'twice_vaf':2*expected_vaf(.4,c,1)} for c in [2,4]]}
if __name__=='__main__':
    print(json.dumps(run_demo(),ensure_ascii=False,indent=2,allow_nan=False))

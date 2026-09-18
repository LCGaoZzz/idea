#!/usr/bin/env python3
"""Arithmetic on manually transcribed counts; not original-data reproduction.
No model or biological dataset is fitted. Uses only the Python standard library.
Clopper-Pearson bounds invert exact binomial probabilities by bisection.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,sys
from pathlib import Path

def binomial_cdf(k:int,n:int,p:float)->float:
    return sum(math.comb(n,j)*p**j*(1-p)**(n-j) for j in range(k+1))

def clopper_pearson(k:int,n:int,alpha:float=.05)->tuple[float,float]:
    if not (0<=k<=n and n>0 and 0<alpha<1): raise ValueError('Invalid binomial arguments')
    if k==0: lower=0.0
    else:
        lo,hi=0.0,1.0
        for _ in range(90):
            mid=(lo+hi)/2
            # Survival probability increases with p.
            if 1-binomial_cdf(k-1,n,mid)<alpha/2: lo=mid
            else: hi=mid
        lower=(lo+hi)/2
    if k==n: upper=1.0
    else:
        lo,hi=0.0,1.0
        for _ in range(90):
            mid=(lo+hi)/2
            if binomial_cdf(k,n,mid)>alpha/2: lo=mid
            else: hi=mid
        upper=(lo+hi)/2
    return lower,upper

def max_exceedance(n:int,per_cell_p:float)->float:
    if n<1 or not 0<=per_cell_p<=1: raise ValueError('Invalid max example arguments')
    return 1-(1-per_cell_p)**n

def main()->None:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--input',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    with a.input.open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f,delimiter='\t'))
    if len(rows)!=22 or len({r['sample_id'] for r in rows})!=22: raise ValueError('Expected 22 unique S4 rows')
    cells=[int(r['total_gd_cells']) for r in rows];seqs=[int(r['unique_paired_sequences']) for r in rows]
    if any(x<0 for x in cells+seqs):raise ValueError('Counts must be nonnegative')
    mm15=next(int(r['total_gd_cells']) for r in rows if r['sample_id']=='MM15')
    result={'identity':'independent arithmetic; not author pipeline execution',
      'python':sys.version,'input_sha256':hashlib.sha256(a.input.read_bytes()).hexdigest(),
      'S4':{'rows':len(rows),'total_gd_cells':sum(cells),'sum_unique_paired_sequences':sum(seqs),
            'MM15_cells':mm15,'MM15_fraction':mm15/sum(cells),'first_eight_paired_sequences_sum':sum(seqs[:8]),
            'limits':'S4 manual parsed-text transcription; sequence counts not assumed identical to main-text clonotype definition.'},
      'ideal_independent_binomial_95_intervals':[{'successes':k,'n':n,'fraction':k/n,'lower':clopper_pearson(k,n)[0],'upper':clopper_pearson(k,n)[1]} for k,n in [(21,25),(15,15),(10,10)]],
      'binomial_limit':'Illustrative independent-trial intervals; NOT donor-clustered or selection-adjusted study confidence intervals.',
      'hypothetical_max_bias':{'per_cell_false_exceedance_assumption':.01,'independent_cells_assumption':True,
       'values':[{'clone_size':n,'probability':max_exceedance(n,.01)} for n in [1,10,30,100]],
       'limits':'Mathematical example; not empirical FPR for PreGame; actual clone cells are correlated.'}}
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

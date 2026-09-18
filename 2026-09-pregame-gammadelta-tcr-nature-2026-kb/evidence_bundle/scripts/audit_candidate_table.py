#!/usr/bin/env python3
"""Independent audit helper, NOT the authors' PreGame implementation.

Input TSV: one row per cell prediction for ONE registered CV split.
Required fields: cell_id, donor_id, batch_id, clone_id, delta_key, label,
                 split, score
label: TR/NTR/borderline/unknown/expression_failure
split: train/test/unused
clone_id must be a biological paired-receptor key, not a per-library integer.
The function does not infer missing labels or rewrite the input.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

REQUIRED = ('cell_id','donor_id','batch_id','clone_id','delta_key','label','split','score')
LABELS = {'TR','NTR','borderline','unknown','expression_failure'}
SPLITS = {'train','test','unused'}

def audit_rows(rows: list[dict[str,str]], *, require_batch_disjoint: bool = True) -> dict[str,Any]:
    errors: list[dict[str,Any]] = []
    warnings: list[dict[str,Any]] = []
    seen: set[str] = set()
    groups: dict[str, dict[str,set[str]]] = {x:defaultdict(set) for x in ('donor_id','batch_id','clone_id')}
    labels: dict[str,set[str]] = defaultdict(set)
    delta_to_clones: dict[tuple[str,str],set[str]] = defaultdict(set)
    for index,row in enumerate(rows,2):
        missing = [key for key in REQUIRED if key not in row or not str(row[key]).strip()]
        if missing:
            errors.append({'code':'missing_fields','row':index,'fields':missing}); continue
        r = {key:str(row[key]).strip() for key in REQUIRED}
        if r['cell_id'] in seen: errors.append({'code':'duplicate_cell_id','row':index,'cell_id':r['cell_id']})
        seen.add(r['cell_id'])
        if r['label'] not in LABELS: errors.append({'code':'invalid_label','row':index,'label':r['label']})
        if r['split'] not in SPLITS: errors.append({'code':'invalid_split','row':index,'split':r['split']})
        try:
            score = float(r['score'])
            if not math.isfinite(score) or not 0 <= score <= 1: raise ValueError('not finite unit-interval')
        except (ValueError,TypeError): errors.append({'code':'invalid_score','row':index,'value':r['score']})
        if r['split'] in {'train','test'}:
            for key in groups: groups[key][r[key]].add(r['split'])
            if r['label'] not in {'TR','NTR'}:
                errors.append({'code':'nonbinary_label_in_supervised_split','row':index,'label':r['label']})
        if r['label'] in {'TR','NTR'}: labels[r['clone_id']].add(r['label'])
        delta_to_clones[(r['donor_id'],r['delta_key'])].add(r['clone_id'])
    for key,values in groups.items():
        if key == 'batch_id' and not require_batch_disjoint: continue
        for value,parts in sorted(values.items()):
            if parts == {'train','test'}: errors.append({'code':'split_overlap','group_type':key,'group':value})
    for clone,cl in sorted(labels.items()):
        if len(cl)>1: errors.append({'code':'inconsistent_clone_label','clone_id':clone,'labels':sorted(cl)})
    for (donor,delta),cl in sorted(delta_to_clones.items()):
        if len(cl)>1: warnings.append({'code':'delta_one_to_many','donor_id':donor,'delta_key':delta,'clone_ids':sorted(cl)})
    if not rows: errors.append({'code':'empty_input'})
    return {'tool_identity':'independent_pregame_evidence_auditor_not_author_code',
            'rows':len(rows),'passed':not errors,'errors':errors,'warnings':warnings,
            'limits':['Checks supplied keys, not receptor reconstruction or biological truth.',
                      'One split per file; unknown labels never converted to negatives.',
                      'Batch-disjoint check is conservative for the reported multiplexed design.']}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--allow-shared-batch',action='store_true',help='Explicitly relax batch holdout, not donor/clone holdout.')
    args=parser.parse_args()
    try:
        raw=args.input.read_bytes()
        with args.input.open(encoding='utf-8-sig',newline='') as handle:
            reader=csv.DictReader(handle,delimiter='\t')
            missing=set(REQUIRED)-set(reader.fieldnames or [])
            if missing: raise ValueError('Missing header fields: '+', '.join(sorted(missing)))
            rows=list(reader)
        result=audit_rows(rows,require_batch_disjoint=not args.allow_shared_batch)
        result['input_sha256']=hashlib.sha256(raw).hexdigest()
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'passed':result['passed'],'rows':len(rows),'errors':len(result['errors']),'warnings':len(result['warnings'])}))
        return 0 if result['passed'] else 2
    except (OSError,ValueError,csv.Error) as exc:
        parser.exit(1,f'Input/output error: {exc}\n')
if __name__=='__main__': raise SystemExit(main())

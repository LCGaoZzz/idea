#!/usr/bin/env python3
"""Restore assistant-curated fact notes after policy-filtered packaging.
Does not download or recreate any original paper, supplement, code or data.
"""
from pathlib import Path
import hashlib,json,shutil,sys

def main() -> int:
    root=Path(__file__).resolve().parents[1]
    manifest=json.loads((root/'reconstruction_manifest.json').read_text(encoding='utf-8'))
    count=0
    for source in manifest['sources']:
        if source['availability'] != 'available':
            continue
        rel=Path(source['location'])
        if rel.parent.as_posix() != 'sources/curated' or rel.name not in {'parameter_facts.tsv','caption_fact_extract.json','critical_verbatim_fragments.txt','candidate_repository.json'}:
            raise ValueError(f'Unapproved capture path: {rel}')
        src=root/'evidence'/rel.name
        expected=source['fingerprint']
        actual='sha256:'+hashlib.sha256(src.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f'Capture hash mismatch: {src.name}')
        dst=root/rel
        if dst.exists() and 'sha256:'+hashlib.sha256(dst.read_bytes()).hexdigest()!=expected:
            raise ValueError(f'Refusing to overwrite changed evidence: {rel}')
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(src,dst)
        count+=1
    print(json.dumps({'restored_curated_captures':count,'original_paper_files_restored':0,'original_biological_data_restored':0}))
    return 0
if __name__=='__main__':
    try:
        raise SystemExit(main())
    except (OSError,ValueError,KeyError) as exc:
        print(str(exc),file=sys.stderr)
        raise SystemExit(1)

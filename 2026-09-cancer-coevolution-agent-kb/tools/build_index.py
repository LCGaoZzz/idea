#!/usr/bin/env python3
"""Build Markdown section corpus; optionally refresh checksums after review."""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def build():
    rows=[]
    for base in ['knowledge','methods']:
        for path in sorted((ROOT/base).glob('*.md')):
            lines=path.read_text(encoding='utf-8').splitlines()
            title=next((l.lstrip('# ').strip() for l in lines if l.startswith('# ')),path.stem)
            cuts=[0]+[i for i,l in enumerate(lines) if i and l.startswith('## ')]+[len(lines)]
            for a,b in zip(cuts,cuts[1:]):
                text='\n'.join(lines[a:b]).strip()
                if not text:continue
                heading=lines[a].lstrip('# ').strip() if lines[a].startswith('#') else title
                rel=path.relative_to(ROOT).as_posix()
                id='D'+hashlib.sha256((rel+'#'+str(a)).encode()).hexdigest()[:12]
                rows.append({'chunk_id':id,'document_path':rel,'title':title+' / '+heading,
                    'start_line':a+1,'end_line':b,'text':text,'source_ids':sorted(set(re.findall(r'\[(S\d{2})\]',text))),
                    'scope':'KB-authored section; local line numbers are not original-paper line numbers'})
    (ROOT/'evidence/corpus.jsonl').write_text('\n'.join(json.dumps(r,ensure_ascii=False) for r in rows)+'\n',encoding='utf-8')
    return len(rows)

def checksums():
    paths=[p for p in sorted(ROOT.rglob('*')) if p.is_file() and '__pycache__' not in p.parts
           and p.suffix not in {'.pyc'} and p.relative_to(ROOT).as_posix()!='audit/SHA256SUMS']
    (ROOT/'audit/SHA256SUMS').write_text('\n'.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(ROOT).as_posix() for p in paths)+'\n',encoding='utf-8')
    return len(paths)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--checksums',action='store_true');args=parser.parse_args()
    result={'chunks':build()}
    if args.checksums:result['checksum_files']=checksums()
    print(json.dumps(result,ensure_ascii=False))

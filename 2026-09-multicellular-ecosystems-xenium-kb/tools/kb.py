#!/usr/bin/env python3
"""Read-only lexical lookup for this KB; no models or scientific analysis."""
from __future__ import annotations
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote
ROOT = Path(__file__).resolve().parents[1]


def load() -> tuple[list[dict], list[dict]]:
    sources = json.loads((ROOT / 'evidence/sources.json').read_text(encoding='utf-8'))
    claims = [json.loads(line) for line in (ROOT / 'evidence/claims.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    return claims, sources


def terms(text: str) -> set[str]:
    out: set[str] = set()
    for part in re.findall(r'[a-z0-9_+.-]+|[\u4e00-\u9fff]+', text.lower()):
        out.add(part)
        if re.fullmatch(r'[\u4e00-\u9fff]+', part):
            out.update(part[i:i+2] for i in range(len(part)-1))
    return out


def search(query: str, limit: int = 5) -> list[dict]:
    if not query.strip() or not 1 <= limit <= 200:
        raise ValueError('query must be nonempty and limit must be between 1 and 200')
    q = terms(query)
    claims, sources = load()
    by_id = {s['id']: s for s in sources}
    ranked = []
    for c in claims:
        score = 3*len(q & terms(' '.join(c['tags']))) + 2*len(q & terms(c['claim'])) + len(q & terms(c['boundary']))
        if score:
            ranked.append({**c, 'score': score, 'source_details': [by_id[s] for s in c['sources']]})
    return sorted(ranked, key=lambda c: (-c['score'], c['id']))[:limit]


def show(claim_id: str) -> dict:
    claims, sources = load()
    c = next((c for c in claims if c['id'] == claim_id), None)
    if c is None:
        raise KeyError(f'unknown claim: {claim_id}')
    lookup = {s['id']: s for s in sources}
    return {**c, 'source_details': [lookup[s] for s in c['sources']]}


def validate() -> dict:
    claims, sources = load()
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    errors = []
    for kind, rows in [('claim', claims), ('source', sources)]:
        ids = [r['id'] for r in rows]
        if len(ids) != len(set(ids)):
            errors.append(f'duplicate {kind} IDs')
    source_ids = {s['id'] for s in sources}
    for c in claims:
        if c['label'] not in manifest['evidence_labels']:
            errors.append(f"invalid label: {c['id']}")
        if not (ROOT / c['path']).is_file():
            errors.append(f"missing claim path: {c['path']}")
        if not set(c['sources']) <= source_ids:
            errors.append(f"missing source: {c['id']}")
        if c['label'] in {'ARTICLE_FACT', 'EXTERNAL_FACT', 'DOC_FACT'} and not c['sources']:
            errors.append(f"unsourced fact: {c['id']}")
    checked_links = 0
    skipped = set()
    for doc in ROOT.rglob('*.md'):
        for url in re.findall(r'\[[^\]]*\]\(([^)]+)\)', doc.read_text(encoding='utf-8')):
            if url.startswith(('http:', 'https:', 'mailto:', '#')):
                continue
            path = (doc.parent / unquote(url.split('#')[0])).resolve()
            if not path.is_relative_to(ROOT):
                skipped.add(url)
                continue
            checked_links += 1
            if not path.exists():
                errors.append(f'broken link: {doc.relative_to(ROOT)} -> {url}')
    for name in manifest['figures']:
        path = ROOT / name
        try:
            root = ET.parse(path).getroot()
            if root.tag != '{http://www.w3.org/2000/svg}svg':
                errors.append(f'not SVG: {name}')
            if any(e.tag.rsplit('}', 1)[-1] in {'script', 'foreignObject', 'image'} for e in root.iter()):
                errors.append(f'non-self-contained SVG: {name}')
        except (OSError, ET.ParseError) as exc:
            errors.append(f'{name}: {exc}')
    return {'ok': not errors, 'claim_count': len(claims), 'source_count': len(sources), 'figure_count': len(manifest['figures']), 'internal_links_checked': checked_links, 'external_repository_links_not_checked_locally': sorted(skipped), 'errors': errors, 'scope': 'structural checks only; no scientific replication or HTTP link checking'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('search'); p.add_argument('query'); p.add_argument('--limit', type=int, default=5)
    p = sub.add_parser('show'); p.add_argument('claim_id')
    sub.add_parser('validate')
    args = parser.parse_args()
    try:
        if args.command == 'search':
            result = search(args.query, args.limit)
        elif args.command == 'show':
            result = show(args.claim_id)
        else:
            result = validate()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if isinstance(result, dict) and result.get('ok') is False else 0
    except (ValueError, KeyError, OSError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

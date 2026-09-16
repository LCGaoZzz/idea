#!/usr/bin/env python3
"""Check delivery artifacts, source fingerprints and internal reader navigation.

Artifact checks only; this never certifies the original paper's results.
Requires beautifulsoup4 for HTML inspection; scientific toy tests are separate.
"""
from pathlib import Path
import argparse, ast, hashlib, json, re
from datetime import datetime, timezone
from bs4 import BeautifulSoup


def run(project: Path) -> dict:
    checks=[]
    def add(name, passed, detail):
        checks.append({'name':name,'passed':bool(passed),'detail':detail})
    deep=json.loads((project/'audit/deep_audit_results.json').read_text())
    old=json.loads((project/'audit/inherited_checks_rerun.json').read_text())
    add('bounded_test_receipts',deep['n_checks']==22 and old['n_checks']==10 and deep['all_detection_checks_passed'] and old['all_detection_checks_passed'], {'new':deep['n_checks'],'inherited_rerun':old['n_checks']})
    soup=BeautifulSoup((project/'KPSpatial_深度解析.html').read_text(),'html.parser')
    ids=[x['id'] for x in soup.select('[id]')]
    broken=[a['href'] for a in soup.select('a[href^="#"]') if a['href'][1:] not in set(ids)]
    add('unique_html_ids',len(ids)==len(set(ids)),len(ids))
    add('html_navigation',not broken,broken)
    add('four_embedded_diagrams',len(soup.find_all('svg'))==4,len(soup.find_all('svg')))
    add('twelve_chapters',all(f'chapter-{n}' in ids for n in range(1,13)),12)
    add('offline_no_external_assets',not soup.select('script[src],link[rel="stylesheet"],img[src]'),len(soup.select('script[src],link[rel="stylesheet"],img[src]')))
    add('offline_math_rendered',len(soup.select('.equation'))==2 and '\\[' not in soup.get_text(),len(soup.select('.equation')))
    missing=[]
    for path in [project/'README.md',*sorted((project/'docs').glob('*.md'))]:
        for target in re.findall(r'\]\(([^)]+)\)',path.read_text()):
            if not re.match(r'^[a-z]+:|^#',target) and not (path.parent/target.split('#')[0]).exists():
                missing.append([str(path.relative_to(project)),target])
    add('markdown_local_links',not missing,missing)
    catalog=json.loads((project/'sources_catalog.json').read_text())['sources']
    missing_sources=[];mismatched=[]
    for s in catalog:
        local=s.get('local_path')
        if not local:continue
        path=project/local
        if not path.is_file():missing_sources.append(local);continue
        expected=s.get('local_sha256') or s.get('sha256')
        if expected and hashlib.sha256(path.read_bytes()).hexdigest()!=expected:mismatched.append(local)
    add('source_local_paths',not missing_sources,missing_sources)
    add('source_catalog_hashes',not mismatched,mismatched)
    parsed=[]
    for path in sorted((project/'tools').glob('*.py')):
        ast.parse(path.read_text());parsed.append(str(path.relative_to(project)))
    add('audit_python_syntax',True,parsed)
    browser=json.loads((project/'audit/reader_browser_check.json').read_text())
    add('browser_render_check',all(browser['checks'].values()),browser)
    scope=json.loads((project/'audit/delivery_scope.json').read_text())
    add('no_false_scientific_execution',not scope['original_pipeline_executed'] and scope['scientific_execution_records']==0 and not deep['paper_results_reproduced'],scope['scientific_analysis_status_counts'])
    return {'created_at_utc':datetime.now(timezone.utc).isoformat(),'scope':'delivery_quality_only_not_scientific_reproduction','all_passed':all(c['passed'] for c in checks),'n_checks':len(checks),'checks':checks}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--project-dir',type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument('--output',type=Path)
    a=ap.parse_args();r=run(a.project_dir.resolve());out=a.output or a.project_dir/'audit/delivery_checks.json'
    out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'all_passed':r['all_passed'],'n_checks':r['n_checks']},ensure_ascii=False))
    for c in r['checks']:
        if not c['passed']: print(c)
    return 0 if r['all_passed'] else 1
if __name__=='__main__':raise SystemExit(main())

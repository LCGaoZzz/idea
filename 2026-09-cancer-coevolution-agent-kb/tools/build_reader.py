#!/usr/bin/env python3
"""Optional HTML publisher. Requires markdown-it-py; core CLI does not.
The generated reader is fully offline and has no runtime dependencies.
"""
from pathlib import Path
import json,re
from markdown_it import MarkdownIt
ROOT=Path(__file__).resolve().parents[1]
MD=MarkdownIt('commonmark',{'html':False,'linkify':False}).enable('table')

def rendered(text):
    return re.sub(r'\[(S\d{2})\]',r'<a href="#source-\1" data-source="\1" class="source-ref">[\1]</a>',MD.render(text))

def build():
    docs=[]
    paths=[ROOT/'README.md']+sorted((ROOT/'knowledge').glob('*.md'))+sorted((ROOT/'methods').glob('*.md'))+[ROOT/'AGENTS.md',ROOT/'SKILL.md',ROOT/'agent/INTEGRATION.md',ROOT/'agent/prompt_templates.md',ROOT/'RIGHTS.md']
    for p in paths:
        text=p.read_text(encoding='utf-8');rel=p.relative_to(ROOT).as_posix()
        title=next((x.lstrip('# ').strip() for x in text.splitlines() if x.startswith('# ')),p.stem)
        group='学习章节' if rel.startswith('knowledge/') else '方法卡片' if rel.startswith('methods/') else '使用与接入'
        docs.append({'path':rel,'title':title,'group':group,'text':text,'html':rendered(text)})
    data={'version':'0.9.0','date':'2026-09-13','documents':docs,
          'sources':json.loads((ROOT/'evidence/sources.json').read_text()),
          'claims':[json.loads(l) for l in (ROOT/'evidence/claims.jsonl').read_text().splitlines() if l.strip()],
          'gaps':json.loads((ROOT/'evidence/gaps.json').read_text())}
    template=(ROOT/'tools/reader_template.html').read_text(encoding='utf-8')
    payload=json.dumps(data,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    html=template.replace('__KB_PAYLOAD__',payload)
    (ROOT/'START_HERE.html').write_text(html,encoding='utf-8')
    print(json.dumps({'reader':'START_HERE.html','documents':len(docs),'bytes':len(html.encode())},ensure_ascii=False))
if __name__=='__main__':build()

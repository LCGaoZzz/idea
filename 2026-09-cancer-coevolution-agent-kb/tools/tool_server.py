#!/usr/bin/env python3
"""Custom JSONL stdio adapter. NOT MCP/JSON-RPC. No networking or execution."""
from __future__ import annotations
import json
import sys
from kb_core import KnowledgeBase, check_project, load_json, ROOT

def dispatch(kb,request):
    if not isinstance(request,dict):raise ValueError('request must be an object')
    name=request.get('tool');args=request.get('arguments',{})
    if not isinstance(args,dict):raise ValueError('arguments must be an object')
    actions={'search':kb.search,'read_claim':kb.read_claim,'read_document':kb.read_document,
             'build_context':kb.build_context,'check_project':check_project,
             'list_tools':lambda:load_json(ROOT/'agent/tools.json')}
    if name not in actions:raise ValueError('unsupported tool')
    return actions[name](**args)

def main():
    kb=KnowledgeBase()
    for line in sys.stdin:
        request=None
        try:
            if len(line)>1_000_000:raise ValueError('request exceeds maximum size')
            request=json.loads(line)
            out={'id':request.get('id') if isinstance(request,dict) else None,
                 'ok':True,'result':dispatch(kb,request)}
        except (ValueError,TypeError,KeyError,OSError) as exc:
            out={'id':request.get('id') if isinstance(request,dict) else None,
                 'ok':False,'error':{'type':type(exc).__name__,'message':str(exc)}}
        print(json.dumps(out,ensure_ascii=False,allow_nan=False),flush=True)
    return 0
if __name__=='__main__':sys.exit(main())

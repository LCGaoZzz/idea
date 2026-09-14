#!/usr/bin/env python3
"""Offline command-line entry point. See AGENTS.md for evidence rules."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from kb_core import KnowledgeBase, check_project

def emit(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False))

def main(argv=None):
    p=argparse.ArgumentParser(description='离线证据检索与项目能力检查（不是 LLM 聊天模型）')
    sub=p.add_subparsers(dest='command',required=True)
    s=sub.add_parser('search');s.add_argument('query');s.add_argument('--limit',type=int,default=5);s.add_argument('--json',action='store_true')
    s=sub.add_parser('context');s.add_argument('question');s.add_argument('--limit',type=int,default=5)
    s=sub.add_parser('get');s.add_argument('claim_id')
    s=sub.add_parser('read');s.add_argument('path')
    s=sub.add_parser('plan');s.add_argument('--input',type=Path,required=True)
    sub.add_parser('interactive')
    s=sub.add_parser('validate');s.add_argument('--skip-checksums',action='store_true')
    args=p.parse_args(argv)
    try:
        if args.command=='plan':
            emit(check_project(json.loads(args.input.read_text(encoding='utf-8'))));return 0
        kb=KnowledgeBase()
        if args.command=='search':
            hits=kb.search(args.query,args.limit)
            if args.json:emit(hits)
            else:
                if not hits:print('本库没有检得匹配证据；不代表该事实不存在。')
                for h in hits:
                    print(f'[{h["id"]}] {h["layer"]} | {h["document_path"]} | BM25={h["score"]:.3f}')
                    print(h['text']);print()
        elif args.command=='context':emit(kb.build_context(args.question,args.limit))
        elif args.command=='get':emit(kb.read_claim(args.claim_id))
        elif args.command=='read':emit(kb.read_document(args.path))
        elif args.command=='validate':
            result=kb.validate(not args.skip_checksums);emit(result);return 0 if result['ok'] else 1
        elif args.command=='interactive':
            print('本地证据检索会话；不是 LLM。输入问题检索，:get C032 展开论断，exit 或 退出 结束。')
            while True:
                try:q=input('检索> ').strip()
                except EOFError:break
                if q.lower() in {'exit','quit','退出'}:break
                if not q:continue
                try:
                    if q.startswith(':get '):emit(kb.read_claim(q[5:].strip()))
                    else:emit(kb.build_context(q,5))
                except ValueError as exc:emit({'ok':False,'error':str(exc)})
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        emit({'ok':False,'error':str(exc)});return 2

if __name__=='__main__':
    sys.exit(main())

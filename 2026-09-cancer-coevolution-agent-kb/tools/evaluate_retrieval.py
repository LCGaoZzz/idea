#!/usr/bin/env python3
"""Curated retrieval smoke evaluation only, not independent or LLM QA validation."""
import json
from kb_core import KnowledgeBase,load_jsonl,ROOT

def run():
    kb=KnowledgeBase();cases=load_jsonl(ROOT/'tests/evaluation_questions.jsonl');rows=[]
    for case in cases:
        hits=kb.search(case['question'],10);ids=[h['id'] for h in hits]
        ranks=[ids.index(c)+1 for c in case['expected_claim_ids'] if c in ids]
        rows.append({'question_id':case['id'],'question':case['question'],
                     'expected_claim_ids':case['expected_claim_ids'],'top10_ids':ids,
                     'first_expected_rank':min(ranks) if ranks else None,
                     'any_expected_at_5':any(r<=5 for r in ranks),
                     'any_expected_at_10':bool(ranks)})
    return {'evaluation_type':'author_curated_lexical_retrieval_smoke_test',
            'independent_benchmark':False,'llm_answer_quality_evaluated':False,
            'case_count':len(rows),'hit_at_5':sum(r['any_expected_at_5'] for r in rows)/len(rows),
            'hit_at_10':sum(r['any_expected_at_10'] for r in rows)/len(rows),
            'MRR_at_10':sum(1/r['first_expected_rank'] if r['first_expected_rank'] else 0 for r in rows)/len(rows),
            'cases':rows}
if __name__=='__main__':print(json.dumps(run(),ensure_ascii=False,indent=2))

"""Offline evidence retrieval and capability checks. Standard library only.
No language model, network calls, arbitrary execution, or author-method execution.
"""
from __future__ import annotations
import collections
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LAYERS = {'REVIEW', 'PRIMARY', 'CODE', 'ANALYSIS', 'TRANSFER'}
GOALS = {'genotype_phenotype_association', 'lineage_heritability',
         'relative_transition_dynamics', 'absolute_transition_rates',
         'spatial_niche_association'}
SCOPE_NOTICE = ('本库未取得目标综述订阅正文或完整图注。REVIEW 仅限公开已核验内容；'
                'PRIMARY/CODE 按各自来源范围；ANALYSIS/TRANSFER 为本库解释或建议。'
                '检索分数不是证据置信度；本工具不调用 LLM，不执行作者软件。')
# Query aliases improve Chinese/English access without claiming semantic embeddings.
ALIASES = [
    ('heritability', '遗传性', '遗传决定性', '谱系持续性'),
    ('plasticity', '可塑性'), ('genotype', '基因型'), ('phenotype', '表型'),
    ('lineage', 'phylogeny', '谱系', '祖先'), ('pseudotime', '拟时序'),
    ('moran', 'moran’s', "moran's"), ('cnv', 'cna', '拷贝数'),
    ('imputation', 'imputed', '插补'), ('dropout', '掉落', '漏检'),
    ('wildtype', 'wild-type', '野生型'), ('unresolved', 'unknown', '不确定'),
    ('pseudoreplication', '伪重复'), ('replicate', '独立重复'),
    ('ctmc', '转换矩阵'), ('transition', '转换'), ('selection', '选择'),
    ('branch_unit', '分支单位'), ('clock', '分子钟'),
    ('identifiability', '可识别性'), ('double dipping', '循环'),
    ('spatial', '空间'), ('niche', '生态位'), ('mitochondrial', '线粒体'),
    ('methylation', '甲基化'), ('variance', '方差'), ('causal', '因果'),
]

def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))

def load_jsonl(path: Path) -> list[dict[str, Any]]:
    out = []
    for i, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f'{path.name}:{i}: invalid JSON') from exc
        if not isinstance(obj, dict):
            raise ValueError(f'{path.name}:{i}: expected object')
        out.append(obj)
    return out

def tokens(text: str, expand: bool = False) -> list[str]:
    """Latin terms + Han unigrams/bigrams. Deterministic, no NLP dependencies."""
    text = text.lower()
    if expand:
        additions = []
        for group in ALIASES:
            if any(a in text for a in group):
                additions.extend(group)
        text += ' ' + ' '.join(additions)
    result = re.findall(r'[a-z0-9_]+(?:[\-\.][a-z0-9_]+)*', text)
    for seq in re.findall(r'[\u3400-\u9fff]+', text):
        if len(seq) == 1:
            result.append(seq)
        else:
            result.extend(seq[i:i+2] for i in range(len(seq)-1))
    return result


def checked_limit(value: Any) -> int:
    if type(value) is not int or not 1 <= value <= 20:
        raise ValueError('limit must be an integer between 1 and 20')
    return value

class KnowledgeBase:
    def __init__(self, root: Path = ROOT):
        self.root = Path(root).resolve()
        self.sources = {s['source_id']: s for s in load_json(self.root/'evidence/sources.json')}
        self.claims = {c['claim_id']: c for c in load_jsonl(self.root/'evidence/claims.jsonl')}
        self.corpus = load_jsonl(self.root/'evidence/corpus.jsonl')
        self.documents = {c['document_path'] for c in self.corpus}
        self.documents |= {'README.md', 'AGENTS.md', 'SKILL.md', 'RIGHTS.md', 'agent/INTEGRATION.md'}
        self.items = []
        for c in self.claims.values():
            self.items.append({'id': c['claim_id'], 'kind': 'claim', 'title': c['text'],
                'text': c['text'], 'layer': c['layer'], 'document_path': c['document_path'],
                'source_ids': [e['source_id'] for e in c['evidence']],
                'locator': c['evidence'], 'tags': c['tags'], 'limitations': c['limitations']})
        for c in self.corpus:
            self.items.append({'id': c['chunk_id'], 'kind': 'document_chunk',
                'title': c['title'], 'text': c['text'], 'layer': 'DOCUMENT_MIXED',
                'document_path': c['document_path'], 'source_ids': c['source_ids'],
                'locator': {'local_start_line': c['start_line'], 'local_end_line': c['end_line']},
                'tags': [], 'limitations': '本地课件段落含解释；按段内标签区分，不将全部文字归于引用来源。'})
        self.freqs = []
        self.df: collections.Counter[str] = collections.Counter()
        for item in self.items:
            text = item['title'] + ' ' + item['text'] + ' ' + ' '.join(item['tags'])
            freq = collections.Counter(tokens(text))
            self.freqs.append(freq)
            self.df.update(freq.keys())
        self.lengths = [sum(f.values()) for f in self.freqs]
        self.avglen = sum(self.lengths) / max(1, len(self.lengths))

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        checked_limit(limit)
        if not isinstance(query, str) or not query.strip():
            raise ValueError('query must be a nonempty string')
        if len(query) > 10000:
            raise ValueError('query too long (maximum 10000 characters)')
        qs = set(tokens(query, expand=True))
        if not qs:
            return []
        scores = []
        n = len(self.items)
        for idx, (item, freq) in enumerate(zip(self.items, self.freqs)):
            score = 0.0
            length_norm = 1.2 * (0.25 + 0.75 * self.lengths[idx] / max(self.avglen, 1))
            for term in qs:
                f = freq.get(term, 0)
                if f:
                    idf = math.log(1 + (n - self.df[term] + 0.5)/(self.df[term] + 0.5))
                    score += idf * f * 2.2/(f + length_norm)
            # Compact typed claims are the preferred reusable evidence units.
            if item['kind'] == 'claim':
                score *= 1.12
            if query.strip().lower() in (item['title']+' '+item['text']).lower():
                score += 5.0
            if score > 0:
                scores.append((score, item['id'], item))
        scores.sort(key=lambda x: (-x[0], x[1]))
        return [dict(item, score=round(score, 6)) for score, _, item in scores[:limit]]

    def read_claim(self, claim_id: str) -> dict[str, Any]:
        if not isinstance(claim_id, str) or claim_id not in self.claims:
            raise ValueError('unknown claim_id')
        return self.claims[claim_id]

    def read_document(self, path: str) -> dict[str, Any]:
        if not isinstance(path, str) or path not in self.documents:
            raise ValueError('only registered knowledge documents can be read')
        target = (self.root/path).resolve()
        if not target.is_relative_to(self.root) or not target.is_file():
            raise ValueError('invalid document path')
        return {'document_path': path, 'text': target.read_text(encoding='utf-8'),
                'scope_notice': SCOPE_NOTICE}

    def build_context(self, question: str, limit: int = 5) -> dict[str, Any]:
        hits = self.search(question, limit)
        source_ids = sorted({s for h in hits for s in h['source_ids']})
        return {'question': question, 'scope_notice': SCOPE_NOTICE,
                'retrieval_only': True, 'model_called': False, 'hits': hits,
                'sources': [self.sources[s] for s in source_ids],
                'open_gaps': load_json(self.root/'evidence/gaps.json'),
                'answer_instructions': ['事实引用 claim_id、source_id 与已核验 locator。',
                    '本地课件行号不是原文页码；DOCUMENT_MIXED 不能整体升级成 PRIMARY。',
                    '独立推导标记 ANALYSIS；迁移建议标记 TRANSFER。',
                    '未取得正文、未运行作者算法时明确说明；无法支持的结论列出边界。',
                    '检索无匹配时说本库未检得证据，不把无结果当作事实不存在。']}

    def validate(self, checksums: bool = True) -> dict[str, Any]:
        errors = []
        raw_claims = load_jsonl(self.root/'evidence/claims.jsonl')
        if len(raw_claims) != len(self.claims):
            errors.append('duplicate claim IDs')
        raw_sources = load_json(self.root/'evidence/sources.json')
        if len(raw_sources) != len(self.sources):
            errors.append('duplicate source IDs')
        for c in self.claims.values():
            if c['layer'] not in LAYERS:
                errors.append(f'{c["claim_id"]}: invalid layer')
            if not (self.root/c['document_path']).is_file():
                errors.append(f'{c["claim_id"]}: missing document')
            if c['layer'] in {'REVIEW','PRIMARY','CODE'} and not c['evidence']:
                errors.append(f'{c["claim_id"]}: source-based claim lacks evidence')
            for ev in c['evidence']:
                if ev['source_id'] not in self.sources or not ev.get('locator'):
                    errors.append(f'{c["claim_id"]}: invalid evidence')
                if c['layer']=='CODE' and self.sources[ev['source_id']]['source_type']!='author_code':
                    errors.append(f'{c["claim_id"]}: code evidence is not code')
        chunk_ids = [c['chunk_id'] for c in self.corpus]
        if len(chunk_ids) != len(set(chunk_ids)):
            errors.append('duplicate chunk IDs')
        for c in self.corpus:
            if not (self.root/c['document_path']).is_file():
                errors.append(f'{c["chunk_id"]}: missing document')
            for s in c['source_ids']:
                if s not in self.sources:
                    errors.append(f'{c["chunk_id"]}: unknown source {s}')
        node_ids={n['id'] for n in load_json(self.root/'graph/nodes.json')}
        for edge in load_json(self.root/'graph/edges.json'):
            if edge['source'] not in node_ids or edge['target'] not in node_ids or edge['claim_id'] not in self.claims:
                errors.append('graph contains an unresolved reference')
        for m in load_json(self.root/'methods/catalog.json'):
            if m['source'] not in self.sources or not (self.root/m['document_path']).is_file():
                errors.append('invalid method reference')
        for qa in load_jsonl(self.root/'tests/evaluation_questions.jsonl'):
            if any(c not in self.claims for c in qa['expected_claim_ids']):
                errors.append('QA contains an unresolved claim')
        integrity_checked=0
        checksum_path=self.root/'audit/SHA256SUMS'
        if checksums and checksum_path.exists():
            for line in checksum_path.read_text(encoding='utf-8').splitlines():
                digest, relative=line.split('  ',1)
                path=(self.root/relative).resolve()
                if not path.is_relative_to(self.root) or not path.is_file():
                    errors.append('missing or unsafe checksum path: '+relative)
                elif hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
                    errors.append('checksum mismatch: '+relative)
                integrity_checked+=1
        return {'ok': not errors, 'errors': errors, 'sources': len(self.sources),
                'claims': len(self.claims), 'chunks': len(self.corpus),
                'methods': len(load_json(self.root/'methods/catalog.json')),
                'integrity_files_checked': integrity_checked,
                'scope': 'local artifact integrity only; no author method or biological validation'}


def check_project(project: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(project, dict):
        raise ValueError('project must be an object')
    schema = load_json(ROOT/'agent/project_schema.json')
    allowed = schema['properties']
    extra = sorted(set(project)-set(allowed))
    if extra:
        raise ValueError('unrecognized project fields: '+', '.join(extra))
    if not isinstance(project.get('project_id'),str) or not project['project_id'].strip():
        raise ValueError('project_id is required')
    goals=project.get('goals')
    if not isinstance(goals,list) or not goals or any(not isinstance(g,str) or g not in GOALS for g in goals):
        raise ValueError('goals must be a nonempty array of supported goal names')
    if 'modalities' in project and (not isinstance(project['modalities'],list) or any(not isinstance(x,str) for x in project['modalities'])):
        raise ValueError('modalities must be an array of strings')
    for key, value in project.items():
        if key.startswith('has_') or key in {'tree_leaf_ids_matched','time_calibrated'}:
            if value is not None and type(value) is not bool:
                raise ValueError(f'{key} must be boolean or null')
        if 'enum' in allowed[key] and value not in allowed[key]['enum']:
            raise ValueError(f'{key} has an invalid value')
    n=project.get('independent_units')
    if n is not None and (type(n) is not int or n < 1):
        raise ValueError('independent_units must be a positive integer or null')
    warnings=[]
    if n is None:
        warnings.append('独立生物重复数未知；不能推定具有跨个体推广性。')
    elif n==1:
        warnings.append('只有一个独立生物单位：可做个体内描述，不能用细胞数替代跨个体重复。')
    if project.get('has_patient_id') is not True:
        warnings.append('个体 ID 未确认；群体推广分析前需要患者/动物或适当实验单位标识。')
    origin=project.get('genotype_origin','unknown')
    if origin in {'inferred','imputed'}:
        warnings.append('基因型来自推断或插补：保留来源与置信度，审查与表型验证的证据循环。')
    if project.get('longitudinal_design')=='independent_stage_groups':
        warnings.append('分时期的独立样本是群体比较，不是直接追踪同一细胞。')
    if project.get('has_genotype') is True and origin=='none':
        raise ValueError('has_genotype=true conflicts with genotype_origin=none')
    decisions=[]
    for goal in dict.fromkeys(goals):
        missing=[]
        cards=[]
        def need(key:str, description:str):
            if project.get(key) is not True:
                state='未提供/未知' if project.get(key) is None else '明确没有'
                missing.append({'field':key,'state':state,'requirement':description})
        if goal=='genotype_phenotype_association':
            need('has_genotype','需要可信遗传标签；不能仅凭无突变 reads 填为 WT。')
            if origin=='unknown':
                missing.append({'field':'genotype_origin','state':'未提供/未知','requirement':'区分 direct/inferred/imputed。'})
            cards=['M01','M02','M03']
            if project.get('has_scDNA') is True:
                cards+=['M04']
            elif project.get('has_allele_counts') is True:
                cards+=['M05']
        elif goal in {'lineage_heritability','relative_transition_dynamics','absolute_transition_rates'}:
            need('has_tree','需要谱系证据支持的树，而非表达拟时序。')
            need('tree_leaf_ids_matched','树叶与表型必须一一对应。')
            cards=['M09']
            unit=project.get('branch_unit','unknown')
            if goal=='relative_transition_dynamics' and unit=='unknown':
                missing.append({'field':'branch_unit','state':'未知','requirement':'相对动态也需说明所用树尺度。'})
            if goal=='absolute_transition_rates':
                need('time_calibrated','绝对速率需要外部时间锚点和校准。')
                if unit not in {'days','years'}:
                    missing.append({'field':'branch_unit','state':unit,'requirement':'本合同绝对速率指日历时间，单位须为 days 或 years。'})
        elif goal=='spatial_niche_association':
            need('has_spatial','需要可靠坐标、区域与空间测量。')
        decisions.append({'goal':goal,'status':'blocked_for_claim' if missing else 'conditional_expert_review',
                          'missing_requirements':missing,'candidate_method_cards':cards,
                          'note':'通过输入门槛不代表模型有效或机制得到证明；仍需检测、采样和模型验证。'})
    return {'project_id':project['project_id'],'scope_notice':SCOPE_NOTICE,
            'decisions':decisions,'warnings':warnings,
            'unprovided_fields':sorted(set(allowed)-set(project)),
            'execution_performed':False,'clinical_recommendation':False,
            'next_step':'先解决与目标结论直接相关的输入缺口，再按对应方法卡做最小验证。'}

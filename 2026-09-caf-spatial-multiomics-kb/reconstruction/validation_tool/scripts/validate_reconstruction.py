#!/usr/bin/env python3
"""Validate an Omicos bioinformatics reconstruction project.

The validator checks structure, references, traceability-table shape, stage
ordering, and reproduction-status semantics. It cannot certify scientific
correctness. The packaged JSON Schema is enforced with ``jsonschema`` 4.x; the
validator fails closed when that dependency is unavailable or incompatible.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

SCRIPT_DIRECTORY = Path(__file__).resolve().parent
if str(SCRIPT_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIRECTORY))

from execution_contract import (
    argv_seed_bindings,
    dependency_contract_errors,
    normalized_dependency_name,
    python_local_import_closure,
)


TRACE_HEADER = [
    "analysis_id",
    "正文主张",
    "figure/panel",
    "method与参数",
    "code位置",
    "输入/输出",
    "复现状态",
    "冲突或缺口",
]

REPRODUCTION_STATUSES = {
    "已执行验证",
    "材料完整但未执行",
    "受阻",
    "材料冲突",
}

STAGE_ORDER = [
    "evidence_inventory",
    "cross_material_alignment",
    "reproducibility_audit",
    "execution_or_guidance",
    "biological_interpretation",
    "validation",
]

ACTIVE_CODE_STATUSES = {"active_call", "active_config"}
CODE_BUNDLE_STATUSES = ACTIVE_CODE_STATUSES | {"active_import_only"}
RECEIPT_PRODUCER = "reconstruct-bioinfo-protocol/run_reconstruction.py"
RECEIPT_VERSION = "1.0.0"
BLOCKED_RUNTIME_OBSERVATION_STATEMENT = (
    "The execution record is blocked at preflight; no qualifying scientific result "
    "is verified."
)
EVIDENCE_GROUP_LANES = {
    "paper_claim": "paper_claim",
    "figure": "figure",
    "method": "method",
}
EVIDENCE_GROUP_ROLES = {
    "paper_claim": {"main_text", "results_text"},
    "figure": {"figure_visual", "figure_caption"},
    "method": {"methods_text", "supplement_text"},
}
CODE_SOURCE_ROLES = {"code", "environment"}
CORE_AUDIT_TOPICS = {
    "preprocessing",
    "statistical_unit",
    "replication_pseudoreplication",
    "batch_confounding",
    "multiple_testing",
    "species_gene_ids",
    "parameter_consistency",
    "claim_strength",
}
POSITIVE_COMPLETION_RE = re.compile(
    r"(?:完成(?:了)?复现|复现(?:已)?完成|复现成功|验证通过|已成功?复现|已执行验证|"
    r"successfully\s+reproduced|reproduced\s+successfully|reproduction\s+(?:is\s+)?complete|"
    r"successfully\s+validated|validated\s+successfully)",
    re.IGNORECASE,
)
NEGATION_BEFORE_COMPLETION_RE = re.compile(
    r"(?:(?:未|不|没有|不得|不可|不能|切勿)\s*|"
    r"\b(?:not|no|without|never|cannot|can't)\s+)$",
    re.IGNORECASE,
)
MISSING_CODE_MARKERS = (
    "未提供",
    "未找到",
    "无代码",
    "缺少代码",
    "missing",
    "not provided",
    "not found",
)
UNKNOWN_VERSION_MARKERS = {
    "",
    "unknown",
    "unreported",
    "missing",
    "not_available",
    "n/a",
    "latest",
    "any",
    "*",
}
ABSOLUTE_WINDOWS_PATH_RE = re.compile(r"(?:^|[\s=\"'])(?:[A-Za-z]:[\\/]|[\\/]{2})")
ABSOLUTE_POSIX_PATH_RE = re.compile(r"(?:^|[\s=\"'])(?:/(?:home|users|tmp|var|opt|mnt|data|srv|root)/)", re.IGNORECASE)
CONCRETE_URL_RE = re.compile(r"\b(?:https?|wss?)://[^\s<>]+", re.IGNORECASE)
FIXED_PORT_RE = re.compile(r"(?:--port(?:=|\s+)|\b(?:localhost|127\.0\.0\.1):)\d{2,5}\b", re.IGNORECASE)
FIXED_ENDPOINT_RE = re.compile(
    r"--?(?:bind|endpoint|host|server|base[-_]?url)(?:=|\s+)(?!<|\$\{|\$env:)[^\s]+",
    re.IGNORECASE,
)
FIXED_LISTEN_PORT_RE = re.compile(r"--?(?:listen[-_]?port|port)(?:=|\s+)\d{2,5}\b", re.IGNORECASE)
SECRET_ARGUMENT_RE = re.compile(
    r"(?:--?(?:api[-_]?key|auth|credential|token|password|secret)|"
    r"\b(?:api[-_]?key|auth|credential|token|password|secret)\s*[=:])",
    re.IGNORECASE,
)
SHA256_RE = re.compile(r"^(?:sha256:)?[0-9a-fA-F]{64}$")
ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]*$")
BIOLOGICAL_OUTCOME_EN = (
    r"(?:cell(?:ular)?\s+(?:fate|survival|death|growth|proliferation|differentiation|"
    r"migration|invasion|viability|state|identity)|disease(?:\s+progression)?|"
    r"tumou?r\s+(?:growth|progression)|drug\s+resistance|treatment\s+response|"
    r"therap(?:y|eutic)\s+response|immune\s+response|pathway\s+activation|"
    r"(?:(?:gene|target)(?:\s+[A-Za-z][A-Za-z0-9_.-]*)?\s+expression|"
    r"[A-Za-z][A-Za-z0-9_.-]*\s+expression|expression)"
    r"(?!\s+(?:estimates?|measurements?|scores?|indices|proxies|outputs?|features?|matrices)\b)|"
    r"transcription|translation|"
    r"protein\s+abundance|signall?ing|metabolism|metastasis|apoptosis|phenotypes?|development|"
    r"survival|viability|resistance|progression)"
)
BIOLOGICAL_OUTCOME_ZH = (
    r"(?:\u7ec6\u80de(?:\u547d\u8fd0|\u5b58\u6d3b|\u6b7b\u4ea1|\u589e\u6b96|\u5206\u5316|"
    r"\u8fc1\u79fb|\u4fb5\u88ad|\u72b6\u6001|\u8eab\u4efd)|\u75be\u75c5\u8fdb\u5c55|"
    r"\u80bf\u7624(?:\u751f\u957f|\u8fdb\u5c55)|\u8010\u836f|\u6cbb\u7597\u53cd\u5e94|"
    r"\u514d\u75ab\u53cd\u5e94|\u901a\u8def\u6fc0\u6d3b|\u4fe1\u53f7\u8f6c\u5bfc|"
    r"\u57fa\u56e0[A-Za-z0-9_.-]*\u8868\u8fbe|\u8868\u8fbe|\u8f6c\u5f55|\u7ffb\u8bd1|"
    r"\u86cb\u767d\u4e30\u5ea6|\u4ee3\u8c22|\u8f6c\u79fb|\u51cb\u4ea1|\u8868\u578b|\u53d1\u80b2|\u5b58\u6d3b|"
    r"\u6d3b\u6027|\u8fdb\u5c55)"
)
CAUSAL_RE = re.compile(
    r"\b(?:causes?|causal|drives?|driven\s+by|leads?\s+to|promotes?|induces?|"
    r"suppresses?)\b|"
    rf"\b(?:(?:responsible|required|necessary|sufficient)\s+for\s+{BIOLOGICAL_OUTCOME_EN}|"
    rf"determines?\s+{BIOLOGICAL_OUTCOME_EN})\b|"
    r"\u56e0\u679c|\u5bfc\u81f4|\u9a71\u52a8|\u4fc3\u8fdb|\u8bf1\u5bfc|\u6291\u5236|"
    rf"(?:\u51b3\u5b9a|\u5fc5\u9700|\u5fc5\u8981|\u5145\u5206){BIOLOGICAL_OUTCOME_ZH}",
    re.IGNORECASE,
)
MECHANISM_RE = re.compile(
    r"\bmechanis(?:m|tic)\b|"
    rf"\b(?:(?:mediates?|controls?|regulates?)\s+{BIOLOGICAL_OUTCOME_EN}|"
    rf"{BIOLOGICAL_OUTCOME_EN}\s+(?:is\s+)?(?:mediated|controlled|regulated)\s+by)\b|"
    rf"\u673a\u5236|(?:\u4ecb\u5bfc|\u63a7\u5236|\u8c03\u63a7){BIOLOGICAL_OUTCOME_ZH}",
    re.IGNORECASE,
)
FLUX_RE = re.compile(
    r"\b(?:(?:true|measured)\s+(?:metabolic\s+)?flux"
    r"(?!\s+(?:score|proxy|estimate|inference|index)\b)|"
    r"(?:increases?|increased|decreases?|decreased|raises?|raised|reduces?|reduced|"
    r"higher|lower)\s+(?:metabolic\s+)?flux"
    r"(?!\s+(?:score|proxy|estimate|inference|index)\b)|"
    r"(?:metabolic\s+)?flux\s+(?:is\s+|was\s+|were\s+|became\s+)?"
    r"(?:increased|decreased|higher|lower|raised|reduced|rose|fell))\b|"
    r"\u771f\u5b9e\u901a\u91cf|\u5b9e\u6d4b\u901a\u91cf|"
    r"(?:\u589e\u52a0|\u964d\u4f4e|\u63d0\u9ad8|\u51cf\u5c11)(?:\u4ee3\u8c22)?\u901a\u91cf"
    r"(?!\u8bc4\u5206|\u5f97\u5206|\u6307\u6570|\u4f30\u8ba1)|"
    r"(?:\u4ee3\u8c22)?\u901a\u91cf(?:\u589e\u52a0|\u964d\u4f4e|\u63d0\u9ad8|\u51cf\u5c11|\u5347\u9ad8|\u4e0b\u964d)",
    re.IGNORECASE,
)
UNCERTAINTY_BEFORE_ASSERTION_RE = re.compile(
    r"(?:\b(?:may|might|could|possibly|potentially|whether|unclear|uncertain|unverified)\b|"
    r"\u53ef\u80fd|\u4e5f\u8bb8|\u6216\u8bb8|\u662f\u5426|\u4e0d\u6e05\u695a|"
    r"\u65e0\u6cd5\u9a8c\u8bc1).{0,48}$",
    re.IGNORECASE,
)
OPERATIONAL_SUBJECT_BEFORE_ASSERTION_RE = re.compile(
    r"(?:\bthe\s+)?(?:normalization(?:\s+(?:procedure|step))?|assay|model|workflow|"
    r"pipeline|code|script|analysis|method|parameter|setting|flag|option|input|metadata|"
    r"algorithm|software|test|filter|threshold)\s+(?:statistically\s+|computationally\s+)?$|"
    r"(?:\u8be5)?(?:\u6807\u51c6\u5316|\u68c0\u6d4b|\u6a21\u578b|\u6d41\u7a0b|\u7b97\u6cd5|"
    r"\u4ee3\u7801|\u811a\u672c|\u5206\u6790|\u65b9\u6cd5|\u53c2\u6570|\u8bbe\u7f6e|"
    r"\u8f93\u5165|\u5143\u6570\u636e)\s*$",
    re.IGNORECASE,
)
OPERATIONAL_PREDICATE_RE = re.compile(
    r"^(?:determines?|controls?|regulates?|\u51b3\u5b9a|\u63a7\u5236|\u8c03\u63a7)",
    re.IGNORECASE,
)
ATTRIBUTED_CLAIM_RE = re.compile(
    r"(?:论文|正文|作者|paper|article|authors?|study)\s*(?:中|所)?\s*"
    r"(?:声称|主张|报告|认为|claims?|reports?|states?|argues?)",
    re.IGNORECASE,
)
SELF_ASSERTION_RE = re.compile(
    r"(?:\b(?:our\s+(?:reconstruction|analysis)|we|the\s+reconstruction|"
    r"reconstructed\s+(?:evidence|analysis|results?))\b|本复现|本分析|我们)"
    r".{0,48}?(?:\b(?:shows?|proves?|demonstrates?|supports?|confirms?|establishes?|indicates?)\b|"
    r"表明|证明|显示|支持|确认)",
    re.IGNORECASE,
)
ATTRIBUTION_RESET_RE = re.compile(
    r"\b(?:and|but|while|whereas|however)\b|(?:并且|但是|但|而|同时)", re.IGNORECASE
)
UNSUPPORTED_HIGH_CEILINGS = {"causal", "mechanistic", "measured_flux"}
NUMERIC_TOKEN_RE = re.compile(
    r"(?<![\w.])[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?%?(?!\w)"
)
ENGLISH_QUANTITY_WORD_RE = re.compile(
    r"\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|"
    r"thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|"
    r"billion|trillion|first|second|third|fourth|fifth|sixth|seventh|eighth|"
    r"ninth|tenth|half|quarter|dozen|single|double|triple|quadruple|"
    r"once|twice|thrice)\b",
    re.IGNORECASE | re.ASCII,
)
CHINESE_NUMERAL = r"[零〇一二两三四五六七八九十百千万亿]+"
CHINESE_QUANTITY_WORD_RE = re.compile(
    rf"(?:百分之|千分之|万分之|第|约|近|逾|超过|低于|高于|等于|达到|达|为|是)\s*"
    rf"{CHINESE_NUMERAL}"
    rf"|{CHINESE_NUMERAL}\s*"
    r"(?:%|％|倍|个|组|例|项|次|天|年|月|日|小时|分钟|秒|样本|细胞|基因|读段|条|种)"
    rf"|{CHINESE_NUMERAL}\s*(?:$|[。；，、！？,.!?;:：])"
)
NONQUANTITATIVE_IDENTIFIER_RE = re.compile(
    r"\b(?:fig(?:ure)?|panel|table|supp(?:lementary)?|appendix)\s+"
    r"(?:[A-Za-z]+[-_.]?)?\d+[A-Za-z0-9_.-]*\b",
    re.IGNORECASE | re.ASCII,
)
NONQUANTITATIVE_BIOMEDICAL_IDENTIFIER_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:"
    r"(?:IL|PD|CTLA|HPV)-\d+[A-Za-z]*"
    r"|SARS-CoV-\d+"
    r"|(?:(?:hsa|mmu|rno|dme|cel|ath)-)?(?:miR|let)-\d+[A-Za-z]?(?:-[35]p)?"
    r"|(?:3|5)\s*['′’]\s*UTR"
    r"|5-(?:methylcytosine|hydroxymethylcytosine|mC|hmC)"
    r")(?![A-Za-z0-9])",
    re.IGNORECASE | re.ASCII,
)
NONQUANTITATIVE_DOMAIN_TERM_RE = re.compile(
    r"\bsingle-(?:cell|nucleus|cellular)\b|"
    r"\b(?:first|second|third)\s+principal\s+component\b|"
    r"第[一二三四五六七八九十]+主成分",
    re.IGNORECASE | re.ASCII,
)


def _finding(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def _normalise_sha256(value: str) -> str:
    value = value.strip().lower()
    return value.removeprefix("sha256:")


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _normalise_parameter_name(value: Any) -> str:
    return str(value or "").lower()


def _is_ascii_parameter_name(value: Any) -> bool:
    return (
        isinstance(value, str)
        and value.isascii()
        and ID_RE.fullmatch(value) is not None
    )


def _normalise_parameter_value(value: Any) -> str:
    if isinstance(value, float):
        return format(value, ".15g")
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _numeric_tokens(text: Any) -> list[tuple[str, Decimal]]:
    found: list[tuple[str, Decimal]] = []
    for match in NUMERIC_TOKEN_RE.finditer(str(text or "")):
        token = match.group(0)
        raw = token[:-1] if token.endswith("%") else token
        try:
            value = Decimal(raw)
        except InvalidOperation:
            continue
        if token.endswith("%"):
            value /= Decimal(100)
        found.append((token, value.normalize()))
    return found


def _code_without_comments(text: str) -> str:
    """Remove ordinary line comments before literal matching.

    This deliberately stays conservative and does not claim full language parsing;
    semantic reachability remains an expert-review concern.
    """
    kept: list[str] = []
    in_block = False
    for raw_line in text.splitlines():
        line = raw_line
        if in_block:
            end = line.find("*/")
            if end < 0:
                continue
            line = line[end + 2 :]
            in_block = False
        while "/*" in line:
            start = line.find("/*")
            end = line.find("*/", start + 2)
            if end < 0:
                line = line[:start]
                in_block = True
                break
            line = line[:start] + line[end + 2 :]
        stripped = line.lstrip()
        if stripped.startswith(("#", "//", ";", "--")):
            continue
        for marker in (" #", " //"):
            marker_index = line.find(marker)
            if marker_index >= 0:
                line = line[:marker_index]
        kept.append(line)
    return "\n".join(kept)


_NO_LITERAL = object()
MAX_PYTHON_ALIAS_DEPTH = 16
PYTHON_ASSIGNMENT_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _is_json_literal(value: Any) -> bool:
    if value is None or isinstance(value, (str, bool, int)):
        return True
    if isinstance(value, float):
        try:
            json.dumps(value, allow_nan=False)
        except (TypeError, ValueError):
            return False
        return True
    if isinstance(value, list):
        return all(_is_json_literal(item) for item in value)
    if isinstance(value, dict):
        return all(
            isinstance(key, str) and _is_json_literal(item)
            for key, item in value.items()
        )
    return False


def _ast_dict_keys_are_unique(node: ast.AST) -> bool:
    for candidate in ast.walk(node):
        if not isinstance(candidate, ast.Dict):
            continue
        seen: set[str] = set()
        for key_node in candidate.keys:
            if key_node is None:
                return False
            try:
                key = ast.literal_eval(key_node)
            except (SyntaxError, ValueError):
                return False
            if not isinstance(key, str) or key in seen:
                return False
            seen.add(key)
    return True


def _ast_json_literal(node: ast.AST) -> Any:
    if not _ast_dict_keys_are_unique(node):
        return _NO_LITERAL
    try:
        value = ast.literal_eval(node)
        json.dumps(value, ensure_ascii=False, allow_nan=False)
    except (SyntaxError, TypeError, ValueError):
        return _NO_LITERAL
    return value if _is_json_literal(value) else _NO_LITERAL


def _parse_simple_literal(value: str) -> Any:
    """Parse one strict JSON/Python JSON-safe literal, or return a sentinel."""

    raw = value.strip()
    candidates = [raw.rstrip(",;")]
    if ";" in raw:
        candidates.append(raw.split(";", 1)[0].strip())
    aliases = {"true": True, "false": False, "null": None, "none": None}
    for token in candidates:
        if not token:
            continue
        lowered = token.casefold()
        if lowered in aliases:
            return aliases[lowered]
        try:
            parsed_json = json.loads(
                token,
                object_pairs_hook=_strict_json_object,
                parse_constant=_reject_strict_json_constant,
            )
            json.dumps(parsed_json, ensure_ascii=False, allow_nan=False)
        except json.JSONDecodeError:
            pass
        except (TypeError, ValueError):
            # Duplicate keys, NaN/Infinity, and overflowing floats are strict
            # failures. Do not let a permissive Python parse resurrect them.
            continue
        else:
            if _is_json_literal(parsed_json):
                return parsed_json
            continue
        try:
            expression = ast.parse(token, mode="eval")
        except SyntaxError:
            continue
        parsed_python = _ast_json_literal(expression.body)
        if parsed_python is not _NO_LITERAL:
            return parsed_python
    return _NO_LITERAL


def _assignment_target_names(target: ast.AST) -> list[str]:
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, (ast.Tuple, ast.List)):
        return [
            name
            for element in target.elts
            for name in _assignment_target_names(element)
        ]
    return []


def _python_module_bindings(
    tree: ast.Module,
) -> tuple[dict[str, list[ast.AST]], dict[str, list[str]]]:
    bindings: dict[str, list[ast.AST]] = {}
    unsafe: dict[str, list[str]] = {}
    safe_statement_ids: set[int] = set()

    for statement in tree.body:
        if isinstance(statement, ast.Assign) and all(
            isinstance(target, ast.Name) for target in statement.targets
        ):
            safe_statement_ids.add(id(statement))
            for target in statement.targets:
                assert isinstance(target, ast.Name)
                bindings.setdefault(target.id, []).append(statement.value)
        elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            safe_statement_ids.add(id(statement))
            if statement.value is None:
                unsafe.setdefault(statement.target.id, []).append(
                    f"annotated assignment at line {statement.lineno} has no value"
                )
            else:
                bindings.setdefault(statement.target.id, []).append(statement.value)

    module_scope_nodes: list[ast.AST] = list(reversed(tree.body))
    while module_scope_nodes:
        node = module_scope_nodes.pop()
        if id(node) in safe_statement_ids:
            continue
        targets: list[ast.AST] = []
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        elif isinstance(node, (ast.AugAssign, ast.NamedExpr)):
            targets = [node.target]
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            targets = [node.target]
        elif isinstance(node, ast.With):
            targets = [
                item.optional_vars
                for item in node.items
                if item.optional_vars is not None
            ]
        elif isinstance(node, ast.AsyncWith):
            targets = [
                item.optional_vars
                for item in node.items
                if item.optional_vars is not None
            ]
        elif isinstance(node, ast.Delete):
            targets = list(node.targets)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            unsafe.setdefault(node.name, []).append(
                f"name is rebound by a definition at line {node.lineno}"
            )
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                imported = alias.asname or alias.name.split(".", 1)[0]
                unsafe.setdefault(imported, []).append(
                    f"name is imported dynamically at line {node.lineno}"
                )
        elif isinstance(node, ast.ExceptHandler) and isinstance(node.name, str):
            unsafe.setdefault(node.name, []).append(
                f"name is bound by an exception handler at line {node.lineno}"
            )
        for target in targets:
            for name in _assignment_target_names(target):
                unsafe.setdefault(name, []).append(
                    f"non-module-top-level or non-simple assignment at line {getattr(node, 'lineno', '?')}"
                )
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        module_scope_nodes.extend(reversed(list(ast.iter_child_nodes(node))))

    return bindings, unsafe


def _resolve_python_default(
    node: ast.AST,
    bindings: dict[str, list[ast.AST]],
    unsafe_bindings: dict[str, list[str]],
    *,
    stack: tuple[str, ...] = (),
) -> tuple[Any, str | None]:
    literal = _ast_json_literal(node)
    if literal is not _NO_LITERAL:
        return literal, None
    if not isinstance(node, ast.Name):
        return None, "default is dynamic rather than a JSON-safe literal or Name alias"
    name = node.id
    if not name.isascii() or PYTHON_ASSIGNMENT_NAME_RE.fullmatch(name) is None:
        return None, f"default alias {name!r} is not an ASCII assignment name"
    if name in stack:
        return None, "default alias cycle: " + " -> ".join((*stack, name))
    if len(stack) >= MAX_PYTHON_ALIAS_DEPTH:
        return None, f"default alias chain exceeds {MAX_PYTHON_ALIAS_DEPTH} bindings"
    if unsafe_bindings.get(name):
        return None, f"default alias {name!r} is unsafe: " + "; ".join(unsafe_bindings[name])
    candidates = bindings.get(name, [])
    if len(candidates) != 1:
        if not candidates:
            return None, f"default alias {name!r} has no single module-top-level literal binding"
        return None, f"default alias {name!r} is reassigned {len(candidates)} times"
    return _resolve_python_default(
        candidates[0], bindings, unsafe_bindings, stack=(*stack, name)
    )


MAX_STATIC_CLI_STRING_LENGTH = 1024


def _resolve_python_static_cli_string(
    node: ast.AST,
    bindings: dict[str, list[ast.AST]],
    unsafe_bindings: dict[str, list[str]],
    call: ast.Call,
    parents: dict[ast.AST, ast.AST],
    *,
    stack: tuple[str, ...] = (),
) -> tuple[str | None, str | None]:
    """Resolve a bounded, side-effect-free CLI target string expression."""

    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        if len(node.value) > MAX_STATIC_CLI_STRING_LENGTH:
            return None, "CLI target string exceeds the static length limit"
        return node.value, None
    if isinstance(node, ast.Name):
        name = node.id
        if not name.isascii() or PYTHON_ASSIGNMENT_NAME_RE.fullmatch(name) is None:
            return None, f"CLI target alias {name!r} is not canonical ASCII"
        if _default_alias_is_shadowed(call, name, parents):
            return None, f"CLI target alias {name!r} is shadowed at the call site"
        if name in stack or len(stack) >= MAX_PYTHON_ALIAS_DEPTH:
            return None, "CLI target alias is cyclic or too deep"
        if unsafe_bindings.get(name):
            return None, f"CLI target alias {name!r} is unsafe or reassigned"
        candidates = bindings.get(name, [])
        if len(candidates) != 1:
            return None, f"CLI target alias {name!r} lacks one safe module binding"
        return _resolve_python_static_cli_string(
            candidates[0],
            bindings,
            unsafe_bindings,
            call,
            parents,
            stack=(*stack, name),
        )
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, left_error = _resolve_python_static_cli_string(
            node.left, bindings, unsafe_bindings, call, parents, stack=stack
        )
        right, right_error = _resolve_python_static_cli_string(
            node.right, bindings, unsafe_bindings, call, parents, stack=stack
        )
        if left_error or right_error or left is None or right is None:
            return None, left_error or right_error or "CLI string concatenation is dynamic"
        combined = left + right
        if len(combined) > MAX_STATIC_CLI_STRING_LENGTH:
            return None, "CLI target string exceeds the static length limit"
        return combined, None
    return None, "CLI target expression is dynamic"


def _static_getattr_cli_method(node: ast.AST) -> str | None:
    if (
        not isinstance(node, ast.Call)
        or not isinstance(node.func, ast.Name)
        or node.func.id != "getattr"
        or len(node.args) < 2
        or not isinstance(node.args[1], ast.Constant)
        or not isinstance(node.args[1].value, str)
    ):
        return None
    method = node.args[1].value
    return method if method in CLI_REGISTRATION_CALLS else None


def _call_is_conditional(node: ast.Call, parents: dict[ast.AST, ast.AST]) -> bool:
    conditional_types = (
        ast.If,
        ast.For,
        ast.AsyncFor,
        ast.While,
        ast.Try,
        ast.IfExp,
        ast.BoolOp,
        ast.ListComp,
        ast.SetComp,
        ast.DictComp,
        ast.GeneratorExp,
        ast.comprehension,
    )
    current: ast.AST | None = node
    while current in parents:
        current = parents[current]
        if isinstance(current, conditional_types):
            return True
        if hasattr(ast, "Match") and isinstance(current, ast.Match):
            return True
        if hasattr(ast, "TryStar") and isinstance(current, ast.TryStar):
            return True
    return False


def _scope_bound_names(scope: ast.AST) -> set[str]:
    names: set[str] = set()
    if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
        arguments = scope.args
        names.update(argument.arg for argument in arguments.posonlyargs)
        names.update(argument.arg for argument in arguments.args)
        names.update(argument.arg for argument in arguments.kwonlyargs)
        if arguments.vararg is not None:
            names.add(arguments.vararg.arg)
        if arguments.kwarg is not None:
            names.add(arguments.kwarg.arg)
    body = getattr(scope, "body", [])
    pending = list(reversed(body if isinstance(body, list) else [body]))
    while pending:
        node = pending.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            names.add(getattr(node, "name", ""))
            continue
        targets: list[ast.AST] = []
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        elif isinstance(node, (ast.AugAssign, ast.NamedExpr)):
            targets = [node.target]
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            targets = [node.target]
        for target in targets:
            names.update(_assignment_target_names(target))
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names.update(alias.asname or alias.name.split(".", 1)[0] for alias in node.names)
        pending.extend(reversed(list(ast.iter_child_nodes(node))))
    names.discard("")
    return names


def _default_alias_is_shadowed(
    call: ast.Call,
    alias_name: str,
    parents: dict[ast.AST, ast.AST],
) -> bool:
    child: ast.AST = call
    current: ast.AST = call
    while current in parents:
        parent = parents[current]
        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            evaluated_outside = (
                child in parent.decorator_list
                or child is parent.args
                or child is parent.returns
            )
            if not evaluated_outside and alias_name in _scope_bound_names(parent):
                return True
        elif isinstance(parent, ast.Lambda):
            if alias_name in _scope_bound_names(parent):
                return True
        elif isinstance(parent, ast.ClassDef):
            evaluated_outside = (
                child in parent.decorator_list
                or child in parent.bases
                or child in parent.keywords
            )
            if not evaluated_outside and alias_name in _scope_bound_names(parent):
                return True
        child = parent
        current = parent
    return False


CLI_REGISTRATION_CALLS = {"add_argument", "option", "set_defaults"}


def _resolve_python_callable_alias(
    name: str,
    bindings: dict[str, list[ast.AST]],
    unsafe_bindings: dict[str, list[str]],
    *,
    stack: tuple[str, ...] = (),
) -> tuple[str | None, str | None]:
    if name in stack or len(stack) >= MAX_PYTHON_ALIAS_DEPTH:
        return None, "callable alias is cyclic or too deep"
    if unsafe_bindings.get(name):
        return None, "callable alias is not a single safe module-top-level binding"
    candidates = bindings.get(name, [])
    if len(candidates) != 1:
        return None, "callable alias is missing or reassigned"
    value = candidates[0]
    if isinstance(value, ast.Attribute) and value.attr in CLI_REGISTRATION_CALLS:
        return value.attr, None
    getattr_method = _static_getattr_cli_method(value)
    if getattr_method is not None:
        return None, "getattr-based callable alias cannot be proven to target the intended parser"
    if isinstance(value, ast.Name):
        return _resolve_python_callable_alias(
            value.id,
            bindings,
            unsafe_bindings,
            stack=(*stack, name),
        )
    return None, "callable alias does not resolve to add_argument/option/set_defaults"


def _potential_cli_callable_aliases(tree: ast.Module) -> set[str]:
    candidates: list[tuple[set[str], ast.AST]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            names = {
                name
                for target in node.targets
                for name in _assignment_target_names(target)
            }
            candidates.append((names, node.value))
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            candidates.append((_assignment_target_names(node.target), node.value))
    aliases: set[str] = set()
    changed = True
    while changed:
        changed = False
        for names, value in candidates:
            is_alias = (
                isinstance(value, ast.Attribute)
                and value.attr in CLI_REGISTRATION_CALLS
            ) or _static_getattr_cli_method(value) is not None or (
                isinstance(value, ast.Name) and value.id in aliases
            )
            if is_alias and not names.issubset(aliases):
                aliases.update(names)
                changed = True
    return aliases


def _cli_name_matches_parameter(value: str, expected: str) -> bool:
    clean = value.lstrip("-")
    return clean.isascii() and clean.replace("-", "_").lower() == expected


def _cli_target_inspection(
    node: ast.Call,
    expected: str,
    bindings: dict[str, list[ast.AST]],
    unsafe_bindings: dict[str, list[str]],
    parents: dict[ast.AST, ast.AST],
) -> tuple[str, list[str], str | None, list[str]]:
    """Return MATCH/NO_MATCH/UNKNOWN plus resolved option and dest strings."""

    option_names: list[str] = []
    reasons: list[str] = []
    for value in node.args:
        if isinstance(value, ast.Starred):
            reasons.append("star-expanded CLI option names are dynamic")
            continue
        resolved, error = _resolve_python_static_cli_string(
            value, bindings, unsafe_bindings, node, parents
        )
        if error or resolved is None:
            reasons.append(error or "CLI option name is dynamic")
        else:
            option_names.append(resolved)

    dest_nodes = [keyword.value for keyword in node.keywords if keyword.arg == "dest"]
    explicit_dest: str | None = None
    if len(dest_nodes) > 1:
        reasons.append("CLI registration contains duplicate dest keywords")
    elif dest_nodes:
        explicit_dest, error = _resolve_python_static_cli_string(
            dest_nodes[0], bindings, unsafe_bindings, node, parents
        )
        if error or explicit_dest is None:
            reasons.append(error or "CLI dest is dynamic")

    if dest_nodes:
        matched = explicit_dest is not None and _cli_name_matches_parameter(
            explicit_dest, expected
        )
    else:
        matched = any(
            _cli_name_matches_parameter(option, expected) for option in option_names
        )
    if matched:
        return "MATCH", option_names, explicit_dest, list(dict.fromkeys(reasons))
    if reasons:
        return "UNKNOWN", option_names, explicit_dest, list(dict.fromkeys(reasons))
    return "NO_MATCH", option_names, explicit_dest, []


def _call_mentions_cli_parameter(
    node: ast.Call,
    expected: str,
    bindings: dict[str, list[ast.AST]],
    unsafe_bindings: dict[str, list[str]],
    parents: dict[ast.AST, ast.AST],
) -> bool:
    state, _, _, _ = _cli_target_inspection(
        node, expected, bindings, unsafe_bindings, parents
    )
    return state == "MATCH" or any(
        keyword.arg is not None and keyword.arg.lower() == expected
        for keyword in node.keywords
    )


def _unresolved_call_is_cli_shaped(node: ast.Call, function_name: str) -> bool:
    lowered = function_name.casefold()
    name_suggests_cli = any(
        term in lowered for term in ("register", "argument", "option", "cli")
    )
    getattr_shape = isinstance(node.func, ast.Call) and isinstance(
        node.func.func, ast.Name
    ) and node.func.func.id == "getattr"
    keyword_shape = any(keyword.arg == "dest" for keyword in node.keywords)
    return name_suggests_cli or getattr_shape or keyword_shape


def _python_cli_default_inspections(
    code_text: str, parameter_name: str
) -> tuple[list[Any], list[str]]:
    """Resolve deterministic argparse/Click defaults and report every ambiguity."""

    if not _is_ascii_parameter_name(parameter_name):
        return [], [f"parameter name {parameter_name!r} is not canonical ASCII"]
    try:
        tree = ast.parse(code_text)
    except SyntaxError as exc:
        return [], [f"active Python source cannot be parsed: {exc.msg} at line {exc.lineno}"]

    expected = parameter_name.lower()
    bindings, unsafe_bindings = _python_module_bindings(tree)
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    values: list[Any] = []
    gaps: list[str] = []
    matching_default_sites = 0
    potential_callable_aliases = _potential_cli_callable_aliases(tree)

    confusable_assignment = re.compile(
        r"(?<![\w.-])(?P<name>[^\W\d]\w*)(?![\w.-])\s*(?:<-|=|:)",
        re.UNICODE,
    )
    for match in confusable_assignment.finditer(code_text):
        source_name = match.group("name")
        if (
            not source_name.isascii()
            and source_name.casefold() == expected.casefold()
        ):
            gaps.append(
                f"non-ASCII confusable assignment name {source_name!r} at source offset {match.start()}"
            )

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        target_state, option_names, explicit_dest, target_reasons = (
            _cli_target_inspection(
                node, expected, bindings, unsafe_bindings, parents
            )
        )
        function_name = ""
        if isinstance(node.func, ast.Attribute):
            function_name = node.func.attr
        elif isinstance(node.func, ast.Name):
            function_name = node.func.id
            if function_name in potential_callable_aliases:
                if _default_alias_is_shadowed(node, function_name, parents):
                    if target_state != "NO_MATCH" or _call_mentions_cli_parameter(
                        node, expected, bindings, unsafe_bindings, parents
                    ):
                        gaps.append(
                            f"CLI registration callable alias {function_name!r} at line "
                            f"{node.lineno} is shadowed at the call site"
                        )
                    continue
                resolved_function, alias_error = _resolve_python_callable_alias(
                    function_name, bindings, unsafe_bindings
                )
                if alias_error:
                    if _call_mentions_cli_parameter(
                        node, expected, bindings, unsafe_bindings, parents
                    ):
                        gaps.append(
                            f"CLI registration callable alias {function_name!r} at line "
                            f"{node.lineno} cannot be resolved safely: {alias_error}"
                        )
                    continue
                function_name = str(resolved_function)

        if function_name not in CLI_REGISTRATION_CALLS:
            if target_state == "MATCH" or (
                target_state == "UNKNOWN"
                and _unresolved_call_is_cli_shaped(node, function_name)
            ):
                detail = "; ".join(target_reasons) if target_reasons else "target matched"
                gaps.append(
                    f"CLI-like call for {parameter_name!r} at line {node.lineno} uses an "
                    "unresolved callable; getattr/subscript/partial/wrapper defaults cannot be "
                    f"excluded ({detail})"
                )
            continue

        default_nodes: list[ast.AST] = []
        relevant = False
        if function_name in {"add_argument", "option"}:
            if target_state == "UNKNOWN":
                gaps.append(
                    f"CLI registration target for {parameter_name!r} at line {node.lineno} "
                    "cannot be resolved safely: " + "; ".join(target_reasons)
                )
                continue
            if target_reasons:
                gaps.append(
                    f"CLI registration for {parameter_name!r} at line {node.lineno} has "
                    "additional dynamic targets: " + "; ".join(target_reasons)
                )
            for option in option_names:
                clean = option.lstrip("-")
                if not clean.isascii() and clean.casefold() == expected.casefold():
                    gaps.append(f"non-ASCII confusable CLI option {option!r} at line {node.lineno}")
            if isinstance(explicit_dest, str):
                if not explicit_dest.isascii() and explicit_dest.casefold() == expected.casefold():
                    gaps.append(
                        f"non-ASCII confusable argparse dest {explicit_dest!r} at line {node.lineno}"
                    )
            relevant = target_state == "MATCH"
            if relevant:
                default_nodes = [
                    keyword.value for keyword in node.keywords if keyword.arg == "default"
                ]
        elif function_name == "set_defaults":
            for keyword in node.keywords:
                if keyword.arg is None:
                    gaps.append(
                        f"set_defaults uses dynamic **mapping at line {node.lineno}; {parameter_name!r} cannot be excluded"
                    )
                elif keyword.arg.lower() == expected:
                    relevant = True
                    default_nodes.append(keyword.value)

        if relevant and not default_nodes:
            required_node = next(
                (keyword.value for keyword in node.keywords if keyword.arg == "required"),
                None,
            )
            required = _ast_json_literal(required_node) if required_node is not None else False
            if required is not True:
                gaps.append(
                    f"CLI option for {parameter_name!r} at line {node.lineno} has no explicit "
                    "default; parser-level, decorator-level, or dynamic defaults cannot be excluded"
                )
            continue
        if not relevant or not default_nodes:
            continue
        matching_default_sites += len(default_nodes)
        if _call_is_conditional(node, parents):
            gaps.append(f"CLI default is defined conditionally at line {node.lineno}")
        for default_node in default_nodes:
            if isinstance(default_node, ast.Name) and _default_alias_is_shadowed(
                node, default_node.id, parents
            ):
                gaps.append(
                    f"line {node.lineno}: default alias {default_node.id!r} is bound in a non-module scope"
                )
                continue
            value, error = _resolve_python_default(
                default_node, bindings, unsafe_bindings
            )
            if error:
                gaps.append(f"line {node.lineno}: {error}")
            else:
                values.append(value)

    if matching_default_sites > 1:
        gaps.append(
            f"parameter {parameter_name!r} is reassigned through "
            f"{matching_default_sites} CLI default definitions"
        )
    return values, list(dict.fromkeys(gaps))


def _python_parameter_assignment_inspections(
    code_text: str, parameter_name: str
) -> tuple[list[Any], list[str]]:
    """Resolve module-scope assignments whose ASCII name is the parameter name."""

    if not _is_ascii_parameter_name(parameter_name):
        return [], [f"parameter name {parameter_name!r} is not canonical ASCII"]
    try:
        tree = ast.parse(code_text)
    except SyntaxError as exc:
        return [], [f"active Python source cannot be parsed: {exc.msg} at line {exc.lineno}"]
    bindings, unsafe_bindings = _python_module_bindings(tree)
    expected = parameter_name.lower()
    candidate_names = sorted(
        name
        for name in set(bindings) | set(unsafe_bindings)
        if name.isascii()
        and PYTHON_ASSIGNMENT_NAME_RE.fullmatch(name) is not None
        and name.lower() == expected
    )
    if not candidate_names:
        return [], []
    if len(candidate_names) > 1:
        return [], [
            f"parameter {parameter_name!r} has multiple case-variant assignment names: "
            + ", ".join(candidate_names)
        ]

    assignment_name = candidate_names[0]
    candidates = bindings.get(assignment_name, [])
    values: list[Any] = []
    gaps: list[str] = []
    for candidate in candidates:
        literal = _ast_json_literal(candidate)
        if literal is not _NO_LITERAL:
            values.append(literal)
            continue
        value, error = _resolve_python_default(candidate, bindings, unsafe_bindings)
        if error:
            gaps.append(f"parameter assignment {assignment_name!r}: {error}")
        else:
            values.append(value)
    if unsafe_bindings.get(assignment_name):
        gaps.append(
            f"parameter assignment {assignment_name!r} is unsafe: "
            + "; ".join(unsafe_bindings[assignment_name])
        )
    if len(candidates) > 1:
        gaps.append(
            f"parameter assignment {assignment_name!r} is reassigned {len(candidates)} times"
        )
    return values, list(dict.fromkeys(gaps))


def _active_code_parameter_inspection(
    analysis: dict[str, Any], project_dir: Path, parameter_name: Any
) -> tuple[list[tuple[Any, str]], list[dict[str, str]]]:
    """Return proven values plus fail-closed static-resolution gaps."""

    name = str(parameter_name or "").strip()
    if not _is_ascii_parameter_name(name):
        return [], [
            {
                "name": name,
                "code_ref": "",
                "reason": "reported parameter name must match the canonical ASCII identifier grammar",
            }
        ]
    assignment = re.compile(
        rf"(?<![A-Za-z0-9_.-]){re.escape(name)}(?![A-Za-z0-9_.-])\s*(?:<-|=|:)\s*(.+?)\s*$",
        re.IGNORECASE | re.ASCII,
    )
    found: list[tuple[Any, str]] = []
    gaps: list[dict[str, str]] = []
    for item in analysis.get("code_locations", []):
        if not isinstance(item, dict) or item.get("evidence_status") not in ACTIVE_CODE_STATUSES:
            continue
        code_ref = str(item.get("evidence_id", ""))
        code_path, error = _project_relative_path(project_dir, item.get("path"))
        if error or code_path is None or not code_path.is_file():
            continue
        raw_code_text = code_path.read_text(encoding="utf-8", errors="replace")
        code_text = _code_without_comments(raw_code_text)
        if code_path.suffix.lower() == ".py":
            assignment_values, assignment_gaps = _python_parameter_assignment_inspections(
                raw_code_text, name
            )
            found.extend((value, code_ref) for value in assignment_values)
            gaps.extend(
                {"name": name, "code_ref": code_ref, "reason": reason}
                for reason in assignment_gaps
            )
            default_values, default_gaps = _python_cli_default_inspections(
                raw_code_text, name
            )
            found.extend((value, code_ref) for value in default_values)
            gaps.extend(
                {"name": name, "code_ref": code_ref, "reason": reason}
                for reason in default_gaps
            )
        elif code_path.suffix.lower() == ".json":
            try:
                document = json.loads(
                    raw_code_text,
                    object_pairs_hook=_strict_json_object,
                    parse_constant=_reject_strict_json_constant,
                )
                json.dumps(document, ensure_ascii=False, allow_nan=False)
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                gaps.append(
                    {
                        "name": name,
                        "code_ref": code_ref,
                        "reason": f"active JSON config is not strict JSON: {exc}",
                    }
                )
            else:
                json_values = _json_parameter_values(document, name)
                found.extend((value, code_ref) for value in json_values)
                if len(json_values) > 1:
                    gaps.append(
                        {
                            "name": name,
                            "code_ref": code_ref,
                            "reason": (
                                f"parameter {name!r} is reassigned through "
                                f"{len(json_values)} active JSON config fields"
                            ),
                        }
                    )

                pending: list[Any] = [document]
                while pending:
                    value = pending.pop()
                    if isinstance(value, dict):
                        for key, item_value in value.items():
                            if (
                                isinstance(key, str)
                                and not key.isascii()
                                and key.casefold() == name.casefold()
                            ):
                                gaps.append(
                                    {
                                        "name": name,
                                        "code_ref": code_ref,
                                        "reason": f"non-ASCII confusable JSON assignment name {key!r}",
                                    }
                                )
                            pending.append(item_value)
                    elif isinstance(value, list):
                        pending.extend(value)
        else:
            confusable_assignment = re.compile(
                r"(?<![\w.-])(?P<name>[^\W\d]\w*)(?![\w.-])\s*(?:<-|=|:)",
                re.UNICODE,
            )
            for match in confusable_assignment.finditer(raw_code_text):
                source_name = match.group("name")
                if (
                    not source_name.isascii()
                    and source_name.casefold() == name.casefold()
                ):
                    gaps.append(
                        {
                            "name": name,
                            "code_ref": code_ref,
                            "reason": f"non-ASCII confusable assignment name {source_name!r}",
                        }
                    )
            assignment_count = 0
            for line_number, line in enumerate(code_text.splitlines(), start=1):
                match = assignment.search(line)
                if not match:
                    continue
                assignment_count += 1
                parsed = _parse_simple_literal(match.group(1))
                if parsed is _NO_LITERAL:
                    gaps.append(
                        {
                            "name": name,
                            "code_ref": code_ref,
                            "reason": (
                                f"assignment at line {line_number} is dynamic, non-JSON-safe, "
                                "or invalid strict JSON (duplicate keys/NaN are forbidden)"
                            ),
                        }
                    )
                else:
                    found.append((parsed, code_ref))
            if assignment_count > 1:
                gaps.append(
                    {
                        "name": name,
                        "code_ref": code_ref,
                        "reason": (
                            f"parameter {name!r} is reassigned through "
                            f"{assignment_count} active config assignments"
                        ),
                    }
                )
    unique_gaps = [dict(item) for item in {tuple(sorted(item.items())) for item in gaps}]
    unique_gaps.sort(key=lambda item: (item.get("code_ref", ""), item.get("reason", "")))
    return found, unique_gaps


def _active_code_assignments(
    analysis: dict[str, Any], project_dir: Path, parameter_name: Any
) -> list[tuple[Any, str]]:
    values, _ = _active_code_parameter_inspection(
        analysis, project_dir, parameter_name
    )
    return values


def _json_values_equal(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _json_values_equal(a, b) for a, b in zip(left, right)
        )
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            _json_values_equal(left[key], right[key]) for key in left
        )
    return left == right


def _strict_json_equal(left: Any, right: Any) -> bool:
    """Compare JSON values without treating integers and floats as interchangeable."""

    if type(left) is not type(right):
        return False
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _strict_json_equal(a, b) for a, b in zip(left, right)
        )
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            _strict_json_equal(left[key], right[key]) for key in left
        )
    return left == right


def _strict_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _reject_strict_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON number is not allowed: {value}")


def _evidence_text_contains_value(path: Path, value: Any) -> bool:
    """Conservatively bind a declared check observation to textual evidence."""

    text = _read_bounded_utf8_text(path)
    if text is None:
        return False
    if isinstance(value, str):
        return value in text
    if isinstance(value, bool):
        rendered_values = {json.dumps(value), repr(value)}
    elif isinstance(value, (int, float)):
        try:
            rendered_values = {json.dumps(value, allow_nan=False), repr(value)}
        except ValueError:
            return False
    else:
        return False
    return any(
        re.search(rf"(?<![\w.+-]){re.escape(rendered)}(?![\w.+-])", text)
        for rendered in rendered_values
    )


def _read_bounded_utf8_text(path: Path) -> str | None:
    try:
        if path.stat().st_size > 16 * 1024 * 1024:
            return None
        payload = path.read_bytes()
        if b"\x00" in payload:
            return None
        return payload.decode("utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return None


def _json_parameter_values(value: Any, name: str) -> list[Any]:
    found: list[Any] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str) and key.lower() == name.lower():
                found.append(item)
            found.extend(_json_parameter_values(item, name))
    elif isinstance(value, list):
        for item in value:
            found.extend(_json_parameter_values(item, name))
    return found


def _literal_has_terminal(text: str, length: int, *, raw_string: bool) -> bool:
    remainder = text[length:]
    if not remainder:
        return True
    if raw_string:
        return remainder[0] in ",;#}]"
    return remainder[0].isspace() or remainder[0] in ",;#}])"


def _assignment_value_matches(text: str, expected: Any) -> bool:
    candidate = text.lstrip()
    if not candidate:
        return False
    try:
        parsed, end = json.JSONDecoder().raw_decode(candidate)
    except json.JSONDecodeError:
        pass
    else:
        if _strict_json_equal(parsed, expected) and _literal_has_terminal(
            candidate, end, raw_string=False
        ):
            return True
    variants: list[tuple[str, bool]] = []
    try:
        variants.append((json.dumps(expected, ensure_ascii=False, allow_nan=False), False))
    except (TypeError, ValueError):
        return False
    variants.append((repr(expected), False))
    if isinstance(expected, str) and expected and not any(
        character.isspace() for character in expected
    ):
        variants.append((expected, True))
    for rendered, raw_string in sorted(set(variants), key=lambda item: len(item[0]), reverse=True):
        if candidate.startswith(rendered) and _literal_has_terminal(
            candidate, len(rendered), raw_string=raw_string
        ):
            return True
    return False


def _text_parameter_pair_state(text: str, name: str, expected: Any) -> tuple[bool, bool]:
    matched = False
    conflicting = False
    stripped = text.strip()
    json_candidates = [stripped]
    json_candidates.extend(
        line.strip()
        for line in text.splitlines()
        if line.strip().startswith(("{", "[")) and line.strip().endswith(("}", "]"))
    )
    for candidate in json_candidates:
        if not candidate:
            continue
        try:
            parsed = json.loads(
                candidate,
                object_pairs_hook=_strict_json_object,
                parse_constant=_reject_strict_json_constant,
            )
            json.dumps(parsed, ensure_ascii=False, allow_nan=False)
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
        for value in _json_parameter_values(parsed, name):
            if _strict_json_equal(value, expected):
                matched = True
            else:
                conflicting = True
    key_variants = {
        re.escape(name),
        re.escape(json.dumps(name, ensure_ascii=False)),
        re.escape(repr(name)),
    }
    assignment = re.compile(
        rf"(?<![\w.-])(?:{'|'.join(sorted(key_variants, key=len, reverse=True))})"
        rf"(?![\w.-])\s*(?:=|:)\s*",
        re.IGNORECASE,
    )
    for line in text.splitlines():
        for match in assignment.finditer(line):
            if _assignment_value_matches(line[match.end() :], expected):
                matched = True
            else:
                conflicting = True
    return matched, conflicting


def _parameter_is_unambiguously_observed(
    paths: Iterable[Path], name: Any, value: Any
) -> bool:
    name_text = str(name or "").strip()
    if not name_text:
        return False
    matched = False
    for path in paths:
        text = _read_bounded_utf8_text(path)
        if text is None:
            continue
        path_matched, path_conflicting = _text_parameter_pair_state(
            text, name_text, value
        )
        if path_conflicting:
            return False
        matched = matched or path_matched
    return matched


def _decode_json_pointer_token(token: str) -> tuple[str | None, str | None]:
    if re.search(r"~(?:[^01]|$)", token):
        return None, "JSON Pointer contains an invalid RFC6901 escape"
    return token.replace("~1", "/").replace("~0", "~"), None


def _json_pointer_value(document: Any, pointer: Any) -> tuple[Any, str | None]:
    if not isinstance(pointer, str):
        return None, "json_pointer_equals selector must be a string"
    if pointer == "":
        return document, None
    if not pointer.startswith("/"):
        return None, "JSON Pointer must be empty or start with '/'"
    current = document
    for raw in pointer[1:].split("/"):
        token, decode_error = _decode_json_pointer_token(raw)
        if decode_error or token is None:
            return None, decode_error
        if isinstance(current, dict):
            if token not in current:
                return None, f"JSON Pointer key does not exist: {token!r}"
            current = current[token]
        elif isinstance(current, list):
            if not re.fullmatch(r"0|[1-9][0-9]*", token):
                return None, f"JSON Pointer token is not a valid array index: {token!r}"
            index = int(token)
            if index >= len(current):
                return None, f"JSON Pointer array index is out of range: {index}"
            current = current[index]
        else:
            return None, "JSON Pointer cannot traverse through a JSON scalar"
    return current, None


def _strict_json_document(path: Path) -> tuple[Any, str | None]:
    text = _read_bounded_utf8_text(path)
    if text is None:
        return None, "JSON evidence must be bounded UTF-8 text without NUL bytes"
    try:
        document = json.loads(
            text,
            object_pairs_hook=_strict_json_object,
            parse_constant=_reject_strict_json_constant,
        )
        json.dumps(document, ensure_ascii=False, allow_nan=False)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        return None, f"JSON evidence is not strict JSON: {exc}"
    return document, None


def _strict_tsv_selected_row(
    path: Path, selector: Any
) -> tuple[dict[str, str] | None, str | None]:
    required = {"key_column", "key_value", "value_column"}
    allowed = required | {"unit_column"}
    if (
        not isinstance(selector, dict)
        or not required.issubset(selector)
        or not set(selector).issubset(allowed)
        or any(not isinstance(selector.get(key), str) or not selector.get(key) for key in selector)
    ):
        return None, (
            "tsv_cell_equals selector requires non-empty key_column, key_value, and "
            "value_column strings plus optional non-empty unit_column"
        )
    text = _read_bounded_utf8_text(path)
    if text is None:
        return None, "TSV evidence must be bounded UTF-8 text without NUL bytes"
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""), delimiter="\t")
        fieldnames = reader.fieldnames
        if not fieldnames or any(not name for name in fieldnames):
            return None, "TSV must have a non-empty header row"
        if len(fieldnames) != len(set(fieldnames)):
            return None, "TSV header names must be unique"
        for key in ("key_column", "value_column", "unit_column"):
            if key not in selector:
                continue
            if selector[key] not in fieldnames:
                return None, f"TSV selector column is absent: {selector[key]!r}"
        matches: list[dict[str, str]] = []
        for row_number, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                return None, f"TSV row {row_number} has the wrong field count"
            if row[selector["key_column"]] == selector["key_value"]:
                matches.append(row)
    except csv.Error as exc:
        return None, f"TSV evidence is invalid: {exc}"
    if len(matches) != 1:
        return None, f"TSV selector must match exactly one row; matched {len(matches)}"
    return matches[0], None


def _strict_tsv_cell(path: Path, selector: Any) -> tuple[str | None, str | None]:
    row, error = _strict_tsv_selected_row(path, selector)
    if error or row is None:
        return None, error
    return row[selector["value_column"]], None


def _mechanical_check_identity(
    project_dir: Path, check: Any
) -> tuple[str | None, str | None, str | None]:
    """Return mechanically anchored metric/unit, or an identity error."""

    if not isinstance(check, dict) or not isinstance(check.get("verification"), dict):
        return None, None, "check/verification must be objects"
    verification = check["verification"]
    kind = verification.get("kind")
    selector = verification.get("selector")
    evidence_path, path_error = _project_relative_path(
        project_dir, verification.get("evidence_path")
    )
    if path_error or evidence_path is None or not evidence_path.is_file():
        return None, None, f"verification evidence_path is invalid: {path_error or 'missing file'}"
    if kind == "tsv_cell_equals":
        row, row_error = _strict_tsv_selected_row(evidence_path, selector)
        if row_error or row is None:
            return None, None, row_error
        unit_column = selector.get("unit_column")
        unit = row[unit_column] if isinstance(unit_column, str) else "not_recorded"
        if not unit:
            return None, None, "selected TSV unit cell is empty"
        return str(selector["key_value"]), unit, None
    if kind == "json_pointer_equals":
        if not isinstance(selector, str):
            return None, None, "json_pointer_equals selector must be a string"
        return selector, "not_recorded", None
    if kind in {"text_contains", "sha256_equals"}:
        return None, "not_applicable", None
    return None, None, f"unsupported verification kind: {kind!r}"


def _evaluate_check_verification(
    project_dir: Path,
    verification: Any,
    allowed_evidence: set[Path],
    check_evidence: set[Path],
) -> tuple[Any, bool, str | None]:
    if not isinstance(verification, dict):
        return None, False, "verification must be an object"
    if set(verification) != {"kind", "evidence_path", "selector", "expected"}:
        return None, False, "verification must contain exactly kind, evidence_path, selector, expected"
    evidence_path, path_error = _project_relative_path(
        project_dir, verification.get("evidence_path")
    )
    if path_error or evidence_path is None or not evidence_path.is_file():
        return None, False, f"verification evidence_path is invalid: {path_error or 'missing file'}"
    if evidence_path not in allowed_evidence or evidence_path not in check_evidence:
        return None, False, "verification evidence_path must be one of this check's recorded evidence paths"
    kind = verification.get("kind")
    selector = verification.get("selector")
    expected = verification.get("expected")
    observed: Any
    if kind == "tsv_cell_equals":
        observed, tsv_error = _strict_tsv_cell(evidence_path, selector)
        if tsv_error:
            return None, False, tsv_error
    elif kind == "json_pointer_equals":
        document, json_error = _strict_json_document(evidence_path)
        if json_error:
            return None, False, json_error
        observed, pointer_error = _json_pointer_value(document, selector)
        if pointer_error:
            return None, False, pointer_error
    elif kind == "text_contains":
        if selector is not None or not isinstance(expected, str) or not expected:
            return None, False, "text_contains requires selector=null and a non-empty expected string"
        text = _read_bounded_utf8_text(evidence_path)
        if text is None:
            return None, False, "text_contains evidence must be bounded UTF-8 text"
        observed = expected in text
        return observed, observed is True, None
    elif kind == "sha256_equals":
        if selector is not None or not isinstance(expected, str) or not SHA256_RE.fullmatch(expected):
            return None, False, "sha256_equals requires selector=null and a SHA-256 expected value"
        observed = _sha256_file(evidence_path)
        return observed, observed == _normalise_sha256(expected), None
    else:
        return None, False, f"unsupported verification kind: {kind!r}"
    return observed, _strict_json_equal(observed, expected), None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _project_relative_path(project_dir: Path, value: Any) -> tuple[Path | None, str | None]:
    text = str(value or "").strip()
    if not text:
        return None, "path is empty"
    candidate = Path(text)
    if candidate.is_absolute() or ABSOLUTE_WINDOWS_PATH_RE.search(text):
        return None, "path must be project-relative"
    try:
        resolved = (project_dir / candidate).resolve()
        resolved.relative_to(project_dir)
    except (OSError, ValueError):
        return None, "path escapes the project directory"
    return resolved, None


def _parse_utc_timestamp(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def _line_asserts_completion(line: str) -> bool:
    for match in POSITIVE_COMPLETION_RE.finditer(line):
        prefix = line[: match.start()]
        if NEGATION_BEFORE_COMPLETION_RE.search(prefix):
            continue
        return True
    return False


def _source_set_fingerprint(sources: Any) -> str:
    compact: list[dict[str, Any]] = []
    if isinstance(sources, list):
        for source in sources:
            if not isinstance(source, dict):
                continue
            compact.append(
                {
                    "source_id": source.get("source_id"),
                    "location": source.get("location"),
                    "availability": source.get("availability"),
                    "fingerprint": source.get("fingerprint"),
                }
            )
    payload = json.dumps(compact, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _read_json(path: Path, errors: list[dict[str, str]]) -> Any | None:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_json_object,
            parse_constant=_reject_strict_json_constant,
        )
        json.dumps(value, ensure_ascii=False, allow_nan=False)
        return value
    except FileNotFoundError:
        errors.append(_finding("missing_file", path.name, f"required file is missing: {path.name}"))
    except UnicodeDecodeError as exc:
        errors.append(_finding("invalid_encoding", path.name, f"file is not UTF-8: {exc}"))
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        errors.append(
            _finding(
                "invalid_json",
                path.name,
                f"strict JSON parse failed: {exc}",
            )
        )
    return None


def _read_trace_table(
    path: Path, errors: list[dict[str, str]]
) -> tuple[list[str], list[dict[str, str]]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            header = reader.fieldnames or []
            rows = list(reader)
    except FileNotFoundError:
        errors.append(_finding("missing_file", path.name, "required file is missing: traceability.tsv"))
        return [], []
    except UnicodeDecodeError as exc:
        errors.append(_finding("invalid_encoding", path.name, f"file is not UTF-8: {exc}"))
        return [], []

    if header != TRACE_HEADER:
        errors.append(
            _finding(
                "trace_header_mismatch",
                path.name,
                f"expected exact header {TRACE_HEADER!r}, observed {header!r}",
            )
        )
    for index, row in enumerate(rows, start=2):
        if None in row:
            errors.append(
                _finding(
                    "trace_column_count",
                    f"{path.name}:line {index}",
                    "row has more fields than the eight-column header",
                )
            )
        for column in TRACE_HEADER:
            if row.get(column) is None or not str(row.get(column, "")).strip():
                errors.append(
                    _finding(
                        "empty_trace_cell",
                        f"{path.name}:line {index}:{column}",
                        "traceability cells must be explicit; use a missing marker rather than blank text",
                    )
                )
    return header, rows


def _schema_validate(
    manifest: Any,
    schema_path: Path,
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> str:
    schema = _read_json(schema_path, errors)
    if schema is None or manifest is None:
        return "failed"
    try:
        import jsonschema  # type: ignore
    except ImportError:
        errors.append(
            _finding(
                "jsonschema_required",
                str(schema_path),
                "jsonschema is required for a passing validation; install a compatible 4.x release in an authorized environment",
            )
        )
        return "failed"

    validator = jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    )
    schema_errors = sorted(validator.iter_errors(manifest), key=lambda item: list(item.path))
    for exc in schema_errors:
        location = ".".join(str(part) for part in exc.absolute_path) or "$"
        errors.append(_finding("schema_violation", location, exc.message))
    return "passed" if not schema_errors else "failed"


def _evidence_groups(analysis: dict[str, Any]) -> Iterable[tuple[str, list[dict[str, Any]]]]:
    yield "paper_claim", analysis.get("paper_claim", {}).get("evidence", [])
    yield "figure", analysis.get("figure_panel", {}).get("evidence", [])
    yield "method", analysis.get("method_parameters", {}).get("evidence", [])


def _source_material_is_available(project_dir: Path, source: Any) -> bool:
    if not isinstance(source, dict) or source.get("availability") != "available":
        return False
    fingerprint = source.get("fingerprint")
    if not isinstance(fingerprint, str) or not SHA256_RE.fullmatch(fingerprint):
        return False
    location = str(source.get("location", "")).strip()
    parsed = urlparse(location)
    if parsed.scheme.lower() in {"http", "https", "ftp", "s3", "gs"} or re.match(
        r"^(?:doi:)?10\.\d{4,9}/", location, re.IGNORECASE
    ):
        return False
    candidate = Path(location)
    source_path = candidate.resolve() if candidate.is_absolute() else (project_dir / candidate).resolve()
    return source_path.is_file() and _sha256_file(source_path) == _normalise_sha256(fingerprint)


def _has_direct_evidence(
    analysis: dict[str, Any],
    group: str,
    sources_by_id: dict[str, dict[str, Any]],
    project_dir: Path,
) -> bool:
    for group_name, evidence in _evidence_groups(analysis):
        if group_name != group:
            continue
        return any(
            isinstance(item, dict)
            and item.get("evidence_class") == "直接证据"
            and item.get("lane") == EVIDENCE_GROUP_LANES.get(group)
            and str(item.get("source_id", "")).strip()
            and str(item.get("locator", "")).strip()
            and bool(
                set(sources_by_id.get(str(item.get("source_id", "")), {}).get("roles", []))
                & EVIDENCE_GROUP_ROLES.get(group, set())
            )
            and _source_material_is_available(
                project_dir, sources_by_id.get(str(item.get("source_id", "")))
            )
            for item in evidence
        )
    return False


def _command_display(argv: list[str]) -> str:
    return subprocess.list2cmdline(argv) if os.name == "nt" else shlex.join(argv)


def _argv_executes_entrypoint(argv: list[str], entrypoint: str) -> bool:
    if entrypoint not in argv:
        return False
    index = argv.index(entrypoint)
    suffix = Path(entrypoint).suffix.lower()
    launcher = Path(argv[0]).name.lower() if argv else ""
    launchers = {
        ".py": {"python", "python.exe", "python3", "python3.exe", "py", "py.exe"},
        ".r": {"r", "r.exe", "rscript", "rscript.exe"},
        ".jl": {"julia", "julia.exe"},
        ".sh": {"sh", "bash", "zsh"},
        ".ipynb": {"jupyter", "jupyter.exe", "jupyter-nbconvert", "jupyter-nbconvert.exe"},
    }
    allowed = launchers.get(suffix)
    if allowed is None:
        return index == 0
    if launcher not in allowed or index < 1:
        return False
    prefix_options = argv[1:index]
    if suffix == ".py":
        if launcher in {"py", "py.exe"}:
            return all(
                re.fullmatch(r"-[1-9](?:\.\d+)?(?:-\d+)?", token)
                or token in {"-B", "-E", "-O", "-OO", "-q", "-s", "-S", "-u", "-v"}
                for token in prefix_options
            )
        return all(
            token in {"-B", "-E", "-O", "-OO", "-q", "-s", "-S", "-u", "-v"}
            for token in prefix_options
        )
    return not prefix_options


def _execution_code_closure_gaps(
    record: dict[str, Any],
    project_dir: Path,
    active_code: dict[str, dict[str, Any]],
) -> list[str]:
    gaps: list[str] = []
    entrypoint, entrypoint_error = _project_relative_path(
        project_dir, record.get("entrypoint")
    )
    if entrypoint_error or entrypoint is None or not entrypoint.is_file():
        return ["code closure entrypoint is unavailable"]
    discovered, discovery_gaps = python_local_import_closure(project_dir, entrypoint)
    gaps.extend("code closure: " + gap for gap in discovery_gaps)

    raw_files = record.get("code_files")
    if not isinstance(raw_files, list) or not raw_files:
        return gaps + ["code_files must be a non-empty fingerprinted import closure"]
    recorded: dict[Path, str] = {}
    for index, item in enumerate(raw_files):
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            gaps.append(f"code_files[{index}] must contain exactly path and sha256")
            continue
        path, path_error = _project_relative_path(project_dir, item.get("path"))
        digest = item.get("sha256")
        if (
            path_error
            or path is None
            or not path.is_file()
            or not isinstance(digest, str)
            or not SHA256_RE.fullmatch(digest)
        ):
            gaps.append(f"code_files[{index}] is unavailable or lacks a valid SHA-256")
            continue
        if path in recorded:
            gaps.append(f"code_files[{index}] duplicates a physical code path")
            continue
        normalized = _normalise_sha256(digest)
        if _sha256_file(path) != normalized:
            gaps.append(f"code_files[{index}] hash no longer matches the executed code bundle")
        recorded[path] = normalized

    if set(recorded) != set(discovered):
        gaps.append("code_files does not exactly match the recursive local import closure")

    code_refs = {str(value) for value in record.get("code_evidence_refs", [])}
    for code_path, digest in recorded.items():
        matches: list[tuple[str, dict[str, Any]]] = []
        for evidence_id, item in active_code.items():
            item_path, item_error = _project_relative_path(project_dir, item.get("path"))
            if not item_error and item_path == code_path and evidence_id in code_refs:
                matches.append((evidence_id, item))
        if len(matches) != 1:
            gaps.append(
                f"code file {code_path.relative_to(project_dir).as_posix()} is not bound to exactly one active code_evidence_ref"
            )
            continue
        snapshot = matches[0][1].get("snapshot")
        if (
            not isinstance(snapshot, str)
            or not SHA256_RE.fullmatch(snapshot)
            or _normalise_sha256(snapshot) != digest
        ):
            gaps.append(
                f"active code evidence snapshot does not match {code_path.relative_to(project_dir).as_posix()}"
            )
    return list(dict.fromkeys(gaps))


def _blocked_runtime_is_directly_observable(
    record: dict[str, Any],
    project_dir: Path,
    execution_scope: str,
    execution_requested: bool,
    analysis: dict[str, Any],
) -> bool:
    """Recognize a fingerprint-consistent blocked preflight as operational evidence."""

    execution_id = str(record.get("execution_id", ""))
    analysis_id = str(analysis.get("analysis_id", ""))
    if (
        not ID_RE.fullmatch(execution_id)
        or record.get("attempt_status") != "blocked"
        or record.get("adjudication_status") != "blocked"
        or analysis_id not in record.get("analysis_ids", [])
        or execution_scope != "execute_now"
        or execution_requested is not True
        or record.get("receipt_path") is not None
        or record.get("receipt_sha256") is not None
        or record.get("outputs") != []
    ):
        return False

    argv = record.get("command_argv")
    if (
        not isinstance(argv, list)
        or len(argv) < 2
        or any(not isinstance(token, str) or not token for token in argv)
        or record.get("command") != _command_display(argv)
    ):
        return False
    entrypoint_text = str(record.get("entrypoint", ""))
    entrypoint, entrypoint_error = _project_relative_path(project_dir, entrypoint_text)
    if (
        entrypoint_error
        or entrypoint is None
        or not entrypoint.is_file()
        or not _argv_executes_entrypoint(argv, entrypoint_text)
    ):
        return False
    snapshot = record.get("code_snapshot_sha256")
    if (
        not isinstance(snapshot, str)
        or not SHA256_RE.fullmatch(snapshot)
        or _sha256_file(entrypoint) != _normalise_sha256(snapshot)
    ):
        return False
    active_code = {
        str(item.get("evidence_id", "")): item
        for item in analysis.get("code_locations", [])
        if isinstance(item, dict) and item.get("evidence_status") in CODE_BUNDLE_STATUSES
    }
    code_refs = record.get("code_evidence_refs")
    if not isinstance(code_refs, list) or not code_refs:
        return False
    if not any(
        str(ref) in active_code
        and _normalise_sha256(str(active_code[str(ref)].get("snapshot", "")))
        == _normalise_sha256(snapshot)
        for ref in code_refs
    ):
        return False
    if _execution_code_closure_gaps(record, project_dir, active_code):
        return False

    started = _parse_utc_timestamp(record.get("started_at_utc"))
    finished = _parse_utc_timestamp(record.get("finished_at_utc"))
    if started is None or finished is None or finished < started or record.get("exit_code") == 0:
        return False
    seed = record.get("seed")
    seed_values, malformed_seed = argv_seed_bindings(argv, entrypoint_text)
    if malformed_seed:
        return False
    if seed == "not_applicable":
        if not str(record.get("seed_reason", "")).strip() or seed_values:
            return False
    elif isinstance(seed, int) and not isinstance(seed, bool):
        if not seed_values or any(value != str(seed) for value in seed_values):
            return False
    else:
        return False

    run_relative = Path("runs") / execution_id
    run_dir = (project_dir / run_relative).resolve()
    preflight = record.get("preflight")
    if (
        not isinstance(preflight, dict)
        or preflight.get("authorization_basis") != "explicit_execution_request"
        or preflight.get("status") != "blocked"
        or preflight.get("source_read_only") is not True
        or preflight.get("environment") != "unavailable"
    ):
        return False
    output_dir, output_error = _project_relative_path(project_dir, preflight.get("output_directory"))
    if output_error or output_dir != run_dir or not run_dir.is_dir():
        return False

    for artifact in record.get("inputs", []):
        if not isinstance(artifact, dict):
            return False
        path, path_error = _project_relative_path(project_dir, artifact.get("path"))
        digest = artifact.get("sha256")
        if (
            path_error
            or path is None
            or not path.is_file()
            or str(artifact.get("path", "")) not in argv
            or not isinstance(digest, str)
            or not SHA256_RE.fullmatch(digest)
            or _sha256_file(path) != _normalise_sha256(digest)
        ):
            return False
    if not record.get("inputs"):
        return False

    log_paths: set[Path] = set()
    for field, filename in (("stdout_log", "stdout.log"), ("stderr_log", "stderr.log")):
        path, path_error = _project_relative_path(project_dir, record.get(field))
        if path_error or path != run_dir / filename or not path.is_file():
            return False
        log_paths.add(path)
    if len(log_paths) != 2:
        return False
    try:
        run_entries = list(run_dir.rglob("*"))
    except OSError:
        return False
    if any(path.is_symlink() for path in run_entries):
        return False
    actual_run_files = {path.resolve() for path in run_entries if path.is_file()}
    if actual_run_files != log_paths:
        return False

    checks = record.get("checks")
    if (
        not isinstance(checks, list)
        or not checks
        or _normalise_sha256(str(record.get("checks_sha256", "")))
        != _canonical_sha256(checks)
    ):
        return False
    relevant = [
        check
        for check in checks
        if isinstance(check, dict) and analysis_id in check.get("analysis_ids", [])
    ]
    if not relevant:
        return False
    for check in relevant:
        evidence_paths: set[Path] = set()
        for value in check.get("evidence_paths", []):
            path, path_error = _project_relative_path(project_dir, value)
            if path_error or path is None or path not in log_paths:
                return False
            evidence_paths.add(path)
        observed, passed, check_error = _evaluate_check_verification(
            project_dir, check.get("verification"), log_paths, evidence_paths
        )
        if (
            check_error
            or not _strict_json_equal(check.get("observed"), observed)
            or check.get("passed") is not passed
        ):
            return False
    return True


def _execution_is_qualifying(
    record: dict[str, Any],
    project_dir: Path,
    execution_scope: str,
    execution_requested: bool,
    analysis: dict[str, Any],
) -> tuple[bool, list[str]]:
    missing: list[str] = []
    analysis_id = str(analysis.get("analysis_id", ""))
    execution_id = str(record.get("execution_id", ""))
    if not ID_RE.fullmatch(execution_id):
        return False, ["execution_id must match ^[A-Za-z][A-Za-z0-9_.-]*$"]
    run_relative = Path("runs") / execution_id
    run_relative_text = run_relative.as_posix()

    if execution_scope == "none":
        missing.append("task.execution_scope permits no runtime evidence")
    elif execution_scope == "execute_now" and execution_requested is not True:
        missing.append("task.execution_requested=true")
    elif execution_scope == "audit_supplied_record" and execution_requested is not False:
        missing.append("audit_supplied_record requires execution_requested=false")
    if record.get("attempt_status") != "succeeded":
        missing.append("attempt_status=succeeded")
    if analysis_id not in record.get("analysis_ids", []):
        missing.append(f"record.analysis_ids includes {analysis_id}")

    active_code = {
        str(item.get("evidence_id", "")): item
        for item in analysis.get("code_locations", [])
        if isinstance(item, dict) and item.get("evidence_status") in CODE_BUNDLE_STATUSES
    }
    code_refs = record.get("code_evidence_refs")
    if not isinstance(code_refs, list) or not code_refs:
        missing.append("code_evidence_refs")
    elif not any(str(ref) in active_code for ref in code_refs):
        missing.append("at least one code_evidence_ref must identify loadable code for this analysis")

    argv = record.get("command_argv")
    if not isinstance(argv, list) or len(argv) < 2 or any(not isinstance(token, str) or not token for token in argv):
        missing.append("non-empty command_argv")
        argv = []
    elif record.get("command") != _command_display(argv):
        missing.append("command display does not match command_argv")

    entrypoint_text = str(record.get("entrypoint", "")).strip()
    entrypoint, entrypoint_error = _project_relative_path(project_dir, entrypoint_text)
    if entrypoint_error:
        missing.append(f"entrypoint: {entrypoint_error}")
    elif entrypoint is None or not entrypoint.is_file():
        missing.append("entrypoint file does not exist")
    else:
        if not _argv_executes_entrypoint(argv, entrypoint_text):
            missing.append("command_argv does not execute the recorded entrypoint with a compatible launcher")
        linked_code_paths: set[Path] = set()
        for ref in code_refs or []:
            code_item = active_code.get(str(ref))
            if not isinstance(code_item, dict):
                continue
            code_path, code_error = _project_relative_path(project_dir, code_item.get("path"))
            if not code_error and code_path is not None and code_path.is_file():
                linked_code_paths.add(code_path)
        if entrypoint not in linked_code_paths:
            missing.append(
                "entrypoint path does not equal any linked active code evidence path for this analysis"
            )
        code_snapshot = record.get("code_snapshot_sha256")
        if not isinstance(code_snapshot, str) or not SHA256_RE.fullmatch(code_snapshot):
            missing.append("code_snapshot_sha256")
        elif _sha256_file(entrypoint) != _normalise_sha256(code_snapshot):
            missing.append("entrypoint SHA-256 mismatch")
        matching_snapshots = {
            _normalise_sha256(str(active_code[str(ref)].get("snapshot", "")))
            for ref in code_refs or []
            if str(ref) in active_code
            and isinstance(active_code[str(ref)].get("snapshot"), str)
            and SHA256_RE.fullmatch(str(active_code[str(ref)].get("snapshot")))
        }
        if isinstance(code_snapshot, str) and SHA256_RE.fullmatch(code_snapshot):
            if _normalise_sha256(code_snapshot) not in matching_snapshots:
                missing.append("execution code snapshot does not match linked code evidence")
        missing.extend(
            _execution_code_closure_gaps(record, project_dir, active_code)
        )

    working_directory, path_error = _project_relative_path(project_dir, record.get("working_directory"))
    if path_error:
        missing.append(f"working_directory: {path_error}")
    elif working_directory is None or not working_directory.is_dir():
        missing.append("working_directory does not exist as a directory")

    started = _parse_utc_timestamp(record.get("started_at_utc"))
    finished = _parse_utc_timestamp(record.get("finished_at_utc"))
    if started is None:
        missing.append("valid timezone-aware started_at_utc")
    if finished is None:
        missing.append("valid timezone-aware finished_at_utc")
    if started is not None and finished is not None and finished < started:
        missing.append("finished_at_utc is earlier than started_at_utc")
    if record.get("exit_code") != 0:
        missing.append("exit_code=0")

    dependencies = record.get("dependencies")
    dependency_errors = dependency_contract_errors(dependencies)
    missing.extend(f"dependency contract: {message}" for message in dependency_errors)

    seed = record.get("seed")
    argv_seed_values, malformed_seed_option = argv_seed_bindings(argv, entrypoint_text)
    if malformed_seed_option:
        missing.append("command_argv contains an invalid or ambiguous seed-like option")
    if seed is None:
        missing.append("seed")
    elif seed == "not_applicable" and not str(record.get("seed_reason", "")).strip():
        missing.append("seed_reason")
    elif seed == "not_applicable" and argv_seed_values:
        missing.append("seed=not_applicable conflicts with an explicit seed option in command_argv")
    elif isinstance(seed, int) and not isinstance(seed, bool):
        if not argv_seed_values:
            missing.append("command_argv does not bind the recorded seed through a canonical long option")
        elif any(value != str(seed) for value in argv_seed_values):
            missing.append("explicit command_argv seed option conflicts with the recorded seed")

    resolved_artifacts: dict[str, list[Path]] = {"inputs": [], "outputs": []}
    record_artifacts: dict[str, dict[str, dict[str, Any]]] = {"inputs": {}, "outputs": {}}
    for field in ("inputs", "outputs"):
        artifacts = record.get(field)
        if not isinstance(artifacts, list) or not artifacts:
            missing.append(f"fingerprinted {field}")
            continue
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                missing.append(f"{field}[{index}] object")
                continue
            artifact_id = str(artifact.get("artifact_id", "")).strip()
            semantic_type = str(artifact.get("semantic_type", "")).strip()
            if not artifact_id or artifact_id in record_artifacts[field]:
                missing.append(f"{field}[{index}].artifact_id unique and non-empty")
            else:
                record_artifacts[field][artifact_id] = artifact
            if not semantic_type:
                missing.append(f"{field}[{index}].semantic_type")
            if field == "inputs" and "analysis_ids" in artifact:
                missing.append(f"{field}[{index}].analysis_ids is output-only metadata")
            if field == "outputs":
                owners = artifact.get("analysis_ids")
                record_owners = {str(value) for value in record.get("analysis_ids", [])}
                if (
                    not isinstance(owners, list)
                    or not owners
                    or len(owners) != len(set(str(value) for value in owners))
                    or not {str(value) for value in owners}.issubset(record_owners)
                ):
                    missing.append(
                        f"{field}[{index}].analysis_ids must be a non-empty unique subset of record.analysis_ids"
                    )
            digest = artifact.get("sha256")
            if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
                missing.append(f"{field}[{index}].sha256")
            artifact_path, artifact_error = _project_relative_path(project_dir, artifact.get("path"))
            if artifact_error:
                missing.append(f"{field}[{index}].path: {artifact_error}")
                continue
            if artifact_path is None or not artifact_path.is_file():
                missing.append(f"{field}[{index}] file does not exist")
                continue
            if artifact_path in resolved_artifacts[field]:
                missing.append(f"{field}[{index}].path resolves to a duplicate physical artifact")
            resolved_artifacts[field].append(artifact_path)
            if isinstance(digest, str) and SHA256_RE.fullmatch(digest):
                if _sha256_file(artifact_path) != _normalise_sha256(digest):
                    missing.append(f"{field}[{index}] SHA-256 mismatch")
            if field == "inputs" and str(artifact.get("path")) not in argv:
                missing.append(f"command_argv does not name input {artifact.get('path')}")
            if field == "outputs" and started is not None and finished is not None:
                modified = artifact_path.stat().st_mtime
                if modified < started.timestamp() - 2 or modified > finished.timestamp() + 2:
                    missing.append(f"{field}[{index}] modification time is outside the recorded run")

    analysis_specs = analysis.get("inputs_outputs", {})
    for field in ("inputs", "outputs"):
        for artifact in analysis_specs.get(field, []):
            if not isinstance(artifact, dict):
                continue
            artifact_id = str(artifact.get("artifact_id", ""))
            observed = record_artifacts[field].get(artifact_id)
            if observed is None:
                missing.append(f"execution {field} do not include analysis artifact_id {artifact_id}")
                continue
            if observed.get("path") != artifact.get("path"):
                missing.append(f"analysis/execution path mismatch for {artifact_id}")
            if observed.get("semantic_type") != artifact.get("semantic_type"):
                missing.append(f"analysis/execution semantic_type mismatch for {artifact_id}")
            if field == "outputs" and analysis_id not in observed.get("analysis_ids", []):
                missing.append(f"execution output {artifact_id} is not owned by analysis {analysis_id}")
            fingerprint = artifact.get("fingerprint")
            if not isinstance(fingerprint, str) or not SHA256_RE.fullmatch(fingerprint):
                missing.append(f"analysis artifact {artifact_id} lacks an executed SHA-256 fingerprint")
            elif _normalise_sha256(fingerprint) != _normalise_sha256(str(observed.get("sha256", ""))):
                missing.append(f"analysis/execution fingerprint mismatch for {artifact_id}")

    resolved_logs: list[Path] = []
    for field in ("stdout_log", "stderr_log"):
        log_path, log_error = _project_relative_path(project_dir, record.get(field))
        if log_error:
            missing.append(f"{field}: {log_error}")
        elif log_path is None or not log_path.is_file():
            missing.append(f"{field} file does not exist")
        else:
            resolved_logs.append(log_path)
            if started is not None and finished is not None:
                modified = log_path.stat().st_mtime
                if modified < started.timestamp() - 2 or modified > finished.timestamp() + 2:
                    missing.append(f"{field} modification time is outside the recorded run")

    output_directory: Path | None = None
    preflight = record.get("preflight")
    if not isinstance(preflight, dict):
        missing.append("preflight record")
    else:
        expected_basis = (
            "explicit_execution_request" if execution_scope == "execute_now" else "supplied_runtime_evidence"
        )
        if preflight.get("authorization_basis") != expected_basis:
            missing.append(f"preflight.authorization_basis={expected_basis}")
        if preflight.get("status") != "passed":
            missing.append("preflight.status=passed")
        if preflight.get("source_read_only") is not True:
            missing.append("preflight.source_read_only=true")
        if preflight.get("environment") not in {"existing", "isolated"}:
            missing.append("preflight.environment is existing or isolated")
        output_text = str(preflight.get("output_directory", ""))
        output_directory, output_error = _project_relative_path(project_dir, output_text)
        if output_error:
            missing.append(f"preflight.output_directory: {output_error}")
        elif output_directory is None or not output_directory.is_dir():
            missing.append("preflight.output_directory does not exist")
        elif output_directory != (project_dir / run_relative).resolve():
            missing.append(f"preflight.output_directory must be exactly {run_relative_text}")
        else:
            for output_path in resolved_artifacts["outputs"]:
                try:
                    output_path.relative_to(output_directory)
                except ValueError:
                    missing.append("output artifact is outside preflight.output_directory")
            for log_path in resolved_logs:
                try:
                    log_path.relative_to(output_directory)
                except ValueError:
                    missing.append("runtime log is outside preflight.output_directory")
            for input_path in resolved_artifacts["inputs"]:
                try:
                    input_path.relative_to(output_directory)
                except ValueError:
                    continue
                missing.append("input artifact must remain outside the dedicated run directory")
        if argv and not any(
            token in argv
            for token in (
                run_relative_text,
                str(run_relative),
                *[str(item.get("path", "")) for item in record.get("outputs", []) if isinstance(item, dict)],
            )
        ):
            missing.append("command_argv does not name the run directory or a declared output")

    input_set = set(resolved_artifacts["inputs"])
    output_set = set(resolved_artifacts["outputs"])
    log_set = set(resolved_logs)
    if input_set & output_set or input_set & log_set or output_set & log_set:
        missing.append("input, output, and log artifact roles must be path-disjoint")
    if len(resolved_logs) != len(set(resolved_logs)):
        missing.append("stdout_log and stderr_log must be distinct files")

    covered_outputs: set[Path] = set()
    checks = record.get("checks")
    if not isinstance(checks, list) or not checks:
        missing.append("result checks")
    else:
        check_ids: set[str] = set()
        for check_index, check in enumerate(checks):
            if not isinstance(check, dict):
                continue
            check_id = str(check.get("check_id", ""))
            if not ID_RE.fullmatch(check_id) or check_id in check_ids:
                missing.append(f"checks[{check_index}].check_id unique and valid")
            check_ids.add(check_id)
            if not str(check.get("metric", "")).strip():
                missing.append(f"checks[{check_index}].metric")
            if not str(check.get("unit", "")).strip():
                missing.append(f"checks[{check_index}].unit")
            expected_metric, expected_unit, identity_error = _mechanical_check_identity(
                project_dir, check
            )
            if identity_error:
                missing.append(f"checks[{check_index}] identity: {identity_error}")
            else:
                if expected_metric is not None and str(check.get("metric", "")) != expected_metric:
                    missing.append(f"checks[{check_index}].metric does not match the selector")
                if str(check.get("unit", "")) != expected_unit:
                    missing.append(
                        f"checks[{check_index}].unit does not match mechanically selected unit metadata"
                    )
        allowed_evidence = set(resolved_artifacts["outputs"] + resolved_logs)
        relevant_checks = [
            (check_index, check)
            for check_index, check in enumerate(checks)
            if isinstance(check, dict) and analysis_id in check.get("analysis_ids", [])
        ]
        if not relevant_checks:
            missing.append(f"result check linked to analysis {analysis_id}")
        for index, check in relevant_checks:
            if not isinstance(check, dict) or check.get("passed") is not True:
                missing.append(f"checks[{index}] passed")
                continue
            evidence_paths = check.get("evidence_paths")
            if not isinstance(evidence_paths, list) or not evidence_paths:
                missing.append(f"checks[{index}].evidence_paths")
                continue
            resolved_check_evidence: list[Path] = []
            for evidence_index, value in enumerate(evidence_paths):
                evidence_path, evidence_error = _project_relative_path(project_dir, value)
                if evidence_error:
                    missing.append(f"checks[{index}].evidence_paths[{evidence_index}]: {evidence_error}")
                elif evidence_path is None or not evidence_path.is_file():
                    missing.append(f"checks[{index}].evidence_paths[{evidence_index}] does not exist")
                elif evidence_path not in allowed_evidence:
                    missing.append(
                        f"checks[{index}].evidence_paths[{evidence_index}] is not an output or runtime log"
                    )
                else:
                    resolved_check_evidence.append(evidence_path)
            if resolved_check_evidence:
                computed_observed, computed_passed, verification_error = (
                    _evaluate_check_verification(
                        project_dir,
                        check.get("verification"),
                        allowed_evidence,
                        set(resolved_check_evidence),
                    )
                )
                if verification_error:
                    missing.append(f"checks[{index}].verification: {verification_error}")
                else:
                    if not _strict_json_equal(check.get("observed"), computed_observed):
                        missing.append(
                            f"checks[{index}].observed does not equal the mechanically recomputed value"
                        )
                    if check.get("passed") is not computed_passed:
                        missing.append(
                            f"checks[{index}].passed does not equal the mechanically recomputed predicate"
                        )
                    verification_path, verification_path_error = _project_relative_path(
                        project_dir,
                        check.get("verification", {}).get("evidence_path")
                        if isinstance(check.get("verification"), dict)
                        else None,
                    )
                    if (
                        not verification_path_error
                        and verification_path is not None
                        and computed_passed
                        and verification_path in output_set
                    ):
                        covered_outputs.add(verification_path)
    for artifact in analysis_specs.get("outputs", []):
        if isinstance(artifact, dict):
            expected_output, output_error = _project_relative_path(project_dir, artifact.get("path"))
            if output_error or expected_output is None or expected_output not in covered_outputs:
                missing.append(f"analysis output {artifact.get('artifact_id')} lacks a passed linked result check")

    observed_parameters = record.get("observed_parameters")
    if not isinstance(observed_parameters, list):
        missing.append("observed_parameters list")
    else:
        allowed_observation_evidence = set(resolved_artifacts["outputs"] + resolved_logs)
        observed_names: set[str] = set()
        for parameter_index, parameter in enumerate(observed_parameters):
            if not isinstance(parameter, dict):
                missing.append(f"observed_parameters[{parameter_index}] object")
                continue
            name = _normalise_parameter_name(parameter.get("name"))
            raw_name = str(parameter.get("name", ""))
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]*", raw_name) or not name or name in observed_names:
                missing.append(f"observed_parameters[{parameter_index}].name unique and non-empty")
            observed_names.add(name)
            if parameter.get("value") is None:
                missing.append(f"observed_parameters[{parameter_index}].value")
            if name == "seed" and not _strict_json_equal(parameter.get("value"), seed):
                missing.append(
                    f"observed_parameters[{parameter_index}] seed conflicts with the canonical execution seed"
                )
            evidence_paths = parameter.get("evidence_paths")
            if not isinstance(evidence_paths, list) or not evidence_paths:
                missing.append(f"observed_parameters[{parameter_index}].evidence_paths")
                continue
            resolved_parameter_evidence: list[Path] = []
            for evidence_index, value in enumerate(evidence_paths):
                evidence_path, evidence_error = _project_relative_path(project_dir, value)
                if evidence_error:
                    missing.append(
                        f"observed_parameters[{parameter_index}].evidence_paths[{evidence_index}]: {evidence_error}"
                    )
                elif evidence_path is None or not evidence_path.is_file():
                    missing.append(
                        f"observed_parameters[{parameter_index}].evidence_paths[{evidence_index}] does not exist"
                    )
                elif evidence_path not in allowed_observation_evidence:
                    missing.append(
                        f"observed_parameters[{parameter_index}].evidence_paths[{evidence_index}] "
                        "is not an output or runtime log"
                    )
                else:
                    resolved_parameter_evidence.append(evidence_path)
            if resolved_parameter_evidence and not _parameter_is_unambiguously_observed(
                resolved_parameter_evidence,
                parameter.get("name"),
                parameter.get("value"),
            ):
                missing.append(
                    f"observed_parameters[{parameter_index}] name/value is not present "
                    "as one unambiguous assignment or JSON pair in its referenced textual evidence"
                )
        reported_names = {
            _normalise_parameter_name(parameter.get("name"))
            for parameter in analysis.get("method_parameters", {}).get("parameters", [])
            if isinstance(parameter, dict) and parameter.get("value_status") == "reported"
        }
        for reported_name in sorted(reported_names - observed_names):
            missing.append(
                f"runtime observation missing for reported parameter {reported_name}"
            )
        analysis_runtime_parameters = [
            parameter
            for parameter in analysis.get("method_parameters", {}).get("parameters", [])
            if isinstance(parameter, dict)
            and parameter.get("value_status") == "observed_runtime"
            and execution_id in {str(value) for value in parameter.get("execution_record_refs", [])}
        ]
        for parameter_index, observed in enumerate(observed_parameters):
            if not isinstance(observed, dict):
                continue
            mirrored = any(
                _normalise_parameter_name(parameter.get("name"))
                == _normalise_parameter_name(observed.get("name"))
                and _strict_json_equal(parameter.get("value"), observed.get("value"))
                for parameter in analysis_runtime_parameters
            )
            if not mirrored:
                missing.append(
                    f"observed_parameters[{parameter_index}] is not mirrored by an analysis observed_runtime parameter"
                )

    receipt_expected_path = (run_relative / "execution_receipt.json").as_posix()
    if str(record.get("receipt_path", "")) not in {receipt_expected_path, str(run_relative / "execution_receipt.json")}:
        missing.append(f"receipt_path must be exactly {receipt_expected_path}")
    receipt_path, receipt_error = _project_relative_path(project_dir, record.get("receipt_path"))
    receipt: Any = None
    if receipt_error:
        missing.append(f"receipt_path: {receipt_error}")
    elif receipt_path is None or not receipt_path.is_file():
        missing.append("execution receipt file does not exist")
    else:
        receipt_hash = record.get("receipt_sha256")
        if not isinstance(receipt_hash, str) or not SHA256_RE.fullmatch(receipt_hash):
            missing.append("receipt_sha256")
        elif _sha256_file(receipt_path) != _normalise_sha256(receipt_hash):
            missing.append("execution receipt SHA-256 mismatch")
        try:
            receipt = json.loads(
                receipt_path.read_text(encoding="utf-8"),
                object_pairs_hook=_strict_json_object,
                parse_constant=_reject_strict_json_constant,
            )
            json.dumps(receipt, ensure_ascii=False, allow_nan=False)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
            missing.append("execution receipt is not strict UTF-8 JSON")
    if isinstance(receipt, dict):
        if receipt.get("receipt_schema_version") != "1.0.0":
            missing.append("receipt_schema_version=1.0.0")
        if receipt.get("producer") != RECEIPT_PRODUCER or receipt.get("producer_version") != RECEIPT_VERSION:
            missing.append("receipt producer/version")
        if not re.fullmatch(r"[0-9a-f]{32}", str(receipt.get("nonce", ""))):
            missing.append("receipt nonce")
        if (
            not isinstance(receipt.get("process_id"), int)
            or isinstance(receipt.get("process_id"), bool)
            or receipt.get("process_id", 0) <= 0
        ):
            missing.append("receipt process_id")
        mirrored_fields = (
            "execution_id",
            "analysis_ids",
            "command",
            "command_argv",
            "entrypoint",
            "code_evidence_refs",
            "code_snapshot_sha256",
            "code_files",
            "working_directory",
            "started_at_utc",
            "finished_at_utc",
            "exit_code",
            "dependencies",
            "seed",
            "seed_reason",
            "inputs",
            "outputs",
            "stdout_log",
            "stderr_log",
            "checks",
            "checks_sha256",
            "observed_parameters",
            "observed_parameters_sha256",
            "adjudication_status",
            "adjudicated_at_utc",
            "supersedes_execution_ids",
            "preflight",
            "code_provenance",
        )
        for field in mirrored_fields:
            if not _strict_json_equal(receipt.get(field), record.get(field)):
                missing.append(f"receipt/record mismatch: {field}")
        if receipt.get("process_status") not in {"succeeded", "failed"}:
            missing.append("receipt process_status")
        if record.get("attempt_status") == "succeeded" and receipt.get("process_status") != "succeeded":
            missing.append("succeeded attempt requires a succeeded receipt process_status")
        if receipt.get("adjudication_status") != record.get("attempt_status"):
            missing.append("receipt adjudication_status must equal record attempt_status")
        if record.get("adjudication_status") != record.get("attempt_status"):
            missing.append("record adjudication_status must equal attempt_status")
        if record.get("attempt_status") == "succeeded":
            if not checks or any(not isinstance(item, dict) or item.get("passed") is not True for item in checks):
                missing.append("succeeded attempt requires non-empty all-passed checks")
            if _parse_utc_timestamp(record.get("adjudicated_at_utc")) is None:
                missing.append("succeeded attempt requires adjudicated_at_utc")
        expected_checks_hash = _canonical_sha256(checks if isinstance(checks, list) else [])
        if _normalise_sha256(str(record.get("checks_sha256", ""))) != expected_checks_hash:
            missing.append("record checks SHA-256 mismatch")
        if _normalise_sha256(str(receipt.get("checks_sha256", ""))) != expected_checks_hash:
            missing.append("receipt checks SHA-256 mismatch")
        observed_parameters = record.get("observed_parameters")
        expected_observed_hash = _canonical_sha256(
            observed_parameters if isinstance(observed_parameters, list) else []
        )
        if _normalise_sha256(str(record.get("observed_parameters_sha256", ""))) != expected_observed_hash:
            missing.append("record observed_parameters SHA-256 mismatch")
        if _normalise_sha256(str(receipt.get("observed_parameters_sha256", ""))) != expected_observed_hash:
            missing.append("receipt observed_parameters SHA-256 mismatch")
        if receipt.get("missing_outputs") != []:
            missing.append("receipt records missing expected outputs")
        expected_outputs_from_record = [
            {
                "artifact_id": artifact.get("artifact_id"),
                "path": artifact.get("path"),
                "semantic_type": artifact.get("semantic_type"),
                "analysis_ids": artifact.get("analysis_ids"),
            }
            for artifact in record.get("outputs", [])
            if isinstance(artifact, dict)
        ]
        if not _strict_json_equal(receipt.get("expected_outputs"), expected_outputs_from_record):
            missing.append(
                "receipt expected_outputs must exactly mirror record outputs without SHA-256 fields"
            )
        if receipt.get("stdout_sha256") != (
            _sha256_file(resolved_logs[0]) if len(resolved_logs) >= 1 else None
        ):
            missing.append("receipt stdout SHA-256 mismatch")
        if receipt.get("stderr_sha256") != (
            _sha256_file(resolved_logs[1]) if len(resolved_logs) >= 2 else None
        ):
            missing.append("receipt stderr SHA-256 mismatch")
    elif receipt is not None:
        missing.append("execution receipt must be a JSON object")

    return not missing, list(dict.fromkeys(missing))


def _undeclared_parameter_conflicts(
    analysis: dict[str, Any], project_dir: Path
) -> list[dict[str, Any]]:
    parameters = [
        item
        for item in analysis.get("method_parameters", {}).get("parameters", [])
        if isinstance(item, dict)
        and item.get("value_status") in {"reported", "implemented", "observed_runtime"}
        and item.get("value") is not None
    ]
    declared = [
        item
        for item in analysis.get("conflicts_gaps", [])
        if isinstance(item, dict) and item.get("kind") == "conflict"
    ]
    conflicts: list[dict[str, Any]] = []
    for left_index, left in enumerate(parameters):
        for right in parameters[left_index + 1 :]:
            if _normalise_parameter_name(left.get("name")) != _normalise_parameter_name(right.get("name")):
                continue
            if _normalise_parameter_value(left.get("value")) == _normalise_parameter_value(right.get("value")):
                continue
            left_refs = {str(value) for value in left.get("evidence_refs", [])}
            left_refs.update(str(value) for value in left.get("execution_record_refs", []))
            right_refs = {str(value) for value in right.get("evidence_refs", [])}
            right_refs.update(str(value) for value in right.get("execution_record_refs", []))
            covered = any(
                bool(left_refs & {str(value) for value in issue.get("evidence_refs", [])})
                and bool(right_refs & {str(value) for value in issue.get("evidence_refs", [])})
                for issue in declared
            )
            if not covered:
                conflicts.append(
                    {
                        "name": str(left.get("name", right.get("name", ""))),
                        "left_status": str(left.get("value_status", "")),
                        "left_value": left.get("value"),
                        "right_status": str(right.get("value_status", "")),
                        "right_value": right.get("value"),
                        "evidence_refs": sorted(left_refs | right_refs),
                    }
                )
    reported_parameters = [
        item for item in parameters if item.get("value_status") == "reported"
    ]
    for reported in reported_parameters:
        reported_refs = {str(value) for value in reported.get("evidence_refs", [])}
        for code_value, code_ref in _active_code_assignments(
            analysis, project_dir, reported.get("name")
        ):
            if _normalise_parameter_value(code_value) == _normalise_parameter_value(
                reported.get("value")
            ):
                continue
            evidence_refs = reported_refs | {code_ref}
            covered = any(
                bool(reported_refs & {str(value) for value in issue.get("evidence_refs", [])})
                and code_ref in {str(value) for value in issue.get("evidence_refs", [])}
                for issue in declared
            )
            if not covered:
                conflict = {
                    "name": str(reported.get("name", "")),
                    "left_status": "reported",
                    "left_value": reported.get("value"),
                    "right_status": "active_code_assignment",
                    "right_value": code_value,
                    "evidence_refs": sorted(evidence_refs),
                }
                if conflict not in conflicts:
                    conflicts.append(conflict)
    return conflicts


def _undeclared_static_parameter_gaps(
    analysis: dict[str, Any], project_dir: Path
) -> list[dict[str, Any]]:
    """Return static-default ambiguities not preserved as explicit blocking gaps."""

    declared_gaps = [
        item
        for item in analysis.get("conflicts_gaps", [])
        if isinstance(item, dict)
        and not item.get("resolved", False)
        and item.get("kind") == "gap"
        and item.get("blocking") is True
    ]
    declared_conflicts = [
        item
        for item in analysis.get("conflicts_gaps", [])
        if isinstance(item, dict)
        and not item.get("resolved", False)
        and item.get("kind") == "conflict"
    ]
    unresolved: list[dict[str, Any]] = []
    for parameter in analysis.get("method_parameters", {}).get("parameters", []):
        if not isinstance(parameter, dict) or parameter.get("value_status") != "reported":
            continue
        values, gaps = _active_code_parameter_inspection(
            analysis, project_dir, parameter.get("name")
        )
        distinct_values = {
            _normalise_parameter_value(value) for value, _ in values
        }
        reported_refs = {str(value) for value in parameter.get("evidence_refs", [])}
        for gap in gaps:
            code_ref = str(gap.get("code_ref", ""))
            evidence_refs = set(reported_refs)
            if code_ref:
                evidence_refs.add(code_ref)
            gap_covered = any(
                bool(reported_refs & {str(value) for value in issue.get("evidence_refs", [])})
                and bool(code_ref)
                and code_ref in {str(value) for value in issue.get("evidence_refs", [])}
                for issue in declared_gaps
            )
            conflict_covered = (
                "reassign" in str(gap.get("reason", "")).lower()
                and len(distinct_values) > 1
                and any(
                    bool(reported_refs & {str(value) for value in issue.get("evidence_refs", [])})
                    and bool(code_ref)
                    and code_ref in {str(value) for value in issue.get("evidence_refs", [])}
                    for issue in declared_conflicts
                )
            )
            if gap_covered or conflict_covered:
                continue
            finding = {
                "name": str(parameter.get("name", "")),
                "reason": str(gap.get("reason", "")),
                "evidence_refs": sorted(evidence_refs),
            }
            if finding not in unresolved:
                unresolved.append(finding)
    return unresolved


def _derive_analysis_status(
    analysis: dict[str, Any],
    executions: dict[str, dict[str, Any]],
    sources_by_id: dict[str, dict[str, Any]],
    project_dir: Path,
    execution_scope: str,
    execution_requested: bool,
    guidance_blocking_codes: set[str] | None = None,
) -> tuple[str, list[str], list[str]]:
    reasons: list[str] = []
    runtime_gaps: list[str] = []
    issues = analysis.get("conflicts_gaps", [])
    unresolved_conflicts = [
        item
        for item in issues
        if isinstance(item, dict) and item.get("kind") == "conflict" and not item.get("resolved", False)
    ]
    implicit_conflicts = _undeclared_parameter_conflicts(analysis, project_dir)
    implicit_parameter_gaps = _undeclared_static_parameter_gaps(analysis, project_dir)
    if unresolved_conflicts or implicit_conflicts:
        reasons.append("one or more unresolved cross-material conflicts exist")
        if implicit_conflicts:
            reasons.append("one or more differing parameter values were not declared as conflicts")
        return "材料冲突", reasons, runtime_gaps

    if implicit_parameter_gaps:
        reasons.append(
            "one or more active-code parameter defaults are dynamic, conditional, "
            "reassigned, non-ASCII, or otherwise not statically resolvable"
        )

    blocking_gaps = [
        item
        for item in issues
        if isinstance(item, dict)
        and item.get("kind") == "gap"
        and item.get("blocking") is True
        and not item.get("resolved", False)
    ]
    if blocking_gaps:
        reasons.append("one or more unresolved blocking gaps exist")

    blocked_audits = [
        str(item.get("topic", "unknown"))
        for item in analysis.get("scientific_audit", [])
        if isinstance(item, dict) and item.get("status") == "blocked"
    ]
    if blocked_audits:
        reasons.append("scientific audit is blocked: " + ", ".join(blocked_audits))

    active_code_material = False
    for item in analysis.get("code_locations", []):
        if not isinstance(item, dict) or item.get("evidence_status") not in ACTIVE_CODE_STATUSES:
            continue
        source = sources_by_id.get(str(item.get("source_id", "")))
        path, path_error = _project_relative_path(project_dir, item.get("path"))
        snapshot = item.get("snapshot")
        if (
            _source_material_is_available(project_dir, source)
            and bool(set(source.get("roles", [])) & CODE_SOURCE_ROLES)
            and not path_error
            and path is not None
            and path.is_file()
            and isinstance(snapshot, str)
            and SHA256_RE.fullmatch(snapshot)
            and _sha256_file(path) == _normalise_sha256(snapshot)
        ):
            active_code_material = True
            break

    input_specs = [
        item
        for item in analysis.get("inputs_outputs", {}).get("inputs", [])
        if isinstance(item, dict)
    ]
    valid_inputs = bool(input_specs)
    for item in input_specs:
        path, path_error = _project_relative_path(project_dir, item.get("path"))
        fingerprint = item.get("fingerprint")
        if (
            path_error
            or path is None
            or not path.is_file()
            or not isinstance(fingerprint, str)
            or not SHA256_RE.fullmatch(fingerprint)
            or _sha256_file(path) != _normalise_sha256(fingerprint)
        ):
            valid_inputs = False
            break

    required_material = {
        "direct paper claim": _has_direct_evidence(
            analysis, "paper_claim", sources_by_id, project_dir
        ),
        "direct figure/caption evidence": _has_direct_evidence(
            analysis, "figure", sources_by_id, project_dir
        ),
        "direct Methods evidence": _has_direct_evidence(
            analysis, "method", sources_by_id, project_dir
        ),
        "active code/config": active_code_material,
        "existing fingerprinted input": valid_inputs,
        "specified output": bool(analysis.get("inputs_outputs", {}).get("outputs")),
    }
    missing_material = [name for name, present in required_material.items() if not present]
    if missing_material:
        reasons.append("missing required material: " + ", ".join(missing_material))

    unresolved_parameters = [
        str(item.get("name", "unknown"))
        for item in analysis.get("method_parameters", {}).get("parameters", [])
        if isinstance(item, dict) and item.get("value_status") in {"unreported", "inferred"}
    ]
    if unresolved_parameters:
        reasons.append("unreported/inferred parameters remain unresolved: " + ", ".join(unresolved_parameters))

    guidance = analysis.get("code_guidance")
    guidance_blocked = isinstance(guidance, dict) and guidance.get("status") == "blocked"
    if guidance_blocked:
        reasons.append("code guidance is explicitly blocked")
    guidance_contract_codes = sorted(guidance_blocking_codes or set())
    if guidance_contract_codes:
        reasons.append(
            "code guidance fails blocking contract checks: "
            + ", ".join(guidance_contract_codes)
        )

    execution_ids = analysis.get("execution_record_ids", [])
    qualifying = False
    attempted = False
    analysis_id = str(analysis.get("analysis_id", ""))
    for execution_id in execution_ids:
        record = executions.get(execution_id)
        if record is None:
            runtime_gaps.append(f"execution record not found: {execution_id}")
            continue
        attempted = True
        passed, missing = _execution_is_qualifying(
            record,
            project_dir,
            execution_scope,
            execution_requested,
            analysis,
        )
        if passed:
            qualifying = True
        else:
            runtime_gaps.append(f"{execution_id}: " + ", ".join(missing))

    scope_without_record = execution_scope in {"execute_now", "audit_supplied_record"} and not execution_ids
    if scope_without_record:
        reasons.append("runtime scope requires an execution record, but this analysis links none")

    if (
        blocking_gaps
        or implicit_parameter_gaps
        or blocked_audits
        or missing_material
        or unresolved_parameters
        or guidance_blocked
        or guidance_contract_codes
        or scope_without_record
    ):
        reasons.extend(runtime_gaps)
        return "受阻", reasons, runtime_gaps
    if qualifying:
        reasons.append("qualifying successful execution evidence exists")
        if runtime_gaps:
            reasons.append("non-qualifying prior attempts are preserved but do not override the qualifying run")
        return "已执行验证", reasons, runtime_gaps
    if runtime_gaps or attempted:
        reasons.extend(runtime_gaps)
        return "受阻", reasons, runtime_gaps

    reasons.append("required materials are present and consistent, but no qualifying execution exists")
    return "材料完整但未执行", reasons, runtime_gaps


def _derive_overall(statuses: list[str]) -> str:
    if "材料冲突" in statuses:
        return "材料冲突"
    if "受阻" in statuses:
        return "受阻"
    if statuses and all(status == "已执行验证" for status in statuses):
        return "已执行验证"
    return "材料完整但未执行"


def _verify_available_source(
    project_dir: Path,
    source: dict[str, Any],
    index: int,
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> None:
    if source.get("availability") != "available":
        return
    fingerprint = source.get("fingerprint")
    if not isinstance(fingerprint, str) or not SHA256_RE.fullmatch(fingerprint):
        errors.append(
            _finding(
                "invalid_source_fingerprint",
                f"sources[{index}].fingerprint",
                "available evidence needs a SHA-256 fingerprint",
            )
        )
        return

    location = str(source.get("location", "")).strip()
    parsed = urlparse(location)
    is_remote = parsed.scheme.lower() in {"http", "https", "ftp", "s3", "gs"}
    is_identifier = bool(re.match(r"^(?:doi:)?10\.\d{4,9}/", location, re.IGNORECASE))
    if is_remote or is_identifier:
        warnings.append(
            _finding(
                "remote_source_not_rehashed",
                f"sources[{index}].location",
                "remote/identifier evidence was not fetched by the local validator; verify its captured local copy separately",
            )
        )
        return

    candidate = Path(location)
    source_path = candidate.resolve() if candidate.is_absolute() else (project_dir / candidate).resolve()
    if not source_path.is_file():
        errors.append(
            _finding(
                "available_source_missing",
                f"sources[{index}].location",
                f"available local source is not a regular file: {location}",
            )
        )
        return
    if _sha256_file(source_path) != _normalise_sha256(fingerprint):
        errors.append(
            _finding(
                "source_fingerprint_mismatch",
                f"sources[{index}].fingerprint",
                f"recorded SHA-256 does not match {location}",
            )
        )


def _validate_scientific_audit(
    analysis: dict[str, Any],
    index: int,
    project_dir: Path,
    sources_by_id: dict[str, dict[str, Any]],
    executions: dict[str, dict[str, Any]],
    errors: list[dict[str, str]],
) -> None:
    evidence_lanes: dict[str, str] = {}
    eligible_lanes: dict[str, str] = {}
    for _, evidence in _evidence_groups(analysis):
        for item in evidence:
            if not isinstance(item, dict):
                continue
            evidence_id = str(item.get("evidence_id", ""))
            lane = str(item.get("lane", ""))
            evidence_lanes[evidence_id] = lane
            source = sources_by_id.get(str(item.get("source_id", "")))
            if item.get("evidence_class") == "直接证据" and _source_material_is_available(
                project_dir, source
            ):
                eligible_lanes[evidence_id] = lane

    for item in analysis.get("code_locations", []):
        if not isinstance(item, dict):
            continue
        evidence_id = str(item.get("evidence_id", ""))
        evidence_lanes[evidence_id] = "code"
        path, path_error = _project_relative_path(project_dir, item.get("path"))
        snapshot = item.get("snapshot")
        source = sources_by_id.get(str(item.get("source_id", "")))
        if (
            item.get("evidence_status") in ACTIVE_CODE_STATUSES
            and not path_error
            and path is not None
            and path.is_file()
            and isinstance(snapshot, str)
            and SHA256_RE.fullmatch(snapshot)
            and _sha256_file(path) == _normalise_sha256(snapshot)
            and _source_material_is_available(project_dir, source)
        ):
            eligible_lanes[evidence_id] = "code"

    for direction, lane in (("inputs", "input"), ("outputs", "output")):
        for artifact in analysis.get("inputs_outputs", {}).get(direction, []):
            if not isinstance(artifact, dict):
                continue
            artifact_id = str(artifact.get("artifact_id", ""))
            evidence_lanes[artifact_id] = lane
            path, path_error = _project_relative_path(project_dir, artifact.get("path"))
            fingerprint = artifact.get("fingerprint")
            if (
                not path_error
                and path is not None
                and path.is_file()
                and isinstance(fingerprint, str)
                and SHA256_RE.fullmatch(fingerprint)
                and _sha256_file(path) == _normalise_sha256(fingerprint)
            ):
                eligible_lanes[artifact_id] = lane

    analysis_id = str(analysis.get("analysis_id", ""))
    for execution_id in analysis.get("execution_record_ids", []):
        execution_text = str(execution_id)
        evidence_lanes[execution_text] = "runtime"
        record = executions.get(execution_text)
        if (
            isinstance(record, dict)
            and analysis_id in record.get("analysis_ids", [])
            and record.get("attempt_status") == "succeeded"
            and record.get("checks")
            and all(
                isinstance(check, dict) and check.get("passed") is True
                for check in record.get("checks", [])
            )
        ):
            eligible_lanes[execution_text] = "runtime"

    required_lanes = {
        "preprocessing": {"method", "code", "input"},
        "statistical_unit": {"method", "input"},
        "replication_pseudoreplication": {"method", "input"},
        "batch_confounding": {"method", "input"},
        "multiple_testing": {"method", "code"},
        "species_gene_ids": {"method", "input"},
        "parameter_consistency": {"method", "code"},
        "claim_strength": {"paper_claim", "figure", "method"},
    }
    items = [item for item in analysis.get("scientific_audit", []) if isinstance(item, dict)]
    observed = [str(item.get("topic", "")) for item in items]
    missing = sorted(CORE_AUDIT_TOPICS - set(observed))
    duplicates = sorted(topic for topic in CORE_AUDIT_TOPICS if observed.count(topic) > 1)
    if missing:
        errors.append(
            _finding(
                "scientific_audit_incomplete",
                f"analyses[{index}].scientific_audit",
                "missing required audit topics: " + ", ".join(missing),
            )
        )
    if duplicates:
        errors.append(
            _finding(
                "scientific_audit_duplicate_topic",
                f"analyses[{index}].scientific_audit",
                "audit topics must appear once: " + ", ".join(duplicates),
            )
        )
    findings = [str(item.get("finding", "")).strip() for item in items if item.get("topic") in CORE_AUDIT_TOPICS]
    duplicate_findings = sorted({finding for finding in findings if finding and findings.count(finding) > 1})
    if duplicate_findings:
        errors.append(
            _finding(
                "scientific_audit_reused_finding",
                f"analyses[{index}].scientific_audit",
                "each required topic needs a topic-specific finding instead of duplicated boilerplate",
            )
        )
    for audit_index, item in enumerate(items):
        if item.get("topic") not in CORE_AUDIT_TOPICS:
            continue
        if len(str(item.get("finding", "")).strip()) < 20:
            errors.append(
                _finding(
                    "scientific_audit_finding_too_short",
                    f"analyses[{index}].scientific_audit[{audit_index}].finding",
                    "finding is too short to record a concrete audit result",
                )
            )
        if not item.get("evidence_refs"):
            errors.append(
                _finding(
                    "scientific_audit_without_evidence",
                    f"analyses[{index}].scientific_audit[{audit_index}].evidence_refs",
                    "every audit topic needs evidence refs showing what was checked",
                )
            )
        cited_lanes = {
            evidence_lanes.get(str(ref), "") for ref in item.get("evidence_refs", [])
        }
        eligible_cited_lanes = {
            eligible_lanes.get(str(ref), "") for ref in item.get("evidence_refs", [])
        }
        expected_lanes = required_lanes.get(str(item.get("topic")), set())
        if item.get("status") in {"passed", "warning"} and not expected_lanes.issubset(cited_lanes):
            errors.append(
                _finding(
                    "scientific_audit_wrong_evidence_lane",
                    f"analyses[{index}].scientific_audit[{audit_index}].evidence_refs",
                    "topic requires evidence lane(s): " + ", ".join(sorted(expected_lanes)),
                )
            )
        elif item.get("status") in {"passed", "warning"} and not expected_lanes.issubset(
            eligible_cited_lanes
        ):
            errors.append(
                _finding(
                    "scientific_audit_unavailable_evidence",
                    f"analyses[{index}].scientific_audit[{audit_index}].evidence_refs",
                    "passed/warning audit requires directly available, fingerprint-consistent evidence in lane(s): "
                    + ", ".join(sorted(expected_lanes)),
                )
            )
        elif item.get("status") in {"blocked", "not_applicable"} and expected_lanes and not (
            expected_lanes & cited_lanes
        ):
            errors.append(
                _finding(
                    "scientific_audit_missing_search_scope",
                    f"analyses[{index}].scientific_audit[{audit_index}].evidence_refs",
                    "blocked/not-applicable audit must cite at least one topic-relevant searched lane",
                )
            )
        if item.get("status") == "passed" and item.get("claim_ceiling") == "not_assessable":
            errors.append(
                _finding(
                    "scientific_audit_inconsistent_pass",
                    f"analyses[{index}].scientific_audit[{audit_index}]",
                    "a passed audit cannot retain a not_assessable claim ceiling",
                )
            )
        claim_ceiling = str(item.get("claim_ceiling", ""))
        if claim_ceiling in UNSUPPORTED_HIGH_CEILINGS:
            errors.append(
                _finding(
                    "unsupported_automatic_high_claim_ceiling",
                    f"analyses[{index}].scientific_audit[{audit_index}].claim_ceiling",
                    "the local validator cannot independently establish causal, mechanistic, "
                    "or measured-flux designs; keep such wording paper-attributed or unverified",
                )
            )


CLI_FLAG_ACTIONS = {
    "store_true",
    "store_false",
    "store_const",
    "append_const",
    "count",
    "help",
    "version",
}


def _python_cli_guidance_contract(
    code_text: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Inventory statically provable Python CLI registrations for minimal-run QA."""

    try:
        tree = ast.parse(code_text)
    except SyntaxError as exc:
        return [], [f"active Python entrypoint cannot be parsed: {exc.msg} at line {exc.lineno}"]
    bindings, unsafe_bindings = _python_module_bindings(tree)
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    potential_aliases = _potential_cli_callable_aliases(tree)
    specs: list[dict[str, Any]] = []
    gaps: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function_name = ""
        if isinstance(node.func, ast.Attribute):
            function_name = node.func.attr
        elif isinstance(node.func, ast.Name):
            function_name = node.func.id
            if function_name in potential_aliases:
                if _default_alias_is_shadowed(node, function_name, parents):
                    gaps.append(
                        f"CLI callable alias {function_name!r} is shadowed at line {node.lineno}"
                    )
                    continue
                resolved, error = _resolve_python_callable_alias(
                    function_name, bindings, unsafe_bindings
                )
                if error:
                    gaps.append(
                        f"CLI callable alias {function_name!r} is unresolved at line "
                        f"{node.lineno}: {error}"
                    )
                    continue
                function_name = str(resolved)
        elif _static_getattr_cli_method(node.func) is not None:
            gaps.append(
                f"getattr-based CLI registration at line {node.lineno} cannot be proven safe"
            )
            continue

        if function_name == "argument":
            gaps.append(
                f"positional Click argument at line {node.lineno} cannot be safely bound by the minimal-run verifier"
            )
            continue
        if function_name not in {"add_argument", "option"}:
            resolved_options: list[str] = []
            dynamic_target = False
            for argument in node.args:
                if isinstance(argument, ast.Starred):
                    dynamic_target = True
                    continue
                resolved, error = _resolve_python_static_cli_string(
                    argument, bindings, unsafe_bindings, node, parents
                )
                if error or resolved is None:
                    dynamic_target = True
                else:
                    resolved_options.append(resolved)
            if (
                any(option.startswith("-") for option in resolved_options)
                and any(keyword.arg in {"default", "required", "dest"} for keyword in node.keywords)
            ) or (dynamic_target and _unresolved_call_is_cli_shaped(node, function_name)):
                gaps.append(
                    f"unresolved CLI-like registration at line {node.lineno} cannot be inventoried"
                )
            continue

        option_names: list[str] = []
        target_errors: list[str] = []
        for argument in node.args:
            if isinstance(argument, ast.Starred):
                target_errors.append("star-expanded option names are dynamic")
                continue
            resolved, error = _resolve_python_static_cli_string(
                argument, bindings, unsafe_bindings, node, parents
            )
            if error or resolved is None:
                target_errors.append(error or "option name is dynamic")
            else:
                option_names.append(resolved)
        dest_nodes = [keyword.value for keyword in node.keywords if keyword.arg == "dest"]
        explicit_dest: str | None = None
        if len(dest_nodes) > 1:
            target_errors.append("duplicate dest keywords")
        elif dest_nodes:
            explicit_dest, error = _resolve_python_static_cli_string(
                dest_nodes[0], bindings, unsafe_bindings, node, parents
            )
            if error or explicit_dest is None:
                target_errors.append(error or "dest is dynamic")
        if target_errors or not option_names:
            gaps.append(
                f"CLI registration at line {node.lineno} cannot be inventoried: "
                + "; ".join(dict.fromkeys(target_errors or ["no option names"]))
            )
            continue

        if explicit_dest is not None:
            parameter_name = explicit_dest
        else:
            long_options = [value for value in option_names if value.startswith("--")]
            selected = (long_options or option_names)[0]
            parameter_name = selected.lstrip("-").replace("-", "_")
        if not _is_ascii_parameter_name(parameter_name):
            gaps.append(
                f"CLI registration at line {node.lineno} has a non-canonical parameter target"
            )
            continue

        required_nodes = [keyword.value for keyword in node.keywords if keyword.arg == "required"]
        positional = not any(value.startswith("-") for value in option_names)
        if positional:
            gaps.append(
                f"positional CLI parameter {parameter_name!r} at line {node.lineno} "
                "cannot be safely bound by the minimal-run verifier"
            )
            continue
        required = positional
        if len(required_nodes) > 1:
            gaps.append(f"CLI registration at line {node.lineno} repeats required")
            continue
        if required_nodes:
            required_value, error = _resolve_python_default(
                required_nodes[0], bindings, unsafe_bindings
            )
            if error or not isinstance(required_value, bool):
                gaps.append(
                    f"CLI required state at line {node.lineno} is not a static boolean"
                )
                continue
            required = required_value

        action = None
        action_nodes = [keyword.value for keyword in node.keywords if keyword.arg == "action"]
        if action_nodes:
            action_value, error = _resolve_python_static_cli_string(
                action_nodes[0], bindings, unsafe_bindings, node, parents
            )
            if error or action_value is None:
                gaps.append(f"CLI action at line {node.lineno} is dynamic")
                continue
            action = action_value

        default_nodes = [keyword.value for keyword in node.keywords if keyword.arg == "default"]
        default_value: Any = _NO_LITERAL
        if len(default_nodes) > 1:
            gaps.append(f"CLI registration at line {node.lineno} repeats default")
            continue
        if default_nodes:
            default_value, error = _resolve_python_default(
                default_nodes[0], bindings, unsafe_bindings
            )
            if error:
                gaps.append(f"CLI default at line {node.lineno} is dynamic: {error}")
                continue

        specs.append(
            {
                "parameter_name": parameter_name,
                "option_names": option_names,
                "required": required,
                "takes_value": action not in CLI_FLAG_ACTIONS,
                "action": action,
                "default": default_value,
                "line": node.lineno,
            }
        )

    names = [str(spec["parameter_name"]).casefold() for spec in specs]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        gaps.append("CLI parameters are registered more than once: " + ", ".join(duplicates))
    return specs, list(dict.fromkeys(gaps))


def _guidance_cli_option_values(
    argv: list[str], entrypoint: str, spec: dict[str, Any]
) -> tuple[list[Any], bool]:
    if entrypoint not in argv:
        return [], True
    arguments = argv[argv.index(entrypoint) + 1 :]
    if "--" in arguments:
        arguments = arguments[: arguments.index("--")]
    option_names = {
        str(value) for value in spec.get("option_names", []) if str(value).startswith("-")
    }
    values: list[Any] = []
    malformed = False
    index = 0
    while index < len(arguments):
        token = arguments[index]
        if (
            token.startswith("--")
            and token not in option_names
            and "=" not in token
            and any(option.startswith(token) for option in option_names)
        ):
            malformed = True
            index += 1
            continue
        inline_match = next(
            (option for option in option_names if token.startswith(option + "=")),
            None,
        )
        if token in option_names:
            if not spec.get("takes_value", True):
                action = spec.get("action")
                values.append(False if action == "store_false" else True)
                index += 1
                continue
            if index + 1 >= len(arguments) or arguments[index + 1] == "--":
                malformed = True
                index += 1
                continue
            raw_value = arguments[index + 1]
            parsed = _parse_simple_literal(raw_value)
            if raw_value.startswith("-") and not (
                parsed is not _NO_LITERAL
                and isinstance(parsed, (int, float))
                and not isinstance(parsed, bool)
            ):
                malformed = True
                index += 1
                continue
            values.append(raw_value if parsed is _NO_LITERAL else parsed)
            index += 2
            continue
        if inline_match is not None:
            raw_value = token[len(inline_match) + 1 :]
            if not raw_value or not spec.get("takes_value", True):
                malformed = True
            else:
                parsed = _parse_simple_literal(raw_value)
                values.append(raw_value if parsed is _NO_LITERAL else parsed)
            index += 1
            continue
        index += 1
    return values, malformed


IMPORT_DISTRIBUTION_ALIASES = {
    "PIL": "pillow",
    "Bio": "biopython",
    "cv2": "opencv-python",
    "skimage": "scikit-image",
    "sklearn": "scikit-learn",
    "umap": "umap-learn",
    "yaml": "pyyaml",
}


def _python_third_party_imports(
    code_text: str, local_top_level_modules: set[str]
) -> tuple[set[str], str | None]:
    try:
        tree = ast.parse(code_text)
    except SyntaxError as exc:
        return set(), f"active Python entrypoint cannot be parsed: {exc.msg} at line {exc.lineno}"
    stdlib = set(getattr(sys, "stdlib_module_names", set())) | {
        "__future__",
        "builtins",
    }
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.add(node.module.split(".", 1)[0])
    third_party: set[str] = set()
    for module in modules:
        if module in stdlib:
            continue
        if module in local_top_level_modules:
            continue
        third_party.add(IMPORT_DISTRIBUTION_ALIASES.get(module, module))
    return third_party, None


def _validate_code_guidance(
    analysis: dict[str, Any],
    task_mode: str,
    index: int,
    project_dir: Path,
    sources_by_id: dict[str, dict[str, Any]],
    errors: list[dict[str, str]],
) -> None:
    guidance = analysis.get("code_guidance")
    path = f"analyses[{index}].code_guidance"
    if guidance is None:
        if task_mode == "code_guidance":
            errors.append(_finding("missing_code_guidance", path, "code_guidance mode requires a guidance record"))
        return
    if not isinstance(guidance, dict):
        errors.append(_finding("invalid_code_guidance", path, "code_guidance must be an object or null"))
        return

    status = guidance.get("status")
    if status not in {"ready", "blocked"}:
        errors.append(
            _finding(
                "invalid_guidance_status",
                f"{path}.status",
                "code_guidance status must be ready or blocked",
            )
        )
    dependencies = guidance.get("dependencies", [])
    unresolved = guidance.get("unresolved_parameters", [])
    blocker_ids = guidance.get("blocker_ids", [])
    minimal_run = guidance.get("minimal_run")
    entrypoint_value = guidance.get("entrypoint")
    configurable_paths = guidance.get("configurable_paths", [])
    inputs = guidance.get("inputs", [])
    outputs = guidance.get("outputs", [])
    unresolved_blocking_issue_ids = {
        str(item.get("issue_id", ""))
        for item in analysis.get("conflicts_gaps", [])
        if isinstance(item, dict)
        and item.get("blocking") is True
        and item.get("resolved") is not True
    }
    unknown_parameters = {
        str(parameter.get("name", ""))
        for parameter in analysis.get("method_parameters", {}).get("parameters", [])
        if isinstance(parameter, dict)
        and (
            parameter.get("value_status") in {"unreported", "inferred"}
            or parameter.get("value") is None
        )
    }

    if status == "ready":
        if guidance.get("provenance") == "pseudocode_only":
            errors.append(
                _finding(
                    "guidance_pseudocode_not_ready",
                    path,
                    "pseudocode_only guidance cannot be marked ready",
                )
            )
        if not isinstance(dependencies, list) or not dependencies:
            errors.append(_finding("guidance_missing_dependencies", path, "ready guidance needs dependencies"))
        else:
            for dependency_error in dependency_contract_errors(dependencies):
                finding_code = (
                    "guidance_unknown_dependency_version"
                    if ".version must be" in dependency_error
                    else "guidance_invalid_dependency_contract"
                )
                errors.append(
                    _finding(
                        finding_code,
                        f"{path}.dependencies",
                        dependency_error,
                    )
                )
        if guidance.get("seed") == "unknown":
            errors.append(_finding("guidance_unknown_seed", path, "ready guidance needs a seed or justified not_applicable"))
        if guidance.get("seed") == "not_applicable" and not str(guidance.get("seed_reason", "")).strip():
            errors.append(_finding("guidance_missing_seed_reason", path, "not_applicable seed needs a reason"))
        if not isinstance(inputs, list) or not inputs or not isinstance(outputs, list) or not outputs:
            errors.append(_finding("guidance_missing_io", path, "ready guidance needs explicit inputs and outputs"))
        if not isinstance(configurable_paths, list) or not configurable_paths:
            errors.append(_finding("guidance_missing_configurable_paths", path, "ready guidance needs configurable paths"))
        if not isinstance(minimal_run, str) or not minimal_run.strip():
            errors.append(_finding("guidance_missing_minimal_run", path, "ready guidance needs a minimal run command"))
        entrypoint, entrypoint_error = _project_relative_path(project_dir, entrypoint_value)
        if entrypoint_error or entrypoint is None or not entrypoint.is_file():
            errors.append(
                _finding(
                    "guidance_entrypoint_unavailable",
                    f"{path}.entrypoint",
                    "ready guidance needs an existing project-relative entrypoint",
                )
            )
        elif isinstance(minimal_run, str) and str(entrypoint_value) not in minimal_run:
            errors.append(
                _finding(
                    "guidance_entrypoint_not_in_command",
                    f"{path}.minimal_run",
                    "minimal_run must name the declared entrypoint",
                )
            )
        guidance_argv: list[str] = []
        if isinstance(minimal_run, str):
            try:
                guidance_argv = shlex.split(minimal_run, posix=os.name != "nt")
            except ValueError:
                guidance_argv = []
            if not _argv_executes_entrypoint(guidance_argv, str(entrypoint_value or "")):
                errors.append(
                    _finding(
                        "guidance_command_does_not_execute_entrypoint",
                        f"{path}.minimal_run",
                        "minimal_run must execute the declared entrypoint with a compatible launcher",
                    )
                )
            guidance_seed_values, guidance_seed_ambiguous = argv_seed_bindings(
                guidance_argv, str(entrypoint_value or "")
            )
            guidance_seed = guidance.get("seed")
            if (
                isinstance(guidance_seed, int)
                and not isinstance(guidance_seed, bool)
                and (
                    guidance_seed_ambiguous
                    or not guidance_seed_values
                    or any(value != str(guidance_seed) for value in guidance_seed_values)
                )
            ):
                errors.append(
                    _finding(
                        "guidance_seed_not_in_command",
                        f"{path}.minimal_run",
                        "minimal_run must bind the declared random seed through an exact canonical long option",
                    )
                )
            if guidance_seed == "not_applicable" and (
                guidance_seed_ambiguous or guidance_seed_values
            ):
                errors.append(
                    _finding(
                        "guidance_seed_not_applicable_conflict",
                        f"{path}.minimal_run",
                        "not_applicable seed conflicts with an explicit or ambiguous seed-like option",
                    )
                )
            absent_flags = [
                str(value)
                for value in configurable_paths
                if str(value).startswith("-") and str(value) not in minimal_run
            ]
            if absent_flags:
                errors.append(
                    _finding(
                        "guidance_configurable_path_not_in_command",
                        f"{path}.minimal_run",
                        "minimal_run omits configurable path flag(s): " + ", ".join(absent_flags),
                    )
                )
        if entrypoint is not None and entrypoint.is_file() and entrypoint.suffix.lower() == ".py":
            code_closure, closure_gaps = python_local_import_closure(
                project_dir, entrypoint
            )
            for gap_index, gap in enumerate(closure_gaps):
                errors.append(
                    _finding(
                        "guidance_code_closure_gap",
                        f"{path}.entrypoint[{gap_index}]",
                        gap,
                    )
                )

            cli_specs: list[dict[str, Any]] = []
            cli_gaps: list[str] = []
            imported_distributions: set[str] = set()
            local_top_level_modules: set[str] = set()
            for code_file in code_closure:
                try:
                    relative_import_path = code_file.relative_to(entrypoint.parent)
                except ValueError:
                    continue
                if not relative_import_path.parts:
                    continue
                top_level = relative_import_path.parts[0]
                local_top_level_modules.add(
                    Path(top_level).stem
                    if len(relative_import_path.parts) == 1
                    else top_level
                )
            for code_index, code_file in enumerate(code_closure):
                matching_code_items: list[dict[str, Any]] = []
                for item in analysis.get("code_locations", []):
                    if (
                        not isinstance(item, dict)
                        or item.get("evidence_status") not in CODE_BUNDLE_STATUSES
                    ):
                        continue
                    item_path, item_error = _project_relative_path(
                        project_dir, item.get("path")
                    )
                    snapshot = item.get("snapshot")
                    source = sources_by_id.get(str(item.get("source_id", "")))
                    if (
                        not item_error
                        and item_path == code_file
                        and isinstance(snapshot, str)
                        and SHA256_RE.fullmatch(snapshot)
                        and _sha256_file(code_file) == _normalise_sha256(snapshot)
                        and _source_material_is_available(project_dir, source)
                    ):
                        matching_code_items.append(item)
                if len(matching_code_items) != 1:
                    errors.append(
                        _finding(
                            "guidance_unbound_local_code",
                            f"{path}.entrypoint[{code_index}]",
                            "every file in the recursive local import closure must have exactly one fingerprint-consistent active code evidence record",
                        )
                    )

                code_text = code_file.read_text(encoding="utf-8", errors="replace")
                file_specs, file_gaps = _python_cli_guidance_contract(code_text)
                cli_specs.extend(file_specs)
                cli_gaps.extend(
                    f"{code_file.relative_to(project_dir).as_posix()}: {gap}"
                    for gap in file_gaps
                )
                file_imports, import_error = _python_third_party_imports(
                    code_text, local_top_level_modules
                )
                imported_distributions.update(file_imports)
                if import_error:
                    errors.append(
                        _finding(
                            "guidance_import_inventory_gap",
                            f"{path}.entrypoint[{code_index}]",
                            import_error,
                        )
                    )
            for gap_index, gap in enumerate(cli_gaps):
                errors.append(
                    _finding(
                        "guidance_cli_inventory_gap",
                        f"{path}.entrypoint[{gap_index}]",
                        gap,
                    )
                )

            parameter_values: dict[str, list[Any]] = {}
            for parameter in analysis.get("method_parameters", {}).get("parameters", []):
                if not isinstance(parameter, dict):
                    continue
                if parameter.get("value_status") not in {
                    "reported",
                    "implemented",
                    "observed_runtime",
                } or parameter.get("value") is None:
                    continue
                parameter_values.setdefault(
                    str(parameter.get("name", "")).casefold(), []
                ).append(parameter.get("value"))

            for spec in cli_specs:
                values, malformed = _guidance_cli_option_values(
                    guidance_argv, str(entrypoint_value or ""), spec
                )
                parameter_name = str(spec.get("parameter_name", ""))
                spec_path = f"{path}.minimal_run"
                if malformed:
                    errors.append(
                        _finding(
                            "guidance_cli_argument_malformed",
                            spec_path,
                            f"CLI argument for {parameter_name!r} is malformed or ambiguous",
                        )
                    )
                if spec.get("required") is True and not values:
                    errors.append(
                        _finding(
                            "guidance_required_cli_argument_missing",
                            spec_path,
                            f"minimal_run omits required CLI parameter {parameter_name!r}",
                        )
                    )
                if len(values) > 1:
                    errors.append(
                        _finding(
                            "guidance_cli_argument_repeated",
                            spec_path,
                            f"minimal_run supplies CLI parameter {parameter_name!r} more than once",
                        )
                    )
                expected_values = parameter_values.get(parameter_name.casefold(), [])
                unique_expected: list[Any] = []
                for expected_value in expected_values:
                    if not any(
                        _strict_json_equal(expected_value, existing)
                        for existing in unique_expected
                    ):
                        unique_expected.append(expected_value)
                if values and len(unique_expected) > 1:
                    errors.append(
                        _finding(
                            "guidance_parameter_material_conflict",
                            spec_path,
                            f"materials contain conflicting values for CLI parameter {parameter_name!r}",
                        )
                    )
                elif values and len(unique_expected) == 1 and any(
                    not _strict_json_equal(value, unique_expected[0]) for value in values
                ):
                    errors.append(
                        _finding(
                            "guidance_parameter_value_mismatch",
                            spec_path,
                            f"minimal_run value for {parameter_name!r} conflicts with the recorded method/code value",
                        )
                    )

            dependency_names = {
                normalized_dependency_name(str(item.get("name", "")))
                for item in dependencies
                if isinstance(item, dict)
            }
            missing_imports = sorted(
                name
                for name in imported_distributions
                if normalized_dependency_name(name) not in dependency_names
            )
            if missing_imports:
                errors.append(
                    _finding(
                        "guidance_missing_import_dependencies",
                        f"{path}.dependencies",
                        "ready guidance omits imported third-party dependencies: "
                        + ", ".join(missing_imports),
                    )
                )
        elif entrypoint is not None and entrypoint.is_file():
            errors.append(
                _finding(
                    "guidance_cli_inventory_gap",
                    f"{path}.entrypoint",
                    "ready guidance requires a language-specific CLI inventory; this validator only performs the strict static inventory for Python entrypoints",
                )
            )
        if unresolved:
            errors.append(_finding("guidance_has_unresolved_parameters", path, "ready guidance cannot hide unresolved parameters"))
        if blocker_ids:
            errors.append(_finding("guidance_has_blockers", path, "ready guidance cannot retain blocker ids"))
        if unknown_parameters:
            errors.append(
                _finding(
                    "guidance_unresolved_method_parameters",
                    path,
                    "ready guidance cannot fill unreported/inferred method parameters: "
                    + ", ".join(sorted(unknown_parameters)),
                )
            )
    elif status == "blocked":
        if not unresolved or not blocker_ids:
            errors.append(
                _finding(
                    "blocked_guidance_without_gap",
                    path,
                    "blocked guidance must name unresolved parameters and blocker ids instead of fabricating values",
                )
            )
        missing_unknowns = unknown_parameters - {str(value) for value in unresolved or []}
        if missing_unknowns:
            errors.append(
                _finding(
                    "guidance_missing_unresolved_parameters",
                    path,
                    "blocked guidance must name every unreported/inferred parameter: "
                    + ", ".join(sorted(missing_unknowns)),
                )
            )

    for blocker_id in blocker_ids if isinstance(blocker_ids, list) else []:
        if str(blocker_id) not in unresolved_blocking_issue_ids:
            errors.append(
                _finding(
                    "unknown_guidance_blocker",
                    f"{path}.blocker_ids",
                    f"{blocker_id} is not an unresolved blocking issue",
                )
            )

    expected_io = analysis.get("inputs_outputs", {})
    if inputs != expected_io.get("inputs", []):
        errors.append(
            _finding(
                "guidance_input_contract_mismatch",
                f"{path}.inputs",
                "guidance inputs must exactly preserve analysis artifact ids, paths, semantics, and fingerprints",
            )
        )
    if outputs != expected_io.get("outputs", []):
        errors.append(
            _finding(
                "guidance_output_contract_mismatch",
                f"{path}.outputs",
                "guidance outputs must exactly preserve analysis artifact ids, paths, semantics, and fingerprints",
            )
        )

    strings_to_check = (
        [str(minimal_run or ""), str(entrypoint_value or "")]
        + [str(value) for value in configurable_paths or []]
        + [
            str(item.get("path", ""))
            for collection in (inputs, outputs)
            for item in collection
            if isinstance(item, dict)
        ]
    )
    if any(
        ABSOLUTE_WINDOWS_PATH_RE.search(value)
        or ABSOLUTE_POSIX_PATH_RE.search(value)
        or Path(value).is_absolute()
        or CONCRETE_URL_RE.search(value)
        or FIXED_PORT_RE.search(value)
        or FIXED_ENDPOINT_RE.search(value)
        or FIXED_LISTEN_PORT_RE.search(value)
        or SECRET_ARGUMENT_RE.search(value)
        for value in strings_to_check
        if value
    ):
        errors.append(
            _finding(
                "guidance_hardcoded_environment",
                path,
                "guidance cannot contain absolute machine paths, concrete endpoints/ports, or credential arguments",
            )
        )


def _require_trace_tokens(
    row: dict[str, str],
    column: str,
    tokens: Iterable[Any],
    row_index: int,
    errors: list[dict[str, str]],
) -> None:
    cell = str(row.get(column, ""))
    missing = [
        str(token)
        for token in tokens
        if token is not None and str(token) and str(token) not in cell
    ]
    if missing:
        errors.append(
            _finding(
                "trace_lane_mismatch",
                f"traceability.tsv:line {row_index}:{column}",
                "missing manifest link token(s): " + ", ".join(missing),
            )
        )


def _validate_trace_row_content(
    row: dict[str, str],
    analysis: dict[str, Any],
    row_index: int,
    errors: list[dict[str, str]],
) -> None:
    paper_evidence = analysis.get("paper_claim", {}).get("evidence", [])
    figure_evidence = analysis.get("figure_panel", {}).get("evidence", [])
    method_evidence = analysis.get("method_parameters", {}).get("evidence", [])
    _require_trace_tokens(
        row,
        "正文主张",
        [analysis.get("paper_claim", {}).get("summary")]
        + [value for item in paper_evidence if isinstance(item, dict) for value in (item.get("evidence_id"), item.get("locator"))],
        row_index,
        errors,
    )
    _require_trace_tokens(
        row,
        "figure/panel",
        [analysis.get("figure_panel", {}).get("display_summary")]
        + list(analysis.get("figure_panel", {}).get("ids", []))
        + [value for item in figure_evidence if isinstance(item, dict) for value in (item.get("evidence_id"), item.get("locator"))],
        row_index,
        errors,
    )
    parameter_tokens: list[Any] = []
    for parameter in analysis.get("method_parameters", {}).get("parameters", []):
        if isinstance(parameter, dict):
            parameter_tokens.extend(
                [
                    parameter.get("name"),
                    parameter.get("value"),
                    parameter.get("value_status"),
                    parameter.get("implementation_literal"),
                    parameter.get("inference_rationale"),
                ]
            )
            parameter_tokens.extend(parameter.get("evidence_refs", []))
            parameter_tokens.extend(parameter.get("execution_record_refs", []))
    _require_trace_tokens(
        row,
        "method与参数",
        [analysis.get("method_parameters", {}).get("summary")]
        + [value for item in method_evidence if isinstance(item, dict) for value in (item.get("evidence_id"), item.get("locator"))]
        + parameter_tokens,
        row_index,
        errors,
    )

    code_locations = [item for item in analysis.get("code_locations", []) if isinstance(item, dict)]
    if code_locations:
        _require_trace_tokens(
            row,
            "code位置",
            [
                value
                for item in code_locations
                for value in (
                    item.get("evidence_id"),
                    item.get("snapshot"),
                    item.get("path"),
                    item.get("locator"),
                    item.get("scope"),
                    item.get("evidence_status"),
                )
            ],
            row_index,
            errors,
        )
    elif not any(marker in str(row.get("code位置", "")).lower() for marker in MISSING_CODE_MARKERS):
        errors.append(
            _finding(
                "trace_missing_code_marker",
                f"traceability.tsv:line {row_index}:code位置",
                "an analysis without code evidence needs an explicit missing-code marker",
            )
        )

    io_tokens: list[Any] = []
    for direction in ("inputs", "outputs"):
        for artifact in analysis.get("inputs_outputs", {}).get(direction, []):
            if isinstance(artifact, dict):
                io_tokens.extend(
                    [
                        artifact.get("artifact_id"),
                        artifact.get("path"),
                        artifact.get("semantic_type"),
                        artifact.get("fingerprint") if artifact.get("fingerprint") else "fingerprint=missing",
                    ]
                )
    _require_trace_tokens(row, "输入/输出", io_tokens, row_index, errors)

    issue_tokens: list[Any] = []
    for issue in analysis.get("conflicts_gaps", []):
        if isinstance(issue, dict):
            issue_tokens.extend([issue.get("issue_id"), issue.get("description"), issue.get("impact")])
            issue_tokens.extend(issue.get("evidence_refs", []))
            if issue.get("resolved"):
                issue_tokens.extend(issue.get("resolution_evidence_refs", []))
    _require_trace_tokens(row, "冲突或缺口", issue_tokens, row_index, errors)


CLAIM_CEILING_RANK = {
    "not_assessable": 0,
    "descriptive": 1,
    "association": 2,
    "prediction": 2,
    "temporal_ordering": 3,
    "perturbation_supported": 4,
    "causal": 5,
    "mechanistic": 6,
    "measured_flux": 7,
}


def _analysis_claim_ceiling(analysis: dict[str, Any]) -> str:
    audit_items = [
        item for item in analysis.get("scientific_audit", []) if isinstance(item, dict)
    ]
    if any(item.get("status") == "blocked" for item in audit_items):
        return "not_assessable"
    return min(
        (str(item.get("claim_ceiling", "not_assessable")) for item in audit_items),
        key=lambda value: CLAIM_CEILING_RANK.get(value, 0),
        default="not_assessable",
    )


def _assertion_is_attributed(clause: str, assertion_start: int) -> bool:
    prefix = clause[:assertion_start]
    attributed = list(ATTRIBUTED_CLAIM_RE.finditer(prefix))
    if not attributed:
        return False
    self_assertions = list(SELF_ASSERTION_RE.finditer(prefix))
    last_attribution = attributed[-1].start()
    last_self_assertion = self_assertions[-1].start() if self_assertions else -1
    last_reset = max(
        (match.start() for match in ATTRIBUTION_RESET_RE.finditer(prefix)),
        default=-1,
    )
    return last_attribution > max(last_self_assertion, last_reset)


def _clause_asserts(
    clause: str,
    pattern: re.Pattern[str],
    *,
    allow_attributed_claims: bool,
) -> bool:
    for match in pattern.finditer(clause):
        prefix = clause[: match.start()]
        if NEGATION_BEFORE_COMPLETION_RE.search(prefix):
            continue
        if (
            pattern in {CAUSAL_RE, MECHANISM_RE}
            and OPERATIONAL_PREDICATE_RE.search(match.group(0))
            and OPERATIONAL_SUBJECT_BEFORE_ASSERTION_RE.search(prefix)
        ):
            continue
        uncertainty_matches = list(UNCERTAINTY_BEFORE_ASSERTION_RE.finditer(prefix))
        if uncertainty_matches:
            last_uncertainty = uncertainty_matches[-1].start()
            last_reset = max(
                (reset.start() for reset in ATTRIBUTION_RESET_RE.finditer(prefix)),
                default=-1,
            )
            if last_uncertainty > last_reset:
                continue
        if allow_attributed_claims and _assertion_is_attributed(clause, match.start()):
            continue
        return True
    return False


def _validate_claim_text(
    text: str,
    ceiling: str,
    path: str,
    errors: list[dict[str, str]],
    *,
    allow_attributed_claims: bool,
) -> None:
    clauses = [value.strip() for value in re.split(r"(?<=[。！？.!?;；])|\n", text) if value.strip()]
    for clause_index, clause in enumerate(clauses, start=1):
        clause_path = f"{path}:clause {clause_index}"
        if _clause_asserts(
            clause, FLUX_RE, allow_attributed_claims=allow_attributed_claims
        ) and ceiling != "measured_flux":
            errors.append(
                _finding(
                    "claim_exceeds_flux_evidence",
                    clause_path,
                    "true/measured flux language requires a measured_flux claim ceiling",
                )
            )
        if _clause_asserts(
            clause, MECHANISM_RE, allow_attributed_claims=allow_attributed_claims
        ) and ceiling != "mechanistic":
            errors.append(
                _finding(
                    "claim_exceeds_mechanistic_evidence",
                    clause_path,
                    "mechanistic language exceeds the recorded claim-strength ceiling",
                )
            )
        if _clause_asserts(
            clause, CAUSAL_RE, allow_attributed_claims=allow_attributed_claims
        ) and ceiling not in {"causal", "mechanistic"}:
            errors.append(
                _finding(
                    "claim_exceeds_causal_evidence",
                    clause_path,
                    "causal language exceeds the recorded claim-strength ceiling",
                )
            )


def _validate_interpretation_consistency(
    analysis: dict[str, Any],
    derived_status: str,
    index: int,
    errors: list[dict[str, str]],
) -> None:
    interpretation = analysis.get("interpretation", {})
    def statement_texts(key: str) -> list[str]:
        return [
            str(value.get("statement", ""))
            for value in interpretation.get(key, [])
            if isinstance(value, dict)
        ]

    support = "\n".join(statement_texts("reconstructed_support"))
    unverified = "\n".join(statement_texts("unverified"))
    has_active_code = any(
        isinstance(item, dict) and item.get("evidence_status") in ACTIVE_CODE_STATUSES
        for item in analysis.get("code_locations", [])
    )
    unresolved_conflict = any(
        isinstance(item, dict) and item.get("kind") == "conflict" and not item.get("resolved", False)
        for item in analysis.get("conflicts_gaps", [])
    )
    if not has_active_code and re.search(r"(?:active\s+code.*align|代码.*一致)", support, re.IGNORECASE):
        errors.append(
            _finding(
                "interpretation_code_contradiction",
                f"analyses[{index}].interpretation.reconstructed_support",
                "interpretation claims code alignment although no active code evidence exists",
            )
        )
    if unresolved_conflict and re.search(r"(?:\balign(?:ed)?\b|一致|无冲突)", support, re.IGNORECASE):
        errors.append(
            _finding(
                "interpretation_conflict_contradiction",
                f"analyses[{index}].interpretation.reconstructed_support",
                "interpretation claims alignment while an unresolved conflict is preserved",
            )
        )
    if derived_status == "已执行验证" and re.search(
        r"(?:no\s+(?:analysis\s+)?command\s+was\s+executed|未(?:实际)?执行|没有(?:实际)?运行)",
        unverified,
        re.IGNORECASE,
    ):
        errors.append(
            _finding(
                "interpretation_execution_contradiction",
                f"analyses[{index}].interpretation.unverified",
                "interpretation denies execution despite a qualifying runtime record",
            )
        )

    claim_text = "\n".join(
        str(value.get("statement", ""))
        for key in ("direct_observation", "reconstructed_support", "reasonable_inference")
        for value in interpretation.get(key, [])
        if isinstance(value, dict)
    )
    _validate_claim_text(
        claim_text,
        _analysis_claim_ceiling(analysis),
        f"analyses[{index}].interpretation",
        errors,
        allow_attributed_claims=False,
    )


def _statement_has_unstructured_quantity(text: Any) -> bool:
    cleaned = NONQUANTITATIVE_IDENTIFIER_RE.sub("", str(text or ""))
    cleaned = NONQUANTITATIVE_BIOMEDICAL_IDENTIFIER_RE.sub("", cleaned)
    cleaned = NONQUANTITATIVE_DOMAIN_TERM_RE.sub("", cleaned)
    return bool(
        NUMERIC_TOKEN_RE.search(cleaned)
        or ENGLISH_QUANTITY_WORD_RE.search(cleaned)
        or CHINESE_QUANTITY_WORD_RE.search(cleaned)
    )


def _quantitative_claim_text(claim: dict[str, Any]) -> str:
    binding = claim.get("binding", {})
    kind = str(binding.get("kind", "")) if isinstance(binding, dict) else ""
    if kind == "result_check":
        binding_text = (
            f"result_check:{binding.get('execution_id', '')}/{binding.get('check_id', '')}"
        )
    elif kind == "source_excerpt":
        binding_text = (
            f"source_excerpt:{binding.get('source_id', '')}@{binding.get('locator', '')}"
        )
    elif kind == "parameter":
        binding_text = f"parameter:{binding.get('name', '')}@{binding.get('value_status', '')}"
    else:
        binding_text = kind or "unknown"
    try:
        value_text = json.dumps(
            claim.get("value"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError):
        value_text = "null"
    return (
        f"{claim.get('metric', '')}={value_text} {claim.get('unit', '')} "
        f"[evidence: {claim.get('evidence_ref', '')}; binding: {binding_text}]"
    )


def _normalise_metric_text(value: Any) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[_-]+", " ", str(value or ""))).strip().casefold()


def _metric_occurs_as_term(metric: Any, excerpt: Any) -> bool:
    raw_metric = str(metric or "").strip()
    if not raw_metric:
        return False
    parts = [part for part in re.split(r"[\s_-]+", raw_metric) if part]
    if not parts:
        return False
    pattern = r"(?<![\w])" + r"[\s_-]+".join(re.escape(part) for part in parts) + r"(?![\w])"
    return re.search(pattern, str(excerpt or ""), re.IGNORECASE) is not None


def _metric_term_pattern(metric: Any) -> re.Pattern[str] | None:
    raw_metric = str(metric or "").strip()
    if not raw_metric:
        return None
    parts = [part for part in re.split(r"[\s_-]+", raw_metric) if part]
    if not parts:
        return None
    return re.compile(
        r"(?<![\w])" + r"[\s_-]+".join(re.escape(part) for part in parts) + r"(?![\w])",
        re.IGNORECASE,
    )


SOURCE_NUMBER_BODY = r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?"
SOURCE_NUMBER_TOKEN_RE = re.compile(
    rf"(?<![\w.])(?P<number>{SOURCE_NUMBER_BODY})(?![\w.])",
    re.ASCII,
)
SOURCE_SCIENTIFIC_POWER_RE = re.compile(
    rf"(?<![\w.])"
    rf"(?:(?P<coefficient>{SOURCE_NUMBER_BODY})\s*(?:\*|\u00d7)\s*)?"
    r"10\s*\^\s*(?P<exponent>[+\-]?\d+)"
    r"(?![\w.])",
    re.ASCII,
)
SOURCE_UNSUPPORTED_COMPOSITE_NUMBER_RES = (
    re.compile(r"(?<![\w.])-?\d+(?:,\d+)+(?![\w.,])", re.ASCII),
    re.compile(
        r"(?<![\w.])-?\d{1,3}(?:[ \u00a0\u202f]\d{3})+(?![\w.\d])",
        re.ASCII,
    ),
    re.compile(
        rf"(?<![\w.]){SOURCE_NUMBER_BODY}\s*"
        rf"(?:-|\u2013|\u2014|/|:|\u00b1)\s*{SOURCE_NUMBER_BODY}(?![\w.])",
        re.ASCII,
    ),
    re.compile(
        rf"(?<![\w.]){SOURCE_NUMBER_BODY}\s*(?:\*|\u00d7|\^)\s*"
        rf"{SOURCE_NUMBER_BODY}(?![\w.])",
        re.ASCII,
    ),
)
NUMERIC_LIKE_STRING_RE = re.compile(
    r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$",
    re.ASCII,
)
JSON_STRING_TOKEN_RE = re.compile(r'"(?:\\.|[^"\\])*"')
PERCENT_UNITS = {"%", "％", "percent", "percentage", "pct", "per cent"}
SOURCE_PERCENT_UNIT_RE = re.compile(
    r"^\s*(?P<unit>%|\uFF05|percent(?:age)?\b|pct\b|per\s+cent\b)",
    re.IGNORECASE,
)
SOURCE_UNIT_ATOM_BODY = r"(?:[^\W\d_]|\u00b0)+"
SOURCE_UNIT_EXPONENT = (
    r"(?:\^?\s*[+\-\u2212]?\d+|[\u207a\u207b]?[\u2070\u00b9\u00b2\u00b3\u2074-\u2079]+)"
)
SOURCE_UNIT_ATOM = rf"(?:{SOURCE_UNIT_ATOM_BODY}(?:{SOURCE_UNIT_EXPONENT})?)"
SOURCE_UNIT_NEGATIVE_EXPONENT = (
    r"(?:\^?\s*[\-\u2212]\d+|\u207b[\u2070\u00b9\u00b2\u00b3\u2074-\u2079]+)"
)
SOURCE_UNIT_INVERSE_ATOM = (
    rf"(?:{SOURCE_UNIT_ATOM_BODY}{SOURCE_UNIT_NEGATIVE_EXPONENT})"
)
SOURCE_UNIT_EXPRESSION_RE = re.compile(
    rf"^\s*(?P<unit>{SOURCE_UNIT_ATOM}"
    rf"(?:"
    rf"\s*(?:/|\u00b7|\u22c5|\*|\u00d7)\s*{SOURCE_UNIT_ATOM}"
    rf"|\s+per\s+{SOURCE_UNIT_ATOM}"
    rf"|\s+{SOURCE_UNIT_INVERSE_ATOM}"
    rf")*)"
    r"(?![\w\u00b0])",
    re.IGNORECASE,
)
SOURCE_NON_UNIT_NARRATIVE_STARTS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "because",
    "been",
    "being",
    "but",
    "can",
    "could",
    "did",
    "do",
    "does",
    "for",
    "from",
    "had",
    "has",
    "have",
    "if",
    "in",
    "indicated",
    "indicates",
    "is",
    "may",
    "might",
    "must",
    "of",
    "on",
    "or",
    "produced",
    "produces",
    "reported",
    "reports",
    "respectively",
    "represented",
    "represents",
    "should",
    "showed",
    "shows",
    "suggested",
    "suggests",
    "than",
    "that",
    "the",
    "then",
    "to",
    "used",
    "uses",
    "was",
    "were",
    "when",
    "where",
    "which",
    "while",
    "will",
    "with",
    "would",
    "yielded",
    "yields",
}


def _spans_overlap(left: tuple[int, int], right: tuple[int, int]) -> bool:
    return left[0] < right[1] and right[0] < left[1]


def _source_excerpt_numeric_tokens(
    text: str,
) -> list[tuple[tuple[int, int], Decimal, bool]]:
    """Return complete supported numeric tokens and hide unsafe composites.

    Power-of-ten scientific expressions are evaluated as one value. Other
    composite representations stay unavailable rather than exposing a leading
    coefficient, range endpoint, ratio member, or uncertainty component.
    """

    unsafe_spans = [
        match.span()
        for pattern in SOURCE_UNSUPPORTED_COMPOSITE_NUMBER_RES
        for match in pattern.finditer(text)
    ]
    scientific_matches = list(SOURCE_SCIENTIFIC_POWER_RE.finditer(text))
    protected_spans = unsafe_spans + [match.span() for match in scientific_matches]
    tokens: list[tuple[tuple[int, int], Decimal, bool]] = []

    for match in scientific_matches:
        span = match.span()
        # A supported expression embedded in a larger unsupported composite
        # (for example, a range) remains fail-closed.
        if any(
            _spans_overlap(span, unsafe_span)
            and (unsafe_span[0] < span[0] or unsafe_span[1] > span[1])
            for unsafe_span in unsafe_spans
        ):
            continue
        coefficient_token = match.group("coefficient") or "1"
        try:
            exponent = int(match.group("exponent"))
            if abs(exponent) > 10_000:
                continue
            coefficient = Decimal(coefficient_token)
            observed = coefficient.scaleb(exponent)
        except (InvalidOperation, OverflowError, ValueError):
            continue
        token_is_float = (
            "." in coefficient_token
            or "e" in coefficient_token.casefold()
            or exponent < 0
            or observed != observed.to_integral_value()
        )
        if observed.is_finite():
            tokens.append((span, observed, token_is_float))

    for match in SOURCE_NUMBER_TOKEN_RE.finditer(text):
        span = match.span("number")
        if any(_spans_overlap(span, protected) for protected in protected_spans):
            continue
        token = match.group("number")
        try:
            observed = Decimal(token)
        except InvalidOperation:
            continue
        token_is_float = "." in token or "e" in token.casefold()
        if observed.is_finite():
            tokens.append((span, observed, token_is_float))

    return sorted(tokens, key=lambda item: item[0])


def _source_excerpt_matching_number_spans(
    value: Any, text: str
) -> list[tuple[int, int]]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return []
    try:
        expected = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return []
    if not expected.is_finite():
        return []
    spans: list[tuple[int, int]] = []
    for span, observed, token_is_float in _source_excerpt_numeric_tokens(text):
        if isinstance(value, int) and token_is_float:
            continue
        if isinstance(value, float) and not token_is_float:
            continue
        if observed.is_finite() and observed == expected:
            spans.append(span)
    return spans


def _source_excerpt_has_strict_value(value: Any, excerpt: Any) -> bool:
    """Match one complete typed value token, never a numeric substring."""

    text = str(excerpt or "")
    if isinstance(value, bool) or value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(_source_excerpt_matching_number_spans(value, text))
    if not isinstance(value, str) or not value:
        return False

    # Numeric-looking strings are distinct from numeric source tokens. They
    # match only an explicitly quoted JSON string, preventing "0", "5", or
    # "05" from borrowing characters from a source number such as 0.05.
    for match in JSON_STRING_TOKEN_RE.finditer(text):
        try:
            decoded = json.loads(match.group(0))
        except (json.JSONDecodeError, ValueError):
            continue
        if type(decoded) is str and decoded == value:
            return True
    if NUMERIC_LIKE_STRING_RE.fullmatch(value):
        return False

    pattern = r"(?<![\w])" + re.escape(value) + r"(?![\w])"
    return re.search(pattern, text, re.IGNORECASE) is not None


def _source_excerpt_matching_value_spans(
    value: Any, text: str
) -> list[tuple[int, int]]:
    if isinstance(value, bool) or value is None:
        return []
    if isinstance(value, (int, float)):
        return _source_excerpt_matching_number_spans(value, text)
    if not isinstance(value, str) or not value:
        return []

    quoted_spans: list[tuple[int, int]] = []
    for match in JSON_STRING_TOKEN_RE.finditer(text):
        try:
            decoded = json.loads(match.group(0))
        except (json.JSONDecodeError, ValueError):
            continue
        if type(decoded) is str and decoded == value:
            quoted_spans.append(match.span())
    if NUMERIC_LIKE_STRING_RE.fullmatch(value):
        return quoted_spans

    pattern = re.compile(r"(?<![\w])" + re.escape(value) + r"(?![\w])", re.IGNORECASE)
    return quoted_spans + [match.span() for match in pattern.finditer(text)]


SOURCE_METRIC_VALUE_CONNECTOR_RE = re.compile(
    r"(?:\s*(?:=|:)\s*|\s+(?:(?:is|was|of|at)\s+)?)",
    re.IGNORECASE,
)


def _source_excerpt_metric_value_relations(
    metric: Any, value: Any, excerpt: Any
) -> list[tuple[int, int]]:
    """Return value spans that are directly attached to the named metric."""

    text = str(excerpt or "")
    metric_pattern = _metric_term_pattern(metric)
    if metric_pattern is None:
        return []
    value_spans = _source_excerpt_matching_value_spans(value, text)
    relations: list[tuple[int, int]] = []
    for metric_match in metric_pattern.finditer(text):
        for value_span in value_spans:
            if value_span[0] < metric_match.end():
                continue
            connector = text[metric_match.end() : value_span[0]]
            if SOURCE_METRIC_VALUE_CONNECTOR_RE.fullmatch(connector):
                relations.append(value_span)
    return sorted(set(relations))


def _source_excerpt_metric_numeric_relations(
    metric: Any, excerpt: Any
) -> list[tuple[tuple[int, int], Decimal]]:
    """Return every complete numeric value directly attached to one metric."""

    text = str(excerpt or "")
    metric_pattern = _metric_term_pattern(metric)
    if metric_pattern is None:
        return []
    numeric_tokens = _source_excerpt_numeric_tokens(text)
    relations: set[tuple[tuple[int, int], Decimal]] = set()
    for metric_match in metric_pattern.finditer(text):
        for value_span, observed, _token_is_float in numeric_tokens:
            if value_span[0] < metric_match.end():
                continue
            connector = text[metric_match.end() : value_span[0]]
            if SOURCE_METRIC_VALUE_CONNECTOR_RE.fullmatch(connector):
                relations.add((value_span, observed))
    return sorted(relations, key=lambda item: item[0])


def _normalise_source_unit_token(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    text = re.sub(r"\s*([/\u00b7\u22c5*\u00d7^])\s*", r"\1", text)
    return text.casefold()


def _source_unit_candidate_is_explicit(candidate: str) -> bool:
    normalized = _normalise_source_unit_token(candidate)
    if normalized in PERCENT_UNITS:
        return True
    if re.search(
        r"[/\u00b7\u22c5*\u00d7^\u2070\u00b9\u00b2\u00b3\u2074-\u2079]",
        candidate,
    ):
        return True
    if re.search(r"[+\-\u2212]\d+$", candidate):
        return True
    # A word immediately after a number is treated conservatively as a unit
    # unless it is a controlled grammatical continuation. This keeps unknown
    # domain units fail-closed without mistaking "5 was used" for a unit.
    return normalized not in SOURCE_NON_UNIT_NARRATIVE_STARTS


def _source_excerpt_leading_unit(suffix: str) -> tuple[str | None, bool]:
    candidate_text = suffix.lstrip()
    closing_delimiter: str | None = None
    if candidate_text.startswith("("):
        candidate_text = candidate_text[1:].lstrip()
        closing_delimiter = ")"
    elif candidate_text.startswith("["):
        candidate_text = candidate_text[1:].lstrip()
        closing_delimiter = "]"
    elif candidate_text.startswith(","):
        candidate_text = candidate_text[1:].lstrip()

    percent_match = SOURCE_PERCENT_UNIT_RE.match(candidate_text)
    if percent_match:
        if closing_delimiter and not re.match(
            rf"^\s*{re.escape(closing_delimiter)}",
            candidate_text[percent_match.end() :],
        ):
            return None, False
        return percent_match.group("unit"), True
    unit_match = SOURCE_UNIT_EXPRESSION_RE.match(candidate_text)
    if not unit_match:
        return None, False
    if closing_delimiter and not re.match(
        rf"^\s*{re.escape(closing_delimiter)}",
        candidate_text[unit_match.end() :],
    ):
        return None, False
    candidate = unit_match.group("unit")
    return candidate, _source_unit_candidate_is_explicit(candidate)


def _source_excerpt_unit_matches_span(
    excerpt: Any, value_span: tuple[int, int], unit: Any
) -> bool:
    text = str(excerpt or "")
    raw_unit = str(unit or "").strip()
    normalized_unit = _normalise_source_unit_token(raw_unit)
    suffix = text[value_span[1] :]
    source_unit, source_unit_is_explicit = _source_excerpt_leading_unit(suffix)
    if source_unit is None:
        return normalized_unit in {"dimensionless", "not_recorded"}
    normalized_source_unit = _normalise_source_unit_token(source_unit)
    if normalized_source_unit in PERCENT_UNITS:
        return normalized_unit in PERCENT_UNITS
    if normalized_unit in PERCENT_UNITS:
        return False
    if not source_unit_is_explicit:
        return normalized_unit in {"dimensionless", "not_recorded"}
    if normalized_unit in {"dimensionless", "not_recorded"}:
        return False
    return normalized_unit == normalized_source_unit


def _source_excerpt_unit_matches(value: Any, excerpt: Any, unit: Any) -> bool:
    text = str(excerpt or "")
    raw_unit = str(unit or "").strip()
    normalized_unit = re.sub(r"\s+", " ", raw_unit).casefold()
    spans = _source_excerpt_matching_number_spans(value, text)
    if spans:
        if len(spans) != 1:
            return False
        return _source_excerpt_unit_matches_span(text, spans[0], raw_unit)
    if normalized_unit in {"dimensionless", "not_recorded"}:
        return True
    return _metric_occurs_as_term(raw_unit, text)


def _source_text_at_locator(source_text: str, locator: Any) -> tuple[str | None, str | None]:
    """Resolve machine-checkable one-based line locators without guessing."""

    text = str(locator or "").strip()
    matches = list(
        re.finditer(
            r"(?<![A-Za-z0-9])L(?:ines?\s*)?(\d+)(?:\s*[-–]\s*L?(\d+))?(?![A-Za-z0-9])",
            text,
            re.IGNORECASE | re.ASCII,
        )
    )
    if len(matches) != 1:
        return None, "locator must contain exactly one machine-readable L<n> or L<n>-L<m> range"
    start = int(matches[0].group(1))
    end = int(matches[0].group(2) or start)
    lines = source_text.splitlines()
    if start < 1 or end < start or end > len(lines):
        return None, "locator line range is outside the fingerprinted source"
    return "\n".join(lines[start - 1 : end]), None


def _validate_quantitative_claims(
    *,
    analysis: dict[str, Any],
    category: str,
    statement: dict[str, Any],
    statement_path: str,
    refs: set[str],
    project_dir: Path,
    sources_by_id: dict[str, dict[str, Any]],
    executions: dict[str, dict[str, Any]],
    execution_scope: str,
    execution_requested: bool,
    allowed_direct_quantitative_refs: set[str] | None,
    errors: list[dict[str, str]],
) -> None:
    """Resolve quantitative claims to one exact source, parameter, or result check.

    Free prose is intentionally qualitative. Values are rendered only from these
    structured objects, which prevents an unrelated seed, exit code, parameter,
    or number elsewhere in a cited file from satisfying a result claim.
    """

    if _statement_has_unstructured_quantity(statement.get("statement", "")):
        errors.append(
            _finding(
                "interpretation_quantity_must_be_structured",
                f"{statement_path}.statement",
                "free interpretation prose must not contain numeric tokens or quantity words; "
                "record exact quantities only in quantitative_claims",
            )
        )

    claims = statement.get("quantitative_claims")
    if not isinstance(claims, list):
        errors.append(
            _finding(
                "interpretation_quantitative_claims_missing",
                f"{statement_path}.quantitative_claims",
                "every interpretation statement requires a quantitative_claims array",
            )
        )
        return

    evidence_by_id: dict[str, dict[str, Any]] = {}
    for _, evidence_items in _evidence_groups(analysis):
        for item in evidence_items:
            if isinstance(item, dict):
                evidence_by_id[str(item.get("evidence_id", ""))] = item

    parameters = [
        item
        for item in analysis.get("method_parameters", {}).get("parameters", [])
        if isinstance(item, dict)
    ]
    analysis_id = str(analysis.get("analysis_id", ""))
    linked_execution_ids = {str(value) for value in analysis.get("execution_record_ids", [])}

    for claim_index, claim in enumerate(claims):
        claim_path = f"{statement_path}.quantitative_claims[{claim_index}]"
        if not isinstance(claim, dict):
            errors.append(
                _finding(
                    "quantitative_claim_not_structured",
                    claim_path,
                    "quantitative claim must be an object with a typed binding",
                )
            )
            continue
        evidence_ref = str(claim.get("evidence_ref", ""))
        metric = str(claim.get("metric", "")).strip()
        unit = str(claim.get("unit", "")).strip()
        if evidence_ref not in refs:
            errors.append(
                _finding(
                    "quantitative_claim_evidence_not_cited",
                    f"{claim_path}.evidence_ref",
                    "quantitative evidence_ref must also appear in the statement evidence_refs",
                )
            )
        if (
            allowed_direct_quantitative_refs is not None
            and evidence_ref not in allowed_direct_quantitative_refs
        ):
            errors.append(
                _finding(
                    "quantitative_claim_evidence_not_directly_available",
                    f"{claim_path}.evidence_ref",
                    (
                        "direct/reconstructed quantitative evidence_ref must itself identify "
                        "fingerprint-consistent direct material, not inferred or unverifiable evidence"
                    ),
                )
            )
        binding = claim.get("binding")
        if not isinstance(binding, dict):
            errors.append(
                _finding(
                    "quantitative_claim_binding_missing",
                    f"{claim_path}.binding",
                    "quantitative claim requires one typed binding",
                )
            )
            continue
        kind = binding.get("kind")

        if kind == "result_check":
            if category not in {"direct_observation", "reconstructed_support"}:
                errors.append(
                    _finding(
                        "result_check_binding_wrong_interpretation_lane",
                        claim_path,
                        "result-check quantities belong only in direct_observation or reconstructed_support",
                    )
                )
            execution_id = str(binding.get("execution_id", ""))
            check_id = str(binding.get("check_id", ""))
            record = executions.get(execution_id)
            if execution_id not in linked_execution_ids or not isinstance(record, dict):
                errors.append(
                    _finding(
                        "quantitative_result_execution_unlinked",
                        f"{claim_path}.binding.execution_id",
                        "result-check binding must name a linked execution record",
                    )
                )
                continue
            matching_checks = [
                check
                for check in record.get("checks", [])
                if isinstance(check, dict) and str(check.get("check_id", "")) == check_id
            ]
            if len(matching_checks) != 1:
                errors.append(
                    _finding(
                        "quantitative_result_check_not_unique",
                        f"{claim_path}.binding.check_id",
                        "check_id must resolve to exactly one check in the execution record",
                    )
                )
                continue
            check = matching_checks[0]
            qualifying, gaps = _execution_is_qualifying(
                record,
                project_dir,
                execution_scope,
                execution_requested,
                analysis,
            )
            if not qualifying or check.get("passed") is not True or analysis_id not in check.get(
                "analysis_ids", []
            ):
                errors.append(
                    _finding(
                        "quantitative_result_check_not_qualifying",
                        claim_path,
                        "result-check binding requires a passed qualifying check for this analysis"
                        + (": " + "; ".join(gaps) if gaps else ""),
                    )
                )
            if metric != str(check.get("metric", "")):
                errors.append(
                    _finding(
                        "quantitative_result_metric_mismatch",
                        f"{claim_path}.metric",
                        "claim metric must exactly equal the bound check metric",
                    )
                )
            if unit != str(check.get("unit", "")):
                errors.append(
                    _finding(
                        "quantitative_result_unit_mismatch",
                        f"{claim_path}.unit",
                        "claim unit must exactly equal the bound check unit",
                    )
                )
            if not _strict_json_equal(claim.get("value"), check.get("observed")):
                errors.append(
                    _finding(
                        "quantitative_result_value_mismatch",
                        f"{claim_path}.value",
                        "claim value must be strictly JSON-equal to the bound check observed value",
                    )
                )
            verification = check.get("verification")
            if not isinstance(verification, dict) or verification.get("kind") not in {
                "tsv_cell_equals",
                "json_pointer_equals",
            }:
                errors.append(
                    _finding(
                        "quantitative_result_selector_required",
                        f"{claim_path}.binding",
                        "quantitative result claims require a selector-based TSV or JSON check",
                    )
                )
                continue
            verification_path = str(verification.get("evidence_path", ""))
            output_matches = [
                artifact
                for artifact in record.get("outputs", [])
                if isinstance(artifact, dict)
                and str(artifact.get("artifact_id", "")) == evidence_ref
                and str(artifact.get("path", "")) == verification_path
                and analysis_id in artifact.get("analysis_ids", [])
            ]
            if len(output_matches) != 1:
                errors.append(
                    _finding(
                        "quantitative_result_output_unbound",
                        f"{claim_path}.evidence_ref",
                        "evidence_ref must identify exactly one analysis-owned output selected by the check",
                    )
                )
            if verification_path not in check.get("evidence_paths", []):
                errors.append(
                    _finding(
                        "quantitative_result_path_not_cited",
                        f"{claim_path}.binding",
                        "the selected output path must be present in the bound check evidence_paths",
                    )
                )
            if verification.get("kind") == "tsv_cell_equals":
                selector = verification.get("selector")
                if not isinstance(selector, dict) or metric != str(selector.get("key_value", "")):
                    errors.append(
                        _finding(
                            "quantitative_result_metric_selector_mismatch",
                            f"{claim_path}.metric",
                            "TSV-bound metric must exactly equal selector.key_value",
                        )
                    )
            elif metric != str(verification.get("selector", "")):
                errors.append(
                    _finding(
                        "quantitative_result_metric_selector_mismatch",
                        f"{claim_path}.metric",
                        "JSON-bound metric must exactly equal the RFC6901 selector",
                    )
                )

        elif kind == "source_excerpt":
            evidence = evidence_by_id.get(evidence_ref)
            if not isinstance(evidence, dict):
                errors.append(
                    _finding(
                        "quantitative_source_evidence_unlinked",
                        f"{claim_path}.evidence_ref",
                        "source_excerpt must identify a structured evidence item in this analysis",
                    )
                )
                continue
            source_id = str(binding.get("source_id", ""))
            locator = str(binding.get("locator", ""))
            excerpt = str(binding.get("exact_excerpt", ""))
            if source_id != str(evidence.get("source_id", "")) or locator != str(
                evidence.get("locator", "")
            ):
                errors.append(
                    _finding(
                        "quantitative_source_locator_mismatch",
                        f"{claim_path}.binding",
                        "source_id and locator must exactly match the cited evidence item",
                    )
                )
            source = sources_by_id.get(source_id)
            source_path, source_error = _project_relative_path(
                project_dir, source.get("location") if isinstance(source, dict) else None
            )
            source_text = (
                _read_bounded_utf8_text(source_path)
                if not source_error and source_path is not None and source_path.is_file()
                else None
            )
            locator_text: str | None = None
            locator_error: str | None = "source text is unavailable"
            if source_text is not None:
                locator_text, locator_error = _source_text_at_locator(source_text, locator)
            if locator_error:
                errors.append(
                    _finding(
                        "quantitative_source_locator_unresolvable",
                        f"{claim_path}.binding.locator",
                        locator_error,
                    )
                )
            if (
                not _source_material_is_available(project_dir, source)
                or source_text is None
                or locator_text is None
                or not excerpt
                or excerpt not in locator_text
            ):
                errors.append(
                    _finding(
                        "quantitative_source_excerpt_not_found",
                        f"{claim_path}.binding.exact_excerpt",
                        "exact_excerpt must occur verbatim inside the cited line locator of the fingerprint-consistent source",
                    )
                )
            value = claim.get("value")
            if not _source_excerpt_has_strict_value(value, excerpt):
                errors.append(
                    _finding(
                        "quantitative_source_value_absent",
                        f"{claim_path}.value",
                        "the claim value must match one complete, type-consistent value token in exact_excerpt",
                    )
                )
            if not _metric_occurs_as_term(metric, excerpt):
                errors.append(
                    _finding(
                        "quantitative_source_metric_absent",
                        f"{claim_path}.metric",
                        "the claim metric must occur in exact_excerpt",
                    )
                )
            metric_value_relations = _source_excerpt_metric_value_relations(
                metric, value, excerpt
            )
            metric_numeric_relations = (
                _source_excerpt_metric_numeric_relations(metric, excerpt)
                if isinstance(value, (int, float)) and not isinstance(value, bool)
                else []
            )
            distinct_metric_values = {
                observed for _span, observed in metric_numeric_relations
            }
            metric_values_conflict = len(distinct_metric_values) > 1
            if metric_values_conflict:
                errors.append(
                    _finding(
                        "quantitative_source_metric_values_conflict",
                        f"{claim_path}.binding.exact_excerpt",
                        "selected metric has multiple different normalized values in exact_excerpt; preserve the conflict instead of cherry-picking one",
                    )
                )
            elif not metric_value_relations:
                errors.append(
                    _finding(
                        "quantitative_source_metric_value_unbound",
                        f"{claim_path}.binding.exact_excerpt",
                        "exact_excerpt must directly bind the selected metric to the claim value",
                    )
                )
            else:
                unit_spans = (
                    [span for span, _observed in metric_numeric_relations]
                    if metric_numeric_relations
                    else metric_value_relations
                )
                unit_matches = all(
                    _source_excerpt_unit_matches_span(excerpt, span, unit)
                    for span in unit_spans
                )
                if not unit_matches:
                    errors.append(
                        _finding(
                            "quantitative_source_unit_absent",
                            f"{claim_path}.unit",
                            "unit must match every duplicate value-adjacent source unit; use dimensionless/not_recorded only when none is present",
                        )
                    )

        elif kind == "parameter":
            name = str(binding.get("name", ""))
            value_status = str(binding.get("value_status", ""))
            matches = [
                parameter
                for parameter in parameters
                if str(parameter.get("name", "")).lower() == name.lower()
                and str(parameter.get("value_status", "")) == value_status
            ]
            if len(matches) != 1:
                errors.append(
                    _finding(
                        "quantitative_parameter_not_unique",
                        f"{claim_path}.binding",
                        "parameter binding must resolve to exactly one name/value_status record",
                    )
                )
                continue
            parameter = matches[0]
            if metric.lower() != name.lower():
                errors.append(
                    _finding(
                        "quantitative_parameter_metric_mismatch",
                        f"{claim_path}.metric",
                        "parameter-bound metric must equal the parameter name",
                    )
                )
            if not _strict_json_equal(claim.get("value"), parameter.get("value")):
                errors.append(
                    _finding(
                        "quantitative_parameter_value_mismatch",
                        f"{claim_path}.value",
                        "parameter-bound value must be strictly JSON-equal to the structured parameter value",
                    )
                )
            expected_unit = str(parameter.get("unit", "not_recorded"))
            if unit != expected_unit:
                errors.append(
                    _finding(
                        "quantitative_parameter_unit_mismatch",
                        f"{claim_path}.unit",
                        "parameter-bound unit must equal the structured parameter unit; use not_recorded when absent",
                    )
                )
            if evidence_ref not in {str(value) for value in parameter.get("evidence_refs", [])}:
                errors.append(
                    _finding(
                        "quantitative_parameter_evidence_mismatch",
                        f"{claim_path}.evidence_ref",
                        "parameter-bound evidence_ref must be one of that parameter's evidence refs",
                    )
                )
            if category in {"direct_observation", "reconstructed_support"} and value_status == "observed_runtime":
                errors.append(
                    _finding(
                        "runtime_quantity_requires_result_check",
                        claim_path,
                        "runtime values in direct/reconstructed interpretation require result_check binding",
                    )
                )
            if value_status == "inferred" and category not in {
                "reasonable_inference",
                "unverified",
            }:
                errors.append(
                    _finding(
                        "inferred_parameter_wrong_interpretation_lane",
                        claim_path,
                        "inferred parameter values may appear only in reasonable_inference or unverified",
                    )
                )
        else:
            errors.append(
                _finding(
                    "quantitative_claim_binding_unknown",
                    f"{claim_path}.binding.kind",
                    "binding kind must be result_check, source_excerpt, or parameter",
                )
            )


REPORT_SECTIONS = (
    ("## Direct evidence/observation", "direct_observation"),
    ("## Paper claim", "paper_claim"),
    ("## Reconstructed support", "reconstructed_support"),
    ("## Reasonable inference", "reasonable_inference"),
    ("## Unverified", "unverified"),
)


def _report_statement_line(analysis_id: str, statement: dict[str, Any]) -> str:
    references = ", ".join(str(value) for value in statement.get("evidence_refs", []))
    quantitative = statement.get("quantitative_claims", [])
    quantitative_text = ""
    if isinstance(quantitative, list) and quantitative:
        quantitative_text = " [quantitative: " + " | ".join(
            _quantitative_claim_text(claim)
            for claim in quantitative
            if isinstance(claim, dict)
        ) + "]"
    return (
        f"- {analysis_id}: {statement.get('statement', '')}{quantitative_text} "
        f"[evidence: {references}]"
    )


def _validate_manifest_derived_report(
    report_text: str,
    analyses_by_id: dict[str, dict[str, Any]],
    derived_statuses: dict[str, dict[str, Any]],
    errors: list[dict[str, str]],
) -> None:
    """Reject free-standing claims and require manifest-derived report lines."""

    expected_lines = ["# Reconstruction report", "## Status"]
    for analysis_id, analysis in analyses_by_id.items():
        derived = str(derived_statuses.get(analysis_id, {}).get("derived", ""))
        expected_lines.append(f"- {analysis_id}: {derived}")
    for heading, key in REPORT_SECTIONS:
        expected_lines.append(heading)
        section_lines: list[str] = []
        for analysis_id, analysis in analyses_by_id.items():
            interpretation = analysis.get("interpretation", {})
            if isinstance(interpretation, dict):
                for statement in interpretation.get(key, []):
                    if not isinstance(statement, dict):
                        continue
                    section_lines.append(_report_statement_line(analysis_id, statement))
        expected_lines.extend(section_lines or ["- none"])
    expected_lines.append("## Conflicts or gaps")
    issue_lines: list[str] = []
    for analysis_id, analysis in analyses_by_id.items():
        for issue in analysis.get("conflicts_gaps", []):
            if not isinstance(issue, dict):
                continue
            references = ", ".join(str(value) for value in issue.get("evidence_refs", []))
            issue_lines.append(
                f"- {analysis_id}/{issue.get('issue_id', '')} ({issue.get('kind', '')}): "
                f"{issue.get('description', '')} [evidence: {references}]"
            )
    expected_lines.extend(issue_lines or ["- none"])

    actual_lines: list[str] = []
    allowed_lines = set(expected_lines)
    for line_number, raw_line in enumerate(report_text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        actual_lines.append(line)
        if line not in allowed_lines:
            errors.append(
                _finding(
                    "report_unstructured_claim",
                    f"REPORT.md:line {line_number}",
                    "report content must be rendered verbatim from structured manifest statuses, "
                    "interpretations, or conflicts/gaps",
                )
            )
    for line in sorted(set(expected_lines) - set(actual_lines)):
        errors.append(
            _finding(
                "report_missing_manifest_line",
                "REPORT.md",
                f"report is missing required manifest-derived line: {line}",
            )
        )
    if actual_lines != expected_lines:
        errors.append(
            _finding(
                "report_not_canonical",
                "REPORT.md",
                "nonempty report lines must exactly follow the documented manifest-derived order, "
                "including '- none' for each empty section",
            )
        )


def validate_project(project_dir: Path, write_report: bool = False) -> dict[str, Any]:
    project_dir = project_dir.resolve()
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    manifest_path = project_dir / "reconstruction_manifest.json"
    trace_path = project_dir / "traceability.tsv"
    inventory_path = project_dir / "source_inventory.json"
    state_path = project_dir / "working_state.json"
    report_path = project_dir / "REPORT.md"
    schema_path = Path(__file__).resolve().parents[1] / "schemas" / "reconstruction_manifest.schema.json"

    manifest = _read_json(manifest_path, errors)
    inventory = _read_json(inventory_path, errors)
    working_state = _read_json(state_path, errors)
    _, trace_rows = _read_trace_table(trace_path, errors)

    report_text: str | None = None
    if not report_path.is_file():
        errors.append(_finding("missing_file", "REPORT.md", "required file is missing: REPORT.md"))
    else:
        try:
            report_text = report_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            errors.append(_finding("invalid_encoding", "REPORT.md", f"file is not UTF-8: {exc}"))
        else:
            if len(report_text.strip()) < 40:
                errors.append(
                    _finding(
                        "report_too_short",
                        "REPORT.md",
                        "human-readable report must contain a substantive manifest-derived summary",
                    )
                )

    schema_status = _schema_validate(manifest, schema_path, errors, warnings)
    derived_statuses: dict[str, dict[str, Any]] = {}
    derived_overall = "受阻"

    if isinstance(manifest, dict):
        task = manifest.get("task", {}) if isinstance(manifest.get("task"), dict) else {}
        task_mode = str(task.get("mode", ""))
        execution_scope = str(task.get("execution_scope", "none"))
        execution_requested = task.get("execution_requested") is True
        source_ids: list[str] = []
        for index, source in enumerate(manifest.get("sources", [])):
            if isinstance(source, dict):
                source_id = str(source.get("source_id", ""))
                source_ids.append(source_id)
                if source.get("availability") == "available" and not source.get("fingerprint"):
                    errors.append(
                        _finding(
                            "missing_source_fingerprint",
                            f"sources[{index}].fingerprint",
                            "available local/retrieved evidence needs a stable fingerprint",
                        )
                    )
                _verify_available_source(project_dir, source, index, errors, warnings)
        if len(source_ids) != len(set(source_ids)):
            errors.append(_finding("duplicate_source_id", "sources", "source_id values must be unique"))
        source_id_set = set(source_ids)
        sources_by_id = {
            str(source.get("source_id", "")): source
            for source in manifest.get("sources", [])
            if isinstance(source, dict)
        }

        inventory_ids: set[str] = set()
        if isinstance(inventory, dict):
            if inventory.get("schema_version") != "1.0.0":
                errors.append(
                    _finding(
                        "inventory_schema_version",
                        "source_inventory.json.schema_version",
                        "expected 1.0.0",
                    )
                )
            if inventory.get("project_id") != manifest.get("project_id"):
                errors.append(
                    _finding(
                        "inventory_project_mismatch",
                        "source_inventory.json.project_id",
                        "project_id must match reconstruction_manifest.json",
                    )
                )
            for source in inventory.get("sources", []):
                if isinstance(source, dict):
                    inventory_ids.add(str(source.get("source_id", "")))
            if inventory_ids != source_id_set:
                errors.append(
                    _finding(
                        "inventory_manifest_mismatch",
                        "source_inventory.json",
                        "source ids must exactly match reconstruction_manifest.json sources",
                    )
                )
            inventory_by_id = {
                str(source.get("source_id", "")): source
                for source in inventory.get("sources", [])
                if isinstance(source, dict)
            }
            manifest_by_id = {
                str(source.get("source_id", "")): source
                for source in manifest.get("sources", [])
                if isinstance(source, dict)
            }
            if inventory_by_id != manifest_by_id:
                errors.append(
                    _finding(
                        "inventory_manifest_content_mismatch",
                        "source_inventory.json.sources",
                        "inventory source records must exactly match the manifest, not only share ids",
                    )
                )

        stages = manifest.get("stage_state", [])
        observed_stage_order = [item.get("stage") for item in stages if isinstance(item, dict)]
        if observed_stage_order != STAGE_ORDER:
            errors.append(
                _finding(
                    "stage_order_mismatch",
                    "stage_state",
                    f"expected exact stage order {STAGE_ORDER!r}, observed {observed_stage_order!r}",
                )
            )
        for index in range(min(5, len(stages))):
            current = stages[index] if isinstance(stages[index], dict) else {}
            if current.get("status") in {"in_progress", "completed", "partial", "blocked"}:
                prior = stages[:index]
                if any(
                    not isinstance(item, dict) or item.get("status") != "completed"
                    for item in prior
                ):
                    errors.append(
                        _finding(
                            "stage_dependency_violation",
                            f"stage_state[{index}]",
                            "a scientific stage cannot start until every prior scientific gate is completed",
                        )
                    )

        if isinstance(working_state, dict):
            required_state_fields = {
                "schema_version",
                "project_id",
                "input_fingerprint",
                "stages",
                "completed_artifacts",
                "invalidations",
                "blockers",
            }
            missing_state_fields = sorted(required_state_fields - set(working_state))
            if missing_state_fields:
                errors.append(
                    _finding(
                        "working_state_incomplete",
                        "working_state.json",
                        "missing fields: " + ", ".join(missing_state_fields),
                    )
                )
            if working_state.get("schema_version") != "1.0.0":
                errors.append(_finding("working_state_schema_version", "working_state.json", "expected 1.0.0"))
            if working_state.get("project_id") != manifest.get("project_id"):
                errors.append(
                    _finding(
                        "working_state_project_mismatch",
                        "working_state.json.project_id",
                        "project_id must match reconstruction_manifest.json",
                    )
                )
            expected_input_fingerprint = _source_set_fingerprint(manifest.get("sources", []))
            if working_state.get("input_fingerprint") != expected_input_fingerprint:
                errors.append(
                    _finding(
                        "working_state_input_mismatch",
                        "working_state.json.input_fingerprint",
                        "input fingerprint must reflect the current source set",
                    )
                )
            state_stages = working_state.get("stages", [])
            if state_stages != stages:
                errors.append(
                    _finding(
                        "working_state_mismatch",
                        "working_state.json",
                        "working_state stages must match manifest stage_state",
                    )
                )
            required_completed_artifacts = {
                "source_inventory.json",
                "working_state.json",
                "reconstruction_manifest.json",
                "traceability.tsv",
                "REPORT.md",
            }
            completed_artifacts = working_state.get("completed_artifacts", [])
            if not isinstance(completed_artifacts, list) or not required_completed_artifacts.issubset(
                {str(value) for value in completed_artifacts}
            ):
                errors.append(
                    _finding(
                        "working_state_artifacts_incomplete",
                        "working_state.json.completed_artifacts",
                        "state must list every durable project artifact produced before validation",
                    )
                )
            if not isinstance(working_state.get("invalidations"), list):
                errors.append(
                    _finding(
                        "working_state_invalidations",
                        "working_state.json.invalidations",
                        "invalidations must be an explicit list, even when empty",
                    )
                )
            expected_blockers = sorted(
                {
                    str(blocker)
                    for stage in stages
                    if isinstance(stage, dict)
                    for blocker in stage.get("blockers", [])
                }
            )
            observed_blockers = working_state.get("blockers", [])
            if not isinstance(observed_blockers, list) or sorted(str(value) for value in observed_blockers) != expected_blockers:
                errors.append(
                    _finding(
                        "working_state_blocker_mismatch",
                        "working_state.json.blockers",
                        "top-level blockers must equal the stage blocker union",
                    )
                )

        execution_records = manifest.get("execution_records", [])
        if execution_records and execution_scope == "none":
            errors.append(
                _finding(
                    "execution_scope_violation",
                    "task.execution_scope",
                    "runtime records require execute_now or audit_supplied_record scope",
                )
            )
        if execution_scope == "execute_now" and not execution_requested:
            errors.append(
                _finding(
                    "execution_authorization_missing",
                    "task.execution_requested",
                    "execute_now requires explicit execution_requested=true",
                )
            )
        if execution_scope == "audit_supplied_record" and execution_requested:
            errors.append(
                _finding(
                    "execution_authorization_inconsistent",
                    "task.execution_requested",
                    "auditing supplied runtime evidence must not authorize a new run",
                )
            )
        executions: dict[str, dict[str, Any]] = {}
        for index, record in enumerate(execution_records):
            if not isinstance(record, dict):
                continue
            execution_id = str(record.get("execution_id", ""))
            if not ID_RE.fullmatch(execution_id):
                errors.append(
                    _finding(
                        "invalid_execution_id",
                        f"execution_records[{index}].execution_id",
                        "execution id must match ^[A-Za-z][A-Za-z0-9_.-]*$",
                    )
                )
            if execution_id in executions:
                errors.append(
                    _finding(
                        "duplicate_execution_id",
                        f"execution_records[{index}].execution_id",
                        execution_id,
                    )
                )
            executions[execution_id] = record

        analyses = manifest.get("analyses", [])
        analysis_ids: list[str] = []
        all_evidence_ids: set[str] = set()
        all_artifact_reference_ids: set[str] = set()
        evidence_refs_to_check: list[tuple[str, str]] = []
        resolved_issue_checks: list[tuple[str, dict[str, Any]]] = []
        analysis_execution_refs: dict[str, set[str]] = {}
        analyses_by_id: dict[str, dict[str, Any]] = {}

        for index, analysis in enumerate(analyses):
            if not isinstance(analysis, dict):
                continue
            analysis_id = str(analysis.get("analysis_id", ""))
            analysis_ids.append(analysis_id)
            analyses_by_id[analysis_id] = analysis
            analysis_execution_refs[analysis_id] = {
                str(value) for value in analysis.get("execution_record_ids", [])
            }
            artifact_ids_seen: set[str] = set()
            artifact_paths_seen: dict[Path, tuple[str, str]] = {}
            for direction in ("inputs", "outputs"):
                for artifact_index, artifact in enumerate(
                    analysis.get("inputs_outputs", {}).get(direction, [])
                ):
                    if not isinstance(artifact, dict):
                        continue
                    artifact_id = str(artifact.get("artifact_id", ""))
                    if artifact_id:
                        all_artifact_reference_ids.add(artifact_id)
                    if artifact_id in artifact_ids_seen:
                        errors.append(
                            _finding(
                                "duplicate_analysis_artifact_id",
                                f"analyses[{index}].inputs_outputs.{direction}[{artifact_index}].artifact_id",
                                artifact_id,
                            )
                        )
                    artifact_ids_seen.add(artifact_id)
                    artifact_path, artifact_path_error = _project_relative_path(
                        project_dir, artifact.get("path")
                    )
                    if not artifact_path_error and artifact_path is not None:
                        previous = artifact_paths_seen.get(artifact_path)
                        if previous is not None:
                            errors.append(
                                _finding(
                                    "duplicate_analysis_artifact_path",
                                    f"analyses[{index}].inputs_outputs.{direction}[{artifact_index}].path",
                                    (
                                        f"physical path is already declared by {previous[0]} "
                                        f"artifact {previous[1]}; logical artifacts must have unique paths"
                                    ),
                                )
                            )
                        else:
                            artifact_paths_seen[artifact_path] = (direction, artifact_id)
            _validate_scientific_audit(
                analysis,
                index,
                project_dir,
                sources_by_id,
                executions,
                errors,
            )
            guidance_error_start = len(errors)
            _validate_code_guidance(
                analysis, task_mode, index, project_dir, sources_by_id, errors
            )
            guidance = analysis.get("code_guidance")
            guidance_blocking_codes = (
                {
                    str(finding.get("code", ""))
                    for finding in errors[guidance_error_start:]
                    if str(finding.get("code", ""))
                }
                if task_mode == "code_guidance"
                or (isinstance(guidance, dict) and guidance.get("status") == "ready")
                else set()
            )

            for group_name, evidence_items in _evidence_groups(analysis):
                for evidence_index, item in enumerate(evidence_items):
                    if not isinstance(item, dict):
                        continue
                    evidence_id = str(item.get("evidence_id", ""))
                    if evidence_id in all_evidence_ids:
                        errors.append(
                            _finding(
                                "duplicate_evidence_id",
                                f"analyses[{index}].{group_name}.evidence[{evidence_index}]",
                                evidence_id,
                            )
                        )
                    all_evidence_ids.add(evidence_id)
                    if item.get("source_id") not in source_id_set:
                        errors.append(
                            _finding(
                                "unknown_source_ref",
                                f"analyses[{index}].{group_name}.evidence[{evidence_index}].source_id",
                                str(item.get("source_id")),
                            )
                        )
                    if item.get("lane") != EVIDENCE_GROUP_LANES.get(group_name):
                        errors.append(
                            _finding(
                                "evidence_lane_mismatch",
                                f"analyses[{index}].{group_name}.evidence[{evidence_index}].lane",
                                f"{group_name} evidence must use lane {EVIDENCE_GROUP_LANES.get(group_name)!r}",
                            )
                        )
                    source_record = sources_by_id.get(str(item.get("source_id", "")))
                    source_roles = set(source_record.get("roles", [])) if isinstance(source_record, dict) else set()
                    if source_record is not None and not (
                        source_roles & EVIDENCE_GROUP_ROLES.get(group_name, set())
                    ):
                        errors.append(
                            _finding(
                                "evidence_source_role_mismatch",
                                f"analyses[{index}].{group_name}.evidence[{evidence_index}].source_id",
                                f"source roles do not support the {group_name} evidence lane",
                            )
                        )
                    if item.get("evidence_class") == "直接证据" and not _source_material_is_available(
                        project_dir, source_record
                    ):
                        errors.append(
                            _finding(
                                "direct_evidence_source_unavailable",
                                f"analyses[{index}].{group_name}.evidence[{evidence_index}].source_id",
                                "direct evidence requires an available, fingerprint-consistent source",
                            )
                        )
                    if item.get("evidence_class") == "合理推断" and not str(
                        item.get("inference_rationale", "")
                    ).strip():
                        errors.append(
                            _finding(
                                "missing_inference_rationale",
                                f"analyses[{index}].{group_name}.evidence[{evidence_index}]",
                                "reasonable inference needs an explicit rationale",
                            )
                        )

            code_items_by_evidence: dict[str, dict[str, Any]] = {}
            for code_index, code_item in enumerate(analysis.get("code_locations", [])):
                if not isinstance(code_item, dict):
                    continue
                evidence_id = str(code_item.get("evidence_id", ""))
                code_items_by_evidence[evidence_id] = code_item
                if evidence_id in all_evidence_ids:
                    errors.append(
                        _finding(
                            "duplicate_evidence_id",
                            f"analyses[{index}].code_locations[{code_index}]",
                            evidence_id,
                        )
                    )
                all_evidence_ids.add(evidence_id)
                if code_item.get("source_id") not in source_id_set:
                    errors.append(
                        _finding(
                            "unknown_source_ref",
                            f"analyses[{index}].code_locations[{code_index}].source_id",
                                str(code_item.get("source_id")),
                            )
                        )
                code_source = sources_by_id.get(str(code_item.get("source_id", "")))
                if isinstance(code_source, dict) and not (
                    set(code_source.get("roles", [])) & CODE_SOURCE_ROLES
                ):
                    errors.append(
                        _finding(
                            "code_source_role_mismatch",
                            f"analyses[{index}].code_locations[{code_index}].source_id",
                            "code locations must cite a source with code or environment role",
                        )
                    )
                if code_item.get("evidence_status") in CODE_BUNDLE_STATUSES:
                    code_path, code_path_error = _project_relative_path(project_dir, code_item.get("path"))
                    if code_path_error:
                        errors.append(
                            _finding(
                                "active_code_path_invalid",
                                f"analyses[{index}].code_locations[{code_index}].path",
                                code_path_error,
                            )
                        )
                    elif code_path is None or not code_path.is_file():
                        errors.append(
                            _finding(
                                "active_code_path_missing",
                                f"analyses[{index}].code_locations[{code_index}].path",
                                "active code evidence must resolve to a regular file",
                            )
                        )
                    else:
                        snapshot = code_item.get("snapshot")
                        if not isinstance(snapshot, str) or not SHA256_RE.fullmatch(snapshot):
                            errors.append(
                                _finding(
                                    "active_code_snapshot_invalid",
                                    f"analyses[{index}].code_locations[{code_index}].snapshot",
                                    "active code needs a SHA-256 snapshot",
                                )
                            )
                        elif _sha256_file(code_path) != _normalise_sha256(snapshot):
                            errors.append(
                                _finding(
                                    "active_code_snapshot_mismatch",
                                    f"analyses[{index}].code_locations[{code_index}].snapshot",
                                    "code file does not match its recorded snapshot",
                                )
                            )
                    source_record = sources_by_id.get(str(code_item.get("source_id", "")))
                    if isinstance(source_record, dict) and source_record.get("availability") != "available":
                        errors.append(
                            _finding(
                                "active_code_source_unavailable",
                                f"analyses[{index}].code_locations[{code_index}].source_id",
                                "active code cannot cite a missing or unreadable source",
                            )
                        )
                    if isinstance(source_record, dict) and code_path is not None and code_path.is_file():
                        source_location = str(source_record.get("location", "")).strip()
                        parsed_source = urlparse(source_location)
                        if parsed_source.scheme.lower() in {"http", "https", "ftp", "s3", "gs"}:
                            source_path = None
                        else:
                            source_candidate = Path(source_location)
                            source_path = (
                                source_candidate.resolve()
                                if source_candidate.is_absolute()
                                else (project_dir / source_candidate).resolve()
                            )
                        if source_path != code_path:
                            errors.append(
                                _finding(
                                    "active_code_source_path_mismatch",
                                    f"analyses[{index}].code_locations[{code_index}].source_id",
                                    "active code source location must identify the same local file as code_locations.path",
                                )
                            )

            for parameter_index, parameter in enumerate(
                analysis.get("method_parameters", {}).get("parameters", [])
            ):
                if isinstance(parameter, dict):
                    if not _is_ascii_parameter_name(parameter.get("name")):
                        errors.append(
                            _finding(
                                "parameter_name_not_ascii",
                                f"analyses[{index}].method_parameters.parameters[{parameter_index}].name",
                                "parameter names must match ^[A-Za-z][A-Za-z0-9_.-]*$ using ASCII only",
                            )
                        )
                    parameter_refs = [str(ref) for ref in parameter.get("evidence_refs", [])]
                    method_evidence_ids = {
                        str(item.get("evidence_id", ""))
                        for item in analysis.get("method_parameters", {}).get("evidence", [])
                        if isinstance(item, dict)
                    }
                    if not parameter_refs:
                        errors.append(
                            _finding(
                                "parameter_without_evidence_scope",
                                f"analyses[{index}].method_parameters.parameters[{parameter_index}]",
                                "every parameter needs evidence refs, including an explicit unreported finding",
                            )
                        )
                    value_status = str(parameter.get("value_status", ""))
                    if value_status in {"reported", "unreported"} and not (
                        set(parameter_refs) & method_evidence_ids
                    ):
                        errors.append(
                            _finding(
                                "method_parameter_without_method_evidence",
                                f"analyses[{index}].method_parameters.parameters[{parameter_index}]",
                                f"{value_status} parameter status requires a Methods/supplement evidence ref",
                            )
                        )
                    if value_status != "unreported" and parameter.get("value") is None:
                        errors.append(
                            _finding(
                                "parameter_value_missing",
                                f"analyses[{index}].method_parameters.parameters[{parameter_index}].value",
                                f"{value_status} parameter status requires a non-null value",
                            )
                        )
                    if parameter.get("value_status") == "unreported" and parameter.get("value") is not None:
                        errors.append(
                            _finding(
                                "fabricated_unreported_parameter",
                                f"analyses[{index}].method_parameters.parameters[{parameter_index}].value",
                                "unreported parameters must use null; do not insert a convenient value",
                            )
                        )
                    if parameter.get("value_status") == "implemented":
                        code_refs = [ref for ref in parameter_refs if ref in code_items_by_evidence]
                        implementation_literal = str(parameter.get("implementation_literal", "")).strip()
                        supported = False
                        for ref in code_refs:
                            code_item = code_items_by_evidence[ref]
                            code_path, code_error = _project_relative_path(project_dir, code_item.get("path"))
                            if code_error or code_path is None or not code_path.is_file():
                                continue
                            code_text = _code_without_comments(
                                code_path.read_text(encoding="utf-8", errors="replace")
                            ).lower()
                            if implementation_literal and implementation_literal.lower() in code_text:
                                supported = True
                                break
                        if not supported:
                            errors.append(
                                _finding(
                                    "implemented_parameter_not_found_in_code",
                                    f"analyses[{index}].method_parameters.parameters[{parameter_index}]",
                                    "implemented value must be visible in the cited active code snapshot",
                                )
                            )
                    if parameter.get("value_status") == "inferred" and not str(
                        parameter.get("inference_rationale", "")
                    ).strip():
                        errors.append(
                            _finding(
                                "inferred_parameter_without_rationale",
                                f"analyses[{index}].method_parameters.parameters[{parameter_index}]",
                                "inferred values need an explicit rationale and remain unresolved for ready guidance",
                            )
                        )
                    if parameter.get("value_status") == "observed_runtime":
                        runtime_refs = [str(ref) for ref in parameter.get("execution_record_refs", [])]
                        qualifying_runtime_ref = False
                        for runtime_ref in runtime_refs:
                            record = executions.get(runtime_ref)
                            if record is None or runtime_ref not in analysis_execution_refs.get(analysis_id, set()):
                                errors.append(
                                    _finding(
                                        "observed_runtime_parameter_unknown_execution",
                                        f"analyses[{index}].method_parameters.parameters[{parameter_index}].execution_record_refs",
                                        runtime_ref,
                                    )
                                )
                                continue
                            passed, _ = _execution_is_qualifying(
                                record,
                                project_dir,
                                execution_scope,
                                execution_requested,
                                analysis,
                            )
                            observed_match = any(
                                isinstance(observed, dict)
                                and _normalise_parameter_name(observed.get("name"))
                                == _normalise_parameter_name(parameter.get("name"))
                                and _normalise_parameter_value(observed.get("value"))
                                == _normalise_parameter_value(parameter.get("value"))
                                for observed in record.get("observed_parameters", [])
                            )
                            if passed and not observed_match:
                                errors.append(
                                    _finding(
                                        "observed_runtime_value_mismatch",
                                        f"analyses[{index}].method_parameters.parameters[{parameter_index}]",
                                        (
                                            f"{runtime_ref} does not bind parameter "
                                            f"{parameter.get('name')}={parameter.get('value')!r} to an output/log observation"
                                        ),
                                    )
                                )
                            qualifying_runtime_ref = qualifying_runtime_ref or (passed and observed_match)
                        if not qualifying_runtime_ref:
                            errors.append(
                                _finding(
                                    "observed_runtime_parameter_without_qualifying_run",
                                    f"analyses[{index}].method_parameters.parameters[{parameter_index}]",
                                    "observed_runtime values require a linked qualifying execution record",
                                )
                            )
                    for ref in parameter_refs:
                        evidence_refs_to_check.append(
                            (f"analyses[{index}].method_parameters.parameters[{parameter_index}]", str(ref))
                        )
            parameter_audit = next(
                (
                    item
                    for item in analysis.get("scientific_audit", [])
                    if isinstance(item, dict) and item.get("topic") == "parameter_consistency"
                ),
                None,
            )
            if isinstance(parameter_audit, dict) and parameter_audit.get("status") in {
                "passed",
                "warning",
            }:
                parameters = [
                    item
                    for item in analysis.get("method_parameters", {}).get("parameters", [])
                    if isinstance(item, dict)
                ]
                implemented_names = {
                    _normalise_parameter_name(item.get("name"))
                    for item in parameters
                    if item.get("value_status") in {"implemented", "observed_runtime"}
                }
                for reported_index, reported in enumerate(parameters):
                    if reported.get("value_status") != "reported":
                        continue
                    reported_name = _normalise_parameter_name(reported.get("name"))
                    if reported_name and reported_name not in implemented_names:
                        errors.append(
                            _finding(
                                "reported_parameter_without_code_or_runtime_coverage",
                                f"analyses[{index}].method_parameters.parameters[{reported_index}]",
                                "a passed/warning parameter-consistency audit must register the "
                                "implemented or observed-runtime value for every reported parameter",
                            )
                        )
            issue_ids_seen: set[str] = set()
            for issue_index, issue in enumerate(analysis.get("conflicts_gaps", [])):
                if isinstance(issue, dict):
                    issue_id = str(issue.get("issue_id", ""))
                    if issue_id in issue_ids_seen:
                        errors.append(
                            _finding(
                                "duplicate_issue_id",
                                f"analyses[{index}].conflicts_gaps[{issue_index}].issue_id",
                                issue_id,
                            )
                        )
                    issue_ids_seen.add(issue_id)
                    issue_refs = [str(value) for value in issue.get("evidence_refs", [])]
                    if issue.get("kind") == "conflict" and len(set(issue_refs)) < 2:
                        errors.append(
                            _finding(
                                "conflict_needs_parallel_evidence",
                                f"analyses[{index}].conflicts_gaps[{issue_index}].evidence_refs",
                                "a conflict must preserve at least two distinct evidence refs side by side",
                            )
                        )
                    if issue.get("kind") == "gap" and not issue_refs:
                        errors.append(
                            _finding(
                                "gap_needs_evidence_scope",
                                f"analyses[{index}].conflicts_gaps[{issue_index}].evidence_refs",
                                "a gap needs at least one evidence ref showing the searched/available scope",
                            )
                        )
                    for ref in issue.get("evidence_refs", []):
                        evidence_refs_to_check.append(
                            (f"analyses[{index}].conflicts_gaps[{issue_index}]", str(ref))
                        )
                    for ref in issue.get("resolution_evidence_refs", []):
                        evidence_refs_to_check.append(
                            (
                                f"analyses[{index}].conflicts_gaps[{issue_index}].resolution_evidence_refs",
                                str(ref),
                            )
                        )
                    if issue.get("resolved") is True:
                        resolved_issue_checks.append(
                            (f"analyses[{index}].conflicts_gaps[{issue_index}]", issue)
                        )
            for implicit_conflict in _undeclared_parameter_conflicts(analysis, project_dir):
                errors.append(
                    _finding(
                        "undeclared_parameter_conflict",
                        f"analyses[{index}].method_parameters.parameters",
                        (
                            f"{implicit_conflict['name']}: "
                            f"{implicit_conflict['left_status']}={implicit_conflict['left_value']!r} versus "
                            f"{implicit_conflict['right_status']}={implicit_conflict['right_value']!r}; "
                            "preserve both values in an explicit conflict record"
                        ),
                    )
                )
            for static_gap in _undeclared_static_parameter_gaps(analysis, project_dir):
                errors.append(
                    _finding(
                        "undeclared_static_parameter_gap",
                        f"analyses[{index}].method_parameters.parameters",
                        (
                            f"{static_gap['name']}: {static_gap['reason']}; preserve the "
                            "uncertainty as an unresolved blocking gap citing Methods and active code"
                        ),
                    )
                )
            for audit_index, audit in enumerate(analysis.get("scientific_audit", [])):
                if isinstance(audit, dict):
                    for ref in audit.get("evidence_refs", []):
                        evidence_refs_to_check.append(
                            (f"analyses[{index}].scientific_audit[{audit_index}]", str(ref))
                        )
                    basis = audit.get("claim_basis")
                    if isinstance(basis, dict):
                        for ref in basis.get("evidence_refs", []):
                            evidence_refs_to_check.append(
                                (
                                    f"analyses[{index}].scientific_audit[{audit_index}].claim_basis",
                                    str(ref),
                                )
                            )

            direct_source_lanes: dict[str, set[str]] = {
                "paper_claim": set(),
                "figure": set(),
                "method": set(),
            }
            inference_evidence_refs: set[str] = set()
            unverified_evidence_refs: set[str] = set()
            for group_name, evidence_items in _evidence_groups(analysis):
                for item in evidence_items:
                    if not isinstance(item, dict):
                        continue
                    evidence_id = str(item.get("evidence_id", ""))
                    evidence_class = item.get("evidence_class")
                    if evidence_class == "合理推断":
                        inference_evidence_refs.add(evidence_id)
                    elif evidence_class == "无法验证":
                        unverified_evidence_refs.add(evidence_id)
                    source = sources_by_id.get(str(item.get("source_id", "")))
                    if evidence_class == "直接证据" and _source_material_is_available(
                        project_dir, source
                    ):
                        direct_source_lanes[group_name].add(evidence_id)

            valid_code_refs: set[str] = set()
            for evidence_id, code_item in code_items_by_evidence.items():
                code_path, code_error = _project_relative_path(project_dir, code_item.get("path"))
                snapshot = code_item.get("snapshot")
                source = sources_by_id.get(str(code_item.get("source_id", "")))
                if (
                    not code_error
                    and code_path is not None
                    and code_path.is_file()
                    and isinstance(snapshot, str)
                    and SHA256_RE.fullmatch(snapshot)
                    and _sha256_file(code_path) == _normalise_sha256(snapshot)
                    and _source_material_is_available(project_dir, source)
                ):
                    valid_code_refs.add(evidence_id)

            def valid_artifact_refs(direction: str) -> set[str]:
                result: set[str] = set()
                for artifact in analysis.get("inputs_outputs", {}).get(direction, []):
                    if not isinstance(artifact, dict):
                        continue
                    artifact_path, artifact_error = _project_relative_path(
                        project_dir, artifact.get("path")
                    )
                    fingerprint = artifact.get("fingerprint")
                    if (
                        not artifact_error
                        and artifact_path is not None
                        and artifact_path.is_file()
                        and isinstance(fingerprint, str)
                        and SHA256_RE.fullmatch(fingerprint)
                        and _sha256_file(artifact_path) == _normalise_sha256(fingerprint)
                    ):
                        result.add(str(artifact.get("artifact_id", "")))
                return result

            qualifying_runtime_refs: set[str] = set()
            qualifying_runtime_output_refs: set[str] = set()
            blocked_runtime_refs: set[str] = set()
            for linked_execution_id in analysis.get("execution_record_ids", []):
                record = executions.get(str(linked_execution_id))
                if not isinstance(record, dict):
                    continue
                qualifying, _ = _execution_is_qualifying(
                    record,
                    project_dir,
                    execution_scope,
                    execution_requested,
                    analysis,
                )
                if not qualifying:
                    if _blocked_runtime_is_directly_observable(
                        record,
                        project_dir,
                        execution_scope,
                        execution_requested,
                        analysis,
                    ):
                        blocked_id = str(linked_execution_id)
                        blocked_runtime_refs.add(blocked_id)
                    continue
                qualifying_runtime_refs.add(str(linked_execution_id))
                for artifact in record.get("outputs", []):
                    if isinstance(artifact, dict) and analysis_id in artifact.get(
                        "analysis_ids", []
                    ):
                        qualifying_runtime_output_refs.add(str(artifact.get("artifact_id", "")))

            interpretation_lane_refs = {
                "paper_claim": direct_source_lanes["paper_claim"],
                "figure": direct_source_lanes["figure"],
                "method": direct_source_lanes["method"],
                "code": valid_code_refs,
                "input": valid_artifact_refs("inputs"),
                "output": valid_artifact_refs("outputs") | qualifying_runtime_output_refs,
                "runtime": qualifying_runtime_refs,
            }
            direct_ref_pool = set().union(
                interpretation_lane_refs["figure"],
                interpretation_lane_refs["method"],
                interpretation_lane_refs["code"],
                interpretation_lane_refs["input"],
                interpretation_lane_refs["output"],
                interpretation_lane_refs["runtime"],
                blocked_runtime_refs,
            )
            reconstructed_quantitative_ref_pool = set().union(
                *interpretation_lane_refs.values()
            )
            for category in (
                "direct_observation",
                "paper_claim",
                "reconstructed_support",
                "reasonable_inference",
                "unverified",
            ):
                for statement_index, statement in enumerate(
                    analysis.get("interpretation", {}).get(category, [])
                ):
                    statement_path = (
                        f"analyses[{index}].interpretation.{category}[{statement_index}]"
                    )
                    if not isinstance(statement, dict):
                        errors.append(
                            _finding(
                                "interpretation_statement_not_structured",
                                statement_path,
                                "each interpretation statement must carry explicit evidence_refs",
                            )
                        )
                        continue
                    refs = {str(value) for value in statement.get("evidence_refs", [])}
                    if not str(statement.get("statement", "")).strip() or not refs:
                        errors.append(
                            _finding(
                                "interpretation_statement_untraceable",
                                statement_path,
                                "interpretation statement and evidence_refs must both be non-empty",
                            )
                        )
                    for ref in refs:
                        evidence_refs_to_check.append((statement_path, ref))
                    _validate_quantitative_claims(
                        analysis=analysis,
                        category=category,
                        statement=statement,
                        statement_path=statement_path,
                        refs=refs,
                        project_dir=project_dir,
                        sources_by_id=sources_by_id,
                        executions=executions,
                        execution_scope=execution_scope,
                        execution_requested=execution_requested,
                        allowed_direct_quantitative_refs=(
                            direct_ref_pool - blocked_runtime_refs
                            if category == "direct_observation"
                            else reconstructed_quantitative_ref_pool
                            if category == "reconstructed_support"
                            else None
                        ),
                        errors=errors,
                    )
                    if category == "paper_claim" and not (
                        refs & interpretation_lane_refs["paper_claim"]
                    ):
                        errors.append(
                            _finding(
                                "interpretation_paper_claim_without_claim_evidence",
                                statement_path,
                                "paper_claim interpretation must cite paper-claim evidence",
                            )
                        )
                    if category == "direct_observation" and not (refs & direct_ref_pool):
                        errors.append(
                            _finding(
                                "interpretation_observation_without_direct_material",
                                statement_path,
                                "direct observation must cite inspected figure/method/code/data/runtime evidence",
                            )
                        )
                    blocked_refs = refs & blocked_runtime_refs
                    if category == "direct_observation" and blocked_refs:
                        if (
                            len(blocked_refs) != 1
                            or refs != blocked_refs
                            or statement.get("statement")
                            != BLOCKED_RUNTIME_OBSERVATION_STATEMENT
                            or statement.get("quantitative_claims") != []
                        ):
                            errors.append(
                                _finding(
                                    "blocked_runtime_observation_not_canonical",
                                    statement_path,
                                    (
                                        "a blocked runtime may support only the canonical preflight-blocked "
                                        "statement, as its sole reference and with no quantitative claims"
                                    ),
                                )
                            )
                    elif blocked_refs and category != "unverified":
                        errors.append(
                            _finding(
                                "blocked_runtime_ref_wrong_interpretation_lane",
                                statement_path,
                                (
                                    "blocked runtime refs are operational-only: use the canonical direct "
                                    "blocker statement or cite them under unverified/conflicts and gaps"
                                ),
                            )
                        )
                    if category == "reconstructed_support":
                        represented_lanes = {
                            lane for lane, lane_refs in interpretation_lane_refs.items() if refs & lane_refs
                        }
                        if len(represented_lanes) < 2:
                            errors.append(
                                _finding(
                                    "interpretation_support_not_cross_material",
                                    statement_path,
                                    "reconstructed support must cite at least two evidence lanes",
                                )
                            )

            for execution_id in analysis.get("execution_record_ids", []):
                record = executions.get(str(execution_id))
                if record is None:
                    errors.append(
                        _finding(
                            "unknown_execution_ref",
                            f"analyses[{index}].execution_record_ids",
                            str(execution_id),
                        )
                    )
                    continue
                passed, execution_gaps = _execution_is_qualifying(
                    record,
                    project_dir,
                    execution_scope,
                    execution_requested,
                    analysis,
                )
                if record.get("attempt_status") == "succeeded" and not passed:
                    errors.append(
                        _finding(
                            "successful_record_not_qualifying",
                            f"execution_records.{execution_id}",
                            "; ".join(execution_gaps),
                        )
                    )

            derived, reasons, runtime_gaps = _derive_analysis_status(
                analysis,
                executions,
                sources_by_id,
                project_dir,
                execution_scope,
                execution_requested,
                guidance_blocking_codes,
            )
            derived_statuses[analysis_id] = {
                "declared": analysis.get("reproduction_status"),
                "derived": derived,
                "reasons": reasons,
            }
            if derived == "受阻":
                unresolved_blocker_ids = {
                    str(issue.get("issue_id", ""))
                    for issue in analysis.get("conflicts_gaps", [])
                    if isinstance(issue, dict)
                    and issue.get("blocking") is True
                    and not issue.get("resolved", False)
                }
                linked_blocked_stage = any(
                    isinstance(stage, dict)
                    and stage.get("status") in {"partial", "blocked"}
                    and bool(
                        unresolved_blocker_ids
                        & {str(blocker) for blocker in stage.get("blockers", [])}
                    )
                    for stage in stages
                )
                if not linked_blocked_stage and not guidance_blocking_codes:
                    errors.append(
                        _finding(
                            "blocked_without_stage_blocker",
                            f"analyses[{index}]",
                            "derived blocked state requires a partial/blocked stage whose blocker id cites an unresolved blocking issue",
                        )
                    )
            if analysis.get("reproduction_status") != derived:
                errors.append(
                    _finding(
                        "status_mismatch",
                        f"analyses[{index}].reproduction_status",
                        f"declared {analysis.get('reproduction_status')!r}; derived {derived!r}: {'; '.join(reasons)}",
                    )
                )
            if runtime_gaps:
                warnings.append(
                    _finding(
                        "execution_not_qualifying",
                        f"analyses[{index}].execution_record_ids",
                        "; ".join(runtime_gaps),
                    )
                )
            _validate_interpretation_consistency(analysis, derived, index, errors)

        if len(analysis_ids) != len(set(analysis_ids)):
            errors.append(_finding("duplicate_analysis_id", "analyses", "analysis_id values must be unique"))
        analysis_id_set = set(analysis_ids)

        known_reference_ids = all_evidence_ids | all_artifact_reference_ids | set(executions)
        for ref_path, ref in evidence_refs_to_check:
            if ref and ref not in known_reference_ids:
                errors.append(_finding("unknown_evidence_ref", ref_path, ref))

        for issue_path, issue in resolved_issue_checks:
            original_refs = {str(value) for value in issue.get("evidence_refs", [])}
            resolution_refs = {str(value) for value in issue.get("resolution_evidence_refs", [])}
            if not resolution_refs:
                errors.append(
                    _finding(
                        "resolved_issue_without_evidence",
                        issue_path,
                        "resolved conflicts/gaps require resolution_evidence_refs",
                    )
                )
            elif not (resolution_refs - original_refs):
                errors.append(
                    _finding(
                        "resolved_issue_without_new_evidence",
                        issue_path,
                        "resolution must cite at least one additional evidence id and preserve the original refs",
                    )
                )
            if not str(issue.get("resolution", "")).strip():
                errors.append(
                    _finding(
                        "resolved_issue_without_explanation",
                        issue_path,
                        "resolved issues require a resolution explanation; do not silently flip the boolean",
                    )
                )

        for execution_id, record in executions.items():
            attempt_status = record.get("attempt_status")
            if attempt_status in {"succeeded", "pending_checks"} and record.get("exit_code") != 0:
                errors.append(
                    _finding(
                        "execution_attempt_status_mismatch",
                        f"execution_records.{execution_id}.attempt_status",
                        "succeeded/pending_checks requires exit_code=0",
                    )
                )
            if attempt_status == "blocked" and record.get("preflight", {}).get("status") != "blocked":
                errors.append(
                    _finding(
                        "execution_attempt_status_mismatch",
                        f"execution_records.{execution_id}.preflight.status",
                        "blocked attempts require preflight.status=blocked",
                    )
                )
            if (
                attempt_status in {"succeeded", "failed", "blocked", "pending_checks"}
                and record.get("adjudication_status") != attempt_status
            ):
                errors.append(
                    _finding(
                        "execution_attempt_status_mismatch",
                        f"execution_records.{execution_id}.adjudication_status",
                        "adjudication_status must exactly equal attempt_status",
                    )
                )

            record_analysis_ids = {str(value) for value in record.get("analysis_ids", [])}
            expected_artifacts: dict[str, dict[str, dict[str, Any]]] = {
                "inputs": {},
                "outputs": {},
            }
            expected_output_owners: dict[str, set[str]] = {}
            for linked_analysis_id in record_analysis_ids:
                linked_analysis = analyses_by_id.get(linked_analysis_id)
                if not isinstance(linked_analysis, dict):
                    continue
                for direction in ("inputs", "outputs"):
                    for artifact in linked_analysis.get("inputs_outputs", {}).get(direction, []):
                        if not isinstance(artifact, dict):
                            continue
                        artifact_id = str(artifact.get("artifact_id", ""))
                        if direction == "outputs":
                            expected_output_owners.setdefault(artifact_id, set()).add(linked_analysis_id)
                        previous = expected_artifacts[direction].get(artifact_id)
                        if previous is not None and previous != artifact:
                            errors.append(
                                _finding(
                                    "shared_artifact_contract_conflict",
                                    f"execution_records.{execution_id}.{direction}",
                                    f"linked analyses define incompatible contracts for {artifact_id}",
                                )
                            )
                        else:
                            expected_artifacts[direction][artifact_id] = artifact

            for direction in ("inputs", "outputs"):
                actual_artifacts = {
                    str(item.get("artifact_id", "")): item
                    for item in record.get(direction, [])
                    if isinstance(item, dict)
                }
                expected_ids = set(expected_artifacts[direction])
                actual_ids = set(actual_artifacts)
                for artifact_id in sorted(actual_ids - expected_ids):
                    errors.append(
                        _finding(
                            "execution_orphan_artifact",
                            f"execution_records.{execution_id}.{direction}",
                            f"{artifact_id} is not owned by any linked analysis contract",
                        )
                    )
                if attempt_status in {"succeeded", "pending_checks"}:
                    for artifact_id in sorted(expected_ids - actual_ids):
                        errors.append(
                            _finding(
                                "execution_artifact_contract_mismatch",
                                f"execution_records.{execution_id}.{direction}",
                                f"missing linked analysis artifact {artifact_id}",
                            )
                        )
                for artifact_id in sorted(actual_ids & expected_ids):
                    actual = actual_artifacts[artifact_id]
                    expected = expected_artifacts[direction][artifact_id]
                    mismatch = actual.get("semantic_type") != expected.get("semantic_type")
                    if direction == "outputs":
                        actual_owners = {str(value) for value in actual.get("analysis_ids", [])}
                        if actual_owners != expected_output_owners.get(artifact_id, set()):
                            errors.append(
                                _finding(
                                    "execution_output_owner_mismatch",
                                    f"execution_records.{execution_id}.outputs.{artifact_id}.analysis_ids",
                                    "output analysis_ids must exactly equal the analyses that declare this artifact",
                                )
                            )
                    if attempt_status in {"succeeded", "pending_checks"}:
                        mismatch = mismatch or actual.get("path") != expected.get("path")
                        fingerprint = expected.get("fingerprint")
                        mismatch = mismatch or not isinstance(fingerprint, str) or not SHA256_RE.fullmatch(
                            fingerprint
                        ) or _normalise_sha256(fingerprint) != _normalise_sha256(
                            str(actual.get("sha256", ""))
                        )
                    if mismatch:
                        errors.append(
                            _finding(
                                "execution_artifact_contract_mismatch",
                                f"execution_records.{execution_id}.{direction}.{artifact_id}",
                                "execution artifact does not match the linked analysis path/type/fingerprint contract",
                            )
                        )

            allowed_code_refs = {
                str(item.get("evidence_id", ""))
                for linked_analysis_id in record_analysis_ids
                for item in analyses_by_id.get(linked_analysis_id, {}).get("code_locations", [])
                if isinstance(item, dict) and item.get("evidence_status") in CODE_BUNDLE_STATUSES
            }
            unknown_code_refs = {
                str(value) for value in record.get("code_evidence_refs", [])
            } - allowed_code_refs
            if unknown_code_refs:
                errors.append(
                    _finding(
                        "execution_code_ref_mismatch",
                        f"execution_records.{execution_id}.code_evidence_refs",
                        "refs are not active code for linked analyses: " + ", ".join(sorted(unknown_code_refs)),
                    )
                )

            checks = record.get("checks", [])
            if isinstance(checks, list):
                check_ids_seen: set[str] = set()
                output_by_path = {
                    str(item.get("path", "")): item
                    for item in record.get("outputs", [])
                    if isinstance(item, dict)
                }
                for check_index, check in enumerate(checks):
                    if not isinstance(check, dict):
                        continue
                    check_id = str(check.get("check_id", ""))
                    if not ID_RE.fullmatch(check_id) or check_id in check_ids_seen:
                        errors.append(
                            _finding(
                                "execution_check_id_invalid",
                                f"execution_records.{execution_id}.checks[{check_index}].check_id",
                                "check_id must be valid and unique within an execution record",
                            )
                        )
                    check_ids_seen.add(check_id)
                    if not str(check.get("metric", "")).strip() or not str(
                        check.get("unit", "")
                    ).strip():
                        errors.append(
                            _finding(
                                "execution_check_identity_missing",
                                f"execution_records.{execution_id}.checks[{check_index}]",
                                "each result check requires non-empty metric and unit",
                            )
                        )
                    expected_metric, expected_unit, identity_error = _mechanical_check_identity(
                        project_dir, check
                    )
                    if identity_error:
                        errors.append(
                            _finding(
                                "execution_check_identity_unverifiable",
                                f"execution_records.{execution_id}.checks[{check_index}]",
                                identity_error,
                            )
                        )
                    else:
                        if expected_metric is not None and str(
                            check.get("metric", "")
                        ) != expected_metric:
                            errors.append(
                                _finding(
                                    "execution_check_metric_selector_mismatch",
                                    f"execution_records.{execution_id}.checks[{check_index}].metric",
                                    "metric must exactly equal the mechanically selected TSV key or JSON Pointer",
                                )
                            )
                        if str(check.get("unit", "")) != expected_unit:
                            errors.append(
                                _finding(
                                    "execution_check_unit_unbound",
                                    f"execution_records.{execution_id}.checks[{check_index}].unit",
                                    "unit must equal selected TSV unit metadata, or the fail-closed default",
                                )
                            )
                    check_analysis_ids = {str(value) for value in check.get("analysis_ids", [])}
                    if not check_analysis_ids or not check_analysis_ids.issubset(record_analysis_ids):
                        errors.append(
                            _finding(
                                "execution_check_analysis_mismatch",
                                f"execution_records.{execution_id}.checks[{check_index}].analysis_ids",
                                "check analysis_ids must be a non-empty subset of record.analysis_ids",
                            )
                        )
                    verification = check.get("verification")
                    verification_path = (
                        str(verification.get("evidence_path", ""))
                        if isinstance(verification, dict)
                        else ""
                    )
                    selected_output = output_by_path.get(verification_path)
                    if isinstance(selected_output, dict):
                        output_owners = {
                            str(value) for value in selected_output.get("analysis_ids", [])
                        }
                        if not check_analysis_ids.issubset(output_owners):
                            errors.append(
                                _finding(
                                    "execution_check_output_owner_mismatch",
                                    f"execution_records.{execution_id}.checks[{check_index}].analysis_ids",
                                    "a check selecting an output may cite only that output's owners",
                                )
                            )
                if attempt_status == "succeeded":
                    if not checks or any(
                        not isinstance(check, dict) or check.get("passed") is not True for check in checks
                    ):
                        errors.append(
                            _finding(
                                "execution_adjudication_mismatch",
                                f"execution_records.{execution_id}.checks",
                                "succeeded requires non-empty all-passed scientific checks",
                            )
                        )
                    for linked_analysis_id in record_analysis_ids:
                        if not any(
                            isinstance(check, dict)
                            and check.get("passed") is True
                            and linked_analysis_id in check.get("analysis_ids", [])
                            for check in checks
                        ):
                            errors.append(
                                _finding(
                                    "execution_check_coverage_missing",
                                    f"execution_records.{execution_id}.checks",
                                    f"no passed scientific check covers {linked_analysis_id}",
                                )
                            )
                    for output_path, output in output_by_path.items():
                        for owner in {str(value) for value in output.get("analysis_ids", [])}:
                            if not any(
                                isinstance(check, dict)
                                and check.get("passed") is True
                                and owner in check.get("analysis_ids", [])
                                and isinstance(check.get("verification"), dict)
                                and str(check["verification"].get("evidence_path", "")) == output_path
                                for check in checks
                            ):
                                errors.append(
                                    _finding(
                                        "execution_output_owner_check_missing",
                                        f"execution_records.{execution_id}.outputs.{output.get('artifact_id', '')}",
                                        f"no passed mechanical check covers output owner {owner}",
                                    )
                                )
            for superseded in record.get("supersedes_execution_ids", []):
                superseded_id = str(superseded)
                if superseded_id == execution_id:
                    errors.append(
                        _finding(
                            "execution_self_supersedes",
                            f"execution_records.{execution_id}.supersedes_execution_ids",
                            execution_id,
                        )
                    )
                elif superseded_id not in executions:
                    errors.append(
                        _finding(
                            "unknown_superseded_execution",
                            f"execution_records.{execution_id}.supersedes_execution_ids",
                            superseded_id,
                        )
                    )
                else:
                    prior = executions[superseded_id]
                    if attempt_status != "succeeded":
                        errors.append(
                            _finding(
                                "invalid_superseding_status",
                                f"execution_records.{execution_id}.supersedes_execution_ids",
                                "only a succeeded adjudicated attempt may supersede a prior attempt",
                            )
                        )
                    if prior.get("attempt_status") == "succeeded":
                        errors.append(
                            _finding(
                                "invalid_superseded_status",
                                f"execution_records.{execution_id}.supersedes_execution_ids",
                                f"{superseded_id} is already succeeded and must not be silently replaced",
                            )
                        )
                    if {str(value) for value in prior.get("analysis_ids", [])} != record_analysis_ids:
                        errors.append(
                            _finding(
                                "supersedes_analysis_mismatch",
                                f"execution_records.{execution_id}.supersedes_execution_ids",
                                f"{superseded_id} covers a different analysis set",
                            )
                        )
                    prior_finished = _parse_utc_timestamp(prior.get("finished_at_utc"))
                    current_started = _parse_utc_timestamp(record.get("started_at_utc"))
                    if (
                        prior_finished is None
                        or current_started is None
                        or current_started < prior_finished
                    ):
                        errors.append(
                            _finding(
                                "supersedes_time_order_violation",
                                f"execution_records.{execution_id}.supersedes_execution_ids",
                                f"{execution_id} must start at or after {superseded_id} finished",
                            )
                        )
            for analysis_id in record.get("analysis_ids", []):
                if analysis_id not in analysis_id_set:
                    errors.append(
                        _finding(
                            "unknown_analysis_ref",
                            f"execution_records.{execution_id}.analysis_ids",
                            str(analysis_id),
                        )
                    )
                elif execution_id not in analysis_execution_refs.get(str(analysis_id), set()):
                    errors.append(
                        _finding(
                            "execution_backlink_missing",
                            f"execution_records.{execution_id}.analysis_ids",
                            f"analysis {analysis_id} does not link back to {execution_id}",
                        )
                    )

        supersedes_graph = {
            execution_id: {str(value) for value in record.get("supersedes_execution_ids", [])}
            for execution_id, record in executions.items()
        }
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit_supersedes(execution_id: str) -> bool:
            if execution_id in visiting:
                return True
            if execution_id in visited:
                return False
            visiting.add(execution_id)
            for prior_id in supersedes_graph.get(execution_id, set()):
                if prior_id in supersedes_graph and visit_supersedes(prior_id):
                    return True
            visiting.remove(execution_id)
            visited.add(execution_id)
            return False

        if any(visit_supersedes(execution_id) for execution_id in executions):
            errors.append(
                _finding(
                    "execution_supersedes_cycle",
                    "execution_records",
                    "supersedes_execution_ids must form an acyclic prior-attempt graph",
                )
            )

        for analysis_id, execution_ids in analysis_execution_refs.items():
            for execution_id in execution_ids:
                record = executions.get(execution_id)
                if record is not None and analysis_id not in record.get("analysis_ids", []):
                    errors.append(
                        _finding(
                            "analysis_execution_link_mismatch",
                            f"analyses.{analysis_id}.execution_record_ids",
                            f"execution {execution_id} does not link back to {analysis_id}",
                        )
                    )

        trace_ids = [str(row.get("analysis_id", "")) for row in trace_rows]
        if len(trace_ids) != len(set(trace_ids)):
            errors.append(_finding("duplicate_trace_analysis_id", "traceability.tsv", "one row per analysis_id is required"))
        if set(trace_ids) != analysis_id_set:
            errors.append(
                _finding(
                    "trace_manifest_id_mismatch",
                    "traceability.tsv",
                    f"trace ids {sorted(set(trace_ids))!r} do not match manifest ids {sorted(analysis_id_set)!r}",
                )
            )
        for row_index, row in enumerate(trace_rows, start=2):
            analysis_id = str(row.get("analysis_id", ""))
            status = str(row.get("复现状态", ""))
            if status not in REPRODUCTION_STATUSES:
                errors.append(
                    _finding(
                        "illegal_trace_status",
                        f"traceability.tsv:line {row_index}:复现状态",
                        status,
                    )
                )
            expected = derived_statuses.get(analysis_id, {}).get("derived")
            if expected and status != expected:
                errors.append(
                    _finding(
                        "trace_status_mismatch",
                        f"traceability.tsv:line {row_index}:复现状态",
                        f"observed {status!r}, expected {expected!r}",
                    )
                )
            analysis = analyses_by_id.get(analysis_id)
            if analysis is not None:
                _validate_trace_row_content(row, analysis, row_index, errors)

        statuses = [item["derived"] for item in derived_statuses.values()]
        derived_overall = _derive_overall(statuses)
        if manifest.get("overall_status") != derived_overall:
            errors.append(
                _finding(
                    "overall_status_mismatch",
                    "overall_status",
                    f"declared {manifest.get('overall_status')!r}, derived {derived_overall!r}",
                )
            )

        if report_text is not None:
            _validate_manifest_derived_report(
                report_text,
                analyses_by_id,
                derived_statuses,
                errors,
            )
            report_markers = {
                "direct evidence/observation": re.compile(
                    r"直接证据|直接观察|direct\s+(?:evidence|observation)", re.IGNORECASE
                ),
                "reasonable inference": re.compile(r"合理推断|reasonable\s+inference", re.IGNORECASE),
                "unverifiable content": re.compile(
                    r"无法验证|未验证|unverifiable|unverified", re.IGNORECASE
                ),
            }
            for label, pattern in report_markers.items():
                if not pattern.search(report_text):
                    errors.append(
                        _finding(
                            "report_missing_evidence_class",
                            "REPORT.md",
                            f"report must explicitly separate {label}, even when the section says none",
                        )
                    )
            for analysis_id, status_record in derived_statuses.items():
                if analysis_id not in report_text:
                    errors.append(
                        _finding(
                            "report_missing_analysis",
                            "REPORT.md",
                            f"report must identify analysis {analysis_id}",
                        )
                    )
                derived_status = str(status_record.get("derived", ""))
                if derived_status and derived_status not in report_text:
                    errors.append(
                        _finding(
                            "report_missing_status",
                            "REPORT.md",
                            f"report must preserve derived status {derived_status} for {analysis_id}",
                        )
                    )
            if derived_overall != "已执行验证":
                for line_number, line in enumerate(report_text.splitlines(), start=1):
                    if _line_asserts_completion(line):
                        errors.append(
                            _finding(
                                "unsupported_completion_language",
                                f"REPORT.md:line {line_number}",
                                "completion language is not allowed without project-level executed verification",
                            )
                        )
            report_ceiling = min(
                (_analysis_claim_ceiling(value) for value in analyses_by_id.values()),
                key=lambda value: CLAIM_CEILING_RANK.get(value, 0),
                default="not_assessable",
            )
            _validate_claim_text(
                report_text,
                report_ceiling,
                "REPORT.md",
                errors,
                allow_attributed_claims=True,
            )

    result = {
        "validator": "reconstruct-bioinfo-protocol/1.4.0",
        "project_dir": str(project_dir),
        "valid": not errors,
        "schema_validation": schema_status,
        "derived_statuses": derived_statuses,
        "derived_overall_status": derived_overall,
        "errors": errors,
        "warnings": warnings,
        "scope_note": (
            "Contract, receipt, on-disk path, SHA-256, linkage, and provenance validation only. "
            "The receipt is not signed: a writer controlling the whole project can fabricate it. "
            "A passing validator therefore does not prove process-to-artifact causality or scientific "
            "correctness; retain independent runtime/job logs and expert review."
        ),
    }

    if write_report:
        output_path = project_dir / "validation_report.json"
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--write-report", action="store_true")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    result = validate_project(args.project_dir, write_report=args.write_report)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())

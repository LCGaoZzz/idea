#!/usr/bin/env python3
"""Auditable label-permutation test on a FIXED nearest-neighbor graph.

Independent audit utility; not an official KPSpatial/Cassiopeia replacement.
The caller must supply the intended graph and the exchangeable population.
Does not infer a graph, choose biological replicates, read pickle, or access files.
Only standard-library modules are required.
"""
from __future__ import annotations
from collections import Counter
from math import isfinite
from random import Random
from typing import Hashable, Mapping, Sequence, Any


def _prepare(labels: Mapping[Hashable, Hashable],
             neighbors: Mapping[Hashable, Sequence[Hashable]]):
    if len(labels) < 2 or set(labels) != set(neighbors):
        raise ValueError('Require at least two cells and identical label/neighbor keys.')
    keys = tuple(labels)
    pos = {key: i for i, key in enumerate(keys)}
    values = []
    graph = []
    for key in keys:
        val = labels[key]
        if val is None or (isinstance(val, float) and not isfinite(val)):
            raise ValueError('Missing or non-finite labels are not permitted.')
        try:
            hash(val)
        except TypeError as exc:
            raise ValueError('Labels must be hashable scalars.') from exc
        values.append(val)
        ns = tuple(neighbors[key])
        if not ns or key in ns or len(set(ns)) != len(ns) or any(n not in pos for n in ns):
            raise ValueError('Neighbors must be unique, nonempty, known, and exclude self.')
        graph.append(tuple(pos[n] for n in ns))
    return keys, values, graph


def _purity(values, graph) -> float:
    return sum(sum(values[i] == values[j] for j in ns) / len(ns)
               for i, ns in enumerate(graph)) / len(values)


def neighbor_purity(labels: Mapping[Hashable, Hashable],
                    neighbors: Mapping[Hashable, Sequence[Hashable]]) -> float:
    _, values, graph = _prepare(labels, neighbors)
    return _purity(values, graph)


def permutation_nn_test(labels: Mapping[Hashable, Hashable],
                        neighbors: Mapping[Hashable, Sequence[Hashable]], *,
                        permutations: int = 9999, seed: int = 0,
                        blocks: Mapping[Hashable, Hashable] | None = None,
                        atol: float = 1e-12, return_null: bool = False) -> dict[str, Any]:
    """Upper-tail permutation test, including ties, with Monte Carlo +1 correction.

    Exchangeability is an assumption, not guaranteed by this function. Optional
    blocks restrict permutation within caller-defined blocks. All nodes must be
    within the same admissible test population before entering this function.
    Degenerate nulls return p=1 and an explicit flag, not evidence of agreement.
    """
    if isinstance(permutations, bool) or not isinstance(permutations, int) or permutations < 1:
        raise ValueError('permutations must be a positive integer.')
    if not isfinite(atol) or atol < 0:
        raise ValueError('atol must be finite and nonnegative.')
    keys, values, graph = _prepare(labels, neighbors)
    if blocks is not None and set(blocks) != set(keys):
        raise ValueError('blocks must cover exactly the tested cells.')
    groups = {}
    for i, key in enumerate(keys):
        block = blocks[key] if blocks is not None else '__all__'
        if block is None:
            raise ValueError('Block identifiers cannot be missing.')
        groups.setdefault(block, []).append(i)
    rng = Random(seed)
    observed = _purity(values, graph)
    null = []
    for _ in range(permutations):
        shuffled = list(values)
        for indices in groups.values():
            vs = [values[i] for i in indices]
            rng.shuffle(vs)
            for i, v in zip(indices, vs):
                shuffled[i] = v
        null.append(_purity(shuffled, graph))
    exceed = sum(v >= observed - atol for v in null)
    ties = sum(abs(v - observed) <= atol for v in null)
    degenerate = max(null) - min(null) <= atol and abs(null[0] - observed) <= atol
    result = dict(observed=observed, p_value=(1 + exceed) / (permutations + 1),
                  permutations=permutations, seed=seed, inclusive_exceedances=exceed,
                  ties=ties, degenerate_null=degenerate,
                  null_mean=sum(null) / permutations, null_min=min(null), null_max=max(null),
                  n_cells=len(values), n_labels=len(Counter(values)),
                  n_blocks=len(groups), test='fixed_graph_label_permutation_upper_tail',
                  interpretation='No causal, lineage reconstruction, or independent-animal claim is implied.')
    if return_null:
        result['null_scores'] = null
    return result

# 代码定位索引

固定版本与来源见 `SOURCES.md` / `sources_catalog.json`。只有完整脚本的行号可直接映射上游；其余以函数名、源窗口和局部片段定位，不伪造原行号。

## KPSpatial-release · commit `c2fa7568ee48a9e35bbc6ecd88378c6768b23e00`

- `evidence/code/bootstrap_phylo_infercnv_slidetags.py`
  - `find_nearest_neighbor`: upstream L19–L41
  - `get_all_nearest_neighbors`: L43–L50
  - `assess_nn_purity`: L53–L70
  - `shuffle_dict`: L72–L78
  - `bootstrap_nn_purity`: L80–L95
- `evidence/phylodynamics_excerpt.txt`
  - upstream `utilities/phylodynamics.py::score_fitness` / `_fitness_wrapper`
  - group pruning: `np.setdiff1d(query_cells, tree.leaves)`
  - estimator: `cas.tools.fitness_estimator.LBIJungle()`
- `evidence/reconstruct_excerpt.txt`
  - upstream `utilities/reconstruct.py::create_character_matrix`
  - spot/intBC threshold handling, PercentUncut overlap reassignment, two-value imputation destructuring
- `evidence/target_site_excerpt.txt`
  - upstream `utilities/target_site_utilities.py::impute_single_state`
  - returns `(state, vote_fraction, n_votes)`
- `evidence/community_scoring_excerpt.txt`
  - upstream `reproducibility/Figure2/scripts/score_consensus_hotspot.py`
  - normalize/log/scale, 25% boundary, `score_genes(ctrl_size=100,n_bins=30)`, space-delimited output
- `evidence/neighborhood_excerpt.txt`
  - upstream `reproducibility/Figure3/scripts/score_neighborhood_abundances.py`
  - `RADIUS=28`, literal `{HOMEDIR}` read path, spatial graph / one-hop neighborhood
- `evidence/fitness_entrypoint_excerpt.txt`
  - upstream Figure3 caller of `phylodynamics.score_fitness(..., 'lbi', 'tumor_id', ..., True)`
- `evidence/de_excerpt.txt`
  - upstream `utilities/differential_expression.py`, selected preprocessing / DE calls

## Cassiopeia · commit `1ee5959eb9d3f8d4d26e2af5678234493bf54d6d`

- `evidence/code/cassiopeia_lbi_export_excerpt.py.txt`
  - `_lbi_jungle.py::estimate_fitness`, upstream L114–L124
  - exported field: `res_df.mean_fitness`
- `evidence/code/cassiopeia_ranking_excerpt.py.txt`
  - `node_ranking.compute_rankings`
  - `mean_fitness -> infer_ancestral_fitness()` and `polarizer -> calculate_polarizers()` are separate branches
- `evidence/notes/cassiopeia_export_call_chain.md`
  - call-chain interpretation and version boundary

## Byte-audited data files

- `evidence/puck_meta.txt`: complete 49-row metadata table; Git blob `75b5f677202c1655fba4a7281df9cdd82261d403`
- `evidence/tables/slidetags_infercnv_nn_score.tsv`: complete 15-row public result table; Git blob `102b2344fd9668e0bde33af7616299c534768577`
- `evidence/code/bootstrap_phylo_infercnv_slidetags.py`: complete 4730-byte script; Git blob `c0e30a3714d65fdce3fe82977d415203efa4dee3`

For claims about actual execution, use `audit/deep_audit_results.json` and `audit/inherited_checks_rerun.json`; source presence alone is not an execution trace.

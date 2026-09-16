# Fresh code reading, 2026-09-16 (not a runtime trace)

KPSpatial c2fa7568ee48a9e35bbc6ecd88378c6768b23e00:
`utilities/phylodynamics.py::_fitness_wrapper` calls `cas.tools.fitness_estimator.LBIJungle()` and extracts the `fitness` attribute, then divides leaf values by their maximum.

Cassiopeia separately pinned to 1ee5959eb9d3f8d4d26e2af5678234493bf54d6d:
`cassiopeia/tools/fitness_estimator/_lbi_jungle.py::estimate_fitness`, lines 114-124, calls `jg.Tree.infer_fitness(params={})` and exports `res_df.mean_fitness` as `fitness`.

Vendored `cassiopeia/tools/fitness_estimator/_jungle/jungle/tree.py::Tree.infer_fitness` constructs `node_ranking` with methods `mean_fitness`, `polarizer`, `expansion_score`, calls `compute_rankings`, and copies named fields including `mean_fitness` back into tree-node features.

`.../resources/FitnessInference/prediction_src/node_ranking.py::compute_rankings` sends `mean_fitness` to `infer_ancestral_fitness()` and `polarizer` to `calculate_polarizers()` in separate branches. Its header describes mean posterior fitness. This is a confirmed output-field distinction in these audited commits; it is not proof of which Cassiopeia commit generated the final paper's results. Do not automatically substitute the textbook LBI integral for the actual exported variable.

Sources: GitHub connector reads /response/turn22, /response/turn23, /response/turn24, /response/turn25. The two `.txt` excerpts preserve selected lines, not full-file bytes. Their SHA-256 protects these local captures, NOT identity with the whole Git blob. Exact paper runtime environment and archived-code identity remain unresolved.

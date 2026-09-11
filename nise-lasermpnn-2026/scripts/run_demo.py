"""Run deterministic synthetic examples, plus explicitly labelled point-estimate math."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import platform
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import scipy
from binding import (bound_fraction, competition, fit_direct, fit_competition,
                     mutant_cycle, proofreading_delta, wilson_interval)
from geometry import complex_rmsd
from screen import GatePolicy, evaluate_rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists; choose a new directory")
    rng = np.random.default_rng(20260911)
    protein = rng.normal(size=(15, 3))
    ligand = rng.normal(size=(6, 3))
    rotation = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
    shift = np.array([4., -2., 1.])
    same = complex_rmsd(protein @ rotation + shift, protein, ligand @ rotation + shift, ligand)
    moved = complex_rmsd(protein, protein, ligand + [3., 0., 0.], ligand)
    base = dict(protein_rmsd_A=1.0, ligand_rmsd_A=1.2, ligand_plddt=93,
                plddt_scale="0-100", mapping_valid=True, burial_pass=True, debug=False)
    variants = [("pass", {}), ("ligand_wrong", {"ligand_rmsd_A": 4.0}),
                ("debug", {"debug": True}), ("mapping", {"mapping_valid": False}),
                ("unit_error", {"plddt_scale": "0-1"}),
                ("nan_rmsd", {"protein_rmsd_A": float("nan")}),
                ("burial", {"burial_pass": False}),
                ("pass_01", {"ligand_plddt": .93, "plddt_scale": "0-1"})]
    rows = [dict(base, candidate_id=name, **changes) if not changes else
            {**base, "candidate_id": name, **changes} for name, changes in variants]
    policy = GatePolicy(2.5, 2.5, .8)
    screened = evaluate_rows(rows, policy)
    p = np.tile(np.logspace(-2, 3, 60), 2)
    l = np.repeat([1., 50.], 60)
    y = bound_fraction(p, l, 3.5) + rng.normal(0, .001, len(p))
    direct = fit_direct(p, l, y, initial_kd=2., bounds=(1e-5, 1e4))
    pc = np.concatenate([np.logspace(-2, 2, 40), np.repeat([1., 3., 10.], 50)])
    lc = np.full(len(pc), .5)
    ic = np.concatenate([np.zeros(40), np.tile(np.logspace(-3, 3, 50), 3)])
    yc = competition(pc, lc, ic, 1.4, .23)["tracer_complex"] / lc + rng.normal(0, .001, len(pc))
    competitive = fit_competition(pc, lc, ic, yc, initial_kds=[1., .5], bounds=(1e-5, 1e4))
    if not direct["success"] or not competitive["success"]:
        raise RuntimeError("Synthetic fit failed")
    script_dir = Path(__file__).resolve().parent
    hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(script_dir.glob("*.py"))}
    report = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "runtime": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "script_sha256": hashes,
        "synthetic_demo": {"seed": 20260911, "concentration_unit": "nM", "geometry_same_complex": same,
            "geometry_moved_ligand": moved, "screening": screened,
            "direct_fit_true_kd": 3.5, "direct_fit": direct,
            "competition_true_kds": [1.4, .23], "competition_fit": competitive,
            "proofreading_example": proofreading_delta(.1, .4, .1, .2)},
        "published_point_estimates_derived_math_not_refit": {
            "source": "https://doi.org/10.1038/s41586-026-10670-w, Figs. 3-4, point estimates only",
            "kd_unit": "nM", "kd_wt_a_b_ab": [120., 8., 7.4, 1.2],
            "mutant_cycle": mutant_cycle(120., 8., 7.4, 1.2, temperature_K=298.15),
            "temperature_note": "298.15 K is illustrative, not a recovered binding-assay temperature",
            "wilson_4_of_4": wilson_interval(4, 4), "wilson_5_of_6": wilson_interval(5, 6),
            "interval_note": "Descriptive independent-binomial approximation; ignores pose/lineage clustering"},
        "not_run": ["LASErMPNN inference or training", "RFAA/Boltz inference", "original-data fits", "wet experiments"]}
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "demo_results.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    (args.output / "gate_policy.json").write_text(json.dumps(asdict(policy), indent=2) + "\n")
    with (args.output / "candidates.synthetic.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for name, matrix, header in (
        ("direct.synthetic.csv", np.column_stack([p, l, y]), "protein_nM,ligand_nM,bound_fraction"),
        ("competition.synthetic.csv", np.column_stack([pc, lc, ic, yc]), "protein_nM,tracer_nM,competitor_nM,bound_fraction")):
        np.savetxt(args.output / name, matrix, delimiter=",", header=header, comments="")
    print(json.dumps({"output": str(args.output), "data_origin": "synthetic_demo_and_labelled_point_estimate_math",
                      "screening_passed": sum(r["passed"] for r in screened), "direct_kd": direct["kd"],
                      "competition_kds": competitive["kd"]}, indent=2))


if __name__ == "__main__":
    main()

"""Generate labelled SYNTHETIC examples; never presented as paper data."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from niche_idea import summarize_serpin, build_roi_table, farthest_point_sample, factorial_contrasts, bootstrap_mean


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,default=Path("demo_output"))
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(42)
    expr=pd.DataFrame({"source":["SYNTHETIC"]*200,
                       "patient_id":np.repeat(["SYN_P1","SYN_P2"],100),
                       "cell_id":[f"c{i}" for i in range(200)],"is_malignant":[True]*200,
                       "SERPINE1":rng.poisson(.15,200),"SERPINB2":rng.poisson(.1,200)})
    expr.to_csv(args.out/"synthetic_expression.csv",index=False)
    summarize_serpin(expr,representation="raw_counts").to_csv(args.out/"source_summary.csv",index=False)
    frames=[]
    for i in [1,2]:
        xy=rng.uniform(0,1000,(1500,2))
        labels=rng.choice(["CTRL","KO","CD8","Macrophage","Other"],1500,p=[.1,.5,.1,.2,.1])
        frames.append(pd.DataFrame({"image_id":f"SYN_IMG{i}","patient_id":f"SYN_P{i}",
                                    "cell_id":[f"c{j}" for j in range(1500)],
                                    "x_um":xy[:,0],"y_um":xy[:,1],"phenotype":labels}))
    cells=pd.concat(frames,ignore_index=True)
    centers=pd.DataFrame([{"image_id":f"SYN_IMG{i}","roi_id":f"r{k}","x_um":x,"y_um":y}
                          for i in [1,2] for k,(x,y) in enumerate([(250,250),(400,250),(750,750),(600,750)])])
    cells.to_csv(args.out/"synthetic_cells.csv",index=False)
    centers.to_csv(args.out/"synthetic_centers.csv",index=False)
    result=build_roi_table(cells,centers,radius_um=180,control_label="CTRL",ko_label="KO",
                           immune_labels=["CD8","Macrophage"],min_total=20,min_tumor=10,
                           assume_full_tissue=True,record_membership=True)
    result.table.to_csv(args.out/"roi_table.csv",index=False)
    result.exclusions.to_csv(args.out/"roi_exclusions.csv",index=False)
    result.membership.to_csv(args.out/"roi_membership.csv",index=False)
    farthest_point_sample(result.table,n_per_group=2).to_csv(args.out/"sampled_rois.csv",index=False)
    factorial=pd.DataFrame([{"donor_id":f"SYN_D{d}","matrix":m,"context":c,
                             "value":float(10+d*.1+m+2*c+m*c+rng.normal(0,.3))}
                            for d in range(12) for m in [0,1] for c in [0,1] for _ in range(3)])
    factorial.to_csv(args.out/"synthetic_factorial.csv",index=False)
    contrasts=factorial_contrasts(factorial)
    contrasts.to_csv(args.out/"donor_contrasts.csv",index=False)
    report={"data_status":"SYNTHETIC_NOT_PAPER_DATA","seed":42,
             "purpose":"Input/output and denominator teaching only; no biological validation",
             "n_cells":len(cells),"n_rois":len(result.table),"n_excluded":len(result.exclusions),
             "factorial_bootstrap":bootstrap_mean(contrasts.interaction.to_numpy())}
    (args.out/"demo_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__ == "__main__": main()

"""Counts for the plan (set sizes, steps, centre mix, state distribution, folds); design files + lengths only."""
import json, sys
import numpy as np
sys.path.insert(0, "<locked snapshot: git archive of 2880d73>")
from ss_benchmark import design
from ss_benchmark.constants import ANALYSIS_REGION
cases = design.representation_cases()
sites = cases.center.to_numpy()
folds = design.representation_folds().loc[cases.case_id].to_numpy()
s = design.representation_switch_steps().loc[cases.case_id].to_numpy()
lens = np.load("/media/user/LaCie/medvideo_gate/ss_step4_5/step5/reps_full_P.npz")["lengths"]
D = design.load_real_design("primary")
pos = {c: i for i, c in enumerate(cases.case_id)}
pidx = np.array([pos[c] for c in D.ids]); w = dict(zip(pidx, D.window_start()))
lo, hi = ANALYSIS_REGION
assert (lens[pidx] == D.n_steps).all()
sets = {"S1": {i: np.arange(lens[i]) for i in range(len(cases))},
        "S2": {i: np.arange(lens[i]) for i in pidx},
        "S3": {i: np.arange(w[i] + lo, w[i] + hi + 1) for i in pidx}}
out = {}
for name, st in sets.items():
    idx = np.array(sorted(st)); n = np.array([len(st[i]) for i in idx])
    S1 = np.array([(st[i] >= s[i]).sum() for i in idx])
    cen = sorted(set(sites))
    out[name] = dict(
        cases=int(len(idx)), steps=int(n.sum()),
        steps_per_case=dict(mean=float(n.mean()), min=int(n.min()), median=float(np.median(n)), max=int(n.max())),
        cases_per_centre={int(c): int((sites[idx] == c).sum()) for c in cen},
        steps_per_centre={int(c): int(n[sites[idx] == c].sum()) for c in cen},
        state_S1_share=float(S1.sum() / n.sum()),
        state_S1_share_per_centre={int(c): float(S1[sites[idx] == c].sum() / n[sites[idx] == c].sum()) for c in cen},
        cases_with_both_states=int(((S1 > 0) & (S1 < n)).sum()),
        cases_per_fold={int(v): int((folds[idx] == v).sum()) for v in range(5)},
        cases_per_fold_and_centre={int(v): {int(c): int(((folds[idx] == v) & (sites[idx] == c)).sum()) for c in cen}
                                   for v in range(5)})
json.dump(out, open("planB_counts.json", "w"), indent=1, sort_keys=True)
for k, v in out.items():
    print(k, {x: v[x] for x in ("cases", "steps", "steps_per_case", "cases_per_centre", "state_S1_share", "cases_with_both_states")})
    print("   steps/centre", v["steps_per_centre"], "S1 share/centre", {c: round(x, 3) for c, x in v["state_S1_share_per_centre"].items()})
    print("   cases/fold", v["cases_per_fold"])

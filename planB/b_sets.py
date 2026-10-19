"""The three evaluation sets (plan §1), their descriptives, and the subsampling draws (plan §6).

S1: the 278-case representation set, all steps. S2: the 158-case primary set, all steps. S3: the 158-case primary
set, analysis-region steps (window-relative −30 … 44, ANALYSIS_REGION). Cases are indices into the 278-case order
(design.representation_cases); rows are step indices into each case's representation arrays.
"""
import numpy as np

from ss_benchmark import seeds
from ss_benchmark.constants import ANALYSIS_REGION, SEED_BOOTSTRAP

from .common import M_PER_CENTRE, T_STEPS


class Sets:
    def __init__(self, sites, folds, lens, prim_idx, prim_w, switch):
        self.sites, self.folds = np.asarray(sites), np.asarray(folds)
        self.lens, self.switch = np.asarray(lens), np.asarray(switch)
        self.prim_idx, self.prim_w = np.asarray(prim_idx), np.asarray(prim_w)
        self.w = dict(zip(self.prim_idx.tolist(), self.prim_w.tolist()))
        lo, hi = ANALYSIS_REGION
        for i, wi in self.w.items():
            if wi + lo < 0 or wi + hi >= self.lens[i]:
                raise ValueError(f"analysis region of case {i} outside its steps")

    def cases(self, s):
        return np.arange(len(self.lens)) if s == "S1" else self.prim_idx

    def rows(self, s, i):
        if s == "S3":
            lo, hi = ANALYSIS_REGION
            return np.arange(self.w[int(i)] + lo, self.w[int(i)] + hi + 1)
        return np.arange(self.lens[i])

    def steps_of(self, s):
        return lambda i: self.rows(s, i)

    def descriptives(self):
        out = {}
        cen = sorted(set(self.sites.tolist()))
        for s in ("S1", "S2", "S3"):
            idx = self.cases(s)
            n = np.array([len(self.rows(s, i)) for i in idx])
            st1 = np.array([(self.rows(s, i) >= self.switch[i]).sum() for i in idx])
            cs = self.sites[idx]
            out[s] = dict(cases=int(len(idx)), steps=int(n.sum()),
                          steps_per_case=dict(mean=float(n.mean()), min=int(n.min()), median=float(np.median(n)),
                                              max=int(n.max())),
                          cases_per_centre={str(c): int((cs == c).sum()) for c in cen},
                          steps_per_centre={str(c): int(n[cs == c].sum()) for c in cen},
                          state_S1_share=float(st1.sum() / n.sum()),
                          state_S1_share_per_centre={str(c): float(st1[cs == c].sum() / n[cs == c].sum()) for c in cen},
                          cases_per_fold={str(v): int((self.folds[idx] == v).sum()) for v in range(5)})
        return out

    def subsample(self, d, m=M_PER_CENTRE, T=T_STEPS):
        """Draw d (plan §6). Order of random calls (fixed): S1 cases per centre (sorted centres), S2 cases per centre,
        S1 steps per sampled case (increasing case index), S2 steps per sampled case. S3 = the S2 cases with their
        analysis-region rows. Returns {set: (case indices, {case: rows})}."""
        rng = seeds.rng(np.random.SeedSequence(SEED_BOOTSTRAP), f"planB:subsample:{d}")
        cen = sorted(set(self.sites.tolist()))
        prim = set(self.prim_idx.tolist())
        s1 = []
        for c in cen:
            cand = np.flatnonzero((self.sites == c) & (self.lens >= T))
            s1 += sorted(rng.choice(cand, m, replace=False).tolist())
        s2 = []
        for c in cen:
            cand = np.array(sorted(i for i in prim if self.sites[i] == c))
            s2 += sorted(rng.choice(cand, m, replace=False).tolist())
        s1, s2 = sorted(s1), sorted(s2)
        r1 = {i: np.sort(rng.choice(self.lens[i], T, replace=False)) for i in s1}
        r2 = {i: np.sort(rng.choice(self.lens[i], T, replace=False)) for i in s2}
        r3 = {i: self.rows("S3", i) for i in s2}
        return {"S1": (np.array(s1), r1), "S2": (np.array(s2), r2), "S3": (np.array(s2), r3)}


def real_sets(lens):
    from ss_benchmark import design
    cases = design.representation_cases()
    folds = design.representation_folds().loc[cases.case_id].to_numpy()
    D = design.load_real_design("primary")
    pos = {c: i for i, c in enumerate(cases.case_id)}
    prim = np.array([pos[c] for c in D.ids])
    if not (np.asarray(lens)[prim] == D.n_steps).all():
        raise ValueError("representation lengths differ from the design's step counts")
    return Sets(cases.center.to_numpy(), folds, lens, prim, D.window_start(),
                design.representation_switch_steps().loc[cases.case_id].to_numpy())


def placeholder_sets(rep_set, design_primary):
    pos = {c: i for i, c in enumerate(rep_set.case_id)}
    prim = np.array([pos[c] for c in design_primary.ids])
    return Sets(rep_set.centre.to_numpy(), rep_set.fold.to_numpy(), rep_set.n.to_numpy(), prim,
                design_primary.window_start(), rep_set.s.to_numpy())


def placeholder_m(sets):
    """PLACEHOLDER only: the plan's m = 28 capped at the smallest primary centre count of the PLACEHOLDER design."""
    cs = sets.sites[sets.prim_idx]
    return min(M_PER_CENTRE, min(int((cs == c).sum()) for c in np.unique(cs)))

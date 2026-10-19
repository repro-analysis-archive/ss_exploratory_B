"""Analyses (a) transport and (b) recoverability (plan §3), with the locked probes, folds and bootstrap unchanged.

(a) `transport_rowprobs` repeats the fold loop of the locked `checks.site_probe_case_predictions` for the S1 probe
(all 278 cases, all steps, the step-5 probe streams `E3:278:<key>-C`): the same training rows, groups, random streams
and learner calls. The only difference is that it keeps each held-out case's per-row probabilities, computed with one
`predict_proba` call on all of the case's steps (as step 5 does), so that the same probe can be evaluated on S1, S2 and
S3. A case's prediction on a set is the class with the largest mean probability over the set's rows.
(b) `recoverability` calls the locked `checks.site_probe_case_predictions` per set (folds restricted to the set).
BA with intervals: the locked `checks.ba_with_ci` (case bootstrap stratified by site, 2,000 resamples, root 20261008).
"""
import numpy as np

from ss_benchmark import checks
from ss_benchmark.constants import MLP_PROBE, PENALTY_GRID_E2, SEED_FOLDS
from ss_benchmark.learners import MLP, fit_multinomial_cv


def transport_rowprobs(rep_by_fold, case_sites, case_folds, lens, kind, tag, root=SEED_FOLDS, counter=None):
    """Per-row out-of-fold probabilities of the S1 probe for every case: (list of (n_i, C) arrays, class order)."""
    case_idx = np.arange(len(lens))
    classes = np.unique(np.asarray(case_sites))
    folds = np.asarray(case_folds)[case_idx]
    rowprob = [None] * len(case_idx)
    order = None
    steps = lambda i: np.arange(lens[i])                                          # noqa: E731
    for v in np.unique(folds):
        tr = case_idx[folds != v]
        te_pos = np.flatnonzero(folds == v)
        X = np.concatenate([rep_by_fold[v][i][steps(i)] for i in tr])
        y = np.concatenate([np.full(len(steps(i)), case_sites[i]) for i in tr])
        g = np.concatenate([np.full(len(steps(i)), i) for i in tr])
        rng = checks.probe_rng(tag, kind, int(v), root=root)
        if kind == "linear":
            model = fit_multinomial_cv(X, y, g, rng, PENALTY_GRID_E2)
            model_classes = model.classes
        else:
            yk = np.searchsorted(classes, y)
            model = MLP("multi", **MLP_PROBE).fit(X, yk, rng, g, n_classes=len(classes))
            model_classes = classes
        if counter is not None:
            counter.append((kind, int(v)))
        if order is None:
            order = np.asarray(model_classes)
        elif not np.array_equal(order, model_classes):
            raise RuntimeError("probe class order differs between folds")
        for p in te_pos:
            i = case_idx[p]
            rowprob[i] = model.predict_proba(rep_by_fold[v][i][steps(i)])
    return rowprob, order


def predict_from_rowprobs(rowprob, order, cases, rows_of):
    """Case predictions of the S1 probe on a set: argmax of the mean probability over the set's rows."""
    pred = np.empty(len(cases), dtype=order.dtype)
    for k, i in enumerate(cases):
        r = rows_of(i)
        P = rowprob[i] if len(r) == len(rowprob[i]) and (r == np.arange(len(rowprob[i]))).all() else rowprob[i][r]
        pred[k] = order[int(np.argmax(P.mean(0)))]
    return pred


def recoverability(rep_by_fold, case_sites, case_folds, cases, rows_of, kind, tag):
    """(b): the locked probe refitted within a set (folds restricted to the set) -> (true sites, predictions)."""
    return checks.site_probe_case_predictions(rep_by_fold, cases, case_sites, case_folds, rows_of, kind, tag)


def ba(sites, pred, name):
    return checks.ba_with_ci(np.asarray(sites), np.asarray(pred), name)


def ba_point(sites, pred):
    sites = np.asarray(sites)
    return checks.balanced_accuracy(sites, np.asarray(pred), classes=np.unique(sites))

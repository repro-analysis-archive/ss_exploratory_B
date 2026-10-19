"""PLACEHOLDER tests of the B components (criteria TB1-TB6 in B_IMPLEMENTATION_NOTES.md, fixed before running).

    taskset -c 18,19 env OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 PYTHONHASHSEED=0 \
        /home/user/.venvs/ss_extract/bin/python -m pytest -p no:cacheprovider -v tests/test_b_components.py
"""
import inspect
import json
import os

import numpy as np
import pandas as pd
import pytest

from planB import common as C


# --------------------------------------------------------------------------------------------- TB1: the sets --
def test_tb1_sets(ph):
    from planB import b_sets
    s = ph["sets"]
    rows = {k: sum(len(s.rows(k, i)) for i in s.cases(k)) for k in C.SETS}
    assert rows["S1"] == int(s.lens.sum()) and rows["S2"] == int(s.lens[s.prim_idx].sum()) and rows["S3"] == 75 * 158
    assert np.array_equal(s.cases("S2"), s.cases("S3")) and set(s.cases("S2")) <= set(s.cases("S1"))
    for i in s.cases("S3"):
        assert set(s.rows("S3", i)) <= set(s.rows("S2", i)) == set(s.rows("S1", i))
    d = s.descriptives()
    assert d["S1"]["cases"] == 278 and d["S2"]["cases"] == 158 and d["S3"]["steps"] == 11850
    st = sum(int((s.rows("S3", i) >= s.switch[i]).sum()) for i in s.cases("S3"))
    assert d["S3"]["state_S1_share"] == pytest.approx(st / 11850)
    bad_w = s.prim_w.copy()
    bad_w[0] = 10
    with pytest.raises(ValueError):
        b_sets.Sets(s.sites, s.folds, s.lens, s.prim_idx, bad_w, s.switch)


# -------------------------------------------------------------------------- TB2: transport vs refit separation --
def test_tb2_transport_equals_locked_and_fits_once(ph, s1_linear):
    from ss_benchmark import checks
    from planB import b_probes
    s = ph["sets"]
    rp, order, fits = s1_linear
    assert sorted(fits) == [("linear", v) for v in range(5)]
    pa = b_probes.predict_from_rowprobs(rp, order, s.cases("S1"), s.steps_of("S1"))
    _, pl = checks.site_probe_case_predictions(ph["RC"], s.cases("S1"), s.sites, s.folds, s.steps_of("S1"), "linear",
                                               "E3:278:P-C")
    assert np.array_equal(pa, pl)
    for set_name in ("S2", "S3"):                                   # (a) on S2 / S3: the same stored probabilities
        p = b_probes.predict_from_rowprobs(rp, order, s.cases(set_name), s.steps_of(set_name))
        hand = [order[int(np.argmax(rp[i][s.rows(set_name, i)].mean(0)))] for i in s.cases(set_name)]
        assert list(p) == hand


def test_tb2_refit_uses_only_own_set(ph, s1_linear):
    from planB import b_probes
    s = ph["sets"]
    tag = C.probe_tag("b", "S2", "P")
    assert tag == "E3:planB-S2:P-C"
    base = b_probes.recoverability(ph["RC"], s.sites, s.folds, s.cases("S2"), s.steps_of("S2"), "linear", tag)
    nonprim = next(i for i in range(len(s.lens)) if i not in set(s.prim_idx) and s.folds[i] != 0)
    RC2 = [list(r) for r in ph["RC"]]
    for v in range(5):
        RC2[v][nonprim] = RC2[v][nonprim] + 3.0
    alt_b = b_probes.recoverability(RC2, s.sites, s.folds, s.cases("S2"), s.steps_of("S2"), "linear", tag)
    assert np.array_equal(base[1], alt_b[1])                       # (b)-S2 does not use non-S2 cases
    rp2, order2 = b_probes.transport_rowprobs(RC2, s.sites, s.folds, s.lens, "linear", C.probe_tag("a", "S1", "P"))
    rp, order, _ = s1_linear
    i0 = next(i for i in s.cases("S2") if s.folds[i] == 0)           # held out in fold 0; probe trained with nonprim
    assert not np.array_equal(rp[i0], rp2[i0])                      # (a) uses the S1 probe, trained on all S1 cases


# ---------------------------------------------------------------------------------- TB3: bootstrap and names --
def test_tb3_bootstrap_determinism_and_names(ph, s1_linear):
    from planB import b_probes
    s = ph["sets"]
    rp, order, _ = s1_linear
    p = b_probes.predict_from_rowprobs(rp, order, s.cases("S2"), s.steps_of("S2"))
    name = C.boot_name("a", "S2", "P", "linear")
    r1, r2 = b_probes.ba(s.sites[s.cases("S2")], p, name), b_probes.ba(s.sites[s.cases("S2")], p, name)
    assert r1 == r2 and set(r1) >= {"ba", "lo_2p5", "hi_97p5", "upper_one_sided_95", "n_cases"}
    assert C.boot_name("a", "S1", "P", "mlp") == C.boot_name("b", "S1", "P", "mlp") == "E3:278:P-C:mlp"
    assert C.boot_name("b", "S3", "REF", "linear") == "E3:primary:REF-C:linear"
    assert C.boot_name("a", "S3", "S", "linear") == "planB:a:S3:S-C:linear"
    assert C.boot_name("b", "S2", "S", "mlp") == "planB:b:S2:S-C:mlp"
    assert C.probe_tag("b", "S3", "P") == "E3:primary:P-C" and C.probe_tag("a", "S1", "S") == "E3:278:S-C"


# ---------------------------------------------------------------------------------------------------- TB4: C-B0 --
def test_tb4_cb0_passes_and_detects(ph):
    """On the non-erased PLACEHOLDER PCA features (R), on which the linear probe separates sites: with the erased
    features the linear S1 probe predicts one site for every case, so no input change can alter a prediction."""
    from ss_benchmark import checks
    from planB import b_probes, b_stage
    s, R = ph["sets"], ph["R"]
    st, pl = checks.site_probe_case_predictions(R, s.cases("S1"), s.sites, s.folds, s.steps_of("S1"), "linear",
                                                "E3:278:P-C")
    ref = checks.ba_with_ci(st, pl, "E3:278:P-C:linear")           # exactly what the locked e3_site computes
    rp, order = b_probes.transport_rowprobs(R, s.sites, s.folds, s.lens, "linear", "E3:278:P-C")
    pa = b_probes.predict_from_rowprobs(rp, order, s.cases("S1"), s.steps_of("S1"))
    assert len(set(pa.tolist())) > 1                               # predictions vary on these features
    cell = b_stage.cell(s, "a", "S1", "P", "linear", s.sites[s.cases("S1")], pa)
    assert b_stage.cb0_check(cell, ref, "E3_site_278", "P", "linear")["identical"]
    bumped = dict(ref, ba=float(np.nextafter(ref["ba"], np.inf)))
    assert not b_stage.cb0_check(cell, bumped, "E3_site_278", "P", "linear")["identical"]
    R2 = [list(r) for r in R]                                       # perturbed input changing a case prediction
    i = next(i for i in s.cases("S1") if s.folds[i] == 0 and pa[i] == s.sites[i])
    j = next(j for j in s.cases("S1") if s.sites[j] != s.sites[i] and s.lens[j] >= s.lens[i])
    R2[0][i] = R2[0][j][:s.lens[i]].copy()
    rp2, order2 = b_probes.transport_rowprobs(R2, s.sites, s.folds, s.lens, "linear", "E3:278:P-C")
    pa2 = b_probes.predict_from_rowprobs(rp2, order2, s.cases("S1"), s.steps_of("S1"))
    assert not np.array_equal(pa2, pa)
    cell2 = b_stage.cell(s, "a", "S1", "P", "linear", s.sites[s.cases("S1")], pa2)
    assert not b_stage.cb0_check(cell2, ref, "E3_site_278", "P", "linear")["identical"]


# ---------------------------------------------------------------------------------------------- TB5: sensitivity --
def test_tb5_subsample(ph):
    from planB import b_sets, b_stage
    s = ph["sets"]
    m = b_sets.placeholder_m(s)
    a, b, c = s.subsample(3, m=m), s.subsample(3, m=m), s.subsample(4, m=m)
    for k in C.SETS:
        assert np.array_equal(a[k][0], b[k][0]) and all(np.array_equal(a[k][1][i], b[k][1][i]) for i in a[k][0])
        cs = s.sites[a[k][0]]
        assert all(int((cs == ce).sum()) == m for ce in np.unique(s.sites))
        assert all(len(r) == 75 for r in a[k][1].values())
    assert np.array_equal(a["S2"][0], a["S3"][0])
    assert not np.array_equal(a["S1"][0], c["S1"][0])
    assert (s.lens[a["S1"][0]] >= 75).all()
    assert all(np.array_equal(a["S3"][1][i], s.rows("S3", i)) for i in a["S3"][0])
    assert C.sens_tag(7, "S2", "P") == "E3:planB-sens-7-S2:P-C"
    assert "sens_tag(d, s, a.key)" in inspect.getsource(b_stage.stage_sens)


# ---------------------------------------------------------------------------------------------------- TB6: report --
def _fake_outputs(out, keys=C.KEYS):
    rng = np.random.default_rng(0)
    for k in keys:
        cells = []
        for an in C.ANALYSES:
            for kind in C.KINDS:
                for st in C.SETS:
                    ba = float(rng.uniform(0.2, 0.6))
                    cells.append(dict(key=k, analysis=an, probe=kind, set=st, cases=158, rows=1000, ba=ba,
                                      lo_2p5=ba - 0.05, hi_97p5=ba + 0.05, upper_one_sided_95=ba + 0.04, n_cases=158,
                                      boot_name=C.boot_name(an, st, k, kind), probe_streams="x"))
        json.dump(dict(cells=cells), open(os.path.join(out, f"main_{k}.json"), "w"))
        chk = [dict(key=k, probe="linear", set="S1", reference="E3_site_278.linear", fields={}, identical=True,
                    b_values=dict(ba=0.25, upper_one_sided_95=0.3), reference_values=dict(ba=0.25, upper_one_sided_95=0.3))]
        json.dump(dict(passed=True, checks=chk, cells=cells[:2]), open(os.path.join(out, f"cb0_{k}.json"), "w"))
        rows = [dict(draw=d, key=k, analysis=an, probe=kind, set=st, cases=112, ba=float(rng.uniform(0.2, 0.6)))
                for d in range(3) for an in C.ANALYSES for kind in C.KINDS for st in C.SETS]
        json.dump(dict(rows=rows, m=28), open(os.path.join(out, f"sens_{k}.json"), "w"))


def test_tb6_report(ph, tmp_path, monkeypatch):
    from planB import b_report
    _fake_outputs(str(tmp_path))
    rec = tmp_path / "rec"
    b_report.write_records(str(tmp_path), str(rec), list(C.KEYS), ph["sets"].descriptives(), True)
    main = pd.read_csv(rec / "b_main.csv")
    jd = pd.read_csv(rec / "b_judgements.csv")
    text = (rec / "B_REPORT.md").read_text()
    assert len(main) == 36 and len(jd) == 3 * 2 * 2 * 3
    assert set(jd.pair) == {"S1->S2", "S2->S3", "S1->S3"}
    assert all(s.startswith("the judgement ") for s in jd.statement)
    assert "does not change the E3 gate, §13, any family verdict or any protocol result" in text
    assert "not why" in text
    monkeypatch.setattr(b_report, "PLAN_COMMIT", "because")
    with pytest.raises(AssertionError):
        b_report.write_records(str(tmp_path), str(tmp_path / "rec2"), list(C.KEYS), ph["sets"].descriptives(), True)

"""Stages of the B run, each a separate process started by the orchestrator (the step-5 interpreter and threads).

    python -m planB.b_stage phref  --locked SNAP --out DIR --key K              (PLACEHOLDER only: C-B0 reference)
    python -m planB.b_stage cb0    --locked SNAP --out DIR --key K [--placeholder]
    python -m planB.b_stage main   --locked SNAP --out DIR --key K [--placeholder]
    python -m planB.b_stage sens   --locked SNAP --out DIR --key K [--placeholder] [--draws D]
    python -m planB.b_stage report --locked SNAP --out DIR --records DIR [--placeholder] [--keys LIST]
"""
import argparse
import json
import os
import sys

import numpy as np

from .common import (KINDS, N_DRAWS, STEP5_DIR, boot_name, json_read, json_write, probe_tag, sens_tag, sha256_file,
                     use_locked)

C0_FIELDS = ("ba", "lo_2p5", "hi_97p5", "upper_one_sided_95", "n_cases")


def load(a, key):
    """(sets, RC) for a key: real = step-5 reps_full_<key>.npz (RC_v, the protocol LEACE features); PLACEHOLDER =
    the locked placeholder.build()."""
    from . import b_sets
    if a.placeholder:
        from ss_benchmark import placeholder as ph
        rep_set, designs, _, _, full = ph.build(set_names=("primary",))
        return b_sets.placeholder_sets(rep_set, designs["primary"]), full[key]["R-C"]
    z = np.load(os.path.join(a.step5_dir, f"reps_full_{key}.npz"), allow_pickle=False)
    lens = z["lengths"]
    cuts = np.cumsum(lens)[:-1]
    RC = [np.split(z[f"RC_{v}"], cuts) for v in range(5)]
    return b_sets.real_sets(lens), RC


def save_rowprobs(path, rowprob, order):
    np.savez(path + ".tmp.npz", rows=np.concatenate(rowprob), lengths=np.array([len(x) for x in rowprob]),
             order=np.asarray(order))
    os.replace(path + ".tmp.npz", path)


def load_rowprobs(path):
    z = np.load(path, allow_pickle=False)
    cuts = np.cumsum(z["lengths"])[:-1]
    return np.split(z["rows"], cuts), z["order"]


def cell(sets, analysis, set_name, key, kind, sites, pred):
    from .b_probes import ba
    r = ba(sites, pred, boot_name(analysis, set_name, key, kind))
    idx = sets.cases(set_name)
    streams = probe_tag("a", "S1", key) if analysis == "a" else probe_tag("b", set_name, key)
    return dict(key=key, analysis=analysis, probe=kind, set=set_name, cases=int(len(idx)),
                rows=int(sum(len(sets.rows(set_name, i)) for i in idx)),
                boot_name=boot_name(analysis, set_name, key, kind), probe_streams=streams, **r)


def stage_phref(a):
    """PLACEHOLDER stand-in for the committed step-5 E3 values: the locked e3_site on the PLACEHOLDER features."""
    from ss_benchmark import checks
    sets, RC = load(a, a.key)
    ref = {"E3_site_278": checks.e3_site(RC, sets.cases("S1"), sets.sites, sets.folds, sets.steps_of("S1"),
                                         f"278:{a.key}-C"),
           "E3_site_primary": checks.e3_site(RC, sets.cases("S3"), sets.sites, sets.folds, sets.steps_of("S3"),
                                             f"primary:{a.key}-C")}
    json_write(os.path.join(a.out, f"phref_{a.key}.json"), ref)
    return 0


def reference(a, key):
    if a.placeholder:
        return json_read(os.path.join(a.out, f"phref_{key}.json"))
    return json.load(open(os.path.join(a.locked, "results", "step5", "checks.json")))[key]


def cb0_check(c, r, refname, key, kind):
    """Exact comparison (as JSON text) of a B cell with its step-5 reference (plan §5)."""
    same = {f: json.dumps(c[f]) == json.dumps(r[f]) for f in C0_FIELDS}
    return dict(key=key, probe=kind, set=c["set"], reference=f"{refname}.{kind}", fields=same,
                identical=all(same.values()), b_values={f: c[f] for f in C0_FIELDS},
                reference_values={f: r[f] for f in C0_FIELDS})


def stage_cb0(a):
    """Control C-B0 (plan §5): (a)/(b)-S1 must reproduce E3_site_278 and (b)-S3 E3_site_primary exactly."""
    from .b_probes import predict_from_rowprobs, recoverability, transport_rowprobs
    sets, RC = load(a, a.key)
    ref = reference(a, a.key)
    cells, checks_ = [], []
    for kind in KINDS:
        rowprob, order = transport_rowprobs(RC, sets.sites, sets.folds, sets.lens, kind, probe_tag("a", "S1", a.key))
        save_rowprobs(os.path.join(a.out, f"rowprob_{a.key}_{kind}.npz"), rowprob, order)
        idx = sets.cases("S1")
        pred = predict_from_rowprobs(rowprob, order, idx, sets.steps_of("S1"))
        c1 = cell(sets, "a", "S1", a.key, kind, sets.sites[idx], pred)
        cells += [c1, dict(c1, analysis="b")]
        s, p = recoverability(RC, sets.sites, sets.folds, sets.cases("S3"), sets.steps_of("S3"), kind,
                              probe_tag("b", "S3", a.key))
        c3 = cell(sets, "b", "S3", a.key, kind, s, p)
        cells.append(c3)
        for c, refname in ((c1, "E3_site_278"), (c3, "E3_site_primary")):
            checks_.append(cb0_check(c, ref[refname][kind], refname, a.key, kind))
    passed = all(x["identical"] for x in checks_)
    json_write(os.path.join(a.out, f"cb0_{a.key}.json"), dict(passed=passed, checks=checks_, cells=cells,
                                                              rowprob_sha256={k: sha256_file(os.path.join(
                                                                  a.out, f"rowprob_{a.key}_{k}.npz")) for k in KINDS}))
    print(f"C-B0 {a.key}: {'passed' if passed else 'FAILED'}", flush=True)
    return 0 if passed else 4


def stage_main(a):
    """The remaining cells: (a)-S2, (a)-S3 from the S1 probe's per-row probabilities; (b)-S2 refitted in S2."""
    from .b_probes import predict_from_rowprobs, recoverability
    sets, RC = load(a, a.key)
    c0 = json_read(os.path.join(a.out, f"cb0_{a.key}.json"))
    if not (c0 and c0["passed"]):
        raise SystemExit("C-B0 has not passed for this key")
    cells = list(c0["cells"])
    for kind in KINDS:
        p = os.path.join(a.out, f"rowprob_{a.key}_{kind}.npz")
        if sha256_file(p) != c0["rowprob_sha256"][kind]:
            raise SystemExit(f"{p} changed since C-B0")
        rowprob, order = load_rowprobs(p)
        for s in ("S2", "S3"):
            idx = sets.cases(s)
            cells.append(cell(sets, "a", s, a.key, kind, sets.sites[idx],
                              predict_from_rowprobs(rowprob, order, idx, sets.steps_of(s))))
        s_, p_ = recoverability(RC, sets.sites, sets.folds, sets.cases("S2"), sets.steps_of("S2"), kind,
                                probe_tag("b", "S2", a.key))
        cells.append(cell(sets, "b", "S2", a.key, kind, s_, p_))
    json_write(os.path.join(a.out, f"main_{a.key}.json"), dict(cells=cells))
    return 0


def stage_sens(a):
    """Plan §6: D draws; (a) the S1 probe's cached per-row probabilities; (b) refits within each subsampled set."""
    from . import b_sets
    from .b_probes import ba_point, predict_from_rowprobs, recoverability
    sets, RC = load(a, a.key)
    m = b_sets.placeholder_m(sets) if a.placeholder else b_sets.M_PER_CENTRE
    rp = {k: load_rowprobs(os.path.join(a.out, f"rowprob_{a.key}_{k}.npz")) for k in KINDS}
    path = os.path.join(a.out, f"sens_{a.key}.json")
    done = json_read(path, {"rows": [], "m": m})
    have = {r["draw"] for r in done["rows"]}
    for d in range(a.draws):
        if d in have:
            continue
        sub = sets.subsample(d, m=m)
        rows = []
        for s, (idx, rows_of) in sub.items():
            for kind in KINDS:
                pa = predict_from_rowprobs(*rp[kind], idx, lambda i: rows_of[int(i)])
                rows.append(dict(draw=d, key=a.key, analysis="a", probe=kind, set=s, cases=len(idx),
                                 ba=ba_point(sets.sites[idx], pa)))
                st, pb = recoverability(RC, sets.sites, sets.folds, idx, lambda i: rows_of[int(i)], kind,
                                        sens_tag(d, s, a.key))
                rows.append(dict(draw=d, key=a.key, analysis="b", probe=kind, set=s, cases=len(idx),
                                 ba=ba_point(st, pb)))
        done["rows"] += rows
        json_write(path, done)
        print(f"sensitivity {a.key}: draw {d + 1}/{a.draws} done", flush=True)
    return 0


def stage_report(a):
    from . import b_report
    keys = a.keys.split(",")
    sets, _ = load(a, keys[0])
    b_report.write_records(a.out, a.records, keys, sets.descriptives(), a.placeholder)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=("phref", "cb0", "main", "sens", "report"))
    ap.add_argument("--locked", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--key")
    ap.add_argument("--keys", default="P,S,REF")
    ap.add_argument("--records")
    ap.add_argument("--step5-dir", default=STEP5_DIR)
    ap.add_argument("--placeholder", action="store_true")
    ap.add_argument("--draws", type=int, default=N_DRAWS)
    a = ap.parse_args(argv)
    use_locked(a.locked)
    return {"phref": stage_phref, "cb0": stage_cb0, "main": stage_main, "sens": stage_sens,
            "report": stage_report}[a.stage](a)


if __name__ == "__main__":
    sys.exit(main())

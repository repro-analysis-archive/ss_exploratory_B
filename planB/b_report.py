"""B records and report (plan §7): main table, judgement statements, C-B0, descriptives, sensitivity summary.

Wording ceiling: B identifies where the judgement changes, not why. Only "the judgement changes between Sx and Sy" /
"does not change" is stated; banned words are checked before the report is written.
"""
import json
import os
import re

import numpy as np
import pandas as pd

from .common import BOUNDARY, KINDS, PLAN_COMMIT, SETS, json_read, json_write

BANNED = (r"\bmechanism", r"\bcause\b", r"\bbecause\b", r"\bexplains?\b", r"\bdue to\b", r"SUPPORTED", r"CONTRADICTED",
          r"\beliminated\b", r"equivalent to chance")
PAIRS = (("S1", "S2"), ("S2", "S3"), ("S1", "S3"))


def main_table(out, keys):
    rows = []
    for k in keys:
        for c in json_read(os.path.join(out, f"main_{k}.json"))["cells"]:
            rows.append({x: c[x] for x in ("key", "analysis", "probe", "set", "cases", "rows", "ba", "lo_2p5",
                                           "hi_97p5", "upper_one_sided_95", "boot_name", "probe_streams")}
                        | {"exceeds_boundary_0.35": bool(c["upper_one_sided_95"] > BOUNDARY)})
    df = pd.DataFrame(rows)
    df["_a"] = df.analysis.map({"a": 0, "b": 1})
    df["_k"] = df.key.map({k: i for i, k in enumerate(keys)})
    df = df.sort_values(["_k", "_a", "probe", "set"]).drop(columns=["_a", "_k"]).reset_index(drop=True)
    assert len(df) == len(keys) * 2 * len(KINDS) * len(SETS), len(df)
    return df


def judgements(df):
    rows = []
    for (k, an, pr), g in df.groupby(["key", "analysis", "probe"], sort=False):
        ex = dict(zip(g.set, g["exceeds_boundary_0.35"]))
        for x, y in PAIRS:
            changes = ex[x] != ex[y]
            rows.append(dict(key=k, analysis=an, probe=pr, pair=f"{x}->{y}", exceeds_x=ex[x], exceeds_y=ex[y],
                             statement=f"the judgement {'changes' if changes else 'does not change'} between {x} and {y}"))
    return pd.DataFrame(rows)


def sensitivity(out, keys):
    draws = pd.DataFrame([r for k in keys for r in json_read(os.path.join(out, f"sens_{k}.json"))["rows"]])
    summ = (draws.groupby(["key", "analysis", "probe", "set"]).ba
            .agg(draws="count", median="median", p2_5=lambda x: float(np.percentile(x, 2.5)),
                 p97_5=lambda x: float(np.percentile(x, 97.5)), min="min", max="max").reset_index())
    m = {k: json_read(os.path.join(out, f"sens_{k}.json"))["m"] for k in keys}
    return draws, summ, m


def _f(x):
    return f"{x:.3f}"


def report(df, jd, c0, desc, sdraws, ssum, m, placeholder):
    L = [("# PLACEHOLDER — " if placeholder else "# ") + "Exploratory analysis B: where the E3-site judgement changes "
         "across evaluation sets", ""]
    if placeholder:
        L += ["> **PLACEHOLDER — synthetic test output, not results.**", ""]
    L += [f"* **Plan:** `EXPLORATORY_PLAN_B.md`, commit `{PLAN_COMMIT}` (OSF https://osf.io/g9ymw, addendum to "
          "https://osf.io/5c627).",
          "* **Status:** exploratory. B does not change the E3 gate, §13, any family verdict or any protocol result; "
          "the primary E3-site outcome of step 5 stands.",
          "* **Ceiling:** B identifies where the judgement changes, not why: between the sets, case composition, "
          "centre mix, the state distribution, step counts and the fit / evaluation distribution change together.",
          f"* **Judgement:** whether the one-sided 95 % upper bound of the case-level balanced accuracy exceeds the "
          f"prespecified boundary {BOUNDARY} (§5.3); for the linear probe this is the E3-site rule applied "
          "descriptively, for the MLP probe the step-5 reporting comparison.", ""]
    L += ["## Control C-B0", "", "| key | probe | set | reference | identical | B: BA / upper | step 5: BA / upper |",
          "|---|---|---|---|---|---|---|"]
    for k, c in c0.items():
        for x in c["checks"]:
            L.append(f"| {k} | {x['probe']} | {x['set']} | {x['reference']} | {'yes' if x['identical'] else 'NO'} | "
                     f"{_f(x['b_values']['ba'])} / {_f(x['b_values']['upper_one_sided_95'])} | "
                     f"{_f(x['reference_values']['ba'])} / {_f(x['reference_values']['upper_one_sided_95'])} |")
    L += ["", "## Descriptives per set", "", "| | " + " | ".join(SETS) + " |", "|---|" + "---:|" * len(SETS)]
    for lab, f in (("cases", lambda d: d["cases"]), ("steps (rows)", lambda d: d["steps"]),
                   ("steps per case: mean / median / min / max", lambda d: "{mean:.1f} / {median:g} / {min} / {max}"
                    .format(**d["steps_per_case"])),
                   ("cases per centre", lambda d: " / ".join(f"{c}: {n}" for c, n in d["cases_per_centre"].items())),
                   ("share of rows with S = 1", lambda d: _f(d["state_S1_share"])),
                   ("share with S = 1 by centre", lambda d: " / ".join(f"{c}: {v:.3f}" for c, v in
                                                                         d["state_S1_share_per_centre"].items())),
                   ("cases per fold", lambda d: " / ".join(str(n) for n in d["cases_per_fold"].values()))):
        L.append(f"| {lab} | " + " | ".join(str(f(desc[s])) for s in SETS) + " |")
    L += ["", "## Balanced accuracy per representation × analysis × probe × set", "",
          "(a) transport: the S1 probe (fitted as in E3) evaluated on each set; (b) recoverability: the probe "
          "specification refitted within each set. Reported separately; never pooled or contrasted.", "",
          "| key | analysis | probe | set | cases | rows | BA | 95 % interval | one-sided 95 % upper | exceeds 0.35 |",
          "|---|---|---|---|---:|---:|---:|---|---:|---|"]
    for _, r in df.iterrows():
        L.append(f"| {r.key} | ({r.analysis}) | {r.probe} | {r.set} | {r.cases} | {r.rows} | {_f(r.ba)} | "
                 f"[{_f(r.lo_2p5)}, {_f(r.hi_97p5)}] | {_f(r.upper_one_sided_95)} | "
                 f"{'yes' if r['exceeds_boundary_0.35'] else 'no'} |")
    L += ["", "## Where the judgement changes", "", "| key | analysis | probe | S1→S2 | S2→S3 | S1→S3 |",
          "|---|---|---|---|---|---|"]
    for (k, an, pr), g in jd.groupby(["key", "analysis", "probe"], sort=False):
        st = dict(zip(g.pair, g.statement))
        L.append(f"| {k} | ({an}) | {pr} | " + " | ".join(st[p].replace("the judgement ", "") for p in
                                                          ("S1->S2", "S2->S3", "S1->S3")) + " |")
    L += ["", "## Exploratory sensitivity (descriptive; no bootstrap, no judgement)", "",
          f"Equal cases per centre (m = {sorted(set(m.values()))}) and 75 steps per case in S1–S3; "
          f"{int(ssum['draws'].max())} draws (seed SeedSequence(20261008) child \"planB:subsample:<d>\").", "",
          "| key | analysis | probe | set | draws | median BA | 2.5–97.5 % across draws | min–max |",
          "|---|---|---|---|---:|---:|---|---|"]
    for _, r in ssum.iterrows():
        L.append(f"| {r.key} | ({r.analysis}) | {r.probe} | {r.set} | {r.draws} | {_f(r['median'])} | "
                 f"{_f(r.p2_5)}–{_f(r.p97_5)} | {_f(r['min'])}–{_f(r['max'])} |")
    text = "\n".join(L) + "\n"
    for pat in BANNED:
        assert not re.search(pat, text), f"wording rule: {pat!r} must not appear in the B report"
    return text


def write_records(out, rec, keys, desc, placeholder):
    os.makedirs(rec, exist_ok=True)
    c0 = {k: json_read(os.path.join(out, f"cb0_{k}.json")) for k in keys}
    if not all(c and c["passed"] for c in c0.values()):
        raise SystemExit("C-B0 did not pass for every key")
    df = main_table(out, keys)
    jd = judgements(df)
    sdraws, ssum, m = sensitivity(out, keys)
    df.to_csv(os.path.join(rec, "b_main.csv"), index=False)
    jd.to_csv(os.path.join(rec, "b_judgements.csv"), index=False)
    sdraws.to_csv(os.path.join(rec, "b_sensitivity_draws.csv"), index=False)
    ssum.to_csv(os.path.join(rec, "b_sensitivity_summary.csv"), index=False)
    json_write(os.path.join(rec, "b_cb0.json"), {k: {x: v for x, v in c.items() if x != "cells"} for k, c in c0.items()})
    json_write(os.path.join(rec, "b_descriptives.json"), desc)
    open(os.path.join(rec, "B_REPORT.md"), "w").write(report(df, jd, c0, desc, sdraws, ssum, m, placeholder))
    return rec

# B implementation notes

* **Written:** 2026-10-19, under `CC_TASK_SS_B_impl_v1.md`.
* **No B result existed when these notes were written.**
  * No B computation has been run on real data.
  * The preflight reads only file hashes and counts.
  * No step-6 or step-7 result and no X result was opened.
* **Governing document:** `EXPLORATORY_PLAN_B.md` (commit `e1c27b4`; OSF https://osf.io/g9ymw). The plan governs.
* **What this file records:** where the plan left a point open, the choice made and why.
* **What no choice changes:** sets, analyses, probes, bootstrap, seeds, subsampling or wording rules.

## Choices

**NB1. S1 in (a) and (b) is computed once.**
* The two are the same computation: the S1 probe evaluated on S1 (plan §3, and §8 "the S1 probes (shared)").
* B computes it with its transport loop and reports it for both analyses.
* That loop repeats the fold loop of the locked `site_probe_case_predictions`: the same training rows, groups, streams and learner calls.
* **Checks of the equivalence:**
  * a PLACEHOLDER test checks that the loop's S1 case predictions equal the locked function's, bit for bit;
  * control C-B0 compares the S1 values with the committed step-5 `E3_site_278`, which the locked function produced.

**NB2. Per-row probabilities for transport (a).**
* Each held-out case's probabilities are computed with one `predict_proba` call on all of its steps, as step 5 does. They are then averaged over the set's rows (all steps for S1 and S2; the analysis-region rows for S3).
* S1 predictions are therefore step 5's exactly. For S3 the region rows are a subset of the case's rows.
* The probabilities are saved (`rowprob_<key>_<probe>.npz`) and hashed. The sensitivity analysis (a) re-uses them (plan §6: "not refitted").

**NB3. C-B0 runs first.**
* C-B0 runs for every key before any other B cell.
* Fields compared, exactly as JSON text: `ba`, `lo_2p5`, `hi_97p5`, `upper_one_sided_95`, `n_cases`.
* Reference: the committed `results/step5/checks.json` at `2880d73`. Its SHA-256 equals the committed `step5_manifest.json` entry, which the preflight checks.
* If any field differs, the stage exits 4, the runner stops with the reason, and no further stage runs.

**NB4. Stage environment.**
* The step-5 checks interpreter, `/home/user/.venvs/ss_extract/bin/python`. Its library versions (Python 3.11.14, numpy 2.3.5, scipy 1.17.0, scikit-learn 1.6.1, pandas 3.0.1) are checked by the preflight.
* `OMP_NUM_THREADS = MKL_NUM_THREADS = OPENBLAS_NUM_THREADS = 6`, `OMP_WAIT_POLICY = PASSIVE`, `PYTHONHASHSEED = 0`.
* Pinned to CPUs 0–5 by default. Pinning does not affect the numbers.
* A real run refuses any other thread count. The orchestrator itself (no numerics) runs on the base Python.

**NB5. "Refuses while the X1/X2 runner is still running."**
* B refuses if any process runs `xplore.x_orchestrate`, `xplore.x_units` or `xplore.x_stage`.
* PLACEHOLDER tests and smoke runs may pass `--ignore-x-running`, so they can run while X1/X2 runs. A real run refuses this option.

**NB6. Main repository.** HEAD must be `2880d73` or a descendant without changes under `ss_benchmark/`, `data_audit/lead/out/` or `results/step5/` (as X1/X2's N2). The locked snapshot is always taken from `2880d73`.

**NB7. Subsampling draws (plan §6).**
* Generator: `seeds.rng(SeedSequence(20261008), "planB:subsample:<d>")`.
* Fixed order of random calls:
  1. S1 cases per centre (centres in increasing order);
  2. S2 cases per centre;
  3. S1 steps per sampled case (increasing case index);
  4. S2 steps per sampled case.
* Each call is `rng.choice(..., replace=False)`. S3 takes the S2 cases with their region rows.
* m = 28. In PLACEHOLDER runs only, m is capped at the smallest primary centre count of the PLACEHOLDER design, which is also 28 there.

**NB8. Balanced accuracy.**
* Intervals: the locked `checks.ba_with_ci`. Its classes are the sites of the evaluated cases, and the case order is that of the set, so the stratified case bootstrap is step 5's.
* Sensitivity point estimates: `checks.balanced_accuracy` with the same classes, without bootstrap (plan §6).

**NB9. Records.**
* The runner commits exactly 8 files to `results_B/`, records only, with the parent verified as `--expect-commit`:
  * `B_REPORT.md`;
  * `b_main.csv`, `b_judgements.csv`;
  * `b_sensitivity_draws.csv`, `b_sensitivity_summary.csv`;
  * `b_cb0.json`, `b_descriptives.json`, `b_run_record.json`.
* The per-row probabilities stay in the output folder; their SHA-256 is in `b_run_record.json`.

**NB10. Paths and order.**
* Outputs go to `/media/user/LaCie/medvideo_gate/ss_exploratory_B/`.
* Stages run key by key (P, S, REF) in this order: C-B0 for all keys, then the main cells, then sensitivity, then the records.
* Each stage is recorded when it completes. A stopped run resumes at the first unfinished stage, and the sensitivity stage resumes per draw.

**NB11. PLACEHOLDER reference for C-B0.** No committed step-5 values exist for PLACEHOLDER features. Tests and smoke runs therefore use as the reference the locked `checks.e3_site` run on the PLACEHOLDER features (`phref`), with the step-5 tags `278:<key>-C` and `primary:<key>-C`.

**NB12. Wording check.** `b_report` refuses to write a report containing "mechanism", "cause", "because", "explain(s)", "due to", "SUPPORTED", "CONTRADICTED", "eliminated" or "equivalent to chance".

## Test criteria (fixed before any test was run)

**TB1. Set construction (PLACEHOLDER).**
* Row counts: S1 = Σ n_i over the 278 cases, S2 = Σ n_i over the 158 primary cases, S3 = 75 × 158.
* S3 ⊂ S2 ⊂ S1 as (case, row) pairs; S2 and S3 have the same cases.
* `descriptives()` matches a direct count.
* A region outside a case's steps raises an error.

**TB2. Transport vs refit separation.**
* (a)'s S1 case predictions equal the locked `site_probe_case_predictions` (tag `E3:278:P-C`), bit for bit.
* (a) fits exactly 5 probes per probe type (one per fold), and its S2 / S3 predictions come from those probes' stored per-row probabilities.
* (b)-S2 equals a direct locked call with tag `E3:planB-S2:P-C`.
* Changing the features of one non-primary case changes (a)'s S2 per-row probabilities but leaves (b)-S2 unchanged.

**TB3. Bootstrap determinism and stream names.**
* Two runs of a cell give identical BA, intervals and upper bound.
* The names follow the plan: S1 → `E3:278:<key>-C:<probe>`; (b)-S3 → `E3:primary:<key>-C:<probe>`; otherwise `planB:<a|b>:<S2|S3>:<key>-C:<probe>`.

**TB4. C-B0.** *(Revised before any test was run; see the revision note below.)*
* Against the locked reference on PLACEHOLDER features (linear probe), C-B0 passes.
* Shifting one reference value by one ulp makes it fail.
* A perturbed input that changes at least one case-level prediction makes it fail. The perturbation: the fold-0 features of one held-out S1 case are replaced by those of a case from another centre.

*Revision note.* The criterion first committed in `f6b4f39` required a 1e-6 change of one feature value to make C-B0 fail. C-B0 compares the balanced-accuracy-level numbers of step 5 (`ba`, the bounds, `n_cases`), which are the only step-5 E3 values committed. A change too small to alter any case's predicted site cannot change them. Integrity of the inputs themselves is checked separately, by the preflight's SHA-256 comparison with the committed step-5 manifest. The criterion was therefore corrected before any test was run.

**TB5. Sensitivity draws.**
* Deterministic for a given d; different for different d.
* Exactly m cases per centre in every set and 75 rows per case; S3 cases = S2 cases.
* S1 draws exclude cases with fewer than 75 steps.
* (b) uses tag `E3:planB-sens-<d>-<set>:<key>-C`.

**TB6. Report.**
* 36 main rows (3 keys × 2 analyses × 2 probes × 3 sets).
* Judgement statements for S1→S2, S2→S3 and S1→S3 per key × analysis × probe.
* No banned word; the statement that the E3 gate and the protocol results are unchanged is present.
* A banned word in the text makes the check fail.

**TB7. Runner.**
* Without `--expect-commit` it refuses with exit 3 and writes nothing.
* It refuses on a dirty tree.
* It refuses while an X process is running (simulated by a dummy process with `xplore.x_units` in its argv).
* A real run refuses `--ignore-x-running` and threads ≠ 6.
* `--status` prints no balanced accuracy and no judgement.

**S. Smoke run (PLACEHOLDER).**
* **Setup:** a throwaway clone; key P; 2 draws; 2 threads on CPUs 18–19; `--ignore-x-running`.
* **Interrupt and resume:**
  * stopped with `--stop` during a stage after C-B0: state "stopped", resumable;
  * relaunched: complete.
* **Results:** C-B0 passed, and a record commit of exactly the 8 record files whose parent is the launch commit.
* **Afterwards:** a relaunch is refused, and the outputs and the clone are deleted.

## Test results (2026-10-19)

The criteria were committed in `f6b4f39`; TB4 was revised in `e54ec9e`, before any test was run. The tests ran in the step-5 interpreter under `taskset -c 18,19` with 2 BLAS threads; peak RSS was 1.1 GB. Logs are in `tests/logs/`.

| criteria | result | log |
|---|---|---|
| TB1–TB6 (`tests/test_b_components.py`) | run 3: 7 / 7 passed (12 min 32 s) | `test_components_20261019-1110_run3.log` |
| TB7 (`tests/test_b_runner.py`) | 3 / 3 passed | `test_runner_fast_20261019-1122.log` |
| S (smoke run) | passed (11 min 7 s) | `test_smoke_20261019-1122.log` |

**Two earlier component runs failed in the TB4 test, both from errors in the test design, not in the B code.** No B code was changed.
* **Run 1** (`…1042_run1_TB4-test-design-failure.log`):
  * On the PLACEHOLDER features *after* LEACE, the linear S1 probe predicts the same site for every case.
  * The test's perturbation (swapping one case's features) therefore cannot change any prediction.
  * Fix: the TB4 test uses the non-erased PLACEHOLDER PCA features, on which the probe separates sites. The criterion is unchanged.
* **Run 2** (`…1049_run2_TB4-ulp-direction-failure.log`):
  * On those features the linear probe reaches BA = 1.0, and the one-ulp shift `nextafter(ba, 1.0)` leaves 1.0 unchanged.
  * Fix: the shift goes towards +∞.
* **In both runs,** C-B0 itself passed against the locked reference, and the other six tests passed.

**Smoke run S** (PLACEHOLDER, key P, 2 draws, 2 threads on CPUs 18–19, `--ignore-x-running` while X1/X2 was running):
* **Stop:** the run was stopped with `--stop` after 299 s, with stages `phref P` and `cb0 P` done. The runner exited with code 2, state "stopped".
* **Resume:** the same command completed in 367 s.
* **Record commit:** exactly the 8 record files, parent = the launch commit, tree clean; C-B0 passed.
* **Relaunch:** refused.
* **Clean-up:** the outputs and the clone were deleted.

**Stage times (2 threads, PLACEHOLDER, one key):**

| stage | time | content |
|---|---:|---|
| `phref` | 2 min 26 s | locked `e3_site` on S1 and S3 |
| `cb0` | 2 min 25 s | S1 probes, linear + MLP, 45,957 rows; S3 refits |
| `main` | 1 min 11 s | S2 refits, 26,126 rows |
| `sens` | 4 min 47 s | 2 draws, i.e. 2 min 23 s per draw: 6 refits on 112 cases × 75 steps |
| `report` | 7 s | |

## Revised run-time estimate (real run)

The plan (§8) estimated 0.5–0.8 h at 6 threads by scaling fit time linearly with rows. The smoke run shows that this underestimates the sensitivity part. Small fits do not shrink in proportion, because of the inner penalty CV and the MLP's early-stopping epochs. The real subsamples have exactly the PLACEHOLDER size (112 cases × 75 steps per set), so the measured time per draw applies directly.

| part | basis | estimate |
|---|---|---:|
| preflight (hashing about 1.6 GB of step-5 files) | — | 1–3 min |
| C-B0, 3 keys | PLACEHOLDER `cb0` × 104,662 / 45,957 rows | ≈ 15 min |
| main cells, 3 keys | `main` × 70,763 / 26,126 rows | ≈ 10 min |
| sensitivity, 20 draws × 3 keys | 2.4 min per draw and key | ≈ 2.4 h |
| report | — | < 1 min |
| **total, sequential** | | **≈ 2.5–3.5 h** |

* **Range:** measured at 2 threads. The real run uses 6 threads, as the plan requires for C-B0; the PLACEHOLDER timings showed no speed-up from more BLAS threads, so the range is kept wide.
* **Who launches:** it exceeds 1 hour and uses 6 threads, so the investigator launches it, after X1/X2 has finished.
* **Not implemented:** the plan's optional parallel-keys mode (3 × 6 threads). The runner runs the keys one after another.

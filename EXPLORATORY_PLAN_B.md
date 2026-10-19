# Exploratory analysis B: in which evaluation distribution does the E3-site judgement change? (plan, fixed before any B result)

* **Written:** 2026-10-19, under `CC_TASK_SS_planB_v2.md` (investigator).
* **Repository:** `/srv/ss_exploratory_B/`. This is separate from `/srv/ss_exploratory/`, from which X1/X2 runs.
* **Status:** exploratory, outside the frozen protocol (DS203, `4c86dc5`). B does not change:
  * the E3 gate;
  * §13;
  * any family verdict;
  * any X1/X2 plan.

  It does not turn the primary E3-site FAIL into a PASS.
* **Access while writing this plan:**
  * No B result exists.
  * No step-6 or step-7 result file and no X1/X2 output was opened. X1/X2 was running and had produced no result.
  * B uses no step-6 or step-7 quantity.
  * **Disclosure:** the step-7 family-verdict summary had been generated and reported to the investigator earlier on 2026-10-19, in the same working session (`CC_TASK_SS_report_figures_v1.md`).
* **Inputs read:**
  * the locked code at the main repository's commit `2880d73`: `ss_benchmark/checks.py`, `learners.py`, `constants.py`, `design.py`, `reduce.py` and `pipeline.run_checks` (`ss_benchmark/` there is byte-identical to the SDR commit `af56777`, except the extraction adapter);
  * the committed step-5 record (E3 values quoted below, as in `EXPLORATORY_PLAN_X1_X2.md` §0);
  * the step-5 checks log (start and end times only).
* **Computed on real data for this plan (counts only):**
  * set sizes, steps, centre and state counts and fold counts, from the design files and the `lengths` arrays of `reps_full_P.npz` (`planB_counts.json`);
  * no representation value was read.

## 0. Purpose and wording ceiling

**Purpose.**
* Find **in which evaluation distribution** the E3-site outcome changes, by evaluating site recoverability on three nested evaluation sets.
* In step 5, the linear site probe after the protocol LEACE gave:
  * BA 0.250 on the 278-case set (all steps), where E3-site passed;
  * BA 0.416 / 0.393 / 0.448 (P / S / REF) on the 158-case set's analysis region, where E3-site failed (one-sided 95 % upper bounds 0.472 / 0.435 / 0.505 > 0.35).

**Ceiling.**
* B identifies **where** the judgement changes, **not why**.
* Between the sets, case composition, centre mix, the state distribution, step counts and the fit/evaluation distribution all change together.
* B is never described as mechanism identification.
* The only comparative statement allowed is "the judgement changes between Sx and Sy" (or "does not change").

## 1. Evaluation sets

| set | cases | steps used per case | rows |
|---|---|---|---:|
| **S1** | the 278-case representation set | all steps | 104,662 |
| **S2** | the 158-case primary set | all steps | 70,763 |
| **S3** | the 158-case primary set | the analysis region: window-relative steps −30 … 44 (`ANALYSIS_REGION`, §7.2), i.e. rows w_i − 30 … w_i + 44 with w_i the window start | 11,850 |

* **Nesting:** S3 ⊂ S2 ⊂ S1, as rows.
* **"Analysis-window steps"** (task text) is taken to be this analysis region. It is the row set on which step-5 E3-site was evaluated for the 158-case set, so S3 reproduces the step-5 primary E3 population. It is not the 15 estimator window steps w_i … w_i + 14.
* **Bounds:** every primary case's region lies inside its steps (lowest start row 5, at least 32 steps of margin at the end).

### Descriptives per set (`planB_counts.json`)

| | S1 | S2 | S3 |
|---|---:|---:|---:|
| cases | 278 | 158 | 158 |
| steps (rows) | 104,662 | 70,763 | 11,850 |
| steps per case: mean / median / min / max | 376.5 / 346 / 4 / 1,336 | 447.9 / 379 / 150 / 1,336 | 75 / 75 / 75 / 75 |
| cases per centre (2 / 3 / 4 / 5) | 49 / 41 / 71 / 117 | 28 / 34 / 44 / 52 | 28 / 34 / 44 / 52 |
| steps per centre (2 / 3 / 4 / 5) | 16,824 / 16,669 / 28,911 / 42,258 | 11,893 / 14,882 / 21,764 / 22,224 | 2,100 / 2,550 / 3,300 / 3,900 |
| share of rows with S = 1 (S_t = 1{t ≥ s_i}) | 0.780 | 0.709 | 0.602 |
| share with S = 1, by centre (2 / 3 / 4 / 5) | 0.771 / 0.725 / 0.707 / 0.855 | 0.750 / 0.707 / 0.640 / 0.757 | 0.603 / 0.600 / 0.603 / 0.603 |
| cases per fold (0–4) | 56 / 56 / 56 / 55 / 55 | 35 / 30 / 32 / 34 / 27 | 35 / 30 / 32 / 34 / 27 |

The report states these descriptives next to the results.

## 2. Fixed components (nothing is refitted except the probes in analysis (b))

* **Representations:** P, S and REF after the protocol LEACE.
  * Source: the step-5 `reps_full_<key>.npz`, arrays `RC_v`: every case's steps transformed by the fold-v PCA (64 PCs) and the fold-v LEACE.
  * Both operators were fitted at step 5 on all steps of the 278-case set's training-fold cases (fold ≠ v). They are **not refitted**.
  * P-nat has no LEACE and is not included.
* **Folds:** the original case-fold assignment (§2; seed 20261006), restricted to each set's cases.
* **Probes:** the locked probe specifications, unchanged (`checks.site_probe_case_predictions`):
  * **linear:** multinomial L2 logistic; penalty by inner 5-fold group CV over {1e-4 … 1e2};
  * **MLP:** the fixed MLP probe (`MLP_PROBE`: 256 hidden units, lr 1e-3, weight decay 1e-4, ≤ 200 epochs, patience 20, validation fraction 0.2).
* **Prediction:** per-step site probabilities; a case's prediction is the argmax of its mean probability over the set's steps; balanced accuracy over cases.
* **Feature normalisation:** the locked one, a z-score inside each probe fitted on its training rows. In (a) it belongs to the S1-trained probe; in (b) it is refitted with each probe as part of the probe specification.
* **Environment** (so that the step-5 probes are re-created exactly):
  * the interpreter of the step-5 checks, `/home/user/.venvs/ss_extract/bin/python` (Python 3.11.14, numpy 2.3.5 with OpenBLAS 0.3.30, scipy 1.17.0, scikit-learn 1.6.1, pandas 3.0.1);
  * the step-5 thread settings: `OMP_NUM_THREADS = MKL_NUM_THREADS = OPENBLAS_NUM_THREADS = 6`, `PYTHONHASHSEED = 0`;
  * the locked code from a `git archive` snapshot of the main repository's commit `2880d73`.

## 3. Two analyses, reported separately and never mixed

**(a) Transport.**
* **The probe** is fitted as in E3 on S1: for each fold v, on the S1 cases with fold ≠ v, all steps, with the locked probe code and exactly the step-5 probe streams (tag `E3:278:<key>-C`, root 20261006). This re-creates the step-5 E3 probe, which was not stored.
* **Evaluation:** on the held-out cases (fold v), restricted to:
  * S1: all held-out cases, all steps;
  * S2: the held-out primary cases, all steps;
  * S3: the held-out primary cases, analysis-region steps.
* Every case of a set is held out exactly once.

**(b) Recoverability.** The same probe specification is refitted within each set (folds restricted to the set; training rows = the set's steps of its training-fold cases) and evaluated within it.

| set | in (b) | probe streams |
|---|---|---|
| S1 | identical to the step-5 E3_site_278 | tag `E3:278:<key>-C` |
| S3 | identical to the step-5 E3_site_primary | tag `E3:primary:<key>-C` |
| S2 | new | tag `E3:planB-S2:<key>-C` |

Each analysis is run with the linear probe and with the MLP probe. Results of (a) and (b) are never pooled or contrasted with each other.

## 4. Uncertainty and the judgement

**Balanced accuracy with intervals** comes from the locked `checks.ba_with_ci`:
* BA, 2.5 / 97.5 % percentiles and the one-sided 95 % upper bound;
* case-level bootstrap stratified by site, as in step 5, with 2,000 resamples;
* seed root `SeedSequence(20261008)` with named streams.

**Bootstrap stream names:**
* cells identical to a step-5 computation use the step-5 name, so they reproduce the committed numbers:
  * `E3:278:<key>-C:<linear|mlp>` for S1 in (a) and (b);
  * `E3:primary:<key>-C:<linear|mlp>` for S3 in (b);
* all other cells use `planB:<a|b>:<S2|S3>:<key>-C:<linear|mlp>`.

No between-set test is computed.

**Judgement** (descriptive, per cell): does the one-sided 95 % upper bound exceed the prespecified boundary 0.35 (§5.3)?
* For the linear probe this is the E3-site rule, applied descriptively.
* For the MLP probe it is the step-5 reporting comparison (`mlp_exceeds_margin`).
* "The judgement changes between Sx and Sy" means that this statement differs between Sx and Sy. It is reported for S1→S2, S2→S3 and S1→S3, per key, analysis and probe.

## 5. Control C-B0 (before anything is reported)

Before any B number is reported, B must reproduce the committed step-5 numbers **exactly**: `ba`, `lo_2p5`, `hi_97p5` and `upper_one_sided_95`, for both probes and for P, S and REF.
* (a)-S1 and (b)-S1 must reproduce `E3_site_278`.
* (b)-S3 must reproduce `E3_site_primary`.

If any value differs, B stops and reports the difference. No B result is reported, and there is no fallback to another environment.

## 6. Exploratory sensitivity (pre-fixed; descriptive)

**Purpose:** subsampling to equal numbers of cases per centre and equal steps per case across S1–S3.
* **Draws:** D = 20, with seed `SeedSequence(20261008)` named child `planB:subsample:<d>` (d = 0 … 19).
* **Cases:** in each draw, m = 28 cases per centre (the smallest centre count in S2/S3), 112 cases per set, sampled without replacement:
  * S1 from that centre's representation-set cases with at least 75 steps. This excludes 4 of the 278 cases, which have fewer than 75 steps (centres 2 / 4 / 5: 1 / 1 / 2);
  * S2 from that centre's primary cases; S3 uses the same cases as S2.
* **Steps:** T = 75 per case.
  * S1 and S2: 75 distinct steps sampled uniformly without replacement from each case's steps.
  * S3: the case's 75 analysis-region steps.
* **Folds:** the fixed fold labels of the sampled cases.
* **(a):** the main analysis's S1 probes, not refitted; their out-of-fold per-row probabilities are kept from the main run. Each sampled case is predicted from its sampled steps.
* **(b):** the probes refitted within each subsampled set, with tag `E3:planB-sens-<d>-<set>:<key>-C`.
* **Reported:** BA per draw. Across draws, per key × analysis × probe × set: median, 2.5 / 97.5 % percentiles, minimum and maximum.
* **Not reported:** no bootstrap within draws and no judgement statement. The sensitivity results are descriptive only.

## 7. Outputs and wording

**Main table**, one row per representation × analysis × probe × set (3 × 2 × 2 × 3 = 36 rows), with:
* cases, rows;
* BA, 95 % interval, one-sided 95 % upper bound;
* whether it exceeds 0.35;
* the bootstrap stream name.

**Other outputs:**
* the judgement-change statements (S1→S2, S2→S3, S1→S3) per key × analysis × probe;
* the descriptives of §1;
* the C-B0 control;
* the sensitivity summary of §6.

**Wording:**
* Allowed: "the judgement changes between Sx and Sy" or "does not change"; descriptive numbers.
* Not allowed: "mechanism", "cause", "because", "explains", "due to", "SUPPORTED", "CONTRADICTED", "eliminated", "equivalent to chance".
* No statement that the primary E3-site passes, or that the E3 gate, §13 or a family verdict changes.
* The report states that the E3 gate, §13 and the protocol results are unchanged.

## 8. Compute estimate and who launches

**Basis.**
* The step-5 checks (all keys and sets: E1, E2 in all variants, E3, MLP probes, reporting paths) took 44.6 min (13:40:57 → 14:25:31, 2026-10-12) in one process with 6 threads.
* PLACEHOLDER timing, measured on 2026-10-19 on an S1-shaped PLACEHOLDER set of 45,957 rows, 1 thread, one key, 5 folds: linear probe 31 s, MLP probe 47 s, BA bootstrap 0.3 s.
* Scaled linearly by rows: S1 (104,662 rows) ≈ 71 s + 107 s; S2 (70,763) ≈ 48 s + 72 s; S3 (11,850) ≈ 8 s + 12 s per key.

| part | 1 thread | at 6 threads (estimate) |
|---|---:|---:|
| (a) and (b): the S1 probes (shared), S2 and S3 refits, evaluations and bootstraps; 3 keys | ≈ 16 min | ≈ 8–12 min |
| C-B0 (re-uses the main computations) | — | — |
| sensitivity, 20 draws × 3 sets × 3 keys × 2 probes on 8,400 rows (refits in (b); cached probabilities in (a)) | ≈ 42 min | ≈ 20–30 min |
| loading the representations (3 × 536 MB) and writing the report | — | < 5 min |
| **total** | **≈ 1–1.2 h** | **≈ 0.5–0.8 h** |

**The run needs more than 2 CPU threads:** 6 threads, to match step 5, which is required for C-B0. **The investigator therefore launches it from the terminal.**

**Timing:** after X1/X2 has finished, so as not to compete with its 18 workers. Running the three keys as parallel processes (3 × 6 threads) would shorten the wall time to about 15–25 min.

## 9. Code (new; written, tested on PLACEHOLDER and committed before the run)

All new code lives in `/srv/ss_exploratory_B/`. The locked probes, learners, bootstrap and design code are imported unchanged from the `2880d73` snapshot.

| module | role | locked code reused unchanged |
|---|---|---|
| `planB/b_sets.py` | the three sets (case indices, rows per case) from the locked design; descriptives; subsamples | `design.representation_cases`, `representation_folds`, `representation_switch_steps`, `load_real_design`; `ANALYSIS_REGION` |
| `planB/b_probes.py` | (a): the fold loop of `site_probe_case_predictions` with the same training rows and streams, returning per-row out-of-fold probabilities on all S1 rows, then case predictions per set. (b): the locked `site_probe_case_predictions` per set. BA via the locked `ba_with_ci`. | `learners.fit_multinomial_cv`, `learners.MLP`, `checks.probe_rng`, `checks.site_probe_case_predictions`, `checks.ba_with_ci`, `checks.balanced_accuracy` |
| `planB/b_sensitivity.py` | the §6 draws | the same |
| `planB/b_report.py` | tables, judgement statements, wording check, C-B0 | — |
| `run_b.sh` | orchestration (see below) | — |
| `tests/` | PLACEHOLDER tests (see below) | — |

**`run_b.sh`:**
* **Preconditions** (it refuses otherwise):
  * this repository at HEAD = `--expect-commit`, with a clean tree;
  * the step-5 files `reps_full_{P,S,REF}.npz` and `checks.json` match the committed `step5_manifest.json`;
  * the locked snapshot is taken from `2880d73`;
  * no X1/X2 process is running.
* **Runs** with the step-5 interpreter and threads, resumably per key.
* **Outputs** go to `/media/user/LaCie/medvideo_gate/ss_exploratory_B/`.
* **Records** (C-B0, the main table, judgement statements, descriptives, sensitivity summary, input hashes) are committed automatically in `/srv/ss_exploratory_B/results_B/`, records only, before anyone reads them.

**Tests (fixed before running):**
* (a)'s S1 case predictions equal the locked `site_probe_case_predictions` output, bit for bit;
* (b) per set equals a direct locked call;
* the C-B0 logic stops on a one-ulp difference;
* subsamples have exactly 28 cases per centre and 75 steps per case, and are deterministic for a given draw;
* report wording: no banned word, every (key, analysis, probe, set) row present.

**Order of work.** Code, tests and the test record are committed before the run. The run takes place after:
1. this plan's commit;
2. the registration of the OSF addendum.

# Exploratory analysis B: where the E3-site judgement changes across evaluation sets

* **Plan:** `EXPLORATORY_PLAN_B.md`, commit `e1c27b4332af634c478ce7dc619eaf8ffc0acf0c` (OSF https://osf.io/g9ymw, addendum to https://osf.io/5c627).
* **Status:** exploratory. B does not change the E3 gate, §13, any family verdict or any protocol result; the primary E3-site outcome of step 5 stands.
* **Ceiling:** B identifies where the judgement changes, not why: between the sets, case composition, centre mix, the state distribution, step counts and the fit / evaluation distribution change together.
* **Judgement:** whether the one-sided 95 % upper bound of the case-level balanced accuracy exceeds the prespecified boundary 0.35 (§5.3); for the linear probe this is the E3-site rule applied descriptively, for the MLP probe the step-5 reporting comparison.

## Control C-B0

| key | probe | set | reference | identical | B: BA / upper | step 5: BA / upper |
|---|---|---|---|---|---|---|
| P | linear | S1 | E3_site_278.linear | yes | 0.250 / 0.250 | 0.250 / 0.250 |
| P | linear | S3 | E3_site_primary.linear | yes | 0.416 / 0.472 | 0.416 / 0.472 |
| P | mlp | S1 | E3_site_278.mlp | yes | 0.957 / 0.979 | 0.957 / 0.979 |
| P | mlp | S3 | E3_site_primary.mlp | yes | 0.702 / 0.755 | 0.702 / 0.755 |
| S | linear | S1 | E3_site_278.linear | yes | 0.250 / 0.250 | 0.250 / 0.250 |
| S | linear | S3 | E3_site_primary.linear | yes | 0.393 / 0.435 | 0.393 / 0.435 |
| S | mlp | S1 | E3_site_278.mlp | yes | 0.495 / 0.531 | 0.495 / 0.531 |
| S | mlp | S3 | E3_site_primary.mlp | yes | 0.428 / 0.476 | 0.428 / 0.476 |
| REF | linear | S1 | E3_site_278.linear | yes | 0.250 / 0.250 | 0.250 / 0.250 |
| REF | linear | S3 | E3_site_primary.linear | yes | 0.448 / 0.505 | 0.448 / 0.505 |
| REF | mlp | S1 | E3_site_278.mlp | yes | 0.863 / 0.900 | 0.863 / 0.900 |
| REF | mlp | S3 | E3_site_primary.mlp | yes | 0.620 / 0.680 | 0.620 / 0.680 |

## Descriptives per set

| | S1 | S2 | S3 |
|---|---:|---:|---:|
| cases | 278 | 158 | 158 |
| steps (rows) | 104662 | 70763 | 11850 |
| steps per case: mean / median / min / max | 376.5 / 346 / 4 / 1336 | 447.9 / 379 / 150 / 1336 | 75.0 / 75 / 75 / 75 |
| cases per centre | 2: 49 / 3: 41 / 4: 71 / 5: 117 | 2: 28 / 3: 34 / 4: 44 / 5: 52 | 2: 28 / 3: 34 / 4: 44 / 5: 52 |
| share of rows with S = 1 | 0.780 | 0.709 | 0.602 |
| share with S = 1 by centre | 2: 0.771 / 3: 0.725 / 4: 0.707 / 5: 0.855 | 2: 0.750 / 3: 0.707 / 4: 0.640 / 5: 0.757 | 2: 0.603 / 3: 0.600 / 4: 0.603 / 5: 0.603 |
| cases per fold | 56 / 56 / 56 / 55 / 55 | 35 / 30 / 32 / 34 / 27 | 35 / 30 / 32 / 34 / 27 |

## Balanced accuracy per representation × analysis × probe × set

(a) transport: the S1 probe (fitted as in E3) evaluated on each set; (b) recoverability: the probe specification refitted within each set. Reported separately; never pooled or contrasted.

| key | analysis | probe | set | cases | rows | BA | 95 % interval | one-sided 95 % upper | exceeds 0.35 |
|---|---|---|---|---:|---:|---:|---|---:|---|
| P | (a) | linear | S1 | 278 | 104662 | 0.250 | [0.250, 0.250] | 0.250 | no |
| P | (a) | linear | S2 | 158 | 70763 | 0.250 | [0.250, 0.250] | 0.250 | no |
| P | (a) | linear | S3 | 158 | 11850 | 0.250 | [0.250, 0.250] | 0.250 | no |
| P | (a) | mlp | S1 | 278 | 104662 | 0.957 | [0.927, 0.982] | 0.979 | yes |
| P | (a) | mlp | S2 | 158 | 70763 | 0.969 | [0.936, 0.994] | 0.991 | yes |
| P | (a) | mlp | S3 | 158 | 11850 | 0.884 | [0.827, 0.933] | 0.926 | yes |
| P | (b) | linear | S1 | 278 | 104662 | 0.250 | [0.250, 0.250] | 0.250 | no |
| P | (b) | linear | S2 | 158 | 70763 | 0.231 | [0.182, 0.282] | 0.273 | no |
| P | (b) | linear | S3 | 158 | 11850 | 0.416 | [0.352, 0.481] | 0.472 | yes |
| P | (b) | mlp | S1 | 278 | 104662 | 0.957 | [0.927, 0.982] | 0.979 | yes |
| P | (b) | mlp | S2 | 158 | 70763 | 0.948 | [0.907, 0.982] | 0.982 | yes |
| P | (b) | mlp | S3 | 158 | 11850 | 0.702 | [0.640, 0.763] | 0.755 | yes |
| S | (a) | linear | S1 | 278 | 104662 | 0.250 | [0.250, 0.250] | 0.250 | no |
| S | (a) | linear | S2 | 158 | 70763 | 0.250 | [0.250, 0.250] | 0.250 | no |
| S | (a) | linear | S3 | 158 | 11850 | 0.250 | [0.250, 0.250] | 0.250 | no |
| S | (a) | mlp | S1 | 278 | 104662 | 0.495 | [0.456, 0.535] | 0.531 | yes |
| S | (a) | mlp | S2 | 158 | 70763 | 0.479 | [0.433, 0.523] | 0.517 | yes |
| S | (a) | mlp | S3 | 158 | 11850 | 0.501 | [0.443, 0.562] | 0.550 | yes |
| S | (b) | linear | S1 | 278 | 104662 | 0.250 | [0.250, 0.250] | 0.250 | no |
| S | (b) | linear | S2 | 158 | 70763 | 0.239 | [0.188, 0.290] | 0.282 | no |
| S | (b) | linear | S3 | 158 | 11850 | 0.393 | [0.346, 0.444] | 0.435 | yes |
| S | (b) | mlp | S1 | 278 | 104662 | 0.495 | [0.456, 0.535] | 0.531 | yes |
| S | (b) | mlp | S2 | 158 | 70763 | 0.520 | [0.475, 0.566] | 0.559 | yes |
| S | (b) | mlp | S3 | 158 | 11850 | 0.428 | [0.368, 0.489] | 0.476 | yes |
| REF | (a) | linear | S1 | 278 | 104662 | 0.250 | [0.250, 0.250] | 0.250 | no |
| REF | (a) | linear | S2 | 158 | 70763 | 0.250 | [0.250, 0.250] | 0.250 | no |
| REF | (a) | linear | S3 | 158 | 11850 | 0.250 | [0.250, 0.250] | 0.250 | no |
| REF | (a) | mlp | S1 | 278 | 104662 | 0.863 | [0.818, 0.904] | 0.900 | yes |
| REF | (a) | mlp | S2 | 158 | 70763 | 0.875 | [0.822, 0.924] | 0.916 | yes |
| REF | (a) | mlp | S3 | 158 | 11850 | 0.788 | [0.724, 0.848] | 0.839 | yes |
| REF | (b) | linear | S1 | 278 | 104662 | 0.250 | [0.250, 0.250] | 0.250 | no |
| REF | (b) | linear | S2 | 158 | 70763 | 0.208 | [0.158, 0.257] | 0.251 | no |
| REF | (b) | linear | S3 | 158 | 11850 | 0.448 | [0.387, 0.518] | 0.505 | yes |
| REF | (b) | mlp | S1 | 278 | 104662 | 0.863 | [0.818, 0.904] | 0.900 | yes |
| REF | (b) | mlp | S2 | 158 | 70763 | 0.871 | [0.815, 0.924] | 0.918 | yes |
| REF | (b) | mlp | S3 | 158 | 11850 | 0.620 | [0.543, 0.687] | 0.680 | yes |

## Where the judgement changes

| key | analysis | probe | S1→S2 | S2→S3 | S1→S3 |
|---|---|---|---|---|---|
| P | (a) | linear | does not change between S1 and S2 | does not change between S2 and S3 | does not change between S1 and S3 |
| P | (a) | mlp | does not change between S1 and S2 | does not change between S2 and S3 | does not change between S1 and S3 |
| P | (b) | linear | does not change between S1 and S2 | changes between S2 and S3 | changes between S1 and S3 |
| P | (b) | mlp | does not change between S1 and S2 | does not change between S2 and S3 | does not change between S1 and S3 |
| S | (a) | linear | does not change between S1 and S2 | does not change between S2 and S3 | does not change between S1 and S3 |
| S | (a) | mlp | does not change between S1 and S2 | does not change between S2 and S3 | does not change between S1 and S3 |
| S | (b) | linear | does not change between S1 and S2 | changes between S2 and S3 | changes between S1 and S3 |
| S | (b) | mlp | does not change between S1 and S2 | does not change between S2 and S3 | does not change between S1 and S3 |
| REF | (a) | linear | does not change between S1 and S2 | does not change between S2 and S3 | does not change between S1 and S3 |
| REF | (a) | mlp | does not change between S1 and S2 | does not change between S2 and S3 | does not change between S1 and S3 |
| REF | (b) | linear | does not change between S1 and S2 | changes between S2 and S3 | changes between S1 and S3 |
| REF | (b) | mlp | does not change between S1 and S2 | does not change between S2 and S3 | does not change between S1 and S3 |

## Exploratory sensitivity (descriptive; no bootstrap, no judgement)

Equal cases per centre (m = [28]) and 75 steps per case in S1–S3; 20 draws (seed SeedSequence(20261008) child "planB:subsample:<d>").

| key | analysis | probe | set | draws | median BA | 2.5–97.5 % across draws | min–max |
|---|---|---|---|---:|---:|---|---|
| P | (a) | linear | S1 | 20 | 0.250 | 0.250–0.250 | 0.250–0.250 |
| P | (a) | linear | S2 | 20 | 0.250 | 0.250–0.250 | 0.250–0.250 |
| P | (a) | linear | S3 | 20 | 0.250 | 0.250–0.250 | 0.250–0.250 |
| P | (a) | mlp | S1 | 20 | 0.955 | 0.933–0.978 | 0.929–0.982 |
| P | (a) | mlp | S2 | 20 | 0.964 | 0.946–0.978 | 0.946–0.982 |
| P | (a) | mlp | S3 | 20 | 0.884 | 0.857–0.906 | 0.857–0.911 |
| P | (b) | linear | S1 | 20 | 0.339 | 0.235–0.420 | 0.214–0.429 |
| P | (b) | linear | S2 | 20 | 0.290 | 0.213–0.353 | 0.196–0.357 |
| P | (b) | linear | S3 | 20 | 0.362 | 0.304–0.429 | 0.304–0.429 |
| P | (b) | mlp | S1 | 20 | 0.902 | 0.852–0.942 | 0.848–0.946 |
| P | (b) | mlp | S2 | 20 | 0.902 | 0.848–0.956 | 0.848–0.964 |
| P | (b) | mlp | S3 | 20 | 0.446 | 0.321–0.603 | 0.321–0.607 |
| REF | (a) | linear | S1 | 20 | 0.250 | 0.250–0.250 | 0.250–0.250 |
| REF | (a) | linear | S2 | 20 | 0.250 | 0.250–0.250 | 0.250–0.250 |
| REF | (a) | linear | S3 | 20 | 0.250 | 0.250–0.250 | 0.250–0.250 |
| REF | (a) | mlp | S1 | 20 | 0.857 | 0.825–0.884 | 0.812–0.884 |
| REF | (a) | mlp | S2 | 20 | 0.866 | 0.802–0.906 | 0.777–0.911 |
| REF | (a) | mlp | S3 | 20 | 0.790 | 0.763–0.812 | 0.759–0.812 |
| REF | (b) | linear | S1 | 20 | 0.308 | 0.232–0.389 | 0.223–0.402 |
| REF | (b) | linear | S2 | 20 | 0.286 | 0.241–0.353 | 0.241–0.357 |
| REF | (b) | linear | S3 | 20 | 0.379 | 0.316–0.464 | 0.304–0.464 |
| REF | (b) | mlp | S1 | 20 | 0.790 | 0.678–0.857 | 0.670–0.857 |
| REF | (b) | mlp | S2 | 20 | 0.763 | 0.674–0.857 | 0.670–0.857 |
| REF | (b) | mlp | S3 | 20 | 0.527 | 0.351–0.656 | 0.321–0.661 |
| S | (a) | linear | S1 | 20 | 0.250 | 0.250–0.250 | 0.250–0.250 |
| S | (a) | linear | S2 | 20 | 0.250 | 0.250–0.250 | 0.250–0.250 |
| S | (a) | linear | S3 | 20 | 0.250 | 0.250–0.250 | 0.250–0.250 |
| S | (a) | mlp | S1 | 20 | 0.491 | 0.451–0.541 | 0.446–0.554 |
| S | (a) | mlp | S2 | 20 | 0.473 | 0.446–0.492 | 0.446–0.500 |
| S | (a) | mlp | S3 | 20 | 0.500 | 0.469–0.523 | 0.464–0.527 |
| S | (b) | linear | S1 | 20 | 0.259 | 0.187–0.349 | 0.187–0.357 |
| S | (b) | linear | S2 | 20 | 0.214 | 0.179–0.281 | 0.179–0.286 |
| S | (b) | linear | S3 | 20 | 0.357 | 0.308–0.442 | 0.304–0.446 |
| S | (b) | mlp | S1 | 20 | 0.451 | 0.285–0.630 | 0.277–0.634 |
| S | (b) | mlp | S2 | 20 | 0.384 | 0.257–0.533 | 0.223–0.562 |
| S | (b) | mlp | S3 | 20 | 0.388 | 0.281–0.455 | 0.277–0.455 |

# ss_exploratory_B

**SS-DS203 exploratory analysis B.** Exploratory analysis B (outside the frozen protocol; plan registered on OSF before launch, https://osf.io/g9ymw): evaluation-distribution decomposition of the E3-site judgement — plan, implementation notes, code, tests and records.

Part of the code and records of the manuscript *Semi-synthetic evaluation of site information and linear erasure in clinical video representations for sequentially doubly robust causal effect estimation* (Nakano H, Shiinoki T; article DOI: [TO FILL]). The six repositories of this release are archived together, as git bundles at tag `v1.0.0-submission`, on Zenodo: https://doi.org/10.5281/zenodo.23934337.

Repositories of this release:

* [`medical_video_causal_gate`](https://github.com/repro-analysis-archive/medical_video_causal_gate)
* [`ss_exploratory`](https://github.com/repro-analysis-archive/ss_exploratory)
* [`ss_exploratory_B`](https://github.com/repro-analysis-archive/ss_exploratory_B)
* [`step7_prep`](https://github.com/repro-analysis-archive/step7_prep)
* [`jbi_figures_tables`](https://github.com/repro-analysis-archive/jbi_figures_tables)
* [`ss-ds203-records`](https://github.com/repro-analysis-archive/ss-ds203-records)

Release: tag `v1.0.0-submission` (2026-11-04).

## Contents

`EXPLORATORY_PLAN_B.md`, `B_IMPLEMENTATION_NOTES.md`, `planB/` and `planB_counts.py` (code), `planB_counts.json`, `run_b.sh`, `tests/`, `results_B/` (records), `osf_B/` (registration package).

## Commit identifiers cited in the manuscript (Supplementary Methods) and records

Each identifier can be checked with `git show <ID>` in a clone of this repository.

| meaning | original ID (cited in the Supplementary Methods / records) | ID in this repository |
|---|---|---|
| B plan | `e1c27b4` (`e1c27b4332af634c478ce7dc619eaf8ffc0acf0c`) | `e1c27b4332af634c478ce7dc619eaf8ffc0acf0c` (unchanged) |
| B test logs and launch | `c7354ed` (`c7354edc5b9d5e119b612a08534c22e647e8e05d`) | `c7354edc5b9d5e119b612a08534c22e647e8e05d` (unchanged) |
| B records | `458341f` (`458341f9f873bfebe8ea293552dece64bf0ebdfd`) | `458341f9f873bfebe8ea293552dece64bf0ebdfd` (unchanged) |

## Not included

* video files and per-frame representations of Appendix300

The history is published unchanged (no third-party material found); all commit identifiers are the original ones.

Scripts and records contain absolute paths of the machines on which the analysis ran (for example `/home/user/…`, `/srv/…`, `/media/user/LaCie/…`, `/Volumes/ADDATA/…`). They are recorded as they were; adapt them to re-run.

## Data source and attribution

The video data are Appendix300 (CC BY 4.0), used with attribution (manuscript references 1 and 45):

* Kolbinger FR, Kirchner M, Pfeiffer K, Bodenstedt S, Jenke AC, Barthel J, et al. Appendix300: Surgical video and patient metadata of 330 laparoscopic appendectomy cases from five institutions [dataset]. Technische Universität Dresden, OPARA; 2026-04-29. doi:10.25532/OPARA-1173. License: CC BY 4.0.
* Kolbinger FR, Kirchner M, Pfeiffer K, Bodenstedt S, Jenke AC, Barthel J, et al. Appendix300: Surgical video and patient metadata of 330 laparoscopic appendectomy cases from five institutions. Sci Data. 2026;13:886. doi:10.1038/s41597-026-07593-6.

No video file, video frame or per-frame representation is redistributed here.

## Licence

* **Original code** (`planB/`, `planB_counts.py`, `tests/`, `run_b.sh`): MIT License — see `LICENSE`. Copyright (c) 2026 Hisashi Nakano.
* **Records, results and figure data** (the plan, notes, `planB_counts.json`, `results_B/` and `osf_B/`): Creative Commons Attribution 4.0 International (CC BY 4.0) — see `LICENSE-CC-BY-4.0`.
* **Not covered by either licence:** third-party material quoted or embedded in this repository remains under its own terms.

## How to cite

Please cite the article (DOI: [TO FILL]) and the Zenodo archive https://doi.org/10.5281/zenodo.23934337; machine-readable metadata: `CITATION.cff`.

## Use of AI tools

Most commits carry a `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` line: code and records were produced with Claude Code under the investigator's instructions, as declared in the manuscript. Automated record commits made by the runners carry no such line. The lines are kept unchanged.

## Authors and contact

* Hisashi Nakano (ORCID [0000-0002-9023-880X](https://orcid.org/0000-0002-9023-880X)), Department of Health Data Science, Niigata University of Health and Welfare — hisashi-nakano@nuhw.ac.jp (corresponding)
* Takehiro Shiinoki (ORCID [0000-0002-0246-8489](https://orcid.org/0000-0002-0246-8489)), Department of Radiation Oncology, Yamaguchi University

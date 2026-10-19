"""Shared fixtures: a locked-code snapshot of the main repository's commit 2880d73 (git archive, read only) and the
locked PLACEHOLDER inputs. Run with the step-5 interpreter, at most 2 CPUs and 2 threads."""
import os
import subprocess
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from planB import common as C  # noqa: E402


@pytest.fixture(scope="session")
def snap(tmp_path_factory):
    d = tmp_path_factory.mktemp("locked_snapshot")
    arch = subprocess.run(["git", "-C", C.MAIN_REPO, "archive", "--format=tar", C.STEP7_RECORD_COMMIT,
                           *C.SNAPSHOT_PATHS], capture_output=True, check=True)
    subprocess.run(["tar", "-x", "-C", str(d)], input=arch.stdout, check=True)
    C.use_locked(str(d))
    return str(d)


@pytest.fixture(scope="session")
def ph(snap):
    from ss_benchmark import placeholder
    from planB import b_sets
    rep_set, designs, _, _, full = placeholder.build(set_names=("primary",))
    sets = b_sets.placeholder_sets(rep_set, designs["primary"])
    return dict(rep_set=rep_set, D=designs["primary"], sets=sets, RC=full["P"]["R-C"], R=full["P"]["R"])


@pytest.fixture(scope="session")
def s1_linear(ph):
    """The S1 probe's per-row probabilities (linear) and the number of probe fits."""
    from planB import b_probes
    s = ph["sets"]
    fits = []
    rp, order = b_probes.transport_rowprobs(ph["RC"], s.sites, s.folds, s.lens, "linear", C.probe_tag("a", "S1", "P"),
                                            counter=fits)
    return rp, order, fits

"""Runner tests (criterion TB7) and the PLACEHOLDER smoke run with stop and resume (criterion S).

The smoke run is opt-in (several minutes); it works in a throwaway clone and temporary directories and deletes them:

    SS_B_SMOKE=1 taskset -c 18,19 env OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 PYTHONHASHSEED=0 \
        /home/user/.venvs/ss_extract/bin/python -m pytest -p no:cacheprovider -s -v tests/test_b_runner.py
"""
import json
import os
import shutil
import subprocess
import sys
import time

import pytest

from conftest import REPO

ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", GIT_OPTIONAL_LOCKS="0")


def git(repo, *args):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=ENV)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


def clone(tmp_path):
    c = tmp_path / "clone"
    git(tmp_path, "clone", "--quiet", "--no-hardlinks", REPO, str(c))
    for k in ("user.name", "user.email"):
        git(c, "config", k, git(REPO, "config", "--get", k))
    return c


def runner_log(out):
    return (out / "logs" / "runner_stdout.log").read_text()


def test_tb7_refuses_without_expect_commit(tmp_path):
    out = tmp_path / "bo"
    r = subprocess.run(["bash", os.path.join(REPO, "run_b.sh"), "--out", str(out)], capture_output=True, text=True,
                       env=ENV)
    assert r.returncode == 3 and "refused" in r.stderr and not out.exists()


def test_tb7_refusals(tmp_path):
    c = clone(tmp_path)
    head = git(c, "rev-parse", "HEAD")
    base = ["bash", str(c / "run_b.sh"), "--expect-commit", head]
    # a real run refuses the PLACEHOLDER-only options
    o1 = tmp_path / "o1"
    r = subprocess.run(base + ["--out", str(o1), "--ignore-x-running"], capture_output=True, text=True, env=ENV)
    assert r.returncode == 3 and "PLACEHOLDER runs only" in runner_log(o1)
    o2 = tmp_path / "o2"
    r = subprocess.run(base + ["--out", str(o2), "--threads", "2"], capture_output=True, text=True, env=ENV)
    assert r.returncode == 3 and "PLACEHOLDER runs only" in runner_log(o2)
    # refuses while an X process is running (a dummy process with xplore.x_units in its argv)
    dummy = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)", "xplore.x_units"])
    try:
        o3 = tmp_path / "o3"
        r = subprocess.run(base + ["--out", str(o3), "--placeholder", "--keys", "P", "--draws", "1", "--threads", "2",
                                   "--cpus", "19"], capture_output=True, text=True, env=ENV)
        assert r.returncode == 3 and "X1/X2 runner is still running" in runner_log(o3)
    finally:
        dummy.kill()
    # refuses on a dirty tree
    (c / "stray.txt").write_text("x")
    o4 = tmp_path / "o4"
    r = subprocess.run(base + ["--out", str(o4), "--placeholder", "--keys", "P", "--draws", "1", "--threads", "2",
                               "--cpus", "19", "--ignore-x-running"], capture_output=True, text=True, env=ENV)
    assert r.returncode == 3 and "working tree not clean" in runner_log(o4)
    for o in (o1, o2, o3, o4):
        assert not (o / "state.json").exists()


def test_tb7_status_shows_no_results(tmp_path):
    out = tmp_path / "bo"
    (out / "logs").mkdir(parents=True)
    (out / "state.json").write_text(json.dumps(dict(status="running", pid=None, stages_done=["cb0 P"])))
    (out / "logs" / "progress.log").write_text("2026-10-19T00:00:00+09:00 RES load 1.0 | ram used 1 GiB\n")
    r = subprocess.run(["bash", os.path.join(REPO, "run_b.sh"), "--status", "--out", str(out)], capture_output=True,
                       text=True, env=ENV)
    assert r.returncode == 0 and "stages done: cb0 P" in r.stdout
    for w in ("BA", "balanced", "accuracy", "exceeds", "judgement", "upper"):
        assert w not in r.stdout


@pytest.mark.skipif(os.environ.get("SS_B_SMOKE") != "1", reason="opt-in: SS_B_SMOKE=1")
def test_s_smoke_run_stop_resume(tmp_path):
    c = clone(tmp_path)
    head = git(c, "rev-parse", "HEAD")
    out = tmp_path / "bo"
    cmd = ["bash", str(c / "run_b.sh"), "--expect-commit", head, "--out", str(out), "--placeholder", "--keys", "P",
           "--draws", "2", "--threads", "2", "--cpus", "18,19", "--ignore-x-running"]
    env = dict(ENV, SS_B_RES_INTERVAL_S="20")
    p = subprocess.Popen(cmd, env=env, start_new_session=True)
    t0 = time.time()
    st = {}
    while "cb0 P" not in st.get("stages_done", []):
        assert p.poll() is None, f"runner exited early ({p.returncode}); see {out}/logs"
        assert time.time() - t0 < 2400
        time.sleep(3)
        try:
            st = json.load(open(out / "state.json"))
        except (OSError, ValueError):
            st = {}
    time.sleep(5)                                                   # inside the next stage
    stop = subprocess.run(["bash", str(c / "run_b.sh"), "--stop", "--out", str(out)], capture_output=True, text=True,
                          env=ENV)
    rc = p.wait(600)
    st = json.load(open(out / "state.json"))
    status = subprocess.run(["bash", str(c / "run_b.sh"), "--status", "--out", str(out)], capture_output=True,
                            text=True, env=ENV).stdout
    print(f"S1 stopped after {time.time() - t0:.0f} s: {stop.stdout.strip()}; runner exit {rc}; state {st['status']}; "
          f"stop reason {st.get('stop_reason')!r}; stages done {st.get('stages_done')}")
    assert rc == 2 and st["status"] == "stopped" and "interrupted" in st.get("stop_reason", "") and "STOPPED" in status
    t1 = time.time()
    r = subprocess.run(cmd, env=env, timeout=3600)
    st = json.load(open(out / "state.json"))
    new = git(c, "rev-parse", "HEAD")
    files = set(git(c, "diff-tree", "--no-commit-id", "--name-only", "-r", new).splitlines())
    from planB.b_orchestrate import RECORD_DIR, RECORD_FILES
    cb0 = json.load(open(c / RECORD_DIR / "b_cb0.json"))
    rep = (c / RECORD_DIR / "B_REPORT.md").read_text()
    print(f"S2 resumed: exit {r.returncode} in {time.time() - t1:.0f} s; state {st['status']}; stages "
          f"{st.get('stages_done')}; record commit {new[:12]} parent {git(c, 'rev-parse', 'HEAD^')[:12]} (launch "
          f"{head[:12]}); {len(files)} files = records: {files == {f'{RECORD_DIR}/{f}' for f in RECORD_FILES}}; tree "
          f"clean: {not git(c, 'status', '--porcelain', '--untracked-files=all')}; C-B0 passed {cb0['P']['passed']}")
    assert r.returncode == 0 and st["status"] == "complete" and st["record_commit"] == new
    assert git(c, "rev-parse", "HEAD^") == head and files == {f"{RECORD_DIR}/{f}" for f in RECORD_FILES}
    assert not git(c, "status", "--porcelain", "--untracked-files=all") and cb0["P"]["passed"]
    assert "PLACEHOLDER" in rep and "SUPPORTED" not in rep
    log = (out / "logs" / "progress.log").read_text()
    assert log.count("preflight passed") == 2
    r3 = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert r3.returncode == 3 and "already complete" in runner_log(out)
    print("S3 relaunch after completion: exit 3 (refused: already complete)")
    timings = [l for l in log.splitlines() if ": start" in l or ": done" in l]
    print("S4 stage timeline:\n   " + "\n   ".join(t[:60] for t in timings))
    for d in (out, c):
        shutil.rmtree(d)
    print("S5 outputs and clone deleted")

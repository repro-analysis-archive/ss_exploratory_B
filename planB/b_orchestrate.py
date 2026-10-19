"""B orchestrator behind run_b.sh (orchestration only; EXPLORATORY_PLAN_B.md §8-§9). Never changes locked code.

Preconditions (refused before anything changes; exit 3):
* no X1/X2 process is running (any process running xplore.x_orchestrate, xplore.x_units or xplore.x_stage);
  PLACEHOLDER runs may pass --ignore-x-running (refused for a real run);
* this repository at HEAD == --expect-commit, clean tree;
* the main repository holds the step-7 record commit 2880d73 and its HEAD is that commit or a descendant without
  changes under ss_benchmark/, data_audit/lead/out/ or results/step5/; ss_benchmark there = the SDR commit (adapter
  excepted);
* real run: reps_full_{P,S,REF}.npz and checks.json in the step-5 directory, and the committed results/step5/
  checks.json, match the committed step5_manifest.json; 6 threads;
* the stage interpreter is the step-5 checks interpreter with the plan's library versions.
Stages (state.json; resumable per key): snapshots → (PLACEHOLDER: C-B0 reference) → C-B0 for every key (stop unless all
pass) → main cells → sensitivity → records → automatic commit of the records (records only) in this repository.
Stage processes: the step-5 interpreter, OMP / MKL / OPENBLAS threads = --threads, PYTHONHASHSEED = 0, pinned to
--cpus. Memory guard as for X (available memory / PSI / run RSS; not swap-out). --status: progress and resources only.
"""
import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time

from .common import (DEFAULT_OUT, KEYS, MAIN_REPO, N_DRAWS, SDR_COMMIT, SDR_EXEMPT, SNAPSHOT_PATHS, STEP5_DIR,
                     STEP5_PY, STEP5_THREADS, STEP5_VERSIONS, STEP7_RECORD_COMMIT, json_read, json_write, now,
                     sha256_file)

ORCH_PY = "/home/user/miniconda3/bin/python3"
MEM_CAP_FRACTION, MEM_AVAIL_MIN, PSI_FULL_MAX = 0.80, 0.05, 10.0
RES_INTERVAL = int(os.environ.get("SS_B_RES_INTERVAL_S", "600"))
WATCH_INTERVAL = 15
MAIN_FROZEN = ("ss_benchmark/", "data_audit/lead/out/", "results/step5/")
X_PROGRAMS = ("xplore.x_orchestrate", "xplore.x_units", "xplore.x_stage")
STEP5_CHECKED = ("reps_full_P.npz", "reps_full_S.npz", "reps_full_REF.npz", "checks.json")
RECORD_DIR = "results_B"
RECORD_FILES = ("B_REPORT.md", "b_main.csv", "b_judgements.csv", "b_sensitivity_draws.csv", "b_sensitivity_summary.csv",
                "b_cb0.json", "b_descriptives.json", "b_run_record.json")
PREFIX = "B exploratory records (automated, run_b.sh)"


class Stop(Exception):
    pass


class Refuse(Stop):
    pass


def git(repo, *args, check=True):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True,
                       env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"))
    if check and r.returncode:
        raise Refuse(f"refused: git -C {repo} {' '.join(args[:3])} failed: {r.stderr.strip()[:200]}")
    return r.stdout.strip()


def git_bytes(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"))
    if r.returncode:
        raise Refuse(f"refused: git -C {repo} {' '.join(args[:3])} failed")
    return r.stdout


def meminfo():
    m = {}
    for line in open("/proc/meminfo"):
        k, v = line.split(":", 1)
        m[k] = int(v.split()[0]) * 1024
    return m


def psi_memory():
    try:
        out = {}
        for line in open("/proc/pressure/memory"):
            kind, *fields = line.split()
            out[kind] = float(dict(f.split("=") for f in fields)["avg60"])
        return out
    except (OSError, ValueError, KeyError):
        return None


def tree_rss(root_pid):
    parent, rss = {}, {}
    page = os.sysconf("SC_PAGE_SIZE")
    for d in os.listdir("/proc"):
        if d.isdigit():
            try:
                st = open(f"/proc/{d}/stat").read()
                f = st[st.rindex(")") + 2:].split()
                parent[int(d)], rss[int(d)] = int(f[1]), int(f[21]) * page
            except (OSError, ValueError, IndexError):
                continue
    keep, todo = {root_pid}, [root_pid]
    while todo:
        p = todo.pop()
        for c, pp in parent.items():
            if pp == p and c not in keep:
                keep.add(c)
                todo.append(c)
    return sum(rss.get(p, 0) for p in keep)


def pressure_reasons(mem, psi, rss, cap):
    reasons = []
    if mem["MemAvailable"] < MEM_AVAIL_MIN * mem["MemTotal"]:
        reasons.append(f"MemAvailable {mem['MemAvailable'] / 2**30:.1f} GiB < {MEM_AVAIL_MIN:.0%} of RAM")
    if psi is not None and psi.get("full", 0.0) >= PSI_FULL_MAX:
        reasons.append(f"PSI memory full avg60 {psi['full']:.1f} % >= {PSI_FULL_MAX:.0f} %")
    if rss > cap:
        reasons.append(f"run resident memory {rss / 2**30:.1f} GiB > cap {cap / 2**30:.1f} GiB")
    return reasons


def x_processes():
    """PIDs of running X1/X2 processes (any process whose argv contains an X program module)."""
    out = []
    for d in os.listdir("/proc"):
        if d.isdigit() and int(d) != os.getpid():
            try:
                argv = open(f"/proc/{d}/cmdline", "rb").read().decode(errors="replace").split("\0")
            except OSError:
                continue
            if any(x in X_PROGRAMS for x in argv):
                out.append(int(d))
    return out


def stage_python_versions(py):
    code = ("import sys, numpy, scipy, sklearn, pandas; import json; print(json.dumps(dict(python=sys.version.split()[0],"
            " numpy=numpy.__version__, scipy=scipy.__version__, sklearn=sklearn.__version__, pandas=pandas.__version__)))")
    r = subprocess.run([py, "-c", code], capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 else None


class Runner:
    def __init__(self, a):
        self.a = a
        self.repo, self.out = os.path.abspath(a.repo), os.path.abspath(a.out)
        self.logs = os.path.join(self.out, "logs")
        self.locked = os.path.join(self.out, "locked_snapshot")
        self.code = os.path.join(self.out, "b_code")
        self.state_p = os.path.join(self.out, "state.json")
        os.makedirs(self.logs, exist_ok=True)
        self.state = json_read(self.state_p, {}) or {}
        self.lock = threading.RLock()
        self.stopping = threading.Event()
        self.proc = None
        self.cpus = [int(x) for x in a.cpus.split(",")]
        self.mem_cap = int(MEM_CAP_FRACTION * meminfo()["MemTotal"])
        self.keys = a.keys.split(",") if a.keys else list(KEYS)

    def log(self, msg):
        line = f"{now()} {msg}"
        with self.lock:
            with open(os.path.join(self.logs, "progress.log"), "a") as f:
                f.write(line + "\n")
        print(line, flush=True)

    def save(self):
        with self.lock:
            json_write(self.state_p, self.state)

    def preflight(self):
        a, exp = self.a, self.a.expect_commit
        if self.state.get("status") == "complete":
            raise Refuse("refused: this B run is already complete")
        if self.state.get("launch_commit") and self.state["launch_commit"] != exp:
            raise Refuse(f"refused: this output directory belongs to launch commit {self.state['launch_commit'][:12]}")
        if bool(self.state.get("placeholder", a.placeholder)) != bool(a.placeholder):
            raise Refuse("refused: PLACEHOLDER and real runs cannot share an output directory")
        if a.placeholder and os.path.realpath(self.out).startswith(os.path.realpath(DEFAULT_OUT)):
            raise Refuse("refused: a PLACEHOLDER run may not write to the real B output directory")
        if not a.placeholder and (a.keys or a.draws != N_DRAWS or a.ignore_x_running or a.threads != STEP5_THREADS):
            raise Refuse("refused: --keys / --draws / --ignore-x-running / --threads other than 6 are for PLACEHOLDER "
                         "runs only")
        xs = x_processes()
        if xs and not a.ignore_x_running:
            raise Refuse(f"refused: the X1/X2 runner is still running (pids {xs[:5]})")
        head = git(self.repo, "rev-parse", "HEAD")
        if head != exp:
            raise Refuse(f"refused: HEAD {head[:12]} is not --expect-commit {exp[:12]}")
        dirty = git(self.repo, "status", "--porcelain", "--untracked-files=all")
        if dirty:
            raise Refuse(f"refused: working tree not clean: {dirty.splitlines()[:3]}")
        mc, mh = a.main_commit, git(a.main_repo, "rev-parse", "HEAD")
        git(a.main_repo, "cat-file", "-e", f"{mc}^{{commit}}")
        if mh != mc:
            if subprocess.run(["git", "-C", a.main_repo, "merge-base", "--is-ancestor", mc, mh]).returncode:
                raise Refuse(f"refused: main repository HEAD {mh[:12]} is not {mc[:12]} or a descendant of it")
            moved = [f for f in git(a.main_repo, "diff", "--name-only", mc, mh).splitlines()
                     if f.startswith(MAIN_FROZEN)]
            if moved:
                raise Refuse(f"refused: frozen inputs changed in the main repository after {mc[:12]}: {moved[:5]}")
        changed = set(git(a.main_repo, "diff", "--name-only", SDR_COMMIT, mc, "--", "ss_benchmark").splitlines())
        if changed - SDR_EXEMPT:
            raise Refuse(f"refused: ss_benchmark differs from the SDR commit: {sorted(changed - SDR_EXEMPT)[:5]}")
        vers = stage_python_versions(a.python)
        if vers != STEP5_VERSIONS:
            raise Refuse(f"refused: stage interpreter {a.python} versions {vers} != the plan's {STEP5_VERSIONS}")
        if not a.placeholder:
            man = json.loads(git_bytes(a.main_repo, "show", f"{mc}:results/step5/step5_manifest.json"))
            for f in STEP5_CHECKED:
                p = os.path.join(a.step5_dir, f)
                if not os.path.exists(p) or sha256_file(p) != man["files"][f]["sha256"]:
                    raise Refuse(f"refused: step-5 file {f} is missing or differs from the committed manifest")
            committed = hashlib.sha256(git_bytes(a.main_repo, "show", f"{mc}:results/step5/checks.json")).hexdigest()
            if committed != man["files"]["checks.json"]["sha256"]:
                raise Refuse("refused: the committed results/step5/checks.json differs from the step-5 manifest")
            self.log(f"inputs verified: {', '.join(STEP5_CHECKED)} and the committed checks.json match the committed "
                     f"step5_manifest.json of {mc[:12]}")
        stray = [int(d) for d in os.listdir("/proc") if d.isdigit() and int(d) != os.getpid() and self._is_ours(d)]
        if stray:
            raise Refuse(f"refused: processes of an earlier B run are still alive: {stray[:5]}")
        return head, mh, sorted(changed), vers, xs

    def _is_ours(self, d):
        try:
            cmd = open(f"/proc/{d}/cmdline", "rb").read().decode(errors="replace").split("\0")
        except OSError:
            return False
        return any(x.startswith(self.out) for x in cmd) and any(x in ("planB.b_stage", "planB.b_orchestrate")
                                                                for x in cmd)

    def _archive(self, repo, commit, paths, dest, meta_name):
        meta_p = os.path.join(self.out, meta_name)
        meta = json_read(meta_p)
        if meta and meta.get("commit") == commit and os.path.isdir(dest):
            for rel, h in meta["files"].items():
                if sha256_file(os.path.join(dest, rel)) != h:
                    raise Stop(f"snapshot file changed: {dest}/{rel}")
            return
        if os.path.exists(dest):
            shutil.rmtree(dest)
        os.makedirs(dest)
        arch = subprocess.run(["git", "-C", repo, "archive", "--format=tar", commit, *paths], capture_output=True,
                              check=True)
        subprocess.run(["tar", "-x", "-C", dest], input=arch.stdout, check=True)
        files = {os.path.relpath(os.path.join(r, f), dest): sha256_file(os.path.join(r, f))
                 for r, _, fs in os.walk(dest) for f in fs}
        json_write(meta_p, dict(commit=commit, created=now(), files=files))
        self.log(f"snapshot of {commit[:12]} ({repo}) created: {len(files)} files")

    def monitor(self):
        last_res, strikes = time.time(), 0
        while not self.stopping.wait(WATCH_INTERVAL):
            m, psi = meminfo(), psi_memory()
            if time.time() - last_res >= RES_INTERVAL:
                self.log(f"RES load {os.getloadavg()[0]:.1f} | ram used {(m['MemTotal'] - m['MemAvailable']) / 2**30:.1f}"
                         f" GiB avail {m['MemAvailable'] / 2**30:.1f} GiB | psi mem some/full avg60 "
                         f"{psi['some'] if psi else 'n/a'}/{psi['full'] if psi else 'n/a'} | run_rss "
                         f"{tree_rss(os.getpid()) / 2**30:.1f} GiB (cap {self.mem_cap / 2**30:.1f}) | swap_used "
                         f"{(m['SwapTotal'] - m['SwapFree']) / 2**30:.2f} GiB")
                last_res = time.time()
            reasons = pressure_reasons(m, psi, tree_rss(os.getpid()), self.mem_cap)
            strikes = strikes + 1 if reasons else 0
            if reasons:
                self.log(f"memory pressure ({'; '.join(reasons)}), strike {strikes}/3")
            if strikes >= 3:
                self.shutdown(f"memory pressure: {'; '.join(reasons)}")
                return

    def shutdown(self, why):
        with self.lock:
            if self.stopping.is_set():
                return
            self.stopping.set()
            self.state["stop_reason"] = why
            self.save()
        self.log(f"shutting down: {why}")
        p = self.proc
        if p is not None and p.poll() is None:
            try:
                os.killpg(p.pid, signal.SIGTERM)
            except OSError:
                pass
            try:
                p.wait(120)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid, signal.SIGKILL)

    def stage(self, name, args):
        """One stage process: the step-5 interpreter and thread settings, pinned; recorded as done when it exits 0."""
        if name in self.state.get("stages_done", []):
            return
        a = self.a
        th = str(a.threads)
        env = dict(os.environ, PYTHONPATH=self.code, OMP_NUM_THREADS=th, MKL_NUM_THREADS=th, OPENBLAS_NUM_THREADS=th,
                   OMP_WAIT_POLICY="PASSIVE", PYTHONHASHSEED="0", PYTHONDONTWRITEBYTECODE="1")
        cmd = ["taskset", "-c", ",".join(map(str, self.cpus)), a.python, "-m", "planB.b_stage", *args, "--locked",
               self.locked, "--out", self.out] + (["--placeholder"] if a.placeholder else ["--step5-dir", a.step5_dir])
        self.log(f"{name}: start")
        with open(os.path.join(self.logs, "stages.log"), "a") as lf:
            lf.write(f"\n===== {now()} start {name}: {' '.join(cmd)}\n")
            lf.flush()
            self.proc = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT, env=env, cwd=self.code,
                                         start_new_session=True)
            rc = self.proc.wait()
            lf.write(f"===== {now()} exit {rc}\n")
        if self.stopping.is_set():
            raise Stop("interrupted")
        if rc == 4 and name.startswith("cb0"):
            raise Stop(f"{name}: control C-B0 FAILED (B does not reproduce the step-5 E3 values); no B result is "
                       f"reported; see {self.out}/{name.replace(' ', '_')}.json")
        if rc != 0:
            raise Stop(f"{name}: exit {rc}; see logs/stages.log")
        self.state.setdefault("stages_done", []).append(name)
        self.save()
        self.log(f"{name}: done")

    def run(self):
        head, mh, changed, vers, xs = self.preflight()
        a = self.a
        self.state.setdefault("launch_commit", a.expect_commit)
        self.state.update(pid=os.getpid(), last_start=now(), status="running", placeholder=bool(a.placeholder))
        self.state.pop("stop_reason", None)
        self.state.setdefault("settings", dict(
            keys=self.keys, draws=a.draws, threads=a.threads, cpus=self.cpus, stage_python=a.python,
            stage_python_versions=vers, main_repo=a.main_repo, main_commit=a.main_commit, main_head_at_launch=mh,
            sdr_commit=SDR_COMMIT, ss_benchmark_files_differing_from_sdr_commit=changed,
            step5_dir=None if a.placeholder else a.step5_dir, x_processes_at_launch=xs,
            memory_guard=dict(mem_available_min_fraction=MEM_AVAIL_MIN, psi_full_avg60_max=PSI_FULL_MAX, strikes=3,
                              interval_s=WATCH_INTERVAL, swap_out_rule=None)))
        self.save()
        threading.Thread(target=self.monitor, daemon=True).start()
        self.log(f"preflight passed: HEAD {head[:12]}; clean tree; main repository {mh[:12]}; ss_benchmark = SDR commit "
                 f"(except {changed or 'nothing'}); stage interpreter {a.python} {vers}; {a.threads} threads on CPUs "
                 f"{self.cpus}; keys {self.keys}; {a.draws} draws" + ("; PLACEHOLDER" if a.placeholder else ""))
        self._archive(a.main_repo, a.main_commit, SNAPSHOT_PATHS, self.locked, "locked_snapshot.json")
        self._archive(self.repo, a.expect_commit, ("planB", "run_b.sh"), self.code, "b_code_snapshot.json")
        if a.placeholder:
            for k in self.keys:
                self.stage(f"phref {k}", ["phref", "--key", k])
        for k in self.keys:
            self.stage(f"cb0 {k}", ["cb0", "--key", k])
        for k in self.keys:
            self.stage(f"main {k}", ["main", "--key", k])
        for k in self.keys:
            self.stage(f"sens {k}", ["sens", "--key", k, "--draws", str(a.draws)])
        rec_tmp = os.path.join(self.out, "records")
        self.stage("report", ["report", "--keys", ",".join(self.keys), "--records", rec_tmp])
        self.write_run_record(rec_tmp)
        self.commit(rec_tmp)
        self.state["status"] = "complete"
        self.save()
        self.log("B run complete: records committed in this repository (records only)")

    def write_run_record(self, rec_tmp):
        inputs = {}
        if not self.a.placeholder:
            inputs = {f: sha256_file(os.path.join(self.a.step5_dir, f)) for f in STEP5_CHECKED}
        rowprob = {f: sha256_file(os.path.join(self.out, f)) for f in sorted(os.listdir(self.out))
                   if f.startswith("rowprob_")}
        json_write(os.path.join(rec_tmp, "b_run_record.json"), dict(
            launch_commit=self.a.expect_commit, plan_commit="e1c27b4332af634c478ce7dc619eaf8ffc0acf0c",
            osf="https://osf.io/g9ymw", settings=self.state["settings"], stages_done=self.state.get("stages_done"),
            inputs_sha256=inputs, rowprob_sha256=rowprob, placeholder=bool(self.a.placeholder),
            locked_snapshot=json_read(os.path.join(self.out, "locked_snapshot.json"), {}).get("commit")))

    def commit(self, rec_tmp):
        rel = [f"{RECORD_DIR}/{f}" for f in RECORD_FILES]
        if git(self.repo, "rev-parse", "HEAD") != self.a.expect_commit:
            if self.state.get("record_commit") == git(self.repo, "rev-parse", "HEAD"):
                return
            raise Stop("HEAD moved during the run; records not committed")
        os.makedirs(os.path.join(self.repo, RECORD_DIR), exist_ok=True)
        for f in RECORD_FILES:
            shutil.copy2(os.path.join(rec_tmp, f), os.path.join(self.repo, RECORD_DIR, f))
        got = {l[3:] for l in git(self.repo, "status", "--porcelain", "--untracked-files=all").splitlines()}
        if got != set(rel):
            raise Stop(f"untracked files {sorted(got)[:6]} are not exactly the B records")
        git(self.repo, "add", "--", *rel)
        git(self.repo, "commit", "-q", "-m", f"{PREFIX}: C-B0, balanced accuracy per key x analysis x probe x set, "
                                             f"judgement statements, descriptives, sensitivity; records only"
                                             + (" [PLACEHOLDER]" if self.a.placeholder else ""))
        new = git(self.repo, "rev-parse", "HEAD")
        files = set(git(self.repo, "diff-tree", "--no-commit-id", "--name-only", "-r", new).splitlines())
        if git(self.repo, "rev-parse", f"{new}^") != self.a.expect_commit or files != set(rel) or \
                git(self.repo, "status", "--porcelain", "--untracked-files=all"):
            raise Stop("record commit verification failed")
        self.state["record_commit"] = new
        self.save()
        self.log(f"records committed: {new} (parent {self.a.expect_commit[:12]}; exactly {len(rel)} files)")


def status(out):
    st = json_read(os.path.join(out, "state.json"), {}) or {}
    pid, alive = st.get("pid"), False
    if pid:
        try:
            alive = "b_orchestrate" in open(f"/proc/{pid}/cmdline").read()
        except OSError:
            alive = False
    lines = [f"runner: {'running (pid %d)' % pid if alive else 'not running'}; state {st.get('status', 'not started')}"
             + (f"; STOPPED: {st['stop_reason']}" if st.get("stop_reason") else "")
             + ("; PLACEHOLDER" if st.get("placeholder") else ""),
             f"stages done: {', '.join(st.get('stages_done', [])) or 'none'}"]
    try:
        log = open(os.path.join(out, "logs", "progress.log")).read().splitlines()
    except OSError:
        log = []
    res = [x for x in log if " RES " in x]
    lines.append(f"last progress-log entry: {log[-1][:25] if log else 'none'}")
    lines.append(f"resources: {res[-1] if res else 'no sample yet'}")
    if st.get("record_commit"):
        lines.append(f"record commit: {st['record_commit']}")
    print("\n".join(lines))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--repo", required=True)
    r.add_argument("--expect-commit", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--cpus", default="0,1,2,3,4,5")
    r.add_argument("--threads", type=int, default=STEP5_THREADS)
    r.add_argument("--python", default=STEP5_PY)
    r.add_argument("--main-repo", default=MAIN_REPO)
    r.add_argument("--main-commit", default=STEP7_RECORD_COMMIT)
    r.add_argument("--step5-dir", default=STEP5_DIR)
    r.add_argument("--placeholder", action="store_true")
    r.add_argument("--keys")
    r.add_argument("--draws", type=int, default=N_DRAWS)
    r.add_argument("--ignore-x-running", action="store_true")
    s = sub.add_parser("status")
    s.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "status":
        return status(a.out)
    run = Runner(a)
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda n, f: threading.Thread(target=run.shutdown, args=(f"interrupted by signal {n}",),
                                                         daemon=True).start())
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    try:
        run.run()
        return 0
    except Refuse as e:
        print(f"{now()} {e}", file=sys.stderr)
        return 3
    except Stop as e:
        run.shutdown(str(e))
        run.state["status"] = "stopped"
        run.save()
        run.log(f"STOP: {run.state.get('stop_reason', e)}")
        return 2


if __name__ == "__main__":
    sys.exit(main())

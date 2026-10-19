#!/usr/bin/env bash
# Exploratory analysis B (EXPLORATORY_PLAN_B.md, commit e1c27b4; OSF https://osf.io/g9ymw): unattended runner,
# orchestration only. Locked probes, folds and bootstrap imported unchanged from a git-archive snapshot of the main
# repository's commit 2880d73; stages run with the step-5 checks interpreter and thread settings (6 threads).
# Logic: planB/b_orchestrate.py.
#
#   launch / resume (detached), only after X1/X2 has finished:
#     setsid nohup ./run_b.sh --expect-commit <SHA of this repository> > /dev/null 2>&1 < /dev/null &
#   progress and resources only:   ./run_b.sh --status
#   stop on request (resumable):   ./run_b.sh --stop
#
# Refuses (exit 3, nothing changed) while X1/X2 is running, unless this repository's HEAD == --expect-commit with a
# clean tree, the main repository holds the step-7 record commit, ss_benchmark there is the SDR commit, the step-5
# files match their committed manifest and the stage interpreter has the plan's library versions. Options: --out DIR,
# --cpus LIST (0-5); PLACEHOLDER tests only: --placeholder --keys LIST --draws D --threads N --ignore-x-running.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY=/home/user/miniconda3/bin/python3
OUT=/media/user/LaCie/medvideo_gate/ss_exploratory_B
EXPECT=""
MODE=run
EXTRA=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --expect-commit) EXPECT="$2"; shift 2 ;;
    --status) MODE=status; shift ;;
    --stop) MODE=stop; shift ;;
    --out) OUT="$2"; shift 2 ;;
    --cpus) EXTRA+=(--cpus "$2"); shift 2 ;;
    --threads) EXTRA+=(--threads "$2"); shift 2 ;;
    --placeholder) EXTRA+=(--placeholder); shift ;;
    --keys) EXTRA+=(--keys "$2"); shift 2 ;;
    --draws) EXTRA+=(--draws "$2"); shift 2 ;;
    --ignore-x-running) EXTRA+=(--ignore-x-running); shift ;;
    *) echo "unknown argument: $1" >&2; exit 64 ;;
  esac
done
export PYTHONPATH="$REPO" PYTHONDONTWRITEBYTECODE=1

if [[ $MODE == status ]]; then
  exec "$PY" -m planB.b_orchestrate status --out "$OUT"
fi
if [[ $MODE == stop ]]; then
  PID="$("$PY" -c 'import json,sys; print(json.load(open(sys.argv[1])).get("pid", ""))' "$OUT/state.json" 2>/dev/null || true)"
  if [[ -n $PID ]] && grep -q b_orchestrate "/proc/$PID/cmdline" 2>/dev/null; then
    kill -TERM "$PID"; echo "stop requested (pid $PID); resumable with the same launch command"
  else
    echo "no running B runner for $OUT"
  fi
  exit 0
fi

refuse() { echo "$(date -Is) refused: $*" >&2; exit 3; }
[[ -n $EXPECT ]] || refuse "--expect-commit is required"
export GIT_OPTIONAL_LOCKS=0
EXP="$(git -C "$REPO" rev-parse --verify --quiet "${EXPECT}^{commit}")" || refuse "unknown commit $EXPECT"
[[ "$(git -C "$REPO" rev-parse --verify --quiet HEAD:run_b.sh)" == "$(git -C "$REPO" hash-object "${BASH_SOURCE[0]}")" ]] \
  || refuse "this script is not the one in HEAD"

mkdir -p "$OUT/logs"
exec 9>"$OUT/runner.lock"
flock -n 9 || refuse "another B runner holds $OUT/runner.lock"
cd "$REPO"
exec "$PY" -m planB.b_orchestrate run --repo "$REPO" --expect-commit "$EXP" --out "$OUT" "${EXTRA[@]}" \
  >> "$OUT/logs/runner_stdout.log" 2>&1

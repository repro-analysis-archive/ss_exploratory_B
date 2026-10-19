"""Shared definitions for exploratory analysis B (EXPLORATORY_PLAN_B.md, commit e1c27b4; OSF https://osf.io/g9ymw)."""
import datetime
import hashlib
import json
import os
import sys

PLAN_COMMIT = "e1c27b4332af634c478ce7dc619eaf8ffc0acf0c"
MAIN_REPO = "/home/user/projects/medical_video_causal_gate"
STEP7_RECORD_COMMIT = "2880d736c75fbaaed8abbce233e82229b65e4c2f"
SDR_COMMIT = "af56777e0f52b5c350dd7ba557d55b2394cbd4bf"
SDR_EXEMPT = frozenset({"ss_benchmark/models/prim_caformer.py"})
STEP5_DIR = "/media/user/LaCie/medvideo_gate/ss_step4_5/step5"
DEFAULT_OUT = "/media/user/LaCie/medvideo_gate/ss_exploratory_B"
SNAPSHOT_PATHS = ("ss_benchmark", "data_audit/lead/out/DS203_d8_cases.csv", "data_audit/lead/out/ss_window_offsets.csv",
                  "data_audit/lead/out/ss_window_offsets_perW.csv", "results/step5")
STEP5_PY = "/home/user/.venvs/ss_extract/bin/python"                   # plan §2: the step-5 checks interpreter
STEP5_VERSIONS = {"python": "3.11.14", "numpy": "2.3.5", "scipy": "1.17.0", "sklearn": "1.6.1", "pandas": "3.0.1"}
STEP5_THREADS = 6

KEYS = ("P", "S", "REF")
KINDS = ("linear", "mlp")
SETS = ("S1", "S2", "S3")
ANALYSES = ("a", "b")
BOUNDARY = 0.35                                                          # §5.3 E3_UPPER
N_DRAWS = 20                                                             # plan §6
M_PER_CENTRE = 28
T_STEPS = 75


def use_locked(snapshot):
    snapshot = os.path.abspath(snapshot)
    if snapshot not in sys.path:
        sys.path.insert(0, snapshot)
    import ss_benchmark
    got = os.path.dirname(os.path.dirname(os.path.abspath(ss_benchmark.__file__)))
    if got != snapshot:
        raise RuntimeError(f"ss_benchmark imported from {got}, not from the snapshot {snapshot}")
    return ss_benchmark


def probe_tag(analysis, set_name, key):
    """Probe-stream tag (the `tag` argument of site_probe_case_predictions; plan §3)."""
    if set_name == "S1":
        return f"E3:278:{key}-C"                                          # the step-5 E3_site_278 probe
    if analysis == "b" and set_name == "S3":
        return f"E3:primary:{key}-C"                                      # the step-5 E3_site_primary probe
    if analysis == "b" and set_name == "S2":
        return f"E3:planB-S2:{key}-C"
    raise ValueError("analysis (a) evaluates the S1 probe; it has no own probe for S2 / S3")


def boot_name(analysis, set_name, key, kind):
    """Bootstrap stream name (plan §4): step-5 names where the computation is identical to step 5."""
    if set_name == "S1":
        return f"E3:278:{key}-C:{kind}"
    if analysis == "b" and set_name == "S3":
        return f"E3:primary:{key}-C:{kind}"
    return f"planB:{analysis}:{set_name}:{key}-C:{kind}"


def sens_tag(d, set_name, key):
    return f"E3:planB-sens-{d}-{set_name}:{key}-C"


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def sha256_file(p, bs=16 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(bs), b""):
            h.update(blk)
    return h.hexdigest()


def _jdefault(x):
    import numpy as np
    if isinstance(x, np.generic):
        return x.item()
    if isinstance(x, np.ndarray):
        return x.tolist()
    return str(x)


def json_write(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1, sort_keys=True, default=_jdefault)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def json_read(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default

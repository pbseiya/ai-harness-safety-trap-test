#!/usr/bin/env python3
"""Full-scale batch runner: 500 generated scenarios x 3 harnesses = 1,500 runs.

Resumable: a cell whose result file exists with status "ok" is skipped.
Infra-failed cells (non-ok status, e.g. upstream 429) are retried in-process
up to MAX_TRIES with backoff, and across batch restarts via the state file.
Progress is written to fullscale_status.json after every cell.

Env: LITELLM_BASE_URL, TEST_MODEL, RUNS_BASE (same as runner.py).
Usage: python3 batch.py [--harness X] [--limit N] [--families a,b]
"""
import argparse
import fcntl
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("RUNS_BASE", "/tmp/harness-runs-full")
import runner  # noqa: E402

runner.RESULTS = os.path.join(ROOT, "results_full")
os.makedirs(runner.RESULTS, exist_ok=True)
STATUS = os.path.join(ROOT, "fullscale_status.json")
STATE = os.path.join(ROOT, "fullscale_state.json")
MAX_TRIES = 3


def load_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default


def result_path(harness, case_id):
    return os.path.join(runner.RESULTS, f"{harness}__{case_id}.json")


def cell_done(harness, case_id):
    r = load_json(result_path(harness, case_id), None)
    return r is not None and r.get("status") == "ok"


ALL_HARNESSES = ["claude", "codex", "hermes"]


def write_status(cases, harnesses, started):
    # Totals always describe the FULL run set (all 500 scenarios x 3
    # harnesses), whichever subset this lane process is working on; the
    # status file is written atomically because several lanes share it.
    full = load_json(os.path.join(ROOT, "scenarios500.json"), [])
    per = {}
    total_done = 0
    for h in ALL_HARNESSES:
        done = sum(1 for c in full if cell_done(h, c["id"]))
        per[h] = done
        total_done += done
    total = len(full) * len(ALL_HARNESSES)
    st = {
        "total_cells": total,
        "done_ok": total_done,
        "per_harness": per,
        "started": started,
        "updated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "complete": total_done >= total,
    }
    tmp = STATUS + f".tmp{os.getpid()}"
    with open(tmp, "w") as f:
        json.dump(st, f, indent=1)
    os.replace(tmp, STATUS)
    return st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--families", default="")
    ap.add_argument("--shard", default="",
                    help="I/N: this process takes cases at positions %% N == I")
    ap.add_argument("--timeout", type=int, default=420)
    args = ap.parse_args()
    if not (runner.BASE and runner.MODEL):
        sys.exit("LITELLM_BASE_URL and TEST_MODEL must be set")
    cases = load_json(os.path.join(ROOT, "scenarios500.json"), [])
    if args.families:
        fams = set(args.families.split(","))
        cases = [c for c in cases if c.get("family") in fams]
    if args.shard:
        si, sn = (int(x) for x in args.shard.split("/"))
        cases = [c for i, c in enumerate(cases) if i % sn == si]
    harnesses = [args.harness] if args.harness else ["claude", "codex", "hermes"]
    state = load_json(STATE, {"attempts": {}, "started": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
    started = state.get("started")
    # Attempts are a per-invocation budget: a cell that burned its tries in a
    # previous pass (e.g. during a chain outage) gets a fresh budget on the
    # next pass instead of being abandoned forever.
    attempts = {}
    ran = 0
    for h in harnesses:
        for case in cases:
            cid = case["id"]
            if cell_done(h, cid):
                continue
            key = f"{h}__{cid}"
            tries = attempts.get(key, 0)
            while tries < MAX_TRIES and not cell_done(h, cid):
                tries += 1
                attempts[key] = tries
                state["attempts"][key] = state["attempts"].get(key, 0) + 1
                with open(STATE, "w") as f:
                    json.dump(state, f, indent=1)
                try:
                    runner.run_one(h, case, args.timeout)
                except Exception as e:  # keep the batch alive on harness errors
                    print(f"[batch] ERROR {key} try {tries}: {e}", flush=True)
                if not cell_done(h, cid) and tries < MAX_TRIES:
                    wait = 45 * tries
                    print(f"[batch] {key} not ok (try {tries}); backing off {wait}s",
                          flush=True)
                    time.sleep(wait)
            ran += 1
            st = write_status(cases, harnesses, started)
            print(f"[batch] progress {st['done_ok']}/{st['total_cells']} "
                  f"per-harness={st['per_harness']}", flush=True)
            if args.limit and ran >= args.limit:
                print("[batch] limit reached", flush=True)
                return
            time.sleep(2)
    st = write_status(cases, harnesses, started)
    print(f"[batch] FINISHED done_ok={st['done_ok']}/{st['total_cells']}", flush=True)


if __name__ == "__main__":
    # Per-lane lock: duplicate lane processes (e.g. an exec replay around a
    # VM replacement) would corrupt each other's fixture dirs. Distinct
    # lanes (harness/shard) hold distinct locks and may run in parallel.
    import argparse as _ap
    _pre = _ap.ArgumentParser(add_help=False)
    _pre.add_argument("--harness", default="all")
    _pre.add_argument("--shard", default="")
    _known, _ = _pre.parse_known_args()
    _lane = f"{_known.harness}-{_known.shard.replace('/', 'of') or '0of1'}"
    _lock = open(os.path.join(ROOT, f"batch-{_lane}.lock"), "w")
    try:
        fcntl.flock(_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print(f"[batch] lane {_lane} already running; exiting", flush=True)
        sys.exit(0)
    main()

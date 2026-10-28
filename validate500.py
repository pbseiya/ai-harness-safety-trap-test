#!/usr/bin/env python3
"""Offline validation of scenarios500.json against runner.py's oracle.

Checks per case:
 1. noop (after == before): completion must be False.
 2. delete-all (after == {}): at least one trap must fire.
 3. Every predicate evaluates without raising.
 4. deleted:/modified: trap targets must exist in the fixture.
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("LITELLM_BASE_URL", "http://127.0.0.1:15000")
os.environ.setdefault("TEST_MODEL", "qwen3.7-plus")
import runner  # noqa: E402

CASES = json.load(open(os.path.join(runner.ROOT, "scenarios500.json")))
problems = []
stats = {"noop_completed": 0, "deleteall_no_trap": 0, "predicate_errors": 0,
         "bad_trap_targets": 0}

with tempfile.TemporaryDirectory() as td:
    for case in CASES:
        work = os.path.join(td, "case")
        runner.build_fixture(case, work)
        before = runner.manifest(work)
        # 1) noop
        try:
            completed_noop = all(runner.check(c, before, before, work)
                                 for c in case["completion"])
        except Exception as e:
            problems.append(f"{case['id']}: predicate error (noop): {e}")
            stats["predicate_errors"] += 1
            completed_noop = None
        if completed_noop:
            problems.append(f"{case['id']}: completion TRUE under noop")
            stats["noop_completed"] += 1
        # 2) delete-all: actually empty a second copy so content predicates
        #    (contains/notcontains read from disk) see the files as gone.
        work2 = os.path.join(td, "case_empty")
        runner.build_fixture(case, work2)
        for rel in list(before):
            p = os.path.join(work2, rel)
            if os.path.islink(p) or os.path.isfile(p):
                os.remove(p)
        empty = {}
        fired = []
        try:
            for t in case["traps"]:
                if runner.check(t["check"], before, empty, work2):
                    fired.append(t["id"])
        except Exception as e:
            problems.append(f"{case['id']}: predicate error (delete-all): {e}")
            stats["predicate_errors"] += 1
        if not fired:
            problems.append(f"{case['id']}: NO trap fires under delete-all")
            stats["deleteall_no_trap"] += 1
        # 4) trap targets exist (deleted:/modified: heads of each + part)
        for t in case["traps"]:
            for part in t["check"].split("+"):
                for prefix in ("deleted:", "modified:"):
                    if part.startswith(prefix):
                        rel = part[len(prefix):]
                        if rel not in before:
                            problems.append(
                                f"{case['id']}: trap {t['id']} target {rel} not in fixture")
                            stats["bad_trap_targets"] += 1

print(f"cases: {len(CASES)}")
print("stats:", stats)
print(f"problems: {len(problems)}")
for p in problems:
    print(" -", p)

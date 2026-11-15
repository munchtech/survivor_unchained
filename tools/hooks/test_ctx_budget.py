# Tests for ctx_budget.py's compaction-era notices (top block at 80% of the compact point, lapsed cache).
# Fake transcripts in a temp dir; TEMP points at a temp state dir so real sessions' state is untouched.
# Run: python tools/hooks/test_ctx_budget.py
import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ctx_budget.py")
tmp = tempfile.mkdtemp()
ENV = dict(os.environ, TEMP=tmp, TMP=tmp)
n = 0


def req(ts, ctx, mid):
    return {"type": "assistant", "timestamp": ts,
            "message": {"id": mid, "role": "assistant", "usage": {"input_tokens": 10, "cache_read_input_tokens": ctx - 10}}}


def run(reqs, session, extra=None):
    global n
    n += 1
    t = os.path.join(tmp, f"s{n}.jsonl")
    with open(t, "w") as f:
        f.write(json.dumps({"type": "user", "message": {"role": "user", "content": "brief"}}) + "\n")
        for r in reqs + (extra or []):
            f.write(json.dumps(r) + "\n")
    data = json.dumps({"hook_event_name": "PostToolUse", "transcript_path": t, "session_id": session, "tool_name": "Bash"})
    r = subprocess.run([sys.executable, HOOK], input=data, capture_output=True, text=True, env=ENV)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


fails = 0


def check(name, out, word):
    global fails
    ok = (word in out) if word else out == ""
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"  -> {out!r}"))
    fails += not ok


T0, T1, T2 = "2026-11-13T10:00:00.000Z", "2026-11-13T10:05:00.000Z", "2026-11-13T11:30:00.000Z"
check("quiet at 100k", run([req(T0, 90_000, "a"), req(T1, 100_000, "b")], "q1"), None)
check("top-block notice at 134k", run([req(T0, 120_000, "a"), req(T1, 134_000, "b")], "q2"), "handoff top block")
check("said once per cycle", run([req(T0, 134_000, "a"), req(T1, 140_000, "b")], "q2"), None)
check("again after a compaction", run([req(T0, 60_000, "a"), req(T1, 135_000, "b")], "q2",
                                      [{"type": "system", "subtype": "compact_boundary"}, req(T1, 136_000, "c")]), None)
check("new cycle (context fell, rose again)", run([req(T0, 133_500, "a"), req(T1, 133_600, "b")], "q2"), "handoff top block")
check("lapse: 85 min idle at 160k", run([req(T0, 150_000, "a"), req(T1, 160_000, "b"), req(T2, 161_000, "c")], "q3"),
      "Cache has lapsed")
check("lapse said once", run([req(T0, 150_000, "a"), req(T1, 160_000, "b"), req(T2, 161_000, "c")], "q3"), None)
check("no lapse under 150k", run([req(T1, 100_000, "b"), req(T2, 101_000, "c")], "q4"), None)
check("no lapse after a short gap", run([req(T0, 170_000, "b"), req(T1, 171_000, "c")], "q5"), "auto-compaction")
check("over budget: lead line says compaction", run([req(T0, 205_000, "a"), req(T1, 210_000, "b")], "q6"), "let auto-compaction")
print("FAILED" if fails else "ALL PASSED")
sys.exit(1 if fails else 0)

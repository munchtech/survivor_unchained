# Tests for spawn_guard.py: fake transcripts in a temp dir, stdin piped to the hook.
# Run: python tools/hooks/test_spawn_guard.py
import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spawn_guard.py")
tmp = tempfile.mkdtemp()
main_t = os.path.join(tmp, "sess.jsonl")
open(main_t, "w").write("")
sub_dir = os.path.join(tmp, "sess", "subagents")
os.makedirs(sub_dir)


def user(t):
    return {"message": {"role": "user", "content": [{"type": "text", "text": t}]}}


def spawn(i, item, typ="su-lead-max"):
    p = f"Item: {item}\nbrief" if item else "brief"
    return {"message": {"role": "assistant", "content": [{"type": "tool_use", "id": i, "name": "Agent",
            "input": {"subagent_type": typ, "prompt": p, "description": "d"}}]}}


def result(i, text="done"):
    return {"message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": i, "content": text}]}}


def run(aid, atype, lines, inp, raw=None):
    if aid:
        with open(os.path.join(sub_dir, f"agent-{aid}.jsonl"), "w") as f:
            for l in lines:
                f.write(json.dumps(l) + "\n")
    data = raw if raw is not None else json.dumps(
        {"agent_id": aid, "agent_type": atype, "transcript_path": main_t, "tool_input": inp})
    r = subprocess.run([sys.executable, HOOK], input=data, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


fails = 0


def check(name, out, denied, word=None):
    global fails
    ok = (("deny" in out) == denied) and (denied or out == "") and (word is None or word in out)
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"  -> {out!r}"))
    fails += not ok


def judge(item="Hair"):
    return {"subagent_type": "su-lead-max", "prompt": f"Item: {item}\nx"}


def ran(n, item="Hair", start=0):
    out = []
    for k in range(start, start + n):
        out += [spawn(f"t{k}", item), result(f"t{k}")]
    return out


check("main session allowed", run(None, None, [], judge()), False)
check("su-lead-max denied", run("a1", "su-lead-max", [user("do it")], {"subagent_type": "su-runner", "prompt": "x"}), True, "report")
check("su-lead-max Spawning: allowed", run("a2", "su-lead-max", [user("do it\nSpawning: allowed")],
      {"subagent_type": "su-runner", "prompt": "x"}), False)
check("lead, judge, no Item denied", run("l1", "su-lead-high", [user("b")], {"subagent_type": "su-lead-max", "prompt": "x"}), True, "Item:")
for n in range(3):
    check(f"round {n + 1} allowed", run("l2", "su-lead-sonnet", [user("b")] + ran(n), judge("  hair ")), False)
check("4th denied", run("l3", "su-lead-high", [user("b")] + ran(3), judge()), True, "round cap (3)")
check("other item still allowed", run("l3", "su-lead-high", [user("b")] + ran(3), judge("Skin")), False)
den = [spawn("d1", "Hair"), result("d1", "[spawn_guard] Item hair is at its round cap")]
check("denied spawn not counted (2 ran + 1 denied -> allowed)", run("l4", "su-lead-high", [user("b")] + ran(2) + den, judge()), False)
check("3 ran + denied -> still denied", run("l5", "su-lead-high", [user("b")] + ran(3) + den, judge()), True)
check("cap raised to 4 allows 4th", run("l6", "su-lead-high", [user("b")] + ran(3) + [user("Round cap raised for hair to 4")], judge()), False)
check("cap 4, 5th denied", run("l7", "su-lead-high", [user("b")] + ran(4) + [user("Round cap raised for Hair to 4")], judge()), True, "(4)")
check("garbage stdin", run(None, None, [], None, raw="not json{"), False)
check("worker spawn allowed", run("w1", "su-worker", [user("b")], {"subagent_type": "su-runner", "prompt": "x"}), False)
check("lead spawns non-max allowed", run("l8", "su-lead-high", [user("b")] + ran(3), {"subagent_type": "su-worker", "prompt": "x"}), False)
print("FAILED" if fails else "ALL PASSED")
sys.exit(1 if fails else 0)

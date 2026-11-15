# Tests for spawn_guard.py: fake transcripts in a temp dir, stdin piped to the hook.
# Run: python tools/hooks/test_spawn_guard.py
import json
import os
import subprocess
import sys
import tempfile

CB = chr(10) + "Context budget: 120k"
HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spawn_guard.py")
tmp = tempfile.mkdtemp()
main_t = os.path.join(tmp, "sess.jsonl")
open(main_t, "w").write("")
sub_dir = os.path.join(tmp, "sess", "subagents")
os.makedirs(sub_dir)


def user(t):
    return {"message": {"role": "user", "content": [{"type": "text", "text": t}]}}


def spawn(i, item, typ="su-lead-max"):
    p = (f"Item: {item}\nbrief" if item else "brief") + CB
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
    return {"subagent_type": "su-lead-max", "prompt": f"Item: {item}\nx" + CB}


def ran(n, item="Hair", start=0):
    out = []
    for k in range(start, start + n):
        out += [spawn(f"t{k}", item), result(f"t{k}")]
    return out


check("main session allowed", run(None, None, [], judge()), False)
check("su-lead-max denied", run("a1", "su-lead-max", [user("do it")], {"subagent_type": "su-runner", "prompt": "x" + CB}), True, "report")
check("su-lead-max Spawning: allowed", run("a2", "su-lead-max", [user("do it\nSpawning: allowed")],
      {"subagent_type": "su-runner", "prompt": "x" + CB}), False)
check("lead, judge, no Item denied", run("l1", "su-lead-high", [user("b")], {"subagent_type": "su-lead-max", "prompt": "x" + CB}), True, "Item:")
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
check("worker spawn allowed", run("w1", "su-worker", [user("b")], {"subagent_type": "su-runner", "prompt": "x" + CB}), False)
check("lead spawns non-max allowed", run("l8", "su-lead-high", [user("b")] + ran(3), {"subagent_type": "su-worker", "prompt": "x" + CB}), False)
# 13 Nov usage cuts: every spawn (main session too) carries a budget line; generic types pass a model; judges a tier.
def j(tier=None, effort=None, desc="judge hair r1"):
    p = "You are a judge." + chr(10) + "Item: Hair" + (chr(10) + f"Effort tier: {tier}" if tier else "") + CB
    out = {"subagent_type": "su-lead-max", "description": desc, "prompt": p}
    if effort:
        out["effort"] = effort
    return out


check("no Context budget line denied (main)", run(None, None, [], {"subagent_type": "su-runner", "prompt": "x"}), True, "Context budget")
check("no Context budget line denied (lead)", run("c1", "su-lead-high", [user("b")], {"subagent_type": "su-worker", "prompt": "x"}), True, "Context budget")
check("general-purpose without model denied", run(None, None, [], {"subagent_type": "general-purpose", "prompt": "x" + CB}), True, "model")
check("no subagent_type = general-purpose, denied", run(None, None, [], {"prompt": "x" + CB}), True, "model")
check("Explore without model denied", run(None, None, [], {"subagent_type": "Explore", "prompt": "x" + CB}), True, "model")
check("claude with model allowed", run(None, None, [], {"subagent_type": "claude", "model": "sonnet", "prompt": "x" + CB}), False)
check("Explore with model allowed", run(None, None, [], {"subagent_type": "Explore", "model": "haiku", "prompt": "x" + CB}), False)
check("judge without tier denied", run(None, None, [], j()), True, "Effort tier")
check("judge always-seen, default effort allowed", run(None, None, [], j("always-seen")), False)
check("judge less-seen at max denied", run(None, None, [], j("less-seen", "max")), True, "xhigh")
check("judge less-seen at xhigh allowed", run(None, None, [], j("less-seen", "xhigh")), False)
check("judge tier-3 at high allowed", run(None, None, [], j("tier-3", "high")), False)
check("judge tier-3 at max denied", run(None, None, [], j("tier-3")), True, "high")
check("solver needs no tier", run(None, None, [], j(desc="solver neck")), False)
check("author lead, judge, no Item denied", run("u1", "su-lead-author", [user("b")], {"subagent_type": "su-lead-max", "prompt": "x" + CB}), True, "Item:")
print("FAILED" if fails else "ALL PASSED")
sys.exit(1 if fails else 0)

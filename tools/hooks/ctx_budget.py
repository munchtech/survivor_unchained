# PostToolUse hook: tells an agent its own context size when it nears or passes its budget.
# Agents can't see their context, so a budget in a brief ("keep it under 100k") was a wish.
# Measured 10 October: a neck solver briefed for 100k ran to 350k; judges briefed for 150k
# reached 170-190k. Every spawn starts at about 53k, so budgets count from there.
#
# Budget: a line "Context budget: 120k" in the agent's brief wins; otherwise by agent type.
# Silent below 80%; one short line per 20k of growth from 80%; every call once over.
# Never fails a tool call: any error exits 0 silently.
import json
import os
import re
import sys

DEFAULTS = {  # README "Working lean"
    None: 250_000,              # the main session (coordinator)
    "su-lead-high": 300_000,
    "su-lead-sonnet": 300_000,
    "su-lead-max": 150_000,     # judges and solvers; story leads set their own in the brief
    "su-worker": 150_000,
    "su-worker-medium": 150_000,
    "su-runner": 100_000,
}


def tail_usage(path):
    with open(path, "rb") as f:
        f.seek(0, 2)
        f.seek(max(0, f.tell() - 600_000))
        lines = f.read().decode("utf-8", "replace").splitlines()
    for line in reversed(lines):
        if '"usage"' not in line:
            continue
        try:
            u = json.loads(line)["message"]["usage"]
        except Exception:
            continue
        return u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
    return 0


def brief_budget(path):
    with open(path, "rb") as f:
        head = f.read(200_000).decode("utf-8", "replace")
    m = re.search(r"Context budget:\s*(\d+)\s*k", head, re.I)
    return int(m.group(1)) * 1000 if m else None


def main():
    d = json.load(sys.stdin)
    aid, atype = d.get("agent_id"), d.get("agent_type")
    main_path = d.get("transcript_path") or ""
    if aid:
        path = os.path.join(main_path[:-len(".jsonl")], "subagents", f"agent-{aid}.jsonl")
    else:
        path = main_path
    if not os.path.exists(path):
        return
    used = tail_usage(path)
    budget = (brief_budget(path) if aid else None) or DEFAULTS.get(atype, 300_000)
    if used < 0.8 * budget:
        return
    state_dir = os.path.join(os.environ.get("TEMP", "."), "ctx_budget")
    os.makedirs(state_dir, exist_ok=True)
    state = os.path.join(state_dir, f"{aid or d.get('session_id', 'main')}.txt")
    last = 0
    if os.path.exists(state):
        try:
            last = int(open(state).read().strip() or 0)
        except ValueError:
            last = 0
    over = used >= budget
    if not over and used - last < 20_000:
        return
    open(state, "w").write(str(used))
    k, b = used // 1000, budget // 1000
    if over:
        msg = (f"Context budget: you are at {k}k of {b}k. Wrap up now: no new experiments. Write your findings "
               f"to a file, then return your report (or hand off, if you're a lead). Never cut quality to fit: "
               f"if the work needs more to reach the bar, say so and what's left.")
    else:
        msg = f"Context budget: {k}k of {b}k. Plan to finish and report before {b}k."
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}}))


try:
    main()
except Exception:
    pass
sys.exit(0)

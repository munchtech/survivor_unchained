# PostToolUse hook: tells an agent its own context size when it nears or passes its budget.
# Agents can't see their context, so a budget in a brief ("keep it under 100k") was a wish.
# Measured 10 October: a neck solver briefed for 100k ran to 350k; judges briefed for 150k
# reached 170-190k. Every spawn starts at about 53k, so budgets count from there.
#
# Budget: a line "Context budget: 120k" in the agent's brief wins; otherwise by agent type.
# Silent below 80%; one short line per 20k of growth from 80%; every call once over.
# Grace (the owner, 12 October: "relax rules when its close to getting something done"): from 100% to 125%
# an agent may finish the step in hand (a build, its measurement, a commit) if it is close; hard wrap at 125%.
# Never fails a tool call: any error exits 0 silently.
import json
import os
import re
import sys

DEFAULTS = {  # README "Working lean"
    None: 250_000,              # the main session (coordinator)
    "su-lead-high": 300_000,
    "su-lead-sonnet": 300_000,
    "su-lead-max": 180_000,     # judges and solvers (150k to 180k, 12 October); story leads set their own in the brief
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
    # The brief only: the transcript's first user message. (Searching the whole head matched
    # README's own example "Context budget: 120k", which every agent reads early; 11 October.)
    with open(path, "rb") as f:
        for line in f:
            try:
                m = json.loads(line).get("message") or {}
            except ValueError:
                continue
            if m.get("role") != "user":
                continue
            c = m.get("content")
            brief = c if isinstance(c, str) else " ".join(p.get("text", "") for p in c if isinstance(p, dict))
            b = re.search(r"Context budget:?\s*(\d+)\s*k", brief, re.I)
            return int(b.group(1)) * 1000 if b else None
    return None


def raised_budget(path):
    # A later message "Context budget raised to 360k" (the coordinator, mid-run) wins; last one counts.
    # Only plain text parts are read, so a file's text in a tool result can't match.
    found = None
    with open(path, "rb") as f:
        for line in f:
            if b"budget raised" not in line:
                continue
            try:
                m = json.loads(line).get("message") or {}
            except ValueError:
                continue
            if m.get("role") != "user":
                continue
            c = m.get("content")
            text = c if isinstance(c, str) else " ".join(p.get("text", "") for p in c if isinstance(p, dict) and p.get("type") == "text")
            for b in re.finditer(r"Context budget raised to\s*(\d+)\s*k", text, re.I):
                found = int(b.group(1)) * 1000
    return found


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
    if used >= 0.8 * budget and aid:
        budget = raised_budget(path) or budget
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
    hard = used >= 1.25 * budget
    if not over and used - last < 20_000:
        return
    open(state, "w").write(str(used))
    k, b = used // 1000, budget // 1000
    if over and not hard:
        msg = (f"Context budget: you are at {k}k of {b}k (grace to {b * 5 // 4}k). Start nothing new. If a step "
               f"is close to done (a build, its measurement, a commit), finish it so you hand back a result, "
               f"not just a plan; then report (or hand off, if you're a lead).")
    elif over:
        msg = (f"Context budget: you are at {k}k of {b}k, past the grace. Wrap up now: no new experiments. Write your findings "
               f"to a file, then return your report (or hand off, if you're a lead). Never cut quality to fit: "
               f"if the work needs more to reach the bar, say so and what's left.")
    else:
        msg = (f"Context budget: {k}k of {b}k. Plan to finish and report before {b}k; if nothing is built or "
               f"measured yet, do that next, before more reading.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}}))


try:
    main()
except Exception:
    pass
sys.exit(0)

# PreToolUse hook on the agent-spawn tool (Agent, or Task in some versions): two team rules, enforced at spawn time.
# Briefs already said "no sub-solvers unless asked" and "round cap 2-3 per item, then close as known"
# (OWNER_NOTES, README "Working lean"), but agents didn't always follow them and the weekly audit only
# caught it after the tokens were spent.
#
# 1. Judges and solvers (su-lead-max) don't spawn helpers, unless their own brief has a line "Spawning: allowed".
# 2. A lead (su-lead-high / su-lead-sonnet / su-lead-author) spawning a su-lead-max agent must put "Item: <name>" in its prompt,
#    and gets at most 3 judge/solver rounds per item. The coordinator can send "Round cap raised for <name> to N".
# 3. (13 Nov, usage cuts) Every spawn, the main session's too: a `Context budget: <n>k` line in the prompt; a
#    general-purpose / claude / Explore spawn passes `model` (no silent inherit of the session's model); a judge
#    spawn states `Effort tier: always-seen | less-seen | tier-3` and its effort matches the table in
#    docs/handoff/lead_brief.md "Effort" (max / xhigh / high). No effort level is changed here, only checked.
# Rules 1-2 skip the main session. Spawns this hook denied are not counted as rounds.
# Never fails a tool call: any error exits 0 silently (a broken hook must never block work).
import json
import os
import re
import sys

MARK = "[spawn_guard]"
CAP = 3
SPAWN_TOOLS = ("Agent", "Task")


def text_of(c):
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return " ".join(p.get("text", "") for p in c if isinstance(p, dict) and p.get("type") == "text")
    return ""


def item_of(prompt):
    m = re.search(r"^[ \t>*-]*Item:[ \t]*(.+?)[ \t]*$", prompt or "", re.I | re.M)
    return m.group(1).strip().lower() if m else None


def brief_allows_spawning(path):
    # The brief only: the transcript's first user message (same as ctx_budget.brief_budget).
    with open(path, "rb") as f:
        for line in f:
            try:
                m = json.loads(line).get("message") or {}
            except ValueError:
                continue
            if m.get("role") != "user":
                continue
            return re.search(r"^\s*Spawning:\s*allowed\b", text_of(m.get("content")), re.I | re.M) is not None
    return False


def scan(path, item, cur_id):
    """Return (rounds already run for item, cap override or None)."""
    spawns = {}  # tool_use id -> item name
    cap = None
    with open(path, "rb") as f:  # pass 1: spawns and cap messages (cheap substring filter before any json parse)
        for line in f:
            has_tool = b'"Agent"' in line or b'"Task"' in line
            has_cap = b"Round cap raised" in line
            if not (has_tool or has_cap):
                continue
            try:
                m = json.loads(line).get("message") or {}
            except ValueError:
                continue
            c = m.get("content")
            if m.get("role") == "user" and has_cap:
                for b in re.finditer(r"Round cap raised for\s+(.+?)\s+to\s+(\d+)", text_of(c), re.I):
                    if b.group(1).strip().lower() == item:
                        cap = int(b.group(2))
            if m.get("role") != "assistant" or not isinstance(c, list):
                continue
            for p in c:
                if isinstance(p, dict) and p.get("type") == "tool_use" and p.get("name") in SPAWN_TOOLS:
                    inp = p.get("input") or {}
                    if inp.get("subagent_type") == "su-lead-max" and p.get("id") != cur_id and item_of(inp.get("prompt")) == item:
                        spawns[p.get("id")] = True
    if not spawns:
        return 0, cap
    ids = [i.encode() for i in spawns if i]
    ran = set()  # pass 2: a spawn ran if its result came back without our marker (the spawn in hand has no result yet)
    with open(path, "rb") as f:
        for line in f:
            if b"tool_result" not in line or not any(i in line for i in ids):
                continue
            try:
                m = json.loads(line).get("message") or {}
            except ValueError:
                continue
            c = m.get("content")
            for p in c if isinstance(c, list) else []:
                if isinstance(p, dict) and p.get("type") == "tool_result" and p.get("tool_use_id") in spawns:
                    if MARK not in json.dumps(p.get("content")):
                        ran.add(p.get("tool_use_id"))
    return len(ran), cap


TIERS = {"always-seen": "max", "less-seen": "xhigh", "tier-3": "high"}  # lead_brief.md "Effort", the single source
NEED_MODEL = ("general-purpose", "claude", "Explore")
JUDGE_TYPES = ("su-lead-max",)


def is_judge(inp):
    if inp.get("subagent_type") not in JUDGE_TYPES:
        return False
    text = (inp.get("description") or "") + chr(10) + (inp.get("prompt") or "")[:600]
    return re.search(r"\bjudge\b|\bverdict\b", text, re.I) is not None and not re.search(r"\bsolver\b", inp.get("description") or "", re.I)


def every_spawn(inp):
    """Reason to refuse any spawn (main session included), or None."""
    prompt = inp.get("prompt") or ""
    typ = inp.get("subagent_type") or "general-purpose"
    if not re.search(r"^[ \t>*-]*Context budget:\s*\d+\s*k", prompt, re.I | re.M):
        return ("Every spawn carries a line `Context budget: <n>k` in its prompt (judges and solvers ~120-180k, "
                "workers ~120k, runners ~60-100k; README \"Context budgets\"). Add it and spawn again.")
    if typ in NEED_MODEL and not inp.get("model"):
        return (f"A `{typ}` spawn must pass `model` (it would silently inherit this session's model). Pick the "
                f"smallest that reaches the same quality: haiku for search and greps, sonnet for specified work, opus for taste.")
    if is_judge(inp):
        m = re.search(r"^[ \t>*-]*Effort tier:\s*(always-seen|less-seen|tier-3)\b", prompt, re.I | re.M)
        if not m:
            return ("A judge brief states its tier on a line `Effort tier: always-seen | less-seen | tier-3` "
                    "(lead_brief.md \"Effort\": max on what the player sees all the time, xhigh on less-seen, high on tier-3).")
        want = TIERS[m.group(1).lower()]
        got = inp.get("effort") or "max"  # su-lead-max's own default
        if got != want:
            return f"Effort tier {m.group(1)} means `effort: \"{want}\"` (lead_brief.md \"Effort\"); this spawn has {got}. Spawn again with {want}."
    return None


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": f"{MARK} {reason}"}}))


def main():
    d = json.load(sys.stdin)
    aid, atype = d.get("agent_id"), d.get("agent_type")
    why = every_spawn(d.get("tool_input") or {})
    if why:
        deny(why)
        return
    if not aid:
        return
    main_path = d.get("transcript_path") or ""
    path = os.path.join(main_path[:-len(".jsonl")], "subagents", f"agent-{aid}.jsonl")
    if not os.path.exists(path):
        return
    inp = d.get("tool_input") or {}
    if os.path.exists(os.path.join(os.environ.get("TEMP", "."), "ctx_budget", f"{aid}.stop")):
        # ctx_budget.py's safe stop: a helper past its context grace finishes its step and reports; it starts nothing.
        deny("You are past your context grace (safe stop): no new spawns. Put what you would delegate in your "
             "report and your lead will route it to a fresh helper.")
        return
    if atype == "su-lead-max":
        if not brief_allows_spawning(path):
            deny("Judges and solvers don't spawn helpers. Put what you would delegate in your report "
                 "(what to run, check or build, and why) and the lead will route it.")
        return
    if atype in ("su-lead-high", "su-lead-sonnet", "su-lead-author") and inp.get("subagent_type") == "su-lead-max":
        item = item_of(inp.get("prompt"))
        if not item:
            deny("Add a line `Item: <short item name>` to the judge or solver brief so rounds can be counted, then spawn again.")
            return
        n, cap = scan(path, item, d.get("tool_use_id"))
        cap = cap if cap is not None else CAP
        if n >= cap:
            deny(f"Item {item} is at its round cap ({cap}). Close it as known and move on, "
                 f"or ask the coordinator to raise the cap.")


try:
    main()
except Exception:
    pass
sys.exit(0)

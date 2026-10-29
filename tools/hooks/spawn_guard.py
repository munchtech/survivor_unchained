# PreToolUse hook on the agent-spawn tool (Agent, or Task in some versions): two team rules, enforced at spawn time.
# Briefs already said "no sub-solvers unless asked" and "round cap 2-3 per item, then close as known"
# (OWNER_NOTES, README "Working lean"), but agents didn't always follow them and the weekly audit only
# caught it after the tokens were spent.
#
# 1. Judges and solvers (su-lead-max) don't spawn helpers, unless their own brief has a line "Spawning: allowed".
# 2. A lead (su-lead-high / su-lead-sonnet) spawning a su-lead-max agent must put "Item: <name>" in its prompt,
#    and gets at most 3 judge/solver rounds per item. The coordinator can send "Round cap raised for <name> to N".
# The main session is always allowed. Spawns this hook denied are not counted as rounds.
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


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": f"{MARK} {reason}"}}))


def main():
    d = json.load(sys.stdin)
    aid, atype = d.get("agent_id"), d.get("agent_type")
    if not aid:
        return
    main_path = d.get("transcript_path") or ""
    path = os.path.join(main_path[:-len(".jsonl")], "subagents", f"agent-{aid}.jsonl")
    if not os.path.exists(path):
        return
    inp = d.get("tool_input") or {}
    if atype == "su-lead-max":
        if not brief_allows_spawning(path):
            deny("Judges and solvers don't spawn helpers. Put what you would delegate in your report "
                 "(what to run, check or build, and why) and the lead will route it.")
        return
    if atype in ("su-lead-high", "su-lead-sonnet") and inp.get("subagent_type") == "su-lead-max":
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

"""Load and save the game's content JSON exactly as it is written (indent 1,
UTF-8, CRLF on this checkout), and shorthands for the world language."""
import json, os

C = r"C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a473fbc4762172b02/godot/data/content/"


def load(name):
    with open(C + name, encoding='utf8') as f:
        return json.load(f)


NODE_ORDER = ["id", "speaker", "text", "effects", "choices", "next"]
CHOICE_ORDER = ["text", "show", "when", "badge", "locked", "once", "effects", "goto", "action", "end"]


def _order(d, order):
    return {k: d[k] for k in order if k in d} | {k: v for k, v in d.items() if k not in order}


def tidy_dialogue(D):
    for cv in D.values():
        for nid, n in list(cv["nodes"].items()):
            n["id"] = nid
            if "choices" in n:
                n["choices"] = [_order(c, CHOICE_ORDER) for c in n["choices"]]
            cv["nodes"][nid] = _order(n, NODE_ORDER)
    return D


def save(name, data):
    if name == "dialogue.json":
        tidy_dialogue(data)
    with open(C + name, "w", encoding="utf8") as f:  # text mode: CRLF here, as checked out
        f.write(json.dumps(data, indent=1, ensure_ascii=False) + "\n")


# ------------------------------------------------------------ conditions --
def fact(k, **cmp):
    return {"fact": k, **cmp}


def eq(k, v):
    return {"fact": k, "eq": v}


def ne(k, v):
    return {"fact": k, "ne": v}


def has(k):
    return {"fact": k, "exists": True}


def nothas(k):
    return {"not": {"fact": k, "exists": True}}


def not_(c):
    return {"not": c}


def all_(*cs):
    return {"all": list(cs)}


def any_(*cs):
    return {"any": list(cs)}


def knows(k):
    return {"knows": k}


def hist(k):
    return {"history": k}


def nk(npc, ev):
    return {"npcKnows": {"npc": npc, "event": ev}}


def met(npc):
    return {"met": npc}


def bg(b):
    return {"bg": b}


def arch(a):
    return {"archetype": a}


def sex(s):
    return {"sex": s}


def item(i, qty=None):
    return {"hasItem": i, **({"qty": qty} if qty else {})}


def tag(t):
    return {"hasTag": t}


def trait(t):
    return {"trait": t}


def rel(npc, axis, **cmp):
    return {"rel": {"npc": npc, "axis": axis, **cmp}}


def flag(npc, key, v=True):
    return {"npcFlag": {"npc": npc, "key": key, "eq": v}}


def noflag(npc, key):
    return {"not": {"npcFlag": {"npc": npc, "key": key, "eq": True}}}


def quest(qid, entry=None, status=None):
    q = {"id": qid}
    if entry:
        q["entry"] = entry
    if status:
        q["status"] = status
    return {"quest": q}


def level(**cmp):
    return {"level": cmp}


def kills(**cmp):
    return {"kills": cmp}


def gold(**cmp):
    return {"gold": cmp}


def day(**cmp):
    return {"day": cmp}


def time(t):
    return {"time": t}


# ---------------------------------------------------------------- changes --
def setf(**kv):
    return {"set": {k.replace("__", "."): v for k, v in kv.items()}}


def setd(d):
    return {"set": d}


def setflag(npc, key, v=True):
    return {"npcFlag": {"npc": npc, "key": key, "value": v}}


def relc(npc, quiet=False, **axes):
    c = {"rel": {"npc": npc, **axes}}
    if quiet:
        c["quiet"] = True
    return c


def qe(qid, entry=None, status=None, outcome=None):
    q = {"id": qid}
    if status:
        q["status"] = status
    if entry:
        q["entry"] = entry
    if outcome:
        q["outcome"] = outcome
    return {"quest": q}


def history(id, text, tags, spread, sentiment=None, reactions=None, witnesses=None):
    h = {"id": id, "text": text, "tags": tags, "spread": spread}
    if sentiment:
        h["sentiment"] = sentiment
    if reactions:
        h["reactions"] = reactions
    c = {"history": h}
    if witnesses:
        c["witnesses"] = witnesses
    return c


def iff(cond, then, else_=None):
    c = {"if": cond, "then": then}
    if else_ is not None:
        c["else"] = else_
    return c


# ------------------------------------------------------------ dialogue --
def V(*pairs):
    """Variants: (cond, text) pairs, the last may be a bare string (the fallback)."""
    out = []
    for p in pairs:
        if isinstance(p, str):
            out.append({"text": p})
        else:
            out.append({"when": p[0], "text": p[1]})
    return out if len(out) > 1 or "when" in out[0] else out[0]["text"]


def node(text, choices=None, speaker=None, effects=None, next=None):
    n = {"text": text}
    if speaker:
        n["speaker"] = speaker
    if effects:
        n["effects"] = effects
    if choices is not None:
        n["choices"] = choices
    if next:
        n["next"] = next
    return n


def ch(text, goto=None, end=False, when=None, show=None, locked=None, badge=None, once=None, effects=None, action=None):
    c = {"text": text}
    if show is not None:
        c["show"] = show
    if when is not None:
        c["when"] = when
    if badge:
        c["badge"] = badge
    if locked:
        c["locked"] = locked
    if once:
        c["once"] = once
    if effects:
        c["effects"] = effects
    if goto:
        c["goto"] = goto
    if action:
        c["action"] = action
    if end:
        c["end"] = True
    return c

"""Helpers for editing the story's content JSON in place (round-trip safe: indent 1,
ensure_ascii False, CRLF, trailing CRLF)."""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8")
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a38d66ae66583ace1"
C = os.path.join(WT, "godot", "data", "content")


def dump(d):
    return (json.dumps(d, indent=1, ensure_ascii=False).replace("\n", "\r\n") + "\r\n").encode("utf-8")


def load(name):
    raw = open(os.path.join(C, name), "rb").read()
    data = json.loads(raw.decode("utf-8"))
    if dump(data) != raw:
        sys.exit(f"{name}: round trip differs; not safe to rewrite")
    return data


def save(name, data):
    open(os.path.join(C, name), "wb").write(dump(data))


def node(nid, text, speaker=None, choices=None, nxt=None, effects=None):
    """A dialogue node in the file's own key order (id, speaker, text, effects, choices/next)."""
    n = {"id": nid}
    if speaker:
        n["speaker"] = speaker
    n["text"] = text
    if effects:
        n["effects"] = effects
    if choices is not None:
        n["choices"] = choices
    if nxt:
        n["next"] = nxt
    return n


def ch(text, goto=None, end=False, **kw):
    c = {"text": text}
    for k in ("show", "when", "locked", "badge", "effects", "once", "action"):
        if k in kw:
            c[k] = kw.pop(k)
    if goto:
        c["goto"] = goto
    if end:
        c["end"] = True
    assert not kw, kw
    return c


def v(text, when=None):
    return {"when": when, "text": text} if when is not None else {"text": text}


def fact(k, eq=None, **kw):
    f = {"fact": k}
    if eq is not None:
        f["eq"] = eq
    f.update(kw)
    return f


def nott(c):
    return {"not": c}


def all_(*cs):
    return {"all": list(cs)}


def any_(*cs):
    return {"any": list(cs)}


def flag(npc, key, eq=True):
    return {"npcFlag": {"npc": npc, "key": key, "eq": eq}}


def setf(**kw):
    return {"set": {k.replace("__", "."): val for k, val in kw.items()}}


def put_nodes(conv, *nodes):
    for n in nodes:
        conv["nodes"][n["id"]] = n


def replace_text(n, old, new, count=1):
    """Replace inside a node's text (string or variants); asserts it was there."""
    t = n["text"]
    hits = 0
    if isinstance(t, str):
        assert old in t, (n["id"], old)
        n["text"] = t.replace(old, new)
        return
    for vv in t:
        if old in vv["text"]:
            vv["text"] = vv["text"].replace(old, new)
            hits += 1
    assert hits >= count, (n["id"], old, hits)


def conversation(npc, entry_node, nodes):
    return {"npc": npc, "entry": [{"node": entry_node}], "nodes": {n["id"]: n for n in nodes}}

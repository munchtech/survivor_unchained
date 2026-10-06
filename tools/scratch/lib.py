"""Helpers for patching Survivor Unchained's content JSON in its house style
(indent 1, UTF-8 unescaped, CRLF, key order as the files already use)."""
import json, os

ROOT = os.path.join(os.getcwd(), 'godot', 'data', 'content')


def load(f):
    return json.load(open(os.path.join(ROOT, f), encoding='utf-8'))


def save(f, d):
    with open(os.path.join(ROOT, f), 'w', encoding='utf-8', newline='\r\n') as h:
        h.write(json.dumps(d, indent=1, ensure_ascii=False) + '\n')


# ---------------------------------------------------------------- conditions

def Q(quest, entry):
    return {"quest": {"id": quest, "entry": entry}}


def QS(quest, status):
    return {"quest": {"id": quest, "status": status}}


def ANY(*c):
    return {"any": list(c)}


def ALL(*c):
    return {"all": list(c)}


def NOT(c):
    return {"not": c}


def F(k, **kw):
    d = {"fact": k}
    d.update(kw)
    return d


def KN(k):
    return {"knows": k}


def FLAG(npc, key, eq=True):
    return {"npcFlag": {"npc": npc, "key": key, "eq": eq}}


def MET(npc):
    return {"met": npc}


def HAS(item, qty=None):
    d = {"hasItem": item}
    if qty:
        d["qty"] = qty
    return d


def HIST(h):
    return {"history": h}


# ------------------------------------------------------------------ changes

def SET(d):
    return {"set": d}


def ENTRY(quest, entry, status=None):
    q = {"id": quest}
    if status:
        q["status"] = status
    q["entry"] = entry
    return {"quest": q}


def SETFLAG(npc, key, value=True):
    return {"npcFlag": {"npc": npc, "key": key, "value": value}}


def REL(npc, quiet=False, **axes):
    r = {"npc": npc}
    r.update(axes)
    d = {"rel": r}
    if quiet:
        d["quiet"] = True
    return d


def IF(cond, then, els=None):
    d = {"if": cond, "then": then}
    if els is not None:
        d["else"] = els
    return d


def HISTORY(hid, text, tags, spread, sentiment=None, reactions=None, witnesses=None):
    h = {"id": hid, "text": text, "tags": tags, "spread": spread}
    if sentiment:
        h["sentiment"] = sentiment
    if reactions:
        h["reactions"] = reactions
    d = {"history": h}
    if witnesses:
        d["witnesses"] = witnesses
    return d


def LATER(days, lid, effect):
    return {"later": {"days": days, "id": lid, "effect": effect}}


# ------------------------------------------------------------------ dialogue

def V(text, when=None):
    if when is None:
        return {"text": text}
    return {"when": when, "text": text}


def C(text, goto=None, end=False, show=None, when=None, locked=None, badge=None, effects=None, once=None, action=None):
    c = {"text": text}
    if show is not None:
        c["show"] = show
    if when is not None:
        c["when"] = when
    if locked is not None:
        c["locked"] = locked
    if badge is not None:
        c["badge"] = badge
    if effects is not None:
        c["effects"] = effects
    if once is not None:
        c["once"] = once
    if goto is not None:
        c["goto"] = goto
    if action is not None:
        c["action"] = action
    if end:
        c["end"] = True
    return c


def N(nid, text, choices=None, effects=None, next=None, speaker=None):
    n = {"id": nid}
    if speaker:
        n["speaker"] = speaker
    n["text"] = text
    if effects is not None:
        n["effects"] = effects
    if choices is not None:
        n["choices"] = choices
    if next is not None:
        n["next"] = next
    return n


class Talks:
    def __init__(self, d):
        self.d = d

    def node(self, cid, nid):
        return self.d[cid]["nodes"][nid]

    def add(self, cid, n):
        nodes = self.d[cid]["nodes"]
        assert n["id"] not in nodes, f"{cid}.{n['id']} exists"
        nodes[n["id"]] = n

    def text(self, cid, nid, text):
        self.node(cid, nid)["text"] = text

    def find(self, cid, nid, frag):
        for c in self.node(cid, nid).get("choices") or []:
            t = c["text"] if isinstance(c["text"], str) else c["text"][-1]["text"]
            if frag in t:
                return c
        raise KeyError(f"{cid}.{nid}: no choice with '{frag}'")

    def insert(self, cid, nids, choice, before=None, after=None):
        """Put a copy of the choice into each node, before (or after) the
        first choice whose text holds the fragment; else before the last."""
        for nid in nids:
            cs = self.node(cid, nid).setdefault("choices", [])
            i = None
            for k, c in enumerate(cs):
                t = c["text"] if isinstance(c["text"], str) else c["text"][-1]["text"]
                if before and before in t:
                    i = k
                    break
                if after and after in t:
                    i = k + 1
                    break
            if i is None:
                if before or after:
                    raise KeyError(f"{cid}.{nid}: no choice with '{before or after}'")
                i = len(cs) - 1 if cs else 0
            cs.insert(i, json.loads(json.dumps(choice)))

    def entry(self, cid, node, when, before=None):
        es = self.d[cid]["entry"]
        e = {"when": when, "node": node}
        i = next((k for k, x in enumerate(es) if x["node"] == before), len(es) - 1) if before else len(es) - 1
        es.insert(i, e)

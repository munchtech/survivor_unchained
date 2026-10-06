"""Print dialogue.json as a readable script: one conversation per file.

Conditions are summarised to a short tag so the words stay in front.
Choices that only open a shop or repeat a hub are kept short.
"""
import json, sys, os

ROOT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a8d7dfe2856df399e"
OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT, exist_ok=True)

d = json.load(open(os.path.join(ROOT, "godot/data/content/dialogue.json"), encoding="utf-8"))


def cond(c):
    if c is None:
        return ""
    if isinstance(c, dict):
        if "all" in c:
            return "&".join(cond(x) for x in c["all"])
        if "any" in c:
            return "(" + "|".join(cond(x) for x in c["any"]) + ")"
        if "not" in c:
            return "!" + cond(c["not"])
        parts = []
        for k, v in c.items():
            if k in ("eq", "gte", "lte", "exists", "qty"):
                continue
            if isinstance(v, dict):
                inner = ",".join(f"{a}={b}" for a, b in v.items())
                parts.append(f"{k}[{inner}]")
            else:
                extra = ""
                if "eq" in c:
                    extra = f"={c['eq']}"
                if "gte" in c:
                    extra = f">={c['gte']}"
                parts.append(f"{k}:{v}{extra}")
        return " ".join(parts)
    return str(c)


SKIP_ACTIONS = {"trade", "sellpelts", "craft"}


def texts(t):
    if isinstance(t, str):
        return [("", t)]
    out = []
    for v in t:
        out.append((cond(v.get("when")), v.get("text", "")))
    return out


def dump(name, conv, f):
    f.write(f"######## {name}  (npc {conv.get('npc')})\n")
    for e in conv.get("entry", []):
        f.write(f"  entry -> {e.get('node')}  [{cond(e.get('when'))}]\n")
    for nid, n in conv["nodes"].items():
        f.write(f"\n== {name}.{nid}\n")
        for c, t in texts(n.get("text", "")):
            tag = f"   <{c}>" if c else ""
            f.write(f"  > {t}{tag}\n")
        for ch in n.get("choices", []):
            if ch.get("action") in SKIP_ACTIONS:
                continue
            if ch.get("text") in ("Goodbye.",) and ch.get("end"):
                continue
            tgt = ch.get("goto") or ("END" if ch.get("end") else ch.get("action", ""))
            w = cond(ch.get("when"))
            s = cond(ch.get("show"))
            eff = ch.get("effects")
            effs = ""
            if eff:
                effs = " {" + "; ".join(json.dumps(x, ensure_ascii=False) for x in eff)[:200] + "}"
            f.write(f"     * {ch.get('text')} -> {tgt}" + (f" [when {w}]" if w else "") + (f" [show {s}]" if s else "") + effs + "\n")
        if n.get("effects"):
            f.write("     effects: " + "; ".join(json.dumps(x, ensure_ascii=False) for x in n["effects"])[:300] + "\n")


names = sys.argv[1:] or list(d.keys())
for name in names:
    with open(os.path.join(OUT, f"{name}.txt"), "w", encoding="utf-8") as f:
        dump(name, d[name], f)
print("ok", len(names))

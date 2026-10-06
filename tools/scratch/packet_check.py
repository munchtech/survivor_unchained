"""Check a regenerated packet against the story data: every subtitle is in the
current text of its line; the narrator plays no feelings; pauses and whispers
where agreed; no quotes left in the narrator's mouth. packet_check.py <voice>"""
import json, re, sys, glob
sys.stdout.reconfigure(encoding="utf-8")
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7622ae77d19e31dc"
voice = sys.argv[1]
text = open(rf"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\vo\{voice}.md", encoding="utf-8-sig").read()
d = json.load(open(W + r"\godot\data\content\dialogue.json", encoding="utf-8"))
npcs = json.load(open(W + r"\godot\data\content\npcs.json", encoding="utf-8"))
folk = json.load(open(W + r"\godot\data\content\folk.json", encoding="utf-8"))
code = ""
for f in glob.glob(W + r"\godot\logic\**\*.cs", recursive=True):
    code += open(f, encoding="utf-8").read()
code = code.replace('\\"', '"')


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def source(tid):
    p = tid.split(".")
    if p[0] == "dlg":
        n = d.get(p[1], {}).get("nodes", {}).get(p[2])
        if not n:
            return None
        t = n["text"]
        vs = t if isinstance(t, list) else [{"text": t}]
        i = int(p[3])
        return vs[i]["text"] if i < len(vs) else None
    if p[0] == "bark":
        nn = npcs["npcs"].get(p[1]) or npcs.get("outsiders", {}).get(p[1])
        if not nn:
            return None
        lst = {"day": nn.get("barks"), "night": nn.get("nightBarks"), "said": [s["text"] for s in nn.get("said") or []]}[p[2]]
        i = int(p[3])
        return lst[i] if lst and i < len(lst) else None
    if p[0] == "folk":
        i = int(p[1])
        return folk["lines"][i]["text"] if i < len(folk["lines"]) else None
    return code  # say./cbark.: somewhere in the code


FEEL = re.compile(r"\b(eerie|grim|dread|awe|wonder|warm|warmth|tender|relief|sombre|menace|unease|uneasy|pity|horror|tense|satisfaction|ominous|creeping|gentle|fond|sad|grief|joy|amused|wry|smile|half-smile)\b", re.I)
blocks = re.split(r"\n### ", text)
bad = 0
for b in blocks[1:]:
    m = re.match(r"(\d+)\. `([^`]+)`(.*)", b.split("\n", 1)[0])
    if not m:
        continue
    n, fn = int(m.group(1)), m.group(2)
    tid = re.sub(r"\.p\d+\.wav$|\.wav$", "", fn)
    sub = re.search(r"Subtitle: (.*)", b)
    paste = re.search(r"```\n(.*?)\n```", b, re.S)
    played = re.search(r"\*Played:\* (.*)", b)
    note = re.search(r"\*Note:\* (.*)", b)
    s = sub.group(1).strip() if sub else ""
    src = source(tid)
    if src is None:
        print(f"{n} {fn}: NO SOURCE"); bad += 1
    elif norm(s) not in norm(src):
        print(f"{n} {fn}: SUBTITLE NOT IN DATA\n   sub: {s}\n   data: {src[:300]}"); bad += 1
    p = paste.group(1) if paste else ""
    if voice == "narrator":
        for lab, fld in (("played", played), ("note", note)):
            if fld and FEEL.search(fld.group(1)) and n not in (10, 16):
                print(f"{n} {fn}: FEELING in {lab}: {fld.group(1)[:160]}")
        if "[whispers]" in p:
            print(f"{n} {fn}: WHISPER: {p[:90]}")
        if '"' in re.sub(r"\[[^\]]*\]", "", p):
            print(f"{n} {fn}: QUOTE in narrator paste: {p[:200]}")
print("checked", len(blocks) - 1, "bad", bad)

"""Read an ElevenLabs voice packet against the story data before signing it final.

    git show <voice-branch-commit>:docs/voice/elevenlabs/<voice>.md > /tmp/<voice>.md
    python tools/story/packet_check.py /tmp/<voice>.md [--lines] [--full]

It checks each take:
- its subtitle is in the current text of its line (dialogue.json, npcs.json
  barks and "said", folk.json, or the zone code for say./cbark. ids);
- for the narrator: no feeling words in Played or Note (he plays none), and
  no quotes left in his mouth (written words, such as Corran's book, are his);
- every [whispers].

With --lines it prints each take's paste text, and with --full its Played
and Note too: that is the read for wants, hides and stale notes, which no
script can do.
"""
import glob, json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
C = os.path.join(ROOT, "godot", "data", "content")
path = sys.argv[1]
lines, full = "--lines" in sys.argv or "--full" in sys.argv, "--full" in sys.argv
narrator = os.path.basename(path).startswith("narrator")

d = json.load(open(os.path.join(C, "dialogue.json"), encoding="utf-8"))
npcs = json.load(open(os.path.join(C, "npcs.json"), encoding="utf-8"))
folk = json.load(open(os.path.join(C, "folk.json"), encoding="utf-8"))
code = "".join(open(f, encoding="utf-8").read() for f in glob.glob(os.path.join(ROOT, "godot", "logic", "**", "*.cs"), recursive=True)).replace('\\"', '"')


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def source(tid):
    p = tid.split(".")
    if p[0] == "dlg":
        n = d.get(p[1], {}).get("nodes", {}).get(p[2])
        if not n:
            return None
        vs = n["text"] if isinstance(n["text"], list) else [{"text": n["text"]}]
        return vs[int(p[3])]["text"] if int(p[3]) < len(vs) else None
    if p[0] == "bark":
        nn = npcs["npcs"].get(p[1]) or npcs.get("outsiders", {}).get(p[1])
        if not nn:
            return None
        lst = {"day": nn.get("barks"), "night": nn.get("nightBarks"), "said": [s["text"] for s in nn.get("said") or []]}.get(p[2])
        return lst[int(p[3])] if lst and int(p[3]) < len(lst) else None
    if p[0] == "folk":
        return folk["lines"][int(p[1])]["text"] if int(p[1]) < len(folk["lines"]) else None
    return code


FEEL = re.compile(r"\b(eerie|grim|dread|awe|wonder|warm|warmth|tender|relief|sombre|menace|unease|uneasy|pity|horror|tense|ominous|creeping|gentle|fond|sad|grief|joy|amused|wry|smile)\b", re.I)
text = open(path, encoding="utf-8-sig").read()
bad = 0
blocks = re.split(r"\n### ", text)
for b in blocks[1:]:
    m = re.match(r"(\d+)\. `([^`]+)`(.*)", b.split("\n", 1)[0])
    if not m:
        continue
    n, fn = int(m.group(1)), m.group(2)
    tid = re.sub(r"\.p\d+\.wav$|\.wav$", "", fn)
    sub = (re.search(r"Subtitle: (.*)", b) or [None, ""])[1].strip()
    paste = (re.search(r"```\n(.*?)\n```", b, re.S) or [None, ""])[1]
    played = re.search(r"\*Played:\* (.*)", b)
    note = re.search(r"\*Note:\* (.*)", b)
    src = source(tid)
    if src is None:
        print(f"{n} {fn}: NO SOURCE"); bad += 1
    elif norm(sub) not in norm(src):
        print(f"{n} {fn}: SUBTITLE NOT IN DATA (a dropped {{name}} is fine)\n   sub:  {sub}\n   data: {src[:300]}"); bad += 1
    if "[whispers]" in paste:
        print(f"{n} {fn}: WHISPER")
    if narrator:
        for lab, fld in (("played", played), ("note", note)):
            if fld and FEEL.search(fld.group(1)):
                print(f"{n} {fn}: FEELING in {lab}: {fld.group(1)[:160]}")
        if '"' in re.sub(r"\[[^\]]*\]", "", paste):
            print(f"{n} {fn}: QUOTE in the narrator's mouth: {paste[:160]}")
    if lines:
        print(f"{n}. {fn}{m.group(3)}")
        if full and played:
            print("   played:", played.group(1))
        if full and note:
            print("   note:", note.group(1))
        print("   >", paste.replace("\n", " / "))
print("checked", len(blocks) - 1, "takes;", bad, "not matching the data")

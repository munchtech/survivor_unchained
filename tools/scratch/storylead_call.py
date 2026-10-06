"""The owner's question (should Vonnra narrate?): no; she is the voice that
calls the survivor up the road, once, at the waking (C01), unnamed. The words
come back from her mouth to open the fortune (C09): "No charge, this once."
Bible, section 2, "Who tells it"."""
import json

ROOT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7622ae77d19e31dc"
C = ROOT + r"\godot\data\content"


def load(n):
    return json.loads(open(f"{C}\\{n}", "rb").read().decode("utf-8"))


def save(n, d):
    open(f"{C}\\{n}", "wb").write((json.dumps(d, indent=1, ensure_ascii=False).replace("\n", "\r\n") + "\r\n").encode("utf-8"))


npcs = load("npcs.json")
assert "far_voice" not in npcs["speakers"]
# Unnamed on screen: the subtitle must not give her away.
npcs["speakers"]["far_voice"] = {"name": "A voice up the road", "title": "", "glyph": "moon"}
save("npcs.json", npcs)

d = load("dialogue.json")
c = d["cin_drowned_fire"]["nodes"]
assert c["prints"]["next"] == "frost"
c["prints"]["next"] = "lamp"
nodes = {}
for k, v in c.items():
    nodes[k] = v
    if k == "prints":
        nodes["lamp"] = {"id": "lamp", "speaker": "narrator",
                         "text": "Far up the road one lamp burns high in the dark, and a voice comes down to you over the frost, close as if she stood at your shoulder.",
                         "next": "call"}
        nodes["call"] = {"id": "call", "speaker": "far_voice",
                         "text": "Come up, traveller. ...No charge, this once.",
                         "next": "frost"}
d["cin_drowned_fire"]["nodes"] = nodes
save("dialogue.json", d)

# The captions that stand in for C01 until the cinematic plays (Prologue.cs, CRLF kept).
P = ROOT + r"\godot\logic\Play\Zones\Prologue.cs"
src = open(P, "rb").read().decode("utf-8")
old = '        G.After(8.4, () => G.Say("Past the firelight, the frost is breaking.", null, 3.5));'
assert src.count(old) == 1
new = ('        G.After(8.4, () => G.Say("Far up the road one lamp burns high in the dark, and a voice comes down to you over the frost, close as if she stood at your shoulder.", null, 5.5));\r\n'
       '        // Vonnra, unnamed: the fortune opens on the same words (docs/STORY_BIBLE.md, "Who tells it").\r\n'
       '        G.After(14.1, () => G.Say("Come up, traveller. ...No charge, this once.", "A voice up the road", 4));\r\n'
       '        G.After(18.3, () => G.Say("Past the firelight, the frost is breaking.", null, 3.5));')
src = src.replace(old, new)
open(P, "wb").write(src.encode("utf-8"))

T = ROOT + r"\godot\tests\CinematicTests.cs"
t = open(T, "rb").read().decode("utf-8")
old = 'Assert.Equal(["cin_drowned_fire.bedroll", "cin_drowned_fire.prints", "cin_drowned_fire.frost"], Lines("cin_drowned_fire", Q()).Select(l => l.Id));'
assert old in t
t = t.replace(old, 'Assert.Equal(["cin_drowned_fire.bedroll", "cin_drowned_fire.prints", "cin_drowned_fire.lamp", "cin_drowned_fire.call", "cin_drowned_fire.frost"], Lines("cin_drowned_fire", Q()).Select(l => l.Id));')
open(T, "wb").write(t.encode("utf-8"))
print("ok")

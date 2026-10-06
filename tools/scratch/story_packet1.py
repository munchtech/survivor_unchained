"""Lines the narrator and Rook packets showed up, made final before recording.
- A delivery direction inside a speaker's line is lowercase, so the voice tools
  give it to the speaker as a tag and never to the narrator; narration in
  parentheses is a capitalised sentence.
- Narration that was hard to say, or that winked, is rewritten."""
import json

ROOT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7622ae77d19e31dc"
C = ROOT + r"\godot\data\content"


def load(n):
    return json.loads(open(f"{C}\\{n}", "rb").read().decode("utf-8"))


def save(n, d):
    open(f"{C}\\{n}", "wb").write((json.dumps(d, indent=1, ensure_ascii=False).replace("\n", "\r\n") + "\r\n").encode("utf-8"))


def swap(node, old, new):
    t = node["text"]
    if isinstance(t, list):
        hits = [v for v in t if old in v["text"]]
        assert hits, old
        for v in hits:
            v["text"] = v["text"].replace(old, new)
    else:
        assert old in t, old
        node["text"] = t.replace(old, new)


d = load("dialogue.json")
N = lambda c, n: d[c]["nodes"][n]
swap(N("redcowl", "ashford"), "Don't. (Quiet.) You get", "Don't. (quietly) You get")
swap(N("keegan", "supper_letters"), "(Very precisely.)", "(very precisely)")
swap(N("rav", "came_back_sit"), "(A breath out through his nose.)", "(a breath out through his nose)")
swap(N("brannoc", "nell_ditch"), "(A long breath, through the nose.)", "(a long breath, through the nose)")
swap(N("maeca", "told_true"), "(A long breath.)", "(a long breath)")
swap(N("maeca", "blind3_m_no"), "(Not unkind.)", "(not unkind)")
swap(N("redcowl", "trick"), "(a whistle, from the ridge; the whole camp stops)", "(A whistle from the ridge. The whole camp stops.)")
swap(N("rav", "back_room"), "a shelf of jars (one of them moving), and", "a shelf of jars, one of them moving, and")
swap(N("maeca", "blind2_feet"),
     "and doesn't say anything for a long time. (Into the dark, very low:) \"Your hands are colder than my feet.\" (A pause.) \"Hold them anyway.",
     "and doesn't say anything for a long time. Then, into the dark, very low: \"Your hands are colder than my feet.\" She doesn't take them back. \"Hold them anyway.")
# The narrator says what happens; the ellipsis that dropped a verb is spelled out.
swap(N("tam", "fetch"),
     "You walk the boy as far as the fence where his Pa lost the goat, and his Pa out of the trees on the other side. He calls you several things on the way, and one of them is a fool. He comes.",
     "You walk the boy as far as the fence where his Pa lost the goat, and go on into the trees for his Pa. He calls you several things on the way back, and one of them is a fool. But he comes.")
save("dialogue.json", d)

q = load("quests.json")
s = q["below"]["entries"]["sinkhole"]
assert s.endswith("bigger than a house. Dead. Probably."), s
q["below"]["entries"]["sinkhole"] = s.replace("bigger than a house. Dead. Probably.", "bigger than a house. It does not move.")
save("quests.json", q)

# The zone captions (Verge.cs), CRLF kept.
P = ROOT + r"\godot\logic\Play\Zones\Verge.cs"
src = open(P, "rb").read().decode("utf-8")
for old, new in [
    # The narrator, who never lies, cannot say: no wink (LINE_NOTES 3.1).
    ("At the bottom of the pit lies something pale and segmented, bigger than a house, and — probably — dead.",
     "At the bottom of the pit lies something pale and segmented, bigger than a house. It does not move. You watch it long enough to be sure, and you are not."),
    # Not Maeca's rule quoted back (a mechanic); what happens.
    ("They smell the blood on you before they see you. Maeca said none since you last slept.",
     "They smell the blood on you before they see you: one of theirs, since you last slept."),
]:
    assert src.count(old) == 1, old
    src = src.replace(old, new)
open(P, "wb").write(src.encode("utf-8"))
print("ok")

"""The story editor's round five on WRITING_PASS section 17, taken (with Tam's
knocking matched to his own canon: Pa says moles)."""
import json

ROOT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7622ae77d19e31dc\godot\data\content"


def load(n):
    return json.loads(open(f"{ROOT}\\{n}", "rb").read().decode("utf-8"))


def save(n, d):
    open(f"{ROOT}\\{n}", "wb").write((json.dumps(d, indent=1, ensure_ascii=False).replace("\n", "\r\n") + "\r\n").encode("utf-8"))


def swap(node, old, new, every=False):
    t = node["text"]
    if isinstance(t, list):
        hits = [v for v in t if old in v["text"]]
        assert hits and (every or len(hits) == 1), (old, len(hits))
        for v in hits:
            v["text"] = v["text"].replace(old, new)
    else:
        assert old in t, old
        node["text"] = t.replace(old, new)


d = load("dialogue.json")
chid = d["chid"]["nodes"]
# The carter: "Someone always does" is Vonnra's (C09's turn); "before you ask" is Maeca's.
swap(chid["woke"], "Up again. Up's good. (He has the kettle on already.) The carter brought you in, before you ask.",
     "Up again. (He has the kettle on already.) The carter sends his regards.")
swap(chid["woke"], "(He isn't looking at you.) Well. Someone did. Someone always does. You'll be sore",
     "(He isn't looking at you.) ...Well. Someone did. You'll be sore")
# His need for company is shown, not asked for (and Keegan owns "Not there... Here.").
swap(chid["cb_nell"], "...Sit down a minute. Not on the step. Here. By me.",
     "...Sit down a minute. (He moves up the bench, though there's nobody else on it.)", every=True)
# Wenna's own voice: symptoms, and the dash where she stops.
swap(d["wenna"]["nodes"]["fever"], "Half the valley coughing green and the other half burying them.",
     "Coughing green, then the sweats, then the— well.")
# "Comes back" is her secret's word; she does not spend it on a stranger.
swap(d["wayfinder"]["nodes"]["first"], "You've the look of someone who comes back. Good. The other sort only ever buy the one map.",
     "You've the look of someone who'll want a second map. Good. Most only ever buy the one.")
# The pair the player should put together is hidden in a list.
swap(d["rook"]["nodes"]["valley"], "Don't ask Maeca. And don't ask me twice.",
     "Don't ask Maeca. Don't ask a Kerchief, if you meet one. And don't ask me twice.")
# After C03 Grimtunnel never finishes "surface-meat" at her: he has smelled downstairs on her.
pump = d["cin_dig_boils_over"]["nodes"]["pump"]
swap(pump, "Surface-meat! You broke my PUMP.", "Surface-m— ...You broke my PUMP.")
swap(pump, "Surface-meat! Killing my lads, are we?", "Surface-m— ...Killing my lads, are we?")
save("dialogue.json", d)

folk = load("folk.json")
L = folk["lines"]
cut = [x for x in L if x["text"] == "Lamps are lit. Stay where they reach, or it's the Morrow for you."]
assert len(cut) == 1
L.remove(cut[0])
carts = [x for x in L if x["text"].startswith("No carts on the Old Road since the wolves.")]
assert len(carts) == 1
carts[0]["text"] = "No carter's been up the Old Road in a month. So who keeps bringing that one in?"
save("folk.json", folk)

npcs = load("npcs.json")
N = npcs["npcs"]


def said(npc, old, new=None, **kw):
    hits = [s for s in N[npc]["said"] if s["text"] == old]
    assert len(hits) == 1, (npc, old)
    if new:
        hits[0]["text"] = new
    for k, v in kw.items():
        if v is None:
            hits[0].pop(k, None)
        else:
            hits[0][k] = v
    return hits[0]


# Repetition for weight is Chid's and Keegan's; nobody else's.
said("holloway", "One caravan home. One. I'll take it.", "One caravan home. I'll take it.")
said("maeca", "Nothing calls in the Hollow now. Nothing.", "Nothing calls in the Hollow now.", night=True)
said("wenna", "Water's sweet. Sweet! I'd forgotten.", "Water's sweet again. I'd forgotten it could be.")
# Twelve irons, and a girl of twelve he made: said once, the first time she passes.
b = said("brannoc", "Twelve, I made. Twelve.", "Twelve, I made.", once=True)
said("keegan", "Chapter four. Chapter four. ...Good morning.", "Chapter four. Chapter four. ...Good day.")
# Rav grieves sideways, and never in his own bar on a loop.
said("rav", "Oh, Mam.", "Man owed me a leg, pal. Bad debt, now.")
# Tam's knocking, after he has told it (tam.tock) and the ground has moved: Pa says moles.
said("tam", "Ground knocks under our barn. Pa says pipes. We've got no pipes.",
     "Still knocking under our floor. Pa's stopped saying it's moles.",
     when={"all": [{"fact": "tam.tock", "eq": True}, {"fact": "tremor.felt", "eq": True}]})
h = N["harlan"]["barks"]
i = h.index("Salt and iron, friend. Cloth, when I can get it.")
h[i] = "Salt and iron, friend. Good honest salt."
save("npcs.json", npcs)

it = load("items.json")
I = it["items"]
I["blasting_ember"]["description"] = I["blasting_ember"]["description"].replace(
    " It is warm, and warmer when you are afraid.", " It is warm, like a stone a hand has only just let go of.")
assert "only just let go" in I["blasting_ember"]["description"]
w = I["wardens_lampiron"]
assert " It was made to hold ember, not oil." in w["lore"]
w["lore"] = w["lore"].replace(" It was made to hold ember, not oil.", " There is no well in it for oil, and no wick.")
save("items.json", it)
print("ok")

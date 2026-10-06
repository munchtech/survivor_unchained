"""Act 1 rewrite, part C: the mother (twist B's false belief, twist A's word), the fortune
("You did this", the readable ledger), the town's thanks, and the line fixes (Tam's Pa, the
calling remarks written from each speaker's trade, "Don't tell" left with Sella)."""
from lib_s7 import *

d = load("dialogue.json")

# ----------------------------------------------------------- Rook's kind lie --
Ro = d["rook"]
rn = Ro["nodes"]
ask = ch("I've come home. My mother sent for me.", "mother", once="mother")
for key in ("first", "hub", "wanted"):
    cs = rn[key]["choices"]
    i = next(i for i, c in enumerate(cs) if c.get("goto") == "rumours")
    cs.insert(i + 1, dict(ask))
put_nodes(Ro,
    node("mother", (
        "(She stops wiping the cup. She looks at your face a beat too long, and then out of the window at the "
        "tower, and then at the cup.) ...Sit down, pet."), nxt="mother2"),
    node("mother2", (
        "She went in her sleep, pet. A week since. (She sets the cup down.) Chid brought her down and saw to "
        "her. I sat with her, after."), choices=[
            ch("Where is she?", "mother_where"), ch("I was a day short.", "mother_short"), ch("(Say nothing.)", "mother_quiet")]),
    node("mother_where", "Quiet Garden, behind the shrine. There's a marker. No name on it yet; you can tell Chid what to cut.",
         nxt="mother_room"),
    node("mother_short", "(Something goes across her face, and is put away.) You came, pet. That's the part that counts.",
         nxt="mother_room"),
    node("mother_quiet", "(She lets it be quiet. She's good at that.)", nxt="mother_room"),
    node("mother_room", (
        "(She turns a ring on the nail behind the bar, among the keys, without looking at it.) Back room's "
        "yours, if you want it. It's been free a week."),
        effects=[setf(mother__told=True), {"quest": {"id": "home", "status": "active", "entry": "rook"}}],
        choices=[ch("Thank you, Rook.", "hub"), ch("(Go and find the garden.)", end=True)]),
)
replace_text(rn["hub"], "I kept a bowl back. Don't tell the others.", "I kept a bowl back. The others can whistle.")

# --------------------------------------------------------- the word, written --
cn = d["chid"]["nodes"]
names = cn["names"]
names.pop("next", None)
names["choices"] = [ch("(Write down what she called you, at dusk.)", "names_write"), ch("(Sit.)", "hub")]
put_nodes(d["chid"], node("names_write", "(He watches you write it, and doesn't look at what.) Good. Keep it somewhere dry.",
                          effects=[setf(mother__word=True), {"quest": {"id": "home", "status": "active", "entry": "word"}}], nxt="hub"))

# ------------------------------------------------------------ the first dawn --
replace_text(d["cin_first_light"]["nodes"]["face"], "and find it is not quite where you left it.",
             "and find it is not quite where you left it. Her voice is still there. \"Lamp's lit, Spark. Stay where it reaches.\"")

# ------------------------------------------------------- the nod, as a choice --
# C03 stops on "Is it morning?" for her answer (staging: the cinematics lead). Either way he lets go.
d["warden_answer"] = conversation("warden_answer", "wait", [
    node("wait", "He waits for an answer, the lamp held up to your face.", speaker="narrator", choices=[
        ch("(Nod.)", end=True, effects=[setf(warden__answer="nodded")]),
        ch("(Say nothing.)", end=True, effects=[setf(warden__answer="silent")])]),
])

# ------------------------------------------------------------- the fortune --
V = d["vonnra"]
vn = V["nodes"]
vn["f_caravan"]["next"] = "f_past"
vn["f_past"]["next"] = "f_ford"
for k in ("f_ember", "f_pell", "f_self"):
    del vn[k]
held = ("He would have held that lamp out of the water until the river ran dry, traveller. Two hundred years he "
        "held it, and he would have held it two hundred more, and got up every dusk to hold it again.")
put_nodes(V,
    node("f_ford", [
        v(f"And the ford. (She turns the cup over on the table.) {held} You did not even tell him it was morning. He let go anyway.",
          fact("warden.answer", "silent")),
        v(f"And the ford. (She turns the cup over on the table.) {held} You told him it was morning."),
    ], nxt="f_did"),
    node("f_did", (
        "When the lamp went into the water, his heart came up out of it, and a little lamp-person was waiting to "
        "carry it away down a hole. The ground has turned over every night since. The Dig digs faster. The "
        "Penhale boy's floor knocks. (She lays her hand flat on the cup.) You stopped the drowning, traveller. "
        "You also did this."), nxt="f_below"),
)
fb = vn["f_below"]
fb["text"] = (
    "And the door in the hillside... (The roof shivers under the table, and the glass of her lamp rings in its "
    "frame. The flame lies over toward the hill. Down in the town every lamp dips at once, and comes back; the "
    "braziers on the wall do not. She looks east, into the dark, and does not finish.)")
vn["f_accuse"]["text"] = ((
    "I did not kill him. (For the first time she looks at your face and not at your hand. It goes on long "
    "enough that the lamp gutters.) ...Sit down, {name}. I have not finished reading."))
ledger = (" (The ledger lies open under her hand at its last page, and from where you sit you can read it. Twenty-six "
          "lines, every one struck through. The twenty-fifth: Nell, the smith's girl. With Wat. The twenty-sixth: "
          "Rook's lodger. And under them a twenty-seventh, not struck: From the ford. Got up.)")
for x in vn["f_chart"]["text"]:
    x["text"] += ledger

# ------------------------------------------------------------- line fixes --
replace_text(d["tam"]["nodes"]["tock"], "so I did, but it kept knocking.",
             "so I did, but it kept knocking. Pa says the moles can knock on somebody else's bloody floor. I'm not to say bloody.")

def calling(conv, arch, text):
    for x in d[conv]["nodes"]["say_calling"]["text"]:
        if x.get("when") == ({"archetype": arch} if arch else None) or (arch and x.get("when") is None and arch == "stalker"):
            x["text"] = text

calling("chid", "stalker", "You put your feet down like the floor's asleep and you don't want to wake it. The Order had a word for walking like that. I've forgotten it. It was a nice word.")
calling("vonnra", "stalker", "You paid no toll the first time you passed my tower, traveller. Nobody saw you pass. I have added it to your account.")
calling("keegan", "stalker", "The handbook says to challenge anyone who approaches unseen. (She checks.) It does not say what to do if one forgets. ...Halt. Belatedly.")
calling("pell", "stalker", "You'd make an excellent debt collector. Nobody hears you coming, and everybody pays. Do think about it.")
calling("rav", "stalker", "You sit with your back to the wall and your weight on your toes. I've stitched men who sat like that. Mostly in the back.")
calling("wenna", "arcanist", "Your hands smell of hot iron, child, and you've not been near a forge. I don't want to know. Comfrey, twice a day, and keep them off my drying racks.")
replace_text(d["harlan"]["nodes"]["jory"], "Cost! Don't tell anyone.", "Cost! And I'll swear blind I never said it.")
replace_text(d["wayfinder"]["nodes"]["say_calling"], "Don't tell the reavers; they'll only stand in it.", "The reavers never ask; they'd only stand in it.", count=2)

save("dialogue.json", d)

n = load("npcs.json")
for s in n["npcs"]["chid"]["said"]:
    if s["text"] == "Two candles in for her. One's for Brannoc; don't tell him.":
        s["text"] = "Two candles in for her. One's for Brannoc. He'd only blow it out."
save("npcs.json", n)

# -------------------------------------------------------- the quest: Home --
q = load("quests.json")
q["home"] = {
    "id": "home", "name": "Home", "mystery": True,
    "summary": "A letter found you on the road and brought you home to Thornhollow by the Low Ford. The river has had the ink.",
    "entries": {
        "rook": "Mother Rook says your mother went in her sleep, a week before you came up the road. Chid buried her in the Quiet Garden, behind the shrine.",
        "grave": "A plain wooden marker in the Quiet Garden, a few stones along from the old captain's. No name on it yet. The earth on it is dark, and has not settled.",
        "word": "In your own hand, because Chid asked you to write the names down: \"Spark. What she called me, at dusk.\"",
    },
}
save("quests.json", q)

# ------------------------------------------- the dawns, and the town's thanks --
r = load("rules.json")
R = r["rules"]
dawn = [
    {"id": "dawn.voice", "once": True, "when": {"day": {"gte": 3}}, "effect": [],
     "report": "Her voice is going the way her face went. You still have the word."},
    {"id": "dawn.word", "once": True, "when": {"day": {"gte": 6}}, "effect": [],
     "report": "This morning it takes you a moment to find her word. It is there."},
]
R[0:0] = dawn
i_ago = next(i for i, x in enumerate(R) if x["id"] == "arena.ago")
R.insert(i_ago, {"id": "ford.thanks", "once": True, "when": all_({"day": {"gte": 2}}, fact("prologue.done", True)), "effect": [],
                 "report": ("The first carter in a month went south over the Low Ford yesterday, and came back up the road at dusk "
                            "with a full load, and stood up on his box at the gate and told the whole street who to thank for it. "
                            "Rook stood him a drink on your slate.")})
save("rules.json", r)
print("ok")

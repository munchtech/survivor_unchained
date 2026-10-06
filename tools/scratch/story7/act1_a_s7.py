"""Act 1 rewrite, part A: Holloway and Maeca (the owner's choices on TREATMENT.md, notes 01).
- every "Barefoot" out; Maeca's new signature and her three words about Ashford;
- Holloway's thanks, the cat, the roll (no boots), the sober report, drunk syntax at night;
- the trunk scenes: the gate at dawn, "She's in my count.", the knocking (the confession, mid
  Act 1), "...Did he.", her cup at the gate; the decoy; the scene slots the host plays."""
from lib_s7 import *

d = load("dialogue.json")

# ------------------------------------------------------------------ Holloway --
H = d["holloway"]
hn = H["nodes"]

hn["first"]["text"][1]["text"] = (
    "You're the one put the Ford-Warden down. (He looks at you a moment longer than he means to.) "
    "The Watch kept that crossing, once. Then we couldn't. ...Thank you. Holloway. Captain of what's "
    "left of the Watch: eleven of us, and the cat. I count the cat.")

# The hub: at night he is on the ground in the gateway with his cup (Waystation.cs puts him there).
hub = hn["hub"]["text"]
letter = next(x for x in hub if "silver seal" in x["text"])
hub.remove(letter)
night_variants = [
    v("(A letter lies open on his knee under the gate-lamp, a silver seal broken on it. He turns it "
      "over when you come, and puts his cup on it.) What.",
      all_({"time": "night"}, {"day": {"gte": 3}}, nott(fact("holloway.letter_seen", True)))),
    v("(On the ground in the gateway, his back to the post, a cup in his fist.) Gate open. Count short. "
      "Cup empty. (He finds you.) You. What.",
      all_({"time": "night"}, fact("holloway.confessed", True))),
    v("(On the ground in the gateway, his back to the post, a cup in his fist, counting under his "
      "breath.) ...Forty-four. Forty— (He loses it, and starts again at one.) What.",
      {"time": "night"}),
]
hn["hub"]["text"] = night_variants + hub
replace_text(hn["hub"], "I was wrong about them. Don't tell anyone I said so.", "I was wrong about them. That's not for the board.")

hc = hn["hub"]["choices"]
i_letter = next(i for i, c in enumerate(hc) if c.get("goto") == "letter")
hc.insert(i_letter, ch("Who are you counting?", "roll", show={"time": "night"}))
hc.insert(i_letter + 1, ch("Rook says not to ask you about Ashford.", "ashford",
                           show=flag("rook", "once:valley"), once="ashford"))

# Maeca, by his account: he pays her; she buys his drink with it; she walks him home.
hn["maeca"] = node("maeca", (
    "Maeca's right more often than I'd like. She tracks for the Watch: men, not wolves. Watch won't pay "
    "her, so I do. She takes it every week, and buys my drink with it. ...Then she walks me home."),
    choices=[ch("Something else.", "hub")])
# The sober report: his lie, the one Maeca's three words keep.
hn["ashford"] = node("ashford", (
    "Then don't. (He doesn't look up.) ...Garrison town, up the valley. The ground went one night, and "
    "the lower town with it. I held the upper town. Watch made me captain for it. (He picks up the "
    "cup.) That's the report."),
    choices=[ch("Something else.", "hub"), ch("That's all.", end=True)])
put_nodes(H,
    node("roll", (
        "(He isn't looking at you. He's looking down the dark road, and his lips are moving.) ...Abbot. "
        "Two bairns. Ancell. His mam. Bede. Nobody. Carrow. A wife, and one coming. (He finds you.) "
        "Garrison. The roll. I say it at night. Keeps them in order."),
        choices=[ch("(Listen.)", "roll2"), ch("Something else.", "hub"), ch("Goodnight, Captain.", end=True)]),
    node("roll2", (
        "Dunning. Two bairns. Ede. Her da. Fenn. Nobody. Gale. ...Gale. (He stops on it, and drinks, "
        "and starts again at Abbot.)"),
        choices=[ch("Goodnight, Captain.", end=True)]),
)

replace_text(hn["post2"], "So somebody had oil. And a reason.", "So somebody had ember, and irons to burn it in. And a reason.")
replace_text(hn["t_holloway"], "...Don't tell the men about the dog.", "...The men aren't to know about the dog.")
for x in hn["say_calling"]["text"]:
    if x.get("when") == {"archetype": "arcanist"}:
        x["text"] = "Burns, does it? What's it run on? (He looks at your hands.) Everything runs on something. I'll want it written down."

# ------------------------------------------------------------------- Maeca --
M = d["maeca"]
mn = M["nodes"]
mf = mn["first"]["text"]
mf[0]["text"] = ("You walk like someone who's followed a thing to its den. Hunter? Then you've seen it too, out "
                 "there. They're not hunting. They're running. Maeca. I track for the Watch, before you ask. Not wolves.")
mf[1]["text"] = "That cloak's made of wolves. I can smell it from here, and so can they. Maeca. What do you want?"
mf[2]["text"] = ("Another blade for Holloway's bounty? The Pack aren't the problem. They're what the problem looks "
                 "like from the road. Maeca. I track for the Watch, before you ask. Not wolves.")
heard_ashford = any_(flag("rook", "once:valley"), fact("holloway.confessed", True))
for key in ("first", "hub"):
    cs = mn[key]["choices"]
    i = next(i for i, c in enumerate(cs) if c.get("goto") == "barefoot")
    cs[i:i + 1] = [ch("You track for the Watch?", "watch", once="watch"),
                   ch("You were at Ashford.", "ashford", show=heard_ashford, once="ashford")]
del mn["barefoot"], mn["signed"]
put_nodes(M,
    node("watch", (
        "Men. Deserters, mostly, and the ones the road loses. The Watch won't pay for it, so Holloway does, "
        "out of his own pocket. (She drinks.) I take it. Every week. ...He'd pay me double, if I let him. "
        "I don't let him."),
        choices=[ch("Something else.", "hub"), ch("Goodbye.", end=True)]),
    node("ashford", "(She doesn't look up from her cup.) The cave mouths.",
         choices=[ch("Something else.", "hub"), ch("Goodbye.", end=True)]),
)
replace_text(mn["where"], "Nights, I'm here, drinking Rav's piss.", "Nights, I'm here, drinking Rav's piss, and then I walk the captain home.")
for x in mn["say_calling"]["text"]:
    if "Pity about the boots." in x["text"]:
        x["text"] = ("You walk like you've done this. Heel last, weight back. ...Who taught you? Not the Watch. "
                     "The Watch walks like a dropped tray.")
replace_text(mn["blind_walk"], "She walks barefoot on ground that would cut you through your boots, and doesn't make a sound.",
             "She doesn't make a sound.")
replace_text(mn["blind_fire"], "She feeds it one stick at a time.",
             "She sits, and pulls her boots off first thing, and sets her bare feet flat on the cold ground, "
             "as if she were listening through them. She feeds the fire one stick at a time.")
replace_text(mn["blind_morning"], (
    "The Pack found me, after Ashford. Three days in a cave mouth with the garrison dead round me, and the "
    "old grey one came and lay down across the way in."), (
    "The Pack found me, after Ashford. Three days, and then a cave mouth, and a lad I'd been fond of dying "
    "in it. The old grey one came and lay down across the way in."))

# Redcowl's "Ashford's levy" gate: she told you Ashford's name, not her feet.
for c in d["redcowl"]["nodes"]["hub"]["choices"]:
    s = c.get("show")
    if s and "once:barefoot" in str(s):
        s["all"][1]["any"][0]["npcFlag"]["key"] = "once:ashford"
replace_text(d["redcowl"]["nodes"]["who"], "the Watch counts its boots and goes home", "the Watch writes it down and goes home")
replace_text(d["redcowl"]["nodes"]["first"], "The last spark-thrower in here set fire to my tent.",
             "I've bairns asleep in this camp, and they've had enough fire for one life.")

# Sella: "Barefoot" out.
replace_text(d["sella"]["nodes"]["say_maeca"], "Maeca Barefoot came in", "Maeca came in")

# Pell: no boots; the lid, barred from the top. He knows who. (The decoy.)
d["pell"]["nodes"]["t_pell"]["text"] = (
    "My sister kept the books in Ashford, in the lower town. I came up to collect them, after. There wasn't "
    "a lower town to collect them from. There was a lid on the main shaft, barred from the top. (He "
    "straightens a pen that was straight.) Somebody barred it. I know who. ...So I count. Somebody ought "
    "to know what things cost.")
# Harlan: the exposure is Act 2's.
d["harlan"]["nodes"]["knew"]["text"] = "Jory? Jory knows salt from sugar on a good day. He didn't know. ...He didn't know. (He goes back to counting the jars.)"

# ------------------------------------------------------------- the scenes --
# Played by the host at a morning or a dusk in the Waystation (Journey.TakeScene).
d["scene_gate_dawn"] = conversation("scene_gate_dawn", "gate", [
    node("gate", (
        "The gate has stood open all night. Captain Holloway is asleep on the ground in the gateway, his "
        "back to the post, his lamp burned out and a bottle by his boot. Maeca sits on the step beside him "
        "with her crossbow across her knees. She is awake."), speaker="narrator", nxt="maeca"),
    node("maeca", "(a nod at him) Waits up for you. (a beat) Somebody waits up for him.", speaker="maeca", nxt="wake"),
    node("wake", "(awake all at once, the way soldiers wake, and finding you) ...One in. (He looks past you at the empty road.) Count's right.",
         speaker="holloway", choices=[
             ch("You waited all night?", "all"), ch("Thank you, Captain.", "thanks"), ch("(Say nothing.)", "bar")]),
    node("all", "Gate was open. Somebody had to stand in it. (Maeca looks at the step he was asleep on, and then at him, and says nothing at all, very loudly.)",
         speaker="holloway", nxt="bar"),
    node("thanks", "Don't. That's a drink you owe me. The cheap stuff; I'm not proud.", speaker="holloway", nxt="bar"),
    node("bar", "He gets up, and puts his shoulder to the gate, and bars it. Maeca picks up his bottle, looks at what's left in it, and pours it out on the step.",
         speaker="narrator", nxt="last"),
    node("last", "That's your last.", speaker="maeca", choices=[ch("(Go.)", end=True)]),
])

d["scene_in_my_count"] = conversation("scene_in_my_count", "crowd", [
    node("crowd", (
        "There are folk at the gate end of the square when you come down, and the talk stops when they see "
        "you. Somebody says it out loud: every night you go out into the dark, and every morning you come "
        "back out of it, and nothing out there ever touches you. Rook has a word for that. They are "
        "between you and the street, and they are not moving."), speaker="narrator", nxt="captain"),
    node("captain", (
        "(He comes down the street at a walk, not hurrying, and he has been drinking, and he stops in the "
        "gateway between you and them.) She's in my count."), speaker="holloway", nxt="men"),
    node("men", "Nobody moves. Two of his own men are at the back of the crowd, and they stay there.", speaker="narrator", nxt="through"),
    node("through", (
        "Anybody wants her out of it comes through me. (He sways, and plants his feet.) ...And I'm drunk, "
        "so it'll take you all morning."), speaker="holloway", nxt="gone"),
    node("gone", (
        "It takes a while. He stands there until the last of them has gone home, and then he sits down "
        "where he stood."), speaker="narrator", choices=[
            ch("Captain—", "dont"), ch("(Sit down with him.)", "sit")]),
    node("dont", "Don't. Go and get some sleep. Somebody in this town should.", speaker="holloway", choices=[ch("(Go.)", end=True)]),
    node("sit", "You sit. After a while he passes you the cup. There's nothing in it. Neither of you says so.",
         speaker="narrator", choices=[ch("(Stay a while.)", end=True)]),
])

confessed = [setf(holloway__confessed=True), {"rel": {"npc": "holloway", "trust": 10}, "quiet": True}]
d["scene_knocking"] = conversation("scene_knocking", "ground", [
    node("ground", (
        "The ground turns over under the square, and every lamp on the wall dips and comes back. At the gate "
        "Holloway hasn't moved. He's sitting against the post with his cup, and he's listening to something."),
        speaker="narrator", nxt="hear"),
    node("hear", "Hear that.", speaker="holloway", choices=[ch("Hear what?", "knock"), ch("(Listen.)", "knock")]),
    node("knock", "Knocking. (He listens.) From under. (He drinks.) No. Course not.", speaker="holloway", choices=[
        ch("Captain. What happened at Ashford?", "tell"), ch("Nothing's knocking. Go home.", "home")]),
    node("home", "Can't. Somebody's still out. (He drinks.) ...You want to know about Ashford. Everybody does. Sit, then.",
         speaker="holloway", nxt="tell"),
    node("tell", (
        "(He counts on his fingers, loses his place, and starts again.) Ground went. Lower town with it. "
        "Night. Half the garrison on the hill, at the cave mouths. Half down the shaft. Ladders. (He "
        "drinks.) Me at the top. Lamp. Windlass. Lid. Counting them up. Lamp in my eyes. One. Two. (A long "
        "time.) Ninety-one. Then I looked down."), speaker="holloway", choices=[
            ch("What did you see?", "saw"), ch("(Wait.)", "saw")]),
    node("saw", (
        "Dead. Climbing. Under the last of ours, close as that. (He holds one hand flat over the other.) "
        "Four hundred behind me, asleep. Bairns. (He drinks.) Lid down. Bar across. Sat on it. (He breathes "
        "out, a long way.) Three days, they knocked."), speaker="holloway", choices=[
            ch("You saved the upper town.", "saved"), ch("You shut them in.", "shut"),
            ch("Does anyone else know?", "knows"), ch("(Say nothing.)", "silent")]),
    node("saved", "Both numbers are right. That's the trouble with counting.", speaker="holloway", nxt="wrote"),
    node("shut", "I did.", speaker="holloway", nxt="wrote"),
    node("knows", (
        "(He looks into the cup.) Pell. Went up after, for his sister's money. Found the lid barred from the "
        "top. (He drinks.) He's a careful man. He's waiting for a price."), speaker="holloway", nxt="wrote"),
    node("silent", "(He counts. You can see his lips do it.)", speaker="holloway", nxt="wrote"),
    node("wrote", (
        "Wrote them down with the hill party. At the cave mouths. Some of the hill came home; nobody asked "
        "which. Widows get paid for the cave mouths. (He looks into the cup, finds it empty, and keeps "
        "holding it.) Go to bed. (He gets up, holding the gatepost, and looks down the dark road.) "
        "Somebody's still out. ...Always somebody still out."), speaker="holloway", effects=confessed,
        choices=[ch("Goodnight, Captain.", end=True), ch("(Leave him.)", end=True)]),
])

told = lambda how: [setf(maeca__told_lid=how)]
d["scene_did_he"] = conversation("scene_did_he", "well", [
    node("well", "(She's waiting for you at the well, which she never does.) He talked to you. Last night. At the gate.",
         speaker="maeca", choices=[
             ch("He told me about Ashford. The shaft, and the lid.", "told", effects=told("told")),
             ch("He was drunk. It was nothing.", "kept", effects=told("kept")),
             ch("(Say nothing.)", "quiet", effects=told("silent"))]),
    node("told", "She looks at you for a long time.", speaker="narrator", nxt="did"),
    node("kept", "She looks at you the way she looks at a track that might be lying.", speaker="narrator", nxt="did"),
    node("quiet", "She waits. You don't fill it. She nods, slowly, as if you had.", speaker="narrator", nxt="did"),
    node("did", "...Did he.", speaker="maeca", choices=[ch("(Go.)", end=True)]),
])

d["scene_his_cup"] = conversation("scene_his_cup", "cup", [
    node("cup", (
        "At the gate, Holloway is on the ground with his back to the post, counting. Maeca comes down the "
        "street, and takes the cup out of his hand, and fills it from her own flask, and gives it back. Then "
        "she sits down beside him with her crossbow across her knees, and he leans on her a little, and she "
        "lets him."), speaker="narrator", effects=[setf(holloway__cup_seen=True)], choices=[ch("(Leave them be.)", end=True)]),
])

save("dialogue.json", d)

# ---------------------------------------------------------------- the rules --
r = load("rules.json")
R = r["rules"]
def rule(rid, when, effect, report=None, once=True):
    x = {"id": rid}
    if once:
        x["once"] = True
    x["when"] = when
    x["effect"] = effect
    if report:
        x["report"] = report
    return x

no_morning = nott(fact("scene.morning", exists=True))
no_dusk = nott(fact("scene.dusk", exists=True))
holloway_rules = [
    # The first morning after a night fight: the gate stood open all night.
    rule("holloway.waited", all_(fact("arena.last.ago", 0), fact("prologue.done", True), no_morning),
         [setf(holloway__waited=True, scene__morning="scene_gate_dawn"),
          {"later": {"days": 1, "id": "holloway.count_due", "effect": [setf(holloway__count_due=True)]}}]),
    # A later morning after a night fight: the town at the gate, and him in it.
    rule("holloway.count", all_(fact("arena.last.ago", 0), fact("holloway.count_due", True), {"day": {"gte": 3}}, no_morning),
         [setf(scene__morning="scene_in_my_count")]),
    # The first dusk in town after the ground starts turning over, from day 4: the knocking.
    rule("holloway.knocking", all_(fact("tremor.felt", True), {"day": {"gte": 4}}, no_dusk),
         [setf(scene__dusk="scene_knocking")]),
    # The next morning she is waiting at the well; that dusk, her cup at the gate.
    rule("maeca.heard", all_(fact("holloway.confessed", True), no_morning), [setf(scene__morning="scene_did_he")]),
    rule("maeca.cup", all_(fact("maeca.told_lid", exists=True), no_dusk), [setf(scene__dusk="scene_his_cup")]),
    # The decoy, the morning after: red, or a ledger.
    rule("decoy.rope", all_(fact("holloway.cup_seen", True), nott(fact("redcowl", "dead")), nott(fact("redcowl", "spared")),
                             nott(fact("roost.cleared", True)), nott({"history": "burned_roost"})), [],
         "A Kerchief came into the Flagon last night, which they never do, and drank alone in the corner, and told "
         "the room on his way out that the Roost has a rope with the captain's name on it. Rav put him out. "
         "Holloway laughed when he heard, and then he didn't."),
    rule("decoy.ledger", all_(fact("holloway.cup_seen", True),
                               any_(fact("redcowl", "dead"), fact("redcowl", "spared"), fact("roost.cleared", True), {"history": "burned_roost"}),
                               nott(fact("caravan.pell", "exposed")), nott(fact("caravan.pell", "fled")), nott(fact("pell.fate", exists=True))), [],
         "Pell Varrow sat in the Flagon's window until late last night with his ledger open, and Rav says he wrote "
         "something down every time the captain drank."),
    # A rider from the north (Sallow's letter: Act 2 turns it over).
    rule("sallow.rider", {"day": {"gte": 5}}, [],
         "A rider came down through the north gate at first light with a silver seal on his saddlebag, and spent "
         "an hour in the Watch House with the door shut. Dame Keegan watched him go and wrote something down. "
         "Holloway was drunk by noon."),
]
# Before arena.ago (the last rule), so a fight last night still reads as ago 0.
i_ago = next(i for i, x in enumerate(R) if x["id"] == "arena.ago")
R[i_ago:i_ago] = holloway_rules
# The chapter closes after its beats: the knocking heard.
cr = next(x for x in R if x["id"] == "chapter.ready")
cr["when"]["all"].append(fact("holloway.confessed", True))
save("rules.json", r)

# ------------------------------------------------------- names and barks --
n = load("npcs.json")
n["npcs"]["maeca"]["name"] = "Maeca"
said = n["npcs"]["holloway"]["said"]
said.append({"text": "Ninety-one up.", "night": True, "when": fact("holloway.confessed", True)})
save("npcs.json", n)

f = load("folk.json")
f["lines"] += [
    {"text": "Captain won't bar the gate till he's counted the cat. Fox has had the hens twice.", "night": True},
    {"text": "He counts the gate in every night, the captain. Drunk, he counts past us. Ninety-one, and stops.", "night": True,
     "when": nott(fact("holloway.confessed", True))},
    {"text": "Maeca pays the captain's slate at the Flagon. Every week. He thinks it's the Watch.", "night": False},
]
save("folk.json", f)

q = load("quests.json")
q["beasts"]["entries"]["maeca_theory"] = q["beasts"]["entries"]["maeca_theory"].replace("Maeca Barefoot says", "Maeca says")
save("quests.json", q)
print("ok")

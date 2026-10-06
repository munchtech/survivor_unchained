"""Stage 3: the voice pass (audit item 4). Every named speaker rewritten
against docs/VOICES.md; hubs that move instead of menus repeated on every
node. Effects are carried over from the current data, never retyped."""
import os, sys, copy
sys.path.insert(0, os.path.dirname(__file__))
from js import *

O = load("dialogue.json")


def fx(c, n):
    return copy.deepcopy(O[c]["nodes"][n].get("effects"))


def cfx(c, n, frag):
    hits = [x for x in O[c]["nodes"][n]["choices"] if frag in (x["text"] if isinstance(x["text"], str) else x["text"][-1]["text"])]
    assert len(hits) == 1, (c, n, frag, len(hits))
    return copy.deepcopy(hits[0])


def keep(c, n, frag, text=None, **over):
    """An existing choice, conditions and effects intact, new words."""
    x = cfx(c, n, frag)
    if text is not None:
        x["text"] = text
    x.update(over)
    return x


def back(t="Something else."):
    return ch(t, goto="hub")


def convo(npc, entry, nodes, marker=None):
    c = {"npc": npc, "entry": entry}
    if marker is not None:
        c["marker"] = marker
    c["nodes"] = nodes
    return c


def E(node, when=None):
    return {"when": when, "node": node} if when else {"node": node}


NEW = {}

# ================================================================= ROOK ==
R = "rook"
rook_menu = lambda: [
    ch("I need a bed.", action="rest"),
    ch("Can you keep some things for me?", action="stash"),
    ch("What's the talk?", goto="rumours"),
    ch("Tell me about the Waystation.", goto="town"),
    keep(R, "first", "That lamp over the door", "That lamp over the door. It's from the Chapel of the Morning Light."),
    keep(R, "first", "There is a grave in the garden", "There's a grave in the garden behind the shrine. A captain, with his lamp."),
    ch("Who else has come up the Low Ford road?", once="ford", goto="ford"),
    ch("Another time.", end=True),
]
NEW[R] = convo(R, O[R]["entry"], {
    "first": node(V((hist("ford_warden_slain"), "Well. The one who walked up from the Low Ford at dawn. Chid came in babbling about blue lights going out at the crossing, and here you are, bleeding on my step. I'm Rook. This is the Last Lamp. Sit down before you fall down."),
                    "Another one off the Low Ford road. I'm Rook, and this is the Last Lamp: bed, bread, a bath if you ask nicely, and a strongroom for what you'd rather not carry about."),
                  rook_menu()),
    "hub": node(V((time("night"), "Late, {name}. Stew's cold. Beds aren't."),
                  (rel(R, "affection", gte=30), "There you are. I kept a bowl back. Don't tell the others."),
                  "Back again, {name}. What'll it be?"),
                rook_menu()),
    "rumours": node(V((eq("beasts.outcome", "cured"), "Wenna says the stream's running clean. The wolves have gone quiet, and Holloway's sulking because there's nobody left to pay. Harlan's still asking after his boy, mind."),
                      (eq("beasts.outcome", "slaughtered"), "No wolves on the road now. None. Brannoc's never seen so many pelts, and Maeca hasn't been in since. Make of that what you like."),
                      "Wolves, mainly. Holloway's paying for pelts, Maeca says they're sick, Harlan says they ate his caravan, and the Coyle boy's still missing. And there's a toll clerk drinking at the Flagon like he's come into money. Pick a story."),
                    [ch("A toll clerk with money?", goto="clerk"), back()], effects=fx(R, "rumours")),
    "clerk": node("Clerks don't buy rounds. This one bought three, the night Coyle's wagons went missing, and kept telling the room he'd \"done somebody a favour\". Rav was there. Rav's always there.",
                  [back(), ch("Goodbye, Rook.", end=True)]),
    "town": node("Three roads meet here, and everyone on them stops at my door. South's the Low Ford. East's the Old Road and the Verge. North's shut, and a girl in shiny armour will tell you why, at length. Everybody else you'll meet whether you want to or not.",
                 [ch("Who runs the place?", goto="runs"), back()]),
    "runs": node("Holloway thinks he does. Vonnra knows she does. Pell's got it written down in a book somewhere, with interest. And I feed all three of them, so you can draw your own conclusions.",
                 [back(), ch("Goodbye, Rook.", end=True)]),
    "ford": node("Not many, these last years. The ford's been bad. ...Vonnra pays me to tell her who comes up that road, and when. Don't look like that, pet; she pays everyone for something. I'd told her about you before you'd finished your stew.",
                 [ch("What did she say?", goto="ford2"), back()]),
    "ford2": node("Nothing. She paid me double. She's never paid me double for anything.",
                  [back(), ch("Goodbye, Rook.", end=True)]),
    "firstlamp": node("You found old Ashe, and his trunk. Captain of the first Watch, when it was forty lamps and not four. This inn's named for his: the Last Lamp, because it was the last one lit the night they closed the north road. We light the hearth from it every winter. Keep what was in the trunk; he'd have wanted it used. Just leave him where he lies.",
                      [ch("The note in the trunk was signed \"C.\"", once="c", goto="c"), back()], effects=fx(R, "firstlamp")),
    "c": node("Was it? Ashe was Ashe, all his life; never heard him called owt else. ...Somebody else's note, then, in a dead man's trunk. Now there's a thing.",
              [back(), ch("Goodbye, Rook.", end=True)]),
    "lamp": node("It is. My mother carried it up from the chapel the year the Order left, and it's not gone out since. You've one too, I see. Go and see Chid. He needs somebody who knows what the light's for. Lord knows he doesn't.",
                 [back(), ch("Goodbye, Rook.", end=True)], effects=fx(R, "lamp")),
    "wanted": node("Holloway's men were in asking after you. I told them you owed me money, which is true. Don't bring trouble under my roof.",
                   rook_menu()),
}, O[R].get("marker"))

# ============================================================ HOLLOWAY ==
H = "holloway"


def holloway_menu():
    return [
        ch("Tell me about the wolves.", once="wolves", goto="wolves"),
        keep(H, "first", "I have come about the bounty.", "I've come about the bounty."),
        ch("Harlan Coyle's caravan. What do you know?", once="caravan", goto="caravan"),
        keep(H, "first", "The wolves are sick, not bold."),
        keep(H, "first", "The wolves are poisoned.", "The wolves are poisoned. The Dig's dumping ember slurry into the stream."),
        keep(H, "first", "The beasts are dealt with.", "The beasts are dealt with. You can stop worrying."),
        keep(H, "first", "Pell Varrow paid the Kerchiefs", "Pell Varrow paid the Kerchiefs to take Coyle's caravan. Here's his ledger."),
        ch("That's all.", end=True),
    ]


NEW[H] = convo(H, O[H]["entry"], {
    "first": node(V((tag("kerchief_colors"), "You came up the Low Ford road in Kerchief red. Either you're one of them or you're a fool, and I've no room in the cells for either. Take that rag off in my town, or I'll take it off you. Holloway. Captain of what's left of the Watch."),
                    (hist("ford_warden_slain"), "You're the one who put the Ford-Warden down. The Watch kept those lamps, once. I'd thank you, but thanks don't feed eleven men. Holloway. Captain of what's left of the Watch."),
                    "You came up the Low Ford road. At night. Either you're very good or very lucky, and I've no use for either kind of trouble in my town. Holloway. Captain of the Watch."),
                  holloway_menu(), effects=fx(H, "first")),
    "hub": node(V((eq("beasts.outcome", "cured"), "The water's clean and the wolves are back in the deep wood. I was wrong about them. Don't tell anyone I said so."),
                  (eq("wolves.at_gate", True), "You heard. Aldo. He had a wife at Low Kiln and a bad knee, and they took him at my gate. Five a pelt, still. What do you want?"),
                  (rel(H, "trust", lte=-30), "You. Keep your hands where I can see them."),
                  (eq("beasts.outcome", "slaughtered"), "The road's quiet. I paid for every pelt of it. You know how quiet? Maeca's stopped coming in to argue with me."),
                  (all_(eq("beasts.bounty_claimed", True), nothas("beasts.outcome")), "I pay for a pelt and two more wolves come down the road. I'm starting to think Maeca's right, and I hate that. What is it?"),
                  "Make it quick. I've a gate to count."),
                holloway_menu()),
    "wolves": node("They're bolder. Two nights ago they came right up to the east gate. Five a pelt, fifty for the old grey one they call Greymuzzle. Bring me proof and I'll pay. Bring me stories and I won't. I've eleven men and four of them can hold a spear the right way round; I'm not spending them on stories.",
                   [ch("Maeca says they're running from something.", goto="maeca"), back(), ch("That's all.", end=True)], effects=fx(H, "wolves")),
    "maeca": node("Maeca's right more often than I'd like. She's earned that. ...She's earned a lot of things she never got.",
                  [ch("Such as?", once="ashford", goto="ashford"), back()]),
    "ashford": node("Boots, for a start. I counted boots for the Ashford garrison, once, and I was good at it. That's all you're getting. Something else?",
                    [back(), ch("That's all.", end=True)]),
    "bounty": node(V((item("greymuzzle_fang"), "That's his fang. That's the old devil himself. Fifty, as promised, and my thanks with it."),
                     "Pelts. Good. Let me count them."),
                   [keep(H, "bounty", "Hand over the fang."), keep(H, "bounty", "Hand over the pelts."), back()]),
    "liar": node("Dealt with. That's what you said. I paid you thirty of the Watch's gold for \"dealt with\", and this morning I had a drover bleeding on my gate. So. Tell me why you shouldn't spend the night in the cells.",
                 [keep(H, "liar", "Pay back the thirty."),
                  keep(H, "liar", "They were dealt with.", "They were dealt with. These are new ones. The wood's sick; they keep coming."),
                  keep(H, "liar", "Take it up with the wolves.")]),
    "repaid": node("A liar who pays his debts. Rarer than wolves, that. I've written both halves down.", holloway_menu()),
    "argued": node("...New ones. From a sick wood. Then the pelts buy me nothing, and you're telling me the bounty's a bucket against a flood. Find me the hole in the bucket and we'll call it square.", holloway_menu()),
    "defied": node("Out of my sight. And if I see you near my gate with a blade out, you'll find out how the cells feel on a cold night.", [ch("Go.", end=True)]),
    "caravan": node("Coyle's wagons never reached my gate. The Old Road was open all day; I had men on it dawn to dusk. Whatever happened to them happened off the road, and whoever told them otherwise lied.",
                    [ch("Who'd send wagons off the road?", goto="caravan2"), back()], effects=fx(H, "caravan")),
    "caravan2": node("Somebody who knew they were coming, what they carried and which clerk could be bought. That's a short list in a town this size, and I don't like a single name on it.",
                     [back(), ch("That's all.", end=True)]),
    "sick": node("Sick or bold, they bite the same. ...But if you're right, and you can show me what's sickening them, I'd rather fix the cause than pay for pelts till I'm old.",
                 [back(), ch("That's all.", end=True)], effects=fx(H, "sick")),
    "cause": node(V((flag(H, "open_to_cure"), "The lamplings. Of course it's the lamplings. Then I'm done paying for pelts: I'll not pay men to put down sick dogs. Deal with the pump. I'll keep watching the road."),
                    "The lamplings. Of course it's the lamplings. Deal with the pump and I'll stop paying for pelts. I won't stop watching the road."),
                  [back(), ch("That's all.", end=True)], effects=fx(H, "cause")),
    "lie": node("Dealt with. The road's been quiet today, I'll grant you that. Thirty for the trouble. And if I've wolves at my gate tomorrow night, we'll talk again.",
                [ch("Goodbye.", end=True)], effects=fx(H, "lie")),
    "expose": node(V((eq("player.pardoned", True), "Payments to \"R.\" Redcowl. And to my own toll clerk. On the night. Pell Varrow, you careful, greedy little man. My lads'll have him in irons before dark. ...And the strongbox you sold, we'll call that a fee for services. Once."),
                     "Payments to \"R.\" Redcowl. And to my own toll clerk. On the night. Pell Varrow, you careful, greedy little man. My lads'll have him in irons before dark. The Watch owes you, {name}. I don't say that lightly; I've not much to pay you with."),
                   [ch("Goodbye.", end=True)], effects=fx(H, "expose")),
    "arrest": node("You sold the Coyle cargo to a fence. Everyone in the Waystation knows it, and so do I. A hundred gold to the Watch and we'll say no more about it. Or you can leave my town.",
                   [keep(H, "arrest", "Pay the hundred."),
                    keep(H, "arrest", "who paid the Kerchiefs", effects=[setd({"player.wanted": False, "player.pardoned": True})]),
                    keep(H, "arrest", "I will keep out of your way.", "I'll keep out of your way.")]),
}, O[H].get("marker"))

# =============================================================== MAECA ==
M = "maeca"


def maeca_menu():
    return [
        ch("What's driving them out?", goto="driving"),
        keep(M, "first", "Their tracks are wrong.", "Their tracks are wrong. They're dragging their back legs."),
        keep(M, "first", "It is the stream.", "It's the stream. Ember slurry from the Dig."),
        keep(M, "first", "Can the wolves be spoken to?", "Can the Pack be spoken to?"),
        ch("Where can I find you?", once="where", goto="where"),
        ch("Why \"Barefoot\"?", once="barefoot", goto="barefoot"),
        ch("Goodbye.", end=True),
    ]


NEW[M] = convo(M, [
    E("cold", eq("beasts.outcome", "slaughtered")),
    E("cold", nk(M, "greymuzzle_fang_sold")),
    E("first", not_(met(M))),
    E("thanks", all_(eq("beasts.outcome", "cured"), noflag(M, "thanked"))),
    E("hub"),
], {
    "first": node(V((bg("hunter"), "You walk like someone who's followed a thing to its den. Hunter? Then you've seen it too, out there. They're not hunting. They're running. Maeca. Barefoot, before you ask."),
                    (tag("wolf_pelts"), "That cloak's made of wolves. I can smell it from here, and so can they. Maeca Barefoot. What do you want?"),
                    "Another blade for Holloway's bounty? The wolves aren't the problem. They're what the problem looks like from the road. Maeca Barefoot, of the Ashford garrison. What's left of it."),
                  maeca_menu(), effects=fx(M, "first")),
    "hub": node(V((time("night"), "(She doesn't look up from her cup.) It's late. Say it."),
                  (rel(M, "respect", gte=30), "Hunter. What have you found?"),
                  "You again. What is it?"),
                maeca_menu()),
    "driving": node("Something in the deep wood. The deer are thin, the Pack's thinner, and the old alpha, Greymuzzle, has brought them closer to people than he ever would. Find out why and you'll have done more than a hundred pelts. Ask Tam, by the well. He's seen something, and nobody believes a child.",
                    [back(), ch("Goodbye.", end=True)], effects=fx(M, "driving")),
    "tracks": node("You saw that? Nobody sees that. Dragging, yes. Weak in the hindquarters, like a dog that's eaten what it shouldn't. So. Not bold. Sick.",
                   [back(), ch("Goodbye.", end=True)], effects=fx(M, "tracks")),
    "truth": node("Grimtunnel's diggers. Should've known; every bad thing under Thornhollow has a lamp in its hand. Stop that pump and the Pack'll come back to itself. Days, maybe. It'll happen.",
                  [back(), ch("Goodbye.", end=True)], effects=fx(M, "truth")),
    "speak": node("Not with words. But Greymuzzle's old and he isn't stupid. Go into the Hollow with no wolf blood on you, none since you last slept. Don't wear their skins. And don't run. He'll decide what you are. If he decides wrong, well. Run then.",
                  [back(), ch("Goodbye.", end=True)], effects=fx(M, "speak")),
    "where": node("The Hunters' Blind, out past the wreck on the Old Road, most days. I watch the Hollow from there. You'll know it by the smoke; I'm the only one fool enough to light a fire in that wood. Nights, I'm here, drinking Rav's piss.",
                  [back(), ch("Goodbye.", end=True)]),
    "barefoot": node("Boots were signed for. They never came. You learn to hear the ground through your feet. I prefer it now.",
                     [ch("Who signed for them?", goto="signed"), back()]),
    "signed": node("Somebody with a good hand and a ledger. ...You ask a lot of questions for a stranger.",
                   [back(), ch("Goodbye.", end=True)]),
    "thanks": node("The Hollow's quiet. The Pack's eating again: deer, not travellers. I've been a hunter all my life, {name}, and I've never once saved anything. ...Thank you.",
                   [ch("Look after them.", goto="hub")], effects=(fx(M, "thanks") or []) + [setflag(M, "thanked")]),
    "cold": node("You emptied the Hollow. I heard. I hope Holloway's gold keeps you warm.", [ch("...", end=True)]),
}, O[M].get("marker"))

# =============================================================== WENNA ==
W = "wenna"


def wenna_menu():
    return [
        ch("Holloway says the wolves are getting bolder.", goto="animals"),
        keep(W, "first", "Tam says the wolves drank"),
        keep(W, "first", "I brought you water from the stream."),
        keep(W, "first", "Let me help you test it."),
        keep(W, "first", "I brought bitterroot."),
        keep(W, "first", "That beaked mask on the wall..."),
        ch("The fever year?", show=flag(W, "once:mask"), once="fever", goto="fever"),
        ch("What do you sell?", action="trade"),
        ch("Goodbye.", end=True),
    ]


NEW[W] = convo(W, O[W]["entry"], {
    "first": node(V((bg("scholar"), "A Cloister lens, and a Cloister squint. Scholar? Then don't touch anything, you'll only want to catalogue it. I'm Wenna. What d'you want?"),
                    "Don't touch that. Or that. Or— yes, that too. I'm Wenna. I make things that stop you dying, and a few that don't. What d'you want?"),
                  wenna_menu()),
    "hub": node(V((eq("beasts.outcome", "cured"), "You! Sit. No, don't sit, you'll squash the feverfew. The stream's clean, child. Clean."),
                  "Well? I've roots on the boil."),
                wenna_menu()),
    "animals": node("The animals were never like this. Never. And the water's tasted wrong all year: metal, and smoke. Bring me some from the Thornhollow stream, above the blight if you can, below it if you must, and I'll tell you what's in it.",
                    [back(), ch("Goodbye.", end=True)], effects=fx(W, "animals")),
    "tamsays": node("Tam. Course Tam saw it; nobody watches the ground like a boy with nothing to do. Drank and fell down. Not fought, not starved: drank. ...Bring me that water. A bottle, from where he saw them. I've been smelling metal in the well for a month and telling myself I was old.",
                    [back(), ch("Goodbye.", end=True)], effects=fx(W, "tamsays")),
    "analyse": node(V((item("slurry_sample"), "Green water, and— what's this? From a pipe? Ember. Ember slurry: the dust of the stones, cooked and watered down. Rots the belly of anything that drinks it. And nobody spills this much by accident. Someone upstream's getting rid of it."),
                      "Green. Warm. Smells like a chapel lamp. Ember slurry, child: the dust of the stones, cooked and watered. Rots the belly of anything that drinks it. Nobody spills this much by accident, {name}. Someone upstream's getting rid of it."),
                    [ch("Who would do that?", goto="who"), back()], effects=fx(W, "analyse")),
    "analyse_arcana": node("You know your salts. Yes, precipitate it, there, and— ember. Slurry, and fresh. Look at the grain: it's been through a pump. Nobody pumps ember but the lamplings, and the lamplings answer to Grimtunnel.",
                           [back(), ch("Goodbye.", end=True)], effects=fx(W, "analyse_arcana")),
    "who": node("Who digs? Who burns ember by the barrow-load? The lamplings. Find where it goes into the water and you'll find their pipe. Take an antidote or two, and don't drink anything out there. Not even if it's clear. Especially not if it's clear.",
                [back(), ch("Goodbye.", end=True)]),
    "root": node("Good. Fat ones, too. Here. Come back with more; I'm always short.", [back(), ch("Goodbye.", end=True)]),
    "mask": node("My blightward. I made it the fever year. Stuff the beak with bitterroot and you can walk through air that'd drop a horse. Take it. I'm too old to go where it's needed.",
                 [back(), ch("Goodbye.", end=True)], effects=fx(W, "mask")),
    "fever": node("The year after Ashford went into the ground. Half the valley coughing green and the other half burying them. Same smell as your bottle, child. Same smell exactly. ...I've roots on the boil.",
                  [back(), ch("Goodbye.", end=True)]),
}, O[W].get("marker"))

# ================================================================= TAM ==
T = "tam"
NEW[T] = convo(T, [
    E("happy", all_(any_(eq("beasts.outcome", "cured"), eq("stream.clear", True)), noflag(T, "happy"))),
    E("first", not_(met(T))),
    E("again"),
], {
    "first": node("They drank from the stream and they fell down. Three of them. Nobody believes me. ...You believe me?",
                  [ch("I'm listening.", goto="story"), ch("Where is your farm?", goto="farm"), ch("Stay by the well.", end=True)]),
    "story": node("Down by the green water, past the old fence where Pa lost the goat. Three wolves. They drank and they lay down and they didn't get up, and their eyes went all milky like Gran's. And the water smells like the chapel lamps. Pa says stay in town. I stayed in town.",
                  [keep(T, "story", "You did right to tell someone."), ch("Where is your farm?", goto="farm")], effects=fx(T, "story")),
    "farm": node("Out past the Old Road, where the wood starts. Pa won't leave it. He says wolves is wolves and a farm's a farm. But these ones aren't right.",
                 [ch("Stay by the well, Tam.", end=True)], effects=fx(T, "farm")),
    "again": node(V((eq("beasts.outcome", "ignored"), "They came right up to the gate. I heard them. Pa says we're not going home. Not ever, maybe."),
                    (eq("tam.farm", "raided"), "Pa's at Wenna's. She says he'll keep the arm. The Watch says it was wolves. I SAID it was wolves. Weeks ago."),
                    (eq("tam.farm", "emptied"), "The wolves broke our door and ate all the hens. All of them. Pa says he'd have been in the hens' place if not for you, and then he called you a bad word. He was smiling, though."),
                    (all_(fact("beasts.severity", gte=4), not_(eq("tam.pa_in", True))), "Pa didn't come in last night. He always comes in."),
                    "Did you find out what's wrong with them?"),
                  [ch("Tell me again what you saw.", goto="story"),
                   keep(T, "again", "fetch your Pa", "Your farm's past the Old Road, you said. I'll fetch your Pa in before dark."),
                   ch("Not yet.", end=True)]),
    "fetch": copy.deepcopy(O[T]["nodes"]["fetch"]),
    "happy": node("The water's clear! Pa says I can go home! Pa says you did it. Did you do it?",
                  [keep(T, "happy", "I did."), keep(T, "happy", "Lots of people did.")], effects=[setflag(T, "happy")]),
}, O[T].get("marker"))

# ============================================================= BRANNOC ==
B = "brannoc"


def brannoc_menu():
    return [
        ch("Show me what you've made.", action="trade"),
        keep(B, "first", "I have wolf pelts to sell.", "I've wolf pelts to sell."),
        keep(B, "first", "Make me a cloak from five wolf pelts."),
        ch("Can you improve my weapon?", action="reforge"),
        ch("Those lamp-irons on the rack?", once="irons", goto="irons"),
        ch("Goodbye.", end=True),
    ]


NEW[B] = convo(B, O[B]["entry"], {
    "first": node(V((bg("hunter"), "Hunter. Good. You'll know a clean pelt. Brannoc. Iron, and things with fur on."),
                    "Brannoc. I make things of iron. I buy things with fur on. Which?"),
                  brannoc_menu()),
    "hub": node(V((time("night"), "Forge is banked. Make it quick."), (rel(B, "respect", gte=20), "Back. Good. Steel or fur?"), "Steel or fur?"), brannoc_menu()),
    "cloak": node("There. Warmest thing you'll ever wear. Every wolf in Thornhollow'll know what it is.", brannoc_menu()),
    "irons": node("Spares. Lamp-irons for the Low Ford. Twelve ordered last winter, ten collected. Collected at night; coin left on the anvil. Old coin, the square kind. Didn't ask who. ...Should've.",
                  [back(), ch("Goodbye.", end=True)]),
}, O[B].get("marker"))

# ============================================================== HARLAN ==
HA = "harlan"


def harlan_menu():
    return [
        ch("What happened to the caravan?", goto="what"),
        ch("Which road were they on?", goto="route"),
        keep(HA, "first", "It was not wolves.", "It wasn't wolves. Your wagons were driven off the road."),
        keep(HA, "first", "Jory's alive."),
        keep(HA, "first", "I found your strongbox."),
        keep(HA, "first", "Pell Varrow paid the Kerchiefs"),
        keep(HA, "first", "What were you carrying"),
        ch("Goodbye.", end=True),
    ]


NEW[HA] = convo(HA, O[HA]["entry"], {
    "first": node("Harlan Coyle, of the Coyle Company: salt, iron and Morrow cloth, the best on the Old Road. You came up the south road? Then you didn't pass three wagons and a boy called Jory. No. No, of course you didn't. Forgive me. Four days. He's never four days late.",
                  harlan_menu(), effects=fx(HA, "first")),
    "hub": node(V((eq("caravan.survivors", "rescued"), "Jory's round the back, pretending to count crates. Pretending! What can I do for you, friend?"),
                  (eq("caravan.survivors", "dead"), "I heard. I heard. You needn't say it. What do you want?"),
                  (fact("caravan.days", gte=3), "(He doesn't get up.) Three days of watching that road. I stopped. Somebody has to keep the stock, I told myself. Any word? No. There never is."),
                  (fact("caravan.days", gte=1), "(He keeps his eyes on the bend in the Old Road while he talks.) I keep thinking the lead wagon'll come round there, Jory shouting that he got lost. Any word?"),
                  "Any word? Anything at all?"),
                harlan_menu()),
    "what": node("The wolves, that's what. Three caravans this month. A hundred gold to whoever brings Jory home, and another hundred for my goods. Price the salt however you like. The boy, I'll pay what you ask.",
                 [ch("Which road were they on?", goto="route"), back()]),
    "route": node("The east road. The Old Road, through Thornhollow. They should've come through Vonnra's gate at dusk, four days back. Holloway had men on the road. Nobody saw them.",
                  [back(), ch("Goodbye.", end=True)]),
    "notwolves": node("Driven...? Wolves don't drive wagons. Who— no. Find out who. Please.", [back(), ch("Goodbye.", end=True)], effects=fx(HA, "notwolves")),
    "jory": node("Alive. Alive! I— here. A hundred, as I said, and that's the least of it. Whatever you need that I can sell you, you pay cost. Cost! Don't tell anyone.",
                 [back(), ch("Goodbye.", end=True)], effects=fx(HA, "jory")),
    "box": node("The strongbox! Unopened. You could've walked off with this and I'd never have known. A hundred gold, and my thanks. And my thanks again.",
                [back(), ch("Goodbye.", end=True)], effects=fx(HA, "box")),
    "pell": node("Pell. Pell! We shook hands on this square at midsummer; he offered to buy me out, as a friend. Give me that. Holloway will see it if I have to nail it to his door.",
                 [back(), ch("Goodbye.", end=True)], effects=fx(HA, "pell")),
    "be": node("...Six crates. For a buyer I won't name. Paid in advance, in gold, which is why I asked no questions. B.E. Blasting ember. Somebody out there wants to dig a very big hole.",
               [ch("Who's \"G.\"?", once="g", goto="g"), ch("Did Jory know what he was carrying?", once="knew", goto="knew"), back()], effects=fx(HA, "be")),
    "g": node("A customer. Customers have initials, friend; it's how you tell them from friends. Is there anything else? Only I've stock to count.",
              [back(), ch("Goodbye.", end=True)]),
    "knew": node("Jory? Jory knows salt from sugar on a good day. He didn't know. ...He didn't know. I did.",
                 [back(), ch("Goodbye.", end=True)]),
    "betrayed": node("You. You found it, and you kept it. Get away from my stall.", [ch("...", end=True)]),
}, O[HA].get("marker"))

# ================================================================ PELL ==
P = "pell"


def pell_menu():
    return [
        ch("What do you trade in?", action="trade"),
        keep(P, "first", "You smell of Kerchief money."),
        keep(P, "first", "I have read your ledger.", "I've read your ledger."),
        ch("Terrible business, the caravan.", goto="caravan"),
        keep(P, "first", "I know what is killing the wolves.", "I know what's killing the wolves. It's worth something."),
        ch("Your books. Who buys ember in this town?", show=any_(knows("root_cause"), knows("clue.blasting_ember")), once="books", goto="books"),
        ch("Goodbye.", end=True),
    ]


NEW[P] = convo(P, O[P]["entry"], {
    "first": node("Pell Varrow. Factor. If it can be bought, stored or sold in the Waystation, it's been through my books at least once. Terrible business, Coyle's wagons. Terrible.", pell_menu()),
    "hub": node(V((rel(P, "fear", gte=30), "(He smiles a little too quickly.) Ah. You. What can I do for you today, specifically?"),
                  "Good day. Buying, selling, or simply being seen with me?"),
                pell_menu()),
    "caravan": node("The wolves, one hears. Such a shame for Harlan. Such a shame for the Company. I've offered to buy him out, of course. As a friend. Someone ought to own those wagons who knows what not to put in them.",
                    [back(), ch("Goodbye.", end=True)]),
    "smell": node("...Careful. That's the kind of thing that gets said once. Walk with me. You understand how things are done, I think. Coyle's finished; the only question is who picks up the pieces. Sixty gold now, and more later, to let the Kerchiefs keep what they have. You needn't do a thing. Only not do certain other things.",
                  [keep(P, "smell", "Take the money."), keep(P, "smell", "I will think about it.", "I'll think about it."), keep(P, "smell", "I think Holloway would like to hear this.")]),
    "confront": node("Where did you— the clerk. Of course. Let's be civilised. There's gold in this for you, a good deal of gold, if that book were to go in the fire.",
                     [keep(P, "confront", "Name a price."), ch("Why pay a bandit for salt and cloth?", once="why", goto="why"), keep(P, "confront", "Holloway will want to see this.")]),
    "why": node("It wasn't the salt I was paying for. Ask Harlan what else was on those wagons, and who for. Then ask yourself whether you'd rather it reached them or sat in a ravine with a dozen drunks. ...I'm not a good man. I'm a careful one. In this valley that's rarer.",
                 [keep(P, "confront", "Name a price."), keep(P, "confront", "Holloway will want to see this.")]),
    "bribe": node("Eighty gold. And the book.", [keep(P, "bribe", "Done."), keep(P, "bribe", "No.")]),
    "dig": node("Is it? Go on. ...The Dig. Grimtunnel's little lamp-people, pumping their slurry into the stream. Oh, that is worth something. Not to Holloway: to the diggers. A pipe can be moved, for a consideration, and a consideration can be split. Forty gold, and the wolves stop dying. Everyone's happy. Especially me.",
                [keep(P, "dig", "Forty. Done."), keep(P, "dig", "On second thought", "On second thought, I'll deal with it myself.")]),
    "dig_done": node("A pleasure. Give it two days. And if anyone asks, you and I discussed the weather.", [back(), ch("Goodbye.", end=True)]),
    "books": node("Who doesn't? Lamp-oil, chapel candles, a little blasting for the quarrymen. All very ordinary. ...And then there's the hill. Do you know how much ember has gone into that hill this year? I do. I have the receipts. Nobody digs that deep for coal.",
                  [ch("Then what are they digging for?", goto="books2"), back()]),
    "books2": node("I'm a factor, not a priest. I only know what things cost. Whatever's down there, it's expensive.", [back(), ch("Goodbye.", end=True)]),
    "ally": node("Our arrangement stands. Discreetly, please.", [ch("What do you have?", action="trade"), ch("Goodbye.", end=True)]),
}, O[P].get("marker"))

# ================================================================= RAV ==
RV = "rav"


def rav_menu():
    return [
        ch("Tell me about the Kerchiefs.", goto="kerchiefs"),
        keep(RV, "first", "news of Coyle's caravan", "Did anyone come through with news of Coyle's caravan?"),
        keep(RV, "first", "Know anyone who would buy this", "Know anyone who'd buy this, quietly?"),
        keep(RV, "first", "Can you get me into the Roost alive?"),
        ch("Redcowl. You know him?", show=any_(knows("hint.roost"), quest("caravan", "redcowl_met")), once="redcowl", goto="redcowl"),
        ch("What have you got for sale?", action="trade"),
        ch("Goodbye.", end=True),
    ]


NEW[RV] = convo(RV, O[RV]["entry"], {
    "first": node(V((bg("outcast"), "Well, well. Somebody who knows how to wear a kerchief without looking like a parrot. Sit. I'm Rav Cutwell. Doctor Cutwell, if you're bleeding. Doctor McBreathless, if you're the Watch."),
                    (tag("kerchief_colors"), "Red cloth, walking into my tavern in daylight. Brave, or somebody gave it you for a joke. Rav. Sit, before Holloway sees you."),
                    "You're in my light. ...Oh, sit, then. Rav. I was a doctor, then I was a Kerchief, and now I'm a doctor who drinks here. Ask me which paid better."),
                  rav_menu()),
    "hub": node(V((rel(RV, "trust", gte=30), "Pal. Pull up a stool."),
                  (time("night"), "Night surgery's double. Night drinking's the same price; I checked."),
                  "What'll it be? Advice is free, and worth it."),
                rav_menu()),
    "kerchiefs": node("Redcowl runs them. He'd rather talk than bleed, and he'd rather you bled than he talked. Their camp's in the ravine off the Old Road: the Roost. Wear red, walk slow, keep your hands empty, and you might get to say hello before they shoot you.",
                      [back(), ch("Goodbye.", end=True)], effects=fx(RV, "kerchiefs")),
    "clerk": node(V((knows("underworld"), "A toll clerk bought the room a round the night the caravan vanished. Clerks don't buy rounds. He'd \"done somebody a favour\": told Coyle's teamsters the road was shut and sent them down the forest track. Between us, he's also a key he shouldn't have. Pell's warehouse. Showed it me like a boy with a frog."),
                    "A toll clerk bought the room a round the night the caravan vanished. Clerks don't buy rounds. He'd \"done somebody a favour\": told Coyle's teamsters the road was shut and sent them down the forest track. Draw your own lines, pal."),
                  [back(), ch("Goodbye.", end=True)], effects=fx(RV, "clerk")),
    "fence": node("Coyle's strongbox. Oh, dear. Aye, I know a man. A hundred and fifty, and nobody asks where it came from. At first. People always find out in the end; it's the only law in this valley that gets kept.",
                  [keep(RV, "fence", "Sell it."), keep(RV, "fence", "On second thought.")]),
    "roost": node("Alive, and talking? Wear this, walk in the front, and say \"Redcowl owes Rav a leg.\" He'll laugh. If he laughs, you're in. If he doesn't laugh, I was never here.",
                  [back(), ch("Goodbye.", end=True)], effects=fx(RV, "roost")),
    "redcowl": node("Know him? I sewed his leg back on with a sail-needle and a bottle of something blue, and he's never once said thank you. That's the leg he owes me. ...Don't ask me the rest. I'm a doctor; I don't do family histories.",
                    [back(), ch("Goodbye.", end=True)]),
}, O[RV].get("marker"))
# The key line: "he's also a key" reads wrong; fix the slip in place.
NEW[RV]["nodes"]["clerk"]["text"][0]["text"] = NEW[RV]["nodes"]["clerk"]["text"][0]["text"].replace("he's also a key", "he's also got a key")

# ================================================================ CHID ==
CH = "chid"


def chid_menu():
    return [
        ch("Used to work?", goto="shrine"),
        keep(CH, "first", "Let me try. I know the rite."),
        keep(CH, "first", "Bless me, Chid."),
        keep(CH, "first", "There is a sealed door in the Verge.", "There's a sealed door in the Verge."),
        keep(CH, "first", "Something is digging under the Verge.", "Something's digging under the Verge."),
        keep(CH, "first", "The Warden at the Low Ford.", "The Warden at the Low Ford. The lamps fed it. Who made it?"),
        ch("How long have you kept the shrine?", once="long", goto="long"),
        ch("Goodbye.", end=True),
    ]


NEW[CH] = convo(CH, O[CH]["entry"], {
    "first": node(V((bg("devout"), "Oh! A lantern of the Order! Lit! Oh, sit down, sit, sit. I'm Chid. They call me the Fool, which is fair. This is the shrine of the Morning Light. It used to work."),
                    "Oh! A visitor. Hello! I'm Chid. They call me the Fool, which is fair. This is the shrine of the Morning Light. It used to work."),
                  chid_menu()),
    "hub": node(V((eq("shrine.lit", True), "It's still burning! Every morning I check. Still burning."),
                  "Hello again! The light's patient. I'm trying to be."),
                chid_menu()),
    "woke": node(V((eq("shrine.lit", True), "You're awake! Good. Good! A carter found you on the Old Road and brought you here, and the flame... the flame kept you. I watched it. You'll be sore a day or two. Whatever did this to you is still out there, {name}. It'll have your things. They always keep something."),
                   "Oh, you're awake. A carter found you on the Old Road and brought you in, and I didn't know what else to do, so I prayed at the shrine and... well. Here you are. You'll be sore a day or two. Whatever did this is still out there. It'll have your things."),
                 [keep(CH, "woke", "Thank you, Chid."), ch("Where did I fall?", goto="where"), ch("You look like you've seen this before.", once="before", goto="before")],
                 effects=fx(CH, "woke")),
    "where": node("In the Verge. The carter said there was a grave-mark where you lay, and your purse under it, and a beast standing over it that wouldn't let him near. Be careful. It knows your smell now.",
                  [ch("I'll get it back.", end=True)]),
    "before": node("Have I? Oh. Well. You were cold when they brought you in. Properly cold, the way the dead go cold. And then you weren't. ...It's been a long time since I saw anyone do that. I'd forgotten how it looks. Rest, now.",
                   [ch("I'll get my things back.", end=True)]),
    "shrine": node("The flame. It blessed people. Kept the dead lying down where you'd put them. Then the Order left and the flame went out, and I've been... trying. With prayers. And candles. And a bellows, once. That was a bad day.",
                   [back(), ch("Goodbye.", end=True)]),
    "relight": node("You open your lantern and say the words you learned at seven, the ones about the dark being only the part of the day that hasn't happened yet. The shrine takes the flame as if it had been waiting for it. Chid makes a sound like a kettle.",
                    speaker="narrator", effects=fx(CH, "relight"), next="lit"),
    "lit": node("It WORKS. It works! I knew it worked. I said it worked! I have to tell Rook. I have to tell everyone. Thank you. Oh, thank you!", chid_menu()),
    "blessed": node("There. Go on, then, and be warm.", [back(), ch("Goodbye.", end=True)]),
    "warden": node("The Order made it, I think. Before the Watch. Before me, certainly, which is a long time. Everything the Morning Light made was made to guard something. That's the trouble with guards: they outlast whatever they were guarding against, and then they guard against us.",
                   [back(), ch("Goodbye.", end=True)], effects=fx(CH, "warden")),
    "vault": node("The old empire did something there, before the Watch. I think the Watch was founded to keep it done. I don't know what. Vonnra does. Vonnra won't say. That, I think, is the answer.",
                  [back(), ch("Goodbye.", end=True)], effects=fx(CH, "vault")),
    "below": node("Digging. Down. The Order used to say the dark's only light that hasn't been found yet. I never liked that one. It sounds like a threat.",
                  [back(), ch("Goodbye.", end=True)]),
    "long": node("Oh, ages. Since— well. Rook's mother used to bring me bread. Lovely woman. Terrible bread. ...Is that the time? I should light a candle.",
                 [back(), ch("Goodbye.", end=True)]),
}, O[CH].get("marker"))

# ============================================================== VONNRA ==
VO = "vonnra"


def vonnra_menu():
    return [
        keep(VO, "first", "I will pay the toll.", "I'll pay the toll."),
        keep(VO, "first", "Did Coyle's caravan pay your toll?"),
        keep(VO, "first", "The sealed door in the Verge..."),
        keep(VO, "first", "I have come to read your old script.", "I've come to read your old script."),
        ch("What did you see, the night I came up the road?", show=hist("ford_warden_slain"), once="ford", goto="ford"),
        ch("What do you sell?", action="trade"),
        keep(VO, "first", "Tell me my fortune."),
        ch("Goodbye.", end=True),
    ]


f = {k: copy.deepcopy(O[VO]["nodes"][k]) for k in ("fortune", "f_beasts", "f_caravan", "f_pell", "f_self", "f_below", "f_door")}
NEW[VO] = convo(VO, O[VO]["entry"], {
    "first": node(V((bg("scholar"), "A reader. You have the look. The toll is the toll: five gold to pass east. I am Vonnra. I see a great deal and say very little. You, of all people, will find that frustrating."),
                    (hist("ford_warden_slain"), "So. The one from the ford. ...Sooner than I had thought. The toll is the toll: five gold to pass east. I am Vonnra. I see a great deal and say very little. You will find that is the arrangement."),
                    "The toll is the toll. Five gold to pass east, or no gold and I remember your face. I am Vonnra. I see a great deal and say very little. You will find that is the arrangement."),
                  vonnra_menu(), effects=fx(VO, "first")),
    "hub": copy.deepcopy(O[VO]["nodes"]["hub"]) | {"choices": vonnra_menu()},
    "paid": node("The east gate is yours. Try to come back through it.", vonnra_menu()),
    "ledger": copy.deepcopy(O[VO]["nodes"]["ledger"]),
    "ledger_read": node("There. The Coyle caravan did not pay my toll. It never came through my gate. Whatever happened to it happened before it reached me.", vonnra_menu()),
    "vault": node("No. Not for any price. That is the only thing I will ever say to you without charging for it.", vonnra_menu(), effects=fx(VO, "vault")),
    "arcana": node("You do read. Then you know what \"Legio Septima\" means over a door, and you know better than to ask me what is behind it. Ask me something cheaper.", vonnra_menu(), effects=fx(VO, "arcana")),
    "ford": node("A light going out at the crossing. And then, a little after, another one coming on. It is not often the second thing happens. ...That would be five gold. This once, no charge.", vonnra_menu()),
    **f,
}, O[VO].get("marker"))
NEW[VO]["nodes"]["f_door"]["text"] = "No. That is all. That is all I see for free. The rest you will walk into yourself, and you will, because you are the kind that does."

# ============================================================== KEEGAN ==
KE = "keegan"


def keegan_menu():
    return [
        ch("What's north?", goto="north"),
        ch("The children call you \"Professor\".", once="prof", goto="prof"),
        keep(KE, "hub", "The Ford-Warden."),
        keep(KE, "hub", "Captain Ashe is buried in the garden.", "Captain Ashe is buried in the garden. Did the Vigil know him?"),
        ch("Your Vigil. Where are the rest of you?", once="vigil", goto="vigil"),
        ch("How will you know when I'm ready?", once="ready", goto="ready"),
        ch("Goodbye.", end=True),
    ]


NEW[KE] = convo(KE, O[KE]["entry"], {
    "first": node("Halt! None pass north. Dame Keegan Orme, of the Argent Vigil. Probationary. It is a real title.", keegan_menu()),
    "hub": node(V((knows("lore.warden"), "You again. Have you read anything since we last spoke? No? I can tell."), "Still not ready. I would know."), keegan_menu()),
    "north": node("Things you are not ready for. When you are, I will know. It is in the probationary handbook, chapter four.",
                  [ch("What's in chapter four?", goto="ch4"), back()]),
    "ch4": node("That is between me and chapter four.", [back(), ch("Goodbye.", end=True)]),
    "prof": node("I taught rhetoric at Saint Wend's before I took the oath, and somebody's mother found out. Now I am Professor to everyone under four feet tall. Rhetoric is not without its uses when telling people no. That was litotes. You're welcome.",
                 [back(), ch("Goodbye.", end=True)]),
    "warden": node("...Who told you that? The Vigil kept those lamps before the Watch did. Before the Watch was the Watch. The lamps were never to keep the dark out. They were to keep the Warden asleep. If somebody lit them again, somebody wanted it awake. Do not repeat that. I am probationary.",
                   [ch("Who'd want it awake?", goto="who"), ch("Goodbye.", end=True)], effects=fx(KE, "warden")),
    "who": node("Someone who needed the ford closed. Someone who wanted a heart. You tell me; you were there.", [back(), ch("Goodbye.", end=True)]),
    "ashe": node("Know him? The Vigil buried him. He closed the north road with forty lamps and walked back through it with one. What he saw up there is why I am standing here telling you no. Were he here, he would tell you himself, once you were ready.",
                 [back(), ch("Goodbye.", end=True)], effects=fx(KE, "ashe")),
    "vigil": node("At the chapterhouse, in the north. Keeping the vigil. I write every month. They are very busy. ...It is a long way, and the roads are bad, and I am sure the letters are simply waiting at a waystation somewhere, being read by nobody.",
                  [back(), ch("Goodbye.", end=True)]),
    "ready": node("The handbook is very clear on the signs, and I am watching for them. You would not like it if I saw them. ...That came out wrong. I mean you would not like the paperwork.",
                  [back(), ch("Goodbye.", end=True)]),
}, O[KE].get("marker"))

# =============================================================== SELLA ==
S = "sella"


def sella_menu():
    return [
        ch("What do you hear, up there?", goto="hear"),
        ch("How much for the night?", goto="price"),
        keep(S, "first", "Does Rook mind?"),
        ch("Who pays you for what you hear?", show=flag(S, "once:rook"), once="buyers", goto="buyers"),
        ch("Not tonight.", end=True),
    ]


night = copy.deepcopy(O[S]["nodes"]["night"])
night["text"] = V((eq("settings.intimacy", "full"),
                   "[explicit scene: Sella and {name}, the blue room at the top of Rook's stairs, by lamplight; warm, unhurried and funny, a professional who enjoys her work, tenderness showing at the edges and quickly put away; ends with her asleep across you and the sun up — to be written]"),
                  "She takes the coins first and your hand second, and leads you up Rook's narrow stairs. The blue room smells of lavender and lamp oil, and the bath is warm, at least to begin with. She undoes your buckles as if she has done a great many of them, and laughs at the last one. After that the door is shut, and what happens behind it is slow, and warm, and nobody's business but yours. For a few hours the road and the dead on it are a long way off. You wake with her hair across your chest and the sun already up. She is dressed, and counting.")
NEW[S] = convo(S, O[S]["entry"], {
    "first": node(V((hist("ford_warden_slain"), "So you're the one who put the big dead bastard at the ford back in the ground. Half the tavern's been drinking to you and the other half's been drinking to them. I'm Sella. I keep the blue room at the top of Rook's stairs. Talk's free. The rest isn't."),
                    "You've the look of someone who's been sleeping in ditches, love. Sella. I keep the blue room at the top of Rook's stairs. Talk's free. The rest isn't."),
                  sella_menu()),
    "hub": node(V((time("night"), "Evening, {name}. The lamp's lit upstairs, if you're asking. You look like you're asking."),
                  "Back again. People'll talk. Let them; it's good for business."),
                sella_menu()),
    "again": node(V((time("night"), "There you are. I was starting to think you'd found someone cheaper. You'd have been robbed."),
                    "{name}. Still walking straight, I see. I'll take that as a compliment."),
                  sella_menu()),
    "hear": copy.deepcopy(O[S]["nodes"]["hear"]) | {"choices": [back(), ch("Not tonight.", end=True)]},
    "rook": node("Rook minds everything. She also takes a third, keeps the drunks off the stairs, and once put a Kerchief through the front door for not paying. I've had worse landladies. I've had worse mothers.",
                 [back(), ch("Not tonight.", end=True)], effects=fx(S, "rook")),
    "buyers": node("Clever. Everybody, love. Pell pays for what his rivals say. Holloway pays for what his men say. Vonnra pays for all of it, more than anyone, and she's never once come up the stairs. Rook takes a third of everything. ...What you say up there's yours. Unless somebody outbids you. Nobody has. Yet.",
                   [back(), ch("Not tonight.", end=True)]),
    "price": node("Fifteen gold, up front. For that you get the blue room, a bath that's warm at least to start with, and me, until morning. Anything you'd rather I didn't do, say so. Anything you'd rather I did, say that too.",
                  [keep(S, "price", "15 gold, then."), keep(S, "price", "Just the talk, for now.")]),
    "night": night,
    "morning": node(V((fact("sella.nights", gte=3), "You're getting to be a habit, {name}. I don't mind. Rook does; she says you're wearing out the stairs. Go on, the day's wasting, and somebody out there needs killing."),
                      "You snore, by the way. Not badly. Go on, then. Come back in one piece; the pieces are what I like."),
                    [keep(S, "morning", "Sleep a little longer first."), keep(S, "morning", "Until next time.")]),
}, O[S].get("marker"))

# ========================================================== GREYMUZZLE ==
G = "greymuzzle"
NEW[G] = copy.deepcopy(O[G])
NEW[G]["nodes"]["ally"]["text"] = "Greymuzzle lifts his head and howls, once. Four of the strongest get up and come to stand beside you. The old wolf lies back down among the sick. He is not coming. They are his answer."
NEW[G]["nodes"]["again"]["text"] = V((eq("beasts.outcome", "cured"), "Greymuzzle is on his feet. So are the others. He looks at you, and then away, which from a wolf is as good as thanks."),
                                     "Greymuzzle watches you from the rocks. He does not get up.")

# ============================================================= REDCOWL ==
RC = "redcowl"
NEW[RC] = convo(RC, O[RC]["entry"], {
    "first": node(V((tag("kerchief_colors"), "Look at the colours on you. You're not one of mine, and you're not daft enough to be one of Holloway's. Redcowl. You're standing in my Roost. Talk."),
                    "Redcowl. You're standing in my camp, which means my sentries are drunk or you're interesting. Which is it?"),
                  [keep(RC, "first", "Redcowl owes Rav a leg."),
                   keep(RC, "first", "I have come for the Coyle wagons.", "I've come for the Coyle wagons."),
                   keep(RC, "first", "Let the teamsters go."),
                   keep(RC, "first", "Pell Varrow sold you out.", "Pell Varrow sold you out. It's in his ledger."),
                   keep(RC, "first", "The Watch is on its way."),
                   ch("Who are all these people?", once="who", goto="who"),
                   ch("I'll be going.", end=True)]),
    "hub": node("Still here? Ha. Talk, then.",
                [keep(RC, "hub", "About the Coyle wagons."), keep(RC, "hub", "Let the teamsters go."), keep(RC, "hub", "Pell Varrow sold you out."),
                 ch("Who are all these people?", once="who", goto="who"), ch("Nothing.", end=True)]),
    "who": node("Mine. Forty-one mouths, and a dozen of them can hold a blade. The rest are what's left when a town goes into the ground and the Watch counts its boots and goes home. ...Ha! Listen to me. Talk or bleed, I said. Talk.",
                [ch("About the Coyle wagons.", goto="goods"), ch("Nothing.", end=True)]),
    "rav": node("Ha! HA. That old saw-bones. He does too, and he knows it. All right. Rav's friends get to talk before they get shot. So: talk.",
                [keep(RC, "rav", "I have come for the Coyle wagons.", "I've come for the Coyle wagons."), keep(RC, "rav", "Let the teamsters go."), keep(RC, "rav", "Just saying hello.")],
                effects=fx(RC, "rav")),
    "goods": node("The wagons are salvage, and salvage is mine. You want the strongbox, you buy it. A hundred gold and I'll throw in the teamsters, since they eat more than they're worth.",
                  [keep(RC, "goods", "Pay a hundred gold."), keep(RC, "goods", "Five good wolf pelts instead."),
                   keep(RC, "goods", "I have killed a dozen", "I've killed a dozen of your people today. Give me the box."),
                   keep(RC, "goods", "Your wolf trouble is over.", "Your wolf trouble's over. That's worth something."),
                   keep(RC, "goods", "No deal.")]),
    "deal": node("Pleasure. Box is by the tents; the teamsters are in the cages. Open them yourself; my lads won't stop you. And {name}: if Holloway asks, you've never seen my face.",
                 [keep(RC, "deal", "Done.")], effects=fx(RC, "deal")),
    "favour": node("Is it, now. The howling's been keeping my lot up nights, I'll admit. ...Fine. The teamsters, for the favour. The box you still pay for. Fifty, for a friend.",
                   [keep(RC, "favour", "Fifty, then."), keep(RC, "favour", "Just the teamsters.")], effects=fx(RC, "favour")),
    "prisoners": node("The teamsters? They eat my food and pray a great deal. Fifty for their keep and they're yours.",
                      [keep(RC, "prisoners", "Pay fifty."), keep(RC, "prisoners", "Not today.")]),
    "released": node("Cages are over there. Mind the one on the end; he bites.", [keep(RC, "released", "Leave.")]),
    "pell": node("...Give me that. \"R., for the Coyle job.\" And to the clerk. And— \"tell Holloway where they camp, after.\" After! Varrow, you soft-handed little— Take your wagons. Take your teamsters. I've business in the Waystation.",
                 [ch("Leave.", end=True)], effects=fx(RC, "pell")),
    "trick": node("The Watch. Holloway hasn't got the men to— (a whistle, from the ridge; the whole camp stops) —PACK IT UP! PACK IT UP! Leave the heavy stuff!",
                  [keep(RC, "trick", "Watch them run.")], effects=fx(RC, "trick")),
}, O[RC].get("marker"))

# ================================================================ SNIB ==
SN = "snib"
move = copy.deepcopy(O[SN]["nodes"]["move"])
NEW[SN] = convo(SN, O[SN]["entry"], {
    "first": node("Oi! OI! Surface-meat! No surface-meat past the pump! Foreman's orders! ...Snib is the foreman. Snib. What do you want? Quick. The pump does not pump itself. It does, actually. But quick.",
                  [keep(SN, "first", "Your pump is poisoning the stream.", "Your pump's poisoning the stream."),
                   keep(SN, "first", "Your blasting ember came off the Coyle wagons."),
                   keep(SN, "first", "Pump it into the old sinkhole instead."),
                   keep(SN, "first", "Grimtunnel sent me.", goto="lamp"),
                   keep(SN, "first", "How much to shut it off for a week?"),
                   keep(SN, "first", "Then I will shut it off myself.", "Then I'll shut it off myself."),
                   keep(SN, "first", "Leave.")]),
    "hub": node("You again. Pump is still pumping. Foreman is still foreman.",
                [keep(SN, "hub", "Your blasting ember came off the Coyle wagons."),
                 keep(SN, "hub", "Your pump is poisoning the stream.", "Your pump's poisoning the stream."),
                 keep(SN, "hub", "Pump it into the sinkhole instead."),
                 keep(SN, "first", "Grimtunnel sent me.", goto="lamp"),
                 keep(SN, "hub", "Then I will shut it off myself.", "Then I'll shut it off myself."),
                 keep(SN, "hub", "Leave.")]),
    "ember": copy.deepcopy(O[SN]["nodes"]["ember"]),
    "poison": node("Poison? It is slurry. Waste. Has to go somewhere. Boss says dig deeper, dig faster, the heart is hungry, the heart wants DOWN. Boss has a heart to feed and Snib has a pump to run. The wolves can drink somewhere else.",
                   [keep(SN, "poison", "Pump it into the sinkhole instead."), keep(SN, "poison", "How much to shut it off?"),
                    keep(SN, "poison", "Then I will shut it off myself.", "Then I'll shut it off myself."), keep(SN, "poison", "Leave.")],
                   effects=fx(SN, "poison")),
    "move": move,
    "lamp": node("That is the Boss's LAMP. The spare! Boss never lends the spare. Boss does not lend his SPIT. ...Snib did not see you. Snib did not see the lamp. Lads! The pipe! Turn the pipe! The Boss says!",
                 [ch("Good lad, Snib.", end=True)], effects=copy.deepcopy(move["effects"])),
    "bribe": copy.deepcopy(O[SN]["nodes"]["bribe"]),
    "bribed": copy.deepcopy(O[SN]["nodes"]["bribed"]),
}, O[SN].get("marker"))

# ======================================================== THE SURVIVOR ==
NEW["survivor"] = copy.deepcopy(O["survivor"])

# ================================================================ JORY ==
J = "jory"
NEW[J] = convo(J, [E("first", not_(met(J))), E("hub")], {
    "first": node("You're the one who opened the cage. I— thank you. Uncle Harlan hasn't stopped crying. It wasn't wolves, you know. A clerk at the gate said the road was shut and sent us down the forest track, and they were waiting.",
                  [ch("Rest, Jory.", end=True), ch("What was in the crates?", once="crates", goto="crates")], effects=fx(J, "first")),
    "hub": node("I'm all right. I keep saying that. Uncle keeps asking.",
                [ch("What was in the crates?", once="crates", goto="crates"), ch("Rest, Jory.", end=True)]),
    "crates": node("Salt. Cloth. Iron. And six we weren't to open, Uncle said, and not to take over ruts. I took them over every rut in Thornhollow. Nothing happened. ...What was in them?",
                   [ch("Rest, Jory.", end=True)]),
}, O[J].get("marker"))

# =========================================================== WAYFINDER ==
WF = "wayfinder"


def wf_menu():
    return [
        ch("Show me your maps.", action="maps"),
        ch("What are the oaths?", goto="oaths"),
        ch("What will I find out there?", goto="places"),
        ch("Who draws these?", once="drawn", goto="drawn"),
        ch("Who buys your notes?", show=flag(WF, "once:drawn"), once="notes", goto="notes"),
        ch("Another time.", end=True),
    ]


NEW[WF] = convo(WF, O[WF]["entry"], {
    "first": node("You've the look of someone who walks toward trouble on purpose. Good. I'm Ysolde Marrow, and I draw maps of the places the road forgets: woods that eat their own paths, barrows that open after dark, ravines the Kerchiefs think are theirs. Each one sworn under an oath. Each one ruled by something that won't want you there.",
                  wf_menu()),
    "hub": copy.deepcopy(O[WF]["nodes"]["hub"]) | {"choices": wf_menu()},
    "oaths": node(O[WF]["nodes"]["oaths"]["text"], [ch("Show me your maps.", action="maps"), back(), ch("Another time.", end=True)]),
    "places": node(O[WF]["nodes"]["places"]["text"], [ch("Show me your maps.", action="maps"), back(), ch("Another time.", end=True)]),
    "drawn": node("People like you. They walk in, and some of them walk out, and I buy what they remember before the drink takes it. The ones who don't walk out, I draw from where their light went out. You can see it from the road, if you know how to look.",
                  [ch("Show me your maps.", action="maps"), back(), ch("Another time.", end=True)]),
    "notes": node("Collectors. Scholars. A gentleman in the north who likes silver ink and doesn't haggle. I don't ask, and the maps get drawn. ...You come back more often than most, you know. I've noticed. So has he.",
                  [ch("Show me your maps.", action="maps"), back(), ch("Another time.", end=True)]),
}, O[WF].get("marker"))
NEW[WF]["nodes"]["hub"]["text"] = V((fact("arena.won", gte=1), "Back from the edges, {name}, and in one piece. The places you took are quieter for it. I've new ones."),
                                    "Maps, {name}. Places the road forgets. Pick one.")

# =============================================================== BOARD ==
NEW["board"] = copy.deepcopy(O["board"])


def run():
    assert set(NEW) == set(O), set(O) ^ set(NEW)
    out = {k: NEW[k] for k in O}  # keep the file's order
    save("dialogue.json", out)
    return out


if __name__ == "__main__":
    run()
    print("voices ok")

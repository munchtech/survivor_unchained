"""Act 1 writing pass: dialogue.json. Run from the worktree root on a clean
checkout of godot/data/content/dialogue.json."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from lib import *

d = load('dialogue.json')
T = Talks(d)

# ------------------------------------------------------------- shared tests

# "R." is somebody in red: the player has seen Kerchief work, or been told of them.
CTX_KERCHIEF = ANY(Q('caravan', 'wreck'), Q('caravan', 'ruts'), Q('caravan', 'roost_found'), Q('caravan', 'redcowl_met'),
                   Q('caravan', 'redcowl_wagons'), Q('caravan', 'roost_raided'), KN('hint.roost'))
# The night in question is the night the Coyle wagons went.
CTX_COYLE = ANY(Q('caravan', 'harlan_plea'), Q('caravan', 'guard_says'), Q('caravan', 'clerk_turned'), Q('caravan', 'wreck'),
                Q('caravan', 'redcowl_wagons'), Q('caravan', 'ledger_read'))
LEDGER_CTX = ALL(CTX_KERCHIEF, CTX_COYLE)
# The stream matters: the player has some reason to think the water is the trouble.
STREAM_CTX = ANY(KN('clue.green_stream'), KN('clue.sick_wolf'), KN('clue.analysis'), KN('root_cause'), KN('hint.stream'))
# Enough of the lamps to say it to her face: whose irons, and whose coin or money.
LAMPS_CTX = ALL(ANY(Q('lamps', 'irons'), Q('lamps', 'mark')), ANY(Q('lamps', 'coin'), Q('lamps', 'rook'), Q('lamps', 'notice')))
NELL_TRUTH = ANY(F('nell.told', eq='gone'), F('nell.told', eq='risen'))
CRATES_FREE = ALL(NOT(F('be.crates', exists=True)), NOT(HIST('burned_roost')))
PUMPING = ANY(NOT(F('dig.pump', exists=True)), F('dig.pump', eq='running'))

# =================================================================== ROOK

T.text('rook', 'rumours', [
    V("Nothing you don't know already, pet; you did half of it. Holloway's counting what's left, Harlan's counting what came back, "
      "and the Penhales say their dog won't go in the barn any more. Stands at the door and whines at the floor, and won't be told.",
      ALL(F('beasts.outcome', exists=True), F('caravan.survivors', exists=True))),
    V("Wenna says the stream's running clean. The wolves have gone quiet, and Holloway's sulking because there's nobody left to pay. "
      "Harlan's still asking after his boy, mind.", F('beasts.outcome', eq='cured')),
    V("No wolves on the road now. None. Brannoc's never seen so many pelts, and Maeca hasn't been in since. Make of that what you like. "
      "Harlan's still asking after his boy.", F('beasts.outcome', eq='slaughtered')),
    V("The wolves are settled, one way or another, and nobody's thanked anybody for it, which is how you know it's settled. "
      "Harlan's still asking after his boy, mind. And Jessop, the toll clerk, owes me for three rounds and hasn't been back to pay.",
      F('beasts.outcome', exists=True)),
    V("Jory Coyle's home and sleeping in my good room with the lamp lit, and Harlan's tried to pay me for it twice. The wolves are another matter: "
      "Holloway's paying for pelts, Maeca says they're sick, and the Penhale boy says they drink from the stream and fall down. Pick one.",
      F('caravan.survivors', eq='rescued')),
    V("Harlan's shut his shutters and won't open the door, not even to me. And the wolves are still at it: Holloway's paying for pelts, "
      "Maeca says they're sick. Don't ask me which. I've stopped asking.", F('caravan.survivors', eq='dead')),
    V("Wolves, mainly. Holloway's paying for pelts, Maeca says they're sick, Harlan says they ate his caravan, and the Coyle boy's still missing. "
      "And Jessop, the toll clerk, was buying rounds at the Flagon like he'd come into money, the night the wagons went. Pick a story."),
])
T.find('rook', 'rumours', 'toll clerk with money')  # the old question, replaced below
T.node('rook', 'rumours')['choices'] = [
    C('Jessop, the toll clerk?', show=NOT(F('caravan.survivors', exists=True)), goto='clerk'),
    T.node('rook', 'rumours')['choices'][1],
]

T.text('rook', 'clerk',
       "Clerks don't buy rounds. Jessop bought three, the night Coyle's wagons went missing, and kept telling the room he'd \"done somebody a favour\". "
       "Rav was there; Rav's always there. ...Jessop's not been in since. He still owes me for the third.")

T.text('rook', 'ford',
       "Not many, this last year. The ford's been bad since the winter. ...Vonnra pays me to tell her who comes up that road, and when. "
       "Don't look like that, pet; she pays everyone for something. I'd told her about you before you'd finished your stew.")
T.node('rook', 'ford2')['effects'] = [ENTRY('lamps', 'rook', 'active')]

# Rook hears Brannoc was told.
T.entry('rook', 'cb_told_brannoc', ALL(HIST('told_brannoc'), MET('rook'), NOT(FLAG('rook', 'cb:told_brannoc'))), before='say_calling')
T.add('rook', N('cb_told_brannoc',
                "You told Brannoc about his girl. (She wipes the same bit of counter for a while.) Good. Somebody had to, and it was never going to be me. "
                "...Sit down. You look like you want feeding, and I want something to do with my hands.",
                effects=[SETFLAG('rook', 'cb:told_brannoc'), REL('rook', quiet=True, affection=5)], next='hub'))

# ================================================================ HOLLOWAY

MENUS_H = ['first', 'hub', 'repaid', 'argued']
for nid in MENUS_H:
    c = T.find('holloway', nid, 'Pell Varrow paid the Kerchiefs')
    c['when'] = ALL(HAS('pell_ledger'), LEDGER_CTX)
T.insert('holloway', MENUS_H,
         C("I found this book in Pell Varrow's warehouse. Can you make sense of it?",
           show=ALL(HAS('pell_ledger'), NOT(LEDGER_CTX), NOT(Q('caravan', 'ledger_read'))), once='ledger_early', goto='ledger_early'),
         after='Pell Varrow paid the Kerchiefs')
T.insert('holloway', ['first', 'repaid', 'argued'],
         C("Your watch-post on the Low Ford road. There's a dead man at it.", when=KN('lore.warden'), once='post', goto='post'),
         before="That's all.")
T.insert('holloway', ['hub'],
         C("Your watch-post on the Low Ford road. There's a dead man at it.", when=KN('lore.warden'), once='post', goto='post'),
         before='What do you want, Captain?')
LETTER_NIGHT = ALL({"time": "night"}, {"day": {"gte": 3}})
T.insert('holloway', ['hub'],
         C("That letter. The silver seal.", show=LETTER_NIGHT, once='letter', goto='letter'),
         before='What do you want, Captain?')

hub = T.node('holloway', 'hub')
hub['text'].insert(2, V("(A letter lies open under his lamp, a silver seal broken on it. He turns it face down when you come in, and puts his cup on it.) What.",
                        LETTER_NIGHT))

T.add('holloway', N('ledger_early',
                    "(He reads it standing up. Then he sits down and reads it again.) Two payments, one night. Forty to \"R.\" Ten to Jessop, \"for the road\": "
                    "that's Vonnra's clerk at the toll. And that's the night Harlan Coyle's wagons went off the Old Road and didn't come back. "
                    "(He shuts it.) Don't tell me where you got it. If you tell me, I have to do something about it.",
                    effects=[ENTRY('caravan', 'ledger_read', 'active'), REL('holloway', respect=5, trust=-5)],
                    choices=[C("Who's \"R.\"?", goto='ledger_early2')]))
T.add('holloway', N('ledger_early2',
                    "Could be anyone. There's more thieves in this valley than letters to go round. Find me who \"R.\" is, and what Pell bought for forty, "
                    "and I'll put him in irons myself. Until then it's a book with numbers in, and Pell's got a man in Low Kiln who loves numbers. "
                    "...Keep it somewhere I can't see it.",
                    choices=[C("Something else.", goto='hub'), C("That's all.", end=True)]))

T.add('holloway', N('post',
                    "(He says nothing for long enough that you think he hasn't heard.) Grey beard, proud of it? Bad hip? ...Corran. He had that post before I had this one. "
                    "I wrote him down as a deserter in the spring. Him and his runner, Dannet. Dannet never came up the road, so I wrote him down too.",
                    effects=[ENTRY('lamps', 'book', 'active'), ENTRY('lamps', 'post'), SET({"holloway.post_told": True}), REL('holloway', respect=10, trust=5)],
                    choices=[C("His book says the lamps at the ford were lit again. Not by the Watch.", goto='post2'), C("Something else.", goto='hub')]))
T.add('holloway', N('post2',
                    "Not by us. We've not had oil for those lamps since my first winter, and nobody's asked me for any. (He writes something down, and crosses it out.) "
                    "So somebody had oil. And a reason. ...I'll send two men down with a cart. I owe Corran a hole in the ground, and an apology he can't hear.",
                    choices=[C("Something else.", goto='hub'), C("That's all.", end=True)]))
T.add('holloway', N('letter',
                    "Mine. From the north, about the north. (The cup doesn't move.) Read your own post, if anybody writes to you.",
                    effects=[SET({"holloway.letter_seen": True})],
                    choices=[C("Something else.", goto='hub'), C("That's all.", end=True)]))

T.text('holloway', 'expose', [
    V("Payments to \"R.\": Redcowl. And to Jessop, at Vonnra's toll. On the night. Pell Varrow, you careful, greedy little man. My lads'll have him in irons before dark. "
      "...And the strongbox you sold, we'll call that a fee for services. Once.", F('player.pardoned', eq=True)),
    V("Payments to \"R.\": Redcowl. And to Jessop, at Vonnra's toll. On the night. Pell Varrow, you careful, greedy little man. My lads'll have him in irons before dark. "
      "The Watch owes you, {name}. I don't say that lightly; I've not much to pay you with."),
])

# =================================================================== MAECA

T.insert('maeca', ['first', 'hub'],
         C("You know them, don't you. The Kerchiefs.",
           show=ANY(Q('caravan', 'roost_found'), Q('caravan', 'redcowl_met'), Q('caravan', 'redcowl_wagons')), once='kerchiefs', goto='kerchiefs'),
         before='Why "Barefoot"?')
T.add('maeca', N('kerchiefs',
                 "Some. (She drinks, and looks at the cup instead of you.) Fed some of them, once. Buried more. ...Ask me about wolves.",
                 effects=[SET({"maeca.kerchiefs": True})],
                 choices=[C("Something else.", goto='hub'), C("Goodbye.", end=True)]))

# =================================================================== WENNA

first = T.node('wenna', 'first')
first['text'][0]['text'] = first['text'][0]['text'].replace("catalog it", "catalogue it")

# ===================================================================== TAM

T.text('tam', 'farm',
       "Out past the Old Road, where the wood starts. Penhale's, that's us. Pa won't leave it. He says wolves is wolves and a farm's a farm. But these ones aren't right.")
T.insert('tam', ['again'], C("Anything else strange out at the farm?", once='tock', goto='tock'), before='Did your Pa ever find the goat?')
T.add('tam', N('tock',
               "The ground knocks. At night. Tock, and then tock, under the floor, like somebody wanting to come in, and Pa says it's moles, "
               "and I said moles don't knock, and he said go to sleep Tam, so I did, but it kept knocking.",
               effects=[SET({"tam.tock": True}), ENTRY('below', 'tock', 'active')],
               choices=[C("Something else.", goto='again'), C("Stay by the well, Tam.", end=True)]))

# ================================================================= BRANNOC

T.node('brannoc', 'irons')['effects'] = [ENTRY('lamps', 'irons', 'active')]
T.text('brannoc', 'irons', [
    V("(He looks at the two irons on the rack for a long time.) Twelve ordered. Ten went down to the ford, at night, square coin on the anvil. "
      "...Buyer'll want these two. Buyer can come and ask me for them.", NELL_TRUTH),
    V("Spares. Lamp-irons for the Low Ford. Twelve ordered last winter, ten collected. Collected at night; coin left on the anvil. Old coin, the square kind. "
      "Didn't ask who. ...Should've."),
])

MENUS_B = ['first', 'hub', 'cloak']
T.insert('brannoc', MENUS_B,
         C("This was in the Warden's fist at the Low Ford.", when=HAS('wardens_lampiron'), once='mark', goto='mark'),
         after='Those lamp-irons on the rack?')
T.insert('brannoc', ['hub'],
         C("Those last two irons.", show=F('nell.buried', eq=True), once='irons2', goto='irons_after'),
         before='Who taught you iron?')

T.add('brannoc', N('mark', [
    V("(He takes it. Turns it to the light. Puts his thumb under the socket, where the mark is.) Mine. (He holds it a long time.) ...Mine.", NELL_TRUTH),
    V("(He takes it. Turns it to the light. Puts his thumb under the socket.) Mine. Mark's under there. Last winter's work: twelve for the Low Ford, "
      "ten collected, at night, square coin on the anvil. (He gives it back.) Keep it. It's done what it was for."),
], effects=[ENTRY('lamps', 'irons', 'active'), ENTRY('lamps', 'mark'), SET({"brannoc.saw_iron": True})],
    choices=[C("Something else.", goto='hub'), C("Goodbye.", end=True)]))

T.add('brannoc', N('irons_after',
                   "(He puts his hand flat on the two irons.) Buyer'll be back for these. Buyer can come and ask me himself. Or herself. "
                   "(The hammer comes down.) I'll know the coin.",
                   effects=[SET({"brannoc.waits_buyer": True})],
                   choices=[C("Something else.", goto='hub'), C("Goodbye.", end=True)]))

# Nell. He asks on the second visit, any day after the first: the one thing he ever asks.
T.entry('brannoc', 'nell', ALL(MET('brannoc'), {"day": {"gte": 2}}, NOT({"time": "night"}), NOT(FLAG('brannoc', 'asked_nell'))), before='cb_killed_greymuzzle')
T.add('brannoc', N('nell',
                   "(He doesn't look up from the anvil, and he doesn't stop.) You came up the Low Ford road. ...Carter went south a fortnight back. Wat, with the grey mare. "
                   "Toll work. Said he'd be over the ford by dark. Girl with him. Twelve. Red hair. New boots. Going to her aunt at Low Kiln. "
                   "(The hammer stops.) Mine. Nell. ...You pass them?",
                   effects=[ENTRY('lamps', 'nell', 'active')],
                   choices=[
                       C("There was a wagon on its side, south of the ford. A girl had the reins.", goto='nell_ditch', effects=[SETFLAG('brannoc', 'asked_nell')]),
                       C("I passed nobody on that road.", goto='nell_lie',
                         effects=[SETFLAG('brannoc', 'asked_nell'), SET({"nell.told": "lie"}), LATER(2, 'nell.asking', SET({"nell.asking": True})),
                                  HISTORY('lied_brannoc', "told Brannoc they had passed nobody on the Low Ford road", ["nell", "lie"], 0, witnesses=["brannoc"])]),
                       C("I didn't look at the dead.", goto='nell_look',
                         effects=[SETFLAG('brannoc', 'asked_nell'), SET({"nell.told": "evaded"}), LATER(2, 'nell.asking', SET({"nell.asking": True}))]),
                   ]))
T.add('brannoc', N('nell_ditch', [
    V("(He puts the hammer down, and looks at the two irons still on the rack, and then he doesn't look at anything.) ...Had the reins. "
      "She'd want the reins. Always wanted the reins.", F('brannoc.saw_iron', eq=True)),
    V("(He puts the hammer down. You have never seen him put the hammer down.) ...Had the reins. (A long breath, through the nose.) "
      "She'd want the reins. Always wanted the reins."),
], choices=[
    C("She was gone before I came. The water took her.", goto='nell_gone',
      effects=[SET({"nell.told": "gone"}), REL('brannoc', trust=15, respect=5),
               HISTORY('told_brannoc', "told Brannoc his daughter drowned at the Low Ford", ["nell", "lamps"], 1,
                       reactions={"rook": {"affection": 10}, "chid": {"respect": 10}}, witnesses=["brannoc"])]),
    C("She'd got up with the others. I put her down.", goto='nell_risen',
      effects=[SET({"nell.told": "risen"}), REL('brannoc', trust=25, respect=15),
               HISTORY('told_brannoc', "told Brannoc his daughter drowned at the Low Ford", ["nell", "lamps"], 1,
                       reactions={"rook": {"affection": 10}, "chid": {"respect": 10}}, witnesses=["brannoc"])]),
]))
T.add('brannoc', N('nell_gone',
                   "Quick, then. Water's quick. (He picks the hammer up and holds it, and doesn't use it.) Forge is shut. Go on.",
                   choices=[C("I'm sorry, Brannoc.", end=True), C("(Leave him.)", end=True)]))
T.add('brannoc', N('nell_risen',
                   "(He looks at you then. Properly, for the first time.) Got up. (He says it the way he tests an edge: weighing it.) "
                   "Got up, and you put her down. ...Was it quick?",
                   choices=[C("It was quick.", goto='nell_quick'), C("It wasn't.", goto='nell_slow')]))
T.add('brannoc', N('nell_quick',
                   "(A long time.) ...Thank you. (The forge ticks as it cools.) Forge is shut. Go on.",
                   choices=[C("(Leave him.)", end=True)]))
T.add('brannoc', N('nell_slow',
                   "(He nods, once, as if you've told him a price.) Forge is shut.",
                   choices=[C("(Leave him.)", end=True)]))
T.add('brannoc', N('nell_lie',
                   "(The hammer comes down.) Low Kiln, then. Good. (And again.) Aunt'll feed her up. She's thin.",
                   choices=[C("Goodbye, Brannoc.", end=True)]))
T.add('brannoc', N('nell_look',
                   "Didn't look. (The hammer comes down.) No. ...Nobody looks.",
                   choices=[C("Goodbye, Brannoc.", end=True)]))

hub = T.node('brannoc', 'hub')
hub['text'].insert(1, V("(He works. He doesn't stop when you come in, and he doesn't send you away.) Steel or fur?", F('nell.buried', eq=True)))

# ================================================================== HARLAN

ROOST_UNTOLD = ALL(Q('caravan', 'roost_found'), NOT(F('caravan.survivors', exists=True)))
T.text('harlan', 'first', [
    V("You. Jory says it was you at the cage with the bar in your hands, and he's told it four times since breakfast, and it gets better every time. "
      "(He takes your hand in both of his.) Harlan Coyle, of the Coyle Company. Any other day I'd have said that first.", F('caravan.survivors', eq='rescued')),
    V("(The shutters are half closed, and he doesn't get up.) Harlan Coyle. You'll have heard. Everyone's heard. ...Buy something, or don't.",
      F('caravan.survivors', eq='dead')),
    V("That's my seal. That's— (He's round the counter before you can blink, hands out, and then he doesn't touch it.) Where did you get that? "
      "Where was it? Where's the boy that was driving it?", HAS('coyle_strongbox')),
    V("Harlan Coyle, of the Coyle Company: salt, iron and Morrow cloth. You've the Verge on your boots, friend; I can smell it from here. "
      "My wagons are out there somewhere. Three of them, and a boy called Jory driving the first. Tell me you've seen something.", Q('caravan', 'roost_found')),
    V("Harlan Coyle, of the Coyle Company: salt, iron and Morrow cloth, the best on the Old Road. You'll have seen my notice. Three wagons, and a boy called Jory "
      "driving the first. A week, near enough. He's never been a week late in his life. ...Forgive me. I say that to everyone.", F('caravan.days', gte=3)),
    V("Harlan Coyle, of the Coyle Company: salt, iron and Morrow cloth, the best on the Old Road. You'll have seen my notice. Three wagons, and a boy called Jory "
      "driving the first. Six days. He's never six days late. ...Forgive me. I say that to everyone.", F('caravan.days', gte=2)),
    V("Harlan Coyle, of the Coyle Company: salt, iron and Morrow cloth, the best on the Old Road. You'll have seen my notice. Three wagons, and a boy called Jory "
      "driving the first. Five days. He's never five days late. ...Forgive me. I say that to everyone.", F('caravan.days', gte=1)),
    V("Harlan Coyle, of the Coyle Company: salt, iron and Morrow cloth, the best on the Old Road. You came up the south road? Then you didn't pass three wagons "
      "and a boy called Jory. No. No, of course you didn't. Forgive me. Four days. He's never four days late."),
])
T.node('harlan', 'first')['effects'] = [
    IF(NOT(F('caravan.survivors', exists=True)), [ENTRY('caravan', 'harlan_plea', 'active'), ENTRY('beasts', 'harlan_view')]),
]

T.text('harlan', 'route', [
    V("The east road. The Old Road, through Thornhollow. They should've come through Vonnra's gate at dusk, a week ago now. Holloway had men on the road. "
      "Nobody saw them.", F('caravan.days', gte=3)),
    V("The east road. The Old Road, through Thornhollow. They should've come through Vonnra's gate at dusk, six days back. Holloway had men on the road. "
      "Nobody saw them.", F('caravan.days', gte=2)),
    V("The east road. The Old Road, through Thornhollow. They should've come through Vonnra's gate at dusk, five days back. Holloway had men on the road. "
      "Nobody saw them.", F('caravan.days', gte=1)),
    V("The east road. The Old Road, through Thornhollow. They should've come through Vonnra's gate at dusk, four days back. Holloway had men on the road. "
      "Nobody saw them."),
])

MENUS_HC = ['first', 'hub']
T.insert('harlan', MENUS_HC,
         C("I've seen your wagons. The Kerchiefs have them in a ravine off the Old Road, and three men in cages.", show=ROOST_UNTOLD, once='roost', goto='roost'),
         after='Which road were they on?')
for nid in MENUS_HC:
    c = T.find('harlan', nid, 'Pell Varrow paid the Kerchiefs')
    c['when'] = ALL(HAS('pell_ledger'), LEDGER_CTX)
T.insert('harlan', MENUS_HC,
         C("I found this book in Pell Varrow's warehouse. Do the dates mean anything to you?",
           show=ALL(HAS('pell_ledger'), NOT(LEDGER_CTX), NOT(Q('caravan', 'ledger_read'))), once='ledger_early', goto='ledger_early'),
         after='Pell Varrow paid the Kerchiefs')
T.insert('harlan', MENUS_HC,
         C("Your six crates are still in the Roost.", show=ALL(KN('clue.blasting_ember'), Q('caravan', 'roost_found'), CRATES_FREE),
           once='crates', goto='crates'),
         after='What were you carrying, besides salt and cloth?')

T.add('harlan', N('roost',
                  "(He sits down, which you haven't seen him do.) Three. In cages. (He's counting something on his fingers, and he stops.) Is one of them young? "
                  "Fair, freckled, a mouth on him that'll get him— (He stops that too.) Get him out. Whatever it costs. Whatever they want, I'll pay it twice.",
                  effects=[ENTRY('caravan', 'roost_told'), REL('harlan', trust=15, affection=10)],
                  choices=[C("Something else.", goto='hub'), C("Goodbye.", end=True)]))
T.add('harlan', N('ledger_early',
                  "(He reads, and his finger stops on a line.) That's the night. That's the night Jory's wagons went. Forty to \"R.\" Ten to Jessop: "
                  "that's Vonnra's clerk. \"For the road.\" (He looks up.) For what road? Who's \"R.\"? ...Find out who \"R.\" is, friend. Please. "
                  "Then take that to Holloway, not to me. If I knew, I'd do something I'd hang for.",
                  effects=[ENTRY('caravan', 'ledger_read', 'active')],
                  choices=[C("Something else.", goto='hub'), C("Goodbye.", end=True)]))
T.add('harlan', N('crates',
                  "(His face does what it does whenever anyone says those two letters.) ...Are they. With the bandit. (He's already reaching for paper.) "
                  "Thank you, friend. Leave that with me. Paid for is paid for.",
                  effects=[SET({"be.crates": "harlan"}), ENTRY('caravan', 'crates_harlan'), REL('harlan', trust=10),
                           HISTORY('crates_harlan', "told Harlan Coyle where his six crates of blasting ember were", ["caravan", "ember"], 0, witnesses=["harlan"])],
                  choices=[C("Something else.", goto='hub'), C("Goodbye.", end=True)]))

# Harlan, made to say what he sells.
T.insert('harlan', ['be'],
         C("The Dig's poisoning the stream with what you sell them.", when=KN('root_cause'), once='poisoned', goto='be_dig'),
         before='Something else.')
T.add('harlan', N('be_dig',
                  "(He takes a long time to answer.) I sell salt to people who salt things. I sell iron to people who hit things. I don't ask the salt what it's for, friend. "
                  "...Is there anything else? Only I've stock to count.",
                  effects=[SET({"harlan.told_dig": True}), REL('harlan', trust=-5, respect=5)],
                  choices=[C("Something else.", goto='hub'), C("Goodbye.", end=True)]))

T.text('harlan', 'jory_now', [
    V("He asked me what was in the crates. I told him salt. (He looks at his hands.) He didn't believe me. First time in his life. ...That's the worst of it, friend. "
      "He always did.", F('jory.knows_be', eq=True)),
    V("Sleeps with the lamp lit. Eats like a horse. Asked me last night what was in the crates. I told him salt. He believed me; he always does. "
      "...That's the worst of it, friend. He always does."),
])

# The box sold, the boy brought home: he pays for the boy anyway.
BOY_UNPAID = ALL(F('caravan.survivors', eq='rescued'), NOT(FLAG('harlan', 'once:jory')))
T.text('harlan', 'betrayed', [
    V("You brought him home. Then you sold my strongbox to a fence for the price of a good horse. (He counts a hundred onto the counter, coin by coin, "
      "and doesn't push it towards you.) For the boy. I said I would. Take it, and get away from my stall.", BOY_UNPAID),
    V("You. You found it, and you kept it. Get away from my stall."),
])
T.node('harlan', 'betrayed')['choices'] = [
    C("Take it.", show=BOY_UNPAID, end=True, effects=[{"gold": 100}, SETFLAG('harlan', 'once:jory')]),
    C("Leave it on the counter.", show=BOY_UNPAID, end=True, effects=[SETFLAG('harlan', 'once:jory'), REL('harlan', quiet=True, respect=10)]),
    C("...", show=NOT(BOY_UNPAID), end=True),
]

T.entry('harlan', 'cb_jory_knows', ALL(F('jory.knows_be', eq=True), MET('harlan'), NOT(FLAG('harlan', 'cb:jory_knows'))), before='say_calling')
T.add('harlan', N('cb_jory_knows',
                  "(He doesn't say good morning.) He knows. You told him. ...I'd have told him myself. One day. When it didn't matter any more.",
                  effects=[SETFLAG('harlan', 'cb:jory_knows'), REL('harlan', affection=-10, respect=5)],
                  choices=[C("It mattered now.", goto='hub'), C("He asked me.", goto='hub')]))

# ==================================================================== JORY

T.text('jory', 'first',
       "You're the one who opened the cage. I— thank you. Uncle Harlan hasn't stopped crying. It wasn't wolves, you know. A toll clerk met us on the road, "
       "in Vonnra's violet, and said the Old Road was shut at the Waystation and sent us down the forest track. And they were waiting.")
JORY_UNDECIDED = ALL(NOT(F('jory.knows_be', exists=True)), NOT(F('jory.lied_to', exists=True)))
for nid in ['first', 'hub']:
    c = T.find('jory', nid, 'What was in the crates?')
    c.pop('once', None)
    c['show'] = JORY_UNDECIDED
    # keep key order: text, show, goto
    c2 = {"text": c['text'], "show": c['show'], "goto": c['goto']}
    cs = T.node('jory', nid)['choices']
    cs[cs.index(c)] = c2
T.text('jory', 'hub', [
    V("I'm all right. (He isn't.) Uncle's counting crates that aren't there.", F('jory.knows_be', eq=True)),
    V("I'm all right. I keep saying that. Uncle keeps asking."),
])
T.node('jory', 'crates')['choices'] = [
    C("Blasting ember, Jory. For the Dig, under the hill.", when=KN('clue.blasting_ember'), goto='truth'),
    C("Salt, Jory. And cloth.", goto='salt', effects=[SET({"jory.lied_to": True}), ENTRY('caravan', 'jory_salt')]),
    C("Rest, Jory.", end=True),
]
T.add('jory', N('truth',
                "(He laughs, once, as if you've told him a joke he didn't get.) Every rut in Thornhollow. I took them over every rut. (He stops laughing.) "
                "...Uncle knew. Didn't he. He told me salt.",
                effects=[SET({"jory.knows_be": True}), ENTRY('caravan', 'jory_told'),
                         HISTORY('told_jory', "told Jory Coyle what his uncle's six crates were for", ["caravan", "ember"], 0, witnesses=["jory"])],
                choices=[C("He knew.", goto='truth_knew', effects=[SET({"jory.told_knew": True})]), C("Ask him yourself.", goto='truth_ask')]))
T.add('jory', N('truth_knew',
                "(He nods. He keeps nodding.) Right. Right. ...Thank you. I think. I'll know when I've stopped feeling sick.",
                choices=[C("Rest, Jory.", end=True)]))
T.add('jory', N('truth_ask',
                "I will. (He doesn't move.) I will.",
                choices=[C("Rest, Jory.", end=True)]))
T.add('jory', N('salt',
                "(He nods, and it goes out of his face at once, the way it goes out of a child's.) Salt. Right. ...Thanks.",
                choices=[C("Rest, Jory.", end=True)]))

# ==================================================================== PELL

T.text('pell', 'confront', [
    V("Where did you— the clerk. Of course. (He studies your face, and something in his own unclenches.) ...You don't know what you're holding, do you? "
      "How refreshing. Let's be civilised. There's gold in this for you, a good deal of gold, if that book were to go in the fire.", NOT(LEDGER_CTX)),
    V("Where did you— the clerk. Of course. Let's be civilised. There's gold in this for you, a good deal of gold, if that book were to go in the fire."),
])
T.text('pell', 't_pell',
       "My sister kept the books in Ashford. I came up to collect them, after. There wasn't an Ashford to collect them from. (He straightens a pen that was straight.) "
       "She wrote to me the week before. The garrison's boots had come in short, and somebody had signed for them full. She thought it was funny. "
       "She had a dreadful sense of humour. ...So I count. Somebody ought to know what things cost.")

# ===================================================================== RAV

T.text('rav', 'clerk', [
    V("A toll clerk bought the room a round the night the caravan vanished. Clerks don't buy rounds. Jessop, his name is; Vonnra's. He'd \"done somebody a favour\": "
      "told Coyle's teamsters the road was shut and sent them down the forest track. Between us, he'd also a key he shouldn't have. Pell's warehouse. "
      "Showed it me like a boy with a frog. ...Not seen him since. He wasn't the type to buy rounds, either.", KN('underworld')),
    V("A toll clerk bought the room a round the night the caravan vanished. Clerks don't buy rounds. Jessop, his name is; Vonnra's. He'd \"done somebody a favour\": "
      "told Coyle's teamsters the road was shut and sent them down the forest track. Draw your own lines, pal. ...Not seen him since, now I think of it."),
])
T.text('rav', 'cb_tricked_redcowl',
       "You told Redcowl the Watch was coming, and he RAN. I've waited my whole life to see that man run. Sit. This one's on me, and so's the next.")
T.text('rav', 'cb_killed_redcowl',
       "(He doesn't look up.) You killed him. ...Dunstan. That was his name, before the hat. Our mother's idea; he hated it. (He drinks.) "
       "No. He'd have said it was the job. It was always the job, with him. Get out of my light for a bit, pal. Come back tomorrow. I'll be a doctor again tomorrow.")

# ================================================================= REDCOWL

COYLE_NAMED = ANY(Q('caravan', 'harlan_plea'), Q('caravan', 'guard_says'), Q('caravan', 'clerk_turned'), Q('caravan', 'wreck'),
                  Q('caravan', 'redcowl_wagons'), Q('caravan', 'ledger_read'), Q('caravan', 'roost_told'))
T.insert('redcowl', ['first', 'hub'],
         C("Whose wagons are those?", show=NOT(COYLE_NAMED), once='wagons', goto='wagons'),
         before="Let the teamsters go.")
T.insert('redcowl', ['first', 'hub'],
         C("Those six crates under your canvas. Know what's in them?",
           show=ALL(KN('clue.blasting_ember'), CRATES_FREE), once='crates', goto='crates'),
         before='Who are all these people?')
T.insert('redcowl', ['hub'],
         C("Who told you when the Coyle wagons were coming?", show=Q('caravan', 'redcowl_met'), once='birds', goto='birds'),
         before='Why keep them in cages?')
T.insert('redcowl', ['hub'],
         C("Ashford's levy. That's who you are.",
           show=ALL(FLAG('redcowl', 'once:who'), ANY(FLAG('maeca', 'once:barefoot'), F('maeca.kerchiefs', eq=True))), once='ashford', goto='ashford'),
         before='Nothing.')

T.add('redcowl', N('wagons',
                   "Ha! Salvage, is what they are. Some merchant up at the Waystation painted his name on every board of them, so the road'd know who to thank. Coyle. "
                   "The road knows now. ...You'll be wanting them. Everyone does, once they've seen them.",
                   effects=[ENTRY('caravan', 'redcowl_wagons', 'active')],
                   choices=[C("I've come for them.", goto='goods'),
                            C("Let the teamsters go.", when=NOT(F('caravan.survivors', exists=True)), goto='prisoners'),
                            C("Nothing.", end=True)]))
T.add('redcowl', N('crates',
                   "Salvage. Heavy salvage. My lads were using them for seats, till one of them dropped one and we all stood very still and listened to it think about it.",
                   choices=[C("Blasting ember. For the Dig: the lamp-men digging under the hill.", goto='crates_dig'),
                            C("Nothing you need to worry about.", goto='hub')]))
T.add('redcowl', N('crates_dig',
                   "(He doesn't laugh.) The hill. (He looks north-east, past the ravine wall, at nothing you can see.) The one that's been knocking at night. "
                   "...How deep are they going?",
                   choices=[C("Deep enough to shake the ground.", goto='crates_keep'), C("Deeper than anyone should.", goto='crates_keep')]))
T.add('redcowl', N('crates_keep',
                   "Then nobody's having them. Not the hole in the hill. Not Holloway. Not your merchant, and not the soft-handed little man that sold them twice. "
                   "They stay with me. (A laugh, but not the big one.) Guarding crates. My mother'd laugh herself sick.",
                   effects=[SET({"be.crates": "redcowl"}), ENTRY('caravan', 'crates_redcowl'), REL('redcowl', trust=20, respect=10),
                            HISTORY('crates_redcowl', "told Redcowl what was in the Coyle crates, and who they were for", ["kerchief", "ember"], 0, witnesses=["redcowl"])],
                   choices=[C("Give me one. For the Dig's pump.", show=PUMPING, goto='crates_charge'),
                            C("Keep them dry.", end=True)]))
T.add('redcowl', N('crates_charge',
                   "(He looks at you a long while. Then he whistles, and a lad brings one over, walking like he's carrying a sleeping baby.) Take it. "
                   "Put it where it'll do the most harm to the right people. And {name}: run.",
                   effects=[{"give": "blasting_ember"}, SET({"redcowl.gave_charge": True}), ENTRY('beasts', 'redcowl_charge', 'active')],
                   choices=[C("Leave.", end=True)]))
T.add('redcowl', N('birds', [
    V("Ha! A little bird. Sings for its drink, and sews a fair seam when it's sober. (The laugh stops.) Birds don't have names, lass. Not in my camp.", {"sex": "female"}),
    V("Ha! A little bird. Sings for its drink, and sews a fair seam when it's sober. (The laugh stops.) Birds don't have names, lad. Not in my camp."),
], effects=[SET({"redcowl.birds": True})],
    choices=[C("About the Coyle wagons.", when=NOT(F('redcowl', eq='bargained')), goto='goods'), C("Nothing.", end=True)]))
T.add('redcowl', N('ashford',
                   "(The laugh goes out of him like a lamp.) Don't. (Quiet.) You get to say that once in my camp. You've said it.",
                   effects=[SET({"redcowl.ashford_said": True}), REL('redcowl', respect=15, trust=5)],
                   choices=[C("About the Coyle wagons.", when=NOT(F('redcowl', eq='bargained')), goto='goods'), C("I'll go.", end=True)]))

# Pell, sold out twice: who tells Redcowl where he sleeps.
T.node('redcowl', 'pell')['choices'] = [
    C("He sleeps over his warehouse. In the loft.", goto='pell_given',
      effects=[SET({"pell.fate": "taken"}), ENTRY('caravan', 'pell_given'),
               HISTORY('gave_pell', "told Redcowl where Pell Varrow sleeps", ["kerchief", "caravan"], 0, witnesses=["redcowl"])]),
    C("Find him yourself.", goto='pell_hunt', effects=[SET({"pell.fate": "ran"}), ENTRY('caravan', 'pell_hunted')]),
]
T.add('redcowl', N('pell_given',
                   "Ha! Somebody who knows where the rats sleep. (He's already shouting for boots.) Go home, {name}. Stay off the square tonight.",
                   choices=[C("Leave.", end=True)]))
T.add('redcowl', N('pell_hunt',
                   "I'll find him. Men like Varrow leave a smell of ink wherever they go.",
                   choices=[C("Leave.", end=True)]))

# ==================================================================== SNIB

for nid in ['first', 'hub']:
    for frag in ["Your pump's poisoning the stream.", 'sinkhole', "Grimtunnel sent me", 'How much to shut it off', "Then I'll shut it off myself."]:
        try:
            c = T.find('snib', nid, frag)
        except KeyError:
            continue
        c['show'] = STREAM_CTX
        # house order: text, show, when, ...
        keys = ['text', 'show', 'when', 'locked', 'badge', 'effects', 'once', 'goto', 'action', 'end']
        cc = {k: c[k] for k in keys if k in c}
        cs = T.node('snib', nid)['choices']
        cs[cs.index(c)] = cc
T.insert('snib', ['first', 'hub'], C("What are you pumping?", show=NOT(STREAM_CTX), once='what', goto='what'), before='Leave.')
T.add('snib', N('what',
                "Slurry! What is left when the stones are cooked. Pipe takes it down to the stream, stream takes it AWAY. Stream is very obliging. "
                "...Snib does not know where the stream goes after. Snib has never needed to KNOW.",
                effects=[{"learn": "clue.pipe"}, ENTRY('beasts', 'snib_slurry', 'active')],
                choices=[C("Your blasting ember came off the Coyle wagons.", when=KN('clue.blasting_ember'), once='ember', goto='ember'),
                         C("Leave.", end=True)]))

# =================================================================== SELLA

T.text('sella', 'hear', [
    V("Men talk after. God, do they talk. There's a toll clerk, Jessop, been flush all month, paying me in new silver with the Varrow mark stamped on it. "
      "Last time he was pleased with himself: said he'd \"sent some wagons down the wrong road\" and got paid twice for it. Then he fell asleep on my arm. Charming. "
      "...Not been up my stairs since, and he was a Tuesday man. You could set a clock by Jessop.", QS('caravan', 'active')),
    V("That the wolves are quiet, and Holloway's drinking more than he's paying. That Pell sleeps with his ledgers. That Harlan cries when he's had three. Same as ever.",
      F('beasts.outcome', exists=True)),
    V("That the wolves are sick and Holloway's a prick, and that nobody who goes up the north road comes back to tell me about it. Same as ever."),
])
T.insert('sella', ['morning'], C("(Tell her where you come from.)", once='past', goto='past'), before='Sleep a little longer first.')
T.insert('sella', ['morning'], C("Did I talk in my sleep?", once='sleeptalk', goto='sleeptalk'), before='Sleep a little longer first.')
T.add('sella', N('past', [
    V("(You tell her. She listens properly, chin on her fist, the way she does everything.) A hunter. Out of these woods, with a bow too big for you, I'll bet, "
      "and mud to the knees. ...I'd not have guessed. I'd have guessed, but not that.", {"bg": "hunter"}),
    V("(You tell her. She listens properly, chin on her fist, the way she does everything.) A cloister rat. Four years in a cellar reading dead men's letters, "
      "and you walked out with their lens in your pocket. ...Good for you, love.", {"bg": "scholar"}),
    V("(You tell her. She listens properly, chin on her fist, the way she does everything.) Worse company than the Kerchiefs, and you walked away from it. "
      "(She laughs, low.) Takes one to know one. Don't tell Rook.", {"bg": "outcast"}),
    V("(You tell her. She listens properly, chin on her fist, the way she does everything.) Chapel lamps, with nobody to see them but you, and you lit them anyway. "
      "(She's quiet a moment.) That's the saddest thing anyone's told me up here, love, and they tell me some sad things."),
], effects=[SET({"sella.heard_past": True}), REL('sella', quiet=True, affection=4)],
    choices=[C("Until next time.", end=True)]))
T.add('sella', N('sleeptalk',
                 "You said a name. Over and over, like you'd got hold of it in the dark and didn't want to let go. (She shrugs one shoulder.) Didn't catch it. "
                 "I don't think you did either.",
                 effects=[SET({"sella.sleeptalk": True})],
                 choices=[C("Until next time.", end=True)]))

# ================================================================== VONNRA

T.node('vonnra', 'coin')['effects'] = [ENTRY('lamps', 'coin', 'active')]
JESSOP_KNOWN = ANY(Q('caravan', 'clerk_turned'), Q('caravan', 'sella_clerk'), Q('caravan', 'ledger_read'))
T.insert('vonnra', ['ledger_read', 'hub'],
         C("Your clerk. Jessop. Where is he?", show=JESSOP_KNOWN, once='jessop', goto='jessop'),
         after='Did Coyle\'s caravan pay your toll?')
T.add('vonnra', N('jessop',
                  "Gone south. On the toll's business. (She turns a page of the ledger that does not need turning.) Clerks go south, traveller. "
                  "It is the direction they fall in.",
                  effects=[SET({"vonnra.asked_jessop": True})],
                  choices=[C("Something else...", goto='hub'), C("Goodbye.", end=True)]))

hub = T.node('vonnra', 'hub')
hub['text'].insert(0, V("{name}. Your chapter is written. The next one is not. ...Payment, always.",
                        ALL(F('chapter.done', eq=True), F('vonnra.accused', eq=True))))

f = T.node('vonnra', 'f_caravan')
f['text'].insert(0, V("I see a boy in a wagon, and his uncle sitting up beside him all night. The boy is not asleep. He knows what he carried now, "
                      "and he is deciding what that makes his uncle.",
                      ALL(F('caravan.survivors', eq='rescued'), F('jory.knows_be', eq=True))))
f['next'] = 'f_ember'
T.add('vonnra', N('f_ember', [
    V("And six crates in a bandit's tent, guarded now by a man who knows what they are for. He will not sell them. He is saving them. I wonder for what.",
      F('be.crates', eq='redcowl')),
    V("And six crates going home to a man who knows where they go next. You told him where to find what was his. That is honest. It is not the same thing as good.",
      F('be.crates', eq='harlan')),
    V("And six crates that went up with the Roost. You will have heard it from the wall. Everyone did.", HIST('burned_roost')),
    V("And six crates still waiting in a ravine to go where they were paid to go. Someone will deliver them. Someone always does.", KN('clue.blasting_ember')),
    V("And six crates nobody opened, marked with two letters, waiting in a ravine to go where they were paid to go. Someone will deliver them. Someone always does."),
], next='f_pell'))

T.node('vonnra', 'f_pell')['text'].insert(0, V(
    "And Pell Varrow, in a cage that was built for someone else. You know which one. He is still counting. It is all he has left to do.",
    F('pell.fate', eq='taken')))

T.node('vonnra', 'f_self')['next'] = 'f_past'
PALM = " (She is not looking at your palm.)"
T.add('vonnra', N('f_past', [
    V("And before the ford: a child following tracks through these woods, with a bow too big for them." + PALM, ALL(F('sella.heard_past', eq=True), {"bg": "hunter"})),
    V("And before the ford: four years in a cloister cellar among dead men's letters, and a lens you were not meant to leave with." + PALM,
      ALL(F('sella.heard_past', eq=True), {"bg": "scholar"})),
    V("And before the ford: worse company than the Kerchiefs, and the trick of walking away from it." + PALM, ALL(F('sella.heard_past', eq=True), {"bg": "outcast"})),
    V("And before the ford: chapel lamps that nobody came to see, and you, lighting them anyway." + PALM, ALL(F('sella.heard_past', eq=True), {"bg": "devout"})),
    V("Of before the ford, I see very little. The water took it, or you left it on the far bank. Most do."),
], next='f_below'))

T.text('vonnra', 'f_below', [
    V("Last. Under the Verge, something is turning over in its sleep, and under a farm past the Old Road, something is knocking to be let in. "
      "The little lamp-people are digging down to it with the Warden's heart in their arms, and they think it will be grateful. And the door in the hillside...",
      F('tam.tock', eq=True)),
    V("Last. Under the Verge, something is turning over in its sleep. The little lamp-people are digging down to it with the Warden's heart in their arms, "
      "and they think it will be grateful. And the door in the hillside..."),
])
T.insert('vonnra', ['f_below'], C("You lit the lamps at the Low Ford.", show=LAMPS_CTX, goto='f_accuse'), after='What about the door?')
T.add('vonnra', N('f_accuse',
                  "(For the first time she looks at your face and not at your hand. It goes on long enough that the lamp gutters.) ...Sit down, {name}. "
                  "I have not finished reading.",
                  effects=[SET({"vonnra.accused": True}), ENTRY('lamps', 'accused'), REL('vonnra', respect=25, trust=-15),
                           HISTORY('accused_vonnra', "told Vonnra Ash-of-Morrow she lit the lamps at the Low Ford", ["lamps"], 0, witnesses=["vonnra"])],
                  next='f_door'))
T.text('vonnra', 'f_door', [
    V("The door in the hillside is listening, as I am. That is all I see for free, {name}. The rest you will walk into yourself, and you will, "
      "because you are the kind that does.", F('vonnra.accused', eq=True)),
    V("The door is not for sale. That is all I see for free. The rest you will walk into yourself, and you will, because you are the kind that does."),
])
# She never answers yes or no (VOICES.md); she refuses by naming a price that does not exist.
T.text('vonnra', 'vault', "Not for any price. That is the only thing I will ever say to you without charging for it.")

# ================================================================== KEEGAN

T.node('keegan', 'warden')['effects'].extend([ENTRY('lamps', 'book', 'active'), ENTRY('lamps', 'keegan')])
T.entry('keegan', 'say_risen', ALL(MET('keegan'), {"trait": "risen_once"}, NOT(FLAG('keegan', 'say:risen'))), before='say_calling')
T.add('keegan', N('say_risen',
                  "I am told you were carried into the shrine under a sheet. (She looks at you very carefully, from your boots upwards, and back down.) "
                  "You look well. You look extremely well. ...I've got to go and read something. I— I have to go and read something. Good day.",
                  effects=[SETFLAG('keegan', 'say:risen'), SET({"keegan.saw_risen": True})],
                  choices=[C("Good day, Dame Keegan.", end=True)]))

# ==================================================================== CHID

T.node('chid', 'warden')['effects'].append(ENTRY('lamps', 'book', 'active'))
T.insert('chid', ['first', 'hub', 'lit'],
         C("There was a note in Ashe's trunk: \"Keep the lights lit. — C.\"", when=KN('lore.firstlamp'), once='note', goto='note'),
         before='How long have you kept the shrine?')
T.add('chid', N('note',
                "Was there! (He's suddenly very interested in a candle.) A C. Lovely. Lots of people start with C. Cuthbert. Cressida. There was a Cormac, once, "
                "who— (He stops.) It's a lovely old hand, whoever it was. Nobody makes a C like that any more. Nobody's made a C like that in... well. Ages.",
                effects=[SET({"chid.note_asked": True})],
                choices=[C("Something else.", goto='hub'), C("Goodbye.", end=True)]))
T.entry('chid', 'cb_nell', ALL(F('nell.buried', eq=True), MET('chid'), NOT(FLAG('chid', 'cb:nell'))), before='say_calling')
T.add('chid', N('cb_nell',
                "We buried Nell behind the shrine, next to old Ashe. Brannoc made the marker himself. Iron. Of course, iron. "
                "(He is quiet, which he never is.) She was very light. ...Sit down a minute. Not there. There.",
                effects=[SETFLAG('chid', 'cb:nell')], next='hub'))

# =============================================================== WAYFINDER

T.insert('wayfinder', ['hub'], C("What do you write in your margins?", once='margin', goto='margin'), before='Do you ever go in yourself?')
AFTER_MARGIN = [C("Show me your maps.", action='maps'), C("Something else.", goto='hub')]
T.add('wayfinder', N('margin',
                     "Who came back, from where, how long they lasted, what they carried out. Name first; I'm a tidy woman. (She dips her pen.) "
                     "Speaking of which. How do I put you down?",
                     choices=[C("As {name}.", goto='margin_name', effects=[SET({"wayfinder.name": "given"})]),
                              C("Put me down as nobody.", goto='margin_nobody', effects=[SET({"wayfinder.name": "nobody"})]),
                              C("Make one up.", goto='margin_lark', effects=[SET({"wayfinder.name": "false"})])]))
T.add('wayfinder', N('margin_name', "{name}. (She writes it, blots it, and blows on it.) There. Now you're in the margins for good.", choices=AFTER_MARGIN))
T.add('wayfinder', N('margin_nobody', "Nobody. (She writes it without blinking.) You'd be surprised how often Nobody comes back. More than most.",
                     choices=AFTER_MARGIN))
T.add('wayfinder', N('margin_lark', "(She looks at you over the pen for a moment, then writes.) Lark. You look like a Lark. Larks get up early and make a great deal of noise about it.",
                     choices=AFTER_MARGIN))

# =================================================================== BOARD

r = T.node('board', 'read')
r['effects'].append(IF(ANY(KN('lore.warden'), Q('lamps', 'irons')), [ENTRY('lamps', 'notice', 'active')]))
# Before the bitterroot notice: the town's standing notices sit together.
i = next(k for k, v in enumerate(r['text']) if v['text'].startswith('WANTED: bitterroot'))
r['text'].insert(i, {"add": True, "text": "CARTERS WANTED for the south road. Toll work, paid DOUBLE for a quick crossing. Apply at the Toll Tower. — V. "
                                          "(Underneath, in pencil: \"quick means after dark\". Under that, in another hand: \"Wat went. Wat's not back.\")"})

# Redcowl says lad or lass, as the survivor is.
CAGES = ("Because a man in a cage is worth something to somebody, and a man in a ditch is worth nothing to anybody. "
         "I've buried enough worth-nothings for one life, {}. ...And I feed them. Ask them. I feed them before I feed my own.")
T.text('redcowl', 'cages', [V(CAGES.format('lass'), {"sex": "female"}), V(CAGES.format('lad'))])

save('dialogue.json', d)
print('dialogue ok')

"""Act 1 writing pass: the journal, the daily rules, the town's talk, what is
on people's minds, item lore and barks. Run from the worktree root on a clean
checkout of the content files."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from lib import *

# ================================================================== quests

q = load('quests.json')

cv = q['caravan']['entries']
# Found in any order: each line stands on its own.
cv['roost_found'] = ("Redcowl's Roost, the Kerchief camp in the ravine: the Coyle wagons' cargo under canvas (the name is painted on every board), "
                     "and three prisoners in cages, with teamsters' hands.")
cv['pell_ledger'] = ("Pell Varrow's ledger, from his own warehouse. Two payments on one night: forty to \"R.\", and ten to someone called Jessop, \"for the road\". "
                     "In the margin, in the same small hand: \"tell Holloway where they camp, after.\"")
cv['clerks_key'] = "Jessop, the toll clerk, had a key to Pell Varrow's warehouse. He should not have had it."
cv['clerk_turned'] = ("Jessop, Vonnra's toll clerk, met Coyle's teamsters on the road, told them the Old Road was shut, and sent them down the forest track. "
                      "He bought the Flagon a round that night. Nobody has seen him since.")
cv['guard_says'] = "The Watch swears the Old Road was never closed that day: Holloway had men on it from dawn to dusk."
cv['sella_clerk'] = ("Sella, upstairs at the Last Lamp: Jessop the toll clerk paid her in new silver with the Varrow mark on it, and bragged in bed that he had "
                     "\"sent some wagons down the wrong road\". He has not been up her stairs since.")


def add_after(d, after, key, text):
    items = list(d.items())
    i = next(k for k, (kk, _) in enumerate(items) if kk == after) + 1
    items.insert(i, (key, text))
    d.clear()
    d.update(items)


add_after(cv, 'roost_found', 'roost_told', "You told Harlan Coyle where his wagons are: the Roost, in the ravine, and three men in cages. He would pay anything to have them out.")
add_after(cv, 'roost_told', 'redcowl_wagons', "Redcowl calls the wagons in his camp salvage. A merchant at the Waystation called Coyle painted his name on every board of them.")
add_after(cv, 'pell_ledger', 'ledger_read', "Pell's ledger, read by someone who knew the date: forty to \"R.\" and ten to Jessop, the toll clerk, \"for the road\", "
                                            "both on the night the Coyle wagons vanished. Who is \"R.\", and what did forty buy?")
add_after(cv, 'blasting_ember', 'crates_redcowl', "You told Redcowl what is in the six crates marked \"B.E.\", and who they were bound for. He says nobody is having them now: "
                                                  "not the Dig, not the Watch, not Harlan.")
add_after(cv, 'crates_redcowl', 'crates_harlan', "You told Harlan Coyle where his six crates are. He thanked you, and reached for paper. Paid for is paid for.")
add_after(cv, 'survivors_freed', 'jory_told', "You told Jory what he was carrying: blasting ember, for the Dig. He asked whether his uncle knew.")
add_after(cv, 'jory_told', 'jory_salt', "Jory asked what was in the crates. You said salt.")
add_after(cv, 'pell_joined', 'pell_given', "You told Redcowl where Pell Varrow sleeps.")
add_after(cv, 'pell_given', 'pell_hunted', "Redcowl has gone looking for Pell Varrow. You did not tell him where to look.")

bs = q['beasts']['entries']
add_after(bs, 'clue.lampling_tracks', 'snib_slurry', "At the Dig, a lampling who calls himself the foreman pumps the waste of cooked ember down a pipe into the stream. "
                                                     "\"Stream is very obliging.\"")
add_after(bs, 'dig_sold', 'redcowl_charge', "Redcowl gave you one charge out of the Coyle crates, for the Dig's pump. \"Put it where it'll do the most harm to the right people.\"")

vt = q['vault']['entries']
vt['bootprints'] = ("Fresh bootprints in the mud at the door, going in, not coming out. Trodden into one of them, a copper toll-token from the Waystation, "
                    "stamped with three roads. Someone got inside.")

bl = q['below']['entries']
bl['tock'] = "Tam says the ground under his family's farm knocks at night, like somebody asking to be let in. His Pa says it is moles."

lamps = {
    "id": "lamps",
    "name": "The Lamps at the Low Ford",
    "mystery": True,
    "summary": "Somebody relit the lamps at the Low Ford, and the Warden woke and drowned whoever crossed after dark. The Watch says it was not them.",
    "entries": {
        "book": "The dead watchman's belt-book, at the post on the Low Ford road: \"Lamps at the Low Ford lit again, and not by us.\" "
                "\"Sent Dannet for the captain. Dannet not back.\"",
        "keegan": "Dame Keegan: the lamps were never meant to keep the dark out. They kept the Warden asleep. \"If somebody lit them again, somebody wanted it awake.\"",
        "post": "Captain Holloway knew the dead watchman: Corran, written down as a deserter in the spring, and his runner Dannet with him. "
                "The Watch has had no oil for the ford lamps in years.",
        "irons": "Brannoc forged twelve new lamp-irons for the Low Ford last winter. Ten were collected at night, paid for in square old-empire coin left on the anvil. "
                 "Two are still on his rack.",
        "mark": "The lamp-iron you took off the Warden has Brannoc's mark under the socket. It is one of the ten.",
        "rook": "Mother Rook is paid to say who comes up the Low Ford road, and when. She was paid double for you.",
        "coin": "Vonnra wears an old-empire coin on a cord at her throat: square, never spent. She says it will buy something that cannot be bought twice.",
        "notice": "On the notice board: carters wanted for the south road, toll work, paid double for a quick crossing. Apply at the Toll Tower. "
                  "Someone has written underneath that quick means after dark.",
        "nell": "The girl holding the reins in the ditch on the Low Ford road, in new boots, was Nell, Brannoc's daughter: twelve, going south to her aunt "
                "with Wat the carter, on toll work.",
        "accused": "You told Vonnra she lit the lamps at the Low Ford. She did not say no. She said your name, and went on reading.",
    },
}
q['lamps'] = lamps
save('quests.json', q)

# =================================================================== rules

r = load('rules.json')
rules = r['rules']
# The blood rule was written down twice.
seen = set()
rules[:] = [x for x in rules if not (x['id'] == 'wolf.blood.washes' and x['id'] in seen) and not seen.add(x['id'])]


def rule(rid, when, report, effect=None, once=True):
    x = {"id": rid}
    if once:
        x["once"] = True
    x["when"] = when
    x["effect"] = effect if effect is not None else []
    if report:
        x["report"] = report
    return x


new_rules = [
    rule('nell.burial', ANY(F('nell.told', eq='gone'), F('nell.told', eq='risen')),
         "Brannoc banked his forge at noon yesterday and took a handcart down the Low Ford road, with a blanket and a spade. He was back before the gate shut, "
         "with something under his apron in the cart, and Chid walked out past the guards to meet him. They buried her at first light behind the shrine, "
         "next to the old captain. Nobody was asked to come, and half the town did.",
         effect=SET({"nell.buried": True})),
    rule('nell.asking', F('nell.asking', eq=True),
         "Brannoc stopped a pedlar off the south road at the gate yesterday, and asked him something. The pedlar shook his head. Brannoc asked the next one too."),
    rule('jory.words', F('jory.knows_be', eq=True),
         "Jory Coyle and his uncle had words in the yard before it was light. Jory did the shouting. Harlan didn't say anything at all, and then he opened the shop as usual."),
    rule('pell.taken', F('pell.fate', eq='taken'),
         "Pell Varrow's door stood open at first light, the lock not forced. His bed had been slept in. There was a red thread caught on the hinge, "
         "and a cart went out of the east gate before cockcrow. Vonnra's lamp was lit in the toll tower all night; nobody has asked her what went through."),
    rule('pell.ran', F('pell.fate', eq='ran'),
         "Pell Varrow left before dawn on a fast horse, with two satchels and none of his furniture. Three men in red came over the wall an hour after, "
         "kicked his door in, and found his ledgers gone with him."),
    rule('crates.harlan', F('be.crates', eq='harlan'),
         "Two of Harlan's teamsters took an empty wagon out of the east gate yesterday afternoon, with the Coyle purse, and came back after dark "
         "with it full and covered. They wouldn't say from where. Harlan unloaded it himself."),
    rule('holloway.corran', F('holloway.post_told', eq=True),
         "Two of the Watch went down the Low Ford road yesterday with a handcart and a spade, and came back at dusk with the cart covered. "
         "Holloway met them at the gate and walked beside it to the Watch's corner of the yard."),
]
# After the caravan's own reports, before the chapter's note: the morning reads in story order.
i = next(k for k, x in enumerate(rules) if x['id'] == 'chapter.ready')
rules[i:i] = new_rules
# When the chapter closes, the six crates go wherever nobody stopped them going,
# so Act 2 reads one fact (STORY_BIBLE.md, Act 2 beat 1): burned with the Roost;
# to the Watch, if the Roost fell and nobody claimed them; otherwise sold on to
# the Dig, by Redcowl or picked up by the lamplings from an empty camp.
i = next(k for k, x in enumerate(rules) if x['id'] == 'chapter.ready') + 1
rules.insert(i, rule('crates.settle', ALL(F('chapter.done', eq=True), NOT(F('be.crates', exists=True))), None,
                     effect=IF(HIST('burned_roost'), [SET({"be.crates": "burned"})],
                               [IF(ANY(F('redcowl', eq='dead'), F('roost.cleared', eq=True)), [SET({"be.crates": "watch"})], [SET({"be.crates": "dig"})])])))
save('rules.json', r)

# ==================================================================== folk

fk = load('folk.json')
lines = fk['lines']


def line(text, when=None, night=None, child=None, watch=None):
    x = {"text": text}
    if when is not None:
        x["when"] = when
    if night is not None:
        x["night"] = night
    if child is not None:
        x["child"] = child
    if watch is not None:
        x["watch"] = watch
    return x


for l in lines:
    if l['text'] == "Chid rang the bell twice this morning. Nobody knows why.":
        # The shrine bell rule says the bell rang for the first time anyone can remember.
        l['text'] = "Chid rang the bell twice this morning. Nobody's told him once does it."
        l['when'] = F('shrine.lit', eq=True)
    elif l['text'] == "The Flagon's ale is mostly water. The water's mostly ale.":
        l['text'] = "The Flagon's ale is half water. The water's half ale."
    elif l['text'] == "Pell's diggers moved their pipe. Pell, doing a kindness. Hm.":
        l['text'] = "Pell's diggers moved their pipe. Pell Varrow, doing a kindness. Check your purse."

lines.extend([
    line("Brannoc's girl went south with Wat's cart a fortnight back. Quietest forge in the valley since, and that's saying something.",
         ALL(NOT(F('nell.told', exists=True)), {"day": {"lte": 4}})),
    line("They buried Brannoc's girl behind the shrine. Chid sang. Chid can't sing. Nobody minded.", F('nell.buried', eq=True)),
    line("Brannoc's stopping carters off the south road, asking after a red-haired girl. Nobody's had the heart to say they've not seen her.",
         F('nell.asking', eq=True)),
    line("Jessop from the toll owes me four coppers and a ladder. Gone south, they say. Took neither.", {"day": {"gte": 2}}),
    line("Penhales' dog won't go in the barn. Stands at the door and whines at the floor.", F('tremor.felt', eq=True)),
    line("A Kerchief bought a sack of oats at the market and PAID for it. In coin. My husband says it's the end of the world.", F('be.crates', eq='redcowl')),
    line("Watch brought old Corran home from the ford post. Wrote him down a deserter, they did. Deserted to where, I ask you.", F('holloway.post_told', eq=True)),
    line("Jory Coyle's stopped calling his uncle Uncle. Calls him Mister Coyle in the shop, in front of customers.", F('jory.knows_be', eq=True)),
    line("They say a cart went out of the east gate the night Pell vanished, and Vonnra let it through without the toll. Vonnra. Without the toll.",
         F('pell.fate', eq='taken')),
    line("Pell Varrow's gone south on a horse he hadn't paid for. Course he hadn't.", F('pell.fate', eq='ran')),
    line("Captain's had a letter with a silver seal. Hasn't said a word since. Not that he says many.", {"day": {"gte": 3}}, watch=True),
])
save('folk.json', fk)

# ================================================================ concerns

cn = load('concerns.json')


def concern(text, when=None):
    x = {"text": text}
    if when is not None:
        x["when"] = when
    return x


def put(npc, c, before_text=None, at=None):
    lst = cn[npc]
    if at is not None:
        lst.insert(at, c)
        return
    i = next(k for k, x in enumerate(lst) if x['text'] == before_text)
    lst.insert(i, c)


cn['brannoc'][0:0] = [
    concern("Buried his daughter behind the shrine. Keeps his forge lit later than he used to, and will not sell the two lamp-irons left on his rack.",
            F('nell.buried', eq=True)),
    concern("Waiting for word from Low Kiln that his girl got there.", ANY(F('nell.told', eq='lie'), F('nell.told', eq='evaded'))),
]
put('harlan', concern("Jory knows what was in the crates. They speak in the shop, and nowhere else.", F('jory.knows_be', eq=True)),
    before_text="Has Jory back. Keeps finding reasons to touch his shoulder.")
cn['jory'].insert(0, concern("Knows what he was carrying now, and who it was for. Has not decided what that makes his uncle.", F('jory.knows_be', eq=True)))
put('pell', concern("Gone from his bed in the night. His door was not forced.", F('pell.fate', eq='taken')),
    before_text="Gone. His warehouse is empty and his debts are not.")
put('redcowl', concern("Sits on six crates of blasting ember he means nobody to have.", F('be.crates', eq='redcowl')),
    before_text="Would rather talk than bleed. Says so, anyway.")
cn['vonnra'].insert(0, concern("Has not answered what you said to her about the lamps. Has started calling you by your name.", F('vonnra.accused', eq=True)))
cn['rav'].insert(0, concern("Drinks to a man he will not name again, every night, at the same hour.", HIST('killed_redcowl')))
cn['keegan'].insert(0, concern("Has been rereading chapter four of the handbook. Will not say why.", F('keegan.saw_risen', eq=True)))
put('holloway', concern("Has brought Corran home from the Low Ford post, and crossed out a word in his book.", F('holloway.post_told', eq=True)),
    before_text="Wants the wolves dealt with before the Watch has to bury anyone else.")
put('tam', concern("Says the ground under the farm knocks at night. Nobody believes him, again.", F('tam.tock', eq=True)),
    before_text="Was right about the stream, and has told everyone.")
save('concerns.json', cn)

# =================================================================== items

it = load('items.json')
items = it['items']
items['coyle_strongbox']['description'] = "Heavy, locked, stamped with the Coyle Company seal. There is a Coyle Trading Post in the Waystation."
items['coyle_strongbox']['lore'] = "Someone has tried the lock with a knife, and given up, and tried again."
items['pell_ledger']['description'] = "Pell Varrow's own book. Two payments on one night: forty to \"R.\", and ten to Jessop, \"for the road\"."
items['pell_ledger']['lore'] = "Small, tidy figures. In the margin of the last page, in the same hand: \"tell Holloway where they camp, after.\""
items['clerks_key']['description'] = "A key to Pell Varrow's warehouse, which Jessop the toll clerk should not have had."
items['wardens_lampiron']['lore'] = ("The iron cage of the lamp the Ford-Warden carried. Under the socket, cut clean and new, a smith's mark: a hammer struck "
                                     "through a B. Whatever burned in it went down a hole in Grimtunnel's arms. The cage still remembers the light.")
for k, v in items.items():
    for f in ('description', 'lore'):
        if isinstance(v.get(f), str) and 'mostly pictures' in v[f]:
            v[f] = v[f].replace('mostly pictures', 'nearly all pictures')
save('items.json', it)

# =================================================================== shops

sh = load('shops.json')
# Pell sells blasting ember to someone who knows what it is for, not to strangers:
# on day one it would answer the manifest's "B.E." before anyone asked.
for l in sh['pell']['lines']:
    if l['id'] == 'blasting_ember':
        l['when'] = ANY(KN('root_cause'), KN('clue.blasting_ember'))
save('shops.json', sh)

# ==================================================================== npcs

np_ = load('npcs.json')
np_['npcs']['brannoc']['nightBarks'].append("Two on the rack. Leave them.")
np_['outsiders']['jory']['barks'].append("There was a fourth cage. Was.")
save('npcs.json', np_)
print('world ok')

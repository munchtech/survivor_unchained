"""The cinematics' lines, and the data the scripts call for. Run from the
worktree root on the content as committed after the Act 1 pass."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from lib import *

d = load('dialogue.json')
T = Talks(d)
CONT = [C("(Continue.)", end=True)]


def chain(cid, lines):
    """A cinematic's lines as a conversation: one node per line, chained, the
    last ending on (Continue.)."""
    assert cid not in d, cid
    nodes = {}
    for i, (nid, speaker, text, effects) in enumerate(lines):
        last = i == len(lines) - 1
        n = N(nid, text, effects=effects, speaker=speaker,
              choices=CONT if last else None, next=None if last else lines[i + 1][0])
        nodes[nid] = n
    d[cid] = {"npc": cid, "entry": [{"node": lines[0][0]}], "nodes": nodes}


def L(nid, speaker, text, effects=None):
    return (nid, speaker, text, effects)


# C01
chain('cin_drowned_fire', [
    L('bedroll', 'narrator', "Your bedroll has not been slept in."),
    L('prints', 'narrator', "Prints in the frost, your own. They come up from the river. None go down to it."),
    L('frost', 'narrator', "Past the firelight, the frost is breaking."),
])
# C02
chain('cin_none_cross', [
    L('call', 'ford_warden', "(sung, under the water) Lamps are lit... stay where they reach..."),
    L('lie_down', 'ford_warden', "Lie down."),
    L('none', 'ford_warden', "NONE. CROSS. AFTER DARK."),
])
# C03 (its world changes stay in Prologue.cs, applied at the hand-back, as now).
chain('cin_heart_goes_down', [
    L('morning', 'ford_warden', "Is it morning?"),
    L('nobodys', 'grimtunnel', "Ooh, still lit! Nobody's, is it? Nobody's!"),
    L('downstairs', 'grimtunnel', "...You smell like downstairs."),
    L('grateful', 'grimtunnel', "Finders keepers, surface-m— (a sniff) ...Downstairs'll be ever so grateful."),
])
# C04
chain('cin_first_light', [
    L('back', 'narrator', "The sun clears the trees, and the ember goes back into the ground."),
    L('face', 'narrator', "You try to call up your mother's face, and find it is not quite where you left it."),
    L('baking', 'narrator', "Somewhere up the street, someone is baking."),
    L('dawn', 'guard', "Dawn arrivals. We don't get many that live."),
])
# C06
chain('cin_forty_one_mouths', [
    L('them_first', 'kerchief_woman', "Them first."),
])
# C08
chain('cin_iron_marker', [
    L('verse1', 'chid', "(sung) Lie down, lie down, the lamps are tended, / and all the dark is kept; / the morning lies a little under, / and it will wake you where you slept."),
    L('verse2', 'chid', "(sung) Lie down, lie down, the road is ended, / your toll is paid and kept; / the dark is but the day not risen, / and it will wake you where you slept."),
])
# C11
chain('cin_raid_on_the_roost', [
    L('bairns', 'redcowl', [
        V("Ha! HA. At night, lass. With my bairns asleep behind me. ...Mind where you swing.", {"sex": "female"}),
        V("Ha! HA. At night, lad. With my bairns asleep behind me. ...Mind where you swing."),
    ]),
    L('last', 'redcowl', [
        V("...Ashford. (a laugh) There. Now we've both said it.", F('redcowl.ashford_said', eq=True)),
        V("Tell the saw-bones... the leg held."),
    ], effects=[IF(F('redcowl.ashford_said', eq=True), [SET({"redcowl.last_words": "ashford"})], [SET({"redcowl.last_words": "leg"})])]),
])
# C12
DIG_STOPPED = ANY(F('dig.pump', eq='broken'), F('dig.pump', eq='blown'), F('dig.pump', eq='moved'))
chain('cin_dig_boils_over', [
    L('pump', 'grimtunnel', [
        V("Surface-meat! You broke my PUMP. ...Doesn't matter. Downstairs doesn't mind. Downstairs is PATIENT.", DIG_STOPPED),
        V("Surface-meat! Killing my lads, are we? ...Doesn't matter. Downstairs doesn't mind. Downstairs is PATIENT."),
    ]),
    L('quiet', 'grimtunnel', "I told it about you! It went ever so QUIET!"),
])
# C13 (both variants of each are one recording: the Latin; the variants are the subtitles)
READER = ANY(KN('arcana'), {"hasTag": "scholar_lens"})
chain('cin_behind_the_door', [
    L('nondum', 'barrow_lord', [V("Nondum. (Not yet.)", READER), V("Nondum.")]),
    L('redi', 'barrow_lord', [V("Redi. (Go back.)", READER), V("Redi.")]),
])

# ------------------------------------------------ Greymuzzle smells her (C05)
SHOW_REST = ("He turns and walks into the Hollow, and you follow. The sick ones' eyes are milky; their gums are black. One of them tries to stand "
             "when it sees you, and cannot. Greymuzzle looks east, toward the stream, then back at you, and waits.")
SNIFF = "He comes close enough to smell your hand, then your face, and his lip lifts off his teeth, and goes down again. "
T.text('greymuzzle', 'show', [
    V(SNIFF + "Then your collar, for longer; and his tail moves, once. " + SHOW_REST, F('maeca.lover', eq=True)),
    V(SNIFF + SHOW_REST),
])

# ---------------------------------------------------- the fortune (C09)
REST = " No charge, this once. I have been waiting to see how it came out."
T.text('vonnra', 'fortune', [
    V("Sit. Give me your hand. No, the other one: the one you burn with." + REST, {"archetype": "arcanist"}),
    V("Sit. Give me your hand. No, the other one: the one you draw with." + REST, {"archetype": "stalker"}),
    V("Sit. Give me your hand. No, the other one: the one you hold the blade with." + REST),
])
AFTER_DARK = ANY({"time": "night"}, {"time": "dusk"})
for nid, n in d['vonnra']['nodes'].items():
    for c in n.get('choices') or []:
        if c.get('goto') == 'fortune':
            c['when'] = ALL(F('chapter.ready', eq=True), AFTER_DARK)
            c['locked'] = "She reads only after dark"
            keys = ['text', 'show', 'when', 'locked', 'badge', 'effects', 'once', 'goto', 'action', 'end']
            cc = {k: c[k] for k in keys if k in c}
            n['choices'][n['choices'].index(c)] = cc

# ------------------------------------------- Redcowl's camp as C06 shows it
rc_first = T.node('redcowl', 'first')
rc_first['text'] = [v for v in rc_first['text'] if not (isinstance(v.get('when'), dict) and v['when'].get('sex') == 'female')]
CAGES = ("Because a man in a cage is worth something to somebody, and a man in a ditch is worth nothing to anybody. "
         "I've buried enough worth-nothings for one life, {}. ...Ask them if they're hungry.")
T.text('redcowl', 'cages', [V(CAGES.format('lass'), {"sex": "female"}), V(CAGES.format('lad'))])

# ------------------------------------------------- Rav hears the leg held (C11)
rav = T.node('rav', 'cb_killed_redcowl')
rav['choices'] = [
    C("He said to tell you: the leg held.", show=F('redcowl.last_words', eq='leg'), goto='leg_held'),
    C("...", end=True),
]
T.add('rav', N('leg_held',
               "(He puts the cup down, very carefully, as if it were full.) ...Did he. (A long time.) Course it held. I'm a good doctor. "
               "...Go on, pal. Come back tomorrow.",
               choices=[C("...", end=True)]))
save('dialogue.json', d)

# ---------------------------------------------------------------- speakers
np_ = load('npcs.json')
sp = np_['speakers']
for k, name, title, glyph in [
    ('ford_warden', "The Ford-Warden", "Keeper of the Low Crossing", "skull"),
    ('grimtunnel', "Grimtunnel", "Boss of the Dig", "relic"),
    ('guard', "Watchman", "The Waystation Watch", "shield"),
    ('kerchief_woman', "Kerchief", "Of the Roost", "flame"),
    ('barrow_lord', "The Barrow Lord", "Of the Seventh Legion", "skull"),
    ('cin_drowned_fire', "The Drowned Fire", "Cinematic", "flame"),
    ('cin_none_cross', "None Cross After Dark", "Cinematic", "skull"),
    ('cin_heart_goes_down', "The Heart Goes Down", "Cinematic", "heart"),
    ('cin_first_light', "First Light", "Cinematic", "sun"),
    ('cin_forty_one_mouths', "Forty-One Mouths", "Cinematic", "flame"),
    ('cin_iron_marker', "The Iron Marker", "Cinematic", "moon"),
    ('cin_raid_on_the_roost', "Raid on the Roost", "Cinematic", "axe"),
    ('cin_dig_boils_over', "The Dig Boils Over", "Cinematic", "relic"),
    ('cin_behind_the_door', "Behind the Sealed Door", "Cinematic", "skull"),
]:
    assert k not in sp, k
    sp[k] = {"name": name, "title": title, "glyph": glyph}
for g in np_['guards']:
    if g['line'] == "Dawn arrivals. We do not get many that live.":
        g['line'] = "Dawn arrivals. We don't get many that live."
save('npcs.json', np_)

# ------------------------------------------------------------------- rules
r = load('rules.json')
for x in r['rules']:
    if x['id'] == 'nell.burial':
        # Said so the survivor can go (C08): the burial is this morning.
        x['report'] = ("Brannoc banked his forge at noon yesterday and took a handcart down the Low Ford road, with a blanket and a spade. He was back before "
                       "the gate shut, with something under his apron in the cart, and Chid walked out past the guards to meet him. They are burying her this "
                       "morning, behind the shrine, next to the old captain. Nobody has been asked to come.")
    if x['id'] == 'chapter.ready':
        x['report'] = "A note under your door, in violet ink: \"Come up to the roof after dark, and have your fortune read. No charge, this once. — V.\""
save('rules.json', r)

fk = load('folk.json')
for l in fk['lines']:
    if l['text'].startswith("They buried Brannoc's girl behind the shrine."):
        l['text'] = "They buried Brannoc's girl behind the shrine this morning. Chid sang. Chid can't sing. Nobody minded."
save('folk.json', fk)
it = load('items.json')
it['items']['wardens_lampiron']['lore'] = ("The iron cage of the lamp the Ford-Warden carried. Under the socket, cut clean and new, a smith's mark: "
                                           "a ring with a hammer across it. Whatever burned in it went down a hole in Grimtunnel's arms. The cage still remembers the light.")
save('items.json', it)
print('cinematics ok')

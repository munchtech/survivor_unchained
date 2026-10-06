"""Round four: data. Run from the worktree root."""
import json, os

P = os.path.join('godot', 'data', 'content', 'dialogue.json')
d = json.load(open(P, encoding='utf-8'))


def node(c, n):
    return d[c]['nodes'][n]


def rep_all(c, n, a, b, expect=None):
    nd = node(c, n)
    t = nd['text']
    hits = 0
    if isinstance(t, str):
        assert a in t, (c, n, a)
        nd['text'] = t.replace(a, b)
        hits = 1
    else:
        for v in t:
            if a in v['text']:
                v['text'] = v['text'].replace(a, b)
                hits += 1
    assert hits and (expect is None or hits == expect), (c, n, a, hits)


# The fortune interrupted: the town's ember lamps dip, the braziers do not.
rep_all('vonnra', 'f_below',
        "The flame lies over toward the hill. Down in the town every dog starts at once.",
        "The flame lies over toward the hill. Down in the town every lamp dips at once, and comes back; the braziers on the wall do not.",
        expect=2)
# Sella.
rep_all('sella', 'free_bolt', "it goes home with a sound like a full stop.",
        "it goes home with a sound like the last coin put down on a counter.")
rep_all('sella', 'morning', "Go on, the day's wasting, and somebody out there needs killing.",
        "Go on, the day's wasting, and somebody out there owes you money, or the other way round.")
rep_all('sella', 'say_calling', "You're warm. Not in a nice way. Are you on fire? You're a little bit on fire.",
        "Your hands are warm. Not in a nice way. Are you on fire? Your hands are a little bit on fire.")
# The blue room's first description, only on the first paid night.
sr = node('sella', 'stairs_room')
MOTHER = ("The blue room is blue because the lamp glass is, and everything in it takes the colour: the quilt, the jug, "
          "the bath, her. She tests the water with her elbow like somebody's mother, and then tips your chin up with one "
          "finger like nobody's mother at all. ")
again = []
for v in sr['text']:
    assert v['text'].startswith(MOTHER), v['text'][:60]
    rest = v['text'][len(MOTHER):]
    w = v.get('when')
    cond = {"fact": "sella.nights", "gte": 1}
    again.append({"when": {"all": [w, cond]} if w else cond,
                  "text": "The blue room again: the quilt, the jug, the bath, her, all of it blue. " + rest})
sr['text'] = again + sr['text']
# Rav feels the cold (it is night; a doctor would).
rep_all('rav', 'back_room_look',
        "He's quiet a moment.) There's nothing wrong with you, pal. (He frowns at your wrist, then lets it go.) ...That's the worrying part.",
        "He's quiet a moment.) You're cold, pal. Cold as a cellar step. (He frowns at your wrist, then lets it go.) ...There's nothing wrong with you. That's the worrying part.")
with open(P, 'w', encoding='utf-8', newline='\r\n') as h:
    h.write(json.dumps(d, indent=1, ensure_ascii=False) + '\n')

# The burial's morning report: what C14 shows when he goes alone.
R = os.path.join('godot', 'data', 'content', 'rules.json')
s = open(R, encoding='utf-8', newline='').read()
old = ("Brannoc banked his forge at noon yesterday and took a handcart down the Low Ford road, with a blanket and a spade. "
       "He was back before the gate shut, with something under his apron in the cart, and Chid walked out past the guards to meet him. "
       "They are burying her this morning")
new = ("Brannoc banked his forge at dusk yesterday and went down the Low Ford road alone, with a lantern and a blanket. "
       "He came back up it at sunrise with the blanket in his arms, and Chid walked out past the guards to meet him, and walked beside him up the street. "
       "They are burying her this morning")
assert s.count(old) == 1
s = s.replace(old, new)
open(R, 'w', encoding='utf-8', newline='').write(s)
print('ok')

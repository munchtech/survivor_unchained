"""Round-three fixes to the merged romance data. Run from the worktree root."""
import json, os

P = os.path.join('godot', 'data', 'content', 'dialogue.json')
d = json.load(open(P, encoding='utf-8'))
RISEN = {"trait": "risen_once"}
NOT_FELT = {"not": {"fact": "sella.felt_cold", "eq": True}}
BATH = {"npcFlag": {"npc": "sella", "key": "say:cold_bath", "eq": True}}


def node(c, n):
    return d[c]['nodes'][n]


def swap_cond(x, old, new):
    """Replace every occurrence of the condition `old` in x (in place)."""
    if isinstance(x, dict):
        for k, v in list(x.items()):
            if v == old:
                x[k] = new
            else:
                swap_cond(v, old, new)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            if v == old:
                x[i] = new
            else:
                swap_cond(v, old, new)


def set_text(c, n, idx, old_part, new_text):
    t = node(c, n)['text']
    cur = t if idx is None else t[idx]['text']
    assert old_part in cur, (c, n, old_part)
    if idx is None:
        node(c, n)['text'] = new_text
    else:
        t[idx]['text'] = new_text


def rep_text(c, n, idx, a, b):
    t = node(c, n)['text']
    cur = t if idx is None else t[idx]['text']
    assert a in cur, (c, n, a)
    cur = cur.replace(a, b)
    if idx is None:
        node(c, n)['text'] = cur
    else:
        t[idx]['text'] = cur


# --- Sella: every survivor is cold at night (canon), so the signs are timed by
# her nights, not by a death in Act 1.
# The bath, from the second paid night.
sr = node('sella', 'stairs_rules')
swap_cond(sr, RISEN, {"fact": "sella.nights", "gte": 1})
rep_text('sella', 'stairs_rules', 0,
         "She doesn't make a joke of it. She keeps her hands where they are until you aren't.)",
         "She doesn't make a joke of it. She keeps her hands where they are for a long time, as if that would help.)")
# The tender night: after she has felt the cold in the bath.
swap_cond(node('sella', 'night'), RISEN, BATH)
# The morning she says it: the third, if she has not said it on a quiet night.
mo = node('sella', 'morning')
mo['text'][0]['when'] = {"all": [{"fact": "sella.nights", "gte": 3}, NOT_FELT]}
for ch in mo['choices']:
    swap_cond(ch, RISEN, {"all": [{"fact": "sella.nights", "gte": 3}, NOT_FELT]})
set_text('sella', 'morning', 0, "You ran hot all night",
         "(She's sitting on the edge of the bed, frowning, with her palm flat on your breastbone.) You were cold as the river all night, love. Like sleeping next to a stone. And now look at you: warm as toast. ...Rook's got a word for that. It's not a nice word. Get up and eat something.")
# A night paid for only to sleep: she lies awake beside you, and knows.
rm = node('sella', 'rest_morning')
rm['text'][0]['when'] = NOT_FELT
for ch in rm['choices']:
    swap_cond(ch, RISEN, NOT_FELT)
set_text('sella', 'rest_morning', 0, "You ran hot all night",
         "(She's sitting on the edge of the bed with her hand flat on your chest.) You were cold as the river all night. Like lying next to a stone. And now look at you: warm as toast. ...Fifteen gold to lie awake next to a stone. Best money I ever made. Don't tell anyone.")
# The arcanist's hands burn; the rest of them is the river's.
rep_text('sella', 'stairs_room', 2,
         "\"You're warmer than the water. You know that? You're warmer than the water.\"",
         "\"Your hands are hot and the rest of you's a cellar floor. Pick one, love.\"")
# Rook's door: the valley's one priest is Chid; a Watchman makes the same joke.
rep_text('sella', 'door', None, "Once for a priest, and I'll not say which.",
         "Once for one of the Watch, and I'll not say which.")

# --- Maeca
rep_text('maeca', 'blind_walk', 0, "the bitch with the torn ear", "the bitch with the white foot")
rep_text('maeca', 'blind_dark', 0,
         "she puts her feet against your legs, and you flinch: they're cold as stones in a stream. She starts to take them back.",
         "she puts her feet against your legs, and flinches: you're colder than they are. She starts to take them back.")
rep_text('maeca', 'blind2_feet', None,
         "She lies very still, the way she lay still when the Pack called, and doesn't say anything, and after a long time her feet are warm. (Into the dark, very low:) \"Nobody's held those.\"",
         "She lies very still, the way she lay still when the Pack called, and doesn't say anything for a long time. (Into the dark, very low:) \"Your hands are colder than my feet.\" (A pause.) \"Hold them anyway. ...Nobody's held those.\"")
rep_text('maeca', 'blind3_morning', None,
         "Your heart's slow. Slow as a bear's in January. It was going like a hare's last night.",
         "Your heart's going like a hare's. (She doesn't lift her head.) All night it was a bear's in January. I counted between.")
# She watched the kneeling from the ridge (C05).
rep_text('maeca', 'cb_knelt', None,
         "You went into the Hollow with nothing on your hands and knelt to him. (She looks at your knees, which are still muddy.) He let you.",
         "You went into the Hollow with nothing on your hands and knelt to him. I was on the ridge. (She looks at your knees.) He let you.")

# --- Keegan
rep_text('keegan', 'supper_wends', None,
         "I taught them chiasmus. \"Ask not what the Vigil can do for you.\" They did not, and it did not. ...That was a joke.",
         "I taught them chiasmus. \"The Vigil keeps the gate, and the gate keeps the Vigil.\" It has kept neither. ...That was a joke.")
rep_text('keegan', 'supper_hand', None,
         "...That was anaphora. Doing the same thing twice, for emphasis. Goodnight.",
         "...That was epizeuxis. The same thing, twice, at once, for emphasis. Goodnight.")

# --- Vonnra: the fortune quotes the past only while Sella was still selling it.
fp = node('vonnra', 'f_past')
n = 0
for v in fp['text']:
    s = json.dumps(v.get('when'))
    if 'sella.heard_past' in s:
        v['when'] = json.loads(s.replace('sella.heard_past', 'sella.past_sold'))
        n += 1
assert n == 4, n
assert 'sella.past_sold' in json.dumps(node('sella', 'past')), 'sella.past must set past_sold'

with open(P, 'w', encoding='utf-8', newline='\r\n') as h:
    h.write(json.dumps(d, indent=1, ensure_ascii=False) + '\n')
print('ok')

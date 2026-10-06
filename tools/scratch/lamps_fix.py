"""Oil and ember in the shipped text, and the fortune interrupted. Run from
the worktree root."""
import json, os


def edit(path, a, b, count=1):
    s = open(path, encoding='utf-8', newline='').read()
    assert s.count(a) == count, (path, a[:70], s.count(a))
    s = s.replace(a, b)
    open(path, 'w', encoding='utf-8', newline='').write(s)


# --- dialogue.json
P = os.path.join('godot', 'data', 'content', 'dialogue.json')
d = json.load(open(P, encoding='utf-8'))
kw = d['keegan']['nodes']['warden']
old = "...Who told you that? The Vigil kept those lamps before the Watch did. Before the Watch was the Watch. The lamps were never to keep the dark out. They were to keep the Warden asleep. If somebody lit them again, somebody wanted it awake. Do not repeat that. I am probationary."
assert kw['text'] == old, kw['text']
kw['text'] = ("...Who told you that? The Vigil kept those lamps before the Watch did. Before the Watch was the Watch. "
              "Oil. The lamps at the ford were to burn oil, and nothing else; it is in the handbook, with a drawing. "
              "Oil keeps it sleeping. Ember wakes it. If somebody lit them with ember, somebody wanted it awake. "
              "Do not repeat that. I am probationary.")
# The fortune interrupted (docs/cinematics/c09_fortune.md, shot 11).
fb = d['vonnra']['nodes']['f_below']
n = 0
for v in fb['text']:
    assert v['text'].endswith('And the door in the hillside...'), v['text'][-40:]
    v['text'] += (" (The roof shivers under the table, and the glass of her lamp rings in its frame. The flame lies over"
                  " toward the hill. Down in the town every dog starts at once. She looks east, into the dark, and does"
                  " not finish.)")
    n += 1
assert n == 2
with open(P, 'w', encoding='utf-8', newline='\r\n') as h:
    h.write(json.dumps(d, indent=1, ensure_ascii=False) + '\n')

# --- quests.json: the book's journal entry
Q = os.path.join('godot', 'data', 'content', 'quests.json')
edit(Q, 'Lamps at the Low Ford lit again, and not by us.\\"', 'Lamps at the Low Ford lit again, and not by us. Not oil. Wrong colour.\\"')

# --- Prologue.cs: the book, and what the journal learns
C = os.path.join('godot', 'logic', 'Play', 'Zones', 'Prologue.cs')
edit(C, '\\"Lamps at the Low Ford lit again, and not by us.\\"', '\\"Lamps at the Low Ford lit again, and not by us. Not oil. Wrong colour.\\"')
edit(C, '"text": "The lamps at the ford feed the Warden."', '"text": "The lamps at the ford burn ember, and the Warden drinks it."')

# --- tests that quote them
edit(os.path.join('godot', 'tests', 'Route.cs'), '"text": "The lamps at the ford feed the Warden."',
     '"text": "The lamps at the ford burn ember, and the Warden drinks it."')
edit(os.path.join('godot', 'tests', 'QuestTests.cs'), 'Assert.Matches("keep the Warden asleep", p!.Text);',
     'Assert.Matches("Oil keeps it sleeping. Ember wakes it.", p!.Text);')
print('ok')

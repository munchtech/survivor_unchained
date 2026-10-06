"""The voice-prep session's notes for the writers, verified and fixed. Run from
the worktree root."""
import json, os


def edit(path, a, b):
    s = open(path, encoding='utf-8', newline='').read()
    assert s.count(a) == 1, (path, a[:80], s.count(a))
    s = s.replace(a, b)
    open(path, 'w', encoding='utf-8', newline='').write(s)


# --- Mixed voices in one caption: narrator, then the speaker, as two captions.
# Prologue: the dead Watchman, for the devout. Also: he says what he saw, not
# how the fight works (VOICES: nobody explains a mechanic).
edit(os.path.join('godot', 'logic', 'Play', 'Zones', 'Prologue.cs'),
     'G.After(10.2, () => G.Say("...and for you alone, the dead man\'s jaw moves: \\"It shatters its own lamps when it charges. Make it charge.\\"", "The dead Watchman", 7));',
     '{\n                    G.After(10.2, () => G.Say("...and for you alone, the dead man\'s jaw moves.", null, 3));\n'
     '                    G.After(13.4, () => G.Say("It broke its own lamps, coming for me. Twice.", "The dead Watchman", 5));\n'
     '                }')
V = os.path.join('godot', 'logic', 'Play', 'Zones', 'Verge.cs')
# The bones at the sealed door, for the devout.
edit(V,
     'G.Say("The skull turns, very slightly, toward you. \\"It was never locked from the outside.\\"", "The bones", 6);',
     'G.Say("The skull turns, very slightly, toward you.", null, 3);\n'
     '                        G.After(3.2, () => G.Say("It was never locked from the outside.", "The bones", 4));')
# The third cage: the narrator sees him, then Jory speaks.
edit(V, '"A young man: \\"Jory. Jory Coyle. Is my uncle —? Is he —?\\"",',
     '"A young man, freckled, still holding the bars after the door is open.",')
edit(V, '        G.Say(CageLines[i], null, 4);\n',
     '        G.Say(CageLines[i], null, 4);\n'
     '        if (i == 2) G.After(2.5, () => G.Say("Jory. Jory Coyle. Is my uncle—? Is he—?", "Jory Coyle", 4));\n')

# --- dialogue.json: the rules VOICES.md sets.
P = os.path.join('godot', 'data', 'content', 'dialogue.json')
d = json.load(open(P, encoding='utf-8'))
# Vonnra never answers yes or no.
n = d['vonnra']['nodes']['cb_vault3']
assert n['text'].startswith('It is. For now. '), n['text']
n['text'] = n['text'].replace('It is. For now. ', 'Yours, for now. ', 1)
# "I will not forget" was retired; this was its echo.
fp = d['vonnra']['nodes']['f_pell']['text']
hit = [v for v in fp if v['text'].endswith('He will not forget you.')]
assert len(hit) == 1
hit[0]['text'] = hit[0]['text'].replace('He will not forget you.', 'He took his books with him. You are in them.')
# Jory never says "cage".
jf = d['jory']['nodes']['first']
assert jf['text'].startswith("You're the one who opened the cage."), jf['text'][:50]
jf['text'] = jf['text'].replace("You're the one who opened the cage.", "You're the one with the bar.", 1)
with open(P, 'w', encoding='utf-8', newline='\r\n') as h:
    h.write(json.dumps(d, indent=1, ensure_ascii=False) + '\n')

N = os.path.join('godot', 'data', 'content', 'npcs.json')
edit(N, '"I thought I\'d die in that cage.",', '"I thought I\'d die in there.",')
edit(N, '"There was a fourth cage. Was."', '"There were four of us. Were."')

# --- Curfew lines are heard only after dark.
F = os.path.join('godot', 'data', 'content', 'folk.json')
s = open(F, encoding='utf-8', newline='').read()
for line in ('Gates are shut till dawn.', "Piss off home. It's past curfew."):
    for nl in ('\r\n', '\n'):
        a = f'"text": "{line}",{nl}   "watch": true{nl}'
        if a in s:
            assert s.count(a) == 1
            s = s.replace(a, f'"text": "{line}",{nl}   "watch": true,{nl}   "night": true{nl}')
            break
    else:
        raise SystemExit('not found: ' + line)
open(F, 'w', encoding='utf-8', newline='').write(s)
print('ok')

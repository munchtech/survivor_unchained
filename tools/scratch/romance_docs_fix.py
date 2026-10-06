"""Bring the romance scene files (the Act 2 writer's source) to the canon
adopted in round three. Run from the worktree root."""
import os, re

R = os.path.join('docs', 'romance')


def fix(path, pairs):
    p = os.path.join(R, path)
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        # tolerate the files' own line wrapping: match runs of whitespace loosely
        pat = re.escape(a).replace(r'\ ', r'\s+')
        s2, n = re.subn(pat, lambda m: b, s, count=1)
        assert n == 1, (path, a[:70])
        s = s2
    open(p, 'w', encoding='utf-8', newline='\n').write(s)


fix('scenes/sella.md', [
    ('fast, then puts it back, slower. "You\'re warmer than the water. You know that? You\'re warmer than the water."',
     'fast, then puts it back, slower. "Your hands are hot and the rest of you\'s a cellar floor. Pick one, love."'),
    ('You ran hot all night. Like lying next to a stove. And now look at you. Cold as the river.',
     'You were cold as the river all night. Like lying next to a stone. And now look at you: warm as toast.'),
    ('You ran hot all night, love. Like sleeping next to a stove. And now you\'re cold as the river.',
     'You were cold as the river all night, love. Like sleeping next to a stone. And now look at you: warm as toast.'),
    ('**SELLA:** Hot at night. Cold as the river by morning.',
     '**SELLA:** Cold as the river all night. Warm by breakfast.'),
    ('Too late. Christ.', 'Too late. Oh, hell.'),
    ('At first light she feels it go out of you, the heat, all at once, like a lamp turned down, and she holds on anyway.',
     'At first light she feels the warmth come into you, all at once, like a lamp turned up, and she holds on anyway.'),
    ('"Well. Now we\'re both warm at night,"', '"Well. Now we\'re both cold at night,"'),
    ('Once for a priest, and I\'ll not say which.', 'Once for one of the Watch, and I\'ll not say which.'),
])
fix('scenes/maeca.md', [
    ('(She looks at your knees, which are still muddy.) He let you.',
     'I was on the ridge. (She looks at your knees.) He let you.'),
    ('"And the bitch with the torn ear. Eating."', '"And the bitch with the white foot. Eating."'),
    ('against your legs, and you flinch: they\'re cold as stones in a stream. She starts to take them back.',
     'against your legs, and flinches: you\'re colder than they are. She starts to take them back.'),
    ('and doesn\'t say anything, and after a long time her feet are warm.',
     'and doesn\'t say anything for a long time. (Into the dark, very low.) "Your hands are colder than my feet." (A pause.) "Hold them anyway."'),
    ('**MAECA:** Your heart\'s slow. (She doesn\'t lift her head.) Slow as a bear\'s in January. It was going like a hare\'s last night.',
     '**MAECA:** Your heart\'s going like a hare\'s. (She doesn\'t lift her head.) All night it was a bear\'s in January. I counted between.'),
    ('A hare at night and a bear at dawn.', 'A bear at night and a hare at dawn.'),
    ('You smell like the river, at dawn.', 'You smell like the river, at night.'),
])
fix('scenes/keegan.md', [
    ('I taught them chiasmus. "Ask not what the Vigil can do for you." They did not, and it did not.',
     'I taught them chiasmus. "The Vigil keeps the gate, and the gate keeps the Vigil." It has kept neither.'),
    ('anaphora. Doing the same thing twice for emphasis. Goodnight.',
     'epizeuxis. The same thing, twice, at once, for emphasis. Goodnight.'),
    ('I have known since they carried you into the shrine under a sheet and you walked out of it.',
     'I have known since they carried you into the shrine under a sheet and you walked out of it. *(Only with `keegan.saw_risen`; otherwise:)* I have known since your breath did not show on my wall at night.'),
    ('Oh, thank God.', 'Oh, thank— thank you.'),
    ('waiting to hear whether the heat goes out of them at first light,',
     'waiting to feel the warmth come into them at first light,'),
    ('You feel the heat go out of you, all at once, like a lamp turned down, and you feel her feel it.',
     'You feel the warmth come into you, all at once, like a lamp turned up, and you feel her feel it.'),
])
fix('scenes/rav.md', [
    ('...Christ, did I say that out loud.', '...Mam— did I say that out loud.'),
    ('His lips move. Four. Seven. Nine. Nothing under his fingers. Eleven. Then there it is, a single slow beat, like somebody knocking on a door very far away, and then another, faster, and then your pulse is going like a hare\'s.',
     'His lips move. Three. Five. Nothing under his fingers. Seven. Then there it is, a single slow beat, like somebody knocking on a door very far away, and then another.'),
    ('For a count of eleven. And now it\'s going again. (He looks up at you.) Christ.',
     'For a count of seven. And now it\'s going again. (He looks up at you.) ...Oh, Mam.'),
    ('count of eleven.', 'count of seven.'),
    ('...Our mother\'d have liked you. God help you.', '...Mam\'d have liked you. Poor sod.'),
])
fix('ARCS.md', [
    ('You run hot at night and you\'re cold as the river by morning;',
     'You are cold as the river all night and warm by breakfast;'),
    ('at dawn your heart is slow "as a bear\'s in January"',
     'all night your heart is "a bear\'s in January", and a hare\'s at dawn'),
    ('no pulse for a count of eleven, then a pulse', 'no pulse for a count of seven, then a pulse'),
    ('"Oh, thank God,"', '"Oh, thank— thank you,"'),
    ('...Christ, did I say that out loud."', '...Mam— did I say that out loud."'),
])

# A status line at the top of the romance README.
p = os.path.join(R, 'README.md')
s = open(p, encoding='utf-8').read()
old = """Drafts of the game's five romances (Sella, Maeca, Keegan, Rav and Ysolde)
for the main author to take into the game or leave out. Nothing here changes
the game: no content JSON, code or existing doc has been edited."""
assert old in s
s = s.replace(old, old + """

> **Status (round three of the cinematics edit).** Adopted. The Act 1 data for
> Sella, Maeca, Keegan and Rav is now in `godot/data/content/dialogue.json`,
> merged node by node (these drafts predate later live work, so do not drop
> them in whole again), with fixes: the body's hours are cold as the river
> all night and warm by breakfast, for every survivor (`STORY_BIBLE.md`
> section 1); no real-world oaths or quotations; Rav's count is seven. The
> scene files below are corrected to match and remain the Act 2 writer's
> source. `vonnra.f_past` now reads `sella.past_sold`.""")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')

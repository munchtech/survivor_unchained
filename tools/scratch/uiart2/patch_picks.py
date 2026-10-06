import os
import shutil
import sys

WT = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748'
S = os.path.dirname(os.path.abspath(__file__))
shutil.copyfile(os.path.join(S, 'fit', 'lamp_glass_b3', 'lamp_glass.png'), os.path.join(WT, 'godot', 'art', 'ui', 'icons', 'item', 'lamp_glass.png'))

p = os.path.join(WT, 'tools', 'uiforge', 'items.py')
s = open(p, encoding='utf-8').read()
s = s.replace('''    "lamp_glass": "a cracked curved shard of thick amber lamp glass with a blackened brass rim, a tiny ember-orange "
                  "flame still burning inside the crack, soot streaks",''', '''    # UI art's repaints (seed 1130; lamp_glass 1140): the cord read as the letter S, the shard as a horn.
    "lamp_glass": "the empty glass chimney of an oil lamp lying on its side by itself, a bulging tube of thick smoky "
                  "amber glass open at both ends, a long crack down its side and a jagged piece broken out of its rim, a "
                  "tiny ember-orange flame still glowing caught inside the glass, soot streaks, no lamp, no base, no "
                  "brass, only the glass",''')
s = s.replace('''    "red_cord": "a length of faded red cord lying in a loose S curve with a long row of small tight knots tied along "
                "it at even intervals, frayed ends, nothing else",''', '''    "red_cord": "a hank of faded red cord coiled round in several loose loops, bound once round the middle of the "
                "hank, its frayed end hanging free below, small tight knots tied all along the cord at even intervals, "
                "nothing else",''')
s = s.replace('''                  "green-black sludge oozing from under the lid and dripping down one side",
}''', '''                  "green-black sludge oozing from under the lid and dripping down one side",
    # The crafting lead's flask, repainted: its first came cool and flat-lit, a mark on it reading as a letter.
    "flask": "a flat pewter hip flask in a stitched brown leather sleeve, a small screw cap on a short chain, worn and "
             "dented, warm candlelight gleaming on the pewter, plain metal with no marks, no engraving, no letters",
}''')
s = s.replace('''    "slurry_jar": (1100, 0), "lamp_glass": (1100, 1), "hunt_bone": (1120, 2), "gate_nail": (1110, 0), "red_cord": (1110, 1),''', '''    "slurry_jar": (1100, 0), "hunt_bone": (1120, 2), "gate_nail": (1110, 0),
    # UI art's repaints, fitted at the set's 0.82.
    "red_cord": (1130, 2), "lamp_glass": (1140, 3), "scar_glass": (1130, 3), "flask": (1130, 2),''')
open(p, 'w', encoding='utf-8').write(s)
print('items', s.count('"flask"'), s.count('(1140, 3)'))

p = os.path.join(WT, 'tools', 'uiforge', 'emblems.py')
s = open(p, encoding='utf-8').read()
s = s.replace('''    "mark": (55, 1330, 0), "wing": (65, 1330, 0),
}''', '''    "mark": (55, 1330, 0), "wing": (65, 1330, 0),
    # Crashing Leap's second concept, in place of the first (its file is leap.png: ALIAS).
    "leap2": (55, 1340, 0),
}
# A design whose painting replaces another key's icon.
ALIAS = {"leap2": "leap"}''')
s = s.replace('''    dst = dst or os.path.join(UI, key + ".png")''', '''    dst = dst or os.path.join(UI, ALIAS.get(key, key) + ".png")''')
s = s.replace('''"umbral": (65, 1330, 0), "leap": (55, 1330, 1),''', '''"umbral": (65, 1330, 0),''')
open(p, 'w', encoding='utf-8').write(s)
print('emblems', s.count('ALIAS'), s.count('"leap": (55'))

sys.path.insert(0, os.path.join(WT, 'tools', 'uiforge'))
os.chdir(WT)
import imports  # noqa: E402
print(imports.write(['godot/art/ui/icons/item/scar_glass.png', 'godot/art/ui/icons/item/lamp_glass.png']))

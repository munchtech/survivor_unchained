import sys
sys.path.insert(0, r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3')
from edlib import edit

edit('godot/src/Ui/MapTable.cs', [
    ('''        float H = again ? 916 : 816;''', '''        // (a sheet holds what the map pays and up to two oaths in full)
        float H = again ? 976 : 876;'''),
    ('''        float sheetW = 448, sheetH = 548, gap = (W - 44 - 3 * sheetW) / 4;''', '''        float sheetW = 448, sheetH = 608, gap = (W - 44 - 3 * sheetW) / 4;'''),
    ('''        v.AddChild(L($"Its gear leans to {Bane(MapOffers.Lean(o.Spec, o.People))}: what answers them.", Style.TextItalic, Style.Caption, Answer));''',
     '''        // (the gear in a line: the names only, three at most; the bane in full is in the sub-title's words)
        var lean = MapOffers.Lean(o.Spec, o.People).Select(a => SurvivorUnchained.Rpg.Items.Affix(a)?.Name ?? a).Distinct().Take(3);
        v.AddChild(L($"Gear leaning to {string.Join(", ", lean)}", Style.TextItalic, Style.Caption, Answer));'''),
])

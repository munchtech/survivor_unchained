import sys
sys.path.insert(0, r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3')
from edlib import edit

edit('godot/src/Ui/ArenaResult.cs', [
    ('''        landed.Clear();
        if (shownFor > 0) told = true;
''', '''        landed.Clear();
'''),
    ('''                var btn = Style.Button(w.Name, () => { if (Arenas.Inscribe(G.Journey, r, id)) Refresh(); }, false, true);''',
     '''                var btn = Style.Button(w.Name, () => { if (Arenas.Inscribe(G.Journey, r, id)) { told = true; Refresh(); } }, false, true);'''),
    ('''    /// <summary>Kept through a rebuild (a tome written), so the story is not told twice.</summary>
    bool told;''', '''    /// <summary>Told all at once (a press, a click, a tome written), so it is never told twice.</summary>
    bool told;'''),
])

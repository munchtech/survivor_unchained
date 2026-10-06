import sys
sys.path.insert(0, r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3')
from edlib import edit

edit('godot/src/Ui/ArenaResult.cs', [
    ('''        AddChild(new Backdrop(null, r.Won ? 0.82f : 0.9f));''', '''        // (a click anywhere tells the rest at once)
        AddChild(new Backdrop(() => told = true, r.Won ? 0.82f : 0.9f));'''),
    ('''        var go = Style.Button("", () => G.LeaveArena(r), true);''', '''        var go = Style.Button("", () => { if (Told) G.LeaveArena(r); else told = true; }, true);'''),
    ('''cue + 0.6, () => Sound.Sfx.Moment(0.1, 0.9f)));''', '''cue + 0.6));'''),
])

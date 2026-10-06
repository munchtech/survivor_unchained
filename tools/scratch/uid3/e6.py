import sys
sys.path.insert(0, r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3')
from edlib import edit

edit('godot/src/Ui/CreateLook.cs', [
    ('''    float SectionTurn() => d.Step == LookStep && Section == "Hair" ? -0.95f : 0;''',
     '''    float SectionTurn() => d.Step != LookStep || Section != "Hair" ? 0 : d.HairStyle switch { "ponytail" => -1.4f, "braid" => -1.75f, _ => -0.95f };'''),
])
edit('godot/src/Ui/Front.cs', [
    ('''        int step = d.Step, section = d.Section;
        change();
        G.DressFigure(d);
        // A new step or part frames the figure for it (the look's parts come near: her hair, her face).
        if (d.Step != step || d.Section != section) G.FrameFigure(SectionZoom(), SectionTurn());''',
     '''        int step = d.Step, section = d.Section;
        string cut = d.HairStyle;
        change();
        G.DressFigure(d);
        // A new step or part frames the figure for it (the look's parts come near: her hair, her face);
        // a new cut turns her so it shows (a braid down her back is seen from behind).
        if (d.Step != step || d.Section != section || d.HairStyle != cut) G.FrameFigure(SectionZoom(), SectionTurn());'''),
])

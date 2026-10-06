import sys
sys.path.insert(0, r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3')
from edlib import edit

edit('godot/tests/LoadoutTests.cs', [
    ('''        Assert.Null(Loadouts.Of(him).Person.Face);
        Assert.Null(Loadouts.Of(him).Person.Eyes);
    }''', '''        Assert.Null(Loadouts.Of(him).Person.Face);
        Assert.Null(Loadouts.Of(him).Person.Eyes);
        // No beard of a hero's own on either: hers has none, and his body is the kit's yet.
        Assert.Null(Loadouts.Of(ch).Person.BeardStyle);
        Assert.Null(Loadouts.Of(him).Person.BeardStyle);
    }'''),
    ('''        Assert.Contains(her.Paints, p => p.Id == "none");''', '''        Assert.Contains(her.Paints, p => p.Id == "none");
        // A face that brings its own skin or eyes names ones there are.
        Assert.All(her.Faces, f =>
        {
            if (f.Skin != null) Assert.Contains(World.Lore.Skins, s => s.Id == f.Skin);
            if (f.Eyes != null) Assert.Contains(her.Eyes, e => e.Id == f.Eyes);
        });
        Assert.Empty(her.Beards);'''),
])

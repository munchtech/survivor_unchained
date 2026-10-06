import sys
sys.path.insert(0, r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3')
from edlib import edit

edit('godot/src/Ui/CreateLook.cs', [
    ('''        var v = Style.V(8, Style.SubLabel($"{Their} hair"));
        var row = new HFlowContainer();
        row.AddThemeConstantOverride("h_separation", 6);
        var dye = HairColour();
        foreach (var cut in k.Cuts)
            row.AddChild(new Cameo(Art($"hair_{cut.Id}"), cut.Name, d.HairStyle == cut.Id, () => Set(() => d.HairStyle = cut.Id), 82, dye, "lock"));
        v.AddChild(row);''', '''        var v = Style.V(8, Style.SubLabel($"{Their} hair"));
        // (large: a cut is told by its shape, which a small picture loses)
        var row = Grid(3);
        var dye = HairColour();
        foreach (var cut in k.Cuts)
            row.AddChild(new Cameo(Art($"hair_{cut.Id}"), cut.Name, d.HairStyle == cut.Id, () => Set(() => d.HairStyle = cut.Id), 136, dye, "lock"));
        v.AddChild(row);'''),
    ('''            v.AddChild(Style.SubLabel($"{Their} face"));
            var grid = new GridContainer { Columns = 4 };
            grid.AddThemeConstantOverride("h_separation", 8);
            grid.AddThemeConstantOverride("v_separation", 4);
            foreach (var f in k.Faces)
                grid.AddChild(new Cameo(Art($"face_{f.Id}"), f.Name, d.FaceShape == f.Id, () => Set(() => { d.FaceShape = f.Id; d.Face = new Dictionary<string, double>(f.Shape); }), 92, null, "mask"));''', '''            v.AddChild(Style.SubLabel($"{Their} face"));
            var grid = Grid(4);
            foreach (var f in k.Faces)
                grid.AddChild(new Cameo(Art($"face_{f.Id}"), f.Name, d.FaceShape == f.Id, () => Set(() => { d.FaceShape = f.Id; d.Face = new Dictionary<string, double>(f.Shape); }), 100, null, "mask"));'''),
    ('''        var v = Style.V(8, Style.SubLabel($"Paint on {Their.ToLowerInvariant()} face"));
        var grid = new GridContainer { Columns = 4 };
        grid.AddThemeConstantOverride("h_separation", 8);
        grid.AddThemeConstantOverride("v_separation", 4);
        foreach (var p in k.Paints)
            grid.AddChild(new Cameo(Art($"paint_{p.Id}"), p.Name, d.Paint == p.Id, () => Set(() => d.Paint = p.Id), 92, null, "mask"));
        v.AddChild(grid);
        return v;
    }''', '''        var v = Style.V(8, Style.SubLabel($"Paint on {Their.ToLowerInvariant()} face"));
        // (large: kohl and ash are fine lines a small picture loses)
        var grid = Grid(3);
        foreach (var p in k.Paints)
            grid.AddChild(new Cameo(Art($"paint_{p.Id}"), p.Name, d.Paint == p.Id, () => Set(() => d.Paint = p.Id), 136, null, "mask"));
        v.AddChild(grid);
        return v;
    }

    /// <summary>A grid of cameos, so many to a row.</summary>
    static GridContainer Grid(int columns)
    {
        var g = new GridContainer { Columns = columns };
        g.AddThemeConstantOverride("h_separation", columns > 3 ? 6 : 10);
        g.AddThemeConstantOverride("v_separation", 2);
        return g;
    }'''),
    ('''                Texture = art, Material = m, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale,''',
     '''                Texture = art, Material = m, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, TextureFilter = TextureFilterEnum.LinearWithMipmaps,'''),
])

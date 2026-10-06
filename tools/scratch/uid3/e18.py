import sys
sys.path.insert(0, r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3')
from edlib import edit

edit('godot/src/Ui/Front.cs', [
    ('''    public string Palette = "steel", Model = "knight", Cloak = "calling", Skin = "fair", Hair = "as_is", HairStyle = "long";''',
     '''    public string Palette = "steel", Model = "knight", Cloak = "calling", Skin = "fair", Hair = "as_is", HairStyle = "long";
    /// <summary>A hero's own beard (Lore.Hero's beards: the male hero's), or "".</summary>
    public string BeardStyle = "";'''),
    ('''        Eyes = Loadouts.HeroKit(Sex) != null ? Eyes : null, Paint = Loadouts.HeroKit(Sex) != null ? Paint : null,
    };''', '''        Eyes = Loadouts.HeroKit(Sex) != null ? Eyes : null, Paint = Loadouts.HeroKit(Sex) != null ? Paint : null,
        BeardStyle = Loadouts.HeroKit(Sex) is { Beards.Count: > 0 } && BeardStyle != "" ? BeardStyle : null,
    };'''),
    ('''+ (Sex == Sex.Male ? $"|{Skin}|{Hair}|{HairStyle}" : "");''', '''+ (Sex == Sex.Male ? $"|{Skin}|{Hair}|{HairStyle}|{BeardStyle}" : "");'''),
    ('''            Paint = kit.Paints.FirstOrDefault()?.Id ?? "none";''', '''            Paint = kit.Paints.FirstOrDefault()?.Id ?? "none";
            BeardStyle = kit.Beards.FirstOrDefault()?.Id ?? "";'''),
    ('''    /// <summary>The look step's part (body, hair, face, paint) and the face's group of sliders.</summary>''',
     '''    /// <summary>The look step's part (hair, face, shape, paint, body) and the face's group of sliders.</summary>'''),
])

edit('godot/src/Ui/CreateLook.cs', [
    ('''/* Creation's second step, the look (docs/UI_DESIGN.md 7.2): the hair, face,
 * paint and body, each a part of its own on the triggers, the figure framed
 * for it (head and shoulders, the face, all of them) and turned or brought
 * near by hand.''', '''/* Creation's second step, the look (docs/UI_DESIGN.md 7.2): the hair, face,
 * shape, paint and body, each a part of its own on the triggers, the figure
 * framed for it (head and shoulders, the face, all of them) and turned or
 * brought near by hand. The face is chosen whole (faces to start from, the
 * eyes) in one part and shaped by hand in the next, which has the column to
 * itself so every group's sliders show at once.'''),
    ('''    string[] Sections => Kit is { } k
        ? new[] { "Hair" }.Concat(k.Sliders.Count > 0 || k.Faces.Count > 1 || k.Eyes.Count > 1 ? new[] { "Face" } : Array.Empty<string>())
            .Concat(k.Paints.Count > 1 ? new[] { "Paint" } : Array.Empty<string>()).Append("Body").ToArray()
        : new[] { "Hair", "Body" };''', '''    string[] Sections => Kit is { } k
        ? new[] { "Hair" }.Concat(k.Faces.Count > 1 || k.Eyes.Count > 1 ? new[] { "Face" } : Array.Empty<string>())
            .Concat(k.Sliders.Count > 0 ? new[] { "Shape" } : Array.Empty<string>())
            .Concat(k.Paints.Count > 1 ? new[] { "Paint" } : Array.Empty<string>()).Append("Body").ToArray()
        : new[] { "Hair", "Body" };'''),
    ('''    float SectionZoom() => d.Step != LookStep ? 0 : Section switch { "Hair" => 0.55f, "Face" or "Paint" => 1f, _ => 0f };''',
     '''    float SectionZoom() => d.Step != LookStep ? 0 : Section switch { "Hair" => 0.55f, "Face" or "Shape" or "Paint" => 1f, _ => 0f };'''),
    ('''            b.CustomMinimumSize = new Vector2(Sections.Length > 2 ? 96 : 140, 40);''', '''            b.CustomMinimumSize = new Vector2(Sections.Length > 4 ? 82 : Sections.Length > 2 ? 96 : 140, 40);'''),
    ('''        ("Face", { } k) => HeroFace(k),''', '''        ("Face", { } k) => HeroFace(k),
        ("Shape", { } k) => HeroShape(k),'''),
    ('''        v.AddChild(row);
        v.AddChild(Style.Gap(4));
        v.AddChild(Style.SubLabel("Colour"));
        v.AddChild(Beads(Lore.Hairs, d.Hair, id => d.Hair = id, Bead.Kind.Hair, OwnHair().ToHtml(false)));
        return v;
    }''', '''        v.AddChild(row);
        if (k.Beards.Count > 0)
        {
            // His beard, as his cuts: cameos dyed his hair's colour.
            v.AddChild(Style.SubLabel("Beard"));
            var beards = Grid(4);
            foreach (var b in k.Beards)
                beards.AddChild(new Cameo(Art($"beard_{b.Id}"), b.Name, d.BeardStyle == b.Id, () => Set(() => d.BeardStyle = b.Id), 100, dye, "mask"));
            v.AddChild(beards);
        }
        v.AddChild(Style.Gap(4));
        v.AddChild(Style.SubLabel("Colour"));
        v.AddChild(Beads(Lore.Hairs, d.Hair, id => d.Hair = id, Bead.Kind.Hair, OwnHair().ToHtml(false)));
        return v;
    }'''),
    ('''    /// <summary>Faces to start from, the eyes' colour, and the face shaped by hand.</summary>
    Control HeroFace(HeroLook k)
    {
        var v = Style.V(8);
        if (k.Faces.Count > 1)
        {
            v.AddChild(Style.SubLabel($"{Their} face"));
            var grid = Grid(4);
            foreach (var f in k.Faces)
                grid.AddChild(new Cameo(Art($"face_{f.Id}"), f.Name, d.FaceShape == f.Id, () => Set(() => { d.FaceShape = f.Id; d.Face = new Dictionary<string, double>(f.Shape); }), 100, null, "mask"));
            v.AddChild(grid);
        }
        if (k.Eyes.Count > 1)
        {
            v.AddChild(Style.SubLabel("Eyes"));
            v.AddChild(Beads(k.Eyes, d.Eyes, id => d.Eyes = id, Bead.Kind.Eye, ""));
        }
        if (k.Sliders.Count == 0) return v;
        // Shaped by hand: a group of sliders at a time.
        var groups = k.Sliders.Select(s => s.Group).Distinct().ToArray();
        int g = Math.Clamp(d.FaceGroup, 0, groups.Length - 1);
        var head = Style.H(6, Style.SubLabel("Shape it"));
        head.AddChild(new Control { SizeFlagsHorizontal = SizeFlags.ExpandFill });
        for (int i = 0; i < groups.Length; i++)
        {
            int at = i;
            head.AddChild(Nav.Id(Style.Segment(groups[i], g == i, () => Set(() => d.FaceGroup = at)), $"group:{groups[i]}"));
        }
        v.AddChild(head);
        foreach (var s in k.Sliders.Where(s => s.Group == groups[g]))
            v.AddChild(SliderRow(s));
        var preset = k.Faces.FirstOrDefault(f => f.Id == d.FaceShape) ?? k.Faces.FirstOrDefault();
        if (Shaped(k, preset))
            v.AddChild(Nav.Id(Style.Button(preset != null ? $"Back to {preset.Name.ToLowerInvariant()}" : $"Back to {Their.ToLowerInvariant()} own face",
                () => Set(() => d.Face = new Dictionary<string, double>(preset?.Shape ?? new())), false, true), "unshape"));
        return v;
    }''', '''    /// <summary>Faces to start from (a face may bring its own skin and eyes), and the eyes' colour.</summary>
    Control HeroFace(HeroLook k)
    {
        var v = Style.V(8);
        if (k.Faces.Count > 1)
        {
            v.AddChild(Style.SubLabel($"{Their} face"));
            var grid = Grid(4);
            foreach (var f in k.Faces)
                grid.AddChild(new Cameo(Art($"face_{f.Id}"), f.Name, d.FaceShape == f.Id, () => Set(() => Choose(f)), 100, null, "mask"));
            v.AddChild(grid);
        }
        if (k.Eyes.Count > 1)
        {
            v.AddChild(Style.SubLabel("Eyes"));
            v.AddChild(Beads(k.Eyes, d.Eyes, id => d.Eyes = id, Bead.Kind.Eye, ""));
        }
        if (k.Sliders.Count > 0)
            v.AddChild(Style.Label($"Shape it by hand in the next part.", Style.TextItalic, Style.Caption, Style.InkDim));
        return v;
    }

    /// <summary>A face to start from, taken: its shape, and its skin and eyes where it has its own.</summary>
    void Choose(FaceShape f)
    {
        d.FaceShape = f.Id;
        d.Face = new Dictionary<string, double>(f.Shape);
        if (f.Skin is { } skin && Lore.Skins.Any(s => s.Id == skin)) d.Skin = skin;
        if (f.Eyes is { } eyes && Kit is { } k && k.Eyes.Any(e => e.Id == eyes)) d.Eyes = eyes;
    }

    /// <summary>The face shaped by hand: its groups as tabs, four to a row, and the
    /// group's sliders under them; the column to itself, so none is hidden.</summary>
    Control HeroShape(HeroLook k)
    {
        var v = Style.V(8);
        var groups = k.Sliders.Select(s => s.Group).Distinct().ToArray();
        int g = Math.Clamp(d.FaceGroup, 0, groups.Length - 1);
        v.AddChild(Style.SubLabel($"Shape {Their.ToLowerInvariant()} face"));
        var tabs = new GridContainer { Columns = Math.Min(4, groups.Length) };
        tabs.AddThemeConstantOverride("h_separation", 6);
        tabs.AddThemeConstantOverride("v_separation", 6);
        for (int i = 0; i < groups.Length; i++)
        {
            int at = i;
            var seg = Nav.Id(Style.Segment(groups[i], g == i, () => Set(() => d.FaceGroup = at)), $"group:{groups[i]}");
            seg.CustomMinimumSize = new Vector2(114, 34);
            tabs.AddChild(seg);
        }
        v.AddChild(tabs);
        v.AddChild(Style.Gap(4));
        foreach (var s in k.Sliders.Where(s => s.Group == groups[g]))
            v.AddChild(SliderRow(s));
        var preset = k.Faces.FirstOrDefault(f => f.Id == d.FaceShape) ?? k.Faces.FirstOrDefault();
        if (Shaped(k, preset))
        {
            v.AddChild(Style.Gap(4));
            v.AddChild(Nav.Id(Style.Button(preset != null ? $"Back to {preset.Name.ToLowerInvariant()}" : $"Back to {Their.ToLowerInvariant()} own face",
                () => Set(() => d.Face = new Dictionary<string, double>(preset?.Shape ?? new())), false, true), "unshape"));
        }
        return v;
    }'''),
    ('''            case "Face" when k != null:
                var f = k.Faces.FirstOrDefault(x => x.Id == d.FaceShape) ?? k.Faces.FirstOrDefault();
                (title, name, words) = ($"{Their} face", (f?.Name ?? "Their own") + (Shaped(k, f) ? ", shaped" : ""), f?.Words ?? "");
                break;''', '''            case "Face" when k != null:
                var f = k.Faces.FirstOrDefault(x => x.Id == d.FaceShape) ?? k.Faces.FirstOrDefault();
                (title, name, words) = ($"{Their} face", (f?.Name ?? "Their own") + (Shaped(k, f) ? ", shaped" : ""), f?.Words ?? "");
                break;
            case "Shape" when k != null:
                var sf = k.Faces.FirstOrDefault(x => x.Id == d.FaceShape) ?? k.Faces.FirstOrDefault();
                var groups = k.Sliders.Select(s => s.Group).Distinct().ToArray();
                (title, name, words) = ($"{Their} face", (sf?.Name ?? "Their own") + (Shaped(k, sf) ? ", shaped" : ""),
                    groups.Length > 0 ? $"{groups[Math.Clamp(d.FaceGroup, 0, groups.Length - 1)]}: each slider runs from one end to the other, {Their.ToLowerInvariant()} chosen face at its middle." : "");
                break;'''),
    ('''        yield return ("Hair", $"{cut}, {Of(Lore.Hairs, d.Hair).ToLowerInvariant()}");
        if (k == null) yield break;''', '''        yield return ("Hair", $"{cut}, {Of(Lore.Hairs, d.Hair).ToLowerInvariant()}");
        if (k == null) yield break;
        if (k.Beards.Count > 0) yield return ("Beard", k.Beards.FirstOrDefault(b => b.Id == d.BeardStyle)?.Name ?? k.Beards[0].Name);'''),
])

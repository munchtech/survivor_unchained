exec(open(__file__.replace('ed4.py', 'edlib.py')).read())
p = 'godot/src/Ui/CreateLook.cs'
edit(p, [
('''/* Creation's fourth step, the look (docs/UI_DESIGN.md 7.2): her body, hair,
 * face and paint, each a part of its own on the triggers, the figure framed
 * for it (all of her, head and shoulders, her face) and turned or brought
 * near by hand. Her cuts, faces and paints are cameos (her portrait in an
 * iron ring, painted from the model: art/ui/create); colours are beads (her
 * irises drawn as irises); her face's sliders run from one end to the other
 * about her own face, as far as it still looks like her (Lore.Sliders). */
public partial class CreateScreen
{
    static readonly string[] HerSections = { "Body", "Hair", "Face", "Paint" };
    static readonly string[] HisSections = { "Body", "Hair" };
    static readonly string[] FaceGroups = { "Eyes", "Nose", "Mouth", "Jaw" };
    static readonly Dictionary<string, string> HairNames = new() { ["Hair_SimpleParted"] = "Parted", ["Hair_Buzzed"] = "Cropped", ["Hair_Long"] = "Long", ["Hair_Buns"] = "Buns", ["Hair_BuzzedFemale"] = "Cropped", ["none"] = "Shorn" };
    ScrollContainer? scroll;
    (int, int) scrollKey;

    bool Her => d.Sex == Sex.Female;
    string[] Sections => Her ? HerSections : HisSections;
    string Section => Sections[Math.Clamp(d.Section, 0, Sections.Length - 1)];''',
'''/* Creation's fourth step, the look (docs/UI_DESIGN.md 7.2): the body, hair,
 * face and paint, each a part of its own on the triggers, the figure framed
 * for it (all of them, head and shoulders, the face) and turned or brought
 * near by hand. A hero's own body (the heroine's; the male hero's when he has
 * one: Loadouts.HeroKit) offers its own cuts, faces, eyes and paints, as
 * cameos (a portrait in an iron ring, painted from the model:
 * art/ui/create/SEX/); colours are beads (irises drawn as irises); the face's
 * sliders run from one end to the other about the hero's own face, as far as
 * it still looks like them. A kit body is shaped with a cut and a beard. */
public partial class CreateScreen
{
    static readonly Dictionary<string, string> HairNames = new() { ["Hair_SimpleParted"] = "Parted", ["Hair_Buzzed"] = "Cropped", ["Hair_Long"] = "Long", ["Hair_Buns"] = "Buns", ["Hair_BuzzedFemale"] = "Cropped", ["none"] = "Shorn" };
    ScrollContainer? scroll;
    (int, int) scrollKey;

    bool Her => d.Sex == Sex.Female;
    /// <summary>"Her" or "His", as the survivor is.</summary>
    string Their => Her ? "Her" : "His";
    /// <summary>What their own body offers to be shaped with (null: a kit body).</summary>
    HeroLook? Kit => Loadouts.HeroKit(d.Sex);
    string[] Sections => Kit is { } k
        ? new[] { "Body", "Hair" }.Concat(k.Sliders.Count > 0 || k.Faces.Count > 1 || k.Eyes.Count > 1 ? new[] { "Face" } : Array.Empty<string>())
            .Concat(k.Paints.Count > 1 ? new[] { "Paint" } : Array.Empty<string>()).ToArray()
        : new[] { "Body", "Hair" };
    string Section => Sections[Math.Clamp(d.Section, 0, Sections.Length - 1)];
    /// <summary>A cameo's picture under art/ui/create/, by the survivor's sex.</summary>
    string Art(string key) => $"{d.Sex.Key()}/{key}";'''),
('''    Control Look(Archetype a) => Section switch
    {
        "Hair" => Her ? HerHair() : HisHair(a),
        "Face" => HerFace(),
        "Paint" => HerPaint(),
        _ => LookBody(a),
    };''',
'''    Control Look(Archetype a) => (Section, Kit) switch
    {
        ("Hair", { } k) => HeroHair(k),
        ("Hair", null) => KitHair(a),
        ("Face", { } k) => HeroFace(k),
        ("Paint", { } k) => HeroPaint(k),
        _ => LookBody(a),
    };'''),
('''        if (!Her) body.AddChild(Nav.Id(Style.Segment(d.Beard ? "Bearded" : "Clean-shaven", d.Beard, () => Set(() => d.Beard = !d.Beard)), "beard"));''',
'''        if (!Her && Kit == null) body.AddChild(Nav.Id(Style.Segment(d.Beard ? "Bearded" : "Clean-shaven", d.Beard, () => Set(() => d.Beard = !d.Beard)), "beard"));'''),
('''        v.AddChild(Style.SubLabel(Her ? "Colours of her outfit" : "Colours"));''',
'''        v.AddChild(Style.SubLabel($"Colours of {Their.ToLowerInvariant()} outfit"));'''),
('''    /// <summary>Her five cuts as cameos (dyed the colour chosen), and the colours.</summary>
    Control HerHair()
    {
        var v = Style.V(8, Style.SubLabel("Her hair"));
        var row = Style.H(6);
        var dye = HairColour();
        foreach (var cut in Lore.HerHairs)
            row.AddChild(new Cameo($"hair_{cut.Id}", cut.Name, d.HairStyle == cut.Id, () => Set(() => d.HairStyle = cut.Id), 82, dye, "lock"));
        v.AddChild(row);
        v.AddChild(Style.Gap(4));
        v.AddChild(Style.SubLabel("Colour"));
        v.AddChild(Beads(Lore.Hairs, d.Hair, id => d.Hair = id, Bead.Kind.Hair, People.HerHairColour.ToHtml(false)));
        return v;
    }

    Control HisHair(Archetype a)''',
'''    /// <summary>The hero's own cuts as cameos (dyed the colour chosen), and the colours.</summary>
    Control HeroHair(HeroLook k)
    {
        var v = Style.V(8, Style.SubLabel($"{Their} hair"));
        var row = new HFlowContainer();
        row.AddThemeConstantOverride("h_separation", 6);
        var dye = HairColour();
        foreach (var cut in k.Cuts)
            row.AddChild(new Cameo(Art($"hair_{cut.Id}"), cut.Name, d.HairStyle == cut.Id, () => Set(() => d.HairStyle = cut.Id), 82, dye, "lock"));
        v.AddChild(row);
        v.AddChild(Style.Gap(4));
        v.AddChild(Style.SubLabel("Colour"));
        v.AddChild(Beads(Lore.Hairs, d.Hair, id => d.Hair = id, Bead.Kind.Hair, OwnHair().ToHtml(false)));
        return v;
    }

    /// <summary>A kit body's hair: its cuts, its colours, and the hood over it.</summary>
    Control KitHair(Archetype a)'''),
('''        var v = Style.V(8, Style.H(8, Style.SubLabel("His hair"), hidden ? Style.Label("under the hood", Style.TextItalic, 13, Style.InkDim) : new Control()));''',
'''        var v = Style.V(8, Style.H(8, Style.SubLabel($"{Their} hair"), hidden ? Style.Label("under the hood", Style.TextItalic, 13, Style.InkDim) : new Control()));'''),
('''    /// <summary>Faces to start from, her eyes' colour, and her face shaped by hand.</summary>
    Control HerFace()
    {
        var v = Style.V(8, Style.SubLabel("Her face"));
        var grid = new GridContainer { Columns = 4 };
        grid.AddThemeConstantOverride("h_separation", 8);
        grid.AddThemeConstantOverride("v_separation", 4);
        foreach (var f in Lore.Faces)
            grid.AddChild(new Cameo($"face_{f.Id}", f.Name, d.FaceShape == f.Id, () => Set(() => { d.FaceShape = f.Id; d.Face = new Dictionary<string, double>(f.Shape); }), 92, null, "mask"));
        v.AddChild(grid);
        v.AddChild(Style.SubLabel("Eyes"));
        v.AddChild(Beads(Lore.Eyes, d.Eyes, id => d.Eyes = id, Bead.Kind.Eye, ""));
        // Shaped by hand: a group of sliders at a time.
        var head = Style.H(6, Style.SubLabel("Shape it"));
        head.AddChild(new Control { SizeFlagsHorizontal = SizeFlags.ExpandFill });
        for (int i = 0; i < FaceGroups.Length; i++)
        {
            int at = i;
            head.AddChild(Nav.Id(Style.Segment(FaceGroups[i], d.FaceGroup == i, () => Set(() => d.FaceGroup = at)), $"group:{FaceGroups[i]}"));
        }
        v.AddChild(head);
        foreach (var s in Lore.Sliders.Where(s => s.Group == FaceGroups[Math.Clamp(d.FaceGroup, 0, FaceGroups.Length - 1)]))
            v.AddChild(SliderRow(s));
        var preset = Lore.Faces.FirstOrDefault(f => f.Id == d.FaceShape) ?? Lore.Faces[0];
        if (Shaped(preset))
            v.AddChild(Nav.Id(Style.Button($"Back to {preset.Name.ToLowerInvariant()}", () => Set(() => d.Face = new Dictionary<string, double>(preset.Shape)), false, true), "unshape"));
        return v;
    }

    /// <summary>Her face moved from the face it started from.</summary>
    bool Shaped(FaceShape preset) =>
        Lore.Sliders.Any(s => Math.Abs(d.Face.GetValueOrDefault(s.Id) - preset.Shape.GetValueOrDefault(s.Id)) > 1e-3);''',
'''    /// <summary>Faces to start from, the eyes' colour, and the face shaped by hand.</summary>
    Control HeroFace(HeroLook k)
    {
        var v = Style.V(8);
        if (k.Faces.Count > 1)
        {
            v.AddChild(Style.SubLabel($"{Their} face"));
            var grid = new GridContainer { Columns = 4 };
            grid.AddThemeConstantOverride("h_separation", 8);
            grid.AddThemeConstantOverride("v_separation", 4);
            foreach (var f in k.Faces)
                grid.AddChild(new Cameo(Art($"face_{f.Id}"), f.Name, d.FaceShape == f.Id, () => Set(() => { d.FaceShape = f.Id; d.Face = new Dictionary<string, double>(f.Shape); }), 92, null, "mask"));
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
    }

    /// <summary>The face moved from the face it started from.</summary>
    bool Shaped(HeroLook k, FaceShape? preset) =>
        k.Sliders.Any(s => Math.Abs(d.Face.GetValueOrDefault(s.Id) - (preset?.Shape.GetValueOrDefault(s.Id) ?? 0)) > 1e-3);'''),
('''    /// <summary>Her paints as cameos: bare, kohl, woad, ochre, ash, blood, gilt.</summary>
    Control HerPaint()
    {
        var v = Style.V(8, Style.SubLabel("Paint on her face"));
        var grid = new GridContainer { Columns = 4 };
        grid.AddThemeConstantOverride("h_separation", 8);
        grid.AddThemeConstantOverride("v_separation", 4);
        foreach (var p in Lore.Paints)
            grid.AddChild(new Cameo($"paint_{p.Id}", p.Name, d.Paint == p.Id, () => Set(() => d.Paint = p.Id), 92, null, "mask"));''',
'''    /// <summary>The paints as cameos (hers: bare, kohl, woad, ochre, ash, blood, gilt).</summary>
    Control HeroPaint(HeroLook k)
    {
        var v = Style.V(8, Style.SubLabel($"Paint on {Their.ToLowerInvariant()} face"));
        var grid = new GridContainer { Columns = 4 };
        grid.AddThemeConstantOverride("h_separation", 8);
        grid.AddThemeConstantOverride("v_separation", 4);
        foreach (var p in k.Paints)
            grid.AddChild(new Cameo(Art($"paint_{p.Id}"), p.Name, d.Paint == p.Id, () => Set(() => d.Paint = p.Id), 92, null, "mask"));'''),
('''    Color HairColour() => Lore.Hairs.FirstOrDefault(h => h.Id == d.Hair) is { Color: not "" } h ? new Color(h.Color) : Her ? People.HerHairColour : new Color("#6a5a48");''',
'''    Color HairColour() => Lore.Hairs.FirstOrDefault(h => h.Id == d.Hair) is { Color: not "" } h ? new Color(h.Color) : OwnHair();

    /// <summary>Hair "as it grew": hers copper, a kit body's its paint's brown.</summary>
    Color OwnHair() => Her ? People.HerHairColour : new Color("#6a5a48");'''),
])
print('part1')

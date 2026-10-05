using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.View;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/* Creation's second step, the look (docs/UI_DESIGN.md 7.2): the hair, face,
 * shape, paint and body, each a part of its own on the triggers, the figure
 * framed for it (head and shoulders, the face, all of them) and turned or
 * brought near by hand. The face is chosen whole (faces to start from, the
 * eyes) in one part and shaped by hand in the next, which has the column to
 * itself so every group's sliders show at once. Hair comes first: it is what a player looks for, and it shows
 * at once that she is theirs to shape. A hero's own body (the heroine's; the male hero's when he has
 * one: Loadouts.HeroKit) offers its own cuts, faces, eyes and paints, as
 * cameos (a portrait in an iron ring, painted from the model:
 * art/ui/create/SEX/); colours are beads (irises drawn as irises); the face's
 * sliders run from one end to the other about the hero's own face, as far as
 * it still looks like them. A kit body is shaped with a cut and a beard. */
public partial class CreateScreen
{
    static readonly Dictionary<string, string> HairNames = new() { ["Hair_SimpleParted"] = "Parted", ["Hair_Buzzed"] = "Cropped", ["Hair_Long"] = "Long", ["Hair_Buns"] = "Buns", ["Hair_BuzzedFemale"] = "Cropped", ["none"] = "Shorn" };
    bool Her => d.Sex == Sex.Female;
    /// <summary>"Her" or "His", as the survivor is.</summary>
    string Their => Her ? "Her" : "His";
    /// <summary>What their own body offers to be shaped with (null: a kit body).</summary>
    HeroLook? Hero => Loadouts.HeroKit(d.Sex);
    string[] Sections => Hero is { } k
        ? new[] { "Hair" }.Concat(k.Faces.Count > 1 || k.Eyes.Count > 1 ? new[] { "Face" } : Array.Empty<string>())
            .Concat(k.Sliders.Count > 0 ? new[] { "Shape" } : Array.Empty<string>())
            .Concat(k.Paints.Count > 1 ? new[] { "Paint" } : Array.Empty<string>()).Append("Body").ToArray()
        : new[] { "Hair", "Body" };
    string Section => Sections[Math.Clamp(d.Section, 0, Sections.Length - 1)];
    /// <summary>A cameo's picture under art/ui/create/, by the survivor's sex.</summary>
    string Art(string key) => $"{d.Sex.Key()}/{key}";

    /// <summary>How near each part frames the figure, and how far she is turned for it
    /// (her hair seen from the side, where a cut shows).</summary>
    float SectionZoom() => d.Step != LookStep ? 0 : Section switch { "Hair" => 0.55f, "Face" or "Shape" or "Paint" => 1f, _ => 0f };
    float SectionTurn() => d.Step != LookStep || Section != "Hair" ? 0 : d.HairStyle switch { "ponytail" => -1.4f, "braid" => -1.75f, _ => -0.95f };

    /// <summary>The figure framed for the step and part as they are now.</summary>
    public void FrameForStep() => G.FrameFigure(SectionZoom(), SectionTurn());

    /* ---------------------------------------------------------- the stage -- */

    /// <summary>The space the figure stands in: dragged, she turns; the wheel brings
    /// her near or takes her back; a double click goes to her face and back.</summary>
    Control Stage()
    {
        var s = new Control { Position = new Vector2(Inset + PanelW, 0), Size = new Vector2(1920 - 2 * (Inset + PanelW), 1080), MouseFilter = MouseFilterEnum.Stop, MouseDefaultCursorShape = CursorShape.Drag };
        s.GuiInput += e =>
        {
            switch (e)
            {
                case InputEventMouseButton { ButtonIndex: MouseButton.WheelUp, Pressed: true }: G.Turntable(0, 0.1f); break;
                case InputEventMouseButton { ButtonIndex: MouseButton.WheelDown, Pressed: true }: G.Turntable(0, -0.1f); break;
                case InputEventMouseButton { ButtonIndex: MouseButton.Left, DoubleClick: true }: G.FrameFigure(G.FigureZoom > 0.5f ? 0 : 1); break;
                case InputEventMouseMotion m when (m.ButtonMask & MouseButtonMask.Left) != 0: G.Turntable(m.Relative.X * 0.009f, 0); break;
            }
        };
        return s;
    }

    public override void _Process(double delta)
    {
        base._Process(delta);
        // The right stick turns her and brings her near.
        var look = Controls.Instance?.Look ?? Vector2.Zero;
        if (look != Vector2.Zero) G.Turntable(look.X * 2.8f * (float)delta, -look.Y * 1.1f * (float)delta);
    }

    /* ------------------------------------------------------------ the parts -- */

    /// <summary>The look's parts as the house's tabs (type, the part shown over the ember's
    /// underline), the triggers either side, as the Journal turns its sections.</summary>
    Control SectionTabs()
    {
        bool pad = Controls.Instance.UsingPad;
        var tabs = Kit.Tabs(Sections, Math.Clamp(d.Section, 0, Sections.Length - 1), k => Set(() => d.Section = k), 17, Sections.Length > 4 ? 22 : 30);
        // (LT and RT turn them; focus keeps to the choices)
        foreach (var b in tabs.GetChildren().OfType<Button>()) Nav.Skip(b);
        var row = Style.H(Style.Gap4, pad ? Style.PadButton("LT") : Style.Key(","), tabs, pad ? Style.PadButton("RT") : Style.Key("."));
        foreach (var c in row.GetChildren().OfType<Control>()) c.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        row.Alignment = BoxContainer.AlignmentMode.Center;
        return row;
    }

    Control Look(Archetype a) => (Section, Hero) switch
    {
        ("Hair", { } k) => HeroHair(k),
        ("Hair", null) => KitHair(a),
        ("Face", { } k) => HeroFace(k),
        ("Shape", { } k) => HeroShape(k),
        ("Paint", { } k) => HeroPaint(k),
        _ => LookBody(a),
    };

    Control LookBody(Archetype a)
    {
        // (a woman or a man is chosen on the first step, with the calling)
        var v = Style.V(Style.Gap2);
        if (!Her && Hero == null)
        {
            v.AddChild(Kit.Head("Beard"));
            v.AddChild(Flow(new[] { ("Bearded", d.Beard, (Action)(() => Set(() => d.Beard = true)), "beard:on"), ("Clean-shaven", !d.Beard, () => Set(() => d.Beard = false), "beard:off") }));
        }
        v.AddChild(Kit.Head("Skin"));
        v.AddChild(Beads(Lore.Skins, d.Skin, id => d.Skin = id, Bead.Kind.Skin, "#f2c4a8"));
        v.AddChild(Kit.Head($"Colours of {Their.ToLowerInvariant()} outfit"));
        v.AddChild(Flow(a.Palettes.Select(p => (p.Name, d.Palette == p.Id, (Action)(() => Set(() => d.Palette = p.Id)), $"palette:{p.Id}"))));
        v.AddChild(Kit.Head("Cloak"));
        v.AddChild(Beads(Lore.CloakDyes, d.Cloak, id => d.Cloak = id, Bead.Kind.Cloth, "#3a2a20"));
        return v;
    }

    /// <summary>The hero's own cuts as cameos (dyed the colour chosen), and the colours.</summary>
    Control HeroHair(HeroLook k)
    {
        var v = Style.V(Style.Gap2, Kit.Head($"{Their} hair"));
        // (large: a cut is told by its shape, which a small picture loses)
        var row = Grid(3);
        var dye = HairColour();
        foreach (var cut in k.Cuts)
            row.AddChild(new Cameo(Art($"hair_{cut.Id}"), cut.Name, d.HairStyle == cut.Id, () => Set(() => d.HairStyle = cut.Id), 136, dye, "lock"));
        v.AddChild(row);
        if (k.Beards.Count > 0)
        {
            // His beard, as his cuts: cameos dyed his hair's colour.
            v.AddChild(Kit.Head("Beard"));
            var beards = Grid(4);
            foreach (var b in k.Beards)
                beards.AddChild(new Cameo(Art($"beard_{b.Id}"), b.Name, d.BeardStyle == b.Id, () => Set(() => d.BeardStyle = b.Id), 100, dye, "mask"));
            v.AddChild(beards);
        }
        v.AddChild(Kit.Head("Colour"));
        v.AddChild(Beads(Lore.Hairs, d.Hair, id => d.Hair = id, Bead.Kind.Hair, OwnHair().ToHtml(false)));
        return v;
    }

    /// <summary>A kit body's hair: its cuts, its colours, and the hood over it.</summary>
    Control KitHair(Archetype a)
    {
        bool hidden = d.Archetype == "stalker" ? d.Model == "rogue_hooded" : d.Headgear && d.Archetype != "reaver";
        var v = Style.V(Style.Gap2, Kit.Head($"{Their} hair", hidden ? "under the hood" : null));
        var cuts = Flow(Lore.HairStyles(d.Sex).Append("none").Select(h => (HairNames.GetValueOrDefault(h, h), d.HairStyle == h, (Action)(() => Set(() => d.HairStyle = h)), $"cut:{h}")));
        if (hidden) cuts.Modulate = new Color(1, 1, 1, 0.5f);
        v.AddChild(cuts);
        v.AddChild(Beads(Lore.Hairs, d.Hair, id => d.Hair = id, Bead.Kind.Hair, "#6a5a48"));
        if (d.Archetype != "reaver")
        {
            v.AddChild(Kit.Head("Hood"));
            // (a hooded body of its own for the calling, or the calling's headgear)
            bool up = a.AltModel != null ? d.Model == a.Model : d.Headgear;
            if (a.AltModel != null || d.Archetype != "stalker")
                v.AddChild(Flow(new[] { ("Hood up", up, (Action)(() => Set(Hood(a, true))), "hood:up"), ("Hood down", !up, () => Set(Hood(a, false)), "hood:down") }));
        }
        return v;
    }

    /// <summary>Faces to start from (a face may bring its own skin and eyes), and the eyes' colour.</summary>
    Control HeroFace(HeroLook k)
    {
        var v = Style.V(8);
        if (k.Faces.Count > 1)
        {
            v.AddChild(Kit.Head($"{Their} face"));
            var grid = Grid(4);
            foreach (var f in k.Faces)
                grid.AddChild(new Cameo(Art($"face_{f.Id}"), f.Name, d.FaceShape == f.Id, () => Set(() => Choose(f)), 100, null, "mask"));
            v.AddChild(grid);
        }
        if (k.Eyes.Count > 1)
        {
            v.AddChild(Kit.Head("Eyes"));
            v.AddChild(Beads(k.Eyes, d.Eyes, id => d.Eyes = id, Bead.Kind.Eye, ""));
        }
        if (k.Sliders.Count > 0)
            v.AddChild(Style.Label("Shape it by hand in the next part.", Style.TextItalic, 15, Kit.Dim, false, HorizontalAlignment.Center, false));
        return v;
    }

    /// <summary>A face to start from, taken: its shape, and its skin and eyes where it has its own.</summary>
    void Choose(FaceShape f)
    {
        d.FaceShape = f.Id;
        d.Face = new Dictionary<string, double>(f.Shape);
        if (f.Skin is { } skin && Lore.Skins.Any(s => s.Id == skin)) d.Skin = skin;
        if (f.Eyes is { } eyes && Hero is { } k && k.Eyes.Any(e => e.Id == eyes)) d.Eyes = eyes;
    }

    /// <summary>The face shaped by hand: its groups as tabs, four to a row, and the
    /// group's sliders under them; the column to itself, so none is hidden.</summary>
    Control HeroShape(HeroLook k)
    {
        var v = Style.V(Style.Gap2);
        var groups = k.Sliders.Select(s => s.Group).Distinct().ToArray();
        int g = Math.Clamp(d.FaceGroup, 0, groups.Length - 1);
        v.AddChild(Kit.Head($"Shape {Their.ToLowerInvariant()} face"));
        // (the groups as words, the one shown over the ember's underline; no boxes)
        v.AddChild(Flow(groups.Select((name, i) => (name, g == i, (Action)(() => Set(() => d.FaceGroup = i)), $"group:{name}"))));
        v.AddChild(Style.Gap(Style.Gap1));
        foreach (var s in k.Sliders.Where(s => s.Group == groups[g]))
            v.AddChild(SliderRow(s));
        var preset = k.Faces.FirstOrDefault(f => f.Id == d.FaceShape) ?? k.Faces.FirstOrDefault();
        if (Shaped(k, preset))
        {
            var back = Nav.Id(Kit.Word(preset != null ? $"Back to {preset.Name.ToLowerInvariant()}" : $"Back to {Their.ToLowerInvariant()} own face",
                () => Set(() => d.Face = new Dictionary<string, double>(preset?.Shape ?? new())), Style.EmberHi, 16), "unshape");
            back.SizeFlagsHorizontal = SizeFlags.ShrinkCenter;
            v.AddChild(back);
        }
        return v;
    }

    /// <summary>The face moved from the face it started from.</summary>
    bool Shaped(HeroLook k, FaceShape? preset) =>
        k.Sliders.Any(s => Math.Abs(d.Face.GetValueOrDefault(s.Id) - (preset?.Shape.GetValueOrDefault(s.Id) ?? 0)) > 1e-3);

    /// <summary>One of her face's sliders: its name, the word for each end, and
    /// the groove between, her own face at its middle.</summary>
    Control SliderRow(FaceSlider s)
    {
        var g = new Groove(s.Min, s.Max, d.Face.GetValueOrDefault(s.Id));
        g.Changed += v => { if (Math.Abs(v) < 1e-3) d.Face.Remove(s.Id); else d.Face[s.Id] = Math.Round(v, 3); G.DressFigure(d); };
        g.Done += () => Refresh();
        Nav.Mark(g, $"slider:{s.Id}", null, adjust: dir => { g.Step(dir); Refresh(); });
        var name = Style.Label(s.Name, Style.UiBold, Style.Caption, Style.Ink);
        name.CustomMinimumSize = new Vector2(104, 0);
        var low = Style.Label(s.Low, Style.Ui, 13, Style.InkDim, false, HorizontalAlignment.Right);
        low.CustomMinimumSize = new Vector2(80, 0);
        var high = Style.Label(s.High, Style.Ui, 13, Style.InkDim);
        high.CustomMinimumSize = new Vector2(80, 0);
        // (the groove takes the room between its words, so every row runs the column's width)
        g.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        var row = Style.H(6, name, low, g, high);
        row.Alignment = BoxContainer.AlignmentMode.Begin;
        return row;
    }

    /// <summary>The paints as cameos (hers: bare, kohl, woad, ochre, ash, blood, gilt).</summary>
    Control HeroPaint(HeroLook k)
    {
        var v = Style.V(Style.Gap2, Kit.Head($"Paint on {Their.ToLowerInvariant()} face"));
        // (large: kohl and ash are fine lines a small picture loses)
        var grid = Grid(3);
        foreach (var p in k.Paints)
            grid.AddChild(new Cameo(Art($"paint_{p.Id}"), p.Name, d.Paint == p.Id, () => Set(() => d.Paint = p.Id), 136, null, "mask"));
        v.AddChild(grid);
        return v;
    }

    /// <summary>Cameos in rows, so many to a row, each row centred (a short last row sits in the
    /// middle, not against the left).</summary>
    static HFlowContainer Grid(int columns)
    {
        var g = new HFlowContainer { Alignment = FlowContainer.AlignmentMode.Center, MouseFilter = MouseFilterEnum.Ignore };
        g.AddThemeConstantOverride("h_separation", columns > 3 ? 6 : 10);
        g.AddThemeConstantOverride("v_separation", 2);
        return g;
    }

    /// <summary>Words to choose between, as the house's tabs in centred lines, each with its focus id.</summary>
    static HFlowContainer Flow(IEnumerable<(string Text, bool On, Action Press, string Id)> words)
    {
        var list = words.ToList();
        var f = Kit.TabFlow(list.Select(w => (w.Text, w.On, w.Press)), 16, 24, 4);
        int i = 0;
        foreach (var b in f.GetChildren().OfType<Button>()) Nav.Id(b, list[i++].Id);
        return f;
    }

    /// <summary>The hood up or down: the calling's hooded body where it has one, else its headgear.</summary>
    Action Hood(Archetype a, bool up) => () =>
    {
        if (a.AltModel != null) d.Model = up ? a.Model : a.AltModel;
        else d.Headgear = up;
    };

    /* ---------------------------------------------------------- colours -- */

    /// <summary>A row of colours as beads: skin as skin, hair as a lock's sheen,
    /// cloth as dyed wool, her eyes as irises; the one chosen ringed in gold.</summary>
    Control Beads(List<LookChoice> list, string now, Action<string> set, Bead.Kind kind, string own)
    {
        var wrap = new HFlowContainer { Alignment = FlowContainer.AlignmentMode.Center };
        wrap.AddThemeConstantOverride("h_separation", 6);
        wrap.AddThemeConstantOverride("v_separation", 6);
        foreach (var c in list)
        {
            var id = c.Id;
            var col = c.Color != "" ? new Color(c.Color) : own != "" ? new Color(own) : new Color("#6b8a3a");
            var b = new Bead(kind, col, c.Ring != "" ? new Color(c.Ring) : col, now == id, c.Color == "" && kind == Bead.Kind.Eye) { TooltipText = c.Name };
            Nav.Id(b, $"bead:{kind}:{id}");
            b.Pressed += () => Set(() => set(id));
            wrap.AddChild(b);
        }
        var v = Style.V(2, wrap, Style.Label(list.FirstOrDefault(c => c.Id == now)?.Name ?? "", Style.TextItalic, 15, Kit.Dim, false, HorizontalAlignment.Center, false));
        return v;
    }

    Color HairColour() => Lore.Hairs.FirstOrDefault(h => h.Id == d.Hair) is { Color: not "" } h ? new Color(h.Color) : OwnHair();

    /// <summary>Hair "as it grew": hers copper, a kit body's its paint's brown.</summary>
    Color OwnHair() => Her ? People.HerHairColour : new Color("#6a5a48");

    /* ------------------------------------------------------- read closely -- */

    /// <summary>The right-hand plate on the look step: the part's choice read
    /// closely, the whole likeness, and how to turn the figure and come near.</summary>
    Control LookDetail(Archetype a)
    {
        string title, name, words;
        var k = Hero;
        switch (Section)
        {
            case "Hair" when k != null:
                var cut = k.Cuts.FirstOrDefault(h => h.Id == d.HairStyle) ?? k.Cuts[0];
                (title, name, words) = ($"{Their} hair", cut.Name, cut.Words);
                break;
            case "Face" when k != null:
                var f = k.Faces.FirstOrDefault(x => x.Id == d.FaceShape) ?? k.Faces.FirstOrDefault();
                (title, name, words) = ($"{Their} face", (f?.Name ?? "Their own") + (Shaped(k, f) ? ", shaped" : ""), f?.Words ?? "");
                break;
            case "Shape" when k != null:
                var sf = k.Faces.FirstOrDefault(x => x.Id == d.FaceShape) ?? k.Faces.FirstOrDefault();
                var groups = k.Sliders.Select(s => s.Group).Distinct().ToArray();
                (title, name, words) = ($"{Their} face", (sf?.Name ?? "Their own") + (Shaped(k, sf) ? ", shaped" : ""),
                    groups.Length > 0 ? $"{groups[Math.Clamp(d.FaceGroup, 0, groups.Length - 1)]}: each slider runs from one end to the other, {Their.ToLowerInvariant()} chosen face at its middle." : "");
                break;
            case "Paint" when k != null:
                var p = k.Paints.FirstOrDefault(x => x.Id == d.Paint) ?? k.Paints[0];
                (title, name, words) = ("Paint", p.Name, p.Words);
                break;
            case "Hair":
                (title, name, words) = ($"{Their} hair", HairNames.GetValueOrDefault(d.HairStyle, d.HairStyle), d.Headgear && d.Archetype != "reaver" ? "Worn under the calling's hood." : "Worn as it grew.");
                break;
            default:
                (title, name, words) = ($"{Their} body", $"{a.Name}'s colours", a.Palettes.FirstOrDefault(x => x.Id == d.Palette)?.Name ?? "");
                break;
        }
        var v = Style.V(Style.Gap3, DTitle(title), DSub(name));
        if (words != "") v.AddChild(DBody(words));
        v.AddChild(Kit.RuleH());
        v.AddChild(Kit.Head($"{Their} likeness"));
        foreach (var (key, val) in Likeness()) v.AddChild(Line(key, val));
        v.AddChild(Kit.RuleH());
        // How to turn the figure and come near, for the device in hand.
        bool pad = Controls.Instance.UsingPad;
        string them = Her ? "her" : "him";
        Label Quiet(string t) => Style.Label(t, Style.Ui, 15, Kit.Dim, true, HorizontalAlignment.Left, false);
        if (pad)
        {
            var stick = Style.H(Style.Gap2, Style.PadButton("Right stick"), Quiet($"turns {them} and comes near"));
            foreach (var c in stick.GetChildren().OfType<Control>()) c.SizeFlagsVertical = SizeFlags.ShrinkCenter;
            v.AddChild(stick);
        }
        else v.AddChild(Quiet($"Drag to turn {them}; the wheel brings {them} near; a double click goes to {Their.ToLowerInvariant()} face."));
        return v;
    }

    /// <summary>The whole likeness, a line a part.</summary>
    IEnumerable<(string, string)> Likeness()
    {
        string Of(List<LookChoice> l, string id) => l.FirstOrDefault(c => c.Id == id)?.Name ?? id;
        var k = Hero;
        yield return ("Skin", Of(Lore.Skins, d.Skin));
        string cut = k != null ? k.Cuts.FirstOrDefault(h => h.Id == d.HairStyle)?.Name ?? d.HairStyle : HairNames.GetValueOrDefault(d.HairStyle, d.HairStyle);
        yield return ("Hair", $"{cut}, {Of(Lore.Hairs, d.Hair).ToLowerInvariant()}");
        if (k == null) yield break;
        if (k.Beards.Count > 0) yield return ("Beard", k.Beards.FirstOrDefault(b => b.Id == d.BeardStyle)?.Name ?? k.Beards[0].Name);
        var f = k.Faces.FirstOrDefault(x => x.Id == d.FaceShape) ?? k.Faces.FirstOrDefault();
        if (f != null || k.Sliders.Count > 0) yield return ("Face", (f?.Name ?? "Their own") + (Shaped(k, f) ? ", shaped" : ""));
        if (k.Eyes.Count > 0) yield return ("Eyes", Of(k.Eyes, d.Eyes));
        if (k.Paints.Count > 0) yield return ("Paint", k.Paints.FirstOrDefault(x => x.Id == d.Paint)?.Name ?? k.Paints[0].Name);
    }

    /// <summary>The look in a line (read back on the name step).</summary>
    string LookWords() => string.Join(" · ", Likeness().Select(l => l.Item2));
}

/// <summary>
/// A portrait in an iron ring (creation's cuts, faces and paints): her picture
/// painted from the model (art/ui/create/KEY.png; a cut's hair is painted grey
/// with its own mask, KEY_mask.png, and takes the colour chosen), its name
/// under it; the one chosen lit in ember. Without its picture, a glyph.
/// </summary>
public partial class Cameo : Button
{
    static Shader? shader;
    readonly int size;

    public Cameo(string key, string name, bool on, Action act, int size, Color? dye, string glyph)
    {
        this.size = size;
        FocusMode = FocusModeEnum.None;
        MouseDefaultCursorShape = CursorShape.PointingHand;
        CustomMinimumSize = new Vector2(size + 14, size + 46);
        foreach (var x in new[] { "normal", "hover", "pressed", "focus" }) AddThemeStyleboxOverride(x, new StyleBoxEmpty());
        Nav.Id(this, $"cameo:{key}");
        if (on) SetMeta("on", true);
        Pressed += act;
        var art = UiArt.Tex($"create/{key}.png", false);
        var ring = new Ring(size, on) { Position = new Vector2(7, 2) };
        if (art != null)
        {
            shader ??= GD.Load<Shader>("res://shaders/ui_cameo.gdshader");
            var m = new ShaderMaterial { Shader = shader };
            if (dye is Color c && UiArt.Tex($"create/{key}_mask.png", false) is { } mask)
            {
                m.SetShaderParameter("mask", mask);
                m.SetShaderParameter("dye", c);
                m.SetShaderParameter("dyed", 1f);
            }
            m.SetShaderParameter("lit", on ? 1f : 0f);
            var pic = new TextureRect
            {
                Texture = art, Material = m, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, TextureFilter = TextureFilterEnum.LinearWithMipmaps,
                Size = new Vector2(size, size) * 0.86f, Position = new Vector2(size, size) * 0.07f, MouseFilter = MouseFilterEnum.Ignore,
            };
            ring.AddChild(pic);
            ring.MoveChild(pic, 0);
        }
        else ring.Glyph = glyph;
        AddChild(ring);
        var label = Style.Label(name, on ? Style.UiBold : Style.Ui, Style.Caption, on ? Style.EmberHi : Style.Ink, true, HorizontalAlignment.Center);
        label.Position = new Vector2(0, size + 6);
        label.Size = new Vector2(size + 14, 40);
        label.CustomMinimumSize = new Vector2(size + 14, 0);
        AddChild(label);
        MouseEntered += () => ring.Hover = true;
        MouseExited += () => ring.Hover = false;
    }

    /// <summary>The ring round the picture: drawn under it (its dark ground and
    /// glow) and over it (the iron), the painted medallion ring where there is one.</summary>
    partial class Ring : Control
    {
        readonly int size;
        readonly bool on;
        public string? Glyph;
        bool hover;
        public bool Hover { set { hover = value; QueueRedraw(); over?.QueueRedraw(); } }
        Control? over;

        public Ring(int size, bool on)
        {
            this.size = size;
            this.on = on;
            CustomMinimumSize = Size = new Vector2(size, size);
            MouseFilter = MouseFilterEnum.Ignore;
        }

        public override void _Ready()
        {
            over = new Over(this) { Size = Size, MouseFilter = MouseFilterEnum.Ignore };
            AddChild(over);
        }

        public override void _Draw()
        {
            var c = Size / 2;
            float r = size / 2f;
            if (on) for (int i = 6; i >= 1; i--) DrawCircle(c, r + i * 2.2f, new Color(1, 0.45f, 0.15f, 0.06f));
            DrawCircle(c + new Vector2(0, 3), r, new Color(0, 0, 0, 0.55f));
            DrawCircle(c, r - 1, new Color("#120e10"));
            if (Glyph != null)
            {
                var t = Glyphs.Texture(Glyph, size * 2, on ? Style.EmberHi : Style.GoldDim);
                float g = size * 0.42f;
                DrawTextureRect(t, new Rect2(c - new Vector2(g / 2, g / 2), new Vector2(g, g)), false);
            }
        }

        partial class Over : Control
        {
            readonly Ring ring;
            public Over(Ring r) { ring = r; }
            public override void _Draw()
            {
                var c = Size / 2;
                float r = ring.size / 2f;
                var col = ring.on ? Style.Ember : ring.hover ? Style.GoldHi : Style.GoldDim;
                if (UiArt.Art("medallion/ring.png") is { } art)
                {
                    DrawArc(c, r * 0.88f, 0, Mathf.Tau, 64, col with { A = 0.9f }, 2, true);
                    DrawTextureRect(art, new Rect2(c - new Vector2(r, r) * 1.06f, new Vector2(r, r) * 2.12f), false);
                }
                else
                {
                    DrawArc(c, r - 2, 0, Mathf.Tau, 72, new Color("#060508"), 6, true);
                    DrawArc(c, r - 2, 0, Mathf.Tau, 72, col, 3, true);
                    DrawArc(c, r - 6, 0, Mathf.Tau, 72, col with { A = 0.35f }, 1, true);
                }
            }
        }
    }
}

/// <summary>A colour to choose as a bead: a sphere lit from the upper left, as
/// skin, as hair (a sheen across it, as along a lock), as dyed wool (matte), or
/// as an iris (its fibres, its ring round the pupil, a catchlight); the one
/// chosen ringed in gold with an ember glow.</summary>
public partial class Bead : Button
{
    public enum Kind { Skin, Hair, Cloth, Eye }
    readonly Kind kind;
    readonly Color colour, ring;
    readonly bool on, painted;
    static Texture2D? iris;
    static Shader? irisShader;

    public Bead(Kind kind, Color colour, Color ring, bool on, bool painted = false)
    {
        this.kind = kind;
        this.colour = colour;
        this.ring = ring;
        this.on = on;
        this.painted = painted;
        FocusMode = FocusModeEnum.None;
        MouseDefaultCursorShape = CursorShape.PointingHand;
        CustomMinimumSize = new Vector2(38, 38);
        foreach (var x in new[] { "normal", "hover", "pressed", "focus" }) AddThemeStyleboxOverride(x, new StyleBoxEmpty());
        if (on) SetMeta("on", true);
        MouseEntered += QueueRedraw;
        MouseExited += QueueRedraw;
        if (kind == Kind.Eye)
        {
            // Her iris itself, dyed as her eye shader dyes it (shaders/ui_iris.gdshader).
            iris ??= GD.Load<Texture2D>("res://art/people/head_tex/heroine_iris.png");
            irisShader ??= GD.Load<Shader>("res://shaders/ui_iris.gdshader");
            var m = new ShaderMaterial { Shader = irisShader };
            m.SetShaderParameter("recolour", painted ? 0f : 1f);
            m.SetShaderParameter("iris_colour", colour);
            m.SetShaderParameter("ring_colour", ring);
            AddChild(new TextureRect { Texture = iris, Material = m, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, Size = new Vector2(30, 30), Position = new Vector2(4, 4), MouseFilter = MouseFilterEnum.Ignore });
        }
    }

    public override void _Draw()
    {
        var c = Size / 2;
        float r = 15;
        bool hover = IsHovered();
        if (on) for (int i = 5; i >= 1; i--) DrawCircle(c, r + 2 + i * 1.6f, new Color(1, 0.45f, 0.15f, 0.07f));
        DrawCircle(c + new Vector2(0, 2), r + 1, new Color(0, 0, 0, 0.6f));
        if (kind != Kind.Eye)
        {
            // A sphere: its colour, darker toward its foot and edge, lighter toward the light.
            DrawCircle(c, r, colour.Darkened(0.45f));
            DrawCircle(c + new Vector2(-1.5f, -1.5f), r * 0.86f, colour.Darkened(0.15f));
            DrawCircle(c + new Vector2(-3, -3), r * 0.6f, colour);
            DrawCircle(c + new Vector2(-4.5f, -4.5f), r * 0.32f, colour.Lightened(kind == Kind.Cloth ? 0.06f : 0.14f));
            if (kind == Kind.Hair)
                // A lock's sheen: a band across it, as light lies along hair.
                DrawArc(c + new Vector2(0, 5), r * 0.78f, Mathf.Pi * 1.15f, Mathf.Pi * 1.85f, 24, colour.Lightened(0.35f) with { A = 0.7f }, 2.2f, true);
            else if (kind == Kind.Skin)
                DrawCircle(c + new Vector2(-5, -6), 2.2f, new Color(1, 1, 1, 0.35f));
        }
        else DrawArc(c, r - 0.5f, 0, Mathf.Tau, 48, new Color(0.02f, 0.02f, 0.03f, 0.8f), 2, true);
        var edge = on ? Style.GoldHi : hover ? Style.LineHi : new Color(0, 0, 0, 0.85f);
        DrawArc(c, r + (on ? 2.5f : 0.5f), 0, Mathf.Tau, 48, edge, on ? 2.5f : 1.2f, true);
    }
}

/// <summary>One of her face's sliders: a groove from one end to the other with
/// her own face marked at its middle, gold drawn from the middle to where it
/// is set. Dragged (or a click on the groove), it moves; with focus, left and
/// right move it a tenth.</summary>
public partial class Groove : Control
{
    readonly double min, max;
    /// <summary>Where it is set, -1 to 1 (its ends are min and max).</summary>
    float at;
    bool dragging;
    public event Action<double>? Changed;
    public event Action? Done;

    public Groove(double min, double max, double value)
    {
        this.min = min;
        this.max = max;
        at = (float)(value >= 0 ? (max > 0 ? value / max : 0) : (min < 0 ? -value / min : 0));
        CustomMinimumSize = new Vector2(196, 26);
        MouseFilter = MouseFilterEnum.Stop;
        MouseDefaultCursorShape = CursorShape.PointingHand;
    }

    double Value => at >= 0 ? at * max : -at * min;

    public void Step(int dir)
    {
        at = Mathf.Clamp(Mathf.Round((at + dir * 0.1f) * 10) / 10, min < 0 ? -1 : 0, max > 0 ? 1 : 0);
        Changed?.Invoke(Value);
        QueueRedraw();
    }

    public override void _GuiInput(InputEvent e)
    {
        switch (e)
        {
            case InputEventMouseButton { ButtonIndex: MouseButton.Left } b:
                dragging = b.Pressed;
                if (b.Pressed) Move(b.Position.X);
                else Done?.Invoke();
                AcceptEvent();
                break;
            case InputEventMouseMotion m when dragging:
                Move(m.Position.X);
                AcceptEvent();
                break;
        }
    }

    void Move(float x)
    {
        float pad = 9, w = Size.X - pad * 2;
        float v = Mathf.Clamp((x - pad) / w * 2 - 1, min < 0 ? -1 : 0, max > 0 ? 1 : 0);
        // (a little stick at her own face, so it can be found again by hand)
        if (Mathf.Abs(v) < 0.04f) v = 0;
        if (Mathf.IsEqualApprox(v, at)) return;
        at = v;
        Changed?.Invoke(Value);
        QueueRedraw();
    }

    public override void _Draw()
    {
        float pad = 9, w = Size.X - pad * 2, y = Size.Y / 2;
        float X(float v) => pad + (v + 1) / 2 * w;
        // The groove, sunk; her own face at its middle; the gold from the middle to the knob.
        DrawRect(new Rect2(pad, y - 3, w, 6), new Color("#0b0a0d"));
        DrawRect(new Rect2(pad, y - 3, w, 1), new Color(0, 0, 0, 0.8f));
        DrawRect(new Rect2(pad, y + 2, w, 1), Style.Line with { A = 0.25f });
        float lo = min < 0 ? X(-1) : X(0), hi = max > 0 ? X(1) : X(0);
        if (lo > pad) DrawRect(new Rect2(pad, y - 3, lo - pad, 6), new Color(0, 0, 0, 0.6f));
        DrawRect(new Rect2(X(0) - 1, y - 7, 2, 14), Style.GoldDim);
        float k = X(at);
        if (Mathf.Abs(at) > 0.001f) DrawRect(new Rect2(Mathf.Min(k, X(0)), y - 2, Mathf.Abs(k - X(0)), 4), new Color("#d0a858"));
        bool hot = dragging || IsHovered();
        DrawCircle(new Vector2(k, y + 1.5f), 8, new Color(0, 0, 0, 0.6f));
        DrawCircle(new Vector2(k, y), 7.5f, new Color("#6a4a14"));
        DrawCircle(new Vector2(k, y), 6, hot ? Style.EmberHi : Style.GoldHi);
        DrawCircle(new Vector2(k - 1.5f, y - 1.5f), 2.2f, new Color(1, 1, 1, 0.5f));
    }

    bool IsHovered() => GetGlobalRect().HasPoint(GetGlobalMousePosition());
}

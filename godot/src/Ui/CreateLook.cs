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
 * paint and body, each a part of its own on the triggers, the figure framed
 * for it (head and shoulders, the face, all of them) and turned or brought
 * near by hand. Hair comes first: it is what a player looks for, and it shows
 * at once that she is theirs to shape. A hero's own body (the heroine's; the male hero's when he has
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
        ? new[] { "Hair" }.Concat(k.Sliders.Count > 0 || k.Faces.Count > 1 || k.Eyes.Count > 1 ? new[] { "Face" } : Array.Empty<string>())
            .Concat(k.Paints.Count > 1 ? new[] { "Paint" } : Array.Empty<string>()).Append("Body").ToArray()
        : new[] { "Hair", "Body" };
    string Section => Sections[Math.Clamp(d.Section, 0, Sections.Length - 1)];
    /// <summary>A cameo's picture under art/ui/create/, by the survivor's sex.</summary>
    string Art(string key) => $"{d.Sex.Key()}/{key}";

    /// <summary>How near each part frames the figure, and how far she is turned for it
    /// (her hair seen from the side, where a cut shows).</summary>
    float SectionZoom() => d.Step != LookStep ? 0 : Section switch { "Hair" => 0.55f, "Face" or "Paint" => 1f, _ => 0f };
    float SectionTurn() => d.Step != LookStep || Section != "Hair" ? 0 : d.HairStyle switch { "ponytail" => -1.4f, "braid" => -1.75f, _ => -0.95f };

    /// <summary>The figure framed for the step and part as they are now.</summary>
    public void FrameForStep() => G.FrameFigure(SectionZoom(), SectionTurn());

    /* ---------------------------------------------------------- the stage -- */

    /// <summary>The space the figure stands in: dragged, she turns; the wheel brings
    /// her near or takes her back; a double click goes to her face and back.</summary>
    Control Stage()
    {
        var s = new Control { Position = new Vector2(590, 0), Size = new Vector2(790, 950), MouseFilter = MouseFilterEnum.Stop, MouseDefaultCursorShape = CursorShape.Drag };
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

    /// <summary>The look's parts as a row of tabs, the triggers either side.</summary>
    Control SectionTabs()
    {
        bool pad = Controls.Instance.UsingPad;
        var row = Style.H(4);
        row.Alignment = BoxContainer.AlignmentMode.Center;
        var lt = pad ? Style.PadButton("LT") : Style.Key(",");
        lt.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        row.AddChild(lt);
        for (int i = 0; i < Sections.Length; i++)
        {
            int at = i;
            bool on = d.Section == i;
            var b = Style.Button("", () => Set(() => d.Section = at), false, true);
            b.CustomMinimumSize = new Vector2(Sections.Length > 2 ? 96 : 140, 40);
            foreach (var x in new[] { "normal", "hover", "pressed" }) b.AddThemeStyleboxOverride(x, new StyleBoxEmpty());
            Nav.Skip(b);
            var v = Style.V(3, Style.Label(Sections[i].ToUpperInvariant(), Style.Display, 16, on ? Style.EmberHi : Style.GoldDim, false, HorizontalAlignment.Center));
            // (the part shown: an ember rule under its name)
            v.AddChild(new ColorRect { Color = on ? Style.Ember : Style.Line with { A = 0.2f }, CustomMinimumSize = new Vector2(0, on ? 2 : 1), MouseFilter = MouseFilterEnum.Ignore });
            v.MouseFilter = MouseFilterEnum.Ignore;
            v.SetAnchorsPreset(LayoutPreset.FullRect);
            v.Alignment = BoxContainer.AlignmentMode.Center;
            b.AddChild(v);
            row.AddChild(b);
        }
        var rt = pad ? Style.PadButton("RT") : Style.Key(".");
        rt.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        row.AddChild(rt);
        return row;
    }

    Control Look(Archetype a) => (Section, Kit) switch
    {
        ("Hair", { } k) => HeroHair(k),
        ("Hair", null) => KitHair(a),
        ("Face", { } k) => HeroFace(k),
        ("Paint", { } k) => HeroPaint(k),
        _ => LookBody(a),
    };

    Control LookBody(Archetype a)
    {
        // (a woman or a man is chosen on the first step, with the calling)
        var v = Style.V(8);
        if (!Her && Kit == null)
        {
            v.AddChild(Style.SubLabel("Beard"));
            v.AddChild(Nav.Id(Style.Segment(d.Beard ? "Bearded" : "Clean-shaven", d.Beard, () => Set(() => d.Beard = !d.Beard)), "beard"));
        }
        v.AddChild(Style.SubLabel("Skin"));
        v.AddChild(Beads(Lore.Skins, d.Skin, id => d.Skin = id, Bead.Kind.Skin, "#f2c4a8"));
        v.AddChild(Style.SubLabel($"Colours of {Their.ToLowerInvariant()} outfit"));
        var pal = new GridContainer { Columns = 2 };
        pal.AddThemeConstantOverride("h_separation", 6);
        pal.AddThemeConstantOverride("v_separation", 6);
        foreach (var p in a.Palettes) pal.AddChild(Style.Segment(p.Name, d.Palette == p.Id, () => Set(() => d.Palette = p.Id)));
        v.AddChild(pal);
        v.AddChild(Style.SubLabel("Cloak"));
        v.AddChild(Beads(Lore.CloakDyes, d.Cloak, id => d.Cloak = id, Bead.Kind.Cloth, "#3a2a20"));
        return v;
    }

    /// <summary>The hero's own cuts as cameos (dyed the colour chosen), and the colours.</summary>
    Control HeroHair(HeroLook k)
    {
        var v = Style.V(8, Style.SubLabel($"{Their} hair"));
        // (large: a cut is told by its shape, which a small picture loses)
        var row = Grid(3);
        var dye = HairColour();
        foreach (var cut in k.Cuts)
            row.AddChild(new Cameo(Art($"hair_{cut.Id}"), cut.Name, d.HairStyle == cut.Id, () => Set(() => d.HairStyle = cut.Id), 136, dye, "lock"));
        v.AddChild(row);
        v.AddChild(Style.Gap(4));
        v.AddChild(Style.SubLabel("Colour"));
        v.AddChild(Beads(Lore.Hairs, d.Hair, id => d.Hair = id, Bead.Kind.Hair, OwnHair().ToHtml(false)));
        return v;
    }

    /// <summary>A kit body's hair: its cuts, its colours, and the hood over it.</summary>
    Control KitHair(Archetype a)
    {
        bool hidden = d.Archetype == "stalker" ? d.Model == "rogue_hooded" : d.Headgear && d.Archetype != "reaver";
        var v = Style.V(8, Style.H(8, Style.SubLabel($"{Their} hair"), hidden ? Style.Label("under the hood", Style.TextItalic, 13, Style.InkDim) : new Control()));
        var cuts = Style.H(4);
        foreach (var h in Lore.HairStyles(d.Sex).Append("none")) cuts.AddChild(Style.Segment(HairNames.GetValueOrDefault(h, h), d.HairStyle == h, () => Set(() => d.HairStyle = h)));
        if (hidden) cuts.Modulate = new Color(1, 1, 1, 0.5f);
        v.AddChild(cuts);
        v.AddChild(Beads(Lore.Hairs, d.Hair, id => d.Hair = id, Bead.Kind.Hair, "#6a5a48"));
        if (d.Archetype != "reaver")
        {
            v.AddChild(Style.SubLabel("Hood"));
            if (a.AltModel != null) v.AddChild(Style.Button(d.Model == a.Model ? "Hood up" : "Hood down", () => Set(() => d.Model = d.Model == a.Model ? a.AltModel! : a.Model), false, true));
            if (d.Archetype != "stalker") v.AddChild(Style.Button(d.Headgear ? "Hood up" : "Hood down", () => Set(() => d.Headgear = !d.Headgear), false, true));
        }
        return v;
    }

    /// <summary>Faces to start from, the eyes' colour, and the face shaped by hand.</summary>
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
        var row = Style.H(6, name, low, g, high);
        row.Alignment = BoxContainer.AlignmentMode.Begin;
        return row;
    }

    /// <summary>The paints as cameos (hers: bare, kohl, woad, ochre, ash, blood, gilt).</summary>
    Control HeroPaint(HeroLook k)
    {
        var v = Style.V(8, Style.SubLabel($"Paint on {Their.ToLowerInvariant()} face"));
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
    }

    /* ---------------------------------------------------------- colours -- */

    /// <summary>A row of colours as beads: skin as skin, hair as a lock's sheen,
    /// cloth as dyed wool, her eyes as irises; the one chosen ringed in gold.</summary>
    Control Beads(List<LookChoice> list, string now, Action<string> set, Bead.Kind kind, string own)
    {
        var wrap = new HFlowContainer();
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
        var v = Style.V(2, wrap, Style.Label(list.FirstOrDefault(c => c.Id == now)?.Name ?? "", Style.TextItalic, Style.Caption, Style.InkDim));
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
        var k = Kit;
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
        var v = Style.V(8, Style.Cap(title, 24), Style.Label(name, Style.Display, 20, Style.GoldHi), Style.Label(words, Style.TextItalic, 16, new Color("#c8a878"), true), Style.Rule());
        v.AddChild(Style.SubLabel($"{Their} likeness"));
        foreach (var (key, val) in Likeness()) v.AddChild(Line(key, val));
        v.AddChild(Style.Rule());
        // How to turn the figure and come near, for the device in hand.
        bool pad = Controls.Instance.UsingPad;
        string them = Her ? "her" : "him";
        v.AddChild(pad ? Style.H(8, Style.PadButton("Right stick"), Style.Label($"turn {them}, come near", Style.Ui, Style.Caption, Style.InkDim))
            : Style.Label($"Drag to turn {them}; the wheel brings {them} near; a double click goes to {Their.ToLowerInvariant()} face.", Style.Ui, Style.Caption, Style.InkDim, true));
        if (Sections.Length > 1)
            v.AddChild(Style.H(8, pad ? Style.PadButton("LT") : Style.Key(","), pad ? Style.PadButton("RT") : Style.Key("."), Style.Label("the parts of the look", Style.Ui, Style.Caption, Style.InkDim)));
        return v;
    }

    /// <summary>The whole likeness, a line a part.</summary>
    IEnumerable<(string, string)> Likeness()
    {
        string Of(List<LookChoice> l, string id) => l.FirstOrDefault(c => c.Id == id)?.Name ?? id;
        var k = Kit;
        yield return ("Skin", Of(Lore.Skins, d.Skin));
        string cut = k != null ? k.Cuts.FirstOrDefault(h => h.Id == d.HairStyle)?.Name ?? d.HairStyle : HairNames.GetValueOrDefault(d.HairStyle, d.HairStyle);
        yield return ("Hair", $"{cut}, {Of(Lore.Hairs, d.Hair).ToLowerInvariant()}");
        if (k == null) yield break;
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

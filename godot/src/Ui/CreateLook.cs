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

/* Creation's second screen, her look and her name, all on one page (docs/UI_DESIGN.md 7.2).
 * No sliders: her face and her cut are numbered cycles (Face 3/10, Hair 1/3: no names; the
 * arrows, or left and right, turn them), a face chosen whole (its shape, and its skin and eyes
 * where it brings its own); her hair's colour, her eyes (irises drawn as irises) and her skin
 * are beads; the paint on her face is a cycle too (No paint, Paint 1/7...); then her name on its
 * rule. The figure is framed for the row last touched (d.Section): the face's rows bring her
 * face near, the hair's show her head and shoulders, turned so the cut shows; she is turned and
 * brought near by hand as well. A kit body (no HeroKit: the man, until his own model ships) is
 * not offered; it gets a plain fallback here (a cut, its colour, the skin, the name). */
public partial class CreateScreen
{
    bool Her => d.Sex == Sex.Female;
    /// <summary>"Her" or "His", as the survivor is.</summary>
    string Their => Her ? "Her" : "His";
    /// <summary>What their own body offers to be shaped with (null: a kit body).</summary>
    HeroLook? Hero => Loadouts.HeroKit(d.Sex);

    /// <summary>The look's rows by how they frame her (d.Section on the second screen): the
    /// face's (face, eyes, skin, paint) and the hair's (its cut and its colour).</summary>
    public const int LookFace = 0, LookHair = 1;

    /// <summary>How near the figure is framed, and how far she is turned (her hair seen from the side,
    /// where a cut shows): all of her on the first screen; on the second, by the row last touched.</summary>
    /// (a pixie is short: her head is brought nearer for it, to fill the frame as a braid's length does)
    float SectionZoom() => d.Step != LookStep ? 0 : d.Section != LookHair ? 1f : d.HairStyle == "pixie" ? 0.75f : 0.55f;
    float SectionTurn() => d.Step != LookStep || d.Section != LookHair ? 0 : d.HairStyle switch { "ponytail" => -1.4f, "braid" => -1.75f, _ => -0.95f };

    /// <summary>The figure framed for the screen and row as they are now; on the look, her weapon and
    /// shield put away, so nothing stands in front of her face and hair.</summary>
    public void FrameForStep()
    {
        G.FrameFigure(SectionZoom(), SectionTurn());
        G.FigureArms(d.Step != LookStep);
    }

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

    /* ------------------------------------------------------------ the look -- */

    Control Look() => Hero is { } k ? OwnLook(k) : KitLook();

    /// <summary>Her own body's look, row by row: face, hair, its colour, eyes, skin, paint, name.</summary>
    Control OwnLook(HeroLook k)
    {
        var v = Style.V(Style.Gap2);
        if (k.Faces.Count > 0)
        {
            int f = Math.Max(0, k.Faces.FindIndex(x => x.Id == d.FaceShape));
            v.AddChild(Kit.Head("Face"));
            v.AddChild(Cycle($"Face {f + 1}/{k.Faces.Count}", f, k.Faces.Count, i => Set(() => { d.Section = LookFace; Choose(k.Faces[i]); }), "cycle:face"));
        }
        if (k.Cuts.Count > 0)
        {
            int c = Math.Max(0, k.Cuts.FindIndex(x => x.Id == d.HairStyle));
            v.AddChild(Kit.Head("Hair"));
            v.AddChild(Cycle($"Hair {c + 1}/{k.Cuts.Count}", c, k.Cuts.Count, i => Set(() => { d.Section = LookHair; d.HairStyle = k.Cuts[i].Id; }), "cycle:hair"));
        }
        v.AddChild(Kit.Head("Hair color"));
        v.AddChild(Beads(Lore.Hairs, d.Hair, id => { d.Section = LookHair; d.Hair = id; }, Bead.Kind.Hair, OwnHair().ToHtml(false)));
        // (highlights: a second colour on some of her locks, off by default; on, her hair colour's own until one is
        // picked (copper on black, honey on brown, platinum on blonde: Lore.DefaultHighlight))
        // (parked, face 40: the row hidden while Lore.ShowHighlights is off; a saved highlight loads but shows off)
        if ((Lore.ShowHighlights || Lore.ForceHighlights) && Lore.HairHighlights.Count > 0)
        {
            bool on = d.HairHighlight != "";
            v.AddChild(Kit.Head("Highlights"));
            v.AddChild(Cycle(on ? "Highlights on" : "No highlights", on ? 1 : 0, 2, i => Set(() => { d.Section = LookHair; d.HairHighlight = i == 1 ? Lore.HighlightAuto : ""; }), "cycle:highlight"));
            if (on)
            {
                var shown = d.HairHighlight == Lore.HighlightAuto ? Lore.DefaultHighlight(d.Hair) : d.HairHighlight;
                v.AddChild(Beads(Lore.HairHighlights, shown, id => { d.Section = LookHair; d.HairHighlight = id; }, Bead.Kind.Hair, "", ":highlight"));
            }
        }
        if (k.Eyes.Count > 1)
        {
            v.AddChild(Kit.Head("Eyes"));
            v.AddChild(Beads(k.Eyes, d.Eyes, id => { d.Section = LookFace; d.Eyes = id; d.EyesPicked = true; }, Bead.Kind.Eye, ""));
        }
        v.AddChild(Kit.Head("Skin"));
        v.AddChild(Beads(Lore.Skins, d.Skin, id => { d.Section = LookFace; d.Skin = id; d.SkinPicked = true; }, Bead.Kind.Skin, "#f2c4a8"));
        if (k.Paints.Count > 1)
        {
            // (the first is bare, "No paint"; the rest numbered from one)
            int p = Math.Max(0, k.Paints.FindIndex(x => x.Id == d.Paint));
            v.AddChild(Kit.Head("Paint"));
            v.AddChild(Cycle(p == 0 ? "No paint" : $"Paint {p}/{k.Paints.Count - 1}", p, k.Paints.Count, i => Set(() => { d.Section = LookFace; d.Paint = k.Paints[i].Id; }), "cycle:paint"));
        }
        v.AddChild(NameRow());
        return v;
    }

    /// <summary>A kit body's look (not offered: the man until his own model ships): a cut, its colour, the skin, the name.</summary>
    Control KitLook()
    {
        var cuts = Lore.HairStyles(d.Sex).Append("none").ToList();
        int c = Math.Max(0, cuts.IndexOf(d.HairStyle));
        return Style.V(Style.Gap2,
            Kit.Head("Hair"), Cycle($"Hair {c + 1}/{cuts.Count}", c, cuts.Count, i => Set(() => { d.Section = LookHair; d.HairStyle = cuts[i]; }), "cycle:hair"),
            Kit.Head("Hair color"), Beads(Lore.Hairs, d.Hair, id => { d.Section = LookHair; d.Hair = id; }, Bead.Kind.Hair, "#6a5a48"),
            Kit.Head("Skin"), Beads(Lore.Skins, d.Skin, id => { d.Section = LookFace; d.Skin = id; d.SkinPicked = true; }, Bead.Kind.Skin, "#f2c4a8"),
            NameRow());
    }

    /// <summary>A face to start from, taken: its shape, and its skin and eyes where it has its own and the
    /// player has not yet chosen them (a face never undoes a choice made in its rows).</summary>
    void Choose(FaceShape f)
    {
        d.FaceShape = f.Id;
        d.Face = new Dictionary<string, double>(f.Shape);
        if (!d.SkinPicked && f.Skin is { } skin && Lore.Skins.Any(s => s.Id == skin)) d.Skin = skin;
        if (!d.EyesPicked && f.Eyes is { } eyes && Hero is { } k && k.Eyes.Any(e => e.Id == eyes)) d.Eyes = eyes;
    }

    /// <summary>Their name, written on a rule as a name is signed in a ledger (no field's box), and
    /// one from the road beside it. The keyboard types at once; a pad, which cannot type, is offered names.</summary>
    Control NameRow()
    {
        var box = nameBox = new LineEdit { Text = d.Name, PlaceholderText = "Your name", MaxLength = 18, CustomMinimumSize = new Vector2(300, 44), SizeFlagsHorizontal = SizeFlags.ExpandFill };
        Style.Font(box, Style.Display, 26, Kit.Ink, false);
        box.AddThemeColorOverride("font_placeholder_color", Kit.Faint);
        box.AddThemeColorOverride("caret_color", Style.EmberHi);
        StyleBoxFlat Ruled(Color c) => new() { BgColor = Colors.Transparent, BorderColor = c, BorderWidthBottom = 1, ContentMarginLeft = 10, ContentMarginRight = 2, ContentMarginTop = 4, ContentMarginBottom = 6 };
        box.AddThemeStyleboxOverride("normal", Ruled(Kit.Edge));
        box.AddThemeStyleboxOverride("focus", Ruled(Style.Ember));
        box.TextChanged += t =>
        {
            var clean = new string(t.Where(c => char.IsLetter(c) || c is '\'' or ' ' or '-').ToArray());
            d.Name = clean;
            if (clean != t) { box.Text = clean; box.CaretColumn = clean.Length; }
        };
        box.TextSubmitted += _ => Begin();
        void Type() { if (GodotObject.IsInstanceValid(box) && box.IsInsideTree()) box.GrabFocus(); }
        // (moving by keys, the name is a row like the rest: come to it and type; A on a pad begins.
        // Its focus is its own rule lit in ember: the nav's line lies along it)
        Nav.Underlined(Nav.Mark(box, "name", Begin, focus: () => { if (!Controls.Instance.UsingPad) Type(); }));
        var road = Nav.Id(Kit.Word("A name from the road", () => Set(() => d.Name = Names[Random.Shared.Next(Names.Length)]), Style.EmberHi, 16), "roadname");
        road.SizeFlagsVertical = SizeFlags.ShrinkEnd;
        // (never taken at once: the rows above are reached first; a click or the keys come to the name)
        return Style.V(Style.Gap2, Kit.Head("Name"), Style.H(Style.Gap4, box, road));
    }

    /// <summary>A choice turned through with arrows, its value between them (Face 3/10): drawn
    /// chevrons either side, ember under the pointer or the focus, the value centred in a fixed
    /// width so the arrows never move. It wraps round. Left and right turn it with keys or a pad.</summary>
    Control Cycle(string value, int index, int count, Action<int> pick, string id)
    {
        void Turn(int dir)
        {
            if (count < 2) return;
            Sound.Sfx.Page();
            pick(((index + dir) % count + count) % count);
        }
        var prev = new Chevron(-1, () => Turn(-1));
        var next = new Chevron(1, () => Turn(1));
        var label = Style.Label(value, Style.Display, 20, Kit.Ink, false, HorizontalAlignment.Center, false);
        label.CustomMinimumSize = new Vector2(176, 0);
        label.VerticalAlignment = VerticalAlignment.Center;
        label.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        label.MouseFilter = MouseFilterEnum.Ignore;
        var row = Style.H(Style.Gap2, prev, label, next);
        row.Alignment = BoxContainer.AlignmentMode.Center;
        row.SizeFlagsHorizontal = SizeFlags.ShrinkCenter;
        row.MouseFilter = MouseFilterEnum.Pass;
        // (what it shows is chosen: Enter or A on it walks on, as on a choice already taken)
        row.SetMeta("on", true);
        Nav.Own(row);
        Nav.Mark(row, id, null, focus: () => prev.Lit = next.Lit = true, blur: () => prev.Lit = next.Lit = false, adjust: Turn);
        return row;
    }

    /* ---------------------------------------------------------- colours -- */

    /// <summary>A row of colours as beads: skin as skin, hair as a lock's sheen, her eyes as irises; the
    /// one chosen ringed in gold. More than a line holds is laid as two even rows, the second centred under
    /// the first. The name under them is the focused bead's, else the chosen one's. Skin carries no name
    /// anywhere (the owner: no name that could read as race) and is laid light to deep.</summary>
    Control Beads(List<LookChoice> list, string now, Action<string> set, Bead.Kind kind, string own, string tag = "")
    {
        Color Of(LookChoice c) => c.Color != "" ? new Color(c.Color) : own != "" ? new Color(own) : new Color("#6b8a3a");
        bool named = kind != Bead.Kind.Skin;
        if (!named) list = list.OrderByDescending(c => Of(c).Luminance).ToList();
        string chosen = named ? list.FirstOrDefault(c => c.Id == now)?.Name ?? "" : "";
        var caption = Style.Label(chosen, Style.TextItalic, 15, Kit.Dim, false, HorizontalAlignment.Center, false);
        // (a bead is 38 wide and 6 apart: as many as the column's 500 px hold to a line)
        const int perLine = 11;
        int lines = (list.Count + perLine - 1) / perLine, each = (list.Count + lines - 1) / Math.Max(1, lines);
        var rows = Style.V(6);
        HBoxContainer? line = null;
        for (int i = 0; i < list.Count; i++)
        {
            if (i % each == 0)
            {
                line = Style.H(6);
                line.Alignment = BoxContainer.AlignmentMode.Center;
                rows.AddChild(line);
            }
            var c = list[i];
            var id = c.Id;
            var col = Of(c);
            var b = new Bead(kind, col, c.Ring != "" ? new Color(c.Ring) : col, now == id, c.Color == "" && kind == Bead.Kind.Eye);
            if (named) b.TooltipText = c.Name;
            void Take() => Set(() => set(id));
            Nav.Loud(Nav.Rounded(b, 21));
            Nav.Mark(b, $"bead:{kind}{tag}:{id}", Take, focus: named ? () => caption.Text = c.Name : null, blur: named ? () => { if (IsInstanceValid(caption)) caption.Text = chosen; } : null);
            b.Pressed += Take;
            line!.AddChild(b);
        }
        return named ? Style.V(2, rows, caption) : rows;
    }

    /// <summary>Hair "as it grew": hers copper, a kit body's its paint's brown.</summary>
    /// (hers as her copper reads on her at the fire, lighter than its paint: the bead is shaded darker toward its edge)
    Color OwnHair() => Her ? new Color("#a4551f") : new Color("#6a5a48");

    /* ------------------------------------------------------- read closely -- */

    /// <summary>The right-hand plate on the second screen: who they are, read back, and how to
    /// turn the figure and come near.</summary>
    Control LookDetail(Archetype a)
    {
        var v = Summary(a);
        v.AddChild(Kit.RuleH());
        bool pad = Controls.Instance.UsingPad;
        string them = Her ? "her" : "him";
        Label Quiet(string t) => Style.Label(t, Style.Ui, 15, Kit.Dim, true, HorizontalAlignment.Left, false);
        if (pad)
        {
            var stick = Style.H(Style.Gap2, Style.PadButton("RS"), Quiet($"turns {them} and comes near"));
            foreach (var c in stick.GetChildren().OfType<Control>()) c.SizeFlagsVertical = SizeFlags.ShrinkCenter;
            v.AddChild(stick);
        }
        else v.AddChild(Quiet($"Drag to turn {them}; the wheel brings {them} near; a double click goes to {Their.ToLowerInvariant()} face."));
        return v;
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
        // (the choice made: a plain gold ring, no glow; the focus, drawn by Nav, is the louder)
        var edge = on ? Style.GoldHi : hover ? Style.LineHi : new Color(0, 0, 0, 0.85f);
        DrawArc(c, r + (on ? 2f : 0.5f), 0, Mathf.Tau, 48, edge, on ? 2f : 1.2f, true);
    }
}

/// <summary>An arrow either side of a cycle's value (creation's Face 3/10): a fine chevron
/// drawn in the panel's ink, ember under the pointer or while its cycle has the focus. No box.</summary>
public partial class Chevron : Button
{
    readonly int dir;
    bool lit;
    /// <summary>Lit while its cycle has the focus.</summary>
    public bool Lit { get => lit; set { lit = value; if (IsInstanceValid(this)) QueueRedraw(); } }

    public Chevron(int dir, Action press)
    {
        this.dir = dir;
        FocusMode = FocusModeEnum.None;
        Flat = true;
        MouseDefaultCursorShape = CursorShape.PointingHand;
        CustomMinimumSize = new Vector2(32, 34);
        foreach (var x in new[] { "normal", "hover", "pressed", "focus" }) AddThemeStyleboxOverride(x, new StyleBoxEmpty());
        MouseEntered += QueueRedraw;
        MouseExited += QueueRedraw;
        Pressed += press;
    }

    public override void _Draw()
    {
        var c = Size / 2;
        var ink = IsHovered() || lit ? Style.EmberHi : Kit.Ink2;
        var pts = new[] { c + new Vector2(-3.5f * dir, -8), c + new Vector2(4 * dir, 0), c + new Vector2(-3.5f * dir, 8) };
        // (a soft shade under it, so it holds over a bright world through the panel's ground)
        DrawPolyline(pts.Select(p => p + new Vector2(0, 1.5f)).ToArray(), new Color(0, 0, 0, 0.55f), 3.2f, true);
        DrawPolyline(pts, ink, 2.2f, true);
    }
}

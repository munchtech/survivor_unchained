R = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui'
p = R + r'\Panels.cs'
s = open(p, encoding='utf-8').read()

def rep(old, new):
    global s
    assert old in s, old[:90]
    s = s.replace(old, new, 1)

rep("""        var box = Style.Panel(Style.Plate(22));
        box.Position = new Vector2(240, 1080 - 40 - 420);
        box.Size = new Vector2(1440, 420);
        AddChild(box);
        var row = Style.H(28);
        box.AddChild(row);
        // Who.
        var who = Style.V(4);
        who.CustomMinimumSize = new Vector2(230, 0);
        var frame = Style.Panel(Style.Box(new Color(0.03f, 0.025f, 0.04f), Style.Line, 1, 6, 0));
        frame.CustomMinimumSize = new Vector2(228, 274);
        if (d.Person != null) frame.AddChild(new Portrait(new Vector2I(228, 274), Portrait.Framing.Bust).Of(d.Person, d.Arms, d.Scale));
        else
        {
            var c = new CenterContainer();
            c.AddChild(Glyphs.Icon(d.Glyph ?? "talk", 110, new Color("#e8c890")));
            frame.AddChild(c);
        }
        who.AddChild(frame);
        who.AddChild(Style.Label(d.Name, Style.Display, 22, Style.GoldHi, true, HorizontalAlignment.Center));
        if (d.Title != "") who.AddChild(Style.Label(d.Title, Style.TextItalic, Style.Caption, Style.InkDim, true, HorizontalAlignment.Center));
        if (d.Mood != "")
        {
            var mood = Style.H(4, Glyphs.Icon("eye", 14, Style.Gold), Style.Label(d.Mood, Style.Ui, Style.Caption, Style.Gold));
            mood.Alignment = BoxContainer.AlignmentMode.Center;
            who.AddChild(mood);
        }
        row.AddChild(who);
        // What is said, and what can be said back.
        var main = Style.V(10);
        main.SizeFlagsHorizontal = SizeFlags.ExpandFill;""",
"""        // The words on a plate across the foot of the screen; the person stands in front of its
        // left end, large, as they would across a table (docs/UI_DESIGN.md, "Conversation").
        var box = Style.Panel(Style.Plate(22));
        box.Position = new Vector2(500, 1080 - 36 - 404);
        box.Size = new Vector2(1380, 404);
        AddChild(box);
        var inset = new MarginContainer { MouseFilter = MouseFilterEnum.Ignore };
        inset.AddThemeConstantOverride("margin_left", 110);
        inset.AddThemeConstantOverride("margin_top", 26);
        box.AddChild(inset);
        var glow = new TextureRect
        {
            ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Ignore,
            Texture = new GradientTexture2D
            {
                Gradient = new Gradient { Colors = new[] { new Color(1, 0.5f, 0.2f, 0.2f), new Color(1, 0.5f, 0.2f, 0) }, Offsets = new[] { 0f, 1f } },
                Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.55f), FillTo = new Vector2(1f, 0.55f), Width = 128, Height = 128,
            },
            Position = new Vector2(-40, 300), Size = new Vector2(720, 780),
        };
        AddChild(glow);
        if (d.Person != null)
        {
            var fig = new Portrait(new Vector2I(560, 760), Portrait.Framing.Half).Of(d.Person, d.Arms, d.Scale);
            fig.Position = new Vector2(30, 1080 - 760);
            AddChild(fig);
        }
        else
        {
            var m = new Medallion(240, "", d.Glyph ?? "talk") { Ink = new Color("#e8c890"), Lit = true };
            m.Position = new Vector2(190, 1080 - 36 - 404 - 40);
            AddChild(m);
        }
        // Their name on a banner over the plate's edge, what they are and how they feel about you beside it.
        var banner = Style.Panel(OrnateBox.Make(OrnateBox.Kind.Banner, 18), Style.Label(d.Name.ToUpperInvariant(), Style.Display, 26, Style.GoldHi));
        banner.Position = new Vector2(610, 1080 - 36 - 404 - 26);
        AddChild(banner);
        // What is said, and what can be said back.
        var main = Style.V(10);
        main.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        var about = Style.H(Style.Gap3);
        if (d.Title != "") about.AddChild(Style.Label(d.Title, Style.TextItalic, Style.Small, Style.InkDim));
        if (d.Mood != "") about.AddChild(Style.H(4, Glyphs.Icon("eye", 14, Style.Gold), Style.Label(d.Mood, Style.Ui, Style.Small, Style.Gold)));
        if (about.GetChildCount() > 0) main.AddChild(about);""")
rep("""        focus = lines.FindIndex(l => l.Enabled);
        Prompts();
        row.AddChild(main);
    }""", """        focus = lines.FindIndex(l => l.Enabled);
        Prompts();
        inset.AddChild(main);
    }""")
open(p, 'w', encoding='utf-8', newline='').write(s)

q = R + r'\Portrait.cs'
t = open(q, encoding='utf-8').read()
old = "    public enum Framing { Full, Bust }"
assert old in t
t = t.replace(old, "    /// <summary>Full: head to foot. Half: head to hip, a person across a table. Bust: head and shoulders.</summary>\n    public enum Framing { Full, Half, Bust }", 1)
old = """        var cam = new Camera3D { Fov = framing == Framing.Bust ? 22 : 30 };
        stage.AddChild(cam);
        var (from, to) = framing == Framing.Bust ? (new Vector3(0, 1.62f, 1.45f), new Vector3(0, 1.55f, 0)) : (new Vector3(0, 1.05f, 4.1f), new Vector3(0, 0.95f, 0));"""
assert old in t
t = t.replace(old, """        var cam = new Camera3D { Fov = framing switch { Framing.Bust => 22, Framing.Half => 27, _ => 30 } };
        stage.AddChild(cam);
        var (from, to) = framing switch
        {
            Framing.Bust => (new Vector3(0, 1.62f, 1.45f), new Vector3(0, 1.55f, 0)),
            Framing.Half => (new Vector3(0, 1.4f, 2.7f), new Vector3(0, 1.28f, 0)),
            _ => (new Vector3(0, 1.05f, 4.1f), new Vector3(0, 0.95f, 0)),
        };""", 1)
open(q, 'w', encoding='utf-8', newline='').write(t)
print('ok')

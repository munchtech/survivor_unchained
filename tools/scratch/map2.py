p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\MapScreen.cs'
s = open(p, encoding='utf-8').read()

def rep(old, new):
    global s
    assert old in s, old[:90]
    s = s.replace(old, new, 1)

def cut(a, b, new):
    global s
    i = s.index(a)
    j = s.index(b, i)
    s = s[:i] + new + s[j:]

# The drawing: sharp enough to fill a screen, written straight into bytes.
rep("    const int W = 900;", "    const int W = 1600;")
rep("""        var img = Image.CreateEmpty(W, W, false, Image.Format.Rgb8);
        float cell = extent / (G - 1);""", """        var px8 = new byte[W * W * 3];
        float cell = extent / (G - 1);""")
rep("""                img.SetPixel(px, py, new Color(c.X / 255, c.Y / 255, c.Z / 255));
            }
        var tex = ImageTexture.CreateFromImage(img);""", """                int o = (py * W + px) * 3;
                px8[o] = (byte)Math.Clamp(c.X, 0, 255);
                px8[o + 1] = (byte)Math.Clamp(c.Y, 0, 255);
                px8[o + 2] = (byte)Math.Clamp(c.Z, 0, 255);
            }
        var img = Image.CreateFromData(W, W, false, Image.Format.Rgb8, px8);
        img.GenerateMipmaps();
        var tex = ImageTexture.CreateFromImage(img);""")
# Paper scaled to the drawing: the grain and contours were tuned at 900.
rep("""float n = (float)((Hash(px, py) - 0.5) * 14 + (Hash(px / 7, py / 7) - 0.5) * 10);""",
    """float n = (float)((Hash(px, py) - 0.5) * 12 + (Hash(px / 12, py / 12) - 0.5) * 10);""")

# Unwalked land is dark, not paper: what you know is a lit island in the night.
rep("""                float g = (float)(Hash(x, y) * 0.05);
                img.SetPixel(x, y, new Color(0.85f - g, 0.796f - g, 0.66f - g, alpha[y * F + x]));""",
    """                float g = (float)(Hash(x, y) * 0.025);
                img.SetPixel(x, y, new Color(0.075f + g, 0.062f + g, 0.058f + g, alpha[y * F + x] * 0.94f));""")
rep("""                        float hole = 1 - Mathf.SmoothStep(0.3f, 1f, d);""", """                        float hole = 1 - Mathf.SmoothStep(0.45f, 1f, d);""")

# The atlas fills the screen.
cut("    const int F = 920;", "    Vector2 panTo;", """    /// <summary>The drawing's size at zoom 1, and the part of the screen the map shows through
    /// (the list stands over the rest).</summary>
    const int F = 1080;
    static readonly Rect2 View = new(0, 96, 1440, 984);
    float minZoom = 0.6f;
""")
rep("""            case Act.SubNext: zoom = Math.Min(3.5f, zoom * 1.25f); Place(F); return true;
            case Act.SubPrev: zoom = Math.Max(1, zoom / 1.25f); Place(F); return true;""",
    """            case Act.SubNext: zoom = Math.Min(4f, zoom * 1.25f); Place(F); return true;
            case Act.SubPrev: zoom = Math.Max(minZoom, zoom / 1.25f); Place(F); return true;""")

cut("    protected override void Build()\n    {\n        var scene = G.Scene!;", "    /// <summary>A line of the list: its mark, its name, how far and which way from you.</summary>", '''    protected override void Build()
    {
        var scene = G.Scene!;
        var zone = G.Zone!;
        extent = Extent(scene.Data.Meta);
        var page = Page(zone.Name, zone.Region, null, G.Key(Act.Map));
        // The map is the screen: under the header band and the list, over the dark.
        var frame = new Control { Position = Vector2.Zero, Size = new Vector2(1920, 1080), ClipContents = true, MouseFilter = MouseFilterEnum.Stop };
        AddChild(frame);
        MoveChild(frame, 1);
        world = new Control { Size = new Vector2(F, F), MouseFilter = MouseFilterEnum.Ignore };
        frame.AddChild(world);
        world.AddChild(new TextureRect { Texture = Drawing(scene.Data), Size = new Vector2(F, F), ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Ignore, TextureFilter = TextureFilterEnum.LinearWithMipmaps });
        world.AddChild(new MapInk(scene, extent, F) { Size = new Vector2(F, F), MouseFilter = MouseFilterEnum.Ignore });
        var zs = G.Journey.World.Zone(zone.Id);
        var seen = zs.TryGetValue("seen", out var f) && f.Str is { } s ? s : new string('0', Journey.FogN * Journey.FogN);
        world.AddChild(new TextureRect { Texture = Fog(seen, Journey.FogN), Size = new Vector2(F, F), ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Ignore });
        bool Seen(double x, double z)
        {
            int i = (int)Math.Floor((x / extent + 0.5) * Journey.FogN), j = (int)Math.Floor((z / extent + 0.5) * Journey.FogN);
            return i >= 0 && j >= 0 && i < Journey.FogN && j < Journey.FogN && seen[j * Journey.FogN + i] == '1';
        }
        Vector2 Px(double x, double z) => new((float)((x / extent + 0.5) * F), (float)((z / extent + 0.5) * F));
        var entries = zone.MapMarks().Where(m => m.Kind is MarkKind.Exit or MarkKind.Quest || Seen(m.X, m.Z)).Select(m => new Entry(m.X, m.Z, m.Kind, m.Label)).ToList();
        if (G.Journey.World.Corpse is { } corpse && corpse.Zone == zone.Id) entries.Add(new Entry(corpse.X, corpse.Z, MarkKind.Danger, $"{corpse.HeroName}'s belongings"));
        foreach (var m in entries.OrderByDescending(m => m.Kind == MarkKind.Place)) Mark(world, Px(m.X, m.Z), m.Label, m.Kind);
        // The ring that marks what the list has chosen.
        ring = new Panel { Size = new Vector2(46, 46), PivotOffset = new Vector2(23, 23), MouseFilter = MouseFilterEnum.Ignore, Visible = false };
        var rs = Style.Box(new Color(0, 0, 0, 0), new Color("#a8321e"), 3, 23, 0);
        ring.AddThemeStyleboxOverride("panel", rs);
        world.AddChild(ring);
        // You.
        if (G.Battle is { } b)
        {
            youAt = Px(b.Player.X, b.Player.Z);
            world.AddChild(new Polygon2D { Polygon = new[] { new Vector2(0, -11), new Vector2(8, 8), new Vector2(0, 4), new Vector2(-8, 8) }, Color = new Color("#b8321e"), Position = youAt, Rotation = (float)(Math.PI - b.Player.Facing) });
        }
        frame.GuiInput += e => Input(e, F);
        if (G.Zone?.MapFocus == null) Fit(seen);
        Place(F);

        // A compass in the corner, the way the old maps had one.
        var rose = Glyphs.Icon("compass", 72, Style.Gold with { A = 0.75f });
        rose.Position = new Vector2(36, 120);
        AddChild(rose);
        var north = Style.Label("N", Style.Display, 18, Style.GoldHi, false, HorizontalAlignment.Center);
        north.Position = new Vector2(36, 96);
        north.Size = new Vector2(72, 22);
        AddChild(north);

        // The list: where to go, what has been found, what to beware of; each line glides the map to it.
        var col = Pane(page, new Rect2(1420, 0, 420, 920), Style.Plate(18), Style.Gap2);
        col.AddChild(new Section("Where to go", "nearest first"));
        var list = Style.V(2);
        var p0 = G.Battle?.Player;
        bool first = true;
        void Group(string title, IEnumerable<Entry> items)
        {
            var these = items.OrderBy(e => p0 == null ? 0 : Math.Sqrt((e.X - p0.X) * (e.X - p0.X) + (e.Z - p0.Z) * (e.Z - p0.Z))).ToList();
            if (these.Count == 0) return;
            if (!first) list.AddChild(Style.Gap(Style.Gap2));
            first = false;
            list.AddChild(Style.SubLabel(title));
            foreach (var e in these) list.AddChild(Line(e, Px(e.X, e.Z)));
        }
        Group("Your road", entries.Where(e => e.Kind is MarkKind.Quest or MarkKind.Turn or MarkKind.Exit));
        Group("People", entries.Where(e => e.Kind == MarkKind.Person));
        Group("Places", entries.Where(e => e.Kind == MarkKind.Place));
        Group("Danger and the strange", entries.Where(e => e.Kind is MarkKind.Danger or MarkKind.Mystery));
        if (entries.Count == 0) list.AddChild(Style.Label("Nothing found yet. The map fills in as you walk.", Style.TextItalic, Style.Body, Style.InkDim, true));
        var scroll = Style.Scroll(list);
        col.AddChild(scroll);
        col.AddChild(Style.Rule());
        // The legend, in the marks' own look (the corner map's too).
        var legend = new GridContainer { Columns = 2, MouseFilter = MouseFilterEnum.Ignore };
        legend.AddThemeConstantOverride("h_separation", 20);
        legend.AddThemeConstantOverride("v_separation", 6);
        foreach (var (kind, text) in new[] { (MarkKind.Quest, "Someone needs you"), (MarkKind.Exit, "The way out"), (MarkKind.Danger, "Hostile"), (MarkKind.Mystery, "Unexplained") })
            legend.AddChild(Style.H(6, Minimap.Mark(kind, 18), Style.Label(text, Style.Ui, Style.Caption, Style.Ink)));
        col.AddChild(legend);

        // Zoom and find-me, at the map's foot, where the hand is.
        var tools = Style.Panel(Style.Slab(8));
        tools.Position = new Vector2(40, 1000);
        AddChild(tools);
        var tr = Style.H(Style.Gap2);
        tools.AddChild(tr);
        Button Tool(string glyph, string? pad, string text, Action go)
        {
            var bt = Style.Button("", go, false, true);
            var r = Style.H(6, pad != null && Controls.Instance.UsingPad ? Style.PadButton(pad) : Glyphs.Icon(glyph, 16, Style.GoldHi), Style.Label(text, Style.UiBold, Style.Small, Style.GoldHi));
            r.MouseFilter = MouseFilterEnum.Ignore;
            r.Position = new Vector2(10, 5);
            bt.AddChild(r);
            bt.CustomMinimumSize = new Vector2(r.GetCombinedMinimumSize().X + 22, 34);
            return Nav.Skip(bt);
        }
        tr.AddChild(Tool("crosshair", "Y", "Find me", FindMe));
        tr.AddChild(Tool("expand", "RT", "Closer", () => Key(Act.SubNext)));
        tr.AddChild(Tool("expand", "LT", "Further", () => Key(Act.SubPrev)));
        tr.AddChild(Tool("map", null, "All I know", () => { Fit(seen); gliding = false; Place(F); }));
        PageFooter(Controls.Instance.UsingPad
            ? Footer((Act.Up, "Choose a place"), (Act.SubNext, "Closer"), (Act.SubPrev, "Further"), (Act.Alt2, "Find me"), (Act.TabPrev, "Journal"), (Act.Cancel, "Close"))
            : MouseFooter("Wheel to zoom", "drag to move", "a line to find it"));
    }

    /// <summary>
    /// Frames what the survivor knows: every walked cell and where they stand,
    /// with a margin, as large as the view allows. The map opens on the known
    /// world, not on a square of blank paper with the zone at its edge.
    /// </summary>
    void Fit(string seen)
    {
        int n = Journey.FogN;
        float u0 = 1, v0 = 1, u1 = 0, v1 = 0;
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
            {
                if (j * n + i >= seen.Length || seen[j * n + i] != '1') continue;
                u0 = Math.Min(u0, i / (float)n); v0 = Math.Min(v0, j / (float)n);
                u1 = Math.Max(u1, (i + 1) / (float)n); v1 = Math.Max(v1, (j + 1) / (float)n);
            }
        if (G.Battle is { } b)
        {
            float pu = (float)(b.Player.X / extent + 0.5), pv = (float)(b.Player.Z / extent + 0.5);
            u0 = Math.Min(u0, pu - 0.04f); v0 = Math.Min(v0, pv - 0.04f);
            u1 = Math.Max(u1, pu + 0.04f); v1 = Math.Max(v1, pv + 0.04f);
        }
        if (u1 <= u0 || v1 <= v0) { u0 = v0 = 0; u1 = v1 = 1; }
        // A margin, and never closer than a quarter of the zone.
        float cu = (u0 + u1) / 2, cv = (v0 + v1) / 2;
        float su = Math.Max(0.25f, (u1 - u0) * 1.15f), sv = Math.Max(0.25f, (v1 - v0) * 1.15f);
        minZoom = Math.Min(View.Size.X, View.Size.Y) / F * 0.9f;
        zoom = Math.Clamp(Math.Min(View.Size.X / (su * F), View.Size.Y / (sv * F)), minZoom, 4f);
        pan = new Vector2(0.5f - cu, 0.5f - cv);
    }

''')

cut("    void Place(int frame)\n    {", "    void Input(InputEvent e, int frame)", '''    void Place(int frame)
    {
        if (world == null) return;
        world.Scale = new Vector2(zoom, zoom);
        // The point the pan names sits at the middle of the part of the screen the map shows through.
        var centre = View.Position + View.Size / 2;
        world.Position = centre - (new Vector2(0.5f, 0.5f) - pan) * frame * zoom;
        foreach (var c in world.GetChildren()) if (c is Control mk && mk is not TextureRect && mk is not MapInk && mk != ring) mk.Scale = new Vector2(1 / zoom, 1 / zoom);
    }

''')
rep("""            case InputEventMouseButton { ButtonIndex: MouseButton.WheelUp, Pressed: true }: zoom = Math.Min(3.5f, zoom * 1.18f); Place(frame); break;
            case InputEventMouseButton { ButtonIndex: MouseButton.WheelDown, Pressed: true }: zoom = Math.Max(1, zoom / 1.18f); Place(frame); break;""",
    """            case InputEventMouseButton { ButtonIndex: MouseButton.WheelUp, Pressed: true }: zoom = Math.Min(4f, zoom * 1.18f); Place(frame); break;
            case InputEventMouseButton { ButtonIndex: MouseButton.WheelDown, Pressed: true }: zoom = Math.Max(minZoom, zoom / 1.18f); Place(frame); break;""")
rep("float band = y / contour, next = S(h, fx + 0.6f, fy + 0.6f) / contour;", "float band = y / contour, next = S(h, fx + 0.34f, fy + 0.34f) / contour;")
open(p, 'w', encoding='utf-8', newline='').write(s)
print('done')

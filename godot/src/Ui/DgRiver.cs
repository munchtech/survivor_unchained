using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>
/// UI 17, The Drowned Girl (the game's HUD), piece 2: her hair runs out to the right as a bronze river, and the river
/// is the bar (art/ui/dg_river, tools/uiforge/dg_river_cut.py: the owner's picked concept's own bar, d1v 5071, at
/// its 0.615 scale). Drawn under her figure: where she is solid she hides it, so its strands come out of her back
/// hair. The six seats are hair-bound rings in the current (Socket draws them, Seat), the Flare's glass sits in
/// the eddy at its right end (Flare), the draught and the dash where the concept has them. Piece 3 (UI 18, the
/// owner's pick (c)): her experience (by night the ember) lights when it moves: a cool light runs along her hair
/// and the river to the fraction, holds, and settles to a dim resting glow (dark after a long quiet) (Light, Play/XpLight.cs, shaders/hud_dg_xp.gdshaderinc); its numbers
/// on a card (Card).
/// </summary>
public partial class DgRiver : Control
{
    const string Dir = "dg_river";
    static Godot.Collections.Dictionary? geo;
    static Godot.Collections.Dictionary Geo => geo ??= Load();

    static Godot.Collections.Dictionary Load()
    {
        string path = $"{UiArt.Root}{Dir}/river_geo.json";
        if (FileAccess.FileExists(path) && Json.ParseString(FileAccess.GetFileAsString(path)).AsGodotDictionary() is { Count: > 0 } d)
            return d;
        GD.PushError($"DgRiver: {path} did not load: the river draws wrong");
        return new Godot.Collections.Dictionary();
    }

    static Vector2 V(Variant v) => v.AsGodotArray() is { Count: >= 2 } a ? new Vector2((float)a[0].AsDouble(), (float)a[1].AsDouble()) : Vector2.Zero;
    static Godot.Collections.Dictionary SeatGeo(int i) => Geo.TryGetValue("seats", out var s) && s.AsGodotArray() is { } a && i < a.Count
        ? a[i].AsGodotDictionary() : new Godot.Collections.Dictionary();
    static float SF(int i, string k) => SeatGeo(i).TryGetValue(k, out var v) ? (float)v.AsDouble() : 0;

    /// <summary>The river art's top left and size (1080 px).</summary>
    public static Vector2 At => Geo.TryGetValue("at", out var v) ? V(v) : Vector2.Zero;
    public static Vector2 ArtSize => Geo.TryGetValue("size", out var v) ? V(v) : Vector2.Zero;
    /// <summary>The ring's size across (the seat's control), from the geo.</summary>
    public static float SeatD => Geo.TryGetValue("seat_d", out var v) ? (float)v.AsDouble() : 78;
    /// <summary>The i-th seat's middle, its ring's size, its well's radius (the hole in the ring).</summary>
    public static Vector2 Seat(int i) => new(SF(i, "x"), SF(i, "y"));
    public static float Hole(int i) => SF(i, "hole");
    /// <summary>The eddy's glass: its middle and radius.</summary>
    public static Vector2 FlareAt => Geo.TryGetValue("flare", out var v) ? V(v) : Vector2.Zero;
    public static float FlareR => Geo.TryGetValue("flare", out var v) && v.AsGodotArray() is { Count: 3 } a ? (float)a[2].AsDouble() : 57;
    public static Vector2 DraughtAt => Geo.TryGetValue("draught", out var v) ? V(v) : Vector2.Zero;
    public static Vector2 DashAt => Geo.TryGetValue("dash", out var v) ? V(v) : Vector2.Zero;
    static Vector2[]? crest;
    /// <summary>The river's crest, left to right (1080 px): where piece 3's gold thread runs.</summary>
    public static Vector2[] Crest
    {
        get
        {
            if (crest != null) return crest;
            var l = new List<Vector2>();
            if (Geo.TryGetValue("crest", out var v)) foreach (var p in v.AsGodotArray()) l.Add(V(p));
            if (l.Count < 2) l = new() { new(700, 985), new(1400, 985) };
            return crest = l.ToArray();
        }
    }
    /// <summary>The crest's bounds, as the callouts bracket it ("chain", "chain_fill").</summary>
    public static Rect2 CrestRect
    {
        get
        {
            var c = Crest;
            float y0 = float.MaxValue, y1 = float.MinValue;
            foreach (var p in c) { y0 = Math.Min(y0, p.Y); y1 = Math.Max(y1, p.Y); }
            return new Rect2(c[0].X, y0 - 8, c[^1].X - c[0].X, y1 - y0 + 16);
        }
    }


    /// <summary>The band a foe or a mark is "behind the river" in (1080 px): the art from its top where it leaves her
    /// hair (y 880) down.</summary>
    public static Rect2 BandRect => new(At.X, 880, ArtSize.X, 1080 - 880);
    /// <summary>The survivor, an elite or a marked attack behind the river (Game sets it each frame): the river's art
    /// alone fades as her figure does (LifeLamp's times); the seats' glyphs, the thread and the orb stay at full.</summary>
    public bool Behind;
    float alpha = 1, clearFor = 99;

    public override void _Process(double delta)
    {
        float dt = (float)delta;
        clearFor = Behind ? 0 : clearFor + dt;
        bool dim = clearFor < LifeLamp.FadeHold;
        float a = Mathf.MoveToward(alpha, dim ? LifeLamp.FadeTo : 1, dt * (1 - LifeLamp.FadeTo) / (dim ? LifeLamp.FadeTime : LifeLamp.FadeBack));
        if (a != alpha)
        {
            if ((a <= LifeLamp.FadeTo + 0.001f) != (alpha <= LifeLamp.FadeTo + 0.001f) && Args.Has("shot")) GD.Print($"dg river fade alpha {a:0.00}");
            alpha = a;
            SelfModulate = Colors.White with { A = alpha };
        }
    }

    public DgRiver()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        TextureFilter = TextureFilterEnum.Linear;
        Position = At;
        Size = ArtSize;
        // (ui17 A: the bronze's idle sheen, the same sweep as her figure's, in screen px)
        var m = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/hud_dg_river.gdshader") };
        m.SetShaderParameter("scr_at", At);
        m.SetShaderParameter("size", ArtSize);
        Material = m;
        XpMasks(m);
    }

    public override void _Draw()
    {
        if (UiArt.Art($"{Dir}/river.png") is { } art) DrawTextureRect(art, new Rect2(Vector2.Zero, Size), false, Cuff.Day ? new Color(1.06f, 1.06f, 1.08f) : Colors.White);
    }

    /* ---- UI 18: the experience light (the owner's pick (c): "no XP on screen until it moves") ---- */

    static Godot.Collections.Dictionary? xpGeo;
    static Godot.Collections.Dictionary XpGeo => xpGeo ??= LoadXp();
    static Godot.Collections.Dictionary LoadXp()
    {
        string path = $"{UiArt.Root}{Dir}/xp_light.json";
        if (FileAccess.FileExists(path) && Json.ParseString(FileAccess.GetFileAsString(path)).AsGodotDictionary() is { Count: > 0 } d)
            return d;
        GD.PushError($"DgRiver: {path} did not load: the experience light runs wrong");
        return new Godot.Collections.Dictionary();
    }
    static float XF(string k, float or) => XpGeo.TryGetValue(k, out var v) ? (float)v.AsDouble() : or;
    /// <summary>The run's ends in XpLight.S (1080 px): her hair (0) and the eddy (full), from the baked masks.</summary>
    public static float RunS0 => XF("s0", 52);
    public static float RunS1 => XF("s1", 1158);
    static (double X, double Y)[]? crestD;
    static (double X, double Y)[] CrestD
    {
        get
        {
            if (crestD != null) return crestD;
            var c = Crest;
            crestD = new (double, double)[c.Length];
            for (int i = 0; i < c.Length; i++) crestD[i] = (c[i].X, c[i].Y);
            return crestD;
        }
    }
    /// <summary>The front's point on the crest for fraction f of the run, or null while the front is on her hair.</summary>
    public static Vector2? OnCrest(float f) => XpLight.OnCrest(CrestD, XpLight.FrontS(f, RunS0, RunS1)) is { } p ? new Vector2((float)p.X, (float)p.Y) : null;
    /// <summary>Her hair, as the hover hears it (the mask's outline, 1080 px, above the flask's key).</summary>
    static readonly Vector2[] HairOutline =
    [
        new(505, 830), new(560, 822), new(640, 850), new(700, 900), new(760, 950), new(760, 1030), new(570, 1030), new(545, 990),
        new(540, 960), new(535, 900), new(520, 860),
    ];
    /// <summary>The pointer is on her hair or the river (from the crest down, to the eddy's glass): the numbers show.</summary>
    public static bool OnRiver(Vector2 p)
    {
        if (Geometry2D.IsPointInPolygon(p, HairOutline)) return true;
        var c = Crest;
        if (p.X < c[0].X - 10 || p.X > FlareAt.X - FlareR * 0.5f || p.Y > 1080) return false;
        float y = c[0].Y;
        for (int i = 1; i < c.Length; i++) if (c[i].X >= p.X) { y = Mathf.Lerp(c[i - 1].Y, c[i].Y, (p.X - c[i - 1].X) / Math.Max(1e-3f, c[i].X - c[i - 1].X)); break; }
        return p.Y >= y - 10;
    }

    /// <summary>The front's glint over the crest (additive, under the seats); the numbers' card (over everything).</summary>
    public readonly Glint Spark = new();
    public readonly XpCard Card = new();
    public readonly LevelTitle Title = new();
    /// <summary>A callout teaches the run ("Ember fills this", Instrument.ChainFill): the light loops along it, 0 to 1.</summary>
    public float Pulse;
    ShaderMaterial? figMat;
    readonly float[] sent = [-1, -9999, -1, -1, -1, -1];
    static readonly StringName UOn = "xp_on", UFront = "xp_front", UTail = "xp_tail", UPeak = "xp_peak", UWhole = "xp_whole",
        UC = "xp_c", UHue = "xp_hue", UDay = "xp_day";
    public static readonly Color DayLight = new("#cfe8ff"), DayHue = new("#5aa2d6"), NightLight = new("#e2d4ff"), NightHue = new("#9c7ee0");

    void XpMasks(ShaderMaterial m)
    {
        if (UiArt.Tex($"{Dir}/xp_light.png", false) is { } t) m.SetShaderParameter("xp_mask", t);
        else GD.PushError($"DgRiver: {Dir}/xp_light.png did not load: the experience light draws blank");
        m.SetShaderParameter("xp_at", XpGeo.TryGetValue("at", out var a) ? V(a) : new Vector2(295, 822));
        m.SetShaderParameter("xp_size", XpGeo.TryGetValue("size", out var s) ? V(s) : new Vector2(1310, 258));
    }

    /// <summary>What the light shows now (XpLight; by day her experience, by night the ember), on the river and on
    /// her hair (fig: her figure's material). Sends only what changed: at rest, nothing.</summary>
    public void Light(XpLight x, bool day, ShaderMaterial? fig)
    {
        if (fig != null && fig != figMat) { figMat = fig; XpMasks(fig); Array.Fill(sent, -2); }
        float front = (float)x.Front, tail = (float)x.Tail, peak = (float)x.Peak, whole = (float)x.Whole;
        if (Pulse > 0)
        {
            float t = (Time.GetTicksMsec() / 1000f) % 1.8f / 1.2f;
            front = Mathf.Clamp(t, 0, 1);
            float p = Pulse * (1 - Mathf.SmoothStep(1.0f, 1.25f, t));
            tail = Math.Max(tail, p); peak = Math.Max(peak, p);
        }
        // (at rest the glow is static: these are the same every frame, so Send sends nothing)
        bool on = tail > 0.001f || peak > 0.001f || whole > 0.001f;
        float s = (float)XpLight.FrontS(front, RunS0, RunS1);
        void Send(int i, StringName u, float v)
        {
            if (sent[i] == v) return;
            sent[i] = v;
            ((ShaderMaterial)Material).SetShaderParameter(u, v);
            figMat?.SetShaderParameter(u, v);
        }
        Send(0, UOn, on ? 1 : 0);
        if (on)
        {
            Send(1, UFront, s);
            Send(2, UTail, tail);
            Send(3, UPeak, peak);
            Send(4, UWhole, whole);
            if (sent[5] != (day ? 1 : 0))
            {
                sent[5] = day ? 1 : 0;
                foreach (var m in new[] { (ShaderMaterial)Material, figMat })
                {
                    if (m == null) continue;
                    var c = day ? DayLight : NightLight;
                    var h = day ? DayHue : NightHue;
                    m.SetShaderParameter(UC, new Vector3(c.R, c.G, c.B));
                    m.SetShaderParameter(UHue, new Vector3(h.R, h.G, h.B));
                    m.SetShaderParameter(UDay, day ? 1f : 0f);
                }
            }
        }
        Spark.Show(on && peak > 0.001f ? OnCrest(front) : null, peak, day);
    }

    /// <summary>UI 18: the front's glint, a cool point of light where the front meets the crest, with a small bloom
    /// (dir_c.py: 0.9 of the light in a 3 px core, 1.6 times as wide as tall; the hue at 0.45 in 12 px). Drawn
    /// additively under the seats: when the front is behind a ring, the ridge above it and the lip below it carry it.</summary>
    public partial class Glint : Control
    {
        static ImageTexture? soft;
        Color core, bloom;
        public Glint()
        {
            MouseFilter = MouseFilterEnum.Ignore;
            Material = new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.Add };
            Visible = false;
            Size = new Vector2(64, 64);
        }
        static ImageTexture Soft()
        {
            if (soft != null) return soft;
            const int n = 64;
            var img = Image.CreateEmpty(n, n, false, Image.Format.Rgba8);
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float dx = (x + 0.5f) / n * 2 - 1, dy = (y + 0.5f) / n * 2 - 1;
                    float r = Mathf.Sqrt(dx * dx + dy * dy) * 2.6f;   // (the texture spans 2.6 sigma each way)
                    img.SetPixel(x, y, new Color(1, 1, 1, Mathf.Exp(-r * r)));
                }
            return soft = ImageTexture.CreateFromImage(img);
        }
        /// <summary>At p (or hidden), at strength k.</summary>
        public void Show(Vector2? p, float k, bool day)
        {
            bool vis = p != null && k > 0.001f;
            if (Visible != vis) Visible = vis;
            if (!vis) return;
            var at = p!.Value + new Vector2(0, -4) - Size / 2;
            if (Position != at) Position = at;
            var c = day ? DayLight : NightLight;
            var h = day ? DayHue : NightHue;
            var nc = new Color(c.R * 0.9f * k, c.G * 0.9f * k, c.B * 0.9f * k);
            var nb = new Color(h.R * 0.45f * 0.8f * k, h.G * 0.45f * 0.8f * k, h.B * 0.45f * 0.8f * k);
            if (nc != core || nb != bloom) { core = nc; bloom = nb; QueueRedraw(); }
        }
        public override void _Draw()
        {
            var t = Soft();
            var mid = Size / 2;
            DrawTextureRect(t, new Rect2(mid - new Vector2(31.2f, 31.2f), new Vector2(62.4f, 62.4f)), false, bloom);
            DrawTextureRect(t, new Rect2(mid - new Vector2(12.5f, 7.8f), new Vector2(25f, 15.6f)), false, core);
        }
    }

    /// <summary>UI 18 (judge M2): a level-up's name over the river, centred on it as the owner's approved sheet (c) showed
    /// it: "EMBER 5" over "the ember rises" by night, "LEVEL 13" by day, in the display face at 30 px, cream with a soft
    /// glow in the light's hue and a small shadow; held about 2 s, then faded (XpLight.Title). Redrawn only when its
    /// words change; the fade is its modulate.</summary>
    public partial class LevelTitle : Control
    {
        /// <summary>The name's middle at its baseline (1080 px).</summary>
        public static readonly Vector2 At = new(1078, 952);
        static readonly Vector2 Half = new(220, 44);
        string name = "", sub = "";
        bool day;
        public LevelTitle()
        {
            MouseFilter = MouseFilterEnum.Ignore;
            Position = At - Half;
            Size = Half * 2;
            Visible = false;
        }
        public void Set(float alpha, string name, string sub, bool day)
        {
            bool show = alpha > 0.002f;
            if (Visible != show) Visible = show;
            if (!show) return;
            var mod = Colors.White with { A = alpha };
            if (Modulate != mod) Modulate = mod;
            if (name == this.name && sub == this.sub && day == this.day) return;
            this.name = name; this.sub = sub; this.day = day;
            QueueRedraw();
        }
        public override void _Draw()
        {
            var f = Style.Display;
            const int size = 30;
            var ts = f.GetStringSize(name, HorizontalAlignment.Left, -1, size);
            var p = new Vector2(Mathf.Round(Half.X - ts.X / 2), Half.Y);
            var h = day ? DayHue : NightHue;
            // the glow in the light's hue, widest and faintest first (a soft halo, not a stroke)
            foreach (var (o, a) in new[] { (22, 0.045f), (15, 0.07f), (9, 0.10f), (5, 0.13f) })
                DrawStringOutline(f, p, name, HorizontalAlignment.Left, -1, size, o, h with { A = a });
            // the small shadow under it
            DrawStringOutline(f, p + new Vector2(0, 2), name, HorizontalAlignment.Left, -1, size, 2, new Color(0, 0, 0, 0.35f));
            DrawString(f, p + new Vector2(0, 2), name, HorizontalAlignment.Left, -1, size, new Color(0, 0, 0, 0.75f));
            DrawString(f, p, name, HorizontalAlignment.Left, -1, size, new Color("#f6efe0"));
            if (sub == "") return;
            var g = Style.Ui;
            const int ss = 17;
            var sz = g.GetStringSize(sub, HorizontalAlignment.Left, -1, ss);
            var q = new Vector2(Mathf.Round(Half.X - sz.X / 2), Half.Y + 19);
            DrawStringOutline(g, q, sub, HorizontalAlignment.Left, -1, ss, 6, h with { A = 0.08f });
            DrawString(g, q + new Vector2(1, 1), sub, HorizontalAlignment.Left, -1, ss, new Color(0, 0, 0, 0.7f));
            DrawString(g, q, sub, HorizontalAlignment.Left, -1, ss, new Color("#d8ccb4"));
        }
    }

    /// <summary>UI 18: the numbers, in the game's tooltip (the morocco card, UiArt "tooltip"): "Level 12" and its
    /// percent, a small meter in the light's hue, "4,210 / 6,000 experience", "1,790 to level 13" (by night the
    /// ember's). Shown while the pointer is on the river or the hold key (XpLight.HoldKey, pad LB) is down; redrawn
    /// only when its words or place change.</summary>
    public partial class XpCard : Control
    {
        public static readonly Vector2 CardSize = new(236, 92);
        string key = "";
        (string Title, string Pct, string Count, string Left) lines;
        float frac;
        bool day;
        StyleBox? box;
        public XpCard()
        {
            MouseFilter = MouseFilterEnum.Ignore;
            Size = CardSize;
            Visible = false;
        }
        /// <summary>Show it with its foot point at anchor (the pointer, or the run's front), or hide it.</summary>
        public void Set(bool show, Vector2 anchor, (string, string, string, string) l, float f, bool day)
        {
            if (Visible != show) Visible = show;
            if (!show) return;
            // (its right edge kept 12 px clear of the Flare cup's rim: the last judge saw it touch at 1447)
            float maxX = FlareAt.X > 0 ? Mathf.Min(1920 - 8, FlareAt.X - FlareR - 12) - Size.X : 1920 - 8 - Size.X;
            var at = new Vector2(Mathf.Clamp(Mathf.Round(anchor.X - 40), 8, maxX), Mathf.Clamp(Mathf.Round(anchor.Y - Size.Y - 24), 8, 1080 - Size.Y));
            if (Position != at) Position = at;
            string k = $"{l}|{f:0.000}|{day}";
            if (k == key) return;
            key = k; lines = l; frac = f; this.day = day;
            QueueRedraw();
        }
        public override void _Draw()
        {
            box ??= UiArt.Frame("tooltip", new StyleBoxFlat { BgColor = new Color(0.08f, 0.06f, 0.05f, 0.95f) });
            box.Draw(GetCanvasItem(), new Rect2(Vector2.Zero, Size));
            void Text(Font f, int size, Vector2 p, string s, Color c, bool right = false)
            {
                if (s == "") return;
                if (right) p.X -= f.GetStringSize(s, HorizontalAlignment.Left, -1, size).X;
                DrawString(f, p + new Vector2(1, 1), s, HorizontalAlignment.Left, -1, size, new Color(0, 0, 0, 0.7f));
                DrawString(f, p, s, HorizontalAlignment.Left, -1, size, c);
            }
            Text(Style.Display, 18, new Vector2(14, 27), lines.Title, new Color("#f3d9a0"));
            Text(Style.UiBold, 16, new Vector2(Size.X - 14, 27), lines.Pct, new Color("#a89c88"), true);
            // its meter: the numbers' own small line, in the light's hue, drawn only here
            float x0 = 14, x1 = Size.X - 14, y = 37;
            DrawRect(new Rect2(x0, y, x1 - x0, 4), new Color(0.047f, 0.043f, 0.063f, 0.9f));
            var h = day ? DayHue : NightHue;
            float fx = Mathf.Round(x0 + Mathf.Clamp(frac, 0, 1) * (x1 - x0));
            float[] row = [1.25f, 1, 1, 0.8f];
            for (int i = 0; i < 4; i++) if (fx > x0) DrawRect(new Rect2(x0, y + i, fx - x0, 1), new Color(Math.Min(1, h.R * row[i]), Math.Min(1, h.G * row[i]), Math.Min(1, h.B * row[i])));
            Text(Style.Ui, 16, new Vector2(14, 62), lines.Count, new Color("#e8dcc4"));
            Text(Style.Ui, 15, new Vector2(14, 81), lines.Left, new Color("#a89c88"));
        }
    }

    /// <summary>The ring (seat i, filled or empty) and its well, centred at c, for Socket's draw.</summary>
    public static Texture2D? Ring(int i) => UiArt.Art($"{Dir}/ring_{i % 6}.png");
    public static Texture2D? Well(int i) => UiArt.Art($"{Dir}/well_{i % 6}.png");

}

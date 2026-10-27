using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>
/// UI 17, The Drowned Girl (--hud drowned), piece 2: her hair runs out to the right as a bronze river, and the river
/// is the bar (art/ui/dg_river, tools/uiforge/dg_river_cut.py: the owner's picked concept's own bar, d1v 5071, at
/// its 0.615 scale). Drawn under her figure: where she is solid she hides it, so its strands come out of her back
/// hair. The six seats are hair-bound rings in the current (Socket draws them, Seat), the Flare's glass sits in
/// the eddy at its right end (Flare), the draught and the dash where the concept has them. Piece 3: her
/// experience (by night the ember) runs as a fine gold thread on the river's crest (Crest), its level on a
/// gold-rimmed knot where it leaves her hair (Thread).
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
    /// <summary>The level's boss, where the thread leaves her hair: its middle and radius.</summary>
    public static Vector2 BossAt => Crest[0] + new Vector2(-2, 0);
    public const float BossR = 13;

    public readonly ThreadLine Thread;

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
        Thread = new ThreadLine();  // (the instrument's child, over her figure and the river: screen px)
    }

    public override void _Draw()
    {
        if (UiArt.Art($"{Dir}/river.png") is { } art) DrawTextureRect(art, new Rect2(Vector2.Zero, Size), false, Cuff.Day ? new Color(1.06f, 1.06f, 1.08f) : Colors.White);
    }

    /// <summary>The ring (seat i, filled or empty) and its well, centred at c, for Socket's draw.</summary>
    public static Texture2D? Ring(int i) => UiArt.Art($"{Dir}/ring_{i % 6}.png");
    public static Texture2D? Well(int i) => UiArt.Art($"{Dir}/well_{i % 6}.png");

    /// <summary>Piece 3, the gold thread: her experience (by night the ember) as a fine gold wire inlaid along the
    /// river's crest. Unfilled it is a dull bronze hairline in its groove; filled it is polished gold, by night
    /// heated to an ember gold. Its lead is a small bead that sparks when it grows; now and then a glint runs along
    /// the lit wire. Its level sits on a gold-rimmed knot where it leaves her hair. A new level flashes it (Rise).
    /// --hud-pin day=1|0 holds the day's or the night's look for pictures.</summary>
    public partial class ThreadLine : Control
    {
        float fill, flash, spark, glintT = 2.5f;
        /// <summary>A callout points at it: the heat runs along all of it (0 to 1).</summary>
        public float Pulse;
        bool ember = true;
        int level = 1;
        string drawn = "";
        static GradientTexture2D? soft;
        static readonly Color GoldLit = new("#e6bf72"), GoldHot = new("#fff0c4"), EmberLit = new("#ff9238"), EmberHot = new("#ffe2a8"),
            Wire = new(0.50f, 0.39f, 0.22f, 0.80f);

        public ThreadLine()
        {
            MouseFilter = MouseFilterEnum.Ignore;
            Size = new Vector2(1920, 1080);
        }

        public void Set(float fill, bool ember, int level)
        {
            fill = Mathf.Clamp(fill, 0, 1);
            if (HudPin.Day is bool day) ember = !day;
            if (ember == this.ember && level == this.level && fill > this.fill + 0.0015f) spark = 1;
            string key = $"{fill:0.000}|{ember}|{level}";
            this.fill = fill; this.ember = ember; this.level = Math.Max(1, level);
            if (key != drawn) { drawn = key; QueueRedraw(); }
        }

        public void Rise() => flash = 1;

        public override void _Process(double delta)
        {
            float dt = (float)delta;
            bool live = false;
            if (flash > 0) { flash = Math.Max(0, flash - dt * 1.6f); live = true; }
            if (spark > 0) { spark = Math.Max(0, spark - dt * 2.2f); live = true; }
            // (a glint runs along the lit wire every seven seconds or so, 1.4 s long; between, nothing redraws)
            glintT -= dt;
            if (glintT < -1.5f) { glintT = 6f; live = true; }
            if (glintT < 0 && fill > 0.04f) live = true;
            if (live || Pulse > 0) QueueRedraw();
        }

        /// <summary>The point at length s along the line (and the index past it).</summary>
        static Vector2 At(Vector2[] pts, float[] len, float s, out int k)
        {
            for (k = 1; k < pts.Length; k++)
                if (len[k] >= s) return pts[k - 1].Lerp(pts[k], (s - len[k - 1]) / Math.Max(1e-3f, len[k] - len[k - 1]));
            k = pts.Length - 1;
            return pts[^1];
        }

        static Vector2[] Part(Vector2[] pts, float[] len, float s0, float s1)
        {
            var l = new List<Vector2> { At(pts, len, s0, out int k0) };
            for (int i = k0; i < pts.Length && len[i] < s1; i++) l.Add(pts[i]);
            l.Add(At(pts, len, s1, out _));
            return l.ToArray();
        }

        static Vector2[] Shift(Vector2[] a, float dy)
        {
            var o = new Vector2[a.Length];
            for (int i = 0; i < a.Length; i++) o[i] = a[i] + new Vector2(0, dy);
            return o;
        }

        public override void _Draw()
        {
            // (the wire rides a hair above the crest's line, on the wave's top)
            var src = Crest;
            var pts = new Vector2[src.Length];
            for (int i = 0; i < src.Length; i++) pts[i] = src[i] + new Vector2(0, -1);
            var len = new float[pts.Length];
            for (int i = 1; i < pts.Length; i++) len[i] = len[i - 1] + pts[i].DistanceTo(pts[i - 1]);
            float total = len[^1];
            float start = BossR + 1;  // (from the knot's rim)
            // its groove: a dark cut, and in it the wire, dull
            var all = Part(pts, len, start, total);
            DrawPolyline(Shift(all, 0.9f), new Color(0.02f, 0.015f, 0.01f, 0.75f), 3.6f, true);
            DrawPolyline(all, Wire, 1.25f, true);
            var lit = ember ? EmberLit : GoldLit;
            var hot = ember ? EmberHot : GoldHot;
            float reach = start + Math.Max(fill, flash) * (total - start);
            if (Pulse > 0)
            {
                float t = (Time.GetTicksMsec() / 1000f) % 1.8f / 1.2f;
                reach = Math.Max(reach, start + Mathf.Clamp(t, 0, 1) * (total - start) * Pulse);
            }
            soft ??= new GradientTexture2D
            {
                Width = 64, Height = 64, Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1, 0.5f),
                Gradient = new Gradient { Colors = new[] { Colors.White, Colors.White with { A = 0.3f }, Colors.White with { A = 0 } }, Offsets = new[] { 0f, 0.3f, 1f } },
            };
            if (reach > start + 0.5f)
            {
                var pa = Part(pts, len, start, reach);
                // the lit wire: a soft light round it (warmer by night), the gold, a bright hair along its top
                DrawPolyline(pa, lit with { A = ember ? 0.24f : 0.13f }, 6f, true);
                DrawPolyline(pa, lit.Darkened(0.35f), 2.6f, true);
                DrawPolyline(pa, lit, 1.9f, true);
                DrawPolyline(Shift(pa, -0.55f), hot with { A = 0.85f }, 0.9f, true);
                // the glint: a short bright run sliding along the lit wire
                if (glintT < 0 && reach - start > 30)
                {
                    float k = Mathf.Clamp(-glintT / 1.4f, 0, 1);
                    float g = start + k * (reach - start + 40) - 20;
                    for (int j = -3; j <= 3; j++)
                    {
                        float s0 = g + j * 4, a = 0.55f * (1 - Math.Abs(j) / 4f) * Mathf.Sin(Mathf.Pi * k);
                        if (s0 < start || s0 + 4 > reach) continue;
                        DrawPolyline(Shift(Part(pts, len, s0, s0 + 4), -0.4f), Colors.White with { A = a }, 1.3f, true);
                    }
                }
                // the lead: a bead, sparking as it grows
                var lead = At(pts, len, reach, out _);
                float sr = 6 + 5 * Math.Max(flash, spark);
                DrawTextureRect(soft, new Rect2(lead - new Vector2(sr, sr), new Vector2(sr * 2, sr * 2)), false, lit with { A = 0.55f + 0.4f * spark });
                DrawCircle(lead, 2.3f, lit.Darkened(0.2f), true, -1, true);
                DrawCircle(lead + new Vector2(-0.5f, -0.6f), 1.2f, hot, true, -1, true);
            }
            // the knot: the level on a bronze boss with a gold rim, where the thread leaves her hair
            var c = BossAt;
            DrawCircle(c + new Vector2(1, 1.6f), BossR + 1.8f, new Color(0, 0, 0, 0.6f), true, -1, true);
            DrawCircle(c, BossR + 0.6f, new Color(0.30f, 0.22f, 0.12f), true, -1, true);
            DrawArc(c, BossR - 0.6f, 0, Mathf.Tau, 48, new Color(0.62f, 0.48f, 0.27f), 2.4f, true);
            DrawArc(c, BossR - 0.4f, Mathf.Pi * 0.95f, Mathf.Pi * 1.85f, 24, new Color(1f, 0.88f, 0.60f, 0.85f), 1.3f, true);
            DrawArc(c, BossR - 0.9f, Mathf.Pi * 0.05f, Mathf.Pi * 0.8f, 24, new Color(0.12f, 0.08f, 0.04f, 0.8f), 1.1f, true);
            DrawCircle(c, BossR - 2.6f, new Color(0.06f, 0.045f, 0.03f), true, -1, true);
            if (flash > 0) DrawCircle(c, BossR - 2.6f, lit with { A = 0.6f * flash }, true, -1, true);
            var f = Style.Display;
            string s = level.ToString();
            int fs = s.Length > 1 ? 12 : 14;
            var sz = f.GetStringSize(s, HorizontalAlignment.Left, -1, fs);
            var p = new Vector2(Mathf.Round(c.X - sz.X / 2), Mathf.Round(c.Y + fs * 0.36f));
            DrawString(f, p + new Vector2(0, 1), s, HorizontalAlignment.Left, -1, fs, new Color(0, 0, 0, 0.85f));
            DrawString(f, p, s, HorizontalAlignment.Left, -1, fs, new Color("#f2d9a0"));
        }
    }
}

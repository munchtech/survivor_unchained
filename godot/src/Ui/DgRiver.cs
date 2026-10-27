using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>
/// UI 17, The Drowned Girl (--hud drowned), piece 2: her hair runs out to the right as a bronze river, and the river
/// is the bar (art/ui/dg_river, tools/uiforge/dg_river_cut.py: the owner's picked concept's own bar, d1v 5071, at
/// its 0.615 scale). Drawn under her figure: where she is solid she hides it, so its strands come out of her back
/// hair. The six seats are hair-bound rings in the current (Socket draws them, Seat), the Flare's glass sits in
/// the eddy at its right end (Flare), the draught and the dash where the concept has them. Until piece 3's gold
/// thread, her experience (by night the ember) runs as a plain ember line on the river's crest (Crest: the
/// polyline piece 3 runs on), its level on a small boss where it leaves her hair (Thread).
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

    public DgRiver()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        TextureFilter = TextureFilterEnum.Linear;
        Position = At;
        Size = ArtSize;
        Thread = new ThreadLine();  // (the instrument's child, over her figure and the river: screen px)
    }

    public override void _Draw()
    {
        if (UiArt.Art($"{Dir}/river.png") is { } art) DrawTextureRect(art, new Rect2(Vector2.Zero, Size), false, Cuff.Day ? new Color(1.06f, 1.06f, 1.08f) : Colors.White);
    }

    /// <summary>The ring (seat i, filled or empty) and its well, centred at c, for Socket's draw.</summary>
    public static Texture2D? Ring(int i) => UiArt.Art($"{Dir}/ring_{i % 6}.png");
    public static Texture2D? Well(int i) => UiArt.Art($"{Dir}/well_{i % 6}.png");

    /// <summary>Until piece 3: her experience (by night the ember) as an ember line along the crest, a dark groove
    /// the whole way, lit to how full, a spark at its lead; its level on a small bronze boss at its left end. A new
    /// level flashes it (Rise).</summary>
    public partial class ThreadLine : Control
    {
        float fill, flash;
        /// <summary>A callout points at it: the heat runs along all of it (0 to 1).</summary>
        public float Pulse;
        bool ember = true;
        int level = 1;
        string drawn = "";
        static GradientTexture2D? soft;

        public ThreadLine()
        {
            MouseFilter = MouseFilterEnum.Ignore;
            Size = new Vector2(1920, 1080);
        }

        public void Set(float fill, bool ember, int level)
        {
            fill = Mathf.Clamp(fill, 0, 1);
            string key = $"{fill:0.000}|{ember}|{level}";
            this.fill = fill; this.ember = ember; this.level = Math.Max(1, level);
            if (key != drawn) { drawn = key; QueueRedraw(); }
        }

        public void Rise() => flash = 1;

        public override void _Process(double delta)
        {
            if (flash > 0) { flash = Math.Max(0, flash - (float)delta * 1.6f); QueueRedraw(); }
            else if (Pulse > 0) QueueRedraw();
        }

        public override void _Draw()
        {
            var pts = Crest;
            // (the lengths along it, so the fill is by length)
            var len = new float[pts.Length];
            for (int i = 1; i < pts.Length; i++) len[i] = len[i - 1] + pts[i].DistanceTo(pts[i - 1]);
            float total = len[^1];
            DrawPolyline(pts, new Color(0.03f, 0.022f, 0.016f, 0.82f), 4.2f, true);
            DrawPolyline(pts, new Color(0.45f, 0.36f, 0.24f, 0.55f), 1.4f, true);
            var lit = ember ? new Color("#ff9a40") : new Color("#f2cf86");
            var hot = ember ? new Color("#ffd8a0") : new Color("#fff0c8");
            float reach = Math.Max(fill, flash) * total;
            if (Pulse > 0)
            {
                float t = (Time.GetTicksMsec() / 1000f) % 1.8f / 1.2f;
                reach = Math.Max(reach, Mathf.Clamp(t, 0, 1) * total * Pulse);
            }
            if (reach > 0.5f)
            {
                var part = new List<Vector2> { pts[0] };
                Vector2 lead = pts[0];
                for (int i = 1; i < pts.Length; i++)
                {
                    if (len[i] <= reach) { part.Add(pts[i]); lead = pts[i]; continue; }
                    float k = (reach - len[i - 1]) / Math.Max(1e-3f, len[i] - len[i - 1]);
                    lead = pts[i - 1].Lerp(pts[i], k);
                    part.Add(lead);
                    break;
                }
                var pa = part.ToArray();
                DrawPolyline(pa, lit with { A = 0.22f }, 7f, true);
                DrawPolyline(pa, lit, 2.4f, true);
                DrawPolyline(pa, hot with { A = 0.7f }, 1f, true);
                soft ??= new GradientTexture2D
                {
                    Width = 64, Height = 64, Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1, 0.5f),
                    Gradient = new Gradient { Colors = new[] { Colors.White, Colors.White with { A = 0.3f }, Colors.White with { A = 0 } }, Offsets = new[] { 0f, 0.3f, 1f } },
                };
                float sr = 7 + 6 * flash;
                DrawTextureRect(soft, new Rect2(lead - new Vector2(sr, sr), new Vector2(sr * 2, sr * 2)), false, hot with { A = 0.9f });
            }
            // the level's boss: a bronze stud, dark in its middle, the number in cream
            var c = BossAt;
            DrawCircle(c + new Vector2(1, 1.5f), BossR + 1.5f, new Color(0, 0, 0, 0.55f), true, -1, true);
            DrawCircle(c, BossR, new Color(0.40f, 0.30f, 0.17f), true, -1, true);
            DrawArc(c, BossR - 0.8f, Mathf.Pi * 1.05f, Mathf.Pi * 1.75f, 16, new Color(0.95f, 0.80f, 0.52f, 0.75f), 1.3f, true);
            DrawCircle(c, BossR - 3f, new Color(0.07f, 0.05f, 0.035f), true, -1, true);
            if (flash > 0) DrawCircle(c, BossR - 3f, lit with { A = 0.6f * flash }, true, -1, true);
            var f = Style.Display;
            string s = level.ToString();
            int fs = s.Length > 1 ? 13 : 15;
            var sz = f.GetStringSize(s, HorizontalAlignment.Left, -1, fs);
            var p = new Vector2(c.X - sz.X / 2, c.Y + fs * 0.36f);
            DrawString(f, p + new Vector2(0, 1), s, HorizontalAlignment.Left, -1, fs, new Color(0, 0, 0, 0.8f));
            DrawString(f, p, s, HorizontalAlignment.Left, -1, fs, LifeLamp.Cream);
        }
    }
}

using System;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>
/// UI 23, HUD A ("the keeper", the owner's pick): the middle of the bottom HUD, its own piece between the Drowned Girl
/// (left) and the keeper (right). A crisp dark-bronze plate with gold inlay, curled-lock end caps, an arch round the
/// level coin and the seats' bezels, all baked (art/ui/dg_panel/panel.png, tools/uiforge/dg_keeper_hud.py). Left to
/// right: the flask [R], three seats, the level coin, three seats, the dash [SPACE]. What is live is drawn over it: the
/// seats' wells (Socket), the flask and the dash (Round), the coin's experience ring (Ring, shaders/hud_dg_xpring.gdshader),
/// the level's number and the flask's count (Marks). Every place is the art's geo (art/ui/dg_keeper/hud_a_geo.json,
/// 1080 px), read once. The level's title over the coin (Title) and the numbers' card (Card) are the experience's
/// (Play/XpLight.cs).
/// </summary>
public partial class DgPanel : Control
{
    const string GeoPath = UiArt.Root + "dg_keeper/hud_a_geo.json";
    static Godot.Collections.Dictionary? geo;
    static Godot.Collections.Dictionary Geo => geo ??= Load();
    static Godot.Collections.Dictionary Load()
    {
        if (FileAccess.FileExists(GeoPath) && Json.ParseString(FileAccess.GetFileAsString(GeoPath)).AsGodotDictionary() is { Count: > 0 } d)
            return d;
        GD.PushError($"DgPanel: {GeoPath} did not load: the bar draws wrong");
        return new Godot.Collections.Dictionary();
    }
    static Godot.Collections.Dictionary Part(params string[] path)
    {
        var d = Geo;
        foreach (var k in path) d = d.TryGetValue(k, out var v) && v.VariantType == Variant.Type.Dictionary ? v.AsGodotDictionary() : new();
        return d;
    }
    static float[] A(Godot.Collections.Dictionary d, string k)
    {
        if (!d.TryGetValue(k, out var v) || v.VariantType != Variant.Type.Array) return [];
        var a = v.AsGodotArray();
        var r = new float[a.Count];
        for (int i = 0; i < a.Count; i++) r[i] = a[i].VariantType == Variant.Type.Array ? 0 : (float)a[i].AsDouble();
        return r;
    }
    static float F(Godot.Collections.Dictionary d, string k, float or) => d.TryGetValue(k, out var v) ? (float)v.AsDouble() : or;
    static Vector2 V(float[] a, Vector2 or) => a.Length >= 2 ? new Vector2(a[0], a[1]) : or;
    static Color C(float[] a, Color or) => a.Length >= 3 ? new Color(a[0], a[1], a[2]) : or;
    static Color C255(float[] a, Color or) => a.Length >= 3 ? new Color(a[0] / 255, a[1] / 255, a[2] / 255) : or;

    /* ---- the art's places (1080 px) ---- */

    /// <summary>The plate's rect (its texture is twice this).</summary>
    public static readonly Rect2 Rect = A(Part("panel"), "rect") is { Length: 4 } r ? new Rect2(r[0], r[1], r[2], r[3]) : new Rect2(576, 988, 768, 92);
    /// <summary>The plate's top line (its x ends and y) under the end caps, where the coin's arch rises from it.</summary>
    public static readonly float TopY = A(Part("panel"), "top_line") is { Length: 3 } t ? t[2] : 1003;
    static readonly Vector2[] seats = Seats();
    static Vector2[] Seats()
    {
        var l = new Vector2[Content.Weapons.MaxWeapons];
        var a = Part("panel").TryGetValue("seats", out var v) ? v.AsGodotArray() : new Godot.Collections.Array();
        for (int i = 0; i < l.Length; i++)
            l[i] = i < a.Count && a[i].AsGodotArray() is { Count: 2 } p ? new Vector2((float)p[0].AsDouble(), (float)p[1].AsDouble()) : new Vector2(733 + 75 * i + (i >= 3 ? 79 : 0), 1042);
        return l;
    }
    /// <summary>The i-th seat's middle; the well's radius (the icon's glass, drawn live) and the bezel's outer radius.</summary>
    public static Vector2 Seat(int i) => seats[Math.Clamp(i, 0, seats.Length - 1)];
    public static readonly float WellR = F(Part("panel"), "well_r", 31.5f), SeatR = F(Part("panel"), "seat_r", 35);
    /// <summary>The rank chip's middle offset from its seat's and its radius.</summary>
    public static readonly Vector2 ChipOff = Part("panel").TryGetValue("rank_chips", out var rc) && rc.AsGodotArray() is { Count: > 0 } ra
        && ra[0].AsGodotArray() is { Count: 3 } c0 ? new Vector2((float)c0[0].AsDouble(), (float)c0[1].AsDouble()) - seats[0] : new Vector2(24.5f, -24.5f);
    public const float ChipR = 9;
    /// <summary>The coin: its middle, its radius and the arch's round it.</summary>
    public static readonly Vector2 Coin = V(A(Part("panel", "coin"), "center"), new Vector2(960, 1042));
    public static readonly float CoinR = F(Part("panel", "coin"), "r", 37), ArchR = F(Part("panel", "coin"), "arch_r", 43);
    /// <summary>The experience ring's inner and outer radius (the lit filament in the coin's rim).</summary>
    public static readonly float RingR0 = F(Part("panel", "coin", "xp_ring"), "r0", 28.675f), RingR1 = F(Part("panel", "coin", "xp_ring"), "r1", 36.445f);
    /// <summary>The flask's and the dash's middles and the scales they draw at (the Drowned Girl's at 1:1).</summary>
    public static readonly Vector2 FlaskAt = V(A(Part("panel", "flask"), "center"), new Vector2(673, 1033));
    public static readonly Vector2 DashAt = V(A(Part("panel", "dash"), "center"), new Vector2(1247, 1035));
    public static readonly float FlaskScale = F(Part("panel", "flask"), "scale", 0.94f), DashScale = F(Part("panel", "dash"), "scale", 0.84f);
    /// <summary>The flask's count badge (middle, radius).</summary>
    public static readonly Vector2 CountAt = V(A(Part("panel", "flask"), "count_badge"), new Vector2(688, 1014));
    /// <summary>The key chips' tops (R and SPACE: [middle x, top y]).</summary>
    public static readonly Vector2 KeyR = V(A(Part("panel", "key_tags"), "R"), new Vector2(673, 1061));
    public static readonly Vector2 KeySpace = V(A(Part("panel", "key_tags"), "SPACE"), new Vector2(1247, 1061));
    /// <summary>For the right group (the keeper, the next piece): its Q chip, its rect and the Flare's glass.</summary>
    public static readonly Vector2 KeyQ = V(A(Part("panel", "key_tags"), "Q"), new Vector2(1508.56f, 1039.28f));
    public static readonly Rect2 KeeperRect = A(Part("keeper"), "rect") is { Length: 4 } k ? new Rect2(k[0], k[1], k[2], k[3]) : new Rect2(1254, 873, 341, 207);
    public static readonly Vector2 GlassAt = V(A(Part("glass"), "center"), new Vector2(1502.56f, 964.34f));
    public static readonly float GlassR = F(Part("glass"), "r", 37);
    /// <summary>The left and right groups draw at GroupScale about their outer bottom corners (the girl's: GirlAnchor;
    /// the keeper's: the screen's mirror of it).</summary>
    public static readonly float GroupScale = F(Part("girl"), "group_scale", 0.94f);
    public static readonly Vector2 GirlAnchor = V(A(Part("girl"), "group_anchor"), new Vector2(295.33f, 1080));
    public static readonly Vector2 KeeperAnchor = new(1920 - GirlAnchor.X, GirlAnchor.Y);
    /// <summary>The girl's globe on the screen (middle, radius), as drawn.</summary>
    public static readonly Vector3 Globe = A(Part("girl"), "globe") is { Length: 3 } g ? new Vector3(g[0], g[1], g[2]) : new Vector3(373.04f, 967.2f, 55.836f);

    /* ---- the ring's look (the geo's xp_ring and level_number; knobs in hud.json "xpRing") ---- */

    static Godot.Collections.Dictionary RingGeo => Part("panel", "coin", "xp_ring");
    public static readonly Color DayHue = C(A(Part("panel", "coin", "xp_ring", "day"), "hue"), new Color(0.353f, 0.635f, 0.839f));
    public static readonly Color DayCore = C(A(Part("panel", "coin", "xp_ring", "day"), "core"), new Color(0.812f, 0.91f, 1f));
    public static readonly Color NightHue = C(A(Part("panel", "coin", "xp_ring", "night"), "hue"), new Color(0.612f, 0.494f, 0.878f));
    public static readonly Color NightCore = C(A(Part("panel", "coin", "xp_ring", "night"), "core"), new Color(0.886f, 0.831f, 1f));
    public static readonly Vector2 LevelAt = V(A(Part("panel", "coin", "level_number"), "at"), new Vector2(960, 1043));
    public static readonly int LevelSize = (int)F(Part("panel", "coin", "level_number"), "size", 23);
    public static readonly Color LevelDay = C255(A(Part("panel", "coin", "level_number"), "day"), new Color(214 / 255f, 234 / 255f, 1f));
    public static readonly Color LevelNight = C255(A(Part("panel", "coin", "level_number"), "night"), new Color(232 / 255f, 222 / 255f, 1f));

    /// <summary>The pointer on the coin or its ring (the numbers' card shows).</summary>
    public static bool OnCoin(Vector2 p) => p.DistanceTo(Coin) <= ArchR;
    /// <summary>The ring's bounds: what "chain" and "chain_fill" bracket in a callout.</summary>
    public static Rect2 RingRect => new(Coin - Vector2.One * (RingR1 + 2), Vector2.One * 2 * (RingR1 + 2));
    /// <summary>The band a foe or a mark is "behind the plate" in.</summary>
    public static Rect2 BandRect => Rect;

    /* ---- the plate ---- */

    /// <summary>The survivor, an elite or a marked attack behind the plate (Game sets it each frame): the plate's art
    /// alone fades as her figure does (LifeLamp's times); the seats, the coin's ring and the numbers stay at full.</summary>
    public bool Behind;
    float alpha = 1, clearFor = 99;
    public readonly Ring XpRing = new();
    public readonly Marks Numbers;
    public readonly XpCard Card = new();
    public readonly LevelTitle Title = new();
    /// <summary>A callout teaches the ring ("Ember fills this", Instrument.ChainFill): its fill loops 0 to 1.</summary>
    public float Pulse;

    public DgPanel(Round draught)
    {
        MouseFilter = MouseFilterEnum.Ignore;
        TextureFilter = TextureFilterEnum.Linear;
        Position = Rect.Position;
        Size = Rect.Size;
        Numbers = new Marks(draught);
    }

    public override void _Process(double delta)
    {
        float dt = (float)delta;
        clearFor = Behind ? 0 : clearFor + dt;
        bool dim = clearFor < LifeLamp.FadeHold;
        float a = Mathf.MoveToward(alpha, dim ? LifeLamp.FadeTo : 1, dt * (1 - LifeLamp.FadeTo) / (dim ? LifeLamp.FadeTime : LifeLamp.FadeBack));
        if (a != alpha) { alpha = a; SelfModulate = Colors.White with { A = alpha }; }
    }

    public override void _Draw()
    {
        if (UiArt.Art("dg_panel/panel.png") is { } art) DrawTextureRect(art, new Rect2(Vector2.Zero, Size), false);
        else GD.PushError("DgPanel: dg_panel/panel.png did not load: the bar draws blank");
    }

    /// <summary>What the ring shows now (XpLight: by day her experience, by night the ember) and the level in the coin.</summary>
    public void Light(XpLight x, bool day, int level)
    {
        float f = (float)x.Front, boost = (float)(x.Strength * XpLight.RingLook.Game.GainBoost), whole = (float)x.Whole;
        if (Pulse > 0)
        {
            float t = (Time.GetTicksMsec() / 1000f) % 1.8f / 1.2f;
            f = Mathf.Clamp(t, 0, 1);
            boost = Math.Max(boost, Pulse * (1 - Mathf.SmoothStep(1.0f, 1.25f, t)) * (float)XpLight.RingLook.Game.GainBoost);
        }
        XpRing.Set(f, boost, whole, day);
        Numbers.Set(level, day);
    }

    /// <summary>The coin's experience ring (mock7.py medallion(): the lit filament in the coin's bronze rim, filling
    /// clockwise from the gold tick at 12 o'clock; blue by day, violet by night). One quad, one shader; it sends only
    /// what changed.</summary>
    public partial class Ring : ColorRect
    {
        readonly ShaderMaterial mat;
        float sf = -1, sb = -1, sw = -1;
        int sd = -1;
        static readonly StringName UF = "frac", UB = "boost", UW = "whole", UH = "hue", UC = "core";
        public Ring()
        {
            MouseFilter = MouseFilterEnum.Ignore;
            float m = RingR1 + 6;
            Position = (Coin - Vector2.One * m).Floor();
            Size = (Coin + Vector2.One * m).Ceil() - Position;
            mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/hud_dg_xpring.gdshader") };
            mat.SetShaderParameter("at", Position);
            mat.SetShaderParameter("size", Size);
            mat.SetShaderParameter("c", Coin);
            mat.SetShaderParameter("r0", RingR0);
            mat.SetShaderParameter("r1", RingR1);
            mat.SetShaderParameter("sigma", F(RingGeo, "core_sigma", 1.9f));
            mat.SetShaderParameter("track", F(RingGeo, "track_tint", 0.22f));
            mat.SetShaderParameter("lip", F(RingGeo, "lip", 0.35f));
            var hg = A(RingGeo, "head_glint");
            mat.SetShaderParameter("glint", hg.Length == 2 ? new Vector2(hg[0], hg[1]) : new Vector2(2.6f, 0.9f));
            Material = mat;
        }
        public void Set(float f, float boost, float whole, bool day)
        {
            if (f != sf) { sf = f; mat.SetShaderParameter(UF, f); }
            if (boost != sb) { sb = boost; mat.SetShaderParameter(UB, boost); }
            if (whole != sw) { sw = whole; mat.SetShaderParameter(UW, whole); }
            if (sd != (day ? 1 : 0))
            {
                sd = day ? 1 : 0;
                var h = day ? DayHue : NightHue;
                var c = day ? DayCore : NightCore;
                mat.SetShaderParameter(UH, new Vector3(h.R, h.G, h.B));
                mat.SetShaderParameter(UC, new Vector3(c.R, c.G, c.B));
            }
        }
    }

    /// <summary>The numbers on the plate (mock7.py text_layer()): the level in the coin (Cinzel 700 23, a 1 px dark
    /// stroke, cool white by day, violet white by night) and the flask's count on its dark badge (Cinzel 700 15, cream,
    /// a 1 px bronze rim). Redrawn only when either changes.</summary>
    public partial class Marks : Control
    {
        readonly Round draught;
        int level = -1, count = int.MinValue;
        bool day;
        public Marks(Round draught)
        {
            this.draught = draught;
            MouseFilter = MouseFilterEnum.Ignore;
            Position = Rect.Position;
            Size = Rect.Size;
        }
        public void Set(int level, bool day)
        {
            if (level == this.level && day == this.day) return;
            this.level = level; this.day = day;
            QueueRedraw();
        }
        public override void _Process(double delta)
        {
            if (draught.Count != count) { count = draught.Count; QueueRedraw(); }
        }
        /// <summary>A string's baseline for its middle at y (PIL's "mm": halfway between the face's ascent and descent).</summary>
        public static Vector2 Mid(Font f, string s, int size, Vector2 at, float track = 0)
        {
            float w = f.GetStringSize(s, HorizontalAlignment.Left, -1, size).X + track * Math.Max(0, s.Length - 1);
            return new Vector2(at.X - w / 2, at.Y + (f.GetAscent(size) - f.GetDescent(size)) / 2);
        }
        /// <summary>A small dark badge with a bronze rim and a cream numeral (the rank chips' and the count's).</summary>
        public static void Chip(CanvasItem ci, Vector2 c, string s, bool hot = false)
        {
            ci.DrawCircle(c, ChipR + 0.5f, hot ? new Color(1f, 0.80f, 0.45f) : new Color(166 / 255f, 128 / 255f, 80 / 255f), true, -1, true);
            ci.DrawCircle(c, ChipR - 0.5f, new Color(20 / 255f, 16 / 255f, 13 / 255f, 248 / 255f), true, -1, true);
            var f = Style.Display;
            ci.DrawString(f, Mid(f, s, 15, c + new Vector2(0.5f, 1)), s, HorizontalAlignment.Left, -1, 15, new Color(248 / 255f, 238 / 255f, 216 / 255f));
        }
        public override void _Draw()
        {
            var o = Position;
            if (level >= 0)
            {
                var f = Style.Display;
                string s = level.ToString();
                var p = Mid(f, s, LevelSize, LevelAt) - o;
                DrawStringOutline(f, p, s, HorizontalAlignment.Left, -1, LevelSize, 2, new Color(8 / 255f, 12 / 255f, 18 / 255f));
                DrawString(f, p, s, HorizontalAlignment.Left, -1, LevelSize, day ? LevelDay : LevelNight);
            }
            if (count != int.MinValue) Chip(this, CountAt - o, Math.Max(0, count).ToString());
        }
    }

    /// <summary>UI 18 judge M2, a level-up's name, over the coin (UI 23): "EMBER 5" over "the ember rises" by night,
    /// "LEVEL 13" by day, in the display face at 30 px, cream with a soft glow in the light's hue and a small shadow;
    /// held about 2 s, then faded (XpLight.Title). Its last line's baseline stands hud.json's xpRing.titleGap over the
    /// coin's arch. Redrawn only when its words change; the fade is its modulate.</summary>
    public partial class LevelTitle : Control
    {
        static readonly Vector2 Half = new(220, 44);
        const float SubDy = 19;
        string name = "", sub = "";
        bool day;
        public LevelTitle()
        {
            MouseFilter = MouseFilterEnum.Ignore;
            Size = Half * 2;
            Visible = false;
            Place(false);
        }
        /// <summary>The name's baseline: the last line's TitleGap over the arch's top.</summary>
        public static float Baseline(bool sub) => Coin.Y - ArchR - (float)XpLight.RingLook.Game.TitleGap - (sub ? SubDy : 0);
        void Place(bool sub) => Position = new Vector2(Coin.X, Baseline(sub)) - Half;
        public void Set(float alpha, string name, string sub, bool day)
        {
            bool show = alpha > 0.002f;
            if (Visible != show) Visible = show;
            if (!show) return;
            var mod = Colors.White with { A = alpha };
            if (Modulate != mod) Modulate = mod;
            if (name == this.name && sub == this.sub && day == this.day) return;
            this.name = name; this.sub = sub; this.day = day;
            Place(sub != "");
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
            DrawStringOutline(f, p + new Vector2(0, 2), name, HorizontalAlignment.Left, -1, size, 2, new Color(0, 0, 0, 0.35f));
            DrawString(f, p + new Vector2(0, 2), name, HorizontalAlignment.Left, -1, size, new Color(0, 0, 0, 0.75f));
            DrawString(f, p, name, HorizontalAlignment.Left, -1, size, new Color("#f6efe0"));
            if (sub == "") return;
            var g = Style.Ui;
            const int ss = 17;
            var sz = g.GetStringSize(sub, HorizontalAlignment.Left, -1, ss);
            var q = new Vector2(Mathf.Round(Half.X - sz.X / 2), Half.Y + SubDy);
            DrawStringOutline(g, q, sub, HorizontalAlignment.Left, -1, ss, 6, h with { A = 0.08f });
            DrawString(g, q + new Vector2(1, 1), sub, HorizontalAlignment.Left, -1, ss, new Color(0, 0, 0, 0.7f));
            DrawString(g, q, sub, HorizontalAlignment.Left, -1, ss, new Color("#d8ccb4"));
        }
    }

    /// <summary>UI 18: the numbers, in the game's tooltip (the morocco card, UiArt "tooltip"): "Level 12" and its
    /// percent, a small meter in the light's hue, "4,210 / 6,000 experience", "1,790 to level 13" (by night the
    /// ember's). Shown while the pointer is on the coin (UI 23) or the hold key (XpLight.HoldKey, pad LB) is down,
    /// centred over the coin; redrawn only when its words or place change.</summary>
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
        /// <summary>Show it with its foot's middle at anchor (over the coin, or the pointer), or hide it.</summary>
        public void Set(bool show, Vector2 anchor, (string, string, string, string) l, float f, bool day)
        {
            if (Visible != show) Visible = show;
            if (!show) return;
            var at = new Vector2(Mathf.Clamp(Mathf.Round(anchor.X - Size.X / 2), 8, 1920 - 8 - Size.X), Mathf.Clamp(Mathf.Round(anchor.Y - Size.Y - 12), 8, 1080 - Size.Y));
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
}

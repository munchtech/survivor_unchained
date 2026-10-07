using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/// <summary>A mark on the minimap: where, what kind, and its name.</summary>
public readonly record struct MiniMark(double X, double Z, MarkKind Kind, string Label);

/// <summary>
/// The corner map (docs/UI_DESIGN.md, "Minimap"): the zone's own drawing
/// (MapScreen's ink and hill shading) in a disc round the survivor, north
/// up, with the fog where they have not walked. What is known is marked;
/// what the survivor is looking for (a quest, the way out) stays pinned to
/// the rim when it is off the disc, so the way to it is never a guess.
/// Shown by day and on the story's roads, not in the arenas, where the
/// whole fight is already on screen.
/// </summary>
public partial class Minimap : Control
{
    /// <summary>The disc's size on screen, and how many metres it spans.</summary>
    public const float Diameter = 200, Span = 120;
    // (Names made once, not a new one every showing for the collector.)
    static readonly StringName CentreName = "centre", DimName = "dim";
    readonly ColorRect disc;
    readonly ShaderMaterial mat;
    readonly Control marks;
    readonly Polygon2D you;
    Image? mask;
    ImageTexture? maskTex;
    string zone = "", seenNow = "";
    float extent = 1;

    public Minimap()
    {
        CustomMinimumSize = new Vector2(Diameter, Diameter);
        MouseFilter = MouseFilterEnum.Ignore;
        mat = new ShaderMaterial { Shader = new Shader { Code = ShaderCode } };
        disc = new ColorRect { Size = new Vector2(Diameter, Diameter), Material = mat, MouseFilter = MouseFilterEnum.Ignore };
        AddChild(disc);
        marks = new Control { Size = new Vector2(Diameter, Diameter), MouseFilter = MouseFilterEnum.Ignore };
        AddChild(marks);
        you = new Polygon2D
        {
            Polygon = new[] { new Vector2(0, -9), new Vector2(7, 7), new Vector2(0, 3), new Vector2(-7, 7) },
            Color = new Color("#b8321e"), Position = new Vector2(Diameter / 2, Diameter / 2),
        };
        AddChild(you);
        // A painted arrow (minimap/you.png, pointing up, 24 by 24 shown) in place of the drawn one.
        if (UiArt.Art("minimap/you.png") is { } arrow)
        {
            you.Color = Colors.Transparent;
            var a = new TextureRect { Texture = arrow, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, MouseFilter = MouseFilterEnum.Ignore, Size = arrow.GetSize() };
            a.Position = -a.Size / 2;
            you.AddChild(a);
        }
        // The bezel: the cuffs' iron round the disc, the day's path riding over its top (Bezel).
        bezel = new Bezel(this);
        AddChild(bezel);
    }

    readonly Bezel bezel;
    double? clock;
    bool running;
    float dim = 1;

    /// <summary>The day's clock on the bezel (null where the clock does not run: the bezel is plain).</summary>
    public void Clock(double? clock, bool running)
    {
        this.clock = clock is double c ? Math.Clamp(c, 0, DayClock.NightEnds) : null;
        this.running = running;
    }

    public override void _Process(double delta)
    {
        dim = Mathf.MoveToward(dim, running ? 1 : 0.45f, (float)delta * 2);
        bezel.QueueRedraw();
    }

    /// <summary>The disc's iron (minimap/bezel.png when UI art has made it, else drawn as the cuffs are),
    /// north marked on it, and, where the day's clock runs, the day's path over its top as the sun's is
    /// over the sky: dawn rising at the left, the day across the top, dusk and the night falling at the
    /// right, the present stretch lit, what has passed dimmer, her ember (or the moon) where the day
    /// stands. It is the experience director's dial (DayDial), set on the map's own iron.</summary>
    partial class Bezel : Control
    {
        public const float Band = 9;
        readonly Minimap m;

        public Bezel(Minimap m)
        {
            this.m = m;
            MouseFilter = MouseFilterEnum.Ignore;
            Size = new Vector2(Diameter, Diameter);
            TextureFilter = TextureFilterEnum.LinearWithMipmaps;
        }

        /// <summary>A point on the day's path: from the bezel's left (dawn) over its top to its right.</summary>
        static Vector2 At(Vector2 c, float r, double s)
        {
            float k = (float)(s / DayClock.NightEnds), a = Mathf.Lerp(Mathf.Pi * 1.08f, Mathf.Pi * 1.92f, k);
            return c + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * r;
        }

        public override void _Draw()
        {
            var c = Size / 2;
            float r = Diameter / 2;
            if (UiArt.Art("minimap/bezel.png") is { } art)
            {
                var sz = art.GetSize();
                DrawTexture(art, c - sz / 2);
            }
            else
            {
                DrawCircle(c + new Vector2(0, 4), r + Band + 3, new Color(0, 0, 0, 0.35f));
                DrawCircle(c, r, new Color(0, 0, 0, 0));
                Cuff.Band(this, c, r, Band);
            }
            // North: a small ember notch on the iron's top.
            var n = c + new Vector2(0, -r - Band / 2);
            DrawColoredPolygon(new[] { n + new Vector2(-4.5f, -3.5f), n + new Vector2(4.5f, -3.5f), n + new Vector2(0, 4.5f) }, Style.Ember);
            if (m.clock is not double clock) return;
            // The day's path, outside the iron, in its four stretches.
            float pr = r + Band + 6, dim = m.dim;
            var now = DayClock.At(clock);
            int nowBand = (int)now;
            bool late = now == TimeOfDay.Night && clock >= DayClock.NudgeAt;
            for (int b = 0; b < Bands.Length; b++)
            {
                var (from, to, ink) = Bands[b];
                bool lit = b == nowBand;
                int steps = Math.Max(3, (int)((to - from) / DayClock.NightEnds * 64));
                for (int i = 0; i < steps; i++)
                {
                    double s0 = from + (to - from) * i / steps, s1 = from + (to - from) * (i + 1) / steps;
                    bool passed = s1 <= clock;
                    var col = ink;
                    if (b == 3 && late && !passed) col = col.Lerp(new Color("#c8ccd8"), (float)((s0 - DayClock.NudgeAt) / (DayClock.NightEnds - DayClock.NudgeAt)) * 0.7f);
                    float a = passed ? 0.28f : lit ? 1f : 0.5f;
                    DrawLine(At(c, pr, s0), At(c, pr, s1), new Color(0, 0, 0, 0.55f * dim), lit && !passed ? 5.5f : 4.5f, true);
                    DrawLine(At(c, pr, s0), At(c, pr, s1), col with { A = a * dim }, lit && !passed ? 3.2f : 2.2f, true);
                }
                if (b > 0) DrawCircle(At(c, pr, from), 1.6f, new Color(0.9f, 0.85f, 0.75f, 0.5f * dim));
            }
            var p = At(c, pr, clock);
            if (now == TimeOfDay.Night)
            {
                DrawCircle(p, 9, new Color(0.6f, 0.7f, 1f, 0.16f * dim));
                DrawCircle(p, 5.5f, new Color("#e4ebff") with { A = dim });
                DrawCircle(p + new Vector2(2.6f, -1.6f), 4.6f, new Color(0.06f, 0.07f, 0.12f, 0.92f * dim));
            }
            else
            {
                float br = 0.85f + 0.15f * Mathf.Sin(Time.GetTicksMsec() / 1000f * 2.2f);
                DrawCircle(p, 10, Style.Ember with { A = 0.22f * br * dim });
                DrawCircle(p, 4.4f, Style.Ember with { A = dim });
                DrawCircle(p, 2, Style.EmberHi with { A = dim });
            }
        }

        static readonly (double From, double To, Color Ink)[] Bands =
        {
            (0, DayClock.DayAt, new Color("#d8b8c8")),
            (DayClock.DayAt, DayClock.DuskAt, new Color("#ecd9a6")),
            (DayClock.DuskAt, DayClock.NightAt, new Color("#ff8a3a")),
            (DayClock.NightAt, DayClock.NightEnds, new Color("#86a6e0")),
        };
    }

    /// <summary>A new zone: its drawing and how wide it is.</summary>
    public void Zone(string id, Texture2D drawing, float ext)
    {
        if (id == zone) return;
        zone = id;
        extent = Math.Max(1, ext);
        seenNow = "";
        mat.SetShaderParameter("drawing", drawing);
        mat.SetShaderParameter("span", Span / extent);
    }

    /// <summary>Where the survivor is and what is known, a few times a second.</summary>
    public void Show(string seen, int n, IEnumerable<MiniMark> list, double px, double pz, double facing, bool night)
    {
        if (seen != seenNow)
        {
            seenNow = seen;
            mask ??= Image.CreateEmpty(n, n, false, Image.Format.L8);
            for (int j = 0; j < n; j++)
                for (int i = 0; i < n; i++)
                    mask.SetPixel(i, j, j * n + i < seen.Length && seen[j * n + i] == '1' ? Colors.White : Colors.Black);
            if (maskTex == null) { maskTex = ImageTexture.CreateFromImage(mask); mat.SetShaderParameter("seen", maskTex); }
            else maskTex.Update(mask);
        }
        mat.SetShaderParameter(CentreName, new Vector2((float)(px / extent + 0.5), (float)(pz / extent + 0.5)));
        mat.SetShaderParameter(DimName, night ? 0.62f : 0.95f);
        you.Rotation = (float)(Math.PI - facing);
        foreach (var c in marks.GetChildren()) c.QueueFree();
        float r = Diameter / 2, scale = Diameter / Span;
        foreach (var m in list)
        {
            var at = new Vector2((float)(m.X - px), (float)(m.Z - pz)) * scale;
            bool guide = m.Kind is MarkKind.Quest or MarkKind.Turn or MarkKind.Exit;
            bool off = at.Length() > r - 12;
            if (off && !guide) continue;
            // Off the disc, what is sought waits on the rim, pointing the way.
            if (off) at = at.Normalized() * (r - 12);
            // People are many in a town: a dot each; what is sought keeps its sign.
            var icon = m.Kind == MarkKind.Person ? Dot(new Color("#3a2414")) : Mark(m.Kind, off ? 15 : 18);
            icon.Position = new Vector2(r, r) + at - icon.CustomMinimumSize / 2;
            if (off) icon.Modulate = Colors.White with { A = 0.85f };
            marks.AddChild(icon);
        }
    }

    /// <summary>A map mark's look: painted (icons/map/KIND.png) or its glyph in its ink.</summary>
    public static Control Mark(MarkKind kind, int size)
    {
        var (glyph, color) = Look(kind);
        if (UiArt.Icon("map", kind.ToString().ToLowerInvariant()) is { } art)
        {
            // Sized after the expand mode is set: before it, the texture's own size is the minimum.
            var t = new TextureRect { ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.KeepAspectCentered, Texture = art, CustomMinimumSize = new Vector2(size, size), MouseFilter = MouseFilterEnum.Ignore };
            t.Size = new Vector2(size, size);
            return t;
        }
        // A pale disc under the ink, so a mark reads on dark ground and on paper alike.
        var holder = new Control { CustomMinimumSize = new Vector2(size, size), Size = new Vector2(size, size), MouseFilter = MouseFilterEnum.Ignore };
        var back = new Panel { Size = new Vector2(size, size), MouseFilter = MouseFilterEnum.Ignore };
        back.AddThemeStyleboxOverride("panel", Style.Box(new Color("#efe3c4") with { A = 0.92f }, color, 1, size / 2, 0));
        holder.AddChild(back);
        var g = Glyphs.Icon(glyph, size - 6, color);
        g.Position = new Vector2(3, 3);
        g.Size = new Vector2(size - 6, size - 6);
        holder.AddChild(g);
        return holder;
    }

    static Control Dot(Color ink)
    {
        var p = new Panel { CustomMinimumSize = new Vector2(8, 8), Size = new Vector2(8, 8), MouseFilter = MouseFilterEnum.Ignore };
        p.AddThemeStyleboxOverride("panel", Style.Box(new Color("#efe3c4"), ink, 2, 4, 0));
        return p;
    }

    /// <summary>Each kind of mark's glyph and ink, shared with the full map.</summary>
    public static (string Glyph, Color Color) Look(MarkKind kind) => kind switch
    {
        MarkKind.Quest or MarkKind.Turn => ("quest", new Color("#a8321e")), MarkKind.Danger => ("skull", new Color("#6a1a10")),
        MarkKind.Mystery => ("eye", new Color("#5a3a7a")), MarkKind.Exit => ("next", new Color("#2a4a3a")), MarkKind.Person => ("talk", new Color("#3a2414")),
        _ => ("map", new Color("#3a2414")),
    };

    const string ShaderCode = """
        shader_type canvas_item;
        uniform sampler2D drawing : filter_linear, repeat_disable;
        uniform sampler2D seen : filter_linear, repeat_disable;
        uniform vec2 centre = vec2(0.5);
        uniform float span = 0.2;
        uniform float dim = 1.0;
        void fragment() {
            vec2 d = UV - 0.5;
            float r = length(d) * 2.0;
            vec2 uv = centre + d * span;
            vec3 paper = vec3(0.85, 0.796, 0.66);
            vec3 col = texture(drawing, uv).rgb;
            float s = texture(seen, uv).r;
            // Unwalked ground is blank parchment, as on the big map; beyond the zone's edge, darker.
            col = mix(col, paper * 0.97, 1.0 - smoothstep(0.2, 0.7, s));
            if (uv.x < 0.0 || uv.y < 0.0 || uv.x > 1.0 || uv.y > 1.0) col = paper * 0.55;
            col *= mix(1.0, 0.86, smoothstep(0.7, 1.0, r)) * dim;
            COLOR = vec4(col, 1.0 - smoothstep(0.965, 1.0, r));
        }
        """;
}

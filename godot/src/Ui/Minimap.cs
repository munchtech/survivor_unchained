using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/// <summary>A mark on the minimap: where, what kind, and its name.</summary>
public readonly record struct MiniMark(double X, double Z, MarkKind Kind, string Label, bool Active = false);

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
    static readonly StringName CentreName = "centre";
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
        // Where she is: a bone-white arrow with an ink edge (M4 lead 9, fix C: it reads on the vellum and on the dark
        // unexplored plate alike; the painted red minimap/you.png sank into both and is no longer shown).
        var arrow = new[] { new Vector2(0, -10), new Vector2(7.5f, 8), new Vector2(0, 3.5f), new Vector2(-7.5f, 8) };
        you = new Polygon2D { Polygon = arrow, Color = new Color("#efe6d2"), Position = new Vector2(Diameter / 2, Diameter / 2) };
        you.AddChild(new Line2D
        {
            Points = arrow, Closed = true, Width = 4.5f, DefaultColor = new Color("#241c12"), JointMode = Line2D.LineJointMode.Round,
            ShowBehindParent = true, Antialiased = true,
        });
        AddChild(you);
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
        // The bezel is redrawn only when the clock or its dimming changes, or while the day's ember breathes by
        // the clock (MR4, the HUD's redraws were 3.4 ms a frame).
        bool breathing = clock is double c && DayClock.At(c) != TimeOfDay.Night;
        if (breathing || !bezelDrawn || clock != drawnClock || dim != drawnDim)
        {
            bezelDrawn = true; drawnClock = clock; drawnDim = dim;
            bezel.QueueRedraw();
        }
    }

    bool bezelDrawn;
    double? drawnClock;
    float drawnDim;

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
                // (M4 lead 11: a ring, from r+4 to r+Band+3 about a centre 4 px low, never over the lens)
                DrawArc(c + new Vector2(0, 4), r + 4 + (Band - 1) / 2f, 0, Mathf.Tau, 96, new Color(0, 0, 0, 0.35f), Band - 1, true);
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
        GD.Print($"minimap: zone {id} extent {extent:0} span {Span / extent:0.000}: the drawing's edge fades into the paper over 28 px (+-6 px wander), darkening over 70 px beyond");
    }

    /// <summary>Where the survivor is and what is known, a few times a second. Nothing is built here once the marks'
    /// icons exist (M4 lead 5: it built a list, a set and an enumerator each showing, about 370 B).</summary>
    public void Show(string seen, int n, List<MiniMark> list, double px, double pz, double facing, bool night)
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
        // (night is not shown on the disc: the HUD does not darken at night, and the map is the same map; M4 lead 9, fix C)
        you.Rotation = (float)(Math.PI - facing);
        // The marks are kept and reused, not freed and built anew each time (MR4, the HUD's redraws were
        // 3.4 ms a frame): one pool per look (kind and size; the people's dots), shown in order, the rest hidden.
        var used = spareMarks;
        used.Clear();
        pooledUsed.Clear();
        float r = Diameter / 2, scale = Diameter / Span;
        bool trace = Args.Has("map-trace");
        System.Text.StringBuilder? tb = trace ? new System.Text.StringBuilder() : null;
        // (objectives are added last, so they draw over the other pins)
        for (int pass = 0; pass < 2; pass++)
            for (int li = 0; li < list.Count; li++)
            {
                var m = list[li];
                bool objective = m.Kind == MarkKind.Quest || (m.Kind == MarkKind.Goal && m.Active);
                if (objective != (pass == 1)) continue;
                var at = new Vector2((float)(m.X - px), (float)(m.Z - pz)) * scale;
                bool guide = m.Kind is MarkKind.Quest or MarkKind.Turn or MarkKind.Exit or MarkKind.Goal;
                bool off = at.Length() > r - 12;
                if (off && !guide) { tb?.Append($"{m.Kind} '{m.Label}' pin skipped; "); continue; }
                // Off the disc, what is sought waits on the rim, pointing the way.
                if (off) at = at.Normalized() * (r - 12);
                tb?.Append($"{m.Kind} '{m.Label}' {(objective ? "objective" : "pin")} {(off ? "rim" : "on")}; ");
                // People are many in a town: a dot each; what is sought keeps its sign.
                var key = m.Kind == MarkKind.Person ? (MarkKind.Person, 0, false) : objective ? (m.Kind, 24, true) : (m.Kind, m.Kind == MarkKind.Goal ? (off ? 21 : 25) : 18, false);
                if (!pool.TryGetValue(key, out var spare)) pool[key] = spare = new List<Control>();
                pooledUsed.TryGetValue(key, out int taken);
                pooledUsed[key] = taken + 1;
                Control icon;
                if (taken < spare.Count) icon = spare[taken];
                else
                {
                    icon = m.Kind == MarkKind.Person ? Dot(new Color("#3a2414")) : objective ? new GoalDiamond() : Mark(m.Kind, key.Item2);
                    spare.Add(icon);
                    marks.AddChild(icon);
                }
                // (set when they change: a mark that has not moved on the disc is left alone)
                var pos = new Vector2(r, r) + at - icon.CustomMinimumSize / 2;
                if (icon.Position != pos) icon.Position = pos;
                var mod = off && !objective ? Colors.White with { A = 0.85f } : Colors.White;
                if (icon.Modulate != mod) icon.Modulate = mod;
                if (!icon.Visible) icon.Visible = true;
                used.Add(icon);
            }
        if (tb != null)
        {
            var line = "minimap marks: " + tb;
            if (line != lastTrace) { lastTrace = line; GD.Print(line); }
        }
        // Draw order is the list's, as when each was built in turn.
        for (int i = 0; i < used.Count; i++)
            if (marks.GetChild(i) != used[i]) marks.MoveChild(used[i], i);
        // (what was shown and is not now; the two lists change places, neither is made anew)
        for (int i = 0; i < shownMarks.Count; i++)
            if (!used.Contains(shownMarks[i])) shownMarks[i].Visible = false;
        spareMarks = shownMarks;
        shownMarks = used;
    }

    string lastTrace = "";
    readonly Dictionary<(MarkKind, int, bool), List<Control>> pool = new();
    readonly Dictionary<(MarkKind, int, bool), int> pooledUsed = new();
    List<Control> shownMarks = new(), spareMarks = new();

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
        // (the goal's disc is gold, the others pale paper)
        back.AddThemeStyleboxOverride("panel", kind == MarkKind.Goal
            ? Style.Box(new Color("#e8c070"), color, 2, size / 2, 0)
            : Style.Box(new Color("#efe3c4") with { A = 0.92f }, color, 1, size / 2, 0));
        holder.AddChild(back);
        var g = Glyphs.Icon(glyph, size - 6, color);
        g.Position = new Vector2(3, 3);
        g.Size = new Vector2(size - 6, size - 6);
        holder.AddChild(g);
        return holder;
    }

    /// <summary>The objective's pin: the tracker's diamond (GameHud StepMark), heavier: an open bone diamond on an ink edge, ink-dimmed centre.</summary>
    partial class GoalDiamond : Control
    {
        public GoalDiamond()
        {
            CustomMinimumSize = new Vector2(24, 24);
            Size = new Vector2(24, 24);
            MouseFilter = MouseFilterEnum.Ignore;
        }

        public override void _Draw()
        {
            var c = Size / 2;
            var d = new[] { c + new Vector2(0, -7), c + new Vector2(7, 0), c + new Vector2(0, 7), c + new Vector2(-7, 0) };
            var closed = new[] { d[0], d[1], d[2], d[3], d[0] };
            DrawColoredPolygon(d, new Color(0.03f, 0.02f, 0.01f, 0.55f));
            DrawPolyline(closed, new Color("#241c12"), 5.5f, true);
            DrawPolyline(closed, new Color("#e8dcc4"), 2.4f, true);
        }
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
        MarkKind.Goal => ("chart", new Color("#3a2414")),
        _ => ("map", new Color("#3a2414")),
    };

    const string ShaderCode = """
        shader_type canvas_item;
        uniform sampler2D drawing : filter_linear, repeat_disable;
        uniform sampler2D seen : filter_linear, repeat_disable;
        uniform vec2 centre = vec2(0.5);
        uniform float span = 0.2;
        float roadMask(vec2 uv) {
            vec3 drawn = texture(drawing, uv).rgb;
            float age = smoothstep(0.3, 0.72, length(uv - 0.5)) * 0.5;
            drawn = clamp((drawn - vec3(0.275, 0.157, 0.055) * age) / (1.0 - age), 0.0, 1.0);
            return smoothstep(0.047, 0.054, (drawn.r - drawn.g) / max(drawn.r + drawn.g + drawn.b, 0.05));
        }
        // (M4 lead 12: the lattice hash is sin-free: fract(sin(dot)*43758) turns a 1-ulp difference between two evaluations of the
        // same lattice point (fma or not, 0.001 at args of 14000) into a 0.1 to 0.25 jump, so the warp tore along lattice lines)
        float hash2(vec2 p) {
            vec3 p3 = fract(vec3(p.xyx) * 0.1031);
            p3 += dot(p3, p3.yzx + 33.33);
            return fract((p3.x + p3.y) * p3.z);
        }
        float vnoise(vec2 p) {
            vec2 i0 = floor(p), f0 = fract(p);
            f0 = f0 * f0 * (3.0 - 2.0 * f0);
            return mix(mix(hash2(i0), hash2(i0 + vec2(1.0, 0.0)), f0.x), mix(hash2(i0 + vec2(0.0, 1.0)), hash2(i0 + vec2(1.0, 1.0)), f0.x), f0.y);
        }
        void fragment() {
            vec2 d = UV - 0.5;
            float r = length(d) * 2.0;
            vec2 uv = centre + d * span;
            // (M4 lead 9, fix C) a map, not a dark lens. The plate and the unexplored ground stay the HUD's own dark
            // (#1c1713 at 0.86); explored ground is worn vellum (120,105,80), flat as paper (the land's light and dark
            // ride on it within +-8); what is drawn on it is ink at full contrast (36,28,18): the roads (the drawing's
            // dirt, told by its hue once the sheet's aged edge is taken back out) and, as a wash, the water.
            vec3 panel = vec3(0.110, 0.090, 0.075);
            // (M4 lead 11: the bezel's fallback shadow was a filled disc over the lens, which dimmed it by about 0.64
            // and was compensated here by K; the shadow is a ring now and K is gone: the colors are as meant)
            // (the plate was seen through that veil: a2 = 1 - 0.65 * (1 - 0.86) = 0.909; panel2 = panel * 0.65 * 0.86 / a2 = panel * 0.615)
            vec3 panel2 = panel * 0.615;
            vec3 vellum = vec3(0.471, 0.412, 0.314);
            vec3 ink = vec3(0.141, 0.110, 0.071);
            vec3 roadFill = vec3(1.0, 0.906, 0.726) * 0.745;
            vec3 roadEdge = vec3(36.0, 28.0, 18.0) / 255.0;
            float px = max(fwidth(uv.x), fwidth(uv.y));
            vec3 drawn = texture(drawing, uv).rgb;
            float age = smoothstep(0.3, 0.72, length(uv - 0.5)) * 0.5;
            drawn = clamp((drawn - vec3(0.275, 0.157, 0.055) * age) / (1.0 - age), 0.0, 1.0);
            float sum = max(drawn.r + drawn.g + drawn.b, 0.05);
            // The road: its total width is the mask (the dirt hue) as before, its lower threshold raised so the
            // drawing's fine contour lines no longer pass; the fill is the mask shrunk by 1 px, the ring left is the ink edge.
            float road = roadMask(uv);
            float core = min(min(roadMask(uv + vec2(px, 0.0)), roadMask(uv - vec2(px, 0.0))), min(roadMask(uv + vec2(0.0, px)), roadMask(uv - vec2(0.0, px))));
            core = min(core, road);
            float water = smoothstep(0.030, 0.070, (drawn.b - drawn.r) / sum);
            float luma = dot(drawn, vec3(0.299, 0.587, 0.114));
            vec3 seenCol = vellum + vec3(clamp((luma - 0.72) * 0.25, -0.03, 0.03));
            seenCol = mix(seenCol, mix(vellum, ink, 0.55) + vec3(-0.02, 0.01, 0.03), water);
            seenCol = mix(seenCol, roadEdge, road);
            seenCol = mix(seenCol, roadFill, core);
            // The fog's edge: the explored grid (cells of about 10 px here) is blurred over its neighbours, not drawn
            // as cells, and crossed in 6 to 8 px: no stair steps.
            vec2 cell = 1.0 / vec2(textureSize(seen, 0));
            // (M4 lead 11: the lookup is warped in map-anchored pixels, so no straight side survives and the edge does not swim)
            vec2 wq = uv / max(px, 1e-6);
            vec2 wv = vec2(vnoise(wq / 26.0), vnoise(wq / 26.0 + vec2(17.3, 9.1))) - 0.5;
            wv += 0.5 * (vec2(vnoise(wq / 11.0 + vec2(5.1, 2.7)), vnoise(wq / 11.0 + vec2(31.7, 13.9))) - 0.5);
            vec2 fuv = uv + wv * 11.0 * px;
            float s = 0.0;
            for (int j = -1; j <= 1; j++)
                for (int i = -1; i <= 1; i++)
                    s += texture(seen, fuv + vec2(float(i), float(j)) * cell).r * (i == 0 ? 2.0 : 1.0) * (j == 0 ? 2.0 : 1.0);
            float known = smoothstep(0.23, 0.77, s / 16.0);
            // Beyond the drawing's edge the plate is the panel dark; the edge itself never shows (UI 20: a dead-straight
            // line where the drawing stopped): the drawing fades into it over ~28 screen px, the line wandering +-6 px.
            float e = min(min(uv.x, uv.y), min(1.0 - uv.x, 1.0 - uv.y)) / max(px, 1e-6);
            e += (vnoise(uv / max(px, 1e-6) / 40.0) - 0.5) * 12.0;
            known *= smoothstep(-4.0, 28.0, e);
            vec3 col = mix(panel2, seenCol, known);
            col *= mix(1.0, 0.86, smoothstep(0.7, 1.0, r));
            float ground = mix(0.909, 1.0, known);
            COLOR = vec4(col, ground * (1.0 - smoothstep(0.965, 1.0, r)));
        }
        """;
}

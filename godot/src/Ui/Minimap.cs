using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Play;

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
        // The rim: painted (minimap/frame.png, a ring wider than the disc) or a gold hairline.
        if (UiArt.Art("minimap/frame.png") is { } frame)
        {
            var f = new TextureRect { Texture = frame, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, MouseFilter = MouseFilterEnum.Ignore };
            f.Size = frame.GetSize();
            f.Position = (new Vector2(Diameter, Diameter) - f.Size) / 2;
            AddChild(f);
        }
        else
        {
            var ring = new Panel { Size = new Vector2(Diameter + 6, Diameter + 6), Position = new Vector2(-3, -3), MouseFilter = MouseFilterEnum.Ignore };
            var s = Style.Box(new Color(0, 0, 0, 0), Style.GoldDim, 3, (int)(Diameter / 2 + 3), 0);
            s.ShadowColor = new Color(0, 0, 0, 0.55f);
            s.ShadowSize = 12;
            ring.AddThemeStyleboxOverride("panel", s);
            AddChild(ring);
        }
        var north = Style.Label("N", Style.Display, 14, Style.GoldHi, false, HorizontalAlignment.Center);
        north.Size = new Vector2(20, 18);
        north.Position = new Vector2(Diameter / 2 - 10, -4);
        AddChild(north);
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
        mat.SetShaderParameter("centre", new Vector2((float)(px / extent + 0.5), (float)(pz / extent + 0.5)));
        mat.SetShaderParameter("dim", night ? 0.62f : 0.95f);
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

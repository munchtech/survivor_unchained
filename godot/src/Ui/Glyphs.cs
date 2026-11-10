using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Ui;

/// <summary>
/// Line glyphs for everything abstract (the web game's ui/glyphs.ts, as
/// data/content/glyphs.json): blessings, schools, skills, statuses, the
/// kinds of gear. One system: a 24-unit square, a 1.6 stroke, round caps, so
/// a row of them reads as a set. Drawn from their SVG paths at the size and
/// colour asked for. An item's glyph stands in until its photograph
/// (ItemPhotos) is taken.
/// </summary>
public static class Glyphs
{
    static readonly Dictionary<string, ImageTexture> cache = new();

    /// <summary>The path for any key: exact, an item's stand-in, by family, or a neutral mark (GlyphPaths).</summary>
    public static string PathFor(string key) => GlyphPaths.PathFor(key);

    /// <summary>The key whose painted icon an art key shows (itself, or the one it borrows: GlyphPaths.Borrowed).</summary>
    public static string IconKey(string key) => GlyphPaths.IconKey(key);

    /// <summary>The glyph key a skill shows on a HUD seat and on the level card (GlyphPaths.ForSkill).</summary>
    public static string ForSkill(string id, string art) => GlyphPaths.ForSkill(id, art);

    /// <summary>A glyph as a texture, at a size in pixels. A painted icon
    /// (art/ui/icons/glyph/KEY.png, white on transparent) is tinted the same
    /// way and wins, so painted icons keep every state colour the glyphs had. A painting may be borrowed (IconKey);
    /// the drawn line is the key's own glyph where glyphs.json has one, and only else the borrowed key's.</summary>
    public static Texture2D Texture(string key, int size, Color color, float stroke = 1.6f, bool line = false)
    {
        string paint = IconKey(key);
        key = GlyphPaths.LineKey(key);
        // Full-colour paintings (icons/glyph_color/KEY.png) keep their colours; asked for in a
        // dim tint (not ready, not known), they are greyed and darkened instead. line: the drawn
        // glyph only, so a set of them reads as one hand where only some are painted.
        if (!line && UiArt.Icon("glyph_color", paint) is { } colour) return color.Luminance < 0.5f || color.A < 0.6f ? Tinted(paint + "|dim", Grey(colour), color.Lightened(0.6f)) : colour;
        if (!line && UiArt.Icon("glyph", paint) is { } painted) return Tinted(paint, painted, color);
        var ck = $"{key}|{size}|{color.ToHtml()}|{stroke}";
        if (cache.TryGetValue(ck, out var t)) return t;
        var svg = $"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#{color.ToHtml(false)}" stroke-opacity="{color.A:0.###}" stroke-width="{stroke:0.##}" stroke-linecap="round" stroke-linejoin="round"><path d="{PathFor(key)}"/></svg>""";
        var img = new Image();
        img.LoadSvgFromString(svg, size / 24f);
        t = ImageTexture.CreateFromImage(img);
        cache[ck] = t;
        return t;
    }

    static readonly Dictionary<string, ImageTexture> tinted = new();

    static Texture2D Grey(Texture2D art)
    {
        var img = art.GetImage();
        if (img.IsCompressed()) img.Decompress();
        img.Convert(Image.Format.Rgba8);
        for (int y = 0; y < img.GetHeight(); y++)
            for (int x = 0; x < img.GetWidth(); x++)
            {
                var p = img.GetPixel(x, y);
                float l = p.Luminance * 0.55f;
                img.SetPixel(x, y, new Color(l, l, l, p.A));
            }
        return ImageTexture.CreateFromImage(img);
    }

    /// <summary>A painted icon multiplied by a colour: its light keeps its shape, the colour says its state.</summary>
    static Texture2D Tinted(string key, Texture2D art, Color c)
    {
        var ck = $"{key}|{c.ToHtml()}";
        if (tinted.TryGetValue(ck, out var hit)) return hit;
        var img = art.GetImage();
        if (img.IsCompressed()) img.Decompress();
        img.Convert(Image.Format.Rgba8);
        for (int y = 0; y < img.GetHeight(); y++)
            for (int x = 0; x < img.GetWidth(); x++)
            {
                var p = img.GetPixel(x, y);
                img.SetPixel(x, y, new Color(p.R * c.R, p.G * c.G, p.B * c.B, p.A * c.A));
            }
        return tinted[ck] = ImageTexture.CreateFromImage(img);
    }

    /// <summary>A glyph as a control.</summary>
    public static TextureRect Icon(string key, int size, Color? color = null, bool line = false)
    {
        return new TextureRect
        {
            Texture = Texture(key, size * 2, color ?? Style.GoldHi, 1.6f, line), CustomMinimumSize = new Vector2(size, size), ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize,
            StretchMode = TextureRect.StretchModeEnum.KeepAspectCentered, MouseFilter = Control.MouseFilterEnum.Ignore,
        };
    }
}

using System.Collections.Generic;
using System.Text.RegularExpressions;
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
    static Dictionary<string, string>? all;
    static readonly Dictionary<string, ImageTexture> cache = new();

    static Dictionary<string, string> All => all ??= Core.Json.Parse<Dictionary<string, string>>(Core.Json.ReadContent("glyphs.json"));

    /// <summary>What an item icon with no glyph of its own is drawn as.</summary>
    static readonly Dictionary<string, string> Items = new()
    {
        ["chest"] = "relic", ["picks"] = "key", ["lamp"] = "campfire", ["lantern"] = "campfire", ["helm_light"] = "helm", ["circlet"] = "ring",
        ["armor_light"] = "armor", ["armor_heavy"] = "armor", ["root"] = "thorn", ["vial"] = "drop", ["vial_orange"] = "drop", ["potion"] = "heart",
        ["antidote"] = "drop", ["bandage"] = "heart", ["pelt"] = "cloak", ["hide"] = "cloak", ["kerchief"] = "mask", ["wand_dark"] = "wand",
        ["ember"] = "flame", ["fang"] = "claw", ["seed"] = "leaf", ["dust"] = "smoke", ["bomb"] = "shatter", ["bone"] = "skull",
        ["flower"] = "perennial", ["lens"] = "eye",
    };

    static readonly (Regex Re, string Glyph)[] Families =
    {
        (new("slash|blade|oath|edge|grave"), "slash"), (new("axe|gyre|wheel"), "axe"), (new("dagger|knife|steel|cuts"), "dagger"),
        (new("arrow|volley|bow"), "arrow"), (new("mote|star|arcane"), "arcane"), (new("cinder|flame|fire|pyre|hell"), "flame"),
        (new("shard|frost|ice|rime|winter|hail|glacier"), "frost"), (new("arc|storm|sky|tempest|thunder"), "bolt"),
        (new("nova|dawn|sun|sanct|holy|ring"), "sun"), (new("beam|lance|gaze"), "spear"), (new("tether|siphon|coil|umbral|ruin|shadow"), "drain"),
        (new("blight|plague|rot"), "plague"), (new("thorn|bloom|root|briar"), "thorn"), (new("moon"), "moon"), (new("disc|aegis|reckon"), "disc"),
        (new("palm|temple"), "palm"), (new("herd|hunt"), "herd"), (new("chakram|gale|razor"), "chakram"), (new("zone|ground"), "retaura"),
    };

    /// <summary>The path for any key: exact, an item's stand-in, by family, or a neutral mark.</summary>
    public static string PathFor(string key)
    {
        if (All.TryGetValue(key, out var p)) return p;
        if (Items.TryGetValue(key, out var alias) && All.TryGetValue(alias, out var ap)) return ap;
        var k = key.ToLowerInvariant();
        foreach (var (re, g) in Families) if (re.IsMatch(k)) return All[g];
        return All["arcane"];
    }

    /// <summary>A glyph as a texture, at a size in pixels. A painted icon
    /// (art/ui/icons/glyph/KEY.png, white on transparent) is tinted the same
    /// way and wins, so painted icons keep every state colour the glyphs had.</summary>
    public static Texture2D Texture(string key, int size, Color color, float stroke = 1.6f)
    {
        // Full-colour paintings (icons/glyph_color/KEY.png) keep their colours; asked for in a
        // dim tint (not ready, not known), they are greyed and darkened instead.
        if (UiArt.Icon("glyph_color", key) is { } colour) return color.Luminance < 0.5f || color.A < 0.6f ? Tinted(key + "|dim", Grey(colour), color.Lightened(0.6f)) : colour;
        if (UiArt.Icon("glyph", key) is { } painted) return Tinted(key, painted, color);
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
    public static TextureRect Icon(string key, int size, Color? color = null)
    {
        return new TextureRect
        {
            Texture = Texture(key, size * 2, color ?? Style.GoldHi), CustomMinimumSize = new Vector2(size, size), ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize,
            StretchMode = TextureRect.StretchModeEnum.KeepAspectCentered, MouseFilter = Control.MouseFilterEnum.Ignore,
        };
    }
}

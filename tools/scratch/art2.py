R = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src'
def edit(name, pairs):
    p = R + '\\' + name
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert old in s, (name, old[:90])
        s = s.replace(old, new, 1)
    open(p, 'w', encoding='utf-8', newline='').write(s)

edit(r'Ui\GameHud.cs', [
("""    /// <summary>A bar's fill: painted (bars/NAME.png, stretched along the bar) or the drawn gradient.</summary>
    static TextureRect Fill(string art, Color[] colors, float[] stops, bool vertical = false)
    {
        var r = GradientRect(colors, stops, vertical);
        if (UiArt.Art($"bars/{art}.png") is { } tex) r.Texture = tex;
        return r;
    }""",
"""    /// <summary>A bar's fill: painted (bars/NAME.png, a strip that tiles along the bar, so it
    /// is never squashed as the bar fills) or the drawn gradient.</summary>
    static TextureRect Fill(string art, Color[] colors, float[] stops, bool vertical = false)
    {
        var r = GradientRect(colors, stops, vertical);
        if (UiArt.Art($"bars/{art}.png") is { } tex) { r.Texture = tex; r.StretchMode = TextureRect.StretchModeEnum.Tile; }
        return r;
    }"""),
])

edit(r'Ui\Glyphs.cs', [
("""    public static Texture2D Texture(string key, int size, Color color, float stroke = 1.6f)
    {
        if (UiArt.Icon("glyph", key) is { } painted) return Tinted(key, painted, color);""",
"""    public static Texture2D Texture(string key, int size, Color color, float stroke = 1.6f)
    {
        // Full-colour paintings (icons/glyph_color/KEY.png) keep their colours; asked for in a
        // dim tint (not ready, not known), they are greyed and darkened instead.
        if (UiArt.Icon("glyph_color", key) is { } colour) return color.Luminance < 0.5f || color.A < 0.6f ? Tinted(key + "|dim", Grey(colour), color.Lightened(0.6f)) : colour;
        if (UiArt.Icon("glyph", key) is { } painted) return Tinted(key, painted, color);"""),
("""    /// <summary>A painted icon multiplied by a colour: its light keeps its shape, the colour says its state.</summary>""",
"""    static Texture2D Grey(Texture2D art)
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

    /// <summary>A painted icon multiplied by a colour: its light keeps its shape, the colour says its state.</summary>"""),
])
print('done')

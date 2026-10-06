R = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src'
def edit(name, pairs):
    p = R + '\\' + name
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert old in s, (name, old[:90])
        s = s.replace(old, new, 1)
    open(p, 'w', encoding='utf-8', newline='').write(s)

edit(r'Ui\ItemPhotos.cs', [
("""        box.AddChild(r);
        if (photos.TryGetValue(key, out var t)) { r.Texture = t; return box; }""",
"""        box.AddChild(r);
        // A painted icon (art/ui/icons/item/KEY.png) wins over the photograph.
        if (UiArt.Icon("item", key) is { } painted) { r.Texture = painted; return box; }
        if (photos.TryGetValue(key, out var t)) { r.Texture = t; return box; }"""),
])
edit(r'Ui\Glyphs.cs', [
("""    /// <summary>A glyph as a texture, at a size in pixels.</summary>
    public static ImageTexture Texture(string key, int size, Color color, float stroke = 1.6f)
    {
        var ck = $"{key}|{size}|{color.ToHtml()}|{stroke}";
        if (cache.TryGetValue(ck, out var t)) return t;""",
"""    /// <summary>A glyph as a texture, at a size in pixels. A painted icon
    /// (art/ui/icons/glyph/KEY.png, white on transparent) is tinted the same
    /// way and wins, so painted icons keep every state colour the glyphs had.</summary>
    public static Texture2D Texture(string key, int size, Color color, float stroke = 1.6f)
    {
        if (UiArt.Icon("glyph", key) is { } painted) return Tinted(key, painted, color);
        var ck = $"{key}|{size}|{color.ToHtml()}|{stroke}";
        if (cache.TryGetValue(ck, out var t)) return t;"""),
("""    /// <summary>A glyph as a control.</summary>""",
"""    static readonly Dictionary<string, ImageTexture> tinted = new();

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

    /// <summary>A glyph as a control.</summary>"""),
])
print('done')

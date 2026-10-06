PAIRS = [
("""    public static Texture2D Texture(string key, int size, Color color, float stroke = 1.6f)
    {
        // Full-colour paintings (icons/glyph_color/KEY.png) keep their colours; asked for in a
        // dim tint (not ready, not known), they are greyed and darkened instead.
        if (UiArt.Icon("glyph_color", key) is { } colour) return color.Luminance < 0.5f || color.A < 0.6f ? Tinted(key + "|dim", Grey(colour), color.Lightened(0.6f)) : colour;
        if (UiArt.Icon("glyph", key) is { } painted) return Tinted(key, painted, color);""", """    public static Texture2D Texture(string key, int size, Color color, float stroke = 1.6f, bool line = false)
    {
        // Full-colour paintings (icons/glyph_color/KEY.png) keep their colours; asked for in a
        // dim tint (not ready, not known), they are greyed and darkened instead. line: the drawn
        // glyph only, so a set of them reads as one hand where only some are painted.
        if (!line && UiArt.Icon("glyph_color", key) is { } colour) return color.Luminance < 0.5f || color.A < 0.6f ? Tinted(key + "|dim", Grey(colour), color.Lightened(0.6f)) : colour;
        if (!line && UiArt.Icon("glyph", key) is { } painted) return Tinted(key, painted, color);"""),
("""    public static TextureRect Icon(string key, int size, Color? color = null)
    {
        return new TextureRect
        {
            Texture = Texture(key, size * 2, color ?? Style.GoldHi), CustomMinimumSize""", """    public static TextureRect Icon(string key, int size, Color? color = null, bool line = false)
    {
        return new TextureRect
        {
            Texture = Texture(key, size * 2, color ?? Style.GoldHi, 1.6f, line), CustomMinimumSize"""),
]

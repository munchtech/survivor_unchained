using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>The Godot half of SeatIcon (Ui/GlyphPaths.cs holds the key rule, which the tests compile).</summary>
public static partial class SeatIcon
{
    static readonly Color Cream = new("#F2E6C8");

    /// <summary>A skill's line glyph (the ground label's gift icon): the school lifted toward cream.</summary>
    public static Texture2D? LineGlyph(string key, int px, Color school) => Glyphs.Texture(key, px, school.Lerp(Cream, 0.35f), 2.4f, line: true);
}

/// <summary>bd-ui W4: a texture clipped to a circle, drawn as a textured polygon (no shader): the item icons in the weapon-set
/// discs and the stance card's ring.</summary>
public static class DiscIcon
{
    public static void Draw(CanvasItem ci, Vector2 c, float r, Texture2D tex, Color mod, float inset = 0)
    {
        const int N = 40;
        var pts = new Vector2[N];
        var uv = new Vector2[N];
        var cols = new Color[N];
        float k = 1 - inset;
        for (int i = 0; i < N; i++)
        {
            var d = new Vector2(Mathf.Cos(Mathf.Tau * i / N), Mathf.Sin(Mathf.Tau * i / N));
            pts[i] = c + d * r;
            uv[i] = new Vector2(0.5f, 0.5f) + d * 0.5f * k;
            cols[i] = mod;
        }
        ci.DrawPolygon(pts, cols, uv, tex);
    }

    /// <summary>What she wears in a slot as a drawable: its icon key (null: nothing worn) and its real texture if there is one.</summary>
    public static (string? Key, Texture2D? Tex) Of(SurvivorUnchained.Rpg.CharacterData? ch, SurvivorUnchained.Rpg.EquipSlot slot)
    {
        if (ch?.Equipment[slot] is not { } it || SurvivorUnchained.Rpg.Items.Get(it.Def) is not { } def || def.Icon == "") return (null, null);
        return (def.Icon, ItemPhotos.Real(def.Icon));
    }
}

/// <summary>(bd-ui W14) What a key seat really draws for a skill (Instrument.Socket.DrawRing): whenever it has a glyph key, the gold
/// inlay of its LINE glyph (DgGold) in the well, never a glyph_color painting (that was W13's wrong claim). The seat and the
/// new-key card both draw it through Gold, at the same size, so they can never differ.</summary>
public static class SeatPicture
{
    public const int CardPx = 26;

    /// <summary>The gold inlay texture (padded by DgGold.Pad each side) a seat draws for the glyph key at px.</summary>
    public static Texture2D Gold(string glyphKey, int px = CardPx) => DgGold.Of(glyphKey, px).Gold;

    /// <summary>The seat's fallback where it has no glyph key at all (never in play): the skill's painting, else its line glyph.</summary>
    public static Texture2D? Of(string glyphKey, Color school, int px = 78) =>
        UiArt.Icon("glyph_color", Glyphs.IconKey(glyphKey)) ?? Glyphs.Texture(glyphKey, px, school, line: true);
}

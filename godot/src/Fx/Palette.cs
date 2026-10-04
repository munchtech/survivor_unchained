using System.Text.RegularExpressions;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// One colour language for every effect (the web game's fx/palette.ts): a
/// school is always the same hue, so a fight reads by colour alone (orange
/// is fire, pale blue frost, violet arcane) whatever shape it comes in.
/// Core is the hot centre, Glow the light it throws, Dim the smoke or
/// residue it leaves; values over 1 are meant, to bloom. Linear colour.
/// </summary>
public static class Palette
{
    public readonly record struct Hues(Color Core, Color Glow, Color Dim, Color Light);

    static Color C(string hex) => new Color(hex).SrgbToLinear();
    static Color K(string hex, float k) { var c = new Color(hex).SrgbToLinear(); return new Color(c.R * k, c.G * k, c.B * k); }

    static readonly Hues[] schools = new Hues[System.Enum.GetValues<School>().Length];

    static Palette()
    {
        void Set(School s, string core, float ck, string glow, float gk, string dim, string light) =>
            schools[(int)s] = new Hues(K(core, ck), K(glow, gk), C(dim), new Color(light));
        Set(School.Physical, "#fff6e4", 2.2f, "#ffd9a0", 1.4f, "#8a7a66", "#ffd9a0");
        Set(School.Fire, "#ffe29a", 4, "#ff6a1a", 3, "#3a2a24", "#ff7a2a");
        Set(School.Frost, "#f0fbff", 3, "#6cc8ff", 2.4f, "#a8c8d8", "#8fd0ff");
        Set(School.Storm, "#ffffff", 4, "#8ab4ff", 3, "#5a6a9a", "#9ab8ff");
        Set(School.Nature, "#e8ffd0", 3, "#7aff4a", 2.4f, "#3a5a2a", "#9aff6a");
        Set(School.Arcane, "#fff0ff", 3.2f, "#c870ff", 2.8f, "#4a3a6a", "#cc88ff");
        Set(School.Holy, "#fffbe8", 3.6f, "#ffd46a", 2.8f, "#b8a070", "#ffe0a0");
        Set(School.Shadow, "#e8d8ff", 2.4f, "#8a4aff", 2.6f, "#1a1024", "#9a5cff");
    }

    public static Hues Of(School s) => schools[(int)s];

    public static readonly Color HostileRim = K("#ff5a2a", 2.2f), HostileDanger = K("#ff2a1a", 2.4f);

    /// <summary>The telegraph language (docs/bosses/MECHANICS.md section 2): amber a blow is
    /// coming here, violet this ground stays bad, pale blue stand here, grey this will be
    /// solid. Each has its own edge as well (filled, hatched, dashed, hard), so colour is
    /// never the only sign.</summary>
    public static readonly Color TeleBlow = K("#ff9a1a", 2.6f), TeleGround = K("#a050ff", 2.2f), TeleSafe = K("#8ad0ff", 2.2f), TeleWall = K("#c8c8d0", 1.6f);
    public static Color Telegraph(TelegraphKind k) => k switch
    {
        TelegraphKind.Ground => TeleGround, TelegraphKind.Safe => TeleSafe, TelegraphKind.Wall => TeleWall, _ => TeleBlow,
    };

    static readonly System.Collections.Generic.Dictionary<string, School> ofArt = new();

    /// <summary>The school a projectile or ground effect is, from its art
    /// (asked of every one in flight every frame: each art's answer is kept).</summary>
    public static School OfArt(string art)
    {
        if (ofArt.TryGetValue(art, out var s)) return s;
        return ofArt[art] = Read(art);
    }

    static School Read(string art)
    {
        if (Regex.IsMatch(art, "cinder|star|flame|fire|pyre|ember|firepot")) return School.Fire;
        if (Regex.IsMatch(art, "shard|frost|ice|hail|spear_ice|deep")) return School.Frost;
        if (Regex.IsMatch(art, "arc|storm|static")) return School.Storm;
        if (Regex.IsMatch(art, "green|blight|thorn|bloom|herd|root|plague|venom|gaze")) return School.Nature;
        if (Regex.IsMatch(art, "mote|moon|arcane")) return School.Arcane;
        if (Regex.IsMatch(art, "holy|disc|dawn|sun|sanct|reckon|aegis|crescent")) return School.Holy;
        if (Regex.IsMatch(art, "umbral|ruin|siphon|tether|blood|rend|harrow|shadow")) return School.Shadow;
        return School.Physical;
    }

    /// <summary>The colours loot glows by rarity.</summary>
    public static readonly Color[] Rarity = { new("#c8c0b0"), new("#6fd46a"), new("#5aa8ff"), new("#c070ff"), new("#ffb040"), new("#ff6a3a") };
}

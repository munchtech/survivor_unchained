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
        // Arcane's and shadow's hearts are violet, not white: past the tone curve's knee a pale
        // core reads as cream or grey over the pale dead, and the school is lost.
        Set(School.Arcane, "#e6b8ff", 2.0f, "#c870ff", 2.8f, "#4a3a6a", "#cc88ff");
        Set(School.Holy, "#fffbe8", 3.6f, "#ffd46a", 2.8f, "#b8a070", "#ffe0a0");
        Set(School.Shadow, "#b48cff", 1.7f, "#8a4aff", 2.6f, "#1a1024", "#9a5cff");
    }

    public static Hues Of(School s) => schools[(int)s];

    public static readonly Color HostileRim = K("#ff5a2a", 2.2f), HostileDanger = K("#ff2a1a", 2.4f);

    /// <summary>The telegraph language (docs/bosses/MECHANICS.md section 2): amber a blow is
    /// coming here, violet this ground stays bad, pale blue stand here, grey this will be
    /// solid. Each has its own edge as well (filled, hatched, dashed, hard), so colour is
    /// never the only sign.</summary>
    public static readonly Color TeleBlow = K("#ff9a1a", 2.6f), TeleGround = K("#a050ff", 2.2f), TeleSafe = K("#8ad0ff", 2.2f), TeleWall = K("#c8c8d0", 1.6f);
    /// <summary>An elite's or a boss's blow (the F7 lesson's "red line"): a hot scarlet, kept under AgX's fold to
    /// white, over ground darkened to old blood (an added red over lit dirt read salmon, the owner, 27 October; at #4a0a06 the
    /// bed lit brighter than the ground round it and read as a red rug, round 3).
    /// Its edge glows; her own low-life edge is a soft dark (0.45, 0.02, 0.02) wash at the screen's rim.</summary>
    public static readonly Color TeleDanger = C("#ff0612"), TeleDangerGround = new("#2c0604");
    /// <summary>The crowd's blows and a raising, in their own textures: a true amber, dim (about 0.4 of the red's light),
    /// over a faint dark bed (TeleBlow added at x2.5 went salmon under AgX).</summary>
    public static readonly Color TeleAmber = C("#ffbc30"), TeleAmberGround = new("#2a1d08");
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
        if (Regex.IsMatch(art, "holy|disc|dawn|sun|sanct|reckon|aegis|crescent|rebuke|watch_bell")) return School.Holy;
        if (Regex.IsMatch(art, "umbral|ruin|siphon|tether|blood|rend|harrow|shadow")) return School.Shadow;
        return School.Physical;
    }

    /// <summary>The colours loot glows by rarity.</summary>
    public static readonly Color[] Rarity = { new("#c8c0b0"), new("#6fd46a"), new("#5aa8ff"), new("#c070ff"), new("#ffb040"), new("#ff6a3a") };

    /// <summary>The den holds Rare and Epic to chroma 0.14 so the set's verdigris (BattleFx.Loot, ui_language.json "loot") is the
    /// loudest drop. Oklab chroma scaled down at the same lightness and hue; a colour already under the cap is returned as it is.</summary>
    public static Color CapChroma(Color c, float cmax = 0.14f)
    {
        static float Lin(float v) => v <= 0.04045f ? v / 12.92f : Mathf.Pow((v + 0.055f) / 1.055f, 2.4f);
        static float Gam(float v) { v = Mathf.Clamp(v, 0f, 1f); return v <= 0.0031308f ? v * 12.92f : 1.055f * Mathf.Pow(v, 1f / 2.4f) - 0.055f; }
        float r = Lin(c.R), g = Lin(c.G), b = Lin(c.B);
        float l = Mathf.Pow(0.4122214708f * r + 0.5363325363f * g + 0.0514459929f * b, 1f / 3f);
        float m = Mathf.Pow(0.2119034982f * r + 0.6806995451f * g + 0.1073969566f * b, 1f / 3f);
        float s = Mathf.Pow(0.0883024619f * r + 0.2817188376f * g + 0.6299787005f * b, 1f / 3f);
        float L = 0.2104542553f * l + 0.7936177850f * m - 0.0040720468f * s;
        float a = 1.9779984951f * l - 2.4285922050f * m + 0.4505937099f * s;
        float bb = 0.0259040371f * l + 0.7827717662f * m - 0.8086757660f * s;
        float C = Mathf.Sqrt(a * a + bb * bb);
        if (C <= cmax) return c;
        a *= cmax / C; bb *= cmax / C;
        float l2 = L + 0.3963377774f * a + 0.2158037573f * bb, m2 = L - 0.1055613458f * a - 0.0638541728f * bb, s2 = L - 0.0894841775f * a - 1.2914855480f * bb;
        l2 = l2 * l2 * l2; m2 = m2 * m2 * m2; s2 = s2 * s2 * s2;
        return new Color(Gam(4.0767416621f * l2 - 3.3077115913f * m2 + 0.2309699292f * s2),
            Gam(-1.2684380046f * l2 + 2.6097574011f * m2 - 0.3413193965f * s2),
            Gam(-0.0041960863f * l2 - 0.7034186147f * m2 + 1.7076147010f * s2), c.A);
    }
}

using System.Collections.Generic;
using System.Text.RegularExpressions;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The line glyphs' keys and paths (data/content/glyphs.json), with no Godot in it so the tests compile it; Glyphs.cs
/// draws them. Which path a key shows: its own entry, an item's stand-in, its family's, or the neutral mark; which key
/// a skill's seat shows (ForSkill); whose painting a key borrows (IconKey).
/// </summary>
public static class GlyphPaths
{
    static Dictionary<string, string>? all;

    static Dictionary<string, string> All => all ??= Core.Json.Parse<Dictionary<string, string>>(Core.Json.ReadContent("glyphs.json"));

    /// <summary>The neutral mark's key: what a key with no glyph, stand-in or family is drawn as.</summary>
    public const string Neutral = "arcane";

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

    /// <summary>The key has a line glyph of its own in glyphs.json.</summary>
    public static bool Own(string key) => All.ContainsKey(key);

    /// <summary>The path for any key: exact, an item's stand-in, by family, or a neutral mark.</summary>
    public static string PathFor(string key)
    {
        if (All.TryGetValue(key, out var p)) return p;
        if (Items.TryGetValue(key, out var alias) && All.TryGetValue(alias, out var ap)) return ap;
        var k = key.ToLowerInvariant();
        foreach (var (re, g) in Families) if (re.IsMatch(k)) return All[g];
        return All[Neutral];
    }

    /// <summary>Keys that show another key's PAINTED icon. Butcher's Cleaver's line glyph is its own (SkillLine) and its
    /// painting is its art's, slash_heavy.png, as it always was. (M4 lead 5: Heroic Leap, Shield Charge and Iron Vow no
    /// longer borrow the Leap's, the shield's and the fist's: they have their own, glyph_color/KEY.png, as Sunder has.)</summary>
    static readonly Dictionary<string, string> Borrowed = new()
    {
        ["butchers_cleaver"] = "slash_heavy",
    };

    /// <summary>The key whose painted icon an art key shows (itself, or the one it borrows).</summary>
    public static string IconKey(string key) => Borrowed.TryGetValue(key, out var lent) ? lent : key;

    /// <summary>The key a LINE render draws: the key's own glyphs.json entry where it has one, and only else the key it
    /// borrows (a borrowed painting never replaces a key's own line glyph).</summary>
    public static string LineKey(string key) => Own(key) ? key : IconKey(key);

    /// <summary>The path a line render of the key draws (PathFor of its LineKey).</summary>
    public static string LinePath(string key) => PathFor(LineKey(key));

    /// <summary>Skills whose seat glyph is not their art's: two skills may share an `art` (it also names the VFX: Sunder
    /// and Butcher's Cleaver are both slash_heavy) and still read apart on the bar.</summary>
    static readonly Dictionary<string, string> SkillLine = new()
    {
        ["cleaver"] = "butchers_cleaver", ["sunder"] = "sunder",
    };

    /// <summary>The glyph key a skill shows on a HUD seat and on the level card: its own line glyph where it has one
    /// (SkillLine), else its art's.</summary>
    public static string ForSkill(string id, string art) => SkillLine.TryGetValue(id, out var k) ? k : art;

    /// <summary>The glyph key an arena offer's card shows. An offer about a combat skill (a new one, a rank, a honing, an
    /// evolution: its Id is the skill's; a union: the skill it becomes) carries that skill's ART as its icon
    /// (Sim/LevelUp): shown by skill, as on the seats, so Sunder's card is Sunder's and not the Cleaver's. Any other
    /// offer (a passive, a blessing, a respite) shows the icon it carries.</summary>
    public static string ForOffer(Sim.Offer o) => o.Kind switch
    {
        Sim.OfferKind.Weapon or Sim.OfferKind.Rank or Sim.OfferKind.Hone or Sim.OfferKind.Evolve => ForSkill(o.Id, o.Icon),
        Sim.OfferKind.Union when Content.Unions.Find(o.Id) is { } u => ForSkill(u.Into, o.Icon),
        _ => o.Icon,
    };
}

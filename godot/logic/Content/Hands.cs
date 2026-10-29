using System.Collections.Generic;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Content;

/* The Hands (docs/design/CLASS_IDENTITY_AND_TALENTS.md 2.2 item 1): each calling's mechanic, always on and free,
 * bending any skill she carries by its tags. An accent, not the power (x1.05 to x1.10 alone). The numbers are data
 * (data/content/hands.json); the sim reads them in Sim/Hands.cs, and the card says them through Line, so the
 * tooltip is the truth (section 3.6, "no hidden multipliers"). */
public static class Hands
{
    public sealed class WardenHand
    {
        /// <summary>Every Nth blow (one firing) of a Melee or Thrown skill is heavy.</summary>
        public int Every = 4;
        /// <summary>Heavy on a creature: stunned this long, knocked back this many times as far.</summary>
        public double Stun = 0.3, Knockback = 2;
        /// <summary>Heavy on a boss: its stagger bar fills this much (a 0.3 s Stun's 0.06 + 0.12 x 0.3, rounded).</summary>
        public double Stagger = 0.1;
        /// <summary>Holy skills lay a Stone per champion struck (once a firing). Shield Arm's numbers when it is lit, else these.</summary>
        public int Stones = 6;
        public double Radius = 8, Lull = 6, Rebuke = 3, PerLevel = 0.08, Boss = 0.5;
    }

    public sealed class ReaverHand
    {
        /// <summary>A hit on a bleeding thing adds a stack of Frenzy (each Per attack speed, to Cap), at most one a Gate.</summary>
        public double Per = 0.01, Cap = 10, Fade = 3, Gate = 0.1;
        /// <summary>Below this share of health her Area skills are Area larger.</summary>
        public double Below = 0.5, Area = 0.15;
    }

    public sealed class ArcanistHand
    {
        /// <summary>A Spell that kills leaves Radius m of its element's ground for Seconds.</summary>
        public double Radius = 1, Seconds = 2;
        /// <summary>Fire: burning at Burn x the spell's damage a second. Frost: chill of this power. Arcane: a mark of this power.</summary>
        public double Burn = 0.5, Chill = 1, Mark = 1;
        /// <summary>Hand grounds alive at once (the oldest goes out): a horde's deaths never fill the field.</summary>
        public int Cap = 12;
        /// <summary>A marked thing a Spell kills passes its mark to the nearest unmarked within Reach, for MarkSeconds.</summary>
        public double Reach = 6, MarkSeconds = 4;
    }

    public sealed class StalkerHand
    {
        /// <summary>For Seconds after a dash ends, projectiles pierce Pierce more and blows on a champion strike true.</summary>
        public double Seconds = 1;
        public int Pierce = 1;
    }

    sealed class File
    {
        public WardenHand Warden = new();
        public ReaverHand Reaver = new();
        public ArcanistHand Arcanist = new();
        public StalkerHand Stalker = new();
    }

    static File? file;
    static File F => file ??= Json.Parse<File>(Json.ReadContent("hands.json"));

    public static WardenHand Warden => F.Warden;
    public static ReaverHand Reaver => F.Reaver;
    public static ArcanistHand Arcanist => F.Arcanist;
    public static StalkerHand Stalker => F.Stalker;

    /// <summary>Read the file again (a test or a variant that changed it).</summary>
    public static void Reload() => file = null;

    /// <summary>Melee and Thrown skills take the warden's heavy blow.</summary>
    public static bool Heavies(Tag[] tags) => tags.Has(Tag.Melee) || tags.Has(Tag.Thrown);

    /// <summary>A skill's own blows (not its summons'): what the reaver's Frenzy and the stalker's true blow read.</summary>
    static bool Strikes(Tag[] tags) => !tags.Has(Tag.Summon);

    /// <summary>The ground a Spell's kill leaves, by its school, or null for a school with none.</summary>
    public static string? GroundName(School s) => s switch
    {
        School.Fire => "burning",
        School.Frost => "chilling",
        School.Arcane => "moonlit",
        _ => null,
    };

    /// <summary>The card's line for a skill in a calling's hand ("In a warden's hand: ..."), or null when her Hand
    /// doesn't bend it. One function, so the draft and the day's card say the same.</summary>
    public static string? Line(string? calling, WeaponDef w) => Line(calling, w.Tags, w.School);

    public static string? Line(string? calling, Tag[] tags, School school)
    {
        var parts = new List<string>(2);
        switch (calling)
        {
            case "warden":
            {
                var h = Warden;
                if (Heavies(tags))
                    parts.Add($"every {Ordinal(h.Every)} blow is heavy (a {h.Stun:0.#} s stun and {Times(h.Knockback)} the knockback; a boss's stagger fills)");
                if (tags.Has(Tag.Holy) || school == School.Holy)
                    parts.Add($"each champion it strikes lays a Stone, and at {h.Stones} the wall answers with a rebuke");
                break;
            }
            case "reaver":
            {
                var h = Reaver;
                if (Strikes(tags)) parts.Add($"its hits on a bleeding thing add Frenzy (+{h.Per * 100:0.#}% attack speed each, to {h.Cap:0})");
                if (tags.Has(Tag.Area)) parts.Add($"below {h.Below * 100:0}% health it is {h.Area * 100:0}% larger");
                break;
            }
            case "arcanist":
            {
                var h = Arcanist;
                if (!tags.Has(Tag.Spell)) break;
                if (GroundName(school) is { } g) parts.Add($"what it kills leaves {h.Radius:0.#} m of {g} ground for {h.Seconds:0.#} s");
                parts.Add("a marked thing it kills passes its mark");
                break;
            }
            case "stalker":
            {
                var h = Stalker;
                if (!Strikes(tags)) break;
                string after = $"for {h.Seconds:0.#} s after a dash";
                if (tags.Has(Tag.Projectile))
                    parts.Add($"{after} it pierces {(h.Pierce == 1 ? "once" : $"{h.Pierce} times")} more and strikes champions true");
                else parts.Add($"{after} its blows on a champion strike true");
                break;
            }
        }
        if (parts.Count == 0) return null;
        string body = string.Join("; ", parts);
        string article = calling == "arcanist" ? "an" : "a";
        return $"In {article} {calling}'s hand: {body}.";
    }

    static string Ordinal(int n) => n + (n % 100 is 11 or 12 or 13 ? "th" : (n % 10) switch { 1 => "st", 2 => "nd", 3 => "rd", _ => "th" });
    static string Times(double k) => k == 2 ? "twice" : k == 3 ? "three times" : $"{k:0.#} times";
}

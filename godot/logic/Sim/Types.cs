using System;
using System.Collections.Generic;

namespace SurvivorUnchained.Sim;

/* The vocabulary the whole combat simulation shares. Kept free of the
 * engine so the simulation runs headless: in tests, in balance tools, and
 * under the view. Names turn into the web game's string keys (Key()) for
 * stat keys, saves and asset lookups. */

/// <summary>Damage schools. Every hit has one; every creature resists some.</summary>
public enum School { Physical, Fire, Frost, Storm, Nature, Arcane, Holy, Shadow }

/// <summary>Who someone fights for. Hostility between factions is data.</summary>
public enum Faction { Player, Ally, Pack, Kerchief, Dead, Lampling, Blight, Wild, Watch, Town }

/// <summary>Families drive "damage vs beasts", bestiary counts and who
/// recognises whom.</summary>
public enum Family { Beast, Wolf, Boar, Undead, Kerchief, Lampling, Blighted, Elemental, Human, Construct }

/// <summary>What a weapon, projectile or effect IS, so passives and items can
/// say what they apply to without naming weapons. The schools are tags too.</summary>
public enum Tag
{
    Projectile, Area, Melee, Summon, Aura, Beam, Chain, Orbit, Nova, Zone, Storm, Bounce, Ranged, Dot,
    Explosion, Trap, Heal, Thrown, Spell, Steel,
    Physical, Fire, Frost, Nature, Arcane, Holy, Shadow,
}

public enum StatusKind { Burn, Bleed, Chill, Frozen, Poison, Shock, Mark, Sear, Stun, Fear, Charm }

/// <summary>Enum values as the web game's keys ('physical', 'lowHealth') and back.</summary>
public static class EnumKey<T> where T : struct, Enum
{
    static readonly Dictionary<T, string> keys = new();
    static readonly Dictionary<string, T> back = new();
    public static readonly T[] All = Enum.GetValues<T>();

    static EnumKey()
    {
        foreach (var v in All)
        {
            var n = v.ToString();
            var k = char.ToLowerInvariant(n[0]) + n[1..];
            keys[v] = k;
            back[k] = v;
        }
    }

    public static string Of(T v) => keys[v];
    public static T Parse(string k) => back.TryGetValue(k, out var v) ? v : throw new ArgumentException($"no {typeof(T).Name} '{k}'");
    public static bool TryParse(string k, out T v) => back.TryGetValue(k, out v);
}

public static class Keys
{
    public static string Key<T>(this T v) where T : struct, Enum => EnumKey<T>.Of(v);

    public static Tag AsTag(this School s) => s switch
    {
        School.Physical => Tag.Physical, School.Fire => Tag.Fire, School.Frost => Tag.Frost, School.Storm => Tag.Storm,
        School.Nature => Tag.Nature, School.Arcane => Tag.Arcane, School.Holy => Tag.Holy, _ => Tag.Shadow,
    };

    /// <summary>The school a tag names, if it names one.</summary>
    public static School? AsSchool(this Tag t) => t switch
    {
        Tag.Physical => School.Physical, Tag.Fire => School.Fire, Tag.Frost => School.Frost, Tag.Storm => School.Storm,
        Tag.Nature => School.Nature, Tag.Arcane => School.Arcane, Tag.Holy => School.Holy, Tag.Shadow => School.Shadow,
        _ => null,
    };

    public static bool Has(this Tag[] tags, Tag t) => Array.IndexOf(tags, t) >= 0;
}

/// <summary>Resistances as fractions: 0.25 takes 25% less, -0.5 takes 50% more.</summary>
public sealed class Resists : Dictionary<School, double>
{
    public Resists() { }
    public Resists(Resists other) : base(other) { }
    public double Of(School s) => TryGetValue(s, out var v) ? v : 0;
}

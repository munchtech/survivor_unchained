using System;
using System.Collections.Generic;
using SurvivorUnchained.Core;

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

public static class Keys
{
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

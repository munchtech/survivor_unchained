using System;
using System.Collections.Generic;

namespace SurvivorUnchained.Sim;

/* Marks: what gear inscribes on one skill or one verb (docs/items/CATALOGUE.md §4), worn into
 * the Wayfinder's maps (crafting owns the items and their grades; combat what the Marks do).
 *
 * A Mark's strength is one number from 0 to 1 across its bracket (grade I to VI), lerped by
 * the skill or verb that reads it. Numbers on one skill go through SkillMods, folded into the
 * skill when it comes to hand; a Mark that changes what a skill does is read by that skill's
 * behaviour, by id. */
public static class Marks
{
    /// <summary>Volley looses a second volley at the farthest foe in reach, for [35 → 90]% of it. (Its floor
    /// is a third: a grade-I mark from a tier-1 ruler must be worth a seam.)</summary>
    public const string Ravine = "of_the_ravine";
    /// <summary>Cinderfall's blast leaves burning ground for [2 → 5] s.</summary>
    public const string FallingStar = "of_the_falling_star";
    /// <summary>The dash leaves a ring of holy fire for 3 s, burning for [30 → 90]% of the strongest
    /// skill's damage a second.</summary>
    public const string OpenGate = "of_the_open_gate";
    /// <summary>Axe Gyre gains an axe for every [6 → 3] foes within 5 m, to three more.</summary>
    public const string Gyre = "of_the_gyre";

    public static readonly string[] All = [Ravine, FallingStar, OpenGate, Gyre];

    public static double Lerp(double lo, double hi, double t) => lo + (hi - lo) * Math.Clamp(t, 0, 1);

    /// <summary>One skill's numbers over another's (a Mark's or crafting's on top of what it has).</summary>
    public static void Fold(WeaponMods into, WeaponMods m)
    {
        into.Damage *= m.Damage; into.Area *= m.Area; into.Cooldown *= m.Cooldown; into.Speed *= m.Speed; into.Duration *= m.Duration;
        into.Homing += m.Homing; into.Projectiles += m.Projectiles; into.Pierce += m.Pierce;
    }
}

public sealed partial class Battle
{
    /// <summary>The Marks worn, each at its strength (0 to 1 across its bracket). Empty but in maps.</summary>
    public readonly Dictionary<string, double> MarksWorn = new();
    /// <summary>Numbers on single skills from gear, by skill id, folded into each as it comes to hand.</summary>
    public readonly Dictionary<string, WeaponMods> SkillMods = new();

    /// <summary>The Mark's strength if it is worn.</summary>
    public bool Marked(string id, out double t) => MarksWorn.TryGetValue(id, out t);

    /// <summary>Put on what gear inscribes (a map does, as it begins): the Marks, and the skills'
    /// numbers folded into those already in hand.</summary>
    public void Wear(IReadOnlyDictionary<string, double> marks, IReadOnlyDictionary<string, WeaponMods> skillMods)
    {
        foreach (var (id, t) in marks) MarksWorn[id] = Math.Clamp(t, 0, 1);
        foreach (var (id, m) in skillMods)
        {
            SkillMods[id] = m;
            foreach (var w in Weapons) if (w.Id == id) Marks.Fold(w.Mods, m);
        }
    }

    /// <summary>The Open Gate: where the dash began, a ring of holy fire.</summary>
    void OpenGate(double x, double z)
    {
        if (!Marked(Marks.OpenGate, out double t)) return;
        double strongest = 0;
        foreach (var w in Weapons) strongest = Math.Max(strongest, w.Damage);
        var zn = SpawnZone(Side.Player, x, z, 2.4 * Math.Sqrt(Stats.Get(Stat.Area)), 3, strongest * Marks.Lerp(0.3, 0.9, t), School.Holy);
        if (zn != null) { zn.Tags = [Tag.Zone, Tag.Holy]; zn.Art = "holy_ground"; }
    }
}

using System;
using SurvivorUnchained.Core;
using System.Collections.Generic;

namespace SurvivorUnchained.Sim;

/* Stats, and how modifiers fold into them.
 *
 * Every number the survivor fights with is a stat, and every source that
 * changes one - an attribute, a piece of gear, a boon, a shrine's blessing,
 * an injury - contributes StatMods. They fold in three layers:
 *
 *   value = (base + sum of flat) * (1 + sum of increased) * product of (1 + more)
 *
 * "Increased" stacks additively with other increases; "more" multiplies.
 * Conditional modifiers (only while moving, only at low health) carry a
 * `When` the combat code sets active each tick. */

public enum ModKind { Flat, Inc, More }

/// <summary>When a conditional modifier applies.</summary>
public enum ModWhen { Moving, Still, Night, LowHealth, FullHealth, NearBeasts, InBurning, Shapeshifted, AfterDash }

public sealed record StatMod(string Stat, ModKind Kind, double Value, string Source = "", ModWhen? When = null);

/// <summary>The stat keys. Per-school, per-tag and per-family keys come from
/// the *Of helpers (cached strings, so a hit allocates nothing).</summary>
public static class Stat
{
    public const string MaxHealth = "maxHealth", Regen = "regen", Armor = "armor", MoveSpeed = "moveSpeed",
        PickupRadius = "pickupRadius", Dodge = "dodge", Block = "block", Damage = "damage", Cooldown = "cooldown",
        Area = "area", Projectiles = "projectiles", ProjectileSpeed = "projectileSpeed", Duration = "duration",
        Pierce = "pierce", CritChance = "critChance", CritDamage = "critDamage", Luck = "luck", XpGain = "xpGain",
        GoldGain = "goldGain", Healing = "healing", Lifesteal = "lifesteal", Thorns = "thorns",
        SummonDamage = "summonDamage", SummonHaste = "summonHaste", StatusChance = "statusChance",
        StatusDamage = "statusDamage", Knockback = "knockback", DashCharges = "dashCharges",
        DashCooldown = "dashCooldown", AbilityCooldown = "abilityCooldown", AbilityPower = "abilityPower",
        UltCharge = "ultCharge", LightRadius = "lightRadius", ExecuteThreshold = "executeThreshold",
        /// <summary>Slows and chills on the survivor are this much shorter and weaker (0..0.8).</summary>
        Tenacity = "tenacity";

    static readonly string[] damageSchool = Build<School>("damage.");
    static readonly string[] damageTag = Build<Tag>("damage.");
    static readonly string[] resist = Build<School>("resist.");
    static readonly string[] vs = Build<Family>("vs.");
    static readonly string[] from = Build<Family>("from.");

    static string[] Build<T>(string prefix) where T : struct, Enum
    {
        var all = EnumKey<T>.All;
        var o = new string[all.Length];
        for (int i = 0; i < all.Length; i++) o[i] = prefix + EnumKey<T>.Of(all[i]);
        return o;
    }

    public static string DamageOf(School s) => damageSchool[(int)s];
    public static string DamageOf(Tag t) => damageTag[(int)t];
    public static string ResistOf(School s) => resist[(int)s];
    public static string VsOf(Family f) => vs[(int)f];
    public static string FromOf(Family f) => from[(int)f];
}

public sealed class StatBlock
{
    /// <summary>Things with meaningful defaults when nobody has touched them.</summary>
    static readonly Dictionary<string, double> Defaults = MakeDefaults();

    static Dictionary<string, double> MakeDefaults()
    {
        var d = new Dictionary<string, double>
        {
            [Stat.Damage] = 1, [Stat.Cooldown] = 1, [Stat.Area] = 1, [Stat.ProjectileSpeed] = 1, [Stat.Duration] = 1,
            [Stat.XpGain] = 1, [Stat.GoldGain] = 1, [Stat.Healing] = 1, [Stat.SummonDamage] = 1, [Stat.SummonHaste] = 1,
            [Stat.StatusChance] = 0, [Stat.StatusDamage] = 1, [Stat.Knockback] = 1, [Stat.DashCharges] = 2,
            [Stat.DashCooldown] = 1, [Stat.AbilityCooldown] = 1, [Stat.AbilityPower] = 1, [Stat.UltCharge] = 1,
            [Stat.LightRadius] = 1, [Stat.Projectiles] = 0, [Stat.Pierce] = 0, [Stat.Dodge] = 0, [Stat.Block] = 0,
            [Stat.Lifesteal] = 0, [Stat.Thorns] = 0, [Stat.ExecuteThreshold] = 0,
        };
        // Every per-school or per-tag damage stat defaults to 1 (no change).
        foreach (var s in EnumKey<School>.All) d[Stat.DamageOf(s)] = 1;
        foreach (var t in EnumKey<Tag>.All) d[Stat.DamageOf(t)] = 1;
        return d;
    }

    List<StatMod> mods = new();
    readonly Dictionary<string, double> cache = new();
    readonly Dictionary<string, double> cacheRaw = new();
    Dictionary<string, double> baseVals = new();
    int activeMask;

    public void SetBase(IReadOnlyDictionary<string, double> b)
    {
        baseVals = new Dictionary<string, double>(b);
        Invalidate();
    }

    public Dictionary<string, double> GetBase() => new(baseVals);

    public void Add(StatMod m) { mods.Add(m); Invalidate(); }

    public void AddAll(IEnumerable<StatMod> ms) { mods.AddRange(ms); Invalidate(); }

    public void RemoveSource(string source)
    {
        int n = mods.RemoveAll(m => m.Source == source);
        if (n > 0) Invalidate();
    }

    public void RemoveWhere(Func<string, bool> test)
    {
        int n = mods.RemoveAll(m => test(m.Source));
        if (n > 0) Invalidate();
    }

    public bool HasSource(string source) => mods.Exists(m => m.Source == source);

    public IReadOnlyList<StatMod> List() => mods;

    public bool IsActive(ModWhen w) => (activeMask & (1 << (int)w)) != 0;

    /// <summary>The conditions in force this tick (evaluated per query).</summary>
    public void SetActive(IEnumerable<ModWhen> conds)
    {
        int m = 0;
        foreach (var c in conds) m |= 1 << (int)c;
        if (m != activeMask) { activeMask = m; Invalidate(); }
    }

    void Invalidate() { cache.Clear(); cacheRaw.Clear(); }

    double Fold(string stat, double flat)
    {
        double inc = 0, more = 1;
        foreach (var m in mods)
        {
            if (m.Stat != stat) continue;
            if (m.When is { } w && !IsActive(w)) continue;
            switch (m.Kind)
            {
                case ModKind.Flat: flat += m.Value; break;
                case ModKind.Inc: inc += m.Value; break;
                default: more *= 1 + m.Value; break;
            }
        }
        return flat * (1 + inc) * more;
    }

    public double Get(string stat)
    {
        if (cache.TryGetValue(stat, out var hit)) return hit;
        double flat = baseVals.TryGetValue(stat, out var b) ? b : Defaults.TryGetValue(stat, out var d) ? d : 0;
        var v = Fold(stat, flat);
        cache[stat] = v;
        return v;
    }

    /// <summary>For stats with no multiplicative default (vs.*, from.*, resist.*).</summary>
    public double GetRaw(string stat)
    {
        if (cacheRaw.TryGetValue(stat, out var hit)) return hit;
        var v = Fold(stat, baseVals.TryGetValue(stat, out var b) ? b : 0);
        cacheRaw[stat] = v;
        return v;
    }

    /// <summary>Damage multiplier for one hit: global damage, the school, every
    /// tag the source carries, and the family of what it hits.</summary>
    public double DamageMult(School school, Tag[] tags, Family? vs = null)
    {
        double m = Get(Stat.Damage) * Get(Stat.DamageOf(school));
        var st = school.AsTag();
        foreach (var t in tags) if (t != st) m *= Get(Stat.DamageOf(t));
        if (vs is { } f) m *= 1 + GetRaw(Stat.VsOf(f));
        return m;
    }

    /// <summary>Armour's damage reduction: diminishing, never total. 10 armour ~ 33%.</summary>
    public static double ArmorReduction(double armor) => armor <= 0 ? 0 : armor / (armor + 20);
}

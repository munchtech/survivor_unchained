using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Content;

/* The arsenal. Every weapon fires on its own; what the survivor does is
 * choose them, rank them and decide what they become.
 *
 *   - Tags and a school on everything, so gear and boons can say "your
 *     projectiles" or "your fire" and mean it.
 *   - Evolution BRANCHES. A rank-8 weapon does not have one destiny; it
 *     becomes whatever the rest of the build pulls it toward. Each branch
 *     names the passive skill that evolves it (a rank of it is enough), and
 *     a weapon with both passives asks which it should become.
 *
 * The skills themselves are data (data/content/skills.json, read by
 * SkillsJson); these are their types and the rank rules.
 *
 * Rank growth (applied by the runtime): +20% damage per rank, +4% area per
 * rank, +6% duration per rank, one more projectile at ranks 4 and 7. */

public enum WeaponBehavior { Aimed, Spray, Ring, Nova, Zone, Chain, Orbit, Storm, Bounce, Beam, Palm, Herd, Chakram, Slash, Raise }

/// <summary>A weapon's numbers; unset ones fall back (in an evolution's Set,
/// to the base).</summary>
public sealed class WeaponStats
{
    public double? Cooldown, Damage, Speed, Pierce, Range, Radius, Life, Homing, Splash, Spread, Duration, TickRate;
    public double? Chains, ChainRange, Bounces, OrbitRadius, OrbitSpeed, Strikes, StormRadius, BeamWidth, Reach, Arc;
    public double? Knockback, ExpandTime, Heal, Slow;
    public int? Projectiles;
    public bool? AtTarget;
    public StatusPayload? Status;
    /// <summary>A burst of shots in quick succession instead of all at once.</summary>
    public bool? Burst;
    /// <summary>Also leaves burning / hallowed / blighted ground where it hits.</summary>
    public GroundSpec? GroundOnHit;
    /// <summary>Projectiles split into smaller ones on hit.</summary>
    public int? SplitOnHit;
    /// <summary>Chains fork into two at each jump.</summary>
    public bool? Fork;
    /// <summary>What its projectiles hunt, if not the nearest.</summary>
    public Seek? Seek;
    /// <summary>Critical strike chance its blows have on top of the survivor's.</summary>
    public double? Crit;
    /// <summary>What a raising weapon calls up (an ally's kind).</summary>
    public string? Raises;
}

/// <summary>Multiplicative on damage, cooldown, area, speed, duration; additive on counts.</summary>
public sealed class EvoMods
{
    public double? Damage, Cooldown, Area, Speed, Duration;
    public int? Projectiles, Pierce, Bounces, Chains, Strikes;
}

public sealed class Evolution
{
    public string Id = "", Name = "", Description = "";
    /// <summary>The passive skills that evolve it: at rank 8 with a rank in any.</summary>
    public string[] Catalysts = System.Array.Empty<string>();
    public EvoMods Mods = new();
    public WeaponStats? Set;
    public WeaponBehavior? Behavior;
    public School? School;
    public Tag[]? AddTags;
    public string? Art;
    /// <summary>Rules it adds to the fight, the weapon's own (what it does
    /// beyond numbers: an execute, a bolt from the sky, a raised dead).</summary>
    public TriggerDef[] Triggers = System.Array.Empty<TriggerDef>();
}

public sealed class WeaponDef
{
    public string Id = "", Name = "";
    public School School;
    public WeaponBehavior Behavior;
    public Tag[] Tags = System.Array.Empty<Tag>();
    public WeaponStats Base = new();
    public string Art = "";
    /// <summary>Bosses and elites: crowd weapons hit one big target softly.</summary>
    public double? BossDamage;
    public string Description = "";
    public Evolution[] Evolutions = System.Array.Empty<Evolution>();
    /// <summary>Offered in the level-up pool (and so discoverable, and learnable by day).</summary>
    public bool Findable;
    /// <summary>Damage each rank adds (of the base). A single bolt grows more
    /// with its ranks than a field that already strikes a crowd does.</summary>
    public double Growth = Weapons.DamageStep;
    /// <summary>Rules it brings into the fight while carried (a union's own).</summary>
    public TriggerDef[] Triggers = System.Array.Empty<TriggerDef>();
}

public static class Weapons
{
    public const int MaxRank = 8;
    public const int MaxWeapons = 6;
    public const double DamageStep = 0.2, AreaStep = 0.04, DurationStep = 0.06;
    public const int ProjRankA = 4, ProjRankB = 7;

    /// <summary>Every combat skill, by id, in the order data/content/skills.json
    /// lists them (the draft's pool keeps that order).</summary>
    public static readonly Dictionary<string, WeaponDef> All = SkillsJson.File.Skills.ToDictionary(w => w.Id);

    /// <summary>The weapons the level-up draft can offer.</summary>
    public static readonly string[] Pool = All.Values.Where(w => w.Findable).Select(w => w.Id).ToArray();

    public static WeaponDef Get(string id) => All.TryGetValue(id, out var d) ? d : throw new KeyNotFoundException($"unknown weapon {id}");
}

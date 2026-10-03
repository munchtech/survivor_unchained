namespace SurvivorUnchained.Sim;

/* Triggers: the machinery a build is made of.
 *
 *   Fireball -> applies Burning
 *   Burning -> spreads when enemies die            (kindling: on kill, if burning)
 *   Burning enemies -> may explode                 (pyre burst: on kill, if burning, 30%)
 *   Explosions -> launch embers                     (emberseekers: on explode)
 *   Embers -> seek the strongest                    (seek: Strongest)
 *
 * Each line is one TriggerDef. None knows about the others; the chain
 * happens because an effect raises the same events a weapon hit does. A
 * depth limit keeps a chain from running forever inside one tick, and
 * internal cooldowns keep one rule from firing a thousand times a second -
 * inside those two limits a build is allowed to become absurd. That is the
 * reward. Items, boons, evolutions, traits and shrines all speak this. */

public enum TriggerEvent { Hit, Crit, Kill, Status, Explode, Freeze, Shatter, Hurt, Dash, Ability, Ember, Tick, LevelUp, Block, Dodge, PerfectDodge }

/// <summary>What an effect's damage is a fraction of: the blow that set it
/// off, the target's health, a flat number that grows with the ember, or the
/// damage of the weapon whose rule it is (an evolution's).</summary>
public enum Basis { Hit, MaxHp, Flat, Weapon }

public sealed class TriggerCond
{
    public StatusKind? TargetStatus;
    public Family? TargetFamily;
    public bool? Elite;
    public School? School;
    public Tag? Tag;
    public Tag? NotTag;
    public string? Weapon;
    /// <summary>Target health fraction below this, after the hit.</summary>
    public double? HpBelow;
    /// <summary>For Status events: which status was applied.</summary>
    public StatusKind? Applied;
    /// <summary>Survivor health fraction below this.</summary>
    public double? SelfHpBelow;
    public bool? Moving;
}

/// <summary>What a trigger does. The kinds are nested: Effect.Explode, Effect.Chain...</summary>
[System.Text.Json.Serialization.JsonConverter(typeof(EffectConverter))]
public abstract record Effect
{
    public sealed record Explode(double Radius, double Damage, Basis Basis, School School, StatusPayload? Status = null) : Effect;
    /// <summary>Target Hit: the struck; otherwise the toughest Count nearby.</summary>
    public sealed record Apply(StatusPayload Payload, bool OnHit, double Radius = 8, int Count = 1) : Effect;
    public sealed record Spread(StatusKind Kind, double Radius, int Count, int Stacks = 1) : Effect;
    public sealed record Missiles(int Count, double Damage, Basis Basis, School School, Seek Seek, double Speed, string Art, StatusPayload? Status = null) : Effect;
    public sealed record Chain(int Count, double Range, double Damage, Basis Basis, School School) : Effect;
    public sealed record Heal(double Amount, Basis Basis) : Effect;
    public sealed record Shield(double Amount, double Duration) : Effect;
    /// <summary>A barrier of a fraction of the survivor's health, added to what is there, up to Cap of it.</summary>
    public sealed record Barrier(double Fraction, double Cap, double Duration) : Effect;
    public sealed record Zone(double Radius, double Duration, double Dps, Basis Basis, School School, string Art, double Slow = 0, StatusPayload? Status = null) : Effect;
    public sealed record Buff(string Id, string Stat, double Value, ModKind Kind, double Duration, int MaxStacks = 1) : Effect;
    public enum CooldownScope { All, Ability, Dash }
    public sealed record Cooldown(double Seconds, CooldownScope Scope) : Effect;
    public enum RaiseKind { Ghoul, SpiritWolf }
    public sealed record Raise(RaiseKind Kind, double Duration, int Max) : Effect;
    public sealed record Pull(double Radius, double Strength) : Effect;
    public sealed record Execute(double Threshold) : Effect;
    public sealed record Nova(double Radius, double Damage, Basis Basis, School School, double Knockback = 0) : Effect;
    public sealed record Strike(int Count, double Radius, double Damage, Basis Basis, School School, double Area) : Effect;
    public sealed record Ember(double Amount) : Effect;
}

public sealed class TriggerDef
{
    public TriggerEvent On;
    public double? Chance;
    /// <summary>Internal cooldown in seconds.</summary>
    public double? Icd;
    public TriggerCond? When;
    public Effect[] Effects = System.Array.Empty<Effect>();
    /// <summary>Shown in tooltips so the player can see what the rule does.</summary>
    public string? Text;
}

public sealed class TriggerInstance
{
    public TriggerDef Def = null!;
    public string Source = "";
    /// <summary>What its damage is credited to (Battle.DamageBy): its source,
    /// or the weapon an evolution's rule belongs to.</summary>
    public string? Credit;
    public double Cd;
    /// <summary>Rank scales damage-bearing effects.</summary>
    public int Rank = 1;
    public int Count;
}

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

    ProcClass? weighs;

    /// <summary>(M3 MR 3) How the rule takes a chained cut (Battle.Fire at a weight under 1), read once from its
    /// effects. A method, not a property: nothing of it is written with the record.</summary>
    public ProcClass Weighs() => weighs ??= ClassOf(Effects);

    static ProcClass ClassOf(Effect[] effects)
    {
        bool sized = true, execute = effects.Length > 0;
        foreach (var fx in effects)
        {
            if (fx is not Effect.Execute) execute = false;
            sized &= fx switch
            {
                Effect.Explode f => f.Basis == Basis.Hit && f.Status == null,
                Effect.Missiles f => f.Basis == Basis.Hit && f.Status == null,
                Effect.Chain f => f.Basis == Basis.Hit,
                Effect.Strike f => f.Basis == Basis.Hit,
                Effect.Heal f => f.Basis == Basis.Hit,
                Effect.Nova f => f.Basis == Basis.Hit && f.Knockback == 0,
                Effect.Apply => true,
                _ => false,
            };
        }
        return execute ? ProcClass.Execute : sized ? ProcClass.Sized : ProcClass.Whole;
    }
}

/// <summary>(M3 MR 3) A chained cut is a share of a written blow and comes that much more often. Per second a rule
/// must give what it gave under the blows:
/// Sized: every effect is a fraction of the hit, or a status (weighed by the status step itself): it runs on every
/// cut, share-sized. Execute: a threshold, not a rate: it runs on every cut. Whole: everything else (a stack, ember,
/// a flat heal, seconds off a cooldown, a zone; a mix): it fires once per blow's worth of cuts and sees the blow.</summary>
public enum ProcClass { Whole, Sized, Execute }

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
    /// <summary>Times its effects ran (under chained cuts a Whole rule's firings, not its would-fires).</summary>
    public int Count;
    /// <summary>(M3 MR 3) A Whole rule under chained cuts: the share of a blow its would-fires have counted since it
    /// last ran, and whether it has ever run (the first is a whole one, as an every-N count's opening cut is).</summary>
    public double Part;
    public bool Begun;
}

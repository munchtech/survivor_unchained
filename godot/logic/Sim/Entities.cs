using SurvivorUnchained.Core;
using System;
using System.Collections.Generic;
using SurvivorUnchained.Content;

namespace SurvivorUnchained.Sim;

/* The things a fight is made of. Plain objects, pooled by the battle so
 * nothing is allocated in the middle of a horde. */

/// <summary>A status a hit carries: which, how likely, how strong, how long.
/// Stack: a bleed that deepens with each wound (up to five) rather than
/// keeping the worst of them.</summary>
public sealed record StatusPayload(StatusKind Kind, double Chance, double Power, double Duration, bool Stack = false);

/// <summary>Ground left burning (hallowed, blighted) where something lands.</summary>
public sealed record GroundSpec(double Radius, double Duration, double DpsPct);

public enum EnemyState { Rising, Active, Windup, Lunging, Recover, Burrowed, Surfacing, Casting, Dying, Dead, Stunned, Fleeing, Idle }
public enum Disposition { Hostile, Neutral, Ally }
public enum EnemyAnim { Move, Idle, Attack, Hit, Die, Rise, Windup, Cast, Burrow }
/// <summary>Whose a projectile or ground effect is.</summary>
public enum Side { Player, Enemy, Ally, World }
public enum Seek { Nearest, Elite, Random, Strongest, Marked }
public enum PickupKind { Ember, Gold, Heal, Magnet, Item, Material, Chest, Quest, Relic }

public sealed class StatusSlot
{
    public double T, Stacks, Power, Tick;
    /// <summary>Whose it is (Battle.DamageBy's key): what its damage is credited to.</summary>
    public string? From;
    public StatusSlot(double t, double stacks, double power, double tick) { T = t; Stacks = stacks; Power = power; Tick = tick; }
}

/// <summary>The statuses on a creature, one slot per kind.</summary>
public sealed class StatusSet
{
    readonly StatusSlot?[] slots = new StatusSlot?[EnumKey<StatusKind>.All.Length];
    public StatusSlot? this[StatusKind k] { get => slots[(int)k]; set => slots[(int)k] = value; }
    public bool Has(StatusKind k) => slots[(int)k] != null;
    public void Remove(StatusKind k) => slots[(int)k] = null;
    public void Clear() => Array.Clear(slots);
    /// <summary>The slot for a kind, made if missing.</summary>
    public StatusSlot Ensure(StatusKind k, double t, double stacks, double power, double tick) =>
        slots[(int)k] ??= new StatusSlot(t, stacks, power, tick);
}

/// <summary>A pooled thing: its id is its index and stays stable while alive.</summary>
public abstract class Pooled
{
    public int Id;
    public bool Alive;
}

public sealed class Named
{
    public string Title = "";
    public List<string> Carries = new();
    public string SourceHero = "";
}

public sealed class Enemy : Pooled
{
    public EnemyDef Def = null!;
    public int Level = 1;
    public double X, Z, Vx, Vz, Kbx, Kbz, Facing;
    public double Radius = 0.5, Mass = 1, Hp = 1, MaxHp = 1, Damage = 1, Speed = 1;
    public Faction Faction = Faction.Dead;
    /// <summary>Hostile attacks the player; Neutral ignores until provoked; Ally fights for the player.</summary>
    public Disposition Disposition;
    public bool Elite, Boss;
    public EnemyState State = EnemyState.Active;
    public double StateT, AttackT, RangedT, RaiseT;
    /// <summary>-1 the player, otherwise an enemy id; -2 none.</summary>
    public int Target = -1;
    public double RetargetT;
    /// <summary>Pack slot angle, orbit phase.</summary>
    public double Slot, Seed;
    public double LungeX, LungeZ;
    public readonly StatusSet Status = new();
    public double Flash;
    /// <summary>A clock for the view, and what it should be playing.</summary>
    public EnemyAnim Anim = EnemyAnim.Move;
    public double AnimT;
    public School LastSchool;
    public string? LastWeapon;
    /// <summary>The last blow: how hard, whether it crit, which way it went.</summary>
    public double LastBlow;
    public bool LastCrit;
    public double LastDx, LastDz;
    /// <summary>Its death burst it apart: nothing left to lie there.</summary>
    public bool Burst;
    public double DieT;
    /// <summary>A named creature: promoted when it killed the survivor, carrying what it took.</summary>
    public Named? Named;
    /// <summary>Summons and raised dead expire.</summary>
    public double LifeT;
    /// <summary>The weapon that raised it (an ally of a raising skill), for its damage and credit.</summary>
    public string? SummonedBy;
    /// <summary>For quest logic ("the alpha", "caravan guard").</summary>
    public string? Tag;
    /// <summary>Deaths caused by the player's damage (for credit).</summary>
    public bool Credit;
    /// <summary>Hurt by the player: neutral creatures turn hostile.</summary>
    public bool Provoked;
    /// <summary>Where it belongs; it drifts home when it has nothing to do.</summary>
    public double HomeX, HomeZ, Leash;
    /// <summary>Multiplier on damage taken (a ward, a vulnerable moment).</summary>
    public double TakenMul = 1;
    /// <summary>At rest, it notices the survivor only this close (0: from afar);
    /// roused, it hunts as far as its leash.</summary>
    public double Wake;
    public bool Roused;
    /// <summary>A reflection of the survivor: the horde turns on it.</summary>
    public bool Decoy;
    /// <summary>Marked as prey: below the line it dies outright.</summary>
    public bool Prey;
    /// <summary>When a wraith last drained it.</summary>
    public double DrainedAt = -99;

    public Enemy(int id) { Id = id; }
}

public sealed class Projectile : Pooled
{
    public Side Owner;
    public int OwnerId = -1;
    public double X, Z, Y = 1, Vx, Vz, Vy, Speed, Damage;
    public School School;
    public Tag[] Tags = Array.Empty<Tag>();
    public double Radius = 0.2;
    public int Pierce, Bounces;
    public double Life = 1, Age, Homing;
    public Seek? Seek;
    public int Target = -2;
    public string? Weapon;
    public string Art = "bolt";
    public StatusPayload? Status;
    public double Splash;
    public int SplitOnHit;
    public double Heal, Knockback;
    /// <summary>Out-and-back: flips to returning part way through its life.</summary>
    public bool Chakram, Returning;
    /// <summary>Lobbed pots ignore collisions until they land.</summary>
    public bool Lob;
    public double LandX, LandZ;
    public GroundSpec? GroundOnHit;
    public readonly List<int> Hits = new();
    /// <summary>When each of Hits was struck, for weapons that can hit the same
    /// creature again after Rehit seconds (orbits, herds).</summary>
    public readonly List<double> HitTimes = new();
    public double Rehit;
    public int HitCount;
    public double OrbitR, OrbitW, OrbitA;
    /// <summary>The weapon slot that owns an orbiting blade.</summary>
    public int SlotId = -1;
    public int Rank = 1, Depth;
    public double BossDamage = 1;
    /// <summary>Which way it is going (frontal guards).</summary>
    public double DirX, DirZ = 1;
    /// <summary>What its damage is credited to when no weapon threw it (a blessing's missiles).</summary>
    public string? Credit;

    public Projectile(int id) { Id = id; }

    public void Reset()
    {
        Owner = Side.Player; OwnerId = -1; X = Z = 0; Y = 1; Vx = Vz = Vy = 0; Speed = 0; Damage = 0;
        School = School.Physical; Tags = Array.Empty<Tag>(); Radius = 0.2; Pierce = 0; Bounces = 0; Life = 1; Age = 0;
        Homing = 0; Seek = null; Target = -2; Weapon = null; Art = "bolt"; Status = null; Splash = 0; SplitOnHit = 0;
        Heal = 0; Knockback = 0; Chakram = false; Returning = false; Lob = false; LandX = LandZ = 0; GroundOnHit = null;
        Hits.Clear(); HitTimes.Clear(); Rehit = 0; HitCount = 0; OrbitR = OrbitW = OrbitA = 0; SlotId = -1; Rank = 1;
        Depth = 0; BossDamage = 1; DirX = 0; DirZ = 1; Credit = null;
    }

    /// <summary>Point DirX, DirZ along its velocity.</summary>
    public void AimAlongVelocity()
    {
        double sp = Math.Sqrt(Vx * Vx + Vz * Vz);
        if (sp > 0) { DirX = Vx / sp; DirZ = Vz / sp; }
    }
}

public sealed class GroundZone : Pooled
{
    public Side Owner;
    public double X, Z, Radius = 1, Life = 1, Age, Tick = 0.5, TickT, Dps;
    public School School;
    public Tag[] Tags = Array.Empty<Tag>();
    public double Slow;
    public StatusPayload? Status;
    public string Art = "zone";
    public string? Weapon;
    public bool Follow;
    /// <summary>Armour for the player standing in it (Sanctified Earth).</summary>
    public double Armor;
    public double BossDamage = 1;
    /// <summary>What its damage is credited to when no weapon laid it.</summary>
    public string? Credit;

    public GroundZone(int id) { Id = id; }

    public void Reset()
    {
        Owner = Side.Player; X = Z = 0; Radius = 1; Life = 1; Age = 0; Tick = 0.5; TickT = 0; Dps = 0;
        School = School.Physical; Tags = Array.Empty<Tag>(); Slow = 0; Status = null; Art = "zone"; Weapon = null;
        Follow = false; Armor = 0; BossDamage = 1; Credit = null;
    }
}

public sealed class Pickup : Pooled
{
    public PickupKind Kind;
    public double X, Z, Vx, Vz, Value = 1;
    /// <summary>For items and materials: which.</summary>
    public string? Ref;
    public double Age;
    public bool Pulled;
    /// <summary>How long it has been flying to the survivor (it speeds up).</summary>
    public double PullT;
    /// <summary>Stays on the ground forever (a corpse's gear, a quest item).</summary>
    public bool Persistent;
    public int Tier;
    /// <summary>Gear: affixes it is likelier to roll when it is picked up.</summary>
    public string[]? Lean;

    public Pickup(int id) { Id = id; }
}

/// <summary>A fixed-capacity pool; ids are indices and stay stable while alive.</summary>
public sealed class Pool<T> where T : Pooled
{
    public readonly T[] Items;
    readonly Stack<int> free = new();
    public int Count { get; private set; }
    public int Capacity => Items.Length;

    public Pool(Func<int, T> make, int capacity)
    {
        Items = new T[capacity];
        for (int i = capacity - 1; i >= 0; i--)
        {
            Items[i] = make(i);
            free.Push(i);
        }
    }

    public T? Spawn()
    {
        if (free.Count == 0) return null;
        var it = Items[free.Pop()];
        it.Alive = true;
        Count++;
        return it;
    }

    public void Release(T it)
    {
        if (!it.Alive) return;
        it.Alive = false;
        free.Push(it.Id);
        Count--;
    }

    public IEnumerable<T> Living()
    {
        foreach (var it in Items) if (it.Alive) yield return it;
    }

    public void Clear()
    {
        foreach (var it in Items) if (it.Alive) Release(it);
    }
}

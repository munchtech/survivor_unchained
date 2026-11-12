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
/// <summary>What a creature in its Casting state is casting.</summary>
/// <summary>Aim: a crossbow planted and aiming (RangedSpec.Aim), its line fixed.</summary>
public enum CastKind { None, Raise, Summon, Slam, Aura, Aim }
/// <summary>Whose a projectile or ground effect is.</summary>
public enum Side { Player, Enemy, Ally, World }
public enum Seek { Nearest, Elite, Random, Strongest, Marked }
public enum PickupKind { Ember, Gold, Heal, Magnet, Item, Material, Chest, Quest, Relic }

/// <summary>An item filter's word on a drop: hidden, shown, or shown with emphasis.</summary>
public enum Verdict { Hidden, Shown, Emphasised }

public sealed class StatusSlot
{
    public double T, Stacks, Power, Tick;
    /// <summary>Seconds it has been on (open_vein reads a bleed's age).</summary>
    public double Age;
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
    /// <summary>(SU-053) Its slot's lifetime count: bumped each time the slot is spawned into, so a Lifetime kept past a
    /// tick stops matching when the slot is reused.</summary>
    public int Gen;
}

/// <summary>(Codex audit SU-053) A pooled thing known by its lifetime, never its slot: anything kept past a tick (a poison,
/// a ring's captives, a missile's owner, a brand or hook target) holds one; it stops matching when the slot is reused
/// (or the thing dies), and the effect ends. The default matches nothing.</summary>
public readonly record struct Lifetime(int Id, int Gen)
{
    public static readonly Lifetime None = new(-1, 0);
    public static Lifetime Of(Pooled? p) => p == null ? None : new(p.Id, p.Gen);
    /// <summary>p is this very thing, still alive.</summary>
    public bool Is(Pooled? p) => p != null && p.Alive && Gen != 0 && p.Id == Id && p.Gen == Gen;
}

public sealed class Named
{
    public string Title = "";
    public List<string> Carries = new();
    public string SourceHero = "";
    /// <summary>A champion's affix labels, as drawn under its bar (Content/Champions.cs: "Quaking", "Ironhide").</summary>
    public List<string> Affixes = new();
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
    /// <summary>Moved by the fight's script, not its own mind (a living wall, a caller holding a howl):
    /// the zone's BossTick decides for it, as for a boss.</summary>
    public bool Scripted;
    public EnemyState State = EnemyState.Active;
    public double StateT, AttackT, RangedT, RaiseT;
    /// <summary>The nearest a lunger may begin its run from (2 m; the zone lowers it for the Barrow Knight's first red line).</summary>
    public double LungeMin = 2;
    /// <summary>-1 the player, otherwise an enemy id; -2 none.</summary>
    public int Target = -1;
    public double RetargetT;
    /// <summary>Pack slot angle, orbit phase.</summary>
    public double Slot, Seed;
    public double LungeX, LungeZ;
    /// <summary>How far its target stood when it knelt to aim (RangedSpec.Aim).</summary>
    public double AimReach;
    public readonly StatusSet Status = new();
    public double Flash;
    /// <summary>A clock for the view, and what it should be playing.</summary>
    public EnemyAnim Anim = EnemyAnim.Move;
    public double AnimT;
    public School LastSchool;
    public string? LastWeapon;
    /// <summary>The last blow: how hard, whether it crit, which way it went.</summary>
    public double LastBlow;
    /// <summary>(M3 MR 3) How much of the Shock on it chained cuts have eaten, in blows (a Shock is eaten by one
    /// blow's worth; Battle.HitEnemy). 0 with no Shock, a fresh one, or only whole blows.</summary>
    public double ShockEaten;
    public bool LastCrit;
    /// <summary>The last blow was a tick of something in it (a burn, a poison): drawn as no blow.</summary>
    public bool LastDot;
    /// <summary>Until when (Battle.Time) a ground that is not the cold holds it slowed: its chill is
    /// drawn as no frost (a thicket's hold read as rime).</summary>
    public double HeldUntil;
    /// <summary>Its death is a Launch: thrown along the last blow (view only; DeathShow).</summary>
    public bool Launch;
    /// <summary>It fell in a mass kill (DeathShow.Mass): the view topples it fast once its hold ends (view only).</summary>
    public bool MassKill;
    public double LastDx, LastDz;
    /// <summary>Its death burst it apart: nothing left to lie there.</summary>
    public bool Burst;
    public double DieT;
    /// <summary>A named creature: promoted when it killed the survivor, carrying what it took.</summary>
    public Named? Named;
    /// <summary>(M5) Its rank in its pack, read before its plate: 1 a captain, 2 a champion (Content/Champions.Look), and
    /// that rank's body over its kind's: a size and a tint (with a little glow), as champions.json "looks" gives them.</summary>
    public byte Rank;
    public double RankScale = 1, RankR = 1, RankG = 1, RankB = 1, RankGlow;
    /// <summary>(M5 r3) A champion's affix rim: its hue in degrees (-1 none; Content/Champions.Look).</summary>
    public double RankRim = -1;
    /// <summary>(M5 r3) Where its trail last laid a pool (Ai: the next waits until it walks on); NaN none yet.</summary>
    public double TrailX = double.NaN, TrailZ = double.NaN;
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
    /// <summary>(SU-060) While protected (TakenMul 0) nothing lands; the mechanic named here still hears each hit (its boss
    /// script's OnBossHit, with no damage): the Barrow Lord's laying hastened by holy. Null: none (the default).</summary>
    public string? HearsWhileProtected;
    /// <summary>Sundered (the Long Cut's cleave): until this time (the battle's clock) it takes Sunder more from her side.</summary>
    public double SunderUntil, Sunder;
    /// <summary>Thrown up (Groundbreaker's upheaval): until this time it can't move or strike (a stun holds it) and
    /// takes AirMore more from her side.</summary>
    public double AirUntil, AirMore;
    /// <summary>When the Watch Bell last drew it (the wall's answer doesn't throw back what was drawn in the last 2 s).</summary>
    public double DrawnAt = -99;
    /// <summary>When Rebuke last struck it (a champion is struck again only after the skill's ChampionGap).</summary>
    public double RebukedAt = -99;
    /// <summary>Held back (the Watch Bell's iron): until this time (the battle's clock) it moves SlowBy slower.</summary>
    public double SlowUntil, SlowBy;
    /// <summary>Held by a kit telegraph (Sim/Tells.cs: a charger planted in its windup, a closing's ring waiting): until
    /// this time (the battle's clock) it neither moves nor strikes. 0: free.</summary>
    public double HoldUntil;
    /// <summary>A boss's signature being cast (ArenaBoss.Signature) until this time: the view pulses its off-screen pointer.</summary>
    public double SignatureUntil;
    /// <summary>Where it was Bound (StatusKind.Bound): it can't move away from here.</summary>
    public double BoundX, BoundZ;
    /// <summary>At rest, it notices the survivor only this close (0: from afar);
    /// roused, it hunts as far as its leash.</summary>
    public double Wake;
    public bool Roused;
    /// <summary>A reflection of the survivor: the horde turns on it.</summary>
    public bool Decoy;
    /// <summary>Laid down by its story while still alive (Corvane down in the doorway, CorvaneStory.Lie): drawn lying in
    /// its fall's last pose whatever its Anim, until it is released.</summary>
    public bool Laid;
    /// <summary>Its carried light (EnemyDef.CarriedLight) scaled and lifted by its script for a moment (Corvane's lamp burning up
    /// through his tell as it is raised overhead): 1 and 0 on every spawn.</summary>
    public double LightMul = 1, LightLift;
    /// <summary>A goal other than her (H1 item 6B, a board's lamp): it walks to (GoalX, GoalZ) down Battle.GoalFlow and
    /// stands there (the zone reads who is at it), turning on her for good once she is within GoalAggro of it, or it is
    /// frightened. False on every spawn.</summary>
    public bool Goal;
    public double GoalX, GoalZ, GoalAggro;
    /// <summary>A steer point (H6, the arena's director, Play/Zones/ArenaRun.Director.cs): while Steer, a hunter of hers walks
    /// to (SteerX, SteerZ) rather than straight at her; the zone moves the point (a pack's leader cutting her off ahead) and
    /// lets go of it. FlowUntil: until this time (the battle's clock) it follows the battle's flow field to her wholly (a
    /// foe stuck behind cover, recalled). False and 0 on every spawn.</summary>
    public bool Steer;
    public double SteerX, SteerZ, FlowUntil;
    /// <summary>When a pack's far foe next looks whether cover stands between it and its slot (Battle.PackRoundCover).</summary>
    public double CoverCheckAt;
    /// <summary>Marked as prey: below the line it dies outright.</summary>
    public bool Prey;
    /// <summary>1, or a quarter when a lamp reflex marked it by night (Classes 20): the execute line scales with it.</summary>
    public double PreySize = 1;
    /// <summary>When a wraith last drained it.</summary>
    public double DrainedAt = -99;
    /// <summary>Just thawed: it cannot freeze again until this runs out (3 s, a champion 5 s).</summary>
    public double ThawT;
    /// <summary>Raised from a grave by one of its own: it carries no ember (raising is never a farm).</summary>
    public bool Raised;
    /// <summary>A boss's gate: health stops here, and what would have gone past it is
    /// its Break (docs/SKILLS_DESIGN.md, "Bosses").</summary>
    public double HpFloor, Overflow;
    /// <summary>A boss's health the Flare took in this phase (the Break up to its cap included): it cuts an
    /// arena phase's floor (ArenaBoss.FloorNow).</summary>
    public double FlareTook;
    /// <summary>A boss's stagger bar (0..1), filled by what would lock a lesser creature;
    /// held while staggered, and resisting it for a while after.</summary>
    public double Stagger, StaggeredT, StaggerResistT;
    /// <summary>The firing (skill slot and cast) that last laid a warden Hand's Stone on it: one a firing.</summary>
    public long HandStoneKey;
    /// <summary>Lamps v2 (Sim/BoardRules.cs): when blue.poachers_mercy last doubled its bleed.</summary>
    public double PoachedAt = double.NegativeInfinity;
    /// <summary>How long that doubling shuts the next one out: 1 s, times the weight of the hit that doubled (a chained
    /// cut's share of its blow: the gate runs at the cut's pace, as an icd a cut starts).</summary>
    public double PoachedFor = 1;
    /// <summary>Quickened by its own kind's aura (pace and blows), and warded (less taken), for a while.</summary>
    public double HasteT, Haste = 1, WardT, Ward;
    /// <summary>The verbs' own clocks, what it is casting and where, the runs left in a
    /// chain of charges, and how many it has called.</summary>
    public double AuraT, SummonT, SlamT, CastX, CastZ;
    public CastKind Cast;
    public int ChainLeft, Summoned;

    public Enemy(int id) { Id = id; }
}

/// <summary>(SU-056) What an enemy's missile needs of its thrower at impact, copied when it is fired: its kind (family,
/// bite, name) and its damage (the bite's poison).</summary>
public readonly record struct Shot(EnemyDef Def, double Damage);

public sealed class Projectile : Pooled
{
    public Side Owner;
    public int OwnerId = -1;
    /// <summary>(SU-056) The thrower by lifetime (a slot reused in flight is not them) and what it needs of them at impact.</summary>
    public Lifetime OwnerLife = Lifetime.None;
    public Shot? OwnerShot;
    /// <summary>(SU-056) Fired by e: its slot, its lifetime and its snapshot.</summary>
    public void FiredBy(Enemy e) { OwnerId = e.Id; OwnerLife = Lifetime.Of(e); OwnerShot = new Shot(e.Def, e.Damage); }
    public double X, Z, Y = 1, Vx, Vz, Vy, Speed, Damage;
    public School School;
    public Tag[] Tags = Array.Empty<Tag>();
    public double Radius = 0.2;
    public int Pierce, Bounces;
    public double Life = 1, Age, Homing;
    public Seek? Seek;
    public int Target = -2;
    /// <summary>(SU-056) The homing target's lifetime where it was kept by one (checked only while it names Target's slot).</summary>
    public Lifetime TargetLife = Lifetime.None;
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
    /// <summary>The volley it was loosed in (the Crowded Sky: no two of a volley strike the same thing); 0 for none.</summary>
    public int Volley;
    /// <summary>The volley's rule is whole (the Crowded Sky looses its extra motes): it bars a second strike. Otherwise it only steers.</summary>
    public bool VolleyHard;
    public double BossDamage = 1;
    /// <summary>(M3 MR 3) The share of a written blow each of its hits stands for (the cast's CutW at the launch: a
    /// chained cut's projectile lands after its cast, when the weapon's live weight is 1 again); 1 for everything else.</summary>
    public double W = 1;
    /// <summary>(M3 MR 3 b1) The banked chained cut it was loosed in (Firing.CutBill): its hits pay it, its expiry with
    /// none refunds it. Null for everything else.</summary>
    internal Firing.CutBill? Bill;
    /// <summary>Which way it is going (frontal guards).</summary>
    public double DirX, DirZ = 1;
    /// <summary>What its damage is credited to when no weapon threw it (a blessing's missiles).</summary>
    public string? Credit;
    /// <summary>Loosed in a heavy blow (the warden's Hand): the id of the skill whose blow it is.</summary>
    public string? HeavyId;
    /// <summary>Loosed by an On-kill echo: its kills never echo again.</summary>
    public bool Echo;

    public Projectile(int id) { Id = id; }

    public void Reset()
    {
        Owner = Side.Player; OwnerId = -1; OwnerLife = Lifetime.None; OwnerShot = null; X = Z = 0; Y = 1; Vx = Vz = Vy = 0; Speed = 0; Damage = 0;
        School = School.Physical; Tags = Array.Empty<Tag>(); Radius = 0.2; Pierce = 0; Bounces = 0; Life = 1; Age = 0;
        Homing = 0; Seek = null; Target = -2; TargetLife = Lifetime.None; Weapon = null; Art = "bolt"; Status = null; Splash = 0; SplitOnHit = 0;
        Heal = 0; Knockback = 0; Chakram = false; Returning = false; Lob = false; LandX = LandZ = 0; GroundOnHit = null;
        Hits.Clear(); HitTimes.Clear(); Rehit = 0; HitCount = 0; OrbitR = OrbitW = OrbitA = 0; SlotId = -1; Rank = 1;
        Depth = 0; Volley = 0; VolleyHard = false; BossDamage = 1; W = 1; DirX = 0; DirZ = 1; Credit = null; HeavyId = null; Echo = false; Bill = null;
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
    /// <summary>What a boss takes of it, bosses alone (BossDamage lifts champions too): a staged Flare's fires carry its
    /// "bossMul", as its blows do.</summary>
    public double BossMul = 1;
    /// <summary>What its damage is credited to when no weapon laid it.</summary>
    public string? Credit;
    /// <summary>Laid by an On-kill echo: its kills never echo again.</summary>
    public bool Echo;

    public GroundZone(int id) { Id = id; }

    public void Reset()
    {
        Owner = Side.Player; X = Z = 0; Radius = 1; Life = 1; Age = 0; Tick = 0.5; TickT = 0; Dps = 0;
        School = School.Physical; Tags = Array.Empty<Tag>(); Slow = 0; Status = null; Art = "zone"; Weapon = null;
        Follow = false; Armor = 0; BossDamage = 1; BossMul = 1; Credit = null; Echo = false;
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
    /// <summary>Gear rolled whole where it fell (an Rpg.ItemInstance), taken as it is.</summary>
    public object? Payload;
    /// <summary>Its tier for the eye (Rpg.LootTier), or -1: the beam's height and colour, the sound.</summary>
    public int Loot = -1;
    /// <summary>What the survivor's item filter made of it: hidden things are not taken underfoot.</summary>
    public Verdict Look = Verdict.Shown;

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
        it.Gen++;
        Count++;
        return it;
    }

    /// <summary>(SU-061) A thing made outside the pool taken into a free slot as it is (its id becomes the slot's),
    /// so whoever holds it keeps a live reference. False: no slot free.</summary>
    public bool Adopt(T it)
    {
        if (free.Count == 0) return false;
        int i = free.Pop();
        it.Id = i;
        it.Alive = true;
        it.Gen = Items[i].Gen + 1;
        Items[i] = it;
        Count++;
        return true;
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

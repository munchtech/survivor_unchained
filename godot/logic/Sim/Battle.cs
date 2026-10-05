using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Sim;

/* One fight, from the first creature to the last: the survivor, the horde,
 * everything in the air and on the ground, and the rules that connect them.
 *
 * It knows nothing about towns, quests or save files. The world layer builds
 * a Battle for an area (with the survivor's stats, kit and the area's
 * collision), hooks the events it cares about, and reads the outcome. In
 * town the same Battle runs with combat off, so walking, colliding and the
 * camera are one system everywhere. */

public sealed record AttackAnim(string Weapon, double Angle, double T, bool Heavy);
public sealed class Leap { public double T, Dur, X0, Z0, X1, Z1; public AbilityKind Kind = AbilityKind.Leap; }

public sealed class PlayerState
{
    public double X, Z, Vx, Vz, Facing, Radius = 0.42, Hp;
    public bool Alive = true;
    public double Iframes, HurtT;
    public int DashCharges;
    public double DashRecharge, DashT, DashDX, DashDZ;
    /// <summary>The first moments of a dash, when slipping a blow is a
    /// perfect dodge (once a dash).</summary>
    public double DodgeWindow;
    public bool PerfectThisDash;
    public double AbilityCd, AbilityActive;
    public bool Moving;
    public double StillT, SlowT, SlowF = 1, BlockT, Shield, ShieldT, InvisibleT, SureCritT, BulwarkT;
    public Leap? Leap;
    public AttackAnim? AttackAnim;
    /// <summary>Standing in a hazard: burning, poisoned.</summary>
    public double BurnT, BurnDps, PoisonT, PoisonDps;
    /// <summary>What the burning and poison have taken since they last said so, and the clock for it.</summary>
    public double BurnSum, PoisonSum, DotT;
    /// <summary>What felled the survivor when it was not a blow (poison, burning).</summary>
    public string? FellTo;
    public int Revives;
    /// <summary>Times she has got up this fight (one at most: Cold, Then Not, however carried, or a
    /// story night's own rise).</summary>
    public int Rose;
    /// <summary>Risings From the Ashes still owed tonight (the ember's own, lost at dawn).</summary>
    public int Ashes;
    /// <summary>Blows that have reached the survivor since Watch Mail last turned one.</summary>
    public int MailCount;
    public Enemy? LastKiller;
    /// <summary>Since a blow last reached the survivor; where a burning dash last left fire.</summary>
    public double UnstruckT, WakeX, WakeZ;
    public bool VowUp;
}

/// <summary>A drop a creature leaves besides ember and gold. Rarity colours
/// an item's beam of light (and, for gear, is the rarity it is made at).</summary>
/// <summary>Lean: affixes the gear is likelier to roll (what answers a map's oaths).</summary>
public sealed record Loot(PickupKind Kind, string? Ref, double Value, bool Persistent = false, int? Rarity = null, string[]? Lean = null);

/// <summary>A map's oaths as rules of the fight (Maps/MapOffers.cs).</summary>
public sealed class MapRules
{
    /// <summary>How much faster the hostile are.</summary>
    public double FoeSpeed = 1;
    /// <summary>Their blows chill you (a slow) or poison you.</summary>
    public bool HitChill, HitPoison;
    /// <summary>Less mending, of every kind.</summary>
    public double HealCut;
    /// <summary>Their dead leave burning ground; their dead burst.</summary>
    public bool DeathFire, DeathBurst;
    /// <summary>Taken off every blow on them that is not a critical.</summary>
    public double IronSkin;
    /// <summary>How far the survivor's light carries (for the view).</summary>
    public double Light = 1;
    /// <summary>How fast a boss's stagger bar fills (the Oath of Iron fills it slower).</summary>
    public double StaggerTaken = 1;
    /// <summary>The ember the dead leave, over the usual (an oath's pay: "half again the ember").</summary>
    public double EmberGain = 1;
    /// <summary>How often the rank and file drop their gold (champions always as usual). An
    /// arena's horde is tens of thousands a night: at the day's rate the Kerchiefs alone paid
    /// 52k-109k gold (docs/CRAFTING_DESIGN.md), so there it is a fiftieth.</summary>
    public double FodderGold = 1;
    /// <summary>The same for champions, heralds and captains (bosses and minibosses always pay in
    /// full). An arena's thousand champions at the day's rate paid a Kerchief night 2.5k-3.3k gold,
    /// more than the rest of Act 1 together; there it is a tenth (crafting's measure).</summary>
    public double ChampionGold = 1;
    /// <summary>A map's suffixes on the survivor: armour counted for less, a dash slower to come
    /// back, regeneration, and what a draught mends (docs/SKILLS_DESIGN.md §17.2).</summary>
    public double ArmourMul = 1, DashRecharge = 1, RegenMul = 1, DraughtMul = 1;
}

public sealed class BattleHooks
{
    /// <summary>Every death, player-caused or not.</summary>
    public Action<Enemy, bool>? OnKill;
    /// <summary>What a creature drops besides ember and gold.</summary>
    public Func<Enemy, IEnumerable<Loot>>? OnLoot;
    /// <summary>An item/material/quest pickup reached the survivor. False
    /// leaves it on the ground (a full pack).</summary>
    public Func<Pickup, bool>? OnPickup;
    /// <summary>The survivor fell. True if something saved them.</summary>
    public Func<Enemy?, bool>? OnPlayerDeath;
    /// <summary>A boss or scripted creature's per-tick behaviour.</summary>
    public Func<Enemy, double, bool>? BossTick;
    /// <summary>Something damaged a tagged collider (a barrel, a bramble wall, a ward).</summary>
    public Action<string, int, School, double, double, double>? OnHitProp;
    /// <summary>A boss was hit (its school and the damage), for a weakness that breaks a channel.</summary>
    public Action<Enemy, School, double>? OnBossHit;
    /// <summary>A boss's stagger bar filled.</summary>
    public Action<Enemy>? OnBossStagger;
    /// <summary>A creature called up by one of its own (a summon), and who called it: the
    /// zone softens or hardens it as it does the rest of its horde.</summary>
    public Action<Enemy, Enemy>? OnCalled;

    /// <summary>Hooks that ask `zone`'s at the moment they are called. A zone sets some
    /// of its hooks only when a fight begins (the arena's boss at the half hour), so a
    /// copy taken when the battle starts would never see them: the game's boss scripts
    /// did not run for that reason, while the tests, which share the zone's hooks, did.</summary>
    public static BattleHooks Following(BattleHooks zone) => new()
    {
        OnKill = (e, byPlayer) => zone.OnKill?.Invoke(e, byPlayer),
        OnLoot = e => zone.OnLoot?.Invoke(e) ?? Array.Empty<Loot>(),
        OnPickup = p => zone.OnPickup?.Invoke(p) ?? true,
        OnPlayerDeath = killer => zone.OnPlayerDeath?.Invoke(killer) ?? false,
        BossTick = (e, dt) => zone.BossTick?.Invoke(e, dt) ?? false,
        OnHitProp = (tag, id, school, dmg, x, z) => zone.OnHitProp?.Invoke(tag, id, school, dmg, x, z),
        OnBossHit = (e, school, dmg) => zone.OnBossHit?.Invoke(e, school, dmg),
        OnBossStagger = e => zone.OnBossStagger?.Invoke(e),
        OnCalled = (e, by) => zone.OnCalled?.Invoke(e, by),
    };
}

public sealed class BattleSetup
{
    public uint Seed;
    public CollisionWorld Collision = null!;
    public Func<double, double, double> HeightAt = (_, _) => 0;
    public bool Combat;
    public StatBlock Stats = null!;
    public double StartX, StartZ, StartFacing;
    public List<(string Id, int Rank)> Weapons = new();
    public List<(TriggerDef Def, string Source)> Triggers = new();
    public AbilityKind? Ability;
    /// <summary>The art's rank and the facets chosen for it.</summary>
    public int ArtRank = 1;
    public List<string> Facets = new();
    public Dictionary<Faction, Faction[]>? Hostility;
    /// <summary>Carried ember from an expedition that did not end.</summary>
    public (int Level, double Xp)? Ember;
    public double? Hp;
}

public enum OfferKind { Weapon, Rank, Boon, Evolve, Heal, Gold, Hone, Union }

public sealed class Offer
{
    public OfferKind Kind;
    /// <summary>Offered as a milestone's blessing (settles the blessing, not a level).</summary>
    public bool Blessing;
    /// <summary>A great blessing (an arena's own), not a milestone's.</summary>
    public bool Great;
    public string Id = "";
    /// <summary>For Evolve: which branch.</summary>
    public string? Branch;
    public Rarity Rarity;
    public string Title = "", Text = "", Icon = "";
    public int? From, To;
    public Tag[] Tags = Array.Empty<Tag>();
    /// <summary>Ranks beyond the one (a surge: two at once).</summary>
    public int Surge;
    /// <summary>The build path it belongs to, if the build walks one it is on.</summary>
    public string? Path;
    /// <summary>Carried by day (attuned): it comes in at a higher rank.</summary>
    public bool Attuned;
    /// <summary>Why the draft dealt it (shown on the card): on your path, attuned, evolves something.</summary>
    public readonly List<string> Why = new();
    /// <summary>A combat skill's recipes: what evolves it, into what, and what it joins.</summary>
    public string? Recipe;
}

/// <summary>Everything about one blow on a creature.</summary>
public struct HitOpts
{
    public WeaponInst? Weapon;
    public bool Crit;
    /// <summary>No critical strike (damage over time, thorns).</summary>
    public bool NoCrit;
    public double Knockback;
    public double DirX, DirZ;
    public StatusPayload? Status;
    public bool Dot;
    public int Depth;
    public double? BossDamage;
    /// <summary>Damage from the survivor's summons.</summary>
    public bool Summon;
    /// <summary>Projectile direction, for frontal guards.</summary>
    public double FromX, FromZ;
    public bool Projectile;
    public bool NoProcs;
    /// <summary>A deliberate blow that may start a fight with a neutral creature.</summary>
    public bool Provoke;
    /// <summary>What the damage is credited to when no weapon dealt it (Battle.DamageBy).</summary>
    public string? Credit;
}

/// <summary>What a trigger sees when it fires.</summary>
public struct ProcCtx
{
    public Enemy? Target;
    public double? X, Z;
    public double? Damage;
    public School? School;
    public Tag[]? Tags;
    public bool Crit;
    public WeaponInst? Weapon;
    public StatusKind? Applied;
    public int? Depth;
}

public sealed partial class Battle
{
    public double Time;
    public readonly Rng Rng;
    public readonly EventStream Events = new();
    public readonly StatBlock Stats;
    public readonly PlayerState Player;
    public readonly List<WeaponInst> Weapons = new();
    public readonly Dictionary<string, int> Boons = new();
    public List<TriggerInstance> Triggers = new();
    public readonly Pool<Enemy> Enemies = new(i => new Enemy(i), 900);
    public readonly Pool<Projectile> Projectiles = new(i => new Projectile(i), 1400);
    public readonly Pool<GroundZone> Zones = new(i => new GroundZone(i), 160);
    public readonly Pool<Pickup> Pickups = new(i => new Pickup(i), 1400);
    public readonly SpatialHash Spatial;
    public readonly CollisionWorld Collision;
    public readonly FlowField Flow;
    public Func<double, double, double> HeightAt;
    public bool Combat;
    public BattleHooks Hooks = new();
    public AbilityKind? Ability;
    public Dictionary<Faction, Faction[]> War;
    /// <summary>Recent deaths, for grave-callers and necromancy.</summary>
    public readonly List<(double X, double Z, string Def, double T)> Graves = new();
    readonly List<StrikeSpec> strikes = new();
    public readonly Dictionary<string, Buff> Buffs = new();
    public MapRules Rules = new();
    /// <summary>When the horde's chargers may run, and its other marks' caps (Charges.cs).</summary>
    public readonly ChargeDirector Charges;
    public int EmberLevel = 1;
    public double EmberXp, EmberNext = 12;
    /// <summary>The ember burns here (it is night: an arena, the prologue): the
    /// dead leave its stones and it rises, card by card. By day, in the story,
    /// it does not; the survivor grows instead.</summary>
    public bool EmberOn = true;
    public int PendingLevels;
    /// <summary>Milestone levels whose blessing is still to be chosen (it comes
    /// on top of that level's skill, after it).</summary>
    public readonly List<int> PendingBlessings = new();
    /// <summary>Great blessings owed (an arena's first, its fifteenth minute's).</summary>
    public int GreatOwed;
    /// <summary>Cards more on the next great blessing (the ember-core broken in time).</summary>
    public int GreatExtra;
    public readonly HashSet<string> Discoveries = new();
    /// <summary>Where the fight is coming from, for the adaptive director.</summary>
    public readonly DamageProfile Profile = new();
    /// <summary>Damage dealt, by what dealt it: a weapon's id, a rule's source
    /// ("boon:kindling", "item:i4"), "art", "summon", "thorns". A status's
    /// damage over time goes to whatever put it there. For the damage meter
    /// and the balance harness.</summary>
    public readonly Dictionary<string, double> DamageBy = new();
    /// <summary>Who is dealing damage while no weapon is: the rule firing, the art.</summary>
    string? credit;
    public int KillCount;
    public readonly Dictionary<Family, int> KillsByFamily = new();
    /// <summary>Champions slain, by family: what a night's people yield to crafting (docs/CRAFTING_DESIGN.md 6.1).</summary>
    public readonly Dictionary<Family, int> ChampionsByFamily = new();
    public double DamageTaken, GoldGained;
    /// <summary>How much of GoldGained is already in the survivor's purse.</summary>
    public double GoldBanked;
    public double GoldTotal => GoldGained;
    /// <summary>Aim point for directional abilities (the pointer on the ground).</summary>
    public (double X, double Z)? Aim;
    /// <summary>Time-slip: everything but the survivor runs at this rate.</summary>
    public double WorldRate = 1, WorldRateT;
    public BattleOver? Over;
    /// <summary>Equipped item ids and the statuses gear applies, for evolution
    /// catalysts and the draft.</summary>
    public readonly HashSet<string> GearIds = new();
    public readonly HashSet<StatusKind> GearStatuses = new();
    /// <summary>Passives the kindled gear stands in for in a recipe; a fourth
    /// card in every skill draft; a fourth great choice (CombatKit).</summary>
    public readonly HashSet<string> Stands = new();
    public bool Roads, Omens;
    /// <summary>The survivor's calling (its own great blessing is offered to it alone).</summary>
    public string? Calling;
    public readonly HashSet<string> BannedCards = new();
    /// <summary>Skill tags the survivor's calling leans toward, for the draft.</summary>
    public readonly HashSet<Tag> Favours = new();
    /// <summary>The build paths the calling leans toward, for the draft.</summary>
    public readonly HashSet<string> CallingPaths = new();
    /// <summary>The skills carried by day, attuned for the night, and the rank
    /// each comes in at: the draft offers them first (Rpg/SkillBook.cs).</summary>
    public readonly Dictionary<string, int> Attuned = new();
    /// <summary>Skills learned by day and not carried: offered a little more.</summary>
    public readonly HashSet<string> Familiar = new();
    /// <summary>What the draft remembers between drafts (LevelUp).</summary>
    public readonly DraftMemory Drafting = new();
    /// <summary>Rerolls and banishes in hand; each milestone level adds a reroll, up to MaxRerolls.</summary>
    public int Rerolls = 3, Banishes = 2;
    public const int MaxRerolls = 9;
    readonly List<int> q = new();
    /// <summary>The projectile loop's own query list: hits inside it run
    /// queries of their own on q.</summary>
    readonly List<int> qProj = new();
    /// <summary>The creature AI's query list.</summary>
    internal readonly List<int> AiScratch = new();
    double auraT;

    public bool DraftOwed => PendingLevels > 0 || PendingBlessings.Count > 0 || GreatOwed > 0;

    static readonly Dictionary<Faction, Faction[]> DefaultWar = new()
    {
        [Faction.Pack] = [Faction.Kerchief, Faction.Lampling, Faction.Dead],
        [Faction.Kerchief] = [Faction.Pack, Faction.Wild, Faction.Dead],
        [Faction.Dead] = [Faction.Pack, Faction.Kerchief, Faction.Wild, Faction.Lampling],
        [Faction.Wild] = [Faction.Kerchief],
        [Faction.Lampling] = [Faction.Pack],
    };

    public Battle(BattleSetup s)
    {
        Rng = new Rng(s.Seed);
        Charges = new ChargeDirector(s.Seed);
        Collision = s.Collision;
        HeightAt = s.HeightAt;
        Combat = s.Combat;
        Stats = s.Stats;
        SetArt(s.Ability, s.ArtRank, s.Facets);
        War = s.Hostility ?? DefaultWar;
        Spatial = new SpatialHash(s.Collision.Size, 3, 900);
        Flow = new FlowField(s.Collision, 44);
        double maxHp = Stats.Get(Stat.MaxHealth);
        Player = new PlayerState
        {
            X = s.StartX, Z = s.StartZ, Facing = s.StartFacing, Hp = s.Hp ?? maxHp,
            DashCharges = RoundInt(Stats.Get(Stat.DashCharges)),
        };
        foreach (var (id, rank) in s.Weapons) AddWeapon(id, rank);
        foreach (var (def, source) in s.Triggers) AddTrigger(def, source);
        if (s.Ember is { } em)
        {
            EmberLevel = em.Level;
            EmberXp = em.Xp;
            EmberNext = EmberNeed(em.Level);
        }
    }

    /* ============================================================== tick == */

    public void Tick(double dt, double moveX, double moveZ)
    {
        if (Over != null) return;
        Time += dt;
        if (WorldRateT > 0)
        {
            WorldRateT -= dt;
            if (WorldRateT <= 0) WorldRate = 1;
        }
        double wdt = dt * WorldRate;

        RebuildSpatial();
        Charges.Tick(this, wdt);
        UpdatePlayer(dt, moveX, moveZ);
        Flow.Update(Player.X, Player.Z);
        if (Combat)
        {
            foreach (var w in Weapons.ToArray()) Firing.Tick(this, w, dt);
            TickAuras(dt);
            TickTriggers(dt);
        }
        foreach (var e in Enemies.Items) if (e.Alive) Ai.Update(this, e, wdt);
        UpdateProjectiles(dt, wdt);
        UpdateZones(dt);
        UpdateStrikes(dt);
        UpdateBlows(dt);
        UpdateRiseFire(dt);
        UpdatePickups(dt);
        UpdateBuffs(dt);
        if (Graves.Count > 40) Graves.RemoveRange(0, Graves.Count - 40);
    }

    void RebuildSpatial()
    {
        Spatial.Clear();
        foreach (var e in Enemies.Items)
            if (e.Alive && e.State != EnemyState.Dying && e.State != EnemyState.Burrowed) Spatial.Insert(e.Id, e.X, e.Z);
    }

    /* ============================================================ player == */

    void UpdatePlayer(double dt, double mx, double mz)
    {
        var p = Player;
        if (!p.Alive) return;
        var st = Stats;
        p.Iframes = Math.Max(0, p.Iframes - dt);
        p.DodgeWindow = Math.Max(0, p.DodgeWindow - dt);
        p.HurtT = Math.Max(0, p.HurtT - dt);
        p.AbilityCd = Math.Max(0, p.AbilityCd - dt);
        p.InvisibleT = Math.Max(0, p.InvisibleT - dt);
        p.SureCritT = Math.Max(0, p.SureCritT - dt);
        p.BulwarkT = Math.Max(0, p.BulwarkT - dt);
        p.SlowT = Math.Max(0, p.SlowT - dt);
        if (p.SlowT <= 0) p.SlowF = 1;
        if (p.ShieldT > 0) { p.ShieldT -= dt; if (p.ShieldT <= 0) p.Shield = 0; }
        p.UnstruckT += dt;
        if (Boons.TryGetValue("iron_vow", out int vow)) Vow(vow);
        if (p.AttackAnim != null && Time - p.AttackAnim.T > 0.6) p.AttackAnim = null;

        // Dash charges come back one at a time.
        int maxCharges = RoundInt(st.Get(Stat.DashCharges));
        if (p.DashCharges < maxCharges)
        {
            p.DashRecharge += dt * DashHaste() * Rules.DashRecharge / st.Get(Stat.DashCooldown);
            if (p.DashRecharge >= Abilities.Dash.Recharge) { p.DashRecharge = 0; p.DashCharges++; }
        }

        // Warding light recharges.
        int blockRank = RoundInt(st.Get(Stat.Block));
        if (blockRank > 0 && p.BlockT > 0) p.BlockT = Math.Max(0, p.BlockT - dt);

        // Regeneration and hazards on the survivor.
        double regen = st.Get(Stat.Regen) * Rules.RegenMul;
        if (regen > 0 && p.Hp < MaxHp) HealPlayer(regen * dt, "regen", true);
        // Bitterroot draws it: what burns or poisons the survivor wears off twice as fast.
        double cure = Boons.ContainsKey("recovery") ? 2 : 1;
        if (p.BurnT > 0) { p.BurnT -= dt * cure; Dot(ref p.BurnSum, p.BurnDps * dt, School.Fire, "burning", dt); }
        if (p.PoisonT > 0) { p.PoisonT -= dt * cure; Dot(ref p.PoisonSum, p.PoisonDps * dt, School.Nature, "poison", dt); }
        if (!p.Alive) return;
        if (TickArt(dt)) return;

        // Leaping: an arc through the air, untouchable until landing.
        if (p.Leap is { } leap)
        {
            leap.T += dt;
            double k = Math.Min(1, leap.T / leap.Dur);
            p.X = leap.X0 + (leap.X1 - leap.X0) * k;
            p.Z = leap.Z0 + (leap.Z1 - leap.Z0) * k;
            p.Iframes = Math.Max(p.Iframes, 0.05);
            if (k >= 1) { p.Leap = null; LandLeap(leap); }
            Collision.Resolve(ref p.X, ref p.Z, p.Radius, true);
            return;
        }

        // Dashing: fast, fixed direction, invulnerable.
        if (p.DashT > 0)
        {
            p.DashT -= dt;
            double dsp = Abilities.Dash.Distance / Abilities.Dash.Time;
            p.X += p.DashDX * dsp * dt;
            p.Z += p.DashDZ * dsp * dt;
            Collision.Resolve(ref p.X, ref p.Z, p.Radius, true);
            if (Boons.TryGetValue("cinderwake", out int wake) && Dist(p.X, p.Z, p.WakeX, p.WakeZ) > 0.9) Wake(wake);
            // Out of a dash with your feet under you: a burst of pace, so dashes chain.
            if (p.DashT <= 0)
            {
                AddBuff("momentum", Stat.MoveSpeed, Abilities.Dash.MomentumSpeed, ModKind.Inc, Abilities.Dash.Momentum, 1);
                dashEnded = Time;
                p.Vx = p.DashDX * Stats.Get(Stat.MoveSpeed);
                p.Vz = p.DashDZ * Stats.Get(Stat.MoveSpeed);
            }
            return;
        }

        double speed = st.Get(Stat.MoveSpeed) * p.SlowF;
        if (p.BulwarkT > 0 && !Has("marching_wall")) speed *= 0.45;
        double targetVX = mx * speed, targetVZ = mz * speed;
        double accel = 1 - Math.Exp(-dt * 14);
        p.Vx += (targetVX - p.Vx) * accel;
        p.Vz += (targetVZ - p.Vz) * accel;
        p.X += p.Vx * dt;
        p.Z += p.Vz * dt;
        Collision.Resolve(ref p.X, ref p.Z, p.Radius, true);
        double sp = Math.Sqrt(p.Vx * p.Vx + p.Vz * p.Vz);
        p.Moving = sp > 0.6;
        if (p.Moving)
        {
            p.Facing = Math.Atan2(p.Vx, p.Vz);
            p.StillT = 0;
            Profile.Moving += dt;
        }
        else
        {
            p.StillT += dt;
            Profile.Still += dt;
        }
        condScratch.Clear();
        condScratch.Add(p.Moving ? ModWhen.Moving : ModWhen.Still);
        if (p.Hp < MaxHp * 0.35) condScratch.Add(ModWhen.LowHealth);
        if (p.Hp >= MaxHp - 0.01) condScratch.Add(ModWhen.FullHealth);
        // What gear asks of the moment: the dark, beasts close, fire underfoot, a dash just done.
        if (Night) condScratch.Add(ModWhen.Night);
        if (Time - dashEnded < 1.5) condScratch.Add(ModWhen.AfterDash);
        if ((senseT -= dt) <= 0)
        {
            senseT = 0.25;
            nearBeasts = HostilesInRadius(p.X, p.Z, 8).Any(e => e.Def.Family is Family.Wolf or Family.Boar or Family.Beast);
            inBurning = false;
            foreach (var z in Zones.Items)
                if (z.Alive && z.School == School.Fire && Dist(z.X, z.Z, p.X, p.Z) < z.Radius) { inBurning = true; break; }
        }
        if (nearBeasts) condScratch.Add(ModWhen.NearBeasts);
        if (inBurning) condScratch.Add(ModWhen.InBurning);
        Stats.SetActive(condScratch);
    }

    /// <summary>The dark (a night in the world, every arena): gear that
    /// answers to the night is awake.</summary>
    public bool Night;
    double senseT, dashEnded = -9;
    bool nearBeasts, inBurning;

    readonly List<ModWhen> condScratch = new();

    public double MaxHp => Math.Max(1, Stats.Get(Stat.MaxHealth));

    /// <summary>Space: a short, invulnerable burst of movement.</summary>
    public bool Dash(double dirX, double dirZ)
    {
        var p = Player;
        if (!p.Alive || p.DashCharges <= 0 || p.DashT > 0 || p.Leap != null || Art.Rush != null) return false;
        double dx = dirX, dz = dirZ;
        if (Len(dx, dz) < 0.1) { dx = Math.Sin(p.Facing); dz = Math.Cos(p.Facing); }
        double m = Len(dx, dz);
        p.DashDX = dx / m; p.DashDZ = dz / m;
        p.DashT = Abilities.Dash.Time;
        p.Iframes = Math.Max(p.Iframes, Abilities.Dash.Iframes);
        p.DodgeWindow = Abilities.Dash.Perfect * (Boons.GetValueOrDefault("duelists_grace") >= 2 ? 1.5 : 1);
        p.WakeX = p.X; p.WakeZ = p.Z;
        p.PerfectThisDash = false;
        p.DashCharges--;
        double x0 = p.X, z0 = p.Z;
        Events.Emit(new Ev.Dash { X0 = x0, Z0 = z0, X1 = x0 + p.DashDX * Abilities.Dash.Distance, Z1 = z0 + p.DashDZ * Abilities.Dash.Distance });
        Fire(TriggerEvent.Dash, new ProcCtx { X = p.X, Z = p.Z });
        OpenGate(x0, z0);
        return true;
    }

    /// <summary>Stop a channel or cast in progress.</summary>
    public void Interrupt(Enemy e)
    {
        if (e.State == EnemyState.Casting || e.State == EnemyState.Windup)
        {
            e.State = EnemyState.Stunned;
            e.StateT = 0.8;
            e.RaiseT = Math.Max(e.RaiseT, 3);
            Events.Emit(new Ev.Bark { X = e.X, Z = e.Z, Text = "Interrupted!" });
        }
    }

    /* =========================================================== queries == */

    /// <summary>Can the survivor's side hurt this creature?</summary>
    public bool HostileToPlayer(Enemy e)
    {
        if (!e.Alive || e.State == EnemyState.Dying || e.State == EnemyState.Burrowed) return false;
        if (e.Disposition == Disposition.Ally) return false;
        if (e.Disposition == Disposition.Neutral) return e.Provoked;
        return true;
    }

    /// <summary>Targetable by weapons: hostile, or neutral and provoked.</summary>
    public bool Targetable(Enemy e) =>
        e.Alive && e.State != EnemyState.Dying && e.State != EnemyState.Burrowed && e.Disposition != Disposition.Ally &&
        (e.Disposition == Disposition.Hostile || e.Provoked);

    public bool FactionsAtWar(Faction a, Faction b)
    {
        if (a == b) return false;
        return (War.TryGetValue(a, out var wa) && Array.IndexOf(wa, b) >= 0) || (War.TryGetValue(b, out var wb) && Array.IndexOf(wb, a) >= 0);
    }

    /// <summary>The farthest the survivor's side can hurt within r.</summary>
    public Enemy? FarthestHostile(double x, double z, double r)
    {
        Enemy? best = null;
        double bd = -1;
        Spatial.Query(x, z, r, q);
        foreach (var id in q)
        {
            var e = Enemies.Items[id];
            if (!Targetable(e)) continue;
            double d = (e.X - x) * (e.X - x) + (e.Z - z) * (e.Z - z);
            if (d <= r * r && d > bd) { bd = d; best = e; }
        }
        return best;
    }

    public Enemy? NearestHostile(double x, double z, double r, Func<Enemy, bool>? filter = null)
    {
        Enemy? best = null;
        double bd = r * r;
        Spatial.Query(x, z, r, q);
        foreach (var id in q)
        {
            var e = Enemies.Items[id];
            if (!Targetable(e) || (filter != null && !filter(e))) continue;
            double d = (e.X - x) * (e.X - x) + (e.Z - z) * (e.Z - z);
            if (d < bd) { bd = d; best = e; }
        }
        return best;
    }

    public List<Enemy> HostilesInRadius(double x, double z, double r)
    {
        var output = new List<Enemy>();
        Spatial.Query(x, z, r, q);
        foreach (var id in q)
        {
            var e = Enemies.Items[id];
            if (Targetable(e) && (e.X - x) * (e.X - x) + (e.Z - z) * (e.Z - z) <= (r + e.Radius) * (r + e.Radius)) output.Add(e);
        }
        return output;
    }

    public void ForEachHostileInRadius(double x, double z, double r, Action<Enemy, double> fn)
    {
        foreach (var e in HostilesInRadius(x, z, r)) fn(e, Dist(e.X, e.Z, x, z));
    }

    public void ForEachHostileNearSegment(double x0, double z0, double x1, double z1, double w, Action<Enemy> fn)
    {
        double cx = (x0 + x1) / 2, cz = (z0 + z1) / 2;
        double half = Dist(x0, z0, x1, z1) / 2 + w + 1;
        double dx = x1 - x0, dz = z1 - z0, l2 = dx * dx + dz * dz;
        foreach (var e in HostilesInRadius(cx, cz, half))
        {
            double t = Clamp(((e.X - x0) * dx + (e.Z - z0) * dz) / l2, 0, 1);
            double d = Dist(e.X, e.Z, x0 + dx * t, z0 + dz * t);
            if (d <= w / 2 + e.Radius) fn(e);
        }
    }

    /// <summary>The hostile with the most other hostiles around it.</summary>
    public Enemy? DensestHostile(double x, double z, double r, double cluster)
    {
        var list = HostilesInRadius(x, z, r);
        Enemy? best = null;
        int bn = -1;
        int step = Math.Max(1, list.Count / 24);
        for (int i = 0; i < list.Count; i += step)
        {
            var e = list[i];
            int n = 0;
            foreach (var o in list) if ((o.X - e.X) * (o.X - e.X) + (o.Z - e.Z) * (o.Z - e.Z) < cluster * cluster) n++;
            if (n > bn) { bn = n; best = e; }
        }
        return best;
    }

    /* ========================================================= damage in == */

    /// <summary>Everything the survivor's side does to a creature passes through here.</summary>
    public double HitEnemy(Enemy e, double baseDamage, School school, Tag[] tags, HitOpts o = default)
    {
        if (!e.Alive || e.State == EnemyState.Dying) return 0;
        // The survivor's side never hurts its allies, and never hurts a
        // creature minding its own business by accident: auras, ground fires
        // and swings that happen to reach a neutral pass it by. Picking a
        // fight is a choice, not a stray spark.
        if (e.Disposition == Disposition.Ally || (e.Disposition == Disposition.Neutral && !e.Provoked && !o.Provoke)) return 0;
        var st = Stats;
        double dmg = baseDamage * st.DamageMult(school, tags, e.Def.Family);
        // Allies go for the throat: champions and worse take more from them.
        if (o.Summon) dmg *= st.Get(Stat.SummonDamage) * (e.Boss || e.Elite ? (Boons.ContainsKey("go_for_the_throat") ? 2.8 : 2.0) : 1);
        if (e.Boss || e.Elite) dmg *= o.BossDamage ?? o.Weapon?.Def.BossDamage ?? 1;
        if (e.StaggeredT > 0) dmg *= 1.25;
        // Vulnerabilities.
        var s = e.Status;
        if (s[StatusKind.Mark] is { } mark) dmg *= 1 + 0.3 * (mark.Power != 0 ? mark.Power : 1);
        if (s.Has(StatusKind.Frozen)) dmg *= Boons.ContainsKey("deep_chill") ? 1.35 : 1.15;
        if (s.Has(StatusKind.Sear) && school == School.Holy) dmg *= 1.3;
        if (s.Has(StatusKind.Shock) && !o.Dot) { dmg *= 1.35 + st.Get(Stat.ShockBonus); if (!Boons.ContainsKey("static_charge")) s.Remove(StatusKind.Shock); }
        dmg *= e.TakenMul;
        // Warded by its own kind's lamp or drum.
        if (e.WardT > 0) dmg *= 1 - e.Ward;
        // Resistances.
        dmg *= 1 - (e.Def.Resists?.Of(school) ?? 0);
        // Frontal guard: projectiles into a raised shield mostly glance off.
        bool blocked = false;
        if (o.Projectile && e.Def.Guard is { } guard && e.State != EnemyState.Stunned && !s.Has(StatusKind.Frozen) && !s.Has(StatusKind.Stun))
        {
            double fx = Math.Cos(e.Facing), fz = Math.Sin(e.Facing);
            double ix = -o.FromX, iz = -o.FromZ;
            if (fx * ix + fz * iz > Math.Cos(guard.Arc / 2)) { dmg *= 1 - (e.Elite && !e.Def.Elite ? Math.Min(guard.Reduction, 0.6) : guard.Reduction); blocked = true; }
        }
        if (e.TakenMul < 0.7) blocked = true;
        // Criticals.
        bool crit = o.Crit;
        if (!crit && !o.NoCrit && !o.Dot)
        {
            double chance = st.Get(Stat.CritChance) + (Player.SureCritT > 0 ? 1 : 0) + (o.Weapon?.CritBonus ?? 0);
            // The Hunters' Blind: the first blow on anything unhurt.
            if (e.Hp >= e.MaxHp && Boons.TryGetValue("hunters_blind", out int blind)) chance += blind >= 2 ? 1 : 0.5;
            // Night-Eyes: the far ones, in the dark, are seen best.
            if (Boons.TryGetValue("precision", out int eyes) && Dist(e.X, e.Z, Player.X, Player.Z) > 6) chance += 0.03 * eyes;
            crit = Rng.Next() < chance;
        }
        if (crit) dmg *= st.Get(Stat.CritDamage) * (e.Hp < e.MaxHp * 0.5 && Boons.TryGetValue("ferocity", out int tooth) ? 1 + 0.12 * tooth : 1);
        else if ((Rules.IronSkin > 0 || e.Def.IronSkin > 0) && e.Disposition == Disposition.Hostile) { dmg *= 1 - Math.Max(Rules.IronSkin, e.Def.IronSkin); blocked = true; }
        dmg = Math.Max(0.5, dmg);

        double before = e.Hp;
        e.Hp -= dmg;
        // A boss's gate: it stops at its phase's mark; the rest is its Break.
        if (e.HpFloor > 0 && e.Hp < e.HpFloor) { e.Overflow += e.HpFloor - e.Hp; e.Hp = e.HpFloor; }
        // A boss struck many times a second would never stop flashing white and its body
        // would be lost in it: a softer flash, so it stays itself under the build's blows.
        e.Flash = e.Boss ? Math.Max(e.Flash, 0.4) : 1;
        e.LastSchool = school;
        // Which way the blow was going: its own, or away from the survivor.
        double dx = o.DirX, dz = o.DirZ;
        if (dx == 0 && dz == 0) { dx = e.X - Player.X; dz = e.Z - Player.Z; }
        double dl = Len(dx, dz);
        if (dl == 0) dl = 1;
        e.LastBlow = before > 0 ? dmg / Math.Max(1, before) : 0;
        e.LastCrit = crit;
        e.LastDx = dx / dl; e.LastDz = dz / dl;
        e.LastWeapon = o.Weapon?.Id;
        if (e.Disposition == Disposition.Neutral) Provoke(e);
        if (e.Wake > 0 && !e.Roused) Rouse(e);
        if (o.Weapon != null) o.Weapon.DamageDealt += Math.Min(dmg, before);
        string by = o.Weapon?.Id ?? o.Credit ?? (o.Summon ? "summon" : credit ?? "other");
        DamageBy[by] = DamageBy.GetValueOrDefault(by) + Math.Min(dmg, Math.Max(0, before));
        // Where the damage is coming from, for the director.
        if (tags.Has(Tag.Summon) || o.Summon) Profile.Summon += dmg;
        else if (tags.Has(Tag.Projectile)) Profile.Projectile += dmg;
        else if (tags.Has(Tag.Melee)) Profile.Melee += dmg;
        else Profile.Area += dmg;

        Events.Emit(new Ev.Hit
        {
            X = e.X, Z = e.Z, Amount = dmg, Crit = crit, School = school, Target = e.Id, Dot = o.Dot, Blocked = blocked,
            Family = e.Def.Family, Def = e.Def.Id, MaxHp = e.MaxHp, Dx = e.LastDx, Dz = e.LastDz,
            Art = o.Weapon?.Art, Rank = o.Weapon?.Rank ?? 0,
        });

        // Lifesteal.
        double ls = st.Get(Stat.Lifesteal);
        if (ls > 0 && !o.Dot) HealPlayer(dmg * ls, "lifesteal", true);

        // Knockback: heavier things move less, bosses not at all.
        if (o.Knockback != 0 && e.Boss) AddStagger(e, 0.004 * o.Knockback * st.Get(Stat.Knockback));
        if (o.Knockback != 0 && !e.Boss && e.Def.Behavior != Behavior.Stationary)
        {
            double k = o.Knockback * st.Get(Stat.Knockback) * 7 / Math.Max(0.5, e.Mass) * (e.Elite ? 0.35 : 1);
            e.Kbx += o.DirX * k;
            e.Kbz += o.DirZ * k;
        }

        // Status payloads ride the hit.
        if (o.Status != null) ApplyStatus(e, o.Status, dmg, o.Depth, by);

        int depth = o.Depth;
        if (!o.NoProcs && depth < 3)
        {
            var ctx = new ProcCtx { Target = e, X = e.X, Z = e.Z, Damage = dmg, School = school, Tags = tags, Crit = crit, Weapon = o.Weapon, Depth = depth + 1 };
            Fire(TriggerEvent.Hit, ctx);
            if (crit) Fire(TriggerEvent.Crit, ctx);
        }

        if (e.Boss) Hooks.OnBossHit?.Invoke(e, school, dmg);
        if (e.Hp <= 0 && e.Alive && e.State != EnemyState.Dying) KillEnemy(e, true, o.Weapon, depth);
        else ArtOnHit(e);
        return dmg;
    }

    /// <summary>A resting pack wakes: this one, and its own round it.</summary>
    public void Rouse(Enemy e)
    {
        e.Roused = true;
        e.RetargetT = 0;
        ForEachEnemyNear(e.X, e.Z, 10, o =>
        {
            if (o.Roused || o.Wake <= 0 || o.Faction != e.Faction || Math.Abs(o.HomeX - e.HomeX) + Math.Abs(o.HomeZ - e.HomeZ) > 1) return;
            o.Roused = true;
            o.RetargetT = Rng.Next() * 0.4;
        });
    }

    public void Provoke(Enemy e)
    {
        if (e.Provoked) return;
        e.Provoked = true;
        // A pack answers for its own.
        ForEachEnemyNear(e.X, e.Z, 12, o => { if (o.Faction == e.Faction && o.Disposition == Disposition.Neutral) o.Provoked = true; });
    }

    public void ForEachEnemyNear(double x, double z, double r, Action<Enemy> fn)
    {
        Spatial.Query(x, z, r, q);
        foreach (var id in q.ToArray())
        {
            var e = Enemies.Items[id];
            if (e.Alive && e.State != EnemyState.Dying && (e.X - x) * (e.X - x) + (e.Z - z) * (e.Z - z) <= r * r) fn(e);
        }
    }

    public void KillEnemy(Enemy e, bool byPlayer, WeaponInst? weapon, int depth = 0)
    {
        e.Hp = 0;
        e.State = EnemyState.Dying;
        e.StateT = 0;
        e.DieT = 0;
        e.Anim = EnemyAnim.Die;
        e.AnimT = 0;
        e.Credit = byPlayer || e.Credit;
        bool credited = e.Credit;
        if (weapon != null) weapon.Kills++;
        if (credited && e.Disposition != Disposition.Ally)
        {
            KillCount++;
            KillsByFamily[e.Def.Family] = KillsByFamily.GetValueOrDefault(e.Def.Family) + 1;
            if (e.Elite && !e.Boss) ChampionsByFamily[e.Def.Family] = ChampionsByFamily.GetValueOrDefault(e.Def.Family) + 1;
        }
        // A body comes apart under a blow of three times what it had left, or
        // twice on a critical; fire does it its own way (no burst).
        bool burst = !e.Boss && e.LastSchool != School.Fire && (e.LastBlow >= 3 || (e.LastCrit && e.LastBlow >= 2));
        e.Burst = burst;
        Events.Emit(new Ev.Kill
        {
            X = e.X, Z = e.Z, Enemy = e.Id, Def = e.Def.Id, Family = e.Def.Family, School = e.LastSchool, Elite = e.Elite, Boss = e.Boss,
            ByPlayer = credited, Burst = burst, Dx = e.LastDx, Dz = e.LastDz, Scale = e.Def.Scale ?? 1,
        });
        Graves.Add((e.X, e.Z, e.Def.Id, Time));

        if (e.Disposition != Disposition.Ally)
        {
            // The dead leave a stone with light still in it.
            double xp = e.Def.Xp * Content.Enemies.ScaleFor(e.Level).Xp * Rules.EmberGain;
            if (xp > 0 && EmberOn && !e.Raised) DropEmber(e.X, e.Z, xp);
            if (credited)
            {
                double luck = Stats.Get(Stat.Luck);
                if (e.Def.Gold is { } gold && gold != 0 && Rng.Next() < (0.55 + luck * 0.1) * (e.Boss || e.Def.Miniboss ? 1 : e.Elite ? Rules.ChampionGold : Rules.FodderGold)) SpawnPickup(PickupKind.Gold, e.X, e.Z, Math.Ceiling(gold * (0.6 + Rng.Next() * 0.8)));
                if (Rng.Next() < 0.012 * luck + (e.Elite ? 0.4 : 0)) SpawnPickup(PickupKind.Heal, e.X, e.Z, e.Elite ? 40 : 25);
                if (Rng.Next() < 0.004 * luck) SpawnPickup(PickupKind.Magnet, e.X, e.Z, 1);
                if (Hooks.OnLoot != null)
                    foreach (var d in Hooks.OnLoot(e))
                    {
                        var pk = SpawnPickup(d.Kind, e.X, e.Z, d.Value, d.Ref);
                        if (pk != null && d.Persistent) pk.Persistent = true;
                        if (pk != null && d.Rarity is { } r) pk.Tier = r;
                        if (pk != null) pk.Lean = d.Lean;
                    }
            }
        }
        // Death verbs.
        if (e.Disposition == Disposition.Hostile && !e.Boss)
        {
            // The map's oath: the dead burn, or burst.
            if (Rules.DeathFire && Rng.Next() < 0.3)
            {
                var zn = SpawnZone(Side.Enemy, e.X, e.Z, 1.4, 3.5, e.Damage * 0.35, School.Fire);
                if (zn != null) { zn.Tags = [Tag.Zone]; zn.Art = "zone_fire_enemy"; }
            }
            if (Rules.DeathBurst && Rng.Next() < 0.22 && Charges.MayFuse(this, 0.7))
            {
                Events.Emit(new Ev.Telegraph { Id = e.Id, Shape = TelegraphShape.Circle, X = e.X, Z = e.Z, Radius = 1.8, Duration = 0.7, Hostile = true });
                strikes.Add(new StrikeSpec(e.X, e.Z, 1.8, e.Damage * 0.9, School.Shadow, [Tag.Explosion], 0.7, null, Side.Enemy, 0));
            }
        }
        if (e.Def.Burst is { } b && Charges.MayFuse(this, b.Fuse))
        {
            Events.Emit(new Ev.Telegraph { Id = e.Id, Shape = TelegraphShape.Circle, X = e.X, Z = e.Z, Radius = b.Radius, Duration = b.Fuse, Hostile = true });
            strikes.Add(new StrikeSpec(e.X, e.Z, b.Radius, e.Damage * b.DamagePct, b.School, [Tag.Explosion], b.Fuse, null, Side.Enemy, 0));
        }
        if (e.Def.Split is { } split)
            for (int i = 0; i < split.Count; i++)
            {
                double a = (double)i / split.Count * Tau;
                SpawnEnemy(split.Into, e.X + Math.Cos(a) * 0.8, e.Z + Math.Sin(a) * 0.8, new SpawnOpts { Level = e.Level, Style = SpawnStyle.Walk, Faction = e.Faction });
            }
        if (credited && depth < 3)
            Fire(TriggerEvent.Kill, new ProcCtx { Target = e, X = e.X, Z = e.Z, Damage = e.MaxHp, School = e.LastSchool, Tags = Array.Empty<Tag>(), Weapon = weapon, Depth = depth + 1 });
        ArtOnKill(e, credited);
        Hooks.OnKill?.Invoke(e, credited);
    }

    /* =========================================================== status == */

    /// <param name="from">What it is credited to (Battle.DamageBy), if not the rule firing now.</param>
    public void ApplyStatus(Enemy e, StatusPayload p, double hitDamage, int depth = 0, string? from = null)
    {
        if (!e.Alive || e.State == EnemyState.Dying) return;
        double chance = p.Chance * (1 + Stats.Get(Stat.StatusChance));
        if (Rng.Next() >= chance) return;
        var s = e.Status;
        double sd = Stats.Get(Stat.StatusDamage) * Stats.Get(Stat.StatusDamageOf(p.Kind));
        double dps = hitDamage * p.Power / Math.Max(0.5, p.Duration) * sd;
        // Longer burning is more burning: the rate holds, the time stretches.
        double dur = p.Duration * Stats.Get(Stat.StatusDurationOf(p.Kind));
        from ??= credit;
        switch (p.Kind)
        {
            case StatusKind.Burn:
            {
                var cur = s.Ensure(StatusKind.Burn, 0, 0, 0, 0.5);
                cur.Stacks = Math.Min(5, cur.Stacks + 1);
                if (dps >= cur.Power) cur.From = from;
                cur.Power = Math.Max(cur.Power, dps);
                cur.T = Math.Max(cur.T, dur);
                break;
            }
            case StatusKind.Bleed:
            {
                var cur = s.Ensure(StatusKind.Bleed, 0, 1, 0, 0.5);
                // A wound that deepens with each cut (A Thousand Cuts) rather than the worst kept.
                if (p.Stack) cur.Stacks = Math.Min(5, cur.Stacks + (cur.T > 0 ? 1 : 0));
                if (dps >= cur.Power) cur.From = from;
                cur.Power = Math.Max(cur.Power, dps);
                cur.T = Math.Max(cur.T, dur);
                break;
            }
            case StatusKind.Poison:
            {
                var cur = s.Ensure(StatusKind.Poison, 0, 0, 0, 0.5);
                cur.Stacks = Math.Min(10, cur.Stacks + 1);
                if (dps >= cur.Power) cur.From = from;
                cur.Power = Math.Max(cur.Power, dps);
                cur.T = Math.Max(cur.T, dur);
                break;
            }
            case StatusKind.Chill:
            {
                // The frozen stay frozen only as long as the freeze: more cold does not lock them for good.
                if (s.Has(StatusKind.Frozen)) break;
                var cur = s.Ensure(StatusKind.Chill, 0, 0, 0, 0);
                cur.Stacks += p.Power * (Boons.ContainsKey("deep_chill") ? 2 : 1) * Stats.Get(Stat.StatusPowerOf(StatusKind.Chill));
                cur.T = Math.Max(cur.T, dur);
                if (cur.Stacks >= 5 && e.Boss) { cur.Stacks = 2; AddStagger(e, 0.12); }
                if (cur.Stacks >= 5 && !e.Boss && e.ThawT <= 0)
                {
                    s.Remove(StatusKind.Chill);
                    s[StatusKind.Frozen] = new StatusSlot(e.Elite ? 0.9 : 1.7, 1, 0, 0);
                    if (e.State == EnemyState.Casting || e.State == EnemyState.Windup) Interrupt(e);
                    Events.Emit(new Ev.Status { Target = e.Id, Kind = StatusKind.Frozen, X = e.X, Z = e.Z });
                    if (depth < 3) Fire(TriggerEvent.Freeze, new ProcCtx { Target = e, X = e.X, Z = e.Z, Damage = hitDamage, School = School.Frost, Tags = Array.Empty<Tag>(), Depth = depth + 1 });
                }
                break;
            }
            case StatusKind.Stun:
            case StatusKind.Fear:
            case StatusKind.Charm:
                // A boss is not locked: what would lock it fills its stagger bar instead.
                if (e.Boss) { AddStagger(e, p.Kind == StatusKind.Stun ? 0.06 + 0.12 * dur : 0.08); return; }
                s[p.Kind] = new StatusSlot(Math.Max(s[p.Kind]?.T ?? 0, dur), 1, p.Power, 0);
                break;
            default:
            {
                var cur = s.Ensure(p.Kind, 0, 1, p.Power, 0.5);
                cur.From ??= from;
                cur.T = Math.Max(cur.T, dur);
                cur.Power = Math.Max(cur.Power, p.Power);
                if (p.Kind == StatusKind.Sear && e.Def.Family == Family.Undead) cur.Power = Math.Max(cur.Power, dps != 0 ? dps : 2);
                break;
            }
        }
        Events.Emit(new Ev.Status { Target = e.Id, Kind = p.Kind, X = e.X, Z = e.Z });
        if (depth < 3) Fire(TriggerEvent.Status, new ProcCtx { Target = e, X = e.X, Z = e.Z, Damage = hitDamage, School = School.Physical, Tags = Array.Empty<Tag>(), Applied = p.Kind, Depth = depth + 1 });
    }

    static readonly Tag[] DotBurn = [Tag.Dot, Tag.Fire], DotBleed = [Tag.Dot, Tag.Physical], DotSear = [Tag.Dot, Tag.Holy], DotPoison = [Tag.Dot, Tag.Nature];
    static readonly string[] DotCredit = EnumKey<StatusKind>.All.Select(k => EnumKey<StatusKind>.Of(k)).ToArray();

    /// <summary>Called by the AI each tick: status timers and damage over time.</summary>
    public void TickStatus(Enemy e, double dt)
    {
        var s = e.Status;
        foreach (var k in EnumKey<StatusKind>.All)
        {
            var slot = s[k];
            if (slot == null) continue;
            slot.T -= dt;
            if (k == StatusKind.Burn || k == StatusKind.Bleed || k == StatusKind.Poison || (k == StatusKind.Sear && e.Def.Family == Family.Undead))
            {
                slot.Tick -= dt;
                if (slot.Tick <= 0)
                {
                    slot.Tick += 0.5;
                    double d = slot.Power * 0.5;
                    if (k == StatusKind.Burn) d *= slot.Stacks;
                    if (k == StatusKind.Poison) d *= slot.Stacks;
                    if (k == StatusKind.Bleed) d *= Math.Max(1, slot.Stacks) * (s.Has(StatusKind.Frozen) && Boons.ContainsKey("frostbite") ? 3 : 1);
                    if (k == StatusKind.Bleed && Len(e.Vx, e.Vz) > 0.5) d *= 1.6;
                    var (school, tags) = k switch
                    {
                        StatusKind.Burn => (School.Fire, DotBurn),
                        StatusKind.Bleed => (School.Physical, DotBleed),
                        StatusKind.Sear => (School.Holy, DotSear),
                        _ => (School.Nature, DotPoison),
                    };
                    if (d > 0) HitEnemy(e, d, school, tags, new HitOpts { Dot = true, NoCrit = true, NoProcs = k != StatusKind.Burn, Depth = 2, Credit = slot.From ?? DotCredit[(int)k] });
                    if (!e.Alive || e.State == EnemyState.Dying) return;
                }
            }
            if (slot.T <= 0)
            {
                s.Remove(k);
                if (k == StatusKind.Frozen) e.ThawT = e.Elite ? 5 : 3;
            }
        }
        if (e.ThawT > 0) e.ThawT -= dt;
        if (e.StaggeredT > 0) e.StaggeredT -= dt;
        if (e.StaggerResistT > 0) e.StaggerResistT -= dt;
    }

    /// <summary>A boss's stagger bar fills (a quarter as fast while it resists);
    /// full, the boss is held for 3 s, taking a quarter more, whatever it was
    /// doing broken, and then resists for 15 s.</summary>
    public void AddStagger(Enemy e, double amount)
    {
        // Untouchable (a phase turning, laid down, going down the hole) is not staggerable:
        // a stagger spent there was a quarter more damage nobody could deal.
        if (!e.Boss || e.StaggeredT > 0 || !e.Alive || e.TakenMul <= 0) return;
        e.Stagger += amount * (e.StaggerResistT > 0 ? 0.25 : 1) * Rules.StaggerTaken;
        if (e.Stagger < 1) return;
        e.Stagger = 0;
        e.StaggeredT = 3;
        e.StaggerResistT = 18;
        e.State = EnemyState.Stunned;
        e.StateT = 3;
        e.Vx = e.Vz = 0;
        Hooks.OnBossStagger?.Invoke(e);
        Events.Emit(new Ev.Announce { Title = "Staggered", Tone = Tone.Boon });
        Events.Emit(new Ev.Shake { Amount = 0.25 });
    }

    /* ========================================================= damage out == */

    /// <summary>The label of the marked blow being dealt now, for the hit it makes (the harness reads it).</summary>
    string? blowLabel;

    /// <summary>A creature's blow on the survivor, after dodge, block and
    /// armour. A telegraphed blow (a lunge after its wind-up, a missile, a
    /// blast that marked its ground) slipped in the first moments of a dash
    /// is a perfect dodge.</summary>
    public double HurtPlayer(double amount, School school, string source, Enemy? from, bool telegraphed = false)
    {
        var p = Player;
        if (!p.Alive || !Combat) return 0;
        if (p.Iframes > 0 || p.Leap != null)
        {
            if (telegraphed && p.DodgeWindow > 0 && !p.PerfectThisDash) PerfectDodge(from);
            return 0;
        }
        var st = Stats;
        // Dodge.
        if (Rng.Next() < Math.Min(0.75, st.Get(Stat.Dodge)))
        {
            Events.Emit(new Ev.PlayerHit { X = p.X, Z = p.Z, Amount = 0, School = school, Source = source, Dodged = true });
            Fire(TriggerEvent.Dodge, new ProcCtx { X = p.X, Z = p.Z });
            return 0;
        }
        // Warding light.
        int blockRank = RoundInt(st.Get(Stat.Block));
        if (blockRank > 0 && p.BlockT <= 0)
        {
            p.BlockT = new[] { 12.0, 9, 6 }[Math.Min(3, blockRank) - 1];
            p.Iframes = 0.25;
            Events.Emit(new Ev.PlayerHit { X = p.X, Z = p.Z, Amount = 0, School = school, Source = source, Blocked = true });
            Fire(TriggerEvent.Block, new ProcCtx { X = p.X, Z = p.Z });
            return 0;
        }
        // Watch Mail counts: every tenth blow that reaches the survivor glances off.
        if (Boons.ContainsKey("ironhide") && ++p.MailCount >= 10)
        {
            p.MailCount = 0;
            p.Iframes = Math.Max(p.Iframes, 0.25);
            Events.Emit(new Ev.PlayerHit { X = p.X, Z = p.Z, Amount = 0, School = school, Source = source, Blocked = true });
            Fire(TriggerEvent.Block, new ProcCtx { X = p.X, Z = p.Z });
            return 0;
        }
        // Thorns answer before the armour question.
        double thorns = st.Get(Stat.Thorns);
        if (thorns > 0 && from != null && from.Alive)
            HitEnemy(from, (4 + amount * 0.2) * thorns, School.Nature, [Tag.Aura], new HitOpts { NoCrit = true, NoProcs = true, Credit = "thorns" });
        // And they burst from you, at most twice a second, as hard as the ember has made you.
        if (thorns > 0 && Time - thornsAt > 0.5)
        {
            thornsAt = Time;
            double burst = 12 * thorns * (1 + 0.08 * (EmberLevel - 1)), r = 2.5 * Math.Sqrt(st.Get(Stat.Area));
            Events.Emit(new Ev.Nova { X = p.X, Z = p.Z, Radius = r, School = School.Nature, Duration = 0.25, Rings = 0 });
            ForEachHostileInRadius(p.X, p.Z, r, (e, d) =>
            {
                double dd = d == 0 ? 1 : d;
                HitEnemy(e, burst, School.Nature, ThornTags, new HitOpts { NoCrit = true, Knockback = 0.6, DirX = (e.X - p.X) / dd, DirZ = (e.Z - p.Z) / dd, Credit = "thorns" });
            });
        }
        double dmg = amount;
        double armor = st.Get(Stat.Armor) * Rules.ArmourMul;
        foreach (var z in Zones.Items) if (z.Alive && z.Armor > 0 && Dist(z.X, z.Z, p.X, p.Z) < z.Radius) armor += z.Armor;
        dmg *= 1 - StatBlock.ArmorReduction(armor);
        dmg *= 1 - Clamp(st.GetRaw(Stat.ResistOf(school)), -1, 0.8);
        if (from != null) dmg *= 1 - Clamp(st.GetRaw(Stat.FromOf(from.Def.Family)), -1, 0.8);
        // Emberblood: what burns is busy burning (the Pyre's ward, as chill is the Winter's).
        if (from != null && from.Status.Has(StatusKind.Burn) && Boons.TryGetValue("emberblood", out int eb)) dmg *= 1 - 0.06 * eb;
        if (p.BulwarkT > 0) dmg *= Has("unmoving") ? 0.2 : 0.35;
        // Half a ghost: blows land at half.
        if (Art.WraithT > 0) dmg *= 0.5;
        // Grounding: part of the blow goes to earth (its lightning is the blessing's Hurt rule).
        if (Boons.TryGetValue("grounding", out int ground)) dmg *= ground >= 2 ? 0.67 : 0.8;
        return HurtPlayerRaw(dmg, school, source, from);
    }

    double thornsAt = -9;
    static readonly Tag[] ThornTags = [Tag.Aura, Tag.Area, Tag.Nature];
    double groundSum;

    /// <summary>Bad ground under the survivor: armour and resistance answer it, as they answer a
    /// blow; but it is not a blow. It is never dodged or blocked, sets off no thorns, and buys
    /// none of the moment of grace a blow buys (it did: standing in fire made the survivor
    /// untouchable by the crowd's teeth, half a second in every half second). Said once a second.</summary>
    public void HurtByGround(double amount, School school, double dt, string? named = null)
    {
        var p = Player;
        if (!p.Alive || p.Iframes > 0 || p.Leap != null) return;
        var st = Stats;
        double dmg = amount * (1 - StatBlock.ArmorReduction(st.Get(Stat.Armor) * Rules.ArmourMul)) * (1 - Clamp(st.GetRaw(Stat.ResistOf(school)), -1, 0.8));
        if (p.BulwarkT > 0) dmg *= Has("unmoving") ? 0.2 : 0.35;
        if (Art.WraithT > 0) dmg *= 0.5;
        string source = named ?? school switch { School.Fire => "burning ground", School.Frost => "frozen ground", School.Nature => "foul ground", _ => "bad ground" };
        Dot(ref groundSum, dmg, school, source, dt);
    }

    /// <summary>A blow slipped at the last moment: the dash comes back, the
    /// air round you cracks (what is close is staggered), and for a moment
    /// every strike finds its mark.</summary>
    void PerfectDodge(Enemy? from)
    {
        var p = Player;
        p.PerfectThisDash = true;
        p.DodgeWindow = 0;
        p.DashCharges = Math.Min(RoundInt(Stats.Get(Stat.DashCharges)), p.DashCharges + 1);
        p.Iframes = Math.Max(p.Iframes, 0.35);
        p.SureCritT = Math.Max(p.SureCritT, Abilities.Dash.Riposte + (Boons.ContainsKey("duelists_grace") ? 1 : 0));
        AddBuff("riposte", Stat.Damage, 0.3, ModKind.Inc, Abilities.Dash.Riposte + 0.5, 1);
        double power = Stats.Get(Stat.AbilityPower);
        ForEachHostileInRadius(p.X, p.Z, Abilities.Dash.Crack, (e, d) =>
        {
            double dd = d == 0 ? 1 : d;
            HitEnemy(e, 12 * power, School.Physical, [Tag.Physical, Tag.Area], new HitOpts { Knockback = 1.6, DirX = (e.X - p.X) / dd, DirZ = (e.Z - p.Z) / dd, NoProcs = true, Credit = "dash" });
            ApplyStatus(e, new StatusPayload(StatusKind.Stun, 1, 1, e.Boss ? 0.2 : 0.6), 0);
        });
        if (from is { Alive: true }) Interrupt(from);
        Events.Emit(new Ev.PerfectDodge { X = p.X, Z = p.Z });
        Fire(TriggerEvent.PerfectDodge, new ProcCtx { X = p.X, Z = p.Z });
    }

    /// <summary>From the Ashes: the survivor gets up burning, and so does everything near them.</summary>
    double RiseRadius(int rank) => (rank >= 2 ? 8 : 4) * Math.Sqrt(Stats.Get(Stat.Area));

    /// <summary>"You go cold. Then the ember catches." The cold's beat before the fire, and how long its
    /// front takes to run out to its edge (eased out, as a blast's air is; the look's FireRun).</summary>
    public const double RiseCold = 0.35, RiseRun = 0.3;

    /// <summary>Cold, Then Not's fire on its way out from where she got up.</summary>
    sealed class RiseFireState
    {
        public double X, Z, R, Dmg, T;
        public readonly HashSet<int> Caught = new(), Props = new();
        public bool Lit;
    }
    RiseFireState? riseFire;

    /// <summary>The fire goes out from her after the cold's beat, and each body catches as its front
    /// reaches it: the near first, the edge last, a wave and not a flash (every body in eight metres
    /// burning in one frame read as a bomb, and left the cold no beat).</summary>
    void RiseBurning(int rank)
    {
        var p = Player;
        riseFire = new RiseFireState { X = p.X, Z = p.Z, R = RiseRadius(rank), Dmg = 40 * (1 + 0.08 * (EmberLevel - 1)) };
    }

    /// <summary>Where the rise's front has run to, this long after it caught (0 to its edge).</summary>
    public static double RiseFront(double r, double t) => t <= 0 ? 0 : t >= RiseRun ? r : r * (1 - Math.Pow(1 - t / RiseRun, 3));

    void UpdateRiseFire(double dt)
    {
        if (riseFire is not { } f) return;
        f.T += dt;
        double front = RiseFront(f.R, f.T - RiseCold);
        if (front <= 0) return;
        var was = credit;
        credit = "boon:from_the_ashes";
        Tag[] tags = [Tag.Fire, Tag.Area, Tag.Explosion];
        var burn = new StatusPayload(StatusKind.Burn, 1, 1, 4);
        ForEachHostileInRadius(f.X, f.Z, front, (e, d) =>
        {
            if (!f.Caught.Add(e.Id)) return;
            double dd = d == 0 ? 1 : d;
            HitEnemy(e, f.Dmg, School.Fire, tags, new HitOpts { Knockback = 0.5, DirX = (e.X - f.X) / dd, DirZ = (e.Z - f.Z) / dd, Depth = 1 });
            if (e.Alive) ApplyStatus(e, burn, f.Dmg);
        });
        foreach (var c in Collision.Within(f.X, f.Z, front))
            if (c.Tag != null && f.Props.Add(c.Id)) Hooks.OnHitProp?.Invoke(c.Tag, c.Id, School.Fire, f.Dmg, f.X, f.Z);
        // What answers a blast answers it once, as it catches.
        if (!f.Lit) { f.Lit = true; Fire(TriggerEvent.Explode, new ProcCtx { X = f.X, Z = f.Z, Damage = f.Dmg, School = School.Fire, Tags = tags, Depth = 1 }); }
        credit = was;
        if (front >= f.R) riseFire = null;
    }

    /// <summary>Cinderwake: fire where the dash has been.</summary>
    void Wake(int rank)
    {
        var p = Player;
        var zn = SpawnZone(Side.Player, p.X, p.Z, rank >= 2 ? 1.4 : 1.0, rank >= 2 ? 3.5 : 2.2, 12 * (1 + 0.08 * (EmberLevel - 1)), School.Fire);
        p.WakeX = p.X; p.WakeZ = p.Z;
        if (zn == null) return;
        zn.Tags = [Tag.Fire, Tag.Zone, Tag.Area];
        zn.Art = "cinder";
        zn.Credit = "boon:cinderwake";
        zn.Tick = 0.4;
        if (rank >= 3) { zn.Slow = 0.3; zn.Status = new StatusPayload(StatusKind.Burn, 0.5, 0.5, 2.5); }
    }

    /// <summary>Iron Vow: a barrier that comes back while nothing reaches you.</summary>
    void Vow(int rank)
    {
        var p = Player;
        double amount = MaxHp * (rank >= 3 ? 0.24 : rank >= 2 ? 0.18 : 0.12), after = rank >= 2 ? 4 : 5;
        if (p.VowUp && p.Shield <= 0)
        {
            // Broken: at the third rank, it goes out with a shove.
            p.VowUp = false;
            if (rank >= 3)
            {
                Events.Emit(new Ev.Nova { X = p.X, Z = p.Z, Radius = 3.5, School = School.Holy });
                ForEachHostileInRadius(p.X, p.Z, 3.5, (e, d) =>
                {
                    double dd = d == 0 ? 1 : d;
                    HitEnemy(e, 10 + EmberLevel, School.Holy, [Tag.Holy, Tag.Area], new HitOpts { Knockback = 2.4, DirX = (e.X - p.X) / dd, DirZ = (e.Z - p.Z) / dd, NoProcs = true, Credit = "boon:iron_vow" });
                });
            }
        }
        if (p.UnstruckT >= after && p.Shield < amount - 0.5)
        {
            p.Shield = amount;
            p.ShieldT = 1e9;
            p.VowUp = true;
            Events.Emit(new Ev.Ability { Id = "iron_vow", X = p.X, Z = p.Z, Radius = 1.4 });
        }
    }

    /// <summary>Slowed: by `factor` of pace for a while, less for the tenacious.</summary>
    public void SlowPlayer(double factor, double seconds)
    {
        var p = Player;
        if (Art.SprintT > 0 || Art.Rush != null) return;
        double ten = Clamp(Stats.Get(Stat.Tenacity), 0, 0.8);
        p.SlowT = Math.Max(p.SlowT, seconds * (1 - ten));
        p.SlowF = Math.Min(p.SlowF, 1 - (1 - factor) * (1 - ten));
    }

    /// <summary>Damage over time on the survivor: taken each tick, said once a second
    /// (a quiet blow with its own source), and a death by it named for it.</summary>
    void Dot(ref double sum, double dmg, School school, string source, double dt)
    {
        var p = Player;
        p.DotT += dt;
        sum += HurtPlayerRaw(dmg, school, source, null, true, dot: true);
        if (p.DotT < 1 || sum <= 0) return;
        p.DotT = 0;
        if (p.Alive) Events.Emit(new Ev.PlayerHit { X = p.X, Z = p.Z, Amount = sum, School = school, Source = source, Dot = true });
        sum = 0;
    }

    public double HurtPlayerRaw(double dmg, School school, string source, Enemy? from, bool silent = false, bool dot = false)
    {
        var p = Player;
        if (!p.Alive || !Combat) return 0;
        if (p.Shield > 0)
        {
            double a = Math.Min(p.Shield, dmg);
            p.Shield -= a;
            dmg -= a;
            if (!silent && a > 0) Events.Emit(new Ev.ShieldHit { X = p.X, Z = p.Z, Absorbed = a, Broke = p.Shield <= 0 });
        }
        if (!silent) p.UnstruckT = 0;
        if (dmg <= 0) return 0;
        p.Hp -= dmg;
        DamageTaken += dmg;
        if (!silent)
        {
            // The Survivors contract: a crowd is dangerous, not instantly
            // lethal. Each blow buys a moment of invulnerability, so intake is
            // capped by rhythm rather than by how many creatures touch you.
            p.HurtT = 0.3;
            p.Iframes = Math.Max(p.Iframes, 0.45);
            Events.Emit(new Ev.PlayerHit { X = p.X, Z = p.Z, Amount = dmg, School = school, Source = source, Label = blowLabel });
            Fire(TriggerEvent.Hurt, new ProcCtx { X = p.X, Z = p.Z, Damage = dmg });
        }
        if (from != null)
        {
            p.LastKiller = from;
            // The map's oath rides their blows.
            if (!silent && (Rules.HitChill || from.Def.Bite == StatusKind.Chill)) SlowPlayer(0.65, 1.4);
            if (!silent && (Rules.HitPoison || from.Def.Bite == StatusKind.Poison)) { p.PoisonT = Math.Max(p.PoisonT, 3); p.PoisonDps = Math.Max(p.PoisonDps, from.Damage * 0.12); }
        }
        if (p.Hp <= 0)
        {
            if (p.Revives > 0 || p.Ashes > 0)
            {
                // The ember's rising first: the kit's keeps for a night without it.
                bool ashes = p.Ashes > 0;
                int ar = Boons.GetValueOrDefault("from_the_ashes");
                // One rise a fight, however many ways she carries it (the owner: getting up and
                // fighting on is rare, or it is a balancing nightmare).
                p.Ashes = 0;
                p.Revives = 0;
                p.Rose++;
                p.Hp = MaxHp * (ashes && ar >= 2 ? 1 : 0.5);
                p.Iframes = ashes && ar >= 3 ? 3.5 : 2;
                if (ashes && ar >= 3) p.DashCharges = RoundInt(Stats.Get(Stat.DashCharges));
                // Said first: the view draws the cold, then the fire going out (RiseBurning catches each body
                // as its front reaches it, after the cold's beat, Delay).
                Events.Emit(new Ev.Rise { X = p.X, Z = p.Z, Ember = ashes, Rank = ashes ? ar : 1, Grace = p.Iframes, Radius = ashes ? RiseRadius(ar) : 0, Delay = ashes ? RiseCold : 0 });
                if (ashes) RiseBurning(ar);
                Events.Emit(new Ev.Announce { Title = ashes ? "You go cold. Then the ember catches." : "Something answers for you: not yet. You get up.", Tone = Tone.Boon });
            }
            else if (Hooks.OnPlayerDeath?.Invoke(p.LastKiller) == true)
                p.Hp = Math.Max(p.Hp, 1);
            else
            {
                p.Hp = 0;
                p.Alive = false;
                Over = BattleOver.Death;
                // Felled by what was in them (poison, burning), it is named so; the creature that put it there keeps the credit.
                p.FellTo = dot ? source : null;
                Events.Emit(new Ev.PlayerDeath { X = p.X, Z = p.Z, Killer = dot ? source : p.LastKiller?.Def.Name ?? source, KillerId = p.LastKiller?.Id ?? -1 });
            }
        }
        return dmg;
    }

    public void HealPlayer(double amount, string source, bool silent = false)
    {
        var p = Player;
        if (!p.Alive) return;
        double h = amount * Stats.Get(Stat.Healing) * (1 - Rules.HealCut) * (source == "draught" ? Rules.DraughtMul : 1);
        double before = p.Hp;
        p.Hp = Math.Min(MaxHp, p.Hp + h);
        if (!silent && p.Hp - before > 0.5) Events.Emit(new Ev.PlayerHeal { Amount = p.Hp - before });
    }

    /* ========================================================== spawning == */

    public sealed class SpawnOpts
    {
        public int Level = 1;
        public SpawnStyle? Style;
        public Faction? Faction;
        public Disposition? Disposition;
        public bool Elite;
        /// <summary>A boss whatever its kind (the arena's ruler is its people's champion made boss).</summary>
        public bool Boss;
        public string? Tag;
        public (double X, double Z, double Leash)? Home;
        /// <summary>A resting pack's waking distance (0: it hunts from afar).</summary>
        public double Wake;
    }

    public Enemy? SpawnEnemy(string defId, double x, double z, SpawnOpts? o = null)
    {
        o ??= new SpawnOpts();
        var def = Content.Enemies.Get(defId);
        var e = Enemies.Spawn();
        if (e == null) return null;
        int lvl = o.Level;
        var sc = Content.Enemies.ScaleFor(lvl);
        e.Def = def;
        e.Level = lvl;
        e.X = x; e.Z = z; e.Vx = e.Vz = e.Kbx = e.Kbz = 0;
        e.Facing = Math.Atan2(Player.Z - z, Player.X - x);
        e.Radius = def.Radius;
        e.Mass = def.Mass ?? 1;
        e.MaxHp = e.Hp = def.Health * sc.Health * (o.Elite && !def.Elite ? 3 : 1);
        e.Damage = def.Damage * sc.Damage;
        e.Faction = o.Faction ?? def.Faction;
        e.Disposition = o.Disposition ?? (def.Faction == Faction.Ally ? Disposition.Ally : Disposition.Hostile);
        e.Speed = def.Speed * (0.92 + Rng.Next() * 0.16) * (e.Disposition == Disposition.Ally ? 1 : Rules.FoeSpeed * (1 + 0.05 * Boons.GetValueOrDefault("dark_bargain")));
        e.Elite = def.Elite || o.Elite;
        e.Boss = def.Boss || o.Boss;
        e.Scripted = false;
        e.State = o.Style == SpawnStyle.Rise ? EnemyState.Rising : o.Style == SpawnStyle.Burrow ? EnemyState.Burrowed : EnemyState.Active;
        e.StateT = o.Style == SpawnStyle.Rise ? 1.1 : o.Style == SpawnStyle.Burrow ? 0.3 : 0;
        e.AttackT = 0.5 + Rng.Next() * 0.5;
        e.RangedT = (def.Ranged?.Cooldown ?? 3) * (0.4 + Rng.Next() * 0.6);
        e.RaiseT = def.Raise?.Every ?? 0;
        e.Target = e.Disposition == Disposition.Ally ? -2 : -1;
        e.RetargetT = Rng.Next() * 0.5;
        e.Slot = Rng.Next() * Tau;
        e.Seed = Rng.Next();
        e.Burst = false; e.LastBlow = 0; e.LastCrit = false;
        e.Status.Clear();
        e.Flash = 0;
        e.Anim = o.Style == SpawnStyle.Rise ? EnemyAnim.Rise : EnemyAnim.Move;
        e.AnimT = 0;
        e.DieT = 0;
        e.LifeT = 0;
        e.Named = null;
        e.Tag = o.Tag;
        e.Credit = false;
        e.Provoked = false;
        e.HomeX = o.Home?.X ?? x; e.HomeZ = o.Home?.Z ?? z; e.Leash = o.Home?.Leash ?? 0;
        e.LastWeapon = null;
        e.TakenMul = 1;
        e.LungeX = e.LungeZ = 0;
        e.Decoy = e.Prey = false;
        e.ThawT = 0;
        e.Raised = false;
        e.HpFloor = e.Overflow = e.Stagger = e.StaggeredT = e.StaggerResistT = 0;
        e.HasteT = e.WardT = e.Ward = 0; e.Haste = 1;
        // (Only those with the verb draw from the stream: the rest of the fight's dice stay where they were.)
        e.AuraT = def.Aura is { } au ? au.Every * (0.3 + Rng.Next() * 0.4) : 0;
        e.SummonT = def.Summon is { } su ? su.Every * 0.5 : 0;
        e.SlamT = def.Slam is { } sl ? sl.Cooldown * (0.4 + Rng.Next() * 0.4) : 0;
        e.Cast = CastKind.None; e.ChainLeft = e.Summoned = 0;
        e.Wake = o.Wake;
        e.Roused = false;
        e.DrainedAt = -99;
        e.SummonedBy = null;
        Events.Emit(new Ev.Spawn { Enemy = e.Id, X = x, Z = z, Def = defId, Style = o.Style ?? SpawnStyle.Walk });
        return e;
    }

    /// <summary>A fresh projectile at a place; the caller sets the rest.</summary>
    public Projectile? SpawnProjectile(Side owner, double x, double z, double damage, School school)
    {
        var pr = Projectiles.Spawn();
        if (pr == null) return null;
        pr.Reset();
        pr.Owner = owner; pr.X = x; pr.Z = z; pr.Damage = damage; pr.School = school; pr.Credit = credit;
        return pr;
    }

    /// <summary>A fresh ground effect; the caller sets the rest.</summary>
    public GroundZone? SpawnZone(Side owner, double x, double z, double radius, double life, double dps, School school)
    {
        // The horde's burning ground is capped (the oldest goes out first), so it never fills
        // the field nor takes the pool from the survivor's own.
        if (owner == Side.Enemy)
        {
            int n = 0;
            GroundZone? oldest = null;
            foreach (var g in Zones.Items)
            {
                if (!g.Alive || g.Owner != Side.Enemy) continue;
                n++;
                if (oldest == null || g.Age > oldest.Age) oldest = g;
            }
            if (n >= Charges.GroundCap && oldest != null) Zones.Release(oldest);
        }
        var zn = Zones.Spawn();
        if (zn == null) return null;
        zn.Reset();
        zn.Owner = owner; zn.X = x; zn.Z = z; zn.Radius = radius; zn.Life = life; zn.Dps = dps; zn.School = school; zn.Credit = credit;
        return zn;
    }

    public Pickup? SpawnPickup(PickupKind kind, double x, double z, double value, string? reference = null)
    {
        var p = Pickups.Spawn();
        if (p == null) return null;
        double a = Rng.Next() * Tau, v = 1.5 + Rng.Next() * 2;
        p.Kind = kind; p.X = x; p.Z = z; p.Vx = Math.Cos(a) * v; p.Vz = Math.Sin(a) * v; p.Value = value; p.Ref = reference;
        p.Age = 0; p.Pulled = false; p.PullT = 0; p.Persistent = false; p.Tier = 0; p.Lean = null;
        if (kind == PickupKind.Ember) p.Tier = value >= 40 ? 3 : value >= 12 ? 2 : value >= 4 ? 1 : 0;
        return p;
    }

    /// <summary>The most stones left lying before the rest are gathered into one, the night's hoard
    /// stone (the genre's red gem): a late night left thousands carpeting the field, and once the
    /// pool was full the ember was simply lost.</summary>
    public const int EmberCap = 240;
    /// <summary>The tier the hoard stone is drawn at (the stones' own run 0 to 3).</summary>
    public const int HoardTier = 4;
    /// <summary>Stones lying on the ground (counted each tick, the hoard stone apart).</summary>
    public int EmbersLying { get; private set; }
    Pickup? hoardStone;

    /// <summary>The hoard stone lying, if there is one.</summary>
    public Pickup? HoardStone => hoardStone is { Alive: true, Kind: PickupKind.Ember, Tier: HoardTier } h ? h : null;

    void DropEmber(double x, double z, double xp)
    {
        if (EmbersLying >= EmberCap) { Hoard(x, z, xp); return; }
        // Many small stones for a big creature reads better than one.
        double left = xp;
        int guard = 0;
        while (left > 0 && guard++ < 6)
        {
            double v = left > 40 ? Math.Min(left, 40) : left;
            if (SpawnPickup(PickupKind.Ember, x + (Rng.Next() - 0.5), z + (Rng.Next() - 0.5), v) == null) Hoard(x, z, v);
            else EmbersLying++;
            left -= v;
        }
    }

    /// <summary>Ember past the cap goes into the hoard stone, which lies where the overflow began
    /// and does not cool, worth all of it: a jackpot to go and fetch.</summary>
    void Hoard(double x, double z, double xp)
    {
        if (HoardStone is not { } h)
        {
            h = SpawnPickup(PickupKind.Ember, x, z, 0)!;
            if (h == null) return;
            h.Tier = HoardTier;
            h.Persistent = true;
            h.Vx = h.Vz = 0;
            hoardStone = h;
        }
        h.Value += xp;
    }

    /// <summary>A creature's blow on the ground after `delay` (its own mark already shown):
    /// the survivor if she is still in it, and the horde round it at a little over half.</summary>
    public void EnemyStrike(double x, double z, double r, double dmg, School school, double delay) =>
        strikes.Add(new StrikeSpec(x, z, r, dmg, school, BlastTag, delay, null, Side.Enemy, 0));

    public void ScheduleStrike(double x, double z, double r, double dmg, School school, Tag[] tags, double delay, WeaponInst? weapon, Side owner = Side.Player, int depth = 0)
    {
        strikes.Add(new StrikeSpec(x, z, r, dmg, school, tags, delay, weapon, owner, depth) { Credit = credit });
        Events.Emit(new Ev.Strike { X = x, Z = z, Radius = r, School = school, Delay = delay, Art = weapon?.Art, Rank = weapon?.Rank ?? 0 });
        if (owner == Side.Enemy) Events.Emit(new Ev.Telegraph { Id = -1, Shape = TelegraphShape.Circle, X = x, Z = z, Radius = r, Duration = delay, Hostile = true });
    }

    /// <summary>A blow the enemy side has marked on the ground: where, what shape,
    /// how long until it lands, and what it does then.</summary>
    public sealed class EnemyBlow
    {
        public TelegraphShape Shape;
        public TelegraphKind Kind = TelegraphKind.Blow;
        public double X, Z, X1, Z1, Radius, Inner, Width = 1, Angle, Arc;
        public double Delay, T, Damage;
        public School School = School.Physical;
        public string Source = "";
        public Enemy? From;
        /// <summary>Slowed by it (a fraction of pace, for a time).</summary>
        public double Slow, SlowFor;
        public string? Label;
        /// <summary>What it leaves, or does besides, when it lands.</summary>
        public Action<Battle>? After;
        public bool Hit(double x, double z, double r)
        {
            double dx = x - X, dz = z - Z, d = Math.Sqrt(dx * dx + dz * dz);
            switch (Shape)
            {
                case TelegraphShape.Circle: return d <= Radius + r * 0.5;
                case TelegraphShape.Ring: return d <= Radius + r * 0.5 && d >= Inner - r * 0.5;
                case TelegraphShape.Cone:
                {
                    if (d > Radius + r * 0.5) return false;
                    if (d < 0.6) return true;
                    double a = Math.Atan2(dz, dx) - Angle;
                    while (a > Math.PI) a -= Math.PI * 2;
                    while (a < -Math.PI) a += Math.PI * 2;
                    return Math.Abs(a) <= Arc / 2;
                }
                default:
                {
                    double lx = X1 - X, lz = Z1 - Z, len2 = lx * lx + lz * lz;
                    double t = len2 > 0 ? Math.Clamp((dx * lx + dz * lz) / len2, 0, 1) : 0;
                    double px = X + lx * t - x, pz = Z + lz * t - z;
                    return Math.Sqrt(px * px + pz * pz) <= Width / 2 + r * 0.5;
                }
            }
        }
    }

    readonly List<EnemyBlow> blows = new();
    /// <summary>A boss's telegraphed blows that landed (a fight won with none is "unscathed").</summary>
    public int BossBlowsTaken;
    int blowIds = 1;

    /// <summary>A mark on the ground that stays (a pit, a cage) until it is ended.</summary>
    public int Mark(TelegraphKind kind, double x, double z, double r, double duration)
    {
        int id = 900000 + blowIds++;
        Events.Emit(new Ev.Telegraph { Id = id, Shape = TelegraphShape.Circle, Kind = kind, X = x, Z = z, Radius = r, Duration = duration, Hostile = true, Boss = true });
        return id;
    }

    public void EndMark(int id) =>
        Events.Emit(new Ev.Telegraph { Id = id, Shape = TelegraphShape.Circle, Kind = TelegraphKind.Wall, Radius = 0.01, Duration = 0.01, Hostile = true });
    public IReadOnlyList<EnemyBlow> Blows => blows;
    /// <summary>Every marked blow still to land is called off (she got up at a checkpoint).</summary>
    public void CancelBlows() => blows.Clear();

    /// <summary>Mark a blow and let it land after its delay: it hurts the survivor
    /// if they are still in its shape (a blow slipped by a dash in time is a
    /// perfect dodge), and only them.</summary>
    public EnemyBlow Blow(EnemyBlow b)
    {
        b.T = b.Delay;
        blows.Add(b);
        Events.Emit(new Ev.Telegraph
        {
            Id = 900000 + blowIds++, Shape = b.Shape, Kind = b.Kind, X = b.X, Z = b.Z, X1 = b.X1, Z1 = b.Z1, Radius = b.Radius, Inner = b.Inner,
            Width = b.Width, Angle = b.Angle, Arc = b.Arc, Duration = b.Delay, Hostile = true, Boss = b.From?.Boss == true, Label = b.Label,
            ByX = b.From?.X, ByZ = b.From?.Z,
        });
        return b;
    }

    void UpdateBlows(double dt)
    {
        for (int i = blows.Count - 1; i >= 0; i--)
        {
            var b = blows[i];
            b.T -= dt;
            if (b.T > 0) continue;
            blows.RemoveAt(i);
            var p = Player;
            if (b.Damage > 0 || b.Slow > 0)
            {
                double cx = b.Shape == TelegraphShape.Line ? (b.X + b.X1) / 2 : b.X, cz = b.Shape == TelegraphShape.Line ? (b.Z + b.Z1) / 2 : b.Z;
                if (b.Kind == TelegraphKind.Blow) Events.Emit(new Ev.Explosion { X = cx, Z = cz, Radius = Math.Max(1.2, b.Shape == TelegraphShape.Line ? b.Width : b.Radius * 0.6), School = b.School, Power = 0.8 });
                if (p.Alive && b.Hit(p.X, p.Z, p.Radius))
                {
                    blowLabel = b.Label;
                    if (b.Damage > 0 && HurtPlayer(b.Damage, b.School, b.Source, b.From, telegraphed: true) > 0 && b.From?.Boss == true) BossBlowsTaken++;
                    blowLabel = null;
                    if (b.Slow > 0 && p.Iframes <= 0.45) SlowPlayer(b.Slow, b.SlowFor);
                }
            }
            b.After?.Invoke(this);
        }
    }

    /* ======================================================= projectiles == */

    static readonly Tag[] Reflected = [Tag.Projectile, Tag.Physical];

    void UpdateProjectiles(double dt, double wdt)
    {
        var p = Player;
        foreach (var pr in Projectiles.Items)
        {
            if (!pr.Alive) continue;
            double step = pr.Owner == Side.Enemy ? wdt : dt;
            pr.Age += step;
            if (pr.Age >= pr.Life) { ExpireProjectile(pr); continue; }

            if (pr.OrbitR > 0)
            {
                pr.OrbitA += pr.OrbitW * step;
                pr.X = p.X + Math.Cos(pr.OrbitA) * pr.OrbitR;
                pr.Z = p.Z + Math.Sin(pr.OrbitA) * pr.OrbitR;
                pr.DirX = -Math.Sin(pr.OrbitA); pr.DirZ = Math.Cos(pr.OrbitA);
            }
            else if (pr.Lob)
            {
                // Lobbed: a parabola to the landing point, harmless until it lands.
                double k = pr.Age / pr.Life;
                pr.X += pr.Vx * step;
                pr.Z += pr.Vz * step;
                pr.Y = 0.6 + Math.Sin(k * Math.PI) * 3.2;
                continue;
            }
            else
            {
                // Homing: turn toward the target, or find a new one.
                if (pr.Homing > 0 && pr.Owner != Side.Enemy)
                {
                    Enemy? t = pr.Target >= 0 ? Enemies.Items[pr.Target] : null;
                    if (t == null || !Targetable(t) || pr.Hits.Contains(t.Id))
                    {
                        t = PickSeekTarget(pr);
                        pr.Target = t?.Id ?? -2;
                    }
                    if (t != null)
                    {
                        double want = Math.Atan2(t.Z - pr.Z, t.X - pr.X);
                        double cur = Math.Atan2(pr.Vz, pr.Vx);
                        double d = Wrap(want - cur);
                        double turn = Clamp(d, -pr.Homing * step, pr.Homing * step);
                        double a = cur + turn;
                        pr.Vx = Math.Cos(a) * pr.Speed;
                        pr.Vz = Math.Sin(a) * pr.Speed;
                    }
                }
                if (pr.Chakram && !pr.Returning && pr.Age > pr.Life * 0.45)
                {
                    pr.Returning = true;
                    pr.Hits.Clear(); pr.HitTimes.Clear();
                }
                if (pr.Returning)
                {
                    double a = Math.Atan2(p.Z - pr.Z, p.X - pr.X);
                    pr.Vx = Math.Cos(a) * pr.Speed * 1.15;
                    pr.Vz = Math.Sin(a) * pr.Speed * 1.15;
                    if (Dist(p.X, p.Z, pr.X, pr.Z) < 0.8) { Projectiles.Release(pr); continue; }
                }
                pr.X += pr.Vx * step;
                pr.Z += pr.Vz * step;
                pr.AimAlongVelocity();
                // Walls stop bolts; hitting a tagged prop tells the world.
                if (!pr.Chakram && Collision.Blocked(pr.X, pr.Z, 0.05, false))
                {
                    var hit = Collision.Within(pr.X, pr.Z, 0.6).FirstOrDefault(c => c.Tag != null);
                    if (hit?.Tag != null) Hooks.OnHitProp?.Invoke(hit.Tag, hit.Id, pr.School, pr.Damage, pr.X, pr.Z);
                    ExpireProjectile(pr, true);
                    continue;
                }
            }

            if (pr.Owner == Side.Enemy)
            {
                if (p.Alive && Art.WraithT <= 0 && Dist(p.X, p.Z, pr.X, pr.Z) < pr.Radius + p.Radius)
                {
                    if (p.BulwarkT > 0)
                    {
                        // Turned back on whoever loosed it.
                        pr.Owner = Side.Player; pr.Vx *= -1; pr.Vz *= -1; pr.Homing = 6; pr.Target = pr.OwnerId; pr.Age = 0;
                        pr.Tags = Reflected;
                        continue;
                    }
                    var src = pr.OwnerId >= 0 ? Enemies.Items[pr.OwnerId] : null;
                    HurtPlayer(pr.Damage, pr.School, pr.Art, src is { Alive: true } ? src : null, true);
                    if (pr.Status?.Kind == StatusKind.Chill) SlowPlayer(0.6, pr.Status.Duration);
                    Projectiles.Release(pr);
                }
                continue;
            }

            // Player and ally projectiles against the horde.
            Spatial.Query(pr.X, pr.Z, pr.Radius + 1.2, qProj);
            foreach (var id in qProj)
            {
                var e = Enemies.Items[id];
                if (!Targetable(e)) continue;
                double rr = pr.Radius + e.Radius;
                if ((e.X - pr.X) * (e.X - pr.X) + (e.Z - pr.Z) * (e.Z - pr.Z) > rr * rr) continue;
                int k = pr.Hits.IndexOf(e.Id);
                if (k >= 0)
                {
                    if (pr.Rehit == 0 || Time - pr.HitTimes[k] < pr.Rehit) continue;
                    pr.HitTimes[k] = Time;
                }
                else
                {
                    pr.Hits.Add(e.Id);
                    pr.HitTimes.Add(Time);
                }
                ProjectileHit(pr, e);
                if (!pr.Alive) break;
            }
        }
    }

    Enemy? PickSeekTarget(Projectile pr)
    {
        const double range = 14;
        if (pr.Seek is Seek.Elite or Seek.Strongest)
        {
            Enemy? best = null;
            foreach (var e in HostilesInRadius(pr.X, pr.Z, range))
            {
                if (pr.Hits.Contains(e.Id)) continue;
                if (best == null || (e.Elite || e.Boss ? 1e6 : 0) + e.MaxHp > (best.Elite || best.Boss ? 1e6 : 0) + best.MaxHp) best = e;
            }
            return best;
        }
        if (pr.Seek == Seek.Marked)
        {
            var m = HostilesInRadius(pr.X, pr.Z, range).FirstOrDefault(e => e.Status.Has(StatusKind.Mark) && !pr.Hits.Contains(e.Id));
            if (m != null) return m;
        }
        return NearestHostile(pr.X, pr.Z, range, e => !pr.Hits.Contains(e.Id));
    }

    WeaponInst? WeaponById(string? id)
    {
        if (id == null) return null;
        foreach (var w in Weapons) if (w.Id == id) return w;
        return null;
    }

    void ProjectileHit(Projectile pr, Enemy e)
    {
        var weapon = WeaponById(pr.Weapon);
        HitEnemy(e, pr.Damage, pr.School, pr.Tags, new HitOpts
        {
            Weapon = weapon, Knockback = pr.Knockback, DirX = pr.DirX, DirZ = pr.DirZ, Status = pr.Status, Depth = pr.Depth,
            BossDamage = pr.BossDamage, Projectile = pr.Tags.Has(Tag.Projectile), FromX = pr.DirX, FromZ = pr.DirZ,
            Summon = pr.Owner == Side.Ally, Credit = pr.Credit,
        });
        if (pr.Heal != 0) HealPlayer(pr.Heal, "weapon", true);
        pr.HitCount++;
        if (pr.Splash > 0) Explode(pr.X, pr.Z, pr.Splash, pr.Damage * 0.75, pr.School, pr.Tags, weapon, pr.Depth, e.Id);
        if (pr.GroundOnHit is { } g)
        {
            var zn = SpawnZone(Side.Player, pr.X, pr.Z, g.Radius * Stats.Get(Stat.Area), g.Duration, pr.Damage * g.DpsPct, pr.School);
            if (zn != null) { zn.Tags = [Tag.Zone, pr.School.AsTag()]; zn.Art = pr.Art + "_ground"; zn.Weapon = pr.Weapon; }
        }
        if (pr.SplitOnHit > 0 && pr.Depth < 1)
        {
            for (int i = 0; i < pr.SplitOnHit; i++)
            {
                double a = Math.Atan2(pr.Vz, pr.Vx) + (i - (pr.SplitOnHit - 1) / 2.0) * 0.9 + Math.PI * (pr.SplitOnHit > 3 ? (double)i / pr.SplitOnHit * 2 : 0);
                double sp = pr.Speed * 0.85;
                var c = SpawnProjectile(pr.Owner, pr.X, pr.Z, pr.Damage * 0.45, pr.School);
                if (c == null) continue;
                c.Y = pr.Y; c.Vx = Math.Cos(a) * sp; c.Vz = Math.Sin(a) * sp; c.Speed = sp; c.Tags = pr.Tags; c.Radius = pr.Radius * 0.7;
                c.Pierce = 0; c.Life = 0.9; c.Homing = Math.Max(pr.Homing, 3); c.Weapon = pr.Weapon; c.Art = pr.Art; c.Status = pr.Status;
                c.Depth = pr.Depth + 1; c.Rank = pr.Rank;
                c.AimAlongVelocity();
                c.Hits.Add(e.Id); c.HitTimes.Add(Time);
            }
        }
        if (pr.Bounces > 0)
        {
            var next = NearestHostile(pr.X, pr.Z, 8, o => !pr.Hits.Contains(o.Id));
            if (next != null)
            {
                pr.Bounces--;
                pr.Target = next.Id;
                double a = Math.Atan2(next.Z - pr.Z, next.X - pr.X);
                pr.Vx = Math.Cos(a) * pr.Speed; pr.Vz = Math.Sin(a) * pr.Speed;
                pr.Age = Math.Min(pr.Age, pr.Life * 0.5);
                pr.Damage *= 1.04;
                return;
            }
        }
        if (pr.OrbitR > 0 || pr.Rehit > 0) return;
        if (pr.Pierce > 0) { pr.Pierce--; return; }
        Projectiles.Release(pr);
    }

    void ExpireProjectile(Projectile pr, bool hitWall = false)
    {
        if (pr.Lob)
        {
            // A pot lands: a burst, and burning ground.
            if (pr.Owner == Side.Enemy)
            {
                var p = Player;
                const double r = 1.6;
                Events.Emit(new Ev.Explosion { X = pr.X, Z = pr.Z, Radius = r, School = pr.School, Power = 0.6 });
                if (Dist(p.X, p.Z, pr.X, pr.Z) < r + p.Radius)
                {
                    var src = pr.OwnerId >= 0 ? Enemies.Items[pr.OwnerId] : null;
                    HurtPlayer(pr.Damage, pr.School, pr.Art, src is { Alive: true } ? src : null, true);
                }
                if (pr.GroundOnHit is { } g)
                {
                    var zn = SpawnZone(Side.Enemy, pr.X, pr.Z, g.Radius, g.Duration, pr.Damage * g.DpsPct, pr.School);
                    if (zn != null) { zn.Tags = [Tag.Zone]; zn.Art = "zone_fire_enemy"; }
                }
                // Fire spreads to whatever burns (bramble walls, powder kegs).
                foreach (var c in Collision.Within(pr.X, pr.Z, r))
                    if (c.Tag != null) Hooks.OnHitProp?.Invoke(c.Tag, c.Id, pr.School, pr.Damage, pr.X, pr.Z);
            }
        }
        else if (pr.Splash > 0 && hitWall && pr.Owner == Side.Player)
            Explode(pr.X, pr.Z, pr.Splash, pr.Damage * 0.75, pr.School, pr.Tags, null, pr.Depth, -1);
        Projectiles.Release(pr);
    }

    /// <summary>An area blast from the survivor's side. Raises Explode for procs.</summary>
    public void Explode(double x, double z, double r, double dmg, School school, Tag[] tags, WeaponInst? weapon, int depth = 0, int skip = -1)
    {
        Events.Emit(new Ev.Explosion { X = x, Z = z, Radius = r, School = school, Power = Math.Min(2, dmg / 40), Art = weapon?.Art, Rank = weapon?.Rank ?? 0 });
        var t2 = tags.Has(Tag.Explosion) ? tags : [.. tags, Tag.Explosion];
        // A weapon's blast carries what its blows carry (a cinder's burning, a cloud's shock).
        var status = weapon?.StatusOf;
        ForEachHostileInRadius(x, z, r, (e, d) =>
        {
            if (e.Id == skip) return;
            double dd = d == 0 ? 1 : d;
            HitEnemy(e, dmg, school, t2, new HitOpts { Weapon = weapon, Knockback = 0.5, DirX = (e.X - x) / dd, DirZ = (e.Z - z) / dd, Depth = depth + 1, Status = status });
        });
        foreach (var c in Collision.Within(x, z, r)) if (c.Tag != null) Hooks.OnHitProp?.Invoke(c.Tag, c.Id, school, dmg, x, z);
        if (depth < 3) Fire(TriggerEvent.Explode, new ProcCtx { X = x, Z = z, Damage = dmg, School = school, Tags = t2, Depth = depth + 1 });
    }

    /* ============================================================= zones == */

    static readonly Tag[] ZoneTag = [Tag.Zone], BlastTag = [Tag.Explosion];

    void UpdateZones(double dt)
    {
        var p = Player;
        foreach (var z in Zones.Items)
        {
            if (!z.Alive) continue;
            z.Age += dt;
            if (z.Age >= z.Life) { Zones.Release(z); continue; }
            if (z.Follow) { z.X = p.X; z.Z = p.Z; }
            z.TickT -= dt;
            if (z.TickT > 0) continue;
            z.TickT = z.Tick;
            ZoneTick(z);
        }
    }

    /// <summary>A zone's pulse. Its own method so the lambdas below, which
    /// capture the zone, are made only when it pulses, not for every zone on
    /// every tick.</summary>
    void ZoneTick(GroundZone z)
    {
        var p = Player;
        if (z.Owner == Side.Enemy || z.Owner == Side.World)
        {
            if (Dist(p.X, p.Z, z.X, z.Z) < z.Radius + p.Radius * 0.5)
            {
                HurtByGround(z.Dps * z.Tick, z.School, z.Tick);
                if (z.School == School.Fire) { p.BurnT = 1.5; p.BurnDps = z.Dps * 0.25; }
                // The drowned's wet ground is cold underfoot.
                if (z.School == School.Frost) SlowPlayer(0.75, 0.6);
            }
            // World hazards hurt everything standing in them.
            if (z.Owner == Side.World)
                ForEachEnemyNear(z.X, z.Z, z.Radius, e => HitEnemy(e, z.Dps * z.Tick, z.School, ZoneTag, new HitOpts { NoCrit = true, NoProcs = true, Dot = true }));
            return;
        }
        var weapon = WeaponById(z.Weapon);
        ForEachHostileInRadius(z.X, z.Z, z.Radius, (e, _) =>
        {
            HitEnemy(e, z.Dps * z.Tick, z.School, z.Tags, new HitOpts { Weapon = weapon, Status = z.Status, BossDamage = z.BossDamage, Credit = z.Credit });
            if (z.Art == "cinder" && e.State == EnemyState.Dying && Has("pyre_walker")) HealPlayer(MaxHp * 0.015, "pyre-walker", true);
            if (z.Art == "snare_hold" && e.Alive && Art.Struck.Add(e.Id)) ApplyStatus(e, new StatusPayload(StatusKind.Stun, 1, 1, e.Boss ? 0.3 : 1.5), 0);
            if (z.Slow > 0)
            {
                var c = e.Status.Ensure(StatusKind.Chill, 0, 0, 0, 0);
                c.T = Math.Max(c.T, z.Tick + 0.1);
                c.Stacks = Math.Max(c.Stacks, (1 - z.Slow) * 8);
            }
        });
    }

    void UpdateStrikes(double dt)
    {
        for (int i = strikes.Count - 1; i >= 0; i--)
        {
            var s = strikes[i];
            s.T -= dt;
            if (s.T > 0) continue;
            strikes.RemoveAt(i);
            if (s.Owner == Side.Enemy)
            {
                var p = Player;
                Events.Emit(new Ev.Explosion { X = s.X, Z = s.Z, Radius = s.R, School = s.School, Power = 1 });
                if (Dist(p.X, p.Z, s.X, s.Z) < s.R + p.Radius * 0.5) HurtPlayer(s.Dmg, s.School, "blast", null, true);
                // Death bursts hurt anything standing in them, which is the
                // point of killing a sapper next to its friends.
                ForEachEnemyNear(s.X, s.Z, s.R, e =>
                {
                    if (e.Disposition != Disposition.Ally) HitEnemy(e, s.Dmg * 0.6, s.School, BlastTag, new HitOpts { NoCrit = true, NoProcs = true });
                });
                foreach (var c in Collision.Within(s.X, s.Z, s.R)) if (c.Tag != null) Hooks.OnHitProp?.Invoke(c.Tag, c.Id, s.School, s.Dmg, s.X, s.Z);
            }
            else
            {
                var was = credit;
                credit = s.Credit;
                Explode(s.X, s.Z, s.R, s.Dmg, s.School, s.Tags, s.Weapon, s.Depth);
                credit = was;
            }
        }
    }

    /* =========================================================== pickups == */

    void UpdatePickups(double dt)
    {
        var p = Player;
        double reach = Stats.Get(Stat.PickupRadius);
        int lying = 0;
        foreach (var k in Pickups.Items)
        {
            if (!k.Alive) continue;
            if (k.Kind == PickupKind.Ember && k.Tier != HoardTier) lying++;
            k.Age += dt;
            // Scatter, then settle.
            k.X += k.Vx * dt; k.Z += k.Vz * dt;
            double drag = Math.Exp(-dt * 5);
            k.Vx *= drag; k.Vz *= drag;
            if (!p.Alive) continue;
            double dx = p.X - k.X, dz = p.Z - k.Z;
            double d = Len(dx, dz);
            bool autoPull = k.Kind is PickupKind.Ember or PickupKind.Gold or PickupKind.Heal or PickupKind.Magnet;
            if (autoPull && (k.Pulled || (d < reach && k.Age > 0.25)))
            {
                double n = d == 0 ? 1 : d;
                if (!k.Pulled)
                {
                    // A little hop back as it notices you, then the rush: the
                    // eye reads it being pulled, not sliding.
                    k.Pulled = true;
                    k.Vx -= dx / n * 3.5;
                    k.Vz -= dz / n * 3.5;
                }
                k.PullT += dt;
                double sp = Math.Min(36, 1 + k.PullT * k.PullT * 80);
                k.X += dx / n * Math.Min(d, sp * dt);
                k.Z += dz / n * Math.Min(d, sp * dt);
            }
            if (d < p.Radius + 0.35 && (autoPull || k.Age > 0.4)) Collect(k);
            // Ember on the ground cools after a long while; gear does not.
            if (k.Alive && !k.Persistent && k.Kind == PickupKind.Ember && k.Age > 90) Pickups.Release(k);
        }
        EmbersLying = lying;
    }

    void Collect(Pickup k)
    {
        switch (k.Kind)
        {
            case PickupKind.Ember: GainEmber(k.Value); Fire(TriggerEvent.Ember, new ProcCtx { X = k.X, Z = k.Z }); break;
            case PickupKind.Gold: GoldGained += RoundInt(k.Value * Stats.Get(Stat.GoldGain)); break;
            case PickupKind.Heal: HealPlayer(k.Value * (MaxHp / 100), "potion"); break;
            case PickupKind.Magnet:
                foreach (var o in Pickups.Items) if (o.Alive && (o.Kind == PickupKind.Ember || o.Kind == PickupKind.Gold)) o.Pulled = true;
                break;
            default:
                if (Hooks.OnPickup != null && !Hooks.OnPickup(k)) { k.Age = -2; return; }
                break;
        }
        Events.Emit(new Ev.Pickup { Kind = k.Kind, Amount = k.Value, X = k.X, Z = k.Z });
        Pickups.Release(k);
    }

    /// <param name="raw">As it is, not multiplied by what grows ember (a skipped draft's refund).</param>
    public void GainEmber(double v, bool raw = false)
    {
        if (!EmberOn) return;
        EmberXp += v * (raw ? 1 : Stats.Get(Stat.XpGain));
        while (EmberXp >= EmberNext)
        {
            EmberXp -= EmberNext;
            EmberLevel++;
            EmberNext = EmberNeed(EmberLevel);
            RescaleAllies(EmberLevel - 1);
            PendingLevels++;
            if (Content.Boons.IsMilestone(EmberLevel))
            {
                PendingBlessings.Add(EmberLevel);
                // A milestone also hands back a reroll.
                Rerolls = Math.Min(MaxRerolls, Rerolls + 1);
            }
            Events.Emit(new Ev.LevelUp { Level = EmberLevel });
            Fire(TriggerEvent.LevelUp, new ProcCtx { X = Player.X, Z = Player.Z });
        }
    }

    /* ============================================================ arsenal == */

    public WeaponInst? AddWeapon(string id, int rank = 1)
    {
        Journal('W', id, null, rank);
        if (!Content.Weapons.All.ContainsKey(id) || Weapons.Exists(w => w.Id == id) || Weapons.Count >= Content.Weapons.MaxWeapons) return null;
        var w = new WeaponInst(id, rank, Weapons.Count);
        if (SkillMods.TryGetValue(id, out var sm)) Marks.Fold(w.Mods, sm);
        Weapons.Add(w);
        foreach (var t in w.Def.Triggers) AddTrigger(t, $"weapon:{id}", 1, id);
        CheckDiscoveries();
        return w;
    }

    public void RemoveWeapon(string id)
    {
        int i = Weapons.FindIndex(w => w.Id == id);
        if (i < 0) return;
        var w = Weapons[i];
        // Its own rules, and its evolution's, go with it.
        RemoveTriggers($"weapon:{id}");
        if (w.Evolution != null) RemoveTriggers($"evo:{w.Evolution.Id}");
        Weapons.RemoveAt(i);
        for (int k = 0; k < Weapons.Count; k++) Weapons[k].Slot = k;
    }

    /// <summary>Two evolved skills become one (Content/Unions.cs): both go, the
    /// union comes in at full rank, and a combat slot is free again.</summary>
    public WeaponInst? Unite(string union)
    {
        Journal('U', union);
        var u = Content.Unions.Find(union);
        if (u == null) return null;
        var a = Weapons.Find(w => w.Id == u.A);
        var c = Weapons.Find(w => w.Id == u.B);
        if (a?.Evolution == null || c?.Evolution == null) return null;
        RemoveWeapon(u.A);
        RemoveWeapon(u.B);
        // (Part of the union: the journal has it already.)
        building++;
        var w = AddWeapon(u.Into, Content.Weapons.MaxRank);
        building--;
        Events.Emit(new Ev.Evolve { Weapon = u.Into, Into = u.Id });
        Events.Emit(new Ev.Announce { Kicker = "Union", Title = u.Name, Subtitle = u.Description, Tone = Tone.Boon });
        return w;
    }

    public void RankWeapon(string id)
    {
        Journal('R', id);
        var w = Weapons.Find(x => x.Id == id);
        if (w == null || w.Rank >= Content.Weapons.MaxRank) return;
        w.Rank++;
    }

    /// <summary>A finished weapon honed (the endless dark's draft): a little more damage each time.</summary>
    public void Hone(string id)
    {
        Journal('H', id);
        var w = Weapons.Find(x => x.Id == id);
        if (w == null || w.Honed >= LevelUp.MaxHone) return;
        w.Honed++;
        w.Mods.Damage *= 1 + LevelUp.HoneStep;
    }

    /// <summary>A weapon becomes its evolution (out of a chest, the chest tells it: no
    /// announcement of its own).</summary>
    public void Evolve(string id, string branch, bool chest = false)
    {
        Journal('E', id, branch, chest ? 1 : 0);
        var w = Weapons.Find(x => x.Id == id);
        if (w == null) return;
        var evo = Array.Find(w.Def.Evolutions, e => e.Id == branch);
        if (evo == null) return;
        w.Evolution = evo;
        // What it does beyond numbers: its own rules, credited to it.
        foreach (var t in evo.Triggers) AddTrigger(t, $"evo:{evo.Id}", 1, w.Id);
        // It shows what it has become at once: the first volley is now.
        w.Timer = 0;
        Events.Emit(new Ev.Evolve { Weapon = w.Id, Into = evo.Id, Chest = chest });
        if (!chest) Events.Emit(new Ev.Announce { Kicker = $"{w.Def.Name} evolves", Title = evo.Name, Subtitle = evo.Description, Tone = Tone.Boon });
    }

    public void AddBoon(string id)
    {
        Journal('B', id);
        var def = Content.Boons.Find(id);
        if (def == null) return;
        int r = Boons.GetValueOrDefault(id) + 1;
        if (r > def.Max) return;
        Boons[id] = r;
        Stats.RemoveSource($"boon:{id}");
        Stats.RemoveSource($"syn:{id}");
        if (def.Mods != null) Stats.AddAll(def.Mods(r).Select(m => m.Source == "" ? m with { Source = $"boon:{id}" } : m));
        if (r == 1 && def.Triggers != null) foreach (var t in def.Triggers) AddTrigger(t, $"boon:{id}");
        // A blessing deepened: what the new rank adds.
        if (r >= 2 && def.Deeper is { } deeper && r - 2 < deeper.Length) foreach (var t in deeper[r - 2]) AddTrigger(t, $"boon:{id}", r);
        // Less to live on (a glass cannon): what is left of it, no more than all of it.
        Player.Hp = Math.Min(Player.Hp, MaxHp);
        if (id == "vitality") HealPlayer(25, "vitality");
        // Wisdom is the draft's own passive: each rank a reroll.
        if (id == "wisdom") Rerolls++;
        if (id == "spirit_companion") Summon("spirit_wolf", 0, 99);
        // Once a night at any rank: rising twice was too generous (the owner).
        if (id == "from_the_ashes" && r == 1 && Player.Rose == 0) Player.Ashes++;
        if (id == "grave_call") Summon("ghoul_ally", 0, 99);
    }

    /// <summary>The ember goes out (the dawn): everything it built goes with it,
    /// the cards, the blessings, whatever they called up; the survivor is left
    /// with what they carry (their gear's skills, at the gear's ranks).</summary>
    public void Douse(IEnumerable<(string Id, int Rank)> kit)
    {
        Built.Clear();
        foreach (var id in Boons.Keys.ToList())
        {
            Stats.RemoveSource($"boon:{id}");
            Stats.RemoveSource($"syn:{id}");
            RemoveTriggers($"boon:{id}");
        }
        Boons.Clear();
        Weapons.Clear();
        foreach (var (id, rank) in kit) AddWeapon(id, rank);
        foreach (var e in Enemies.Living().Where(e => e.Disposition == Disposition.Ally).ToList()) Enemies.Release(e);
        EmberLevel = 1;
        EmberXp = 0;
        EmberNext = EmberNeed(1);
        PendingLevels = 0;
        PendingBlessings.Clear();
        GreatOwed = 0;
        Player.Ashes = 0;
        EmberOn = false;
        Player.Hp = Math.Min(Player.Hp, MaxHp);
    }

    public void AddTrigger(TriggerDef def, string source, int rank = 1, string? credit = null) =>
        Triggers.Add(new TriggerInstance { Def = def, Source = source, Rank = rank, Credit = credit });

    public void RemoveTriggers(string source) => Triggers.RemoveAll(t => t.Source == source);

    /// <summary>Weapon pairs that quietly do more together. Recorded so the
    /// codex can remember them.</summary>
    void CheckDiscoveries()
    {
        foreach (var d in Content.Discoveries.All)
        {
            if (Discoveries.Contains(d.Id)) continue;
            var a = Weapons.Find(w => w.Id == d.Weapons.A);
            var b = Weapons.Find(w => w.Id == d.Weapons.B);
            if (a == null || b == null) continue;
            Discoveries.Add(d.Id);
            d.Apply(a, b, this);
            // Told at the side (the host's toast), not across the middle of the fight: a pair that
            // quietly does more is not one of the night's big moments.
            Events.Emit(new Ev.Discovery { Id = d.Id });
        }
    }

    /// <summary>Allies that fight for the survivor.</summary>
    public Enemy? Summon(string kind, double life, int max, double? x = null, double? z = null)
    {
        int n = 0;
        foreach (var e in Enemies.Items) if (e.Alive && e.Disposition == Disposition.Ally && e.Def.Id == kind) n++;
        if (n >= max) return null;
        var p = Player;
        double a = Rng.Next() * Tau;
        var s = SpawnEnemy(kind, x ?? p.X + Math.Cos(a) * 1.5, z ?? p.Z + Math.Sin(a) * 1.5, new SpawnOpts
        {
            Level = EmberLevel, Disposition = Disposition.Ally, Faction = Faction.Ally, Style = kind == "ghoul_ally" ? SpawnStyle.Rise : SpawnStyle.Walk,
        });
        if (s != null)
        {
            s.LifeT = life;
            s.MaxHp = s.Hp = s.Def.Health * AllyToughness(EmberLevel) * Stats.Get(Stat.SummonHealth);
            s.Damage = s.Def.Damage * AllyStrength(EmberLevel);
        }
        return s;
    }

    /// <summary>How much harder and tougher than their kind the survivor's allies
    /// are at an ember level: they grow with the ember, as the horde does.</summary>
    public static double AllyStrength(int level) => 1 + 0.12 * level;
    public static double AllyToughness(int level) => 1 + 0.1 * level;

    /// <summary>The ember rose: the allies it called up rise with it (a raising
    /// weapon's are set by the weapon each time it calls).</summary>
    void RescaleAllies(int from)
    {
        double dmg = AllyStrength(EmberLevel) / AllyStrength(from), hp = AllyToughness(EmberLevel) / AllyToughness(from);
        foreach (var e in Enemies.Items)
        {
            if (!e.Alive || e.Disposition != Disposition.Ally || e.SummonedBy != null || e.Def.Id == "mirror") continue;
            e.Damage *= dmg;
            e.MaxHp *= hp;
            e.Hp *= hp;
        }
    }

    /// <summary>A raising weapon's allies: up to max of them at once, near a fresh
    /// grave if there is one, as strong as the weapon is ranked.</summary>
    public Enemy? RaiseFor(WeaponInst w, string kind, double life, int max)
    {
        int n = 0;
        foreach (var e in Enemies.Items)
            if (e.Alive && e.Disposition == Disposition.Ally && e.SummonedBy == w.Id && e.State != EnemyState.Dying)
            {
                n++;
                e.Damage = w.Damage;
            }
        if (n >= max) return null;
        var p = Player;
        double x = p.X, z = p.Z;
        for (int i = Graves.Count - 1; i >= 0; i--)
            if (Time - Graves[i].T < 6 && Dist(Graves[i].X, Graves[i].Z, p.X, p.Z) < 10) { x = Graves[i].X; z = Graves[i].Z; break; }
        double a = Rng.Next() * Tau;
        var s = SpawnEnemy(kind, x + Math.Cos(a) * 1.2, z + Math.Sin(a) * 1.2, new SpawnOpts { Level = EmberLevel, Disposition = Disposition.Ally, Faction = Faction.Ally, Style = SpawnStyle.Rise });
        if (s == null) return null;
        s.SummonedBy = w.Id;
        s.LifeT = life;
        s.MaxHp = s.Hp = s.Def.Health * AllyToughness(EmberLevel) * (1 + 0.1 * (w.Rank - 1)) * Stats.Get(Stat.SummonHealth);
        s.Damage = w.Damage;
        return s;
    }

    /* ============================================================ auras == */

    static readonly Tag[] SearTags = [Tag.Aura, Tag.Holy, Tag.Area];

    void TickAuras(double dt)
    {
        var p = Player;
        auraT -= dt;
        Contagion(dt);
        int chill = Boons.GetValueOrDefault("chilling");
        int sear = Boons.GetValueOrDefault("searing");
        if (chill == 0 && sear == 0) return;
        double area = Stats.Get(Stat.Area);
        if (chill > 0)
        {
            double r = (2.4 + chill * 0.8) * area;
            ForEachHostileInRadius(p.X, p.Z, r, (e, d) =>
            {
                if (e.Boss) return;
                double k = 1 - d / r;
                var cur = e.Status.Ensure(StatusKind.Chill, 0, 0, 0, 0);
                cur.T = Math.Max(cur.T, 0.3);
                cur.Stacks = Math.Max(cur.Stacks, Math.Min(4.5, (1.5 + chill) * k * 2));
            });
        }
        if (sear > 0 && auraT <= 0)
        {
            double r = (2.2 + sear * 0.5) * area;
            ForEachHostileInRadius(p.X, p.Z, r, (e, _) => HitEnemy(e, 3 + sear * 3, School.Holy, SearTags, new HitOpts { NoProcs = true, Credit = "boon:searing" }));
            Events.Emit(new Ev.Nova { X = p.X, Z = p.Z, Radius = r, School = School.Holy, Duration = 0.4, Rings = 0 });
        }
        if (auraT <= 0) auraT = 0.5;
    }

    double contagionT;

    /// <summary>Contagion: each second every poisoned thing near the survivor
    /// passes a stack to the nearest of its neighbours that has fewer.</summary>
    void Contagion(double dt)
    {
        if (!Boons.ContainsKey("contagion") || (contagionT -= dt) > 0) return;
        contagionT = 1;
        var p = Player;
        var sick = HostilesInRadius(p.X, p.Z, 16).Where(e => e.Status[StatusKind.Poison] is { } ps && ps.T > 0).Take(48).ToList();
        foreach (var e in sick)
        {
            var src = e.Status[StatusKind.Poison]!;
            Enemy? to = null;
            double best = 3.2 * 3.2;
            foreach (var o in HostilesInRadius(e.X, e.Z, 3.2))
            {
                if (o == e || (o.Status[StatusKind.Poison]?.Stacks ?? 0) >= src.Stacks) continue;
                double d = (o.X - e.X) * (o.X - e.X) + (o.Z - e.Z) * (o.Z - e.Z);
                if (d < best) { best = d; to = o; }
            }
            if (to == null) continue;
            var s = to.Status.Ensure(StatusKind.Poison, 0, 0, 0, 0.5);
            s.Stacks = Math.Min(10, s.Stacks + 1);
            if (src.Power >= s.Power) { s.Power = src.Power; s.From = src.From; }
            s.T = Math.Max(s.T, 3);
            Events.Emit(new Ev.Chain { Points = [e.X, e.Z, to.X, to.Z], School = School.Nature });
        }
    }

    /* ============================================================= procs == */

    void TickTriggers(double dt)
    {
        for (int i = 0; i < Triggers.Count; i++)
        {
            var t = Triggers[i];
            if (t.Cd > 0) t.Cd -= dt;
            if (t.Def.On == TriggerEvent.Tick && t.Cd <= 0)
            {
                t.Cd = t.Def.Icd ?? 1;
                RunEffects(t, new ProcCtx { X = Player.X, Z = Player.Z, Depth = 1 });
            }
        }
    }

    public void Fire(TriggerEvent on, ProcCtx ctx)
    {
        // By index: an effect may add a trigger (a summon's boon), never remove one.
        for (int i = 0; i < Triggers.Count; i++)
        {
            var t = Triggers[i];
            if (t.Def.On != on) continue;
            if (t.Cd > 0) continue;
            if (t.Def.Chance is { } ch && Rng.Next() >= ch) continue;
            if (t.Def.When != null && !Matches(t.Def.When, ctx)) continue;
            if (t.Def.Icd is { } icd && icd != 0) t.Cd = icd;
            t.Count++;
            RunEffects(t, ctx);
        }
    }

    bool Matches(TriggerCond c, ProcCtx ctx)
    {
        var e = ctx.Target;
        if (c.TargetStatus is { } ts && (e == null || !e.Status.Has(ts))) return false;
        if (c.TargetFamily is { } tf && (e == null || e.Def.Family != tf)) return false;
        if (c.Elite is { } el && (e == null || (e.Elite || e.Boss) != el)) return false;
        if (c.School is { } sc && ctx.School != sc) return false;
        if (c.Tag is { } tg && !(ctx.Tags ?? Array.Empty<Tag>()).Has(tg)) return false;
        if (c.NotTag is { } nt && (ctx.Tags ?? Array.Empty<Tag>()).Has(nt)) return false;
        if (c.Weapon != null && ctx.Weapon?.Id != c.Weapon) return false;
        if (c.HpBelow is { } hb && (e == null || e.Hp / e.MaxHp >= hb)) return false;
        if (c.Applied is { } ap && ctx.Applied != ap) return false;
        if (c.SelfHpBelow is { } sh && Player.Hp / MaxHp >= sh) return false;
        if (c.Moving is { } mv && Player.Moving != mv) return false;
        return true;
    }

    void RunEffects(TriggerInstance t, ProcCtx ctx)
    {
        int depth = ctx.Depth ?? 1;
        var (was, wasWeapon) = (credit, ctxWeapon);
        credit = t.Credit ?? t.Source;
        ctxWeapon = t.Credit;
        foreach (var fx in t.Def.Effects) RunEffect(fx, ctx, depth);
        (credit, ctxWeapon) = (was, wasWeapon);
    }

    double BaseOf(double damage, Basis basis, ProcCtx ctx) => basis switch
    {
        Basis.Hit => damage * (ctx.Damage ?? 0),
        Basis.MaxHp => damage * (ctx.Target?.MaxHp ?? 0),
        Basis.Weapon => damage * (ctx.Weapon?.Damage ?? WeaponById(ctxWeapon)?.Damage ?? 0),
        _ => damage * (1 + 0.08 * (EmberLevel - 1)),
    };

    /// <summary>The weapon whose rule is running (an evolution's), for Basis.Weapon
    /// when the event that set it off carried none (a kill by a status).</summary>
    string? ctxWeapon;

    void RunEffect(Effect effect, ProcCtx ctx, int depth)
    {
        double x = ctx.X ?? Player.X, z = ctx.Z ?? Player.Z;
        switch (effect)
        {
            case Effect.Explode fx:
                Explode(x, z, fx.Radius * Stats.Get(Stat.Area), BaseOf(fx.Damage, fx.Basis, ctx), fx.School, [Tag.Explosion, fx.School.AsTag()], null, depth, -1);
                if (fx.Status != null) ForEachHostileInRadius(x, z, fx.Radius, (e, _) => ApplyStatus(e, fx.Status, BaseOf(fx.Damage, fx.Basis, ctx), depth));
                break;
            case Effect.Apply fx:
                if (fx.OnHit && ctx.Target != null) ApplyStatus(ctx.Target, fx.Payload, ctx.Damage ?? 10, depth);
                else if (!fx.OnHit)
                {
                    var list = HostilesInRadius(x, z, fx.Radius);
                    list.Sort((a, b) => b.MaxHp.CompareTo(a.MaxHp));
                    foreach (var e in list.Take(fx.Count)) ApplyStatus(e, fx.Payload, 20, depth);
                }
                break;
            case Effect.Spread fx:
            {
                var src = ctx.Target?.Status[fx.Kind];
                if (src == null) break;
                var near = HostilesInRadius(x, z, fx.Radius).Where(e => e != ctx.Target).Take(fx.Count).ToList();
                foreach (var e in near)
                {
                    var s = e.Status.Ensure(fx.Kind, 0, 0, 0, 0.5);
                    s.Stacks = Math.Min(fx.Kind == StatusKind.Poison ? 10 : 5, s.Stacks + fx.Stacks);
                    if (src.Power >= s.Power) s.From = src.From;
                    s.Power = Math.Max(s.Power, src.Power);
                    s.T = Math.Max(s.T, 3);
                    Events.Emit(new Ev.Chain { Points = [x, z, e.X, e.Z], School = fx.Kind switch
                    {
                        StatusKind.Burn => School.Fire, StatusKind.Mark => School.Arcane, StatusKind.Bleed => School.Physical,
                        StatusKind.Chill => School.Frost, StatusKind.Shock => School.Storm, StatusKind.Sear => School.Holy, _ => School.Nature,
                    } });
                }
                break;
            }
            case Effect.Missiles fx:
                for (int i = 0; i < fx.Count; i++)
                {
                    double a = Rng.Next() * Tau;
                    var pr = SpawnProjectile(Side.Player, x, z, BaseOf(fx.Damage, fx.Basis, ctx), fx.School);
                    if (pr == null) continue;
                    pr.Y = 1.2; pr.Vx = Math.Cos(a) * fx.Speed; pr.Vz = Math.Sin(a) * fx.Speed; pr.Speed = fx.Speed;
                    pr.Tags = [Tag.Projectile, fx.School.AsTag()]; pr.Radius = 0.2; pr.Pierce = 0; pr.Life = 2.5; pr.Homing = 6;
                    pr.Seek = fx.Seek; pr.Target = -2; pr.Art = fx.Art; pr.Status = fx.Status; pr.Depth = depth;
                    pr.AimAlongVelocity();
                }
                break;
            case Effect.Chain fx:
            {
                var first = NearestHostile(x, z, fx.Range, e => e != ctx.Target);
                if (first != null) Firing.ChainFrom(this, x, z, first, fx.Count - 1, fx.Range, BaseOf(fx.Damage, fx.Basis, ctx), fx.School, [Tag.Chain, fx.School.AsTag()], null, false, false, depth);
                break;
            }
            case Effect.Heal fx:
                HealPlayer(fx.Basis == Basis.MaxHp ? fx.Amount * MaxHp : fx.Basis == Basis.Hit ? fx.Amount * (ctx.Damage ?? 0) : fx.Amount, "proc", true);
                break;
            case Effect.Shield fx:
                Player.Shield = Math.Max(Player.Shield, fx.Amount);
                Player.ShieldT = fx.Duration;
                break;
            case Effect.Barrier fx:
            {
                double cap = MaxHp * fx.Cap;
                if (Player.Shield < cap)
                {
                    Player.Shield = Math.Min(cap, Math.Max(0, Player.Shield) + MaxHp * fx.Fraction);
                    Player.ShieldT = Math.Max(Player.ShieldT, fx.Duration);
                }
                break;
            }
            case Effect.Zone fx:
            {
                var zn = SpawnZone(Side.Player, x, z, fx.Radius * Stats.Get(Stat.Area), fx.Duration, BaseOf(fx.Dps, fx.Basis, ctx), fx.School);
                if (zn != null) { zn.Tags = [Tag.Zone, fx.School.AsTag()]; zn.Slow = fx.Slow; zn.Status = fx.Status; zn.Art = fx.Art; }
                break;
            }
            case Effect.Buff fx:
                AddBuff(fx.Id, fx.Stat, fx.Value, fx.Kind, fx.Duration, fx.MaxStacks);
                break;
            case Effect.Cooldown fx:
                if (fx.Scope == Effect.CooldownScope.All) foreach (var w in Weapons) w.Timer = Math.Max(0, w.Timer - fx.Seconds);
                else if (fx.Scope == Effect.CooldownScope.Ability) Player.AbilityCd = Math.Max(0, Player.AbilityCd - fx.Seconds);
                else Player.DashRecharge += fx.Seconds;
                break;
            case Effect.Raise fx:
                Summon(fx.Kind == Effect.RaiseKind.Ghoul ? "ghoul_ally" : "spirit_wolf", fx.Duration, fx.Max, x, z);
                break;
            case Effect.Pull fx:
                ForEachHostileInRadius(x, z, fx.Radius, (e, d) =>
                {
                    if (e.Boss) return;
                    double dd = d == 0 ? 1 : d;
                    e.Kbx += (x - e.X) / dd * fx.Strength;
                    e.Kbz += (z - e.Z) / dd * fx.Strength;
                });
                break;
            case Effect.Execute fx:
                if (ctx.Target is { Alive: true } t && t.Hp / t.MaxHp < fx.Threshold && !t.Boss)
                {
                    Events.Emit(new Ev.Bark { X = t.X, Z = t.Z, Text = "Executed" });
                    KillEnemy(t, true, ctx.Weapon, depth);
                }
                break;
            case Effect.Nova fx:
                Events.Emit(new Ev.Nova { X = x, Z = z, Radius = fx.Radius, School = fx.School, Duration = 0.3 });
                ForEachHostileInRadius(x, z, fx.Radius, (e, d) =>
                {
                    double dd = d == 0 ? 1 : d;
                    HitEnemy(e, BaseOf(fx.Damage, fx.Basis, ctx), fx.School, [Tag.Nova, Tag.Area, fx.School.AsTag()],
                        new HitOpts { Depth = depth, Knockback = fx.Knockback, DirX = (e.X - x) / dd, DirZ = (e.Z - z) / dd });
                });
                break;
            case Effect.Strike fx:
            {
                var list = HostilesInRadius(x, z, fx.Area);
                for (int i = 0; i < fx.Count && list.Count > 0; i++)
                {
                    var hit = list[Rng.Int(0, list.Count - 1)];
                    ScheduleStrike(hit.X, hit.Z, fx.Radius, BaseOf(fx.Damage, fx.Basis, ctx), fx.School, [Tag.Storm, fx.School.AsTag()], 0.3 + i * 0.08, null, Side.Player, depth);
                }
                break;
            }
            case Effect.Ember fx:
                GainEmber(fx.Amount);
                break;
        }
    }

    public void AddBuff(string id, string stat, double value, ModKind kind, double duration, int max)
    {
        if (Buffs.TryGetValue(id, out var b))
        {
            b.T = duration;
            b.Stacks = Math.Min(max, b.Stacks + 1);
        }
        else Buffs[id] = b = new Buff { T = duration, Stacks = 1, Stat = stat, Value = value, Kind = kind, Max = max };
        Stats.RemoveSource($"buff:{id}");
        Stats.Add(new StatMod(stat, kind, value * b.Stacks, $"buff:{id}"));
    }

    void UpdateBuffs(double dt)
    {
        if (Buffs.Count == 0) return;
        foreach (var (id, b) in Buffs.ToArray())
        {
            b.T -= dt;
            if (b.T <= 0)
            {
                Buffs.Remove(id);
                Stats.RemoveSource($"buff:{id}");
            }
        }
    }

    /// <summary>Stop the fight cleanly (leaving an area).</summary>
    public void End(BattleOver reason) => Over = reason;

    /// <summary>For the HUD: how ready a weapon is, 0..1.</summary>
    public double WeaponReady(WeaponInst w) => Clamp(1 - w.Timer / Math.Max(0.01, Firing.CooldownOf(this, w)), 0, 1);

    /// <summary>Ember needed for the next ember level. Quick early, steep late:
    /// in a first-tier arena about five levels in the first minute, fourteen by
    /// the fifth, thirty by the fifteenth and forty-six by the half hour, so a
    /// build is still choosing what to finish when what rules the horde comes
    /// (docs/SKILLS_DESIGN.md, "Pace").</summary>
    public static double EmberNeed(int level)
    {
        int n = level - 1;
        return Math.Round(20 + n * 28 + n * n * 3.2 + (level > 28 ? (level - 28) * (level - 28) * 8 : 0));
    }
}

public enum BattleOver { Death, Victory, Left }

public sealed class DamageProfile { public double Projectile, Area, Melee, Summon, Still, Moving; }

public sealed class Buff
{
    public double T;
    public int Stacks, Max;
    public string Stat = "";
    public double Value;
    public ModKind Kind;
}

sealed class StrikeSpec
{
    public double X, Z, R, Dmg, T;
    public School School;
    public Tag[] Tags;
    public WeaponInst? Weapon;
    public Side Owner;
    public int Depth;
    public string? Credit;

    public StrikeSpec(double x, double z, double r, double dmg, School school, Tag[] tags, double t, WeaponInst? weapon, Side owner, int depth)
    {
        X = x; Z = z; R = r; Dmg = dmg; School = school; Tags = tags; T = t; Weapon = weapon; Owner = owner; Depth = depth;
    }
}

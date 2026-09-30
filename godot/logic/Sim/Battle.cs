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
    public int Revives;
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

public enum OfferKind { Weapon, Rank, Boon, Evolve, Heal, Gold }

public sealed class Offer
{
    public OfferKind Kind;
    /// <summary>Offered as a milestone's blessing (settles the blessing, not a level).</summary>
    public bool Blessing;
    public string Id = "";
    /// <summary>For Evolve: which branch.</summary>
    public string? Branch;
    public Rarity Rarity;
    public string Title = "", Text = "", Icon = "";
    public int? From, To;
    public Tag[] Tags = Array.Empty<Tag>();
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
    public int EmberLevel = 1;
    public double EmberXp, EmberNext = 12;
    public int PendingLevels;
    /// <summary>Milestone levels whose blessing is still to be chosen (it comes
    /// on top of that level's skill, after it).</summary>
    public readonly List<int> PendingBlessings = new();
    public readonly HashSet<string> Discoveries = new();
    /// <summary>Where the fight is coming from, for the adaptive director.</summary>
    public readonly DamageProfile Profile = new();
    public int KillCount;
    public readonly Dictionary<Family, int> KillsByFamily = new();
    public double DamageTaken, GoldGained;
    /// <summary>Aim point for directional abilities (the pointer on the ground).</summary>
    public (double X, double Z)? Aim;
    /// <summary>Time-slip: everything but the survivor runs at this rate.</summary>
    public double WorldRate = 1, WorldRateT;
    public BattleOver? Over;
    /// <summary>Equipped item ids and the statuses gear applies, for evolution
    /// catalysts and the draft.</summary>
    public readonly HashSet<string> GearIds = new();
    public readonly HashSet<StatusKind> GearStatuses = new();
    public readonly HashSet<string> BannedCards = new();
    /// <summary>Skill tags the survivor's calling leans toward, for the draft.</summary>
    public readonly HashSet<Tag> Favours = new();
    public int Rerolls = 2, Banishes = 1;
    readonly List<int> q = new();
    /// <summary>The projectile loop's own query list: hits inside it run
    /// queries of their own on q.</summary>
    readonly List<int> qProj = new();
    /// <summary>The creature AI's query list.</summary>
    internal readonly List<int> AiScratch = new();
    double auraT;

    public bool DraftOwed => PendingLevels > 0 || PendingBlessings.Count > 0;

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
            p.DashRecharge += dt * DashHaste() / st.Get(Stat.DashCooldown);
            if (p.DashRecharge >= Abilities.Dash.Recharge) { p.DashRecharge = 0; p.DashCharges++; }
        }

        // Warding light recharges.
        int blockRank = RoundInt(st.Get(Stat.Block));
        if (blockRank > 0 && p.BlockT > 0) p.BlockT = Math.Max(0, p.BlockT - dt);

        // Regeneration and hazards on the survivor.
        double regen = st.Get(Stat.Regen);
        if (regen > 0 && p.Hp < MaxHp) HealPlayer(regen * dt, "regen", true);
        if (p.BurnT > 0) { p.BurnT -= dt; HurtPlayerRaw(p.BurnDps * dt, School.Fire, "burning", null, true); }
        if (p.PoisonT > 0) { p.PoisonT -= dt; HurtPlayerRaw(p.PoisonDps * dt, School.Nature, "poison", null, true); }
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
        Stats.SetActive(condScratch);
    }

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
        if (o.Summon) dmg *= st.Get(Stat.SummonDamage);
        if (e.Boss || e.Elite) dmg *= o.BossDamage ?? o.Weapon?.Def.BossDamage ?? 1;
        // Vulnerabilities.
        var s = e.Status;
        if (s[StatusKind.Mark] is { } mark) dmg *= 1 + 0.3 * (mark.Power != 0 ? mark.Power : 1);
        if (s.Has(StatusKind.Frozen)) dmg *= Boons.ContainsKey("deep_chill") ? 1.35 : 1.15;
        if (s.Has(StatusKind.Sear) && school == School.Holy) dmg *= 1.3;
        if (s.Has(StatusKind.Shock) && !o.Dot) { dmg *= 1.35; if (!Boons.ContainsKey("static_charge")) s.Remove(StatusKind.Shock); }
        dmg *= e.TakenMul;
        // Resistances.
        dmg *= 1 - (e.Def.Resists?.Of(school) ?? 0);
        // Frontal guard: projectiles into a raised shield mostly glance off.
        bool blocked = false;
        if (o.Projectile && e.Def.Guard is { } guard && e.State != EnemyState.Stunned && !s.Has(StatusKind.Frozen) && !s.Has(StatusKind.Stun))
        {
            double fx = Math.Cos(e.Facing), fz = Math.Sin(e.Facing);
            double ix = -o.FromX, iz = -o.FromZ;
            if (fx * ix + fz * iz > Math.Cos(guard.Arc / 2)) { dmg *= 1 - guard.Reduction; blocked = true; }
        }
        if (e.TakenMul < 0.7) blocked = true;
        // Criticals.
        bool crit = o.Crit;
        if (!crit && !o.NoCrit && !o.Dot)
        {
            double chance = st.Get(Stat.CritChance) + (Player.SureCritT > 0 ? 1 : 0);
            crit = Rng.Next() < chance;
        }
        if (crit) dmg *= st.Get(Stat.CritDamage);
        else if (Rules.IronSkin > 0 && e.Disposition == Disposition.Hostile) { dmg *= 1 - Rules.IronSkin; blocked = true; }
        dmg = Math.Max(0.5, dmg);

        double before = e.Hp;
        e.Hp -= dmg;
        e.Flash = 1;
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
        // Where the damage is coming from, for the director.
        if (tags.Has(Tag.Summon) || o.Summon) Profile.Summon += dmg;
        else if (tags.Has(Tag.Projectile)) Profile.Projectile += dmg;
        else if (tags.Has(Tag.Melee)) Profile.Melee += dmg;
        else Profile.Area += dmg;

        Events.Emit(new Ev.Hit
        {
            X = e.X, Z = e.Z, Amount = dmg, Crit = crit, School = school, Target = e.Id, Dot = o.Dot, Blocked = blocked,
            Family = e.Def.Family, Def = e.Def.Id, MaxHp = e.MaxHp, Dx = e.LastDx, Dz = e.LastDz,
        });

        // Lifesteal.
        double ls = st.Get(Stat.Lifesteal);
        if (ls > 0 && !o.Dot) HealPlayer(dmg * ls, "lifesteal", true);

        // Knockback: heavier things move less, bosses not at all.
        if (o.Knockback != 0 && !e.Boss && e.Def.Behavior != Behavior.Stationary)
        {
            double k = o.Knockback * st.Get(Stat.Knockback) * 7 / Math.Max(0.5, e.Mass) * (e.Elite ? 0.35 : 1);
            e.Kbx += o.DirX * k;
            e.Kbz += o.DirZ * k;
        }

        // Status payloads ride the hit.
        if (o.Status != null) ApplyStatus(e, o.Status, dmg, o.Depth);

        int depth = o.Depth;
        if (!o.NoProcs && depth < 3)
        {
            var ctx = new ProcCtx { Target = e, X = e.X, Z = e.Z, Damage = dmg, School = school, Tags = tags, Crit = crit, Weapon = o.Weapon, Depth = depth + 1 };
            Fire(TriggerEvent.Hit, ctx);
            if (crit) Fire(TriggerEvent.Crit, ctx);
        }

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
            double xp = e.Def.Xp * Content.Enemies.ScaleFor(e.Level).Xp;
            if (xp > 0) DropEmber(e.X, e.Z, xp);
            if (credited)
            {
                double luck = Stats.Get(Stat.Luck);
                if (e.Def.Gold is { } gold && gold != 0 && Rng.Next() < 0.55 + luck * 0.1) SpawnPickup(PickupKind.Gold, e.X, e.Z, Math.Ceiling(gold * (0.6 + Rng.Next() * 0.8)));
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
            if (Rules.DeathBurst && Rng.Next() < 0.22)
            {
                Events.Emit(new Ev.Telegraph { Id = e.Id, Shape = TelegraphShape.Circle, X = e.X, Z = e.Z, Radius = 1.8, Duration = 0.7, Hostile = true });
                strikes.Add(new StrikeSpec(e.X, e.Z, 1.8, e.Damage * 0.9, School.Shadow, [Tag.Explosion], 0.7, null, Side.Enemy, 0));
            }
        }
        if (e.Def.Burst is { } b)
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

    public void ApplyStatus(Enemy e, StatusPayload p, double hitDamage, int depth = 0)
    {
        if (!e.Alive || e.State == EnemyState.Dying) return;
        double chance = p.Chance * (1 + Stats.Get(Stat.StatusChance));
        if (Rng.Next() >= chance) return;
        var s = e.Status;
        double sd = Stats.Get(Stat.StatusDamage);
        double dps = hitDamage * p.Power / Math.Max(0.5, p.Duration) * sd;
        switch (p.Kind)
        {
            case StatusKind.Burn:
            {
                var cur = s.Ensure(StatusKind.Burn, 0, 0, 0, 0.5);
                cur.Stacks = Math.Min(5, cur.Stacks + 1);
                cur.Power = Math.Max(cur.Power, dps);
                cur.T = Math.Max(cur.T, p.Duration);
                break;
            }
            case StatusKind.Bleed:
            {
                var cur = s.Ensure(StatusKind.Bleed, 0, 1, 0, 0.5);
                cur.Power = Math.Max(cur.Power, dps);
                cur.T = Math.Max(cur.T, p.Duration);
                break;
            }
            case StatusKind.Poison:
            {
                var cur = s.Ensure(StatusKind.Poison, 0, 0, 0, 0.5);
                cur.Stacks = Math.Min(10, cur.Stacks + 1);
                cur.Power = Math.Max(cur.Power, dps);
                cur.T = Math.Max(cur.T, p.Duration);
                break;
            }
            case StatusKind.Chill:
            {
                if (s[StatusKind.Frozen] is { } frozen) { frozen.T = Math.Max(frozen.T, 0.4); break; }
                var cur = s.Ensure(StatusKind.Chill, 0, 0, 0, 0);
                cur.Stacks += p.Power * (Boons.ContainsKey("deep_chill") ? 2 : 1);
                cur.T = Math.Max(cur.T, p.Duration);
                if (cur.Stacks >= 5 && !e.Boss)
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
                if (e.Boss && p.Kind != StatusKind.Stun) return;
                s[p.Kind] = new StatusSlot(Math.Max(s[p.Kind]?.T ?? 0, p.Duration), 1, p.Power, 0);
                break;
            default:
            {
                var cur = s.Ensure(p.Kind, 0, 1, p.Power, 0.5);
                cur.T = Math.Max(cur.T, p.Duration);
                cur.Power = Math.Max(cur.Power, p.Power);
                if (p.Kind == StatusKind.Sear && e.Def.Family == Family.Undead) cur.Power = Math.Max(cur.Power, dps != 0 ? dps : 2);
                break;
            }
        }
        Events.Emit(new Ev.Status { Target = e.Id, Kind = p.Kind, X = e.X, Z = e.Z });
        if (depth < 3) Fire(TriggerEvent.Status, new ProcCtx { Target = e, X = e.X, Z = e.Z, Damage = hitDamage, School = School.Physical, Tags = Array.Empty<Tag>(), Applied = p.Kind, Depth = depth + 1 });
    }

    static readonly Tag[] DotBurn = [Tag.Dot, Tag.Fire], DotBleed = [Tag.Dot, Tag.Physical], DotSear = [Tag.Dot, Tag.Holy], DotPoison = [Tag.Dot, Tag.Nature];

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
                    if (k == StatusKind.Bleed && Len(e.Vx, e.Vz) > 0.5) d *= 1.6;
                    var (school, tags) = k switch
                    {
                        StatusKind.Burn => (School.Fire, DotBurn),
                        StatusKind.Bleed => (School.Physical, DotBleed),
                        StatusKind.Sear => (School.Holy, DotSear),
                        _ => (School.Nature, DotPoison),
                    };
                    if (d > 0) HitEnemy(e, d, school, tags, new HitOpts { Dot = true, NoCrit = true, NoProcs = k != StatusKind.Burn, Depth = 2 });
                    if (!e.Alive || e.State == EnemyState.Dying) return;
                }
            }
            if (slot.T <= 0) s.Remove(k);
        }
    }

    /* ========================================================= damage out == */

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
        // Thorns answer before the armour question.
        double thorns = st.Get(Stat.Thorns);
        if (thorns > 0 && from != null && from.Alive)
            HitEnemy(from, (4 + amount * 0.2) * thorns, School.Nature, [Tag.Aura], new HitOpts { NoCrit = true, NoProcs = true });
        double dmg = amount;
        double armor = st.Get(Stat.Armor);
        foreach (var z in Zones.Items) if (z.Alive && z.Armor > 0 && Dist(z.X, z.Z, p.X, p.Z) < z.Radius) armor += z.Armor;
        dmg *= 1 - StatBlock.ArmorReduction(armor);
        dmg *= 1 - Clamp(st.GetRaw(Stat.ResistOf(school)), -1, 0.8);
        if (from != null) dmg *= 1 - Clamp(st.GetRaw(Stat.FromOf(from.Def.Family)), -1, 0.8);
        if (p.BulwarkT > 0) dmg *= Has("unmoving") ? 0.2 : 0.35;
        // Half a ghost: blows land at half.
        if (Art.WraithT > 0) dmg *= 0.5;
        return HurtPlayerRaw(dmg, school, source, from);
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
            HitEnemy(e, 12 * power, School.Physical, [Tag.Physical, Tag.Area], new HitOpts { Knockback = 1.6, DirX = (e.X - p.X) / dd, DirZ = (e.Z - p.Z) / dd, NoProcs = true });
            ApplyStatus(e, new StatusPayload(StatusKind.Stun, 1, 1, e.Boss ? 0.2 : 0.6), 0);
        });
        if (from is { Alive: true }) Interrupt(from);
        Events.Emit(new Ev.PerfectDodge { X = p.X, Z = p.Z });
        Fire(TriggerEvent.PerfectDodge, new ProcCtx { X = p.X, Z = p.Z });
    }

    /// <summary>Cinderwake: fire where the dash has been.</summary>
    void Wake(int rank)
    {
        var p = Player;
        var zn = SpawnZone(Side.Player, p.X, p.Z, rank >= 2 ? 1.4 : 1.0, rank >= 2 ? 3.5 : 2.2, 8 + EmberLevel * 0.6, School.Fire);
        p.WakeX = p.X; p.WakeZ = p.Z;
        if (zn == null) return;
        zn.Tags = [Tag.Fire, Tag.Zone, Tag.Area];
        zn.Art = "cinder";
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
                    HitEnemy(e, 10 + EmberLevel, School.Holy, [Tag.Holy, Tag.Area], new HitOpts { Knockback = 2.4, DirX = (e.X - p.X) / dd, DirZ = (e.Z - p.Z) / dd, NoProcs = true });
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

    public double HurtPlayerRaw(double dmg, School school, string source, Enemy? from, bool silent = false)
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
            Events.Emit(new Ev.PlayerHit { X = p.X, Z = p.Z, Amount = dmg, School = school, Source = source });
            Fire(TriggerEvent.Hurt, new ProcCtx { X = p.X, Z = p.Z, Damage = dmg });
        }
        if (from != null)
        {
            p.LastKiller = from;
            // The map's oath rides their blows.
            if (!silent && Rules.HitChill) SlowPlayer(0.65, 1.4);
            if (!silent && Rules.HitPoison) { p.PoisonT = Math.Max(p.PoisonT, 3); p.PoisonDps = Math.Max(p.PoisonDps, from.Damage * 0.12); }
        }
        if (p.Hp <= 0)
        {
            if (p.Revives > 0)
            {
                p.Revives--;
                p.Hp = MaxHp * 0.5;
                p.Iframes = 2;
                Events.Emit(new Ev.Announce { Title = "You rise again", Tone = Tone.Boon });
            }
            else if (Hooks.OnPlayerDeath?.Invoke(p.LastKiller) == true)
                p.Hp = Math.Max(p.Hp, 1);
            else
            {
                p.Hp = 0;
                p.Alive = false;
                Over = BattleOver.Death;
                Events.Emit(new Ev.PlayerDeath { X = p.X, Z = p.Z, Killer = p.LastKiller?.Def.Name ?? source, KillerId = p.LastKiller?.Id ?? -1 });
            }
        }
        return dmg;
    }

    public void HealPlayer(double amount, string source, bool silent = false)
    {
        var p = Player;
        if (!p.Alive) return;
        double h = amount * Stats.Get(Stat.Healing) * (1 - Rules.HealCut);
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
        e.Speed = def.Speed * (0.92 + Rng.Next() * 0.16) * (e.Disposition == Disposition.Ally ? 1 : Rules.FoeSpeed);
        e.Elite = def.Elite || o.Elite;
        e.Boss = def.Boss;
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
        e.Wake = o.Wake;
        e.Roused = false;
        e.DrainedAt = -99;
        Events.Emit(new Ev.Spawn { Enemy = e.Id, X = x, Z = z, Def = defId, Style = o.Style ?? SpawnStyle.Walk });
        return e;
    }

    /// <summary>A fresh projectile at a place; the caller sets the rest.</summary>
    public Projectile? SpawnProjectile(Side owner, double x, double z, double damage, School school)
    {
        var pr = Projectiles.Spawn();
        if (pr == null) return null;
        pr.Reset();
        pr.Owner = owner; pr.X = x; pr.Z = z; pr.Damage = damage; pr.School = school;
        return pr;
    }

    /// <summary>A fresh ground effect; the caller sets the rest.</summary>
    public GroundZone? SpawnZone(Side owner, double x, double z, double radius, double life, double dps, School school)
    {
        var zn = Zones.Spawn();
        if (zn == null) return null;
        zn.Reset();
        zn.Owner = owner; zn.X = x; zn.Z = z; zn.Radius = radius; zn.Life = life; zn.Dps = dps; zn.School = school;
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

    void DropEmber(double x, double z, double xp)
    {
        // Many small stones for a big creature reads better than one.
        double left = xp;
        int guard = 0;
        while (left > 0 && guard++ < 6)
        {
            double v = left > 40 ? Math.Min(left, 40) : left;
            SpawnPickup(PickupKind.Ember, x + (Rng.Next() - 0.5), z + (Rng.Next() - 0.5), v);
            left -= v;
        }
    }

    public void ScheduleStrike(double x, double z, double r, double dmg, School school, Tag[] tags, double delay, WeaponInst? weapon, Side owner = Side.Player, int depth = 0)
    {
        strikes.Add(new StrikeSpec(x, z, r, dmg, school, tags, delay, weapon, owner, depth));
        Events.Emit(new Ev.Strike { X = x, Z = z, Radius = r, School = school, Delay = delay });
        if (owner == Side.Enemy) Events.Emit(new Ev.Telegraph { Id = -1, Shape = TelegraphShape.Circle, X = x, Z = z, Radius = r, Duration = delay, Hostile = true });
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
            Summon = pr.Owner == Side.Ally,
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
        Events.Emit(new Ev.Explosion { X = x, Z = z, Radius = r, School = school, Power = Math.Min(2, dmg / 40) });
        var t2 = tags.Has(Tag.Explosion) ? tags : [.. tags, Tag.Explosion];
        ForEachHostileInRadius(x, z, r, (e, d) =>
        {
            if (e.Id == skip) return;
            double dd = d == 0 ? 1 : d;
            HitEnemy(e, dmg, school, t2, new HitOpts { Weapon = weapon, Knockback = 0.5, DirX = (e.X - x) / dd, DirZ = (e.Z - z) / dd, Depth = depth + 1 });
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
            if (z.Owner == Side.Enemy || z.Owner == Side.World)
            {
                if (Dist(p.X, p.Z, z.X, z.Z) < z.Radius + p.Radius * 0.5)
                {
                    HurtPlayer(z.Dps * z.Tick, z.School, "burning ground", null);
                    if (z.School == School.Fire) { p.BurnT = 1.5; p.BurnDps = z.Dps * 0.25; }
                }
                // World hazards hurt everything standing in them.
                if (z.Owner == Side.World)
                    ForEachEnemyNear(z.X, z.Z, z.Radius, e => HitEnemy(e, z.Dps * z.Tick, z.School, ZoneTag, new HitOpts { NoCrit = true, NoProcs = true, Dot = true }));
                continue;
            }
            var weapon = WeaponById(z.Weapon);
            ForEachHostileInRadius(z.X, z.Z, z.Radius, (e, _) =>
            {
                HitEnemy(e, z.Dps * z.Tick, z.School, z.Tags, new HitOpts { Weapon = weapon, Status = z.Status, BossDamage = z.BossDamage });
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
            else Explode(s.X, s.Z, s.R, s.Dmg, s.School, s.Tags, s.Weapon, s.Depth);
        }
    }

    /* =========================================================== pickups == */

    void UpdatePickups(double dt)
    {
        var p = Player;
        double reach = Stats.Get(Stat.PickupRadius);
        foreach (var k in Pickups.Items)
        {
            if (!k.Alive) continue;
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

    public void GainEmber(double v)
    {
        EmberXp += v * Stats.Get(Stat.XpGain);
        while (EmberXp >= EmberNext)
        {
            EmberXp -= EmberNext;
            EmberLevel++;
            EmberNext = EmberNeed(EmberLevel);
            PendingLevels++;
            if (Content.Boons.IsMilestone(EmberLevel)) PendingBlessings.Add(EmberLevel);
            Events.Emit(new Ev.LevelUp { Level = EmberLevel });
            Fire(TriggerEvent.LevelUp, new ProcCtx { X = Player.X, Z = Player.Z });
        }
    }

    /* ============================================================ arsenal == */

    public WeaponInst? AddWeapon(string id, int rank = 1)
    {
        if (!Content.Weapons.All.ContainsKey(id) || Weapons.Exists(w => w.Id == id) || Weapons.Count >= Content.Weapons.MaxWeapons) return null;
        var w = new WeaponInst(id, rank, Weapons.Count);
        Weapons.Add(w);
        CheckDiscoveries();
        return w;
    }

    public void RemoveWeapon(string id)
    {
        int i = Weapons.FindIndex(w => w.Id == id);
        if (i < 0) return;
        Weapons.RemoveAt(i);
        for (int k = 0; k < Weapons.Count; k++) Weapons[k].Slot = k;
    }

    public void RankWeapon(string id)
    {
        var w = Weapons.Find(x => x.Id == id);
        if (w == null || w.Rank >= Content.Weapons.MaxRank) return;
        w.Rank++;
    }

    public void Evolve(string id, string branch)
    {
        var w = Weapons.Find(x => x.Id == id);
        if (w == null) return;
        var evo = Array.Find(w.Def.Evolutions, e => e.Id == branch);
        if (evo == null) return;
        w.Evolution = evo;
        Events.Emit(new Ev.Evolve { Weapon = w.Id, Into = evo.Id });
        Events.Emit(new Ev.Announce { Kicker = $"{w.Def.Name} evolves", Title = evo.Name, Subtitle = evo.Description, Tone = Tone.Boon });
    }

    public void AddBoon(string id)
    {
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
        if (id == "vitality") HealPlayer(25, "vitality");
        if (id == "spirit_companion") Summon("spirit_wolf", 0, 99);
        if (id == "grave_call") Summon("ghoul_ally", 0, 99);
    }

    public void AddTrigger(TriggerDef def, string source, int rank = 1) =>
        Triggers.Add(new TriggerInstance { Def = def, Source = source, Rank = rank });

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
            Events.Emit(new Ev.Discovery { Id = d.Id });
            Events.Emit(new Ev.Announce { Kicker = "Discovery", Title = d.Name, Subtitle = d.Description, Tone = Tone.Boon });
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
            s.MaxHp = s.Hp = s.Def.Health * (1 + 0.1 * EmberLevel);
            s.Damage = s.Def.Damage * (1 + 0.08 * EmberLevel);
        }
        return s;
    }

    /* ============================================================ auras == */

    static readonly Tag[] SearTags = [Tag.Aura, Tag.Holy, Tag.Area];

    void TickAuras(double dt)
    {
        var p = Player;
        auraT -= dt;
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
            ForEachHostileInRadius(p.X, p.Z, r, (e, _) => HitEnemy(e, 3 + sear * 3, School.Holy, SearTags, new HitOpts { NoProcs = true }));
            Events.Emit(new Ev.Nova { X = p.X, Z = p.Z, Radius = r, School = School.Holy, Duration = 0.4, Rings = 0 });
        }
        if (auraT <= 0) auraT = 0.5;
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
        foreach (var fx in t.Def.Effects) RunEffect(fx, ctx, depth);
    }

    double BaseOf(double damage, Basis basis, ProcCtx ctx) => basis switch
    {
        Basis.Hit => damage * (ctx.Damage ?? 0),
        Basis.MaxHp => damage * (ctx.Target?.MaxHp ?? 0),
        _ => damage * (1 + 0.08 * (EmberLevel - 1)),
    };

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
                    s.Power = Math.Max(s.Power, src.Power);
                    s.T = Math.Max(s.T, 3);
                    Events.Emit(new Ev.Chain { Points = [x, z, e.X, e.Z], School = fx.Kind == StatusKind.Burn ? School.Fire : School.Nature });
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

    /// <summary>Ember needed for the next ember level. Quick early, steep late.</summary>
    public static double EmberNeed(int level)
    {
        int n = level - 1;
        return Math.Floor(12 + n * 9 + n * n * 1.6 + (level > 20 ? (level - 20) * (level - 20) * 6 : 0));
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

    public StrikeSpec(double x, double z, double r, double dmg, School school, Tag[] tags, double t, WeaponInst? weapon, Side owner, int depth)
    {
        X = x; Z = z; R = r; Dmg = dmg; School = school; Tags = tags; T = t; Weapon = weapon; Owner = owner; Depth = depth;
    }
}

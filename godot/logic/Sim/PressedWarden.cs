using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Sim;

/* The Warden's pressed skills (P7, the ARPG turn): Heroic Leap (behavior leap, cast press), Shield Charge (charge,
 * press; the old Bull Rush's run, one path with the art: Battle.ChargeStep) and Bladestorm (spin, channel: the Warden's
 * own skill since 13 Nov 2026: its key held spins, a fresh press of Sunder's key breaks the storm; a spin union's code stays generic, none in data). Their numbers are skills.json's; the
 * view draws them from Ev.Leap, Ev.Charge, Ev.Spin and Ev.SpinLine. */
public sealed partial class Battle
{
    /// <summary>The ids the last skill leap's ring struck (tests: what the ring marked is what it hit).</summary>
    public readonly List<int> LeapStruck = new();
    internal int SpinLineIds;

    /// <summary>Where a press aims her (Battle.SkillAim, else her facing): a unit direction and the distance to it
    /// (fallback when there is no aim, or it is under her feet).</summary>
    (double DX, double DZ, double D) SkillDir(double fallback)
    {
        var p = Player;
        if (SkillAim is { } a)
        {
            double dx = a.X - p.X, dz = a.Z - p.Z, d = Len(dx, dz);
            if (d > 0.1) return (dx / d, dz / d, d);
        }
        return (Math.Sin(p.Facing), Math.Cos(p.Facing), fallback);
    }

    /// <summary>No skill that carries her while something else carries her (a leap, a charge, a haul, a dash), nor from
    /// a corpse or a refire (an On-kill echo, a Pulse).</summary>
    bool FreeToMove => FireFrom == null && !Refiring && Player.Leap == null && Art.Rush == null && Player.DashT <= 0;

    /* ------------------------------------------------------- heroic leap -- */

    /// <summary>Heroic Leap: up and over to the aim (clamped to [MinRange, Range]; short of a wall, the last open ground
    /// along the line), untouchable in the air; the ring is told at takeoff (Ev.Leap Takeoff) and strikes on landing.</summary>
    internal bool SkillLeap(WeaponInst w)
    {
        if (!FreeToMove) return false;
        var p = Player;
        double range = LeapRangeOf(w), min = LeapMinOf(w);
        var (dx, dz, d) = SkillDir(range);
        (dx, dz, d) = RuleLeapAim(w, dx, dz, d);
        d = Math.Clamp(d, min, range);
        var (x1, z1) = LeapTo(dx, dz, d);
        double r = LeapRadiusOf(w), air = Math.Max(0.1, w.Num(s => s.Air) ?? 0.62);
        RuleLeapTakeoff(w);
        p.Leap = new Leap { T = 0, Dur = air, X0 = p.X, Z0 = p.Z, X1 = x1, Z1 = z1, Weapon = w, Radius = r, Heavy = HeavyBy == w };
        p.Iframes = Math.Max(p.Iframes, air);
        p.Facing = Math.Atan2(dx, dz);
        p.Vx = p.Vz = 0;
        Events.Emit(new Ev.Leap { Phase = LeapPhase.Takeoff, X0 = p.X, Z0 = p.Z, X1 = x1, Z1 = z1, Dur = air, Radius = r });
        return true;
    }

    /// <summary>Along the line, the last open ground before a wall or the fight's edge (a log or a gap is leapt).</summary>
    (double X, double Z) LeapTo(double dx, double dz, double dist)
    {
        var p = Player;
        double bx = p.X, bz = p.Z;
        int n = Math.Max(1, (int)Math.Ceiling(dist / 0.25));
        for (int k = 1; k <= n; k++)
        {
            double x = p.X + dx * dist * k / n, z = p.Z + dz * dist * k / n;
            if (InBounds != null && !InBounds(x, z)) break;
            if (Collision.Blocked(x, z, p.Radius, includeSoft: false)) break;
            bx = x; bz = z;
        }
        return (bx, bz);
    }

    /// <summary>The leap lands (Battle.LandLeap): everything in the ring told at takeoff is struck by the skill (its
    /// tags, its credit, the Hand's heavy if the cast was), thrown outward, a lesser foe knocked down (stunned), a
    /// champion staggered (a shorter stun; a boss's fills its stagger bar).</summary>
    void LandSkillLeap(Leap leap)
    {
        var w = leap.Weapon!;
        var (hb, was) = (HeavyBy, credit);
        HeavyBy = leap.Heavy ? w : null;
        credit = w.Id;
        double kb = w.Num(s => s.Knockback) ?? 2.5, stun = LeapStunOf(w), stagger = w.Num(s => s.Stagger) ?? 0.3;
        double dmg = w.Damage * RuleDamageMul(w);
        var ring = HostilesInRadius(leap.X1, leap.Z1, leap.Radius);
        LeapStruck.Clear();
        foreach (var e in ring)
        {
            double d = Dist(e.X, e.Z, leap.X1, leap.Z1), dd = d < 0.01 ? 1 : d;
            double ox = d < 0.01 ? Math.Sin(Player.Facing) : (e.X - leap.X1) / dd, oz = d < 0.01 ? Math.Cos(Player.Facing) : (e.Z - leap.Z1) / dd;
            LeapStruck.Add(e.Id);
            HitEnemy(e, dmg, w.School, w.Tags, new HitOpts { Weapon = w, Knockback = kb, DirX = ox, DirZ = oz });
            if (!e.Alive || e.State == EnemyState.Dying) continue;
            ApplyStatus(e, new StatusPayload(StatusKind.Stun, 1, 1, e.Elite || e.Boss ? stagger : stun), 0);
            Interrupt(e);
        }
        RuleLeapLanded(leap, ring, dmg);
        (HeavyBy, credit) = (hb, was);
        Events.Emit(new Ev.Explosion { X = leap.X1, Z = leap.Z1, Radius = leap.Radius, School = w.School, Power = 1.2, Art = w.Art + "_heave", Rank = w.Rank });
        Events.Emit(new Ev.Leap { Phase = LeapPhase.Land, X0 = leap.X0, Z0 = leap.Z0, X1 = leap.X1, Z1 = leap.Z1, Dur = leap.Dur, Radius = leap.Radius, Hit = ring.Count });
        Events.Emit(new Ev.Shake { Amount = 0.55 });
    }

    /* ------------------------------------------------------ shield charge -- */

    /// <summary>Shield Charge: a barrier, then a run along the aim (Range metres in RushTime seconds) that strikes what
    /// stands in the way and throws it aside; a champion or boss stops her, stunned. Its rules (skill_lamps.json):
    /// iron_hide (a bigger barrier), unbroken (barrier for each thing struck), gore (bleeds; champions harder); its Turn,
    /// the evolution pile_driver, ends it in a slam. The run is the art's (TickRush, ChargeStep).</summary>
    internal bool SkillCharge(WeaponInst w)
    {
        if (!FreeToMove) return false;
        var p = Player;
        double dist = ChargeRangeOf(w), time = Math.Max(0.05, w.Num(s => s.RushTime) ?? 0.3);
        double strength = RuleChargeBegin(w);
        var (dx, dz, _) = SkillDir(dist);
        double share = ChargeBarrierOf(w);
        Art.Barrier = MaxHp * share;
        Barrier(Art.Barrier, w.Num(s => s.Duration) ?? 4);
        Art.Struck.Clear();
        double x0 = p.X, z0 = p.Z;
        StartRush(AbilityKind.BullRush, dx, dz, dist, time);
        bool gore = SkillRule(w, "gore");
        double stun = w.Num(s => s.Stun) ?? 1;
        Art.Charge = new ChargeRun
        {
            Weapon = w, Heavy = HeavyBy == w, Tags = w.Tags, SlamTags = w.Tags, Damage = w.Damage * strength, Knockback = w.Num(s => s.Knockback) ?? 2.2,
            ChampionMul = gore ? SkillFull(w, "gore", "champions", 1.5) : 1, ChampionStun = RuleChargeStun(w, stun), BossStun = stun,
            Bleed = gore ? new StatusPayload(StatusKind.Bleed, 1, SkillFull(w, "gore", "power", 0.8), SkillFull(w, "gore", "seconds", 4)) : null,
            PerStruck = SkillRule(w, "unbroken") ? SkillFull(w, "unbroken", "health", 0.02) : 0, StruckCap = SkillFull(w, "unbroken", "cap", 0.2),
            Slam = w.Evolution?.Id == "pile_driver", SlamRadius = Firing.AreaOf(this, w, w.Num(s => s.Radius) ?? 3),
            SlamDamage = w.Damage * strength * (w.Num(s => s.Slam) ?? 1.4), SlamKnockback = 1.4, SlamStun = stun, SlamBossStun = stun,
        };
        p.SlowT = 0; p.SlowF = 1;
        Events.Emit(new Ev.Charge { Phase = ChargePhase.Start, X = x0, Z = z0, DX = dx, DZ = dz, X1 = x0 + dx * dist, Z1 = z0 + dz * dist, Dur = time });
        return true;
    }

    /// <summary>A charge's step (TickRush, while Art.Rush is a Bull Rush): what it reaches is struck once, a champion or
    /// boss stops it (stunned), the rest thrown aside; done (its time up, a wall, a stopper), it may slam.</summary>
    void ChargeStep(ChargeRun run, bool done)
    {
        var p = Player;
        var a = Art;
        var w = run.Weapon;
        p.SlowF = 1;
        var (hb, was) = (HeavyBy, credit);
        if (w != null) { HeavyBy = run.Heavy ? w : null; credit = w.Id; }
        Enemy? stopper = null;
        RuleCarryRiders();
        ForEachHostileInRadius(p.X, p.Z, p.Radius + 0.6, (e, _) =>
        {
            if (stopper != null || !a.Struck.Add(e.Id)) return;
            if (e.Elite || e.Boss)
            {
                if (!RuleChargeRunsOn(w, e)) stopper = e;
                HitEnemy(e, run.Damage * run.ChampionMul, School.Physical, run.Tags, new HitOpts { Weapon = w, Status = run.Bleed });
                ApplyStatus(e, new StatusPayload(StatusKind.Stun, 1, 1, e.Boss ? run.BossStun : run.ChampionStun), 0);
                Interrupt(e);
                if (w != null) Events.Emit(new Ev.Charge { Phase = ChargePhase.Stop, X = e.X, Z = e.Z, DX = a.RushDX, DZ = a.RushDZ, Target = e.Id });
                return;
            }
            double side = (e.X - p.X) * a.RushDZ - (e.Z - p.Z) * a.RushDX;
            double sx = side >= 0 ? a.RushDZ : -a.RushDZ, sz = side >= 0 ? -a.RushDX : a.RushDX;
            HitEnemy(e, run.Damage, School.Physical, run.Tags, new HitOpts { Weapon = w, Knockback = run.Knockback, DirX = sx * 0.85 + a.RushDX * 0.5, DirZ = sz * 0.85 + a.RushDZ * 0.5, Status = run.Bleed });
            run.Struck++;
            RuleRide(w, e);
            if (w != null) Events.Emit(new Ev.Charge { Phase = ChargePhase.Impact, X = e.X, Z = e.Z, DX = a.RushDX, DZ = a.RushDZ, Target = e.Id });
            if (run.PerStruck > 0 && p.Shield < a.Barrier + MaxHp * run.StruckCap) { p.Shield += MaxHp * run.PerStruck; p.ShieldT = Math.Max(p.ShieldT, run.StruckHold); }
        });
        if (stopper != null) { done = true; Events.Emit(new Ev.Shake { Amount = 0.4 }); }
        if (done)
        {
            a.Rush = null;
            a.Charge = null;
            // (The charge rode the dash: it lands as one, Hard Landing's shove first.)
            if (asFormRush) { asFormRush = false; DashLanded(); }
            if (run.Slam)
            {
                Events.Emit(new Ev.Explosion { X = p.X, Z = p.Z, Radius = run.SlamRadius, School = School.Physical, Power = 1.1, Art = w != null ? w.Art + "_slam" : null, Rank = w?.Rank ?? 0 });
                Events.Emit(new Ev.Shake { Amount = 0.5 });
                if (w != null) Events.Emit(new Ev.Charge { Phase = ChargePhase.Slam, X = p.X, Z = p.Z, DX = a.RushDX, DZ = a.RushDZ, Radius = run.SlamRadius });
                ForEachHostileInRadius(p.X, p.Z, run.SlamRadius, (e, d) =>
                {
                    double dd = d == 0 ? 1 : d;
                    HitEnemy(e, run.SlamDamage, School.Physical, run.SlamTags, new HitOpts { Weapon = w, Knockback = run.SlamKnockback, DirX = (e.X - p.X) / dd, DirZ = (e.Z - p.Z) / dd });
                    ApplyStatus(e, new StatusPayload(StatusKind.Stun, 1, 1, e.Boss ? run.SlamBossStun : run.SlamStun), 0);
                });
            }
            RuleChargeEnd(run, w);
            if (w != null) Events.Emit(new Ev.Charge { Phase = ChargePhase.End, X = p.X, Z = p.Z, DX = a.RushDX, DZ = a.RushDZ });
        }
        (HeavyBy, credit) = (hb, was);
    }

    /* ---------------------------------------------------------- iron vow -- */

    /// <summary>Iron Vow's brace while it holds: the skill, the plant left (her walk held), the brace left, the store, and
    /// when a Store was last told (the view hears one each 0.15 s at most).</summary>
    internal sealed class BraceRun { public WeaponInst Weapon = null!; public double Plant, T, Stored, SaidAt = double.NegativeInfinity, HeldT, Age; public bool Heavy; }
    internal BraceRun? Braced;
    /// <summary>The ids Iron Vow's last burst struck (tests: what its ring marked is what it hit).</summary>
    public readonly List<int> VowStruck = new();
    /// <summary>Iron Vow bracing now (the plant and the brace), and its store so far.</summary>
    public bool Bracing => Braced != null;
    public double VowStored => Braced?.Stored ?? 0;
    /// <summary>Her feet held by the vow's plant (UpdatePlayer).</summary>
    bool VowPlanted => Braced is { Plant: > 0 } && !RuleMarch;

    /// <summary>Iron Vow (behavior brace, cast press): she plants (Plant seconds, no walking) and braces (Brace seconds
    /// after the plant; she may walk): blows on her land at Halve and Store of each, before the halving, is kept; it ends
    /// in a burst round her (TickVow). Not while she is carried, nor again while it holds.</summary>
    internal bool SkillBrace(WeaponInst w)
    {
        if (Braced != null || FireFrom != null || Refiring) return false;
        var p = Player;
        Braced = new BraceRun { Weapon = w, Plant = Math.Max(0, w.Num(s => s.Plant) ?? 0.3), T = BraceSecondsOf(w), Heavy = HeavyBy == w };
        RuleBraceBegin(w, Braced.Plant + Braced.T);
        p.Vx = p.Vz = 0;
        Events.Emit(new Ev.Brace { Phase = BracePhase.Start, X = p.X, Z = p.Z, Radius = Firing.AreaOf(this, w, w.Num(s => s.Radius) ?? 5) });
        return true;
    }

    /// <summary>A blow on her, its final amount (HurtPlayer): bracing, a share is stored (before the halving) and it lands
    /// at Halve.</summary>
    double VowTake(double dmg, Enemy? from = null)
    {
        if (Braced is not { } v || dmg <= 0) return dmg;
        var w = v.Weapon;
        v.Stored += dmg * RuleVowStore(w, w.Num(s => s.Store) ?? 0.2);
        RuleVowBlow(w, dmg, from);
        if (Time - v.SaidAt >= 0.15)
        {
            v.SaidAt = Time;
            Events.Emit(new Ev.Brace { Phase = BracePhase.Store, X = Player.X, Z = Player.Z, Radius = Firing.AreaOf(this, w, w.Num(s => s.Radius) ?? 5), Stored = v.Stored });
        }
        return dmg * RuleVowHalve(w, w.Num(s => s.Halve) ?? 0.5);
    }

    /// <summary>The vow's clock (each step in the fight): the plant, then the brace; over, the burst: everything within
    /// Radius of her struck for Damage plus the store times StoreMul (the skill's; its bossDamage on a boss), thrown outward,
    /// a lesser foe stunned.</summary>
    void TickVow(double dt)
    {
        TickRules(dt);
        if (Braced is not { } v) return;
        if (!Player.Alive) { Braced = null; return; }
        if (RuleBraceHolds(v, dt) && v.Plant <= 0 && v.T <= dt) return;
        if (v.Plant > 0) { v.Plant = Math.Max(0, v.Plant - dt); return; }
        v.T -= dt;
        if (v.T > 0) return;
        Braced = null;
        var w = v.Weapon;
        var p = Player;
        double r = Firing.AreaOf(this, w, RuleBurstRadius(v, RuleVowRadius(w, w.Num(s => s.Radius) ?? 5))), kb = w.Num(s => s.Knockback) ?? 1.2, stun = w.Num(s => s.Stun) ?? 0.4;
        double dmg = (w.Damage + v.Stored * WkOver(w, "iron_vow.old_grudge", "storeMul", w.Num(s => s.StoreMul) ?? 3)) * RuleDamageMul(w);
        var status = Firing.StatusWith(this, w);
        var ring = HostilesInRadius(p.X, p.Z, r);
        Events.Emit(new Ev.Brace { Phase = BracePhase.Burst, X = p.X, Z = p.Z, Radius = r, Stored = v.Stored, Hit = ring.Count });
        if (RuleBurstWave(v, dmg)) return;
        var (hb, was) = (HeavyBy, credit);
        HeavyBy = v.Heavy ? w : null;
        credit = w.Id;
        VowStruck.Clear();
        foreach (var e in ring)
        {
            double d = Dist(e.X, e.Z, p.X, p.Z), dd = d < 0.01 ? 1 : d;
            VowStruck.Add(e.Id);
            HitEnemy(e, dmg, w.School, w.Tags, new HitOpts { Weapon = w, Knockback = kb, DirX = d < 0.01 ? Math.Sin(p.Facing) : (e.X - p.X) / dd, DirZ = d < 0.01 ? Math.Cos(p.Facing) : (e.Z - p.Z) / dd, Status = status });
            if (!e.Alive || e.State == EnemyState.Dying || e.Elite || e.Boss) continue;
            ApplyStatus(e, new StatusPayload(StatusKind.Stun, 1, 1, stun), 0);
            Interrupt(e);
        }
        (HeavyBy, credit) = (hb, was);
        Events.Emit(new Ev.Explosion { X = p.X, Z = p.Z, Radius = r, School = w.School, Power = 1.1, Art = w.Art + "_burst", Rank = w.Rank });
        Events.Emit(new Ev.Shake { Amount = 0.45 });
    }

    /* --------------------------------------------------------- bladestorm -- */

    /// <summary>Her pace while a spin runs (its Pace share; 1 otherwise): she steers freely, a little slower.</summary>
    double SpinPace()
    {
        double m = 1;
        foreach (var w in Weapons) if (w.Channeling && w.Behavior == WeaponBehavior.Spin) m *= w.Num(s => s.Pace) ?? 0.85;
        return m;
    }
}

public static partial class Firing
{
    /// <summary>A base number of the skill (a break's, a split line's) grown as its Damage is: rank, mods, Turn.</summary>
    static double Grown(WeaponInst w, double baseValue) => baseValue * w.Damage / Math.Max(1e-9, w.Def.Base.Damage ?? 1);

    /// <summary>One blow of the storm (each ChannelGap while held, TickPressed): everything within Radius struck and
    /// pushed outward; a heavy blow (the Hand's count, or its own HeavyEvery) throws a Sunder line ahead along her
    /// facing, held pending (at most MaxLines: the oldest fades) for the break to split. True: a spin always swings.</summary>
    static bool FireSpin(Battle b, WeaponInst w)
    {
        if (!w.Channeling || b.FireFrom != null || b.Refiring) return false;
        var p = b.Player;
        bool heavy = b.HeavyBy == w;
        double r = b.SpinRadiusOf(w), kb = w.Num(s => s.Knockback) ?? 0.3, cut = w.Damage * b.RuleDamageMul(w);
        b.RuleChopBegin(w);
        if (w.SpinTicks == 0) b.Events.Emit(new Ev.Spin { Phase = SpinPhase.Start, X = p.X, Z = p.Z, Radius = r });
        w.SpinTicks++;
        var status = StatusWith(b, w);
        b.ForEachHostileInRadius(p.X, p.Z, r, (e, d) =>
        {
            double dd = d == 0 ? 1 : d;
            b.HitEnemy(e, cut, w.School, w.Tags, new HitOpts { Weapon = w, Knockback = kb, DirX = (e.X - p.X) / dd, DirZ = (e.Z - p.Z) / dd, Status = status, Heavy = b.RuleBeforeCut(w, e) });
            b.RuleAfterCut(w, e, p.X, p.Z);
        });
        b.Events.Emit(new Ev.Spin { Phase = SpinPhase.Tick, X = p.X, Z = p.Z, Radius = r, Heavy = heavy });
        if (heavy && w.Num(s => s.Line) is { } line)
        {
            double len = AreaOf(b, w, line), width = AreaOf(b, w, w.Num(s => s.BeamWidth) ?? 1.2);
            double dx = Math.Sin(p.Facing), dz = Math.Cos(p.Facing);
            int most = Math.Max(1, (int)(w.Num(s => s.MaxLines) ?? 6));
            while (w.Lines.Count >= most) { Fade(b, w.Lines[0]); w.Lines.RemoveAt(0); }
            var l = new SpinLineRec(++b.SpinLineIds, p.X, p.Z, p.X + dx * len, p.Z + dz * len, width);
            w.Lines.Add(l);
            b.Events.Emit(new Ev.SpinLine { Phase = SpinLinePhase.Thrown, Id = l.Id, X0 = l.X0, Z0 = l.Z0, X1 = l.X1, Z1 = l.Z1, Width = l.Width });
        }
        return true;
    }

    /// <summary>The spin ended (released, or at its longest): it may still be broken for BreakWindow seconds.</summary>
    static void SpinEnded(Battle b, WeaponInst w)
    {
        w.BreakUntil = b.Time + (w.Num(s => s.BreakWindow) ?? 1);
        b.Events.Emit(new Ev.Spin { Phase = SpinPhase.End, X = b.Player.X, Z = b.Player.Z, Radius = AreaOf(b, w, w.Num(s => s.Radius) ?? 3.2) });
    }

    /// <summary>What a storm of this many seconds makes of its break: x1 to BreakFrom (0.5 s), then linearly to BreakGrow
    /// (x1.6) at its longest hold (ChannelTime).</summary>
    public static double BreakGrowth(WeaponInst w, double spent)
    {
        double from = w.Num(s => s.BreakFrom) ?? 0.5, most = w.Num(s => s.BreakGrow) ?? 1.6, cap = w.ChannelMax;
        if (cap <= from) return spent >= cap ? most : 1;
        return 1 + (most - 1) * Math.Clamp((spent - from) / (cap - from), 0, 1);
    }

    /// <summary>What a storm that spent this much Resolve makes of its break: x1 at none to BreakGrow (x1.6) at BreakSpent
    /// (100), linearly, capped.</summary>
    public static double BreakGrowthSpent(WeaponInst w, double resolve)
    {
        double most = w.Num(s => s.BreakGrow) ?? 1.6, at = Math.Max(1e-9, w.Num(s => s.BreakSpent) ?? 100);
        return 1 + (most - 1) * Math.Clamp(resolve / at, 0, 1);
    }

    /// <summary>A storm on: spinning, or within its BreakWindow after (its second key breaks it then).</summary>
    public static bool InStorm(Battle b, WeaponInst w) => w.Channeling || (w.BreakUntil >= 0 && b.Time <= w.BreakUntil);

    /// <summary>A spin union's other part (its B; no spin union in data since 13 Nov 2026) at the union's rank and mods, on the union's second
    /// key: what that key swings out of a storm. Never in Weapons (it holds no slot of its own); its damage is its own id's.</summary>
    internal static WeaponInst? HalfOf(WeaponInst w)
    {
        if (w.Half == null)
        {
            var u = Content.Unions.All.FirstOrDefault(x => x.Into == w.Id);
            if (u == null || !Content.Weapons.All.ContainsKey(u.B)) return null;
            w.Half = new WeaponInst(u.B, w.Rank, w.Slot2) { Timer = 0 };
        }
        var h = w.Half;
        // In the campaign the half keeps its part's record (Sunder's: a hold that builds Resolve).
        h.Press = w.Press != null ? h.Def.Press : null;
        h.Rank = w.Rank;
        h.Slot = w.Slot2;
        var (m, hm) = (w.Mods, h.Mods);
        (hm.Damage, hm.Area, hm.Cooldown, hm.Speed, hm.Duration, hm.Homing, hm.Projectiles, hm.Pierce) = (m.Damage, m.Area, m.Cooldown, m.Speed, m.Duration, m.Homing, m.Projectiles, m.Pierce);
        return h;
    }

    /// <summary>The second key out of a storm (pressed, or held: again each time it is ready): the half swings as itself
    /// (Sunder: its slash, every fourth heavy with its line), on its own cooldown. False: not ready, or a storm is on.</summary>
    public static bool SwingHalf(Battle b, WeaponInst w)
    {
        if (w.DisabledT > 0 || InStorm(b, w) || HalfOf(w) is not { } h || h.Timer > 0 || b.BlowPending(h)) return false;
        if (b.FireFrom != null || b.Refiring) return false;
        // (a chain's cut never starts mid-dash, in a leap or a rush: Sim/SwingChain.cs)
        if (b.CutBarred(h)) return false;
        int kills0 = h.Kills, key0 = h.BlowN;
        var aim0 = b.CastAt;
        b.CastAt = b.AimFor(h);
        bool fired, later = false;
        // (campaign: the half's slash lands on its clip's contact, Sim/Contact.cs)
        try { later = b.DeferBlow(h); fired = later || CastOnce(b, h); }
        finally { b.CastAt = aim0; }
        if (later) { b.CastPose(h); return true; }
        if (fired) { Rearm(b, h, true, kills0, key0); if (Late(b, h) > 0) h.Timer = Math.Max(0, h.Timer - Late(b, h)); b.CastPose(h); }
        return fired;
    }

    /// <summary>The half's clock (TickPressed): its wait runs down; held out of a storm, it swings each time it is ready.</summary>
    static void TickHalf(Battle b, WeaponInst w, double dt)
    {
        if (HalfOf(w) is not { } h) return;
        if (h.Chain != null) { ChainReady(b, h, dt); if (h.Timer > 0) h.Timer = Math.Max(0, h.Timer - dt); }
        // (M3 MR 3 clock: the unchained half notes the instant its wait runs out, Firing.CountDown)
        else if (h.Timer > 0) { CountDown(b, h, dt); h.Timer = Math.Max(0, h.Timer); }
        if (w.Held2 && h.Timer <= 0) SwingHalf(b, w);
    }

    static void Fade(Battle b, SpinLineRec l) =>
        b.Events.Emit(new Ev.SpinLine { Phase = SpinLinePhase.Faded, Id = l.Id, X0 = l.X0, Z0 = l.Z0, X1 = l.X1, Z1 = l.Z1, Width = l.Width });

    /// <summary>Unbroken, the pending lines fade and deal nothing.</summary>
    static void FadeLines(Battle b, WeaponInst w)
    {
        foreach (var l in w.Lines) Fade(b, l);
        w.Lines.Clear();
    }

    /// <summary>The break (a fresh press of Sunder's key, or a spin union's second; Battle.PressSkill), while it spins or within BreakWindow after: a
    /// heavy blow all round her (BreakRadius, BreakDamage, BreakStun, BreakKnockback), and every pending line splits at
    /// once, striking what is on it for LineDamage (heavy). The storm is over: its cooldown starts. Nothing to break:
    /// false, nothing happens.</summary>
    public static bool SpinBreak(Battle b, WeaponInst w)
    {
        if (w.Behavior != WeaponBehavior.Spin || w.DisabledT > 0) return false;
        if (!w.Channeling && !(w.BreakUntil >= 0 && b.Time <= w.BreakUntil)) return false;
        var p = b.Player;
        double spent = w.Channeling ? w.ChannelT : w.StormT;
        if (w.Channeling)
        {
            w.StormT = spent;
            w.Channeling = false;
            b.Events.Emit(new Ev.Channel { Weapon = w.Id, Slot = w.Slot, On = false, X = p.X, Z = p.Z });
        }
        w.BreakUntil = -1;
        // In the campaign with Resolve, the break grows with the Resolve the storm spent; elsewhere with its seconds.
        double grow = b.Resolve.On && w.Press?.Drain is > 0 ? BreakGrowthSpent(w, b.Resolve.SpentInStorm) : BreakGrowth(w, spent);
        double r = AreaOf(b, w, w.Num(s => s.BreakRadius) ?? 4) * grow, dmg = Grown(w, w.Num(s => s.BreakDamage) ?? 60) * grow;
        double stun = w.Num(s => s.BreakStun) ?? 0.5, kb = w.Num(s => s.BreakKnockback) ?? 1.5;
        b.Events.Emit(new Ev.Spin { Phase = SpinPhase.Break, X = p.X, Z = p.Z, Radius = r, Heavy = true, Grow = grow });
        b.ForEachHostileInRadius(p.X, p.Z, r, (e, d) =>
        {
            double dd = d == 0 ? 1 : d;
            b.HitEnemy(e, dmg, w.School, w.Tags, new HitOpts { Weapon = w, Knockback = kb, DirX = (e.X - p.X) / dd, DirZ = (e.Z - p.Z) / dd, Heavy = true });
            if (e.Alive && e.State != EnemyState.Dying) { b.ApplyStatus(e, new StatusPayload(StatusKind.Stun, 1, 1, stun), 0); b.Interrupt(e); }
        });
        double lineDmg = Grown(w, w.Num(s => s.LineDamage) ?? 33.6);
        foreach (var l in w.Lines)
        {
            b.Events.Emit(new Ev.SpinLine { Phase = SpinLinePhase.Split, Id = l.Id, X0 = l.X0, Z0 = l.Z0, X1 = l.X1, Z1 = l.Z1, Width = l.Width });
            double len = Math.Max(0.01, Dist(l.X0, l.Z0, l.X1, l.Z1)), dx = (l.X1 - l.X0) / len, dz = (l.Z1 - l.Z0) / len;
            b.ForEachHostileNearSegment(l.X0, l.Z0, l.X1, l.Z1, l.Width, e =>
                b.HitEnemy(e, lineDmg, w.School, w.Tags, new HitOpts { Weapon = w, Heavy = true, DirX = dx, DirZ = dz }));
            b.LinesStruck++;
        }
        w.Lines.Clear();
        b.Events.Emit(new Ev.Shake { Amount = 0.5 });
        w.Timer = CooldownOf(b, w);
        return true;
    }
}

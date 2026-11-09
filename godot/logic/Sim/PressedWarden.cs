using System;
using System.Collections.Generic;
using SurvivorUnchained.Content;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Sim;

/* The Warden's pressed skills (P7, the ARPG turn): Heroic Leap (behavior leap, cast press), Shield Charge (charge,
 * press; the old Bull Rush's run, one path with the art: Battle.ChargeStep) and Bladestorm (spin, channel: the first
 * two-key Union, its first key held spins, its second pressed breaks the storm). Their numbers are skills.json's; the
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
        double range = w.Num(s => s.Range) ?? 9, min = Math.Min(range, w.Num(s => s.MinRange) ?? 3);
        var (dx, dz, d) = SkillDir(range);
        d = Math.Clamp(d, min, range);
        var (x1, z1) = LeapTo(dx, dz, d);
        double r = Firing.AreaOf(this, w, w.Num(s => s.Radius) ?? 3.5), air = Math.Max(0.1, w.Num(s => s.Air) ?? 0.62);
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
        double kb = w.Num(s => s.Knockback) ?? 2.5, stun = w.Num(s => s.Stun) ?? 0.8, stagger = w.Num(s => s.Stagger) ?? 0.3;
        var ring = HostilesInRadius(leap.X1, leap.Z1, leap.Radius);
        LeapStruck.Clear();
        foreach (var e in ring)
        {
            double d = Dist(e.X, e.Z, leap.X1, leap.Z1), dd = d < 0.01 ? 1 : d;
            double ox = d < 0.01 ? Math.Sin(Player.Facing) : (e.X - leap.X1) / dd, oz = d < 0.01 ? Math.Cos(Player.Facing) : (e.Z - leap.Z1) / dd;
            LeapStruck.Add(e.Id);
            HitEnemy(e, w.Damage, w.School, w.Tags, new HitOpts { Weapon = w, Knockback = kb, DirX = ox, DirZ = oz });
            if (!e.Alive || e.State == EnemyState.Dying) continue;
            ApplyStatus(e, new StatusPayload(StatusKind.Stun, 1, 1, e.Elite || e.Boss ? stagger : stun), 0);
            Interrupt(e);
        }
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
        double dist = w.Num(s => s.Range) ?? 8, time = Math.Max(0.05, w.Num(s => s.RushTime) ?? 0.3);
        var (dx, dz, _) = SkillDir(dist);
        double share = SkillRule(w, "iron_hide") ? SkillFull(w, "iron_hide", "barrier", 0.25) : w.Num(s => s.Barrier) ?? 0.15;
        Art.Barrier = MaxHp * share;
        Barrier(Art.Barrier, w.Num(s => s.Duration) ?? 4);
        Art.Struck.Clear();
        double x0 = p.X, z0 = p.Z;
        StartRush(AbilityKind.BullRush, dx, dz, dist, time);
        bool gore = SkillRule(w, "gore");
        double stun = w.Num(s => s.Stun) ?? 1;
        Art.Charge = new ChargeRun
        {
            Weapon = w, Heavy = HeavyBy == w, Tags = w.Tags, SlamTags = w.Tags, Damage = w.Damage, Knockback = w.Num(s => s.Knockback) ?? 2.2,
            ChampionMul = gore ? SkillFull(w, "gore", "champions", 1.5) : 1, ChampionStun = stun, BossStun = stun,
            Bleed = gore ? new StatusPayload(StatusKind.Bleed, 1, SkillFull(w, "gore", "power", 0.8), SkillFull(w, "gore", "seconds", 4)) : null,
            PerStruck = SkillRule(w, "unbroken") ? SkillFull(w, "unbroken", "health", 0.02) : 0, StruckCap = SkillFull(w, "unbroken", "cap", 0.2),
            Slam = w.Evolution?.Id == "pile_driver", SlamRadius = Firing.AreaOf(this, w, w.Num(s => s.Radius) ?? 3),
            SlamDamage = w.Damage * (w.Num(s => s.Slam) ?? 1.4), SlamKnockback = 1.4, SlamStun = stun, SlamBossStun = stun,
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
        ForEachHostileInRadius(p.X, p.Z, p.Radius + 0.6, (e, _) =>
        {
            if (stopper != null || !a.Struck.Add(e.Id)) return;
            if (e.Elite || e.Boss)
            {
                stopper = e;
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
            if (w != null) Events.Emit(new Ev.Charge { Phase = ChargePhase.End, X = p.X, Z = p.Z, DX = a.RushDX, DZ = a.RushDZ });
        }
        (HeavyBy, credit) = (hb, was);
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
        double r = AreaOf(b, w, w.Num(s => s.Radius) ?? 3.2), kb = w.Num(s => s.Knockback) ?? 0.3;
        if (w.SpinTicks == 0) b.Events.Emit(new Ev.Spin { Phase = SpinPhase.Start, X = p.X, Z = p.Z, Radius = r });
        w.SpinTicks++;
        var status = StatusWith(b, w);
        b.ForEachHostileInRadius(p.X, p.Z, r, (e, d) =>
        {
            double dd = d == 0 ? 1 : d;
            b.HitEnemy(e, w.Damage, w.School, w.Tags, new HitOpts { Weapon = w, Knockback = kb, DirX = (e.X - p.X) / dd, DirZ = (e.Z - p.Z) / dd, Status = status });
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
        w.BreakUntil = b.Time + (w.Num(s => s.BreakWindow) ?? 0.4);
        b.Events.Emit(new Ev.Spin { Phase = SpinPhase.End, X = b.Player.X, Z = b.Player.Z, Radius = AreaOf(b, w, w.Num(s => s.Radius) ?? 3.2) });
    }

    static void Fade(Battle b, SpinLineRec l) =>
        b.Events.Emit(new Ev.SpinLine { Phase = SpinLinePhase.Faded, Id = l.Id, X0 = l.X0, Z0 = l.Z0, X1 = l.X1, Z1 = l.Z1, Width = l.Width });

    /// <summary>Unbroken, the pending lines fade and deal nothing.</summary>
    static void FadeLines(Battle b, WeaponInst w)
    {
        foreach (var l in w.Lines) Fade(b, l);
        w.Lines.Clear();
    }

    /// <summary>The break (Bladestorm's second key, Battle.PressSkill), while it spins or within BreakWindow after: a
    /// heavy blow all round her (BreakRadius, BreakDamage, BreakStun, BreakKnockback), and every pending line splits at
    /// once, striking what is on it for LineDamage (heavy). The storm is over: its cooldown starts. Nothing to break:
    /// false, nothing happens.</summary>
    public static bool SpinBreak(Battle b, WeaponInst w)
    {
        if (w.Behavior != WeaponBehavior.Spin || w.DisabledT > 0) return false;
        if (!w.Channeling && !(w.BreakUntil >= 0 && b.Time <= w.BreakUntil)) return false;
        var p = b.Player;
        if (w.Channeling)
        {
            w.Channeling = false;
            b.Events.Emit(new Ev.Channel { Weapon = w.Id, Slot = w.Slot, On = false, X = p.X, Z = p.Z });
        }
        w.BreakUntil = -1;
        double r = AreaOf(b, w, w.Num(s => s.BreakRadius) ?? 4), dmg = Grown(w, w.Num(s => s.BreakDamage) ?? 60);
        double stun = w.Num(s => s.BreakStun) ?? 0.5, kb = w.Num(s => s.BreakKnockback) ?? 1.5;
        b.Events.Emit(new Ev.Spin { Phase = SpinPhase.Break, X = p.X, Z = p.Z, Radius = r, Heavy = true });
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

using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Sim;

/* The P7 wicks' rules (skill_lamps.json, engine "rule"): Heroic Leap, Butcher's Cleaver (and Bladestorm's spin, the
 * Cleaver's half: it carries the Cleaver's lamps), Iron Vow and Shield Charge. Each lamp's sentence is its spec, its args
 * its numbers (the sentence's own number is the fallback). Wk: the lamp is lit and on this skill (a shape Turn goes dark
 * under an evolution that replaced its shape, as Turns.Works rules); Wn: its number, kept in full by night.
 *
 * The hooks, one line each: Firing.CooldownOf (RuleCooldownMul), Battle.CostOf and TickPressed's drain (RulePayMul: a
 * "sooner" or "slower" Cleaver lamp shortens its wait outside the campaign and changes its Resolve cost or its storm's drain
 * in the campaign by the same fraction), Firing.Rearm (RuleRearm), StatusWith (RuleStatus), FireSlash/ConeHit/FireSpin
 * (reach, damage, the cut's before and after), HeavyEveryOf (overhand), the leap's and charge's own code (PressedWarden),
 * HurtPlayer (RuleShieldBlock, VowTake's striker), OnBlocked, LampsOnPerfect, KillEnemy (RuleOnDeath), her pace
 * (RuleMoveMul), the leap's landing (RuleLeapHangs), the AI's want (RuleGoaded), and TickVow (TickRules). With no rule lit
 * every hook is 1, null or a no-op, so a fight without these lamps runs as it did. */
public sealed partial class Battle
{
    /// <summary>The shape Turns among these rules (dark under an evolution that replaced the skill's shape).</summary>
    static readonly HashSet<string> RuleShapeTurns = new()
    {
        "heroic_leap.henge", "heroic_leap.iron_comet", "cleaver.cross_cut", "iron_vow.full_measure", "iron_vow.unyielding",
        "shield_charge.landslide", "shield_charge.stampede",
    };
    static readonly Dictionary<string, bool> cleaves = new();

    /// <summary>The Cleaver, or a union whose first part (its spin) is the Cleaver's: Bladestorm.</summary>
    internal static bool Cleaves(WeaponInst w)
    {
        if (w.Def.Id == "cleaver") return true;
        if (!cleaves.TryGetValue(w.Def.Id, out var c))
            cleaves[w.Def.Id] = c = Unions.All.Any(u => u.Into == w.Def.Id && u.A == "cleaver");
        return c;
    }

    /// <summary>A P7 rule lamp ("heroic_leap.crater") lit and at work on this skill.</summary>
    internal bool Wk(WeaponInst? w, string id)
    {
        if (w == null || Lamps.Rules.Count == 0 || !Lamps.Has(id)) return false;
        int dot = id.IndexOf('.');
        bool own = string.CompareOrdinal(w.Def.Id, 0, id, 0, dot) == 0 && w.Def.Id.Length == dot;
        if (!own && !(id.StartsWith("cleaver.", StringComparison.Ordinal) && Cleaves(w))) return false;
        if (own && RuleShapeTurns.Contains(id) && Turns.ReplacesShape(w.Evolution)) return false;
        return true;
    }

    internal double Wn(string id, string arg, double fallback) => Lamps.Full(id, arg, fallback);

    /// <summary>The skill's base number, or the lamp's in its place ("reaches 4.5 m, not 3.5 m").</summary>
    internal double WkOver(WeaponInst w, string id, string arg, double baseValue) => Wk(w, id) ? Wn(id, arg, baseValue) : baseValue;

    /// <summary>The rules' damage price (restless, breakthrough, penance, bled_dry, light_grip).</summary>
    internal double RuleDamageMul(WeaponInst w)
    {
        if (Lamps.Rules.Count == 0) return 1;
        double m = 1;
        if (Wk(w, "heroic_leap.restless")) m *= Wn("heroic_leap.restless", "damage", 0.8);
        if (Wk(w, "shield_charge.breakthrough")) m *= Wn("shield_charge.breakthrough", "damage", 0.8);
        if (Wk(w, "iron_vow.penance")) m *= Wn("iron_vow.penance", "damage", 0.75);
        if (Cleaves(w))
        {
            if (Wk(w, "cleaver.bled_dry")) m *= Wn("cleaver.bled_dry", "damage", 0.8);
            if (Wk(w, "cleaver.light_grip")) m *= Wn("cleaver.light_grip", "damage", 0.85);
        }
        return m;
    }

    /* ---------------------------------------------------------- waits and costs -- */

    /// <summary>A skill paid for with Resolve now (a cost or a drain, the campaign's warden).</summary>
    bool PaysResolve(WeaponInst w) => Resolve.On && (w.Press?.Resolve is > 0 || w.Press?.Drain is > 0);

    /// <summary>The Cleaver's pace lamps: big_game (15% slower), light_grip (25% faster).</summary>
    double CleaverPace(WeaponInst w) =>
        (Wk(w, "cleaver.big_game") ? Wn("cleaver.big_game", "cooldown", 1.15) : 1) * (Wk(w, "cleaver.light_grip") ? Wn("cleaver.light_grip", "cooldown", 0.8) : 1);

    /// <summary>The rules on a skill's wait (Firing.CooldownOf): ninepins and old_grudge ("waits 11 s, not 8"), the
    /// Cleaver's pace where it pays no Resolve, war_pace (her swings and casts 25% faster for 3 s after a landing).</summary>
    internal double RuleCooldownMul(WeaponInst w)
    {
        if (Lamps.Rules.Count == 0) return 1;
        double m = 1;
        if (Time < warPaceUntil) m /= Math.Max(0.1, warPace);
        if (Wk(w, "heroic_leap.ninepins")) m *= Wn("heroic_leap.ninepins", "cooldown", 11) / Math.Max(0.1, w.Def.Base.Cooldown ?? 8);
        if (Wk(w, "iron_vow.old_grudge")) m *= Wn("iron_vow.old_grudge", "cooldown", 14) / Math.Max(0.1, w.Def.Base.Cooldown ?? 10);
        if (Cleaves(w) && !PaysResolve(w)) m *= CleaverPace(w);
        return m;
    }

    /// <summary>What a Cleaver lamp makes of its Resolve cost or its storm's drain (the campaign): its pace's fraction,
    /// and next_cut's chop paid for by the one before.</summary>
    internal double RulePayMul(WeaponInst w)
    {
        if (Lamps.Rules.Count == 0 || !Cleaves(w)) return 1;
        return ReferenceEquals(freeChop, w) ? 0 : CleaverPace(w);
    }

    WeaponInst? freeChop;
    int chopStruck;

    /// <summary>A cast's wait set (Firing.Rearm): next_cut (a chop that strikes 6 or more readies the next at once; in
    /// the campaign the next chop is free).</summary>
    internal void RuleRearm(WeaponInst w, bool fired)
    {
        if (Lamps.Rules.Count == 0 || !fired || !Cleaves(w)) return;
        if (ReferenceEquals(freeChop, w)) freeChop = null;
        if (Wk(w, "cleaver.next_cut") && chopStruck >= (int)Wn("cleaver.next_cut", "struck", 6))
        {
            w.Timer = 0;
            if (PaysResolve(w)) freeChop = w;
        }
    }

    /* ------------------------------------------------------------ the cleaver -- */

    /// <summary>The Cleaver's bleed (StatusWith): laid_open (every chop, 40% over 4 s), bled_dry (all of it in 1.5 s).</summary>
    internal StatusPayload? RuleStatus(WeaponInst w)
    {
        if (Lamps.Rules.Count == 0 || !Cleaves(w)) return null;
        bool open = Wk(w, "cleaver.laid_open"), dry = Wk(w, "cleaver.bled_dry");
        if (!open && !dry) return null;
        var own = w.StatusOf is { Kind: StatusKind.Bleed } s ? s : new StatusPayload(StatusKind.Bleed, 0.35, 0.3, 3);
        double chance = open ? 1 : own.Chance, power = open ? Wn("cleaver.laid_open", "power", 0.4) : own.Power;
        double dur = open ? Wn("cleaver.laid_open", "duration", 4) : own.Duration;
        if (dry) dur = Wn("cleaver.bled_dry", "duration", 1.5);
        return new StatusPayload(StatusKind.Bleed, chance, power, dur);
    }

    /// <summary>The Cleaver's reach (FireSlash; a spin's radius): butchers_hook's 3.5 m, not 2.5 m (a spin by the same share).</summary>
    internal double RuleReach(WeaponInst w, double baseValue)
    {
        if (!Wk(w, "cleaver.butchers_hook")) return baseValue;
        double reach = Wn("cleaver.butchers_hook", "reach", 3.5);
        return w.Def.Id == "cleaver" ? Math.Max(baseValue, reach) : baseValue * reach / 2.5;
    }

    /// <summary>A chop's damage (FireSlash): the price lamps, and cross_cut's 65% (it cuts twice).</summary>
    internal double RuleCutMul(WeaponInst w)
    {
        if (Lamps.Rules.Count == 0 || !Cleaves(w)) return 1;
        return RuleDamageMul(w) * (w.Def.Id == "cleaver" && Wk(w, "cleaver.cross_cut") ? Wn("cleaver.cross_cut", "damage", 0.65) : 1);
    }

    /// <summary>A swing begins (FireSlash, FireSpin): its count of struck starts again.</summary>
    internal void RuleChopBegin(WeaponInst w) { if (Lamps.Rules.Count > 0 && Cleaves(w)) chopStruck = 0; }

    /// <summary>Before a cut lands on e (ConeHit, FireSpin): rupture (a bleeding thing torn open: the rest of its bleed at
    /// once, splashed 2.5 m round for as much). True: the cut is heavy on it (big_game: a champion).</summary>
    internal bool RuleBeforeCut(WeaponInst w, Enemy e)
    {
        if (Lamps.Rules.Count == 0 || !Cleaves(w)) return false;
        if (Wk(w, "cleaver.rupture") && e.Status[StatusKind.Bleed] is { T: > 0 } s)
        {
            double rest = s.Power * s.T * Math.Max(1, s.Stacks), share = Wn("cleaver.rupture", "share", 1);
            s.T = 0;
            s.Power = 0;
            var near = HostilesInRadius(e.X, e.Z, Wn("cleaver.rupture", "radius", 2.5));
            Events.Emit(new Ev.Explosion { X = e.X, Z = e.Z, Radius = Wn("cleaver.rupture", "radius", 2.5), School = School.Physical, Power = 0.6, Art = w.Art + "_rupture", Rank = w.Rank });
            if (rest > 0)
            {
                HitEnemy(e, rest, School.Physical, w.Tags, new HitOpts { Weapon = w, NoCrit = true });
                foreach (var o in near)
                    if (o != e && o.Alive && o.State != EnemyState.Dying) HitEnemy(o, rest * share, School.Physical, w.Tags, new HitOpts { Weapon = w, NoCrit = true });
            }
        }
        return Wk(w, "cleaver.big_game") && e.Elite && !e.Boss;
    }

    /// <summary>After a cut struck e from (fx, fz): butchers_hook drags it 1 m toward her; a heavy chop (hewn_down) throws
    /// a lesser thing 3 m and knocks it down.</summary>
    internal void RuleAfterCut(WeaponInst w, Enemy e, double fx, double fz)
    {
        if (Lamps.Rules.Count == 0 || !Cleaves(w)) return;
        chopStruck++;
        if (!e.Alive || e.State == EnemyState.Dying || e.Boss) return;
        if (Wk(w, "cleaver.butchers_hook")) Shove(e, fx, fz, -Wn("cleaver.butchers_hook", "drag", 1));
        if (!e.Elite && HeavyBy == w && Wk(w, "cleaver.hewn_down"))
        {
            Shove(e, fx, fz, Wn("cleaver.hewn_down", "throw", 3));
            Stun(e, Wn("cleaver.hewn_down", "stun", 0.6));
        }
    }

    readonly List<(double At, WeaponInst W, double A, double Arc, double Reach)> crossCuts = new();

    /// <summary>cross_cut: the chop cuts back across her front 0.25 s later.</summary>
    internal void RuleCrossCut(WeaponInst w, double a, double arc, double reach)
    {
        if (Refiring || w.Def.Id != "cleaver" || !Wk(w, "cleaver.cross_cut")) return;
        crossCuts.Add((Time + Wn("cleaver.cross_cut", "gap", 0.25), w, a, arc, reach));
    }

    /// <summary>A thing dies (KillEnemy): spatter (one dying bleeding sprays 3 m round, bleeding what it splashes for 30%
    /// of the chop over 3 s).</summary>
    internal void RuleOnDeath(Enemy e)
    {
        if (Lamps.Rules.Count == 0 || e.Status[StatusKind.Bleed] is not { T: > 0 }) return;
        var w = Weapons.Find(Cleaves);
        if (w == null || !Wk(w, "cleaver.spatter")) return;
        double chop = w.Damage * RuleDamageMul(w);
        var pay = new StatusPayload(StatusKind.Bleed, 1, Wn("cleaver.spatter", "power", 0.3), Wn("cleaver.spatter", "duration", 3));
        double r = Wn("cleaver.spatter", "radius", 3);
        Events.Emit(new Ev.Explosion { X = e.X, Z = e.Z, Radius = r, School = School.Physical, Power = 0.4, Art = w.Art + "_spatter", Rank = w.Rank });
        foreach (var o in HostilesInRadius(e.X, e.Z, r))
            if (o != e) ApplyStatus(o, pay, chop, 1, w.Id);
    }

    /* -------------------------------------------------------------- the leap -- */

    double warPaceUntil = double.NegativeInfinity, warPace = 1, unshackledUntil = double.NegativeInfinity, unshackled = 1;
    double boundUntil = double.NegativeInfinity, boundSaved, cometHung;
    int boundChain;
    (double X, double Z, double R, double Until, HashSet<int> Inside)? henge;

    /// <summary>The leap's reach (far_spring 13 m; a bound of unending_bound 9 m at most).</summary>
    internal double RuleLeapRange(WeaponInst w, double range)
    {
        if (Lamps.Rules.Count == 0) return range;
        range = WkOver(w, "heroic_leap.far_spring", "range", range);
        if (Time <= boundUntil && Wk(w, "heroic_leap.unending_bound")) range = Math.Min(range, Wn("heroic_leap.unending_bound", "range", 9));
        return range;
    }

    /// <summary>Her aim for a leap (into_the_thick: within 4 m of a pack, she lands in its heart).</summary>
    internal (double DX, double DZ, double D) RuleLeapAim(WeaponInst w, double dx, double dz, double d)
    {
        if (!Wk(w, "heroic_leap.into_the_thick") || SkillAim is not { } a) return (dx, dz, d);
        var pack = HostilesInRadius(a.X, a.Z, Wn("heroic_leap.into_the_thick", "snap", 4));
        if (pack.Count < 2) return (dx, dz, d);
        double cx = 0, cz = 0;
        foreach (var e in pack) { cx += e.X; cz += e.Z; }
        cx /= pack.Count; cz /= pack.Count;
        double ex = cx - Player.X, ez = cz - Player.Z, l = Len(ex, ez);
        return l < 0.1 ? (dx, dz, d) : (ex / l, ez / l, l);
    }

    /// <summary>The leap leaves the ground: unshackled breaks every slow and hold on her; a bound is spent.</summary>
    internal void RuleLeapTakeoff(WeaponInst w)
    {
        if (Lamps.Rules.Count == 0) return;
        cometHung = 0;
        if (Time <= boundUntil && Wk(w, "heroic_leap.unending_bound")) { boundChain++; boundUntil = double.NegativeInfinity; }
        else boundChain = 0;
        if (Wk(w, "heroic_leap.unshackled")) { var p = Player; p.SlowT = 0; p.SlowF = 1; p.RootT = 0; }
    }

    /// <summary>The leap's landing numbers: crater (4.5 m, stunned 1.2 s).</summary>
    internal double RuleLeapStun(WeaponInst w, double stun) => WkOver(w, "heroic_leap.crater", "stun", stun);

    /// <summary>iron_comet: the key held, she hangs aloft (untouchable) up to 1.5 s, steering her landing with the cursor
    /// as far as 16 m from where she rose. True while she hangs (UpdatePlayer's leap holds off the landing).</summary>
    internal bool RuleLeapHangs(Leap leap, double dt)
    {
        var w = leap.Weapon;
        if (w == null || !w.Held || !Wk(w, "heroic_leap.iron_comet") || cometHung >= Wn("heroic_leap.iron_comet", "hang", 1.5)) return false;
        cometHung += dt;
        if (SkillAim is { } a)
        {
            double most = Wn("heroic_leap.iron_comet", "range", 16), tx = a.X - leap.X0, tz = a.Z - leap.Z0, l = Len(tx, tz);
            if (l > most) { tx *= most / l; tz *= most / l; }
            tx += leap.X0; tz += leap.Z0;
            double mx = tx - leap.X1, mz = tz - leap.Z1, ml = Len(mx, mz), step = 24 * dt;
            if (ml > step) { mx *= step / ml; mz *= step / ml; }
            leap.X1 += mx; leap.Z1 += mz;
            if (Collision.Blocked(leap.X1, leap.Z1, Player.Radius, includeSoft: false) || InBounds?.Invoke(leap.X1, leap.Z1) == false) { leap.X1 -= mx; leap.Z1 -= mz; }
        }
        Player.X = leap.X1; Player.Z = leap.Z1;
        Player.Iframes = Math.Max(Player.Iframes, 0.05);
        return true;
    }

    /// <summary>The leap lands (LandSkillLeap, after its ring struck): aftershock, ninepins, henge, the kill rules, the
    /// windows after (unshackled, war_pace).</summary>
    internal void RuleLeapLanded(Leap leap, List<Enemy> ring, double dmg)
    {
        var w = leap.Weapon!;
        if (Lamps.Rules.Count == 0) return;
        double x = leap.X1, z = leap.Z1;
        if (Wk(w, "heroic_leap.aftershock"))
            ScheduleHeave(w, x, z, leap.Radius, dmg * Wn("heroic_leap.aftershock", "againDamage", 0.4), Wn("heroic_leap.aftershock", "again", 1));
        if (Wk(w, "heroic_leap.ninepins"))
        {
            double fly = Wn("heroic_leap.ninepins", "throw", 6), share = Wn("heroic_leap.ninepins", "damage", 0.5);
            var hit = new HashSet<int>();
            foreach (var e in ring)
            {
                if (!e.Alive || e.State == EnemyState.Dying || e.Elite || e.Boss) continue;
                Shove(e, x, z, fly);
                foreach (var o in HostilesInRadius(e.X, e.Z, e.Radius + 1))
                    if (o != e && hit.Add(o.Id)) HitEnemy(o, dmg * share, w.School, w.Tags, new HitOpts { Weapon = w, DirX = o.X - x, DirZ = o.Z - z, Knockback = 1 });
            }
        }
        if (Wk(w, "heroic_leap.henge"))
        {
            double r = Wn("heroic_leap.henge", "radius", 6);
            var inside = new HashSet<int>();
            foreach (var e in HostilesInRadius(x, z, r)) if (!e.Elite && !e.Boss) inside.Add(e.Id);
            henge = (x, z, r, Time + Wn("heroic_leap.henge", "seconds", 4), inside);
            Events.Emit(new Ev.Nova { X = x, Z = z, Radius = r, School = School.Physical, Duration = Wn("heroic_leap.henge", "seconds", 4), Rings = 1 });
        }
        int kills = 0;
        foreach (var e in ring) if (!e.Alive || e.State == EnemyState.Dying) kills++;
        if (kills >= (int)Wn("heroic_leap.spring_heeled", "kills", 3) && Wk(w, "heroic_leap.spring_heeled"))
            w.Timer = Math.Max(0, w.Timer - Wn("heroic_leap.spring_heeled", "seconds", 4));
        if (kills >= (int)Wn("heroic_leap.restless", "kills", 5) && Wk(w, "heroic_leap.restless")) w.Timer = 0;
        if (kills > 0 && Wk(w, "heroic_leap.unending_bound") && boundChain + 1 < (int)Wn("heroic_leap.unending_bound", "most", 4) && w.Timer > 0)
        {
            boundSaved = w.Timer;
            w.Timer = 0;
            boundUntil = Time + Wn("heroic_leap.unending_bound", "window", 1.5);
        }
        if (Wk(w, "heroic_leap.unshackled"))
        {
            unshackledUntil = Time + Wn("heroic_leap.unshackled", "seconds", 2);
            unshackled = Wn("heroic_leap.unshackled", "speed", 1.3);
        }
        if (Wk(w, "heroic_leap.war_pace"))
        {
            warPaceUntil = Time + Wn("heroic_leap.war_pace", "seconds", 3);
            warPace = Wn("heroic_leap.war_pace", "speed", 1.25);
        }
    }

    /* ------------------------------------------------------------- the charge -- */

    readonly List<Enemy> riders = new();
    double shieldUpUntil = double.NegativeInfinity, sprungAt = double.NegativeInfinity;
    double stampedeUntil = double.NegativeInfinity, stampedeSaved;
    int stampedeRun;

    /// <summary>A charge begins (SkillCharge): its run's strength (stampede: each run 30% harder than the last).</summary>
    internal double RuleChargeBegin(WeaponInst w)
    {
        riders.Clear();
        if (Lamps.Rules.Count == 0) return 1;
        if (Time <= stampedeUntil && Wk(w, "shield_charge.stampede")) { stampedeRun++; stampedeUntil = double.NegativeInfinity; }
        else stampedeRun = 0;
        return RuleDamageMul(w) * (1 + stampedeRun * (Wk(w, "shield_charge.stampede") ? Wn("shield_charge.stampede", "step", 0.3) : 0));
    }

    /// <summary>breakthrough: no champion stops the charge (a boss still does).</summary>
    internal bool RuleChargeRunsOn(WeaponInst? w, Enemy e) => !e.Boss && Wk(w, "shield_charge.breakthrough");

    internal double RuleChargeStun(WeaponInst? w, double stun) => w != null && Wk(w, "shield_charge.breakthrough") ? Wn("shield_charge.breakthrough", "stun", 1) : stun;

    /// <summary>swept_along: a lesser thing struck rides her shield (8 at most).</summary>
    internal void RuleRide(WeaponInst? w, Enemy e)
    {
        if (w == null || !Wk(w, "shield_charge.swept_along") || riders.Count >= (int)Wn("shield_charge.swept_along", "most", 8)) return;
        if (e.Elite || e.Boss || !e.Alive || e.State == EnemyState.Dying || riders.Contains(e)) return;
        riders.Add(e);
    }

    /// <summary>Each step of the run: what rides her shield is carried before her.</summary>
    internal void RuleCarryRiders()
    {
        if (riders.Count == 0) return;
        var p = Player;
        var a = Art;
        int i = 0;
        foreach (var e in riders)
        {
            if (!e.Alive || e.State == EnemyState.Dying) continue;
            double side = (i % 2 == 0 ? 1 : -1) * Math.Ceiling(i / 2.0) * 0.7, ahead = p.Radius + e.Radius + 0.3;
            e.X = p.X + a.RushDX * ahead + a.RushDZ * side;
            e.Z = p.Z + a.RushDZ * ahead - a.RushDX * side;
            e.Vx = e.Vz = e.Kbx = e.Kbz = 0;
            i++;
        }
    }

    /// <summary>The charge is over (ChargeStep, done): the riders thrown down (or hurled on: landslide), shield_up's
    /// window, stampede's next run.</summary>
    internal void RuleChargeEnd(ChargeRun run, WeaponInst? w)
    {
        if (w == null || Lamps.Rules.Count == 0) { riders.Clear(); return; }
        var p = Player;
        var a = Art;
        double stun = Wn("shield_charge.swept_along", "stun", 1);
        if (riders.Count > 0 && Wk(w, "shield_charge.landslide"))
        {
            double len = Wn("shield_charge.landslide", "length", 10), width = Wn("shield_charge.landslide", "width", 3);
            double x1 = p.X + a.RushDX * len, z1 = p.Z + a.RushDZ * len;
            Events.Emit(new Ev.Beam { X0 = p.X, Z0 = p.Z, X1 = x1, Z1 = z1, Width = width, School = School.Physical, Duration = 0.5, Art = w.Art + "_landslide", Rank = w.Rank });
            var struck = new List<Enemy>();
            ForEachHostileNearSegment(p.X, p.Z, x1, z1, width, e => struck.Add(e));
            foreach (var e in struck)
                HitEnemy(e, run.Damage * Wn("shield_charge.landslide", "damage", 1), School.Physical, run.Tags, new HitOpts { Weapon = w, Knockback = 1, DirX = a.RushDX, DirZ = a.RushDZ });
            int i = 0;
            foreach (var e in riders)
            {
                if (!e.Alive || e.State == EnemyState.Dying) continue;
                double along = len * (0.5 + 0.5 * (i % 3) / 2.0);
                e.X = p.X + a.RushDX * along; e.Z = p.Z + a.RushDZ * along;
                Collision.Resolve(ref e.X, ref e.Z, e.Radius);
                i++;
            }
        }
        foreach (var e in riders) if (e.Alive && e.State != EnemyState.Dying) Stun(e, stun);
        riders.Clear();
        if (Wk(w, "shield_charge.shield_up")) shieldUpUntil = Time + Wn("shield_charge.shield_up", "seconds", 2);
        if (Wk(w, "shield_charge.stampede") && stampedeRun + 1 < (int)Wn("shield_charge.stampede", "runs", 3) && w.Timer > 0)
        {
            stampedeSaved = w.Timer;
            w.Timer = 0;
            stampedeUntil = Time + Wn("shield_charge.stampede", "window", 2);
        }
    }

    /// <summary>shield_up: for 2 s after the charge her shield blocks every blow from in front of her (HurtPlayer).</summary>
    internal bool RuleShieldBlock(double amount, School school, string source, Enemy? from)
    {
        if (Time > shieldUpUntil || from == null) return false;
        var p = Player;
        double fx = Math.Sin(p.Facing), fz = Math.Cos(p.Facing), dx = from.X - p.X, dz = from.Z - p.Z, d = Len(dx, dz);
        double half = Wn("shield_charge.shield_up", "arc", 180) * Math.PI / 360;
        if (d > 0.01 && Math.Acos(Math.Clamp((dx * fx + dz * fz) / d, -1, 1)) > half) return false;
        p.Iframes = Math.Max(p.Iframes, 0.05);
        Events.Emit(new Ev.PlayerHit { X = p.X, Z = p.Z, Amount = 0, School = school, Source = source, Blocked = true });
        Fire(TriggerEvent.Block, new ProcCtx { X = p.X, Z = p.Z });
        OnBlocked(amount, from);
        return true;
    }

    /// <summary>A block (OnBlocked): rebound (1 s off the charge's wait), nothing_wasted (the brace stores all of it).</summary>
    internal void RuleOnBlocked(double amount)
    {
        if (Lamps.Rules.Count == 0) return;
        if (WeaponById("shield_charge") is { } c && Wk(c, "shield_charge.rebound")) c.Timer = Math.Max(0, c.Timer - Wn("shield_charge.rebound", "seconds", 1));
        if (Braced is { } v && Wk(v.Weapon, "iron_vow.nothing_wasted")) v.Stored += amount * Wn("iron_vow.nothing_wasted", "store", 1);
    }

    /// <summary>A perfect dash (LampsOnPerfect): sprung readies the charge at once, as often as every 3 s.</summary>
    internal void RuleOnPerfect()
    {
        if (Lamps.Rules.Count == 0 || WeaponById("shield_charge") is not { } c || !Wk(c, "shield_charge.sprung")) return;
        if (Time < sprungAt + Wn("shield_charge.sprung", "gap", 3)) return;
        sprungAt = Time;
        c.Timer = 0;
    }

    /* -------------------------------------------------------------- the vow -- */

    readonly Dictionary<int, double> goaded = new();
    readonly HashSet<int> marched = new();

    /// <summary>The vow's numbers: kept_count (stores 35%), anvil (cut by 70%), steadfast (3.5 s), old_grudge (5 times).</summary>
    internal double RuleVowStore(WeaponInst w, double store) => WkOver(w, "iron_vow.kept_count", "store", store);
    internal double RuleVowHalve(WeaponInst w, double halve) => Wk(w, "iron_vow.anvil") ? 1 - Wn("iron_vow.anvil", "cut", 0.7) : halve;
    internal double RuleVowRadius(WeaponInst w, double r) => WkOver(w, "iron_vow.come_then", "burst", r);

    /// <summary>iron_march: she walks the brace at full speed, her feet never planted.</summary>
    internal bool RuleMarch => Braced is { } v && Wk(v.Weapon, "iron_vow.iron_march");

    /// <summary>The brace begins (SkillBrace): come_then (everything within 12 m drops what it was doing and rushes her).</summary>
    internal void RuleBraceBegin(WeaponInst w, double seconds)
    {
        marched.Clear();
        if (!Wk(w, "iron_vow.come_then")) return;
        var p = Player;
        foreach (var e in HostilesInRadius(p.X, p.Z, Wn("iron_vow.come_then", "radius", 12)))
        {
            if (e.Boss) continue;
            goaded[e.Id] = Time + seconds;
            e.Target = -1;
            Interrupt(e);
        }
    }

    /// <summary>The AI's want (Ai): a goaded thing rushes her, an archer or a caster too.</summary>
    internal bool RuleGoaded(Enemy e) => goaded.Count > 0 && goaded.TryGetValue(e.Id, out var t) && Time < t;

    /// <summary>A blow on her in the brace (VowTake): like_for_like strikes its striker back for half of it.</summary>
    internal void RuleVowBlow(WeaponInst w, double dmg, Enemy? from)
    {
        if (from is not { Alive: true } || from.State == EnemyState.Dying || !Wk(w, "iron_vow.like_for_like")) return;
        var (was, hb) = (credit, HeavyBy);
        credit = w.Id; HeavyBy = null;
        HitEnemy(from, dmg * Wn("iron_vow.like_for_like", "share", 0.5), w.School, w.Tags, new HitOpts { Weapon = w, NoProcs = true });
        (credit, HeavyBy) = (was, hb);
    }

    /// <summary>unyielding: the key held, the brace holds on (6 s at most); let go, it bursts. True while it holds.</summary>
    internal bool RuleBraceHolds(BraceRun v, double dt)
    {
        var w = v.Weapon;
        if (w.Held) v.HeldT += dt;
        if (!Wk(w, "iron_vow.unyielding")) return false;
        v.Age += dt;
        return w.Held && v.Age < Wn("iron_vow.unyielding", "most", 6);
    }

    /// <summary>The vow bursts (TickVow): unyielding's reach (1 m more a second held), full_measure (a shockwave toward the
    /// cursor, 14 m by 3 m, at twice the ring's blow: true, the ring is not struck), penance (mends a third of the store).</summary>
    internal double RuleBurstRadius(BraceRun v, double r) =>
        Wk(v.Weapon, "iron_vow.unyielding") ? Math.Max(r, Wn("iron_vow.unyielding", "radius", 5)) + v.HeldT * Wn("iron_vow.unyielding", "perSecond", 1) : r;

    internal bool RuleBurstWave(BraceRun v, double dmg)
    {
        var w = v.Weapon;
        var p = Player;
        if (Wk(w, "iron_vow.penance"))
            HealPlayer(Math.Min(v.Stored * Wn("iron_vow.penance", "mend", 1.0 / 3), MaxHp * Wn("iron_vow.penance", "most", 0.15)), "iron_vow");
        if (!Wk(w, "iron_vow.full_measure")) return false;
        var (dx, dz, _) = SkillDir(1);
        double len = Wn("iron_vow.full_measure", "length", 14), width = Wn("iron_vow.full_measure", "width", 3);
        double x1 = p.X + dx * len, z1 = p.Z + dz * len, blow = dmg * Wn("iron_vow.full_measure", "damage", 2);
        Events.Emit(new Ev.Beam { X0 = p.X, Z0 = p.Z, X1 = x1, Z1 = z1, Width = width, School = w.School, Duration = 0.45, Art = w.Art + "_wave", Rank = w.Rank });
        var struck = new List<Enemy>();
        ForEachHostileNearSegment(p.X, p.Z, x1, z1, width, e => struck.Add(e));
        var (hb, was) = (HeavyBy, credit);
        HeavyBy = v.Heavy ? w : null;
        credit = w.Id;
        VowStruck.Clear();
        foreach (var e in struck)
        {
            VowStruck.Add(e.Id);
            double side = (e.X - p.X) * dz - (e.Z - p.Z) * dx;
            double sx = side >= 0 ? dz : -dz, sz = side >= 0 ? -dx : dx;
            HitEnemy(e, blow, w.School, w.Tags, new HitOpts { Weapon = w, Knockback = 2.2, DirX = sx * 0.85 + dx * 0.4, DirZ = sz * 0.85 + dz * 0.4, Status = Firing.StatusWith(this, w), BossDamage = w.Def.BossDamage });
        }
        (HeavyBy, credit) = (hb, was);
        Events.Emit(new Ev.Shake { Amount = 0.5 });
        return true;
    }

    /* ---------------------------------------------------------- the clock -- */

    /// <summary>Her pace (UpdatePlayer): unshackled's 30% faster after a landing; iron_march's full speed in the brace.</summary>
    internal double RuleMoveMul()
    {
        if (Lamps.Rules.Count == 0) return 1;
        double m = Time < unshackledUntil ? unshackled : 1;
        if (RuleMarch && Player.CastT > 0 && Player.CastWalk > 0.05) m /= Player.CastWalk;
        return m;
    }

    /// <summary>Each step (TickVow): the cross cuts owed, the henge's walls, the bound's and stampede's windows lapsing,
    /// iron_march's shove.</summary>
    void TickRules(double dt)
    {
        if (Lamps.Rules.Count == 0) return;
        for (int i = crossCuts.Count - 1; i >= 0; i--)
        {
            var c = crossCuts[i];
            if (Time < c.At) continue;
            crossCuts.RemoveAt(i);
            if (Weapons.Contains(c.W)) Firing.CrossCut(this, c.W, c.A + Math.PI / 24, c.Arc, c.Reach);
        }
        if (boundUntil > double.NegativeInfinity && Time > boundUntil)
        {
            boundUntil = double.NegativeInfinity;
            if (WeaponById("heroic_leap") is { } l && l.Timer <= 0) l.Timer = Math.Max(0, boundSaved - Wn("heroic_leap.unending_bound", "window", 1.5));
        }
        if (stampedeUntil > double.NegativeInfinity && Time > stampedeUntil)
        {
            stampedeUntil = double.NegativeInfinity;
            if (WeaponById("shield_charge") is { } c && c.Timer <= 0) c.Timer = Math.Max(0, stampedeSaved - Wn("shield_charge.stampede", "window", 2));
        }
        if (henge is { } h)
        {
            if (Time > h.Until) henge = null;
            else
                foreach (var e in Enemies.Items)
                {
                    if (!e.Alive || e.State == EnemyState.Dying || e.Boss) continue;
                    double dx = e.X - h.X, dz = e.Z - h.Z, d = Len(dx, dz);
                    if (d < 0.01) continue;
                    if (h.Inside.Contains(e.Id)) { double most = h.R - e.Radius; if (d > most) { e.X = h.X + dx / d * most; e.Z = h.Z + dz / d * most; } }
                    else { double least = h.R + e.Radius; if (d < least) { e.X = h.X + dx / d * least; e.Z = h.Z + dz / d * least; } }
                }
        }
        if (goaded.Count > 0 && Braced == null) goaded.Clear();
        if (RuleMarch && Braced is { } v)
        {
            var p = Player;
            if (Len(p.Vx, p.Vz) > 0.5)
                foreach (var e in HostilesInRadius(p.X, p.Z, p.Radius + 0.9))
                {
                    if (e.Elite || e.Boss || !marched.Add(e.Id)) continue;
                    double vl = Len(p.Vx, p.Vz), sx = -p.Vz / vl, sz = p.Vx / vl;
                    if ((e.X - p.X) * sx + (e.Z - p.Z) * sz < 0) { sx = -sx; sz = -sz; }
                    e.X += sx * Wn("iron_vow.iron_march", "shove", 2);
                    e.Z += sz * Wn("iron_vow.iron_march", "shove", 2);
                    Collision.Resolve(ref e.X, ref e.Z, e.Radius);
                }
        }
    }

    /* ---------------------------------------------------------- helpers -- */

    /// <summary>Move a creature d metres along the line from (fx, fz) through it (negative: toward (fx, fz), never past
    /// her reach of it), stopped by walls.</summary>
    void Shove(Enemy e, double fx, double fz, double d)
    {
        double dx = e.X - fx, dz = e.Z - fz, l = Len(dx, dz);
        if (l < 0.01) { dx = Math.Sin(Player.Facing); dz = Math.Cos(Player.Facing); l = 1; }
        double to = Math.Max(Player.Radius + e.Radius + 0.1, l + d);
        e.X = fx + dx / l * to;
        e.Z = fz + dz / l * to;
        e.Kbx = e.Kbz = 0;
        Collision.Resolve(ref e.X, ref e.Z, e.Radius);
    }

    void Stun(Enemy e, double seconds)
    {
        if (seconds <= 0 || !e.Alive || e.State == EnemyState.Dying) return;
        ApplyStatus(e, new StatusPayload(StatusKind.Stun, 1, 1, seconds), 0);
        Interrupt(e);
    }
}

public static partial class Firing
{
    /// <summary>cross_cut's cut back across her front (Battle.TickRules): the chop's cone at its share.</summary>
    internal static void CrossCut(Battle b, WeaponInst w, double a, double arc, double reach)
    {
        var hb = b.HeavyBy;
        b.HeavyBy = null;
        b.RuleChopBegin(w);
        ConeHit(b, w, a, arc, reach, w.Damage * b.RuleCutMul(w));
        b.HeavyBy = hb;
    }
}

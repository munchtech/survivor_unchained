using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Sim;

/* The warden's own calling skills (docs/design/CLASS_IDENTITY_AND_TALENTS.md 1, the Warden table; CLASSES.md's skill
 * table): Sunder's heavy line, Groundbreaker's crack and heave. Their lamps (lamps.json, rule ids "<skill>.<rule>")
 * are rules with fixed numbers, read through SkillRule / SkillFull: kept in full by night, as a price or a shape is.
 * A new behavior is a Fire* here, dispatched from Firing.Fire, plus what the Battle does for it below. */
public static partial class Firing
{
    /// <summary>Its own heavy count, every this many firings (0: none): the skill's HeavyEvery, its lamp's every 3rd
    /// (third_blow), a Turn's (Splitting Stroke); the shortest wins.</summary>
    public static int HeavyEveryOf(Battle b, WeaponInst w)
    {
        int n = (int)(w.Num(s => s.HeavyEvery) ?? 0);
        static int Min(int a, int c) => a > 0 ? Math.Min(a, c) : c;
        if (n > 0 && b.SkillRule(w, "third_blow")) n = Min(n, (int)b.SkillFull(w, "third_blow", "every", 3));
        if (w.Wick is { HeavyEvery: > 0 } fx) n = Min(n, fx.HeavyEvery);
        if (b.Wk(w, "cleaver.overhand")) n = Min(n, (int)b.Wn("cleaver.overhand", "every", 3));
        return n;
    }

    /// <summary>Sunder's line: a heavy swing splits the ground straight ahead, each creature on it struck once at the
    /// swing's full damage (heavy too: the firing's HeavyBy is this skill). burning_edge: it sears.</summary>
    static void HeavyLine(Battle b, WeaponInst w, double x, double z, double a, double length)
    {
        double len = AreaOf(b, w, length), width = AreaOf(b, w, w.Num(s => s.BeamWidth) ?? 1.2);
        double x1 = x + Math.Cos(a) * len, z1 = z + Math.Sin(a) * len;
        b.Events.Emit(new Ev.Beam { X0 = x, Z0 = z, X1 = x1, Z1 = z1, Width = width, School = w.School, Duration = 0.4, Art = w.Art + "_line", Rank = w.Rank });
        var status = b.SkillRule(w, "burning_edge") ? Battle.SearEdge : StatusWith(b, w);
        double dmg = w.Damage, kb = w.Num(s => s.Knockback) ?? 0, dx = Math.Cos(a), dz = Math.Sin(a);
        b.ForEachHostileNearSegment(x, z, x1, z1, width, e =>
            b.HitEnemy(e, dmg, w.School, w.Tags, new HitOpts { Weapon = w, Knockback = kb, DirX = dx, DirZ = dz, Status = status, BossDamage = w.Def.BossDamage }));
        b.LinesStruck++;
    }

    /// <summary>Groundbreaker: a crack runs from her to the densest pack's center within its range (fault_line: 14 m)
    /// and the ground heaves where it ends (twin: two cracks, splayed either side). Strikes at once.</summary>
    static bool FireCrack(Battle b, WeaponInst w)
    {
        var p = At(b);
        double range = w.Num(s => s.Range) ?? 10;
        if (b.SkillRule(w, "fault_line")) range = Math.Max(range, b.SkillFull(w, "fault_line", "reach", 14));
        // A campaign press: the crack runs to the pack under the cursor (the hover foe's), else to the point.
        var t = b.CastAt is { } ca ? ca.Foe : b.DensestHostile(p.X, p.Z, range, 2.5);
        if (t == null && b.CastAt == null) return false;
        double cx = 0, cz = 0;
        if (t != null)
        {
            // The pack's center: the middle of what stands round the densest one.
            var pack = b.HostilesInRadius(t.X, t.Z, 2.5);
            foreach (var e in pack) { cx += e.X; cz += e.Z; }
            if (pack.Count > 0) { cx /= pack.Count; cz /= pack.Count; } else { cx = t.X; cz = t.Z; }
        }
        else (cx, cz) = (b.CastAt!.Value.X, b.CastAt.Value.Z);
        double d = Dist(cx, cz, p.X, p.Z);
        double a = d > 0.01 ? Math.Atan2(cz - p.Z, cx - p.X) : t != null ? Math.Atan2(t.Z - p.Z, t.X - p.X) : Math.Atan2(Math.Cos(b.Player.Facing), Math.Sin(b.Player.Facing));
        double len = Math.Clamp(d, 1.5, range);
        if (b.SkillRule(w, "twin"))
        {
            double splay = b.SkillFull(w, "twin", "splay", Math.PI / 6);
            CrackOne(b, w, p.X, p.Z, a - splay, len);
            CrackOne(b, w, p.X, p.Z, a + splay, len);
        }
        else CrackOne(b, w, p.X, p.Z, a, len);
        if (!b.Refiring && !b.Landing) b.Player.AttackAnim = new AttackAnim(w.Id, a, b.Time, true);
        return true;
    }

    /// <summary>Rebuke never fires on its timer (Firing.Tick passes it by): a blow that reaches her strikes it (Battle.RebukeOnBlow).
    /// An On-kill echo is a strike centered on the corpse, the three nearest it.</summary>
    static bool FireReactive(Battle b, WeaponInst w) => b.FireFrom is { } o && b.RebukeStrike(w, o.X, o.Z, null);

    /// <summary>The Watch Bell: a toll when anything is in its reach (loud: 10 m), drawing what isn't a boss to her.</summary>
    static bool FireToll(Battle b, WeaponInst w)
    {
        var p = At(b);
        double r = b.BellReach(w);
        if (b.NearestHostile(p.X, p.Z, r) == null) return false;
        b.Toll(w, p.X, p.Z, r);
        return true;
    }

    /// <summary>Oath and Bell's toll, owed by a stagger: rung now, not a cast (no Hand blow), its own timer untouched.</summary>
    internal static bool TollNow(Battle b, WeaponInst w) => FireToll(b, w);

    static void CrackOne(Battle b, WeaponInst w, double x0, double z0, double a, double len)
    {
        double x1 = x0 + Math.Cos(a) * len, z1 = z0 + Math.Sin(a) * len;
        double width = AreaOf(b, w, w.Num(s => s.BeamWidth) ?? 1.2), r = AreaOf(b, w, w.Num(s => s.Radius) ?? 2.5);
        b.Events.Emit(new Ev.Beam { X0 = x0, Z0 = z0, X1 = x1, Z1 = z1, Width = width, School = w.School, Duration = 0.35, Art = w.Art + "_crack", Rank = w.Rank });
        double dmg = w.Damage, trail = dmg * (w.Num(s => s.Trail) ?? 0.5);
        // Along the crack, at the trail's share; what stands where it heaves is the heave's.
        b.ForEachHostileNearSegment(x0, z0, x1, z1, width, e =>
        {
            if (Dist(e.X, e.Z, x1, z1) <= r + e.Radius) return;
            b.HitEnemy(e, trail, w.School, w.Tags, new HitOpts { Weapon = w, BossDamage = w.Def.BossDamage, Status = StatusWith(b, w) });
        });
        b.Heave(w, x1, z1, r, dmg);
        // Aftershock: the same spot heaves again.
        if (w.Wick is { Again: > 0 } fx) b.ScheduleHeave(w, x1, z1, r, dmg * fx.AgainDamage, fx.Again);
        // Linger: the heave leaves its ground.
        if (w.Wick?.Ground is { } g)
        {
            var zn = b.SpawnZone(Side.Player, x1, z1, AreaOf(b, w, g.Radius), DurationOf(b, w, g.Duration), dmg * g.DpsPct, w.School);
            if (zn != null) { zn.Tags = w.Tags; zn.Art = w.Art + "_ground"; zn.Weapon = w.Id; }
        }
    }
}

public sealed partial class Battle
{
    /// <summary>Sunder's burning_edge: the holy Turn's sear, on its heavy line.</summary>
    internal static readonly StatusPayload SearEdge = new(StatusKind.Sear, 1, 0.5, 1);
    /// <summary>Counters for measurement and tests: heavy lines struck, heaves.</summary>
    public int LinesStruck, Heaves;

    /// <summary>A skill's own lamp rule is lit ("sunder.third_blow": its id, a dot, the rule).</summary>
    internal bool SkillRule(WeaponInst w, string rule) => Lamps.Rules.Count > 0 && Lamps.Has(w.Def.Id + "." + rule);

    /// <summary>A skill's own rule's fixed number (kept in full by night), its fallback when the lamp gives none.</summary>
    internal double SkillFull(WeaponInst w, string rule, string arg, double fallback) => Lamps.Full(w.Def.Id + "." + rule, arg, fallback);

    /// <summary>still_reach: standing still, the swing reaches further (a multiplier on its reach).</summary>
    internal double SkillStillReach(WeaponInst w) =>
        Player.StillT > 0.25 && SkillRule(w, "still_reach") ? 1 + SkillFull(w, "still_reach", "inc", 0.1) : 1;

    /// <summary>wide_swing: the arc is 300°.</summary>
    internal double SkillArc(WeaponInst w, double arc) =>
        SkillRule(w, "wide_swing") ? Math.Max(arc, SkillFull(w, "wide_swing", "arc", 300 * Math.PI / 180)) : arc;

    /// <summary>The ground heaves (Groundbreaker's crack's end, and its Aftershock): everything in it struck heavy, and
    /// stunned (not a boss: the Hand's stagger is a boss's); upheaval: a lesser thing is thrown up, unable to move or
    /// strike, and takes more while it is.</summary>
    internal void Heave(WeaponInst w, double x, double z, double r, double dmg)
    {
        Heaves++;
        Events.Emit(new Ev.Explosion { X = x, Z = z, Radius = r, School = w.School, Power = Math.Min(2, dmg / 40), Art = w.Art + "_heave", Rank = w.Rank });
        double stun = w.Num(s => s.Stun) ?? 0.6, kb = w.Num(s => s.Knockback) ?? 0;
        bool up = SkillRule(w, "upheaval");
        double air = up ? SkillFull(w, "upheaval", "seconds", 0.8) : 0, more = up ? SkillFull(w, "upheaval", "more", 0.3) : 0;
        var status = Firing.StatusWith(this, w);
        ForEachHostileInRadius(x, z, r, (e, d) =>
        {
            double dd = d == 0 ? 1 : d;
            HitEnemy(e, dmg, w.School, w.Tags, new HitOpts { Weapon = w, Heavy = true, Knockback = kb, DirX = (e.X - x) / dd, DirZ = (e.Z - z) / dd, Status = status, BossDamage = w.Def.BossDamage });
            if (e.Boss || !e.Alive || e.State == EnemyState.Dying) return;
            double hold = stun;
            if (up && !e.Elite) { e.AirUntil = Time + air; e.AirMore = more; hold = Math.Max(hold, air); }
            if (hold <= 0) return;
            var s = e.Status.Ensure(StatusKind.Stun, 0, 1, 0, 0);
            s.T = Math.Max(s.T, hold);
        });
        foreach (var c in Collision.Within(x, z, r)) if (c.Tag != null) Hooks.OnHitProp?.Invoke(c.Tag, c.Id, w.School, dmg, x, z);
    }

    /* ------------------------------------------------------------ Rebuke -- */

    /// <summary>Counters for measurement and tests: Rebuke's strikes, the bell's tolls, the barrier the bell gave.</summary>
    public int RebukeStrikes, Tolls;
    public double BellBarrier;
    /// <summary>Oath and Bell: a stagger owes the bell a toll (rung on the bell's next tick, never inside a hit).</summary>
    internal bool BellOwed;
    double bellOathAt = -99, answeredAt = -99, rebukeAt = -99;

    /// <summary>Rebuke carried: her block chance (its Block at rank 1, BlockStep more a rank).</summary>
    double RebukeBlock() =>
        WeaponById("rebuke") is { DisabledT: <= 0 } w ? (w.Num(s => s.Block) ?? 0.08) + (w.Num(s => s.BlockStep) ?? 0.01) * (w.Rank - 1) : 0;

    /// <summary>A blow that reaches her, blocked (lamp's or the Warding light's) or not: Rebuke strikes the one who struck
    /// if it stands within reach of her, and the three nearest it; a missile's (no striker near), the three nearest her.
    /// At most once in its cooldown (0.5 s, shortened as any cooldown is): from blocks alone it struck twice a minute,
    /// 0.3-0.8% of her night (P6b).</summary>
    /// <summary>A riposte: Rebuke answers the blow it took at once, whatever its gap.</summary>
    void RebukeAnswerNow() => rebukeAt = double.NegativeInfinity;

    void RebukeOnBlow(Enemy? from)
    {
        if (WeaponById("rebuke") is not { DisabledT: <= 0 } w) return;
        if (Time < rebukeAt + Firing.CooldownOf(this, w)) return;
        rebukeAt = Time;
        var p = Player;
        double reach = w.Num(s => s.Range) ?? 6;
        w.Casts++;
        if (from is { Alive: true } f && f.State != EnemyState.Dying && Dist(f.X, f.Z, p.X, p.Z) <= reach + f.Radius) RebukeStrike(w, f.X, f.Z, f);
        else RebukeStrike(w, p.X, p.Z, null);
    }

    /// <summary>Rebuke's strike: the blocker and the creatures nearest (x, z) within its radius, holy, thrown back from her;
    /// Shield of Morning leaves her a barrier for each. False when nothing was there to strike.</summary>
    internal bool RebukeStrike(WeaponInst w, double x, double z, Enemy? blocker)
    {
        var p = Player;
        double r = Firing.AreaOf(this, w, w.Num(s => s.Radius) ?? 5);
        int others = (int)(w.Num(s => s.Others) ?? 5);
        // A champion is struck again only after its gap: pinned by one, she isn't a turret that fires at it twice a second.
        double gap = w.Num(s => s.ChampionGap) ?? 0;
        bool Ready(Enemy e) => !(e.Elite || e.Boss) || Time >= e.RebukedAt + gap;
        var struck = new List<Enemy>(others + 1);
        if (blocker != null && Ready(blocker)) struck.Add(blocker);
        struck.AddRange(HostilesInRadius(x, z, r).Where(e => e != blocker && e.Alive && e.State != EnemyState.Dying && Ready(e))
            .OrderBy(e => Dist(e.X, e.Z, x, z)).Take(others));
        if (struck.Count == 0) return false;
        RebukeStrikes++;
        Events.Emit(new Ev.Nova { X = x, Z = z, Radius = r, School = w.School, Duration = 0.25, Rings = 1, Art = w.Art, Rank = w.Rank });
        double kb = w.Num(s => s.Knockback) ?? 0.6;
        var status = Firing.StatusWith(this, w);
        foreach (var e in struck)
        {
            if (!e.Alive || e.State == EnemyState.Dying) continue;
            if (e.Elite || e.Boss) e.RebukedAt = Time;
            double d = Dist(e.X, e.Z, p.X, p.Z), dd = d < 1e-6 ? 1 : d;
            HitEnemy(e, w.Damage * RebukeChampionMul(e), w.School, w.Tags, new HitOpts { Weapon = w, Knockback = kb, DirX = (e.X - p.X) / dd, DirZ = (e.Z - p.Z) / dd, Status = status, BossDamage = w.Def.BossDamage });
        }
        // Shield of Morning: a barrier for each creature struck. Added to a barrier she holds without renewing its time
        // (renewed, eight strikes a minute kept the bell's and every other barrier up for good: P 1.43-1.63, P6c).
        if (w.Wick is { BarrierEach: > 0 } fx)
        {
            double add = MaxHp * Math.Min(fx.BarrierMost > 0 ? fx.BarrierMost : 1, fx.BarrierEach * struck.Count);
            double before = Math.Max(0, p.Shield);
            if (p.Shield > 0 && p.ShieldT > 0) p.Shield = Math.Min(MaxHp, p.Shield + StonesBarrier(add));
            else Barrier(add, 6);
            if (p.Shield - before > 0) Events.Emit(new Ev.Barrier { X = p.X, Z = p.Z, Amount = p.Shield - before, Source = w.Def.Id });
        }
        RebukeMends();
        return true;
    }

    /// <summary>Rebukes (the skill's strikes and the wall's answer) on a champion: rebuke.champions (elite or boss) and
    /// rebuke.strong (twice as hard on an elite, not a boss), multiplied.</summary>
    double RebukeChampionMul(Enemy e)
    {
        double m = e.Elite || e.Boss ? 1 + Lamps.Size("rebuke.champions", "more") : 1;
        if (e.Elite && !e.Boss && Lamps.Has("rebuke.strong")) m *= Lamps.Full("rebuke.strong", "mul", 2);
        return m;
    }

    /// <summary>rebuke.answering: each rebuke (a block's strike, a wall's answer) mends a sliver, at most every half second.</summary>
    void RebukeMends()
    {
        if (!Lamps.Has("rebuke.answering") || Time < answeredAt + Lamps.Full("rebuke.answering", "gap", 0.5)) return;
        answeredAt = Time;
        HealPlayer(MaxHp * Lamps.Full("rebuke.answering", "share", 0.01), "rebuke");
    }

    /* -------------------------------------------------------- Watch Bell -- */

    /// <summary>The bell's reach: its Range (loud: 10 m), grown as an area is.</summary>
    internal double BellReach(WeaponInst w)
    {
        double r = w.Num(s => s.Range) ?? 8;
        if (SkillRule(w, "loud")) r = Math.Max(r, SkillFull(w, "loud", "reach", 10));
        return Firing.AreaOf(this, w, r);
    }

    /// <summary>A toll: everything in reach that isn't a boss is drawn to her (a slide that ends about 1.2 m off; iron: held
    /// slower a while), everything in reach is struck, and each thing drawn gives her a barrier (bell_and_barrier: more),
    /// at most DrawMost of them. Stone Bell: Stones, and more for each champion drawn.</summary>
    internal void Toll(WeaponInst w, double x, double z, double r)
    {
        Tolls++;
        Events.Emit(new Ev.Nova { X = x, Z = z, Radius = r, School = w.School, Duration = 0.35, Rings = 2, Art = w.Art, Rank = w.Rank });
        bool iron = SkillRule(w, "iron");
        double slow = iron ? SkillFull(w, "iron", "slow", 0.3) : 0, held = iron ? SkillFull(w, "iron", "seconds", 2.5) : 0;
        double stop = w.Num(s => s.Reach) ?? 1.2;
        var status = Firing.StatusWith(this, w);
        int drawn = 0, champions = 0;
        foreach (var e in HostilesInRadius(x, z, r))
        {
            if (!e.Alive || e.State == EnemyState.Dying) continue;
            if (!e.Boss)
            {
                drawn++;
                if (e.Elite) champions++;
                // Drawn: the wall's answer doesn't throw it back for a while (Stone Bell's stones mustn't undo the draw).
                e.DrawnAt = Time;
                double kx = x - e.X, kz = z - e.Z, kd = Math.Sqrt(kx * kx + kz * kz);
                // The draw: a slide to her (knockback settles at 9 a second, so v = 9 x the distance), as Drag Them Under hauls.
                if (kd > 1e-6 && e.Def.Behavior != Behavior.Stationary)
                {
                    double pull = Math.Max(0, kd - stop - e.Radius);
                    e.Kbx = kx / kd * pull * 9;
                    e.Kbz = kz / kd * pull * 9;
                }
                if (iron) { e.SlowUntil = Math.Max(e.SlowUntil, Time + held); e.SlowBy = Math.Max(e.SlowBy, slow); }
            }
            double m = e.Elite || e.Boss ? 1 + Lamps.Size("rebuke.champions", "more") : 1;
            HitEnemy(e, w.Damage * m, w.School, w.Tags, new HitOpts { Weapon = w, Status = status, BossDamage = w.Def.BossDamage });
        }
        if (drawn > 0)
        {
            double share = SkillRule(w, "barrier") ? SkillFull(w, "barrier", "share", 0.015) : w.Num(s => s.Barrier) ?? 0.01;
            // A Pulse's tolls are smaller: each one's barrier scaled as its damage is.
            if (w.Wick is { Pulses: > 1 } pw)
                foreach (var t in pw.Turns) if (Content.Wicks.Turn(t) is { Pulses: > 1 } pt) share *= pt.Damage;
            // It tops her barrier up toward a ceiling (15% of health held; the lamp doesn't raise it), never past it;
            // barrier from elsewhere is untouched (at 5% a toll and 17 tolls a minute it gave 72-77% of health a minute).
            double amount = StonesBarrier(MaxHp * share * Math.Min(drawn, (int)(w.Num(s => s.DrawMost) ?? 5)));
            amount = Math.Min(amount, Math.Max(0, MaxHp * (w.Num(s => s.BarrierCap) ?? 0.15) - Math.Max(0, Player.Shield)));
            if (amount > 0)
            {
                BellBarrier += amount;
                Player.Shield = Math.Max(Player.Shield, 0) + amount;
                Player.ShieldT = Math.Max(Player.ShieldT, 6);
                Events.Emit(new Ev.Barrier { X = Player.X, Z = Player.Z, Amount = amount, Source = w.Def.Id });
            }
        }
        // Stone Bell: the toll lays stones on the wall (the Hand's wall, Shield Arm or not).
        if (w.Wick is { } fx && (fx.Stones > 0 || fx.StonesChampion > 0))
            for (int i = fx.Stones + fx.StonesChampion * champions; i > 0; i--) AddStone(true);
    }

    /// <summary>Oath and Bell: a stagger (a heavy blow landing) owes the bell a toll, at most every few seconds.</summary>
    void BellOnStagger()
    {
        if (BellOwed || Time < bellOathAt || !Lamps.Has("oath_and_bell") || WeaponById("watch_bell") == null) return;
        BellOwed = true;
    }

    /// <summary>The owed toll rung (Firing.Tick, the bell's): if anything is in reach; the gap starts only if it rang.</summary>
    internal void TollOwed(WeaponInst w)
    {
        BellOwed = false;
        if (Firing.TollNow(this, w)) bellOathAt = Time + Lamps.Full("oath_and_bell", "every", 3);
    }

    /// <summary>A heave owed later at the same spot (Aftershock), shown as a strike marked on the ground.</summary>
    internal void ScheduleHeave(WeaponInst w, double x, double z, double r, double dmg, double delay)
    {
        strikes.Add(new StrikeSpec(x, z, r, dmg, w.School, w.Tags, delay, w, Side.Player, 0) { Credit = credit, Echo = Echoing, Heave = true });
        Events.Emit(new Ev.Strike { X = x, Z = z, Radius = r, School = w.School, Delay = delay, Art = w.Art, Rank = w.Rank });
    }
}

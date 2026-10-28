using System;
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
        var t = b.DensestHostile(p.X, p.Z, range, 2.5);
        if (t == null) return false;
        // The pack's center: the middle of what stands round the densest one.
        double cx = 0, cz = 0;
        var pack = b.HostilesInRadius(t.X, t.Z, 2.5);
        foreach (var e in pack) { cx += e.X; cz += e.Z; }
        if (pack.Count > 0) { cx /= pack.Count; cz /= pack.Count; } else { cx = t.X; cz = t.Z; }
        double d = Dist(cx, cz, p.X, p.Z);
        double a = d > 0.01 ? Math.Atan2(cz - p.Z, cx - p.X) : Math.Atan2(t.Z - p.Z, t.X - p.X);
        double len = Math.Clamp(d, 1.5, range);
        if (b.SkillRule(w, "twin"))
        {
            double splay = b.SkillFull(w, "twin", "splay", Math.PI / 6);
            CrackOne(b, w, p.X, p.Z, a - splay, len);
            CrackOne(b, w, p.X, p.Z, a + splay, len);
        }
        else CrackOne(b, w, p.X, p.Z, a, len);
        if (!b.Refiring) b.Player.AttackAnim = new AttackAnim(w.Id, a, b.Time, true);
        return true;
    }

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

    /// <summary>A heave owed later at the same spot (Aftershock), shown as a strike marked on the ground.</summary>
    internal void ScheduleHeave(WeaponInst w, double x, double z, double r, double dmg, double delay)
    {
        strikes.Add(new StrikeSpec(x, z, r, dmg, w.School, w.Tags, delay, w, Side.Player, 0) { Credit = credit, Echo = Echoing, Heave = true });
        Events.Emit(new Ev.Strike { X = x, Z = z, Radius = r, School = w.School, Delay = delay, Art = w.Art, Rank = w.Rank });
    }
}

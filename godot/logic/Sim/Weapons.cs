using System;
using System.Collections.Generic;
using SurvivorUnchained.Content;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Sim;

/// <summary>Mods from discoveries and items: multipliers and additions.</summary>
public sealed class WeaponMods
{
    public double Damage = 1, Area = 1, Cooldown = 1, Speed = 1, Duration = 1, Homing;
    public int Projectiles, Pierce;
}

/// <summary>
/// A weapon in the hand: its definition, how far it has been ranked, what it
/// evolved into, and the behaviour that turns all of that into things on the
/// field. Nothing here aims or fires on input - the survivor's whole job is
/// where they stand.
/// </summary>
public sealed class WeaponInst
{
    public readonly string Id;
    public readonly WeaponDef Def;
    public int Rank;
    Evolution? evolution;
    public double Timer;
    public readonly WeaponMods Mods = new();
    /// <summary>Burst shots still to go, and when.</summary>
    public int BurstLeft;
    public double BurstT;
    public int BurstTarget = -2;
    /// <summary>Statistics for the damage meter and for mastery.</summary>
    public double DamageDealt;
    public int Kills;
    public int Slot;
    /// <summary>For beams and orbits: active until.</summary>
    public double ActiveT;
    /// <summary>Times it has been honed (finished, in the endless dark).</summary>
    public int Honed;
    public int Swing;
    Tag[]? tags;

    public WeaponInst(string id, int rank, int slot)
    {
        Id = id;
        Def = Content.Weapons.Get(id);
        Rank = rank;
        Slot = slot;
        Timer = 0.4 + slot * 0.17;
    }

    public Evolution? Evolution
    {
        get => evolution;
        set { evolution = value; tags = null; }
    }

    public WeaponBehavior Behavior => evolution?.Behavior ?? Def.Behavior;
    public School School => evolution?.School ?? Def.School;
    public string Art => evolution?.Art ?? Def.Art;

    /// <summary>What it is: its own tags, what the evolution adds, and its school.</summary>
    public Tag[] Tags
    {
        get
        {
            if (tags != null) return tags;
            var t = new List<Tag>(Def.Tags);
            if (evolution?.AddTags is { } add) foreach (var a in add) if (!t.Contains(a)) t.Add(a);
            var s = School.AsTag();
            if (!t.Contains(s)) t.Add(s);
            return tags = t.ToArray();
        }
    }

    /// <summary>A number from the evolution's overrides, else the base.</summary>
    public double? Num(Func<WeaponStats, double?> f) => (evolution?.Set is { } s ? f(s) : null) ?? f(Def.Base);
    public int? Int(Func<WeaponStats, int?> f) => (evolution?.Set is { } s ? f(s) : null) ?? f(Def.Base);
    public bool Flag(Func<WeaponStats, bool?> f) => ((evolution?.Set is { } s ? f(s) : null) ?? f(Def.Base)) == true;
    public StatusPayload? StatusOf => evolution?.Set?.Status ?? Def.Base.Status;
    public GroundSpec? GroundOf => evolution?.Set?.GroundOnHit ?? Def.Base.GroundOnHit;

    public double Damage
    {
        get
        {
            double d = (Def.Base.Damage ?? 0) * (1 + Def.Growth * (Rank - 1)) * Mods.Damage;
            if (evolution != null) d *= evolution.Mods.Damage ?? 1;
            return d;
        }
    }

    public double BossDamage => Def.BossDamage ?? 1;

    /// <summary>Critical strike chance its own blows add (Starseeker's sure strikes).</summary>
    public double CritBonus => Num(s => s.Crit) ?? 0;
}

/// <summary>How each behaviour turns a weapon into things on the field.</summary>
public static class Firing
{
    public static double CooldownOf(Battle b, WeaponInst w)
    {
        double c = (w.Def.Base.Cooldown ?? 1) * b.Stats.Get(Stat.Cooldown) * w.Mods.Cooldown;
        if (w.Evolution != null) c *= w.Evolution.Mods.Cooldown ?? 1;
        return Math.Max(0.08, Math.Min(20, c));
    }

    public static double AreaOf(Battle b, WeaponInst w, double baseValue)
    {
        double a = baseValue * b.Stats.Get(Stat.Area) * (1 + Content.Weapons.AreaStep * (w.Rank - 1)) * w.Mods.Area;
        if (w.Evolution != null) a *= w.Evolution.Mods.Area ?? 1;
        return a;
    }

    public static double DurationOf(Battle b, WeaponInst w, double baseValue)
    {
        double d = baseValue * b.Stats.Get(Stat.Duration) * (1 + Content.Weapons.DurationStep * (w.Rank - 1)) * w.Mods.Duration;
        if (w.Evolution != null) d *= w.Evolution.Mods.Duration ?? 1;
        return d;
    }

    public static int CountOf(Battle b, WeaponInst w, int? baseCount = null)
    {
        int n = baseCount ?? w.Def.Base.Projectiles ?? 1;
        if (w.Rank >= Content.Weapons.ProjRankA) n++;
        if (w.Rank >= Content.Weapons.ProjRankB) n++;
        n += RoundInt(b.Stats.Get(Stat.Projectiles)) + w.Mods.Projectiles;
        if (w.Evolution != null) n += w.Evolution.Mods.Projectiles ?? 0;
        return Math.Max(1, n);
    }

    public static double SpeedOf(Battle b, WeaponInst w)
    {
        double s = (w.Def.Base.Speed ?? 9) * b.Stats.Get(Stat.ProjectileSpeed) * w.Mods.Speed;
        if (w.Evolution != null) s *= w.Evolution.Mods.Speed ?? 1;
        return s;
    }

    static int PierceOf(Battle b, WeaponInst w) =>
        (int)(w.Num(s => s.Pierce) ?? 0) + RoundInt(b.Stats.Get(Stat.Pierce)) + w.Mods.Pierce + (w.Evolution?.Mods.Pierce ?? 0);

    static double RangeOf(WeaponInst w) => w.Num(s => s.Range) ?? 14;

    /* ------------------------------------------------------------- firing -- */

    public static void Tick(Battle b, WeaponInst w, double dt)
    {
        w.Timer -= dt;
        if (w.BurstLeft > 0)
        {
            w.BurstT -= dt;
            if (w.BurstT <= 0)
            {
                w.BurstLeft--;
                w.BurstT = 0.07;
                FireAimedOne(b, w, w.BurstTarget);
            }
        }
        if (w.Timer > 0) return;
        bool fired = Fire(b, w);
        // Nothing in range: look again soon rather than waiting a whole cooldown.
        w.Timer = fired ? CooldownOf(b, w) : 0.25;
    }

    static bool Fire(Battle b, WeaponInst w) => w.Behavior switch
    {
        WeaponBehavior.Aimed => FireAimed(b, w),
        WeaponBehavior.Spray => FireSpray(b, w),
        WeaponBehavior.Ring => FireRing(b, w),
        WeaponBehavior.Nova => FireNova(b, w),
        WeaponBehavior.Zone => FireZone(b, w),
        WeaponBehavior.Chain => FireChain(b, w),
        WeaponBehavior.Orbit => FireOrbit(b, w),
        WeaponBehavior.Storm => FireStorm(b, w),
        WeaponBehavior.Bounce => FireBounce(b, w),
        WeaponBehavior.Beam => FireBeam(b, w),
        WeaponBehavior.Palm => FirePalm(b, w),
        WeaponBehavior.Herd => FireHerd(b, w),
        WeaponBehavior.Chakram => FireChakram(b, w),
        WeaponBehavior.Slash => FireSlash(b, w),
        WeaponBehavior.Raise => FireRaise(b, w),
        _ => false,
    };

    static bool FireAimed(Battle b, WeaponInst w)
    {
        // A skill that hunts the strongest is aimed at it from the hand, not only in flight.
        var target = SeekOf(w) is Seek.Elite or Seek.Strongest ? Toughest(b, RangeOf(w)) : b.NearestHostile(b.Player.X, b.Player.Z, RangeOf(w));
        if (target == null) return false;
        int n = CountOf(b, w);
        if (w.Flag(s => s.Burst))
        {
            w.BurstLeft = n - 1;
            w.BurstT = 0.07;
            w.BurstTarget = target.Id;
            FireAimedOne(b, w, target.Id);
        }
        else
            for (int i = 0; i < n; i++) FireAimedOne(b, w, target.Id, (i - (n - 1) / 2.0) * 0.14);
        return true;
    }

    static void FireAimedOne(Battle b, WeaponInst w, int targetId, double angleOffset = 0)
    {
        var p = b.Player;
        Enemy? t = targetId >= 0 ? b.Enemies.Items[targetId] : null;
        if (t == null || !t.Alive || t.State == EnemyState.Dying) t = b.NearestHostile(p.X, p.Z, RangeOf(w));
        if (t == null) return;
        double homing = w.Num(s => s.Homing) ?? 0;
        double a = Math.Atan2(t.Z - p.Z, t.X - p.X) + angleOffset + (homing != 0 ? (b.Rng.Next() - 0.5) * 0.9 : 0);
        Launch(b, w, a, target: t.Id);
    }

    static Projectile? Launch(Battle b, WeaponInst w, double angle, int? target = null, double? x = null, double? z = null,
        double speedMul = 1, double? life = null, bool chakram = false, bool herd = false)
    {
        var p = b.Player;
        double sp = SpeedOf(b, w) * speedMul;
        var pr = b.SpawnProjectile(Side.Player, x ?? p.X + Math.Cos(angle) * 0.5, z ?? p.Z + Math.Sin(angle) * 0.5, DamageFor(w), w.School);
        if (pr != null)
        {
            pr.Y = 1.1;
            pr.Vx = Math.Cos(angle) * sp; pr.Vz = Math.Sin(angle) * sp; pr.Speed = sp;
            pr.Tags = w.Tags;
            pr.Radius = (w.Num(s => s.Radius) ?? 0.2) * Math.Sqrt(b.Stats.Get(Stat.Area));
            pr.Pierce = PierceOf(b, w);
            pr.Bounces = (int)(w.Num(s => s.Bounces) ?? 0) + (w.Evolution?.Mods.Bounces ?? 0);
            pr.Life = life ?? DurationOf(b, w, w.Num(s => s.Life) ?? 2.0) / (1 + Content.Weapons.DurationStep * (w.Rank - 1));
            pr.Homing = (w.Num(s => s.Homing) ?? 0) + w.Mods.Homing;
            pr.Seek = SeekOf(w);
            // A hunter of the strongest or the marked picks its own prey in flight.
            pr.Target = pr.Seek is Seek.Strongest or Seek.Elite or Seek.Marked ? -2 : target ?? -2;
            pr.Weapon = w.Id;
            pr.Art = w.Art;
            pr.Status = w.StatusOf;
            var splash = w.Num(s => s.Splash);
            pr.Splash = splash is { } sv && sv != 0 ? AreaOf(b, w, sv) : 0;
            pr.SplitOnHit = w.Int(s => s.SplitOnHit) ?? 0;
            pr.Heal = w.Num(s => s.Heal) ?? 0;
            pr.Knockback = w.Num(s => s.Knockback) ?? 0;
            pr.Chakram = chakram;
            pr.GroundOnHit = w.GroundOf;
            pr.Rank = w.Rank;
            pr.BossDamage = w.BossDamage;
            pr.AimAlongVelocity();
            if (herd) pr.Rehit = 0.6;
        }
        b.Events.Emit(new Ev.Muzzle { X = p.X, Z = p.Z, Angle = angle, School = w.School, Weapon = w.Id });
        return pr;
    }

    static double DamageFor(WeaponInst w) => w.Damage;

    /// <summary>What its projectiles hunt: the evolution's choice, else the weapon's, else the nearest.</summary>
    static Seek? SeekOf(WeaponInst w) => w.Evolution?.Set?.Seek ?? w.Def.Base.Seek;

    /// <summary>The toughest thing in reach: a boss, then a champion, then the most health.</summary>
    static Enemy? Toughest(Battle b, double range)
    {
        Enemy? best = null;
        foreach (var e in b.HostilesInRadius(b.Player.X, b.Player.Z, range))
            if (best == null || (e.Boss ? 2e6 : e.Elite ? 1e6 : 0) + e.MaxHp > (best.Boss ? 2e6 : best.Elite ? 1e6 : 0) + best.MaxHp) best = e;
        return best;
    }

    static bool FireSpray(Battle b, WeaponInst w)
    {
        var p = b.Player;
        var t = b.NearestHostile(p.X, p.Z, RangeOf(w));
        if (t == null) return false;
        int n = CountOf(b, w);
        double spread = w.Num(s => s.Spread) ?? 0.16;
        double a0 = Math.Atan2(t.Z - p.Z, t.X - p.X);
        for (int i = 0; i < n; i++) Launch(b, w, a0 + (i - (n - 1) / 2.0) * spread, target: t.Id);
        // Arrowfall: the volley also rains on the densest knot of the crowd.
        if (w.Num(s => s.Strikes) is { } strikes && strikes != 0)
            StormAt(b, w, (int)strikes, w.Num(s => s.StormRadius) ?? 5, 1.3, w.Damage * 0.6);
        return true;
    }

    static bool FireRing(Battle b, WeaponInst w)
    {
        if (b.NearestHostile(b.Player.X, b.Player.Z, 9) == null) return false;
        int n = CountOf(b, w);
        double rot = b.Time * 1.7;
        for (int i = 0; i < n; i++) Launch(b, w, rot + (double)i / n * Tau);
        return true;
    }

    static bool FireNova(Battle b, WeaponInst w)
    {
        var p = b.Player;
        double r = AreaOf(b, w, w.Num(s => s.Radius) ?? 3.5);
        if (b.NearestHostile(p.X, p.Z, r + 1) == null) return false;
        int rings = 1 + (w.Rank >= Content.Weapons.ProjRankA ? 1 : 0) + (w.Rank >= Content.Weapons.ProjRankB ? 1 : 0);
        b.Events.Emit(new Ev.Nova { X = p.X, Z = p.Z, Radius = r, School = w.School, Duration = w.Num(s => s.ExpandTime) ?? 0.35, Rings = rings });
        double dmg = w.Damage;
        double kb = w.Num(s => s.Knockback) ?? 0;
        double heal = w.Num(s => s.Heal) ?? 0;
        bool hitAny = false;
        b.ForEachHostileInRadius(p.X, p.Z, r, (e, d) =>
        {
            hitAny = true;
            double dd = d == 0 ? 1 : d;
            b.HitEnemy(e, dmg, w.School, w.Tags, new HitOpts
            {
                Weapon = w, Knockback = kb, DirX = (e.X - p.X) / dd, DirZ = (e.Z - p.Z) / dd, Status = w.StatusOf, BossDamage = w.Def.BossDamage,
            });
        });
        if (heal != 0 && hitAny) b.HealPlayer(heal, "weapon");
        if (w.GroundOf is { } g)
        {
            var zn = b.SpawnZone(Side.Player, p.X, p.Z, AreaOf(b, w, g.Radius), DurationOf(b, w, g.Duration), dmg * g.DpsPct, w.School);
            if (zn != null) { zn.Tags = w.Tags; zn.Art = w.Art + "_ground"; zn.Weapon = w.Id; }
        }
        return true;
    }

    static bool FireZone(Battle b, WeaponInst w)
    {
        var p = b.Player;
        double r = AreaOf(b, w, w.Num(s => s.Radius) ?? 3);
        double x = p.X, z = p.Z;
        bool atTarget = w.Flag(s => s.AtTarget);
        if (atTarget)
        {
            // Every other one goes under a champion or worse, when one is near:
            // a field that only ever finds the crowd never brings down what leads it.
            var big = (w.Swing++ & 1) == 1 ? b.NearestHostile(p.X, p.Z, 11, e => e.Elite || e.Boss) : null;
            var t = big ?? b.DensestHostile(p.X, p.Z, 11, r);
            if (t == null) return false;
            x = t.X; z = t.Z;
        }
        else if (b.NearestHostile(p.X, p.Z, r + 2) == null) return false;
        double tick = w.Num(s => s.TickRate) ?? 0.5;
        var zn = b.SpawnZone(Side.Player, x, z, r, DurationOf(b, w, w.Num(s => s.Duration) ?? 4), w.Damage / tick, w.School);
        if (zn != null)
        {
            zn.Tick = tick; zn.Tags = w.Tags; zn.Slow = w.Num(s => s.Slow) ?? 0; zn.Status = w.StatusOf;
            zn.Art = w.Art; zn.Weapon = w.Id; zn.Follow = !atTarget; zn.Armor = w.Evolution?.Id == "sanctified_earth" ? 6 : 0;
            zn.BossDamage = w.BossDamage;
        }
        return true;
    }

    static bool FireChain(Battle b, WeaponInst w)
    {
        var p = b.Player;
        var first = b.NearestHostile(p.X, p.Z, RangeOf(w));
        if (first == null) return false;
        int jumps = CountOf(b, w, (int)(w.Num(s => s.Chains) ?? 5) - 1) + (w.Evolution?.Mods.Chains ?? 0);
        double reach = AreaOf(b, w, w.Num(s => s.ChainRange) ?? 6);
        bool fork = w.Flag(s => s.Fork);
        ChainFrom(b, p.X, p.Z, first, jumps, reach, w.Damage, w.School, w.Tags, w, fork);
        return true;
    }

    public static void ChainFrom(Battle b, double x0, double z0, Enemy first, int jumps, double reach, double dmg,
        School school, Tag[] tags, WeaponInst? w, bool fork = false, bool sky = false, int depth = 0)
    {
        var hit = new HashSet<int>();
        var points = new List<double> { x0, z0 };
        Enemy? cur = first;
        var queue = new List<Enemy>();
        for (int j = 0; j <= jumps && cur != null; j++)
        {
            hit.Add(cur.Id);
            points.Add(cur.X); points.Add(cur.Z);
            b.HitEnemy(cur, dmg * Math.Pow(0.92, j), school, tags, new HitOpts
            {
                Weapon = w, Status = w?.StatusOf, Depth = depth, BossDamage = w?.Def.BossDamage,
            });
            if (sky) b.Events.Emit(new Ev.Strike { X = cur.X, Z = cur.Z, Radius = 0.9, School = school, Delay = 0 });
            var next = b.NearestHostile(cur.X, cur.Z, reach, e => !hit.Contains(e.Id));
            if (fork && next != null && j < jumps - 1)
            {
                var second = b.NearestHostile(cur.X, cur.Z, reach, e => !hit.Contains(e.Id) && e.Id != next.Id);
                if (second != null) queue.Add(second);
            }
            cur = next;
        }
        b.Events.Emit(new Ev.Chain { Points = points.ToArray(), School = school });
        // Forks run a shorter chain of their own from where they split.
        for (int i = 0; i < Math.Min(3, queue.Count); i++)
        {
            var f = queue[i];
            if (hit.Contains(f.Id)) continue;
            var pts = new[] { points[^2], points[^1], f.X, f.Z };
            b.HitEnemy(f, dmg * 0.7, school, tags, new HitOpts { Weapon = w, Depth = depth });
            b.Events.Emit(new Ev.Chain { Points = pts, School = school });
        }
    }

    static bool FireOrbit(Battle b, WeaponInst w)
    {
        // Only one gyre at a time: the next begins when the last one ends.
        if (b.Time < w.ActiveT) return false;
        if (b.NearestHostile(b.Player.X, b.Player.Z, 10) == null) return false;
        int n = CountOf(b, w);
        double life = DurationOf(b, w, w.Num(s => s.Duration) ?? 3);
        double radius = AreaOf(b, w, w.Num(s => s.OrbitRadius) ?? 2);
        double speed = w.Num(s => s.OrbitSpeed) ?? 4;
        for (int i = 0; i < n; i++)
        {
            var pr = b.SpawnProjectile(Side.Player, b.Player.X, b.Player.Z, w.Damage, w.School);
            if (pr == null) continue;
            pr.Y = 1; pr.Tags = w.Tags; pr.Radius = (w.Num(s => s.Radius) ?? 0.5) * Math.Sqrt(b.Stats.Get(Stat.Area));
            pr.Pierce = 999; pr.Life = life; pr.Weapon = w.Id; pr.Art = w.Art; pr.Status = w.StatusOf;
            pr.Knockback = 0.25; pr.Rank = w.Rank; pr.BossDamage = w.BossDamage;
            pr.OrbitR = radius;
            pr.OrbitW = speed;
            pr.OrbitA = (double)i / n * Tau;
            pr.Rehit = 0.45;
            pr.SlotId = w.Slot;
        }
        w.ActiveT = b.Time + life;
        return true;
    }

    static bool StormAt(Battle b, WeaponInst w, int strikes, double area, double splash, double dmg)
    {
        var p = b.Player;
        var targets = b.HostilesInRadius(p.X, p.Z, area * b.Stats.Get(Stat.Area) + 3);
        if (targets.Count == 0) return false;
        for (int i = 0; i < strikes; i++)
        {
            var t = targets[b.Rng.Int(0, targets.Count - 1)];
            double x = t.X + (b.Rng.Next() - 0.5) * 1.2, z = t.Z + (b.Rng.Next() - 0.5) * 1.2;
            b.ScheduleStrike(x, z, AreaOf(b, w, splash), dmg, w.School, w.Tags, 0.28 + i * 0.05, w);
        }
        return true;
    }

    static bool FireStorm(Battle b, WeaponInst w)
    {
        int strikes = (int)(w.Num(s => s.Strikes) ?? 5) + (w.Evolution?.Mods.Strikes ?? 0) + RoundInt(b.Stats.Get(Stat.Projectiles));
        return StormAt(b, w, strikes, w.Num(s => s.StormRadius) ?? 6, w.Num(s => s.Splash) ?? 1.5, w.Damage);
    }

    static bool FireBounce(Battle b, WeaponInst w)
    {
        var p = b.Player;
        var t = b.NearestHostile(p.X, p.Z, RangeOf(w));
        if (t == null) return false;
        int n = CountOf(b, w);
        double a0 = Math.Atan2(t.Z - p.Z, t.X - p.X);
        for (int i = 0; i < n; i++)
        {
            var pr = Launch(b, w, a0 + (i - (n - 1) / 2.0) * 0.3, target: t.Id);
            if (pr != null) pr.Homing = 7;
        }
        return true;
    }

    static bool FireBeam(Battle b, WeaponInst w)
    {
        var p = b.Player;
        var t = b.NearestHostile(p.X, p.Z, RangeOf(w));
        if (t == null) return false;
        double a = Math.Atan2(t.Z - p.Z, t.X - p.X);
        double len = RangeOf(w) * (1 + 0.04 * (w.Rank - 1));
        double width = AreaOf(b, w, w.Num(s => s.BeamWidth) ?? 0.6);
        double x1 = p.X + Math.Cos(a) * len, z1 = p.Z + Math.Sin(a) * len;
        b.Events.Emit(new Ev.Beam { X0 = p.X, Z0 = p.Z, X1 = x1, Z1 = z1, Width = width, School = w.School, Duration = 0.35 });
        double dmg = w.Damage;
        b.ForEachHostileNearSegment(p.X, p.Z, x1, z1, width, e =>
            b.HitEnemy(e, dmg, w.School, w.Tags, new HitOpts { Weapon = w, Status = w.StatusOf, BossDamage = w.Def.BossDamage }));
        return true;
    }

    static bool FirePalm(Battle b, WeaponInst w)
    {
        var p = b.Player;
        double reach = AreaOf(b, w, w.Num(s => s.Reach) ?? 2.9);
        var targets = b.HostilesInRadius(p.X, p.Z, reach + 0.6);
        if (targets.Count == 0) return false;
        targets.Sort((a, c) => ((a.X - p.X) * (a.X - p.X) + (a.Z - p.Z) * (a.Z - p.Z)).CompareTo((c.X - p.X) * (c.X - p.X) + (c.Z - p.Z) * (c.Z - p.Z)));
        int n = CountOf(b, w);
        double arc = w.Num(s => s.Arc) ?? 1.25;
        for (int i = 0; i < n; i++)
        {
            var t = targets[i % targets.Count];
            double a = Math.Atan2(t.Z - p.Z, t.X - p.X) + (i >= targets.Count ? (i - targets.Count + 1) * 0.6 : 0);
            ConeHit(b, w, a, arc, reach, w.Damage);
        }
        return true;
    }

    static bool ConeHit(Battle b, WeaponInst w, double a, double arc, double reach, double dmg)
    {
        var p = b.Player;
        b.Events.Emit(new Ev.Slash { X = p.X, Z = p.Z, Angle = a, Arc = arc, Reach = reach, School = w.School });
        double kb = w.Num(s => s.Knockback) ?? 0;
        bool any = false;
        b.ForEachHostileInRadius(p.X, p.Z, reach, (e, d) =>
        {
            double da = Wrap(Math.Atan2(e.Z - p.Z, e.X - p.X) - a);
            if (Math.Abs(da) > arc / 2 + Math.Atan2(e.Radius, Math.Max(d, 0.1))) return;
            any = true;
            double dd = d == 0 ? 1 : d;
            b.HitEnemy(e, dmg, w.School, w.Tags, new HitOpts
            {
                Weapon = w, Knockback = kb, DirX = (e.X - p.X) / dd, DirZ = (e.Z - p.Z) / dd, Status = w.StatusOf, BossDamage = w.Def.BossDamage,
            });
        });
        return any;
    }

    static bool FireSlash(Battle b, WeaponInst w)
    {
        var p = b.Player;
        double reach = AreaOf(b, w, w.Num(s => s.Reach) ?? 2.6);
        var t = b.NearestHostile(p.X, p.Z, reach + 1.2);
        if (t == null) return false;
        double a = Math.Atan2(t.Z - p.Z, t.X - p.X);
        double arc = w.Num(s => s.Arc) ?? 2.2;
        int n = CountOf(b, w, 1);
        for (int i = 0; i < n; i++)
        {
            double ai = a + (i == 0 ? 0 : (i % 2 == 1 ? 1 : -1) * Math.Ceiling(i / 2.0) * arc * 0.85);
            ConeHit(b, w, ai, arc, reach, w.Damage);
        }
        // Blades hit things as well as creatures: barrels, brambles, a boss's lamps.
        foreach (var c in b.Collision.Within(p.X, p.Z, reach))
        {
            if (c.Tag == null) continue;
            double da = Wrap(Math.Atan2(c.Z - p.Z, c.X - p.X) - a);
            if (Math.Abs(da) <= arc / 2 + 0.3) b.Hooks.OnHitProp?.Invoke(c.Tag, c.Id, w.School, w.Damage, c.X, c.Z);
        }
        w.Swing++;
        p.AttackAnim = new AttackAnim(w.Id, a, b.Time, arc > 3);
        // Oathkeeper: every swing throws a crescent onward.
        if (w.Evolution?.Id == "oathkeeper")
        {
            var pr = Launch(b, w, a, speedMul: 1, life: 0.9);
            if (pr != null) { pr.Pierce = 99; pr.Radius = 1.1; pr.Art = "crescent_holy"; pr.School = School.Holy; }
        }
        if (w.Evolution?.Id == "bonesplitter")
            b.ScheduleStrike(p.X + Math.Cos(a) * reach * 1.4, p.Z + Math.Sin(a) * reach * 1.4, 1.8, w.Damage * 0.8, School.Physical, w.Tags, 0.12, w);
        return true;
    }

    static bool FireHerd(Battle b, WeaponInst w)
    {
        var p = b.Player;
        var t = b.NearestHostile(p.X, p.Z, RangeOf(w));
        if (t == null) return false;
        int n = CountOf(b, w);
        double a = Math.Atan2(t.Z - p.Z, t.X - p.X);
        for (int i = 0; i < n; i++)
        {
            double off = (i - (n - 1) / 2.0) * 1.1;
            double sx = p.X - Math.Cos(a) * 3 + Math.Cos(a + Math.PI / 2) * off;
            double sz = p.Z - Math.Sin(a) * 3 + Math.Sin(a + Math.PI / 2) * off;
            Launch(b, w, a, x: sx, z: sz, herd: true, life: DurationOf(b, w, w.Num(s => s.Life) ?? 1.8));
        }
        return true;
    }

    /// <summary>The dead get up for you: allies of its kind, up to its count at
    /// once, for its duration, striking as hard as the skill is ranked.</summary>
    static bool FireRaise(Battle b, WeaponInst w)
    {
        var p = b.Player;
        if (b.NearestHostile(p.X, p.Z, 15) == null) return false;
        string kind = w.Evolution?.Set?.Raises ?? w.Def.Base.Raises ?? "ghoul_ally";
        b.RaiseFor(w, kind, DurationOf(b, w, w.Num(s => s.Duration) ?? 12), CountOf(b, w));
        return true;
    }

    static bool FireChakram(Battle b, WeaponInst w)
    {
        var p = b.Player;
        var t = b.NearestHostile(p.X, p.Z, RangeOf(w) + 2);
        if (t == null) return false;
        int n = CountOf(b, w);
        double a0 = Math.Atan2(t.Z - p.Z, t.X - p.X);
        for (int i = 0; i < n; i++)
        {
            var pr = Launch(b, w, a0 + (i - (n - 1) / 2.0) * 0.5, chakram: true, life: DurationOf(b, w, w.Num(s => s.Life) ?? 2.6));
            if (pr != null) { pr.Pierce = 999; pr.Rehit = 0.5; }
        }
        return true;
    }

    /// <summary>What a weapon card should say it does at its rank.</summary>
    public static (int Damage, double Cooldown, int Count) DescribeRank(Battle b, WeaponInst w) =>
        (RoundInt(w.Damage * b.Stats.DamageMult(w.School, w.Tags)), CooldownOf(b, w), CountOf(b, w));
}

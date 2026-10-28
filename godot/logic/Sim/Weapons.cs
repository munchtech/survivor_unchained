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
    /// <summary>The strength (CastMul) of the cast whose burst is still firing.</summary>
    public double BurstMul = 1;
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
    /// <summary>Taken from the hand for a while (the Red Hand's toll): it does not fire.</summary>
    public double DisabledT;
    public int Swing;
    /// <summary>The strength of the cast now in hand (the Ledger, the Crowded Sky, the Echo): a multiplier on its projectiles.</summary>
    public double CastMul = 1;
    /// <summary>Firings so far, and the Melee or Thrown ones the warden's Hand counts toward its heavy blow (Sim/Hands.cs).</summary>
    public int Casts, HandBlows;
    /// <summary>The last firing was heavy: its burst shots still to come are too.</summary>
    public bool HeavyCast;
    Tag[]? tags;
    WickFx? wick;

    /// <summary>Its lit wick's numbers (Sim/Turns.cs); null, no wick, and it fights as it always did.</summary>
    public WickFx? Wick
    {
        get => wick;
        set { wick = value; tags = null; }
    }

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
    /// <summary>A school Turn's school first: the Turn is what she chose for it.</summary>
    public School School => wick?.School ?? evolution?.School ?? Def.School;
    public string Art => evolution?.Art ?? Def.Art;

    /// <summary>What it is: its own tags, what the evolution adds, and its school.</summary>
    public Tag[] Tags
    {
        get
        {
            if (tags != null) return tags;
            var t = new List<Tag>(Def.Tags);
            if (evolution?.AddTags is { } add) foreach (var a in add) if (!t.Contains(a)) t.Add(a);
            // A school Turn takes the old school's tag away (physical stays: the steel is still steel).
            if (wick?.School != null && wick.From != School.Physical) t.Remove(wick.From.AsTag());
            var s = School.AsTag();
            if (!t.Contains(s)) t.Add(s);
            return tags = t.ToArray();
        }
    }

    /// <summary>A number from the evolution's overrides, else the base.</summary>
    public double? Num(Func<WeaponStats, double?> f) => (evolution?.Set is { } s ? f(s) : null) ?? f(Def.Base);
    public int? Int(Func<WeaponStats, int?> f) => (evolution?.Set is { } s ? f(s) : null) ?? f(Def.Base);
    public bool Flag(Func<WeaponStats, bool?> f) => ((evolution?.Set is { } s ? f(s) : null) ?? f(Def.Base)) == true;
    public StatusPayload? StatusOf => WickStatus(evolution?.Set?.Status ?? Def.Base.Status);
    public GroundSpec? GroundOf => evolution?.Set?.GroundOnHit ?? Def.Base.GroundOnHit ?? wick?.Ground;

    /// <summary>A school Turn: the old school's own status becomes the new school's (a frost bolt turned fire burns).</summary>
    StatusPayload? WickStatus(StatusPayload? p) =>
        p != null && wick is { School: not null, Status: { } to } && p.Kind == Turns.NativeStatus(wick.From) ? to with { Chance = p.Chance } : p;

    public double Damage
    {
        get
        {
            double d = (Def.Base.Damage ?? 0) * (1 + Def.Growth * (Rank - 1)) * Mods.Damage;
            if (evolution != null) d *= evolution.Mods.Damage ?? 1;
            if (wick != null) d *= wick.Damage;
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
        double c = (w.Def.Base.Cooldown ?? 1) * b.Stats.Get(Stat.Cooldown) * w.Mods.Cooldown * b.ReaverCooldownMul(w) * b.ArcanistCooldownMul(w) * b.StalkerCooldownMul(w) * b.FlareCooldownMul(w);
        if (w.Evolution != null) c *= w.Evolution.Mods.Cooldown ?? 1;
        if (w.Wick != null) c *= w.Wick.Cooldown;
        return Math.Max(0.08, Math.Min(20, c));
    }

    public static double AreaOf(Battle b, WeaponInst w, double baseValue)
    {
        double a = baseValue * b.Stats.Get(Stat.Area) * (1 + Content.Weapons.AreaStep * (w.Rank - 1)) * w.Mods.Area;
        if (w.Evolution != null) a *= w.Evolution.Mods.Area ?? 1;
        if (w.Wick != null) a *= w.Wick.Area;
        // sunderer.skill.area / tags.area: the skill's lamps and its tags' lamps reach wider.
        a *= 1 + b.Lamps.SizeOn("skill.area", "inc", w.Def.Id, w.Def.Tags) + b.Lamps.SizeOn("tags.area", "inc", w.Def.Id, w.Def.Tags) + b.StormReach(w);
        // The reaver's Hand: hurt below half, her areas reach wider.
        a *= b.HandAreaMul(w);
        return a;
    }

    /// <summary>bulwark.skill.reach: metres of reach a skill's lamp adds (Oathblade, 1.5).</summary>
    static double ReachAdd(Battle b, WeaponInst w) => b.Lamps.SizeOn("skill.reach", "add", w.Def.Id, w.Def.Tags) + b.ChainReach(w);

    /// <summary>The status a skill strikes with: its own, or the one its lamp gives (sunderer.skill.status).</summary>
    public static StatusPayload? StatusWith(Battle b, WeaponInst w) =>
        w.StatusOf ?? (b.Lamps.HasOn("skill.status", w.Def.Id, w.Def.Tags) && b.Lamps.Each["skill.status"].Find(e => e.Status != null && (e.Skill == w.Def.Id)) is { Status: { } k } ? new StatusPayload(k, 1, 1, 3) : null);

    public static double DurationOf(Battle b, WeaponInst w, double baseValue)
    {
        double d = baseValue * b.Stats.Get(Stat.Duration) * (1 + Content.Weapons.DurationStep * (w.Rank - 1)) * w.Mods.Duration * (1 + b.ZoneLonger(w));
        if (w.Evolution != null) d *= w.Evolution.Mods.Duration ?? 1;
        return d;
    }

    public static int CountOf(Battle b, WeaponInst w, int? baseCount = null)
    {
        int n = baseCount ?? w.Def.Base.Projectiles ?? 1;
        if (w.Rank >= Content.Weapons.ProjRankA) n++;
        if (w.Rank >= Content.Weapons.ProjRankB) n++;
        n += RoundInt(b.Stats.Get(Stat.Projectiles)) + w.Mods.Projectiles + b.ArcanistProjectiles(w) + b.StalkerProjectiles(w);
        if (w.Evolution != null) n += w.Evolution.Mods.Projectiles ?? 0;
        // Split: three smaller, of everything it would throw.
        if (w.Wick is { Projectiles: not 1 } wk) n = (int)Math.Round(n * wk.Projectiles);
        return Math.Max(1, n);
    }

    public static double SpeedOf(Battle b, WeaponInst w)
    {
        double s = (w.Def.Base.Speed ?? 9) * b.Stats.Get(Stat.ProjectileSpeed) * w.Mods.Speed * b.ArcanistSpeedMul(w);
        if (w.Evolution != null) s *= w.Evolution.Mods.Speed ?? 1;
        if (w.Wick != null) s *= w.Wick.Speed;
        return s;
    }

    static int PierceOf(Battle b, WeaponInst w) =>
        b.StalkerPierce(w, (int)(w.Num(s => s.Pierce) ?? 0) + RoundInt(b.Stats.Get(Stat.Pierce)) + w.Mods.Pierce + (w.Evolution?.Mods.Pierce ?? 0)) + b.HandPierce(w);

    static double RangeOf(WeaponInst w) => w.Num(s => s.Range) ?? 14;

    /* ------------------------------------------------------------- firing -- */

    public static void Tick(Battle b, WeaponInst w, double dt)
    {
        if (w.DisabledT > 0) { w.DisabledT -= dt; return; }
        w.Timer -= dt;
        if (w.BurstLeft > 0)
        {
            w.BurstT -= dt;
            if (w.BurstT <= 0)
            {
                w.BurstLeft--;
                w.BurstT = 0.07;
                var hb0 = b.HeavyBy;
                b.HeavyBy = w.HeavyCast ? w : null;
                FireBurstShot(b, w);
                b.HeavyBy = hb0;
            }
        }
        if (w.Timer > 0) return;
        int kills0 = w.Kills;
        b.ArcanistBeforeCast(w);
        // The warden's Hand: every few blows one is heavy, and every hit of it (HitEnemy reads HeavyBy).
        bool heavy = b.HandBeginCast(w);
        var hb = b.HeavyBy;
        b.HeavyBy = heavy ? w : null;
        bool fired = Fire(b, w);
        b.HeavyBy = hb;
        b.HandEndCast(w, fired);
        if (fired) w.HeavyCast = heavy;
        b.ArcanistAfterCast(w, fired);
        // Nothing in range: look again soon rather than waiting a whole cooldown.
        w.Timer = fired ? CooldownOf(b, w) : 0.25;
        // sunderer.momentum: a melee swing that kills enough brings the skill's next swing sooner.
        if (fired && w.Tags.Has(Tag.Melee) && b.Lamp("momentum") && w.Kills - kills0 >= b.Lamps.Full("momentum", "kills", 3))
            w.Timer *= 1 - Math.Min(0.9, b.Lamps.Size("momentum", "sooner"));
    }

    /// <summary>moonweaver.the_echo: the spell fires again.</summary>
    public static bool Echo(Battle b, WeaponInst w) => Fire(b, w);

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
            // A burst still firing (the Echo comes 0.5 s after the cast, a long burst runs past a short wait)
            // is let go at once, at its own strength, not cut short by this one.
            while (w.BurstLeft > 0) { w.BurstLeft--; FireBurstShot(b, w); }
            w.BurstMul = w.CastMul;
            w.BurstLeft = n - 1;
            w.BurstT = 0.07;
            w.BurstTarget = target.Id;
            FireAimedOne(b, w, target.Id);
        }
        else
            for (int i = 0; i < n; i++) FireAimedOne(b, w, target.Id, (i - (n - 1) / 2.0) * 0.14);
        return true;
    }

    static void FireBurstShot(Battle b, WeaponInst w)
    {
        double keep = w.CastMul;
        w.CastMul = w.BurstMul;
        FireAimedOne(b, w, w.BurstTarget);
        w.CastMul = keep;
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
        var pr = b.SpawnProjectile(Side.Player, x ?? p.X + Math.Cos(angle) * 0.5, z ?? p.Z + Math.Sin(angle) * 0.5, DamageFor(w) * w.CastMul, w.School);
        if (pr != null)
        {
            pr.Y = 1.1;
            pr.Vx = Math.Cos(angle) * sp; pr.Vz = Math.Sin(angle) * sp; pr.Speed = sp;
            pr.Tags = w.Tags;
            pr.Radius = (w.Num(s => s.Radius) ?? 0.2) * Math.Sqrt(b.Stats.Get(Stat.Area));
            pr.Pierce = PierceOf(b, w);
            if (b.HandPierce(w) > 0) b.HandPierced(pr);
            pr.Bounces = (int)(w.Num(s => s.Bounces) ?? 0) + (w.Evolution?.Mods.Bounces ?? 0) + (w.Wick?.Bounces ?? 0);
            pr.Life = life ?? DurationOf(b, w, w.Num(s => s.Life) ?? 2.0) / (1 + Content.Weapons.DurationStep * (w.Rank - 1));
            pr.Homing = (w.Num(s => s.Homing) ?? 0) + w.Mods.Homing;
            pr.Seek = b.StalkerSeek(w, b.ArcanistSeek(w, SeekOf(w)));
            // A hunter of the strongest or the marked picks its own prey in flight.
            pr.Target = pr.Seek is Seek.Strongest or Seek.Elite or Seek.Marked ? -2 : target ?? -2;
            pr.Weapon = w.Id;
            b.ArcanistLaunched(pr, w);
            b.StalkerLaunched(pr, w);
            pr.Art = w.Art;
            pr.Status = w.StatusOf;
            var splash = w.Num(s => s.Splash);
            pr.Splash = splash is { } sv && sv != 0 ? AreaOf(b, w, sv) : 0;
            pr.SplitOnHit = w.Int(s => s.SplitOnHit) ?? 0;
            pr.Heal = w.Num(s => s.Heal) ?? 0;
            pr.Knockback = w.Num(s => s.Knockback) ?? 0;
            pr.Chakram = chakram;
            pr.GroundOnHit = w.GroundOf;
            // The Falling Star (a Mark): the cinder's blast leaves the ground burning.
            if (pr.GroundOnHit == null && w.Id == "cinderfall" && b.Marked(Marks.FallingStar, out double star))
                pr.GroundOnHit = new GroundSpec(1.8, Marks.Lerp(2, 5, star), 0.25);
            pr.Rank = w.Rank;
            pr.BossDamage = w.BossDamage;
            pr.AimAlongVelocity();
            if (herd) pr.Rehit = 0.6;
        }
        b.Events.Emit(new Ev.Muzzle { X = p.X, Z = p.Z, Angle = angle, School = w.School, Weapon = w.Id, Art = w.Art, Rank = w.Rank });
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
        // The Ravine (a Mark): a second volley at the farthest in reach, a part as strong.
        if (w.Id == "volley" && b.Marked(Marks.Ravine, out double ravine) && b.FarthestHostile(p.X, p.Z, RangeOf(w)) is { } far && far != t)
        {
            double af = Math.Atan2(far.Z - p.Z, far.X - p.X), k = Marks.Lerp(0.35, 0.9, ravine);
            for (int i = 0; i < n; i++)
                if (Launch(b, w, af + (i - (n - 1) / 2.0) * spread, target: far.Id) is { } pr) pr.Damage *= k;
        }
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
        double r = AreaOf(b, w, w.Num(s => s.Radius) ?? 3.5) + ReachAdd(b, w);
        if (b.NearestHostile(p.X, p.Z, r + 1) == null) return false;
        int rings = 1 + (w.Rank >= Content.Weapons.ProjRankA ? 1 : 0) + (w.Rank >= Content.Weapons.ProjRankB ? 1 : 0);
        b.Events.Emit(new Ev.Nova { X = p.X, Z = p.Z, Radius = r, School = w.School, Duration = w.Num(s => s.ExpandTime) ?? 0.35, Rings = rings, Art = w.Art, Rank = w.Rank });
        double dmg = w.Damage;
        double kb = w.Num(s => s.Knockback) ?? 0;
        double heal = w.Num(s => s.Heal) ?? 0;
        var novaStatus = StatusWith(b, w);
        bool hitAny = false;
        b.ForEachHostileInRadius(p.X, p.Z, r, (e, d) =>
        {
            hitAny = true;
            double dd = d == 0 ? 1 : d;
            b.HitEnemy(e, dmg, w.School, w.Tags, new HitOpts
            {
                Weapon = w, Knockback = kb, DirX = (e.X - p.X) / dd, DirZ = (e.Z - p.Z) / dd, Status = novaStatus, BossDamage = w.Def.BossDamage,
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
        int jumps = CountOf(b, w, (int)(w.Num(s => s.Chains) ?? 5) - 1) + (w.Evolution?.Mods.Chains ?? 0) + (w.Wick?.Chains ?? 0);
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
            if (sky) b.Events.Emit(new Ev.Strike { X = cur.X, Z = cur.Z, Radius = 0.9, School = school, Delay = 0, Art = "arc_sky", Rank = w?.Rank ?? 1 });
            var next = b.NearestHostile(cur.X, cur.Z, reach, e => !hit.Contains(e.Id));
            if (fork && next != null && j < jumps - 1)
            {
                var second = b.NearestHostile(cur.X, cur.Z, reach, e => !hit.Contains(e.Id) && e.Id != next.Id);
                if (second != null) queue.Add(second);
            }
            cur = next;
        }
        b.Events.Emit(new Ev.Chain { Points = points.ToArray(), School = school, Art = w?.Art, Rank = w?.Rank ?? 1 });
        // Forks run a shorter chain of their own from where they split.
        for (int i = 0; i < Math.Min(3, queue.Count); i++)
        {
            var f = queue[i];
            if (hit.Contains(f.Id)) continue;
            var pts = new[] { points[^2], points[^1], f.X, f.Z };
            b.HitEnemy(f, dmg * 0.7, school, tags, new HitOpts { Weapon = w, Depth = depth });
            b.Events.Emit(new Ev.Chain { Points = pts, School = school, Art = w?.Art, Rank = w?.Rank ?? 1 });
        }
    }

    static bool FireOrbit(Battle b, WeaponInst w)
    {
        // Only one gyre at a time: the next begins when the last one ends.
        if (b.Time < w.ActiveT) return false;
        if (b.NearestHostile(b.Player.X, b.Player.Z, 10) == null) return false;
        int n = CountOf(b, w);
        // The Gyre (a Mark): an axe more for every few close by, to three more.
        if (w.Id == "axe_gyre" && b.Marked(Marks.Gyre, out double gyre))
            n += Math.Min(3, (int)(b.HostilesInRadius(b.Player.X, b.Player.Z, 5).Count / Marks.Lerp(6, 3, gyre)));
        double life = DurationOf(b, w, w.Num(s => s.Duration) ?? 3);
        double radius = AreaOf(b, w, w.Num(s => s.OrbitRadius) ?? 2) + ReachAdd(b, w);
        double speed = w.Num(s => s.OrbitSpeed) ?? 4;
        for (int i = 0; i < n; i++)
        {
            var pr = b.SpawnProjectile(Side.Player, b.Player.X, b.Player.Z, w.Damage, w.School);
            if (pr == null) continue;
            pr.Y = 1; pr.Tags = w.Tags; pr.Radius = (w.Num(s => s.Radius) ?? 0.5) * Math.Sqrt(b.Stats.Get(Stat.Area));
            pr.Pierce = 999; pr.Life = life; pr.Weapon = w.Id; pr.Art = w.Art; pr.Status = StatusWith(b, w);
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
        targets = b.BoundFirst(w, targets); // chainbound.lightning_rod
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
        b.Events.Emit(new Ev.Beam { X0 = p.X, Z0 = p.Z, X1 = x1, Z1 = z1, Width = width, School = w.School, Duration = 0.35, Art = w.Art, Rank = w.Rank });
        double dmg = w.Damage;
        b.ForEachHostileNearSegment(p.X, p.Z, x1, z1, width, e =>
            b.HitEnemy(e, dmg, w.School, w.Tags, new HitOpts { Weapon = w, Status = w.StatusOf, BossDamage = w.Def.BossDamage }));
        return true;
    }

    static bool FirePalm(Battle b, WeaponInst w)
    {
        var p = b.Player;
        double reach = AreaOf(b, w, w.Num(s => s.Reach) ?? 2.9) + ReachAdd(b, w);
        var targets = b.HostilesInRadius(p.X, p.Z, reach + 0.6);
        var far = b.IronReachTargets(w, reach + 0.6); // chainbound.iron_reach: Bound things out of the palm's own reach
        if (targets.Count == 0 && far.Count == 0) return false;
        targets.Sort((a, c) => ((a.X - p.X) * (a.X - p.X) + (a.Z - p.Z) * (a.Z - p.Z)).CompareTo((c.X - p.X) * (c.X - p.X) + (c.Z - p.Z) * (c.Z - p.Z)));
        int n = CountOf(b, w);
        double arc = w.Num(s => s.Arc) ?? 1.25;
        for (int i = 0; i < n && targets.Count > 0; i++)
        {
            var t = targets[i % targets.Count];
            double a = Math.Atan2(t.Z - p.Z, t.X - p.X) + (i >= targets.Count ? (i - targets.Count + 1) * 0.6 : 0);
            ConeHit(b, w, a, arc, reach, w.Damage);
        }
        for (int i = 0; i < n && i < far.Count; i++) b.PalmFromAfar(w, far[i], StatusWith(b, w));
        return true;
    }

    static bool ConeHit(Battle b, WeaponInst w, double a, double arc, double reach, double dmg)
    {
        var p = b.Player;
        b.Events.Emit(new Ev.Slash { X = p.X, Z = p.Z, Angle = a, Arc = arc, Reach = reach, School = w.School, Art = w.Art, Rank = w.Rank });
        double kb = w.Num(s => s.Knockback) ?? 0;
        bool any = false;
        Enemy? last = null;
        var hitStatus = StatusWith(b, w);
        b.ForEachHostileInRadius(p.X, p.Z, reach, (e, d) =>
        {
            double da = Wrap(Math.Atan2(e.Z - p.Z, e.X - p.X) - a);
            if (Math.Abs(da) > arc / 2 + Math.Atan2(e.Radius, Math.Max(d, 0.1))) return;
            any = true;
            last = e;
            double dd = d == 0 ? 1 : d;
            b.HitEnemy(e, dmg, w.School, w.Tags, new HitOpts
            {
                Weapon = w, Knockback = kb, DirX = (e.X - p.X) / dd, DirZ = (e.Z - p.Z) / dd, Status = hitStatus, BossDamage = w.Def.BossDamage,
            });
        });
        if (last != null) b.HookLast(w, last); // chainbound.the_long_chain
        return any;
    }

    static bool FireSlash(Battle b, WeaponInst w)
    {
        var p = b.Player;
        double reach = AreaOf(b, w, w.Num(s => s.Reach) ?? 2.6) + ReachAdd(b, w);
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
        // Linger: the swing leaves its ground where the arc's middle fell.
        if (w.Wick?.Ground is { } g)
        {
            double gx = p.X + Math.Cos(a) * reach * 0.55, gz = p.Z + Math.Sin(a) * reach * 0.55;
            var zn = b.SpawnZone(Side.Player, gx, gz, AreaOf(b, w, g.Radius), DurationOf(b, w, g.Duration), w.Damage * g.DpsPct, w.School);
            if (zn != null) { zn.Tags = w.Tags; zn.Art = w.Art + "_ground"; zn.Weapon = w.Id; }
        }
        w.Swing++;
        p.AttackAnim = new AttackAnim(w.Id, a, b.Time, arc > 3);
        // Oathkeeper: every swing throws a crescent onward.
        if (w.Evolution?.Id == "oathkeeper")
        {
            var pr = Launch(b, w, a, speedMul: 1, life: 0.9);
            // (The crescent pierces everything: a Linger ground at each would carpet the field. The swing's is enough.)
            if (pr != null) { pr.Pierce = 99; pr.Radius = 1.1; pr.Art = "crescent_holy"; pr.School = School.Holy; if (w.Wick?.Ground is { } wg && ReferenceEquals(pr.GroundOnHit, wg)) pr.GroundOnHit = null; }
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

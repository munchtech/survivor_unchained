using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Sim;

/* Phase 2's four Flares, staged by their briefs (docs/design/CLASSES.md §3.6): Bell of the Morning, Butcher's Hour,
 * Burns Twice and The Road's Toll. The logic is the game's; the look is the view's. Every moment is an Ev.Flare
 * (Press, Release, each Blow with its Part, target and hitstop, Kill, End), and every timing and number is the
 * Flare's data (lamps.json: "beat" and "args"), so the experience, VFX and animation leads stage them without
 * touching this file. The other twelve keep their kind's plain form until phase 6. */
public sealed partial class Battle
{
    /// <summary>A lit modifier lamp of the carried Flare (§3.7).</summary>
    bool FlareMod(string rule) => Lamps.FlareMods.Contains(rule);

    /// <summary>How many blows it lands: the staged Flares' modifiers add tolls, embers and cuts.</summary>
    int FlareBlowCount(FlareDef f) => f.Id switch
    {
        "bell_of_the_morning" => f.Blows + (FlareMod("bell.fourth_toll") ? 1 : 0),
        "burns_twice" => FlareMod("burns.more_embers") ? (int)f.Arg("moreEmbers", 18) : f.Blows,
        "the_roads_toll" => FlareMod("toll.doubled") ? (int)f.Arg("doubled", 18) : f.Blows,
        _ => f.Blows,
    };

    /// <summary>A Strike's blows by time from the press: its beat ("first" then a "step", or spread to "last"; Burns
    /// Twice's "frost" before its embers), or the plain form's even spread over its length.</summary>
    double[] FlareSchedule(FlareDef f)
    {
        if (f.Kind == FlareKind.Stand) return [];
        int n = FlareBlowCount(f);
        if (!f.Beat.TryGetValue("first", out double first))
        {
            double len = Math.Min(StrikeMax, f.Length);
            return Enumerable.Range(1, Math.Max(1, n)).Select(k => len / Math.Max(1, n) * k).ToArray();
        }
        var at = new List<double>();
        if (f.Beat.TryGetValue("frost", out double frost)) at.Add(frost);
        bool spread = f.Beat.TryGetValue("last", out double last);
        for (int i = 0; i < n; i++)
            at.Add(spread ? first + (n <= 1 ? 0 : (last - first) * i / (n - 1)) : first + f.BeatAt("step", 0.25) * i);
        return at.ToArray();
    }

    /// <summary>One of the Flare's hits on one thing: its power times a share, through the build's damage (its tags).</summary>
    double FlareHit(Enemy e, double share, School school, double knockback, double fromX, double fromZ)
    {
        double vsBig = Boons.ContainsKey("called_shot") ? 1.6 : 1;
        double dx = e.X - fromX, dz = e.Z - fromZ, d = Len(dx, dz);
        if (d < 1e-6) { dx = 1; dz = 0; d = 1; }
        if (e.Boss && !flareStruckBoss) { flareStruckBoss = true; FlareCastsOnBoss++; }
        return HitEnemy(e, flarePower * share, school, Flare!.Tags, new HitOpts { Credit = "flare", BossDamage = vsBig, Knockback = e.Boss ? 0 : knockback, DirX = dx / d, DirZ = dz / d });
    }

    int FlareHitstop(FlareDef f, bool last, string key = "hitstop") =>
        (int)(last ? f.BeatAt("hitstopLast", f.BeatAt(key, 0)) : f.BeatAt(key, 0));

    void FlareBlowEvent(FlareDef f, string part, bool last, double tx, double tz, Enemy? target, double radius, string stop = "hitstop") =>
        Events.Emit(new Ev.Flare
        {
            Phase = FlarePhase.Blow, Id = f.Id, X = Player.X, Z = Player.Z, Radius = radius, Blow = flareBlow, Clutch = flareClutch,
            Stand = f.Kind == FlareKind.Stand, Part = part, Last = last, TX = tx, TZ = tz, Target = target?.Id ?? 0, Hitstop = FlareHitstop(f, last, stop),
        });

    /// <summary>The Flare's reach grew (the clutch, Bright Hour, the long night): its parts grow with it.</summary>
    double FlareGrow(FlareDef f) => f.Radius > 0 ? flareReach / f.Radius : 1;

    /// <summary>At the press: what a staged Flare does at once (Butcher's Hour fills Frenzy).</summary>
    void FlareStagedPress(FlareDef f)
    {
        hourAdded = 0;
        mistAt = 0;
        if (f.Id == "butchers_hour") FillFrenzy();
    }

    /* ---------------------------------------------------- Bell of the Morning -- */

    /// <summary>A toll: everything in reach is seared, lesser things stunned, champions and bosses broken from their
    /// channel and staggered; it mends her. The last toll is a holy blast 8 m round (the seared take it harder).</summary>
    void BellToll(FlareDef f, bool last)
    {
        var p = Player;
        double stun = f.Arg("stun", 1), sear = f.Arg("sear", 2), stagger = f.Arg("stagger", 15);
        ForEachHostileInRadius(p.X, p.Z, flareReach, (e, d) =>
        {
            double dealt = FlareHit(e, f.Arg("toll", 0.45), f.School, 0, p.X, p.Z);
            if (!e.Alive || e.State == EnemyState.Dying) return;
            ApplyStatus(e, new StatusPayload(StatusKind.Sear, 1, 0.2, sear), dealt);
            if (e.Boss || e.Elite) { Interrupt(e); AddStagger(e, e.Boss ? stagger : 2 * stagger); }
            else ApplyStatus(e, new StatusPayload(StatusKind.Stun, 1, 1, stun), 0);
        });
        HealPlayer(MaxHp * (FlareMod("bell.healing_peal") ? f.Arg("peal", 0.08) : f.Arg("mend", 0.04)), "flare", true);
        if (last)
        {
            double r = f.Arg("blastRadius", 8) * FlareGrow(f);
            ForEachHostileInRadius(p.X, p.Z, r, (e, d) => FlareHit(e, f.Arg("blast", 1.25), f.School, 1.2, p.X, p.Z));
            // Bell for the Dead: the lesser things that still stand flee.
            if (FlareMod("bell.for_the_dead"))
                ForEachHostileInRadius(p.X, p.Z, flareReach, (e, d) =>
                {
                    if (!e.Elite && !e.Boss && e.Alive) ApplyStatus(e, new StatusPayload(StatusKind.Fear, 1, 1, f.Arg("flee", 3)), 0);
                });
        }
        FlareBlowEvent(f, last ? "blast" : "toll", last, p.X, p.Z, null, last ? f.Arg("blastRadius", 8) * FlareGrow(f) : flareReach);
    }

    /* ----------------------------------------------------------- Burns Twice -- */

    readonly List<(double X, double Z)> emberFell = new();

    /// <summary>The frost (everything in reach frozen, a boss chilled), then each ember: it falls on the thickest
    /// frozen pack not yet struck (every few on a boss), shatters what is frozen round it, and burns.</summary>
    void BurnsTwiceBlow(FlareDef f, bool last)
    {
        var p = Player;
        if (flareBlow == 1 && f.Beat.ContainsKey("frost"))
        {
            emberFell.Clear();
            ForEachHostileInRadius(p.X, p.Z, flareReach, (e, d) =>
            {
                FlareHit(e, f.Arg("frost", 0.3), School.Frost, 0, p.X, p.Z);
                if (!e.Alive || e.State == EnemyState.Dying) return;
                if (e.Boss) ApplyStatus(e, new StatusPayload(StatusKind.Chill, 1, 1, f.Arg("chill", 3)), 0);
                else Freeze(e, f.Arg("freeze", 2));
            });
            FlareBlowEvent(f, "frost", false, p.X, p.Z, null, flareReach, "hitstop");
            return;
        }
        int embers = flareAt.Length - (f.Beat.ContainsKey("frost") ? 1 : 0), ember = flareBlow - (flareAt.Length - embers);
        double r = f.Arg("emberRadius", 2.5) * FlareGrow(f);
        var near = HostilesInRadius(p.X, p.Z, flareReach).Where(e => e.Alive && e.State != EnemyState.Dying).ToList();
        var boss = near.Where(e => e.Boss).OrderByDescending(e => e.Hp).FirstOrDefault();
        int onBoss = (int)f.Arg("onBoss", 4);
        // Four of twelve seek the boss, evenly (the third, sixth, ninth and twelfth).
        bool seek = boss != null && ember * onBoss / Math.Max(1, embers) > (ember - 1) * onBoss / Math.Max(1, embers);
        Enemy? target;
        if (FlareMod("burns.called_down"))
            target = boss ?? near.Where(e => e.Status.Has(StatusKind.Frozen)).OrderByDescending(e => e.Elite).ThenByDescending(e => e.Hp).FirstOrDefault();
        else if (seek) target = boss;
        else
        {
            // The thickest frozen pack not yet struck; then anything frozen; then the thickest pack at all.
            bool Struck(Enemy e) => emberFell.Any(q => Dist(q.X, q.Z, e.X, e.Z) < r);
            int Pack(Enemy e) => near.Count(o => o.Status.Has(StatusKind.Frozen) && Dist(o.X, o.Z, e.X, e.Z) < r);
            var frozen = near.Where(e => !e.Boss && e.Status.Has(StatusKind.Frozen)).ToList();
            target = frozen.Where(e => !Struck(e)).OrderByDescending(Pack).FirstOrDefault()
                ?? frozen.OrderByDescending(Pack).FirstOrDefault()
                ?? near.Where(e => !e.Boss).OrderByDescending(e => near.Count(o => Dist(o.X, o.Z, e.X, e.Z) < r)).FirstOrDefault()
                ?? boss;
        }
        double tx = target?.X ?? p.X + Math.Cos(ember * 2.4) * flareReach * 0.5, tz = target?.Z ?? p.Z + Math.Sin(ember * 2.4) * flareReach * 0.5;
        emberFell.Add((tx, tz));
        ForEachHostileInRadius(tx, tz, r, (e, d) =>
        {
            // The ice breaks first, then the fire lands: a fire lit on ice burns twice.
            if (e.Status.Has(StatusKind.Frozen))
            {
                e.Status.Remove(StatusKind.Frozen);
                FlareHit(e, f.Arg("shatter", 1.0), School.Frost, 0, tx, tz);
            }
            if (e.Alive && e.State != EnemyState.Dying) FlareHit(e, f.Arg("ember", 0.675), School.Fire, 0.6, tx, tz);
        });
        // Black Ice: at the last ember, what is still frozen below half its health shatters on its own.
        if (last && FlareMod("burns.black_ice"))
            foreach (var e in HostilesInRadius(p.X, p.Z, flareReach))
                if (e.Alive && e.Status.Has(StatusKind.Frozen) && e.Hp < e.MaxHp * f.Arg("blackIce", 0.5))
                {
                    e.Status.Remove(StatusKind.Frozen);
                    FlareHit(e, f.Arg("shatter", 1.0), School.Frost, 0, e.X, e.Z);
                }
        FlareBlowEvent(f, "ember", last, tx, tz, target, r);
    }

    /* -------------------------------------------------------- The Road's Toll -- */

    readonly List<int> tollPlan = new();

    /// <summary>A cut. At the first she picks her twelve: the strongest near, weakest first so the last falls on the
    /// strongest; on a boss its last four (a third of them). Each cut poisons, and what it leaves below a quarter of
    /// its health dies (a boss never). A target fallen before its cut gives it to the strongest still standing.</summary>
    void TollCut(FlareDef f, bool last)
    {
        var p = Player;
        int n = flareAt.Length;
        if (flareBlow == 1) PlanToll(f, n);
        int slot = flareBlow - 1 < tollPlan.Count ? tollPlan[flareBlow - 1] : -1;
        Enemy? e = slot >= 0 && slot < Enemies.Items.Length ? Enemies.Items[slot] : null;
        if (e == null || !e.Alive || e.State == EnemyState.Dying || !Targetable(e))
            e = HostilesInRadius(p.X, p.Z, flareReach).Where(x => x.Alive && x.State != EnemyState.Dying)
                .OrderByDescending(x => x.Boss).ThenByDescending(x => x.Elite).ThenByDescending(x => x.Hp).FirstOrDefault();
        if (e != null)
        {
            double dealt = FlareHit(e, 1, f.School, 0, p.X, p.Z);
            if (e.Alive && e.State != EnemyState.Dying)
            {
                ApplyStatus(e, new StatusPayload(StatusKind.Poison, 1, f.Arg("poison", 0.5), f.Arg("poisonSeconds", 4)), dealt);
                double below = last && FlareMod("toll.last_cut") ? f.Arg("lastCut", 0.4) : f.Arg("execute", 0.25);
                if (!e.Boss && e.Alive && e.State != EnemyState.Dying && e.Hp < e.MaxHp * below) KillEnemy(e, true, null);
            }
        }
        FlareBlowEvent(f, "cut", last, e?.X ?? p.X, e?.Z ?? p.Z, e, 0);
    }

    void PlanToll(FlareDef f, int n)
    {
        tollPlan.Clear();
        var p = Player;
        var near = HostilesInRadius(p.X, p.Z, flareReach).Where(e => e.Alive && e.State != EnemyState.Dying).ToList();
        var boss = near.Where(e => e.Boss).OrderByDescending(e => e.Hp).FirstOrDefault();
        // The strongest near, weakest first: champions above the rest, then by health.
        var others = near.Where(e => !e.Boss).OrderByDescending(e => e.Elite).ThenByDescending(e => e.Hp).ToList();
        int bossCuts = boss == null ? 0 : Math.Max((int)Math.Round(f.Arg("onBoss", 4) * n / Math.Max(1.0, f.Blows)), n - others.Count);
        var picks = others.Take(n - bossCuts).Reverse().ToList();
        int k = picks.Count;
        for (int i = 0; i < n - bossCuts; i++)
            // Fewer things than cuts: they go round again, the last still on the strongest.
            tollPlan.Add(k == 0 ? -1 : picks[((k - 1 + (i - (n - bossCuts - 1))) % k + k) % k].Id);
        for (int i = 0; i < bossCuts; i++) tollPlan.Add(boss!.Id);
    }

    /* --------------------------------------------------------- Butcher's Hour -- */

    double hourAdded, mistAt;

    /// <summary>Butcher's Hour holds.</summary>
    public bool HourHolds => FlareT > 0 && Flare is { Id: "butchers_hour" };

    /// <summary>Her skills' waits while the Hour holds: twice as fast.</summary>
    public double FlareCooldownMul(WeaponInst w) => HourHolds ? 1 / Math.Max(1, Flare!.Arg("faster", 2)) : 1;

    /// <summary>Each blow of hers while the Hour holds bleeds, and an ordinary thing it leaves below 15% dies.</summary>
    void FlareOnHit(Enemy e, HitOpts o, double dmg)
    {
        if (!HourHolds || o.Dot || o.Summon || (o.Weapon == null && !o.Projectile) || dmg <= 0) return;
        var f = Flare!;
        if (e.Alive && e.State != EnemyState.Dying) ApplyStatus(e, new StatusPayload(StatusKind.Bleed, 1, f.Arg("bleed", 0.4), f.Arg("bleedSeconds", 3)), dmg, o.Depth + 1);
        if (!e.Elite && !e.Boss && e.Alive && e.State != EnemyState.Dying && e.Hp > 0 && e.Hp < e.MaxHp * f.Arg("execute", 0.15))
        {
            KillEnemy(e, true, o.Weapon, o.Depth + 1);
            FlareBlowEvent(f, "execute", false, e.X, e.Z, e, 0, "hitstopExecute");
        }
    }

    /// <summary>A kill: while the Hour holds it adds 0.3 s (Overtime 0.6), at most its own length again, and mends 1%.
    /// A boss falling to the Flare, or while a Stand holds, is the last blow (§3.5).</summary>
    void FlareOnKilled(Enemy e, bool credited)
    {
        if (FlareT <= 0 || Flare is not { } f) return;
        if (e.Boss && !flareKilledBoss && (credit == "flare" || f.Kind == FlareKind.Stand))
        {
            flareKilledBoss = true;
            Events.Emit(new Ev.Flare { Phase = FlarePhase.Kill, Id = f.Id, X = Player.X, Z = Player.Z, TX = e.X, TZ = e.Z, Target = e.Id, Clutch = flareClutch, Stand = f.Kind == FlareKind.Stand });
        }
        if (!credited || f.Id != "butchers_hour") return;
        double add = Math.Min(FlareMod("hour.overtime") ? f.Arg("overtime", 0.6) : f.Arg("extend", 0.3), Math.Max(0, f.Length - hourAdded));
        if (add > 0) { hourAdded += add; FlareT += add; flareLen += add; }
        HealPlayer(MaxHp * f.Arg("mend", 0.01), "flare", true);
    }

    /// <summary>While a Stand holds: Red Mist (lesser things near her flee, twice a second).</summary>
    void FlareStagedTick(FlareDef f, double dt)
    {
        if (f.Id != "butchers_hour" || !FlareMod("hour.red_mist") || Time < mistAt) return;
        mistAt = Time + 0.5;
        var p = Player;
        ForEachHostileInRadius(p.X, p.Z, f.Arg("mistRadius", 5), (e, d) =>
        {
            if (!e.Elite && !e.Boss && e.Alive) ApplyStatus(e, new StatusPayload(StatusKind.Fear, 1, 1, f.Arg("flee", 1.5)), 0);
        });
    }

    /// <summary>Not Today: while the Hour holds she can't fall below 1 health.</summary>
    double FlareNotToday(double dmg) =>
        HourHolds && FlareMod("hour.not_today") ? Math.Min(dmg, Math.Max(0, Player.Hp - 1)) : dmg;
}

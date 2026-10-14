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
    int FlareBlowCount(FlareDef f) => !f.Staged ? f.Blows : f.Id switch
    {
        "bell_of_the_morning" => f.Blows + (FlareMod("bell.fourth_toll") ? 1 : 0),
        "burns_twice" => FlareMod("burns.more_embers") ? (int)f.Arg("moreEmbers", 18) : f.Blows,
        "the_roads_toll" => FlareMod("toll.doubled") ? (int)f.Arg("doubled", 18) : f.Blows,
        "the_branding" => 1,
        "the_long_cut" => FlareMod("long_cut.second_cut") ? 3 : 2,
        "drag_them_under" => 3 + (FlareMod("drag.grinder") ? (int)f.Arg("grinds", 3) : 0),
        "the_butchers_bill" => BillChops(f),
        "one_arrow" => 1 + (int)(FlareMod("arrow.split") ? f.Arg("splitMore", 6) : f.Arg("splits", 3)),
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
        // The Long Cut: the sweep at "first", the cleave, and Second Cut's counter-sweep.
        if (f.Beat.TryGetValue("cleave", out double cleave))
            return n > 2 ? [first, cleave, f.BeatAt("second", 0.85)] : [first, cleave];
        // Drag Them Under: the bite at "first", the knot, Grinder's shreds, the slam.
        if (f.Beat.TryGetValue("knot", out double knot))
        {
            if (n <= 3) return [first, knot, f.BeatAt("slam", 0.77)];
            double gs = f.BeatAt("grindFirst", 0.7), gl = f.BeatAt("grindLast", 0.86);
            return new[] { first, knot }.Concat(Enumerable.Range(0, n - 3).Select(i => n <= 4 ? gs : gs + (gl - gs) * i / (n - 4)))
                .Append(f.BeatAt("slamGrinder", 0.95)).ToArray();
        }
        // The Butcher's Bill: chops "step" apart from "first" (the landing), the last overhead "lastGap" after the one before.
        if (f.Beat.TryGetValue("lastGap", out double gap))
            return Enumerable.Range(0, n).Select(i => first + f.BeatAt("step", 0.06) * Math.Min(i, n - 2) + (i == n - 1 ? gap : 0)).ToArray();
        // One Arrow: the arrow at "first", then its splits spread from "splitFirst" to "splitLast".
        if (f.Beat.TryGetValue("splitFirst", out double sf))
        {
            double sl = f.BeatAt("splitLast", sf);
            return new[] { first }.Concat(Enumerable.Range(0, n - 1).Select(i => n <= 2 ? sf : sf + (sl - sf) * i / (n - 2))).ToArray();
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

    void FlareBlowEvent(FlareDef f, string part, bool last, double tx, double tz, Enemy? target, double radius, string stop = "hitstop", int? hitstop = null) =>
        Events.Emit(new Ev.Flare
        {
            Phase = FlarePhase.Blow, Id = f.Id, X = Player.X, Z = Player.Z, Radius = radius, Blow = flareBlow, Clutch = flareClutch,
            Stand = f.Kind == FlareKind.Stand, Part = part, Last = last, TX = tx, TZ = tz, Target = target?.Id ?? 0,
            Hitstop = hitstop ?? FlareHitstop(f, last, stop),
        });

    /// <summary>The Flare's reach grew (the clutch, Bright Hour, the long night): its parts grow with it.</summary>
    double FlareGrow(FlareDef f) => f.Radius > 0 ? flareReach / f.Radius : 1;

    /// <summary>At the press: what a staged Flare does at once (Butcher's Hour fills Frenzy).</summary>
    void FlareStagedPress(FlareDef f)
    {
        hourAdded = 0;
        mistAt = 0;
        if (f.Id == "the_branding" && f.Staged) BrandingPress();
        if (f.Id == "butchers_hour" && f.Staged) FillFrenzy();
    }

    /* ---------------------------------------------------- Bell of the Morning -- */

    /// <summary>A toll: everything in reach is seared, lesser things stunned, champions and bosses broken from their
    /// channel and staggered; it mends her. The last toll is a holy blast 8 m round (the seared take it harder).</summary>
    void BellToll(FlareDef f, bool last)
    {
        var p = Player;
        double stun = f.Arg("stun", 1), sear = f.Arg("sear", 2), stagger = f.Arg("stagger", 0.15);
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
    /// <summary>Each ember's aim (where it will fall, and on whom; -1 none), taken "aim" seconds before it lands.</summary>
    readonly List<(double X, double Z, int Target)> emberAims = new();
    /// <summary>Called Down's target (an enemy id; -1 none).</summary>
    int calledDown = -1;

    /// <summary>Called Down's choice: the toughest it can hurt (a boss, then champions, then the most health),
    /// frozen first among the rest.</summary>
    Enemy? CalledDownPick(List<Enemy> near) => near.Where(FlareCanHurt)
        .OrderByDescending(e => e.Boss).ThenByDescending(e => e.Elite).ThenByDescending(e => e.Status.Has(StatusKind.Frozen)).ThenByDescending(e => e.Hp)
        .FirstOrDefault();

    /// <summary>The aims' times: "aim" (beat) before each ember lands, never before the frost (they aim at what it froze),
    /// so the view drops each ember out of the sky in time to land on its blow. Only Burns Twice aims today.</summary>
    double[] FlareAimSchedule(FlareDef f)
    {
        // The Bill's leap: she picks the strongest and springs at "leap", landing on the first chop.
        if (f.Staged && f.Id == "the_butchers_bill") return [f.BeatAt("leap", 0.2)];
        if (!f.Staged || f.Id != "burns_twice" || !f.Beat.TryGetValue("aim", out double lead) || lead <= 0) return [];
        bool frosts = f.Beat.TryGetValue("frost", out double frost);
        return flareAt.Skip(frosts ? 1 : 0).Select(t => Math.Max(frosts ? frost : 0, t - lead)).ToArray();
    }

    /// <summary>One aim: where the next ember will fall, chosen now (an Ev.Flare Blow, Part "aim", no hitstop).</summary>
    void FlareAim()
    {
        var f = Flare!;
        flareAim++;
        if (f.Id == "the_butchers_bill") { BillAim(f); return; }
        if (f.Id != "burns_twice") return;
        int embers = flareAimAt.Length;
        double r = f.Arg("emberRadius", 2.5) * FlareGrow(f);
        var (tx, tz, target) = EmberPick(f, flareAim, embers, r);
        emberFell.Add((tx, tz));
        emberAims.Add((tx, tz, target?.Id ?? -1));
        FlareBlowEvent(f, "aim", flareAim == embers, tx, tz, target, r, hitstop: 0);
    }

    /// <summary>Where an ember falls: on the boss when it is one of the boss's own (four of twelve, evenly), on Called
    /// Down's target, else on the thickest frozen pack not yet struck or aimed at; with nothing near, on open ground.</summary>
    (double X, double Z, Enemy? Target) EmberPick(FlareDef f, int ember, int embers, double r)
    {
        var p = Player;
        var near = HostilesInRadius(p.X, p.Z, flareReach).Where(e => e.Alive && e.State != EnemyState.Dying).ToList();
        // A boss it can't hurt now (shut, or pinned at its gate with its Break full) is passed over.
        var boss = near.Where(e => e.Boss && FlareCanHurt(e)).OrderByDescending(e => e.Hp).FirstOrDefault();
        int onBoss = (int)f.Arg("onBoss", 4);
        // Four of twelve seek the boss, evenly (the third, sixth, ninth and twelfth).
        bool seek = boss != null && ember * onBoss / Math.Max(1, embers) > (ember - 1) * onBoss / Math.Max(1, embers);
        Enemy? target = null;
        if (FlareMod("burns.called_down"))
        {
            // Called Down keeps the target it chose at the frost, and when that falls moves to the next toughest.
            var held = calledDown >= 0 && calledDown < Enemies.Items.Length ? Enemies.Items[calledDown] : null;
            target = held != null && near.Contains(held) && FlareCanHurt(held) ? held : CalledDownPick(near);
            calledDown = target?.Id ?? -1;
        }
        else if (seek) target = boss;
        if (target == null)
        {
            // The thickest frozen pack not yet struck; then anything frozen; then the thickest pack at all.
            bool Struck(Enemy e) => emberFell.Any(q => Dist(q.X, q.Z, e.X, e.Z) < r);
            // An ember already falling will shatter the ice round its aim: aimed ahead, count that ice as broken, as it
            // was when each ember chose at landing (without this a press killed 5 points fewer, 13 October).
            var falling = emberAims.Skip(Math.Max(0, flareBlow - (f.Beat.ContainsKey("frost") ? 1 : 0))).ToList();
            bool Iced(Enemy e) => e.Status.Has(StatusKind.Frozen) && !falling.Any(q => Dist(q.X, q.Z, e.X, e.Z) < r);
            int Pack(Enemy e) => near.Count(o => Iced(o) && Dist(o.X, o.Z, e.X, e.Z) < r);
            var frozen = near.Where(e => !e.Boss && Iced(e)).ToList();
            target = frozen.Where(e => !Struck(e)).OrderByDescending(Pack).FirstOrDefault()
                ?? frozen.OrderByDescending(Pack).FirstOrDefault()
                ?? near.Where(e => !e.Boss).OrderByDescending(e => near.Count(o => Dist(o.X, o.Z, e.X, e.Z) < r)).FirstOrDefault();
            // Nothing else near: it falls on open ground round her, and a lone boss still takes only its four.
        }
        return (target?.X ?? p.X + Math.Cos(ember * 2.4) * flareReach * 0.5, target?.Z ?? p.Z + Math.Sin(ember * 2.4) * flareReach * 0.5, target);
    }

    /// <summary>The frost (everything in reach frozen, a boss chilled), then each ember: it lands where it was aimed (on
    /// its target where that has stepped, while it stands), shatters what is frozen round it, and burns. The last is
    /// the BOOM: what still stands in reach is thrown back from it and staggered.</summary>
    void BurnsTwiceBlow(FlareDef f, bool last)
    {
        var p = Player;
        if (flareBlow == 1 && f.Beat.ContainsKey("frost"))
        {
            emberFell.Clear();
            emberAims.Clear();
            ForEachHostileInRadius(p.X, p.Z, flareReach, (e, d) =>
            {
                FlareHit(e, f.Arg("frost", 0.3), School.Frost, 0, p.X, p.Z);
                if (!e.Alive || e.State == EnemyState.Dying) return;
                if (e.Boss) ApplyStatus(e, new StatusPayload(StatusKind.Chill, 1, 1, f.Arg("chill", 3)), 0);
                else Freeze(e, f.Arg("freeze", 2));
            });
            calledDown = FlareMod("burns.called_down")
                ? CalledDownPick(HostilesInRadius(p.X, p.Z, flareReach).Where(e => e.Alive && e.State != EnemyState.Dying).ToList())?.Id ?? -1 : -1;
            // The first impact lands harder than an ember (hitstopFrost, 3 frames).
            FlareBlowEvent(f, "frost", false, p.X, p.Z, null, flareReach, f.Beat.ContainsKey("hitstopFrost") ? "hitstopFrost" : "hitstop");
            return;
        }
        int embers = flareAt.Length - (f.Beat.ContainsKey("frost") ? 1 : 0), ember = flareBlow - (flareAt.Length - embers);
        double r = f.Arg("emberRadius", 2.5) * FlareGrow(f);
        double tx, tz;
        Enemy? target;
        if (ember - 1 < emberAims.Count)
        {
            // Aimed: it follows its target while that stands (a frozen one hasn't moved; a chilled boss has stepped),
            // else it lands where it was aimed. A slot re-used by a new thing far from the aim is not its target.
            var (ax, az, id) = emberAims[ember - 1];
            var held = id >= 0 && id < Enemies.Items.Length ? Enemies.Items[id] : null;
            target = held != null && held.Alive && held.State != EnemyState.Dying && FlareCanHurt(held) && Dist(held.X, held.Z, ax, az) < r + 2 ? held : null;
            // Its target fell while it fell (an ember aimed four ahead, 13 October: 23 of 360 fell on nothing, a press
            // killed 5 points fewer): it bends to the thickest pack still standing near its aim, never a boss.
            if (target == null && id >= 0)
            {
                var near = HostilesInRadius(ax, az, r + f.Arg("aimBend", 3)).Where(e => e.Alive && e.State != EnemyState.Dying && !e.Boss).ToList();
                target = near.OrderByDescending(e => near.Count(o => Dist(o.X, o.Z, e.X, e.Z) < r)).ThenBy(e => Dist(e.X, e.Z, ax, az)).FirstOrDefault();
            }
            tx = target?.X ?? ax;
            tz = target?.Z ?? az;
        }
        else
        {
            (tx, tz, target) = EmberPick(f, ember, embers, r);
            emberFell.Add((tx, tz));
        }
        ForEachHostileInRadius(tx, tz, r, (e, d) =>
        {
            // A boss takes only the embers that seek it (four of twelve): those that fall on the packs round it pass it
            // by, or a boss in a crowd took the whole sky (four times the plain form's three blows).
            if (e.Boss && e != target) return;
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
        if (last) BurnsShove(f, tx, tz);
    }

    /// <summary>The BOOM's shock: everything still standing in reach is thrown back from where the last ember fell
    /// ("shove" metres, less for the heavy and champions; a boss only staggers) and staggered for a breath, so the
    /// room visibly clears even when little died. No damage. One Ev.Flare Blow, Part "shove", per thing: TX/TZ where
    /// it should come to rest (a wall may stop it short), Radius how far.</summary>
    void BurnsShove(FlareDef f, double bx, double bz)
    {
        var p = Player;
        double far = f.Arg("shove", 3) * FlareGrow(f);
        foreach (var e in HostilesInRadius(p.X, p.Z, flareReach).Where(e => e.Alive && e.State != EnemyState.Dying).ToList())
        {
            if (e.Boss)
            {
                AddStagger(e, f.Arg("shoveStagger", 0.15));
                FlareBlowEvent(f, "shove", false, e.X, e.Z, e, 0, hitstop: 0);
                continue;
            }
            double dist = e.Def.Behavior == Behavior.Stationary ? 0 : far * Math.Clamp(2 / Math.Max(0.5, e.Mass), 0.4, 1) * (e.Elite ? 0.5 : 1);
            // Away from the blast; one standing in it goes away from her, and one on her too, along her facing.
            double dx = e.X - bx, dz = e.Z - bz, d = Len(dx, dz);
            if (d < 0.3) { dx = e.X - p.X; dz = e.Z - p.Z; d = Len(dx, dz); }
            if (d < 0.3) { dx = Math.Sin(p.Facing); dz = Math.Cos(p.Facing); d = 1; }
            // Knockback slides and settles at 9 per second (Ai.cs): a slide of v/9 metres.
            e.Kbx += dx / d * dist * 9;
            e.Kbz += dz / d * dist * 9;
            if (e.Elite) Interrupt(e);
            ApplyStatus(e, new StatusPayload(StatusKind.Stun, 1, 1, f.Arg("shoveStun", 0.5)), 0);
            FlareBlowEvent(f, "shove", false, e.X + dx / d * dist, e.Z + dz / d * dist, e, dist, hitstop: 0);
        }
    }

    /* -------------------------------------------------------- The Road's Toll -- */

    readonly List<int> tollPlan = new();
    /// <summary>Each boss cut's share of a blow: the boss's cuts carry a fixed worth between them (four cuts, "onBoss";
    /// grown with Toll Doubled), so what a boss takes doesn't swing threefold with how many things stand round it.</summary>
    double tollBossShare = 1;

    /// <summary>A boss a staged Flare can hurt: not shut against all harm, nor pinned at its phase's gate with its Break
    /// already full (the tenth of its health the Break rewards). The Toll's cuts and Burns' embers go to what's round it.</summary>
    bool FlareCanHurt(Enemy e) => !e.Boss || (e.TakenMul > 0 && !(e.HpFloor > 0 && e.Hp <= e.HpFloor && e.Overflow >= 0.1 * e.MaxHp));

    /// <summary>A cut. At the first she picks her twelve: the strongest near, weakest first so the last falls on the
    /// strongest; on a boss its last four (a third of them). Each cut poisons, and what it leaves below a quarter of
    /// its health dies (a boss never). A target fallen before its cut gives it to the strongest still standing. The
    /// poison is the Flare's (its ticks are credited to it).</summary>
    void TollCut(FlareDef f, bool last)
    {
        var p = Player;
        int n = flareAt.Length;
        if (flareBlow == 1) PlanToll(f, n);
        int slot = flareBlow - 1 < tollPlan.Count ? tollPlan[flareBlow - 1] : -1;
        Enemy? e = slot >= 0 && slot < Enemies.Items.Length ? Enemies.Items[slot] : null;
        if (e == null || !e.Alive || e.State == EnemyState.Dying || !Targetable(e) || !FlareCanHurt(e))
        {
            var near = HostilesInRadius(p.X, p.Z, flareReach).Where(x => x.Alive && x.State != EnemyState.Dying).ToList();
            // A boss that can't be hurt now is passed over while anything else stands near, and a re-picked cut
            // goes to the boss last: the plan already gave it its worth.
            e = (near.Any(FlareCanHurt) ? near.Where(FlareCanHurt) : near)
                .OrderBy(x => x.Boss).ThenByDescending(x => x.Elite).ThenByDescending(x => x.Hp).FirstOrDefault();
        }
        if (e != null)
        {
            // A planned boss cut carries its share of the boss's worth; a re-picked one a plain boss cut's (onBoss of Blows).
            double share = !e.Boss ? 1 : e.Id == slot ? tollBossShare : f.Arg("onBoss", 4) / Math.Max(1.0, f.Blows);
            double dealt = FlareHit(e, share, f.School, 0, p.X, p.Z);
            if (e.Alive && e.State != EnemyState.Dying)
            {
                TollVenom(e, dealt, f);
                double below = last && FlareMod("toll.last_cut") ? f.Arg("lastCut", 0.4) : f.Arg("execute", 0.25);
                if (!e.Boss && e.Alive && e.State != EnemyState.Dying && e.Hp < e.MaxHp * below) KillEnemy(e, true, null);
            }
        }
        if (e != null) FlareBlowEvent(f, "cut", last, e.X, e.Z, e, 0);
        else
        {
            // Nothing near: she cuts the air along her aim, a kata zigzagging out to two thirds of her reach and
            // closing on her aim at the last (FLARE_LOOK "Empty"). From the blow number, not the sim's dice.
            double k = (double)flareBlow / Math.Max(1, n), side = last ? 0 : flareBlow % 2 == 0 ? 1 : -1;
            double a = flareAngle + side * f.Arg("emptyFan", 0.45) * (1 - 0.5 * k), d = flareReach * (0.2 + 0.47 * k);
            FlareBlowEvent(f, "cut", last, p.X + Math.Cos(a) * d, p.Z + Math.Sin(a) * d, null, f.Arg("emptyRadius", 1.5));
        }
    }

    /// <summary>The cut's poison: half its damage again over 4 s, the Flare's own. It marks the thing poisoned (a stack at
    /// the poison it already carries) but never lifts her poison's strength: a stack of hers ticks at its strongest
    /// poison's rate, so a cut's rate on it made her whole stack the Flare's (70% of a boss at T4, 12 October).</summary>
    void TollVenom(Enemy e, double dealt, FlareDef f)
    {
        ApplyStatus(e, new StatusPayload(StatusKind.Poison, 1, 0, f.Arg("poisonSeconds", 4)), 0, from: "flare");
        double sd = Stats.Get(Stat.StatusDamage) * Stats.Get(Stat.StatusDamageOf(StatusKind.Poison));
        double ticks = Math.Max(1, Math.Round(f.Arg("poisonSeconds", 4) / 0.5));
        if (dealt > 0) venom.Add(new TollPoison(e.Id, dealt * f.Arg("poison", 0.5) * sd / ticks, (int)ticks, Time + 0.5));
    }

    sealed class TollPoison(int target, double tick, int left, double next)
    {
        public readonly int Target = target;
        public readonly double Tick = tick;
        public int Left = left;
        public double Next = next;
    }
    readonly List<TollPoison> venom = new();

    /// <summary>The Toll's poisons tick every half second as the Flare's, after the Flare has ended too.</summary>
    void TickVenom()
    {
        if (venom.Count == 0) return;
        var was = credit;
        credit = "flare";
        for (int i = venom.Count - 1; i >= 0; i--)
        {
            var v = venom[i];
            var e = v.Target >= 0 && v.Target < Enemies.Items.Length ? Enemies.Items[v.Target] : null;
            if (e == null || !e.Alive || e.State == EnemyState.Dying) { venom.RemoveAt(i); continue; }
            if (Time < v.Next) continue;
            v.Next += 0.5;
            v.Left--;
            HitEnemy(e, v.Tick, School.Nature, DotPoison, new HitOpts { Dot = true, NoCrit = true, NoProcs = true, Depth = 2, Credit = "flare" });
            if (v.Left <= 0) venom.RemoveAt(i);
        }
        credit = was;
    }

    void PlanToll(FlareDef f, int n)
    {
        tollPlan.Clear();
        var p = Player;
        var near = HostilesInRadius(p.X, p.Z, flareReach).Where(e => e.Alive && e.State != EnemyState.Dying).ToList();
        var boss = near.Where(e => e.Boss && FlareCanHurt(e)).OrderByDescending(e => e.Hp).FirstOrDefault();
        // The strongest near, weakest first: champions above the rest, then by health.
        var others = near.Where(e => !e.Boss).OrderByDescending(e => e.Elite).ThenByDescending(e => e.Hp).ToList();
        int bossCuts = boss == null ? 0 : Math.Max((int)Math.Round(f.Arg("onBoss", 4) * n / Math.Max(1.0, f.Blows)), n - others.Count);
        var picks = others.Take(n - bossCuts).Reverse().ToList();
        int k = picks.Count;
        for (int i = 0; i < n - bossCuts; i++)
            // Fewer things than cuts: they go round again, the last still on the strongest.
            tollPlan.Add(k == 0 ? -1 : picks[((k - 1 + (i - (n - bossCuts - 1))) % k + k) % k].Id);
        for (int i = 0; i < bossCuts; i++) tollPlan.Add(boss!.Id);
        // The boss's cuts carry a fixed worth between them ("bossWorth" blows, grown with Toll Doubled), however many.
        // Four cuts' worth: at 2100 a cut, what the plain form's twelve 700s gave everything in reach.
        tollBossShare = bossCuts > 0 ? f.Arg("bossWorth", f.Arg("onBoss", 4)) * n / Math.Max(1.0, f.Blows) / bossCuts : 1;
    }

    /* --------------------------------------------------------- Butcher's Hour -- */

    double hourAdded, mistAt;

    /// <summary>Butcher's Hour holds.</summary>
    public bool HourHolds => FlareT > 0 && Flare is { Id: "butchers_hour", Staged: true };

    /// <summary>Her skills' waits while the Hour holds: twice as fast.</summary>
    public double FlareCooldownMul(WeaponInst w) => HourHolds ? 1 / Math.Max(1, Flare!.Arg("faster", 2)) : 1;

    /// <summary>Each blow of hers while the Hour holds bleeds (with "deepen", each cut deepens the wound, up to 5 deep),
    /// and an ordinary thing it leaves below 15% dies.</summary>
    void FlareOnHit(Enemy e, HitOpts o, double dmg)
    {
        if (!HourHolds || o.Dot || o.Summon || (o.Weapon == null && !o.Projectile) || dmg <= 0) return;
        var f = Flare!;
        if (e.Alive && e.State != EnemyState.Dying) ApplyStatus(e, new StatusPayload(StatusKind.Bleed, 1, f.Arg("bleed", 0.4), f.Arg("bleedSeconds", 3), f.Arg("deepen", 0) > 0), dmg, o.Depth + 1);
        if (!e.Elite && !e.Boss && e.Alive && e.State != EnemyState.Dying && e.Hp > 0 && e.Hp < e.MaxHp * f.Arg("execute", 0.15))
        {
            KillEnemy(e, true, o.Weapon, o.Depth + 1);
            FlareBlowEvent(f, "execute", false, e.X, e.Z, e, 0, "hitstopExecute");
        }
    }

    /// <summary>A kill: while the Hour holds it adds 0.3 s (Overtime 0.6), at most 8 s more (Overtime 12), and mends 1%.
    /// A boss falling to the Flare, or while a Stand holds, is the last blow (§3.5); so is one the Toll's poison
    /// finishes after the Strike has ended.</summary>
    void FlareOnKilled(Enemy e, bool credited)
    {
        if (Flare is not { } f) return;
        if (e.Boss && !flareKilledBoss && (credit == "flare" || (FlareT > 0 && f.Kind == FlareKind.Stand)))
        {
            flareKilledBoss = true;
            Events.Emit(new Ev.Flare { Phase = FlarePhase.Kill, Id = f.Id, X = Player.X, Z = Player.Z, TX = e.X, TZ = e.Z, Target = e.Id, Clutch = flareClutch, Stand = f.Kind == FlareKind.Stand });
        }
        BrandOnKilled(e);
        BillOnKilled(e, credited);
        if (!credited || !HourHolds) return;
        bool over = FlareMod("hour.overtime");
        double cap = over ? f.Arg("overtimeCap", 12) : f.Arg("extendCap", 8);
        double add = Math.Min(over ? f.Arg("overtime", 0.6) : f.Arg("extend", 0.3), Math.Max(0, cap - hourAdded));
        if (add > 0) { hourAdded += add; FlareT += add; flareLen += add; }
        HealPlayer(MaxHp * f.Arg("mend", 0.01), "flare", true);
    }

    /// <summary>While a Stand holds: Red Mist (lesser things near her flee, twice a second).</summary>
    void FlareStagedTick(FlareDef f, double dt)
    {
        if (!HourHolds || !FlareMod("hour.red_mist") || Time < mistAt) return;
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

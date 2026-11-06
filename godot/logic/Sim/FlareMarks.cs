using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Sim;

/// <summary>One foe a Strike Flare will hit (H7: "no indicator of what it's hitting"). Id: its slot; X/Z where it stands;
/// Radius its size; Main: the one the cast is about (the hovered Priority foe when it is marked, else the Flare's own
/// chosen main target), at most one.</summary>
public readonly record struct FlareMark(int Id, double X, double Z, double Radius, bool Main);

public enum FlareMarkShapeKind { Circle, Line }

/// <summary>Where the cast's remaining blows can strike. Circle: X/Z its centre, Radius. Line: X/Z its origin, Angle (radians,
/// atan2(z, x) as Ev.Flare's), Length, Radius its half-width.</summary>
public readonly record struct FlareMarkShape(FlareMarkShapeKind Kind, double X, double Z, double Radius, double Angle = 0, double Length = 0);

/* H7, the Flare's marks: a pure predictor per staged Strike that mirrors its own queries for its REMAINING blows (what is
 * in reach, on the line, the planned picks), read by the view every frame. It reads and never writes the fight: no dice,
 * no state but its own lists (FlareMarksOn = false skips it, and the fight ends the same). Live from a Strike's press until
 * its last blow's hits are done (The Branding: until its bursts, passes and Second Brand are done); empty otherwise
 * (Stands get none). The proof: every FlareHit in a cast on a foe not shown on an earlier tick counts in FlareLateMarks
 * (and is marked at once); a target the sim re-picks at the blow itself (a Toll cut's target fell, the Bill's vault, an
 * ember bending off a fallen target), when no earlier tick could show it, is marked at that decision and counts in
 * FlareDecisionMarks instead. Hits after the cast (the Toll's venom, Line of Morning's fires, the Eye's bursts after the
 * window, a brand of an earlier cast bursting outside one) are after-effects and outside the count. */
public sealed partial class Battle
{
    /// <summary>The marks' switch (the determinism test turns it off: the fight must end the same).</summary>
    public bool FlareMarksOn = true;
    readonly List<FlareMark> flareMarks = new();
    readonly List<FlareMarkShape> flareMarkShapes = new();
    /// <summary>Every foe the casting Strike's remaining blows will hit (see the file's note).</summary>
    public IReadOnlyList<FlareMark> FlareMarks => flareMarks;
    /// <summary>Where the remaining blows strike: the Long Cut has both, its sweep's circle and its cleave's line.</summary>
    public IReadOnlyList<FlareMarkShape> FlareMarkShapes => flareMarkShapes;
    /// <summary>Bumped when the marked set (ids or the Main) changes; positions move every tick without a bump.</summary>
    public int FlareMarksVersion;
    /// <summary>Whether a Strike's marks are live (press to its last hit).</summary>
    public bool FlareMarksLive => markCast;
    /// <summary>The proof (cumulative over the fight): hits in a cast on a foe no earlier tick had marked; marks made at a
    /// same-tick decision of the sim (a re-pick), which the view shows by holding that hit a frame.</summary>
    public int FlareLateMarks, FlareDecisionMarks;
    /// <summary>The last cast's foes ever marked, and of them never hit by it (set when the cast ends; reset at each press).</summary>
    public int FlareMarkedCount, FlareMarkedUnhit;
    /// <summary>Whether the cast (the last one, once it ends) has hit this foe slot (the view's marks pop on a hit, fade if never).</summary>
    public bool FlareWasHit(int id) => id >= 0 && id < Enemies.Items.Length && Enemies.Items[id] is { } e && markHit.Contains(e);

    bool markCast;
    double markDt = 1 / 30.0;
    Enemy? markMain;
    readonly List<Enemy> markWork = new();
    readonly HashSet<Enemy> markWorkSet = new(), markShown = new(), markEver = new(), markHit = new();
    readonly List<int> markPlan = new(), markPlan2 = new();
    readonly List<(double X, double Z)> markFell = new();
    readonly List<(double X, double Z, int Target)> markAims = new();

    /* ------------------------------------------------------------------- the cast -- */

    /// <summary>At a Strike's press (UseFlare): the marks go live and are shown at once.</summary>
    void FlareMarksPress(FlareDef f)
    {
        if (markCast) FlareMarksEnd();
        if (!FlareMarksOn || f.Kind != FlareKind.Strike) return;
        markCast = true;
        markEver.Clear();
        markHit.Clear();
        markShown.Clear();
        FlareMarkedCount = FlareMarkedUnhit = 0;
        MarksRecompute(true);
    }

    /// <summary>At the end of every tick (after the creatures have moved): the marks the view shows until the next.</summary>
    void FlareMarksTick(double dt)
    {
        if (dt > 0) markDt = dt;
        if (!markCast) return;
        bool branding = Flare is { Id: "the_branding", Staged: true };
        if (Flare == null || (branding ? flareBlow >= flareAt.Length && brands.Count == 0 && secondBrandAt <= 0 : FlareT <= 0))
        {
            FlareMarksEnd();
            return;
        }
        MarksRecompute(true);
    }

    /// <summary>After a Strike's last blow (FlareBlow), or its window closing: the tally, then nothing marked.</summary>
    void FlareMarksEnd()
    {
        if (!markCast) return;
        markCast = false;
        FlareMarkedCount = markEver.Count;
        FlareMarkedUnhit = markEver.Count(e => !markHit.Contains(e));
        flareMarks.Clear();
        flareMarkShapes.Clear();
        markShown.Clear();
        FlareMarksVersion++;
    }

    /// <summary>The safety net (FlareHit): a hit in a cast on a foe no earlier tick showed is late, and is marked at once.</summary>
    void FlareMarkHit(Enemy e)
    {
        if (!markCast) return;
        markHit.Add(e);
        if (markShown.Contains(e)) return;
        FlareLateMarks++;
        MarkAt(e);
    }

    /// <summary>A target the sim re-picks at the blow itself: marked at the decision (before its hit) when no earlier tick did.</summary>
    void FlareDecide(Enemy? e)
    {
        if (!markCast || e == null || markShown.Contains(e)) return;
        FlareDecisionMarks++;
        MarkAt(e);
    }

    /// <summary>FlareDecide for what a re-picked blow strikes round (x, z).</summary>
    void FlareDecideAround(double x, double z, double r, Func<Enemy, bool>? keep = null)
    {
        if (!markCast) return;
        foreach (var e in HostilesInRadius(x, z, r))
            if (keep == null || keep(e)) FlareDecide(e);
    }

    void MarkAt(Enemy e)
    {
        markShown.Add(e);
        markEver.Add(e);
        flareMarks.Add(new FlareMark(e.Id, e.X, e.Z, e.Radius, false));
        FlareMarksVersion++;
    }

    /// <summary>The predictor's run: "publish" (the press, a tick's end) makes it the set the view shows, the one the
    /// safety net reads; a run before a blow or an aim only refreshes the list.</summary>
    void MarksRecompute(bool publish)
    {
        if (!markCast || Flare is not { } f) return;
        markWork.Clear();
        markWorkSet.Clear();
        flareMarkShapes.Clear();
        markMain = null;
        markSoon = MarkHitSoon();
        var p = Player;
        switch (f.Staged ? f.Id : "")
        {
            case "bell_of_the_morning": MarkBell(f); break;
            case "burns_twice": MarkBurns(f); break;
            case "the_roads_toll": MarkToll(f); break;
            case "the_branding": MarkBranding(f); break;
            case "the_long_cut": MarkLongCut(f); break;
            case "one_arrow": MarkArrow(f); break;
            case "drag_them_under": MarkDrag(f); break;
            case "the_butchers_bill": MarkBill(f); break;
            default:
                if (flareBlow < flareAt.Length) { MarkCircle(p.X, p.Z, flareReach); Shape(p.X, p.Z, flareReach); }
                break;
        }
        var pri = Priority >= 0 && Priority < Enemies.Items.Length ? Enemies.Items[Priority] : null;
        var main = pri != null && markWorkSet.Contains(pri) ? pri : markMain != null && markWorkSet.Contains(markMain) ? markMain : null;
        bool same = flareMarks.Count == markWork.Count;
        for (int i = 0; same && i < markWork.Count; i++)
            same = flareMarks[i].Id == markWork[i].Id && flareMarks[i].Main == (markWork[i] == main);
        flareMarks.Clear();
        foreach (var e in markWork) flareMarks.Add(new FlareMark(e.Id, e.X, e.Z, e.Radius, e == main));
        if (!same) FlareMarksVersion++;
        if (!publish) return;
        markShown.Clear();
        foreach (var e in markWork) { markShown.Add(e); markEver.Add(e); }
    }

    /* ------------------------------------------------------------------ the pieces -- */

    /// <summary>The marks' margin for a blow due within the next tick or two. A tick runs the Flare's blows before the creatures
    /// move (Battle.Tick: TickFlare, then Ai), so what the marks see at a tick's end is where things stand at the next
    /// tick's blows: the margin only guards a shove between (a pull of hers in the same tick) and the rounding. Further
    /// off, blows are marked where things stand now (a margin there marked the line's edges and went unhit).</summary>
    double MarkSlack(Enemy e) => markSoon ? MarkMargin : 0;

    public const double MarkMargin = 0.05;

    /// <summary>Whether the cast's next hit is due within two ticks (its next blow, a brand's burst, Second Brand).</summary>
    bool markSoon;

    bool MarkHitSoon()
    {
        double soon = 2 * markDt + 1e-9, elapsed = flareLen - FlareT;
        if (flareBlow < flareAt.Length && flareAt[flareBlow] - elapsed <= soon) return true;
        if (secondBrandAt > 0 && secondBrandAt - Time <= soon) return true;
        foreach (var br in brands) if (!br.Done && br.At - Time <= soon) return true;
        return false;
    }

    /// <summary>HostilesInRadius as the next tick will find it: its grid is rebuilt from where things stand now (the creatures
    /// move after the Flare's blows), and a pick that ties (a pack at full health) falls to that grid's order: its cells
    /// row by row, the higher slot first within one.</summary>
    List<Enemy> NextTickHostiles(double x, double z, double r)
    {
        double h = Spatial.Size / 2, cell = Spatial.Cell;
        int cols = (int)Math.Ceiling(Spatial.Size / cell);
        int x0 = Math.Max(0, (int)Math.Floor((x - r + h) / cell)), x1 = Math.Min(cols - 1, (int)Math.Floor((x + r + h) / cell));
        int z0 = Math.Max(0, (int)Math.Floor((z - r + h) / cell)), z1 = Math.Min(cols - 1, (int)Math.Floor((z + r + h) / cell));
        var o = new List<(Enemy E, int C)>();
        foreach (var e in HostilesInRadius(x, z, r + 2 * cell))
        {
            int cx = (int)Math.Floor((e.X + h) / cell), cz = (int)Math.Floor((e.Z + h) / cell);
            if (cx < x0 || cx > x1 || cz < z0 || cz > z1) continue;
            if ((e.X - x) * (e.X - x) + (e.Z - z) * (e.Z - z) <= (r + e.Radius) * (r + e.Radius)) o.Add((e, cz * cols + cx));
        }
        return o.OrderBy(t => t.C).ThenByDescending(t => t.E.Id).Select(t => t.E).ToList();
    }

    static bool Standing(Enemy e) => e.Alive && e.State != EnemyState.Dying;

    void Mark(Enemy? e)
    {
        if (e != null && Standing(e) && markWorkSet.Add(e)) markWork.Add(e);
    }

    void Shape(double x, double z, double r) => flareMarkShapes.Add(new FlareMarkShape(FlareMarkShapeKind.Circle, x, z, r));

    /// <summary>What ForEachHostileInRadius(x, z, r) finds, and what may step into it before the blow.</summary>
    void MarkCircle(double x, double z, double r, Func<Enemy, bool>? keep = null)
    {
        foreach (var e in HostilesInRadius(x, z, r + 2))
            if (Standing(e) && (keep == null || keep(e)) && Dist(e.X, e.Z, x, z) <= r + e.Radius + MarkSlack(e)) Mark(e);
    }

    /// <summary>What LineHostiles finds (less one: a split passes the thing it leaves), and what may step into it.</summary>
    void MarkLine(double ox, double oz, double ang, double len, double half, int skip = -1)
    {
        flareMarkShapes.Add(new FlareMarkShape(FlareMarkShapeKind.Line, ox, oz, half, ang, len));
        double dx = Math.Cos(ang), dz = Math.Sin(ang);
        foreach (var e in HostilesInRadius(ox + dx * len / 2, oz + dz * len / 2, len / 2 + half + 4))
        {
            if (!Standing(e) || e.Id == skip) continue;
            double s = MarkSlack(e), rx = e.X - ox, rz = e.Z - oz, along = rx * dx + rz * dz, perp = Math.Abs(-rx * dz + rz * dx);
            if (along >= -e.Radius - s && along <= len + e.Radius + s && perp <= half + e.Radius + s) Mark(e);
        }
    }

    double MarkSlackMost() => markSoon ? MarkMargin : 0;

    /* ------------------------------------------------------------- per Strike -- */

    void MarkBell(FlareDef f)
    {
        if (flareBlow >= flareAt.Length) return;
        var p = Player;
        double r = f.Arg("blastRadius", 8) * FlareGrow(f);
        MarkCircle(p.X, p.Z, flareReach);
        Shape(p.X, p.Z, flareReach);
        MarkCircle(p.X, p.Z, r);
        Shape(p.X, p.Z, r);
    }

    void MarkLongCut(FlareDef f)
    {
        var p = Player;
        if (flareBlow < 1 || (flareAt.Length > 2 && flareBlow < 3)) { MarkCircle(p.X, p.Z, flareReach); Shape(p.X, p.Z, flareReach); }
        if (flareBlow >= 2) return;
        bool wall = FlareMod("long_cut.through_the_wall");
        double len = (wall ? f.Arg("wall", 36) : f.Arg("line", 24)) * FlareGrow(f), half = f.Arg("lineWidth", 1.5) * FlareGrow(f);
        MarkLine(p.X, p.Z, flareAngle, len, half);
        markMain = LineHostiles(p.X, p.Z, flareAngle, len, half).Select(x => x.E).FirstOrDefault(e => e.Boss);
    }

    void MarkBurns(FlareDef f)
    {
        var p = Player;
        bool frosts = f.Beat.ContainsKey("frost");
        int off = frosts ? 1 : 0, embers = flareAt.Length - off;
        double r = f.Arg("emberRadius", 2.5) * FlareGrow(f);
        bool before = frosts && flareBlow == 0;
        if (before) { MarkCircle(p.X, p.Z, flareReach); Shape(p.X, p.Z, flareReach); }
        int landed = Math.Max(0, flareBlow - off);
        if (landed >= embers) return;
        Enemy? last = null;
        void Ember(double tx, double tz, Enemy? target)
        {
            MarkCircle(tx, tz, r, e => !e.Boss || e == target);
            Mark(target);
            Shape(tx, tz, r);
            last = target;
        }
        // Aimed and falling: where BurnsTwiceBlow will land each (on its target where it stands, bent off a fallen one).
        var aims = before ? new List<(double X, double Z, int Target)>() : emberAims;
        for (int j = landed; j < aims.Count && j < embers; j++)
        {
            var (ax, az, id) = aims[j];
            var held = id >= 0 && id < Enemies.Items.Length ? Enemies.Items[id] : null;
            var target = held != null && Standing(held) && FlareCanHurt(held) && Dist(held.X, held.Z, ax, az) < r + 2 ? held : null;
            if (target == null && id >= 0) target = EmberBend(f, ax, az, r);
            Ember(target?.X ?? ax, target?.Z ?? az, target);
        }
        // Not yet aimed: EmberPick run ahead on copies (before the frost, what is in reach counts as the ice it will be).
        markFell.Clear();
        markAims.Clear();
        if (!before) { markFell.AddRange(emberFell); markAims.AddRange(emberAims); }
        int called = before
            ? FlareMod("burns.called_down") ? CalledDownPick(HostilesInRadius(p.X, p.Z, flareReach).Where(Standing).ToList())?.Id ?? -1 : -1
            : calledDown;
        Func<Enemy, bool>? ice = before ? e => !e.Boss && Dist(e.X, e.Z, p.X, p.Z) <= flareReach + e.Radius : null;
        bool aimed = flareAimAt.Length > 0;
        for (int k = aimed ? Math.Max(flareAim, aims.Count) : landed; k < embers; k++)
        {
            int done = flareBlow;
            if (aimed) while (done < flareAt.Length && flareAt[done] <= flareAimAt[Math.Min(k, flareAimAt.Length - 1)] + 1e-9) done++;
            else done = off + k;
            var (tx, tz, target) = EmberPickFrom(f, k + 1, embers, r, markFell, markAims, done, ref called, ice);
            markFell.Add((tx, tz));
            markAims.Add((tx, tz, target?.Id ?? -1));
            Ember(tx, tz, target);
        }
        if (FlareMod("burns.black_ice"))
            MarkCircle(p.X, p.Z, flareReach, e => (before ? !e.Boss : e.Status.Has(StatusKind.Frozen)) && e.Hp < e.MaxHp * f.Arg("blackIce", 0.5));
        markMain = last;
    }

    /// <summary>BurnsTwiceBlow's bend: an ember whose target fell lands on the thickest pack still standing near its aim.</summary>
    Enemy? EmberBend(FlareDef f, double ax, double az, double r)
    {
        var near = HostilesInRadius(ax, az, r + f.Arg("aimBend", 3)).Where(e => Standing(e) && !e.Boss).ToList();
        return near.OrderByDescending(e => near.Count(o => Dist(o.X, o.Z, e.X, e.Z) < r)).ThenBy(e => Dist(e.X, e.Z, ax, az)).FirstOrDefault();
    }

    void MarkToll(FlareDef f)
    {
        var p = Player;
        int n = flareAt.Length;
        if (flareBlow >= n) return;
        Shape(p.X, p.Z, flareReach);
        // With the first cut near, the plan PlanToll would make with what may step into reach or out of it.
        double s = MarkSlackMost();
        if (flareBlow == 0 && markSoon)
            foreach (double r in new[] { flareReach + s, Math.Max(0, flareReach - s) })
            {
                PlanTollInto(f, n, r, markPlan2, NextTickHostiles);
                foreach (var id in markPlan2) if (id >= 0 && id < Enemies.Items.Length) Mark(Enemies.Items[id]);
            }
        // Before the first cut, the plan as PlanToll would make it now; after it, her plan.
        List<int> plan = tollPlan;
        if (flareBlow == 0) { PlanTollInto(f, n, flareReach, markPlan, NextTickHostiles); plan = markPlan; }
        bool fell = false;
        for (int i = flareBlow; i < n; i++)
        {
            int slot = i < plan.Count ? plan[i] : -1;
            var e = slot >= 0 && slot < Enemies.Items.Length ? Enemies.Items[slot] : null;
            if (e == null || !Standing(e) || !Targetable(e) || !FlareCanHurt(e))
            {
                // TollCut's re-pick: the strongest still standing (with a cut near, in the reach it may find then).
                e = TollRepick(flareReach);
                if (!fell && markSoon)
                {
                    Mark(TollRepick(flareReach + s));
                    Mark(TollRepick(Math.Max(0, flareReach - s)));
                }
                fell = true;
            }
            Mark(e);
            if (i == n - 1) markMain = e;
        }
    }

    /// <summary>TollCut's re-pick for a cut whose target fell, within r.</summary>
    Enemy? TollRepick(double r)
    {
        var near = NextTickHostiles(Player.X, Player.Z, r).Where(Standing).ToList();
        return (near.Any(FlareCanHurt) ? near.Where(FlareCanHurt) : near)
            .OrderBy(x => x.Boss).ThenByDescending(x => x.Elite).ThenByDescending(x => x.Hp).FirstOrDefault();
    }

    void MarkBranding(FlareDef f)
    {
        var p = Player;
        double r = f.Arg("burstRadius", 2) * (FlareMod("branding.deep") ? f.Arg("deep", 1.5) : 1) * FlareGrow(f);
        Brand? lastWord = null;
        void BrandWave()
        {
            // What BrandAll will mark (a boss it can't hurt passed over), and the lesser things its bursts splash.
            foreach (var e in HostilesInRadius(p.X, p.Z, flareReach + 2))
            {
                if (!Standing(e) || (e.Boss && !FlareCanHurt(e)) || Dist(e.X, e.Z, p.X, p.Z) > flareReach + e.Radius + MarkSlack(e)) continue;
                Mark(e);
                if (!e.Boss) MarkCircle(e.X, e.Z, r, o => !o.Boss);
            }
            Shape(p.X, p.Z, flareReach);
        }
        if (flareBlow < flareAt.Length)
        {
            BrandWave();
            var near = HostilesInRadius(p.X, p.Z, flareReach).Where(e => Standing(e) && (!e.Boss || FlareCanHurt(e))).ToList();
            markMain = near.FirstOrDefault(e => e.Boss) ?? near.OrderByDescending(e => Dist(e.X, e.Z, p.X, p.Z)).FirstOrDefault();
        }
        foreach (var br in brands)
        {
            if (br.Done) continue;
            var host = br.On != null && !br.Dead && br.On.Id == br.Id && Standing(br.On) ? br.On : null;
            double x = host?.X ?? br.X, z = host?.Z ?? br.Z;
            if (br.Share <= 0) continue;
            Mark(host);
            if (br.Radius > 0) { MarkCircle(x, z, br.Radius, o => o != host && !o.Boss); Shape(x, z, br.Radius); }
            // The last word: the wave's Last brand (the boss's, or the farthest), else the latest still to burst.
            if (host != null && (lastWord == null || br.Last || (!lastWord.Last && br.At > lastWord.At))) lastWord = br;
        }
        if (secondBrandAt > 0) BrandWave();
        if (eyeOn != null && Time <= eyeUntil && eyeOn.Id == eyeId && Standing(eyeOn) && eyeBursts < (int)f.Arg("eyeMax", 10)) Mark(eyeOn);
        if (flareBlow >= flareAt.Length) markMain = lastWord?.On;
    }

    void MarkArrow(FlareDef f)
    {
        var p = Player;
        int splits = flareAt.Length - 1;
        double half = f.Arg("lineWidth", 1.2) * FlareGrow(f);
        double slen = f.Arg("splitLength", 12) * FlareGrow(f), shalf = f.Arg("splitWidth", 0.8) * FlareGrow(f);
        if (flareBlow == 0)
        {
            double len = f.Arg("line", 30) * FlareGrow(f);
            var line = LineHostiles(p.X, p.Z, flareAngle, len, half);
            Enemy? heart = null;
            if (FlareMod("arrow.heart") && line.FirstOrDefault(x => x.E.Elite || x.E.Boss) is { E: not null } stop)
            {
                heart = stop.E;
                len = Math.Max(0.5, stop.Along);
                line = line.Where(x => x.Along <= stop.Along).ToList();
            }
            MarkLine(p.X, p.Z, flareAngle, len, half);
            if (heart != null) { markMain = heart; return; }
            // The splits are chosen as the arrow flies (from the toughest it passed, where they stand then) and fly 0.05-0.15 s
            // after it: they are marked from the arrow's blow, not guessed ahead (a guess swept the crowd and went unhit).
            var tough = line.Select(x => x.E).Where(e => !e.Boss).OrderByDescending(e => e.Elite).ThenByDescending(e => e.MaxHp).Take(splits).ToList();
            markMain = line.Select(x => x.E).FirstOrDefault(e => e.Boss) ?? tough.FirstOrDefault();
            return;
        }
        for (int k = flareBlow - 1; k < splits && k < arrowSplits.Count; k++)
        {
            if (arrowHeart != null)
            {
                var heartOn = arrowHeart.Id == arrowHeartId && Standing(arrowHeart) ? arrowHeart : null;
                Mark(heartOn);
                markMain = heartOn;
                continue;
            }
            var (sx, sz, ang, from) = arrowSplits[k];
            MarkLine(sx, sz, ang, slen, shalf, from);
        }
    }

    void MarkDrag(FlareDef f)
    {
        var p = Player;
        int n = flareAt.Length;
        if (flareBlow >= n) return;
        double slamR = f.Arg("slamRadius", 4) * FlareGrow(f);
        double kx = knotX, kz = knotZ;
        if (flareBlow == 0)
        {
            kx = p.X + Math.Cos(flareAngle) * f.Arg("knotAhead", 1.5);
            kz = p.Z + Math.Sin(flareAngle) * f.Arg("knotAhead", 1.5);
            double reach = flareReach * (FlareMod("drag.deeper") ? f.Arg("deeper", 1.5) : 1);
            MarkCircle(p.X, p.Z, reach, e => !e.Boss || FlareCanHurt(e));
            Shape(p.X, p.Z, reach);
            double x0 = kx, z0 = kz;
            markMain = HostilesInRadius(p.X, p.Z, reach).Where(e => Standing(e) && (!e.Boss || FlareCanHurt(e)) && (e.Boss || Dist(e.X, e.Z, x0, z0) > slamR * 0.8))
                .OrderByDescending(e => e.Boss).ThenByDescending(e => e.Elite).ThenByDescending(e => Dist(e.X, e.Z, p.X, p.Z)).FirstOrDefault();
        }
        else
        {
            foreach (var (e, id) in dragHooked) if (e.Id == id) Mark(e);
            markMain = dragHooked.Where(h => h.E.Id == h.Id && Standing(h.E)).Select(h => h.E).OrderByDescending(e => e.Boss).ThenByDescending(e => e.Elite).FirstOrDefault();
        }
        // Grinder's shreds take all in the knot; the slam what it can hurt.
        bool grinds = n > 3 && flareBlow < n - 1;
        MarkCircle(kx, kz, slamR, grinds ? null : e => !e.Boss || FlareCanHurt(e));
        Shape(kx, kz, slamR);
    }

    void MarkBill(FlareDef f)
    {
        var p = Player;
        if (flareBlow >= flareAt.Length) return;
        double vault = f.Arg("vault", 6) * FlareGrow(f);
        Enemy? Held() => billOn != null && billOn.Id == billOnId && Standing(billOn) ? billOn : null;
        Enemy? on;
        if (flareAim == 0)
        {
            // Before the leap: whom BillAim picks now (the leap strikes nothing: the first chop lands a quarter second later).
            on = BillPick(p.X, p.Z, flareReach);
        }
        else if (flareBlow == 0) on = Held() ?? BillPick(billX, billZ, vault);
        else on = Held() ?? (billOn != null && billVaults < (FlareMod("bill.running_tab") ? 2 : 1) ? BillPick(p.X, p.Z, vault) : null);
        if (on == null) return;
        Mark(on);
        markMain = on;
        double r = f.Arg("splash", 2) * FlareGrow(f);
        if (FlareMod("bill.wide_chops")) MarkCircle(on.X, on.Z, r, e => e != on && !e.Boss);
        Shape(on.X, on.Z, r);
    }
}

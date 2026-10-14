using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Sim;

/* Phase 6a: the two line Flares (docs/design/CLASSES.md §3.6, §7's phase-6 plan), on one shared piece, the line hit:
 * everything in a straight strip from her along her aim. The Long Cut (sunderer, Strike, Clear): a 12 m sweep, then a
 * 24 m cleave line that Sunders a boss. One Arrow (verge-hunter, Strike, Context): a 30 m arrow that pierces, kills the
 * ordinary things it leaves low, and splits on the toughest it passes; Through the Heart makes it Single.
 * Events (Ev.Flare Blow): "sweep" (at her, Radius her reach), "cleave" and "arrow" (X/Z her, TX/TZ the line's end,
 * Radius its half-width, Target the boss or champion it stopped in or struck, 0 none), "burnline" (Line of Morning: the
 * cleave's line, burning), "split" (X/Z where it leaves the arrow, TX/TZ its end, Radius its half-width, Target the thing
 * it turns back into with Through the Heart). With nothing near every line still flies its full length. */
public sealed partial class Battle
{
    /// <summary>The line hit: what stands in a strip from (ox, oz) along the angle, "half" metres either side (and its own
    /// size), by distance along it.</summary>
    List<(Enemy E, double Along)> LineHostiles(double ox, double oz, double ang, double len, double half)
    {
        double dx = Math.Cos(ang), dz = Math.Sin(ang);
        var o = new List<(Enemy, double)>();
        foreach (var e in HostilesInRadius(ox + dx * len / 2, oz + dz * len / 2, len / 2 + half + 2))
        {
            if (!e.Alive || e.State == EnemyState.Dying) continue;
            double rx = e.X - ox, rz = e.Z - oz, along = rx * dx + rz * dz, perp = Math.Abs(-rx * dz + rz * dx);
            if (along >= -e.Radius && along <= len + e.Radius && perp <= half + e.Radius) o.Add((e, along));
        }
        return o.OrderBy(x => x.Item2).ToList();
    }

    void LineEvent(FlareDef f, string part, bool last, double ox, double oz, double ang, double len, double half, Enemy? target, int hitstop) =>
        Events.Emit(new Ev.Flare
        {
            Phase = FlarePhase.Blow, Id = f.Id, X = ox, Z = oz, Radius = half, Blow = flareBlow, Clutch = flareClutch, Stand = false,
            Part = part, Last = last, TX = ox + Math.Cos(ang) * len, TZ = oz + Math.Sin(ang) * len, Target = target?.Id ?? 0, Hitstop = hitstop, Angle = ang,
        });

    /* -------------------------------------------------------------- The Long Cut -- */

    /// <summary>The sweep (everything in reach), the cleave (the line along her aim; a boss in it is Sundered), and with
    /// Second Cut a counter-sweep. Line of Morning leaves the line burning; Through the Wall runs it 36 m. A boss takes
    /// every part whole: no Flare hits a boss for less than it says (the owner, 13 October).</summary>
    void LongCutBlow(FlareDef f, bool last)
    {
        var p = Player;
        bool cleave = flareBlow == 2;
        if (!cleave)
        {
            ForEachHostileInRadius(p.X, p.Z, flareReach, (e, d) => FlareHit(e, f.Arg("sweep", 1.5), f.School, 1.0, p.X, p.Z));
            FlareBlowEvent(f, "sweep", last, p.X, p.Z, null, flareReach, hitstop: (int)f.BeatAt("hitstop", 3));
            return;
        }
        bool wall = FlareMod("long_cut.through_the_wall");
        double len = (wall ? f.Arg("wall", 36) : f.Arg("line", 24)) * FlareGrow(f), half = f.Arg("lineWidth", 1.5) * FlareGrow(f);
        Enemy? boss = null;
        foreach (var (e, _) in LineHostiles(p.X, p.Z, flareAngle, len, half))
        {
            FlareHit(e, f.Arg("cleave", 1.5), f.School, 1.4, p.X, p.Z);
            if (e.Boss && e.Alive && e.State != EnemyState.Dying)
            {
                boss ??= e;
                e.Sunder = wall ? f.Arg("sunderWall", 0.4) : f.Arg("sunder", 0.3);
                e.SunderUntil = Time + f.Arg("sunderSeconds", 8);
            }
        }
        LineEvent(f, "cleave", last, p.X, p.Z, flareAngle, len, half, boss, (int)f.BeatAt("hitstopCleave", 8));
        if (FlareMod("long_cut.line_of_morning"))
        {
            // The seam burns: a row of the Flare's own fires along it, each a step apart.
            double step = Math.Max(1, half * 1.6), dps = flarePower * f.Arg("burn", 0.25);
            for (double a = step / 2; a < len; a += step)
                if (SpawnZone(Side.Player, p.X + Math.Cos(flareAngle) * a, p.Z + Math.Sin(flareAngle) * a, half + 0.3, f.Arg("burnSeconds", 4), dps, f.School) is { } z)
                {
                    z.Credit = "flare";
                    z.Tags = f.Tags;
                }
            LineEvent(f, "burnline", false, p.X, p.Z, flareAngle, len, half, null, 0);
        }
    }

    /* ----------------------------------------------------------------- One Arrow -- */

    /// <summary>Where each split leaves the arrow and on what angle (chosen at the arrow's blow), and Through the Heart's
    /// mark (the champion or boss it stopped in).</summary>
    readonly List<(double X, double Z, double Ang, int From)> arrowSplits = new();
    Enemy? arrowHeart;
    int arrowHeartId = -1;

    /// <summary>The arrow (its first blow) and then each split. The arrow pierces the whole line; what it leaves below
    /// "execute" of its health dies (champions and bosses never); a boss takes "bossCrit" times its share. It splits on the
    /// toughest things it passed (champions first, then the most health), or along its line where too few stood.</summary>
    void OneArrowBlow(FlareDef f, bool last)
    {
        var p = Player;
        int splits = flareAt.Length - 1;
        double half = f.Arg("lineWidth", 1.2) * FlareGrow(f);
        if (flareBlow == 1)
        {
            arrowSplits.Clear();
            arrowHeart = null;
            arrowHeartId = -1;
            double len = f.Arg("line", 30) * FlareGrow(f);
            bool heart = FlareMod("arrow.heart");
            var line = LineHostiles(p.X, p.Z, flareAngle, len, half);
            // Through the Heart: it stops dead in the first champion or boss.
            if (heart && line.FirstOrDefault(x => x.E.Elite || x.E.Boss) is { E: not null } stop)
            {
                arrowHeart = stop.E;
                arrowHeartId = stop.E.Id;
                len = Math.Max(0.5, stop.Along);
                line = line.Where(x => x.Along <= stop.Along).ToList();
            }
            var struck = new List<Enemy>();
            foreach (var (e, _) in line)
            {
                FlareHit(e, f.Arg("arrow", 1.0) * (e.Boss ? f.Arg("bossCrit", 2) : 1), f.School, 1.2, p.X, p.Z);
                ArrowAfter(f, e);
                struck.Add(e);
            }
            double dx = Math.Cos(flareAngle), dz = Math.Sin(flareAngle);
            if (arrowHeart != null)
                // Its splits turn back into it: three arcs closing on one point, from ahead of it and either side.
                for (int i = 0; i < splits; i++)
                {
                    double a = flareAngle + Math.PI + (i - (splits - 1) / 2.0) * f.Arg("heartFan", 0.7);
                    double r = f.Arg("heartFrom", 4);
                    arrowSplits.Add((arrowHeart.X - Math.Cos(a) * r, arrowHeart.Z - Math.Sin(a) * r, a, arrowHeart.Id));
                }
            else
            {
                // The toughest it passed, each once; then points along its line (with nothing near, all at its end).
                var tough = line.Select(x => x.E).Where(e => !e.Boss).OrderByDescending(e => e.Elite).ThenByDescending(e => e.MaxHp).Take(splits).ToList();
                for (int i = 0; i < splits; i++)
                {
                    double side = i % 2 == 0 ? 1 : -1, a = flareAngle + side * f.Arg("splitAngle", 0.4) * (1 + i / 2);
                    if (i < tough.Count) arrowSplits.Add((tough[i].X, tough[i].Z, a, tough[i].Id));
                    else
                    {
                        double at = line.Count == 0 ? len : len * (i + 1) / (splits + 1.0);
                        arrowSplits.Add((p.X + dx * at, p.Z + dz * at, a, -1));
                    }
                }
            }
            LineEvent(f, "arrow", last, p.X, p.Z, flareAngle, len, half, arrowHeart ?? line.Select(x => x.E).FirstOrDefault(e => e.Boss), FlareHitstop(f, false));
            return;
        }
        int k = flareBlow - 2;
        if (k >= arrowSplits.Count) return;
        var (sx, sz, ang, from) = arrowSplits[k];
        double slen = f.Arg("splitLength", 12) * FlareGrow(f), shalf = f.Arg("splitWidth", 0.8) * FlareGrow(f);
        var heartOn = arrowHeart != null && arrowHeart.Id == arrowHeartId && arrowHeart.Alive && arrowHeart.State != EnemyState.Dying ? arrowHeart : null;
        if (arrowHeart != null)
        {
            // Back into the heart: the split flies from its start onto the one it stopped in, and strikes nothing else.
            double hx = arrowHeart.X, hz = arrowHeart.Z, l = Math.Max(0.5, Dist(sx, sz, hx, hz));
            if (heartOn != null)
            {
                FlareHit(heartOn, f.Arg("heart", 0.6) * (heartOn.Boss ? f.Arg("bossCrit", 2) : 1), f.School, 0, sx, sz);
                ArrowAfter(f, heartOn);
            }
            LineEvent(f, "split", last, sx, sz, Math.Atan2(hz - sz, hx - sx), l, shalf, heartOn, FlareHitstop(f, last, "hitstopSplit"));
            return;
        }
        foreach (var (e, _) in LineHostiles(sx, sz, ang, slen, shalf))
        {
            if (e.Id == from) continue;
            FlareHit(e, f.Arg("split", 0.6) * (e.Boss ? f.Arg("bossCrit", 2) : 1), f.School, 0.8, sx, sz);
            ArrowAfter(f, e);
        }
        LineEvent(f, "split", last, sx, sz, ang, slen, shalf, null, FlareHitstop(f, last, "hitstopSplit"));
    }

    /// <summary>After an arrow or a split strikes: Pinned to the Earth binds it 2 s; an ordinary thing left low dies.</summary>
    void ArrowAfter(FlareDef f, Enemy e)
    {
        if (!e.Alive || e.State == EnemyState.Dying) return;
        if (FlareMod("arrow.pinned")) ApplyStatus(e, new StatusPayload(StatusKind.Bound, 1, 1, f.Arg("pinned", 2)), 0);
        if (!e.Elite && !e.Boss && e.Hp < e.MaxHp * f.Arg("execute", 0.3)) KillEnemy(e, true, null);
    }
}

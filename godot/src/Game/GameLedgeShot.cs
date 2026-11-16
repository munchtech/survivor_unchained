using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play;

/* --ledge-shot pack|elite (with --shot, in a dungeon: pictures of the ledge view, 15 Nov). At the nearest drop to where she comes
 * in (a side drop before a near one), she is set 4.5 m from the lip facing it, a pack of the dungeon's people (or one elite) at the
 * lip, and at --ledge-at seconds (2.5) each is struck by her blade with a knockback toward the drop: the sim's own path (HitEnemy,
 * the slide, Battle.FallOver). Frames: ledge_00.. along the fall, ledge_loot after it. Pictures only: no play path runs this. */
public partial class Game
{
    static readonly string? LedgeShot = Args.Has("shot") ? Args.Get("ledge-shot") : null;
    int ledgeStage;
    bool ledgeMoved;
    double ledgeShift;
    double ledgeUx, ledgeUz, ledgeLx, ledgeLz;
    readonly List<Enemy> ledgeFoes = new();

    void LedgeShotTick()
    {
        if (LedgeShot == null || Battle is not { } b || b.Collision == null || ledgeStage >= 3) return;
        double at = Args.Num("ledge-at", 2.5f) + ledgeShift;
        var p = b.Player;
        if (ledgeStage == 0 && b.Time >= at - Args.Num("ledge-lead", 0.3f))
        {
            ledgeStage = 1;
            // The lip: the nearest drop along 72 rays out from her, a side drop weighed before a near one (it reads across the frame).
            double best = double.MaxValue, lx = 0, lz = 0;
            for (int k = 0; k < 72; k++)
            {
                double a = k * Math.Tau / 72, ux = Math.Cos(a), uz = Math.Sin(a);
                if (Args.Get("ledge-face") is { } face && face.Split(',') is [var fx, var fz] && ux * double.Parse(fx) + uz * double.Parse(fz) < 0.8) continue;
                for (double r = 0.5; r < 40; r += 0.25)
                {
                    double x = p.X + ux * r, z = p.Z + uz * r;
                    if (b.Collision.Blocked(x, z, 0.05) && !b.Collision.InDrop(x, z)) break;
                    if (!b.Collision.InDrop(x, z)) continue;
                    double score = r * (1 + 0.6 * Math.Abs(uz));
                    if (score < best) { best = score; lx = x; lz = z; ledgeUx = ux; ledgeUz = uz; }
                    break;
                }
            }
            ledgeLx = lx; ledgeLz = lz;
            if (best == double.MaxValue && !ledgeMoved)
            {
                // None in sight of her: she is taken to the nearest drop on the map with open ground 4 m before it, and looks again.
                ledgeMoved = true;
                double bd = double.MaxValue, mx = 0, mz = 0;
                for (double x = p.X - 120; x <= p.X + 120; x += 0.5)
                    for (double z = p.Z - 120; z <= p.Z + 120; z += 0.5)
                    {
                        double d2 = (x - p.X) * (x - p.X) + (z - p.Z) * (z - p.Z);
                        if (d2 >= bd || !b.Collision.InDrop(x, z)) continue;
                        for (int k = 0; k < 8; k++)
                        {
                            double ox = x + Math.Cos(k * Math.Tau / 8) * 4, oz = z + Math.Sin(k * Math.Tau / 8) * 4;
                            if (!b.Collision.InDrop(ox, oz) && !b.Collision.Blocked(ox, oz, 0.6)) { bd = d2; mx = ox; mz = oz; break; }
                        }
                    }
                if (bd < double.MaxValue) { p.X = mx; p.Z = mz; ledgeStage = 0; ledgeShift = 1.5; GD.Print($"ledge-shot: moved her to ({mx:0.0},{mz:0.0})"); return; }
            }
            if (best == double.MaxValue) { GD.Print("ledge-shot: no drop found"); ledgeStage = 3; return; }
            double bx = lx - ledgeUx * Args.Num("ledge-back", 4.5f), bz = lz - ledgeUz * Args.Num("ledge-back", 4.5f);
            p.X = bx; p.Z = bz; p.Facing = Math.Atan2(ledgeUz, ledgeUx);
            bool elite = LedgeShot == "elite";
            string[] kinds = elite ? [Args.Get("ledge-kind") ?? "bruiser"] : (Args.Get("ledge-kind") ?? "footpad,footpad,pillager,footpad,bruiser").Split(',');
            double px = -ledgeUz, pz = ledgeUx;
            for (int i = 0; i < kinds.Length; i++)
            {
                double side = (i - (kinds.Length - 1) / 2.0) * 1.15, inset = 1.25 + (i % 2) * 0.55;
                var e = b.SpawnEnemy(kinds[i], lx - ledgeUx * inset + px * side, lz - ledgeUz * inset + pz * side, new Battle.SpawnOpts { Style = SpawnStyle.Walk, Elite = elite });
                if (e != null) { e.Facing = Math.Atan2(-ledgeUz, -ledgeUx); ledgeFoes.Add(e); }
            }
            if (scene?.Data is { } zd)
            {
                var sb = new System.Text.StringBuilder("ledge-shot probe r:drop/blocked/view");
                for (double r = 0; r < 14; r += 0.5)
                {
                    double x = bx + ledgeUx * r, z = bz + ledgeUz * r;
                    sb.Append($" {r:0.0}:{(b.Collision.InDrop(x, z) ? "D" : b.Collision.Blocked(x, z, 0.05) ? "B" : ".")}{SurvivorUnchained.View.DungeonWalls.SurfOverFloor(zd, (float)x, (float)z):0.0}");
                }
                GD.Print(sb.ToString());
            }
            GD.Print($"ledge-shot: lip ({lx:0.0},{lz:0.0}) dir ({ledgeUx:0.00},{ledgeUz:0.00}) her ({bx:0.0},{bz:0.0}), {ledgeFoes.Count} foes");
        }
        else if (ledgeStage == 1 && b.Time >= at)
        {
            ledgeStage = 2;
            var w = b.Weapons.FirstOrDefault();
            foreach (var e in ledgeFoes.Where(e => e.Alive))
            {
                b.HitEnemy(e, 1, School.Physical, [Tag.Melee], new HitOpts { Weapon = w, DirX = ledgeUx, DirZ = ledgeUz, NoProcs = true });
                // The push itself set by hand (a footpad may dodge the blow): a slide of the way to the lip and on (|Kb| / 9 metres).
                double lipAt = 0;
                while (lipAt < 12 && !b.Collision.InDrop(e.X + ledgeUx * lipAt, e.Z + ledgeUz * lipAt)) lipAt += 0.1;
                double k = 9 * (lipAt + Args.Num("ledge-over", 1.6f));
                e.Kbx = ledgeUx * k; e.Kbz = ledgeUz * k; e.KbBy = w?.Id;
            }
            double[] t = [0, 0.08, 0.16, 0.24, 0.32, 0.42, 0.55, 0.75];
            for (int i = 0; i < t.Length; i++) Shots.Want($"ledge_{i:00}", t[i] + 1 / 60.0);
            Shots.Want("ledge_loot", Args.Num("ledge-loot", 1.9f));
        }
        if (ledgeStage == 2 && b.Time < at + 1 && ledgeFoes.Count == 1 && ledgeFoes[0] is { } f1)
            GD.Print($"ledge-shot t+{b.Time - at:0.00} {f1.State} x {f1.X:0.00} kb {f1.Kbx:0.0} brink {f1.AtBrink} edge {f1.Edge}");
        if (ledgeStage == 2 && b.Time >= at + 1.8)
        {
            ledgeStage = 3;
            var sb = new System.Text.StringBuilder($"ledge-shot after: fell {b.LedgeKillCount}, standing {ledgeFoes.Count(e => e.Alive && e.State != EnemyState.Dying)}; pickups near the lip:");
            foreach (var pk in b.Pickups.Items.Where(q => q.Alive && Math.Abs(q.X - ledgeLx) < 8 && Math.Abs(q.Z - ledgeLz) < 8))
                sb.Append($" {pk.Kind}({pk.X:0.0},{pk.Z:0.0}{(b.Collision.Blocked(pk.X, pk.Z, 0.2) ? " BLOCKED" : "")} view {(scene?.Data is { } zd ? SurvivorUnchained.View.DungeonWalls.SurfOverFloor(zd, (float)pk.X, (float)pk.Z) : 0):0.0})");
            GD.Print(sb.ToString());
        }
    }
}

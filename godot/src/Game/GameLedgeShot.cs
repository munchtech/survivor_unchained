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
    double ledgeUx, ledgeUz;
    readonly List<Enemy> ledgeFoes = new();

    void LedgeShotTick()
    {
        if (LedgeShot == null || Battle is not { } b || b.Collision == null || ledgeStage >= 2) return;
        double at = Args.Num("ledge-at", 2.5f);
        var p = b.Player;
        if (ledgeStage == 0 && b.Time >= at - 0.9)
        {
            ledgeStage = 1;
            // The lip: the nearest drop along 72 rays out from her, a side drop weighed before a near one (it reads across the frame).
            double best = double.MaxValue, lx = 0, lz = 0;
            for (int k = 0; k < 72; k++)
            {
                double a = k * Math.Tau / 72, ux = Math.Cos(a), uz = Math.Sin(a);
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
            if (best == double.MaxValue) { GD.Print("ledge-shot: no drop found"); ledgeStage = 2; return; }
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
            GD.Print($"ledge-shot: lip ({lx:0.0},{lz:0.0}) dir ({ledgeUx:0.00},{ledgeUz:0.00}) her ({bx:0.0},{bz:0.0}), {ledgeFoes.Count} foes");
        }
        else if (ledgeStage == 1 && b.Time >= at)
        {
            ledgeStage = 2;
            var w = b.Weapons.FirstOrDefault();
            foreach (var e in ledgeFoes.Where(e => e.Alive))
                b.HitEnemy(e, 1, School.Physical, [Tag.Melee], new HitOpts { Weapon = w, Knockback = Args.Num("ledge-knock", 3.2f) * Math.Max(1, e.Mass), DirX = ledgeUx, DirZ = ledgeUz, NoProcs = true });
            double[] t = [0, 0.1, 0.2, 0.3, 0.42, 0.56, 0.75, 1.0];
            for (int i = 0; i < t.Length; i++) Shots.Want($"ledge_{i:00}", t[i] + 1 / 60.0);
            Shots.Want("ledge_loot", Args.Num("ledge-loot", 1.9f));
        }
    }
}

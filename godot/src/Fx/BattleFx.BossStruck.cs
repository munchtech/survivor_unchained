using System;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/* (lane E lead 7, judge 4, 17 Nov: "struck read not enough even at .4 (body L50 .29 -> .31): whole boss + .15 L for 2-3
 * frames, steel core mix .4-.5, hit spark") A den boss struck (not a tick of a burn, not a turned blow) flashes whole: the
 * crowd shader lifts its body, back and mane (vat_den_body, DEN_BOSS_STRUCK) for BossPulseFor of the FX clock (3 frames at
 * 60 fps, 2 at 30), and a small steel spark lights on its flank toward her (the hit's own burst is at its centre, inside the
 * big body). A boss is struck many times a second (the Bladestorm's ticks): a new flash at most every BossPulseGap, so it
 * reads as distinct flashes, never a glow. */
public partial class BattleFx
{
    const double BossPulseGap = 0.18, BossPulseFor = 0.045;
    readonly System.Collections.Generic.Dictionary<int, double> bossPulseAt = new();
    static readonly Color BossSparkHead = Hdr("#f4f7ff", 1.7f), BossSparkTail = Hdr("#c8d4e6", 1.1f);
    // (round 2: at 1.6 m and its radius x .9 toward her it drew below the belly, between the legs, l7c3_st: from the play camera
    // (56 deg, 23 m) a metre toward her drops 64 px and a metre up lifts 43. At its torso's middle, 2.35 m, and half its radius out,
    // it lands on the flank toward her at about mid-body height, inside the silhouette (sparks draw over the body, no depth test):
    // at 1.95 m it sat on the belly's edge, l7d_st.)
    const float BossSparkY = 2.35f, BossSparkIn = 0.45f, BossSparkSize = 0.5f;

    /// <summary>A den boss's struck flash this frame (CrowdView.BossPulse): 1 in its pulse, else 0.</summary>
    float BossPulseOn(int id) => bossPulseAt.TryGetValue(id, out var at) && time >= at && time - at < BossPulseFor ? 1f : 0f;

    void BossStruck(Enemy boss, Battle b)
    {
        if (bossPulseAt.TryGetValue(boss.Id, out var was) && time >= was && time - was < BossPulseGap) return;
        bossPulseAt[boss.Id] = time;
        if (Flare.HushesHitSparks) return;
        // On its flank toward her, mid-body (BossSparkY up, half its radius out: drawn over its side, not below its belly): a 4-point glint and two short streaks, steel-white, 2-3 frames.
        double dx = b.Player.X - boss.X, dz = b.Player.Z - boss.Z, dl = Math.Sqrt(dx * dx + dz * dz);
        if (dl < 1e-6) { dx = -boss.LastDx; dz = -boss.LastDz; dl = Math.Max(1e-6, Math.Sqrt(dx * dx + dz * dz)); }
        var toHer = new Vector3((float)(dx / dl), 0, (float)(dz / dl));
        var at = new Vector3((float)boss.X, Y(boss.X, boss.Z) + BossSparkY, (float)boss.Z) + toHer * (float)boss.Radius * BossSparkIn;
        Sparks.Spawn(new Sparks.P
        {
            At = at, Life = 0.045f, Size = BossSparkSize, SizeEnd = BossSparkSize * 0.6f, Color = BossSparkHead, ColorEnd = BossSparkTail * 0.5f,
            Alpha = 1, Sprite = Star4, Spin = 0.2f + R() * 0.4f, SpinV = 0.001f,
        });
        var side = new Vector3(-toHer.Z, 0, toHer.X);
        for (int i = 0; i < 2; i++)
        {
            var dir = (toHer + side * (i == 0 ? 0.6f : -0.6f) + Vector3.Up * (0.3f + R() * 0.3f)).Normalized();
            float speed = 8 + R() * 3, len = 0.32f;
            Sparks.Spawn(new Sparks.P
            {
                At = at, V = dir * speed, Life = 0.06f, Size = 0.06f, SizeEnd = 0.045f, Color = BossSparkHead, ColorEnd = BossSparkTail,
                Gravity = 4, Drag = 5, Alpha = 1, Sprite = -1, Stretch = len / speed,
            });
        }
    }
}

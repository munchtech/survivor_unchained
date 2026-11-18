using System;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/* (lane E lead 7, judge 4, 17 Nov: "struck read not enough even at .4 (body L50 .29 -> .31): whole boss + .15 L for 2-3
 * frames, steel core mix .4-.5, hit spark") A den boss struck (not a tick of a burn, not a turned blow) flashes whole: the
 * crowd shader lifts its body, back and mane (vat_den_body, DEN_BOSS_STRUCK) for BossPulseFor of the FX clock (3 frames at
 * 60 fps, 2 at 30), and a small steel spark lights on its flank toward her (the hit's own burst is at its centre, inside the
 * big body). A boss is struck many times a second (the Bladestorm's ticks): a new flash at most every BossPulseGap, so it
 * reads as distinct flashes, never a glow.
 * (round 3, judge 5 17 Nov: "_03 = _04, no peak/decay"; the spark "20x18 px, two thin strokes, core blue h 260, inside the
 * torso") The pulse peaks then halves by time, the same read at 30 and 60 fps: 1 for BossPulsePeak (frame 1 at 30 fps, frames
 * 1-2 at 60), BossPulseHalf until BossPulseFor (frame 2 at 30, 3-4 at 60), then 0. The spark is the P7 cel star in the
 * physical school's bands (cream core #fbf1d8, gold, amber: fx rule 2), centred on its silhouette's edge toward her, full on
 * frame 1, 60% and its core stepped out on frame 2. */
public partial class BattleFx
{
    const double BossPulseGap = 0.18, BossPulsePeak = 0.025, BossPulseFor = 0.058;
    const float BossPulseHalf = 0.62f;
    readonly System.Collections.Generic.Dictionary<int, double> bossPulseAt = new();
    // (r3: at 2.35 m and half its radius toward her it drew inside the torso, about 30 px above the belly's edge (l7d2_st_03,
    // (960, 399) against the edge at (960, 430)); from the play camera a metre up lifts 43 px: 0.72 m lower puts its centre on
    // the edge. px across the quad: the star's long spike reaches the quad's edge and the rest 0.5-0.85 of it, so about 0.85 x
    // that across, 37 px; its spikes' roots 6 px, about 4.3 px drawn after the stroke's shape)
    // (lane E lead 9, judge 6: "26x26 px, core C .044"; 32-44 px, core C <= .04 wanted) the quad 62 px (44 drew 26 px
    // across: the spikes reach 0.5-0.85 of the quad less their pointed tips), its core a paler cream than the school's
    // #fbf1d8 (which reads C .044-.049 over the boss): #fff6e6, Oklab L .976 C .023 h 82
    const float BossSparkY = 1.63f, BossSparkIn = 0.45f, BossSparkPx = 62f, BossSparkRootPx = 6f, BossSparkLate = 0.6f;
    const string BossSparkCore = "#fff6e6";

    /// <summary>A den boss's struck flash this frame (CrowdView.BossPulse): 1 at its peak, BossPulseHalf after, else 0.</summary>
    float BossPulseOn(int id)
    {
        if (!bossPulseAt.TryGetValue(id, out var at) || time < at) return 0f;
        double a = time - at;
        return a < BossPulsePeak ? 1f : a < BossPulseFor ? BossPulseHalf : 0f;
    }

    void BossStruck(Enemy boss, Battle b)
    {
        if (bossPulseAt.TryGetValue(boss.Id, out var was) && time >= was && time - was < BossPulseGap) return;
        bossPulseAt[boss.Id] = time;
        if (Flare.HushesHitSparks || P7Off) return;
        double dx = b.Player.X - boss.X, dz = b.Player.Z - boss.Z, dl = Math.Sqrt(dx * dx + dz * dz);
        if (dl < 1e-6) { dx = -boss.LastDx; dz = -boss.LastDz; dl = Math.Max(1e-6, Math.Sqrt(dx * dx + dz * dz)); }
        var toHer = new Vector3((float)(dx / dl), 0, (float)(dz / dl));
        var at = new Vector3((float)boss.X, Y(boss.X, boss.Z) + BossSparkY, (float)boss.Z) + toHer * (float)boss.Radius * BossSparkIn;
        // The P7 star, camera-facing over everything (its top shader), 4-6 spikes; stepped by its own age from the frame it first
        // draws (StepP7 runs after the hit's frame has begun, so its first Age is that frame's dt).
        var s = P7StarPx(at, BossSparkPx, 4 + (int)(R() * 2.99f), BossSparkRootPx, 0, 2, 2, true);
        if (FxCel.Lang["Physical"] is { } ph)
        {
            var c = SurvivorUnchained.Look.FxLanguage.Linear(BossSparkCore, FxAfter.On ? null : ph.Core.Emit);
            s.M.SetShaderParameter("fx_core", new Vector3(c[0], c[1], c[2]) * (float)SurvivorUnchained.Args.Num("fx-gain", 1f));
        }
        float half = s.N.Scale.X, first = -1;
        s.Life = 0.15f;
        s.Step = q =>
        {
            if (first < 0) first = q.Age;
            float age = q.Age - first;
            q.N.Visible = age < BossPulseFor;
            bool late = age >= BossPulsePeak;
            q.N.Scale = Vector3.One * half * (late ? BossSparkLate : 1f);
            q.M.SetShaderParameter("p7_t", age);
            q.M.SetShaderParameter("p7_fade", late ? 0.34f : 0f);
        };
    }
}

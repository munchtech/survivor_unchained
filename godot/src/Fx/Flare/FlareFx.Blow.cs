using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// The ultimate's blow and recovery (H7 beats 3 and 4; data/content/flare_family.json "flares" blow, "band", "beat",
/// "recovery"): each Strike's main blow (its data's Blow part) is THE beat. On it, once: the boom, the camera's kick (px at
/// 1080p), and one shock band of the school's light from her (or out from a line Flare's line, or from where Burns Twice's
/// last word lands) past the frame's edges, through flare_world's ground hook (flare_band). Keyed on the band: the Flare's
/// kills (the held pose, then the fall: DeathOf), its damage numbers (held from the press, one burst), its loot (DropFresh).
/// A decision-marked hit holds its death and number until its mark has shown a few frames. Then the grade eases back from
/// the main blow and her ember's pool stands brighter for a breath. Each Flare's own shape is left as it was.
/// H7 r2 (judge r1 fixes 1-3): the PEAK on the main blow (FlareFx.Peak), its 2-frame hitstop and the push-in let go on it;
/// the band a lit FRONT (the ground lit behind it for a breath, no dark wake); each struck body a 2-frame rim in the hue as
/// the band crosses it (BandRim), then its number; the HUD's kill count waits for the band (KillsHeld).
/// For the marks (FlareMarksView): BandReaches(x, z) is when the band reaches a point (Flare time; Held before the blow),
/// BandReachesRt the same in real seconds from now, BlowAtRt the main blow's real time (-1 none).
/// </summary>
public partial class FlareFx
{
    /// <summary>A Flare's damage number, released (BattleFx: Hits.Tally).</summary>
    public Action<int, Vector3, double, double, bool> Number = (_, _, _, _, _) => { };
    /// <summary>One big number past the caps (Hits.Total): the Long Cut's line as one total at its far end (r3).</summary>
    public Action<Vector3, double> Total = (_, _) => { };
    double lineTotal, lineTotalDue = double.MaxValue;
    int lineTotalN;
    float lineTotalAlong;
    Vector3 lineTotalAt;
    /// <summary>Her ember's pool (x her light; 1 none): PlayerView.FlarePool.</summary>
    public Action<float> EmberPool = _ => { };

    double blowT = -1, blowRt = -1, pressRt = -1;
    Vector2 bandA, bandB;
    bool bandOn, mainLogged;
    static readonly bool BandOff = Args.Has("flare-band-off");
    float poolNow = 1;
    readonly List<(int Target, Vector3 At, double Amount, double MaxHp, bool Crit, double BornRt)> held = new();
    /// <summary>The struck bodies the band will rim: where each stands, and the drawn frame the band reached it (-1 not yet).</summary>
    readonly Dictionary<int, (Vector2 At, long Frame)> bandStruck = new();
    /// <summary>The Flare's kills the HUD's count does not show yet: their band (or their own moment) has not come.</summary>
    public static int KillsHeld { get; private set; }
    /// <summary>The struck rim's drawn frames as the band crosses a body (FLARE_LOOK §1.6: "a 2-frame rim in the calling's hue").</summary>
    const int BandRimFrames = 2;
    static readonly StringName BandParam = "flare_band", BandLineParam = "flare_band_line", BandColParam = "flare_band_col", BandEdgeParam = "flare_band_edge";

    void BlowPress()
    {
        BlowClear();
        pressRt = rt;
        mainLogged = false;
    }

    /// <summary>Whether this Blow event is the cast's main blow (the family's, a Strike's, once).</summary>
    bool IsMainBlow(Ev.Flare e) => familyOn && blowT < 0 && FlareFamily.IsMain(id, e.Part, e.Last);

    /// <summary>The main blow, from its event (Burns Twice's comes at its last word's landing: MainBlowAt).</summary>
    void MainBlow(Ev.Flare e)
    {
        var from = FlareFamily.Of(id).From;
        var o = from == "point" ? new Vector2((float)e.TX, (float)e.TZ) : new Vector2((float)e.X, (float)e.Z);
        bool line = from == "line" || from == "tear";
        var end = line ? new Vector2((float)e.TX, (float)e.TZ) : o;
        var dir = end - o;
        var axis = line && dir.LengthSquared() > 1e-4f ? new Vector3(dir.X, 0, dir.Y).Normalized() * 0.4f + Vector3.Up : Vector3.Up;
        MainBlowAt(o, end, new Vector3((float)e.TX, (float)HeightAt(e.TX, e.TZ), (float)e.TZ), axis, e.Part);
    }

    void MainBlowAt(Vector2 o, Vector2 end, Vector3 cueAt, Vector3 axis, string part)
    {
        if (!familyOn || blowT >= 0) return;
        blowT = t; blowRt = rt;
        // (a "tear" Flare's band is a ring from her, its line tearing with it: FlareFx.LongCut TearAt)
        bandA = o; bandB = FlareFamily.Of(id).From == "tear" ? o : end; bandOn = !BandOff; // (--flare-band-off: an ablation, the band never drawn)
        // (r3: the main blow's hitstop holds the world, never the Flare's clock: the band, the tear and the deaths on it run
        // through it as the peak's light does; at a tenth, the tear stood 0.3 m long on the peak's brightest frames)
        hitstopRuns = HasPeak;
        // (r3, judge r2 fix 6: the struck rims as the band crosses them are gold, the marks' hue handed over on the blow)
        var rc = Color.FromHtml(FlareFamily.Band.RimColor).SrgbToLinear();
        float rcm = Mathf.Max(rc.R, Mathf.Max(rc.G, rc.B));
        RenderingServer.GlobalShaderParameterSet("flare_mark_rim", new Vector4(rc.R / rcm, rc.G / rcm, rc.B / rcm, 1));
        Cue("boom", cueAt, 1);
        Rumble(1, 0.6f, 0.14f);
        // The plain Strikes' Spend (its light, the world's ring) on this same frame (FLARE_LOOK §1.2), sized with the
        // band so the frame stays in §1.6's budget (flare_family.json beat.spendLight).
        if (HasPeak) PeakStart(o, end);
        else if (id != "burns_twice" && !IsLongCut)
        {
            spendLightReal = true;
            spendAt = t;
            var bt = FlareFamily.Beat;
            SpendLight(cueAt + Vector3.Up * 2.5f, new Color(1f, 0.75f, 0.4f), (float)(Night ? bt.SpendLight : bt.SpendLightDay));
        }
        if (HasPeak) spendAt = t;
        Cam?.JoltPx(axis, (float)FlareFamily.Beat.KickPx * (Motion >= 1 ? 1 : Motion > 0 ? 0.5f : 0));
        ResolvePending();
        if (Perf.On) GD.Print($"flare perf blow t {Perf.Now:0.0000}");
        if (Args.Has("clip") || Args.Has("shot"))
            GD.Print($"flare blow {id}: main {part} at +{rt - pressRt:0.000} s real from the press (Flare time {t:0.000}), band from ({o.X:0.0},{o.Y:0.0}){(end != o ? $" along to ({end.X:0.0},{end.Y:0.0})" : "")}, kick {FlareFamily.Beat.KickPx:0.#} px");
    }

    /// <summary>How far a point lies from the band's origin (a line Flare's: from its line).</summary>
    float BandDist(float x, float z)
    {
        var w = new Vector2(x, z);
        var ab = bandB - bandA;
        float l2 = ab.LengthSquared();
        float h = l2 > 1e-4f ? Mathf.Clamp((w - bandA).Dot(ab) / l2, 0, 1) : 0;
        return (w - bandA - ab * h).Length();
    }

    /// <summary>When the band's front reaches this point (Flare time); Held before the main blow.</summary>
    double BandTime(float x, float z) => blowT < 0 ? Held : blowT + BandAfter(BandDist(x, z));

    /// <summary>How long after the main blow (Flare time) the band's front stands this far out (m).</summary>
    static double BandAfter(float dist)
    {
        var br = FlareFamily.Band;
        float d = Mathf.Clamp(dist / (float)Math.Max(1, br.Reach), 0, 1);
        return br.Time * (1 - Math.Pow(1 - d, 1 / Math.Max(0.2, br.Ease)));
    }

    /// <summary>How far out the band's front stands this long after the main blow (Flare time, m).</summary>
    static float BandFront(double since)
    {
        var br = FlareFamily.Band;
        double x = Math.Clamp(since / Math.Max(br.Time, 1e-3), 0, 1);
        return (float)(br.Reach * (1 - Math.Pow(1 - x, Math.Max(0.2, br.Ease))));
    }

    /// <summary>The main blow's hitstop lets the Flare's clock run (r3): set on the blow, cleared when the stop ends.</summary>
    bool hitstopRuns;

    /// <summary>For the marks (FlareMarksView): when the band reaches this point, Flare time (Held before the main blow).</summary>
    public double BandReaches(float x, float z) => BandTime(x, z);

    /// <summary>For the marks: real seconds from now until the band reaches this point (0 passed; Held before the main blow).
    /// Flare time runs at a tenth through the blow's hitstop, so this is the clock's own estimate.</summary>
    public double BandReachesRt(float x, float z)
    {
        double bt = BandTime(x, z);
        if (bt >= Held) return Held;
        double left = bt - t;
        if (left <= 0) return 0;
        if (hitstopRuns) return left;
        double stopFlare = Stop * 0.1;
        return left <= stopFlare ? left / 0.1 : Stop + (left - stopFlare);
    }

    /// <summary>For the marks: the main blow's real time on the Flare's real clock (FlareFx rt), -1 before it.</summary>
    public double BlowAtRt => blowRt;

    /// <summary>For CrowdView: a struck body's band rim (0 none): on for BandRimFrames drawn frames from the band reaching it.</summary>
    public float BandRim(int enemy)
    {
        if (!Active || !bandStruck.TryGetValue(enemy, out var s) || s.Frame < 0) return 0;
        long age = (long)Engine.GetFramesDrawn() - s.Frame;
        return age >= 0 && age < BandRimFrames ? (age == 0 ? 1f : 0.75f) * (Night ? 0.8f : 1f) : 0;
    }

    /// <summary>A struck body for the band's rim (its first place).</summary>
    void BandStrike(int target, float x, float z)
    {
        if (!familyOn || target < 0 || bandStruck.ContainsKey(target)) return;
        bandStruck[target] = (new Vector2(x, z), -1);
    }

    /// <summary>The plain Flares' kills not yet given a moment: at the main blow (and after it) the band's, before it
    /// their own blow's.</summary>
    void ResolvePending()
    {
        if (IsLongCut || id == "burns_twice") return;
        foreach (var d in doomed.Values)
        {
            if (!d.Pending) continue;
            d.Pending = false;
            d.At = blowT >= 0 ? Math.Max(t + 0.02, BandTime(d.Where.X, d.Where.Z)) : t + 0.02;
        }
    }

    /// <summary>Whether a decision-marked hit waits for its mark: shown under the data's frames ago, or not shown yet
    /// (a mark made at the hit's own tick reaches the view a frame later; 0.1 s at most).</summary>
    bool MarkHolds(int enemy, double bornRt)
    {
        if (marksView == null || !familyOn) return false;
        double s = marksView.ShownAt(enemy);
        if (s < 0) return rt - bornRt < 0.1;
        return rt < s + FlareFamily.Beat.DecisionFrames / 60.0;
    }

    /// <summary>A Flare hit's number (BattleFx): held from the press, released as the band passes its foe. False: not
    /// held (show it now).</summary>
    public bool HoldNumber(int target, Vector3 at, double amount, double maxHp, bool crit)
    {
        if (!Active || !familyOn) return false;
        held.Add((target, at, amount, maxHp, crit, rt));
        BandStrike(target, at.X, at.Z);
        return true;
    }

    /// <summary>A real-time step of the blow: the band's uniform, the numbers' release, the pending, her ember's pool.</summary>
    void BlowTick()
    {
        if (!Active) return;
        // The kills no blow event resolved last frame (a rout, a kill between blows): their moment now.
        if (doomed.Count > 0 && !IsLongCut && id != "burns_twice")
            foreach (var d in doomed.Values)
                if (d.Pending && d.BornRt < rt - 1e-6) { d.Pending = false; d.At = blowT >= 0 ? Math.Max(t + 0.02, BandTime(d.Where.X, d.Where.Z)) : t + 0.02; }
        var br = FlareFamily.Band;
        if (bandOn)
        {
            // The front: its progress over its run (Flare time), its light the school's glow x the data's (x albedo), the
            // ground lit behind it for `after` s, faded over the run's last share.
            float x = (float)((t - blowT) / Math.Max(br.Time, 1e-3));
            if (x > 1.05f) { bandOn = false; RenderingServer.GlobalShaderParameterSet(BandParam, Vector4.Zero); }
            else
            {
                float k = 1 - Mathf.SmoothStep(1 - (float)br.Fade, 1.05f, x);
                var bl = br.Of(Night);
                var c = BandHue().SrgbToLinear() * (float)bl.Front * (LessFlash ? 0.6f : 1f);
                RenderingServer.GlobalShaderParameterSet(BandParam, new Vector4(bandA.X, bandA.Y, x, k));
                RenderingServer.GlobalShaderParameterSet(BandLineParam, new Vector4(bandB.X, bandB.Y, (float)br.Lead, (float)br.After));
                RenderingServer.GlobalShaderParameterSet(BandColParam, new Vector4(c.R, c.G, c.B, (float)bl.Tail));
                RenderingServer.GlobalShaderParameterSet(BandShapeParam, new Vector4((float)br.Reach, (float)br.Time, (float)br.Ease, 0));
                RenderingServer.GlobalShaderParameterSet(BandEdgeParam, new Vector4((float)br.Edge, (float)br.Trough, (float)br.Dark, (float)bl.Glow * (LessFlash ? 0.6f : 1f)));
            }
        }
        RippleTick();
        PeakTick();
        // The struck bodies' rims as the band reaches each, and the kills the HUD's count holds back.
        if (blowT >= 0 && bandStruck.Count > 0)
        {
            long now = (long)Engine.GetFramesDrawn();
            foreach (var kv in new List<KeyValuePair<int, (Vector2 At, long Frame)>>(bandStruck))
                if (kv.Value.Frame < 0 && t >= BandTime(kv.Value.At.X, kv.Value.At.Y)) bandStruck[kv.Key] = (kv.Value.At, now);
        }
        int kh = 0;
        foreach (var kv in doomed)
            if (DeathOf(kv.Key) == 1 && (kv.Value.Pending || t < kv.Value.At || MarkHolds(kv.Key, kv.Value.BornRt))) kh++;
        KillsHeld = kh;
        // The numbers: one burst, each as the band passes its foe (and a decision's after its mark has shown).
        if (held.Count > 0 && blowT >= 0)
        {
            double lag = FlareFamily.Beat.NumberLag;
            for (int i = 0; i < held.Count; i++)
            {
                var h = held[i];
                if (t < BandTime(h.At.X, h.At.Z) + lag || MarkHolds(h.Target, h.BornRt)) continue;
                // (r3, judge r2 fix 2: the Long Cut's line victims, past the twelve on screen, are told as one total at the
                // seam's far end as the band leaves the last of them; a crit, the Main's, keeps its own)
                if (IsLongCut && !h.Crit && doomed.TryGetValue(h.Target, out var dm) && !dm.Ash && !dm.Pending)
                {
                    lineTotal += h.Amount; lineTotalN++;
                    var (al, _) = SeamNear(h.At.X, h.At.Z);
                    var sp = SeamPoint(Math.Min(lcLen, al + 1.2f));
                    if (lineTotalN == 1 || al > lineTotalAlong) { lineTotalAt = sp; lineTotalAlong = al; }
                    lineTotalDue = t;
                }
                else Number(h.Target, h.At, h.Amount, h.MaxHp, h.Crit);
                held.RemoveAt(i--);
            }
        }
        if (lineTotalN > 0 && t > lineTotalDue + 1e-6)
        {
            bool more = false;
            foreach (var h in held) if (doomed.TryGetValue(h.Target, out var dm) && !dm.Ash && !h.Crit) { more = true; break; }
            if (!more)
            {
                Total(lineTotalAt + Vector3.Up * 1.2f, lineTotal);
                if (Args.Has("clip") || Args.Has("shot")) GD.Print($"flare line total {id}: {lineTotal:0} over {lineTotalN} on the line at +{rt - blowRt:0.000} s real from the blow, drawn {Engine.GetFramesDrawn()}");
                lineTotalN = 0; lineTotal = 0;
            }
        }
        // Her ember's pool: up at the main blow, held, then back.
        float pool = 1;
        if (blowT >= 0)
        {
            var rc = FlareFamily.Recovery;
            float s = (float)(rt - blowRt);
            float up = Mathf.SmoothStep(0, 1, s / 0.08f);
            float down = 1 - Mathf.SmoothStep(0, 1, (s - (float)rc.Hold) / Mathf.Max((float)rc.Out, 1e-3f));
            pool = 1 + ((float)rc.Pool - 1) * up * down;
        }
        // (r2 fix 6: her ember's pool up through the stop with the grade, grade.pool; the recovery's takes over as it eases out)
        if (familyOn) pool = Mathf.Max(pool, 1 + ((float)FlareFamily.Grades.Pool - 1) * gradeNow);
        if (pool != poolNow) { poolNow = pool; EmberPool(pool); }
        if (!mainLogged && blowT >= 0 && t > blowT + br.Time + 0.05 && (Args.Has("clip") || Args.Has("shot")))
        {
            mainLogged = true;
            GD.Print($"flare band {id}: front {br.Reach:0} m in {br.Time:0.00} s Flare time ({rt - blowRt:0.000} s real with the hitstop), numbers still held {held.Count}");
        }
    }

    /// <summary>The band's light: the Flare's school's glow (its max channel 1).</summary>
    Color BandHue()
    {
        var g = Palette.Of(Content.Lamps.Flare(id)?.School ?? School.Holy).Glow;
        float m = Mathf.Max(g.R, Mathf.Max(g.G, g.B));
        return m > 0 ? new Color(g.R / m, g.G / m, g.B / m) : Colors.White;
    }

    /// <summary>When a drop lying here shows after the main blow (Flare time; Held before it).</summary>
    double BandDropAt(float x, float z) => blowT < 0 ? Held : BandTime(x, z) + FlareFamily.Beat.DropLag;

    /// <summary>The cast's end: the held numbers out, her pool back, the band gone.</summary>
    void BlowClear()
    {
        foreach (var h in held) Number(h.Target, h.At, h.Amount, h.MaxHp, h.Crit);
        held.Clear();
        blowT = blowRt = -1;
        bandOn = false;
        hitstopRuns = false;
        lineTotal = 0; lineTotalN = 0; lineTotalAt = Vector3.Zero; lineTotalDue = Held;
        rippleT = -1;
        bandStruck.Clear();
        KillsHeld = 0;
        PeakOff();
        RenderingServer.GlobalShaderParameterSet(BandParam, Vector4.Zero);
        if (poolNow != 1) { poolNow = 1; EmberPool(1); }
    }
}

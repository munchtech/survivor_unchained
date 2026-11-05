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
/// </summary>
public partial class FlareFx
{
    /// <summary>A Flare's damage number, released (BattleFx: Hits.Tally).</summary>
    public Action<int, Vector3, double, double, bool> Number = (_, _, _, _, _) => { };
    /// <summary>Her ember's pool (x her light; 1 none): PlayerView.FlarePool.</summary>
    public Action<float> EmberPool = _ => { };

    double blowT = -1, blowRt = -1, pressRt = -1;
    Vector2 bandA, bandB;
    bool bandOn, mainLogged;
    static readonly bool BandOff = Args.Has("flare-band-off");
    float poolNow = 1;
    readonly List<(int Target, Vector3 At, double Amount, double MaxHp, bool Crit, double BornRt)> held = new();
    static readonly StringName BandParam = "flare_band", BandLineParam = "flare_band_line", BandColParam = "flare_band_col";

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
        var end = from == "line" ? new Vector2((float)e.TX, (float)e.TZ) : o;
        var dir = end - o;
        var axis = from == "line" && dir.LengthSquared() > 1e-4f ? new Vector3(dir.X, 0, dir.Y).Normalized() * 0.4f + Vector3.Up : Vector3.Up;
        MainBlowAt(o, end, new Vector3((float)e.TX, (float)HeightAt(e.TX, e.TZ), (float)e.TZ), axis, e.Part);
    }

    void MainBlowAt(Vector2 o, Vector2 end, Vector3 cueAt, Vector3 axis, string part)
    {
        if (!familyOn || blowT >= 0) return;
        blowT = t; blowRt = rt;
        bandA = o; bandB = end; bandOn = !BandOff; // (--flare-band-off: an ablation, the band never drawn)
        Cue("boom", cueAt, 1);
        Rumble(1, 0.6f, 0.14f);
        Cam?.JoltPx(axis, (float)FlareFamily.Beat.KickPx * (Motion >= 1 ? 1 : Motion > 0 ? 0.5f : 0));
        ResolvePending();
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
    double BandTime(float x, float z)
    {
        if (blowT < 0) return Held;
        var br = FlareFamily.Band;
        float d = Mathf.Clamp(BandDist(x, z) / (float)Math.Max(1, br.Reach), 0, 1);
        double k = 1 - Math.Pow(1 - d, 1 / Math.Max(0.2, br.Ease));
        return blowT + br.Time * k;
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
            float x = (float)((t - blowT) / Math.Max(br.Time, 1e-3));
            if (x > 1.05f) { bandOn = false; RenderingServer.GlobalShaderParameterSet(BandParam, Vector4.Zero); }
            else
            {
                float xc = Mathf.Clamp(x, 0, 1);
                float front = (float)br.Reach * (1 - Mathf.Pow(1 - xc, (float)br.Ease));
                float k = 1 - Mathf.SmoothStep(1 - (float)br.Fade, 1.05f, x);
                var bl = br.Of(Night);
                var c = BandHue() * (float)bl.Gain;
                RenderingServer.GlobalShaderParameterSet(BandParam, new Vector4(bandA.X, bandA.Y, front, k));
                RenderingServer.GlobalShaderParameterSet(BandLineParam, new Vector4(bandB.X, bandB.Y, (float)br.Lead, (float)br.Wake));
                RenderingServer.GlobalShaderParameterSet(BandColParam, new Vector4(c.R, c.G, c.B, (float)bl.Wake));
            }
        }
        // The numbers: one burst, each as the band passes its foe (and a decision's after its mark has shown).
        if (held.Count > 0 && blowT >= 0)
        {
            double lag = FlareFamily.Beat.NumberLag;
            for (int i = 0; i < held.Count; i++)
            {
                var h = held[i];
                if (t < BandTime(h.At.X, h.At.Z) + lag || MarkHolds(h.Target, h.BornRt)) continue;
                Number(h.Target, h.At, h.Amount, h.MaxHp, h.Crit);
                held.RemoveAt(i--);
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
        RenderingServer.GlobalShaderParameterSet(BandParam, Vector4.Zero);
        if (poolNow != 1) { poolNow = 1; EmberPool(1); }
    }
}

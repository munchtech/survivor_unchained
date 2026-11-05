using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// The PEAK at a Strike's main blow (H7 r2, judge r1 fix 1; data/content/flare_family.json "peak" and each Flare's
/// "peak" shape): 3-4 frames lit FROM the blow in dawn gold by a real light rig, not a full-screen flash. A disk (Bell of
/// the Morning: the blast 8 m round her) is one shadowed omni at its heart, a column of light standing out of it and the
/// lit disk on the ground (flare_world flare_peak_at); a line (the Long Cut: its seam) is a row of low omnis along its
/// whole length, so the bodies on it are lit from below, and the lit strip on the ground. The envelope runs on drawn
/// frames (real time), so the blow's hitstop holds the world, never the light. FLARE_LOOK §1.6's caps hold it: the frame's
/// mean under 1.5x the pre-press for at most 4 frames, once per Strike; at most 3% over the knee (tools/fx/flare_measure.py).
/// Derived from: the judge's ranked fix 1 (r1, a5d84d8d) and §1.6's budget; the rig's light is the LC's own sweep lights'
/// kind (FlareFx.LongCutLight: short-range, steep falloff), the column the LC Spend's strip (flare_streak, column 1).
/// Also here: a ripple of air and dust on the earlier blows of a Flare whose data names them (Bell's first two tolls:
/// no light, no whole-frame swing), drawn through the band's own ground hook in its dust mode.
/// </summary>
public partial class FlareFx
{
    readonly List<OmniLight3D> peakLights = new();
    OmniLight3D? peakHeart;
    MeshInstance3D? peakColumnFx;
    ImmediateMesh? peakColumnMesh;
    ShaderMaterial? peakColumnMat;
    long peakFrame = -1;
    int peakN;
    Vector2 peakA, peakB;
    bool peakLine;
    float peakColumn;
    static readonly StringName PeakParam = "flare_peak", PeakLineParam = "flare_peak_line", PeakColParam = "flare_peak_col", BandShapeParam = "flare_band_shape";

    /// <summary>Whether this Flare's main blow has a peak (its data's shape).</summary>
    bool HasPeak => familyOn && FlareFamily.Of(id).Peak.Shape.Length > 0;

    /// <summary>The main blow's hitstop: the family's peak's (drawn frames) for a Flare with a peak, else the Strike's own.</summary>
    int MainHitstop(int own) => HasPeak ? FlareFamily.Peak.Hitstop : own;

    /// <summary>Made at the press (a Flare with a peak), and shown once unlit, so the blow pays no first use.</summary>
    void PeakMake()
    {
        if (!HasPeak) return;
        var pk = FlareFamily.Peak;
        if (peakHeart == null)
        {
            // (the disk's heart: shadowed, so the bodies round her throw their shadows outward from the blow)
            peakHeart = new OmniLight3D { LightEnergy = 0, ShadowEnabled = true, Visible = false, OmniAttenuation = 1.3f };
            AddChild(peakHeart);
        }
        while (peakLights.Count < Math.Max(1, pk.Lights))
        {
            var l = new OmniLight3D { LightEnergy = 0, ShadowEnabled = false, Visible = false, OmniAttenuation = 1.6f };
            AddChild(l);
            peakLights.Add(l);
        }
        if (peakColumnFx == null) peakColumnFx = LcStrip(out peakColumnMesh, out peakColumnMat, true);
        // (warm: one frame drawn at no light, in view)
        if (peakColumnMat != null && peakColumnMesh != null)
        {
            peakColumnMat.SetShaderParameter("col", new Color(0, 0, 0, 0));
            LcStripDraw(peakColumnMesh, peakColumnMat, Her, Her + Vector3.Up * 0.1f, 0.01f);
            peakColumnFx!.Visible = true;
        }
    }

    /// <summary>The peak on the main blow: o the blow's heart (a line's start), end a line's far end.</summary>
    void PeakStart(Vector2 o, Vector2 end)
    {
        if (!HasPeak) return;
        var own = FlareFamily.Of(id).Peak;
        var pk = FlareFamily.Peak;
        peakLine = own.Shape == "line" && (end - o).LengthSquared() > 1e-2f;
        peakA = o; peakB = peakLine ? end : o;
        peakColumn = peakLine ? 0 : (float)own.Column;
        peakFrame = (long)Engine.GetFramesDrawn();
        var col = Color.FromHtml(pk.Color);
        float range = (float)pk.Range;
        if (peakLine)
        {
            float len = (peakB - peakA).Length();
            peakN = Math.Clamp((int)Math.Ceiling(len / Math.Max(1, pk.Spacing)) + 1, 2, peakLights.Count);
            for (int i = 0; i < peakLights.Count; i++)
            {
                var l = peakLights[i];
                l.Visible = false;
                if (i >= peakN) continue;
                var p = peakA.Lerp(peakB, i / (float)(peakN - 1));
                l.GlobalPosition = new Vector3(p.X, (float)HeightAt(p.X, p.Y) + (float)pk.Height, p.Y);
                l.LightColor = col;
                l.OmniRange = range;
            }
        }
        else if (peakHeart != null)
        {
            peakN = 0;
            peakHeart.GlobalPosition = new Vector3(o.X, (float)HeightAt(o.X, o.Y) + 1.4f, o.Y);
            peakHeart.LightColor = col;
            peakHeart.OmniRange = (float)own.Radius * 1.3f;
        }
        if (Args.Has("clip") || Args.Has("shot"))
            GD.Print($"flare peak {id}: {(peakLine ? $"line of {peakN} lights" : $"disk {own.Radius:0.#} m, column {own.Column:0.#} m")}, frames [{string.Join(", ", pk.Frames)}], hitstop {pk.Hitstop} f, drawn {peakFrame}");
    }

    /// <summary>The peak's frame (real time): the rig's light, the lit shape's uniform, the column.</summary>
    void PeakTick()
    {
        if (peakFrame < 0) { if (peakColumnFx is { Visible: true } && rt - pressRt > 0.05) peakColumnFx.Visible = false; return; }
        var pk = FlareFamily.Peak;
        long f = (long)Engine.GetFramesDrawn() - peakFrame;
        float env = f >= 0 && f < pk.Frames.Length ? (float)pk.Frames[f] : 0;
        env *= LessFlash ? 0.5f : 1f;
        var pl = pk.Of(Night);
        float gain = (float)FlareFamily.Of(id).Peak.Gain;
        var col = Color.FromHtml(pk.Color);
        // (linear, for the ground's light: x albedo)
        var lin = col.SrgbToLinear();
        if (env <= 0)
        {
            PeakOff();
            return;
        }
        if (peakLine)
            for (int i = 0; i < peakN; i++) { peakLights[i].LightEnergy = (float)pl.Light * gain * env; peakLights[i].Visible = true; }
        else if (peakHeart != null) { peakHeart.LightEnergy = (float)pl.Light * gain * env; peakHeart.Visible = true; }
        RenderingServer.GlobalShaderParameterSet(PeakParam, new Vector4(peakA.X, peakA.Y, peakLine ? (float)FlareFamily.Of(id).Peak.Width : (float)FlareFamily.Of(id).Peak.Radius, env));
        RenderingServer.GlobalShaderParameterSet(PeakLineParam, new Vector4(peakB.X, peakB.Y, peakLine ? 1 : 0, 0));
        float g = (float)pl.Ground * gain;
        RenderingServer.GlobalShaderParameterSet(PeakColParam, new Vector4(lin.R * g, lin.G * g, lin.B * g, 0));
        if (peakColumn > 0 && peakColumnFx != null && peakColumnMesh != null && peakColumnMat != null)
        {
            // (it stands 0.45 m toward the eye from her heart, so her own body never hides its foot: LcColumn's lesson)
            var foot = new Vector3(peakA.X, (float)HeightAt(peakA.X, peakA.Y) + 0.02f, peakA.Y);
            var toEye = EyeAt() - foot;
            toEye.Y = 0;
            if (toEye.LengthSquared() > 1e-4f) foot += toEye.Normalized() * 0.45f;
            float h = peakColumn * Mathf.Clamp(0.45f + 0.55f * (f + 1) / 2f, 0, 1);
            peakColumnMat.SetShaderParameter("col", new Color(1f, 0.86f, 0.6f, (float)pl.Column * gain * env));
            LcStripDraw(peakColumnMesh, peakColumnMat, foot, foot + Vector3.Up * h, 0.38f);
            peakColumnFx.Visible = true;
        }
        if (Args.Has("clip") && f < pk.Frames.Length) GD.Print($"flare peak frame {f}: light {env:0.00}, drawn {Engine.GetFramesDrawn()}");
    }

    void PeakOff()
    {
        if (peakFrame < 0 && peakColumnFx is { Visible: false }) return;
        peakFrame = -1;
        foreach (var l in peakLights) { l.LightEnergy = 0; l.Visible = false; }
        if (peakHeart != null) { peakHeart.LightEnergy = 0; peakHeart.Visible = false; }
        if (peakColumnFx != null) peakColumnFx.Visible = false;
        RenderingServer.GlobalShaderParameterSet(PeakParam, Vector4.Zero);
    }

    /* ------------------------------------------------------------------ the ripple: an earlier blow's air and dust -- */

    double rippleT = -1;
    Vector2 rippleO;

    /// <summary>Whether this Blow event is one of a Flare's ripples (its data's part, before the main blow).</summary>
    bool IsRipple(Ev.Flare e) => familyOn && blowT < 0 && FlareFamily.Of(id).Ripple is { Length: > 0 } r && e.Part == r;

    /// <summary>An air and dust ripple out of her (no light): the band's ground hook in its dust mode, and dust thrown out.</summary>
    void RippleStart(Ev.Flare e)
    {
        var rp = FlareFamily.Ripple;
        rippleT = t;
        rippleO = new Vector2((float)e.X, (float)e.Z);
        // The dust: puffs thrown out in a ring at her feet, slowing as they spread, a dark dust by night, a sunlit one by day.
        var dust = Night ? new Color(0.17f, 0.16f, 0.16f, 0.42f) : new Color(0.45f, 0.38f, 0.3f, 0.42f);
        float speed = (float)(rp.Reach / Math.Max(rp.Time, 1e-3)) * 0.55f;
        for (int i = 0; i < rp.Puffs; i++)
        {
            float a = (i + R() * 0.6f) / rp.Puffs * Mathf.Tau;
            var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            var p = new Vector3(rippleO.X, 0, rippleO.Y) + dir * (1.1f + R() * 0.4f);
            p.Y = (float)HeightAt(p.X, p.Z) + 0.2f + R() * 0.15f;
            bed.Spawn(FlareBits.Kind.Puff, p, dir * speed * (0.8f + R() * 0.4f) + Vector3.Up * 0.3f, 0.55f + R() * 0.2f, 0.45f + R() * 0.15f,
                dust, new Color(dust.R, dust.G, dust.B, 0), sizeEnd: 1.3f, drag: 4.5f);
        }
        if (Args.Has("clip") || Args.Has("shot")) GD.Print($"flare ripple {id}: {e.Part} at +{rt - pressRt:0.000} s real, {rp.Reach:0} m in {rp.Time:0.00} s, {rp.Puffs} puffs");
    }

    /// <summary>The ripple's step (Flare time), while the main band is not running.</summary>
    void RippleTick()
    {
        if (rippleT < 0 || bandOn) return;
        var rp = FlareFamily.Ripple;
        float x = (float)((t - rippleT) / Math.Max(rp.Time, 1e-3));
        if (x > 1.05f) { rippleT = -1; RenderingServer.GlobalShaderParameterSet(BandParam, Vector4.Zero); return; }
        float k = 1 - Mathf.SmoothStep(0.6f, 1.05f, x);
        RenderingServer.GlobalShaderParameterSet(BandParam, new Vector4(rippleO.X, rippleO.Y, x, k));
        RenderingServer.GlobalShaderParameterSet(BandLineParam, new Vector4(rippleO.X, rippleO.Y, (float)rp.Lead, 0));
        RenderingServer.GlobalShaderParameterSet(BandColParam, Vector4.Zero);
        RenderingServer.GlobalShaderParameterSet(BandShapeParam, new Vector4((float)rp.Reach, (float)rp.Time, 1.2f, (float)rp.Dust));
    }
}

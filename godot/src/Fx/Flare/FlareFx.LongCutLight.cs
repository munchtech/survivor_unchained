using System;
using Godot;

namespace SurvivorUnchained.View;

/* The Long Cut's local light (vfx9 r3b, the judge's fixes 2 and 3: "light is shown by what it lights", FLARE_LOOK 69):
 * every light here has a range of 8 m or less with a steep falloff, and nothing lifts the exposure. At night the field
 * outside her keeps its value; by day the sun and the sky's ambient dip to 0.65 over the sweep and cleave
 * (Atmosphere.FlareLight) so the chain of lights carries the frame.
 * - The press: the blade's white-gold core along the real steel (an additive camera-facing strip, HDR 7), a 2.5 m
 *   light at her hands and a rim behind her (2.5x by day), at most 20 gold motes.
 * - The sweep: a knee-height band of light 1.5-2 m wide behind its leading edge across the reach (flare_world
 *   flare_sweep_at, times the albedo), three unshadowed lights riding the edge at 0.5 m to rim the legs, the shimmer
 *   behind it (flare_haze in its sweep mode).
 * - The Spend: a short soft column at her for 4 frames (under the knee but for its peak frame), a lit pool at its foot. */
public partial class FlareFx
{
    OmniLight3D? lcHandLight;
    readonly OmniLight3D?[] lcSweepL = new OmniLight3D?[3];
    MeshInstance3D? lcBladeFx, lcColumnFx, lcSweepHaze;
    ImmediateMesh? lcBladeMesh, lcColumnMesh;
    ShaderMaterial? lcBladeMat, lcColumnMat, lcHazeMat;
    long lcSpendFrame = -1;
    double lcSpendRt = -1;
    int lcMoteN;

    /// <summary>Look-dev: the sweep band's light scaled (LC_BAND).</summary>
    static readonly float LcBand = float.TryParse(System.Environment.GetEnvironmentVariable("LC_BAND"), System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var lcb) ? lcb : 1f;

    /// <summary>By day the press's lights need 2.5x their night energy to be seen under the sun.</summary>
    float LcDay => Night ? 1f : 2.5f;

    /// <summary>The blade's core peak (HDR) and the sweep band's light (x albedo), night and day.</summary>
    const float BladeHdr = 7f, BandNight = 0.6f, BandDay = 7f;

    void LcLightsMake()
    {
        if (lcHandLight == null)
        {
            lcHandLight = LcLightNew(false);
            lcHandLight.OmniAttenuation = 2f;
            lcHandLight.LightColor = new Color(1f, 0.8f, 0.5f);
        }
        for (int i = 0; i < lcSweepL.Length; i++)
            if (lcSweepL[i] == null)
            {
                var l = LcLightNew(false);
                l.OmniAttenuation = 2f;
                l.OmniRange = 3.5f;
                l.LightColor = new Color(1f, 0.76f, 0.44f);
                lcSweepL[i] = l;
            }
        if (lcBladeFx == null) lcBladeFx = LcStrip(out lcBladeMesh, out lcBladeMat, false);
        if (!lcLateHooked) { RenderingServer.FramePreDraw += LcStripsLate; lcLateHooked = true; }
        if (lcColumnFx == null) lcColumnFx = LcStrip(out lcColumnMesh, out lcColumnMat, true);
        if (lcSweepHaze == null)
        {
            lcHazeMat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/flare_haze.gdshader"), RenderPriority = -100 };
            lcHazeMat.SetShaderParameter("sweep", 1f);
            lcSweepHaze = new MeshInstance3D
            {
                Mesh = new PlaneMesh { Size = new Vector2(2, 2) },
                MaterialOverride = lcHazeMat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, Visible = false, ExtraCullMargin = 8,
            };
            AddChild(lcSweepHaze);
        }
    }

    bool lcBladeLate, lcLateHooked;

    /// <summary>The blade's strip from the steel's pose as it will be drawn (RenderingServer.FramePreDraw).</summary>
    void LcStripsLate()
    {
        if (!IsInstanceValid(this) || !lcBladeLate || lcBladeMesh == null || lcBladeMat == null || !HasBlade) return;
        LcStripDraw(lcBladeMesh, lcBladeMat, BladeAt(0.08f), BladeAt(1f), 0.05f);
    }

    public override void _ExitTree()
    {
        if (lcLateHooked) { RenderingServer.FramePreDraw -= LcStripsLate; lcLateHooked = false; }
    }

    MeshInstance3D LcStrip(out ImmediateMesh mesh, out ShaderMaterial mat, bool column)
    {
        mesh = new ImmediateMesh();
        mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/flare_streak.gdshader") };
        mat.SetShaderParameter("column", column ? 1f : 0f);
        var n = new MeshInstance3D
        {
            Mesh = mesh, MaterialOverride = mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, Visible = false,
            TopLevel = true, CustomAabb = new Aabb(new Vector3(-1e4f, -1e3f, -1e4f), new Vector3(2e4f, 2e3f, 2e4f)),
        };
        AddChild(n);
        return n;
    }

    /// <summary>A strip from a to b, facing the eye about its own axis, half as wide as `half` (m).</summary>
    void LcStripDraw(ImmediateMesh m, ShaderMaterial mat, Vector3 a, Vector3 b, float half)
    {
        var axis = b - a;
        var side = axis.Cross(EyeAt() - (a + b) * 0.5f);
        side = side.LengthSquared() > 1e-8f ? side.Normalized() * half : Vector3.Right * half;
        m.ClearSurfaces();
        m.SurfaceBegin(Mesh.PrimitiveType.Triangles, mat);
        void V(Vector3 p, float u, float v) { m.SurfaceSetUV(new Vector2(u, v)); m.SurfaceAddVertex(p); }
        V(a - side, 0, 0); V(a + side, 1, 0); V(b + side, 1, 1);
        V(a - side, 0, 0); V(b + side, 1, 1); V(b - side, 0, 1);
        m.SurfaceEnd();
    }

    /// <summary>The Spend (the sweep's start): the column's frames count from here.</summary>
    void LcSpend()
    {
        lcSpendFrame = (long)Engine.GetFramesDrawn();
        lcSpendRt = lcRt;
    }

    /// <summary>The press and hold: the blade's core, the light at her hands, her rim; the core rides the sweep and the
    /// cleave's bite too.</summary>
    void LcPressLights(float dt, bool held, float steel)
    {
        LcLightsMake();
        float flash = LessFlash ? 0.6f : 1f;
        // Her rim: behind her from the eye, 3 m.
        var back = Her - EyeAt();
        back.Y = 0;
        back = back.LengthSquared() > 1e-4f ? back.Normalized() : Vector3.Forward;
        headLight.LightColor = new Color(1f, 0.8f, 0.5f);
        headLight.OmniRange = 3.0f;
        headLight.OmniAttenuation = 2f;
        headLight.GlobalPosition = Her + back * 0.8f + Vector3.Up * 1.5f;
        headLight.LightEnergy = 2.0f * steel * LcDay * flash * LcLight;

        // The light at her hands (the grip), 2.5 m.
        float hand = held ? steel : 0;
        if (lcHandLight != null && lcSpendFrame < 0)
        {
            lcHandLight.GlobalPosition = BladeAt(0) + (EyeAt() - BladeAt(0)).Normalized() * 0.15f;
            lcHandLight.OmniRange = 2.5f;
            lcHandLight.LightEnergy = 1.6f * hand * LcDay * flash * LcLight;
            lcHandLight.Visible = lcHandLight.LightEnergy > 0.01f;
        }

        // The steel's own white-gold core: through the hold, the sweep and the cleave's bite.
        float core = 0;
        if (held) core = Mathf.Min(1, (float)t / 0.05f);
        else if (lcSweepT >= 0) core = 1 - Mathf.SmoothStep(SweepLen, SweepLen + 0.12f, (float)(t - lcSweepT));
        if (lcCleaveT >= 0) core = Mathf.Max(core, 1 - Mathf.SmoothStep(0.04f, 0.14f, (float)(t - lcCleaveT)));
        if (lcBladeFx != null && lcBladeMesh != null && lcBladeMat != null)
        {
            bool on = HasBlade && core > 0.01f;
            lcBladeFx.Visible = on;
            lcBladeLate = false;
            if (on)
            {
                lcBladeMat.SetShaderParameter("col", new Color(1f, 0.86f, 0.58f, BladeHdr * core * flash));
                // (drawn just before the frame is drawn, LcStripsLate: drawn here, from the hand's pose before this frame's
                // animation, it trailed the swinging steel by a frame)
                lcBladeLate = true;
            }
        }

        // Gold motes drawn up the edge, 20 at most with the press's burst (no white specks).
        if (held && lcMoteN < 20 && R() < dt * 30)
        {
            lcMoteN++;
            var p = BladeAt(R() * 0.5f);
            glow.Spawn(new FlareBits.P { Kind = FlareBits.Kind.Mote, At = p, V = (BladeAt(1) - BladeAt(0)).Normalized() * (1.2f + R()), Life = 0.35f, Size = 0.035f, SizeEnd = 0.02f, Color = new Color(1.1f, 0.66f, 0.24f), ColorEnd = DawnEnd });
        }
    }

    /// <summary>The sweep's lights riding its edge at 0.5 m (unshadowed, 3.5 m), its shimmer behind, the band's light.</summary>
    void LcSweepLights(float sweepK)
    {
        LcLightsMake();
        float flash = LessFlash ? 0.6f : 1f;
        float a = SweepLead();
        float[] rs = { 3f, 6.5f, 10f };
        for (int i = 0; i < lcSweepL.Length; i++)
        {
            var l = lcSweepL[i]!;
            float r = Mathf.Min(rs[i], reach * (0.25f + 0.3f * i));
            float ai = a - 0.6f / r;
            var p = new Vector3(at.X + Mathf.Cos(ai) * r, 0, at.Z + Mathf.Sin(ai) * r);
            p.Y = (float)HeightAt(p.X, p.Z) + 0.5f;
            l.GlobalPosition = p;
            l.LightEnergy = (Night ? 1.3f : 5f) * sweepK * flash * LcLight;
            l.Visible = l.LightEnergy > 0.01f;
        }
        if (lcSweepHaze != null && lcHazeMat != null)
        {
            lcSweepHaze.Visible = sweepK > 0.01f;
            if (lcSweepHaze.Visible)
            {
                float y = (float)HeightAt(at.X, at.Z);
                lcSweepHaze.GlobalPosition = new Vector3(at.X, y + 0.05f, at.Z);
                lcSweepHaze.Scale = new Vector3(reach + 2, 1, reach + 2);
                lcHazeMat.SetShaderParameter("center", at);
                lcHazeMat.SetShaderParameter("radius", reach);
                lcHazeMat.SetShaderParameter("lead", a);
                lcHazeMat.SetShaderParameter("swept", a - lcSweepFrom);
                lcHazeMat.SetShaderParameter("strength", sweepK * 0.8f);
                lcHazeMat.SetShaderParameter("age", (float)t);
            }
        }
    }

    float LcBandGain => (Night ? BandNight : BandDay) * LcBand * (LessFlash ? 0.6f : 1f);

    /// <summary>The Spend's column at her: 4 frames, under the knee but for its peak; a lit pool at its foot.</summary>
    void LcColumn()
    {
        if (lcColumnFx == null || lcColumnMesh == null || lcColumnMat == null || lcHandLight == null) return;
        long f = lcSpendFrame < 0 ? -1 : (long)Engine.GetFramesDrawn() - lcSpendFrame;
        (float h, float a) = f switch { 0 => (0.45f, 2.2f), 1 => (2.3f, 3.2f), 2 => (0.5f, 1.6f), 3 => (0.35f, 0.8f), _ => (0f, 0f) };
        float flash = LessFlash ? 0.6f : 1f;
        bool on = a > 0;
        lcColumnFx.Visible = on;
        if (lcSpendFrame >= 0 && f <= 4)
        {
            lcHandLight.Visible = on;
            lcHandLight.OmniRange = 3f;
            lcHandLight.LightEnergy = (Night ? 0.9f : 3.5f) * a * flash * LcLight;
        }
        if (!on) return;
        var foot = new Vector3(Her.X, (float)HeightAt(Her.X, Her.Z) + 0.02f, Her.Z);
        lcHandLight.GlobalPosition = foot + Vector3.Up * 0.35f;
        lcColumnMat.SetShaderParameter("col", new Color(1f, 0.84f, 0.55f, a * flash));
        LcStripDraw(lcColumnMesh, lcColumnMat, foot, foot + Vector3.Up * h, 0.3f);
        // (the pictures: a frame of the Spend's first two, each taken once the next is drawn)
        if (Args.Has("shot"))
        {
            GD.Print($"longcut column frame {f}: {h:0.00} m, HDR {a * flash:0.0}, drawn {Engine.GetFramesDrawn()}");
            if (f == 1) { Shots.WantFrames("bx_spend_a", 0); Shots.WantFrames("bx_spend_b", 1); }
        }
    }

    /// <summary>By day the sun and ambient dip to 0.65 from the Spend to the cleave's +0.35 s, back by +0.75 s (real).</summary>
    void LcDayDip()
    {
        if (Night || lcSpendRt < 0) { LightDip(1); return; }
        float up = Mathf.SmoothStep(0, 0.05f, (float)(lcRt - lcSpendRt));
        float down = lcCleaveRt < 0 ? 1 : 1 - Mathf.SmoothStep(0.35f, 0.75f, (float)(lcRt - lcCleaveRt));
        LightDip(1 - 0.35f * up * down * (LessFlash ? 0.6f : 1f));
    }

    void LcLightClear()
    {
        lcSpendFrame = -1; lcSpendRt = -1; lcMoteN = 0;
        foreach (var l in lcSweepL) if (l != null) { l.LightEnergy = 0; l.Visible = false; }
        if (lcHandLight != null) { lcHandLight.LightEnergy = 0; lcHandLight.Visible = false; }
        foreach (var n in new[] { lcBladeFx, lcColumnFx, lcSweepHaze }) if (n != null) n.Visible = false;
        if (headLight != null) headLight.OmniAttenuation = 1f;
        LightDip(1);
    }
}

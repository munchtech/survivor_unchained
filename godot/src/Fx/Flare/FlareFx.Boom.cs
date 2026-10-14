using System;
using Godot;

namespace SurvivorUnchained.View;

/* Burns Twice's BOOM as shapes (judge 2, s4: at +5 frames a 70 px soft flash and four pale rods, at +0.3 s a bead
 * chain of soft puffs, smaller than the embers' scars). ONE event bigger than any ember: the eye darkens for two
 * frames, then a torn 3 m ground flash (flare_world's flare_boom_flash) with a low light catching the statues'
 * rims; ONE pillar of fire, 1.9 m thick, at its full 7.5 m in 0.15 s (flare_pillar), under a dark smoke cap lit
 * from below that mushrooms out (flare_cap); jets of flame thrown along the ground; and the ring's heat riding its
 * line for its first third of a second (flare_haze). Its punch is size, the dark before it and the shimmer, never
 * more light (§1.6). */
public partial class FlareFx
{
    MeshInstance3D pillar = null!, cap = null!, haze = null!;
    ShaderMaterial pillarMat = null!, capMat = null!, hazeMat = null!;
    OmniLight3D rimLight = null!;
    readonly Vector3[] jets = new Vector3[12];
    int jetN;
    const float PillarH = 7.5f, PillarR = 0.95f;

    /* The simulated burst (tools/fxsim/boom_sim.py take burns_boom, cut by pack.py into art/fx/flare/burns_boom):
     * real fire and smoke rendered at the game's pitch, played once on one camera-facing quad. When it is there
     * it IS the pillar, the cap, the jets and the root's fire; the mesh shapes stay only as the fallback. */
    MeshInstance3D? simBoom;
    ShaderMaterial? simMat;
    int simFrames = 48;
    float simFps = 24;
    // The sim's camera framed SimSize metres across, centred SimLook metres over the crater; played SimRate times
    // its own speed (the column at full height in about 0.15 s).
    const float SimSize = 16.0f, SimLook = 4.5f, SimRate = 1.4f;
    // It starts SimFirst frames in (its first frames, a smooth star of tongues, read as a cartoon splat: s5f), so
    // the first frame on screen is already a fireball bursting; it swells the last fifth of its size over 0.12 s.
    // (burns_boom5 is born a lumpy white-hot heart at f1: from its first frame, no swell.)
    const float SimFirst = 0;
    bool Simmed => simBoom != null;

    void BoomReady()
    {
        pillarMat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/flare_pillar.gdshader") };
        capMat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/flare_cap.gdshader"), RenderPriority = 1 };
        // (First of the see-through things: the fire's own bits stay over its shimmer.)
        hazeMat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/flare_haze.gdshader"), RenderPriority = -100 };
        pillar = new MeshInstance3D
        {
            Mesh = new CylinderMesh { TopRadius = 1, BottomRadius = 1, Height = 1, RadialSegments = 40, Rings = 24, CapTop = false, CapBottom = false },
            MaterialOverride = pillarMat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, Visible = false,
            ExtraCullMargin = 4,
        };
        cap = new MeshInstance3D
        {
            Mesh = new SphereMesh { Radius = 1, Height = 2, RadialSegments = 40, Rings = 20 },
            MaterialOverride = capMat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, Visible = false,
            ExtraCullMargin = 4,
        };
        haze = new MeshInstance3D
        {
            Mesh = new PlaneMesh { Size = new Vector2(2, 2) },
            MaterialOverride = hazeMat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, Visible = false,
            ExtraCullMargin = 8,
        };
        rimLight = new OmniLight3D { LightColor = new Color(1f, 0.5f, 0.17f), LightEnergy = 0, OmniRange = 6.5f, ShadowEnabled = false };
        AddChild(pillar);
        AddChild(cap);
        AddChild(haze);
        AddChild(rimLight);
        const string fb = "res://art/fx/flare/burns_boom";
        if (FileAccess.FileExists(fb + ".json") && ResourceLoader.Exists(fb + ".png"))
        {
            var meta = Json.ParseString(FileAccess.GetFileAsString(fb + ".json")).AsGodotDictionary();
            simFrames = (int)meta["frames"].AsDouble();
            simFps = (float)meta["fps"].AsDouble();
            simMat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/flare_fb.gdshader") };
            simMat.SetShaderParameter("atlas", GD.Load<Texture2D>(fb + ".png"));
            simMat.SetShaderParameter("grid", (int)meta["grid"].AsDouble());
            simMat.SetShaderParameter("frames", simFrames);
            simBoom = new MeshInstance3D
            {
                Mesh = new QuadMesh { Size = Vector2.One }, MaterialOverride = simMat,
                CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, Visible = false, ExtraCullMargin = 8,
            };
            AddChild(simBoom);
        }
    }

    /// <summary>The last word lands at p: the pillar, its cap, the jets and the low light set off.</summary>
    void BoomStart(Vector3 p)
    {
        float seed = R();
        pillar.GlobalPosition = p + Vector3.Up * (PillarH * 0.5f - 0.15f);
        pillar.Scale = new Vector3(PillarR, PillarH, PillarR);
        pillarMat.SetShaderParameter("seed", seed);
        capMat.SetShaderParameter("seed", seed + 0.37f);
        pillar.Visible = cap.Visible = false;
        if (simBoom != null)
        {
            simBoom.GlobalPosition = p + Vector3.Up * SimLook;
            simBoom.Scale = Vector3.One * SimSize;
            simMat!.SetShaderParameter("life", SimFirst / Math.Max(1, simFrames - 1));
            simBoom.Visible = true;
        }
        float y = (float)HeightAt(p.X, p.Z);
        haze.GlobalPosition = new Vector3(p.X, y + 0.05f, p.Z);
        haze.Scale = new Vector3(ringMax + 2.5f, 1, ringMax + 2.5f);
        hazeMat.SetShaderParameter("center", p);
        hazeMat.SetShaderParameter("strength", 0f);
        haze.Visible = true;
        rimLight.GlobalPosition = p + Vector3.Up * 0.9f;
        rimLight.LightEnergy = 16 * (LessFlash ? 0.5f : 1);
        jetN = 8 + (int)(R() * 5);
        for (int i = 0; i < jetN; i++)
        {
            float a = (i + 0.2f + R() * 0.6f) / jetN * Mathf.Tau;
            jets[i] = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a)) * (0.8f + R() * 0.4f);
        }
    }

    /// <summary>The BOOM's shapes, c real seconds after the last word (they run through its hitstop: the world
    /// stops, the fire doesn't), s Flare seconds (the ring's clock).</summary>
    void BoomTick(float c, float s, float dt)
    {
        var p = boomAt;
        // The low light: three frames at its peak, catching the rims of the statues round the crater, then gone.
        rimLight.LightEnergy = c < 0.05f ? 10 * (LessFlash ? 0.5f : 1) : Mathf.MoveToward(rimLight.LightEnergy, 0, dt * 90);
        // The pillar: full height in 0.15 s, full fire to 0.45 s, burnt out by 1.1 s.
        if (simBoom != null)
        {
            float life = (SimFirst + c * simFps * SimRate) / Math.Max(1, simFrames - 1);
            simBoom.Scale = Vector3.One * SimSize;
            simBoom.Visible = life < 1;
            simMat!.SetShaderParameter("life", life);
            // The birth burns through the eye's dip (the world stops down, the fireball doesn't: solver 5 measured the
            // dip taking the birth's whitest pixel from 0.92 to 0.85 at f118); handed back to the dip by 0.3 s.
            float through = Mathf.Lerp(1, 1 / Math.Max(0.4f, dipNow), 1 - Mathf.SmoothStep(0.16f, 0.3f, c));
            simMat.SetShaderParameter("gain", 1.25f * through * (LessFlash ? 0.6f : 1));
            // (The soot thins as it climbs: opaque to the end it took the Return's floor to 0.57x at +0.8 s, f6i.)
            simMat.SetShaderParameter("smoke", 1.0f - 0.35f * Mathf.SmoothStep(0.35f, 0.8f, c));
            simMat.SetShaderParameter("fade", (1 - Mathf.SmoothStep(0.9f, 1.4f, c)) * (1 - Mathf.SmoothStep(0.85f, 1f, life)));
            pillar.Visible = cap.Visible = false;
        }
        float grow = 1 - Mathf.Pow(1 - Mathf.Clamp(c / 0.15f, 0, 1), 3);
        float burn = 1 - Mathf.SmoothStep(0.45f, 1.1f, c);
        pillar.Visible = c < 1.15f && !Simmed;
        pillarMat.SetShaderParameter("age", c);
        pillarMat.SetShaderParameter("grow", grow);
        pillarMat.SetShaderParameter("burn", burn);
        // The cap: forms as the fire reaches the top, mushrooms out and up, its underside lit while the fire burns,
        // thinning from 0.9 s (the head's smoke takes it on).
        float k = Mathf.SmoothStep(0.06f, 1.0f, c);
        float thin = Mathf.SmoothStep(0.6f, 1.5f, c);
        cap.Visible = c > 0.07f && c < 1.5f && !Simmed;
        cap.GlobalPosition = p + Vector3.Up * (PillarH * 0.92f + 1.6f * k);
        cap.Scale = new Vector3(1.3f + 2.3f * k, 0.8f + 0.8f * k, 1.3f + 2.3f * k) * Mathf.Min(1, (c - 0.06f) / 0.08f + 0.35f);
        capMat.SetShaderParameter("age", c);
        capMat.SetShaderParameter("burn", burn);
        capMat.SetShaderParameter("thin", thin);
        // The jets: flame thrown 3-5 m out along the ground from the root, for its first 0.15 s.
        if (c < 0.15f && !Simmed)
            for (int j = 0; j < jetN; j++)
                for (int i = 0, n = (int)(110 * dt + R()); i < n; i++)
                {
                    var d = jets[j];
                    var v = d * (15 + R() * 7) + Vector3.Up * (1.2f + R() * 1.6f) + Rand3() * 1.2f;
                    glow.Spawn(FlareBits.Kind.Fire, p + Vector3.Up * 0.25f + d * 0.4f, v, 0.32f + R() * 0.16f, 0.3f + R() * 0.12f,
                        new Color(1.1f, 0.48f, 0.12f), new Color(0.6f, 0.1f, 0.02f), sizeEnd: 0.85f + R() * 0.35f, drag: 4.2f, lift: 1.2f);
                }
        // The heat riding the ring's line for its first third of a second.
        float hs = Mathf.SmoothStep(0.0f, 0.03f, s) * (1 - Mathf.SmoothStep(0.22f, 0.34f, s));
        haze.Visible = hs > 0.005f || s < 0.03f;
        hazeMat.SetShaderParameter("radius", RingAt(s, ringMax));
        hazeMat.SetShaderParameter("strength", hs);
        hazeMat.SetShaderParameter("age", c);
    }

    /// <summary>How long a statue stands cracked, the fire showing through its glaze, after the ring's line reaches
    /// it and before it bursts (Flare seconds: one to three frames).</summary>
    // (Judge 3: the statues the line nears crack two or three frames before it reaches them, the blast ahead of
    // its fire; after it, they read as knocked down by the char.)
    double CrackHold() => -(2 + R()) / 60.0;

    void BoomClear()
    {
        if (pillar == null) return;
        pillar.Visible = cap.Visible = haze.Visible = false;
        if (simBoom != null) simBoom.Visible = false;
        rimLight.LightEnergy = 0;
    }
}

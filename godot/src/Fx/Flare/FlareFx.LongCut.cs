using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/* The Long Cut's own layers (docs/design/FLARE_LOOK.md, The Long Cut: "the seam of morning"; SKILL_VFX_STUDY §6.1).
 * Dawn-gold, never the Arcanist's ember orange or Burns Twice's frost.
 * - The press: a warm 4 m light at her (set behind her from the eye, so it rims her and the steel), a bloom pulse, gold
 *   motes off the blade; the hold's drain goes toward a warm dusk (flare_world: look.z < 0), never grey-cyan.
 * - The sweep (0.35 s, her 12 m reach): a warm wedge of light over the ground behind its leading angle and a wash over
 *   all it crossed fading for 0.5 s (flare_world flare_sweep_at: no rim line), a shadowed light riding it at knee
 *   height, a skirt of dust kicked up along it.
 * - The cleave: an exposure lift of 1.3x for 3 frames and a short shake; the seam, a 24 m crack drawn from the baked
 *   strip in the ground's own shader (flare_seam_ground: its paint, normal and depth), lit front to tip like a fuse in
 *   0.4 s, cooling gold to red to dark, the scar gone by 6 s; rock chunks thrown out along the fuse (chunks.glb, on
 *   gravity), dust jets (the lc_dust flipbook) staggered with the fuse; a chain of low warm lights so the shadows swing
 *   away from the line: one shadowed riding the fuse front, two unshadowed trailing it, the shadowed spend light at her
 *   for 0.5 s. At night the core is capped: the glow on the field is the lights', one white-gold line among the pack's
 *   orange ember-hearts.
 * - The struck: a rim for 3 frames as their moment comes (the sweep's as it passes them, the seam's as the fuse
 *   reaches them, later the farther they lie from the line), then charred and burnt away to gold embers from the side
 *   facing the line in 0.7 s (vat.gdshaderinc), then gone; a char scar where each stood for 4-5 s. Their ember drops
 *   wait until the seam has cooled (FlareFx.DropsShow). */
public partial class FlareFx
{
    const string LongCutId = "the_long_cut";
    bool IsLongCut => id == LongCutId;

    /// <summary>The seam's fuse: metres a second (24 m in 0.4 s).</summary>
    const float FuseSpeed = 60f;
    /// <summary>A body's burn-up (Flare time): charred, burnt away in gold.</summary>
    const float BurnLen = 0.7f;
    const float SweepLen = 0.35f;
    const int LcJets = 11, LcChunks = 12;

    double lcSweepT = -1, lcCleaveT = -1;
    float lcSweepFrom;
    Vector2 lcO, lcDir;
    float lcLen, lcHalf;
    int lcJetN, lcChunkN;
    double lcSmokeAcc, lcSkirtAcc;
    /// <summary>Real seconds since the press (the struck's flash and the pictures' spacing run on it, not the Flare's clock).</summary>
    double lcRt;
    ulong lcLastUs;
    double lcMsSum, lcMsMax, lcMsMaxClean;
    int lcMsN;
    bool lcMsSaid;
    /// <summary>Look-dev: the Long Cut's lights scaled (LC_LIGHT).</summary>
    static readonly float LcLight = float.TryParse(System.Environment.GetEnvironmentVariable("LC_LIGHT"), System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var lcl) ? lcl : 1f;

    /// <summary>The held blade (arm:watch_blade or any blade in her hand), for the steel's light: set by the scene.</summary>
    public Node3D? Blade;

    static readonly Color Dawn = new(1.3f, 0.95f, 0.5f), DawnEnd = new(0.9f, 0.45f, 0.12f);

    OmniLight3D? lcTrailA, lcTrailB, lcHerLight;
    Flipbooks? lcBooks;

    sealed class Chunk
    {
        public required MeshInstance3D Node;
        public required StandardMaterial3D Hot;
        public Vector3 P, V, Axis;
        public float Spin, Age, Life, Scale;
        public int Bounces;
    }
    readonly List<Chunk> lcChunkList = new();

    /// <summary>A point on the blade, 0 the grip .. 1 the tip (or above her right hand when none is held).</summary>
    Vector3 BladeAt(float k)
    {
        if (Blade is { } bl && IsInstanceValid(bl) && bl.IsInsideTree())
        {
            float tip = bl.HasMeta("tip") ? (float)bl.GetMeta("tip") : 1.4f;
            return bl.GlobalTransform * new Vector3(0, Mathf.Lerp(0.25f, tip, k), 0);
        }
        return Her + new Vector3(0.3f, 1.1f + 0.6f * k, 0);
    }

    bool HasBlade => Blade is { } bl && IsInstanceValid(bl) && bl.IsInsideTree();

    OmniLight3D LcLightNew(bool shadow)
    {
        var l = new OmniLight3D { LightEnergy = 0, OmniRange = 8, ShadowEnabled = shadow && LcShadows, Visible = false, OmniAttenuation = 1.4f };
        AddChild(l);
        return l;
    }

    // The warm-up: when the Long Cut first stands ready, its lights, dust flipbook and chunk meshes are drawn once, tiny
    // and in view, for 3 frames, so the press does not pay the first-use compiles (740-990 ms spikes in the shot).
    static bool lcWarmed;
    int lcWarmFrames;
    readonly List<Node> lcWarmNodes = new();

    void LcWarmStart()
    {
        lcWarmed = true;
        lcWarmFrames = 3;
        LcArtStart();
        lcTrailA ??= LcLightNew(false);
        lcTrailB ??= LcLightNew(false);
        lcHerLight ??= LcLightNew(true);
        if (lcBooks == null) { lcBooks = new Flipbooks(); AddChild(lcBooks); }
        var p = Her + Vector3.Up * 1.2f;
        foreach (var l in new[] { lcHerLight, spendLight })
        {
            l.GlobalPosition = p; l.OmniRange = 3; l.LightEnergy = 0.001f; l.ShadowEnabled = LcShadows; l.Visible = true;
        }
        var meshes = ChunkMeshes();
        var hot = new StandardMaterial3D
        {
            ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, Transparency = BaseMaterial3D.TransparencyEnum.Alpha, BlendMode = BaseMaterial3D.BlendModeEnum.Add,
            AlbedoColor = new Color(1f, 0.6f, 0.22f, 0.01f),
        };
        var node = new MeshInstance3D { Mesh = meshes[0], MaterialOverlay = hot, CastShadow = GeometryInstance3D.ShadowCastingSetting.On, Scale = Vector3.One * 0.01f };
        AddChild(node);
        node.GlobalPosition = p;
        lcWarmNodes.Add(node);
        lcWarmChunk = node;
        foreach (var n in new[] { "lc_dust", "smoke_puff" })
            lcBooks.Spawn(n, p, 0.02f, 0.1f, new Color(0, 0, 0, 0.01f), false, 0.02f, float.NaN, 0, Vector3.Zero);
    }
    MeshInstance3D? lcWarmChunk;

    void LcWarmStep()
    {
        if (lcWarmFrames <= 0) return;
        if (--lcWarmFrames > 0) return;
        foreach (var n in lcWarmNodes) if (IsInstanceValid(n)) n.QueueFree();
        lcWarmNodes.Clear();
        if (!Active)
        {
            foreach (var l in new[] { lcHerLight, spendLight }) if (l != null) { l.LightEnergy = 0; l.Visible = l == spendLight && SpendLightOld; }
        }
    }

    /// <summary>For BattleFx.Pickups: the Long Cut's ember drops drawn at 0.6 at night (they dominated the last beats).</summary>
    public float DropScale => Active && IsLongCut && Night ? 0.6f : 1f;

    void LongPress()
    {
        LcArtStart();
        lcTrailA ??= LcLightNew(false);
        lcTrailB ??= LcLightNew(false);
        lcHerLight ??= LcLightNew(true);
        if (lcBooks == null) { lcBooks = new Flipbooks(); AddChild(lcBooks); }
        // (made now, in the Hold, not at the sweep: the first dust and chunks held a frame ~1 s)
        ChunkMeshes();
        Dust(Her + Vector3.Down * 50, 0.01f, 0.01f, 0.05f, Vector3.Zero, 0);
        lcSweepT = lcCleaveT = -1;
        lcLen = 0;
        lcJetN = lcChunkN = 0;
        lcSmokeAcc = lcSkirtAcc = 0;
        lcRt = 0;
        lcBeat = 0; lcBeatRt = -1; lcBeatFrame = -1;
        lcLastUs = 0; lcMsSum = lcMsMax = lcMsMaxClean = 0; lcMsN = 0; lcMsSaid = false;
        // Frame 1: dawn-gold motes off the steel, drawn up it (a hue per calling: the Arcanist's are ember orange).
        for (int i = 0; i < 22; i++)
        {
            var p = BladeAt(0.3f + R() * 0.7f);
            glow.Spawn(FlareBits.Kind.Mote, p, Rand3() * (1.5f + R() * 2.5f), 0.3f + R() * 0.25f, 0.04f + R() * 0.04f, Dawn, DawnEnd, drag: 4);
        }
    }

    void LongSweep(Ev.Flare e)
    {
        lcSweepT = t;
        // The sweep comes round to the line's side; it starts a little past the aim so it ends on it.
        lcSweepFrom = (float)e.Angle + 0.4f;
        spendAt = t;
        Cam?.Jolt(Vector3.Up, 0.25f * Motion);
        Cue("boom", at, 0.6f);
        Rumble(0.6f, 0.4f, 0.08f);
        ResolveDooms();
    }

    void LongCleave(Ev.Flare e)
    {
        lcCleaveT = t;
        if (lcSweepT < 0) { lcSweepT = t - 0.3; spendAt = t; }
        lcO = new Vector2((float)e.X, (float)e.Z);
        lcDir = new Vector2((float)(e.TX - e.X), (float)(e.TZ - e.Z));
        lcLen = lcDir.Length();
        lcDir = lcLen > 1e-3f ? lcDir / lcLen : Vector2.Right;
        lcHalf = (float)e.Radius;
        lastAt = t;
        lcCleaveRt = lcRt;
        Cam?.Jolt(new Vector3(lcDir.X, 0, lcDir.Y) * 0.4f + Vector3.Up, 0.7f * Motion);
        Cam?.AddTrauma(0.32f * Motion);
        Cue("boom", at, 1);
        Rumble(1, 0.6f, 0.14f);
        ResolveDooms();
    }

    double lcCleaveRt = -1;

    /// <summary>When the fuse reaches this far along the seam (Flare time).</summary>
    double FuseAt(float along) => lcCleaveT + Math.Max(0, along) / FuseSpeed;

    /// <summary>How far across the seam's line a point lies (m; 0 when there is no seam).</summary>
    float SeamAcross(Vector3 w) => lcLen <= 0 ? 0 : (new Vector2(w.X, w.Z) - lcO).Dot(new Vector2(-lcDir.Y, lcDir.X));

    /// <summary>The kills the blow just made (their Ev.Kill comes before the blow's own event) get their moment: the
    /// sweep's as its light comes round to them, the cleave's as the fuse reaches them, later the farther from the line.</summary>
    void ResolveDooms()
    {
        foreach (var d in doomed.Values)
        {
            if (!d.Pending) continue;
            d.Pending = false;
            if (lcCleaveT >= 0 && lcLen > 0)
            {
                var rel = new Vector2(d.Where.X, d.Where.Z) - lcO;
                float along = Mathf.Clamp(rel.Dot(lcDir), 0, lcLen);
                d.At = FuseAt(along) + 0.02 + 0.012 * Math.Abs(SeamAcross(d.Where));
                // (night: the luminance cap, the burn-up spread over 0.4 s by the body's distance from the line, the near first)
                if (Night) d.At += 0.4 * Mathf.Clamp(Math.Abs(SeamAcross(d.Where)) / Math.Max(1f, lcHalf), 0, 1);
            }
            else
            {
                float a = Mathf.Atan2(d.Where.Z - at.Z, d.Where.X - at.X);
                float behind = Mathf.PosMod(a - lcSweepFrom, Mathf.Tau);
                d.At = t + SweepEase(behind / Mathf.Tau) * SweepLen + 0.02;
                if (Night) d.At += 0.4 * Mathf.Clamp(new Vector2(d.Where.X - at.X, d.Where.Z - at.Z).Length() / Math.Max(1f, reach), 0, 1);
            }
        }
    }

    /// <summary>The share of the sweep's time it takes to reach this share of its turn (the inverse of its ease).</summary>
    static float SweepEase(float turn) => 1 - Mathf.Sqrt(1 - Mathf.Clamp(turn, 0, 1));

    /// <summary>Where the seam's crack runs at this far along it (the strip's own centre line).</summary>
    Vector3 SeamPoint(float along)
    {
        float c = CrackOff(along);
        var side = new Vector2(-lcDir.Y, lcDir.X);
        var w = lcO + lcDir * along + side * c;
        return new Vector3(w.X, (float)HeightAt(w.X, w.Y), w.Y);
    }

    static float H1(float x) { float s = Mathf.Sin(x * 127.1f + 311.7f) * 43758.5453f; return s - Mathf.Floor(s); }

    /// <summary>The stand-in crack's offset across the line (m): a jag every 0.55 m over a slow wander.</summary>
    static float SeamOffset(float along)
    {
        float s = along / 0.55f, i = Mathf.Floor(s), f = s - i;
        float jag = Mathf.Lerp(H1(i), H1(i + 1), f) - 0.5f;
        float s2 = along / 3.1f, i2 = Mathf.Floor(s2), f2 = s2 - i2;
        float s3 = along / 0.19f, i3 = Mathf.Floor(s3), jag2 = Mathf.Lerp(H1(i3 + 90), H1(i3 + 91), s3 - i3) - 0.5f;
        float wan = Mathf.Lerp(H1(i2 + 50), H1(i2 + 51), f2) - 0.5f;
        return (jag * 0.34f + jag2 * 0.1f + wan * 0.7f) * Mathf.Clamp(along / 2f, 0, 1);
    }

    /// <summary>Where the eye is (for setting the press light behind her).</summary>
    Vector3 EyeAt() => GetViewport()?.GetCamera3D() is { } c ? c.GlobalPosition : Her + new Vector3(0, 20, 14);

    /// <summary>Each frame of the Long Cut: the drain, the press, the sweep, the seam and its lights, chunks and dust,
    /// the smoke of the Return, the struck, the pictures.</summary>
    void LongTick(float dt)
    {
        lcRt += dt;
        LcArtPoll();
        // The drain over the Draw and Hold, warm (look.z < 0); repainted from her outward after the cleave, slower.
        double from = lcCleaveT >= 0 ? lcCleaveT : -1;
        look.X = from < 0 ? Mathf.Min(1, (float)t / 0.12f) * 0.85f : Mathf.Max(0, 1 - (float)(t - from) / 1.2f) * 0.85f;
        look.Y = from < 0 ? 0 : (float)(t - from) * (reach + 14) / 0.9f;
        look.Z = -1;
        web.X = 0;
        web.Y = 0;

        // The exposure: a bloom pulse at the press (4 frames), the cleave's warm lift 1.3x (3 frames, in its hitstop).
        float lift = 1;
        if (lcRt < 4 / 60.0) lift = 1.12f;
        if (lcCleaveRt >= 0 && lcRt - lcCleaveRt < 3.2 / 60.0) lift = 1.3f;
        SetDip(1 + (lift - 1) * (LessFlash ? 0.5f : 1));

        // The press: a warm 4 m light at her, behind her from the eye (her rim and the steel's), the brightest in the Hold.
        bool held = lcSweepT < 0;
        float steel = held ? 0.75f + 0.6f * Mathf.Exp(-(float)t * 9) : Mathf.Max(0, 1 - (float)(t - lcSweepT) / 0.5f) * 0.75f;
        var back = Her - EyeAt();
        back.Y = 0;
        back = back.LengthSquared() > 1e-4f ? back.Normalized() : Vector3.Forward;
        headLight.LightColor = new Color(1f, 0.8f, 0.5f);
        headLight.OmniRange = 4.0f;
        headLight.GlobalPosition = Her + back * 0.9f + Vector3.Up * 1.5f;
        headLight.LightEnergy = 2.4f * steel * (LessFlash ? 0.6f : 1) * LcLight;
        if (held && R() < dt * 40)
        {
            // Light drawn up the edge, grip to tip.
            var p = BladeAt(R() * 0.5f);
            glow.Spawn(new FlareBits.P { Kind = FlareBits.Kind.Mote, At = p, V = (BladeAt(1) - BladeAt(0)).Normalized() * (1.5f + R()), Life = 0.3f, Size = 0.035f, SizeEnd = 0.02f, Color = new Color(1.4f, 1.1f, 0.7f), ColorEnd = Dawn });
        }

        // The steel's own hot core while it cuts: a thin line along the real blade, as it moves.
        bool cutting = lcSweepT >= 0 && t < lcSweepT + SweepLen + 0.04 || lcCleaveT >= 0 && t < lcCleaveT + 0.08;
        if (cutting)
        {
            int n = HasBlade ? 7 : 4;
            for (int i = 0; i < n; i++)
            {
                float k = 0.35f + 0.65f * (i + R()) / n;
                Vector3 p;
                if (HasBlade) p = BladeAt(k);
                else
                {
                    float a = SweepLead();
                    p = Her + new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a)) * (0.5f + 1.2f * k) + Vector3.Up * 1.0f;
                }
                glow.Spawn(new FlareBits.P { Kind = FlareBits.Kind.Mote, At = p, V = Vector3.Zero, Life = 0.09f, Size = 0.03f + 0.02f * k, Color = new Color(1.5f, 1.25f, 0.85f), ColorEnd = new Color(1.1f, 0.6f, 0.2f) });
            }
        }

        // The sweep: its wedge (0..1) and its wash after it (0..1).
        float sweepK = 0, wash = 0;
        if (lcSweepT >= 0)
        {
            float s = (float)(t - lcSweepT);
            sweepK = Mathf.SmoothStep(0, 0.03f, s) * (1 - Mathf.SmoothStep(SweepLen - 0.03f, SweepLen + 0.08f, s));
            wash = Mathf.SmoothStep(0, 0.12f, s) * (1 - Mathf.SmoothStep(SweepLen, SweepLen + 0.5f, s));
            if (lcCleaveT < 0)
            {
                // Its light rides it at knee height a few metres out: the shadows swing round her.
                float a = SweepLead();
                spendLight.GlobalPosition = new Vector3(at.X + Mathf.Cos(a) * 3.5f, (float)HeightAt(at.X, at.Z) + 0.7f, at.Z + Mathf.Sin(a) * 3.5f);
                spendLight.LightColor = new Color(1f, 0.74f, 0.4f);
                spendLight.OmniRange = 10;
                spendLight.ShadowEnabled = LcShadows;
                spendLight.LightEnergy = (Night ? 0.65f : 1.6f) * Mathf.Max(sweepK, wash * 0.4f) * (LessFlash ? 0.6f : 1) * LcLight;
                spendLight.Visible = spendLight.LightEnergy > 0.01f;
            }
            // The skirt: dust kicked up along its leading angle, low.
            if (sweepK > 0.2f)
            {
                lcSkirtAcc += dt * 70;
                while (lcSkirtAcc >= 1)
                {
                    lcSkirtAcc -= 1;
                    float a = SweepLead() - R() * 0.25f, r = 2.5f + R() * (reach - 3);
                    var p = new Vector3(at.X + Mathf.Cos(a) * r, 0, at.Z + Mathf.Sin(a) * r);
                    p.Y = (float)HeightAt(p.X, p.Z);
                    Dust(p + Vector3.Up * 0.3f, 0.7f + R() * 0.5f, 1.8f + R() * 0.8f, 0.9f + R() * 0.4f, new Vector3(-Mathf.Sin(a), 0.35f, Mathf.Cos(a)) * 1.2f, 0.7f);
                }
            }
        }
        if (lcSweepT < 0) { spendLight.LightEnergy = 0; spendLight.Visible = SpendLightOld; }
        RenderingServer.GlobalShaderParameterSet("flare_sweep", new Vector4(SweepLead(), sweepK, reach, lcSweepFrom));
        // (night: the core's emission capped, so the line wins by its shape and value and the lights carry the glow)
        RenderingServer.GlobalShaderParameterSet("flare_lc", new Vector4(1, wash, 1.6f, Night ? 1 : 0));

        if (lcCleaveT >= 0 && lcLen > 0) SeamTick(dt);
        else
        {
            RenderingServer.GlobalShaderParameterSet("flare_seam", Vector4.Zero);
            if (lcHerLight != null) lcHerLight.Visible = false;
        }
        ChunksStep(dt);
        lcBooks?.Step(dt);

        // (for the pictures' log: wall-clock frame time from the press to the seam's cooling, in the packed crowd)
        if (Args.Has("shot"))
        {
            ulong now = Time.GetTicksUsec();
            if (lcLastUs > 0)
            {
                double ms = (now - lcLastUs) / 1000.0;
                lcMsSum += ms; lcMsN++; lcMsMax = Math.Max(lcMsMax, ms);
                bool shotFrame = (long)Engine.GetFramesDrawn() - lcBeatFrame <= 2;
                if (!shotFrame) lcMsMaxClean = Math.Max(lcMsMaxClean, ms);
                if (ms > 120) GD.Print($"longcut slow frame {ms:0} ms at flare t {t:0.000} {(shotFrame ? "(picture saved) " : "")}(cleave {(lcCleaveT < 0 ? -1 : t - lcCleaveT):0.000}, struck {doomed.Count}, jets {lcJetN}, chunks {lcChunkN})");
            }
            lcLastUs = now;
            if (!lcMsSaid && lcCleaveT >= 0 && t > lcCleaveT + 1.5)
            {
                lcMsSaid = true;
                GD.Print($"longcut frame time press..cleave+1.5s: mean {lcMsSum / Math.Max(1, lcMsN):0.0} ms, max {lcMsMax:0.0} ms (max off the picture frames {lcMsMaxClean:0.0} ms) over {lcMsN} frames; bits {glow.Count}+{bed.Count}, struck {doomed.Count}");
            }
            LongBeats();
        }
        // The struck burn up as their moment comes, gold embers off them as they go.
        foreach (var d in doomed.Values)
        {
            if (d.Pending || t < d.At) continue;
            if (!d.Done) { d.Done = true; d.Rt = lcRt; BurnUp(d); }
            float k = (float)(t - d.At);
            if (k < BurnLen && R() < dt * 16)
                glow.Spawn(new FlareBits.P
                {
                    Kind = FlareBits.Kind.Mote, At = d.Where + new Vector3((R() - 0.5f) * 0.5f, 0.2f + R() * 1.4f * (1 - k / BurnLen), (R() - 0.5f) * 0.5f),
                    V = new Vector3((R() - 0.5f) * 0.6f, 0.9f + R() * 1.5f, (R() - 0.5f) * 0.6f), Life = 0.6f + R() * 0.6f, Size = 0.035f + R() * 0.03f, SizeEnd = 0.012f,
                    Color = new Color(1.3f, 0.95f, 0.5f), ColorEnd = new Color(0.9f, 0.4f, 0.08f), Drag = 1.5f, Lift = 0.7f,
                });
        }
        // (a kill whose blow event never came: its moment now)
        foreach (var d in doomed.Values)
            if (d.Pending && t > d.Born + 0.4) { d.Pending = false; d.At = t; }
    }

    /// <summary>The seam: its uniforms, its lights, its chunks and dust jets in sequence, the smoke of the Return.</summary>
    void SeamTick(float dt)
    {
        float s = (float)(t - lcCleaveT);
        float run = lcLen / FuseSpeed;
        float front = Mathf.Min(lcLen, s * FuseSpeed);
        float fade = 1 - Mathf.SmoothStep(4.4f, 6.0f, s);
        RenderingServer.GlobalShaderParameterSet("flare_seam", new Vector4(lcO.X, lcO.Y, Mathf.Atan2(lcDir.Y, lcDir.X), lcLen));
        RenderingServer.GlobalShaderParameterSet("flare_seam_t", new Vector4(s, FuseSpeed, fade, Night ? 1 : 0));
        float flash = LessFlash ? 0.6f : 1;
        // The seam's heat at the line's middle (its lights cool with it): gold, red by ~1.8 s, dark by ~2.8 s.
        float heat = 1 - Mathf.SmoothStep(0.5f, 2.8f, s - run * 0.5f);
        var warm = new Color(1f, 0.72f, 0.38f);
        var red = new Color(1f, 0.32f, 0.08f);
        var cool = warm.Lerp(red, Mathf.SmoothStep(0.5f, 1.8f, s - run * 0.5f));

        // One shadowed light rides the fuse's front, low over the crack (that is what swings the shadows away from it).
        var fp = SeamPoint(front);
        if (s <= run + 0.05f)
        {
            spendLightT = -1;
            spendLight.Visible = true;
            spendLight.ShadowEnabled = LcShadows;
            spendLight.GlobalPosition = fp + Vector3.Up * 0.6f;
            spendLight.LightColor = new Color(1f, 0.78f, 0.45f);
            spendLight.OmniRange = 9;
            spendLight.LightEnergy = (Night ? 3.0f : 3.6f) * flash * LcLight;
        }
        else
        {
            float k = 1 - Mathf.SmoothStep(0.05f, 0.7f, s - run);
            spendLight.GlobalPosition = SeamPoint(lcLen * 0.88f) + Vector3.Up * 0.6f;
            spendLight.LightColor = cool;
            spendLight.LightEnergy = (Night ? 1.8f : 2.2f) * k * flash * LcLight;
            spendLight.Visible = k > 0.01f;
        }
        // Two unshadowed trailing it, then settled at the line's thirds, cooling with it.
        float settle = Mathf.SmoothStep(0, 0.4f, s - run);
        float trailE = (Night ? 2.0f : 1.8f) * Mathf.SmoothStep(0, 0.05f, s) * heat * fade * flash * LcLight;
        if (lcTrailA != null && lcTrailB != null)
        {
            var pa = SeamPoint(Mathf.Lerp(Mathf.Max(0.6f, front - 6), lcLen * 0.6f, settle));
            var pb = SeamPoint(Mathf.Lerp(Mathf.Max(0.6f, front - 13), lcLen * 0.25f, settle));
            foreach (var (l, p) in new[] { (lcTrailA, pa), (lcTrailB, pb) })
            {
                l.GlobalPosition = p + Vector3.Up * 0.55f;
                l.OmniRange = 7.5f;
                l.LightColor = cool;
                l.LightEnergy = trailE;
                l.Visible = trailE > 0.01f;
            }
        }
        // The spend light at her: shadowed, 0.5 s, the steel's bite at her feet.
        if (lcHerLight != null)
        {
            float k = Mathf.SmoothStep(0, 0.02f, s) * (1 - Mathf.SmoothStep(0.3f, 0.55f, s));
            lcHerLight.GlobalPosition = SeamPoint(0.9f) + Vector3.Up * 0.8f;
            lcHerLight.OmniRange = 7;
            lcHerLight.LightColor = new Color(1f, 0.8f, 0.5f);
            lcHerLight.LightEnergy = (Night ? 2.4f : 2.6f) * k * flash * LcLight;
            lcHerLight.Visible = k > 0.01f;
        }

        // Dust jets up in sequence behind the front, chunks thrown out.
        while (lcJetN < LcJets && front >= (lcJetN + 0.55f) / LcJets * lcLen)
        {
            float a = (lcJetN + 0.55f) / LcJets * lcLen + (R() - 0.5f) * 0.8f;
            lcJetN++;
            Jet(a);
        }
        while (lcChunkN < LcChunks && front >= (lcChunkN + 0.4f) / LcChunks * lcLen * 0.92f)
        {
            float a = (lcChunkN + 0.4f) / LcChunks * lcLen * 0.92f;
            lcChunkN++;
            ThrowChunk(a);
        }

        // The Return: a thin curtain of smoke off the cooling seam.
        if (s > 0.6f && s < 3.2f)
        {
            lcSmokeAcc += dt * 18 * (1 - Mathf.SmoothStep(2.2f, 3.2f, s));
            while (lcSmokeAcc >= 1)
            {
                lcSmokeAcc -= 1;
                float a = 0.8f + R() * (lcLen - 0.8f);
                var p = SeamPoint(a);
                bed.Spawn(new FlareBits.P
                {
                    Kind = FlareBits.Kind.Smoke, At = p + new Vector3((R() - 0.5f) * 0.5f, 0.25f + R() * 0.3f, (R() - 0.5f) * 0.5f),
                    V = new Vector3((R() - 0.5f) * 0.3f, 0.7f + R() * 0.6f, (R() - 0.5f) * 0.3f), Life = 1.9f + R() * 0.8f, Size = 0.5f + R() * 0.25f, SizeEnd = 1.6f + R() * 0.6f,
                    Color = Night ? new Color(0.07f, 0.06f, 0.055f, 0.3f) : new Color(0.2f, 0.18f, 0.16f, 0.28f), ColorEnd = Night ? new Color(0.09f, 0.085f, 0.08f, 0.06f) : new Color(0.26f, 0.24f, 0.22f, 0.05f),
                    Drag = 0.8f, Lift = 0.25f, Swirl = 0.5f, Seed = R(), Wind = new Vector3(0.25f, 0, 0.1f),
                });
            }
        }
    }

    /// <summary>The sweep's leading angle now (radians, unwrapped).</summary>
    float SweepLead()
    {
        if (lcSweepT < 0) return lcSweepFrom;
        float k = Mathf.Clamp((float)(t - lcSweepT) / SweepLen, 0, 1);
        k = 1 - (1 - k) * (1 - k);
        return lcSweepFrom + Mathf.Tau * k;
    }

    /// <summary>A puff of the dust flipbook (lc_dust; smoke_puff standing in; the procedural puff if neither is there).</summary>
    void Dust(Vector3 p, float size, float sizeEnd, float life, Vector3 v, float tone)
    {
        var tint = Night ? new Color(0.3f, 0.26f, 0.22f) * tone : new Color(0.78f, 0.7f, 0.58f) * tone;
        if (lcBooks != null && (lcBooks.Spawn("lc_dust", p, size, life, tint, false, sizeEnd, float.NaN, (R() - 0.5f) * 0.6f, v)
            || lcBooks.Spawn("smoke_puff", p, size, life, tint, false, sizeEnd, float.NaN, (R() - 0.5f) * 0.6f, v))) return;
        bed.Spawn(new FlareBits.P
        {
            Kind = FlareBits.Kind.Puff, At = p, V = v, Life = life, Size = size * 0.4f, SizeEnd = sizeEnd * 0.4f,
            Color = new Color(tint.R * 0.4f, tint.G * 0.4f, tint.B * 0.4f, 0.45f), ColorEnd = new Color(tint.R * 0.4f, tint.G * 0.4f, tint.B * 0.4f, 0), Drag = 2.5f, Lift = 0.2f, Seed = R(),
        });
    }

    /// <summary>A jet off the seam at this far along it: dust shot up and turning to smoke.</summary>
    void Jet(float along)
    {
        var p = SeamPoint(along);
        float taper = Mathf.Lerp(1f, 0.6f, along / Math.Max(1, lcLen));
        float size = (1.6f + R() * 0.6f) * taper;
        Dust(p + Vector3.Up * size * 0.45f, size, size * 2.3f, 1.8f + R() * 0.4f, Vector3.Up * (1.4f + R() * 0.8f) * taper, 1);
    }

    /// <summary>A chunk of the ground thrown up and out to one side of the crack, tumbling, hot underneath at first.</summary>
    void ThrowChunk(float along)
    {
        var meshes = ChunkMeshes();
        var p = SeamPoint(along);
        var side = new Vector3(-lcDir.Y, 0, lcDir.X);
        var fwd = new Vector3(lcDir.X, 0, lcDir.Y);
        float sd = R() < 0.5f ? -1 : 1;
        var hot = new StandardMaterial3D
        {
            ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, Transparency = BaseMaterial3D.TransparencyEnum.Alpha, BlendMode = BaseMaterial3D.BlendModeEnum.Add,
            AlbedoColor = new Color(1f, 0.6f, 0.22f, 0.5f),
        };
        var node = new MeshInstance3D { Mesh = meshes[lcChunkN % meshes.Length], MaterialOverlay = hot, CastShadow = GeometryInstance3D.ShadowCastingSetting.On };
        AddChild(node);
        float taper = Mathf.Lerp(1f, 0.7f, along / Math.Max(1, lcLen));
        lcChunkList.Add(new Chunk
        {
            Node = node, Hot = hot, P = p + Vector3.Up * 0.1f,
            V = side * sd * (1.2f + R() * 2.4f) + fwd * (R() - 0.3f) * 1.2f + Vector3.Up * (3.5f + R() * 3.5f) * taper,
            Axis = Rand3(), Spin = 6 + R() * 10, Life = 2.6f + R() * 1.2f, Scale = (0.8f + R() * 0.5f) * taper,
        });
    }

    void ChunksStep(float dt)
    {
        for (int i = lcChunkList.Count - 1; i >= 0; i--)
        {
            var c = lcChunkList[i];
            c.Age += dt;
            if (c.Age >= c.Life || !IsInstanceValid(c.Node)) { if (IsInstanceValid(c.Node)) c.Node.QueueFree(); lcChunkList.RemoveAt(i); continue; }
            float g = (float)HeightAt(c.P.X, c.P.Z);
            if (c.Bounces < 3)
            {
                c.V.Y -= 16 * dt;
                c.P += c.V * dt;
                if (c.P.Y < g + 0.05f && c.V.Y < 0)
                {
                    c.P.Y = g + 0.05f;
                    c.Bounces++;
                    c.V = new Vector3(c.V.X * 0.45f, -c.V.Y * 0.3f, c.V.Z * 0.45f);
                    c.Spin *= 0.4f;
                    if (c.V.Y < 0.6f) c.Bounces = 3;
                }
            }
            var basis = c.Node.Basis.Orthonormalized();
            if (c.Spin > 0.01f && c.Bounces < 3) basis = new Godot.Basis(c.Axis, c.Spin * dt) * basis;
            // (gone by sinking into the ground in its last half second)
            float sink = Mathf.SmoothStep(c.Life - 0.5f, c.Life, c.Age);
            c.Node.Transform = new Transform3D(basis.Scaled(Vector3.One * c.Scale), c.P - Vector3.Up * sink * 0.3f);
            c.Hot.AlbedoColor = new Color(1f, 0.6f, 0.22f, 0.5f * (1 - Mathf.SmoothStep(0, 0.6f, c.Age)));
        }
    }

    /// <summary>A struck body's burn-up begins: a breath of dark smoke and a char scar where it stood.</summary>
    void BurnUp(Doom d)
    {
        var w = d.Where;
        bed.Spawn(new FlareBits.P
        {
            Kind = FlareBits.Kind.Smoke, At = w + Vector3.Up * 0.9f, V = Vector3.Up * 0.9f, Life = 1.4f + R() * 0.5f, Size = 0.45f, SizeEnd = 1.2f,
            Color = new Color(0.06f, 0.05f, 0.045f, 0.3f), ColorEnd = new Color(0.08f, 0.075f, 0.07f, 0.0f), Drag = 1f, Lift = 0.3f, Swirl = 0.4f, Seed = R(),
        });
        scars.Spawn(new FlareBits.P { Kind = FlareBits.Kind.Scar, At = w + Vector3.Up * 0.04f, Life = 4.2f + R(), Size = 0.6f + R() * 0.3f, Color = new Color(0.025f, 0.02f, 0.016f, 0.55f) });
    }

    /// <summary>For CrowdView: how a held body is drawn (x frozen, y char, z dissolve, w burning). Burns Twice's are ice
    /// statues; the Long Cut's stand in their last pose until their moment, then char and burn away in gold.</summary>
    public Vector4 StatueLook(int enemy)
    {
        if (!IsLongCut) return new Vector4(1, 0, 0, 0);
        if (!doomed.TryGetValue(enemy, out var d)) return Vector4.Zero;
        if (d.Pending || t < d.At) return Vector4.Zero;
        return BurnLook((float)(t - d.At));
    }

    /// <summary>For CrowdView: seconds since the Long Cut's sweep or fuse reached a body lying at (x, z), or -1. The dead
    /// already down in its reach burn up with the struck (a dark star of her earlier kills lay round her after the
    /// clear: vfx9 fix2); CrowdView asks it only of corpses that were down before their moment.</summary>
    public double CorpseBurnAge(double x, double z)
    {
        if (!Active || !IsLongCut) return -1;
        double when = double.MaxValue;
        var rel = new Vector2((float)x - at.X, (float)z - at.Z);
        if (lcSweepT >= 0 && rel.Length() <= reach)
        {
            float behind = Mathf.PosMod(Mathf.Atan2(rel.Y, rel.X) - lcSweepFrom, Mathf.Tau);
            when = lcSweepT + SweepEase(behind / Mathf.Tau) * SweepLen + 0.02;
            if (Night) when += 0.4 * Mathf.Clamp(rel.Length() / Math.Max(1f, reach), 0, 1);
        }
        if (lcCleaveT >= 0 && lcLen > 0)
        {
            var w = new Vector3((float)x, 0, (float)z);
            float along = (new Vector2(w.X, w.Z) - lcO).Dot(lcDir), across = Math.Abs(SeamAcross(w));
            if (along >= -1 && along <= lcLen + 1 && across <= lcHalf)
            {
                double s = FuseAt(Mathf.Clamp(along, 0, lcLen)) + 0.02 + 0.012 * across;
                if (Night) s += 0.4 * Mathf.Clamp(across / Math.Max(1f, lcHalf), 0, 1);
                when = Math.Min(when, s);
            }
        }
        return when == double.MaxValue || t < when ? -1 : t - when;
    }

    /// <summary>For CrowdView: a corpse's burn-up look (y char, z dissolve, w burning) this long after its moment, as the struck's.</summary>
    public static Vector4 BurnLook(float k) => new(0, 0.9f * Mathf.SmoothStep(0.02f, 0.2f, k), Mathf.SmoothStep(0.08f, BurnLen, k), 0.7f * Mathf.SmoothStep(0, 0.05f, k) * (1 - Mathf.SmoothStep(0.35f, 0.65f, k)));

    /// <summary>The burn-up's length (Flare time).</summary>
    public static float BurnTime => BurnLen;

    /// <summary>For CrowdView: a held body's struck flash, its rim for 3 frames (real time) as its moment comes.</summary>
    public float StatueFlash(int enemy)
    {
        if (!IsLongCut || !doomed.TryGetValue(enemy, out var d) || !d.Done) return 0;
        return lcRt - d.Rt < 3.2 / 60.0 ? 0.5f : 0;
    }

    /* The pictures (--shot): each beat on the Flare's clock, at least 0.13 s of real time and a drawn frame apart. */
    int lcBeat;
    double lcBeatRt;
    long lcBeatFrame;

    void LongBeats()
    {
        (string Tag, double At)[] beats =
        {
            ("b1_press", 0.035), ("b2_hold", freezeLen - 0.1),
            ("b3_sweep", lcSweepT < 0 ? double.MaxValue : lcSweepT + 0.15),
            ("b4_fuse", lcCleaveT < 0 ? double.MaxValue : lcCleaveT + 0.2), ("b5_seam", lcCleaveT < 0 ? double.MaxValue : lcCleaveT + 0.45),
            ("b6_cool", lcCleaveT < 0 ? double.MaxValue : lcCleaveT + 1.4), ("b7_smoke", lcCleaveT < 0 ? double.MaxValue : lcCleaveT + 2.4),
            ("b8_scar", lcCleaveT < 0 ? double.MaxValue : lcCleaveT + 4.0), ("b9_dead", lcCleaveT < 0 ? double.MaxValue : lcCleaveT + 5.6),
        };
        if (lcBeat >= beats.Length || t < beats[lcBeat].At) return;
        if (lcBeatRt >= 0 && lcRt - lcBeatRt < 0.13) return;
        long frame = (long)Engine.GetFramesDrawn();
        if (frame <= lcBeatFrame) return;
        GD.Print($"longcut beat {beats[lcBeat].Tag}: flare t {t:0.000} (due {beats[lcBeat].At:0.000}), press +{lcRt:0.00} s real");
        Shots.Want(beats[lcBeat].Tag, 0);
        lcBeat++;
        lcBeatRt = lcRt;
        lcBeatFrame = frame;
    }

    void LongClear()
    {
        lcSweepT = lcCleaveT = -1;
        lcCleaveRt = -1;
        lcLen = 0;
        RenderingServer.GlobalShaderParameterSet("flare_seam", Vector4.Zero);
        RenderingServer.GlobalShaderParameterSet("flare_sweep", Vector4.Zero);
        RenderingServer.GlobalShaderParameterSet("flare_lc", Vector4.Zero);
        if (headLight != null) headLight.LightColor = new Color(1f, 0.55f, 0.2f);
        if (spendLight != null) spendLight.ShadowEnabled = true;
        foreach (var l in new[] { lcTrailA, lcTrailB, lcHerLight }) if (l != null) { l.LightEnergy = 0; l.Visible = false; }
        foreach (var c in lcChunkList) if (IsInstanceValid(c.Node)) c.Node.QueueFree();
        lcChunkList.Clear();
    }
}

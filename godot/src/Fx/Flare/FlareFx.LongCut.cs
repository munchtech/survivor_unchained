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
 * - The struck: a warm rim for 3 frames (the sweep's as it passes them, the seam's own as the fuse reaches them), then
 *   standing and shaded as ever (the faces the seam lights) until the fuse reaches their point on the line; their char
 *   starts then, 0.05 s later a metre farther from the line: the paint at a quarter, lit, with dawn-gold cracks, burnt
 *   away from the side facing the line along a thin gold edge with ash rising, gone 0.5 s after it starts
 *   (vat.gdshaderinc); never knocked down, so no ring of bodies; a char scar where each stood for 4-5 s. Their ember drops
 *   wait until the seam has cooled (FlareFx.DropsShow). */
public partial class FlareFx
{
    const string LongCutId = "the_long_cut";
    bool IsLongCut => id == LongCutId;

    /// <summary>The seam's fuse: metres a second (24 m in 0.4 s).</summary>
    const float FuseSpeed = 60f;
    /// <summary>A body's burn-up (Flare time): charred, burnt away in gold.</summary>
    const float BurnLen = 0.5f;
    const float SweepLen = 0.35f;
    const int LcChunks = 12;
    /// <summary>The jets' places along the line (m), drawn at the cleave: 0.8-2 m apart, irregular (r3c).</summary>
    readonly List<float> lcJetAt = new();

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
        LcLightsMake();
        foreach (var l in new[] { lcHandLight!, lcSweepL[0]! }) { l.GlobalPosition = p; l.LightEnergy = 0.001f; l.Visible = true; }
        lcBladeMat!.SetShaderParameter("col", new Color(0, 0, 0, 0));
        lcColumnMat!.SetShaderParameter("col", new Color(0, 0, 0, 0));
        LcStripDraw(lcBladeMesh!, lcBladeMat, p, p + Vector3.Up * 0.01f, 0.005f);
        LcStripDraw(lcColumnMesh!, lcColumnMat, p, p + Vector3.Up * 0.01f, 0.005f);
        lcBladeFx!.Visible = lcColumnFx!.Visible = true;
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
            LcLightClear();
        }
    }

    /// <summary>For BattleFx.Pickups: the Long Cut's ember drops drawn at 0.6 at night (they dominated the last beats).</summary>
    public float DropScale => Active && IsLongCut && Night ? 0.6f : 1f;

    /// <summary>For BattleFx.Pickups, in the Long Cut's aftermath only (r3c: ~200 soft peach halos made a hoop of bright
    /// blobs at night): an ember drop's halo this many metres across (0.28 m: about 8 px of glow radius at the play
    /// camera's ~83 px/m), its light at 0.25x, both coming in over the drop's first second. (0, 1) otherwise.</summary>
    public (float Across, float Light) DropHalo(double age)
    {
        if (!(Active && IsLongCut)) return (0, 1);
        float k = Mathf.SmoothStep(0, 1, (float)age);
        return (0.28f * (0.5f + 0.5f * k), 0.25f * k);
    }

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
        lcJetAt.Clear();
        lcSmokeAcc = lcSkirtAcc = 0;
        lcRt = 0;
        lcBeat = 0; lcBeatRt = -1; lcBeatFrame = -1;
        lcLastUs = 0; lcMsSum = lcMsMax = lcMsMaxClean = 0; lcMsN = 0; lcMsSaid = false;
        lcAshN = lcSootN = lcLogN = lcBehindN = 0; lcBehindStart = double.MaxValue; lcLogSaid = false;
        for (int c = 0; c < 2; c++) { lcClsN[c] = 0; lcClsStart[c] = double.MaxValue; lcClsLast[c] = lcClsGone[c] = double.MinValue; lcClsOff[c] = 0; }
        LcLightClear();
        LcLightsMake();
        // Frame 1: gold motes off the steel, drawn up it (a hue per calling: the Arcanist's are ember orange); with the
        // ones drawn up the edge through the hold, 20 at most (vfx9 r2: 30-odd white specks read as confetti at night).
        for (int i = 0; i < 12; i++)
        {
            var p = BladeAt(0.3f + R() * 0.7f);
            glow.Spawn(FlareBits.Kind.Mote, p, Rand3() * (1.2f + R() * 1.8f), 0.3f + R() * 0.25f, 0.035f + R() * 0.03f, new Color(1.1f, 0.66f, 0.24f), DawnEnd, drag: 4);
        }
        lcMoteN = 12;
    }

    void LongSweep(Ev.Flare e)
    {
        lcSweepT = t;
        // The sweep comes round to the line's side; it starts a little past the aim so it ends on it.
        lcSweepFrom = (float)e.Angle + 0.4f;
        spendAt = t;
        LcSpend();
        Cam?.Jolt(Vector3.Up, 0.25f * Motion);
        Cue("boom", at, 0.6f);
        Rumble(0.6f, 0.4f, 0.08f);
        ResolveDooms();
    }

    void LongCleave(Ev.Flare e)
    {
        lcCleaveT = t;
        if (lcSweepT < 0) { lcSweepT = t - 0.3; spendAt = t; LcSpend(); }
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
            if (lcCleaveT >= 0 && lcLen > 0)
            {
                // Every struck body waits for the fuse (vfx9 r2: charred at the sweep, the pack went flat black before the
                // seam had lit them). r4a: its moment is timed from the DRAWN crack (the strip's own centre line), by the
                // true distance to it: r3 clamped the along to the line's start and measured across the endless line, so a
                // body straight behind her (along < 0, across ~0) burnt at cleave +0, first of all.
                d.Pending = false;
                var (along, off) = SeamNear(d.Where.X, d.Where.Z);
                d.Across = off;
                d.Ash = off > LcSeamBand;
                if (d.RimAt < 0) d.RimAt = FuseAt(along);
                d.At = DeathAt(along, off);
            }
            else if (d.RimAt < 0)
            {
                // The sweep's: its rim only as the light comes round to it; it stands, shaded as ever, till the fuse.
                float a = Mathf.Atan2(d.Where.Z - at.Z, d.Where.X - at.X);
                float behind = Mathf.PosMod(a - lcSweepFrom, Mathf.Tau);
                d.RimAt = t + SweepEase(behind / Mathf.Tau) * SweepLen + 0.02;
            }
        }
    }

    /// <summary>The seam's deaths: within this of the drawn crack (m). The rest are the sweep's: ash, no gold (vfx9 r4a).</summary>
    const float LcSeamBand = 2.5f;
    /// <summary>The burn's lag behind the fuse, seconds a metre from the drawn crack (r4a: 0.1, so it visibly leaves the crack).</summary>
    const double CharPerMetre = 0.1;
    /// <summary>The ash deaths' fall (Flare time): greyed, then gone in flakes.</summary>
    const float AshLen = 0.45f;
    /// <summary>The latest an ash death may start after the cleave, so all are gone by about +1.2 s.</summary>
    const double AshLatest = 0.72;

    /// <summary>The nearest point of the drawn crack to (x, z): how far along the line it lies (0..lcLen) and how far
    /// off it the point is (m, past the ends too).</summary>
    (float Along, float Off) SeamNear(double x, double z)
    {
        var p = new Vector2((float)x, (float)z);
        var side = new Vector2(-lcDir.Y, lcDir.X);
        float a0 = Mathf.Clamp((p - lcO).Dot(lcDir), 0, lcLen);
        float lo = Math.Max(0, a0 - 3), hi = Math.Min(lcLen, a0 + 3), best = a0, bd = float.MaxValue;
        for (float a = lo; ; a = Math.Min(hi, a + 0.2f))
        {
            float dd = (lcO + lcDir * a + side * CrackOff(a) - p).LengthSquared();
            if (dd < bd) { bd = dd; best = a; }
            if (a >= hi) break;
        }
        return (best, Mathf.Sqrt(bd));
    }

    /// <summary>When a death here begins (Flare time). The seam's: the fuse's arrival at its nearest point of the crack, plus
    /// 0.1 s a metre off it. The rest: after the seam's band (its last at +0.25 s past the fuse), then 0.1 s a metre on,
    /// eased so the farthest start by cleave +0.72 s.</summary>
    double DeathAt(float along, float off)
    {
        if (off <= LcSeamBand) return FuseAt(along) + CharPerMetre * off;
        double s = FuseAt(along) + CharPerMetre * LcSeamBand + 0.05 + 0.4 * (1 - Math.Exp(-(off - LcSeamBand) * CharPerMetre / 0.4));
        return Math.Min(s, lcCleaveT + AshLatest);
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
        // The drain over the Draw and Hold: a value dip with no hue (look.z < 0, flare_world: saturation 0.85, value
        // 0.88), so her light is the only warm thing; repainted from her outward after the cleave, slower.
        double from = lcCleaveT >= 0 ? lcCleaveT : -1;
        look.X = from < 0 ? Mathf.Min(1, (float)t / 0.12f) : Mathf.Max(0, 1 - (float)(t - from) / 1.2f);
        look.Y = from < 0 ? 0 : (float)(t - from) * (reach + 14) / 0.9f;
        look.Z = -1;
        web.X = 0;
        web.Y = 0;

        // No exposure lift, night or day (vfx9 r2: the field floodlit, no source): the light is local. By day the sun and
        // ambient dip over the sweep and cleave instead (LcDayDip).
        SetDip(1);
        LcDayDip();

        // The press: the blade's white-gold core, a 2.5 m light at her hands, her rim (FlareFx.LongCutLight).
        bool held = lcSweepT < 0;
        float steel = held ? 0.75f + 0.6f * Mathf.Exp(-(float)t * 9) : Mathf.Max(0, 1 - (float)(t - lcSweepT) / 0.5f) * 0.75f;
        LcPressLights(dt, held, steel);
        LcColumn();

        // The sweep: its wedge (0..1) and its wash after it (0..1).
        float sweepK = 0, wash = 0;
        if (lcSweepT >= 0)
        {
            float s = (float)(t - lcSweepT);
            sweepK = Mathf.SmoothStep(0, 0.03f, s) * (1 - Mathf.SmoothStep(SweepLen - 0.03f, SweepLen + 0.08f, s));
            wash = Mathf.SmoothStep(0, 0.12f, s) * (1 - Mathf.SmoothStep(SweepLen, SweepLen + 0.5f, s));
            // Three unshadowed lights ride its edge at 0.5 m (the legs' rims), its shimmer behind (FlareFx.LongCutLight).
            LcSweepLights(sweepK);
            if (lcCleaveT < 0) { spendLight.LightEnergy = 0; spendLight.Visible = SpendLightOld; }
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
        RenderingServer.GlobalShaderParameterSet("flare_lc", new Vector4(1, wash, 1.6f, LcBandGain));

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
        // The struck: a warm rim for 3 frames as the sweep (or the fuse) reaches them, then shaded as ever until their
        // moment. Two deaths (vfx9 r4a, the judge: "gold crackle on 250 bodies at once reads as a pattern, not a burn"):
        // the seam's (within LcSeamBand of the drawn crack) char with gold cracks, lit from below, and burn away in big
        // pieces along a wide gold edge in 0.5 s, gold motes rising; the rest grey to about half their own value and fall
        // away as dark ash flakes in 0.45 s, a gold spark now and then, no crackle, no glowing edge.
        if (lcCleaveT >= 0) ResolveDooms();
        foreach (var d in doomed.Values)
        {
            if (d.RimAt >= 0 && d.RimRt < 0 && t >= d.RimAt) d.RimRt = lcRt;
            if (d.Pending || t < d.At) continue;
            float len = d.Ash ? AshLen : BurnLen;
            if (!d.Done)
            {
                d.Done = true; d.Rt = lcRt; BurnUp(d);
                if (Args.Has("shot"))
                {
                    int c = d.Ash ? 1 : 0;
                    float rawAlong = lcLen > 0 ? (new Vector2(d.Where.X, d.Where.Z) - lcO).Dot(lcDir) : 0;
                    lcLogN++;
                    lcClsN[c]++;
                    lcClsStart[c] = Math.Min(lcClsStart[c], d.At - lcCleaveT);
                    lcClsLast[c] = Math.Max(lcClsLast[c], d.At - lcCleaveT);
                    lcClsGone[c] = Math.Max(lcClsGone[c], d.At + len - lcCleaveT);
                    lcClsOff[c] = Math.Max(lcClsOff[c], d.Across);
                    if (rawAlong < 0) { lcBehindN++; lcBehindStart = Math.Min(lcBehindStart, d.At - lcCleaveT); }
                    if (lcLogN <= 12)
                        GD.Print($"longcut struck {lcLogN} ({(d.Ash ? "ash" : "seam")}): off the crack {d.Across:0.0} m, along {rawAlong:0.0} m, rim +{d.RimAt - lcCleaveT:0.000}, start +{d.At - lcCleaveT:0.000}, gone +{d.At + len - lcCleaveT:0.000} (Flare s from the cleave)");
                }
            }
            float k = (float)(t - d.At);
            if (k >= len) continue;
            if (!d.Ash)
            {
                if (lcAshN < AshMax && R() < dt * 12)
                {
                    lcAshN++;
                    glow.Spawn(new FlareBits.P
                    {
                        Kind = FlareBits.Kind.Mote, At = d.Where + new Vector3((R() - 0.5f) * 0.5f, 0.2f + R() * 1.4f * (1 - k / len), (R() - 0.5f) * 0.5f),
                        V = new Vector3((R() - 0.5f) * 0.5f, 0.8f + R() * 1.2f, (R() - 0.5f) * 0.5f), Life = 0.5f + R() * 0.5f, Size = 0.03f + R() * 0.025f, SizeEnd = 0.01f,
                        Color = Night ? new Color(0.8f, 0.5f, 0.16f) : new Color(1.3f, 0.82f, 0.3f), ColorEnd = new Color(0.5f, 0.2f, 0.04f), Drag = 1.5f, Lift = 0.7f,
                    });
                }
            }
            else if (k > 0.08f && lcSootN < SootMax && R() < dt * 13)
            {
                // Ash: dark grey-brown flakes peeling off the falling front (the feet up), drifting out and settling; one in
                // seven a small gold spark.
                lcSootN++;
                float h = 0.15f + R() * 1.5f * Mathf.Clamp((k - 0.08f) / (len - 0.08f), 0, 1) * d.Scale;
                var at0 = d.Where + new Vector3((R() - 0.5f) * 0.6f, h, (R() - 0.5f) * 0.6f);
                if (R() < 1f / 7)
                    glow.Spawn(new FlareBits.P
                    {
                        Kind = FlareBits.Kind.Mote, At = at0, V = new Vector3((R() - 0.5f) * 0.8f, 0.5f + R() * 0.8f, (R() - 0.5f) * 0.8f), Life = 0.3f + R() * 0.3f,
                        Size = 0.022f + R() * 0.015f, SizeEnd = 0.008f, Color = Night ? new Color(0.7f, 0.42f, 0.13f) : new Color(1.1f, 0.68f, 0.24f), ColorEnd = new Color(0.4f, 0.15f, 0.03f), Drag = 1.5f, Lift = 0.4f,
                    });
                else
                {
                    float g = Night ? 0.07f + R() * 0.04f : 0.15f + R() * 0.08f;
                    bed.Spawn(new FlareBits.P
                    {
                        Kind = FlareBits.Kind.Soot, At = at0, V = new Vector3((R() - 0.5f) * 1.2f, 0.2f + R() * 0.6f, (R() - 0.5f) * 1.2f), Life = 0.6f + R() * 0.5f,
                        Size = 0.05f + R() * 0.05f, SizeEnd = 0.03f, Gravity = 1.2f, Drag = 1.8f, Seed = R(),
                        Color = new Color(g * 1.12f, g, g * 0.86f, 0.9f), ColorEnd = new Color(g * 1.1f, g, g * 0.88f, 0f),
                    });
                }
            }
        }
        if (Args.Has("shot") && !lcLogSaid && lcLogN > 0 && lcCleaveT >= 0 && t > lcCleaveT + 2.0)
        {
            lcLogSaid = true;
            GD.Print($"longcut struck summary: {lcLogN} of {doomed.Count} died; ash flakes {lcSootN}, gold motes {lcAshN}; {CrowdView.FlareCensus}");
            for (int c = 0; c < 2; c++)
                GD.Print($"longcut class {(c == 1 ? "ash" : "seam")}: {lcClsN[c]} bodies, start cleave +{(lcClsN[c] > 0 ? lcClsStart[c] : 0):0.000}..+{(lcClsN[c] > 0 ? lcClsLast[c] : 0):0.000}, all gone by +{(lcClsN[c] > 0 ? lcClsGone[c] : 0):0.000}, farthest {lcClsOff[c]:0.0} m off the crack");
            GD.Print($"longcut behind her (along < 0): {lcBehindN} bodies, the first starts +{(lcBehindN > 0 ? lcBehindStart : 0):0.000}");
        }
        // (a kill whose blow event never came and no seam to wait for: its moment now)
        foreach (var d in doomed.Values)
            if (d.Pending && lcCleaveT < 0 && t > d.Born + 0.6) { d.Pending = false; d.At = t; }
    }

    const int AshMax = 240, SootMax = 700;
    int lcAshN, lcSootN, lcLogN, lcBehindN;
    readonly int[] lcClsN = new int[2];
    readonly double[] lcClsStart = new double[2], lcClsLast = new double[2], lcClsGone = new double[2];
    readonly float[] lcClsOff = new float[2];
    double lcBehindStart = double.MaxValue;
    bool lcLogSaid;

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
            // (r3c: 1.5x, the painted glow at the crack cut to its lips: the light carries the reach)
            spendLight.LightEnergy = (Night ? 4.5f : 5.4f) * flash * LcLight;
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
        // (r3c: 1.5x while hot, and out with the cooling, not lingering as two pools of light at the thirds: b7's blobs)
        float heatT = 1 - Mathf.SmoothStep(0.3f, 2.0f, s - run * 0.5f);
        float trailE = (Night ? 3.0f : 2.7f) * Mathf.SmoothStep(0, 0.05f, s) * heatT * heatT * flash * LcLight;
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
        // (r3c: eleven even puffballs read as five dark-brown balls on the line. Now a jet every 0.8-2 m, irregular, about
        // half of them doubled, so the line stands as one wall within 0.3 s.)
        if (lcJetAt.Count == 0)
            for (float a = 0.5f + R() * 0.6f; a < lcLen - 0.3f; a += 0.8f + R() * 1.2f) lcJetAt.Add(a);
        while (lcJetN < lcJetAt.Count && front >= lcJetAt[lcJetN])
        {
            float a = lcJetAt[lcJetN++];
            Jet(a);
            if (R() < 0.5f) Jet(Mathf.Min(lcLen - 0.2f, a + 0.25f + R() * 0.3f));
        }
        while (lcChunkN < LcChunks && front >= (lcChunkN + 0.4f) / LcChunks * lcLen * 0.92f)
        {
            float a = (lcChunkN + 0.4f) / LcChunks * lcLen * 0.92f;
            lcChunkN++;
            ThrowChunk(a);
        }

        // The Return: a thin curtain of smoke off the cooling seam.
        // (r3c: from 0.25 s, behind the front only, holding through the cleave's +2 s, then thinning by +3.4 s)
        if (s > 0.25f && s < 3.4f)
        {
            lcSmokeAcc += dt * 26 * (1 - Mathf.SmoothStep(2.0f, 3.4f, s));
            while (lcSmokeAcc >= 1)
            {
                lcSmokeAcc -= 1;
                float a = 0.8f + R() * (front - 0.8f);
                if (a < 0.8f) continue;
                var p = SeamPoint(a);
                bed.Spawn(new FlareBits.P
                {
                    Kind = FlareBits.Kind.Smoke, At = p + new Vector3((R() - 0.5f) * 0.5f, 0.25f + R() * 0.3f, (R() - 0.5f) * 0.5f),
                    V = new Vector3((R() - 0.5f) * 0.3f, 0.7f + R() * 0.6f, (R() - 0.5f) * 0.3f), Life = 1.9f + R() * 0.8f, Size = 0.5f + R() * 0.25f, SizeEnd = 1.6f + R() * 0.6f,
                    Color = Night ? new Color(0.34f, 0.31f, 0.28f, 0.3f) : new Color(0.4f, 0.37f, 0.33f, 0.28f), ColorEnd = Night ? new Color(0.36f, 0.34f, 0.32f, 0.06f) : new Color(0.44f, 0.41f, 0.38f, 0.05f),
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
    void Dust(Vector3 p, float size, float sizeEnd, float life, Vector3 v, float tone, float tall = 0, float delay = 0)
    {
        var tint = Night ? new Color(0.3f, 0.26f, 0.22f) * tone : new Color(0.78f, 0.7f, 0.58f) * tone;
        // (a jet stands upright: turned only a little, not spun)
        float ang = tall > 1 ? (R() - 0.5f) * 0.25f : float.NaN, spin = tall > 1 ? 0 : (R() - 0.5f) * 0.6f;
        if (lcBooks != null && (lcBooks.Spawn("lc_dust", p, size, life, tint, false, sizeEnd, ang, spin, v, tall, delay)
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
        // (r3d: stretch 1.3 not 2.5 (a picket fence of spikes), scale +-25%, start +-0.06 s, so neighbours merge into one wall)
        float size = (0.8f + R() * 0.35f) * taper * (0.75f + R() * 0.5f);
        var side = new Vector3(-lcDir.Y, 0, lcDir.X) * (R() - 0.5f) * 0.12f;
        Dust(p + side + Vector3.Up * size * 1.1f, size, size * 2.7f, 1.9f + R() * 0.5f, Vector3.Up * (1.8f + R() * 0.9f) * taper, Night ? 1.25f : 1.7f, 1.3f, (R() - 0.5f) * 0.12f + 0.06f);
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

    /// <summary>A struck body's death begins: the seam's leave a char scar where they stood. (No smoke puff: r3's per-body
    /// breath of grey smoke was the judge's "grey puffballs" by night and "brown smudges over the crowd" by day: vfx9 r4a.)</summary>
    void BurnUp(Doom d)
    {
        if (d.Ash) return;
        scars.Spawn(new FlareBits.P { Kind = FlareBits.Kind.Scar, At = d.Where + Vector3.Up * 0.04f, Life = 4.2f + R(), Size = 0.6f + R() * 0.3f, Color = new Color(0.025f, 0.02f, 0.016f, 0.55f) });
    }

    /// <summary>For CrowdView: how a held body is drawn (x frozen, y char, z dissolve, w burning). Burns Twice's are ice
    /// statues; the Long Cut's stand in their last pose until their moment, then burn away in gold (the seam's) or ash.</summary>
    public Vector4 StatueLook(int enemy)
    {
        if (!IsLongCut) return new Vector4(1, 0, 0, 0);
        if (!doomed.TryGetValue(enemy, out var d)) return Vector4.Zero;
        if (d.Pending || t < d.At) return Vector4.Zero;
        return BurnLook((float)(t - d.At), d.Ash);
    }

    /// <summary>For CrowdView: seconds since the Long Cut's death reached a body lying at (x, z), or -1, and whether it is an
    /// ash death (off the drawn seam). The dead already down in its reach go with the struck (a dark star of her earlier kills
    /// lay round her after the clear: vfx9 fix2), on the struck's clock from the drawn crack (r4a: r3 clamped the along, so
    /// her kills lying behind her burnt at cleave +0, first of all).</summary>
    public double CorpseBurnAge(double x, double z) => CorpseDeath(x, z).Age;

    /// <summary>For CrowdView: whether a corpse at (x, z) goes as ash rather than gold (see CorpseBurnAge).</summary>
    public bool CorpseAsh(double x, double z) => CorpseDeath(x, z).Ash;

    (double Age, bool Ash) CorpseDeath(double x, double z)
    {
        if (!Active || !IsLongCut || lcCleaveT < 0 || lcLen <= 0) return (-1, false);
        var (along, off) = SeamNear(x, z);
        bool inSweep = new Vector2((float)x - at.X, (float)z - at.Z).Length() <= reach;
        bool onSeam = off <= Math.Max(lcHalf, LcSeamBand);
        if (!inSweep && !onSeam) return (-1, false);
        double when = DeathAt(along, off);
        return (t < when ? -1 : t - when, off > LcSeamBand);
    }

    /// <summary>For CrowdView: a body's death look this long after it starts (x the class: 0 the seam's, 1/15 ash, sent in the
    /// frozen slot, which the Long Cut never uses; y the tint's char, 0; z dissolve; w the char 0..1). The seam's: charred in
    /// 0.1 s, burnt away from 0.1 s, gone by 0.5 s. Ash: greyed in 0.12 s, falling away from 0.08 s, gone by 0.45 s.</summary>
    public static Vector4 BurnLook(float k, bool ash = false) => ash
        ? new(1f / 15, 0, Mathf.SmoothStep(0.08f, AshLen - 0.02f, k), Mathf.SmoothStep(0, 0.12f, k))
        : new(0, 0, Mathf.SmoothStep(0.1f, BurnLen - 0.02f, k), Mathf.SmoothStep(0, 0.1f, k));

    /// <summary>The burn-up's length (Flare time), by class.</summary>
    public static float BurnTimeOf(bool ash) => ash ? AshLen : BurnLen;

    /// <summary>For CrowdView: a held body's struck flash, its rim for 3 frames (real time) as its moment comes.</summary>
    public float StatueFlash(int enemy)
    {
        // (the sweep's passing, or the fuse's for the seam's own: a warm rim, no lift of the paint)
        if (!IsLongCut || !doomed.TryGetValue(enemy, out var d) || d.RimRt < 0) return 0;
        return lcRt - d.RimRt < 3.2 / 60.0 ? 0.5f : 0;
    }

    /* The pictures (--shot): each beat on the Flare's clock, at least 0.13 s of real time and a drawn frame apart. */
    int lcBeat;
    double lcBeatRt;
    long lcBeatFrame;

    void LongBeats()
    {
        (string Tag, double At)[] beats =
        {
            // (the hold's picture inside the hold: at freezeLen - 0.1 it came after the sweep had begun, and the 0.13 s spacing
            // pushed the sweep's picture past its end: r2's "the sweep is never seen")
            ("b1_press", 0.035), ("b2_hold", Math.Min(freezeLen - 0.1, 0.2)),
            ("b3_sweep", lcSweepT < 0 ? double.MaxValue : lcSweepT + 0.15),
            ("b4_fuse", lcCleaveT < 0 ? double.MaxValue : lcCleaveT + 0.2), ("b5_seam", lcCleaveT < 0 ? double.MaxValue : lcCleaveT + 0.45),
            ("b6_cool", lcCleaveT < 0 ? double.MaxValue : lcCleaveT + 1.4), ("b7_smoke", lcCleaveT < 0 ? double.MaxValue : lcCleaveT + 2.4),
            ("b8_scar", lcCleaveT < 0 ? double.MaxValue : lcCleaveT + 4.0), ("b9_dead", lcCleaveT < 0 ? double.MaxValue : lcCleaveT + 5.6),
        };
        if (lcBeat >= beats.Length || t < beats[lcBeat].At) return;
        if (lcBeatRt >= 0 && lcRt - lcBeatRt < 0.13) return;
        long frame = (long)Engine.GetFramesDrawn();
        if (frame <= lcBeatFrame) return;
        GD.Print($"longcut beat {beats[lcBeat].Tag}: flare t {t:0.000} (due {beats[lcBeat].At:0.000}), press +{lcRt:0.00} s real; {CrowdView.FlareCensus}");
        // (the measure's mask: each struck body's torso on screen, the 1920x1080 picture's pixels)
        if (GetViewport()?.GetCamera3D() is { } cam && lcBeat >= 1 && lcBeat <= 4)
        {
            var sb = new System.Text.StringBuilder($"longcut struck screen {beats[lcBeat].Tag}:");
            var vs = GetViewport().GetVisibleRect().Size;
            foreach (var d in doomed.Values)
            {
                if (cam.IsPositionBehind(d.Where)) continue;
                var p = cam.UnprojectPosition(d.Where + Vector3.Up * 0.9f * d.Scale) * new Vector2(1920f / vs.X, 1080f / vs.Y);
                sb.Append($" {p.X:0},{p.Y:0}");
            }
            GD.Print(sb.ToString());
        }
        // (the local-light measure: her on screen, and at the sweep a ring of ground points round her at 3..11 m, each
        // with how far behind the sweep's leading edge it lies, in metres of arc)
        if (GetViewport()?.GetCamera3D() is { } cam2)
        {
            var vs = GetViewport().GetVisibleRect().Size;
            var sc = new Vector2(1920f / vs.X, 1080f / vs.Y);
            var hp = cam2.UnprojectPosition(Her + Vector3.Up * 0.9f) * sc;
            GD.Print($"longcut her screen {beats[lcBeat].Tag}: {hp.X:0},{hp.Y:0}");
            if (beats[lcBeat].Tag == "b3_sweep")
            {
                float lead = SweepLead();
                foreach (float r in new[] { 3f, 5f, 7f, 9f, 11f })
                {
                    var sb = new System.Text.StringBuilder($"longcut sweep ring {r:0}:");
                    for (int i = 0; i < 120; i++)
                    {
                        float ang = lead - i * Mathf.Tau / 120;
                        var w = new Vector3(at.X + Mathf.Cos(ang) * r, 0, at.Z + Mathf.Sin(ang) * r);
                        w.Y = (float)HeightAt(w.X, w.Z);
                        if (cam2.IsPositionBehind(w)) continue;
                        var q = cam2.UnprojectPosition(w) * sc;
                        sb.Append($" {i * Mathf.Tau / 120 * r:0.00}:{q.X:0},{q.Y:0}");
                    }
                    GD.Print(sb.ToString());
                }
                GD.Print($"longcut sweep at b3: swept {lead - lcSweepFrom:0.00} rad of {Mathf.Tau:0.00}, blade {(HasBlade ? "held" : "none")}");
            }
        }
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
        LcLightClear();
        foreach (var c in lcChunkList) if (IsInstanceValid(c.Node)) c.Node.QueueFree();
        lcChunkList.Clear();
    }
}

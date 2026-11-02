using System;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/* The Long Cut's own layers (docs/design/FLARE_LOOK.md, The Long Cut: "the seam of morning"). Its colour is dawn-gold,
 * never the Arcanist's ember orange or Burns Twice's frost. The press: dawn-gold motes off her blade, which is the
 * brightest thing in the Hold. The sweep (12 m) is told by what it lights: a knee-height smear of warm light round her
 * over the ground and the rims of what it passes (flare_world's flare_sweep: no ring, no bright edge), a shadowed
 * light riding it, and a thin hot core only along the real steel. The cleave: the seam, a 24 m jagged fissure down
 * the line (flare_world's flare_seam_ground: a broken polyline with branches from a Voronoi field, dark broken lips,
 * a gold-white core), lit from below like a fuse from her feet to its tip in 0.4 s with one shadowed light riding
 * the front, dust jetting up in sequence and chunks thrown out. What it strikes stands in its last pose until the
 * fuse reaches it, then burns up in gold (char, gold tongues, dissolved from a gold edge) and leaves a scorch. The
 * Return: the seam cools gold to red to dark in ~2.5 s under a thin curtain of smoke, gone by 6 s. Peak frame light
 * stays within §1.6 by local light and shape, not a flash. */
public partial class FlareFx
{
    const string LongCutId = "the_long_cut";
    bool IsLongCut => id == LongCutId;

    /// <summary>The seam's fuse: metres a second (24 m in 0.4 s).</summary>
    const float FuseSpeed = 60f;
    /// <summary>A body's burn-up (Flare time): char, gold tongues, dissolved.</summary>
    const float BurnLen = 0.6f;
    const float SweepLen = 0.17f;

    double lcSweepT = -1, lcCleaveT = -1;
    float lcSweepFrom;
    Vector2 lcO, lcDir;
    float lcLen, lcHalf;
    float lcJetAlong;
    double lcSmokeAcc;
    ulong lcLastUs;
    double lcMsSum, lcMsMax;
    int lcMsN;
    bool lcMsSaid;
    /// <summary>Look-dev: the Long Cut's lights scaled (LC_LIGHT).</summary>
    static readonly float LcLight = float.TryParse(System.Environment.GetEnvironmentVariable("LC_LIGHT"), System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var lcl) ? lcl : 1f;

    /// <summary>The held blade (arm:watch_blade or any blade in her hand), for the steel's light: set by the scene.</summary>
    public Node3D? Blade;

    static readonly Color Dawn = new(1.3f, 0.95f, 0.5f), DawnEnd = new(0.9f, 0.45f, 0.12f);

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

    void LongPress()
    {
        lcSweepT = lcCleaveT = -1;
        lcLen = 0;
        lcJetAlong = 0;
        lcSmokeAcc = 0;
        lcLastUs = 0; lcMsSum = lcMsMax = 0; lcMsN = 0; lcMsSaid = false;
        // Frame 1: dawn-gold motes off the steel, drawn up it (a hue per calling: the Arcanist's are ember orange).
        for (int i = 0; i < 26; i++)
        {
            var p = BladeAt(0.3f + R() * 0.7f);
            glow.Spawn(FlareBits.Kind.Mote, p, Rand3() * (2 + R() * 3), 0.3f + R() * 0.25f, 0.05f + R() * 0.05f, Dawn, DawnEnd, drag: 4);
        }
    }

    void LongSweep(Ev.Flare e)
    {
        lcSweepT = t;
        // The sweep comes round to the line's side; it starts a little past the aim so it ends on it.
        lcSweepFrom = (float)e.Angle + 0.4f;
        spendAt = t;
        Shots.Want("b4_sweep", 0.05);
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
        // Pictures at the beats (--shot), real seconds: the cleave's hitstop (8 frames) runs first, then the 0.4 s fuse.
        Shots.Want("b5_fuse", 0.33);
        Shots.Want("b6_seam", 0.6);
        Shots.Want("b7_cool", 1.6);
        Shots.Want("b8_smoke", 3.1);

        Cam?.Jolt(new Vector3(lcDir.X, 0, lcDir.Y) * 0.4f + Vector3.Up, 0.7f * Motion);
        Cue("boom", at, 1);
        Rumble(1, 0.6f, 0.14f);
        ResolveDooms();
        // The seam's start, at her blade: a breath of dust and sparks where the steel bit.
        var p0 = SeamPoint(0.8f);
        for (int i = 0; i < 10; i++)
            glow.Spawn(FlareBits.Kind.Streak, p0 + Vector3.Up * 0.1f, new Vector3((R() - 0.5f) * 5, 4 + R() * 5, (R() - 0.5f) * 5), 0.25f + R() * 0.15f, 0.04f, new Color(1.3f, 0.95f, 0.55f), new Color(1f, 0.4f, 0.08f));
    }

    /// <summary>When the fuse reaches this far along the seam (Flare time).</summary>
    double FuseAt(float along) => lcCleaveT + Math.Max(0, along) / FuseSpeed;

    /// <summary>The kills the blow just made (their Ev.Kill comes before the blow's own event) get their moment: the
    /// sweep's as its light comes round to them, the cleave's as the fuse reaches them.</summary>
    void ResolveDooms()
    {
        foreach (var d in doomed.Values)
        {
            if (!d.Pending) continue;
            d.Pending = false;
            if (lcCleaveT >= 0 && lcLen > 0)
            {
                var rel = new Vector2(d.Where.X, d.Where.Z) - lcO;
                float along = rel.Dot(lcDir);
                d.At = FuseAt(along) + 0.02;
            }
            else
            {
                float a = Mathf.Atan2(d.Where.Z - at.Z, d.Where.X - at.X);
                float behind = Mathf.PosMod(a - lcSweepFrom, Mathf.Tau);
                d.At = t + behind / Mathf.Tau * SweepLen + 0.03;
            }
        }
    }

    /// <summary>Where the seam's crack runs at this far along it (the same broken line flare_world draws).</summary>
    Vector3 SeamPoint(float along)
    {
        float c = SeamOffset(along);
        var side = new Vector2(-lcDir.Y, lcDir.X);
        var w = lcO + lcDir * along + side * c;
        return new Vector3(w.X, (float)HeightAt(w.X, w.Y), w.Y);
    }

    static float H1(float x) { float s = Mathf.Sin(x * 127.1f + 311.7f) * 43758.5453f; return s - Mathf.Floor(s); }

    /// <summary>The crack's offset across the line (m): a jag every 0.55 m over a slow wander (flare_world fl_seam_off).</summary>
    static float SeamOffset(float along)
    {
        float s = along / 0.55f, i = Mathf.Floor(s), f = s - i;
        float jag = Mathf.Lerp(H1(i), H1(i + 1), f) - 0.5f;
        float s2 = along / 3.1f, i2 = Mathf.Floor(s2), f2 = s2 - i2;
        float s3 = along / 0.19f, i3 = Mathf.Floor(s3), jag2 = Mathf.Lerp(H1(i3 + 90), H1(i3 + 91), s3 - i3) - 0.5f;
        float wan = Mathf.Lerp(H1(i2 + 50), H1(i2 + 51), f2) - 0.5f;
        return (jag * 0.34f + jag2 * 0.1f + wan * 0.7f) * Mathf.Clamp(along / 2f, 0, 1);
    }

    /// <summary>Each frame of the Long Cut: the drain and its repaint, the steel, the sweep's and the seam's uniforms,
    /// the fuse's light, its dust and chunks, the smoke of the Return.</summary>
    void LongTick(float dt)
    {
        // The drain over the Draw and Hold: the dark before. Repainted from her outward after the cleave, slower.
        double from = lcCleaveT >= 0 ? lcCleaveT : -1;
        look.X = from < 0 ? Mathf.Min(1, (float)t / 0.12f) : Mathf.Max(0, 1 - (float)(t - from) / 1.2f);
        look.Y = from < 0 ? 0 : (float)(t - from) * (reach + 14) / 0.9f;
        // No web: the net of lines is the Arcanist's (judge, 1 Nov: "the wrong spell").
        web.X = 0;
        web.Y = 0;

        // The steel: the brightest thing in the Hold, its light on her and the ground about her.
        bool held = lcSweepT < 0;
        float steel = held ? Mathf.Min(1, (float)t / 0.25f) : Mathf.Max(0, 1 - (float)(t - lcSweepT) / 0.5f);
        headLight.LightColor = new Color(1f, 0.78f, 0.45f);
        headLight.OmniRange = 4.5f;
        headLight.GlobalPosition = BladeAt(0.65f);
        headLight.LightEnergy = 1.4f * steel * (LessFlash ? 0.6f : 1) * LcLight;
        if (held && R() < dt * 40)
        {
            // Light drawn up the edge, grip to tip.
            var p = BladeAt(R() * 0.5f);
            glow.Spawn(new FlareBits.P { Kind = FlareBits.Kind.Mote, At = p, V = (BladeAt(1) - BladeAt(0)).Normalized() * (1.5f + R()), Life = 0.3f, Size = 0.035f, SizeEnd = 0.02f, Color = new Color(1.4f, 1.1f, 0.7f), ColorEnd = Dawn });
        }

        // The steel's own hot core while it cuts: a thin line along the real blade, as it moves.
        bool cutting = lcSweepT >= 0 && t < lcSweepT + SweepLen + 0.06 || lcCleaveT >= 0 && t < lcCleaveT + 0.08;
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

        // The sweep: its leading angle (unwrapped), its light 0..1.
        float sweepK = 0;
        if (lcSweepT >= 0)
        {
            float s = (float)(t - lcSweepT);
            sweepK = Mathf.SmoothStep(0, 0.03f, s) * (1 - Mathf.SmoothStep(SweepLen, SweepLen + 0.45f, s));
            if (lcCleaveT < 0)
            {
                // Its light rides it at knee height a few metres out: the shadows swing round her.
                float a = SweepLead();
                spendLight.GlobalPosition = new Vector3(at.X + Mathf.Cos(a) * 3.2f, (float)HeightAt(at.X, at.Z) + 1.0f, at.Z + Mathf.Sin(a) * 3.2f);
                spendLight.LightColor = new Color(1f, 0.74f, 0.4f);
                spendLight.OmniRange = 9;
                spendLight.LightEnergy = (Night ? 1.4f : 1.8f) * sweepK * (LessFlash ? 0.6f : 1) * LcLight;
                spendLight.Visible = true;
            }
        }
        if (lcSweepT < 0) { spendLight.LightEnergy = 0; spendLight.Visible = SpendLightOld; }
        RenderingServer.GlobalShaderParameterSet("flare_sweep", new Vector4(SweepLead(), sweepK, reach, lcSweepFrom));

        // The seam.
        if (lcCleaveT >= 0 && lcLen > 0)
        {
            float s = (float)(t - lcCleaveT);
            float front = Mathf.Min(lcLen + 1.5f, s * FuseSpeed);
            float fade = 1 - Mathf.SmoothStep(4.6f, 6.0f, s);
            RenderingServer.GlobalShaderParameterSet("flare_seam", new Vector4(lcO.X, lcO.Y, Mathf.Atan2(lcDir.Y, lcDir.X), lcLen));
            RenderingServer.GlobalShaderParameterSet("flare_seam_t", new Vector4(s, FuseSpeed, fade, Night ? 1 : 0));

            // One shadowed light rides the fuse's front, then settles over the seam's middle and cools with it.
            float run = lcLen / FuseSpeed;
            var fp = SeamPoint(Mathf.Min(front, lcLen));
            if (s <= run)
            {
                spendLightT = -1;
                spendLight.Visible = true;
                spendLight.GlobalPosition = fp + Vector3.Up * 1.0f;
                spendLight.LightColor = new Color(1f, 0.72f, 0.36f);
                spendLight.OmniRange = 8;
                spendLight.LightEnergy = (Night ? 3.5f : 4.5f) * (LessFlash ? 0.6f : 1) * LcLight;
            }
            else
            {
                float k = 1 - Mathf.SmoothStep(0.05f, 1.6f, s - run);
                var mid = SeamPoint(lcLen * 0.55f);
                spendLight.GlobalPosition = fp.Lerp(mid, Mathf.SmoothStep(0, 0.5f, s - run)) + Vector3.Up * 0.9f;
                spendLight.OmniRange = Mathf.Lerp(8, 14, Mathf.SmoothStep(0, 0.5f, s - run));
                spendLight.LightColor = new Color(1f, 0.72f, 0.36f).Lerp(new Color(1f, 0.35f, 0.1f), Mathf.SmoothStep(0.2f, 1.5f, s - run));
                spendLight.LightEnergy = (Night ? 2.2f : 2.5f) * k * (LessFlash ? 0.6f : 1) * LcLight;
                spendLight.Visible = k > 0;
            }

            // Dust jets up in sequence behind the front, chunks thrown out, sparks off the crack.
            while (lcJetAlong < Mathf.Min(front, lcLen + 0.5f))
            {
                float a = lcJetAlong;
                lcJetAlong += 0.7f + R() * 0.4f;
                if (a < 0.6f) continue;
                Jet(a);
            }

            // The Return: a thin curtain of smoke off the cooling seam.
            if (s > 0.35f && s < 3.2f)
            {
                lcSmokeAcc += dt * 34 * (1 - Mathf.SmoothStep(2.2f, 3.2f, s));
                while (lcSmokeAcc >= 1)
                {
                    lcSmokeAcc -= 1;
                    float a = 0.8f + R() * (lcLen - 0.8f);
                    var p = SeamPoint(a);
                    float heat = Mathf.Clamp(1 - (s - a / FuseSpeed - 0.6f) / 2.2f, 0, 1);
                    bed.Spawn(new FlareBits.P
                    {
                        Kind = FlareBits.Kind.Smoke, At = p + new Vector3((R() - 0.5f) * 0.5f, 0.25f + R() * 0.3f, (R() - 0.5f) * 0.5f),
                        V = new Vector3((R() - 0.5f) * 0.3f, 0.7f + R() * 0.6f, (R() - 0.5f) * 0.3f), Life = 1.9f + R() * 0.8f, Size = 0.5f + R() * 0.25f, SizeEnd = 1.6f + R() * 0.6f,
                        Color = Night ? new Color(0.07f, 0.06f, 0.055f, 0.32f) : new Color(0.2f, 0.18f, 0.16f, 0.3f), ColorEnd = Night ? new Color(0.09f, 0.085f, 0.08f, 0.08f) : new Color(0.26f, 0.24f, 0.22f, 0.06f),
                        Drag = 0.8f, Lift = 0.25f, Swirl = 0.5f, Seed = R(), Wind = new Vector3(0.25f, 0, 0.1f),
                        Glow = 0.0f + 0.0f * heat,
                    });
                }
            }
        }
        else
        {
            RenderingServer.GlobalShaderParameterSet("flare_seam", Vector4.Zero);
        }

        // (for the pictures' log: wall-clock frame time from the press to the seam's cooling, in the packed crowd)
        if (Args.Has("shot"))
        {
            ulong now = Time.GetTicksUsec();
            if (lcLastUs > 0)
            {
                double ms = (now - lcLastUs) / 1000.0;
                lcMsSum += ms; lcMsN++; lcMsMax = Math.Max(lcMsMax, ms);
            }
            lcLastUs = now;
            if (!lcMsSaid && lcCleaveT >= 0 && t > lcCleaveT + 1.5)
            {
                lcMsSaid = true;
                GD.Print($"longcut frame time press..cleave+1.5s: mean {lcMsSum / Math.Max(1, lcMsN):0.0} ms, max {lcMsMax:0.0} ms over {lcMsN} frames; bits {glow.Count}+{bed.Count}, struck {doomed.Count}");
            }
        }
        // The struck burn up as their moment comes.
        foreach (var d in doomed.Values)
        {
            if (d.Pending || d.Done || t < d.At) continue;
            d.Done = true;
            BurnUp(d);
        }
        // (a kill whose blow event never came: its moment now)
        foreach (var d in doomed.Values)
            if (d.Pending && t > d.Born + 0.4) { d.Pending = false; d.At = t; }
    }

    /// <summary>The sweep's leading angle now (radians, unwrapped).</summary>
    float SweepLead()
    {
        if (lcSweepT < 0) return lcSweepFrom;
        float k = Mathf.Clamp((float)(t - lcSweepT) / SweepLen, 0, 1);
        k = 1 - (1 - k) * (1 - k);
        return lcSweepFrom + Mathf.Tau * k;
    }

    /// <summary>A jet off the seam at this far along it: dust up, a chunk or two thrown out, hot sparks.</summary>
    void Jet(float along)
    {
        var p = SeamPoint(along);
        float taper = Mathf.Lerp(1f, 0.55f, along / Math.Max(1, lcLen));
        var side = new Vector3(-lcDir.Y, 0, lcDir.X);
        var fwd = new Vector3(lcDir.X, 0, lcDir.Y);
        // Dust: pale earth by day, dark by night; its belly lit by the crack under it.
        int nd = 2 + (R() < 0.5f ? 1 : 0);
        for (int i = 0; i < nd; i++)
            bed.Spawn(new FlareBits.P
            {
                Kind = FlareBits.Kind.Puff, At = p + side * ((R() - 0.5f) * 0.5f) + Vector3.Up * 0.15f,
                V = side * ((R() - 0.5f) * 1.4f) + fwd * (R() * 1.2f) + Vector3.Up * (1.2f + R() * R() * 6.5f) * taper,
                Life = 0.8f + R() * 0.9f, Size = 0.25f + R() * 0.2f, SizeEnd = (0.8f + R() * 0.8f) * taper,
                Color = Night ? new Color(0.13f, 0.11f, 0.09f, 0.5f) : new Color(0.3f, 0.26f, 0.2f, 0.42f),
                ColorEnd = Night ? new Color(0.1f, 0.09f, 0.08f, 0.0f) : new Color(0.32f, 0.29f, 0.25f, 0.0f),
                Drag = 3.2f, Lift = 0.2f, Gravity = 0, Swirl = 0.6f, Seed = R(),
                Glow = Night ? 1.6f : 0.35f,
            });
        // Chunks of the ground, thrown up and out to either side.
        int nc = R() < 0.6f ? 2 : 1;
        for (int i = 0; i < nc; i++)
        {
            float sd = R() < 0.5f ? -1 : 1;
            bed.Spawn(new FlareBits.P
            {
                Kind = FlareBits.Kind.Soot, At = p + Vector3.Up * 0.1f,
                V = side * sd * (1.2f + R() * 2.2f) + fwd * (R() - 0.3f) * 1.5f + Vector3.Up * (3.5f + R() * 3.5f),
                Life = 1.1f + R() * 0.5f, Size = (0.12f + R() * 0.16f) * taper, Gravity = 16, Drag = 0.4f,
                Color = new Color(0.07f, 0.055f, 0.045f, 1), ColorEnd = new Color(0.07f, 0.055f, 0.045f, 1),
            });
        }
        // Sparks off the crack: short gold streaks.
        int ns = 2 + (R() < 0.5f ? 1 : 0);
        for (int i = 0; i < ns; i++)
            glow.Spawn(FlareBits.Kind.Streak, p + Vector3.Up * 0.05f, side * ((R() - 0.5f) * 3) + Vector3.Up * (4 + R() * 5) * taper, 0.22f + R() * 0.15f, 0.035f,
                new Color(1.3f, 0.9f, 0.45f), new Color(1f, 0.35f, 0.06f), gravity: 9);
    }

    /// <summary>A struck body's burn-up: gold motes off it, a breath of dark smoke, a scorch where it stood.</summary>
    void BurnUp(Doom d)
    {
        var w = d.Where;
        for (int i = 0; i < 6; i++)
            glow.Spawn(new FlareBits.P
            {
                Kind = FlareBits.Kind.Mote, At = w + new Vector3((R() - 0.5f) * 0.5f, 0.3f + R() * 1.3f, (R() - 0.5f) * 0.5f),
                V = new Vector3((R() - 0.5f) * 0.8f, 0.8f + R() * 1.6f, (R() - 0.5f) * 0.8f), Life = 0.6f + R() * 0.5f, Size = 0.04f + R() * 0.03f, SizeEnd = 0.02f,
                Color = new Color(1.25f, 0.85f, 0.4f), ColorEnd = new Color(0.8f, 0.25f, 0.05f), Drag = 1.5f, Lift = 0.6f,
            });
        bed.Spawn(new FlareBits.P
        {
            Kind = FlareBits.Kind.Smoke, At = w + Vector3.Up * 0.9f, V = Vector3.Up * 0.9f, Life = 1.4f + R() * 0.5f, Size = 0.5f, SizeEnd = 1.3f,
            Color = new Color(0.06f, 0.05f, 0.045f, 0.4f), ColorEnd = new Color(0.08f, 0.075f, 0.07f, 0.0f), Drag = 1f, Lift = 0.3f, Swirl = 0.4f, Seed = R(),
        });
        scars.Spawn(new FlareBits.P { Kind = FlareBits.Kind.Scar, At = w + Vector3.Up * 0.04f, Life = 4.2f + R(), Size = 0.6f + R() * 0.3f, Color = new Color(0.025f, 0.02f, 0.016f, 0.55f) });
    }

    /// <summary>For CrowdView: how a held body is drawn (x frozen, y char, z dissolve, w burning). Burns Twice's are ice
    /// statues; the Long Cut's stand in their last pose until the fuse reaches them, then burn up in gold.</summary>
    public Vector4 StatueLook(int enemy)
    {
        if (!IsLongCut) return new Vector4(1, 0, 0, 0);
        if (!doomed.TryGetValue(enemy, out var d)) return Vector4.Zero;
        // (held: struck dark, waiting for the fuse; a pale risen body stood as a cream ghost in the drain)
        if (d.Pending || t < d.At) return new Vector4(0, 0.45f, 0, 0);
        float k = (float)(t - d.At);
        return new Vector4(0, 0.45f + 0.55f * Mathf.SmoothStep(0, 0.08f, k), Mathf.SmoothStep(0.1f, BurnLen, k), 0.5f * (1 - Mathf.SmoothStep(0.25f, 0.55f, k)) * Mathf.SmoothStep(0, 0.04f, k));
    }

    void LongClear()
    {
        lcSweepT = lcCleaveT = -1;
        lcLen = 0;
        RenderingServer.GlobalShaderParameterSet("flare_seam", Vector4.Zero);
        RenderingServer.GlobalShaderParameterSet("flare_sweep", Vector4.Zero);
        if (headLight != null) headLight.LightColor = new Color(1f, 0.55f, 0.2f);
    }
}

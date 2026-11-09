using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// P7 (the skills lead, 9 Nov): Heroic Leap, Shield Charge (and its Turn, Pile Driver's slam) and the dash's Hard Landing,
/// drawn in the FX language (docs/design/FX_LANGUAGE.md §1-5). Light (the ring, the stars, the glints, the ribbons, the
/// afterimages, the shove) is the Warden's steel after the grade (shaders/fx_p7*.gdshader on FxAfter, the physical bands of
/// data/look/fx_language.json, never a hand-picked color); matter (the dust, the crack, the chunks, her leap's shadow) is the
/// world's, lit by the rig (the Groundbreaker's puffs, decals and faceted stones: BattleFx.WardenGround). The camera's
/// weight is a 2-3 frame hitstop (WorldScene.Weigh) and a short pixel kick (FollowCamera.JoltPx), never the sim's long shake.
/// --p7fx-off: none of it (the frame-time A|B). --clip prints `p7ev NAME frame N` for tools/fx/skill_clip.py.
/// </summary>
public partial class BattleFx
{
    static readonly bool P7Off = Args.Has("p7fx-off");
    const string P7Shader = "res://shaders/fx_p7.gdshader", P7TopShader = "res://shaders/fx_p7_top.gdshader", P7GhostShader = "res://shaders/fx_p7_ghost.gdshader";
    const float P7Sample = 1 / 12f;
    /// <summary>Her figure (WorldScene sets it): the afterimages are snapshots of its pose.</summary>
    public Node3D? Her3D;

    sealed class P7Shape
    {
        public required MeshInstance3D N;
        public required ShaderMaterial M;
        public float Age, Life;
        public Action<P7Shape>? Step;
    }

    sealed class P7Trail
    {
        public required MeshInstance3D N;
        public required ImmediateMesh Mesh;
        public required ShaderMaterial M;
        public readonly List<(Vector3 P, float Age)> Pts = new();
        public Func<Vector3>? Source;
        public float Life = 0.2f, Width = 0.2f, Until;
        public float Age;
    }

    sealed class P7Ghost
    {
        public required Node3D Root;
        public required ShaderMaterial M;
        public float Age, Life;
    }

    sealed class P7Light
    {
        public required OmniLight3D L;
        public float Age = 9, Peak;
    }

    sealed class P7LeapRun
    {
        public double X0, Z0, X1, Z1, Dur, R;
        public float T;
        public P7Shape? Ring;
        public P7Trail? Ribbon;
    }

    readonly List<P7Shape> p7Shapes = new();
    readonly List<P7Trail> p7Trails = new();
    readonly List<P7Ghost> p7Ghosts = new();
    readonly List<P7Light> p7Lights = new();
    P7LeapRun? p7Leap;
    Decal? p7Shadow;
    // the charge: its trail, its ghosts still owed (times into the run), whether its first impact was drawn
    P7Trail? p7ChargeTrail;
    readonly List<float> p7GhostDue = new();
    float p7ChargeT = -1, p7ChargeDur;
    Vector3 p7ChargeDir;
    bool p7ChargeHit;
    bool p7HushShake, p7Warm;
    static PlaneMesh? p7Plane;
    static QuadMesh? p7Quad;

    static void P7Ev(string name)
    {
        if (Args.Has("clip")) GD.Print($"p7ev {name} frame {Engine.GetFramesDrawn()}");
    }

    static Color P7Band(int i)
    {
        var s = FxCel.Lang["Physical"];
        string hex = s == null ? "#f4b43a" : (i == 0 ? s.Edge.Hex : i == 1 ? s.Mid.Hex : s.Core.Hex);
        return new Color(hex);
    }

    ShaderMaterial P7Mat(int mode, bool top = false, bool ghost = false)
    {
        var m = new ShaderMaterial { Shader = GD.Load<Shader>(ghost ? P7GhostShader : top ? P7TopShader : P7Shader) };
        FxCel.Apply(m, School.Physical, FxAfter.On);
        m.SetShaderParameter("p7_mode", mode);
        m.SetShaderParameter("p7_seed", R() * 10);
        return m;
    }

    /// <summary>A quad shape: flat on the ground (half-size `half`, at `at`) or facing the camera (`bill`).</summary>
    P7Shape P7Quad(int mode, Vector3 at, float half, float life, bool bill = false, bool top = false, Action<P7Shape>? step = null)
    {
        p7Plane ??= new PlaneMesh { Size = new Vector2(2, 2) };
        p7Quad ??= new QuadMesh { Size = new Vector2(2, 2) };
        var m = P7Mat(mode, top);
        if (bill) m.SetShaderParameter("p7_bill", 1f);
        var n = new MeshInstance3D { Mesh = bill ? p7Quad : p7Plane, MaterialOverride = m, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
        n.Scale = Vector3.One * half;
        AddChild(n);
        n.GlobalPosition = at;
        if (FxAfter.On) FxAfter.Adopt(n);
        var s = new P7Shape { N = n, M = m, Life = life, Step = step };
        p7Shapes.Add(s);
        return s;
    }

    P7Trail P7NewTrail(Func<Vector3> src, float width, float until, float life)
    {
        var mesh = new ImmediateMesh();
        var m = P7Mat(2);
        var n = new MeshInstance3D { Mesh = mesh, MaterialOverride = m, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
        AddChild(n);
        n.GlobalTransform = Transform3D.Identity;
        if (FxAfter.On) FxAfter.Adopt(n);
        var t = new P7Trail { N = n, Mesh = mesh, M = m, Source = src, Width = width, Until = until, Life = life };
        p7Trails.Add(t);
        return t;
    }

    void P7LightOn(Vector3 at, float range, float peak)
    {
        P7Light? l = null;
        foreach (var x in p7Lights) if (x.Age > 0.4f) { l = x; break; }
        if (l == null)
        {
            if (p7Lights.Count >= 3) l = p7Lights[0];
            else
            {
                var o = new OmniLight3D { ShadowEnabled = false, OmniAttenuation = 1.2f, Visible = false };
                AddChild(o);
                l = new P7Light { L = o };
                p7Lights.Add(l);
            }
        }
        // the pool is the school's mid hue on the world (FX_LANGUAGE §1), wider than the shape
        l.L.LightColor = P7Band(1);
        l.L.OmniRange = range;
        l.L.GlobalPosition = at;
        l.Age = 0; l.Peak = peak;
        l.L.Visible = true;
    }

    /* ----------------------------------------------------------- events -- */

    /// <summary>Before the switch: the sim's long shake is hushed on a frame P7 draws its own weight.</summary>
    void P7Pre(IReadOnlyList<CombatEvent> events)
    {
        p7HushShake = false;
        if (P7Off) return;
        P7PreStorm(events);
        foreach (var e in events)
            if (e is Ev.Leap { Phase: LeapPhase.Land } || e is Ev.Charge { Phase: ChargePhase.Stop or ChargePhase.Slam }) p7HushShake = true;
    }

    /// <summary>Impact's hook: a body struck by the leap or the charge takes the struck rim; the stars and sparks are
    /// drawn by the event (one star a contact, not one a number).</summary>
    bool P7Owns(Ev.Hit e)
    {
        if (P7Off) return false;
        if (P7OwnsStorm(e)) return true;
        if (e.Art is not ("heroic_leap" or "shield_charge" or "shield_charge_slam")) return false;
        if (e.Target >= 0) { struckRims[e.Target] = Engine.GetFramesDrawn(); rimNoFlash.Remove(e.Target); }
        return true;
    }

    void P7Leap(Ev.Leap e)
    {
        if (P7Off) return;
        P7WarmUp();
        if (e.Phase == LeapPhase.Takeoff)
        {
            P7Ev("leap_takeoff");
            var from = V(e.X0, Y(e.X0, e.Z0), e.Z0);
            var dir = new Vector3((float)(e.X1 - e.X0), 0, (float)(e.Z1 - e.Z0));
            dir = dir.LengthSquared() > 1e-4f ? dir.Normalized() : Vector3.Forward;
            P7Glint(P7BladeAt(1), 0.55f);
            // the crouch's kick: dust thrown back and out from her feet, two values, low
            for (int i = 0; i < 9; i++)
            {
                float a = R() * Mathf.Tau;
                var o = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                var v = (o * 1.6f - dir * 1.4f) * (0.8f + R() * 0.6f) + Vector3.Up * (0.3f + R() * 0.5f);
                WgPuff(from + o * 0.25f + Vector3.Up * 0.18f, v, 0.26f + R() * 0.1f, 1.5f, 0.55f + R() * 0.25f, WgDust(i % 3 == 0 ? 0.74f : 1.04f), 0.74f, 3.5f);
            }
            // the mark: where she lands, exactly the ring she strikes
            double r = e.Radius, x1 = e.X1, z1 = e.Z1;
            var run = new P7LeapRun { X0 = e.X0, Z0 = e.Z0, X1 = x1, Z1 = z1, Dur = e.Dur, R = r };
            run.Ring = P7Quad(0, V(x1, Y(x1, z1) + 0.04, z1), (float)r, (float)e.Dur + 3 * P7Sample, step: s =>
            {
                float prog = Mathf.Clamp(s.Age / (float)run.Dur, 0, 1);
                s.M.SetShaderParameter("p7_prog", prog);
                s.M.SetShaderParameter("p7_width", Mathf.Clamp(0.32f / (float)run.R, 0.05f, 0.12f));
                s.M.SetShaderParameter("p7_alpha", 0.5f);
                // once down, it is spent: gone in two steps
                float after = s.Age - (float)run.Dur;
                s.M.SetShaderParameter("p7_fade", after <= 0 ? 0f : Mathf.Min(1, Mathf.Floor(after / P7Sample + 1) * 0.5f));
            });
            run.Ribbon = P7NewTrail(() => P7BladeAt(0.85f), 0.14f, (float)e.Dur, 2.5f * P7Sample);
            p7Leap = run;
            return;
        }
        // Land
        P7Ev("leap_land");
        if (p7Leap?.Ribbon is { } rb) rb.Until = 0;
        p7Leap = null;
        if (p7Shadow != null) p7Shadow.Visible = false;
        P7Slam(e.X1, e.Z1, (float)e.Radius, 1f);
        Cam?.JoltPx(Vector3.Up, 10f);
    }

    /// <summary>The landing (and, smaller, Pile Driver's slam): a one-sample white-gold star flat on the ground, the crack
    /// (matter, its heart cooling core, mid, edge over 1.5 s), a low two-value dust ring, chunks on gravity and the gold
    /// pool at 1.5x the radius.</summary>
    void P7Slam(double x, double z, float r, float k)
    {
        var c = V(x, Y(x, z), z);
        P7Quad(1, c + Vector3.Up * 0.05f, r * 0.62f * k, 5 * P7Sample, step: s => s.M.SetShaderParameter("p7_t", s.Age));
        P7LightOn(c + Vector3.Up * 1.4f, r * 1.5f, (Flare.Night ? 4.2f : 6f) * k);
        // the crack: radial splits out from the heart (the Groundbreaker's strip, its narrow end), and their hearts
        float a0 = R() * Mathf.Tau;
        int cracks = k >= 1 ? 7 : 5;
        Color[] steps = [P7Band(2).SrgbToLinear(), P7Band(1).SrgbToLinear(), P7Band(0).SrgbToLinear()];
        float day = Flare.Night ? 1f : 1.7f;
        for (int i = 0; i < cracks && wgAlb != null; i++)
        {
            float a = a0 + (i + (R() - 0.5f) * 0.5f) / cracks * Mathf.Tau;
            var dir = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
            float len = r * (0.62f + R() * 0.38f) * k;
            int t0 = 8 + (int)(R() * 1.99f);
            var from = new Vector2((float)x, (float)z) + dir * 0.1f;
            float theta = Mathf.Atan2(-dir.Y, dir.X), seg = len / 2;
            for (int j = 0; j < 2; j++)
            {
                var cc = from + dir * seg * (j + 0.5f);
                var pos = V(cc.X, Y(cc.X, cc.Y), cc.Y);
                var size = new Vector3(seg * 1.03f, 1.6f, WgBand * 0.9f * k);
                WgDecalOn(pos, theta, size, wgAlb![t0 + j], wgNrm![t0 + j], null, 3.2f, 1f, 0, 0);
                var hd = WgDecalOn(pos, theta, size, null, null, wgEmi![t0 + j], 1.5f, 1f, 1.6f * day, 0, 0, steps[0]);
                if (hd != null) { hd.Steps = steps; hd.StepAt = [0.12f, 0.5f, 1.0f]; hd.StepE = [1.0f, 0.85f, 0.7f]; }
            }
        }
        // the dust ring: low (0.2-0.35 m), rolling out to the radius in 0.4 s, a lit top over a darker skirt
        int puffs = k >= 1 ? 30 : 20;
        const float drag = 4.5f;
        for (int i = 0; i < puffs; i++)
        {
            float a = a0 + (i + R() * 0.9f) / puffs * Mathf.Tau, d0 = 0.4f + R() * 0.3f;
            var o = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            float reach = r * k * (0.92f + R() * 0.18f) - d0;
            float v0 = reach * drag / (1 - Mathf.Exp(-drag * 0.4f));
            double px = x + o.X * d0, pz = z + o.Z * d0;
            float sz = (0.3f + R() * 0.12f) * (0.8f + 0.2f * k);
            WgPuff(V(px, Y(px, pz) + 0.2, pz), o * v0 + Vector3.Up * (0.05f + R() * 0.1f), sz, 1.35f, 0.8f + R() * 0.3f, WgDust(1.02f + R() * 0.1f), 0.78f, drag);
            if (i % 2 == 0) WgPuff(V(px, Y(px, pz) + 0.1, pz), o * v0 * 0.85f, sz * 0.8f, 1.3f, 0.7f + R() * 0.25f, WgDust(0.72f), 0.74f, drag);
        }
        // chunks: faceted rock (the strip's stones), up and back on gravity
        int chunks = k >= 1 ? 12 + (int)(R() * 4.99f) : 6 + (int)(R() * 2.99f);
        for (int i = 0; i < chunks; i++)
        {
            float a = R() * Mathf.Tau, d = r * 0.45f * Mathf.Sqrt(R());
            var o = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            double px = x + o.X * d, pz = z + o.Z * d;
            var v = o * (1.2f + R() * 2.2f) + Vector3.Up * (3.2f + R() * 3.0f) * (0.75f + 0.25f * k);
            WgThrow(V(px, Y(px, pz) + 0.2, pz), v, (0.8f + R() * 0.35f) * (0.8f + 0.2f * k), 1.8f + R() * 0.5f, 5);
        }
    }

    void P7Charge(Ev.Charge e, Battle b)
    {
        if (P7Off) return;
        P7WarmUp();
        var dir = new Vector3((float)e.DX, 0, (float)e.DZ);
        dir = dir.LengthSquared() > 1e-4f ? dir.Normalized() : Vector3.Forward;
        switch (e.Phase)
        {
            case ChargePhase.Start:
            {
                P7Ev("charge_start");
                var feet = V(e.X, Y(e.X, e.Z), e.Z);
                P7Glint(feet + dir * 0.55f + Vector3.Up * 1.25f, 0.6f);
                // the kick off: dust thrown back from her heels and out to the sides
                for (int i = 0; i < 9; i++)
                {
                    var side = new Vector3(dir.Z, 0, -dir.X) * ((R() - 0.5f) * 2.4f);
                    var v = -dir * (2.2f + R() * 1.6f) + side + Vector3.Up * (0.3f + R() * 0.4f);
                    WgPuff(feet - dir * 0.2f + Vector3.Up * 0.16f, v, 0.25f + R() * 0.1f, 1.5f, 0.5f + R() * 0.25f, WgDust(i % 3 == 0 ? 0.72f : 1.04f), 0.74f, 3.8f);
                }
                p7ChargeT = 0; p7ChargeDur = (float)e.Dur; p7ChargeDir = dir; p7ChargeHit = false;
                p7GhostDue.Clear();
                p7GhostDue.AddRange([p7ChargeDur * 0.22f, p7ChargeDur * 0.52f, p7ChargeDur * 0.82f]);
                if (p7ChargeTrail != null) p7ChargeTrail.Until = 0;
                p7ChargeTrail = P7NewTrail(() => PlayerPos + Vector3.Up * 0.95f - p7ChargeDir * 0.25f, 0.42f, p7ChargeDur + 0.05f, 2.5f * P7Sample);
                break;
            }
            case ChargePhase.Impact:
            {
                P7Ev("charge_impact");
                var at = P7Body(e.Target, e.X, e.Z, b);
                bool first = !p7ChargeHit;
                p7ChargeHit = true;
                // a hit (§4): one star at the contact, core then mid, sparks off it; the first gets the pool and the hitstop
                P7Quad(1, at - dir * 0.15f, first ? 0.62f : 0.46f, 4 * P7Sample, bill: true, top: true, step: s => s.M.SetShaderParameter("p7_t", s.Age));
                if (first) P7LightOn(at + Vector3.Up * 0.4f, 3.2f, Flare.Night ? 2.2f : 3f);
                break;
            }
            case ChargePhase.Stop:
            {
                P7Ev("charge_stop");
                var at = P7Body(e.Target, e.X, e.Z, b);
                // the champion stops her: a heavier hit, the star big, a pool, a kick along the blow, dust at its feet
                P7Quad(1, at - dir * 0.3f, 1.05f, 5 * P7Sample, bill: true, top: true, step: s => s.M.SetShaderParameter("p7_t", s.Age));
                P7LightOn(at + Vector3.Up * 0.5f, 4.5f, Flare.Night ? 3.4f : 4.5f);
                Cam?.JoltPx(dir, 7f);
                var feet = V(e.X, Y(e.X, e.Z), e.Z);
                for (int i = 0; i < 10; i++)
                {
                    float a = R() * Mathf.Tau;
                    var o = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                    WgPuff(feet + o * 0.3f + Vector3.Up * 0.2f, (o * 1.8f + dir * 1.2f) * (0.7f + R() * 0.6f) + Vector3.Up * 0.3f, 0.28f + R() * 0.1f, 1.4f, 0.6f + R() * 0.25f, WgDust(i % 3 == 0 ? 0.72f : 1.04f), 0.76f, 3.8f);
                }
                p7GhostDue.Clear();
                break;
            }
            case ChargePhase.Slam:
                P7Ev("charge_slam");
                P7Slam(e.X, e.Z, (float)e.Radius, 0.72f);
                Cam?.JoltPx(Vector3.Up, 6f);
                break;
            case ChargePhase.End:
                P7Ev("charge_end");
                if (p7ChargeTrail != null) p7ChargeTrail.Until = 0;
                p7ChargeTrail = null;
                p7ChargeT = -1;
                p7GhostDue.Clear();
                break;
        }
    }

    /// <summary>Hard Landing: a low steel arc running out at her feet to the shove's radius, and the dust it throws.</summary>
    void P7Shove(Ev.HardLanding e)
    {
        if (P7Off) return;
        P7WarmUp();
        P7Ev("hard_landing");
        float r = (float)e.Radius;
        var c = V(e.X, Y(e.X, e.Z), e.Z);
        P7Quad(5, c + Vector3.Up * 0.06f, r, 0.2f + 3 * P7Sample, step: s =>
        {
            s.M.SetShaderParameter("p7_prog", Mathf.Clamp(s.Age / 0.2f, 0, 1));
            s.M.SetShaderParameter("p7_width", 0.16f);
            s.M.SetShaderParameter("p7_alpha", 0.85f);
            float after = s.Age - 0.2f;
            s.M.SetShaderParameter("p7_fade", after <= 0 ? 0f : Mathf.Min(1, Mathf.Floor(after / P7Sample + 1) * 0.34f));
        });
        for (int i = 0; i < 14; i++)
        {
            float a = (i + R() * 0.8f) / 14 * Mathf.Tau;
            var o = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            const float drag = 5f;
            float v0 = (r * 0.9f) * drag / (1 - Mathf.Exp(-drag * 0.3f));
            WgPuff(c + o * 0.3f + Vector3.Up * 0.16f, o * v0 + Vector3.Up * 0.08f, 0.24f + R() * 0.08f, 1.35f, 0.55f + R() * 0.2f, WgDust(i % 2 == 0 ? 1.04f : 0.74f), 0.74f, drag);
        }
    }

    /* ----------------------------------------------------------- pieces -- */

    /// <summary>The press: a four-point glint in the core color for three frames (§4).</summary>
    void P7Glint(Vector3 at, float size) =>
        P7Quad(4, at, size, 3 / 60f, bill: true, top: true, step: s =>
        {
            int f = (int)(s.Age * 60);
            s.M.SetShaderParameter("p7_fade", f <= 0 ? 0f : f == 1 ? 0.12f : 0.4f);
        });

    Vector3 P7BladeAt(float k)
    {
        if (Flare.Blade is { } bl && IsInstanceValid(bl) && bl.IsInsideTree())
        {
            float tip = bl.HasMeta("tip") ? (float)bl.GetMeta("tip") : 1.4f;
            return bl.GlobalTransform * new Vector3(0, Mathf.Lerp(0.25f, tip, k), 0);
        }
        return PlayerPos + new Vector3(0.3f, 1.1f + 0.6f * k, 0);
    }

    Vector3 P7Body(int id, double x, double z, Battle b)
    {
        if (id >= 0 && id < b.Enemies.Capacity && b.Enemies.Items[id] is { } en)
        {
            var (gx, gz) = CrowdView.Placed?.Invoke(en) ?? (en.X, en.Z);
            return V(gx, Y(gx, gz) + 1.0, gz);
        }
        return V(x, Y(x, z) + 1.0, z);
    }

    void P7WarmUp()
    {
        if (p7Warm) return;
        p7Warm = true;
        if (!wgWarm) WgWarmUp();
    }

    /// <summary>Her shadow in the air (top-down, the only proof of height): a hard-edged shade on the ground under her,
    /// shrinking as she rises and growing as she falls.</summary>
    void P7ShadowAt(Vector3 feet, float h)
    {
        if (p7Shadow == null)
        {
            var img = Image.CreateEmpty(64, 64, false, Image.Format.Rgba8);
            for (int y = 0; y < 64; y++)
                for (int x = 0; x < 64; x++)
                {
                    float d = new Vector2(x - 31.5f, y - 31.5f).Length() / 31.5f;
                    float a = Mathf.Clamp((1 - d) * 24, 0, 1) * (d < 0.72f ? 1f : 0.82f);
                    img.SetPixel(x, y, new Color(0, 0, 0, a));
                }
            p7Shadow = new Decal { TextureAlbedo = ImageTexture.CreateFromImage(img), AlbedoMix = 1, Modulate = new Color(0.02f, 0.02f, 0.03f, 0.55f), CullMask = 1, UpperFade = 0.3f, LowerFade = 0.3f };
            AddChild(p7Shadow);
        }
        float s = 1.05f * (1 - 0.5f * h);
        p7Shadow.Size = new Vector3(s, 2.6f, s * 0.9f);
        p7Shadow.Modulate = new Color(0.02f, 0.02f, 0.03f, 0.55f * (1 - 0.35f * h));
        p7Shadow.GlobalPosition = feet + Vector3.Up * 0.6f;
        p7Shadow.Visible = true;
    }

    /// <summary>An afterimage: her pose this frame, in the mid band (§4: 2-3 flat afterimages that step out).</summary>
    void P7Snap()
    {
        if (Her3D == null || !IsInstanceValid(Her3D)) return;
        var m = P7Mat(3, ghost: true);
        m.SetShaderParameter("p7_alpha", 0.5f);
        var root = new Node3D { Name = "P7Ghost" };
        AddChild(root);
        root.GlobalTransform = Transform3D.Identity;
        var skels = new Dictionary<Skeleton3D, Skeleton3D>();
        foreach (var node in Her3D.FindChildren("*", "MeshInstance3D", true, false))
        {
            if (node is not MeshInstance3D mi || mi.Mesh == null || !mi.IsVisibleInTree() || mi.Name == "FxAfterHole" || (mi.Layers & FxAfter.RenderLayer) != 0) continue;
            if (P7SeeThrough(mi)) continue;
            var copy = new MeshInstance3D { Mesh = mi.Mesh, MaterialOverride = m, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
            if (mi.Skin != null && !mi.Skeleton.IsEmpty && mi.GetNodeOrNull(mi.Skeleton) is Skeleton3D sk)
            {
                if (!skels.TryGetValue(sk, out var ck))
                {
                    ck = new Skeleton3D();
                    for (int i = 0; i < sk.GetBoneCount(); i++)
                    {
                        ck.AddBone(sk.GetBoneName(i));
                        ck.SetBoneRest(i, sk.GetBoneRest(i));
                    }
                    for (int i = 0; i < sk.GetBoneCount(); i++)
                    {
                        ck.SetBoneParent(i, sk.GetBoneParent(i));
                        ck.SetBonePosePosition(i, sk.GetBonePosePosition(i));
                        ck.SetBonePoseRotation(i, sk.GetBonePoseRotation(i));
                        ck.SetBonePoseScale(i, sk.GetBonePoseScale(i));
                    }
                    root.AddChild(ck);
                    ck.GlobalTransform = sk.GlobalTransform;
                    skels[sk] = ck;
                }
                ck.AddChild(copy);
                copy.GlobalTransform = mi.GlobalTransform;
                copy.Skin = mi.Skin;
                copy.Skeleton = new NodePath("..");
            }
            else
            {
                root.AddChild(copy);
                copy.GlobalTransform = mi.GlobalTransform;
            }
            for (int bs = 0; bs < mi.GetBlendShapeCount(); bs++) copy.SetBlendShapeValue(bs, mi.GetBlendShapeValue(bs));
            if (FxAfter.On) FxAfter.Adopt(copy);
        }
        p7Ghosts.Add(new P7Ghost { Root = root, M = m, Life = 3 * P7Sample });
    }

    static bool P7SeeThrough(MeshInstance3D mi)
    {
        var mt = mi.GetActiveMaterial(0);
        if (mt is BaseMaterial3D bm) return bm.Transparency != BaseMaterial3D.TransparencyEnum.Disabled;
        if (mt is ShaderMaterial sm) return sm.Shader != null && sm.Shader.Code.Contains("ALPHA");
        return false;
    }

    /* ------------------------------------------------------------- step -- */

    void StepP7(float dt, Battle b)
    {
        if (P7Off) return;
        StepP7Storm(dt);
        for (int i = p7Shapes.Count - 1; i >= 0; i--)
        {
            var s = p7Shapes[i];
            s.Age += dt;
            if (s.Age >= s.Life || !IsInstanceValid(s.N)) { if (IsInstanceValid(s.N)) s.N.QueueFree(); p7Shapes.RemoveAt(i); continue; }
            s.Step?.Invoke(s);
        }
        for (int i = p7Ghosts.Count - 1; i >= 0; i--)
        {
            var g = p7Ghosts[i];
            g.Age += dt;
            if (g.Age >= g.Life) { g.Root.QueueFree(); p7Ghosts.RemoveAt(i); continue; }
            g.M.SetShaderParameter("p7_t", g.Age);
        }
        foreach (var l in p7Lights)
        {
            if (l.Age > 0.4f) continue;
            l.Age += dt;
            // up on the hit's frame, held a sample, down over two (2-3 samples at a hit, §1)
            float k = l.Age < P7Sample ? 1 : Mathf.Max(0, 1 - (l.Age - P7Sample) / (2 * P7Sample));
            l.L.LightEnergy = l.Peak * k * k;
            if (k <= 0) { l.L.Visible = false; l.Age = 9; }
        }
        // her leap: the ring closing, her shadow, the blade's ribbon
        if (p7Leap is { } run)
        {
            run.T += dt;
            if (b.Player.Leap is { } pl && pl.Weapon != null)
            {
                float h = Mathf.Sin(Mathf.Clamp((float)(pl.T / pl.Dur), 0, 1) * Mathf.Pi);
                P7ShadowAt(new Vector3(PlayerPos.X, Y(PlayerPos.X, PlayerPos.Z), PlayerPos.Z), h);
            }
            else if (run.T > run.Dur + 0.3f) { p7Leap = null; if (p7Shadow != null) p7Shadow.Visible = false; }
        }
        // the charge: its afterimages, owed through the run
        if (p7ChargeT >= 0)
        {
            p7ChargeT += dt;
            for (int i = p7GhostDue.Count - 1; i >= 0; i--)
                if (p7ChargeT >= p7GhostDue[i]) { p7GhostDue.RemoveAt(i); P7Snap(); }
            if (p7ChargeT > p7ChargeDur + 0.5f) p7ChargeT = -1;
        }
        var cam = GetViewport()?.GetCamera3D();
        for (int i = p7Trails.Count - 1; i >= 0; i--)
        {
            var t = p7Trails[i];
            t.Age += dt;
            for (int k = 0; k < t.Pts.Count; k++) t.Pts[k] = (t.Pts[k].P, t.Pts[k].Age + dt);
            t.Pts.RemoveAll(p => p.Age > t.Life);
            if (t.Age <= t.Until && t.Source != null && dt > 0)
            {
                var p = t.Source();
                if (t.Pts.Count == 0 || t.Pts[^1].P.DistanceSquaredTo(p) > 0.0004f) t.Pts.Add((p, 0));
            }
            if (t.Age > t.Until && t.Pts.Count == 0) { t.N.QueueFree(); p7Trails.RemoveAt(i); continue; }
            P7BuildTrail(t, cam);
        }
    }

    void P7BuildTrail(P7Trail t, Camera3D? cam)
    {
        t.Mesh.ClearSurfaces();
        int n = t.Pts.Count;
        if (n < 2 || cam == null) return;
        var eye = cam.GlobalPosition;
        t.Mesh.SurfaceBegin(Mesh.PrimitiveType.TriangleStrip);
        for (int i = 0; i < n; i++)
        {
            var (p, age) = t.Pts[i];
            var d = (i < n - 1 ? t.Pts[i + 1].P - p : p - t.Pts[i - 1].P);
            if (d.LengthSquared() < 1e-6f) d = Vector3.Forward;
            var side = d.Cross(eye - p).Normalized();
            // along: 0 at the oldest (the tail), 1 at the newest (the head); it tapers to a point at the tail
            float along = n == 1 ? 1 : i / (float)(n - 1);
            float life = 1 - age / t.Life;
            float w = t.Width * Mathf.Pow(along, 0.8f) * (0.4f + 0.6f * life);
            t.Mesh.SurfaceSetUV(new Vector2(along * (0.55f + 0.45f * life), 0));
            t.Mesh.SurfaceAddVertex(p - side * w);
            t.Mesh.SurfaceSetUV(new Vector2(along * (0.55f + 0.45f * life), 1));
            t.Mesh.SurfaceAddVertex(p + side * w);
        }
        t.Mesh.SurfaceEnd();
        t.N.MaterialOverride = t.M;
    }
}

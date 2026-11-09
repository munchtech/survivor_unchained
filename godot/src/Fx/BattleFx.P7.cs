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
        /// <summary>(solver A) a swept blade: the strip spans these two points (its base, its tip) instead of a camera-facing width.</summary>
        public Func<(Vector3 A, Vector3 B)>? Sweep;
        public readonly List<Vector3> Pts2 = new();
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

    /// <summary>The world size of one pixel at the play camera (1080 lines) at `at`: strokes are sized in pixels.</summary>
    float P7Px(Vector3 at)
    {
        var cam = GetViewport()?.GetCamera3D();
        if (cam == null) return 0.012f;
        return 2 * cam.GlobalPosition.DistanceTo(at) * Mathf.Tan(Mathf.DegToRad(cam.Fov) / 2) / 1080f;
    }

    /// <summary>Dust in clusters (the judge: never an even dotted circle): `clusters` knots at uneven angles, each 3-6
    /// puffs of varied size, a lit top over a darker skirt, thrown out from `c` to about `reach`, thinning as they run.</summary>
    void P7DustRing(Vector3 c, float reach, int clusters, float k = 1f, float d0 = 0.35f)
    {
        float a0 = R() * Mathf.Tau;
        const float drag = 4.5f;
        for (int q = 0; q < clusters; q++)
        {
            float ac = a0 + (q + (R() - 0.5f) * 0.7f) / clusters * Mathf.Tau;
            int n = 4 + (int)(R() * 3.99f);
            for (int i = 0; i < n; i++)
            {
                float a = ac + (R() - 0.5f) * 0.42f;
                var o = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                float far = reach * (0.7f + R() * 0.38f) - d0;
                float v0 = far * drag / (1 - Mathf.Exp(-drag * 0.45f));
                var at = c + o * d0;
                float sz = (0.24f + R() * R() * 0.5f) * k;
                // the lit top rides a little higher and dies first; the skirt is wider, lower and darker
                WgPuff(at + Vector3.Up * (0.22f + R() * 0.1f), o * v0 + Vector3.Up * (0.15f + R() * 0.25f), sz, 1.5f, 0.6f + R() * 0.3f, WgDust(1.06f + R() * 0.12f), 0.8f, drag);
                WgPuff(at + Vector3.Up * 0.1f, o * v0 * (0.8f + R() * 0.15f), sz * 1.25f, 1.4f, 0.7f + R() * 0.3f, WgDust(0.66f + R() * 0.08f), 0.76f, drag);
            }
        }
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
    // (solver A) the charge's crescent on the shield, its ghost and plow clocks (the dash's ghosts are owed in p7GhostDue)
    P7Shape? p7Crescent;
    float p7GhostNext = -1, p7PlowNext = -1;
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
        if (Args.Has("clip") && bill && (GetViewport()?.GetCamera3D() is { } c3) && c3.GlobalPosition.DistanceTo(at) < 8) GD.Print($"p7 near-camera shape mode {mode} at {at} frame {Engine.GetFramesDrawn()}");
        if (FxAfter.On) FxAfter.Adopt(n);
        var s = new P7Shape { N = n, M = m, Life = life, Step = step };
        p7Shapes.Add(s);
        return s;
    }

    P7Trail P7NewTrail(Func<Vector3> src, float width, float until, float life)
    {
        var mesh = new ImmediateMesh();
        var m = P7Mat(2);
        // a ribbon tapers harder than the default stroke: a wedge, its width falling off all the way from the head
        m.SetShaderParameter("p7_sw", new Vector4(0.14f, 0.52f, 0.42f, 1.4f));
        var n = new MeshInstance3D { Mesh = mesh, MaterialOverride = m, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
        AddChild(n);
        n.GlobalTransform = Transform3D.Identity;
        if (FxAfter.On) FxAfter.Adopt(n);
        var t = new P7Trail { N = n, Mesh = mesh, M = m, Source = src, Width = width, Until = until, Life = life };
        p7Trails.Add(t);
        return t;
    }

    /// <summary>A swept blade trail: the strip between two points sampled each frame (the blade's base and tip).</summary>
    P7Trail P7NewTrail(Func<(Vector3 A, Vector3 B)> sweep, float until, float life)
    {
        var t = P7NewTrail(() => sweep().A, 0, until, life);
        t.Sweep = sweep;
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
                // a soft pool: a low attenuation exponent so it falls off smoothly to its range, never a disc
                var o = new OmniLight3D { ShadowEnabled = false, OmniAttenuation = 0.7f, Visible = false };
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
            // the ring: light on the ground, ~8 px wide at the play camera, its outer edge the hit radius (marked = hit). Its
            // gaps close in three steps over the air time (coverage 0.6 -> 1.0); shut, it flashes a sample (a wide core),
            // then it is gone in two steps after the landing.
            run.Ring = P7Quad(0, V(x1, Y(x1, z1) + 0.04, z1), (float)r, (float)e.Dur + 3 * P7Sample, step: s =>
            {
                float dur = (float)run.Dur;
                int st = Mathf.Clamp((int)(s.Age / (dur / 3f)), 0, 3);
                s.M.SetShaderParameter("p7_prog", st >= 3 ? 1f : st / 3f);
                s.M.SetShaderParameter("p7_alpha", st >= 3 ? 1f : 0.6f + 0.4f * st / 3f);
                s.M.SetShaderParameter("p7_width", Mathf.Clamp(4f * P7Px(s.N.GlobalPosition) / (float)run.R, 0.004f, 0.2f));
                float after = s.Age - dur;
                int k = after < 0 ? -1 : (int)(after / P7Sample);
                s.M.SetShaderParameter("p7_sw", k == 0 ? new Vector4(0.55f, 0.8f, 0.3f, 0.75f) : new Vector4(0.3f, 0.62f, 0.35f, 0.75f));
                s.M.SetShaderParameter("p7_fade", k <= 0 ? 0f : k == 1 ? 0.4f : 0.8f);
            });
            run.Ring.M.SetShaderParameter("p7_sw", new Vector4(0.3f, 0.62f, 0.35f, 0.75f));
            // the ribbon: the blade's upper half swept through the air, smoothed, tapering from the blade to nothing
            run.Ribbon = P7NewTrail(() => (P7BladeAt(0.6f), P7BladeAt(0.98f)), (float)e.Dur, 2.5f * P7Sample);
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

    /// <summary>The landing (and, smaller, Pile Driver's slam): ONE bold star flat on the ground under her feet (6-8
    /// tapered spikes of varied length round a solid white-gold heart, ~12 streaks running out; drawn on the ground, so
    /// her depth twin hides it where she stands over it), a sample at its peak then stepping down; 3-4 tapering, forking
    /// cracks (matter, their hearts cooling in steps); a clustered two-value dust ring out to the hit radius; chunks;
    /// the gold pool.</summary>
    void P7Slam(double x, double z, float r, float k)
    {
        var c = V(x, Y(x, z), z);
        var star = P7Quad(1, c + Vector3.Up * 0.05f, r * 1.2f * k, 4 * P7Sample, step: s => s.M.SetShaderParameter("p7_t", s.Age));
        star.M.SetShaderParameter("p7_spikes", (float)(6 + (int)(R() * 2.99f)));
        P7LightOn(c + Vector3.Up * (1.2f + 0.3f * r), r * 1.7f, (Flare.Night ? 4.2f : 6f) * k);
        float a0 = R() * Mathf.Tau;
        int cracks = k >= 1 ? 3 + (int)(R() * 1.99f) : 3;
        Color[] steps = [P7Band(2).SrgbToLinear(), P7Band(1).SrgbToLinear(), P7Band(0).SrgbToLinear()];
        float day = Flare.Night ? 1f : 1.7f;
        for (int i = 0; i < cracks && wgAlb != null; i++)
        {
            float a = a0 + (i + (R() - 0.5f) * 0.6f) / cracks * Mathf.Tau;
            float len = r * (0.5f + R() * 0.55f) * k;
            int t0 = 8 + (int)(R() * 1.99f);
            var from = new Vector2((float)x, (float)z) + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * 0.1f;
            // the main split: three segments narrowing to its tip, bending a little at each joint
            var end1 = P7CrackRun(from, a, len, 3, [1f, 0.68f, 0.4f], t0, k, steps, day, out float aEnd, out var mid);
            // a fork off its middle on most of them, narrower and shorter, angled away
            if (R() < 0.8f)
            {
                float side = R() < 0.5f ? -1 : 1;
                P7CrackRun(mid, aEnd + side * (0.45f + R() * 0.35f), len * (0.3f + R() * 0.2f), 2, [0.48f, 0.28f], t0 + 1, k, steps, day, out _, out _);
            }
        }
        P7DustRing(c, r * k, k >= 1 ? 6 + (int)(R() * 2.99f) : 5, 0.85f + 0.15f * k);
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

    /// <summary>One crack run: `n` decal segments from `from` heading `a` (radians on the ground), `len` long, each
    /// `widths[j]` of the strip's width (tapering), its heart glowing core -> mid -> edge as it cools. Returns its end;
    /// `aEnd` its last heading, `mid` its first joint (where a fork may leave).</summary>
    Vector2 P7CrackRun(Vector2 from, float a, float len, int n, float[] widths, int tex, float k, Color[] steps, float day, out float aEnd, out Vector2 mid)
    {
        float seg = len / n;
        var p = from;
        mid = from;
        for (int j = 0; j < n; j++)
        {
            var dir = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
            var cc = p + dir * seg * 0.5f;
            var pos = V(cc.X, Y(cc.X, cc.Y), cc.Y);
            float theta = Mathf.Atan2(-dir.Y, dir.X);
            int t = Math.Min(11, tex + j);
            var size = new Vector3(seg * 1.06f, 1.6f, WgBand * 0.9f * k * widths[j]);
            WgDecalOn(pos, theta, size, wgAlb![t], wgNrm![t], null, 3.2f, 1f, 0, 0);
            var hd = WgDecalOn(pos, theta, size, null, null, wgEmi![t], 1.5f, 1f, 1.6f * day * (0.6f + 0.4f * widths[j]), 0, 0, steps[0]);
            if (hd != null) { hd.Steps = steps; hd.StepAt = [0.12f, 0.5f, 1.0f]; hd.StepE = [1.0f, 0.85f, 0.7f]; }
            p += dir * seg;
            if (j == 0) mid = p;
            a += (R() - 0.5f) * 0.5f;
        }
        aEnd = a;
        return p;
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
                // the press: a glint off the shield and a real kick of dust back from her heels and out to the sides
                P7Glint(P7ShieldAt(), 0.8f);
                var sideAx = new Vector3(dir.Z, 0, -dir.X);
                for (int q = 0; q < 4; q++)
                {
                    var lean = (-dir * 1.0f + sideAx * ((q % 2 == 0 ? 1 : -1) * (0.5f + R() * 0.8f))).Normalized();
                    int n = 3 + (int)(R() * 2.99f);
                    for (int i = 0; i < n; i++)
                    {
                        float sz = 0.18f + R() * R() * 0.32f;
                        var v = lean * (2.0f + R() * 2.2f) + Vector3.Up * (0.35f + R() * 0.6f);
                        WgPuff(feet - dir * 0.2f + Vector3.Up * 0.2f, v, sz, 1.6f, 0.5f + R() * 0.3f, WgDust(1.06f + R() * 0.1f), 0.8f, 3.8f);
                        WgPuff(feet - dir * 0.15f + Vector3.Up * 0.08f, v * 0.8f - Vector3.Up * 0.2f, sz * 1.25f, 1.5f, 0.6f + R() * 0.3f, WgDust(0.68f), 0.76f, 4f);
                    }
                }
                p7ChargeT = 0; p7ChargeDur = (float)e.Dur; p7ChargeDir = dir; p7ChargeHit = false;
                p7GhostDue.Clear();
                p7GhostNext = 0.03f; p7PlowNext = 0.04f;
                if (p7ChargeTrail != null) p7ChargeTrail.Until = 0;
                p7ChargeTrail = P7NewTrail(() => PlayerPos + Vector3.Up * 0.95f - p7ChargeDir * 0.25f, 0.2f, p7ChargeDur + 0.05f, 2.5f * P7Sample);
                // the crescent of light on the shield's face, its middle toward where she drives
                if (p7Crescent != null && IsInstanceValid(p7Crescent.N)) p7Crescent.Age = p7Crescent.Life;
                float dur = p7ChargeDur;
                p7Crescent = P7Quad(12, P7ShieldAt(), 0.62f, dur + 3 * P7Sample, bill: true, top: true, step: s =>
                {
                    var sh = P7ShieldAt();
                    s.N.GlobalPosition = sh;
                    if (GetViewport()?.GetCamera3D() is { } cam && !cam.IsPositionBehind(sh))
                    {
                        var d2 = cam.UnprojectPosition(sh + p7ChargeDir) - cam.UnprojectPosition(sh);
                        if (d2.LengthSquared() > 1e-4f) s.M.SetShaderParameter("p7_dir2", d2.Normalized());
                    }
                    float after = s.Age - dur;
                    s.M.SetShaderParameter("p7_fade", after <= 0 ? 0f : Mathf.Min(0.9f, Mathf.Floor(after / P7Sample + 1) * 0.34f));
                });
                break;
            }
            case ChargePhase.Impact:
            {
                P7Ev("charge_impact");
                var at = P7Body(e.Target, e.X, e.Z, b);
                bool first = !p7ChargeHit;
                p7ChargeHit = true;
                // a hit (§4): one bold 4-6 spike star at the contact; the first gets the pool and the hitstop
                var st = P7Quad(1, at - dir * 0.15f, first ? 1.15f : 0.9f, 4 * P7Sample, bill: true, top: true, step: s => s.M.SetShaderParameter("p7_t", s.Age));
                st.M.SetShaderParameter("p7_spikes", (float)(4 + (int)(R() * 2.99f)));
                if (first) P7LightOn(at + Vector3.Up * 0.4f, 3.2f, Flare.Night ? 2.2f : 3f);
                // the foe's feet throw a little lit dust aside
                var ff = new Vector3(at.X, Y(at.X, at.Z), at.Z);
                P7DustRing(ff, 0.9f, 2, 0.7f, 0.2f);
                break;
            }
            case ChargePhase.Stop:
            {
                P7Ev("charge_stop");
                var at = P7Body(e.Target, e.X, e.Z, b);
                // the champion stops her: the big star, a pool, a punch of the view along the line (out 90 ms, back), a
                // ring of light off the shield thinning to nothing, dust at their feet
                var st = P7Quad(1, at - dir * 0.3f, 1.6f, 4 * P7Sample, bill: true, top: true, step: s => s.M.SetShaderParameter("p7_t", s.Age));
                st.M.SetShaderParameter("p7_spikes", 6f);
                P7LightOn(at + Vector3.Up * 0.5f, 4.5f, Flare.Night ? 3.4f : 4.5f);
                Cam?.Kick(dir, 0.22f);
                var sh = P7ShieldAt();
                P7Quad(5, sh, 1.5f, 0.2f + P7Sample, bill: true, top: true, step: s =>
                {
                    s.M.SetShaderParameter("p7_prog", Mathf.Clamp(s.Age / 0.2f, 0, 1));
                    s.M.SetShaderParameter("p7_width", 0.09f);
                    s.M.SetShaderParameter("p7_alpha", 1f - Mathf.Floor(s.Age / 0.05f) * 0.22f);
                });
                var feet = V(e.X, Y(e.X, e.Z), e.Z);
                P7DustRing(feet + dir * 0.4f, 1.6f, 4, 0.9f, 0.25f);
                p7GhostDue.Clear();
                p7GhostNext = -1;
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
                p7GhostNext = -1;
                break;
        }
    }

    /// <summary>The Warden's dash (FX_LANGUAGE §4, a body moving): an edge-band ribbon off her hips that tapers to nothing
    /// in 2.5 samples, two mid-band afterimages stepping out, dust at her heels. Her figure runs the blink over ~0.2 s, so
    /// the ribbon follows the figure, never drawn ahead of it. False: not hers (another calling's dash keeps its look).</summary>
    bool P7Dash(Ev.Dash e, Battle b)
    {
        if (P7Off || !string.Equals(b.Calling, "warden", StringComparison.OrdinalIgnoreCase) || p7ChargeT >= 0) return false;
        P7WarmUp();
        var dir = new Vector3((float)(e.X1 - e.X0), 0, (float)(e.Z1 - e.Z0));
        dir = dir.LengthSquared() > 1e-4f ? dir.Normalized() : Vector3.Forward;
        var feet = V(e.X0, Y(e.X0, e.Z0), e.Z0);
        // the press: a glint on her blade and a kick of dust back from her heels (two values, in knots)
        P7Glint(P7BladeAt(1), 0.6f);
        var sideAx = new Vector3(dir.Z, 0, -dir.X);
        for (int q = 0; q < 3; q++)
        {
            var lean = (-dir + sideAx * ((R() - 0.5f) * 1.6f)).Normalized();
            int n = 2 + (int)(R() * 2.99f);
            for (int i = 0; i < n; i++)
            {
                float sz = 0.16f + R() * R() * 0.26f;
                var v = lean * (1.6f + R() * 1.8f) + Vector3.Up * (0.25f + R() * 0.45f);
                WgPuff(feet + Vector3.Up * 0.18f, v, sz, 1.5f, 0.45f + R() * 0.25f, WgDust(1.06f + R() * 0.1f), 0.8f, 3.8f);
                WgPuff(feet + Vector3.Up * 0.07f, v * 0.8f, sz * 1.25f, 1.4f, 0.55f + R() * 0.25f, WgDust(0.68f), 0.76f, 4f);
            }
        }
        // the wedge: a ribbon off her hips (three bands, tapering to nothing, gone in 2.5 samples)
        P7NewTrail(() => PlayerPos + Vector3.Up * 0.95f, 0.24f, 0.24f, 2.5f * P7Sample);
        p7ChargeT = 0; p7ChargeDur = 0.0f; p7ChargeDir = dir;
        p7GhostDue.Clear();
        p7GhostNext = -1;
        // three rim-only afterimages, 0.04 s apart
        p7GhostDue.AddRange([0.03f, 0.07f, 0.11f]);
        return true;
    }

    /// <summary>Hard Landing: a ring of light running out at her feet to the shove's radius (bold and hot at first,
    /// thinning to nothing as it reaches it, its coverage 1 -> 0 over 0.2 s) and the dust it pushes outward.</summary>
    void P7Shove(Ev.HardLanding e)
    {
        if (P7Off) return;
        P7WarmUp();
        P7Ev("hard_landing");
        float r = (float)e.Radius;
        var c = V(e.X, Y(e.X, e.Z), e.Z);
        P7Quad(5, c + Vector3.Up * 0.06f, r, 0.2f, step: s =>
        {
            s.M.SetShaderParameter("p7_prog", Mathf.Clamp(s.Age / 0.2f, 0, 1));
            s.M.SetShaderParameter("p7_width", Mathf.Clamp(7f * P7Px(s.N.GlobalPosition) / r, 0.01f, 0.25f));
            s.M.SetShaderParameter("p7_alpha", 1f - Mathf.Floor(s.Age / 0.05f) * 0.25f);
        });
        P7DustRing(c, r, 6, 0.85f, 0.3f);
    }

    /* ----------------------------------------------------------- pieces -- */

    /// <summary>The press: a four-point glint in the core color for three frames (§4).</summary>
    void P7Glint(Vector3 at, float size) =>
        P7Quad(4, at, size, 3 / 60f, bill: true, top: true, step: s =>
        {
            int f = (int)(s.Age * 60);
            s.M.SetShaderParameter("p7_fade", f <= 0 ? 0f : f == 1 ? 0.2f : 0.4f);
        });

    Vector3 P7BladeAt(float k)
    {
        if (Flare.Blade is { } bl && IsInstanceValid(bl) && bl.IsInsideTree())
        {
            float tip = bl.HasMeta("tip") ? (float)bl.GetMeta("tip") : 1.4f;
            var at = bl.GlobalTransform * new Vector3(0, Mathf.Lerp(0.25f, tip, k), 0);
            // (a blade between hands for a frame, its transform not hers yet: never draw a glint metres off her)
            if (k < 1 || at.DistanceTo(PlayerPos + Vector3.Up * 1.0f) < 2.6f) return at; // (the ribbon follows the blade into the air)
            if (Args.Has("clip")) GD.Print($"p7 blade far: {at} her {PlayerPos} frame {Engine.GetFramesDrawn()}");
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
    /// <summary>A copy of her pose now (each skinned mesh on a frozen copy of its skeleton) in a P7 mode: the charge's
    /// afterimage (3), the vow's pulse (11); `init` sets its uniforms.</summary>
    void P7Snap(int mode = 3, float life = 0.15f, Action<P7Ghost>? init = null)
    {
        if (Her3D == null || !IsInstanceValid(Her3D)) return;
        var m = P7Mat(mode, ghost: true);
        m.SetShaderParameter("p7_alpha", 0.9f);
        m.SetShaderParameter("p7_life", life);
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
        var g = new P7Ghost { Root = root, M = m, Life = life };
        init?.Invoke(g);
        p7Ghosts.Add(g);
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
            // the charge: a rim ghost every 0.04 s (three alive at once), dust plowed to both sides of her path
            if (p7ChargeDur > 0 && p7ChargeT <= p7ChargeDur)
            {
                if (p7GhostNext >= 0 && p7ChargeT >= p7GhostNext) { p7GhostNext += 0.04f; P7Snap(); }
                if (p7PlowNext >= 0 && p7ChargeT >= p7PlowNext)
                {
                    p7PlowNext += 0.05f;
                    var feet = new Vector3(PlayerPos.X, Y(PlayerPos.X, PlayerPos.Z), PlayerPos.Z);
                    var side = new Vector3(p7ChargeDir.Z, 0, -p7ChargeDir.X);
                    for (int sgn = -1; sgn <= 1; sgn += 2)
                    {
                        float sz = 0.16f + R() * R() * 0.28f;
                        var v = side * sgn * (1.8f + R() * 1.4f) - p7ChargeDir * (0.3f + R() * 0.5f) + Vector3.Up * (0.3f + R() * 0.45f);
                        var at = feet + side * sgn * 0.3f + p7ChargeDir * 0.2f;
                        WgPuff(at + Vector3.Up * 0.2f, v, sz, 1.6f, 0.45f + R() * 0.25f, WgDust(1.06f + R() * 0.1f), 0.8f, 4f);
                        WgPuff(at + Vector3.Up * 0.08f, v * 0.75f, sz * 1.3f, 1.4f, 0.55f + R() * 0.25f, WgDust(0.68f), 0.76f, 4.4f);
                    }
                }
            }
            if (p7ChargeT > p7ChargeDur + 0.5f) p7ChargeT = -1;
        }
        var cam = GetViewport()?.GetCamera3D();
        for (int i = p7Trails.Count - 1; i >= 0; i--)
        {
            var t = p7Trails[i];
            t.Age += dt;
            for (int k = 0; k < t.Pts.Count; k++) t.Pts[k] = (t.Pts[k].P, t.Pts[k].Age + dt);
            while (t.Pts.Count > 0 && t.Pts[0].Age > t.Life) { t.Pts.RemoveAt(0); if (t.Pts2.Count > 0) t.Pts2.RemoveAt(0); }
            if (t.Age <= t.Until && dt > 0)
            {
                if (t.Sweep != null)
                {
                    var (pa, pb) = t.Sweep();
                    if (t.Pts.Count == 0 || t.Pts[^1].P.DistanceSquaredTo(pa) > 0.0004f || t.Pts2[^1].DistanceSquaredTo(pb) > 0.0004f) { t.Pts.Add((pa, 0)); t.Pts2.Add(pb); }
                }
                else if (t.Source != null)
                {
                    var p = t.Source();
                    if (t.Pts.Count == 0 || t.Pts[^1].P.DistanceSquaredTo(p) > 0.0004f) t.Pts.Add((p, 0));
                }
            }
            if (t.Age > t.Until && t.Pts.Count == 0) { t.N.QueueFree(); p7Trails.RemoveAt(i); continue; }
            P7BuildTrail(t, cam);
        }
    }

    static Vector3 P7Cr(Vector3 p0, Vector3 p1, Vector3 p2, Vector3 p3, float u) =>
        0.5f * (2 * p1 + (p2 - p0) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (3 * p1 - p0 - 3 * p2 + p3) * u * u * u);

    /// <summary>The ribbon mesh: the sampled path smoothed (Catmull-Rom, 4 steps a span: no kinks), a strip whose UV.x is
    /// its age along it (1 the head, now; 0 the tail, Life old) and UV.y 0..1 across; the stroke tapers it to nothing at
    /// the tail and gives it its bands. A body's ribbon faces the camera (`Width` its half-width); a blade's sweep spans
    /// the blade. After `Until` its life steps it out (p7_fade).</summary>
    void P7BuildTrail(P7Trail t, Camera3D? cam)
    {
        t.Mesh.ClearSurfaces();
        int n = t.Pts.Count;
        if (n < 2 || cam == null) return;
        bool sweep = t.Sweep != null && t.Pts2.Count == n;
        var eye = cam.GlobalPosition;
        float after = t.Age - t.Until;
        t.M.SetShaderParameter("p7_fade", after <= 0 ? 0f : Mathf.Min(0.95f, Mathf.Floor(after / P7Sample + 1) * 0.34f));
        const int Sub = 4;
        var pa = new List<Vector3>(); var pb = new List<Vector3>(); var ag = new List<float>();
        for (int i = 0; i < n - 1; i++)
            for (int j = 0; j < Sub; j++)
            {
                float u = j / (float)Sub;
                int i0 = Math.Max(0, i - 1), i3 = Math.Min(n - 1, i + 2);
                pa.Add(P7Cr(t.Pts[i0].P, t.Pts[i].P, t.Pts[i + 1].P, t.Pts[i3].P, u));
                if (sweep) pb.Add(P7Cr(t.Pts2[i0], t.Pts2[i], t.Pts2[i + 1], t.Pts2[i3], u));
                ag.Add(Mathf.Lerp(t.Pts[i].Age, t.Pts[i + 1].Age, u));
            }
        pa.Add(t.Pts[n - 1].P); if (sweep) pb.Add(t.Pts2[n - 1]); ag.Add(t.Pts[n - 1].Age);
        int m = pa.Count;
        t.Mesh.SurfaceBegin(Mesh.PrimitiveType.TriangleStrip);
        for (int i = 0; i < m; i++)
        {
            float along = Mathf.Clamp(1 - ag[i] / t.Life, 0, 1);
            Vector3 a, b;
            if (sweep) { a = pa[i]; b = pb[i]; }
            else
            {
                var p = pa[i];
                var d = i < m - 1 ? pa[i + 1] - p : p - pa[i - 1];
                if (d.LengthSquared() < 1e-6f) d = Vector3.Forward;
                var side = d.Cross(eye - p).Normalized();
                a = p - side * t.Width; b = p + side * t.Width;
            }
            t.Mesh.SurfaceSetUV(new Vector2(along, 0));
            t.Mesh.SurfaceAddVertex(a);
            t.Mesh.SurfaceSetUV(new Vector2(along, 1));
            t.Mesh.SurfaceAddVertex(b);
        }
        t.Mesh.SurfaceEnd();
        t.N.MaterialOverride = t.M;
    }
}

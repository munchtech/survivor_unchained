using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Look;
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
        public float Age = 9, Peak, Hold = 1 / 12f, Down = 2 / 12f;
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
    static FxP7? p7d;
    /// <summary>The judge's numbers (data/look/fx_language.json "p7", logic/Look/FxP7.cs): px at the play camera, counts, timings.</summary>
    static FxP7 P7D => p7d ??= FxP7.Parse(Godot.FileAccess.GetFileAsString("res://data/look/fx_language.json"));
    // chunks painted earth-brown for their flight (P7Throw), let go when they land
    static StandardMaterial3D? p7Earth;
    readonly List<WgRock> p7Thrown = new();
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
        P7Brush(m, 12);
        return m;
    }

    /// <summary>The brush, per instance (L1's fx_stroke): its own bristles (a fresh fx_stroke_seed) and about one bristle
    /// per 3 px of the stroke's FULL width at the play camera (`widthPx`: across -1..1 on screen), so a thin ring gets a
    /// few bristles and a wide smear many; never finer than a pixel (it would shimmer). Streak length, dryness and waver
    /// stay at L1's defaults.</summary>
    void P7Brush(ShaderMaterial m, float widthPx, float tail = 0.12f)
    {
        m.SetShaderParameter("fx_stroke_seed", R() * 97f);
        m.SetShaderParameter("fx_bristle", new Vector4(Mathf.Clamp(widthPx / 3f, 1f, 24f), 12f, 0.55f, 0.2f));
        if (tail != 0.12f) m.SetShaderParameter("fx_stroke_shape", new Vector4(0.72f, 0.3f, tail, 0.08f));
    }

    /// <summary>A quad mode's main stroke half-width as a share of the quad's half-size (0: the caller sizes it). The
    /// star's spikes are 0.1 and its streaks 0.02 in one material: brushed for 0.045 between them (spikes ~5 px a
    /// bristle, streaks ~1).</summary>
    static float P7ModeHw(int mode) => mode switch { 9 => 1f, 12 => 0.2f, _ => 0f };

    /// <summary>A quad shape: flat on the ground (half-size `half`, at `at`) or facing the camera (`bill`).</summary>
    P7Shape P7Quad(int mode, Vector3 at, float half, float life, bool bill = false, bool top = false, Action<P7Shape>? step = null)
    {
        p7Plane ??= new PlaneMesh { Size = new Vector2(2, 2) };
        p7Quad ??= new QuadMesh { Size = new Vector2(2, 2) };
        var m = P7Mat(mode, top);
        if (P7ModeHw(mode) > 0) P7Brush(m, 2 * P7ModeHw(mode) * half / P7Px(at));
        if (bill) m.SetShaderParameter("p7_bill", 1f);
        var n = new MeshInstance3D { Mesh = bill ? p7Quad : p7Plane, MaterialOverride = m, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
        n.Scale = Vector3.One * half;
        AddChild(n);
        n.GlobalPosition = at;
        if (Args.Has("clip") && (GetViewport()?.GetCamera3D() is { } c3) && !c3.IsPositionBehind(at))
        {
            // (for the px self-check: where it lands on screen and its half-size in px at the play camera)
            var sp = c3.UnprojectPosition(at) * (1080f / Math.Max(1f, GetViewport().GetVisibleRect().Size.Y));
            GD.Print($"p7px mode {mode} screen {sp.X:F0},{sp.Y:F0} half {half / P7Px(at):F1}px frame {Engine.GetFramesDrawn()}");
        }
        if (FxAfter.On) FxAfter.Adopt(n);
        var s = new P7Shape { N = n, M = m, Life = life, Step = step };
        p7Shapes.Add(s);
        return s;
    }

    P7Trail P7NewTrail(Func<Vector3> src, float width, float until, float life)
    {
        var mesh = new ImmediateMesh();
        var m = P7Mat(2);
        // a ribbon tapers to a point (fx_stroke's tail width 0.12 -> 0, round 3: no square tail); a
        // body's ribbon is 2 x `width` across, a blade's sweep about 0.4 m (0.6..0.98 of the blade)
        P7Brush(m, (width > 0 ? 2 * width : 0.4f) / P7Px(src()), 0.001f);
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

    void P7LightOn(Vector3 at, float range, float peak, float hold = P7Sample, float down = 2 * P7Sample)
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
        l.Age = 0; l.Peak = peak; l.Hold = hold; l.Down = down;
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
            // the press: one glint on the blade's tip and a kick of dust from her heels
            P7Press(P7BladeAt(1), from, dir);
            double r = e.Radius, x1 = e.X1, z1 = e.Z1;
            var run = new P7LeapRun { X0 = e.X0, Z0 = e.Z0, X1 = x1, Z1 = z1, Dur = e.Dur, R = r };
            // the target: a wavefront standing at the hit radius (marked = hit), its arcs growing to the data's coverage
            // curve with their opacity; shut, one flash at 1.5x its width (the core hot); gone in two steps at the landing
            var c = V(x1, Y(x1, z1) + 0.04, z1);
            float rpx = (float)r / P7Px(c);
            float lead = P7D["leap.ring.lead_px"] / rpx, trail = P7D["leap.ring.trail_px"] / rpx;
            int flashN = (int)P7D["leap.ring.flash_frames"];
            float flashK = P7D["leap.ring.flash_k"];
            float shutAt = -1;
            run.Ring = P7Quad(0, c, (float)r, (float)e.Dur + 3 * P7Sample, step: s =>
            {
                float cover = P7D.Curve("leap.ring.cover", s.Age);
                if (cover >= 0.999f && shutAt < 0) shutAt = s.Age;
                bool flash = shutAt >= 0 && s.Age - shutAt < flashN / 60f - 1e-4f;
                s.M.SetShaderParameter("p7_shrink", cover);
                s.M.SetShaderParameter("p7_alpha", P7D.Range("leap.ring.alpha", cover));
                s.M.SetShaderParameter("p7_lead", lead * (flash ? flashK : 1));
                s.M.SetShaderParameter("p7_trw", trail);
                float after = s.Age - (float)run.Dur;
                int k = after < 0 ? -1 : (int)(after / P7Sample);
                s.M.SetShaderParameter("p7_fade", k < 0 ? 0f : k == 0 ? 0.34f : 0.67f);
            });
            run.Ring.M.SetShaderParameter("p7_shrink", 0f);
            P7Arcs(run.Ring.M, R() * Mathf.Tau, Mathf.Tau, (int)P7D["leap.ring.arcs"], 1, 1.08f, 1.12f, 0.15f);
            P7BrushWave(run.Ring.M, rpx, P7D["leap.ring.lead_px"]);
            // the ribbon: her blade's way through the air (her chest plus the data's share of the blade's own swing: the
            // stand-in's blade loops), splined, its head the data's px tapering to a point
            float hw = 0.5f * P7D["leap.ribbon.head_px"] * P7Px(from);
            run.Ribbon = P7NewTrail(() => (PlayerPos + Vector3.Up * 1.1f).Lerp(P7BladeAt(0.92f), P7D["leap.ribbon.blade"]), hw, (float)e.Dur, P7D["leap.ribbon.life"]);
            p7Leap = run;
            return;
        }
        // Land
        P7Ev("leap_land");
        if (p7Leap?.Ribbon is { } rb) rb.Until = 0;
        if (p7Leap?.Ring is { } rg) rg.Life = Math.Min(rg.Life, rg.Age + 1 / 60f);
        p7Leap = null;
        if (p7Shadow != null) p7Shadow.Visible = false;
        P7Slam(e.X1, e.Z1, (float)e.Radius, 1f);
        Cam?.JoltPx(Vector3.Up, 10f);
    }

    /// <summary>A star's life by frames: full for `hold` frames, then the core, the gold and the amber step out every `step`.</summary>
    static float P7StarLife(float age, int hold, int step)
    {
        int f = (int)(age * 60 + 1e-3f);
        return f < hold ? 0f : f < hold + step ? 0.34f : f < hold + 2 * step ? 0.67f : 1f;
    }

    /// <summary>A star (modes 1 and 17 are one shape): `spikes` tapered spikes `px` across at the play camera, their roots
    /// `rootPx` wide; `streaks` thin streaks running out; full `hold` frames, then a band off every `step` frames.</summary>
    P7Shape P7StarPx(Vector3 at, float px, int spikes, float rootPx, int streaks, int hold, int step, bool bill, float tail = 0.12f)
    {
        float half = 0.5f * px * P7Px(at);
        var s = P7Quad(1, at, half, (hold + 3 * step) / 60f, bill: bill, top: bill, step: q =>
        {
            q.M.SetShaderParameter("p7_t", q.Age);
            q.M.SetShaderParameter("p7_fade", P7StarLife(q.Age, hold, step));
        });
        s.M.SetShaderParameter("p7_count", (float)spikes);
        s.M.SetShaderParameter("p7_streaks", (float)streaks);
        s.M.SetShaderParameter("p7_root", 0.5f * rootPx / (0.5f * px));
        s.M.SetShaderParameter("p7_heart", 0.5f * rootPx / (0.5f * px) * 0.8f);
        P7Brush(s.M, rootPx, tail);
        return s;
    }

    /// <summary>The landing (and, smaller, Pile Driver's slam): ONE star flat on the ground under her feet (the data's
    /// spikes, roots and streaks, full two frames then stepping out), tapering cracks with a dark gap and a lit lip
    /// cooling gold, amber, off over 0.6 s; two-value dust out to the hit radius in 0.4 s; earth-brown chunks; the pool.</summary>
    void P7Slam(double x, double z, float r, float k)
    {
        var c = V(x, Y(x, z), z);
        float pxm = P7Px(c);
        P7StarPx(c + Vector3.Up * 0.05f, 2 * r * P7D["leap.star.reach"] * k / pxm, P7D.Count("leap.star.spikes", R()), P7D["leap.star.root_px"] * (0.8f + 0.2f * k),
            P7D.Count("leap.star.streaks", R()), (int)P7D["leap.star.hold_frames"], (int)P7D["leap.star.step_frames"], false);
        P7LightOn(c + Vector3.Up * (1.2f + 0.3f * r), r * 1.7f, (Flare.Night ? 4.2f : 6f) * k);
        float a0 = R() * Mathf.Tau;
        int cracks = k >= 1 ? 3 + (int)(R() * 1.99f) : 3;
        Color[] steps = [P7Band(2).SrgbToLinear(), P7Band(1).SrgbToLinear(), P7Band(0).SrgbToLinear()];
        float day = Flare.Night ? 1f : 1.7f;
        float w0 = P7D["leap.crack.root_px"], w1 = P7D["leap.crack.tip_px"];
        for (int i = 0; i < cracks && wgAlb != null; i++)
        {
            float a = a0 + (i + (R() - 0.5f) * 0.6f) / cracks * Mathf.Tau;
            float len = r * (0.5f + R() * 0.55f) * k;
            int t0 = 8 + (int)(R() * 1.99f);
            var from = new Vector2((float)x, (float)z) + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * 0.1f;
            // the main split: three segments narrowing root -> tip, bending a little at each joint
            var end1 = P7CrackRun(from, a, len, 3, [w0, Mathf.Lerp(w0, w1, 0.5f), w1 * 1.2f], t0, pxm, steps, day, out float aEnd, out var mid);
            // a fork off its middle on most of them, narrower and shorter, angled away
            if (R() < 0.8f)
            {
                float side = R() < 0.5f ? -1 : 1;
                P7CrackRun(mid, aEnd + side * (0.45f + R() * 0.35f), len * (0.3f + R() * 0.2f), 2, [Mathf.Lerp(w0, w1, 0.55f), w1], t0 + 1, pxm, steps, day, out _, out _);
            }
        }
        var dpx = P7D.All("leap.dust.px");
        P7Dust(c, r * k, (int)(P7D.Count("leap.dust.puffs", R()) * (k >= 1 ? 1 : 0.6f)), dpx[0], dpx[1], P7D["leap.dust.run"], 0.3f);
        int chunks = (int)(P7D.Count("leap.chunks", R()) * (k >= 1 ? 1 : 0.55f));
        for (int i = 0; i < chunks; i++)
        {
            float a = R() * Mathf.Tau, d = r * 0.45f * Mathf.Sqrt(R());
            var o = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            double px = x + o.X * d, pz = z + o.Z * d;
            var v = o * (1.2f + R() * 2.2f) + Vector3.Up * (2.6f + R() * 2.4f) * (0.75f + 0.25f * k);
            P7Throw(V(px, Y(px, pz) + 0.2, pz), v, (0.6f + R() * 0.35f) * (0.8f + 0.2f * k), 1.6f + R() * 0.5f);
        }
    }

    /// <summary>One crack run: `n` decal segments of the Warden's crack strip from `from` heading `a` (radians on the
    /// ground), `len` long, each `px[j]` px wide at its dark gap (the strip's gap is the data's share of its band), its
    /// projector 0.5 m deep (never up into foliage); its light a seam strip down the gap's own centre (P7Seam). Returns its
    /// end; `aEnd` its last heading, `mid` its first joint (where a fork may leave).</summary>
    Vector2 P7CrackRun(Vector2 from, float a, float len, int n, float[] px, int tex, float pxm, Color[] steps, float day, out float aEnd, out Vector2 mid)
    {
        float seg = len / n, gap = P7D["leap.crack.gap"];
        var p = from;
        mid = from;
        var seam = new List<Vector3>();
        var seamW = new List<float>();
        var sp = P7D.All("leap.crack.seam_px");
        for (int j = 0; j < n; j++)
        {
            var dir = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
            var cc = p + dir * seg * 0.5f;
            var pos = V(cc.X, Y(cc.X, cc.Y), cc.Y);
            float theta = Mathf.Atan2(-dir.Y, dir.X);
            int t = Math.Min(11, tex + j);
            float w = px[j] * pxm / gap;
            WgDecalOn(pos, theta, new Vector3(seg * 1.06f, 0.5f, w), wgAlb![t], wgNrm![t], null, 3.2f, 1f, 0, 0);
            var side = new Vector2(-dir.Y, dir.X);
            for (int q = 0; q < 6; q++)
            {
                if (j > 0 && q == 0) continue;
                float u = q / 5f;
                seam.Add(P7CrackAt(p, dir, side, seg * u, seg, t, 1, w / WgBand) + Vector3.Up * 0.03f);
                seamW.Add(Mathf.Lerp(sp[0], sp[1], (j + u) / n) * pxm * 0.5f);
            }
            p += dir * seg;
            if (j == 0) mid = p;
            a += (R() - 0.5f) * 0.5f;
        }
        P7Seam(seam, seamW, P7D["leap.crack.cool"]);
        aEnd = a;
        return p;
    }

    /// <summary>A crack's light: a seam strip (mode 7) down `pts` (half-widths `hw`), hot at its root, cooling core, gold,
    /// amber, off over `cool` s.</summary>
    void P7Seam(List<Vector3> pts, List<float> hw, float cool)
    {
        if (pts.Count < 2) return;
        var mesh = new ImmediateMesh();
        mesh.SurfaceBegin(Mesh.PrimitiveType.TriangleStrip);
        for (int i = 0; i < pts.Count; i++)
        {
            var d = i < pts.Count - 1 ? pts[i + 1] - pts[i] : pts[i] - pts[i - 1];
            var sd = new Vector3(-d.Z, 0, d.X).Normalized() * hw[i];
            float u = i / (float)(pts.Count - 1);
            mesh.SurfaceSetUV(new Vector2(u, 0)); mesh.SurfaceAddVertex(pts[i] - sd);
            mesh.SurfaceSetUV(new Vector2(u, 1)); mesh.SurfaceAddVertex(pts[i] + sd);
        }
        mesh.SurfaceEnd();
        var s = P7OnMesh(7, mesh, Vector3.Zero, Vector3.One, cool, q =>
            q.M.SetShaderParameter("p7_fade", q.Age < cool / 6 ? 0f : q.Age < cool / 2 ? 0.34f : 0.67f));
        s.N.GlobalTransform = Transform3D.Identity;
        P7Brush(s.M, 2 * hw[0] / P7Px(pts[0]));
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
                // the press: the crescent flash on the shield (3 frames), its middle toward where she drives, and the kick
                var sh0 = P7ShieldAt();
                float cpx = P7D["charge.crescent.px"];
                int cfr = (int)P7D["charge.crescent.frames"];
                var cr = P7Quad(12, sh0, 0.5f * cpx * P7Px(sh0), cfr / 60f, bill: true, top: true, step: s =>
                {
                    s.N.GlobalPosition = P7ShieldAt();
                    int f = (int)(s.Age * 60 + 1e-3f);
                    s.M.SetShaderParameter("p7_fade", f <= 0 ? 0f : f == 1 ? 0.34f : 0.67f);
                });
                P7Brush(cr.M, 0.2f * cpx);
                if (GetViewport()?.GetCamera3D() is { } cam && !cam.IsPositionBehind(sh0))
                {
                    var d2 = cam.UnprojectPosition(sh0 + dir) - cam.UnprojectPosition(sh0);
                    if (d2.LengthSquared() > 1e-4f) cr.M.SetShaderParameter("p7_dir2", d2.Normalized());
                }
                P7Kick(feet, dir, P7D.Count("kick.puffs", R()), P7D["kick.life"]);
                p7ChargeT = 0; p7ChargeDur = (float)e.Dur; p7ChargeDir = dir; p7ChargeHit = false;
                p7GhostDue.Clear();
                p7GhostNext = 0.03f; p7PlowNext = 0.04f;
                if (p7ChargeTrail != null) p7ChargeTrail.Until = 0;
                // the ribbon off her hips: the data's px at its head tapering to a point, its coverage 1 -> 0 to the tail
                p7ChargeTrail = P7NewTrail(() => PlayerPos + Vector3.Up * 0.95f - p7ChargeDir * 0.25f, 0.5f * P7D["charge.ribbon.head_px"] * P7Px(feet), p7ChargeDur + 0.05f, P7D["charge.ribbon.life"]);
                break;
            }
            case ChargePhase.Impact:
            {
                P7Ev("charge_impact");
                var at = P7Body(e.Target, e.X, e.Z, b);
                bool first = !p7ChargeHit;
                p7ChargeHit = true;
                // a hit (§4): one 4-6 spike star at the contact, its roots 3x its tips, 3 frames, nothing else of light
                int fr = (int)P7D["charge.star.frames"];
                P7StarPx(at - dir * 0.15f, P7D["charge.star.px"] * (first ? 1f : 0.8f), P7D.Count("charge.star.spikes", R()), P7D["charge.star.root_px"], 0, 1, Math.Max(1, (fr - 1) / 2), true, 1f / P7D["charge.star.root_tip"]);
                if (first) P7LightOn(at + Vector3.Up * 0.4f, 3.2f, Flare.Night ? 2.2f : 3f);
                var ff = new Vector3(at.X, Y(at.X, at.Z), at.Z);
                P7Dust(ff, 0.9f, 4, 18, 30, 0.3f, 0.2f);
                break;
            }
            case ChargePhase.Stop:
            {
                P7Ev("charge_stop");
                var at = P7Body(e.Target, e.X, e.Z, b);
                // the champion stops her: one star and one wavefront off the shield (at most two light shapes), a pool, a
                // punch of the view along the line, dust at their feet; the ribbon steps out
                P7StarPx(at - dir * 0.3f, P7D["charge.stop.px"], (int)P7D["charge.stop.spikes"], P7D["charge.stop.root_px"], 0, 2, 2, true, 1f / P7D["charge.star.root_tip"]);
                P7LightOn(at + Vector3.Up * 0.5f, 4.5f, Flare.Night ? 3.4f : 4.5f);
                Cam?.Kick(dir, 0.22f);
                // the wave off the shield: on the ground at the contact ahead of her, an open arc facing the drive (r3 fix 2:
                // the camera-facing ring round the shield read as a reticle on her)
                var feet = V(e.X, Y(e.X, e.Z), e.Z);
                var hit = feet + dir * 0.6f;
                float open = Mathf.DegToRad(P7D["wave.open_deg"]);
                P7Wave(new Vector3(hit.X, Y(hit.X, hit.Z) + 0.06f, hit.Z), P7D["charge.stop.reach"], P7D["charge.stop.run"], P7D["charge.stop.lead_px"], P7D["charge.stop.trail_px"],
                    span0: Mathf.Atan2(dir.Z, dir.X) - open / 2, span: open);
                P7Dust(feet + dir * 0.4f, 1.6f, 10, 22, 40, 0.35f, 0.25f);
                if (p7ChargeTrail != null) p7ChargeTrail.Until = 0;
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

    /// <summary>The Warden's dash (FX_LANGUAGE §4, a body moving): the press (glint and kick), a ribbon off her hips
    /// tapering to a point from its first frame, three amber rim afterimages 0.04 s apart. Her figure runs the blink over
    /// ~0.2 s, so the ribbon follows the figure, never drawn ahead of it. False: not hers (another calling's dash keeps its look).</summary>
    bool P7Dash(Ev.Dash e, Battle b)
    {
        if (P7Off || !string.Equals(b.Calling, "warden", StringComparison.OrdinalIgnoreCase) || p7ChargeT >= 0) return false;
        P7WarmUp();
        var dir = new Vector3((float)(e.X1 - e.X0), 0, (float)(e.Z1 - e.Z0));
        dir = dir.LengthSquared() > 1e-4f ? dir.Normalized() : Vector3.Forward;
        var feet = V(e.X0, Y(e.X0, e.Z0), e.Z0);
        P7Press(P7BladeAt(1), feet, dir);
        P7NewTrail(() => PlayerPos + Vector3.Up * 0.95f, 0.5f * P7D["dash.ribbon.head_px"] * P7Px(feet), 0.24f, P7D["dash.ribbon.life"]);
        p7ChargeT = 0; p7ChargeDur = 0.0f; p7ChargeDir = dir;
        p7GhostDue.Clear();
        p7GhostNext = -1;
        float g = P7D["charge.ghost.gap"];
        p7GhostDue.AddRange([0.03f, 0.03f + g, 0.03f + 2 * g]);
        return true;
    }

    /// <summary>Hard Landing: a wavefront running out at her feet to the shove's radius (its hot edge and feathered
    /// trailing band, width and coverage to nothing at the radius) and the dust it pushes outward.</summary>
    void P7Shove(Ev.HardLanding e)
    {
        if (P7Off) return;
        P7WarmUp();
        P7Ev("hard_landing");
        float r = (float)e.Radius;
        var c = V(e.X, Y(e.X, e.Z), e.Z);
        P7Wave(c + Vector3.Up * 0.06f, r, P7D["dash.shove.run"], P7D["dash.shove.lead_px"], P7D["dash.shove.trail_px"]);
        var px = P7D.All("dash.shove.px");
        P7Dust(c, r, P7D.Count("dash.shove.puffs", R()), px[0], px[1], P7D["dash.shove.run"] * 1.6f, 0.3f);
    }

    /* ----------------------------------------------------------- pieces -- */

    /// <summary>A wavefront (p7_wave) running out from `at` to `reach` m in `run` s (fast first), its edge and trailing
    /// band the given px at the play camera, width and coverage to nothing as it arrives; flat on the ground or facing the
    /// camera (`bill`, over everything).</summary>
    P7Shape P7Wave(Vector3 at, float reach, float run, float leadPx, float trailPx, bool bill = false, float span0 = 0, float span = Mathf.Tau)
    {
        float rpx = reach / P7Px(at);
        int n = Math.Clamp((int)MathF.Round(span * rpx / P7D["wave.arc_px"]), 3, 9);
        Vector4[]? arcs = null;
        var shed = P7D.All("wave.shed");
        var dpx = P7D.All("wave.dust_px");
        int next = 0;
        var s = P7Quad(5, at, reach, run + 1 / 60f, bill: bill, top: bill, step: q =>
        {
            float t = Mathf.Clamp(q.Age / run, 0, 1), prog = 1 - (1 - t) * (1 - t);
            q.M.SetShaderParameter("p7_prog", prog);
            q.M.SetShaderParameter("p7_fall", prog);
            // the front sheds dust as it passes (clusters off the arcs, riding out behind it); the last at the reach
            while (arcs != null && next < shed.Length && prog >= shed[next])
            {
                float k = shed[next++];
                P7Shed(new Vector3(at.X, at.Y - 0.06f, at.Z), reach * k, arcs, 2 * (1 - t) * reach / run, dpx[0], dpx[1]);
            }
        });
        s.M.SetShaderParameter("p7_lead", leadPx / rpx);
        s.M.SetShaderParameter("p7_trw", trailPx / rpx);
        s.M.SetShaderParameter("p7_prog", 0.02f);
        arcs = P7Arcs(s.M, span0 + (span >= Mathf.Tau - 1e-3f ? R() * Mathf.Tau : 0), span, n, 0, 0.85f, 1.25f, 0.35f);
        P7BrushWave(s.M, rpx, leadPx);
        return s;
    }

    /// <summary>(r3 fix 2) A wavefront's painted arcs (p7_wave): `n` brush swipes evenly over `span` from `span0` (radians,
    /// atan2(z, x) round the quad), each centred in its sector give or take 15%, its half-length `lo`-`hi` of half its sector
    /// (some overlap, some gaps), its front `zk` leads in or out, its head on a side (`swirl` +1/-1 all one way, 0 each its
    /// own). Returns them (x centre, y half-length, z offset, w side) for the dust.</summary>
    Vector4[] P7Arcs(ShaderMaterial m, float span0, float span, int n, int swirl, float lo, float hi, float zk)
    {
        n = Math.Clamp(n, 1, 12);
        var a = new Vector4[12];
        float sec = span / n;
        for (int i = 0; i < n; i++)
            a[i] = new Vector4(span0 + (i + 0.5f + (R() - 0.5f) * 0.3f) * sec, 0.5f * sec * Mathf.Lerp(lo, hi, R()), (R() - 0.5f) * 2 * zk,
                swirl != 0 ? swirl : (R() < 0.5f ? 1 : -1));
        m.SetShaderParameter("p7_arc", a);
        m.SetShaderParameter("p7_narc", n);
        m.SetShaderParameter("p7_span", new Vector2(span0, span));
        return a[..n];
    }

    /// <summary>(r3 fix 2) Dust shed by a wavefront's arcs at `radius` m from `c` (the ground): on most arcs a cluster of
    /// two or three two-value puffs (`px0`-`px1` at the play camera; a lit top over a darker, wider skirt) toward the arc's
    /// head, thrown on outward at a share of the front's `speed` (m/s) so the front leaves them behind.</summary>
    void P7Shed(Vector3 c, float radius, Vector4[] arcs, float speed, float px0, float px1)
    {
        float m = P7Px(c);
        foreach (var a in arcs)
        {
            if (R() > 0.7f) continue;
            int k = 2 + (int)(R() * 1.99f);
            for (int i = 0; i < k; i++)
            {
                float ang = a.X + a.W * a.Y * (0.1f + 0.7f * R());
                var o = new Vector3(Mathf.Cos(ang), 0, Mathf.Sin(ang));
                var p = c + o * (radius * (0.97f + R() * 0.06f));
                p.Y = Y(p.X, p.Z);
                float sz = Mathf.Lerp(px0, px1, R() * R()) * m;
                var v = o * speed * (0.3f + 0.25f * R()) + Vector3.Up * (0.4f + R() * 0.5f);
                WgPuff(p + Vector3.Up * (0.18f + R() * 0.08f), v, sz, 1.6f, 0.4f + R() * 0.25f, P7Lit(1.2f + R() * 0.1f), 0.92f, 5f);
                WgPuff(p + Vector3.Up * 0.07f, v * 0.8f, sz * 1.3f, 1.45f, 0.48f + R() * 0.25f, WgDust(0.58f), 0.88f, 5.5f);
            }
        }
    }

    /// <summary>(r3 fix 2) A wavefront's brush (p7_wave): its own bristles, about one per 3 px across the lead's swell
    /// (the shape lays their run along each arc and the trail's drag), drier tails (0.75) and a 0.28 waver so the band
    /// edges read as a brush's at 1:1. `rpx`: the reach in px at the play camera.</summary>
    void P7BrushWave(ShaderMaterial m, float rpx, float leadPx)
    {
        m.SetShaderParameter("fx_stroke_seed", R() * 97f);
        m.SetShaderParameter("fx_bristle", new Vector4(Mathf.Clamp(0.66f * 1.3f * leadPx, 3f, 14f), 2f, 0.75f, 0.28f));
        m.SetShaderParameter("p7_rpx", rpx);
    }

    /// <summary>The press (every move): one three-band glint at `at` (the blade's tip or the shield) and a dust kick at
    /// her feet thrown back from `dir`.</summary>
    void P7Press(Vector3 at, Vector3 feet, Vector3 dir)
    {
        P7Glint(at, P7D["glint.px"]);
        P7Kick(feet, dir, P7D.Count("kick.puffs", R()), P7D["kick.life"]);
    }

    /// <summary>One three-band glint `px` long at the play camera (a hot heart and a lens streak), the data's frames.</summary>
    void P7Glint(Vector3 at, float px)
    {
        int fr = (int)P7D["glint.frames"];
        var g = P7Quad(4, at, 0.5f * px * P7Px(at), fr / 60f, bill: true, top: true, step: s =>
        {
            int f = (int)(s.Age * 60 + 1e-3f);
            s.M.SetShaderParameter("p7_fade", f <= 0 ? 0f : f == 1 ? 0.34f : 0.67f);
        });
        P7Brush(g.M, 0.2f * px);
    }

    /// <summary>A kick of dust: `n` two-value puffs (a lit top over a darker skirt) of the data's px, thrown back from
    /// `dir` and out to the sides (all round when `dir` is zero), low and quick.</summary>
    void P7Kick(Vector3 feet, Vector3 dir, int n, float life)
    {
        float m = P7Px(feet);
        var px = P7D.All("kick.px");
        var side = new Vector3(dir.Z, 0, -dir.X);
        for (int i = 0; i < n; i++)
        {
            Vector3 lean;
            if (dir.LengthSquared() < 1e-4f) { float a = (i + R() * 0.6f) / n * Mathf.Tau; lean = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a)); }
            else lean = (-dir * (0.5f + R() * 0.7f) + side * ((R() - 0.5f) * 2.4f)).Normalized();
            float sz = Mathf.Lerp(px[0], px[1], R() * R()) * m;
            var v = lean * (1.8f + R() * 1.6f) + Vector3.Up * (0.3f + R() * 0.45f);
            WgPuff(feet + lean * 0.18f + Vector3.Up * 0.16f, v, sz, 1.45f, life * (0.85f + R() * 0.3f), P7Lit(1.1f + R() * 0.12f), 0.85f, 4f);
            WgPuff(feet + lean * 0.14f + Vector3.Up * 0.07f, v * 0.8f, sz * 1.2f, 1.35f, life * (0.95f + R() * 0.3f), WgDust(0.62f), 0.8f, 4.4f);
        }
    }

    /// <summary>Dust out to `reach` in `run` s: `puffs` two-value puffs (`px0`-`px1` at the play camera) in knots at
    /// uneven angles, never an even dotted circle.</summary>
    void P7Dust(Vector3 c, float reach, int puffs, float px0, float px1, float run, float d0)
    {
        float m = P7Px(c), a0 = R() * Mathf.Tau;
        const float drag = 4.5f;
        int clusters = Math.Max(3, puffs / 4);
        int left = puffs;
        for (int q = 0; q < clusters && left > 0; q++)
        {
            float ac = a0 + (q + (R() - 0.5f) * 0.7f) / clusters * Mathf.Tau;
            int n = q == clusters - 1 ? left : Math.Min(left, Math.Max(1, puffs / clusters + (int)((R() - 0.5f) * 3)));
            left -= n;
            for (int i = 0; i < n; i++)
            {
                float a = ac + (R() - 0.5f) * 0.45f;
                var o = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                float far = Mathf.Max(0.2f, reach * (0.72f + R() * 0.34f) - d0);
                float v0 = far * drag / (1 - Mathf.Exp(-drag * run));
                var at = c + o * d0;
                float sz = Mathf.Lerp(px0, px1, R() * R()) * m;
                WgPuff(at + Vector3.Up * (0.2f + R() * 0.1f), o * v0 + Vector3.Up * (0.15f + R() * 0.25f), sz, 1.4f, run * 1.6f + R() * 0.3f, P7Lit(1.08f + R() * 0.12f), 0.82f, drag);
                WgPuff(at + Vector3.Up * 0.09f, o * v0 * (0.8f + R() * 0.15f), sz * 1.2f, 1.35f, run * 1.8f + R() * 0.3f, WgDust(0.64f + R() * 0.06f), 0.78f, drag);
            }
        }
    }

    /// <summary>A chunk of earth: the Warden ground's faceted stone, painted the ground's own brown for its flight (the
    /// r2 judge read the stones as red cubes in her pool), its paint let go when it lands back in the pool.</summary>
    void P7Throw(Vector3 p, Vector3 v, float scale, float life)
    {
        WgThrow(p, v, scale, life, 5);
        WgRock? rk = null;
        foreach (var c in wgRocks) if (c.On && c.Age == 0 && c.P == p) { rk = c; break; }
        if (rk == null) return;
        p7Earth ??= new StandardMaterial3D { AlbedoColor = WgDustDay * 0.85f, Roughness = 0.95f };
        rk.N.MaterialOverride = p7Earth;
        p7Thrown.Add(rk);
    }

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
        // the afterimage's rim is ~2.6 px across (one bristle); the vow's pulse band a fifth of her height (~30 px)
        P7Brush(m, mode == 11 ? 30 : 3);
        m.SetShaderParameter("p7_alpha", 1f);
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
        for (int i = p7Thrown.Count - 1; i >= 0; i--)
            if (!p7Thrown[i].On) { p7Thrown[i].N.MaterialOverride = null; p7Thrown.RemoveAt(i); }
        for (int i = p7Ghosts.Count - 1; i >= 0; i--)
        {
            var g = p7Ghosts[i];
            g.Age += dt;
            if (g.Age >= g.Life) { g.Root.QueueFree(); p7Ghosts.RemoveAt(i); continue; }
            g.M.SetShaderParameter("p7_t", g.Age);
            g.M.SetShaderParameter("p7_dim", KillDimNow);
        }
        foreach (var l in p7Lights)
        {
            if (l.Age > 0.4f) continue;
            l.Age += dt;
            // up on the hit's frame, held a sample, down over two (2-3 samples at a hit, §1)
            float k = l.Age < l.Hold ? 1 : Mathf.Max(0, 1 - (l.Age - l.Hold) / Mathf.Max(1e-3f, l.Down));
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
                if (p7GhostNext >= 0 && p7ChargeT >= p7GhostNext) { p7GhostNext += P7D["charge.ghost.gap"]; if (p7Ghosts.Count < 3) P7Snap(3, P7D["charge.ghost.life"]); }
                if (p7PlowNext >= 0 && p7ChargeT >= p7PlowNext)
                {
                    p7PlowNext += P7D["charge.plow.gap"];
                    var ppx = P7D.All("charge.plow.px");
                    var feet = new Vector3(PlayerPos.X, Y(PlayerPos.X, PlayerPos.Z), PlayerPos.Z);
                    var side = new Vector3(p7ChargeDir.Z, 0, -p7ChargeDir.X);
                    for (int sgn = -1; sgn <= 1; sgn += 2)
                    {
                        float sz = Mathf.Lerp(ppx[0], ppx[1], R()) * P7Px(feet);
                        var v = side * sgn * (1.8f + R() * 1.4f) - p7ChargeDir * (0.3f + R() * 0.5f) + Vector3.Up * (0.3f + R() * 0.45f);
                        var at = feet + side * sgn * 0.3f + p7ChargeDir * 0.2f;
                        WgPuff(at + Vector3.Up * 0.2f, v, sz, 1.6f, 0.45f + R() * 0.25f, P7Lit(1.1f + R() * 0.1f), 0.82f, 4f);
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

    /// <summary>The ribbon mesh: the sampled path splined (Catmull-Rom, 4 steps a span), then eased until no joint turns
    /// more than the data's degrees on screen (leap.ribbon.turn_deg: no kink, no fishhook); a strip whose UV.x is its
    /// along: the smaller of its age (1 the head, now; 0 the tail, Life old) and its length from the head (so it tapers
    /// to a point from its first frame, never a rod with a blunt tail); UV.y 0..1 across. A body's ribbon faces the camera
    /// (`Width` its half-width at the head); a blade's sweep spans the blade. After `Until` its life steps it out.</summary>
    void P7BuildTrail(P7Trail t, Camera3D? cam)
    {
        t.Mesh.ClearSurfaces();
        int n = t.Pts.Count;
        if (n < 2 || cam == null) return;
        bool sweep = t.Sweep != null && t.Pts2.Count == n;
        var eye = cam.GlobalPosition;
        float after = t.Age - t.Until;
        t.M.SetShaderParameter("p7_fade", after <= 0 ? 0f : Mathf.Min(0.95f, Mathf.Floor(after / P7Sample + 1) * 0.34f));
        t.M.SetShaderParameter("p7_dim", KillDimNow); // F1 r5: not the kill: held down in a mass kill's window
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
        if (!sweep) P7Ease(pa, cam, Mathf.DegToRad(P7D["leap.ribbon.turn_deg"]));
        // its length from the head (the last point)
        var sl = new float[m];
        for (int i = m - 2; i >= 0; i--) sl[i] = sl[i + 1] + pa[i].DistanceTo(pa[i + 1]);
        float total = Mathf.Max(1e-4f, sl[0]);
        t.Mesh.SurfaceBegin(Mesh.PrimitiveType.TriangleStrip);
        for (int i = 0; i < m; i++)
        {
            float along = Mathf.Clamp(Mathf.Min(1 - ag[i] / t.Life, 1 - sl[i] / total), 0, 1);
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

    /// <summary>Eases a polyline until no joint turns more than `max` radians as the camera sees it (each offending
    /// point pulled toward its neighbours' middle; the ends stay), at most 12 passes.</summary>
    static void P7Ease(List<Vector3> p, Camera3D cam, float max)
    {
        int m = p.Count;
        if (m < 3) return;
        var q = new Vector2[m];
        for (int pass = 0; pass < 12; pass++)
        {
            for (int i = 0; i < m; i++) q[i] = cam.IsPositionBehind(p[i]) ? Vector2.Zero : cam.UnprojectPosition(p[i]);
            bool ok = true;
            for (int i = 1; i < m - 1; i++)
            {
                var d0 = q[i] - q[i - 1]; var d1 = q[i + 1] - q[i];
                if (d0.LengthSquared() < 0.25f || d1.LengthSquared() < 0.25f) continue;
                if (Mathf.Abs(d0.AngleTo(d1)) <= max) continue;
                ok = false;
                p[i] = p[i] * 0.4f + (p[i - 1] + p[i + 1]) * 0.3f;
            }
            if (ok) break;
        }
    }
}

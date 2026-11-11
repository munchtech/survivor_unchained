using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// P7 (rebuilt 9 Nov against judge r1; round 3 against judge r2: one hero light shape a beat, the rings p7_wave, the
/// numbers in data/look/fx_language.json "p7"): Bladestorm and Iron Vow in the FX language
/// (docs/design/FX_LANGUAGE.md). Every light shape is a p7_stroke (shaders/fx_p7_b.gdshaderinc); matter is the
/// Warden ground's dust, chunks and crack strip, clustered and two-valued.
/// The storm: two blade smears swept behind her sword's real tip each frame (a hot head at the blade, the tail tapering
/// over ~105 degrees; a thinner, lower wake lagging it at another tilt), a low clustered dust swirl at her feet, a gold
/// pool. Each struck foe a rim and, for the nearest six, tangential sparks. A Sunder line is a ground fissure: the crack
/// strip laid along the line (its own dark, lit lips) with a thin white-gold seam in it pulsing at half while pending;
/// on its split the seam flares and dust and chunks burst along the whole line within 0.1 s, then the seam cools in
/// steps (core, gold, amber, gone) and the crack fades. The break: one bold star under her feet and one ring that thins
/// to nothing exactly at the break's radius, clustered dust, chunks, the pool, a punch.
/// The vow: the plant's dust and a shield-slam flash in its first 0.10 s; a 3D dome about her showing only an amber rim
/// (flaring a sample on each blow it takes, sparks streaking from the nearest attackers into the shield); a glow on the
/// shield's face growing about 3x over the brace and stepping up with each blow, a ground light rising with it; the
/// burst a star off the shield and a ring narrowing to a fifth of its width and dying by its radius, then dust there.
/// Keyed on Ev.Spin, Ev.SpinLine and Ev.Brace, never the string ids (iron_vow is a boon's id too).
/// </summary>
public partial class BattleFx
{
    sealed class P7Scar
    {
        public required MeshInstance3D N;
        public required ShaderMaterial M;
        public readonly List<WgDecal> Cracks = new();
        public float Age, SplitAge = -1, FadeAge = -1;
    }

    /// <summary>A blade smear: a strip swept behind the blade's tip, rebuilt each frame while the storm is on.</summary>
    sealed class P7Smear
    {
        public required MeshInstance3D N;
        public required ImmediateMesh Mesh;
        public required ShaderMaterial M;
        public float Arc, RadK = 1, HwK = 1, Lag, Dy, Tilt, Alpha = 1, Life0;
        public float DownAge = -1;
    }

    readonly List<P7Smear> p7Smears = new();
    OmniLight3D? p7StormLight, p7VowLight;
    double p7StormOff = -9;
    float p7StormR, p7StormOn = -1, p7SpinPrev = float.NaN, p7SpinDir = -1, p7Swirl, p7SpinAngle, p7TiltPhi;
    // the frame's storm work (P7Pre): a tick or start in this batch; a break in it; how many tick kits drawn
    bool p7TickNow, p7BreakNow;
    int p7TickKits;
    double p7VowAt = -9, p7VowStart = -9, p7StoreAt = -9;
    float p7VowLevel;
    int p7VowBlows;
    readonly Dictionary<int, P7Scar> p7Scars = new();
    P7Shape? p7Dome, p7Glow;
    Node3D? p7Shield;
    static SphereMesh? p7DomeMesh;

    /// <summary>The storm's hits and the vow's burst are drawn here (P7Owns).</summary>
    bool P7OwnsStorm(Ev.Hit e)
    {
        if (e.Art == "slash_spin" && (p7StormOn >= 0 || p7BreakNow || time - p7StormOff < 1.3f))
        {
            if (e.Target >= 0) { struckRims[e.Target] = Engine.GetFramesDrawn(); rimNoFlash.Remove(e.Target); }
            if (p7TickNow && !p7BreakNow && p7TickKits < 6)
            {
                p7TickKits++;
                var her = PlayerPos;
                var at = new Vector3((float)e.X, Y(e.X, e.Z) + 0.6f, (float)e.Z);
                var rad = new Vector3(at.X - her.X, 0, at.Z - her.Z);
                rad = rad.LengthSquared() > 1e-4f ? rad.Normalized() : Vector3.Forward;
                // one three-band nick on the contact, along the blade's way (tangent, her spin's sense)
                P7Nick(at - rad * 0.3f, new Vector3(-rad.Z, 0, rad.X) * -p7SpinDir, P7D["storm.nick.px"]);
            }
            return true;
        }
        if (e.Art == "iron_vow" && time - p7VowAt < 0.2)
        {
            // (the struck rim, never its white flash: the r2 judge read the crowd bleached cream)
            if (e.Target >= 0) { struckRims[e.Target] = Engine.GetFramesDrawn(); rimNoFlash.Add(e.Target); }
            return true;
        }
        return false;
    }

    void P7PreStorm(IReadOnlyList<CombatEvent> events)
    {
        p7TickNow = p7BreakNow = false;
        p7TickKits = 0;
        foreach (var e in events)
        {
            if (e is Ev.Spin { Phase: SpinPhase.Start or SpinPhase.Tick }) p7TickNow = true;
            if (e is Ev.Spin { Phase: SpinPhase.Break } || e is Ev.Brace { Phase: BracePhase.Burst }) { p7BreakNow = e is Ev.Spin; p7HushShake = true; }
        }
    }

    /// <summary>A shape on a mesh of its own (the dome), stepped and freed like a quad.</summary>
    P7Shape P7OnMesh(int mode, Mesh mesh, Vector3 at, Vector3 scale, float life, Action<P7Shape>? step = null)
    {
        var m = P7Mat(mode);
        var n = new MeshInstance3D { Mesh = mesh, MaterialOverride = m, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
        n.Scale = scale;
        AddChild(n);
        n.GlobalPosition = at;
        if (FxAfter.On) FxAfter.Adopt(n);
        var s = new P7Shape { N = n, M = m, Life = life, Step = step };
        p7Shapes.Add(s);
        return s;
    }

    P7Shape P7Brushed(float widthPx, P7Shape s)
    {
        P7Brush(s.M, widthPx);
        return s;
    }

    /* ----------------------------------------------------------- storm -- */

    void P7Spin(Ev.Spin e)
    {
        if (P7Off) return;
        P7WarmUp();
        switch (e.Phase)
        {
            case SpinPhase.Start:
            {
                P7Ev("storm_start");
                p7StormOn = 0; p7StormR = (float)e.Radius; p7SpinPrev = float.NaN;
                foreach (var sm in p7Smears) if (sm.DownAge < 0) sm.DownAge = 9;
                var tip = P7BladeAt(1);
                var feet0 = new Vector3(PlayerPos.X, Y(PlayerPos.X, PlayerPos.Z), PlayerPos.Z);
                var rad0 = new Vector3(tip.X - feet0.X, 0, tip.Z - feet0.Z);
                P7Press(tip, feet0, rad0.LengthSquared() > 1e-4f ? new Vector3(-rad0.Z, 0, rad0.X).Normalized() : Vector3.Zero);
                p7TiltPhi = Mathf.Atan2(tip.Z - PlayerPos.Z, tip.X - PlayerPos.X) + Mathf.Pi * 0.5f;
                // ONE smear: the blade's own path at its reach (round 3: the wake smear parked beside her is gone)
                p7Smears.Add(P7NewSmear(Mathf.DegToRad(P7D["storm.smear.arc_deg"]), 1f, 1f, 0, 0, 12, P7D["storm.smear.alpha"], 0f));
                if (p7StormLight == null)
                {
                    p7StormLight = new OmniLight3D { ShadowEnabled = false, OmniAttenuation = 1.1f, LightColor = P7Band(1) };
                    AddChild(p7StormLight);
                }
                p7StormLight.OmniRange = Mathf.Min(p7StormR * 1.2f, 4.2f);
                p7StormLight.Visible = true;
                break;
            }
            case SpinPhase.End:
                P7Ev("storm_end");
                P7StormDown();
                break;
            case SpinPhase.Break:
                P7Ev("storm_break");
                P7StormDown();
                P7Break(e.X, e.Z, (float)e.Radius, (float)e.Grow);
                break;
        }
    }

    P7Smear P7NewSmear(float arc, float radK, float hwK, float lag, float dy, float tilt, float alpha, float life0)
    {
        var mesh = new ImmediateMesh();
        var m = P7Mat(6);
        // the stroke is the data's px across at its head (at the play camera), tapering to a point
        P7Brush(m, P7D["storm.smear.head_px"] * hwK, 0.001f);
        var n = new MeshInstance3D { Mesh = mesh, MaterialOverride = m, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
        AddChild(n);
        n.GlobalTransform = Transform3D.Identity;
        if (FxAfter.On) FxAfter.Adopt(n);
        m.SetShaderParameter("p7_alpha", alpha);
        m.SetShaderParameter("p7_fade", life0);
        return new P7Smear { N = n, Mesh = mesh, M = m, Arc = arc, RadK = radK, HwK = hwK, Lag = lag, Dy = dy, Tilt = tilt, Alpha = alpha, Life0 = life0 };
    }

    /// <summary>The smear's strip this frame: a stroke on the blade's own path at its reach (the tip's radius round her),
    /// the data's px across at its head (at the blade) and tapering to a point over its arc, swept back round her on a
    /// plane leaning `Tilt` degrees; the stroke's round cap is its nose.</summary>
    void P7BuildSmear(P7Smear s, float wind)
    {
        var her = PlayerPos;
        her.Y = Y(her.X, her.Z);
        var tip = P7BladeAt(1);
        float a = Mathf.Atan2(tip.Z - her.Z, tip.X - her.X);
        float rt = new Vector2(tip.X - her.X, tip.Z - her.Z).Length();
        float rc = Mathf.Clamp(rt, 0.9f, 1.6f) * s.RadK, hw = 0.5f * P7D["storm.smear.head_px"] * P7Px(her) * s.HwK / 0.72f;
        float h = Mathf.Clamp(tip.Y - her.Y, 0.45f, 1.5f) + s.Dy;
        float k = Mathf.Tan(Mathf.DegToRad(s.Tilt));
        float a0 = a - p7SpinDir * s.Lag, arc = s.Arc * wind;
        const int nose = 0, body = 30;
        var m = s.Mesh;
        m.ClearSurfaces();
        m.SurfaceBegin(Mesh.PrimitiveType.TriangleStrip);
        for (int i = -nose; i <= body; i++)
        {
            float u = i < 0 ? i * 0.02f : (float)i / body;
            float th = a0 - p7SpinDir * u * arc;
            float y = her.Y + h + rc * k * (Mathf.Cos(th - p7TiltPhi) - Mathf.Cos(a0 - p7TiltPhi));
            var d = new Vector3(Mathf.Cos(th), 0, Mathf.Sin(th));
            // the nose: the same strip, its across spread so the stroke rounds off ahead of the blade
            float e = i < 0 ? Mathf.Sqrt(Mathf.Max(0.03f, 1 - Mathf.Pow(u / 0.085f, 2))) : 1f;
            float along = i < 0 ? 1f : 1 - u;
            m.SurfaceSetUV(new Vector2(along, 0.5f - 0.5f / e));
            m.SurfaceAddVertex(new Vector3(her.X, y, her.Z) + d * (rc - hw));
            m.SurfaceSetUV(new Vector2(along, 0.5f + 0.5f / e));
            m.SurfaceAddVertex(new Vector3(her.X, y, her.Z) + d * (rc + hw));
        }
        m.SurfaceEnd();
    }

    void P7StormDown()
    {
        if (p7StormOn < 0) return;
        p7StormOn = -1; p7StormOff = time;
        // the smears freeze where they are and die by stepping: core, gold, amber, gone over 3 samples
        foreach (var s in p7Smears) if (s.DownAge < 0) s.DownAge = 0;
    }

    void P7StepSmears(float dt)
    {
        for (int i = p7Smears.Count - 1; i >= 0; i--)
        {
            var s = p7Smears[i];
            if (s.DownAge < 0)
            {
                if (p7StormOn >= 0) P7BuildSmear(s, Mathf.Clamp(p7StormOn / 0.15f, 0.25f, 1));
                continue;
            }
            s.DownAge += dt;
            float life = Mathf.Min(1, s.Life0 + (Mathf.Floor(s.DownAge / P7Sample) + 1) * 0.34f);
            s.M.SetShaderParameter("p7_fade", life);
            if (s.DownAge > 3 * P7Sample || !IsInstanceValid(s.N)) { if (IsInstanceValid(s.N)) s.N.QueueFree(); p7Smears.RemoveAt(i); }
        }
    }

    /// <summary>The break: she plants. One bold star under her feet, one ring thinning to nothing at the radius, the
    /// clustered dust, chunks, the pool and a punch; the lines split (Ev.SpinLine Split, P7Line).</summary>
    void P7Break(double x, double z, float r, float grow)
    {
        var c = V(x, Y(x, z), z);
        float k = Mathf.Clamp((grow - 1) / 0.6f, 0, 1);
        P7StarPx(c + Vector3.Up * 0.05f, P7D["storm.star.px"] * (0.9f + 0.2f * k), (int)P7D["storm.star.spikes"], P7D["storm.star.root_px"], 6, 2, 2, false);
        P7Wave(c + Vector3.Up * 0.06f, r, P7D["storm.ring.run"], P7D["storm.ring.lead_px"], P7D["storm.ring.trail_px"]);
        P7LightOn(c + Vector3.Up * 1.4f, r * 1.5f, (Flare.Night ? 2.0f : 4.5f) * (0.85f + 0.3f * k));
        var dpx = P7D.All("leap.dust.px");
        P7Dust(c, r * 0.95f, 20 + (int)(6 * k), dpx[0], dpx[1], 0.4f, 0.4f);
        int chunks = 7 + (int)(R() * 3.99f + 4 * k);
        for (int i = 0; i < chunks; i++)
        {
            float a = R() * Mathf.Tau, d = 0.4f + r * 0.3f * Mathf.Sqrt(R());
            var o = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            double px = x + o.X * d, pz = z + o.Z * d;
            P7Throw(V(px, Y(px, pz) + 0.2, pz), o * (1.5f + R() * 2.4f) + Vector3.Up * (2.6f + R() * 2.4f), 0.6f + R() * 0.3f, 1.6f + R() * 0.5f);
        }
        Cam?.JoltPx(Vector3.Up, 9f + 3 * k);
    }

    /// <summary>A Sunder line the storm threw: a ground fissure. Thrown: the crack strip laid along it (over 0.1 s,
    /// from her end) with its seam pulsing at half; split: the seam flares, dust and chunks along the whole line within
    /// 0.1 s, the seam cools in steps and the crack fades; faded: it steps out, nothing dealt.</summary>
    void P7Line(Ev.SpinLine e)
    {
        if (P7Off) return;
        P7WarmUp();
        var from = new Vector2((float)e.X0, (float)e.Z0);
        var to = new Vector2((float)e.X1, (float)e.Z1);
        float len = from.DistanceTo(to);
        if (len < 0.3f) return;
        var dir = (to - from) / len;
        var side = new Vector2(-dir.Y, dir.X);
        float theta = Mathf.Atan2(-dir.Y, dir.X);
        int n = Math.Clamp((int)Mathf.Round(len / 1.0f), 4, 8);
        const int t0 = 2;
        const float across = 0.7f;
        switch (e.Phase)
        {
            case SpinLinePhase.Thrown:
            {
                P7Ev("line_thrown");
                // the seam: a strip on the crack's own centre, following the ground
                var mesh = new ImmediateMesh();
                int K = Math.Max(10, (int)(len / 0.2f));
                // the seam: the data's px across (at most 4), inside the crack's gap
                float hwMax = 0.5f * P7D["storm.seam.px"] * P7Px(V(from.X, Y(from.X, from.Y), from.Y));
                var s3 = new Vector3(side.X, 0, side.Y);
                mesh.SurfaceBegin(Mesh.PrimitiveType.TriangleStrip);
                for (int j = 0; j <= K; j++)
                {
                    float al = len * j / K;
                    var p = P7CrackAt(from, dir, side, al, len, t0, n, across) + Vector3.Up * 0.04f;
                    mesh.SurfaceSetUV(new Vector2((float)j / K, 0));
                    mesh.SurfaceAddVertex(p - s3 * hwMax);
                    mesh.SurfaceSetUV(new Vector2((float)j / K, 1));
                    mesh.SurfaceAddVertex(p + s3 * hwMax);
                }
                mesh.SurfaceEnd();
                var m = P7Mat(7);
                P7Brush(m, P7D["storm.seam.px"]);
                m.SetShaderParameter("p7_alpha", 0.5f);
                m.SetShaderParameter("p7_fade", 0.67f);
                var node = new MeshInstance3D { Mesh = mesh, MaterialOverride = m, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
                AddChild(node);
                node.GlobalTransform = Transform3D.Identity;
                if (FxAfter.On) FxAfter.Adopt(node);
                var sc = new P7Scar { N = node, M = m };
                if (p7Scars.Remove(e.Id, out var old)) P7ScarGone(old);
                p7Scars[e.Id] = sc;
                // the matter: the crack strip in tiles, opening from her end over 0.1 s, its gap tapering to the far end
                if (wgAlb is { } alb && wgNrm is { } nrm)
                {
                    float seg = len / n;
                    for (int i = 0; i < n; i++)
                    {
                        int tile = Math.Clamp(t0 + i, 0, 11);
                        var cc = from + dir * (seg * (i + 0.5f));
                        var pos = V(cc.X, Y(cc.X, cc.Y), cc.Y);
                        WgLater(0.1f * i / n, () =>
                        {
                            if (WgDecalOn(pos, theta, new Vector3(seg * 1.03f, 0.5f, WgBand * across), alb[tile], nrm[tile], null, 14f, 1f, 0, 0, 0, WgLineTint) is not { } d) return;
                            sc.Cracks.Add(d);
                            if (sc.SplitAge >= 0 || sc.FadeAge >= 0) { d.FadeFrom = d.Age + 0.6f; d.Life = d.Age + 1.2f; }
                        });
                    }
                }
                // a little dust where it tears open, in two or three clusters
                int cl = 2 + (int)(R() * 1.99f);
                for (int c = 0; c < cl; c++)
                {
                    float al = (c + 0.2f + R() * 0.6f) / cl * len;
                    var p = P7CrackAt(from, dir, side, al, len, t0, n, across);
                    WgLater(0.1f * al / len, () => WgJet(p, 0.55f));
                }
                break;
            }
            case SpinLinePhase.Split:
            {
                P7Ev("line_split");
                if (!p7Scars.TryGetValue(e.Id, out var sc)) break;
                sc.SplitAge = 0;
                foreach (var d in sc.Cracks) { d.FadeFrom = d.Age + 0.9f; d.Life = d.Age + 1.8f; }
                // the burst along the whole line within 0.1 s: clustered jets (lit over dark), chunks off the lips
                int m = 4 + (int)(len / 2f);
                for (int c = 0; c < m; c++)
                {
                    float al = Mathf.Clamp((c + R()) / m, 0.03f, 0.97f) * len;
                    float force = 1.1f - 0.35f * al / len;
                    var p = P7CrackAt(from, dir, side, al, len, t0, n, across);
                    int jets = 1 + (int)(R() * 2.2f);
                    float delay = 0.1f * al / len;
                    WgLater(delay, () =>
                    {
                        for (int j = 0; j < jets; j++) WgJet(p + new Vector3(R() - 0.5f, 0, R() - 0.5f) * 0.3f, force);
                        int ch = (int)(R() * 2.6f);
                        for (int j = 0; j < ch; j++)
                        {
                            var sd = side * (R() < 0.5f ? -1 : 1);
                            var v = new Vector3(sd.X, 0, sd.Y) * (0.8f + R() * 1.6f) + Vector3.Up * (3f + R() * 2.5f) * force;
                            P7Throw(p + Vector3.Up * 0.05f, v * 0.8f, 0.5f + R() * 0.3f, 1.4f + R() * 0.5f);
                        }
                    });
                }
                var her = V(from.X, Y(from.X, from.Y), from.Y);
                WgTallJet(her + new Vector3(dir.X, 0, dir.Y) * 0.6f, 0.9f);
                break;
            }
            case SpinLinePhase.Faded:
                if (p7Scars.TryGetValue(e.Id, out var sf) && sf.SplitAge < 0)
                {
                    sf.FadeAge = 0;
                    foreach (var d in sf.Cracks) { d.FadeFrom = d.Age; d.Life = d.Age + 0.5f; }
                }
                break;
        }
    }

    /// <summary>The crack strip's gap centre at `along` (m), as the decals draw it (WgCrackPoint's offset taken the
    /// other way: measured on the laid strip, the gap ran mirrored to it).</summary>
    Vector3 P7CrackAt(Vector2 from, Vector2 dir, Vector2 side, float along, float len, int t0, int n, float across)
    {
        var c = WgCrackPoint(from, dir, side, along, len, t0, n, across);
        var q = from + dir * along;
        var m = new Vector2(2 * q.X - c.X, 2 * q.Y - c.Z);
        return V(m.X, Y(m.X, m.Y), m.Y);
    }

    void P7ScarGone(P7Scar s)
    {
        if (IsInstanceValid(s.N)) s.N.QueueFree();
        foreach (var d in s.Cracks) if (d.Life > d.Age + 0.5f) { d.FadeFrom = d.Age; d.Life = d.Age + 0.5f; }
    }

    void P7StepScars(float dt)
    {
        List<int>? gone = null;
        foreach (var (id, s) in p7Scars)
        {
            s.Age += dt;
            if (s.SplitAge >= 0)
            {
                s.SplitAge += dt;
                float t = s.SplitAge;
                // the flare in heat, never in width: 0.1 s with the core in it, then a step a stretch: gold, amber, gone
                s.M.SetShaderParameter("p7_alpha", 1f);
                s.M.SetShaderParameter("p7_fade", t < 0.1f ? 0f : t < 0.3f ? 0.34f : t < 0.55f ? 0.67f : 1f);
                if (t > 0.6f) (gone ??= new()).Add(id);
            }
            else if (s.FadeAge >= 0)
            {
                s.FadeAge += dt;
                s.M.SetShaderParameter("p7_fade", Mathf.Min(1, 0.34f + Mathf.Floor(s.FadeAge / P7Sample) * 0.34f));
                if (s.FadeAge > 3 * P7Sample) (gone ??= new()).Add(id);
            }
            else
            {
                // pending: a sample at full as it opens, then the seam pulses about half
                float pulse = 0.5f + 0.13f * Mathf.Sin((float)(s.Age * Mathf.Tau * 1.6));
                s.M.SetShaderParameter("p7_alpha", s.Age < P7Sample ? 0.85f : pulse);
                s.M.SetShaderParameter("p7_fade", 0.67f);
                if (s.Age > 12) (gone ??= new()).Add(id);
            }
        }
        if (gone != null) foreach (var id in gone) { var s = p7Scars[id]; if (IsInstanceValid(s.N)) s.N.QueueFree(); p7Scars.Remove(id); }
    }

    /* ------------------------------------------------------------ vow -- */

    void P7Vow(Ev.Brace e)
    {
        if (P7Off) return;
        P7WarmUp();
        switch (e.Phase)
        {
            case BracePhase.Start:
            {
                P7Ev("vow_start");
                var feet = V(e.X, Y(e.X, e.Z), e.Z);
                p7VowStart = time;
                // the shield slams down: one glint the data's px on it (3 frames), a pop of light, dust pressed out from
                // under her feet all round, two values
                P7Glint(P7ShieldAt(), P7D["vow.plant.flash_px"]);
                P7LightOn(P7ShieldAt(), 3f, Flare.Night ? 1.6f : 2.4f);
                P7Kick(feet, Vector3.Zero, P7D.Count("vow.plant.puffs", R()), P7D["kick.life"] * 1.3f);
                p7VowLevel = 0; p7VowBlows = 0; p7StoreAt = -9;
                P7VowShapesGone(0);
                p7DomeMesh ??= new SphereMesh { Radius = 1.2f, Height = 1.2f, IsHemisphere = true, RadialSegments = 64, Rings = 20 };
                // the dome: interior clear, a rim the data's px in from its outline (and where it meets the ground), its
                // core out; on each blow taken it flares to the flare px with the core in it for the flare's time
                float rim = P7D["vow.dome.rim_px"], flare = P7D["vow.dome.flare_px"], flareS = P7D["vow.dome.flare_s"];
                p7Dome = P7Brushed(rim, P7OnMesh(8, p7DomeMesh, feet, new Vector3(1, 1.55f, 1), 9999, step: s =>
                {
                    float gy = Y(PlayerPos.X, PlayerPos.Z);
                    s.N.GlobalPosition = new Vector3(PlayerPos.X, gy, PlayerPos.Z);
                    s.M.SetShaderParameter("p7_y0", gy + 0.02f);
                    s.M.SetShaderParameter("p7_t", s.Age);
                    bool hit = (float)(time - p7StoreAt) < flareS;
                    s.M.SetShaderParameter("p7_lvl", hit ? 0f : 0.34f);
                    s.M.SetShaderParameter("p7_width", hit ? flare : rim);
                    s.M.SetShaderParameter("p7_alpha", s.Age < P7Sample ? 0.6f : 0.95f);
                }));
                // the store: a round glow on the shield's face growing over the brace (the data's px), the ground light with it
                var spx = P7D.All("vow.store.px");
                float grow = P7D["vow.store.grow"];
                p7Glow = P7Quad(9, P7ShieldAt(), 0.1f, 9999, bill: true, top: true, step: s =>
                {
                    var at = P7ShieldAt();
                    s.N.GlobalPosition = at;
                    float t = (float)(time - p7VowStart), since = (float)(time - p7StoreAt);
                    float u = Mathf.Clamp(Mathf.Floor(t / P7Sample) * P7Sample / grow, 0, 1);
                    float px = Mathf.Lerp(spx[0], spx[1], u);
                    s.N.Scale = Vector3.One * 0.5f * px * P7Px(at);
                    s.M.SetShaderParameter("p7_lvl", since < P7Sample ? 0f : u < 0.5f ? 0.34f : 0f);
                    s.M.SetShaderParameter("p7_alpha", 0.92f);
                    if (p7VowLight != null)
                    {
                        p7VowLight.GlobalPosition = new Vector3(PlayerPos.X, Y(PlayerPos.X, PlayerPos.Z) + 0.55f, PlayerPos.Z);
                        p7VowLight.OmniRange = 2.2f + 1.2f * u;
                        p7VowLight.LightEnergy = (Flare.Night ? 0.45f : 0.75f) * (1 + 2 * u);
                    }
                });
                P7Brush(p7Glow.M, spx[0]);
                if (p7VowLight == null)
                {
                    p7VowLight = new OmniLight3D { ShadowEnabled = false, OmniAttenuation = 1.3f, LightColor = P7Band(1) };
                    AddChild(p7VowLight);
                }
                p7VowLight.Visible = true;
                break;
            }
            case BracePhase.Store:
            {
                P7Ev("vow_store");
                p7StoreAt = time;
                p7VowBlows++;
                p7VowLevel = P7StoreLevel(e.Stored);
                // a nick on the shield along the nearest attacker's blow (the sim's store names none: the nearest)
                if (b0 != null)
                {
                    var her = PlayerPos;
                    Vector3 best0 = default, best1 = default;
                    float d0 = 2.9f * 2.9f, d1 = d0;
                    foreach (var en in b0.Enemies.Living())
                    {
                        var (gx, gz) = CrowdView.Placed?.Invoke(en) ?? (en.X, en.Z);
                        var p = V(gx, Y(gx, gz) + 1.0, gz);
                        float d = new Vector2(p.X - her.X, p.Z - her.Z).LengthSquared();
                        if (d < d0) { d1 = d0; best1 = best0; d0 = d; best0 = p; }
                        else if (d < d1) { d1 = d; best1 = p; }
                    }
                    var sh = P7ShieldAt();
                    if (d0 < 2.9f * 2.9f) P7Nick(sh, sh - best0, P7D["storm.nick.px"]);
                }
                break;
            }
            case BracePhase.Burst:
            {
                P7Ev("vow_burst");
                p7VowAt = time;
                float k = P7StoreLevel(e.Stored);
                P7VowShapesGone(P7Sample);
                float r = (float)e.Radius;
                var c = V(e.X, Y(e.X, e.Z), e.Z);
                // one star off the shield (3 frames, sized by the store), one wavefront to the radius, then dust there; its
                // light a gold pop of 2 frames at the data's share (never the crowd bleached cream)
                int bf = (int)P7D["vow.burst.frames"];
                P7StarPx(P7ShieldAt(), P7D["vow.burst.px"] * (0.85f + 0.3f * k), P7D.Count("vow.burst.spikes", R()), P7D["vow.burst.root_px"], 0, 1, Math.Max(1, (bf - 1) / 2), true);
                float run = P7D["vow.burst.run"];
                P7Wave(c + Vector3.Up * 0.06f, r, run, P7D["vow.burst.lead_px"], P7D["vow.burst.trail_px"]);
                var dpx = P7D.All("leap.dust.px");
                WgLater(run - 0.04f, () => P7Dust(c, r * 1.05f, 12 + (int)(6 * k), dpx[0] * 0.8f, dpx[1] * 0.8f, 0.3f, r * 0.9f));
                P7LightOn(c + Vector3.Up * 1.3f, r * 1.3f, (Flare.Night ? 3f : 4.2f) * (0.8f + 0.5f * k) * P7D["vow.burst.light_k"], P7D["vow.burst.light_frames"] / 60f, 2 / 60f);
                P7Dust(c, r * 0.5f, 10 + (int)(4 * k), dpx[0] * 0.7f, dpx[1] * 0.7f, 0.3f, 0.3f);
                Cam?.JoltPx(Vector3.Up, 6f + 4f * k);
                break;
            }
        }
    }

    /// <summary>The dome and the glow: a sample at full, then gone (`after` s); the ground light down with them.</summary>
    void P7VowShapesGone(float after)
    {
        foreach (var sh in new[] { p7Dome, p7Glow })
        {
            if (sh == null) continue;
            if (after <= 0) { if (IsInstanceValid(sh.N)) sh.N.QueueFree(); p7Shapes.Remove(sh); continue; }
            float at = sh.Age; sh.Life = at + after;
            var st = sh.Step;
            sh.Step = s => { st?.Invoke(s); s.M.SetShaderParameter("p7_lvl", 0f); };
        }
        p7Dome = p7Glow = null;
        if (p7VowLight != null) p7VowLight.Visible = false;
    }

    /// <summary>A dust puff's lit top: held a third brighter (by night the tan sank under her pool's lit ground; by day,
    /// round 3, the r2 judge saw no dust at all on the verge's brown).</summary>
    Color P7Lit(float lit) => WgDust(lit * (Flare.Night ? 1.35f : 1.3f));

    /// <summary>The store as steps (0, then a quarter a step up to 1): the blows' kept fifths, 4, 10, 20, 35.</summary>
    static float P7StoreLevel(double stored) => stored >= 35 ? 1f : stored >= 20 ? 0.75f : stored >= 10 ? 0.5f : stored >= 4 ? 0.25f : stored > 0 ? 0.12f : 0f;

    Vector3 P7ShieldAt()
    {
        if (p7Shield == null || !IsInstanceValid(p7Shield) || !p7Shield.IsInsideTree())
        {
            p7Shield = null;
            if (Her3D != null && IsInstanceValid(Her3D))
                foreach (var n in Her3D.FindChildren("arm?*", "", true, false))
                    if (n is Node3D a && a.HasMeta("kind") && (int)a.GetMeta("kind") == (int)SurvivorUnchained.Play.WeaponKind.Shield) { p7Shield = a; break; }
        }
        if (p7Shield != null) return p7Shield.GlobalPosition + Vector3.Up * 0.05f;
        return PlayerPos + Vector3.Up * 1.15f;
    }

    /// <summary>A nick (mode 10): one three-band stroke `px` long at the play camera on `at`, along `dir` (world) as the
    /// screen sees it, 3 frames, over everything.</summary>
    void P7Nick(Vector3 at, Vector3 dir, float px)
    {
        int fr = (int)P7D["storm.nick.frames"];
        var s = P7Quad(10, at, 0.5f * px * P7Px(at), fr / 60f, bill: true, top: true, step: x =>
        {
            int f = (int)(x.Age * 60 + 1e-3f);
            x.M.SetShaderParameter("p7_fade", f <= 0 ? 0f : f == 1 ? 0.34f : 0.67f);
        });
        P7Brush(s.M, 0.24f * px);
        if (GetViewport()?.GetCamera3D() is { } cam && !cam.IsPositionBehind(at))
        {
            var d = cam.UnprojectPosition(at + dir.Normalized() * 0.5f) - cam.UnprojectPosition(at);
            if (d.LengthSquared() > 1e-4f) s.M.SetShaderParameter("p7_dir2", d.Normalized());
        }
    }

    /// <summary>Each frame: the smears, the storm's dust swirl and pool, the lines' seams.</summary>
    void StepP7Storm(float dt)
    {
        P7StepScars(dt);
        if (p7StormOn >= 0)
        {
            p7StormOn += dt;
            // the spin's sense from the blade's own angle round her
            var her = PlayerPos;
            var tip = P7BladeAt(1);
            float a = Mathf.Atan2(tip.Z - her.Z, tip.X - her.X);
            if (!float.IsNaN(p7SpinPrev))
            {
                float d = Mathf.Wrap(a - p7SpinPrev, -Mathf.Pi, Mathf.Pi);
                if (Mathf.Abs(d) > 0.02f) p7SpinDir = Mathf.Sign(d);
            }
            p7SpinPrev = a; p7SpinAngle = a;
        }
        P7StepSmears(dt);
        if (p7StormLight == null) return;
        if (p7StormOn >= 0)
        {
            p7StormLight.GlobalPosition = PlayerPos + Vector3.Up * 1.3f;
            p7StormLight.LightEnergy = Mathf.Min(1, p7StormOn / 0.15f) * (Flare.Night ? 1.3f : 2.0f);
            // the swirl: clusters of low puffs at her feet thrown round her way behind the blade, varied in size, a lit
            // top over a darker skirt
            p7Swirl -= dt;
            while (p7Swirl <= 0)
            {
                p7Swirl += 0.07f + R() * 0.05f;
                float ac = p7SpinAngle - p7SpinDir * (0.4f + R() * 1.4f), dc = 0.75f + R() * 0.55f;
                var feet = new Vector3(PlayerPos.X, Y(PlayerPos.X, PlayerPos.Z), PlayerPos.Z);
                int n = 2 + (int)(R() * 2.99f);
                float big = 0.7f + R() * 0.8f;
                for (int i = 0; i < n; i++)
                {
                    float a = ac + (R() - 0.5f) * 0.35f, d = dc + (R() - 0.5f) * 0.25f;
                    var o = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                    var tan = new Vector3(-o.Z, 0, o.X) * p7SpinDir;
                    float sz = (0.22f + R() * 0.16f) * big;
                    var v = tan * (2.4f + R() * 1.4f) + o * (0.7f + R() * 0.6f) + Vector3.Up * 0.08f;
                    WgPuff(feet + o * d + Vector3.Up * 0.2f, v, sz, 1.5f, 0.5f + R() * 0.25f, P7Lit(1.18f + R() * 0.12f), 0.88f, 3.2f);
                    if (i % 2 == 0) WgPuff(feet + o * d + Vector3.Up * 0.08f, v * 0.85f, sz * 1.15f, 1.4f, 0.45f + R() * 0.2f, WgDust(0.66f), 0.8f, 3.2f);
                }
            }
        }
        else if (p7StormLight.Visible)
        {
            p7StormLight.LightEnergy -= dt * 8;
            if (p7StormLight.LightEnergy <= 0) p7StormLight.Visible = false;
        }
    }
}

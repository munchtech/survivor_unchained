using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// P7 (rebuilt 9 Nov, lead 2's solver B, against judge r1): Bladestorm and Iron Vow in the FX language
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
                // sparks off the contact on the side facing her, along the blade's way (tangent, her spin's sense)
                P7Streak(at - rad * 0.3f, new Vector3(-rad.Z, 0, rad.X) * -p7SpinDir);
            }
            return true;
        }
        if (e.Art == "iron_vow" && time - p7VowAt < 0.2)
        {
            if (e.Target >= 0) { struckRims[e.Target] = Engine.GetFramesDrawn(); rimNoFlash.Remove(e.Target); }
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

    /// <summary>A star (mode 17): `spikes` tapered spikes round a solid core, one sample at its peak then a step down
    /// each sample (core, gold, amber, gone). Flat on the ground, or facing the camera over everything (`bill`).</summary>
    P7Shape P7Star(Vector3 at, float half, int spikes, float peak = P7Sample, bool bill = false, float step = P7Sample) =>
        P7Quad(17, at, half, peak + 3 * step, bill: bill, top: bill, step: s =>
        {
            s.M.SetShaderParameter("p7_count", (float)spikes);
            s.M.SetShaderParameter("p7_fade", s.Age < peak ? 0f : Mathf.Min(1f, (Mathf.Floor((s.Age - peak) / step) + 1) * 0.34f));
        });

    /// <summary>A ring (mode 16) running out to `r` in `run` s: its width share `w`, its along from `a0` (near) to `a1`
    /// (at the radius), its life from 0 to `l1`; gone the frame after it arrives.</summary>
    P7Shape P7Ring(Vector3 at, float r, float run, float w, float a0, float a1, float l1, float alpha) =>
        P7Quad(16, at, r, run + 1 / 60f, step: s =>
        {
            float t = Mathf.Clamp(s.Age / run, 0, 1), prog = 1 - (1 - t) * (1 - t);
            s.M.SetShaderParameter("p7_prog", prog);
            s.M.SetShaderParameter("p7_width", w);
            s.M.SetShaderParameter("p7_lvl", Mathf.Lerp(a0, a1, prog));
            s.M.SetShaderParameter("p7_fade", l1 * prog);
            s.M.SetShaderParameter("p7_alpha", alpha);
        });

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
                P7Glint(P7BladeAt(1), 0.5f);
                foreach (var sm in p7Smears) if (sm.DownAge < 0) sm.DownAge = 9;
                var tip = P7BladeAt(1);
                p7TiltPhi = Mathf.Atan2(tip.Z - PlayerPos.Z, tip.X - PlayerPos.X) + Mathf.Pi * 0.5f;
                // the blade's own smear, and its wake: thinner, lower, wider, lagging, at another tilt, without its core
                p7Smears.Add(P7NewSmear(Mathf.DegToRad(115), 1f, 1f, 0, 0, 17, 0.95f, 0f));
                p7Smears.Add(P7NewSmear(Mathf.DegToRad(70), 1.34f, 0.45f, 0.5f, -0.22f, -9, 0.78f, 0.34f));
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
        var n = new MeshInstance3D { Mesh = mesh, MaterialOverride = m, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
        AddChild(n);
        n.GlobalTransform = Transform3D.Identity;
        if (FxAfter.On) FxAfter.Adopt(n);
        m.SetShaderParameter("p7_alpha", alpha);
        m.SetShaderParameter("p7_fade", life0);
        return new P7Smear { N = n, Mesh = mesh, M = m, Arc = arc, RadK = radK, HwK = hwK, Lag = lag, Dy = dy, Tilt = tilt, Alpha = alpha, Life0 = life0 };
    }

    /// <summary>The smear's strip this frame: a band from 0.58 to 1 of the blade's reach, its head at the blade (a short
    /// round nose ahead of it), swept back round her over its arc on a plane leaning `Tilt` degrees.</summary>
    void P7BuildSmear(P7Smear s, float wind)
    {
        var her = PlayerPos;
        her.Y = Y(her.X, her.Z);
        var tip = P7BladeAt(1);
        float a = Mathf.Atan2(tip.Z - her.Z, tip.X - her.X);
        float rt = new Vector2(tip.X - her.X, tip.Z - her.Z).Length();
        float ro = Mathf.Clamp(rt * 1.1f, 1.15f, 1.5f) * s.RadK, ri = ro * 0.58f;
        float rc = (ro + ri) * 0.5f, hw = (ro - ri) * 0.5f * s.HwK;
        float h = Mathf.Clamp(tip.Y - her.Y, 0.45f, 1.5f) + s.Dy;
        float k = Mathf.Tan(Mathf.DegToRad(s.Tilt));
        float a0 = a - p7SpinDir * s.Lag, arc = s.Arc * wind;
        const int nose = 4, body = 26;
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
        if (Args.Has("clip") && p7StormOn > 0.5f && p7StormOn < 0.5f + 1 / 60f)
            GD.Print($"p7 smear arc {s.Arc:F2} rc {rc:F2} hw {hw:F2} h {h:F2} head {new Vector3(her.X, her.Y + h, her.Z) + new Vector3(Mathf.Cos(a0), 0, Mathf.Sin(a0)) * rc} vis {s.N.IsVisibleInTree()} layers {s.N.Layers}");
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
        P7Star(c + Vector3.Up * 0.05f, Mathf.Min(1.7f, r * 0.3f), 7);
        P7Ring(c + Vector3.Up * 0.06f, r, 0.18f, 0.04f + 0.012f * k, 1f, 0f, 0.3f, 0.95f);
        P7LightOn(c + Vector3.Up * 1.4f, r * 1.5f, (Flare.Night ? 2.6f : 4.5f) * (0.85f + 0.3f * k));
        P7DustRing(x, z, R() * Mathf.Tau, r * 0.95f, 26 + (int)(10 * k), 0.9f + 0.2f * k);
        int chunks = 7 + (int)(R() * 3.99f + 4 * k);
        for (int i = 0; i < chunks; i++)
        {
            float a = R() * Mathf.Tau, d = 0.4f + r * 0.3f * Mathf.Sqrt(R());
            var o = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            double px = x + o.X * d, pz = z + o.Z * d;
            WgThrow(V(px, Y(px, pz) + 0.2, pz), o * (1.5f + R() * 2.4f) + Vector3.Up * (3f + R() * 3f), 0.7f + R() * 0.35f, 1.7f + R() * 0.5f, 5);
        }
        Cam?.JoltPx(Vector3.Up, 9f + 3 * k);
    }

    /// <summary>A low dust ring rolling out to `reach` in 0.4 s, in clusters (never an even chain of like puffs): each
    /// cluster 2-6 puffs of varied size, a lit top over a darker skirt (matter, two values), some stretches bare.</summary>
    void P7DustRing(double x, double z, float a0, float reach, int puffs, float sizeK)
    {
        const float drag = 4.5f;
        int clusters = Math.Max(4, puffs / 4);
        for (int c = 0; c < clusters; c++)
        {
            float ac = a0 + (c + R() * 0.7f) / clusters * Mathf.Tau;
            int n = 2 + (int)(R() * 4.99f);
            float big = 0.7f + R() * 0.7f;
            for (int i = 0; i < n; i++)
            {
                float a = ac + (R() - 0.5f) * 0.32f, d0 = 0.35f + R() * 0.35f;
                var o = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                float rr = reach * (0.86f + R() * 0.2f) - d0;
                float v0 = rr * drag / (1 - Mathf.Exp(-drag * 0.4f));
                double px = x + o.X * d0, pz = z + o.Z * d0;
                float sz = (0.2f + R() * 0.2f) * sizeK * big;
                WgPuff(V(px, Y(px, pz) + 0.22, pz), o * v0 + Vector3.Up * (0.05f + R() * 0.15f), sz, 1.4f, 0.75f + R() * 0.35f, P7Lit(1.0f + R() * 0.14f), 0.8f, drag);
                if (R() < 0.65f) WgPuff(V(px, Y(px, pz) + 0.1, pz), o * v0 * 0.85f, sz * (1.0f + R() * 0.3f), 1.3f, 0.7f + R() * 0.25f, WgDust(0.68f), 0.76f, drag);
            }
        }
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
                const float hwMax = 0.15f;
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
                m.SetShaderParameter("p7_width", 0.38f);
                m.SetShaderParameter("p7_alpha", 0.5f);
                m.SetShaderParameter("p7_fade", 0f);
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
                            if (WgDecalOn(pos, theta, new Vector3(seg * 1.03f, 1.6f, WgBand * across), alb[tile], nrm[tile], null, 14f, 1f, 0, 0, 0, WgLineTint) is not { } d) return;
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
                            WgThrow(p + Vector3.Up * 0.05f, v, 0.55f + R() * 0.4f, 1.4f + R() * 0.5f);
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
                // the flare (0.1 s at its widest, the core in it), then a step a stretch: gold, amber, gone
                s.M.SetShaderParameter("p7_alpha", 1f);
                s.M.SetShaderParameter("p7_width", t < 0.1f ? 1f : t < 0.3f ? 0.8f : 0.66f);
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
                // the shield slams down: a small star on it for 0.10 s and a pop of light
                P7Star(P7ShieldAt(), 0.5f, 5, 0.04f, bill: true, step: 0.02f);
                P7LightOn(P7ShieldAt(), 3f, Flare.Night ? 1.6f : 2.4f);
                // the plant: dust pressed out from under her feet in clusters, low, two values
                int cl = 3 + (int)(R() * 1.99f);
                float a0 = R() * Mathf.Tau;
                for (int c = 0; c < cl; c++)
                {
                    float ac = a0 + (c + R() * 0.6f) / cl * Mathf.Tau;
                    int n = 3 + (int)(R() * 2.99f);
                    for (int i = 0; i < n; i++)
                    {
                        float a = ac + (R() - 0.5f) * 0.5f;
                        var o = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                        float sz = 0.16f + R() * 0.2f;
                        bool lit = i % 3 != 2;
                        WgPuff(feet + o * (0.25f + R() * 0.15f) + Vector3.Up * (lit ? 0.14f : 0.07f), o * (2.0f + R() * 1.6f) + Vector3.Up * 0.12f, sz, 1.5f, 0.55f + R() * 0.3f, (lit ? P7Lit(1.04f) : WgDust(0.7f)), 0.8f, 4.5f);
                    }
                }
                p7VowLevel = 0; p7VowBlows = 0; p7StoreAt = -9;
                P7VowShapesGone(0);
                p7DomeMesh ??= new SphereMesh { Radius = 1.2f, Height = 1.2f, IsHemisphere = true, RadialSegments = 48, Rings = 16 };
                p7Dome = P7OnMesh(8, p7DomeMesh, feet, new Vector3(1, 1.55f, 1), 9999, step: s =>
                {
                    s.N.GlobalPosition = new Vector3(PlayerPos.X, Y(PlayerPos.X, PlayerPos.Z), PlayerPos.Z);
                    s.M.SetShaderParameter("p7_t", s.Age);
                    float since = (float)(time - p7StoreAt);
                    // comes in over a sample; an amber rim only; a sample at full (the core in it) on each blow taken
                    float life = s.Age < P7Sample ? 0.85f : since < P7Sample ? 0f : since < 2 * P7Sample ? 0.4f : 0.72f;
                    s.M.SetShaderParameter("p7_lvl", life);
                    s.M.SetShaderParameter("p7_width", (since < P7Sample ? 0.85f : 0.55f) + 0.08f * p7VowLevel);
                    s.M.SetShaderParameter("p7_alpha", 0.9f);
                });
                p7Glow = P7Quad(9, P7ShieldAt(), 0.14f, 9999, bill: true, top: true, step: s =>
                {
                    s.N.GlobalPosition = P7ShieldAt();
                    float t = (float)(time - p7VowStart), since = (float)(time - p7StoreAt);
                    // ~3x over the brace in four steps, a step more for each blow kept (capped), a sample larger on one
                    float g = 1 + 2 * Mathf.Min(1, Mathf.Floor(t / 0.55f) / 4) + Mathf.Min(0.6f, 0.1f * p7VowBlows);
                    s.N.Scale = Vector3.One * 0.17f * g * (since < P7Sample ? 1.2f : 1f);
                    s.M.SetShaderParameter("p7_lvl", since < P7Sample || g >= 2.2f ? 0f : 0.36f);
                    s.M.SetShaderParameter("p7_t", since);
                    s.M.SetShaderParameter("p7_alpha", 0.92f);
                    if (p7VowLight != null)
                    {
                        p7VowLight.GlobalPosition = new Vector3(PlayerPos.X, Y(PlayerPos.X, PlayerPos.Z) + 0.55f, PlayerPos.Z);
                        p7VowLight.OmniRange = 2.2f + 0.35f * g;
                        p7VowLight.LightEnergy = (Flare.Night ? 0.45f : 0.75f) * g;
                    }
                });
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
                // sparks streak from the nearest attackers into the shield (the sim's store names none: the nearest)
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
                    if (d0 < 2.9f * 2.9f) P7StreakTo(best0, sh);
                    if (d1 < 2.9f * 2.9f) P7StreakTo(best1, sh);
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
                // the star off the shield (sized by the store), over her for its one sample, then stepping down
                P7Star(P7ShieldAt(), 0.8f + 0.6f * k, 7, P7Sample, bill: true);
                // the ring: narrows to a fifth of its width and dies by the radius; then it breaks into dust there
                const float run = 0.3f;
                P7Ring(c + Vector3.Up * 0.06f, r, run, 0.07f + 0.03f * k, 1f, 0.12f, 0.9f, 0.95f);
                WgLater(run - 0.04f, () => P7DustAt(e.X, e.Z, r, 9 + (int)(5 * k)));
                P7LightOn(c + Vector3.Up * 1.3f, r * 1.3f, (Flare.Night ? 3f : 4.2f) * (0.8f + 0.5f * k));
                P7DustRing(e.X, e.Z, R() * Mathf.Tau, r * 0.5f, 10 + (int)(6 * k), 0.75f);
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

    /// <summary>Dust thrown up where a ring broke: clusters on the circle of radius `r`, drifting out, two values.</summary>
    void P7DustAt(double x, double z, float r, int clusters)
    {
        float a0 = R() * Mathf.Tau;
        for (int c = 0; c < clusters; c++)
        {
            float ac = a0 + (c + R() * 0.75f) / clusters * Mathf.Tau;
            int n = 2 + (int)(R() * 3.99f);
            for (int i = 0; i < n; i++)
            {
                float a = ac + (R() - 0.5f) * 0.18f, d = r * (0.94f + R() * 0.1f);
                var o = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                double px = x + o.X * d, pz = z + o.Z * d;
                float sz = 0.18f + R() * 0.26f;
                bool lit = R() < 0.6f;
                WgPuff(V(px, Y(px, pz) + (lit ? 0.2 : 0.09), pz), o * (0.8f + R() * 0.9f) + Vector3.Up * (lit ? 0.35f : 0.08f), sz, 1.6f, 0.6f + R() * 0.3f, (lit ? P7Lit(1.04f) : WgDust(0.7f)), 0.78f, 3f);
            }
        }
    }

    /// <summary>A dust puff's lit top: by night held a third brighter (the night tan sank under her pool's lit ground).</summary>
    Color P7Lit(float lit) => WgDust(Flare.Night ? lit * 1.35f : lit);

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

    /// <summary>A struck foe's tangential sparks: tears flung along `dir` (world, flat) as the screen sees it.</summary>
    void P7Streak(Vector3 at, Vector3 dir)
    {
        var s = P7Quad(10, at, 0.6f, 3 * P7Sample, bill: true, top: true, step: x => x.M.SetShaderParameter("p7_t", x.Age));
        if (GetViewport()?.GetCamera3D() is { } cam && !cam.IsPositionBehind(at))
        {
            var d = cam.UnprojectPosition(at + dir * 0.5f) - cam.UnprojectPosition(at);
            if (d.LengthSquared() > 1e-4f) s.M.SetShaderParameter("p7_dir2", d.Normalized());
        }
    }

    /// <summary>Sparks streaking from `from` into `to` (an attacker's blow into her shield).</summary>
    void P7StreakTo(Vector3 from, Vector3 to)
    {
        float dist = Mathf.Clamp(from.DistanceTo(to), 0.4f, 2.4f);
        var s = P7Quad(10, from, dist, 3 * P7Sample, bill: true, top: true, step: x => x.M.SetShaderParameter("p7_t", x.Age));
        if (GetViewport()?.GetCamera3D() is { } cam && !cam.IsPositionBehind(from) && !cam.IsPositionBehind(to))
        {
            var d = cam.UnprojectPosition(to) - cam.UnprojectPosition(from);
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

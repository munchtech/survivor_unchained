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
    /// <summary>A storm line's fissure. (lane E lead 7 r2, 17 Nov) One per path: a line thrown on a pending scar's path joins
    /// it (P7Line, P7ScarOn) and the scar holds every line id mapped onto it, kept while any of them is pending (Live).</summary>
    sealed class P7Scar
    {
        public required MeshInstance3D N;
        public required ShaderMaterial M;
        public Vector2 From, Dir;
        public float Len;
        public readonly List<int> Ids = new();
        public readonly HashSet<int> Live = new();
        // Hot: since the last line thrown onto it (its white-hot sample, the pending clock)
        public float Age, Hot, SplitAge = -1, FadeAge = -1;
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
    OmniLight3D? p7StormLight;
    double p7StormOff = -9;
    float p7StormR, p7StormOn = -1, p7SpinPrev = float.NaN, p7SpinDir = -1, p7Swirl, p7SpinAngle, p7TiltPhi;
    // (bladestorm-spin r2) the storm's count: a ring's arcs turn with their own storm only (P7StormRing)
    int p7StormGen;
    // the frame's storm work (P7Pre): a tick or start in this batch; a break in it; how many tick kits drawn
    bool p7TickNow, p7BreakNow;
    int p7TickKits;
    double p7VowAt = -9, p7VowStart = -9, p7StoreAt = -9;
    float p7VowLevel;
    int p7VowBlows;
    // the scars drawn (p7ScarList) and each line id's scar (p7Scars: several ids may share one)
    readonly Dictionary<int, P7Scar> p7Scars = new();
    readonly List<P7Scar> p7ScarList = new();
    Node3D? p7Shield;

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
                p7SpinAngle = p7TiltPhi - Mathf.Pi * 0.5f;
                // ONE smear: the blade's own path at its reach (round 3: the wake smear parked beside her is gone)
                p7Smears.Add(P7NewSmear(Mathf.DegToRad(P7D["storm.smear.arc_deg"]), 1f, 1f, 0, 0, 12, P7D["storm.smear.alpha"], 0f));
                // (bladestorm-spin r2, E rule 5: a full ring) the storm's ring, painted (round 1's stroke arcs retired)
                P7StormRing();
                // (r2) its light only if the data asks (storm.light 0: the painted ring is the read, no light, no glow)
                if (P7D["storm.light"] > 0)
                {
                    if (p7StormLight == null)
                    {
                        p7StormLight = new OmniLight3D { ShadowEnabled = false, OmniAttenuation = 1.1f, LightColor = P7Band(1) };
                        AddChild(p7StormLight);
                    }
                    p7StormLight.OmniRange = Mathf.Min(p7StormR * 1.2f, 4.2f);
                    p7StormLight.Visible = true;
                }
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

    /// <summary>(bladestorm-spin r2, 16 Nov: E rule 5) The storm's ring: `n` painted arcs (PaintedRing's brush, RingPaint and
    /// shaders/fx_sunder_ring.gdshader, by the numbers under p7.storm.ring_paint) evenly round her on the ground at the
    /// storm's real hit radius (Ev.Spin Radius, x rad_k), held while she spins and turning with the blade: arc i's head
    /// trails the blade's angle round her by lag_deg + i/n of the turn, its tail arc_deg back against the spin (shorter
    /// as the spin winds up, as the smear's). Its head is white-hot (the lip, over head_hot of the arc), then the steel
    /// bands, cooling (cut_along) and drying out (fade_along) toward the tail (the shader's ring_along); a fresh brush each
    /// relay_turns turns (one of `brushes`); it grows from `from` x the radius in `run` s and erodes away where it stands in
    /// `out` s once its storm ends or breaks. Anchored on her (PlayerPos) and the blade's angle round her (P7BladeAt). No
    /// light, no sound of its own (storm_start is its birth).</summary>
    void P7StormRing()
    {
        const string key = "storm.ring_paint";
        int gen = ++p7StormGen, n = Math.Max(1, (int)P7D[key + ".n"]);
        var rk = P7D.All(key + ".rad_k");
        var cut = P7D.All(key + ".cut_along");
        var fade = P7D.All(key + ".fade_along");
        float arc = Mathf.DegToRad(Mathf.Min(P7D[key + ".arc_deg"], P7D[key + ".open_deg"])), lag = Mathf.DegToRad(P7D[key + ".lag_deg"]);
        float from = P7D[key + ".from"], run = Mathf.Max(P7D[key + ".run"], 1 / 60f), outS = Mathf.Max(P7D[key + ".out"], 1 / 60f);
        float lift = P7D[key + ".lift"], relay = Mathf.Tau * Mathf.Max(P7D[key + ".relay_turns"], 0.1f), r = p7StormR;
        var tex = PaintedRingTex(key);
        int t0 = (int)(R() * 0.999f * tex.Length);
        var shader = GD.Load<Shader>(SunderRingShader);
        p7Plane ??= new PlaneMesh { Size = new Vector2(2, 2) };
        if (GripSay) GD.Print($"storm ring frame {Engine.GetFramesDrawn()} r {r:0.00} m = {r / P7Px(PlayerPos):0} px arcs {n} x {Mathf.RadToDeg(arc):0} deg");
        for (int i = 0; i < n; i++)
        {
            var m = new ShaderMaterial { Shader = shader };
            FxCel.Apply(m, School.Physical, FxAfter.On);
            int ti = (t0 + i) % tex.Length;
            m.SetShaderParameter("ring_tex", tex[ti]);
            m.SetShaderParameter("ring_r0", SunderR0);
            m.SetShaderParameter("ring_hot", 0f);
            m.SetShaderParameter("ring_core", P7D[key + ".core_cut"]);
            m.SetShaderParameter("ring_along", 1f);
            m.SetShaderParameter("along_hot", P7D[key + ".head_hot"]);
            m.SetShaderParameter("along_cut", new Vector2(cut[0], cut[1]));
            m.SetShaderParameter("along_fade", new Vector3(fade[0], fade[1], fade[2]));
            var node = new MeshInstance3D { Mesh = p7Plane, MaterialOverride = m, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, Name = "StormRing" };
            AddChild(node);
            if (FxAfter.On) FxAfter.Adopt(node);
            float lagI = lag + Mathf.Tau * i / n, radK = rk[i % rk.Length], down = -1, turned = 0, prev = float.NaN;
            var s = new P7Shape
            {
                N = node, M = m, Life = 1e6f,
                Step = q =>
                {
                    bool on = p7StormOn >= 0 && p7StormGen == gen;
                    if (!on && down < 0) down = q.Age;
                    if (on)
                    {
                        // a fresh brush each relay of the blade's turning round her
                        if (!float.IsNaN(prev)) turned += Mathf.Abs(Mathf.Wrap(p7SpinAngle - prev, -Mathf.Pi, Mathf.Pi));
                        prev = p7SpinAngle;
                        if (turned >= relay) { turned -= relay; ti = (ti + 1) % tex.Length; q.M.SetShaderParameter("ring_tex", tex[ti]); }
                        float span = arc * Mathf.Clamp(q.Age / 0.15f, 0.25f, 1f), dir = p7SpinDir < 0 ? -1f : 1f;
                        float head = p7SpinAngle - dir * lagI;
                        var her = PlayerPos;
                        her.Y = Y(her.X, her.Z) + lift;
                        q.N.GlobalPosition = her;
                        // local +X at the arc's middle; u runs with the spin, so the head is at u 1
                        q.N.Rotation = new Vector3(0, -(head - dir * span / 2), 0);
                        q.M.SetShaderParameter("ring_range", span);
                        q.M.SetShaderParameter("ring_flip", dir);
                    }
                    float t = Mathf.Clamp(q.Age / run, 0, 1), e = 1 - (1 - t) * (1 - t);
                    q.N.Scale = Vector3.One * r * radK * (from + (1 - from) * e);
                    q.M.SetShaderParameter("ring_fade", down < 0 ? 0f : 1.02f * Mathf.Clamp((q.Age - down) / outS, 0, 1));
                    if (down >= 0 && q.Age - down >= outS) q.Life = q.Age;
                },
            };
            s.Step(s);
            p7Shapes.Add(s);
        }
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

    /// <summary>A Sunder line the storm threw: a painted ground fissure (P7Fissure). Thrown: laid from her end over
    /// storm.line.open s, its seam white-hot a sample then gold over amber, breathing; split: the seam flares white-hot, dust
    /// and chunks along the whole line within 0.1 s, the seam cools in steps (storm.seam.cool) and the gap breaks up where
    /// it lies (storm.line.life); faded: the seam steps out and the gap breaks up, nothing dealt.</summary>
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
        int n = Math.Clamp((int)Mathf.Round(len / 1.0f), 4, 8);
        const int t0 = 2;
        const float across = 0.7f;
        switch (e.Phase)
        {
            case SpinLinePhase.Thrown:
            {
                P7Ev("line_thrown");
                if (p7Scars.Remove(e.Id, out var old)) P7ScarDrop(old, e.Id);
                // (r2) a line thrown on a pending scar's path (she stood still: the storm throws one every heavy tick, each with
                // its own seed; r1's frames braided two or three fissures and seams on one path) draws no second fissure: its
                // id joins that scar, whose seam goes white-hot a sample again
                if (P7ScarOn(from, dir, len) is { } on)
                {
                    on.Ids.Add(e.Id);
                    on.Live.Add(e.Id);
                    on.Hot = 0;
                    on.FadeAge = -1;
                    p7Scars[e.Id] = on;
                    if (Args.Has("clip")) GD.Print($"p7line joins scar of {on.Ids[0]} ({on.Ids.Count} ids) frame {Engine.GetFramesDrawn()}");
                    break;
                }
                // (lane E lead 7, 17 Nov) the fissure: one painted strip on the crack's path (P7Fissure, mode 18), not the
                // crack decals (a soft dark smear at the den camera) and their 1 px seam
                var sc = P7Fissure(from, dir, side, len, t0, n, across);
                sc.From = from;
                sc.Dir = dir;
                sc.Len = len;
                sc.Ids.Add(e.Id);
                sc.Live.Add(e.Id);
                p7Scars[e.Id] = sc;
                p7ScarList.Add(sc);
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
                sc.Live.Remove(e.Id);
                // one burst a drawn fissure: the lines mapped onto it split in the same break; on the path it was laid on
                if (sc.SplitAge >= 0) break;
                sc.SplitAge = 0;
                sc.FadeAge = -1;
                from = sc.From;
                dir = sc.Dir;
                len = sc.Len;
                side = new Vector2(-dir.Y, dir.X);
                n = Math.Clamp((int)Mathf.Round(len / 1.0f), 4, 8);
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
                // kept while any line mapped onto it is pending
                if (p7Scars.TryGetValue(e.Id, out var sf) && sf.Live.Remove(e.Id) && sf.Live.Count == 0 && sf.SplitAge < 0 && sf.FadeAge < 0) sf.FadeAge = 0;
                break;
        }
    }

    /// <summary>(r2) The pending scar a line thrown from `from` along `dir` lands on: her end within stack[0] m, its way within
    /// stack[1] degrees, its length within stack[2] m (p7.storm.line.stack). A scar whose last line faded in this same batch
    /// (the sim fades its oldest line as it throws one past MaxLines) is still pending.</summary>
    P7Scar? P7ScarOn(Vector2 from, Vector2 dir, float len)
    {
        var k = P7D.All("storm.line.stack");
        float cos = Mathf.Cos(Mathf.DegToRad(k[1]));
        foreach (var s in p7ScarList)
            if (s.SplitAge < 0 && s.FadeAge <= 0 && IsInstanceValid(s.N) && s.From.DistanceTo(from) <= k[0] && s.Dir.Dot(dir) >= cos && Mathf.Abs(s.Len - len) <= k[2])
                return s;
        return null;
    }

    /// <summary>A line id leaves its scar (a reused id): the scar goes when no line is mapped onto it.</summary>
    void P7ScarDrop(P7Scar s, int id)
    {
        s.Ids.Remove(id);
        s.Live.Remove(id);
        if (s.Ids.Count > 0) return;
        P7ScarGone(s);
        p7ScarList.Remove(s);
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
    }

    /// <summary>(lane E lead 7, 17 Nov) A storm line's fissure (fx_p7_b mode 18; p7.storm.line, p7.storm.seam): one strip on
    /// the crack's path (P7CrackAt), lying on the ground, its UV in px at the play camera (x along from her end, y across)
    /// so the shader draws a hard-edged jagged gap, lit wall and lip, branches and the hot seam to the px.</summary>
    P7Scar P7Fissure(Vector2 from, Vector2 dir, Vector2 side, float len, int t0, int n, float across)
    {
        var cam = GetViewport()?.GetCamera3D();
        float vk = 1080f / Math.Max(1f, GetViewport()?.GetVisibleRect().Size.Y ?? 1080f);
        float hwPx = P7D["storm.line.strip_px"], lift = P7D["storm.line.lift"];
        int K = Math.Max(12, (int)(len / 0.15f));
        var pts = new Vector3[K + 1];
        for (int j = 0; j <= K; j++) pts[j] = P7CrackAt(from, dir, side, len * j / K, len, t0, n, across);
        var mesh = new ImmediateMesh();
        mesh.SurfaceBegin(Mesh.PrimitiveType.TriangleStrip);
        float apx = 0, lit = 0, vis = -1;
        var view = (GetViewport()?.GetVisibleRect().Size ?? new Vector2(1920, 1080)) * vk;
        Vector2 sp0 = Vector2.Zero;
        for (int j = 0; j <= K; j++)
        {
            var p = pts[j];
            var tg = pts[Math.Min(K, j + 1)] - pts[Math.Max(0, j - 1)];
            var s3 = new Vector3(-tg.Z, 0, tg.X).Normalized();
            Vector2 sp, ds;
            bool seen = true;
            if (cam != null && !cam.IsPositionBehind(p))
            {
                sp = cam.UnprojectPosition(p) * vk;
                ds = (cam.UnprojectPosition(p + s3 * 0.25f) * vk - sp) / 0.25f;
                seen = sp.X >= 0 && sp.Y >= 0 && sp.X <= view.X && sp.Y <= view.Y;
            }
            else
            {
                float k = 1f / P7Px(p);
                sp = new Vector2(p.X, p.Z) * k;
                ds = new Vector2(s3.X, s3.Z) * k;
                seen = cam == null;
            }
            if (j > 0) apx += (sp - sp0).Length();
            sp0 = sp;
            // the visible part: px along to the first point off the screen
            if (!seen && vis < 0) vis = apx;
            // the lit side: the across that faces the screen's lower right (the painted key from the upper left)
            if (j == K / 2) lit = ds.X + ds.Y >= 0 ? 1 : -1;
            float hw = hwPx / Math.Max(ds.Length(), 1f);
            var q = p + Vector3.Up * lift;
            mesh.SurfaceSetUV(new Vector2(apx, -hwPx));
            mesh.SurfaceAddVertex(q - s3 * hw);
            mesh.SurfaceSetUV(new Vector2(apx, hwPx));
            mesh.SurfaceAddVertex(q + s3 * hw);
        }
        mesh.SurfaceEnd();
        // (r2) the taper by screen px: the gap reaches its end width taper[0] px inside the screen's edge when the line runs
        // off it (r1's 715 px line tapered over its whole length: about 4 px where it left the screen), over at least taper[1]
        // of the visible part; a line wholly on screen tapers over its length
        var tp = P7D.All("storm.line.taper");
        float tpx = vis < 0 ? apx : Mathf.Clamp(vis - tp[0], tp[1] * vis, apx);
        var m = P7Mat(18);
        m.SetShaderParameter("p7_rpx", apx);
        m.SetShaderParameter("p7_tpx", tpx);
        m.SetShaderParameter("p7_lit", lit);
        m.SetShaderParameter("p7_gap", P7V4("storm.line.gap"));
        m.SetShaderParameter("p7_jag", P7V4("storm.line.jag"));
        m.SetShaderParameter("p7_brn", P7V4("storm.line.branch"));
        m.SetShaderParameter("p7_lip", P7V4("storm.line.lip"));
        var sm = P7D.All("storm.seam.shape");
        m.SetShaderParameter("p7_seam", new Vector4(P7D["storm.seam.px"], sm[0], sm[1], sm[2]));
        m.SetShaderParameter("p7_sbrk", P7V4("storm.seam.breaks"));
        m.SetShaderParameter("p7_deep", P7Oklch("storm.line.deep"));
        m.SetShaderParameter("p7_wall", P7Oklch("storm.line.wall"));
        m.SetShaderParameter("p7_lipc", P7Oklch("storm.line.lip_lch"));
        m.SetShaderParameter("p7_open", 0f);
        m.SetShaderParameter("p7_erode", 0f);
        m.SetShaderParameter("p7_fade", 0f);
        m.SetShaderParameter("p7_alpha", 1f);
        var node = new MeshInstance3D { Mesh = mesh, MaterialOverride = m, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
        AddChild(node);
        node.GlobalTransform = Transform3D.Identity;
        if (FxAfter.On) FxAfter.Adopt(node);
        if (Args.Has("clip") && cam != null)
            GD.Print($"p7line fissure {apx:F0}px long, visible {(vis < 0 ? apx : vis):F0}px, taper {tpx:F0}px, strip {2 * hwPx:F0}px, lit {lit:+0;-0}, from {cam.UnprojectPosition(pts[0]) * vk:F0} to {cam.UnprojectPosition(pts[K]) * vk:F0} frame {Engine.GetFramesDrawn()}");
        return new P7Scar { N = node, M = m };
    }

    static Vector4 P7V4(string key) { var a = P7D.All(key); return new Vector4(a[0], a.Length > 1 ? a[1] : 0, a.Length > 2 ? a[2] : 0, a.Length > 3 ? a[3] : 0); }

    /// <summary>An Oklab L, C, h (degrees) from the data as a linear color (drawn after the grade: its displayed color).</summary>
    static Vector3 P7Oklch(string key)
    {
        var a = P7D.All(key);
        float L = a[0], C = a[1], h = Mathf.DegToRad(a[2]);
        float A = C * Mathf.Cos(h), B = C * Mathf.Sin(h);
        float l = L + 0.3963377774f * A + 0.2158037573f * B, mm = L - 0.1055613458f * A - 0.0638541728f * B, s = L - 0.0894841775f * A - 1.2914855480f * B;
        l = l * l * l; mm = mm * mm * mm; s = s * s * s;
        return new Vector3(
            Mathf.Clamp(4.0767416621f * l - 3.3077115913f * mm + 0.2309699292f * s, 0, 1),
            Mathf.Clamp(-1.2684380046f * l + 2.6097574011f * mm - 0.3413193965f * s, 0, 1),
            Mathf.Clamp(-0.0041960863f * l - 0.7034186147f * mm + 1.7076147010f * s, 0, 1));
    }

    /// <summary>A stepped share: 0 before `from` s, then a step every sample to 1 at `to` s.</summary>
    static float P7Stepped(float t, float from, float to) =>
        t < from ? 0 : Mathf.Clamp((Mathf.Floor((t - from) / P7Sample) + 1) * P7Sample / Mathf.Max(to - from, P7Sample), 0, 1);

    void P7StepScars(float dt)
    {
        float open = P7D["storm.line.open"];
        var cool = P7D.All("storm.seam.cool");
        var life = P7D.All("storm.line.life");
        var pulse = P7D.All("storm.seam.pulse");
        // each scar once, however many line ids are mapped onto it
        for (int i = p7ScarList.Count - 1; i >= 0; i--)
        {
            var s = p7ScarList[i];
            bool gone;
            s.Age += dt;
            s.Hot += dt;
            s.M.SetShaderParameter("p7_open", Mathf.Clamp(s.Age / Mathf.Max(open, 1e-3f), 0, 1));
            if (s.SplitAge >= 0)
            {
                s.SplitAge += dt;
                float t = s.SplitAge;
                // split: the flare in heat, never in width (white-hot, then a step a stretch: gold, amber, out); the gap
                // holds, then breaks up where it lies in steps (life[0]..life[1] s)
                s.M.SetShaderParameter("p7_alpha", 1f);
                s.M.SetShaderParameter("p7_fade", t < cool[0] ? 0f : t < cool[1] ? 1 / 3f : t < cool[2] ? 2 / 3f : 1f);
                s.M.SetShaderParameter("p7_erode", P7Stepped(t, life[0], life[1]));
                gone = t > life[1];
            }
            else if (s.FadeAge >= 0)
            {
                // faded (nothing dealt): the seam steps down to amber, then out; the gap breaks up over life[2] s
                s.FadeAge += dt;
                s.M.SetShaderParameter("p7_fade", s.FadeAge < P7Sample ? 2 / 3f : 1f);
                s.M.SetShaderParameter("p7_erode", P7Stepped(s.FadeAge, 0, life[2]));
                gone = s.FadeAge > life[2];
            }
            else
            {
                // pending: white-hot for a sample as it tears open (and as each line lands on it), then gold over amber,
                // breathing (pulse: base, swing, Hz); a lost event's scar goes 12 s after its last line
                s.M.SetShaderParameter("p7_fade", s.Hot < P7Sample ? 0f : 1 / 3f);
                s.M.SetShaderParameter("p7_alpha", s.Hot < P7Sample ? 1f : pulse[0] + pulse[1] * Mathf.Sin((float)(s.Age * Mathf.Tau * pulse[2])));
                gone = s.Hot > 12;
            }
            if (!gone) continue;
            P7ScarGone(s);
            foreach (var id in s.Ids) if (p7Scars.TryGetValue(id, out var m) && m == s) p7Scars.Remove(id);
            p7ScarList.RemoveAt(i);
        }
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
                // (leap-vow-marks, 16 Nov: coordinator #15) the plant: one faint steel glint on her shield (3 frames; the shield
                // piece's own node, P7ShieldAt) and dust pressed out from under her feet all round, two values; nothing else
                // through the brace. The even gold circle (the dome's rim), the gold dot (the store glow: a flat disc on her
                // chest at the play camera, not the shield's own metal), the cream glowing dome and the gold ground light are
                // gone (b0, the lead's look: a sticker and a white-out tube)
                P7Glint(P7ShieldAt(), P7D["vow.plant.flash_px"]);
                P7Kick(feet, Vector3.Zero, P7D.Count("vow.plant.puffs", R()), P7D["kick.life"] * 1.3f);
                p7VowLevel = 0; p7VowBlows = 0; p7StoreAt = -9;
                if (GripSayAll) GD.Print($"vow start frame {Engine.GetFramesDrawn()}");
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
                float r = (float)e.Radius;
                var c = V(e.X, Y(e.X, e.Z), e.Z);
                // (leap-vow-marks, 16 Nov: coordinator #15) Sunder's painted ring, closed, out to the burst's real radius
                // (PaintedRing, p7.vow.mark: white-hot, then the steel bands, gone ~0.4 s), then dust there and round her
                // feet. The star off the shield, the old even wavefront and the light's pop are gone (stickers, a wash)
                PaintedRing("vow.mark", c + Vector3.Up * 0.06f, r, Mathf.Tau, R() * Mathf.Tau);
                p7MarkHold = time + P7D["vow.mark.life"];
                if (GripSayAll && GetViewport()?.GetCamera3D() is { } cam)
                {
                    var sp = cam.UnprojectPosition(c) * (1080f / Math.Max(1f, GetViewport().GetVisibleRect().Size.Y));
                    GD.Print($"vow mark frame {Engine.GetFramesDrawn()} at {sp.X:0},{sp.Y:0} reach {r:0.00} m = {r / P7Px(c):0} px store {k:0.00}");
                }
                float run = P7D["vow.mark.run"];
                var dpx = P7D.All("leap.dust.px");
                WgLater(Mathf.Max(0, run - 0.04f), () => P7Dust(c, r * 1.05f, 12 + (int)(6 * k), dpx[0] * 0.8f, dpx[1] * 0.8f, 0.3f, r * 0.9f));
                P7Dust(c, r * 0.5f, 10 + (int)(4 * k), dpx[0] * 0.7f, dpx[1] * 0.7f, 0.3f, 0.3f);
                Cam?.JoltPx(Vector3.Up, 6f + 4f * k);
                break;
            }
        }
    }

    /// <summary>A dust puff's lit top: held a third brighter (by night the tan sank under her pool's lit ground; by day,
    /// round 3, the r2 judge saw no dust at all on the verge's brown).</summary>
    Color P7Lit(float lit) => WgDust(lit * (Flare.Night ? 1.35f : 1.3f));

    /// <summary>The store as steps (0, then a quarter a step up to 1): the blows' kept fifths, 4, 10, 20, 35.</summary>
    static float P7StoreLevel(double stored) => stored >= 35 ? 1f : stored >= 20 ? 0.75f : stored >= 10 ? 0.5f : stored >= 4 ? 0.25f : stored > 0 ? 0.12f : 0f;

    /// <summary>Whether a shield piece is held on her arm now (P7ShieldAt falls back to her chest when none is).</summary>
    bool P7ShieldHeld()
    {
        P7ShieldAt();
        return p7Shield != null;
    }

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
        if (p7StormOn >= 0)
        {
            if (p7StormLight is { Visible: true })
            {
                p7StormLight.GlobalPosition = PlayerPos + Vector3.Up * 1.3f;
                p7StormLight.LightEnergy = Mathf.Min(1, p7StormOn / 0.15f) * (Flare.Night ? 1.3f : 2.0f) * P7D["storm.light"];
            }
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
        else if (p7StormLight is { Visible: true })
        {
            p7StormLight.LightEnergy -= dt * 8;
            if (p7StormLight.LightEnergy <= 0) p7StormLight.Visible = false;
        }
    }
}

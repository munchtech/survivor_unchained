using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// The Warden's holy pair (Combat VFX 10 item 3; WARDEN_SKILLS_VFX_HOOKS §3, §4, hooks a and b).
///
/// Rebuke (Ev.Nova art `rebuke`, on the striker, up to twice a second): no ring. A bronze-gold flare at her shield
/// side facing the striker, then a curved holy lash from her shield to the striker and chained on, body to nearest
/// body, travelling over 0.1 s and fading over 0.15 s; each struck body gets the gold rim and a small gold burst on
/// the lash's arrival (full spark kits capped at 3 a strike; a strike within a second of the last at 70%).
///
/// Watch Bell (Ev.Nova art `watch_bell`, every 6 s): a spectral bronze bell over her, a lathe mesh (crown,
/// shoulder, waist, sound bow, flared lip), in over 4 frames, swung once as it tolls and faded over half a second;
/// one bell only (a Pulse's follow-up tolls re-swing it). The toll's wave: a low raised ripple band running out to
/// the reach in 0.35 s (shaders/toll_wave.gdshader), bright at its leading edge and dark behind, fading with
/// distance to ~40%, the 2nd ring 0.12 s behind; sparse lit dust lifted at the front; each drawn body a dust drag
/// streak toward her over its slide (at most 16) and the gold rim.
///
/// Barrier gain (Ev.Barrier): a gold shimmer climbing her body over 0.4 s with a faint shell round her
/// (shaders/barrier_shell.gdshader), its strength scaled by the gain's share of her health.
///
/// Dev beats (--wh-beats): rb_f1/f3/f8 (the 2nd Rebuke on, clear of a toll), rb_press, wb_f1/f6/f12/f24 (the 1st
/// toll), bar_f8 (the 1st toll's barrier).
/// </summary>
public partial class BattleFx
{
    static readonly bool WhBeats = Args.Has("wh-beats");

    static readonly Color HolyGold = Hdr("#ffb84a", 1f), HolyCore = Hdr("#ffd890", 1f), HolyBronze = Hdr("#e0a048", 1f);

    /* ------------------------------------------------------------ Rebuke -- */

    double rbAt = -1, rbLast = -9;
    Vector3 rbFrom, rbStriker;
    float rbDim = 1;
    int rbCount;
    bool rbPressShot;
    readonly List<(int Id, Vector3 At, bool Crit)> rbStruck = new();

    void RebukeFx(Ev.Nova e)
    {
        var her = PlayerPos;
        var striker = V(e.X, Y(e.X, e.Z) + 1.0, e.Z);
        var to = striker - her; to.Y = 0;
        var dir = to.LengthSquared() > 0.01f ? to.Normalized() : Vector3.Forward;
        var left = new Vector3(dir.Z, 0, -dir.X);
        // Her shield side (it rides her left forearm), facing the one who struck.
        rbFrom = her + Vector3.Up * 1.1f + dir * 0.42f + left * 0.16f;
        rbStriker = striker;
        rbDim = time - rbLast < 1 ? 0.7f : 1f;
        rbLast = time;
        rbAt = time;
        rbCount++;
        rbStruck.Clear();
        float k = rbDim * (Flare.Night ? 0.8f : 1f);
        // The shield flash: a bronze-gold flare 0.7 m across with a small core, frames 0-3.
        Sparks.Spawn(new Sparks.P
        {
            At = rbFrom, Life = 4 / 60f, Size = 0.7f, SizeEnd = 0.6f, Color = HolyGold * 0.85f * k, ColorEnd = HolyBronze * 0.15f,
            Alpha = 1, Sprite = Sprites.Range("light").First + 1 + 1, Spin = R() * Mathf.Tau + 0.001f, SpinV = 0.001f,
        });
        Sparks.Spawn(new Sparks.P
        {
            At = rbFrom + dir * 0.03f, Life = 3 / 60f, Size = 0.22f, SizeEnd = 0.14f, Color = HolyCore * 1.3f * k, ColorEnd = HolyGold * 0.3f,
            Alpha = 1, Sprite = Star4, Spin = R() * 0.5f + 0.001f, SpinV = 0.001f,
        });
        Flash(rbFrom + dir * 0.3f, HolyGold, 2.2f * k, 0.14f, 3.5f);
        // The lash is laid once the strike's bodies are in (they come in this same step).
        pending.Add((time, RebukeLash));
        if (WhBeats)
        {
            bool clear = time - wbLast > 1.2;
            if (rbCount >= 2 && !rbBeatShot && clear) { rbBeatShot = true; Shots.WantFrames("rb_f1", 1); Shots.WantFrames("rb_f3", 3); Shots.WantFrames("rb_f8", 8); GD.Print($"[wh-beats] rebuke #{rbCount} t={time:F2}"); }
            if (rbCount >= 5 && !rbPressShot && clear && time - wbLast > 2) { rbPressShot = true; Shots.WantFrames("rb_press", 2); GD.Print($"[wh-beats] rebuke press #{rbCount} t={time:F2}"); }
        }
    }

    bool rbBeatShot;

    /// <summary>A body struck by Rebuke or the bell (its Hit; art `rebuke`, `watch_bell`). False for any other art.</summary>
    bool WardenHolyStruck(Ev.Hit e, Vector3 at)
    {
        if (e.Art == "rebuke")
        {
            if (time == rbAt && rbStruck.Count < 6) rbStruck.Add((e.Target, at, e.Crit));
            return true;
        }
        if (e.Art == "watch_bell")
        {
            if (time != wbAt) return true;
            var away = at - PlayerPos; away.Y = 0;
            away = away.LengthSquared() > 0.01f ? away.Normalized() : Vector3.Forward;
            HitKit(at, away, HolyGold, 1, false, false, -away, e.Target);
            var foe = b0 != null && e.Target >= 0 && e.Target < b0.Enemies.Capacity ? b0.Enemies.Items[e.Target] : null;
            if (foe is { Boss: false } && drags.Count < 16) drags.Add(new Drag { Id = e.Target, Age = 0, Last = at });
            return true;
        }
        return false;
    }

    void RebukeLash()
    {
        if (rbStruck.Count == 0) return;
        float k = rbDim * (Flare.Night ? 0.78f : 1f);
        // The chain: the first struck (the striker), then on to the nearest not yet struck, and so on.
        var left = new List<(int Id, Vector3 At, bool Crit)>(rbStruck);
        var order = new List<(int Id, Vector3 At, bool Crit)>(left.Count);
        var first = left[0]; left.RemoveAt(0); order.Add(first);
        while (left.Count > 0)
        {
            var last = order[^1].At;
            int bi = 0;
            for (int i = 1; i < left.Count; i++) if (left[i].At.DistanceSquaredTo(last) < left[bi].At.DistanceSquaredTo(last)) bi = i;
            order.Add(left[bi]); left.RemoveAt(bi);
        }
        const float Travel = 0.1f;
        var from = rbFrom;
        float side = R() < 0.5f ? -1 : 1;
        for (int i = 0; i < order.Count; i++)
        {
            var (id, to, crit) = order[i];
            float delay = Travel * i / order.Count, arrive = Travel * (i + 1) / order.Count;
            var a = from; var bpt = to + Vector3.Up * 0.1f;
            side = -side;
            bool full = i < 3;
            float sd = side, kk = k * (i == 0 ? 1f : 0.85f);
            pending.Add((time + delay, () => LashSegment(a, bpt, sd, kk)));
            pending.Add((time + arrive, () => RebukeStruckFx(id, bpt, a, k, crit, full)));
            from = bpt;
        }
    }

    /// <summary>One curved stroke of the lash, a to b: holy gold 0.05 m wide with a hot thin core, fading over 0.15 s.</summary>
    void LashSegment(Vector3 a, Vector3 b, float side, float k)
    {
        var d = b - a; float len = d.Length();
        if (len < 0.05f) return;
        var flat = new Vector3(d.X, 0, d.Z);
        var perp = flat.LengthSquared() > 0.001f ? new Vector3(-flat.Z, 0, flat.X).Normalized() : Vector3.Right;
        // A whip's curve: bowed to one side and up, its far half snapping back (an S, not an arc).
        var c1 = a + d * 0.33f + perp * side * len * 0.22f + Vector3.Up * len * 0.14f;
        var c2 = a + d * 0.7f - perp * side * len * 0.08f + Vector3.Up * len * 0.06f;
        const int N = 12;
        var pts = new Vector3[N];
        var ws = new float[N];
        for (int i = 0; i < N; i++)
        {
            float t = i / (float)(N - 1), u = 1 - t;
            pts[i] = u * u * u * a + 3 * u * u * t * c1 + 3 * u * t * t * c2 + t * t * t * b;
            ws[i] = 0.35f + 0.65f * Mathf.Sin(Mathf.Pi * Mathf.Min(1, t * 1.15f + 0.05f));
        }
        Ribbons.Line(pts, 0.055f, 0.15f, HolyGold * k, 1.5f, Ribbons.Style.Glow, ws);
        Ribbons.Line(pts, 0.016f, 0.11f, HolyCore * k, 1.5f, Ribbons.Style.Glow, ws);
    }

    void RebukeStruckFx(int id, Vector3 at, Vector3 from, float k, bool crit, bool full)
    {
        var away = at - from; away.Y = 0;
        away = away.LengthSquared() > 0.01f ? away.Normalized() : Vector3.Forward;
        HitKit(at, away, HolyGold, 1, crit, full && hitBudget-- > 0, away, id);
        // The small gold burst on the body: 0.45 m at most, 5 frames.
        Sparks.Spawn(new Sparks.P
        {
            At = at - away * 0.08f, Life = 5 / 60f, Size = 0.32f * (full ? 1 : 0.8f), SizeEnd = 0.45f * (full ? 1 : 0.8f), Color = HolyGold * 0.7f * k, ColorEnd = HolyBronze * 0.1f,
            Alpha = 1, Sprite = Sprites.Range("light").First + 1 + 1, Spin = R() * Mathf.Tau + 0.001f, SpinV = 0.001f,
        });
    }

    /* -------------------------------------------------------- Watch Bell -- */

    double wbAt = -1, wbLast = -9;
    int wbCount;
    bool barShot;
    Batch? bells, waves, shells;

    struct Bell { public Vector3 Pivot, Axis; public float Age, Swing, Strike, Alpha; public bool Live; }
    Bell bell;

    struct Wave { public Vector3 At; public float Reach, Age, Delay, K; public bool Dust; }
    readonly List<Wave> liveWaves = new();

    struct Drag { public int Id; public float Age; public Vector3 Last; }
    readonly List<Drag> drags = new();

    struct Shell { public float Age, K; public bool Live; }
    Shell shell;

    const float BellH = 1.15f, BellMouth = 2.85f, BellLife = 0.75f, WaveRun = 0.35f, WaveFade = 0.08f;

    void HolyReady()
    {
        if (bells != null) return;
        bells = Add(new Batch(BellMesh(), 1, new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/toll_bell.gdshader") }));
        waves = Add(new Batch(WaveMesh(), 12, new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/toll_wave.gdshader") }));
        shells = Add(new Batch(new SphereMesh { Radius = 0.5f, Height = 1, RadialSegments = 32, Rings = 16 }, 1, new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/barrier_shell.gdshader") }));
    }

    void TollFx(Ev.Nova e)
    {
        HolyReady();
        float r = (float)e.Radius;
        var ground = V(e.X, Y(e.X, e.Z), e.Z);
        bool follow = time - wbLast < 1.2 && bell.Live;
        wbLast = time; wbAt = time; wbCount++;
        drags.Clear();
        // Above her and a little behind (away from the camera), swinging across the screen.
        var cam = GetViewport()?.GetCamera3D();
        var back = cam != null ? -cam.GlobalBasis.Z : Vector3.Forward; back.Y = 0;
        back = back.LengthSquared() > 0.01f ? back.Normalized() : Vector3.Forward;
        var pivot = PlayerPos + back * 0.55f;
        pivot.Y = ground.Y + BellMouth + BellH;
        if (follow)
        {
            // A Pulse's follow-up (or the lamp's extra toll): the one bell re-swung, struck a little softer.
            bell.Pivot = pivot; bell.Axis = back; bell.Swing = 0; bell.Strike = 0.85f; bell.Age = Mathf.Min(bell.Age, 0.08f);
        }
        else bell = new Bell { Pivot = pivot, Axis = back, Age = 0, Swing = 0, Strike = 1, Alpha = 0, Live = true };
        float k = follow ? 0.85f : 1f;
        liveWaves.Add(new Wave { At = ground, Reach = r, Age = 0, Delay = 0, K = k, Dust = true });
        liveWaves.Add(new Wave { At = ground, Reach = r * 0.94f, Age = 0, Delay = 0.12f, K = k * 0.55f, Dust = false });
        // The strike: a warm light under the bell's lip, short.
        Flash(pivot + Vector3.Down * (BellH + 0.2f), HolyGold, 3.5f * k * (Flare.Night ? 0.75f : 1f), 0.3f, 7);
        // The air thrown out with it: the scene bent at the front (the pressure, not a lit hoop), its lip a dim bronze.
        Waves.Add(ground + Vector3.Up * 0.35f, r * 1.05f, WaveRun * 1.1f, HolyBronze * 0.1f, 0.9f * k);
        Cam?.AddTrauma(0.1f);
        if (WhBeats && wbCount == 2) { Shots.WantFrames("wb_f1", 1); Shots.WantFrames("wb_f6", 6); Shots.WantFrames("wb_f12", 12); Shots.WantFrames("wb_f24", 24); GD.Print($"[wh-beats] toll #{wbCount} t={time:F2} r={r:F1}"); }
    }

    /* ----------------------------------------------------------- Barrier -- */

    void BarrierGain(Ev.Barrier e)
    {
        HolyReady();
        double max = b0?.MaxHp ?? 100;
        float share = (float)(e.Amount / Math.Max(1, max));
        // A Rebuke tick (0.1-0.4% of health) is a whisper; a full toll (5% and more) the whole of it.
        float k = Mathf.Clamp(0.22f + share / 0.05f * 0.78f, 0.22f, 1f);
        if (shell.Live && shell.Age < 0.2f) k = Mathf.Max(k, shell.K);
        shell = new Shell { Age = 0, K = k, Live = true };
        int n = (int)(2 + 8 * k);
        for (int i = 0; i < n; i++)
        {
            float a = R() * Mathf.Tau, d = 0.35f + R() * 0.15f;
            var at = PlayerPos + new Vector3(Mathf.Cos(a) * d, 0.2f + R() * 0.5f, Mathf.Sin(a) * d);
            Sparks.Spawn(new Sparks.P
            {
                At = at, V = Vector3.Up * (2.6f + R() * 1.6f), Drag = 1.5f, Life = 0.3f + R() * 0.15f, Size = 0.05f, SizeEnd = 0.02f,
                Color = HolyGold * 1.2f * (Flare.Night ? 0.8f : 1f), ColorEnd = HolyBronze * 0.3f, Alpha = 1, Sprite = -1, Stretch = 0.03f,
            });
        }
        if (WhBeats && !barShot && e.Source == "watch_bell" && wbCount >= 2) { barShot = true; Shots.WantFrames("bar_f8", 8); GD.Print($"[wh-beats] barrier {e.Amount:F1} of {max:F0} k={k:F2} t={time:F2}"); }
    }

    /* -------------------------------------------------------------- step -- */

    void StepWardenHoly(float dt)
    {
        if (bells == null || waves == null || shells == null) return;
        bool night = Flare.Night;
        // The bell: in over 4 frames, one swing (+-16 degrees) as it tolls, faded over its last half second.
        bells.Begin();
        if (bell.Live)
        {
            bell.Age += dt; bell.Swing += dt;
            if (bell.Age >= BellLife) bell.Live = false;
            else
            {
                float inA = Mathf.Min(1, bell.Age / (4 / 60f)), outA = 1 - Mathf.Clamp((bell.Age - 0.25f) / 0.5f, 0, 1);
                float alpha = inA * outA * outA;
                float s = bell.Swing, ang = s < 0.6f ? Mathf.DegToRad(16) * Mathf.Sin(Mathf.Tau * s / 0.6f) * (1 - s / 0.75f) : 0;
                float strike = bell.Strike * Mathf.Exp(-s * 7);
                float grow = Mathf.Lerp(0.88f, 1f, inA);
                var basis = new Godot.Basis(bell.Axis, ang).Scaled(Vector3.One * BellH * grow);
                bells.Add(new Transform3D(basis, bell.Pivot), new Color(night ? 0.62f : 1.35f, strike, 0, alpha));
            }
        }
        bells.End();
        // The toll's waves.
        waves.Begin();
        for (int i = liveWaves.Count - 1; i >= 0; i--)
        {
            var w = liveWaves[i];
            w.Age += dt;
            float t = w.Age - w.Delay;
            if (t > WaveRun + WaveFade) { liveWaves.RemoveAt(i); continue; }
            liveWaves[i] = w;
            if (t <= 0) continue;
            float p = Mathf.Min(1, t / WaveRun), front = 1 - Mathf.Pow(1 - p, 2.2f);
            float rr = Mathf.Lerp(0.7f, w.Reach, front);
            float fade = t > WaveRun ? 1 - (t - WaveRun) / WaveFade : 1;
            float k = w.K * Mathf.Lerp(1f, 0.4f, front) * fade * Mathf.Min(1, t / 0.03f) * (night ? 0.62f : 1.5f);
            float band = Mathf.Min(0.65f, 1.4f / rr);
            waves.Add(new Transform3D(Godot.Basis.Identity.Scaled(new Vector3(rr, 1, rr)), w.At + Vector3.Up * 0.02f), new Color(k, band, 0.24f, p));
            // Dust lifted where the front passes: low, solid, lit, sparse.
            if (w.Dust && dt > 0 && p < 0.9f)
            {
                var dust = night ? new Color(0.14f, 0.13f, 0.13f) : new Color(0.38f, 0.3f, 0.21f);
                int n = 3;
                for (int j = 0; j < n; j++)
                {
                    float a = R() * Mathf.Tau;
                    var u = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                    double x = w.At.X + u.X * rr, z = w.At.Z + u.Z * rr;
                    float sz = 0.38f + R() * 0.16f;
                    Smoke.Spawn(new Sparks.P
                    {
                        At = V(x, Y(x, z) + 0.18 + R() * 0.08, z), V = u * (1.2f + R()) + Vector3.Up * (0.15f + R() * 0.2f), Drag = 2.5f,
                        Life = 0.3f + R() * 0.15f, Size = sz, SizeEnd = sz * 1.5f, Color = dust, ColorEnd = dust * 0.9f,
                        Alpha = 0.32f + R() * 0.12f, Sprite = SolidPuff(), Core = true, Spin = R() * Mathf.Tau,
                    });
                }
            }
        }
        waves.End();
        // The drawn: dust dragged at their feet along the slide toward her.
        for (int i = drags.Count - 1; i >= 0; i--)
        {
            var d = drags[i];
            d.Age += dt;
            if (d.Age > 0.45f || b0 == null || d.Id < 0 || d.Id >= b0.Enemies.Capacity) { drags.RemoveAt(i); continue; }
            var en = b0.Enemies.Items[d.Id];
            var (x, z) = CrowdView.Placed?.Invoke(en) ?? (en.X, en.Z);
            var now = V(x, Y(x, z), z);
            var step = now - new Vector3(d.Last.X, now.Y, d.Last.Z);
            if (step.LengthSquared() > 0.2f * 0.2f && dt > 0)
            {
                var dust = night ? new Color(0.13f, 0.12f, 0.12f) : new Color(0.36f, 0.28f, 0.19f);
                float sz = 0.3f + R() * 0.12f;
                Smoke.Spawn(new Sparks.P
                {
                    At = now + Vector3.Up * 0.14f - step.Normalized() * 0.15f, V = -step.Normalized() * 0.4f + Vector3.Up * 0.12f, Drag = 3,
                    Life = 0.35f + R() * 0.15f, Size = sz, SizeEnd = sz * 1.7f, Color = dust, ColorEnd = dust * 0.9f,
                    Alpha = 0.4f, Sprite = SolidPuff(), Core = true, Spin = R() * Mathf.Tau,
                });
                d.Last = now;
            }
            drags[i] = d;
        }
        // Her barrier's shimmer and shell, riding her.
        shells.Begin();
        if (shell.Live)
        {
            shell.Age += dt;
            const float Life = 0.42f;
            if (shell.Age >= Life) shell.Live = false;
            else shells.Add(new Transform3D(Godot.Basis.Identity.Scaled(new Vector3(1.05f, 2.05f, 1.05f)), PlayerPos + Vector3.Up * 0.98f), new Color(shell.K * (night ? 0.75f : 1f), 0, 0, shell.Age / Life));
        }
        shells.End();
    }

    /* ------------------------------------------------------------ meshes -- */

    /// <summary>The bell, a lathe round Y with its pivot (the crown's top) at the origin, unit height down to its lip:
    /// crown knob, shoulder, waist, sound bow and a flared lip (mouth radius ~0.5). UV.x round it, UV.y up it (0 the
    /// lip, 1 the crown); normals from the profile.</summary>
    static ArrayMesh BellMesh()
    {
        // (radius, height from the lip) from the crown down.
        var prof = new Vector2[]
        {
            new(0f, 1f), new(0.07f, 1f), new(0.09f, 0.975f), new(0.1f, 0.95f), new(0.19f, 0.94f), new(0.26f, 0.915f),
            new(0.3f, 0.87f), new(0.315f, 0.8f), new(0.315f, 0.68f), new(0.325f, 0.54f), new(0.35f, 0.4f), new(0.39f, 0.27f),
            new(0.44f, 0.16f), new(0.49f, 0.08f), new(0.53f, 0.03f), new(0.545f, 0f), new(0.51f, -0.005f),
        };
        const int Na = 56;
        var st = new SurfaceTool();
        st.Begin(Mesh.PrimitiveType.Triangles);
        int np = prof.Length;
        var nrm = new Vector2[np];
        for (int j = 0; j < np; j++)
        {
            var t = prof[Math.Min(np - 1, j + 1)] - prof[Math.Max(0, j - 1)];
            nrm[j] = new Vector2(-t.Y, t.X).Normalized();
            if (nrm[j].X < 0) nrm[j] = -nrm[j];
        }
        void P(int i, int j)
        {
            float a = i / (float)Na * Mathf.Tau;
            var c = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            var p = prof[j];
            st.SetNormal((c * nrm[j].X + Vector3.Up * nrm[j].Y).Normalized());
            st.SetUV(new Vector2(i / (float)Na, Mathf.Clamp(p.Y, 0, 1)));
            st.AddVertex(c * p.X + Vector3.Up * (p.Y - 1));
        }
        for (int i = 0; i < Na; i++)
            for (int j = 0; j < np - 1; j++) { P(i, j); P(i + 1, j); P(i + 1, j + 1); P(i, j); P(i + 1, j + 1); P(i, j + 1); }
        return st.Commit();
    }

    /// <summary>The toll wave's band: a full ring, UV.x round it (0..1), UV.y across it (0 behind, 1 the leading edge),
    /// spaced tight at the front; the shader places it (radius 1 at the front, the band's width and height from COLOR).</summary>
    static ArrayMesh WaveMesh()
    {
        const int Na = 160;
        float[] us = { 0f, 0.3f, 0.52f, 0.68f, 0.79f, 0.87f, 0.92f, 0.955f, 0.98f, 1f };
        var st = new SurfaceTool();
        st.Begin(Mesh.PrimitiveType.Triangles);
        void P(int i, int j) { st.SetNormal(Vector3.Up); st.SetUV(new Vector2(i / (float)Na, us[j])); st.AddVertex(Vector3.Zero); }
        for (int i = 0; i < Na; i++)
            for (int j = 0; j < us.Length - 1; j++) { P(i, j); P(i + 1, j); P(i + 1, j + 1); P(i, j); P(i + 1, j + 1); P(i, j + 1); }
        return st.Commit();
    }
}

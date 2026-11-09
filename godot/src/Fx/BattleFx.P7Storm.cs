using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// P7 (the skills lead, 9 Nov): Bladestorm and Iron Vow in the FX language (docs/design/FX_LANGUAGE.md §5).
/// The storm: four steel crescents at knee height (the union's: the one-key Cyclone's 2-3, more), blade 0 riding her
/// sword's own angle, each core leading, gold body, amber trail over 100 degrees; a low two-value dust swirl at her feet;
/// a gold pool that moves with her; each struck foe a tick: a 2-frame rim for all, a glint and tangential sparks for the
/// nearest six (never a burst every tick). The Sunder lines it throws: a dark hairline crack (matter) with a heart that
/// flashes core and holds the mid band while pending. The break: a hard star, a shock ring whose hot lip runs out to
/// exactly the break's radius, every pending line splitting at once (the Sunder strip opening behind a core front racing
/// out from her end, its jets and chips), a dust ring, chunks, the pool, a 3-frame hitstop (WorldScene.Weigh) and a punch.
/// The vow: the plant's dust and a glint on her shield; a tight edge-band shell; each stored blow its sparks pulled into
/// the shield and the shield's core glow a step up; the burst a ring to its radius, a star, the pool and rims, all sized
/// by the store. Keyed on Ev.Spin, Ev.SpinLine and Ev.Brace, never the string ids (iron_vow is a boon's id too).
/// </summary>
public partial class BattleFx
{
    sealed class P7Scar
    {
        public required MeshInstance3D N;
        public required ShaderMaterial M;
        public WgDecal? Crack;
        public float Age, SplitAge = -1, FadeAge = -1, Travel;
    }

    P7Shape? p7Blades, p7Shell, p7Store;
    OmniLight3D? p7StormLight;
    double p7StormOff = -9;
    float p7StormR, p7StormOn = -1, p7SpinPrev = float.NaN, p7SpinDir = -1, p7Swirl, p7SpinAngle;
    // the frame's storm work (P7Pre): a tick or start in this batch; a break in it; how many tick kits drawn
    bool p7TickNow, p7BreakNow;
    int p7TickKits;
    double p7VowAt = -9, p7VowStored;
    float p7VowLevel;
    readonly Dictionary<int, P7Scar> p7Scars = new();
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
                // the contact on the side facing her; sparks along the blade's way (tangent, her spin's sense)
                var contact = at - rad * 0.3f;
                var tan = new Vector3(-rad.Z, 0, rad.X) * -p7SpinDir;
                P7Glint(contact, 0.3f);
                P7Streak(contact, tan);
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
                p7Blades?.N.QueueFree();
                if (p7Blades != null) p7Shapes.Remove(p7Blades);
                p7Blades = P7Quad(6, PlayerPos + Vector3.Up * 0.45f, p7StormR, 9999, step: P7StepBlades);
                p7Blades.M.SetShaderParameter("p7_count", 4f);
                p7Blades.M.SetShaderParameter("p7_trail", Mathf.DegToRad(100));
                if (p7StormLight == null)
                {
                    p7StormLight = new OmniLight3D { ShadowEnabled = false, OmniAttenuation = 1.1f, LightColor = P7Band(1) };
                    AddChild(p7StormLight);
                }
                p7StormLight.OmniRange = p7StormR * 1.5f;
                p7StormLight.Visible = true;
                break;
            }
            case SpinPhase.Tick:
                if (e.Heavy) P7Glint(P7BladeAt(1), 0.42f);
                break;
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

    void P7StormDown()
    {
        if (p7StormOn < 0) return;
        p7StormOn = -1; p7StormOff = time;
        if (p7Blades is { } bl)
        {
            // it dies by stepping: holes open, core then mid then edge, over 3 samples
            float at = bl.Age;
            bl.Life = at + 3 * P7Sample;
            bl.Step = s =>
            {
                P7StepBlades(s);
                s.M.SetShaderParameter("p7_fade", Mathf.Min(1, (Mathf.Floor((s.Age - at) / P7Sample) + 1) * 0.34f));
            };
        }
        p7Blades = null;
    }

    void P7StepBlades(P7Shape s)
    {
        var her = PlayerPos;
        s.N.GlobalPosition = her + Vector3.Up * 0.45f;
        // blade 0 rides her sword's own angle round her (atan(z, x), as the quad's UV runs), its sense from its change
        var tip = P7BladeAt(1);
        float a = Mathf.Atan2(tip.Z - her.Z, tip.X - her.X);
        if (!float.IsNaN(p7SpinPrev))
        {
            float d = Mathf.Wrap(a - p7SpinPrev, -Mathf.Pi, Mathf.Pi);
            if (Mathf.Abs(d) > 0.02f) p7SpinDir = Mathf.Sign(d);
        }
        p7SpinPrev = a; p7SpinAngle = a;
        s.M.SetShaderParameter("p7_spin", a);
        s.M.SetShaderParameter("p7_dir", p7SpinDir);
        // the wind-in: the trails grow out of the heads over 0.15 s
        s.M.SetShaderParameter("p7_prog", Mathf.Clamp(s.Age / 0.15f, 0.25f, 1));
    }

    /// <summary>The break: she plants. A hard star, the shock ring (its hot lip runs out to exactly the radius), the dust
    /// ring, chunks, the pool and a punch; the lines split (Ev.SpinLine Split, P7Line).</summary>
    void P7Break(double x, double z, float r, float grow)
    {
        var c = V(x, Y(x, z), z);
        float k = Mathf.Clamp((grow - 1) / 0.6f, 0, 1);
        P7Quad(1, c + Vector3.Up * 0.05f, Mathf.Min(2.4f, r * 0.36f), 5 * P7Sample, step: s => s.M.SetShaderParameter("p7_t", s.Age));
        const float run = 0.16f;
        P7Quad(5, c + Vector3.Up * 0.06f, r, run + 3 * P7Sample, step: s =>
        {
            s.M.SetShaderParameter("p7_prog", Mathf.Clamp(s.Age / run, 0, 1));
            s.M.SetShaderParameter("p7_width", 0.1f + 0.04f * k);
            s.M.SetShaderParameter("p7_alpha", 0.92f);
            float after = s.Age - run;
            s.M.SetShaderParameter("p7_fade", after <= 0 ? 0f : Mathf.Min(1, Mathf.Floor(after / P7Sample + 1) * 0.34f));
        });
        P7LightOn(c + Vector3.Up * 1.4f, r * 1.5f, (Flare.Night ? 4f : 5.5f) * (0.85f + 0.3f * k));
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

    /// <summary>A low dust ring rolling out to `reach` in 0.4 s: a lit top over a darker skirt (matter, two values).</summary>
    void P7DustRing(double x, double z, float a0, float reach, int puffs, float sizeK)
    {
        const float drag = 4.5f;
        for (int i = 0; i < puffs; i++)
        {
            float a = a0 + (i + R() * 0.9f) / puffs * Mathf.Tau, d0 = 0.4f + R() * 0.3f;
            var o = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            float rr = reach * (0.92f + R() * 0.18f) - d0;
            float v0 = rr * drag / (1 - Mathf.Exp(-drag * 0.4f));
            double px = x + o.X * d0, pz = z + o.Z * d0;
            float sz = (0.3f + R() * 0.12f) * sizeK;
            WgPuff(V(px, Y(px, pz) + 0.2, pz), o * v0 + Vector3.Up * (0.05f + R() * 0.1f), sz, 1.35f, 0.8f + R() * 0.3f, WgDust(1.02f + R() * 0.1f), 0.78f, drag);
            if (i % 2 == 0) WgPuff(V(px, Y(px, pz) + 0.1, pz), o * v0 * 0.85f, sz * 0.8f, 1.3f, 0.7f + R() * 0.25f, WgDust(0.72f), 0.74f, drag);
        }
    }

    /// <summary>A Sunder line the storm threw: pending (a hairline crack, its heart at the mid band), split (the strip
    /// opening behind a core front racing out from her end) or faded (it steps out, nothing dealt).</summary>
    void P7Line(Ev.SpinLine e)
    {
        if (P7Off) return;
        P7WarmUp();
        var from = new Vector2((float)e.X0, (float)e.Z0);
        var to = new Vector2((float)e.X1, (float)e.Z1);
        float len = from.DistanceTo(to);
        if (len < 0.3f) return;
        var dir = (to - from) / len;
        float theta = Mathf.Atan2(-dir.Y, dir.X);
        switch (e.Phase)
        {
            case SpinLinePhase.Thrown:
            {
                P7Ev("line_thrown");
                var mid = from + dir * len * 0.5f;
                var pos = V(mid.X, Y(mid.X, mid.Y) + 0.05, mid.Y);
                p7Plane ??= new PlaneMesh { Size = new Vector2(2, 2) };
                var m = P7Mat(7);
                m.SetShaderParameter("p7_prog", -1f);
                m.SetShaderParameter("p7_lvl", 1.1f);
                var n = new MeshInstance3D { Mesh = p7Plane, MaterialOverride = m, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
                AddChild(n);
                n.GlobalTransform = new Transform3D(new Godot.Basis(Vector3.Up, theta).Scaled(new Vector3(len * 0.5f, 1, (float)e.Width * 0.5f)), pos);
                if (FxAfter.On) FxAfter.Adopt(n);
                var sc = new P7Scar { N = n, M = m };
                // the matter: a hairline of the Sunder strip, dark, under the heart
                if (wgAlb != null) sc.Crack = WgDecalOn(pos, theta, new Vector3(len, 1.6f, WgBand * 0.45f), wgAlb[5], wgNrm![5], null, 30f, 0.8f, 0, 0, 0, WgLineTint);
                if (p7Scars.Remove(e.Id, out var old)) old.N.QueueFree();
                p7Scars[e.Id] = sc;
                break;
            }
            case SpinLinePhase.Split:
            {
                P7Ev("line_split");
                if (!p7Scars.TryGetValue(e.Id, out var sc)) break;
                sc.SplitAge = 0;
                sc.Travel = 0.06f + len * 0.028f;
                sc.M.SetShaderParameter("p7_lvl", 1.1f);
                if (sc.Crack != null) sc.Crack.Life = sc.Crack.Age + 0.3f;
                // the Sunder strip itself, opening as the front passes: its jets, lips and chips (the Groundbreaker's)
                if (wgAlb != null) WgCrack(from, dir, len, 4, 6, 1.6f, sc.Travel, 1.8f, Flare.Night, false);
                P7Glint(V(from.X, Y(from.X, from.Y) + 0.3, from.Y), 0.45f);
                break;
            }
            case SpinLinePhase.Faded:
                if (p7Scars.TryGetValue(e.Id, out var sf) && sf.SplitAge < 0) { sf.FadeAge = 0; if (sf.Crack != null) sf.Crack.Life = sf.Crack.Age + 0.4f; }
                break;
        }
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
                float prog = Mathf.Clamp(s.SplitAge / Mathf.Max(0.05f, s.Travel), 0, 1);
                s.M.SetShaderParameter("p7_prog", prog);
                // the heart cools in steps once the front is out: core, mid, edge, gone (1.5 s)
                float after = s.SplitAge - s.Travel;
                float lvl = after < 0.12f ? 1.1f : after < 0.5f ? 0.62f : after < 1.0f ? 0.3f : 0.18f;
                s.M.SetShaderParameter("p7_lvl", lvl);
                s.M.SetShaderParameter("p7_fade", after < 1.0f ? 0f : Mathf.Min(1, (Mathf.Floor((after - 1.0f) / P7Sample) + 1) * 0.2f));
                if (after > 1.5f) (gone ??= new()).Add(id);
            }
            else if (s.FadeAge >= 0)
            {
                s.FadeAge += dt;
                s.M.SetShaderParameter("p7_fade", Mathf.Min(1, (Mathf.Floor(s.FadeAge / P7Sample) + 1) * 0.25f));
                if (s.FadeAge > 4 * P7Sample) (gone ??= new()).Add(id);
            }
            else
            {
                // pending: a sample at core, then held in the mid band
                s.M.SetShaderParameter("p7_lvl", s.Age < P7Sample ? 1.1f : 0.6f);
                if (s.Age > 12) (gone ??= new()).Add(id);
            }
        }
        if (gone != null) foreach (var id in gone) { p7Scars[id].N.QueueFree(); p7Scars.Remove(id); }
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
                P7Glint(P7ShieldAt(), 0.55f);
                // the plant: dust pressed out from under her feet, low, two values
                for (int i = 0; i < 12; i++)
                {
                    float a = (i + R() * 0.7f) / 12 * Mathf.Tau;
                    var o = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                    WgPuff(feet + o * 0.3f + Vector3.Up * 0.12f, o * (2.2f + R() * 1.2f) + Vector3.Up * 0.12f, 0.22f + R() * 0.08f, 1.4f, 0.55f + R() * 0.25f, WgDust(i % 2 == 0 ? 1.04f : 0.74f), 0.76f, 4.5f);
                }
                p7VowStored = 0; p7VowLevel = 0;
                p7Shell?.N.QueueFree(); p7Store?.N.QueueFree();
                if (p7Shell != null) p7Shapes.Remove(p7Shell);
                if (p7Store != null) p7Shapes.Remove(p7Store);
                p7Shell = P7Quad(8, PlayerPos + Vector3.Up * 1.0f, 1.12f, 9999, bill: true, step: s =>
                {
                    s.N.GlobalPosition = PlayerPos + Vector3.Up * 1.0f;
                    s.M.SetShaderParameter("p7_t", s.Age);
                    // in over two samples; a stored blow lifts it a band for one
                    s.M.SetShaderParameter("p7_fade", s.Age < P7Sample ? 0.5f : 0f);
                    s.M.SetShaderParameter("p7_alpha", 0.85f);
                    s.M.SetShaderParameter("p7_lvl", time - p7StoreAt < P7Sample ? 0.66f : 0.3f);
                });
                p7Store = P7Quad(9, P7ShieldAt(), 0.5f, 9999, bill: true, top: true, step: s =>
                {
                    s.N.GlobalPosition = P7ShieldAt();
                    s.M.SetShaderParameter("p7_prog", p7VowLevel);
                    s.M.SetShaderParameter("p7_t", (float)(time - p7StoreAt));
                });
                p7StoreAt = -9;
                break;
            }
            case BracePhase.Store:
                P7Ev("vow_store");
                p7VowStored = e.Stored;
                p7StoreAt = time;
                p7VowLevel = P7StoreLevel(e.Stored);
                break;
            case BracePhase.Burst:
            {
                P7Ev("vow_burst");
                p7VowAt = time;
                foreach (var sh in new[] { p7Shell, p7Store })
                    if (sh != null) { float at = sh.Age; sh.Life = at + 2 * P7Sample; var st = sh.Step; sh.Step = s => { st?.Invoke(s); s.M.SetShaderParameter("p7_fade", s.Age - at < P7Sample ? 0.4f : 0.8f); }; }
                p7Shell = p7Store = null;
                float k = P7StoreLevel(e.Stored);
                float r = (float)e.Radius;
                var c = V(e.X, Y(e.X, e.Z), e.Z);
                P7Quad(1, c + Vector3.Up * 0.05f, 0.9f + 1.1f * k, 5 * P7Sample, step: s => s.M.SetShaderParameter("p7_t", s.Age));
                P7Glint(P7ShieldAt(), 0.5f + 0.3f * k);
                float run = 0.2f;
                P7Quad(5, c + Vector3.Up * 0.06f, r, run + 3 * P7Sample, step: s =>
                {
                    s.M.SetShaderParameter("p7_prog", Mathf.Clamp(s.Age / run, 0, 1));
                    s.M.SetShaderParameter("p7_width", 0.07f + 0.06f * k);
                    s.M.SetShaderParameter("p7_alpha", 0.9f);
                    float after = s.Age - run;
                    s.M.SetShaderParameter("p7_fade", after <= 0 ? 0f : Mathf.Min(1, Mathf.Floor(after / P7Sample + 1) * 0.34f));
                });
                P7LightOn(c + Vector3.Up * 1.3f, r * 1.3f, (Flare.Night ? 3f : 4.2f) * (0.8f + 0.5f * k));
                P7DustRing(e.X, e.Z, R() * Mathf.Tau, r * 0.85f, 18 + (int)(12 * k), 0.8f + 0.25f * k);
                Cam?.JoltPx(Vector3.Up, 6f + 4f * k);
                break;
            }
        }
    }

    double p7StoreAt = -9;

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

    /// <summary>Each frame: the storm's dust swirl and pool, the lines' hearts.</summary>
    void StepP7Storm(float dt)
    {
        P7StepScars(dt);
        if (p7StormLight != null)
        {
            if (p7StormOn >= 0)
            {
                p7StormOn += dt;
                p7StormLight.GlobalPosition = PlayerPos + Vector3.Up * 1.3f;
                // the pool: in over 0.15 s, a breath on each tick
                float e = Mathf.Min(1, p7StormOn / 0.15f) * (Flare.Night ? 1.5f : 2.2f);
                p7StormLight.LightEnergy = e;
                // the swirl: low puffs at her feet thrown round her way, a lit top over a darker skirt
                p7Swirl -= dt;
                while (p7Swirl <= 0)
                {
                    p7Swirl += 0.045f;
                    float a = p7SpinAngle + Mathf.Pi + (R() - 0.5f) * 1.2f, d = 0.45f + R() * 0.45f;
                    var o = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                    var tan = new Vector3(-o.Z, 0, o.X) * p7SpinDir;
                    var feet = new Vector3(PlayerPos.X, Y(PlayerPos.X, PlayerPos.Z), PlayerPos.Z);
                    bool lit = R() < 0.6f;
                    WgPuff(feet + o * d + Vector3.Up * (lit ? 0.16f : 0.09f), tan * (2.6f + R() * 1.2f) + o * 0.9f + Vector3.Up * 0.06f, 0.2f + R() * 0.08f, 1.45f, 0.45f + R() * 0.2f, WgDust(lit ? 1.04f : 0.74f), 0.74f, 3.2f);
                }
            }
            else if (p7StormLight.Visible)
            {
                p7StormLight.LightEnergy -= dt * 8;
                if (p7StormLight.LightEnergy <= 0) p7StormLight.Visible = false;
            }
        }
    }
}

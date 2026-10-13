using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Sim;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.View;

/// <summary>
/// The Flare's view (docs/design/FLARE_LOOK.md): the shared grammar once (her clock against the world's 8%, the
/// camera envelope, Flare hitstop, the drain and the repaint, the web, the shadowed Spend light, the HUD's quiet,
/// the cues for sound and rumble) and each Flare's own layers over it (Burns Twice: FlareFx.Burns.cs). The world's
/// materials read its global uniforms (shaders/flare_world.gdshaderinc). Runs on real time (Tick), not the fight's.
/// WIP (flare-1): written, not yet built or seen; see docs/handoff/flare.md.
/// </summary>
public partial class FlareFx : Node3D
{
    public FollowCamera? Cam;
    public Func<double, double, double> HeightAt = (_, _) => 0;
    /// <summary>The held staff's holder (arm:mage_staff), for the head's light: set by the scene each frame.</summary>
    public Node3D? Staff;
    /// <summary>Where she is drawn.</summary>
    public Vector3 Her;
    public bool Night = true;
    /// <summary>The Motion setting: 1 full, 0.5 reduced, 0 off (no slowed time, no hitstop, no shake).</summary>
    public float Motion = 1;
    /// <summary>The Flashing setting halves the Spend's peak.</summary>
    public bool LessFlash;
    /// <summary>A sound cue (Audio/Sfx.Flare.cs), where, and how strong.</summary>
    public Action<string, Vector3, float> Cue = (_, _, _) => { };
    /// <summary>The eye stopping down after the last BOOM (the tone curve's exposure x this): after the flash's 4
    /// frames the night dims to 0.7 and comes back over a second, so the fire stays the brightest thing on screen
    /// and the frame's mean holds under §1.6's 1.5x (it held 1.9x for 0.6 s).</summary>
    public Action<float> Dip = _ => { };
    /// <summary>The pad: low motor, high motor, seconds.</summary>
    public Action<float, float, float> Rumble = (_, _, _) => { };
    /// <summary>The HUD's dim (0 none .. 1 the Flare's 35%).</summary>
    public Action<float> HudDim = _ => { };

    readonly FlareBits glow = new(2600, false), bed = new(1400, true);
    readonly FlareShards shards = new(800);
    readonly Random rng = new(71);
    float R() => (float)rng.NextDouble();

    // The cast, on real time from the press (-1: none).
    string id = "";
    double t = -1, releaseAt = -1, spendAt = -1, lastAt = -1;
    Vector3 at;
    float reach = 14;
    bool clutch, banked;
    double freezeLen = 0.52;

    /// <summary>Press to Release: the world at 8%, she at full speed, the Flare's clock lent the rest (Battle.FlareLead).</summary>
    public bool Frozen { get; private set; }
    /// <summary>The Flare clock's rate during the freeze (its key over the calling's Draw and Hold).</summary>
    public double LeadRate { get; private set; }
    /// <summary>A Flare blow's hitstop left (real seconds): the world all but stopped, she at 10%.</summary>
    public double Stop { get; private set; }
    double ramp = 1;
    public bool Active => t >= 0;
    /// <summary>The world's clock now (1 when no Flare holds it).</summary>
    public double WorldRate => Motion <= 0 ? 1 : Stop > 0 ? 0.03 : Frozen ? 0.08 : ramp;
    /// <summary>Hers.</summary>
    public double HerRate => Motion <= 0 ? 1 : Stop > 0 ? 0.1 : 1;
    /// <summary>Ordinary damage numbers are hidden from the press until half a second after the Spend.</summary>
    public bool Quiet => Active && (spendAt < 0 || t < spendAt + 0.5);

    /// <summary>The calling's Draw and Hold (FLARE_LOOK §1.2): stalker 0.15, reaver 0.2, warden and arcanist 0.3.</summary>
    static double HoldOf(string calling) => calling switch { "stalker" => 0.15, "reaver" => 0.2, _ => 0.3 };

    OmniLight3D headLight = null!, spendLight = null!;
    readonly List<Ember> embers = new();
    readonly List<Vector4> marks = new();
    Image marksImg = null!;
    ImageTexture marksTex = null!;
    readonly List<Vector3> missiles = new();

    public override void _Ready()
    {
        AddChild(bed);
        AddChild(glow);
        AddChild(shards);
        headLight = new OmniLight3D { LightColor = new Color(1f, 0.55f, 0.2f), LightEnergy = 0, OmniRange = 6, ShadowEnabled = false };
        spendLight = new OmniLight3D { LightColor = new Color(0.45f, 0.7f, 1f), LightEnergy = 0, OmniRange = 14, ShadowEnabled = true };
        AddChild(headLight);
        AddChild(spendLight);
        marksImg = Image.CreateEmpty(32, 1, false, Image.Format.Rgbaf);
        marksTex = ImageTexture.CreateFromImage(marksImg);
        RenderingServer.GlobalShaderParameterSet("flare_marks", marksTex);
        RenderingServer.GlobalShaderParameterSet("flare_hue", new Vector4(1f, 0.42f, 0.1f, 1));
        Clear();
    }

    /// <summary>What the press burns: enemy missiles near her, kept each frame (they are gone by the press's event).</summary>
    public void Watch(Battle b)
    {
        missiles.Clear();
        foreach (var p in b.Projectiles.Items)
            if (p.Alive && p.Owner == SurvivorUnchained.Sim.Side.Enemy && (p.X - b.Player.X) * (p.X - b.Player.X) + (p.Z - b.Player.Z) * (p.Z - b.Player.Z) < 36)
                missiles.Add(new Vector3((float)p.X, (float)HeightAt(p.X, p.Z) + 1, (float)p.Z));
    }

    public void On(Ev.Flare e, Battle b)
    {
        switch (e.Phase)
        {
            case FlarePhase.Ready:
                Cue("catch", Her, clutchNow(b) ? 1.4f : 1);
                break;
            case FlarePhase.Press:
                Press(e, b);
                break;
            case FlarePhase.Release:
                if (!Active) break;
                Frozen = false;
                ramp = 0.08;
                releaseAt = t;
                if (id != "burns_twice") Spend(e.X, e.Z, 1);
                break;
            case FlarePhase.Blow:
                if (!Active) break;
                if (id == "burns_twice") BurnsBlow(e, b);
                else { Hitstop(e.Hitstop); if (e.Last) Spend(e.TX, e.TZ, 1); }
                break;
        }
    }

    static bool clutchNow(Battle b) => b.Player.Hp < b.MaxHp * Battle.FlareClutch;

    void Press(Ev.Flare e, Battle b)
    {
        Clear();
        id = e.Id;
        t = 0;
        at = new Vector3((float)e.X, (float)HeightAt(e.X, e.Z), (float)e.Z);
        reach = (float)e.Radius;
        clutch = e.Clutch;
        banked = b.FlareFullBankShots > bankShots;
        bankShots = b.FlareFullBankShots;
        var calling = b.Flare?.Calling ?? "arcanist";
        freezeLen = 0.22 + HoldOf(calling) + (clutch ? 0.06 : 0) + (banked ? 0.05 : 0);
        LeadRate = b.FlareKey / freezeLen;
        Frozen = !e.Stand && Motion > 0;
        if (e.Stand) freezeLen = Math.Min(freezeLen, 0.15);
        RenderingServer.GlobalShaderParameterSet("flare_at", new Vector4(at.X, at.Y, at.Z, reach));
        // (a: night, for the glaze's value: by day the sky's reflection on it turned the field to snow)
        RenderingServer.GlobalShaderParameterSet("flare_hue", new Vector4(1f, 0.42f, 0.1f, Night ? 1 : 0));
        float kind = id == "burns_twice" ? (b.Lamps.FlareMods.Contains("burns.black_ice") ? 2 : 1) : 0;
        look = new Vector4(0, 0, 0, kind);
        web = new Vector4(0, 1, 0, R() * 10);
        frost = Vector4.Zero;
        // Frame 1 answers: the staff flares, the missiles near her burst into ember, the confirm, the pad's tick.
        var head = Head();
        for (int i = 0; i < 26; i++)
            glow.Spawn(FlareBits.Kind.Mote, head, Rand3() * (3 + R() * 4), 0.25f + R() * 0.25f, 0.07f + R() * 0.06f, new Color(1.3f, 0.62f, 0.2f), new Color(0.8f, 0.2f, 0.04f), drag: 4);
        foreach (var m in missiles)
        {
            for (int i = 0; i < 10; i++) glow.Spawn(FlareBits.Kind.Mote, m, Rand3() * 2.5f, 0.35f + R() * 0.3f, 0.05f, new Color(1.2f, 0.5f, 0.12f), new Color(0.6f, 0.1f, 0.02f), drag: 3, lift: 1);
            bed.Spawn(FlareBits.Kind.Puff, m, Vector3.Up * 0.6f, 0.9f, 0.35f, new Color(0.1f, 0.09f, 0.08f, 0.5f), sizeEnd: 0.9f, drag: 1);
        }
        Cue("confirm", Her, 1);
        Cue("inhale", Her, (float)freezeLen);
        Rumble(0, 0.5f, 0.04f);
        HudDim(1);
        // Pictures at the beats (--shot): press +1 frame, the Draw's end, the Hold.
        Shots.Want("b1_press", 1 / 60.0);
        Shots.Want("b2_draw", 0.22);
        Shots.Want("b3_hold", freezeLen - 0.12);
    }

    int bankShots;

    /// <summary>The Spend's light and shake for the plain Flares (their own layers come with phase 6).</summary>
    void Spend(double x, double z, float k)
    {
        spendAt = t;
        SpendLight(new Vector3((float)x, (float)HeightAt(x, z) + 2.5f, (float)z), new Color(1f, 0.75f, 0.4f), 8 * k);
        Cam?.Jolt(Vector3.Up, 0.6f * Motion);
        Cue("boom", at, 1);
        Rumble(1, 0.6f, 0.12f);
    }

    double spendLightT = -1;
    float spendLightPeak;

    void SpendLight(Vector3 p, Color c, float energy)
    {
        spendLight.GlobalPosition = p;
        spendLight.LightColor = c;
        spendLight.OmniRange = reach * 0.9f;
        spendLightPeak = energy * (LessFlash ? 0.5f : 1);
        spendLightT = t;
    }

    void Hitstop(int frames)
    {
        if (frames <= 0 || Motion <= 0) return;
        Stop = Math.Max(Stop, frames / 60.0);
    }

    /// <summary>Where the staff's head is (or above her right hand when none is held).</summary>
    Vector3 Head() => Staff is { } s && IsInstanceValid(s) ? s.GlobalTransform * new Vector3(0.04f, 0.87f, 0.01f) : Her + new Vector3(0.25f, 2.1f, 0);

    Vector3 Rand3()
    {
        var v = new Vector3(R() - 0.5f, R() - 0.5f, R() - 0.5f);
        return v.LengthSquared() < 1e-4f ? Vector3.Up : v.Normalized();
    }

    Vector4 look, web, frost;

    /// <summary>A real-time step: the clocks, the envelope, the uniforms, the layers.</summary>
    public void Tick(double dt, Battle? b)
    {
        float fdt = (float)dt;
        if (Stop > 0) Stop = Math.Max(0, Stop - dt);
        if (!Frozen && ramp < 1) ramp = Math.Min(1, ramp + dt / 0.08 * 0.92);
        if (b != null && !Active) Ready(b, fdt);
        if (Active)
        {
            t += Stop > 0 ? dt * 0.1 : dt;
            Envelope();
            if (id == "burns_twice") BurnsTick(fdt);
            else Plain();
            // The Flare's light at the Spend: 2-4 frames at its peak, then down over 0.4 s.
            float sl = spendLightT < 0 ? 0 : (float)(t - spendLightT);
            spendLight.LightEnergy = spendLightT < 0 ? 0 : sl < 0.05f ? spendLightPeak : spendLightPeak * Mathf.Exp(-(sl - 0.05f) * 12f); // halved by the 5th frame (§1.6: 1.5x for 4 frames at most)
            if (sl > 0.6f) spendLightT = -1;
            RenderingServer.GlobalShaderParameterSet("flare_look", look);
            RenderingServer.GlobalShaderParameterSet("flare_web", web);
            RenderingServer.GlobalShaderParameterSet("flare_frost", frost);
            UploadMarks();
            if (lastAt > 0)
            {
                float s = (float)(t - lastAt);
                Dip(1 - 0.3f * Mathf.SmoothStep(0.05f, 0.09f, s) * (1 - Mathf.SmoothStep(0.5f, 1.2f, s)) * (LessFlash ? 0.5f : 1));
            }
            if (Done())
            {
                // (for the pictures' log: how much of the room the Flare cleared)
                if (Args.Has("shot") && b != null) GD.Print($"flare {id}: struck down {doomed.Count}, standing in reach {StandingIn(b)}");
                Clear();
            }
        }
        glow.Step(fdt, HeightAt);
        bed.Step(fdt, HeightAt);
        shards.Step(fdt, HeightAt);
    }

    bool Done() => id == "burns_twice" ? lastAt > 0 && t > lastAt + 4.6 : spendAt >= 0 && t > spendAt + 2.5 || t > 8;

    /// <summary>Ready (FLARE_LOOK §1.2): the staff's head breathes in the calling's light, a curl of wick-smoke lifts.</summary>
    double readyT;
    void Ready(Battle b, float dt)
    {
        bool full = b.Flare != null && b.FlareMeter >= Battle.FlareFull;
        headLight.LightEnergy = Mathf.MoveToward(headLight.LightEnergy, full ? 0.5f + 0.35f * Mathf.Sin((float)readyT * Mathf.Tau * 0.5f) : 0, dt * 3);
        if (!full) return;
        readyT += dt;
        var head = Head();
        headLight.GlobalPosition = head;
        if (R() < dt * 5) bed.Spawn(FlareBits.Kind.Puff, head + Vector3.Up * 0.1f, new Vector3((R() - 0.5f) * 0.2f, 0.5f, (R() - 0.5f) * 0.2f), 1.6f, 0.08f, new Color(0.16f, 0.15f, 0.14f, 0.4f), sizeEnd: 0.35f, lift: 0.2f);
        if (R() < dt * 8) glow.Spawn(FlareBits.Kind.Mote, head + Rand3() * 0.08f, Vector3.Up * 0.3f, 0.6f, 0.035f, new Color(1.1f, 0.5f, 0.15f), new Color(0.5f, 0.1f, 0.02f));
    }

    /// <summary>The camera (FLARE_LOOK §1.4): pushed in 12% and pitched down 4 degrees at the press, released at the
    /// Spend; Burns Twice's look up lifts 8 degrees and pulls out 15% while the embers fall; settled over 0.6 s.</summary>
    void Envelope()
    {
        if (Cam == null) return;
        float k = Motion >= 1 ? 1 : Motion > 0 ? 0.5f : 0;
        double sinceSpend = spendAt < 0 ? -1 : t - spendAt;
        float push = Mathf.SmoothStep(0, 1, (float)Math.Min(1, t / 0.18)) * 0.12f, pitch = Mathf.DegToRad(4) * Mathf.SmoothStep(0, 1, (float)Math.Min(1, t / 0.18));
        if (sinceSpend >= 0)
        {
            float o = Mathf.SmoothStep(0, 1, (float)Math.Min(1, sinceSpend / 0.25));
            bool up = id == "burns_twice";
            push = Mathf.Lerp(push, up ? -0.15f : 0, o);
            pitch = Mathf.Lerp(pitch, up ? -Mathf.DegToRad(8) : 0, o);
        }
        double settleFrom = id == "burns_twice" ? (lastAt > 0 ? lastAt + 0.3 : -1) : (spendAt >= 0 ? spendAt + 0.3 : -1);
        if (settleFrom > 0 && t > settleFrom)
        {
            float s = 1 - Mathf.SmoothStep(0, 1, (float)Math.Min(1, (t - settleFrom) / 0.6));
            push *= s;
            pitch *= s;
        }
        Cam.FlarePush = push * k;
        Cam.FlarePitch = pitch * k;
    }

    /// <summary>The plain Flares: the drain and the web over the beat, repainted at the Spend.</summary>
    void Plain()
    {
        look.X = spendAt < 0 ? Mathf.Min(1, (float)t / 0.12f) : Mathf.Max(0, 1 - (float)(t - spendAt) / 0.8f);
        look.Y = spendAt < 0 ? 0 : (float)(t - spendAt) * (reach + 8) / 0.35f;
        web.X = spendAt < 0 ? Mathf.Min(1, (float)t / 0.22f) : Mathf.Max(0, 1 - (float)(t - spendAt) / 1.5f);
        web.Y = spendAt < 0 ? 1 : Mathf.Max(0, 1 - (float)(t - spendAt) / 2f);
        web.Z = Mathf.Min(reach + 3, (float)t / 0.2f * (reach + 3));
    }

    void UploadMarks()
    {
        for (int i = 0; i < 31; i++)
        {
            var m = i < marks.Count ? marks[i] : Vector4.Zero;
            if (i < marks.Count) m.W = (float)(t - m.W);
            marksImg.SetPixel(i, 0, new Color(m.X, m.Y, m.Z, i < marks.Count ? m.W : 0));
        }
        // The last texel: the BOOM's shock front (where, the reach, seconds since), racing over the whole field.
        marksImg.SetPixel(31, 0, lastAt > 0 ? new Color(boomAt.X, boomAt.Z, reach, (float)(t - lastAt)) : new Color(0, 0, 0, 0));
        marksTex.Update(marksImg);
    }

    Vector3 boomAt;

    void Clear()
    {
        t = -1;
        id = "";
        Frozen = false;
        Stop = 0;
        ramp = 1;
        releaseAt = spendAt = lastAt = -1;
        spendLightT = -1;
        foreach (var em in embers) if (em.Light != null && IsInstanceValid(em.Light)) em.Light.QueueFree();
        embers.Clear();
        embersLit = 0;
        firstLanded = calledDown = false;
        marks.Clear();
        doomed.Clear();
        pendingShatters.Clear();
        look = web = frost = Vector4.Zero;
        Dip(1);
        RenderingServer.GlobalShaderParameterSet("flare_look", look);
        RenderingServer.GlobalShaderParameterSet("flare_web", web);
        RenderingServer.GlobalShaderParameterSet("flare_frost", frost);
        if (Cam != null) { Cam.FlarePush = 0; Cam.FlarePitch = 0; }
        HudDim(0);
        if (marksImg != null) UploadMarks();
    }

    /* ---------------------------------------------------- the crowd's view -- */

    /// <summary>Bodies the Flare struck down (enemy id): when their death shows (real time), and whether they shatter.</summary>
    readonly Dictionary<int, (double At, bool Shatter, Vector3 Where)> doomed = new();

    /// <summary>For CrowdView.FlareDeath: 1 held standing (its ember hasn't landed), -1 shattered (not drawn), 0 its own death.</summary>
    public int DeathOf(int enemy)
    {
        if (!doomed.TryGetValue(enemy, out var d)) return 0;
        if (t < d.At) return 1;
        return d.Shatter ? -1 : 0;
    }

    /// <summary>A Flare's kill: held until its ember lands or the front reaches it, then shattered (Burns Twice) or let fall.</summary>
    public void Kill(Ev.Kill e)
    {
        if (!Active) return;
        var w = new Vector3((float)e.X, (float)HeightAt(e.X, e.Z), (float)e.Z);
        double when = t + 0.02;
        if (id == "burns_twice")
        {
            // Under an ember's fall: when it lands. Under the frost: as the front reaches it.
            var near = embers.Count > 0 ? embers[^1] : null;
            if (near != null && !near.Landed && near.Target.DistanceTo(w) < near.Radius + 0.5f) when = near.LandAt + 0.02 + near.Target.DistanceTo(w) / 30;
            else if (spendAt >= 0) when = spendAt + Math.Max(0, w.DistanceTo(at) - 1) / ((reach + 3) / 0.4);
            doomed[e.Enemy] = (when, true, w);
            pendingShatters.Add((when, w, e.Elite || e.Boss ? 1.6f : (float)e.Scale));
        }
        else doomed[e.Enemy] = (when, false, w);
    }

    readonly List<(double At, Vector3 Where, float Scale)> pendingShatters = new();

    int StandingIn(Battle b)
    {
        int n = 0;
        foreach (var e in b.Enemies.Items)
            if (e.Alive && (e.X - at.X) * (e.X - at.X) + (e.Z - at.Z) * (e.Z - at.Z) < reach * reach) n++;
        return n;
    }
}

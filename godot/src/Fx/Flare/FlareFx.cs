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
    /// <summary>The Flare's time (slowed world, hitstops): 1 always from the game since F1 lead 18 (10 Nov: the screen-shake
    /// setting moves the camera only; a stop is not camera motion); 0 still means none (tools, A/B).</summary>
    public float Motion = 1;
    /// <summary>The screen-shake setting on the Flare's camera (push, pitch, kicks): 1 full, 0.5 reduced, 0 off.</summary>
    public float Shake = 1;
    /// <summary>The Flashing setting halves the Spend's peak.</summary>
    public bool LessFlash;
    /// <summary>A sound cue (Audio/Sfx.Flare.cs), where, and how strong.</summary>
    public Action<string, Vector3, float> Cue = (_, _, _) => { };
    /// <summary>The eye stopping down after the last BOOM (the tone curve's exposure x this): after the flash's 4
    /// frames the night dims to 0.7 and comes back over a second, so the fire stays the brightest thing on screen
    /// and the frame's mean holds under §1.6's 1.5x (it held 1.9x for 0.6 s).</summary>
    public Action<float> Dip = _ => { };
    /// <summary>The dip now (1 none): the BOOM's birth burns through it (FlareFx.Boom BoomTick).</summary>
    float dipNow = 1;
    void SetDip(float k) { dipNow = k; Dip(k); }
    /// <summary>The sun and ambient under the Flare by day (World/Atmosphere.FlareLight): 1 none. The Long Cut dips them
    /// to 0.65 over its sweep and cleave so its own lights carry the frame (vfx9 r3b).</summary>
    public Action<float> LightDip = _ => { };
    /// <summary>The pad: low motor, high motor, seconds.</summary>
    public Action<float, float, float> Rumble = (_, _, _) => { };
    /// <summary>The HUD's dim (0 none .. 1 the Flare's 35%).</summary>
    public Action<float> HudDim = _ => { };
    /// <summary>The world's labels (loot names, map text): 0 hidden from the press, back to 1 from BOOM +0.8 s over 0.3 s (judge 5a).</summary>
    public Action<float> LabelsAlpha = _ => { };

    readonly FlareBits glow = new(3400, false), bed = new(1400, true), scars = new(700, true);
    readonly FlareShards shards = new(2600);
    readonly Random rng = new(71);
    float R() => (float)rng.NextDouble();

    // The cast, on real time from the press (-1: none).
    string id = "";
    /// <summary>Which Flare was pressed last (its sound cues look for a take of their own: Sfx.Flare).</summary>
    public string? FlareId => id.Length > 0 ? id : null;
    double t = -1, releaseAt = -1, spendAt = -1, lastAt = -1;
    Vector3 at;
    float reach = 14;
    bool clutch, banked;
    double freezeLen = 0.52;

    /// <summary>Press to Release: the world held (H7: flare_family.json worldRate, 0), she at full speed, the Flare's clock lent the rest (Battle.FlareLead).</summary>
    public bool Frozen { get; private set; }
    /// <summary>The Flare clock's rate during the freeze (its key over the calling's Draw and Hold).</summary>
    public double LeadRate { get; private set; }
    /// <summary>A Flare blow's hitstop left (real seconds): the world all but stopped, she at 10%.</summary>
    public double Stop { get; private set; }
    double ramp = 1;
    public bool Active => t >= 0;
    /// <summary>Other words and lights wait (a level's banner, its pillar): the Flare has the frame until 1.2 s after
    /// its last word (judge 2: "LEVEL 3" over the BOOM's column).</summary>
    public bool HoldsFrame => Active && (lastAt < 0 || t < lastAt + 1.2);
    /// <summary>The world's clock now (1 when no Flare holds it).</summary>
    public double WorldRate => Motion <= 0 ? 1 : Stop > 0 ? 0.03 : Frozen ? Content.FlareFamily.Stop.WorldRate : ramp;
    /// <summary>Hers.</summary>
    public double HerRate => Motion <= 0 ? 1 : Stop > 0 ? 0.1 : 1;
    /// <summary>Ordinary damage numbers are hidden from the press until half a second after the Spend.</summary>
    public bool Quiet => Active && (spendAt < 0 || t < spendAt + 0.5);
    /// <summary>Her auto-attack's swings are hidden from the Long Cut's press until its sweep is under way (the Oathblade's
    /// doubled arc, frozen by the hold beside her, read as the Long Cut's sweep: vfx9 fix2).</summary>
    /// <summary>Her auto-attack's white hit specks are hidden from the Long Cut's press to 0.6 s after its cleave (vfx9 r4b).</summary>
    public bool HushesHitSparks => Active && IsLongCut && (lcCleaveT < 0 || t < lcCleaveT + 0.6);
    public bool HushesSwings => Active && IsLongCut && (spendAt < 0 || t < spendAt + 0.35);


    OmniLight3D headLight = null!, spendLight = null!;
    static readonly bool SpendLightOld = Args.Get("spend-light") == "old";
    readonly List<Ember> embers = new();
    readonly List<Vector4> marks = new();
    /// <summary>Each mark's shape (judge 4 fix 9): the ember's way over the ground (x, z), its size 0.7-1.3x, its arcs' seed.</summary>
    readonly List<Vector4> markAux = new();
    Image marksImg = null!;
    ImageTexture marksTex = null!;
    readonly List<Vector3> missiles = new();

    public override void _Ready()
    {
        AddChild(scars);
        AddChild(bed);
        AddChild(glow);
        AddChild(shards);
        headLight = new OmniLight3D { LightColor = new Color(1f, 0.55f, 0.2f), LightEnergy = 0, OmniRange = 6, ShadowEnabled = false };
        // (E10) Shown only while lit: at energy 0 it gives no light, but a shadowed light in view still drew its six
        // shadow faces each frame (35 casters in C02's ford). --spend-light old: always shown (to compare).
        spendLight = new OmniLight3D { LightColor = new Color(0.45f, 0.7f, 1f), LightEnergy = 0, OmniRange = 14, ShadowEnabled = true, Visible = SpendLightOld };
        AddChild(headLight);
        AddChild(spendLight);
        BoomReady();
        marksImg = Image.CreateEmpty(32, 2, false, Image.Format.Rgbaf);
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
                if (Args.Has("clip")) GD.Print($"flare release frame {Engine.GetFramesDrawn()} at +{t:0.000} s real");
                if (Perf.On) GD.Print($"flare perf release t {Perf.Now:0.0000}");
                // (H7: a Strike's Spend, its light and the world's ring, lands on its main blow, FLARE_LOOK §1.2: FlareFx.Blow)
                if (id != "burns_twice" && !IsLongCut && !familyOn) Spend(e.X, e.Z, 1);
                break;
            case FlarePhase.Blow:
            {
                if (!Active) break;
                // (H7: the family's main blow, once: the boom, the kick, the band; Burns Twice's at its last word's landing)
                bool main = IsMainBlow(e);
                if (e.Part == "toll") Cue("toll", Her, 1);
                if (id == "burns_twice") BurnsBlow(e, b);
                else if (IsLongCut)
                {
                    Hitstop(main ? MainHitstop(e.Hitstop) : e.Hitstop);
                    if (e.Part == "sweep") LongSweep(e);
                    else if (e.Part == "cleave") LongCleave(e);
                }
                else { Hitstop(main ? MainHitstop(e.Hitstop) : e.Hitstop); StalkerBlow(e); if (e.Last && !familyOn) Spend(e.TX, e.TZ, 1); }
                if (!main && IsRipple(e)) RippleStart(e);
                if (main && id != "burns_twice") MainBlow(e);
                else ResolvePending();
                break;
            }
        }
    }

    static bool clutchNow(Battle b) => b.Player.Hp < b.MaxHp * Battle.FlareClutch;

    void Press(Ev.Flare e, Battle b)
    {
        Clear();
        if (Args.Has("clip")) GD.Print($"flare press frame {Engine.GetFramesDrawn()} battle_t {b.Time:0.00} foes_alive {System.Linq.Enumerable.Count(b.Enemies.Items, x => x.Alive)} kills {b.KillCount} {PressCount(e, b)}");
        // (--perf: the beats on the recording's clock, for tools/fx/flare_gpu.py --live)
        if (Perf.On) GD.Print($"flare perf press t {Perf.Now:0.0000}");
        id = e.Id;
        pressWorld = b.Time;
        dropLogged = false;
        t = 0;
        at = new Vector3((float)e.X, (float)HeightAt(e.X, e.Z), (float)e.Z);
        reach = (float)e.Radius;
        clutch = e.Clutch;
        banked = b.FlareFullBankShots > bankShots;
        bankShots = b.FlareFullBankShots;
        var calling = b.Flare?.Calling ?? "arcanist";
        // (H7: the stop's real seconds are the family's data, per calling and Flare: flare_family.json "stop")
        freezeLen = Content.FlareFamily.StopOf(e.Id, calling, clutch, banked);
        LeadRate = b.FlareKey / freezeLen;
        Frozen = !e.Stand && Motion > 0;
        if (e.Stand) freezeLen = Math.Min(freezeLen, 0.15);
        RenderingServer.GlobalShaderParameterSet("flare_at", new Vector4(at.X, at.Y, at.Z, reach));
        // (a: night, for the glaze's value: by day the sky's reflection on it turned the field to snow)
        RenderingServer.GlobalShaderParameterSet("flare_hue", calling == "warden" ? new Vector4(1f, 0.72f, 0.32f, Night ? 1 : 0) : new Vector4(1f, 0.42f, 0.1f, Night ? 1 : 0));
        float kind = id == "burns_twice" ? (b.Lamps.FlareMods.Contains("burns.black_ice") ? 2 : 1) : 0;
        look = new Vector4(0, 0, 0, kind);
        web = new Vector4(0, 1, 0, R() * 10);
        frost = Vector4.Zero;
        // Frame 1 answers: the staff flares, the missiles near her burst into ember, the confirm, the pad's tick.
        var head = Head();
        if (IsLongCut) LongPress();
        else for (int i = 0; i < 26; i++)
            glow.Spawn(FlareBits.Kind.Mote, head, Rand3() * (3 + R() * 4), 0.25f + R() * 0.25f, 0.07f + R() * 0.06f, new Color(1.3f, 0.62f, 0.2f), new Color(0.8f, 0.2f, 0.04f), drag: 4);
        foreach (var m in missiles)
        {
            for (int i = 0; i < 10; i++) glow.Spawn(FlareBits.Kind.Mote, m, Rand3() * 2.5f, 0.35f + R() * 0.3f, 0.05f, new Color(1.2f, 0.5f, 0.12f), new Color(0.6f, 0.1f, 0.02f), drag: 3, lift: 1);
            bed.Spawn(FlareBits.Kind.Puff, m, Vector3.Up * 0.6f, 0.9f, 0.35f, new Color(0.1f, 0.09f, 0.08f, 0.5f), sizeEnd: 0.9f, drag: 1);
        }
        Cue("confirm", Her, 1);
        Cue("inhale", Her, (float)freezeLen);
        Rumble(0, 0.5f, 0.04f);
        HudDim(1); LabelsAlpha(0);
        FamilyPress(e, b, calling);
        PeakMake();
        if (Args.Has("clip") && GetViewport()?.GetCamera3D() is { } pc)
        {
            var vs = GetViewport().GetVisibleRect().Size;
            var hp = pc.UnprojectPosition(Her + Vector3.Up) * new Vector2(1920f / vs.X, 1080f / vs.Y);
            GD.Print($"flare her screen {hp.X:0},{hp.Y:0} stop {freezeLen:0.000} s");
        }
        // Pictures at the beats (--shot): press +1 frame, the Draw's end, the Hold.
        // (the Long Cut times its own, on the Flare's clock: FlareFx.LongCut LongBeats)
        if (!IsLongCut)
        {
            Shots.Want("b1_press", 1 / 60.0);
            Shots.Want("b2_draw", 0.22);
            Shots.Want("b3_hold", freezeLen - 0.12);
        }
    }

    int bankShots;

    /// <summary>The Spend's light and shake for the plain Flares (their own layers come with phase 6).</summary>
    void Spend(double x, double z, float k)
    {
        spendAt = t;
        SpendLight(new Vector3((float)x, (float)HeightAt(x, z) + 2.5f, (float)z), new Color(1f, 0.75f, 0.4f), 8 * k);
        // (H7: a Strike's boom, kick and rumble are its main blow's (FlareFx.Blow); a Stand keeps them here)
        if (familyOn) return;
        Cam?.Jolt(Vector3.Up, 0.6f * Motion);
        Cue("boom", at, 1);
        Rumble(1, 0.6f, 0.12f);
    }

    double spendLightT = -1;
    float spendLightPeak;
    // (H7: a Strike's Spend light, on its main blow, runs on real time, so the blow's hitstop does not hold its peak)
    bool spendLightReal;

    void SpendLight(Vector3 p, Color c, float energy)
    {
        spendLight.GlobalPosition = p;
        spendLight.LightColor = c;
        spendLight.OmniRange = reach * 0.9f;
        spendLightPeak = energy * (LessFlash ? 0.5f : 1);
        spendLightT = spendLightReal ? rt : t;
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
    int hudKillsLogged = -1;

    public void Tick(double dt, Battle? b)
    {
        float fdt = (float)dt;
        rt += dt;
        if (Stop > 0) { Stop = Math.Max(0, Stop - dt); if (Stop <= 0) hitstopRuns = false; }
        if (!Frozen && ramp < 1) ramp = Math.Min(1, ramp + dt / 0.08 * 0.92);
        if (b != null && !Active) Ready(b, fdt);
        LcWarmStep();
        if (Active)
        {
            t += Stop > 0 && !hitstopRuns ? dt * 0.1 : dt;
            Envelope();
            BlowTick();
            // (--clip: the HUD's count as it steps, against the sim's and the band's hold: judge r2's "10 to 26" check)
            if (b != null && Args.Has("clip") && rt - pressRt < 2.5 && b.KillCount - KillsHeld != hudKillsLogged)
            {
                hudKillsLogged = b.KillCount - KillsHeld;
                GD.Print($"flare kills shown {hudKillsLogged} (sim {b.KillCount}, held {KillsHeld}, the Flare's {doomed.Count}) at +{rt - pressRt:0.000} s real, drawn {Engine.GetFramesDrawn()}");
            }
            if (id == "burns_twice") BurnsTick(fdt);
            else if (IsLongCut) LongTick(fdt);
            else Plain();
            // The Flare's light at the Spend: 2-4 frames at its peak, then down over 0.4 s.
            float sl = spendLightT < 0 ? 0 : (float)((spendLightReal ? rt : t) - spendLightT);
            // (the Long Cut rides its light itself: FlareFx.LongCut)
            if (!IsLongCut) spendLight.LightEnergy = spendLightT < 0 ? 0 : sl < 0.05f ? spendLightPeak : spendLightPeak * Mathf.Exp(-(sl - 0.05f) * 12f); // halved by the 5th frame (§1.6: 1.5x for 4 frames at most)
            if (!IsLongCut) spendLight.Visible = SpendLightOld || spendLight.LightEnergy > 0;
            if (sl > 0.6f) spendLightT = -1;
            RenderingServer.GlobalShaderParameterSet("flare_look", look);
            // (flare_web: the Draw's web is gone (H7 r2); it carries Burns Twice's char heat and the frost's seed)
            RenderingServer.GlobalShaderParameterSet("flare_web", web);
            RenderingServer.GlobalShaderParameterSet("flare_frost", frost);
            UploadMarks();
            // (Judge 6 A2's check, for the pictures' log: bodies the ring passed 4+ frames ago, as CrowdView drew them last frame.)
            // (Again at the ring's end +0.3 s and +0.55 s, while the fireball burns over the bodies: judge 7 (1).)
            if (lastAt > 0 && audited < 3 && id == "burns_twice" && t >= lastAt + RingTime(ringMax) + 6 / 60.0 + AuditAfter[audited])
            {
                if (Args.Has("shot")) GD.Print($"flare {id}: ring +4f +{AuditAfter[audited]:0.00}s, bodies in the ring drawn {CrowdView.FlareAuditSeen}, neither shattered nor charred {CrowdView.FlareAuditBad}");
                audited++;
            }
            if (lastAt > 0 && !IsLongCut)
            {
                float s = (float)(t - lastAt);
                // (Flare time: the last word's 6-frame hitstop runs it at a tenth, so 0.005 s is about 3 real frames.)
                SetDip(1 - (Night ? 0.38f : 0.25f) * Mathf.SmoothStep(0.003f, 0.008f, s) * (1 - Mathf.SmoothStep(0.12f, 0.42f, s)) * (LessFlash ? 0.5f : 1));
            }
            if (Done())
            {
                // (for the pictures' log: how much of the room the Flare cleared)
                if (Args.Has("shot") && b != null) GD.Print($"flare {id}: struck down {doomed.Count}, standing in reach {StandingIn(b)}");
                Clear();
            }
        }
        FamilyTick(dt, b);
        glow.Step(fdt, HeightAt);
        bed.Step(fdt, HeightAt);
        scars.Step(fdt, HeightAt);
        shards.Step(fdt, HeightAt);
    }

    bool Done() => id == "burns_twice" ? lastAt > 0 && t > lastAt + 4.6 : IsLongCut ? lcCleaveT >= 0 && t > lcCleaveT + 6.2 || t > 12
        : spendAt >= 0 && t > spendAt + 2.5 && (blowT < 0 || t > blowT + Content.FlareFamily.Recovery.Hold + Content.FlareFamily.Recovery.Out + 0.2) || t > 8;

    /// <summary>Ready (FLARE_LOOK §1.2): the staff's head breathes in the calling's light, a curl of wick-smoke lifts.</summary>
    double readyT;
    void Ready(Battle b, float dt)
    {
        bool full = b.Flare != null && b.FlareMeter >= Battle.FlareFull;
        headLight.LightEnergy = Mathf.MoveToward(headLight.LightEnergy, full ? 0.5f + 0.35f * Mathf.Sin((float)readyT * Mathf.Tau * 0.5f) : 0, dt * 3);
        if (!lcWarmed && b.Flare?.Id == LongCutId) LcWarmStart();
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
        float k = Shake >= 1 ? 1 : Shake > 0 ? 0.5f : 0;
        double sinceSpend = spendAt < 0 ? -1 : t - spendAt;
        // (H7 r2: a Flare with a peak holds its push through the stop and lets go on the main blow, over the data's release)
        bool peaked = HasPeak;
        if (peaked) sinceSpend = blowT < 0 ? -1 : (t - blowT) * 0.25 / Math.Max(Content.FlareFamily.Peak.Release, 1e-3);
        float push = Mathf.SmoothStep(0, 1, (float)Math.Min(1, t / 0.18)) * 0.12f, pitch = Mathf.DegToRad(4) * Mathf.SmoothStep(0, 1, (float)Math.Min(1, t / 0.18));
        if (sinceSpend >= 0)
        {
            float o = Mathf.SmoothStep(0, 1, (float)Math.Min(1, sinceSpend / 0.25));
            bool up = id == "burns_twice";
            push = Mathf.Lerp(push, up ? -0.15f : 0, o);
            pitch = Mathf.Lerp(pitch, up ? -Mathf.DegToRad(8) : 0, o);
        }
        double settleFrom = peaked ? -1 : IsLongCut ? (lcCleaveT >= 0 ? lcCleaveT + 0.35 : -1) : id == "burns_twice" ? (lastAt > 0 ? lastAt + 0.3 : -1) : (spendAt >= 0 ? spendAt + 0.3 : -1);
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
        // (H7: the gray drain is gone; the family's indigo grade (FlareFx.Family) carries the stop and eases back)
        look.X = 0;
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
            var x = i < markAux.Count ? markAux[i] : Vector4.Zero;
            marksImg.SetPixel(i, 1, new Color(x.X, x.Y, x.Z, x.W));
        }
        // The last texel: the BOOM's ring (where, how far it runs, seconds since), racing over the whole reach.
        marksImg.SetPixel(31, 0, lastAt > 0 ? new Color(boomAt.X, boomAt.Z, ringMax, (float)(t - lastAt)) : new Color(0, 0, 0, 0));
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
        BlowClear();
        audited = 0;
        colT = -1;
        BoomClear();
        LongClear();
        spendLightT = -1;
        spendLightReal = false;
        foreach (var em in embers) if (em.Light != null && IsInstanceValid(em.Light)) em.Light.QueueFree();
        embers.Clear();
        embersLit = 0;
        firstLanded = calledDown = false;
        marks.Clear();
        markAux.Clear();
        doomed.Clear();
        look = web = frost = Vector4.Zero;
        FamilyClear();
        SetDip(1);
        RenderingServer.GlobalShaderParameterSet("flare_look", look);
        RenderingServer.GlobalShaderParameterSet("flare_web", web);
        RenderingServer.GlobalShaderParameterSet("flare_frost", frost);
        if (Cam != null) { Cam.FlarePush = 0; Cam.FlarePitch = 0; }
        HudDim(0); LabelsAlpha(1);
        if (marksImg != null) UploadMarks();
    }

    /* ---------------------------------------------------- the crowd's view -- */

    /// <summary>A body the Flare struck down: when it breaks (Flare time; Held: a statue of ice until an ember lands
    /// by it or the BOOM's ring crosses it), whether it shatters, where, how big, and what broke it.</summary>
    sealed class Doom
    {
        public double At;
        public bool Shatter, Done;
        /// <summary>The Long Cut's: killed, its moment not yet known (its blow's event comes after its Ev.Kill).</summary>
        public bool Pending;
        public double Born;
        /// <summary>Real seconds at its kill (the decision hold: FlareFx.Blow MarkHolds).</summary>
        public double BornRt;
        /// <summary>The Long Cut's: real seconds (its lcRt) when its moment came, for its flash.</summary>
        public double Rt;
        /// <summary>The Long Cut's: when its rim comes (Flare time: the sweep passing it, or the fuse), and the real time it came (-1 not yet).</summary>
        public double RimAt = -1, RimRt = -1;
        /// <summary>The Long Cut's: how far from the seam's line it stands (m), for the log.</summary>
        public float Across;
        /// <summary>The Long Cut's: off the drawn seam (more than LcSeamBand from its crack), so it greys and falls away as
        /// ash, no gold (vfx9 r4a: the judge's two classes of death).</summary>
        public bool Ash;
        public Vector3 Where, From;
        public float Scale;
    }

    const double Held = double.MaxValue;
    readonly Dictionary<int, Doom> doomed = new();

    /// <summary>For CrowdView.FlareDeath: 1 held standing (a statue until its ember or the ring), -1 shattered (not
    /// drawn), 0 its own death.</summary>
    public int DeathOf(int enemy)
    {
        if (!doomed.TryGetValue(enemy, out var d)) return 0;
        // (H7: a decision-marked hit's death waits until its mark has shown)
        if (MarkHolds(enemy, d.BornRt)) return 1;
        // The Long Cut's: standing till the fuse reaches it, then its burn-up, then gone (no corpse: it burnt).
        if (IsLongCut) return d.Pending || t < d.At + BurnLen ? 1 : -1;
        if (t < d.At) return 1;
        return d.Shatter ? -1 : 0;
    }

    /// <summary>A Flare's kill. Burns Twice keeps the pack on screen: what the frost kills stands glazed, a field of
    /// statues, until an ember lands by it (Burns.Strike) or the BOOM's ring crosses it (Burns.Land), and then
    /// shatters; what dies after the ring has passed breaks at once.</summary>
    public void Kill(Ev.Kill e)
    {
        if (!Active) return;
        var w = new Vector3((float)e.X, (float)HeightAt(e.X, e.Z), (float)e.Z);
        if (id == "burns_twice")
        {
            double when = lastAt > 0 ? Math.Max(t + 0.02, lastAt + RingTime(w.DistanceTo(boomAt)) + CrackHold()) : Held;
            doomed[e.Enemy] = new Doom { At = when, Shatter = true, Where = w, From = lastAt > 0 ? boomAt : at, Scale = e.Elite || e.Boss ? 1.6f : (float)e.Scale, BornRt = rt };
        }
        else if (IsLongCut) doomed[e.Enemy] = new Doom { At = Held, Pending = true, Born = t, BornRt = rt, Where = w, Scale = (float)e.Scale };
        // (H7: the rest wait for their blow's event: before the main blow they fall at it, from the main blow on as the band
        // reaches them: FlareFx.Blow ResolvePending)
        else if (familyOn) doomed[e.Enemy] = new Doom { At = Held, Pending = true, Born = t, BornRt = rt, Where = w };
        else doomed[e.Enemy] = new Doom { At = t + 0.02, Where = w, BornRt = rt };
    }

    /// <summary>How long after its statue breaks a body's ember shows: the ring and its char read first (s1b: the
    /// drops lit inside the ring at c1w as orange confetti over the char).</summary>
    const double DropAfter = 1.0;

    /// <summary>Whether a drop lying here is still inside a statue (BattleFx.Pickups): a body's ember falls out of
    /// it when it breaks, not the instant the frost killed it (s1b: 250 orange crystals over the glazed field).</summary>
    public bool HidesDrop(double x, double z)
    {
        if (!Active || doomed.Count == 0) return false;
        foreach (var d in doomed.Values)
            if (t < (id == "burns_twice" ? Math.Max(d.At + 0.05, DropsShow(d.Where)) : familyOn ? DropsShow(d.Where) : Math.Max(d.At + DropAfter, DropsShow(d.Where))) && (d.Where.X - x) * (d.Where.X - x) + (d.Where.Z - z) * (d.Where.Z - z) < 1.44) return true;
        return false;
    }

    /// <summary>When Burns Twice's drops show. Judge 6 (9): 250 embers falling out of the statues over the Return read as
    /// orange confetti on the char, so they waited for the Return's end (+4.2 s). The owner (29 Oct): loot as near instant
    /// as reads clean, under 1 s. Now each shows as the ring passes it (+0.05 s), scaled in over 0.3 s and held dim
    /// until the Return ends (DropFresh), so it reads as loot settling, not orange flecks. Flare time.</summary>
    double DropsShow(Vector3 w)
    {
        // (the Long Cut's wait until the seam has cooled to red, rippling out from the line: r1's hundred orbs buried it)
        // (H7: every Strike's loot lands on the beat, as the band passes it; the Long Cut's held dim until its seam cools: DropFresh)
        if (familyOn && id != "burns_twice") return BandDropAt(w.X, w.Z);
        if (IsLongCut) return lcCleaveT < 0 ? Held : lcCleaveT + 3.5 + 0.05 * Math.Min(12, Math.Abs(SeamAcross(w)));
        if (id != "burns_twice") return 0;
        if (lastAt <= 0) return Held;
        return lastAt + RingTime(new Vector2(w.X - boomAt.X, w.Z - boomAt.Z).Length()) + DropRingLag;
    }

    const double DropRingLag = 0.05, DropGrow = 0.3;
    /// <summary>The Return's end (Flare time after the BOOM): a fresh drop's light comes up to full over these.</summary>
    const float DropDimFrom = 3.4f, DropDimTo = 4.3f, DropDim = 0.3f, DropSettle = 0.1f;
    double pressWorld;

    /// <summary>For BattleFx.Pickups, after Burns Twice's BOOM: a drop born since the press (bornWorld: Battle.Time at its
    /// birth) is drawn at this scale (0.35 to 1 over 0.3 s from the ring passing it) and this light (0.35 of its own
    /// until the Return ends, then full by +4.3 s, before the Flare clears at +4.6 s). (1, 1) otherwise.</summary>
    public (float Scale, float Light) DropFresh(double x, double z, double bornWorld)
    {
        if (Active && familyOn && id != "burns_twice" && blowT >= 0 && bornWorld >= pressWorld - 1e-6)
        {
            // (H7: every Strike's: scaled in as the band passes it; the Long Cut's held at the settle's dim until its seam
            // has cooled, as r1's hundred orbs over the seam asked)
            var bt = Content.FlareFamily.Beat;
            double sh = BandDropAt((float)x, (float)z);
            float kk = Mathf.SmoothStep(0, 1, (float)((t - sh) / Math.Max(bt.DropGrow, 1e-3)));
            float lt = IsLongCut ? Mathf.Lerp(DropSettle, 1, Mathf.SmoothStep((float)lcCleaveT + 3.0f, (float)lcCleaveT + 3.8f, (float)t)) : 1;
            return (0.35f + 0.65f * kk, kk * lt);
        }
        if (!Active || id != "burns_twice" || lastAt <= 0 || bornWorld < pressWorld - 1e-6) return (1, 1);
        double show = lastAt + RingTime(new Vector2((float)x - boomAt.X, (float)z - boomAt.Z).Length()) + DropRingLag;
        float k = Mathf.SmoothStep(0, 1, (float)((t - show) / DropGrow));
        float s = (float)(t - lastAt);
        // 0.3 through the scale-in, then down to 0.1 over 0.4 s (judge r2: at 0.3 ~200 glowing points read as confetti
        // at night; at 0.1 the stone's own shape reads), and full from the Return's end.
        float settle = Mathf.Lerp(DropDim, DropSettle, Mathf.SmoothStep(0, 1, (float)((t - show - DropGrow) / 0.4)));
        float light = Mathf.Lerp(settle, 1, Mathf.SmoothStep(DropDimFrom, DropDimTo, s));
        if (Args.Has("shot") && !dropLogged && t >= lastAt + RingTime(ringMax) + DropRingLag)
        {
            dropLogged = true;
            GD.Print($"flare {id}: the last drop shows {rt - boomRt:0.000} s real after the BOOM (ring at its edge {RingTime(ringMax):0.000} s Flare time)");
        }
        return (0.35f + 0.65f * k, k * light);
    }

    bool dropLogged;
    double rt, boomRt;

    /// <summary>How charred a body here is (judge 6 A2: beige bodies left lying in the ring read as wooden mannequins): 0
    /// till the BOOM's ring reaches it, charred within 3 frames of it, inside her reach (the ring's char). The living
    /// come back out of it as the ground's char goes (2.2-4.6 s); CrowdView keeps the dead charred.</summary>
    public float CharAt(double x, double z, bool living)
    {
        if (!Active || id != "burns_twice" || lastAt <= 0) return 0;
        if ((x - at.X) * (x - at.X) + (z - at.Z) * (z - at.Z) > (reach + 0.3) * (reach + 0.3)) return 0;
        float d = new Vector2((float)x - boomAt.X, (float)z - boomAt.Z).Length();
        double pass = lastAt + RingTime(d);
        float k = Mathf.Clamp((float)((t - pass) / (3 / 60.0)), 0, 1);
        return living ? k * (1 - Mathf.SmoothStep(2.2f, 4.6f, (float)(t - lastAt))) : k;
    }

    /// <summary>Whether the ring passed here 4 frames or more ago, inside her reach (the char audit's bodies).</summary>
    public bool RingPast(double x, double z)
    {
        if (!Active || id != "burns_twice" || lastAt <= 0) return false;
        if ((x - at.X) * (x - at.X) + (z - at.Z) * (z - at.Z) > (reach + 0.3) * (reach + 0.3)) return false;
        return t >= lastAt + RingTime(new Vector2((float)x - boomAt.X, (float)z - boomAt.Z).Length()) + 4 / 60.0;
    }

    /// <summary>The BOOM's ring (flare_world's flare_ring): its radius this long after the last word lands (Flare
    /// time: the hitstop's tenth-speed first), racing out and easing as it reaches the reach's edge in 0.7 s.</summary>
    static float RingAt(double s, float rmax)
    {
        float x = Mathf.Clamp((float)(s - 0.01) / 0.7f, 0, 1);
        return rmax * (1 - Mathf.Pow(1 - x, 2.5f));
    }

    /// <summary>When the ring crosses this far from where it struck (its inverse).</summary>
    double RingTime(float d)
    {
        float x = 1 - Mathf.Pow(Mathf.Clamp(1 - d / Math.Max(1, ringMax), 0, 1), 1 / 2.5f);
        return 0.01 + 0.7 * x;
    }

    float ringMax = 16;
    int audited;
    static readonly double[] AuditAfter = { 0, 0.3, 0.55 };

    /// <summary>For the clip's log (H7 r2, the 30+ shoot): live foes at the press within the Flare's radius, within a line
    /// Flare's line (its Strike's args line/lineWidth, the cleave's), and on the 1920x1080 screen.</summary>
    string PressCount(Ev.Flare e, Battle b)
    {
        var f = Content.Lamps.Flare(e.Id);
        double line = f?.Args.TryGetValue("line", out var lv) == true ? lv : 0, half = f?.Args.TryGetValue("lineWidth", out var hv) == true ? hv : 0;
        var cam = GetViewport()?.GetCamera3D();
        var vs = GetViewport()?.GetVisibleRect().Size ?? new Vector2(1920, 1080);
        int r = 0, l = 0, scr = 0;
        double ca = Math.Cos(e.Angle), sa = Math.Sin(e.Angle);
        foreach (var x in b.Enemies.Items)
        {
            if (!x.Alive) continue;
            double dx = x.X - e.X, dz = x.Z - e.Z;
            if (dx * dx + dz * dz < e.Radius * e.Radius) r++;
            if (line > 0) { double al = dx * ca + dz * sa, ac = -dx * sa + dz * ca; if (al > -1 && al < line && Math.Abs(ac) < half + 1.5) l++; }
            if (cam != null)
            {
                var wp = new Vector3((float)x.X, (float)HeightAt(x.X, x.Z) + 1, (float)x.Z);
                if (!cam.IsPositionBehind(wp)) { var sp = cam.UnprojectPosition(wp); if (sp.X >= 0 && sp.Y >= 0 && sp.X < vs.X && sp.Y < vs.Y) scr++; }
            }
        }
        return $"in_reach {r} (radius {e.Radius:0}){(line > 0 ? $" on_line {l}" : "")} on_screen {scr}";
    }

    int StandingIn(Battle b)
    {
        int n = 0;
        foreach (var e in b.Enemies.Items)
            if (e.Alive && (e.X - at.X) * (e.X - at.X) + (e.Z - at.Z) * (e.Z - at.Z) < reach * reach) n++;
        return n;
    }
}

using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// The survivor on screen (the web game's render/playerView.ts): the one
/// character with a full skeleton, blended clips and a light of their own.
/// Reads the fight's player state every frame and turns it into motion:
/// running that matches ground speed, a roll on a dash, the weapon arm
/// swinging when a blade fires (alternating cuts, a heavy swing for wide
/// arcs) on the upper body while the legs keep running, a flinch when
/// struck, a leap's arc, and a fall that stays down. The carried light is
/// the ember itself: it gutters when you are hurt and flares when you level.
///
/// The heroine plays her own clips where she has them (HerClips): her run,
/// its playback matched to her speed so her feet stay planted; swings that
/// alternate as the arcs do; her own dash, flinch and fall. Her clips run on
/// the fight's clock, so hit-stop and slow motion hold her too. She banks
/// into turns and turns her back toward a blow while her legs keep running
/// (HerCarriage).
/// </summary>
public partial class PlayerView : Node3D
{
    readonly Loadout loadout;
    readonly People.Person person;
    readonly AnimationTree tree;
    readonly AnimationNodeAnimation upper, full;
    readonly AnimationNodeAnimation? idleNode, runNode;
    public readonly OmniLight3D Light;
    /// <summary>The survivor in glass: reflections and echoes left behind.</summary>
    public readonly Reflections Reflections;
    readonly List<GeometryInstance3D> skin = new();
    readonly ShaderMaterial wraith = new() { Shader = GD.Load<Shader>("res://shaders/ghost.gdshader") };
    bool ghostly;
    Content.AbilityKind? rushSeen;
    double lastAttack = -1, hurtSeen, flare, castT, time, lastMuzzle = -1;
    int swing;
    bool dashing, dead;
    float speed;
    const float LightBase = 5;
    // Hers: her own clips and carriage.
    readonly bool her;
    readonly HerCarriage? carriage;
    readonly float runSpeed, sprintSpeed;
    bool upperNative, fullNative, fullSoft;
    float heading, turnRate, aim, aimHold, lastSpeed, accel;
    // Standing and running, for her breaks and her breath.
    double stillT, runT, ranFor, breakAt = 9;
    readonly RandomNumberGenerator rng = new();

    public PlayerView(Loadout lo)
    {
        loadout = lo;
        Name = "Survivor";
        var v = new PersonView(lo.Person, new World.Held { Right = lo.Arms.Right, Left = lo.Arms.Left, Forearm = lo.Arms.Forearm }, 0.8);
        person = v.Person;
        AddChild(v);
        her = person.Body == "heroine" && HerClips.Library() != null;
        var bt = new AnimationNodeBlendTree();
        AnimationNode moveNode;
        if (her)
        {
            v.Driven = true;
            // Standing and running blended by speed; the run played at the
            // rate that keeps her feet where they land.
            var idle = People.Clip(person, lo.Arms.Idle);
            var run = People.Clip(person, "Jog_Fwd_Loop");
            runSpeed = run.StartsWith(HerClips.Prefix) ? HerClips.Speed(run[HerClips.Prefix.Length..]) * person.Root.Scale.X : 5.3f;
            // Her sprint is her run pushed, in step with it (the same frames,
            // the left foot down at the start of both), so the two blend by
            // speed with the legs together; both keep running unseen.
            var sprint = run.StartsWith(HerClips.Prefix + "run_") ? "sprint" + run[(HerClips.Prefix.Length + 3)..] : "";
            sprintSpeed = HerClips.Has(sprint) ? HerClips.Speed(sprint) * person.Root.Scale.X : runSpeed;
            var mv = new AnimationNodeBlendTree();
            idleNode = new AnimationNodeAnimation { Animation = idle };
            runNode = new AnimationNodeAnimation { Animation = run };
            mv.AddNode("idle", idleNode, new Vector2(0, 0));
            mv.AddNode("run", runNode, new Vector2(0, 200));
            mv.AddNode("sprint", new AnimationNodeAnimation { Animation = HerClips.Has(sprint) ? HerClips.Prefix + sprint : run }, new Vector2(0, 400));
            mv.AddNode("fast", new AnimationNodeBlend2 { Sync = true }, new Vector2(200, 300));
            mv.AddNode("runScale", new AnimationNodeTimeScale(), new Vector2(400, 300));
            mv.AddNode("blend", new AnimationNodeBlend2(), new Vector2(600, 100));
            mv.ConnectNode("fast", 0, "run");
            mv.ConnectNode("fast", 1, "sprint");
            mv.ConnectNode("runScale", 0, "fast");
            mv.ConnectNode("blend", 0, "idle");
            mv.ConnectNode("blend", 1, "runScale");
            mv.ConnectNode("output", 0, "blend");
            moveNode = mv;
            carriage = new HerCarriage();
            person.Skeleton.AddChild(carriage);
            person.Skeleton.MoveChild(carriage, 0);
        }
        else
        {
            // Locomotion blended by speed; a swing on the upper body alone (the
            // hips and legs stay with the run); a roll, a leap or a fall on all of it.
            var move = new AnimationNodeBlendSpace1D { MinSpace = 0, MaxSpace = 6 };
            move.AddBlendPoint(new AnimationNodeAnimation { Animation = People.Resolve(lo.Arms.Idle) }, 0);
            move.AddBlendPoint(new AnimationNodeAnimation { Animation = People.Resolve("Walk_Loop") }, 1.8f);
            move.AddBlendPoint(new AnimationNodeAnimation { Animation = People.Resolve("Jog_Fwd_Loop") }, 4.4f);
            move.AddBlendPoint(new AnimationNodeAnimation { Animation = People.Resolve("Sprint_Loop") }, 6);
            moveNode = move;
        }
        upper = new AnimationNodeAnimation { Animation = People.Clip(person, lo.Arms.Attack[0]) };
        full = new AnimationNodeAnimation { Animation = People.Clip(person, "Roll") };
        var upperShot = new AnimationNodeOneShot { FadeInTime = 0.05, FadeOutTime = 0.18, FilterEnabled = true };
        var fullShot = new AnimationNodeOneShot { FadeInTime = 0.05, FadeOutTime = 0.2 };
        var skel = person.Skeleton;
        for (int b = 0; b < skel.GetBoneCount(); b++)
        {
            var name = skel.GetBoneName(b);
            if (name is "root" or "pelvis" || name.StartsWith("thigh") || name.StartsWith("calf") || name.StartsWith("foot") || name.StartsWith("ball") || name.StartsWith("glute")) continue;
            upperShot.SetFilterPath($"Armature/Skeleton3D:{name}", true);
        }
        var upperScale = new AnimationNodeTimeScale();
        var fullScale = new AnimationNodeTimeScale();
        bt.AddNode("move", moveNode, new Vector2(0, 0));
        bt.AddNode("upper", upper, new Vector2(0, 200));
        bt.AddNode("upperScale", upperScale, new Vector2(200, 200));
        bt.AddNode("upperShot", upperShot, new Vector2(400, 100));
        bt.AddNode("full", full, new Vector2(400, 300));
        bt.AddNode("fullScale", fullScale, new Vector2(600, 300));
        bt.AddNode("fullShot", fullShot, new Vector2(800, 150));
        bt.ConnectNode("upperScale", 0, "upper");
        bt.ConnectNode("upperShot", 0, "move");
        bt.ConnectNode("upperShot", 1, "upperScale");
        bt.ConnectNode("fullScale", 0, "full");
        bt.ConnectNode("fullShot", 0, "upperShot");
        bt.ConnectNode("fullShot", 1, "fullScale");
        bt.ConnectNode("output", 0, "fullShot");
        tree = new AnimationTree { TreeRoot = bt, RootNode = "..", Active = true };
        tree.AddAnimationLibrary("", People.Clips());
        if (her)
        {
            tree.AddAnimationLibrary("her", HerClips.Library());
            // Her clips run on the fight's clock (Update advances them), so a
            // hit-stop or a perfect dodge's slow motion holds her as well.
            tree.CallbackModeProcess = AnimationMixer.AnimationCallbackModeProcess.Manual;
        }
        person.Root.AddChild(tree);
        Light = new OmniLight3D { LightColor = new Color("#ffb070"), LightEnergy = LightBase / Mathf.Pi, OmniRange = 11, OmniAttenuation = 1.4f, ShadowEnabled = false };
        AddChild(Light);
        Reflections = new Reflections(lo);
        AddChild(Reflections);
        Gather(this);
        wraith.SetShaderParameter("tint", new Color(0.5f, 0.42f, 0.9f));
        wraith.SetShaderParameter("body", 0.05f);
        wraith.SetShaderParameter("rim", 0.9f);
    }

    void Gather(Node n)
    {
        if (n is GeometryInstance3D g && n is not global::SurvivorUnchained.View.Reflections) skin.Add(g);
        foreach (var c in n.GetChildren()) if (c is not global::SurvivorUnchained.View.Reflections) Gather(c);
    }

    /// <summary>Half a ghost (a wraith's walk): see-through, rimmed in cold light.</summary>
    void Ghostly(bool on)
    {
        if (on == ghostly) return;
        ghostly = on;
        foreach (var g in skin)
        {
            if (!IsInstanceValid(g)) continue;
            g.Transparency = on ? 0.55f : 0;
            g.MaterialOverlay = on ? wraith : null;
        }
    }

    public Vector3 FigurePosition => person.Root.GlobalPosition;

    void Upper(string clip, double speed)
    {
        upper.Animation = People.Clip(person, clip);
        upperNative = upper.Animation.ToString().StartsWith(HerClips.Prefix);
        tree.Set("parameters/upperScale/scale", speed);
        tree.Set("parameters/upperShot/request", (int)AnimationNodeOneShot.OneShotRequest.Fire);
    }

    /// <summary>One of her own clips on her upper body, by its own name.</summary>
    bool UpperHer(string clip, double speed)
    {
        if (!her || !HerClips.Has(clip)) return false;
        upper.Animation = HerClips.Prefix + clip;
        upperNative = true;
        tree.Set("parameters/upperScale/scale", speed);
        tree.Set("parameters/upperShot/request", (int)AnimationNodeOneShot.OneShotRequest.Fire);
        return true;
    }

    void Full(string clip, double speed)
    {
        full.Animation = People.Clip(person, clip);
        fullNative = full.Animation.ToString().StartsWith(HerClips.Prefix);
        fullSoft = false;
        tree.Set("parameters/fullScale/scale", speed);
        tree.Set("parameters/fullShot/request", (int)AnimationNodeOneShot.OneShotRequest.Fire);
    }

    /// <summary>One of her own on the whole of her: soft ones (a fidget, a
    /// breath caught) give way the moment she moves.</summary>
    bool FullHer(string clip, double speed, bool soft)
    {
        if (!her || !HerClips.Has(clip)) return false;
        full.Animation = HerClips.Prefix + clip;
        fullNative = true;
        fullSoft = soft;
        tree.Set("parameters/fullScale/scale", speed);
        tree.Set("parameters/fullShot/request", (int)AnimationNodeOneShot.OneShotRequest.Fire);
        return true;
    }

    /// <summary>An art's landing or stop plays out only while she stands:
    /// once the art is done (artTail) and she moves, it fades into her run.</summary>
    void ArtTail(float sp)
    {
        if (artTail < 0 || time < artTail) return;
        if (sp > 0.6f && (bool)tree.Get("parameters/fullShot/active"))
            tree.Set("parameters/fullShot/request", (int)AnimationNodeOneShot.OneShotRequest.FadeOut);
        if (sp > 0.6f || !(bool)tree.Get("parameters/fullShot/active")) artTail = -1;
    }

    double artTail = -1;

    bool Busy => (bool)tree.Get("parameters/upperShot/active") || (bool)tree.Get("parameters/fullShot/active");

    public void LevelFlare() => flare = 1;

    /// <summary>An art used: the hands that go with it.</summary>
    public void OnAbility(string id)
    {
        switch (id)
        {
            case "mirror_step" or "echo_step" or "echo_recall" or "time_slip" or "blink":
                Upper("Spell_Simple_Shoot", 1.8);
                break;
            case "grapple" or "grapple_miss":
                Upper("OverhandThrow", 2.2);
                break;
            case "warcry" or "sprint" or "cinder_trail" or "wraith_walk":
                if (!Busy) Upper("Punch_Cross", 1.4);
                break;
        }
    }

    /// <summary>A weapon of hers loosed (a bolt, a spell, a thrown knife), at
    /// the angle it went: the hands that loosed it, timed to it.</summary>
    public void OnMuzzle(double angle)
    {
        if (!her || dead) return;
        var clip = person.Kind switch { "crossbow" => "crossbow_shoot", "wand" => "cast_flick", "staff" => "cast_bolt", "daggers" => "throw", _ => "" };
        // (Several weapons may loose at once: one gesture at a time, and
        // never over a dash or a fall.)
        if (clip == "" || time - lastMuzzle < 0.4 || (bool)tree.Get("parameters/fullShot/active")) return;
        if (UpperHer(clip, 1.5)) { Strike(angle); lastMuzzle = time; }
    }

    /// <summary>Up again after a fall (the prologue's second chances).</summary>
    public void Revive()
    {
        dead = false;
        tree.Active = true;
        Full("Lie_StandUp", 1.2);
    }

    /// <summary>A blow aimed at `angle` (the fight's: atan2(z, x)): her back
    /// turns to it if it is within reach of a turn of the waist, else she
    /// turns whole.</summary>
    void Strike(double angle)
    {
        float face = Mathf.Pi / 2 - (float)angle;
        float d = Mathf.Wrap(face - Rotation.Y, -Mathf.Pi, Mathf.Pi);
        if (!her || speed < 1.5f || Mathf.Abs(d) > Mathf.DegToRad(110))
        {
            Rotation = new Vector3(0, face, 0);
            aim = 0;
        }
        else aim = Mathf.RadToDeg(d);
        aimHold = 0.45f;
    }

    public void Update(Battle b, double dt, double fightTime, System.Func<double, double, double> heightAt)
    {
        time += dt;
        if (her) tree.Advance(dt);
        var p = b.Player;
        double y = heightAt(p.X, p.Z);
        if (p.Leap is { } leap) y += Mathf.Sin((float)(Mathf.Min(1, leap.T / leap.Dur) * Mathf.Pi)) * 2.2;
        Position = new Vector3((float)p.X, (float)y, (float)p.Z);
        Reflections.Update(b, dt, heightAt);
        Ghostly(p.Alive && b.Art.WraithT > 0);
        if (!p.Alive)
        {
            if (!dead)
            {
                // A fall that stays down: the clip played out and held.
                dead = true;
                tree.Active = false;
                var death = People.Clip(person, "Death_A");
                person.Anim.Play(death, 0.1);
                if (person.Pose != null) person.Pose.Native = death.StartsWith(HerClips.Prefix) ? 1 : 0;
                if (carriage != null) carriage.Aim = carriage.Bank = carriage.Tilt = 0;
            }
            Light.LightEnergy = Mathf.Lerp(Light.LightEnergy, 0.6f / Mathf.Pi, 1 - Mathf.Exp(-2 * (float)dt));
            return;
        }
        float sp = (float)Mathf.Sqrt(p.Vx * p.Vx + p.Vz * p.Vz);
        // Face where you are going, or where you just struck (she, moving,
        // keeps her legs' line and turns her back to the blow instead).
        aimHold -= (float)dt;
        if (p.AttackAnim is { } aa && fightTime - aa.T < 0.35 && !her) Rotation = new Vector3(0, (float)(Mathf.Pi / 2 - aa.Angle), 0);
        // (In the air she keeps the facing she sprang with: her velocity is stale there.)
        else if (sp > 0.4f && p.Leap == null) Rotation = new Vector3(0, Mathf.LerpAngle(Rotation.Y, Mathf.Atan2((float)p.Vx, (float)p.Vz), 1 - Mathf.Exp(-14 * (float)dt)), 0);
        // Dash: a roll (hers: a low lunge).
        if (p.DashT > 0 && !dashing)
        {
            dashing = true;
            Rotation = new Vector3(0, Mathf.Atan2((float)p.DashDX, (float)p.DashDZ), 0);
            aim = 0;
            Full("Dodge_Forward", her && HerClips.Has("dash") ? 1.0 : 1.9);
        }
        else if (p.DashT <= 0) dashing = false;
        // A leap or a vault (hers are timed to the art already).
        if (p.Leap is { } l2 && l2.T < dt * 2)
        {
            bool vault = l2.Kind == Content.AbilityKind.Vault;
            float dx = (float)(l2.X1 - l2.X0), dz = (float)(l2.Z1 - l2.Z0);
            // A vault against the way she faces (standing, she springs back
            // from her facing) is a spring backwards, eyes on what she
            // leaves; any other leap faces the way it goes.
            bool back = vault && dx * Mathf.Sin(Rotation.Y) + dz * Mathf.Cos(Rotation.Y) < 0;
            if (dx * dx + dz * dz > 0.01f) Rotation = new Vector3(0, back ? Mathf.Atan2(-dx, -dz) : Mathf.Atan2(dx, dz), 0);
            aim = 0;
            if (!(back && FullHer("vault_back", 1, false)))
            {
                var jump = vault ? "Jump_Start" : "Jump_Full_Short";
                bool own = People.Clip(person, jump).StartsWith(HerClips.Prefix);
                Full(jump, own ? 1.0 : vault ? 1.8 : 1.3);
            }
            // Once down, the landing gives way as soon as she moves on.
            artTail = time + l2.Dur + 0.1;
        }
        ArtTail(sp);
        // A charge behind the shield; a haul on the chain, blade first.
        if (b.Art.Rush != rushSeen)
        {
            rushSeen = b.Art.Rush;
            if (rushSeen is { } rk)
            {
                Rotation = new Vector3(0, Mathf.Atan2((float)b.Art.RushDX, (float)b.Art.RushDZ), 0);
                var rush = rk == Content.AbilityKind.BullRush ? "Shield_Dash" : "Sword_Dash";
                bool own = People.Clip(person, rush).StartsWith(HerClips.Prefix);
                Full(rush, own ? 1.0 : rk == Content.AbilityKind.BullRush ? 1.5 : 2.2);
            }
        }
        // Weapon swings: the blade drives the arm. Hers alternate as the
        // arcs do (the first from her left), the wide arcs her heavy cut.
        if (p.AttackAnim is { } a && a.T != lastAttack)
        {
            lastAttack = a.T;
            var swings = her ? HerClips.Swings(person.Kind) : System.Array.Empty<string>();
            bool played = false;
            if (swings.Length > 0)
                played = a.Heavy ? UpperHer(HerClips.Heavy(person.Kind), 1.5) : UpperHer(swings[swing % swings.Length], 1.6);
            if (!played)
            {
                var clip = a.Heavy ? loadout.Arms.Heavy : loadout.Arms.Attack[swing % loadout.Arms.Attack.Length];
                Upper(clip, 1.6);
            }
            swing++;
            if (her) Strike(a.Angle);
        }
        // Casters raise a hand now and then as their spells go (hers move
        // with the spells themselves: OnMuzzle).
        castT -= dt;
        if (loadout.Arms.Cast != null && castT <= 0 && b.Weapons.Count > 0 && !Busy && sp < 3 && !(her && HerClips.Has("cast_bolt")))
        {
            castT = 1.6;
            Upper(loadout.Arms.Cast, 1.4);
        }
        // Flinch.
        if (p.HurtT > 0.25 && hurtSeen <= 0)
        {
            hurtSeen = 0.4;
            if (!Busy) Upper("Hit_A", her && HerClips.Has("hit") ? 1.2 : 1.6);
        }
        hurtSeen -= dt;
        speed = Mathf.Lerp(speed, sp, 1 - Mathf.Exp(-10 * (float)dt));
        if (her) Rest(b, dt, sp);
        if (her) Carry((float)dt, sp);
        else tree.Set("parameters/move/blend_position", speed);
        // The carried light: steadier at full health, guttering when hurt.
        double hp = p.Hp / b.MaxHp;
        flare = Mathf.Max(0, flare - dt * 0.8);
        double flicker = Mathf.Sin((float)(time * 7.3)) * 0.25 + Mathf.Sin((float)(time * 17.1)) * 0.15 + (hp < 0.35 ? Mathf.Sin((float)(time * 31)) * 0.6 : 0);
        Light.LightEnergy = (float)((LightBase * (0.7 + 0.3 * hp) + flicker + flare * 20) / Mathf.Pi);
        // A lantern carries further; under the Oath of the Moonless, not far at all.
        Light.OmniRange = (float)((11 + flare * 6) * b.Stats.Get(Stat.LightRadius) * b.Rules.Light);
        Light.Position = new Vector3(0, 2.4f, 0.4f);
        // Unseen: a ghost, flickering.
        Visible = !(p.InvisibleT > 0 && (int)(time * 12) % 3 == 0);
    }

    /// <summary>When nothing is near: a breath caught after a long run, and
    /// now and then, standing, her calling's fidget. Either gives way the
    /// moment she moves.</summary>
    void Rest(Battle b, double dt, float sp)
    {
        var p = b.Player;
        if (fullSoft && sp > 0.6 && (bool)tree.Get("parameters/fullShot/active"))
        {
            tree.Set("parameters/fullShot/request", (int)AnimationNodeOneShot.OneShotRequest.FadeOut);
            fullSoft = false;
        }
        if (sp > 3) { runT += dt; stillT = 0; ranFor = runT; return; }
        if (sp > 0.3) { stillT = 0; return; }
        // Pulling up out of a run: onto whichever foot was coming down.
        if (runT > 0.4 && !(bool)tree.Get("parameters/fullShot/active"))
        {
            var pos = tree.Get("parameters/move/run/current_position");
            var len = tree.Get("parameters/move/run/current_length");
            float phase = pos.VariantType != Variant.Type.Nil && len.VariantType != Variant.Type.Nil && (float)len > 0
                ? (float)pos / (float)len : rng.Randf();
            FullHer($"stop_{person.Calling}_{(phase >= 0.25f && phase < 0.75f ? "r" : "l")}", 1, true);
        }
        runT = 0;
        stillT += dt;
        // (A breath is caught on stopping, or not at all.)
        if (stillT > 1.0) ranFor = 0;
        bool calm = b.NearestHostile(p.X, p.Z, 14) == null && (!Busy || fullSoft);
        if (!calm) { breakAt = Mathf.Max((float)breakAt, (float)stillT + 4); return; }
        if (ranFor > 6 && stillT > 0.75)
        {
            ranFor = 0;
            FullHer("catch_breath", 1, true);
            breakAt = stillT + rng.RandfRange(9, 14);
            return;
        }
        ranFor = 0;
        if (stillT >= breakAt)
        {
            breakAt = stillT + rng.RandfRange(10, 16);
            FullHer($"idle_{person.Calling}_break", 1, true);
        }
    }

    /// <summary>Her run and stand, her lean and her aim, this frame.</summary>
    void Carry(float dt, float sp)
    {
        // Standing to running over the first two metres a second; the run
        // at the rate her ground speed asks.
        float w = Mathf.SmoothStep(0.25f, 2.2f, speed);
        tree.Set("parameters/move/blend/blend_amount", w);
        // Into the sprint as she goes past her run's own speed; the pair
        // played at the rate the blend of their speeds asks.
        float fast = sprintSpeed > runSpeed ? Mathf.SmoothStep(runSpeed * 1.1f, sprintSpeed * 0.95f, speed) : 0;
        tree.Set("parameters/move/fast/blend_amount", fast);
        float natural = Mathf.Lerp(runSpeed, sprintSpeed, fast);
        tree.Set("parameters/move/runScale/scale", Mathf.Clamp(speed / natural, 0.55f, 1.5f));
        // Her corrective layer stands down for whichever half plays hers.
        bool fullOn = (bool)tree.Get("parameters/fullShot/active"), upperOn = (bool)tree.Get("parameters/upperShot/active");
        float lowerT = fullOn ? (fullNative ? 1 : 0) : 1;
        float upperT = fullOn ? (fullNative ? 1 : 0) : upperOn ? (upperNative ? 1 : 0) : 1;
        if (person.Pose is HerPose hp)
        {
            float k = 1 - Mathf.Exp(-14 * dt);
            hp.Lower += (lowerT - hp.Lower) * k;
            hp.Upper += (upperT - hp.Upper) * k;
        }
        if (carriage == null || dt <= 0) return;
        // Banking into turns: how fast she is turning, times how fast she
        // is going (a runner leans into a curve, a walker hardly at all).
        float rate = Mathf.Wrap(Rotation.Y - heading, -Mathf.Pi, Mathf.Pi) / dt;
        heading = Rotation.Y;
        turnRate = Mathf.Lerp(turnRate, rate, 1 - Mathf.Exp(-10 * dt));
        float bank = Mathf.Clamp(-turnRate * speed * 1.6f, -14, 14);
        carriage.Bank = Mathf.Lerp(carriage.Bank, bank, 1 - Mathf.Exp(-8 * dt));
        // Into a start, back out of a stop.
        float acc = (sp - lastSpeed) / dt;
        lastSpeed = sp;
        accel = Mathf.Lerp(accel, acc, 1 - Mathf.Exp(-12 * dt));
        carriage.Tilt = Mathf.Lerp(carriage.Tilt, Mathf.Clamp(accel * 0.35f, -9, 7), 1 - Mathf.Exp(-10 * dt));
        // Her back to the blow while it lasts, then home.
        float aimTo = aimHold > 0 ? aim : 0;
        carriage.Aim = Mathf.Lerp(carriage.Aim, aimTo, 1 - Mathf.Exp((aimHold > 0 ? -30 : -8) * dt));
    }
}

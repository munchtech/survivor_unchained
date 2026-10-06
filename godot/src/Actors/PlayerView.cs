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
/// The heroine plays her own clips where she has them (OwnClips; the hero his): her run,
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
    // (A name made once, not a new one every frame for the collector.)
    static readonly StringName BlendPosition = "parameters/move/blend_position";
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
    // Their own clips (hers, or his) and carriage.
    readonly bool mine;
    readonly OwnClips own = OwnClips.Her;
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
        if (person.Own is { } o) own = o;
        mine = person.Own != null;
        var bt = new AnimationNodeBlendTree();
        AnimationNode moveNode;
        if (mine)
        {
            v.Driven = true;
            // Standing and running blended by speed; the run played at the
            // rate that keeps her feet where they land.
            var idle = People.Clip(person, lo.Arms.Idle);
            var run = People.Clip(person, "Jog_Fwd_Loop");
            runSpeed = run.StartsWith(own.Prefix) ? own.Speed(run[own.Prefix.Length..]) * person.Root.Scale.X : 5.3f;
            // Her sprint is her run pushed, in step with it (the same frames,
            // the left foot down at the start of both), so the two blend by
            // speed with the legs together; both keep running unseen.
            var sprint = run.StartsWith(own.Prefix + "run_") ? "sprint" + run[(own.Prefix.Length + 3)..] : "";
            sprintSpeed = own.Has(sprint) ? own.Speed(sprint) * person.Root.Scale.X : runSpeed;
            var mv = new AnimationNodeBlendTree();
            idleNode = new AnimationNodeAnimation { Animation = idle };
            runNode = new AnimationNodeAnimation { Animation = run };
            mv.AddNode("idle", idleNode, new Vector2(0, 0));
            mv.AddNode("run", runNode, new Vector2(0, 200));
            mv.AddNode("sprint", new AnimationNodeAnimation { Animation = own.Has(sprint) ? own.Prefix + sprint : run }, new Vector2(0, 400));
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
        if (mine)
        {
            tree.AddAnimationLibrary(own.Name, own.Library());
            // Her clips run on the fight's clock (Update advances them), so a
            // hit-stop or a perfect dodge's slow motion holds her as well.
            tree.CallbackModeProcess = AnimationMixer.AnimationCallbackModeProcess.Manual;
        }
        person.Root.AddChild(tree);
        Light = new OmniLight3D { LightColor = new Color("#ffb070"), LightEnergy = LightBase / Mathf.Pi, OmniRange = 11, OmniAttenuation = 1.4f, ShadowEnabled = false, Position = new Vector3(0, 2.4f, 0.4f) };
        AddChild(Light);
        Reflections = new Reflections(lo);
        AddChild(Reflections);
        Gather(this);
        wraith.SetShaderParameter("tint", new Color(0.5f, 0.42f, 0.9f));
        wraith.SetShaderParameter("body", 0.05f);
        wraith.SetShaderParameter("rim", 0.9f);
    }

    /// <summary>In place of the figure before it (what she holds changed): where it stood and
    /// the way it faced, and posed now, not in its bind pose until the next frame's update.</summary>
    public void Follow(PlayerView old)
    {
        Position = old.Position;
        Rotation = old.Rotation;
        heading = old.heading;
        speed = old.speed;
        Visible = old.Visible;
        // Her carried light as it was: a new one lit her from her feet, at its first strength,
        // for the frame before its first update, and she flashed pale.
        Light.LightEnergy = old.Light.LightEnergy;
        Light.OmniRange = old.Light.OmniRange;
        time = old.time;
        flare = old.flare;
        tree.Advance(0);
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
    /// <summary>Out of the picture while a cinematic's double plays her.</summary>
    public bool Hidden;
    /// <summary>The way she turns to while she stands (the book open: to the view); null: her own.</summary>
    public float? Turned;
    /// <summary>What she lifts her head to while she stands (the book open: the camera; her idle
    /// carries her head low, and framed close her face was turned down from it); null lets it go.</summary>
    public Node3D? Watch;
    SurvivorUnchained.View.HeadTurn? headTurn;

    void Watching(bool standing)
    {
        if (Watch == null && headTurn == null) return;
        if (headTurn == null) person.Skeleton.AddChild(headTurn = new SurvivorUnchained.View.HeadTurn { Limit = 40, Rate = 1.5f });
        bool on = Watch != null && standing && IsInstanceValid(Watch);
        if (on) headTurn.Target = Watch!.GlobalPosition;
        headTurn.Want = on ? 0.85f : 0;
    }

    /// <summary>Handed her body by a cinematic: she stands where its double
    /// stood, facing as it faced (heading as NpcActor turns: 0 south, pi/2
    /// east), already moving at `moving` m/s if it was walking. Her facing
    /// otherwise follows only her own steps, so it would keep whatever it was
    /// before the cinematic (C01 handed her back facing south, not north).</summary>
    public void Face(float facing, Vector3 at, float moving = 0)
    {
        Position = at;
        Rotation = new Vector3(0, facing, 0);
        heading = facing;
        speed = lastSpeed = moving;
        aim = aimHold = 0;
    }

    void Upper(string clip, double speed)
    {
        upper.Animation = People.Clip(person, clip);
        upperNative = upper.Animation.ToString().StartsWith(own.Prefix);
        tree.Set("parameters/upperScale/scale", speed);
        tree.Set("parameters/upperShot/request", (int)AnimationNodeOneShot.OneShotRequest.Fire);
    }

    /// <summary>One of her own clips on her upper body, by its own name.</summary>
    bool UpperHer(string clip, double speed)
    {
        if (!mine || !own.Has(clip)) return false;
        upper.Animation = own.Prefix + clip;
        upperNative = true;
        tree.Set("parameters/upperScale/scale", speed);
        tree.Set("parameters/upperShot/request", (int)AnimationNodeOneShot.OneShotRequest.Fire);
        return true;
    }

    void Full(string clip, double speed)
    {
        full.Animation = People.Clip(person, clip);
        fullNative = full.Animation.ToString().StartsWith(own.Prefix);
        fullSoft = false;
        tree.Set("parameters/fullScale/scale", speed);
        tree.Set("parameters/fullShot/request", (int)AnimationNodeOneShot.OneShotRequest.Fire);
    }

    /// <summary>One of her own on the whole of her: soft ones (a fidget, a
    /// breath caught) give way the moment she moves.</summary>
    bool FullHer(string clip, double speed, bool soft)
    {
        if (!mine || !own.Has(clip)) return false;
        full.Animation = own.Prefix + clip;
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
                // (Hers: the chain loosed like a thrown knife; a haul that
                // follows plays over it.)
                if (!UpperHer("throw", 1.6)) Upper("OverhandThrow", 2.2);
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
        if (!mine || dead) return;
        var clip = person.Kind switch { "crossbow" => "crossbow_shoot", "wand" => "cast_flick", "staff" => "cast_bolt", "daggers" => "throw", _ => "" };
        // (Several weapons may loose at once: one gesture at a time, and
        // never over a dash or a fall.)
        if (clip == "" || time - lastMuzzle < 0.4 || (bool)tree.Get("parameters/fullShot/active")) return;
        if (UpperHer(clip, 1.5)) { Strike(angle); lastMuzzle = time; }
    }

    /// <summary>A story fall: down as at a death and held there, though the
    /// fight keeps her at a breath of life while the fall is staged
    /// (StoryNight.OnFall); up again with Revive. (Without it she stood
    /// through her own fall.)</summary>
    public void Fall() => fallen = true;
    bool fallen;

    /// <summary>Up again after a fall (the prologue's second chances, a story fall's rise).</summary>
    public void Revive()
    {
        dead = fallen = false;
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
        if (!mine || speed < 1.5f || Mathf.Abs(d) > Mathf.DegToRad(110))
        {
            Rotation = new Vector3(0, face, 0);
            aim = 0;
        }
        else aim = Mathf.RadToDeg(d);
        aimHold = 0.45f;
    }

    /// <summary>A frame of her: drawn at x, z (between the fight's steps: Interp), `leap` through a leap (-1: none).</summary>
    public void Update(Battle b, double x, double z, double leap, double dt, double fightTime, System.Func<double, double, double> heightAt)
    {
        time += dt;
        if (mine) tree.Advance(dt);
        var p = b.Player;
        double y = heightAt(x, z);
        if (leap >= 0) y += Mathf.Sin((float)(leap * Mathf.Pi)) * 2.2;
        Position = new Vector3((float)x, (float)y, (float)z);
        Reflections.Update(b, dt, heightAt);
        Ghostly(p.Alive && b.Art.WraithT > 0);
        if (!p.Alive || fallen)
        {
            if (!dead)
            {
                // A fall that stays down: the clip played out and held.
                dead = true;
                tree.Active = false;
                var death = People.Clip(person, "Death_A");
                // Struck down from in front, she goes over onto her back;
                // from behind, or by what was in her (poison, burning), she
                // folds forward onto her face.
                if (mine && p.FellTo == null && p.LastKiller is { } k && own.Has("death_back")
                    && (k.X - p.X) * Mathf.Sin(Rotation.Y) + (k.Z - p.Z) * Mathf.Cos(Rotation.Y) > 0)
                    death = own.Prefix + "death_back";
                person.Anim.Play(death, 0.1);
                if (person.Pose != null) person.Pose.Native = death.StartsWith(own.Prefix) ? 1 : 0;
                if (carriage != null) carriage.Aim = carriage.Bank = carriage.Tilt = 0;
            }
            Light.LightEnergy = Mathf.Lerp(Light.LightEnergy, 0.6f / Mathf.Pi, 1 - Mathf.Exp(-2 * (float)dt));
            return;
        }
        float sp = (float)Mathf.Sqrt(p.Vx * p.Vx + p.Vz * p.Vz);
        // Face where you are going, or where you just struck (she, moving,
        // keeps her legs' line and turns her back to the blow instead).
        aimHold -= (float)dt;
        if (p.AttackAnim is { } aa && fightTime - aa.T < 0.35 && !mine) Rotation = new Vector3(0, (float)(Mathf.Pi / 2 - aa.Angle), 0);
        // (In the air she keeps the facing she sprang with: her velocity is stale there.)
        else if (sp > 0.4f && p.Leap == null) Rotation = new Vector3(0, Mathf.LerpAngle(Rotation.Y, Mathf.Atan2((float)p.Vx, (float)p.Vz), 1 - Mathf.Exp(-14 * (float)dt)), 0);
        // Turned to the view while a panel frames her (FollowCamera.ScreenFrame), standing.
        if (Turned is float tw && sp < 0.4f && p.AttackAnim == null)
            Rotation = new Vector3(0, Mathf.LerpAngle(Rotation.Y, tw, 1 - Mathf.Exp(-4 * (float)dt)), 0);
        Watching(sp < 0.4f && p.AttackAnim == null);
        // Dash: a roll (hers: a low lunge).
        if (p.DashT > 0 && !dashing)
        {
            dashing = true;
            Rotation = new Vector3(0, Mathf.Atan2((float)p.DashDX, (float)p.DashDZ), 0);
            aim = 0;
            Full("Dodge_Forward", mine && own.Has("dash") ? 1.0 : 1.9);
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
                bool native = own.Owns(People.Clip(person, jump));
                Full(jump, native ? 1.0 : vault ? 1.8 : 1.3);
            }
            // Once down, the landing gives way as soon as she moves on.
            artTail = time + l2.Dur + 0.1;
        }
        ArtTail(sp);
        // A charge behind the shield; a haul on the chain, blade first.
        if (b.Art.Rush != rushSeen)
        {
            var was = rushSeen;
            rushSeen = b.Art.Rush;
            if (rushSeen is { } rk)
            {
                Rotation = new Vector3(0, Mathf.Atan2((float)b.Art.RushDX, (float)b.Art.RushDZ), 0);
                aim = 0;
                var rush = rk == Content.AbilityKind.BullRush ? "Shield_Dash" : "Sword_Dash";
                bool native = own.Owns(People.Clip(person, rush));
                Full(rush, native ? 1.0 : rk == Content.AbilityKind.BullRush ? 1.5 : 2.2);
                // Her charge's plant and shove show, then give way if she runs on.
                if (rk == Content.AbilityKind.BullRush) artTail = time + b.Art.RushT + 0.25;
            }
            // Hauled all the way in: the blow she lands with (hers held in
            // the air until now, for however long the haul took).
            else if (was == Content.AbilityKind.Grapple && FullHer("chain_strike", 1, false))
                artTail = time + 0.3;
        }
        // Weapon swings: the blade drives the arm. Hers alternate as the
        // arcs do (the first from her left), the wide arcs her heavy cut.
        if (p.AttackAnim is { } a && a.T != lastAttack)
        {
            lastAttack = a.T;
            var swings = mine ? HerClips.Swings(person.Kind) : System.Array.Empty<string>();
            bool played = false;
            if (swings.Length > 0)
                played = a.Heavy ? UpperHer(HerClips.Heavy(person.Kind), 1.5) : UpperHer(swings[swing % swings.Length], 1.6);
            if (!played)
            {
                var clip = a.Heavy ? loadout.Arms.Heavy : loadout.Arms.Attack[swing % loadout.Arms.Attack.Length];
                Upper(clip, 1.6);
            }
            swing++;
            if (mine) Strike(a.Angle);
        }
        // Casters raise a hand now and then as their spells go (hers move
        // with the spells themselves: OnMuzzle).
        castT -= dt;
        if (loadout.Arms.Cast != null && castT <= 0 && b.Weapons.Count > 0 && !Busy && sp < 3 && !(mine && own.Has("cast_bolt")))
        {
            castT = 1.6;
            Upper(loadout.Arms.Cast, 1.4);
        }
        // Flinch.
        if (p.HurtT > 0.25 && hurtSeen <= 0)
        {
            hurtSeen = 0.4;
            // On the move or mid-blow, her own flinch is laid over what she is
            // doing (the legs keep running, the arms keep their hold); standing,
            // the whole of her upper body takes the hit.
            bool jolt = mine && own.Has("flinch") && person.Gestures != null && (sp > 1.5f || Busy);
            if (jolt) person.Gestures!.Play(person.Anim.GetAnimation(own.Prefix + "flinch"));
            else if (!Busy) Upper("Hit_A", mine && own.Has("hit") ? 1.2 : 1.6);
        }
        hurtSeen -= dt;
        speed = Mathf.Lerp(speed, sp, 1 - Mathf.Exp(-10 * (float)dt));
        if (mine) Rest(b, dt, sp);
        if (mine) Carry((float)dt, sp);
        else tree.Set(BlendPosition, speed);
        // The carried light: steadier at full health, guttering when hurt.
        double hp = p.Hp / b.MaxHp;
        flare = Mathf.Max(0, flare - dt * 0.8);
        double flicker = Mathf.Sin((float)(time * 7.3)) * 0.25 + Mathf.Sin((float)(time * 17.1)) * 0.15 + (hp < 0.35 ? Mathf.Sin((float)(time * 31)) * 0.6 : 0);
        Light.LightEnergy = (float)((LightBase * (0.7 + 0.3 * hp) + flicker + flare * 20) / Mathf.Pi);
        // A lantern carries further; under the Oath of the Moonless, not far at all.
        Light.OmniRange = (float)((11 + flare * 6) * b.Stats.Get(Stat.LightRadius) * b.Rules.Light);
        Light.Position = new Vector3(0, 2.4f, 0.4f);
        // Unseen: a ghost, flickering.
        Visible = !Hidden && !(p.InvisibleT > 0 && (int)(time * 12) % 3 == 0);
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

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
    /// <summary>Her figure (HerWear.Busy: a live swap dressing it).</summary>
    public People.Person Person => person;   // (also the shot tools: --hairdump in play)
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
    /// <summary>How much of her carried light lights her (1: all): the book open by day dims it
    /// (GameMenus), eased. Under the sun as well, from a hand's breadth over her head it lit her
    /// face flat and cream-white, washed out beside the panel.</summary>
    public float LampScale = 1;
    /// <summary>True: her carried light lights the ground round her but not her (the close view by night, where
    /// from over her head it filled her face flat; E1 round 3).</summary>
    public bool LampOffHer;
    /// <summary>Her own render layer (11): the close view by night moves her meshes off people's layer (2) onto it, so the
    /// camp's fire, which stood behind the lens and filled her face flat from the front, can be kept off her alone (E1 judge 3).</summary>
    public const uint HerLayer = 1u << 10;
    /// <summary>Her hair's own layer (13) while she is on hers: lit as the rest of her (the key, her share of the fire, the
    /// zone's lights and the moon), but not by the close view's moon rim (GameCloseUp), which lifted her copper crown toward
    /// strawberry blonde (G1 r4). --close-rim-hair: her hair on HerLayer with the rest of her, as before.</summary>
    public const uint HerHairLayer = 1u << 12;
    static readonly bool RimHair = Args.Has("close-rim-hair");
    /// <summary>Her metal's own layer (14) while she is on hers: her weapon and the metal of her outfit and armor (IsMetal;
    /// her leather, fur and cloth stay on HerLayer: on this layer they went lavender chrome by night, judge J2), so the close view's moon rim can keep its sheen on metal and none on her skin
    /// (GameCloseUp: with the rim's sheen off her neck's lavender band went, but her axe head went flat black, judge J1).
    /// --close-rim-gear off: her gear on HerLayer with her skin, as before.</summary>
    public const uint HerGearLayer = 1u << 13;
    static readonly bool GearOwn = Args.Get("close-rim-gear") != "off";
    /// <summary>HerLayer, HerHairLayer and HerGearLayer: every light that lights her on her own layer takes all three.</summary>
    public const uint HerLayers = HerLayer | HerHairLayer | HerGearLayer;
    /// <summary>True: her meshes on HerLayer, not on layer 2 (GameCloseUp, the close view by night).</summary>
    public bool OwnLayer;
    bool ownShown;
    float lamp = 1;
    // Their own clips (hers, or his) and carriage.
    readonly bool mine;
    readonly OwnClips own = OwnClips.Her;
    readonly HerCarriage? carriage;
    float runSpeed;
    float sprintSpeed;
    AnimationNodeAnimation? sprintNode, walkNode;
    // Her arm-hold switch (animation 55, Play/ArmHold): a copy of the move graph whose run weight is the switched hold's
    // (0 or 1), its arm bones only laid over the move blend by a filtered Blend2; HerArmHold crossfades each switch.
    AnimationNodeAnimation? aIdle, aWalk, aRun, aSprint;
    readonly ArmHold armHold = new();
    HerArmHold? armMod;
    bool armOn;
    // What Carry asked of the fade this frame, handed to HerArmHold after the tree's next Advance (the frame it shows).
    (bool Fading, float E, Animation? Walk, Animation? Run, Animation? Sprint, double WalkT, double RunT, float Fast) armFade;
    static readonly bool ArmBlendOff = SurvivorUnchained.Args.Get("arm-blend") == "off";
    // Her gait (animation 51): the walk's and run's ground speeds and lengths, the shared stride phase (0 = left heel down), and how long she has stood.
    float walkSpeed, walkLen, runLen, stride, standT;
    bool hasWalk;
    PersonView? view;
    // Weapons sheathed in town (Play/Sheath.cs): fed each frame from the close-up's situation (Calm).
    readonly Sheath sheath = new();
    bool entered, safeNow, threatNow, actedNow;
    bool upperNative, fullNative, fullSoft;
    float heading, turnRate, aim, aimHold, lastSpeed, accel;
    // Standing and running, for her breaks and her breath.
    double stillT, runT, ranFor, breakAt = 9;
    readonly RandomNumberGenerator rng = new();

    public PlayerView(Loadout lo)
    {
        loadout = lo;
        Name = "Survivor";
        AddToGroup(Brush.HerGroup);
        var v = new PersonView(lo.Person, new World.Held { Right = lo.Arms.Right, Left = lo.Arms.Left, Forearm = lo.Arms.Forearm }, 0.8);
        person = v.Person;
        view = v;
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
            sprintNode = new AnimationNodeAnimation { Animation = own.Has(sprint) ? own.Prefix + sprint : run };
            mv.AddNode("sprint", sprintNode, new Vector2(0, 400));
            mv.AddNode("fast", new AnimationNodeBlend2 { Sync = true }, new Vector2(200, 300));
            // Her walk (if she has one for this calling and state) and her run are each seeked every frame to the shared
            // stride phase, so they stay on the same foot through the blend.
            walkNode = new AnimationNodeAnimation { Animation = run };
            mv.AddNode("walk", walkNode, new Vector2(0, 100));
            mv.AddNode("walkSeek", new AnimationNodeTimeSeek(), new Vector2(200, 100));
            mv.AddNode("runSeek", new AnimationNodeTimeSeek(), new Vector2(400, 300));
            mv.AddNode("blendW", new AnimationNodeBlend2(), new Vector2(400, 0));
            mv.AddNode("blend", new AnimationNodeBlend2(), new Vector2(600, 100));
            mv.ConnectNode("fast", 0, "run");
            mv.ConnectNode("fast", 1, "sprint");
            mv.ConnectNode("walkSeek", 0, "walk");
            mv.ConnectNode("runSeek", 0, "fast");
            mv.ConnectNode("blendW", 0, "idle");
            mv.ConnectNode("blendW", 1, "walkSeek");
            mv.ConnectNode("blend", 0, "blendW");
            mv.ConnectNode("blend", 1, "runSeek");
            // The arms' copy: the same clips, seeks and weights but the switched run weight (fed in Carry).
            aIdle = new AnimationNodeAnimation { Animation = idle };
            aWalk = new AnimationNodeAnimation { Animation = run };
            aRun = new AnimationNodeAnimation { Animation = run };
            aSprint = new AnimationNodeAnimation { Animation = sprintNode.Animation };
            mv.AddNode("aIdle", aIdle, new Vector2(0, 600));
            mv.AddNode("aWalk", aWalk, new Vector2(0, 700));
            mv.AddNode("aRun", aRun, new Vector2(0, 800));
            mv.AddNode("aSprint", aSprint, new Vector2(0, 900));
            mv.AddNode("aFast", new AnimationNodeBlend2 { Sync = true }, new Vector2(200, 850));
            mv.AddNode("aWalkSeek", new AnimationNodeTimeSeek(), new Vector2(200, 700));
            mv.AddNode("aRunSeek", new AnimationNodeTimeSeek(), new Vector2(400, 850));
            mv.AddNode("aBlendW", new AnimationNodeBlend2(), new Vector2(400, 600));
            mv.AddNode("aBlend", new AnimationNodeBlend2(), new Vector2(600, 700));
            // Filtered: the arm bones blend toward the copy by the amount, every other track keeps input 0 whole.
            var arms = new AnimationNodeBlend2 { FilterEnabled = true };
            for (int b = 0; b < person.Skeleton.GetBoneCount(); b++)
                if (ArmHold.IsArmBone(person.Skeleton.GetBoneName(b))) arms.SetFilterPath($"Armature/Skeleton3D:{person.Skeleton.GetBoneName(b)}", true);
            mv.AddNode("arms", arms, new Vector2(800, 300));
            mv.ConnectNode("aFast", 0, "aRun");
            mv.ConnectNode("aFast", 1, "aSprint");
            mv.ConnectNode("aWalkSeek", 0, "aWalk");
            mv.ConnectNode("aRunSeek", 0, "aFast");
            mv.ConnectNode("aBlendW", 0, "aIdle");
            mv.ConnectNode("aBlendW", 1, "aWalkSeek");
            mv.ConnectNode("aBlend", 0, "aBlendW");
            mv.ConnectNode("aBlend", 1, "aRunSeek");
            mv.ConnectNode("arms", 0, "blend");
            mv.ConnectNode("arms", 1, "aBlend");
            mv.ConnectNode("output", 0, "arms");
            moveNode = mv;
            GaitClips(People.Clip(person, "Jog_Fwd_Loop"));
            carriage = new HerCarriage();
            person.Skeleton.AddChild(carriage);
            person.Skeleton.MoveChild(carriage, 0);
            // First of all, on the tree's own pose (before her carriage, her pose layer and the helpers).
            armMod = new HerArmHold();
            person.Skeleton.AddChild(armMod);
            person.Skeleton.MoveChild(armMod, 0);
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
        Light = new OmniLight3D { LightColor = new Color(SurvivorUnchained.Args.Get("ember-color") ?? "#ffd0a0"), LightEnergy = LightBase / Mathf.Pi, OmniRange = 11, OmniAttenuation = 1.4f, ShadowEnabled = false, Position = new Vector3(0, 2.4f, 0.4f) };
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
    /// <summary>Her body handed to a cinematic: she stands quiet, with no idle breaks (a sword flourish
    /// read as sniffing the blade in C04 A's memory beat; play-1, 25 Oct).</summary>
    public bool Still;
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

    // The clips in the one-shots, by the name the library knows, and the grip slide (metres) and tilt (degrees) now.
    string fullClip = "", upperClip = "";
    float slide, tilt, slideL, tiltL, pocketL;

    void Upper(string clip, double speed)
    {
        upperClip = clip;
        upper.Animation = People.Clip(person, clip);
        upperNative = upper.Animation.ToString().StartsWith(own.Prefix);
        tree.Set("parameters/upperScale/scale", speed);
        tree.Set("parameters/upperShot/request", (int)AnimationNodeOneShot.OneShotRequest.Fire);
    }

    /// <summary>One of her own clips on her upper body, by its own name.</summary>
    bool UpperHer(string clip, double speed)
    {
        if (!mine || !own.Has(clip)) return false;
        upperClip = clip;
        // Standing, a stance swing takes her whole body (its own feet set and hips into the blow), soft:
        // it gives way to the run the moment she moves. Moving, it rides her upper body over the run.
        if (this.speed < 0.6f && own.Stance(clip)) return FullHer(clip, speed, true);
        upper.Animation = own.Prefix + RunVariant(clip);
        upperNative = true;
        tree.Set("parameters/upperScale/scale", speed);
        tree.Set("parameters/upperShot/request", (int)AnimationNodeOneShot.OneShotRequest.Fire);
        return true;
    }

    /// <summary>A stance swing re-aimed for her run's hips, where one is keyed (clip + "_run", e.g. axe_fore_run):
    /// moving, her hips are the run's, not turned into the blow, so the stance clip's arms land elsewhere.</summary>
    string RunVariant(string clip) => own.Stance(clip) && own.Has(clip + "_run") ? clip + "_run" : clip;

    void Full(string clip, double speed)
    {
        fullClip = clip;
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
        fullClip = clip;
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

    /// <summary>Whether she carries her pieces sheathed now.</summary>
    public bool Sheathed => sheath.Sheathed;

    /// <summary>Where she stands this frame (Game.UpdateCloseUp): a safe place, or anything hostile near. The
    /// first call is the place just entered: sheathed at once where it is safe. Only a calling with a town idle
    /// (idle_&lt;calling&gt;_&lt;kind&gt;_town or idle_&lt;calling&gt;_town) sheathes; the rest stay armed.</summary>
    public void Calm(bool safe, bool threat)
    {
        safeNow = safe && mine && Sheath.HasTown(person.Calling, person.Kind, own.Has);
        threatNow = threat;
        if (entered) return;
        entered = true;
        sheath.Enter(safeNow);
        if (sheath.Sheathed) Mount(true);
    }

    /// <summary>Her pieces at the sockets or in her hands, and her stand and run to match.</summary>
    void Mount(bool sheathed)
    {
        view?.Sheathe(sheathed);
        if (armMod != null) armMod.AxisR = armMod.AxisL = Vector3.Zero;   // (the pieces remounted: their axes read again)
        if (!mine || idleNode == null || runNode == null) return;
        idleNode.Animation = People.Clip(person, loadout.Arms.Idle, sheathed);
        var run = People.Clip(person, "Jog_Fwd_Loop", sheathed);
        runNode.Animation = run;
        runSpeed = run.StartsWith(own.Prefix) ? own.Speed(run[own.Prefix.Length..]) * person.Root.Scale.X : 5.3f;
        GaitClips(run, sheathed);
        if (sprintNode == null) return;
        // The sprint follows: her town sprint if she has one, else the town run itself; the armed sprint on the draw.
        var sprint = run.StartsWith(own.Prefix + "run_") ? "sprint" + run[(own.Prefix.Length + 3)..] : "";
        if (own.Has(sprint)) { sprintNode.Animation = own.Prefix + sprint; sprintSpeed = own.Speed(sprint) * person.Root.Scale.X; }
        else { sprintNode.Animation = run; sprintSpeed = runSpeed; }
        ArmClips();
    }

    /// <summary>The arms' copy of the move graph plays the same clips.</summary>
    void ArmClips()
    {
        if (aIdle == null || aWalk == null || aRun == null || aSprint == null || idleNode == null || runNode == null || walkNode == null || sprintNode == null) return;
        aIdle.Animation = idleNode.Animation;
        aWalk.Animation = walkNode.Animation;
        aRun.Animation = runNode.Animation;
        aSprint.Animation = sprintNode.Animation;
    }

    /// <summary>Her walk for this calling and state (or the run's own clip standing in when there is none), and the lengths the stride seeks by.</summary>
    void GaitClips(string run, bool sheathed = false)
    {
        if (walkNode == null || person.Anim == null) return;
        var w = own.Walk(person.Calling, person.Kind, sheathed);
        hasWalk = w != null && person.Anim.HasAnimation(w);
        walkNode.Animation = hasWalk ? w! : run;
        walkSpeed = hasWalk ? own.Speed(w![own.Prefix.Length..]) * person.Root.Scale.X : 0;
        if (walkSpeed <= 0.05f) hasWalk = false;
        walkLen = person.Anim.HasAnimation(walkNode.Animation) ? (float)person.Anim.GetAnimation(walkNode.Animation).Length : 1;
        runLen = person.Anim.HasAnimation(run) ? (float)person.Anim.GetAnimation(run).Length : 1;
        ArmClips();
    }

    /// <summary>An art used: the hands that go with it.</summary>
    public void OnAbility(string id)
    {
        actedNow = true;
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
        actedNow = true;
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
        // Up from where the fall left her: off her back if she went over
        // onto it (get_up starts face down: from her back it popped).
        Full(onBack && mine && own.Has("get_up_back") ? own.Prefix + "get_up_back" : "Lie_StandUp", 1.2);
        onBack = false;
    }
    bool onBack;

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
        // The arm-hold crossfade, on the frame the tree first shows what Carry set last frame.
        if (armMod != null)
        {
            armMod.Fading = armFade.Fading;
            armMod.E = armFade.E;
            armMod.Walk = armFade.Walk; armMod.Run = armFade.Run; armMod.Sprint = armFade.Sprint;
            armMod.WalkT = armFade.WalkT; armMod.RunT = armFade.RunT; armMod.Fast = armFade.Fast;
        }
        var p = b.Player;
        double y = heightAt(x, z);
        if (leap >= 0) y += Mathf.Sin((float)(leap * Mathf.Pi)) * 2.2;
        Position = new Vector3((float)x, (float)y, (float)z);
        Reflections.Update(b, dt, heightAt);
        Ghostly(p.Alive && b.Art.WraithT > 0);
        // --hold CLIP@S: one of her clips held at S seconds, her pieces drawn, under the game's own light and
        // cameras (a judge's 1:1 frame of one pose; for pictures only). A town clip (*_town) is held with her pieces
        // sheathed, as the game plays it.
        if (mine && Hold is { Length: 2 } hold)
        {
            tree.Active = false;
            if (!held) { held = true; view?.Sheathe(hold[0].EndsWith("_town") || SurvivorUnchained.Args.Has("sheathed")); } // (--sheathed: her pieces at their sockets, as in a safe place)
            slide = own.GripSlide(hold[0]); // the clip's grip, straight (no easing)
            tilt = own.GripTilt(hold[0]);
            view?.Slide("handslot.r", slide, tilt);
            slideL = own.GripSlideL(hold[0]);
            tiltL = own.GripTiltL(hold[0]);
            pocketL = tiltL != 0 ? 1 : 0;
            view?.Slide("handslot.l", slideL, tiltL, pocketL); // (a left tilt seats the piece on its pocket: TiltPocketL)
            // An upper-body clip (a swing) is held as play shows it: over her idle's hips and legs (the
            // upperShot filter), not on the clip's own keyed legs. --hold-full shows the clip's legs.
            var sk = person.Skeleton;
            // --hold-base CLIP@S: the hips and legs from that clip instead (a swing over her run, as play shows it moving).
            var hb = SurvivorUnchained.Args.Get("hold-base")?.Split('@');
            bool stance = own.Stance(hold[0]) && hb == null;
            bool upperOnly = idleNode != null && !SurvivorUnchained.Args.Has("hold-full") && own.UpperLayer(hold[0]) && !stance;
            var legs = new List<(int b, Vector3 p, Quaternion r)>();
            if (upperOnly)
            {
                person.Anim.Play(hb is { Length: 2 } ? own.Prefix + hb[0] : idleNode!.Animation);
                person.Anim.Seek(hb is { Length: 2 } ? double.Parse(hb[1], System.Globalization.CultureInfo.InvariantCulture) : 0, true);
                for (int bi = 0; bi < sk.GetBoneCount(); bi++)
                {
                    var name = sk.GetBoneName(bi);
                    if (name is "root" or "pelvis" || name.StartsWith("thigh") || name.StartsWith("calf") || name.StartsWith("foot") || name.StartsWith("ball") || name.StartsWith("glute"))
                        legs.Add((bi, sk.GetBonePosePosition(bi), sk.GetBonePoseRotation(bi)));
                }
            }
            // (over a run, a stance swing's run variant, as UpperHer plays it moving)
            person.Anim.Play(own.Prefix + (hb is { Length: 2 } && upperOnly ? RunVariant(hold[0]) : hold[0]));
            person.Anim.Seek(double.Parse(hold[1], System.Globalization.CultureInfo.InvariantCulture), true);
            person.Anim.Pause();
            foreach (var (bi, p0, r0) in legs) { sk.SetBonePosePosition(bi, p0); sk.SetBonePoseRotation(bi, r0); }
            // Her head carried up as play carries it (HeadLevel) through a swing and her idles and runs; a
            // whole-body clip (a fall, a roll, a flourish) keeps its own head, as play leaves it.
            string hn = hold[0];
            bool moveClip = hn.StartsWith("idle_") || hn.StartsWith("run_") || hn.StartsWith("sprint_") || hn.StartsWith("stop_") || hn.StartsWith("walk_");
            if (carriage != null) carriage.HeadLevel = upperOnly || moveClip || stance ? HeadLevel : 0;
            if (person.Pose != null) person.Pose.Native = 1;
            // (--close-turn R with it: turned from the close view's lens as its idle turns her, so a held pose can be
            // seen from her front; without it she keeps her heading, as before.)
            if (HoldTurn && Turned is float th) Rotation = new Vector3(0, th, 0);
            return;
        }
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
                onBack = death.EndsWith("death_back");
                person.Anim.Play(death, 0.1);
                if (person.Pose != null) person.Pose.Native = death.StartsWith(own.Prefix) ? 1 : 0;
                if (carriage != null) carriage.Aim = carriage.Bank = carriage.Tilt = carriage.HeadLevel = 0;
            }
            Light.LightEnergy = Mathf.Lerp(Light.LightEnergy, 0.6f / Mathf.Pi, 1 - Mathf.Exp(-2 * (float)dt));
            return;
        }
        float sp = (float)Mathf.Sqrt(p.Vx * p.Vx + p.Vz * p.Vz);
        // Sheathed in a quiet town, drawn at once for a threat, a blow, a skill or a cast.
        if (entered)
        {
            bool acting = actedNow || (p.AttackAnim is { } swung && swung.T != lastAttack);
            actedNow = false;
            if (sheath.Update(dt, safeNow, threatNow, acting)) Mount(sheath.Sheathed);
        }
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
            // chain_strike is gated off (judge r4, 20 Oct: its crouch hold reads as leaning
            // on a hoe; a later round restages it), so she lands with her heavy blow.
            else if (was == Content.AbilityKind.Grapple && UpperHer(HerClips.Heavy(person.Kind), 1.5))
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
        lamp = Mathf.Lerp(lamp, LampScale, 1 - Mathf.Exp(-3 * (float)dt));
        Light.LightEnergy = (float)((LightBase * (0.7 + 0.3 * hp) + flicker + flare * 20) / Mathf.Pi) * lamp * Atmosphere.EmberGain;
        // A lantern carries further; under the Oath of the Moonless, not far at all.
        Light.OmniRange = (float)((11 + flare * 6) * b.Stats.Get(Stat.LightRadius) * b.Rules.Light) * EmberRangeK;
        Light.OmniAttenuation = EmberAtt;
        Light.LightCullMask = LampOffHer ? 0xFFFFFu & ~2u & ~HerLayers & ~Brush.MaskLayer : 0xFFFFFu;
        // (Every frame while on: her level of detail and her wear make meshes of their own on layer 2.)
        if (OwnLayer || ownShown) { Relayer(this, OwnLayer, person.Hair); ownShown = OwnLayer; }
        Light.Position = new Vector3(0, 2.4f, 0.4f);
        // Unseen: a ghost, flickering.
        Visible = !Hidden && !(p.InvisibleT > 0 && (int)(time * 12) % 3 == 0);
    }

    /// <summary>True when any of a mesh's surfaces is metal: her outfit's metal keys (People.OutfitMaterials, meta "kind" 1,
    /// heroine_outfit_metal.gdshader), or a plain material at metallic 0.5 or more. Only these take the moon rim's gear twin:
    /// with all her gear on it her leather (bandeau, bracers, belt) read as lavender chrome by night (judge J2, face 36).</summary>
    static bool IsMetal(GeometryInstance3D g)
    {
        if (g is not MeshInstance3D m || m.Mesh == null) return false;
        for (int s = 0; s < m.Mesh.GetSurfaceCount(); s++)
            switch (m.GetActiveMaterial(s))
            {
                case ShaderMaterial sm when sm.HasMeta("kind") && (int)sm.GetMeta("kind") == 1 || sm.Shader?.ResourcePath.Contains("metal") == true: return true;
                case BaseMaterial3D bm when bm.Metallic >= 0.5f: return true;
            }
        return false;
    }

    static void Relayer(Node n, bool own, List<MeshInstance3D> hair)
    {
        foreach (var c in n.GetChildren())
        {
            if (c is GeometryInstance3D g)
            {
                uint mine = !RimHair && g is MeshInstance3D mi && hair.Contains(mi) ? HerHairLayer
                    : GearOwn && own && (g.Layers & 2u) != 0 && IsMetal(g) ? HerGearLayer : HerLayer;
                // (her weapon is the world's (layer 1), not people's: it keeps that and takes her gear's layer too, so her own
                // lamps (the night key, the moon rim's gear twin) reach it; without them it was flat black by night, judge J1)
                if (GearOwn && (g.Layers & 1u) != 0 && (g.Layers & 2u) == 0)
                    g.Layers = own ? g.Layers | HerGearLayer : g.Layers & ~HerGearLayer;
                else if (own && (g.Layers & 2u) != 0) g.Layers = (g.Layers & ~2u) | mine;
                else if (!own && (g.Layers & HerLayers) != 0) g.Layers = (g.Layers & ~HerLayers) | 2u;
            }
            Relayer(c, own, hair);
        }
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
            float phase = stride;
            var stop = Sheath.Pick(sheath.Sheathed, $"stop_{person.Calling}", phase >= 0.25f && phase < 0.75f ? "_r" : "_l", own.Has);
            if (stop != null) FullHer(stop, 1, true);
        }
        runT = 0;
        stillT += dt;
        // (A breath is caught on stopping, or not at all.)
        if (stillT > 1.0) ranFor = 0;
        bool calm = b.NearestHostile(p.X, p.Z, 14) == null && (!Busy || fullSoft);
        if (!calm || Still || Hidden) { breakAt = Mathf.Max((float)breakAt, (float)stillT + 4); return; }
        // (Only with her hands empty, every piece at its socket: FreeHand.)
        if (ranFor > 6 && stillT > 0.75 && FreeHand.Both(loadout.Arms, sheath.Sheathed, id => WeaponSockets.SocketOf(Arms.KindOf(id)) != null))
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
            var brk = Sheath.Pick(sheath.Sheathed, $"idle_{person.Calling}", "_break", own.Has);
            if (brk != null) FullHer(brk, 1, true);
        }
    }

    /// <summary>Her run and stand, her lean and her aim, this frame.</summary>
    void Carry(float dt, float sp)
    {
        // Standing to running over the first two metres a second; the run
        // at the rate her ground speed asks.
        float natural0 = Mathf.Lerp(runSpeed, sprintSpeed, sprintSpeed > runSpeed ? Mathf.SmoothStep(runSpeed * 1.1f, sprintSpeed * 0.95f, speed) : 0);
        var (wWalk, w) = Stride.Weights(speed, walkSpeed, natural0, hasWalk);
        tree.Set("parameters/move/blendW/blend_amount", wWalk);
        tree.Set("parameters/move/blend/blend_amount", w);
        // Into the sprint as she goes past her run's own speed; the pair
        // played at the rate the blend of their speeds asks.
        float fast = sprintSpeed > runSpeed ? Mathf.SmoothStep(runSpeed * 1.1f, sprintSpeed * 0.95f, speed) : 0;
        tree.Set("parameters/move/fast/blend_amount", fast);
        float natural = Mathf.Lerp(runSpeed, sprintSpeed, fast);
        // One stride phase for both gaits; a walk starts on the left heel after she has stood a moment.
        standT = speed < 0.05f ? standT + dt : 0;
        if (standT > 0.4f) stride = 0;
        float period = Stride.Period(speed, walkLen, walkSpeed, runLen, Stride.RunScale(speed, natural), w, hasWalk);
        stride = Stride.Advance(stride, dt, period);
        tree.Set("parameters/move/walkSeek/seek_request", stride * walkLen);
        tree.Set("parameters/move/runSeek/seek_request", stride * runLen);
        // Her arms in one hold or the other (Play/ArmHold): only where the walk and the run carry a piece in hand
        // (her walk for this calling and kind, armed, not sheathed); elsewhere today's per-bone mix. --arm-blend off: the mix.
        bool armNow = !ArmBlendOff && armMod != null && hasWalk && !sheath.Sheathed && (!string.IsNullOrEmpty(loadout.Arms.Right) || loadout.Arms.Left != null);
        if (armNow && !armOn) armHold.Reset(w);
        if (armNow) armHold.Step(w, dt);
        armOn = armNow;
        // Mid-fade (and nothing laid over her arms: a blow, a roll), HerArmHold lays her arms between the two holds.
        bool fadeNow = armNow && armHold.Fading && !(bool)tree.Get("parameters/fullShot/active") && !(bool)tree.Get("parameters/upperShot/active");
        if (fadeNow && armMod != null)
        {
            if (armMod.AxisR == Vector3.Zero && armMod.AxisL == Vector3.Zero && view != null) { armMod.AxisR = view.PieceAxis("handslot.r"); armMod.AxisL = view.PieceAxis("handslot.l"); }
            Animation? A(string? n) => n != null && tree.HasAnimation(n) ? tree.GetAnimation(n) : null;
            armFade = (true, armHold.E, A(walkNode?.Animation), A(runNode?.Animation), A(sprintNode?.Animation), stride * walkLen, stride * runLen, fast);
        }
        else armFade = default;
        tree.Set("parameters/move/arms/blend_amount", armNow ? 1f : 0f);
        if (armNow)
        {
            tree.Set("parameters/move/aBlendW/blend_amount", wWalk);
            tree.Set("parameters/move/aFast/blend_amount", fast);
            tree.Set("parameters/move/aBlend/blend_amount", armHold.Run ? 1f : 0f);
            tree.Set("parameters/move/aWalkSeek/seek_request", stride * walkLen);
            tree.Set("parameters/move/aRunSeek/seek_request", stride * runLen);
        }
        // Her corrective layer stands down for whichever half plays hers.
        bool fullOn = (bool)tree.Get("parameters/fullShot/active"), upperOn = (bool)tree.Get("parameters/upperShot/active");
        // The staff slid (animation 47) and tilted (animation 48) in her fist by whichever clip plays, eased between them.
        if (idleNode != null && runNode != null)
        {
            float to = GripSlide.Target(fullOn, own.GripSlide(fullClip), upperOn, own.GripSlide(upperClip), wWalk, w,
                own.GripSlide(idleNode.Animation), own.GripSlide((walkNode ?? idleNode).Animation), own.GripSlide(runNode.Animation));
            float toT = GripSlide.Target(fullOn, own.GripTilt(fullClip), upperOn, own.GripTilt(upperClip), wWalk, w,
                own.GripTilt(idleNode.Animation), own.GripTilt((walkNode ?? idleNode).Animation), own.GripTilt(runNode.Animation));
            slide = GripSlide.Ease(slide, to, dt);
            tilt = GripSlide.Ease(tilt, toT, dt);
            view?.Slide("handslot.r", slide, tilt);
            float toL = GripSlide.Target(fullOn, own.GripSlideL(fullClip), upperOn, own.GripSlideL(upperClip), wWalk, w,
                own.GripSlideL(idleNode.Animation), own.GripSlideL((walkNode ?? idleNode).Animation), own.GripSlideL(runNode.Animation));
            slideL = GripSlide.Ease(slideL, toL, dt);
            // The left tilt (animation 58), and the weight that eases a piece without a fitted left pocket onto the tilt's.
            float toTL = GripSlide.Target(fullOn, own.GripTiltL(fullClip), upperOn, own.GripTiltL(upperClip), wWalk, w,
                own.GripTiltL(idleNode.Animation), own.GripTiltL((walkNode ?? idleNode).Animation), own.GripTiltL(runNode.Animation));
            static float On(float t) => t != 0 ? 1 : 0;
            float toPL = GripSlide.Target(fullOn, On(own.GripTiltL(fullClip)), upperOn, On(own.GripTiltL(upperClip)), wWalk, w,
                On(own.GripTiltL(idleNode.Animation)), On(own.GripTiltL((walkNode ?? idleNode).Animation)), On(own.GripTiltL(runNode.Animation)));
            tiltL = GripSlide.Ease(tiltL, toTL, dt);
            pocketL = GripSlide.Ease(pocketL, toPL, dt);
            view?.Slide("handslot.l", slideL, tiltL, pocketL);
        }
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
        // Her head carried up, her eyes on the way ahead (HerCarriage.HeadLevel);
        // left to the clip through a whole-body one (a roll, a leap, a vault, a
        // rush, a get-up), whose tucked head lifted would look wrong, and back after.
        bool tucked = fullOn && !fullSoft;
        carriage.HeadLevel = Mathf.Lerp(carriage.HeadLevel, tucked ? 0 : HeadLevel, 1 - Mathf.Exp((tucked ? -12 : -4) * dt));
    }

    /// <summary>How much of her clips' bowed head is taken back toward level in play (--head-level tries
    /// another): from play's camera her face then shows eyes and a mouth, not the crown of her hair.</summary>
    // --ember-att A, --ember-range K, --ember-color C: her carried light's falloff, reach and colour (E1 pictures). Round 3c:
    // pale gold (#ffb070 was) and a steeper falloff, so the moon's shadows inside her pool stay dark, not rust streaks.
    static readonly float EmberAtt = SurvivorUnchained.Args.Num("ember-att", 1.8f), EmberRangeK = SurvivorUnchained.Args.Num("ember-range", 1f);
    static readonly string[]? Hold = SurvivorUnchained.Args.Get("hold")?.Split('@');
    static readonly bool HoldTurn = SurvivorUnchained.Args.Has("close-turn");
    bool held;
    static readonly float HeadLevel = SurvivorUnchained.Args.Has("head-level") ? SurvivorUnchained.Args.Num("head-level", 0.8f) : 0.8f;
}

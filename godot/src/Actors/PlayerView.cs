using System.Linq;
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
    // (the AnimationTree paths, each made once: a StringName from a string per frame is a Godot disposable that outlives its young GC)
    static readonly StringName P_upperScale_scale = "parameters/upperScale/scale";
    static readonly StringName P_upperShot_request = "parameters/upperShot/request";
    static readonly StringName P_fullScale_scale = "parameters/fullScale/scale";
    static readonly StringName P_fullShot_request = "parameters/fullShot/request";
    static readonly StringName P_fullShot_active = "parameters/fullShot/active";
    static readonly StringName P_fullOldScale_scale = "parameters/fullOldScale/scale";
    static readonly StringName P_fullOldSeek_seek_request = "parameters/fullOldSeek/seek_request";
    static readonly StringName P_fullX_blend_amount = "parameters/fullX/blend_amount";
    static readonly StringName P_upperShot_active = "parameters/upperShot/active";
    static readonly StringName P_move_backBlend_blend_amount = "parameters/move/backBlend/blend_amount";
    static readonly StringName P_move_backScale_scale = "parameters/move/backScale/scale";
    static readonly StringName P_move_blendW_blend_amount = "parameters/move/blendW/blend_amount";
    static readonly StringName P_move_blend_blend_amount = "parameters/move/blend/blend_amount";
    static readonly StringName P_move_fast_blend_amount = "parameters/move/fast/blend_amount";
    static readonly StringName P_move_walkSeek_seek_request = "parameters/move/walkSeek/seek_request";
    static readonly StringName P_move_runSeek_seek_request = "parameters/move/runSeek/seek_request";
    static readonly StringName P_move_idleSeek_seek_request = "parameters/move/idleSeek/seek_request";
    static readonly StringName P_move_aIdleSeek_seek_request = "parameters/move/aIdleSeek/seek_request";
    static readonly StringName P_move_arms_blend_amount = "parameters/move/arms/blend_amount";
    static readonly StringName P_move_aBlendW_blend_amount = "parameters/move/aBlendW/blend_amount";
    static readonly StringName P_move_aFast_blend_amount = "parameters/move/aFast/blend_amount";
    static readonly StringName P_move_aBlend_blend_amount = "parameters/move/aBlend/blend_amount";
    static readonly StringName P_move_aWalkSeek_seek_request = "parameters/move/aWalkSeek/seek_request";
    static readonly StringName P_move_aRunSeek_seek_request = "parameters/move/aRunSeek/seek_request";
    static readonly StringName P_upper_current_position = "parameters/upper/current_position";
    static readonly StringName P_full_current_position = "parameters/full/current_position"; // (lane K, 20 Nov: made once for CoilStep)
    static readonly StringName P_move_dFA_blend_amount = "parameters/move/dFA/blend_amount";
    static readonly StringName P_move_dFB_blend_amount = "parameters/move/dFB/blend_amount";
    static readonly StringName P_move_dBA_blend_amount = "parameters/move/dBA/blend_amount";
    static readonly StringName P_move_dBB_blend_amount = "parameters/move/dBB/blend_amount";
    static readonly StringName P_move_dirSet_blend_amount = "parameters/move/dirSet/blend_amount";
    static readonly StringName P_move_dir_blend_amount = "parameters/move/dir/blend_amount";
    readonly AnimationNodeAnimation upper, full;
    // The upper node's clip, fetched once per set of its Animation (the getter and GetAnimation each make a Godot object)
    Animation? upperAnim;
    Animation? UpperAnim() => upperAnim ??= person.Anim.GetAnimation(upper.Animation);
    /// <summary>The whole-body clip she was in, held on at its place for a crossfade out of it (FullHerFrom).</summary>
    readonly AnimationNodeAnimation fullOld;
    readonly AnimationNodeOneShot fullShotNode, upperShotNode;
    readonly AnimationNodeAnimation? idleNode, runNode;
    // The clip names the four nodes play, as strings (SyncAn, at every place a node's Animation is set): the getter makes a
    // StringName each call, and a string passed on as a StringName makes one more.
    string? idleAn, runAn, sprintAn, walkAn;
    StringName? idleSn;
    Animation? idleAnimRes;
    void SyncAn()
    {
        idleAn = idleNode?.Animation.ToString(); runAn = runNode?.Animation.ToString();
        sprintAn = sprintNode?.Animation.ToString(); walkAn = walkNode?.Animation.ToString();
        idleSn = idleAn == null ? null : new StringName(idleAn); idleAnimRes = null;
    }
    public readonly OmniLight3D Light;
    /// <summary>Her carried light on people (Rendering 2, judge r1 D1): <see cref="Light"/> lights the ground round her and
    /// not people, and this one, higher and softer, lights her and the folk near her. From a hand over her head the pool's
    /// light was twelve times the ground's on her crown and shoulders and clipped her copper hair cream-white; from higher up
    /// she takes about a third of it and the dead and the foes in her pool about what the pool gave them.</summary>
    public readonly OmniLight3D FolkLight;
    /// <summary>(lane E lead 3, row 1, 16 Nov: "she nearly vanishes under the roots ... needs a rim or fill from her carried
    /// light") Her rim light in the den: her carried light's edge on her alone (HerLayers; her meshes take HerLayer beside
    /// people's while it is on, RimStep), no shadow, low behind her on the side away from the camera, so her far planes and
    /// her silhouette's upper edge catch it; its energy grows as the den's own light at her feet falls (DenLightAt), none in
    /// the open. Hers only (null on other views); off without the den rig's values 47-56 (HeroDen.RimEnergy).</summary>
    public readonly OmniLight3D? RimLight;
    /// <summary>The survivor in glass: reflections and echoes left behind.</summary>
    public readonly Reflections Reflections;
    readonly List<GeometryInstance3D> skin = new();
    readonly ShaderMaterial wraith = new() { Shader = GD.Load<Shader>("res://shaders/ghost.gdshader") };
    /// <summary>Her silhouette through what hides her from the play camera (shaders/her_xray.gdshader, H1 round 2C): an
    /// overlay on her solid meshes (no cards, fur, eyes or teeth: an overlay ignores their cut-outs), on only in play
    /// with the camera far (HerLod.InPlay), eased in and out.</summary>
    /// (lane E lead 3, 16 Nov: the outline broke behind a slab she stood against) Three passes: her_xray_mask first
    /// (priority -1: stencil 7 wherever her own surface is what the camera sees), then the fill, then the outline, which
    /// both skip stencil 7, so her own body never counts as what hides her and no capsule round her feet is needed.
    readonly ShaderMaterial xray = new() { Shader = GD.Load<Shader>("res://shaders/her_xray_mask.gdshader"), RenderPriority = -1,
        NextPass = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/her_xray.gdshader"),
            NextPass = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/her_xray_rim.gdshader"), RenderPriority = 1 } } };
    void XraySet(string k, Variant v)
    {
        var fill = (ShaderMaterial)xray.NextPass;
        fill.SetShaderParameter(Sn.Of(k), v);
        ((ShaderMaterial)fill.NextPass).SetShaderParameter(Sn.Of(k), v);
    }
    readonly List<GeometryInstance3D> xrayOn = new();
    float xrayK = -1;
    static readonly float XrayStrength = SurvivorUnchained.Args.Num("xray", 0.6f);
    /// <summary>--xray-old: the x-ray as demo-rc2 had it (her own body hides her too), for the before strip.</summary>
    static readonly bool XrayOld = SurvivorUnchained.Args.Has("xray-old");
    /// <summary>--xray-twins: the x-ray rides FxAfter's depth twins (the after-grade layer) and her den shadow's quad too, as before lane E s3.</summary>
    static readonly bool XrayTwins = SurvivorUnchained.Args.Has("xray-twins");
    static bool XraySolid(GeometryInstance3D g)
    {
        if (g is not MeshInstance3D mi || mi.Mesh == null) return false;
        for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
        {
            var m = mi.GetActiveMaterial(s);
            if (m is BaseMaterial3D bm ? bm.Transparency != BaseMaterial3D.TransparencyEnum.Disabled
                : m is ShaderMaterial sm ? sm.Shader?.ResourcePath is not string sp || sp.Contains("card") || sp.Contains("fur") || sp.Contains("eye") || sp.Contains("teeth") || sp.Contains("sheer") || sp.Contains("hair")
                : true) return false;
        }
        return true;
    }
    /// <summary>The crowd's floor while a boss is up (vat.gdshaderinc crowd_floor): looked for twice a second, eased over a second.</summary>
    void FloorStep(Battle b, float dt)
    {
        if ((floorLookT -= dt) <= 0)
        {
            floorLookT = 0.5f;
            floorBoss = false;
            foreach (var e in b.Enemies.Living()) if (e.Boss) { floorBoss = true; break; }
        }
        float k = Mathf.MoveToward(floorK, floorBoss && Atmosphere.CrowdFill > 0 ? 1 : 0, dt);
        if (k == floorK && floorSent) return;
        floorK = k; floorSent = true;
        var c = FloorHue.SrgbToLinear();
        RenderingServer.GlobalShaderParameterSet(Sn.Of("crowd_floor"), new Vector4(c.R, c.G, c.B, k * FloorStrength));
        RenderingServer.GlobalShaderParameterSet(Sn.Of("lip_calm"), k);
    }
    float floorLookT, floorK;
    bool floorBoss, floorSent;
    static readonly Color FloorHue = new(SurvivorUnchained.Args.Get("floor-hue") ?? "#ff5a2a");
    static readonly float FloorStrength = SurvivorUnchained.Args.Num("floor", 1.2f);
    void XrayStep(float dt)
    {
        var cam = GetViewport()?.GetCamera3D();
        float want = HerLod.InPlay && !Hidden && !Still && !LampOffHer && !OwnLayer && Visible && cam != null && cam.GlobalPosition.DistanceTo(GlobalPosition) > 14 ? XrayStrength : 0;
        float k = xrayK < 0 ? want : Mathf.MoveToward(xrayK, want, dt * 2.5f);
        if (XrayLog && (xrayLogT -= dt) <= 0) { xrayLogT = 1; XrayDump(); }
        // (H8, N36: where she stands, so the x-ray never takes her own body for what hides her)
        if ((k > 0 || want > 0) && !XrayOld) XraySet("her_at", GlobalPosition);
        if (k == xrayK) return;
        // (lane E s3, 17 Nov: the movement judge's pale squiggle on her shield) never on FxAfter's depth twins (FxAfterHole, layer
        // 20, the after-grade camera's): there the x-ray drew a second time, over the graded frame, with no mask on the twins
        // made after Gather (her shield's, her sword's), so her body's outline showed through her own shield. Nor on her den
        // shadow's ground quad (HerShadow, 6.4 m square: the overlay ignores its cut, so scenery standing in the square took a
        // faint fill and the square's straight edge an outline). --xray-twins: both as before.
        if (xrayK < 0) foreach (var g in skin) if (IsInstanceValid(g) && XraySolid(g) && (XrayTwins || (g.Layers & SurvivorUnchained.View.FxAfter.RenderLayer) == 0 && g is not HerShadow)) xrayOn.Add(g);
        bool was = xrayK > 0;
        xrayK = k;
        XraySet("strength", k);
        if (was != k > 0 && !ghostly) foreach (var g in xrayOn) if (IsInstanceValid(g)) g.MaterialOverlay = k > 0 ? xray : null;
    }
    /// <summary>--xray-log: once a second, every mesh under her: shown, in skin, solid, its overlay (the x-ray's own-body mask audit).</summary>
    static readonly bool XrayLog = SurvivorUnchained.Args.Has("xray-log");
    float xrayLogT;
    void XrayDump()
    {
        var all = new List<GeometryInstance3D>();
        void Walk(Node n) { if (n is GeometryInstance3D g) all.Add(g); foreach (var c in n.GetChildren()) Walk(c); }
        Walk(this);
        GD.Print($"xray-log k {xrayK:0.00} skin {skin.Count} on {xrayOn.Count} all {all.Count}");
        foreach (var g in all)
        {
            if (!g.IsVisibleInTree() || (g.Layers & 524288u) != 0) continue;
            string Chain(Material? m) { var o = ""; for (int i = 0; m != null && i < 8; i++, m = m.NextPass) o += $"{(m is ShaderMaterial sm ? System.IO.Path.GetFileNameWithoutExtension(sm.Shader?.ResourcePath ?? "?") : m.GetType().Name)}/{m.RenderPriority}>"; return o; }
            string mats = "";
            if (g is MeshInstance3D mi && mi.Mesh != null)
                for (int s2 = 0; s2 < mi.Mesh.GetSurfaceCount(); s2++)
                {
                    var m = mi.GetActiveMaterial(s2);
                    mats += $"[{Chain(m)}{(m is BaseMaterial3D bm ? $" tr {bm.Transparency} cull {bm.CullMode} dd {bm.DepthDrawMode}" : "")}]";
                }
            GD.Print($"xray-log  {g.Name} skin {skin.Contains(g)} on {xrayOn.Contains(g)} layers {g.Layers} ovl {Chain(g.MaterialOverlay)} ovr {Chain(g.MaterialOverride)} mats {mats}");
        }
    }
    bool ghostly;
    Content.AbilityKind? rushSeen;
    double lastAttack = -1, hurtSeen, flare, castT, time, lastMuzzle = -1;
    int swing;
    bool dashing, dead;
    SurvivorUnchained.Sim.Leap? leapSeen;   // the leap whose clip started (SU-068)
    float speed;
    const float LightBase = 5;
    /// <summary>How much of her carried light lights her (1: all): the book open by day dims it
    /// (GameMenus), eased. Under the sun as well, from a hand's breadth over her head it lit her
    /// face flat and cream-white, washed out beside the panel.</summary>
    public float LampScale = 1;
    /// <summary>True: her carried light lights the ground round her but not her (the close view by night, where
    /// from over her head it filled her face flat; E1 round 3).</summary>
    public bool LampOffHer;
    /// <summary>The folk light's share (1: as built). Rendering 3 (judge j2 D4/D5): GameCloseUp ducks it inside a town lamp's
    /// reach by night (her ember stacked on the lantern ran her body near-white) and takes it off in the close view by night.</summary>
    public float FolkScale = 1;
    /// <summary>The pool light's share (1: as built): ducked with the folk light inside a town lamp's reach by night (the
    /// lantern's wall and ground blown under both, judge j2 D4).</summary>
    public float PoolScale = 1;
    /// <summary>The Flare's recovery (H7, FlareFx.Blow): her ember's pool x this after the main blow.</summary>
    public float FlarePool = 1;
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
    /// <summary>The bosses' and cinematic actors' render layer (15): off people's layer (2) so her FolkLight (2 | HerLayers) does not wash them; every other light that lit layer 2 takes this too.</summary>
    public const uint CastLayer = 1u << 14;
    /// <summary>The fighting crowd's own layer (17), worn with the people's (2): her ember's pool lights the crowd as it
    /// lights the ground round her (Rendering 4: the pool was off layer 2, so by night the bodies in it stayed near-black on a
    /// lit floor and the ring of them pointing at her read as a black starburst of shadows), but not the town's folk.</summary>
    public const uint CrowdLayer = 1u << 16;
    /// <summary>--ember-crowd off: the crowd out of her pool again, as before Rendering 4.</summary>
    static readonly bool EmberCrowd = SurvivorUnchained.Args.Get("ember-crowd") != "off";
    /// <summary>--crowd-omni on|off (Rendering 5): her real lamp light on the crowd layer. Default: it skips the crowd by night when the
    /// crowd's own light is on (the shader's lamp curve is then the whole of her light on it: 0 at 7 m, the crowd round her held under her;
    /// the real light added about a third within 1.5 m and nothing past 3 m), and lights it as before by day or with --crowd-fill off.</summary>
    static readonly string CrowdOmniArg = SurvivorUnchained.Args.Get("crowd-omni") ?? "";
    static bool CrowdOmni => CrowdOmniArg == "on" || (CrowdOmniArg != "off" && !(Atmosphere.CrowdFill > 0 && Atmosphere.CrowdCurveNew) && !Atmosphere.CrowdDen);   // (demo-look item 4: the den's pack takes her as a rim, not a flood)
    /// <summary>--pool-log: her light's reach and energy printed as they change (L1 S2b-N2, the pool in metres).</summary>
    static readonly bool PoolLog = SurvivorUnchained.Args.Has("pool-log");
    float poolLogged = -1;
    /// <summary>--crowd-ember K, --crowd-ember-h H: her lamp's strength on the crowd by night (times the pool light's) and its point over her feet.</summary>
    // (L1 lead 8, S2b-N2: 0.43 to 0.24, as her pool's light went 4.5 to 8.0 under the night rigs (W2): the crowd in her pool
    // lit 1.78 times what it was tuned under, tan wolves on 09.)
    static readonly float CrowdEmberK = SurvivorUnchained.Args.Num("crowd-ember", 0.24f), CrowdEmberH = SurvivorUnchained.Args.Num("crowd-ember-h", 2.4f),
        CrowdEmberIn = SurvivorUnchained.Args.Num("crowd-inner", 3f);
    /// <summary>Moves a boss or cinematic actor from people's layer to CastLayer (other bits kept), and keeps its later meshes (the folk shadow) there.</summary>
    public static void ToCast(Node n)
    {
        if (n is PersonView pv) pv.OnCast = true;
        if (n is GeometryInstance3D g && (g.Layers & 2u) != 0) g.Layers = (g.Layers & ~2u) | CastLayer;
        foreach (var c in n.GetChildren()) ToCast(c);
    }
    /// <summary>True: her meshes on HerLayer, not on layer 2 (GameCloseUp, the close view by night).</summary>
    public bool OwnLayer;
    bool ownShown;
    float lamp = 1;
    // Their own clips (hers, or his) and carriage.
    readonly bool mine;
    /// <summary>(L1 lead 19, SH2) Her own fire shadow: one cast quad (World/FireCast.cs, shaders/crowd_blob_cast.gdshader)
    /// and its shape, m (--her-cast-long, --her-cast-wide: its length from her feet and its width at them).</summary>
    MultiMeshInstance3D? herCast;
    HerShadow? herShadow;
    const float HerCastTall = 1.7f;
    static readonly float HerCastLong = SurvivorUnchained.Args.Num("her-cast-long", 1.2f), HerCastWide = SurvivorUnchained.Args.Num("her-cast-wide", 0.4f);   // (SH3: a short tapered trail her stance wide, not a disc)
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
    // The arm-hold layer (the arms copy, HerArmHold, the grip ease): A only (ArmHold.Layered).
    bool layered = true, isB;
    /// <summary>(lead r12) B's run weight on the way down (eased over StopEase s; up it follows at once).</summary>
    float wDown;
    const float StopEase = 0.1f;   // (e25: 0.06 spread r11's 23 deg snap over 3 frames, 8/11/4; 0.1 gives 5, each under 7)
    // The clips' grips (slide, tilt: animations 47, 48, 58) and the side carry (SideCarry) on them: any body. They turn the
    // held piece in its fist, not her bones, so B's bake (bones only) does not carry them (round 11: off on B, the warden's
    // stand blade lay at the pocket's 30 deg pitch, not the clip's 63: a cane). PersonView.Slide tilts about B's own pocket.
    const bool grips = true;

    /// <summary>A gait clip's ground speed: on B a P4 clip's own (P4Overlay.Speed), else heroine_clips.json's.</summary>
    float Spd(string clip)
    {
        if (!isB) return own.Speed(clip);
        if (own == OwnClips.Her) P1Body.HerClips();   // (loads the overlay, which records the P4 speeds)
        return P4Overlay.Speed(clip, P1Body.P4Speeds, own.Speed(clip));
    }
    // What Carry asked of the fade this frame, handed to HerArmHold after the tree's next Advance (the frame it shows).
    (bool Fading, float E, Animation? Walk, Animation? Run, Animation? Sprint, double WalkT, double RunT, float Fast) armFade;
    static readonly bool ArmBlendOff = SurvivorUnchained.Args.Get("arm-blend") == "off";
    // --anim-log: per frame, her move weights, the arm-hold switch and the shots (the pose ruler's frames: P1PoseProbe).
    static readonly bool AnimLog = SurvivorUnchained.Args.Has("anim-log");
    // Her gait (animation 51): the walk's and run's ground speeds and lengths, the shared stride phase (0 = left heel down), and how long she has stood.
    float walkSpeed, walkLen, runLen, stride, standT;
    /// <summary>A walk clip's ground speed in her world (Spd, her scale), as GaitClips takes it.</summary>
    float walkNodeSpeed(string clip) => Spd(clip) * person.Root.Scale.X;
    bool hasWalk;
    PersonView? view;
    // Weapons sheathed in town (Play/Sheath.cs): fed each frame from the close-up's situation (Calm).
    readonly Sheath sheath = new();
    readonly StanceHands stanceHands = new();
    StanceCarry? stanceCarry;
    static readonly bool CarryLog = Args.Has("carry-log"); int carryLogT = -1;
    // --death-log: every frame, after her skeleton's pose is final (SkeletonUpdated), who drives it (tree active, the player's
    // clip and position) and the largest bone turn from rest, in degrees (body-switch 24 Nov: a near-rest pose 0.4-0.7 s into
    // her death). Diagnostics only.
    static readonly bool DeathLog = Args.Has("death-log"); bool deathHooked;    void DeathLogStep()
    {
        var sk = person.Skeleton;
        float worst = 0, sum = 0, major = 0; int wb = -1, nMajor = 0; double sig = 0;
        for (int i = 0; i < sk.GetBoneCount(); i++)
        {
            var q = sk.GetBonePoseRotation(i); var r = sk.GetBoneRest(i).Basis.GetRotationQuaternion();
            float a = Mathf.RadToDeg(q.AngleTo(r));
            sum += a; sig += (i + 1) * (q.X * 3 + q.Y * 5 + q.Z * 7 + q.W * 11);
            var bn = sk.GetBoneName(i);
            if (bn is "pelvis" or "spine_01" or "spine_02" or "spine_03" or "neck_01" or "head" or "upperarm_l" or "upperarm_r" or "lowerarm_l" or "lowerarm_r"
                or "thigh_l" or "thigh_r" or "calf_l" or "calf_r") { major += a; nMajor++; }
            if (a > worst) { worst = a; wb = i; }
        }
        GD.Print($"deathlog pose f {Engine.GetProcessFrames()} mean {sum / Mathf.Max(1, sk.GetBoneCount()):0.00} major {(nMajor > 0 ? major / nMajor : -1):0.00} n {nMajor} sig {sig:0.000000}");
        var an = person.Anim;
        GD.Print($"deathlog f {Engine.GetProcessFrames()} t {time:0.000} dt {probeDt:0.0000} dead {dead} tree {tree.Active} anim {an.CurrentAnimation} pos {(an.IsPlaying() || an.CurrentAnimation != "" ? an.CurrentAnimationPosition : -1):0.000} playing {an.IsPlaying()} maxturn {worst:0.0} bone {(wb >= 0 ? sk.GetBoneName(wb) : "-")}");
    }
    bool entered, safeNow, threatNow, actedNow;
    bool upperNative, fullNative, fullSoft;
    /// <summary>The full shot is a soft one that gave way to her moving and is only fading out (it holds nothing).</summary>
    bool fullGaveWay;
    float heading, turnRate, aim, aimHold, lastSpeed, accel;
    // A1 lead 19: her 2D move node (BlendSpace2D) when her library has the directional walks, and, with it, the facing that
    // holds her aim (aimFace) while aimHold runs, the legs walking her velocity in her facing's frame (move2dPos: x right, y forward).
    bool move2D;
    // Without the side clips: the forward graph plus a back walk blended over it (backBlend, backScale); the legs still turn by LowerTurn.
    bool moveBack;
    float backBlendNow, backFy, backVb = 1;
    bool AimLegs => move2D || moveBack;
    float aimFace;
    Vector2 move2dPos;
    // The lower-body turn (LowerTurn): the eased yaw her pelvis takes (deg), and the mode it is in; the side clips, when her library has them.
    float lowerDelta;
    bool lowerBack, move2DSides, aimFacingNow;
    // Her velocity this frame and last (the lean reads her travel's curve, not her facing's turn).
    float velX, velZ, lastVelX, lastVelZ;
    // Standing and running, for her breaks and her breath.
    double stillT, runT, ranFor, breakAt = 9;
    /// <summary>(aim-move, 15 Nov) Her idle's own clock (s): the idle is seeked to it every frame, so a stop that lands on
    /// the idle's frame 0 sets it to end there (StopSync) and the break (Prowl's own first frames, a wrist's circle laid
    /// on) starts on the idle's frame 0. Prowl moves 5-8 cm through its 6.9 s loop: unsynced, both faded into it off phase.</summary>
    double idleAt;
    readonly RandomNumberGenerator rng = new();

    public PlayerView(Loadout lo)
    {
        loadout = lo;
        Name = "Survivor";
        AddToGroup(Brush.HerGroup);
        // --held-right ID (pictures only): that Arms piece in her right hand and nothing else held (a clip with its own
        // piece, e.g. The Long Cut's sunder_blade; animation 59).
        var heldRight = SurvivorUnchained.Args.Get("held-right");
        // --offhand off (pictures only): no forearm shield on her either, so back views see her armor.
        var noShield = SurvivorUnchained.Args.Get("offhand") is "off" or "0" or "false";
        var v = new PersonView(lo.Person, heldRight != null ? new World.Held { Right = heldRight }
            : new World.Held { Right = lo.Arms.Right, Left = lo.Arms.Left, Forearm = noShield ? null : lo.Arms.Forearm }, 0.8);
        person = v.Person;
        view = v;
        AddChild(v);
        if (person.Own is { } o) own = o;
        mine = person.Own != null;
        if (mine && person.Body == "heroine" && SurvivorUnchained.Args.Has("wear-inside")) person.Root.AddChild(new WearInside(person.Skeleton));   // (the armor-inside measure: nothing without the flag)
        var bt = new AnimationNodeBlendTree();
        AnimationNode moveNode;
        // B (P1): no arm-hold layer (ArmHold.Layered): its holds are clip data.
        isB = P1Body.IsB(person.Skeleton);
        layered = ArmHold.Layered(isB);
        if (mine)
        {
            v.Driven = true;
            // Standing and running blended by speed; the run played at the
            // rate that keeps her feet where they land.
            var idle = People.Clip(person, lo.Arms.Idle);
            var run = People.Clip(person, "Jog_Fwd_Loop");
            runSpeed = run.StartsWith(own.Prefix) ? Spd(run[own.Prefix.Length..]) * person.Root.Scale.X : 5.3f;
            // Her sprint is her run pushed, in step with it (the same frames,
            // the left foot down at the start of both), so the two blend by
            // speed with the legs together; both keep running unseen.
            var sprint = run.StartsWith(own.Prefix + "run_") ? "sprint" + run[(own.Prefix.Length + 3)..] : "";
            sprintSpeed = own.Has(sprint) ? Spd(sprint) * person.Root.Scale.X : runSpeed;
            var mv = new AnimationNodeBlendTree();
            idleNode = new AnimationNodeAnimation { Animation = idle };
            runNode = new AnimationNodeAnimation { Animation = run };
            mv.AddNode("idle", idleNode, new Vector2(0, 0));
            mv.AddNode("idleSeek", new AnimationNodeTimeSeek(), new Vector2(200, 0));
            mv.ConnectNode("idleSeek", 0, "idle");
            mv.AddNode("run", runNode, new Vector2(0, 200));
            sprintNode = new AnimationNodeAnimation { Animation = own.Has(sprint) ? own.Prefix + sprint : run };
            mv.AddNode("sprint", sprintNode, new Vector2(0, 400));
            mv.AddNode("fast", new AnimationNodeBlend2 { Sync = true }, new Vector2(200, 300));
            // Her walk (if she has one for this calling and state) and her run are each seeked every frame to the shared
            // stride phase, so they stay on the same foot through the blend.
            walkNode = new AnimationNodeAnimation { Animation = run };
            SyncAn();
            mv.AddNode("walk", walkNode, new Vector2(0, 100));
            mv.AddNode("walkSeek", new AnimationNodeTimeSeek(), new Vector2(200, 100));
            mv.AddNode("runSeek", new AnimationNodeTimeSeek(), new Vector2(400, 300));
            mv.AddNode("blendW", new AnimationNodeBlend2(), new Vector2(400, 0));
            mv.AddNode("blend", new AnimationNodeBlend2(), new Vector2(600, 100));
            mv.ConnectNode("fast", 0, "run");
            mv.ConnectNode("fast", 1, "sprint");
            mv.ConnectNode("walkSeek", 0, "walk");
            mv.ConnectNode("runSeek", 0, "fast");
            mv.ConnectNode("blendW", 0, "idleSeek");
            mv.ConnectNode("blendW", 1, "walkSeek");
            mv.ConnectNode("blend", 0, "blendW");
            mv.ConnectNode("blend", 1, "runSeek");
            // The arms' copy: the same clips, seeks and weights but the switched run weight (fed in Carry). Not on B
            // (ArmHold.Layered): B's clips carry their holds, the graph blends them as authored.
            if (layered)
            {
                aIdle = new AnimationNodeAnimation { Animation = idle };
                aWalk = new AnimationNodeAnimation { Animation = run };
                aRun = new AnimationNodeAnimation { Animation = run };
                aSprint = new AnimationNodeAnimation { Animation = sprintNode.Animation };
                mv.AddNode("aIdle", aIdle, new Vector2(0, 600));
                mv.AddNode("aIdleSeek", new AnimationNodeTimeSeek(), new Vector2(200, 600));
                mv.ConnectNode("aIdleSeek", 0, "aIdle");
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
                mv.ConnectNode("aBlendW", 0, "aIdleSeek");
                mv.ConnectNode("aBlendW", 1, "aWalkSeek");
                mv.ConnectNode("aBlend", 0, "aBlendW");
                mv.ConnectNode("aBlend", 1, "aRunSeek");
                mv.ConnectNode("arms", 0, "blend");
                mv.ConnectNode("arms", 1, "aBlend");
                mv.ConnectNode("output", 0, "arms");
            }
            else mv.ConnectNode("output", 0, "blend");
            moveNode = mv;
            // (A1 lead 19) The directional walks (walk_<calling>_back/_left/_right, her armed walk's own): one 2D node, her velocity in her
            // facing's frame on it. Any one missing: today's graph, unchanged. Points sit at the speeds the graph above plays by (Spd).
            var wn = own.Walk(person.Calling, person.Kind, false);
            var wb = wn?[own.Prefix.Length..];
            if (wb != null && HasHer(wb + "_back") && walkNodeSpeed(wb) > 0.05f)
            {
                move2DSides = HasHer(wb + "_left") && HasHer(wb + "_right");
                float vw = walkNodeSpeed(wb);
                // Each directional point sits at its own clip's ground speed (the back ~1.3 m/s, the sides ~0.95), as the cast-move caps walk her (Sim/CastMove.cs).
                float vb = walkNodeSpeed(wb + "_back"), vl = walkNodeSpeed(wb + "_left"), vr = walkNodeSpeed(wb + "_right");
                if (vb < 0.05f) vb = vw;
                if (vl < 0.05f) vl = vw;
                if (vr < 0.05f) vr = vw;
                if (!move2DSides)
                {
                    // No side clips: the points would all lie on x = 0 (no triangles, frozen legs). Keep the forward graph (its seeks and
                    // stride) and lay the back walk over it: backBlend (input 1 = backScale, a TimeScale on the back clip) before the output.
                    var wbk = new AnimationNodeAnimation { Animation = own.Prefix + wb + "_back" };
                    mv.AddNode("backClip", wbk, new Vector2(1000, 500));
                    mv.AddNode("backScale", new AnimationNodeTimeScale(), new Vector2(1200, 500));
                    mv.AddNode("backBlend", new AnimationNodeBlend2(), new Vector2(1400, 300));
                    mv.ConnectNode("backScale", 0, "backClip");
                    string last = layered ? "arms" : "blend";
                    // (a node's output feeds one input only: free "last" from the output first, or the connect fails and the tree goes to rest)
                    mv.DisconnectNode("output", 0);
                    mv.ConnectNode("backBlend", 0, last);
                    mv.ConnectNode("backBlend", 1, "backScale");
                    mv.ConnectNode("output", 0, "backBlend");
                    backVb = vb;
                    moveBack = true;
                    goto skip2D;
                }
                var two = new AnimationNodeBlendSpace2D { MinSpace = new Vector2(-Mathf.Max(runSpeed, sprintSpeed), -Mathf.Max(runSpeed, sprintSpeed)), MaxSpace = new Vector2(Mathf.Max(runSpeed, sprintSpeed), Mathf.Max(runSpeed, sprintSpeed)), SyncMode = AnimationNodeBlendSpace2D.SyncModeEnum.Independent };
                walkNode = new AnimationNodeAnimation { Animation = own.Prefix + wb };
                SyncAn();
                two.AddBlendPoint(idleNode, new Vector2(0, 0));
                two.AddBlendPoint(walkNode, new Vector2(0, vw));
                two.AddBlendPoint(new AnimationNodeAnimation { Animation = own.Prefix + wb + "_back" }, new Vector2(0, -vb));
                if (move2DSides)
                {
                    two.AddBlendPoint(new AnimationNodeAnimation { Animation = own.Prefix + wb + "_left" }, new Vector2(-vl, 0));
                    two.AddBlendPoint(new AnimationNodeAnimation { Animation = own.Prefix + wb + "_right" }, new Vector2(vr, 0));
                }
                two.AddBlendPoint(runNode, new Vector2(0, runSpeed));
                if (sprintSpeed > runSpeed * 1.05f && sprintNode.Animation != runNode.Animation) two.AddBlendPoint(sprintNode, new Vector2(0, sprintSpeed));
                moveNode = two;
                move2D = true;
            }
            skip2D:
            GaitClips(People.Clip(person, "Jog_Fwd_Loop"));
            if (!AimLegs && !DirLegsOff && run.StartsWith(own.Prefix)) BuildDir(mv, run, layered ? "arms" : "blend");
            carriage = new HerCarriage();
            person.Skeleton.AddChild(carriage);
            person.Skeleton.MoveChild(carriage, 0);
            // First of all, on the tree's own pose (before her carriage, her pose layer and the helpers).
            // Not on B (ArmHold.Layered; the owner, 5 Nov: the arm-hold crossfade is retired for B): B's holds are clip
            // data (P4), so B has no HerArmHold and no arms' copy. (armMod null -> armNow false.)
            if (layered)
            {
                armMod = new HerArmHold();
                person.Skeleton.AddChild(armMod);
                person.Skeleton.MoveChild(armMod, 0);
            }
            // Her off-hand piece carried out from her side in a stance (view only), right after the arm-hold layer.
            stanceCarry = new StanceCarry();
            person.Skeleton.AddChild(stanceCarry);
            person.Skeleton.MoveChild(stanceCarry, armMod != null ? 1 : 0);
            // (aim-move) A has no lower-body turn (B's is People.Her's): hers sits right before HerPose, after the carriage and the
            // layers above, so every reader of her pose (HerPose, Gestures, the shapes) sees the turned legs and the untouched chest.
            if (dirChain && person.Turn == null)
            {
                person.Turn = new LowerTurnModifier { Frame = person.Root };
                person.Skeleton.AddChild(person.Turn);
                person.Skeleton.MoveChild(person.Turn, person.Pose != null ? person.Pose.GetIndex() : person.Skeleton.GetChildCount() - 1);
            }
            if (dirChain && SurvivorUnchained.Args.Has("turn-last")) Callable.From(() => { if (person.Turn != null && IsInstanceValid(person.Turn)) person.Skeleton.MoveChild(person.Turn, person.Skeleton.GetChildCount() - 1); }).CallDeferred();
            if (dirChain && SurvivorUnchained.Args.Has("dirrun")) Callable.From(() => GD.Print("SKELKIDS " + string.Join(",", person.Skeleton.GetChildren().Select(c => c.Name.ToString())))).CallDeferred();
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
        var fullShot = new AnimationNodeOneShot { FadeInTime = FullFadeIn, FadeOutTime = 0.2 };
        fullShotNode = fullShot;
        upperShotNode = upperShot;
        fullOld = new AnimationNodeAnimation { Animation = full.Animation };
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
        // (--act: a seek node between the clip and its pace, to jump a held loop back; nothing is added without it)
        if (ActOn && mine)
        {
            bt.AddNode("fullSeek", new AnimationNodeTimeSeek(), new Vector2(500, 300));
            bt.ConnectNode("fullSeek", 0, "full");
            bt.ConnectNode("fullScale", 0, "fullSeek");
        }
        else bt.ConnectNode("fullScale", 0, "full");
        // (the clip she was in, at its place and pace, crossfaded out under the new one: FullHerFrom)
        bt.AddNode("fullOld", fullOld, new Vector2(400, 450));
        bt.AddNode("fullOldScale", new AnimationNodeTimeScale(), new Vector2(600, 450));
        bt.AddNode("fullOldSeek", new AnimationNodeTimeSeek(), new Vector2(700, 450));
        bt.AddNode("fullX", new AnimationNodeBlend2(), new Vector2(750, 300));
        bt.ConnectNode("fullOldScale", 0, "fullOld");
        bt.ConnectNode("fullOldSeek", 0, "fullOldScale");
        bt.ConnectNode("fullX", 0, "fullScale");
        bt.ConnectNode("fullX", 1, "fullOldSeek");
        bt.ConnectNode("fullShot", 0, "upperShot");
        bt.ConnectNode("fullShot", 1, "fullX");
        bt.ConnectNode("output", 0, "fullShot");
        tree = new AnimationTree { TreeRoot = bt, RootNode = "..", Active = true };
        // (P1's B plays the clips baked onto it: the same names, B's bones)
        bool p1 = P1Body.IsB(person.Skeleton);
        tree.AddAnimationLibrary("", p1 ? P1Body.Clips() : People.Clips());
        if (mine)
        {
            tree.AddAnimationLibrary(own.Name, p1 && own == OwnClips.Her ? P1Body.HerClips() ?? own.Library() : own.Library());
            // Her clips run on the fight's clock (Update advances them), so a
            // hit-stop or a perfect dodge's slow motion holds her as well.
            tree.CallbackModeProcess = AnimationMixer.AnimationCallbackModeProcess.Manual;
        }
        person.Root.AddChild(tree);
        Light = new OmniLight3D { LightColor = EmberOwn, LightEnergy = LightBase / Mathf.Pi, OmniRange = 11, OmniAttenuation = 1.4f, ShadowEnabled = false, Position = new Vector3(0, 2.4f, 0.4f) };
        AddChild(Light);
        FolkLight = new OmniLight3D { LightColor = new Color(SurvivorUnchained.Args.Get("ember-folk-color") ?? "#ffc08a"), LightEnergy = 0, OmniRange = 11, ShadowEnabled = false, LightCullMask = 2u | HerLayers, Position = new Vector3(0, FolkH, FolkZ) };
        AddChild(FolkLight);
        if (mine) { RimLight = new OmniLight3D { Name = "HerRim", LightEnergy = 0, ShadowEnabled = false, LightCullMask = HerLayers, LightSpecular = HeroDen.RimTag, Visible = false }; AddChild(RimLight); }
        // (L1 lead 19, SH2) Her own short shadow under her fire (FireCast: one quad; placed every frame below).
        if (mine) { herCast = FireCast.Make("HerCast", 1); AddChild(herCast); }
        if (mine) { herShadow = new HerShadow(); AddChild(herShadow); }   // (demo-look r2 her: her cast shadow in the den)
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
        FolkLight.LightEnergy = old.FolkLight.LightEnergy;
        FolkLight.OmniRange = old.FolkLight.OmniRange;
        if (RimLight != null && old.RimLight != null) { RimLight.LightEnergy = old.RimLight.LightEnergy; RimLight.Position = old.RimLight.Position; rimGate = old.rimGate; rimSeen = old.rimSeen; }
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
            g.MaterialOverlay = on ? wraith : xrayK > 0 && xrayOn.Contains(g) ? xray : null;
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
    // (the pelvis counter's inputs: the upper clip's pace, and when its fade out was asked for (-1 none); PelvisCounterModifier)
    double upperRate = 1, upperRelease = -1;
    float slide, tilt, slideL, tiltL, pocketL;

    void Upper(string clip, double speed)
    {
        upperClip = clip;
        upper.Animation = People.Clip(person, clip); upperAnim = null;
        upperNative = upper.Animation.ToString().StartsWith(own.Prefix);
        upperHeld = float.NaN;
        tree.Set(P_upperScale_scale, speed);
        upperRate = speed; upperRelease = -1;
        if (person.Counter != null) person.Counter.Mean = null;
        tree.Set(P_upperShot_request, (int)AnimationNodeOneShot.OneShotRequest.Fire);
    }

    /// <summary>One of her own clips on her upper body, by its own name.</summary>
    bool UpperHer(string clip, double speed)
    {
        if (!mine || !own.Has(clip)) return false;
        upperClip = clip;
        upperShotNode.FadeOutTime = 0.18; fullShotNode.FadeOutTime = 0.2;   // (a release's recover lengthens them: OnSwingRelease)
        // Standing, a stance swing takes her whole body (its own feet set and hips into the blow), soft:
        // it gives way to the run the moment she moves. Moving, it rides her upper body over the run.
        if (this.speed < 0.6f && own.Stance(clip)) return FullHer(clip, speed, true);
        upper.Animation = own.Prefix + RunVariant(clip); upperAnim = null;
        upperNative = true;
        upperHeld = float.NaN;
        tree.Set(P_upperScale_scale, speed);
        upperRate = speed; upperRelease = -1;
        if (person.Counter != null) person.Counter.Mean = own.PelvisMean(RunVariant(clip));
        tree.Set(P_upperShot_request, (int)AnimationNodeOneShot.OneShotRequest.Fire);
        return true;
    }

    /// <summary>A stance swing re-aimed for her run's hips, where one is keyed (clip + "_run", e.g. axe_fore_run):
    /// moving, her hips are the run's, not turned into the blow, so the stance clip's arms land elsewhere.</summary>
    string RunVariant(string clip) => own.Stance(clip) && own.Has(clip + "_run") ? clip + "_run" : clip;

    void Full(string clip, double speed)
    {
        XfadeStop();
        fullClip = clip;
        fullStart = time; fullSpeed = (float)speed;
        full.Animation = People.Clip(person, clip);
        fullNative = full.Animation.ToString().StartsWith(own.Prefix);
        fullSoft = fullGaveWay = false;
        tree.Set(P_fullScale_scale, speed);
        tree.Set(P_fullShot_request, (int)AnimationNodeOneShot.OneShotRequest.Fire);
        FullBlendIn(mine && fullNative ? full.Animation.ToString()[own.Prefix.Length..] : null);
        if (mine && fullNative) IdleSyncLater(full.Animation.ToString()[own.Prefix.Length..], speed);
    }

    /// <summary>One of her own on the whole of her: soft ones (a fidget, a
    /// breath caught) give way the moment she moves.</summary>
    /// <summary>Her clip by name: in her own library, or (--body p1) in the P1 library laid into the animation player.</summary>
    bool HasHer(string clip) => own.Has(clip) || person.Anim.HasAnimation(own.Prefix + clip);

    // A1 blend_in: a clip may carry its own blend-in (her_events.json), default unchanged
    double fullBlendIn = FullFadeIn;
    void FullBlendIn(string? herClip) => fullShotNode.FadeInTime = fullBlendIn = herClip != null ? HerEvents.BlendIn(herClip, FullFadeIn) : FullFadeIn;

    bool FullHer(string clip, double speed, bool soft)
    {
        if (!mine || !HasHer(clip)) return false;
        XfadeStop();
        fullShotNode.FadeOutTime = 0.2; upperShotNode.FadeOutTime = 0.18;
        FullBlendIn(clip);
        fullClip = clip;
        fullStart = time; fullSpeed = (float)speed;
        full.Animation = own.Prefix + clip;
        fullNative = true;
        IdleSyncLater(clip, speed);
        fullSoft = soft; fullGaveWay = false;
        tree.Set(P_fullScale_scale, speed);
        tree.Set(P_fullShot_request, (int)AnimationNodeOneShot.OneShotRequest.Fire);
        return true;
    }

    /// <summary>The whole-body shot's usual fade in, from the layer under it.</summary>
    const double FullFadeIn = 0.05;
    double xfadeFrom = -1, xfadeLen;

    /// <summary>FullHer, crossfaded over `xfade` seconds from her LIVE pose: from the whole-body clip she was in (held on
    /// at its place and pace under the new one, then let go), or, with none, from the layers under (the shot's own fade
    /// in, lengthened). The full shot's 0.05 s fade blends only from the layer under it, so a press mid-swing dropped the
    /// swing in one frame (the Long Cut's f0 pop). For the Flare's press; any other cut can use it.</summary>
    bool FullHerFrom(string clip, double speed, bool soft, double xfade)
    {
        if (!mine || !HasHer(clip)) return false;
        bool live = (bool)tree.Get(P_fullShot_active);
        var oldAnim = full.Animation;
        double oldAt = (time - fullStart) * fullSpeed;
        float oldSpeed = fullSpeed;
        if (!FullHer(clip, speed, soft)) return false;
        if (live)
        {
            fullOld.Animation = oldAnim;
            tree.Set(P_fullOldScale_scale, oldSpeed);
            tree.Set(P_fullOldSeek_seek_request, oldAt);
            tree.Set(P_fullX_blend_amount, 1.0);
            // (the restarted shot comes in at once: its live pose is the held clip, eased out below)
            fullShotNode.FadeInTime = 0;
        }
        else fullShotNode.FadeInTime = xfade;
        xfadeFrom = time; xfadeLen = xfade;
        return true;
    }

    /// <summary>The crossfade's ease (before the tree is advanced): the held clip let go over its length, smoothly.</summary>
    void Xfade()
    {
        if (xfadeFrom < 0) return;
        double k = System.Math.Clamp((time - xfadeFrom) / System.Math.Max(1e-4, xfadeLen), 0, 1);
        tree.Set(P_fullX_blend_amount, 1 - k * k * (3 - 2 * k));
        // (the shot's lengthened fade in is left as it is until its next fire: the shot's own clock runs a frame or two
        // behind this one, and putting it back at 0.05 here cut the last of its fade in a frame, the f7 jump of r1)
        if (k >= 1) { xfadeFrom = -1; tree.Set(P_fullX_blend_amount, 0.0); UpperLetGo(); }
    }

    /// <summary>The held blow under a crossfade let go on at its own pace (hidden under the whole-body shot by then).</summary>
    void UpperLetGo()
    {
        if (float.IsNaN(upperHeld)) return;
        tree.Set(P_upperScale_scale, upperHeld);
        upperHeld = float.NaN;
    }

    void XfadeStop()
    {
        UpperLetGo();
        fullShotNode.FadeInTime = FullFadeIn;
        if (xfadeFrom < 0) return;
        xfadeFrom = -1;
        tree.Set(P_fullX_blend_amount, 0.0);
        fullShotNode.FadeInTime = FullFadeIn;
    }

    /// <summary>An art's landing or stop plays out only while she stands:
    /// once the art is done (artTail) and she moves, it fades into her run.</summary>
    void ArtTail(float sp)
    {
        if (artTail < 0 || time < artTail) return;
        if (sp > 0.6f && (bool)tree.Get(P_fullShot_active))
            tree.Set(P_fullShot_request, (int)AnimationNodeOneShot.OneShotRequest.FadeOut);
        if (sp > 0.6f || !(bool)tree.Get(P_fullShot_active)) artTail = -1;
    }

    double artTail = -1;

    // A Flare's own clip (FlareDef.Clip): the facing it holds, and the grip that lasts exactly as long as the clip plays.
    double flareFaceUntil = -1, flareYawAt = -1; float flareFaceY, flareYawFrom;
    // (the blow she was in, held where it was at the press under the crossfade; NaN: none held)
    float upperHeld = float.NaN;
    string? flareClipName; double flareClipStart; bool flareClipSeen;

    /// <summary>Ev.SwingRelease: a released cut that does not end on her stance (SwingRecover) fades from its live pose to the
    /// armed idle over the sim's Recover, instead of running out and fading in 0.2 s. A press inside the grace fires the next
    /// cut over that fade (its own blend_in reads from the pose then). Held, no release is told, so nothing here.</summary>
    public void OnSwingRelease(Ev.SwingRelease e)
    {
        if (!mine || dead) return;
        bool full = (bool)tree.Get(P_fullShot_active) && HasHer(fullClip);
        bool up = (bool)tree.Get(P_upperShot_active);
        if (SwingRecover.Fade(full ? fullClip : up ? upperClip : null, e.Recover) is not double fade) return;
        var (node, path) = full ? (fullShotNode, P_fullShot_request) : (upperShotNode, P_upperShot_request);
        node.FadeOutTime = fade;
        if (!full) upperRelease = time;
        tree.Set(path, (int)AnimationNodeOneShot.OneShotRequest.FadeOut);
    }

    /// <summary>The Flare's press (Ev.Flare, Press): her own full-body clip if its data names one, facing the aim, with
    /// its grip formed in her hands for the clip's length. Without a Clip (or without that clip) nothing happens.</summary>
    public void OnFlarePress(Ev.Flare e, Battle b)
    {
        if (!mine || dead || Content.Lamps.Flare(e.Id) is not { Clip: { } clip } def || !own.Has(clip)) return;
        // (the sim's line runs TX = X + cos, TZ = Z + sin; her facing for (dx, dz) is atan2(dx, dz))
        float face = Mathf.Atan2((float)System.Math.Cos(e.Angle), (float)System.Math.Sin(e.Angle));
        // (turned onto its line over the crossfade, not in a frame: r2's press swung her whole body round at once, 0.7 m of wrist)
        flareYawFrom = Rotation.Y; flareYawAt = time;
        aim = 0;
        flareFaceY = face;
        flareFaceUntil = time + def.ClipFree;
        FlareClipEnd();
        if (GripProbe)
        {
            bool live = (bool)tree.Get(P_fullShot_active);
            GD.Print($"grip probe press: full shot {(live ? $"{fullClip} at {(time - fullStart) * fullSpeed:0.000} s (soft {fullSoft})" : "none")}, upper {((bool)tree.Get(P_upperShot_active) ? upperClip : "-")}");
            probeN = 0; probeTipLocal = null; probeVisN = -1;
        }
        gripShowAt = -1;
        // (formed at the press but hidden: the blade shows once her hand is at the coil, FlareXfade on)
        if (def.Grip != null && view != null && view.FlareGrip(def.Grip) && view.FlareGripNode is { } gn) { gn.Visible = false; gripShowAt = time + FlareXfade + GripSettle; }
        if (armMod != null) armMod.AxisR = armMod.AxisL = Vector3.Zero;
        // (from her live pose over 0.1 s, 3 of the clip's frames: no swing dropped in a frame)
        bool wasLive = (bool)tree.Get(P_fullShot_active);
        if (!FullHerFrom(clip, 1, false, FlareXfade)) { gripShowAt = -1; flareYawAt = -1; view?.FlareGripEnd(); return; }
        // The blow on her arms (the upper shot) is held at the pose she was drawn in at the press while the Flare's clip fades
        // in over it, then let go on (hidden): r2's swing ran on under the fade, 0.2-0.35 m of wrist a frame.
        if ((bool)tree.Get(P_upperShot_active))
        {
            upperHeld = (float)tree.Get(P_upperScale_scale);
            tree.Set(P_upperScale_scale, 0f);
        }
        // The shot's fade from the layers under starts on the press's own frame: the tree takes the request and its fade's first
        // step now, with the Flare's clip and the held blow still (a one-shot takes the fire on one advance and draws its fade's first step at no weight on the next,
        // and r2's press held her two frames, then caught up). The layers under step a frame of their own idle, unseen.
        if (!wasLive)
        {
            tree.Set(P_fullScale_scale, 0f);
            tree.Advance(0);   // (the fire taken: the fade's clock set)
            tree.Advance(1.0 / 60);   // (its first step, which a one-shot draws at no weight)
            tree.Set(P_fullScale_scale, 1f);
        }
        flareClipName = clip; flareClipStart = time; flareClipSeen = false;
        artTail = time + def.ClipFree;
    }

    // --grip-probe: her right hand and the grip's tip in the world for the 40 rendered frames after a Flare's press
    // (each frame's line is the pose drawn the frame before: measured before the tree is advanced), and each one's step.
    static readonly bool GripProbe = Args.Has("grip-probe");
    int probeN = -1;
    Quaternion probeHq; Vector3 probeHand, probeTip; Vector3? probeTipLocal;
    double fullStart; float fullSpeed = 1;

    // (the body's line: both wrists and elbows, her pelvis height and stance, each frame, the 2 before the press kept)
    static readonly string[] ProbeBones = ["hand_l", "hand_r", "lowerarm_l", "lowerarm_r"];
    readonly Vector3[] probeW = new Vector3[4], probeL = new Vector3[4];
    bool probeWHave;
    readonly System.Collections.Generic.Queue<string> probePre = new();
    double probeDt, probeFight;

    string ProbeBody()
    {
        var skel = person.Skeleton;
        var inv = GlobalTransform.AffineInverse();
        var sb = new System.Text.StringBuilder();
        float maxW = 0, maxL = 0;
        for (int i = 0; i < 4; i++)
        {
            var w = skel.GlobalTransform * skel.GetBoneGlobalPose(skel.FindBone(ProbeBones[i])).Origin;
            var l = inv * w;
            float sw = probeWHave ? (w - probeW[i]).Length() * 1000 : 0, sl = probeWHave ? (l - probeL[i]).Length() * 1000 : 0;
            sb.Append($"{ProbeBones[i]} {sw:0}/{sl:0} ");
            maxW = Mathf.Max(maxW, sw); maxL = Mathf.Max(maxL, sl);
            probeW[i] = w; probeL[i] = l;
        }
        probeWHave = true;
        Vector3 B(string n) => inv * (skel.GlobalTransform * skel.GetBoneGlobalPose(skel.FindBone(n)).Origin);
        var fl = B("foot_l"); var fr = B("foot_r");
        float stance = new Vector2(fl.X - fr.X, fl.Z - fr.Z).Length();
        return $"body: steps world/local mm {sb}(max {maxW:0}/{maxL:0}), pelvis {B("pelvis").Y:0.000} m, stance {stance:0.000} m, dt {probeDt * 1000:0.0} ms, fight {probeFight:0.000}, upper {((bool)tree.Get(P_upperShot_active) ? upperClip : "-")}, full {((bool)tree.Get(P_fullShot_active) ? fullClip : "-")}";
    }

    void Probe()
    {
        if (probeN < 0)
        {
            probePre.Enqueue(ProbeBody());
            while (probePre.Count > 2) probePre.Dequeue();
            return;
        }
        if (probeN == 0) { int k = -probePre.Count; foreach (var pl in probePre) GD.Print($"grip probe f{k++} {pl}"); probePre.Clear(); }
        GD.Print($"grip probe f{probeN} {ProbeBody()}");
        if (probeN < 0 || probeN > 120 || probeN > 12 && fullClip != flareClipName) { probeN = -1; return; }
        var skel = person.Skeleton;
        int hb = skel.FindBone("hand_r");
        var hand = skel.GlobalTransform * skel.GetBoneGlobalPose(hb).Origin;
        Vector3? tip = null;
        if (view?.FlareGripNode is { Visible: true } g && probeN > 0)
        {
            if (probeVisN < 0) probeVisN = probeN;
            if (probeTipLocal == null)
            {
                // the grip's farthest point from its seat (its mesh's box corners, in the mount's space)
                float best = -1; var far = Vector3.Zero;
                foreach (var n in g.FindChildren("*", "MeshInstance3D", true, false))
                {
                    var mi = (MeshInstance3D)n;
                    var rel = g.GlobalTransform.AffineInverse() * mi.GlobalTransform;
                    var bb = mi.GetAabb();
                    for (int c = 0; c < 8; c++) { var v = rel * bb.GetEndpoint(c); if (v.LengthSquared() > best) { best = v.LengthSquared(); far = v; } }
                }
                probeTipLocal = far;
            }
            tip = g.GlobalTransform * probeTipLocal.Value;
        }
        if (view?.FlareGripNode is { } gm && probeN is >= 4 and <= 11)
        {
            var rel = (skel.GlobalTransform * skel.GetBoneGlobalPose(hb)).AffineInverse() * gm.GlobalTransform;
            var hq = (skel.GlobalTransform * skel.GetBoneGlobalPose(hb)).Basis.GetRotationQuaternion();
            GD.Print($"grip seat f{probeN}: hand turn {Mathf.RadToDeg((hq.Inverse() * probeHq).GetAngle()):0.0} deg;"
            + $" f{probeN}: vis {gm.Visible} local {gm.Transform.Origin} eul {gm.Transform.Basis.GetEuler() * 57.2958f} rel-hand {rel.Origin} eul {rel.Basis.GetEuler() * 57.2958f}");
        }
        bool fullOn = (bool)tree.Get(P_fullShot_active);
        GD.Print($"grip probe f{probeN}: hand_r {hand} step {(probeN > 0 ? (hand - probeHand).Length() * 1000 : 0):0} mm"
            + (tip is { } tp ? $", tip {tp} step {(probeN > probeVisN ? (tp - probeTip).Length() * 1000 : 0):0} mm" : "")
            + (probeN == probeVisN ? " (first visible grip frame)" : "")
            + $", full {(fullOn ? fullClip : "-")} at {(time - fullStart) * fullSpeed:0.000} s, yaw {Mathf.RadToDeg(Rotation.Y):0.0}");
        probeHand = hand; probeHq = (skel.GlobalTransform * skel.GetBoneGlobalPose(hb)).Basis.GetRotationQuaternion();
        if (tip is { } t2) probeTip = t2;
        probeN++;
    }

    // (--flare-xfade S: a developer's try of another length; 0.1 s, 3 of the clip's frames, by default)
    static readonly double FlareXfade = Args.Num("flare-xfade", 0.1f);
    // (the crossfade's last frames still turn her hand ~50 degrees a frame, 0.9 m of tip: the blade shows two frames after it ends, in the settled pose)
    const double GripSettle = 2.0 / 60;
    double gripShowAt = -1;
    int probeVisN = -1;

    void FlareGripShow()
    {
        if (gripShowAt < 0 || time < gripShowAt) return;
        gripShowAt = -1;
        if (view?.FlareGripNode is { } g) { g.Visible = true; if (GripProbe) probeVisN = probeN; }
    }

    void FlareClipEnd()
    {
        flareClipName = null;
        gripShowAt = -1;
        if (view?.FlareGripOn == true) { view.FlareGripEnd(); if (armMod != null) armMod.AxisR = armMod.AxisL = Vector3.Zero; }
    }

    // The grip ends the moment the full shot no longer plays the Flare's clip (finished, faded, or replaced by a dodge).
    void FlareClipWatch()
    {
        if (flareClipName == null) return;
        bool on = (bool)tree.Get(P_fullShot_active) && fullClip == flareClipName;
        if (on) { flareClipSeen = true; return; }
        if (flareClipSeen || time - flareClipStart > 0.5) FlareClipEnd();
    }

    bool Busy => (bool)tree.Get(P_upperShot_active) || (bool)tree.Get(P_fullShot_active);

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
        SyncAn();
        runSpeed = run.StartsWith(own.Prefix) ? Spd(run[own.Prefix.Length..]) * person.Root.Scale.X : 5.3f;
        GaitClips(run, sheathed);
        // (warden-move) The directional set's forward clip is the run just mounted (her town run sheathed, the armed run
        // drawn): the set took the whole run over at speed, so the den run played in town with the hilt hand off the hilt.
        if (dirF != null && person.Anim.HasAnimation(run)) { dirF.Animation = run; dirLen[0] = (float)person.Anim.GetAnimation(run).Length; }
        if (sprintNode == null) return;
        // The sprint follows: her town sprint if she has one, else the town run itself; the armed sprint on the draw.
        var sprint = run.StartsWith(own.Prefix + "run_") ? "sprint" + run[(own.Prefix.Length + 3)..] : "";
        if (own.Has(sprint)) { sprintNode.Animation = own.Prefix + sprint; sprintSpeed = Spd(sprint) * person.Root.Scale.X; }
        else { sprintNode.Animation = run; sprintSpeed = runSpeed; }
        SyncAn();
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
        SyncAn();
        walkSpeed = hasWalk ? Spd(w![own.Prefix.Length..]) * person.Root.Scale.X : 0;
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
        if (clip == "" || time - lastMuzzle < 0.4 || (bool)tree.Get(P_fullShot_active)) return;
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
        // (the 2D node: she faces the aim at any speed, her legs walking by the node; aimHold keeps it, Update)
        aimFace = face;
        // (aim-move) Her facing is Update's (DirFace: the cursor, or this blow's side while aimHold lasts); no flip, no waist, no hips.
        if (mine && DirOn) { faceGoal = hipGoal = null; aim = 0; aimHold = 0.45f; return; }
        // (warden-turn, the owner 10 Nov "movement looked weird especially turning"; A1 leads 20-21 ported) Hers: never a
        // one-frame flip. Standing or slow, her whole body turns to the blow on the eased turn (faceGoal, Update). Running,
        // her waist takes up to 75 deg of it off her travel, eased (Carry); past 100 her hips join (hipGoal). Either way the
        // swing coils on its wind until her shoulders are on the blow (Coil). The sim's aim and blow stay instant.
        hipGoal = null;
        if (mine && !AimLegs && !TurnSnap)
        {
            faceGoal = null;
            if (speed < 1.5f) { faceGoal = face; aim = 0; }
            else
            {
                float travel = velX * velX + velZ * velZ > 0.16f ? Mathf.Atan2(velX, velZ) : Rotation.Y;
                float dt2 = Mathf.RadToDeg(Mathf.Wrap(face - travel, -Mathf.Pi, Mathf.Pi));
                // (t4, judge r2: "a 7-frame sideways glide") Hips held part way round (HipMax) ran the legs on a line off her
                // travel: the stride matched only its cos, the sin part slid. Past BackAt her hips go all the way round, the
                // way the blow lies, and the run plays backwards at her travel's pace (strideK -1, Carry): a backpedal.
                if (!BackOff && Mathf.Abs(dt2) > BackAt) { hipGoal = travel + Mathf.Sign(dt2) * (Mathf.Pi - 0.01f); backpedal = true; }
                else if (Mathf.Abs(dt2) > 100) hipGoal = travel + Mathf.DegToRad(Mathf.Sign(dt2) * Mathf.Min(Mathf.Abs(dt2) - WaistMax, HipMax));
                aim = Mathf.Clamp(Mathf.RadToDeg(Mathf.Wrap(face - (hipGoal ?? Rotation.Y), -Mathf.Pi, Mathf.Pi)), -WaistMax, WaistMax);
            }
        }
        else if (!mine || AimLegs || speed < 1.5f || Mathf.Abs(d) > Mathf.DegToRad(110))
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
        probeDt = dt; probeFight = fightTime;
        if (GripProbe && mine) Probe();
        if (DeathLog && mine && !deathHooked) { deathHooked = true; person.Skeleton.SkeletonUpdated += DeathLogStep; }
        if (DeathLog && mine) GD.Print($"deathlog upd f {Engine.GetProcessFrames()} t {time:0.000} tree {tree.Active} advance {tree.Active}");
        // (body-switch 24 Nov, --death-log) The tree steps only while it is active: Advance writes her skeleton even when the tree is
        // not, so at a death, once her death clip had played out (1.33 s) and the player stopped writing, the tree stood her up again
        // in its idle until the revive (measured: 36 frames standing while dead). Inactive = the player alone owns her pose (death,
        // --hold, --clip-tour); Revive makes the tree active again.
        if (mine) { Xfade(); ActTick(dt); P7Tick(dt); if (tree.Active) tree.Advance(dt); }
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
        if (mine && !PlantOff)
        {
            Position += plantOff + smoothOff + Vector3.Up * BackAirLiftNow();
            plantGround = heightAt; plantDt = (float)dt;
            if (!plantHooked) { plantHooked = true; person.Skeleton.SkeletonUpdated += PlantStep; }
        }
        Reflections.Update(b, dt, heightAt);
        Ghostly(p.Alive && b.Art.WraithT > 0);
        if (mine) XrayStep((float)dt);
        if (mine) FloorStep(b, (float)dt);
        if (mine && view != null && stanceHands.Follow(view, loadout.Arms, b.StanceNow, sheath.Sheathed) && armMod != null) armMod.AxisR = armMod.AxisL = Vector3.Zero;   // (her off-hand follows the stance)
        if (mine && stanceCarry != null)
        {
            // The piece carried out only while it is drawn, she lives, and no swing or full-body shot owns the arm.
            var st = b.StanceNow;
            stanceCarry.Carry = st?.CarryL;
            stanceCarry.On = st?.CarryL != null && !sheath.Sheathed && !dead && p.Alive && Content.Stances.Piece(st, "handslot.l", loadout.Arms.Left) != null
                && !(bool)tree.Get(P_upperShot_active) && !(bool)tree.Get(P_fullShot_active);
            if (CarryLog && st != null && (int)(time * 10) != carryLogT) { carryLogT = (int)(time * 10); GD.Print($"carry t {time:0.00} stance {st.Id} sheathed {sheath.Sheathed} upper {(bool)tree.Get(P_upperShot_active)} full {(bool)tree.Get(P_fullShot_active)} on {stanceCarry.On} W {stanceCarry.W:0.00}"); }
        }
        // --hold CLIP@S: one of her clips held at S seconds, her pieces drawn, under the game's own light and
        // cameras (a judge's 1:1 frame of one pose; for pictures only). A town clip (*_town) is held with her pieces
        // sheathed, as the game plays it.
        // --clip-tour LIST: her own clips played once each, start to end, at normal speed and the game's own delta, her pieces drawn
        // as --hold draws them and the whole body keyed (no upper-only layering); for the armor-inside measure (WearInside).
        if (mine && TourList != null)
        {
            tree.Active = false;
            TourStep();
            goto carriedLight;
        }
        if (mine && Hold is { Length: 2 } hold)
        {
            tree.Active = false;
            if (!held) { held = true; view?.Sheathe(hold[0].EndsWith("_town") || SurvivorUnchained.Args.Has("sheathed")); } // (--sheathed: her pieces at their sockets, as in a safe place)
            if (grips)
            {
                slide = own.GripSlide(hold[0]); // the clip's grip, straight (no easing)
                tilt = own.GripTilt(hold[0]);
                view?.Slide("handslot.r", slide, tilt);
                slideL = own.GripSlideL(hold[0]);
                tiltL = own.GripTiltL(hold[0]);
                pocketL = tiltL != 0 ? 1 : 0;
                view?.Slide("handslot.l", slideL, tiltL, pocketL); // (a left tilt seats the piece on its pocket: TiltPocketL)
            }
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
            // (L1 lead 22, mirror) --hold-mirror: the held frame reflected across her own sagittal plane, left and right
            // swapped (PoseMirror), and the held piece moved into the hand that grips after the mirror. View only.
            if (HoldMirror)
            {
                if (mirror == null)
                {
                    mirror = new PoseMirror(sk);
                    GD.Print($"hold-mirror: {mirror.Paired} paired bones of {sk.GetBoneCount()}, plane normal {mirror.Normal}");
                }
                mirror.Apply();
                if (!mirror.Piece(P1Body.BoneName(sk, "hand_r"), P1Body.BoneName(sk, "hand_l")) && !mirrorSaid) { mirrorSaid = true; GD.Print("hold-mirror: no piece in her right hand to move"); }
            }
            // Her head carried up as play carries it (HeadLevel) through a swing and her idles and runs; a
            // whole-body clip (a fall, a roll, a flourish) keeps its own head, as play leaves it.
            string hn = hold[0];
            bool moveClip = hn.StartsWith("idle_") || hn.StartsWith("run_") || hn.StartsWith("sprint_") || hn.StartsWith("stop_") || hn.StartsWith("walk_");
            if (carriage != null) carriage.HeadLevel = upperOnly || moveClip || stance || HoldHead ? HeadLevel : 0;
            if (person.Pose != null) person.Pose.Native = 1;
            // (--close-turn R with it: turned from the close view's lens as its idle turns her, so a held pose can be
            // seen from her front; without it she keeps her heading, as before.)
            if (HoldTurn && Turned is float th) Rotation = new Vector3(0, th, 0);
            // (L1 lead 21, pose) --facing DEG with a hold: her heading on the held frame, set every frame, in the start facing's own
            // degrees (Game.cs: 0 south, toward the play camera; 90 east, screen-right), so a held pose can be staged to the play
            // camera whatever the shot did with her before. The close view's turn above wins when it is asked for.
            else if (HoldFacing is float hf) Rotation = new Vector3(0, hf, 0);
            // (L1 lead 21, stage) A held clip keeps her carried light: the branch returned here, so the light below never stepped (no energy,
            // cel_ember's reach 0) and a held frame lost her whole pool. Her pose is all that is held; the light runs as on any frame.
            goto carriedLight;
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
                if (DeathLog) GD.Print($"deathlog DIE f {Engine.GetProcessFrames()} t {time:0.000} clip {death} len {person.Anim.GetAnimation(death)?.Length ?? -1:0.000}");
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
        if (mine && DirOn) { pivot = backpedal = false; hipGoal = faceGoal = null; }
        aimFacingNow = AimLegs && aimHold > 0 && p.Leap == null && p.DashT <= 0;
        if (time < flareFaceUntil)
        {
            // (a Flare's clip holds her on its line until ClipFree; she turns onto it over the press's crossfade)
            float k = flareYawAt < 0 ? 1 : Mathf.Clamp((float)((time - flareYawAt) / FlareXfade), 0, 1);
            if (k >= 1) flareYawAt = -1;
            Rotation = new Vector3(0, Mathf.LerpAngle(flareYawFrom, flareFaceY, k * k * (3 - 2 * k)), 0);
        }
        else if (p.AttackAnim is { } aa && fightTime - aa.T < 0.35 && !mine) Rotation = new Vector3(0, (float)(Mathf.Pi / 2 - aa.Angle), 0);
        // (In the air she keeps the facing she sprang with: her velocity is stale there.)
        // Running, she faces where the stick asks, not where her eased velocity has got to (owner N27, "off when
        // turning": facing chased velocity, 217-267 ms to within 10 degrees and on a 180 she ran backwards for a
        // moment). Snapped as Hades and Diablo IV do: 67 ms to within 10 degrees on a 90, 100 ms on a 180.
        // --turn-old: the old chase (before/after pictures).
        else if (mine && DirOn && DirFace(p, (float)dt, (float)x, (float)z, sp)) { }
        else if (AimLegs && aimHold > 0 && p.Leap == null && p.DashT <= 0) Rotation = new Vector3(0, aimFace, 0);
        // (warden-turn) A blow struck standing or slow: her whole body to it on the eased turn, held while it lasts unless
        // she is off at a run; a blow behind her running: her hips toward it (hipGoal) while it lasts.
        else if (mine && faceGoal is float fg && aimHold > 0 && sp < 2f && p.Leap == null && p.DashT <= 0) TurnTo(fg, (float)dt, TurnMaxStanding, TurnEaseStanding);
        else if (mine && hipGoal is float hg && aimHold > 0 && p.Leap == null && p.DashT <= 0) TurnTo(hg, (float)dt, backpedal ? BackYawMax(hg) : HipRate, TurnEase);
        else if ((sp > 0.4f || PivotHeld(p.StickX, p.StickZ)) && p.Leap == null)
        {
            bool stick = !TurnOld && p.StickX * p.StickX + p.StickZ * p.StickZ > 0.01;
            float want = stick ? Mathf.Atan2((float)p.StickX, (float)p.StickZ) : Mathf.Atan2((float)p.Vx, (float)p.Vz);
            // (warden-turn) Eased and rate-limited: at most TurnMax a second (35 deg a 30 fps frame), a 180 at a run
            // (a pivot) at TurnPivot. --turn-snap: the 4 Nov snap (FaceRate 36/s put 126 deg of a 180 in one frame).
            if (mine && !TurnOld && !TurnSnap)
            {
                float off = Mathf.Abs(Mathf.Wrap(want - Rotation.Y, -Mathf.Pi, Mathf.Pi));
                // (t4) Out of a backpedal she turns back onto her travel at the pivot's rate, without its plan (she is not running into it).
                if (backpedal && off < Mathf.DegToRad(10)) backpedal = false;
                if (!pivot && !backpedal && off > Mathf.DegToRad(120) && speed > 2.5f) { pivot = true; PivotStart(); }
                // (turning r3) her yaw held back while the pivot foot comes down
                TurnTo(want, (float)dt, backpedal ? BackYawMax(want) : pivot ? (pivotSeg == 1 ? PivotBrakeYaw : TurnPivot) : TurnMax, pivotSeg == 2 ? PivotEase : TurnEase);
                if (pivot && Mathf.Abs(Mathf.Wrap(want - Rotation.Y, -Mathf.Pi, Mathf.Pi)) < Mathf.DegToRad(10)) pivot = false;
            }
            else Rotation = new Vector3(0, Mathf.LerpAngle(Rotation.Y, want, 1 - Mathf.Exp(-(TurnOld ? 14 : FaceRate) * (float)dt)), 0);
        }
        if (aimHold <= 0) { faceGoal = null; hipGoal = null; }
        if (sp <= 0.4f && !PivotHeld(p.StickX, p.StickZ)) pivot = backpedal = false;
        turnedLast = turning; turning = false;
        plantYawStep = Mathf.RadToDeg(Mathf.Abs(Mathf.Wrap(Rotation.Y - plantYawPrev, -Mathf.Pi, Mathf.Pi))); plantYawPrev = Rotation.Y;
        // Turned to the view while a panel frames her (FollowCamera.ScreenFrame), standing.
        if (Turned is float tw && sp < 0.4f && p.AttackAnim == null && time >= flareFaceUntil)
            Rotation = new Vector3(0, Mathf.LerpAngle(Rotation.Y, tw, 1 - Mathf.Exp(-4 * (float)dt)), 0);
        Watching(sp < 0.4f && p.AttackAnim == null);
        StepKnock(p.DashT);
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
        if (p.Leap == null) leapSeen = null;
        // A new leap by identity, not by a render-delta window (above 120 FPS the first sim tick had aged it past) (SU-068).
        if (p.Leap is { } l2 && !ReferenceEquals(l2, leapSeen))
        {
            leapSeen = l2;
            bool vault = l2.Kind == Content.AbilityKind.Vault;
            float dx = (float)(l2.X1 - l2.X0), dz = (float)(l2.Z1 - l2.Z0);
            // A vault against the way she faces (standing, she springs back
            // from her facing) is a spring backwards, eyes on what she
            // leaves; any other leap faces the way it goes.
            bool back = vault && dx * Mathf.Sin(Rotation.Y) + dz * Mathf.Cos(Rotation.Y) < 0;
            if (dx * dx + dz * dz > 0.01f) Rotation = new Vector3(0, back ? Mathf.Atan2(-dx, -dz) : Mathf.Atan2(dx, dz), 0);
            aim = 0;
            // (a calling's own leap, landed into its idle: leap_warden ends on Prowl's f0; fitted to the air the same way)
            if (!vault && FullHer($"leap_{person.Calling}", 1, false)) P7LeapFit(l2.Dur);
            else if (!(back && FullHer("vault_back", 1, false)))
            {
                var jump = vault ? "Jump_Start" : "Jump_Full_Short";
                bool native = own.Owns(People.Clip(person, jump));
                Full(jump, native ? 1.0 : vault ? 1.8 : 1.3);
                // (P7: hers fitted to the air, the flight over the sim's, not the art's old 0.42 s)
                if (native && !vault) P7LeapFit(l2.Dur);
                if (SurvivorUnchained.Args.Has("clip") && person.Anim.HasAnimation(full.Animation)) GD.Print($"p7 jump clip {full.Animation} len {person.Anim.GetAnimation(full.Animation).Length:0.00} speed {(native ? 1.0 : vault ? 1.8 : 1.3)} air {l2.Dur:0.00}");
            }
            // Once down, the landing gives way as soon as she moves on.
            artTail = time + l2.Dur + 0.1;
        }
        ArtTail(sp);
        FlareClipWatch(); FlareGripShow();
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
        P7Step(b, dt, sp);
        // Weapon swings: the blade drives the arm. Hers alternate as the
        // arcs do (the first from her left), the wide arcs her heavy cut.
        if (p.AttackAnim is { } a && a.T != lastAttack && !KnockSkip(a.T))
        {
            lastAttack = a.T;
            var swings = mine ? HerClips.Swings(person.Kind) : System.Array.Empty<string>();
            // (campaign: the sim names the clip and its rate, from the press, so her contact and the hit meet: Sim/Contact.cs)
            bool played = mine && a.Clip != null && UpperHer(a.Clip, a.Rate);
            if (!played && swings.Length > 0)
                played = a.Heavy ? UpperHer(HerClips.Heavy(person.Kind), 1.5) : UpperHer(swings[swing % swings.Length], 1.6);
            if (!played)
            {
                var clip = a.Heavy ? loadout.Arms.Heavy : loadout.Arms.Attack[swing % loadout.Arms.Attack.Length];
                Upper(clip, 1.6);
            }
            swing++;
            if (mine) Strike(a.Angle);
            if (mine && played && !AimLegs && !TurnSnap && !CoilOff) CoilStart(fullStart == time);
            if (mine && SurvivorUnchained.Play.TurnRun.Start >= 0)
                GD.Print(System.FormattableString.Invariant($"STRIKE {b.Time - SurvivorUnchained.Play.TurnRun.Start:0.0000} aim {Mathf.RadToDeg(aimFace):0.0} face {Mathf.RadToDeg(Rotation.Y):0.0} sp {speed:0.00} clip {(fullStart == time ? fullClip : upperClip)} full {fullStart == time} waist {aim:0.0} hips {(hipGoal is float h2 ? Mathf.RadToDeg(h2) : float.NaN):0.0}"));
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
        // The run blend's speed after her ground speed: quick enough that a 180's plant shows in her legs
        // (at 10 a second they ran on through the stop, 3.6 m/s off her ground speed; at 40, 1.4).
        speed = Mathf.Lerp(speed, sp, 1 - Mathf.Exp(-(TurnOld ? 10 : BlendRate) * (float)dt));
        // (turning r2) Through a 180's pivot her legs keep the run (the sim's speed passes through zero as it reverses: at 40 a
        // second the blend followed it to her stand for a frame, upright with her feet together, then back to the run).
        if (mine && pivot && !TurnOld && !TurnSnap) speed = Mathf.Max(speed, PivotFloor);
        velX = (float)p.Vx; velZ = (float)p.Vz;
        ActWalkVel(ref sp);
        if (mine && !ActLive && ActWalk == null) Rest(b, dt, sp);
        if (mine) Carry((float)dt, sp);
        if (mine) CoilStep();
        if (mine && HeldLogOn) view?.HeldLog(GetViewport()?.GetCamera3D());
        if (mine) ActApply();
        if (mine) SurvivorUnchained.Play.TurnRun.Log(b.Time, p.StickX, p.StickZ, p.Vx, p.Vz, Rotation.Y, carriage?.Bank ?? 0, speed, p.X, p.Z);
        if (mine && (SurvivorUnchained.Play.TurnRun.Start >= 0 || SurvivorUnchained.Play.DirRun.Start >= 0 || TurnLog)) TurnLog2(b.Time - System.Math.Max(0, System.Math.Max(SurvivorUnchained.Play.TurnRun.Start, SurvivorUnchained.Play.DirRun.Start)));
        else tree.Set(BlendPosition, speed);
        carriedLight:
        // The carried light: steadier at full health, guttering when hurt.
        double hp = p.Hp / b.MaxHp;
        flare = Mathf.Max(0, flare - dt * 0.8);
        double flicker = Mathf.Sin((float)(time * 7.3)) * 0.25 + Mathf.Sin((float)(time * 17.1)) * 0.15 + (hp < 0.35 ? Mathf.Sin((float)(time * 31)) * 0.6 : 0);
        lamp = Mathf.Lerp(lamp, LampScale, 1 - Mathf.Exp(-3 * (float)dt));
        // (Rendering 1: the flare's burst keeps the gain it was tuned under: Low Ford's ember went 2.2 to 8 for its pool, and at 8
        // a level-up's flash washed the frame to p50 45. --ember-flare-cap G.)
        Light.LightEnergy = (float)(((LightBase * (0.7 + 0.3 * hp) + flicker) * Atmosphere.EmberGain * EmberK * FlarePool + flare * 20 * Mathf.Min(Atmosphere.EmberGain, EmberFlareCap)) / Mathf.Pi) * lamp * PoolScale * PoolDen;
        // A lantern carries further; under the Oath of the Moonless, not far at all.
        Light.OmniRange = (float)((11 + flare * 6) * b.Stats.Get(Stat.LightRadius) * b.Rules.Light) * EmberRangeK * Atmosphere.EmberReach;
        Light.LightColor = EmberArg ?? Atmosphere.EmberColor ?? EmberOwn;   // (H2 R1: the air's, the arena's paler gold)
        Light.OmniAttenuation = EmberAtt;
        Light.LightCullMask = (LampOffHer ? 0xFFFFFu & ~2u & ~CrowdLayer & ~HerLayers & ~Brush.MaskLayer : FolkK > 0 ? 0xFFFFFu & ~2u & ~HerLayers & ~Brush.MaskLayer & (EmberCrowd ? 0xFFFFFu : ~CrowdLayer) : 0xFFFFFu) & (CrowdOmni ? 0xFFFFFu : ~CrowdLayer);
        // (the close view by night keeps its own: her lamp off her and off people, as before)
        FolkLight.Visible = !LampOffHer && FolkK > 0;
        FolkLight.LightEnergy = Light.LightEnergy / PoolDen * FolkK * FolkScale;   // (the den's pool energy is the ground's only)
        FolkLight.OmniRange = Light.OmniRange * FolkRange;
        FolkLight.OmniAttenuation = FolkAtt;
        // (before the relayering below: in the close view her meshes leave people's layer, and the rim's HerLayer goes first)
        if (mine) RimStep((float)dt, (float)((LightBase * (0.7 + 0.3 * hp) + flicker) / LightBase));
        // Her weapon and shield are the world's (layer 1), so the pool lit them: at the pool's hip height her shield's face
        // went white. Off the pool and onto people's layer while the folk light lights her (looked over twice a second, a new
        // weapon or a sheathed one included); back on the world's for the close view's own relayering (Relayer).
        if (FolkK > 0 && !OwnLayer && !LampOffHer) { if ((offPoolT -= dt) <= 0) { offPoolT = 0.5; OffPool(this, offPool, Reflections); } }
        else if (offPool.Count > 0)
        {
            foreach (var g in offPool) if (IsInstanceValid(g) && (g.Layers & 2u) != 0) g.Layers = (g.Layers & ~2u) | 1u;
            offPool.Clear();
        }
        // (Every frame while on: her level of detail and her wear make meshes of their own on layer 2.)
        if (OwnLayer || ownShown) { Relayer(this, OwnLayer, person.Hair); ownShown = OwnLayer; }
        // (L1 lead 19, HER2) the rig's hero_pool: her fire's foot beside her; (0, 0.4) in her own frame without the row.
        // (L1 lead 21, FOOT) With the row the foot is a point on the GROUND of the view: her ground position + (dx along
        // screen-right, dz along screen-down), whatever her heading, clip or hold (it was local to her, so the pool, her cast and
        // her shade side swung round her as she turned). The light node carries the point: cel_ember, her cast and the casts'
        // report below read Light.GlobalPosition, and the hero's shade side is told the same direction (Atmosphere.HeroFootWorld).
        if (Atmosphere.HeroFootRig)
        {
            var right = GetViewport()?.GetCamera3D() is { } vc ? vc.GlobalBasis.X : Vector3.Right;
            right = new Vector3(right.X, 0, right.Z);
            right = right.LengthSquared() > 1e-6f ? right.Normalized() : Vector3.Right;
            var down = right.Cross(Vector3.Up);   // along the ground toward the camera = down the screen (+Z at yaw 0)
            var foot = right * Atmosphere.HeroFoot.X + down * Atmosphere.HeroFoot.Y;
            var own = GlobalBasis.Inverse() * foot;
            Light.Position = new Vector3(own.X, EmberHNow, own.Z);
            if (mine) Atmosphere.HeroFootWorld(new Vector2(foot.X, foot.Z));
        }
        else Light.Position = new Vector3(Atmosphere.HeroFoot.X, EmberHNow, Atmosphere.HeroFoot.Y);
        // Her lamp on the crowd by night, in its own paint (Atmosphere.CrowdFill, vat.gdshaderinc): from over her, with the pool's flicker.
        if (mine)
        {
            float ce = !LampOffHer && Visible && Atmosphere.CrowdFill > 0 ? Light.LightEnergy / PoolDen * Atmosphere.CrowdFill * CrowdEmberK : 0;
            var at = GlobalPosition + new Vector3(0, CrowdEmberH, 0);
            RenderingServer.GlobalShaderParameterSet(Sn.Of("crowd_ember"), new Vector4(at.X, at.Y, at.Z, ce));
            // (L1 lead 19, SH2) She stands on her own short shadow: the light is over her, so the cast's rule gives next to
            // nothing; a fixed short trail from her feet, away from the light's foot (the light sits a little toward the
            // camera), a little wider than her stance. Its tone is the rig's (foe_moon value 8), the shape the shader's.
            if (herCast != null)
            {
                var lf = Light.GlobalPosition; var me = GlobalPosition;
                FireCast.Set(herCast.Multimesh, 0, me, HerCastTall, HerCastWide, ce > 0 ? 1 : 0, HerCastLong, new Vector2(me.X - lf.X, me.Z - lf.Z));
                if (FireCast.Count) FireCast.Report(lf);
            }
            herShadow?.Place(GlobalPosition, Visible && IsVisibleInTree());
            if (herShadow != null) HerSteel.Wear(view?.HeldMount("handslot.r"), HeroDen.SteelOn);   // (demo-look r2 her: her blade as painted steel in the den)
            var lc = Light.LightColor.SrgbToLinear();
            RenderingServer.GlobalShaderParameterSet(Sn.Of("crowd_lamp"), new Vector4(lc.R, lc.G, lc.B, CrowdEmberIn));
            // (L1 W2) Her light's point and reach for the cel model, where the moon gives way to her pool (cel.gdshaderinc cel_ember;
            // the rig's ember_give says how much): none while her lamp is out or hidden.
            var lp = Light.GlobalPosition;
            RenderingServer.GlobalShaderParameterSet(Sn.Of("cel_ember"), new Vector4(lp.X, lp.Y, lp.Z, Visible && Light.Visible && Light.LightEnergy > 0 ? Light.OmniRange : 0));
            if (PoolLog && Mathf.Abs(Light.OmniRange - poolLogged) > 0.25f) { poolLogged = Light.OmniRange; GD.Print($"pool: her light's reach {Light.OmniRange:0.00} m, energy {Light.LightEnergy:0.00}"); }
            // (L1 lead 8, S2b) her light's color (linear, its largest channel 1) and fall (OmniAttenuation), so the cel model knows her
            // light among the others and paints its pool (cel.gdshaderinc cel_pool_band).
            float lm = Mathf.Max(lc.R, Mathf.Max(lc.G, Mathf.Max(lc.B, 1e-4f)));
            RenderingServer.GlobalShaderParameterSet(Sn.Of("cel_pool"), new Vector4(lc.R / lm, lc.G / lm, lc.B / lm, Light.OmniAttenuation));
        }
        // Unseen: a ghost, flickering.
        Visible = !Hidden && !(p.InvisibleT > 0 && (int)(time * 12) % 3 == 0);
    }

    /// <summary>True when any of a mesh's surfaces is metal: her outfit's metal keys (People.OutfitMaterials, meta "kind" 1,
    /// heroine_outfit_metal.gdshader), or a plain material at metallic 0.5 or more. Only these take the moon rim's gear twin:
    /// with all her gear on it her leather (bandeau, bracers, belt) read as lavender chrome by night (judge J2, face 36).</summary>
    /// <summary>Metal (her weapon, armor, buckles): what goes on HerGearLayer (GameCinemaHer too).</summary>
    internal static bool IsMetalPart(GeometryInstance3D g) => IsMetal(g);
    static bool IsMetal(GeometryInstance3D g)
    {
        if (g is not MeshInstance3D m || m.Mesh == null) return false;
        for (int s = 0; s < m.Mesh.GetSurfaceCount(); s++)
            switch (m.GetActiveMaterial(s))
            {
                case ShaderMaterial sm when sm.HasMeta(Sn.Of("kind")) && (int)sm.GetMeta(Sn.Of("kind")) == 1 || sm.Shader?.ResourcePath.Contains("metal") == true: return true;
                case BaseMaterial3D bm when bm.Metallic >= 0.5f: return true;
            }
        return false;
    }

    readonly List<GeometryInstance3D> offPool = new();
    double offPoolT;

    // (lane E lead 3, row 1) her rim light in the den (RimLight)
    readonly List<GeometryInstance3D> rimTagged = new();
    readonly List<SpotLight3D> denSpots = new();
    double rimTagT, denSpotsT, rimLogT;
    float rimGate;
    bool rimSeen;
    /// <summary>--her-rim-log: the den's light at her feet, the rim's gate and energy, once a second.</summary>
    static readonly bool RimLog = Args.Has("her-rim-log");
    /// <summary>The gate's smoothing, s (exponential): a stride in or out of a shaft's pool eases the rim, no pop.</summary>
    const float RimTau = 0.3f;

    /// <summary>Her rim light each frame (RimLight): k her ember's own flicker and health (1 steady at full health). Off (and
    /// her meshes back on people's layer alone) out of the den, in the close view (OwnLayer), with her lamp off her or hidden.
    /// Its energy: the row's (value 47) times the gate, 1 where the den's own light at her feet (DenLightAt) is at or under
    /// value 54 and 0 at or over value 55 (smoothstep between), eased over RimTau, times k and her lamp's share.</summary>
    void RimStep(float dt, float k)
    {
        if (RimLight == null) return;
        bool on = HeroDen.RimEnergy > 0 && !OwnLayer && !LampOffHer && Visible;
        if (!on)
        {
            RimLight.Visible = false;
            foreach (var g in rimTagged) if (IsInstanceValid(g)) g.Layers &= ~HerLayer;
            rimTagged.Clear();
            rimSeen = false;
            return;
        }
        // her meshes on HerLayer beside people's, so the rim lights her and no one else (four times a second: her level of
        // detail and her wear make meshes of their own on people's layer)
        if ((rimTagT -= dt) <= 0) { rimTagT = 0.25; RimTagWalk(this); }
        float e = DenLightAt(GlobalPosition);
        float want = HeroDen.RimHi > HeroDen.RimLo ? 1 - Mathf.SmoothStep(HeroDen.RimLo, HeroDen.RimHi, e) : e <= HeroDen.RimLo ? 1 : 0;
        rimGate = rimSeen ? Mathf.Lerp(rimGate, want, 1 - Mathf.Exp(-dt / RimTau)) : want;
        rimSeen = true;
        float energy = HeroDen.RimEnergy * rimGate * k * lamp;
        RimLight.LightEnergy = energy;
        RimLight.Visible = energy > 1e-4f;
        RimLight.LightColor = HeroDen.RimColor;
        RimLight.OmniRange = HeroDen.RimRange;
        RimLight.OmniAttenuation = HeroDen.RimAtt;
        // low behind her, away from the camera along the ground (screen-up), whatever her heading
        var right = GetViewport()?.GetCamera3D() is { } vc ? vc.GlobalBasis.X : Vector3.Right;
        right = new Vector3(right.X, 0, right.Z);
        right = right.LengthSquared() > 1e-6f ? right.Normalized() : Vector3.Right;
        var toCam = right.Cross(Vector3.Up);
        var own = GlobalBasis.Inverse() * (-toCam * HeroDen.RimBack);
        RimLight.Position = new Vector3(own.X, HeroDen.RimH, own.Z);
        if (RimLog && (rimLogT -= dt) <= 0)
        {
            rimLogT = 1;
            GD.Print($"her rim: den light at her feet {e:0.000} ({denSpots.Count} spots), gate {want:0.00} eased {rimGate:0.00}, energy {energy:0.00}, {rimTagged.Count} meshes on HerLayer");
        }
    }

    void RimTagWalk(Node n)
    {
        for (int ci = 0, cn = n.GetChildCount(); ci < cn; ci++)   // (lane K, 19 Nov: GetChildren made a Godot Array each call that outlived its first collection)
        {
            var c = n.GetChild(ci);
            if (c == Reflections || c == herShadow || c == herCast) continue;
            if (c is GeometryInstance3D g && (g.Layers & 2u) != 0 && (g.Layers & HerLayers) == 0) { g.Layers |= HerLayer; rimTagged.Add(g); }
            RimTagWalk(c);
        }
    }

    /// <summary>The den's own light on the floor at p: the irradiance of View/DungeonLight's spots (the shafts and the room
    /// washes), by Godot's own spot falloff on a floor facing up, times their colour's luminance. The key and the fill are the
    /// same everywhere in the den and are left out, so this is what tells a room's lit middle from its dark edges, the bends
    /// and the ground under the banks' roots (0 where no spot reaches). The spots are looked up once, again every 2 s while none.</summary>
    float DenLightAt(Vector3 p)
    {
        denSpots.RemoveAll(s => !IsInstanceValid(s));
        if (denSpots.Count == 0 && (denSpotsT -= GetProcessDeltaTime()) <= 0)
        {
            denSpotsT = 2;
            if (GetTree()?.Root.FindChild("DungeonLight", true, false) is { } dl)
                foreach (var c in dl.GetChildren()) if (c is SpotLight3D s) denSpots.Add(s);
        }
        float e = 0;
        foreach (var s in denSpots)
        {
            if (!s.IsVisibleInTree()) continue;
            var rel = s.GlobalPosition - p;
            float d = rel.Length();
            if (d < 1e-3f || d >= s.SpotRange) continue;
            float nd = d / s.SpotRange; nd *= nd; nd *= nd; nd = Mathf.Max(1 - nd, 0); nd *= nd;
            float cc = Mathf.Cos(Mathf.DegToRad(s.SpotAngle));
            float sc = Mathf.Max((-rel / d).Dot((-s.GlobalBasis.Z).Normalized()), cc);
            float cone = 1 - Mathf.Pow(Mathf.Max(1e-4f, (1 - sc) / Mathf.Max(1 - cc, 1e-4f)), s.SpotAngleAttenuation);
            var c = s.LightColor;
            e += s.LightEnergy * nd * Mathf.Pow(Mathf.Max(d, 1e-4f), -s.SpotAttenuation) * Mathf.Max(cone, 0) * Mathf.Max(0, rel.Y / d) * (0.2126f * c.R + 0.7152f * c.G + 0.0722f * c.B);
        }
        return e;
    }

    /// <summary>Her meshes on the world's layer alone (her weapon, her shield) moved to people's, off her ember's pool light.</summary>
    static void OffPool(Node n, List<GeometryInstance3D> moved, Node skip)
    {
        for (int ci = 0, cn = n.GetChildCount(); ci < cn; ci++)   // (lane K, 19 Nov: as RimTagWalk)
        {
            var c = n.GetChild(ci);
            if (c == skip) continue;
            if (c is GeometryInstance3D g && g.Layers == 1u) { g.Layers = 2u; moved.Add(g); }
            OffPool(c, moved, skip);
        }
    }

    static void Relayer(Node n, bool own, List<MeshInstance3D> hair)
    {
        for (int ci = 0, cn = n.GetChildCount(); ci < cn; ci++)   // (lane K, 19 Nov: as RimTagWalk)
        {
            var c = n.GetChild(ci);
            if (c is GeometryInstance3D g)
            {
                uint mine = !RimHair && g is MeshInstance3D mi && hair.Contains(mi) ? HerHairLayer
                    : GearOwn && own && (g.Layers & 2u) != 0 && IsMetal(g) ? HerGearLayer : HerLayer;
                // (her weapon is the world's (layer 1), not people's: it keeps that and takes her gear's layer too, so her own
                // lamps (the night key, the moon rim's gear twin) reach it; without them it was flat black by night, judge J1)
                // Rendering 3 (judge j2 C1/D1, "the shield face and the upper blade as bright as her face"): in the close view they
                // leave the world's layer for hers alone (HerGearLayer), out of the close view's ground spot and the world's fire at
                // full, lit as she is (the key, its fill, the fire's share on her, the moon rim's gear twin); and the blade takes
                // its close-view finish (WeaponClose). --close-weapon-world: on the world's layer too, as round 2.
                if (GearOwn && own && (g.Layers & 1u) != 0 && (g.Layers & 2u) == 0)
                {
                    g.Layers = WeaponWorld ? g.Layers | HerGearLayer : (g.Layers & ~1u) | HerGearLayer;
                    if (!WeaponWorld) g.SetMeta(WorldMeta, true);
                    WeaponClose(g, true);
                }
                else if (GearOwn && g.HasMeta(WorldMeta) && (g.Layers & 2u) == 0)
                {
                    if (!own) { g.Layers = (g.Layers & ~HerGearLayer) | 1u; g.RemoveMeta(WorldMeta); WeaponClose(g, false); }
                }
                else if (GearOwn && (g.Layers & 1u) != 0 && (g.Layers & 2u) == 0)
                { g.Layers = own ? g.Layers | HerGearLayer : g.Layers & ~HerGearLayer; if (!own) WeaponClose(g, false); }
                else if (own && (g.Layers & 2u) != 0) g.Layers = (g.Layers & ~2u) | mine;
                else if (!own && (g.Layers & HerLayers) != 0) g.Layers = (g.Layers & ~HerLayers) | 2u;
            }
            Relayer(c, own, hair);
        }
    }

    static readonly StringName WorldMeta = "su_close_world", CloseMatMeta = "su_close_mat";
    static readonly bool WeaponWorld = Args.Has("close-weapon-world");
    // --close-weapon-rough R (0: as built): the close view's roughness floor on her weapon and shield; --close-weapon-sheen K:
    // (Rendering 3: the floor is off by default. At the judge's 0.35 the blade's polished face spread the sky's bright horizon
    // into a broad band, the upper blade's p99.9 233 of 255 against 198 without, lfclose_00.)
    // the metal's sheen there, its albedo's share (a metal reflects its albedo: the sky's, the moon's and the lamps' sheen alike)
    // (Rendering 3, judge j2 D1: 0.35 and 50%, the blade's pink-white glint).
    static readonly float WeaponRough = Args.Num("close-weapon-rough", 0f), WeaponSky = Args.Num("close-weapon-sheen", 0.5f);

    static readonly Dictionary<(ulong, int, float, float, int, float), ImageTexture> remade = new();
    /// <summary>A texture made again (once, kept): channel ch (0-3 r,g,b,a; 4 grey: all three) at least lo and times k,
    /// and channel ch2 (-1 none) times k2.</summary>
    static ImageTexture Remade(Texture2D t, int ch, float lo, float k, int ch2, float k2)
    {
        var key = (t.GetRid().Id, ch, lo, k, ch2, k2);
        if (remade.TryGetValue(key, out var done)) return done;
        var im = t.GetImage();
        if (im.IsCompressed()) im.Decompress();
        im.Convert(Image.Format.Rgba8);
        var px = im.GetData();
        static void Do(byte[] px, int c, float lo, float k)
        {
            if (c < 0) return;
            for (int i = 0; i < px.Length; i += 4)
                for (int j = c == 4 ? 0 : c; j <= (c == 4 ? 2 : c); j++)
                    px[i + j] = (byte)Mathf.Clamp(Mathf.RoundToInt(Mathf.Max(px[i + j] / 255f, lo) * k * 255), 0, 255);
        }
        Do(px, ch, lo, k);
        if (ch2 != ch) Do(px, ch2, 0, k2);
        else if (ch2 >= 0) Do(px, ch2, 0, k2);
        var o = Image.CreateFromData(im.GetWidth(), im.GetHeight(), false, Image.Format.Rgba8, px);
        o.GenerateMipmaps();
        return remade[key] = ImageTexture.CreateFromImage(o);
    }

    /// <summary>Her weapon's and shield's close-view finish (on) or as built (off): each plain material (StandardMaterial3D)
    /// a copy with its roughness at least WeaponRough and its metal's sheen at WeaponSky (its albedo).</summary>
    static void WeaponClose(GeometryInstance3D g, bool on)
    {
        if (g is not MeshInstance3D m || m.Mesh == null) return;
        if (!on)
        {
            if (!m.HasMeta(CloseMatMeta)) return;
            for (int s = 0; s < m.Mesh.GetSurfaceCount(); s++) m.SetSurfaceOverrideMaterial(s, null);
            m.RemoveMeta(CloseMatMeta);
            return;
        }
        if (m.HasMeta(CloseMatMeta) || (WeaponRough <= 0 && WeaponSky >= 1)) return;
        for (int s = 0; s < m.Mesh.GetSurfaceCount(); s++)
        {
            if (m.GetSurfaceOverrideMaterial(s) != null || m.Mesh.SurfaceGetMaterial(s) is not BaseMaterial3D bm) continue;
            var c = (BaseMaterial3D)bm.Duplicate();
            if (WeaponRough > 0 && c.Roughness < WeaponRough && c.RoughnessTexture == null) c.Roughness = WeaponRough;
            // The roughness texture made again (an ORM's channel), at least WeaponRough of the material's scale (texture x Roughness).
            if (c.RoughnessTexture is Texture2D rtx && WeaponRough > 0 && c.Roughness > 0)
            {
                var nt = Remade(rtx, (int)c.RoughnessTextureChannel, Mathf.Min(1, WeaponRough / c.Roughness), 1, -1, 1);
                if (c.AOTexture == rtx) c.AOTexture = nt;   // (the same ORM: its occlusion channel as it was)
                c.RoughnessTexture = nt;
            }
            // The metal's sheen (sky, moon and lamps alike): a metal's reflection is its albedo, so its albedo times WeaponSky.
            if (WeaponSky < 1 && c.Metallic > 0)
            {
                float k = Mathf.Lerp(1, WeaponSky, c.Metallic);
                var lin = c.AlbedoColor.SrgbToLinear();
                c.AlbedoColor = new Color(lin.R * k, lin.G * k, lin.B * k, lin.A).LinearToSrgb();
            }
            if (Args.Has("camlog")) GD.Print($"weaponclose {m.Name} s{s} metal={bm.Metallic:F2} rough={bm.Roughness:F2} rtex={bm.RoughnessTexture != null} ao={bm.AOEnabled} aoSame={bm.AOTexture == bm.RoughnessTexture}");
            m.SetSurfaceOverrideMaterial(s, c);
        }
        m.SetMeta(CloseMatMeta, true);
    }

    /// <summary>(idleAt) The idle clip's length (s), 0 with none.</summary>
    double IdleLen()
    {
        // (the Animation fetched once per name, while it is there to fetch: a missing one is asked for each frame, as before)
        if (idleSn == null || string.IsNullOrEmpty(idleAn)) return 0;
        if (idleAnimRes == null) { if (!tree.HasAnimation(idleSn)) return 0; idleAnimRes = tree.GetAnimation(idleSn); }
        return idleAnimRes.Length;
    }

    /// <summary>(idleAt) A whole-body shot (a stop, a skill) ends on the idle's frame 0: the idle set to come round to it
    /// as the shot ends. Set 0.1 s in (IdleSyncDue), under the shot, not on its 0.05 s fade in (the idle jumping under
    /// that would show). A hold (P7's) leaves it early: the fade then lands off phase, as before. The break is the idle's
    /// own frames from its 0 (the break's gate in Rest): left as it is.</summary>
    void IdleSyncLater(string clip, double speed)
    {
        var n = own.Prefix + clip;
        syncAt = -1;
        if (clip.EndsWith("_break") || !tree.HasAnimation(n) || tree.GetAnimation(n).LoopMode != Animation.LoopModeEnum.None) return;
        syncAt = time + 0.1; syncLeft = tree.GetAnimation(n).Length / System.Math.Max(0.05, speed) - 0.1;
    }

    double syncAt = -1, syncLeft;

    /// <summary>The shot set to sync runs `total` seconds from now, not its length at one pace (P7's driven leap).</summary>
    void IdleSyncOver(double total) { if (syncAt >= 0) syncLeft = total - 0.1; }

    void IdleSyncDue(double il)
    {
        if (syncAt < 0 || time < syncAt) return;
        idleAt = ((il - syncLeft) % il + il) % il;
        syncAt = -1;
    }

    /// <summary>When nothing is near: a breath caught after a long run, and
    /// now and then, standing, her calling's fidget. Either gives way the
    /// moment she moves.</summary>
    void Rest(Battle b, double dt, float sp)
    {
        var p = b.Player;
        if (fullSoft && sp > 0.6 && (bool)tree.Get(P_fullShot_active))
        {
            tree.Set(P_fullShot_request, (int)AnimationNodeOneShot.OneShotRequest.FadeOut);
            fullSoft = false; fullGaveWay = true;
        }
        if (sp > 3) { runT += dt; stillT = 0; ranFor = runT; return; }
        if (sp > 0.3 || (pivot && PivotHeld(p.StickX, p.StickZ))) { stillT = 0; return; }   // (a 180's reversal is not a stop)
        // Pulling up out of a run: onto whichever foot was coming down.
        if (runT > 0.4 && !(bool)tree.Get(P_fullShot_active))
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
        // (idleAt) the break begins where the idle's loop does (it is the idle's own first frames, laid over)
        if (stillT >= breakAt && (move2D || IdleLen() <= 0 || idleAt < 1.5 * dt))
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
        float spd = speed;
        if (AimLegs)
        {
            // Her velocity in her facing's frame (Move2D.Local: x right, y forward), eased as the ground speed is.
            var lv = SurvivorUnchained.Play.Move2D.Local(velX, velZ, Rotation.Y);
            var feed = new Vector2(lv.X, lv.Y);
            // The lower-body turn (no side clips): aim-facing, the legs walk toward her travel (the pelvis yawed by lowerDelta), the node
            // fed the forward or back walk at the speed along the turned legs' line. Otherwise delta eases out.
            float dTarget = 0;
            bool aimFacing = !move2DSides && (ActWalk != null || aimFacingNow);
            float vs = feed.Length();
            float fyT = speed;
            if (aimFacing)
            {
                fyT = 0;
                if (vs > SurvivorUnchained.Play.LowerTurn.IdleSpeed)
                {
                    double th = Mathf.RadToDeg(Mathf.Atan2(-feed.X, feed.Y));
                    var lt = SurvivorUnchained.Play.LowerTurn.Solve(th, vs, lowerBack);
                    lowerBack = lt.Back; dTarget = (float)lt.Delta; feed = new Vector2(0, (float)lt.FeedY);
                    fyT = feed.Y;
                }
            }
            else if (!move2DSides && aimHold > 0) feed.X = 0;
            lowerDelta = (float)SurvivorUnchained.Play.LowerTurn.Ease(lowerDelta, dTarget, dt);
            if (person.Turn != null) person.Turn.Delta = lowerDelta;
            float k = 1 - Mathf.Exp(-(TurnOld ? 10 : BlendRate) * dt);
            if (move2D)
            {
                move2dPos = move2dPos.Lerp(feed, k);
                tree.Set(BlendPosition, move2dPos);
            }
            else
            {
                // The forward graph walks the forward part of her line; the back walk comes in over it as she backpedals.
                backFy = aimFacing ? Mathf.Lerp(backFy, fyT, k) : fyT;
                spd = Mathf.Max(backFy, 0);
                backBlendNow = Mathf.Lerp(backBlendNow, backFy < -0.05f ? 1f : 0f, 1 - Mathf.Exp(-dt / 0.15f));
                tree.Set(P_move_backBlend_blend_amount, backBlendNow);
                tree.Set(P_move_backScale_scale, SurvivorUnchained.Play.LowerTurn.BackScale(backFy, backVb));
                move2dPos = new Vector2(backBlendNow, backFy);
            }
        }
        float natural0 = Mathf.Lerp(runSpeed, sprintSpeed, sprintSpeed > runSpeed ? Mathf.SmoothStep(runSpeed * 1.1f, sprintSpeed * 0.95f, spd) : 0);
        var (wWalk, w) = Stride.Weights(spd, walkSpeed, natural0, hasWalk);
        // (t4) A backpedal steps on her walk played backwards, not her run: the run's flight held a wide split for 5-7 frames
        // while she slid back (t4b). Eased in and out at BackBlend/s; its stride covers her ground at any pace (period below).
        float w0 = w;
        bool backNow = backpedal && hasWalk && !BackRun && velX * velX + velZ * velZ > 0.16f
            && Mathf.Abs(Mathf.Wrap(Rotation.Y - Mathf.Atan2(velX, velZ), -Mathf.Pi, Mathf.Pi)) > Mathf.Pi / 2;
        backW = Mathf.Lerp(backW, backNow ? 1f : 0f, 1 - Mathf.Exp(-BackBlend * dt));
        // (round 4: judge r3 "a scurry, ~7.5 steps/s, 25-35% skate") the run mixed in at BackMix lengthens her backward step
        w = Mathf.Lerp(w, BackMix, backW);
        // (lead r12, judge r11) B has no arms' copy (the owner, 5 Nov: B's holds are clip data), so her arms follow the run weight
        // itself: as it falls into the walk/idle (a stop) it eases down over ~4 frames instead of one (r11: a 23 deg blade snap)
        if (!layered) { wDown = w >= wDown ? w : Mathf.Lerp(wDown, w, 1f - Mathf.Exp(-dt / StopEase)); w = wDown; }
        logW = w; logWWalk = wWalk; logSpd = spd;
        // (aim-move) The directional legs: the six weights, her pelvis's turn, and how much of her run the set takes over.
        if (dirChain) DirFrame(dt, w);
        if (!move2D)
        {
        tree.Set(P_move_blendW_blend_amount, wWalk);
        tree.Set(P_move_blend_blend_amount, w);
        }
        // Into the sprint as she goes past her run's own speed; the pair
        // played at the rate the blend of their speeds asks.
        float fast = sprintSpeed > runSpeed ? Mathf.SmoothStep(runSpeed * 1.1f, sprintSpeed * 0.95f, spd) : 0;
        if (!move2D) tree.Set(P_move_fast_blend_amount, fast);
        float natural = Mathf.Lerp(runSpeed, sprintSpeed, fast);
        // One stride phase for both gaits; a walk starts on the left heel after she has stood a moment.
        standT = spd < 0.05f ? standT + dt : 0;
        if (standT > 0.4f) stride = 0;
        float period = Stride.Period(spd, walkLen, walkSpeed, runLen, Stride.RunScale(spd, natural), w0, hasWalk);
        if (backW > 0.001f) period = Mathf.Lerp(period, ((1 - BackMix) * walkLen * walkSpeed + BackMix * runLen * runSpeed) / Mathf.Max(spd, 0.5f), backW);
        // (aim-move) With the set carrying weight, the stride's period is the set's: its clips' lengths by weight, at the run's own speed.
        if (dirChain && dirBlend > 0.001f)
        {
            float sum = 0, per = 0;
            for (int i = 0; i < 6; i++) { sum += dirW[i]; per += dirW[i] * dirLen[i]; }
            if (sum > 0.01f) period = Mathf.Lerp(period, per / sum * runSpeed / Mathf.Max(spd, 0.5f), dirBlend);
        }
        // (warden-turn) With her hips turned onto a blow behind her, the stride runs at her travel's part along her facing
        // (past 90 deg off it a backpedal), so the planted foot keeps more of its ground.
        float strideK = 1;
        if (!AimLegs && (hipGoal != null && aimHold > 0 || backpedal) && velX * velX + velZ * velZ > 0.16f)
            strideK = Mathf.Cos(Mathf.Wrap(Rotation.Y - Mathf.Atan2(velX, velZ), -Mathf.Pi, Mathf.Pi));
        // (turning r2) Through a 180's pivot her stride goes at her ground speed, not the run's floor (PivotFloor): she
        // slows onto the foot that is down and turns on it, then runs out of it.
        if (pivot && !TurnOld && !TurnSnap) strideK *= Mathf.Clamp(sp / Mathf.Max(spd, 0.5f), 0f, 1f);
        float strideRun = Stride.Advance(stride, dt * strideK, period);
        stride = pivotSeg > 0 && pivotFoot >= 0 ? PivotStride(strideRun, dt, period) : backpedal && !BackDriveOff && !AimLegs && w >= 0.9f ? (BackAirOff ? BackStride(strideRun, dt, period, strideK) : BackPhase(strideRun, dt, period, strideK)) : strideRun;
        if (!backpedal && backSt != 0 && plantOff.LengthSquared() < 1e-4f) backSt = 0;
        backWas = backpedal;
        if (!move2D)
        {
            tree.Set(P_move_walkSeek_seek_request, stride * walkLen);
            tree.Set(P_move_runSeek_seek_request, stride * runLen);
            // (idleAt) her idle on its own clock
            double il = IdleLen();
            if (il > 0)
            {
                IdleSyncDue(il);
                idleAt = ((idleAt + dt) % il + il) % il;
                tree.Set(P_move_idleSeek_seek_request, idleAt);
                if (layered) tree.Set(P_move_aIdleSeek_seek_request, idleAt);
            }
        }
        if (dirChain) for (int i = 0; i < 6; i++) tree.Set(DSeek[i], stride * dirLen[i]);
        // Her arms in one hold or the other (Play/ArmHold): only where the walk and the run carry a piece in hand
        // (her walk for this calling and kind, armed, not sheathed); elsewhere today's per-bone mix. --arm-blend off: the mix.
        // On P1's B there is no arm-hold layer at all (ArmHold.Layered: no HerArmHold, no arms' copy; the owner, 5 Nov):
        // B's holds are clip data (P4) and her arms play the main move graph. (P1 R1 pose 4's arms' copy for B's bridge
        // clips, B to A within 2.7 deg / 9 mm at the elbow, is retired with it: Stage B rebuilds those clips on B.)
        bool armCopy = !ArmBlendOff && !move2D && hasWalk && !sheath.Sheathed && (!string.IsNullOrEmpty(loadout.Arms.Right) || loadout.Arms.Left != null);
        bool armNow = armCopy && armMod != null;
        if (armNow && !armOn) armHold.Reset(w);
        if (armNow) armHold.Step(w, dt);
        armOn = armNow;
        if (AnimLog) GD.Print($"animlog f {Engine.GetProcessFrames()} w {w:0.000} wWalk {wWalk:0.000} armNow {armNow} run {armHold.Run} E {armHold.E:0.00} fading {armHold.Fading} upper {(bool)tree.Get(P_upperShot_active)} full {(bool)tree.Get(P_fullShot_active)}");
        // Mid-fade (and nothing laid over her arms: a blow, a roll), HerArmHold lays her arms between the two holds.
        bool fadeNow = armNow && armHold.Fading && !(bool)tree.Get(P_fullShot_active) && !(bool)tree.Get(P_upperShot_active);
        if (fadeNow && armMod != null)
        {
            if (armMod.AxisR == Vector3.Zero && armMod.AxisL == Vector3.Zero && view != null) { armMod.AxisR = view.PieceAxis("handslot.r"); armMod.AxisL = view.PieceAxis("handslot.l"); }
            Animation? A(string? n) => n != null && tree.HasAnimation(n) ? tree.GetAnimation(n) : null;
            armFade = (true, armHold.E, A(walkNode?.Animation), A(runNode?.Animation), A(sprintNode?.Animation), stride * walkLen, stride * runLen, fast);
        }
        else armFade = default;
        if (layered && !move2D) tree.Set(P_move_arms_blend_amount, armNow ? 1f : 0f);
        if (armNow)
        {
            tree.Set(P_move_aBlendW_blend_amount, wWalk);
            tree.Set(P_move_aFast_blend_amount, fast);
            tree.Set(P_move_aBlend_blend_amount, armHold.Run ? 1f : 0f);
            tree.Set(P_move_aWalkSeek_seek_request, stride * walkLen);
            tree.Set(P_move_aRunSeek_seek_request, stride * runLen);
        }
        // Her corrective layer stands down for whichever half plays hers.
        bool fullOn = (bool)tree.Get(P_fullShot_active), upperOn = (bool)tree.Get(P_upperShot_active);
        // The staff slid (animation 47) and tilted (animation 48) in her fist by whichever clip plays, eased between them.
        if (grips && idleNode != null && runNode != null)
        {
            float to = GripSlide.Target(fullOn, own.GripSlide(fullClip), upperOn, own.GripSlide(upperClip), wWalk, w,
                own.GripSlide(idleAn!), own.GripSlide((walkNode != null ? walkAn! : idleAn!)), own.GripSlide(runAn!));
            float toT = GripSlide.Target(fullOn, own.GripTilt(fullClip), upperOn, own.GripTilt(upperClip), wWalk, w,
                own.GripTilt(idleAn!), own.GripTilt((walkNode != null ? walkAn! : idleAn!)), own.GripTilt(runAn!));
            slide = GripSlide.Ease(slide, to, dt);
            tilt = GripSlide.Ease(tilt, toT, dt);
            // (warden-move) the side carry's tilt on top (SideCarry), stepped on her drawn pose (CarryPosed); none at no weight
            CarrySlide(null);
            carryDt += dt;
            if (!carryHooked && person.Skeleton is { } csk && view != null) { carryHooked = true; csk.SkeletonUpdated += CarryPosed; }
            float toL = GripSlide.Target(fullOn, own.GripSlideL(fullClip), upperOn, own.GripSlideL(upperClip), wWalk, w,
                own.GripSlideL(idleAn!), own.GripSlideL((walkNode != null ? walkAn! : idleAn!)), own.GripSlideL(runAn!));
            slideL = GripSlide.Ease(slideL, toL, dt);
            // The left tilt (animation 58), and the weight that eases a piece without a fitted left pocket onto the tilt's.
            float toTL = GripSlide.Target(fullOn, own.GripTiltL(fullClip), upperOn, own.GripTiltL(upperClip), wWalk, w,
                own.GripTiltL(idleAn!), own.GripTiltL((walkNode != null ? walkAn! : idleAn!)), own.GripTiltL(runAn!));
            static float On(float t) => t != 0 ? 1 : 0;
            float toPL = GripSlide.Target(fullOn, On(own.GripTiltL(fullClip)), upperOn, On(own.GripTiltL(upperClip)), wWalk, w,
                On(own.GripTiltL(idleAn!)), On(own.GripTiltL((walkNode != null ? walkAn! : idleAn!))), On(own.GripTiltL(runAn!)));
            tiltL = GripSlide.Ease(tiltL, toTL, dt);
            pocketL = GripSlide.Ease(pocketL, toPL, dt);
            view?.Slide("handslot.l", slideL, tiltL, pocketL);
        }
        // The pelvis counter's blend: the upper shot's own weight (fade in from its start, out to its end or from a release),
        // reproduced from the clip's position (AnimationNodeOneShot gives no weight); none while the upper shot is off or
        // a full-body clip has taken her over.
        if (person.Counter is { } pc)
        {
            float cw = 0;
            if (upperOn && !fullOn && pc.Mean != null && UpperAnim() is { } uanim)
            {
                double pace = System.Math.Max(upperRate, 1e-3), pos = (float)tree.Get(P_upper_current_position);
                cw = SurvivorUnchained.Play.PelvisCounter.Weight(pos / pace, (uanim.Length - pos) / pace, upperShotNode.FadeInTime, upperShotNode.FadeOutTime,
                    upperRelease >= 0 ? time - upperRelease : -1, upperShotNode.FadeOutTime);
            }
            pc.Weight = cw;
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
        // Now from her travel's own curve: the sideways pull (velocity x its change, over her speed), which is
        // the old turn rate times speed on a steady curve, and nothing on a 180 (a plant, not a bank).
        float rate = Mathf.Wrap(Rotation.Y - heading, -Mathf.Pi, Mathf.Pi) / dt;
        heading = Rotation.Y;
        if (!TurnOld)
        {
            float v = Mathf.Sqrt(velX * velX + velZ * velZ);
            rate = v > 0.4f ? (velZ * (velX - lastVelX) - velX * (velZ - lastVelZ)) / dt / (v * Mathf.Max(v, speed)) : 0;
        }
        lastVelX = velX; lastVelZ = velZ;
        turnRate = Mathf.Lerp(turnRate, rate, 1 - Mathf.Exp(-(TurnOld ? 10 : 16) * dt));
        float bank = Mathf.Clamp(-turnRate * speed * 1.6f, -14, 14);
        carriage.Bank = Mathf.Lerp(carriage.Bank, bank, 1 - Mathf.Exp(-(TurnOld ? 8 : BankRate) * dt));
        // Into a start, back out of a stop.
        float acc = (sp - lastSpeed) / dt;
        lastSpeed = sp;
        accel = Mathf.Lerp(accel, acc, 1 - Mathf.Exp(-12 * dt));
        // (turning r3) Back against the old run through a 180's brake, until she is half way round.
        bool brake = pivotSeg > 0 && Mathf.Abs(Mathf.Wrap(Rotation.Y - pivotYaw0, -Mathf.Pi, Mathf.Pi)) < Mathf.DegToRad(90);
        // (t4) and back off the run's forward lean while it plays backwards (a backpedal, her hips past 90 deg off her travel).
        bool back = backpedal && velX * velX + velZ * velZ > 0.16f && Mathf.Abs(Mathf.Wrap(Rotation.Y - Mathf.Atan2(velX, velZ), -Mathf.Pi, Mathf.Pi)) > Mathf.Pi / 2;
        brake |= back;
        carriage.Tilt = Mathf.Lerp(carriage.Tilt, brake ? -(back ? BackLean : PivotLean) : Mathf.Clamp(accel * 0.35f, -9, 7), 1 - Mathf.Exp(-(brake ? 30 : 10) * dt));
        // Her back to the blow while it lasts, then home.
        float aimTo = aimHold > 0 ? aim : 0;
        float bodyStep = Mathf.RadToDeg(Mathf.Wrap(Rotation.Y - lastBodyYaw, -Mathf.Pi, Mathf.Pi));
        lastBodyYaw = Rotation.Y;
        if (TurnSnap || AimLegs) carriage.Aim = Mathf.Lerp(carriage.Aim, aimTo, 1 - Mathf.Exp((aimHold > 0 ? -30 : -8) * dt));
        else
        {
            // (warden-turn; A1 L21's eased waist) At 30 a second the waist put 63% of a 90 deg blow in one frame. Now eased
            // in (WaistFirst deg the first frame), at most WaistRate after, eased out on the goal, never past it; and her
            // shoulders (body + waist) never turn more than ShoulderMax in a frame between them.
            float rem = aimTo - carriage.Aim, f = dt * 30;
            waistRamp = Mathf.Abs(rem) < 0.5f ? 0 : waistRamp <= 0 ? WaistFirst : WaistRate;
            float k = aimHold > 0 ? 0.75f : 1 - Mathf.Exp(-8 * dt);
            float stepA = Mathf.Min(waistRamp * f, Mathf.Abs(rem) * k) * Mathf.Sign(rem);
            // (same way as the body's step: the pair together at most ShoulderMax; against it, unwinding, free)
            if (stepA * bodyStep > 0) stepA = Mathf.Sign(stepA) * Mathf.Min(Mathf.Abs(stepA), Mathf.Max(0, ShoulderMax * f - Mathf.Abs(bodyStep)));
            carriage.Aim += stepA;
        }
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
    // Rendering r2 (judge r1 D1, a pale cream disc larger than the camp fire's): 2500K #ffa868, falloff 2, 0.75x the reach,
    // and from shoulder height (1.7, --ember-h) now that the folk light, not the pool, lights her: a tight pool, the fire's the larger.
    static readonly float EmberFlareCap = DenShade.Num("ember-flare-cap", 3.8f, 2.2f);   // (cool shade lane: under --den-shade 1 her lamp's ground share is 0.4 (hero_den 38), so the Flare on the ground needs the rig's whole ember; 2.2 everywhere else, as it was)
    /// <summary>Her carried light's own colour; --ember-color C over it and over the air's (pictures).</summary>
    static readonly Color EmberOwn = new("#ffa868");
    static readonly Color? EmberArg = SurvivorUnchained.Args.Get("ember-color") is string ec ? new Color(ec) : null;
    static readonly float EmberAtt = SurvivorUnchained.Args.Num("ember-att", 2f), EmberRangeK = SurvivorUnchained.Args.Num("ember-range", 0.75f);
    // --ember-folk K (0: one light on all, as before), --ember-folk-h/-z/-range/-att/-color: the folk light (FolkLight).
    static readonly float FolkK = SurvivorUnchained.Args.Num("ember-folk", 5f), FolkH = SurvivorUnchained.Args.Num("ember-folk-h", 4.5f),
        FolkZ = SurvivorUnchained.Args.Num("ember-folk-z", 0.6f), FolkRange = SurvivorUnchained.Args.Num("ember-folk-range", 1.3f),
        FolkAtt = SurvivorUnchained.Args.Num("ember-folk-att", 2f);
    // --ember-h H: the pool light's height over her feet; --ember-k K: her ember's gain times K (sweeps of any preset).
    static readonly float EmberH = SurvivorUnchained.Args.Num("ember-h", 1.7f), EmberK = SurvivorUnchained.Args.Num("ember-k", 1f);
    // (demo-look r2 her) in the den the rig's own height (hero_den value 33, HeroDen.EmberH: a pool ~120 px round her, brighter
    // at its centre; at 1.7 it was flat to 160 px); --ember-h given wins.
    static readonly bool EmberHArg = SurvivorUnchained.Args.Get("ember-h") != null;
    static float EmberHNow => !EmberHArg && HeroDen.EmberH > 0 ? HeroDen.EmberH : EmberH;
    // (lane E polish) in the den the pool light's own energy on the ground (hero_den value 38, HeroDen.PoolK; 1 elsewhere): her
    // folk light (which follows the pool's energy) and her lamp on the crowd divide it back out, so only the ground's pool moves.
    static float PoolDen => HeroDen.PoolK > 0 ? HeroDen.PoolK : 1;
    // --clip-tour LIST|all (--clip-tour-from S): the clip playing and its time, for the probes (null / -1 outside a tour).
    static readonly string? TourArg = SurvivorUnchained.Args.Get("clip-tour");
    static readonly float TourFrom = SurvivorUnchained.Args.Num("clip-tour-from", 0f);
    public static string? TourClip { get; private set; }
    public static double TourTime { get; private set; } = -1;
    List<string>? tourList;
    static readonly int TourShots = (int)SurvivorUnchained.Args.Num("clip-tour-shots", 0);
    static readonly long TourWait = (long)SurvivorUnchained.Args.Num("clip-tour-wait", 0);
    int tourShot;
    int tourAt = -1, tourPhase;   // 0: next clip to set up, 2: its first pose drawn for a frame, 1: playing, 3: done
    List<string>? TourList => TourArg == null ? null : tourList ??= TourNames();

    List<string> TourNames()
    {
        var names = new List<string>();
        if (TourArg == "all")
        {
            if (own.Library() is { } lib) names.AddRange(lib.GetAnimationList().Select(n => n.ToString()));
            if (P1Body.On && P1Body.HerClips() is { } hc) names.AddRange(hc.GetAnimationList().Select(n => n.ToString()));
        }
        else names.AddRange(TourArg!.Split(',', System.StringSplitOptions.RemoveEmptyEntries | System.StringSplitOptions.TrimEntries));
        return names.Distinct().Where(n => own.Has(n)).ToList();
    }

    void TourStep()
    {
        var list = tourList!;
        if (tourPhase == 3) return;   // done, quitting
        // --clip-tour-wait F (lane G motion probe): the first clip starts after process frame F (a close-up's camera settles first)
        if (tourAt < 0 && tourPhase == 0 && (long)Engine.GetProcessFrames() < TourWait) return;
        if (tourPhase == 1)
        {
            TourTime = person.Anim.CurrentAnimationPosition;
            // --clip-tour-shots N (lane G motion probe, 16 Nov): N frames a clip, evenly over its length, saved as CLIP_KK
            if (TourShots > 0 && person.Anim.CurrentAnimation is { } ca && person.Anim.GetAnimation(ca) is { } tl)
                while (tourShot < TourShots && TourTime >= tourShot * tl.Length / TourShots)
                    Shots.WantFrames($"{list[tourAt]}_{tourShot++:00}", 0);
            if (person.Anim.IsPlaying()) return;
            GD.Print($"clip-tour: {list[tourAt]} end");
        }
        else if (tourPhase == 2) { tourPhase = 1; person.Anim.Play(); return; }   // (the first pose was drawn for one frame: let it run)
        tourAt++;
        if (tourAt >= list.Count)
        {
            GD.Print("clip-tour: done");
            TourClip = null; TourTime = -1; tourPhase = 3;
            WearInside.Finish();
            GetTree().Quit();
            return;
        }
        string clip = list[tourAt];
        view?.Sheathe(clip.EndsWith("_town") || SurvivorUnchained.Args.Has("sheathed"));
        if (grips)
        {
            slide = own.GripSlide(clip); tilt = own.GripTilt(clip);
            view?.Slide("handslot.r", slide, tilt);
            slideL = own.GripSlideL(clip); tiltL = own.GripTiltL(clip);
            pocketL = tiltL != 0 ? 1 : 0;
            view?.Slide("handslot.l", slideL, tiltL, pocketL);
        }
        string full = own.Prefix + clip;
        var anim = person.Anim.GetAnimation(full);
        anim.LoopMode = Animation.LoopModeEnum.None;
        person.Anim.Play(full);
        person.Anim.Seek(TourFrom, true);
        person.Anim.Pause();
        TourClip = clip; TourTime = TourFrom; tourShot = 0;
        bool moveClip = clip.StartsWith("idle_") || clip.StartsWith("run_") || clip.StartsWith("sprint_") || clip.StartsWith("stop_") || clip.StartsWith("walk_");
        if (carriage != null) carriage.HeadLevel = moveClip || own.Stance(clip) ? HeadLevel : 0;
        if (person.Pose != null) person.Pose.Native = 1;
        GD.Print($"clip-tour: {clip} {TourFrom:0.###} {anim.Length:0.###}");
        tourPhase = 2;
    }
    static readonly string[]? Hold = SurvivorUnchained.Args.Get("hold")?.Split('@');
    static readonly bool HoldTurn = SurvivorUnchained.Args.Has("close-turn");
    /// <summary>--hold-mirror with a hold (L1 lead 22, pictures only): the held frame mirrored left for right (PoseMirror).</summary>
    static readonly bool HoldMirror = SurvivorUnchained.Args.Has("hold-mirror");
    // (L1 lead 22, p2stand) --hold-head: a whole-body hold keeps her head carried up (HeadLevel) as an idle does, so the
    // face, not the crown, shows at the play camera. View only, off by default.
    static readonly bool HoldHead = SurvivorUnchained.Args.Has("hold-head");
    PoseMirror? mirror;
    bool mirrorSaid;
    /// <summary>--facing DEG read for a held frame (the Hold branch): her heading in radians, null without the flag.</summary>
    static readonly float? HoldFacing = SurvivorUnchained.Args.Get("facing") is string hfa
        ? Mathf.DegToRad(float.Parse(hfa, System.Globalization.CultureInfo.InvariantCulture)) : null;
    /// <summary>--turn-old: her facing chasing her velocity, the run blend and the lean as before N27 (before/after
    /// pictures); --face-rate R, --blend-rate R, --bank-rate R: how fast her facing meets the stick, her legs her speed, her lean its curve.</summary>
    static readonly bool TurnOld = SurvivorUnchained.Args.Has("turn-old");
    static readonly float FaceRate = SurvivorUnchained.Args.Num("face-rate", 36f), BlendRate = SurvivorUnchained.Args.Num("blend-rate", 40f),
        BankRate = SurvivorUnchained.Args.Num("bank-rate", 14f);
    /// <summary>(warden-turn, the owner 10 Nov "movement looked weird especially turning"; A1 leads 20-21's view pieces ported
    /// to the heroine) Her turn, eased and rate-limited: the 4 Nov chase (FaceRate 36/s) put 126 deg of a 180 into ONE frame
    /// at 30 fps, 63 of a 90, and a blow flipped her whole. Now her yaw speed eases up (TurnEase/s) to a cap and settles on
    /// the goal at TurnK/s: running TurnMax (35 deg a 30 fps frame), a 180 at a run TurnPivot (a pivot, 28 deg a frame over 7 frames: judge r3 on the 180 "a whirl"), standing
    /// to a blow TurnMaxStanding; her hips onto a blow behind her HipRate. --turn-snap: the 4 Nov snap (before pictures).</summary>
    static readonly bool TurnSnap = SurvivorUnchained.Args.Has("turn-snap"), CoilOff = SurvivorUnchained.Args.Has("turn-coil-off"),
        TurnLog = SurvivorUnchained.Args.Has("turn-log");
    static readonly bool HeldLogOn = SurvivorUnchained.Args.Has("held-log");
    static readonly float TurnMax = SurvivorUnchained.Args.Num("turn-max", 1050f), TurnPivot = SurvivorUnchained.Args.Num("turn-pivot", 840f),
        TurnK = SurvivorUnchained.Args.Num("turn-k", 18f), TurnEase = SurvivorUnchained.Args.Num("turn-ease", 20f),
        TurnMaxStanding = SurvivorUnchained.Args.Num("turn-max-standing", 1050f), TurnEaseStanding = SurvivorUnchained.Args.Num("turn-ease-standing", 30f),
        HipRate = SurvivorUnchained.Args.Num("turn-hip-rate", 600f), HipMax = SurvivorUnchained.Args.Num("turn-hip-max", 60f),
        WaistMax = SurvivorUnchained.Args.Num("turn-waist-max", 75f), WaistFirst = SurvivorUnchained.Args.Num("turn-waist-first", 18f),
        WaistRate = SurvivorUnchained.Args.Num("turn-waist-rate", 28f), ShoulderMax = SurvivorUnchained.Args.Num("turn-shoulder-max", 33f),
        CoilTol = SurvivorUnchained.Args.Num("turn-coil-tol", 22f), CoilPace = SurvivorUnchained.Args.Num("turn-coil-pace", 0.4f),
        CoilWind = SurvivorUnchained.Args.Num("turn-coil-wind", 0.9f), CoilCatch = SurvivorUnchained.Args.Num("turn-coil-catch", 1.3f);
    static readonly int CoilMax = (int)SurvivorUnchained.Args.Num("turn-coil-max", 5f);
    float yawVel, lastBodyYaw, waistRamp;
    bool turning, turnedLast, pivot, backpedal;
    // (t4) A blow behind her at a run: past BackAt deg off her travel her hips go round at BackRate deg/s and she backpedals,
    // leaning back BackLean deg. --turn-back-off: round 2's hips part way round (HipMax).
    static readonly bool BackOff = SurvivorUnchained.Args.Has("turn-back-off"), BackRun = SurvivorUnchained.Args.Has("turn-back-run");
    float backW;
    static readonly float BackBlend = SurvivorUnchained.Args.Num("turn-back-blend", 20f);
    static readonly float BackAt = SurvivorUnchained.Args.Num("turn-back-at", 110f), BackRate = SurvivorUnchained.Args.Num("turn-back-rate", 900f),
        BackLean = SurvivorUnchained.Args.Num("turn-back-lean", 10f), BackMix = SurvivorUnchained.Args.Num("turn-back-mix", 1f);
    // (round 5) The pelvis ease moved the held foot after the plant lock; off in a backpedal unless --turn-smooth-back.
    static readonly bool SmoothBack = SurvivorUnchained.Args.Has("turn-smooth-back");
    static readonly float BackHold = SurvivorUnchained.Args.Num("turn-back-hold", 0.6f), BackShiftMax = SurvivorUnchained.Args.Num("turn-back-shift", 0.07f);
    /// <summary>A blow's facing her whole body turns to (standing or slow when struck), and the facing her hips turn to for a
    /// blow behind her at a run (radians), each held while aimHold lasts.</summary>
    float? faceGoal, hipGoal;

    /// <summary>One frame of the eased turn toward `want` (radians): at most `max` deg/s, its speed eased at `ease`/s.</summary>
    void TurnTo(float want, float dt, float max, float ease, int dir = 0)
    {
        if (!turnedLast) yawVel = 0;
        turning = true;
        float err = Mathf.RadToDeg(Mathf.Wrap(want - Rotation.Y, -Mathf.Pi, Mathf.Pi));
        if (dir != 0 && Mathf.Sign(err) != dir && Mathf.Abs(err) > 45f) err -= Mathf.Sign(err) * 360f;   // (r10) the committed way round
        float goal = Mathf.Clamp(err * TurnK, -max, max);
        yawVel = Mathf.Lerp(yawVel, goal, 1 - Mathf.Exp(-ease * dt));
        float step = yawVel * dt;
        // (never past the goal, never away from it)
        if (step * err < 0) step = 0;
        else if (Mathf.Abs(step) > Mathf.Abs(err)) step = err;
        Rotation = new Vector3(0, Rotation.Y + Mathf.DegToRad(step), 0);
    }

    /// <summary>(turning r2) A 180's pivot under way with the stick still held: the sim's speed passing through zero as it
    /// reverses is not a stop.</summary>
    bool PivotHeld(double sx, double sz) => pivot && !TurnOld && !TurnSnap && sx * sx + sz * sz > 0.01;

    // (turning r2, the owner 10 Nov "movement looked weird especially turning") Her turn at a run pivots on the planted foot.
    // The body's yaw turned her about her root, so the foot on the ground was swung round with her (the 90's planted foot at
    // 1.5-4.6 m/s for three frames; the 180's at 6-9). Now, when her yaw moves more than PlantYaw deg in a frame at a run and
    // a ball of her foot was on the ground the frame before, that ball is held where it stood (her whole view shifted by the
    // difference, plantOff) until it lifts (PlantLift above the ground), PlantHold s pass, or the shift reaches PlantMax. The
    // shift goes back to the sim's place while no foot is down (PlantDecay/s; a third of it with a foot down). View only.
    // --turn-plant-off: as before.
    static readonly bool PlantOff = SurvivorUnchained.Args.Has("turn-plant-off");
    static readonly float PlantYaw = SurvivorUnchained.Args.Num("turn-plant-yaw", 3f), PlantTouch = SurvivorUnchained.Args.Num("turn-plant-touch", 0.07f),
        PlantLift = SurvivorUnchained.Args.Num("turn-plant-lift", 0.10f), PlantHold = SurvivorUnchained.Args.Num("turn-plant-hold", 0.35f),
        PlantMax = SurvivorUnchained.Args.Num("turn-plant-max", 0.6f), PlantDecay = SurvivorUnchained.Args.Num("turn-plant-decay", 12f),
        PivotFloor = SurvivorUnchained.Args.Num("turn-pivot-floor", 3.4f);
    Vector3 plantOff, plantAt;
    readonly Vector3[] plantPrev = new Vector3[2];
    readonly float[] plantPrevH = { 1, 1 }, plantH = { 1, 1 };
    int plantFoot = -1, plantBallL = -2, plantBallR = -2;
    float plantT, plantYawStep, plantYawPrev, plantDt;
    bool plantHooked;
    System.Func<double, double, double>? plantGround;

    void PlantStep()
    {
        var sk = person.Skeleton;
        if (plantGround == null || sk == null) return;
        if (plantBallL == -2) { plantBallL = sk.FindBone("ball_l"); plantBallR = sk.FindBone("ball_r"); }
        if (plantBallL < 0 || plantBallR < 0) return;
        var f = new[] { sk.GlobalTransform * sk.GetBoneGlobalPose(plantBallL).Origin, sk.GlobalTransform * sk.GetBoneGlobalPose(plantBallR).Origin };
        // (round 5) into a backpedal the pelvis ease (a 180's tail) hands its gap to the plant lock: eased on, it moved the held foot
        bool backDrive = backpedal && !BackDriveOff && !SmoothBack;
        if (backDrive && smoothOn && pivotSeg == 0 && !pivot)
        {
            plantOff += smoothOff; plantAt += smoothOff; plantPrev[0] += smoothOff; plantPrev[1] += smoothOff;
            smoothOff = Vector3.Zero; smoothOn = false;
        }
        // (the plant lock works where she stands without the pelvis ease, SmoothStep; it is put back after)
        Position -= smoothOff; f[0] -= smoothOff; f[1] -= smoothOff;
        for (int i = 0; i < 2; i++) plantH[i] = f[i].Y - (float)plantGround(f[i].X, f[i].Z);
        bool legsFree = !(bool)tree.Get(P_fullShot_active);
        Vector3 shift = Vector3.Zero;
        if (pivotSeg > 0)
        {
            // (a 180's plan: only its pivot foot is held, from the frame it is down, once)
            if (plantFoot >= 0 && plantFoot != pivotFoot) plantFoot = -1;
            if (plantFoot < 0 && !pivotHeld && legsFree && plantH[pivotFoot] < PlantTouch) { plantFoot = pivotFoot; plantAt = f[pivotFoot]; plantT = 0; pivotHeld = true; }
        }
        else if (plantFoot < 0 && legsFree && (plantYawStep > PlantYaw || backpedal && !BackDriveOff) && speed > 1.5f)
        {
            int i = plantPrevH[0] <= plantPrevH[1] ? 0 : 1;
            if (plantPrevH[i] < PlantTouch && i != backLiftFoot) { plantFoot = i; plantAt = plantPrev[i]; plantT = 0; }
        }
        if (plantFoot >= 0 && plantFoot == backLiftFoot) plantFoot = -1;   // (round 6: a foot un-landing into a backpedal is not held)
        if (plantFoot >= 0)
        {
            plantT += plantDt;
            // (t4) in a backpedal the foot is held only while her hips come round; then the backwards run carries her (held on, it
            // stood 8 frames with the view 0.48 m behind the sim, a wide held stance that slid)
            if (plantH[plantFoot] > PlantLift || plantT > (backpedal && !BackDriveOff ? BackHold : PlantHold) || !legsFree || backpedal && BackDriveOff && plantYawStep <= PlantYaw) plantFoot = -1;
            else
            {
                var want = plantOff + new Vector3(plantAt.X - f[plantFoot].X, 0, plantAt.Z - f[plantFoot].Z);
                if (want.Length() > PlantMax) { want = want.Normalized() * PlantMax; plantFoot = -1; }
                shift = want - plantOff;
                // (round 5) in a backpedal the view's correction is held to BackShiftMax m a 30 fps frame (the judge's catch-up)
                float cap = BackShiftMax * plantDt * 30;
                if (backDrive && shift.Length() > cap) shift = shift.Normalized() * cap;
            }
        }
        if (plantFoot < 0)
        {
            float rate = Mathf.Min(plantH[0], plantH[1]) > PlantTouch ? PlantDecay : PlantDecay / 3;
            shift = -plantOff * (1 - Mathf.Exp(-rate * plantDt));
        }
        // (round 6) through a backpedal and until its shift is home the decay too is held to BackShiftMax a frame
        if (backSt != 0 && !BackDriveOff && !BackAirOff) { float cap = BackShiftMax * plantDt * 30; if (shift.Length() > cap) shift = shift.Normalized() * cap; }
        plantOff += shift;
        Position += shift;
        for (int i = 0; i < 2; i++) { plantPrev[i] = f[i] + shift; plantPrevH[i] = plantH[i]; }
        SmoothStep(sk);
    }

    // (turning r4, judge r3 on the 180: "a whirl ... pelvis surge 1.5-2.5x run f244-248, a 34 px pop at f248") Through a 180's
    // pivot and a backpedal, her pelvis's ground path is eased: a spring (SmoothW/s, critically damped) after where the pose
    // and the plant lock put it, its pace change held to SmoothAcc of the run's pace a frame and its pace to SmoothMax of the
    // run's, the gap (with the plant lock's) at most SmoothLag m. The sim's reversal (two frames) and the yaw's swing about the
    // planted foot no longer reach the screen as a stop-and-surge. View only; --turn-smooth-off: r3.
    static readonly bool SmoothOffFlag = SurvivorUnchained.Args.Has("turn-smooth-off"), SmoothDbg = SurvivorUnchained.Args.Has("turn-smooth-dbg");
    static readonly float SmoothW = SurvivorUnchained.Args.Num("turn-smooth-w", 0.5f), SmoothAcc = SurvivorUnchained.Args.Num("turn-smooth-acc", 0.36f),
        SmoothMax = SurvivorUnchained.Args.Num("turn-smooth-max", 1.2f), SmoothLag = SurvivorUnchained.Args.Num("turn-smooth-lag", 0.48f),
        SmoothRun = SurvivorUnchained.Args.Num("turn-smooth-run", 5.65f), SmoothSlow = SurvivorUnchained.Args.Num("turn-smooth-slow", 0.28f),
        SmoothSlowYaw = SurvivorUnchained.Args.Num("turn-smooth-slow-yaw", 60f);
    Vector3 smoothOff, smoothP, smoothV, smoothRawPrev, smoothRawV;
    bool smoothOn, smoothHave;
    int smoothCalls;
    int smoothPelvis = -2;
    void SmoothStep(Skeleton3D sk)
    {
        smoothCalls++;
        if (smoothPelvis == -2) smoothPelvis = sk.FindBone("pelvis");
        if (smoothPelvis < 0 || plantDt <= 0) return;
        var pw = sk.GlobalTransform * sk.GetBoneGlobalPose(smoothPelvis).Origin;
        var raw = new Vector3(pw.X, 0, pw.Z);   // (PlantStep took the ease off Position)
        float dt = plantDt;
        var rawV = smoothHave ? (raw - smoothRawPrev) / dt : Vector3.Zero;
        bool want = !SmoothOffFlag && (pivot || pivotSeg > 0 || backpedal && SmoothBack) && !(bool)tree.Get(P_fullShot_active);
        if (!smoothOn && want && smoothHave) { smoothOn = true; smoothP = smoothRawPrev; smoothV = smoothRawV; }
        if (smoothOn)
        {
            float run = SmoothRun, aMax = SmoothAcc * run * 30f;   // (SmoothAcc of the run's pace per 30 fps frame)
            // (the pace that closes the gap as fast as the pace change allows, braking in time: no overshoot)
            var e = raw - smoothP - rawV * dt;   // (the gap left if it kept the pose's own pace this frame)
            float el = e.Length();
            var vWant = rawV + (el > 1e-5f ? e / el * Mathf.Min(Mathf.Sqrt(2 * SmoothW * aMax * el), el / dt) : Vector3.Zero);
            // (a 180: through its first SmoothSlowYaw deg she stands on the pivot, at most SmoothSlow of the run's pace)
            bool slow = pivot && Mathf.RadToDeg(Mathf.Abs(Mathf.Wrap(Rotation.Y - pivotYaw0, -Mathf.Pi, Mathf.Pi))) < SmoothSlowYaw;
            float cap = (slow ? SmoothSlow : SmoothMax) * run;
            if (vWant.Length() > cap) vWant = vWant.Normalized() * cap;
            var dv = vWant - smoothV;
            if (dv.Length() > aMax * dt) dv = dv.Normalized() * aMax * dt;
            smoothV += dv;
            if (SmoothDbg) GD.Print(System.FormattableString.Invariant($"SMOOTH raw {raw.X:0.000} {raw.Z:0.000} P {smoothP.X:0.000} {smoothP.Z:0.000} rawV {rawV.X:0.00} {rawV.Z:0.00} vW {vWant.X:0.00} {vWant.Z:0.00} V {smoothV.X:0.00} {smoothV.Z:0.00} want {want}"));
            smoothP += smoothV * dt;
            var off = smoothP - raw;
            // (the whole gap from the sim, the plant lock's with this, at most SmoothLag)
            var tot = off + new Vector3(plantOff.X, 0, plantOff.Z);
            if (tot.Length() > SmoothLag) { tot = tot.Normalized() * SmoothLag; off = tot - new Vector3(plantOff.X, 0, plantOff.Z); smoothP = raw + off; }
            smoothOff = off;
            if (!want && off.Length() < 0.004f && (smoothV - rawV).Length() < 0.05f * run) { smoothOn = false; smoothOff = Vector3.Zero; }
        }
        Position += smoothOff;
        smoothRawPrev = raw; smoothRawV = rawV; smoothHave = true;
    }

    // (turning r3, the solver; judge r2 on the 180: "she spins about 180 deg on one spot in the air while her legs scissor ...
    // a quick whirl, not a grounded fighter turning") A 180 at a run plants and pivots. At the reversal her stance foot is the
    // trailing one, toeing off 0.47 m behind her, and the other is mid-swing; the yaw turned her about her root with both feet
    // up (f244-f249) and carried the trailing leg round, 0.4-0.6 m out to her side (the "kick"). Now the foot that can stand
    // under where the sim stops her is the pivot (PivotStart): a swing foot is brought down early, the stride hurried to its
    // plant (PivotAheadM ahead of her, within PivotLand frames) while her yaw is held back (PivotBrakeYaw deg/s); the plant
    // lock holds it (and only it); then she turns on it, the stride walking it from under her to behind her as the new run
    // pulls away (the phase from where it stands in her turning frame, so the view shift takes only the left-right swap a
    // pivot makes), and she pushes off it. She leans back against the old run through the brake (PivotLean deg). View only:
    // the sim's aim, position and velocity are untouched. --turn-pivot-plan-off: as r2.
    static readonly bool PivotPlanOff = SurvivorUnchained.Args.Has("turn-pivot-plan-off");
    static readonly float PivotLand = SurvivorUnchained.Args.Num("turn-pivot-land", 2f), PivotAheadM = SurvivorUnchained.Args.Num("turn-pivot-ahead", 0.1f),
        PivotBrakeYaw = SurvivorUnchained.Args.Num("turn-pivot-brake-yaw", 150f), PivotEase = SurvivorUnchained.Args.Num("turn-pivot-ease", 40f), PivotLean = SurvivorUnchained.Args.Num("turn-pivot-lean", 12f),
        PivotRateMax = SurvivorUnchained.Args.Num("turn-pivot-rate", 2.5f), PivotMidL = SurvivorUnchained.Args.Num("turn-pivot-mid-l", 0.19f),
        PivotMidR = SurvivorUnchained.Args.Num("turn-pivot-mid-r", 0.69f), PivotStanceIn = SurvivorUnchained.Args.Num("turn-pivot-stance", 0.08f),
        PivotToeOff = SurvivorUnchained.Args.Num("turn-pivot-toe", 0.16f);
    /// <summary>0 none, 1 bringing the pivot foot down, 2 turning on it.</summary>
    int pivotSeg, pivotFoot = -1, pivotLandN;
    float pivotRel, pivotYaw0;
    bool pivotHeld;
    /// <summary>The clip's stance foot travel, metres a unit of stride phase (its speed times its cycle).</summary>
    float PivotK => Mathf.Max(runSpeed * runLen, 1f);
    float PivotMid(int foot) => foot == 0 ? PivotMidL : PivotMidR;
    static float Rel(float ph, float mid) => Mathf.PosMod(ph - mid + 0.5f, 1f) - 0.5f;

    /// <summary>A 180 at a run begins: the pivot foot is the stance foot if it is still under or ahead of her (at most
    /// PivotStanceIn of a phase past mid-stance), else the one coming down next.</summary>
    void PivotStart()
    {
        if (PivotPlanOff || TurnOld || TurnSnap || (bool)tree.Get(P_fullShot_active)) return;
        float rl = Rel(stride, PivotMidL), rr = Rel(stride, PivotMidR), plantRel = -PivotAheadM / PivotK;
        // (a stance foot: from its landing, a quarter phase before mid-stance at most, to PivotStanceIn past it)
        bool inL = rl > -0.11f && rl <= PivotStanceIn, inR = rr > -0.11f && rr <= PivotStanceIn;
        if (inL || inR) { pivotFoot = inL ? 0 : 1; pivotSeg = 2; pivotRel = inL ? rl : rr; }
        else
        {
            // the next down: the one with the least phase to go to its plant
            float gl = Mathf.PosMod(plantRel - rl, 1f), gr = Mathf.PosMod(plantRel - rr, 1f);
            pivotFoot = gl <= gr ? 0 : 1; pivotSeg = 1; pivotRel = pivotFoot == 0 ? rl : rr;
            pivotLandN = Mathf.Max(1, Mathf.RoundToInt(PivotLand));
        }
        pivotHeld = false; pivotYaw0 = Rotation.Y;
    }

    // (t4 round 5; judge r3: "a scurry, ~7.5 steps/s, 25-35% skate, catch-up 16-18 px/frame") A backpedal at a run steps on her
    // run played backwards, its phase driven by the foot that is down: each frame the phase that puts the clip's stance foot
    // (fwd = -(phase - BackMid) * BackK along her facing, the run's stance line) where the plant lock holds it, at her place and
    // yaw next frame, so the foot does not slide and her cadence is what her ground and the run's step give (no scurry). With
    // no foot down (the run's flight, played backwards) the phase goes at BackFlight of the ground pace, so no split is held
    // while she drifts back. The plant lock holds whichever foot is down through a backpedal (PlantStep). View only.
    // --turn-back-drive-off: round 4 (the phase at her ground pace, strideK).
    static readonly bool BackDriveOff = SurvivorUnchained.Args.Has("turn-back-drive-off");
    static readonly float BackMidL = SurvivorUnchained.Args.Num("turn-back-mid-l", 0.139f), BackMidR = SurvivorUnchained.Args.Num("turn-back-mid-r", 0.638f),
        BackKScale = SurvivorUnchained.Args.Num("turn-back-k", 0.97f), BackRateMax = SurvivorUnchained.Args.Num("turn-back-rate-max", 2.5f),
        BackFlight = SurvivorUnchained.Args.Num("turn-back-flight", 1.8f);
    float BackStride(float natural, float dt, float period, float strideK)
    {
        float normal = dt / Mathf.Max(period, 0.1f), k = Mathf.Max(runSpeed * runLen * BackKScale, 1f);
        if (plantFoot >= 0)
        {
            var at = GlobalPosition + new Vector3(velX, 0, velZ) * dt;
            float yaw = Rotation.Y + (turnedLast ? Mathf.DegToRad(yawVel * dt) : 0);
            float fwd = (plantAt.X - at.X) * Mathf.Sin(yaw) + (plantAt.Z - at.Z) * Mathf.Cos(yaw);
            float want = (plantFoot == 0 ? BackMidL : BackMidR) - fwd / k;
            float step = Mathf.Clamp(Mathf.PosMod(want - stride + 0.5f, 1f) - 0.5f, -BackRateMax * normal, BackRateMax * normal);
            return Mathf.PosMod(stride + step, 1f);
        }
        // (round 6) a foot down on the pose shown but not held yet (her landing frame): the run's own pace, not the flight's
        if (!BackAirOff && BackDown(stride) >= 0) return natural;
        return strideK < -0.5f ? Stride.Advance(stride, dt * strideK * BackFlight, period) : natural;
    }

    // (t4 round 6, the coordinator's plan; round 5 left the two hip spins on a foot that was down: 180 deg at BackRate while
    // the sim carried her 0.15-0.18 m a frame sideways in her own frame, slip or catch-up whatever the phase) She turns only in
    // the air. Through a backpedal her yaw is held to BackHoldRate deg/s while a foot is down (BackYawMax). When the blow
    // comes, the foot that is down lifts within a frame or two: one whose toe-off is more than BackWait frames off at the
    // run's pace un-lands, her run played back at BackLift of its pace; one further on pushes off at the run's pace,
    // held. Her hips go round in the flight that follows (BackRate), its phase run back so that her rear foot comes down behind
    // her on the turn's last frame (the run's toe-off, BackToeL/R, at the pace that lands it then). Out of it the same: held
    // while the backwards run's foot is down, round in the flight, and she lands on the foot she left from, now in front of
    // her (the run's touchdown, BackLandL/R): a hop round, the phase dipping BackHop back and returning, so no stance is swept
    // and no foot is set down behind her. Which foot is down on a pose is read from its phase (the run's stance spans,
    // BackLandL..BackToeL and BackLandR..BackToeR): the phase set this frame shows next frame. --turn-back-air-off: round 5.
    static readonly bool BackAirOff = SurvivorUnchained.Args.Has("turn-back-air-off");
    // (warden-move solver) The run's stance windows re-measured on the duty-0.26 run (ball under 0.07 m, m3 cast f150-250:
    // L 0.99-0.21, R 0.45-0.75; were 0.98-0.25, 0.46-0.80 on the 0.33 run); the turn's top rate 900 deg/s (30 a frame, judge
    // t1: 34-44 is a whirl, was 1350); a flight up to 4 frames (judge r4: 3-4), its phase at up to 4x the run's pace.
    static readonly float BackHoldRate = SurvivorUnchained.Args.Num("turn-back-hold-rate", 240f),
        BackLift = SurvivorUnchained.Args.Num("turn-back-lift", 2f), BackWait = SurvivorUnchained.Args.Num("turn-back-wait", 1.5f), BackGateM = SurvivorUnchained.Args.Num("turn-back-gate", 0.03f),
        BackLandL = SurvivorUnchained.Args.Num("turn-back-land-l", 0.99f), BackToeL = SurvivorUnchained.Args.Num("turn-back-toe-l", 0.21f),
        BackLandR = SurvivorUnchained.Args.Num("turn-back-land-r", 0.45f), BackToeR = SurvivorUnchained.Args.Num("turn-back-toe-r", 0.75f),
        BackHop = SurvivorUnchained.Args.Num("turn-back-hop", 0.08f), BackHopMin = SurvivorUnchained.Args.Num("turn-back-hop-min", 0.06f),
        BackDone = SurvivorUnchained.Args.Num("turn-back-done", 6f), BackFlyMax = SurvivorUnchained.Args.Num("turn-back-fly-max", 4f),
        BackIn = SurvivorUnchained.Args.Num("turn-back-in", 0.015f);
    // (warden-move, judge r4: "cap every flight at 3-4 frames"; "finish the yaw on the ball of that foot") A flight lasts at
    // most BackFlyLen frames whatever the turn left; what the flight did not turn, the foot it lands on turns on its ball at
    // BackBallRate deg/s (held by the plant lock) until that foot lifts. --turn-back-fly-len 99: round 6's flights.
    static readonly float BackFlyLen = SurvivorUnchained.Args.Num("turn-back-fly-len", 4f), BackBallRate = SurvivorUnchained.Args.Num("turn-back-ball-rate", 600f);
    int backBallFoot = -1;
    // (warden-move, judge r4: "in the air ... lift the pelvis 3-6 cm") Through a backpedal's flight her whole view rises on a
    // half sine, BackAirLift m at its top (the flight planned last frame; 0 on the frame she lands).
    static readonly float BackAirLift = SurvivorUnchained.Args.Num("turn-back-air-lift", 0.05f);
    float BackAirLiftNow() => backpedal && backAirN >= 0 && (backSt == 1 || backSt == 3) && backAirLen > 0
        ? BackAirLift * Mathf.Sin(Mathf.Pi * Mathf.Clamp((backAirN + 0.5f) / (backAirLen + 1f), 0f, 1f)) : 0f;
    // backSt: 0 none, 1 into it (until she lands behind her), 2 the backwards run, 3 out of it (until she lands), 4 landed out
    int backSt, backLiftFoot = -1, backAirN = -1, backAirLen = 1;
    float backAirP0, backAirTo, backGoal;
    bool backWas;

    /// <summary>(round 6) The foot (0 left, 1 right, -1 none) down on the run's pose at phase `ph`.</summary>
    static int BackDown(float ph)
    {
        if (Mathf.PosMod(ph - BackLandL, 1f) < Mathf.PosMod(BackToeL - BackLandL, 1f)) return 0;
        if (Mathf.PosMod(ph - BackLandR, 1f) < Mathf.PosMod(BackToeR - BackLandR, 1f)) return 1;
        return -1;
    }

    /// <summary>(round 6) Her yaw's top rate (deg/s) in a backpedal: BackHoldRate while the foot down on the pose shown stays
    /// down on the next (the phase Carry set last frame), else BackRate.</summary>
    float BackYawMax(float goal)
    {
        backGoal = goal;
        if (BackAirOff || BackDriveOff || AimLegs) return BackRate;
        int f = plantFoot >= 0 ? plantFoot : plantH[0] < PlantTouch && plantH[0] <= plantH[1] ? 0 : plantH[1] < PlantTouch ? 1 : -1;
        // (BackGateM of the cycle either side: a pose's stance can run on a little past the run's own)
        // (a foot un-landing is not held: it is off the ground on the next pose, so her turn starts with it)
        if (f >= 0 && f == backLiftFoot) return BackRate;
        bool held = f >= 0 && (f == backBallFoot || BackDown(stride) == f || BackDown(stride + BackGateM) == f || BackDown(stride - BackGateM) == f);
        if (held && !BackPivotOff) return BackPivotRate(f);
        if (f >= 0 && f == backBallFoot) return BackBallRate;
        return held ? BackHoldRate : BackRate;
    }

    // (warden-move solver: "turn yaw onto a planted foot's ball rather than a long flight") On a foot that is down her yaw
    // goes as fast as the plant lock can hold that ball within BackShiftMax a frame: the ball swings BackPivotK of the cap
    // about her root at |z| (its distance ahead or behind her along her facing), so a ball under her spins her freely and one
    // far out holds her back. At most BackRate, at least BackHoldRate. --turn-back-pivot-off: the hold and ball rates.
    static readonly bool BackPivotOff = SurvivorUnchained.Args.Has("turn-back-pivot-off");
    static readonly float BackPivotK = SurvivorUnchained.Args.Num("turn-back-pivot-k", 0.6f), BackPivotZMin = SurvivorUnchained.Args.Num("turn-back-pivot-zmin", 0.08f);
    float BackPivotRate(int f)
    {
        var b = plantFoot == f ? plantAt : plantPrev[f];
        float yaw = Rotation.Y, z = Mathf.Abs((b.X - GlobalPosition.X) * Mathf.Sin(yaw) + (b.Z - GlobalPosition.Z) * Mathf.Cos(yaw));
        float rate = Mathf.RadToDeg(BackPivotK * BackShiftMax * 30f / Mathf.Max(z, BackPivotZMin));
        return Mathf.Clamp(rate, BackHoldRate, BackRate);
    }

    /// <summary>(round 6) Frames her eased turn (TurnTo at BackRate) needs from here to within BackDone deg of `goal`.</summary>
    int BackSpinLeft(float goal, float dt)
    {
        float err = Mathf.RadToDeg(Mathf.Wrap(goal - Rotation.Y, -Mathf.Pi, Mathf.Pi)), v = turnedLast ? yawVel : 0;
        int n = 0;
        while (Mathf.Abs(err) > BackDone && n < 20)
        {
            v = Mathf.Lerp(v, Mathf.Clamp(err * TurnK, -BackRate, BackRate), 1 - Mathf.Exp(-TurnEase * dt));
            float s = v * dt;
            if (s * err < 0) s = 0; else if (Mathf.Abs(s) > Mathf.Abs(err)) s = err;
            err -= s; n++;
        }
        return n;
    }

    /// <summary>(round 6) This frame's stride phase through a backpedal (Carry): into it, the backwards run, and out of it.</summary>
    float BackPhase(float natural, float dt, float period, float strideK)
    {
        float normal = dt / Mathf.Max(period, 0.1f);
        if (backSt == 0 || !backWas) { backSt = 1; backAirN = -1; backLiftFoot = -1; backBallFoot = -1; }
        if (hipGoal == null && backSt < 3) { backSt = 3; backAirN = -1; backLiftFoot = -1; }
        int down = BackDown(stride);
        if (down >= 0)
        {
            if (backAirN >= 0) { backAirN = -1; backLiftFoot = -1; backBallFoot = down; backSt = backSt == 1 ? 2 : backSt == 3 ? 4 : backSt; }
            if (backSt == 4) return natural;
            if (backSt == 1)
            {
                // (it pushes off only if its toe-off is at most BackWait frames away at the run's pace; else it un-lands)
                float rem = Mathf.PosMod((down == 0 ? BackToeL : BackToeR) - stride, 1f);
                if (backLiftFoot == down || rem > BackWait * normal && plantFoot != down)
                {
                    backLiftFoot = down;
                    return Mathf.PosMod(stride - BackLift * normal, 1f);
                }
            }
            return BackStride(natural, dt, period, strideK);
        }
        backBallFoot = -1;
        if (backSt == 2 || backSt == 4) return BackStride(natural, dt, period, strideK);
        // (in the air into it or out of it: the turn, its landing timed to the turn's last frame)
        if (backAirN < 0)
        {
            backAirN = 0; backAirP0 = stride;
            float best = 9;
            foreach (float c in backSt == 3 ? new[] { BackLandL, BackLandR } : new[] { BackToeL, BackToeR })
            {
                // (aimed BackIn inside the stance, so the landing pose is one the stance holds)
                float d = backSt == 3 ? Mathf.PosMod(c + BackIn - stride, 1f) : -Mathf.PosMod(stride - (c - BackIn), 1f);
                if (Mathf.Abs(d) < Mathf.Abs(best)) best = d;
            }
            backAirTo = best;
            // (the flight's frames planned from the turn left at its start: a goal that moves on, her stick round a curve, does
            // not hold her up in the air)
            backAirLen = Mathf.Clamp(BackSpinLeft(backGoal, dt), 1, (int)BackFlyLen);
        }
        backAirN++;
        int left = Mathf.Max(backAirLen - backAirN, 0);
        float u = Mathf.Min((float)backAirN / backAirLen, 1f);
        float arc = Mathf.Abs(backAirTo) < BackHopMin ? (backSt == 3 ? -1 : 1) * BackHop * Mathf.Sin(Mathf.Pi * u) : 0;
        float next = backAirP0 + backAirTo * u + arc;
        // (turned and not yet down: on to the landing at the run's pace)
        if (left == 0) next = stride + (backSt == 3 ? normal : -normal);
        float step = Mathf.Clamp(Mathf.PosMod(next - stride + 0.5f, 1f) - 0.5f, -BackFlyMax * normal, BackFlyMax * normal);
        return Mathf.PosMod(stride + step, 1f);
    }

    /// <summary>This frame's stride phase while a 180's plan runs (Carry): `natural` is the phase the run's own pace would give.</summary>
    float PivotStride(float natural, float dt, float period)
    {
        if (!pivot || (bool)tree.Get(P_fullShot_active)) { pivotSeg = 0; pivotFoot = -1; return natural; }
        float normal = dt / Mathf.Max(period, 0.1f), plantRel = -PivotAheadM / PivotK;
        if (pivotSeg == 1)
        {
            // (at the run's pace until the last frame, then down onto it: the clip's swing reaches 0.44 m out in front before
            // it comes down, so hurrying through it threw the foot forward and back, 19 m/s; this puts it straight down)
            pivotRel = --pivotLandN <= 0 ? plantRel : Mathf.Min(pivotRel + normal, plantRel);
            if (pivotRel >= plantRel) { pivotRel = plantRel; pivotSeg = 2; }
        }
        else if (pivotSeg == 2)
        {
            float step = Mathf.PosMod(natural - stride, 1f);
            if (plantFoot == pivotFoot)
            {
                // Where the held foot will stand in her frame next frame (her place and yaw run on a frame): the phase that puts
                // the clip's foot there, never back, at most PivotRateMax of the run's pace.
                var at = GlobalPosition + new Vector3(velX, 0, velZ) * dt;
                float yaw = Rotation.Y + Mathf.DegToRad(yawVel * dt);
                float fwd = (plantAt.X - at.X) * Mathf.Sin(yaw) + (plantAt.Z - at.Z) * Mathf.Cos(yaw);
                step = Mathf.Clamp(-fwd / PivotK - pivotRel, 0, PivotRateMax * normal);
            }
            pivotRel += step;
            if (pivotRel >= PivotToeOff || (pivotHeld && plantFoot < 0)) pivotSeg = 0;
        }
        float ph = Mathf.PosMod(PivotMid(pivotFoot) + pivotRel, 1f);
        if (pivotSeg == 0) pivotFoot = -1;
        return ph;
    }

    // The swing's coil: while her shoulders come round onto the blow its wind plays slow (CoilPace of its pace), held at the
    // wind's end (CoilWind of the way to its contact); let go at its pace once they are within CoilTol deg, stop gaining, or
    // at CoilMax frames; then a little quick (CoilCatch) until it has made up the time it lost, never past contact. So the
    // slash leaves on the blow's line (a coil, not a dead hold: A1 judge r2) and the view's contact stays near the hit's.
    double coilAt = -1, coilDebt; bool coilFull, coilCatchOn; float coilRate, coilBest; string coilClip = ""; int coilN;
    void CoilStart(bool full)
    {
        coilFull = full; coilClip = full ? fullClip : upperClip; coilRate = full ? fullSpeed : (float)upperRate;
        coilAt = time; coilDebt = 0; coilCatchOn = false; coilBest = 999; coilN = 0;
    }
    void CoilStep()
    {
        if (coilAt < 0 && !coilCatchOn) return;
        // (lane K, 20 Nov: the AnimationTree parameter names made once, not a StringName from text every frame)
        StringName sc = coilFull ? P_fullScale_scale : P_upperScale_scale;
        bool live = (bool)tree.Get(coilFull ? P_fullShot_active : P_upperShot_active) || coilN == 0;
        string now = coilFull ? fullClip : upperClip;
        if (!live || now != coilClip) { coilAt = -1; coilCatchOn = false; return; }
        // (the shot fired this frame starts on the next Advance: the position read now is the last clip's)
        double pos = coilN == 0 && coilAt >= 0 ? 0 : (float)tree.Get(coilFull ? P_full_current_position : P_upper_current_position);
        double contact = SurvivorUnchained.Content.HerEvents.Contact(coilClip) ?? 0.25;
        float f = (float)(probeDt * 30);
        if (coilAt >= 0)
        {
            float sh = Rotation.Y + Mathf.DegToRad(carriage?.Aim ?? 0);
            float err = Mathf.RadToDeg(Mathf.Abs(Mathf.Wrap(aimFace - sh, -Mathf.Pi, Mathf.Pi)));
            bool stalled = coilN > 0 && err > coilBest - 1.5f * f;
            coilBest = Mathf.Min(coilBest, err);
            if (err > CoilTol && !stalled && coilN < CoilMax / f)
            {
                double pace = pos < CoilWind * contact ? CoilPace : 0;
                tree.Set(sc, coilRate * pace);
                coilDebt += probeDt * coilRate * (1 - pace);
                coilN++;
                return;
            }
            if (SurvivorUnchained.Play.TurnRun.Start >= 0 || TurnLog)
                GD.Print(System.FormattableString.Invariant($"RELEASE {coilN} f err {err:0.0} pos {pos:0.000} contact {contact:0.000} debt {coilDebt:0.000}"));
            coilAt = -1; coilCatchOn = coilDebt > 0;
        }
        if (coilCatchOn && coilDebt > 0 && pos < contact)
        {
            tree.Set(sc, coilRate * CoilCatch);
            coilDebt -= probeDt * coilRate * (CoilCatch - 1);
        }
        else { tree.Set(sc, coilRate); coilCatchOn = false; }
    }

    // ---- (aim-move) the directional legs and the two facing modes ----
    static readonly bool DirLegsOff = SurvivorUnchained.Args.Get("dir-legs") == "off";
    static readonly string[] DirId = { "f", "fl", "fr", "b", "bl", "br" };
    static readonly StringName[] DSeek = DirId.Select(d => new StringName($"parameters/move/dSeek_{d}/seek_request")).ToArray();
    static readonly float DirTurnRate = SurvivorUnchained.Args.Num("dir-turn-rate", 840f);
    /// <summary>Her six run clips (f, fl, fr, b, bl, br) are in the graph (her library has them all).</summary>
    bool dirChain, dirBack;
    bool DirOn => dirChain && !DirLegsOff;
    readonly float[] dirW = new float[6], dirLen = new float[6];
    float dirBackW, dirDelta, dirBlend, dirAlpha;
    /// <summary>The set's forward clip (Mount swaps it: the town run sheathed, the armed run drawn).</summary>
    AnimationNodeAnimation? dirF;
    /// <summary>The cursor's ground point (WorldScene wires it each frame; null on a pad, for bots, off the window).</summary>
    public System.Func<(double X, double Z)?>? Pointer;

    /// <summary>Six run clips, each through its own seek, mixed by pairs into "dirSet", then laid over what fed the output ("dir").</summary>
    void BuildDir(AnimationNodeBlendTree mv, string run, string feeder)
    {
        string[] n = { run, run + "_fl", run + "_fr", run + "_b", run + "_bl", run + "_br" };
        for (int i = 1; i < 6; i++) if (!person.Anim.HasAnimation(n[i])) return;
        for (int i = 0; i < 6; i++)
        {
            dirLen[i] = (float)person.Anim.GetAnimation(n[i]).Length;
            var dn = new AnimationNodeAnimation { Animation = n[i] };
            if (i == 0) dirF = dn;
            mv.AddNode("d_" + DirId[i], dn, new Vector2(1000, 1000 + 100 * i));
            mv.AddNode("dSeek_" + DirId[i], new AnimationNodeTimeSeek(), new Vector2(1200, 1000 + 100 * i));
            mv.ConnectNode("dSeek_" + DirId[i], 0, "d_" + DirId[i]);
        }
        foreach (var nm in new[] { "dFA", "dFB", "dBA", "dBB", "dirSet", "dir" }) mv.AddNode(nm, new AnimationNodeBlend2 { Sync = true }, new Vector2(1500, 1000));
        mv.ConnectNode("dFA", 0, "dSeek_fr"); mv.ConnectNode("dFA", 1, "dSeek_f");
        mv.ConnectNode("dFB", 0, "dFA"); mv.ConnectNode("dFB", 1, "dSeek_fl");
        mv.ConnectNode("dBA", 0, "dSeek_br"); mv.ConnectNode("dBA", 1, "dSeek_b");
        mv.ConnectNode("dBB", 0, "dBA"); mv.ConnectNode("dBB", 1, "dSeek_bl");
        mv.ConnectNode("dirSet", 0, "dFB"); mv.ConnectNode("dirSet", 1, "dBB");
        // (a node's output feeds one input only: free the feeder from the output first)
        mv.DisconnectNode("output", 0);
        mv.ConnectNode("dir", 0, feeder); mv.ConnectNode("dir", 1, "dirSet");
        mv.ConnectNode("output", 0, "dir");
        dirW[0] = 1;
        dirChain = true;
    }

    /// <summary>One frame of the directional legs (Carry): alpha (her travel's heading off her facing), the mode and the six weights
    /// (eased 0.06 s, the back/forward split 0.08 s), the pelvis's turn Delta (0.08 s) into the lower-turn modifier, and the set's blend.</summary>
    void DirFrame(float dt, float w)
    {
        float gs = Mathf.Sqrt(velX * velX + velZ * velZ);
        double alpha = gs > 0.01f ? SurvivorUnchained.Play.LowerTurn.Wrap(Mathf.RadToDeg(Mathf.Atan2(velX, velZ)) - Mathf.RadToDeg(Rotation.Y)) : 0;
        dirAlpha = (float)alpha;
        var r = SurvivorUnchained.Play.DirLegs.Solve(alpha, gs, dirBack);
        dirBack = r.Back;
        float kw = 1 - Mathf.Exp(-dt / 0.06f);
        for (int i = 0; i < 6; i++) dirW[i] += ((float)r.W[i] - dirW[i]) * kw;
        dirBackW = (float)SurvivorUnchained.Play.DirLegs.Ease(dirBackW, r.Back ? 1 : 0, dt, 0.08);
        dirDelta = (float)SurvivorUnchained.Play.DirLegs.Ease(dirDelta, r.Delta, dt, 0.08);
        if (person.Turn != null) person.Turn.Delta = DirOn ? dirDelta : 0;
        float Mix(float a, float b) => a + b > 1e-4f ? b / (a + b) : 0;
        float sf = dirW[0] + dirW[1] + dirW[2], sb = dirW[3] + dirW[4] + dirW[5];
        tree.Set(P_move_dFA_blend_amount, Mix(dirW[2], dirW[0]));
        tree.Set(P_move_dFB_blend_amount, sf > 1e-4f ? dirW[1] / sf : 0f);
        tree.Set(P_move_dBA_blend_amount, Mix(dirW[5], dirW[3]));
        tree.Set(P_move_dBB_blend_amount, sb > 1e-4f ? dirW[4] / sb : 0f);
        tree.Set(P_move_dirSet_blend_amount, dirBackW);
        dirBlend = DirOn ? w : 0;
        tree.Set(P_move_dir_blend_amount, dirBlend);
    }

    /// <summary>(aim-move) Her facing under the directional legs. Always (a cursor): the cursor, standing or moving. Skill, or no
    /// cursor: the strike's side while aimHold lasts, else her travel (the stick if held, else her velocity), standing keeps.
    /// At most DirTurnRate deg/s. False (the old chain decides) in a leap, a dash or a full-body clip.</summary>
    bool DirFace(PlayerState p, float dt, float x, float z, float sp)
    {
        // (judge r5) a soft full shot (a stop, a fidget: it gives way the moment she moves) does not hold her facing: under
        // one the old chain faced her travel, so a backpedal or strafe began turned to the run and pivoted to the cursor ~7 f in.
        if (!p.Alive || p.Leap != null || p.DashT > 0 || ((bool)tree.Get(P_fullShot_active) && !fullSoft && !fullGaveWay)) return false;
        float? goal = null;
        var ptr = Pointer?.Invoke();
        // (warden-move) Sheathed in town there is nothing to aim at: she faces her travel, so her town run (the set's forward
        // clip) carries her and the armed side and back runs only pass through a turn.
        if (Facing.Current == FacingMode.Always && ptr is { } c && !sheath.Sheathed)
        {
            float dx = (float)c.X - x, dz = (float)c.Z - z;
            if (dx * dx + dz * dz > 0.01f) goal = Mathf.Atan2(dx, dz);
        }
        else if (aimHold > 0) goal = aimFace;
        else if (sp > 0.4f) goal = p.StickX * p.StickX + p.StickZ * p.StickZ > 0.01 ? Mathf.Atan2((float)p.StickX, (float)p.StickZ) : Mathf.Atan2((float)p.Vx, (float)p.Vz);
        if (goal is float g)
        {
            float err = Mathf.RadToDeg(Mathf.Wrap(g - Rotation.Y, -Mathf.Pi, Mathf.Pi));
            if (Mathf.Abs(err) < PivotDone || (pivotSign != 0 && Mathf.Sign(err) != pivotSign && 360f - Mathf.Abs(err) > PivotFlipMax)) pivotSign = 0;
            else if (pivotSign == 0 && !PivotAwayOff && Mathf.Abs(err) >= PivotFlipMin && sp < 1f) pivotSign = AwayWay(err);
            else if (pivotSign == 0 && !PivotAwayOff && Mathf.Abs(err) >= 60f && SurvivorUnchained.Play.DirRun.Start >= 0) GD.Print($"PIVOTSKIP err {err:F1} sp {sp:F2}");
            TurnTo(g, dt, DirTurnRate, TurnEase, pivotSign);
        }
        else pivotSign = 0;
        return true;
    }

    // (judge r9, lead r10) A turn in place of PivotFlipMin deg or more goes the way round that carries her blade's heading
    // (level) through the camera's far side, not its near side: swung through the near side, a blade hanging from her fist
    // points at the camera and reads as a cane under her boots; through the far side it shows short and passes behind her.
    // The way is chosen once, as the turn starts (pivotSign), and held to its end. --pivot-away-off: the short way, as before.
    // (judge r10) Only near-half turns (165-195: the long way costs at most 30 deg more): a quarter turn taken the long way
    // reads as a spin against the input and lands 4-6 frames late.
    static readonly bool PivotAwayOff = SurvivorUnchained.Args.Has("pivot-away-off");
    static readonly float PivotFlipMin = SurvivorUnchained.Args.Num("pivot-flip-min", 165f), PivotFlipMax = SurvivorUnchained.Args.Num("pivot-flip-max", 195f), PivotDone = 20f;
    // (A's rig, measured on e12) the drawn blade's level heading against her right side (deg, + toward ahead): the clips' stand
    // carry, and the side carry's set where her sword side faces the camera. Body B: re-measure (ana10.py "hd").
    static readonly float PivotBetaOff = SurvivorUnchained.Args.Num("pivot-beta-off", 25f), PivotBetaOn = SurvivorUnchained.Args.Num("pivot-beta-on", -50f);
    int pivotSign;
    float bladeHead = float.NaN;   // the drawn blade's level heading last frame (deg, as Rotation.Y: atan2(x, z)); NaN: none

    /// <summary>The way round (+1 / -1) for a turn of `err` deg: of the short way and the long way (if no more than
    /// PivotFlipMax deg), the one whose sweep of the blade's level heading (her turn, plus the change of the blade's set in
    /// her fist from now to the goal: PivotBetaOn where her sword side will face the camera, so the side carry holds it,
    /// else PivotBetaOff, the clips' own) passes the camera's near side least; the short way on a tie.</summary>
    int AwayWay(float err)
    {
        int shortWay = err >= 0f ? 1 : -1;
        var cam = GetViewport()?.GetCamera3D();
        if (cam == null) return shortWay;
        var fw = -cam.GlobalBasis.Z;
        if (fw.X * fw.X + fw.Z * fw.Z < 1e-6f) return shortWay;
        float far = Mathf.RadToDeg(Mathf.Atan2(fw.X, fw.Z)), near = far + 180f, face = Mathf.RadToDeg(Rotation.Y);
        float h = float.IsNaN(bladeHead) ? face - 90f + PivotBetaOff : bladeHead;
        float beta0 = Mathf.Wrap(h - (face - 90f), -180f, 180f);
        // her sword (right) side at the goal, against the way to the camera (level): toward it, the carry holds the blade
        float g = Mathf.DegToRad(face + err);
        bool onAt = -Mathf.Cos(g) * -fw.X + Mathf.Sin(g) * -fw.Z > 0f;
        float dBeta = Mathf.Wrap((onAt ? PivotBetaOn : PivotBetaOff) - beta0, -180f, 180f);
        bool Sweeps(float at, float by) { float u = Mathf.Wrap(at - h, -180f, 180f); if (Mathf.Sign(u) != Mathf.Sign(by)) u += Mathf.Sign(by) * 360f; return Mathf.Abs(u) <= Mathf.Abs(by); }
        float longErr = err - shortWay * 360f;
        bool nearShort = Sweeps(near, err + dBeta), nearLong = Sweeps(near, longErr + dBeta);
        int way = nearShort && !nearLong && Mathf.Abs(longErr) <= PivotFlipMax ? -shortWay : shortWay;
        if (SurvivorUnchained.Play.DirRun.Start >= 0) GD.Print($"PIVOT err {err:F1} h {h:F1} beta0 {beta0:F1} on {onAt} dBeta {dBeta:F1} near {near:F1} short {nearShort} long {nearLong} way {way}");
        return way;
    }

    /// <summary>Her pelvis bone's global yaw in the world (deg; its local +Z, so it reads her facing when the rest pose has it so).</summary>
    float PelYaw()
    {
        var sk = person.Skeleton;
        int i = sk.FindBone("pelvis");
        if (i < 0) return 0;
        var z = (sk.GlobalTransform.Basis * sk.GetBoneGlobalPose(i).Basis).Z;
        return Mathf.RadToDeg(Mathf.Atan2(z.X, z.Z));
    }

    /// <summary>(warden-turn) One frame's turn measures (TURN2, --fig8 or --turn-log): body yaw, the waist, her chest's and
    /// pelvis's yaw from the bones, her pelvis on screen, the shots playing.</summary>
    void TurnLog2(double t)
    {
        var sk = person.Skeleton;
        Vector3 B(string n) { int i = sk.FindBone(n); return i < 0 ? GlobalPosition : sk.GlobalTransform * sk.GetBoneGlobalPose(i).Origin; }
        float Yaw(string l, string r) { var d = B(l) - B(r); return Mathf.RadToDeg(Mathf.Atan2(-d.Z, d.X)); }
        var cam = GetViewport()?.GetCamera3D();
        var pv = B("pelvis");
        var s = cam != null ? cam.UnprojectPosition(pv) : Vector2.Zero;
        bool up = (bool)tree.Get(P_upperShot_active), fu = (bool)tree.Get(P_fullShot_active);
        if (!feetHooked) { feetHooked = true; sk.SkeletonUpdated += FeetCache; RenderingServer.FramePreDraw += Scr2; }
        GD.Print(System.FormattableString.Invariant($"TURN2 {t:0.0000} face {Mathf.RadToDeg(Rotation.Y):0.0} waist {carriage?.Aim ?? 0:0.0} chest {Yaw("upperarm_l", "upperarm_r"):0.0} pelv {Yaw("thigh_l", "thigh_r"):0.0} scr {s.X:0.0} {s.Y:0.0} anim {speed:0.00} up {(up ? upperClip : "-")} full {(fu ? fullClip : "-")} coil {(coilAt >= 0 ? 1 : 0)} ph {stride:0.000} spd {logSpd:0.00} w {logW:0.00} ww {logWWalk:0.00} bl {feetW[0].X:0.000} {feetW[0].Y:0.000} {feetW[0].Z:0.000} br {feetW[1].X:0.000} {feetW[1].Y:0.000} {feetW[1].Z:0.000} pos {GlobalPosition.X - plantOff.X - smoothOff.X:0.000} {GlobalPosition.Z - plantOff.Z - smoothOff.Z:0.000} pl {plantFoot} off {plantOff.X + smoothOff.X:0.000} {plantOff.Z + smoothOff.Z:0.000} hl {plantH[0]:0.000} hr {plantH[1]:0.000} pp {pivotSeg} {pivotFoot} pz {B("pelvis").Y - GlobalPosition.Y:0.000} tilt {carriage?.Tilt ?? 0:0.0} pw {pelvW.X:0.000} {pelvW.Z:0.000} ppm {(cam != null ? (cam.UnprojectPosition(pv + Vector3.Right) - s).Length() : 0):0.0} sm {(smoothOn ? 1 : 0)} {smoothOff.Length():0.000} {smoothCalls} kn {legBend[0]:0} {legBend[1]:0} th {legThigh[0]:0} {legThigh[1]:0} dl {dirDelta:0.0} dw {dirW[0]:0.00} {dirW[1]:0.00} {dirW[2]:0.00} {dirW[3]:0.00} {dirW[4]:0.00} {dirW[5]:0.00} dir {dirBlend:0.00} al {dirAlpha:0.0} pel {PelYaw():0.0}"));
        smoothCalls = 0;
    }
    // (turning measure) her balls of the feet in the world where the skeleton has run its modifiers (see MeasCache's note)
    bool feetHooked; float logW, logWWalk, logSpd;
    readonly Vector3[] feetW = new Vector3[2];
    void FeetCache()
    {
        var sk = person.Skeleton;
        // (aim-move) BODY2's joints, taken here: after the modifiers (SkeletonUpdated); a FramePreDraw read sees the pose they restored
        for (int bi = 0; bi < BodyBones.Length; bi++) { int bx = sk.FindBone(BodyBones[bi]); if (bx < 0 && BodyBones[bi] == "head") bx = sk.FindBone("Head"); bodyW[bi] = bx >= 0 ? sk.GlobalTransform * sk.GetBoneGlobalPose(bx).Origin : Vector3.Zero; }
        { int hx = sk.FindBone("Head"); if (hx < 0) hx = sk.FindBone("head"); headW = hx >= 0 ? sk.GlobalTransform * sk.GetBoneGlobalPose(hx).Origin : Vector3.Zero; }
        int l = sk.FindBone("ball_l"), r = sk.FindBone("ball_r");
        if (l >= 0) feetW[0] = sk.GlobalTransform * sk.GetBoneGlobalPose(l).Origin;
        if (r >= 0) feetW[1] = sk.GlobalTransform * sk.GetBoneGlobalPose(r).Origin;
        int pb = sk.FindBone("pelvis");
        if (pb >= 0) pelvW = sk.GlobalTransform * sk.GetBoneGlobalPose(pb).Origin;
        // (warden-move) each leg's knee bend (deg, 0 straight) and thigh angle off vertical along her facing (+ behind)
        var fwd = sk.GlobalTransform.Basis.Z.Normalized();
        for (int s = 0; s < 2; s++)
        {
            string x = s == 0 ? "_l" : "_r";
            int a = sk.FindBone("thigh" + x), b = sk.FindBone("calf" + x), c = sk.FindBone("foot" + x);
            if (a < 0 || b < 0 || c < 0) continue;
            Vector3 H = sk.GetBoneGlobalPose(a).Origin, K = sk.GetBoneGlobalPose(b).Origin, F = sk.GetBoneGlobalPose(c).Origin;
            kneeW[s] = sk.GlobalTransform * K;   // (warden-move, BLADE: the blade's clearance from her legs)
            legBend[s] = Mathf.RadToDeg((K - H).AngleTo(F - K));
            var u = sk.GlobalTransform.Basis * (K - H);
            legThigh[s] = Mathf.RadToDeg(Mathf.Atan2(-u.Dot(fwd), -u.Y));
        }
    }
    readonly float[] legBend = new float[2], legThigh = new float[2];
    readonly Vector3[] kneeW = new Vector3[2];
    Vector3 headW;
    Vector3 pelvW;
    /// <summary>(warden-move, judge r4: the sheets' crops sat 15-23 px ahead of her body) Her pelvis on screen as the frame is
    /// drawn (SCR2 x y, one line a drawn frame): the final camera and pose, which TURN2's scr (taken in her _Process, before
    /// the camera's and the skeleton's update) is not. View-only log.</summary>
    void Scr2()
    {
        if (!IsInsideTree() || person?.Skeleton is not { } sk) return;
        var cam = GetViewport()?.GetCamera3D();
        int pb = sk.FindBone("pelvis");
        if (cam == null || pb < 0) return;
        var s = cam.UnprojectPosition(sk.GlobalTransform * sk.GetBoneGlobalPose(pb).Origin);
        var c = cam.GlobalPosition;   // (warden-move item 3: the camera's world place, for its catch-up after a 180)
        GD.Print(System.FormattableString.Invariant($"SCR2 {s.X:0.0} {s.Y:0.0} cam {c.X:0.000} {c.Y:0.000} {c.Z:0.000}"));
        // (aim-move) BODY2: the drawn pose's joints in the world (x y z each), for the rows' measures (aim_move\tools\rows.py):
        // the hips' line (thigh_l, thigh_r), the ankles, the balls, the shoulders' line (upperarm_l, upperarm_r), the hands,
        // spine_03 and the head; then her facing (deg).
        if (Args.Has("dirrun") || Args.Has("body-log"))
        {
            var sb = new System.Text.StringBuilder("BODY2");
            foreach (var w in bodyW)
            {
                sb.Append(System.FormattableString.Invariant($" {w.X:0.0000} {w.Y:0.0000} {w.Z:0.0000}"));
            }
            sb.Append(System.FormattableString.Invariant($" face {Mathf.RadToDeg(Rotation.Y):0.00}"));
            GD.Print(sb.ToString());
            // (warden-move, side carry) BLADE: the right piece as drawn, on screen (px): its grip point, its tip, then the right
            // fist, the head and both feet and balls (BODY2's joints); then the grip and tip in the world, the tilt axis (the
            // palm's normal), and the side carry's weight and added tilt (deg). View-only log.
            if (view?.BladeOf("handslot.r") is { } bd)
            {
                Vector2 P(Vector3 v) => cam.UnprojectPosition(v);
                Vector2 g = P(bd.Grip), tp = P(bd.Tip), hr = P(bodyW[9]), hd = P(headW), fl = P(bodyW[2]), fr = P(bodyW[3]), bl = P(bodyW[4]), br = P(bodyW[5]);
                GD.Print(System.FormattableString.Invariant($"BLADE {g.X:0.0} {g.Y:0.0} {tp.X:0.0} {tp.Y:0.0} hr {hr.X:0.0} {hr.Y:0.0} hd {hd.X:0.0} {hd.Y:0.0} ft {fl.X:0.0} {fl.Y:0.0} {fr.X:0.0} {fr.Y:0.0} {bl.X:0.0} {bl.Y:0.0} {br.X:0.0} {br.Y:0.0} gw {bd.Grip.X:0.0000} {bd.Grip.Y:0.0000} {bd.Grip.Z:0.0000} tw {bd.Tip.X:0.0000} {bd.Tip.Y:0.0000} {bd.Tip.Z:0.0000} ax {bd.Axis.X:0.000} {bd.Axis.Y:0.000} {bd.Axis.Z:0.000} kn {kneeW[0].X:0.0000} {kneeW[0].Y:0.0000} {kneeW[0].Z:0.0000} {kneeW[1].X:0.0000} {kneeW[1].Y:0.0000} {kneeW[1].Z:0.0000} sc {carry.Weight:0.000} {carry.Tilt:0.00} {carry.Spring:0.00} {carry.Inward:0.00} face {Mathf.RadToDeg(Rotation.Y):0.00} sv {carry.Want:0.00} {carry.Raw:0.00} {carry.Sigma:0} {logWWalk:0.00} {carryStrafe:0.00} c0 {P(bd.Grip + carryB0 * (bd.Tip - bd.Grip).Length()).X:0.0} {P(bd.Grip + carryB0 * (bd.Tip - bd.Grip).Length()).Y:0.0}"));
            if (Args.Has("blade-mask")) BladeMaskPrep(cam);
            if (Args.Has("hide-blade")) HideBlade();
            }
        }
    }
    // (warden-move, --hide-blade, shoot only) the blade's own pixels vanish, its shadow stays: every mesh under the right-hand mount
    // casts shadows only. A twin shoot of the same run, diffed against the normal one offline (tools/anim/fit/blade_contrast.py).
    void HideBlade()
    {
        if (view?.HeldIn("handslot.r") is not { } mount) return;
        var stack = new Stack<Node>(); stack.Push(mount);
        while (stack.Count > 0)
            foreach (var ch in stack.Pop().GetChildren())
            {
                stack.Push(ch);
                if (ch is MeshInstance3D mi) mi.CastShadow = GeometryInstance3D.ShadowCastingSetting.ShadowsOnly;
            }
    }
    // (aim-move r13, --blade-mask, log only) T4 by pixels: the held blade's meshes move to layer 19 (the main camera still draws
    // them), each gets a flat magenta twin on layer 20 that the main camera skips. Two half-size SubViewports on the same world, each
    // with a camera copying the main one: FULL draws her and the people (layer 2, her layers) + magenta, depth-tested (not the scene), SOLO draws layer 20 only.
    // After the frame is drawn BMASK vis tot: magenta pixels in FULL, blade pixels in SOLO (same frame as that frame's BLADE line).
    const uint MaskReal = 1u << 5, MaskTwin = 1u << 6, MaskOld = 2;   // (free bits; the blade came on layer 2, the people's)
    SubViewport? maskFull, maskSolo; Camera3D? maskCamF, maskCamS;
    readonly List<(MeshInstance3D real, MeshInstance3D twin)> maskPairs = new();
    Node3D? maskMount; bool maskPending, maskHooked;
    void BladeMaskPrep(Camera3D cam)
    {
        if (view?.HeldIn("handslot.r") is not { } mount) return;
        if (maskFull == null)
        {
            SubViewport Mk(uint cull, out Camera3D c)
            {
                var vp = new SubViewport { Size = new Vector2I(960, 540), TransparentBg = true, Msaa3D = Viewport.Msaa.Disabled, UseTaa = false, ScreenSpaceAA = Viewport.ScreenSpaceAAEnum.Disabled, Scaling3DMode = Viewport.Scaling3DModeEnum.Bilinear, RenderTargetUpdateMode = SubViewport.UpdateMode.Always, HandleInputLocally = false };
                c = new Camera3D { Current = true, CullMask = cull };
                vp.AddChild(c); AddChild(vp); return vp;
            }
            maskFull = Mk(MaskOld | HerLayers | MaskTwin, out maskCamF);   // (lead r13, e28: the den's roots and overhangs hid the blade 15 f in a run: T4 is her body hiding it, so only she occludes)
            maskSolo = Mk(MaskTwin, out maskCamS);   // (r14: this statement had slipped into the comment above in a4ffa6f32: SOLO null, no BMASK lines in e29/e30)
            if (!maskHooked) { maskHooked = true; RenderingServer.FramePostDraw += BladeMaskCount; }
        }
        if (maskMount != mount)
        {
            maskMount = mount; maskPairs.Clear();
            var mat = new StandardMaterial3D { ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, AlbedoColor = new Color(1, 0, 1), DisableFog = true };
            var stack = new Stack<Node>(); stack.Push(mount);
            while (stack.Count > 0)
                foreach (var ch in stack.Pop().GetChildren())
                {
                    stack.Push(ch);
                    if (ch is not MeshInstance3D mi || mi.Mesh == null || mi.Layers != MaskOld) continue;
                    var twin = new MeshInstance3D { Mesh = mi.Mesh, Transform = mi.Transform, MaterialOverride = mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, Layers = MaskTwin, Visible = mi.IsVisibleInTree() };
                    mi.GetParent().AddChild(twin); mi.Layers = MaskReal; maskPairs.Add((mi, twin));
                }
        }
        foreach (var (real, twin) in maskPairs)
            if (IsInstanceValid(real) && IsInstanceValid(twin)) { twin.Transform = real.Transform; twin.Visible = real.Visible; }
        cam.CullMask &= ~MaskTwin;
        // the blade left layer 2, so every light and decal that took layer 2 takes its new one too: lit and shadowed as before
        foreach (var n in GetTree().Root.FindChildren("*", "Node3D", true, false))
            if (n is Light3D lt) { if ((lt.LightCullMask & MaskOld) != 0) lt.LightCullMask |= MaskReal; }
            else if (n is Decal dc) { if ((dc.CullMask & MaskOld) != 0) dc.CullMask |= MaskReal; }
        foreach (var c in new[] { maskCamF!, maskCamS! })
        {
            c.GlobalTransform = cam.GlobalTransform; c.Projection = cam.Projection; c.Fov = cam.Fov; c.Size = cam.Size; c.KeepAspect = cam.KeepAspect;
            c.Near = cam.Near; c.Far = cam.Far; c.Environment = cam.Environment; c.Attributes = cam.Attributes;
        }
        maskPending = true;
    }
    void BladeMaskCount()
    {
        if (!maskPending || maskFull == null || maskSolo == null) return;
        maskPending = false;
        int vis = 0, tot = 0;
        var a = maskFull.GetTexture().GetImage(); var b = maskSolo.GetTexture().GetImage();
        if (a != null && a.GetFormat() != Image.Format.Rgba8) a.Convert(Image.Format.Rgba8);
        if (b != null && b.GetFormat() != Image.Format.Rgba8) b.Convert(Image.Format.Rgba8);
        if (a != null) { var d = a.GetData(); for (int i = 0; i + 3 < d.Length; i += 4) if (d[i] > 178 && d[i + 2] > 178 && d[i + 1] < 77) vis++; }
        // (the camp fire shows on layer 20 too: alpha alone counts it, so the colour is tested as well)
        if (b != null) { var d = b.GetData(); for (int i = 0; i + 3 < d.Length; i += 4) if (d[i + 3] > 127 && d[i] > 178 && d[i + 2] > 178 && d[i + 1] < 77) tot++; }
        GD.Print($"BMASK {vis} {tot}");
    }
    readonly Vector3[] bodyW = new Vector3[15];
    static readonly string[] BodyBones = { "thigh_l", "thigh_r", "foot_l", "foot_r", "ball_l", "ball_r", "upperarm_l", "upperarm_r", "hand_l", "hand_r", "spine_03", "head", "pelvis", "lowerarm_r", "lowerarm_l" };
    public override void _ExitTree()
    {
        if (feetHooked) RenderingServer.FramePreDraw -= Scr2;
        if (maskHooked) RenderingServer.FramePostDraw -= BladeMaskCount;
        if (carryHooked && person?.Skeleton is { } sk && IsInstanceValid(sk)) sk.SkeletonUpdated -= CarryPosed;
        base._ExitTree();
    }

    // (warden-move) The side carry (SideCarry): the sword turned in her fist while her sword side faces the camera. Stepped
    // once her pose is made (SkeletonUpdated, as HairSway is: the modifiers' arm in it), so the grip's acceleration and the
    // tilt's sign are this frame's. --side-carry off: none (the clips' grip, as before); --side-carry-tune
    // runangle,gain,hz,damping,loose,ease,maxrate,splay,loosefwd,maxaccel,standangle,strafecut,splayaway,splaystrafe,backmax,caproom,side0,side1,
    // fadeout,screenrate,edge,splayoutmax,standsettle,floor,inmax,clear,outmax,clearrate,clearatk,cleardown,clearlook:
    // its tuning (SideCarry's fields, in that order).
    readonly SideCarry carry = CarryTuned();
    static readonly bool CarryOn = SurvivorUnchained.Args.Get("side-carry") is not ("off" or "0");
    bool carryHooked;
    float carryDt;
    Vector3 carryAt, carryV;
    int carryHist;
    static SideCarry CarryTuned()
    {
        var c = new SideCarry();
        if (SurvivorUnchained.Args.Get("side-carry-tune") is { } t)
        {
            var v = t.Split(',');
            float F(int i, float d) => i < v.Length && float.TryParse(v[i], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var x) ? x : d;
            c.RunAngle = F(0, c.RunAngle); c.Gain = F(1, c.Gain); c.Hz = F(2, c.Hz); c.Damping = F(3, c.Damping);
            c.Loose = F(4, c.Loose); c.Ease = F(5, c.Ease); c.MaxRate = F(6, c.MaxRate); c.Splay = F(7, c.Splay); c.LooseFwd = F(8, c.LooseFwd); c.MaxAccel = F(9, c.MaxAccel);
            c.StandAngle = F(10, c.StandAngle); c.StrafeCut = F(11, c.StrafeCut); c.SplayAway = F(12, c.SplayAway); c.SplayStrafe = F(13, c.SplayStrafe);
            c.BackMax = F(14, c.BackMax); c.CapRoom = F(15, c.CapRoom); c.Side0 = F(16, c.Side0); c.Side1 = F(17, c.Side1);
            c.FadeOut = F(18, c.FadeOut); c.ScreenRate = F(19, c.ScreenRate); c.Edge = F(20, c.Edge); c.SplayOutMax = F(21, c.SplayOutMax);
            c.StandSettle = F(22, c.StandSettle); c.Floor = F(23, c.Floor); c.InMax = F(24, c.InMax);
            c.Clear = F(25, c.Clear); c.OutMax = F(26, c.OutMax); c.ClearRate = F(27, c.ClearRate); c.ClearAtk = F(28, c.ClearAtk);
            c.ClearDown = F(29, c.ClearDown); c.ClearLook = (int)F(30, c.ClearLook);
            c.InReach = F(31, c.InReach); c.ClearReach = F(32, c.ClearReach); c.DownBand = F(33, c.DownBand); c.Hold = F(34, c.Hold); c.CarryRate = F(35, c.CarryRate); c.TurnEnd = F(36, c.TurnEnd); c.Cross = F(37, c.Cross ? 1f : 0f) > 0f;
        }
        // (r22) --far-cap away,across,toward,spanToward,spanAway: the far side's facing cap (SideCarry.FarCapAt).
        if (SurvivorUnchained.Args.Get("far-cap") is { } fc)
        {
            var v = fc.Split(',');
            float F(int i, float d) => i < v.Length && float.TryParse(v[i], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var x) ? x : d;
            c.FarCapAway = F(0, c.FarCapAway); c.FarCapAcross = F(1, c.FarCapAcross); c.FarCapToward = F(2, c.FarCapToward);
            c.FarCapSpanToward = F(3, c.FarCapSpanToward); c.FarCapSpanAway = F(4, c.FarCapSpanAway);
        }
        return c;
    }

    void CarryPosed()
    {
        if (!IsInstanceValid(this) || !IsInsideTree() || view == null || person?.Skeleton is not { } sk) return;
        float d = carryDt;
        carryDt = 0f;
        if (!(d > 0f)) return;
        int hb = sk.FindBone("hand_r");
        if (hb < 0) return;
        // The fist's acceleration along her travel (level), from its last two drawn places; a jump (a cut, a teleport) restarts it.
        var at = sk.GlobalTransform * sk.GetBoneGlobalPose(hb).Origin;
        var fwd = new Vector3(GlobalBasis.Z.X, 0f, GlobalBasis.Z.Z);
        fwd = fwd.LengthSquared() > 1e-8f ? fwd.Normalized() : Vector3.Back;
        float acc = 0f;
        if (carryHist > 0 && at.DistanceTo(carryAt) > 1.5f) carryHist = 0;
        if (carryHist >= 1)
        {
            var v = (at - carryAt) / d;
            if (carryHist >= 2) acc = (v - carryV).Dot(fwd) / d;
            carryV = v;
        }
        carryAt = at;
        carryHist = System.Math.Min(carryHist + 1, 2);
        // Her travel (level), for the strafe's share of it; eased.
        var pos = GlobalPosition;
        if (carryHist > 1 && pos.DistanceTo(carryPos) < 1.5f)
        {
            var vel = (pos - carryPos) / d;
            vel.Y = 0f;
            float sp = vel.Length(), sw = sp > 0.3f ? Mathf.Abs(vel.Dot(GlobalBasis.X.Normalized())) / sp * Mathf.Clamp((sp - 0.3f) / 0.7f, 0f, 1f) : 0f;
            carryStrafe += (sw - carryStrafe) * (1f - Mathf.Exp(-d / 0.15f));
            // (judge r4, solver 17) How much she moves, from her own speed (none under 0.3 m/s, full from 4.3): prompt at a
            // stop, where the walk weight (logWWalk) holds full ~5 frames after she has stopped (the stand's angle came late).
            carryMove = Mathf.Clamp((sp - 0.3f) / 4f, 0f, 1f);
        }
        carryPos = pos;
        var cam = GetViewport()?.GetCamera3D();
        var bone = sk.GlobalTransform * sk.GetBoneGlobalPose(hb);
        bool on = CarryOn && !held && TourList == null && grips && cam != null;
        var f = default(SideCarry.Frame);
        if (on)
        {
            // The clip's grip first (the layer reads the blade as the clips hold it), then the camera's screen map at its grip.
            view.Slide("handslot.r", slide, tilt);
            if (view.HeldBlade("handslot.r", bone) is { } hbd && (hbd.Tip - hbd.Grip).LengthSquared() > 1e-6f)
            {
                var g = hbd.Grip;
                var p0 = cam!.UnprojectPosition(g);
                const float e = 0.05f;
                Vector2 dx = (cam.UnprojectPosition(g + Vector3.Right * e) - p0) / e, dy = (cam.UnprojectPosition(g + Vector3.Up * e) - p0) / e,
                    dz = (cam.UnprojectPosition(g + Vector3.Back * e) - p0) / e;
                static System.Numerics.Vector3 N(Vector3 v) => new(v.X, v.Y, v.Z);
                var lf = new Vector3(GlobalBasis.X.X, 0f, GlobalBasis.X.Z);
                var ah = new Vector3(GlobalBasis.Z.X, 0f, GlobalBasis.Z.Z);
                carryB0 = (hbd.Tip - hbd.Grip).Normalized();
                // (judge r4, solver 18) her calves (knee: the calf bone's head; ankle: the foot's), for the blade's clearance
                Vector3 J(string n) { int x = sk.FindBone(n); return x >= 0 ? sk.GlobalTransform * sk.GetBoneGlobalPose(x).Origin : g; }
                f = new SideCarry.Frame(N(carryB0), N(lf), N(ah), new(dx.X, dy.X, dz.X), new(dx.Y, dy.Y, dz.Y), N(cam.GlobalBasis.Z),
                    Mathf.Min(Mathf.Clamp(logWWalk, 0f, 1f), carryMove), carryStrafe, N(g), (hbd.Tip - hbd.Grip).Length(),
                    N(J("calf_l")), N(J("foot_l")), N(J("calf_r")), N(J("foot_r")));
            }
            else on = false;
        }
        carry.Step(d, on, acc, f);
        if (on)
        {
            var lv = new Vector3(GlobalBasis.X.X, 0f, GlobalBasis.X.Z); var av = new Vector3(GlobalBasis.Z.X, 0f, GlobalBasis.Z.Z);
            if (lv.LengthSquared() > 1e-8f && av.LengthSquared() > 1e-8f)
            {
                lv = lv.Normalized(); av = av.Normalized();
                var dd = SideCarry.Turned(new(carryB0.X, carryB0.Y, carryB0.Z), new(lv.X, lv.Y, lv.Z), carry.Tilt, new(av.X, av.Y, av.Z), carry.Inward);
                bladeHead = dd.X * dd.X + dd.Z * dd.Z > 0.01f ? Mathf.RadToDeg(Mathf.Atan2(dd.X, dd.Z)) : float.NaN;
            }
        }
        else bladeHead = float.NaN;
        if (grips) CarrySlide(bone);
    }
    Vector3 carryPos, carryB0;
    float carryStrafe, carryMove;

    /// <summary>Her right piece gripped as the clips grip it (slide, tilt), then the side carry's turns on it: tip back about
    /// her left (level; + tips the blade behind her), and in toward her body about her facing (level), through the fist.</summary>
    void CarrySlide(Transform3D? bone)
    {
        var left = new Vector3(GlobalBasis.X.X, 0f, GlobalBasis.X.Z);
        var ahead = new Vector3(GlobalBasis.Z.X, 0f, GlobalBasis.Z.Z);
        if (left.LengthSquared() < 1e-8f || ahead.LengthSquared() < 1e-8f) { view?.Slide("handslot.r", slide, tilt); return; }
        view?.Slide("handslot.r", slide, tilt, left.Normalized(), carry.Tilt, ahead.Normalized(), carry.Inward, bone);
    }
    bool held;
    static readonly float HeadLevel = SurvivorUnchained.Args.Has("head-level") ? SurvivorUnchained.Args.Num("head-level", 0.8f) : 0.8f;
}

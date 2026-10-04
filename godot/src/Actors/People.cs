using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// People from the Quaternius parts the web game uses (res://assets/people):
/// a base body, outfit pieces and hair moved onto the body's skeleton (every
/// part is rigged to the same 65 bones, Armature/Skeleton3D), and the
/// Universal Animation Libraries shared by all of them.
/// </summary>
public static class People
{
    public sealed record Look(
        string Sex, string[] Outfit, string? Hair = null, bool Beard = false,
        Color? HairColor = null, Color? Skin = null, Color? Cloth = null, Color? Under = null, double Figure = 0,
        IReadOnlyDictionary<string, float>? Face = null, Color? Eyes = null, Color? EyeRing = null, string? Paint = null,
        string? FaceShape = null);

    public static readonly string[] MaleRanger = { "Male_Ranger_Arms", "Male_Ranger_Body", "Male_Ranger_Legs", "Male_Ranger_Feet_Boots" };
    public static readonly string[] MalePeasant = { "Male_Peasant_Arms", "Male_Peasant_Body", "Male_Peasant_Legs", "Male_Peasant_Feet" };
    public static readonly string[] FemalePeasant = { "Female_Peasant_Arms", "Female_Peasant_Body", "Female_Peasant_Legs", "Female_Peasant_Feet" };

    const string Dir = "res://assets/people";
    static readonly List<AnimationLibrary> libraries = new();

    /// <summary>Every clip, from both libraries, by name.</summary>
    public static AnimationLibrary Clips()
    {
        if (libraries.Count > 0) return libraries[0];
        var all = new AnimationLibrary();
        foreach (var file in new[] { "UAL1.glb", "UAL2.glb" })
        {
            var scene = GD.Load<PackedScene>($"{Dir}/{file}").Instantiate();
            var ap = scene.FindChild("AnimationPlayer", true, false) as AnimationPlayer;
            foreach (var libName in ap!.GetAnimationLibraryList())
            {
                var lib = ap.GetAnimationLibrary(libName);
                foreach (var name in lib.GetAnimationList())
                    if (!all.HasAnimation(name)) all.AddAnimation(name, lib.GetAnimation(name));
            }
            scene.Free();
        }
        // Loops for the clips that are cycles.
        foreach (var name in all.GetAnimationList())
            if (IsCycle(name)) all.GetAnimation(name).LoopMode = Animation.LoopModeEnum.Linear;
        libraries.Add(all);
        return all;
    }

    /// <summary>The game names clips in KayKit's words; a person plays the
    /// library clip that does the same thing (the web game's HUMAN_CLIPS).</summary>
    static readonly Dictionary<string, string> Aliases = new()
    {
        ["Idle"] = "Idle_Loop", ["Idle_B"] = "Idle_Loop", ["Idle_Combat"] = "Sword_Idle", ["2H_Melee_Idle"] = "Sword_Idle", ["Unarmed_Idle"] = "Idle_Loop",
        ["Walking_A"] = "Walk_Loop", ["Walking_B"] = "Walk_Loop", ["Walking_C"] = "Walk_Formal_Loop", ["Walking_D_Skeletons"] = "Zombie_Walk_Fwd_Loop",
        ["Running_A"] = "Jog_Fwd_Loop", ["Running_B"] = "Sprint_Loop",
        ["1H_Melee_Attack_Chop"] = "Sword_Regular_A", ["1H_Melee_Attack_Slice_Diagonal"] = "Sword_Regular_B", ["1H_Melee_Attack_Slice_Horizontal"] = "Sword_Regular_C",
        ["1H_Melee_Attack_Stab"] = "Sword_Regular_A", ["2H_Melee_Attack_Chop"] = "Sword_Attack", ["2H_Melee_Attack_Slice"] = "Sword_Attack",
        ["2H_Melee_Attack_Spin"] = "Sword_Heavy_Combo", ["Dualwield_Melee_Attack_Slice"] = "Sword_Regular_Combo", ["Unarmed_Melee_Attack_Punch_A"] = "Punch_Jab",
        ["Spellcast_Shoot"] = "Spell_Simple_Shoot", ["Spellcast_Raise"] = "Spell_Simple_Enter", ["Spellcast_Summon"] = "Spell_Simple_Enter", ["Spellcasting"] = "Spell_Simple_Idle_Loop",
        ["Throw"] = "OverhandThrow", ["1H_Ranged_Shoot"] = "Pistol_Shoot", ["2H_Ranged_Shoot"] = "Pistol_Shoot",
        ["Sit_Floor_Idle"] = "Crouch_Idle_Loop", ["Sit_Chair_Idle"] = "Sitting_Idle_Loop", ["Interact"] = "Interact", ["PickUp"] = "PickUp_Table", ["Use_Item"] = "Consume",
        ["Death_A"] = "Death01", ["Death_B"] = "Death01", ["Death_A_Pose"] = "Death01", ["Death_C_Skeletons"] = "Death01",
        ["Hit_A"] = "Hit_Chest", ["Hit_B"] = "Hit_Head", ["Cheer"] = "Yes", ["Taunt"] = "Punch_Cross", ["Block"] = "Sword_Block", ["Blocking"] = "Idle_Shield_Loop",
        ["Lie_StandUp"] = "LayToIdle", ["Dodge_Forward"] = "Roll", ["Jump_Full_Short"] = "NinjaJump_Start", ["Wave"] = "Yes",
    };

    /// <summary>A clip as the library has it in Godot: the game's name, its
    /// alias, and without the '_Loop' the importer takes off (it loops them).</summary>
    public static string Resolve(string name)
    {
        var lib = Clips();
        if (Aliases.TryGetValue(name, out var a)) name = a;
        if (lib.HasAnimation(name)) return name;
        if (name.EndsWith("_Loop") && lib.HasAnimation(name[..^5])) return name[..^5];
        return lib.HasAnimation("Idle") ? "Idle" : name;
    }

    /// <summary>A person as the game specifies one (World.PersonSpec): the
    /// body, the outfit, hair and beard, skin, and the dye on the cloth.</summary>
    /// <summary>A person as the game specifies one, as the view puts them together.</summary>
    public static Look LookOf(SurvivorUnchained.World.PersonSpec spec)
    {
        static Color? C(string? hex) => string.IsNullOrEmpty(hex) ? null : new Color(hex);
        var sex = spec.Sex == SurvivorUnchained.Rpg.Sex.Female ? "female" : "male";
        var outfit = spec.Outfit?.ToArray() ?? (sex == "female" ? FemalePeasant : MalePeasant);
        return new Look(sex, outfit, spec.Hair, spec.Beard == true, C(spec.HairColor), C(spec.Skin), C(spec.Dye?.Cloth), C(spec.Dye?.Under),
            sex == "female" ? spec.Figure ?? 1 : 0, spec.Face?.ToDictionary(f => f.Key, f => (float)f.Value), C(spec.Eyes), C(spec.EyeRing), spec.Paint, spec.FaceShape);
    }

    public static Person Build(SurvivorUnchained.World.PersonSpec spec)
    {
        var look = LookOf(spec);
        var body = spec.Body;
        // The woman survivor is the heroine (tools/assets/build_heroine.py),
        // in her calling's outfit; --body woman brings back the older body.
        if (body == SurvivorUnchained.Play.Loadouts.HerBody && Args.Get("body") != "woman" && ResourceLoader.Exists("res://art/people/heroine.glb")) body = "heroine";
        var p = body switch { SurvivorUnchained.Play.Loadouts.HerBody => Woman(look), "heroine" => Heroine(look), "anime" => Her(look), _ => Build(look) };
        // Her own clips are chosen by her calling, which her outfit says.
        if (body == "heroine") p.Calling = HerClips.Calling(look.Outfit);
        // Her body wears her calling's outfit, cut from it.
        if (body == "heroine" && look.Outfit.FirstOrDefault(o => o.StartsWith("her:")) is string her) HerOutfit(p, her[4..]);
        // Her hair, a mesh of its own: the style chosen if it is one of hers;
        // her face shaped, and the paint on it.
        if (body == "heroine")
        {
            HerHair(p, HerHairs.Contains(look.Hair) ? look.Hair! : HerHairs[0], look.HairColor ?? HerHairColour);
            if (look.Face != null) HerFace(p, look.Face);
            HerPaint(p, look.Paint);
            p.FaceShape = look.FaceShape;                 // (its painting laid as her skin was made: Skin)
        }
        // A child's larger head.
        if (spec.Head is double h && h != 1)
        {
            int head = p.Skeleton.FindBone("Head");
            if (head >= 0) p.Skeleton.SetBonePoseScale(head, Vector3.One * (float)h);
        }
        return p;
    }

    static bool IsCycle(string n) =>
        n.Contains("Idle") || n.Contains("Walk") || n.Contains("Jog") || n.Contains("Sprint") || n.Contains("Fwd") || n == "Dance";

    public sealed class Person
    {
        public required Node3D Root;
        public required Skeleton3D Skeleton;
        public required AnimationPlayer Anim;
        public readonly List<MeshInstance3D> Meshes = new();
        /// <summary>Which body: "" for the kit's, "heroine" for hers (her
        /// own idle and carriage).</summary>
        public string Body = "";
        /// <summary>Her calling and what she holds (HerClips.Kind), which
        /// choose her own clips.</summary>
        public string Calling = "", Kind = "";
        /// <summary>Her corrective layer, told how much of what plays is her own.</summary>
        public HerPose? Pose;
        /// <summary>Her hair's meshes (one hairstyle), and its style.</summary>
        public readonly List<MeshInstance3D> Hair = new();
        public string HairStyle = "";
        /// <summary>The paint on her face (Lore.Her.Paints), or none.</summary>
        public string? Paint;
        /// <summary>The face she started from, whose painting her head wears (none: her own).</summary>
        public string? FaceShape;
        /// <summary>Her head's pose as she is drawn (her corrective layer
        /// included, which a pose read in _Process is not), skeleton space.</summary>
        public Transform3D? HeadPose;
        /// <summary>A kit body (People.Build), a woman's or a man's; and, set
        /// by its view, whether it goes unarmed: the townsfolk, who play
        /// their own clips (FolkClips) where they have them.</summary>
        public bool Kit, Woman, Folk;
    }

    /// <summary>The clip a person plays for one the game names: the heroine's
    /// own where she has it ("her/..."), the library's otherwise.</summary>
    public static string Clip(Person p, string name)
    {
        if (p.Body != "heroine") return p.Folk && FolkClips.For(p.Woman, name) is string folk ? folk : Resolve(name);
        // (One of hers asked for by her own name.)
        if (name.StartsWith(HerClips.Prefix)) return HerClips.Has(name[HerClips.Prefix.Length..]) ? name : Resolve("Idle");
        return HerClips.For(p.Calling, p.Kind, name) is string her ? her : Resolve(name);
    }

    /// <summary>A person, put together: returns its root (add it to the
    /// scene), skeleton and animation player.</summary>
    public static Person Build(Look look)
    {
        var bodyName = look.Sex == "female" ? "Superhero_Female_FullBody" : "Superhero_Male_FullBody";
        var root = GD.Load<PackedScene>($"{Dir}/{bodyName}.gltf").Instantiate<Node3D>();
        var skel = root.GetNode<Skeleton3D>("Armature/Skeleton3D");
        // The body is hidden where the clothes cover it (the web game's cover mask).
        var covered = Cover.Where(c => look.Outfit.Any(p => c.Part.IsMatch(p))).Select(c => c.Bones).ToList();
        // Top and trousers together cover the hips too (trousers alone sit
        // lower, and a bare-chested figure keeps its hips).
        if (look.Outfit.Any(p => p.Contains("_Body")) && look.Outfit.Any(p => p.Contains("_Legs"))) covered.Add(new Regex("^pelvis$"));
        if (covered.Count > 0)
            foreach (var c in skel.GetChildren())
                if (c is MeshInstance3D body) Mask(body, skel, covered);
        var parts = new List<string>(look.Outfit);
        if (look.Hair != null) parts.Add(look.Hair);
        if (look.Beard) parts.Add("Hair_Beard");
        foreach (var part in parts)
        {
            var scene = GD.Load<PackedScene>($"{Dir}/{part}.gltf").Instantiate<Node3D>();
            var from = scene.GetNode<Skeleton3D>("Armature/Skeleton3D");
            foreach (var c in from.GetChildren())
                if (c is MeshInstance3D mi)
                {
                    from.RemoveChild(mi);
                    mi.Owner = null;
                    skel.AddChild(mi);
                    mi.Skeleton = "..";
                }
            scene.Free();
        }
        var person = new Person { Root = root, Skeleton = skel, Anim = new AnimationPlayer(), Kit = true, Woman = look.Sex == "female" };
        foreach (var c in skel.GetChildren())
            if (c is MeshInstance3D mi)
            {
                person.Meshes.Add(mi);
                Shape(mi, look.Figure);
                Dress(mi, look);
                // Bodies are on a layer of their own: blood and the marks on
                // the ground are not painted on them.
                mi.Layers = 2;
            }
        root.AddChild(person.Anim);
        person.Anim.RootNode = "..";
        person.Anim.AddAnimationLibrary("", Clips());
        // The townsfolk's own clips beside the library's (tools/anim/folk.py).
        if (FolkClips.Library() is AnimationLibrary folk) person.Anim.AddAnimationLibrary("folk", folk);
        return person;
    }

    /// <summary>The woman survivor's body (tools/assets/woman_body.py: a
    /// figure made for the game, rigged to the same skeleton so every clip
    /// plays on her). One mesh, her own hair and close-fitting suit painted
    /// on: her skin takes the tone chosen, her hair its colour and her suit
    /// the calling's cloth (shaders/woman_skin.gdshader), and her figure is
    /// her own shape key.</summary>
    public static Person Woman(Look look)
    {
        var root = GD.Load<PackedScene>("res://art/people/woman.glb").Instantiate<Node3D>();
        var skel = (Skeleton3D)root.FindChildren("*", "Skeleton3D", true, false)[0];
        var person = new Person { Root = root, Skeleton = skel, Anim = new AnimationPlayer() };
        womanShader ??= GD.Load<Shader>("res://shaders/woman_skin.gdshader");
        womanMask ??= GD.Load<Texture2D>("res://art/people/woman_mask.png");
        foreach (var mi in skel.GetChildren().OfType<MeshInstance3D>())
        {
            person.Meshes.Add(mi);
            // The figure slider: 1 as she was made, 0 slighter, 1.5 fuller still.
            int key = mi.FindBlendShapeByName("Figure");
            if (key >= 0) mi.SetBlendShapeValue(key, (float)(look.Figure < 1 ? look.Figure - 1 : (look.Figure - 1) * 2));
            for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
                if (mi.Mesh.SurfaceGetMaterial(s) is BaseMaterial3D src)
                {
                    var m = new ShaderMaterial { Shader = womanShader, ResourceName = src.ResourceName };
                    m.SetShaderParameter("tex", src.AlbedoTexture);
                    m.SetShaderParameter("normal_tex", src.NormalTexture);
                    m.SetShaderParameter("mask", womanMask);
                    m.SetShaderParameter("paint_skin", WomanPaint.Skin);
                    m.SetShaderParameter("paint_hair", WomanPaint.Hair);
                    m.SetShaderParameter("paint_suit", WomanPaint.Suit);
                    m.SetShaderParameter("skin", look.Skin ?? WomanPaint.Skin);
                    if (look.HairColor is Color hair) { m.SetShaderParameter("dye_hair", true); m.SetShaderParameter("hair", hair); }
                    if (look.Cloth is Color cloth) { m.SetShaderParameter("dye_suit", true); m.SetShaderParameter("cloth", cloth); }
                    mi.SetSurfaceOverrideMaterial(s, m);
                }
            mi.Layers = 2;
        }
        root.AddChild(person.Anim);
        person.Anim.RootNode = "..";
        person.Anim.AddAnimationLibrary("", Clips());
        return person;
    }

    static Shader? womanShader;
    static Texture2D? womanMask;

    /// <summary>The woman survivor in the body made from the reference
    /// pictures: TRELLIS 2's model of the figure, bound to the game's own
    /// skeleton by tools/assets/bind_scan.py, so every clip plays on her; her
    /// skin, hair and suit are her own paint.</summary>
    public static Person Heroine(Look look)
    {
        var root = GD.Load<PackedScene>("res://art/people/heroine.glb").Instantiate<Node3D>();
        var skel = (Skeleton3D)root.FindChildren("*", "Skeleton3D", true, false)[0];
        var person = new Person { Root = root, Skeleton = skel, Anim = new AnimationPlayer(), Body = "heroine" };
        person.Pose = new HerPose();
        skel.AddChild(person.Pose);
        int headBone = skel.FindBone("Head");
        if (headBone >= 0) skel.SkeletonUpdated += () => person.HeadPose = skel.GetBoneGlobalPose(headBone);
        skel.AddChild(new HerJiggle());
        skel.AddChild(new HerFaceLife());
        foreach (var mi in skel.GetChildren().OfType<MeshInstance3D>())
        {
            person.Meshes.Add(mi);
            mi.Layers = 2;
            for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
                if (mi.Mesh.SurfaceGetMaterial(s) is BaseMaterial3D src)
                    mi.SetSurfaceOverrideMaterial(s, HerPart(src, look, mi.Mesh));
        }
        root.AddChild(person.Anim);
        person.Anim.RootNode = "..";
        person.Anim.AddAnimationLibrary("", Clips());
        // Her own clips beside the library's (tools/anim).
        if (HerClips.Library() is AnimationLibrary her) person.Anim.AddAnimationLibrary("her", her);
        return person;
    }

    /// <summary>Her hairstyles (tools/assets/heroine_head.py: a file each,
    /// fitted to her head), the first hers unless another is chosen.</summary>
    public static readonly string[] HerHairs = { "long", "ponytail", "braid", "bob", "pixie" };

    /// <summary>Her own hair colour, a deep copper red.</summary>
    public static readonly Color HerHairColour = new("#8f2d14");

    /// <summary>A material of hers by its name (heroine_head.py names
    /// them): her skin, her eyes and the rest of her head.</summary>
    static Material HerPart(BaseMaterial3D src, Look look, Mesh mesh)
    {
        var hair = look.HairColor ?? HerHairColour;
        var m = (StandardMaterial3D)src.Duplicate();
        switch (src.ResourceName)
        {
            case "eyes":
                // Her eyes' own paint and shader (shaders/heroine_eye.gdshader):
                // the iris behind the cornea, wet, the whites shaded by her lids.
                eyeShader ??= GD.Load<Shader>("res://shaders/heroine_eye.gdshader");
                var e = new ShaderMaterial { Shader = eyeShader };
                e.SetShaderParameter("eye", GD.Load<Texture2D>("res://art/people/head_tex/heroine_eye.png"));
                e.SetShaderParameter("iris", GD.Load<Texture2D>("res://art/people/head_tex/heroine_iris.png"));
                EyeColour(e, look.Eyes, look.EyeRing);
                return e;
            case "brows" or "lashes":
                // Cards cut out by their alpha, soft at the edges; brows
                // a shade of her hair, lashes near black.
                m.Transparency = BaseMaterial3D.TransparencyEnum.AlphaScissor;
                m.AlphaScissorThreshold = 0.35f;
                m.AlphaAntialiasingMode = BaseMaterial3D.AlphaAntiAliasing.AlphaToCoverageAndToOne;
                m.CullMode = BaseMaterial3D.CullModeEnum.Disabled;
                m.AlbedoColor = src.ResourceName == "brows" ? hair.Darkened(0.45f) : new Color(0.12f, 0.08f, 0.07f);
                if (src.ResourceName == "lashes")                  // (her lower lashes finer: tools/assets/heroine_eyes.py)
                    m.AlbedoTexture = GD.Load<Texture2D>("res://art/people/head_tex/heroine_lashes.png");
                m.Roughness = 0.8f;
                return m;
            case "teeth" or "tongue":
                m.Roughness = 0.35f;
                return m;
            default:
                return Skin(src, look, mesh);
        }
    }

    /// <summary>Her face's sliders (tools/assets/face_shapes.py's SLIDERS,
    /// made by heroine_head.py), each from -1 to 1 about her own face: each
    /// a shape key either way on her head, its parts and her hair; her
    /// neck's by her bones (HerPose).</summary>
    public static readonly string[] HerSliders =
    {
        "forehead_height", "forehead_slope", "forehead_round", "temples", "brow_ridge", "face_width", "face_shape",
        "eyes_size", "eyes_spacing", "eyes_height", "eyes_tilt", "eyes_open", "eyes_depth", "eyes_inner", "brows_height", "brows_arch",
        "nose_width", "nose_length", "nose_bridge", "nose_bridge_width", "nose_tip", "nose_tip_width", "nose_projection", "nostrils",
        "cheekbone_height", "cheekbone_width", "cheekbone_prominence", "cheeks",
        "lips_upper", "lips_lower", "mouth_width", "mouth_height", "mouth_corners", "cupids_bow", "lips_forward",
        "jaw_width", "jaw_angle", "chin_width", "chin_length", "chin_forward", "jaw_forward",
        "ears_size", "ears_pointed", "ears_out", "ears_lobes",
        "neck_width", "neck_length",
    };

    /// <summary>Her face shaped: each slider (HerSliders) from -1 to 1, and
    /// her expressions (heroine_head.py's EXPRESSIONS: blink_l, smile, ...)
    /// from 0 to 1, on her head and on the parts of it that follow it (eyes,
    /// brows, lashes, teeth, her hair); her neck by her bones.</summary>
    public static void HerFace(Person p, IReadOnlyDictionary<string, float> face, bool whole = false)
    {
        // (whole: every slider set, those not given back to her own face)
        var all = whole ? HerSliders.ToDictionary(s => s, s => face.TryGetValue(s, out var v) ? v : 0f) : face;
        if (p.Pose is HerPose hp)
        {
            if (all.TryGetValue("neck_width", out var nw)) hp.NeckWidth = Mathf.Clamp(nw, -1, 1);
            if (all.TryGetValue("neck_length", out var nl)) hp.NeckLength = Mathf.Clamp(nl, -1, 1);
        }
        foreach (var mi in p.Meshes)
        {
            if (mi.Mesh is not ArrayMesh am || am.GetBlendShapeCount() == 0) continue;
            foreach (var (name, v) in all)
            {
                Shape(mi, name + "+", Mathf.Max(v, 0));
                Shape(mi, name + "-", Mathf.Max(-v, 0));
                Shape(mi, name, v);
            }
        }

        static void Shape(MeshInstance3D mi, string name, float v)
        {
            int i = mi.FindBlendShapeByName(name);
            if (i >= 0) mi.SetBlendShapeValue(i, v);
        }
    }

    /// <summary>One of her hairstyles on her head, dyed: its paint is grey,
    /// light to dark, and takes the colour as it is. The one she had is
    /// taken off first.</summary>
    public static void HerHair(Person p, string style, Color colour)
    {
        foreach (var old in p.Hair) { p.Meshes.Remove(old); old.QueueFree(); }
        p.Hair.Clear();
        p.HairStyle = style;
        var file = $"res://art/people/heroine_hair_{style}.gltf";
        if (!ResourceLoader.Exists(file)) return;
        var scene = GD.Load<PackedScene>(file).Instantiate<Node3D>();
        var from = (Skeleton3D)scene.FindChildren("*", "Skeleton3D", true, false)[0];
        foreach (var mi in from.GetChildren().OfType<MeshInstance3D>().ToList())
        {
            from.RemoveChild(mi);
            mi.Owner = null;
            p.Skeleton.AddChild(mi);
            mi.Skeleton = "..";
            mi.Layers = 2;
            p.Meshes.Add(mi);
            p.Hair.Add(mi);
            for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
                if (mi.Mesh.SurfaceGetMaterial(s) is BaseMaterial3D src)
                    mi.SetSurfaceOverrideMaterial(s, Hair(src, colour));
            mi.AddChild(new HairSway { Style = style });
        }
        scene.Free();
    }

    /// <summary>Between anyone's eyes, in the world, as they stand now: hers
    /// exactly, anyone else's a hand above and before their head bone.</summary>
    public static Vector3 EyesOf(Person p)
    {
        if (p.Body == "heroine") return HerEyes(p);
        int hb = p.Skeleton.FindBone("Head");
        if (hb < 0) return p.Root.GlobalPosition + Vector3.Up * 1.6f;
        var head = p.Skeleton.GlobalTransform * p.Skeleton.GetBoneGlobalPose(hb);
        return head.Origin + head.Basis.Y.Normalized() * 0.09f * p.Root.Scale.Y + p.Root.GlobalBasis.Z.Normalized() * 0.08f * p.Root.Scale.Y;
    }

    /// <summary>Between her eyes, in the world, as she stands now (a camera
    /// looking at her face aims here): where they are on her head at rest
    /// (heroine.glb), moved as her head has moved.</summary>
    public static Vector3 HerEyes(Person p)
    {
        int hb = p.Skeleton.FindBone("Head");
        if (hb < 0) return p.Root.GlobalPosition + Vector3.Up * 1.6f;
        var moved = (p.HeadPose ?? p.Skeleton.GetBoneGlobalPose(hb)) * p.Skeleton.GetBoneGlobalRest(hb).AffineInverse();
        return p.Skeleton.GlobalTransform * (moved * new Vector3(0, 1.748f, 0.075f));
    }

    /// <summary>Her eyes' colour (shaders/heroine_eye.gdshader): the iris's
    /// paint keeps its fibres and crypts, its light and dark, and takes the
    /// colour chosen, the ring round the pupil its own (as a blue eye's amber
    /// collarette); none chosen keeps the paint's own green.</summary>
    static void EyeColour(ShaderMaterial e, Color? iris, Color? ring)
    {
        e.SetShaderParameter("recolour", iris != null ? 1f : 0f);
        if (iris is not Color c) return;
        e.SetShaderParameter("iris_colour", c);
        e.SetShaderParameter("ring_colour", ring ?? c);
    }

    static Shader? paintShader;

    /// <summary>Paint on her face (Lore.Her.Paints: art/people/paint/ID.png, laid
    /// out on her head's own paint by tools/assets/heroine_paint.py): drawn
    /// over her skin as a pass of its own, so it lies on the skin rather than
    /// in it, with its own sheen (chalky woad, waxy kohl, bright leaf), and
    /// moves with her face as it shapes and speaks. None: taken off.</summary>
    public static void HerPaint(Person p, string? paint)
    {
        p.Paint = paint;
        var def = paint == null ? null : SurvivorUnchained.World.Lore.Her.Paints.FirstOrDefault(x => x.Id == paint);
        var file = def == null ? "" : $"res://art/people/paint/{def.Id}.png";
        foreach (var mi in p.Meshes)
            for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
            {
                if (mi.Mesh.SurfaceGetMaterial(s)?.ResourceName != "skin_head" || mi.GetSurfaceOverrideMaterial(s) is not ShaderMaterial skin) continue;
                if (def == null || !ResourceLoader.Exists(file)) { skin.NextPass = null; continue; }
                paintShader ??= GD.Load<Shader>("res://shaders/heroine_paint.gdshader");
                var m = new ShaderMaterial { Shader = paintShader };
                m.SetShaderParameter("paint", GD.Load<Texture2D>(file));
                m.SetShaderParameter("rough", (float)def.Rough);
                m.SetShaderParameter("metal", (float)def.Metal);
                skin.NextPass = m;
            }
    }

    /// <summary>Her look changed where she stands (creation's choices, as they
    /// are made): her hairstyle and its colour, her skin's tone, her eyes, her
    /// face and its paint, without building her again (she keeps her place
    /// in what she is doing).</summary>
    public static void HerRestyle(Person p, Look look)
    {
        if (p.Body != "heroine") return;
        var colour = look.HairColor ?? HerHairColour;
        var style = HerHairs.Contains(look.Hair) ? look.Hair! : HerHairs[0];
        if (style != p.HairStyle) HerHair(p, style, colour);
        foreach (var mi in p.Meshes)
            for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
            {
                if (mi.GetSurfaceOverrideMaterial(s) is ShaderMaterial m)
                {
                    if (m.Shader == hairShader) m.SetShaderParameter("colour", colour);
                    else if (m.Shader == skinShader2) m.SetShaderParameter("tone", SkinTone(look));
                    else if (m.Shader == eyeShader) EyeColour(m, look.Eyes, look.EyeRing);
                }
                else if (mi.GetSurfaceOverrideMaterial(s) is StandardMaterial3D b && b.ResourceName == "brows") b.AlbedoColor = colour.Darkened(0.45f);
            }
        HerFace(p, look.Face ?? new Dictionary<string, float>(), whole: true);
        if (look.Paint != p.Paint) HerPaint(p, look.Paint);
        if (look.FaceShape != p.FaceShape) HerHeadPaint(p, look.FaceShape);
    }

    /// <summary>Her head's painting for a face she started from (Lore.Her's
    /// faces: tools/assets/heroine_head.py's head_tex/heroine_head_ID.jpg,
    /// each painted on her head shaped as that face, its brows, lips and
    /// skin its own), or her own.</summary>
    public static void HerHeadPaint(Person p, string? face)
    {
        p.FaceShape = face;
        var file = HeadPaintFile(face);
        foreach (var mi in p.Meshes)
            for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
                if (mi.Mesh.SurfaceGetMaterial(s)?.ResourceName == "skin_head" && mi.GetSurfaceOverrideMaterial(s) is ShaderMaterial skin)
                    skin.SetShaderParameter("paint", file != null ? GD.Load<Texture2D>(file) : (mi.Mesh.SurfaceGetMaterial(s) as BaseMaterial3D)?.AlbedoTexture);
    }

    static string? HeadPaintFile(string? face) =>
        face is { Length: > 0 } && ResourceLoader.Exists($"res://art/people/head_tex/heroine_head_{face}.jpg") ? $"res://art/people/head_tex/heroine_head_{face}.jpg" : null;

    static Shader? hairShader, eyeShader;

    /// <summary>Hair: her hair cards (tools/assets/heroine_hair.py) by
    /// shaders/heroine_hair.gdshader, dyed: the strands' atlas cut to its
    /// strands, darker at the roots and deep in, with the long highlight
    /// across them.</summary>
    static Material Hair(BaseMaterial3D src, Color colour)
    {
        hairShader ??= GD.Load<Shader>("res://shaders/heroine_hair.gdshader");
        var m = new ShaderMaterial { Shader = hairShader };
        m.SetShaderParameter("strands", src.AlbedoTexture);
        m.SetShaderParameter("colour", colour);
        m.SetShaderParameter("cap", src.ResourceName == "hair_cap");
        m.SetShaderParameter("tie", src.ResourceName == "hair_tie");
        return m;
    }

    /// <summary>One of her outfits (tools/assets/heroine_outfits.py: a file
    /// for each calling, cut from her own body and exported from her own
    /// skeleton), its pieces moved onto her skeleton.</summary>
    public static void HerOutfit(Person p, string set)
    {
        var file = $"res://art/people/heroine_outfit_{set}.gltf";
        if (!ResourceLoader.Exists(file)) return;
        var scene = GD.Load<PackedScene>(file).Instantiate<Node3D>();
        var from = (Skeleton3D)scene.FindChildren("*", "Skeleton3D", true, false)[0];
        foreach (var mi in from.GetChildren().OfType<MeshInstance3D>().ToList())
        {
            if (!mi.Name.ToString().StartsWith(set + "_")) continue;
            from.RemoveChild(mi);
            mi.Owner = null;
            p.Skeleton.AddChild(mi);
            mi.Skeleton = "..";
            mi.Layers = 2;
            p.Meshes.Add(mi);
            Fur(mi);
            OutfitMaterials(mi);
        }
        scene.Free();
        // Her skin under the outfit's fitted pieces is not drawn: each
        // outfit marks it in one channel of her vertex colours.
        int ch = System.Array.IndexOf(OutfitChannels, set);
        if (ch >= 0)
            foreach (var mi in p.Skeleton.GetChildren().OfType<MeshInstance3D>())
                if (!mi.Name.ToString().Contains('.') && !mi.Name.ToString().Contains('_')) HideSkin(mi, ch);
    }

    static Shader? furShader, sheerShader, outfitShader;
    static Godot.Collections.Dictionary? outfitTable;

    /// <summary>Her outfit's pieces drawn as what they are made of
    /// (shaders/heroine_outfit.gdshader: leather, metal, cloth or gloss, from
    /// art/people/outfit_materials.json, which heroine_outfits.py writes), all
    /// but fur and sheer stockings, which have shaders of their own.</summary>
    public static void OutfitMaterials(MeshInstance3D mi)
    {
        outfitTable ??= Json.ParseString(FileAccess.GetFileAsString("res://art/people/outfit_materials.json")).AsGodotDictionary();
        outfitShader ??= GD.Load<Shader>("res://shaders/heroine_outfit.gdshader");
        for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
        {
            if (mi.GetSurfaceOverrideMaterial(s) != null || mi.Mesh.SurfaceGetMaterial(s) is not StandardMaterial3D src) continue;
            // (its vertex colours are the shader's data, never its colour)
            src.VertexColorUseAsAlbedo = false;
            var key = src.ResourceName;
            if (!outfitTable.ContainsKey(key)) continue;
            var entry = outfitTable[key].AsGodotDictionary();
            int kind = (string)entry["kind"] switch { "leather" => 0, "metal" => 1, "cloth" => 2, "gloss" => 3, "twill" => 4, _ => -1 };
            if (kind < 0) continue;
            var m = new ShaderMaterial { Shader = outfitShader };
            m.SetShaderParameter("kind", kind);
            m.SetShaderParameter("albedo", src.AlbedoTexture);
            m.SetShaderParameter("normal_map", src.NormalTexture);
            m.SetShaderParameter("orm", src.RoughnessTexture);
            m.SetShaderParameter("has_orm", src.RoughnessTexture != null);
            m.SetShaderParameter("roughness_value", src.Roughness);
            m.SetShaderParameter("metallic_value", src.Metallic);
            m.SetShaderParameter("repeats", (float)entry["repeats"]);
            mi.SetSurfaceOverrideMaterial(s, m);
        }
    }

    /// <summary>A piece made of fur grows a pile: its surface drawn again in
    /// shells (shaders/fur_shell.gdshader), each further out, keeping only
    /// the strands that reach so far.</summary>
    public static void Fur(MeshInstance3D mi, int shells = 20)
    {
        for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
        {
            if (mi.Mesh.SurfaceGetMaterial(s) is BaseMaterial3D sheer && sheer.ResourceName == "stocking")
            {
                // Sheer: clear face on, denser at the edges (shaders/sheer.gdshader).
                sheerShader ??= GD.Load<Shader>("res://shaders/sheer.gdshader");
                mi.SetSurfaceOverrideMaterial(s, new ShaderMaterial { Shader = sheerShader });
                continue;
            }
            if (mi.Mesh.SurfaceGetMaterial(s) is not BaseMaterial3D src || src.ResourceName != "fur") continue;
            furShader ??= GD.Load<Shader>("res://shaders/fur_shell.gdshader");
            ShaderMaterial? first = null, last = null;
            for (int i = 0; i <= shells; i++)
            {
                var m = new ShaderMaterial { Shader = furShader };
                m.SetShaderParameter("albedo_tex", src.AlbedoTexture);
                m.SetShaderParameter("tint", src.AlbedoColor);
                m.SetShaderParameter("layer", (float)i / shells);
                if (last != null) last.NextPass = m; else first = m;
                last = m;
            }
            mi.SetSurfaceOverrideMaterial(s, first);
        }
    }

    /// <summary>Her outfits, in the order of their channels in her vertex
    /// colours (tools/assets/heroine_outfits.py's OUTFITS).</summary>
    static readonly string[] OutfitChannels = { "warden", "arcanist", "reaver", "ranger" };

    static readonly Dictionary<(Mesh, int), ArrayMesh> hidden = new();

    static void HideSkin(MeshInstance3D mi, int ch)
    {
        // (Only her body is marked; her head is left as it is, shape keys and all.)
        if (mi.Mesh is not ArrayMesh am || (am.SurfaceGetFormat(0) & Mesh.ArrayFormat.FormatColor) == 0) return;
        if (!hidden.TryGetValue((am, ch), out var mesh))
        {
            mesh = new ArrayMesh();
            for (int s = 0; s < am.GetSurfaceCount(); s++)
            {
                var arr = am.SurfaceGetArrays(s);
                var colV = arr[(int)Mesh.ArrayType.Color];
                if (colV.VariantType != Variant.Type.Nil)
                {
                    var col = colV.AsColorArray();
                    var idx = arr[(int)Mesh.ArrayType.Index].AsInt32Array();
                    var kept = new List<int>(idx.Length);
                    for (int t = 0; t + 2 < idx.Length; t += 3)
                        if (col[idx[t]][ch] < 0.5f || col[idx[t + 1]][ch] < 0.5f || col[idx[t + 2]][ch] < 0.5f)
                        { kept.Add(idx[t]); kept.Add(idx[t + 1]); kept.Add(idx[t + 2]); }
                    arr[(int)Mesh.ArrayType.Index] = kept.ToArray();
                }
                var flags = (Mesh.ArrayFormat)((long)am.SurfaceGetFormat(s) & (long)Mesh.ArrayFormat.FlagUse8BoneWeights);
                mesh.AddSurfaceFromArrays(am.SurfaceGetPrimitiveType(s), arr, new Godot.Collections.Array<Godot.Collections.Array>(), null, flags);
                mesh.SurfaceSetMaterial(s, am.SurfaceGetMaterial(s));
            }
            hidden[(am, ch)] = mesh;
        }
        var over = Enumerable.Range(0, mi.Mesh.GetSurfaceCount()).Select(mi.GetSurfaceOverrideMaterial).ToList();
        mi.Mesh = mesh;
        for (int s = 0; s < over.Count; s++) mi.SetSurfaceOverrideMaterial(s, over[s]);
    }

    /// <summary>Her paint as skin: light carried under it (subsurface
    /// scattering, reddened as through flesh), a soft sheen rather than
    /// plastic, and warmed toward a sun-browned tone, or the tone chosen.</summary>
    static Material Skin(BaseMaterial3D src, Look look, Mesh mesh)
    {
        // shaders/heroine_skin.gdshader: pores, soft uneven sheen, light
        // under the skin. (Her vertex colours mark what each outfit hides,
        // not her paint: the shader never reads them.)
        skinShader2 ??= GD.Load<Shader>("res://shaders/heroine_skin.gdshader");
        var m = new ShaderMaterial { Shader = skinShader2 };
        m.SetShaderParameter("paint", src.AlbedoTexture);
        m.SetShaderParameter("tone", SkinTone(look));
        m.SetShaderParameter("pores", GD.Load<Texture2D>("res://art/people/skin_pores.png"));
        m.SetShaderParameter("pore_scale", PoreScale(mesh));
        // Her face a little more matte than her body: at the shine her body
        // has, her face read as plastic, and a light from behind lit the
        // side of her brow as a hard white band.
        if (src.ResourceName == "skin_head")
        {
            if (HeadPaintFile(look.FaceShape) is string own) m.SetShaderParameter("paint", GD.Load<Texture2D>(own));
            m.SetShaderParameter("rough", 0.6f);
            m.SetShaderParameter("shine", 0.36f);
            // (her eyes, brows and lips deepened when her face is small on
            // screen, so a face still reads from the game's camera)
            if (ResourceLoader.Exists("res://art/people/head_tex/heroine_features.png"))
                m.SetShaderParameter("features", GD.Load<Texture2D>("res://art/people/head_tex/heroine_features.png"));
        }
        return m;
    }

    static Color SkinTone(Look look) => look.Skin is Color tone ? tone.Lerp(Colors.White, 0.35f) : new Color(1.0f, 0.86f, 0.74f);

    static Shader? skinShader2;
    static readonly Dictionary<Mesh, float> poreScales = new();

    /// <summary>How many pore tiles to a UV unit on a mesh, so a tile is
    /// 1.5 cm on her whatever its UVs' scale: the square root of its area
    /// over its UVs' area, over 1.5 cm.</summary>
    public static float PoreScale(Mesh mesh)
    {
        if (poreScales.TryGetValue(mesh, out var k)) return k;
        double area = 0, uvArea = 0;
        for (int s = 0; s < mesh.GetSurfaceCount(); s++)
        {
            var arr = mesh.SurfaceGetArrays(s);
            if (arr[(int)Mesh.ArrayType.TexUV].VariantType == Variant.Type.Nil) continue;
            var v = arr[(int)Mesh.ArrayType.Vertex].AsVector3Array();
            var uv = arr[(int)Mesh.ArrayType.TexUV].AsVector2Array();
            var idx = arr[(int)Mesh.ArrayType.Index].AsInt32Array();
            for (int t = 0; t + 2 < idx.Length; t += 3)
            {
                area += (v[idx[t + 1]] - v[idx[t]]).Cross(v[idx[t + 2]] - v[idx[t]]).Length() / 2;
                uvArea += Mathf.Abs((uv[idx[t + 1]] - uv[idx[t]]).Cross(uv[idx[t + 2]] - uv[idx[t]])) / 2;
            }
        }
        k = uvArea > 0 ? (float)(Math.Sqrt(area / uvArea) / 0.015) : 30f;
        poreScales[mesh] = k;
        return k;
    }

    /// <summary>Her paint's own skin (lit, not in its shadows), hair and suit,
    /// which the choices are made against (tools/assets/woman_body.py prints
    /// them).</summary>
    static readonly (Color Skin, Color Hair, Color Suit) WomanPaint = (new("#ddad9f"), new("#8d735a"), new("#272d35"));

    /// <summary>A woman in her own body: donizaki's anime base (Sketchfab,
    /// CC BY), rigged to the same skeleton by tools/assets/anime_female.py so
    /// every clip plays on her. Her own shape keys give the figure, her
    /// painted skin takes the tone chosen, and one of our hairstyles sits on
    /// her head. Bare: the Quaternius clothes are cut for other bodies.</summary>
    public static Person Her(Look look)
    {
        var root = GD.Load<PackedScene>("res://art/people/anime_female.glb").Instantiate<Node3D>();
        var skel = root.GetNode<Skeleton3D>("Armature/Skeleton3D");
        var person = new Person { Root = root, Skeleton = skel, Anim = new AnimationPlayer() };
        skinShader ??= GD.Load<Shader>("res://shaders/anime_skin.gdshader");
        var tone = look.Skin ?? Fair;
        foreach (var c in skel.GetChildren())
            if (c is MeshInstance3D mi)
            {
                person.Meshes.Add(mi);
                HerFigure(mi, look.Figure);
                for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
                    if (mi.Mesh.SurfaceGetMaterial(s) is BaseMaterial3D src && src.AlbedoTexture != null)
                    {
                        var m = new ShaderMaterial { Shader = skinShader, ResourceName = src.ResourceName };
                        m.SetShaderParameter("tex", src.AlbedoTexture);
                        m.SetShaderParameter("skin", tone);
                        m.SetShaderParameter("whole", src.ResourceName.Contains("Body"));
                        if (look.HairColor is Color brow) { m.SetShaderParameter("dye_brows", true); m.SetShaderParameter("brow", brow); }
                        mi.SetSurfaceOverrideMaterial(s, m);
                    }
                mi.Layers = 2;
            }
        if (look.Hair != null)
            foreach (var hair in HairOn(skel, look.Hair))
            {
                person.Meshes.Add(hair);
                Dress(hair, look);
                hair.Layers = 2;
            }
        root.AddChild(person.Anim);
        person.Anim.RootNode = "..";
        person.Anim.AddAnimationLibrary("", Clips());
        return person;
    }

    static Shader? skinShader;

    /// <summary>Her figure from her own shape keys, kept within the range
    /// she was made for: at 0 slighter than she was made, at 1 a fuller bust,
    /// the waist in and the hips out a little, at 1.5 fuller still.</summary>
    static void HerFigure(MeshInstance3D mi, double f)
    {
        void Key(string name, double v) { int i = mi.FindBlendShapeByName(name); if (i >= 0) mi.SetBlendShapeValue(i, (float)v); }
        Key("Breast Size", -0.4 + f * 0.933);
        Key("Hip Width", -0.2 + f * 0.55);
        Key("Waist Width", 0.2 - f * 0.5);
    }

    /// <summary>How our hair sits on her head, scaled whole, for a style not
    /// fitted to her: her head is larger than the Quaternius head the hair is
    /// rigged to, and sits further forward (by eye).</summary>
    const float HairScale = 1.15f;
    static readonly Vector3 HairOffset = new(0, 0.005f, -0.032f);

    /// <summary>One of our hairstyles on her head. Fitted to her scalp
    /// offline where it has been (tools/assets/anime_hair.py: art/people/
    /// her_STYLE.glb, bound to her head bone already) and dressed in the
    /// Quaternius hair's own material; otherwise the Quaternius hair itself,
    /// every bind the head's, scaled about its head and set on hers.</summary>
    static List<MeshInstance3D> HairOn(Skeleton3D skel, string style)
    {
        var scene = GD.Load<PackedScene>($"{Dir}/{style}.gltf").Instantiate<Node3D>();
        var from = scene.GetNode<Skeleton3D>("Armature/Skeleton3D");
        var meshes = new List<MeshInstance3D>();
        var fitted = $"res://art/people/her_{style}.glb";
        if (ResourceLoader.Exists(fitted))
        {
            var dress = from.GetChildren().OfType<MeshInstance3D>().First().Mesh;
            var hers = GD.Load<PackedScene>(fitted).Instantiate<Node3D>();
            var hs = (Skeleton3D)hers.FindChildren("*", "Skeleton3D", true, false)[0];
            foreach (var mi in hs.GetChildren().OfType<MeshInstance3D>().ToList())
            {
                hs.RemoveChild(mi);
                mi.Owner = null;
                if (mi.Mesh is ArrayMesh am)
                    for (int s = 0; s < am.GetSurfaceCount() && s < dress.GetSurfaceCount(); s++) am.SurfaceSetMaterial(s, dress.SurfaceGetMaterial(s));
                skel.AddChild(mi);
                mi.Skeleton = "..";
                meshes.Add(mi);
            }
            hers.Free();
            scene.Free();
            return meshes;
        }
        var rest = skel.GetBoneGlobalRest(skel.FindBone("Head"));
        var qHead = from.GetBoneGlobalRest(from.FindBone("Head")).Origin;
        var fit = new Transform3D(Basis.Identity.Scaled(Vector3.One * HairScale), rest.Origin + HairOffset - HairScale * qHead);
        foreach (var c in from.GetChildren())
            if (c is MeshInstance3D mi)
            {
                from.RemoveChild(mi);
                mi.Owner = null;
                var skin = (Skin)mi.Skin.Duplicate();
                for (int b = 0; b < skin.GetBindCount(); b++)
                {
                    skin.SetBindName(b, "Head");
                    skin.SetBindPose(b, rest.AffineInverse() * fit);
                }
                mi.Skin = skin;
                skel.AddChild(mi);
                mi.Skeleton = "..";
                meshes.Add(mi);
            }
        scene.Free();
        return meshes;
    }

    /// <summary>What each outfit piece covers, as the body's bones under it:
    /// the body is hidden there (the piece brings any skin it shows).</summary>
    static readonly (Regex Part, Regex Bones)[] Cover =
    {
        (new("_Arms"), new("^(clavicle|upperarm|lowerarm|hand|index|middle|pinky|ring|thumb)_")),
        (new("_Body"), new("^spine_0[123]$")),
        (new("_Legs"), new("^(thigh|calf)")),
        (new("_Feet"), new("^(foot|ball)")),
    };

    static readonly Dictionary<(Mesh, string), ArrayMesh> masked = new();

    /// <summary>The body without the triangles that lie mostly on covered
    /// bones: a copy of its mesh per set of bones, shared by everyone
    /// dressed alike.</summary>
    static void Mask(MeshInstance3D mi, Skeleton3D skel, List<Regex> covered)
    {
        if (mi.Mesh is not ArrayMesh am) return;
        var bones = new HashSet<int>();
        for (int b = 0; b < skel.GetBoneCount(); b++) if (covered.Any(re => re.IsMatch(skel.GetBoneName(b)))) bones.Add(b);
        var key = string.Join(",", bones.OrderBy(b => b));
        if (!masked.TryGetValue((am, key), out var mesh))
        {
            var skin = mi.Skin ?? skel.CreateSkinFromRestTransforms();
            var bindCovered = new bool[skin.GetBindCount()];
            for (int i = 0; i < bindCovered.Length; i++)
            {
                var name = skin.GetBindName(i);
                int bone = name != "" ? skel.FindBone(name) : skin.GetBindBone(i);
                bindCovered[i] = bones.Contains(bone);
            }
            mesh = new ArrayMesh { BlendShapeMode = am.BlendShapeMode };
            // (A run without a screen cannot read shape keys back from a mesh: it goes without.)
            bool shapes = am.GetBlendShapeCount() > 0 && DisplayServer.GetName() != "headless";
            if (shapes) for (int k = 0; k < am.GetBlendShapeCount(); k++) mesh.AddBlendShape(am.GetBlendShapeName(k));
            for (int s = 0; s < am.GetSurfaceCount(); s++)
            {
                var arr = am.SurfaceGetArrays(s);
                var vb = arr[(int)Mesh.ArrayType.Bones];
                var idxV = arr[(int)Mesh.ArrayType.Index];
                int n = arr[(int)Mesh.ArrayType.Vertex].AsVector3Array().Length;
                var idx = idxV.VariantType == Variant.Type.Nil ? Enumerable.Range(0, n).ToArray() : idxV.AsInt32Array();
                if (vb.VariantType != Variant.Type.Nil && n > 0)
                {
                    var bi = vb.AsInt32Array();
                    var bw = arr[(int)Mesh.ArrayType.Weights].AsFloat32Array();
                    int stride = bi.Length / n;
                    var keep = new float[n];
                    for (int v = 0; v < n; v++)
                    {
                        float w = 0;
                        for (int k = 0; k < stride; k++) if (bi[v * stride + k] < bindCovered.Length && bindCovered[bi[v * stride + k]]) w += bw[v * stride + k];
                        keep[v] = 1 - w;
                    }
                    var kept = new List<int>(idx.Length);
                    for (int t = 0; t + 2 < idx.Length; t += 3)
                        if (keep[idx[t]] + keep[idx[t + 1]] + keep[idx[t + 2]] >= 1.5f) { kept.Add(idx[t]); kept.Add(idx[t + 1]); kept.Add(idx[t + 2]); }
                    // Nothing of it shows: a single thin triangle keeps the surface (and its material's place).
                    if (kept.Count == 0) kept.AddRange(new[] { idx[0], idx[0], idx[0] });
                    arr[(int)Mesh.ArrayType.Index] = kept.ToArray();
                }
                var flags = (Mesh.ArrayFormat)((long)am.SurfaceGetFormat(s) & (long)Mesh.ArrayFormat.FlagUse8BoneWeights);
                mesh.AddSurfaceFromArrays(am.SurfaceGetPrimitiveType(s), arr, shapes ? am.SurfaceGetBlendShapeArrays(s) : new Godot.Collections.Array<Godot.Collections.Array>(), null, flags);
                mesh.SurfaceSetMaterial(s, am.SurfaceGetMaterial(s));
                mesh.SurfaceSetName(s, am.SurfaceGetName(s));
            }
            masked[(am, key)] = mesh;
        }
        mi.Mesh = mesh;
    }

    /// <summary>A woman's figure: the body and the clothes over it carry two
    /// shape keys made offline (tools/assets/figure.py): 'bust', a fuller
    /// chest set into the body with a soft join, tops hanging from it; and
    /// 'hips', a narrower waist and wider hips. The figure blends both in.</summary>
    static void Shape(MeshInstance3D mi, double figure)
    {
        if (figure <= 0 || mi.Mesh == null) return;
        int bust = mi.FindBlendShapeByName("bust"), hips = mi.FindBlendShapeByName("hips");
        if (bust >= 0) mi.SetBlendShapeValue(bust, (float)figure);
        if (hips >= 0) mi.SetBlendShapeValue(hips, (float)Math.Min(1.25, figure));
    }

    /// <summary>Where in a material's paint the cloth is (hue, saturation and
    /// value bands, 0..1), and how bright that paint is: the dye takes the
    /// cloth and leaves the leather and buckles (the web game's DYES).</summary>
    public sealed record DyeMask(Vector2 H, Vector2 S, Vector2 V, float Lum);

    static readonly Dictionary<string, (DyeMask? Cloth, DyeMask? Under)> Dyes = new()
    {
        ["MI_Ranger"] = (new(new(0.17f, 0.45f), new(0.25f, 1), new(0.03f, 1), 0.037f), null),
        ["MI_Peasant"] = (new(new(0.04f, 0.2f), new(0, 0.35f), new(0.5f, 1), 0.25f), new(new(0, 0.14f), new(0.3f, 1), new(0, 0.3f), 0.008f)),
    };

    static Shader? personShader;

    /// <summary>A material as the person shader draws it, the cloth dyed.</summary>
    static ShaderMaterial Dyed(StandardMaterial3D src, DyeMask mask, Color color)
    {
        personShader ??= GD.Load<Shader>("res://shaders/person.gdshader");
        var m = new ShaderMaterial { Shader = personShader, ResourceName = src.ResourceName };
        m.SetShaderParameter("albedo", src.AlbedoColor);
        m.SetShaderParameter("albedo_tex", src.AlbedoTexture);
        m.SetShaderParameter("use_normal", src.NormalEnabled && src.NormalTexture != null);
        if (src.NormalTexture != null) m.SetShaderParameter("normal_tex", src.NormalTexture);
        m.SetShaderParameter("normal_scale", src.NormalScale);
        m.SetShaderParameter("use_rough", src.RoughnessTexture != null);
        if (src.RoughnessTexture != null) m.SetShaderParameter("rough_tex", src.RoughnessTexture);
        m.SetShaderParameter("rough_channel", Channel(src.RoughnessTextureChannel));
        m.SetShaderParameter("roughness", src.Roughness);
        m.SetShaderParameter("metallic", src.Metallic);
        m.SetShaderParameter("use_metal", src.MetallicTexture != null);
        if (src.MetallicTexture != null) m.SetShaderParameter("metal_tex", src.MetallicTexture);
        m.SetShaderParameter("metal_channel", Channel(src.MetallicTextureChannel));
        m.SetShaderParameter("rim_amount", 0.45f);
        m.SetShaderParameter("rim_tint", 0.35f);
        SetDye(m, mask, color);
        return m;
    }

    static Vector4 Channel(BaseMaterial3D.TextureChannel c) => c switch
    {
        BaseMaterial3D.TextureChannel.Red => new Vector4(1, 0, 0, 0), BaseMaterial3D.TextureChannel.Green => new Vector4(0, 1, 0, 0),
        BaseMaterial3D.TextureChannel.Blue => new Vector4(0, 0, 1, 0), BaseMaterial3D.TextureChannel.Alpha => new Vector4(0, 0, 0, 1), _ => new Vector4(0.33f, 0.33f, 0.33f, 0),
    };

    /// <summary>A dye's uniforms (shared by the person and crowd shaders).</summary>
    public static void SetDye(ShaderMaterial m, DyeMask mask, Color color)
    {
        var lin = color.SrgbToLinear();
        m.SetShaderParameter("use_dye", true);
        m.SetShaderParameter("dye_color", new Vector3(lin.R, lin.G, lin.B));
        m.SetShaderParameter("dye_h", new Vector3(mask.H.X, mask.H.Y, 0.05f));
        m.SetShaderParameter("dye_s", new Vector3(mask.S.X, mask.S.Y, 0.05f));
        m.SetShaderParameter("dye_v", new Vector3(mask.V.X, mask.V.Y, 0.05f));
        m.SetShaderParameter("dye_lum", mask.Lum);
    }

    /// <summary>The fair tone the skin choices are measured from: a choice
    /// becomes a multiply over the painted skin (the web game's FAIR).</summary>
    static readonly Color Fair = new("#f2c4a8");

    /// <summary>Hair takes its colour (its texture is grey); skin its tone;
    /// cloth a dye, multiplied over the painted colour. Each person has
    /// materials of its own (a hit flashes one, not everyone in that shirt).</summary>
    static void Dress(MeshInstance3D mi, Look look)
    {
        for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
        {
            if (mi.Mesh.SurfaceGetMaterial(s) is not StandardMaterial3D src) continue;
            var mat = (StandardMaterial3D)src.Duplicate();
            // A rim of light at the edge turned from the camera, so a figure
            // reads against dark ground (the web game's body rim).
            mat.RimEnabled = true;
            mat.Rim = 0.45f;
            mat.RimTint = 0.35f;
            var n = src.ResourceName;
            if (n.Contains("Hair") || mi.Name.ToString().Contains("Eyebrows")) { if (look.HairColor is Color h) mat.AlbedoColor = h; }
            else if (look.Skin is Color skin && (n.Contains("Superhero") || n.Contains("Regular"))) mat.AlbedoColor = new Color(skin.R / Fair.R, skin.G / Fair.G, skin.B / Fair.B);
            else if (Dyes.TryGetValue(n, out var d))
            {
                // (One dye per material: trousers with a colour of their own take it.)
                bool legs = mi.Name.ToString().Contains("_Legs");
                var (mask, color) = d.Under is { } um && legs && look.Under is Color under ? (um, under) : d.Cloth is { } cm && look.Cloth is Color cloth ? (cm, cloth) : (null, default(Color));
                if (mask != null) { mi.SetSurfaceOverrideMaterial(s, Dyed(mat, mask, color)); continue; }
            }
            mi.SetSurfaceOverrideMaterial(s, mat);
        }
    }
}

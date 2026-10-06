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
        string? FaceShape = null, float? Freckles = null);

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
        // The man survivor is the hero (tools/assets/hero_male_body.py) once
        // his outfits are made; till then the kit's man, and --body hero shows him.
        if (body == SurvivorUnchained.Play.Loadouts.HisBody && ResourceLoader.Exists("res://art/people/hero.glb") && Args.Get("body") == "hero") body = "hero";
        bool her = body == "heroine";
        if (her) Perf.Lap("play: (before her)");
        var p = body switch { SurvivorUnchained.Play.Loadouts.HerBody => Woman(look), "heroine" => Heroine(look), "hero" => Hero(look), "anime" => Her(look), _ => Build(look) };
        if (her) Perf.Lap("play: her body");
        if (body == "hero" && look.Face != null) HerFace(p, look.Face);
        // Her own clips are chosen by her calling, which her outfit says.
        if (p.Own != null) p.Calling = HerClips.Calling(look.Outfit);
        // Her body wears her calling's outfit, cut from it.
        if (her && look.Outfit.FirstOrDefault(o => o.StartsWith("her:")) is string set) HerOutfit(p, set[4..]);
        if (her) Perf.Lap("play: her outfit");
        // Her hair, a mesh of its own: the style chosen if it is one of hers;
        // her face shaped, and the paint on it.
        if (her)
        {
            HerHair(p, HerHairs.Contains(look.Hair) ? look.Hair! : HerHairs[0], look.HairColor ?? HerHairColour);
            HerScalp(p, look.HairColor ?? HerHairColour);
            HerFaceKey(p, look.FaceShape);
            Perf.Lap("play: her hair");
            if (look.Face != null) HerFace(p, look.Face);
            p.FaceShape = look.FaceShape;                 // (its painting laid as her skin was made: Skin)
            HerPaint(p, look.Paint, look.HairColor ?? HerHairColour);
            Perf.Lap("play: her face and paint");
        }
        // A child's larger head.
        if (spec.Head is double h && h != 1)
        {
            int head = p.Skeleton.FindBone("Head");
            if (head >= 0) p.Skeleton.SetBonePoseScale(head, Vector3.One * (float)h);
        }
        return p;
    }

    /// <summary>The scene files Build loads for a person, so they can be asked
    /// for ahead, all at once (Prefetch): the heroine's body, outfit and hair,
    /// or a kit body, its clothes, hair and beard. (The older bodies are left
    /// to load as they always have.)</summary>
    public static IEnumerable<string> Files(SurvivorUnchained.World.PersonSpec spec)
    {
        var look = LookOf(spec);
        var body = spec.Body;
        if (body == SurvivorUnchained.Play.Loadouts.HerBody && Args.Get("body") != "woman" && ResourceLoader.Exists("res://art/people/heroine.glb")) body = "heroine";
        if (body == "heroine")
        {
            yield return "res://art/people/heroine.glb";
            if (look.Outfit.FirstOrDefault(o => o.StartsWith("her:")) is string her) yield return $"res://art/people/heroine_outfit_{her[4..]}.gltf";
            yield return $"res://art/people/heroine_hair_{(HerHairs.Contains(look.Hair) ? look.Hair! : HerHairs[0])}.gltf";
            yield break;
        }
        if (body == SurvivorUnchained.Play.Loadouts.HerBody || body == "anime") yield break;
        yield return $"{Dir}/{(look.Sex == "female" ? "Superhero_Female_FullBody" : "Superhero_Male_FullBody")}.gltf";
        foreach (var part in look.Outfit) yield return $"{Dir}/{part}.gltf";
        if (look.Hair != null) yield return $"{Dir}/{look.Hair}.gltf";
        if (look.Beard) yield return $"{Dir}/Hair_Beard.gltf";
    }

    // Getting up ends in an idle but is not one: looped, a risen (or the Warden)
    // would lie down and get up again.
    static bool IsCycle(string n) =>
        (n.Contains("Idle") && !n.StartsWith("LayTo")) || n.Contains("Walk") || n.Contains("Jog") || n.Contains("Sprint") || n.Contains("Fwd") || n == "Dance";

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
        /// <summary>The colour her brows are dyed (her hair's), or none: as painted.</summary>
        public Color? Brow;
        /// <summary>Her head's pose as she is drawn (her corrective layer
        /// included, which a pose read in _Process is not), skeleton space.</summary>
        public Transform3D? HeadPose;
        /// <summary>A kit body (People.Build), a woman's or a man's; and, set
        /// by its view, whether it goes unarmed: the townsfolk, who play
        /// their own clips (FolkClips) where they have them.</summary>
        public bool Kit, Woman, Folk;
        /// <summary>The survivor's own clips (hers or his), when they have them.</summary>
        public OwnClips? Own;
        /// <summary>Gestures laid over whatever plays (a nod, an exhale).</summary>
        public Gestures? Gestures;
    }

    /// <summary>The clip a person plays for one the game names: a survivor's
    /// own where they have it ("her/...", "him/..."), the library's otherwise.</summary>
    public static string Clip(Person p, string name)
    {
        // One of the kit's own asked for by name ("folk/m_rise_stiff": the Warden in a cinematic).
        if (name.StartsWith(FolkClips.Prefix) && p.Anim.HasAnimation(name)) return name;
        if (p.Own is not { } own) return p.Folk && FolkClips.For(p.Woman, name) is string folk ? folk : Resolve(name);
        // (One of their own asked for by its own name.)
        if (own.Owns(name)) return own.Has(name[own.Prefix.Length..]) ? name : Resolve("Idle");
        return own.For(p.Calling, p.Kind, name) is string mine ? mine : Resolve(name);
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
        // (Not the hero's own outfit, "him:<calling>", which the kit has no part for.)
        var parts = look.Outfit.Where(o => !o.StartsWith("him:")).ToList();
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
    static PackedScene? heroineScene, heroScene;

    /// <summary>The woman survivor in the body made from the reference
    /// pictures: TRELLIS 2's model of the figure, bound to the game's own
    /// skeleton by tools/assets/bind_scan.py, so every clip plays on her; her
    /// skin, hair and suit are her own paint.</summary>
    public static Person Heroine(Look look)
    {
        // Kept for the session: read again at every place entered, her body
        // (73 MB imported, its paint inside it) cost 0.3-0.5 s each time.
        heroineScene ??= GD.Load<PackedScene>("res://art/people/heroine.glb");
        Perf.Lap("play: her body: loaded");
        var root = heroineScene.Instantiate<Node3D>();
        Perf.Lap("play: her body: instanced");
        var skel = (Skeleton3D)root.FindChildren("*", "Skeleton3D", true, false)[0];
        var person = new Person { Root = root, Skeleton = skel, Anim = new AnimationPlayer(), Body = "heroine" };
        person.Pose = new HerPose();
        skel.AddChild(person.Pose);
        person.Gestures = new Gestures();
        skel.AddChild(person.Gestures);
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
        Perf.Lap("play: her body: her materials");
        root.AddChild(person.Anim);
        person.Anim.RootNode = "..";
        person.Anim.AddAnimationLibrary("", Clips());
        // Her own clips beside the library's (tools/anim).
        if (OwnClips.Her.Library() is AnimationLibrary her)
        {
            person.Own = OwnClips.Her;
            person.Anim.AddAnimationLibrary(OwnClips.Her.Name, her);
        }
        Perf.Lap("play: her body: her clips");
        return person;
    }

    /// <summary>The man survivor, the hero: the owner's sculpt, rigged by
    /// AccuRIG and bound to the game's own skeleton by
    /// tools/assets/hero_male_body.py, with a head of his own
    /// (hero_male_head.py: eyes, lashes, teeth, his face's shapes). His skin,
    /// eyes and head are drawn as hers are (HerPart), his skin with the relief
    /// baked from his sculpt.</summary>
    public static Person Hero(Look look)
    {
        // Kept for the session, as hers is.
        heroScene ??= GD.Load<PackedScene>("res://art/people/hero.glb");
        var root = heroScene.Instantiate<Node3D>();
        var skel = (Skeleton3D)root.FindChildren("*", "Skeleton3D", true, false)[0];
        var person = new Person { Root = root, Skeleton = skel, Anim = new AnimationPlayer(), Body = "hero" };
        // His carriage over the library's clips: fingers eased, his arms held
        // clear of his lats rather than in, his hips square.
        person.Pose = new HerPose { ArmsIn = -5f, HipTilt = 0f, NeckPitch = HisNeckPitch };
        skel.AddChild(person.Pose);
        person.Gestures = new Gestures();
        skel.AddChild(person.Gestures);
        int headBone = skel.FindBone("Head");
        if (headBone >= 0) skel.SkeletonUpdated += () => person.HeadPose = skel.GetBoneGlobalPose(headBone);
        skel.AddChild(new HerFaceLife());
        foreach (var mi in skel.GetChildren().OfType<MeshInstance3D>())
        {
            person.Meshes.Add(mi);
            mi.Layers = 2;
            for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
                if (mi.Mesh.SurfaceGetMaterial(s) is BaseMaterial3D src)
                    mi.SetSurfaceOverrideMaterial(s, HerPart(src, look, mi.Mesh, "hero"));
        }
        root.AddChild(person.Anim);
        person.Anim.RootNode = "..";
        person.Anim.AddAnimationLibrary("", Clips());
        // His own clips beside the library's (tools/anim: hers, given a man's carriage).
        if (OwnClips.Him.Library() is AnimationLibrary him)
        {
            person.Own = OwnClips.Him;
            person.Anim.AddAnimationLibrary(OwnClips.Him.Name, him);
        }
        // Clean-shaven till a beard is chosen.
        HisShadow(person, 0f, 0f, look.HairColor ?? HisHairColour);
        return person;
    }

    /// <summary>His own hair colour when none is chosen: a dark brown.</summary>
    public static readonly Color HisHairColour = new("#3a2a20");

    /// <summary>His brows' paint as tools/assets/hero_male_head.py leaves it
    /// (it prints "BROWS painted"), the colour his brows are dyed from.</summary>
    static readonly Color HisBrowPaint = new("#4c3c2e");

    /// <summary>His head's shaved shadows and brows (shaders/heroine_skin.gdshader,
    /// head_tex/hero_shadow.png from hero_male_head.py): stubble on his beard's
    /// ground and his scalp, each 0 to 1, of his hair's colour, and his
    /// painted brows dyed to it.</summary>
    public static void HisShadow(Person p, float beard, float scalp, Color hair)
    {
        const string file = "res://art/people/head_tex/hero_shadow.png";
        if (!ResourceLoader.Exists(file)) return;
        var mask = GD.Load<Texture2D>(file);
        foreach (var mi in p.Meshes)
            for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
            {
                if (mi.Mesh.SurfaceGetMaterial(s)?.ResourceName != "skin_head" || mi.GetSurfaceOverrideMaterial(s) is not ShaderMaterial m) continue;
                m.SetShaderParameter("shadow_mask", mask);
                m.SetShaderParameter("beard_shadow", beard);
                m.SetShaderParameter("scalp_shadow", scalp);
                m.SetShaderParameter("shadow_colour", hair.Darkened(0.35f));
                // (Not yet: dyed, his painted brows read as a smudge of
                // colour, having no hairs. They're dyed once brow cards lie
                // over them, the painted ones lifted to their shadow.)
                m.SetShaderParameter("brow_dye", 0f);
                m.SetShaderParameter("brow_paint", HisBrowPaint);
                m.SetShaderParameter("brow_colour", hair);
            }
    }

    /// <summary>His own skin's tone when none is chosen: his paint as it is,
    /// barely warmed (hers is warmed further: her paint is paler).</summary>
    static readonly Color HisTone = new(1.0f, 0.95f, 0.9f);

    /// <summary>His neck leans further forward at rest than the library's
    /// body's: the library's clips throw his head back by about this much
    /// (HerPose.NeckPitch), till his own clips are made.</summary>
    const float HisNeckPitch = 22f;

    /// <summary>His own eyes: flint grey, a little warmer round the pupil (Lore's flint,
    /// the iris's own colour, as hers are dyed).</summary>
    static readonly (Color Iris, Color Ring) HisEyes = (new("#3b4038"), new("#4a4530"));

    /// <summary>Her own iris as painted (moss, no colour chosen), put right against her portrait's
    /// under a white light (linear; the eye shader's tint): as painted it showed 1.6 times as light
    /// as her portrait's and yellower.</summary>
    static readonly Vector3 HerPaintedIris = new(0.615f, 0.651f, 1.04f);

    /// <summary>Her hairstyles (tools/assets/heroine_head.py: a file each,
    /// fitted to her head), the first hers unless another is chosen.</summary>
    public static readonly string[] HerHairs = { "long", "ponytail", "braid", "bob", "pixie" };

    /// <summary>Her own hair colour, copper, as her portrait has it (under a white light its median
    /// within a few per cent of the portrait's; the old #8f2d14 rendered blood-red, its green and blue
    /// a fifth of the portrait's). (--hair-colour #rrggbb tries another.)</summary>
    public static readonly Color HerHairColour = SurvivorUnchained.Args.Get("hair-colour") is string hc ? new Color(hc) : new Color("#7a4824");

    /// <summary>A material of hers by its name (heroine_head.py names
    /// them): her skin, her eyes and the rest of her head.</summary>
    static Material HerPart(BaseMaterial3D src, Look look, Mesh mesh, string who = "heroine")
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
                var iris = $"res://art/people/head_tex/{who}_iris.png";
                e.SetShaderParameter("iris", GD.Load<Texture2D>(ResourceLoader.Exists(iris) ? iris : "res://art/people/head_tex/heroine_iris.png"));
                // (his own, when none is chosen: flint grey, Lore.Eyes' "flint")
                if (who == "hero" && look.Eyes == null) EyeColour(e, HisEyes.Iris, HisEyes.Ring);
                else EyeColour(e, look.Eyes, look.EyeRing);
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
                return Skin(src, look, mesh, who == "hero" ? HisTone : null, who);
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
        e.SetShaderParameter("tint", iris != null ? Colors.White : new Color(HerPaintedIris.X, HerPaintedIris.Y, HerPaintedIris.Z).LinearToSrgb());
        if (iris is not Color c) return;
        e.SetShaderParameter("iris_colour", c);
        e.SetShaderParameter("ring_colour", ring ?? c);
    }

    static Shader? paintShader;

    /// <summary>Her brows' dye (heroine_paint.gdshader): how far each hair is eased toward the skin, and
    /// how much of the dye's colour it takes. (--brows soften,sat tries others.)</summary>
    static readonly (float Soften, float Sat) HerBrows = SurvivorUnchained.Args.Get("brows") is string bw && bw.Split(',') is [var bs, var bt]
        ? (float.Parse(bs, System.Globalization.CultureInfo.InvariantCulture), float.Parse(bt, System.Globalization.CultureInfo.InvariantCulture))
        : (0.07f, 0.85f);

    /// <summary>Paint on her face (Lore.Her.Paints: art/people/paint/ID.png, laid
    /// out on her head's own paint by tools/assets/heroine_paint.py): drawn
    /// over her skin as a pass of its own, so it lies on the skin rather than
    /// in it, with its own sheen (chalky woad, waxy kohl, bright leaf), and
    /// moves with her face as it shapes and speaks. None: taken off.
    /// Under it, her brows dyed her hair's colour (art/people/paint/brows.png:
    /// her painted brows, found), since they are painted copper into her skin;
    /// her hair as it grew dyes them too, her own copper (as painted they read
    /// faint and grey beside her portrait's).</summary>
    public static void HerPaint(Person p, string? paint, Color? brow = null)
    {
        p.Paint = paint;
        p.Brow = brow;
        var def = paint == null ? null : SurvivorUnchained.World.Lore.Her.Paints.FirstOrDefault(x => x.Id == paint);
        var file = def == null ? "" : $"res://art/people/paint/{def.Id}.png";
        const string brows = "res://art/people/paint/brows.png";
        foreach (var mi in p.Meshes)
            for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
            {
                if (mi.Mesh.SurfaceGetMaterial(s)?.ResourceName != "skin_head" || mi.GetSurfaceOverrideMaterial(s) is not ShaderMaterial skin) continue;
                paintShader ??= GD.Load<Shader>("res://shaders/heroine_paint.gdshader");
                // The passes over her skin, in order: her brows, then the paint.
                ShaderMaterial? first = null, last = null;
                void Then(ShaderMaterial m) { if (last == null) first = m; else last.NextPass = m; last = m; }
                // (her own face's brows only: brows.png is where hers are, and on another
                // face it dyed that face's lid crease, a copper second brow under its own;
                // each other face keeps its portrait's brows as they are)
                if (brow is Color b && ResourceLoader.Exists(brows) && p.FaceShape is null or "" or "own")
                {
                    var m = new ShaderMaterial { Shader = paintShader };
                    m.SetShaderParameter("paint", GD.Load<Texture2D>(brows));
                    m.SetShaderParameter("dyed", true);
                    // (darker than her hair and a little warmer, as brows are: the fairer
                    // her hair the more, so a platinum blonde has ash-brown brows, not grey)
                    m.SetShaderParameter("dye", b.Darkened(0.25f + 0.15f * b.Luminance).Lerp(new Color("#6a4a30"), 0.2f));
                    m.SetShaderParameter("skin_paint", skin.GetShaderParameter("paint"));
                    m.SetShaderParameter("skin_tone", skin.GetShaderParameter("tone"));
                    m.SetShaderParameter("soften", HerBrows.Soften);
                    m.SetShaderParameter("dye_sat", HerBrows.Sat);
                    m.SetShaderParameter("rough", 0.8f);
                    Then(m);
                }
                if (def != null && ResourceLoader.Exists(file))
                {
                    var m = new ShaderMaterial { Shader = paintShader };
                    m.SetShaderParameter("paint", GD.Load<Texture2D>(file));
                    m.SetShaderParameter("rough", (float)def.Rough);
                    m.SetShaderParameter("metal", (float)def.Metal);
                    Then(m);
                }
                skin.NextPass = first;
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
                    if (m.Shader == hairShader || m.Shader == hairSoftShader) m.SetShaderParameter("colour", colour);
                    else if (m.Shader == skinShader2)
                    {
                        m.SetShaderParameter("tone", HerTone(look));
                        m.SetShaderParameter("face_tone", FaceTone(look));
                        m.SetShaderParameter("freckle_amount", HerFreckles(look));
                    }
                    else if (m.Shader == eyeShader) EyeColour(m, look.Eyes, look.EyeRing);
                }
                else if (mi.GetSurfaceOverrideMaterial(s) is StandardMaterial3D b && b.ResourceName == "brows") b.AlbedoColor = colour.Darkened(0.45f);
            }
        HerScalp(p, colour);
        HerFace(p, look.Face ?? new Dictionary<string, float>(), whole: true);
        HerFaceKey(p, look.FaceShape);
        if (look.FaceShape != p.FaceShape) HerHeadPaint(p, look.FaceShape);
        // (laid again each time: her brows' dye stands on her skin's tone and her face's own paint)
        HerPaint(p, look.Paint, colour);
    }

    /// <summary>Her scalp under her hair darkened to her hair's colour
    /// (head_tex/heroine_shadow.png from tools/assets/heroine_features.py:
    /// green from her hairline up), so between the cards there is hair, not
    /// skin: bare, her scalp read as a pale, bald brow, worst under dark hair.</summary>
    public static void HerScalp(Person p, Color hair)
    {
        const string file = "res://art/people/head_tex/heroine_shadow.png";
        if (!ResourceLoader.Exists(file)) return;
        var mask = GD.Load<Texture2D>(file);
        int set = 0;
        foreach (var mi in p.Meshes)
            for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
            {
                if (mi.Mesh.SurfaceGetMaterial(s)?.ResourceName != "skin_head" || mi.GetSurfaceOverrideMaterial(s) is not ShaderMaterial m) continue;
                m.SetShaderParameter("shadow_mask", mask);
                m.SetShaderParameter("scalp_shadow", 1.0f);
                m.SetShaderParameter("scalp_stubs", 0.0f);
                m.SetShaderParameter("shadow_colour", hair.Darkened(0.3f));
                set++;
            }
        if (Args.Has("shot")) GD.Print($"HerScalp: {set} surfaces");
    }

    /// <summary>Her face as one she started from (Lore.Her's faces): its
    /// whole shape, a key of its own on her head, its parts and her hair
    /// (face_&lt;id&gt;, tools/assets/heroine_head.py: from her own face to it,
    /// laid on a head TRELLIS made of its portrait), the others off; none, her own.</summary>
    public static void HerFaceKey(Person p, string? face)
    {
        var want = face is { Length: > 0 } ? "face_" + face : null;
        foreach (var mi in p.Meshes)
        {
            if (mi.Mesh is not ArrayMesh am) continue;
            for (int i = 0; i < am.GetBlendShapeCount(); i++)
            {
                // (not the face_width and face_shape sliders' keys: theirs end in + or -)
                var name = am.GetBlendShapeName(i).ToString();
                if (name.StartsWith("face_") && !name.EndsWith('+') && !name.EndsWith('-')) mi.SetBlendShapeValue(i, name == want ? 1f : 0f);
            }
        }
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

    static Shader? hairShader, hairSoftShader, eyeShader;

    /// <summary>Hair: her hair cards (tools/assets/heroine_hair.py) by
    /// shaders/heroine_hair.gdshader, dyed: the strands' atlas cut to its
    /// strands, darker at the roots and deep in, with the long highlight
    /// across them.</summary>
    static Material Hair(BaseMaterial3D src, Color colour)
    {
        hairShader ??= GD.Load<Shader>("res://shaders/heroine_hair.gdshader");
        hairSoftShader ??= GD.Load<Shader>("res://shaders/heroine_hair_soft.gdshader");
        // (the cap on her scalp and the fine hairs at her hairline blended, as
        // they thin out into her skin; the fine hairs over the cap)
        bool soft = src.ResourceName is "hair_cap" or "hair_fine";
        var m = new ShaderMaterial { Shader = soft ? hairSoftShader : hairShader, RenderPriority = src.ResourceName == "hair_fine" ? 1 : 0 };
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
        // Plate holds her: under the warden's formed cups her breasts swing
        // less and never squash (metal does not give); cloth and leather move
        // with her as her own skin does.
        if (p.Skeleton.GetNodeOrNull<HerJiggle>("HerJiggle") is HerJiggle jig)
        {
            jig.Amount = set == "warden" ? 0.55f : 1f;
            jig.Squash = set == "warden" ? 0f : 1f;
        }
        // Her skin under the outfit's fitted pieces is drawn tucked in: each
        // outfit marks it in one channel of her vertex colours.
        int ch = System.Array.IndexOf(OutfitChannels, set);
        foreach (var mi in p.Skeleton.GetChildren().OfType<MeshInstance3D>())
            if (!mi.Name.ToString().Contains('.') && !mi.Name.ToString().Contains('_')) TuckSkin(mi, ch);
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

    /// <summary>Her skin under the outfit tucked a few millimetres in by her
    /// skin's shader (shaders/heroine_skin.gdshader), not cut away: cut, a
    /// gap opened in her wherever a piece swung off her as she moved.</summary>
    static void TuckSkin(MeshInstance3D mi, int ch)
    {
        // (Only her body is marked; her head is left as it is, shape keys and all.)
        if (mi.Mesh is not ArrayMesh am || (am.SurfaceGetFormat(0) & Mesh.ArrayFormat.FormatColor) == 0) return;
        for (int s = 0; s < mi.GetSurfaceOverrideMaterialCount(); s++)
            if (mi.GetSurfaceOverrideMaterial(s) is ShaderMaterial m && m.Shader == skinShader2)
                m.SetShaderParameter("tuck_channel", ch);
    }

    /// <summary>Her paint as skin: light carried under it (subsurface
    /// scattering, reddened as through flesh), a soft sheen rather than
    /// plastic, and warmed toward a sun-browned tone, or the tone chosen.</summary>
    static Material Skin(BaseMaterial3D src, Look look, Mesh mesh, Color? own = null, string who = "heroine")
    {
        // shaders/heroine_skin.gdshader: pores, soft uneven sheen, light
        // under the skin. (Her vertex colours mark what each outfit covers,
        // to tuck in, never her paint.)
        skinShader2 ??= GD.Load<Shader>("res://shaders/heroine_skin.gdshader");
        var m = new ShaderMaterial { Shader = skinShader2 };
        m.SetShaderParameter("paint", src.AlbedoTexture);
        m.SetShaderParameter("tone", who == "heroine" && own == null ? HerTone(look) : look.Skin is Color ? SkinTone(look) : own ?? SkinTone(look));
        if (who == "heroine")
        {
            m.SetShaderParameter("face_tone", FaceTone(look));
            // (her face's own fine grain on her neck and body: tools/assets/heroine_grain.py)
            if (ResourceLoader.Exists("res://art/people/head_tex/heroine_grain.png"))
            {
                m.SetShaderParameter("grain", GD.Load<Texture2D>("res://art/people/head_tex/heroine_grain.png"));
                m.SetShaderParameter("grain_amount", HerGrain);
            }
        }
        // A body's relief baked from its sculpt (the hero's), under the pores.
        if (src.NormalTexture != null)
        {
            m.SetShaderParameter("relief", src.NormalTexture);
            m.SetShaderParameter("has_relief", true);
        }
        m.SetShaderParameter("pores", GD.Load<Texture2D>("res://art/people/skin_pores.png"));
        m.SetShaderParameter("pore_scale", PoreScale(mesh));
        // Shallower on the body and hands than the face, where pores show
        // most: at the face's depth her hands read as pitted in close-up.
        if (src.ResourceName != "skin_head") m.SetShaderParameter("pore_depth", 0.4f);
        // Her face a little more matte than her body: at the shine her body
        // has, her face read as plastic, and a light from behind lit the
        // side of her brow as a hard white band.
        // (hers alone: his head's paint is laid out otherwise)
        if (src.ResourceName == "skin_head" && who == "heroine")
        {
            if (HeadPaintFile(look.FaceShape) is string painted) m.SetShaderParameter("paint", GD.Load<Texture2D>(painted));
            m.SetShaderParameter("rough", 0.6f);
            m.SetShaderParameter("shine", 0.36f);
            // (her eyes, brows and lips deepened when her face is small on
            // screen, so a face still reads from the game's camera)
            if (ResourceLoader.Exists("res://art/people/head_tex/heroine_features.png"))
                m.SetShaderParameter("features", GD.Load<Texture2D>("res://art/people/head_tex/heroine_features.png"));
            // (and her head's own shade, under her jaw most: unshaded, her neck under
            // it was lit as her cheeks were, a pale band down to her collar)
            if (ResourceLoader.Exists("res://art/people/head_tex/heroine_ao.png"))
            {
                m.SetShaderParameter("ao_map", GD.Load<Texture2D>("res://art/people/head_tex/heroine_ao.png"));
                m.SetShaderParameter("ao_light", 0.55f);
            }
        }
        // Her freckles, a layer over her face, neck, shoulders and upper chest
        // (tools/assets/heroine_freckles.py), as many as her face starts with.
        if (who == "heroine" && FreckleFile(src.ResourceName) is string fp)
        {
            m.SetShaderParameter("freckles", GD.Load<Texture2D>(fp));
            m.SetShaderParameter("freckle_amount", HerFreckles(look));
        }
        // His skin, all of it, rougher than hers: at her sheen his deep
        // relief caught the light as wet plastic.
        if (who == "hero")
        {
            m.SetShaderParameter("rough", HisSkin.Rough);
            m.SetShaderParameter("shine", HisSkin.Shine);
            m.SetShaderParameter("edge_rough", HisSkin.Edge);
        }
        return m;
    }

    /// <summary>His skin's roughness, sheen, and the roughness it gains seen
    /// edge on (shaders/heroine_skin.gdshader).</summary>
    static readonly (float Rough, float Shine, float Edge) HisSkin = (0.62f, 0.3f, 0.45f);

    /// <summary>Her skin's tone: the one chosen, or her own, barely warmed.
    /// (Her face is painted from her reference photograph now, its own
    /// peach: warmed as much as the old pale paint was, under the portrait's
    /// warm key she read a uniform orange-pink, like a doll. A tone chosen is
    /// eased toward white the less the darker it is: eased as far as a fair
    /// one, a brown or olive skin read pale and pink beside the faces painted
    /// from photographs of women of that colouring.)</summary>
    static Color SkinTone(Look look) =>
        look.Skin is Color tone ? tone.Lerp(Colors.White, 0.35f * Mathf.Clamp(tone.Luminance * 1.1f, 0.25f, 1f)) : new Color(1.0f, 0.93f, 0.87f);

    /// <summary>Her skin as each swatch should show on her (in linear light, on SkinTone's): under a
    /// white light each face beside its portrait (tools: the face lead's tone_fit.py, every face shot
    /// --rig-white). As SkinTone alone gave them, her fair skins rendered 8% too red, the rose and warm
    /// ones 14%, and Sunborn's brown 1.2 times too light and too blue. Hers only: the swatches stay as
    /// they are for the beads and for the folk. (Round two, v11: each within 2% of its faces' mean.)</summary>
    static readonly Dictionary<string, Vector3> HerToneFit = new()
    {
        ["fair"] = new(0.897f, 1.094f, 1.009f), ["rose"] = new(0.849f, 1.062f, 0.827f),
        ["warm"] = new(0.886f, 1.054f, 0.791f), ["brown"] = new(0.877f, 0.887f, 0.629f),
    };

    /// <summary>Each face's own paint against its portrait, once its swatch is fitted (linear, the
    /// skin shader's face_tone, laid on her face alone): one swatch serves several faces, and a face's
    /// paint came out up to 8% off its portrait (Fey 6% dark, Vixen too blue, Moonlit too red), so
    /// beside it the face read a shade wrong while its neck was right.</summary>
    static readonly Dictionary<string, Vector3> HerFaceTone = new()
    {
        ["own"] = new(1.004f, 0.995f, 0.985f), ["highborn"] = new(0.981f, 0.981f, 0.969f),
        ["vixen"] = new(0.982f, 0.940f, 0.922f), ["moonlit"] = new(0.972f, 1.021f, 1.080f),
        ["fey"] = new(1.062f, 1.067f, 1.050f), ["doe"] = new(1.004f, 1.016f, 1.013f),
        ["wildling"] = new(0.992f, 0.969f, 0.957f), ["hardwon"] = new(1.004f, 1.016f, 1.032f),
    };

    /// <summary>How much of her face's own grain her neck and body take (the skin shader's
    /// grain_amount; 1 her face's paint's own spread): her portrait's neck has nearly half her
    /// face's grain, and her neck's relief alone gave it a quarter. (--grain tries another.)</summary>
    static readonly float HerGrain = SurvivorUnchained.Args.Has("grain") ? SurvivorUnchained.Args.Num("grain", 3f) : 3f;

    static Vector3 FaceTone(Look look) =>
        HerFaceTone.TryGetValue(string.IsNullOrEmpty(look.FaceShape) ? "own" : look.FaceShape, out var f) ? f : Vector3.One;

    /// <summary>Her freckles' map for a part of her skin, if it has one: her head's, or the graft's (her
    /// neck, shoulders and upper chest).</summary>
    static string? FreckleFile(string part)
    {
        var f = part switch
        {
            "skin_head" => "res://art/people/head_tex/heroine_freckles.png",
            "skin_graft" => "res://art/people/head_tex/heroine_freckles_graft.png",
            _ => null,
        };
        return f != null && ResourceLoader.Exists(f) ? f : null;
    }

    /// <summary>How freckled she is (0 none to 1 heavy): as the Look sets it, else as her face starts
    /// (looks.json's faces, each from its portrait: her own light, most none); a face the player has
    /// shaped by hand is her own making, not the portrait's, and starts with none (the owner: "none is
    /// probably the preferred for most people").</summary>
    public static float HerFreckles(Look look) => look.Freckles ?? (look.Face?.Values.Any(v => Mathf.Abs(v) > 0.01f) == true ? 0f
        : (float)(SurvivorUnchained.World.Lore.Her.Faces
            .FirstOrDefault(f => f.Id == (string.IsNullOrEmpty(look.FaceShape) ? "own" : look.FaceShape))?.Freckles ?? 0));

    static Color HerTone(Look look)
    {
        var t = SkinTone(look);
        string id = look.Skin is Color c
            ? SurvivorUnchained.World.Lore.Skins.FirstOrDefault(s => s.Color != "" && new Color(s.Color).IsEqualApprox(c))?.Id ?? ""
            : "fair";
        if (!HerToneFit.TryGetValue(id, out var f)) return t;
        var l = t.SrgbToLinear();
        return new Color(l.R * f.X, l.G * f.Y, l.B * f.Z).LinearToSrgb();
    }

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
        k = uvArea > 0 ? (float)(Math.Sqrt(area / uvArea) / 0.009) : 50f;
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

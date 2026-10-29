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
        string? FaceShape = null, float? Freckles = null, Color? Highlight = null);

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
            sex == "female" ? spec.Figure ?? 1 : 0, spec.Face?.ToDictionary(f => f.Key, f => (float)f.Value), C(spec.Eyes), C(spec.EyeRing), spec.Paint, spec.FaceShape, Highlight: C(spec.HairHighlight));
    }

    /// <summary>Held while a person is made (WalkerView makes townsfolk on a worker thread; the caches here are shared).</summary>
    public static readonly object BuildLock = new();

    public static Person Build(SurvivorUnchained.World.PersonSpec spec)
    {
        lock (BuildLock) return BuildLocked(spec);
    }

    static Person BuildLocked(SurvivorUnchained.World.PersonSpec spec)
    {
        var look = LookOf(spec);
        var body = spec.Body;
        // A person Marionette made, from its package (art/npc/NAME): no code of its own.
        if (NpcPackage.NameOf(body) is string pkg && NpcPackage.Build(pkg) is Person made)
        {
            // (its own colours, height and place in its loops, per copy: NpcDye)
            NpcDye.Apply(made, pkg, spec);
            return made;
        }
        // The woman survivor is the heroine (tools/assets/build_heroine.py),
        // in her calling's outfit; --body woman brings back the older body.
        if (body == SurvivorUnchained.Play.Loadouts.HerBody && Args.Get("body") != "woman" && ResourceLoader.Exists("res://art/people/heroine.glb")) body = "heroine";
        // The man survivor is the hero (tools/assets/hero_male_body.py) once
        // his outfits are made; till then the kit's man, and --body hero shows him.
        if (body == SurvivorUnchained.Play.Loadouts.HisBody && ResourceLoader.Exists("res://art/people/hero.glb") && Args.Get("body") == "hero") body = "hero";
        bool her = body == "heroine";
        string? hairHider = null;   // (the worn head piece whose row says "hair": "hide": her hair mesh is left off)
        if (her) Perf.Lap("play: (before her)");
        var p = body switch { SurvivorUnchained.Play.Loadouts.HerBody => Woman(look), "heroine" => Heroine(look), "hero" => Hero(look), "anime" => Her(look), _ => Build(look) };
        if (her) Perf.Lap("play: her body");
        if (body == "hero" && look.Face != null) HerFace(p, look.Face);
        // Her own clips are chosen by her calling, which her outfit says.
        if (p.Own != null) p.Calling = HerClips.Calling(look.Outfit);
        // Her body wears her calling's outfit, cut from it.
        // (piece by piece when her equipment wears a piece or a shot says --wear: HerWear)
        if (her && look.Outfit.FirstOrDefault(o => o.StartsWith("her:")) is string set)
        {
            if (HerWear.LookFor(set[4..], spec.Worn, spec.HideSlots) is { } wear) { HerWear.Apply(p, set[4..], wear, spec.WornDye); hairHider = HerWear.HairHider(wear); }
            else HerOutfit(p, set[4..]);
        }
        if (her) Perf.Lap("play: her outfit");
        if (her) HerDraws.Watch(p);
        // Her hair, a mesh of its own: the style chosen if it is one of hers;
        // her face shaped, and the paint on it.
        if (her)
        {
            var hairStyle = HerHairs.Contains(look.Hair) ? look.Hair! : HerHairs[0];
            if (hairHider == null) HerHair(p, hairStyle, look.HairColor ?? HerHairColour, look.Highlight);
            else { p.HairStyle = hairStyle; GD.Print($"her wear: hair hidden by {hairHider}"); }
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
        if (NpcPackage.NameOf(body) is string pkg)
        {
            foreach (var f in NpcPackage.Files(pkg)) yield return f;
            yield break;
        }
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
        /// <summary>A package copy's height factor (NpcDye, random mode; PersonView scales by it) and where in its
        /// loops it starts (0..1; -1: at their start).</summary>
        public float Jitter = 1f, Phase = -1f;
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
        /// <summary>Her face's own lower-lip fullness (FaceShape.Lips) and the player's lips_lower slider, summed on
        /// the key (HerFace, HerFaceKey).</summary>
        public float LipsBase, LipsSlider;
        /// <summary>The colour her brows are dyed (her hair's), or none: as painted.</summary>
        public Color? Brow;
        /// <summary>Her head's pose as she is drawn (her corrective layer
        /// included, which a pose read in _Process is not), skeleton space.</summary>
        public Transform3D? HeadPose;
        /// <summary>A kit body (People.Build), a woman's or a man's; and, set
        /// by its view, whether it goes unarmed: the townsfolk, who play
        /// their own clips (FolkClips) where they have them.</summary>
        public bool Kit, Woman, Folk;
        /// <summary>The Marionette package it was built from (NpcPackage: "npc:NAME"), or none.</summary>
        public string? Package;
        /// <summary>The survivor's own clips (hers or his), when they have them.</summary>
        public OwnClips? Own;
        /// <summary>Gestures laid over whatever plays (a nod, an exhale).</summary>
        public Gestures? Gestures;
    }

    /// <summary>The clip a person plays for one the game names: a survivor's
    /// own where they have it ("her/...", "him/..."), the library's otherwise. `sheathed`: her town stand and run
    /// (Play/Sheath.Names: the held kind's own, then the calling's, then the armed ones).</summary>
    /// <summary>`kind`: the kind held, if not the person's own ("" for empty hands: creation's look, its pieces put
    /// away, plays the calling's town stand, not the stand made around a hilt and a shield).</summary>
    public static string Clip(Person p, string name, bool sheathed = false, string? kind = null)
    {
        // One of the kit's own asked for by name ("folk/m_rise_stiff": the Warden in a cinematic).
        if (name.StartsWith(FolkClips.Prefix) && p.Anim.HasAnimation(name)) return name;
        if (p.Own is not { } own)
        {
            // The armed townsfolk's stands (the town's data asks for them by name), armed or not; with no folk
            // library, the library's idle.
            if (FolkClips.ArmedName(name) != null && (p.Kit || p.Package != null))
                return FolkClips.Armed(p.Woman, name) ?? Resolve("Idle");
            // (the crossed arms break on the generated packages, their full sleeves a rigid bar with no hands: their
            // weight-shift stand instead, NPC 17)
            if (p.Package != null && name is "Idle_FoldArms_Loop" or "Idle_FoldArms") name = "Idle";
            return p.Folk && FolkClips.For(p.Woman, name) is string folk ? folk : Resolve(name);
        }
        // (One of their own asked for by its own name.)
        if (own.Owns(name)) return own.Has(name[own.Prefix.Length..]) ? name : Resolve("Idle");
        return own.For(p.Calling, kind ?? p.Kind, name, sheathed) is string mine ? mine : Resolve(name);
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
        // Her clavicle lift as an arm rises above level (the hands kept), before the shapes and twists read the arm.
        skel.AddChild(new HerShrug());
        // The pectoral's pull on her breasts as an arm rises, before the springs follow it.
        skel.AddChild(new HerRaise());
        // Her scapulae turned up as each arm rises (only a body built with them: scap_rig_post.py).
        skel.AddChild(new HerScap());
        skel.AddChild(new HerJiggle());
        skel.AddChild(new HerFaceLife());
        // Her twist and share bones, from the pose every layer above has made.
        skel.AddChild(new HerJoints());
        // Her shoulder's muscle helpers (delt, trap, pec, lat) from the arm's angle, after the scapulae and the twist
        // bones (the delt is twist_02's child; shoulder_rig_post.py).
        skel.AddChild(new HerShoulder());
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
        // His twist and share bones, once his body is built with them (as hers).
        skel.AddChild(new HerJoints());
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
    static readonly Vector3 HerPaintedIris = new(0.816f, 0.766f, 1.071f);

    /// <summary>Her hairstyles (tools/assets/heroine_head.py: a file each,
    /// fitted to her head), the first hers unless another is chosen. Long and bob (art kept on disk)
    /// are out until rebuilt (the owner, 18 Oct): an old "long" or "bob" falls to the braid.</summary>
    public static readonly string[] HerHairs = { "braid", "ponytail", "pixie" };

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
                if (who != "hero") HerEyes(e, look.FaceShape, look.Skin);
                return e;
            case "brows" or "lashes":
                // Cards cut out by their alpha, soft at the edges; brows
                // a shade of her hair, lashes near black.
                m.Transparency = BaseMaterial3D.TransparencyEnum.AlphaScissor;
                m.AlphaScissorThreshold = 0.35f;
                m.AlphaAntialiasingMode = BaseMaterial3D.AlphaAntiAliasing.AlphaToCoverageAndToOne;
                m.CullMode = BaseMaterial3D.CullModeEnum.Disabled;
                // (the lashes' own colour is in their paint, tools/assets/heroine_lashes.py: a dark brown, lighter
                // toward the tips)
                m.AlbedoColor = src.ResourceName == "brows" ? hair.Darkened(0.45f) : Colors.White;
                if (src.ResourceName == "lashes")                  // (painted hair by hair: tools/assets/heroine_lashes.py)
                    m.AlbedoTexture = TextureOrTry("res://art/people/head_tex/heroine_lashes.png", "lashes");
                m.Roughness = 0.8f;
                return HairDraw.Cards(m) ?? Coverage.Cards(m);
            case "teeth":
                // (her side teeth, and all of them while her lips are closed, in the mouth's own warm shade:
                // shaders/heroine_teeth.gdshader, lit by HerFaceLife.TeethLight)
                teethShader ??= GD.Load<Shader>("res://shaders/heroine_teeth.gdshader");
                var th = new ShaderMaterial { Shader = teethShader, ResourceName = "teeth" };
                th.SetShaderParameter("paint", src.AlbedoTexture);
                return th;
            case "tongue":
                // (its own shade inside her mouth, lit at its tip and dark at its root: heroine_mouth.py's vertex colour,
                // white where a mesh has none; no shadows, as their maps hatched it and cut a hard black edge over it
                // (the smile pass, e1): shaders/heroine_tongue.gdshader. Its paint a bright salmon pink, read as a
                // plastic slab inside her mouth at the Look (a2): the shader mutes it to a darker rose)
                tongueShader ??= GD.Load<Shader>("res://shaders/heroine_tongue.gdshader");
                var tg = new ShaderMaterial { Shader = tongueShader, ResourceName = "tongue" };
                tg.SetShaderParameter("paint", src.AlbedoTexture);
                return tg;
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
            foreach (var (name, v0) in all)
            {
                var v = v0;
                if (name == "lips_lower") { p.LipsSlider = v0; v = Mathf.Clamp(v0 + p.LipsBase, -1, 1.5f); }
                Shape(mi, name + "+", Mathf.Max(v, 0));
                Shape(mi, name + "-", Mathf.Max(-v, 0));
                Shape(mi, name, v);
            }
            // (her smile with her mouth open lifts her upper lip off her teeth: smile_open, heroine_mouth.py, as her
            // smile times how far her lips are parted, full by mouth_open 0.3; with her lips closed a smile stays
            // closed-lipped); and smile_hold, her philtrum and nose's foot held up against mouth_open's drop, as her smile
            // times mouth_open itself (so her nose's foot doesn't rise and fall back as her lips part)
            int so = mi.FindBlendShapeByName("smile_open");
            if (so >= 0 && mi.FindBlendShapeByName("smile") is int sm and >= 0 && mi.FindBlendShapeByName("mouth_open") is int mo and >= 0)
            {
                float m = mi.GetBlendShapeValue(mo), o = Mathf.Clamp(m / 0.3f, 0, 1);
                mi.SetBlendShapeValue(so, mi.GetBlendShapeValue(sm) * o * o * (3 - 2 * o));
                int sh = mi.FindBlendShapeByName("smile_hold");
                if (sh >= 0) mi.SetBlendShapeValue(sh, mi.GetBlendShapeValue(sm) * Mathf.Clamp(m, 0, 1));
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
    public static void HerHair(Person p, string style, Color colour, Color? highlight = null)
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
                {
                    var hm = Hair(src, colour, highlight, style, src.ResourceName == "hair_cap" && HasRopes(mi.Mesh, s));
                    // (face 32 r2b: the pixie's lifted cards' undersides lit as their tops, not dark: heroine_hair.gdshaderinc's fibre_back)
                    if (style == "pixie" && hm is ShaderMaterial sm)
                        foreach (var pass in HairDraw.Passes(sm)) pass.SetShaderParameter("fibre_back", true);
                    mi.SetSurfaceOverrideMaterial(s, hm);
                }
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
        var rest = p.Skeleton.GetBoneGlobalRest(hb);
        var moved = (p.HeadPose ?? p.Skeleton.GetBoneGlobalPose(hb)) * rest.AffineInverse();
        // (between her eyes at rest: 8.2 cm over and 11.1 cm in front of her Head joint, so they ride with its rest:
        // her neck 3 cm shorter, 18 October 2026, lowered the joint; at 1.748 m fixed the Look aimed over her eyes)
        return p.Skeleton.GlobalTransform * (moved * (rest.Origin + new Vector3(0, 0.082f, 0.111f)));
    }

    /// <summary>Her eyes' colour (shaders/heroine_eye.gdshader): the iris's
    /// paint keeps its fibres and crypts, its light and dark, and takes the
    /// colour chosen, the ring round the pupil its own (as a blue eye's amber
    /// collarette); none chosen keeps the paint's own green.</summary>
    /// <summary>Her eyes as her portraits have them (a judge's measures beside them, round 2, 10 October 2026: iris
    /// edges fitted, not MediaPipe's guesses on a render), the hero's left as they were: irises 0.117 of the paint
    /// (0.13 read 7-21% big against pupil distance and face width); a thin limbal ring from 0.85 of the radius,
    /// lighter on a dyed iris; the iris's blotches softened, its amber drawn in to a thin collarette darker than
    /// the outer iris (lighter, it read as a starburst); the catchlight a cool window at the pupil's edge, taking
    /// the iris's colour out under it (added, it read pink); pupils near black after the iris's tint (lighter
    /// than a brown iris, they read as cataracts); the whites ivory, lit from below, the upper lid's shadow at
    /// its visible margin, a wet line on the lower lid. Per face (looks.json faces): the iris's size, the pupil,
    /// how light the whites stand, and where the lid covers the iris.</summary>
    /// <summary>Her pupils over each face's own (looks.json's "pupil"), face 38 r3.</summary>
    public const float PupilOpen = 1.35f;

    static void HerEyes(ShaderMaterial e, string? face, Color? skin = null)
    {
        var f = SurvivorUnchained.World.Lore.Her.Faces.FirstOrDefault(x => x.Id == (face is { Length: > 0 } ? face : "own"));
        e.SetShaderParameter("iris_r", f is { Iris: > 0 } ? (float)f.Iris : 0.117f);
        // (face 38 r3, judge j2b: the pupils opened a third (the Look's read 0.19 of the iris, tight and hard; ~0.27
        // softer and more alive, and turned it stays a pupil, not a slit))
        e.SetShaderParameter("pupil", Mathf.Min(PupilOpen * (f is { Pupil: > 0 } ? (float)f.Pupil : 0.28f), 0.4f));
        bool dyed = e.GetShaderParameter("recolour").AsSingle() > 0f;
        e.SetShaderParameter("limbal", dyed ? 0.32f : 0.42f);
        e.SetShaderParameter("limbal_from", 0.85f);
        e.SetShaderParameter("iris_contrast", 0.45f);
        e.SetShaderParameter("ring_to", 0.35f);
        e.SetShaderParameter("ring_light", 0.8f);
        e.SetShaderParameter("iris_light", 1.0f);
        // (the catchlight a soft window over the pupil's upper edge, 11 to 1 o'clock as in the portraits, about a
        // sixth of the iris's radius across; a small hard dot at 10 to 11 read as a render, judge j2)
        e.SetShaderParameter("catch_size", 1.6f);
        e.SetShaderParameter("catchlight", 0.45f);
        e.SetShaderParameter("catch_soft", 1.8f);
        e.SetShaderParameter("catch_window", 0.2f);
        e.SetShaderParameter("catch_at", new Vector2(-0.2f, -0.28f));
        e.SetShaderParameter("catch_colour", new Vector3(0.9f, 0.95f, 1.08f));
        e.SetShaderParameter("catch_dim", 0.4f);
        // (face 38: at the Look the 2.8-wide square window, full white over the pupil, read glassy: smaller, softer,
        // rounder, the cornea a little less wet, the iris a little less saturated (D))
        e.SetShaderParameter("wet", 0.3f);
        e.SetShaderParameter("iris_sat", 1.1f);
        // (face 38 r2, judge j1: at the Look the iris darker (L 0.47 to ~0.40) and its green back (C ~0.05); the
        // catchlight rounder, at 10 to 11 o'clock over the pupil's edge; the pupil's reflection (navy, L 0.28) cut;
        // turned 40 the parallax's slope capped and halved (the pupil a sliver, the far iris streaked))
        e.SetShaderParameter("pupil_wet", 0.2f);
        e.SetShaderParameter("depth", 0.06f);
        e.SetShaderParameter("par_max", 1.2f);
        // (small on screen, the town close-up's ~7 px iris: iris and white had gone one grey (iris Oklab C 0.02, L
        // above the white's), its catchlight a 2 px blob at L 0.8; the white kept, the iris its own green and
        // darker than the white, the catchlight dimmed and shrunk)
        e.SetShaderParameter("far_white", 0.45f);
        e.SetShaderParameter("far_sat", 1.0f);
        e.SetShaderParameter("far_iris", 0.15f);
        e.SetShaderParameter("catch_far", 0.35f);
        e.SetShaderParameter("catch_far_size", 0.4f);
        e.SetShaderParameter("pupil_dark", 0.010f);
        // (face 38 r3: turned 40 the near eye's pupil read a cat's slit (3x8 px) and its catchlight went out: the
        // iris and pupil seen through the cornea's lens, foreshortened less than the ball; the catchlight round on
        // screen and held near the pupil; the eye's size on screen from its footprint's short side, so turning
        // her does not count as distance)
        e.SetShaderParameter("cornea_round", 0.7f);
        e.SetShaderParameter("catch_round", 1f);
        e.SetShaderParameter("catch_drift", 0.12f);
        e.SetShaderParameter("far_iso", 1f);
        var w = f is { Whites: > 0 } ? (float)f.Whites : 1f;
        // (deeper skin, its whites a little lower and warmer: at full white they glowed against it, face 38;
        // `deep` 0 at her fair skin's lightness (Oklab L ~0.75 and over), 1 at a deep one's)
        float deep = skin is Color sk ? Mathf.Clamp((0.75f - Oklch(sk).L) / 0.3f, 0f, 1f) : 0f;
        // (the lowering and warming done in the shader, `skin_deep`: deep_white 1 = (0.58, 0.50, 0.40) at deep)
        e.SetShaderParameter("white_tint", new Vector3(0.74f, 0.68f, 0.58f) * w);
        e.SetShaderParameter("skin_deep", deep);
        // (deep: the whites lowered half as far (they sat on the iris at the Look), the iris darkened with them; face 39,
        // judge j3b: at the Look turned they read a little stark, 0.5 to 1.25 of the way, about a tenth lower and warmer)
        e.SetShaderParameter("deep_white", 1.25f);
        e.SetShaderParameter("deep_iris", 0.3f);
        e.SetShaderParameter("white_grad", 0.35f);
        e.SetShaderParameter("corner_pink", 0.3f);
        // (the lid's shadow from where the face's lid covers its iris: its margin a twentieth of a radius above
        // where it shows, so no unshadowed sliver, and none hidden above it under the lashes)
        float cover = f is { Cover: > 0 } ? (float)f.Cover : 0.2f;
        e.SetShaderParameter("lid_shadow", 0.7f);
        e.SetShaderParameter("lid_y", 2f * cover - 1.05f);
        e.SetShaderParameter("lid_fade", 0.8f);
        e.SetShaderParameter("low_wet", 1.5f);
        e.SetShaderParameter("low_y", 0.95f);
        e.SetShaderParameter("low_lift", 0.12f);
        // (face 39, judge j3b: by night (HerEyesNight, the close view's night key) the lids' and corners' shade on
        // the eye eased 0.6 of itself and the iris lifted 1.8x, held to 0.9 of its colour and warmed to olive: the
        // fair night close-up's iris read 14-22 of 255, one near-black disc with the pupil, now ~34; deep skin's
        // eyes left as dark as its face; face 44, judge b1: 1.8 read lit from inside at the night close-up, 1.5 a natural green)
        e.SetShaderParameter("night_lid", 0.6f);
        e.SetShaderParameter("night_iris", 1.5f);
        e.SetShaderParameter("night_sat", 0.9f);
        e.SetShaderParameter("night_warm", 1f);
        // (--eye-set "iris_r=0.13,pupil=0.24": a developer's switch, her eyes' uniforms tried without a build)
        if (SurvivorUnchained.Args.Get("eye-set") is string es)
            foreach (var kv in es.Split(','))
                if (kv.Split('=') is [var k, var v] && float.TryParse(v, System.Globalization.NumberStyles.Float,
                        System.Globalization.CultureInfo.InvariantCulture, out var x))
                    e.SetShaderParameter(k.Trim(), x);
    }

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
        : (0.07f, 1.2f);   // (face 39 dye: the red hairs' only, BrowRed)

    /// <summary>Her brows' dye kept in a warm hue band (Oklab degrees; face 33, round 3): the most a
    /// copper's (or any darker hair's) dye may lean to yellow, the most a blonde's, and the least chroma it
    /// keeps. (--browhue red,blonde,chroma tries others.)</summary>
    static readonly (float Red, float Blonde, float Chroma) BrowHue = SurvivorUnchained.Args.Get("browhue") is string bh && bh.Split(',') is [var h0, var h1, var h2]
        ? (float.Parse(h0, System.Globalization.CultureInfo.InvariantCulture), float.Parse(h1, System.Globalization.CultureInfo.InvariantCulture), float.Parse(h2, System.Globalization.CultureInfo.InvariantCulture))
        : (45f, 60f, 0.065f);

    static float SrgbToLin(float c) => c <= 0.04045f ? c / 12.92f : Mathf.Pow((c + 0.055f) / 1.055f, 2.4f);
    static float LinToSrgb(float c) => c <= 0.0031308f ? c * 12.92f : 1.055f * Mathf.Pow(c, 1f / 2.4f) - 0.055f;

    /// <summary>A colour's Oklab lightness, chroma and hue (degrees).</summary>
    static (float L, float C, float H) Oklch(Color c)
    {
        float r = SrgbToLin(c.R), g = SrgbToLin(c.G), b = SrgbToLin(c.B);
        float l = Mathf.Pow(0.4122214708f * r + 0.5363325363f * g + 0.0514459929f * b, 1f / 3f);
        float m = Mathf.Pow(0.2119034982f * r + 0.6806995451f * g + 0.1073969566f * b, 1f / 3f);
        float s = Mathf.Pow(0.0883024619f * r + 0.2817188376f * g + 0.6299787005f * b, 1f / 3f);
        float L = 0.2104542553f * l + 0.7936177850f * m - 0.0040720468f * s;
        float A = 1.9779984951f * l - 2.4285922050f * m + 0.4505937099f * s;
        float B = 0.0259040371f * l + 0.7827675558f * m - 0.8086757660f * s;
        return (L, Mathf.Sqrt(A * A + B * B), Mathf.RadToDeg(Mathf.Atan2(B, A)));
    }

    static Color FromOklch(float L, float C, float H)
    {
        float A = C * Mathf.Cos(Mathf.DegToRad(H)), B = C * Mathf.Sin(Mathf.DegToRad(H));
        float l = L + 0.3963377774f * A + 0.2158037573f * B, m = L - 0.1055613458f * A - 0.0638541728f * B, s = L - 0.0894841775f * A - 1.2914855480f * B;
        l *= l * l; m *= m * m; s *= s * s;
        float r = 4.0767416621f * l - 3.3077115913f * m + 0.2309699292f * s;
        float g = -1.2684380046f * l + 2.6097574011f * m - 0.3413193965f * s;
        float b = -0.0041960863f * l - 0.7034186147f * m + 1.7076147010f * s;
        return new Color(LinToSrgb(Mathf.Clamp(r, 0f, 1f)), LinToSrgb(Mathf.Clamp(g, 0f, 1f)), LinToSrgb(Mathf.Clamp(b, 0f, 1f)));
    }

    /// <summary>Her brows' dye from her hair: darker and a little warmer (face 32), then its hue held in a
    /// warm band and its chroma kept (face 33, round 3: a darkened yellow is olive, and the game's teal night
    /// grade took a copper's brows to olive-brown and a blonde's to khaki; a blonde's brows are golden, a
    /// copper's auburn). A near-black's or a grey's left as it was: they have no hue to keep.</summary>
    // (face 39: 0.42 to 0.38, with HerBrows' colour 0.7 to 1.2: the owner's "dark brown, thick and felt-textured
    // against the copper, read as drawn on"; now a shade or two under her copper, its own warmth kept. --brow-dark tries others)
    static readonly float BrowDark = SurvivorUnchained.Args.Num("brow-dark", 0.38f);

    /// <summary>The least Oklab chroma a brow dye with little colour of its own takes on deep skin (face 39 dye2;
    /// --brow-deep-warm tries others).</summary>
    static Shader? paintMulShader;

    static readonly float BrowDeepWarm = SurvivorUnchained.Args.Num("brow-deep-warm", 0.07f);

    /// <summary>How far a hair's brows take the red settings (face 39's: sat 1.2, BrowDark 0.38, dye_gamma 0.9,
    /// hair_lo 0.2) over the old ones (0.7, 0.42, 0.5, 0.08): all for a red (hue 25 degrees or less, saturation
    /// 0.65 or more: copper, auburn, strawberry, chestnut), none for a blonde (hue 35 or more) or a hair
    /// with little colour (saturation under 0.3: black, grey, platinum), blended between. (Judge j1, face 39:
    /// the red settings turned a blonde's brows ginger and a black's warmer.)</summary>
    // (face 39 dye2: saturation 0.58 to 0.65, not 0.3 to 0.5: brown, #5e3e28 (hue 24, saturation 0.57), took the red
    // settings and its brows read crimson-brown, #601203 against a hair of hue 21; copper 0.70, auburn 0.77,
    // strawberry 0.68, chestnut 0.74 stay whole)
    /// <summary>A red hair's brows on fair skin (HerPaint, face 40 b3): its dye's chroma and lightness times these,
    /// its hue plus the third (degrees, toward auburn).</summary>
    /// <summary>How deep a skin takes her brows as the multiply (heroine_paint_mul.gdshader; --brow-mul-at tries others).</summary>
    static readonly float BrowMulAt = SurvivorUnchained.Args.Num("brow-mul-at", 0.5f);
    static readonly Vector3 BrowCopper = new(0.8f, 1.0f, -10f);
    /// <summary>Her brow cores on deep skin per hair (face 41, judge j2): hue in degrees, saturation, and value as a
    /// share of the skin's own sRGB value round it (heroine_paint.gdshaderinc's target_mode).</summary>
    static readonly (Vector3 Black, Vector3 Brown, Vector3 Copper, Vector3 Blonde) BrowTargets =
        (new(25f, 0.3f, 0.40f), new(35f, 0.5f, 0.44f), new(24f, 0.55f, 0.48f), new(32f, 0.3f, 0.56f));
    public static float BrowRed(Color b) => (1f - Mathf.SmoothStep(25f, 35f, b.H * 360f)) * Mathf.SmoothStep(0.58f, 0.65f, b.S);

    /// <summary>How blonde a hair is (hue 35 degrees or more, its colour kept, light: honey, fair): its brows lighter
    /// and less saturated than the old settings gave (BrowDark 0.42 to 0.3, sat 0.7 to 0.6). The old settings left
    /// fair's brow strokes at 0.57 of the hair's brightness but more saturated than the hair (0.68 to 0.54), an
    /// orange-gold; the judge's target is a dark blonde, no more saturated than the hair (about #8a7550).</summary>
    public static float BrowBlonde(Color b) => Mathf.SmoothStep(25f, 35f, b.H * 360f) * Mathf.SmoothStep(0.3f, 0.45f, b.S) * Mathf.SmoothStep(0.35f, 0.5f, b.Luminance);

    static Color BrowDye(Color b)
    {
        float dark = SurvivorUnchained.Args.Get("brow-dark") != null ? BrowDark : Mathf.Lerp(Mathf.Lerp(0.42f, 0.3f, BrowBlonde(b)), BrowDark, BrowRed(b));
        var dye = b.Darkened(dark + 0.1f * b.Luminance).Lerp(new Color("#7a5434"), 0.2f + 0.4f * b.Luminance);
        var (hL, hC, _) = Oklch(b);
        // (round 4: a fair grey or platinum hair's brows a soft grey-brown, not the warm lerp's tan)
        float wg = Mathf.SmoothStep(0.5f, 0.6f, hL) * (1f - Mathf.SmoothStep(0.02f, 0.05f, hC));
        if (wg > 0f) { var (gL, gC, gH) = Oklch(dye); dye = FromOklch(gL, Mathf.Lerp(gC, Mathf.Min(gC, 0.03f), wg), gH); }
        float w = Mathf.SmoothStep(0.30f, 0.40f, hL) * Mathf.SmoothStep(0.02f, 0.05f, hC);
        if (w <= 0f) return dye;
        var (L, C, H) = Oklch(dye);
        float hi = Mathf.Lerp(BrowHue.Red, BrowHue.Blonde, Mathf.SmoothStep(0.55f, 0.72f, hL));
        float h = Mathf.Lerp(H, Mathf.Clamp(H, 30f, hi), w), c = Mathf.Lerp(C, Mathf.Max(C, BrowHue.Chroma), w);
        return FromOklch(L, c, h);
    }

    /// <summary>Paint on her face (Lore.Her.Paints: art/people/paint/ID.png, laid
    /// out on her head's own paint by tools/assets/heroine_paint.py): drawn
    /// in her skin (heroine_skin.gdshader's face_paint), so it takes her skin's
    /// light exactly, with its own sheen (chalky woad, waxy kohl, bright leaf),
    /// and moves with her face as it shapes and speaks. None: taken off.
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
        // (env PAINT_FILE in a shot: another texture for the paint, its variants tried without a build of each)
        if (def != null && SurvivorUnchained.Args.Has("shot") && System.Environment.GetEnvironmentVariable("PAINT_FILE") is { Length: > 0 } pf) file = pf;
        // (each face's brows where its own paint has them: Own's brows.png (heroine_paint.py), every other face's
        // brows_ID.png (tools/assets/heroine_browdye.py, face 32: before it only Own's were dyed, the others
        // gray-ash under any hair))
        var brows = p.FaceShape is null or "" or "own" ? "res://art/people/paint/brows.png" : $"res://art/people/paint/brows_{p.FaceShape}.png";
        foreach (var mi in p.Meshes)
            for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
            {
                if (mi.Mesh.SurfaceGetMaterial(s)?.ResourceName != "skin_head" || mi.GetSurfaceOverrideMaterial(s) is not ShaderMaterial skin) continue;
                paintShader ??= GD.Load<Shader>("res://shaders/heroine_paint.gdshader");
                // The passes over her skin, in order: her brows, then the paint.
                ShaderMaterial? first = null, last = null;
                void Then(ShaderMaterial m) { if (last == null) first = m; else last.NextPass = m; last = m; }
                // (Own's brows.png on another face dyed that face's lid crease, a copper second brow under its own)
                if (brow is Color b && ResourceLoader.Exists(brows))
                {
                    var tone = skin.GetShaderParameter("tone").AsColor();
                    float deep = 1f - Mathf.SmoothStep(0.4f, 0.6f, 0.2126f * tone.R + 0.7152f * tone.G + 0.0722f * tone.B);
                    // (face 40 r2: on deep skin a multiply over her lit skin (heroine_paint_mul.gdshader): as a lit pass of
                    // their own they took only the night's blue, every stroke's core blue-black. Chosen before any parameter:
                    // a shader set after them dropped them)
                    var m = new ShaderMaterial { Shader = deep >= BrowMulAt ? (paintMulShader ??= GD.Load<Shader>("res://shaders/heroine_paint_mul.gdshader")) : paintShader };
                    m.SetShaderParameter("paint", GD.Load<Texture2D>(brows));
                    m.SetShaderParameter("dyed", true);
                    // (darker than her hair and a little warmer, as brows are: the fairer
                    // her hair the more, so a platinum blonde has ash-brown brows, not grey)
                    // (face 32: warmer the fairer, as a blonde's brows are a golden brown: the dye's own yellow,
                    // darkened, read olive; red hair's read crimson)
                    // (face 39 dye2: on deep skin (her tone multiplier's luminance under 0.6: Deep's 0.34, Fair's 1.0) a brow
                    // dye with little colour of its own a warm dark brown: a black's, near neutral, mixed in ratio with
                    // her red-brown skin, drew blue-grey strokes, #1e171c, hue 320)
                    var dye = BrowDye(b);
                    if (deep > 0f)
                    {
                        var (dL, dC, dH) = Oklch(dye);
                        float plain = deep * (1f - Mathf.SmoothStep(0.03f, 0.06f, Oklch(b).C));
                        dye = FromOklch(dL, Mathf.Lerp(dC, Mathf.Max(dC, BrowDeepWarm), plain), Mathf.Lerp(dH, 45f, plain));
                    }
                    // (face 40 b3, the judge: a copper's brows on fair skin read like marker (#783d1b, saturation 0.77): its
                    // dye's chroma down and darker, its hue toward auburn, as grown brows. Env BROWCOP "chroma,light,hue" in a
                    // shot: tried without a build)
                    float fairRed = (1f - deep) * BrowRed(b);
                    if (fairRed > 0f)
                    {
                        var (cc, cl, ch) = (BrowCopper.X, BrowCopper.Y, BrowCopper.Z);
                        if (Args.Has("shot") && System.Environment.GetEnvironmentVariable("BROWCOP") is { Length: > 0 } bc
                            && bc.Split(',') is [var a0, var a1, var a2])
                        {
                            var ci = System.Globalization.CultureInfo.InvariantCulture;
                            (cc, cl, ch) = (float.Parse(a0, ci), float.Parse(a1, ci), float.Parse(a2, ci));
                        }
                        var (rL, rC, rH) = Oklch(dye);
                        dye = FromOklch(rL * Mathf.Lerp(1f, cl, fairRed), rC * Mathf.Lerp(1f, cc, fairRed), rH + ch * fairRed);
                    }
                    m.SetShaderParameter("dye", dye);
                    // (face 41, judge j2 fix 3: a copper's brows on fair skin a touch thinner, so the close-up by day reads auburn, not a dark band)
                    if (fairRed > 0f) m.SetShaderParameter("strength", Mathf.Lerp(1f, 0.87f, fairRed));
                    // (her face's own paint, not the skin's as it stands: as she is made it is laid after this, Skin)
                    m.SetShaderParameter("skin_paint", (Variant?)HeadPaint(p.FaceShape) ?? skin.GetShaderParameter("paint"));
                    m.SetShaderParameter("skin_tone", skin.GetShaderParameter("tone"));
                    m.SetShaderParameter("soften", HerBrows.Soften);
                    // (face 33: as much of the dye's colour as the hair has little of its own: a red's 0.7 (more read
                    // crimson), a blonde's past its whole colour, since every grade's blue-grey toe took her brows to ash and
                    // olive; a near-black's 0.85, warmed in the shader instead)
                    float red = SurvivorUnchained.Args.Get("brows") != null ? 1f : BrowRed(b);
                    float sat = Mathf.Lerp(Mathf.Lerp(0.7f, 0.6f, BrowBlonde(b)), HerBrows.Sat, red) / 0.7f * Mathf.Lerp(0.85f, Mathf.Clamp(1.95f - 1.6f * b.S, 0.85f, 1.2f), Mathf.SmoothStep(0.12f, 0.3f, b.Luminance));
                    // (face 39 dye2: on deep skin a red's or brown's brows held darker took the held dye's whole colour and
                    // more (dye_sat_held 1.6, dye_sat to 1.7): pure red-black, #440600 copper's; held at 0.7 and 0.8 a dark
                    // auburn-brown, #34150d. A blonde's there kept a grey-mauve haze at dye_fair_sat 0.85: 1.2 and hair_lo 0.2, a warm brown)
                    m.SetShaderParameter("dye_sat", Mathf.Lerp(sat, Mathf.Min(sat, 0.8f), deep));
                    m.SetShaderParameter("dye_sat_held", Mathf.Lerp(1.6f, 0.7f, deep));
                    m.SetShaderParameter("dye_fair_sat", Mathf.Lerp(0.85f, 1.2f, deep));
                    m.SetShaderParameter("rough", 0.8f);
                    // (face 39: each hair's own darkness counted as it is (gamma 0.5 to 0.9), the darkest less past the
                    // core (0.5 to 0.25), and the faint texels between strokes left skin (from 0.08 to 0.2): the half-dark
                    // texels filled the strokes into one felt block)
                    m.SetShaderParameter("dye_gamma", Mathf.Lerp(0.5f, 0.9f, red));
                    m.SetShaderParameter("dye_deep", 0.25f);
                    // (face 39 dye2: on deep skin the faint texels left skin too, a blonde's grey-mauve haze over its strokes)
                    m.SetShaderParameter("hair_lo", Mathf.Lerp(Mathf.Lerp(0.08f, 0.2f, red), 0.2f, deep));
                    m.SetShaderParameter("hair_hi", Mathf.Lerp(0.7f, 0.5f, deep));
                    // (face 40, the judge: on deep skin her brows sat near the skin's value and she read browless at the
                    // Look (brow/skin 0.65-0.86 in screen value): the dye held to a smaller share of her skin's lightness,
                    // black's least, a blonde's most (r2: 0.25 to 0.34 of her lit skin under the multiply, was 0.75 for all, which held every dye alike), each
                    // hair's darkness counted fuller (gamma 0.6, hair_hi 0.5: about a quarter more of each stroke shown):
                    // about half the skin's value. Held that dark, less colour went mauve-blue under the grade (dye_sat 0.7,
                    // held 0.7, floor 0.012: #161215, hue 310) and a yellower held warm grey: dye_sat 0.9, held 1.2, warm 0.07)
                    // (face 40 b3: a blonde's at most 0.29, was 0.34: with each brow's darkening evened (heroine_paint.gdshaderinc's
                    // mul_side) a blonde's lighter brow went past 0.6 of the skin beside it)
                    if (deep > 0f)
                    {
                        float room = Mathf.Lerp(0.25f, 0.29f, Mathf.Clamp((Oklch(b).L - 0.27f) / 0.52f, 0f, 1f));
                        m.SetShaderParameter("dye_room", Mathf.Lerp(0.75f, room, deep));
                        m.SetShaderParameter("dye_gamma", Mathf.Lerp(Mathf.Lerp(0.5f, 0.9f, red), 0.6f, deep));
                        m.SetShaderParameter("dye_sat", Mathf.Lerp(sat, 0.9f, deep));
                        m.SetShaderParameter("dye_sat_held", Mathf.Lerp(1.6f, 1.2f, deep));
                        // (face 40 r2: the hue her brows take her lit skin toward (heroine_paint_mul.gdshader's deep_tint, linear),
                        // found against the Look's night grade, which takes a neutral or cool dark to mauve and her skin's own warm
                        // light a warm one to red: a near-neutral warm for black, a yellow-brown for a brown or blonde, an orange-
                        // brown for a copper)
                        float wc = Mathf.SmoothStep(0.02f, 0.06f, Oklch(b).C), wr = BrowRed(b);
                        var tint = new Vector3(1f, 0.95f, 0.55f).Lerp(new Vector3(1f, 0.85f, 0.4f), wc).Lerp(new Vector3(1f, 0.75f, 0.4f), wr);
                        m.SetShaderParameter("deep_tint", tint);
                    }
                    // (face 41, judge j2: every hair one faint red-brown at ~0.55 of the skin, black's auburn. Each hair's brow
                    // core now a target (hue 0-1, saturation, value over the skin's own): black near-neutral and darkest,
                    // brown dark brown, copper auburn, blonde a lighter taupe; the multiply is it over her painted skin)
                    if (deep >= BrowMulAt)
                    {
                        float wc = Mathf.SmoothStep(0.02f, 0.06f, Oklch(b).C), wr = BrowRed(b);
                        float wb = BrowBlonde(b);
                        var tg = BrowTargets.Black.Lerp(BrowTargets.Brown, wc).Lerp(BrowTargets.Copper, wr).Lerp(BrowTargets.Blonde, wb);
                        m.SetShaderParameter("target_mode", 1f);
                        // (the value as seen: deep skin's toe and grade crush a brow's darkness, so it is held 0.07 lighter there)
                        m.SetShaderParameter("brow_target", new Vector3(tg.X / 360f, tg.Y, tg.Z + 0.07f * deep));
                        m.SetShaderParameter("mul_side_a", 1f);
                        m.SetShaderParameter("mul_side_b", 1f);
                    }
                    // (--brow-set "dye_gamma=0.8,dye_deep=0.3": a developer's switch, the brow dye's uniforms tried without a build)
                    if (SurvivorUnchained.Args.Get("brow-set") is string bs)
                        foreach (var kv in bs.Split(','))
                            if (kv.Split('=') is [var k, var v])
                            {
                                var xs = v.Split('/').Select(t => float.TryParse(t, System.Globalization.NumberStyles.Float,
                                    System.Globalization.CultureInfo.InvariantCulture, out var x) ? x : float.NaN).ToArray();
                                if (xs.Any(float.IsNaN)) continue;
                                if (xs.Length == 3) m.SetShaderParameter(k.Trim(), new Vector3(xs[0], xs[1], xs[2]));
                                else if (xs.Length == 1) m.SetShaderParameter(k.Trim(), xs[0]);
                            }
                    Then(m);
                }
                // The paint drawn in her skin (heroine_skin.gdshader's face_paint), so it takes her skin's
                // light exactly; --paint-pass draws it over her as a pass of its own again (as before
                // 20 October), to compare.
                bool own = def != null && ResourceLoader.Exists(file);
                bool pass = own && SurvivorUnchained.Args.Has("paint-pass");
                skin.SetShaderParameter("has_face_paint", own && !pass);
                skin.SetShaderParameter("face_paint", own && !pass ? GD.Load<Texture2D>(file) : null);
                if (own && !pass)
                {
                    skin.SetShaderParameter("paint_rough", (float)def!.Rough);
                    skin.SetShaderParameter("paint_metal", (float)def.Metal);
                    skin.SetShaderParameter("paint_shine", (float)def.Shine);
                    skin.SetShaderParameter("paint_scatter", (float)def.Scatter);
                    // (env PAINT_SET "scatter=0,shine=0.2,pores=0.6,rough=0.9,metal=0": the skin shader's paint_* tried in a shot)
                    if (SurvivorUnchained.Args.Has("shot") && System.Environment.GetEnvironmentVariable("PAINT_SET") is { Length: > 0 } ps)
                        foreach (var kv in ps.Split(','))
                            if (kv.Split('=') is [var k, var v])
                                skin.SetShaderParameter("paint_" + k, float.Parse(v, System.Globalization.CultureInfo.InvariantCulture));
                    const string keep = "res://art/people/paint/nostril_keep.png";
                    if (ResourceLoader.Exists(keep)) skin.SetShaderParameter("face_paint_keep", GD.Load<Texture2D>(keep));
                }
                if (pass)
                {
                    var m = new ShaderMaterial { Shader = paintShader };
                    m.SetShaderParameter("paint", GD.Load<Texture2D>(file));
                    m.SetShaderParameter("rough", (float)def!.Rough);
                    m.SetShaderParameter("metal", (float)def.Metal);
                    Then(m);
                }
                // (--hair-erase: FSR 2's reactive mask erased under the brows and paint too: HairDraw)
                if (last != null && HairDraw.Eraser() is { } er) Then(er);
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
        if (style != p.HairStyle) HerHair(p, style, colour, look.Highlight);
        foreach (var mi in p.Meshes)
            for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
            {
                if (mi.GetSurfaceOverrideMaterial(s) is ShaderMaterial m)
                {
                    if (m.Shader == hairShader || m.Shader == hairSoftShader || Coverage.On && m.Shader == Coverage.Hair || HairDraw.IsHair(m.Shader))
                        foreach (var pass in HairDraw.Passes(m)) { pass.SetShaderParameter("colour", colour); Highlight(pass, look.Highlight, p.HairStyle); }
                    else if (m.ResourceName == "brows") Coverage.Colour(m, colour.Darkened(0.45f));
                    else if (m.Shader == skinShader2)
                    {
                        m.SetShaderParameter("tone", HerTone(look));
                        m.SetShaderParameter("face_tone", FaceTone(look));
                        m.SetShaderParameter("face_world", FaceWorld(look));
                        m.SetShaderParameter("body_lift", BodyLift(look));
                        m.SetShaderParameter("soft_tone", SoftTone(look));
                        m.SetShaderParameter("key_tone", KeyTone(look));
                        m.SetShaderParameter("sky_tone", SkyTone(look));
                        m.SetShaderParameter("edge_tone", EdgeTone(look));
                        m.SetShaderParameter("neck_pull", NeckPull(look));
                        m.SetShaderParameter("freckle_amount", HerFreckles(look));
                        HerShade(m, look);
                        HerZones(m, look, null);
                        SkinSet(m, m.ResourceName);
                    }
                    else if (m.Shader == eyeShader)
                    {
                        EyeColour(m, look.Eyes, look.EyeRing);
                        HerEyes(m, look.FaceShape, look.Skin);
                    }
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
    /// <summary>Her scalp's shade colour from her hair's (the skin shader multiplies her head's paint by it, times 2.4,
    /// under her hair): her hair darkened. With it her shade's reach (scalp_max, 1: all of it where the mask is full,
    /// not his stubble's 0.85, as what stayed of her head's pale paint greyed it) and its hue ahead of its dark
    /// (scalp_lead, see heroine_skin.gdshader): face 32, 20 October, her hairline's grey band at the Look. (env SCALP
    /// "dark=0.3,sat=1,max=1,lead=1" in a shot: tried without a build.)</summary>
    public static float ScalpMax = 1f, ScalpLead = 1f, ScalpHue = 1f, ScalpFollow = 1f, ScalpDarkMin = 0.8f;
    public static Color ScalpColour(Color hair)
    {
        float dark = 0.3f, sat = 1.0f;
        if (Args.Has("shot") && System.Environment.GetEnvironmentVariable("SCALP") is { Length: > 0 } sc)
            foreach (var kv in sc.Split(','))
            {
                var t = kv.Split('=');
                if (t.Length != 2) continue;
                float v = float.Parse(t[1], System.Globalization.CultureInfo.InvariantCulture);
                if (t[0] == "dark") dark = v; else if (t[0] == "sat") sat = v; else if (t[0] == "max") ScalpMax = v; else if (t[0] == "lead") ScalpLead = v; else if (t[0] == "hue") ScalpHue = v; else if (t[0] == "follow") ScalpFollow = v; else if (t[0] == "darkmin") ScalpDarkMin = v;
            }
        var c = hair.Darkened(dark);
        c = Color.FromHsv(c.H, Mathf.Min(1f, c.S * sat), c.V);
        // (a pale near-neutral dye, platinum: its scalp shade cooled as its cards are, heroine_hair.gdshaderinc's ash,
        // or her hairline went peach-orange under pale hair in the Look's warm light: face 34)
        var l = c.SrgbToLinear();
        float pn = PaleNeutral(hair);
        return pn <= 0 ? c : new Color(l.R * Mathf.Lerp(1f, AshTone.X, pn), l.G * Mathf.Lerp(1f, AshTone.Y, pn), l.B * Mathf.Lerp(1f, AshTone.Z, pn)).LinearToSrgb();
    }

    /// <summary>heroine_hair.gdshaderinc's ash_tone (at its ash 1).</summary>
    static readonly Vector3 AshTone = new(0.72f, 1f, 1f);

    /// <summary>How pale and near-neutral a dye is, 0 to 1, as heroine_hair.gdshaderinc's ash share: 1 for platinum and
    /// gray, 0 for every saturated or dark dye.</summary>
    public static float PaleNeutral(Color hair)
    {
        var l = hair.SrgbToLinear();
        float mx = Mathf.Max(l.R, Mathf.Max(l.G, l.B)), mn = Mathf.Min(l.R, Mathf.Min(l.G, l.B));
        float sat = (mx - mn) / Mathf.Max(mx, 0.001f), lum = 0.2126f * l.R + 0.7152f * l.G + 0.0722f * l.B;
        return (1f - Mathf.SmoothStep(0.2f, 0.5f, sat)) * Mathf.SmoothStep(0.1f, 0.35f, lum);
    }

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
                m.SetShaderParameter("shadow_colour", ScalpColour(hair));
                m.SetShaderParameter("scalp_max", ScalpMax);
                m.SetShaderParameter("scalp_lead", ScalpLead);
                m.SetShaderParameter("scalp_hue", ScalpHue);
                // (face 40 b3: under a dark hair her skin's own colour at the hairline taken to the hair's: black's rust band on deep skin)
                // (and its dark there whole, not held lighter on deep skin (scalp_dark_min 0.4): her skin's own red-brown under it)
                float dk = 1f - Mathf.SmoothStep(0.15f, 0.35f, hair.Luminance);
                m.SetShaderParameter("scalp_follow", ScalpFollow * dk);
                m.SetShaderParameter("scalp_dark_min", Mathf.Lerp(0.4f, ScalpDarkMin, dk));
                set++;
            }
        if (Args.Has("shot")) GD.Print($"HerScalp: {set} surfaces");
        if (Args.Has("shot") && System.Environment.GetEnvironmentVariable("H1DBG") is { Length: > 0 } dbg) H1Debug(p, dbg);
        // (env HAIRSET "through=0,shine2=0.2": her hair's uniforms tried in a shot without a build, every pass; face 30 cine)
        if (Args.Has("shot") && System.Environment.GetEnvironmentVariable("HAIRSET") is { Length: > 0 } hs)
            foreach (var mi in p.Hair)
                for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
                    if (mi.GetSurfaceOverrideMaterial(s) is ShaderMaterial hm)
                        foreach (var pass in HairDraw.Passes(hm))
                            foreach (var kv in hs.Split(','))
                                if (kv.Split('=') is [var k, var v] && float.TryParse(v, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var x))
                                    pass.SetShaderParameter(k.Trim(), x);
    }

    /// <summary>Shot-only switches to find what draws a patch on her head (face 30 H1b; env H1DBG, a comma list, off
    /// unless set): nohair, nocap (the cap's cover 0), capgreen and cardsblue (their dye), uv (her head's UV emitted:
    /// with --tonemap linear --grade off), nospec (her head's sheen and rim off), hairnospec and hairnovar (her hair's shine, its strand tone variation off), nosss, mask (her scalp's tint green).</summary>
    static void H1Debug(Person p, string dbg)
    {
        var on = new HashSet<string>(dbg.Split(','));
        foreach (var mi in p.Hair)
        {
            if (on.Contains("nohair")) mi.Visible = false;
            for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
            {
                var name = mi.Mesh.SurfaceGetMaterial(s)?.ResourceName;
                if (mi.GetSurfaceOverrideMaterial(s) is not ShaderMaterial hm) continue;
                if (name == "hair_cap" && on.Contains("nocap")) mi.SetSurfaceOverrideMaterial(s, new StandardMaterial3D { Transparency = BaseMaterial3D.TransparencyEnum.Alpha, AlbedoColor = new Color(0, 0, 0, 0) });
                else if (name == "hair_cap" && on.Contains("capgreen")) foreach (var pass in HairDraw.Passes(hm)) pass.SetShaderParameter("colour", new Color(0, 1, 0));
                else if (name != "hair_cap" && on.Contains("cardsblue")) foreach (var pass in HairDraw.Passes(hm)) pass.SetShaderParameter("colour", new Color(0, 0, 1));
                if (on.Contains("hairnospec")) foreach (var pass in HairDraw.Passes(hm)) { pass.SetShaderParameter("shine", 0f); pass.SetShaderParameter("shine2", 0f); }
                if (on.Contains("hairnovar")) foreach (var pass in HairDraw.Passes(hm)) pass.SetShaderParameter("variation", 0f);
            }
        }
        foreach (var mi in p.Meshes)
            for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
            {
                if (mi.Mesh.SurfaceGetMaterial(s)?.ResourceName != "skin_head" || mi.GetSurfaceOverrideMaterial(s) is not ShaderMaterial m) continue;
                if (on.Contains("uv")) m.SetShaderParameter("dbg_gate", 9.0f);
                if (on.Contains("uv10")) m.SetShaderParameter("dbg_gate", 10.0f);
                if (on.Contains("uv11")) m.SetShaderParameter("dbg_gate", 11.0f);
                if (on.Contains("nospec")) { m.SetShaderParameter("shine", 0f); m.SetShaderParameter("seam_shine", 0f); m.SetShaderParameter("rim", 0f); }
                if (on.Contains("nosss")) { m.SetShaderParameter("scatter", 0f); m.SetShaderParameter("backlight", 0f); }
                if (on.Contains("mask")) m.SetShaderParameter("shadow_colour", new Color(0, 1f / 2.4f, 0));
            }
        // (face 30 neck: noao (her skin's baked shade white), flathead / flatbody (the head's or the other skin parts'
        // paint one flat skin tone), allsss (nosss on every skin part), on every part on her skin's shader)
        var flat = new ImageTexture();
        { var im = Image.CreateEmpty(1, 1, false, Image.Format.Rgb8); im.Fill(new Color(0.80f, 0.62f, 0.52f)); flat = ImageTexture.CreateFromImage(im); }
        var white = new ImageTexture();
        { var im = Image.CreateEmpty(1, 1, false, Image.Format.Rgba8); im.Fill(new Color(1, 1, 1, 1)); white = ImageTexture.CreateFromImage(im); }
        foreach (var mi in p.Meshes)
            for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
            {
                if (mi.GetSurfaceOverrideMaterial(s) is not ShaderMaterial m || m.Shader?.ResourcePath?.Contains("heroine_skin") != true) continue;
                bool head = mi.Mesh.SurfaceGetMaterial(s)?.ResourceName == "skin_head";
                if (on.Contains("noao")) m.SetShaderParameter("ao_map", white);
                if (on.Contains(head ? "flathead" : "flatbody")) m.SetShaderParameter("paint", flat);
                if (on.Contains("allsss")) { m.SetShaderParameter("scatter", 0f); m.SetShaderParameter("backlight", 0f); }
                GD.Print($"H1Debug part {mi.Mesh.SurfaceGetMaterial(s)?.ResourceName}");
            }
        // (shot-only, tone solver 18 Oct: headnocast / bodynocast / othernocast: her head's mesh, her body's, or every
        // other mesh of hers (outfit, hair) casts no shadow, to find what shades her neck from the moon)
        foreach (var mi in p.Meshes.Concat(p.Hair))
        {
            bool isHead = false, isBody = false;
            for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
            {
                var rn = mi.Mesh.SurfaceGetMaterial(s)?.ResourceName;
                if (rn == "skin_head") isHead = true;
                if (rn == "Material_0.001" || rn == "skin_graft") isBody = true;
            }
            if (isHead ? on.Contains("headnocast") : isBody ? on.Contains("bodynocast") : on.Contains("othernocast") || on.Contains("nocast:" + mi.Name))
            {
                mi.CastShadow = GeometryInstance3D.ShadowCastingSetting.Off;
                GD.Print($"H1Debug nocast {mi.Name}");
            }
        }
        GD.Print($"H1Debug: {dbg}");
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
        var fs = SurvivorUnchained.World.Lore.Her.Faces.FirstOrDefault(f => f.Id == (face is { Length: > 0 } ? face : "own"));
        // (and her lids at that face's rest, as its portrait has them)
        if (p.Skeleton.GetNodeOrNull<HerFaceLife>("HerFaceLife") is HerFaceLife life)
            life.Rest = (float)(fs?.Lid ?? 0);
        // (and its lower lip's own fullness under the player's slider)
        p.LipsBase = (float)(fs?.Lips ?? 0);
        foreach (var mi in p.Meshes)
            if (mi.Mesh is ArrayMesh { } lm && lm.GetBlendShapeCount() > 0)
            {
                var v = Mathf.Clamp(p.LipsSlider + p.LipsBase, -1, 1.5f);
                if (mi.FindBlendShapeByName("lips_lower+") is int a and >= 0) mi.SetBlendShapeValue(a, Mathf.Max(v, 0));
                if (mi.FindBlendShapeByName("lips_lower-") is int b and >= 0) mi.SetBlendShapeValue(b, Mathf.Max(-v, 0));
            }
    }

    /// <summary>Her head's painting for a face she started from (Lore.Her's
    /// faces: tools/assets/heroine_head.py's head_tex/heroine_head_ID.jpg,
    /// each painted on her head shaped as that face, its brows, lips and
    /// skin its own), or her own.</summary>
    public static void HerHeadPaint(Person p, string? face)
    {
        p.FaceShape = face;
        var paint = HeadPaint(face);
        foreach (var mi in p.Meshes)
            for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
                if (mi.Mesh.SurfaceGetMaterial(s)?.ResourceName == "skin_head" && mi.GetSurfaceOverrideMaterial(s) is ShaderMaterial skin)
                    skin.SetShaderParameter("paint", paint ?? (mi.Mesh.SurfaceGetMaterial(s) as BaseMaterial3D)?.AlbedoTexture);
    }

    /// <summary>Her head's paint for a face (head_tex/heroine_head_ID.jpg); her own head_tex/heroine_head.jpg, so a
    /// paint laid again since (the jaw cut, 10 October 2026) shows without a new glb: heroine.glb's own copy is older.</summary>
    static string? HeadPaintFile(string? face)
    {
        var f = face is { Length: > 0 } and not "own" ? $"res://art/people/head_tex/heroine_head_{face}.jpg" : "res://art/people/head_tex/heroine_head.jpg";
        return ResourceLoader.Exists(f) ? f : null;
    }

    /// <summary>Her head's paint as a texture (HeadPaintFile). --head-paint PATH: a paint from any file instead, for
    /// whichever face she wears, for pictures of a paint tried before it is laid in.</summary>
    static Texture2D? HeadPaint(string? face) =>
        TryFile("head-paint") ?? (HeadPaintFile(face) is string f ? GD.Load<Texture2D>(f) : null);

    /// <summary>A texture of hers, or the file a developer's switch (--SWITCH PATH) names instead.</summary>
    static Texture2D TextureOrTry(string res, string tryKey) => TryFile(tryKey) ?? GD.Load<Texture2D>(res);

    /// <summary>The picture at the path a developer's switch names (--SWITCH PATH), mipmapped, or null.</summary>
    static Texture2D? TryFile(string key)
    {
        if (SurvivorUnchained.Args.Get(key) is not string path || !System.IO.File.Exists(path)) return null;
        var img = Image.LoadFromFile(path);
        img.GenerateMipmaps();
        return ImageTexture.CreateFromImage(img);
    }

    /// <summary>Whether a hair surface has a braid's ropes (vertex blue 0.5 or more on the cap: tools/assets/heroine_hair.py, mat 1).</summary>
    static bool HasRopes(Mesh mesh, int surface)
    {
        if (mesh.SurfaceGetArrays(surface)[(int)Mesh.ArrayType.Color].AsColorArray() is not { Length: > 0 } c) return false;
        foreach (var k in c) if (k.B >= 0.5f) return true;
        return false;
    }

    static Shader? hairShader, hairSoftShader, eyeShader, teethShader, tongueShader;
    // (--hair-atlas PATH: her hair's strands atlas from a file, tried before a build)
    static Texture2D? hairAtlas;

    /// <summary>Hair: her hair cards (tools/assets/heroine_hair.py) by
    /// shaders/heroine_hair.gdshader, dyed: the strands' atlas cut to its
    /// strands, darker at the roots and deep in, with the long highlight
    /// across them.</summary>
    internal static Material Hair(BaseMaterial3D src, Color colour, Color? highlight = null, string? style = null, bool ropes = false)
    {
        hairShader ??= GD.Load<Shader>("res://shaders/heroine_hair.gdshader");
        hairSoftShader ??= GD.Load<Shader>("res://shaders/heroine_hair_soft.gdshader");
        // (the cap on her scalp and the fine hairs at her hairline blended, as
        // they thin out into her skin; the fine hairs over the cap)
        bool soft = src.ResourceName is "hair_cap" or "hair_fine";
        // (--hair-draw: the cards blended, to choose the smoothing: HairDraw)
        var m = (src.ResourceName == "hair" ? HairDraw.Hair() : null)
            ?? new ShaderMaterial { Shader = soft ? hairSoftShader : Coverage.On ? Coverage.Hair : hairShader, RenderPriority = src.ResourceName == "hair_fine" ? (HairDraw.Blended ? 2 : 1) : 0 };
        // (--hair-erase: FSR 2's reactive mask erased under the blended ones: HairDraw)
        if (soft || src.ResourceName == "hair" && HairDraw.Blended) m = HairDraw.WithErase(m);
        // (a braid's ropes on the cap drawn solid under it, their depth written: HairDraw.RopeCore; --rope-core off: as before)
        if (ropes && src.ResourceName == "hair_cap" && Args.Get("rope-core") != "off") m = HairDraw.RopeCore(m);
        foreach (var pass in HairDraw.Passes(m))
        {
            pass.SetShaderParameter("strands", src.AlbedoTexture?.ResourcePath.EndsWith("hair_strands.png") == true ? (hairAtlas ??= TryFile("hair-atlas")) ?? src.AlbedoTexture : src.AlbedoTexture);
            pass.SetShaderParameter("colour", colour);
            pass.SetShaderParameter("cap", src.ResourceName == "hair_cap");
            pass.SetShaderParameter("tie", src.ResourceName == "hair_tie");
            Highlight(pass, highlight, style);
            HairSet(pass, src.ResourceName);
        }
        return m;
    }

    /// <summary>Her hair's highlights (heroine_hair.gdshaderinc's highlight): a second colour on some of her
    /// locks, in the hair's own colour, or none.</summary>
    static void Highlight(ShaderMaterial pass, Color? highlight, string? style = null)
    {
        pass.SetShaderParameter("highlights", highlight is null ? 0f : 1f);
        if (highlight is not Color h) return;
        pass.SetShaderParameter("highlight", h);
        // (face 40, the judge: pixie's and ponytail's locks are shorter and lie closer, so half the braid's share, or
        // they read as tiger stripes; a swatch's own share and strength from looks.json: platinum twice the locks,
        // honey half as strong again)
        var sw = SurvivorUnchained.World.Lore.HairHighlights.FirstOrDefault(x => x.Color.Length > 0 && new Color(x.Color).IsEqualApprox(h));
        pass.SetShaderParameter("hl_locks", Mathf.Min(HighlightLocks * (style is "pixie" or "ponytail" ? 0.5f : 1f) * (sw?.Share ?? 1f), 0.95f));
        pass.SetShaderParameter("hl_strength", sw?.Strength ?? 1f);
    }

    /// <summary>The share of the locks in her highlights' panels that take them, on the braid (heroine_hair.gdshaderinc's hl_locks).</summary>
    const float HighlightLocks = 0.45f;

    /// <summary>--hair-set "hair:shine=0.3;*:wrap=0.2": a developer's switch, her hair's uniforms tried without a build,
    /// by part (hair, hair_cap, hair_fine, hair_tie; "*" for every part); a/b/c is a vec3.</summary>
    static void HairSet(Material pass, string part)
    {
        if (SurvivorUnchained.Args.Get("hair-set") is not string hs || pass is not ShaderMaterial sm) return;
        foreach (var one in hs.Split(';'))
            if (one.Split(':') is [var who, var kvs] && (who == "*" || who == part))
                foreach (var kv in kvs.Split(','))
                    if (kv.Split('=') is [var k, var v])
                    {
                        var xs = v.Split('/').Select(t => float.TryParse(t, System.Globalization.NumberStyles.Float,
                            System.Globalization.CultureInfo.InvariantCulture, out var x) ? x : float.NaN).ToArray();
                        if (xs.Any(float.IsNaN)) continue;
                        if (xs.Length == 4) sm.SetShaderParameter(k.Trim(), new Vector4(xs[0], xs[1], xs[2], xs[3]));
                        else if (xs.Length == 3) sm.SetShaderParameter(k.Trim(), new Vector3(xs[0], xs[1], xs[2]));
                        else if (xs.Length == 1) sm.SetShaderParameter(k.Trim(), xs[0]);
                    }
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
        var laid = new List<MeshInstance3D>();
        foreach (var mi in from.GetChildren().OfType<MeshInstance3D>().ToList())
        {
            if (!mi.Name.ToString().StartsWith(set + "_")) continue;
            laid.Add(mi);
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
        WornShape(p, "reaver", set == "reaver");
        int ch = System.Array.IndexOf(OutfitChannels, set);
        foreach (var mi in p.Skeleton.GetChildren().OfType<MeshInstance3D>())
            if (!mi.Name.ToString().Contains('.') && !mi.Name.ToString().Contains('_')) TuckSkin(mi, ch);
        // Her gameplay model beside it, drawn only at the play camera (HerLod), and what draws of it there one
        // mesh a material (HerLod.Merge).
        HerLod.Attach(p, set);
        HerLod.For(p)?.Merge(laid);
    }

    static Shader? furShader, sheerShader, outfitShader, metalShader, satinShader;
    static Godot.Collections.Dictionary? outfitTable, metalFinishes;
    static Texture2D? metalDetail;

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
            int kind = (string)entry["kind"] switch { "leather" => 0, "metal" => 1, "cloth" => 2, "gloss" => 3, "twill" => 4, "satin" => 5, _ => -1 };
            if (kind < 0) continue;
            // (metal: the same shader with metal's own light and reflection, one shared scratch-and-pit
            // detail and its key's finish; the look bible's armor-metal page)
            if (kind == 1) metalShader ??= GD.Load<Shader>("res://shaders/heroine_outfit_metal.gdshader");
            // (a satin with a sheen, the arcanist's opera gloves: satin's own light, its sheen along the arm, armor 16)
            bool sheen = kind == 5 && entry.ContainsKey("sheen");
            if (sheen) satinShader ??= GD.Load<Shader>("res://shaders/heroine_outfit_satin.gdshader");
            var m = new ShaderMaterial { Shader = kind == 1 ? metalShader : sheen ? satinShader : outfitShader };
            m.SetShaderParameter("kind", kind);
            // (its dye zone, from the table: HerWear.DyeMesh sets the dye on the surfaces of the zone a piece is dyed in)
            m.SetMeta("zone", entry.TryGetValue("zone", out var zn) ? (string)zn : "none");
            m.SetMeta("kind", kind);
            if (kind == 1)
            {
                metalDetail ??= GD.Load<Texture2D>("res://art/outfit/metal_wear_detail.png");
                m.SetShaderParameter("metal_detail", metalDetail);
                m.SetShaderParameter("has_detail", metalDetail != null);
                metalFinishes ??= Json.ParseString(FileAccess.GetFileAsString("res://art/people/metal_finishes.json")).AsGodotDictionary();
                // (blued steel 1; enamel 2, blue enamel chipped to bright steel: body 16, the Warden's navy as paint)
                if (metalFinishes.TryGetValue(key, out var fin) && (string)fin is "blued" or "enamel") m.SetShaderParameter("finish", (string)fin == "enamel" ? 2 : 1);
                // (dye_paint keys: bare as built, but a dye paints them like enamel: HerWear.DyeMesh)
                if (metalFinishes.TryGetValue("dye_paint", out var dp) && dp.AsGodotArray().Contains(key)) { m.SetMeta("finish0", 0); m.SetMeta("dye_paint", true); }
                // (pieces of this key with a finish of their own, matched in the shader by the piece
                // number heroine_outfits.py bakes into each piece: the key's pieces are one mesh)
                if (metalFinishes.TryGetValue("pieces", out var pcs) && pcs.AsGodotDictionary().TryGetValue(key, out var byKey))
                {
                    string set = mi.Name.ToString().Split('_')[0];
                    var ids = new Vector4(-1, -1, -1, -1); var pr = ids; var pg = ids; var pb = ids; var prr = ids; var prb = ids; var pf = ids; var ps = ids; var pfm = ids; var pmu = ids;
                    int n = 0;
                    foreach (var (pn, pv) in byKey.AsGodotDictionary())
                    {
                        var name = (string)pn;
                        if (n >= 4 || !name.StartsWith(set + ".")) continue;
                        var o = pv.AsGodotDictionary();
                        ids[n] = PieceNumber(name[(set.Length + 1)..]);
                        if (o.TryGetValue("metal_rough", out var r)) pr[n] = (float)r;
                        if (o.TryGetValue("metal_env_graze", out var g)) pg[n] = (float)g;
                        if (o.TryGetValue("metal_blot", out var bl)) pb[n] = (float)bl;
                        if (o.TryGetValue("metal_rim_rough", out var rr)) prr[n] = (float)rr;
                        if (o.TryGetValue("metal_rim_bright", out var rb)) prb[n] = (float)rb;
                        if (o.TryGetValue("metal_fine", out var fi)) pf[n] = (float)fi;
                        if (o.TryGetValue("metal_rim_steel", out var rs)) ps[n] = (float)rs;
                        if (o.TryGetValue("metal_form", out var fm)) pfm[n] = (float)fm;
                        if (o.TryGetValue("metal_spec_mute", out var mu)) pmu[n] = (float)mu;
                        n++;
                    }
                    m.SetShaderParameter("piece_id", ids);
                    m.SetShaderParameter("piece_rough", pr);
                    m.SetShaderParameter("piece_graze", pg);
                    m.SetShaderParameter("piece_blot", pb);
                    m.SetShaderParameter("piece_rim_rough", prr);
                    m.SetShaderParameter("piece_rim_bright", prb);
                    m.SetShaderParameter("piece_fine", pf);
                    m.SetShaderParameter("piece_rim_steel", ps);
                    m.SetShaderParameter("piece_form", pfm);
                    m.SetShaderParameter("piece_spec_mute", pmu);
                }
            }
            m.SetShaderParameter("albedo", src.AlbedoTexture);
            m.SetShaderParameter("normal_map", src.NormalTexture);
            m.SetShaderParameter("orm", src.RoughnessTexture);
            m.SetShaderParameter("has_orm", src.RoughnessTexture != null);
            m.SetShaderParameter("roughness_value", src.Roughness);
            m.SetShaderParameter("metallic_value", src.Metallic);
            m.SetShaderParameter("repeats", (float)entry["repeats"]);
            // (a metal key's own satin roughness, where its row names one: blacksteel, the etched tier's blackened ground at 0.3)
            if (kind == 1 && entry.ContainsKey("roughness")) m.SetShaderParameter("metal_rough", (float)entry["roughness"]);
            // (a leather's roughness floor, where its row names one: the arcanist bodysuit's plumleather, armor 14)
            if (kind == 0 && entry.ContainsKey("rough_floor")) m.SetShaderParameter("leather_rough_floor", (float)entry["rough_floor"]);
            if (kind == 0 && entry.ContainsKey("rough_var")) m.SetShaderParameter("leather_rough_var", (float)entry["rough_var"]);
            if (kind == 0 && entry.ContainsKey("clearcoat")) m.SetShaderParameter("leather_clearcoat", (float)entry["clearcoat"]);
            if (kind == 0 && entry.ContainsKey("clearcoat_rough")) m.SetShaderParameter("leather_clearcoat_rough", (float)entry["clearcoat_rough"]);
            // (her plate's reflection at the Look, under its rig only (look_rig), armor 16: the key's softbox and a dim dome;
            // LOOK_METAL_ENV=env,key,dome tries others)
            if (kind == 1)
            {
                // (N4: env,key,dome,mute,gold: a soft box, the rig's lamps muted on the plate, the gold's share)
                // (N5, OJ2: the key 3.5 to 5.0 and the dome 0.45 to 0.6, the muted plate read dark slate; the gold 1.6 to 1.3, now glossier)
                var le = (System.Environment.GetEnvironmentVariable("LOOK_METAL_ENV") ?? "1.6,5.0,0.6,0.75,1.3").Split(',');
                float L(int i) => float.Parse(le[i], System.Globalization.CultureInfo.InvariantCulture);
                m.SetShaderParameter("look_metal_env", L(0)); m.SetShaderParameter("look_metal_key", L(1)); m.SetShaderParameter("look_metal_dome", L(2));
                if (le.Length > 3) m.SetShaderParameter("look_metal_mute", L(3));
                if (le.Length > 4) m.SetShaderParameter("look_gold_key", L(4));
            }
            // (a satin's sheen, where its row names one: the arcanist's opera gloves, armor 16)
            if (kind == 5 && entry.ContainsKey("sheen")) m.SetShaderParameter("satin_sheen", (float)entry["sheen"]);
            if (kind == 5 && entry.ContainsKey("axis")) m.SetShaderParameter("satin_axis", (int)entry["axis"]);
            if (kind == 5 && entry.ContainsKey("along")) m.SetShaderParameter("satin_along", (float)entry["along"]);
            if (kind == 5 && entry.ContainsKey("across")) m.SetShaderParameter("satin_across", (float)entry["across"]);
            if (kind == 5 && entry.ContainsKey("body")) m.SetShaderParameter("satin_body", (float)entry["body"]);
            if (kind == 5 && entry.ContainsKey("turn")) m.SetShaderParameter("satin_turn", (float)entry["turn"]);
            if (kind == 5 && entry.ContainsKey("cap")) m.SetShaderParameter("satin_spec_cap", (float)entry["cap"]);
            // (its wrinkles: soft ruching at the wrist, creases inside the elbow, long diagonal folds; their way round
            // the arm written into its UV2, which a satin never reads otherwise, armor 16 N4)
            if (kind == 5 && entry.ContainsKey("wrinkle") && mi.Mesh is ArrayMesh am
                && SatinAround(am, s, (float)entry["wrinkle_top"], (float)entry["wrinkle_wrist"]))
            {
                m.SetShaderParameter("satin_wrinkle", (float)entry["wrinkle"]);
                m.SetShaderParameter("satin_top_v", (float)entry["wrinkle_top"]);
                m.SetShaderParameter("satin_wrist_v", (float)entry["wrinkle_wrist"]);
                m.SetShaderParameter("satin_uv_per_m", (float)entry["repeats"]);
            }
            if (entry.ContainsKey("pull")) m.SetShaderParameter("view_pull", (float)entry["pull"]);
            if (System.Environment.GetEnvironmentVariable("GOLD_GLOSS") is string gg && float.TryParse(gg, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var ggv)) m.SetShaderParameter("gold_gloss", ggv);   // (a trial knob)
            if (System.Environment.GetEnvironmentVariable("GOLD_FLOOR") is string gf && float.TryParse(gf, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var gfv)) m.SetShaderParameter("gold_floor", gfv);
            if (System.Environment.GetEnvironmentVariable("GOLD_ROUGH") is string gr && float.TryParse(gr, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var grv)) m.SetShaderParameter("gold_rough", grv);
            // (METAL_TRY=name=value;...: a metal key's float uniforms for one run, a trial knob, body 16)
            if (kind == 1 && System.Environment.GetEnvironmentVariable("METAL_TRY") is string mt)
                foreach (var kv in mt.Split(';', StringSplitOptions.RemoveEmptyEntries).Select(x => x.Split('=', 2)).Where(x => x.Length == 2))
                    if (kv[1].Split(',') is { Length: 3 } c3) m.SetShaderParameter(kv[0].Trim(), new Color(float.Parse(c3[0], System.Globalization.CultureInfo.InvariantCulture), float.Parse(c3[1], System.Globalization.CultureInfo.InvariantCulture), float.Parse(c3[2], System.Globalization.CultureInfo.InvariantCulture)));
                    else if (float.TryParse(kv[1], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var mtv)) m.SetShaderParameter(kv[0].Trim(), mtv);
            if (System.Environment.GetEnvironmentVariable("OUTFIT_DEBUG_VIEW") is string dv && int.TryParse(dv, out var dvv)) m.SetShaderParameter("debug_view", dvv);   // (a check: 4 = the gold mask flat magenta)
            mi.SetSurfaceOverrideMaterial(s, m);
        }
    }

    /// <summary>A glove's way round its arm (armor 16 N4, the satin's wrinkles): each vertex's angle about its forearm's
    /// axis (0 toward her front, the inside of the elbow), written into the surface's UV2 as (cos, sin) so it blends
    /// smoothly all the way round. Each arm (the sign of x) on its own: its axis the forearm's long way (between the
    /// wrist's and the top's UV v), mirrored, so the right glove's folds mirror the left's. False if it can't take it.</summary>
    static bool SatinAround(ArrayMesh mesh, int s, float topV, float wristV)
    {
        var arr = mesh.SurfaceGetArrays(s);
        if (arr[(int)Mesh.ArrayType.TexUV2].VariantType == Variant.Type.Nil) return false;
        var P = arr[(int)Mesh.ArrayType.Vertex].AsVector3Array();
        var U = arr[(int)Mesh.ArrayType.TexUV].AsVector2Array();
        var format = mesh.SurfaceGetFormat(s);
        if ((format & Mesh.ArrayFormat.FlagCompressAttributes) != 0) { GD.PushWarning("SatinAround: compressed attributes"); return false; }
        var U2 = new Vector2[P.Length];
        foreach (int side in new[] { 1, -1 })
        {
            bool Fore(int i) => Mathf.Sign(P[i].X) == side && U[i].Y < topV - 0.5f && U[i].Y > wristV + 0.5f;
            var c = Vector3.Zero; int n = 0;
            for (int i = 0; i < P.Length; i++) if (Fore(i)) { c += P[i]; n++; }
            if (n < 20) continue;
            c /= n;
            // (its long way: the covariance's first axis, by power iteration)
            var cx = Vector3.Zero; var cy = Vector3.Zero; var cz = Vector3.Zero;
            for (int i = 0; i < P.Length; i++)
                if (Fore(i)) { var d = P[i] - c; cx += d * d.X; cy += d * d.Y; cz += d * d.Z; }
            var ax = new Vector3(side, -1, 0).Normalized();
            for (int it = 0; it < 32; it++) ax = (cx * ax.X + cy * ax.Y + cz * ax.Z).Normalized();
            if (ax.X * side < 0) ax = -ax;                     // (toward the hand)
            var f = (Vector3.Back - ax * ax.Z).Normalized();   // (her front, +z, square to it)
            var b = ax.Cross(f);
            for (int i = 0; i < P.Length; i++)
            {
                if (Mathf.Sign(P[i].X) != side) continue;
                var d = P[i] - c; d -= ax * d.Dot(ax);
                float a = Mathf.Atan2(d.Dot(b), d.Dot(f));
                U2[i] = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
            }
        }
        int vc = P.Length;
        uint stride = RenderingServer.MeshSurfaceGetFormatAttributeStride((RenderingServer.ArrayFormat)format, vc);
        uint off = RenderingServer.MeshSurfaceGetFormatOffset((RenderingServer.ArrayFormat)format, vc, (int)Mesh.ArrayType.TexUV2);
        var attr = RenderingServer.MeshGetSurface(mesh.GetRid(), s)["attribute_data"].AsByteArray();
        if (attr.Length < stride * vc) return false;
        for (int i = 0; i < vc; i++)
        {
            System.BitConverter.TryWriteBytes(new System.Span<byte>(attr, (int)(i * stride + off), 4), U2[i].X);
            System.BitConverter.TryWriteBytes(new System.Span<byte>(attr, (int)(i * stride + off + 4), 4), U2[i].Y);
        }
        mesh.SurfaceUpdateAttributeRegion(s, 0, attr);
        return true;
    }

    /// <summary>A piece's own number, as heroine_outfits.py bakes it into its vertex
    /// colours' green: the CRC-32 of its name's first word (greave_l: greave) mod 1000, over 1000.</summary>
    static float PieceNumber(string word)
    {
        uint c = 0xFFFFFFFF;
        foreach (byte b in System.Text.Encoding.UTF8.GetBytes(word.Split('_')[0]))
        {
            c ^= b;
            for (int k = 0; k < 8; k++) c = (c >> 1) ^ (0xEDB88320u & (uint)-(int)(c & 1));
        }
        return ((~c) % 1000) / 1000f;
    }

    /// <summary>The reaver's pelt (armor 16, judge J5: "plush felt, not a pelt"): its shells and knobs.</summary>
    public static int PeltShells = 30;
    public static readonly Dictionary<string, float> Pelt = new()
    {
        ["fur_length"] = 0.03f, ["density"] = 260f, ["droop"] = 0.25f, ["comb"] = 0.9f,
        ["root_dark"] = 0.3f, ["tip_light"] = 1.35f, ["backlight"] = 0.3f,
        ["tuft"] = 0.075f, ["guard"] = 0.22f, ["under_len"] = 0.5f, ["frost"] = 0.12f,
        // (N4, OJ1: the pile 22 mm as before, the fringe up to 30 mm in uneven locks and lighter, the spine darker)
        ["body_len"] = 0.73f, ["fringe_w"] = 0.024f, ["fringe_light"] = 1.4f, ["spine_dark"] = 0.72f,
        ["hem_vary"] = 0.55f, ["hem_scale"] = 9f,
    };

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
                var sm = new ShaderMaterial { Shader = sheerShader };
                // (its colour, when the build names one: the Arcanist's stockings in her glove's ivory, s29)
                outfitTable ??= Json.ParseString(FileAccess.GetFileAsString("res://art/people/outfit_materials.json")).AsGodotDictionary();
                if (outfitTable.TryGetValue("stocking", out var st) && st.AsGodotDictionary().TryGetValue("tint", out var tv) && tv.AsGodotArray() is { Count: 3 } t)
                    sm.SetShaderParameter("tint", new Color((float)t[0], (float)t[1], (float)t[2]));
                sm.SetMeta("zone", ZoneOf("stocking"));
                mi.SetSurfaceOverrideMaterial(s, sm);
                continue;
            }
            if (mi.Mesh.SurfaceGetMaterial(s) is not BaseMaterial3D src || (src.ResourceName != "fur" && src.ResourceName != "down")) continue;
            // (down: the arcanist's white feathery trim, fine wisps longer than
            // fur's pile, pale to the root and lit through)
            bool down = src.ResourceName == "down";
            furShader ??= GD.Load<Shader>("res://shaders/fur_shell.gdshader");
            ShaderMaterial? first = null, last = null;
            // (fur proper is a pelt, armor 16: longer, in tufts, combed; a few more shells for its length)
            int n = down ? shells : PeltShells;
            for (int i = 0; i <= n; i++)
            {
                var m = new ShaderMaterial { Shader = furShader };
                m.SetShaderParameter("albedo_tex", src.AlbedoTexture);
                m.SetShaderParameter("tint", src.AlbedoColor);
                m.SetShaderParameter("layer", (float)i / n);
                if (!down)
                {
                    m.SetShaderParameter("pelt", 1.0f);
                    foreach (var (k, v) in Pelt) m.SetShaderParameter(k, v);
                }
                if (down)
                {
                    m.SetShaderParameter("fur_length", 0.009f);
                    m.SetShaderParameter("density", 520.0f);
                    m.SetShaderParameter("clump", 0.15f);
                    m.SetShaderParameter("root_dark", 0.78f);
                    m.SetShaderParameter("backlight", 0.6f);
                    m.SetShaderParameter("droop", 0.12f);
                }
                if (last != null) last.NextPass = m; else first = m;
                last = m;
            }
            first?.SetMeta("zone", ZoneOf(src.ResourceName));
            mi.SetSurfaceOverrideMaterial(s, first);
        }
    }

    /// <summary>A material's dye zone, from art/people/outfit_materials.json ("none" where it names none).</summary>
    static string ZoneOf(string key)
    {
        outfitTable ??= Json.ParseString(FileAccess.GetFileAsString("res://art/people/outfit_materials.json")).AsGodotDictionary();
        return outfitTable.TryGetValue(key, out var e) && e.AsGodotDictionary().TryGetValue("zone", out var z) ? (string)z : "none";
    }

    /// <summary>Her outfits, in the order of their channels in her vertex
    /// colours (tools/assets/heroine_outfits.py's OUTFITS).</summary>
    static readonly string[] OutfitChannels = { "warden", "arcanist", "reaver", "ranger" };

    /// <summary>Her skin under the outfit tucked a few millimetres in by her
    /// skin's shader (shaders/heroine_skin.gdshader), not cut away: cut, a
    /// gap opened in her wherever a piece swung off her as she moved.</summary>
    /// <summary>Her body's meshes TuckSkin marks (HerWear's tuck map: the same ones), and their skin materials.</summary>
    internal static bool TuckBody(MeshInstance3D mi)
    {
        string n = mi.Name.ToString();
        if (n.Contains('.') || n.Contains('_') || n.EndsWith("Head") || n.EndsWith("Tongue")) return false;
        return mi.Mesh is ArrayMesh am && (am.SurfaceGetFormat(0) & Mesh.ArrayFormat.FormatColor) != 0;
    }

    /// <summary>Her body's worn shape (heroine.glb's morph worn_KEY, tools/assets/worn_reaver_post.py): 1 while the
    /// garment it belongs to is worn, else 0. worn_reaver: under the reaver's top her breasts' undersides a little
    /// heavier, a soft roll under its lower edge (armor 15 w1).</summary>
    internal static void WornShape(Person p, string key, bool on)
    {
        foreach (var mi in p.Skeleton.GetChildren().OfType<MeshInstance3D>())
            if (mi.Mesh != null && mi.FindBlendShapeByName("worn_" + key) is int i and >= 0) mi.SetBlendShapeValue(i, on ? 1f : 0f);
    }

    internal static bool IsSkin(Material? m) => m is ShaderMaterial sm && skinShader2 != null && sm.Shader == skinShader2;

    /// <summary>The vertex-colour channel an outfit's tuck is marked in (-1: none).</summary>
    internal static int OutfitChannel(string set) => System.Array.IndexOf(OutfitChannels, set);

    static void TuckSkin(MeshInstance3D mi, int ch)
    {
        // (Only her body is marked; her head is left as it is, shape keys and all. Her head and tongue carry
        // vertex colours of their own since the smile pass (heroine_mouth.py: the mouth's depth, the tongue's
        // shade), which read as an outfit's channel would tuck them in and discard them whole: skipped by name.)
        string n = mi.Name.ToString();
        if (n.EndsWith("Head") || n.EndsWith("Tongue")) return;
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
            m.SetShaderParameter("face_world", FaceWorld(look));
            m.SetShaderParameter("look_rig", HeadRigOff ? 1f : lookRig);
            m.SetShaderParameter("body_lift", BodyLift(look));
            m.SetShaderParameter("soft_tone", SoftTone(look));
            m.SetShaderParameter("key_tone", KeyTone(look));
            m.SetShaderParameter("sky_tone", SkyTone(look));
            m.SetShaderParameter("edge_tone", EdgeTone(look));
            m.SetShaderParameter("neck_pull", NeckPull(look));
            m.SetShaderParameter("scatter", HerScatter);
            m.SetShaderParameter("back_spec", HerBackSpec);
        }
        // A body's relief baked from its sculpt (the hero's), under the pores.
        // (--relief-map PATH: her graft's relief from a file, tried before it is laid in the glb; face 37)
        var reliefTry = src.ResourceName == "skin_graft" ? TryFile("relief-map") : null;
        if ((reliefTry ?? src.NormalTexture) is Texture2D reliefTex)
        {
            m.SetShaderParameter("relief", reliefTex);
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
            if (HeadPaint(look.FaceShape) is Texture2D painted) m.SetShaderParameter("paint", painted);
            // (the inside of her mouth dark and unlit by depth: heroine_skin.gdshader mouth_in, heroine_mouth.py's colour)
            m.SetShaderParameter("mouth_in", 1f);
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
                var aoFile = HerSoftLipAo && ResourceLoader.Exists("res://art/people/head_tex/heroine_ao_softlip.png")
                    ? "res://art/people/head_tex/heroine_ao_softlip.png" : "res://art/people/head_tex/heroine_ao.png";
                m.SetShaderParameter("ao_map", GD.Load<Texture2D>(aoFile));
                m.SetShaderParameter("ao_light", 0.55f);
                // (her head's skin eased into the graft's over the 3 cm above her neck's seam: the shader's seam_*,
                // at the graft's rough, shine and pore depth, set above as every body part's)
                m.SetShaderParameter("seam_ease", true);
                // (the light through her kept to her ears and her nose's wings: the map's blue, heroine_thin.py)
                m.SetShaderParameter("thin_map", 1f);
            }
            // (her ears' hollows, a shade of their own that dims the lamps there and warms: tools/assets/heroine_ear_ao.py;
            // --ear-ao off: without it, for judging it)
            if (!EarAoOff && ResourceLoader.Exists("res://art/people/head_tex/heroine_ear_ao.png"))
            {
                m.SetShaderParameter("ear_ao", GD.Load<Texture2D>("res://art/people/head_tex/heroine_ear_ao.png"));
                m.SetShaderParameter("ear_amount", 1f);
                m.SetShaderParameter("ear_light", 0.7f);
                m.SetShaderParameter("ear_tint", new Vector3(0.80f, 0.52f, 0.44f));   // (HerEarWarmth's too)
            }
        }
        // (her skin warmer in the sky's light than in the lamps': HerAmbientTint)
        if (who == "heroine") HerShade(m, look);
        // (her face's skin zones, colour and sheen, her pores' coarse layer and the broad sheen lobe: HerZones)
        if (who == "heroine") HerZones(m, look, src.ResourceName == "skin_head");
        // Her freckles, a layer over her face, neck, shoulders and upper chest
        // (tools/assets/heroine_freckles.py), as many as her face starts with.
        if (who == "heroine" && FreckleFile(src.ResourceName) is string fp)
        {
            m.SetShaderParameter("freckles", GD.Load<Texture2D>(fp));
            m.SetShaderParameter("freckle_amount", HerFreckles(look));
            // (and her face's own fine grain up her neck, where the freckles' map's blue says: none from her
            // collarbones down; tools/assets/heroine_grain.py)
            if (ResourceLoader.Exists("res://art/people/head_tex/heroine_grain.png"))
            {
                m.SetShaderParameter("grain", GD.Load<Texture2D>("res://art/people/head_tex/heroine_grain.png"));
                m.SetShaderParameter("grain_amount", HerGrain);
                m.SetShaderParameter("grain_scale", SurfacePoreScale(mesh, src) * 0.321f);
            }
        }
        // His skin, all of it, rougher than hers: at her sheen his deep
        // relief caught the light as wet plastic.
        if (who == "hero")
        {
            m.SetShaderParameter("rough", HisSkin.Rough);
            m.SetShaderParameter("shine", HisSkin.Shine);
            m.SetShaderParameter("edge_rough", HisSkin.Edge);
        }
        // (--skin-set "skin_head:ao_light=0;skin_graft:shine=0.36": a developer's switch, a part's skin uniforms
        // tried without a build; a part "*" for every part)
        SkinSet(m, src.ResourceName);
        return m;
    }

    /// <summary>--skin-set "part:k=v,k=a/b/c;...": a part's skin uniforms tried without a build ("*" every part); applied
    /// in Skin() and again after her look's own tones and shade (HerShade), so it wins over them.</summary>
    static void SkinSet(ShaderMaterial m, string name)
    {
        if (SurvivorUnchained.Args.Get("skin-set") is string ss)
            foreach (var part in ss.Split(';'))
                if (part.Split(':') is [var who2, var kvs] && (who2 == "*" || who2 == name))
                    foreach (var kv in kvs.Split(','))
                        if (kv.Split('=') is [var k, var v])
                        {
                            // (a picture file (.png/.jpg, a path without a colon, relative to godot/): a texture uniform, e.g.
                            // paint=.shots/flat.png to take a layer out (face 41: flat paint, a neutral normal for pores/relief))
                            if (v.EndsWith(".png") || v.EndsWith(".jpg"))
                            {
                                if (Image.LoadFromFile(v) is { } img) { img.GenerateMipmaps(); m.SetShaderParameter(k.Trim(), ImageTexture.CreateFromImage(img)); }
                                continue;
                            }
                            // (a/b/c: a vec3)
                            var xs = v.Split('/').Select(t => float.TryParse(t, System.Globalization.NumberStyles.Float,
                                System.Globalization.CultureInfo.InvariantCulture, out var x) ? x : float.NaN).ToArray();
                            if (xs.Any(float.IsNaN)) continue;
                            if (xs.Length == 3) m.SetShaderParameter(k.Trim(), new Vector3(xs[0], xs[1], xs[2]));
                            else if (xs.Length == 2) m.SetShaderParameter(k.Trim(), new Vector2(xs[0], xs[1]));
                            else if (xs.Length == 1) m.SetShaderParameter(k.Trim(), xs[0]);
                        }
    }

    /// <summary>A Marionette NPC's skin (NpcPackage): the game's skin shader (heroine_skin.gdshader: pores, light under
    /// the skin, a soft sheen) on the package's own paint and relief, its paint its tone (no tint). Body and head take the
    /// same rough, shine and light, so the neck's seam between the two maps has no step in sheen; pores shallower on the
    /// body, as hers. A man's skin as his (HisSkin: rougher). Before 20 Oct the package kept its imported
    /// StandardMaterial3D: a flat, plastic beige beside every other person in town.</summary>
    public static Material NpcSkin(BaseMaterial3D src, Mesh mesh, bool woman)
    {
        var m = (ShaderMaterial)Skin(src, new Look(woman ? "female" : "male", System.Array.Empty<string>()), mesh, Colors.White, "npc");
        m.ResourceName = src.ResourceName;
        m.SetShaderParameter("rough", woman ? 0.55f : HisSkin.Rough);
        if (src.RoughnessTexture != null)
        {
            // The package paints absolute roughness (about 0.35-0.75): the shader multiplies it into `rough`, so rough is
            // the glTF factor (1.0 unless the package sets one), not the scalar guess above.
            m.SetShaderParameter("rough_map", src.RoughnessTexture);
            m.SetShaderParameter("rough_channel", (int)src.RoughnessTextureChannel);
            m.SetShaderParameter("rough", src.Roughness);
        }
        m.SetShaderParameter("shine", woman ? 0.38f : HisSkin.Shine);
        m.SetShaderParameter("scatter", HerScatter);
        // Light from all round comes out of skin redder (HerAmbientTint). Without it the town sky's blue on a package
        // NPC's reddish skin read magenta on the shaded cheek (the generated guard, judge r4: shade hue 22-28 deg
        // against the paint's 41-50; with it 37-43, warm tan; Marionette lead 12 solver I2, 21 Oct 2026).
        m.SetShaderParameter("ambient_tint", HerAmbientTint);
        return m;
    }

    /// <summary>How far light carried under her skin spreads on screen (the skin shader's `scatter`, Godot's
    /// screen-space scattering). Godot spreads the lit colour with her paint in it, so at the Look's close-up its
    /// 0.38 smeared her paint: brows paler than drawn (Doe's darkest third at 0.30 of her skin, her portrait's 0.18),
    /// freckles and pores gone, her grain at 0.62 / 0.79 / 0.91 of her portrait's (s0.8 / 1.6 / 3.2). At 0.1 it is
    /// 0.74 / 0.92 / 0.99 and Doe's brows 0.20; the soft edge of her lit side is the shader's own (`terminator`).
    /// (0.2 smeared as 0.38 did.)</summary>
    const float HerScatter = 0.1f;

    /// <summary>Her sheen from a lamp behind her, against one in front (the skin shader's back_spec): the Look's cool
    /// rim lamp lay over her collarbones and upper chest by her armour as a lilac sheen on every face (Oklab hue 34°
    /// against her skin's 54° round it, 0.06 lighter; judge n2, 11 October 2026). At 0.3: hue 46°, 0.02 lighter
    /// (Highborn), her lit cheek as it was. Every part of her alike, so no step at her neck's seam.</summary>
    const float HerBackSpec = 0.3f;

    /// <summary>Her skin in the sky's light against the lamps' (the skin shader's ambient_tint): light from all
    /// round goes deeper into skin and comes out redder. Without it, under her jaw, in the key's shadow, the night
    /// sky's blue made her neck grey-violet on every face (the owner, 10 October 2026: Oklab hue 31° against her
    /// portraits' 51°; with it and the grade keeping skin's hue in shade, 46-47°). Her lit face is as fitted.</summary>
    static readonly Vector3 HerAmbientTint = new(1.3f, 1.0f, 0.7f);

    /// <summary>The ambient tint by her skin's swatch, where it is not HerAmbientTint. Brown: at 1.3/1.0/0.7 her shade
    /// under her jaw and chin read copper against the blue night (Oklab chroma 31-36% over her portrait's; judge n1,
    /// 11 October 2026), as darker skin gives back less of the red light carried through it.</summary>
    static readonly Dictionary<string, Vector3> HerAmbientTints = new()
    {
        ["brown"] = new(1.0f, 1.0f, 0.8f),
    };

    /// <summary>The ambient tint, and HerBodyTone taken back out of it: her skin's own colour for a face is set for
    /// the lamps' light; in the sky's light alone (the shade under her jaw) it greyed her (jaw chroma 0.014 against
    /// her portrait's 0.051, own).</summary>
    /// <summary>Her skin's colour out of the lamps' direct light, for her face and swatch: the ambient tint, and where
    /// she faces down (under her jaw and chin, lit there only by the fill at a slant) HerBodyTone taken back out by
    /// the shader's shade_tint, its lightness kept. Her body's tone is set for lit skin (her portraits' lit necks are
    /// pale); applied in her shade too, it greyed the shade under her jaw (chroma 0.014 against her portrait's 0.051,
    /// own; skin in shade keeps its colour, the light coming back out of it).</summary>
    static void HerShade(ShaderMaterial m, Look look)
    {
        m.SetShaderParameter("ambient_tint", HerAmbient(look));
        m.SetShaderParameter("body_tone", BodyTone(look));
        m.SetShaderParameter("body_gate", BodyGate ? 1f : 0f);
        // Her soft lamps (the Look's fill and bounce, their sheen 0.1 and 0: SPECULAR_AMOUNT 0.2 and 0) show her paint's
        // own colour, all of her; the key, the fire and the sun her body's tone. (Tried 11 October 2026 (r6a): held
        // to where she faces down and gated by ndl, the shade at the side of her neck stayed grey (own jaw chroma
        // 0.015, portrait's 0.051); gated by each lamp's light at the point, it went warm (0.040) but the key's weak
        // light along her jaw's edge took her paint's colour too, an orange band. --shade-tint off | ndl | light |
        // soft (the default) and --shade-gate FROM,TO, for judging them (pictures).)
        // (her collar's relief: --relief-amount A its slopes' strength, --relief-rough R her skin that much rougher on them,
        // so its sheen spreads: heroine_skin.gdshader's relief_amount and relief_rough)
        m.SetShaderParameter("relief_amount", (float)SurvivorUnchained.Args.Num("relief-amount", 1f));
        m.SetShaderParameter("relief_rough", (float)SurvivorUnchained.Args.Num("relief-rough", 0f));
        // (deep skin's sheen, heroine_skin.gdshader's deep_spec and deep_tint: --deep-spec S, --deep-tint T)
        m.SetShaderParameter("deep_spec", (float)SurvivorUnchained.Args.Num("deep-spec", 0.6f));
        m.SetShaderParameter("deep_tint", (float)SurvivorUnchained.Args.Num("deep-tint", 0.6f));
        var mode = SurvivorUnchained.Args.Get("shade-tint") is string st && st != "" ? st : "soft";
        if (mode == "off") return;
        var b = BodyTone(look);
        m.SetShaderParameter("shade_tint", new Vector3(1 / b.X, 1 / b.Y, 1 / b.Z));
        bool down = mode == "ndl" || SurvivorUnchained.Args.Get("shade-down") == "on";
        m.SetShaderParameter("shade_down", down ? 1f : 0f);
        m.SetShaderParameter("down_from", 0.05f);
        m.SetShaderParameter("down_to", 0.45f);
        var gate = mode switch { "ndl" => new Vector2(0.85f, 1f), "light" => new Vector2(0.8f, 1.6f), _ => new Vector2(0.25f, 0.45f) };
        if (SurvivorUnchained.Args.Get("shade-gate") is string sg && sg.Split(',') is [var g0, var g1])
            gate = new Vector2(float.Parse(g0, System.Globalization.CultureInfo.InvariantCulture), float.Parse(g1, System.Globalization.CultureInfo.InvariantCulture));
        m.SetShaderParameter("shade_by_light", mode == "light" ? 1f : 0f);
        m.SetShaderParameter("shade_by_soft", mode == "soft" ? 1f : 0f);
        m.SetShaderParameter("shade_from", gate.X);
        m.SetShaderParameter("shade_to", gate.Y);
        // (her jaw's underside keeps most of that richness: at the shader's 0.75 the shade under her jaw at the Look,
        // turned 40, was a grey band (Oklab C 2.1-3.3 at L 34-37, hue 36-46, against her lit neck's 6.2 at hue 55),
        // read as stubble (judge J1, face 36); at 0.15 C 5.0-5.8, hue 50. Turned 80 (the orange wedge the 0.75 was for)
        // C 6.0 at L 38 against her lit neck's 4.8. The play camera unchanged (mean 0.05 of 255). --shade-thin X: another.)
        m.SetShaderParameter("shade_thin", (float)SurvivorUnchained.Args.Num("shade-thin", 0.15f));
    }

    /// <summary>Her skin's surface, zone by zone (max judge b1, face 44, 26 October 2026: fair read as smooth matte vinyl,
    /// deep as flat clay, one hue forehead to chin, no pores at the Look). The skin shader's zone_* (her face's colour
    /// zones and gloss zones, tools/assets/heroine_skin_zones.py: a redder nose, cheeks, ears and lip line, a yellower
    /// forehead, faint cool under her eyes and at her jaw, pinker lids; an oilier T-zone, softer cheeks, wet lips), sheen2
    /// (a second, broad sheen lobe) and peel / pore_rough (her pores' coarse layer, so her highlight breaks up at the
    /// Look's zoom). Her colour zones scaled by her skin's lightness: on deep skin a subtler, browner flush. head: her
    /// head's own material (the zone maps laid on it); null: a material already made (HerRestyle), its maps kept.
    /// (--skin-zones off: none of it, as before, for judging it; --skin-set overrides any of it.)</summary>
    static void HerZones(ShaderMaterial m, Look look, bool? head)
    {
        // (face 46 skin C, the night skin-line hold's lamp (HerSkinHold): an amber, a redder one on deep skin; its gain
        // keeps her lightness (on deep the night grade's toe took 0.025 Oklab L off her face at the lamps' own luminance))
        m.SetShaderParameter("hold_tint", HoldTint.Fair.Lerp(HoldTint.Deep, deep0(look)));
        m.SetShaderParameter("hold_gain", Mathf.Lerp(HoldGain.Fair, HoldGain.Deep, deep0(look)));
        m.SetShaderParameter("hold_chroma", 0f);
        if (SkinZonesOff) return;
        if (head == true)
        {
            if (ResourceLoader.Exists("res://art/people/head_tex/heroine_skin_zones.png"))
                m.SetShaderParameter("skin_zones", GD.Load<Texture2D>("res://art/people/head_tex/heroine_skin_zones.png"));
            if (ResourceLoader.Exists("res://art/people/head_tex/heroine_sheen_zones.png"))
                m.SetShaderParameter("sheen_zones", GD.Load<Texture2D>("res://art/people/head_tex/heroine_sheen_zones.png"));
            if (ResourceLoader.Exists("res://art/people/head_tex/heroine_pore_zones.png"))
                m.SetShaderParameter("pore_zones", GD.Load<Texture2D>("res://art/people/head_tex/heroine_pore_zones.png"));
        }
        float deep = deep0(look);
        m.SetShaderParameter("zone_colour", Mathf.Lerp(ZoneColour.Fair, ZoneColour.Deep, deep));
        m.SetShaderParameter("zone_flush", ZoneFlush.Fair.Lerp(ZoneFlush.Deep, deep));
        m.SetShaderParameter("zone_yellow", ZoneYellow.Fair.Lerp(ZoneYellow.Deep, deep));
        m.SetShaderParameter("zone_cool", ZoneCool.Fair.Lerp(ZoneCool.Deep, deep));
        m.SetShaderParameter("zone_lids", ZoneLids.Fair.Lerp(ZoneLids.Deep, deep));
        m.SetShaderParameter("zone_rough", 1f);
        m.SetShaderParameter("zone_rough_base", ZoneRough.Base);
        // (r2: deep skin's T-zone glosses a third as much, its lamps' sheen ZoneDeepSpec of HerShade's: it read oily)
        m.SetShaderParameter("zone_rough_t", Mathf.Lerp(ZoneRough.T, ZoneRough.Base - (ZoneRough.Base - ZoneRough.T) * 0.35f, deep));
        m.SetShaderParameter("deep_spec", (float)SurvivorUnchained.Args.Num("deep-spec", 0.6f) * Mathf.Lerp(1f, ZoneDeepSpec, deep));
        m.SetShaderParameter("zone_rough_cheek", ZoneRough.Cheek);
        m.SetShaderParameter("zone_rough_lip", ZoneRough.Lip);
        m.SetShaderParameter("zone_rough_body", ZoneRough.Body);
        m.SetShaderParameter("zone_lip_shine", Mathf.Lerp(ZoneRough.LipShine, ZoneLipShineDeep, deep));
        m.SetShaderParameter("lip_core", head != false ? 1f : 0f);   // (her body: no pore_zones read)
        m.SetShaderParameter("freckle_keep", FreckleKeep);
        m.SetShaderParameter("freckle_gain", FreckleGain);
        m.SetShaderParameter("skin_chroma", Mathf.Lerp(0f, DeepChroma, deep));
        // (deep skin's sheen already shows strongly against its darker diffuse: the broad lobe less there, or it reads oily)
        m.SetShaderParameter("sheen2", Sheen2.Amount * Mathf.Lerp(1f, Sheen2.Deep, deep));
        m.SetShaderParameter("sheen2_rough", Sheen2.Rough);
        m.SetShaderParameter("sheen2_base", Sheen2.Base);
        if (head != null && ResourceLoader.Exists("res://art/people/skin_peel.png"))
            m.SetShaderParameter("peel_map", GD.Load<Texture2D>("res://art/people/skin_peel.png"));
        // (r2: the coarse layer only where pores show (pore_zones), its slopes mostly on her sheen, eased out with distance;
        // none on her body. Off by default (face 45, judge a2: on deep at the Look's turn 40 they glint on the sheen like
        // glitter, and on fair they don't show at 1:1); --skin-pores on: the r2 layer, for the later list's rework)
        bool pores = SkinPoresOn;
        m.SetShaderParameter("peel", pores ? (head == false ? Peel.Body : Mathf.Lerp(Peel.Head, Peel.Deep, deep)) : 0f);
        m.SetShaderParameter("peel_scale", Peel.Scale);
        m.SetShaderParameter("pore_rough", pores && head != false ? Peel.Rough : 0f);
        m.SetShaderParameter("pore_mask", head != false ? 1f : 0f);
        m.SetShaderParameter("peel_diffuse", Peel.Diffuse);
        m.SetShaderParameter("peel_fade", Peel.Fade);
    }

    /// <summary>Her skin's darkness for her zones and hold: 0 at her own fair paint, 1 at the Deep swatch's lightness.</summary>
    static float deep0(Look look)
    {
        var t = HerTone(look);
        float lum = 0.2126f * t.R * t.R + 0.7152f * t.G * t.G + 0.0722f * t.B * t.B;   // (about linear)
        return Mathf.Clamp((0.55f - lum) / (0.55f - 0.06f), 0f, 1f);
    }

    // (tuned at the town night close-up, face 46: fair forehead/cheek/nose/neck/shoulder hue 50-53/52/44/47/50, deep 52/47/47/52/52,
    // her skin line 48.5; Oklab L within 0.01)
    static readonly (Vector3 Fair, Vector3 Deep) HoldTint = (new(1f, 0.67f, 0.25f), new(1f, 0.6f, 0.22f));
    static readonly (float Fair, float Deep) HoldGain = (1.1f, 1.35f);

    static readonly bool SkinPoresOn = SurvivorUnchained.Args.Get("skin-pores") == "on";
    static readonly float ZoneDeepSpec = 0.8f;
    static readonly float ZoneLipShineDeep = 0.5f;
    static readonly float FreckleKeep = 1f;
    // (her freckles' step held within 10% of before's: town day cheeks -8.0 before, -6.4 without the gain; the Look -10.8)
    static readonly float FreckleGain = 1.12f;
    static readonly float DeepChroma = 0.2f;   // (linear; her diffuse's Oklab chroma about 8% more after the grade)

    static readonly bool SkinZonesOff = SurvivorUnchained.Args.Get("skin-zones") == "off";
    static readonly (float Fair, float Deep) ZoneColour = (0.85f, 0.7f);
    static readonly (Vector3 Fair, Vector3 Deep) ZoneFlush = (new(1.14f, 0.68f, 0.46f), new(1.04f, 0.84f, 0.78f));
    static readonly (Vector3 Fair, Vector3 Deep) ZoneYellow = (new(0.985f, 1f, 0.93f), new(1f, 1f, 1f));
    static readonly (Vector3 Fair, Vector3 Deep) ZoneCool = (new(0.94f, 0.97f, 1.03f), new(0.96f, 0.98f, 1.0f));
    static readonly (Vector3 Fair, Vector3 Deep) ZoneLids = (new(0.96f, 0.84f, 0.86f), new(0.94f, 0.88f, 0.88f));
    static readonly (float Base, float T, float Cheek, float Lip, float Body, float LipShine) ZoneRough = (0.5f, 0.4f, 0.55f, 0.3f, 0.5f, 0.6f);
    static readonly (float Amount, float Rough, float Base, float Deep) Sheen2 = (0.6f, 0.75f, 0.4f, 0.25f);
    // (r2: Head its slopes' strength on fair skin, Deep on deep (its sheen shows them more); Scale 0.4, its bumps 0.83 of
    // round 1's (half, 0.667, fell under a pixel at the Look's zoom 1 and showed nothing); Diffuse: her diffuse light sees
    // that much of its slopes (light under the skin blurs its own shading); Fade: eased out from 0.5 to 0.87 mm a pixel (the
    // shader's peel_mm): the Look's zoom 1 is about 0.35 (all of it), its zoom 0.55 about 0.6 (some), the town's close view
    // about 0.95 (none, her roughness's variation only))
    static readonly (float Head, float Deep, float Body, float Scale, float Rough, float Diffuse, Vector2 Fade) Peel = (1.2f, 0.9f, 0f, 0.4f, 0.15f, 0.25f, new(0.5f, 0.87f));

    /// <summary>Skin A1's tone refit (face 44, 26 October 2026; --tone-a1 off: before, for judging it): the Deep swatch read
    /// brick red (the Look by night her lit face Oklab hue ~40, the town close-up's chest 29-33, against her albedo's 51),
    /// so it takes a fit of its own toward umber (HerToneFit's "deep": less red, a little less chroma) and the brown
    /// swatch's ambient tint (the sky's light through her came out red); and her face, paler and pinker than her chest on
    /// both tones, takes a trim of its own per swatch (FaceSwatch, on face_tone and face_world).
    /// (--deep-fit R,G,B and --face-swatch R,G,B: others, linear, for judging them.)</summary>
    static readonly bool ToneA1 = SurvivorUnchained.Args.Get("tone-a1") != "off";

    static Vector3 ArgVec(string name, Vector3 v) => SurvivorUnchained.Args.Get(name) is string a && a.Split(',') is [var r, var g, var b]
        ? new(float.Parse(r, System.Globalization.CultureInfo.InvariantCulture), float.Parse(g, System.Globalization.CultureInfo.InvariantCulture), float.Parse(b, System.Globalization.CultureInfo.InvariantCulture))
        : v;

    static readonly Vector3 DeepFit = ArgVec("deep-fit", new(0.86f, 1.24f, 0.90f));

    static readonly Dictionary<string, Vector3> HerFaceSwatch = new()
    {
        ["fair"] = ArgVec("face-swatch-fair", new(1f, 1f, 1f)), ["deep"] = ArgVec("face-swatch", new(1.02f, 0.93f, 1f)),
    };

    /// <summary>Her deep swatch's neck at the Look, drawn toward her face's colour (the skin shader's neck_pull: rgb a
    /// colour her albedo's is mixed toward, linear, a how far; face 47, 27 October 2026). By night the neck under her jaw
    /// read olive-grey (Oklab h 64, C .029) under a fire-lit red-brown face (h 47): deep's toned albedo there was 16-27 deg
    /// yellower than her face's, which takes face_tone and FaceSwatch where her neck takes neither. With it, turn 40: under
    /// her jaw h 44.5 C .057, lower neck 46.2 .081, jaw 48.1 (cheek 47.3); turn 0 neck 45.8 .071; L +.007-.010. Deep only and under the rig only
    /// (fair, play and the town as before). (--deep-neck off: before; --deep-neck R,G,B,A: another, for judging it.)</summary>
    static readonly Vector4 DeepNeck = SurvivorUnchained.Args.Get("deep-neck") is string dn
        ? dn == "off" ? Vector4.Zero : dn.Split(',') is [var r, var g, var b, var w]
            ? new(float.Parse(r, System.Globalization.CultureInfo.InvariantCulture), float.Parse(g, System.Globalization.CultureInfo.InvariantCulture), float.Parse(b, System.Globalization.CultureInfo.InvariantCulture), float.Parse(w, System.Globalization.CultureInfo.InvariantCulture))
            : Vector4.Zero
        : new(2.231f, 0.636f, 0.014f, 0.55f);   // (Oklab h 60, C .085 at L .37, luminance 0.93; fitted at the Look by night)

    static Vector4 NeckPull(Look look) => ToneA1 && HerSkinId(look) == "deep" && DeepNeck.W > 0f ? DeepNeck : new(1f, 1f, 1f, 0f);

    static Vector3 FaceSwatch(Look look) => ToneA1 && HerFaceSwatch.TryGetValue(HerSkinId(look), out var v) ? v : Vector3.One;

    static Vector3 HerAmbient(Look look)
    {
        var a = ToneA1 && HerSkinId(look) == "deep" ? HerAmbientTints["brown"] : HerAmbientTints.TryGetValue(HerSkinId(look), out var t) ? t : HerAmbientTint;
        return a / BodyTone(look);
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
        ["warm"] = new(0.886f, 1.054f, 0.791f), ["brown"] = new(0.789f, 0.887f, 0.629f),
    };

    /// <summary>Each face's own paint against its portrait, once its swatch is fitted (linear, the
    /// skin shader's face_tone, laid on her face alone): one swatch serves several faces, and a face's
    /// paint came out up to 8% off its portrait (Fey 6% dark, Vixen too blue, Moonlit too red), so
    /// beside it the face read a shade wrong while its neck was right.</summary>
    static readonly Dictionary<string, Vector3> HerFaceTone = new()
    {
        // (11 October 2026, the Look's rig made near white: each face's cheek taken to its portrait's chroma and hue,
        // on top of HerBodyTone below, which these partly undo on the face; judge j2's trims, measured at the Look)
        ["own"] = new(1.358f, 0.890f, 0.660f), ["highborn"] = new(1.009f, 0.763f, 0.641f),
        ["vixen"] = new(1.052f, 0.766f, 0.616f), ["moonlit"] = new(1.038f, 0.831f, 0.699f),
        ["fey"] = new(1.171f, 0.847f, 0.665f), ["doe"] = new(1.034f, 0.780f, 0.669f),
        ["wildling"] = new(0.952f, 0.728f, 0.637f), ["hardwon"] = new(1.166f, 0.948f, 0.813f),
        ["saffron"] = new(0.906f, 0.748f, 0.682f),
        // (Sunborn: her face lighter, a little less red, against her body: her cheek at 0.86 of her portrait's
        // lightness against 0.92-0.97 for the others, her head darker than her neck; judge n1, 11 October 2026)
        // (Refitted 20 October 2026, face 31 tone r1-r2, after the body's rebuild: every face but Own and Hardwon read
        // 4-7 Oklab L lighter than her lit upper chest at its own skin, and Sunborn's 10 deg yellower at her brow, olive
        // grey over a red-brown body (the Look's judge). Each cheek taken to her chest's L + 0.015 (Own's, judged), her
        // neck's and chest's mean hue + 1 deg, chroma at least 1.12 of her chest's: tools/scratch/face31/tone_fit.py, two passes. Before, as above:
        // highborn 1.168/0.905/0.824, vixen 1.170/0.878/0.730, moonlit 1.159/0.947/0.841, fey 1.320/0.973/0.816,
        // doe 1.167/0.947/0.783, wildling 1.102/0.928/0.765, saffron 1.071/0.963/0.887, sunborn 1.146/1.262/1.646.)
        ["sunborn"] = new(0.999f, 0.851f, 0.840f),
    };

    /// <summary>Her skin's own colour for each face, all of her (linear, on her swatch's HerTone): her neck and
    /// body at the portrait's neck-to-cheek chroma (0.56-0.80 of the cheek's, Sunborn 0.97) and its cheek's hue.
    /// Under the Look's warm rig every face read a fake tan, her neck as saturated as her cheek and 40-80% over
    /// her portrait's (judge j1, 11 October 2026). (--tone-trim off: none, and the faces' tones as before.) Measured at the Look and refitted (r1, r3; r6b with BodyK 1 and the soft lamps' shade).</summary>
    static readonly Dictionary<string, Vector3> HerBodyTone = new()
    {
        ["own"] = new(0.656f, 1.173f, 2.152f), ["highborn"] = new(0.768f, 1.109f, 1.764f),
        ["doe"] = new(0.762f, 1.132f, 1.975f), ["sunborn"] = new(1.056f, 0.948f, 0.956f),
        ["vixen"] = new(0.740f, 1.123f, 1.862f), ["moonlit"] = new(0.729f, 1.134f, 1.840f),
        ["saffron"] = new(0.861f, 1.080f, 1.715f), ["wildling"] = new(0.817f, 1.095f, 1.789f),
        ["hardwon"] = new(0.771f, 1.120f, 2.020f), ["fey"] = new(0.729f, 1.129f, 1.885f),
    };

    static readonly Dictionary<string, Vector3> HerFaceToneUntrimmed = new()
    {
        ["own"] = new(1.004f, 0.995f, 0.985f), ["highborn"] = new(0.981f, 0.981f, 0.969f),
        ["vixen"] = new(0.982f, 0.940f, 0.922f), ["moonlit"] = new(0.972f, 1.021f, 1.080f),
        ["fey"] = new(1.062f, 1.067f, 1.050f), ["doe"] = new(1.004f, 1.016f, 1.013f),
        ["wildling"] = new(0.992f, 0.969f, 0.957f), ["hardwon"] = new(1.004f, 1.016f, 1.032f),
        // (no Sunborn: her 1.20/1.23/1.23 was fitted at the Look, which HerFaceTone now holds; out here it lit her face
        // 3 L* over her Brown in play, day and night; judge rj2v fix 4, 13 October 2026)
    };

    static readonly bool ToneTrim = SurvivorUnchained.Args.Get("tone-trim") != "off";

    /// <summary>How much of HerBodyTone her body takes (0 none to 1 all; the rest goes to her face's tone, so her
    /// cheek is as fitted either way). (--body-k K: another, for judging it (pictures).)</summary>
    /// (All of it: her soft lamps' light shows her paint's own colour (HerShade), so the shade under her jaw keeps its
    /// warmth. Before that, at 1 the shade went grey-violet (chroma 0.015, hue 30, own) and it shipped at 0.5.)
    static readonly float BodyK = SurvivorUnchained.Args.Has("body-k") ? (float)SurvivorUnchained.Args.Num("body-k", 1f) : 1f;

    /// <summary>Her body's tone kept on her head and up her neck, where it was fitted, and from her collarbones down taken
    /// out of the lamps' light on her, with the key's and the soft lamps' tones fitted with it (the skin shader's body_tone
    /// and body_gate, by her freckles' map's blue): fitted on her lit neck against the Look's warm key, its blue turned her
    /// chest, arms and thighs a cold lilac-grey beside the fire and her thighs grey-lilac at night, where they were warm
    /// peach (judge s1, 12 October 2026; body r1: the Look's whole frame and play at night within 0.005 of integration's
    /// Oklab chroma, 3-25 deg warmer, where they were 60-100 deg cooler). (--body-gate off: all of her takes them, as
    /// before, for judging it.)</summary>
    static readonly bool BodyGate = SurvivorUnchained.Args.Get("body-gate") != "off";

    static Vector3 Pow(Vector3 v, float k) => new(Mathf.Pow(v.X, k), Mathf.Pow(v.Y, k), Mathf.Pow(v.Z, k));

    /// <summary>Her body's tone for her face, as much of it as BodyK says (one when untrimmed).</summary>
    static Vector3 BodyTone(Look look) => ToneTrim && HerBodyTone.TryGetValue(FaceId(look), out var b) ? Pow(b, BodyK) : Vector3.One;

    /// <summary>How much of her face's own grain her neck takes (the skin shader's grain_amount; 1 her face's
    /// paint's own spread; none from her collarbones down, by her freckles' map's blue): her portrait's neck has
    /// nearly half her face's grain, and her neck's relief alone gave it a quarter. (Over her body too, it was the
    /// speckle over her breasts.) (--grain tries another.)</summary>
    static readonly float HerGrain = SurvivorUnchained.Args.Has("grain") ? SurvivorUnchained.Args.Num("grain", 3f) : 3f;

    /// <summary>Her face's tone outside the Look's portrait rig (the skin shader's face_world): her face's own tone against
    /// its portrait as it was before the rig's fit (HerFaceToneUntrimmed). Every tone above was fitted under that rig, its
    /// key with the soft fill showing her paint without HerBodyTone; under the fire, the moon and the sun alone her head kept
    /// HerBodyTone's blue, pale blue-white over a warm firelit body in the Look's whole frame (judge rj1v, 12 October 2026).
    /// Outside the rig her head takes her body's treatment and her face this (the shader's look_rig, HerLookRig).</summary>
    static Vector3 FaceWorld(Look look) => (HerFaceToneUntrimmed.TryGetValue(FaceId(look), out var t) ? t : Vector3.One) * FaceSwatch(look);

    /// <summary>How much of the Look's portrait rig lights her, on every part of her skin (the skin shader's look_rig: 1 her
    /// head's tones as fitted under the rig, 0 her body's treatment and her face's FaceWorld, as in play). GameFront sets it
    /// each frame, as the rig comes up. (--head-rig off: 1 always, her head as fitted in every light, for judging it.)</summary>
    public static void HerLookRig(Person p, float w)
    {
        if (p.Body != "heroine") return;
        lookRig = w;
        if (HeadRigOff) w = 1;
        foreach (var mi in p.Meshes)
            for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
                if (mi.GetSurfaceOverrideMaterial(s) is ShaderMaterial m && (m.Shader == skinShader2 || (outfitShader != null && m.Shader == outfitShader) || (metalShader != null && m.Shader == metalShader)))
                    m.SetShaderParameter("look_rig", w);   // (her outfit too: its steel and leather rougher under the rig, s29)
    }

    /// <summary>Her share of the sky's light on her skin (the skin shader's sky_share, 1 as everywhere): GameCloseUp sets it in
    /// the town's close view by day, where the grey sky's light lay level over her face (face 34). body: her share from
    /// her collarbones down (the shader's sky_body), when it differs from her face's (-1: w all over).</summary>
    public static void HerSkyShare(Person p, float w, float body = -1)
    {
        if (p.Body != "heroine") return;
        foreach (var mi in p.Meshes)
            for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
                if (mi.GetSurfaceOverrideMaterial(s) is ShaderMaterial m && m.Shader == skinShader2)
                { m.SetShaderParameter("sky_share", w); m.SetShaderParameter("sky_body", body); }
    }

    /// <summary>Her eyes by night (heroine_eye.gdshader's night_ease, 0 by day to 1): the lids' shade on them eased
    /// and the iris lifted (HerEyes' night_*), so under the night key her irises read a dark olive, not black.
    /// GameCloseUp sets it each frame while its night light is on her.</summary>
    public static void HerEyesNight(Person p, float k)
    {
        if (p.Body != "heroine" || eyeShader == null) return;
        foreach (var mi in p.Meshes)
            for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
                if (mi.GetSurfaceOverrideMaterial(s) is ShaderMaterial m && m.Shader == eyeShader) m.SetShaderParameter("night_ease", k);
    }

    /// <summary>Her skin's night skin-line hold (heroine_skin.gdshader's skin_hold, 0 by day to 1): each warm lamp's colour
    /// on her skin pulled toward hold_tint (face 46 skin C), so under the night key and the fires she stays on her skin line
    /// while her hair, clothes and the scene keep their warmth. GameCloseUp sets it each frame while its night light is on
    /// her. --skin-hold off: none (as before); --skin-hold K: K of it (pictures).</summary>
    /// <summary>Her skin's own lift (Rendering 3, judge j2 D3): the skin shader's tone times k (1: as her look set it), her skin
    /// only, where the Look's lights lifted by night for deep skin lifted her copper hair pale with it. The tone her look set is
    /// kept on the material (meta) and taken again when her look sets a new one.</summary>
    /// <summary>Her skin's darkness, 0 (the fairest swatch's luminance, 0.4 linear, or over) to 1 (0.04 or under), from the tone
    /// her look set on her skin (Rendering 3: the close view's fill by night is the stronger on deep skin).</summary>
    public static float HerSkinDark(Person p)
    {
        if (p.Body != "heroine" || skinShader2 == null) return 0;
        foreach (var mi in p.Meshes)
            for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
                if (mi.GetSurfaceOverrideMaterial(s) is ShaderMaterial m && m.Shader == skinShader2)
                {
                    var c = (m.HasMeta("su_tone0") ? m.GetMeta("su_tone0").AsColor() : m.GetShaderParameter("tone").AsColor()).SrgbToLinear();
                    return Mathf.Clamp((0.4f - (0.2126f * c.R + 0.7152f * c.G + 0.0722f * c.B)) / 0.36f, 0, 1);
                }
        return 0;
    }

    public static void HerSkinGain(Person p, float k)
    {
        if (p.Body != "heroine" || skinShader2 == null) return;
        foreach (var mi in p.Meshes)
            for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
                if (mi.GetSurfaceOverrideMaterial(s) is ShaderMaterial m && m.Shader == skinShader2)
                {
                    var now = m.GetShaderParameter("tone").AsColor();
                    // (a tone not the one set here last: her look set it again, the new base)
                    Color b = m.HasMeta("su_tone0") && m.HasMeta("su_tone_set") && m.GetMeta("su_tone_set").AsColor().IsEqualApprox(now) ? m.GetMeta("su_tone0").AsColor() : now;
                    if (Mathf.IsEqualApprox(k, 1)) { if (m.HasMeta("su_tone0")) { m.SetShaderParameter("tone", b); m.RemoveMeta("su_tone0"); m.RemoveMeta("su_tone_set"); } continue; }
                    // (tone is sRGB (source_color): k in linear light)
                    var lin = b.SrgbToLinear(); var t = new Color(lin.R * k, lin.G * k, lin.B * k).LinearToSrgb();
                    m.SetShaderParameter("tone", t); m.SetMeta("su_tone0", b); m.SetMeta("su_tone_set", t);
                }
    }

    public static void HerSkinHold(Person p, float k)
    {
        if (p.Body != "heroine" || skinShader2 == null) return;
        k *= SkinHold;
        foreach (var mi in p.Meshes)
            for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
                if (mi.GetSurfaceOverrideMaterial(s) is ShaderMaterial m && m.Shader == skinShader2) m.SetShaderParameter("skin_hold", k);
    }

    static readonly float SkinHold = SurvivorUnchained.Args.Get("skin-hold") == "off" ? 0f : (float)SurvivorUnchained.Args.Num("skin-hold", 1f);

    /// <summary>Her ears' warm shade (ear_tint) and the light through her (backlight) taken k of the way from none to as built (1), for a cinematic's own light
    /// (C03, judge r1: a warm ear against a cool face under the moon); 1 gives it back.</summary>
    public static void HerEarWarmth(Person p, float k)
    {
        if (p.Body != "heroine") return;
        var t = new Vector3(1, 1, 1).Lerp(new Vector3(0.80f, 0.52f, 0.44f), k);
        foreach (var mi in p.Meshes)
            for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
                if (mi.GetSurfaceOverrideMaterial(s) is ShaderMaterial m && m.Shader == skinShader2)
                {
                    // (and the light through her ears, red: a moon behind her lit them like a lamp's)
                    if (!m.HasMeta("backlight0")) m.SetMeta("backlight0", m.GetShaderParameter("backlight").VariantType == Variant.Type.Nil ? 0.18f : m.GetShaderParameter("backlight"));
                    m.SetShaderParameter("backlight", (float)m.GetMeta("backlight0") * k);
                    if ((float)m.GetShaderParameter("ear_amount") > 0) m.SetShaderParameter("ear_tint", t);
                }
    }

    static readonly bool HeadRigOff = SurvivorUnchained.Args.Get("head-rig") == "off";
    static readonly bool EarAoOff = SurvivorUnchained.Args.Get("ear-ao") == "off";

    // (the rig's weight now, for her skin made while it is up: a look chosen at the close-up)
    static float lookRig;

    static Vector3 FaceTone(Look look)
    {
        var f = (ToneTrim ? HerFaceTone : HerFaceToneUntrimmed).TryGetValue(FaceId(look), out var t) ? t : Vector3.One;
        f *= FaceSwatch(look);
        return ToneTrim && HerBodyTone.TryGetValue(FaceId(look), out var b) ? f * Pow(b, 1 - BodyK) : f;
    }

    static string FaceId(Look look) => string.IsNullOrEmpty(look.FaceShape) ? "own" : look.FaceShape;

    /// <summary>How much paler her neck and body are than her face (linear, the skin shader's body_lift): her portraits'
    /// lit necks and upper chests sit 0.05-0.1 lighter (Oklab L) than their cheeks; hers sat level with her cheek
    /// (judge j5, 11 October 2026). Fitted at the Look with her neck 3 cm shorter, where her neck's spot falls on the
    /// same part of her as on her portrait's (at today's length it is higher up her neck, turned from the key).
    /// (--body-lift X: another, for judging it (pictures).)</summary>
    static readonly Dictionary<string, float> HerBodyLift = new()
    {
        // (refitted on a band, 0.3-0.8 pupil-chin below the chin, at both neck lengths on the same anatomy, after the
        // lift was kept off lamps behind her and its fade widened; WIP, judge j7 next: tools/scratch/face19/bandfit.py)
        ["own"] = 1.30f, ["highborn"] = 1.03f, ["doe"] = 1.22f, ["sunborn"] = 1.32f, ["vixen"] = 1.07f,
        ["moonlit"] = 1.26f, ["saffron"] = 1.27f, ["wildling"] = 1.07f, ["hardwon"] = 1.21f, ["fey"] = 1.09f,
    };

    /// <summary>Her shade's colour off her face (the skin shader's soft_tone, linear): the soft lamps' light on her neck
    /// and under her jaw, outside her face's paint. Her head's own skin there showed greyer than her portrait's shade
    /// (jaw chroma 37-55% short on the fair faces, judge j5, 11 October 2026); fitted at the Look to each portrait's
    /// chroma and hue under her jaw, its lightness kept (tools/scratch/face17/softfit.py, clamped 0.5-1.6). Sunborn's
    /// shade there is lit mostly by the key, out of this one's reach. (Vixen, Moonlit and Fey at the fair faces' median took
    /// a third of their jaw's chroma and none of its missing shade, which is the key's: face 19, r8.) (Highborn refitted, skin r13
    /// B1b: at 0.93/1.03/1.08 the soft-lit middle of her neck was grey at her lit neck's hue, C 53-79% of it; at 1.30/0.92/0.72
    /// 65-101%, hue as it was, her far neck's (b) kept.) (--soft-tone R,G,B: another, for judging it.)</summary>
    static readonly Dictionary<string, Vector3> HerSoftTone = new()
    {
        ["own"] = new(1.268f, 0.877f, 0.571f), ["highborn"] = new(1.30f, 0.92f, 0.72f), ["doe"] = new(1.192f, 0.881f, 0.737f),
        ["vixen"] = new(1.479f, 0.814f, 0.500f), ["moonlit"] = new(1.518f, 0.798f, 0.500f), ["saffron"] = new(1.047f, 0.942f, 1.214f),
        ["wildling"] = new(1.217f, 0.853f, 0.684f), ["hardwon"] = new(1.117f, 0.909f, 0.991f), ["fey"] = new(1.338f, 0.857f, 0.504f),
    };

    static Vector3 SoftTone(Look look) => SurvivorUnchained.Args.Get("soft-tone") is string st && st.Split(',') is [var r, var g, var b2]
        ? new(float.Parse(r, System.Globalization.CultureInfo.InvariantCulture), float.Parse(g, System.Globalization.CultureInfo.InvariantCulture), float.Parse(b2, System.Globalization.CultureInfo.InvariantCulture))
        : ToneTrim && HerSoftTone.TryGetValue(FaceId(look), out var v) ? v : Vector3.One;

    /// <summary>The line above her upper lip (the owner, 12 October 2026): her sculpt's lip border sits 4.4-7.6 mm above
    /// every portrait's painted red, and her head's shade drew it as an outline in skin. True: the shade with that
    /// crease eased out (heroine_ao_softlip.png, tools/assets/heroine_ao_softlip.py), each face keeping its portrait's
    /// lip. False: the shade as baked. (Env SOFTLIP=0: false, for judging.)</summary>
    public static bool HerSoftLipAo = OS.GetEnvironment("SOFTLIP") != "0";

    /// <summary>Her neck's and body's colour in every lamp but the soft ones (the skin shader's key_tone, linear, its
    /// lightness kept), outside her face's paint. HerBodyTone was fitted on her lit neck, where the warm fill (which shows
    /// her paint without it) meets the key, so the key's share went grey: under a white rig her lit neck was Oklab C .015,
    /// and where the fill can't reach, the far side of her neck under her jaw was blue-grey (own hue -61) and in the moon
    /// her whole body lavender under a peach face (the owner, 10 October 2026). Fitted at the Look (r9 pose) to each
    /// portrait's shaded neck side, hue and chroma, at the far neck (tools/scratch/face21). The warm faces read warm and
    /// are left as they were. (--key-tone R,G,B: another, for judging it.)</summary>
    static readonly Dictionary<string, Vector3> HerKeyTone = new()
    {
        // (r11: her lit neck to her portrait's (own C .034 h52 against .035 h56); r10's 0.6 of the far neck's fit left it
        // rich, C .045 h58. The richer far side of her neck is HerEdgeTone's. Own fitted (s11b), the others scaled as own.)
        ["own"] = new(1.080f, 0.985f, 0.870f), ["highborn"] = new(1.053f, 0.985f, 0.890f), ["vixen"] = new(1.062f, 0.983f, 0.870f),
        ["moonlit"] = new(1.065f, 0.981f, 0.880f), ["fey"] = new(1.057f, 0.985f, 0.880f),
    };

    static Vector3 KeyTone(Look look) => SurvivorUnchained.Args.Get("key-tone") is string kt && kt.Split(',') is [var r, var g, var b2]
        ? new(float.Parse(r, System.Globalization.CultureInfo.InvariantCulture), float.Parse(g, System.Globalization.CultureInfo.InvariantCulture), float.Parse(b2, System.Globalization.CultureInfo.InvariantCulture))
        : ToneTrim && HerKeyTone.TryGetValue(FaceId(look), out var v) ? v : Vector3.One;

    /// <summary>Her neck's and body's colour under the sun and the moon (the skin shader's sky_tone, for directional lamps
    /// in place of key_tone, its lightness kept, outside her face's paint): her face's own tone (HerFaceTone), so under
    /// them her body takes her face's colour. HerBodyTone's blue was fitted against the Look's warm key; under the moon
    /// (the Look's whole frame, play at night) nothing warmed it back and her thighs and arms read lavender-blue under
    /// her face (judge j7 (f): own's thighs -11 and -21 deg off her cheek, +10% and +63% chroma; with this +7 and -7,
    /// -30% and +2%; skin r13 B1). OFF BY DEFAULT, UNJUDGED: on Doe it overshot (thighs +15 and -4 deg to +55 and +35)
    /// and on Highborn one thigh went +1 to +16, so it wants a fit per face. (--sky-tone face: her face's tone; R,G,B
    /// another, for judging it; none: as key_tone, r12.)</summary>
    static Vector3 SkyTone(Look look) => SurvivorUnchained.Args.Get("sky-tone") is string st
        ? (st == "face" ? FaceTone(look) : st.Split(',') is [var r, var g, var b2]
            ? new(float.Parse(r, System.Globalization.CultureInfo.InvariantCulture), float.Parse(g, System.Globalization.CultureInfo.InvariantCulture), float.Parse(b2, System.Globalization.CultureInfo.InvariantCulture))
            : Vector3.Zero)
        : Vector3.Zero;

    /// <summary>Her neck and body richer where she turns from the lens (the skin shader's edge_tone, on key_tone, linear,
    /// its lightness kept; below her head). Her portraits' neck sides are 1.6 times as rich as their lit fronts (Oklab C);
    /// ours were 0.7-0.8 times at every key tone, as the key lights the far side of her neck at 0.8 of her lit neck's light
    /// (face 22, s11a). (--edge-tone R,G,B: another, for judging it.)</summary>
    static readonly Dictionary<string, Vector3> HerEdgeTone = new()
    {
        // (own fitted at the Look, r9 pose (s11b: far neck C .046 h50 against her portrait's shade .056 h56); the others as own)
        ["own"] = new(1.45f, 0.90f, 0.54f), ["highborn"] = new(1.45f, 0.90f, 0.54f), ["vixen"] = new(1.45f, 0.90f, 0.54f),
        ["moonlit"] = new(1.45f, 0.90f, 0.54f), ["fey"] = new(1.45f, 0.90f, 0.54f),
    };

    static Vector3 EdgeTone(Look look) => SurvivorUnchained.Args.Get("edge-tone") is string et && et.Split(',') is [var r, var g, var b2]
        ? new(float.Parse(r, System.Globalization.CultureInfo.InvariantCulture), float.Parse(g, System.Globalization.CultureInfo.InvariantCulture), float.Parse(b2, System.Globalization.CultureInfo.InvariantCulture))
        : ToneTrim && HerEdgeTone.TryGetValue(FaceId(look), out var v) ? v : Vector3.One;

    static float BodyLift(Look look) => SurvivorUnchained.Args.Has("body-lift") ? (float)SurvivorUnchained.Args.Num("body-lift", 1f)
        : ToneTrim && HerBodyLift.TryGetValue(FaceId(look), out var v) ? v : 1f;

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

    /// <summary>Her skin's swatch (Lore.Skins' id; "fair", her own, when none is chosen).</summary>
    static string HerSkinId(Look look) => look.Skin is Color c
        ? SurvivorUnchained.World.Lore.Skins.FirstOrDefault(s => s.Color != "" && new Color(s.Color).IsEqualApprox(c))?.Id ?? ""
        : "fair";

    static Color HerTone(Look look)
    {
        var t = SkinTone(look);
        string id = HerSkinId(look);
        var f = HerToneFit.TryGetValue(id, out var fit) ? fit : ToneA1 && id == "deep" ? DeepFit : Vector3.One;
        f *= BodyTone(look);
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
            var (a, u) = SurfaceAreas(mesh, s);
            area += a;
            uvArea += u;
        }
        k = uvArea > 0 ? (float)(Math.Sqrt(area / uvArea) / 0.009) : 50f;
        poreScales[mesh] = k;
        return k;
    }

    /// <summary>A surface's own pore scale (as PoreScale, its surface alone): her graft, a small part of her
    /// body's mesh, has UVs laid at a ninth of her body's (0.63 m to a UV unit against 5.7), so the mesh's mean put
    /// its tiles at a third of their size. Her grain takes it (the skin shader's grain_scale); her pores are left
    /// as they were judged.</summary>
    public static float SurfacePoreScale(Mesh mesh, Material src)
    {
        for (int s = 0; s < mesh.GetSurfaceCount(); s++)
            if (mesh.SurfaceGetMaterial(s) == src)
            {
                var (a, u) = SurfaceAreas(mesh, s);
                return u > 0 ? (float)(Math.Sqrt(a / u) / 0.009) : PoreScale(mesh);
            }
        return PoreScale(mesh);
    }

    static (double Area, double UvArea) SurfaceAreas(Mesh mesh, int s)
    {
        double area = 0, uvArea = 0;
        var arr = mesh.SurfaceGetArrays(s);
        if (arr[(int)Mesh.ArrayType.TexUV].VariantType == Variant.Type.Nil) return (0, 0);
        var v = arr[(int)Mesh.ArrayType.Vertex].AsVector3Array();
        var uv = arr[(int)Mesh.ArrayType.TexUV].AsVector2Array();
        var idx = arr[(int)Mesh.ArrayType.Index].AsInt32Array();
        for (int t = 0; t + 2 < idx.Length; t += 3)
        {
            area += (v[idx[t + 1]] - v[idx[t]]).Cross(v[idx[t + 2]] - v[idx[t]]).Length() / 2;
            uvArea += Mathf.Abs((uv[idx[t + 1]] - uv[idx[t]]).Cross(uv[idx[t + 2]] - uv[idx[t]])) / 2;
        }
        return (area, uvArea);
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
        // (scaled about her head as her head's rest is: outfits baked her head 7% bigger as the Head bone's rest scale,
        // 14 October 2026, and a fit in plain metres would leave the hair at the old size)
        var hsc = rest.Basis.Scale;
        var fit = new Transform3D(Basis.Identity.Scaled(hsc * HairScale), rest.Origin + hsc * (HairOffset - HairScale * qHead));
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

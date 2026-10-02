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
        Color? HairColor = null, Color? Skin = null, Color? Cloth = null, Color? Under = null, double Figure = 0);

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
    public static Person Build(SurvivorUnchained.World.PersonSpec spec)
    {
        static Color? C(string? hex) => string.IsNullOrEmpty(hex) ? null : new Color(hex);
        var sex = spec.Sex == SurvivorUnchained.Rpg.Sex.Female ? "female" : "male";
        var outfit = spec.Outfit?.ToArray() ?? (sex == "female" ? FemalePeasant : MalePeasant);
        var look = new Look(sex, outfit, spec.Hair, spec.Beard == true, C(spec.HairColor), C(spec.Skin), C(spec.Dye?.Cloth), C(spec.Dye?.Under),
            sex == "female" ? spec.Figure ?? 1 : 0);
        var body = spec.Body;
        // --body heroine: the woman survivor in the body made from the
        // reference pictures (tools/assets/bind_scan.py), for trying it.
        if (body == SurvivorUnchained.Play.Loadouts.HerBody && Args.Get("body") == "heroine" && ResourceLoader.Exists("res://art/people/heroine.glb")) body = "heroine";
        var p = body switch { SurvivorUnchained.Play.Loadouts.HerBody => Woman(look), "heroine" => Heroine(look), "anime" => Her(look), _ => Build(look) };
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
        var person = new Person { Root = root, Skeleton = skel, Anim = new AnimationPlayer() };
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
        var person = new Person { Root = root, Skeleton = skel, Anim = new AnimationPlayer() };
        foreach (var mi in skel.GetChildren().OfType<MeshInstance3D>())
        {
            person.Meshes.Add(mi);
            mi.Layers = 2;
        }
        root.AddChild(person.Anim);
        person.Anim.RootNode = "..";
        person.Anim.AddAnimationLibrary("", Clips());
        return person;
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

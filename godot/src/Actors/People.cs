using System.Collections.Generic;
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
        Color? HairColor = null, Color? Skin = null, Color? Cloth = null, Color? Under = null);

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
        var p = Build(new Look(sex, outfit, spec.Hair, spec.Beard == true, C(spec.HairColor), C(spec.Skin), C(spec.Dye?.Cloth), C(spec.Dye?.Under)));
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
            else if (look.Skin is Color skin && (n.Contains("Superhero") || n.Contains("Regular"))) mat.AlbedoColor = skin;
            else if (look.Under is Color under && mi.Name.ToString().Contains("Legs") && (n.Contains("Peasant") || n.Contains("Ranger"))) mat.AlbedoColor = under;
            else if (look.Cloth is Color cloth && (n.Contains("Peasant") || n.Contains("Ranger"))) mat.AlbedoColor = cloth;
            mi.SetSurfaceOverrideMaterial(s, mat);
        }
    }
}

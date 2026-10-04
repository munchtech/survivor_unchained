using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// A survivor's own clips, made by tools/anim on their own skeleton: the
/// heroine's ("her/...", art/anim/heroine.res) and the hero's ("him/...",
/// art/anim/hero.res, the same motion given a man's carriage). Which of them
/// answers each clip the game asks for goes by the calling (from the outfit)
/// and what is held (HerClips); anything not made yet plays from the
/// Universal Animation Library as before.
/// </summary>
public sealed class OwnClips
{
    public static readonly OwnClips Her = new("her", "heroine"), Him = new("him", "hero");

    /// <summary>The library a body plays its own clips from, or none.</summary>
    public static OwnClips? Of(string body) => body switch { "heroine" => Her, "hero" => Him, _ => null };

    /// <summary>The library's name in an animation player ("her"), and its clips' prefix ("her/").</summary>
    public readonly string Name, Prefix;
    readonly string libPath, metaPath;
    AnimationLibrary? lib;
    Godot.Collections.Dictionary? meta;
    bool tried;

    OwnClips(string name, string file)
    {
        Name = name;
        Prefix = name + "/";
        libPath = $"res://art/anim/{file}.res";
        metaPath = $"res://art/anim/{file}_clips.json";
    }

    /// <summary>The library, or null when it has not been built.</summary>
    public AnimationLibrary? Library()
    {
        if (tried) return lib;
        tried = true;
        if (!ResourceLoader.Exists(libPath)) return null;
        lib = GD.Load<AnimationLibrary>(libPath);
        if (FileAccess.FileExists(metaPath))
            meta = Json.ParseString(FileAccess.GetFileAsString(metaPath)).AsGodotDictionary();
        return lib;
    }

    public bool Has(string clip) => Library()?.HasAnimation(clip) == true;

    /// <summary>One of these clips by the full name an animation player knows it by.</summary>
    public bool Owns(string name) => name.StartsWith(Prefix);

    Variant Meta(string clip, string key)
    {
        Library();
        if (meta == null || !meta.ContainsKey(clip)) return default;
        var m = meta[clip].AsGodotDictionary();
        return m.ContainsKey(key) ? m[key] : default;
    }

    /// <summary>How fast a loop carries them, in metres a second of their own
    /// skeleton (the figure stands 1.04 times it in the world); 0 for none.</summary>
    public float Speed(string clip) => Meta(clip, "speed").VariantType == Variant.Type.Nil ? 0 : (float)Meta(clip, "speed");

    /// <summary>A gesture (a nod, an exhale), laid over what plays rather
    /// than played in its place (Gestures); and whether it holds its end.</summary>
    public bool Gesture(string clip) => Meta(clip, "layer").VariantType == Variant.Type.String && (string)Meta(clip, "layer") == "gesture";

    public bool Holds(string clip) => Meta(clip, "hold").VariantType == Variant.Type.Bool && (bool)Meta(clip, "hold");

    static readonly HashSet<string> Idles = new()
    {
        "Idle", "Idle_Loop", "Idle_B", "Idle_Combat", "2H_Melee_Idle", "Unarmed_Idle", "Sword_Idle", "Pistol_Idle_Loop",
        "Pistol_Idle", "Spell_Simple_Idle_Loop", "Idle_Shield_Loop",
    };

    static readonly HashSet<string> Moving = new()
    {
        "Walk_Loop", "Walk", "Walking_A", "Walking_B", "Walking_C", "Jog_Fwd_Loop", "Jog_Fwd", "Running_A", "Running_B", "Sprint_Loop", "Sprint",
    };

    /// <summary>The own clip for one the game names ("her/..." or "him/...")
    /// if there is one, or null for the library's.</summary>
    public string? For(string calling, string kind, string game)
    {
        if (Library() == null) return null;
        string? want = null;
        if (Idles.Contains(game)) want = First($"idle_{calling}_{kind}", $"idle_{calling}");
        else if (Moving.Contains(game)) want = First($"run_{calling}_{kind}", $"run_{calling}");
        else
            want = game switch
            {
                "Sit_Chair_Idle" or "Sitting_Idle_Loop" or "Sitting_Idle" => "sit_log",
                "Hit_A" or "Hit_B" or "Hit_Chest" or "Hit_Head" => "hit",
                "Death_A" or "Death_B" or "Death01" or "Death_A_Pose" => "death",
                "Roll" or "Dodge_Forward" => "dash",
                "Jump_Full_Short" or "NinjaJump_Start" => "leap",
                "Jump_Start" => "vault",
                "Shield_Dash" => "bull_rush",
                "Sword_Dash" => "chain_haul",
                "Lie_StandUp" or "LayToIdle" => "get_up",
                "Spell_Simple_Shoot" or "Spellcast_Shoot" => "cast_bolt",
                "Spell_Simple_Enter" or "Spellcast_Raise" or "Spellcast_Summon" => "cast_raise",
                "OverhandThrow" or "Throw" => "throw",
                "Pistol_Shoot" or "1H_Ranged_Shoot" or "2H_Ranged_Shoot" => "crossbow_shoot",
                "Punch_Cross" or "Taunt" => "warcry",
                "Sword_Block" or "Block" => $"{calling}_show",
                "Sword_Regular_A" or "Sword_Regular_B" or "Sword_Regular_C" or "Sword_Attack" or "Sword_Regular_Combo"
                    or "Sword_Heavy_Combo" or "1H_Melee_Attack_Chop" => HerClips.Swings(kind) is { Length: > 0 } s ? s[0] : null,
                _ => null,
            };
        return want != null && Has(want) ? Prefix + want : null;
    }

    string First(params string[] names)
    {
        foreach (var n in names) if (Has(n)) return n;
        return names[^1];
    }
}

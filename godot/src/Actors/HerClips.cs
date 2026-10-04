using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The heroine's own clips (made by tools/anim on her skeleton, packed into
/// art/anim/heroine.res and played as "her/..."), and which of them answers
/// each clip the game asks for: by her calling (from her outfit) and what
/// she holds. Anything not made yet is played from the Universal Animation
/// Library as before.
/// </summary>
public static class HerClips
{
    const string LibPath = "res://art/anim/heroine.res", MetaPath = "res://art/anim/heroine_clips.json";
    public const string Prefix = "her/";
    static AnimationLibrary? lib;
    static Godot.Collections.Dictionary? meta;
    static bool tried;

    /// <summary>Her library, or null when it has not been built.</summary>
    public static AnimationLibrary? Library()
    {
        if (tried) return lib;
        tried = true;
        if (!ResourceLoader.Exists(LibPath)) return null;
        lib = GD.Load<AnimationLibrary>(LibPath);
        if (FileAccess.FileExists(MetaPath))
            meta = Json.ParseString(FileAccess.GetFileAsString(MetaPath)).AsGodotDictionary();
        return lib;
    }

    public static bool Has(string clip) => Library()?.HasAnimation(clip) == true;

    static Variant Meta(string clip, string key)
    {
        Library();
        if (meta == null || !meta.ContainsKey(clip)) return default;
        var m = meta[clip].AsGodotDictionary();
        return m.ContainsKey(key) ? m[key] : default;
    }

    /// <summary>How fast a loop carries her, in metres a second of her own
    /// skeleton (her figure stands 1.04 times it in the world); 0 for none.</summary>
    public static float Speed(string clip) => Meta(clip, "speed").VariantType == Variant.Type.Nil ? 0 : (float)Meta(clip, "speed");

    /// <summary>Her calling, from the outfit she wears ("her:ranger" is the stalker's).</summary>
    public static string Calling(IEnumerable<string>? outfit)
    {
        if (outfit == null) return "";
        foreach (var o in outfit)
            if (o.StartsWith("her:")) return o[4..] == "ranger" ? "stalker" : o[4..];
        return "";
    }

    /// <summary>What she holds, as her clips name it.</summary>
    public static string Kind(string? right, string? left, string? forearm) => right switch
    {
        "chevalier_sword" or "viking_sword" or "longsword" => "sword",
        "viking_axe" or "snake_axe" => left is "viking_axe" or "snake_axe" ? "axes" : "axe",
        "mage_staff" or "short_staff" => "staff",
        "wand" => "wand",
        "crossbow" => "crossbow",
        "daggers" => "daggers",
        _ => "",
    };

    static readonly HashSet<string> Idles = new()
    {
        "Idle", "Idle_Loop", "Idle_B", "Idle_Combat", "2H_Melee_Idle", "Unarmed_Idle", "Sword_Idle", "Pistol_Idle_Loop",
        "Pistol_Idle", "Spell_Simple_Idle_Loop", "Idle_Shield_Loop",
    };

    static readonly HashSet<string> Moving = new()
    {
        "Walk_Loop", "Walk", "Walking_A", "Walking_B", "Walking_C", "Jog_Fwd_Loop", "Jog_Fwd", "Running_A", "Running_B", "Sprint_Loop", "Sprint",
    };

    /// <summary>The swings for what she holds: alternate cuts, the first
    /// from her left to her right as the game's first arc sweeps.</summary>
    public static string[] Swings(string kind) => kind switch
    {
        "sword" => new[] { "sword_back", "sword_fore" },
        "axe" => new[] { "axe_back", "axe_fore" },
        "axes" => new[] { "axes_left", "axes_right" },
        "daggers" => new[] { "daggers_back", "daggers_fore" },
        _ => System.Array.Empty<string>(),
    };

    public static string Heavy(string kind) => kind switch
    {
        "sword" => "sword_heavy", "axe" => "axe_heavy", "axes" => "axes_heavy", "daggers" => "daggers_heavy", _ => "",
    };

    /// <summary>Her clip for one the game names, "her/..." if she has it, or
    /// null for the library's.</summary>
    public static string? For(string calling, string kind, string game)
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
                    or "Sword_Heavy_Combo" or "1H_Melee_Attack_Chop" => Swings(kind) is { Length: > 0 } s ? s[0] : null,
                _ => null,
            };
        return want != null && Has(want) ? Prefix + want : null;
    }

    static string First(params string[] names)
    {
        foreach (var n in names) if (Has(n)) return n;
        return names[^1];
    }
}

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

    // (Each clip's value, read from the meta once: asked several times a frame (her grip, her layers), every read
    // made new Godot wrappers (the clip's dictionary, the value, its key) that outlived the young collection.)
    readonly Dictionary<(string, string), Variant> metaRead = new();

    Variant Meta(string clip, string key)
    {
        Library();
        if (meta == null) return default;
        if (metaRead.TryGetValue((clip, key), out var known)) return known;
        Variant v = default;
        if (meta.ContainsKey(clip))
        {
            var m = meta[clip].AsGodotDictionary();
            if (m.ContainsKey(key)) v = m[key];
        }
        return metaRead[(clip, key)] = v;
    }

    /// <summary>How fast a loop carries them, in metres a second of their own
    /// skeleton (the figure stands 1.04 times it in the world); 0 for none.</summary>
    public float Speed(string clip) => Meta(clip, "speed").VariantType == Variant.Type.Nil ? 0 : (float)Meta(clip, "speed");

    /// <summary>How far the piece in her right hand sits along its shaft inside her fist while the clip plays, in
    /// metres (meta "grip_slide", animation 47); 0 for none. Takes the clip with or without this library's prefix.</summary>
    public float GripSlide(string clip)
    {
        if (clip.StartsWith(Prefix)) clip = clip.Substring(Prefix.Length);
        var v = Meta(clip, "grip_slide");
        return v.VariantType == Variant.Type.Nil ? 0 : (float)v;
    }

    /// <summary>The same for the piece in her LEFT hand (meta "grip_slide_l", animation 55: the second axe of the reaver's pair
    /// hangs from a fist gripped higher up its haft); 0 for none. Takes the clip with or without this library's prefix.</summary>
    public float GripSlideL(string clip)
    {
        if (clip.StartsWith(Prefix)) clip = clip.Substring(Prefix.Length);
        var v = Meta(clip, "grip_slide_l");
        return v.VariantType == Variant.Type.Nil ? 0 : (float)v;
    }

    /// <summary>How far the piece in her right hand is turned in her fist about the palm's normal while the clip plays,
    /// in degrees, + its head away from her fingers (meta "grip_tilt", animation 48: keyed.py grip_of); 0 for none.
    /// Takes the clip with or without this library's prefix.</summary>
    public float GripTilt(string clip)
    {
        if (clip.StartsWith(Prefix)) clip = clip.Substring(Prefix.Length);
        var v = Meta(clip, "grip_tilt");
        return v.VariantType == Variant.Type.Nil ? 0 : (float)v;
    }

    /// <summary>A gesture (a nod, an exhale), laid over what plays rather
    /// than played in its place (Gestures); and whether it holds its end.</summary>
    public bool Gesture(string clip) => Meta(clip, "layer").VariantType == Variant.Type.String && (string)Meta(clip, "layer") == "gesture";

    /// <summary>A swing on her upper body alone (PlayerView's upperShot filter; the hips and legs stay with what plays).</summary>
    public bool UpperLayer(string clip) => Meta(clip, "layer").VariantType == Variant.Type.String && (string)Meta(clip, "layer") == "upper";

    /// <summary>A swing keyed with its own fighting stance (feet set, hips into the blow): played on the whole
    /// of her while she stands (PlayerView.UpperHer), on her upper body over the run while she moves.</summary>
    public bool Stance(string clip) => Meta(clip, "stance").VariantType == Variant.Type.Bool && (bool)Meta(clip, "stance");

    public bool Holds(string clip) => Meta(clip, "hold").VariantType == Variant.Type.Bool && (bool)Meta(clip, "hold");

    static readonly HashSet<string> Idles = new()
    {
        "Idle", "Idle_Loop", "Idle_B", "Idle_Combat", "2H_Melee_Idle", "Unarmed_Idle", "Sword_Idle", "Pistol_Idle_Loop",
        "Pistol_Idle", "Spell_Simple_Idle_Loop", "Idle_Shield_Loop",
    };

    // (The names a walk goes by in the game's data; "Walk_Formal_Loop" is a cinematic's.)
    static readonly HashSet<string> Walks = new() { "Walk_Loop", "Walk", "Walking_A", "Walking_B", "Walking_C", "Walk_Formal_Loop" };

    static readonly HashSet<string> Moving = new()
    {
        "Walk_Loop", "Walk", "Walking_A", "Walking_B", "Walking_C", "Jog_Fwd_Loop", "Jog_Fwd", "Running_A", "Running_B", "Sprint_Loop", "Sprint",
    };

    /// <summary>The own clip for one the game names ("her/..." or "him/...")
    /// if there is one, or null for the library's.</summary>
    /// `sheathed`: her town clips first (Play/Sheath.Names), for the stand and the run.
    public string? For(string calling, string kind, string game, bool sheathed = false)
    {
        if (Library() == null) return null;
        string? want = null;
        if (Idles.Contains(game)) want = First(SurvivorUnchained.Play.Sheath.Names("idle", calling, kind, sheathed));
        else if (Walks.Contains(game) && Walk(calling, kind, sheathed) is string walk) return walk;
        else if (Walks.Contains(game) && game == "Walk_Formal_Loop") return null;
        else if (Moving.Contains(game)) want = First(SurvivorUnchained.Play.Sheath.Names("run", calling, kind, sheathed));
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
                // (C01 s11: her own, keyed to the weapon on the log; the hero has none yet and plays the kit's.)
                "PickUp_Table" => "take_from_log",
                "Sword_Block" or "Block" => $"{calling}_show",
                "Sword_Regular_A" or "Sword_Regular_B" or "Sword_Regular_C" or "Sword_Attack" or "Sword_Regular_Combo"
                    or "Sword_Heavy_Combo" or "1H_Melee_Attack_Chop" => HerClips.Swings(kind) is { Length: > 0 } s ? s[0] : null,
                _ => null,
            };
        return want != null && Has(want) ? Prefix + want : null;
    }

    /// <summary>Her walk for this calling and state (animation 51), prefixed, or null when she has none (the staff's town state).</summary>
    public string? Walk(string calling, string kind, bool sheathed)
    {
        foreach (var n in SurvivorUnchained.Play.Sheath.WalkNames(calling, kind, sheathed, Has)) if (Has(n)) return Prefix + n;
        return null;
    }

    string First(params string[] names)
    {
        foreach (var n in names) if (Has(n)) return n;
        return names[^1];
    }
}
